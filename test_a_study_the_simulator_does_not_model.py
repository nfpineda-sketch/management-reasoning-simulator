"""A study the resident asks for and this simulator does not produce.

Faculty decision of 2026-09-24. "Grupo y pruebas cruzadas" does not exist as a
study in the bank, nor a head CT in the hypoglycaemia cases. Both stay pending
as capabilities; what changed is how a request for them is treated:

* "not implemented in the simulator" is never "not available in the service"
  -- a resource restriction is a decision the scenario states, with a reason;
* the intention is recognised and the request is recorded with its time and
  its status, and the rest of the submission runs;
* no result is invented and the study is never recorded as performed;
* the request stays in the record, where the faculty can judge whether asking
  for it was pertinent and timely.

Played through the production interpreter and engine, with no provider key.
"""
from copy import deepcopy

import pytest

import family_parser
import record_findings
from family_engine import NOT_MODELED_LABEL, STUDY_NOT_PERFORMED
from tools_rubric_runs import play_orders


def _script(case_id, family, orders):
    return {"case_id": case_id, "family": family, "orders": orders,
            "reflection": {}, "plan": {}, "intent": "test"}


def _summaries(event, kind=STUDY_NOT_PERFORMED):
    return [s for s in event.get("action_summaries") or [] if s.get("type") == kind]


# --- the words ------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "pido TAC de cerebro", "pido TC de craneo", "TAC cerebral", "tomografia cerebral",
    "pido tomografia computada de encefalo", "scanner cerebral", "get a CT of the head",
    "order a head CT"])
def test_a_head_ct_is_recognised_however_it_is_asked_for(text):
    actions = family_parser.parse_family_actions(text)["actions"]
    assert actions == [{"type": "diagnostic", "diagnostic": "head_ct"}]


@pytest.mark.parametrize("text", [
    "pido grupo y pruebas cruzadas", "grupo y pruebas cruzadas", "pido grupo y rh",
    "solicito pruebas cruzadas", "reservar 2 unidades de sangre", "type and screen",
    "send type and crossmatch", "crossmatch 2 units", "order crossmatch for 2 units of blood"])
def test_a_crossmatch_is_recognised_and_is_never_a_transfusion(text):
    actions = family_parser.parse_family_actions(text)["actions"]
    assert actions == [{"type": "diagnostic", "diagnostic": "crossmatch"}]


def test_giving_the_units_is_still_a_transfusion():
    actions = family_parser.parse_family_actions(
        "transfundir 2 unidades de globulos rojos con pruebas cruzadas")["actions"]
    assert actions == [{"type": "blood", "units": 2.0}]


def test_asking_for_units_asks_whether_to_give_them_or_reserve_them():
    actions = family_parser.parse_family_actions("pido 2 unidades de globulos rojos")["actions"]
    assert actions[0]["type"] == "clarification"
    assert "transfuse these units now" in actions[0]["message"]
    assert "crossmatch" in actions[0]["message"]


def test_a_study_list_keeps_its_two_word_requests_whole():
    actions = family_parser.parse_family_actions("pido hemoglobina, grupo y pruebas cruzadas")["actions"]
    assert [a["diagnostic"] for a in actions] == ["hemoglobin", "crossmatch"]


# --- the encounter ----------------------------------------------------------
@pytest.fixture(scope="module")
def glucose_and_head_ct():
    record, transcript = play_orders(_script("hypoglycemia_28m", "hypoglycemia", [
        "Pido glicemia capilar y TAC de cerebro",
    ]))
    return record, transcript


def test_the_rest_of_the_submission_runs_and_the_request_is_recorded(glucose_and_head_ct):
    record, transcript = glucose_and_head_ct
    event = record["payload"]["session"]["management_trace"][0]
    assert event["execution_status"] == "executed", transcript
    # The glucose was obtained: its result is in the record.
    reported = [s.get("diagnostic_type") for s in event["action_summaries"] if s.get("type") == "diagnostic"]
    assert "poc_glucose" in reported
    # The head CT is recorded as asked for, at its minute, and why nothing came.
    [ct] = _summaries(event)
    assert ct["diagnostic"] == "head_ct" and ct["not_performed"] == "not_modeled"
    assert ct["time_min"] == event["decision_time_min"]
    assert ct["label"].startswith(NOT_MODELED_LABEL + ": Head CT.")
    assert "not available" not in ct["label"].lower()


def test_nothing_is_invented_for_it(glucose_and_head_ct):
    record, _ = glucose_and_head_ct
    event = record["payload"]["session"]["management_trace"][0]
    for side in ("state_before", "state_after"):
        assert "head_ct" not in (event[side].get("diagnostics") or {})
    assert all(s.get("diagnostic_type") != "head_ct" for s in event["action_summaries"])


