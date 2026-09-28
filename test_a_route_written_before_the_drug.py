"""A route written before the drug belongs to that drug (KD-01, faculty 2026-09-28).

Found by the held-out check of cycle 4: an English order with no verb that puts the
route first -- "IV morphine 4 mg", "Oral paracetamol 1 g", "Nebulized albuterol
2.5 mg" -- was quoted back as unrecognised, and the other orders of the submission
were held with it. The class: a route word the reader already knows, then a medicine
it knows, then the dose. The route is stepped over to find the order and read where
it was written, so the order is exactly the one written drug first. It is that drug's
route: in a list it never reaches the dose before it, which kept an IV written for the
morphine as the aspirin's route too (the same misreading, in a list).

Every sentence here is written for these tests, and every case is checked against
the same order written drug first, in English and in Spanish.
"""
import re

import pytest

from family_parser import parse_family_actions
from shared_order_language import ROUTE_BEFORE_THE_DRUG, _route
from test_curriculum_trajectories import load_engine


def actions(text):
    return parse_family_actions(text)["actions"]


def read(text):
    return [(a.get("type"), a.get("agent"), a.get("dose_mg"), a.get("route")) for a in actions(text)]


# --- the class: route, medicine, dose -------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("IV morphine 4 mg", ("opioid_analgesia", "morphine", 4.0, "IV")),
    ("IM epinephrine 0.5 mg", ("epinephrine_im", None, 0.5, "IM")),
    ("PO acetaminophen 1 g", ("antipyretic", "paracetamol", 1000.0, "PO")),
    ("IV ceftriaxone 2 g", ("antibiotics", "ceftriaxone", 2000.0, "IV")),
    ("Oral paracetamol 1 g", ("antipyretic", "paracetamol", 1000.0, "PO")),
    ("Intravenous morphine 4 mg", ("opioid_analgesia", "morphine", 4.0, "IV")),
    ("Nebulized albuterol 2.5 mg", ("bronchodilator", "albuterol", 2.5, "nebulized")),
    ("Inhaled salbutamol 5 mg", ("bronchodilator", "albuterol", 5.0, "inhaled")),
    ("IV furosemide 40 mg", ("diuretic", "furosemide", 40.0, "IV")),
    ("IV naloxone 0.4 mg", ("naloxone", "naloxone", 0.4, "IV")),
    ("EV morfina 4 mg", ("opioid_analgesia", "morphine", 4.0, "IV")),
    ("VO paracetamol 1 g", ("antipyretic", "paracetamol", 1000.0, "PO")),
    ("NBZ salbutamol 2.5 mg", ("bronchodilator", "albuterol", 2.5, "nebulized")),
])
def test_the_route_before_the_drug_is_read_as_that_drug_s_route(text, expected):
    assert read(text) == [expected]


@pytest.mark.parametrize("route_first, drug_first", [
    ("IV morphine 4 mg", "morphine 4 mg IV"),
    ("PO acetaminophen 1 g", "acetaminophen 1 g PO"),
    ("IV ceftriaxone 2 g", "ceftriaxone 2 g IV"),
    ("Nebulized albuterol 2.5 mg", "albuterol 2.5 mg nebulized"),
    ("IM epinephrine 0.5 mg", "epinephrine 0.5 mg IM"),
    ("EV morfina 4 mg", "Morfina 4 mg ev"),
    # Without a dose it is not an order either way: no dose is invented (KD-02 stays).
    ("IV morphine", "morphine IV"),
    ("Oral paracetamol", "paracetamol PO"),
    ("EV morfina", "morfina ev"),
    # A repeat that waits on a condition is a plan either way (DF-16b).
    ("IV morphine 4 mg every 10 minutes if pain persists", "Morphine 4 mg IV every 10 minutes if pain persists"),
])
def test_it_is_the_same_order_as_the_drug_written_first(route_first, drug_first):
    first, second = parse_family_actions(route_first), parse_family_actions(drug_first)
    assert first["actions"] == second["actions"]
    assert [d["kind"] for d in first["future_details"]] == [d["kind"] for d in second["future_details"]]


