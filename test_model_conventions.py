"""The evaluation's scope notes: which outputs stand on undecided engine conventions.

Faculty instruction of 2026-09-26, point 5. A convention of the engine can
change gases, pressure, a blocker's duration or the urine, and through them
the decisions that followed; the faculty brief and the rubric panel therefore
name the specific convention-dependent observations of each encounter, and
only those. An encounter that touched none of them carries no note.
"""
import catalog_trajectories
import family_engine
import model_conventions
import weight_based_doses
from clinical_cases import FAMILIES
from family_parser import parse_family_actions


def launch(case_id):
    family = next(name for name, spec in FAMILIES.items() if any(v["id"] == case_id for v in spec["variants"]))
    return catalog_trajectories.launch(case_id, family)


def trace_of(state, *orders):
    trace = []
    for text in orders:
        parsed = parse_family_actions(text)
        assert weight_based_doses.resolve(parsed, state) == [], text
        result = family_engine.execute_family_bundle(state, parsed)
        assert result["executed"], (text, result)
        trace.append({"execution_status": "executed",
                      "decision_time_min": state.get("sim_time", 0),
                      "interpreted_action": parsed["actions"]})
    return trace


def test_a_per_kilogram_dose_on_the_convention_is_named_with_its_decision():
    state = launch("bradycardia_hyperk_63m")            # 122 kg, ideal 60.6
    trace = trace_of(state, "rocuronio 1.2 mg/kg iv")
    rows = model_conventions.notes(trace, state)
    identifiers = [row["id"] for row in rows]
    assert "weight_basis" in identifiers and "blocker_duration" in identifiers
    weight = next(row for row in rows if row["id"] == "weight_basis")
    assert "rocuronium 1.2 mg/kg" in weight["observation"]
    assert "decisions C and E" in weight["decision"]


def test_an_explicitly_named_weight_type_is_not_a_convention_note():
    state = launch("bradycardia_hyperk_63m")
    trace = trace_of(state, "enoxaparina 1 mg/kg de peso real sc")
    assert [row["id"] for row in model_conventions.notes(trace, state)] == []


def test_a_patient_without_the_relevant_gap_carries_no_weight_note():
    state = launch("pulmonary_embolism_61m")            # 83 kg; ratio below 1.30
    trace = trace_of(state, "rocuronio 1.2 mg/kg iv")
    assert [row["id"] for row in model_conventions.notes(trace, state)] == []


def test_the_dialysis_case_notes_its_residual_diuresis_only_when_urine_was_touched():
    untouched = launch("bradycardia_hyperk_63m")
    trace = trace_of(untouched, "Give calcium gluconate 2 g IV")
    assert all(row["id"] != "residual_diuresis"
               for row in model_conventions.notes(trace, untouched))
    touched = launch("bradycardia_hyperk_63m")
    trace = trace_of(touched, "Place a urinary catheter", "Give furosemide 80 mg IV")
    rows = model_conventions.notes(trace, touched)
    diuresis = next(row for row in rows if row["id"] == "residual_diuresis")
    assert "minimal residual renal function" in diuresis["observation"]
    assert "decision D" in diuresis["decision"]


def test_the_rule_bounds_the_observation_and_not_the_domain():
    assert "do not ground a deficiency on one of them alone" in model_conventions.RULE
    assert "Everything else in the encounter is evaluated as usual" in model_conventions.RULE
