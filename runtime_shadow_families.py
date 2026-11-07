"""P3-4: the generic shadow orchestration layer and one adapter per certified Phase-2 family.

Observation only, as in P3-1: the legacy engine is the only runtime authority
(``runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY`` is False) and nothing here writes to a patient state, a
ledger, a score or a trace. This module adds what P3-1 left family-specific, without touching it:

- ``RuntimeFamilyAdapter``: what an adapter may do -- name its certified cases, map the arrival, build the
  family's certified writers, map treatments the engine already decided, and name its parameter snapshot --
  and what it may not: invent a latent value from a future trajectory, write a channel the family does not
  own, read the score, decide an order's fate, or touch runtime state. Each adapter delegates to the
  package Phase 2 certified for its family (``*_reference`` for the arrival, ``*_migration`` for the writers),
  so no mapping is re-derived here.
- ``ShadowParameterSnapshot``: a named, immutable parameter choice with its provenance. Every span it reads is
  a committed Phase-2 tuple (``acs_migration.LOSS_PER_MIN``, ``edema_migration.PROGRESSION``, ...) or a
  reference band's point, all declared ``synthetic_probe`` so the migration gate keeps blocking them: naming a
  witness is reading a region, never approving a value.
- ``ShadowReplayInput`` and ``replay_shadow_encounter``: the immutable input of one shadow run, and its
  deterministic replay. No wall clock, no UI state, no randomness, no provider call.
- ``ShadowDivergenceRecord``: the structured classification by domain.

Live shadow stays gated per family by ``runtime_shadow`` (P3-1 enables GI only); offline replay is available
for every family whose adapter maps its arrival deterministically.

P3-11 made ``ShadowPhysiologyRunner.advance`` the ONE execution primitive: the live session of
``runtime_shadow`` captures the authoritative inputs, builds the immutable mirrored events and calls this
runner, and the offline replay loads those same events and calls the same runner. There is no second
minute-advance, no second classifier and no second replay artifact, so live and replay are equal BY
CONSTRUCTION and the tests only have to confirm it (``LIVE_REPLAY_SINGLE_EXECUTION_PATH``).
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import runtime_shadow as rs

MODULE_VERSION = "P3-4"

#: The domains a divergence is reported in (P3-4O).
DOMAINS = ("HEMODYNAMICS", "RESPIRATION", "OXYGENATION", "ACID_BASE", "METABOLIC", "HR_RHYTHM",
           "CONSCIOUSNESS", "COLLAPSE", "INTERVENTIONS")
#: Which domain each comparison variable belongs to. Anything unlisted is reported as NOT_COMPARABLE.
DOMAIN_OF = {
    "V_ml_eq": "HEMODYNAMICS", "sbp": "HEMODYNAMICS", "dbp": "HEMODYNAMICS", "map": "HEMODYNAMICS",
    "crt_s": "HEMODYNAMICS", "delivery_rel": "HEMODYNAMICS",
    "hr": "HR_RHYTHM", "rhythm": "HR_RHYTHM", "pulse_present": "COLLAPSE",
    "spo2": "OXYGENATION", "fio2": "OXYGENATION",
    "respiratory_rate": "RESPIRATION",
    "lactate_mmol_l": "METABOLIC", "D": "METABOLIC", "glucose_mg_dl": "METABOLIC", "k_mmol_l": "METABOLIC",
    "hb_g_dl": "INTERVENTIONS", "fluid_delivered_ml": "INTERVENTIONS",
    "blood_delivered_units": "INTERVENTIONS", "hemostasis_relief": "INTERVENTIONS",
    "transfusion_overload_units": "INTERVENTIONS",
    "consciousness_level": "CONSCIOUSNESS",
}
#: Statuses a divergence record carries (P3-4O). No numeric safety threshold anywhere.
EXPECTED_ARCHITECTURAL = rs.EXPECTED
PARAMETER_DISABLED = rs.PARAMETER_DISABLED
REGION_DIVERGENCE = "REGION_DIVERGENCE"
MAPPING_GAP = rs.MAPPING_GAP
TREATMENT_GAP = "TREATMENT_GAP"
BOUNDARY = rs.BOUNDARY
UNEXPECTED = rs.UNEXPECTED
NOT_COMPARABLE = rs.NOT_COMPARABLE

#: The three points a region witness may take -- the names the reference modules' own ``Band`` uses -- and
#: the committed default, which reads no band at all.
POINTS = ("lower", "midpoint", "upper")
COMMITTED = "committed_default"


@dataclass(frozen=True)
class ShadowParameterSnapshot:
    """A named parameter choice with its provenance. Immutable; never a claim of clinical approval."""

    id: str
    family: str
    point: str
    #: Where each value comes from: the module and the committed tuple or band it was read from.
    provenance: tuple
    approved: bool = False

    def __post_init__(self):
        if self.approved:
            raise ValueError("a shadow snapshot never carries an approved clinical value")
        if self.point not in POINTS + (COMMITTED,):
            raise ValueError(f"unknown snapshot point {self.point!r}")

    def to_dict(self) -> dict:
        return {"id": self.id, "family": self.family, "point": self.point,
                "provenance": list(self.provenance), "approved": False}


@dataclass(frozen=True)
class ShadowMinuteResult:
    minute: int
    state_digest: str
    derived: Mapping[str, Any]


@dataclass(frozen=True)
class ShadowDivergenceRecord:
    minute: int
    domain: str
    variable: str
    legacy: Any
    core: Any
    status: str
    reasons: tuple = ()


@dataclass(frozen=True)
class ShadowReplayInput:
    """Everything a shadow run needs, and nothing else: no UI state, no clock, no randomness."""

    case_id: str
    family: str
    adapter_version: str
    snapshot: Mapping[str, Any]
    minutes: int
    #: The resident actions as the engine decided them, in order, with their fate already settled.
    actions: tuple
    #: ``integration.scenario_to_dict``: anchors, contributors and profile, all serializable.
    scenario: Mapping[str, Any]
    versions: Mapping[str, Any] = field(default_factory=dict)
    #: The acceptance scenario this run belongs to, when a harness named one (P3-11-11).
    scenario_id: str | None = None

    def to_dict(self) -> dict:
        return {"case_id": self.case_id, "family": self.family, "adapter_version": self.adapter_version,
                "snapshot": dict(self.snapshot), "minutes": self.minutes,
                "actions": [dict(action) for action in self.actions], "scenario": dict(self.scenario),
                "versions": dict(self.versions), "scenario_id": self.scenario_id}

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True, default=str)
                              .encode("utf-8")).hexdigest()


class RuntimeFamilyAdapter:
    """What a family must supply to be shadowed. Read-only by contract; see the module docstring."""

    family = ""
    version = ""
    cases: tuple = ()
    #: Whether this adapter may run inside a live encounter (P3-7 decides; P3-1 enabled GI only).
    live = False
    #: Runtime action types this family maps to a core contributor, and the ones it declares as gaps.
    maps: tuple = ()
    gaps_declared: Mapping[str, str] = {}

    def supports(self, case_id: str) -> str | None:
        """None when the case is one this adapter certifies, else the reason it is refused."""
        return None if case_id in self.cases else f"{case_id!r} is not a certified {self.family} case"

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        raise NotImplementedError

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        raise NotImplementedError

    def profile(self, point: str):
        raise NotImplementedError

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        raise NotImplementedError

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        """(contributors, gaps): only actions the engine already executed, each mapped once or declared."""
        return (), [{"kind": event.kind, "order_id": event.order_id,
                     "why": self.gaps_declared.get(event.kind, "no core intervention for this order type")}
                    for event in mirrored if event.kind not in self.maps]


# -- the six certified families ------------------------------------------------------------------------------

def registry_region() -> dict:
    """The profile magnitudes whose Phase-2 region is a region, from the frozen calibration registry.

    Three rules, all of them refusals:

    - a magnitude the registry holds (``lower == upper``) is not a region and is never moved;
    - a magnitude the committed profile leaves unset is a mechanism Phase 2 left OFF: a witness never
      turns one on, so it is excluded even when the registry carries a span for it;
    - nothing here is approved. ``REGISTRY`` says 0 magnitudes are faculty-approved and a witness is a
      reading of the declared region, never a selection.
    """
    from clinical_core import calibration
    from clinical_core.derived import DEFAULT_PROFILE
    import dataclasses
    fields = {field.name for field in dataclasses.fields(DEFAULT_PROFILE)}
    out = {}
    for name, entry in calibration.REGISTRY.items():
        if entry.target != "profile" or name not in fields:
            continue
        if entry.lower is None or entry.upper is None or float(entry.upper) <= float(entry.lower):
            continue
        if getattr(DEFAULT_PROFILE, name) is None:
            # The committed profile leaves this mechanism OFF; a witness never turns one on.
            continue
        out[name] = entry
    return out


def _bundle_profile(point: str):
    """The committed profile, or the lower/upper corner of the declared region as a named bundle.

    It is a CORNER of the region, not a distribution and not a correlation claim: every magnitude is read
    at the same named edge of its own certified span. ``POINTS``' midpoint is the committed profile, which
    is not the registry midpoint for every magnitude -- ``region_notes`` says exactly where they differ.
    """
    import dataclasses
    from clinical_core.derived import DEFAULT_PROFILE
    if point in (COMMITTED, "midpoint"):
        return DEFAULT_PROFILE
    edge = "lower" if point == "lower" else "upper"
    return dataclasses.replace(DEFAULT_PROFILE,
                               **{name: float(getattr(entry, edge))
                                  for name, entry in registry_region().items()})


def region_notes() -> dict:
    """Where the committed profile sits inside each declared region: the honest reading of the bundle."""
    from clinical_core.derived import DEFAULT_PROFILE
    notes = {}
    for name, entry in registry_region().items():
        committed = float(getattr(DEFAULT_PROFILE, name))
        where = "midpoint" if committed == float(entry.midpoint) else (
            "lower edge" if committed == float(entry.lower) else
            "upper edge" if committed == float(entry.upper) else "inside, off the midpoint")
        notes[name] = {"committed": committed, "lower": float(entry.lower),
                       "midpoint": float(entry.midpoint), "upper": float(entry.upper), "where": where}
    return notes


def _point_index(point: str, span: Sequence) -> int:
    """low / midpoint / high as the first, middle and last point of a committed Phase-2 span."""
    if point in (COMMITTED, "midpoint"):
        return len(span) // 2
    return 0 if point == "lower" else len(span) - 1


class GiHaemorrhageAdapter(RuntimeFamilyAdapter):
    """GI haemorrhage: the reference adapter. Its mapping is the one Phase 2 pinned with a golden."""

    family = "gi_bleed"
    version = "gi_haemorrhage/P3-4"
    cases = ("gi_bleed_57m", "gi_bleed_72f")
    live = True
    maps = ("fluid", "blood", "oxygen", "ppi")

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import calibration
        arrival = ("clinical_core.legacy_adapter: the arrival and the haemorrhage module are read from "
                   "the case",)
        if point in (COMMITTED, "midpoint"):
            return ShadowParameterSnapshot(
                "gi_committed_default", self.family, point,
                arrival + ("clinical_core.derived.DEFAULT_PROFILE: the committed default profile, read "
                           "as a point (no band, no witness)",))
        edge = "lower" if point == "lower" else "upper"
        region = registry_region()
        return ShadowParameterSnapshot(
            f"gi_region_{edge}", self.family, point,
            arrival + (f"clinical_core.calibration.REGISTRY: the {edge} edge of the declared region of "
                       f"{len(region)} profile magnitudes, a named corner and not a distribution",
                       f"clinical_core.calibration.frozen_digest() = {calibration.frozen_digest()}",
                       "clinical_core.calibration.REGISTRY: 0 magnitudes are faculty-approved, so a "
                       "witness reads the region and does not select a value"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import legacy_adapter
        if state is None:
            state = legacy_adapter.bank_case(case_id)
        return legacy_adapter.anchors_from_legacy(state)

    def profile(self, point: str):
        return _bundle_profile(point)

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import legacy_adapter
        if state is None:
            state = legacy_adapter.bank_case(case_id)
        return (legacy_adapter.haemorrhage_from_legacy(state),)

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        endoscopy = (state or {}).get("family_state", {}).get("endoscopy_at") if state else None
        return gi_interventions(mirrored, None if endoscopy is None else int(endoscopy))


class AcsIschaemiaAdapter(RuntimeFamilyAdapter):
    """ACS: the pump and congestion writers of P2N-2, with its own committed spans."""

    family = "acs"
    version = "acs_ischaemia/P3-4"
    cases = ("acs_70f_left_main",)
    live = False
    maps = ("oxygen",)
    gaps_declared = {"reperfusion": "the core has a reperfusion writer but the runtime action is not mapped yet",
                     "fluid": "no certified ACS fluid mapping in the shadow adapter",
                     "medicine": "antiplatelet, anticoagulant, nitrate and opiate have no ACS core target"}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import acs_migration as am
        loss = am.LOSS_PER_MIN[_point_index(point, am.LOSS_PER_MIN)]
        share = am.CONGESTION_SHARES[_point_index(point, am.CONGESTION_SHARES)]
        return ShadowParameterSnapshot(
            f"acs_{point}", self.family, point if point in POINTS else COMMITTED,
            (f"clinical_core.acs_migration.LOSS_PER_MIN[{_point_index(point, am.LOSS_PER_MIN)}] = {loss}",
             f"clinical_core.acs_migration.CONGESTION_SHARES[{_point_index(point, am.CONGESTION_SHARES)}] "
             f"= {share}",
             f"clinical_core.acs_reference.anchors(point={point if point in POINTS else 'midpoint'!r})"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import acs_reference
        return acs_reference.anchors(point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import acs_reference
        return acs_reference.common_profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import acs_migration as am
        return am.writers(loss=am.LOSS_PER_MIN[_point_index(point, am.LOSS_PER_MIN)],
                          share=am.CONGESTION_SHARES[_point_index(point, am.CONGESTION_SHARES)],
                          recovery=am.RECOVERY_SHARES[_point_index(point, am.RECOVERY_SHARES)])


class PulmonaryEdemaAdapter(RuntimeFamilyAdapter):
    """Pulmonary oedema: the lung-water owner of P2P-1. Nitrate, diuresis and NIV stay treatment gaps."""

    family = "pulmonary_edema"
    version = "pulmonary_edema/P3-4"
    cases = ("pulmonary_edema_58m",)
    live = False
    maps = ("oxygen",)
    gaps_declared = {"medicine": "nitrate and diuretic have a decongestive writer, not a mapped runtime action",
                     "ventilation": "NIV and intubation have no core target (P2K-3 recruitment is off)"}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import edema_migration as em
        index = _point_index(point, em.PROGRESSION)
        return ShadowParameterSnapshot(
            f"edema_{point}", self.family, point if point in POINTS else COMMITTED,
            (f"clinical_core.edema_migration.PROGRESSION[{index}] = {em.PROGRESSION[index]}",
             f"clinical_core.edema_reference.anchors(point={point if point in POINTS else 'midpoint'!r})"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import edema_reference
        return edema_reference.anchors(point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import edema_migration
        return edema_migration.profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import edema_migration as em
        return (em.writer(em.PROGRESSION[_point_index(point, em.PROGRESSION)]),)


class PulmonaryEmbolismAdapter(RuntimeFamilyAdapter):
    """PE: obstruction on P, direct G and the zero-lung-water owner of P2Q-2. No treatment is modelled."""

    family = "pulmonary_embolism"
    version = "pulmonary_embolism/P3-4"
    cases = ("pulmonary_embolism_61m", "pulmonary_embolism_33f")
    live = False
    maps = ("oxygen",)
    gaps_declared = {"medicine": "anticoagulation and thrombolysis are not modelled (P2Q-2 declares it)",
                     "fluid": "no certified PE fluid mapping in the shadow adapter"}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import embolism_migration as pm
        span = tuple(pm.LOSS_PER_MIN)
        index = _point_index(point, span)
        return ShadowParameterSnapshot(
            f"pe_{point}", self.family, point if point in POINTS else COMMITTED,
            (f"clinical_core.embolism_migration.LOSS_PER_MIN[{index}] = {span[index]}",
             f"clinical_core.embolism_reference.anchors(point={point if point in POINTS else 'midpoint'!r})"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import embolism_reference
        return embolism_reference.anchors(case_id, point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import embolism_migration
        return embolism_migration.profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import embolism_migration as pm
        span = tuple(pm.LOSS_PER_MIN)
        return pm.writers(loss=span[_point_index(point, span)], name=case_id)


class AsthmaAdapter(RuntimeFamilyAdapter):
    """Asthma: the airway-obstruction writer of P2S-3. The bronchodilator is declared deferred upstream."""

    family = "asthma"
    version = "asthma/P3-4"
    cases = ("asthma_49m", "asthma_24f")
    live = False
    maps = ("oxygen",)
    gaps_declared = {"medicine": "BRONCHODILATOR_WRITER_DEFERRED and STEROID_ACUTE_PHYSIOLOGY_DEFERRED "
                                 "(clinical_core.modules.asthma declares both)",
                     "ventilation": "NIV and intubation have no core target"}

    @staticmethod
    def _span():
        """P2S-3's tuple starts with 0.0, the 'no worsening' sentinel, not the span's lower edge."""
        from clinical_core import asthma_migration as sm
        return tuple(sm.WORSENING_PER_MIN[1:])

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        span = self._span()
        index = _point_index(point, span)
        return ShadowParameterSnapshot(
            f"asthma_{point}", self.family, point if point in POINTS else COMMITTED,
            (f"clinical_core.asthma_migration.WORSENING_PER_MIN[{index + 1}] = {span[index]} "
             "(index 0 of that tuple is the 'no worsening' sentinel, not a witness)",
             f"clinical_core.asthma_reference.anchors(point={point if point in POINTS else 'midpoint'!r})"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import asthma_reference
        return asthma_reference.anchors(case_id, point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import asthma_migration
        return asthma_migration.profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core.modules.asthma import AirwayObstruction
        span = self._span()
        return (AirwayObstruction("p3-asthma-obstruction", span[_point_index(point, span)]),)


class OpioidAdapter(RuntimeFamilyAdapter):
    """Opioid: central depression and its reversal (P2U-1), each a committed point, not a span."""

    family = "opioid"
    version = "opioid/P3-4"
    cases = ("opioid_35m", "opioid_67f")
    live = False
    maps = ("oxygen",)
    gaps_declared = {"medicine": "naloxone has a core writer; the runtime action is not mapped yet",
                     "ventilation": "bag-mask and intubation have no core target"}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import opioid_migration as om
        return ShadowParameterSnapshot(
            f"opioid_{point}", self.family, COMMITTED,
            (f"clinical_core.opioid_migration.DEEPENING_PER_MIN = {om.DEEPENING_PER_MIN} "
             "(a committed point, no span is declared)",
             f"clinical_core.opioid_reference.anchors(point='midpoint')"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import opioid_reference
        return opioid_reference.anchors(case_id, point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import opioid_migration
        return opioid_migration.profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import opioid_migration as om
        return (om.depression(),)


#: Every adapter, by engine family. Live enablement is the adapter's own flag plus runtime_shadow's.
ADAPTERS = {adapter.family: adapter for adapter in (
    GiHaemorrhageAdapter(), AcsIschaemiaAdapter(), PulmonaryEdemaAdapter(),
    PulmonaryEmbolismAdapter(), AsthmaAdapter(), OpioidAdapter())}


def adapter_for(family: str) -> RuntimeFamilyAdapter | None:
    return ADAPTERS.get(str(family or ""))


def gi_interventions(mirrored: Sequence, endoscopy_at: int | None) -> tuple:
    """The GI intervention mapping, shared by the P3-1 session and the P3-4 adapter (one implementation)."""
    from clinical_core import legacy_adapter
    from clinical_core.interventions.modifiers import ProtonPumpInhibitor
    from clinical_core.interventions.oxygen import Oxygen
    from clinical_core.logistics import EndoscopicHemostasis
    import family_engine
    built, deliveries, stops, gaps = [], [], [], []
    for event in mirrored:
        kind = event.kind
        if kind in ("fluid", "blood"):
            operation = event.action.get("operation")
            if kind == "fluid" and operation == "stop":
                stops.append(((event.minute, 0), event.order_id))
                continue
            if operation is not None:
                gaps.append({"order_id": event.order_id, "kind": kind,
                             "why": f"{kind} operation {operation!r} has no core equivalent"})
                continue
            begins = event.receipt.get("delivery_starts_at_min")
            deliveries.append(legacy_adapter.Delivery(
                (event.minute, 0), kind, event.order_id, event.minute, event.action,
                event.minute if begins is None else float(begins)))
        elif kind == "oxygen":
            built.append(Oxygen(event.order_id, event.minute, event.fio2_after))
        elif kind == "ppi":
            built.append(ProtonPumpInhibitor(event.order_id, event.minute))
        elif kind in legacy_adapter.NOT_PHYSIOLOGICAL:
            continue
        else:
            gaps.append({"order_id": event.order_id, "kind": kind,
                         "why": "no core intervention for this order type yet"})
    if endoscopy_at is not None:
        built.append(EndoscopicHemostasis("gastroenterology_endoscopy", int(endoscopy_at)))
    built.extend(legacy_adapter.delivery_contributors(deliveries, stops, family_engine.GI_BLEED))
    return tuple(built), gaps


# -- the generic runner --------------------------------------------------------------------------------------

@dataclass
class ShadowPhysiologyRunner:
    """One shadow run of one encounter: open it, mirror what the engine executed, advance, read the result.

    It owns no runtime state. ``advance`` recomputes the trajectory from arrival with the contributors
    mirrored so far, which is what makes the live run and the offline replay the same function of the same
    immutable input.
    """

    adapter: RuntimeFamilyAdapter
    case_id: str
    point: str = COMMITTED
    scenario_id: str | None = None
    anchors: Any = None
    profile: Any = None
    family_writers: tuple = ()
    snapshot_: Any = None
    mirrored: list = field(default_factory=list)
    seen: set = field(default_factory=set)
    results: list = field(default_factory=list)
    divergences: list = field(default_factory=list)
    #: The minutes a legacy truth was supplied for, so a reader can tell "equal" from "not compared".
    compared: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    endoscopy_at: int | None = None
    minutes_done: int = 0
    #: The last runtime mapping state this run was advanced with. The replay artifact must be built from
    #: the SAME state, or a contributor the live run had (GI haemostasis, read from ``family_state``) would
    #: be missing from the artifact and the replay would diverge from the live run. The full acceptance
    #: battery found exactly that: two turns never ordered endoscopy, so P3-1's evidence could not see it.
    mapping_state: Mapping | None = None

    @classmethod
    def open(cls, family: str, case_id: str, *, point: str = COMMITTED, state: Mapping | None = None,
             scenario_id: str | None = None):
        """Build a runner, or None when no adapter certifies this family and case."""
        adapter = adapter_for(family)
        if adapter is None or adapter.supports(case_id) is not None:
            return None
        runner = cls(adapter, case_id, point, scenario_id)
        try:
            runner.snapshot_ = adapter.snapshot(point)
            runner.anchors = adapter.anchors(case_id, point, deepcopy(dict(state)) if state else None)
            runner.profile = adapter.profile(point)
            runner.family_writers = tuple(adapter.writers(case_id, point,
                                                          deepcopy(dict(state)) if state else None))
        except Exception as error:
            runner.failures.append(rs._failure(0, "open", error, MAPPING_GAP))
            runner.anchors = None
        return runner

    def mirror(self, events: Sequence) -> None:
        """Add the actions the engine already executed. The same order id is never mirrored twice."""
        for event in events:
            if event.order_id in self.seen:
                continue
            self.seen.add(event.order_id)
            self.mirrored.append(event)

    def contributors(self, state: Mapping | None = None) -> tuple:
        if state is not None:
            self.mapping_state = deepcopy(dict(state))
        built, gaps = self.adapter.interventions(self.mirrored, self.mapping_state)
        for gap in gaps:
            if gap not in self.gaps:
                self.gaps.append(gap)
        return tuple(self.family_writers) + tuple(built)

    def advance(self, minute: int, *, state: Mapping | None = None, legacy: Mapping | None = None) -> bool:
        """Advance the shadow to ``minute``. Returns False when it could not run; never raises."""
        if self.anchors is None or minute < self.minutes_done:
            if minute < self.minutes_done:
                self.failures.append(rs.ShadowFailure(minute, "advance", "TimeOrder",
                                                      "the engine's clock went backwards", UNEXPECTED))
            return False
        from clinical_core import integration
        try:
            trajectory = integration.run(self.anchors, self.contributors(state), minute, self.profile)
        except Exception as error:
            self.failures.append(rs._failure(minute, "core", error, rs._class_of(error)))
            return False
        derived = trajectory.derived()
        for index in range(self.minutes_done + 1, minute + 1):
            self.results.append(ShadowMinuteResult(index, rs._digest_of(trajectory.states[index]),
                                                   derived[index].to_dict()))
        if legacy is not None and minute > 0:
            # A turn that advanced no minute still has a legacy truth for it: the comparison of that minute
            # is REPLACED, so the record keeps one comparison per minute -- the latest -- and never two.
            self.divergences = [item for item in self.divergences if item.minute != minute]
            self.divergences.extend(divergence_records(minute, legacy, trajectory.states[minute],
                                                       derived[minute], self.adapter.family))
            if minute not in self.compared:
                self.compared.append(minute)
        self.minutes_done = minute
        return True

    def replay_input(self) -> ShadowReplayInput | None:
        """The immutable input of this run, or None when the adapter could not map the arrival."""
        if self.anchors is None:
            return None
        from clinical_core import integration
        # ``contributors()`` with no argument replays the remembered mapping state, so the artifact holds
        # every contributor the live run had -- nothing is read from the runtime a second time.
        scenario = integration.scenario_to_dict(self.anchors, self.contributors(), self.minutes_done,
                                                self.profile)
        return ShadowReplayInput(
            self.case_id, self.adapter.family, self.adapter.version,
            self.snapshot_.to_dict() if self.snapshot_ else {}, self.minutes_done,
            tuple(_event_identity(event) for event in self.mirrored),
            scenario, {**rs.family_versions(self.adapter.family), "families_module": MODULE_VERSION},
            self.scenario_id)

    def digests(self) -> tuple:
        return tuple(item.state_digest for item in self.results)

    def record(self) -> dict:
        return {
            "runtime_authority": "legacy",
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "case_id": self.case_id, "family": self.adapter.family,
            "adapter": self.adapter.version, "live": self.adapter.live,
            "snapshot": self.snapshot_.to_dict() if self.snapshot_ else {},
            "minutes": [{"minute": item.minute, "state_digest": item.state_digest} for item in self.results],
            "divergences": [vars(item) for item in self.divergences],
            "failures": [vars(item) for item in self.failures],
            "gaps": list(self.gaps),
            "replay_digest": (None if self.anchors is None else self.replay_input().digest()),
            "point": self.point,
        }


def divergence_records(minute: int, legacy: Mapping, state, values, family: str) -> list:
    """The certified variable table, classified by domain. No numeric threshold is introduced."""
    from clinical_core import comparison
    projected = comparison._display(values)
    out = []
    for variable in comparison.VARIABLES:
        if variable.kind in ("core_only", "legacy_only"):
            continue
        left = variable.legacy(legacy) if variable.legacy else None
        right = variable.core(state, values, projected) if variable.core else None
        match = comparison._matches(variable.kind, left, right)
        if match:
            continue
        domain = DOMAIN_OF.get(variable.name, "NOT_COMPARABLE")
        if match is None:
            status, reasons = NOT_COMPARABLE, ()
        else:
            # ONE classifier for both paths (P3-11): safety first, then the golden's own declaration, then
            # a disabled parameter, then loud. No numeric threshold is introduced here or there.
            status, reasons = rs.classify(variable, right, family)
        out.append(ShadowDivergenceRecord(minute, domain, variable.name, left, right, status, tuple(reasons)))
    return out


def _event_identity(event) -> dict:
    """What a replay artifact says about one mirrored action: its identity, never the resident's text."""
    receipt = dict(event.receipt or {})
    return {"order_id": event.order_id, "minute": event.minute, "kind": event.kind,
            "ledger_order_id": event.ledger_order_id, "submission_id": event.submission_id,
            "delivery_starts_at_min": receipt.get("delivery_starts_at_min"),
            "receipt_digest": (hashlib.sha256(json.dumps(receipt, sort_keys=True, default=str)
                                              .encode("utf-8")).hexdigest() if receipt else None)}


