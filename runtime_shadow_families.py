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
#: Un solo texto para el hueco de soporte ventilatorio, que tres familias declaran igual.
NIV_GAP = "NIV, bag-mask and intubation have no core target (P2K-3 recruitment is off)"

#: P3-122: why ACS is not in the live-family list yet. Not a treatment gap: an ARRIVAL MAPPING gap.
ACS_LIVE_GAP = (
    "ACS_LIVE_MANAGEMENT_SHADOW_BLOCKED_BY_ARRIVAL_MAPPING: the ACS adapter's treatment semantics are "
    "ready for a live encounter -- oxygen is mapped, and reperfusion is built from the engine's own "
    "reperfusion_at, never from the referral's minute -- but its anchors() ignores the encounter state "
    "and returns a fixed Phase-2 reference arrival, where the GI adapter maps the arrival it is given. "
    "Live, this family would compute a reference patient's trajectory and label it this patient's, and "
    "the engine authors more ACS variants than the single case this adapter declares. Closing this needs "
    "a certified ACS arrival mapping, which is a methodological decision and not a wiring change."
)
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

    def arrival_identity(self, anchors, state: Mapping) -> list:
        """The family's OWN certified arrival identity requirements, beyond the shared ARRIVAL_ELIGIBLE rule
        (``runtime_shadow.arrival_eligibility``): [(name, live, certified)] for each difference. None by
        default: a family whose certified mapping reads the live state (GI) needs nothing more than the
        shared rule. A family whose mapping reads the authored case must prove the live case is that one."""
        return []

    def region_witnesses(self) -> dict:
        """Name -> a development adapter for each witness of a declared DEVELOPMENT TEST REGION this family
        runs LIVE as an ensemble (P3-140). Empty for a family that declares none, which is every family but
        the opioid one: the registered adapter itself never carries a witness."""
        return {}

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        """(contributors, gaps): only actions the engine already executed, each mapped once or declared.

        P3-141 corrected a silent drop here. An adapter that lists ``oxygen`` in ``maps`` and inherits this
        method used to get NO contributor for it: the order was neither applied nor declared as a gap, so
        three families (oedema, embolism, asthma) said oxygen was mapped while their shadow ignored it.
        Oxygen is the one intervention every family maps the same way, through the common oxygenation path,
        so it is built here; a kind in ``maps`` this method cannot build is declared, never dropped.
        """
        from clinical_core.interventions.oxygen import Oxygen
        built, gaps = [], []
        for event in mirrored:
            if event.kind == "oxygen" and "oxygen" in self.maps:
                built.append(Oxygen(event.order_id, event.minute, event.fio2_after))
            elif event.kind in self.maps:
                gaps.append({"kind": event.kind, "order_id": event.order_id,
                             "why": f"{event.kind} is listed as mapped but this adapter builds no contributor "
                                    "for it"})
            else:
                gaps.append({"kind": event.kind, "order_id": event.order_id,
                             "why": self.gaps_declared.get(event.kind,
                                                           "no core intervention for this order type")})
        return tuple(built), gaps


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
    version = "acs_ischaemia/P3-122"
    cases = ("acs_70f_left_main",)
    #: P3-122 AUDITED AND REFUSED. The action semantics suffice (oxygen is mapped; reperfusion is mapped
    #: off the engine's own door-to-balloon clock), but the ARRIVAL does not: ``anchors`` below ignores
    #: ``state`` and returns a fixed Phase-2 reference, while the GI adapter maps the encounter's own
    #: arrival. Live, this family would model a reference patient and not the one being treated, and the
    #: engine authors more ACS variants than the one case declared here. See ACS_LIVE_GAP.
    live = False
    maps = ("oxygen",)
    #: The order that asks for reperfusion: represented, but on the engine's clock, not the order's minute.
    REPERFUSION_ORDER = "reperfusion_referral"
    gaps_declared = {"fluid": "no certified ACS fluid mapping in the shadow adapter",
                     "aspirin": "antiplatelet has no ACS core target",
                     "p2y12": "antiplatelet has no ACS core target",
                     "anticoagulation": "anticoagulation has no ACS core target",
                     "nitroglycerin": "nitrate has no ACS core target",
                     "nitroglycerin_bolus": "nitrate has no ACS core target",
                     "opioid_analgesia": "opiate analgesia has no ACS core target"}

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

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        """Oxygen, plus the reperfusion the engine already timed. Everything else stays a declared gap.

        The minute the artery opens is NOT read from the order. The engine owns the door-to-balloon clock
        in `family_state` (`acs_reperfusion.py`), so this mirrors the engine's own bookkeeping, exactly as
        the GI adapter mirrors `endoscopy_at`, and the latency is the engine's, never one invented here.

        P3-122 corrected a false gap here. `reperfusion_referral` is NOT in `NOT_PHYSIOLOGICAL` (that set
        is reassessment, consult and diagnostic): the order HAS a physiological consequence, it simply
        arrives on the engine's clock rather than at the order's minute. Recording it as a gap would claim
        the cath lab reached nothing. So it is a gap only when the engine timed no reperfusion for it.
        """
        from clinical_core.interventions.oxygen import Oxygen
        from clinical_core.modules.acs_ischaemia import CoronaryReperfusion
        from clinical_core import legacy_adapter
        built, gaps = [], []
        opens_at = (state or {}).get("family_state", {}).get("reperfusion_at") if state else None
        for event in mirrored:
            if event.kind == "oxygen":
                built.append(Oxygen(event.order_id, event.minute, event.fio2_after))
            elif event.kind in legacy_adapter.NOT_PHYSIOLOGICAL:
                continue
            elif event.kind == self.REPERFUSION_ORDER:
                if opens_at is None:
                    gaps.append({"order_id": event.order_id, "kind": event.kind,
                                 "why": "the engine timed no reperfusion for this referral, so the core "
                                        "has no minute at which the artery opens"})
            else:
                gaps.append({"order_id": event.order_id, "kind": event.kind,
                             "why": self.gaps_declared.get(event.kind,
                                                           "no core intervention for this order type")})
        if opens_at is not None:
            built.append(CoronaryReperfusion("acs-pci", int(opens_at)))
        return tuple(built), gaps


#: P3-141, DEVELOPMENT TEST REGION for the oedema family's decongestion rate (lung water removed per simulated
#: minute once a decongestive treatment has begun). It is the family's OWN declared lung-water rate span
#: (``edema_migration.PROGRESSION``), whose midpoint is the only decongestion rate the repository states
#: (``edema_migration.DECONGESTION``, SYNTHETIC_ONLY). It is a software test region: not a dose, not a drug
#: effect size, not approved, and not clinical truth. The three witnesses exist only to test with, and
#: CENTER_REFERENCE is not a preferred value. See management_generalization_record.DECONGESTION_DECISION.
EDEMA_DECONGESTION_WITNESSES = {"LOW": 0.0025, "CENTER_REFERENCE": 0.005, "HIGH": 0.01}
EDEMA_DECONGESTION_REGION = (EDEMA_DECONGESTION_WITNESSES["LOW"], EDEMA_DECONGESTION_WITNESSES["HIGH"])


