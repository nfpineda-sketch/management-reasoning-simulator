"""P2F-6..9: the Level-2 candidate-band registry and a deterministic calibration sweep.

    python -m clinical_core.calibration [--quick] [--out <directory outside the repository>]

Shadow and offline. The sweep never changes a canonical default and never writes the golden:
every candidate runs on copies (``dataclasses.replace``). It does not select a parameter set.
For each candidate it reports, separately:
- A. the approved qualitative physiological constraints (pass or fail, and why);
- B. the GI trajectories the candidate produces;
- C. the difference from the family engine's golden runs.
Only A decides whether a candidate is acceptable. C is diagnostic: no fitting, no ranking by
match count, no parameter chosen to reduce it (P2F-9).
"""
from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Mapping

from . import gi_reference
from .bands import ARRIVAL, Demand, Drift
from .derived import (DEFAULT_PROFILE, CoreProfile, arterial_pressures, check_arrival_reconstruction, derive,
                      delivery_deficit, relative_delivery)
from .integration import Contribution, Contributor, run
from .provenance import SettingChange, SourceKind
from .state import Anchors, CoreInvariantError, RhythmState, UnresolvedBoundary

CANDIDATE, FACULTY_APPROVED, DEFAULT_UNMAPPED, SYNTHETIC_ONLY = (
    "CANDIDATE", "FACULTY_APPROVED", "DEFAULT_UNMAPPED", "SYNTHETIC_ONLY")
STATUSES = (CANDIDATE, FACULTY_APPROVED, DEFAULT_UNMAPPED, SYNTHETIC_ONLY)


@dataclass(frozen=True)
class RegistryEntry:
    """One calibratable parameter (P2F-7). ``per_case`` bands come from ``gi_reference``."""

    name: str
    group: str
    target: str            # profile, case or family
    lower: float | None
    midpoint: float | None
    upper: float | None
    units: str
    rationale: str
    evidence: tuple[str, ...]
    mechanisms: tuple[str, ...]
    constraints: tuple[str, ...]
    status: str
    canonical: Any
    options: tuple = ()
    per_case: bool = False

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"{self.name}: status is one of {STATUSES}")
        if self.lower is not None and not self.lower <= (self.midpoint if self.midpoint is not None
                                                         else self.lower) <= self.upper:
            raise ValueError(f"{self.name}: lower <= midpoint <= upper")

    def points(self) -> tuple:
        if self.options:
            return tuple(self.options)
        return tuple(sorted({value for value in (self.lower, self.midpoint, self.upper) if value is not None}))


def _p(name, group, lower, mid, upper, units, rationale, mechanisms, constraints, evidence=None, status=CANDIDATE,
       options=()):
    return RegistryEntry(name, group, "profile", lower, mid, upper, units, rationale,
                         evidence or (f"derived.PARAMETERS[{name!r}]",), mechanisms, constraints, status,
                         getattr(DEFAULT_PROFILE, name), options)


def _c(name, group, units, rationale, mechanisms, constraints, canonical, evidence=("gi_reference.case_bands",)):
    return RegistryEntry(name, group, "case", None, None, None, units, rationale, evidence, mechanisms, constraints,
                         CANDIDATE, canonical, per_case=True)


def _u(name, group, units, rationale, mechanisms, target="module", status=DEFAULT_UNMAPPED, canonical=None,
       evidence=()):
    return RegistryEntry(name, group, target, None, None, None, units, rationale, evidence, mechanisms, (), status,
                         canonical)


