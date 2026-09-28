"""A list of orders keeps every order; a repeat keeps its order running (DF-16a, DF-16b).

Faculty authorisation of cycle 4 (2026-09-28). Found in cycle 3 with sentences
written for the validation tooling:

* DF-16a: "Monitor, vía venosa y oxígeno por mascarilla a 8 L/min" ran only the
  line. The bare "monitor" was read as a verb with nothing to watch, lent that
  verb to the items after it (so the oxygen became a check of the saturation),
  and a listed "vía venosa" with no verb of its own was dropped; a route written
  once after a list of doses reached only the last one.
* DF-16b: "salbutamol ... nebulizados ahora, repetir cada 20 minutos ... si
  persiste el broncoespasmo" ran nothing: the repeat's condition made the whole
  sentence a plan, and the order was quoted back as the working model.

Every sentence here is written for these tests -- not from the rehearsal
corpus, not from the cycle 3 probes -- so that each test pins a class, not a
phrase (§57). Each class is checked in English and in Spanish.
"""
import pytest

from family_parser import parse_family_actions, repeat_structure
from test_curriculum_trajectories import load_engine


def actions(text):
    return parse_family_actions(text)["actions"]


def kinds(text):
    return [action["type"] for action in actions(text)]


def plans(text):
    return [(detail["kind"], detail["text"]) for detail in parse_family_actions(text)["future_details"]]


# --- DF-16a · every item of a set-up list is an order ----------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("Monitor, dos vías venosas gruesas y O2 por mascarilla con reservorio a 15 L/min",
     ["monitoring", "vascular_access", "oxygen"]),
    ("Monitorización continua + vía venosa + hemoglucotest", ["monitoring", "vascular_access", "diagnostic"]),
    ("Vía venosa, monitor y SF 1000 ml ev", ["vascular_access", "monitoring", "fluid"]),
    ("Monitor cardíaco; vía periférica; sonda Foley", ["monitoring", "vascular_access", "urinary_catheter"]),
    ("IV access, cardiac monitor and oxygen by nasal cannula at 4 L/min", ["vascular_access", "monitoring", "oxygen"]),
    ("Continuous monitoring, two large-bore IVs, then 500 mL normal saline IV",
     ["monitoring", "vascular_access", "fluid"]),
    ("Monitor + IV + NPO", ["monitoring", "vascular_access", "npo"]),
    ("NPO, IV access and a Foley catheter", ["npo", "vascular_access", "urinary_catheter"]),
])
def test_a_setup_list_keeps_every_item(text, expected):
    assert kinds(text) == expected


@pytest.mark.parametrize("text, device, flow", [
    ("Monitor, vía venosa y oxígeno por naricera a 3 L/min", "nasal cannula", 3.0),
    ("Monitor, IV access and oxygen via non-rebreather at 12 L/min", "non-rebreather mask", 12.0),
])
def test_oxygen_after_a_monitor_is_given_not_watched(text, device, flow):
    oxygen = next(action for action in actions(text) if action["type"] == "oxygen")
    assert (oxygen["device"], oxygen["flow_lpm"]) == (device, flow)


@pytest.mark.parametrize("text", ["Monitor", "Monitorización continua", "Cardiac monitoring", "Monitor cardíaco"])
def test_the_monitor_named_alone_is_the_monitor(text):
    assert actions(text) == [{"type": "monitoring", "operation": "start"}]


@pytest.mark.parametrize("text", ["Monitorizar la saturación de oxígeno cada 10 minutos",
                                  "Monitor the oxygen saturation every 10 minutes"])
def test_watching_the_saturation_is_still_a_reassessment(text):
    assert "oxygen" not in kinds(text) and "reassessment" in kinds(text)


@pytest.mark.parametrize("text", ["Vía venosa permeable, monitorizado", "Tiene una vía periférica funcionando",
                                  "The IV is patent and she is on the monitor", "Vía venosa"])
def test_a_line_the_patient_already_has_is_not_an_order(text):
    assert "vascular_access" not in kinds(text)


