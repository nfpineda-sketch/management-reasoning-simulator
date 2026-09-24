"""The clauses that were quoted back as orders nobody had written.

Measured on 2026-09-23, on fifteen orders that named all four categories the
simulator asks for: eight of them had a piece of their own reasoning quoted back
as ``This order was not recognized``. The resident wrote "quiero frenar la
agregacion", "the goal is to limit thrombus growth", "apunto a PAM sobre 65",
"controlo PAM"; the simulator held the whole submission and asked them to
replace their expectation with a supported intervention and a route.

Two more failures of the same kind are pinned here: a goal announced mid
sentence ("Given the hypoxemia I will start NIV") was read as prose and produced
no action and no question at all, and the Chilean "parto con volumen 500 cc" was
quoted back as unreadable.

The boundary matters more than the relief. A clause that names something
administrable is an order whatever else it says, and a titration is not a goal:
"bajar la nitroglicerina a 20 mcg/min" must still execute. Silence is the worse
failure of the two, and these tests exist to keep it from being the fix.
"""
import pytest

from family_parser import parse_family_actions


def types(text):
    return [action["type"] for action in parse_family_actions(text)["actions"]]


def held(text):
    return [action["message"] for action in parse_family_actions(text)["actions"]
            if action["type"] == "clarification"]


# --- reasoning is not an order ----------------------------------------------

@pytest.mark.parametrize("clause", [
    "quiero frenar la agregacion",
    "busco subir la presion",
    "apunto a PAM sobre 65",
    "la idea es que orine y baje la congestion",
    "the goal is to limit thrombus growth",
    "the aim is to unload the work of breathing",
    "my goal is to improve perfusion",
    "para subir la presion arterial",
    "to raise the MAP",
])
def test_a_stated_goal_is_not_quoted_back_as_an_unreadable_order(clause):
    assert parse_family_actions(clause)["actions"] == []


@pytest.mark.parametrize("clause", [
    "controlo PAM",
    "llene capilar",
    "control de PAM en 15 min",
    "reviso diuresis y saturacion",
    "vigilo la saturacion",
])
def test_what_will_be_watched_is_not_quoted_back_as_an_unreadable_order(clause):
    assert not held(clause), clause


def test_the_whole_submission_survives_its_own_reasoning():
    actions = types("Creo que es un SCA. Aspirina 300 mg VO, quiero frenar la agregacion, "
                    "reevaluo el dolor y el ECG en 10 minutos")
    assert "aspirin" in actions
    assert "clarification" not in actions


# --- an order announced rather than commanded -------------------------------

@pytest.mark.parametrize("text, expected", [
    ("Given the hypoxemia I will start NIV.", "niv"),
    ("Como esta hipotenso le voy a pasar 500 cc de suero fisiologico.", "fluid"),
    ("Voy a iniciar noradrenalina a 0.05 mcg/kg/min.", "norepinephrine"),
    ("Vamos a intubar al paciente.", "intubation"),
    ("Le voy a dar aspirina 300 mg.", "aspirin"),
    ("Shock septico, parto con volumen 500 cc.", "fluid"),
])
def test_a_declared_intention_is_an_order(text, expected):
    assert expected in types(text), text


def test_waiting_is_not_an_order():
    assert types("Voy a esperar 10 minutos.") == []


# --- the boundary -----------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    # A titration names a drug and a new setting: it executes.
    ("Bajar la nitroglicerina a 20 mcg/min.", "nitroglycerin"),
    ("Bajar la noradrenalina.", "norepinephrine"),
    ("Subir el oxigeno a 5 L/min.", "oxygen"),
])
def test_a_titration_is_not_read_as_a_goal(text, expected):
    assert expected in types(text), text


def test_an_administered_quantity_keeps_a_clause_an_order():
    # A dose is an order whatever else the clause says. Intramuscular adrenaline
    # was the example here until the anaphylaxis family made it executable on
    # 2026-09-23; it is now an order rather than a refusal, which is the point.
    assert types("IM adrenaline 0.5 mg") == ["epinephrine_im"]
    # The guard itself: a clause naming an administered quantity is an order
    # whatever else it says, so the goal reading can never reach it.
    from family_parser import _is_reasoning
    assert _is_reasoning("busco subir la presion")
    assert not _is_reasoning("busco subir la presion con 500 cc de suero")


def test_a_withheld_order_is_still_not_an_order():
    assert parse_family_actions("no le pases volumen")["actions"] == []
