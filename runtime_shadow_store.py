"""P3-148: the SHADOW RESEARCH TRACE STORE. Faculty and development only. Never authority.

What it holds: the trace of one live shadow session -- the arrival it opened on, the actions the engine
executed and when each takes effect, every run kept apart (the session's own run and, for a family that runs
a development region, each witness whole), the failures, and enough to REPLAY each run independently.

What it is not:

- it is NOT the authority artifact store (``runtime_authority_store``). A shadow trace is not an authority
  experiment, and neither store accepts the other's records;
- it is NOT readable as resident state. Every record says ``NONAUTHORITATIVE_SHADOW`` and
  ``DEVELOPMENT_ONLY`` in its own body, no resident-facing module reads this store (a test names them), and
  nothing here writes to a patient, a ledger, a score or a trace of the encounter;
- it is NOT on unless a faculty or development environment names a directory
  (``MRS_PHASE3_SHADOW_TRACE_STORE``): absolute, and outside the repository, because a trace is run data and
  the repository holds none. Unset, nothing is written, read or created.

Records are immutable: one per state of a session (it grows turn by turn), named by a deterministic identity,
create-only. The trace's own digest is its integrity check: it detects an accidental or content-level change,
not a change by someone who can recompute it -- no signature is required by this package.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

import runtime_shadow as rs
import runtime_shadow_families as fam

STORE_VERSION = "P3-148"
SCHEMA = "P3-148/1"
#: The faculty or development environment names the directory. Absent means the store is off.
STORE_FLAG = "MRS_PHASE3_SHADOW_TRACE_STORE"
ARTIFACT = "phase3_shadow_session_trace"
NONAUTHORITATIVE = "NONAUTHORITATIVE_SHADOW"
DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
SESSION_RUN = "SESSION_RUN"
WITNESS_RUN = "DEVELOPMENT_TEST_WITNESS"
#: The name the session's own run travels under. It is never a witness.
SESSION_RUN_NAME = "SESSION_RUN"

NOT_CONFIGURED = "NO_SHADOW_TRACE_STORE_CONFIGURED"
NOT_A_TRACE = "NOT_A_SHADOW_SESSION_TRACE"
COLLISION = "TRACE_IDENTITY_COLLISION_WITH_DIFFERENT_CONTENT"
DIGEST_MISMATCH = "TRACE_DIGEST_DOES_NOT_RECOMPUTE"
OUTSIDE_THE_REPOSITORY = ("a shadow trace store must be an absolute path outside the repository: a trace is "
                          "run data, and the repository holds no run data")
#: As with the shadow flag itself: a deployment's secrets file cannot turn the store on.
FROM_SECRETS = ("a shadow trace store named by a deployment's secrets file is not honoured: only the process "
                "environment of a faculty or development run can name one")
NOTHING_TO_REPLAY = "the trace holds no run: there is nothing to replay"
OUTSIDE_THE_STORE = "the record's own name would leave the store's directory: nothing was written"
#: Nothing resident-facing may ever read this store or the observer; the test that proves it names these.
RESIDENT_READERS_FORBIDDEN = ("app.py", "pilot_acceptance.py", "family_engine.py", "management_trace_store.py",
                              "rubric_store.py", "progress_store.py", "faculty_portal.py",
                              "runtime_authority.py", "runtime_authority_store.py")


# -- where --------------------------------------------------------------------------------------------------------

def repository_root() -> Path:
    return Path(__file__).resolve().parent


def root(environ: Mapping[str, str] | None = None) -> Path | None:
    """The directory this process keeps shadow traces in, or None when no environment named one.

    A relative path, or any path inside the repository, is refused rather than created.
    """
    live = os.environ if environ is None else environ
    named = str(live.get(STORE_FLAG, "") or "").strip()
    if not named or rs._named_in_secrets(STORE_FLAG):
        return None
    directory = Path(named)
    if not directory.is_absolute():
        return None
    try:
        resolved = directory.resolve()
        inside = resolved == repository_root() or repository_root() in resolved.parents
    except Exception:
        return None
    return None if inside else directory


def refused_root(environ: Mapping[str, str] | None = None) -> str:
    """Why the named directory was refused. Empty when there is nothing to refuse."""
    live = os.environ if environ is None else environ
    named = str(live.get(STORE_FLAG, "") or "").strip()
    if not named or root(environ) is not None:
        return ""
    return FROM_SECRETS if rs._named_in_secrets(STORE_FLAG) else OUTSIDE_THE_REPOSITORY


def configured(environ: Mapping[str, str] | None = None) -> bool:
    return root(environ) is not None


# -- the trace ----------------------------------------------------------------------------------------------------

def canonical(payload: Any) -> str:
    """The one serialization every digest here is taken over: sorted keys, no spaces."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def digest_of(payload: Any) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def trace_digest(trace: Mapping) -> str:
    """The digest of a trace's content: everything but the digest itself."""
    return digest_of({key: value for key, value in dict(trace).items() if key != "trace_digest"})


