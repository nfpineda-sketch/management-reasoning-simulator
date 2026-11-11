"""P3-203 and P3-205 to P3-207: the pressure + consciousness pair as ONE authority transaction, run DRY (commit disabled by construction).

TEST-SIDE. The legacy engine stays the only authority of the encounter: this module never calls ``AuthorityTransaction.commit``, sets no
authority flag, opens no authority site and writes nothing to a patient state. Each turn it builds what the transaction WOULD do and says
``WOULD_COMMIT`` or ``WOULD_ABORT``; the state it was handed is hashed before and after, and a difference is an error of this harness.

What is real and what is proposed.

* REAL (reused, unchanged): the pressure half is the existing transaction -- ``AuthorityTransaction.capture`` / ``compute`` / ``validate`` with the
  approved pressure point ``gi_pressure_committed``, the candidate ``pressure_point`` of the session's own run, its replay from the immutable
  artifact, ``shaped_like_legacy``, ``action_kinds`` and ``unsupported_among``. Every pressure refusal below is one of ITS validation names.
* PROPOSED (this module, nothing in the layer implements it): the consciousness half and the pairing. The candidate comes from ONE run of the
  common core under the BOUND snapshot (``test_gi_snapshot_binding``); the pair is accepted only if that run and the pressure run are the same
  physical course; the collapse-boundary guard (FD-AUTH-06) and the window (FD-AUTH-07) are checked BEFORE a commit would happen.

The transaction, in order: capture -> compute (exact V1) -> validate lineage -> snapshot -> action -> pressure -> consciousness -> boundary ->
WOULD_COMMIT / WOULD_ABORT. After the first WOULD_ABORT the experiment is HALTED for the encounter: no later minute is evaluated as a commit.

Hardened after the independent review of P3-208 (each item is a probe that got through before and is refused now):

* the snapshot check compares the run with the PINNED digests of version 1, not with whatever the binding object says, and the arrival anchors
  of the bound run with those of the session's run;
* the lineage is READ every minute (the layer's verdict and the core's own bytes); a lineage a caller offers can only add a refusal;
* an exception inside the transaction is a WOULD_ABORT with a record and a halt, and it never reaches the legacy turn;
* a turn the transaction did not see (the clock moved without it) is a WOULD_ABORT: ``turn_was_observed``;
* clinical time outside an order turn (``ShadowSession.observe_time``, the route of ``app.spend_clinical_time``) has NO authority site in the
  layer today, so it is a WOULD_ABORT here: ``turn_has_a_transaction_site``;
* the transaction works on a COPY of the state: it cannot change the encounter, and the guard that proves it keeps a record instead of raising
  into the turn (``run`` raises after the encounter ends);
* the failures and the one-course check cover EVERY minute of the turn, not only its last one (stricter than the existing pressure site, whose
  rule reads the turn's last minute);
* the time limit a caller passes can shorten the window and never lengthen it.
"""
from __future__ import annotations

import dataclasses
import json
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Mapping, Sequence

import pilot_acceptance as acceptance
import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import test_gi_amendment_2_series as series
import test_gi_snapshot_binding as binding
from clinical_core import legacy_adapter

DRY_RUN_VERSION = "P3-206"
#: FD-AUTH-07: the predefined experimental time limit. The window ends at min(this, the first established-collapse boundary).
TIME_LIMIT_MIN = 240
WOULD_COMMIT, WOULD_ABORT, HALTED = "WOULD_COMMIT", "WOULD_ABORT", "EXPERIMENT_HALTED"
NOT_STARTED, ACTIVE = "NOT_STARTED", "ACTIVE"
#: The pair, and nothing else. ``map`` is the display's own mean of the two pressures (the existing rule); ``mental_status`` is the legacy word
#: of the common observable category.
PRESSURE_FIELDS = ("sbp", "dbp", "map")
CONSCIOUSNESS_FIELD = "mental_status"
PAIR_DOMAIN = PRESSURE_FIELDS + (CONSCIOUSNESS_FIELD,)
#: Never authoritative in this design: recorded, compared, not written.
RECORD_ONLY = ("collapse_state",)
NEVER_WRITTEN = ("hr", "spo2", "respiratory_rate", "crt", "rhythm", "pulse_present", "lactate", "hemoglobin")
#: The legacy word of each common category: the inverse of the certified comparison's own table (``legacy_adapter.LEVEL_OF``).
WORD_OF = {level: word for word, level in legacy_adapter.LEVEL_OF.items()}
ESTABLISHED = 2
#: The readings of one common state that do NOT depend on the Amendment-2 magnitudes: equal in the pressure run and in the bound run, or the
#: pair is not one course.
SHARED_READINGS = tuple(name for name in fam.TRACE_READINGS if name != "consciousness_level")

