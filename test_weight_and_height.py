"""Weight and height in the chart, and the weight each calculation uses (faculty, 2026-09-27).

The faculty approved weight and height in every bank case, shown in the chart and
used by new encounters only; a tidal volume per kilogram on the predicted body
weight; and consistent weight rules from the order to its effect. The weight
bases of the other physiology parameters and of each medicine are pending
decisions: until then nothing changes for them silently.
"""
from copy import deepcopy

import pytest

import asthma_ventilation
import catalog_trajectories
import family_engine
import patient_body
import tools_case_bodies
import urine_output
import weight_based_doses
from clinical_cases import FAMILIES, review_candidates, variant_by_id
from family_parser import parse_family_actions


def launch(case_id):
    family = next(name for name, spec in FAMILIES.items() if any(v["id"] == case_id for v in spec["variants"]))
    return catalog_trajectories.launch(case_id, family)


def before_the_weight_rules(state):
    """An encounter launched before 2026-09-27: no weight in its case, no weight rules in its spec."""
    state = deepcopy(state)
    state["encounter_spec"].pop("weight_rules", None)
    state["encounter_spec"]["clinical_case"]["patient"].pop("body", None)
    return state


def run(state, text):
    parsed = parse_family_actions(text)
    assert weight_based_doses.resolve(parsed, state) == [], text
    result = family_engine.execute_family_bundle(state, parsed)
    assert result["executed"], result
    return result


# --------------------------------------------------------------------------- the table

def test_every_bank_case_records_its_weight_and_height_and_how_each_was_obtained():
    cases = [variant for spec in FAMILIES.values() for variant in spec["variants"]]
    assert len(cases) == len(patient_body.BODIES) == 31
    for variant in cases:
        body = variant["patient"]["body"]
        assert 40 <= body["weight_kg"] <= 160 and 1.40 <= body["height_m"] <= 1.95, variant["id"]
        assert body["weight_how"] in ("measured", "reported", "estimated"), variant["id"]
        assert body["height_how"] in ("measured", "reported", "estimated"), variant["id"]
    # A composition of the catalogue is the patient of the bank case it derives from.
    for candidate in review_candidates():
        assert candidate["patient"]["body"] in [v["patient"]["body"] for v in cases]


def test_the_table_is_the_seeded_draw_and_meets_the_faculty_s_conditions():
    rows, _ = tools_case_bodies.draw()
    assert {row["case"]: (row["weight_kg"], row["height_m"]) for row in rows} == {
        case: (body["weight_kg"], body["height_m"]) for case, body in patient_body.BODIES.items()}
    assert all(tools_case_bodies.conditions(rows).values()), tools_case_bodies.conditions(rows)
    # Nobody is given a normal weight because of chemotherapy, alcohol or poor intake,
    # and heights vary as adults' do.
    habitus = {row["case"]: row["habitus"] for row in rows}
    assert habitus["pulmonary_embolism_61m"] != "normal"
    heights = [body["height_m"] for body in patient_body.BODIES.values()]
    assert max(heights) - min(heights) >= 0.35


def test_the_dry_weight_is_not_recorded_until_the_faculty_defines_it():
    # The 117 kg once shown was an inference (122 minus 5 for two missed
    # sessions), not a documented value; the faculty withdrew it (instruction
    # of 2026-09-26, point 7). No case records a dry weight, the chart shows
    # none, and a dose "de peso seco" asks for the missing datum, keeping the
    # whole order.
    patient = variant_by_id("bradycardia_hyperk_63m")["patient"]
    assert "dry_weight_kg" not in patient["body"]
    assert not any("dry weight" in line.lower() for line in patient_body.chart_lines(patient))
    assert patient_body.weights(patient)["actual"] == 122
    assert patient_body.dosing_weight(patient, "dry") == (None, "no dry weight is recorded")
    assert [body.get("dry_weight_kg") for body in patient_body.BODIES.values()] == [None] * 31
    heavy = launch("bradycardia_hyperk_63m")
    parsed = parse_family_actions("enoxaparina 1 mg/kg de peso seco sc")
    assert weight_based_doses.resolve(parsed, heavy) == [0]
    question = weight_based_doses.question_for(parsed, [0], heavy)
    assert "no dry weight is recorded" in question and "The whole order is kept" in question


