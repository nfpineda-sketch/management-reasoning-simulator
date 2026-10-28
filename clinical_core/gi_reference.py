"""P2F-2..5: the two GI cases' repository truth and their candidate physiological reference states.

    python -m clinical_core.gi_reference

Nothing here is a mapping the core uses by default. Three kinds of statement are kept apart
(``reference_mapping``):
- A. repository truth: the inventory reads only what the repository authors, cites the exact
  line, and says which core parameter each item constrains;
- B. candidate inference: bands with their own rationale, CANDIDATE, never faculty-approved,
  never the canonical shadow defaults, never chosen to match the family engine;
- C. faculty decision required: every parameter the case does not state.
A run that uses a candidate declares it as ``synthetic_probe``, so the migration gate keeps
blocking it. Arrival is not assumed to be in steady state, and the D -> lactate gain is not
inferred from the arrival lactate.
"""
from __future__ import annotations

import argparse
import functools
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .derived import DEFAULT_PROFILE, CoreProfile

GI_CASES = ("gi_bleed_57m", "gi_bleed_72f")
CANDIDATE = "CANDIDATE"
_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class InventoryItem:
    """One authored arrival fact: value, exact source line, and what it constrains in the core.

    ``snippet`` must appear on the cited line (checked); ``path`` reads the same value from
    the case bank (checked) when the value is structured data.
    """

    case: str
    item: str
    value: Any
    source: str
    snippet: str
    constrains: tuple[str, ...]
    note: str = ""
    path: tuple[str, ...] = ()


def _items(case, rows):
    return tuple(InventoryItem(case, *row) for row in rows)


