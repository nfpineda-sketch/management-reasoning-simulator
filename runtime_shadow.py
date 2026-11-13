"""Phase 3, P3-1: the live encounter may run the closed Phase-2 common core beside the legacy engine.

Observation only. The legacy engine is the only runtime authority: ``COMMON_CORE_RUNTIME_AUTHORITY = False``.
Nothing here can control a vital sign, a mental status, an arrest, an order's fate, the score, an
interruption, the authoritative persistence or the resident's trace. The core reads deep copies, computes on
its own state and returns a separate result object; a failure inside it is recorded and the encounter goes on
untouched.

Why it lives outside ``clinical_core/``: the formal Phase-2 closure digest covers every source in that
package (``docs/PHASE2_CLOSURE.md``), so a Phase-3 module placed there would move it. Phase 2 is immutable.

How a minute is aligned. The legacy engine advances its own minutes inside ``execute_family_bundle``; this
module does not hook into that loop and never re-drives the engine (that would duplicate treatment). It
mirrors what the engine already decided -- the executed actions with the start minutes its own receipts
report -- and advances the core to the same ``sim_time``. Legacy minute N and shadow minute N are the same
causal interval, counted from arrival; the comparison happens where a legacy truth exists, at each turn
boundary, while the shadow keeps every minute in between.

The mapping is not invented here: the anchors, the haemorrhage module and the interventions come from
``clinical_core.legacy_adapter``, the mapping Phase 2 certified and pinned with a golden, and the comparison
uses ``clinical_core.comparison``'s own variable table and display projection. No clinical parameter is
approved, selected or turned on: the run uses the committed default profile, so a disabled mechanism stays
disabled and shows up as ``PARAMETER_DISABLED_DIVERGENCE`` rather than as physiology.

The flag is an environment variable, off unless set, so that OFF is exactly the frozen engine: no key is
added to the patient state, nothing is initialized, nothing is logged. The pilot's preflight CANNOT list it:
``pilot_freeze.py`` is inside the Phase-2 calibration freeze (``clinical_core.calibration``'s input paths),
so adding the row would move a frozen digest of a closed stage. That path is stopped and declared --
``PILOT_PREFLIGHT_FLAG_GATE_DEFERRED`` (TD-130) -- and the pilot's protection today is that no pilot surface
names the flag and that a clean environment opens no session, both fixed by a test.

Since P3-11 there is ONE execution primitive: this session captures the authoritative inputs and the
immutable mirrored events and hands them to ``runtime_shadow_families.ShadowPhysiologyRunner``, the same
runner the offline replay uses. Live and replay are therefore equal by construction, not by coincidence.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

#: The common core never holds runtime authority in Phase 3.
COMMON_CORE_RUNTIME_AUTHORITY = False

MODE_OFF = "off"
MODE_SHADOW_COMPARE = "shadow_compare"
MODES = (MODE_OFF, MODE_SHADOW_COMPARE)
#: Environment flag. Absent, empty or unknown means OFF.
FLAG = "MRS_PHASE3_SHADOW"
#: Optional comma-separated allowlist of engine families; the default is the one family P3-1 enables.
FAMILIES_FLAG = "MRS_PHASE3_SHADOW_FAMILIES"
#: The families whose live encounter may be SHADOWED. This tuple is read by ``enabled_for`` and by nothing
#: else: it opens a non-authoritative shadow session and grants nothing. Authority has its own gate
#: (``runtime_authority``), which names one family and stays shut.
#:
#: - ``gi_bleed`` since P3-1: the family with a certified runtime mapping and a committed golden.
#: - ``opioid`` since P3-141 (faculty authorization of 2026-11-10, FD-P3-131): the second family, and the
#:   first whose mechanism is not volume. Its arrival is the certified authored case, checked against the
#:   live state before anything runs; its transmission parameter runs as a region ensemble, never a point.
#: - P3-122 audited ACS for this list and REFUSED it, and the refusal stands: its treatment semantics are
#:   ready, its arrival mapping is not (see ``runtime_shadow_families.ACS_LIVE_GAP``).
LIVE_FAMILIES = ("gi_bleed", "opioid")
#: The parameter snapshot P3-1 uses: the committed Phase-2 default profile, with nothing turned on.
PARAMETER_SNAPSHOT_ID = "phase2_committed_default_profile"

#: Divergence classes (P3-1-12). Structural, never a numeric threshold.
EXPECTED = "EXPECTED_ARCHITECTURAL_DIVERGENCE"
PARAMETER_DISABLED = "PARAMETER_DISABLED_DIVERGENCE"
MAPPING_GAP = "MAPPING_GAP"
BOUNDARY = "COMMON_BOUNDARY"
UNEXPECTED = "UNEXPECTED_STRUCTURAL_DIVERGENCE"
#: The golden declares this difference in some of its scenarios and not in others, so it is architectural
#: there and a question here: reported with the count, never silenced and never alarming.
PARTIALLY_EXPLAINED = "PARTIALLY_EXPLAINED_DIVERGENCE"
SAFETY_CRITICAL = "SAFETY_CRITICAL_DIVERGENCE"
NOT_COMPARABLE = "NOT_COMPARABLE"

#: A difference the committed golden already records, with the declared Phase-2 difference that explains it,
#: is the two architectures differing -- not plumbing. Anything else on a variable the golden shows matching
#: is a plumbing fault and must be loud. This is why no numeric threshold is needed anywhere here.
_GOLDEN = {}
_GOLDEN_PARTIAL = {}
_SAFETY_VARIABLES = frozenset({"pulse_present", "rhythm"})
#: Profile fields that must be non-zero for a variable's common mechanism to move at all.
_DRIVERS = {
    "hr": ("hr_per_sympathetic_drive",),
    "spo2": ("oxygen_levels",),
    "crt_s": ("crt_per_output_deficit_s",),
    "lactate_mmol_l": ("debt_to_lactate_gain",),
    "D": ("debt_per_delivery_deficit",),
}


def mode(environ: Mapping[str, str] | None = None) -> str:
    """The shadow mode this process runs in. Unset, empty or unknown is OFF.

    A deployment's Secret cannot turn it on. Streamlit copies every scalar root key of ``secrets.toml``
    into ``os.environ`` (``conftest.py`` says so, and a test of this repository defends it), so reading the
    environment alone would let a Secret of this name enable the shadow silently -- exactly what the pilot
    preflight was meant to catch and cannot, because ``pilot_freeze.py`` is inside the Phase-2 calibration
    freeze. The flag is only honoured when it comes from the process environment and NOT from the secrets
    file; the check runs only when the flag is set, so the off path stays free.
    """
    value = str((environ if environ is not None else os.environ).get(FLAG, "") or "").strip().lower()
    if value != MODE_SHADOW_COMPARE:
        return MODE_OFF
    return MODE_OFF if _named_in_secrets(FLAG) else MODE_SHADOW_COMPARE


def _named_in_secrets(name: str) -> bool:
    """Whether a deployment's secrets file carries this key. Any failure reads as 'not in secrets'."""
    try:
        import streamlit
        return name in streamlit.secrets
    except Exception:
        return False


