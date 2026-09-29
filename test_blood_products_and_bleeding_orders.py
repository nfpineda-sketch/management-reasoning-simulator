"""Blood products, the massive transfusion protocol, bleeding measures, the intraosseous line
and a pregnancy test, read and recorded as the resident wrote them (cycle 7, 2026-09-28).

Faculty decisions TD-26, TD-22 and C7-06 (Decision File, opening of cycle 7; charter A2,
§111-§114):

* red cells run in the units the resident wrote, however they are written ("2 U GR O
  negativo", "O-neg", "packed cells", "uncrossmatched"); "gr" after a dose is still a gram;
* plasma, platelets, cryoprecipitate and whole blood are recorded as ordered, with their
  physiologic effect not modelled; they never become red cells, and nothing says the
  resident did not give them;
* the massive transfusion protocol's activation is recorded and gives no product by itself:
  no unit or ratio is invented, and a transfusion with nothing named is asked about;
* each bleeding measure is its own order and none becomes another;
* an intraosseous line is its own access, never written back as an intravenous one;
* a pregnancy test is recorded as requested, with no result invented, and holds nothing;
* none of it runs when it is the prehospital team's account, a plan, a negation or a result.
"""
import pytest

import language
import report_language
import rubric_screening
import unexecuted_items
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


def read(text):
    return parse_family_actions(text)["actions"]


def kinds(text):
    return [action["type"] for action in read(text)]


def recorded(text):
    return [(detail["kind"], detail.get("category")) for detail in parse_family_actions(text)["future_details"]]


# --- A. red cells: executed in the units written ----------------------------------------

@pytest.mark.parametrize("text, units", [
    ("Transfundir 2 U de GR O negativo", 2), ("2 UGR ahora", 2), ("Transfuse 2 units O-neg", 2),
    ("Give two units of uncrossmatched blood", 2), ("Transfuse 1 unit packed cells", 1),
    ("2 units emergency-release O negative red cells now", 2), ("Transfundo 1 concentrado eritrocitario", 1),
    ("Pasar dos unidades de glóbulos rojos", 2), ("Hang 2 units of O-negative through the Level 1", 2),
    ("Transfundir 2 unidades de sangre O Rh negativo sin cruzar", 2),
])
def test_red_cells_are_run_in_the_units_written(text, units):
    assert read(text) == [{"type": "blood", "units": float(units)}]


def test_red_cells_beside_another_order_are_no_longer_lost_without_a_word():
    # Cycle 6 blind sets: the red cells vanished and only the proton pump inhibitor ran.
    assert kinds("PA 78/40, FC 128: 2 VVP 16G, 2 U de GR O negativo y omeprazol 80 mg ev") == [
        "vascular_access", "blood", "ppi"]


@pytest.mark.parametrize("text", ["Paracetamol 1 gr ev", "Ceftriaxona 2 gr ev", "2 gr/día de paracetamol"])
def test_gr_after_a_dose_is_a_gram_never_red_cells(text):
    assert "blood" not in kinds(text)


def test_the_count_written_after_a_transfusion_is_its_count_not_a_second_one():
    assert read("Stop the saline and go to blood, 2 units of O-neg")[1:] == [{"type": "blood", "units": 2.0}]
    assert read("Transfundir GR, 2 unidades") == [{"type": "blood", "units": 2.0}]


# --- B. products the engine does not model: recorded, never red cells --------------------

@pytest.mark.parametrize("text", [
    "Transfuse 2 units FFP", "Plasma fresco congelado 2 unidades", "Transfuse 1 unit of platelets",
    "1 aféresis de plaquetas", "Crioprecipitado 10 unidades", "Give 10 units cryo",
    "Transfuse 1 unit low-titer O whole blood", "Sangre total 1 unidad",
])
def test_an_unmodelled_product_is_recorded_as_ordered_and_never_becomes_red_cells(text):
    parsed = parse_family_actions(text)
    assert parsed["actions"] == []
    assert recorded(text) == [("not_modelled", "blood_product")]
    assert parsed["future_details"][0]["prescription"] is False


@pytest.mark.parametrize("text, blood, products", [
    ("Transfuse 2 units PRBC and 2 units FFP", 2, 1),
    ("2 U GR + 2 U PFC + 1 aféresis de plaquetas", 2, 2),
    ("Transfundir 2 U de GR con 2 U de PFC", 2, 1),
])
def test_red_cells_and_other_products_in_one_order_each_keep_what_they_are(text, blood, products):
    assert read(text) == [{"type": "blood", "units": float(blood)}]
    assert recorded(text) == [("not_modelled", "blood_product")] * products


