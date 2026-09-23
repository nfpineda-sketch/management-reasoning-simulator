"""What every encounter says before the resident asks anything.

Faculty request of 2026-09-23: every case should carry something at the start
that lets the student place themselves in a line of thinking. Not the vital
signs, which are on the monitor; not how the patient looks, which is in the
photograph; but who this is, what brought them, and a short account of how it
began.

The line this draws is the same one the rubric now draws: what you are told at
the door, and what you have to ask for. Handing over the medication list would
remove the omission the rubric was told to score on the same day.
"""
import pytest

import arrival_brief
from clinical_cases import FAMILIES, variant_by_id


CASES = [case["id"] for family in FAMILIES.values() for case in family["variants"]]


def state_for(case_id):
    return {"encounter_spec": {"clinical_case": variant_by_id(case_id)}}


@pytest.mark.parametrize("case_id", CASES)
def test_every_case_hands_over_a_complaint_and_a_course(case_id):
    item = arrival_brief.brief(state_for(case_id))
    assert item["complaint"].strip(), case_id
    assert item["course"].strip(), case_id


@pytest.mark.parametrize("case_id", CASES)
def test_the_handover_is_exactly_the_two_fields_and_nothing_else(case_id):
    case = variant_by_id(case_id)
    text = arrival_brief.handover(state_for(case_id))
    for field, values in case["history"].items():
        if field in arrival_brief.HANDED_OVER:
            continue
        for value in values:
            # Not one sentence of the history a resident has to ask for.
            assert str(value) not in text, (case_id, field)


@pytest.mark.parametrize("case_id", CASES)
def test_the_medications_are_never_handed_over(case_id):
    # The case that made this a rule: a sulfonylurea nobody asked about.
    text = arrival_brief.handover(state_for(case_id)).lower()
    for value in variant_by_id(case_id)["history"].get("medications", []):
        assert str(value).lower() not in text


@pytest.mark.parametrize("case_id", CASES)
def test_no_vital_sign_and_no_appearance_reaches_the_handover(case_id):
    text = arrival_brief.handover(state_for(case_id)).lower()
    for word in ("mmhg", "bpm", "spo2", "saturation", "/min", "capillary refill",
                 "blood pressure", "heart rate", "respiratory rate"):
        assert word not in text, (case_id, word)


@pytest.mark.parametrize("case_id", CASES)
def test_who_is_telling_the_story_is_named_when_it_is_not_the_patient(case_id):
    case = variant_by_id(case_id)
    source = str(case.get("history_source") or "")
    text = arrival_brief.handover(state_for(case_id))
    if source and source.strip().lower() not in {"patient", "the patient"}:
        assert f"History from: {source}." in text
    else:
        assert "History from:" not in text


def test_the_withheld_fields_are_reported_so_the_line_is_visible():
    item = arrival_brief.brief(state_for("hypoglycemia_76f"))
    assert "medications" in item["withheld"]
    assert "chief_complaint" not in item["withheld"]
    assert "onset" not in item["withheld"]


def test_a_case_with_no_authored_history_hands_over_nothing_rather_than_failing():
    assert arrival_brief.handover({"encounter_spec": {"clinical_case": {}}}) == ""
    assert arrival_brief.handover({}) == ""
    assert arrival_brief.handover(None) == ""
    assert arrival_brief.handover({"encounter_spec": {"clinical_case": {"history": "not a map"}}}) == ""


def test_the_handover_follows_the_presentation_rather_than_replacing_it():
    text = arrival_brief.handover(state_for("asthma_24f"))
    assert text.startswith("\n\n")
    assert "My chest is tight" in text


def test_a_generated_encounter_with_a_history_gets_one_too():
    # Nothing here is specific to the bank: any case that authors the two
    # fields hands them over.
    state = {"encounter_spec": {"clinical_case": {
        "history_source": "Neighbour",
        "history": {"chief_complaint": ["He says his leg gave way."],
                    "onset": ["It began an hour ago."],
                    "medications": ["He takes warfarin."]}}}}
    text = arrival_brief.handover(state)
    assert "He says his leg gave way." in text and "It began an hour ago." in text
    assert "History from: Neighbour." in text
    assert "warfarin" not in text


def test_the_encounter_opens_with_the_presentation_and_the_handover_together():
    # No environment is touched: setting MRS_OFFLINE_CASES here would withhold
    # the provider key for every test that runs after this one in the process.
    from test_cognitive_encounters import encounter
    from test_curriculum_trajectories import load_engine
    engine = load_engine()
    generated = encounter(engine, "hypoglycemia", "hypoglycemia_76f")
    opening = generated["presentation"] + arrival_brief.handover(generated["state"])
    assert generated["presentation"] in opening
    assert "Her intake has been poor for two days" in opening
    assert "glimepiride" not in opening
