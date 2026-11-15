"""P3-315 .. P3-325: the ABSOLUTE scale of the GI bleed rate, reopened after the first human faculty review.

MODEL_ANALYSIS, nothing else. TEST-SIDE and READ-ONLY: it imports the certified shadow core, the frozen faculty evaluators of
``clinical_core.blood_constraints`` and the page-faithful harness of ``frg_crystalloid_analysis`` (which reproduces the pressures the
authority committed in the human-reviewed trajectories), and writes nothing to any encounter, authority record, snapshot, baseline, region or
faculty review. It approves no rate, no pressure parameter and no region; it changes no physiology (``clinical_core/`` and ``family_engine.py``
are read, never edited). Every mutation is a COUNTERFACTUAL copy made inside this process to measure a sensitivity.

The one question (the faculty / architect decision of 2026-11-15): is the current 2.5 mL/min too small for the severity and time course of the
authored GI shock, and does a defensible rate scale ALONE resolve the FR-G concern (1 L of saline over 60 minutes protects too much)?

What it measures, each recomputed from the executable model:

* where 2.5 mL/min comes from (the live literals, the conversion and the first commits; P3-315);
* what the two authored cases say about severity, and that no absolute blood loss is authored (P3-316);
* the current scale kept in three separate concepts: literal blood shed, effective circulating deficit, the model's V coordinate (P3-317);
* the inversion of the untreated course for the rate under the CURRENT pressure map: the existing faculty envelopes (U-OUT) and a broad
  time-window reading, by 1-D bisection (P3-318);
* identifiability: the untreated course reads only ``rate / scale``; the protection of a crystalloid infusion reads only the rate (P3-319);
* rate x crystalloid: FR-G against the same-case untreated course for every justified witness (P3-320);
* the joint rate x pressure-map region the existing faculty constraints leave, and where FR-G falls in it (P3-321);
* the qualitative faculty conclusions of FR-A .. FR-G at the justified witnesses, and early treatment to 240 minutes (P3-322).

Regenerate the stored record with ``MRS_WRITE_BLEED_RATE_ANALYSIS=1 python3 gi_bleed_rate_analysis.py`` (the person who changes the analysis).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
from pathlib import Path

import frg_crystalloid_analysis as fa

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_BLEED_RATE_SCALE_ANALYSIS.json"
FRG_RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_FRG_CRYSTALLOID_ANALYSIS.json"
WRITE_FLAG = "MRS_WRITE_BLEED_RATE_ANALYSIS"
VERSION = "P3-315"
EVIDENCE_CLASS = "MODEL_ANALYSIS"

CASES = ("gi_bleed_57m", "gi_bleed_72f")
ARRIVAL_SBP = {"gi_bleed_57m": 88.0, "gi_bleed_72f": 98.0}      # the authored arrival systolic pressures (checked against the runs below)
FRG_CASE = "gi_bleed_72f"
COMMITTED_FRACTION = 0.5                 # the committed pressure point's arrival position (gi_pressure_committed), both cases
DECLARED_SCALE_BAND = (600.0, 1500.0)    # calibration.REGISTRY["preload_curve_scale_ml"]: a CANDIDATE band, checked live below
HORIZON = 240
READ_MINUTES = (30, 60, 70, 120)
LOSS_MINUTES = (30, 60, 120, 180)
TOLERANCE = 1e-4

#: The descriptive classes of P3-320A, declared here BEFORE any witness is classified. They are an analysis convention and not a faculty
#: definition: ``p`` is the share of the untreated fall of systolic pressure that the infusion prevents at the end of the infusion (minute 60).
#: The faculty words are "closer to the untreated course" (p below one half) and "SUBSTANTIALLY closer" (read here as at least twice as close
#: to the untreated course as to a stable one: p at most one third). Both edges are reported, so no conclusion hides in the boundary.
NEAR_STABILIZATION_FROM = 0.75
MODEST_BELOW = 1.0 / 3.0
MINIMAL_BELOW = 0.10
CLOSER_TO_UNTREATED_BELOW = 0.5
EDGE_WITNESS_STEP = 1.005                # a witness of an edge sits half a percent beyond it, so that its class is the one the edge opens

#: The broad behavioural windows of P3-318, in the assignment's own words: major deterioration by 1-2 h, severe by 2-3 h. Read as time
#: windows on the SHAPE the faculty accepted (never as pressure targets): the state the accepted untreated course shows at the middle of each
#: window has to be reached inside that window.
BROAD_WINDOWS = {"major_deterioration_by_1_to_2_h": (60, 90, 120), "severe_deterioration_by_2_to_3_h": (120, 150, 180)}


# -- the live constants the analysis stands on ------------------------------------------------------------------------------------------------------

def constants() -> dict:
    from clinical_core import blood_anchors, calibration, derived, legacy_adapter
    import family_engine
    literal = legacy_adapter.LEGACY_LITERALS["gi_bleeding_circulation_per_min"]
    per_unit = legacy_adapter.LEGACY_LITERALS["blood_circulation_per_unit"]
    scale = derived.LEGACY_ML_PER_CIRCULATION_UNIT
    band = calibration.REGISTRY["preload_curve_scale_ml"]
    return {"legacy_circulation_per_min": literal[0], "legacy_circulation_per_min_where": literal[1], "legacy_circulation_per_unit": per_unit[0],
            "ml_per_circulation_unit": scale, "ml_per_circulation_unit_is_300_over_0_36": abs(scale - 300.0 / 0.36) < 1e-12,
            "runtime_rate_ml_min": literal[0] * scale, "reference_rate_ml_min": blood_anchors.REFERENCE["bleed_ml_per_min"],
            "exploration_rates_ml_min": list(blood_anchors.EXPLORATION["bleed_ml_per_min"]),
            "default_preload_scale_ml": derived.DEFAULT_PROFILE.preload_curve_scale_ml, "declared_scale_band": [band.lower, band.upper],
            "declared_scale_status": band.status, "arrival_circulating_volume_ml": blood_anchors.REFERENCE["arrival_circulating_volume_ml"],
            "red_cell_unit_volume_ml": blood_anchors.REFERENCE["red_cell_unit_volume_ml"],
            "legacy_fraction_with_ppi": family_engine.GI_BLEED["bleeding_with_ppi"],
            "legacy_fraction_after_hemostasis": family_engine.GI_BLEED["bleeding_after_hemostasis"]}


# -- running the certified core, with counterfactual copies ------------------------------------------------------------------------------------------

def run(scenario: dict, minutes: int, *, rate=None, scale=None, kernel=None, drop_fluid: bool = False, fraction=None):
    """One run of the core on a captured scenario with COUNTERFACTUAL copies of the bleed rate, the preload scale, the arrival position and the
    crystalloid kernel. Returns ``(rows, stopped_at)``: a run that meets the core's own boundary keeps the minutes before it."""
    from clinical_core import integration
    from clinical_core.interventions.fluids import Crystalloid
    anchors, contributors, _captured, profile = integration.scenario_from_dict(scenario)
    made = []
    for item in contributors:
        if isinstance(item, Crystalloid):
            if drop_fluid:
                continue
            if kernel is not None:
                item = dataclasses.replace(item, effective_ml_per_ml=float(kernel[0]), transient_share=float(kernel[1]), leak_tau_min=float(kernel[2]))
        elif rate is not None and type(item).__name__ == "GIHaemorrhage":
            item = dataclasses.replace(item, blood_loss_ml_per_min=float(rate))
        made.append(item)
    changes = {}
    if scale is not None:
        changes["preload_curve_scale_ml"] = float(scale)
    if fraction is not None:
        changes["arrival_preload_fraction"] = float(fraction)
    if changes:
        profile = dataclasses.replace(profile, **changes)
    stopped = None
    try:
        trajectory = integration.run(anchors, made, minutes, profile)
    except Exception as error:                       # the core's own boundary (output reaching zero with a pulse): reported, never worked around
        found = re.search(r"minute (\d+)", str(error))
        if found is None:
            raise
        stopped = int(found.group(1))
        trajectory = integration.run(anchors, made, stopped - 1, profile)
    return fa.per_minute(trajectory, anchors, profile), stopped