def _lineage() -> dict:
    """Which common core produced this trace, and whether the lineage gate stands behind it."""
    import runtime_shadow_evidence as evidence
    versions = rs.versions()
    try:
        certified = bool(evidence.core_lineage_ok())
        reason = "" if certified else (evidence.core_lineage_reason() or "the lineage could not be evaluated")
    except Exception as error:
        certified, reason = False, f"the lineage could not be evaluated: {type(error).__name__}"
    return {"core_version": versions.get("core_version"), "core_digest": versions.get("core_digest"),
            "phase2_closure_head": versions.get("phase2_closure_head"),
            "phase2_digest": versions.get("phase2_digest"),
            "phase3_layer_digest": versions.get("phase3_layer_digest"),
            "certified": certified, "reason": reason}


def _run(runner, role: str, witness: str | None, session_minutes: int) -> dict:
    """One run, whole: its parameter, its recorded minutes with their channels, and its own replay artifact.

    A run that failed keeps the minutes it recorded and its failures, and nothing is made up after its last
    valid minute. A run whose artifact cannot be rebuilt says so. A witness that never opened has no profile:
    its declared value is still named, and the value it RAN with is None, because it ran with none.
    """
    try:
        captured, artifact_error = runner.replay_input(), None
    except Exception as error:
        captured, artifact_error = None, f"{type(error).__name__}: {str(error)[:200]}"
    profile = runner.profile
    parameter = None
    if witness is not None:
        parameter = {"name": fam.TRANSMISSION_FIELD, "declared": fam.TRANSMISSION_WITNESSES.get(witness),
                     "value": None if profile is None else getattr(profile, fam.TRANSMISSION_FIELD),
                     "declared_respiratory_quotient": None if profile is None else profile.respiratory_quotient,
                     "classification": fam.TRANSMISSION_CLASSIFICATION}
    minutes = fam.run_channels(runner)
    failed = bool(runner.failures) or runner.anchors is None or int(runner.minutes_done) < int(session_minutes)
    return {
        "role": role, "witness": witness, "parameter": parameter,
        "adapter": runner.adapter.version,
        "snapshot": runner.snapshot_.to_dict() if runner.snapshot_ else {},
        "minutes": minutes,
        "last_valid_minute": int(runner.minutes_done),
        "failed": failed,
        "failures": [dict(vars(item)) for item in runner.failures],
        "gaps": [dict(gap) for gap in runner.gaps],
        "replay_input": None if captured is None else captured.to_dict(),
        "replay_digest": None if captured is None else captured.digest(),
        "artifact_error": artifact_error,
    }


def _unreadable_run(role: str, witness: str | None, error: Exception) -> dict:
    """A run that could not be read at all: it stays in the trace as failed, with the reason, and empty."""
    return {"role": role, "witness": witness, "parameter": None, "adapter": None, "snapshot": {}, "minutes": [],
            "last_valid_minute": 0, "failed": True,
            "failures": [{"minute": 0, "where": "trace", "exception": type(error).__name__,
                          "message": "this run could not be read into the trace", "classification": rs.UNEXPECTED}],
            "gaps": [], "replay_input": None, "replay_digest": None,
            "artifact_error": f"{type(error).__name__}"}


def _last_channels(runs: Mapping) -> dict | None:
    minutes = ((runs.get(SESSION_RUN_NAME) or {}).get("minutes") or []) if isinstance(runs, Mapping) else []
    last = minutes[-1] if minutes and isinstance(minutes[-1], Mapping) else None
    return None if last is None or not isinstance(last.get("channels"), Mapping) else dict(last["channels"])


def _terminal_boundary(session, runs: Mapping) -> dict:
    declared = None
    try:
        profile = None if session.runner is None else session.runner.profile
        declared = None if profile is None else profile.collapse_output_threshold is not None
    except Exception:
        declared = None
    return fam.terminal_boundary(session.legacy_terminal, _last_channels(runs), declared)