class PulmonaryEdemaAdapter(RuntimeFamilyAdapter):
    """Pulmonary oedema: the lung-water owner of P2P-1.

    The REGISTERED adapter (``ADAPTERS``) is built with no decongestion rate: nitrate and diuresis stay
    declared treatment gaps, exactly as before, because no rate is authored and the committed point invents
    none. ``development(witness)`` returns a separate, offline adapter built with one witness of the
    declared DEVELOPMENT TEST REGION; only that one maps the decongestive orders to the certified
    ``DecongestiveTreatment``. NIV stays a gap in both.
    """

    family = "pulmonary_edema"
    version = "pulmonary_edema/P3-141"
    cases = ("pulmonary_edema_58m",)
    live = False
    maps = ("oxygen",)
    #: The engine's action kinds that are a decongestive therapy.
    DECONGESTIVE_ORDERS = ("diuretic", "nitroglycerin", "nitroglycerin_bolus")
    #: The witness this adapter was built with (None: the registered adapter, no decongestion rate).
    decongestion_witness: str | None = None

    @classmethod
    def development(cls, witness: str) -> "PulmonaryEdemaAdapter":
        """An offline adapter carrying one witness of the decongestion DEVELOPMENT TEST REGION."""
        if witness not in EDEMA_DECONGESTION_WITNESSES:
            raise ValueError(f"unknown decongestion witness {witness!r}: {sorted(EDEMA_DECONGESTION_WITNESSES)}")
        adapter = cls()
        adapter.decongestion_witness = witness
        adapter.maps = ("oxygen",) + cls.DECONGESTIVE_ORDERS
        adapter.live = False
        return adapter

    @property
    def decongestion_per_min(self) -> float:
        return 0.0 if self.decongestion_witness is None else EDEMA_DECONGESTION_WITNESSES[self.decongestion_witness]
    #: Re-keyed in P3-108 to the engine's own action kinds: a gap declared under a key no event carries
    #: can never fire, so its declared reason never reached the record (the generic default did).
    gaps_declared = {"diuretic": "the decongestive writer is a construction parameter of EdemaCongestion, "
                                 "not a mapped runtime action",
                     "nitroglycerin": "the decongestive writer is a construction parameter of "
                                      "EdemaCongestion, not a mapped runtime action",
                     "nitroglycerin_bolus": "the decongestive writer is a construction parameter of "
                                            "EdemaCongestion, not a mapped runtime action",
                     "niv": NIV_GAP, "bag_mask": NIV_GAP, "intubation": NIV_GAP}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import edema_migration as em
        index = _point_index(point, em.PROGRESSION)
        provenance = (f"clinical_core.edema_migration.PROGRESSION[{index}] = {em.PROGRESSION[index]}",
                      f"clinical_core.edema_reference.anchors(point={point if point in POINTS else 'midpoint'!r})")
        if self.decongestion_witness is None:
            return ShadowParameterSnapshot(f"edema_{point}", self.family,
                                           point if point in POINTS else COMMITTED, provenance)
        return ShadowParameterSnapshot(
            f"edema_{point}_decongestion_{self.decongestion_witness.lower()}", self.family,
            point if point in POINTS else COMMITTED,
            provenance + (f"runtime_shadow_families.EDEMA_DECONGESTION_WITNESSES[{self.decongestion_witness!r}] = "
                          f"{self.decongestion_per_min} per minute: DEVELOPMENT_TEST_REGION "
                          f"{EDEMA_DECONGESTION_REGION}, a test witness, not a selection and not approved",))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        from clinical_core import edema_reference
        return edema_reference.anchors(point if point in POINTS else "midpoint")

    def profile(self, point: str):
        from clinical_core import edema_migration
        return edema_migration.profile()

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import edema_migration as em
        return (em.writer(em.PROGRESSION[_point_index(point, em.PROGRESSION)], self.decongestion_per_min),)

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        """Oxygen always; the decongestive treatment only on a development adapter.

        ``DecongestiveTreatment`` is P2P-1's certified contributor: it publishes the moment the therapy begins
        and writes NOTHING. The family writer hears it, stops progressing and removes lung water at its rate,
        never below the arrival congestion; gas exchange, SpO2 and the rest follow in the common core. So
        there is no write to SpO2 here, and oxygen never touches L. One therapy begins once: a second
        decongestive order is the same treatment already running, recorded as such and not built twice.
        """
        from clinical_core.interventions.oxygen import Oxygen
        from clinical_core.modules.pulmonary_edema import DecongestiveTreatment
        built, gaps, begun = [], [], None
        for event in sorted(mirrored, key=lambda item: (item.minute, item.order_id)):
            if event.kind == "oxygen":
                built.append(Oxygen(event.order_id, event.minute, event.fio2_after))
            elif event.kind in self.DECONGESTIVE_ORDERS and self.decongestion_witness is not None:
                if begun is None:
                    begun = event
                    # P3-152: an order the engine executed at minute m is first present in the state of
                    # minute m + 1 -- the layer's one timing rule, the same as oxygen above and as the live
                    # opioid path. The treatment acts in the minute it begins, so it begins one minute after
                    # the order. (Until P3-152 this adapter dated it at the order's own minute, one minute
                    # earlier than every other mapped order; the magnitude region is untouched.)
                    built.append(DecongestiveTreatment(event.order_id, int(event.minute) + 1))
                else:
                    gaps.append({"kind": event.kind, "order_id": event.order_id,
                                 "why": f"decongestion already begun by {begun.order_id} at minute "
                                        f"{begun.minute}: the family writer has one rate, so a second "
                                        "decongestive order adds nothing in this model"})
            else:
                gaps.append({"kind": event.kind, "order_id": event.order_id,
                             "why": self.gaps_declared.get(event.kind,
                                                           "no core intervention for this order type")})
        return tuple(built), gaps