def _replay_trajectory(scenario: Mapping, minutes: int | None = None):
    """Deserialize an artifact's scenario and run it. The ONE place a captured input is replayed.

    ``ShadowPhysiologyRunner.advance`` is the live/incremental primitive; this is the from-artifact one,
    and nothing else in the layer calls ``integration.run``. Both readers of an artifact -- the replay and
    the non-authoritative diagnostics -- come through here, so there is no third way to advance a minute.
    """
    from clinical_core import integration
    anchors, contributors, captured_minutes, profile = integration.scenario_from_dict(scenario)
    return integration.run(anchors, contributors,
                           captured_minutes if minutes is None else minutes, profile), anchors, profile


def replay_shadow_encounter(data: Mapping | ShadowReplayInput) -> dict:
    """Deterministically replay a captured immutable input. Same input, same digests, always.

    ``results`` starts at minute 0, the arrival: a reader comparing it with a live record, which starts at
    minute 1, drops that first entry (``ShadowSession.replay`` does it for the live path).
    """
    payload = data.to_dict() if isinstance(data, ShadowReplayInput) else dict(data)
    trajectory, _anchors, _profile = _replay_trajectory(payload["scenario"])
    minutes = payload.get("minutes")
    derived = trajectory.derived()
    return {
        "case_id": payload.get("case_id"), "family": payload.get("family"),
        "snapshot": payload.get("snapshot"), "minutes": minutes,
        "results": [{"minute": index, "state_digest": rs._digest_of(state),
                     "derived": derived[index].to_dict()}
                    for index, state in enumerate(trajectory.states)],
        "final_digest": rs._digest_of(trajectory.states[-1]),
        "versions": payload.get("versions", {}),
    }