#: P2F-7. No entry is FACULTY_APPROVED: none has an explicit prior faculty approval of its number.
REGISTRY: Mapping[str, RegistryEntry] = {entry.name: entry for entry in (
    # D / lactate
    _p("debt_clearance_tau_min", "D/lactate", 30.0, 60.0, 120.0, "min",
       "first-order repayment of D; no faculty value; 60 is the provisional default",
       ("D", "lactate production", "sympathetic D term"), ("DL1", "DL2", "DL3", "DL4")),
    _p("debt_per_delivery_deficit", "D/lactate", 0.5, 1.0, 2.0, "index-min per unit deficit-minute",
       "deficit -> D gain; lactate shows only its product with the D -> lactate gain, D drive shows it alone",
       ("D", "sympathetic D term"), ("DL1", "DL2", "DL4")),
    _p("lactate_per_output_deficit", "D/lactate", 2.0, 6.0, 12.0, "mmol/L per unit of sustained deficit",
       "D -> lactate production gain, read as the steady-state lactate excess per unit of sustained deficit "
       "(times the deficit-to-debt gain): over 2-12, a sustained deficit of 0.5 settles 1-6 mmol/L above baseline, "
       "moderate to severe hyperlactataemia; the lower bound is the family engine's 2 per circulation unit. The "
       "band is independent of the GI arrival lactates: it is not inferred from fitting them",
       ("lactate", "RR metabolic drive"), ("DL2", "RR1")),
    _p("lactate_clearance_tau_min", "D/lactate", 45.0, 120.0, 240.0, "min",
       "lactate clearance once delivery is restored; half-lives of roughly 0.5-3 h under resuscitation",
       ("lactate",), ("DL2", "DL3", "RR1")),
    _c("arrival_oxygen_debt", "D/lactate", "index-min",
       "the debt accrued before arrival, declared directly: the scale of the variable (0 to a severe deficit's "
       "debt after about two hours), not reconstructed from a pre-arrival history", ("D",), ("AC1", "AC2"), 0.0),
    _c("arrival_lactate_excess", "D/lactate", "mmol/L", "arrival lactate less a non-shock baseline of 0.8-2.0",
       ("lactate",), ("AC1", "AC2"), 0.0),
    _c("arrival_delivery_ratio", "D/lactate", "units of the delivery that meets demand",
       "0.6-1.0: impaired perfusion, hypotension and severe anaemia place arrival at or below adequacy",
       ("D",), ("AC2",), 1.0),
    # RR
    _p("rr_per_lactate", "RR", 3.0, 7.5, 12.0, "breaths/min per mmol/L at the threshold",
       "metabolic drive gain; the ABGs show compensated metabolic acidosis", ("RR",), ("RR1",)),
    _p("lactate_drive_threshold_mmol_l", "RR", 1.5, 2.0, 2.5, "mmol/L",
       "lactate above which acidaemia drives breathing", ("RR",), ("RR1",)),
    _p("rr_metabolic_max", "RR", 15.0, 25.0, 30.0, "breaths/min", "saturation of the metabolic addition", ("RR",),
       ("RR1",)),
    _p("rr_ventilatory_floor", "RR", 10.0, 12.0, 14.0, "breaths/min",
       "RR below which the arrival RR is never read as metabolic", ("RR",), ("RR1",)),
    _p("rr_max", "RR", 40.0, 60.0, 60.0, "breaths/min", "safety bound, not physiology", ("RR",), ("RR1",)),
    # Sympathetic
    _p("sympathetic_per_pressure_deficit", "sympathetic", 0.5, 1.0, 2.0, "drive per unit pressure deficit",
       "baroreflex share of the drive", ("HR",), ("HR1", "HR2", "HR3", "HR4")),
    _p("sympathetic_per_debt", "sympathetic", 0.25, 0.5, 1.0, "drive per unit D / tau_D", "debt share of the drive",
       ("HR",), ("HR1", "HR2", "HR3", "HR4")),
    _p("sympathetic_per_hypoxaemia_point", "sympathetic", 0.01, 0.02, 0.05, "drive per SpO2 point",
       "hypoxaemic share; no GI arrival is hypoxaemic", ("HR",), ("HR3", "HR4")),
    _p("hypoxaemia_threshold_spo2", "sympathetic", 90.0, 92.0, 94.0, "%",
       "SpO2 below which hypoxaemia adds drive; both GI arrivals are above the band", ("HR",), ("HR3", "HR4")),
    _p("sympathetic_per_hypoglycaemia_mg_dl", "sympathetic", 0.005, 0.01, 0.02, "drive per mg/dL",
       "hypoglycaemic share; no GI arrival is hypoglycaemic", ("HR",), ("HR3", "HR4")),
    _p("hypoglycaemia_threshold_mg_dl", "sympathetic", 60.0, 70.0, 70.0, "mg/dL",
       "glucose below which hypoglycaemia adds drive; both GI arrivals are above it", ("HR",), ("HR3", "HR4")),
    _p("sympathetic_decay_tau_min", "sympathetic", 2.0, 5.0, 15.0, "min", "decay of the drive; it rises at once",
       ("HR",), ("HR2", "HR3")),
    _p("hr_per_sympathetic_drive", "sympathetic", 25.0, 25.0, 25.0, "bpm per unit drive",
       "the family engine's literal, adopted in P2C; it sets the drive's units, so it is held", ("HR",), ("HR1",)),
    _c("intrinsic_sinus_rate", "sympathetic", "bpm", "non-acute resting sinus rate, at most the arrival HR",
       ("HR",), ("AC1", "HR2", "HR4"), None),
    _c("arrival_sympathetic_drive", "sympathetic", "drive units", "arrival HR less intrinsic, over the gain",
       ("HR",), ("AC1", "HR3"), 0.0),
    # Preload / pump
    _p("preload_curve_scale_ml", "preload", 600.0, 833.3333333333334, 1500.0, "mL-eq",
       "scale of the saturating preload curve; the default keeps the legacy slope at position 0.5. Read in V units: "
       "with kappa (P2I-2T) only the ratio scale / kappa is identifiable, so it is never decided alone: FD-08, FD-14, "
       "FD-15 and FD-BLD-02..04 all constrain the same scale / kappa (P2I-2U)",
       ("output", "pressure", "congestion"), ("PL1", "PL2", "PL3", "PL4")),
    _p("arrival_preload_fraction", "preload", 0.3, 0.5, 0.7, "position (0-1)", "default arrival position",
       ("output",), ("PL1", "PL2", "PL3")),
    _c("preload_fraction", "preload", "position (0-1)", "POCUS: collapsing IVC, small or hyperdynamic LV",
       ("output",), ("PL1",), None),
    _c("reference_preload_fraction", "preload", "position (0-1)",
       "euvolemic reference, 0.6-0.8 for both cases (not stated by either); diagnostic only", (), (), None),
    _p("pump_preload_coupling", "preload", 0.0, 0.5, 1.0, "exponent c", "how far a depressed pump shrinks the curve",
       ("output",), ("PL2", "PL3")),
    _p("afterload_sensitivity", "preload", 0.1, 0.3, 0.5, "per unit tone", "tone above arrival lowers output",
       ("output",), ("PL1",)),
    _c("pump_reserve", "preload", "share of normal", "no evidence of reduced reserve in either case",
       ("congestion",), ("PL4",), 1.0),
    # Congestion
    _p("congestion_preload_knee", "congestion", 0.75, 0.85, 0.92, "position (0-1)",
       "position above which added preload congests a pump without reserve", ("L",), ("PL4",)),
    _p("congestion_per_excess_preload", "congestion", 0.02, 0.05, 0.1, "L per minute at full excess",
       "overload gain", ("L",), ("PL4",)),
    _p("lung_water_clearance_tau_min", "congestion", 120.0, 240.0, 480.0, "min", "slow clearance of L", ("L",),
       ("PL4",)),
    # Collapse (off by default)
    _p("collapse_output_threshold", "collapse", 0.2, 0.3, 0.4, "output_rel (relative to arrival)",
       "output below which the burden accrues; off by default; normalization against arrival is TBD",
       ("R (terminal)",), ("CO1", "CO2")),
    _p("collapse_burden_per_minute", "collapse", 0.5, 1.0, 2.0, "burden per minute at full severity",
       "how fast severity accrues; 1 since P2E-3",
       ("R (terminal)",), ("CO1", "CO2")),
    _p("collapse_burden_limit", "collapse", 5.0, 15.0, 30.0, "burden (dwell equivalent, minutes at full severity)",
       "the dwell equivalent: minutes at no output before the transition; no clinical dwell is approved",
       ("R (terminal)",), ("CO1", "CO2")),
    _p("collapse_repayment_tau_min", "collapse", 30.0, 60.0, 240.0, "min", "repayment once output recovers",
       ("R (terminal)",), ("CO1",)),
    _p("collapse_terminal_rhythm", "collapse", None, None, None, "policy",
       "which pulseless rhythm the rule ends in; the selection rule is TBD", ("R (terminal)",), ("CO2",),
       options=("pea", "asystole")),
    _u("collapse_rule_test_values", "collapse", "threshold 0.4, limit 10",
       "the values the P2E-3 tests use", ("R (terminal)",), target="tests", status=SYNTHETIC_ONLY,
       canonical=(0.4, 10.0), evidence=("test_clinical_core_low_output.RULE",)),
    # Pressure
    _p("low_output_pressure_knee", "pressure", 0.3, 0.5, 0.6, "pressure_rel",
       "below it pressure is proportional to flow x tone", ("SBP", "DBP", "MAP"), ("PR1", "PR2", "PR3")),
    _p("sbp_per_pressure_deficit", "pressure", 35.0, 45.0, 55.0, "mmHg per unit deficit", "legacy literal 45",
       ("SBP",), ("PR1", "PR3")),
    _p("dbp_per_pressure_deficit", "pressure", 15.0, 25.0, 30.0, "mmHg per unit deficit", "legacy literal 25",
       ("DBP",), ("PR1", "PR3")),
    _p("crt_per_output_deficit_s", "pressure", 3.0, 4.0, 5.0, "s per unit output deficit", "legacy literal 4",
       ("CRT",), ()),
    # Oxygen delivery and demand
    _p("spo2_per_fio2", "demand", 20.0, 30.0, 40.0, "SpO2 points per unit FiO2", "legacy literal 30",
       ("SpO2", "delivery"), ("DM1",)),
    _c("metabolic_demand_baseline", "demand", "units of the delivery that meets it",
       "1 for uncomplicated haemorrhage; never a free parameter for lactate", ("D",), ("DM1",), 1.0),
    _u("sepsis_demand_multiplier", "demand", "factor", "no band: no sepsis module and no GI evidence", ("D",)),
    _u("fever_demand_multiplier", "demand", "factor", "no band: no GI case is febrile", ("D",)),
    _u("seizure_demand_multiplier", "demand", "factor", "no band: no GI seizure", ("D",)),
    _u("agitation_pain_demand_multiplier", "demand", "factor", "no band: no marked agitation or pain", ("D",)),
    _u("vasodilation_with_demand_probe_factor", "demand", "factor", "the Level-2 probe's 1.3",
       ("D",), target="probe", status=SYNTHETIC_ONLY, canonical=1.3, evidence=("bands.PROBES",)),
    # Shared blood state (P2I-2T): provisional values, no band. P2I-2U: none is put to faculty on its own;
    # each is constrained only through the patient-level anchors FD-BLD-01..09
    # (docs/revision/P2I2U_ANCLAS_HEMORRAGIA_COMPARTIDA.md).
    _p("arrival_circulating_volume_ml", "blood", None, None, None, "mL-eq",
       "normalization of red-cell content and Hb; not inferred from the arrival Hb; not decided directly: "
       "constrained through FD-BLD anchors", ("Hb",), ()),
    _p("volume_preload_kappa", "blood", None, None, None, "V per mL-eq of circulating volume",
       "V = kappa x circulating-volume deviation; bookkeeping only: only kappa / preload_curve_scale_ml is "
       "identifiable, so kappa is never decided apart from the curve scale", ("V", "output"), ()),
    _p("plasma_refill_target_share", "blood", None, None, None, "share of the shed volume",
       "how much of the shed volume plasma refill restores at most; not decided directly: FD-BLD-07..09",
       ("V", "Hb"), ()),
    _p("plasma_refill_tau_min", "blood", None, None, None, "min", "refill time constant; not decided directly: "
       "FD-BLD-07..09", ("V", "Hb"), ()),
    _p("plasma_refill_capacity_ml", "blood", None, None, None, "mL-eq", "finite interstitial reserve; not decided "
       "directly: FD-BLD-07..09", ("V", "Hb"), ()),
    _u("red_cell_unit_hb_g_dl", "blood", "g/dL", "haemoglobin concentration of one packed red-cell unit (P2I-2T); "
       "not the legacy 0.85 g/dL step; not decided directly: FD-BLD-01 (the output anchors FD-BLD-02/03 do not "
       "depend on it)", ("Hb",), status=CANDIDATE,
       canonical=20.0, evidence=("legacy_adapter.PROVISIONAL_RED_CELL_UNIT_HB_G_DL",)),
    # GI source parameters (family)
    RegistryEntry("gi_blood_loss_ml_per_min", "GI source", "family", 2.5, 2.5, 2.5, "mL-eq/min",
                  "family engine literal 0.003 circulation/min read as whole-blood loss, adopted for the comparison; "
                  "one rate drives volume and red cells through the shared blood state (P2I-2T)", (
                      "legacy_adapter.LEGACY_LITERALS",), ("V", "Hb"), (), CANDIDATE, 2.5),
    RegistryEntry("gi_fraction_with_ppi", "GI source", "family", 0.8, 0.8, 0.8, "share of the bleed",
                  "family_engine.GI_BLEED['bleeding_with_ppi']", ("family_engine.py:202",), ("V", "Hb"), (), CANDIDATE,
                  0.8),
    RegistryEntry("gi_fraction_after_hemostasis", "GI source", "family", 0.1, 0.1, 0.1, "share of the bleed",
                  "family_engine.GI_BLEED['bleeding_after_hemostasis'] (hemostasis: faculty decision 2026-09-19 on "
                  "the mechanism, not on this core number)", ("family_engine.py:201",), ("V", "Hb"), (), CANDIDATE,
                  0.1),
)}


