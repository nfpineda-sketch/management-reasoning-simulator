"""P3-402 to P3-405: the BUILDER and SOURCE AUDIT of the multifamily tone review set (a tool, never imported by a page; it holds no test).

WHAT IT DOES. It assembles the review set ``COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW`` from sources that are ALREADY certified, and proves, scenario by scenario, that what it assembled IS what they hold:

* FR-F: the per-minute CENTER_REFERENCE rows of the stored candidate record ``PHASE3_FRF_TONE_V1_CANDIDATE.json``, taken unchanged (nothing is recomputed);
* ACS, PULM-EDEMA, PE: the certified harness call (``test_tone_pathway_analysis.shadow_run`` with the same order, minute, witness and horizon the stored family probes used), whose observed values, causal facts and
  unmapped reference are compared with the stored record ``PHASE3_COMMON_TONE_PROBES.json`` and must be EQUAL;
* SYNTH: the common core's synthetic distributive probe, run with the same anchors, burden and infusion the stored probe used, whose pressure at the stored minutes must be EQUAL to the stored values.

It sets NO parameter, tunes nothing, substitutes no witness and adds no physiology: LOW and HIGH are the other two witnesses of the same certified region, computed by the same calls, and they are stored apart from the items
(only the optional sensitivity check, after every scenario is submitted, can show them). The set is a VERSIONED historical record (provenance, seal, index); ``write_all`` refuses to replace it with other bytes.
The review modules are left out of the generating-code fingerprint on purpose: the one that loads the set holds its digest pin, and a pin cannot be part of what it pins.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import clinical_cases as cc
import faculty_tone_review as ftm
import historical_records as hr
import test_tone_pathway_analysis as ta

ROOT = Path(__file__).resolve().parent
SET_PATH = ftm.SET_PATH
GENERATED_ON = "2026-11-18"
DECISIONS = "FD-TONE-01 to FD-TONE-12 (the pathway); the faculty request of 2026-11-18 (the review)"
REVIEW_MODULES = ("faculty_tone_review.py", "faculty_tone_review_ui.py")
CENTER, LOW, HIGH = "CENTER_REFERENCE", "LOW", "HIGH"
HORIZON_FAMILY, ORDER_FAMILY = ta.PROBE_MINUTES, ta.PROBE_ORDER_MINUTE
HORIZON_SYNTH, ORDER_SYNTH = 40, 10
TABLE_MINUTES = {"FR-F": [0, 2, 4, 7, 12, 17, 24, 32], "SYNTH": [0, 4, 10, 12, 14, 20, 30, 40], "ACS": [0, 5, 7, 10, 15, 20, 25, 30], "PULM-EDEMA": [0, 5, 7, 10, 15, 20, 25, 30],
                 "PE": [0, 5, 7, 10, 15, 20, 25, 30]}
#: The five scenarios the faculty named as required, with the optional two that were considered. ``family`` and ``case`` name the certified source.
FAMILIES = {"ACS": ("acs", "acs_70f_left_main"), "PULM-EDEMA": ("pulmonary_edema", "pulmonary_edema_58m"), "PE": ("pulmonary_embolism", "pulmonary_embolism_61m")}
OPTIONAL = {"opioid": ("opioid", "opioid_35m"), "asthma": ("asthma", "asthma_49m")}
PURPOSES = {
    "FR-F": "Does norepinephrine produce a pressure response with an appropriate direction, timing, and magnitude in this patient with ongoing hemorrhage, without implying that vasopressor support corrects the underlying volume loss?",
    "SYNTH": "Does vascular-tone support move pressure toward a more plausible state without creating flow or volume?",
    "ACS": "Does the pressure response to norepinephrine remain clinically defensible in a patient whose forward flow is limited, without implying that vasoconstriction corrects pump failure?",
    "PULM-EDEMA": "Does norepinephrine produce a pressure response that is directionally plausible without overstating benefit in a congested, pump-limited patient?",
    "PE": "Does norepinephrine produce a plausible pressure response in an obstructive low-flow state without implying correction of the underlying obstruction?"}
SHORT = {"FR-F": "GI hemorrhage", "SYNTH": "Low-tone probe", "ACS": "ACS", "PULM-EDEMA": "Pulm. edema", "PE": "Pulm. embolism"}
TITLES = {"FR-F": "57-year-old man with an upper gastrointestinal bleed: norepinephrine during ongoing hemorrhage",
          "SYNTH": "SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE: loss of vascular tone, then norepinephrine",
          "ACS": "70-year-old woman with a left main acute coronary syndrome: norepinephrine with limited forward flow",
          "PULM-EDEMA": "58-year-old man with hypertensive pulmonary edema: norepinephrine in a congested, pump-limited patient",
          "PE": "61-year-old man with a high-risk pulmonary embolism: norepinephrine in an obstructive low-flow state"}
LIMITATIONS = (
    {"id": "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED",
     "text": "How strongly the pressure response depends on the state of the pump is not yet validated. The ACS and pulmonary-edema judgments inform whether the pathway is acceptable for development; they do not support educational promotion."},
    {"id": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED",
     "text": "Consciousness under vascular-tone support was neither shown nor judged in this review. It remains unresolved."},
    {"id": "TITRATION_AND_STOP_NOT_SUPPORTED",
     "text": "Only a single start of norepinephrine at a fixed rate is represented. Titration, rate changes and stopping the infusion are not supported."})
EXCLUSION_REASONS = {
    "opioid": ("the exact certified trajectory can be generated and equals the stored probe, but it is not clinically meaningful for this question: the authored patient is normotensive (arrival {sbp}/{dbp} mmHg) and the "
               "case is a respiratory-depression physiology, so a vasopressor order has no indication and judging its pressure response would ask the reviewer about a response nobody would elicit"),
    "asthma": ("the exact certified trajectory can be generated and equals the stored probe, but it is not clinically meaningful for this question: the authored patient is already hypertensive (arrival {sbp}/{dbp} mmHg) and the "
               "case is a respiratory-failure physiology, so a vasopressor order has no indication and judging its pressure response would ask the reviewer about a response nobody would elicit")}
UNREPRESENTED = ("heart rate and capillary refill are not recomputed for these trajectories and are not stored with them",
                 "the tone state, flow, oxygen delivery, oxygen debt, consciousness and collapse state are model state: they are not stored with the items and never drawn")


# -- the generating code and the sources -------------------------------------------------------------------------------------------------------------------------------
def generating_code() -> dict:
    """What generated the set, by content: the live common core, every application module EXCEPT the two review modules (see the module docstring), and the two harnesses."""
    from clinical_core import amendment_3 as a3
    modules = {name: digest for name, digest in ta.application_modules().items() if name not in REVIEW_MODULES}
    return {"clinical_core": a3.amended_core_digest_now(), "application_modules": hr.digest_of(modules), "application_module_count": len(modules), "excluded_review_modules": list(REVIEW_MODULES),
            "test_tone_pathway_analysis.py": ta._sha(ROOT / "test_tone_pathway_analysis.py"), "test_tone_review_analysis.py": ta._sha(Path(__file__).resolve())}


def sources() -> dict:
    """The two stored certified records, with their file digests and seals."""
    out = {}
    for name, path in (("frf", ta.CANDIDATE_PATH), ("probes", ta.PROBES_PATH)):
        record = ta.load(path)
        out[name] = {"path": str(path.relative_to(ROOT)), "record": record, "file_sha256": ta._sha(path), "record_digest": record["record_digest"], "record_id": record["provenance"]["record_id"]}
    return out


def _case(case_id: str) -> dict:
    return cc.variant_by_id(case_id)


def _arrival(case: dict) -> dict:
    observed = case["observable"]
    sbp, dbp = int(observed["sbp"]), int(observed["dbp"])
    return {"sbp": sbp, "dbp": dbp, "map": int(round((sbp + 2 * dbp) / 3)), "spo2": int(observed["spo2"]), "rr": int(observed["respiratory_rate"])}


def _exam(case: dict, key: str) -> str:
    return f"{key}: {case['examination'][key]}"


def _scan(case: dict, key: str, label: str) -> str:
    return f"Bedside ultrasound, {label}: {case['investigations']['pocus']['result'][key]}"


def _facts(scenario_id: str, case: dict) -> list:
    """The authored baseline facts the reviewer needs, quoted from the authored case (never composed from the model)."""
    return {"FR-F": lambda: [_exam(case, "Abdomen"), _scan(case, "lv", "left ventricle"), _scan(case, "ivc", "inferior vena cava"), f"Hemoglobin {case['engine']['baseline_hemoglobin']} g/dL"],
            "ACS": lambda: [_exam(case, "Respiratory"), _scan(case, "lv", "left ventricle"), _scan(case, "ivc", "inferior vena cava"), _scan(case, "lungs", "lungs")],
            "PULM-EDEMA": lambda: [_exam(case, "Respiratory"), _scan(case, "lv", "left ventricle"), _scan(case, "ivc", "inferior vena cava"), _scan(case, "lungs", "lungs")],
            "PE": lambda: [_scan(case, "rv", "right ventricle"), _scan(case, "lv", "left ventricle"), _scan(case, "ivc", "inferior vena cava"), _exam(case, "Extremities")]}[scenario_id]()


def _points(rows: list) -> list:
    return [ta.displayed(row) for row in rows]


def _item(scenario_id: str, *, kind: str, context: str, facts: list, arrival: dict, minute: int, horizon: int, common: list) -> dict:
    probe = kind == ftm.KIND_PROBE
    rate = f"{ta.PROBE_RATE:g}"
    return {"scenario_id": scenario_id, "short": SHORT[scenario_id], "title": TITLES[scenario_id], "kind": kind, "banner": ftm.PROBE_BANNER if probe else ftm.CASE_BANNER, "note": ftm.PROBE_NOTE if probe else ftm.CASE_NOTE,
            "context": context, "baseline_facts": facts, "purpose": PURPOSES[scenario_id], "arrival": arrival,
            "intervention": (f"Norepinephrine {rate} mcg/min, started at minute {minute} and kept at that rate to the end. Nothing else is given or changed"
                             + ("." if probe else "; the underlying problem is left untreated.")),
            "timeline": [{"n": 1, "minute": minute, "advance": horizon - minute, "action": f"Start norepinephrine {rate} mcg/min",
                          "result": f"Infusion kept at {rate} mcg/min to minute {horizon} (no titration, no stop)", "executed": True, "intervention": True}],
            "common": common, "table_minutes": TABLE_MINUTES[scenario_id], "stopped": False, "required": True}


# -- the five scenarios ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def frf(source: dict) -> dict:
    """FR-F: the stored candidate's CENTER_REFERENCE rows, unchanged. Its own displayed pressures at the reassessments must equal what the rows display (the audit)."""
    record = source["frf"]["record"]
    scenario, case = record["scenario"], _case(record["scenario"]["case_id"])
    witnesses = record["witnesses"]
    rows = witnesses[CENTER]["per_minute"]
    common = _points(rows)
    stored = [dict(row) for row in witnesses[CENTER]["displayed_pressure"]]
    seen = [point for point in common if point["minute"] in {row["minute"] for row in stored}]
    audit = {"source_record": source["frf"]["path"], "source_record_id": source["frf"]["record_id"], "source_record_digest": source["frf"]["record_digest"], "source_file_sha256": source["frf"]["file_sha256"],
             "taken_from": "witnesses.CENTER_REFERENCE.per_minute, minutes 0 to 32, unchanged (nothing recomputed)", "recomputed": False,
             "displayed_pressure_at_the_reassessments_equals_the_stored_ones": seen == stored, "reassessment_minutes": [row["minute"] for row in stored],
             "order_in_the_record": scenario["order_as_mirrored"], "order_minute_in_the_record": scenario["order_minute"], "the_order_minute_and_rate_shown_are_the_record_s": (scenario["order_minute"], scenario["order_as_mirrored"]["rate"]) == (2, ta.PROBE_RATE)}
    case_arrival = _arrival(case)
    audit["first_point_is_the_authored_arrival"] = (common[0]["sbp"], common[0]["dbp"], common[0]["map"]) == (case_arrival["sbp"], case_arrival["dbp"], case_arrival["map"])
    low, high = _points(witnesses[LOW]["per_minute"]), _points(witnesses[HIGH]["per_minute"])
    context = f"{case['presentation']} Authored diagnosis: {case['faculty']['diagnosis']}."
    item = _item("FR-F", kind=ftm.KIND_CASE, context=context, facts=_facts("FR-F", case), arrival=case_arrival, minute=int(scenario["order_minute"]), horizon=common[-1]["minute"], common=common)
    return {"item": item, "low": low, "high": high, "audit": audit}