def test_the_chart_says_when_a_weight_is_an_estimate():
    lines = patient_body.chart_lines(variant_by_id("hypoglycemia_28m")["patient"])
    assert lines[0] == "Weight 102 kg (estimated by the team; the patient could not be weighed)"
    assert lines[1] == "Height 1.73 m (estimated by the team)"
    assert patient_body.chart_lines(variant_by_id("acs_66f_nonst")["patient"])[0] == "Weight 50 kg (measured at triage)"
    assert patient_body.chart_lines({"age_years": 50, "sex": "male"}) == ["Weight not recorded"]


def test_predicted_body_weight_is_the_devine_ardsnet_formula():
    assert patient_body.predicted_weight("male", 1.75) == 70.6
    assert patient_body.predicted_weight("female", 1.60) == 52.4
    assert patient_body.predicted_formula("female", 1.70) == "45.5 + 0.91 × (170 − 152.4) = 61.5 kg"
    assert patient_body.predicted_weight("male", None) is None


def test_new_encounters_carry_the_rules_and_old_ones_keep_theirs():
    state = launch("asthma_24f")
    assert state["encounter_spec"]["weight_rules"] == patient_body.RULES
    assert patient_body.rules_apply(state)
    assert not patient_body.rules_apply(before_the_weight_rules(state))


# --------------------------------------------------------------------------- tidal volume (decision B)

def test_a_tidal_volume_per_kilogram_is_on_the_predicted_body_weight_with_its_formula():
    state = launch("asthma_24f")                     # 83 kg, 1.70 m: predicted 61.5 kg
    result = run(state, "Give ketamine 100 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 "
                        "Vt 8 mL/kg rate 12 flow 80 L/min.")
    settings = asthma_ventilation.settings(state)
    assert settings["tidal_volume_ml"] == 492
    label = next(s["label"] for s in result["action_summaries"] if s["label"].startswith("Intubation"))
    assert "8 mL/kg × 61.5 kg = 492 mL, on the predicted body weight: 45.5 + 0.91 × (170 − 152.4)" in label


def test_an_absolute_tidal_volume_is_kept_as_written_even_after_one_per_kilogram():
    state = launch("asthma_24f")
    run(state, "Give ketamine 100 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 "
               "Vt 8 mL/kg rate 12 flow 80 L/min.")
    run(state, "Ajusta el ventilador a VC/AC, FiO2 60%, PEEP 0, volumen corriente 400 ml y frecuencia 12.")
    assert asthma_ventilation.settings(state)["tidal_volume_ml"] == 400
    assert state["treatments"].get("ventilator_tidal_ml_per_kg") is None


def test_a_weight_type_the_resident_names_for_the_tidal_volume_is_kept():
    state = launch("asthma_24f")
    run(state, "Give ketamine 100 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 "
               "Vt 8 mL/kg rate 12 flow 80 L/min.")
    run(state, "Ajusta el ventilador a VC/AC, FiO2 60%, PEEP 0, volumen corriente 6 ml/kg de peso real y frecuencia 12.")
    assert asthma_ventilation.settings(state)["tidal_volume_ml"] == 6 * 83


def test_before_the_weight_rules_a_tidal_volume_per_kilogram_stays_on_70_kg():
    state = before_the_weight_rules(launch("asthma_24f"))
    run(state, "Give ketamine 100 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 "
               "Vt 8 mL/kg rate 12 flow 80 L/min.")
    assert asthma_ventilation.settings(state)["tidal_volume_ml"] == 560


# --------------------------------------------------------------------------- pending: nothing changes silently

@pytest.mark.parametrize("case_id", ["asthma_24f", "asthma_49m", "bradycardia_hyperk_63m", "pulmonary_embolism_33f"])
def test_the_undecided_physiology_keeps_the_weight_it_was_calibrated_on(case_id):
    # Required minute ventilation, the default tidal volume and baseline urine output
    # wait for the faculty's decision: a weight in the chart does not move them.
    new = launch(case_id)
    old = before_the_weight_rules(new)
    assert asthma_ventilation.settings(new)["weight_kg"] == asthma_ventilation.settings(old)["weight_kg"] == 70.0
    assert asthma_ventilation.settings(new)["tidal_volume_ml"] == 560.0
    assert urine_output.rate_ml_per_min(new) == urine_output.rate_ml_per_min(old)


