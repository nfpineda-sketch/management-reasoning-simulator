"""A single dose of a vasoactive drug must never become a continuous infusion.

A resident testing locally ordered "start nitroglycerin give a iv bolus 600 mcg"
and the app replied "I understood: start nitroglycerin 600 mcg/min". With no
explicit rate, the parser took any lone number as the infusion rate and dropped
its unit and route, so a bolus, an IV push or a sublingual tablet was turned into
an infusion. This engine runs these drugs only as infusions, so the order has to
be named back and nothing converted.
"""
import pytest

from family_parser import parse_family_actions


def only(text):
    actions = [a for a in parse_family_actions(text)["actions"] if a.get("type") != "reassessment"]
    assert len(actions) == 1, actions
    return actions[0]


@pytest.mark.parametrize("text,agent,form,dose", [
    ("nitroglycerin 400 mcg sublingual", "nitroglycerin", "sublingual dose", 400.0),
    ("nitroglycerin 400 mcg SL", "nitroglycerin", "sublingual dose", 400.0),
    ("give norepinephrine 10 mcg IV push", "norepinephrine", "IV push", 10.0),
])
def test_a_single_dose_is_named_back_and_nothing_is_executed(text, agent, form, dose):
    action = only(text)
    assert action["type"] == "clarification"
    assert "rate_mcg_min" not in action and "rate" not in action
    detail = action["unsupported_administration"]
    assert (detail["agent"], detail["form"], detail["dose"]) == (agent, form, dose)
    assert "nothing was converted or executed" in action["message"]


@pytest.mark.parametrize("text", [
    "start nitroglycerin give a iv bolus 600 mcg and reassess in 3 minutes",
    "give nitroglycerin 600 mcg IV bolus",
    "dar nitroglicerina bolo 600 mcg",
])
def test_an_iv_nitroglycerin_bolus_is_a_bolus_never_an_infusion(text):
    # Faculty decision (2026-09-18): nitroglycerin may be given as IV boluses.
    action = only(text)
    assert action == {"type": "nitroglycerin_bolus", "dose_mcg": 600.0, "route": "IV"}


def test_the_reassessment_in_the_same_order_is_kept():
    actions = parse_family_actions(
        "start nitroglycerin give a iv bolus 600 mcg and reassess in 3 minutes")["actions"]
    assert {"type": "reassessment", "delay_min": 3.0} in actions


@pytest.mark.parametrize("text,rate", [
    ("start nitroglycerin at 20 mcg/min", 20.0),
    ("start nitroglycerin at 600 mcg/min", 600.0),
    # A rate written in words is a rate, not a mass dose.
    ("start nitroglycerin 20 mcg per minute", 20.0),
    ("iniciar nitroglicerina 20 mcg por minuto", 20.0),
    ("increase nitroglycerin to 40 mcg/min", 40.0),
])
def test_an_infusion_rate_still_starts_an_infusion(text, rate):
    action = only(text)
    assert action["type"] == "nitroglycerin" and action["rate_mcg_min"] == rate


def test_a_bare_number_still_asks_for_units_rather_than_being_refused():
    action = only("start norepinephrine .1")
    assert action == {"type": "norepinephrine", "rate": 0.1, "units": None, "operation": "start"}


def test_a_weight_based_rate_in_words_is_understood():
    action = only("start norepinephrine 0.1 mcg per kg per min")
    assert action["rate"] == 0.1 and action["units"] == "mcg/kg/min"