# P2F-6 -- oxygen delivery ---------------------------------------------------------------------

DELIVERY_MODEL = ("dimensionless relative delivery: (Q / Q_a)(Hb / Hb_a)(SpO2 / SpO2_a), relative to arrival, times "
                  "the case's arrival delivery ratio for the units of the delivery that meets the reference demand; "
                  "not an indexed physical DO2")
NEUTRAL = Anchors(**ARRIVAL)


def delivery_probes(anchors: Anchors = NEUTRAL) -> list[dict]:
    """The six P2F-6 probes, at fixed demand 1 and at demand 1.2, and the debt they accrue in an hour."""
    cases = {"isolated low output": (0.6, 1.0, 1.0), "isolated anaemia": (1.0, 0.6, 1.0),
             "isolated hypoxaemia": (1.0, 1.0, 0.85), "low output + anaemia": (0.6, 0.6, 1.0),
             "anaemia + hypoxaemia": (1.0, 0.6, 0.85), "all three": (0.6, 0.6, 0.85)}
    gain = DEFAULT_PROFILE.debt_per_delivery_deficit
    rows = []
    for name, (output, hb, spo2) in cases.items():
        delivery = relative_delivery(output, hb * anchors.hb, spo2 * anchors.spo2, anchors)
        deficits = {demand: delivery_deficit(demand, delivery) for demand in (1.0, 1.2)}
        rows.append({"probe": name, "output_rel": output, "hb_ratio": hb, "spo2_ratio": spo2, "delivery": delivery,
                     "deficit_at_demand_1": deficits[1.0], "deficit_at_demand_1_2": deficits[1.2],
                     # P2I-2AC: while a deficit lasts the debt accrues and is not repaid.
                     "debt_after_60_min": deficits[1.0] * gain * 60.0})
    return rows