#: P2F-2. Repository truth only: a fact the case does not state is recorded as not stated.
INVENTORY: tuple[InventoryItem, ...] = _items("gi_bleed_57m", (
    ("rhythm", "Sinus tachycardia", "clinical_cases.py:211", '"rhythm": ("Sinus tachycardia" if hr > 100',
     ("intrinsic_sinus_rate",), "derived by the bank from HR > 100, not authored separately", ("observable", "rhythm")),
    ("hr", 124, "clinical_cases.py:881", "_o = _observable(88, 54, 124, 97, 26",
     ("intrinsic_sinus_rate", "arrival sympathetic contribution"), "upper bound of the intrinsic rate",
     ("observable", "hr")),
    ("sbp", 88, "clinical_cases.py:881", "_o = _observable(88, 54, 124", ("pressure anchor",), "",
     ("observable", "sbp")),
    ("dbp", 54, "clinical_cases.py:881", "_o = _observable(88, 54", ("pressure anchor", "pressure gains and knee"),
     "pulse pressure 34 mmHg bounds (sbp gain - dbp gain) x (1 - knee)", ("observable", "dbp")),
    ("map", "65.3 (derived, not authored)", "clinical_cases.py:881", "_o = _observable(88, 54", (),
     "(SBP + 2 DBP) / 3 of the authored values"),
    ("spo2", 97, "clinical_cases.py:881", "_observable(88, 54, 124, 97", ("delivery saturation reference",),
     "above the hypoxaemia threshold: no hypoxaemic drive at arrival", ("observable", "spo2")),
    ("respiratory_rate", 26, "clinical_cases.py:881", "_observable(88, 54, 124, 97, 26",
     ("rr_per_lactate", "rr_ventilatory_floor"),
     "candidate inference: with the ABG, a metabolic share of RR at arrival",
     ("observable", "respiratory_rate")),
    ("abg", "pH 7.37, PaCO2 31, HCO3 17.3, PaO2 91 on FiO2 21%", "clinical_cases.py:901", "abg=(7.37, 31, 91)",
     ("rr_per_lactate",), "HCO3 is computed by the bank from pH and PaCO2 (clinical_cases.py:251), not authored; "
     "candidate inference: compensated metabolic acidosis, consistent with a lactate-driven ventilatory share"),
    ("mental_status", "Alert", "clinical_cases.py:202", 'mental="Alert"', ("metabolic_demand_baseline",),
     "the bank default (the case passes none); no agitation stated", ("observable", "mental_status")),
    ("neurological_exam", "Awake and oriented, reporting persistent faintness", "clinical_cases.py:899",
     "Awake and oriented, reporting persistent faintness", ("metabolic_demand_baseline",), "no agitation"),
    ("crt_s", 5, "clinical_cases.py:881", "crt=5", ("arrival_delivery_ratio", "preload_fraction"),
     "candidate inference: with cool extremities and impaired perfusion, low output at arrival", ("observable", "crt")),
    ("extremities", "Cool", "clinical_cases.py:881", 'extremities="Cool"', ("arrival_delivery_ratio",), "",
     ("observable", "extremities")),
    ("peripheral_perfusion", "impaired", "clinical_cases.py:882", 'perfusion="impaired"',
     ("arrival_delivery_ratio",), "", ("observable", "peripheral_perfusion")),
    ("hb_g_dl", 6.7, "clinical_cases.py:900", "lactate=4.4, hemoglobin=6.7", ("arrival_delivery_ratio",),
     "candidate inference: about half a normal content, arrival delivery below the reference",
     ("engine", "baseline_hemoglobin")),
    ("lactate_mmol_l", 4.4, "clinical_cases.py:900", "lactate=4.4", ("arrival_lactate_excess",),
     "fixes the sum of the clearance baseline and the clearable excess, not the split; it constrains neither the "
     "D->lactate gain nor the arrival debt",
     ("engine", "baseline_lactate")),
    ("glucose_mg_dl", 118, "clinical_cases.py:882", "temperature=36.5, glucose=118", (),
     "no hypoglycaemic drive", ("observable", "glucose_mg_dl")),
    ("temperature_c", 36.5, "clinical_cases.py:882", "temperature=36.5", ("metabolic_demand_baseline",),
     "afebrile: no fever modifier", ("observable", "temperature_c")),
    ("wbc_k_ul", 11.1, "clinical_cases.py:900", "wbc=11.1", ("metabolic_demand_baseline",),
     "no sepsis stated; WBC alone does not make one"),
    ("pain", "mild epigastric burning; arrival pain 2/10 is the family default", "analgesia.py:22",
     '"gi_bleed": 2.0', ("metabolic_demand_baseline",), "the case authors no pain score (clinical_cases.py:887 "
     "states mild burning); no marked pain"),
    ("oxygen_support", "room air (FiO2 0.21)", "family_engine.py:973", '"oxygen_fio2": .21', ("fio2 anchor",),
     "the engine starts every case on room air; the ABG is on FiO2 21% (clinical_cases.py:253)"),
    ("pocus_lv", "small cavity, hyperdynamic, near-obliteration in systole", "clinical_cases.py:154",
     "Small cavity with hyperdynamic contraction", ("preload_fraction", "pump_reserve"),
     "candidate inference: severe underfilling with a preserved pump"),
    ("pocus_ivc", "0.9 cm, near-complete inspiratory collapse", "clinical_cases.py:155",
     'ivc="0.9 cm; near-complete inspiratory collapse"', ("preload_fraction",),
     "candidate inference: low on the preload curve"),
    ("lungs", "no B-lines; chest X-ray without oedema", "clinical_cases.py:903",
     "No focal consolidation or pulmonary edema", ("pump_reserve",),
     "the X-ray is authored here; 'no B-lines' is the _pocus default (clinical_cases.py:69, :83), which the case "
     "does not override; candidate inference: no arrival congestion (L = 0)"),
    ("troponin_ng_l", "16 (upper reference 19)", "clinical_cases.py:903", "troponin=16", ("pump_reserve",),
     "no myocardial injury stated"),
    ("active_bleeding", "melena since yesterday; black tarry stool on rectal examination",
     "clinical_cases.py:890", "The dark stools began yesterday", ("haemorrhage source parameters",),
     "ongoing loss; the exact pre-arrival duration of hypoperfusion is not stated (near-faint this morning)"),
    ("medications", "ibuprofen most days for two weeks", "clinical_cases.py:889", "I have taken ibuprofen most days",
     ("beta_blockade",), "no beta-blocker is listed; the history does not state that none is taken"),
    ("comorbidities", "knee osteoarthritis; no known liver disease", "clinical_cases.py:888",
     "no known liver disease", ("lactate_clearance_tau_min",), "no hepatic impairment stated"),
    ("prehospital_therapy", "not stated", "clinical_cases.py:884", '"gi_bleed_57m", "gi_bleed", 57', (),
     "no fluids, blood or drugs before arrival are authored"),
    ("potassium", "4.1 (bank default, not authored by the case)", "clinical_cases.py:297",
     "potassium=4.1", ("k anchor",), "the case passes no potassium"),
)) + _items("gi_bleed_72f", (
    ("rhythm", "Sinus tachycardia", "clinical_cases.py:211", '"rhythm": ("Sinus tachycardia" if hr > 100',
     ("intrinsic_sinus_rate",), "derived by the bank from HR > 100", ("observable", "rhythm")),
    ("hr", 112, "clinical_cases.py:910", "_o = _observable(98, 62, 112, 96, 24",
     ("intrinsic_sinus_rate", "arrival sympathetic contribution"), "upper bound of the intrinsic rate",
     ("observable", "hr")),
    ("sbp", 98, "clinical_cases.py:910", "_o = _observable(98, 62, 112", ("pressure anchor",), "",
     ("observable", "sbp")),
    ("dbp", 62, "clinical_cases.py:910", "_o = _observable(98, 62", ("pressure anchor", "pressure gains and knee"),
     "pulse pressure 36 mmHg", ("observable", "dbp")),
    ("map", "74.0 (derived, not authored)", "clinical_cases.py:910", "_o = _observable(98, 62", (), ""),
    ("spo2", 96, "clinical_cases.py:910", "_observable(98, 62, 112, 96", ("delivery saturation reference",),
     "no hypoxaemic drive at arrival", ("observable", "spo2")),
    ("respiratory_rate", 24, "clinical_cases.py:910", "_observable(98, 62, 112, 96, 24",
     ("rr_per_lactate", "rr_ventilatory_floor"), "", ("observable", "respiratory_rate")),
    ("abg", "pH 7.40, PaCO2 33, HCO3 19.8, PaO2 84 on FiO2 21%", "clinical_cases.py:930", "abg=(7.40, 33, 84)",
     ("rr_per_lactate",), "HCO3 is computed by the bank (clinical_cases.py:251), not authored; candidate inference: "
     "compensated metabolic acidosis, milder"),
    ("mental_status", "Alert", "clinical_cases.py:202", 'mental="Alert"', ("metabolic_demand_baseline",),
     "the bank default (the case passes none)", ("observable", "mental_status")),
    ("neurological_exam", "Alert, oriented and moving all limbs symmetrically", "clinical_cases.py:928",
     "Alert, oriented and moving all limbs", ("metabolic_demand_baseline",), "no agitation"),
    ("crt_s", 4, "clinical_cases.py:910", "crt=4", ("arrival_delivery_ratio", "preload_fraction"), "",
     ("observable", "crt")),
    ("extremities", "Cool", "clinical_cases.py:910", 'extremities="Cool"', ("arrival_delivery_ratio",), "",
     ("observable", "extremities")),
    ("peripheral_perfusion", "impaired", "clinical_cases.py:911", 'perfusion="impaired"',
     ("arrival_delivery_ratio",), "", ("observable", "peripheral_perfusion")),
    ("hb_g_dl", 6.4, "clinical_cases.py:929", "lactate=3.4, hemoglobin=6.4", ("arrival_delivery_ratio",), "",
     ("engine", "baseline_hemoglobin")),
    ("lactate_mmol_l", 3.4, "clinical_cases.py:929", "lactate=3.4", ("arrival_lactate_excess",),
     "fixes the sum, not the split; it constrains neither the D->lactate gain nor the arrival debt",
     ("engine", "baseline_lactate")),
    ("glucose_mg_dl", 130, "clinical_cases.py:911", "temperature=36.6, glucose=130", (), "",
     ("observable", "glucose_mg_dl")),
    ("temperature_c", 36.6, "clinical_cases.py:911", "temperature=36.6", ("metabolic_demand_baseline",), "afebrile",
     ("observable", "temperature_c")),
    ("wbc_k_ul", 10.3, "clinical_cases.py:929", "wbc=10.3", ("metabolic_demand_baseline",), ""),
    ("pain", "little abdominal pain; arrival pain 2/10 is the family default", "analgesia.py:22", '"gi_bleed": 2.0',
     ("metabolic_demand_baseline",), "the case authors no pain score (clinical_cases.py:916)"),
    ("oxygen_support", "room air (FiO2 0.21)", "family_engine.py:973", '"oxygen_fio2": .21', ("fio2 anchor",), ""),
    ("pocus_lv", "hyperdynamic contraction", "clinical_cases.py:156", '_pocus(lv="Hyperdynamic contraction"',
     ("preload_fraction", "pump_reserve"), "candidate inference: underfilling with a preserved pump"),
    ("pocus_ivc", "1.1 cm, >50% inspiratory collapse", "clinical_cases.py:156", 'ivc="1.1 cm; >50% inspiratory',
     ("preload_fraction",), "candidate inference: low on the preload curve, less than 57m"),
    ("lungs", "no B-lines; no acute cardiopulmonary abnormality on X-ray", "clinical_cases.py:932",
     "No acute cardiopulmonary abnormality", ("pump_reserve",),
     "the X-ray is authored here; 'no B-lines' is the _pocus default (clinical_cases.py:69, :83); candidate "
     "inference: no arrival congestion"),
    ("troponin_ng_l", "17 (upper reference 19)", "clinical_cases.py:932", "troponin=17", ("pump_reserve",), ""),
    ("active_bleeding", "melena for three days with another episode this morning", "clinical_cases.py:921",
     "I have passed black, sticky stool for three days", ("haemorrhage source parameters",),
     "fatigue four days, lightheadedness worse today: the hypoperfusion duration is not stated"),
    ("medications", "naproxen recently; no gastroprotection", "clinical_cases.py:918",
     "I have recently been taking naproxen", ("beta_blockade",), "no beta-blocker is listed; not stated as none"),
    ("comorbidities", "previous peptic ulcer; osteoarthritis", "clinical_cases.py:913",
     '"gi_bleed_72f", "gi_bleed", 72', ("lactate_clearance_tau_min",), "liver disease is not mentioned either way"),
    ("prehospital_therapy", "not stated", "clinical_cases.py:913", '"gi_bleed_72f", "gi_bleed", 72', (),
     "no fluids, blood or drugs before arrival are authored"),
    ("potassium", "4.1 (bank default, not authored by the case)", "clinical_cases.py:297", "potassium=4.1",
     ("k anchor",), ""),
))


