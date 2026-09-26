"""The reader, focused on the orders the hypoglycaemia battery plays.

The battery gives the engine structured actions, so it proves nothing about
words: that a resident's sentence becomes the action the battery used is a
separate question, answered only here and only for the phrasings listed. A
phrasing absent from this file is untested, not supported. The known gaps are
kept as strict expected failures: when one starts working the test says so and
the list in docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md is updated.
"""
import pytest

from family_parser import parse_family_actions


def _read(text):
    return [{key: value for key, value in action.items() if key not in {"message", "unrecognized_text"}}
            for action in parse_family_actions(text)["actions"]]


@pytest.mark.parametrize("text", ["Pido glicemia capilar", "HGT", "Hemoglucotest", "Control de glicemia capilar",
                                  "Check a fingerstick glucose"])
def test_the_bedside_glucose(text):
    assert _read(text) == [{"type": "diagnostic", "diagnostic": "poc_glucose"}]


@pytest.mark.parametrize("text, grams", [
    ("Doy dextrosa 25 g ev", 25.0), ("Give dextrose 25 g IV", 25.0), ("Doy glucosa 25 g ev", 25.0),
    ("Doy glucosa al 30% 50 ml ev", 15.0),
    # Read since 2026-09-25: a solution with its volume is a dose, verb or not.
    ("Dextrosa al 50% 50 mL EV", 25.0), ("D50 50 mL IV", 25.0),
])
def test_the_ampoule(text, grams):
    [action] = _read(text)
    assert (action["type"], action["dose_g"], action["route"]) == ("dextrose", grams, "IV")


@pytest.mark.parametrize("text", [
    "Inicio infusion de glucosa al 10% a 100 ml/h", "Start dextrose 10% infusion at 100 mL/h",
    "Dextrose 10% at 100 mL/h",
    # Read as the infusion since 2026-09-25; the first was a 10 g bolus before.
    "Inicio infusión de dextrosa al 10% a 100 mL/h", "SG 10% a 100 ml/h", "Suero glucosado al 10% a 100 mL/h EV",
    "Glucosado 10% 100 ml/h",
])
def test_the_ten_percent_infusion(text):
    assert _read(text) == [{"type": "dextrose_infusion", "rate_ml_h": 100.0, "concentration_percent": 10,
                            "operation": "start"}]


@pytest.mark.parametrize("text, kind, route", [
    ("Glucagón 1 mg IM", "glucagon", "IM"), ("Glucagon 1 mg IM", "glucagon", "IM"),
    ("Octreótido 50 mcg SC", "octreotide", "SC"), ("Octreotide 50 mcg SC", "octreotide", "SC"),
    ("Tiamina 100 mg EV", "thiamine", "IV"), ("Thiamine 100 mg IV", "thiamine", "IV"),
])
def test_the_other_agents(text, kind, route):
    [action] = _read(text)
    assert (action["type"], action["route"]) == (kind, route)


@pytest.mark.parametrize("text, expected", [
    ("Instalo nueva vía venosa periférica", [{"type": "vascular_access", "operation": "start"}]),
    ("Place a peripheral IV", [{"type": "vascular_access", "operation": "start"}]),
    ("Le doy jugo con azúcar", [{"type": "oral_carbohydrate"}]),
    ("Give oral glucose", [{"type": "oral_carbohydrate"}]),
    ("Hospitalizo en sala", [{"type": "disposition", "destination": "ward"}]),
    ("Doy de alta", [{"type": "disposition", "destination": "home"}]),
    ("Observación en urgencias por 12 horas", [{"type": "disposition", "destination": "ED observation",
                                                "duration_h": 12.0}]),
    ("Reevalúo en 15 minutos", [{"type": "reassessment", "delay_min": 15.0}]),
])
def test_line_food_destination_and_time(text, expected):
    assert _read(text) == expected


@pytest.mark.parametrize("text", ["La glucosa esta baja", "Espero que la glucosa suba sobre 100"])
def test_a_description_or_an_expectation_is_not_an_order(text):
    assert _read(text) == []