@dataclass(frozen=True)
class OxygenLoss(Contributor):
    """The supplemental oxygen of an arrival on oxygen is lost (probe only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "calibration_oxygen_loss"
    id: str
    at_minute: int

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(settings=(SettingChange("fio2", 0.21, self.source, minute, "oxygen lost"),))


def hypoxaemia_trajectory_probe() -> dict:
    """Isolated hypoxaemia in a run: the core moves SpO2 only through FiO2 (G, L, W do not feed it yet)."""
    on_oxygen = Anchors(**{**ARRIVAL, "fio2": 0.4})
    trajectory = run(on_oxygen, (OxygenLoss("oxygen_lost", 1),), 60)
    derived = trajectory.derived()
    return {"spo2": [derived[0].spo2, derived[1].spo2], "delivery": [derived[0].delivery_rel, derived[1].delivery_rel],
            "D_at_60": trajectory.states[-1].D}


# P2F-8 -- qualitative constraints (A) ---------------------------------------------------------

class Failed(Exception):
    pass


def _expect(condition: bool, reason: str):
    if not condition:
        raise Failed(reason)


def _debts(trajectory):
    return [state.D for state in trajectory.states]


def _excess(trajectory):
    return [state.aux.lactate_excess_mmol_l for state in trajectory.states]


def check_dl1_dl2_dl4(profile: CoreProfile, **_):
    runs = [run(NEUTRAL, (Demand("demand", 0, 120, factor),), 120, profile) for factor in (1.1, 1.3, 1.5)]
    for low, high in zip(runs, runs[1:]):
        _expect(all(b >= a - 1e-12 for a, b in zip(_debts(low), _debts(high))), "DL1: a worse deficit gave less D")
        _expect(all(b >= a - 1e-12 for a, b in zip(_excess(low), _excess(high))),
                "DL2: a worse deficit gave less lactate excess")
    for trajectory in runs:
        _expect(min(_debts(trajectory)) >= 0 and min(_excess(trajectory)) >= 0, "DL4: D or lactate went negative")
        _expect(min(item.lactate for item in trajectory.derived()) >= 0, "DL4: lactate went negative")


def check_dl3(profile: CoreProfile, **_):
    trajectory = run(NEUTRAL, (Demand("demand", 0, 60, 1.3),), 300, profile)
    debts, excess = _debts(trajectory), _excess(trajectory)
    _expect(all(b < a for a, b in zip(debts[60:], debts[61:])), "DL3: D did not fall steadily after recovery")
    _expect(debts[70] > 0.5 * debts[60], "DL3: D halved within 10 minutes of recovery (not gradual)")
    peak = max(excess[60:])
    _expect(excess[peak_index(excess, 60) + 10] > 0.5 * peak, "DL3: lactate halved within 10 minutes of its peak")
    _expect(debts[-1] < debts[60] and excess[-1] < peak, "DL3: no recovery at all")


def peak_index(values, start):
    return max(range(start, len(values)), key=lambda index: values[index])


def check_rr1(profile: CoreProfile, **_):
    arrival = Anchors(**{**ARRIVAL, "lactate": 4.0, "respiratory_rate": 24.0, "arrival_lactate_excess": 3.2,
                         "declared": {"arrival_lactate_excess": "synthetic_probe"}})
    shock = (Drift("loss", "V", 0, 40, -8.0), Drift("restore", "V", 40, 41, 900.0))
    derived = run(arrival, shock, 600, profile).derived()
    floor = min(arrival.respiratory_rate, 10.0)
    _expect(min(item.respiratory_rate for item in derived) >= floor,
            f"RR1: correcting shock took RR to {min(item.respiratory_rate for item in derived):.1f} (< {floor})")


def _midpoint_arrivals() -> dict:
    """Each GI case with every case band at its midpoint: the arrival the group sweeps probe."""
    return {case: gi_reference.candidate_anchors(case, case_values(case, GICandidate({})))
            for case in gi_reference.GI_CASES}


def check_hr(profile: CoreProfile, arrivals: Mapping[str, Anchors] | None = None, **_):
    """HR1-HR4 on each GI case's full declared arrival (the candidate's, or every band at its midpoint).

    The loss is a SYNTHETIC_STATE_PERTURBATION of the preload coordinate (``LEVEL1_DIRECT_WRITES``), not a
    haemorrhage: it moves V alone, with no red cells, no refill and no Hb change."""
    for case, arrival in (arrivals or _midpoint_arrivals()).items():
        rate = arrival.intrinsic_sinus_rate if arrival.intrinsic_sinus_rate is not None else arrival.hr
        volume_loss = run(arrival, (Drift("loss", "V", 0, 30, -8.0),), 30, profile)
        rates = [item.pulse_rate_bpm for item in volume_loss.derived()]
        _expect(max(rates) > arrival.hr, f"HR1 ({case}): deterioration did not raise HR")
        recovered = run(arrival, (Drift("loss", "V", 0, 30, -8.0), Drift("restore", "V", 30, 31, 640.0)), 240,
                        profile)
        after = [item.pulse_rate_bpm for item in recovered.derived()]
        _expect(after[-1] < arrival.hr, f"HR2 ({case}): recovery did not take HR below the arrival HR")
        for trajectory, values in ((volume_loss, rates), (recovered, after)):
            _expect(min(state.aux.sympathetic_drive for state in trajectory.states) >= 0,
                    f"HR3 ({case}): negative sympathetic drive")
            _expect(min(values) >= rate - 1e-9, f"HR4 ({case}): HR below intrinsic without a mechanism")


def _output(profile, anchors, **changes):
    state = run(anchors, (), 0, profile).states[0].evolve(**changes)
    return derive(state, anchors, profile).output_rel


def check_preload(profile: CoreProfile, **_):
    outputs = [_output(profile, NEUTRAL, V=volume) for volume in (0.0, 250.0, 500.0, 750.0)]
    gains = [b - a for a, b in zip(outputs, outputs[1:])]
    _expect(all(g > 0 for g in gains) and gains[0] > gains[1] > gains[2], "PL1: no diminishing returns")
    normal = _output(profile, NEUTRAL, V=500.0) - _output(profile, NEUTRAL)
    weak = _output(profile, NEUTRAL, P=0.6, V=500.0) - _output(profile, NEUTRAL, P=0.6)
    _expect(weak <= normal and _output(profile, NEUTRAL, P=0.6, V=500.0) < 1.0,
            "PL2: a depressed pump was rescued by 500 mL")
    _expect(_output(profile, NEUTRAL, P=0.4, V=250.0) < 0.8, "PL3: a severely depressed pump normalized with 250 mL")


def check_congestion(profile: CoreProfile, **_):
    arrival = Anchors(**{**ARRIVAL, "pump_reserve": 0.3, "declared": {"pump_reserve": "synthetic_probe"}})
    trajectory = run(arrival, (Drift("fluid", "V", 0, 1, 2900.0),), 60, profile)
    _expect(trajectory.states[-1].L > 0, "PL4: no lung water from 2.9 L of added preload with reserve 0.3")


def check_pressure(profile: CoreProfile, **_):
    arrivals = [NEUTRAL] + [gi_reference.candidate_anchors(case, {}) for case in gi_reference.GI_CASES]
    levels = [1.3 - index * 0.013 for index in range(101)]
    for arrival in arrivals:
        readings = [arterial_pressures(level, arrival, profile) for level in levels]
        means = [(sbp + 2 * dbp) / 3 for sbp, dbp in readings]
        _expect(all(b <= a + 1e-12 for a, b in zip(means, means[1:])), f"PR1 ({arrival.case_id}): MAP not monotonic")
        _expect(max(arterial_pressures(1e-6, arrival, profile)) < 1.0, f"PR2 ({arrival.case_id}): no tendency to 0")
        _expect(all(sbp >= dbp for sbp, dbp in readings),
                f"PR3 ({arrival.case_id}): SBP below DBP on the output range (pulse pressure "
                f"{arrival.sbp - arrival.dbp:g} mmHg)")


def check_collapse(profile: CoreProfile, **_):
    rule = profile if profile.collapse_output_threshold is not None else replace(
        profile, collapse_output_threshold=REGISTRY["collapse_output_threshold"].midpoint,
        collapse_burden_limit=REGISTRY["collapse_burden_limit"].midpoint)
    # Frozen (FROZEN_RULES["CO1"]): five minutes at 90% of the threshold, as written before any sweep.
    modest = max(0.1, 0.9 * rule.collapse_output_threshold)
    brief = run(NEUTRAL, (Drift("down", "P", 0, 1, modest - 1.0), Drift("up", "P", 5, 6, 1.0 - modest)), 30, rule)
    _expect(all(state.R.pulse_present for state in brief.states),
            "CO1: five minutes at 90% of the threshold arrested")
    severe = run(NEUTRAL, (Drift("down", "P", 0, 1, -0.9),), 240, rule)
    _expect(not severe.states[-1].R.pulse_present, "CO2: four hours at output 0.1 never met the collapse criterion")


def check_demand(profile: CoreProfile, **_):
    """DM1 through the integrator: at the same reduced delivery, more demand never gives less D."""
    anaemic = Drift("anaemia", "hb", 0, 1, -0.3 * NEUTRAL.hb)
    runs = [run(NEUTRAL, (anaemic, Demand("demand", 0, 60, factor)), 60, profile) for factor in (1.0, 1.2)]
    deliveries = [[item.delivery_rel for item in trajectory.derived()] for trajectory in runs]
    _expect(deliveries[0] == deliveries[1], "DM1: demand changed delivery")
    _expect(all(b >= a - 1e-12 for a, b in zip(_debts(runs[0]), _debts(runs[1]))) and
            _debts(runs[1])[-1] > _debts(runs[0])[-1], "DM1: more demand at the same delivery gave less D")


@dataclass(frozen=True)
class Rule:
    """A qualitative acceptance rule, frozen before the final sweep (P2F methodological correction 3).

    ``guaranteed`` says when the model's construction already ensures the rule within the
    bands, so that passing it says nothing about a candidate (non-discriminating).
    """

    rule: str
    source: str
    probe: str
    rationale: str
    guaranteed: str = ""


#: Every qualitative acceptance rule, frozen before the final sweep. The probe sizes are candidate
#: operationalizations of approved directions, not approved numbers. No rule was chosen, kept or
#: tightened for the number of candidates it passes. Steady state is not a rule; nor is any
#: pre-arrival reconstruction (that is SYNTHETIC_PLAUSIBILITY_PROBE, a diagnostic).
FROZEN_RULES: Mapping[str, Rule] = {
    "DL1": Rule("a worse sustained deficit never yields less D", "KD-S1, P2D-4, P2E-2",
                "demand x1.1, x1.3, x1.5 for 120 min at identical delivery: D ordered every minute",
                "monotonicity of the debt in the deficit", "by construction: D is linear in the deficit, gain > 0"),
    "DL2": Rule("a worse sustained deficit never yields less lactate excess", "KD-S1, P2D-4",
                "the same runs: lactate excess ordered every minute", "monotonicity of lactate in the debt",
                "by construction: lactate is linear in D, gain > 0"),
    "DL3": Rule("recovery is gradual", "KD-S1 (restoration leaves debt and lactate to clear gradually)",
                "demand x1.3 for 60 min, then none: D falls every minute after, lactate falls after its peak, "
                "neither halves within 10 minutes, and both are lower after 4 hours",
                "memory: an abrupt reset (half the debt gone in minutes) is what the decision rules out",
                "within the bands: every time constant is at least 30 min"),
    "DL4": Rule("no negative D, lactate excess or lactate", "P2E-2 invariants", "every probe run",
                "sign consistency", "by construction: the D bound and the state invariants"),
    "RR1": Rule("correcting shock alone does not create pathological bradypnoea", "KD-S1",
                "clearable arrival lactate, 40 min of volume loss, then correction 580 mL beyond arrival, 600 min: "
                "RR >= min(arrival RR, 10)", "clearing lactate may lower RR, never below the ventilatory part",
                "by construction: the metabolic share falls at most to 0 and the floor is >= 10"),
    "HR1": Rule("deterioration can increase HR", "KD-S2",
                "each GI case's full declared arrival (the candidate's), volume loss 8 mL/min for 30 min: HR rises "
                "above the arrival HR", "the drive answers to the pressure deficit; corrected after the review: "
                "the probe used to declare only the intrinsic rate, not the candidate's whole arrival"),
    "HR2": Rule("recovery can reduce HR toward intrinsic", "P2E-1",
                "the same arrival and loss, then 400 mL beyond arrival, 240 min: HR ends below the arrival HR",
                "an arrival sympathetic share can resolve; same correction as HR1"),
    "HR3": Rule("no negative sympathetic contribution", "P2D-3", "every HR probe run", "sign consistency",
                "by construction: the drive's target is floored at 0"),
    "HR4": Rule("HR below intrinsic requires an explicit mechanism", "P2E-1", "every HR probe run: HR >= intrinsic",
                "no probe declares a negative chronotrope",
                "by construction: sinus HR = intrinsic + gain x drive, drive >= 0"),
    "PL1": Rule("diminishing returns of preload", "KD-S4", "+250, +500, +750 mL: each output gain smaller",
                "saturating curve", "by construction: the curve is concave above the empty point"),
    "PL2": Rule("a depressed pump limits fluid rescue", "P2D-5",
                "P 0.6: 500 mL gains no more than at P 1 and does not restore arrival output",
                "the pump shapes the curve"),
    "PL3": Rule("a severely depressed pump is not normalized by trivial volume", "P2D-5",
                "P 0.4 + 250 mL: output stays below 0.8 of arrival", "as PL2, at the severe end"),
    "PL4": Rule("excessive preload may produce lung water when reserve is limited", "KD-S4",
                "reserve 0.3, +2.9 L (the volume bound is 3 L): L > 0 within 60 min",
                "'may': it must be reachable within the bounds"),
    "PR1": Rule("pressure falls monotonically with output at fixed tone", "P2E-4",
                "pressure_rel 1.3 down to 0 for the neutral and both GI arrivals: MAP never rises", "",
                "by construction (P2E-4)"),
    "PR2": Rule("pressure tends toward zero as output tends to zero", "P2E-4",
                "at pressure_rel 1e-6 both pressures below 1 mmHg", "", "by construction (P2E-4)"),
    "PR3": Rule("SBP never below DBP over the output range", "§11.4 invariant (fails closed otherwise)",
                "the same range, for the neutral and both GI arrivals", "state consistency"),
    "CO1": Rule("brief, moderate low flow need not cause arrest", "P2E-3",
                "five minutes at 90% of the collapse threshold, then recovery: no arrest",
                "written before any sweep, as in the P2E-3 tests (a few minutes just inside the critical region); "
                "a change to ten minutes at 75% was tried after a preliminary sweep and reverted, because it was "
                "motivated by that sweep's result",
                "within the bands: severity 0.1 for at most about six minutes at the largest gain 2 accrues "
                "about 1.2, below the smallest limit (5)"),
    "CO2": Rule("severe, prolonged low flow can accumulate burden to the terminal transition", "P2E-3",
                "output 0.1 (the pump bound) for 240 min: the criterion is met", "'can': reachable within bounds",
                "within the bands: 240 x 0.5 x 0.5 = 60 exceeds the largest limit (30)"),
    "DM1": Rule("more demand at identical delivery worsens the deficit", "P2E-2",
                "through the integrator: Hb down by 30%, demand x1 and x1.2 for 60 min: identical delivery, D "
                "never less and finally more with more demand",
                "corrected after the review: the probe used to test only the arithmetic of max(0, .)",
                "by construction: the deficit is monotonic in demand"),
    "AC1": Rule("the declared arrival reconstructs the authored observation exactly", "P2F-1",
                "check_arrival_reconstruction on both GI arrivals", "arrival-state consistency",
                "by construction (P2F-1)"),
    "AC2": Rule("the declared GI arrival responds coherently", "P2F-1, P2E-2",
                "untreated_60 and definitive_management from each declared arrival: at minute 60 treatment never "
                "leaves D or lactate above the untreated run; no negative D or excess; HR never below intrinsic",
                "arrival-state consistency of a dynamically evolving arrival; steady state is not required",
                "the sign and intrinsic parts by construction; the treatment comparison is not guaranteed"),
}


#: P2I-2W-8: what each active Level-1 check that writes V or Hb directly is. A SYNTHETIC_STATE_PERTURBATION
#: perturbs the internal coordinate to test a downstream rule, independently of haemorrhage: it may keep writing
#: it, and it is never evidence about haemorrhage, Hb or DO2 physiology (NOT_EVIDENCE_FOR). A
#: PHYSIOLOGICAL_HAEMORRHAGE_PROBE claims blood loss and must go through the shared blood state; no active
#: check is one. Labels only: no rule, probe size or assertion changed. P2I-2X: the faculty confirmed the label
#: (2026-10-28) and listed what these checks are never evidence about.
SYNTHETIC_STATE_PERTURBATION = "SYNTHETIC_STATE_PERTURBATION"
PHYSIOLOGICAL_HAEMORRHAGE_PROBE = "PHYSIOLOGICAL_HAEMORRHAGE_PROBE"
NOT_EVIDENCE_FOR = ("blood loss", "haemorrhage severity", "Hb", "DO2", "refill", "PRBC", "clinical case calibration")
LEVEL1_DIRECT_WRITES: Mapping[str, Mapping[str, object]] = {
    "RR1": {"function": "check_rr1", "writes": "V", "semantics": SYNTHETIC_STATE_PERTURBATION,
            "how": "V -8 per minute for 40 min, then +900 at minute 40, from the synthetic probe arrival",
            "why": "a generic shock and its correction on the preload coordinate, to test that clearing lactate "
                   "never takes RR below its ventilatory floor; no GI case, no red cells, no refill, Hb unchanged"},
    "HR1-HR4": {"function": "check_hr", "writes": "V", "semantics": SYNTHETIC_STATE_PERTURBATION,
                "how": "V -8 per minute for 30 min, then +640 at minute 30, from each GI case's declared arrival",
                "why": "the rules are the chronotropic answer to haemodynamic deterioration and recovery (KD-S2, "
                       "P2E-1, P2D-3) and read HR and the sympathetic drive only; the loss moves V alone (no red "
                       "cells, no refill, Hb unchanged) and the restoration is no product: a hypovolaemic "
                       "perturbation of the preload coordinate, not a haemorrhage. Through the blood state it "
                       "would need refill and arrival-volume values that are not approved"},
    "PL1-PL3": {"function": "check_preload", "writes": "V", "semantics": SYNTHETIC_STATE_PERTURBATION,
                "how": "V set to 0, 250, 500 and 750 at minute 0 of the neutral arrival (static readings)",
                "why": "reads the shape of the preload curve and the limit a depressed pump sets; no loss and no "
                       "fluid product"},
    "PL4": {"function": "check_congestion", "writes": "V", "semantics": SYNTHETIC_STATE_PERTURBATION,
            "how": "V +2900 within the first minute, from a synthetic arrival with pump reserve 0.3",
            "why": "reachability of lung water under excess preload with limited reserve: a volume-load "
                   "perturbation, not a fluid product (the crystalloid kinetics are not approved) nor a "
                   "haemorrhage"},
    "DM1": {"function": "check_demand", "writes": "Hb", "semantics": SYNTHETIC_STATE_PERTURBATION,
            "how": "Hb -30 % at minute 0 of the neutral arrival",
            "why": "an isolated anaemia that holds delivery fixed while demand changes; no blood loss"},
}


CHECKS: Mapping[str, tuple[Callable, tuple[str, ...]]] = {
    "DL1/DL2/DL4": (check_dl1_dl2_dl4, ("D/lactate",)),
    "DL3": (check_dl3, ("D/lactate",)),
    "RR1": (check_rr1, ("RR", "D/lactate")),
    "HR1-HR4": (check_hr, ("sympathetic", "D/lactate")),
    "PL1-PL3": (check_preload, ("preload",)),
    "PL4": (check_congestion, ("preload", "congestion")),
    "PR1-PR3": (check_pressure, ("pressure",)),
    "CO1/CO2": (check_collapse, ("collapse",)),
    "DM1": (check_demand, ("demand",)),
}


#: P2G-1 -- the family-engine path that produces the GI scenarios' inputs. Every repository file
#: outside clinical_core/ that runs (is imported or called) while the engine builds the GI
#: arrivals and runs every GI scenario, traced in a fresh interpreter; a test keeps the list exact.
#: The case bank is clinical_cases.py: the path opens no data file of its own.
INPUT_PATH_SOURCES = (
    "acs_reperfusion.py", "active_order_context.py", "airway_pharmacology.py", "analgesia.py",
    "anaphylaxis_reaction.py", "antipyretics.py", "asthma_complications.py", "asthma_ventilation.py",
    "bradycardia_toxicology.py", "case_catalog.py", "case_cues.py", "clinical_cases.py", "clinical_time.py",
    "cognitive_catalog.py", "cognitive_generator.py", "competency_mapping.py", "efast_report.py",
    "event_provenance.py", "family_engine.py", "family_parser.py", "glucose_rescue.py", "hypoglycemia_catalog.py",
    "inotrope_support.py", "opioid_reversal.py", "patient_body.py", "pe_obstruction.py", "pilot_freeze.py",
    "shared_order_language.py", "shared_order_quantities.py", "trauma_hemorrhage.py", "unexecuted_items.py",
    "urine_output.py", "visual_observations.py", "weight_based_doses.py", "work_of_breathing.py")
#: The clinical_core files that turn the engine's run into the core's inputs (the order adapter).
INPUT_ADAPTER_SOURCES = ("clinical_core/legacy_adapter.py", "clinical_core/interventions/timing.py")
#: The GI reference mapping: inventory, case bands and candidate anchors (P2F-2/3).
GI_REFERENCE_SOURCE = "clinical_core/gi_reference.py"
#: The harness itself, whole: every rule, check binding, design default and probe it runs.
HARNESS_SOURCES = ("clinical_core/calibration.py", "clinical_core/bands.py")
#: The migration gate and its trusted authority, whole: the claim rules, the registered case
#: mappings and the approved-family-default registry (P2H-0).
MIGRATION_SOURCES = ("clinical_core/migration.py", "clinical_core/migration_authority.py")
REPOSITORY = Path(__file__).resolve().parents[1]


def _source_bytes(path: str) -> bytes:
    return (REPOSITORY / path).read_bytes()


def scenario_inputs() -> dict:
    """P2G-1: what the harness takes from the family engine, materialized.

    Per GI case, the canonical arrival anchors, and per scenario the contributors the core
    runs, the orders as the engine executed them and the engine's snapshots (C reads them).
    A change anywhere that alters an input -- including a core constant the adapter reads --
    shows up here even if no listed source changed.
    """
    from .legacy_adapter import contributors_from_legacy
    from .shadow import SCENARIOS
    inputs = {}
    for case in gi_reference.GI_CASES:
        runs = {}
        for name, spec in SCENARIOS.items():
            legacy = _legacy_run(case, spec)
            runs[name] = {"contributors": [repr(item) for item in contributors_from_legacy(legacy)],
                          "orders": [repr(order) for order in legacy.orders], "snapshots": list(legacy.snapshots)}
        inputs[case] = {"arrival_anchors": gi_reference.canonical_anchors(case).to_dict(), "scenarios": runs}
    return inputs


def digest_components() -> dict[str, str]:
    """P2G-1: the calibration freeze, component by component, so a change says where it is.

    - rules: the rule table, the check registry, the groups and every harness function a check
      or the GI acceptance calls;
    - harness_sources: the harness files whole (HARNESS_SOURCES), so a check's binding, a design
      default or a probe contributor cannot change without the digest;
    - migration_sources: the migration gate and its trusted registries whole (MIGRATION_SOURCES);
    - authority_registries: the trusted authority policies, case mappings and approved defaults
      as loaded (``migration_authority.registry_content``, P2H-1);
    - bands: the registry's band points, the GI case bands, the probe arrival and the levels;
    - gi_reference: the GI reference mapping (inventory, case bands, candidate anchors);
    - scenarios: the GI scenario definitions;
    - input_path_sources: every file of the family-engine path (INPUT_PATH_SOURCES);
    - input_adapter_sources: the order adapter (INPUT_ADAPTER_SOURCES);
    - scenario_inputs: the materialized inputs (``scenario_inputs``).
    The core model the calibration evaluates is not part of the freeze: the Phase-2 tests and
    the golden hold it.
    """
    import hashlib
    import inspect
    from . import migration_authority
    from .bands import ARRIVAL as probe_arrival
    from .shadow import SCENARIOS

    def sha(data) -> str:
        return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()

    def text(data) -> str:
        return json.dumps(data, sort_keys=True, default=repr)

    functions = (check_dl1_dl2_dl4, check_dl3, check_rr1, check_hr, _midpoint_arrivals, check_preload, _output,
                 check_congestion, check_pressure, check_collapse, check_demand, check_arrival_state, _run_case,
                 case_values, _level, gi_physiology, physiology, gi_candidates, acceptable, _expect, _debts, _excess,
                 peak_index, _legacy, _legacy_run)
    rules = {"rules": {name: asdict(rule) for name, rule in FROZEN_RULES.items()},
             "checks": {name: list(groups) for name, (_, groups) in CHECKS.items()},
             "groups": {name: [list(names), list(checks)] for name, (names, checks) in GROUPS.items()}}
    bands = {"points": {name: [str(point) for point in entry.points()] for name, entry in REGISTRY.items()},
             "case_bands": {case: {name: asdict(band) for name, band in gi_reference.case_bands(case).items()}
                            for case in gi_reference.GI_CASES},
             "probe_arrival": {name: str(value) for name, value in probe_arrival.items()}, "levels": list(LEVELS)}
    scenarios = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
                 for name, spec in SCENARIOS.items()}
    return {
        "rules": sha(text(rules) + "".join(inspect.getsource(function) for function in functions)),
        "bands": sha(text(bands)),
        "harness_sources": sha(text({path: sha(_source_bytes(path)) for path in HARNESS_SOURCES})),
        "migration_sources": sha(text({path: sha(_source_bytes(path)) for path in MIGRATION_SOURCES})),
        "authority_registries": sha(text(migration_authority.registry_content())),
        "gi_reference": sha(_source_bytes(GI_REFERENCE_SOURCE)),
        "scenarios": sha(text(scenarios)),
        "input_path_sources": sha(text({path: sha(_source_bytes(path)) for path in INPUT_PATH_SOURCES})),
        "input_adapter_sources": sha(text({path: sha(_source_bytes(path)) for path in INPUT_ADAPTER_SOURCES})),
        "scenario_inputs": sha(text(scenario_inputs())),
    }


def frozen_digest() -> str:
    """The digest of everything acceptance and its inputs depend on (``digest_components``). Any
    later change shows up and has to be recorded with its reason."""
    import hashlib
    return hashlib.sha256(json.dumps(digest_components(), sort_keys=True).encode("utf-8")).hexdigest()


def physiology(profile_values: Mapping[str, Any], checks=None, **context) -> dict:
    """A: every qualitative constraint, pass or fail with its reason. Never reads the family engine."""
    try:
        profile = replace(DEFAULT_PROFILE, **profile_values)
    except CoreInvariantError as error:
        return {"valid": False, "failed": {"profile": f"invalid profile: {error}"}, "passed": []}
    failed, passed = {}, []
    for name in (checks or CHECKS):
        check, _ = CHECKS[name]
        try:
            check(profile, **context)
            passed.append(name)
        except Failed as reason:
            failed[name] = str(reason)
        except (UnresolvedBoundary, CoreInvariantError) as error:
            failed[name] = f"{name}: the probe reached an invalid state: {error}"
    return {"valid": not failed, "failed": failed, "passed": passed}


# Group sweeps (A only) -------------------------------------------------------------------------

GROUPS = {
    "D/lactate": (("debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_per_output_deficit",
                   "lactate_clearance_tau_min"), ("DL1/DL2/DL4", "DL3")),
    "RR": (("rr_per_lactate", "rr_metabolic_max", "rr_ventilatory_floor", "lactate_clearance_tau_min"), ("RR1",)),
    "sympathetic": (("sympathetic_per_pressure_deficit", "sympathetic_per_debt", "sympathetic_decay_tau_min"),
                    ("HR1-HR4",)),
    "preload": (("preload_curve_scale_ml", "arrival_preload_fraction", "pump_preload_coupling",
                 "afterload_sensitivity"), ("PL1-PL3",)),
    "congestion": (("preload_curve_scale_ml", "congestion_preload_knee", "congestion_per_excess_preload",
                    "lung_water_clearance_tau_min"), ("PL4",)),
    "pressure": (("low_output_pressure_knee", "sbp_per_pressure_deficit", "dbp_per_pressure_deficit"), ("PR1-PR3",)),
    "collapse": (("collapse_output_threshold", "collapse_burden_per_minute", "collapse_burden_limit",
                  "collapse_repayment_tau_min", "collapse_terminal_rhythm"), ("CO1/CO2",)),
    "demand": (("spo2_per_fio2",), ("DM1",)),
}


def group_sweep(group: str, quick: bool = False) -> dict:
    """Every combination of the group's candidate points (A only); other parameters canonical."""
    names, checks = GROUPS[group]
    axes = [REGISTRY[name].points() for name in names]
    if quick:
        axes = [axis[:1] + axis[-1:] if len(axis) > 1 else axis for axis in axes]
    rows = []
    for values in itertools.product(*axes):
        candidate = dict(zip(names, values))
        result = physiology(candidate, checks)
        rows.append({"values": candidate, **result})
    accepted = [row for row in rows if row["valid"]]
    region = {name: sorted({row["values"][name] for row in accepted}) for name in names}
    reasons: dict[str, int] = {}
    for row in rows:
        for reason in row["failed"].values():
            reasons[reason] = reasons.get(reason, 0) + 1
    return {"group": group, "parameters": list(names), "checks": list(checks), "evaluated": len(rows),
            "rejected": len(rows) - len(accepted), "rejection_reasons": reasons, "accepted_region": region,
            "rows": rows}


