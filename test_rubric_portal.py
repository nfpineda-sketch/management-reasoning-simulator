"""The faculty's screen: nothing is confirmed until a faculty member confirms it."""
import pytest
from streamlit.testing.v1 import AppTest

import rubric
from rubric_store import RubricStore
from test_faculty_analysis_store import cohort           # noqa: F401  (fixture)

APP = """
import streamlit as st
from account_store import AccountStore
from rubric_portal import render_rubric_assessment
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
record = store.get_attempt(token, st.session_state['test_attempt'])
st.session_state['saved'] = render_rubric_assessment(context, record)
"""

CASE = "acs_48m_wellens"


def attempt_on_case(accounts, token, case_id=CASE):
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic encounter"})
    accounts.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {"review_completed": True,
                    "encounter": {"authored_case_id": case_id},
                    "management_trace": [
                        {"execution_status": "executed", "learner_input": "Give aspirin 300 mg PO.",
                         "decision_time_min": 0, "response_time_min": 3,
                         "reasoning": {"problem_representation": "A synthetic working model"},
                         "state_before": {"observable": {"mental_status": "alert"}},
                         "state_after": {"observable": {"mental_status": "alert"}}}]},
    }, status="completed")
    return attempt_id


def page(cohort, attempt_id, actor="faculty"):
    accounts, _, users = cohort
    app = AppTest.from_string(APP, default_timeout=20)
    app.session_state["database_url"] = accounts._url
    app.session_state["test_token"] = users[actor]["token"]
    app.session_state["test_attempt"] = attempt_id
    app.run()
    assert not app.exception
    return app


def widget(app, kind, label):
    return next(item for item in getattr(app, kind) if item.label == label)


def score_every_domain(app, value=2):
    """Pick a score for each of the five, the way a reviewer has to.

    Since 2026-09-23 the selector starts every domain at "not assessable", so a
    confirmation that nobody touched is refused for want of five written
    reasons. That is the point of the default, and a test that confirms an
    assessment has to do what a reviewer does.
    """
    for item in [s for s in app.selectbox if s.label == "Your score"]:
        item.set_value(value)
    return app.run()


