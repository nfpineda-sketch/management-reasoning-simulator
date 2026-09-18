"""Two gaps seen in the paid sildenafil case.

1. Its POCUS read "At arrival: normal contractility. Current physiology:
   Moderately to severely reduced global contraction". The author wrote a normal
   LV, but the drivers it chose (cardiac_function 0.7, contractile_reserve 0.6)
   make the core read a weak LV from the first minute. A scan now keeps the
   authored finding until the core's own reading changes, and then reports the
   current finding alone.
2. "Chest pressure suggests acute coronary syndrome" was not a working model.
"""
import pytest

import coupled_encounter as adapter
from test_coupled_encounter import patient
from test_curriculum_trajectories import load_engine

AUTHORED = {"lv": "normal contractility", "ivc": "1.2 cm; >50% inspiratory collapse", "lungs": "no B-lines",
            "rv": "smaller than LV; no D-sign; no McConnell sign"}


def weak_core_normal_words():
    state = patient(cardiac_function=.7, contractile_reserve=.6)
    case = state["encounter_spec"]["clinical_case"]
    case["investigations"]["pocus"] = {"duration_min": 2, "result": dict(AUTHORED), "result_bindings": {}}
    return state


def scan(state):
    return adapter.collect(state, "pocus", 2)["result"]


def test_the_core_arrival_reading_is_derived_from_the_authored_drivers():
    state = weak_core_normal_words()
    assert adapter.arrival_core_pocus(state["encounter_spec"]["clinical_case"])["lv"] == \
        "Moderately to severely reduced global contraction"


def test_an_unchanged_physiology_keeps_the_authored_findings_without_an_arrival_prefix():
    result = scan(weak_core_normal_words())
    for key in ("lv", "ivc", "lungs", "rv"):
        assert result[key] == AUTHORED[key]
    assert not any("At arrival" in str(value) for value in result.values())


def test_a_real_change_reports_the_current_finding_alone():
    state = weak_core_normal_words()
    state["coupled_state"]["hidden"].update(cardiac_function=1.0, contractile_reserve=1.0, effective_contractility=1.0)
    result = scan(state)
    assert result["lv"] == "Preserved to hyperdynamic contraction"
    assert result["rv"] == AUTHORED["rv"]


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("text, model", [
    ("Chest pressure suggests acute coronary syndrome. My priority is relieving ischemia.",
     "Chest pressure suggests acute coronary syndrome"),
    ("Hypotension after sildenafil points to vasodilatory shock. My priority is perfusion.",
     "Hypotension after sildenafil points to vasodilatory shock"),
    ("The POCUS is consistent with hypovolemia. My priority is volume.", "The POCUS is consistent with hypovolemia"),
    ("La hipotensión sugiere shock vasodilatador. Mi prioridad es la perfusión.", "La hipotensión sugiere shock vasodilatador"),
])
def test_a_finding_that_suggests_a_diagnosis_is_a_working_model(engine, text, model):
    # The whole statement is kept: the finding the learner reasons from is part of the model.
    assert engine["extract_explicit_reasoning"](text)["problem_representation"] == model


def test_an_order_is_never_the_subject_of_a_suggestion(engine):
    reasoning = engine["extract_explicit_reasoning"]("Give 500 mL NS as the IVC suggests volume responsiveness.")
    assert reasoning.get("problem_representation") is None


# Generation gate ------------------------------------------------------------

import json
from generated_case_schema import compile_case
from generated_case_validation import ContractValidationError
from generated_pocus_consistency import issues as pocus_core_issues
from test_generated_case import novel_payload


def gate_codes(raw):
    try:
        compile_case(raw)
    except ContractValidationError as error:
        return [issue for issue in error.issues if issue["code"] == "POCUS_CORE_MISMATCH"]
    return []


def with_drivers(**hidden):
    raw = novel_payload()
    raw["engine"]["core_profile"]["initial_hidden"].update(hidden)
    return raw


def test_the_default_payload_agrees_with_its_drivers():
    assert gate_codes(novel_payload()) == []


def test_a_normal_lv_with_weak_drivers_is_rejected_with_the_rule_to_fix_it():
    [issue] = gate_codes(with_drivers(cardiac_function=.7, contractile_reserve=.6))
    assert issue["details"] == {"field": "lv", "authored_level": "preserved or hyperdynamic",
                                "core_level": "moderately to severely reduced"}
    assert "cardiac_function x contractile_reserve" in issue["message"]