def replay_from_runner(runner: ShadowPhysiologyRunner) -> dict:
    captured = runner.replay_input()
    if captured is None:
        return {"results": [], "why": "the adapter could not map this arrival"}
    return replay_shadow_encounter(captured)


def family_matrix(point: str = COMMITTED) -> dict:
    """Which families can replay offline and which may run live, computed, never asserted."""
    from clinical_core import integration
    matrix = {}
    for family, adapter in sorted(ADAPTERS.items()):
        rows = {}
        for case in adapter.cases:
            runner = ShadowPhysiologyRunner.open(family, case, point=point)
            if runner is None:
                rows[case] = {"offline_replay": False, "why": "no adapter"}
                continue
            ok = runner.advance(10)
            rows[case] = {
                "offline_replay": bool(ok and runner.results),
                "live_shadow": bool(adapter.live),
                "failures": [item.classification for item in runner.failures],
                "treatments_mapped": list(adapter.maps),
                "treatment_gaps": sorted(adapter.gaps_declared),
                "snapshot": runner.snapshot_.id if runner.snapshot_ else None,
            }
        matrix[family] = rows
    return matrix


# -- P3-6: the region-aware ensemble -------------------------------------------------------------------------

#: The observables an envelope is built for: the ones the legacy engine also shows.
ENVELOPE_VARIABLES = ("sbp", "dbp", "map", "pulse_rate_bpm", "spo2", "respiratory_rate", "crt_s", "lactate")
WITHIN = "LEGACY_WITHIN_COMMON_REGION"
OUTSIDE = "LEGACY_OUTSIDE_COMMON_REGION"
REGION_DISABLED = "COMMON_REGION_DISABLED"


