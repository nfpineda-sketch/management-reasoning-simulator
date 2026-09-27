"""The bank cases' narrative in Spanish, shown only once the faculty approved it (2026-09-26).

The faculty asked that whatever the app stores can be read in English or
Spanish, and that the narrative of the 31 bank cases be translated and used
only after their review, case by case, as with the patient photographs.

* The translations are data beside the English: ``case_text/es/<family>.json``
  (``tools_case_text.py``). Each passage carries the English it translates.
* A faculty member reviews a case's Spanish in the dashboard and approves it
  or asks for changes. The review names the exact version it read (a hash of
  every passage of that case, English and Spanish), so an edit to either
  language after the approval shows the case as pending again -- nothing is
  used on an approval of other words.
* Only approved cases, and within them only passages whose English is still
  the case's English, reach the room and the documents -- and only for that
  case: a sentence two cases share is Spanish in the approved one and stays
  English in the other. Everything else stays in English, whole: a sentence is
  replaced entirely or not at all, so no line mixes the two languages
  (decision 16).
* Approvals are recorded under the account that records them; nothing here
  approves on anyone's behalf. ``case_text/es/approvals.json`` can carry the
  approvals made in one deployment to another, exported only when asked.

The stored encounter stays in English, as every record does: the Spanish is
presentation, so an encounter played before an approval reads in Spanish
after it too.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "case_text"
DECISIONS = ("approved", "changes_requested")
#: The fixed words the room puts around one of a case's passages, translated
#: together with it so the line is whole in one language: English with an
#: unapproved case, Spanish with an approved one. Such a passage (who gives the
#: history: "Wife", "Son") is only ever shown inside these frames -- the arrival
#: line (``arrival_brief``) and the conversation panel -- and is never matched
#: on its own, where one word could stand for something else.
FRAMES = {"es": {"/history_source": (("History from: {}.", "Fuente de la historia: {}."),
                                     ("History source: {}", "Fuente de la historia: {}"))}}
#: How long an installed table is trusted before the reviews are read again.
REFRESH_SECONDS = 120


def _files(language):
    folder = ROOT / language
    return sorted(path for path in folder.glob("*.json") if path.name != "approvals.json") \
        if folder.exists() else []


_LOADED = {}


def passages(language="es"):
    """Every drafted passage: {variant_id: {path: {"en": ..., language: ...}}}."""
    files = _files(language)
    stamp = tuple((path.name, path.stat().st_mtime_ns) for path in files)
    cached = _LOADED.get(language)
    if cached and cached[0] == stamp:
        return cached[1]
    found = {}
    for path in files:
        for variant, rows in json.loads(path.read_text(encoding="utf-8")).items():
            found[variant] = rows
    _LOADED[language] = (stamp, found)
    return found


def version(rows, language="es"):
    """The exact words a review reads: every passage of one case, in both languages."""
    canonical = json.dumps(sorted((path, row.get("en", ""), row.get(language, ""))
                                  for path, row in (rows or {}).items()), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def current_english():
    """What each bank case says today, by variant and passage."""
    from clinical_cases import FAMILIES
    from tools_case_text import passages as case_passages
    return {variant["id"]: case_passages(variant) for spec in FAMILIES.values() for variant in spec["variants"]}


def usable_rows(variant_id, rows, english, language="es"):
    """The passages of an approved case that still translate what the case says."""
    today = english.get(variant_id) or {}
    return {path: row for path, row in (rows or {}).items()
            if row.get(language) and today.get(path) == row.get("en")}


class CaseTextReviews:
    """The faculty's reviews of each case's translation, one row per review."""

    def __init__(self, accounts):
        self.accounts = accounts
        self._execute = accounts._execute
        if not accounts.schema_ready("case_text_reviews"):
            with accounts._transaction(write=True) as connection:
                self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_case_text_reviews (
                    id TEXT PRIMARY KEY,
                    variant_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    version TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL REFERENCES mrs_users(id),
                    reviewer TEXT NOT NULL,
                    created_at BIGINT NOT NULL
                )""")
                self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_case_text_reviews_variant
                    ON mrs_case_text_reviews(variant_id, language, created_at)""")
            accounts.mark_schema_ready("case_text_reviews")

    def record(self, token, variant_id, decision, note="", language="es"):
        """A faculty member's review of the version on screen now; faculty and admin only."""
        from account_store import AccountError
        if decision not in DECISIONS:
            raise AccountError("Choose approve or request changes.")
        rows = passages(language).get(variant_id)
        if not rows:
            raise AccountError("This case has no translation to review.")
        if decision == "changes_requested" and not str(note or "").strip():
            raise AccountError("Say what should change, so the translation can be corrected.")
        import uuid
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"faculty", "admin"})
            self._execute(connection, """INSERT INTO mrs_case_text_reviews
                (id, variant_id, language, version, decision, note, reviewer_id, reviewer, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (f"{time.time_ns():020d}_{uuid.uuid4().hex}", variant_id, language,
                           version(rows, language), decision, str(note or "").strip()[:2000],
                           actor["id"], str(actor.get("username") or actor["id"]), int(time.time())))
        _INSTALLED.pop(language, None)

    def latest(self, language="es"):
        """The newest review of each case: {variant_id: row}."""
        found = {}
        with self.accounts._transaction() as connection:
            for row in self._execute(connection, """SELECT variant_id, version, decision, note, reviewer,
                    created_at FROM mrs_case_text_reviews WHERE language = ?
                    ORDER BY created_at, id""", (language,)).fetchall():
                found[row["variant_id"]] = dict(row)
        return found


def pack_approvals(language="es"):
    """Approvals carried from another deployment: [{variant_id, version, reviewer, ...}]."""
    path = ROOT / language / "approvals.json"
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in rows if isinstance(row, dict) and row.get("decision") == "approved"]


def status(variant_id, rows, latest, pack, language="es"):
    """``approved``, ``changes_requested``, ``pending`` or ``outdated`` for the version on file."""
    now = version(rows, language)
    review = latest.get(variant_id)
    if review and review["version"] == now:
        return review["decision"]
    if any(row.get("variant_id") == variant_id and row.get("version") == now for row in pack):
        return "approved"
    return "outdated" if review and review["decision"] == "approved" else "pending"


def approved_table(latest, pack=(), language="es"):
    """{case: {English: Spanish}} for each approved case, its passages that still translate it.

    Kept per case: many sentences are shared between cases, and an approval
    speaks for the case it was given to, not for every case with the same words.
    """
    english = current_english()
    tables = {}
    for variant_id, rows in passages(language).items():
        if status(variant_id, rows, latest, pack, language) != "approved":
            continue
        usable = usable_rows(variant_id, rows, english, language)
        framed = FRAMES.get(language, {})
        table = {row["en"]: row[language] for path, row in usable.items() if path not in framed}
        for path, frames in framed.items():
            for english_frame, frame in frames if path in usable else ():
                table[english_frame.format(usable[path]["en"])] = frame.format(usable[path][language])
        tables[variant_id] = table
    return tables


_INSTALLED = {}


def install(accounts=None, language="es", *, now=None):
    """Hand the room and the documents the approved passages, read at most every two minutes."""
    import language as languages
    now = time.monotonic() if now is None else now
    stamp = _INSTALLED.get(language)
    if stamp is not None and now - stamp < REFRESH_SECONDS:
        return
    latest = {}
    if accounts is not None:
        try:
            latest = CaseTextReviews(accounts).latest(language)
        except Exception:
            latest = {}
    languages.set_narrative(approved_table(latest, pack_approvals(language), language), language)
    _INSTALLED[language] = now
