"""P3-514 (page level): the GI MANAGEMENT-TRACE REVIEW on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

It runs the flow a faculty reviewer follows -- login (the management-trace review is where the launcher lands once the earlier reviews are done: nothing to choose), path 1 with its action table, its committed
pressure trajectory, its management trace and its development boundary, six answers (the lock waits for Q6), the lock, the overall judgment, ONE submit, the move to path 2 -- then the summary after the tenth path,
the only place where the proposed categories and the limitations appear. And it attacks it: leakage of the mechanism or of the audit, the proposed category before the end, a technical link.
"""
import json
import re
from pathlib import Path

import pytest

import faculty_management_review as fmr
import faculty_management_review_ui as mui
import faculty_trajectory_review as ftr
import test_phase3_faculty_review_page as page
import test_phase3_trajectory_review_page as old
import test_phase3_trajectory_rereview_page as rp
from test_phase3_faculty_review_page import world  # noqa: F401  (the module's fixture: one review process, one store, individual accounts)

ROOT = Path(__file__).resolve().parent
LOADED = fmr.load_set()
ITEMS = LOADED["items"]
SCENARIOS = fmr.SCENARIOS
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No", "Q6": "Reasonable"}
_check, _radio, _button, _disabled, _snap, _everything = rp._check, rp._radio, rp._button, rp._disabled, rp._snap, rp._everything
FORBIDDEN = ("grant", "snapshot", "digest", "fingerprint", "tone_gain", "half_effect", "legacy", "candidate", "lineage", "artifact", "authority", "mental status", "heart rate", "capillary", "consciousness",
             "written as", "category", "CENTER_REFERENCE", "kernel", "parameter")


def _open(world, credentials=None, *, hold=True):
    """Sign in with the earlier holds released by the operator's switches (the shared review environment does that); ``hold=True`` leaves THIS review's own hold in force (what a reviewer lives)."""
    if hold:
        world["mp"].delenv(mui.OPERATOR_FLAG, raising=False)
    else:
        world["mp"].setenv(mui.OPERATOR_FLAG, mui.OPERATOR_OPEN)
    return page._open(world, credentials, mode="management")


def _leaks(snapshot) -> list:
    """What of the mechanism a screen shows. The one fixed note that NAMES what is not displayed (heart rate, capillary refill, mental status) is not a leak and is taken out first, as the titration review's
    page test takes out its own note."""
    found = []
    for source in ("text", "protos"):
        lowered = snapshot[source].replace(mui.PRESSURE_ONLY_NOTE, "").lower()
        found += [(source, token) for token in FORBIDDEN if token.lower() in lowered]
    found += [("kinds", kind) for kind in snapshot["kinds"] & {"download_button", "link_button", "page_link", "iframe", "html", "code", "json"}]
    found += [("links", "markdown link") for _ in [0] if re.search(r"\]\(|<a |href", " ".join(snapshot["markdown"]))]
    return found


def _answer(at, upto=6):
    for question in list(ANSWERS)[:upto]:
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    _check(at)


def _log_of(world, credentials, scenario_id):
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    return fmr.ManagementReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"])


@pytest.fixture(scope="module")
def journey(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    result = {"credentials": credentials, "landing": _snap(at), "text_landing": _everything(at)}
    _answer(at, upto=5)
    result["five"] = {"lock_disabled": _disabled(_button(at, mui.LOCK_LABEL))}
    _answer(at)
    result["six"] = {"lock_disabled": _disabled(_button(at, mui.LOCK_LABEL))}
    _button(at, mui.LOCK_LABEL).click().run()
    _check(at)
    _radio(at, "Overall judgment").set_value("ACCEPT_WITH_LIMITATION")
    at.run()
    _check(at)
    _button(at, mui.NEXT_LABEL).click().run()
    _check(at)
    result["second"] = _snap(at)
    result["before_end"] = _everything(at)
    for scenario_id in SCENARIOS[1:]:
        log = _log_of(world, credentials, scenario_id)
        for question, value in ANSWERS.items():
            assert log.answer(question, value)["ok"]
        assert log.lock()["ok"] and log.set_overall("ACCEPT")["ok"] and log.submit()["ok"]
    at = _open(world, credentials)
    result["complete"] = _snap(at)
    result["text_complete"] = _everything(at)
    return result


def test_p1_the_launcher_lands_on_the_management_review_with_ten_paths_and_the_first_path_shows_its_trace_and_boundary(journey):
    text = journey["text_landing"]
    assert launcher_note() in text
    assert "Management trace" in text and "Development model boundary" in text
    first = ITEMS[SCENARIOS[0]]
    assert first["purpose"] in text and "Q6 · MANAGEMENT MEANING" in text
    buttons = [label for label, _ in journey["landing"]["buttons"] if re.match(r"(✓ )?\d+ · ", label)]
    assert len(buttons) == 10, buttons
    assert _leaks(journey["landing"]) == []


def launcher_note():
    import faculty_review_ui as launcher
    return launcher.MANAGEMENT_HELD_NOTE


def test_p2_the_lock_waits_for_q6(journey):
    assert journey["five"]["lock_disabled"] is True and journey["six"]["lock_disabled"] is False


def test_p3_after_the_submit_the_second_path_opens_and_nothing_of_the_proposal_or_the_limitations_is_shown_before_the_end(journey):
    assert ITEMS[SCENARIOS[1]]["purpose"] in journey["before_end"]
    assert "Written as" not in journey["before_end"] and "CURRENT LIMITATIONS" not in journey["before_end"]
    assert _leaks(journey["second"]) == []


def test_p4_the_chart_is_exactly_the_stored_committed_trajectory(journey):
    rows = set()
    for spec in journey["landing"]["charts"]:
        rows |= old._data_rows(spec)
    expected = {(point["minute"], variable, point[key], mui.SERIES_NAME) for point in ITEMS[SCENARIOS[0]]["common"] for variable, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))}
    assert expected <= rows, sorted(expected - rows)[:5]


def test_p5_the_summary_after_the_tenth_path_counts_tabulates_and_states_the_proposals_and_the_limitations_only_there(journey):
    text = journey["text_complete"]
    assert f"REVIEW COMPLETE · {len(SCENARIOS)} / {len(SCENARIOS)}" in text
    assert "Written as (proposal)" in text and "CURRENT LIMITATIONS" in text
    for entry in LOADED["limitations"]:
        assert entry["text"] in text