def test_a_count_shared_by_two_products_is_asked_about():
    [action] = read("Transfundir GR/PFC 2 U c/u")
    assert action["type"] == "clarification" and "own number of units" in action["message"]


@pytest.mark.parametrize("text", ["Give blood products", "Transfundir hemoderivados", "Transfuse"])
def test_a_transfusion_that_names_no_product_is_asked_about(text):
    [action] = read(text)
    assert action["type"] == "clarification" and "which blood product" in action["message"]


# --- C. the massive transfusion protocol --------------------------------------------------

@pytest.mark.parametrize("text", [
    "Activate massive transfusion protocol", "Activar protocolo de transfusión masiva.",
    "Activo el protocolo de transfusión masiva", "Activate MTP 1:1:1",
])
def test_the_protocol_s_activation_is_recorded_and_gives_nothing_by_itself(text):
    assert read(text) == []
    assert recorded(text) == [("not_modelled", "massive_transfusion")]


def test_the_other_orders_run_beside_the_activation():
    assert kinds("Activo transfusión masiva y paso ácido tranexámico 1 g ev en 10 min") == ["tranexamic_acid"]
    assert recorded("Activo transfusión masiva y paso ácido tranexámico 1 g ev en 10 min") == [
        ("not_modelled", "massive_transfusion")]


def test_the_units_given_are_only_the_ones_written():
    assert read("Activate MTP and transfuse 2 units PRBC") == [{"type": "blood", "units": 2.0}]
    assert read("Activar protocolo de transfusión masiva con 2 U GR O negativo") == [
        {"type": "blood", "units": 2.0}]
    [question] = read("Activate MTP and transfuse")
    assert question["type"] == "clarification"


@pytest.mark.parametrize("text", [
    "This patient may need massive transfusion", "Consider MTP",
    "Una nueva caida de presion me habria hecho activar transfusion masiva.",
])
def test_reasoning_about_the_protocol_is_not_its_activation(text):
    assert read(text) == [] and recorded(text) == []


def test_a_conditional_activation_is_kept_as_a_plan():
    assert recorded("If he keeps bleeding, activate the massive transfusion protocol") == [("conditional", None)]


# --- negative controls: history, plans, negations, results, reservations ------------------

@pytest.mark.parametrize("text", [
    "The medic gave 1 unit of blood en route", "EMS gave 1 unit of plasma", "Plaquetas 45.000",
    "Plasma glucose 60 mg/dL", "No transfundir plasma por ahora", "Paciente O negativo",
    "Blood pressure every 5 minutes", "Reservar 2 unidades de plasma",
])
def test_what_is_not_the_resident_s_order_now_gives_and_records_nothing(text):
    assert not {"blood"} & set(kinds(text))
    assert all(category not in {"blood_product", "massive_transfusion"} for _, category in recorded(text))


@pytest.mark.parametrize("text", ["Reservar 2 unidades de GR", "Pido grupo y pruebas cruzadas", "Crossmatch 4 units",
                                  "2 VVP gruesas, grupo y pruebas cruzadas por 4 U de GR"])
def test_a_reservation_is_a_crossmatch_never_a_transfusion(text):
    assert "crossmatch" in [action.get("diagnostic") for action in read(text)]
    assert "blood" not in kinds(text)


@pytest.mark.parametrize("text", ["Cruzar 4 U de GR", "Tener 4 U de GR disponibles", "Hold 2 units of PRBC"])
def test_units_asked_to_be_ready_are_asked_about_never_given(text):
    [action] = read(text)
    assert action["type"] == "clarification" and "crossmatch" in action["message"]


def test_a_plan_to_give_plasma_is_a_plan():
    assert recorded("If INR > 2, give FFP") == [("conditional", None)]


# --- hemorrhage control: each measure its own, none another --------------------------------

@pytest.mark.parametrize("text, measures", [
    ("Pack the wound and hold pressure", ["packing", "direct pressure"]),
    ("Hold firm pressure on the wound", ["direct pressure"]),
    ("Empaquetar la herida y comprimir", ["packing", "direct pressure"]),
    ("Presión directa sobre la herida", ["direct pressure"]),
    ("Direct pressure with packing", ["direct pressure", "packing"]),
    ("Packing con gasa hemostática", ["packing"]),
    ("Tourniquet high on the right thigh", ["tourniquet"]),
])
def test_each_bleeding_measure_is_its_own_order(text, measures):
    actions = read(text)
    assert [action["type"] for action in actions] == ["hemorrhage_control"] * len(measures)
    assert [action["measure"] for action in actions] == measures


@pytest.mark.parametrize("text, named", [("Apply a pressure dressing", "pressure dressing"),
                                         ("Apósito hemostático en la herida", "hemostatic dressing")])
