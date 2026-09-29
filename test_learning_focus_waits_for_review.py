"""§154AB (faculty, 2026-09-29): a resident reads an encounter's learning focus after review.

Not at the close, not in the saved review, not in the copy of their record: once a
faculty member has reviewed the encounter -- a confirmed rubric or a confirmed
observation, the rule the resident's own pages already publish by. Faculty keep it.
"""
import pytest

import curriculum_runtime
import resident_pages
import resident_portal
import rubric
from rubric_store import RubricStore
from test_resident_owns_their_record import cohort, completed, context_for  # noqa: F401 (fixture)



def test_a_confirmed_rubric_or_a_confirmed_observation_is_a_review():
    goals = [{"observations": [{"attempt_id": "a"}, {"attempt_id": "b", "voided": True}]}]
    assert resident_pages.reviewed_attempts(goals, [{"attempt_id": "c"}]) == {"a", "c"}


def test_the_resident_reads_it_only_after_review_and_faculty_always(cohort):  # noqa: F811
    store, people = cohort
    resident, faculty = people["resident_one"], people["faculty_one"]
    attempt_id = completed(store, resident)
    assert resident_pages.learning_focus_visible(context_for(store, resident), attempt_id) is False
    assert resident_pages.learning_focus_visible(context_for(store, resident), None) is False
    assert resident_pages.learning_focus_visible(context_for(store, faculty), attempt_id) is True
    assert resident_pages.learning_focus_visible(None, attempt_id) is True
    RubricStore(store).save_review(faculty["token"], attempt_id, scores={d: 0 for d in rubric.DOMAIN_IDS},
                                   status="draft")
    assert resident_pages.learning_focus_visible(context_for(store, resident), attempt_id) is False
    RubricStore(store).save_review(faculty["token"], attempt_id, scores={d: 2 for d in rubric.DOMAIN_IDS},
                                   status="confirmed")
    assert resident_pages.learning_focus_visible(context_for(store, resident), attempt_id) is True


def test_the_copy_of_the_record_names_the_target_only_once_reviewed(cohort):  # noqa: F811
    store, people = cohort
    resident, faculty = people["resident_one"], people["faculty_one"]
    first = completed(store, resident, challenge="R1-05")
    second = completed(store, resident, challenge="R1-03")
    RubricStore(store).save_review(faculty["token"], first, scores={d: 2 for d in rubric.DOMAIN_IDS},
                                   status="confirmed")
    exported = {row["attempt_id"]: row for row in resident_portal.account_export(context_for(store, resident))["encounters"]}
    assert exported[first]["challenge_id"] == "R1-05"
    assert exported[second]["challenge_id"] is None


class _Page:
    """Just enough of Streamlit to see what the close screen writes."""

    def __init__(self, session):
        self.session_state, self.written = session, []

    def caption(self, text):
        self.written.append(("caption", text))

    def write(self, text):
        self.written.append(("write", text))

    def expander(self, *args, **kwargs):
        self.written.append(("expander", args[0]))
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _close_screen(monkeypatch, context, attempt_id):
    page = _Page({"encounter_ended": True, "_attempt_id": attempt_id,
                  "encounter_assignment": {"challenge_id": "R1-05"}})
    monkeypatch.setattr(curriculum_runtime, "st", page)
    curriculum_runtime.render_learning_focus(context)
    return page.written


def test_the_close_screen_keeps_it_from_the_resident_and_shows_it_to_faculty(cohort, monkeypatch):  # noqa: F811
    store, people = cohort
    attempt_id = completed(store, people["resident_one"], challenge="R1-05")
    title = curriculum_runtime.CHALLENGES["R1-05"]["title"]
    resident_view = _close_screen(monkeypatch, context_for(store, people["resident_one"]), attempt_id)
    assert not any(title in str(text) for _, text in resident_view)
    assert any("after a faculty member reviews it" in str(text) for _, text in resident_view)
    faculty_view = _close_screen(monkeypatch, context_for(store, people["faculty_one"]), attempt_id)
    assert ("write", title) in faculty_view