@pytest.mark.parametrize("text, route", [
    ("Salbutamol 2.5 mg + bromuro de ipratropio 250 mcg nebulizados", "nebulized"),
    ("Albuterol 2.5 mg and ipratropium 500 mcg neb", "nebulized"),
    ("Ketorolaco 30 mg y paracetamol 1 g endovenosos", "IV"),
    ("Ketorolac 30 mg and acetaminophen 1 g IV", "IV"),
])
def test_a_route_written_after_a_list_of_doses_reaches_each_dose(text, route):
    doses = [action for action in actions(text) if action.get("agent")]
    assert len(doses) == 2 and all(action["route"] == route for action in doses)


def test_a_shared_route_also_crosses_a_medicine_the_simulator_does_not_model():
    [fentanyl] = actions("Fentanyl 50 mcg and ondansetron 4 mg IV")
    assert fentanyl["route"] == "IV"
    assert plans("Fentanyl 50 mcg and ondansetron 4 mg IV") == [("not_modelled", "ondansetron 4 mg iv")]


@pytest.mark.parametrize("text, routes", [
    # Each dose with its own route keeps it.
    ("Paracetamol 1 g vo y ketorolaco 30 mg ev", ["PO", "IV"]),
    # A sequence is not a list: the route written after "luego" is the second dose's.
    ("Salbutamol 5 mg, luego ipratropio 0.5 mg nbz", [None, "nebulized"]),
    # Nothing written, nothing invented.
    ("Paracetamol 1 g y ketorolaco 30 mg", [None, None]),
])
def test_no_route_is_invented(text, routes):
    assert [action.get("route") for action in actions(text)] == routes


# --- DF-16b · the order runs; the repeat keeps its interval, count and condition -------------

@pytest.mark.parametrize("text, runs, structure", [
    ("Adrenalina 0.5 mg IM; repetir cada 5 minutos si no hay respuesta", "epinephrine_im",
     {"every_min": 5.0, "condition": "si no hay respuesta"}),
    ("Morfina 3 mg ev, repetir en 10 minutos si el dolor sigue sobre 6", "opioid_analgesia",
     {"after_min": 10.0, "condition": "si el dolor sigue sobre 6"}),
    ("Nebulizo salbutamol 5 mg y repetir cada 20 minutos hasta 3 veces si persisten las sibilancias",
     "bronchodilator", {"every_min": 20.0, "count": 3, "condition": "si persisten las sibilancias"}),
    ("Albuterol 2.5 mg nebulized, repeat every 20 minutes x3 if still wheezing", "bronchodilator",
     {"every_min": 20.0, "count": 3, "condition": "if still wheezing"}),
    ("Fentanyl 25 mcg IV now; may repeat every 5 minutes until comfortable", "opioid_analgesia",
     {"every_min": 5.0, "condition": "until comfortable"}),
    ("Give epinephrine 0.5 mg IM, repeat once in 5 minutes if hypotension persists", "epinephrine_im",
     {"after_min": 5.0, "count": 1, "condition": "if hypotension persists"}),
])
def test_the_order_runs_and_the_repeat_is_its_plan(text, runs, structure):
    parsed = parse_family_actions(text)
    assert [action["type"] for action in parsed["actions"]] == [runs]
    [repeat] = [detail for detail in parsed["future_details"] if detail["kind"] == "repeat"]
    assert {key: repeat[key] for key in structure} == structure
    assert repeat["of"]
    # The condition is the repeat's: nothing about the order itself is conditional.
    assert all(detail["kind"] != "conditional" for detail in parsed["future_details"])


def test_an_order_written_after_the_repeat_is_an_order_of_its_own():
    parsed = parse_family_actions("Salbutamol 5 mg nbz, repetir en 20 minutos si persiste, e hidrocortisona 200 mg ev")
    assert [action["type"] for action in parsed["actions"]] == ["bronchodilator", "steroid"]
    assert plans("Salbutamol 5 mg nbz, repetir en 20 minutos si persiste, e hidrocortisona 200 mg ev") == [
        ("repeat", "repetir en 20 minutos si persiste")]