def test_a_dressing_keeps_its_own_name(text, named):
    [action] = read(text)
    assert (action["measure"], action["named"]) == ("direct pressure", named)


def test_a_measure_named_by_none_is_asked_about_and_never_chosen():
    [action] = read("Control de hemorragia")
    assert action["type"] == "hemorrhage_control" and action["measure"] is None


@pytest.mark.parametrize("text", ["Descartar taponamiento cardíaco con POCUS", "Hold pressure support at 10",
                                  "Endoscopía urgente para control del sangrado"])
def test_what_only_sounds_like_a_bleeding_measure_is_not_one(text):
    assert "hemorrhage_control" not in kinds(text)


# --- the intraosseous line -----------------------------------------------------------------

@pytest.mark.parametrize("text, site", [
    ("humeral IO", "humeral"), ("Place a tibial IO", "tibial"), ("Vía intraósea humeral", "humeral"),
    ("Coloco una vía intraósea", None), ("Acceso intraóseo en tibia proximal", "tibial"),
    ("EZ-IO in the right humerus", "humeral"), ("Get IO access", None),
])
def test_an_intraosseous_line_is_its_own_access(text, site):
    [action] = read(text)
    assert (action["type"], action["access"], action.get("site")) == ("vascular_access", "intraosseous", site)


def test_io_after_a_dose_is_that_dose_s_route_never_a_line():
    assert "vascular_access" not in kinds("Ceftriaxona 2 g, IO")
    assert read("Dextrosa 25 g IO")[0]["route"] == "IO"


def test_the_whole_hemorrhage_bundle_keeps_every_order():
    # Cycle 6 blind set: only the tranexamic acid ran; the rest was lost without a word.
    assert kinds("Pack the wound and hold pressure, humeral IO, TXA 1 g IV over 10 min") == [
        "hemorrhage_control", "hemorrhage_control", "vascular_access", "tranexamic_acid"]


# --- the pregnancy test (TD-22) ---------------------------------------------------------------

@pytest.mark.parametrize("text, studies", [
    ("Order a pregnancy test and a CT pulmonary angiogram.", ["pregnancy_test", "ctpa"]),
    ("Pide una prueba de embarazo.", ["pregnancy_test"]),
    ("β-hCG cuantitativa, dímero D y angioTAC", ["pregnancy_test", "d_dimer", "ctpa"]),
    ("UPT and D-dimer", ["pregnancy_test", "d_dimer"]),
])
def test_a_pregnancy_test_is_a_study_request(text, studies):
    assert [action.get("diagnostic") for action in read(text)] == studies


@pytest.mark.parametrize("text", ["β-hCG negativa", "Test de embarazo negativo, pido angioTAC"])
def test_a_pregnancy_result_the_resident_reads_is_not_a_request(text):
    assert "pregnancy_test" not in [action.get("diagnostic") for action in read(text)]


# --- the engine and the record --------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(engine, family, case, text):
    state = encounter(engine, family, case)["state"]
    before = state["sim_time"]
    result = execute_family_bundle(state, parse_family_actions(text))
    return state, before, result


def labels(result):
    return [str(summary.get("label") or "") for summary in result["action_summaries"]]


def test_a_pregnancy_test_holds_nothing_and_no_result_is_invented(engine):
    state, _, result = run(engine, "pulmonary_embolism", "pulmonary_embolism_33f",
                           "Order a pregnancy test and a CT pulmonary angiogram.")
    assert result["executed"], result["clarification"]
    [pregnancy] = [s for s in result["action_summaries"] if s.get("diagnostic") == "pregnancy_test"]
    assert pregnancy["not_performed"] == "not_modeled" and "none is invented" in pregnancy["label"]
    assert "pregnancy" not in str(state.get("results") or "").lower()


def test_red_cells_run_and_plasma_is_recorded_beside_them(engine):
    state, _, result = run(engine, "trauma", "trauma_hemothorax_41m", "Transfuse 2 units PRBC and 2 units FFP")
    assert result["executed"]
    assert "Packed red cells 2 units started" in labels(result)
    assert state["family_state"]["pending_blood_units"] + state["family_state"]["blood_delivered_units"] == 2


@pytest.mark.parametrize("text", ["Transfuse 2 units FFP", "Activate the massive transfusion protocol"])
def test_an_order_of_only_what_is_recorded_is_the_resident_s_decision_and_takes_no_minute(engine, text):
    state, before, result = run(engine, "trauma", "trauma_hemothorax_41m", text)
    assert result["executed"] and result.get("recorded_only") and result["clarification"] is None
    assert result["action_summaries"] == [] and state["sim_time"] == before