def protection(treated, untreated, minute: int):
    """The share of the untreated fall of systolic pressure that the treatment prevents at ``minute`` (None where a run stopped earlier)."""
    if minute >= len(treated) or minute >= len(untreated):
        return None
    fall = untreated[0]["sbp"] - untreated[minute]["sbp"]
    return (treated[minute]["sbp"] - untreated[minute]["sbp"]) / fall if fall > 0.05 else None


def classify(p60, p120) -> str:
    if p60 is None:
        return "NOT_READABLE_THE_RUN_STOPPED"
    if p60 < 0.0:
        return "WORSE_THAN_EXPECTED"
    if p60 >= NEAR_STABILIZATION_FROM:
        return "NEAR_STABILIZATION"
    if p60 >= MODEST_BELOW:
        return "SUBSTANTIAL_PROTECTION"
    if p60 >= MINIMAL_BELOW:
        return "MODEST_TRANSIENT_ATTENUATION" if (p120 is None or p120 < p60) else "MODEST_BUT_NOT_TRANSIENT"
    return "MINIMAL_EFFECT"


def bisect(predicate, low: float, high: float, tolerance: float = TOLERANCE) -> float:
    """The point between ``low`` and ``high`` where ``predicate`` changes (it must differ at the two ends)."""
    at_low = predicate(low)
    if at_low == predicate(high):
        raise ValueError(f"the predicate does not change between {low} and {high}")
    while high - low > tolerance:
        middle = (low + high) / 2.0
        if predicate(middle) == at_low:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


# -- the frozen faculty evaluators (never re-implemented) --------------------------------------------------------------------------------------------

def _values(rate: float, scale: float, fraction: float) -> dict:
    from clinical_core import blood_anchors
    return {**blood_anchors.REFERENCE, "bleed_ml_per_min": float(rate), "preload_scale_over_kappa_ml": float(scale), "preload_fraction": float(fraction)}


def u_out(case: str, rate: float, scale: float, fraction: float) -> bool:
    from clinical_core import blood_constraints as bc
    return bc.passes("U-OUT", case, bc.untreated(case, _values(rate, scale, fraction)))


def u_out_interval(case: str, scale: float, fraction: float, inside_c: float) -> list:
    """The rates the frozen U-OUT envelopes admit for ``case`` at one pressure point, by bisection from a point known to be inside."""
    inside = inside_c * scale
    if not u_out(case, inside, scale, fraction):
        raise ValueError(f"{case}: {inside} is not inside U-OUT at scale {scale}, position {fraction}")
    low = bisect(lambda rate: u_out(case, rate, scale, fraction), 0.0003 * scale, inside)
    high = bisect(lambda rate: u_out(case, rate, scale, fraction), inside, 0.02 * scale)
    return [low, high]


def one_unit(case: str, scale: float, fraction: float) -> dict:
    """FD-BLD-02's reading (the frozen row and the frozen verdicts): the relative rise of effective output from one red-cell unit at arrival."""
    from clinical_core import blood_constraints as bc
    row = bc.red_cells(case, _values(constants()["reference_rate_ml_min"], scale, fraction))
    gain = row["output"][1] / row["output"][0] - 1.0
    return {"output_gain": gain, "fd_bld_02_envelope": list(bc.DECISIONS["FD-BLD-02"][case]), "fd_bld_02": bc.passes("FD-BLD-02", case, row),
            "fd_bld_02_lower_bound_variant_v4": bc.passes("FD-BLD-02", case, row, "V4_fd02_lower_bound_when_responsive"),
            "second_unit": bc.passes("SECOND-UNIT", case, row)}


#: A point known to lie inside each case's U-OUT band at the arrival position named (c = rate / scale; from docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md
#: section 3.4, and CHECKED by ``u_out_interval`` before it is used).
INSIDE_C = {("gi_bleed_57m", 0.5): 0.0036, ("gi_bleed_72f", 0.5): 0.0026, ("gi_bleed_72f", 0.6): 0.0038}


# -- the context: the captured scenarios, the kernels ------------------------------------------------------------------------------------------------

def build_context() -> dict:
    live = constants()
    scenarios = {scenario_id: fa.capture(*fa.reviewed_orders(scenario_id)) for scenario_id in ("FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-G")}
    untreated = {case: fa.capture(case, fa.UNTREATED_ORDERS) for case in CASES}
    _case_b, orders_b = fa.reviewed_orders("FR-B")
    early = {case: fa.capture(case, orders_b) for case in CASES}
    frg = json.loads(FRG_RECORD_PATH.read_text(encoding="utf-8"))
    runtime = frg["mass_balance"]["kernel"]
    least = frg["volume_region"]["core_runs"]["region_least_protective"]["point"]
    kernels = {"RUNTIME_OUTSIDE_THE_CLOSED_REGION": (runtime["e"], runtime["s"], runtime["tau"]),
               "CLOSED_REGION_LEAST_PROTECTIVE": (least["e"], least["s"], least["tau"])}
    return {"live": live, "scenarios": scenarios, "untreated": untreated, "early": early, "kernels": kernels, "frg_record_digest": frg["record_digest"],
            "s0": live["default_preload_scale_ml"], "rate0": live["runtime_rate_ml_min"], "c0": live["legacy_circulation_per_min"]}


# -- P3-315: provenance -----------------------------------------------------------------------------------------------------------------------------

STATUSES = ("FACULTY_DEFINED", "AUTHORED_CASE", "LEGACY_DERIVED", "ANALYTICAL_CONVENIENCE", "SYNTHETIC_REFERENCE", "EXPLORATORY_PROBE", "UNKNOWN")