class PulmonaryEmbolismAdapter(RuntimeFamilyAdapter):
    """PE: obstruction on P, direct G and the zero-lung-water owner of P2Q-2. No treatment is modelled."""

    family = "pulmonary_embolism"
    version = "pulmonary_embolism/P3-141"
    cases = ("pulmonary_embolism_61m", "pulmonary_embolism_33f")
    live = False
    maps = ("oxygen",)
    gaps_declared = {"anticoagulation": "anticoagulation is not modelled (P2Q-2 declares it): the PE "
                                        "writer takes no treatment parameter",
                     "thrombolysis": "thrombolysis is not modelled (P2Q-2 declares it): the PE writer "
                                     "takes no treatment parameter",
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
    version = "asthma/P3-141"
    cases = ("asthma_49m", "asthma_24f")
    live = False
    maps = ("oxygen",)
    gaps_declared = {"bronchodilator": "BRONCHODILATOR_WRITER_DEFERRED "
                                       "(clinical_core.modules.asthma declares it)",
                     "continuous_bronchodilator": "BRONCHODILATOR_WRITER_DEFERRED "
                                                  "(clinical_core.modules.asthma declares it)",
                     "steroid": "STEROID_ACUTE_PHYSIOLOGY_DEFERRED "
                                "(clinical_core.modules.asthma declares it)",
                     "niv": NIV_GAP, "bag_mask": NIV_GAP, "intubation": NIV_GAP}

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


#: P3-140, the hypoventilation -> oxygenation transmission of PHASE2_AMENDMENT_1, as the faculty approved it
#: for DEVELOPMENT on 2026-11-10 (FD-P3-129). Two regions, and they are not the same statement:
#:
#: - the MATHEMATICAL region is closed, [0, 0.060621]: every fraction the development target admits, with the
#:   respiratory quotient DECLARED at 0.8 for this analysis (only fraction / quotient is identified);
#: - the ACTIVE CAUSAL region is open below, (0, 0.060621]: a fraction of 0 is the negative control. It
#:   belongs to the representable region and it expresses nothing downstream of PaCO2, so it cannot show
#:   the chain ventilation -> PaCO2 -> oxygenation and is never an ensemble witness.
#:
#: The three witnesses exist ONLY to run a development ensemble and to test with. CENTER_REFERENCE is not a
#: preferred value, no committed profile adopts any of them, and nothing here is clinical truth.
TRANSMISSION_FIELD = "hypoventilation_oxygenation_transmission_fraction"
TRANSMISSION_DECLARED_R = 0.8
TRANSMISSION_MATHEMATICAL_REGION = (0.0, 0.060621)
TRANSMISSION_ACTIVE_REGION = {"above": 0.0, "up_to": 0.060621, "zero_is": "NEGATIVE_CONTROL_NOT_A_WITNESS"}
TRANSMISSION_WITNESSES = {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06}
TRANSMISSION_CLASSIFICATION = "DEVELOPMENT_TEST_REGION"


class ArrivalIdentityError(ValueError):
    """The live arrival is not the authored case the certified reference mapping was built for."""


class OpioidAdapter(RuntimeFamilyAdapter):
    """Opioid: central depression and its reversal (P2U-1), each a committed point, not a span.

    Since P3-141 (second live-shadow family, FD-P3-131) this adapter may run inside a live encounter, with
    no authority. Three things make that honest, and each is checked rather than assumed:

    - the ARRIVAL. The engine authors two opioid variants and this adapter certifies exactly those two. Its
      anchors are P2U-1's certified reference mapping of the AUTHORED case, so a live run is only this
      patient's if the live arrival IS that authored case: ``arrival_identity`` compares every authored
      input the mapping reads with the live state, and a single difference refuses the run, visibly. No
      value is derived from the live state by a new rule;
    - the TIME. An order the engine executed at minute m is first present in the state of minute m + 1
      (the state of minute m existed, and was shown, before the order). Oxygen already behaved so; the
      reversal is now mapped the same way, which is also what keeps a late order from rewriting minutes the
      shadow had already recorded;
    - the PARAMETER. The registered adapter keeps the committed profile, where the transmission link is
      not declared. The development witnesses of the transmission region run beside it as an ENSEMBLE
      (``region_witnesses``), each kept apart, none selected.
    """

    family = "opioid"
    version = "opioid/P3-141L"
    cases = ("opioid_35m", "opioid_67f")
    live = True
    maps = ("oxygen", "naloxone")
    gaps_declared = {"bag_mask": "bag-mask has no core target (P2K-3 recruitment is off)",
                     "niv": "NIV has no core target (P2K-3 recruitment is off)",
                     "intubation": "intubation has no core target (P2K-3 recruitment is off)",
                     "opioid_analgesia": "more opioid has no runtime-mapped deepening writer",
                     "naloxone_infusion": "a naloxone infusion has no core contributor: the certified reversal "
                                          "is one signal with one committed rate"}
    #: What a mapped action carries that the core contributor does not read. Declared, never silent.
    NOT_READ = {"naloxone": ("dose_mg", "route")}
    #: The witness this adapter was built with (None: the registered adapter, the committed profile).
    transmission_witness: str | None = None

    @classmethod
    def witness(cls, name: str) -> "OpioidAdapter":
        """A development adapter carrying ONE witness of the transmission region. Never registered."""
        if name not in TRANSMISSION_WITNESSES:
            raise ValueError(f"unknown transmission witness {name!r}: {sorted(TRANSMISSION_WITNESSES)}")
        adapter = cls()
        adapter.transmission_witness = name
        return adapter

    def region_witnesses(self) -> dict:
        """The live ensemble of the registered adapter: every witness, in declared order. A witness adapter
        declares none of its own, so an ensemble never nests."""
        if self.transmission_witness is not None:
            return {}
        return {name: type(self).witness(name) for name in TRANSMISSION_WITNESSES}

    def snapshot(self, point: str = COMMITTED) -> ShadowParameterSnapshot:
        from clinical_core import opioid_migration as om
        provenance = (f"clinical_core.opioid_migration.DEEPENING_PER_MIN = {om.DEEPENING_PER_MIN} "
                      "(a committed point, no span is declared)",
                      f"clinical_core.opioid_reference.anchors(point='midpoint')")
        if self.transmission_witness is None:
            return ShadowParameterSnapshot(f"opioid_{point}", self.family, COMMITTED, provenance)
        name = self.transmission_witness
        return ShadowParameterSnapshot(
            f"opioid_{point}_transmission_{name.lower()}", self.family, COMMITTED,
            provenance + (
                f"runtime_shadow_families.TRANSMISSION_WITNESSES[{name!r}] = {TRANSMISSION_WITNESSES[name]}: "
                f"{TRANSMISSION_CLASSIFICATION}, active region ({TRANSMISSION_ACTIVE_REGION['above']}, "
                f"{TRANSMISSION_ACTIVE_REGION['up_to']}], a development witness, not a selection and not "
                "clinical truth",
                f"respiratory_quotient = {TRANSMISSION_DECLARED_R}, DECLARED for this development analysis "
                "(only fraction / quotient is identified)",
                f"clinical_core.opioid_migration.NALOXONE['recovery_per_min'] = "
                f"{om.NALOXONE['recovery_per_min']} (SYNTHETIC_ONLY: the order's dose and route are not read)"))

    def anchors(self, case_id: str, point: str, state: Mapping | None = None):
        """P2U-1's certified reference arrival; with a live arrival, only after its identity is checked."""
        from clinical_core import opioid_reference
        anchors = opioid_reference.anchors(case_id, point if point in POINTS else "midpoint")
        if state is not None:
            try:
                differences = self.arrival_identity(anchors, state)
            except Exception as error:
                # A state the check cannot even read is not the authored arrival either: refused, by name.
                raise ArrivalIdentityError("the live arrival could not be compared with the authored case: "
                                           f"{type(error).__name__}: {str(error)[:160]}") from error
            if differences:
                raise ArrivalIdentityError(
                    "the live arrival is not the authored case the certified opioid mapping reads: "
                    + "; ".join(f"{name} live {live!r} / certified {certified!r}"
                                for name, live, certified in differences[:8])
                    + (f"; and {len(differences) - 8} more" if len(differences) > 8 else ""))
        return anchors

    #: The authored items ``opioid_reference.anchors`` reads from the case, by their name in its truth table.
    AUTHORED_ITEMS = ("sbp", "dbp", "hr", "rhythm", "spo2", "respiratory_rate", "crt_s", "mental_status",
                      "glucose_mg_dl", "lactate_mmol_l", "hb_g_dl", "potassium_mmol_l", "abg_paco2", "abg_hco3",
                      "abg_fio2_percent")
    #: The same arrival as the monitor shows it: authored item -> key of the live ``observable``.
    SHOWN_ITEMS = {"sbp": "sbp", "dbp": "dbp", "hr": "hr", "rhythm": "rhythm", "spo2": "spo2",
                   "respiratory_rate": "respiratory_rate", "crt_s": "crt", "mental_status": "mental_status",
                   "glucose_mg_dl": "glucose_mg_dl"}

    @staticmethod
    def arrival_identity(anchors, state: Mapping) -> list:
        """Whether the live state IS the untouched authored arrival the certified mapping reads:
        [(name, live, certified)] for every difference, empty when it is.

        Classified by the faculty (2026-11-10) as a LIVE_SHADOW_ELIGIBILITY_GUARD, not as new clinical
        mapping semantics: it transforms and infers nothing, and only permits the existing certified P2U-1
        mapping while the runtime state still is the authored arrival. Two layers:

        - the SHARED rule, the same for every live family (``runtime_shadow.arrival_eligibility``, P3-147):
          the clock at 0, the engine's state a fresh arrival's field by field, the monitor showing the
          authored arrival, nothing administered, nothing on the diagnostic record;
        - this family's OWN requirement: its mapping reads the BANK case, so every authored value it reads
          must be the same in the live state's own case, and what it takes from the engine's state must
          equal the anchors.

        A comparison and nothing else. Everything is read on copies, through the engine's own initializer.
        """
        from clinical_core import legacy_adapter, opioid_reference
        import family_engine
        differences = []

        def compare(name, live, certified):
            try:
                same = live is not None and (live == certified if isinstance(certified, (str, bool, list, dict))
                                             or certified is None else float(live) == float(certified))
            except (TypeError, ValueError):
                same = False
            if not same and not (live is None and certified is None):
                differences.append((name, live, certified))

        source = legacy_adapter._initialized(state)
        case_id = str(legacy_adapter.engine_case_id(source))
        compare("case_id", case_id, str(anchors.case_id))
        if case_id != str(anchors.case_id):
            return differences
        # the shared rule first: one implementation, the one the session itself applies to every family
        differences.extend(rs.arrival_eligibility(state)["differences"])
        # the case: the live state's own copy of it against the bank case the certified mapping read
        live_case, certified = family_engine._case(source), opioid_reference.truth(case_id)
        for item in OpioidAdapter.AUTHORED_ITEMS:
            value = live_case
            try:
                for key in opioid_reference.TRUTH_PATHS[item]:
                    value = value[key]
            except (KeyError, TypeError):
                value = None
            compare(f"case.{item}", value, certified[item])
        # and what the mapping takes from the engine's state, against the anchors themselves
        live_state = source.get("family_state") or {}
        compare("lactate", live_state.get("lactate"), anchors.lactate)
        compare("hb", live_state.get("hemoglobin"), anchors.hb)
        compare("fio2", live_state.get("oxygen_fio2"), anchors.fio2)
        return differences

    def profile(self, point: str):
        """The committed opioid profile; on a witness adapter, that profile with the link declared and ONE
        fraction. Nothing else differs between two witnesses, and the committed profile is never changed."""
        from clinical_core import opioid_migration
        committed = opioid_migration.profile()
        if self.transmission_witness is None:
            return committed
        import dataclasses
        return dataclasses.replace(committed, respiratory_quotient=TRANSMISSION_DECLARED_R,
                                   **{TRANSMISSION_FIELD: TRANSMISSION_WITNESSES[self.transmission_witness]})

    def writers(self, case_id: str, point: str, state: Mapping | None = None) -> tuple:
        from clinical_core import opioid_migration as om
        return (om.depression(),)

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        """Oxygen and naloxone. Naloxone is already a certified core contributor (P2U-1).

        Naloxone restores the CENTRAL AVAILABILITY and nothing else: it never writes RR, PaCO2, SpO2 or
        mental status, which reach the reading only as downstream consequences. Its rate is the committed
        one of `opioid_migration.NALOXONE`, declared SYNTHETIC_ONLY there; this mapping does not choose it.
        Oxygen acts only through the oxygenation path, so it CANNOT correct central hypoventilation -- the
        educational distinction this family exists to teach.

        P3-141, the time of the reversal. ``event.minute`` is the engine's minute when it executed the
        order, and the state of that minute already existed. The certified contributor acts IN its start
        minute, so it starts at ``event.minute + 1``: the first state that can carry the effect, exactly
        where oxygen's lands. Mapped at ``event.minute`` it changed a minute the shadow had already
        recorded, and a late order made the live run and its own replay disagree.

        One reversal begins once. The certified contributor is one signal with one committed rate, so a
        repeat dose is the same reversal already running: it is declared as such and never built twice
        (two would share a source and the core refuses the run). The order's dose and route are not read.
        """
        from clinical_core.interventions.oxygen import Oxygen
        from clinical_core import opioid_migration as om
        from clinical_core import legacy_adapter
        built, gaps, begun = [], [], None
        # A stable sort by minute: the first reversal is the EARLIEST one, and the order inside a turn is kept.
        for event in sorted(mirrored, key=lambda item: item.minute):
            if event.kind == "oxygen":
                built.append(Oxygen(event.order_id, event.minute, event.fio2_after))
            elif event.kind == "naloxone":
                if begun is None:
                    begun = event
                    built.append(om.naloxone(start=int(event.minute) + 1))
                else:
                    gaps.append({"order_id": event.order_id, "kind": event.kind,
                                 "why": f"the reversal already began with {begun.order_id} at minute "
                                        f"{begun.minute}: the certified contributor has one committed rate, "
                                        "so a repeat dose adds nothing in this model"})
            elif event.kind in legacy_adapter.NOT_PHYSIOLOGICAL:
                continue
            else:
                gaps.append({"order_id": event.order_id, "kind": event.kind,
                             "why": self.gaps_declared.get(event.kind,
                                                           "no core intervention for this order type")})
        return tuple(built), gaps


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
             scenario_id: str | None = None, adapter: RuntimeFamilyAdapter | None = None):
        """Build a runner, or None when no adapter certifies this family and case.

        ``adapter`` is given only for a region witness (P3-140): a development adapter of the SAME family,
        which the registry never holds. Anything else is refused, so a caller cannot run one family's
        arrival through another family's mapping.
        """
        if adapter is None:
            adapter = adapter_for(family)
        elif adapter.family != str(family or ""):
            return None
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
        recorded = next((item for item in reversed(self.results) if item.minute == self.minutes_done), None)
        if recorded is not None and rs._digest_of(trajectory.states[self.minutes_done]) != recorded.state_digest:
            # P3-141: every advance recomputes from arrival, so a contributor that acts at or before a minute
            # this run already recorded REWRITES it: the record would keep the old minute, a replay would
            # compute the new one, and the two would silently disagree. That is a mapping fault (an order's
            # effect dated before the state it was ordered from). It is refused here, loudly, and the run
            # stops where its record is still true.
            self.failures.append(rs.ShadowFailure(
                minute, "history", "HistoryRewritten",
                f"the contributors mirrored by minute {minute} change minute {self.minutes_done}, which this "
                "run had already recorded; nothing after it is recorded", UNEXPECTED))
            return False
        derived = trajectory.derived()
        fresh = [ShadowMinuteResult(index, rs._digest_of(trajectory.states[index]), derived[index].to_dict())
                 for index in range(self.minutes_done + 1, minute + 1)]
        # The minutes and the clock move together (the independent review of P3-141 found them apart: a
        # comparison that raised left minutes recorded and the clock behind, so the next advance recorded
        # them twice -- or, with the history guard, refused a run nothing had rewritten).
        self.results.extend(fresh)
        self.minutes_done = minute
        if legacy is not None and minute > 0:
            # A turn that advanced no minute still has a legacy truth for it: the comparison of that minute
            # is REPLACED, so the record keeps one comparison per minute -- the latest -- and never two.
            try:
                compared = divergence_records(minute, legacy, trajectory.states[minute], derived[minute],
                                              self.adapter.family)
            except Exception as error:
                # The minute ran; only its comparison could not be built. It stays recorded as NOT compared.
                self.failures.append(rs._failure(minute, "compare", error, MAPPING_GAP))
                return True
            self.divergences = [item for item in self.divergences if item.minute != minute]
            self.divergences.extend(compared)
            if minute not in self.compared:
                self.compared.append(minute)
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


