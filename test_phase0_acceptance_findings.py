"""Phase 0 (0J, 0K): what the acceptance battery found, fixed or declared, and kept fixed.

Pre-pilot measurement safety, 2026-10-06. Running every bank case through the battery found:

* orders that still vanished: an order with no dose and no word any vocabulary knew
  ("Arrange urgent haemodialysis"), verbs the ledger did not take for orders ("Keep",
  "Organize", "Turn off"), the name of an order alone ("- Aspirin", "Cefepime now",
  "Heparin drip": TD-45 (a)), and an order written after an intention ("We should start
  heparin", "Necesitamos hemocultivos"), behind a filler pattern that cut the front of words
  ("ecg" read as "cg");
* orders recorded without the words they were written with (a call, a reader's question);
* "Stop the epinephrine infusion" refused: the reader returned an adjustment of no named
  infusion, and the infusion ran on;
* an order the simulator did not carry out quoted, on the page, with another order's words;
* a reassessment written with an order no answer can complete never ran, and the page said
  "held until you answer" when nothing was held;
* a bradycardia's arrest read from a rate the monitor did not show: a patient on adrenaline
  shown at 38/min arrested from a hidden rate of 20;
* the anaphylaxis arrest said adrenaline had never been given to a resident who gave it;
* a treatment's event without the orders it followed, on the page;
* the haemothorax bleeding to an arrest whatever was done, declared a preventable one;
* and the case the freeze excludes, still drawable for a resident.
"""
import random

import pytest

import encounter_generator
import event_provenance
import order_ledger
import order_pipeline
import pilot_acceptance as acceptance
import pilot_freeze
import time_semantics
from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine


def _coverage(text):
    parsed = time_semantics.apply(text, parse_family_actions(text))
    order_pipeline.apply_safe_defaults(parsed, text)
    found = order_ledger.coverage(text, parsed)
    return [item["text"] for item in found["unaccounted"] + found["held"]], parsed


# --- no order vanishes ----------------------------------------------------------------------
@pytest.mark.parametrize("text, missed", [
    ("Arrange urgent hemodialysis.", "Arrange urgent hemodialysis"),
    ("Give calcium gluconate 3 g IV. Arrange urgent hemodialysis. Reassess in 15 minutes.",
     "Arrange urgent hemodialysis"),
    ("Organize emergency dialysis.", "Organize emergency dialysis"),
    ("Organizar diálisis de urgencia.", "Organizar diálisis de urgencia"),
    ("Keep him NPO.", "Keep him NPO"),
    ("Hold pressure meds.", "Hold pressure meds"),
])
def test_an_order_no_vocabulary_knows_is_not_understood_never_gone(text, missed):
    flagged, _ = _coverage(text)
    assert missed in flagged, flagged


@pytest.mark.parametrize("text, missed", [
    # Names of orders with no verb and no dose: a list item, a name with "now" or "drip".
    ("- Aspirin\n- Ticagrelor 180 mg PO\n- ECG now", "Aspirin"),          # TD-45 (a)
    ("Aspirin, heparin 5000 units IV, ECG", "Aspirin"),                     # TD-45 (a)
    ("Plan:\n- Cefepime\n- Vasopressin\n- Bedside echo", "Vasopressin"),
    ("Cefepime and vancomycin.", "vancomycin"),
    ("Heparin drip.", "Heparin drip"),
    ("Bicarbonate 1 amp.", "Bicarbonate 1 amp"),
    ("CPR now.", "CPR now"),
    ("1. Cefepime\n2. Vancomycin", "Vancomycin"),
    # What a resident writes before the order itself: an intention, a need, a wish.
    ("We should start heparin.", "heparin"),
    ("Need a chest X-ray.", "chest X-ray"),
    ("Quiero una radiografía de tórax.", "radiografía de tórax"),
    ("Necesitamos hemocultivos.", "hemocultivos"),
    ("Le daría cefepima.", "cefepima"),
    ("Me gustaría iniciar noradrenalina.", "noradrenalina"),
    ("Debemos llamar a cirugía.", "llamar a cirugía"),
])
def test_the_name_of_an_order_alone_is_an_order_never_gone(text, missed):
    flagged, _ = _coverage(text)
    assert missed in flagged, flagged