def test_no_dose_is_invented():
    for text in ("IV morphine", "Oral paracetamol", "Nebulized albuterol", "EV morfina"):
        assert actions(text) == []
    assert read("IV morphine 4 mg") == [("opioid_analgesia", "morphine", 4.0, "IV")]


# --- only routes the reader knows; nothing else becomes a route ----------------------------

EXAMPLES = ("iv", "ev", "intravenous", "intravenoso", "endovenosa", "io", "intraosseous", "intraosea", "im",
            "intramuscular", "po", "vo", "oral", "orales", "sc", "sq", "subcutaneous", "subcutanea", "intranasal",
            "nebulized", "nebulised", "nebulizado", "neb", "nbz", "nebu", "inhaled", "inhalado")


def test_every_word_that_opens_the_order_is_a_route_the_reader_already_knows():
    alternatives = ROUTE_BEFORE_THE_DRUG[len("(?:"):-1].split("|")
    for alternative in alternatives:
        words = [word for word in EXAMPLES if re.fullmatch(alternative, word)]
        assert words, alternative
        assert all(_route(word) for word in words), alternative
    # "in" is a preposition before it is the nasal route: never stepped over.
    for word in ("in", "on", "via", "per", "by"):
        assert not re.fullmatch(ROUTE_BEFORE_THE_DRUG, word), word


@pytest.mark.parametrize("text", [
    "Oral intake is poor", "IV access now", "Neb treatments helped before", "IM injection site is clean",
    "Oral paracetamol 1 g was given at home",
])
def test_a_route_word_that_opens_no_order_gives_nothing(text):
    assert not [a for a in actions(text) if a.get("agent") or a.get("dose_mg") is not None]


def test_in_the_meantime_opens_an_order_with_its_own_route_never_the_nasal_one():
    # "In" there is a preposition, never the nasal route, as before. Since cycle 8 "in the
    # meantime" opens the order it precedes, which is read with the route written after it;
    # it used to be read as nothing (post hoc, blind set of cycle 8).
    assert read("In the meantime paracetamol 1 g PO") == [("antipyretic", "paracetamol", 1000.0, "PO")]


def test_the_nasal_route_is_still_read_only_after_the_dose():
    assert read("naloxone 2 mg IN") == [("naloxone", "naloxone", 2.0, "IN")]
    # Written first it is not read as a route, and nothing runs in its place.
    assert all(a["type"] == "clarification" for a in actions("IN naloxone 2 mg"))


def test_two_routes_for_one_drug_choose_neither():
    assert read("IV morphine 4 mg PO") == [("opioid_analgesia", "morphine", 4.0, None)]


def test_two_medicines_after_one_route_still_ask_to_be_separated():
    [held] = actions("IV morphine 4 mg ketorolac 30 mg")
    assert held["type"] == "clarification" and "Separate each medication" in held["message"]


# --- the route belongs to its own drug in a list --------------------------------------------

@pytest.mark.parametrize("text, routes", [
    ("IV morphine 4 mg, aspirin 300 mg", {"morphine": "IV", "aspirin": None}),
    ("IV morphine 4 mg and paracetamol 1 g", {"morphine": "IV", "paracetamol": None}),
    ("Nebulized albuterol 2.5 mg and aspirin 300 mg", {"albuterol": "nebulized", "aspirin": None}),
    # Written before the morphine, the IV is not a route written after the aspirin.
    ("Aspirin 300 mg, IV morphine 4 mg", {"aspirin": None, "morphine": "IV"}),
    ("Aspirin 300 mg + IV morphine 4 mg", {"aspirin": None, "morphine": "IV"}),
    ("Aspirina 300 mg, EV morfina 4 mg", {"aspirin": None, "morphine": "IV"}),
    ("Oral aspirin 300 mg then IV morphine 4 mg", {"aspirin": "PO", "morphine": "IV"}),
    # The line's route is not the next drug's.
    ("IV access, morphine 4 mg", {"morphine": None}),
])
def test_the_route_before_a_drug_reaches_no_other_order(text, routes):
    assert {a["agent"]: a.get("route") for a in actions(text) if a.get("agent")} == routes