def test_the_intraosseous_line_is_recorded_as_one_and_changes_nothing_else(engine):
    state, _, result = run(engine, "trauma", "trauma_limb_hemorrhage_27m", "humeral IO")
    assert result["executed"]
    assert "intraosseous access (humeral) placed" in labels(result)
    assert not any("peripheral intravenous" in label for label in labels(result))
    assert state["family_state"]["io_access"] is True


def test_the_intraosseous_line_is_its_own_access_and_repairs_nothing(engine):
    import glucose_rescue
    from family_engine import _case, _initialize
    state = encounter(engine, "hypoglycemia", "hypoglycemia_28m")["state"]
    # The failed-line configuration (hypoglycemia catalog, N4): the forearm line does not run.
    _case(state).setdefault("engine", {})["iv_access_failed"] = True
    state.pop("family_state", None)
    _initialize(state)
    assert state["family_state"]["iv_access_failed"] is True
    result = execute_family_bundle(state, parse_family_actions("Coloco una vía intraósea"))
    # DC3 (2026-09-29): the needle is an access of its own; the cannula stays as it was.
    assert result["executed"] and state["family_state"]["io_access"] is True
    assert state["family_state"]["iv_access_failed"] is True
    assert glucose_rescue.IO_PLACED_TEXT in labels(result)
    assert glucose_rescue.delivered_share(state["family_state"], "IO") == 1.0
    assert glucose_rescue.delivered_share(state["family_state"], "IV") == glucose_rescue.FAILED_ACCESS_SHARE


def test_each_bleeding_measure_acts_and_is_said_as_written(engine):
    _, _, result = run(engine, "trauma", "trauma_limb_hemorrhage_27m", "Pack the wound and hold pressure")
    # Two measures written, two recorded -- and one intervention: the second adds no
    # control to the first, and neither stops an arterial source (TD-31, 2026-09-29).
    assert labels(result)[:2] == ["Packing applied to the wound: the external bleeding is reduced, not stopped",
                                  "Direct pressure applied to the wound: the external bleeding stays reduced, not "
                                  "stopped; this adds no control to what is already applied"]


def test_a_measure_named_by_none_is_asked_before_anything_runs(engine):
    _, _, result = run(engine, "trauma", "trauma_limb_hemorrhage_27m", "Hemorrhage control")
    assert not result["executed"] and "tourniquet, direct pressure or wound packing" in result["clarification"]


def test_the_trace_says_what_the_resident_did(engine):
    parsed = parse_family_actions("Transfuse 2 units PRBC and 2 units FFP. Activate MTP.")
    _, _, result = run(engine, "trauma", "trauma_hemothorax_41m", "Transfuse 2 units PRBC and 2 units FFP. Activate MTP.")
    event = {"learner_input": "", "action_summaries": result["action_summaries"],
             "recognized_future_actions": parsed["recognized_future_actions"],
             "future_details": parsed["future_details"], "interpreted_action": parsed["actions"]}
    trace = engine["_trace_action_text"](event)
    assert "Packed red cells 2 units started" in trace
    assert "2 units ffp (blood product ordered; physiologic effect not modelled)" in trace
    assert "activate mtp (massive transfusion protocol activated" in trace
    assert "not given" not in trace and "nothing was given" not in trace


def test_the_room_says_ordered_never_not_given_in_both_languages():
    said, unclassified = unexecuted_items.messages(parse_family_actions("Transfuse 2 units FFP. Activate MTP."))
    assert unclassified == []
    assert said[0].startswith("Massive transfusion protocol activation recorded: activate mtp.")
    assert said[1].startswith("Blood product ordered and recorded as your decision: transfuse 2 units ffp.")
    assert not any("nothing was given" in line for line in said)
    spanish = [language.say(line, "es") for line in said]
    assert spanish[0].startswith("Activación del protocolo de transfusión masiva registrada: «activate mtp»")
    assert spanish[1].startswith("Hemoderivado indicado y registrado como tu decisión: «transfuse 2 units ffp»")
    for kind in ("blood_product", "massive_transfusion"):
        assert report_language.t(unexecuted_items.CATEGORY_LABELS[kind], "es") != unexecuted_items.CATEGORY_LABELS[kind]


@pytest.mark.parametrize("english", [
    "intraosseous access (humeral) placed", "Hemostatic dressing applied to the wound: the external bleeding is controlled",
    "Specify which blood product to give and how many units.", "Specify a tourniquet, direct pressure or wound packing.",
    "Study requested; not modelled in this version of the simulator: Pregnancy test. The request is recorded with its "
    "time; no result will be produced and none is invented.",
])
def test_the_new_room_sentences_are_said_whole_in_spanish(english):
    spanish = language.say(english, "es")
    for word in ("intraosseous", "applied", "Specify", "blood product", "Pregnancy", "tourniquet"):
        assert word not in spanish, spanish