def live_families(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    raw = str((environ if environ is not None else os.environ).get(FAMILIES_FLAG, "") or "").strip()
    if not raw:
        return LIVE_FAMILIES
    asked = tuple(part.strip() for part in raw.split(",") if part.strip())
    return tuple(name for name in asked if name in LIVE_FAMILIES)


def enabled_for(family: str | None, environ: Mapping[str, str] | None = None) -> bool:
    """Whether live shadow comparison runs for this engine family. OFF, or another family, is False."""
    return mode(environ) == MODE_SHADOW_COMPARE and str(family or "") in live_families(environ)


#: P3-147, ARRIVAL_ELIGIBLE: the one shared invariant that decides whether a runtime state may be MAPPED AS AN
#: ARRIVAL, for every live-shadow family. A clock at zero is not enough: a turn that takes no time leaves
#: the clock at zero and a treated patient behind it. Each condition is a comparison; none derives a value.
ARRIVAL_CONDITIONS = (
    "clock_at_arrival",                  # no positive time: the encounter's clock and the engine's own are at 0
    "engine_state_is_a_fresh_arrival",   # field by field what a fresh initialization of this same case gives
    "monitor_is_the_authored_arrival",   # the monitor shows the authored arrival and nothing the engine adds
    "nothing_administered",              # no medication on record, no treatment timeline
    "nothing_on_the_diagnostic_record",  # no study requested, none resulted
)
ARRIVAL_REJECTED = "ArrivalNotEligible"
#: P3-158: what happens to an order the resident asked to hold until a result is back. The engine holds it
#: (``family_state.deferred_orders``) and runs it itself when the result arrives; only then does the shadow
#: mirror it, once, dated at the minute the engine REALLY executed it and never at the minute it was placed.
ORDER_PLACED = "ORDER_PLACED"
ORDER_HELD = "ORDER_HELD"
ORDER_RELEASED = "ORDER_RELEASED"
ORDER_EXECUTED = "ORDER_EXECUTED"
ORDER_CANCELLED = "ORDER_CANCELLED"
ORDER_TERMINAL_NOT_EXECUTABLE = "ORDER_TERMINAL_NOT_EXECUTABLE"
HELD_ORDER_EVENTS = (ORDER_PLACED, ORDER_HELD, ORDER_RELEASED, ORDER_EXECUTED, ORDER_CANCELLED,
                     ORDER_TERMINAL_NOT_EXECUTABLE)
ANY_PENDING = "any_pending"
#: A held order that left the engine's list with no receipt in an observed turn. The engine cancels nothing,
#: so it ran -- during an information activity, whose clinical time no shadow turn observes.
UNOBSERVED_RELEASE = ("the engine ran this held order in an interval the shadow did not observe: no receipt "
                      "reached the shadow, so it is not mirrored")
#: P3-148: the name a trace the store refused or could not write is recorded under.
PERSISTENCE_FAILED = "TraceNotPersisted"


def arrival_eligibility(state: Mapping) -> dict:
    """ARRIVAL_ELIGIBLE for this runtime state: ``{"eligible", "conditions", "differences"}``. Never raises.

    The state is eligible only while ALL of ``ARRIVAL_CONDITIONS`` hold: it is the authored arrival of its
    own case, shown as authored, and nothing has been done to the patient -- no time, no executed order, no
    treatment state. Everything is read on copies, through the engine's own initializer; a state that
    cannot be evaluated is not eligible, with the reason. The family's own certified identity requirements
    (``RuntimeFamilyAdapter.arrival_identity``) are checked on top of this, when the run opens.
    """
    conditions = {name: False for name in ARRIVAL_CONDITIONS}
    differences: list = []
    try:
        from clinical_core import legacy_adapter
        engine = legacy_adapter._engine()
        source = legacy_adapter._initialized(state)
        fresh = deepcopy(dict(state))
        fresh.pop("family_state", None)
        engine._initialize(fresh)
        live_state, fresh_state = source.get("family_state") or {}, fresh.get("family_state") or {}
        clock = source.get("sim_time", 0) or 0
        elapsed = live_state.get("elapsed", 0) or 0
        # the clock itself, not its whole minutes: any positive advancement has left the arrival
        conditions["clock_at_arrival"] = float(clock) == 0.0 and float(elapsed) == 0.0
        if float(clock) != 0.0:
            differences.append(("sim_time", clock, 0))
        moved = [key for key in sorted(set(live_state) | set(fresh_state))
                 if live_state.get(key) != fresh_state.get(key)]
        conditions["engine_state_is_a_fresh_arrival"] = not moved
        differences.extend((f"family_state.{key}", live_state.get(key), fresh_state.get(key)) for key in moved)
        authored = (engine._case(source) or {}).get("observable") or {}
        shown = source.get("observable") or {}
        off = [key for key in sorted(set(shown) | set(authored)) if shown.get(key) != authored.get(key)]
        # a case with no authored arrival to compare with is not "the authored arrival": fail closed
        conditions["monitor_is_the_authored_arrival"] = bool(authored) and not off
        if not authored:
            differences.append(("case.observable", None, "the authored arrival"))
        differences.extend((f"observable.{key}", shown.get(key), authored.get(key)) for key in off)
        treatments = source.get("treatments") or {}
        given = treatments.get("administered_medications") or []
        ordered = treatments.get("order_history") or []
        disposition = treatments.get("disposition")
        timeline = source.get("treatment_timeline") or {}
        conditions["nothing_administered"] = not given and not timeline and not ordered and not disposition
        if given:
            differences.append(("treatments.administered_medications", len(given), 0))
        if ordered:
            differences.append(("treatments.order_history", len(ordered), 0))
        if disposition:
            differences.append(("treatments.disposition", disposition, None))
        if timeline:
            differences.append(("treatment_timeline", len(timeline), 0))
        studies, history = source.get("diagnostics") or {}, source.get("diagnostic_history") or []
        conditions["nothing_on_the_diagnostic_record"] = not studies and not history
        if studies:
            differences.append(("diagnostics", len(studies), 0))
        if history:
            differences.append(("diagnostic_history", len(history), 0))
    except Exception as error:
        differences.append(("could_not_be_evaluated", f"{type(error).__name__}: {str(error)[:160]}", None))
        return {"eligible": False, "conditions": conditions, "differences": differences}
    return {"eligible": all(conditions.values()), "conditions": conditions, "differences": differences}


def held_execution_minute(entry: Mapping, before: Mapping, after: Mapping, turn: int) -> int | None:
    """The minute the engine ran a held order during the turn from ``before`` to ``after``. None when the
    engine's own record does not establish it.

    The engine releases a held order at the first of its own checks at which the result it waits for is
    back. It checks (a) inside the turn, at every minute a result left pending by an EARLIER turn comes
    back, and (b) once at the end of the turn. So the minute is read from what the engine itself recorded:
    when each pending result was due, and when the awaited result came back. An order placed in this same
    turn (``turn`` is the session's turn number) only meets check (b). Nothing here is fitted, and ``test_shadow_resolution.py`` holds this reading
    against the engine's own timestamp of the released order and against every way of chunking the wait.
    """
    try:
        started, ended = int(before.get("sim_time", 0) or 0), int(after.get("sim_time", 0) or 0)
        study = str(entry["after_result"])
        pending = [(int(item.get("due_min", 0)), str((item.get("summary") or {}).get("diagnostic_type")))
                   for item in (before.get("family_state") or {}).get("pending_diagnostics") or []]
        had = set(before.get("diagnostics") or {})
        came_back = {}
        for name, found in (after.get("diagnostics") or {}).items():
            if name not in had and isinstance(found, Mapping) and found.get("time_min") is not None:
                came_back[str(name)] = int(found["time_min"])

        # The same study can be pending more than once, and the engine keeps only the time of the LAST one
        # that came back: the study is available from the FIRST arrival, which is the earliest pending one.
        arrivals = [due for due, name in pending if name == study and due <= ended]
        if study in came_back:
            arrivals.append(came_back[study])

        def ready(minute: int) -> bool:
            if study == ANY_PENDING:
                return not any(due > minute for due, _name in pending)
            return study in had or any(arrival <= minute for arrival in arrivals)

        if int(entry["placed_turn"]) < int(turn):          # held since an earlier turn: check (a) applies
            for minute in sorted({due for due, _name in pending if started < due <= ended}):
                if ready(minute):
                    return minute
        if study == ANY_PENDING:
            still = (after.get("family_state") or {}).get("pending_diagnostics") or []
            return ended if not still else None
        return ended if study in set(after.get("diagnostics") or {}) else None
    except Exception:
        return None


def arrival_untouched(state: Mapping) -> bool:
    """Whether the state still is the untouched authored arrival. False when it cannot be told."""
    return bool(arrival_eligibility(state)["eligible"])


def _differences_text(differences: Sequence, limit: int = 8) -> str:
    shown = "; ".join(f"{name} live {live!r} / arrival {expected!r}" for name, live, expected in differences[:limit])
    return shown + (f"; and {len(differences) - limit} more" if len(differences) > limit else "")


@dataclass(frozen=True)
class MirroredAction:
    """One action the legacy engine already executed, copied immutably for the shadow run."""

    order_id: str
    minute: int
    kind: str
    action: Mapping[str, Any]
    receipt: Mapping[str, Any]
    fio2_after: float
    #: The ledger's own identity, so a shadow artifact can be joined to the authoritative record.
    ledger_order_id: str | None = None
    submission_id: str | None = None


@dataclass(frozen=True)
class ShadowMinute:
    """One shadow minute as a reader sees it: the runner's digest, its derived values and its divergences."""

    minute: int
    state_digest: str
    derived: Mapping[str, Any]
    compared_against_legacy: bool
    #: ``runtime_shadow_families.ShadowDivergenceRecord``, which carries the domain as well.
    divergences: tuple = ()


@dataclass(frozen=True)
class ShadowFailure:
    """A shadow-side failure, recorded and classified; the encounter never sees it."""

    minute: int
    where: str
    exception: str
    message: str
    classification: str


@dataclass
class ShadowSession:
    """The shadow run of one encounter. Held by the caller, never inside the patient state."""

    case_id: str
    family: str
    mode: str = MODE_SHADOW_COMPARE
    arrival: Mapping[str, Any] | None = None
    #: The ONE execution primitive, shared with the offline replay (P3-11).
    runner: Any = None
    scenario_id: str | None = None
    #: The identity of the encounter this session opened on: the digest of its arrival. Recorded in the
    #: artifact so two attempts at the same case can be told apart after the fact.
    encounter_id: str = ""
    #: P3-159: the encounter's own generation -- a digest of the attempt record the page started it from, when
    #: there is one. None for an encounter that was not started from an attempt record: nothing is invented.
    generation: str | None = None
    mirrored: list = field(default_factory=list)
    seen: set = field(default_factory=set)
    seen_ledger: set = field(default_factory=set)
    failures: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    endoscopy_at: int | None = None
    #: P3-158: every order the engine was asked to hold, with what became of it (see ``HELD_ORDER_EVENTS``).
    held: list = field(default_factory=list)
    #: A2-006: what the legacy engine's own state said of a terminal event the last time it was observed --
    #: the minute of its arrest and of its fibrillation, or None. Read, never decided here.
    legacy_terminal: Mapping[str, Any] | None = None
    _released_seen: set = field(default_factory=set)
    turns: int = 0
    _runner_failures: int = 0
    #: P3-140: the witnesses of a declared development region, each its own run beside ``runner``. None for
    #: a family that declares no live region (GI), whose session is then exactly what it was.
    ensemble: Any = None
    #: P3-147: what ``arrival_eligibility`` said of the state this session was asked to open on.
    eligibility: Mapping[str, Any] | None = None
    #: P3-147: whether the encounter this session follows has LEFT its arrival (time passed, or anything was
    #: done to the patient). Sticky. Only then is an untouched arrival another encounter.
    left_arrival: bool = False
    #: P3-148: what the shadow research trace store said the last time this session's trace was handed to
    #: it. None while no faculty or development environment names a store, which is the default.
    persistence: Mapping[str, Any] | None = None
    _environ: Any = None
    #: The identity of the last record this session stored: what ties one attempt's records together.
    _last_stored: str | None = None
    #: The kinds of persistence failure already recorded, so each is recorded once and not once per turn.
    _persist_kinds: set = field(default_factory=set)

    # -- construction ------------------------------------------------------------------------------------
    @classmethod
    def start(cls, state: Mapping, *, environ: Mapping[str, str] | None = None,
              scenario_id: str | None = None, generation=None) -> "ShadowSession | None":
        """Open a session for this encounter, or None when the flag is off or the family is not enabled.

        The arrival mapping, the family's writers and the profile all come from the family adapter, which is
        the same object the offline replay opens: one mapping, one snapshot, one execution path.
        """
        try:
            family = str(state.get("engine_family") or "")
        except Exception:
            return None                     # a state that cannot be read opens nothing: legacy-only
        if not enabled_for(family, environ):
            return None
        session = cls(case_id="", family=family, scenario_id=scenario_id, generation=generation_key(generation))
        session._environ = None if environ is None else dict(environ)
        session._open(state, scenario_id)
        if session.failures:
            # P3-148/P3-150: a session that could not open as asked says so where a faculty reader looks,
            # even if no turn ever follows it.
            session._persist()
        return session

    def _open(self, state: Mapping, scenario_id: str | None) -> None:
        session, family = self, self.family
        try:
            import runtime_shadow_families
            from clinical_core import legacy_adapter
            arrival = deepcopy(dict(state))
            session.arrival = arrival
            session.case_id = legacy_adapter.engine_case_id(arrival)
            session.encounter_id = _encounter_id(arrival)
            # P3-147, the shared lifecycle rule (faculty decision of 2026-11-10): a state is mapped as an
            # arrival only while it IS one. Opening on a patient time has passed for, or anything was done
            # to, would label a treated patient's values as the arrival and lose every order given before
            # this point from the mirror. That used to be refused only for a clock past zero, and silently
            # (no session at all). It is now refused for every way of having left the arrival -- a turn
            # that takes no time included -- and the refusal is a session that says why and runs nothing:
            # the encounter is legacy-only, which is the honest reading, and a reader can see it.
            session.eligibility = arrival_eligibility(arrival)
            if not session.eligibility["eligible"]:
                session.left_arrival = True
                try:
                    minute = int(arrival.get("sim_time", 0) or 0)
                except Exception:
                    minute = 0
                session.failures.append(ShadowFailure(
                    minute, "start", ARRIVAL_REJECTED,
                    "this state is not an untouched authored arrival, so it is not mapped as one: "
                    + _differences_text(session.eligibility["differences"]), MAPPING_GAP))
                return
            session.runner = runtime_shadow_families.ShadowPhysiologyRunner.open(
                family, session.case_id, state=arrival, scenario_id=scenario_id)
            if session.runner is None:
                session.failures.append(ShadowFailure(
                    0, "start", "NoCertifiedAdapter",
                    f"no certified shadow adapter for {family}/{session.case_id}", MAPPING_GAP))
            else:
                # P3-141: an arrival the adapter refused is a failure the RECORD must show. Before this, the
                # reason stayed on the runner and the session's record was empty without saying why.
                session.failures.extend(session.runner.failures)
                session._runner_failures = len(session.runner.failures)
                if session.runner.anchors is not None:
                    session.ensemble = runtime_shadow_families.RegionEnsemble.open(
                        family, session.case_id, state=arrival, scenario_id=scenario_id)
                    if session.ensemble is not None:
                        session.failures.extend(session.ensemble.new_failures())
        except Exception as error:  # the encounter must not care why the shadow could not start
            session.failures.append(_failure(0, "start", error, MAPPING_GAP))
            session.runner = None
            session.ensemble = None

    # -- the one execution path --------------------------------------------------------------------------
    @property
    def anchors(self):
        """The arrival the adapter mapped, or None when it could not be mapped."""
        return None if self.runner is None else self.runner.anchors

    @property
    def minutes(self) -> list:
        """The shadow minutes, read from the runner: the live path keeps no second copy of them."""
        if self.runner is None:
            return []
        by_minute: dict = {}
        for record in self.runner.divergences:
            by_minute.setdefault(record.minute, []).append(record)
        return [ShadowMinute(item.minute, item.state_digest, item.derived,
                             item.minute in self.runner.compared,
                             tuple(by_minute.get(item.minute, ())))
                for item in self.runner.results]

    # -- observation -------------------------------------------------------------------------------------
    def capture(self, state: Mapping) -> Mapping | None:
        """A private copy of the state before the engine runs, or None when it cannot be copied.

        The copy happens here, inside the session's own guard, so that nothing on the authoritative path
        can raise because the shadow wanted a snapshot.
        """
        try:
            return deepcopy(dict(state))
        except Exception as error:
            self.failures.append(_failure(int(state.get("sim_time", 0) or 0), "capture", error, MAPPING_GAP))
            return None

    def observe(self, before: Mapping | None, after: Mapping, parsed: Mapping | None = None,
                result: Mapping | None = None, ran: Sequence | None = None,
                submission_id: str | None = None) -> None:
        """Mirror what the engine actually ran this turn and advance the shadow to the engine's minute.

        ``ran`` is the settled action list -- what the engine received after the order pipeline decided each
        order's fate. Without it nothing is mirrored: the shadow consumes the fate the ledger settled and
        never decides for itself whether an order happened.

        Pure with respect to its arguments: every copy is made inside this guard, and a failure of any kind
        is recorded here instead of reaching the caller.
        """
        self.turns += 1
        try:
            self._observe(before, deepcopy(dict(after)),
                          deepcopy(dict(parsed)) if parsed else None,
                          deepcopy(dict(result)) if result else None,
                          deepcopy(list(ran)) if ran is not None else None, submission_id)
        except Exception as error:
            minute = 0
            try:
                minute = int(after.get("sim_time", 0) or 0)
            except Exception:
                pass
            self.failures.append(_failure(minute, "observe", error, UNEXPECTED))
        if not self.left_arrival:
            # Read once per turn, and only until it turns true: after that an arrival is another encounter.
            self.left_arrival = not arrival_untouched(after)
        self.legacy_terminal = legacy_terminal_of(after)
        self._persist()

    def observe_time(self, before: Mapping | None, after: Mapping, result: Mapping | None = None) -> None:
        """P3-167: clinical time the engine let pass OUTSIDE an order turn (a question, an examination).

        Nothing was ordered, so nothing is mirrored from the activity itself: its content is never read.
        The one thing that can happen to the mirror here is that the engine RAN an order it was holding,
        because the result it waited for came back during the activity. The engine says so in its own
        receipts of that interval, and that is all this reads: each released order is mirrored once, at the
        minute the engine ran it, by the same rule as a release inside an order turn. Then the shadow
        advances to the engine's minute. Never raises; a failure is recorded here.
        """
        self.turns += 1
        try:
            if self.runner is not None and self.runner.anchors is not None:
                seen_after = deepcopy(dict(after))
                receipts = [dict(item) for item in ((result or {}).get("action_summaries") or [])
                            if isinstance(item, Mapping) and item.get("released_after") is not None]
                if receipts and before is None:
                    self._gap({"why": "the state before the activity could not be copied, so the held orders "
                                      "the engine ran in it were not mirrored", "kind": None, "order_id": None})
                elif receipts:
                    fio2 = float((seen_after.get("family_state") or {}).get("oxygen_fio2", 0.21))
                    self._release(receipts, before, seen_after, fio2)
                self._settle_held(seen_after)
                endoscopy = (seen_after.get("family_state") or {}).get("endoscopy_at")
                if endoscopy is not None:
                    self.endoscopy_at = int(endoscopy)
                self._advance(int(seen_after.get("sim_time", 0) or 0), seen_after)
        except Exception as error:
            minute = 0
            try:
                minute = int(after.get("sim_time", 0) or 0)
            except Exception:
                pass
            self.failures.append(_failure(minute, "observe_time", error, UNEXPECTED))
        if not self.left_arrival:
            self.left_arrival = not arrival_untouched(after)
        self.legacy_terminal = legacy_terminal_of(after)
        self._persist()

    def _persist(self) -> None:
        """P3-148: hand the trace as it stands to the shadow research trace store, if one is named.

        Off by default: with no store named by a faculty or development environment this does nothing and
        costs one lookup. It NEVER raises, whatever the store answers or fails with. A trace that could not
        be stored is a recorded failure -- once per kind of reason, not once per turn -- so the next trace
        that IS stored, and the session's own record, say so.
        """
        try:
            import runtime_shadow_store
            outcome = runtime_shadow_store.persist_session(self, environ=self._environ)
            if outcome is None:
                return
            if not isinstance(outcome, Mapping):
                outcome = {"stored": False, "kind": "STORE_ANSWER",
                           "why": f"the store answered {type(outcome).__name__}, not an outcome"}
            outcome = dict(outcome)
            outcome["stored"] = outcome.get("stored") is True     # only an explicit True is "stored"
            self.persistence = outcome
            if outcome["stored"]:
                self._last_stored = str(outcome.get("trace_id") or "") or self._last_stored
                return
            kind = str(outcome.get("kind") or outcome.get("why") or "NOT_STORED")
            message = str(outcome.get("why") or "the trace was not stored")[:400]
        except Exception as error:
            kind = f"PERSIST_ERROR {type(error).__name__}"
            message = f"the trace could not be handed to the store: {type(error).__name__}"
            self.persistence = {"stored": False, "kind": kind, "why": message}
        if kind in self._persist_kinds:
            return
        self._persist_kinds.add(kind)
        minute = 0 if self.runner is None else int(self.runner.minutes_done)
        self.failures.append(ShadowFailure(minute, "persist", PERSISTENCE_FAILED, message, NOT_COMPARABLE))

    def _observe(self, before, after: Mapping, parsed, result, ran, submission_id) -> None:
        if self.runner is None or self.runner.anchors is None:
            return
        self._mirror(before, after, parsed, result, ran, submission_id)
        endoscopy = (after.get("family_state") or {}).get("endoscopy_at")
        if endoscopy is not None:
            self.endoscopy_at = int(endoscopy)
        self._advance(int(after.get("sim_time", 0) or 0), after)

    def _mirror(self, before, after: Mapping, parsed, result, ran, submission_id) -> None:
        """Only the actions the engine ran become shadow events, once, with the ledger's identity.

        The receipt of a delivered order is paired BY POSITION among the actions of its own kind, as the
        certified Phase-2 mapping does (``legacy_adapter._summaries``): the first bag of a turn takes the
        first bag's receipt. A count that does not match fails closed as a declared gap.
        """
        if not result or not result.get("executed"):
            return
        if ran is None:
            self._gap({"why": "the settled action list was not supplied, so nothing was mirrored",
                       "turn": self.turns, "kind": None, "order_id": None})
            return
        if before is None:
            # Without the state from before the turn there is no minute to date these actions at, and
            # dating them at zero would move a treatment to the arrival. Nothing is mirrored, and the gap
            # says why -- the capture failure alone would not tie itself to the actions it lost.
            self._gap({"why": "the state before the turn could not be copied, so nothing was mirrored",
                       "turn": self.turns, "kind": None, "order_id": None})
            return
        minute = int((before or {}).get("sim_time", 0) or 0)
        fio2 = float((after.get("family_state") or {}).get("oxygen_fio2", 0.21))
        receipts: dict = {}
        released = []
        for summary in list(result.get("action_summaries") or []):
            if summary.get("released_after") is not None:
                released.append(summary)     # a held order the engine ran this turn: mirrored below, not paired here
                continue
            receipts.setdefault(str(summary.get("type") or ""), []).append(summary)
        taken: dict = {}
        for index, action in enumerate(list(ran)):
            kind = str(action.get("type") or "")
            # The turn number keeps two turns of the same minute from sharing an id.
            order_id = f"m{minute:03d}-t{self.turns:02d}-{index}-{kind}"
            if order_id in self.seen:
                continue
            if action.get("after_result"):
                self._hold(order_id, minute, kind, action, submission_id)
                continue
            # The ledger's own id is the identity of a real order: the same turn observed twice is
            # mirrored once, whatever minute or turn number the second look falls in. A synthetic action
            # without one falls back to the structural id, which the turn counter keeps unique.
            ledger_id = action.get("_order_id")
            if ledger_id is not None and str(ledger_id) in self.seen_ledger:
                continue
            position = taken.get(kind, 0)
            taken[kind] = position + 1
            of_kind = receipts.get(kind, [])
            if kind in ("fluid", "blood") and position >= len(of_kind):
                self._gap({"order_id": order_id, "kind": kind,
                           "why": f"the engine reported {len(of_kind)} {kind} receipts for "
                                  f"{position + 1} {kind} actions: the delivery cannot be placed"})
                continue
            receipt = of_kind[position] if position < len(of_kind) else {}
            self.seen.add(order_id)
            if ledger_id is not None:
                self.seen_ledger.add(str(ledger_id))
            self.mirrored.append(MirroredAction(order_id, minute, kind, dict(action), dict(receipt), fio2,
                                                action.get("_order_id"), submission_id))
        self._release(released, before, after, fio2)
        self._settle_held(after)

    # -- P3-158: orders held until a result ----------------------------------------------------------------
    def _hold(self, order_id: str, minute: int, kind: str, action: Mapping, submission_id) -> None:
        """Remember an order the engine was asked to hold. Nothing is mirrored: the engine has not run it."""
        ledger_id = action.get("_order_id")
        if any(item["order_id"] == order_id or (ledger_id is not None and item["ledger_order_id"] == ledger_id)
               for item in self.held):
            return                                    # the same turn observed twice holds it once
        self.held.append({
            "order_id": order_id, "ledger_order_id": ledger_id, "submission_id": submission_id, "kind": kind,
            "action": {key: value for key, value in dict(action).items() if key != "after_result"},
            "after_result": str(action.get("after_result")), "placed_minute": int(minute),
            "placed_turn": int(self.turns), "state": ORDER_HELD,
            "executed_minute": None, "shadow_order_id": None, "why": "",
            "events": [[ORDER_PLACED, int(minute)], [ORDER_HELD, int(minute)]]})

    def _release(self, released: Sequence, before: Mapping, after: Mapping, fio2: float) -> None:
        """Mirror every held order the engine ran this turn, once, at the minute it really ran.

        The engine's receipt of a released order names what it waited for and when it was placed, and that
        is how it is matched to the order this session is holding: same kind, same result, same placement
        minute, oldest first. A release that cannot be matched, or whose minute cannot be established from
        the engine's own record, is NOT mirrored and says so -- its effect is never guessed.
        """
        for index, receipt in enumerate(released):
            kind, study = str(receipt.get("type") or ""), str(receipt.get("released_after"))
            # the same receipt of the same turn, looked at again: it was already settled, and adds nothing
            # ...told apart from ANOTHER turn of the same minute by what the engine state was around it: two
            # zero-minute turns that each release an identical order are two releases, not one seen twice
            told = (_state_mark(before), _state_mark(after), index, kind, study, receipt.get("held_from_min"))
            if told in self._released_seen:
                continue
            self._released_seen.add(told)
            entry = next((item for item in self.held if item["state"] == ORDER_HELD and item["kind"] == kind
                          and item["after_result"] == study
                          and item["placed_minute"] == receipt.get("held_from_min")), None)
            if entry is None:
                self._gap({"order_id": None, "kind": kind,
                           "why": "the engine ran a held order this session was not holding"})
                continue
            executed = held_execution_minute(entry, before, after, self.turns)
            if executed is None:
                entry.update(state=ORDER_RELEASED, why="the engine ran it, but the minute it ran cannot be "
                                                       "established from the engine's own record")
                entry["events"].append([ORDER_RELEASED, None])
                self._gap({"order_id": entry["order_id"], "kind": kind,
                           "why": "a held order ran at a minute that cannot be established"})
                continue
            order_id = f"m{executed:03d}-t{self.turns:02d}-held{index}-{kind}"
            ledger_id = entry["ledger_order_id"]
            if order_id in self.seen or (ledger_id is not None and str(ledger_id) in self.seen_ledger):
                continue                              # already mirrored: never twice
            self.seen.add(order_id)
            if ledger_id is not None:
                self.seen_ledger.add(str(ledger_id))
            entry.update(state=ORDER_EXECUTED, executed_minute=int(executed), shadow_order_id=order_id)
            entry["events"].extend([[ORDER_RELEASED, int(executed)], [ORDER_EXECUTED, int(executed)]])
            self.mirrored.append(MirroredAction(order_id, int(executed), kind, dict(entry["action"]),
                                                dict(receipt), fio2, ledger_id, entry["submission_id"]))

    def _settle_held(self, after: Mapping) -> None:
        """What became of every order still held. One still held when the patient can no longer be treated
        will never run. One that LEFT the engine's held list without a receipt reaching this session was run
        by the engine outside an observed order turn -- the engine has no cancellation, and it also releases
        held orders while clinical time passes in an information activity, which no shadow turn observes.
        That order is NOT mirrored: there is no receipt to mirror it from, so it is declared, never guessed.
        """
        family_state = after.get("family_state") or {}
        waiting = [item for item in (family_state.get("deferred_orders") or []) if isinstance(item, Mapping)]
        terminal = family_state.get("arrest_at") is not None
        minute = int(after.get("sim_time", 0) or 0)
        for entry in self.held:
            if entry["state"] != ORDER_HELD:
                continue
            match = next((item for item in waiting
                          if isinstance(item.get("action"), Mapping)
                          and str(item["action"].get("type")) == entry["kind"]
                          and str(item.get("after_result")) == entry["after_result"]
                          and item.get("requested_at_min") == entry["placed_minute"]), None)
            if match is not None:
                waiting.remove(match)
                if terminal:
                    entry.update(state=ORDER_TERMINAL_NOT_EXECUTABLE)
                    entry["events"].append([ORDER_TERMINAL_NOT_EXECUTABLE, minute])
                continue
            entry.update(state=ORDER_RELEASED, why=UNOBSERVED_RELEASE)
            entry["events"].append([ORDER_RELEASED, None])
            self._gap({"order_id": entry["order_id"], "kind": entry["kind"], "why": UNOBSERVED_RELEASE})

    def _gap(self, gap: Mapping) -> None:
        """One entry per (kind, reason): a gap that survives five turns is recorded once, not five times."""
        key = (gap.get("kind"), gap.get("why"))
        if key not in {(item.get("kind"), item.get("why")) for item in self.gaps}:
            self.gaps.append(dict(gap))

    def is_for(self, state: Mapping, generation=None) -> bool:
        """Whether this session still belongs to the encounter it opened on.

        A case id is not an encounter: a second attempt at the same case is the same case and a different
        patient history, and the generator is deterministic, so the arrival of a second attempt is
        byte-identical to the first. Three things must hold.

        - the case is the one this session opened on;
        - the clock has not gone backwards since the last minute this session saw;
        - the state is not an UNTOUCHED ARRIVAL once this session's encounter has left its own arrival,
          which is exactly what a second attempt, a reset or a regenerated encounter looks like from here.

        P3-147 replaced the third rule. It used to read "the clock is at zero and this session has already
        seen a turn", and a turn that takes no time -- placing a line, a consult, a sedative -- leaves the
        clock at zero: the page then dropped the session and opened another ON THE TREATED PATIENT, as if
        it were the arrival, with the action and its declared gap lost. A zero-minute turn does not make a
        new arrival; an untouched arrival after the encounter has moved on does.

        The session's own identity -- the digest of the arrival it opened on -- travels in the artifact, so
        a reader can tell two attempts apart afterwards even where this rule could not. What stays
        undecidable from a patient state alone (two attempts at the same case swapped between reruns
        without a reset, both already past the same minute; or a second attempt after a first one that left
        no trace at all on the patient) is declared, not papered over: it is why ``reset_session`` drops
        the session explicitly.

        P3-159: where the page has an explicit identity for the attempt (the id of its attempt record), that
        decides first: another attempt is another encounter whatever its patient looks like, which closes
        the "no trace at all" case above for every encounter that has such a record. An encounter without
        one (``generation`` None on both sides) is still read by the three rules, with the same residual.
        """
        try:
            if generation_key(generation) != self.generation:
                return False
            from clinical_core import legacy_adapter
            if str(legacy_adapter.engine_case_id(dict(state))) != self.case_id:
                return False
            minute = int(dict(state).get("sim_time", 0) or 0)
            seen = 0 if self.runner is None else int(self.runner.minutes_done)
            if minute < seen:
                return False
            return not (minute == 0 and self.left_arrival and arrival_untouched(state))
        except Exception:
            return False

    def _advance(self, minute: int, after: Mapping) -> None:
        """Advance the one runner to ``minute`` and compare it with the legacy snapshot of that minute.

        Nothing is recomputed here: the live path owns the capture and the runner owns the physics, so a
        live minute and a replayed minute are the same call on the same immutable input.
        """
        if self.runner is None:
            return
        from clinical_core import legacy_adapter
        legacy = None
        try:
            legacy = legacy_adapter.snapshot(after)
        except Exception as error:
            # A legacy snapshot that cannot be built is not a reason to stop the shadow: the minute runs
            # and is recorded as NOT compared, which is the honest reading of it.
            self.failures.append(_failure(minute, "legacy_snapshot", error, MAPPING_GAP))
        self.runner.mirror(self.mirrored)
        self.runner.advance(minute, state=self._mapping_state(), legacy=legacy)
        for gap in list(self.runner.gaps):
            self._gap(gap)
        new = self.runner.failures[self._runner_failures:]
        self._runner_failures = len(self.runner.failures)
        self.failures.extend(new)
        if self.ensemble is not None:
            # P3-140: the same mirrored actions, the same minute, the same mapping state. A witness has no
            # legacy comparison of its own: it is a development trajectory, never a fit to the engine.
            self.ensemble.advance(self.mirrored, minute, self._mapping_state())
            self.failures.extend(self.ensemble.new_failures())

    def _mapping_state(self) -> dict:
        """The only runtime fact the mapping needs beyond the mirrored actions: when endoscopy happened.

        It is kept on the session, so a later state that no longer carries the key cannot lose a haemostasis
        the engine already performed.
        """
        return {"family_state": {"endoscopy_at": self.endoscopy_at}}

    def _contributors(self):
        """The core contributors for everything mirrored so far, plus the gaps that were refused.

        One implementation, in the family adapter: the live session and the offline replay both reach the
        GI mapping through ``runtime_shadow_families.gi_interventions``.
        """
        if self.runner is None:
            return (), []
        self.runner.mirror(self.mirrored)
        before = list(self.runner.gaps)
        built = self.runner.contributors(self._mapping_state())
        gaps = [gap for gap in self.runner.gaps if gap not in before]
        return tuple(built), gaps

    # -- result ------------------------------------------------------------------------------------------
    def record(self) -> dict:
        """The shadow result: a separate object, never a source of truth and never shown to a resident."""
        failures = [vars(item) for item in self.failures]
        try:
            captured = None if self.runner is None else self.runner.replay_input()
        except Exception as error:
            # A mapping that fails outright cannot rebuild its artifact. The record says so, in the list a
            # reader already looks at, instead of raising at whoever asked for it.
            captured = None
            failures.append(vars(_failure(0 if self.runner is None else int(self.runner.minutes_done),
                                          "artifact", error, MAPPING_GAP)))
        # P3-140: the key exists only for a family that runs a region ensemble, so the record of a family
        # without one (GI) keeps exactly the keys it had.
        region = {} if self.ensemble is None else {"region_ensemble": self.ensemble.record()}
        return {
            **region,
            "runtime_authority": "legacy",
            "common_core_runtime_authority": COMMON_CORE_RUNTIME_AUTHORITY,
            "mode": self.mode,
            "case_id": self.case_id,
            "family": self.family,
            "parameter_snapshot": (PARAMETER_SNAPSHOT_ID if self.family == "gi_bleed" or self.runner is None
                                   or self.runner.snapshot_ is None else self.runner.snapshot_.id),
            "minutes": [{"minute": item.minute, "state_digest": item.state_digest,
                         "compared": item.compared_against_legacy,
                         "divergences": [vars(d) for d in item.divergences]} for item in self.minutes],
            "failures": failures,
            "gaps": list(self.gaps),
            "mirrored": [{"shadow_order_id": e.order_id, "minute": e.minute, "kind": e.kind,
                          "order_id": e.ledger_order_id, "submission_id": e.submission_id}
                         for e in self.mirrored],
            "golden_scenario_counts": golden_partial(self.family),
            # P3-141: a GI record keeps exactly what it carried; any other family names its own adapter and
            # its golden's digest, instead of being labelled with the GI adapter's version.
            "versions": versions() if self.family == "gi_bleed" else family_versions(self.family),
            "scenario_id": self.scenario_id,
            "encounter_id": self.encounter_id,
            "compared_minutes": ([] if self.runner is None else list(self.runner.compared)),
            "replay_input": (None if captured is None else captured.to_dict()),
            "replay_digest": (None if captured is None else captured.digest()),
        }

    def replay(self) -> dict:
        """Replay this run's own immutable artifact, through the same function the offline path uses."""
        import runtime_shadow_families
        try:
            captured = None if self.runner is None else self.runner.replay_input()
        except Exception:
            captured = None                        # no artifact, no replay: never the recorded minutes
        if captured is None:
            return {"minutes": []}
        replayed = runtime_shadow_families.replay_shadow_encounter(captured)
        # ``replay_shadow_encounter`` returns the arrival as minute 0; the live record starts at minute 1,
        # so the arrival is dropped here and the two lists line up index by index. A reader comparing
        # ``replay()["minutes"]`` with ``minutes`` is comparing the same minutes.
        region = {} if self.ensemble is None else {"region_ensemble": self.ensemble.replay()}
        return {**region,
                "minutes": [{"minute": item["minute"], "state_digest": item["state_digest"]}
                            for item in replayed["results"] if item["minute"] >= 1],
                "arrival_digest": next((item["state_digest"] for item in replayed["results"]
                                        if item["minute"] == 0), None),
                "final_digest": replayed["final_digest"]}

    def digests(self) -> tuple[str, ...]:
        return tuple(item.state_digest for item in self.minutes)


def golden_explained(family: str) -> dict:
    """Variable -> the declared Phase-2 differences the committed golden says explain its mismatch.

    Only a variable the golden declares mismatching in EVERY scenario of the family counts as explained. A
    variable that matches in some scenario and differs in others is not architectural there: silencing it
    would hide a plumbing fault behind a difference that belongs to another course. ``consciousness_level``
    is the case that forced this rule: the golden declares it in 1 of 20 GI scenarios, and it is the one
    reading whose disagreement must be loud.
    """
    if family in _GOLDEN:
        return _GOLDEN[family]
    counts: dict = {}
    reasons: dict = {}
    total = 0
    path = Path(__file__).resolve().parent / "clinical_core" / "golden" / f"{family}_shadow.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        scenarios = (data.get("scenarios") or {}).values()
        total = len(scenarios)
        for scenario in scenarios:
            for name, declared in (scenario.get("mismatching") or {}).items():
                counts[name] = counts.get(name, 0) + 1
                reasons.setdefault(name, set()).update(declared or ())
    except Exception:
        counts, reasons, total = {}, {}, 0
    _GOLDEN[family] = {name: tuple(sorted(reasons[name])) for name, seen in counts.items()
                       if total and seen == total}
    _GOLDEN_PARTIAL[family] = {name: (seen, total) for name, seen in sorted(counts.items())}
    return _GOLDEN[family]


def golden_path(family: str) -> Path:
    """Where the committed golden of a family lives: the baseline every classification here reads."""
    return Path(__file__).resolve().parent / "clinical_core" / "golden" / f"{family}_shadow.json"


def golden_digest(family: str) -> str:
    """The digest of that golden. Without it an artifact could not say which baseline classified it."""
    import hashlib
    path = golden_path(family)
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return "missing"


def golden_conditions(family: str) -> dict:
    """For each variable the golden declares in SOME of its scenarios: the condition attached to it.

    A per-scenario declaration is not a probability: the golden records, scenario by scenario, which
    variables differed, and a variable differs there BECAUSE of what that scenario did. So a count alone
    ("10 of 20") explains nothing by itself; what a reader needs is which scenarios declare it and what
    those scenarios ordered. This returns exactly that, computed from the golden, and classifies nothing.
    """
    golden_explained(family)
    partial = {name: (seen, total) for name, (seen, total) in _GOLDEN_PARTIAL.get(family, {}).items()
               if total and 0 < seen < total}
    if not partial:
        return {}
    try:
        data = json.loads(golden_path(family).read_text(encoding="utf-8"))
        scenarios = data.get("scenarios") or {}
    except Exception:
        return {name: {"seen": seen, "total": total} for name, (seen, total) in partial.items()}
    out = {}
    for name, (seen, total) in partial.items():
        declaring = sorted(key for key, item in scenarios.items()
                           if name in (item.get("mismatching") or {}))
        silent = sorted(key for key in scenarios if key not in declaring)
        out[name] = {
            "seen": seen, "total": total, "declaring_scenarios": declaring, "silent_scenarios": silent,
            # The golden's scenario NAMES are the condition (``aggressive_volume``, ``untreated_60``,
            # ``definitive_management``...). Its ``orders`` hold the resident text of each turn, which is
            # neither shorter nor more precise than the name, so the name is what travels.
            "turns_where_declared": sorted({len(scenarios[key].get("orders") or {})
                                            for key in declaring}),
        }
    return out


#: Why a difference is NOT_COMPARABLE for a family that has no committed golden.
NO_GOLDEN = ("no committed golden for this family: the legacy engine is not a baseline here, and it is never a "
             "calibration target, so this difference is recorded and classified as neither architecture nor "
             "plumbing")
_GOLDEN_SCENARIOS = {}
#: The families whose classification REQUIRES their committed golden. If it cannot be read, their differences
#: are UNEXPECTED, as they always were: a lost baseline must trip the evidence blockers, not quiet them.
GOLDEN_REQUIRED = ("gi_bleed",)


def golden_scenarios(family: str) -> int:
    """How many scenarios the family's committed golden holds; 0 when there is no golden to read."""
    if family not in _GOLDEN_SCENARIOS:
        try:
            data = json.loads(golden_path(family).read_text(encoding="utf-8"))
            _GOLDEN_SCENARIOS[family] = len(data.get("scenarios") or {})
        except Exception:
            _GOLDEN_SCENARIOS[family] = 0
    return _GOLDEN_SCENARIOS[family]


def golden_partial(family: str) -> dict:
    """Variable -> (scenarios that declare it, scenarios in total). Reported, never used to silence."""
    golden_explained(family)
    return _GOLDEN_PARTIAL.get(family, {})


def classify(variable, core_value, family: str) -> tuple:
    """(status, reasons) for a mismatching variable. The ONE classifier of the Phase-3 layer (P3-11)."""
    status = _classify(variable, core_value, family)
    if status == NOT_COMPARABLE:
        return status, (NO_GOLDEN,)
    if status == EXPECTED:
        return status, golden_explained(family).get(variable.name, ())
    if status == PARTIALLY_EXPLAINED:
        seen, total = golden_partial(family)[variable.name]
        return status, (f"the golden declares this difference in {seen} of its {total} scenarios",)
    return status, ()


def _classify(variable, core_value, family: str) -> str:
    if core_value is None:
        return BOUNDARY
    if variable.name in _SAFETY_VARIABLES:
        return SAFETY_CRITICAL
    if family not in GOLDEN_REQUIRED and not golden_scenarios(family):
        # P3-141: every class below is read off the family's committed golden. A family that has none has
        # no baseline to say which difference is architecture and which is plumbing, so calling its
        # differences UNEXPECTED would cry plumbing at every one of them and bury a real fault. They are
        # NOT_COMPARABLE, with the reason; the two safety readings above stay loud. A family that is
        # SUPPOSED to have a golden is not excused by losing it: there the old rule stands, and loudly.
        return NOT_COMPARABLE
    if variable.name in golden_explained(family):
        return EXPECTED
    seen, total = golden_partial(family).get(variable.name, (0, 0))
    if seen and total and seen < total:
        return PARTIALLY_EXPLAINED
    if _disabled(variable.name):
        return PARAMETER_DISABLED
    return UNEXPECTED


def _disabled(name: str) -> bool:
    from clinical_core.derived import DEFAULT_PROFILE
    for field_name in _DRIVERS.get(name, ()):
        value = getattr(DEFAULT_PROFILE, field_name, None)
        if value in (0, 0.0, None, (), False):
            return True
    return False


def _class_of(error: Exception) -> str:
    from clinical_core.state import CoreInvariantError, UnresolvedBoundary
    if isinstance(error, UnresolvedBoundary):
        return BOUNDARY
    if isinstance(error, CoreInvariantError):
        return UNEXPECTED
    return MAPPING_GAP


def _failure(minute: int, where: str, error: Exception, classification: str) -> ShadowFailure:
    try:
        message = str(error)[:400]
    except Exception:                       # an error that cannot even describe itself is still recorded
        message = "the error could not be described"
    return ShadowFailure(minute, where, type(error).__name__, message, classification)


def _encounter_id(state: Mapping) -> str:
    """The identity of one encounter: the digest of the patient as it arrived, nothing written anywhere."""
    import hashlib
    payload = {key: state.get(key) for key in ("observable", "hidden", "family_state", "engine_family",
                                               "case_id", "variant_id", "sim_time")}
    try:
        blob = json.dumps(payload, sort_keys=True, default=str)
    except Exception:
        return ""
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _state_mark(state) -> str:
    """A digest of an engine state as the session saw it: what tells one observed turn from another."""
    import hashlib
    try:
        blob = json.dumps(state, sort_keys=True, default=str)
    except Exception:
        blob = repr(state)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def legacy_terminal_of(state) -> dict | None:
    """What the legacy engine's state records of a terminal event: the minute of its arrest and of its
    fibrillation, each None while it has not happened. None when the state cannot be read. Never raises."""
    try:
        family_state = dict(state).get("family_state") or {}
        found = {}
        for name in ("arrest_at", "vf_at"):
            value = family_state.get(name)
            found[name] = None if value is None else int(value)
        return found
    except Exception:
        return None


def generation_key(value) -> str | None:
    """The session's reading of an attempt identity: a digest, so the identifier itself is never copied into
    a session or a trace. None stays None -- an encounter with no attempt record has no generation."""
    if value is None or value == "":
        return None
    import hashlib
    return "g-" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _digest_of(state) -> str:
    from clinical_core.integration import digest
    return digest(state.to_dict())


def layer_digest() -> str:
    """The identity of the Phase-3 layer that produced an artifact: the digest of its own sources.

    A commit hash cannot be read at runtime in a deployment, and a hardcoded one goes stale the moment the
    layer changes; the digest of the layer's files is computable anywhere and says exactly which code ran.
    """
    import hashlib
    here = Path(__file__).resolve().parent
    accumulator = hashlib.sha256()
    for name in LAYER_SOURCES:
        path = here / name
        accumulator.update(name.encode("utf-8"))
        accumulator.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("utf-8")
                           if path.exists() else b"missing")
    return accumulator.hexdigest()


