"""Cycle 9: the known high-risk defects removed before the external validation freeze.

- TD-39: a discharge written for later -- with its own time, after an observation or a result,
  or on a condition -- is a disposition plan, recorded and not carried out now. An immediate
  discharge still runs; a denied, asked or someone else's discharge runs nothing.
- TD-34: a reassessment interval in hours is its minutes, one value from the reader to the
  clock and the record: "Reassess in 1 h" waits 60 minutes, never 0.
- TD-36: a treatment received before the resident's care, as told ("given by EMS", "ya recibió")
  is history: recorded with what, dose, route and who, never given again and never the
  resident's order.
- TD-33: for the transfusion overload rule in trauma only blood replaces the haemorrhagic
  deficit; crystalloid keeps its haemodynamic effect.
- DF-20 closed with no change: acs_54m_inferior declares TD1, F1, C1 and C3, and none of its
  rows rests on the POCUS.
- DF-23 row 4a: the lungs of acs_70f_left_main's POCUS say what its examination and film say.
"""
import pytest

import encounter_close
import language
import unexecuted_items
from family_engine import execute_family_bundle, transfusion_overload
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def read(text):
    return [{key: value for key, value in action.items() if key in ("type", "destination", "delay_min", "agent",
                                                                        "dose_mg", "route", "volume_ml")}
            for action in parse_family_actions(text)["actions"]]


def kept(text):
    return [(detail["kind"], detail.get("category")) for detail in parse_family_actions(text)["future_details"]]


def run(engine, family, case, text):
    state = encounter(engine, family, case)["state"]
    parsed = parse_family_actions(text)
    result = execute_family_bundle(state, parsed)
    return state, parsed, result


def discharges(text):
    return any(action.get("type") == "disposition" and action.get("destination") == "home"
               for action in parse_family_actions(text)["actions"])


# --- TD-39: a discharge for later is a plan -------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Discharge home.", "Alta a domicilio.", "OK to discharge.", "OK to discharge now", "Alta ahora", "Dar de alta",
    "Discharge home now with EpiPen and return precautions", "Alta a domicilio con control en 48 horas",
    "Alta a domicilio, control en APS en 48 h", "Discharge home with follow-up in 2 days", "Discharge home today",
    "Alta hoy", "Discharge home in stable condition", "I will discharge her home", "Monitor and discharge home",
    "Dar paracetamol 1 g y alta", "Salbutamol 5 mg NBZ, alta a domicilio",
])
def test_an_immediate_discharge_still_runs(text):
    assert discharges(text), read(text)


@pytest.mark.parametrize("text", [
    # a time of its own
    "Discharge in 2 hours", "Discharge home in 2 hours", "Alta en 2 horas", "Alta en dos horas", "Alta mañana",
    "Discharge later today", "Dar de alta en 4 horas", "Discharge home at 18:00", "Alta a las 18 horas",
    "OK to discharge home in 2 hours", "Ok para alta en 2 horas", "Plan: alta en 2 horas", "Vamos a dar de alta en 2 horas",
    "Discharge planned for tomorrow", "Alta programada para mañana",
    # after an observation, a reassessment or a result
    "Observe 6 h then discharge", "Observe 6 h then discharge home", "Observar 4 horas y luego alta",
    "Observar y luego alta", "Alta tras 6 horas de observación", "Discharge after 4 hours of observation",
    "Discharge after repeat troponin", "Alta después de la segunda troponina", "Observe 6 h and discharge home",
    "Observar 6 horas y alta", "OK to discharge home, pending repeat lactate", "Ok para alta, mañana",
    # on a condition
    "Discharge if asymptomatic", "Discharge if she remains asymptomatic", "Can discharge if symptoms resolve",
    "Alta si sigue asintomático", "Alta si sigue asintomática", "Dar de alta si no hay recurrencia",
    "Discharge home in two hours if stable",
])
def test_a_discharge_for_later_is_a_disposition_plan_not_a_discharge_now(text):
    assert not discharges(text), read(text)
    assert ("conditional", "disposition_plan") in kept(text), kept(text)


