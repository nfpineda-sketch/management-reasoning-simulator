"""The rubric's descriptors in Spanish, shown only once the faculty approved them (2026-09-27).

What each of the five domains asks and its four level descriptors are the
rubric's criteria. Their Spanish is a draft beside the English
(``rubric_text/es/descriptors.json``), reviewed domain by domain in the faculty
dashboard, as the cases' narrative is (``case_text``):

* A review names the exact words it read (a hash of the domain's descriptors in
  both languages), so an edit to either language after an approval shows the
  domain as pending again -- nothing is used on an approval of other words.
* A domain reads in Spanish only when it is approved and every descriptor
  still translates what ``rubric.DOMAINS`` says today; otherwise it reads in
  English, whole, so no domain mixes the two languages.
* Approvals are recorded under the account that records them; nothing here
  approves on anyone's behalf. ``rubric_text/es/approvals.json`` can carry the
  approvals made in one deployment to another, exported only when asked.

The rubric itself does not change: the scores, the AI proposal and its prompt
keep the English descriptors, which remain the criteria. The Spanish is how
they read on screen.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "rubric_text"
DECISIONS = ("approved", "changes_requested")
#: How long an installed table is trusted before the reviews are read again.
REFRESH_SECONDS = 120


def english(domain):
    """What the rubric says today for one domain: {"asks": ..., "levels/0": ..., ...}."""
    from rubric import DOMAINS
    found = {"asks": DOMAINS[domain]["asks"]}
    found.update({f"levels/{level}": text for level, text in sorted(DOMAINS[domain]["levels"].items())})
    return found


def drafts(language="es"):
    """Every drafted descriptor: {domain: {key: {"en": ..., language: ...}}}."""
    path = ROOT / language / "descriptors.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["domains"]


def version(domain, rows, language="es"):
    """The exact words a review reads: every descriptor of one domain, in both languages."""
    canonical = json.dumps([domain] + sorted([key, row.get("en", ""), row.get(language, "")]
                                             for key, row in (rows or {}).items()), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def current(domain, rows, language="es"):
    """Whether the draft translates every descriptor the rubric has today, and only those."""
    today = english(domain)
    rows = rows or {}
    return set(rows) == set(today) and all(
        rows[key].get("en") == text and str(rows[key].get(language) or "").strip()
        for key, text in today.items())


class RubricTextReviews:
    """The faculty's reviews of each domain's translation, one row per review."""

    def __init__(self, accounts):
        self.accounts = accounts
        self._execute = accounts._execute
        if not accounts.schema_ready("rubric_text_reviews"):
            with accounts._transaction(write=True) as connection:
                self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_rubric_text_reviews (
                    id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    version TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL REFERENCES mrs_users(id),
                    reviewer TEXT NOT NULL,
                    created_at BIGINT NOT NULL
                )""")
                self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_rubric_text_reviews_domain
                    ON mrs_rubric_text_reviews(domain_id, language, created_at)""")
            accounts.mark_schema_ready("rubric_text_reviews")

    def record(self, token, domain, decision, note="", language="es"):
        """A faculty member's review of the version on screen now; faculty and admin only."""
        from account_store import AccountError
        if decision not in DECISIONS:
            raise AccountError("Choose approve or request changes.")
        rows = drafts(language).get(domain)
        if not rows:
            raise AccountError("This domain has no translation to review.")
        if decision == "changes_requested" and not str(note or "").strip():
            raise AccountError("Say what should change, so the translation can be corrected.")
        if decision == "approved" and not current(domain, rows, language):
            raise AccountError("The rubric's English changed after this translation: it must be redone "
                               "before it can be approved.")
        import uuid
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"faculty", "admin"})
            self._execute(connection, """INSERT INTO mrs_rubric_text_reviews
                (id, domain_id, language, version, decision, note, reviewer_id, reviewer, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (f"{time.time_ns():020d}_{uuid.uuid4().hex}", domain, language,
                           version(domain, rows, language), decision, str(note or "").strip()[:2000],
                           actor["id"], str(actor.get("username") or actor["id"]), int(time.time())))
        _INSTALLED.pop(language, None)

    def latest(self, language="es"):
        """The newest review of each domain: {domain: row}."""
        found = {}
        with self.accounts._transaction() as connection:
            for row in self._execute(connection, """SELECT domain_id, version, decision, note, reviewer,
                    created_at FROM mrs_rubric_text_reviews WHERE language = ?
                    ORDER BY created_at, id""", (language,)).fetchall():
                found[row["domain_id"]] = dict(row)
        return found


def pack_approvals(language="es"):
    """Approvals carried from another deployment: [{domain_id, version, reviewer, ...}]."""
    path = ROOT / language / "approvals.json"
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in rows if isinstance(row, dict) and row.get("decision") == "approved"]


def status(domain, rows, latest, pack=(), language="es"):
    """``approved``, ``changes_requested``, ``pending`` or ``outdated`` for the version on file."""
    now = version(domain, rows, language)
    review = latest.get(domain)
    if review and review["version"] == now:
        return review["decision"]
    if any(row.get("domain_id") == domain and row.get("version") == now for row in pack):
        return "approved"
    return "outdated" if review and review["decision"] == "approved" else "pending"


def approved_table(latest, pack=(), language="es"):
    """{domain: {"asks": ..., "levels": {level: ...}}} for each approved domain that still translates the rubric."""
    tables = {}
    for domain, rows in drafts(language).items():
        if status(domain, rows, latest, pack, language) != "approved" or not current(domain, rows, language):
            continue
        tables[domain] = {"asks": rows["asks"][language],
                          "levels": {int(key.split("/", 1)[1]): row[language]
                                     for key, row in rows.items() if key.startswith("levels/")}}
    return tables


_INSTALLED = {}
_APPROVED = {}


def install(accounts=None, language="es", *, now=None):
    """Read the approved domains, at most every two minutes."""
    now = time.monotonic() if now is None else now
    stamp = _INSTALLED.get(language)
    if stamp is not None and now - stamp < REFRESH_SECONDS:
        return
    latest = {}
    if accounts is not None:
        try:
            latest = RubricTextReviews(accounts).latest(language)
        except Exception:
            latest = {}
    _APPROVED[language] = approved_table(latest, pack_approvals(language), language)
    _INSTALLED[language] = now


def descriptors(domain, language="en"):
    """What a domain asks and its level descriptors, in ``language`` once approved, else in English."""
    approved = _APPROVED.get(language, {}).get(domain) if language != "en" else None
    if approved:
        return {"language": language, "asks": approved["asks"], "levels": dict(approved["levels"])}
    from rubric import DOMAINS
    return {"language": "en", "asks": DOMAINS[domain]["asks"], "levels": dict(DOMAINS[domain]["levels"])}