# GI candidate sets (A, B and C apart) ---------------------------------------------------------

LEVELS = ("lower", "midpoint", "upper")


@dataclass(frozen=True)
class GICandidate:
    """One GI candidate set: kinetics, and for both cases the same level of each case band."""

    profile: Mapping[str, float]
    excess: str = "midpoint"
    intrinsic: str = "midpoint"
    preload: str = "midpoint"
    debt: str = "midpoint"
    delivery: str = "midpoint"

    def key(self) -> str:
        values = ",".join(f"{name}={value:g}" for name, value in sorted(self.profile.items()))
        return (f"{values};excess={self.excess};intrinsic={self.intrinsic};preload={self.preload};"
                f"debt={self.debt};delivery={self.delivery}")


def _level(band, level):
    return {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper}[level]


def case_values(case: str, candidate: GICandidate) -> dict:
    """The candidate's declared arrival values for one case, each from its own independent band."""
    bands = gi_reference.case_bands(case)
    return {"arrival_lactate_excess": _level(bands["arrival_lactate_excess"], candidate.excess),
            "arrival_oxygen_debt": _level(bands["arrival_oxygen_debt"], candidate.debt),
            "arrival_delivery_ratio": _level(bands["arrival_delivery_ratio"], candidate.delivery),
            "intrinsic_sinus_rate": _level(bands["intrinsic_sinus_rate"], candidate.intrinsic),
            "preload_fraction": _level(bands["preload_fraction"], candidate.preload),
            "metabolic_demand_baseline": 1.0}


