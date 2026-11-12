"""P3-224 to P3-230: the DORMANT GI pair-authority site (pressure + consciousness), its arming gate, its state machine and its artifact.

This is the real orchestration a future development experiment would run: capture, compute, per-minute validation of every minute of the interval,
interval validation, the candidate payload, a commit-or-abort interface, a persisted artifact and a halt state. It is DORMANT and NON-ACTIVATABLE (FD-AUTH-09 and
FD-AUTH-10): nothing in this repository can arm it today, and arming it is a faculty act that this package does not perform.

What makes it non-activatable (each is tested, and none is enough alone):

1. ``arming`` has nine conditions. The fifth (an explicit pair-authority grant in ``GRANT_REGISTRY``) and the eighth (``FACULTY_APPROVAL`` says GRANTED) are
   source constants that are EMPTY / NOT_GRANTED. No environment variable, no file, no flag, no snapshot name and no ``COMMON_CORE_RUNTIME_AUTHORITY`` reads
   into them. A grant of kind ``TEST_ONLY_FAKE_GRANT`` is never loadable, whatever registry it is put in.
2. ``request_commit`` consults the arming first, then requires version 1 ITSELF to be in the authority registry (it is ratified for development experiments and is
   NOT in it; the pressure point's own approval does not stand in for it), and then the transaction re-evaluates the pressure authority gate. Closed in series, and the
   second does not depend on the faculty's two constants.
3. The page never calls ``request_commit``: it reaches this layer only through ``runtime_authority.after_clock_moved`` and ``after_orders_settled``.
4. The site never writes the encounter. ``minute`` evaluates a deep copy; a commit returns a NEW mapping to the caller (and only an armed site can ask).

The legacy engine is the resident's authority at every step. ``COMMON_CORE_RUNTIME_AUTHORITY`` stays False, and this module neither reads nor sets it to decide.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_minute_validation as mv
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam

MODULE_VERSION = "P3-224/230"
#: The key under which the common candidate keeps its word (named by the pair layer, which owns the field list: this module never writes the literal of the live field).
WORD = pair.CONSCIOUSNESS_FIELDS[1]
ARTIFACT_TYPE = "phase3_pair_authority_dormant"
#: What this artifact IS. It is never "COMMITTED_AUTHORITY": nothing here commits.
LABEL = "DORMANT_AUTHORITY_EVALUATION"
AUTHORITY_MODE = "DORMANT_NOT_ARMED"
GRANULARITY = pair.GRANULARITY

# -- P3-230: the states of one encounter's dormant evaluation ---------------------------------------------------------------------------------------
NOT_STARTED, EVALUATING, WOULD_COMMIT, WOULD_ABORT = "NOT_STARTED", "EVALUATING", "WOULD_COMMIT", "WOULD_ABORT"
EXPERIMENT_HALTED, INVALID_FOR_CONTINUATION = "EXPERIMENT_HALTED", "INVALID_FOR_CONTINUATION"
STATES = (NOT_STARTED, EVALUATING, WOULD_COMMIT, WOULD_ABORT, EXPERIMENT_HALTED, INVALID_FOR_CONTINUATION)
TERMINAL_STATES = (EXPERIMENT_HALTED, INVALID_FOR_CONTINUATION)
#: Allowed moves. Anything else is a bug and is refused loudly (the state machine cannot skip a halt or leave one).
TRANSITIONS = MappingProxyType({
    NOT_STARTED: (EVALUATING,),
    EVALUATING: (NOT_STARTED, WOULD_COMMIT, WOULD_ABORT),
    WOULD_COMMIT: (EVALUATING, WOULD_ABORT),
    WOULD_ABORT: (EXPERIMENT_HALTED, INVALID_FOR_CONTINUATION),
    EXPERIMENT_HALTED: (),
    INVALID_FOR_CONTINUATION: (),
})

# -- P3-226: the arming gate --------------------------------------------------------------------------------------------------------------------------
PAIR_DOMAIN = "GI_PAIR_AUTHORITY"
GRANT_KIND = "FACULTY_GI_PAIR_AUTHORITY_GRANT"
TEST_ONLY_FAKE_GRANT = "TEST_ONLY_FAKE_GRANT"
GRANTED = "GRANTED"
#: The faculty's grants. EMPTY, in source: no environment variable, file, flag or snapshot name loads a grant, and nothing in this package adds one (C8: NOT GRANTED).
GRANT_REGISTRY: tuple = ()
#: The faculty's decision on the domain. NOT_GRANTED: V1 is ratified for development EXPERIMENTS, and ratification is not a grant (FD-AUTH-11).
FACULTY_APPROVAL = MappingProxyType({PAIR_DOMAIN: "NOT_GRANTED"})
#: The schema of a grant a future faculty decision would sign. A grant names WHAT is authorized, exactly: the domain, the snapshot (id, version, record digest),
#: the core member it was ratified on, the cases and the decision that grants it.
GRANT_FIELDS = ("kind", "grant_id", "domain", "snapshot_id", "snapshot_version", "snapshot_record_digest", "core_version", "core_digest", "cases",
                "decision_reference", "issued_by_role")
ARMING_CONDITIONS = ("global_development_capability", "correct_mode", "certified_lineage", "exact_snapshot", "explicit_pair_authority_grant",
                     "case_allowlisted", "experiment_not_halted", "faculty_approval_permits_domain", "technical_site_healthy")
#: The conditions that MUST be false in this package. A test pins them: they are the faculty's, not ours.
FACULTY_CONDITIONS = ("explicit_pair_authority_grant", "faculty_approval_permits_domain")

NOT_A_GRANT = "NOT_A_GRANT"
TEST_ONLY_GRANT_NOT_LOADABLE = "TEST_ONLY_GRANT_IS_NOT_LOADABLE"
WRONG_GRANT_KIND = "WRONG_GRANT_KIND"
WRONG_GRANT_DOMAIN = "WRONG_GRANT_DOMAIN"
GRANT_SNAPSHOT_MISMATCH = "GRANT_NAMES_ANOTHER_SNAPSHOT"
GRANT_CORE_MISMATCH = "GRANT_NAMES_ANOTHER_CORE"
GRANT_CASE_NOT_NAMED = "GRANT_DOES_NOT_NAME_THIS_CASE"
GRANT_WITHOUT_DECISION = "GRANT_HAS_NO_DECISION_REFERENCE"

COMMIT_REFUSED_NOT_ARMED = "COMMIT_REFUSED_NOT_ARMED"
COMMIT_REFUSED_HALTED = "COMMIT_REFUSED_EXPERIMENT_HALTED"
COMMIT_REFUSED_NO_INTERVAL = "COMMIT_REFUSED_NO_VALIDATED_INTERVAL"
COMMIT_REFUSED_V1_NOT_APPROVED = "COMMIT_REFUSED_V1_IS_NOT_AN_AUTHORITY_APPROVED_SNAPSHOT"
COMMIT_REFUSED_ALREADY_PREPARED = "COMMIT_REFUSED_THIS_MINUTE_WAS_ALREADY_PREPARED"
COMMIT_REFUSED_OTHER_STATE = "COMMIT_REFUSED_TARGET_IS_NOT_THE_EVALUATED_STATE"
COMMIT_REFUSED_BY_TRANSACTION = "COMMIT_REFUSED_BY_THE_TRANSACTION"
COMMIT_PREPARED_FOR_THE_CALLER = "COMMIT_PREPARED_FOR_THE_CALLER"
NO_SILENT_FALLBACK = "NO_SILENT_FALLBACK_TO_THE_LEGACY_ENGINE_AFTER_AUTHORITY_BEGAN"


def grant_problems(grant: Any, *, bound: Any = None, case_id: str | None = None, lineage: Mapping | None = None) -> list:
    """Every reason ``grant`` does not authorize THIS pair on THIS snapshot and core for THIS case. Empty: it does.

    The first check refuses a fixture: a grant of kind ``TEST_ONLY_FAKE_GRANT`` is not loadable as configuration of any environment."""
    # an exact ``dict`` of plain JSON data: a Mapping subclass with its own ``get``, a tuple of cases or a version of another type can answer one thing to this
    # check and another to the code that would use the grant (the P3-208 lesson, applied here)
    if type(grant) is not dict or pair.plain(grant) != grant:
        return [NOT_A_GRANT]
    problems = []
    if grant.get("kind") == TEST_ONLY_FAKE_GRANT:
        return [TEST_ONLY_GRANT_NOT_LOADABLE]
    problems += [f"MISSING_{name.upper()}" for name in GRANT_FIELDS if grant.get(name) in (None, "", [], ())]
    problems += [f"UNKNOWN_FIELD_{name}" for name in sorted(set(grant) - set(GRANT_FIELDS))]
    for name in ("kind", "grant_id", "domain", "snapshot_id", "snapshot_record_digest", "core_version", "core_digest", "decision_reference", "issued_by_role"):
        if name in grant and (type(grant[name]) is not str or not grant[name].strip()):
            problems.append(f"{name.upper()}_IS_NOT_A_NONBLANK_STRING")
    if "snapshot_version" in grant and type(grant["snapshot_version"]) is not int:
        problems.append("SNAPSHOT_VERSION_IS_NOT_AN_INT")
    if "cases" in grant and (type(grant["cases"]) is not list or not all(type(item) is str for item in grant["cases"])):
        problems.append("CASES_IS_NOT_A_LIST_OF_STRINGS")
    if grant.get("kind") != GRANT_KIND:
        problems.append(WRONG_GRANT_KIND)
    if grant.get("domain") != PAIR_DOMAIN:
        problems.append(WRONG_GRANT_DOMAIN)
    if bound is None or not pair.bound_is_v1(bound) or (grant.get("snapshot_id"), grant.get("snapshot_version"), grant.get("snapshot_record_digest")) != (
            bound.snapshot_id, bound.version, bound.record_digest):
        problems.append(GRANT_SNAPSHOT_MISMATCH)
    live = lineage if lineage is not None else pair.live_lineage()
    if (grant.get("core_version"), grant.get("core_digest")) != (live.get("version_id"), live.get("digest")):
        problems.append(GRANT_CORE_MISMATCH)
    if case_id is None or case_id not in (grant.get("cases") if type(grant.get("cases")) is list else ()):
        problems.append(GRANT_CASE_NOT_NAMED)
    if not str(grant.get("decision_reference") or "").strip():
        problems.append(GRANT_WITHOUT_DECISION)
    return problems


def _capability(environ: Mapping[str, str]) -> bool:
    """The developer capability: the authority flag names the limited-authority mode, the environment is ``development``, and the shadow runs. It is the
    ONLY condition a flag can satisfy, and it is not enough."""
    return (str(environ.get(ra.AUTHORITY_FLAG, "") or "").strip().lower() == ra.MODE_LIMITED_COMMON_AUTHORITY
            and str(environ.get(ra.ENVIRONMENT_FLAG, "") or "").strip().lower() == "development" and rs.mode(environ=environ) != rs.MODE_OFF)


def arming_of(site: "DormantPairSite", environ: Mapping[str, str] | None = None) -> dict:
    """The nine conditions of arming, each a boolean read from the repository's own evidence. ``armed`` is their conjunction.

    Nothing here reads ``COMMON_CORE_RUNTIME_AUTHORITY``, an environment variable other than the developer capability, a snapshot NAME, or a file. The two
    faculty conditions read source constants this package leaves empty."""
    live = os.environ if environ is None else environ
    lineage = pair.live_lineage()
    grants = [grant for grant in GRANT_REGISTRY if not grant_problems(grant, bound=site.bound, case_id=site.case_id, lineage=lineage)]
    conditions = {
        "global_development_capability": _capability(live),
        "correct_mode": site.mode == mv.PAIR_PRESSURE_CONSCIOUSNESS,
        "certified_lineage": bool(ev.core_lineage_ok()) and pair.lineage_is_v1(lineage),
        "exact_snapshot": pair.bound_is_v1(site.bound) and site.runner is not None and pair.runner_is_bound(site.runner, site.bound),
        "explicit_pair_authority_grant": bool(grants),
        "case_allowlisted": site.case_id in ra.AUTHORITY_CASES,
        "experiment_not_halted": site.state not in TERMINAL_STATES and site.halt is None,
        "faculty_approval_permits_domain": FACULTY_APPROVAL.get(PAIR_DOMAIN) == GRANTED,
        "technical_site_healthy": not site.violations and site.runner is not None and not site.runner.failures,
    }
    return {"armed": all(conditions.values()), "conditions": conditions, "failed": [name for name in ARMING_CONDITIONS if not conditions[name]],
            "faculty_conditions": {name: conditions[name] for name in FACULTY_CONDITIONS}}


# -- the site ------------------------------------------------------------------------------------------------------------------------------------------
class StateMachineError(RuntimeError):
    """A move the state machine does not allow."""


class DormantPairSite(pair.PairDryEvaluator):
    """The dormant pair authority site of ONE encounter: the pair evaluator, a state machine, an arming gate, a commit-or-abort interface and an artifact.

    ``minute`` and ``settle`` are the ones the page's single hook calls. ``request_commit`` is never called by the page, and refuses unless ARMED (never, today)."""

    mode = mv.PAIR_PRESSURE_CONSCIOUSNESS

    def __init__(self, bound, case_id: str, arrival_state: Mapping, *, experiment_id: str = "", time_limit: int = pair.TIME_LIMIT_MIN, lineage: Mapping | None = None,
                 environ: Mapping[str, str] | None = None, simulate_prior_authority: bool = False):
        super().__init__(bound, case_id, arrival_state, time_limit=time_limit, lineage=lineage)
        self.environ = environ
        self.encounter_id = rs._encounter_id(dict(arrival_state))
        self.experiment_id = str(experiment_id) or f"dormant-{case_id}-{self.encounter_id[:12]}"
        self.state = NOT_STARTED
        self.transitions: list = [{"to": NOT_STARTED, "minute": None, "why": "the experiment exists and has evaluated nothing"}]
        self._rest = NOT_STARTED
        #: TEST ONLY: pretend authority had already begun, to exercise the post-authority failure path without any real commit (FD-AUTH-20, 230B).
        self.simulated_prior_authority = bool(simulate_prior_authority)
        self.commit_requests: list = []
        self.replay_inputs: dict = {}
        self.stored: Mapping | None = None
        self._commit_evidence: dict | None = None

    # -- the state machine -------------------------------------------------------------------------------------------------------------------------
    def _move(self, to: str, *, minute: int | None = None, why: str = "") -> None:
        if to == self.state:
            return
        if to not in TRANSITIONS.get(self.state, ()):
            raise StateMachineError(f"{self.state} -> {to} is not a move of the dormant site")
        self.state = to
        self.transitions.append({"to": to, "minute": minute, "why": why})

    def authority_began(self) -> bool:
        """Has authority begun? In a dormant evaluation: a WOULD_COMMIT minute exists (or a test simulated one). It decides how a failure ends (FD-AUTH-20)."""
        return bool(self.would_commit) or self.simulated_prior_authority

    def continuation(self) -> dict:
        """What may happen to the encounter next, as the state machine sees it. The legacy engine is the authority today, whatever this says: this reads, decides
        nothing and writes nothing. After authority began, a failure is INVALID_FOR_CONTINUATION and the legacy engine may NOT quietly take over (FD-AUTH-20)."""
        if self.state == INVALID_FOR_CONTINUATION:
            return {"state": self.state, "legacy_may_continue_silently": False, "encounter_valid_for_continuation": False, "why": NO_SILENT_FALLBACK}
        if self.state == EXPERIMENT_HALTED and not self.authority_began():
            return {"state": self.state, "legacy_may_continue_silently": True, "encounter_valid_for_continuation": True,
                    "why": "authority never began: the experiment ends and the legacy encounter was never changed"}
        return {"state": self.state, "legacy_may_continue_silently": True, "encounter_valid_for_continuation": True, "why": "the experiment is evaluating; nothing is authoritative"}

    def request_legacy_fallback(self) -> dict:
        """Ask for the legacy engine to take the encounter back from the experiment. Granted only while authority has NOT begun (no would-commit minute exists and
        none was simulated); refused once it has, in ANY state -- evaluating or halted --: leaving an experiment whose authority began is an explicit, recorded act
        (``request_abort``), and a halt after it is INVALID_FOR_CONTINUATION, never a silent return. Authority that alternates is not authority."""
        verdict = self.continuation()
        granted = bool(verdict["legacy_may_continue_silently"]) and not self.authority_began()
        return {"granted": granted, "state": self.state, "why": verdict["why"] if granted or self.state == INVALID_FOR_CONTINUATION else NO_SILENT_FALLBACK}

    def _stamp_after_refusal(self, minute: int) -> None:
        """A refusal just created the halt: record its consequence in the terms of this site's own authority notion (simulated prior authority included)."""
        halt = self.halt
        if halt is None:
            return
        if self.simulated_prior_authority and not halt.get("authority_had_begun"):
            halt["authority_had_begun"] = True
            halt["simulated_prior_authority"] = True
            halt["consequence"] = ("the experiment hard-stops; the encounter is INVALID_FOR_CONTINUATION and is never continued with the legacy engine "
                                   "(authority was SIMULATED as begun, in a test)")
        if self.state not in TERMINAL_STATES:
            if self.state == NOT_STARTED:
                self._move(EVALUATING, minute=minute, why="a refusal before any turn was evaluated")
            self._move(WOULD_ABORT, minute=minute, why=f"refused: {halt.get('failed_checks')}")
            self._move(INVALID_FOR_CONTINUATION if halt.get("authority_had_begun") else EXPERIMENT_HALTED, minute=minute,
                       why="authority had begun: no fallback to the legacy engine" if halt.get("authority_had_begun") else "authority never began: the legacy encounter is untouched")

    # -- one turn ----------------------------------------------------------------------------------------------------------------------------------
    def minute(self, before, after, session, ran, submission_id=None, route=pair.ORDER_TURN) -> dict:
        rest = self.state
        if rest not in TERMINAL_STATES:
            self._move(EVALUATING, minute=pair._as_int(after.get("sim_time")) if isinstance(after, Mapping) else None, why="a turn moved the clock")
        self._commit_evidence = None
        record = super().minute(before, after, session, ran, submission_id, route)
        self._capture_replay_inputs(session)
        verdict, at = record.get("verdict"), record.get("minute")
        if self.state not in TERMINAL_STATES:
            if verdict == pair.WOULD_COMMIT:
                self._move(WOULD_COMMIT, minute=at, why="every minute of the interval validated")
            elif verdict == pair.NO_ADVANCE:
                self._move(NOT_STARTED if rest == NOT_STARTED else WOULD_COMMIT, minute=at, why="the clock did not move: no new minute")
            else:
                self._stamp_after_refusal(at)
        return record

    def _refuse(self, record, minute, failed, detail, stage) -> None:
        first = self.halt is None
        super()._refuse(record, minute, failed, detail, stage)
        if first:
            self._stamp_after_refusal(minute)

    def settle(self, orders: Sequence | None) -> None:
        had = self.halt is not None
        super().settle(orders)
        if self.halt is not None and not had:
            self._stamp_after_refusal(self.halt["minute"])
            # the base class stamped the record's digest before the stamp above could change the halt: recompute it
            if self.records:
                self.records[-1]["digest"] = ra.digest_of({key: value for key, value in self.records[-1].items() if key != "digest"})

    def _evaluate(self, record, minute, before, after, legacy_observable, session, ran, candidate, route) -> None:
        super()._evaluate(record, minute, before, after, legacy_observable, session, ran, candidate, route)
        if record.get("verdict") == pair.WOULD_COMMIT:
            # What a commit would need, kept IN MEMORY only (never in the artifact): the state the minute was evaluated on and the legacy pressure beside it.
            self._commit_evidence = {"after": deepcopy(dict(after)), "legacy_pressure": ra.pressure_point(legacy_observable), "payload": dict(record["would_write"]),
                                     "pressure_kwargs": self._last_pressure_kwargs, "interval_rows": [dict(row) for row in record.get("interval") or []]}

    def _capture_replay_inputs(self, session) -> None:
        """The two immutable inputs the artifact replays: the pressure run's (the session's) and the bound run's (this site's). Never raises."""
        try:
            pressure = ra.AuthoritySite._artifact_input(session)
            captured = None if self.runner is None else self.runner.replay_input()
            self.replay_inputs = {"pressure": None if pressure is None else json.loads(ra.canonical(pressure)),
                                  "bound": None if captured is None else json.loads(ra.canonical(captured.to_dict()))}
        except Exception as error:
            self.replay_inputs = {"pressure": None, "bound": None, "error": f"{type(error).__name__}: {error}"}

    # -- the arming gate and the commit-or-abort interface -----------------------------------------------------------------------------------------
    def arming(self, environ: Mapping[str, str] | None = None) -> dict:
        return arming_of(self, self.environ if environ is None else environ)

    def request_abort(self, reason: str) -> dict:
        """The abort half of the interface: stop the experiment, visibly, with nothing committed. A second abort, or one after a halt, changes nothing."""
        if self.state in TERMINAL_STATES:
            return {"aborted": False, "state": self.state, "why": "the experiment is already halted"}
        minute = self._last_seen
        self.phase = pair.HALTED
        began = self.authority_began()
        self.halt = {"minute": minute, "failed_checks": ["abort_requested"], "authority_had_begun": began, "stage": "requested", "detail": {"reason": str(reason)},
                     "consequence": ("the experiment hard-stops on request; authority had begun, so the encounter is INVALID_FOR_CONTINUATION and is never continued with the legacy engine"
                                     if began else "the experiment hard-stops on request; authority never began and the legacy encounter is untouched")}
        self._stamp_after_refusal(minute)
        return {"aborted": True, "state": self.state, "continuation": self.continuation()}

    def request_commit(self, target: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
        """The commit half. REFUSED unless the site is ARMED (never, today), and even then only the pair transaction can write -- into a NEW mapping, after it
        re-evaluated the pressure authority gate (the second lock). The page never calls this.

        Returns ``{committed, outcome, prepared, ...}``; ``prepared`` is None in every refusal and ``target`` is never touched."""
        live = self.environ if environ is None else environ
        arming = arming_of(self, live)
        entry = {"minute": self._last_seen, "state": self.state, "armed": arming["armed"], "failed_conditions": arming["failed"], "outcome": None, "committed": False}
        self.commit_requests.append(entry)
        result = {"committed": False, "prepared": None, "outcome": None, "armed": arming["armed"], "arming": arming, "state": self.state}

        def refuse(outcome: str, reason: str = "") -> dict:
            entry["outcome"] = result["outcome"] = outcome
            result["reason"] = reason
            return result
        if self.state in TERMINAL_STATES:
            return refuse(COMMIT_REFUSED_HALTED, f"the experiment is {self.state}")
        if not arming["armed"]:
            return refuse(COMMIT_REFUSED_NOT_ARMED, f"failed: {arming['failed']}")
        # The second lock stands ON ITS OWN: even with the faculty's two constants satisfied, the pair may be committed only if version 1 itself is in the authority
        # registry. Ratification for development experiments is not that approval (FD-AUTH-11), and the pressure point's real approval (``gi_pressure_committed``) is
        # not version 1's: a commit that named it would otherwise pass the pressure gate for a pair nobody approved.
        if pair.V1_ID not in ra.APPROVED_SNAPSHOTS:
            return refuse(COMMIT_REFUSED_V1_NOT_APPROVED, f"{pair.V1_ID} is ratified for development experiments and is not in the authority registry")
        evidence = self._commit_evidence
        if evidence is None or self.state != WOULD_COMMIT:
            return refuse(COMMIT_REFUSED_NO_INTERVAL, "the last turn did not validate an interval")
        if any(item.get("committed") and item.get("minute") == self._last_seen for item in self.commit_requests[:-1]):
            return refuse(COMMIT_REFUSED_ALREADY_PREPARED, f"minute {self._last_seen} already has a prepared commit")
        if ra.digest_of(target) != ra.digest_of(evidence["after"]):
            return refuse(COMMIT_REFUSED_OTHER_STATE, "a commit applies to exactly the state the interval was evaluated on")
        try:
            payload = pair.PairPayload(**evidence["payload"])
            snapshot = self.pressure_snapshot
            transaction = pair.PairAuthorityTransaction(minute=payload.minute, case_id=self.case_id, snapshot=snapshot, bound=self.bound)
            transaction.capture(evidence["after"]).compute(payload, evidence["legacy_pressure"])
            kwargs = evidence["pressure_kwargs"]                      # exactly what the evaluator proved for this minute: the replay digest, the expected one, the failures
            if not kwargs:
                raise ra.AuthorityRefused("the evaluation kept no pressure validation to commit on")
            transaction.validate(pressure=kwargs, consciousness_ok={}, interval_ok=all(row["ok"] for row in evidence["interval_rows"]), boundary_clear=True,
                                 window_open=payload.minute <= self.time_limit, one_course=True)
            prepared = transaction.commit(deepcopy(dict(target)), environ=live)
        except Exception as error:                                   # every failure is a refusal with nothing written
            return refuse(COMMIT_REFUSED_BY_TRANSACTION, f"{type(error).__name__}: {error}")
        entry["committed"], entry["outcome"] = True, COMMIT_PREPARED_FOR_THE_CALLER
        result.update(committed=True, prepared=prepared, outcome=COMMIT_PREPARED_FOR_THE_CALLER)
        return result

    # -- the artifact ------------------------------------------------------------------------------------------------------------------------------
    def artifact(self) -> dict:
        """The immutable record of this dormant evaluation, digested over its canonical form. It never claims authority was committed, and never raises."""
        try:
            return self._artifact()
        except Exception as error:
            return {"artifact": ARTIFACT_TYPE, "label": LABEL, "committed_authority": False, "case_id": self.case_id, "experiment_id": self.experiment_id,
                    "state": self.state, "turns": [], "artifact_digest": "", "error": f"{type(error).__name__}: {error}"}

    def _artifact(self) -> dict:
        arming = self.arming()
        turns = []
        for record in self.records:
            rows = list(record.get("interval") or [])
            first = next((row for row in rows if not row["ok"]), None)
            turns.append({"ineligible_after": [] if first is None else [row["minute"] for row in rows if row["minute"] > first["minute"]],
                          **{key: record.get(key) for key in ("minute", "route", "verdict", "reason", "failed_checks", "detail", "legacy", "common", "would_write", "would_move",
                                                            "interval", "action_kinds", "no_common_physiology", "settled_classes", "dispositions", "settlement_refusal",
                                                            "phase_before", "phase_after", "digest")}})
        body = {
            "artifact": ARTIFACT_TYPE, "label": LABEL, "authority_mode": AUTHORITY_MODE, "committed_authority": False, "site": MODULE_VERSION,
            "experiment_id": self.experiment_id, "encounter_id": self.encounter_id, "case_id": self.case_id, "family": ra.AUTHORITY_FAMILY,
            "granularity": GRANULARITY, "time_limit": self.time_limit, "validation_mode": self.mode,
            "snapshot": self.bound.summary(), "snapshot_status": pair.RATIFIED, "snapshot_is_authority_approved": False,
            "lineage": pair.live_lineage(), "phase2_digest": rs.PHASE2_DIGEST, "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "arming": {"armed": arming["armed"], "conditions": arming["conditions"], "failed": arming["failed"]},
            "state": self.state, "transitions": [dict(item) for item in self.transitions], "continuation": self.continuation(),
            "authority_had_begun": self.authority_began(), "simulated_prior_authority": self.simulated_prior_authority,
            "halt": None if self.halt is None else json.loads(ra.canonical(self.halt)),
            "turns": turns, "would_commit_minutes": list(self.would_commit), "commit_requests": [dict(item) for item in self.commit_requests],
            "violations": list(self.violations), "replay_inputs": self.replay_inputs,
        }
        body["artifact_digest"] = ra.digest_of(body)
        return json.loads(ra.canonical(body))

    def persist(self, environ: Mapping[str, str] | None = None) -> dict:
        """Hand the artifact to the faculty store (its own sub-directory). Never raises; writes nothing unless a faculty environment named a directory."""
        live = self.environ if environ is None else environ
        if store.root(live) is None:
            self.stored = {"stored": False, "why": store.NOT_CONFIGURED}               # nothing to write to: do not serialize the whole run for nothing
        else:
            self.stored = persist_artifact(self.artifact(), environ=live)
        return dict(self.stored)


# -- the artifact: schema, verification, replay, persistence ---------------------------------------------------------------------------------------------
REQUIRED_FIELDS = ("artifact", "label", "authority_mode", "committed_authority", "site", "experiment_id", "encounter_id", "case_id", "family", "granularity", "snapshot",
                   "snapshot_status", "snapshot_is_authority_approved", "lineage", "phase2_digest", "arming", "state", "transitions", "continuation", "authority_had_begun",
                   "halt", "turns", "would_commit_minutes", "commit_requests", "violations", "replay_inputs", "artifact_digest")
REQUIRED_TURN_FIELDS = ("minute", "route", "verdict", "failed_checks", "legacy", "common", "interval", "action_kinds", "digest")


def _consistency_problems(artifact: Mapping) -> list:
    """What a dormant evaluation's artifact must say about ITSELF, whatever its digest: a legal history of the machine, a state that is the history's end, an
    authority flag that agrees with the would-commit minutes and with the halt, no armed gate, no prepared commit, and the minutes of the turns in order."""
    problems = []
    try:
        history = [item.get("to") for item in artifact.get("transitions") or []]
        if not history or history[0] != NOT_STARTED:
            problems.append("history does not start at NOT_STARTED")
        for before, after in zip(history, history[1:]):
            if after not in TRANSITIONS.get(before, ()):
                problems.append(f"illegal move {before} -> {after}")
        if history and history[-1] != artifact.get("state"):
            problems.append("state is not the end of the history")
        turns = list(artifact.get("turns") or [])
        commits = [turn["minute"] for turn in turns if turn.get("verdict") == WOULD_COMMIT]
        if commits != list(artifact.get("would_commit_minutes") or []) or commits != sorted(set(commits)):
            problems.append("would_commit_minutes are not the strictly increasing minutes of the WOULD_COMMIT turns")
        if [turn["minute"] for turn in turns] != sorted(turn["minute"] for turn in turns):
            problems.append("turns are not in minute order")
        began = bool(commits) or bool(artifact.get("simulated_prior_authority"))
        if bool(artifact.get("authority_had_begun")) != began:
            problems.append("authority_had_begun disagrees with the would-commit minutes")
        halt, state = artifact.get("halt"), artifact.get("state")
        if halt is not None and bool(halt.get("authority_had_begun")) != began:
            problems.append("the halt and the artifact disagree about whether authority began")
        if (state == INVALID_FOR_CONTINUATION) != (halt is not None and began) or (state == EXPERIMENT_HALTED) != (halt is not None and not began):
            problems.append("the halt state does not follow from whether authority began")
        if (artifact.get("arming") or {}).get("armed") is not False or any(item.get("committed") for item in artifact.get("commit_requests") or []):
            problems.append("an armed gate or a prepared commit: this is not a dormant evaluation")
        snapshot = artifact.get("snapshot") or {}
        if (snapshot.get("snapshot_id"), snapshot.get("record_digest"), snapshot.get("profile_digest"), snapshot.get("core_digest")) != (
                pair.V1_ID, pair.V1_RECORD_DIGEST, pair.V1_PROFILE_DIGEST, pair.V1_CORE_DIGEST) or (artifact.get("lineage") or {}).get("digest") != pair.V1_CORE_DIGEST:
            problems.append("the artifact does not name the pinned version 1 and its core")
    except Exception as error:
        problems.append(f"{type(error).__name__}: {error}")
    return problems


def verify_artifact(artifact: Mapping) -> dict:
    """The digest recomputes, every field the schema names is present, the label says DORMANT, the artifact claims no committed authority, and it is consistent with
    itself (``_consistency_problems``). A signature is not required by this package: the checks the digest cannot make are made by ``replay_artifact``."""
    body = dict(artifact or {})
    stored = body.pop("artifact_digest", None)
    missing = [name for name in REQUIRED_FIELDS if name not in artifact]
    incomplete = [turn.get("minute") for turn in (artifact or {}).get("turns") or [] if any(name not in turn for name in REQUIRED_TURN_FIELDS)]
    honest = (artifact or {}).get("label") == LABEL and (artifact or {}).get("committed_authority") is False and (artifact or {}).get("artifact") == ARTIFACT_TYPE
    digest_matches = bool(stored) and ra.digest_of(body) == stored
    problems = [] if missing or incomplete else _consistency_problems(artifact)
    return {"digest_matches": digest_matches, "complete": not missing and not incomplete, "missing_fields": missing, "incomplete_turns": incomplete,
            "claims_no_committed_authority": bool(honest), "consistent": not problems, "consistency_problems": problems,
            "verified": bool(digest_matches and not missing and not incomplete and honest and not problems)}


def replay_artifact(artifact: Mapping) -> dict:
    """Rebuild, FROM THE ARTIFACT ALONE, what each turn recorded, and re-derive the decisions that depend on the run (P3-229B).

    * the snapshot: the bound run's profile is rebuilt from its immutable input and must be the pinned version 1's profile, and the artifact must name it;
    * the pressure candidate of every turn from the pressure run's immutable input; the category, word, collapse state, pulse, F, burden and delivery from the bound
      run's immutable input (``fam.artifact_rows``, the way a trace is replayed) -- the WHOLE recorded candidate, not three of its fields;
    * for every WOULD_COMMIT: the payload it would write re-derived (shaped the way the legacy engine shows the pressures), the interval it validated exactly the minutes
      since the previous turn, every row valid and replay-valid (the ladder, the core's own reading, the pulse), the boundary clear, and the window open;
    * for every aborted turn: a name for the refusal, nothing written, ``window_open`` named exactly when the minute is past the limit, and a collapse-boundary abort
      only where the replay shows an established (or unreadable) minute.
    Returns ``{reproduces, candidate_matches, decisions_match, snapshot_matches, mismatches, compared}``; it never raises."""
    mismatches: list = []
    out = {"reproduces": False, "candidate_matches": False, "decisions_match": False, "snapshot_matches": False, "mismatches": mismatches, "compared": 0}
    try:
        inputs = dict((artifact or {}).get("replay_inputs") or {})
        table = mv.replay_table(inputs.get("pressure")) if inputs.get("pressure") else None
        scenario = None if not inputs.get("bound") else inputs["bound"].get("scenario")
        rows = {row["minute"]: row["channels"] for row in fam.artifact_rows(scenario)} if scenario else {}
        if table is None or not rows:
            mismatches.append("the artifact carries no replay input")
            return out
        profile = fam._replay_trajectory(scenario)[2]
        out["snapshot_matches"] = pair.profile_digest(profile) == pair.V1_PROFILE_DIGEST == (artifact.get("snapshot") or {}).get("profile_digest")
        if not out["snapshot_matches"]:
            mismatches.append("the bound run's rebuilt profile is not the pinned version 1's, or the artifact names another")
        candidate_ok, decisions_ok, previous, cleared_through = True, True, 0, 0
        limit = int(artifact.get("time_limit"))
        for turn in (artifact.get("turns") or []):
            minute, common, verdict = int(turn["minute"]), turn.get("common"), turn.get("verdict")
            channels, pressure = rows.get(minute), table.get(minute)
            if common is not None:
                out["compared"] += 1
                category = None if channels is None else channels.get("category_index")
                expected = None if channels is None or pressure is None else {
                    "sbp": pressure["sbp"], "dbp": pressure["dbp"], "category": category, WORD: pair.WORD_OF.get(category),
                    "F": channels.get("systemic_encephalopathy_burden"), "collapse_burden": channels.get("collapse_burden"),
                    "collapse_state": channels.get("collapse_state_index"), "relative_delivery": channels.get("relative_delivery"),
                    "relative_perfusion": channels.get("relative_perfusion"), "pulse_present": channels.get("pulse_present")}
                # the artifact keeps the run's own floats; the replay table is the pressure point the authority layer compares, rounded the one way it always is
                rounded = ra.pressure_point({"sbp": common.get("sbp"), "dbp": common.get("dbp")})
                shown = {"sbp": rounded["sbp"], "dbp": rounded["dbp"], **{name: common.get(name) for name in (
                    "category", WORD, "F", "collapse_burden", "collapse_state", "relative_delivery", "relative_perfusion", "pulse_present")}}
                if expected is None or expected != shown:
                    candidate_ok = False
                    mismatches.append(f"minute {minute}: the recorded candidate is not the replayed one: {shown} != {expected}")
            elif verdict == WOULD_COMMIT:
                candidate_ok = False
                mismatches.append(f"minute {minute}: a WOULD_COMMIT turn recorded no candidate")
            if verdict in (WOULD_COMMIT, WOULD_ABORT) and not {"transaction_completed", "encounter_state_untouched"} & set(turn.get("failed_checks") or []):
                if (minute > limit) != ("window_open" in (turn.get("failed_checks") or [])):
                    decisions_ok = False
                    mismatches.append(f"minute {minute}: window_open is recorded {'failed' if minute <= limit else 'passed'} against a limit of {limit}")
            if verdict == WOULD_COMMIT:
                if turn.get("failed_checks") or turn.get("would_write") is None:
                    decisions_ok = False
                    mismatches.append(f"minute {minute}: a WOULD_COMMIT turn that records a failed check or no payload")
                interval = list(turn.get("interval") or [])
                if [row["minute"] for row in interval] != list(range(previous + 1, minute + 1)):
                    decisions_ok = False
                    mismatches.append(f"minute {minute}: the interval is not every minute since minute {previous}")
                for row in interval:
                    channel = rows.get(row["minute"])
                    replay_ok = (channel is not None and type(channel.get("category_index")) is int and channel.get("category_index") in mv.LADDER
                                 and channel.get("consciousness_level") == channel.get("category_index") and channel.get("pulse_present") is True
                                 and table.get(row["minute"]) is not None)
                    if not replay_ok or not row["ok"] or row["failed"]:
                        decisions_ok = False
                        mismatches.append(f"minute {row['minute']}: recorded valid, but the replay does not validate it")
                states = [(index, rows.get(index, {}).get("collapse_state_index")) for index in range(cleared_through + 1, minute + 1)]
                if any(type(state) is not int or state >= pair.ESTABLISHED for _, state in states):
                    decisions_ok = False
                    mismatches.append(f"minute {minute}: recorded WOULD_COMMIT across an established collapse or an unreadable minute")
                cleared_through = minute
                if channels is not None and pressure is not None and turn.get("would_write") is not None:
                    shaped = ra.shaped_like_legacy(pressure, {"sbp": (turn.get("legacy") or {}).get("sbp"), "dbp": (turn.get("legacy") or {}).get("dbp")})
                    payload = pair.payload_from(minute, shaped, {"category": channels.get("category_index"), "pulse_present": channels.get("pulse_present")}).as_dict()
                    if turn["would_write"] != payload:
                        decisions_ok = False
                        mismatches.append(f"minute {minute}: the payload a commit would write is not the replayed one: {turn['would_write']} != {payload}")
            elif verdict == WOULD_ABORT:
                if not turn.get("failed_checks") or turn.get("would_write") is not None:
                    decisions_ok = False
                    mismatches.append(f"minute {minute}: a WOULD_ABORT turn that names no failed check, or that still records a payload")
                if "collapse_boundary_not_reached" in (turn.get("failed_checks") or []):
                    states = [rows.get(index, {}).get("collapse_state_index") for index in range(cleared_through + 1, minute + 1)]
                    if not any(type(state) is not int or state >= pair.ESTABLISHED for state in states):
                        decisions_ok = False
                        mismatches.append(f"minute {minute}: recorded a collapse-boundary abort, but the replay shows no established collapse")
            previous = minute
        out.update(candidate_matches=candidate_ok, decisions_match=decisions_ok,
                   reproduces=bool(candidate_ok and decisions_ok and out["snapshot_matches"] and out["compared"] > 0))
    except Exception as error:
        mismatches.append(f"{type(error).__name__}: {error}")
    return out


SUBDIRECTORY = "pair_dormant"


def artifact_name(artifact: Mapping) -> str:
    body = dict(artifact)
    turns = list(body.get("turns") or [])
    last = turns[-1].get("minute") if turns else "x"
    return f"{body.get('case_id') or 'case'}__{body.get('experiment_id') or 'experiment'}__m{last}__{str(body.get('state') or 'x').lower()}__{str(body.get('artifact_digest') or '')[:16]}.json"


def persist_artifact(artifact: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
    """Write one immutable record under the faculty store's own sub-directory, or say why not. Never raises; create-only like the pressure store."""
    try:
        body = dict(artifact)
        if body.get("artifact") != ARTIFACT_TYPE or body.get("committed_authority") is not False or not body.get("artifact_digest"):
            return {"stored": False, "why": store.NOT_AN_ARTIFACT}
        directory = store.root(environ)
        if directory is None:
            return {"stored": False, "why": store.NOT_CONFIGURED}
        directory = directory / SUBDIRECTORY
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / artifact_name(body)
        payload = ra.canonical({"store": MODULE_VERSION, "artifact": body})
        if path.exists():
            if path.read_text(encoding="utf-8") == payload:
                return {"stored": True, "idempotent": True, "path": str(path), "why": ""}
            return {"stored": False, "why": store.COLLISION, "path": str(path)}
        path.write_text(payload, encoding="utf-8")
        return {"stored": True, "idempotent": False, "path": str(path), "bytes": len(payload.encode("utf-8")), "why": ""}
    except Exception as error:
        return {"stored": False, "why": f"STORE_ERROR {type(error).__name__}: {error}"}


def stored_artifacts(*, environ: Mapping[str, str] | None = None) -> list:
    directory = store.root(environ)
    if directory is None or not (directory / SUBDIRECTORY).exists():
        return []
    found = []
    for path in sorted((directory / SUBDIRECTORY).glob("*.json")):
        try:
            found.append(dict(json.loads(path.read_text(encoding="utf-8")).get("artifact") or {}))
        except Exception:
            continue
    return found
