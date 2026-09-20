"""A generated case with right heart strain runs the bank's obstruction pathway.

Third mechanism (faculty decision 2026-09-20), same shape as the coronary and the
airway ones: an obligatory declaration, a gate that refuses what the resident
cannot discover, and the shared pe_obstruction module doing the work.
"""
import pytest

import coupled_encounter as adapter
import generated_pe as gpe
import pe_obstruction as pe
from generated_pe_consistency import issues
from test_coupled_encounter import patient, run

STRAIN = "Dilated right ventricle with septal flattening (D-sign); free wall hypokinesis."
LYSE = {"type": "thrombolysis", "agent": "alteplase", "dose_mg": 100, "route": "IV"}
FAST_FLUID = {"type": "fluid", "volume_ml": 1000, "fluid_type": "normal saline", "route": "IV",
              "administration_duration_min": 10}


def pe_case(bleeding_risk=None, rv=STRAIN, declare=True, history=None):
    state = patient()
    case = state["encounter_spec"]["clinical_case"]
    case["investigations"].setdefault("pocus", {"duration_min": 2, "result": {}})
    case["investigations"]["pocus"]["result"]["rv"] = rv
    case["history"] = history or {"medical_history": ["Ankle surgery twelve days ago."]}
    if declare:
        case["engine"]["pulmonary_obstruction"] = {"bleeding_risk": bleeding_risk}
    return state


def minutes(state, count):
    events = []
    for _ in range(count):
        adapter.tick(state)
        events += state["family_state"].pop("procedure_events", [])
    return events


def codes(case):
    return [issue["code"] for issue in issues(case)]


def test_right_heart_strain_obliges_the_declaration():
    case = {"investigations": {"pocus": {"result": {"rv": STRAIN}}}, "history": {}, "engine": {}}
    assert codes(case) == ["PULMONARY_OBSTRUCTION_UNDECLARED"]


def test_a_filling_defect_obliges_it_too():
    case = {"investigations": {"ctpa": {"result": {"report": "Acute lobar filling defects bilaterally."}}},
            "history": {}, "engine": {}}
    assert codes(case) == ["PULMONARY_OBSTRUCTION_UNDECLARED"]


def test_a_declaration_the_resident_cannot_find_is_refused():
    case = {"investigations": {"pocus": {"result": {"rv": "Smaller than the LV; no D-sign."}}},
            "history": {}, "engine": {"pulmonary_obstruction": {"bleeding_risk": None}}}
    assert codes(case) == ["PULMONARY_OBSTRUCTION_UNDISCOVERABLE"]


def test_a_declared_bleeding_risk_must_appear_in_the_history():
    case = {"investigations": {"pocus": {"result": {"rv": STRAIN}}}, "history": {},
            "engine": {"pulmonary_obstruction": {"bleeding_risk": "recent_surgery"}}}
    assert codes(case) == ["PULMONARY_OBSTRUCTION_UNDISCOVERABLE"]
    case["history"] = {"medical_history": ["He had surgery twelve days ago."]}
    assert codes(case) == []


def test_the_gate_is_wired_into_the_contract_and_its_codes_are_reportable():
    import inspect
    from generated_case_schema import collect_clinical_issues
    from generated_case_validation import CLINICAL_ISSUE_CODES
    assert "generated_pe_consistency" in inspect.getsource(collect_clinical_issues)
    for code in ("PULMONARY_OBSTRUCTION_UNDECLARED", "PULMONARY_OBSTRUCTION_UNDISCOVERABLE"):
        assert code in CLINICAL_ISSUE_CODES


def test_fast_volume_distends_the_ventricle():
    state = pe_case()
    run(state, FAST_FLUID)
    events = minutes(state, 12)
    assert state["family_state"]["rv_strain"] > .3
    sbp, dbp, hr, *_ = gpe.generated_effects(state)
    assert sbp < -8 and dbp < 0 and hr > 0
    assert any("faster than the obstructed right ventricle" in e["label"] for e in events)


def test_slow_volume_is_neither_treatment_nor_insult():
    state = pe_case()
    run(state, {"type": "fluid", "volume_ml": 250, "fluid_type": "normal saline", "route": "IV",
                "administration_duration_min": 30})
    minutes(state, 32)
    assert state["family_state"].get("rv_strain", 0) == 0
    assert gpe.generated_effects(state)[0] == 0


def test_a_vasopressor_keeps_the_hypotension_clock_running():
    state = pe_case()
    run(state, {"type": "norepinephrine", "operation": "start", "rate": .1, "units": "mcg/kg/min"})
    minutes(state, pe.SUSTAINED_HYPOTENSION_MIN + 2)
    assert pe.indicated(state["family_state"])


def test_thrombolysis_after_the_indication_dissolves_the_obstruction():
    state = pe_case()
    run(state, {"type": "norepinephrine", "operation": "start", "rate": .1, "units": "mcg/kg/min"})
    minutes(state, pe.SUSTAINED_HYPOTENSION_MIN + 2)
    result = run(state, LYSE)
    notes = [s["label"] for s in result["action_summaries"]]
    assert state["family_state"]["lysis_indicated"] is True
    minutes(state, 50)
    sbp, *_ = gpe.generated_effects(state)
    assert gpe.relief(state["family_state"]) > .2 and sbp > 5


def test_thrombolysis_before_the_indication_does_nothing():
    state = pe_case()
    run(state, LYSE)
    minutes(state, 50)
    assert state["family_state"]["lysis_indicated"] is False
    assert gpe.relief(state["family_state"]) == 0


def test_the_thrombolytic_bleeds_where_the_case_declares_a_reason():
    state = pe_case(bleeding_risk="recent_surgery")
    run(state, LYSE)
    events = minutes(state, 40)
    assert any("Bleeding from the surgical site" in e["label"] for e in events)
    assert gpe.generated_effects(state)[5] < -.5


def test_without_a_declared_risk_the_loss_stays_occult():
    state = pe_case()
    run(state, LYSE)
    events = minutes(state, 40)
    assert not any("Bleeding from" in e["label"] for e in events)
    assert -1 < gpe.generated_effects(state)[5] < -.1


def test_a_case_without_the_declaration_is_untouched():
    state = pe_case(declare=False)
    run(state, FAST_FLUID)
    minutes(state, 12)
    assert state["family_state"].get("rv_strain") is None
    assert gpe.generated_effects(state) == (0.0,) * 6