def verify_inventory() -> list[str]:
    """Problems with the inventory: a cited line without its snippet, or a value the bank no longer holds."""
    import clinical_cases
    problems, lines = [], {}
    for entry in INVENTORY:
        name, number = entry.source.split(":")
        text = lines.setdefault(name, (_ROOT / name).read_text(encoding="utf-8").splitlines())
        if entry.snippet not in text[int(number) - 1]:
            problems.append(f"{entry.case} {entry.item}: {entry.source} does not contain {entry.snippet!r}")
        if entry.path:
            value: Any = clinical_cases.variant_by_id(entry.case)
            for key in entry.path:
                value = value[key]
            if value != entry.value:
                problems.append(f"{entry.case} {entry.item}: the bank holds {value!r}, the inventory {entry.value!r}")
    return problems


def authored(case: str, item: str):
    return next(entry.value for entry in INVENTORY if entry.case == case and entry.item == item)


@dataclass(frozen=True)
class Band:
    """A candidate band: never approved here, and never the canonical value."""

    name: str
    lower: float
    upper: float
    midpoint: float | None
    units: str
    rationale: str
    evidence: tuple[str, ...]
    status: str = CANDIDATE

    def __post_init__(self):
        if self.lower > self.upper or (self.midpoint is not None and not self.lower <= self.midpoint <= self.upper):
            raise ValueError(f"{self.name}: a band is lower <= midpoint <= upper")

    def points(self) -> tuple[float, ...]:
        return tuple(sorted({self.lower, self.upper} | ({self.midpoint} if self.midpoint is not None else set())))