#: The checks, in the order the transaction applies them. A name here is what a refusal reports.
CHECKS = ("transaction_completed", "encounter_state_untouched", "turn_has_a_transaction_site", "turn_was_observed",
          "lineage_certified", "snapshot_bound", "case_eligible", "supported_management", "minute_not_already_committed",
          "pressure_candidate_present", "pressure_validated", "consciousness_candidate_present", "consciousness_reproducible",
          "pair_is_one_course", "collapse_boundary_not_reached", "window_open", "common_run_did_not_fail", "only_the_pair_would_move")
#: The routes by which the engine's clock moves. Only the first has an authority site in the layer today.
ORDER_TURN, TIME_OUTSIDE_AN_ORDER = "order_turn", "time_outside_an_order_turn"


class DryRunViolation(AssertionError):
    """The harness changed something it must not change. Never a clinical outcome: a defect of this module. It is raised by ``run`` AFTER the
    encounter ended, never from inside a legacy turn: an exception there would itself change the encounter."""


def _digest(value: Any) -> str | None:
    try:
        return authority.digest_of(value)
    except Exception:
        return None


def _plain(value: Any) -> Any:
    """A detail for the record: plain data, or its text when it is not."""
    try:
        return json.loads(json.dumps(value))
    except Exception:
        return repr(value)


def _anchors_digest(runner: Any) -> str | None:
    try:
        return authority.digest_of(dataclasses.asdict(runner.anchors))
    except Exception:
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def legacy_point(observable: Mapping) -> dict:
    """What the legacy engine shows for the pair at this minute (the resident's truth; read, never written)."""
    sbp, dbp = observable.get("sbp"), observable.get("dbp")
    return {"sbp": sbp, "dbp": dbp, "map": authority.derived_map(sbp, dbp), "mental_status": observable.get("mental_status"),
            "pulse_present": observable.get("pulse_present", True)}


