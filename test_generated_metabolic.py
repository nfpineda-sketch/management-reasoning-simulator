"""Glucose and opioid mechanisms inside generated cases (faculty, 2026-09-20).

The last two of the first pass, same shape as the coronary, airway and pulmonary
ones: an obligatory declaration, a gate that refuses what the resident cannot
discover, and the shared modules doing the work.
"""
import pytest

import coupled_encounter as adapter
import generated_glucose as ggluc
import generated_opioid as gopi
import glucose_rescue
import opioid_reversal
from clinical_core_defaults import CORE_VERSION, INITIAL_HIDDEN, PHENOTYPE_FIELDS
from generated_engine import execute_generated_bundle
from generated_metabolic_consistency import glucose_issues, opioid_issues
from test_generated_engine import make_state


def build(**engine_fields):
    state = make_state()
    state["seed"] = 13
    case = state["encounter_spec"]["clinical_case"]
    engine = case["engine"]
    engine["model"] = CORE_VERSION
    engine["core_profile"] = {"version": CORE_VERSION, "infection_active": False,
                              "initial_hidden": {k: INITIAL_HIDDEN[k] for k in PHENOTYPE_FIELDS}}
    engine["untreated_drift_per_min"] = {}
    engine.update(engine_fields)
    return state, case


def hypoglycaemic(glucose=38, **declaration):
    state, case = build(glucose_failure={"sulfonylurea": True, "thiamine_deficient": False, **declaration})
    for target in (case["observable"], state["observable"]):
        target["glucose_mg_dl"] = glucose
    case["investigations"]["poc_glucose"]["result"].update(glucose_mg_dl=glucose, report=f"Glucose {glucose} mg/dL")
    case["investigations"]["basic_labs"]["result"]["glucose_mg_dl"] = glucose
    case["history"] = {"medications": ["She takes glibenclamide for diabetes."]}
    adapter.initialize(state)
    return state


def poisoned(long_acting=False):
    state, case = build(opioid_toxidrome={"long_acting": long_acting})
    for target in (case["observable"], state["observable"]):
        target.update(respiratory_rate=6, spo2=80, mental_status="Obtunded", work_of_breathing="Reduced")
    case["history"] = {"exposure": ["He was found with an opioid tablet."]}
    adapter.initialize(state)
    return state


def minutes(state, count):
    events = []
    for _ in range(count):
        adapter.tick(state)
        events += state["family_state"].pop("procedure_events", [])
    return events


def order(state, *actions):
    result = execute_generated_bundle(state, {"actions": list(actions)})
    assert result["executed"], result
    return result


def test_a_low_arrival_glucose_obliges_the_declaration():
    case = {"observable": {"glucose_mg_dl": 38}, "history": {}, "examination": {}, "engine": {}}
    assert [i["code"] for i in glucose_issues(case)] == ["GLUCOSE_FAILURE_UNDECLARED"]


def test_a_declared_sulfonylurea_must_be_in_the_medicines():
    case = {"observable": {"glucose_mg_dl": 38}, "history": {"medications": ["She takes metformin."]},
            "examination": {}, "engine": {"glucose_failure": {"sulfonylurea": True, "thiamine_deficient": False}}}
    assert [i["path"] for i in glucose_issues(case)] == ["case.engine.glucose_failure.sulfonylurea"]
    case["history"]["medications"].append("She also takes glimepiride.")
    assert glucose_issues(case) == []


def test_a_declared_thiamine_deficiency_must_be_discoverable():
    case = {"observable": {"glucose_mg_dl": 38}, "history": {"medications": ["No regular medicines."]},
            "examination": {}, "engine": {"glucose_failure": {"sulfonylurea": False, "thiamine_deficient": True}}}
    assert [i["path"] for i in glucose_issues(case)] == ["case.engine.glucose_failure.thiamine_deficient"]
    case["history"]["risk_factors"] = ["He drinks heavily and has eaten almost nothing for a week."]
    assert glucose_issues(case) == []


def test_a_normal_glucose_cannot_declare_the_mechanism():
    case = {"observable": {"glucose_mg_dl": 104}, "history": {}, "examination": {},
            "engine": {"glucose_failure": {"sulfonylurea": False, "thiamine_deficient": False}}}
    assert [i["path"] for i in glucose_issues(case)] == ["case.observable.glucose_mg_dl"]


def test_an_opioid_with_slow_breathing_obliges_its_declaration():
    case = {"observable": {"respiratory_rate": 6}, "history": {"exposure": ["He took an opioid tablet."]},
            "examination": {}, "engine": {}}
    assert [i["code"] for i in opioid_issues(case)] == ["OPIOID_TOXIDROME_UNDECLARED"]


def test_an_opioid_declaration_needs_the_exposure_and_the_breathing():
    case = {"observable": {"respiratory_rate": 18}, "history": {}, "examination": {},
            "engine": {"opioid_toxidrome": {"long_acting": False}}}
    assert [i["path"] for i in opioid_issues(case)] == ["case.engine.opioid_toxidrome",
                                                        "case.observable.respiratory_rate"]


