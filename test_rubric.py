"""The arithmetic of the rubric, which is code's and never a model's.

Pilot rubric 1.0. The risks these check are the ones the design carries: a
subtotal presented as a total, a "not assessable" quietly read as a zero, the
same event penalised twice, and a safety alert that disappears behind a high
score.
"""
import pytest

import rubric


FULL = {"D1": 2, "D2": 3, "D3": 2, "D4": 3, "D5": 2}


def test_a_complete_assessment_totals_its_five_domains():
    result = rubric.score(FULL)
    assert result["base"] == 12 and result["maximum"] == 15
    assert result["adjusted"] == 12 and result["penalty"] == 0
    assert result["coverage"] == {"assessed": 5, "total": 5, "complete": True}
    assert result["version"] == rubric.VERSION


def test_a_confirmed_event_costs_three_and_the_total_never_goes_below_zero():
    one = rubric.score(FULL, [{"event_id": "e1", "status": "confirmed"}])
    assert one["penalty"] == rubric.CRITICAL_EVENT_PENALTY == 3
    assert one["adjusted"] == 9 and one["base"] == 12

    floor = rubric.score({"D1": 0, "D2": 0, "D3": 1, "D4": 0, "D5": 1},
                         [{"event_id": "a", "status": "confirmed"},
                          {"event_id": "b", "status": "confirmed"}])
    assert floor["base"] == 2 and floor["penalty"] == 6 and floor["adjusted"] == 0


def test_the_same_event_is_not_penalised_twice():
    """One event across several turns or domains is still one event."""
    repeated = [{"event_id": "e1", "status": "confirmed"},
                {"event_id": "e1", "status": "confirmed"},
                {"event_id": "e1", "status": "confirmed"}]
    assert rubric.score(FULL, repeated)["penalty"] == 3
    assert rubric.score(FULL, repeated)["critical_events"] == 1


def test_only_a_confirmed_event_penalises():
    proposed = [{"event_id": "e1", "status": "proposed"},
                {"event_id": "e2", "status": "dismissed"},
                {"event_id": "e3"}]
    result = rubric.score(FULL, proposed)
    assert result["penalty"] == 0 and result["critical_events"] == 0
    assert result["adjusted"] == result["base"] == 12


def test_a_partial_assessment_has_no_comparable_total():
    partial = rubric.score({**FULL, "D4": rubric.NOT_ASSESSABLE},
                           [{"event_id": "e1", "status": "confirmed"}])
    assert partial["base"] is None and partial["adjusted"] is None and partial["maximum"] is None
    # The events and their penalty are kept and reported.
    assert partial["penalty"] == 3 and partial["critical_events"] == 1
    assert partial["coverage"] == {"assessed": 4, "total": 5, "complete": False}
    # The subtotal exists but is never normalised into a total.
    assert partial["partial_subtotal"] == 9
    assert "4 of 5 domains" in rubric.headline(partial)
    assert "/15" not in rubric.headline(partial)


def test_not_assessable_is_not_a_zero():
    absent = rubric.score({**FULL, "D4": rubric.NOT_ASSESSABLE})
    zero = rubric.score({**FULL, "D4": 0})
    assert absent["coverage"]["assessed"] == 4 and zero["coverage"]["assessed"] == 5
    assert zero["base"] == 9 and absent["base"] is None
    assert absent["per_domain"]["D4"] == rubric.NOT_ASSESSABLE


def test_the_safety_alert_stays_visible_behind_a_high_score():
    top = rubric.score({d: 3 for d in rubric.DOMAIN_IDS},
                       [{"event_id": "e1", "status": "confirmed"}])
    line = rubric.headline(top)
    assert "Base 15/15" in line and "-3" in line and "critical event" in line
    assert "Penalización −3" in rubric.headline(top, "es")


@pytest.mark.parametrize("scores", [
    {"D1": 4}, {"D1": -1}, {"D1": "2"}, {"D1": True}, {"D1": None}, {"DX": 2},
])
def test_a_score_outside_the_rubric_is_refused(scores):
    with pytest.raises(rubric.RubricError):
        rubric.score(scores)


def test_every_domain_has_four_descriptors_and_both_titles():
    assert len(rubric.DOMAIN_IDS) == 5
    for domain in rubric.DOMAIN_IDS:
        levels = rubric.domain_levels(domain)
        assert sorted(levels) == [0, 1, 2, 3]
        assert all(str(text).strip() for text in levels.values())
        assert rubric.DOMAINS[domain]["title"] and rubric.DOMAINS[domain]["title_es"]


def test_the_version_and_the_penalty_are_declared_in_one_place():
    """An update must not silently regrade earlier encounters."""
    assert rubric.VERSION == "1.0-pilot"
    assert rubric.CRITICAL_EVENT_PENALTY == 3
    assert rubric.VERSION in rubric.PILOT_NOTICE and rubric.VERSION in rubric.PILOT_NOTICE_ES
    for notice in (rubric.PILOT_NOTICE, rubric.PILOT_NOTICE_ES):
        assert "ACGME" in notice          # says what it is not