@pytest.mark.parametrize("text", [
    "On aspirin and clopidogrel.", "Home medications: metoprolol and aspirin.", "Received aspirin in the ambulance.",
    "No aspirin.", "Aspirin?", "Troponin negative.", "Lactate 4.2.", "ECG: ST elevation in II, III and aVF.",
    "Allergic to amoxicillin.", "Alergia a la amoxicilina.", "I think this is sepsis and cefepime would cover it.",
    "Aspirin was given by EMS.", "Already on heparin.", "Lactate pending.", "ECG done.",
    "Troponin elevated, ECG with ST depression.", "Medicamentos habituales: metformina.",
    "We should see the lactate fall.", "I want to rule out PE.", "We need to think about sepsis.",
    "So far 2 units PRBC and 2 L crystalloid.", "Can we get a CT?",
])
def test_a_name_in_a_note_a_result_or_the_history_is_not_an_order(text):
    flagged, _ = _coverage(text)
    assert flagged == [], flagged


@pytest.mark.parametrize("text", [
    "Admit to the ICU.", "Repeat vitals.", "Repeat the blood pressure.", "Transfundir 2 U GR, pasar en 2 hrs c/u",
    "Call cardiology.", "Llamo a hemodinamia.", "Decrease FiO2 to 40%.", "Suspende el suero.", "Deja regimen cero.",
    "Hospitalizalo en la unidad coronaria.", "Continue monitoring.",
])
def test_an_order_the_reader_did_read_is_not_flagged(text):
    flagged, parsed = _coverage(text)
    assert not [item for item in flagged if "?" not in item], (flagged, parsed.get("actions"))


def test_the_page_receipt_names_the_order_and_says_nothing_was_given():
    turn = order_pipeline.open_turn("Arrange urgent hemodialysis.", parse_family_actions("Arrange urgent hemodialysis."),
                                    submission_id="s", entry_point="free_text", minute=0)
    [order] = turn["orders"]
    assert order["class"] == "unrecognized" and order["span"] == "Arrange urgent hemodialysis"
    assert order_pipeline.check(turn) == []


# --- a reassessment waits only for what an answer can complete --------------------------------
def test_a_reassessment_written_with_an_order_no_answer_completes_runs():
    refused = acceptance.Encounter("acs_54m_inferior")
    entry = refused.order("Give aspirin 300 mg PO. Stop the infusion. Reassess in 5 minutes.")
    assert {order["class"]: order["fate"] for order in entry["orders"]} == {
        "aspirin": "EXECUTED", "infusion_adjustment": "RECORDED_NOT_MODELLED", "reassessment": "EXECUTED"}
    assert refused.minute == 5
    # An answer can complete the bolus: the reassessment waits with it, as before.
    waiting = acceptance.Encounter("pneumonia_46f")
    entry = waiting.order("Give normal saline. Reassess in 15 minutes.")
    assert [order["fate"] for order in entry["orders"]] == ["HELD_CLARIFICATION", "HELD_CLARIFICATION"]
    assert waiting.minute == 0


def test_the_page_never_says_held_when_no_answer_is_awaited():
    split = {"run": [{"type": "aspirin"}], "held": [({"type": "infusion_adjustment"}, "refused", "question")],
             "question": "No infusion is running. Name the drug and its starting rate.", "no_pending": True}
    text = order_pipeline.held_message(split, lambda parsed: [a["type"] for a in parsed["actions"]])
    assert "PART OF THIS ORDER WAS NOT CARRIED OUT" in text and "Held until you answer" not in text
    assert "Not carried out: **infusion_adjustment**" in text and split["question"] in text
    split["no_pending"] = False
    assert "Held until you answer" in order_pipeline.held_message(split, lambda parsed: [a["type"] for a in
                                                                                         parsed["actions"]])


# --- an infusion is stopped when it is told to stop -----------------------------------------
@pytest.mark.parametrize("variant, start, stop, key", [
    ("anaphylaxis_29f", "Start epinephrine infusion at 0.1 mcg/kg/min.", "Stop the epinephrine infusion.", "epinephrine"),
    ("bradycardia_ccb_68m", "Start epinephrine infusion at 10 mcg/min.", "Stop the adrenaline infusion.", "epinephrine"),
    ("hypoglycemia_28m", "Start a dextrose 10% infusion at 100 mL/h.", "Stop the dextrose infusion.",
     "dextrose_infusion_ml_h"),
    # TD-45 (g), the reader's own example: the reader is unchanged; the room names the infusion.
    ("hypoglycemia_28m", "Start a dextrose 10% infusion at 100 mL/h.", "Suspender la infusión de glucosado.",
     "dextrose_infusion_ml_h"),
])
def test_stop_the_infusion_stops_the_infusion_its_words_name(variant, start, stop, key):
    encounter = acceptance.Encounter(variant)
    encounter.order(start + " Reassess in 5 minutes.")
    assert float(encounter.state["family_state"][key]) > 0
    entry = encounter.order(stop + " Reassess in 5 minutes.")
    assert float(encounter.state["family_state"][key] or 0) == 0
    assert [order["fate"] for order in entry["orders"]] == ["EXECUTED", "EXECUTED"]