def family(scenario_id: str, source: dict, *, case_key: tuple | None = None) -> dict:
    """ACS, PULM-EDEMA and PE (and the optional two, for the exclusion audit): the certified harness call, compared with the stored family probe."""
    name, case_id = case_key or FAMILIES[scenario_id]
    events = (ta.order_event(ORDER_FAMILY),)
    reference = ta.shadow_run(name, case_id, None, events, HORIZON_FAMILY, scenario_id=f"{ta.PROBES_VERSION}::{name}::{ta.NOT_MAPPED}")
    runs = {witness: ta.shadow_run(name, case_id, witness, events, HORIZON_FAMILY, scenario_id=f"{ta.PROBES_VERSION}::{name}::{witness}") for witness in (LOW, CENTER, HIGH)}
    stored = source["probes"]["record"]["family_probes"][name]
    centre = runs[CENTER]
    equal = {"observed_equals_stored": [ta.observed(reference["rows"], centre["rows"], minute) for minute in (ORDER_FAMILY + 2, ORDER_FAMILY + 5, HORIZON_FAMILY)] == stored["witnesses"][CENTER]["observed"],
             "causal_facts_equal_stored": ta.causal_facts(reference["rows"], centre["rows"], ORDER_FAMILY, centre["profile_gain"]) == stored["witnesses"][CENTER]["facts"],
             "unmapped_reference_equals_stored": (reference["rows"][ORDER_FAMILY], reference["rows"][HORIZON_FAMILY]) == (stored["without_the_mapping"]["at_the_order"], stored["without_the_mapping"]["at_the_end"]),
             "case_id_equals_stored": stored["case_id"] == case_id and stored["order_minute"] == ORDER_FAMILY}
    for witness in (LOW, HIGH):
        equal[f"{witness.lower()}_observed_equals_stored"] = ([ta.observed(reference["rows"], runs[witness]["rows"], minute) for minute in (ORDER_FAMILY + 2, ORDER_FAMILY + 5, HORIZON_FAMILY)]
                                                              == stored["witnesses"][witness]["observed"])
    clean = {"replays_exactly": all(run["replay_equal"] and run["same_states_as_the_runner"] for run in runs.values()),
             "no_gap_and_no_failure": all(not run["gaps"] and not run["failures"] for run in runs.values()),
             "the_order_is_built": all([item["disposition"] for item in run["dispositions"] if item["kind"] == "norepinephrine"] == ["BUILT"] for run in runs.values()),
             "stored_run_replays_exactly": all(stored["witnesses"][witness]["replays_exactly"] for witness in (LOW, CENTER, HIGH))}
    case = _case(case_id)
    arrival = _arrival(case)
    common = _points(centre["rows"])
    audit = {"source_record": source["probes"]["path"], "source_record_id": source["probes"]["record_id"], "source_record_digest": source["probes"]["record_digest"], "source_file_sha256": source["probes"]["file_sha256"],
             "taken_from": (f"the certified harness call (test_tone_pathway_analysis.shadow_run: the family's registered mapping plus the declared reader, witness {CENTER}, a start at {ta.PROBE_RATE:g} mcg/min at "
                            f"minute {ORDER_FAMILY}, read to minute {HORIZON_FAMILY}), the call the stored family probe used"), "recomputed": True, "recomputed_with_the_certified_call_and_equal_to_the_stored_record": all(equal.values()),
             **equal, **clean, "first_point_is_the_authored_arrival": (common[0]["sbp"], common[0]["dbp"], common[0]["map"], arrival["spo2"], arrival["rr"]) == (arrival["sbp"], arrival["dbp"], arrival["map"], arrival["spo2"], arrival["rr"]),
             "family": name, "case_id": case_id}
    if scenario_id in FAMILIES and case_key is None:
        item = _item(scenario_id, kind=ftm.KIND_CASE, context=f"{case['presentation']} Authored diagnosis: {case['faculty']['diagnosis']}.", facts=_facts(scenario_id, case), arrival=arrival,
                      minute=ORDER_FAMILY, horizon=HORIZON_FAMILY, common=common)
    else:
        item = None
    return {"item": item, "low": _points(runs[LOW]["rows"]), "high": _points(runs[HIGH]["rows"]), "audit": audit, "arrival": arrival, "common": common}