@dataclass(frozen=True)
class ShadowEnsembleResult:
    """One encounter run against several named witnesses, with the envelope they span."""

    case_id: str
    family: str
    points: tuple
    runs: Mapping[str, Any]
    envelope: Mapping[str, Any]
    snapshots: tuple

    def to_dict(self) -> dict:
        return {"case_id": self.case_id, "family": self.family, "points": list(self.points),
                "snapshots": [dict(item) for item in self.snapshots],
                "envelope": {name: {str(minute): list(values) for minute, values in rows.items()}
                             for name, rows in self.envelope.items()}}


def ensemble(family: str, case_id: str, minutes: int, *, points: Sequence[str] = POINTS,
             mirrored: Sequence = (), state: Mapping | None = None) -> ShadowEnsembleResult:
    """Run named, certified witnesses only. No cartesian product and no invented point.

    The resident actions are applied once by the legacy engine and mirrored once here: the ensemble repeats
    the *execution*, never the actions.
    """
    asked = tuple(dict.fromkeys(point for point in points if point in POINTS + (COMMITTED,)))
    if not asked:
        raise ValueError("an ensemble runs named, certified witnesses")
    if len(asked) > 4:
        raise ValueError("an ensemble runs at most four named witnesses (no parameter matrix)")
    runs, snapshots = {}, []
    for point in asked:
        runner = ShadowPhysiologyRunner.open(family, case_id, point=point, state=state)
        if runner is None:
            continue
        runner.mirror(mirrored)
        runner.advance(minutes, state=state)
        runs[point] = runner
        if runner.snapshot_ is not None:
            snapshots.append(runner.snapshot_.to_dict())
    envelope = {}
    for name in ENVELOPE_VARIABLES:
        rows = {}
        for minute in range(1, minutes + 1):
            values = [item.derived.get(name) for runner in runs.values() for item in runner.results
                      if item.minute == minute]
            numeric = [value for value in values if isinstance(value, (int, float))
                       and not isinstance(value, bool)]
            if numeric:
                rows[minute] = (min(numeric), max(numeric), _structural(runs, name, minute))
        envelope[name] = rows
    return ShadowEnsembleResult(case_id, family, asked, runs, envelope, tuple(snapshots))