def test_an_order_not_carried_out_is_quoted_with_its_own_words():
    text = "Give 50 mL of D50 IV. Stop the infusion. Reassess in 5 minutes."
    turn = order_pipeline.open_turn(text, time_semantics.apply(text, parse_family_actions(text)),
                                    submission_id="s", entry_point="free_text", minute=0)
    assert [(order["class"], order["span"]) for order in turn["orders"]] == [
        ("dextrose", "Give 50 mL of D50 IV"), ("infusion_adjustment", "Stop the infusion"),
        ("reassessment", "Reassess in 5 minutes")]


@pytest.mark.parametrize("text, spans", [
    ("Call cardiology and give aspirin 300 mg.", ["Call cardiology", "give aspirin 300 mg"]),
    ("Pneumonia. Start high-flow nasal oxygen, give ceftriaxone 2 g IV.",
     ["Start high-flow nasal oxygen", "give ceftriaxone 2 g IV"]),
    ("Heparin running at 1000 units/h.", ["Heparin running at 1000 units/h"]),
    ("I expect the vital signs to improve. Give normal saline 1 L. Check the blood pressure in 15 minutes.",
     ["Give normal saline 1 L", "Check the blood pressure in 15 minutes"]),
])
def test_every_order_keeps_the_words_it_was_written_with(text, spans):
    turn = order_pipeline.open_turn(text, time_semantics.apply(text, parse_family_actions(text)),
                                    submission_id="s", entry_point="free_text", minute=0)
    written = [order["span"] for order in turn["orders"]]
    assert all(written) and all(span in written for span in spans), written


def test_an_order_beside_the_answer_to_a_question_is_said_not_run_not_misunderstood():
    text = "1000 mL, and give ceftriaxone 2 g IV."
    answer = order_pipeline.open_turn(text, {"actions": []}, submission_id="s", entry_point="clarification_answer",
                                      minute=0)
    [order] = answer["orders"]
    assert order["fate"] == "UNRECOGNIZED" and "answer to the question above" in order["receipt"]
    assert "other words" not in order["receipt"]
    fresh = order_pipeline.open_turn(text, {"actions": []}, submission_id="t", entry_point="free_text", minute=0)
    assert "Not understood" in fresh["orders"][0]["receipt"]


def test_the_front_of_a_word_is_never_cut_as_a_filler():
    for word in ("ecg now", "enoxaparin", "epinephrine 1 mg", "solicito lactato", "yeso"):
        assert order_ledger._head(word) == word


def test_an_adjustment_that_names_two_infusions_is_left_to_the_engine_s_refusal():
    parsed = {"actions": [{"type": "infusion_adjustment", "operation": "stop"}]}
    order_pipeline.name_the_infusion("Stop the epinephrine and norepinephrine infusions.", parsed)
    assert parsed["actions"][0]["type"] == "infusion_adjustment"


# --- the arrest is the rate the monitor shows -----------------------------------------------
@pytest.mark.parametrize("variant, antidote", [
    ("bradycardia_ccb_68m", "Give calcium chloride 1 g IV. Give glucagon 5 mg IV."),
    ("bradycardia_bb_54f", "Give glucagon 5 mg IV. Give calcium chloride 1 g IV."),
    ("bradycardia_hyperk_63m", "Give calcium gluconate 3 g IV."),
    ("bradycardia_avb3_78f", "Give atropine 1 mg IV."),
])
def test_an_adrenaline_infusion_the_monitor_shows_holds_off_the_arrest(variant, antidote):
    with_it = acceptance.Encounter(variant)
    with_it.order(antidote + " Reassess in 15 minutes.")
    with_it.order("Start epinephrine infusion at 10 mcg/min. Reassess in 30 minutes.")
    with_it.wait_until(165)
    assert not with_it.arrested and with_it.minute == 165
    without = acceptance.Encounter(variant)
    without.order(antidote + " Reassess in 15 minutes.")
    without.wait_until(165)
    assert without.arrested
    # No arrest is ever announced while the monitor shows a rate above the arrest rate.
    for entry in without.entries:
        shown = entry["observable"]
        assert shown.get("pulse_present") is False or shown["hr"] > 20


# --- the anaphylaxis arrest says what happened -------------------------------------------------
def _labels(encounter):
    return [str(s.get("label") or "") for entry in encounter.entries for s in entry["action_summaries"]]


