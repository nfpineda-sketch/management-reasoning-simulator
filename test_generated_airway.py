"""A generated case that describes bronchospasm runs the bank's airway mechanics.

Second mechanism after the coronary one (faculty decision 2026-09-20), same shape:
the declaration is obligatory when the case describes the finding, refused when the
resident cannot discover it, and the shared modules do the work.
"""
import pytest

import asthma_complications
import asthma_ventilation
import coupled_encounter as adapter
import generated_airway as airway
from generated_airway_consistency import issues
from test_coupled_encounter import patient, run

WHEEZE = "Widespread expiratory wheeze with prolonged expiration and reduced air entry."
KETAMINE = {"type": "procedural_sedation", "agent": "ketamine", "dose_mg": 100, "route": "IV"}


def airway_case(severity=1.0, respiratory=WHEEZE, declare=True):
    state = patient()
    case = state["encounter_spec"]["clinical_case"]
    case["examination"]["Respiratory"] = respiratory
    if declare:
        case["engine"]["airway_obstruction"] = {"severity": severity}
    return state


def minutes(state, count):
    events = []
    for _ in range(count):
        adapter.tick(state)
        events += state["family_state"].pop("procedure_events", [])
    return events


def codes(case):
    return [issue["code"] for issue in issues(case)]


def test_a_case_that_describes_bronchospasm_must_declare_it():
    case = {"examination": {"Respiratory": WHEEZE}, "history": {}, "engine": {}}
    assert codes(case) == ["AIRWAY_OBSTRUCTION_UNDECLARED"]


def test_a_declaration_the_resident_cannot_find_is_refused():
    case = {"examination": {"Respiratory": "Clear breath sounds."}, "history": {},
            "engine": {"airway_obstruction": {"severity": 1.0}}}
    assert codes(case) == ["AIRWAY_OBSTRUCTION_UNDISCOVERABLE"]


def test_a_negated_finding_is_not_a_finding():
    case = {"examination": {"Respiratory": "No wheeze and no prolonged expiration."}, "history": {}, "engine": {}}
    assert codes(case) == []


def test_the_severity_must_be_inside_the_supported_range():
    case = {"examination": {"Respiratory": WHEEZE}, "history": {},
            "engine": {"airway_obstruction": {"severity": 4}}}
    assert codes(case) == ["AIRWAY_OBSTRUCTION_UNDISCOVERABLE"]


def test_the_gate_is_wired_into_the_contract_and_its_codes_are_reportable():
    import inspect
    from generated_case_schema import collect_clinical_issues
    from generated_case_validation import CLINICAL_ISSUE_CODES
    assert "generated_airway_consistency" in inspect.getsource(collect_clinical_issues)
    for code in ("AIRWAY_OBSTRUCTION_UNDECLARED", "AIRWAY_OBSTRUCTION_UNDISCOVERABLE"):
        assert code in CLINICAL_ISSUE_CODES


def test_the_obstruction_worsens_untreated_and_answers_to_a_bronchodilator():
    state = airway_case()
    minutes(state, 20)
    assert airway.airflow(state) > 1.0
    run(state, {"type": "bronchodilator", "agent": "albuterol", "dose_mg": 5, "route": "nebulized"})
    assert airway.airflow(state) < .4
    _, _, spo2, rr = airway.generated_effects(state)
    # Relief reaches the patient as oxygenation and a falling rate.
    assert spo2 > 5 and rr < -5


def test_the_moment_of_intubation_is_judged(monkeypatch=None):
    state = airway_case()
    minutes(state, 20)
    result = run(state, KETAMINE, {"type": "intubation", "ventilator_mode": "VC/AC",
                                   "fio2_percent": 100, "peep_cmh2o": 5})
    notes = [s["label"] for s in result["action_summaries"] if s.get("type") == "procedure"]
    assert notes and state["family_state"]["intubation_timing"] in {"premature", "within window", "late"}


def test_a_short_expiratory_time_traps_gas_and_tears_the_lung():
    state = airway_case()
    run(state, KETAMINE, {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100,
                          "peep_cmh2o": 5, "tidal_volume_ml": 750, "rate_per_min": 30})
    events = minutes(state, 30)
    mechanics = state["family_state"]["ventilator_mechanics"]
    assert mechanics["auto_peep_cmh2o"] > 10
    assert mechanics["plateau_cmh2o"] > asthma_ventilation.PLATEAU_LIMIT_CMH2O
    assert any("tension pneumothorax" in e["label"] for e in events)
    sbp, _, spo2, _ = airway.generated_effects(state)
    assert sbp < -20 and spo2 < -5


def test_decompression_and_slower_ventilation_undo_it():
    state = airway_case()
    run(state, KETAMINE, {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100,
                          "peep_cmh2o": 5, "tidal_volume_ml": 750, "rate_per_min": 30})
    minutes(state, 30)
    tense = airway.generated_effects(state)[0]
    run(state, {"type": "chest_decompression", "side": "right", "device": "needle"})
    minutes(state, 6)
    assert airway.generated_effects(state)[0] > tense
    run(state, {"type": "ventilator_adjustment", "ventilator_mode": "VC/AC", "fio2_percent": 60,
                "peep_cmh2o": 0, "tidal_volume_ml": 450, "rate_per_min": 10, "flow_l_per_min": 80})
    minutes(state, 10)
    mechanics = state["family_state"]["ventilator_mechanics"]
    assert mechanics["auto_peep_cmh2o"] < 2 and mechanics["plateau_cmh2o"] < 12
    assert airway.generated_effects(state)[0] > -3


def test_protective_settings_never_tear_the_lung():
    state = airway_case()
    run(state, KETAMINE, {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100,
                          "peep_cmh2o": 0, "tidal_volume_ml": 450, "rate_per_min": 10, "flow_l_per_min": 80})
    events = minutes(state, 60)
    assert state["family_state"].get("pneumothorax_at") is None
    assert not any("pneumothorax" in e["label"] for e in events)


def test_the_pressures_reach_the_update_the_resident_reads():
    from generated_engine import clinical_update
    state = airway_case()
    run(state, KETAMINE, {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100, "peep_cmh2o": 5})
    minutes(state, 3)
    text = clinical_update(state)
    assert "Airway pressures" in text and "plateau" in text


def test_the_mechanism_authorises_its_own_orders():
    state = airway_case()
    assert run(state, {"type": "magnesium", "agent": "magnesium sulfate", "dose_mg": 2000, "route": "IV"})["executed"]
    assert run(state, {"type": "continuous_bronchodilator", "agent": "albuterol", "rate_mg_h": 10,
                       "route": "nebulized", "operation": "start"})["executed"]


def test_a_case_without_the_declaration_is_untouched():
    state = airway_case(declare=False)
    minutes(state, 30)
    assert state["family_state"].get("airway_obstruction") is None
    assert airway.generated_effects(state) == (0.0, 0.0, 0.0, 0.0)
    from generated_engine import execute_generated_bundle
    refused = execute_generated_bundle(state, {"actions": [
        {"type": "chest_decompression", "side": "right", "device": "needle"}]})
    assert not refused["executed"]