class PairDryRun:
    """The dry transaction of ONE encounter. ``minute`` is called where an authority site's minute would be: after the shadow observed the turn."""

    def __init__(self, bound: binding.BoundSnapshot, case_id: str, arrival_state: Mapping, *, time_limit: int = TIME_LIMIT_MIN,
                 lineage: Mapping | None = None):
        if not binding.bound_is_v1(bound):
            raise binding.SnapshotBindingError([binding.WRONG_SNAPSHOT_ID])
        #: FD-AUTH-07: the predefined limit is the ceiling. A caller may shorten the window, never lengthen it.
        self.bound, self.case_id, self.time_limit = bound, str(case_id), max(0, min(int(time_limit), TIME_LIMIT_MIN))
        self.runner = binding.open_bound_runner(bound, case_id, deepcopy(dict(arrival_state)))
        self.pressure_snapshot = authority.approved_snapshot(binding.PRESSURE_POINT, environment="development", family=authority.AUTHORITY_FAMILY,
                                                             case_id=self.case_id, domain=authority.AUTHORITY_DOMAIN)
        #: A lineage the caller OFFERS (a tamper control offers a wrong one). It can only add a refusal: the live lineage is read every minute.
        self.offered_lineage = None if lineage is None else dict(lineage)
        self.lineage = binding.live_lineage()
        self.records: list = []
        self.would_commit: list = []
        self.violations: list = []
        self.phase = NOT_STARTED
        self.halt: dict | None = None
        self._cleared_through = 0          # the last minute whose collapse state this run has examined and found clear
        self._channels: dict = {}
        self._last_seen = _as_int(dict(arrival_state).get("sim_time"))   # the last minute this transaction saw: the arrival, then each turn's end
        self._failures_seen = 0            # how many of the session's failures earlier turns already read
        self._anchors = _anchors_digest(self.runner)

    # -- the common candidate under the bound snapshot ---------------------------------------------------------------------------
    def _advance(self, session, minute: int) -> None:
        if self.runner is None:
            return
        self.runner.mirror(session.mirrored)
        self.runner.advance(minute, state=session._mapping_state())
        if self.runner.failures:
            return
        for row in fam.run_channels(self.runner):
            self._channels[row["minute"]] = row

    def _candidate(self, minute: int) -> dict | None:
        row = self._channels.get(minute)
        if row is None or self.runner is None:
            return None
        result = next((item for item in reversed(self.runner.results) if item.minute == minute), None)
        channels = row["channels"]
        category = channels.get("category_index")
        return {"reproduced": "channels_unavailable" not in row, "derived": None if result is None else dict(result.derived),
                "category": category, "consciousness_level": channels.get("consciousness_level"),
                "mental_status": WORD_OF.get(category), "F": channels.get("systemic_encephalopathy_burden"),
                "collapse_burden": channels.get("collapse_burden"), "collapse_state": channels.get("collapse_state_index"),
                "relative_delivery": channels.get("relative_delivery"), "relative_perfusion": channels.get("relative_perfusion"),
                "pulse_present": channels.get("pulse_present"), "state_digest": row.get("state_digest")}

    def _boundary(self, minute: int) -> dict:
        """FD-AUTH-06, precommit: EVERY minute since the last cleared one, up to the minute that would be committed. A minute the run cannot
        show, or whose state is not exactly one of the core's three, is not a cleared minute: the guard fails closed. By design: a minute an
        earlier turn already cleared is not read again (the run's history cannot change: a rewritten minute is its own failure), and the
        boundary is ESTABLISHED collapse, not impending."""
        first, unseen = None, []
        for index in range(self._cleared_through + 1, minute + 1):
            row = self._channels.get(index)
            state = None if row is None or "channels_unavailable" in row else row["channels"].get("collapse_state_index")
            if type(state) is not int or state not in (0, 1, ESTABLISHED):
                unseen.append(index)                   # absent, or not one of the core's three states (a bool, a float, a string): not shown
            elif state >= ESTABLISHED and first is None:
                first = index
        return {"first_established_minute": first, "minutes_not_shown": unseen, "clear": first is None and not unseen}

    # -- one turn --------------------------------------------------------------------------------------------------------------------
    def minute(self, before: Mapping | None, after: Mapping, session, ran: Sequence | None, submission_id: Any = None,
               route: str = ORDER_TURN) -> dict:
        """One turn. NEVER raises and never touches ``after``: the transaction runs on a copy, an exception inside it is a WOULD_ABORT with a
        record, and the state it was handed is hashed before and after."""
        untouched = _digest(after)
        minute = _as_int(after.get("sim_time")) if isinstance(after, Mapping) else 0
        record = {"minute": minute, "route": route, "legacy": None, "common": None, "would_write": None, "would_move": None, "failed_checks": [],
                  "detail": {}, "action_kinds": [], "phase_before": self.phase}
        try:
            seen = deepcopy(dict(after))               # the transaction's own copy: nothing below can reach the encounter's state
            legacy_observable = dict(seen.get("observable") or {})
            record["legacy"] = legacy_point(legacy_observable)
            self._advance(session, minute)
            candidate = self._candidate(minute)
            record["common"] = self._shown(candidate)
            if self.halt is not None:
                record.update(verdict=HALTED, reason=f"halted at minute {self.halt['minute']}: {self.halt['failed_checks']}")
            else:
                self._evaluate(record, minute, before, seen, legacy_observable, session, ran, candidate, route)
        except Exception as error:                     # a transaction that raised did not complete: it would not commit, and it is not silent
            self._refuse(record, minute, ["transaction_completed"], {"transaction_completed": f"{type(error).__name__}: {error}"}, "exception")
        if _digest(after) != untouched:
            # Unreachable by construction (the copy above); kept as the proof. Recorded and raised by ``run`` after the encounter, never here.
            self.violations.append(f"minute {minute}: the encounter state changed while the dry run evaluated it")
            self._refuse(record, minute, ["encounter_state_untouched"], {"encounter_state_untouched": self.violations[-1]}, "state_guard")
        self._last_seen = minute
        self._failures_seen = len(list(getattr(session, "failures", []) or []))
        record["phase_after"] = self.phase
        record["digest"] = authority.digest_of({key: value for key, value in record.items() if key != "digest"})
        self.records.append(record)
        return record

    def _refuse(self, record: dict, minute: int, failed: Sequence[str], detail: Mapping, stage: str) -> None:
        """Mark this turn refused. The FIRST refusal of an encounter is its halt; a refusal after the halt marks its own record and stays HALTED."""
        names = [name for name in CHECKS if name in set(failed) | set(record.get("failed_checks") or [])]
        record["failed_checks"], record["detail"] = names, {**dict(record.get("detail") or {}), **{key: _plain(value) for key, value in dict(detail).items()}}
        record["would_write"] = None
        if record.get("verdict") == WOULD_COMMIT and minute in self.would_commit:
            self.would_commit.remove(minute)           # a turn refused after its checks passed would never have committed
        self.phase = HALTED
        if self.halt is not None:
            record.update(verdict=HALTED, reason=f"halted at minute {self.halt['minute']}: {self.halt['failed_checks']}; this turn also failed {names}")
            return
        began = bool(self.would_commit)
        record.update(verdict=WOULD_ABORT, reason=f"refused: {names}")
        self.halt = {"minute": minute, "failed_checks": list(names), "authority_had_begun": began, "stage": stage,
                     "consequence": ("the experiment hard-stops; the encounter is INVALID_FOR_CONTINUATION and is never continued with the legacy engine"
                                     if began else "authority never began; the legacy engine simply continues and no experiment exists for this encounter"),
                     "detail": dict(record["detail"])}

    @staticmethod
    def _shown(candidate: Mapping | None) -> dict | None:
        if candidate is None:
            return None
        derived = candidate["derived"] or {}
        return {"sbp": derived.get("sbp"), "dbp": derived.get("dbp"), "category": candidate["category"], "mental_status": candidate["mental_status"],
                "F": candidate["F"], "collapse_burden": candidate["collapse_burden"], "collapse_state": candidate["collapse_state"],
                "relative_delivery": candidate["relative_delivery"], "relative_perfusion": candidate["relative_perfusion"],
                "pulse_present": candidate["pulse_present"]}

    def _evaluate(self, record: dict, minute: int, before: Mapping | None, after: Mapping, legacy_observable: Mapping, session, ran, candidate,
                  route: str) -> None:
        failed, detail = [], {}

        def check(name: str, ok: bool, why: Any = None) -> bool:
            if not ok:
                failed.append(name)
                if why is not None:
                    detail[name] = why
            return bool(ok)

        # 0. the turn itself: it came through a route that has a transaction site, and no turn passed unseen since the last one
        check("turn_has_a_transaction_site", route == ORDER_TURN, {"route": route})
        started = _as_int(before.get("sim_time")) if isinstance(before, Mapping) else None
        check("turn_was_observed", started is not None and started == self._last_seen,
              {"turn_started_at": started, "last_minute_this_transaction_saw": self._last_seen})
        turn_minutes = sorted(set(range(self._last_seen + 1, minute + 1)) | {minute})
        # 1. lineage: READ now, from the layer and from the core's bytes; an offered lineage can only add a refusal
        self.lineage = binding.live_lineage()
        check("lineage_certified", bool(ev.core_lineage_ok()) and binding.lineage_is_v1(self.lineage)
              and (self.offered_lineage is None or binding.lineage_is_v1(self.offered_lineage)),
              {"live": self.lineage.get("version_id"), "bound": self.bound.core_version})
        # 2. snapshot: the run carries the PINNED version 1, and it left from the same arrival as the session's own run
        session_runner = getattr(session, "runner", None)
        check("snapshot_bound", self.runner is not None and binding.runner_is_bound(self.runner, self.bound)
              and self.pressure_snapshot is not None and binding.pressure_point_matches(self.bound.profile)
              and self._anchors is not None and _anchors_digest(self.runner) == self._anchors
              and session_runner is not None and _anchors_digest(session_runner) == self._anchors)
        # 3. case
        check("case_eligible", self.case_id in authority.AUTHORITY_CASES)
        # 4. action: the turn's own classes first, with the shadow's declared gaps through the same filter (the site's rule)
        kinds = authority.action_kinds(ran) if ran is not None else ()
        gap_kinds = tuple(str(gap.get("kind")) for gap in getattr(session, "gaps", []) if gap.get("kind"))
        unsupported = tuple(sorted(set(authority.unsupported_among(kinds)) | set(authority.unsupported_among(gap_kinds))))
        record["action_kinds"] = list(kinds)
        check("supported_management", ran is not None and not unsupported,
              "the caller did not declare which actions ran" if ran is None else {"unsupported": list(unsupported)})
        # 5. one minute, one transaction
        check("minute_not_already_committed", minute not in self.would_commit)
        # 6. pressure: the EXISTING transaction, captured, computed and validated -- never committed
        shadow_minute = next((item for item in reversed(list(getattr(session, "minutes", []) or [])) if _as_int(item.minute) == minute), None)
        pressure = None if shadow_minute is None else authority.pressure_point(shadow_minute.derived)
        present = (shadow_minute is not None and shadow_minute.compared_against_legacy and pressure is not None
                   and all(value is not None for value in pressure.values()))
        written = None
        if check("pressure_candidate_present", present):
            replay_input = authority.AuthoritySite._artifact_input(session)
            replayed = authority.AuthoritySite._replayed_point(replay_input, minute)
            written = authority.shaped_like_legacy(pressure, legacy_observable)
            transaction = authority.AuthorityTransaction(minute=minute, case_id=self.case_id, snapshot=self.pressure_snapshot)
            transaction.capture(after).compute(written, authority.pressure_point(legacy_observable))
            # Every failure the session recorded since the last turn this transaction read, whatever its minute (the site reads the last one)
            failures = list(getattr(session, "failures", []) or [])[self._failures_seen:]
            valid = transaction.validate(invariants_hold=not failures, replay_digest=authority.digest_of(replayed) if replayed is not None else "",
                                         expected_digest=authority.digest_of(pressure), unsupported=unsupported if ran is not None else None,
                                         legacy_arrest=legacy_observable.get("pulse_present") is False, failures=failures)
            check("pressure_validated", valid and transaction.state == authority.VALIDATED and not transaction.committed,
                  {"validation_failures": list(transaction.failures)})
        else:
            failed.append("pressure_validated")
        # 7. consciousness: the bound run has this minute, the artifact reproduces it, and its category is the reading the core reports
        has = (candidate is not None and candidate["derived"] is not None and candidate["category"] in WORD_OF
               and candidate["consciousness_level"] == candidate["category"] and candidate["pulse_present"] is True)
        check("consciousness_candidate_present", has)
        check("consciousness_reproducible", candidate is not None and candidate["reproduced"])
        # 8. the pair is ONE course: at EVERY minute of the turn, every reading that does not depend on the ten magnitudes is equal in the two runs
        mine = {_as_int(item.minute): dict(item.derived) for item in (self.runner.results if self.runner is not None else [])}
        theirs = {_as_int(item.minute): dict(item.derived) for item in list(getattr(session, "minutes", []) or [])}
        apart = [index for index in turn_minutes
                 if index not in mine or index not in theirs or any(mine[index].get(name) != theirs[index].get(name) for name in SHARED_READINGS)]
        check("pair_is_one_course", has and shadow_minute is not None and not apart and candidate["state_digest"] is not None,
              {"minutes_apart_or_missing": apart[:8]})
        # 9. FD-AUTH-06 / FD-AUTH-07: the boundary and the window, BEFORE any commit
        boundary = self._boundary(minute)
        check("collapse_boundary_not_reached", boundary["clear"], boundary)
        check("window_open", minute <= self.time_limit, {"time_limit": self.time_limit})
        check("common_run_did_not_fail", self.runner is not None and not self.runner.failures,
              [f"{item.minute}:{item.where}:{item.exception}" for item in (self.runner.failures if self.runner is not None else [])])
        # 10. what a commit WOULD write, built on a copy and thrown away
        values = None
        if written is not None and has:
            # EVERYTHING the pressure half carries is applied, not a chosen four: a candidate that brought another field would move it here
            values = {**dict(written), "map": authority.derived_map(written.get("sbp"), written.get("dbp")),
                      CONSCIOUSNESS_FIELD: candidate["mental_status"]}
            prepared = deepcopy(dict(after))
            observable = dict(prepared.get("observable") or {})
            observable.update(values)
            prepared["observable"] = observable
            moved = authority.AuthoritySite._moved(after, prepared)
            record["would_move"] = sorted(moved)
            check("only_the_pair_would_move", set(values) == set(PAIR_DOMAIN) and moved <= set(PAIR_DOMAIN)
                  and all(value is not None for value in values.values()), {"moved": sorted(moved), "would_write_fields": sorted(values)})
        else:
            failed.append("only_the_pair_would_move")
        record["failed_checks"], record["detail"] = [name for name in CHECKS if name in failed], detail
        if not failed:
            record.update(verdict=WOULD_COMMIT, reason="every check passed", would_write=values)
            self.would_commit.append(minute)
            self.phase = ACTIVE
            self._cleared_through = minute
            return
        self._refuse(record, minute, failed, detail, "validation")

    # -- after the order pipeline settled the turn (the site's P3-48 rule) ------------------------------------------------------------
    def settle(self, orders: Sequence | None) -> None:
        """An order the engine does not MODEL produces no action for the turn, so the minute above never saw it; the settled ledger is the only
        place its class appears. The same ``unsupported_among`` is applied to EVERY settled row (a row without a class is ``untyped_action``), and
        a ledger that is not a list of rows is unreadable: both refuse. A minute that would already have committed is NOT rewritten: the
        experiment halts after it, as ``AuthoritySite.settle_provenance`` halts."""
        if not self.records:
            return
        record = self.records[-1]
        try:
            readable = isinstance(orders, (list, tuple)) and all(isinstance(item, Mapping) for item in orders)
            # A row with no class is ``untyped_action`` (the site's own reading of it), never a row to skip
            classes = tuple(str(item.get("class") or "") for item in authority.settled_provenance(orders, None)) if readable else ("<unreadable>",)
        except Exception:                               # a ledger that cannot be read is not a supported turn: fail closed
            classes = ("<unreadable>",)
        unsupported = authority.unsupported_among(classes)
        record["settled_classes"] = sorted(set(classes) - {""})
        if unsupported and self.halt is None:
            began = bool(self.would_commit)
            record["settlement_refusal"] = list(unsupported)
            self.halt = {"minute": record["minute"], "failed_checks": ["settled_classes_supported"], "authority_had_begun": began,
                         "stage": "settlement", "detail": {"unsupported": list(unsupported)},
                         "consequence": ("the experiment hard-stops; the minute that would already have committed is not rewritten and the encounter is "
                                         "INVALID_FOR_CONTINUATION" if began else "authority never began; the legacy engine simply continues")}
            self.phase = HALTED
        record["digest"] = authority.digest_of({key: value for key, value in record.items() if key != "digest"})

    # -- the record of the encounter ---------------------------------------------------------------------------------------------------
    def summary(self) -> dict:
        commits = list(self.would_commit)
        return {"case": self.case_id, "snapshot": self.bound.summary(), "snapshot_is_the_pinned_version_1": binding.bound_is_v1(self.bound),
                "time_limit": self.time_limit, "minutes_evaluated": len(self.records), "violations": list(self.violations),
                "would_commit_minutes": len(commits), "first_would_commit": commits[0] if commits else None,
                "last_would_commit": commits[-1] if commits else None,
                "first_would_abort": None if self.halt is None else self.halt["minute"],
                "abort_checks": None if self.halt is None else self.halt["failed_checks"],
                "abort_stage": None if self.halt is None else self.halt.get("stage"),
                "authority_had_begun_at_abort": None if self.halt is None else self.halt["authority_had_begun"],
                "consequence": None if self.halt is None else self.halt["consequence"],
                "halted_minutes": sum(1 for item in self.records if item["verdict"] == HALTED),
                "record_digest": authority.digest_of([item["digest"] for item in self.records])}


