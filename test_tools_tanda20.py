"""The twenty-scenario batch: its plan holds together, and its rehearsal runs.

The rehearsal is not evidence for the batch (the batch must run on the
development app with the real accounts); it is how a script, or the page, is
found to be broken before a paid encounter is spent. One script is played here
end to end through the real page so the tool cannot rot unnoticed.
"""
from collections import Counter

import pytest

import tanda20
import tools_tanda20
from curriculum import CHALLENGES


def test_twenty_different_scenarios_in_the_distribution_the_faculty_asked_for():
    cases = [script["case_id"] for script in tanda20.SCRIPTS]
    assert len(cases) == 20 and len(set(cases)) == 20
    assert Counter(script["category"] for script in tanda20.SCRIPTS) == {
        "bueno": 4, "largo": 4, "recuperacion": 4, "equivocado": 4, "deficiente": 2, "alternativa": 2}
    assert len({script["family"] for script in tanda20.SCRIPTS}) >= 10


def test_each_scenario_is_launched_under_a_challenge_that_offers_its_family():
    for script in tanda20.SCRIPTS:
        families = CHALLENGES[script["challenge"]].get("families") or ()
        assert script["family"] in families, (script["case_id"], script["challenge"])


def test_every_case_declares_what_the_rubric_reads():
    for row in tools_tanda20.plan():
        assert row["declared_events"], row["case_id"]


def test_the_steps_are_ones_a_resident_can_take():
    known = {"ask", "examine", "order", "answer", "complete", "cancel", "recover"}
    for script in tanda20.SCRIPTS:
        assert {step[0] for step in script["steps"]} <= known, script["case_id"]
        assert set(script["reflection"]) == {"working_model_update", "priority_trigger",
                                             "alternative_action", "expected_response_reassessment"}


def test_one_script_rehearses_end_to_end_through_the_real_page(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = tools_tanda20.rehearse(tanda20.BY_NUMBER[7], tmp_path)
    assert result["stopped"] is None, result
    assert result["drawn_case"] == "renal_colic_34m"
    assert not result.get("unanticipated_holds") and not result.get("answers_not_needed")
    assert result["attempt_status"] == "completed" and result["review_completed"]
    # The run says what it was: a synthetic test, never a resident's autonomy.
    assert result["execution_declared"] == "synthetic_agent"
    assert result["decisions_executed"] >= 4 and not result["not_executed"]