#: A baseline (non-shock) lactate taken as 0.8 (the adopted floor) to 2.0 mmol/L (upper normal).
BASELINE_LACTATE = (0.8, 1.0, 2.0)
#: The resting adult sinus rate range used for the intrinsic (non-acute resting) rate.
RESTING_HR = (60.0, 80.0, 100.0)
#: Pre-arrival durations of constant hypoperfusion considered: wide, because neither case states it.
PRE_ARRIVAL_MINUTES = (30, 60, 120, 240, 480, 720)


def _source(case, item):
    return next(entry.source for entry in INVENTORY if entry.case == case and entry.item == item)


def lactate_excess_band(case: str) -> Band:
    lactate = authored(case, "lactate_mmol_l")
    low, mid, high = BASELINE_LACTATE
    return Band("arrival_lactate_excess", round(lactate - high, 6), round(lactate - low, 6), round(lactate - mid, 6),
                "mmol/L", "arrival lactate less a non-shock clearance baseline of 0.8-2.0 mmol/L (the adopted floor "
                "to the upper normal); the baseline is not stated by the case",
                (_source(case, "lactate_mmol_l"), _source(case, "comorbidities")))


def intrinsic_hr_band(case: str) -> Band:
    hr = authored(case, "hr")
    low, mid, high = RESTING_HR
    return Band("intrinsic_sinus_rate", low, min(high, hr), min(mid, hr), "bpm",
                "the patient's non-acute resting sinus rate (not the pharmacological intrinsic rate under full "
                "autonomic blockade); resting adult range, at most the observed arrival HR; no baseline HR, rate "
                "control or beta-blocker is authored", (_source(case, "hr"), _source(case, "medications")))


