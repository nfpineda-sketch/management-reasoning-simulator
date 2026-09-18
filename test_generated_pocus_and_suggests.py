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
