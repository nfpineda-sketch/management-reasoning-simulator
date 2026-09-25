"""What the offline rehearsal of the twenty-scenario batch found, held in place.

2026-09-24. Before any paid encounter, each of the twenty scripts was played
through the real page (tools_tanda20.py --rehearse). Nineteen reached a
completed review; the scripts that did not run as written showed orders a
resident writes every day that the application did not read, or read wrongly:

* "nbz" and "vvp", the chart's own abbreviations for a nebulization and a
  peripheral line, held two whole resuscitations;
* "SF 1000 ml ev" without a verb was held while a drug written the same way ran;
* "mascarilla de no recirculacion" ran as a simple mask;
* "Los gases muestran retencion de CO2" -- a result being read -- asked which
  gases to order, and held an escalation to NIV;
* "Toma glibenclamida", "toma betabloqueador" -- the patient's medicines --
  were read as a study to take, and held the order that followed;
* "Lo traslado a hemodinamia" asked for a bed;
* "Lo dejo en observacion 2 horas" was dropped, or held the order with it;
* an antihistamine, a benzodiazepine or a prescription for discharge held the
  whole submission instead of being said back as recognised and not executed;
* several treatments added after the four-question requirement was written
  (atropine, glucagon, thrombolysis...) ran with no stated expectation.
"""
import pytest

from family_parser import NEW_TREATMENT_ACTIONS, parse_family_actions


def actions(text):
    return parse_family_actions(text)["actions"]


def kinds(text):
    return [action["type"] for action in actions(text)]


@pytest.mark.parametrize("text", ["Doy salbutamol 5 mg nbz", "ipratropio 0,5 mg NBZ",
                                  "salbutamol 2.5 mg en nebulizacion"])
def test_a_nebulization_written_the_chart_s_way(text):
    [action] = actions(text)
    assert action["type"] == "bronchodilator" and action["route"] == "nebulized"


@pytest.mark.parametrize("text", ["colocar vvp", "Instalo 2 vvp gruesas", "coloco 2 VVP"])
def test_a_peripheral_line_written_as_vvp(text):
    assert kinds(text) == ["vascular_access"]


@pytest.mark.parametrize("text", ["SF 1000 ml ev", "sf 1000 ml ev en bolo",
                                  "suero fisiologico 1000 ml ev en bolo"])
def test_a_fluid_written_without_a_verb(text):
    [action] = actions(text)
    assert action["type"] == "fluid" and action["volume_ml"] == 1000.0
    assert action["fluid_type"] == "normal saline"


def test_a_fluid_in_a_list_after_other_orders():
    assert kinds("O2 por naricera 4 L/min; SF 1000 ml ev.") == ["oxygen", "fluid"]


@pytest.mark.parametrize("text", ["Doy O2 por mascarilla de no recirculacion a 15 L/min",
                                  "O2 mascarilla no recirculante 15 L/min",
                                  "oxigeno con mascarilla de no reinhalacion 15 L/min"])
def test_the_non_rebreather_by_what_it_does_not_do(text):
    [action] = actions(text)
    assert action["device"] == "non-rebreather mask" and action["flow_lpm"] == 15


def test_a_result_read_in_the_reasoning_is_not_an_order_for_it():
    assert kinds("Los gases muestran retencion de CO2 y sigue somnoliento: es falla "
                 "ventilatoria. Inicio VMNI BiPAP 12/5 con FiO2 40%") == ["niv"]
    # Asking for gases without saying which still asks.
    assert kinds("Pido gases") == ["clarification"]
    assert actions("pido gases arteriales") == [{"type": "diagnostic", "diagnostic": "abg"}]


@pytest.mark.parametrize("text", ["Toma glibenclamida: puede volver a caer por horas",
                                  "Toma betabloqueador, por eso no responde",
                                  "toma sus remedios para la presion"])
def test_what_the_patient_takes_is_history(text):
    assert actions(text) == []


def test_a_sample_is_still_taken():
    assert actions("toma una glicemia capilar") == [{"type": "diagnostic", "diagnostic": "poc_glucose"}]