def sympathetic_band(case: str, profile: CoreProfile = DEFAULT_PROFILE, beta_blockade: float = 0.0) -> Band:
    hr, intrinsic = authored(case, "hr"), intrinsic_hr_band(case)
    gain = profile.hr_per_sympathetic_drive * (1.0 - beta_blockade)
    return Band("arrival_sympathetic_drive", (hr - intrinsic.upper) / gain, (hr - intrinsic.lower) / gain,
                (hr - intrinsic.midpoint) / gain, "drive units (bpm / chronotropic gain)",
                f"observed HR {hr} less the intrinsic band, over {gain:g} bpm per unit of drive; never negative",
                (_source(case, "hr"),))


def demand_band(case: str) -> Band:
    return Band("metabolic_demand_baseline", 1.0, 1.0, 1.0, "units of the delivery that meets it",
                "uncomplicated haemorrhage: afebrile, alert, mild pain (family default), no sepsis or seizure "
                "stated, so no modifier; the baseline is 1 by the definition of the reference",
                tuple(_source(case, item) for item in ("temperature_c", "neurological_exam", "pain", "wbc_k_ul")))


PRELOAD_BANDS = {"gi_bleed_57m": (0.2, 0.35, 0.5), "gi_bleed_72f": (0.3, 0.45, 0.6)}


def preload_band(case: str) -> Band:
    low, mid, high = PRELOAD_BANDS[case]
    return Band("preload_fraction", low, high, mid, "position on the preload curve (0-1)",
                "POCUS: collapsing IVC and a small or hyperdynamic LV place arrival low on the curve; 57m's "
                "near-obliteration is lower than 72f's", (_source(case, "pocus_ivc"), _source(case, "pocus_lv")))


def pump_reserve_band(case: str) -> Band:
    return Band("pump_reserve", 0.7, 1.0, 1.0, "share of normal reserve",
                "hyperdynamic LV, no B-lines, no oedema, troponin below the reference: no evidence of reduced "
                "reserve; age is not used to infer it, so the lower bound is left for faculty",
                (_source(case, "pocus_lv"), _source(case, "lungs"), _source(case, "troponin_ng_l")))


#: P2F-6 (methodological correction): a reconstructed pre-arrival history is a synthetic
#: plausibility probe and nothing else. It is never a migration input, case truth, parameter
#: provenance or calibration evidence, and no band or acceptance rule is derived from it. The
#: simulation begins at the authored arrival; nothing claims the patient's preceding trajectory.
SYNTHETIC_PLAUSIBILITY_PROBE = "SYNTHETIC_PLAUSIBILITY_PROBE"


@dataclass(frozen=True)
class History:
    """A constant-deficit pre-arrival history that would end at a given lactate excess (diagnostic only)."""

    minutes: int
    deficit: float
    arrival_debt: float
    status: str = SYNTHETIC_PLAUSIBILITY_PROBE


def pre_arrival_plausibility_probe(excess: float, profile: CoreProfile = DEFAULT_PROFILE,
                                   minutes=PRE_ARRIVAL_MINUTES, max_deficit: float = 1.0) -> tuple[History, ...]:
    """SYNTHETIC_PLAUSIBILITY_PROBE: constant pre-arrival deficits that would end at ``excess``.

    From no debt and no excess, a constant deficit s accrues D and lactate with the core's own
    one-minute recurrences (P2I-2AC: while a deficit lasts D accrues and is not repaid); both are
    linear in s, so s is solved exactly per duration. An
    empty result says only that no such idealized history exists under these kinetics: the
    case may still begin with its declared debt and excess, which is why they are declared.
    """
    production = profile.lactate_per_output_deficit / (profile.debt_clearance_tau_min
                                                        * profile.lactate_clearance_tau_min)
    histories = []
    for total in minutes:
        debt = lactate = 0.0
        for _ in range(total):
            debt, lactate = (debt + profile.debt_per_delivery_deficit,
                             lactate + production * debt - lactate / profile.lactate_clearance_tau_min)
        if lactate <= 0.0:
            continue
        deficit = excess / lactate
        if deficit <= max_deficit:
            histories.append(History(total, deficit, deficit * debt))
    return tuple(histories)