def trace_of(session, previous: str | None = None) -> dict:
    """The trace of a live shadow session, as it stands now. Pure: it reads the session and changes nothing.

    Every run is built apart, so one run that cannot be read does not take the others with it: it stays in
    the trace as a failed run with the reason. ``previous`` is the identity of the record this session stored
    before this one, which is what ties the records of one attempt together.
    """
    runner = session.runner
    session_minutes = 0 if runner is None else int(runner.minutes_done)
    runs: dict = {}
    if runner is not None and runner.anchors is not None:
        try:
            runs[SESSION_RUN_NAME] = _run(runner, SESSION_RUN, None, session_minutes)
        except Exception as error:
            runs[SESSION_RUN_NAME] = _unreadable_run(SESSION_RUN, None, error)
    expected: tuple = ()
    ensemble = session.ensemble
    try:
        adapter = fam.adapter_for(session.family)
        expected = tuple(adapter.region_witnesses()) if adapter is not None and runs else ()
    except Exception:
        expected = ()
    if ensemble is not None:
        for name, witness in ensemble.runners.items():
            try:
                runs[name] = _run(witness, WITNESS_RUN, name, session_minutes)
            except Exception as error:
                runs[name] = _unreadable_run(WITNESS_RUN, name, error)
    actions = [] if runner is None else fam.action_dispositions(runner.adapter, session.mirrored,
                                                                session._mapping_state())
    actions = actions + fam.held_rows(session.held, actions)
    actions = actions + fam.unmirrored_rows(session.gaps, actions)
    held = [{key: entry.get(key) for key in ("order_id", "kind", "after_result", "placed_minute", "state",
                                             "executed_minute", "shadow_order_id", "events")}
            for entry in session.held]
    failures = [dict(vars(item)) for item in session.failures]
    status = fam.session_status(
        failures=failures, gaps=list(session.gaps), actions=actions, expected_witnesses=expected,
        runs={name: {"minutes": len(run["minutes"]), "failed": run["failed"]} for name, run in runs.items()},
        session_minutes=session_minutes)
    eligibility = dict(session.eligibility or {})
    trace = {
        "artifact": ARTIFACT, "schema": SCHEMA, "store": STORE_VERSION,
        "authority": NONAUTHORITATIVE, "use": DEVELOPMENT_ONLY,
        "resident_visible": False, "runtime_authority": "legacy",
        "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
        "family": session.family, "case_id": session.case_id,
        "encounter_id": session.encounter_id, "scenario_id": session.scenario_id,
        "generation": session.generation,
        "terminal_boundary": _terminal_boundary(session, runs),
        "previous_trace_id": previous,
        "lineage": _lineage(),
        "arrival": {"fingerprint": session.encounter_id,
                    "eligible": bool(eligibility.get("eligible")),
                    "conditions": dict(eligibility.get("conditions") or {}),
                    "differences": [list(item) for item in (eligibility.get("differences") or [])][:24],
                    "family_identity": ("certified adapter identity checked when the run opened"
                                        if runs else "no run opened")},
        "turns": int(session.turns), "session_minutes": session_minutes,
        "actions": actions,
        "held_orders": held,
        "expected_witnesses": list(expected),
        "witness_policy": (fam.ENSEMBLE_POLICY if expected else "this family runs no development region"),
        "selected_witness": None,
        "region": ({"parameter": fam.TRANSMISSION_FIELD, "classification": fam.TRANSMISSION_CLASSIFICATION,
                    "conditional_on": fam.transmission_condition(),
                    "mathematical_region": list(fam.TRANSMISSION_MATHEMATICAL_REGION),
                    "active_causal_region": dict(fam.TRANSMISSION_ACTIVE_REGION),
                    "declared_respiratory_quotient": fam.TRANSMISSION_DECLARED_R,
                    "refused": None if ensemble is None else ensemble.refused} if expected else None),
        "runs": runs,
        "compared_minutes": [] if runner is None else list(runner.compared),
        "divergences": [] if runner is None else [
            {"minute": d.minute, "domain": d.domain, "variable": d.variable, "status": d.status}
            for d in runner.divergences],
        "failures": failures,
        "gaps": [dict(gap) for gap in session.gaps],
        "status": status,
    }
    trace["trace_digest"] = trace_digest(trace)
    return trace