def _synthetic_run(name: str) -> tuple:
    from clinical_core import distributive_tone as dt
    from clinical_core import integration as ig
    anchors = dt.probe_anchors()
    declared = ta._declared(dt.reader(dt.base_profile()), name)
    burden = (dt.SyntheticVasodilation("probe-burden", dt.BURDEN_STEP, 0, 4),)
    infused = ig.run(anchors, burden + (ta._infusion(name, ORDER_SYNTH),), HORIZON_SYNTH, declared)
    plain = ig.run(anchors, burden, HORIZON_SYNTH, declared)
    return anchors, plain, infused


def synthetic(source: dict) -> dict:
    """SYNTH: the common core's synthetic distributive probe (anchors, scripted burden, infusion) with the same calls the stored probe used."""
    stored = source["probes"]["record"]["core_probes"]["distributive"]
    anchors, plain, infused = _synthetic_run(CENTER)
    derived, with_support = plain.derived(), infused.derived()
    rows = lambda run: [{"minute": minute, "sbp": reading.sbp, "dbp": reading.dbp} for minute, reading in enumerate(run)]
    common = [ta.displayed(row) for row in rows(with_support)]
    equal = {"arrival_map_equals_stored": ta._r(derived[0].map) == stored["arrival"]["map"],
             "map_before_the_order_equals_stored": ta._r(derived[ORDER_SYNTH].map) == stored["low_tone_before_the_order"]["map"],
             "map_without_support_equals_stored": ta._r(derived[HORIZON_SYNTH].map) == stored["low_tone_without_support"]["map"],
             "map_with_support_equals_stored": ta._r(with_support[HORIZON_SYNTH].map) == stored["low_tone_with_support"]["map"],
             "the_whole_stored_probe_is_reproduced": ta.core_distributive(CENTER) == stored}
    audit = {"source_record": source["probes"]["path"], "source_record_id": source["probes"]["record_id"], "source_record_digest": source["probes"]["record_digest"], "source_file_sha256": source["probes"]["file_sha256"],
             "taken_from": (f"clinical_core.distributive_tone probe anchors and scripted burden (0 to 4 min), norepinephrine {ta.PROBE_RATE:g} mcg/min from minute {ORDER_SYNTH}, witness {CENTER}, to minute {HORIZON_SYNTH}: "
                            "the construction of test_tone_pathway_analysis.core_distributive"), "recomputed": True, "recomputed_with_the_certified_call_and_equal_to_the_stored_record": all(equal.values()), **equal,
             "synthetic_only": stored["probe"]}
    base = {"sbp": int(round(anchors.sbp)), "dbp": int(round(anchors.dbp))}
    base["map"] = int(round((base["sbp"] + 2 * base["dbp"]) / 3))
    audit["first_point_is_the_synthetic_baseline"] = (common[0]["sbp"], common[0]["dbp"], common[0]["map"]) == (base["sbp"], base["dbp"], base["map"])
    context = (f"A synthetic state, not a patient: vascular tone falls over the first 4 minutes (a scripted loss of tone) while the heart and the circulating volume are unchanged. "
               f"The pressure before the fall is {base['sbp']}/{base['dbp']} mmHg (MAP {base['map']}).")
    facts = ["The heart and the circulating volume are not changed during the probe.", "There is no patient, no history and no examination: this is a physiology probe."]
    item = _item("SYNTH", kind=ftm.KIND_PROBE, context=context, facts=facts, arrival={**base, "spo2": None, "rr": None}, minute=ORDER_SYNTH, horizon=HORIZON_SYNTH, common=common)
    extremes = {}
    for witness in (LOW, HIGH):
        _, _, run = _synthetic_run(witness)
        extremes[witness] = [ta.displayed(row) for row in rows(run.derived())]
    return {"item": item, "low": extremes[LOW], "high": extremes[HIGH], "audit": audit}