# --- the faculty's reading: an engine limit is never the resident's omission -----------------

def _entry(text, minute, executed=()):
    parsed = parse_family_actions(text)
    return {"execution_status": "executed", "decision_time_min": minute, "response_time_min": minute + 5,
            "learner_input": text, "interpreted_action": parsed["actions"],
            "action_summaries": list(executed), "recognized_future_actions": parsed["recognized_future_actions"],
            "future_details": parsed["future_details"]}


def test_a_blood_product_is_named_as_one_and_as_ordered():
    record = {"payload": {"session": {"management_trace": [_entry("Transfuse 2 units FFP", 0)]}}}
    [row] = rubric_screening.facts(record)["indicated"]
    assert row["category"] == "blood_product"
    fact = rubric_screening._indicated_fact([row])
    assert fact["en"].startswith("Ordered by the resident, with its physiologic effect not modelled: a blood product")
    assert "no administration" not in fact["en"] and fact["es"].startswith("Indicado por el residente")


def test_crystalloid_with_ordered_plasma_is_the_faculty_s_reading_not_a_silent_met():
    fluids = [{"type": "fluid", "volume_ml": 1500, "fluid_type": "normal saline", "label": "normal saline"}] * 2
    record = {"payload": {"session": {"management_trace": [
        _entry("NS 1500 mL IV and 1500 mL more. Transfuse 2 units FFP", 0, executed=fluids)]}}}
    rows = {r["event_id"]: r for r in rubric_screening.screen_events(record, "trauma_limb_hemorrhage_27m")}
    row = rows["trauma_crystalloid_instead_of_blood"]
    assert row["status"] == "reading"
    assert any("a blood product" in fact["en"] for fact in row["facts"])
    # Without the plasma the definition still settles it.
    record["payload"]["session"]["management_trace"] = [_entry("NS 1500 mL IV and 1500 mL more", 0, executed=fluids)]
    rows = {r["event_id"]: r for r in rubric_screening.screen_events(record, "trauma_limb_hemorrhage_27m")}
    assert rows["trauma_crystalloid_instead_of_blood"]["status"] == "met"


def test_crystalloid_with_the_protocol_activated_is_read_too():
    # The activation gives no blood by itself; the faculty reads it beside the
    # crystalloid, and a silent "met" hid it (adversarial review of cycle 7).
    fluids = [{"type": "fluid", "volume_ml": 1500, "fluid_type": "normal saline", "label": "normal saline"}] * 2
    record = {"payload": {"session": {"management_trace": [
        _entry("NS 1500 mL IV and 1500 mL more. Activate the massive transfusion protocol", 0, executed=fluids)]}}}
    row = {r["event_id"]: r for r in rubric_screening.screen_events(
        record, "trauma_limb_hemorrhage_27m")}["trauma_crystalloid_instead_of_blood"]
    assert row["status"] == "reading"
    assert any("massive transfusion protocol" in fact["en"] for fact in row["facts"])


# --- what the independent set and the adversarial review found (A–J, cycle 7) ------------
# A red-cell word and a count anywhere in the clause ran a transfusion nobody ordered; each
# of these must give no red cells. A result, a transfusion elsewhere or before, a refusal, a
# stop, a question, a plan, a consent, an estimated loss and insulin beside "blood glucose".

@pytest.mark.parametrize("text", [
    "Hb 6.2 tras 2 U GR", "Hemoglobin 6.5 after 2 units PRBC", "Lleva 2 U de GR",
    "2 U GR recibidas en el hospital de origen", "Viene de otro centro con 2 U GR", "S/p 2 units PRBC",
    "2 units PRBC given at 14:00", "SAMU: 1 U GR O negativo en ruta", "1 unit of O-neg given en route",
    "Testigo de Jehová: rechaza transfusión de 2 U GR", "Patient refuses 2 units of blood",
    "Suspender transfusión de las 2 U GR por reacción", "Stop the 2 units of PRBC", "¿Transfundo 2 U GR?",
    "Should I give 2 units O-neg?", "Requiere 2 U GR", "He will probably need 2 units of blood",
    "Transfusion threshold Hb < 7: 1 unit PRBC", "Transfundir 2 U GR cuando Hb < 7", "Once blood arrives, 2 units O-neg",
    "En cuanto llegue, 2 U GR", "After the CT, transfuse 2 units PRBC", "Consent obtained for 2 units PRBC",
    "Blood bank says 2 units O-neg are left", "Estimated blood loss 2 units", "Perdió el equivalente a 2 U de sangre",
    "Insulin 4 units SC for blood glucose 300", "Give insulin 4 units for blood sugar 300",
    "Prior transfusion reaction to 1 unit PRBC", "Balance: 2 U GR, 2 L SF", "So far 2 units PRBC and 2 L crystalloid",
    "Grupo y pruebas cruzadas para transfundir 2 U GR", "Keep 2 units O-neg in the room",
    "Bring 2 units O-neg from the fridge", "Use a blood warmer for the 2 units", "Ceftriaxona 2 gr/24h ev",
    "Paracetamol 1 gr/8h vo", "Sulfato de magnesio 2 gr/20 min ev", "Blood pressure on the arm 80/50",
])
def test_nothing_the_resident_did_not_order_runs_red_cells(text):
    assert "blood" not in kinds(text), read(text)