def _structural(runs: Mapping[str, Any], name: str, minute: int):
    """The structural witness: the midpoint run, or the committed one where a family reads no band."""
    for point in ("midpoint", COMMITTED):
        runner = runs.get(point)
        if runner is None:
            continue
        for item in runner.results:
            if item.minute == minute:
                return item.derived.get(name)
    return None


def legacy_against_region(legacy: Mapping, result: ShadowEnsembleResult, minute: int) -> dict:
    """Where the legacy value sits with respect to the span of the NAMED witnesses of this run.

    Two cautions, and both are in the reading, not in a footnote:

    - ``LEGACY_WITHIN_COMMON_REGION`` is conservative and safe: the witnesses are corners of a declared
      region, so the true region is at least as wide and a value inside the witnesses' span is inside it.
    - ``LEGACY_OUTSIDE_COMMON_REGION`` is NOT the same statement. The span is the min/max of at most four
      named runs over a box of many magnitudes, so a value outside that span may still lie inside the
      declared region. Each reading therefore carries ``witnesses``, the number of runs it spans.

    And neither says the common core is right: the legacy engine is not clinical ground truth and no
    parameter in the region is approved.
    """
    pairs = {"sbp": "sbp", "dbp": "dbp", "map": "map", "hr": "pulse_rate_bpm", "spo2": "spo2",
             "respiratory_rate": "respiratory_rate", "crt": "crt_s"}
    out = {}
    for legacy_name, core_name in pairs.items():
        band = (result.envelope.get(core_name) or {}).get(minute)
        value = legacy.get(legacy_name)
        if band is None or value is None:
            out[legacy_name] = {"status": NOT_COMPARABLE}
            continue
        low, high, structural = band
        # A band of width zero is not a region, whatever the family or the variable: where the witnesses
        # coincide -- a held magnitude, or an observable none of them moves -- saying "the legacy value is
        # outside the common region" would dress a point as a region.
        if low == high and len(result.points) > 1:
            status = REGION_DISABLED
        elif low <= float(value) <= high:
            status = WITHIN
        else:
            status = OUTSIDE
        out[legacy_name] = {"status": status, "legacy": value, "region": [low, high],
                            "structural": structural, "witnesses": len(result.points)}
    return out