def test_transferring_to_the_cath_lab_activates_it():
    assert actions("Lo traslado a hemodinamia") == [{"type": "consult", "service": "cath lab"}]
    assert actions("Lo hospitalizo en sala") == [{"type": "disposition", "destination": "ward"}]


@pytest.mark.parametrize("text", ["lo dejo en observacion 2 horas",
                                  "Dejo en observacion con monitorizacion"])
def test_keeping_the_patient_under_observation_is_monitoring(text):
    assert kinds(text) == ["monitoring"]


def test_observation_no_longer_holds_what_was_ordered_with_it():
    parsed = parse_family_actions("Le doy colacion oral y lo dejo en observacion 2 horas con "
                                  "glicemia capilar seriada. Reevaluo en 30 minutos glicemia.")
    assert [a["type"] for a in parsed["actions"]] == ["oral_carbohydrate", "monitoring", "reassessment"]


@pytest.mark.parametrize("text, kept", [
    ("Doy clorfenamina 10 mg ev y hidrocortisona 200 mg ev", ["steroid"]),
    ("Doy lorazepam 1 mg vo. Reevaluo en 30 minutos FC.", ["reassessment"]),
    ("La dejo en observacion 6 horas y le indico autoinyector al alta", ["monitoring"]),
    ("receto amoxicilina para el alta", []),
])
def test_what_is_recognised_and_not_executed_is_said_back_and_the_rest_runs(text, kept):
    parsed = parse_family_actions(text)
    assert [a["type"] for a in parsed["actions"]] == kept
    assert len(parsed["recognized_future_actions"]) == 1
    assert not any(a["type"] == "clarification" for a in parsed["actions"])


def test_withholding_an_unmodelled_drug_is_still_a_withholding():
    parsed = parse_family_actions("sin clorfenamina")
    assert parsed["actions"] == [] and parsed["recognized_future_actions"] == []


# --- the four questions apply to every treatment --------------------------------

# Deliberately outside the requirement, each for a stated reason. Anything the
# parser learns later has to be placed on one side or the other.
NOT_A_DECISION_THAT_NEEDS_THE_FOUR = {
    # Nursing and support orders: recorded, with no physiology of their own.
    "vascular_access", "monitoring", "npo", "urinary_catheter", "gastric_tube",
    # Obtaining information, not treating.
    "stress_test", "result_review",
    # Disconnecting the ventilator is a step inside an airway decision.
    "ventilator_disconnect",
    # Trauma bedside procedures: pending the faculty's decision.
    "chest_decompression", "hemorrhage_control", "pelvic_binder",
}


def test_every_treatment_asks_for_the_four_or_is_exempt_on_purpose():
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).with_name("app.py").read_text(encoding="utf-8"))
    gated = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                 and any(getattr(t, "id", "") == "REASONING_GATE_ACTION_TYPES" for t in node.targets))
    unplaced = sorted(set(NEW_TREATMENT_ACTIONS) - set(gated) - NOT_A_DECISION_THAT_NEEDS_THE_FOUR)
    assert unplaced == [], unplaced


# --- the engine runs what it read, and says what it did not -----------------------

def test_an_unmodelled_drug_does_not_stop_the_adrenaline():
    from tools_rubric_runs import play_orders
    record, transcript = play_orders({
        "case_id": "anaphylaxis_29f", "family": "anaphylaxis", "intent": "test",
        "reflection": {}, "plan": {},
        "orders": ["Creo que es una anafilaxia, porque tiene estridor y PA 84/46. Mi prioridad es la "
                   "adrenalina. Doy adrenalina 0.5 mg im y clorfenamina 10 mg ev; SF 1000 ml ev. Espero "
                   "que suba la PA. Reevaluo en 5 minutos PA y estridor."]})
    [event] = record["payload"]["session"]["management_trace"]
    assert event["execution_status"] == "executed", transcript
    given = [s.get("type") for s in event["action_summaries"]]
    assert "epinephrine_im" in given and "fluid" in given, given
    assert event["recognized_future_actions"] == ["clorfenamina 10 mg ev"]
