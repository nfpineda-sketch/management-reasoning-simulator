"""Two gaps the embolism case showed when it was played (2026-09-22).

The case authors "Unilateral calf swelling and tenderness on the operated
side" -- the finding that turns "maybe it is anxiety" into a pulmonary
embolism. The engine offered Extremities as a region. The interpreter could not
produce it: "Examine the extremities" was refused, "examina las extremidades"
answered with the capillary refill, and the sentence that listed the available
regions was written by hand and never named it.

And the D-dimer, the first test of the algorithm, did not exist anywhere in the
project. Faculty (2026-09-22): its upper reference is age-adjusted.
"""
import pytest

import language
from clinical_cases import (AGE_ADJUSTED_D_DIMER_FROM, D_DIMER_FIXED_LIMIT, FAMILIES,
                            age_adjusted_d_dimer_limit)
from family_engine import available_regions, execute_family_bundle
from family_parser import _EXAMINATION_REGIONS, parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(state, order):
    return execute_family_bundle(state, parse_family_actions(order))


def findings(state, order):
    result = run(state, order)
    assert result["executed"], result["clarification"]
    return " ".join(str(s.get("label") or "") for s in result["action_summaries"])


@pytest.mark.parametrize("order", [
    "Examine the extremities", "examina las extremidades", "Examine the legs",
    "examino las piernas", "busco edema en la pantorrilla", "reviso los miembros inferiores",
    "palpate the calves",
])
def test_the_calf_finding_can_be_asked_for_in_either_language(engine, order):
    state = encounter(engine, "pulmonary_embolism", "pulmonary_embolism_33f")["state"]
    assert "calf swelling" in findings(state, order)


def test_a_case_with_no_authored_leg_finding_still_answers_with_the_perfusion(engine):
    """Asking for the legs used to give the capillary refill. That must not be lost."""
    state = encounter(engine, "acs", "acs_48m_wellens")["state"]
    assert "Extremities" not in available_regions(state)
    assert "Capillary refill" in findings(state, "Examine the extremities")


def test_the_offered_regions_are_the_ones_the_interpreter_can_read(engine):
    """The list was written by hand and drifted from the table beside it."""
    state = encounter(engine, "pulmonary_embolism", "pulmonary_embolism_33f")["state"]
    refused = run(state, "examine the shoulder")
    assert not refused["executed"]
    offered = refused["clarification"].lower()
    for region, _ in _EXAMINATION_REGIONS:
        assert region.lower() in offered, region


@pytest.mark.parametrize("order", [
    "pido dimero D", "order a d-dimer", "D-dimer", "dímero d", "solicito dimeros d",
])
def test_the_d_dimer_is_a_study_the_interpreter_knows(order):
    assert [a.get("diagnostic") for a in parse_family_actions(order)["actions"]] == ["d_dimer"]


@pytest.mark.parametrize("age, limit", [
    (20, 500), (33, 500), (50, 500), (51, 510), (61, 610), (75, 750), (88, 880),
])
def test_the_upper_reference_is_adjusted_for_age(age, limit):
    assert age_adjusted_d_dimer_limit(age) == limit
    assert age_adjusted_d_dimer_limit(AGE_ADJUSTED_D_DIMER_FROM) == D_DIMER_FIXED_LIMIT


@pytest.mark.parametrize("case", FAMILIES["pulmonary_embolism"]["variants"], ids=lambda c: c["id"])
def test_the_limit_follows_the_patient_rather_than_being_written_beside_them(case):
    """Declared twice they could drift; the limit comes from the case's own age."""
    result = case["investigations"]["d_dimer"]["result"]
    assert result["upper_reference_ng_ml_feu"] == age_adjusted_d_dimer_limit(case["patient"]["age_years"])
    assert result["d_dimer_ng_ml_feu"] > result["upper_reference_ng_ml_feu"]
    assert "does not establish a diagnosis and does not exclude one" in result["report"]


def test_the_d_dimer_is_ordered_where_it_exists_and_refused_where_it_does_not(engine):
    state = encounter(engine, "pulmonary_embolism", "pulmonary_embolism_33f")["state"]
    assert run(state, "pido dimero D")["executed"]
    # An unauthored study is absent, never silently reported as a negative test.
    elsewhere = encounter(engine, "pneumonia", "pneumonia_46f")["state"]
    refused = run(elsewhere, "pido dimero D")
    assert not refused["executed"] and "unavailable" in refused["clarification"]


def test_the_result_reads_in_spanish():
    import family_reports
    case = FAMILIES["pulmonary_embolism"]["variants"][1]
    spanish = language.say(family_reports.format_result(
        "d_dimer", case["investigations"]["d_dimer"]["result"]), "es")
    assert "Dímero D" in spanish
    assert "ajustada por edad" in spanish
    assert "age-adjusted" not in spanish and "Upper reference" not in spanish


def test_a_study_the_bank_carries_can_be_asked_for_and_can_be_named():
    """The same drift, three times in one night.

    A study lives in three lists: the bank's whitelist, the interpreter's
    patterns and the reports' labels. Adding the D-dimer to two of them left
    the third to fail the whole bank. A study a case can carry has to be one a
    resident can request and a report can name.
    """
    from clinical_cases import INVESTIGATION_IDS
    from family_parser import _DIAGNOSTICS
    from family_reports import TEST_LABELS
    assert not set(INVESTIGATION_IDS) - set(_DIAGNOSTICS), "no interpreter pattern"
    assert not set(INVESTIGATION_IDS) - set(TEST_LABELS), "no report label"