# -- P3-8: non-authoritative consciousness and collapse diagnostics ------------------------------------------

NONAUTHORITATIVE = "NONAUTHORITATIVE"


def shadow_diagnostics(runner: ShadowPhysiologyRunner, minute: int) -> dict:
    """The P2L-2 and P2M-2 candidates read on one shadow minute, as a diagnostic and nothing else.

    No category is emitted for consciousness (the mapping to an observed mental status is pending faculty),
    no collapse threshold is applied (the MAP mapping and the two limits are UNSET), nothing can arrest a
    patient and the resident keeps seeing the legacy engine's mental status.
    """
    from clinical_core import collapse as co, encephalopathy as en
    captured = runner.replay_input()
    if captured is None or minute < 1 or minute > runner.minutes_done:
        return {"authority": "none", "label": NONAUTHORITATIVE, "available": False,
                "why": "no mapped arrival, or the minute is outside the run"}
    trajectory, anchors, profile = _replay_trajectory(captured.scenario, minute)
    state = trajectory.states[minute]
    reading = en.readings(state, anchors, profile)
    signals = en.acute_signals(reading, en.DEFAULT_ENCEPHALOPATHY)
    stress = en.systemic_acute_brain_stress(dict(signals.values))
    primary = en.primary_neurologic_impairment(state.N)
    impairment = en.observable_impairment(primary, stress, 0.0)
    perfusion = co.perfusion_failure(trajectory.derived()[minute].map or 0.0, co.DEFAULT_COLLAPSE)
    return {
        "authority": "none",
        "label": NONAUTHORITATIVE,
        "available": True,
        "minute": minute,
        "consciousness": {
            "primary_neurologic_impairment": primary,
            "systemic_acute_brain_stress": stress,
            "systemic_encephalopathy_burden": 0.0,
            "observable_impairment": impairment,
            "mental_status_category": None,
            "category_status": en.STATUS["category"],
            "signal_readings": {name: reading.get(source[0]) for name, source in en.SIGNALS.items()},
            "signal_values": dict(signals.values),
            "signals_mapped": bool(en.DEFAULT_ENCEPHALOPATHY.mappings),
            "limitations": (en.STATUS["signals"], en.STATUS["memory"], en.STATUS["arrival"],
                            en.STATUS["availability"]),
            "signals_available": {name: value is not None for name, value in signals.values},
            "reading_note": "S is a LOWER BOUND, not a finding: no bound is committed, and without a "
                            "respiratory closure the acidemia and hypercapnia signals are structurally "
                            "unavailable. A stress of 0.0 means 'nothing measurable here', not 'no stress'.",
        },
        "collapse": {
            "perfusion_failure_signal": perfusion,
            "perfusion_mapping_status": co.STATUS["map_mapping"],
            # Through the Phase-2 helper, so its own scale guard applies instead of publishing a raw value.
            "oxygen_delivery_failure_signal": co.delivery_failure(reading["deficit_fraction"]),
            "delivery_status": co.STATUS["delivery_failure"],
            "collapse_burden": None,
            "burden_status": co.STATUS["burden_kinetics"],
            "terminal_transition": None,
            "terminal_status": (co.STATUS["terminal_burden"], co.STATUS["current_nonviability"],
                                co.STATUS["terminal_rhythm"]),
            "rosc": co.STATUS["rosc"],
        },
        "legacy_comparison": {
            "reading": "the legacy engine keeps deciding the mental status and the arrest; these are "
                       "candidate readings beside it, never instead of it",
        },
    }