# Read since 2026-09-26 (they were the known gaps below until then).
@pytest.mark.parametrize("text, expected", [
    ("Glucosa capilar", [{"type": "diagnostic", "diagnostic": "poc_glucose"}]),
    ("Glicemia capilar", [{"type": "diagnostic", "diagnostic": "poc_glucose"}]),
    ("Hemoglucotest ahora", [{"type": "diagnostic", "diagnostic": "poc_glucose"}]),
    ("Nueva vía venosa", [{"type": "vascular_access", "operation": "start"}]),
    ("Vía venosa nueva", [{"type": "vascular_access", "operation": "start"}]),
    ("2 vvp gruesas", [{"type": "vascular_access", "operation": "start"}]),
    ("VVP", [{"type": "vascular_access", "operation": "start"}]),
    ("Consulto a endocrinología", [{"type": "consult", "service": "endocrinology"}]),
    ("Bolo de SF 500 ml EV", [{"type": "fluid", "volume_ml": 500.0, "fluid_type": "normal saline", "route": "IV"}]),
])
def test_orders_written_as_on_a_chart(text, expected):
    assert _read(text) == expected


@pytest.mark.parametrize("text", ["Vía venosa", "Vía venosa permeable", "VVP permeable"])
def test_a_line_the_patient_has_is_not_an_order_for_a_new_one(text):
    assert _read(text) == []


@pytest.mark.parametrize("text, grams", [
    ("Bolo de glucosado al 50% 50 mL EV", 25.0), ("Bolo de dextrosa 25 g EV", 25.0),
    ("2 ampollas de glucosa al 30% 20 ml cada una EV", 12.0),
])
def test_glucose_written_as_a_bolus_or_by_the_ampoule(text, grams):
    [action] = _read(text)
    assert (action["type"], action["dose_g"], action["route"]) == ("dextrose", grams, "IV")


def test_ampoules_with_no_volume_are_an_order_whose_dose_is_asked_for():
    """Dropped in silence until 2026-09-26; now the same order as with a verb."""
    assert _read("2 ampollas de glucosado al 30%") == [{"type": "dextrose", "dose_g": None, "route": None}]
    assert _read("Doy 2 ampollas de glucosa al 30%") == [{"type": "dextrose", "dose_g": None, "route": None}]


def test_ampoules_whose_volume_may_be_the_total_or_each_ask_for_the_total():
    [question] = parse_family_actions("Doy 2 ampollas de glucosa al 30% de 20 ml")["actions"]
    assert question["type"] == "clarification" and "total" in question["message"]


@pytest.mark.parametrize("text", ["Suero glucosado al 5% a 100 ml/h", "Inicio SG 5% a 100 ml/h", "D5 a 100 ml/h",
                                  "Suero glucosado 5% 500 ml", "Glucosado al 20% a 50 ml/h"])
def test_a_glucose_infusion_the_engine_does_not_run_is_recorded_not_converted(text):
    """Read as the 10% infusion until 2026-09-26. Faculty decision 3: indicated, effect not modelled."""
    parsed = parse_family_actions(text)
    assert parsed["actions"] == []
    assert parsed["recognized_future_actions"] == [text.lower()]


def test_the_rest_of_the_submission_runs_beside_an_infusion_that_is_not_modelled():
    parsed = parse_family_actions("Doy 25 g de glucosa ev y suero glucosado al 5% a 100 ml/h")
    assert [(a["type"], a.get("dose_g")) for a in parsed["actions"]] == [("dextrose", 25.0)]
    assert parsed["recognized_future_actions"] == ["suero glucosado al 5% a 100 ml/h"]


GAPS = [
    ("Coloco una vía intraósea", "vascular_access", "no hay acción de acceso intraóseo (DC3)"),
    ("Reviso la vía venosa", "examination", "revisar la vía no es una acción ni un examen (DC2)"),
]


@pytest.mark.parametrize("text, wanted, gap", GAPS, ids=[g[0] for g in GAPS])
@pytest.mark.xfail(strict=True, reason="known gap of the reader, listed in the pending decisions document")
def test_known_gaps_of_the_reader(text, wanted, gap):
    actions = _read(text)
    kind, _, service = wanted.partition(":")
    assert [a["type"] for a in actions] == [kind]
    if service:
        assert actions[0].get("service") == service