def reading_digest(derived: Mapping) -> str:
    """The digest of one minute's derived readings. Two runs whose STATES coincide can still read differently
    (a profile field that only a reading uses), and then only this tells them apart."""
    return hashlib.sha256(json.dumps(dict(derived), sort_keys=True, default=str).encode("utf-8")).hexdigest()


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


# -- P3-140: the live region ensemble ------------------------------------------------------------------------

#: The readings an ensemble's derived view spans. A view, computed from the witnesses; never a trajectory.
ENSEMBLE_VIEW = ("respiratory_rate", "spo2", "delivery_rel")
ENSEMBLE_POLICY = ("every witness is kept as its own trajectory; none is selected, preferred or averaged; "
                   "the session's own run is the committed profile, where the link is not declared")


@dataclass
class RegionEnsemble:
    """One live encounter run against EVERY witness of a declared development region, beside the session.

    Each witness is its own ``ShadowPhysiologyRunner``, opened on the same arrival, fed the same mirrored
    actions and advanced to the same minute, through the one execution primitive. Two witnesses differ in
    the single profile field the region is about and in nothing else. The witnesses are never combined into
    one patient: the only derived reading is ``view``, a per-minute minimum and maximum beside the
    individual values, and it exists only where every witness has that minute.

    Research and development only, like everything in this layer: it reads copies, owns no runtime state,
    and nothing it produces is written to the patient, the ledger, the score or the resident's trace.
    """

    family: str
    case_id: str
    parameter: str
    runners: dict
    _drained: dict = field(default_factory=dict)
    #: Why no witness runs, when none does. Reported once as a failure and kept in the record.
    refused: str | None = None
    _refusal_reported: bool = False

    @classmethod
    def open(cls, family: str, case_id: str, *, state: Mapping | None = None,
             scenario_id: str | None = None) -> "RegionEnsemble | None":
        """The ensemble of this family's registered adapter, or None when it declares no live region.

        Fail closed on the core's lineage. The parameter a witness sets exists only in a certified
        successor of the Phase-2 closure, so the ensemble runs only while the live core IS a certified
        member of the lineage; otherwise no witness opens and the reason is recorded. A lineage that cannot
        be evaluated is a refusal too.
        """
        adapter = adapter_for(family)
        witnesses = {} if adapter is None else adapter.region_witnesses()
        if not witnesses:
            return None
        try:
            import runtime_shadow_evidence as evidence     # it imports this module: resolved at call time
            certified = evidence.core_lineage_ok()
            why = None if certified else (evidence.core_lineage_reason()
                                          or "the common core lineage could not be evaluated")
        except Exception as error:
            why = f"the common core lineage could not be evaluated: {type(error).__name__}"
        if why is not None:
            return cls(str(family), str(case_id), TRANSMISSION_FIELD, {}, refused=why)
        runners = {}
        for name, witness in witnesses.items():
            runner = ShadowPhysiologyRunner.open(family, case_id, state=state, adapter=witness,
                                                 scenario_id=(None if scenario_id is None
                                                              else f"{scenario_id}::{name}"))
            if runner is not None:
                runners[name] = runner
        return cls(str(family), str(case_id), TRANSMISSION_FIELD, runners)

    def advance(self, mirrored: Sequence, minute: int, state: Mapping | None = None) -> None:
        """Every witness to the same minute, on the same mirrored actions. Never raises: a witness that
        cannot run records why and stops; the others, and the encounter, go on."""
        for runner in self.runners.values():
            try:
                runner.mirror(mirrored)
                runner.advance(minute, state=state)
            except Exception as error:
                # P3-150: ``advance`` guards the core run itself; anything else that raises is THIS witness's
                # failure and nobody else's. Before this guard it left the loop, so the witnesses after it
                # did not run that turn and the failure was recorded against the session, not the witness.
                runner.failures.append(rs._failure(int(minute), "advance", error, UNEXPECTED))

    def new_failures(self) -> list:
        """The failures since the last call, each naming its witness. Nothing is repaired or replaced."""
        out = []
        if self.refused is not None and not self._refusal_reported:
            self._refusal_reported = True
            out.append(rs.ShadowFailure(0, "ensemble:lineage", "CoreLineageNotCertified", self.refused[:400],
                                        MAPPING_GAP))
        for name, runner in self.runners.items():
            seen = self._drained.get(name, 0)
            for item in runner.failures[seen:]:
                out.append(rs.ShadowFailure(item.minute, f"ensemble:{name}:{item.where}", item.exception,
                                            item.message, item.classification))
            self._drained[name] = len(runner.failures)
        return out

    def view(self) -> dict:
        """reading -> minute -> {"witnesses": {name: value}, "min": .., "max": ..}: a derived view.

        Only minutes EVERY witness has. No mean, no median and no representative value: a reader who wants
        a trajectory takes one witness, by name.
        """
        if not self.runners:
            return {}
        common = min(runner.minutes_done for runner in self.runners.values())
        out = {}
        for reading in ENSEMBLE_VIEW:
            rows = {}
            for minute in range(1, common + 1):
                values = {}
                for name, runner in self.runners.items():
                    item = runner.results[minute - 1] if minute - 1 < len(runner.results) else None
                    value = None if item is None else item.derived.get(reading)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        values[name] = float(value)
                if len(values) == len(self.runners):
                    rows[minute] = {"witnesses": values, "min": min(values.values()),
                                    "max": max(values.values())}
            out[reading] = rows
        return out

    def record(self) -> dict:
        """The ensemble as an artifact: each witness whole, then the derived view. Never authority."""
        witnesses = {}
        for name, runner in self.runners.items():
            # A witness whose mapping fails outright cannot rebuild its artifact either. That is recorded as
            # what it is; it never takes the record of the other witnesses, or of the session, down with it.
            try:
                captured, artifact_error = runner.replay_input(), None
            except Exception as error:
                captured, artifact_error = None, f"{type(error).__name__}: {str(error)[:200]}"
            witnesses[name] = {
                "value": TRANSMISSION_WITNESSES.get(name),
                "adapter": runner.adapter.version,
                "snapshot": runner.snapshot_.to_dict() if runner.snapshot_ else {},
                "minutes": self.minutes()[name],
                "failures": [vars(item) for item in runner.failures],
                "gaps": list(runner.gaps),
                "replay_input": None if captured is None else captured.to_dict(),
                "replay_digest": None if captured is None else captured.digest(),
                "artifact_error": artifact_error,
            }
        return {
            "runtime_authority": "legacy",
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "resident_visible": False,
            "family": self.family, "case_id": self.case_id,
            "parameter": self.parameter,
            "classification": TRANSMISSION_CLASSIFICATION,
            "mathematical_region": list(TRANSMISSION_MATHEMATICAL_REGION),
            "active_causal_region": dict(TRANSMISSION_ACTIVE_REGION),
            "declared_respiratory_quotient": TRANSMISSION_DECLARED_R,
            "policy": ENSEMBLE_POLICY,
            "selected_witness": None,
            "refused": self.refused,
            "witnesses": witnesses,
            "complete": all(runner.anchors is not None and not runner.failures
                            for runner in self.runners.values()) and bool(self.runners),
            "view": {reading: {str(minute): row for minute, row in rows.items()}
                     for reading, rows in self.view().items()},
        }

    def minutes(self) -> dict:
        """witness -> its recorded minutes: the state digest AND the digest of the readings. With oxygen on,
        every witness reaches the same states and differs only in what it reads, so a check on states alone
        could not tell a witness from another, or from the committed run."""
        return {name: [{"minute": item.minute, "state_digest": item.state_digest,
                        "reading_digest": reading_digest(item.derived)} for item in runner.results]
                for name, runner in self.runners.items()}

    def replay(self) -> dict:
        """Each witness replayed from its OWN immutable artifact, through the one replay function; the same
        rows ``minutes`` gives, so the two are compared whole."""
        out = {}
        for name, runner in self.runners.items():
            try:
                replayed = replay_from_runner(runner)
            except Exception:
                # No artifact, no replay: an empty list, which can never be mistaken for the recorded minutes.
                out[name] = []
                continue
            out[name] = [{"minute": item["minute"], "state_digest": item["state_digest"],
                          "reading_digest": reading_digest(item["derived"])}
                         for item in replayed.get("results", []) if item["minute"] >= 1]
        return out

    def digests(self) -> dict:
        return {name: runner.digests() for name, runner in self.runners.items()}