def versions() -> dict:
    """What a shadow or replay artifact must carry to be reproducible."""
    from clinical_core import closure_guard
    return {"phase2_closure_head": PHASE2_CLOSURE_HEAD, "phase2_digest": PHASE2_DIGEST,
            **active_core(),
            "phase3_module": MODULE_VERSION, "adapter": ADAPTER_VERSION,
            "parameter_snapshot": PARAMETER_SNAPSHOT_ID,
            "closure_guard_digest": closure_guard.freeze_digest(),
            "phase3_layer_digest": layer_digest()}


def active_core() -> dict:
    """Which member of the lineage the live core is, and the digest its files recompute to. The two closure
    identities say what the lineage roots at; these two say which core actually produced the artifact. Naming a
    version here authorizes nothing: only the lineage gate decides whether the runtime may stand on it."""
    import runtime_shadow_evidence as evidence        # it imports this module: resolved at call time
    live = evidence.phase2_digest_now()
    entry = next((version for version in CORE_LINEAGE if version.digest == live), None)
    return {"core_version": entry.version_id if entry is not None else "NOT_IN_THE_LINEAGE", "core_digest": live}


def family_versions(family: str) -> dict:
    """``versions()`` plus what depends on the family: the golden every divergence is classified against.

    ``versions()`` names the GI adapter, the only one there was. For any other family the artifact names
    ITS adapter (P3-141): an opioid artifact labelled with the GI adapter's version would be a false
    provenance. A GI artifact is unchanged.
    """
    out = {**versions(), "golden_digest": golden_digest(family)}
    if str(family or "") != "gi_bleed":
        import runtime_shadow_families             # it imports this module: resolved at call time
        adapter = runtime_shadow_families.adapter_for(family)
        if adapter is not None:
            out["adapter"] = adapter.version
            # The same false label, found by the review: this family's committed run is its own
            # migration's profile, not the Phase-2 default one.
            out["parameter_snapshot"] = adapter.snapshot().id
    return out


