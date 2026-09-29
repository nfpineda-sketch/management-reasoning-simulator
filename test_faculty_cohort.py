"""The faculty's cohort view (cycle 9, §154G–§154L, §154CM, §154CO). Synthetic accounts only.

Who are my residents, who needs my attention: a card per resident, by training year and
name, with the D1–D5 shape of what faculty confirmed and what waits for review. Opening a
card shows that resident's record. No overall score, no ranking, and the resident never
sees the cohort.
"""
import re

import pytest

from test_curriculum_app import authored_replay_fixture, open_app
from account_store import AccountStore, hash_password
from conftest import onboarded
import faculty_cohort

RANKING = r"\b(?:ranked|rank\s*#?\d|#\d|top\s+\d|best|worst|percentile|leaderboard)\b|overall score:"


@pytest.fixture
def program(tmp_path, monkeypatch):
    authored_replay_fixture(monkeypatch)
    url = "sqlite:///" + str(tmp_path / "accounts.sqlite3")
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("teacher", hash_password("local-test-password"))
    admin = store.authenticate("teacher", "local-test-password")
    people = {}
    for name, year in (("resident-one", 1), ("resident-two", 2), ("resident-three", 2)):
        token = store.register(name, "local-resident-password", store.create_invite(admin, "resident", year))
        onboarded(store, token)
        people[name] = {"token": token, "id": store.get_user(token)["id"]}
    # One completed encounter waits for review.
    attempt = store.create_attempt(people["resident-two"]["token"], "R1-03", {"version": "test", "seed": 17})
    store.save_attempt(people["resident-two"]["token"], attempt, {"evidence": {}}, status="completed")
    faculty = store.register("faculty-one", "local-faculty-password", store.create_invite(admin, "faculty"))
    return store, admin, faculty, people


def page_text(at):
    return " ".join(str(item.value) for kind in ("subheader", "markdown", "caption") for item in getattr(at, kind))


def test_the_roster_lists_every_resident_with_what_waits(program):
    store, _, faculty, people = program
    context = {"store": store, "token": faculty, "user": store.get_user(faculty)}
    roster = {person["username"]: person for person in faculty_cohort.roster(context, store.list_attempts(faculty))}
    assert set(roster) == set(people)
    assert (roster["resident-two"]["completed"], roster["resident-two"]["awaiting"]) == (1, 1)
    assert roster["resident-one"]["awaiting"] == 0 and roster["resident-one"]["confirmed_reviews"] == 0
    assert all("overall" not in key and "rank" not in key for key in roster["resident-two"])


@pytest.mark.parametrize("role", ["faculty", "admin"])
def test_staff_open_on_the_cohort_by_year_and_the_record_is_one_click_away(program, role):
    store, admin, faculty, people = program
    at = open_app(faculty if role == "faculty" else admin)
    assert any(item.value == "Residents" for item in at.subheader)
    text = page_text(at)
    assert "R1" in text and "R2" in text and "resident-three" in text
    assert "1 completed encounter(s) awaiting review" in text
    assert not re.search(RANKING, text.lower())
    # The tools stay where they were when no resident is open.
    assert any(item.value == "Objective progress" for item in at.subheader)
    assert any(widget.label == "Management challenge" for widget in at.selectbox)
    open_button = next(button for button in at.button if button.key == "_cohort_open_" + people["resident-two"]["id"])
    open_button.click().run()
    assert not at.exception
    assert any(item.value == "resident-two" for item in at.subheader)
    assert "Awaiting review: **1**" in page_text(at)
    assert at.session_state["progress_resident"] == people["resident-two"]["id"]
    # The resident's record, not the sandbox: no sandbox start from here.
    assert not any(widget.label == "Management challenge" for widget in at.selectbox)
    assert not any(button.label == "Begin Encounter" for button in at.button)
    next(button for button in at.button if button.label == "Back to all residents").click().run()
    assert any(item.value == "Residents" for item in at.subheader)


def test_search_and_the_needs_review_filter_only_narrow_the_list(program):
    store, _, faculty, people = program
    at = open_app(faculty)
    next(widget for widget in at.radio if widget.key == "_cohort_filter").set_value("Needs review").run()
    keys = {button.key for button in at.button if (button.key or "").startswith("_cohort_open_")}
    assert keys == {"_cohort_open_" + people["resident-two"]["id"]}
    next(widget for widget in at.radio if widget.key == "_cohort_filter").set_value("All").run()
    next(widget for widget in at.text_input if widget.key == "_cohort_search").set_value("three").run()
    keys = {button.key for button in at.button if (button.key or "").startswith("_cohort_open_")}
    assert keys == {"_cohort_open_" + people["resident-three"]["id"]}


def test_an_inactive_resident_keeps_a_card_that_says_so(program):
    store, admin, faculty, people = program
    store.update_user(admin, people["resident-one"]["id"], active=False)
    at = open_app(faculty)
    assert "inactive account" in page_text(at)


def test_a_resident_never_sees_the_cohort(program):
    store, _, _, people = program
    at = open_app(people["resident-one"]["token"])
    assert not any(item.value == "Residents" for item in at.subheader)
    assert not any((button.key or "").startswith("_cohort_open_") for button in at.button)
    assert "resident-two" not in page_text(at)