# -- P3-148 to P3-150: what a faculty reader is shown of a shadow session --------------------------------------

#: What became of one action the engine executed, as the shadow sees it. Every mirrored action has exactly
#: one; UNACCOUNTED is the layer's own detector of a silent drop -- a supported action that produced neither
#: a contributor nor a declared gap -- and is reported as an internal error, never ignored.
BUILT = "BUILT"
SKIPPED_NO_PHYSIOLOGY = "SKIPPED_NO_PHYSIOLOGY"
DECLARED_GAP = "DECLARED_GAP"
APPLIED_AS_A_STOP = "APPLIED_AS_A_STOP"
UNACCOUNTED = "UNACCOUNTED"
#: Two rows that are not mirrored actions, kept in the same timeline so that nothing the run carries, and
#: nothing it does not, is missing from it. FROM_ENGINE_STATE: a contributor the mapping built from the
#: engine's own state and not from an order (GI haemostasis, read from when the engine performed it).
#: NOT_MIRRORED: an order the session did not mirror at all -- one the engine holds until a result and may
#: execute later, or one whose receipt could not be placed. The shadow run does NOT carry it, and says so.
FROM_ENGINE_STATE = "FROM_ENGINE_STATE"
NOT_MIRRORED = "NOT_MIRRORED"
DISPOSITIONS = (BUILT, SKIPPED_NO_PHYSIOLOGY, DECLARED_GAP, APPLIED_AS_A_STOP, UNACCOUNTED, FROM_ENGINE_STATE,
                NOT_MIRRORED)