@pytest.mark.parametrize("text, units", [
    ("GR 2 U", 2), ("GR: 2 U", 2), ("GR x 2", 2), ("2 GR", 2), ("Hang 4 PRBC", 4), ("2 PRBC now", 2),
    ("Transfusión de 2 U GR", 2), ("Transfusion of 2 units PRBC", 2), ("Blood transfusion 2 units", 2),
    ("2 paquetes globulares", 2), ("2 concentrados eritrocitarios", 2), ("Una unidad de GR", 1),
    ("Hang a unit of PRBC", 1), ("HR 132 - give 2 units PRBC now", 2), ("Blood: 2 units O-neg", 2),
    ("2 U O positivo", 2), ("pasar 2 UGR O negativo no cruzados ya", 2), ("pasar 2 GR sin esperar pruebas cruzadas", 2),
])
def test_red_cells_written_as_the_chart_writes_them_run_in_those_units(text, units):
    assert [a for a in read(text) if a["type"] == "blood"] == [{"type": "blood", "units": float(units)}]


def test_only_the_new_units_run_after_a_history_of_units():
    assert read("Hb 7.2 después de 2 U GR; transfundir 1 U más") == [{"type": "blood", "units": 1.0}]
    assert read("Lleva 2 U GR, transfundo 1 más") == [{"type": "blood", "units": 1.0}]


def test_two_red_cell_orders_in_one_sentence_are_one_whose_count_is_asked():
    assert read("2 U GR ahora y 2 U GR en 1 hora") == [{"type": "blood", "units": None}]
    assert read("Transfuse PRBC 2 units, O-neg 2 units") == [{"type": "blood", "units": None}]


@pytest.mark.parametrize("text, drug", [
    ("Transfuse 2 units FFP with TXA 1 g IV over 10 min", "tranexamic_acid"),
    ("Activate MTP with TXA 1 g IV", "tranexamic_acid"), ("Activo PTM con ácido tranexámico 1 g ev", "tranexamic_acid"),
    ("Give TXA 1 g IV with 1 unit of platelets", "tranexamic_acid"), ("Tourniquet with TXA 1 g IV", "tranexamic_acid"),
    ("Torniquete más ácido tranexámico 1 g ev", "tranexamic_acid"),
    ("Transfuse 2 units FFP with calcium gluconate 1 g IV", "calcium"),
    ("Plasma fresco congelado 2 U con omeprazol 80 mg ev", "ppi"),
])
def test_a_medicine_written_with_a_product_or_a_measure_is_given(text, drug):
    # The product's block recorded it as a medicine not modelled: "nothing was given".
    assert drug in kinds(text)
    assert ("not_modelled", "other") not in recorded(text)


@pytest.mark.parametrize("text", [
    "FFP not needed", "PFC no indicado", "Withhold FFP", "Should we give FFP?", "Suspender PFC",
    "Platelet transfusion threshold 50k", "Start NS 1 L, plasma lactate in 2 h", "Whole blood glucose 40 mg/dL",
    "Glucosa en sangre total 40 mg/dL, dar glucosado", "Start heparin, platelets in 24 h", "Dar SF 1 L, plaquetas, INR",
    "Give PCC 50 U/kg instead of plasma", "2 U PFC recibidas en ruta", "Thaw 4 units FFP",
])
def test_a_product_named_but_not_ordered_is_not_recorded_as_ordered(text):
    assert ("not_modelled", "blood_product") not in recorded(text)


@pytest.mark.parametrize("text", [
    "Call blood bank for possible MTP", "MTP activated by the surgeon", "PTM ya activado", "Ya se activó el PTM",
    "Order X-ray of the right first MTP", "Request blood bank standby for MTP",
])
def test_what_is_not_an_activation_now_records_none(text):
    assert ("not_modelled", "massive_transfusion") not in recorded(text)