# -- P3-9: the research trace --------------------------------------------------------------------------------

#: The keys a shadow trace shares with the project's management-reasoning trace. The shadow never writes into
#: that trace: these are what a faculty or research reader joins on, afterwards.
JOIN_KEYS = ("minute", "order_id", "submission_id", "state_digest")


def research_trace(runner: ShadowPhysiologyRunner, *, verbose: bool = False) -> dict:
    """The minimum per-minute trace, or the verbose debug one. Faculty and research only."""
    by_minute = {}
    for item in runner.divergences:
        by_minute.setdefault(item.minute, []).append(item)
    rows = []
    for item in runner.results:
        row = {"minute": item.minute, "state_digest": item.state_digest,
               "divergences": [{"domain": d.domain, "variable": d.variable, "status": d.status,
                                "legacy": d.legacy, "core": d.core, "reasons": list(d.reasons)}
                               for d in by_minute.get(item.minute, ())]}
        if verbose:
            row["derived"] = dict(item.derived)
        rows.append(row)
    captured = runner.replay_input()
    return {
        "artifact": "phase3_shadow_research_trace",
        "verbose": bool(verbose),
        "runtime_authority": "legacy",
        "resident_visible": False,
        "case_id": runner.case_id,
        "family": runner.adapter.family,
        "adapter": runner.adapter.version,
        "snapshot": runner.snapshot_.to_dict() if runner.snapshot_ else {},
        "join_keys": list(JOIN_KEYS),
        "actions": [{"shadow_order_id": event.order_id, "minute": event.minute, "kind": event.kind,
                     "order_id": event.ledger_order_id, "submission_id": event.submission_id}
                    for event in runner.mirrored],
        "rows": rows,
        "failures": [vars(item) for item in runner.failures],
        "gaps": list(runner.gaps),
        "versions": dict(captured.versions) if captured else {},
        "replay_digest": captured.digest() if captured else None,
        "summary": difference_summary(runner),
    }