#: The dispositions of a MIRRORED action. Every mirrored action has exactly one of these.
MIRRORED_DISPOSITIONS = DISPOSITIONS[:5]


def action_dispositions(adapter: RuntimeFamilyAdapter, mirrored: Sequence, state: Mapping | None = None) -> list:
    """One row per mirrored action: its order minute, what the mapping did with it, and when it takes effect.

    ``effective_minute`` is the first shadow minute whose state can carry the action: the minute after the
    engine executed it (or after its delivery starts, where the engine's own receipt says it starts later).
    It is None for an action that builds nothing. Nothing here decides anything: the mapping is the
    adapter's, called once, and this only reads what it returned.
    """
    from clinical_core import legacy_adapter
    try:
        built, gaps = adapter.interventions(list(mirrored), state)
    except Exception as error:
        return [{"shadow_order_id": event.order_id, "order_minute": int(event.minute), "kind": event.kind,
                 "order_id": event.ledger_order_id, "submission_id": event.submission_id,
                 "disposition": UNACCOUNTED, "effective_minute": None,
                 "why": f"the mapping could not be evaluated: {type(error).__name__}"} for event in mirrored]
    built_ids = {str(item.id) for item in built if hasattr(item, "id")}
    gap_of = {str(gap.get("order_id")): str(gap.get("why") or "") for gap in gaps}
    reversal = next((type(item).__name__ for item in built if type(item).__name__ == "NaloxoneReversal"), None)
    first_reversal = next((event.order_id for event in sorted(mirrored, key=lambda item: item.minute)
                           if event.kind == "naloxone"), None)
    rows = []
    for event in mirrored:
        why, disposition, effective = "", UNACCOUNTED, None
        receipt = dict(event.receipt or {})
        begins = receipt.get("delivery_starts_at_min")
        after = int(event.minute if begins is None else max(float(event.minute), float(begins))) + 1
        if event.order_id in gap_of:
            disposition, why = DECLARED_GAP, gap_of[event.order_id]
        elif event.kind in legacy_adapter.NOT_PHYSIOLOGICAL:
            disposition, why = SKIPPED_NO_PHYSIOLOGY, "this order type carries no physiology in the core"
        elif event.kind == "fluid" and dict(event.action or {}).get("operation") == "stop":
            disposition, effective = APPLIED_AS_A_STOP, int(event.minute) + 1
            why = "closes the crystalloid running before it"
        elif event.order_id in built_ids or (reversal and event.order_id == first_reversal):
            disposition, effective = BUILT, after
        else:
            why = ("a supported action produced neither a contributor nor a declared gap: reported, "
                   "never dropped in silence")
        rows.append({"shadow_order_id": event.order_id, "order_minute": int(event.minute), "kind": event.kind,
                     "order_id": event.ledger_order_id, "submission_id": event.submission_id,
                     "disposition": disposition, "effective_minute": effective, "why": why})
    mirrored_ids = {event.order_id for event in mirrored}
    for item in built:
        # A contributor that no mirrored order explains: built from the engine's own state. It is in the run,
        # so it is in the timeline.
        if hasattr(item, "id") and str(item.id) not in mirrored_ids and type(item).__name__ != reversal:
            rows.append({"shadow_order_id": str(item.id), "order_minute": None, "kind": type(item).__name__,
                         "order_id": None, "submission_id": None, "disposition": FROM_ENGINE_STATE,
                         "effective_minute": None,
                         "why": "built from the engine's own state, not from a mirrored order"})
    return rows