@pytest.mark.parametrize("text, condition", [
    ("Si no mejora, repetir adrenalina 0.5 mg im a los 5 minutos", "si no mejora"),
    ("If there is no response, repeat the epinephrine 0.5 mg IM in 5 minutes", "if there is no response"),
])
def test_a_repeat_that_waits_on_a_condition_is_a_plan_and_runs_nothing(text, condition):
    parsed = parse_family_actions(text)
    assert parsed["actions"] == []
    [repeat] = parsed["future_details"]
    assert repeat["kind"] == "repeat" and repeat["condition"] == condition and repeat["after_min"] == 5.0


@pytest.mark.parametrize("text, runs, plan", [
    # Chart shorthand, no verb: the condition is the second order's, not the first's.
    ("Paracetamol 1 g ev y ondansetrón 4 mg ev si vomita", ["antipyretic"], "ondansetron 4 mg ev si vomita"),
    ("NS 1 L IV and norepinephrine if still hypotensive", ["fluid"], "norepinephrine if still hypotensive"),
])
def test_a_condition_after_a_verbless_order_does_not_hold_that_order(text, runs, plan):
    assert kinds(text) == runs
    assert plans(text) == [("conditional", plan)]


@pytest.mark.parametrize("text", ["Repito adrenalina 0.5 mg im", "Repeat the epinephrine 0.5 mg IM"])
def test_a_repeat_with_no_interval_or_condition_is_given_again_now(text):
    assert kinds(text) == ["repeat_order"]


def test_volver_a_with_an_administration_verb_repeats_it():
    assert plans("Doy ondansetrón 4 mg ev y volver a administrar si vomita")[-1] == (
        "repeat", "volver a administrar si vomita")
    # Coming back is still coming back.
    assert plans("Alta y volver a consultar si fiebre") == [("advice", "volver a consultar si fiebre")]


@pytest.mark.parametrize("clause, expected", [
    ("repetir por 3 veces", {"count": 3}),
    ("nebulizar por 20 minutos", {}),
    ("repeat twice every 15 minutes", {"every_min": 15.0, "count": 2}),
    ("repetir en 2 horas si persiste", {"after_min": 120.0, "condition": "si persiste"}),
])
def test_the_structure_of_a_repeat(clause, expected):
    assert repeat_structure(clause) == expected


# --- written after the fix and run once before being kept here (held-out check, 2026-09-28) ---

@pytest.mark.parametrize("text, expected", [
    ("Sonda nasogástrica, régimen cero y vía venosa", ["gastric_tube", "npo", "vascular_access"]),
    ("Vía venosa + régimen cero + ondansetrón 8 mg ev", ["vascular_access", "npo"]),
    ("Oxygen via non-rebreather at 15 L/min; monitor; two large-bore IVs",
     ["oxygen", "monitoring", "vascular_access"]),
    ("Cardiac monitor, two IVs and 1 L lactated Ringer's IV over 30 minutes",
     ["monitoring", "vascular_access", "fluid"]),
])
def test_held_out_lists(text, expected):
    assert kinds(text) == expected


@pytest.mark.parametrize("text, runs, structure", [
    ("Adrenalina 0.3 mg im y repetir a los 5 minutos si persiste el estridor", ["epinephrine_im"],
     {"after_min": 5.0, "condition": "si persiste el estridor"}),
    ("Morfina 2 mg ev; si el dolor persiste, repetir en 10 minutos", ["opioid_analgesia"],
     {"after_min": 10.0, "condition": "si el dolor persiste"}),
    ("Ketamine 20 mg IV, repeat in 10 minutes if pain persists", ["procedural_sedation"],
     {"after_min": 10.0, "condition": "if pain persists"}),
    ("Ondansetron 4 mg IV; can be repeated after 30 minutes if nausea continues", [],
     {"after_min": 30.0, "condition": "if nausea continues"}),
])
def test_held_out_repeats(text, runs, structure):
    parsed = parse_family_actions(text)
    assert [action["type"] for action in parsed["actions"]] == runs
    [repeat] = [detail for detail in parsed["future_details"] if detail["kind"] == "repeat"]
    assert {key: repeat[key] for key in structure} == structure