def trace_id(trace: Mapping) -> str:
    """The deterministic identity of one record: the arrival, everything that was asked of the shadow since,
    how far the session had got, the record before it, and the code that ran it.

    It is taken over the INPUTS (the arrival and what was found of it, the action sequence, each run's own
    replay artifact, what failed and why, the core and the layer) and never over the recorded outputs. So the
    same inputs are the same record -- storing it twice is idempotent -- and the same inputs with DIFFERENT
    recorded content is a collision the store refuses instead of overwriting: that is what a nondeterministic
    run would look like. It carries no participant identity, and none is stored.
    """
    body = dict(trace)
    lineage = dict(body.get("lineage") or {})
    return digest_of({
        "encounter_id": body.get("encounter_id"), "family": body.get("family"), "case_id": body.get("case_id"),
        "session_minutes": body.get("session_minutes"), "turns": body.get("turns"),
        "previous": body.get("previous_trace_id"), "arrival": digest_of(body.get("arrival")),
        "actions": digest_of([[row.get("shadow_order_id"), row.get("order_minute"), row.get("kind"),
                               row.get("order_id"), row.get("submission_id")]
                              for row in (body.get("actions") or [])]),
        "runs": {name: run.get("replay_digest") for name, run in sorted((body.get("runs") or {}).items())},
        "failures": digest_of([[row.get("where"), row.get("exception"), row.get("minute"), row.get("message")]
                               for row in (body.get("failures") or [])]),
        "core": lineage.get("core_digest"), "layer": lineage.get("phase3_layer_digest"),
        "store": STORE_VERSION,
    })[:32]