#: The formally closed Phase-2 base this plumbing observes, as the closure record states it.
PHASE2_CLOSURE_HEAD = "d2cca46626ed5d45a792ec9456d46fb75fe87731"
PHASE2_DIGEST = "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"


@dataclass(frozen=True)
class CoreVersion:
    """One version of the common core that a certification stands behind, or is being asked to.

    ``digest`` is the digest of the package's sources as that version left them. ``record`` is the repository
    path of the version's own record, which states its status and its evidence. ``reversal`` names the module
    that rebuilds the PARENT's tree from this version's by reversing declared insertions: it is what lets the
    historical closure go on being verified from the live files after a successor exists.
    """

    version_id: str
    parent: str | None
    digest: str
    record: str
    head: str | None = None
    reversal: str | None = None


CERTIFIED = "CERTIFIED"
CANDIDATE = "CANDIDATE"
#: The ordered, immutable lineage of the common core. The first entry is the historical Phase-2 closure and is
#: certified by construction: nothing here can restate it. Every later entry is a successor whose STATUS is not
#: written here -- it is read from its record and bound to this entry's digest -- so naming a digest in this
#: tuple authorizes nothing by itself: a successor counts only once its record says CERTIFIED for that same
#: digest, and only while the historical closure still verifies underneath it.
CORE_LINEAGE = (
    CoreVersion("PHASE2_CLOSURE", None, PHASE2_DIGEST, "docs/revision/P2X3_phase2_closure.json",
                head=PHASE2_CLOSURE_HEAD),
    CoreVersion("PHASE2_AMENDMENT_1", "PHASE2_CLOSURE",
                "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635",
                "docs/revision/PHASE2_AMENDMENT_1.json", reversal="clinical_core.amendment_1"),
    CoreVersion("PHASE2_AMENDMENT_2", "PHASE2_AMENDMENT_1",
                "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2",
                "docs/revision/PHASE2_AMENDMENT_2.json", reversal="clinical_core.amendment_2"),
)
MODULE_VERSION = "P3-11"
ADAPTER_VERSION = "gi_haemorrhage/P3-11"
#: The Phase-3 layer's own sources, whose digest identifies the code that produced an artifact.
#: P3-148 and P3-149 add the shadow research trace store and its faculty observer: they are part of the layer,
#: so the digest covers them and the guards that exempt the layer exempt nothing else.
#: P3-213/214/216: the dormant pair authority (the V1 binding, the pair transaction and the dry evaluator) joined the layer, so the digest covers it too.
LAYER_SOURCES = ("runtime_shadow.py", "runtime_shadow_families.py", "runtime_shadow_evidence.py",
                 "runtime_authority.py", "runtime_authority_store.py", "runtime_shadow_store.py",
                 "runtime_shadow_observer.py", "runtime_authority_pair.py", "runtime_minute_validation.py", "runtime_pair_site.py",
                 "runtime_pressure_grant.py", "runtime_authority_session.py", "runtime_authority_turn.py")
