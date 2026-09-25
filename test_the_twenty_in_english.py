"""The twenty scripts in English are read as the Spanish ones are.

Requested on 2026-09-25 ("si puedes correlos con las indicaciones en inglés
también"). The English scripts keep every step of the Spanish ones and change
only the resident's words, so each order can be compared with its original:
the same decision in either language has to become the same actions. Running
them found English phrasings the reader did not know -- a peripheral IV, an
oral snack, "put her on" a mask, metamizole, "I prepare for intubation", a
hyphenated auto-injector, "send her home" -- and one it misread: "...and more
effort", a description, taken for an order to repeat something.
"""
import pytest

import tanda20
import tanda20_en
import tools_tanda20
from family_parser import parse_family_actions


def _read(text):
    parsed = parse_family_actions(text)
    actions = sorted(str(a.get("type")) + (f"/{a.get('destination')}" if a.get("type") == "disposition" else "")
                     for a in parsed["actions"])
    details = sorted({(d.get("kind"), d.get("category")) for d in parsed.get("future_details") or []})
    return actions, details


def test_the_english_scripts_are_the_spanish_scripts_in_other_words():
    assert [s["number"] for s in tanda20_en.SCRIPTS] == [s["number"] for s in tanda20.SCRIPTS]
    for spanish, english in zip(tanda20.SCRIPTS, tanda20_en.SCRIPTS):
        assert (english["case_id"], english["challenge"], english["language"]) == (
            spanish["case_id"], spanish["challenge"], "en")
        assert [tanda20_en._shape(step) for step in english["steps"]] == [
            tanda20_en._shape(step) for step in spanish["steps"]]


ORDERS = [(spanish["number"], index, step[1], english["steps"][index][1])
          for spanish, english in zip(tanda20.SCRIPTS, tanda20_en.SCRIPTS)
          for index, step in enumerate(spanish["steps"]) if step[0] == "order"]


@pytest.mark.parametrize("number, index, spanish, english", ORDERS,
                         ids=[f"{n}-{i + 1}" for n, i, _, _ in ORDERS])
def test_each_order_reads_the_same_in_both_languages(number, index, spanish, english):
    assert _read(english) == _read(spanish)


@pytest.mark.parametrize("text, kind", [
    ("Place a peripheral IV", "vascular_access"),
    ("Place a PIV", "vascular_access"),
    ("Start an IV", "vascular_access"),
    ("Get IV access", "vascular_access"),
    ("Start an IV bolus of NS 500 mL", "fluid"),
    ("Give him an oral snack", "oral_carbohydrate"),
    ("Put her on a non-rebreather mask at 10 L/min", "oxygen"),
    ("Put him on BiPAP 12/5", "niv"),
    ("Put in a Foley catheter", "urinary_catheter"),
    ("Give metamizole 1 g IV", "antipyretic"),
    ("I prepare for intubation", "airway_preparation"),
    ("Prepare for RSI", "airway_preparation"),
    ("Send her home with her husband", "disposition"),
    ("Send a troponin", "diagnostic"),
    ("Continuous monitoring", "monitoring"),
    ("Monitorizacion continua", "monitoring"),
])
def test_english_orders_the_reader_did_not_know(text, kind):
    assert [action["type"] for action in parse_family_actions(text)["actions"]] == [kind]


@pytest.mark.parametrize("text, hours", [
    ("Keep him under observation", None),
    ("Keep him under observation for 2 hours", 2.0),
    ("Observe in the ED for 6 hours", 6.0),
])
def test_observation_in_english_is_the_destination_it_is_in_spanish(text, hours):
    [action] = parse_family_actions(text)["actions"]
    assert action == {"type": "disposition", "destination": "ED observation", "duration_h": hours}


def test_a_hyphenated_auto_injector_is_the_auto_injector():
    [detail] = parse_family_actions("Prescribe an epinephrine auto-injector at discharge")["future_details"]
    assert (detail["kind"], detail["category"]) == ("prescription", "adrenaline_autoinjector")


def test_a_patient_with_more_effort_is_described_not_treated_again():
    assert parse_family_actions("SpO2 92% with RR 32 and more effort")["actions"] == []
    # What "more" still repeats, it repeats as before.
    assert [a["type"] for a in parse_family_actions("Another 500 mL bolus")["actions"]] == ["repeat_order"]
    assert [a["type"] for a in parse_family_actions("Give more naloxone 0.4 mg IV")["actions"]] == ["repeat_order"]


def test_a_reassessment_alone_is_not_an_order_read_as_nothing_in_either_language():
    for text in ("Reevaluo en 15 minutos", "Reassess in 15 minutes", "Reassess in 20 minutes HR and saturation"):
        assert tools_tanda20._ONLY_A_REASSESSMENT.fullmatch(text)


# --- the answers to "what will you check?" and "what do you expect?" ---------------

@pytest.fixture(scope="module")
def engine():
    from copy import deepcopy
    from test_cognitive_encounters import encounter as build_encounter
    from test_curriculum_trajectories import initialize, load_engine
    loaded = load_engine()
    initialize(loaded, deepcopy(build_encounter(loaded, "opioid", "opioid_35m")["state"]))
    return loaded


def _stated(engine, text):
    reasoning = engine["clinical_interpreter"](text).get("reasoning", {})
    return {slot: bool(reasoning.get(slot)) for slot in ("expected_effect", "reassessment_target")}


ANSWERS = [(spanish["number"], index, step[1], english["steps"][index][1])
           for spanish, english in zip(tanda20.SCRIPTS, tanda20_en.SCRIPTS)
           for index, step in enumerate(spanish["steps"]) if step[0] == "answer"]


@pytest.mark.parametrize("number, index, spanish, english", ANSWERS,
                         ids=[f"{n}-{i + 1}" for n, i, _, _ in ANSWERS])
def test_each_answer_states_the_same_categories_in_both_languages(engine, number, index, spanish, english):
    assert _stated(engine, english) == _stated(engine, spanish)


@pytest.mark.parametrize("text, target", [
    ("I will count the respiratory rate and look at the saturation.", "respiratory rate and look at the saturation"),
    ("I will see whether he wakes up.", "he wakes up"),
    ("I will check that she stays awake before she leaves.", "she stays awake before she leaves"),
    ("I'll look at the saturation.", "saturation"),
    ("I see that the RR is 10.", None),
])
def test_an_english_answer_names_what_will_be_checked(engine, text, target):
    assert engine["clinical_interpreter"](text).get("reasoning", {}).get("reassessment_target") == target