# -- running it beside a real, legacy-authoritative encounter (P3-207) -------------------------------------------------------------------------

@contextmanager
def observing(registry: dict):
    """Call the dry transaction where an authority site's minute would be called: right after the shadow observed the turn. The patch is the
    existing development harness's own technique (``test_runtime_authority_series``); unlike it, NOTHING is written back to the state."""
    real, real_time, real_order = rs.ShadowSession.observe, rs.ShadowSession.observe_time, acceptance.Encounter.order
    if any(getattr(item, "_pair_dry_run_patch", False) for item in (real, real_time, real_order)):
        raise RuntimeError("the dry run is already observing: a second, nested observer would evaluate every turn twice")

    def observe(self, before, state, parsed=None, result=None, ran=None, submission_id=None):
        real(self, before, state, parsed, result, ran, submission_id)
        dry = registry.get(id(self))
        if dry is not None:
            dry.minute(before, state, self, ran, submission_id)

    def observe_time(self, before, after, result=None):
        # Clinical time OUTSIDE an order turn (a question, an examination): the layer has no authority site on this route
        real_time(self, before, after, result)
        dry = registry.get(id(self))
        if dry is not None:
            dry.minute(before, after, self, (), None, route=TIME_OUTSIDE_AN_ORDER)

    def order(self, text):
        entry = real_order(self, text)
        dry = registry.get(id(getattr(self, "shadow", None)))
        if dry is not None:
            try:
                dry.settle(entry.get("orders") if isinstance(entry, Mapping) else None)
            except Exception as error:                 # the settlement is part of the transaction: it may refuse, never raise into the turn
                dry.violations.append(f"settlement raised: {type(error).__name__}: {error}")
        return entry
    for patch in (observe, observe_time, order):
        patch._pair_dry_run_patch = True
    rs.ShadowSession.observe, rs.ShadowSession.observe_time, acceptance.Encounter.order = observe, observe_time, order
    try:
        yield
    finally:
        rs.ShadowSession.observe, rs.ShadowSession.observe_time, acceptance.Encounter.order = real, real_time, real_order