# --------------------------------------------------------------------------- declared residual renal function (2026-09-26)

def test_the_dialysis_case_no_longer_makes_the_urine_of_a_working_kidney():
    # "I pass almost no urine; that has been true for years": the case declares
    # minimal residual function. Oliguric, never absolute anuria -- the history
    # says "almost" -- and the exact residual baseline is a pending clinical
    # decision, run meanwhile on a stated simulator convention.
    state = launch("bradycardia_hyperk_63m")
    state["family_state"].setdefault("circulation", 1.0)
    state["family_state"].setdefault("elapsed", 0)
    rate = urine_output.rate_ml_per_min(state) * 60
    assert 0 < rate < 10 and rate == pytest.approx(7.0)
    # The declaration also bounds what furosemide can do on that kidney.
    urine_output.record_dose(state, 80, "IV")
    assert state["family_state"]["furosemide_doses"][0]["responsiveness"] < 0.05


def test_an_encounter_saved_before_the_declaration_keeps_its_own_case_copy():
    state = launch("bradycardia_hyperk_63m")
    state["family_state"].setdefault("circulation", 1.0)
    state["family_state"].setdefault("elapsed", 0)
    del state["encounter_spec"]["clinical_case"]["engine"]["renal"]
    assert urine_output.rate_ml_per_min(state) * 60 == pytest.approx(70.0)


def test_no_other_case_changed_its_urine_and_a_declared_absolute_baseline_is_possible():
    other = launch("gi_bleed_57m")
    other["family_state"].setdefault("circulation", 1.0)
    other["family_state"].setdefault("elapsed", 0)
    assert urine_output.rate_ml_per_min(other) * 60 == pytest.approx(70.0)
    other["encounter_spec"]["clinical_case"]["engine"]["renal"] = {"baseline_urine_ml_h": 55}
    assert urine_output.rate_ml_per_min(other) * 60 == pytest.approx(55.0)


# --------------------------------------------------------------------------- one effect for one amount

def test_the_same_amount_of_blocker_has_the_same_effect_however_it_was_written():
    by_kilogram, in_milligrams = launch("pulmonary_embolism_33f"), launch("pulmonary_embolism_33f")   # 47 kg
    run(by_kilogram, "rocuronio 1.2 mg/kg iv")
    run(in_milligrams, "rocuronio 56.4 mg iv")
    assert by_kilogram["family_state"]["paralysis_until"] == in_milligrams["family_state"]["paralysis_until"]


def test_a_rate_per_kilogram_is_converted_on_the_chart_weight_and_recorded():
    state = launch("pulmonary_embolism_61m")                        # 83 kg; not a relevant ambiguity
    result = run(state, "inicio noradrenalina a 0.1 mcg/kg/min ev")
    assert state["family_state"]["norepinephrine"] == pytest.approx(8.3)
    summary = next(s for s in result["action_summaries"] if s["type"] == "norepinephrine")
    assert summary["weight_kg"] == 83 and "0.1 mcg/kg/min × 83 kg = 8.3 mcg/min" in summary["label"]


def test_dobutamine_per_kilogram_has_the_effect_it_names():
    import inotrope_support
    state = launch("pulmonary_embolism_61m")
    run(state, "inicio dobutamina a 5 mcg/kg/min ev")
    assert inotrope_support.rate_per_kg(state) == pytest.approx(5.0)


def test_a_fluid_per_kilogram_is_a_volume_on_the_weight_not_that_many_millilitres():
    state = launch("pneumonia_46f")                                  # 58 kg
    parsed = parse_family_actions("SF 30 ml/kg ev en bolo")
    assert weight_based_doses.resolve(parsed, state) == []
    assert parsed["actions"][0]["volume_ml"] == 1740


def test_a_sedation_rate_per_kilogram_per_minute_is_read_as_such():
    import airway_pharmacology
    infusion = {"sedation_infusion": {"agent": "propofol", "rate": 0.05, "units": "mg/kg/min"}}
    # 0.05 mg/kg/min is 3 mg/kg/h, propofol's reference rate: 12 mmHg.
    assert airway_pharmacology.infusion_pressure_cost(infusion, 70, weight_rules=True) == pytest.approx(12.0)
    # An encounter launched before keeps the old reading.
    assert airway_pharmacology.infusion_pressure_cost(infusion, 70) < 1


