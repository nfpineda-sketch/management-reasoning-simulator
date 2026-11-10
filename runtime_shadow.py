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
#: Live shadow is GI only in P3-1 (the only family with a certified runtime mapping and a committed
#: golden). P3-122 audited ACS for this list and REFUSED it: its treatment semantics are ready, its
#: arrival mapping is not (see ``runtime_shadow_families.ACS_LIVE_GAP``).
LIVE_FAMILIES = ("gi_bleed",)
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
    mirrored: list = field(default_factory=list)
    seen: set = field(default_factory=set)
    seen_ledger: set = field(default_factory=set)
    failures: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    endoscopy_at: int | None = None
    turns: int = 0
    _runner_failures: int = 0

    # -- construction ------------------------------------------------------------------------------------
    @classmethod
    def start(cls, state: Mapping, *, environ: Mapping[str, str] | None = None,
              scenario_id: str | None = None) -> "ShadowSession | None":
        """Open a session for this encounter, or None when the flag is off or the family is not enabled.

        The arrival mapping, the family's writers and the profile all come from the family adapter, which is
        the same object the offline replay opens: one mapping, one snapshot, one execution path.
        """
        family = str(state.get("engine_family") or "")
        if not enabled_for(family, environ):
            return None
        try:
            minute = int(state.get("sim_time", 0) or 0)
        except Exception:
            minute = -1
        if minute != 0:
            # Opening at minute N would read the arrival from a treated patient and then label the minutes
            # as counted from arrival, and every order given before this point would be missing from the
            # mirror without a gap. A turn of the flag mid-encounter, a reload or a resumed case lands
            # here: the encounter runs legacy-only, which is the honest reading.
            return None
        session = cls(case_id="", family=family, scenario_id=scenario_id)
        try:
            import runtime_shadow_families
            from clinical_core import legacy_adapter
            arrival = deepcopy(dict(state))
            session.arrival = arrival
            session.case_id = legacy_adapter.engine_case_id(arrival)
            session.encounter_id = _encounter_id(arrival)
            session.runner = runtime_shadow_families.ShadowPhysiologyRunner.open(
                family, session.case_id, state=arrival, scenario_id=scenario_id)
            if session.runner is None:
                session.failures.append(ShadowFailure(
                    0, "start", "NoCertifiedAdapter",
                    f"no certified shadow adapter for {family}/{session.case_id}", MAPPING_GAP))
        except Exception as error:  # the encounter must not care why the shadow could not start
            session.failures.append(_failure(0, "start", error, MAPPING_GAP))
            session.runner = None
        return session

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
        """Whether this session still belongs to the encounter it opened on.

        A case id is not an encounter: a second attempt at the same case is the same case and a different
        patient history, and the generator is deterministic, so the arrival of a second attempt is
        byte-identical to the first. The clock is what separates them, and it is the only thing in a
        patient state that can: three things must hold.

        - the case is the one this session opened on;
        - the clock has not gone backwards since the last minute this session saw;
        - the clock has not returned to zero after this session already advanced, which is exactly what a
          second attempt, a reset or a regenerated encounter looks like from here.

        The session's own identity -- the digest of the arrival it opened on -- travels in the artifact, so
        a reader can tell two attempts apart afterwards even where this rule could not. What stays
        undecidable from a patient state alone (two attempts at the same case swapped between reruns
        without a reset, both already past the same minute) is declared, not papered over: it is why
        ``reset_session`` drops the session explicitly.
        """
        try:
            from clinical_core import legacy_adapter
            if str(legacy_adapter.engine_case_id(dict(state))) != self.case_id:
                return False
            minute = int(dict(state).get("sim_time", 0) or 0)
            seen = 0 if self.runner is None else int(self.runner.minutes_done)
            if minute < seen:
                return False
            return not (minute == 0 and (seen > 0 or self.turns > 0))
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
        captured = None if self.runner is None else self.runner.replay_input()
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
            "scenario_id": self.scenario_id,
            "encounter_id": self.encounter_id,
            "compared_minutes": ([] if self.runner is None else list(self.runner.compared)),
            "replay_input": (None if captured is None else captured.to_dict()),
            "replay_digest": (None if captured is None else captured.digest()),
        }

    def replay(self) -> dict:
        """Replay this run's own immutable artifact, through the same function the offline path uses."""
        import runtime_shadow_families
        captured = None if self.runner is None else self.runner.replay_input()
        if captured is None:
            return {"minutes": []}
        replayed = runtime_shadow_families.replay_shadow_encounter(captured)
        # ``replay_shadow_encounter`` returns the arrival as minute 0; the live record starts at minute 1,
        # so the arrival is dropped here and the two lists line up index by index. A reader comparing
        # ``replay()["minutes"]`` with ``minutes`` is comparing the same minutes.
        return {"minutes": [{"minute": item["minute"], "state_digest": item["state_digest"]}
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


def golden_partial(family: str) -> dict:
    """Variable -> (scenarios that declare it, scenarios in total). Reported, never used to silence."""
    golden_explained(family)
    return _GOLDEN_PARTIAL.get(family, {})


def classify(variable, core_value, family: str) -> tuple:
    """(status, reasons) for a mismatching variable. The ONE classifier of the Phase-3 layer (P3-11)."""
    status = _classify(variable, core_value, family)
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
    """``versions()`` plus what depends on the family: the golden every divergence is classified against."""
    return {**versions(), "golden_digest": golden_digest(family)}


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
LAYER_SOURCES = ("runtime_shadow.py", "runtime_shadow_families.py", "runtime_shadow_evidence.py",
                 "runtime_authority.py", "runtime_authority_store.py")