def unmirrored_rows(gaps: Sequence, rows: Sequence) -> list:
    """One row per declared gap that no row of the timeline accounts for: an order the session never mirrored.

    The session records these once per kind and reason (an order held until a result arrives; a delivery
    whose receipt could not be placed; a turn whose settled actions were not supplied). The engine may still
    execute such an order later, and the shadow never sees that: the run does not carry it. The row says so.
    """
    told = {str(row.get("shadow_order_id")) for row in rows}
    out = []
    for gap in gaps:
        if gap.get("order_id") is not None and str(gap.get("order_id")) in told:
            continue
        if any(str(row.get("kind")) == str(gap.get("kind")) and row.get("why") == gap.get("why") for row in rows):
            continue                                  # the adapter's own declared gap for a mirrored action
        out.append({"shadow_order_id": None if gap.get("order_id") is None else str(gap.get("order_id")),
                    "order_minute": None, "kind": gap.get("kind"), "order_id": None, "submission_id": None,
                    "disposition": NOT_MIRRORED, "effective_minute": None,
                    "why": f"{gap.get('why')}: not mirrored, so the shadow run does not carry it"})
    return out


#: The channels a persisted trace carries per minute, where the run has them. Readings of the certified core,
#: named as the core names them; nothing is computed that the core does not already compute.
TRACE_READINGS = ("sbp", "dbp", "map", "monitor_rate_bpm", "spo2", "respiratory_rate", "delivery_rel", "lactate",
                  "crt_s", "consciousness_level", "pulse_present")
TRACE_STATE = ("V", "P", "T", "L", "G", "D", "fio2", "hb")
TRACE_AUXILIARY = ("central_availability", "mechanics_efficiency", "sympathetic_drive", "metabolic_acid_burden")
TRACE_RESPIRATION = ("ventilation", "paco2", "ph")


def artifact_rows(scenario: Mapping) -> list:
    """One row per minute of a replay scenario, from minute 1: the two digests and every channel the trace
    carries. The ONE way a trace row is built -- when a run is recorded and again when a trace is replayed --
    so the replay compares a recorded row with a recomputed one, channel by channel."""
    from clinical_core import derived as dv
    trajectory, anchors, profile = _replay_trajectory(scenario)
    readings = trajectory.derived()
    rows = []
    for minute in range(1, len(trajectory.states)):
        state, derived = trajectory.states[minute], readings[minute].to_dict()
        channels = {name: derived.get(name) for name in TRACE_READINGS}
        channels.update({name: float(getattr(state, name)) for name in TRACE_STATE})
        channels.update({name: float(getattr(state.aux, name)) for name in TRACE_AUXILIARY})
        try:
            breathing = dv.respiration(state, anchors, profile)
            channels.update({"ventilation": breathing.ventilation, "paco2": breathing.paco2, "ph": breathing.ph})
        except Exception:
            pass                       # this profile has no acid-base physiology: the channels are absent
        rows.append({"minute": minute, "state_digest": rs._digest_of(state),
                     "reading_digest": reading_digest(derived), "channels": channels})
    return rows


def run_channels(runner: "ShadowPhysiologyRunner") -> list:
    """The recorded minutes of one run with their channels, rebuilt FROM THE RUN'S OWN ARTIFACT.

    One row per recorded minute: the two digests, then every channel of ``TRACE_READINGS``, ``TRACE_STATE``,
    ``TRACE_AUXILIARY`` and -- where the profile has the acid-base physiology on -- ``TRACE_RESPIRATION``.
    A run that failed keeps the minutes it recorded and nothing after them. A minute the artifact does not
    rebuild keeps what the run recorded -- its digests and its readings -- and says its state channels are
    unavailable: nothing is claimed that was not recomputed.
    """
    rows = [{"minute": item.minute, "state_digest": item.state_digest,
             "reading_digest": reading_digest(item.derived),
             "channels": {name: item.derived.get(name) for name in TRACE_READINGS}} for item in runner.results]
    try:
        captured = runner.replay_input()
        rebuilt = {} if captured is None else {row["minute"]: row for row in artifact_rows(captured.scenario)}
    except Exception:
        rebuilt = {}
    for row in rows:
        again = rebuilt.get(row["minute"])
        if again is None or (again["state_digest"], again["reading_digest"]) != (row["state_digest"],
                                                                                row["reading_digest"]):
            row["channels_unavailable"] = "the artifact does not reproduce this minute"
            continue
        row["channels"] = again["channels"]
    return rows


#: P3-150, what a faculty or development reader is told went wrong, and never less than that.
ARRIVAL_REJECTED = "ARRIVAL_REJECTED"
UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
WITNESS_FAILED = "WITNESS_FAILED"
REPLAY_MISMATCH = "REPLAY_MISMATCH"
LINEAGE_REJECTED = "LINEAGE_REJECTED"
TRACE_PERSISTENCE_FAILED = "TRACE_PERSISTENCE_FAILED"
INTERNAL_SHADOW_ERROR = "INTERNAL_SHADOW_ERROR"
STATUS_CODES = (ARRIVAL_REJECTED, UNSUPPORTED_ACTION, WITNESS_FAILED, REPLAY_MISMATCH, LINEAGE_REJECTED,
                TRACE_PERSISTENCE_FAILED, INTERNAL_SHADOW_ERROR)