def difference_summary(runner: ShadowPhysiologyRunner) -> dict:
    """What a faculty reader needs in one screen. No claim that either engine is clinically right."""
    counts, domains = {}, {}
    for item in runner.divergences:
        counts[item.status] = counts.get(item.status, 0) + 1
        domains.setdefault(item.domain, set()).add(item.status)
    return {
        "minutes": len(runner.results),
        "compared_minutes": len({item.minute for item in runner.divergences}),
        "by_status": dict(sorted(counts.items())),
        "by_domain": {domain: sorted(statuses) for domain, statuses in sorted(domains.items())},
        "boundaries": [vars(item) for item in runner.failures if item.classification == BOUNDARY],
        "unsupported_actions": sorted({str(gap.get("kind")) for gap in runner.gaps}),
        "parameter_uncertainty": (list(runner.snapshot_.provenance) if runner.snapshot_ else []),
        "reading": "a divergence is a difference between two architectures, not an error of either; the "
                   "legacy engine is not clinical ground truth and no common parameter here is approved",
    }


def artifact_sizes(runner: ShadowPhysiologyRunner) -> dict:
    """What each artifact costs, so a default is chosen with evidence instead of taste."""
    minimal = research_trace(runner)
    verbose = research_trace(runner, verbose=True)
    captured = runner.replay_input()
    return {
        "minutes": len(runner.results),
        "replay_input_bytes": len(json.dumps(captured.to_dict(), default=str)) if captured else 0,
        "minimal_trace_bytes": len(json.dumps(minimal, default=str)),
        "verbose_trace_bytes": len(json.dumps(verbose, default=str)),
        "recommended_default": "minimal_trace",
        "why": "the verbose trace keeps every derived value of every minute; the minimal one keeps the "
               "digest, the divergences and the replay input, which reproduces everything else exactly",
    }
