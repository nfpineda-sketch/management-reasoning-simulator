"""A discharge keeps the plan it is written with, in both languages (DF-10).

"Discharge her with cardiology follow-up" and "la doy de alta con control en
policlinico" executed the discharge and lost the follow-up, where the same
follow-up listed after the discharge (", control urologico") was kept. Approved
for correction by class on 2026-09-27. Every sentence here was written for the
test, none is taken from the rehearsal corpus (§57).
"""
import pytest

import language
import unexecuted_items
from family_parser import parse_family_actions


def _read(text):
    parsed = parse_family_actions(text)
    return [(a["type"], a.get("destination")) for a in parsed["actions"]], parsed["recognized_future_actions"]


@pytest.mark.parametrize("text, plan", [
    ("Discharge her home with dermatology follow-up in ten days.", ["dermatology follow-up in ten days"]),
    ("La doy de alta con control en policlínico de dermatología en diez días.",
     ["control en policlinico de dermatologia en diez dias"]),
    ("Discharge him with a follow-up appointment in the chest clinic.", ["a follow-up appointment in the chest clinic"]),
    ("Lo doy de alta con citación a policlínico de broncopulmonar.", ["citacion a policlinico de broncopulmonar"]),
])
def test_the_follow_up_written_into_the_discharge_is_kept_and_the_discharge_still_runs(text, plan):
    actions, future = _read(text)
    assert actions == [("disposition", "home")]
    assert future == plan


@pytest.mark.parametrize("text, plan", [
    ("Discharge with primary care follow-up this week and return precautions for bleeding or dizziness.",
     ["primary care follow-up this week", "return precautions for bleeding or dizziness"]),
    ("Alta con seguimiento en atención primaria esta semana y signos de alarma por sangrado o mareo.",
     ["seguimiento en atencion primaria esta semana", "signos de alarma por sangrado o mareo"]),
    ("Discharge him with a follow-up appointment in the chest clinic and return if the breathlessness worsens.",
     ["a follow-up appointment in the chest clinic", "return if the breathlessness worsens"]),
    ("Lo doy de alta con citación a policlínico y volver si empeora la disnea.",
     ["citacion a policlinico", "volver si empeora la disnea"]),
])
def test_the_follow_up_and_the_return_advice_keep_the_order_they_were_written_in(text, plan):
    actions, future = _read(text)
    assert actions == [("disposition", "home")]
    assert future == plan


@pytest.mark.parametrize("text, plan", [
    ("Discharge with analgesia and ophthalmology follow-up.", ["ophthalmology follow-up"]),
    ("Alta con analgesia y control en policlínico de oftalmología.", ["control en policlinico de oftalmologia"]),
])
def test_a_follow_up_listed_after_the_discharge_is_kept_once(text, plan):
    assert _read(text) == ([("disposition", "home")], plan)


@pytest.mark.parametrize("text", ["Discharge her with her daughter.", "La doy de alta con su hija."])
def test_what_is_not_a_plan_is_not_turned_into_one(text):
    assert _read(text) == ([("disposition", "home")], [])


def test_an_admission_written_with_a_plan_is_left_as_it_was():
    # The correction is for the discharge; an admission's "con control" is an
    # inpatient order, not advice to take home.
    parsed = parse_family_actions("Hospitalizo en sala con control de glicemia cada 6 horas.")
    assert "control de glicemia cada 6 horas" not in parsed["recognized_future_actions"]


@pytest.fixture(scope="module")
def engine():
    from test_curriculum_trajectories import initialize, load_engine
    loaded = load_engine()
    initialize(loaded, loaded["INITIAL_STATE"])
    loaded["st"].session_state["state"] = {"engine_family": "generated", "observable": {}}
    return loaded


@pytest.mark.parametrize("text, rationale", [
    ("Discharge her with nephrology follow-up because the creatinine is back to baseline.",
     "the creatinine is back to baseline"),
    ("La doy de alta con control en nefrología porque la creatinina volvió a su basal.",
     "la creatinina volvió a su basal"),
])
def test_the_reason_for_the_discharge_is_still_the_rationale(engine, text, rationale):
    parsed = engine["clinical_interpreter"](text)
    assert parsed["reasoning"].get("rationale") == rationale
    assert [a["type"] for a in parsed["actions"]] == ["disposition"]
    assert len(parsed["recognized_future_actions"]) == 1


def test_a_held_discharge_names_its_follow_up_as_advice_and_asks_for_nothing_more(engine):
    text = "Lo doy de alta con control en policlínico de traumatología en dos semanas."
    parsed = engine["clinical_interpreter"](text)
    missing = engine["reasoning_gate_missing"](parsed)
    # The gate asks what it asked before the follow-up was kept, and no more.
    assert missing == ["working_model", "expected_effect", "reassessment_target"]
    prompt = engine["reasoning_gate_prompt"](parsed, missing)
    assert "These medications have not been administered" not in prompt
    assert "advice to the patient: control en policlinico de traumatologia en dos semanas" in prompt
    assert "una indicación al paciente: «control en policlinico de traumatologia en dos semanas»" in \
        language.say(prompt, "es")


def test_a_held_order_names_each_item_as_what_it_is():
    parsed = {"future_details": [
        {"text": "ondansetron 4 mg iv", "kind": "not_modelled"},
        {"text": "cardiology follow-up", "kind": "advice"},
    ]}
    assert unexecuted_items.held_messages(parsed) == [
        "Also in this order, indicated with administration and effect not modelled: ondansetron 4 mg iv.",
        "Also in this order, advice to the patient: cardiology follow-up.",
    ]
