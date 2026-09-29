"""The line is a property of the access, not of the bolus (faculty, 2026-09-29: DC2 to DC5).

DC2: every catalogued patient arrives with a cannula in place, said the same in a working
and in a failed configuration; the bedside -- the site on examination, a response that
falls short -- is how the failure is found, and the share that arrives stays technical.
DC4: what runs through the failed cannula reaches the circulation in part, bolus,
infusion and intravenous medicines alike; intramuscular, subcutaneous, intranasal and
oral doses do not go through it. DC3: an intraosseous needle is an access of its own,
placed by a valid intraosseous dose with its minute and never repairing the cannula.
DC5: a running infusion moves to the next line; nothing restarts or repeats.
"""
import json

import pytest

import arrival_brief
import family_engine
import glucose_rescue
import hypoglycemia_catalog as catalog
import language
from catalog_trajectories import launch
from family_engine import current_findings, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

FAILED, WORKING = "hypoglycemia_54m_thiamine", "hypoglycemia_28m"


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, variant, orders):
    state = encounter(engine, "hypoglycemia", variant)["state"]
    summaries = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], (order, result["clarification"])
        summaries += result["action_summaries"]
    return state, summaries


def labels(summaries):
    return [str(s.get("label")) for s in summaries]


def order_summary(summaries, kind):
    return next(s for s in summaries if s.get("type") == kind)


# --- DC2: the same presentation, neutral words ------------------------------------------

def test_every_configuration_declares_the_same_cannula_and_never_its_state():
    said = {}
    for configuration in catalog.configurations():
        state = launch(configuration["id"], "hypoglycemia", allow_review_candidates=True)
        said[configuration["id"]] = arrival_brief.handover(state)
        assert said[configuration["id"]].endswith(glucose_rescue.ARRIVAL_ACCESS_TEXT)
    assert len(said) == 12
    text = glucose_rescue.ARRIVAL_ACCESS_TEXT.lower()
    assert not any(word in text for word in ("fail", "not in the vein", "infiltrat", "paramedic"))


def test_a_new_line_is_placed_and_said_the_same_whether_the_old_one_runs(engine):
    said = {}
    for variant in (FAILED, WORKING):
        state, summaries = course(engine, variant, ["Place a new peripheral IV."])
        said[variant] = (labels(summaries), order_summary(summaries, "vascular_access")["duration_min"])
        assert state["family_state"]["new_line_at"] == 0 and state["family_state"]["iv_access_failed"] is False
    assert said[FAILED] == said[WORKING] == (["peripheral intravenous access placed", glucose_rescue.NEW_LINE_TEXT], 3)
    for text in (glucose_rescue.LEGACY_NEW_ACCESS_TEXT, "peripheral intravenous access replaced"):
        assert text not in said[FAILED][0]


def test_the_share_that_arrives_stays_in_the_technical_record(engine):
    _, summaries = course(engine, FAILED, ["Give 25 g D50 IV. Reassess in 5 minutes.",
                                            "Start D10 at 100 mL/h. Reassess in 10 minutes."])
    assert order_summary(summaries, "dextrose")["delivery"] == {
        "access": "arrival_line", "share_to_circulation": glucose_rescue.FAILED_ACCESS_SHARE, "effect": "proportional"}
    for label in labels(summaries):
        assert "15" not in label and "%" not in label.replace("10%", "") and "reach" not in label, label


# --- discovery: the site on examination, a response that falls short -------------------

def test_the_site_can_be_examined_before_anything_is_given(engine):
    for variant, expected in ((FAILED, "slightly swollen and cool"), (WORKING, "clean, without swelling")):
        state = encounter(engine, "hypoglycemia", variant)["state"]
        assert "family_state" not in state or not state["family_state"]
        assert "Vascular access" in family_engine.available_regions(state)
        assert expected in family_engine.examination_finding(state, "Vascular access")


def test_using_the_failed_line_shows_at_the_site_once_and_stays_on_examination(engine):
    state, summaries = course(engine, FAILED, ["Give 25 g D50 IV. Reassess in 5 minutes.",
                                                "Give thiamine 100 mg IV.", "Reassess in 10 minutes."])
    assert labels(summaries).count(glucose_rescue.FAILED_ACCESS_TEXT) == 1
    assert "swollen, pale, cool and tender" in current_findings(state)["Vascular access"]
    # The response falls short: a quarter of what the ampoule gives through a working line.
    assert state["family_state"]["glucose"] < 50