def _safe(text: Any, fallback: str) -> str:
    """One file-name part: letters, digits, dash and underscore only. A trace's own fields never choose
    where a record is written."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", str(text if text is not None else ""))[:48]
    return cleaned or fallback


def _name(trace: Mapping, identifier: str) -> str:
    body = dict(trace)
    return (f"{_safe(body.get('family'), 'family')}__{_safe(body.get('case_id'), 'case')}"
            f"__m{_safe(body.get('session_minutes'), '0')}__t{_safe(body.get('turns'), '0')}"
            f"__{_safe(identifier, 'id')}.json")


def is_a_trace(trace: Any) -> bool:
    body = dict(trace) if isinstance(trace, Mapping) else {}
    return (str(body.get("artifact") or "") == ARTIFACT and body.get("authority") == NONAUTHORITATIVE
            and body.get("use") == DEVELOPMENT_ONLY and body.get("resident_visible") is False
            and body.get("common_core_runtime_authority") is False
            and body.get("runtime_authority") == "legacy" and body.get("selected_witness") is None)


def persist(trace: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
    """Write one immutable record, or say why nothing was written. Never raises into a caller.

    Create-only: an identity that already holds the same content is idempotent, and one that holds different
    content is a refusal -- a record is never overwritten. The record is written whole or not at all, and
    only ever directly inside the store's own directory. ``kind`` names the reason without the detail.
    """
    try:
        if not is_a_trace(trace):
            return {"stored": False, "kind": NOT_A_TRACE, "why": NOT_A_TRACE}
        body = dict(trace)
        if body.get("trace_digest") != trace_digest(body):
            return {"stored": False, "kind": DIGEST_MISMATCH, "why": DIGEST_MISMATCH}
        directory = root(environ)
        if directory is None:
            why = refused_root(environ) or NOT_CONFIGURED
            return {"stored": False, "kind": why, "why": why}
        identifier = trace_id(body)
        payload = canonical({"store": STORE_VERSION, "trace_id": identifier,
                             "trace_digest": body.get("trace_digest"), "trace": body})
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / _name(body, identifier)
        if path.resolve().parent != directory.resolve():
            return {"stored": False, "kind": OUTSIDE_THE_STORE, "why": OUTSIDE_THE_STORE}
        if path.exists():
            if path.read_text(encoding="utf-8") == payload:
                return {"stored": True, "idempotent": True, "trace_id": identifier, "path": str(path), "why": ""}
            return {"stored": False, "kind": COLLISION, "why": COLLISION, "trace_id": identifier,
                    "path": str(path)}
        pending = path.with_name(f".{path.name}.{os.getpid()}.pending")
        try:
            pending.write_text(payload, encoding="utf-8")
            os.replace(pending, path)                  # whole or not at all: no half-written record is left
        finally:
            if pending.exists():
                pending.unlink()
        return {"stored": True, "idempotent": False, "trace_id": identifier, "path": str(path),
                "bytes": len(payload.encode("utf-8")), "why": ""}
    except Exception as error:              # a store failure may never break an encounter
        return {"stored": False, "kind": f"STORE_ERROR {type(error).__name__}",
                "why": f"STORE_ERROR {type(error).__name__}: {_text(error)}"}


def _text(error: Exception) -> str:
    try:
        return str(error)[:300]
    except Exception:
        return "the error could not be described"


def persist_session(session, *, environ: Mapping[str, str] | None = None) -> dict | None:
    """Persist the session's trace as it stands. None when no store is named, which is the default.

    A store that IS named and cannot be used is not "off": it is a refusal, returned so that it is seen.
    """
    if not configured(environ):
        why = refused_root(environ)
        return {"stored": False, "kind": why, "why": why} if why else None
    try:
        return persist(trace_of(session, previous=session._last_stored), environ=environ)
    except Exception as error:
        return {"stored": False, "kind": f"TRACE_ERROR {type(error).__name__}",
                "why": f"TRACE_ERROR {type(error).__name__}: {_text(error)}"}


# -- reading ------------------------------------------------------------------------------------------------------

UNREADABLE = "UNREADABLE"
NOT_VERIFIED = "NOT_VERIFIED"


def paths(*, environ: Mapping[str, str] | None = None) -> list:
    directory = root(environ)
    if directory is None or not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def _read(path: Path) -> dict | None:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return record if isinstance(record, dict) and isinstance(record.get("trace"), dict) else None


def _row(path: Path, record: Mapping, lineage: Mapping) -> dict:
    body = record["trace"]
    checked = verify(body, lineage=lineage)
    status = body.get("status") if isinstance(body.get("status"), dict) else {}
    return {"trace_id": str(record.get("trace_id")), "path": str(path), "family": str(body.get("family")),
            "case_id": str(body.get("case_id")), "encounter_id": str(body.get("encounter_id")),
            "session_minutes": int(body.get("session_minutes") or 0), "turns": int(body.get("turns") or 0),
            "state": str(status.get("state")), "codes": [str(code) for code in (status.get("codes") or [])],
            "runs": sorted(str(name) for name in (body.get("runs") or {})),
            "trace_digest": body.get("trace_digest"), "previous_trace_id": body.get("previous_trace_id"),
            "verified": bool(checked["verified"]), "why": checked["why"], "unreadable": False}


def records(*, encounter_id: str | None = None, case_id: str | None = None, family: str | None = None,
            environ: Mapping[str, str] | None = None) -> list:
    """The stored records, as a faculty retrieval path lists them: an attempt's records in the order its
    session grew. Never raises: a file that cannot be read as a record is listed as UNREADABLE, last, and a
    record that does not pass ``verify`` says so (``verified``) instead of being listed as if it did."""
    out, broken = [], []
    try:
        lineage = _lineage()
    except Exception:
        lineage = {"certified": False, "reason": "the lineage could not be evaluated", "core_digest": None}
    for path in paths(environ=environ):
        try:
            record = _read(path)
            if record is None:
                raise ValueError("not a stored record")
            row = _row(path, record, lineage)
        except Exception:
            broken.append({"trace_id": None, "path": str(path), "family": None, "case_id": None,
                           "encounter_id": None, "session_minutes": 0, "turns": 0, "state": UNREADABLE,
                           "codes": [], "runs": [], "trace_digest": None, "previous_trace_id": None,
                           "verified": False, "why": "this file cannot be read as a stored record",
                           "unreadable": True, "head": False})
            continue
        out.append(row)
    continued = {row["previous_trace_id"] for row in out if row["previous_trace_id"]}
    for row in out:
        row["head"] = row["trace_id"] not in continued
    out = [row for row in out if (encounter_id is None or row["encounter_id"] == encounter_id)
           and (case_id is None or row["case_id"] == case_id) and (family is None or row["family"] == family)]
    out = sorted(out, key=lambda item: (item["family"], item["case_id"], item["encounter_id"],
                                        item["session_minutes"], item["turns"], item["trace_id"]))
    return out + (broken if encounter_id is None and case_id is None and family is None else [])


def heads(*, encounter_id: str | None = None, case_id: str | None = None, family: str | None = None,
          environ: Mapping[str, str] | None = None) -> list:
    """The records no stored record continues: the furthest state of every stored attempt.

    The arrival fingerprint is the same for every attempt at a case, so it does not tell two attempts apart.
    Each record names the record its own session stored before it, and that chain does: two attempts that
    begin alike share their first records and part where they differ.
    """
    return [row for row in records(encounter_id=encounter_id, case_id=case_id, family=family, environ=environ)
            if row["head"]]


def load(identifier: str, *, environ: Mapping[str, str] | None = None) -> dict | None:
    """One stored trace by its identity, or None. Loading does not verify: ``verify`` and ``replay`` do."""
    for path in paths(environ=environ):
        record = _read(path)
        if record is not None and str(record.get("trace_id")) == str(identifier):
            return dict(record["trace"])
    return None


# -- verifying and replaying --------------------------------------------------------------------------------------

def _plain(value: Any) -> Any:
    return json.loads(canonical(value))


def _held_inconsistencies(body: Mapping) -> list:
    """Where the held orders and the action timeline of a trace disagree. Each held order has exactly one
    row: a mirrored one at its execution minute if it ran, a row that builds nothing if it did not; and no
    row speaks of a held order the trace does not carry. (A held order removed together with its row leaves
    nothing behind to contradict: that is the consistent forgery the store declares it cannot see.)"""
    problems: list = []
    actions = [row for row in (body.get("actions") or []) if isinstance(row, dict)]
    held = [item for item in (body.get("held_orders") or []) if isinstance(item, dict)]
    claimed = set()
    for item in held:
        ran = item.get("state") == rs.ORDER_EXECUTED
        identity = str(item.get("shadow_order_id") if ran else item.get("order_id"))
        rows = [row for row in actions if str(row.get("shadow_order_id")) == identity]
        claimed.add(identity)
        if len(rows) != 1:
            problems.append(f"held order {identity} has {len(rows)} rows in the action timeline")
            continue
        row = rows[0]
        if ran and not (row.get("disposition") in fam.MIRRORED_DISPOSITIONS
                        and row.get("order_minute") == item.get("executed_minute")
                        and row.get("placed_minute") == item.get("placed_minute")):
            problems.append(f"held order {identity} ran and its row does not say so")
        expected = fam.NOT_MIRRORED if item.get("state") == rs.ORDER_RELEASED else fam.HELD_NOT_EXECUTED
        if not ran and not (row.get("disposition") == expected and row.get("order_minute") is None):
            problems.append(f"held order {identity} did not run and its row says otherwise")
    for row in actions:
        if (row.get("disposition") == fam.HELD_NOT_EXECUTED or row.get("placed_minute") is not None) and str(
                row.get("shadow_order_id")) not in claimed:
            problems.append(f"row {row.get('shadow_order_id')} speaks of a held order the trace does not carry")
    return problems


def _inconsistencies(body: Mapping) -> list:
    """Where a trace disagrees WITH ITSELF. A digest only says the bytes are the ones that were sealed; this
    says the sealed parts tell one story: every run is the run its name says, as long as its record says, the
    recorded status is what the recorded content adds up to, and the actions are the ones the run was given.
    It catches an edit that was re-sealed; it is not a signature, and a forgery consistent in every part is
    beyond it -- which the store declares."""
    problems: list = []
    runs = body.get("runs") if isinstance(body.get("runs"), dict) else {}
    family = str(body.get("family") or "")
    session_minutes = body.get("session_minutes")
    problems.extend(_held_inconsistencies(body))
    boundary = body.get("terminal_boundary")
    if boundary is not None:
        # The boundary is a reading of the trace's own last minute and of the legacy record it carries. It is
        # recomputed here, so its state, its reason and its predicates cannot be edited apart from its two
        # sides; and a legacy arrest the run itself recorded as a pulse divergence cannot be erased from it.
        # What stays beyond self-consistency, declared: a legacy record rewritten whole, or the key removed,
        # with nothing else in the trace to contradict it (verify is not a signature), and an edit of the
        # last minute's own channels, which only the replay sees.
        again = None
        if isinstance(boundary, dict) and isinstance(boundary.get("legacy"), dict) and isinstance(
                boundary.get("core"), dict):
            legacy = boundary["legacy"] if boundary["legacy"].get("terminal") is not None else None
            again = fam.terminal_boundary(legacy, _last_channels(runs),
                                          boundary["core"].get("collapse_rule_declared"))
        if again != boundary:
            problems.append("the terminal boundary is not what the trace's own last minute and legacy record give")
        elif (boundary["state"] in (fam.BOTH_ACTIVE, fam.TERMINAL_NOT_COMPARABLE)
              and boundary["core"].get("pulse_present") is True
              and any(isinstance(item, dict) and item.get("variable") == "pulse_present"
                      and item.get("status") == rs.SAFETY_CRITICAL for item in (body.get("divergences") or []))):
            problems.append("the run recorded a pulse divergence with the legacy engine, and the terminal "
                            "boundary says neither engine is terminal")
    adapter = fam.adapter_for(family)
    declared = [] if adapter is None or not runs else list(adapter.region_witnesses())
    if list(body.get("expected_witnesses") or []) != declared:
        problems.append(f"the expected witnesses are not the ones the family declares: {declared}")
    for name, run in runs.items():
        if not isinstance(run, dict):
            problems.append(f"run {name} is not a run")
            continue
        minutes = run.get("minutes") if isinstance(run.get("minutes"), list) else []
        numbers = [row.get("minute") if isinstance(row, dict) else None for row in minutes]
        if numbers != list(range(1, len(minutes) + 1)) or run.get("last_valid_minute") != len(minutes):
            problems.append(f"run {name}: its minutes are not 1 to its last valid minute")
        if len(minutes) != session_minutes and not run.get("failed"):
            problems.append(f"run {name}: {len(minutes)} minutes of {session_minutes} and not marked failed")
        if run.get("failures") and not run.get("failed"):
            problems.append(f"run {name}: it carries failures and is not marked failed")
        artifact = run.get("replay_input") if isinstance(run.get("replay_input"), dict) else None
        if name == SESSION_RUN_NAME:
            if run.get("role") != SESSION_RUN or run.get("witness") is not None or run.get("parameter") is not None:
                problems.append("the session run is labelled as something else")
            if len(minutes) != session_minutes:
                problems.append("the session's minutes are not its own run's")
            continue
        parameter = run.get("parameter") if isinstance(run.get("parameter"), dict) else {}
        value = fam.TRANSMISSION_WITNESSES.get(name)
        if run.get("role") != WITNESS_RUN or run.get("witness") != name or name not in declared:
            problems.append(f"run {name} is not the witness its name says")
        elif (parameter.get("name") != fam.TRANSMISSION_FIELD or parameter.get("declared") != value
              or parameter.get("value") not in (None, value)):
            problems.append(f"run {name}: its parameter is not the declared value of that witness")
        elif artifact is not None and (artifact.get("scenario") or {}).get("profile", {}).get(
                fam.TRANSMISSION_FIELD) != value:
            problems.append(f"run {name}: its artifact ran another value than the witness declares")
    session = runs.get(SESSION_RUN_NAME) if isinstance(runs.get(SESSION_RUN_NAME), dict) else None
    artifact = session.get("replay_input") if session and isinstance(session.get("replay_input"), dict) else None
    rows = [row for row in (body.get("actions") or []) if isinstance(row, dict)]
    if artifact is not None:
        told = {str(row.get("shadow_order_id")): (row.get("order_minute"), row.get("kind")) for row in rows}
        for event in artifact.get("actions") or []:
            if told.get(str(event.get("order_id"))) != (event.get("minute"), event.get("kind")):
                problems.append(f"action {event.get('order_id')} is not in the timeline as the run was given it")
    try:
        again = fam.session_status(
            failures=list(body.get("failures") or []), gaps=list(body.get("gaps") or []), actions=rows,
            expected_witnesses=list(body.get("expected_witnesses") or []),
            runs={name: {"minutes": len(run.get("minutes") or []), "failed": bool(run.get("failed"))}
                  for name, run in runs.items() if isinstance(run, dict)},
            session_minutes=int(session_minutes or 0))
        if _plain(again) != _plain(body.get("status")):
            problems.append(f"the recorded status is not what the recorded content adds up to "
                            f"({again['state']})")
    except Exception as error:
        problems.append(f"the status could not be recomputed: {type(error).__name__}")
    return problems


def verify(trace: Mapping, *, lineage: Mapping | None = None) -> dict:
    """Is this a shadow trace, whole, labelled, consistent with itself, and from the core that is live now?
    Never raises.

    ``lineage_matches`` is what a replay needs: a trace recorded on another core cannot be said to reproduce
    on this one, so it is refused there instead of compared.
    """
    body = dict(trace) if isinstance(trace, Mapping) else {}
    labelled = is_a_trace(body)
    try:
        digest_matches = bool(body) and body.get("trace_digest") == trace_digest(body)
    except Exception:
        digest_matches = False
    runs = body.get("runs") if isinstance(body.get("runs"), dict) else {}
    family = str(body.get("family") or "")
    try:
        wrong_family = sorted(str(name) for name, run in runs.items()
                              if str(((run or {}).get("replay_input") or {}).get("family") or family) != family)
        missing = [name for name in (body.get("expected_witnesses") or []) if name not in runs]
        problems = _inconsistencies(body) if labelled and digest_matches and not wrong_family else []
    except Exception as error:
        wrong_family, missing = [], []
        problems = [f"the trace could not be checked against itself: {type(error).__name__}"]
    try:
        now = dict(_lineage() if lineage is None else lineage)
        recorded = dict(body.get("lineage") or {})
        lineage_matches = bool(now["certified"] and recorded.get("certified")
                               and recorded.get("core_digest") == now["core_digest"])
        lineage_why = "" if lineage_matches else (
            now["reason"] if not now["certified"] else
            "the trace was recorded on an uncertified core" if not recorded.get("certified") else
            f"the trace was recorded on core {str(recorded.get('core_digest'))[:16]} and the live core is "
            f"{str(now['core_digest'])[:16]}")
        if lineage_matches and recorded.get("core_version") != now.get("core_version"):
            problems.append("the trace names another core version than the digest it carries")
    except Exception as error:
        lineage_matches, lineage_why = False, f"the lineage could not be evaluated: {type(error).__name__}"
    verified = bool(labelled and digest_matches and not wrong_family and not problems)
    return {"is_a_shadow_trace": labelled, "digest_matches": digest_matches, "lineage_matches": lineage_matches,
            "lineage_why": lineage_why, "wrong_family_runs": wrong_family, "missing_witnesses": missing,
            "inconsistencies": problems, "verified": verified,
            "why": "" if verified else (
                NOT_A_TRACE if not labelled else DIGEST_MISMATCH if not digest_matches else
                f"runs recorded for another family: {wrong_family}" if wrong_family else
                "the trace is not consistent with itself: " + "; ".join(problems[:4]))}


def again_scenario(payload: Mapping) -> dict:
    """The scenario of a stored replay artifact, as plain data read back from its own serialization."""
    return json.loads(canonical(dict(payload).get("scenario") or {}))


def replay(trace: Mapping) -> dict:
    """Replay every run of a persisted trace from its own artifact and compare it with what was recorded.

    Deterministic and exact: the state digest, the reading digest and every recorded channel of every
    recorded minute. A failed run replays only up to its last valid minute and no state is made up after it.
    A trace that is not verified, or whose core is not the live certified one, is REFUSED, not compared.
    Never raises.
    """
    checked = verify(trace)
    if not checked["verified"]:
        return {"replayed": False, "reproduces": False, "refused": fam.REPLAY_MISMATCH, "why": checked["why"],
                "nothing_to_replay": False, "runs": {}, "missing_witnesses": checked["missing_witnesses"],
                "verify": checked}
    if not checked["lineage_matches"]:
        return {"replayed": False, "reproduces": False, "refused": fam.LINEAGE_REJECTED,
                "why": checked["lineage_why"], "nothing_to_replay": False, "runs": {},
                "missing_witnesses": checked["missing_witnesses"], "verify": checked}
    body, out = dict(trace), {}
    if not body.get("runs"):
        # A rejected arrival ran nothing. That is not a mismatch, and it is not a replay either.
        return {"replayed": False, "reproduces": True, "refused": None, "nothing_to_replay": True,
                "why": NOTHING_TO_REPLAY, "runs": {}, "missing_witnesses": checked["missing_witnesses"],
                "verify": checked}
    for name, run in sorted((body.get("runs") or {}).items()):
        recorded = list(run.get("minutes") or [])
        payload = run.get("replay_input")
        if payload is None:
            out[name] = {"reproduces": not recorded, "minutes": 0, "recorded": len(recorded),
                         "first_mismatch": recorded[0]["minute"] if recorded else None,
                         "why": "this run has no replay artifact" + (
                             f": {run.get('artifact_error')}" if run.get("artifact_error") else "")}
            continue
        try:
            # the artifact as stored, through the layer's one from-artifact path, and read back as plain data
            rows = json.loads(canonical(fam.artifact_rows(again_scenario(payload))))
        except Exception as error:
            out[name] = {"reproduces": False, "minutes": 0, "recorded": len(recorded), "first_mismatch": None,
                         "why": f"the artifact could not be replayed: {type(error).__name__}: {_text(error)[:160]}"}
            continue
        first = None
        for index, row in enumerate(recorded):
            mine = rows[index] if index < len(rows) else None
            # The whole row: the two digests AND every channel a reader is shown. A recorded channel that
            # the artifact does not recompute is a mismatch, whatever the digests say.
            if mine is None or any(mine[key] != row.get(key) for key in ("minute", "state_digest",
                                                                         "reading_digest", "channels")):
                first = row.get("minute")
                break
        # a run replays what it recorded and not a minute more: nothing is made up after a failure
        longer = len(rows) > len(recorded)
        out[name] = {"reproduces": first is None and not longer, "minutes": len(rows), "recorded": len(recorded),
                     "first_mismatch": first,
                     "why": "" if first is None and not longer else (
                         f"the replay does not reproduce minute {first}" if first is not None else
                         f"the artifact replays {len(rows)} minutes and the trace recorded {len(recorded)}")}
    missing = checked["missing_witnesses"]
    for name in missing:
        # A witness the family declares and the trace does not hold: said by name, never passed over.
        out[name] = {"reproduces": False, "minutes": 0, "recorded": 0, "first_mismatch": None,
                     "code": fam.WITNESS_FAILED, "why": "a witness this family declares is missing from the trace"}
    reproduces = bool(out) and all(row["reproduces"] for row in out.values())
    return {"replayed": True, "reproduces": reproduces, "refused": None, "nothing_to_replay": False,
            "why": "" if reproduces else "at least one run does not reproduce",
            "runs": out, "missing_witnesses": missing, "verify": checked}
