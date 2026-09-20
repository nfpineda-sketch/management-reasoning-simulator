"""The last two mechanisms: blood being lost, and a lung that is full.

Faculty decision (2026-09-20). The bleeding one is full, because the shared core
models volume but never models losing blood. The congestion one is deliberately
thin: the core already owns congestion, so the mechanism adds only the intravenous
nitroglycerin bolus, which no native action covers.
"""
import pytest

import coupled_encounter as adapter
import generated_bleeding as bleed
import generated_congestion as congestion
from clinical_core_defaults import CORE_VERSION, INITIAL_HIDDEN, PHENOTYPE_FIELDS
from family_engine import GI_BLEED
from generated_bleeding_consistency import bleeding_issues, congestion_issues
from generated_engine import execute_generated_bundle
from test_generated_engine import make_state

MELENA = "Rectal examination reveals black tarry stool."
CRACKLES = "Bilateral inspiratory crackles to the mid-zones."


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


def bleeding_case(hemoglobin=7.2):
    state, case = build(active_bleeding={"established": True})
    case["engine"]["initial_labs"]["hemoglobin_g_dl"] = hemoglobin
    case["investigations"]["basic_labs"]["result"]["hemoglobin_g_dl"] = hemoglobin
    case["examination"]["Abdomen"] = MELENA
    adapter.initialize(state)
    return state


def congested_case():
    state, case = build(pulmonary_congestion={"cardiogenic": True})
    case["examination"]["Respiratory"] = CRACKLES
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


def test_described_bleeding_obliges_the_declaration():
    case = {"examination": {"Abdomen": MELENA}, "history": {}, "investigations": {}, "engine": {}}
    assert [i["code"] for i in bleeding_issues(case)] == ["ACTIVE_BLEEDING_UNDECLARED"]


def test_a_bleed_nobody_can_find_is_refused():
    case = {"examination": {"Abdomen": "Soft and non-tender."}, "history": {}, "investigations": {},
            "engine": {"active_bleeding": {"established": True}}}
    assert [i["code"] for i in bleeding_issues(case)] == ["ACTIVE_BLEEDING_UNDISCOVERABLE"]


def test_an_established_bleed_must_arrive_anaemic():
    case = {"examination": {"Abdomen": MELENA}, "history": {}, "investigations": {},
            "engine": {"active_bleeding": {"established": True}, "initial_labs": {"hemoglobin_g_dl": 14}}}
    assert [i["path"] for i in bleeding_issues(case)] == ["case.engine.initial_labs.hemoglobin_g_dl"]
    case["engine"]["initial_labs"]["hemoglobin_g_dl"] = 7.4
    assert bleeding_issues(case) == []


def test_described_congestion_obliges_its_declaration():
    case = {"examination": {"Respiratory": CRACKLES}, "history": {}, "investigations": {}, "engine": {}}
    assert [i["code"] for i in congestion_issues(case)] == ["PULMONARY_CONGESTION_UNDECLARED"]


def test_congestion_nobody_can_find_is_refused():
    case = {"examination": {"Respiratory": "Clear breath sounds."}, "history": {}, "investigations": {},
            "engine": {"pulmonary_congestion": {"cardiogenic": True}}}
    assert [i["code"] for i in congestion_issues(case)] == ["PULMONARY_CONGESTION_UNDISCOVERABLE"]


def test_the_gates_are_wired_and_their_codes_are_reportable():
    import inspect
    from generated_case_schema import collect_clinical_issues
    from generated_case_validation import CLINICAL_ISSUE_CODES
    assert "generated_bleeding_consistency" in inspect.getsource(collect_clinical_issues)
    for code in ("ACTIVE_BLEEDING_UNDECLARED", "ACTIVE_BLEEDING_UNDISCOVERABLE",
                 "PULMONARY_CONGESTION_UNDECLARED", "PULMONARY_CONGESTION_UNDISCOVERABLE"):
        assert code in CLINICAL_ISSUE_CODES


def test_the_haemoglobin_falls_while_the_bleeding_continues():
    state = bleeding_case()
    minutes(state, 30)
    assert bleed.generated_effects(state)[5] < -.2
    assert state["family_state"]["bleeding_burden"] > 0


def test_blood_raises_it_and_crystalloid_dilutes_it():
    transfused = bleeding_case()
    order(transfused, {"type": "blood", "units": 2})
    minutes(transfused, 65)
    fluid = bleeding_case()
    order(fluid, {"type": "fluid", "volume_ml": 1000, "fluid_type": "normal saline", "route": "IV"})
    minutes(fluid, 65)
    assert bleed.generated_effects(transfused)[5] > 0
    assert bleed.generated_effects(fluid)[5] < bleed.generated_effects(transfused)[5] - 1


def test_the_proton_pump_inhibitor_slows_it():
    treated = bleeding_case()
    order(treated, {"type": "ppi", "agent": "pantoprazole", "dose_mg": 80, "route": "IV"})
    minutes(treated, 60)
    untreated = bleeding_case()
    minutes(untreated, 60)
    assert bleed.generated_effects(treated)[5] > bleed.generated_effects(untreated)[5]


def test_gastroenterology_defers_the_endoscopy_until_the_patient_is_resuscitated():
    state = bleeding_case()
    order(state, {"type": "consult", "service": "gastroenterology"})
    events = minutes(state, GI_BLEED["endoscopy_after_consult_min"] + 5)
    assert any("defers endoscopy" in e["label"] for e in events)
    assert state["family_state"].get("endoscopy_at") is None


def test_the_mechanism_authorises_blood_and_the_proton_pump_inhibitor():
    state = bleeding_case()
    assert order(state, {"type": "blood", "units": 1})["executed"]
    assert order(state, {"type": "ppi", "agent": "pantoprazole", "dose_mg": 80, "route": "IV"})["executed"]


def test_a_case_without_the_bleeding_declaration_is_untouched():
    state, _ = build()
    adapter.initialize(state)
    minutes(state, 30)
    assert bleed.generated_effects(state) == (0.0,) * 6


def test_the_bolus_the_core_has_no_answer_for():
    state = congested_case()
    result = order(state, {"type": "nitroglycerin_bolus", "dose_mcg": 2000, "route": "IV"})
    assert "2000 mcg IV bolus" in " ".join(s.get("label", "") for s in result["action_summaries"])
    minutes(state, 3)
    sbp, _, spo2, rr = congestion.generated_effects(state)
    assert sbp < -8 and spo2 > 0 and rr < 0
    minutes(state, 12)
    # The bolus fades; what it unloaded stays.
    assert congestion.generated_effects(state)[0] > -2
    assert state["family_state"]["congestion_relieved"] > .2


def test_the_bolus_needs_the_declaration():
    state, _ = build()
    adapter.initialize(state)
    refused = execute_generated_bundle(state, {"actions": [
        {"type": "nitroglycerin_bolus", "dose_mcg": 2000, "route": "IV"}]})
    assert not refused["executed"]
    assert congestion.generated_effects(state) == (0.0,) * 4