# --------------------------------------------------------------------------- orders that were misread or refused (2026-09-26)

def test_fentanyl_doses_are_read_written_and_bounded_in_micrograms():
    state = launch("opioid_35m")                                      # 81 kg estimated
    result = run(state, "Give fentanyl 100 mcg IV")
    assert any("fentanyl 100 mcg IV administered" in (s.get("label") or "")
               for s in result["action_summaries"])
    per_kg = run(launch("opioid_35m"), "Give fentanyl 1 mcg/kg IV")
    label = next(s["label"] for s in per_kg["action_summaries"] if "fentanyl" in s["label"])
    assert "fentanyl 81 mcg IV administered" in label and "1 mcg/kg × 81 kg" in label
    parsed = parse_family_actions("Give fentanyl 40 mg IV")
    assert weight_based_doses.resolve(parsed, launch("opioid_35m")) == []
    refused = family_engine.execute_family_bundle(launch("opioid_35m"), parsed)
    assert not refused["executed"]
    assert refused["clarification"] == "Please specify or confirm the fentanyl dose in micrograms."


def test_a_fentanyl_dose_becomes_its_stated_morphine_equivalence():
    # 100 mcg is about 10 mg of morphine -- the factor the code always claimed.
    state = launch("opioid_35m")
    run(state, "Give fentanyl 100 mcg IV")
    # 10 mg-equivalent landed, minus the clearance of the administration minutes.
    assert 9.5 < state["family_state"]["morphine_mg"] <= 10.0


def test_tranexamic_acid_per_kilogram_converts_and_a_missing_dose_is_stated():
    state = launch("trauma_limb_hemorrhage_27m")                      # 74 kg
    result = run(state, "Give tranexamic acid 15 mg/kg IV")
    label = next(s["label"] for s in result["action_summaries"] if "Tranexamic" in s["label"])
    assert "1.11 g IV administered" in label and "15 mg/kg × 74 kg" in label
    fixed = run(launch("trauma_limb_hemorrhage_27m"), "Give TXA IV")
    label = next(s["label"] for s in fixed["action_summaries"] if "Tranexamic" in s["label"])
    assert "no dose written; 1 g is the standard fixed loading dose" in label


def test_intramuscular_epinephrine_per_kilogram_converts_and_is_judged_openly():
    # The dose is understood, converted on the chart's weight, shown, and then
    # judged by the validation range -- comprehension, validation and execution
    # kept apart; nothing is changed silently.
    state = launch("anaphylaxis_63m_betablocked")                     # 115 kg
    result = run(state, "Give epinephrine 0.01 mg/kg IM")
    label = next(s["label"] for s in result["action_summaries"] if "Epinephrine" in s["label"])
    assert "1.15 mg IM administered" in label and "0.01 mg/kg × 115 kg" in label
    parsed = parse_family_actions("adrenalina 0.05 mg/kg im")
    assert weight_based_doses.resolve(parsed, launch("anaphylaxis_63m_betablocked")) == []
    refused = family_engine.execute_family_bundle(launch("anaphylaxis_63m_betablocked"), parsed)
    assert not refused["executed"] and "0.05 to 2 mg" in refused["clarification"]


# --------------------------------------------------------------------------- the reader

def test_the_weight_gap_alone_is_not_a_question_and_the_convention_is_recorded():
    # Faculty instruction of 2026-09-26 (point 1): the actual/ideal gap is not,
    # by itself, a barrier. The dose runs on the chart's actual weight and the
    # record says that the weight type for the drug is a pending decision.
    heavy = launch("bradycardia_hyperk_63m")       # 122 kg, ideal 60.6 kg
    parsed = parse_family_actions("rocuronio 1.2 mg/kg iv")
    assert weight_based_doses.resolve(parsed, heavy) == []
    action = parsed["actions"][0]
    assert action["dose_mg"] == pytest.approx(146.4)
    assert action["weight_basis"] == "actual" and action["weight_source"] == "chart"
    assert action["weight_convention_pending"] is True
    assert "engine convention while the weight type for this drug is undecided" in action["dose_basis"]
    # A weight type written with the order is respected, with no note.
    named = parse_family_actions("enoxaparina 1 mg/kg de peso real sc")
    assert weight_based_doses.resolve(named, heavy) == []
    assert named["actions"][0]["dose"] == 122
    assert "weight_convention_pending" not in named["actions"][0]
    # A named choice is reused for the same drug and kind of order only.
    ideal = parse_family_actions("rocuronio 1.2 mg/kg de peso ideal iv")
    assert weight_based_doses.resolve(ideal, heavy) == []
    weight_based_doses.remember(heavy, ideal)
    again = parse_family_actions("rocuronio 0.6 mg/kg iv")
    assert weight_based_doses.resolve(again, heavy) == []
    assert again["actions"][0]["weight_basis"] == "ideal"
    assert "chosen earlier for this drug" in again["actions"][0]["dose_basis"]
    # Where actual and ideal weight are close, the plain chart weight, no note.
    close = launch("pulmonary_embolism_33f")
    plain = parse_family_actions("rocuronio 1.2 mg/kg iv")
    assert weight_based_doses.resolve(plain, close) == []
    assert "engine convention" not in plain["actions"][0]["dose_basis"]