#: The state of a shadow encounter as a whole. There is no bare "success": COMPLETE means every run reached
#: the encounter's minute and nothing at all was reported, and every other state says what is missing.
COMPLETE = "COMPLETE"
COMPLETE_WITH_UNSUPPORTED_ACTIONS = "COMPLETE_WITH_UNSUPPORTED_ACTIONS"
PARTIAL = "PARTIAL"
FAILED = "FAILED"
REJECTED = "REJECTED"
STATUS_STATES = (COMPLETE, COMPLETE_WITH_UNSUPPORTED_ACTIONS, PARTIAL, FAILED, REJECTED)
#: Where a session failure comes from decides its code. Anything not listed is an internal error.
_STOPS_THE_SESSION_RUN = ("core", "history", "observe", "artifact")


def status_code(where: str, exception: str = "") -> str:
    """The P3-150 code of one recorded failure, from where it was recorded."""
    where = str(where or "")
    if where == "ensemble:lineage":
        return LINEAGE_REJECTED
    if where.startswith("ensemble:"):
        return WITNESS_FAILED
    if where in ("start", "open"):
        return ARRIVAL_REJECTED
    if where == "persist":
        return TRACE_PERSISTENCE_FAILED
    if where == "replay":
        return REPLAY_MISMATCH
    return INTERNAL_SHADOW_ERROR


def session_status(*, failures: Sequence, gaps: Sequence, actions: Sequence, expected_witnesses: Sequence,
                   runs: Mapping, session_minutes: int, replay: Mapping | None = None) -> dict:
    """The structured status of one shadow encounter: its state, its codes and every item behind them.

    ``failures`` are the session's recorded failures (mappings with ``where``, ``exception``, ``minute``,
    ``message``); ``runs`` maps a run name to its recorded minute count and whether it failed. A witness the
    family declares and the trace does not hold is a failed witness. Nothing here is inferred from a
    trajectory: only from what was recorded.
    """
    items = []
    for failure in failures:
        failure = dict(failure)
        items.append({"code": status_code(failure.get("where"), failure.get("exception")),
                      "where": failure.get("where"), "minute": failure.get("minute"),
                      "detail": f"{failure.get('exception')}: {failure.get('message')}"})
    seen = set()
    for gap in gaps:
        key = (gap.get("kind"), gap.get("why"))
        if key in seen:
            continue
        seen.add(key)
        items.append({"code": UNSUPPORTED_ACTION, "where": "mapping", "minute": None,
                      "detail": f"{gap.get('kind')}: {gap.get('why')}"})
    for action in actions:
        if action.get("disposition") == UNACCOUNTED:
            items.append({"code": INTERNAL_SHADOW_ERROR, "where": "mapping", "minute": action.get("order_minute"),
                          "detail": f"{action.get('kind')} ({action.get('shadow_order_id')}): {action.get('why')}"})
    refused = any(item["code"] == LINEAGE_REJECTED for item in items)
    for name in expected_witnesses:
        run = runs.get(name)
        if run is None and not refused:
            items.append({"code": WITNESS_FAILED, "where": f"ensemble:{name}", "minute": None,
                          "detail": "a witness this family declares is missing from the session"})
        elif run is not None and int(run.get("minutes", 0)) < int(session_minutes) and not any(
                item["code"] == WITNESS_FAILED and str(item["where"]).startswith(f"ensemble:{name}")
                for item in items):
            items.append({"code": WITNESS_FAILED, "where": f"ensemble:{name}", "minute": run.get("minutes"),
                          "detail": f"the witness stopped at minute {run.get('minutes')} of {session_minutes}"})
    items.extend(_replay_items(replay))
    return _status_of(items)


def _replay_items(replay: Mapping | None) -> list:
    """What a replay adds to a status: one item per run that does not reproduce, or the reason it was refused."""
    if replay is None or replay.get("reproduces") is True:
        return []                      # only an explicit "it reproduces" adds nothing: anything else fails closed
    items = []
    for name, row in sorted((replay.get("runs") or {}).items()):
        if not row.get("reproduces", True):
            items.append({"code": row.get("code") or REPLAY_MISMATCH, "where": f"replay:{name}",
                          "minute": row.get("first_mismatch"),
                          "detail": row.get("why") or "the replay does not reproduce the recorded minutes"})
    if not items:
        code = LINEAGE_REJECTED if replay.get("refused") == LINEAGE_REJECTED else REPLAY_MISMATCH
        items.append({"code": code, "where": "replay", "minute": None,
                      "detail": replay.get("why") or "the trace was not replayed"})
    return items


def _status_of(items: Sequence) -> dict:
    """The state and the codes that a list of items adds up to. The one place the state is decided.

    It reads what it is given and fails closed on what it does not understand: an item that is not an item,
    or whose code this layer does not know, is an internal error, never nothing.
    """
    cleaned = []
    for item in items:
        item = dict(item) if isinstance(item, Mapping) else {"code": None, "detail": repr(item)[:120]}
        for key in ("where", "minute", "detail"):
            item.setdefault(key, None)
        if item.get("code") not in STATUS_CODES:
            item["detail"] = f"unknown status code {item.get('code')!r}: {item.get('detail')}"
            item["code"] = INTERNAL_SHADOW_ERROR
        cleaned.append(item)
    items = cleaned
    codes = [code for code in STATUS_CODES if any(item["code"] == code for item in items)]
    stopped = any(item["code"] == INTERNAL_SHADOW_ERROR and str(item["where"]) in _STOPS_THE_SESSION_RUN
                  for item in items)
    if ARRIVAL_REJECTED in codes:
        state = REJECTED
    elif stopped or REPLAY_MISMATCH in codes:
        state = FAILED
    elif any(code in codes for code in (WITNESS_FAILED, LINEAGE_REJECTED, TRACE_PERSISTENCE_FAILED,
                                        INTERNAL_SHADOW_ERROR)):
        state = PARTIAL
    elif UNSUPPORTED_ACTION in codes:
        state = COMPLETE_WITH_UNSUPPORTED_ACTIONS
    else:
        state = COMPLETE
    return {"state": state, "qualified": state != COMPLETE, "codes": codes, "items": items,
            "counts": {code: sum(1 for item in items if item["code"] == code) for code in codes}}


def status_with_replay(status: Mapping, replay: Mapping | None) -> dict:
    """A recorded status with what a later replay found folded in. The recorded status is not changed.

    A trace that does not replay, or that a replay refused, is never left reading as complete.
    """
    recorded = dict(status).get("items") if isinstance(status, Mapping) else None
    items = [item for item in (recorded if isinstance(recorded, (list, tuple)) else [])
             if replay is None or not (isinstance(item, Mapping)
                                       and str(item.get("where") or "").startswith("replay"))]
    return _status_of(items + _replay_items(replay))


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