@pytest.mark.parametrize("text", [
    "Do not discharge", "Not ready for discharge", "No dar de alta", "No dar de alta todavía", "Not for discharge yet",
    "Can she be discharged?", "¿Se puede ir de alta?", "Cardiology recommends discharge",
    "Cardiology says she can be discharged", "Cardiología sugiere alta",
])
def test_a_denied_asked_or_someone_else_s_discharge_runs_nothing(text):
    assert not discharges(text)
    assert ("conditional", "disposition_plan") not in kept(text)


# Found by the adversarial review of cycle 9: a four-digit clock, a time written after what the
# discharge sends home, and a threshold or a wait before it are still a discharge for later.
@pytest.mark.parametrize("text", [
    "Discharge at 1800", "Discharge home at 1800 with EpiPen", "Alta a las 1800", "Discharge home with EpiPen at 1800",
    "Discharge home with EpiPen in 2 hours", "Alta a domicilio con EpiPen en 2 horas",
    "Discharge home with her mother in 1 hour", "Alta con EpiPen a las 20:00",
    "Tras 6 h de observación sin incidencias, alta a domicilio", "After 6 h of uneventful observation, discharge home",
    "Tras 2 h con SatO2 94%, alta", "After PEF > 75%, discharge home", "Tras 3 nebulizaciones, si PEF > 70%, alta",
    "Alta ahora si tolera VO", "Discharge now if asymptomatic",
    # "now" answers the wait written with the discharge, never one written after it
    "OK to discharge now, pending repeat lactate", "Alta ahora, pendiente de la segunda troponina",
])
def test_the_forms_the_review_found_are_plans_too(text):
    assert not discharges(text), read(text)
    assert ("conditional", "disposition_plan") in kept(text), kept(text)


# ... and "now", a value measured, or a time that belongs to the follow-up, a dose or a start keep
# the discharge now; the first two ran now before cycle 9.
@pytest.mark.parametrize("text", [
    "Alta ahora tras 6 h de observación", "Tras 3 nebulizaciones PEF 80%, alta con prednisona 5 días",
    "Tras 3 nebulizaciones con PEF 80%, alta", "PEF 85% after nebs, discharge home", "Alta con control en 2 horas",
    "Alta con cita en policlínico en 48 h", "Discharge home with ceftriaxone, second dose in 24 h",
    "Discharge home with antibiotics to start in 12 hours", "Alta con analgesia y control en 1 hora",
    "Alta a domicilio con prednisona 40 mg cada 24 horas", "Discharge home with instructions to return in 24 h if worse",
    "Alta ahora, control mañana en APS", "Discharge home now with return precautions if worse",
    "Asintomática tras 4 h en observación, alta a domicilio", "Tras 6 h de observación, alta ahora",
])
def test_a_discharge_now_the_review_found_still_runs(text):
    assert discharges(text), read(text)
    assert ("conditional", "disposition_plan") not in kept(text)


def test_what_is_ordered_for_now_runs_beside_the_plan():
    assert read("Salbutamol 5 mg NBZ, OK to discharge home in 2 hours") == [
        {"type": "bronchodilator", "agent": "albuterol", "dose_mg": 5.0, "route": "nebulized"}]
    assert read("Epinephrine 0.5 mg IM, observe 4 hours, then discharge home with EpiPen") == [
        {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}]
    # The observation it waits for runs now; the discharge is the plan after it.
    assert read("Dejar en observación 6 horas y luego alta") == [{"type": "disposition", "destination": "ED observation"}]
    assert read("Reassess in 30 min then discharge home") == [{"type": "reassessment", "delay_min": 30.0}]
    assert read("Reevaluar en 30 min y luego alta") == [{"type": "reassessment", "delay_min": 30.0}]
    assert read("Reevaluar en 30 min y alta") == [{"type": "reassessment", "delay_min": 30.0}]
    # What goes home with the planned discharge is still a prescription, never a dose given now.
    assert kept("Alta en 2 horas, prednisona 40 mg c/24 h por 5 días") == [
        ("conditional", "disposition_plan"), ("prescription", "other")]