# -- the set --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def exclusions(source: dict) -> list:
    out = []
    for key, (name, case_id) in OPTIONAL.items():
        made = family(key, source, case_key=(name, case_id))
        arrival = _arrival(_case(case_id))
        out.append({"scenario": key, "case_id": case_id, "status": "EXCLUDED", "reason": EXCLUSION_REASONS[key].format(**arrival),
                    "reproduced_exactly_from_the_certified_call": made["audit"]["recomputed_with_the_certified_call_and_equal_to_the_stored_record"], "arrival_pressure": f"{arrival['sbp']}/{arrival['dbp']} mmHg"})
    return out


def build(source: dict | None = None) -> dict:
    source = source or sources()
    made = {"FR-F": frf(source), "SYNTH": synthetic(source), **{key: family(key, source) for key in ("ACS", "PULM-EDEMA", "PE")}}
    items = [made[scenario_id]["item"] for scenario_id in ftm.SCENARIOS]
    problems = [problem for item in items for problem in ftm.item_problems(item)]
    if problems:
        raise ValueError(f"the assembled scenarios do not hold: {problems}")
    failed = {scenario_id: [key for key, value in dict(made[scenario_id]["audit"]).items() if value is False and key != "recomputed"] for scenario_id in made}
    if any(failed.values()):
        raise ValueError(f"a scenario is not equal to its certified source: {failed}")
    entries = []
    for scenario_id in ftm.SCENARIOS:
        low, high = made[scenario_id]["low"], made[scenario_id]["high"]
        entries.append({"scenario_id": scenario_id, "material": ftm.is_material(low, high), "points": {"LOW": low, "HIGH": high}})
    audit = {"witness": CENTER, "decision_reference": DECISIONS,
             "sources": {scenario_id: made[scenario_id]["audit"] for scenario_id in ftm.SCENARIOS},
             "selection": {"required": list(ftm.SCENARIOS), "optional_included": [], "excluded": exclusions(source)},
             "not_stored_with_the_items": list(UNREPRESENTED),
             "sensitivity_rule": {"map_span_mmhg": ftm.MATERIAL_MAP_SPAN, "sbp_span_mmhg": ftm.MATERIAL_SBP_SPAN, "declared": "before any trajectory was looked at",
                                  "meaning": "offered only where the pressure at the last minute, or the highest systolic pressure, differs by at least this much between the LOW and the HIGH setting"},
             "no_physiology_change": True, "no_parameter_selected": True, "no_witness_substituted": True}
    body = {"record_type": ftm.SET_TYPE, "version": ftm.VERSION, "set_id": ftm.SET_ID, "statement": ftm.STATEMENT,
            "what_it_is": ("Five review scenarios of ONE norepinephrine order (a start at 10 mcg/min, never changed) -- a hemorrhage, a synthetic low-tone probe, a pump-limited ACS, a congested pulmonary edema and an obstructive "
                           "pulmonary embolism -- with the trajectories of the CENTER_REFERENCE setting taken from, or proven equal to, the certified common-tone records. No comparator, no earlier trajectory and no other set are part of the items."),
            "order": list(ftm.SCENARIOS), "items": items, "sensitivity": {"scenarios": entries}, "limitations": [dict(entry) for entry in LIMITATIONS], "audit": audit}
    body["provenance"] = hr.provenance(record_id=ftm.SET_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"sources": {key: {"record_digest": value["record_digest"], "file_sha256": value["file_sha256"]} for key, value in source.items()},
                                                    "scenarios": list(ftm.SCENARIOS), "witness": CENTER, "order": {"minute": {"family": ORDER_FAMILY, "synthetic": ORDER_SYNTH, "frf": 2}, "rate": ta.PROBE_RATE}})
    return hr.seal(body)