def test_the_protocol_is_read_in_its_other_forms_and_the_units_after_it_run():
    for text in ("Activación de PTM", "MTP activation now", "Activate the major haemorrhage protocol"):
        assert ("not_modelled", "massive_transfusion") in recorded(text), text
    assert kinds("Activate MTP, 4 units O-neg") == ["blood"]
    assert kinds("Activar PTM: 4 U GR O negativo, 4 U PFC, 1 aféresis de plaquetas") == ["blood"]
    assert read("PTM activado: 4 GR + 4 PFC + 1 pool plaquetas")[0] == {"type": "blood", "units": 4.0}
    assert read("MTP cooler 1 arrived: hang 4 PRBC and 4 FFP")[0] == {"type": "blood", "units": 4.0}
    # A product ordered per the protocol is the product.
    assert recorded("Transfuse FFP per MTP") == [("not_modelled", "blood_product")]


@pytest.mark.parametrize("text", [
    "Hold pressure meds", "Nurse is holding pressure on the groin", "Hold pressure at 30 cmH2O for recruitment",
    "FAST para descartar taponamiento", "Descartar taponamiento con ecocardiograma", "Taponamiento con balón de Sengstaken",
    "Remove the tourniquet", "Retirar torniquete", "Convert tourniquet to pressure dressing",
    "Call surgery for preperitoneal packing",
])
def test_what_only_mentions_a_bleeding_measure_applies_none(text):
    assert not any(a["type"] == "hemorrhage_control" and a.get("measure") for a in read(text)), read(text)


# What a verb that stops, keeps or gives nothing does to red cells and to a measure (post hoc,
# cycle 7): "transfusión de …" is what the clause's verb does to it, so stopped or kept it never
# runs; what the engine cannot do is quoted back, never lost without a word; and the bleeding a
# verb stops is not a measure removed.

@pytest.mark.parametrize("text", [
    "Suspender transfusión de las 2 U GR", "Stop transfusion of 2 units", "Retirar transfusión de 2 U GR",
    "Discontinue blood transfusion 2 units", "Mantener transfusión de 2 U GR", "Continuar transfusión de GR",
    "Stop the PRBC", "Stop the blood", "Disconnect the blood", "Place 2 units of PRBC", "Titrate blood",
    "Aplicar 2 U GR", "Stop the saline and the PRBC", "Suspender la noradrenalina y la sangre",
])
def test_a_transfusion_stopped_kept_or_not_given_never_runs_and_is_quoted_back(text):
    actions = read(text)
    assert "blood" not in [a["type"] for a in actions], actions
    assert any(a.get("unrecognized_text") for a in actions), actions


def test_switching_to_blood_is_giving_it():
    for text in ("Switch to blood", "Cambiar a sangre", "Stop the saline and go to blood"):
        assert [a for a in read(text) if a["type"] == "blood"] == [{"type": "blood", "units": None}], text


@pytest.mark.parametrize("text, measure", [
    ("Detener sangrado: presión directa", "direct pressure"), ("Stop the bleeding with direct pressure", "direct pressure"),
    ("Detén el sangrado con un torniquete", "tourniquet"), ("Stop the bleed: tourniquet", "tourniquet"),
    ("Stop bleeding: pack the wound", "packing"), ("Stop the bleeding and hold pressure", "direct pressure"),
])
def test_stopping_the_bleeding_with_a_measure_is_the_measure(text, measure):
    assert [a["measure"] for a in read(text) if a["type"] == "hemorrhage_control"] == [measure]


@pytest.mark.parametrize("text", ["Suspender la presión directa", "Stop direct pressure", "Stop the tourniquet",
                                  "Retirar el torniquete y la presión directa"])
def test_a_measure_stopped_is_never_applied(text):
    assert not any(a["type"] == "hemorrhage_control" for a in read(text)), read(text)


@pytest.mark.parametrize("text", [
    "GR y plasma 1:1, 4 U de cada uno", "Plasma y GR 1:1", "PRBC and FFP 1:1, 4 units each",
    "Transfuse PRBC, FFP and platelets 1:1:1, 4 units each",
])
def test_one_ratio_or_one_count_for_several_products_is_asked(text):
    # Lost without a word, or half read, before (post hoc, cycle 7).
    assert [(a["type"], a.get("message")) for a in read(text)] == [
        ("clarification", "Write each blood product with its own number of units.")]


def test_a_measure_removed_or_converted_is_quoted_back_never_applied():
    for text in ("Remove the tourniquet", "Loosen the tourniquet to check for bleeding",
                 "Convert tourniquet to pressure dressing", "Reemplazar torniquete por vendaje compresivo"):
        actions = read(text)
        assert [a["type"] for a in actions] == ["clarification"] and actions[0].get("unrecognized_text"), text
    assert read("Tourniquet released by EMS") == []