def test_the_working_line_shows_nothing_and_says_nothing(engine):
    state, summaries = course(engine, WORKING, ["Give 25 g D50 IV. Reassess in 5 minutes."])
    assert glucose_rescue.FAILED_ACCESS_TEXT not in labels(summaries)
    assert "clean, without swelling" in current_findings(state)["Vascular access"]
    assert state["family_state"]["glucose"] > 100


# --- DC4: the access, not the bolus -----------------------------------------------------

def test_the_infusion_through_the_failed_line_arrives_only_in_part(engine):
    failed, _ = course(engine, FAILED, ["Start D10 at 100 mL/h. Reassess in 10 minutes."])
    working, _ = course(engine, WORKING, ["Start D10 at 100 mL/h. Reassess in 10 minutes."])
    assert failed["family_state"]["dextrose_infusion_access"] == "arrival_line"
    assert glucose_rescue.infusion_share(failed["family_state"]) == glucose_rescue.FAILED_ACCESS_SHARE
    assert glucose_rescue.infusion_share(working["family_state"]) == 1.0


@pytest.mark.parametrize("order", ["Give glucagon 1 mg IM.", "Give octreotide 50 mcg SC."])
def test_what_does_not_run_through_a_line_does_not_depend_on_it(engine, order):
    _, summaries = course(engine, FAILED, [order])
    assert "delivery" not in summaries[0]
    assert glucose_rescue.FAILED_ACCESS_TEXT not in labels(summaries)


def test_glucagon_through_the_failed_line_keeps_its_modelled_effect_and_says_why(engine):
    """DC4-F, option B (2026-09-29): absorbed from the tissue as a subcutaneous dose, whose effect is the modelled one."""
    failed, summaries = course(engine, FAILED, ["Give glucagon 1 mg IV. Reassess in 20 minutes."])
    replaced, _ = course(engine, FAILED, ["Place a new peripheral IV.", "Give glucagon 1 mg IV. Reassess in 20 minutes."])
    delivery = order_summary(summaries, "glucagon")["delivery"]
    assert delivery["share_to_circulation"] == glucose_rescue.FAILED_ACCESS_SHARE
    assert delivery["effect"] == "absorbed from the tissue as a subcutaneous dose (DC4-F)"
    assert failed["family_state"]["glucagon_at"] is not None
    assert failed["treatments"]["administered_medications"][-1]["access"] == "arrival_line"
    assert replaced["treatments"]["administered_medications"][-1]["share_to_circulation"] == 1.0


def test_thiamine_is_recorded_as_given_where_it_went_and_does_nothing_else(engine):
    state, summaries = course(engine, FAILED, ["Give thiamine 100 mg IV. Reassess in 5 minutes."])
    record = state["treatments"]["administered_medications"][-1]
    assert (record["agent"], record["access"], record["share_to_circulation"]) == (
        "thiamine", "arrival_line", glucose_rescue.FAILED_ACCESS_SHARE)
    assert order_summary(summaries, "thiamine")["delivery"]["effect"] == "no modelled effect"
    assert state["observable"]["mental_status"] == "Drowsy"


# --- DC3: the intraosseous needle -------------------------------------------------------

def test_a_valid_intraosseous_dose_places_its_needle_with_its_minute_and_no_invented_site(engine):
    state, summaries = course(engine, FAILED, ["Reassess in 4 minutes.", "Give 25 g D50 IO. Reassess in 5 minutes."])
    dose = order_summary(summaries, "dextrose")
    assert dose["io_established"] == {"minute": 4, "placed_by": "this order", "site": None}
    assert dose["delivery"]["share_to_circulation"] == 1.0
    assert dose["duration_min"] == 3 + 3
    assert glucose_rescue.IO_IMPLIED_TEXT.format(minute=4) in labels(summaries)
    # No placement order was written, so none is recorded.
    assert not any(s.get("type") == "vascular_access" for s in summaries)
    assert state["family_state"]["glucose"] > 100
    assert "no site was recorded" in current_findings(state)["Vascular access"]