def test_an_encounter_of_the_first_revision_still_asks_as_it_did():
    # Launched under the first stamp, the reader asked once per drug on a 30%
    # gap; a saved encounter must replay exactly as it was played.
    heavy = launch("bradycardia_hyperk_63m")
    heavy["encounter_spec"]["weight_rules"] = patient_body.RULES_FIRST_REVISION
    parsed = parse_family_actions("rocuronio 1.2 mg/kg iv")
    assert weight_based_doses.resolve(parsed, heavy) == [0]
    question = weight_based_doses.question_for(parsed, [0], heavy)
    assert "actual 122 kg" in question and "ideal 60.6 kg" in question and "adjusted 85.2 kg" in question
    assert weight_based_doses.answer(parsed["actions"][0], "el ideal", heavy) is None
    assert parsed["actions"][0]["dose_mg"] == pytest.approx(72.72)
    weight_based_doses.remember(heavy, parsed)
    again = parse_family_actions("rocuronio 0.6 mg/kg iv")
    assert weight_based_doses.resolve(again, heavy) == []
    assert "chosen earlier for this drug" in again["actions"][0]["dose_basis"]


def test_a_generated_case_records_the_same_body_data_a_bank_case_does():
    # Schema v4 (faculty instruction of 2026-09-26, point 2): weight AND height,
    # each with its origin, flat on the patient; one order, one interpretation.
    patient = {"age_years": 42, "sex": "female", "weight_kg": 72, "weight_how": "measured",
               "weight_by": "at triage", "height_m": 1.68, "height_how": "measured",
               "height_by": "at triage"}
    recorded = patient_body.body(patient)
    assert recorded["height_m"] == 1.68 and recorded["weight_how"] == "measured"
    assert patient_body.weights(patient)["ideal"] == 59.7
    assert patient_body.chart_lines(patient) == ["Weight 72 kg (measured at triage)",
                                                 "Height 1.68 m (measured at triage)"]
    kg, description = patient_body.dosing_weight(patient, "ideal")
    assert kg == 59.7 and "45.5 + 0.91" in description


def test_a_case_generated_before_v4_keeps_its_historical_reading():
    # Only a weight, recorded in the case; the chart says the height is not
    # recorded, and a named ideal weight still asks for the missing datum.
    patient = {"age_years": 42, "sex": "female", "weight_kg": 72}
    recorded = patient_body.body(patient)
    assert recorded["weight_how"] == "recorded" and recorded["height_m"] is None
    assert patient_body.chart_lines(patient) == ["Weight 72 kg (recorded in the case)",
                                                 "Height not recorded"]
    assert patient_body.dosing_weight(patient, "ideal") == (None, "the height is not recorded")


def test_a_weight_type_that_cannot_be_calculated_asks_for_the_weight_instead():
    state = launch("pulmonary_embolism_33f")
    state["encounter_spec"]["clinical_case"]["patient"]["body"].pop("height_m")
    parsed = parse_family_actions("enoxaparina 1 mg/kg de peso ideal sc")
    assert weight_based_doses.resolve(parsed, state) == [0]
    assert "the height is not recorded" in weight_based_doses.question_for(parsed, [0], state)
    assert weight_based_doses.answer(parsed["actions"][0], "55 kg", state) is None
    assert parsed["actions"][0]["dose"] == 55