def arrival_debt_band(case: str) -> Band:
    """Independent of any pre-arrival reconstruction and of the lactate kinetics (P2F-3)."""
    return Band("arrival_oxygen_debt", 0.0, 60.0, 20.0, "index-minutes",
                "the scale of the variable, not a fit: 0 (no accrued debt) to 60; neither case states a duration, "
                "so the band is wide and the same for both, and arrival need not be in steady state. Correction "
                "after the review (the values are unchanged, frozen before the sweep): the earlier wording derived "
                "the upper limit from a deficit of 0.5 for about two hours at the provisional repayment time (60 min), "
                "which gives about 26, not 60; 60 is the steady state of a total deficit (no delivery) at 60 min, and "
                "a debt above debt_per_delivery_deficit x demand x debt_clearance_tau_min (30 at tau 30) cannot "
                "accrue from any deficit. Whether to add such a reachability limit is a faculty decision",
                (_source(case, "lactate_mmol_l"), _source(case, "active_bleeding"), _source(case, "crt_s")))


def delivery_ratio_band(case: str) -> Band:
    """Independent of any pre-arrival reconstruction (P2F-1, P2F-6)."""
    return Band("arrival_delivery_ratio", 0.6, 1.0, 0.85, "units of the delivery that meets the reference demand",
                "impaired perfusion (delayed refill, cool extremities), hypotension and severe anaemia place arrival "
                "delivery at or below adequacy; 1 is a compensated arrival, 0.6 a severe ongoing deficit; the case "
                "does not measure delivery", (_source(case, "crt_s"), _source(case, "hb_g_dl"),
                                              _source(case, "peripheral_perfusion")))


def reference_band() -> Band:
    return Band("reference_preload_fraction", 0.6, 0.8, 0.7, "position (0-1)",
                "euvolemic reference; neither case states it; diagnostic only (no mechanism reads it)", ())


def case_bands(case: str, profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """B. CANDIDATE INFERENCE for one case: every band, each with its own rationale and evidence."""
    return {band.name: band for band in (lactate_excess_band(case), arrival_debt_band(case),
                                         delivery_ratio_band(case), intrinsic_hr_band(case),
                                         sympathetic_band(case, profile), demand_band(case), preload_band(case),
                                         pump_reserve_band(case), reference_band())}


#: C. Every candidate the case cannot supply by itself: a faculty decision (or an approved family
#: default, which is also a faculty decision) before any of them becomes a mapping.
FACULTY_DECISIONS = ("intrinsic_sinus_rate", "arrival_sympathetic_drive", "arrival_oxygen_debt",
                     "arrival_lactate_excess", "arrival_delivery_ratio", "metabolic_demand_baseline",
                     "preload_fraction", "pump_reserve", "beta_blockade")


def reference_mapping(case: str) -> dict:
    """P2F-5 (methodological correction): the three kinds of statement, kept apart.

    - A. repository truth: what the case states, with its line;
    - B. candidate inference: bands, never a mapping, whatever they are derived from;
    - C. faculty decision required: every parameter the case does not state itself.
    """
    return {"repository_truth": [asdict(item) for item in INVENTORY if item.case == case],
            "candidate_inference": {name: asdict(band) for name, band in case_bands(case).items()},
            "faculty_decision_required": list(FACULTY_DECISIONS)}


@functools.lru_cache(maxsize=None)
def canonical_anchors(case: str):
    """The case's anchors exactly as the shadow comparison builds them (every reference undeclared)."""
    from .legacy_adapter import anchors_from_legacy, run_legacy
    return anchors_from_legacy(run_legacy(case, {}, 0).arrival)


def candidate_anchors(case: str, values: dict):
    """The case's canonical anchors with candidate values declared as synthetic probes (never as case truth)."""
    base = canonical_anchors(case)
    return replace(base, **values, declared={**dict(base.declared), **{name: "synthetic_probe" for name in values}})


def report() -> dict:
    return {"inventory": [asdict(item) for item in INVENTORY], "inventory_problems": verify_inventory(),
            "mapping": {case: reference_mapping(case) for case in GI_CASES},
            "synthetic_plausibility_probe_at_canonical_kinetics": {
                case: [asdict(item) for item in pre_arrival_plausibility_probe(lactate_excess_band(case).midpoint)]
                for case in GI_CASES}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    print(json.dumps(report(), indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
