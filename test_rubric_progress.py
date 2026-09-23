"""A profile across encounters, and the three things it refuses to count.

A draft is not a decision. An unassessed encounter is not a zero. A domain
nobody could observe is not an average of nothing. Each of those is a way a
longitudinal number quietly becomes a grade, and each is tested here.
"""
import pytest

import rubric_progress as progress
from rubric import DOMAIN_IDS, NOT_ASSESSABLE


def review(created_at, scores, *, status="confirmed", events=0, adjusted=None, complete=None):
    if complete is None:
        complete = all(domain in scores and scores[domain] != NOT_ASSESSABLE
                       for domain in DOMAIN_IDS)
    totals = {"critical_events": events, "coverage": {"complete": complete}}
    if complete:
        totals["adjusted"] = adjusted if adjusted is not None else sum(
            value for value in scores.values() if isinstance(value, int))
    return {"status": status, "created_at": created_at, "sequence": 1, "scores": dict(scores),
            "totals": totals, "rubric_version": "1.0-pilot"}


ALL_TWOS = {domain: 2 for domain in DOMAIN_IDS}


def test_nothing_at_all_is_no_encounters_rather_than_a_zero():
    summary = progress.aggregate([])
    assert summary["encounters"] == 0
    assert summary["mean_adjusted"] is None
    assert all(row["mean"] is None for row in summary["domains"].values())
    assert summary["weakest"] is None


def test_a_draft_is_not_part_of_a_profile():
    drafts = [review(1, {domain: 0 for domain in DOMAIN_IDS}, status="draft")]
    assert progress.aggregate(drafts)["encounters"] == 0
    mixed = progress.aggregate(drafts + [review(2, ALL_TWOS)])
    assert mixed["encounters"] == 1
    assert mixed["domains"]["D1"]["mean"] == 2


def test_a_domain_averages_only_where_it_was_assessable():
    summary = progress.aggregate([
        review(1, {"D1": 3, "D2": 2, "D3": 2, "D4": 2, "D5": NOT_ASSESSABLE}),
        review(2, {"D1": 1, "D2": 2, "D3": 2, "D4": 2, "D5": 2}),
    ])
    assert summary["domains"]["D1"]["mean"] == 2.0
    assert summary["domains"]["D1"]["encounters"] == 2
    # The encounter that offered no opportunity contributes nothing, in either
    # direction: not a zero, and not a silent two.
    assert summary["domains"]["D5"]["mean"] == 2.0
    assert summary["domains"]["D5"]["encounters"] == 1


def test_a_domain_never_assessable_has_no_mean_at_all():
    summary = progress.aggregate([review(1, {"D1": 2, "D2": 2, "D3": 2, "D4": 2})] * 1)
    assert summary["domains"]["D5"]["mean"] is None
    assert summary["domains"]["D5"]["encounters"] == 0


def test_the_events_are_counted_and_never_averaged_into_a_domain():
    summary = progress.aggregate([review(1, ALL_TWOS, events=1, adjusted=7),
                                  review(2, ALL_TWOS, events=2, adjusted=4)])
    assert summary["critical_events"] == 3
    assert all(row["mean"] == 2 for row in summary["domains"].values())


def test_only_complete_assessments_enter_the_mean_total():
    summary = progress.aggregate([
        review(1, ALL_TWOS, adjusted=10),
        review(2, {"D1": 3, "D2": 3, "D3": 3, "D4": 3, "D5": NOT_ASSESSABLE}),
    ])
    assert summary["complete_encounters"] == 1
    assert summary["mean_adjusted"] == 10.0
    # The partial one still shapes the per-domain profile.
    assert summary["domains"]["D1"]["mean"] == 2.5


def test_the_last_movement_is_reported_as_a_step_not_as_a_trend():
    summary = progress.aggregate([review(1, ALL_TWOS), review(2, {**ALL_TWOS, "D3": 0})])
    assert summary["domains"]["D3"]["change"] == -2
    assert summary["domains"]["D1"]["change"] == 0
    single = progress.aggregate([review(1, ALL_TWOS)])
    assert single["domains"]["D1"]["change"] is None


def test_the_order_is_the_order_the_encounters_happened_in():
    summary = progress.aggregate([review(9, {**ALL_TWOS, "D1": 1}), review(2, {**ALL_TWOS, "D1": 3})])
    assert summary["domains"]["D1"]["values"] == [3, 1]
    assert summary["domains"]["D1"]["latest"] == 1


def test_the_weakest_domain_is_named_only_when_one_is_lowest():
    clear = progress.aggregate([review(1, {**ALL_TWOS, "D3": 0})])
    assert clear["weakest"] == "D3"
    tied = progress.aggregate([review(1, {**ALL_TWOS, "D3": 0, "D5": 0})])
    assert tied["weakest"] is None


def test_one_encounter_shows_its_own_shape_without_an_average_of_itself():
    assert progress.average_series(progress.aggregate([review(1, ALL_TWOS)])) is None
    assert progress.caption(progress.aggregate([review(1, ALL_TWOS)])) == ""


def test_the_average_series_carries_only_the_domains_that_have_one():
    summary = progress.aggregate([
        review(1, {"D1": 3, "D2": 2, "D3": 2, "D4": 2}),
        review(2, {"D1": 1, "D2": 2, "D3": 2, "D4": 2}),
    ])
    average = progress.average_series(summary)
    assert set(average["values"]) == {"D1", "D2", "D3", "D4"}
    assert average["values"]["D1"] == 2.0


def test_the_caption_says_when_the_domains_rest_on_different_counts():
    summary = progress.aggregate([
        review(1, {"D1": 3, "D2": 2, "D3": 2, "D4": 2, "D5": NOT_ASSESSABLE}),
        review(2, {"D1": 1, "D2": 2, "D3": 2, "D4": 2, "D5": 2}),
    ])
    line = progress.caption(summary)
    assert "2 confirmed encounters" in line
    assert "between 1 and 2" in line
    spanish = progress.caption(summary, "es")
    assert "2 encuentros confirmados" in spanish and "entre 1 y 2" in spanish


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_domain_appears_in_the_table_even_without_a_mean(language):
    rows = progress.table(progress.aggregate([review(1, {"D1": 2})]), language)
    assert [row["domain_id"] for row in rows] == list(DOMAIN_IDS)
    assert rows[0]["mean_label"].startswith("2.00")
    assert rows[-1]["mean_label"] == "—"


def test_a_score_the_rubric_never_produces_is_not_averaged():
    strange = review(1, ALL_TWOS)
    strange["scores"]["D1"] = "3"
    strange["scores"]["D2"] = True
    summary = progress.aggregate([strange])
    assert summary["domains"]["D1"]["mean"] is None
    assert summary["domains"]["D2"]["mean"] is None
    assert summary["domains"]["D3"]["mean"] == 2