def test_the_plan_keeps_the_resident_s_words():
    texts = [detail["text"] for detail in parse_family_actions("Dejar en observación 6 horas y luego alta")["future_details"]]
    assert texts == ["Dejar en observación 6 horas y luego alta"]
    assert parse_family_actions("Alta mañana")["future_details"][0]["text"] == "Alta mañana"


def test_a_planned_discharge_does_not_close_the_encounter_and_the_trace_says_it_is_a_plan(engine):
    state, parsed, result = run(engine, "anaphylaxis", "anaphylaxis_29f", "Discharge home in 2 hours")
    assert state.get("disposition") is None and state["family_state"].get("discharged_at") is None
    assert not any(summary.get("type") == "disposition" for summary in result.get("action_summaries") or [])
    assert not encounter_close.has_destination([], state)
    said, _ = unexecuted_items.messages(parsed)
    assert said == ["Recorded as a disposition plan, not carried out now: Discharge home in 2 hours. The patient stays "
                    "in the emergency department; a plan is not carried out on its own."]
    assert language.say(said[0], "es") == ("Registrado como plan de destino, no realizado ahora: «Discharge home in 2 "
                                           "hours». El paciente sigue en urgencias; un plan no se realiza por sí solo.")
    assert unexecuted_items.trace_labels(parsed) == [("Discharge home in 2 hours", "disposition plan; not carried out now")]


def test_an_immediate_discharge_still_closes_it(engine):
    state, _, result = run(engine, "anaphylaxis", "anaphylaxis_29f", "Discharge home now")
    assert state.get("disposition") == "home"
    assert any(summary.get("type") == "disposition" for summary in result["action_summaries"])


def test_a_planned_discharge_is_no_executed_discharge_for_the_critical_events(engine):
    # The events defined on a discharge read an executed discharge disposition in the record.
    for text in ("Observe 6 h then discharge home with EpiPen", "Alta en 2 horas", "Alta si sigue asintomática"):
        _, parsed, result = run(engine, "anaphylaxis", "anaphylaxis_29f", text)
        assert not any(action.get("type") == "disposition" for action in parsed["actions"]), text
        assert not any(summary.get("type") == "disposition" for summary in result.get("action_summaries") or []), text


# --- TD-34: a reassessment in hours waits its minutes --------------------------------------------

@pytest.mark.parametrize("text, minutes", [
    ("Reevaluar en 1 h", 60), ("Reassess in 1 h", 60), ("Reassess in 1 hr", 60), ("Reevaluar en 2 h", 120),
    ("Reassess in 1 hour", 60), ("Reevaluar en 1 hora", 60), ("Reassess in 1.5 h", 90), ("Reevaluar en 1,5 horas", 90),
    ("Reassess in 2 hrs", 120), ("Reassess in an hour", 60), ("Reevaluar en media hora", 30),
    ("Reevaluar en una hora y media", 90), ("Reassess in 1 h 30 min", 90), ("Reevaluar después de 2 h de VNI", 120),
    # found by the adversarial review: the minutes after the hour without their unit
    ("Reassess in 1 h 30", 90), ("Reevaluar en 1h30", 90), ("Reassess in 1 hour 30", 90),
    ("Reevaluar en 1 hora 30 minutos", 90), ("Reassess in 1 h, 30 mL/kg bolus of NS", 60),
    # unchanged
    ("Reassess in 30 min", 30), ("Reassess in 90 min", 90), ("Reassess in 60 minutes", 60),
    ("Reevaluar en 15 minutos", 15), ("Reevaluar HGT en 30 min", 30), ("Monitor BP every 15 min", 15),
    ("Reassess", 0), ("Reassess the patient", 0), ("Reevaluar pH y lactato", 0),
])
def test_the_interval_is_its_minutes(text, minutes):
    assert read(text) == [{"type": "reassessment", "delay_min": minutes}]