@pytest.mark.parametrize("text, route", [
    ("Morphine 4 mg and ketorolac 30 mg IV", "IV"),
    ("Paracetamol 1 g y ketorolaco 30 mg endovenosos", "IV"),
    ("Salbutamol 5 mg + ipratropio 0.5 mg nbz", "nebulized"),
])
def test_a_route_written_after_the_list_still_reaches_each_dose(text, route):
    assert {a.get("route") for a in actions(text) if a.get("agent")} == {route}


# --- executed by the engine and recorded as written -----------------------------------------

@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("family, case_id, text, label", [
    ("renal_colic", "renal_colic_34m", "IV morphine 4 mg", "morphine 4 mg IV administered"),
    ("pneumonia", "pneumonia_46f", "IV ceftriaxone 2 g", "ceftriaxone 2000 mg IV administered"),
    ("pneumonia", "pneumonia_46f", "PO acetaminophen 1 g", "paracetamol 1000 mg PO administered"),
    ("asthma", "asthma_24f", "Nebulized albuterol 2.5 mg", "albuterol 2.5 mg nebulized"),
    ("anaphylaxis", "anaphylaxis_29f", "IM epinephrine 0.5 mg", "Epinephrine 0.5 mg IM administered"),
])
def test_the_order_runs_on_the_engine(engine, family, case_id, text, label):
    from family_engine import execute_family_bundle
    from test_cognitive_encounters import encounter
    state = encounter(engine, family, case_id)["state"]
    result = execute_family_bundle(state, parse_family_actions(text))
    assert result["executed"], result["clarification"]
    assert [summary.get("label") for summary in result["action_summaries"]] == [label]


def test_a_dose_left_without_its_route_is_asked_for_not_given_by_another(engine):
    from family_engine import execute_family_bundle
    from test_cognitive_encounters import encounter
    state = encounter(engine, "acs", "acs_54m_inferior")["state"]
    result = execute_family_bundle(state, parse_family_actions("Aspirin 300 mg, IV morphine 4 mg"))
    assert not result["executed"] and "route for aspirin" in result["clarification"]


def test_the_order_is_not_the_working_model(engine):
    extract = engine["extract_explicit_reasoning"]
    for text in ("IV morphine 4 mg", "Nebulized albuterol 2.5 mg", "EV morfina 4 mg"):
        assert extract(text).get("problem_representation") is None


def test_input_execution_and_trace_through_the_real_page(tmp_path, monkeypatch):
    """Played by app.py in English, read back from the stored Management Trace."""
    import tools_order_reading
    import tools_tanda20
    # Through monkeypatch, so the offline mode ends with this test (C-2026-09-26-20).
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    first = "IV ceftriaxone 2 g"
    second = "PO acetaminophen 1 g and nebulized albuterol 2.5 mg"
    script = {"number": 1, "case_id": "pneumonia_46f", "family": "pneumonia", "category": "test",
              "challenge": "R1-05", "intent": "KD-01", "language": "en",
              "steps": [("order", first), ("order", second)], "resolve_until_clear": True,
              "reflection": {}, "plan": {}, "comparison": {"alignment": "-", "adjustment": "-"}}
    result = tools_tanda20.rehearse(script, tmp_path, seed=3000)
    assert result["stopped"] is None
    stored = tools_order_reading.stored_encounter(tmp_path / "rehearsal-01.sqlite3")
    assert stored["ai_calls_spent"] in (0, None)

    def routes(entry):
        # The page adds its guided reassessment to the turn; only the medicines matter here.
        return {dict(map(tuple, signature)).get("agent"): dict(map(tuple, signature)).get("route")
                for signature in entry["actions"] if dict(map(tuple, signature)).get("agent")}

    [antibiotic] = [entry for entry in stored["trace"] if entry["input"].startswith(first)]
    assert antibiotic["status"] == "executed" and routes(antibiotic) == {"ceftriaxone": "IV"}
    [pair] = [entry for entry in stored["trace"] if entry["input"].startswith(second[:20])]
    assert pair["status"] == "executed" and routes(pair) == {"paracetamol": "PO", "albuterol": "nebulized"}
