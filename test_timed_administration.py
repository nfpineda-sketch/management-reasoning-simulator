"""Every case accepts an order's volume, dose, route and administration time.

A resident may write "Give 500 mL Ringer's lactate IV over 15 minutes". Bank cases
refused the whole turn ("Timed administration is available in generated
encounters"), and PS001 read "over 30 minutes" as the reassessment interval,
replacing the resident's own "Reassess in 10 minutes".

Timed orders now run evenly over their stated time on the simulation clock. An
order without a stated time behaves exactly as before.
"""
from copy import deepcopy

import pytest

from cognitive_catalog import BIAS_CHALLENGES
from cognitive_generator import generate_cognitive_encounter
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from family_reports import format_administration
from test_curriculum_trajectories import initialize, load_engine


def bank_case(family, seed=1):
    challenge = next(key for key, entry in BIAS_CHALLENGES.items() if family in entry["families"])
    return generate_cognitive_encounter(challenge, {"sim_time": 0, "hidden": {}, "treatments": {}},
                                        family_id=family, seed=seed)["state"]


def bank(state, text):
    return execute_family_bundle(state, parse_family_actions(text))


# Bank cases -----------------------------------------------------------------

def test_the_reported_sepsis_entry_runs_in_a_bank_case():
    state = bank_case("pneumonia")
    result = bank(state, (
        "Probable sepsis from pneumonia with hypoperfusion. My priority is perfusion and oxygenation. "
        "Start oxygen 4 L/min nasal cannula. Give 500 mL Ringer's lactate IV over 15 minutes. "
        "Order blood cultures, lactate, VBG, chest x-ray and POCUS. "
        "Give ceftriaxone 2 g IV and azithromycin 500 mg IV. "
        "Reassess in 15 minutes BP, HR, SpO2, capillary refill and mental status."))
    assert result["executed"], result["clarification"]
    assert result["elapsed_min"] == 15
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(500)


def test_a_timed_bolus_runs_at_its_own_rate_and_continues_into_the_next_turn():
    state = bank_case("pneumonia")
    result = bank(state, "Give 500 mL Ringer's lactate IV over 15 minutes. Reassess in 5 minutes.")
    fluid = next(s for s in result["action_summaries"] if s["type"] == "fluid")
    assert fluid["label"] == "lactated Ringer's 500 mL IV started over 15 min"
    assert (fluid["delivery_starts_at_min"], fluid["delivery_due_at_min"]) == (0, 15)
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(166.7, abs=.1)
    assert state["family_state"]["pending_fluid_ml"] == pytest.approx(333.3, abs=.1)
    bank(state, "Reassess in 10 minutes.")
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(500)
    assert state["family_state"]["pending_fluid_ml"] == 0
    assert state["family_state"]["deliveries"] == []


def test_without_a_reassessment_the_turn_lasts_until_the_infusion_ends():
    state = bank_case("pneumonia")
    assert bank(state, "Give 1000 mL normal saline IV over 60 minutes.")["elapsed_min"] == 60


def test_a_timed_medicine_reports_what_has_gone_in():
    state = bank_case("pneumonia")
    bank(state, "Give ceftriaxone 2 g IV over 30 minutes. Reassess in 10 minutes.")
    record = state["treatments"]["administered_medications"][0]
    assert record["ordered_dose_mg"] == 2000 and record["administration_status"] == "in_progress"
    assert record["dose_mg"] == pytest.approx(666.67, abs=.01)
    assert format_administration(record) == \
        "ceftriaxone 666.667 mg IV · minute 0 · over 30 min · 666.667 of 2000 mg given so far"
    bank(state, "Reassess in 20 minutes.")
    assert record != state["treatments"]["administered_medications"][0]
    record = state["treatments"]["administered_medications"][0]
    assert (record["dose_mg"], record["administration_status"]) == (2000, "completed")


def test_a_timed_medicine_delivers_the_same_total_effect():
    timed, bolus = bank_case("pulmonary_edema"), bank_case("pulmonary_edema")
    bank(timed, "Give furosemide 80 mg IV over 20 minutes. Reassess in 30 minutes.")
    bank(bolus, "Give furosemide 80 mg IV. Reassess in 30 minutes.")
    assert timed["family_state"]["diuretic_dose"] == pytest.approx(bolus["family_state"]["diuretic_dose"])