SALINE, BLOOD, BLOOD_MORE, ACCESS = series.SALINE, series.BLOOD, series.BLOOD_MORE, series.ACCESS
#: The management series. Supported classes only (fluid, blood, reassessment), except the last, which exists to show what an unsupported class does.
#: ``trigger`` is read on the BOUND snapshot's own category (never on a witness name).
SCENARIOS = {
    "untreated": {"at": {}, "horizon": 240},
    "early_treatment": {"at": {10: (SALINE, BLOOD)}, "horizon": 120},
    "delayed_treatment": {"at": {120: (SALINE, BLOOD)}, "horizon": 200},
    "fluid_focused": {"at": {10: (SALINE,), 40: (SALINE,)}, "horizon": 120},
    "blood_focused": {"at": {10: (BLOOD,)}, "horizon": 120},
    "severe_deterioration": {"at": {}, "horizon": 240, "trigger": (2, (SALINE,))},
    "recovery_after_severe": {"at": {}, "horizon": 240, "trigger": (3, (SALINE, BLOOD_MORE)), "after": 45},
    "late_rescue": {"at": {215: (SALINE, BLOOD_MORE)}, "horizon": 300},
    # Two extras. The first: the same recovery with a bundle whose infusion ends INSIDE the window (the four-unit transfusion above takes 120
    # minutes of the engine's clock in ONE turn, so its turn ends past the time limit). The second: what an unsupported class does.
    "recovery_within_window": {"at": {}, "horizon": 240, "trigger": (3, (SALINE, BLOOD))},
    "unsupported_access": {"at": {10: (ACCESS, SALINE, BLOOD)}, "horizon": 80},
}
EXTRA_SCENARIOS = ("recovery_within_window", "unsupported_access")
REQUIRED_SCENARIOS = tuple(name for name in SCENARIOS if name not in EXTRA_SCENARIOS)
CASES = tuple(authority.AUTHORITY_CASES)


