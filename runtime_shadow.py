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
added to the patient state, nothing is initialized, nothing is logged. The pilot requires it ABSENT: it is
listed in ``pilot_freeze.RUNTIME_FLAGS``, so ``tools_pilot_preflight.py`` reports a deployment that sets it.
That listing is the guarantee -- not the mere fact that nobody sets it today, and not the environment of the
machine that runs the preflight: Streamlit copies every scalar root key of a deployment's Secrets into the
environment, so a Secret of this name would turn the shadow on without the listing to catch it.
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
#: Live shadow is GI only in P3-1 (the only family with a certified runtime mapping and a committed golden).
LIVE_FAMILIES = ("gi_bleed",)
#: The parameter snapshot P3-1 uses: the committed Phase-2 default profile, with nothing turned on.
PARAMETER_SNAPSHOT_ID = "phase2_committed_default_profile"

#: Divergence classes (P3-1-12). Structural, never a numeric threshold.
EXPECTED = "EXPECTED_DIVERGENCE"
PARAMETER_DISABLED = "PARAMETER_DISABLED_DIVERGENCE"
MAPPING_GAP = "MAPPING_GAP"
BOUNDARY = "COMMON_BOUNDARY"
UNEXPECTED = "UNEXPECTED_STRUCTURAL_DIVERGENCE"
#: The golden declares this difference in some of its scenarios and not in others, so it is architectural
#: there and a question here: reported with the count, never silenced and never alarming.
PARTIALLY_EXPLAINED = "PARTIALLY_EXPLAINED_DIVERGENCE"
SAFETY_CRITICAL = "SAFETY_CRITICAL_DIVERGENCE"
MATCH = "MATCH"
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
    """The shadow mode this process runs in. Unset, empty or unknown is OFF."""
    value = str((environ if environ is not None else os.environ).get(FLAG, "") or "").strip().lower()
    return MODE_SHADOW_COMPARE if value == MODE_SHADOW_COMPARE else MODE_OFF


