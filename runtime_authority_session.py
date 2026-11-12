"""P3-250 to P3-260: the authority SESSION lifecycle, its persistent record and the effective-stop guard (development only).

WHAT THIS IS. After a REAL development-authority commit (the GI pressure experiment, ``runtime_pressure_grant``), a later authority transaction may fail and the experiment becomes
``INVALID_FOR_CONTINUATION``. Until this module the legacy engine simply kept running the encounter (declared, advisory). The faculty decision FD-STOP-01 to FD-STOP-09 makes the stop
EFFECTIVE: once authority has begun and the experiment is invalid, the experimental encounter session may not advance clinical time or take a management action until an operator
resolves it (this cycle: abandon / block only). This is EXPERIMENT LIFECYCLE CONTROL. It is not patient death, not clinical terminality, not a common-core terminal state and not a
resident-facing medical outcome: nothing here writes a patient field, a physiology value, a score or a word a resident reads as a clinical event.

TWO DIFFERENT STATE MACHINES (never confused):

* the TRANSACTION (``runtime_authority.AuthorityTransaction``): OPEN, COMMITTED or ABORTED, one minute at a time;
* the encounter's AUTHORITY SESSION (here): where the whole experiment is in its life -- NOT_STARTED, PREAUTHORITY, ACTIVE_AUTHORITY, PRECOMMIT_ABORT, INVALID_FOR_CONTINUATION or
  COMPLETED_AUTHORITY -- derived from the experiment artifact (the single source of truth), kept in the session store and carried with a saved encounter.

THE RULE (FD-STOP-02/03/04). ``authority_began`` (at least one REAL commit) AND halted  ->  INVALID_FOR_CONTINUATION  ->  ``continuation_allowed = False``, no silent legacy fallback.
A halt BEFORE the first commit is PRECOMMIT_ABORT: the untouched legacy encounter may continue (the preauthority development semantics), and that distinction stays explicit.

FAIL CLOSED. Whenever the sources of truth disagree (the live site, the session record, the session artifact), or one cannot be read, or a record does not verify, the answer is DENY.
The less restrictive claim is never chosen automatically. With every flag off and no authority key in the session the guard is one handful of dictionary lookups and allows.

Nothing in this module imports the page, the engine or the common core.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import runtime_authority as ra

VERSION = "P3-251"
RECORD_TYPE = "phase3_authority_session"
#: Where the record lives in the page's session store. It is in ``curriculum_runtime.SESSION_FIELDS``: it travels with a saved encounter, so a reopened encounter keeps it.
SESSION_KEY = ra.SESSION_KEY

# -- the lifecycle (P3-250A) ----------------------------------------------------------------------------------------------------------------------------------
NOT_STARTED = "NOT_STARTED"                              # no authority experiment in this encounter (flags off, case not eligible, or the gate refused)
PREAUTHORITY = "PREAUTHORITY"                            # a site is open, nothing committed, not halted
ACTIVE_AUTHORITY = "ACTIVE_AUTHORITY"                    # at least one REAL commit, not halted
PRECOMMIT_ABORT = "PRECOMMIT_ABORT"                      # halted BEFORE the first commit: the legacy encounter is untouched and may continue
INVALID_FOR_CONTINUATION = "INVALID_FOR_CONTINUATION"    # halted AFTER at least one REAL commit (collapse boundary, unsupported action, lineage, replay, validation, persistence, a resume...)
COMPLETED_AUTHORITY = "COMPLETED_AUTHORITY"              # the encounter was closed with the experiment not halted
LIFECYCLE = (NOT_STARTED, PREAUTHORITY, ACTIVE_AUTHORITY, PRECOMMIT_ABORT, INVALID_FOR_CONTINUATION, COMPLETED_AUTHORITY)
#: The ONLY moves. INVALID_FOR_CONTINUATION, PRECOMMIT_ABORT and COMPLETED_AUTHORITY are terminal for the session: nothing resumes a session by itself.
TRANSITIONS = {
    NOT_STARTED: (NOT_STARTED, PREAUTHORITY),
    PREAUTHORITY: (PREAUTHORITY, ACTIVE_AUTHORITY, PRECOMMIT_ABORT, COMPLETED_AUTHORITY),
    ACTIVE_AUTHORITY: (ACTIVE_AUTHORITY, INVALID_FOR_CONTINUATION, COMPLETED_AUTHORITY),
    PRECOMMIT_ABORT: (PRECOMMIT_ABORT,),
    INVALID_FOR_CONTINUATION: (INVALID_FOR_CONTINUATION,),
    COMPLETED_AUTHORITY: (COMPLETED_AUTHORITY,),
}
#: The lifecycle states from which the session may continue. Only an INVALID session is stopped; the others are governed by the encounter's own lifecycle.
STOPPED_STATES = (INVALID_FOR_CONTINUATION,)

# -- why a session stopped ------------------------------------------------------------------------------------------------------------------------------------
STOP_COLLAPSE_BOUNDARY = "COLLAPSE_BOUNDARY"
STOP_WINDOW_CLOSED = "WINDOW_CLOSED"
STOP_UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
STOP_GATE_OR_LINEAGE = "GATE_OR_LINEAGE"
STOP_VALIDATION = "VALIDATION"
STOP_REPLAY_OR_ARTIFACT = "REPLAY_OR_ARTIFACT"
STOP_PERSISTENCE = "ARTIFACT_PERSISTENCE"
STOP_RESUMED = "RESUMED_WITHOUT_SITE"
STOP_CONFIGURATION = "CONFIGURATION_CHANGED"
STOP_STALE_OR_CONFLICTING = "STALE_OR_CONFLICTING_STATE"
STOP_UNREADABLE = "STATE_UNREADABLE"
STOP_INTERNAL = "INTERNAL_ERROR"
STOP_OTHER = "OTHER"

# -- what an operator may do (FD-STOP-06) ---------------------------------------------------------------------------------------------------------------------
#: Only abandoning is required and implemented. Nothing resumes the session; nothing rolls back an already-authoritative state.
OPERATOR_RESOLUTIONS = ("ABANDON_EXPERIMENT",)
FUTURE_OPERATOR_RESOLUTIONS = ("RESET_FROM_PREAUTHORITY_SNAPSHOT", "START_NEW_ENCOUNTER")

# -- the operations of the page (P3-254A) ---------------------------------------------------------------------------------------------------------------------
READ_ONLY = "READ_ONLY"
ENCOUNTER_MUTATING = "ENCOUNTER_MUTATING"
CLINICAL_TIME_ADVANCING = "CLINICAL_TIME_ADVANCING"
#: Leaving the experimental session (abandon, reset, return to the dashboard): the operator's way out, and the only thing besides reading that survives a stop.
LEAVES_THE_SESSION = "LEAVES_THE_SESSION"
OPERATION_CLASSES = (READ_ONLY, ENCOUNTER_MUTATING, CLINICAL_TIME_ADVANCING, LEAVES_THE_SESSION)
OPERATIONS = {
    # reading
    "render_room": READ_ONLY, "view_chart": READ_ONLY, "view_results": READ_ONLY, "view_ecg_recording": READ_ONLY, "view_review": READ_ONLY, "view_authority_status": READ_ONLY,
    # information activities that cost clinical time (spend_clinical_time)
    "history_question": CLINICAL_TIME_ADVANCING, "history_topic": CLINICAL_TIME_ADVANCING, "examination": CLINICAL_TIME_ADVANCING,
    # orders: the order turn runs the engine (it may advance time by zero or more minutes: it is classified by what it CAN do)
    "order_submission": CLINICAL_TIME_ADVANCING, "guided_submission": CLINICAL_TIME_ADVANCING, "reasoning_followup": CLINICAL_TIME_ADVANCING,
    "clarification_answer": CLINICAL_TIME_ADVANCING, "held_order_release": CLINICAL_TIME_ADVANCING,
    # zero-minute operations that still alter the encounter
    "ecg_acquisition": ENCOUNTER_MUTATING, "cancel_pending_orders": ENCOUNTER_MUTATING, "retrospective_explanation": ENCOUNTER_MUTATING,
    "complete_encounter": ENCOUNTER_MUTATING, "finish_encounter": ENCOUNTER_MUTATING,
    # the engine entry points the page reaches (the chokepoints)
    "clinical_time": CLINICAL_TIME_ADVANCING, "order_execution": CLINICAL_TIME_ADVANCING,
    # the operator's way out
    "abandon_experiment": LEAVES_THE_SESSION, "reset_scenario": LEAVES_THE_SESSION, "return_to_dashboard": LEAVES_THE_SESSION,
}

#: What the page says when it stops. OPERATIONAL, development-scoped, and free of any clinical outcome: no patient is dead, arrested or terminal.
NOTICE_HEADLINE = "DEVELOPMENT AUTHORITY EXPERIMENT HALTED"
NOTICE_BODY = ("This experimental encounter session cannot continue: no further clinical time or management actions are available in it. "
               "To start a new one, end this attempt without completing review (or reset the scenario).")
FORBIDDEN_NOTICE_WORDS = ("dead", "death", "died", "arrest", "terminal", "dying", "deceased", "cardiac", "unresponsive", "obtunded")


AuthoritySessionStopped = ra.AuthoritySessionStopped


# -- the persistent record (P3-251) ---------------------------------------------------------------------------------------------------------------------------
def lifecycle_of_artifact(artifact: Mapping | None, *, encounter_ended: bool = False) -> str:
    """Where the experiment is in its life, read from its artifact alone (the single source of truth). An empty artifact is NOT_STARTED."""
    body = dict(artifact or {})
    if not body or body.get("artifact") != "phase3_authority_experiment":
        return NOT_STARTED
    committed = bool([record for record in (body.get("minutes") or []) if dict(record).get("committed")])
    if body.get("halted"):
        return INVALID_FOR_CONTINUATION if committed else PRECOMMIT_ABORT
    if encounter_ended:
        return COMPLETED_AUTHORITY
    return ACTIVE_AUTHORITY if committed else PREAUTHORITY


def stop_class_of(reason: str) -> str:
    """Why the experiment stopped, as a closed vocabulary (the reason text is kept too)."""
    text = str(reason or "")
    pairs = ((ra.COLLAPSE_BOUNDARY_REACHED, STOP_COLLAPSE_BOUNDARY), (ra.WINDOW_CLOSED, STOP_WINDOW_CLOSED), (ra.COLLAPSE_BOUNDARY_NOT_VERIFIABLE, STOP_COLLAPSE_BOUNDARY),
             (ra.UNSUPPORTED_AUTHORITY_ACTION, STOP_UNSUPPORTED_ACTION), (ra.PROVENANCE_CONTRADICTION, STOP_UNSUPPORTED_ACTION),
             (ra.GATE_REFUSED, STOP_GATE_OR_LINEAGE), (ra.VALIDATION_REFUSED, STOP_VALIDATION), (ra.RESUMED_WITHOUT_SITE, STOP_RESUMED),
             (ra.CONFIGURATION_CHANGED, STOP_CONFIGURATION), (ra.ARTIFACT_PERSISTENCE_FAILED, STOP_PERSISTENCE), ("SITE_ERROR", STOP_INTERNAL), ("ARTIFACT_ERROR", STOP_INTERNAL),
             (ra.COMMIT_REFUSED, STOP_REPLAY_OR_ARTIFACT), (ra.OUT_OF_DOMAIN_WRITE, STOP_REPLAY_OR_ARTIFACT), (ra.MINUTE_ALREADY_COMMITTED, STOP_REPLAY_OR_ARTIFACT),
             (ra.NO_COMMON_CANDIDATE, STOP_REPLAY_OR_ARTIFACT), (ra.MINUTE_NOT_COMPARED, STOP_REPLAY_OR_ARTIFACT))
    for needle, name in pairs:
        if needle and needle in text:
            return name
    return STOP_OTHER if text else ""


def session_record_of(artifact: Mapping | None, *, encounter_ended: bool = False) -> dict:
    """The authority-session record of an experiment artifact: everything the stop guard needs to know, and nothing of the patient. Never raises.

    It holds NO consciousness: the common consciousness is a nonauthoritative overlay and is not part of this record."""
    body = dict(artifact or {})
    minutes = [dict(record) for record in (body.get("minutes") or [])]
    committed = [record for record in minutes if record.get("committed")]
    failed = next((record for record in minutes if record.get("outcome") == ra.ABORTED), None)
    lifecycle = lifecycle_of_artifact(body, encounter_ended=encounter_ended)
    grant = dict(body.get("grant") or {})
    real = body.get("authority_label") == ra.REAL_PRESSURE_LABEL
    last = committed[-1] if committed else None
    halted = bool(body.get("halted"))
    reason = str(body.get("halt_reason") or "")
    # the effective stop applies to a REAL development-authority session; a site opened with a TEST-ONLY point keeps the advisory behaviour it had before the grant existed
    allowed = not (real and lifecycle in STOPPED_STATES)
    out = {
        "record_type": RECORD_TYPE, "version": VERSION, "lifecycle": lifecycle, "continuation_allowed": allowed,
        "stop_policy": "EFFECTIVE_STOP" if real else "ADVISORY_TEST_ONLY",
        "legacy_fallback_allowed": False if (real and halted and committed) else True,
        "authority_began": bool(committed), "last_authoritative_minute": (None if last is None else ra._as_int(last.get("minute"))),
        "last_authoritative_pressure": (None if last is None else dict(last.get("common_pressures") or {}) or None),
        "grant_id": grant.get("grant_id"), "grant_fingerprint": grant.get("fingerprint"), "authority_mode": body.get("authority_mode"),
        "case_id": body.get("case_id"), "family": body.get("family"), "snapshot_id": body.get("snapshot_id"),
        "lineage": {"version_id": grant.get("core_version"), "digest": body.get("phase2_digest")},
        "encounter_id": body.get("encounter_id"), "experiment_id": body.get("experiment_id"), "attempt": body.get("attempt"),
        "halted": halted, "halt_reason": reason, "stop_class": stop_class_of(reason) if halted else "",
        "failed_minute": (None if failed is None else ra._as_int(failed.get("minute"))),
        "failed_operation": (None if failed is None else {"route": failed.get("route"), "submission_id": failed.get("submission_id"),
                                                          "action_kinds": list(failed.get("action_kinds") or ()), "reason": str(failed.get("failure_reason") or "")}),
        "last_artifact": {"artifact_digest": body.get("artifact_digest"), "minutes_recorded": len(minutes)},
        "authority_label": body.get("authority_label"),
    }
    return {**out, "record_digest": ra.digest_of(out)}


def invalidate_record(record: Mapping, reason: str, stop_class: str) -> dict:
    """The same session record, now INVALID_FOR_CONTINUATION for ``reason`` (the stop of a session whose site was lost). Only a REAL (effective-stop) record can be invalidated."""
    body = {key: value for key, value in dict(record).items() if key != "record_digest"}
    body.update({"lifecycle": INVALID_FOR_CONTINUATION, "continuation_allowed": False, "legacy_fallback_allowed": False, "halted": True, "halt_reason": reason, "stop_class": stop_class})
    return {**body, "record_digest": ra.digest_of(body)}


def record_problems(record: Mapping | None) -> list:
    """Every reason a session record is not a record this module wrote and left unchanged. Empty means it verifies."""
    problems: list = []
    try:
        body = dict(record or {})
        if body.get("record_type") != RECORD_TYPE:
            return ["not an authority-session record"]
        digest = body.pop("record_digest", None)
        if digest != ra.digest_of(body):
            problems.append("the record digest does not recompute")
        lifecycle = body.get("lifecycle")
        if lifecycle not in LIFECYCLE:
            problems.append(f"unknown lifecycle {lifecycle!r}")
        real = body.get("stop_policy") == "EFFECTIVE_STOP"
        if body.get("continuation_allowed") is not (not (real and lifecycle in STOPPED_STATES)):
            problems.append("continuation_allowed is not what the lifecycle and the policy give")
        if bool(body.get("authority_began")) != (body.get("last_authoritative_minute") is not None):
            problems.append("authority_began is not what the last authoritative minute says")
        if lifecycle == INVALID_FOR_CONTINUATION and not (body.get("halted") and body.get("authority_began")):
            problems.append("an INVALID session is a halted session that began")
        if lifecycle == PRECOMMIT_ABORT and (not body.get("halted") or body.get("authority_began")):
            problems.append("a PRECOMMIT_ABORT session is halted and never began")
        if lifecycle in (ACTIVE_AUTHORITY,) and (body.get("halted") or not body.get("authority_began")):
            problems.append("an ACTIVE session began and is not halted")
        if body.get("legacy_fallback_allowed") is not (False if (real and body.get("halted") and body.get("authority_began")) else True):
            problems.append("legacy_fallback_allowed does not follow the stop")
    except Exception as error:
        problems.append(f"{type(error).__name__}: {error}")
    return problems


def replay_session_record(artifact: Mapping | None, record: Mapping | None = None) -> dict:
    """P3-259A: rebuild the authority-session record FROM THE ARTIFACT ALONE and compare it with a stored one (or just verify the artifact's own story). It must reproduce the last valid
    authoritative state (minute and pressure), the failure (minute and operation), the halt reason and the continuation prohibition; the artifact itself must replay. Never raises."""
    out = {"reproduces": False, "mismatches": [], "rederived": None}
    try:
        derived = session_record_of(artifact)
        out["rederived"] = derived
        replay = ra.replay_site_artifact(artifact)
        if not replay.get("reproduces"):
            out["mismatches"].append("the artifact does not replay")
        committed = [dict(row) for row in (dict(artifact or {}).get("minutes") or []) if dict(row).get("committed")]
        if committed:
            rows = [row for row in replay.get("minutes", []) if row.get("committed")]
            written = dict(committed[-1].get("written_candidate") or {})
            last = dict(derived.get("last_authoritative_pressure") or {})
            if not rows or {k: written.get(k) for k in ("sbp", "dbp")} != {k: last.get(k) for k in ("sbp", "dbp")}:
                out["mismatches"].append("the last authoritative pressure is not the artifact's last committed one")
            if rows and not (rows[-1].get("written_matches") and rows[-1].get("pressures_match")):
                out["mismatches"].append("the last authoritative minute does not replay")
        if derived.get("lifecycle") in STOPPED_STATES and derived.get("stop_policy") == "EFFECTIVE_STOP":
            if derived.get("continuation_allowed") is not False:
                out["mismatches"].append("an invalid real session does not forbid continuation")
            halt = replay.get("halt_reason_replay") or {}
            if not halt.get("reproduces"):
                out["mismatches"].append("the halt reason does not replay")
        if record is not None:
            body = {k: v for k, v in dict(record).items() if k not in ("record_digest", "last_artifact")}
            expected = {k: v for k, v in derived.items() if k not in ("record_digest", "last_artifact")}
            for key in sorted(set(body) | set(expected)):
                if body.get(key) != expected.get(key):
                    out["mismatches"].append(f"the stored record's {key} is not the one the artifact gives")
        out["reproduces"] = not out["mismatches"]
    except Exception as error:
        out["mismatches"].append(f"{type(error).__name__}: {error}")
    return out


def transition_ok(before: str, after: str) -> bool:
    """Whether a lifecycle may move from ``before`` to ``after`` (no hidden transition: INVALID never returns to ACTIVE or to a legacy continuation)."""
    return after in TRANSITIONS.get(before, ())


# -- the guard (P3-252) ---------------------------------------------------------------------------------------------------------------------------------------
def _asked(live: Mapping[str, str]) -> bool:
    return str(live.get(ra.AUTHORITY_FLAG, "") or "").strip().lower() == ra.MODE_LIMITED_COMMON_AUTHORITY


def _configuration_holds(claim: Mapping, live: Mapping[str, str]) -> bool:
    """Whether the live configuration still asks for the experiment the claim describes: the authority mode and the snapshot the site was opened with."""
    return _asked(live) and str(live.get(ra.SNAPSHOT_FLAG, "") or "").strip() == str(claim.get("snapshot_id") or "")


def _decision(allowed: bool, lifecycle: str, reason: str, *, stop_class: str = "", record: Mapping | None = None, sources: Mapping | None = None) -> dict:
    record = dict(record or {})
    return {"allowed": bool(allowed), "lifecycle": lifecycle, "reason": reason, "stop_class": stop_class,
            "authority_began": bool(record.get("authority_began")), "last_authoritative_minute": record.get("last_authoritative_minute"),
            "last_authoritative_pressure": record.get("last_authoritative_pressure"), "halt_reason": record.get("halt_reason") or "",
            "failed_minute": record.get("failed_minute"), "failed_operation": record.get("failed_operation"),
            "legacy_fallback_allowed": bool(record.get("legacy_fallback_allowed", True)) if allowed else False,
            "operator_resolutions": list(OPERATOR_RESOLUTIONS) if not allowed else [],
            "notice": (None if allowed else {"headline": NOTICE_HEADLINE, "body": NOTICE_BODY}),
            "sources": dict(sources or {})}


def _belongs(record: Mapping | None, state: Mapping) -> bool:
    """Whether a session record is about THIS encounter: the same case, and a state that has not gone back before the experiment's last authoritative minute. A record of an
    earlier encounter (a new patient at minute 0, another case) is stale and says nothing about this one."""
    body = dict(record or {})
    try:
        from clinical_core import legacy_adapter
        if body.get("case_id") and str(legacy_adapter.engine_case_id(dict(state))) != str(body.get("case_id")):
            return False
        minute = ra._as_int(dict(state).get("sim_time"))
        last = body.get("last_authoritative_minute")
        if last is not None and minute < ra._as_int(last):
            return False
        if minute == 0 and body.get("authority_began"):
            return False
        return True
    except Exception:
        return True            # cannot tell: it belongs (the restrictive choice)


def continuation_guard(store: Any, state: Mapping | None, *, environ: Mapping[str, str] | None = None, encounter_ended: bool = False) -> dict:
    """AUTHORITY_SESSION_CAN_CONTINUE: may this experimental encounter session take another clinical step? Consulted BEFORE any operation that can advance clinical time, take a
    management action, release a held action, alter the patient or start another authority transaction. Never raises; any doubt is a DENY.

    Sources, strongest claim wins and disagreement denies: the live site, the session record (which travels with a saved encounter), the session artifact. With none of them and
    every flag off the encounter is a plain legacy one (one handful of lookups). A saved encounter that comes back with committed authority pressures and NO site (nothing carried a record)
    is recognised in the durable store by case, minute and committed pressures, and is INVALID: it never silently continues on the legacy engine."""
    live = os.environ if environ is None else environ
    try:
        site = store.get(ra.SITE_KEY)
        record = store.get(SESSION_KEY)
        artifact = store.get(ra.ARTIFACT_KEY)
        halted_for = store.get(ra.HALTED_KEY)
    except Exception as error:
        return _decision(False, INVALID_FOR_CONTINUATION, f"the authority-session state cannot be read ({type(error).__name__})", stop_class=STOP_UNREADABLE)
    asked = _asked(live)
    if site is None and record is None and artifact is None and halted_for is None and not asked:
        return _decision(True, NOT_STARTED, "no authority experiment in this encounter")
    try:
        state_map = dict(state or {})
        claims: dict = {}
        if site is not None:
            if not hasattr(site, "session_record") or not site.is_for(state_map):
                site = None          # a site of another encounter says nothing about this one (the page clears it on the next arrival)
            else:
                claims["site"] = site.session_record(encounter_ended=encounter_ended)
        if record is not None:
            problems = record_problems(record)
            if problems:
                return _decision(False, INVALID_FOR_CONTINUATION, "the authority-session record does not verify: " + "; ".join(problems[:3]), stop_class=STOP_STALE_OR_CONFLICTING, record=record)
            if _belongs(record, state_map):
                claims["record"] = dict(record)
        if artifact:
            if artifact.get("artifact") == "phase3_authority_experiment" and _belongs({"case_id": artifact.get("case_id"), "last_authoritative_minute": None, "authority_began": False}, state_map):
                from_artifact = session_record_of(artifact, encounter_ended=encounter_ended)
                if _belongs(from_artifact, state_map):
                    claims["artifact"] = from_artifact
        if not claims:
            # no claim about THIS encounter. A saved encounter that comes back with no site and no record is checked against the durable store (flags on only: nothing else can have run)
            if asked and ra._as_int(state_map.get("sim_time")) > 0:
                marker = ra.note_resume_without_site(state_map, store, live)
                if marker is not None:
                    record = session_record_of(marker)
                    store[SESSION_KEY] = record
                    return _decision(False, INVALID_FOR_CONTINUATION, str(marker.get("halt_reason")), stop_class=STOP_RESUMED, record=record, sources={"durable": record["lifecycle"]})
                matched = ra.durable_match(state_map, live)
                if matched is not None and matched.get("authority_began") and matched.get("halted"):
                    return _decision(False, INVALID_FOR_CONTINUATION, "the durable store holds a halted authority experiment for this encounter", stop_class=STOP_RESUMED,
                                     record=matched, sources={"durable": matched["lifecycle"]})
            return _decision(True, NOT_STARTED, "no authority experiment in this encounter")
        # fail closed on disagreement: the claims must tell the same story about whether authority began, where it got to and whether it halted
        shapes = {(bool(claim.get("authority_began")), claim.get("last_authoritative_minute"), bool(claim.get("halted"))) for claim in claims.values()}
        sources = {name: claim.get("lifecycle") for name, claim in claims.items()}
        strongest = next((claim for claim in claims.values() if claim.get("lifecycle") in STOPPED_STATES and claim.get("stop_policy") == "EFFECTIVE_STOP"), None)
        if strongest is not None:
            return _decision(False, INVALID_FOR_CONTINUATION, str(strongest.get("halt_reason") or "the experiment is invalid for continuation"),
                             stop_class=str(strongest.get("stop_class") or STOP_OTHER), record=strongest, sources=sources)
        if len(shapes) > 1:
            return _decision(False, INVALID_FOR_CONTINUATION, "the sources of the authority-session state disagree: " + ", ".join(f"{k}={v}" for k, v in sorted(sources.items())),
                             stop_class=STOP_STALE_OR_CONFLICTING, record=next(iter(claims.values())), sources=sources)
        claim = claims.get("site") or claims.get("record") or next(iter(claims.values()))
        lifecycle = claim.get("lifecycle")
        if "site" in claims and claim.get("stop_policy") == "EFFECTIVE_STOP" and lifecycle == ACTIVE_AUTHORITY and not _configuration_holds(claim, live):
            # P3-262 (review MEDIUM-2): a REAL experiment that began is ACTIVE and the authority configuration that opened it is no longer asked for (a flag removed in the process).
            # The clock route used to carry on on the legacy engine until the next ORDER turn noticed; the guard now says it on every route.
            reason = (f"{ra.CONFIGURATION_CHANGED}: the authority configuration that opened the experiment is no longer in effect (last authoritative minute "
                      f"{claim.get('last_authoritative_minute')}); the legacy engine may not continue it")
            invalid = invalidate_record(claim, reason, STOP_CONFIGURATION)
            try:
                store[SESSION_KEY] = invalid
            except Exception:
                pass
            return _decision(False, INVALID_FOR_CONTINUATION, reason, stop_class=STOP_CONFIGURATION, record=invalid, sources=sources)
        if "site" not in claims and claim.get("stop_policy") == "EFFECTIVE_STOP":
            # An authority session whose SITE is gone: a saved encounter that was reopened, a page session that lost its objects, another process. The site is what continues an
            # authority experiment; without it the only thing left that could run the encounter is the legacy engine, and that is the silent mixed trajectory FD-STOP-03 forbids.
            if lifecycle == ACTIVE_AUTHORITY:
                reason = (f"{ra.RESUMED_WITHOUT_SITE}: the authority session was active (last authoritative minute {claim.get('last_authoritative_minute')}) and its site is gone; "
                          f"the legacy engine may not continue it")
                invalid = invalidate_record(claim, reason, STOP_RESUMED)
                try:
                    store[SESSION_KEY] = invalid
                except Exception:
                    pass
                if asked:
                    ra.note_resume_without_site(state_map, store, live)         # the durable marker, when the store can match this encounter (best effort)
                return _decision(False, INVALID_FOR_CONTINUATION, reason, stop_class=STOP_RESUMED, record=invalid, sources=sources)
            if lifecycle == PREAUTHORITY:
                return _decision(True, PRECOMMIT_ABORT, "the authority site is gone before the first commit: nothing was ever authoritative and the untouched legacy encounter may continue",
                                 record=claim, sources=sources)
        if lifecycle == PRECOMMIT_ABORT:
            return _decision(True, PRECOMMIT_ABORT, "the experiment aborted before the first authority commit: the untouched legacy encounter may continue", record=claim, sources=sources)
        if encounter_ended and lifecycle in (PREAUTHORITY, ACTIVE_AUTHORITY):
            lifecycle = COMPLETED_AUTHORITY
        return _decision(True, lifecycle, "the authority experiment may continue" if lifecycle in (PREAUTHORITY, ACTIVE_AUTHORITY) else "the authority experiment is complete", record=claim, sources=sources)
    except Exception as error:
        return _decision(False, INVALID_FOR_CONTINUATION, f"the guard failed closed: {type(error).__name__}: {error}", stop_class=STOP_INTERNAL)


def operation_allowed(decision: Mapping, operation: str) -> bool:
    """Whether the page may perform ``operation`` under ``decision``. Only READ_ONLY and LEAVES_THE_SESSION survive a stop. An operation the registry does not know is NOT allowed
    while stopped (a route nobody classified is a bypass)."""
    if decision.get("allowed"):
        return True
    return OPERATIONS.get(str(operation)) in (READ_ONLY, LEAVES_THE_SESSION)


def notice_is_operational(text: str) -> bool:
    """The page notice names no clinical outcome: none of the words a resident would read as a patient's death, arrest or terminal state."""
    lowered = str(text or "").lower()
    return not any(word in lowered for word in FORBIDDEN_NOTICE_WORDS)