def test_an_interval_it_cannot_read_is_asked_never_taken_as_now():
    assert parse_family_actions("Reassess in 30 seconds")["actions"][0]["type"] == "clarification"


def test_one_hour_is_sixty_minutes_on_the_clock_and_in_the_record(engine):
    state, parsed, result = run(engine, "asthma", "asthma_24f", "Reevaluar en 1 h")
    assert parsed["actions"] == [{"type": "reassessment", "delay_min": 60.0}]
    assert result["reassess_delay"] == 60 and result["elapsed_min"] == 60
    # The engine accepts 0 to 120 minutes; three hours is asked, as it was.
    _, _, longer = run(engine, "asthma", "asthma_24f", "Reassess in 3 h")
    assert not longer["executed"] and "0 to 120 minutes" in longer["clarification"]


# --- TD-36: what the patient received before is history -------------------------------------------

@pytest.mark.parametrize("text", [
    "Epinephrine 0.5 mg IM given by EMS", "Aspirin 300 mg given by EMS", "Epinephrine given at 10:32",
    "Adrenalina IM ya administrada por SAMU", "El SAMU dio aspirina 300 mg", "Epi 0.5 mg IM given by EMS",
    "Aspirin 325 mg given by paramedics", "Received aspirin 300 mg en route", "Already received aspirin 300 mg",
    "Aspirin 300 mg administered prehospital", "Aspirina 300 mg dada por SAMU", "Aspirina 300 mg administrada por ambulancia",
    "Recibió aspirina 300 mg antes de llegar", "Ya recibió aspirina 300 mg", "Adrenalina 0,5 mg IM dada por SAMU",
    "Ya recibió adrenalina 0,5 mg IM", "Diphenhydramine 50 mg IV given by EMS", "NS 1 L given en route",
    "SF 1000 ml administrado por SAMU",
])
def test_a_treatment_received_before_is_history_never_given_again(text):
    assert read(text) == []
    assert kept(text) == [("prior_treatment", None)]


# Found by the adversarial review of cycle 9: where it was given before the emergency department,
# and how long ago. Epinephrine and steroids written so were given again and credited to the resident.
@pytest.mark.parametrize("text", [
    "Epinephrine 0.5 mg IM given at OSH", "Adrenalina 0,5 mg IM dada en su centro de salud",
    "Epinephrine 0.3 mg IM given at work", "Epinephrine 0.5 mg IM given at urgent care",
    "Epinephrine 0.5 mg IM given 20 min ago", "Adrenalina 0,5 mg IM hace 20 minutos",
    "Hidrocortisona 200 mg IV dada en su centro de salud", "Methylprednisolone 125 mg IV given at OSH",
    "Epinephrine 0.5 mg IM given at home by husband", "Aspirin 325 mg given at urgent care", "NS 1 L given at OSH",
    "SF 1000 ml pasado en otro hospital", "Recibió adrenalina 0,3 mg IM en el colegio",
])
def test_where_and_how_long_ago_it_was_given_make_it_history_too(text):
    assert read(text) == []
    assert kept(text) == [("prior_treatment", None)]


@pytest.mark.parametrize("text", [
    "Adrenalina 0,5 mg IM (última dosis hace 20 min)", "Salbutamol 5 mg neb (last one 20 min ago)",
    "Give epinephrine 0.5 mg IM at the bedside", "Epinephrine 0.5 mg IM given at the bedside",
    "Hidrocortisona 200 mg IV en su domicilio", "Epinephrine 0.5 mg IM, last dose 20 min ago",
])
def test_an_order_that_names_an_earlier_dose_is_still_the_resident_s(text):
    assert read(text) and ("prior_treatment", None) not in kept(text)


def test_how_long_ago_is_kept_as_its_time():
    detail = parse_family_actions("Adrenalina 0,5 mg IM hace 20 minutos")["future_details"][0]
    assert detail["reported_time"] == "hace 20 minutos"
    assert detail["reported"] == {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}
    assert parse_family_actions("Epinephrine 0.5 mg IM given at OSH")["future_details"][0]["source"] == "at osh"


