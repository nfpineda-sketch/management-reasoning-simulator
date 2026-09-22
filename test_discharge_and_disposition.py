"""Sending the patient home, and where an admitted patient goes.

Faculty decisions 1 and 2 of 2026-09-21, from the full bank review: discharge
did not exist at all, so the closing decision of "check whether the problem is
fully addressed" could not be written; and a discharge decided while the problem
is still running is answered by the patient coming back, not by silence. The
coronary unit is a cardiovascular critical-care bed under all of its names.
"""
import pytest

from family_engine import DISCHARGE_RETURN_DELAY_MIN, _discharge_alarm
from family_parser import parse_family_actions


def disposition(text):
    return next((a for a in parse_family_actions(text)["actions"] if a.get("type") == "disposition"), None)


@pytest.mark.parametrize("text", [
    "Dale de alta con indicaciones.",
    "Dar de alta a domicilio.",
    "Dale el alta medica.",
    "Mandalo a la casa con control en 24 horas.",
    "Discharge him home with follow-up.",
])
def test_discharge_is_a_disposition(text):
    assert disposition(text) == {"type": "disposition", "destination": "home"}


@pytest.mark.parametrize("text", [
    "Hospitaliza en la unidad coronaria.",
    "Traslada a la UCO.",
    "Hospitalizalo en la unidad de cuidados coronarios.",
    "Admit to the coronary care unit.",
    "Transfer to the CCU.",
    "Admit to the cardiac ICU.",
])
def test_the_coronary_unit_is_a_destination(text):
    assert disposition(text)["destination"] == "coronary care unit"


@pytest.mark.parametrize("text, destination", [
    ("Hospitalizalo en UCI.", "ICU"),
    ("Hospitalizalo en sala.", "ward"),
    ("Traslada a intermedio.", "intermediate care"),
])
def test_the_other_destinations_are_unchanged(text, destination):
    assert disposition(text)["destination"] == destination


def test_a_bare_admission_asks_where_instead_of_vanishing():
    actions = parse_family_actions("Hospitalizalo.")["actions"]
    assert actions and actions[0]["type"] == "clarification"
    assert "coronary care unit" in actions[0]["message"]


# The alarm that brings a discharged patient back.

@pytest.mark.parametrize("observable, expected", [
    ({"mental_status": "Alert", "spo2": 97, "respiratory_rate": 16, "sbp": 120}, None),
    ({"mental_status": "Drowsy"}, "found drowsy at home"),
    ({"mental_status": "Alert", "glucose_mg_dl": 48}, "unwell again, with a capillary glucose of 48 mg/dL"),
    ({"mental_status": "Alert", "respiratory_rate": 8}, "breathing 8 times a minute"),
    ({"mental_status": "Alert", "spo2": 86}, "with a saturation of 86% on room air"),
    ({"mental_status": "Alert", "sbp": 84}, "with a systolic pressure of 84 mmHg"),
    # A ventilated patient is not "not awake": the support is the reason.
    ({"mental_status": "Sedated"}, None),
])
def test_what_counts_as_coming_back(observable, expected):
    assert _discharge_alarm({"observable": observable}) == expected


def test_the_transport_delay_is_declared():
    assert DISCHARGE_RETURN_DELAY_MIN == 20


# The names a critical-care bed is asked for here. Found playing the generated
# cardiogenic shock case (2026-09-22): "hospitalízalo en la unidad de paciente
# crítico" was held asking for a destination the resident had already named.

@pytest.mark.parametrize("order, destination", [
    ("Hospitalizalo en la unidad de paciente critico.", "ICU"),
    ("Hospitalizalo en la UPC.", "ICU"),
    ("Hospitalizalo en la unidad de cuidados intensivos.", "ICU"),
    ("Hospitalizalo en la unidad de tratamiento intermedio.", "intermediate care"),
    ("Hospitalizalo en intermedio.", "intermediate care"),
    ("Hospitalizalo en la unidad coronaria.", "coronary care unit"),
    ("Hospitalizalo en sala.", "ward"),
])
def test_the_names_a_critical_care_bed_is_asked_for(order, destination):
    assert parse_family_actions(order)["actions"] == [
        {"type": "disposition", "destination": destination}]


def test_an_english_urinary_infection_is_not_a_bed():
    # "UTI" is the intermediate unit here and an infection in English, so the
    # abbreviation is deliberately not read as a destination.
    actions = parse_family_actions("Admit him for a UTI.")["actions"]
    assert actions[0]["type"] == "clarification"