@pytest.mark.parametrize("family, text", [
    ("gi_bleed", "Transfuse 1 unit packed red cells over 60 minutes. Reassess in 30 minutes."),
    ("hypoglycemia", "Give dextrose 25 g IV over 5 minutes. Reassess in 10 minutes."),
    ("opioid", "Give naloxone 0.4 mg IV over 2 minutes. Reassess in 5 minutes."),
    ("pulmonary_embolism", "Give heparin 5000 units IV over 10 minutes. Reassess in 15 minutes."),
])
def test_every_bank_family_accepts_a_stated_time(family, text):
    result = bank(bank_case(family), text)
    assert result["executed"], result["clarification"]


def test_a_crystalloid_by_a_non_intravenous_route_is_questioned():
    result = bank(bank_case("pneumonia"), "Give 500 mL normal saline PO.")
    assert not result["executed"]
    assert result["clarification"] == "A crystalloid bolus is given IV or IO. Please specify the route."


def test_an_untimed_bank_order_is_unchanged():
    # The whole trajectory must match an order that never mentions route or time.
    with_route, without = bank_case("pneumonia"), bank_case("pneumonia")
    bank(with_route, "Give 1000 mL normal saline IV. Reassess in 30 minutes.")
    bank(without, "Give 1000 mL normal saline. Reassess in 30 minutes.")
    assert with_route["observable"] == without["observable"]
    assert with_route["family_state"] == without["family_state"]


# PS001 ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    return load_engine()


def ps001(engine, *texts):
    session = initialize(engine, engine["INITIAL_STATE"])
    results = []
    for text in texts:
        parsed = engine["clinical_interpreter"](text)
        results.append((parsed, engine["execute_bundle"](parsed)))
    return session["state"], results


def test_ps001_keeps_the_residents_reassessment_interval(engine):
    state, [(parsed, result)] = ps001(engine, "Give 1000 mL normal saline IV over 30 minutes. Reassess in 10 minutes.")
    assert next(a for a in parsed["actions"] if a["type"] == "reassessment")["delay_min"] == 10
    assert result["elapsed_min"] == 10 and state["sim_time"] == 10
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(333.3, abs=.1)


def test_ps001_timed_bolus_finishes_on_the_following_turn(engine):
    state, _ = ps001(engine, "Give 1000 mL normal saline IV over 30 minutes. Reassess in 10 minutes.",
                     "Reassess in 20 minutes.")
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(1000)
    assert state["timed_fluids"] == []


def test_ps001_timed_bolus_reaches_a_comparable_state_to_a_rapid_bolus(engine):
    timed, _ = ps001(engine, "Give 1000 mL normal saline IV over 30 minutes.")
    bolus, _ = ps001(engine, "Give 1000 mL normal saline IV. Reassess in 30 minutes.")
    # The same bag given later has had less time to redistribute, so the states
    # differ a little; the delivered volume and the pressure should not.
    assert timed["sim_time"] == bolus["sim_time"] == 30
    assert timed["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(1000)
    assert abs(timed["observable"]["sbp"] - bolus["observable"]["sbp"]) <= 3


def test_ps001_records_a_medication_time(engine):
    _, [(parsed, result)] = ps001(engine, "Give ceftriaxone 2 g IV over 30 minutes. Reassess in 10 minutes.")
    antibiotic = next(s for s in result["action_summaries"] if s.get("support_type") == "antibiotics")
    assert antibiotic["administration_duration_min"] == 30
    assert result["elapsed_min"] == 10


def test_ps001_asks_when_a_time_cannot_be_given_to_one_order(engine):
    state, [(parsed, result)] = ps001(
        engine, "Give 1000 mL normal saline and ceftriaxone 2 g IV over 30 minutes. Reassess in 10 minutes.")
    assert not result["executed"]
    assert result["clarification"].startswith("Specify one delivery duration")
    assert state["sim_time"] == 0 and state["treatments"]["cumulative_crystalloid_ml"] == 0


def test_generated_cases_keep_their_own_delivery_queue():
    # Generated cases schedule timed orders in generated_delivery. The bank queue
    # must not also hold them, or the treatments panel would list each bag twice.
    from family_engine import _initialize, _order
    state = bank_case("pneumonia")
    _initialize(state)
    state["engine_family"] = "generated"
    action = {"type": "fluid", "volume_ml": 500, "fluid_type": "normal saline", "administration_duration_min": 15}
    summary = _order(state, action)
    assert "deliveries" not in state["family_state"]
    assert (summary["administration_duration_min"], summary["duration_min"]) == (15, 15)
    assert "started over" not in summary["label"]