# --- the Management Trace keeps the structure and never takes an order for the model ---------

@pytest.fixture(scope="module")
def extract():
    return load_engine()["extract_explicit_reasoning"]


@pytest.mark.parametrize("text, model", [
    ("Salbutamol 2.5 mg nbz, repetir cada 20 minutos si persiste el broncoespasmo", None),
    ("Albuterol 2.5 mg nebulized now, repeat every 20 minutes if the wheeze persists", None),
    ("Si persiste la hipotensión, repetir adrenalina 0.5 mg im a los 5 minutos", None),
    # A stated appraisal stays the model, up to where the order begins.
    ("Persiste la hipotensión, adrenalina 0.5 mg im y repetir en 5 minutos si no mejora", "Persiste la hipotensión"),
])
def test_neither_the_order_nor_its_repeat_is_the_working_model(extract, text, model):
    assert extract(text).get("problem_representation") == model


def test_the_page_says_what_a_repeat_is_in_both_languages():
    import language
    import unexecuted_items
    parsed = parse_family_actions("Morfina 3 mg ev, repetir en 10 minutos si el dolor sigue sobre 6")
    said, unclassified = unexecuted_items.messages(parsed)
    assert said == ["Recorded as a repeat instruction, not executed now: repetir en 10 minutos si el dolor sigue "
                    "sobre 6."] and unclassified == []
    assert language.say(said[0], "es") == ("Registrado como instrucción de repetición, no ejecutada ahora: "
                                          "«repetir en 10 minutos si el dolor sigue sobre 6».")
    assert unexecuted_items.trace_labels(parsed) == [("repetir en 10 minutos si el dolor sigue sobre 6",
                                                      "repeat instruction; not executed now")]


def test_input_execution_and_trace_through_the_real_page(tmp_path, monkeypatch):
    """The two classes played by app.py, read back from the stored Management Trace."""
    import tools_order_reading
    import tools_tanda20
    # Through monkeypatch, so the offline mode ends with this test: set on
    # os.environ it reached every later file of the run (C-2026-09-26-20).
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    first = "Monitor, vía venosa periférica y O2 por naricera a 4 L/min"
    second = "Salbutamol 2.5 mg + bromuro de ipratropio 250 mcg nbz, repetir cada 20 minutos si persiste el broncoespasmo"
    script = {"number": 1, "case_id": "asthma_24f", "family": "asthma", "category": "test", "challenge": "R3-01",
              "intent": "DF-16", "language": "es", "steps": [("order", first), ("order", second)],
              "resolve_until_clear": True, "reflection": {}, "plan": {},
              "comparison": {"alignment": "-", "adjustment": "-"}}
    result = tools_tanda20.rehearse(script, tmp_path, seed=3000)
    assert result["stopped"] is None
    stored = tools_order_reading.stored_encounter(tmp_path / "rehearsal-01.sqlite3")
    assert stored["ai_calls_spent"] in (0, None)
    [setup] = [entry for entry in stored["trace"] if entry["input"].startswith(first)]
    assert setup["status"] == "executed"
    ran = {dict(map(tuple, signature))["type"] for signature in setup["actions"]}
    assert {"monitoring", "vascular_access", "oxygen"} <= ran
    [nebulized] = [entry for entry in stored["trace"] if entry["input"].startswith(second[:20])]
    assert nebulized["status"] == "executed"
    agents = {dict(map(tuple, signature)).get("agent") for signature in nebulized["actions"]}
    assert {"albuterol", "ipratropium"} <= agents
    assert "repeat/None" in nebulized["future_details"]
    # Whatever the trace records as stated, it is not the order.
    assert "salbutamol" not in str(nebulized["slots"].get("problem_representation", "")).lower()