def test_one_category_apart_is_left_to_the_reviewer():
    # 0.8 x 0.75 = 0.60: the core reads mildly reduced, the author wrote hyperdynamic.
    assert gate_codes(with_drivers(cardiac_function=.8, contractile_reserve=.75)) == []


def test_a_collapsing_ivc_with_full_drivers_is_rejected():
    assert [i["details"]["field"] for i in gate_codes(with_drivers(effective_volume=.8))] == ["ivc"]


def test_no_b_lines_with_heavy_congestion_is_rejected_but_focal_b_lines_are_not_judged():
    assert [i["details"]["field"] for i in gate_codes(with_drivers(pulmonary_congestion=.6))] == ["lungs"]
    raw = with_drivers(pulmonary_congestion=.6)
    pocus = next(study for study in raw["investigations"] if study["id"] == "pocus")
    next(item for item in pocus["result"] if item["field"] == "lungs")["value"] = "Focal B-lines at the right base"
    assert gate_codes(raw) == []


@pytest.mark.parametrize("hidden", [
    {"cardiac_function": .7, "contractile_reserve": .6, "effective_volume": .3, "pulmonary_congestion": .2},
    {"cardiac_function": .9, "contractile_reserve": 1.0, "effective_volume": .7, "pulmonary_congestion": .6},
    {"cardiac_function": .6, "contractile_reserve": .9, "effective_volume": .5, "pulmonary_congestion": .1},
])
def test_the_gate_thresholds_mirror_the_core(hidden):
    # The gate's categories must match the core's own arrival findings.
    from coupled_encounter import arrival_core_pocus
    from generated_pocus_consistency import _b_line_level, _ivc_level, _lv_level
    raw = with_drivers(**hidden)
    case = {"engine": raw["engine"]}
    core = arrival_core_pocus(case)
    for field, classify in (("lv", _lv_level), ("ivc", _ivc_level), ("lungs", _b_line_level)):
        pocus = next(study for study in raw["investigations"] if study["id"] == "pocus")
        next(item for item in pocus["result"] if item["field"] == field)["value"] = core[field]
    assert gate_codes(raw) == []
    assert all(classify(core[field]) is not None for field, classify in
               (("lv", _lv_level), ("ivc", _ivc_level), ("lungs", _b_line_level)))


def test_the_paid_sildenafil_case_would_now_be_sent_back_for_its_lv():
    case = {"engine": {"core_profile": {"initial_hidden": {"cardiac_function": .7, "contractile_reserve": .6,
                                                           "effective_volume": .3, "pulmonary_congestion": .2}}},
            "investigations": {"pocus": {"result": {"lv": "normal contractility", "ivc": "1.2 cm; >50% inspiratory collapse",
                                                    "lungs": "no B-lines"}}}}
    assert [i["details"]["field"] for i in pocus_core_issues(case)] == ["lv"]


# SpO2 anchored to the authored arrival value ---------------------------------

def spo2_patient(authored=96, **hidden):
    state = patient(**hidden)
    case = state["encounter_spec"]["clinical_case"]
    case["observable"]["spo2"] = authored
    state["observable"]["spo2"] = authored
    state["coupled_state"] = {}
    adapter.initialize(state)
    return state


def test_an_authored_room_air_spo2_is_kept_instead_of_falling_to_the_core_equilibrium():
    # The core's room-air target was 94 - 16 x burden: an authored 96% fell to 91%.
    from test_coupled_encounter import run
    from test_generated_engine import wait
    state = spo2_patient(96, pulmonary_congestion=.2, primary_respiratory_burden=.1)
    assert adapter.core_spo2_target(state["coupled_state"]) < 92
    run(state, wait(15))
    assert state["observable"]["spo2"] >= 95


def test_oxygen_still_raises_the_anchored_spo2():
    from test_coupled_encounter import run
    from test_generated_engine import wait
    state = spo2_patient(92, pulmonary_congestion=.2, primary_respiratory_burden=.1)
    run(state, wait(5))
    before = state["observable"]["spo2"]
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4}, wait(10))
    assert state["observable"]["spo2"] > before


def test_a_state_saved_before_the_anchor_behaves_as_before():
    state = spo2_patient(96)
    state["generated_state"].pop("spo2_anchor")
    adapter.prepare_inputs(state)
    assert state["coupled_state"]["physiology_inputs"]["spo2"] == 0