_LEGACY: dict = {}
_RUNS: dict = {}


def _scenario_key(variant: str, spec: Mapping) -> tuple:
    """A scenario's identity is its content, not its name: a changed definition is never served stale."""
    return variant, spec["minutes"], tuple(sorted(spec["orders"].items()))


def _legacy_run(variant: str, spec: Mapping):
    """The family engine's run of one scenario, computed once per content (it does not depend on the core)."""
    from .legacy_adapter import run_legacy
    key = _scenario_key(variant, spec)
    if key not in _RUNS:
        _RUNS[key] = run_legacy(variant, spec["orders"], spec["minutes"])
    return _RUNS[key]


def _legacy(variant: str, scenario: str):
    """The family engine's run and its adapted inputs, computed once (they do not depend on the core)."""
    from .legacy_adapter import contributors_from_legacy
    from .shadow import SCENARIOS
    spec = SCENARIOS[scenario]
    key = _scenario_key(variant, spec)
    if key not in _LEGACY:
        legacy = _legacy_run(variant, spec)
        _LEGACY[key] = (legacy, contributors_from_legacy(legacy), spec["minutes"])
    return _LEGACY[key]


TRACKED = ("sbp", "pulse_rate_bpm", "respiratory_rate", "lactate", "crt_s")


def _run_case(case, scenario, anchors, profile):
    legacy, contributors, minutes = _legacy(case, scenario)
    return legacy, run(anchors, contributors, minutes, profile)