@pytest.mark.parametrize("text, units", [("Un GR", 1), ("Dos GR O negativo", 2), ("Transfundir un GR", 1)])
def test_red_cells_counted_in_words_run_in_that_count(text, units):
    assert read(text) == [{"type": "blood", "units": float(units)}]


def test_activating_the_protocol_just_named_is_its_activation():
    assert recorded("Meets MTP criteria, activate") == [("not_modelled", "massive_transfusion")]
    assert recorded("Cumple criterios de PTM, lo activo") == [("not_modelled", "massive_transfusion")]
    assert recorded("No cumple criterios de PTM, activar") == []


def test_what_the_intraosseous_line_is_for_is_not_given_through_it():
    for text in ("Place humeral IO for fluids", "IO humeral para volumen"):
        assert kinds(text) == ["vascular_access"], text
    assert kinds("Humeral IO with 1 L NS") == ["vascular_access", "fluid"]


def test_a_balance_of_what_the_patient_received_gives_nothing_again():
    # The red cells were read as history; the saline ran again (post hoc, cycle 7).
    for text in ("Balance: 2 U GR, 2 L SF", "Ingresos: 2 U GR y 1 L de SF", "So far 2 units PRBC and 2 L crystalloid"):
        assert read(text) == [], text
    assert kinds("So far no response, give 1 L NS") == ["fluid"]


def test_an_alternative_between_measures_is_asked_about():
    assert read("Tourniquet or direct pressure") == [{"type": "hemorrhage_control", "measure": None, "site": "wound"}]


def test_an_intraosseous_line_removed_or_described_is_never_placed():
    assert read("Remove the humeral IO") == [{"type": "vascular_access", "operation": "stop", "access": "intraosseous"}]
    for text in ("The humeral IO is infiltrated", "IO access failed, place a second peripheral IV"):
        assert not any(a.get("access") == "intraosseous" and a.get("operation") == "start" for a in read(text)), text
    assert kinds("Humeral IO with 2 units O-neg") == ["vascular_access", "blood"]


@pytest.mark.parametrize("text, expected", [
    ("Test de embarazo en orina", ["pregnancy_test"]), ("Prueba de embarazo antes del angioTAC", ["pregnancy_test", "ctpa"]),
    ("Is she pregnant? Check a urine pregnancy test", ["pregnancy_test"]), ("run a quick UPT", ["pregnancy_test"]),
    ("antes de seguir hagan un test pack rapido", ["pregnancy_test"]),
])
def test_the_pregnancy_test_is_read_in_its_natural_forms(text, expected):
    assert [a["diagnostic"] for a in read(text) if a["type"] == "diagnostic"] == expected


@pytest.mark.parametrize("text, expected", [
    # A finding before an order no longer takes the order with it.
    ("sin acceso venoso visible, puyen una EZ-IO tibial ya", ["vascular_access"]),
    ("no IV access, humeral IO now", ["vascular_access"]),
    ("SpO2 88% - start oxygen 15 L NRB", ["oxygen"]),
    ("no tiene PA registrable, activemos el protocolo de transfusion masiva", []),
    # The team's plural and the Chilean "now".
    ("empaquen la herida bien profundo con gasa y mantengan presion encima", ["hemorrhage_control", "hemorrhage_control"]),
    ("activo PTM y de una vez pasen 2 GR no cruzados, e instalen un tubo pleural izquierdo",
     ["blood", "chest_decompression"]),
    # What a transfusion waits for is asked about; an order after a question still runs.
    ("somebody control that bleeding now while I get access", ["hemorrhage_control"]),
])
def test_the_forms_of_the_independent_set_are_read(text, expected):
    assert kinds(text) == expected


@pytest.mark.parametrize("text", [
    "No response: repeat epinephrine 0.5 mg IM.", "How are you feeling? Do you have any pain?",
    "¿Vale la pena 1 g de ácido tranexámico? Después del HALT-IT no me convence mucho en HDA.",
    "Glucosa 40 mg/dL", "left hand cooler than right", "suba la glicemia",
])
def test_what_the_new_readings_must_not_turn_into_an_order(text):
    assert not [a for a in read(text) if a["type"] not in {"clarification"}], read(text)


def test_the_new_held_lines_and_the_count_question_read_in_spanish():
    lines = ("Also in this order, a blood product whose physiologic effect is not modelled: 2 u pfc.\n"
             "Also in this order, the massive transfusion protocol's activation: activate mtp.")
    spanish = language.say(lines, "es")
    assert "Also in this order" not in spanish and "hemoderivado" in spanish and "transfusión masiva" in spanish
    assert language.say("Confirm the number of packed red-cell units (1–4 per order).", "es").startswith("Confirma")