def test_the_gates_are_wired_and_their_codes_are_reportable():
    import inspect
    from generated_case_schema import collect_clinical_issues
    from generated_case_validation import CLINICAL_ISSUE_CODES
    assert "generated_metabolic_consistency" in inspect.getsource(collect_clinical_issues)
    for code in ("GLUCOSE_FAILURE_UNDECLARED", "GLUCOSE_FAILURE_UNDISCOVERABLE",
                 "OPIOID_TOXIDROME_UNDECLARED", "OPIOID_TOXIDROME_UNDISCOVERABLE"):
        assert code in CLINICAL_ISSUE_CODES


def test_the_glucose_falls_and_the_monitor_shows_it():
    state = hypoglycaemic()
    minutes(state, 10)
    assert state["observable"]["glucose_mg_dl"] < 38
    assert state["observable"]["mental_status"] in {"Drowsy", "Obtunded", "Unresponsive"}


def test_the_ampoule_wakes_the_patient_and_the_sulfonylurea_takes_it_back():
    state = hypoglycaemic()
    minutes(state, 10)
    order(state, {"type": "dextrose", "dose_g": 25, "route": "IV"})
    minutes(state, 4)
    corrected = state["observable"]["glucose_mg_dl"]
    assert corrected > 110 and state["observable"]["mental_status"] == "Alert"
    minutes(state, 30)
    assert state["observable"]["glucose_mg_dl"] < corrected - 15


def test_octreotide_stops_the_recurrence():
    """Its onset is fifteen minutes, so the comparison is against the same case untreated."""
    def course(with_octreotide):
        state = hypoglycaemic()
        orders = [{"type": "dextrose", "dose_g": 25, "route": "IV"}]
        if with_octreotide:
            orders.append({"type": "octreotide", "agent": "octreotide", "dose_mg": .1, "route": "SC"})
        order(state, *orders)
        minutes(state, 5)
        corrected = state["observable"]["glucose_mg_dl"]
        minutes(state, 40)
        return corrected - state["observable"]["glucose_mg_dl"]
    assert course(True) < course(False) / 2


def test_neuroglycopenia_left_alone_seizes_in_a_generated_case():
    state = hypoglycaemic()
    events = minutes(state, glucose_rescue.SEIZURE_AFTER_MIN + 2)
    assert any("tonic-clonic seizure" in e["label"] for e in events)
    assert state["observable"]["mental_status"] == "Unresponsive"


def test_a_titrated_dose_reverses_the_opioid():
    state = poisoned()
    order(state, {"type": "bag_mask"}, {"type": "naloxone", "agent": "naloxone", "dose_mg": .4, "route": "IV"})
    minutes(state, 3)
    assert state["observable"]["respiratory_rate"] >= 12
    assert state["observable"]["mental_status"] == "Alert"


def test_the_antidote_wears_off_before_the_drug():
    state = poisoned()
    order(state, {"type": "bag_mask"}, {"type": "naloxone", "agent": "naloxone", "dose_mg": .4, "route": "IV"})
    minutes(state, 45)
    assert state["observable"]["mental_status"] in {"Drowsy", "Obtunded"}
    assert state["family_state"]["naloxone"] < .5


def test_an_infusion_holds_a_long_acting_opioid():
    state = poisoned(long_acting=True)
    order(state, {"type": "naloxone", "agent": "naloxone", "dose_mg": .4, "route": "IV"},
          {"type": "naloxone_infusion", "rate_mg_h": .4, "operation": "start"})
    minutes(state, 45)
    assert state["observable"]["respiratory_rate"] >= 12 and state["observable"]["spo2"] >= 94
    assert state["observable"]["mental_status"] == "Alert"


def test_too_much_antidote_precipitates_withdrawal():
    state = poisoned()
    order(state, {"type": "naloxone", "agent": "naloxone", "dose_mg": 2, "route": "IV"})
    events = minutes(state, 3)
    assert any("Acute withdrawal" in e["label"] for e in events)
    assert state["observable"]["mental_status"] == "Agitated"
    assert state["observable"]["hr"] > 100


def test_unsupported_apnoea_arrests_in_a_generated_case():
    state = poisoned()
    events = minutes(state, opioid_reversal.ARREST_AFTER_MIN + 2)
    assert any("Respiratory arrest" in e["label"] for e in events)
    assert state["observable"]["pulse_present"] is False
    assert state["observable"]["rhythm"] == "Asystole"


def test_a_case_without_the_declarations_is_untouched():
    state, _ = build()
    adapter.initialize(state)
    minutes(state, 20)
    assert ggluc.generated_effects(state) == 0.0
    assert gopi.generated_effects(state) == (0.0,) * 5
    assert ggluc.mental_status(state) is None and gopi.mental_status(state) is None