def test_the_five_domains_and_the_defined_events_are_on_the_screen(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    assert len([s for s in app.selectbox if s.label == "Your score"]) == len(rubric.DOMAIN_IDS)
    body = " ".join(item.value for item in app.markdown)
    # Spelled out on screen too: decisions there are already D1, D2, D3.
    for domain in rubric.DOMAIN_IDS:
        assert f"Domain {domain[1:]}" in body
    assert "acs_no_antiplatelet" in body and "acs_provocation_test" in body
    # The pilot caveat is on the screen, not only in the documents.
    captions = " ".join(item.value for item in app.caption)
    assert "not ACGME Milestone levels" in captions


def test_a_resident_never_sees_the_rubric_panel(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id, "resident")
    assert not app.selectbox and not app.button
    assert app.session_state["saved"] is None


def test_nothing_is_stored_until_the_faculty_saves(cohort):
    accounts, store_unused, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    store = RubricStore(accounts)
    token = users["faculty"]["token"]
    page(cohort, attempt_id)
    assert store.latest_review(token, attempt_id) is None
    assert store.latest_proposal(token, attempt_id) is None


def test_a_draft_is_saved_as_a_draft_and_confirming_is_a_second_revision(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    token = users["faculty"]["token"]
    store = RubricStore(accounts)

    app = page(cohort, attempt_id)
    widget(app, "button", "Save draft").click().run()
    assert not app.exception
    saved = store.latest_review(token, attempt_id)
    assert saved["status"] == "draft" and saved["sequence"] == 1

    app.run()
    score_every_domain(app)
    widget(app, "button", "Confirm assessment").click().run()
    assert not app.exception
    confirmed = store.latest_review(token, attempt_id)
    assert confirmed["status"] == "confirmed" and confirmed["sequence"] == 2
    # The draft is not overwritten.
    assert len(store.history(token, attempt_id)) == 2


def test_a_score_of_not_assessable_asks_for_its_reason_before_it_can_be_confirmed(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    next(s for s in app.selectbox if s.label == "Your score").set_value(rubric.NOT_ASSESSABLE).run()
    assert any(item.label.startswith("Why is it not assessable?") for item in app.text_input)
    widget(app, "button", "Confirm assessment").click().run()
    assert any("reason" in item.value.lower() for item in app.error)
    store = RubricStore(accounts)
    assert store.latest_review(users["faculty"]["token"], attempt_id) is None


def test_confirming_an_event_shows_the_penalty_before_it_is_saved(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    score_every_domain(app)
    radios = [r for r in app.radio if r.label == "Your decision"]
    assert radios, "the defined events offer a decision"
    radios[0].set_value("confirmed").run()
    body = " ".join(item.value for item in app.markdown)
    # The total on screen before saving is the total that gets saved.
    assert "Penalty -3" in body


def test_an_encounter_with_no_authored_case_still_offers_the_five_domains(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"], case_id="")
    app = page(cohort, attempt_id)
    assert len([s for s in app.selectbox if s.label == "Your score"]) == len(rubric.DOMAIN_IDS)
    assert not [r for r in app.radio if r.label == "Your decision"]
    assert any("does not name an authored case" in item.value for item in app.info)


def test_an_untouched_domain_starts_at_not_assessable(cohort):
    """Faculty decision of 2026-09-23.

    Across thirteen real proposals the model chose "not assessable" exactly
    never -- including two encounters where it wrote in its own limits field
    that the encounter had closed before the opportunity. Starting the selector
    at its proposed score pushed a reviewer towards scoring; starting it here
    pushes towards deciding, because a domain left alone cannot be confirmed
    without a written reason.
    """
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    chosen = [s.value for s in app.selectbox if s.label == "Your score"]
    assert chosen == [rubric.NOT_ASSESSABLE] * len(rubric.DOMAIN_IDS)


def test_confirming_without_touching_anything_is_refused(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    widget(app, "button", "Confirm assessment").click().run()
    assert any("reason" in item.value.lower() for item in app.error)
    assert RubricStore(accounts).latest_review(users["faculty"]["token"], attempt_id) is None


def test_a_draft_may_still_be_saved_untouched(cohort):
    # A draft is work in progress. Requiring five reasons to save one would
    # mean no draft could be saved at all.
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    widget(app, "button", "Save draft").click().run()
    assert not app.exception
    saved = RubricStore(accounts).latest_review(users["faculty"]["token"], attempt_id)
    assert saved["status"] == "draft"
    assert saved["totals"]["coverage"]["assessed"] == 0


def test_a_saved_score_is_what_comes_back_not_the_default(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    RubricStore(accounts).save_review(users["faculty"]["token"], attempt_id,
                                      scores={d: 3 for d in rubric.DOMAIN_IDS},
                                      status="confirmed")
    app = page(cohort, attempt_id)
    assert [s.value for s in app.selectbox if s.label == "Your score"] == [3] * len(rubric.DOMAIN_IDS)


def _place(node, label, path=()):
    """Where a button sits on the page: the indexes from the root to it."""
    for index, child in getattr(node, "children", {}).items():
        if type(child).__name__ == "Button" and child.label == label:
            return path + (index,)
        found = _place(child, label, path + (index,))
        if found:
            return found
    return None


def test_the_buttons_keep_their_place_while_domains_change(cohort):
    """While the page reruns, Streamlit keeps the previous run's elements where they were.
    A domain left "not assessable" adds a field, and the button row used to move with it, so
    a faded copy of the buttons stayed below the new ones (development app, 2026-09-26)."""
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    untouched = _place(app._tree, "Confirm assessment")
    assert untouched is not None
    score_every_domain(app)
    assert _place(app._tree, "Confirm assessment") == untouched
    radios = [r for r in app.radio if r.label == "Your decision"]
    radios[0].set_value("confirmed").run()
    assert _place(app._tree, "Confirm assessment") == untouched