def run(case: str, scenario: str, *, bound: binding.BoundSnapshot | None = None, time_limit: int = TIME_LIMIT_MIN, tamper=None) -> dict:
    """One legacy-authoritative encounter with the dry transaction beside it. ``tamper(dry, encounter)`` is called once, after the dry run
    opens, by a test that attacks it; a normal run passes none."""
    plan = SCENARIOS[scenario]
    bound = binding.bind() if bound is None else bound
    registry, orders, legacy_track = {}, [], []
    with ev.shadow(rs.MODE_SHADOW_COMPARE), observing(registry):
        encounter = acceptance.Encounter(case)
        session = encounter.shadow
        dry = PairDryRun(bound, case, encounter.state, time_limit=time_limit)
        registry[id(session)] = dry
        if tamper is not None:
            tamper(dry, encounter)
        fired, triggered, stop_after = set(), None, None
        while int(encounter.minute) < plan["horizon"]:
            due = []
            for minute in sorted(plan["at"]):
                if minute <= int(encounter.minute) and minute not in fired:
                    fired.add(minute)
                    due.extend(plan["at"][minute])
            trigger = plan.get("trigger")
            if triggered is None and trigger is not None and dry.records:
                shown = dry.records[-1]["common"]
                if shown is not None and shown["category"] is not None and shown["category"] >= trigger[0]:
                    triggered, due = int(encounter.minute), list(trigger[1])
                    stop_after = triggered + plan["after"] if plan.get("after") else None
            if due:
                started, text = int(encounter.minute), " ".join(due)
                entry = encounter.order(text)
                orders.append({"minute": started, "text": text, "executed": bool(entry["executed"]), "clock_after": int(encounter.minute)})
            if encounter.arrested or (stop_after is not None and int(encounter.minute) >= stop_after):
                break
            before = int(encounter.minute)
            encounter.wait_until(before + 1, step=1)
            if int(encounter.minute) == before:
                break
        legacy_track = [dict(item["legacy"] or {}, minute=item["minute"]) for item in dry.records]
        final_observable = dict(encounter.state.get("observable") or {})
    if dry.violations:
        raise DryRunViolation("; ".join(dry.violations))      # after the encounter ended: never from inside a legacy turn
    return {"case": case, "scenario": scenario, "orders": orders, "triggered_at": triggered, "minutes_played": int(encounter.minute),
            "legacy_arrested": bool(encounter.arrested), "summary": dry.summary(), "records": dry.records, "halt": dry.halt,
            "legacy_track": legacy_track, "final_legacy_observable": {key: final_observable.get(key) for key in ("sbp", "dbp", "mental_status", "pulse_present")},
            "bound_run_failures": [f"{item.minute}:{item.where}:{item.exception}" for item in (dry.runner.failures if dry.runner else [])],
            "session_failures": len(session.failures), "dry": dry, "encounter": encounter}