def live_families(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    raw = str((environ if environ is not None else os.environ).get(FAMILIES_FLAG, "") or "").strip()
    if not raw:
        return LIVE_FAMILIES
    asked = tuple(part.strip() for part in raw.split(",") if part.strip())
    return tuple(name for name in asked if name in LIVE_FAMILIES)


def enabled_for(family: str | None, environ: Mapping[str, str] | None = None) -> bool:
    """Whether live shadow comparison runs for this engine family. OFF, or another family, is False."""
    return mode(environ) == MODE_SHADOW_COMPARE and str(family or "") in live_families(environ)


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
class Divergence:
    variable: str
    kind: str
    legacy: Any
    core: Any
    status: str
    #: When the status is EXPECTED_DIVERGENCE, the declared Phase-2 differences the golden cites for it.
    reasons: tuple = ()


@dataclass(frozen=True)
class ShadowMinute:
    minute: int
    state_digest: str
    derived: Mapping[str, Any]
    compared_against_legacy: bool
    divergences: tuple[Divergence, ...]


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
    anchors: Any = None
    module: Any = None
    mirrored: list = field(default_factory=list)
    seen: set = field(default_factory=set)
    seen_ledger: set = field(default_factory=set)
    minutes: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    endoscopy_at: int | None = None
    turns: int = 0
    _last_minute: int = 0

    # -- construction ------------------------------------------------------------------------------------
    @classmethod
    def start(cls, state: Mapping, *, environ: Mapping[str, str] | None = None) -> "ShadowSession | None":
        """Open a session for this encounter, or None when the flag is off or the family is not enabled."""
        family = str(state.get("engine_family") or "")
        if not enabled_for(family, environ):
            return None
        session = cls(case_id="", family=family)
        try:
            from clinical_core import legacy_adapter
            arrival = deepcopy(dict(state))
            session.arrival = arrival
            session.case_id = legacy_adapter.engine_case_id(arrival)
            session.anchors = legacy_adapter.anchors_from_legacy(arrival)
            session.module = legacy_adapter.haemorrhage_from_legacy(arrival)
        except Exception as error:  # the encounter must not care why the shadow could not start
            session.failures.append(_failure(0, "start", error, MAPPING_GAP))
            session.anchors = None
        return session

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

    def _observe(self, before, after: Mapping, parsed, result, ran, submission_id) -> None:
        if self.anchors is None:
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
        minute = int((before or {}).get("sim_time", 0) or 0)
        fio2 = float((after.get("family_state") or {}).get("oxygen_fio2", 0.21))
        receipts: dict = {}
        for summary in list(result.get("action_summaries") or []):
            receipts.setdefault(str(summary.get("type") or ""), []).append(summary)
        taken: dict = {}
        for index, action in enumerate(list(ran)):
            kind = str(action.get("type") or "")
            # The turn number keeps two turns of the same minute from sharing an id.
            order_id = f"m{minute:03d}-t{self.turns:02d}-{index}-{kind}"
            if order_id in self.seen:
                continue
            if action.get("after_result"):
                self._gap({"order_id": order_id, "why": "held until a result arrives", "kind": kind})
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

    def _gap(self, gap: Mapping) -> None:
        """One entry per (kind, reason): a gap that survives five turns is recorded once, not five times."""
        key = (gap.get("kind"), gap.get("why"))
        if key not in {(item.get("kind"), item.get("why")) for item in self.gaps}:
            self.gaps.append(dict(gap))

    def is_for(self, state: Mapping) -> bool:
        """Whether this session belongs to the encounter in ``state``; False after the case changed."""
        try:
            from clinical_core import legacy_adapter
            return str(legacy_adapter.engine_case_id(dict(state))) == self.case_id
        except Exception:
            return False

    def _advance(self, minute: int, after: Mapping) -> None:
        """Run the core from arrival to ``minute`` and compare with the legacy snapshot of that minute."""
        if minute < self._last_minute:
            self.failures.append(ShadowFailure(minute, "advance", "TimeOrder",
                                               "the engine's clock went backwards", UNEXPECTED))
            return
        from clinical_core import integration, legacy_adapter
        from clinical_core.derived import DEFAULT_PROFILE
        contributors, gaps = self._contributors()
        for gap in gaps:
            self._gap(gap)
        try:
            trajectory = integration.run(self.anchors, contributors, minute, DEFAULT_PROFILE)
        except Exception as error:
            self.failures.append(_failure(minute, "core", error, _class_of(error)))
            return
        derived = trajectory.derived()
        legacy = legacy_adapter.snapshot(after)
        states = trajectory.states
        for index in range(self._last_minute + 1, minute + 1):
            at_boundary = index == minute
            self.minutes.append(ShadowMinute(
                index, _digest_of(states[index]), derived[index].to_dict(), at_boundary,
                tuple(self._compare(legacy, states[index], derived[index])) if at_boundary else ()))
        if minute == self._last_minute and minute >= 1 and self.minutes:
            # A turn that advanced no minute still has a legacy truth to compare against: the comparison
            # of that minute is refreshed instead of being lost (the record keeps one entry per minute).
            last = self.minutes[-1]
            self.minutes[-1] = ShadowMinute(last.minute, last.state_digest, last.derived, True,
                                            tuple(self._compare(legacy, states[minute], derived[minute])))
        self._last_minute = minute

    def _contributors(self):
        """The core contributors for everything mirrored so far, plus the gaps that were refused.

        The GI mapping itself lives in ``runtime_shadow_families.gi_interventions`` since P3-4, so the live
        session and the generic adapter share one implementation. The import is deferred because that module
        reads this one.
        """
        import runtime_shadow_families
        built, gaps = runtime_shadow_families.gi_interventions(self.mirrored, self.endoscopy_at)
        return (self.module,) + tuple(built), gaps

    def _compare(self, legacy: Mapping, state, values):
        """Legacy against core for this minute, through the certified variable table."""
        from clinical_core import comparison
        projected = comparison._display(values)
        for variable in comparison.VARIABLES:
            left = variable.legacy(legacy) if variable.legacy else None
            right = variable.core(state, values, projected) if variable.core else None
            if variable.kind in ("core_only", "legacy_only"):
                continue
            match = comparison._matches(variable.kind, left, right)
            if match is None:
                yield Divergence(variable.name, variable.kind, left, right, NOT_COMPARABLE)
            elif match:
                yield Divergence(variable.name, variable.kind, left, right, MATCH)
            else:
                status = _classify(variable, right, self.family)
                reasons = ()
                if status == EXPECTED:
                    reasons = golden_explained(self.family).get(variable.name, ())
                elif status == PARTIALLY_EXPLAINED:
                    seen, total = golden_partial(self.family)[variable.name]
                    reasons = (f"the golden declares this difference in {seen} of its {total} scenarios",)
                yield Divergence(variable.name, variable.kind, left, right, status, reasons)

    # -- result ------------------------------------------------------------------------------------------
    def record(self) -> dict:
        """The shadow result: a separate object, never a source of truth and never shown to a resident."""
        from clinical_core import integration
        from clinical_core.derived import DEFAULT_PROFILE
        return {
            "runtime_authority": "legacy",
            "common_core_runtime_authority": COMMON_CORE_RUNTIME_AUTHORITY,
            "mode": self.mode,
            "case_id": self.case_id,
            "family": self.family,
            "parameter_snapshot": PARAMETER_SNAPSHOT_ID,
            "minutes": [{"minute": item.minute, "state_digest": item.state_digest,
                         "compared": item.compared_against_legacy,
                         "divergences": [vars(d) for d in item.divergences]} for item in self.minutes],
            "failures": [vars(item) for item in self.failures],
            "gaps": list(self.gaps),
            "mirrored": [{"shadow_order_id": e.order_id, "minute": e.minute, "kind": e.kind,
                          "order_id": e.ledger_order_id, "submission_id": e.submission_id}
                         for e in self.mirrored],
            "golden_scenario_counts": golden_partial(self.family),
            "versions": versions(),
            "replay_input": (None if self.anchors is None else integration.scenario_to_dict(
                self.anchors, self._contributors()[0], self._last_minute, DEFAULT_PROFILE)),
        }

    def replay(self) -> dict:
        """Replay the captured immutable input and return the minute digests, for determinism checks."""
        from clinical_core import integration
        data = self.record()["replay_input"]
        if data is None:
            return {"minutes": []}
        anchors, contributors, minutes, profile = integration.scenario_from_dict(data)
        trajectory = integration.run(anchors, contributors, minutes, profile)
        return {"minutes": [{"minute": index, "state_digest": _digest_of(state)}
                            for index, state in enumerate(trajectory.states)]}

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


def golden_partial(family: str) -> dict:
    """Variable -> (scenarios that declare it, scenarios in total). Reported, never used to silence."""
    golden_explained(family)
    return _GOLDEN_PARTIAL.get(family, {})


def _classify(variable, core_value, family: str) -> str:
    if core_value is None:
        return BOUNDARY
    if variable.name in _SAFETY_VARIABLES:
        return SAFETY_CRITICAL
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
    return ShadowFailure(minute, where, type(error).__name__, str(error)[:400], classification)


def _digest_of(state) -> str:
    from clinical_core.integration import digest
    return digest(state.to_dict())


def _engine():
    import family_engine
    return family_engine


def versions() -> dict:
    """What a shadow or replay artifact must carry to be reproducible."""
    from clinical_core import closure_guard
    return {"phase2_closure_head": PHASE2_CLOSURE_HEAD, "phase2_digest": PHASE2_DIGEST,
            "phase3_module": MODULE_VERSION, "adapter": ADAPTER_VERSION,
            "parameter_snapshot": PARAMETER_SNAPSHOT_ID,
            "closure_guard_digest": closure_guard.freeze_digest()}


#: The formally closed Phase-2 base this plumbing observes, as the closure record states it.
PHASE2_CLOSURE_HEAD = "d2cca46626ed5d45a792ec9456d46fb75fe87731"
PHASE2_DIGEST = "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
MODULE_VERSION = "P3-1"
ADAPTER_VERSION = "gi_haemorrhage/P3-1"
