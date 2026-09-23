"""The shape on the screen: it is drawn from the scores, and it says what it omits."""
import pytest
from streamlit.testing.v1 import AppTest

import rubric
from rubric_store import RubricStore
from test_faculty_analysis_store import cohort           # noqa: F401  (fixture)
from test_rubric_portal import attempt_on_case

SHAPE_APP = """
import streamlit as st
from rubric_portal import render_rubric_shape
render_rubric_shape(st.session_state['review'], None,
                    average=st.session_state.get('average'),
                    caption=st.session_state.get('caption', ''))
"""

PROFILE_APP = """
import streamlit as st
from account_store import AccountStore
from rubric_portal import render_rubric_profile
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
st.session_state['summary'] = render_rubric_profile(context, st.session_state.get('target'))
"""


def shape(review, **kwargs):
    app = AppTest.from_string(SHAPE_APP, default_timeout=20)
    app.session_state["review"] = review
    for key, value in kwargs.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception
    return app


def markup(app):
    return " ".join(item.value for item in app.markdown)


def captions(app):
    return " ".join(item.value for item in app.caption)


def test_the_chart_is_drawn_inline_and_names_every_domain():
    app = shape({"scores": {domain: 2 for domain in rubric.DOMAIN_IDS}})
    drawn = markup(app)
    assert "<svg" in drawn and "</svg>" in drawn
    import rubric_radar
    for domain in rubric.DOMAIN_IDS:
        assert rubric_radar.short_label(domain) in drawn


def test_a_complete_profile_says_nothing_about_gaps():
    app = shape({"scores": {domain: 2 for domain in rubric.DOMAIN_IDS}})
    assert "not assessable" not in captions(app)


def test_a_gap_is_named_in_words_as_well_as_drawn():
    scores = {domain: 2 for domain in rubric.DOMAIN_IDS}
    scores["D5"] = rubric.NOT_ASSESSABLE
    app = shape({"scores": scores})
    said = captions(app)
    assert "not a zero" in said
    assert "domain 5" in said
    assert "was not assessable" in said


def test_two_gaps_are_named_together():
    scores = {domain: 2 for domain in rubric.DOMAIN_IDS}
    scores["D2"] = scores["D5"] = rubric.NOT_ASSESSABLE
    said = captions(shape({"scores": scores}))
    assert "domain 2" in said and "domain 5" in said and "were not assessable" in said


def test_nothing_is_drawn_without_a_review():
    app = shape(None)
    assert "<svg" not in markup(app)


def test_a_second_outline_is_labelled_where_it_comes_from():
    app = shape({"scores": {domain: 2 for domain in rubric.DOMAIN_IDS}},
                average={"key": "average", "label": "Average of 4 encounters",
                         "values": {domain: 1.5 for domain in rubric.DOMAIN_IDS}},
                caption="Each domain averages only the encounters where it was assessable.")
    drawn = markup(app)
    assert "Average of 4 encounters" in drawn
    assert "Each domain averages only" in drawn


def profile(cohort, target=None, actor="faculty"):
    accounts, _, users = cohort
    app = AppTest.from_string(PROFILE_APP, default_timeout=20)
    app.session_state["database_url"] = accounts._url
    app.session_state["test_token"] = users[actor]["token"]
    app.session_state["target"] = target
    app.run()
    assert not app.exception
    return app


def test_a_resident_with_nothing_confirmed_is_told_it_is_not_a_zero(cohort):
    accounts, _, users = cohort
    attempt_on_case(accounts, users["resident"]["token"])
    app = profile(cohort, users["resident"]["id"])
    assert "not a zero" in captions(app)
    assert "<svg" not in markup(app)


def test_a_confirmed_encounter_appears_with_its_domains(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    RubricStore(accounts).save_review(users["faculty"]["token"], attempt_id,
                                      scores={d: 2 for d in rubric.DOMAIN_IDS},
                                      status="confirmed")
    app = profile(cohort, users["resident"]["id"])
    drawn = markup(app)
    assert "<svg" in drawn
    for number in range(1, 6):
        assert f"Domain {number}" in drawn
    assert app.session_state["summary"]["encounters"] == 1


def test_a_draft_leaves_the_profile_empty(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    RubricStore(accounts).save_review(users["faculty"]["token"], attempt_id,
                                      scores={d: 3 for d in rubric.DOMAIN_IDS}, status="draft")
    app = profile(cohort, users["resident"]["id"])
    assert app.session_state["summary"]["encounters"] == 0
    assert "<svg" not in markup(app)


def test_the_lowest_domain_is_named_without_naming_the_resident(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    scores = {d: 3 for d in rubric.DOMAIN_IDS}
    scores["D3"] = 0
    RubricStore(accounts).save_review(users["faculty"]["token"], attempt_id,
                                      scores=scores, status="confirmed")
    said = captions(profile(cohort, users["resident"]["id"]))
    assert "Lowest mean: domain 3" in said
    assert "not a judgement about the resident" in said