def test_it_costs_no_clinical_time_of_its_own():
    alone, transcript = play_orders(_script("hypoglycemia_28m", "hypoglycemia", ["Pido TAC de cerebro"]))
    [event] = alone["payload"]["session"]["management_trace"]
    assert event["execution_status"] == "executed", transcript
    assert event["decision_time_min"] == event["response_time_min"] == 0
    assert event["state_after"]["observable"] == event["state_before"]["observable"]


def test_the_record_does_not_read_it_as_a_result_that_never_came(glucose_and_head_ct):
    record, _ = glucose_and_head_ct
    trace = record["payload"]["session"]["management_trace"]
    stage = record_findings.order_stages(trace)["trace:0"]
    assert stage["not_performed"] == ["head_ct"]
    assert "head_ct" not in stage["awaiting"]
    assert "head_ct" not in record_findings.orders_without_result(trace)


def test_a_crossmatch_in_a_bleed_is_recorded_beside_the_haemoglobin():
    record, transcript = play_orders(_script("gi_bleed_57m", "gi_bleed", [
        "Pido hemoglobina, grupo y pruebas cruzadas"]))
    [event] = record["payload"]["session"]["management_trace"]
    assert event["execution_status"] == "executed", transcript
    [crossmatch] = _summaries(event)
    assert crossmatch["diagnostic"] == "crossmatch"
    assert crossmatch["label"].startswith(NOT_MODELED_LABEL + ": Blood group and crossmatch.")


def test_a_restriction_is_the_scenario_s_to_state_with_its_reason():
    """Only a case that says so turns a study into "not available in this service"."""
    import clinical_cases
    from family_engine import execute_family_bundle
    from test_cognitive_encounters import encounter as build_encounter
    from test_curriculum_trajectories import load_engine
    engine = load_engine()
    generated = build_encounter(engine, "hypoglycemia", "hypoglycemia_28m")
    state = deepcopy(generated["state"])
    state["encounter_spec"]["clinical_case"]["resources_unavailable"] = {
        "head_ct": "This rural hospital has no CT scanner; transfer takes two hours."}
    result = execute_family_bundle(state, {"actions": [{"type": "diagnostic", "diagnostic": "head_ct"}]})
    [summary] = result["action_summaries"]
    assert summary["not_performed"] == "unavailable_in_service"
    assert summary["label"] == ("Not available in this service: Head CT. This rural hospital has no "
                                "CT scanner; transfer takes two hours.")


def test_the_resident_reads_it_in_their_language():
    import language
    text = ("Study requested; not modelled in this version of the simulator: Blood group and "
            "crossmatch. The request is recorded with its time; no result will be produced and "
            "none is invented.")
    assert language.say(text, "es") == (
        "Estudio solicitado; no modelado en esta versión del simulador: Grupo y pruebas cruzadas. "
        "La solicitud queda registrada con su hora; no habrá resultado y no se inventa ninguno.")


def test_asking_for_head_imaging_counts_as_pursuing_the_altered_state():
    """The event asks whether anything pursued the confusion. A request the
    simulator cannot answer did pursue it: the technical impossibility is not
    the resident's omission."""
    import rubric_screening
    record, _ = play_orders(_script("pneumonia_83m", "pneumonia", [
        "Creo que es una neumonia con compromiso de conciencia. Mi prioridad es antibiotico y "
        "descartar otra causa del compromiso. Doy ceftriaxona 2 g ev; pido TAC de cerebro. Espero "
        "que mejore la perfusion. Reevaluo en 20 minutos."]))
    screen = {row["event_id"]: row["status"] for row in
              rubric_screening.screen_events(record, "pneumonia_83m")}
    assert screen["pneumonia_unexamined_altered_state"] == "contradicted"


def test_a_d_dimer_the_resident_obtained_reaches_the_faculty_analysis():
    """Six studies the bank carries used to be invisible to the brief and the rubric."""
    from faculty_analysis import build_analysis_source
    record, _ = play_orders(_script("pulmonary_embolism_33f", "pulmonary_embolism", [
        "Pido dimero D; pido POCUS. Reevaluo en 30 minutos",
        "Examino las extremidades",
    ]))
    session = record["payload"]["session"]
    session["precomparison_decision_review"] = {"decision-1": {
        "working_model_update": "x", "priority_trigger": "x", "alternative_action": "x",
        "expected_response_reassessment": "x"}}
    source = build_analysis_source(record)
    seen = {}
    for event in source["decision_events"]:
        seen.update(event["state_after"]["diagnostics_available"])
    assert "d_dimer_ng_ml_feu" in seen.get("d_dimer", {}), sorted(seen)
