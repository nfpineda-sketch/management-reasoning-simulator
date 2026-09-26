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


def test_a_previous_dry_weight_is_never_today_s_weight():
    patient = variant_by_id("bradycardia_hyperk_63m")["patient"]
    body = patient["body"]
    assert body["dry_weight_kg"] < body["weight_kg"]
    lines = patient_body.chart_lines(patient)
    assert any("Previous dry weight" in line and "not today's weight" in line for line in lines)
    # Doses are on today's weight unless the resident names the dry weight.
    assert patient_body.weights(patient)["actual"] == body["weight_kg"]
    assert patient_body.dosing_weight(patient, "dry")[0] == body["dry_weight_kg"]
    assert [body.get("dry_weight_kg") for case, body in patient_body.BODIES.items()
            if case != "bradycardia_hyperk_63m"] == [None] * 30


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


# --------------------------------------------------------------------------- the reader

def test_the_weight_type_is_asked_only_when_it_changes_the_dose_and_only_once_per_drug():
    heavy = launch("bradycardia_hyperk_63m")       # 122 kg, ideal 60.6 kg
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
    # A weight type written with the order is never asked.
    named = parse_family_actions("enoxaparina 1 mg/kg de peso real sc")
    assert weight_based_doses.resolve(named, heavy) == []
    assert named["actions"][0]["dose"] == 122
    # Where actual and ideal weight are close, nothing is asked.
    close = launch("pulmonary_embolism_33f")
    assert weight_based_doses.resolve(parse_family_actions("rocuronio 1.2 mg/kg iv"), close) == []


def test_a_weight_type_that_cannot_be_calculated_asks_for_the_weight_instead():
    state = launch("pulmonary_embolism_33f")
    state["encounter_spec"]["clinical_case"]["patient"]["body"].pop("height_m")
    parsed = parse_family_actions("enoxaparina 1 mg/kg de peso ideal sc")
    assert weight_based_doses.resolve(parsed, state) == [0]
    assert "the height is not recorded" in weight_based_doses.question_for(parsed, [0], state)
    assert weight_based_doses.answer(parsed["actions"][0], "55 kg", state) is None
    assert parsed["actions"][0]["dose"] == 55