def test_the_needle_never_repairs_the_cannula(engine):
    state, summaries = course(engine, FAILED, ["Place an IO in the humerus.", "Give 25 g D50 IV. Reassess in 5 minutes."])
    assert state["family_state"]["io_access"] and state["family_state"]["iv_access_failed"]
    assert order_summary(summaries, "dextrose")["delivery"]["access"] == "arrival_line"
    assert state["family_state"]["glucose"] < 50
    assert "(humeral)" in current_findings(state)["Vascular access"]


@pytest.mark.parametrize("order", ["Give glucagon 1 mg IO.", "Give octreotide 50 mcg IO."])
def test_a_route_the_drug_does_not_have_is_not_widened(engine, order):
    state = encounter(engine, "hypoglycemia", FAILED)["state"]
    result = execute_family_bundle(state, parse_family_actions(order))
    assert not result["executed"] and "supported route" in result["clarification"]


# --- DC5: the infusion follows the line -------------------------------------------------

def test_a_running_infusion_moves_to_the_new_line_with_its_access_rate_and_minute(engine):
    state, summaries = course(engine, FAILED, ["Start D10 at 100 mL/h. Reassess in 10 minutes.",
                                                "Place a new peripheral IV. Reassess in 20 minutes."])
    f = state["family_state"]
    assert f["dextrose_infusion_access"] == "new_line"
    assert f["infusion_connections"] == [{"place": "new_line", "minute": 10, "rate_ml_h": 100.0}]
    assert ("The dextrose 10% infusion at 100 mL/h runs through the new cannula in the right forearm from minute 10."
            in labels(summaries))
    # Nothing is repeated to make up for what did not arrive.
    assert sum(s.get("type") == "dextrose" for s in summaries) == 0
    assert f["dextrose_g"] == 0


def test_a_stopped_infusion_stays_stopped(engine):
    state, summaries = course(engine, FAILED, ["Start D10 at 100 mL/h. Reassess in 10 minutes.",
                                                "Stop the D10.", "Place a new peripheral IV."])
    assert not state["family_state"]["dextrose_infusion_ml_h"]
    assert "infusion_connections" not in state["family_state"]


def test_an_intraosseous_needle_also_takes_the_infusion(engine):
    state, _ = course(engine, FAILED, ["Start D10 at 100 mL/h. Reassess in 5 minutes.", "Give 25 g D50 IO."])
    assert state["family_state"]["dextrose_infusion_access"] == "io"
    assert glucose_rescue.infusion_share(state["family_state"]) == 1.0


# --- what stays as it was ---------------------------------------------------------------

def test_an_encounter_begun_under_1_0_keeps_its_rule(engine):
    state = encounter(engine, "hypoglycemia", FAILED)["state"]
    execute_family_bundle(state, parse_family_actions("Reassess in 1 minute."))
    state["family_state"].pop("arrival_line")
    result = execute_family_bundle(state, parse_family_actions("Coloco una vía intraósea"))
    assert state["family_state"]["iv_access_failed"] is False
    assert glucose_rescue.LEGACY_NEW_ACCESS_TEXT in labels(result["action_summaries"])
    assert "Vascular access" not in current_findings(state)


def test_other_families_are_untouched(engine):
    state = encounter(engine, "trauma", "trauma_limb_hemorrhage_27m")["state"]
    execute_family_bundle(state, parse_family_actions("Reassess in 1 minute."))
    assert "arrival_line" not in state["family_state"]
    assert not arrival_brief.handover(state).endswith(glucose_rescue.ARRIVAL_ACCESS_TEXT)


def test_the_room_says_it_in_spanish(engine):
    state, summaries = course(engine, FAILED, ["Start D10 at 100 mL/h. Reassess in 10 minutes.",
                                                "Give 25 g D50 IO.", "Place a new peripheral IV."])
    texts = [glucose_rescue.ARRIVAL_ACCESS_TEXT, current_findings(state)["Vascular access"],
             *[label for label in labels(summaries) if label[0].isupper() and "Dextrose 10% at" not in label]]
    for text in texts:
        spanish = language.say(text, "es")
        assert not any(word in spanish for word in ("cannula", "forearm", "needle", "infusion", "runs")), spanish
    assert json.dumps(texts)
