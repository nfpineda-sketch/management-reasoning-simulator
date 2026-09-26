"""The patient image bank: what exists, what each encounter showed, and what it cost.

Faculty request of 2026-09-26. Until then a patient photograph lived only in
the memory of one browser session: a reload, a resumed encounter or a restart
of the server paid for a new picture of a different person. The bank keeps
them in the application's own database, beside -- never inside -- the clinical
record:

* **images** are stored once, by content (``mrs_image_blobs``), and described
  by an **asset**: which synthetic identity, which visible state and which
  support devices it shows, how it was made, what it was made from, and what
  each check said. A technical check, the automated consistency screen, a
  person's visual review and a clinical review are four different things, kept
  in four fields; the last two start ``pending`` and only a person changes them
  (``mrs_image_reviews`` keeps every change, who made it and when). A rejected
  or excluded asset stays, with its reason, and is never selected again.
* **encounters** keep the identity they drew (``mrs_image_assignments``) and
  every change in what the room showed (``mrs_image_displays``): the image, or
  why there was none. That is what tells a simulator limitation from a
  resident's omission, and it is also each resident's visual exposure.
* **money**: every paid request is reserved before it is sent and settled after
  (``mrs_image_ledger``), against a budget with a dollar and a request limit.
  A failure or a timeout keeps its reservation charged. Nothing here resets it.

Nothing in this module calls a provider; ``image_broker`` does, through here.
"""
from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
import uuid
from collections import OrderedDict
from io import BytesIO

from account_store import AccountError

BANK_VERSION = "1.0"
STAFF = frozenset({"faculty", "admin"})
REVIEW_FIELDS = ("visual_review", "clinical_review")
REVIEW_DECISIONS = ("pending", "approved", "rejected")
SCREEN_ACCEPTED = ("accepted", "accepted_with_limitations")
MAX_NOTE = 1000
MAX_BLOB_BYTES = 12_000_000

# A job that died leaves its claim behind; after the lease another may take it.
DEFAULT_LEASE_SECONDS = 15 * 60


def contract_key(contract):
    """The state an image shows, as a key: only the drawable facts, no version, no vital sign."""
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# The reference state every identity is drawn in first. It is also an ordinary
# asset: a patient who recovers to exactly this state is shown this photograph.
ANCHOR_CONTRACT = {
    "mental_status": "alert", "expression": "neutral", "work_of_breathing": "normal",
    "skin_color": "natural", "diaphoresis": "absent", "mottling": False, "respiratory_support": "none",
}
ANCHOR_KEY = contract_key(ANCHOR_CONTRACT)


def _note(value, name="note"):
    value = str(value or "").strip()
    if len(value) > MAX_NOTE:
        raise AccountError(f"The {name} is too long.")
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _load(value, default):
    try:
        loaded = json.loads(value) if value else default
    except (TypeError, ValueError):
        return default
    return loaded if isinstance(loaded, type(default)) else default


class BudgetRefused(Exception):
    """A request the budget cannot cover. ``reason`` is 'dollars', 'requests' or 'price'."""

    def __init__(self, reason, summary=None):
        self.reason = reason
        self.summary = summary or {}
        super().__init__(f"Image budget refused: {reason}.")


# --- process cache of image bytes ------------------------------------------------------
# Images are not anyone's data: the same bytes serve every session that shows
# the asset. Bounded, so a large bank does not grow the process without end.
_CACHE_LIMIT = 96_000_000
_CACHE = OrderedDict()
_CACHE_SIZE = [0]
_CACHE_LOCK = threading.Lock()


def _cache_get(sha):
    with _CACHE_LOCK:
        raw = _CACHE.get(sha)
        if raw is not None:
            _CACHE.move_to_end(sha)
        return raw


def _cache_put(sha, raw):
    with _CACHE_LOCK:
        if sha in _CACHE:
            _CACHE.move_to_end(sha)
            return
        _CACHE[sha] = raw
        _CACHE_SIZE[0] += len(raw)
        while _CACHE_SIZE[0] > _CACHE_LIMIT and len(_CACHE) > 1:
            _, dropped = _CACHE.popitem(last=False)
            _CACHE_SIZE[0] -= len(dropped)


def forget_cache():
    """What a new process starts with. For tests of a restart."""
    with _CACHE_LOCK:
        _CACHE.clear()
        _CACHE_SIZE[0] = 0


def image_facts(raw):
    """Format and size of an image, or ValueError. Only PNG, JPEG and WebP are stored."""
    from PIL import Image
    if not isinstance(raw, (bytes, bytearray)) or not raw or len(raw) > MAX_BLOB_BYTES:
        raise ValueError("The image is missing or too large.")
    try:
        with Image.open(BytesIO(raw)) as image:
            image_format, size = image.format, image.size
            image.verify()
    except Exception as error:
        raise ValueError("The image could not be read.") from error
    types = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
    if image_format not in types or size[0] * size[1] > 8_000_000:
        raise ValueError("Unsupported image.")
    return {"content_type": types[image_format], "width": size[0], "height": size[1]}