def legacy_alone(case: str, scenario: str, script: Sequence[Mapping]) -> list:
    """The same orders at the same minutes with the shadow OFF and no dry run: the legacy trajectory nobody observed."""
    track = []
    with ev.shadow(rs.MODE_OFF):
        encounter = acceptance.Encounter(case)
        pending = {int(item["minute"]): item["text"] for item in script}
        horizon = SCENARIOS[scenario]["horizon"]
        end = None
        while int(encounter.minute) < horizon:
            if int(encounter.minute) in pending:
                encounter.order(pending.pop(int(encounter.minute)))
                track.append(dict(legacy_point(encounter.state.get("observable") or {}), minute=int(encounter.minute)))
            if encounter.arrested or (end is not None and int(encounter.minute) >= end):
                break
            before = int(encounter.minute)
            encounter.wait_until(before + 1, step=1)
            if int(encounter.minute) == before:
                break
            track.append(dict(legacy_point(encounter.state.get("observable") or {}), minute=int(encounter.minute)))
    return track


VERDICT_CODE = {WOULD_COMMIT: "W", WOULD_ABORT: "A", HALTED: "H"}


def compact(result: Mapping) -> dict:
    """A run for the record: per minute the legacy state, the common candidate, the verdict and the reason (digests keep it reproducible)."""
    rows = []
    for item in result["records"]:
        common = item["common"] or {}
        legacy = item["legacy"] or {}
        rows.append([item["minute"], VERDICT_CODE[item["verdict"]],
                     legacy.get("sbp"), legacy.get("dbp"), legacy.get("mental_status"),
                     None if item["would_write"] is None else item["would_write"]["sbp"],
                     None if item["would_write"] is None else item["would_write"]["dbp"],
                     common.get("mental_status"), None if common.get("F") is None else round(common["F"], 4),
                     None if common.get("collapse_burden") is None else round(common["collapse_burden"], 4), common.get("collapse_state"),
                     ",".join(item["failed_checks"])])
    return {"case": result["case"], "scenario": result["scenario"], "orders": result["orders"], "triggered_at": result["triggered_at"],
            "minutes_played": result["minutes_played"], "summary": result["summary"], "halt": result["halt"],
            "columns": ["minute", "verdict(W=WOULD_COMMIT,A=WOULD_ABORT,H=HALTED)", "legacy_sbp", "legacy_dbp", "legacy_mental_status",
                        "would_write_sbp", "would_write_dbp", "common_mental_status", "F", "collapse_burden", "collapse_state", "failed_checks"],
            "rows": rows, "bound_run_failures": result["bound_run_failures"], "legacy_arrested": result["legacy_arrested"]}