def gi_trajectories(candidate: GICandidate, scenarios=None) -> tuple[dict, dict]:
    """B and C for one candidate: what the GI runs show, and how far they are from the family engine."""
    from .comparison import compare, mismatching, summarize
    from .shadow import SCENARIOS
    profile = replace(DEFAULT_PROFILE, **candidate.profile)
    trajectories, legacy_diff = {}, {}
    for case in gi_reference.GI_CASES:
        anchors = gi_reference.candidate_anchors(case, case_values(case, candidate))
        for scenario in scenarios or SCENARIOS:
            key = f"{case}/{scenario}"
            try:
                legacy, core = _run_case(case, scenario, anchors, profile)
            except (UnresolvedBoundary, CoreInvariantError) as error:
                trajectories[key] = {"stopped": str(error)}
                continue
            derived = core.derived()
            trajectories[key] = {
                "end": {name: getattr(derived[-1], name) for name in TRACKED},
                "range": {name: [min(getattr(item, name) for item in derived if item.pulse_present),
                                 max(getattr(item, name) for item in derived if item.pulse_present)]
                          for name in TRACKED},
                "lactate_below_arrival_at_end": derived[-1].lactate < anchors.lactate,
                "pulse_at_end": derived[-1].pulse_present}
            summary = summarize(compare(legacy.snapshots, core.states, derived))
            legacy_diff[key] = {name: {"mismatched": summary[name]["mismatched"],
                                       "max_abs_diff": summary[name].get("max_abs_diff")}
                                for name in mismatching(summary)}
    return trajectories, legacy_diff


def check_arrival_state(profile: CoreProfile, candidate: GICandidate) -> None:
    """AC1 and AC2 (frozen): arrival-state consistency of the declared GI arrival, never steady state."""
    for case in gi_reference.GI_CASES:
        anchors = gi_reference.candidate_anchors(case, case_values(case, candidate))
        check_arrival_reconstruction(anchors, profile)            # AC1 (raises CoreInvariantError)
        _, untreated = _run_case(case, "untreated_60", anchors, profile)
        _, treated = _run_case(case, "definitive_management", anchors, profile)
        late_u, late_t = untreated.derived()[60], treated.derived()[60]
        _expect(treated.states[60].D <= untreated.states[60].D + 1e-9 and late_t.lactate <= late_u.lactate + 1e-9,
                f"AC2 ({case}): definitive management left D or lactate above the untreated run at minute 60")
        for trajectory in (untreated, treated):
            _expect(min(state.D for state in trajectory.states) >= 0
                    and min(state.aux.lactate_excess_mmol_l for state in trajectory.states) >= 0,
                    f"AC2 ({case}): negative D or lactate excess")
            rates = [item.pulse_rate_bpm for item in trajectory.derived() if item.pulse_present]
            _expect(min(rates) >= anchors.intrinsic_sinus_rate - 1e-9, f"AC2 ({case}): HR below intrinsic")