def test_the_anaphylaxis_arrest_after_a_dose_that_wore_off_says_so():
    import anaphylaxis_reaction
    treated = acceptance.Encounter("anaphylaxis_29f")
    treated.order("Give epinephrine 0.5 mg IM. Reassess in 15 minutes.")
    treated.wait_until(120, step=15)
    assert treated.arrested
    assert anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT in _labels(treated)
    assert anaphylaxis_reaction.ARREST_TEXT not in _labels(treated)
    untreated = acceptance.Encounter("anaphylaxis_29f").wait_until(60)
    assert anaphylaxis_reaction.ARREST_TEXT in _labels(untreated)


def test_a_repeated_dose_keeps_the_waning_reaction_from_the_arrest():
    encounter = acceptance.Encounter("anaphylaxis_29f")
    encounter.order("Give epinephrine 0.5 mg IM. Give 1 liter of normal saline IV. Reassess in 30 minutes.")
    for _ in range(5):
        encounter.order("Give epinephrine 0.5 mg IM. Reassess in 30 minutes.")
    assert not encounter.arrested


# --- provenance names what it can and declares what it cannot ---------------------------------
def test_a_treatment_event_names_the_executed_orders_of_its_cause_from_the_ledger():
    events = [{"kind": "transfusion_overload", "flag": "transfusion_overload_at", "minute": 30,
               "cause_class": "RESIDENT_TREATMENT", "source_order_ids": []}]
    orders = [{"order_id": "a:0", "class": "blood", "fate": "EXECUTED", "written_at_min": 0},
              {"order_id": "a:1", "class": "fluid", "fate": "EXECUTED", "written_at_min": 0},
              {"order_id": "b:0", "class": "blood", "fate": "UNRECOGNIZED", "written_at_min": 10},
              {"order_id": "c:0", "class": "blood", "fate": "EXECUTED", "written_at_min": 45}]
    [event] = event_provenance.attribute(events, orders)
    assert event["source_order_ids"] == ["a:0"]


def test_the_haemothorax_arrest_is_the_engine_s_limitation_and_the_limb_arrest_is_preventable():
    chest = acceptance.Encounter("trauma_hemothorax_41m")
    chest.order("Insert a left chest tube. Transfuse 2 units of packed red blood cells. Reassess in 15 minutes.")
    chest.wait_until(120, step=15)
    [arrest] = [e for entry in chest.entries for e in entry["events"] if e["kind"] == "cardiac_arrest"]
    assert (arrest["cause_class"], arrest["preventability"]) == ("ENGINE_LIMITATION", "NOT_PREVENTABLE_IN_SIMULATOR")
    limb = acceptance.Encounter("trauma_limb_hemorrhage_27m").wait_until(30)
    [arrest] = [e for entry in limb.entries for e in entry["events"] if e["kind"] == "cardiac_arrest"]
    assert (arrest["cause_class"], arrest["preventability"]) == ("NATURAL_DISEASE", "PREVENTABLE")


# --- the freeze ------------------------------------------------------------------------------
@pytest.mark.parametrize("challenge", ["R2-04", "R2-05"])
def test_the_excluded_case_is_never_drawn_for_a_resident(challenge):
    initial = load_engine()["INITIAL_STATE"]
    drawn = set()
    for seed in random.Random(7).sample(range(2**31), 40):
        state = encounter_generator.generate_encounter(challenge, initial, seed=seed, generation_mode="authored")["state"]
        drawn.add(state["encounter_spec"]["variant_id"])
    assert "trauma_limb_hemorrhage_27m" in drawn
    assert not drawn & set(pilot_freeze.excluded_variants())


def test_the_excluded_case_cannot_be_directed_to_a_resident_and_stays_in_the_sandbox():
    import encounter_directives
    offered = {variant for variant, *_ in encounter_directives.case_options("R2-05")}
    assert "trauma_limb_hemorrhage_27m" in offered and "trauma_hemothorax_41m" not in offered
    state = encounter_generator.generate_encounter("R2-05", load_engine()["INITIAL_STATE"], seed=17,
                                                   generation_mode="authored",
                                                   variant_id="trauma_hemothorax_41m")["state"]
    assert state["encounter_spec"]["variant_id"] == "trauma_hemothorax_41m"


def test_every_bank_case_has_a_decision_and_every_limitation_is_declared():
    for variant, case in pilot_freeze.CASES.items():
        assert case["status"] in pilot_freeze.STATUSES, variant
        for item in pilot_freeze.limitations(variant):
            assert item["text"] and item["guard"], (variant, item["id"])
    assert pilot_freeze.excluded_variants() == ["trauma_hemothorax_41m"]
    assert set(pilot_freeze.EXCLUDED_LEGACY_CHALLENGES) == {"R1-03", "R1-04", "R2-01"}