@pytest.mark.parametrize("text, now", [
    ("Methylprednisolone 125 mg IV given by EMS, epinephrine 0.5 mg IM now", {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}),
    ("Aspirin 300 mg given by EMS, give epinephrine 0.5 mg IM", {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}),
])
def test_the_resident_s_order_beside_it_runs(text, now):
    assert read(text) == [now]
    assert kept(text) == [("prior_treatment", None)]


@pytest.mark.parametrize("text", [
    "Epinephrine 0.5 mg IM", "Give aspirin 300 mg", "Aspirin 300 mg given", "Epinephrine 0.5 mg IM given now",
    "Adrenalina 0,5 mg IM administrada ahora",
])
def test_the_resident_s_own_order_is_still_theirs(text):
    assert read(text) and ("prior_treatment", None) not in kept(text)


def test_what_was_received_is_recorded_with_its_dose_route_and_source():
    detail = parse_family_actions("Epinephrine 0.5 mg IM given by EMS")["future_details"][0]
    assert detail["source"] == "by ems"
    assert detail["reported"] == {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}
    fluid = parse_family_actions("NS 1 L given en route")["future_details"][0]
    assert fluid["reported"] == {"type": "fluid", "volume_ml": 1000.0, "fluid_type": "normal saline"}
    timed = parse_family_actions("Epinephrine given at 10:32")["future_details"][0]
    assert timed["reported_time"] == "10:32" and "reported" not in timed
    assert parse_family_actions("Aspirina 300 mg dada por SAMU")["future_details"][0]["text"] == "Aspirina 300 mg dada por SAMU"


def test_it_is_never_given_nor_the_resident_s_decision(engine):
    state, parsed, result = run(engine, "anaphylaxis", "anaphylaxis_29f", "Epinephrine 0.5 mg IM given by EMS")
    assert not (result.get("action_summaries") or [])
    assert not unexecuted_items.indicated(parsed)
    said, _ = unexecuted_items.messages(parsed)
    assert said == ["Recorded as treatment received before your care, as reported: Epinephrine 0.5 mg IM given by EMS. "
                    "It is part of the history, not your order: nothing was given now."]
    assert language.say(said[0], "es").startswith("Registrado como tratamiento recibido antes de tu atención")
    assert unexecuted_items.trace_labels(parsed) == [
        ("Epinephrine 0.5 mg IM given by EMS", "received before your care, as reported; not given here")]


def test_the_review_s_epinephrine_given_elsewhere_is_not_given_again_and_its_timed_discharge_waits(engine):
    for text in ("Epinephrine 0.5 mg IM given at OSH", "Adrenalina 0,5 mg IM hace 20 minutos"):
        state, parsed, result = run(engine, "anaphylaxis", "anaphylaxis_29f", text)
        assert not (result.get("action_summaries") or []), text
        assert not unexecuted_items.indicated(parsed)
    state, parsed, result = run(engine, "anaphylaxis", "anaphylaxis_29f", "Discharge home with EpiPen in 2 hours")
    assert state.get("disposition") is None
    assert not (state.get("family_state") or {}).get("discharged_at")


# --- TD-33: only blood replaces the haemorrhagic deficit for the overload rule ---------------------

TOURNIQUET = "Apply a tourniquet to the limb."
LIMB = "trauma_limb_hemorrhage_27m"


