"""P3-282 to P3-284: the faculty STATUS VIEW, the REVIEW BUNDLE and the FACULTY FEEDBACK schema of the controlled faculty development review (layer, development only).

Everything here READS the authority artifact, the authority-session record and the Management Trace of ONE faculty review encounter; it decides nothing clinical, changes no state, scores nothing and
reaches no resident. It writes only into the review directory of the faculty authority store (``runtime_faculty_review.review_root``), create-only.

THE BUNDLE keeps two parts apart on purpose (P3-285A, blinding where useful): ``authority_view`` is what the pressure authority produced and what management was done; ``comparator`` is the legacy
counterfactual and the common-consciousness comparison. A reviewer judges the first before seeing the second, so the legacy engine does not anchor the judgement. The comparator is EVIDENCE FOR
REVIEW: no closeness, error, match or score of any kind is computed from it (P3-283A), and a test refuses a bundle that carries one.

THE FEEDBACK schema asks educational-validity questions only, never implementation ones. It is bound to one bundle: feedback that names another case, scenario, encounter or bundle is refused.
The cases are synthetic development cases; a feedback form that looks like it carries real-patient identifiers is refused.
"""
from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence

import runtime_authority as ra
import runtime_authority_store as ras
import runtime_faculty_review as fr
import runtime_pressure_grant as grants

VERSION = "P3-283"
BUNDLE_TYPE = "PHASE3_FACULTY_REVIEW_BUNDLE"
FEEDBACK_TYPE = "PHASE3_FACULTY_REVIEW_FEEDBACK"
STATUS_TYPE = "PHASE3_FACULTY_REVIEW_STATUS"
COMPARATOR_LABEL = "NONAUTHORITATIVE DEVELOPMENT COMPARISON"
COMPARATOR_NOTE = ("Evidence for faculty review, not a standard of truth and not a score: a difference from the legacy engine is not an error, and closeness to it is not success. "
                   "The common consciousness is a nonauthoritative faculty-comparison overlay: it is not resident-visible and it writes nothing into the encounter.")
#: Words no bundle key may carry, as whole TOKENS of the key (``mean_absolute_error`` carries ``error``; ``sbp_difference`` carries none): a bundle presents evidence, it does not grade the authority
#: against the legacy engine. Values are free text and are not scanned: the limit is declared (the check is a tripwire on the shape of the bundle, not a proof of intent).
FORBIDDEN_BUNDLE_KEYS = ("score", "scores", "scored", "closeness", "error", "errors", "rmse", "mae", "agreement", "accuracy", "grade", "graded", "pass", "passed", "fail", "failed", "similarity", "distance",
                         "pct", "percent", "percentage")
#: Phrases (the key's tokens joined by ``_``) that grade even though no single token does.
FORBIDDEN_BUNDLE_PHRASES = ("match_rate", "hit_rate", "within_tolerance", "closer_to", "better_than", "worse_than")
LIMITATIONS = (
    "The session record and the provenance anchor are unsigned (accepted for this single-process development review only; FD-FAC-05).",
    "Single process only: the environment enforces one review process per store, it does not solve multiprocess storage (FD-FAC-06).",
    "After a halt, ECG acquisition, cancelling pending actions and the retrospective explanation are blocked and excluded from this protocol (FD-FAC-07).",
    "After a halt the only resolution is to leave the experimental encounter: no resume, no rollback, no restart from the pre-authority snapshot (FD-FAC-08).",
    "The halt notice is the existing English development notice; it is operational and says nothing about the patient (FD-FAC-09).",
    "GI pressure development authority only (SBP, DBP, MAP derived) for two authored cases; nothing is generalized to another case or family.",
    "The common consciousness is nonauthoritative, faculty-comparison only and not resident visible; no live mental_status mapping (FD-FAC-10).",
    "The shadow session keeps in memory what it observed of a refused turn; it is never persisted or shown.",
    "Not a resident pilot, not a production deployment, not a clinical validation.",
)


