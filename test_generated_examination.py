"""Generated examinations retain focal facts without disguising old descriptions."""
from copy import deepcopy

from generated_engine import current_findings
from test_generated_engine import make_state, run, wait


def focused_state():
    state = make_state()
    state["encounter_spec"]["clinical_case"]["examination"].update({
        "General appearance": "Pale conjunctivae, an old left facial scar, and visible discomfort.",
        "Peripheral perfusion": "Left radial pulse weaker than right; left hand cooler than right. Refill approximately 4.5 seconds.",
        "Neurological": "Alert and fully conversational; chronic left foot drop.",
        "Respiratory": "Bilateral breath sounds with diminished air entry at the right base.",
        "Cardiac": "A focal systolic murmur is audible at the apex.",
        "Abdomen": "Focal tenderness in the right upper quadrant, without rigidity.",
    })
    return state


def test_initial_exam_retains_authored_general_and_asymmetric_perfusion_findings():
    state = focused_state()
    before = deepcopy(state)
    findings = current_findings(state)
    assert "Pale conjunctivae" in findings["General appearance"]
    assert "left facial scar" in findings["General appearance"]
    assert "Left radial pulse weaker than right" in findings["Peripheral perfusion"]
    assert "left hand cooler than right" in findings["Peripheral perfusion"]
    assert "Capillary refill 4.5 s" in findings["Peripheral perfusion"]
    assert "skin: pallor" in findings["General appearance"]
    assert "At arrival" not in findings["General appearance"]
    assert findings["Abdomen"] == before["encounter_spec"]["clinical_case"]["examination"]["Abdomen"]
    assert state == before


def test_evolved_physiology_labels_unupdated_arrival_facts_without_erasing_them():
    state = focused_state()
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    findings = current_findings(state)
    assert findings["Peripheral perfusion"].startswith("At arrival: Left radial pulse weaker than right")
    assert "Refill approximately 4.5 seconds" in findings["Peripheral perfusion"]
    assert "Current observations: Capillary refill 3.6 s" in findings["Peripheral perfusion"]
    assert "Pale conjunctivae" in findings["General appearance"]
    assert "systolic murmur" in findings["Cardiac"]
    assert "Current observations: Heart rate" in findings["Cardiac"]


def test_mental_status_change_keeps_unupdated_focal_neurology_as_arrival_history():
    state = focused_state()
    rule = state["encounter_spec"]["clinical_case"]["engine"]["state_rules"][0]
    rule.pop("examination")
    run(state, wait(30))
    findings = current_findings(state)
    assert findings["Neurological"].startswith("At arrival: Alert and fully conversational; chronic left foot drop.")
    assert "Current observations: Mental status: Drowsy." in findings["Neurological"]
    assert findings["General appearance"].startswith("At arrival: Pale conjunctivae")
    assert "Current observations: Drowsy" in findings["General appearance"]
    assert "mottling present" in findings["General appearance"]


def test_explicit_state_specific_exam_is_current_and_replaces_arrival_description():
    state = focused_state()
    rule = state["encounter_spec"]["clinical_case"]["engine"]["state_rules"][0]
    rule["examination"].update({
        "General appearance": "Eyes open to voice; pronounced pallor, with the old facial scar still visible.",
        "Peripheral perfusion": "Both hands now cold; left radial pulse remains weaker than right.",
    })
    run(state, wait(30))
    findings = current_findings(state)
    assert findings["General appearance"].startswith("Examination: Eyes open to voice")
    assert findings["Peripheral perfusion"].startswith("Examination: Both hands now cold")
    assert findings["Neurological"].startswith("Examination: Opens eyes to voice")
    assert "At arrival" not in findings["Neurological"]
    assert "Current observations: Mental status: Drowsy" in findings["Neurological"]


def test_followup_exam_does_not_lose_focal_respiratory_or_abdominal_information():
    state = focused_state()
    state["encounter_spec"]["clinical_case"]["engine"]["untreated_drift_per_min"]["respiratory_rate"] = .1
    run(state, wait(10))
    findings = current_findings(state)
    assert findings["Respiratory"].startswith("At arrival: Bilateral breath sounds with diminished air entry at the right base.")
    assert "Current observations: Respiratory rate 25/min" in findings["Respiratory"]
    assert "right upper quadrant" in findings["Abdomen"]
    assert "left foot drop" in findings["Neurological"]