def write_all() -> dict:
    """Write the set. ``historical_records.write`` refuses to replace an existing record with other content: a new representation is a successor record with its own name, never a regeneration in place."""
    record = build()
    return {str(SET_PATH.relative_to(ROOT)): hr.write(SET_PATH, record)}


CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_CHECKPOINT.json"
CHECKPOINT_ID = "COMMON_TONE_V1_MULTIFAMILY_REVIEW_CHECKPOINT_V1"
VERDICTS = {"A": "MULTIFAMILY_TONE_REVIEW_READY_FOR_HUMAN_USE", "B": "CORE_SCENARIOS_READY_BUT_OPTIONAL_SCENARIOS_EXCLUDED", "C": "REVIEW_UI_READY_BUT_PERSISTENCE_NOT_CERTIFIED",
            "D": "BLINDNESS_LEAK_FOUND", "E": "CANDIDATE_SOURCE_MISMATCH"}


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None) -> dict:
    """The checkpoint record of the cycle (written ONCE, after the certification, by ``write_checkpoint``). The verdict is B: all five required scenarios are ready and the optional two were EXCLUDED on purpose (the exact
    trajectory exists, a vasopressor has no indication in them), which is what B names; A would have included them."""
    record = json.loads(SET_PATH.read_text(encoding="utf-8"))
    audit = record["audit"]
    body = {"record_type": "COMMON_TONE_MULTIFAMILY_REVIEW_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-TONEREV-01 to FD-TONEREV-07", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The multifamily faculty review of the common vascular tone / norepinephrine pathway is ready for a human reviewer: five scenarios (FR-F, the synthetic low-tone probe, ACS, pulmonary edema, pulmonary embolism) "
                          "with the CENTER_REFERENCE trajectories exactly as the certified records hold them, the faculty's own questions, the lock, the overall judgment, an optional sensitivity check that exists only after the fifth "
                          "submit, and a final summary that states the limitations. The two optional scenarios (opioid, asthma) were excluded on purpose. The human review has NOT been done; nothing about physiology, parameters, "
                          "trajectories or authority changed."),
            "verdict": "B", "verdict_name": VERDICTS["B"], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "the optional scenarios are not part of the set: their exact certified trajectories exist but a vasopressor has no indication in a normotensive or hypertensive respiratory-failure patient, so judging them would not be meaningful",
                                   "C": "persistence is certified: the lock is final, a refresh restores progress, one record per scenario, a forged or altered log is unreadable and the optional answers autosave in their own log",
                                   "D": "no first-pass screen, element, chart, session key, file read or forged route carried another setting, a parameter, the configuration, an earlier trajectory or judgment, the comparator, heart rate, capillary refill or a limitation",
                                   "E": "every scenario equals its certified source: FR-F is the stored record's rows, the others are regenerated with the certified calls and equal the stored values"},
            "facts": {"set_id": record["set_id"], "set_record_digest": record["record_digest"], "order": record["order"], "witness": audit["witness"], "optional_included": audit["selection"]["optional_included"],
                      "excluded": [{"scenario": entry["scenario"], "case_id": entry["case_id"], "reason": entry["reason"]} for entry in audit["selection"]["excluded"]],
                      "sensitivity_offered": [entry["scenario_id"] for entry in record["sensitivity"]["scenarios"] if entry["material"]], "sensitivity_rule": audit["sensitivity_rule"],
                      "limitations_shown_only_in_the_final_summary": [entry["id"] for entry in record["limitations"]], **(facts or {})},
            "confirmations": {"no_physiology_change": True, "no_parameter_selected": True, "no_witness_substituted": True, "no_norepinephrine_authority_expansion": True, "no_gi_recalibration": True, "no_source_control": True,
                              "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "human_review_not_performed": True,
                              "common_core_runtime_authority": False},
            "limitations": ["the human review has not been done", "the pulmonary-edema case is hypertensive (218/116 mmHg) and the order takes it to 260/138 mmHg: kept because the assignment requires it, flagged for the reviewer",
                            "heart rate and capillary refill are not shown (not recomputed)", "the launcher offers only this review until its five scenarios are submitted and verified (MRS_FACULTY_TONE_GATE=off releases it for the operator); the re-review hold (FD-REREVIEW-21) keeps its precedence and still withholds this mode while the account's re-review is incomplete in its own store",
                            "the set record has no signature (the same limit as TD-153 item 7)"],
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": "A faculty reviewer performs the five-scenario review (about 20 minutes) and, optionally, the sensitivity check; a faculty decision then follows the interpretation guidance of FD-TONEREV-06. Nothing else is to be done until then.",
            "open_faculty_decisions": ["the result of the human review", "whether the tone mode should also be offered while the re-review is incomplete (TD-156 item 5)", "whether opioid and asthma are wanted as a variant of the set",
                                      "whether a pump-dependent afterload sensitivity is needed before any educational use of a vasopressor (COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED)"]}
    parts = {"clinical_core": generating_code()["clinical_core"], "set_record_digest": record["record_digest"], "test_tone_review_analysis.py": ta._sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"set_record_digest": record["record_digest"], "verdict": "B", "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None) -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts))}


def reproduce(source: dict | None = None) -> dict:
    """The CONTENT of the set, regenerated and returned without provenance or seal: what a test compares with the stored set whatever code generated its provenance."""
    record = build(source)
    return {key: value for key, value in record.items() if key not in ("provenance", "record_digest")}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