def _plain(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _pressure(item: Any) -> dict:
    body = dict(item or {})
    return {key: body.get(key) for key in ("sbp", "dbp", "map")}


# -- the live session -------------------------------------------------------------------------------------------------------------------------------------------------
def from_session(store: Any) -> dict:
    """(artifact, record, trace, decision) of this page session, read through the layer's own keys. The artifact is the live site's, or the preserved one of a halted site. Never raises."""
    try:
        site = store.get(ra.SITE_KEY)
        artifact = site.artifact() if site is not None else (store.get(ra.ARTIFACT_KEY) or None)
    except Exception:
        artifact = None
    try:
        record = store.get(ra.SESSION_KEY)
    except Exception:
        record = None
    try:
        trace = list(store.get("management_trace") or [])
    except Exception:
        trace = []
    try:
        decision = store.get(fr.SESSION_KEY)
    except Exception:
        decision = None
    return {"artifact": artifact, "record": record, "trace": trace, "decision": decision}


def _core_lineage(grant: Mapping) -> dict:
    """The active core member the grant is bound to: the artifact's own grant when it carries it, else the registered grant it names (only when it IS that grant)."""
    own = dict(dict(grant).get("core_lineage") or {})
    if own:
        return own
    registered = dict(grants.GRANT)
    return dict(registered.get("core_lineage") or {}) if dict(grant).get("grant_id") in (None, registered.get("grant_id")) else {}


# -- P3-282: the operational status (faculty only) -----------------------------------------------------------------------------------------------------------------------
def status_view(artifact: Mapping | None, record: Mapping | None, decision: Mapping | None) -> dict:
    """The operational authority status a faculty reviewer needs: case, grant, mode, session state, last authoritative minute and pressure, snapshot and lineage, artifact status, halt. It shows NO
    common consciousness as a state of the encounter; when a comparison is wanted it lives in the bundle's comparator, labelled nonauthoritative."""
    art, rec, dec = dict(artifact or {}), dict(record or {}), dict(decision or {})
    grant = dict(art.get("grant") or {})
    stored = dict(art.get("store") or {}) if isinstance(art.get("store"), Mapping) else {}
    halted = bool(art.get("halted") or rec.get("halted"))
    return _plain({
        "record_type": STATUS_TYPE, "version": VERSION,
        "case_id": art.get("case_id") or rec.get("case_id"), "environment": art.get("environment") or fr.ENVIRONMENT,
        "grant_id": grant.get("grant_id") or rec.get("grant_id") or dec.get("grant_id"), "grant_version": grant.get("grant_version") or dec.get("grant_version"),
        "authority_mode": art.get("authority_mode") or fr.AUTHORITY_MODE,
        "session_state": rec.get("lifecycle") or ("NO_EXPERIMENT_YET" if not art else art.get("experiment_state")),
        "last_authoritative_minute": rec.get("last_authoritative_minute"), "last_authoritative_pressure": rec.get("last_authoritative_pressure"),
        "snapshot_id": art.get("snapshot_id") or rec.get("snapshot_id"),
        # The lineage is the grant's own pair (the active core member's version AND its digest), with the historical Phase-2 closure digest named separately: the session record pairs the active
        # version with the closure digest, which would read as a lineage it is not (P3-251 labelling, declared in TD-146).
        "lineage": {"core_version": _core_lineage(grant).get("version_id"), "core_digest": _core_lineage(grant).get("digest"), "phase2_closure_digest": art.get("phase2_digest")},
        "artifact": {"digest": art.get("artifact_digest"), "stored": stored.get("stored") if stored else None, "minutes_recorded": len(art.get("minutes") or ())},
        "halt": {"halted": halted, "reason": rec.get("halt_reason") or art.get("halt_reason") or "", "stop_class": rec.get("stop_class") or ""},
        "faculty_review": {"enabled": bool(dec.get("enabled")), "single_process": dict(dec.get("single_process") or {}).get("held"), "allowlist": list(fr.ALLOWLIST)},
    })


# -- P3-283: the review bundle -----------------------------------------------------------------------------------------------------------------------------------
def _management_timeline(trace: Sequence) -> list:
    rows = []
    for entry in trace:
        item = dict(entry or {})
        summaries = [str(dict(s or {}).get("label") or dict(s or {}).get("type") or "") for s in (item.get("action_summaries") or ())]
        rows.append({"decision_time_min": item.get("decision_time_min"), "elapsed_minutes": item.get("elapsed_minutes"), "activity": item.get("activity_kind"),
                     "input": str(item.get("learner_input") or "")[:300], "status": item.get("execution_status"), "actions": [label for label in summaries if label][:8]})
    return rows


def _fates(rows: Any) -> list:
    out = []
    for row in (rows or ()):
        item = dict(row or {})
        out.append({key: str(value)[:120] for key, value in item.items() if key in ("order_id", "class", "kind", "fate", "action", "action_kind", "disposition", "submission_id") and value is not None})
    return out


def _overlay_rows(artifact: Mapping) -> list:
    overlay = dict(artifact.get("consciousness_overlay") or {})
    rows = [dict(row) for turn in (overlay.get("turns") or ()) for row in (dict(turn).get("rows") or ()) if dict(row).get("shown")]
    return [{"minute": row.get("minute"), "mental_status": row.get("mental_status"), "F": row.get("F"), "collapse_state": row.get("collapse_state")} for row in rows][:600]


def build(artifact: Mapping | None, *, record: Mapping | None = None, trace: Sequence = (), decision: Mapping | None = None, scenario_id: str | None = None) -> dict:
    """The review bundle of one faculty review encounter. Pure: the same inputs give the same bundle and the same ``bundle_id``. Never raises into a caller that checks ``problems``."""
    art, rec = dict(artifact or {}), dict(record or {})
    minutes = [dict(item) for item in (art.get("minutes") or ())]
    committed = [item for item in minutes if item.get("committed")]
    verification = ra.verify_artifact(art) if art else {}
    replay = ra.replay_site_artifact(art) if art else {}
    authority_view = {
        "authority_mode": art.get("authority_mode") or fr.AUTHORITY_MODE, "grant_id": dict(art.get("grant") or {}).get("grant_id") or rec.get("grant_id"), "snapshot_id": art.get("snapshot_id"),
        "lifecycle": rec.get("lifecycle"), "halted": bool(art.get("halted")), "halt_reason": rec.get("halt_reason") or art.get("halt_reason") or "", "stop_class": rec.get("stop_class") or "",
        "last_authoritative_minute": rec.get("last_authoritative_minute"), "last_authoritative_pressure": rec.get("last_authoritative_pressure"),
        "authoritative_pressure_timeline": [{"minute": item.get("minute"), **_pressure(item.get("common_pressures"))} for item in committed],
        "management_timeline": _management_timeline(trace),
        "action_dispositions": ([{"minute": item.get("minute"), "route": item.get("route"), "outcome": item.get("outcome"), "action_kinds": list(item.get("action_kinds") or ()),
                                  "fates": _fates(item.get("action_fates"))} for item in minutes]
                                + [{"minute": item.get("minute"), "route": item.get("route"), "outcome": item.get("outcome"), "action_kinds": list(item.get("action_kinds") or ()),
                                    "fates": _fates(item.get("action_fates"))} for item in (art.get("no_advance_turns") or ())]),
        "halt_events": [{"minute": item.get("minute"), "route": item.get("route"), "reason": item.get("failure_reason")} for item in minutes if item.get("outcome") == ra.ABORTED],
        "collapse_boundary": art.get("collapse_boundary"),
    }
    comparator = {
        "label": COMPARATOR_LABEL, "note": COMPARATOR_NOTE,
        "legacy_counterfactual_pressure_timeline": [{"minute": item.get("minute"), **_pressure(item.get("legacy_counterfactual"))} for item in committed],
        "differences_from_legacy": [{"minute": item.get("minute"), **{f"{key}_difference": (None if dict(item.get("common_pressures") or {}).get(key) is None or dict(item.get("legacy_counterfactual") or {}).get(key) is None
                                                                                          else round(float(dict(item["common_pressures"])[key]) - float(dict(item["legacy_counterfactual"])[key]), 2))
                                                                                for key in ("sbp", "dbp", "map")}} for item in committed],
        # the artifact's OWN claims about the overlay, never hard-coded: an artifact that claimed authority must show it (and ``claims_are_honest`` says whether it was allowed to)
        "consciousness_overlay_comparison": {"label": COMPARATOR_LABEL, "authority": bool(dict(art.get("consciousness_overlay") or {}).get("authority")),
                                             "resident_visible": bool(dict(art.get("consciousness_overlay") or {}).get("resident_visible")),
                                             "writes_mental_status": bool(dict(art.get("consciousness_overlay") or {}).get("writes_mental_status")), "rows": _overlay_rows(art),
                                             "snapshot_id": dict(art.get("consciousness_overlay") or {}).get("snapshot", {}).get("snapshot_id") if isinstance(dict(art.get("consciousness_overlay") or {}).get("snapshot"), Mapping) else None},
    }
    body = {
        "record_type": BUNDLE_TYPE, "version": VERSION,
        "encounter": {"case_id": art.get("case_id"), "encounter_id": art.get("encounter_id"), "attempt": art.get("attempt"), "experiment_id": art.get("experiment_id"), "family": art.get("family"),
                      "environment": art.get("environment"), "scenario_id": scenario_id},
        "authority_view": authority_view, "comparator": comparator,
        "evidence": {"artifact_digest": art.get("artifact_digest"), "artifact_id": (ras.artifact_id(art) if art else None), "minutes_recorded": len(minutes), "minutes_committed": len(committed),
                     "artifact_verification": {key: verification.get(key) for key in ("complete", "digest_matches", "label_matches_content", "claims_are_honest", "outcomes_consistent", "missing_fields")},
                     "replay": {key: replay.get(key) for key in ("reproduces", "verdict", "covers_every_committed_minute", "minutes_reconstructable", "minutes_recorded", "overlay_replay")},
                     "session_record_digest": rec.get("record_digest")},
        "faculty_review_configuration": {key: dict(decision or {}).get(key) for key in ("enabled", "authority_mode", "grant_id", "grant_version", "environment", "allowlist")},
        "limitations": list(LIMITATIONS),
        "statement": ("A faculty review bundle of a synthetic development encounter. Differences between the common authority and the legacy engine are evidence for review, not a score. "
                      "Not a clinical validation, a resident pilot or a production record."),
    }
    body = _plain(body)
    return {**body, "bundle_id": ra.digest_of(body)[:16]}


def _key_tokens(key: Any) -> list:
    """The lower-case words of a key: ``mean_absolute_error`` -> mean, absolute, error; ``meanAbsoluteError`` the same."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key))
    return [token for token in re.split(r"[^a-z0-9]+", spaced.lower()) if token]


def _grading_key(key: Any) -> bool:
    tokens = _key_tokens(key)
    joined = "_".join(tokens)
    return any(token in FORBIDDEN_BUNDLE_KEYS for token in tokens) or any(phrase in joined for phrase in FORBIDDEN_BUNDLE_PHRASES)


def bundle_problems(bundle: Mapping | None) -> list:
    """What is wrong with a bundle: not a bundle, its id does not recompute, it carries a grading key, it lacks the blinded split, it names no allowlisted case or a scenario that is not that case's.
    Empty means it holds. Structural only: whether the evidence it carries verified and replayed is ``evidence_problems``."""
    problems: list = []
    body = dict(bundle or {})
    if body.get("record_type") != BUNDLE_TYPE:
        return ["not a faculty review bundle"]
    claimed = body.get("bundle_id")
    rest = {key: value for key, value in body.items() if key != "bundle_id"}
    if claimed != ra.digest_of(_plain(rest))[:16]:
        problems.append("the bundle id does not recompute from its content")
    if not {"authority_view", "comparator", "evidence", "limitations"} <= set(body):
        problems.append("the bundle lacks one of its parts (authority view, comparator, evidence, limitations)")
    encounter = dict(body.get("encounter") or {})
    case_id = encounter.get("case_id")
    if not case_id:
        problems.append("the bundle names no case")
    elif not fr.case_allowed(case_id):
        problems.append("the bundle names a case outside the allowlist")
    scenario_id = encounter.get("scenario_id")
    if scenario_id is not None:
        scripted = fr.scenario(scenario_id)
        if scripted is None:
            problems.append("the bundle names a scenario that is not in the review set")
        elif scripted["case_id"] != case_id:
            problems.append("the bundle names a scenario that belongs to another case")

    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if _grading_key(key):
                    problems.append(f"the bundle carries a grading key: {path}{key}")
                walk(item, f"{path}{key}.")
        elif isinstance(value, (list, tuple)):
            for item in value:                       # the whole list: a grading key in the 51st row is as much a grade as in the first
                walk(item, path)

    walk(body)
    return problems


def evidence_problems(bundle: Mapping | None) -> list:
    """Why the evidence a bundle carries cannot be judged: the artifact did not verify, did not replay, or the bundle has none. A bundle of a failed artifact can still be WRITTEN (the failure is
    itself the evidence a reviewer must see); feedback on it is refused, because a judgement of pressures that fail their own checks is a judgement of nothing."""
    evidence = dict(dict(bundle or {}).get("evidence") or {})
    verification, replay = dict(evidence.get("artifact_verification") or {}), dict(evidence.get("replay") or {})
    problems = []
    if not evidence.get("artifact_digest"):
        problems.append("the bundle carries no artifact")
    if verification.get("digest_matches") is not True or verification.get("complete") is not True or verification.get("claims_are_honest") is not True:
        problems.append("the artifact does not verify (digest, completeness or honest claims)")
    if replay.get("reproduces") is not True:
        problems.append("the artifact does not replay to the pressures it recorded")
    return problems


def _bundles_dir(environ: Mapping[str, str] | None = None) -> Path | None:
    base = fr.review_root(environ)
    return None if base is None else base / "bundles"


def _create_only(path: Path, payload: str) -> dict:
    """Create ``path`` with ``payload`` atomically and only when it does not exist: the content is written to a private temporary file and LINKED into place, so the file appears complete or not at all
    (a crash cannot leave a truncated record under a real identity). An existing file is compared by CONTENT: the same content is the same record (idempotent), a different or unreadable one is not."""
    directory = path.parent
    temporary = directory / f".tmp-{os.getpid()}-{threading.get_ident()}-{path.name}"
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(str(temporary), str(path))
            return {"created": True, "same": True}
        except FileExistsError:
            try:
                same = json.loads(path.read_text(encoding="utf-8")) == json.loads(payload)
            except Exception:
                same = False
            return {"created": False, "same": same}
    finally:
        try:
            os.unlink(str(temporary))
        except OSError:
            pass


def write(bundle: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
    """Write one bundle, create-only and atomic. The same id is the same content, so a repeated write is idempotent. Returns ``{"stored", "path", "bundle_id", "why"}``; never raises."""
    result = {"stored": False, "path": "", "bundle_id": dict(bundle).get("bundle_id"), "why": ""}
    try:
        problems = bundle_problems(bundle)
        if problems:
            return {**result, "why": "; ".join(problems[:3])}
        directory = _bundles_dir(environ)
        if directory is None:
            return {**result, "why": "no faculty authority store is configured"}
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{dict(bundle)['encounter']['case_id']}__{bundle['bundle_id']}.json"
        if path.parent != directory:                       # the case is allowlisted (``bundle_problems``), so this cannot happen; it is checked, not assumed
            return {**result, "why": "the bundle path leaves the bundle directory"}
        outcome = _create_only(path, json.dumps(bundle, indent=1, sort_keys=True))
        if outcome["created"] or outcome["same"]:
            return {**result, "stored": True, "path": str(path)}
        return {**result, "path": str(path), "why": "a different or unreadable file already has this identity"}
    except Exception as error:
        return {**result, "why": f"the bundle could not be written ({type(error).__name__})"}


def load(bundle_id: str, *, environ: Mapping[str, str] | None = None) -> dict | None:
    """The stored bundle with this id, verified (its id recomputes), or None. Never raises."""
    try:
        directory = _bundles_dir(environ)
        if directory is None or not re.fullmatch(r"[0-9a-f]{16}", str(bundle_id or "")):
            return None
        for path in sorted(directory.glob(f"*__{bundle_id}.json")):
            body = json.loads(path.read_text(encoding="utf-8"))
            if not bundle_problems(body) and body.get("bundle_id") == bundle_id:
                return body
        return None
    except Exception:
        return None


# -- P3-284: the feedback schema -----------------------------------------------------------------------------------------------------------------------------------
OVERALL = ("ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT")
TIMING = ("TOO_EARLY", "APPROPRIATE", "TOO_LATE", "NOT_APPLICABLE", "CANNOT_JUDGE")
STAGE_BLINDED, STAGE_HALT, STAGE_COMPARATOR, STAGE_OVERALL = "BLINDED_AUTHORITY_ONLY", "HALT", "AFTER_COMPARATOR", "OVERALL"
REVIEWER_ROLES = ("faculty", "admin", "faculty_guest_reviewer")
QUESTIONS = (
    {"id": "Q1", "stage": STAGE_BLINDED, "text": "Did pressure evolve in a clinically coherent direction?", "choices": ("YES", "PARTLY", "NO", "CANNOT_JUDGE")},
    {"id": "Q2", "stage": STAGE_BLINDED, "text": "Did deterioration occur too early, appropriately or too late?", "choices": TIMING},
    {"id": "Q3", "stage": STAGE_BLINDED, "text": "Did the response to treatment begin too early, appropriately or too late?", "choices": TIMING},
    {"id": "Q4", "stage": STAGE_BLINDED, "text": "Were the magnitudes of the changes plausible for the authored scenario?", "choices": ("PLAUSIBLE", "TOO_SMALL", "TOO_LARGE", "MIXED", "CANNOT_JUDGE")},
    {"id": "Q5", "stage": STAGE_BLINDED, "text": "Would any pressure trajectory mislead a resident?", "choices": ("NO", "POSSIBLY", "YES", "CANNOT_JUDGE")},
    {"id": "Q6", "stage": STAGE_HALT, "text": "Did the halt occur at an understandable point?", "choices": ("YES", "NO", "NOT_APPLICABLE")},
    {"id": "Q7", "stage": STAGE_HALT, "text": "Did the halt behaviour create educational confusion?", "choices": ("NO", "SOME", "YES", "NOT_APPLICABLE")},
    {"id": "Q8", "stage": STAGE_COMPARATOR, "text": "Did the common consciousness comparison appear plausible?", "choices": ("YES", "PARTLY", "NO", "CANNOT_JUDGE")},
    {"id": "Q9", "stage": STAGE_COMPARATOR, "text": "Was there any contradiction between pressure, consciousness and management?", "choices": ("NONE", "MINOR", "MAJOR", "CANNOT_JUDGE")},
    {"id": "Q10", "stage": STAGE_OVERALL, "text": "Overall.", "choices": OVERALL},
)
SCHEMA = {"record_type": "PHASE3_FACULTY_REVIEW_FEEDBACK_SCHEMA", "version": VERSION, "questions": [dict(q, choices=list(q["choices"])) for q in QUESTIONS],
          "fields": ["reviewer_role", "case_id", "scenario_id", "bundle_id", "comparator_revealed", "comments"], "overall_choices": list(OVERALL), "max_comment_characters": 4000,
          "notice": "These are synthetic development cases: do not enter real-patient data."}
#: Identifiers a comment may not carry (synthetic cases: no real-patient data). A TRIPWIRE, not a proof: it catches the common shapes (an e-mail, an identifier tag followed by a number, a date, a
#: phone-like number, a long number, a title followed by a surname) after normalising Unicode and removing invisible characters; it cannot recognise an unlabelled name, and says so.
_SENSITIVE = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    re.compile(r"\b(?:mrn|dni|nie|rut|ssn|nhs|cpf|curp|dob)[\s:#._-]*\d", re.IGNORECASE),
    re.compile(r"\b(?:patient|pt|chart|record|file)\s*(?:id|no\.?|number|#)\s*[:#]?\s*\w*\d{3,}", re.IGNORECASE),
    re.compile(r"\b(?:date of birth|born|fecha de nacimiento|nacid[oa])\b[^.\n]{0,24}\d", re.IGNORECASE),
    re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-](?:\d{4}|\d{2})\b"),
    re.compile(r"\+?\d{0,3}[\s.-]?\(?\d{2,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}\b"),
    re.compile(r"\b\d{8,}\b"),
    re.compile(r"(?i:\b(?:mr|mrs|ms|miss|dr|dra|sr|sra|prof)\b\.?)\s+[A-Z][a-z]{2,}"),
)
BLIND_STAGES = (STAGE_BLINDED, STAGE_HALT)


def _normalised(text: str) -> str:
    """NFKC and no invisible (format) or control characters: ``m<zero-width>rn`` is ``mrn`` to this filter as it is to a reader."""
    folded = unicodedata.normalize("NFKC", str(text or ""))
    return "".join(char for char in folded if unicodedata.category(char) not in ("Cf", "Cc") or char in "\n\t")


def feedback_problems(payload: Mapping | None, bundle: Mapping | None) -> list:
    """Why a feedback form is refused. Empty means it can be stored. Bound to ONE bundle: case, scenario, encounter and bundle id must be that bundle's, the bundle must hold and its evidence must
    verify and replay, only the ten questions may be answered, and a feedback that says the comparator was revealed must carry the blinded answers as they stood AT the reveal and unchanged."""
    body, problems = dict(payload or {}), []
    if bundle_problems(bundle):
        return ["the bundle the feedback is for does not verify"]
    failed = evidence_problems(bundle)
    if failed:
        return ["the evidence of the bundle cannot be judged: " + "; ".join(failed)]
    encounter = dict(dict(bundle).get("encounter") or {})
    halted = bool(dict(dict(bundle).get("authority_view") or {}).get("halted"))
    if body.get("bundle_id") != dict(bundle).get("bundle_id"):
        problems.append("the feedback names another bundle")
    if body.get("case_id") != encounter.get("case_id"):
        problems.append("the feedback names another case")
    if (body.get("scenario_id") or None) != (encounter.get("scenario_id") or None):
        problems.append("the feedback names another scenario")
    if body.get("reviewer_role") not in REVIEWER_ROLES:
        problems.append("the reviewer role is not one of " + ", ".join(REVIEWER_ROLES))
    answers = dict(body.get("answers") or {})
    known = {question["id"] for question in QUESTIONS}
    for unknown in sorted(str(key) for key in answers if key not in known):
        problems.append(f"{unknown[:20]!r} is not one of the ten questions")
    revealed = bool(body.get("comparator_revealed"))
    for question in QUESTIONS:
        value = answers.get(question["id"])
        if value is None or value == "":
            if question["stage"] == STAGE_HALT and not halted:
                continue
            if question["stage"] == STAGE_COMPARATOR and not revealed:
                continue
            problems.append(f"{question['id']} is not answered")
        elif value not in question["choices"]:
            problems.append(f"{question['id']} has an answer outside its choices")
        elif question["stage"] == STAGE_COMPARATOR and not revealed:
            problems.append(f"{question['id']} was answered before the comparator was revealed")
        elif question["stage"] == STAGE_HALT and not halted and value != "NOT_APPLICABLE":
            problems.append(f"{question['id']} is a halt question and this encounter did not halt")
    blind_now = {question["id"]: answers.get(question["id"]) for question in QUESTIONS if question["stage"] in BLIND_STAGES and answers.get(question["id"])}
    snapshot = body.get("blinded_answers_at_reveal")
    if revealed:
        if not isinstance(snapshot, Mapping):
            problems.append("the comparator is said to be revealed but the blinded answers at the reveal are not recorded")
        elif {str(key): value for key, value in snapshot.items()} != blind_now:
            problems.append("the blinded answers changed after the comparator was revealed")
    elif snapshot:
        problems.append("blinded answers at a reveal are recorded but the comparator was not revealed")
    comment = str(body.get("comments") or "")
    if len(comment) > SCHEMA["max_comment_characters"]:
        problems.append("the comments are too long")
    seen = _normalised(comment)
    if any(pattern.search(seen) for pattern in _SENSITIVE):
        problems.append("the comments look like they carry personal or real-patient identifiers (a number, a date, an identifier or a titled name): these are synthetic development cases")
    if answers.get("Q5") in ("POSSIBLY", "YES") and not comment.strip():
        problems.append("Q5 asks for a comment when a trajectory could mislead a resident")
    return problems


def store_feedback(payload: Mapping, bundle: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
    """Validate and write one feedback record, create-only and atomic, in the review directory next to its bundle. The bundle must ALREADY be stored, byte for byte what the feedback judged: feedback
    on a bundle nobody can open is feedback on nothing. Never raises."""
    result = {"stored": False, "path": "", "feedback_id": None, "problems": []}
    try:
        problems = feedback_problems(payload, bundle)
        if problems:
            return {**result, "problems": problems}
        base = fr.review_root(environ)
        if base is None:
            return {**result, "problems": ["no faculty authority store is configured"]}
        on_disk = load(str(dict(bundle).get("bundle_id") or ""), environ=environ)
        if on_disk is None or on_disk != json.loads(json.dumps(dict(bundle), default=str)):
            return {**result, "problems": ["the bundle the feedback is for is not stored (or the stored one differs): create the review bundle first"]}
        revealed = bool(payload.get("comparator_revealed"))
        known = {question["id"] for question in QUESTIONS}
        body = _plain({"record_type": FEEDBACK_TYPE, "version": VERSION, "bundle_id": payload["bundle_id"], "case_id": payload["case_id"], "scenario_id": payload.get("scenario_id"),
                       "reviewer_role": payload["reviewer_role"], "comparator_revealed": revealed,
                       "blinded_answers_at_reveal": (dict(payload.get("blinded_answers_at_reveal") or {}) if revealed else None),
                       "answers": {key: value for key, value in dict(payload.get("answers") or {}).items() if key in known},
                       "comments": str(payload.get("comments") or ""), "statement": "Synthetic development case. Not a clinical validation."})
        identifier = ra.digest_of(body)[:16]
        directory = base / "feedback"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{payload['bundle_id']}__{identifier}.json"
        outcome = _create_only(path, json.dumps({**body, "feedback_id": identifier}, indent=1, sort_keys=True))
        if outcome["created"] or outcome["same"]:
            return {**result, "stored": True, "path": str(path), "feedback_id": identifier}
        return {**result, "path": str(path), "problems": ["a different or unreadable file already has this feedback identity"]}
    except Exception as error:
        return {**result, "problems": [f"the feedback could not be written ({type(error).__name__})"]}