#: Every numeric value the bleed rate has ever had in the repository, with where it is and what it was for. Written from the audit (the code,
#: the documents and the full git history, deepened to the first commit of 2026-09-09) and CHECKED against the live code by ``section_provenance``.
PROVENANCE = (
    {"value": "0.003 per minute (dimensionless legacy 'circulation' variable; not mL)", "source": "family_engine._minute, gi_bleed branch",
     "where": "family_engine.py; first commit 8f77d9a (2026-09-13, v0.16.0), whose message says the numerical trajectories 'remain teaching models requiring faculty validation'; scaled by the continuing-bleeding fraction since cec7942 (2026-09-19)",
     "purpose": "the untreated worsening of the legacy engine's circulation variable while a GI bleed is active", "status": "UNKNOWN",
     "note": "no clinical source for the number is recorded in the code, the commit or the release notes; it was never written as a blood-loss rate"},
    {"value": "300 / 0.36 = 833.33 mL-eq per unit of the legacy circulation variable", "source": "clinical_core.derived.LEGACY_ML_PER_CIRCULATION_UNIT",
     "where": "clinical_core/derived.py; commit ec65728 (2026-10-21)",
     "purpose": "unit conversion: one red-cell unit is about 300 mL (family_engine TRANSFUSION note, faculty question of 2026-09-20) and moves the legacy circulation variable by 0.36 (8f77d9a)",
     "status": "ANALYTICAL_CONVENIENCE", "note": "the same constant is the default preload_curve_scale_ml, so rate / scale is exactly the legacy literal"},
    {"value": "2.5 mL-eq/min = 0.003 x 833.33", "source": "clinical_core.legacy_adapter.haemorrhage_from_legacy",
     "where": "clinical_core/legacy_adapter.py; commit 9d1d6df (2026-10-27, P2I-2T). clinical_core/migration.py declares it FAMILY_DEFAULT: 'the family engine's circulation literal as whole-blood loss, adopted for the comparison only'",
     "purpose": "the whole-blood loss of the shadow core, and so of the development pressure authority and of every human-reviewed trajectory", "status": "LEGACY_DERIVED",
     "note": "THE ORIGIN OF 2.5 mL/min: a unit conversion of a legacy teaching magnitude, never authored, never faculty-defined"},
    {"value": "2.5", "source": "clinical_core.blood_anchors.REFERENCE", "where": "clinical_core/blood_anchors.py; commit 9b09e30 (2026-10-27, P2I-2U): 'the canonical provisional values (P2I-2T)'",
     "purpose": "reference point of the shared-blood calibration analysis", "status": "SYNTHETIC_REFERENCE", "note": "provisional by its own declaration"},
    {"value": "(1.25, 2.5, 5.0)", "source": "clinical_core.blood_anchors.EXPLORATION", "where": "clinical_core/blood_anchors.py; commit 9b09e30 (2026-10-27)",
     "purpose": "exploration grid", "status": "SYNTHETIC_REFERENCE", "note": "'SYNTHETIC exploration ranges: neither candidate bands nor approved values'"},
    {"value": "3.0 and 2.0", "source": "clinical_core.blood_constraints.PROBES (P1, P2)", "where": "clinical_core/blood_constraints.py (P2I-2V, 2026-10-27)",
     "purpose": "off-grid probe points before the freeze", "status": "EXPLORATORY_PROBE", "note": ""},
    {"value": "(5, 6, 7, 8, 9, 10)", "source": "clinical_core.blood_rate_boundary.RATES (P2I-2X)", "where": "clinical_core/blood_rate_boundary.py; docs/revision/P2I2X_blood_rate_boundary.json",
     "purpose": "densify the open upper edge of the common rate in the frozen shared-blood filter", "status": "EXPLORATORY_PROBE",
     "note": "registered result: TESTED_VIABLE_RATE_REGION = {5, 6}, FIRST_TESTED_NONVIABLE_RATE = 7, 'no es una tasa aprobada'"},
    {"value": "(5, 6, 7) x refill", "source": "P2I-2Y", "where": "docs/revision/P2I2Y_CRISTALOIDE_Y_TASA.md section 1", "purpose": "robustness of the rate to the refill extension",
     "status": "EXPLORATORY_PROBE", "note": "rate 7 stays non-viable jointly; 6 stays viable"},
    {"value": "2.0 to 3.5 in steps of 0.25", "source": "P3-87", "where": "docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md section 7.2", "purpose": "U-OUT against the rate at the committed pressure point",
     "status": "EXPLORATORY_PROBE", "note": "the 'single shared value 2.75' was an artefact of the 0.25 step (corrected in P3-90)"},
    {"value": "[2.5497, 3.7234] (57m), [1.6894, 2.8038] (72f), common [2.5497, 2.8038]", "source": "P3-89 / P3-90", "where": "docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md sections 2.2 and 3",
     "purpose": "the rates the faculty U-OUT envelopes admit AT the committed pressure point (scale 833.33, position 0.5)", "status": "ANALYTICAL_CONVENIENCE",
     "note": "derived from FACULTY_DEFINED envelopes but conditional on the pressure point: U-OUT bounds rate / scale, not the rate; recomputed here"},
    {"value": "(2.5, 3.5, 5.0)", "source": "frg_crystalloid_analysis.BLEED_RATES_ML_MIN (P3-305)", "where": "frg_crystalloid_analysis.py", "purpose": "sensitivity of FR-G to the rate",
     "status": "EXPLORATORY_PROBE", "note": "a sensitivity, never a target"},
    {"value": "none", "source": "clinical_core.blood_constraints.DECISIONS['bleed_rate_authority'] and ['bleed_rate_analysis']", "where": "clinical_core/blood_constraints.py (faculty decisions of 2026-10-27)",
     "purpose": "the policy: a verified case-specific rate wins, a family value is a fallback, with neither migration fails closed", "status": "FACULTY_DEFINED",
     "note": "the POLICY is faculty-defined; 'no numeric bleed rate is approved' and 'no family default is populated'"},
)