def course(engine, orders):
    state = encounter(engine, "trauma", LIMB)["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
    return state


def test_crystalloid_before_blood_no_longer_makes_appropriate_blood_an_overload(engine):
    state = course(engine, [TOURNIQUET, "Give 3 L normal saline over 60 minutes.",
                            "Transfuse 2 units packed red blood cells over 20 minutes.", "Reassess in 30 minutes."])
    assert transfusion_overload(state) == 0
    assert state["observable"]["spo2"] >= 96


def test_a_real_overtransfusion_after_the_loss_is_replaced_is_still_one(engine):
    state = course(engine, [TOURNIQUET, "Give 3 L normal saline over 60 minutes.",
                            "Transfuse 4 units packed red blood cells over 40 minutes.", "Reassess in 30 minutes."])
    assert transfusion_overload(state) > 1.5


def test_the_crystalloid_keeps_its_haemodynamic_effect(engine):
    import trauma_hemorrhage
    state = course(engine, [TOURNIQUET, "Give 3 L normal saline over 60 minutes.", "Reassess in 10 minutes."])
    f = state["family_state"]
    # The physiology counts the crystalloid; the overload rule does not.
    assert trauma_hemorrhage.deficit_fraction(f) < trauma_hemorrhage.deficit_fraction(f, blood_only=True)
    assert trauma_hemorrhage.active(f, state)


# --- DF-20 closed, and acs_54m_inferior's TDFC rows ------------------------------------------------

def test_acs_54m_inferior_declares_the_rows_the_approved_decisions_derived():
    import case_assessment_bank
    import tdfc_review
    declared = case_assessment_bank.CASES["acs_54m_inferior"]["objectives"]
    assert {objective: declared[objective]["opportunity"] for objective in ("TD1", "F1", "C1", "C3")} == {
        "TD1": "yes", "F1": "yes", "C1": "yes", "C3": "no"}
    assert declared["C1"]["reviewed"]["decision_group"] == "TDFC-5"
    assert declared["C14"]["opportunity"] == "no"
    for objective in ("TD1", "F1", "C1", "C3"):
        released = declared[objective]["reviewed"]["released"]
        assert (released["on"], released["decision"]) == ("2026-09-29", "DF-20 closed, no change to the case")
    assert tdfc_review.PENDING == {}


def test_none_of_its_rows_rests_on_the_pocus():
    import tdfc_declarations
    for objective, row in tdfc_declarations.DECLARATIONS["acs_54m_inferior"].items():
        evidence = " ".join(row.get("expected_evidence", ())) + " " + row.get("observable_component", "")
        assert "pocus" not in evidence.lower() and "ultrasound" not in evidence.lower(), objective


def test_a_new_encounter_freezes_its_rows_as_declared():
    import evaluation_basis
    import observation_opportunities as opportunities
    record = {"id": "fixture", "challenge_id": "R2-03", "payload": {"session": {}},
              "encounter": {"evaluation_basis": evaluation_basis.freeze("acs_54m_inferior")}}
    view = opportunities.summary(record)
    assert {objective: (view[objective]["state"], view[objective]["rule"]) for objective in ("TD1", "F1", "C1", "C3")} == {
        "TD1": ("yes", "declared"), "F1": ("yes", "declared"), "C1": ("yes", "declared"), "C3": ("no", "declared")}


# --- DF-23 row 4a: the lungs of acs_70f_left_main's POCUS -------------------------------------------

def test_the_left_main_case_s_pocus_lungs_agree_with_its_examination_and_film():
    import clinical_cases
    case = next(variant for variant in clinical_cases.FAMILIES["acs"]["variants"] if variant["id"] == "acs_70f_left_main")
    pocus = case["investigations"]["pocus"]["result"]
    assert pocus["lungs"] == "Scattered B-lines at both bases; no diffuse B-line pattern"
    assert "crackles" in case["examination"]["Respiratory"] and "congestion" in case["investigations"]["chest_xray"]["result"]["report"]
    # Only this case changed: the other coronary cases keep their dry lungs.
    others = [variant for variant in clinical_cases.FAMILIES["acs"]["variants"] if variant["id"] != "acs_70f_left_main"]
    assert all(variant["investigations"]["pocus"]["result"]["lungs"] == clinical_cases._B_LINES_NONE for variant in others)


def test_its_spanish_draft_says_the_same_and_waits_for_review():
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parent / "case_text" / "es" / "acs.json").read_text(encoding="utf-8"))
    passage = data["acs_70f_left_main"]["/investigations/pocus/result/lungs"]
    assert passage == {"en": "Scattered B-lines at both bases; no diffuse B-line pattern",
                       "es": "Líneas B dispersas en ambas bases; sin patrón difuso de líneas B"}