def gi_physiology(candidate: GICandidate, cache: dict | None = None) -> dict:
    """A for a GI candidate: the frozen mechanism rules at its kinetics, and AC1/AC2 on both GI arrivals.

    Never reads the family engine's golden, and never the pre-arrival plausibility probe.
    """
    profile = replace(DEFAULT_PROFILE, **candidate.profile)
    values = {case: case_values(case, candidate) for case in gi_reference.GI_CASES}
    arrivals = {case: gi_reference.candidate_anchors(case, values[case]) for case in gi_reference.GI_CASES}
    failed, passed = {}, []
    try:
        check_arrival_state(profile, candidate)
        passed.append("AC1/AC2")
    except (Failed, CoreInvariantError) as error:
        failed["AC1/AC2"] = str(error)
    # The cache key holds every declared value of both cases, so a probe never reuses another arrival.
    key = (tuple(sorted(candidate.profile.items())),
           tuple((case, tuple(sorted(values[case].items()))) for case in gi_reference.GI_CASES))
    cache = {} if cache is None else cache
    if key not in cache:
        cache[key] = physiology(candidate.profile, ("DL1/DL2/DL4", "DL3", "RR1", "HR1-HR4"), arrivals=arrivals)
    failed.update(cache[key]["failed"])
    passed.extend(cache[key]["passed"])
    return {"valid": not failed, "failed": failed, "passed": passed}


def gi_diagnostics(candidate: GICandidate) -> dict:
    """Reported, never used for acceptance: arrival dynamics (not required to be steady) and the
    SYNTHETIC_PLAUSIBILITY_PROBE of a constant pre-arrival history."""
    profile = replace(DEFAULT_PROFILE, **candidate.profile)
    rows = {}
    for case in gi_reference.GI_CASES:
        values = case_values(case, candidate)
        anchors = gi_reference.candidate_anchors(case, values)
        first = run(anchors, (), 1, profile).states
        rows[case] = {
            "arrival_dD_per_min": first[1].D - first[0].D,
            "arrival_dlactate_per_min": first[1].aux.lactate_excess_mmol_l - first[0].aux.lactate_excess_mmol_l,
            "steady_state_required": False,
            "plausibility_probe": {"status": gi_reference.SYNTHETIC_PLAUSIBILITY_PROBE,
                                   "feasible_histories": len(gi_reference.pre_arrival_plausibility_probe(
                                       values["arrival_lactate_excess"], profile))}}
    return rows


def gi_candidates(quick: bool = False) -> list[GICandidate]:
    """The frozen design: kinetics x case-band levels, every level from each band's own rationale."""
    names = ("debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")
    kinetics = [REGISTRY[name].points() for name in names]
    if quick:
        kinetics = [axis[:1] + axis[-1:] for axis in kinetics]
        references = [{}]
    else:
        arrival = [("lower", "upper"), ("midpoint", "midpoint"), ("upper", "lower"), ("lower", "lower"),
                   ("upper", "upper")]       # (debt, delivery): none, middle, severe, and both mixed corners
        references = [{"excess": excess, "intrinsic": intrinsic, "debt": debt, "delivery": delivery}
                      for excess in LEVELS for intrinsic in LEVELS for debt, delivery in arrival]
    candidates = [GICandidate(dict(zip(names, values)), **reference)
                  for values in itertools.product(*kinetics) for reference in references]
    if not quick:
        middle = {name: REGISTRY[name].midpoint for name in names}
        candidates.extend(GICandidate(middle, preload=preload) for preload in ("lower", "upper"))
    return candidates


def acceptable(results: list[dict]) -> list[str]:
    """The candidates that pass every frozen qualitative rule. Reads only A, never B, C or diagnostics."""
    return [result["key"] for result in results if result["physiology"]["valid"]]


def gi_sweep(quick: bool = False, scenarios=None) -> dict:
    cache: dict = {}
    results = []
    for candidate in gi_candidates(quick):
        physiology_result = gi_physiology(candidate, cache)
        trajectories, legacy_diff = gi_trajectories(candidate, scenarios)
        results.append({"key": candidate.key(), "candidate": asdict(candidate), "physiology": physiology_result,
                        "trajectories": trajectories, "legacy_difference": legacy_diff,
                        "diagnostics": gi_diagnostics(candidate)})
    accepted = set(acceptable(results))
    reasons: dict[str, int] = {}
    for result in results:
        for reason in result["physiology"]["failed"].values():
            reasons[reason] = reasons.get(reason, 0) + 1
    return {"evaluated": len(results), "accepted": len(accepted), "rejected": len(results) - len(accepted),
            "rejection_reasons": reasons, "results": results, "accepted_keys": sorted(accepted)}


def trajectory_ranges(sweep: dict, accepted_only: bool = True) -> dict:
    """B summarized: across candidates, the range of each tracked value at the end of each run."""
    ranges: dict = {}
    for result in sweep["results"]:
        if accepted_only and result["key"] not in sweep["accepted_keys"]:
            continue
        for key, entry in result["trajectories"].items():
            if "end" not in entry:
                ranges.setdefault(key, {}).setdefault("stopped", 0)
                ranges[key]["stopped"] += 1
                continue
            for name, value in entry["end"].items():
                low, high = ranges.setdefault(key, {}).get(name, (value, value))
                ranges[key][name] = (min(low, value), max(high, value))
    return ranges


def legacy_ranges(sweep: dict, accepted_only: bool = True) -> dict:
    """C summarized: across candidates, the range of mismatching minutes per variable (diagnostic only)."""
    ranges: dict = {}
    for result in sweep["results"]:
        if accepted_only and result["key"] not in sweep["accepted_keys"]:
            continue
        totals: dict[str, int] = {}
        for entry in result["legacy_difference"].values():
            for name, values in entry.items():
                totals[name] = totals.get(name, 0) + values["mismatched"]
        for name, total in totals.items():
            low, high = ranges.get(name, (total, total))
            ranges[name] = (min(low, total), max(high, total))
    return ranges


def registry_report() -> dict:
    rows = {}
    for name, entry in REGISTRY.items():
        row = asdict(entry)
        if entry.per_case:
            row["per_case"] = {case: asdict(gi_reference.case_bands(case)[name]) for case in gi_reference.GI_CASES}
        rows[name] = row
    return rows


def report(quick: bool = False) -> dict:
    # The freeze the sweep runs under, recorded with its results (P2G-1).
    freeze = {"digest": frozen_digest(), "components": digest_components()}
    groups = {group: group_sweep(group, quick) for group in GROUPS}
    sweep = gi_sweep(quick)
    return {"freeze": freeze, "delivery_model": DELIVERY_MODEL, "delivery_probes": delivery_probes(),
            "hypoxaemia_trajectory_probe": hypoxaemia_trajectory_probe(), "registry": registry_report(),
            "status_counts": {status: sum(entry.status == status for entry in REGISTRY.values())
                              for status in STATUSES},
            "group_sweeps": {group: {key: value for key, value in result.items() if key != "rows"}
                             for group, result in groups.items()},
            "gi_sweep": {key: value for key, value in sweep.items() if key != "results"},
            "gi_trajectory_ranges_accepted": trajectory_ranges(sweep),
            "gi_legacy_mismatch_ranges_accepted": legacy_ranges(sweep),
            "gi_results": sweep["results"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true", help="corners only")
    parser.add_argument("--out", type=Path, help="write the full report as JSON here (outside the repository)")
    args = parser.parse_args(argv)
    data = report(args.quick)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "calibration_report.json").write_text(json.dumps(data, indent=1, default=str) + "\n",
                                                          encoding="utf-8")
    summary = {key: value for key, value in data.items() if key not in ("gi_results", "registry")}
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