def section_provenance(ctx) -> dict:
    live = ctx["live"]
    from clinical_core import blood_constraints as bc, blood_rate_boundary
    checks = {"legacy_literal_is_0_003": live["legacy_circulation_per_min"] == 0.003,
              "conversion_is_300_over_0_36": live["ml_per_circulation_unit_is_300_over_0_36"] and live["legacy_circulation_per_unit"] == 0.36,
              "runtime_rate_is_their_product_2_5": abs(live["runtime_rate_ml_min"] - 2.5) < 1e-12,
              "reference_is_2_5": live["reference_rate_ml_min"] == 2.5, "exploration_is_1_25_2_5_5": live["exploration_rates_ml_min"] == [1.25, 2.5, 5.0],
              "probes_are_3_and_2": [bc.PROBES["P1"]["bleed_ml_per_min"], bc.PROBES["P2"]["bleed_ml_per_min"]] == [3.0, 2.0],
              "p2i2x_rates_are_5_to_10": list(blood_rate_boundary.RATES) == [5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
              "no_numeric_rate_is_approved": "no numeric bleed rate is approved" in bc.DECISIONS["bleed_rate_authority"]["meaning"],
              "default_scale_equals_the_conversion": live["default_preload_scale_ml"] == live["ml_per_circulation_unit"],
              "every_status_is_in_the_vocabulary": all(row["status"] in STATUSES for row in PROVENANCE)}
    return {"records": [dict(row) for row in PROVENANCE], "live": live, "checks": checks, "all_checks_hold": all(checks.values()),
            "origin_of_2_5_ml_min": "0.003 per minute of the legacy engine's dimensionless circulation variable (first committed 2026-09-13 as a teaching magnitude, no clinical source recorded) times 300 mL / 0.36 (the legacy convention that one red-cell unit of about 300 mL moves that variable by 0.36)",
            "status_of_2_5": "LEGACY_DERIVED", "faculty_classification": "HISTORICAL_DEVELOPMENT_REFERENCE, not CLINICALLY_IDENTIFIED_RATE (faculty decision of 2026-11-15)",
            "statuses_with_no_record": [name for name in ("AUTHORED_CASE",) if not any(row["status"] == name for row in PROVENANCE)],
            "history_depth": "the full branch history was read (deepened from a shallow clone to the first commit, 2026-09-09)"}


# -- P3-316: what the authored cases say -------------------------------------------------------------------------------------------------------------

EXPLICIT, INFERRED, NOT_SPECIFIED = "EXPLICIT_CASE_FACT", "INFERRED_SEVERITY_ONLY", "NOT_SPECIFIED"


def section_authored(ctx) -> dict:
    import clinical_cases
    variants = {item["id"]: item for item in clinical_cases.FAMILIES["gi_bleed"]["variants"]}
    out = {}
    for case in CASES:
        item = variants[case]
        obs, inv, history = item["observable"], item["investigations"], item["history"]
        labs = inv["basic_labs"]["result"]
        rows = [
            ("arrival blood pressure", f"{obs['sbp']}/{obs['dbp']} mmHg", EXPLICIT), ("heart rate", f"{obs['hr']} bpm, {obs['rhythm']}", EXPLICIT),
            ("capillary refill", f"{obs['crt']} s; extremities {obs['extremities']}; perfusion {obs['peripheral_perfusion']}", EXPLICIT),
            ("respiratory rate and SpO2", f"{obs['respiratory_rate']}/min; {obs['spo2']} %", EXPLICIT), ("neurological examination", item["examination"]["Neurological"], EXPLICIT),
            ("haemoglobin", f"{inv['hemoglobin']['result']['hemoglobin_g_dl']} g/dL", EXPLICIT), ("lactate", f"{inv['lactate']['result']['lactate_mmol_l']} mmol/L", EXPLICIT),
            ("urea nitrogen and creatinine", f"BUN {labs['bun_mg_dl']} mg/dL; creatinine {labs['creatinine_mg_dl']} mg/dL", EXPLICIT),
            ("bedside ultrasound", f"IVC {inv['pocus']['result']['ivc']}; LV {inv['pocus']['result']['lv']}", EXPLICIT),
            ("symptoms", " ".join(history["chief_complaint"] + history["associated_symptoms"]), EXPLICIT), ("syncope / presyncope", item["presentation"], EXPLICIT),
            ("reported bleeding source", " ".join(history["bleeding"]) + " " + item["examination"]["Abdomen"], EXPLICIT),
            ("reported duration of the melaena", " ".join(history["onset"]), EXPLICIT),
            ("risk context", " ".join(history["medications"] + history["medical_history"]), EXPLICIT),
            ("ongoing bleeding at arrival", "the history reports continuing melaena; the faculty focus says 'monitoring ongoing blood loss': " + item["faculty"]["management_focus"], INFERRED),
            ("severity of the haemorrhage", "hypotension, tachycardia, delayed refill, raised lactate, severe anaemia and a collapsing IVC: a large loss BEFORE arrival is implied, not measured", INFERRED),
            ("duration of the hypoperfusion", "no case states it (gi_reference: 'neither case states the duration of hypoperfusion')", NOT_SPECIFIED),
            ("reported amount of blood lost", "no volume, no number of episodes with volume, no transfusion history", NOT_SPECIFIED),
            ("rate of the ongoing loss (mL/min or mL/h)", "nothing in the case", NOT_SPECIFIED), ("total blood lost", "nothing in the case", NOT_SPECIFIED),
            ("blood volume or weight of the patient", "nothing in the case (the model's 4000 mL-eq arrival circulating volume is a reference value, not authored)", NOT_SPECIFIED),
        ]
        out[case] = [{"item": name, "evidence": text, "class": label} for name, text, label in rows]
    return {"cases": out, "absolute_blood_loss": "ABSOLUTE_BLOOD_LOSS_NOT_DIRECTLY_AUTHORED",
            "estimable_with_confidence_0_80": {"ml_per_min": False, "ml_per_hour": False, "total_blood_lost": False},
            "why": "the cases author the arrival STATE (vital signs, laboratory values, ultrasound) and a qualitative history; no volume, no rate and no body size is written, and no clinical blood-loss volume is invented here",
            "earlier_finding_still_current": "docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md section 2.1: no INDEPENDENT_CLINICAL_AUTHORED evidence about the rate"}


# -- P3-317: the current scale, in three concepts kept apart ----------------------------------------------------------------------------------------

def section_current_scale(ctx) -> dict:
    live, out = ctx["live"], {}
    volume = live["arrival_circulating_volume_ml"]
    for case in CASES:
        rows, stopped = run(ctx["untreated"][case], 400, drop_fluid=True)
        table = {}
        for minute in LOSS_MINUTES:
            row = rows[minute]
            table[str(minute)] = {"A_literal_blood_shed_ml": row["bleed_cum_ml"], "A_as_share_of_the_reference_arrival_volume_pct": 100.0 * row["bleed_cum_ml"] / volume,
                                  "refill_ml": row["refill_cum_ml"], "B_effective_circulating_deficit_ml_eq": -row["V"] / 1.0,
                                  "C_V_coordinate": row["V"], "C_dimensionless_V_over_scale": row["V"] / ctx["s0"], "preload_position": row["preload_position"],
                                  "forward_flow_output_rel": row["forward_flow_output_rel"], "sbp": row["sbp"], "hb": row["hb"], "hb_fall_g_dl": rows[0]["hb"] - row["hb"]}
        if abs(rows[0]["sbp"] - ARRIVAL_SBP[case]) > 1e-6:
            raise AssertionError(f"{case}: the arrival pressure is not the authored one")
        out[case] = {"arrival": {"sbp": rows[0]["sbp"], "hb": rows[0]["hb"]}, "at": table, "core_boundary_minute_untreated": stopped}
    zero_output_deficit = ctx["s0"] * math.log(1.0 / (1.0 - COMMITTED_FRACTION))
    hour = ctx["rate0"] * 60.0
    return {"rate_ml_min": ctx["rate0"], "ml_per_hour": hour, "cases": out,
            "three_concepts": {"A": "literal whole blood shed (shed_ml = rate x t): the repository calls it mL-EQUIVALENTS of modelled whole blood, not a measured flow",
                               "B": "effective circulating deficit (volume_ml): shed minus refill, plus crystalloid and red cells when given",
                               "C": "the model's V coordinate (kappa x volume_ml) and its position on the preload curve (V / scale): the ONLY thing pressure reads"},
            "zero_output_deficit_ml_eq": zero_output_deficit, "zero_output_deficit_share_of_arrival_volume_pct": 100.0 * zero_output_deficit / volume,
            "one_hour_of_bleeding_in_faculty_approved_units": {
                "red_cell_units": hour / live["red_cell_unit_volume_ml"],
                "litres_of_saline_by_FD_BLD_04_early_contribution": [hour / 300.0, hour / 150.0],
                "reading": "FD-BLD-04 says one litre of isotonic crystalloid contributes about 150 to 300 mL early; at 2.5 mL-eq/min one hour of bleeding IS 150 mL-eq. In the repository's own approved units, half a litre to one litre of saline undoes an hour of this bleeding: that is the FR-G finding, before any pressure map"},
            "reading": "arithmetic consistency only, no clinical diagnosis: under the committed map the accepted untreated course reaches its 2-hour state after shedding 7.5 % of the reference arrival volume and the core's zero-output boundary lies 578 mL-eq (14 %) below arrival"}


# -- P3-318: inverting the untreated course for the rate, under the CURRENT pressure map ------------------------------------------------------------

def _time_to(rows, level: float):
    for index in range(1, len(rows)):
        if rows[index]["sbp"] <= level:
            before, after = rows[index - 1]["sbp"], rows[index]["sbp"]
            return (index - 1) + (before - level) / (before - after) if before > after else float(index)
    return None


def section_untreated_inversion(ctx) -> dict:
    s0, rate0 = ctx["s0"], ctx["rate0"]
    u_out_intervals = {case: u_out_interval(case, s0, COMMITTED_FRACTION, INSIDE_C[(case, 0.5)]) for case in CASES}
    common = [max(item[0] for item in u_out_intervals.values()), min(item[1] for item in u_out_intervals.values())]
    broad = {}
    for case in CASES:
        accepted, _ = run(ctx["untreated"][case], HORIZON, drop_fluid=True)
        edges = {}
        for name, (start, middle, end) in BROAD_WINDOWS.items():
            level = accepted[middle]["sbp"]

            def reached_by(rate, minute, level=level, case=case):
                rows, _stopped = run(ctx["untreated"][case], HORIZON, rate=rate, drop_fluid=True)
                found = _time_to(rows, level)
                return found is not None and found <= minute
            edges[name] = {"state_is_the_accepted_course_at_minute": middle, "window_min": [start, end],
                           "slowest_rate": bisect(lambda rate: reached_by(rate, end), 0.25 * rate0, rate0),
                           "fastest_rate": bisect(lambda rate: reached_by(rate, start), rate0, 4.0 * rate0)}
        broad[case] = {"windows": edges, "interval": [max(item["slowest_rate"] for item in edges.values()), min(item["fastest_rate"] for item in edges.values())]}
    broad_common = [max(item["interval"][0] for item in broad.values()), min(item["interval"][1] for item in broad.values())]
    inward = 2.0 * TOLERANCE          # a witness sits just INSIDE the edge it names (the bisection's midpoint can fall on either side)
    witnesses = [
        ("LOWER_72F_U_OUT_EDGE", u_out_intervals[FRG_CASE][0] + inward, "the slowest rate the faculty envelopes admit for FR-G's own case: a lower witness, to show the direction"),
        ("BROAD_WINDOW_LOWER", broad_common[0] + inward, "the slowest rate that keeps both broad windows in both cases"),
        ("REFERENCE", rate0, "the historical development reference, the rate every human-reviewed trajectory used"),
        ("COMMON_U_OUT_LOWER", common[0] + inward, "the lower edge of the rates the faculty envelopes admit in BOTH cases"),
        ("COMMON_U_OUT_UPPER", common[1] - inward, "the upper edge of the same band (it is 72f's own upper edge)"),
        ("BROAD_WINDOW_UPPER", broad_common[1] - inward, "the fastest rate that keeps both broad windows in both cases"),
        ("HIGH_57M_U_OUT_EDGE", u_out_intervals["gi_bleed_57m"][1] - inward, "the fastest rate ANY untreated faculty envelope of either case admits: the high witness, needed to show that even it does not resolve FR-G"),
    ]
    behaviour = {}
    for label, rate, why in witnesses:
        row = {"rate_ml_min": rate, "why": why, "cases": {}}
        for case in CASES:
            rows, stopped = run(ctx["untreated"][case], HORIZON, rate=rate, drop_fluid=True)
            sbp = [item["sbp"] for item in rows]
            row["cases"][case] = {"sbp": {str(m): (rows[m]["sbp"] if m < len(rows) else None) for m in (60, 120, 180)}, "core_boundary_minute": stopped,
                                  "remains_below_arrival": all(value <= sbp[0] + 1e-9 for value in sbp), "progressively_worsens": all(b <= a + 1e-9 for a, b in zip(sbp, sbp[1:])),
                                  "u_out": u_out(case, rate, s0, COMMITTED_FRACTION),
                                  "inside_broad_windows": broad[case]["interval"][0] - 1e-9 <= rate <= broad[case]["interval"][1] + 1e-9}
        row["ordering_57m_below_72f"] = all((row["cases"]["gi_bleed_57m"]["sbp"][m] or 0.0) < (row["cases"]["gi_bleed_72f"]["sbp"][m] or 1e9) for m in ("60", "120"))
        behaviour[label] = row
    return {"pressure_map": {"scale_ml_eq": s0, "arrival_position": COMMITTED_FRACTION, "label": "the committed pressure point (CURRENT map)"},
            "u_out_rate_interval_ml_min": u_out_intervals, "u_out_common_interval_ml_min": common,
            "reference_rate_inside_the_common_u_out_band": common[0] <= rate0 <= common[1],
            "reference_below_the_common_lower_edge_pct": 100.0 * (common[0] - rate0) / common[0],
            "broad_windows": broad, "broad_common_interval_ml_min": broad_common,
            "broad_windows_are": "this analysis's operational reading of the assignment's phrases (time windows on the accepted SHAPE); they are not a faculty constraint and name no pressure",
            "witnesses": behaviour, "method": "analytic reduction (the course reads rate x t), fixed probes (the edges of the envelopes) and 1-D bisection to 1e-4; no Cartesian scan"}


# -- P3-319: identifiability --------------------------------------------------------------------------------------------------------------------------

def section_identifiability(ctx, inversion) -> dict:
    s0, c0 = ctx["s0"], ctx["c0"]
    worst = 0.0
    for case in CASES:
        reference, _ = run(ctx["untreated"][case], HORIZON, drop_fluid=True)
        for scale in (DECLARED_SCALE_BAND[1], 3.0 * s0):
            other, _ = run(ctx["untreated"][case], HORIZON, rate=c0 * scale, scale=scale, drop_fluid=True)
            worst = max(worst, max(abs(a["sbp"] - b["sbp"]) for a, b in zip(reference, other)))
    at_top = {case: u_out_interval(case, DECLARED_SCALE_BAND[1], COMMITTED_FRACTION, INSIDE_C[(case, 0.5)]) for case in CASES}
    c_spread = max(abs(at_top[case][edge] / DECLARED_SCALE_BAND[1] - inversion["u_out_rate_interval_ml_min"][case][edge] / s0) for case in CASES for edge in (0, 1))
    frg, untreated = ctx["scenarios"]["FR-G"], ctx["untreated"][FRG_CASE]
    spread = {}
    for rate in (ctx["rate0"], c0 * DECLARED_SCALE_BAND[1]):
        values = []
        for scale, fraction in ((DECLARED_SCALE_BAND[0], None), (s0, None), (DECLARED_SCALE_BAND[1], None), (3.0 * s0, None), (s0, 0.35), (s0, 0.6)):
            treated, _ = run(frg, 70, rate=rate, scale=scale, fraction=fraction)
            plain, _ = run(untreated, 70, rate=rate, scale=scale, fraction=fraction, drop_fluid=True)
            values.append(protection(treated, plain, 60))
        spread[f"{rate:.4f}"] = {"p60_across_six_pressure_maps": values, "max_minus_min": max(values) - min(values)}
    reused = [
        {"evidence": "U-OUT (frozen faculty envelopes on the untreated output)", "used_for": "rate / scale ONLY", "used_twice": False},
        {"evidence": "the human acceptance of the untreated courses FR-A and FR-D", "used_for": "the same one coordinate (rate / scale): it is NOT independent of U-OUT and is not counted as a second confirmation", "used_twice": False},
        {"evidence": "the human FR-G judgment (qualitative) with the crystalloid retention in real mL", "used_for": "the ABSOLUTE rate ONLY (its protection reads retained / shed, not the map)", "used_twice": False},
        {"evidence": "FD-BLD-02 (frozen faculty envelope on the one-unit response)", "used_for": "a CHECK on the scale that a rate implies; it selects nothing", "used_twice": False},
        {"evidence": "the human acceptance of the treated courses FR-B, FR-C and FR-E", "used_for": "qualitative non-regression only; they read the same coordinate as FD-BLD-02 (the scale) and select nothing", "used_twice": False},
    ]
    invariant = worst < 1e-9
    map_free = max(item["max_minus_min"] for item in spread.values()) < 0.05
    return {"untreated_course_on_the_joint_manifold": {"max_abs_sbp_difference_mmHg": worst, "invariant": invariant,
                                                       "meaning": "multiply the rate and the preload scale by the same factor and the untreated pressure course does not move: it reads only rate / scale"},
            "u_out_bounds_rate_over_scale": {"interval_at_the_top_of_the_declared_band_ml_min": at_top, "max_abs_difference_in_c": c_spread, "holds": c_spread < 1e-6},
            "crystalloid_protection_is_map_free": {"by_rate": spread, "holds": map_free,
                                                   "meaning": "at a fixed rate the share of the untreated fall that the infusion prevents is the same on six pressure maps: it reads the rate (retained / shed), not the map"},
            "effective_dimension": {"from_untreated_evidence": 1, "coordinate": "c = rate x kappa / scale (plus the arrival position f, already known from P3-91)",
                                    "absolute_rate_from_untreated_evidence": "NOT IDENTIFIED AT ALL",
                                    "what_identifies_the_absolute_scale": "only treated behaviour in real millilitres: the crystalloid retention region (FR-G) and the red-cell unit (FD-BLD-02)"},
            "constraints_and_their_single_use": reused, "circular_reuse_found": any(item["used_twice"] for item in reused),
            "verdict": "B" if (invariant and map_free) else "UNCLASSIFIED", "verdict_name": "BLEED_RATE_AND_PRESSURE_MAP_REQUIRE_JOINT_REGION",
            "why_not": {"A": "the untreated evidence does not bound the rate, only rate / scale: a rate interval exists only after the pressure point is named",
                        "C": "the absolute scale IS reachable, through treated behaviour in real mL; it is not unidentifiable in principle",
                        "D": "the map does not make the rate uninterpretable: on the joint manifold every reading stays coherent; it is the current POINT that is outside the faculty constraints"},
            "agrees_with_the_earlier_cycle": "P3-89 IDENTIFIABLE_ONLY_JOINTLY_WITH_PRESSURE and P3-95 C RATE_AND_PRESSURE_MUST_BE_CALIBRATED_JOINTLY (docs/PHASE3_GI_BLEED_RATE_AND_PRESSURE.md)"}


# -- P3-320: rate x crystalloid ------------------------------------------------------------------------------------------------------------------------

def _frg_row(ctx, *, rate, scale, kernel, fraction=None) -> dict:
    treated, stop_t = run(ctx["scenarios"]["FR-G"], 130, rate=rate, scale=scale, kernel=kernel, fraction=fraction)
    plain, stop_u = run(ctx["untreated"][FRG_CASE], 130, rate=rate, scale=scale, fraction=fraction, drop_fluid=True)
    p = {str(minute): protection(treated, plain, minute) for minute in READ_MINUTES}
    return {"rate_ml_min": rate, "scale_ml_eq": scale, "arrival_position": COMMITTED_FRACTION if fraction is None else fraction,
            "blood_lost_by_60_ml": treated[60]["bleed_cum_ml"], "crystalloid_retained_at_60_ml": treated[60]["net_retained_crystalloid_ml"],
            "retained_over_lost": treated[60]["net_retained_crystalloid_ml"] / treated[60]["bleed_cum_ml"],
            "net_effective_volume_change_at_60_ml": treated[60]["V"], "untreated_effective_volume_change_at_60_ml": plain[60]["V"],
            "share_of_untreated_pressure_fall_prevented": p, "sbp_treated": {str(m): treated[m]["sbp"] if m < len(treated) else None for m in READ_MINUTES},
            "sbp_untreated": {str(m): plain[m]["sbp"] if m < len(plain) else None for m in READ_MINUTES},
            "class": classify(p["60"], p["120"]), "closer_to_untreated_than_to_stable": p["60"] is not None and p["60"] < CLOSER_TO_UNTREATED_BELOW,
            "core_boundary_minute": {"treated": stop_t, "untreated": stop_u}}


def _p60(ctx, rate, scale, kernel, fraction=None) -> float:
    treated, _ = run(ctx["scenarios"]["FR-G"], 61, rate=rate, scale=scale, kernel=kernel, fraction=fraction)
    plain, _ = run(ctx["untreated"][FRG_CASE], 61, rate=rate, scale=scale, fraction=fraction, drop_fluid=True)
    return protection(treated, plain, 60)


def section_rate_crystalloid(ctx, inversion) -> dict:
    s0, c0, kernels = ctx["s0"], ctx["c0"], ctx["kernels"]
    current = {}
    for label, item in inversion["witnesses"].items():
        current[label] = {name: _frg_row(ctx, rate=item["rate_ml_min"], scale=s0, kernel=kernel) for name, kernel in kernels.items()}
        current[label]["admitted_for_72f_by_u_out"] = item["cases"][FRG_CASE]["u_out"]
    current_edges = {}
    # under the current map a fast enough bleed ends the untreated run at the core's own boundary before minute 60: beyond it nothing is readable
    readable_to = bisect(lambda value: _p60(ctx, value, s0, None) is not None, ctx["rate0"], ctx["rate0"] * 8.0) - 2.0 * TOLERANCE
    for name, kernel in kernels.items():
        current_edges[name] = {"fastest_rate_whose_untreated_course_reaches_minute_60": readable_to}
        for edge_name, level in (("closer_to_untreated_p60_one_half", CLOSER_TO_UNTREATED_BELOW), ("modest_p60_one_third", MODEST_BELOW)):
            if _p60(ctx, readable_to, s0, kernel) >= level:
                current_edges[name][edge_name] = {"rate_ml_min": None, "reached": False,
                                                  "why": "the untreated course meets the core's boundary before minute 60 at every rate fast enough: the level is not reachable under the current map"}
                continue
            slowest = ctx["rate0"] * 0.5
            if _p60(ctx, slowest, s0, kernel) < level:                 # already below the level at the slowest rate tried: the edge is not above it
                rate = slowest
            else:
                rate = bisect(lambda value: _p60(ctx, value, s0, kernel) < level, slowest, readable_to)
            plain, stopped = run(ctx["untreated"][FRG_CASE], HORIZON, rate=rate, drop_fluid=True)
            current_edges[name][edge_name] = {"rate_ml_min": rate, "reached": True, "untreated_u_out_72f": u_out(FRG_CASE, rate, s0, COMMITTED_FRACTION),
                                              "untreated_sbp_at_60": plain[60]["sbp"], "untreated_sbp_at_120": plain[120]["sbp"] if len(plain) > 120 else None,
                                              "untreated_core_boundary_minute": stopped}
    joint_edges = {}
    for name, kernel in kernels.items():
        joint_edges[name] = {}
        for edge_name, level in (("closer_to_untreated_p60_one_half", CLOSER_TO_UNTREATED_BELOW), ("modest_p60_one_third", MODEST_BELOW)):
            smallest = s0 * 0.5
            if _p60(ctx, c0 * smallest, smallest, kernel) < level:     # already below the level at the smallest scale tried
                scale = smallest
            else:
                scale = bisect(lambda value: _p60(ctx, c0 * value, value, kernel) < level, smallest, s0 * 8.0)
            joint_edges[name][edge_name] = {"scale_ml_eq": scale, "rate_ml_min": c0 * scale, "inside_the_declared_scale_band": DECLARED_SCALE_BAND[0] <= scale <= DECLARED_SCALE_BAND[1],
                                            "one_unit_output_gain_72f": one_unit(FRG_CASE, scale, COMMITTED_FRACTION)["output_gain"]}
    fd02_edge = bisect(lambda value: one_unit(FRG_CASE, value, COMMITTED_FRACTION)["fd_bld_02"], s0 * 0.9, s0 * 1.2)
    joint_witnesses = [("REFERENCE", s0, "the current point"), ("FD_BLD_02_EDGE_72F", fd02_edge + 2 * TOLERANCE, "the smallest scale at which one red-cell unit stays inside the faculty envelope FD-BLD-02 for 72f"),
                       ("DECLARED_BAND_TOP", DECLARED_SCALE_BAND[1], "the upper edge of the declared CANDIDATE band of the preload scale")]
    for name in kernels:
        for edge_name, item in joint_edges[name].items():
            joint_witnesses.append((f"EDGE_{edge_name.upper()}__{name}", item["scale_ml_eq"] * EDGE_WITNESS_STEP,
                                    f"half a percent beyond the scale at which FR-G reaches {edge_name} with the {name} kernel (a derived edge, not a chosen probe)"))
    joint = {}
    for label, scale, why in joint_witnesses:
        units = {case: one_unit(case, scale, COMMITTED_FRACTION) for case in CASES}
        joint[label] = {"why": why, "outside_the_declared_scale_band": not (DECLARED_SCALE_BAND[0] <= scale <= DECLARED_SCALE_BAND[1]),
                        "one_unit": units, "sbp_rise_per_red_cell_unit_at_arrival_mmHg": {case: units[case]["output_gain"] * ARRIVAL_SBP[case] for case in CASES},
                        **{name: _frg_row(ctx, rate=c0 * scale, scale=scale, kernel=kernel) for name, kernel in kernels.items()}}
    # the most favourable corner of every DECLARED domain: the top of the scale band, each case at the upper edge of its own arrival-position band
    from clinical_core import gi_reference
    positions = {case: gi_reference.case_bands(case)["preload_fraction"].upper for case in CASES}
    top = DECLARED_SCALE_BAND[1]
    tops = {case: u_out_interval(case, top, positions[case], INSIDE_C[(case, positions[case])])[1] for case in CASES}
    common_rate = min(tops.values()) - 2 * TOLERANCE
    corner = {"scale_ml_eq": top, "arrival_positions": positions, "fastest_rate_admitted_by_u_out_ml_min": tops, "common_rate_ml_min": common_rate,
              "u_out_both_cases": {case: u_out(case, common_rate, top, positions[case]) for case in CASES},
              "one_unit": {case: one_unit(case, top, positions[case]) for case in CASES},
              **{name: _frg_row(ctx, rate=common_rate, scale=top, kernel=kernel, fraction=positions[FRG_CASE]) for name, kernel in kernels.items()},
              "p2i2x_registered_viable_rates": [5, 6], "p2i2x_first_nonviable_rate": 7}
    return {"classes": {"NEAR_STABILIZATION": f"p60 >= {NEAR_STABILIZATION_FROM}", "SUBSTANTIAL_PROTECTION": f"{MODEST_BELOW:.4f} <= p60 < {NEAR_STABILIZATION_FROM}",
                        "MODEST_TRANSIENT_ATTENUATION": f"{MINIMAL_BELOW} <= p60 < {MODEST_BELOW:.4f} and fading by 120", "MINIMAL_EFFECT": f"0 <= p60 < {MINIMAL_BELOW}",
                        "WORSE_THAN_EXPECTED": "p60 < 0", "note": "a descriptive convention of this analysis, declared before classifying; not a faculty definition and not a fitting objective"},
            "kernels": {name: {"e": k[0], "s": k[1], "tau": k[2]} for name, k in kernels.items()},
            "current_map_witnesses": current, "current_map_edges": current_edges, "joint_witnesses_at_the_accepted_untreated_course": joint, "joint_edges": joint_edges,
            "fd_bld_02_smallest_scale_72f": fd02_edge, "declared_domain_most_favourable_corner": corner}


# -- P3-322: the other reviewed scenarios, qualitatively -------------------------------------------------------------------------------------------

def _first_below(rows, level, after: int):
    return next((row["minute"] for row in rows if row["minute"] > after and row["sbp"] < level), None)


def section_nonregression(ctx, crystalloid) -> dict:
    s0, c0, kernels = ctx["s0"], ctx["c0"], ctx["kernels"]
    runtime, region = "RUNTIME_OUTSIDE_THE_CLOSED_REGION", "CLOSED_REGION_LEAST_PROTECTIVE"
    edges = crystalloid["joint_edges"]
    witnesses = [("REFERENCE", s0, runtime), ("DECLARED_BAND_TOP", DECLARED_SCALE_BAND[1], runtime), ("DECLARED_BAND_TOP__REGION_KERNEL", DECLARED_SCALE_BAND[1], region),
                 ("EDGE_MODEST__RUNTIME", edges[runtime]["modest_p60_one_third"]["scale_ml_eq"] * EDGE_WITNESS_STEP, runtime),
                 ("EDGE_MODEST__REGION", edges[region]["modest_p60_one_third"]["scale_ml_eq"] * EDGE_WITNESS_STEP, region)]
    reviewed = {scenario_id: fa.reviewed_timeline(scenario_id) for scenario_id in ctx["scenarios"]}
    out = {}
    for label, scale, kernel_name in witnesses:
        rate, kernel, row = c0 * scale, kernels[kernel_name], {}
        for scenario_id, scenario in ctx["scenarios"].items():
            minutes = sorted(reviewed[scenario_id])
            rows, stopped = run(scenario, max(minutes), rate=rate, scale=scale, kernel=kernel)
            sbp = {str(m): (rows[m]["sbp"] if m < len(rows) else None) for m in minutes}
            entry = {"sbp_at_the_reviewed_minutes": sbp, "reviewed_committed_sbp": {str(m): reviewed[scenario_id][m][0] for m in minutes}, "core_boundary_minute": stopped}
            series = [rows[m]["sbp"] for m in minutes if m < len(rows)]
            if scenario_id in ("FR-A", "FR-D"):
                entry["progressive_deterioration"] = all(b < a for a, b in zip([rows[0]["sbp"]] + series, series))
            elif scenario_id == "FR-B":
                entry["early_response_above_arrival"] = series[-1] > rows[0]["sbp"]
            elif scenario_id in ("FR-C", "FR-E"):
                nadir = rows[120]["sbp"]
                entry["rises_after_treatment"] = series[-1] > nadir
                entry["share_of_the_fall_recovered_at_the_last_reviewed_minute"] = (series[-1] - nadir) / (rows[0]["sbp"] - nadir)
                entry["ends_above_arrival"] = series[-1] > rows[0]["sbp"]
            row[scenario_id] = entry
        frg_row = _frg_row(ctx, rate=rate, scale=scale, kernel=kernel)
        row["FR-G"]["class"] = frg_row["class"]
        row["FR-G"]["share_of_untreated_pressure_fall_prevented_at_60"] = frg_row["share_of_untreated_pressure_fall_prevented"]["60"]
        long_horizon = {}
        for case in CASES:
            rows, stopped = run(ctx["early"][case], HORIZON, rate=rate, scale=scale, kernel=kernel)
            peak = max(rows, key=lambda item: item["sbp"])
            long_horizon[case] = {"arrival_sbp": rows[0]["sbp"], "peak": {"minute": peak["minute"], "sbp": peak["sbp"], "rise_over_arrival": peak["sbp"] - rows[0]["sbp"]},
                                  "sbp": {str(m): (rows[m]["sbp"] if m < len(rows) else None) for m in (60, 120, 240)},
                                  "reverses_after_the_peak": rows[-1]["sbp"] < peak["sbp"], "plateau_in_the_last_hour": abs(rows[-1]["sbp"] - rows[-61]["sbp"]) < 1.0,
                                  "below_arrival_again_at_minute": _first_below(rows, rows[0]["sbp"], peak["minute"]), "core_boundary_minute": stopped,
                                  "bleeding_ml_min_distinct": sorted({round(item["bleed_ml_min"], 9) for item in rows[1:]})}
        out[label] = {"rate_ml_min": rate, "scale_ml_eq": scale, "kernel": kernel_name, "scenarios": row, "early_treatment_to_240_min_without_source_control": long_horizon,
                      "one_unit": {case: one_unit(case, scale, COMMITTED_FRACTION) for case in CASES},
                      "sbp_rise_per_red_cell_unit_at_arrival_mmHg": {case: one_unit(case, scale, COMMITTED_FRACTION)["output_gain"] * long_horizon[case]["arrival_sbp"] for case in CASES}}
    reference = out["REFERENCE"]["scenarios"]
    matches = all(round(reference[sid]["sbp_at_the_reviewed_minutes"][m]) == reference[sid]["reviewed_committed_sbp"][m] for sid in reference for m in reference[sid]["reviewed_committed_sbp"])
    untreated_same = all(abs(out[label]["scenarios"][sid]["sbp_at_the_reviewed_minutes"][m] - reference[sid]["sbp_at_the_reviewed_minutes"][m]) < 1e-9
                         for label in out for sid in ("FR-A", "FR-D") for m in reference[sid]["sbp_at_the_reviewed_minutes"])
    return {"witnesses": out, "reference_reproduces_the_reviewed_pressures": matches, "untreated_courses_identical_at_every_joint_witness": untreated_same,
            "fr_f": "unchanged by construction: the unsupported norepinephrine order stops the experiment before any rate or map matters; nothing here touches the stop",
            "note": "the accepted human judgments are NOT numerical targets; a joint rescale changes the magnitude of every TREATED course, so the acceptance of FR-B, FR-C and FR-E does not transfer to another scale without a new human review"}


# -- P3-321, P3-323, P3-324: the region, the candidate and the verdict ------------------------------------------------------------------------------

def section_region(ctx, inversion, identifiability, crystalloid) -> dict:
    c_band = [value / ctx["s0"] for value in inversion["u_out_common_interval_ml_min"]]
    corner = crystalloid["declared_domain_most_favourable_corner"]
    runtime, region = "RUNTIME_OUTSIDE_THE_CLOSED_REGION", "CLOSED_REGION_LEAST_PROTECTIVE"
    return {"name": "GI_BLEED_RATE_PRESSURE_JOINT_DEVELOPMENT_REGION", "status": "ANALYSIS_REGION__NOT_APPROVED__NOT_A_RATE_INTERVAL",
            "a_rate_interval_alone_is_defined": False,
            "why_no_rate_interval": "the untreated evidence bounds rate / scale only; a rate has no meaning until its pressure scale is named (P3-319 verdict B)",
            "coordinates": {"c_rate_over_scale_per_min": {"band_at_position_0_5_common_to_both_cases": c_band, "source": "U-OUT, frozen faculty envelopes", "current_value": ctx["c0"],
                                                          "current_inside": c_band[0] <= ctx["c0"] <= c_band[1]},
                            "scale_ml_eq": {"lower_edge": crystalloid["fd_bld_02_smallest_scale_72f"], "lower_edge_source": "FD-BLD-02 upper envelope, 72f (one unit must not raise output more than 30 %)",
                                            "upper_edge": DECLARED_SCALE_BAND[1], "upper_edge_source": "the declared CANDIDATE band of preload_curve_scale_ml: a declared domain, NOT evidence; OPEN",
                                            "current_value": ctx["s0"], "current_inside": ctx["s0"] >= crystalloid["fd_bld_02_smallest_scale_72f"]}},
            "implied_absolute_rate_ml_min": {"lower_corner_at_position_0_5": c_band[0] * crystalloid["fd_bld_02_smallest_scale_72f"],
                                             "top_of_the_declared_band_at_position_0_5": [c_band[0] * DECLARED_SCALE_BAND[1], c_band[1] * DECLARED_SCALE_BAND[1]],
                                             "most_favourable_declared_corner_common_rate": corner["common_rate_ml_min"],
                                             "earlier_registered_viable_rates_P2I_2X": [5, 6]},
            "the_current_point": {"rate_ml_min": ctx["rate0"], "scale_ml_eq": ctx["s0"], "inside_the_joint_region": False,
                                  "why": "rate / scale is 1.95 % below the common U-OUT band and the scale is below the FD-BLD-02 edge for 72f: it sits just outside the LOW corner"},
            "where_fr_g_falls": {"at_the_current_point": {name: crystalloid["joint_witnesses_at_the_accepted_untreated_course"]["REFERENCE"][name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)},
                                 "at_the_top_of_the_declared_band": {name: crystalloid["joint_witnesses_at_the_accepted_untreated_course"]["DECLARED_BAND_TOP"][name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)},
                                 "at_the_most_favourable_declared_corner": {name: corner[name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)},
                                 "rate_needed_for_one_third": {name: crystalloid["joint_edges"][name]["modest_p60_one_third"]["rate_ml_min"] for name in (runtime, region)},
                                 "rate_needed_for_one_half": {name: crystalloid["joint_edges"][name]["closer_to_untreated_p60_one_half"]["rate_ml_min"] for name in (runtime, region)}},
            "shared_or_case_specific": {"verdict": "ONE_FAMILY_REGION_SERVES_BOTH_CASES", "why": "the common U-OUT band is non-empty at the committed position and at the top of the declared band; the absolute scale is bounded by FD-BLD-02 in 72f and FR-G was reviewed in 72f only; no case states a rate, so no case-specific rate is introduced (policy CASE_OVERRIDES_FAMILY_DEFAULT stays as declared)"},
            "confidence": {"that_the_rate_is_identified_only_jointly_with_the_scale": 0.95, "that_the_current_point_is_outside_at_the_low_corner": 0.9,
                           "that_an_admissible_absolute_rate_is_well_above_2_5": 0.8,
                           "in_any_single_number_for_the_fr_g_edge": 0.5,
                           "note": "judgments of the analyst, not statistics: the last one is low because it rests on ONE reviewer's qualitative judgment and on a descriptive class boundary"},
            "uncertainty": ["one human reviewer, one slow-infusion scenario, one case", "the class boundary (one half or one third) is a convention", "the arrival position f is kept at the committed 0.5 except at the declared corner",
                            "the crystalloid kernel itself is undecided: the runtime point is outside the closed region, and a closed-region kernel protects more"],
            "falsifiers": ["a faculty anchor on the blood response (how much one red-cell unit should raise pressure at arrival) that keeps the scale at or below about 1500 mL-eq: then closed-region kernels leave FR-G above one half inside the band and the conflict returns to the crystalloid region",
                           "a verified authored rate or volume in either case", "a second reviewer finding the current FR-G acceptable", "any evidence that the protection of an infusion depends on the pressure map (measured here: it does not)"]}


def decide(ctx, inversion, identifiability, crystalloid, nonregression) -> dict:
    runtime, region = "RUNTIME_OUTSIDE_THE_CLOSED_REGION", "CLOSED_REGION_LEAST_PROTECTIVE"
    joint, corner = crystalloid["joint_witnesses_at_the_accepted_untreated_course"], crystalloid["declared_domain_most_favourable_corner"]
    trade_off = {label: {"rate_ml_min": item["rate_ml_min"], "scale_ml_eq": item["scale_ml_eq"], "kernel": item["kernel"],
                         "fr_g_share_prevented_at_60": item["scenarios"]["FR-G"]["share_of_untreated_pressure_fall_prevented_at_60"], "fr_g_class": item["scenarios"]["FR-G"]["class"],
                         "sbp_rise_per_red_cell_unit_at_arrival_mmHg": item["sbp_rise_per_red_cell_unit_at_arrival_mmHg"],
                         "fr_b_peak_rise_over_arrival_mmHg": item["early_treatment_to_240_min_without_source_control"]["gi_bleed_57m"]["peak"]["rise_over_arrival"],
                         "fr_b_below_arrival_again_at_minute": item["early_treatment_to_240_min_without_source_control"]["gi_bleed_57m"]["below_arrival_again_at_minute"],
                         "fr_e_share_of_fall_recovered": item["scenarios"]["FR-E"]["share_of_the_fall_recovered_at_the_last_reviewed_minute"],
                         "fr_e_ends_above_arrival": item["scenarios"]["FR-E"]["ends_above_arrival"]} for label, item in nonregression["witnesses"].items()}
    admitted = [label for label, item in crystalloid["current_map_witnesses"].items() if item["admitted_for_72f_by_u_out"]]
    rate_alone = any(crystalloid["current_map_witnesses"][label][runtime]["class"] == "MODEST_TRANSIENT_ATTENUATION" for label in admitted)
    best_admitted = min(crystalloid["current_map_witnesses"][label][runtime]["share_of_untreated_pressure_fall_prevented"]["60"] for label in admitted)
    joint_exists = all("modest_p60_one_third" in crystalloid["joint_edges"][name] for name in (runtime, region))
    inside_band = {name: crystalloid["joint_edges"][name]["modest_p60_one_third"]["inside_the_declared_scale_band"] for name in (runtime, region)}
    verdict = "A" if rate_alone else ("B" if (identifiability["verdict"] == "B" and joint_exists) else "UNCLASSIFIED")
    return {"rate_alone_under_the_current_map_resolves_fr_g": rate_alone, "admitted_current_map_witnesses_for_72f": admitted,
            "smallest_p60_among_admitted_current_map_witnesses": best_admitted,
            "a_joint_rescale_can_reach_modest_attenuation": joint_exists, "modest_edge_inside_the_declared_scale_band": inside_band,
            "fr_g_v2_candidate": {"generated": False, "why": "P3-323 allows a candidate ONLY if a defensible bleed-rate region ALONE resolves the conflict; it does not (the rate cannot move without the pressure scale), so no V2 is fabricated"},
            "amendment_3_decision": {"verdict": verdict, "name": {"A": "BLEED_RATE_SCALE_EXPLAINS_FR_G_CONFLICT", "B": "JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED"}.get(verdict, "UNCLASSIFIED"),
                                     "amendment_3": "NOT_OPENED__UNRESOLVED",
                                     "fr_g_share_prevented_at_60": {"current_point": {name: joint["REFERENCE"][name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)},
                                                                    "top_of_the_declared_band_committed_position": {name: joint["DECLARED_BAND_TOP"][name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)},
                                                                    "most_favourable_declared_corner": {name: corner[name]["share_of_untreated_pressure_fall_prevented"]["60"] for name in (runtime, region)}},
                                     "exact_reason": "the absolute rate is identified only jointly with the pressure scale. On the joint manifold FR-G's protection falls as the scale grows (it reads retained / shed), and the response to red cells falls with it, because both are volume in the same millilitres. Inside every declared domain a closed-region crystalloid kernel still prevents 0.40 to 0.58 of the untreated fall; reaching one third needs a scale beyond the declared band, where two units of red cells raise pressure only a few mmHg above arrival. Where that trade is acceptable is a faculty anchor on the blood response, which this analysis cannot supply",
                                     "the_trade_off_on_the_joint_manifold": trade_off,
                                     "why_not": {"A": "under the current map no rate the untreated faculty envelopes admit for 72f brings FR-G below one half",
                                                 "C": "the conflict does not yet PERSIST after a defensible scale, because the defensible scale is not decided; C becomes the verdict if the faculty anchors the blood response at a scale where a closed-region kernel still over-protects",
                                                 "D": "the absolute scale is identifiable through treated behaviour in real mL",
                                                 "E": "no structural defect was found: mass balance, map and kernel behave as declared"}}}


def build() -> dict:
    ctx = build_context()
    provenance = section_provenance(ctx)
    authored = section_authored(ctx)
    scale = section_current_scale(ctx)
    inversion = section_untreated_inversion(ctx)
    identifiability = section_identifiability(ctx, inversion)
    crystalloid = section_rate_crystalloid(ctx, inversion)
    nonregression = section_nonregression(ctx, crystalloid)
    region = section_region(ctx, inversion, identifiability, crystalloid)
    record = {"record_type": "GI_BLEED_RATE_SCALE_ANALYSIS", "version": VERSION, "evidence_class": EVIDENCE_CLASS, "executable_change": False,
              "what_it_is": "A read-only analysis of the absolute scale of the GI bleed rate after the first human faculty review. MODEL_ANALYSIS: it approves no rate, no pressure parameter and no region, and it is not clinical validation.",
              "depends_on": {"frg_crystalloid_analysis_record_digest": ctx["frg_record_digest"]},
              "provenance": provenance, "authored_cases": authored, "current_scale": scale, "untreated_inversion": inversion, "identifiability": identifiability,
              "rate_x_crystalloid": crystalloid, "joint_region": region, "nonregression": nonregression, "decision": decide(ctx, inversion, identifiability, crystalloid, nonregression)}
    record = fa._round(record)
    record["record_digest"] = digest(record)
    return record


def digest(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()


def load_record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    result = build()
    if os.environ.get(WRITE_FLAG) == "1":
        RECORD_PATH.write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=True) + "\n", encoding="utf-8")
        print("written", RECORD_PATH, result["record_digest"])
    else:
        print(result["record_digest"], result["identifiability"]["verdict"], result["decision"]["amendment_3_decision"]["verdict"])