class ImageBank:
    """The bank behind the account store. One per database; cheap to build on a rerun."""

    def __init__(self, accounts):
        self.accounts = accounts
        self._execute = accounts._execute
        self.key = hashlib.sha256(str(accounts._url).encode("utf-8")).hexdigest()[:16]
        if not accounts.schema_ready("image_bank"):
            self._initialize()
            accounts.mark_schema_ready("image_bank")

    def _initialize(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_image_blobs (
                sha256 TEXT PRIMARY KEY,
                content_type TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                size_bytes BIGINT NOT NULL,
                data_b64 TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_image_assets (
                id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                identity_version TEXT NOT NULL,
                kind TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('anchor', 'state')),
                state_key TEXT NOT NULL,
                contract_json TEXT NOT NULL,
                devices_json TEXT NOT NULL,
                master_sha256 TEXT REFERENCES mrs_image_blobs(sha256),
                display_sha256 TEXT NOT NULL REFERENCES mrs_image_blobs(sha256),
                reference_asset_id TEXT,
                generation_json TEXT NOT NULL,
                origin TEXT NOT NULL CHECK (origin IN ('generated', 'imported')),
                technical_check TEXT NOT NULL CHECK (technical_check IN ('passed', 'failed')),
                screen TEXT NOT NULL CHECK (screen IN ('accepted', 'accepted_with_limitations',
                                                       'rejected', 'not_screened')),
                screen_json TEXT NOT NULL,
                visual_review TEXT NOT NULL DEFAULT 'pending',
                clinical_review TEXT NOT NULL DEFAULT 'pending',
                excluded INTEGER NOT NULL DEFAULT 0 CHECK (excluded IN (0, 1)),
                exclusion_reason TEXT NOT NULL DEFAULT '',
                created_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_image_assets_state
                ON mrs_image_assets(identity_id, state_key, created_at)""",
            """CREATE TABLE IF NOT EXISTS mrs_image_reviews (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL REFERENCES mrs_image_assets(id),
                field TEXT NOT NULL,
                value TEXT NOT NULL,
                note TEXT NOT NULL,
                actor_id TEXT NOT NULL REFERENCES mrs_users(id),
                actor_role TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_image_claims (
                identity_id TEXT NOT NULL,
                state_key TEXT NOT NULL,
                owner TEXT NOT NULL,
                lease_until BIGINT NOT NULL,
                started_at BIGINT NOT NULL,
                PRIMARY KEY (identity_id, state_key)
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_image_jobs (
                id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                state_key TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK (outcome IN ('stored', 'rejected', 'failed')),
                code TEXT NOT NULL,
                stage TEXT NOT NULL,
                asset_id TEXT,
                requested_by TEXT NOT NULL,
                started_at BIGINT NOT NULL,
                finished_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_image_jobs_state
                ON mrs_image_jobs(identity_id, state_key, finished_at)""",
            """CREATE TABLE IF NOT EXISTS mrs_image_budgets (
                id TEXT PRIMARY KEY,
                limit_micro BIGINT NOT NULL,
                limit_requests INTEGER NOT NULL,
                authorization_text TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_image_ledger (
                id TEXT PRIMARY KEY,
                seq INTEGER NOT NULL,
                sent_order INTEGER,
                budget_id TEXT NOT NULL REFERENCES mrs_image_budgets(id),
                job_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                model TEXT NOT NULL,
                counts_request INTEGER NOT NULL CHECK (counts_request IN (0, 1)),
                status TEXT NOT NULL CHECK (status IN ('reserved', 'sent', 'succeeded', 'failed',
                                                       'released')),
                reserved_micro BIGINT NOT NULL,
                cost_micro BIGINT,
                cost_basis TEXT NOT NULL,
                usage_json TEXT NOT NULL,
                error_code TEXT NOT NULL,
                retry_of TEXT,
                identity_id TEXT NOT NULL,
                state_key TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at BIGINT NOT NULL,
                sent_at BIGINT,
                finished_at BIGINT
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_image_ledger_budget
                ON mrs_image_ledger(budget_id, created_at)""",
            """CREATE TABLE IF NOT EXISTS mrs_image_assignments (
                attempt_id TEXT PRIMARY KEY REFERENCES mrs_attempts(id),
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                identity_id TEXT NOT NULL,
                family TEXT NOT NULL,
                case_id TEXT NOT NULL,
                repeat_kind TEXT NOT NULL CHECK (repeat_kind IN ('none', 'bank_limited', 'deliberate')),
                selection_json TEXT NOT NULL,
                assigned_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_image_assignments_identity
                ON mrs_image_assignments(identity_id, family)""",
            """CREATE TABLE IF NOT EXISTS mrs_image_displays (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                identity_id TEXT NOT NULL,
                state_key TEXT NOT NULL,
                contract_json TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK (outcome IN ('image', 'pending', 'unavailable', 'failed')),
                asset_id TEXT,
                code TEXT NOT NULL,
                limitations_json TEXT NOT NULL,
                sim_time INTEGER,
                shown_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_image_displays_attempt
                ON mrs_image_displays(attempt_id, sequence)""",
            """CREATE INDEX IF NOT EXISTS mrs_image_displays_user
                ON mrs_image_displays(user_id, identity_id)""",
        ]
        with self.accounts._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)

    # --- images ---------------------------------------------------------------------
    def put_blob(self, raw):
        """Store bytes once, by content. Returns the sha256; storing it again changes nothing."""
        raw = bytes(raw)
        facts = image_facts(raw)
        sha = hashlib.sha256(raw).hexdigest()
        with self.accounts._transaction(write=True) as connection:
            exists = self._execute(connection, "SELECT sha256 FROM mrs_image_blobs WHERE sha256 = ?",
                                   (sha,)).fetchone()
            if exists is None:
                self._execute(connection, """INSERT INTO mrs_image_blobs
                    (sha256, content_type, width, height, size_bytes, data_b64, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sha, facts["content_type"], facts["width"], facts["height"], len(raw),
                     base64.b64encode(raw).decode("ascii"), int(time.time())))
        _cache_put(sha, raw)
        return sha

    def blob(self, sha):
        """The bytes of an image, from this process's cache or the database."""
        if not sha:
            return None
        raw = _cache_get(sha)
        if raw is not None:
            return raw
        with self.accounts._transaction() as connection:
            row = self._execute(connection, "SELECT data_b64 FROM mrs_image_blobs WHERE sha256 = ?",
                                (sha,)).fetchone()
        if row is None:
            return None
        raw = base64.b64decode(row["data_b64"])
        _cache_put(sha, raw)
        return raw

    def blob_facts(self, sha):
        with self.accounts._transaction() as connection:
            row = self._execute(connection, """SELECT sha256, content_type, width, height, size_bytes,
                created_at FROM mrs_image_blobs WHERE sha256 = ?""", (sha,)).fetchone()
        return dict(row) if row is not None else None

    # --- assets ---------------------------------------------------------------------
    def add_asset(self, *, identity_id, identity_version, role, contract, devices, display_sha256,
                  generation, screen, screen_details=None, master_sha256=None, reference_asset_id=None,
                  origin="generated", technical_check="passed", kind="patient_still",
                  excluded=False, exclusion_reason="", asset_id=None, created_at=None,
                  visual_review="pending", clinical_review="pending"):
        if role not in ("anchor", "state") or screen not in (*SCREEN_ACCEPTED, "rejected", "not_screened"):
            raise ValueError("Unknown asset role or screen result.")
        if technical_check not in ("passed", "failed") or origin not in ("generated", "imported"):
            raise ValueError("Unknown technical check or origin.")
        if visual_review not in REVIEW_DECISIONS or clinical_review not in REVIEW_DECISIONS:
            raise ValueError("Unknown review state.")
        identifier = asset_id or uuid.uuid4().hex
        created = int(created_at if created_at is not None else time.time())
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """INSERT INTO mrs_image_assets
                (id, identity_id, identity_version, kind, role, state_key, contract_json, devices_json,
                 master_sha256, display_sha256, reference_asset_id, generation_json, origin,
                 technical_check, screen, screen_json, visual_review, clinical_review, excluded,
                 exclusion_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, identity_id, identity_version, kind, role, contract_key(contract),
                 _json(contract), _json(list(devices)), master_sha256, display_sha256, reference_asset_id,
                 _json(generation), origin, technical_check, screen, _json(screen_details or {}),
                 visual_review, clinical_review, 1 if excluded else 0,
                 _note(exclusion_reason, "exclusion reason"), created))
        return self.asset(identifier)

    def asset(self, asset_id):
        with self.accounts._transaction() as connection:
            row = self._execute(connection, "SELECT * FROM mrs_image_assets WHERE id = ?",
                                (asset_id,)).fetchone()
        return _asset(row) if row is not None else None

    def assets(self, identity_id=None):
        """Every asset, newest first; with an identity, only that identity's."""
        with self.accounts._transaction() as connection:
            if identity_id is None:
                rows = self._execute(connection,
                                     "SELECT * FROM mrs_image_assets ORDER BY created_at DESC, id").fetchall()
            else:
                rows = self._execute(connection, """SELECT * FROM mrs_image_assets WHERE identity_id = ?
                    ORDER BY created_at DESC, id""", (identity_id,)).fetchall()
        return [_asset(row) for row in rows or []]

    def usable_asset(self, identity_id, state_key):
        """The asset the room may show for this person in this state, or None.

        A state is usable only if it was edited from the person's current
        anchor: two photographs of one encounter always descend from the same
        photograph, so a replaced anchor never mixes with its successor.
        """
        from image_selection import best_asset
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, """SELECT * FROM mrs_image_assets
                WHERE identity_id = ? AND state_key IN (?, ?) ORDER BY created_at DESC, id""",
                (identity_id, state_key, ANCHOR_KEY)).fetchall()
        assets = [_asset(row) for row in rows or []]
        anchor = best_asset([a for a in assets if a["role"] == "anchor" and a["state_key"] == ANCHOR_KEY])
        if state_key == ANCHOR_KEY:
            return anchor
        if anchor is None:
            return None
        return best_asset([a for a in assets if a["role"] == "state" and a["state_key"] == state_key
                           and a["reference_asset_id"] == anchor["id"]])

    def current_anchor(self, identity_id):
        return self.usable_asset(identity_id, ANCHOR_KEY)

    def withdraw(self, asset_id, reason, *, by):
        """Take an asset out of every selection for a technical reason, with its dependants.

        For the tool and the broker, not for a person's review: nothing here is
        an approval or a clinical judgement, and ``by`` says who did it. An
        anchor takes the states edited from it along, so the next state of that
        person comes from one photograph again.
        """
        reason = _note(f"{reason} ({by}, {time.strftime('%Y-%m-%d', time.gmtime())})", "reason")
        with self.accounts._transaction(write=True) as connection:
            rows = self._execute(connection, "SELECT id FROM mrs_image_assets WHERE id = ? OR reference_asset_id = ?",
                                 (asset_id, asset_id)).fetchall()
            for row in rows or []:
                self._execute(connection, """UPDATE mrs_image_assets SET excluded = 1, exclusion_reason = ?
                    WHERE id = ? AND excluded = 0""", (reason, row["id"]))
        return [row["id"] for row in rows or []]

    def update_screen(self, asset_id, screen, details):
        """A later screen of a candidate kept unscreened. The earlier result stays in its history."""
        if screen not in (*SCREEN_ACCEPTED, "rejected", "not_screened"):
            raise ValueError("Unknown screen result.")
        with self.accounts._transaction(write=True) as connection:
            row = self._execute(connection, "SELECT screen, screen_json FROM mrs_image_assets WHERE id = ?",
                                (asset_id,)).fetchone()
            if row is None:
                return False
            previous = _load(row["screen_json"], {})
            history = previous.pop("history", [])
            history.append({"screen": row["screen"], **previous, "until": int(time.time())})
            record = {**details, "history": history[-10:]}
            if screen == "rejected":
                self._execute(connection, """UPDATE mrs_image_assets SET screen = ?, screen_json = ?, excluded = 1,
                    exclusion_reason = ? WHERE id = ?""",
                    (screen, _json(record), "Rejected by the automated screen.", asset_id))
            else:
                self._execute(connection, "UPDATE mrs_image_assets SET screen = ?, screen_json = ? WHERE id = ?",
                              (screen, _json(record), asset_id))

    def note_correction(self, asset_id, corrects_id):
        """Link a corrected picture to the rejected candidate it replaces."""
        with self.accounts._transaction(write=True) as connection:
            row = self._execute(connection, "SELECT screen_json FROM mrs_image_assets WHERE id = ?",
                                (asset_id,)).fetchone()
            if row is None:
                return False
            record = {**_load(row["screen_json"], {}), "corrects": corrects_id}
            self._execute(connection, "UPDATE mrs_image_assets SET screen_json = ? WHERE id = ?",
                          (_json(record), asset_id))

    def _staff(self, connection, token):
        return self.accounts._actor(connection, token, STAFF)

    def review(self, token, asset_id, field, decision, note=""):
        """A person's visual or clinical review of one asset. Only staff; nothing earlier is lost."""
        if field not in REVIEW_FIELDS or decision not in REVIEW_DECISIONS:
            raise AccountError("Choose a valid review.")
        note = _note(note)
        with self.accounts._transaction(write=True) as connection:
            actor = self._staff(connection, token)
            if self._execute(connection, "SELECT id FROM mrs_image_assets WHERE id = ?",
                             (asset_id,)).fetchone() is None:
                raise AccountError("The image was not found.")
            self._execute(connection, f"UPDATE mrs_image_assets SET {field} = ? WHERE id = ?",
                          (decision, asset_id))
            self._record_review(connection, actor, asset_id, field, decision, note)

    def exclude(self, token, asset_id, reason, excluded=True):
        """Keep an asset out of every selection (or bring it back), with the reason recorded."""
        reason = _note(reason, "reason")
        if excluded and not reason:
            raise AccountError("Say why this image is excluded.")
        with self.accounts._transaction(write=True) as connection:
            actor = self._staff(connection, token)
            if self._execute(connection, "SELECT id FROM mrs_image_assets WHERE id = ?",
                             (asset_id,)).fetchone() is None:
                raise AccountError("The image was not found.")
            self._execute(connection, """UPDATE mrs_image_assets SET excluded = ?, exclusion_reason = ?
                WHERE id = ?""", (1 if excluded else 0, reason if excluded else "", asset_id))
            self._record_review(connection, actor, asset_id, "excluded", "yes" if excluded else "no", reason)

    def _record_review(self, connection, actor, asset_id, field, value, note):
        self._execute(connection, """INSERT INTO mrs_image_reviews
            (id, asset_id, field, value, note, actor_id, actor_role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (uuid.uuid4().hex, asset_id, field, value, note, actor["id"], actor["role"], int(time.time())))

    def reviews(self, token, asset_id):
        with self.accounts._transaction() as connection:
            self._staff(connection, token)
            rows = self._execute(connection, """SELECT r.*, u.username FROM mrs_image_reviews r
                JOIN mrs_users u ON u.id = r.actor_id WHERE r.asset_id = ? ORDER BY r.created_at, r.id""",
                (asset_id,)).fetchall()
        return [dict(row) for row in rows or []]

    # --- one job per person and state, across processes ------------------------------
    def claim(self, identity_id, state_key, owner, lease_seconds=DEFAULT_LEASE_SECONDS):
        """Take the right to make this image. False while another live owner holds it."""
        now = int(time.time())
        with self.accounts._transaction(write=True) as connection:
            row = self._execute(connection, """SELECT owner, lease_until FROM mrs_image_claims
                WHERE identity_id = ? AND state_key = ?""", (identity_id, state_key)).fetchone()
            if row is not None and row["owner"] != owner and int(row["lease_until"]) > now:
                return False
            if row is not None:
                self._execute(connection, "DELETE FROM mrs_image_claims WHERE identity_id = ? AND state_key = ?",
                              (identity_id, state_key))
            self._execute(connection, """INSERT INTO mrs_image_claims
                (identity_id, state_key, owner, lease_until, started_at) VALUES (?, ?, ?, ?, ?)""",
                (identity_id, state_key, owner, now + int(lease_seconds), now))
        return True

    def release(self, identity_id, state_key, owner):
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """DELETE FROM mrs_image_claims
                WHERE identity_id = ? AND state_key = ? AND owner = ?""", (identity_id, state_key, owner))

    def claimed(self, identity_id, state_key):
        """The live claim on this image, if anyone holds one."""
        with self.accounts._transaction() as connection:
            row = self._execute(connection, """SELECT owner, lease_until, started_at FROM mrs_image_claims
                WHERE identity_id = ? AND state_key = ?""", (identity_id, state_key)).fetchone()
        if row is None or int(row["lease_until"]) <= int(time.time()):
            return None
        return dict(row)

    def record_job(self, *, identity_id, state_key, outcome, code, stage, asset_id, requested_by, started_at):
        identifier = uuid.uuid4().hex
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """INSERT INTO mrs_image_jobs
                (id, identity_id, state_key, outcome, code, stage, asset_id, requested_by, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, identity_id, state_key, outcome, code, stage, asset_id, requested_by,
                 int(started_at), int(time.time())))
        return identifier

    def last_job(self, identity_id, state_key):
        with self.accounts._transaction() as connection:
            row = self._execute(connection, """SELECT * FROM mrs_image_jobs WHERE identity_id = ? AND state_key = ?
                ORDER BY finished_at DESC, id DESC LIMIT 1""", (identity_id, state_key)).fetchone()
        return dict(row) if row is not None else None

    def jobs(self, limit=200):
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, "SELECT * FROM mrs_image_jobs ORDER BY finished_at DESC, id LIMIT ?",
                                 (int(limit),)).fetchall()
        return [dict(row) for row in rows or []]

    # --- money ----------------------------------------------------------------------
    def ensure_budget(self, budget):
        """Record a budget the first time; an identifier never changes its limits afterwards."""
        with self.accounts._transaction(write=True) as connection:
            row = self._execute(connection, "SELECT * FROM mrs_image_budgets WHERE id = ?",
                                (budget["id"],)).fetchone()
            if row is None:
                self._execute(connection, """INSERT INTO mrs_image_budgets
                    (id, limit_micro, limit_requests, authorization_text, created_at) VALUES (?, ?, ?, ?, ?)""",
                    (budget["id"], int(budget["limit_micro"]), int(budget["limit_requests"]),
                     str(budget.get("authorization") or "")[:1000], int(time.time())))
                stored = dict(budget)
            else:
                stored = {"id": row["id"], "limit_micro": int(row["limit_micro"]),
                          "limit_requests": int(row["limit_requests"]), "authorization": row["authorization_text"]}
        # Raised outside the transaction: inside it any error reads as "database unavailable".
        if (int(stored["limit_micro"]) != int(budget["limit_micro"])
                or int(stored["limit_requests"]) != int(budget["limit_requests"])):
            raise ValueError("This budget identifier was recorded with other limits; a new "
                             "authorization needs a new identifier.")
        return stored

    def _totals(self, connection, budget_id):
        row = self._execute(connection, """SELECT
            COALESCE(SUM(CASE WHEN status = 'released' THEN 0
                              WHEN cost_micro IS NOT NULL THEN cost_micro
                              ELSE reserved_micro END), 0) AS committed,
            COALESCE(SUM(CASE WHEN status IN ('reserved', 'sent') THEN reserved_micro ELSE 0 END), 0) AS in_flight,
            COALESCE(SUM(CASE WHEN status NOT IN ('reserved', 'sent', 'released') AND cost_basis = 'provider_usage'
                              THEN cost_micro ELSE 0 END), 0) AS from_usage,
            COALESCE(SUM(CASE WHEN status IN ('succeeded', 'failed') AND cost_basis <> 'provider_usage'
                              THEN reserved_micro ELSE 0 END), 0) AS estimated,
            COALESCE(SUM(CASE WHEN counts_request = 1 AND status <> 'released' THEN 1 ELSE 0 END), 0) AS requests,
            COALESCE(SUM(CASE WHEN counts_request = 1 AND status IN ('sent', 'succeeded', 'failed')
                              THEN 1 ELSE 0 END), 0) AS requests_sent,
            COALESCE(SUM(CASE WHEN status IN ('sent', 'succeeded', 'failed') THEN 1 ELSE 0 END), 0) AS calls_sent,
            COALESCE(SUM(CASE WHEN retry_of IS NOT NULL AND status <> 'released' THEN 1 ELSE 0 END), 0) AS retries
            FROM mrs_image_ledger WHERE budget_id = ?""", (budget_id,)).fetchone()
        return {key: int(row[key] or 0) for key in ("committed", "in_flight", "from_usage", "estimated",
                                                    "requests", "requests_sent", "calls_sent", "retries")}

    def reserve(self, budget, items, *, job_id, identity_id, state_key, requested_by, note=""):
        """Reserve the worst case of every item before anything is sent, or refuse them all.

        ``items`` is a list of ``(kind, model, ceiling_micro, counts_request, retry_of)``.
        Checked and written in one write transaction, so two workers can never
        both take the last dollar.
        """
        budget = self.ensure_budget(budget)
        now = int(time.time())
        refusal = None
        identifiers = []
        with self.accounts._transaction(write=True) as connection:
            totals = self._totals(connection, budget["id"])
            asked = sum(int(item[2]) for item in items)
            asked_requests = sum(1 for item in items if item[3])
            summary = self._summary(budget, totals)
            if totals["committed"] + asked > budget["limit_micro"]:
                refusal = BudgetRefused("dollars", summary)
            elif totals["requests"] + asked_requests > budget["limit_requests"]:
                refusal = BudgetRefused("requests", summary)
            else:
                highest = self._execute(connection, "SELECT COALESCE(MAX(seq), 0) AS highest FROM mrs_image_ledger",
                                        ()).fetchone()
                sequence = int(highest["highest"] or 0)
                for kind, model, ceiling_micro, counts_request, retry_of in items:
                    identifier = uuid.uuid4().hex
                    sequence += 1
                    self._execute(connection, """INSERT INTO mrs_image_ledger
                        (id, seq, sent_order, budget_id, job_id, kind, model, counts_request, status, reserved_micro,
                         cost_micro, cost_basis, usage_json, error_code, retry_of, identity_id, state_key,
                         requested_by, note, created_at, sent_at, finished_at)
                        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 'reserved', ?, NULL, 'reservation', '{}', '', ?, ?, ?, ?, ?,
                                ?, NULL, NULL)""",
                        (identifier, sequence, budget["id"], job_id, kind, model, 1 if counts_request else 0,
                         int(ceiling_micro), retry_of, identity_id, state_key, str(requested_by)[:200],
                         _note(note), now))
                    identifiers.append(identifier)
        # Raised outside the transaction: inside it any error reads as "database unavailable".
        if refusal is not None:
            raise refusal
        return identifiers

    def known_assets(self):
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, "SELECT id FROM mrs_image_assets").fetchall()
        return {row["id"] for row in rows or []}

    def import_ledger(self, budget, entries):
        """Ledger rows written elsewhere (the pilot, run outside this database), kept exactly.

        A row already here is left alone. A row still reserved or sent is
        imported as it is: it stays charged, because nobody knows it was free.
        """
        budget = self.ensure_budget(budget)
        added = 0
        with self.accounts._transaction(write=True) as connection:
            known = {row["id"] for row in self._execute(
                connection, "SELECT id FROM mrs_image_ledger WHERE budget_id = ?", (budget["id"],)).fetchall() or []}
            highest = self._execute(connection, "SELECT COALESCE(MAX(seq), 0) AS highest FROM mrs_image_ledger",
                                    ()).fetchone()
            sequence = int(highest["highest"] or 0)
            for entry in sorted(entries, key=lambda row: row.get("seq") or 0):
                if entry["id"] in known or entry.get("budget_id") != budget["id"]:
                    continue
                sequence += 1
                self._execute(connection, """INSERT INTO mrs_image_ledger
                    (id, seq, sent_order, budget_id, job_id, kind, model, counts_request, status, reserved_micro,
                     cost_micro, cost_basis, usage_json, error_code, retry_of, identity_id, state_key, requested_by,
                     note, created_at, sent_at, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (entry["id"], sequence, entry.get("sent_order"), budget["id"], entry["job_id"], entry["kind"],
                     entry["model"], int(entry["counts_request"]), entry["status"], int(entry["reserved_micro"]),
                     entry.get("cost_micro"), entry["cost_basis"], entry.get("usage_json") or "{}",
                     entry.get("error_code") or "", entry.get("retry_of"), entry["identity_id"], entry["state_key"],
                     entry.get("requested_by") or "", entry.get("note") or "", int(entry["created_at"]),
                     entry.get("sent_at"), entry.get("finished_at")))
                added += 1
        return added

    def import_job(self, job):
        with self.accounts._transaction(write=True) as connection:
            if self._execute(connection, "SELECT id FROM mrs_image_jobs WHERE id = ?", (job["id"],)).fetchone():
                return False
            self._execute(connection, """INSERT INTO mrs_image_jobs
                (id, identity_id, state_key, outcome, code, stage, asset_id, requested_by, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (job["id"], job["identity_id"], job["state_key"], job["outcome"], job["code"], job["stage"],
                 job.get("asset_id"), job["requested_by"], int(job["started_at"]), int(job["finished_at"])))
        return True

    def mark_sent(self, entry_id):
        with self.accounts._transaction(write=True) as connection:
            highest = self._execute(connection, "SELECT COALESCE(MAX(sent_order), 0) AS highest FROM mrs_image_ledger",
                                    ()).fetchone()
            self._execute(connection, """UPDATE mrs_image_ledger SET status = 'sent', sent_at = ?, sent_order = ?
                WHERE id = ? AND status = 'reserved'""", (int(time.time()), int(highest["highest"] or 0) + 1, entry_id))

    def settle(self, entry_id, status, *, usage=None, cost_micro=None, error_code=""):
        """What happened to one sent request. Without reported usage the reservation stays charged."""
        if status not in ("succeeded", "failed"):
            raise ValueError("A settled request succeeded or failed.")
        basis = "provider_usage" if cost_micro is not None else "estimate"
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """UPDATE mrs_image_ledger SET status = ?, cost_micro = ?, cost_basis = ?,
                usage_json = ?, error_code = ?, finished_at = ? WHERE id = ? AND status IN ('reserved', 'sent')""",
                (status, cost_micro, basis, _json(usage or {}), str(error_code or "")[:40], int(time.time()),
                 entry_id))

    def release_reservations(self, entry_ids):
        """Give back reservations for requests that were never sent."""
        if not entry_ids:
            return
        with self.accounts._transaction(write=True) as connection:
            for entry_id in entry_ids:
                self._execute(connection, """UPDATE mrs_image_ledger SET status = 'released', finished_at = ?
                    WHERE id = ? AND status = 'reserved'""", (int(time.time()), entry_id))

    @staticmethod
    def _summary(budget, totals):
        return {"budget_id": budget["id"], "limit_micro": budget["limit_micro"],
                "limit_requests": budget["limit_requests"], **totals,
                "remaining_micro": max(0, budget["limit_micro"] - totals["committed"]),
                "remaining_requests": max(0, budget["limit_requests"] - totals["requests"])}

    def budget_summary(self, budget):
        budget = self.ensure_budget(budget)
        with self.accounts._transaction() as connection:
            totals = self._totals(connection, budget["id"])
        return self._summary(budget, totals)

    def ledger(self, budget_id, limit=500):
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, """SELECT * FROM mrs_image_ledger WHERE budget_id = ?
                ORDER BY seq LIMIT ?""", (budget_id, int(limit))).fetchall()
        return [dict(row) for row in rows or []]

    # --- encounters -----------------------------------------------------------------
    def _owned_attempt(self, connection, token, attempt_id):
        actor = self.accounts._actor(connection, token)
        if not isinstance(attempt_id, str) or not attempt_id or len(attempt_id) > 200:
            raise AccountError("Choose an encounter.")
        row = self._execute(connection, "SELECT id, user_id FROM mrs_attempts WHERE id = ?",
                            (attempt_id,)).fetchone()
        if row is None:
            raise AccountError("The encounter was not found.")
        return actor, row

    def assignment(self, token, attempt_id):
        """The identity this encounter drew, for its owner or staff; None before it drew one."""
        with self.accounts._transaction() as connection:
            actor, row = self._owned_attempt(connection, token, attempt_id)
            if row["user_id"] != actor["id"] and actor["role"] not in STAFF:
                raise AccountError("Your account does not have permission for this action.")
            found = self._execute(connection, "SELECT * FROM mrs_image_assignments WHERE attempt_id = ?",
                                  (attempt_id,)).fetchone()
        return _assignment(found) if found is not None else None

    def assign(self, token, attempt_id, *, identity_id, family, case_id, repeat_kind, selection):
        """Record the encounter's identity once. A second call returns the first choice."""
        with self.accounts._transaction(write=True) as connection:
            actor, row = self._owned_attempt(connection, token, attempt_id)
            if row["user_id"] != actor["id"]:
                raise AccountError("Only the encounter's owner draws its patient.")
            found = self._execute(connection, "SELECT * FROM mrs_image_assignments WHERE attempt_id = ?",
                                  (attempt_id,)).fetchone()
            if found is not None:
                return _assignment(found)
            self._execute(connection, """INSERT INTO mrs_image_assignments
                (attempt_id, user_id, identity_id, family, case_id, repeat_kind, selection_json, assigned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (attempt_id, actor["id"], identity_id, str(family or "")[:80], str(case_id or "")[:120],
                 repeat_kind, _json(selection), int(time.time())))
            found = self._execute(connection, "SELECT * FROM mrs_image_assignments WHERE attempt_id = ?",
                                  (attempt_id,)).fetchone()
        return _assignment(found)

    def log_display(self, token, attempt_id, *, identity_id, contract, outcome, asset_id=None, code="",
                    limitations=(), sim_time=None):
        """One change in what the room showed for this encounter. Only its owner's room writes it."""
        if outcome not in ("image", "pending", "unavailable", "failed"):
            raise ValueError("Unknown display outcome.")
        with self.accounts._transaction(write=True) as connection:
            actor, row = self._owned_attempt(connection, token, attempt_id)
            if row["user_id"] != actor["id"]:
                raise AccountError("Only the encounter's owner shows its patient.")
            highest = self._execute(connection, """SELECT COALESCE(MAX(sequence), 0) AS highest
                FROM mrs_image_displays WHERE attempt_id = ?""", (attempt_id,)).fetchone()
            sequence = int(highest["highest"] or 0) + 1
            self._execute(connection, """INSERT INTO mrs_image_displays
                (id, attempt_id, user_id, sequence, identity_id, state_key, contract_json, outcome, asset_id,
                 code, limitations_json, sim_time, shown_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uuid.uuid4().hex, attempt_id, actor["id"], sequence, identity_id, contract_key(contract),
                 _json(contract), outcome, asset_id, str(code or "")[:40], _json(list(limitations)),
                 None if sim_time is None else int(sim_time), int(time.time())))
        return sequence

    def displays(self, token, attempt_id):
        """What the room showed in one encounter, in order: for its owner and for staff."""
        with self.accounts._transaction() as connection:
            actor, row = self._owned_attempt(connection, token, attempt_id)
            if row["user_id"] != actor["id"] and actor["role"] not in STAFF:
                raise AccountError("Your account does not have permission for this action.")
            rows = self._execute(connection, """SELECT * FROM mrs_image_displays WHERE attempt_id = ?
                ORDER BY sequence""", (attempt_id,)).fetchall()
        return [_display(row) for row in rows or []]

    def exposures(self, user_id):
        """Which identities this person has been shown, when last, and in how many encounters."""
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, """SELECT identity_id, MAX(shown_at) AS last_shown,
                COUNT(DISTINCT attempt_id) AS encounters FROM mrs_image_displays
                WHERE user_id = ? AND outcome = 'image' GROUP BY identity_id""", (user_id,)).fetchall()
        return {row["identity_id"]: {"last_shown": int(row["last_shown"]), "encounters": int(row["encounters"])}
                for row in rows or []}

    def usage(self):
        """How often each identity was drawn, overall and per family: the balance selection keeps."""
        with self.accounts._transaction() as connection:
            rows = self._execute(connection, """SELECT identity_id, family, COUNT(*) AS drawn
                FROM mrs_image_assignments GROUP BY identity_id, family""").fetchall()
        usage = {}
        for row in rows or []:
            record = usage.setdefault(row["identity_id"], {"total": 0, "families": {}})
            record["total"] += int(row["drawn"])
            record["families"][row["family"]] = int(row["drawn"])
        return usage


def _asset(row):
    record = dict(row)
    record["contract"] = _load(record.pop("contract_json", None), {})
    record["devices"] = _load(record.pop("devices_json", None), [])
    record["generation"] = _load(record.pop("generation_json", None), {})
    record["screen_details"] = _load(record.pop("screen_json", None), {})
    record["excluded"] = bool(record.get("excluded"))
    return record


def _assignment(row):
    record = dict(row)
    record["selection"] = _load(record.pop("selection_json", None), {})
    return record


def _display(row):
    record = dict(row)
    record["contract"] = _load(record.pop("contract_json", None), {})
    record["limitations"] = _load(record.pop("limitations_json", None), [])
    return record
