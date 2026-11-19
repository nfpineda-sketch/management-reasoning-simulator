"""P3-406 to P3-412 (page level): the MULTIFAMILY TONE REVIEW on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

It runs the human flow a faculty reviewer follows -- login (the tone review is where the launcher lands: nothing to choose), scenario 1 with no comparator and no mechanism, five answers, a refresh (state restored), the lock
(irreversible), the overall judgment, ONE submit, the automatic move to the next scenario, five scenarios in order, the completion screen with the limitations (only there), and the OPTIONAL sensitivity check (only after
the fifth submit) -- and attacks it: leakage of the configuration, the parameters, the other settings, the other sets, the earlier judgments, the legacy comparator, heart rate or capillary refill, the limitations before the
end, a technical link; a locked answer edited; a refresh that loses answers; a failed submit that moves on; a forged route to the optional check; a resident in the process; the earlier reviews' pages, sets and records
disturbed; the first-pass screens reading any file that holds another set or a source record.
"""
import json
import os
import re
import sys
from pathlib import Path

import pytest

import faculty_tone_review as ftm
import faculty_tone_review_ui as tui
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr
import faculty_trajectory_rereview_ui as rui
import test_phase3_faculty_review_page as page
import test_phase3_trajectory_review_page as old
import test_phase3_trajectory_rereview_page as rp
from test_phase3_faculty_review_page import world  # noqa: F401  (the module's fixture: one review process, one store, individual accounts)

ROOT = Path(__file__).resolve().parent
LOADED = ftm.load_set()
ITEMS = LOADED["items"]
SCENARIOS = ftm.SCENARIOS
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Too large", "Q4": "Uncertain", "Q5": "Maybe"}
JUDGMENT = {"FR-F": "ACCEPT", "SYNTH": "ACCEPT_WITH_LIMITATION", "ACS": "RECALIBRATE", "PULM-EDEMA": "ACCEPT_WITH_LIMITATION", "PE": "REJECT"}
QUESTION_LABELS = rp.QUESTION_LABELS
CHOICES = rp.CHOICES
LAST = SCENARIOS[-1]
#: Everything a reviewer must never be able to read before the review is complete (the identity of the configuration, the other settings, the sources, the mechanism, a technical link, the limitations).
FORBIDDEN = ("CENTER_REFERENCE", "witness", "legacy", "comparator", "candidate", "kernel", "parameter", "tone_gain", "half-effect", "half_effect", "onset", "offset", "snapshot", "grant", "bundle", "artifact", "digest",
             "phase3", "docs/", ".json", ".md", "http", "download", "sensitivity", "Common authority", "earlier trajectory", "conjunto", "joint region", "consciousness", "cardiac output", "oxygen", "debt",
             "amendment", "COMMON_TONE", "CONSCIOUSNESS_UNDER", "TITRATION_AND_STOP", "PUMP_DEPENDENCE")
FORBIDDEN_WORDS = (r"\bLOW\b", r"\bHIGH\b", r"\breveal\b")
HR_CRT = re.compile(r"heart[ _-]?rate|capillary|\bHR\b|\bcrt\b|\bCRT\b|\bhr\b|pulse", re.I)
OTHER_REVIEW_FILES = ("PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json", "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json", "PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json", "PHASE3_JOINT_REGION_V1_BLIND_KEY.json",
                      "PHASE3_JOINT_REGION_V1_FACULTY_REREVIEW_SET.json", "PHASE3_PRESSURE_AUTHORITY_SERIES.json", "PHASE3_GI_JOINT_REGION_V1.json", "region_conjunta_v1",
                      "PHASE3_COMMON_TONE_PROBES.json", "PHASE3_FRF_TONE_V1_CANDIDATE.json", "test_tone_review_analysis", "test_tone_pathway_analysis")
_OPENED = rp._OPENED
_check, _radio, _button, _disabled, _snap, _everything = rp._check, rp._radio, rp._button, rp._disabled, rp._snap, rp._everything


# -- helpers --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def _leaks(snapshot) -> list:
    found = []
    for source in ("text", "protos"):
        lowered = snapshot[source].lower()
        found += [(source, token) for token in FORBIDDEN if token.lower() in lowered]
        found += [(source, pattern) for pattern in FORBIDDEN_WORDS if re.search(pattern, snapshot[source])]
    found += [("kinds", kind) for kind in snapshot["kinds"] & {"download_button", "link_button", "page_link", "iframe", "html", "code", "json"}]
    found += [("links", "markdown link") for _ in [0] if re.search(r"\]\(|<a |href", " ".join(snapshot["markdown"]))]
    return found


def _open(world, credentials=None, *, hold=False, tone_hold=True, land=False):
    """Sign in. The tone review is where the launcher lands once the earlier re-review is not pending: the operator's switch (``MRS_FACULTY_REREVIEW_GATE=off``), or a completed re-review. ``hold=True`` leaves the hold of
    FD-REREVIEW-21 in force. ``tone_hold=True`` (the default: what a reviewer lives) leaves the tone review's OWN hold in force: until the five scenarios are submitted and verified, the launcher offers nothing else."""
    if hold:
        world["mp"].delenv(rui.OPERATOR_FLAG, raising=False)
    else:
        world["mp"].setenv(rui.OPERATOR_FLAG, rui.OPERATOR_OPEN)
    if tone_hold:
        world["mp"].delenv(tui.OPERATOR_FLAG, raising=False)
    else:
        world["mp"].setenv(tui.OPERATOR_FLAG, tui.OPERATOR_OPEN)
    at = page._open(world, credentials, mode="tone")
    radio = next((item for item in at.radio if item.label == "Review mode"), None)
    if not land and radio is not None and radio.value != page.ui.TONE_MODE:
        # P3-441 (declared adaptation): the landing page of a released launcher is now the TITRATION review, so the tone review is an explicit choice. What these tests protect (the tone review's own flow) is unchanged;
        # ``land=True`` leaves the landing page as it is, for the tests that assert it.
        radio.set_value(page.ui.TONE_MODE).run()
        assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _modes(at) -> list:
    return [list(item.options) for item in at.radio if item.label == "Review mode"]


def _answer(at, upto=5):
    for question in list(ANSWERS)[:upto]:
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    _check(at)


def _lock(at):
    _button(at, tui.LOCK_LABEL).click().run()
    _check(at)


def _overall(at, scenario_id, comment=None):
    _radio(at, "Overall judgment").set_value(JUDGMENT[scenario_id])
    at.run()
    if comment:
        next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value(comment)
        at.run()
    _check(at)


def _submit(at, scenario_id):
    _button(at, tui.FINISH_LABEL if scenario_id == LAST else tui.NEXT_LABEL).click().run()
    _check(at)


def _label(number: int, scenario_id: str, done: bool = False) -> str:
    return ("✓ " if done else "") + f"{number} · {ITEMS[scenario_id]['short']}"


def _nav(snapshot) -> list:
    return [(label, disabled) for label, disabled in snapshot["buttons"] if re.match(r"(✓ )?\d · ", label)]


def _scenario_radios(snapshot):
    return [entry for entry in snapshot["radios"] if entry[0] != "Review mode"]


def _tables(snapshot, column):
    return [table for table in snapshot["tables"] if table and column in table[0]]


def _chart_rows(snapshot) -> set:
    rows = set()
    for spec in snapshot["charts"]:
        rows |= old._data_rows(spec)
    return rows


def _expected_chart_rows(item) -> set:
    return {(point["minute"], variable, point[key], tui.SERIES_NAME) for point in item["common"] for variable, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))}


def _log_of(world, credentials, scenario_id="FR-F"):
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    return ftm.ToneReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"])


def _sens_log_of(world, credentials):
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    ids = [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    return ftm.SensitivityLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ids, set_digest=LOADED["digest"])


def _complete_by_log(world, credentials, scenario_ids):
    for scenario_id in scenario_ids:
        log = _log_of(world, credentials, scenario_id)
        for question, value in ANSWERS.items():
            assert log.answer(question, value)["ok"]
        assert log.lock()["ok"] and log.set_overall(JUDGMENT[scenario_id])["ok"] and log.submit()["ok"]


@pytest.fixture(scope="module")
def journey(world):  # noqa: F811
    """ONE complete review by one faculty reviewer, with a snapshot of every stage of every scenario, the summary, and the optional sensitivity check (the tests read these; they do not repeat the flow)."""
    credentials = page._faculty(world)
    at = _open(world, credentials)
    assert _modes(at) == [] and page.ui.TONE_HELD_NOTE in _everything(at), "the launcher lands on the tone review: there is nothing to choose and nothing else to open"
    result = {"credentials": credentials, "landing": _snap(at), "scenarios": {}}
    for scenario_id in SCENARIOS:
        stages = {"blank": _snap(at)}
        _answer(at)
        stages["answered"] = _snap(at)
        _lock(at)
        stages["locked"] = _snap(at)
        _overall(at, scenario_id, comment=f"overall note for {scenario_id}")
        stages["overall"] = _snap(at)
        _submit(at, scenario_id)
        stages["after_submit"] = _snap(at)
        result["scenarios"][scenario_id] = stages
    result["complete"] = _snap(at)
    _button(at, "Sensitivity").click().run()
    _check(at)
    result["sensitivity"] = _snap(at)
    _radio(at, ftm.SENSITIVITY_QUESTION).set_value("BORDERLINE")
    at.run()
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("pump coupling looks wide")
    at.run()
    _check(at)
    result["sensitivity_answered"] = _snap(at)
    result["at"] = at
    return result


# -- the flow --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p1_the_whole_human_flow_five_scenarios_in_order_to_the_completion_screen(journey):
    shown = []
    for scenario_id in SCENARIOS:
        text = journey["scenarios"][scenario_id]["blank"]["text"]
        shown.append(next(identifier for identifier, item in ITEMS.items() if item["title"] in text))
    assert shown == list(SCENARIOS) == ["FR-F", "SYNTH", "ACS", "PULM-EDEMA", "PE"]
    complete = journey["complete"]
    assert "REVIEW COMPLETE · 5 / 5" in complete["text"] and ftm.COMPLETION_NOTE in complete["text"]
    assert complete["metrics"] == [("Accept", "1"), ("Accept with limitation", "2"), ("Recalibrate", "1"), ("Reject", "1")]
    for scenario_id, following in zip(SCENARIOS, SCENARIOS[1:]):           # auto-next: right after each submit the next scenario (never the same, never a menu) is on screen
        after = journey["scenarios"][scenario_id]["after_submit"]
        assert ITEMS[following]["title"] in after["text"] and tui.LOCK_LABEL in " ".join(label for label, _ in after["buttons"]), scenario_id
        assert f"Scenario {SCENARIOS.index(following) + 1} of 5 · {SCENARIOS.index(following)} of 5 reviewed" in after["text"]


def test_p2_the_landing_page_is_the_tone_review_with_five_scenarios_in_order_and_only_the_first_open(journey):
    landing = journey["landing"]
    assert _nav(landing) == [(_label(1, "FR-F"), False)] + [(_label(number, scenario_id), True) for number, scenario_id in enumerate(SCENARIOS[1:], 2)]
    assert "Scenario 1 of 5 · 0 of 5 reviewed" in landing["text"] and "Faculty Trajectory Review" in landing["text"] and "Norepinephrine and vascular tone" in landing["text"]
    assert page.ui.TONE_BANNER in landing["text"] and "GI pressure development authority" not in landing["text"], "the banner says what THIS review is"
    assert "Re-review ·" not in landing["text"] and ITEMS["FR-F"]["title"] in landing["text"]
    assert [button for button, _ in landing["buttons"] if "Summary" in button or "Sensitivity" in button] == [], "neither the summary nor the optional check exists before the fifth submit"


def test_p3_the_first_pass_screen_has_what_the_reviewer_needs_and_nothing_else(journey):
    for scenario_id, stages in journey["scenarios"].items():
        blank, item = stages["blank"], ITEMS[scenario_id]
        text = blank["text"]
        assert f"**{tui.JUDGING_LABEL}.** {item['purpose']}" in text and item["title"] in text and item["context"] in text and item["intervention"] in text
        assert f"{item['banner']} · {item['note']}" in text or f"**{item['banner']}** · {item['note']}" in text
        assert all(fact in text for fact in item["baseline_facts"])
        if item["kind"] == ftm.KIND_CASE:
            assert f"On arrival: BP {item['arrival']['sbp']}/{item['arrival']['dbp']} mmHg (MAP {item['arrival']['map']}) · SpO₂ {item['arrival']['spo2']}% · RR {item['arrival']['rr']}/min." in text
        else:
            assert "On arrival" not in text and "Baseline state" in text
        timeline = _tables(blank, "What was done")[0]
        assert [(row["Minute"], row["What was done"], row["What the encounter did"]) for row in timeline] == [(row["minute"], row["action"], row["result"]) for row in item["timeline"]]
        values = _tables(blank, "SBP")[0]
        assert [(row["Minute"], row["SBP"], row["DBP"], row["MAP"]) for row in values] == [(row["minute"], row["sbp"], row["dbp"], row["map"]) for row in ftm.values_table(item)]
        assert sorted(values[0]) == ["DBP", "MAP", "Minute", "SBP"] and tui.PRESSURE_ONLY_NOTE in text
        radios = _scenario_radios(blank)
        assert [(label, options, value) for label, options, value in radios] == [(QUESTION_LABELS[q], CHOICES[q], None) for q in ANSWERS]
        assert [label for label, _ in blank["text_areas"]] == ["Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)"]
        assert [(label, disabled) for label, disabled in blank["buttons"] if label in (tui.LOCK_LABEL, tui.NEXT_LABEL, tui.FINISH_LABEL)] == [(tui.LOCK_LABEL, True)]
        assert not any("Q5H" in label or "STOPPING" in label for label, _, _ in radios) and "experiment stops" not in text
        assert len(blank["charts"]) == 1


def test_p3b_the_synthetic_probe_is_labelled_as_one_in_the_exact_words_and_the_cases_are_not(journey):
    probe = journey["scenarios"]["SYNTH"]["blank"]["text"]
    assert "SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE" in probe and "This is a synthetic development physiology probe, not a clinical case." in probe
    assert "SYNTHETIC DEVELOPMENT CASE" not in probe
    for scenario_id in ("FR-F", "ACS", "PULM-EDEMA", "PE"):
        text = journey["scenarios"][scenario_id]["blank"]["text"]
        assert "SYNTHETIC DEVELOPMENT CASE" in text and "PHYSIOLOGY PROBE" not in text and "not a clinical case" not in text


def test_p3c_no_screen_of_the_flow_shows_heart_rate_or_capillary_refill_only_the_note_names_them(journey):
    snapshots = [("landing", journey["landing"])] + [(f"{sid}/{stage}", snap) for sid, stages in journey["scenarios"].items() for stage, snap in stages.items()] + [("complete", journey["complete"]), ("sensitivity", journey["sensitivity"])]
    for name, snapshot in snapshots:
        for source in ("text", "protos"):
            seen = HR_CRT.findall(snapshot[source].replace(tui.PRESSURE_ONLY_NOTE, ""))
            assert seen == [], (name, source, seen)
        for spec in snapshot["chart_specs"]:
            assert HR_CRT.findall(spec) == [] and {"SBP", "MAP", "DBP"} >= set(re.findall(r'"variable": "(\w+)"', spec)), name
        assert not [key for key in snapshot["session_keys"] if HR_CRT.search(key)], name
        for table in snapshot["tables"]:
            assert not [column for row in table for column in row if HR_CRT.search(str(column))], name
    for scenario_id, stages in journey["scenarios"].items():
        assert tui.PRESSURE_ONLY_NOTE in stages["blank"]["text"], "the reviewer is told why the other channels are not there"


def test_p4_every_chart_and_table_is_exactly_the_stored_trajectory_including_the_hypertensive_axis(journey):
    for scenario_id, stages in journey["scenarios"].items():
        item = ITEMS[scenario_id]
        for stage in ("blank", "answered", "locked", "overall"):
            assert _chart_rows(stages[stage]) == _expected_chart_rows(item), (scenario_id, stage)
        specs = stages["blank"]["chart_specs"]
        assert len(specs) == 1 and f'"domain": [0, {ftm.y_axis_max(item)}]' in specs[0], scenario_id
        assert ("Minutes" in specs[0] if item["kind"] == ftm.KIND_PROBE else "Minutes since arrival" in specs[0])
        assert max(point["sbp"] for point in item["common"]) <= ftm.y_axis_max(item), "nothing is clipped"
        marker = [row["minute"] for row in item["timeline"] if row["intervention"]]
        assert set(re.findall(r'"minute": (\d+), "label": "1"', specs[0])) == {str(marker[0])}, "the one intervention is marked at its minute"


def test_p5_the_lock_waits_for_the_five_answers_and_then_nothing_of_the_first_impression_can_be_changed(journey):
    for scenario_id, stages in journey["scenarios"].items():
        assert dict(stages["answered"]["buttons"])[tui.LOCK_LABEL] is False
        assert [value for _, _, value in _scenario_radios(stages["answered"])] == list(ANSWERS.values())
        locked = stages["locked"]
        assert [(label, options) for label, options, _ in _scenario_radios(locked)] == [("Overall judgment", list(ftr.OVERALL))]
        assert tui.LOCK_LABEL not in [label for label, _ in locked["buttons"]] and "Your first impression (locked)" in locked["expanders"]
        assert [f"{topic}: **{value}**" for topic, value in zip(("Direction", "Timing", "Magnitude", "Management Response", "Educational Risk"), ANSWERS.values())] == [
            line for line in locked["markdown"] if re.fullmatch(r"(Direction|Timing|Magnitude|Management Response|Educational Risk): \*\*.*\*\*", line)]
        finish = tui.FINISH_LABEL if scenario_id == LAST else tui.NEXT_LABEL
        assert dict(locked["buttons"])[finish] is True and dict(stages["overall"]["buttons"])[finish] is False
        assert [label for label, _ in locked["text_areas"]] == ["Optional overall comment"]


def test_p6_the_completion_screen_counts_tabulates_and_states_the_limitations_only_there(journey):
    complete = journey["complete"]
    text = complete["text"]
    assert "REVIEW COMPLETE · 5 / 5" in text and ftm.COMPLETION_NOTE in text and "not a score and not a clinical validation" in text
    summary = _tables(complete, "Overall")[0]
    assert [(row["Scenario"], row["Overall"]) for row in summary] == [(ITEMS[scenario_id]["short"], JUDGMENT[scenario_id]) for scenario_id in SCENARIOS]
    assert [[row[q] for q in ANSWERS] for row in summary] == [list(ANSWERS.values())] * 5
    for scenario_id in SCENARIOS:
        assert f"{ITEMS[scenario_id]['short']} ({JUDGMENT[scenario_id]}, overall): overall note for {scenario_id}" in text
    assert tui.LIMITATIONS_HEADING in text
    for entry in LOADED["limitations"]:
        assert f"**{entry['id']}** · {entry['text']}" in " ".join(complete["markdown"]) or entry["id"] in text
    assert "do not support educational promotion" in text and "neither shown nor judged" in text and "Titration, rate changes and stopping" in text
    assert [(label, disabled) for label, disabled in complete["buttons"] if label.startswith("✓") or label in ("Summary", "Sensitivity (optional)")] == [
        *[(_label(number, scenario_id, True), False) for number, scenario_id in enumerate(SCENARIOS, 1)], ("Summary", False), ("Sensitivity (optional)", False)]
    for forbidden in ("parameter", "legacy", "Legacy", "comparator", "CENTER_REFERENCE"):
        assert forbidden not in text, forbidden
    assert not re.search(r"\bLOW\b|\bHIGH\b", text), "the other settings are named nowhere on the summary"


def test_p6b_the_limitations_are_stated_nowhere_before_the_review_is_complete(journey):
    for scenario_id, stages in journey["scenarios"].items():
        for stage, snapshot in stages.items():
            if (scenario_id, stage) == (LAST, "after_submit"):                       # the screen after the fifth submit IS the completion screen
                continue
            blob = snapshot["text"] + snapshot["protos"]
            for token in ("LIMITATIONS TO FOLLOW UP", "COMMON_TONE_PUMP", "CONSCIOUSNESS_UNDER", "TITRATION_AND_STOP", "educational promotion", "Titration, rate changes"):
                assert token not in blob, (scenario_id, stage, token)
    assert tui.LIMITATIONS_HEADING not in journey["landing"]["text"]


# -- blindness ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p7_no_first_pass_screen_carries_the_configuration_the_other_settings_the_sources_the_limitations_or_a_technical_link(journey):
    snapshots = [("landing", journey["landing"])] + [(f"{sid}/{stage}", snap) for sid, stages in journey["scenarios"].items() for stage, snap in stages.items() if (sid, stage) != (LAST, "after_submit")]
    for name, snapshot in snapshots:                                  # (the screen after the fifth submit IS the completion screen: the next test reads it)
        assert _leaks(snapshot) == [], (name, _leaks(snapshot))
        for spec in snapshot["chart_specs"]:
            for token in ("CENTER_REFERENCE", "witness", "legacy", "comparator", "candidate", "Common authority", "Legacy", '"setting"', "LOW", "HIGH", "CENTER"):
                assert token not in spec, (name, token)
        assert not [key for key in snapshot["session_keys"] if re.search(r"center|witness|candidate|legacy|comparator|low|high|sens", key, re.I)], (name, snapshot["session_keys"])
        assert not [label for label, *_ in snapshot["radios"] if re.search(r"set|witness|candidate|legacy|setting", label, re.I) and label != "Review mode"], name
    assert "reviewer" in journey["landing"]["protos"].lower() and "Signed in" in journey["landing"]["protos"]


def test_p7b_the_complete_screen_carries_no_parameter_no_configuration_and_no_link(journey):
    snapshot = journey["complete"]
    leaks = [item for item in _leaks(snapshot) if item[1] not in ("COMMON_TONE", "CONSCIOUSNESS_UNDER", "TITRATION_AND_STOP", "PUMP_DEPENDENCE", "consciousness", "sensitivity")]
    assert leaks == [], leaks


def test_p7c_the_leak_detector_can_fail_it_sees_a_leak_in_the_sidebar_a_help_text_a_label_a_chart_and_a_limitation(world, monkeypatch):  # noqa: F811
    import streamlit as st
    real_header, real_chart = tui._header, tui.tui.pressure_chart
    injected = {"sidebar": lambda: st.sidebar.caption("CENTER_REFERENCE / half-effect"), "tooltip": lambda: st.button("x", help="the CENTER_REFERENCE configuration", key="leak_help"),
                "label": lambda: st.radio("legacy comparator", ["a", "b"], key="leak_label"), "markdown link": lambda: st.markdown("[the key](docs/revision/PHASE3_COMMON_TONE_PROBES.json)"),
                "limitation": lambda: st.caption("COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED"), "other setting": lambda: st.caption("The LOW setting of the response.")}
    for name, leak in injected.items():
        with monkeypatch.context() as patch:
            patch.setattr(tui, "_header", lambda *args, _leak=leak, **kwargs: (_leak(), real_header(*args, **kwargs))[1])
            assert _leaks(_snap(_open(world))), f"the detector missed a leak in the {name}"
    with monkeypatch.context() as patch:
        patch.setattr(tui.tui, "pressure_chart", lambda *args, **kwargs: real_chart(*args, **kwargs).properties(title="CENTER_REFERENCE trajectory"))
        assert _leaks(_snap(_open(world))), "the detector missed a leak in the chart"


def test_p7d_the_hr_crt_detector_can_fail_it_sees_each_way_they_could_come_back(world, monkeypatch):  # noqa: F811
    import streamlit as st
    real_header = tui._header
    injected = {"arrival line": lambda: st.markdown("On arrival: BP 88/54 mmHg · HR 124/min · capillary refill 5 s."), "tooltip": lambda: st.button("x", help="heart rate 124", key="hr_help"),
                "column": lambda: st.dataframe([{"Minute": 0, "Heart rate (context)": 124}]), "sidebar": lambda: st.sidebar.caption("CRT 5.0 s")}
    for name, leak in injected.items():
        with monkeypatch.context() as patch:
            patch.setattr(tui, "_header", lambda *args, _leak=leak, **kwargs: (_leak(), real_header(*args, **kwargs))[1])
            snapshot = _snap(_open(world))
            assert [source for source in ("text", "protos") if HR_CRT.findall(snapshot[source].replace(tui.PRESSURE_ONLY_NOTE, ""))], f"the detector missed {name}"


def test_p8_the_first_pass_screens_read_no_file_of_another_set_the_earlier_reviews_or_the_sources(world):  # noqa: F811
    _OPENED["paths"].clear()
    _OPENED["on"] = True
    try:
        at = _open(world)
        _answer(at)
        _lock(at)
    finally:
        _OPENED["on"] = False
    reads = list(_OPENED["paths"])
    touched = [path for path in reads if any(name in path for name in OTHER_REVIEW_FILES)]
    assert touched == [], touched
    assert any(path.endswith("PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json") for path in reads), "the page must read its own set"


def test_p8b_the_file_read_detector_can_fail_it_sees_every_way_of_opening_a_file(world, monkeypatch):  # noqa: F811
    real_header = tui._header
    sources = ROOT / "docs" / "revision" / "PHASE3_COMMON_TONE_PROBES.json"
    readers = {"Path.open": lambda: sources.open("rb").read(1), "Path.read_text": lambda: ftr.SET_PATH.read_text(encoding="utf-8"), "open": lambda: open(rr.BLIND_KEY_PATH, "rb").read(1),
               "os.open": lambda: os.close(os.open(str(sources), os.O_RDONLY))}
    for name, reader in readers.items():
        with monkeypatch.context() as patch:
            patch.setattr(tui, "_header", lambda *args, _read=reader, **kwargs: (_read(), real_header(*args, **kwargs))[1])
            _OPENED["paths"].clear()
            _OPENED["on"] = True
            try:
                _open(world)
            finally:
                _OPENED["on"] = False
            assert [path for path in _OPENED["paths"] if any(token in path for token in OTHER_REVIEW_FILES)], f"the detector missed a read by {name}"


def test_p9_the_url_carries_nothing_and_the_page_offers_no_way_to_another_set(world):  # noqa: F811
    at = _open(world)
    assert dict(at.query_params) == {} and not at.get("download_button") and not at.get("link_button")
    snapshot = _snap(at)
    allowed = [label for label, _ in _nav(snapshot)] + [tui.LOCK_LABEL, "Sign out"]
    assert [label for label, _ in snapshot["buttons"] if label not in allowed and "password" not in label.lower()] == []


# -- the optional sensitivity check -----------------------------------------------------------------------------------------------------------------------------------------------
def test_p10_the_optional_check_exists_only_after_the_fifth_submit_and_a_forged_route_to_it_shows_nothing(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _complete_by_log(world, credentials, SCENARIOS[:-1])
    at = _open(world, credentials)
    for forged in (tui.SENSITIVITY_VIEW, tui.SUMMARY_VIEW):
        at.session_state[tui.VIEW_KEY] = forged
        at.run()
        _check(at)
        snapshot = _snap(at)
        text = snapshot["text"]
        assert ITEMS[LAST]["title"] in text and tui.LOCK_LABEL in " ".join(label for label, _ in snapshot["buttons"]), forged
        assert "Sensitivity range check" not in text and tui.LIMITATIONS_HEADING not in text and "REVIEW COMPLETE" not in text and _leaks(snapshot) == [], forged
        assert not [label for label, _ in snapshot["buttons"] if "Sensitivity" in label or label == "Summary"]
        assert _chart_rows(snapshot) == _expected_chart_rows(ITEMS[LAST])
    _complete_by_log(world, credentials, (LAST,))
    done = _open(world, credentials)
    assert "REVIEW COMPLETE · 5 / 5" in _everything(done) and _button(done, "Sensitivity (optional)") is not None


def test_p10b_the_optional_check_shows_low_center_and_high_on_the_same_axes_with_one_question_per_scenario_and_no_parameter(journey):
    sens, ids = journey["sensitivity"], [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    text = sens["text"]
    assert "Sensitivity range check · optional" in text and tui.OPTIONAL_NOTE in text and "skipping this section changes nothing" in text
    assert [label for label, _, _ in _scenario_radios(sens)] == [ftm.SENSITIVITY_QUESTION] * len(ids) and all(options == ["YES", "BORDERLINE", "NO"] for _, options, _ in _scenario_radios(sens))
    assert [label for label, _ in sens["text_areas"]] == ["Optional comment"] * len(ids) and len(sens["charts"]) == len(ids)
    for scenario_id, spec in zip(ids, sens["chart_specs"]):
        item = ITEMS[scenario_id]
        entry = next(entry for entry in LOADED["sensitivity"] if entry["scenario_id"] == scenario_id)
        rows = set()

        def walk(node):
            if isinstance(node, dict):
                if "setting" in node and "mmHg" in node:
                    rows.add((node["setting"], node["minute"], float(node["mmHg"])))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(json.loads(spec))
        expected = {(name, point["minute"], float(point["map"])) for name, points in (("LOW", entry["points"]["LOW"]), ("CENTER", item["common"]), ("HIGH", entry["points"]["HIGH"])) for point in points}
        assert rows == expected, scenario_id
        assert all(token not in spec for token in ("tone_gain", "half", "onset", "offset", "parameter", "witness", "CENTER_REFERENCE"))
    for name in ("LOW", "CENTER", "HIGH"):
        assert name in " ".join(str(table) for table in sens["tables"])
    assert "No parameter values are shown." in text
    assert not re.search(r"tone_gain|half-effect|onset|offset|CENTER_REFERENCE|witness|legacy|comparator", text + sens["protos"], re.I)


def test_p10c_the_optional_answers_are_autosaved_survive_a_refresh_and_reach_the_summary_and_the_main_review_never_needed_them(journey, world):  # noqa: F811
    answered = journey["sensitivity_answered"]
    assert ("BORDERLINE" in [value for _, _, value in _scenario_radios(answered)]) and "pump coupling looks wide" in [value for _, value in answered["text_areas"]]
    log = _sens_log_of(world, journey["credentials"])
    assert list(log.state()["answers"].values()) == ["BORDERLINE"] and list(log.state()["comments"].values()) == ["pump coupling looks wide"]
    again = _open(world, journey["credentials"])
    _button(again, "Sensitivity").click().run()
    _check(again)
    restored = _snap(again)
    assert [value for _, _, value in _scenario_radios(restored)][:1] == ["BORDERLINE"] and "pump coupling looks wide" in [value for _, value in restored["text_areas"]]
    _button(again, "Summary").click().run()
    summary = _snap(again)
    assert "Optional sensitivity check" in summary["text"] and "BORDERLINE" in str(_tables(summary, "Sensitivity range")) and "REVIEW COMPLETE · 5 / 5" in summary["text"]
    # the summary of a reviewer who never opened the optional check is just as complete
    assert "Optional sensitivity check" not in journey["complete"]["text"] and "REVIEW COMPLETE · 5 / 5" in journey["complete"]["text"]


# -- persistence --------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p11_a_refresh_restores_the_partial_answers_the_lock_the_overall_choice_and_the_progress(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    for question in ("Q1", "Q2", "Q3"):
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("partial first-pass note")
    at.run()
    again = _open(world, credentials)                                                      # a refresh closes the account session: the reviewer signs in again and finds everything
    assert [value for _, _, value in _scenario_radios(_snap(again))] == ["Expected", "Plausible", "Too large", None, None]
    assert next(item for item in again.text_area if item.label.startswith("Optional comment")).value == "partial first-pass note"
    assert dict(_snap(again)["buttons"])[tui.LOCK_LABEL] is True
    for question in ("Q4", "Q5"):
        _radio(again, question + " ·").set_value(ANSWERS[question])
    again.run()
    _lock(again)
    locked = _open(world, credentials)
    snapshot = _snap(locked)
    assert [(label, value) for label, _, value in _scenario_radios(snapshot)] == [("Overall judgment", None)] and "Your first impression (locked)" in snapshot["expanders"] and "partial first-pass note" in snapshot["text"]
    _overall(locked, "FR-F")
    chosen = _open(world, credentials)
    assert [value for label, _, value in _scenario_radios(_snap(chosen))] == ["ACCEPT"]
    _submit(chosen, "FR-F")
    submitted = _open(world, credentials)
    text = _everything(submitted)
    assert ITEMS["SYNTH"]["title"] in text and "Scenario 2 of 5 · 1 of 5 reviewed" in text
    assert dict(_nav(_snap(submitted))) == {_label(1, "FR-F", True): False, _label(2, "SYNTH"): False, _label(3, "ACS"): True, _label(4, "PULM-EDEMA"): True, _label(5, "PE"): True}


def test_p12_a_submitted_scenario_can_be_viewed_but_not_changed_and_the_log_refuses_what_the_page_does_not_offer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    _lock(at)
    _overall(at, "FR-F", comment="kept as written")
    _submit(at, "FR-F")
    _button(at, _label(1, "FR-F", True)).click().run()
    _check(at)
    snapshot = _snap(at)
    assert "This scenario is submitted. It is shown read-only." in snapshot["text"] and "Overall: **ACCEPT**" in snapshot["text"] and "Overall comment: kept as written" in snapshot["text"]
    assert _scenario_radios(snapshot) == [] and not snapshot["text_areas"] and not [label for label, _ in snapshot["buttons"] if label in (tui.LOCK_LABEL, tui.NEXT_LABEL, tui.FINISH_LABEL)]
    log = _log_of(world, credentials)
    assert log.state()["status"] == "SUBMITTED" and not log.answer("Q1", "Wrong")["ok"] and not log.set_overall("REJECT")["ok"] and not log.comment("late")["ok"] and not log.overall_comment("late")["ok"]


def test_p12b_a_lock_never_fixes_what_the_screen_does_not_show_two_windows_of_the_same_account(world):  # noqa: F811
    credentials = page._faculty(world)
    window_a = _open(world, credentials)
    _answer(window_a)
    window_b = _open(world, credentials)
    _radio(window_b, "Q1 ·").set_value("Wrong")
    window_b.run()
    _check(window_b)
    _radio(window_a, "Q2 ·").set_value("Too late")
    window_a.run()
    _check(window_a)
    assert _radio(window_a, "Q1 ·").value == "Expected"
    _button(window_a, tui.LOCK_LABEL).click().run()
    _check(window_a)
    log = _log_of(world, credentials)
    assert not log.state()["locked"], "the lock must not fix an answer the reviewer never saw"
    snapshot = _snap(window_a)
    assert "Nothing was locked: this screen was out of date" in snapshot["text"] and [value for _, _, value in _scenario_radios(snapshot)] == ["Wrong", "Too late", "Too large", "Uncertain", "Maybe"]
    _lock(window_a)
    assert log.state()["locked"] and log.state()["locked_answers"] == {"Q1": "Wrong", "Q2": "Too late", "Q3": "Too large", "Q4": "Uncertain", "Q5": "Maybe"}


def test_p12c_a_comment_the_log_refused_does_not_lock_silently_behind_the_reviewer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("patient MRN 12345678").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    _button(at, tui.LOCK_LABEL).click().run()
    _check(at)
    assert "The comment in the box is not saved" in _everything(at) and not _log_of(world, credentials).state()["locked"]
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("").run()
    _lock(at)
    assert _log_of(world, credentials).state()["locked"]


def test_p13_a_failed_submit_does_not_advance_and_says_so(world, monkeypatch):  # noqa: F811
    at = _open(world)
    _answer(at)
    _lock(at)
    _overall(at, "FR-F")
    monkeypatch.setattr(ftm.ToneReviewLog, "submit", lambda self: {"ok": False, "why": "it could not be saved (a disk error): nothing was changed", "state": self.state()})
    _button(at, tui.NEXT_LABEL).click().run()
    _check(at)
    text = _everything(at)
    assert "Your review could not be saved, so nothing moved on" in text and ITEMS["FR-F"]["title"] in text and ITEMS["SYNTH"]["title"] not in text and "Scenario 1 of 5 · 0 of 5 reviewed" in text


def test_p14_comments_are_refused_when_they_look_like_identifiers_and_saved_otherwise(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("patient MRN 12345678 looked unwell").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("MAP rises about 4 mmHg per litre: fine").run()
    again = _open(world, credentials)
    assert "This comment is not saved yet" not in _everything(again) and next(item for item in again.text_area if item.label.startswith("Optional comment")).value == "MAP rises about 4 mmHg per litre: fine"


# -- boundaries ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p15_the_whole_review_writes_only_its_own_files_and_leaves_the_earlier_reviews_untouched(journey, world):  # noqa: F811
    store = Path(world["store"]) / "faculty_review"
    for earlier in (ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR):
        assert not (store / earlier).exists(), f"the tone review must not create {earlier}"
    assert (store / ftm.SUBDIR).is_dir() and (store / ftm.RECORDS_SUBDIR).is_dir() and (store / ftm.SENSITIVITY_SUBDIR).is_dir()
    records = sorted((store / ftm.RECORDS_SUBDIR).glob("*.json"))
    assert len(records) >= 5 and all(ftm.SET_ID in record.name for record in records)
    assert list((store / ftm.SUBDIR).glob("session_summary_*.json"))
    assert json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))["record_digest"] == ftr.PINNED_SET_DIGEST and rr.load_set()["digest"] == rr.PINNED_SET_DIGEST


def test_p16_with_the_hold_in_force_the_reviewer_sees_only_the_re_review_and_a_forged_choice_of_the_tone_mode_opens_nothing(world):  # noqa: F811
    at = _open(world, hold=True)
    text = _everything(at)
    assert _modes(at) == [] and page.ui.HELD_NOTE in text and "Re-review · scenario 1 of 4" in text and ITEMS["FR-F"]["title"] not in text
    for key, value in ((page.ui.MODE_CHOICE_KEY, page.ui.TONE_MODE), (page.ui.MODE_KEY, page.ui.TONE_MODE)):
        at.session_state[key] = value
        at.run()
        _check(at)
        text = _everything(at)
        assert ITEMS["FR-F"]["title"] not in text and "Re-review · scenario 1 of 4" in text and at.session_state[page.ui.MODE_CHOICE_KEY] == page.ui.REREVIEW_MODE, (key, value)


def test_p16b_once_released_the_modes_are_the_five_the_titration_review_lands_first_and_the_others_return_by_an_explicit_choice(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials, tone_hold=False, land=True)
    assert _modes(at) == [[page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.LIVE_MODE]] and next(item for item in at.radio if item.label == "Review mode").value == page.ui.TITRATION_MODE, "released, the landing page is the titration review (P3-441)"
    assert ITEMS["FR-F"]["title"] not in _everything(at) and page.ui.TITRATION_BANNER in _everything(at)
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TONE_MODE).run()
    _check(at)
    assert ITEMS["FR-F"]["title"] in _everything(at) and page.ui.TONE_BANNER in _everything(at), "the tone review is an explicit choice"
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TRAJECTORY_MODE).run()
    _check(at)
    text = _everything(at)
    assert "Scenario 1 of 5" in text and ITEMS["FR-F"]["title"] not in text and page.ui.BANNER in text and page.ui.TONE_BANNER not in text      # the first review, with its own banner and its own progress
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.LIVE_MODE).run()
    _check(at)
    assert [item for item in at.selectbox if item.label == "Review encounter"] and _button(at, "Begin review encounter") is not None and page.ui.BANNER in _everything(at)
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TONE_MODE).run()
    _check(at)
    assert ITEMS["FR-F"]["title"] in _everything(at) and page.ui.TONE_BANNER in _everything(at)
    store = Path(world["store"]) / "faculty_review"
    assert not (store / ftr.SUBDIR).exists() and not (store / rr.SUBDIR).exists(), "reading the other modes wrote nothing of theirs"


def test_p16c_a_reviewer_who_completed_the_re_review_lands_on_the_tone_review_without_the_operators_switch(world):  # noqa: F811
    credentials = page._faculty(world)
    for scenario_id in rr.SCENARIOS:
        log = rr.ReReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(world["accounts"].get_user(world["accounts"].authenticate(*credentials))["id"]), rr.load_set()["items"][scenario_id],
                             set_digest=rr.load_set()["digest"], audit=rr.load_set()["audit"])
        for question, value in ANSWERS.items():
            assert log.answer(question, value)["ok"]
        assert log.lock()["ok"] and log.set_overall("ACCEPT")["ok"] and log.submit()["ok"]
    at = _open(world, credentials, hold=True)                                         # no operator switch at all: the re-review is complete, the tone review is not
    text = _everything(at)
    assert _modes(at) == [] and ITEMS["FR-F"]["title"] in text and page.ui.TONE_HELD_NOTE in text and page.ui.HELD_NOTE not in text and "Re-review ·" not in text


def test_p17_a_resident_never_reaches_the_tone_review_and_nothing_is_created_for_them(world):  # noqa: F811
    at = rp._open_resident(world)
    text = _everything(at)
    assert not any(item.label == "Review mode" for item in at.radio) and "Faculty Trajectory Review" not in text and not old._charts(at) and "Norepinephrine and vascular tone" not in text

    class Fake:
        def __init__(self):
            self.errors, self.session_state = [], {}

        def error(self, text):
            self.errors.append(text)

    class Layer:
        review = page.fr
        bundles = page.bundles
    fake = Fake()
    tui.draw(fake, Layer, {"user": {"role": "resident", "id": 99}})
    assert fake.errors == [tui.GENERIC_REFUSAL] and fake.session_state == {}
    assert not any(ftr.reviewer_ref(99) in str(path) for path in (Path(world["store"]) / "faculty_review").rglob("*"))


def test_p18_a_set_that_does_not_verify_stops_the_review_with_a_plain_message_and_reads_nothing_more(world, monkeypatch):  # noqa: F811
    monkeypatch.setattr(ftm, "load_set", lambda *args, **kwargs: {"ok": False, "problems": ["unverifiable"], "digest": None, "items": {}, "sensitivity": [], "limitations": [], "audit": {}})
    at = _open(world)
    text = _everything(at)
    assert "The stored trajectories cannot be verified" in text and "unverifiable" not in text and not _scenario_radios(_snap(at))


def test_p19_the_launcher_draws_the_banner_of_the_mode_in_force_and_changes_nothing_for_the_other_modes():
    """The launcher itself, with no Streamlit: the banner of the tone mode is the tone banner, every other mode keeps the environment's, and without a tone page nothing changes at all."""
    class Fake:
        def __init__(self, state=None, choose=None):
            self.session_state, self.warnings, self.choose = dict(state or {}), [], choose

        def title(self, *args, **kwargs): pass
        def caption(self, *args, **kwargs): pass

        def warning(self, text):
            self.warnings.append(text)

        def expander(self, *args, **kwargs):
            import contextlib
            return contextlib.nullcontext()

        def radio(self, label, modes, index=0, **kwargs):
            return self.choose or modes[index]

    class Layer:
        review = object()

    def run(*, state=None, choose=None, tone=True, default=page.ui.TONE_MODE):
        fake, drew = Fake(state, choose), []
        page.ui.launcher(fake, Layer, {}, None, None, None, trajectory_page=lambda *a: drew.append("first"), rereview_page=lambda *a: drew.append("re"), tone_page=(lambda *a: drew.append("tone")) if tone else None,
                         default_mode=default, hold_prior_modes=lambda *a: False)
        return fake, drew
    fake, drew = run()
    assert drew == ["tone"] and fake.warnings == [page.ui.TONE_BANNER]
    fake, drew = run(state={page.ui.MODE_KEY: page.ui.TRAJECTORY_MODE}, choose=page.ui.TRAJECTORY_MODE)
    assert drew == ["first"] and fake.warnings == [page.ui.BANNER]
    fake, drew = run(state={page.ui.MODE_CHOICE_KEY: page.ui.REREVIEW_MODE}, choose=page.ui.REREVIEW_MODE)
    assert drew == ["re"] and fake.warnings == [page.ui.BANNER]
    fake, drew = run(tone=False, default=page.ui.REREVIEW_MODE)
    assert drew == ["re"] and fake.warnings == [page.ui.BANNER], "without a tone page the launcher is exactly what it was"
    fake, drew = run(tone=False, default=page.ui.TONE_MODE)
    assert drew == ["first"] and fake.warnings == [page.ui.BANNER], "a tone landing without a tone page falls back to the first review"


# -- the other modes are held while the tone review is incomplete (adversarial review, finding 1) ------------------------------------------------------------------------
def test_p20_until_the_five_scenarios_are_submitted_and_verified_the_launcher_offers_nothing_else_and_a_forged_choice_reads_nothing_of_the_other_modes(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    text = _everything(at)
    assert _modes(at) == [] and page.ui.TONE_HELD_NOTE in text and page.ui.TONE_BANNER in text and ITEMS["FR-F"]["title"] in text
    assert not [item for item in at.selectbox if item.label == "Review encounter"] and not _button(at, "Begin review encounter") and not _button(at, "Abandon the unfinished attempt")
    _OPENED["paths"].clear()
    _OPENED["on"] = True
    try:
        for key, value in ((page.ui.MODE_CHOICE_KEY, page.ui.TRAJECTORY_MODE), (page.ui.MODE_KEY, page.ui.LIVE_MODE), (page.ui.MODE_CHOICE_KEY, page.ui.REREVIEW_MODE), (page.ui.MODE_KEY, page.ui.TRAJECTORY_MODE)):
            at.session_state[key] = value
            at.run()
            _check(at)
            snapshot = _snap(at)
            assert ITEMS["FR-F"]["title"] in snapshot["text"] and "Scenario 1 of 5" in snapshot["text"] and "Re-review ·" not in snapshot["text"] and len(snapshot["charts"]) == 1, (key, value)
            assert "Heart rate and capillary refill as shown during the encounter" not in snapshot["expanders"] and not [item for item in at.selectbox if item.label == "Review encounter"], (key, value)
            assert at.session_state[page.ui.MODE_CHOICE_KEY] == page.ui.TONE_MODE and _leaks(snapshot) == []
    finally:
        _OPENED["on"] = False
    assert [path for path in _OPENED["paths"] if any(name in path for name in OTHER_REVIEW_FILES)] == []


def test_p20b_the_hold_is_released_only_by_five_verified_records_by_the_operators_switch_and_what_cannot_be_decided_is_held(world, monkeypatch):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS[:-1])
    assert _modes(_open(world, credentials)) == [], "four of five do not release it"
    _complete_by_log(world, credentials, (LAST,))
    done = _open(world, credentials)
    assert _modes(done) == [[page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.LIVE_MODE]] and page.ui.TONE_HELD_NOTE not in _everything(done)
    assert next(item for item in done.radio if item.label == "Review mode").value == page.ui.TONE_MODE and "REVIEW COMPLETE · 5 / 5" in _everything(done)
    log = _log_of(world, credentials, "ACS")
    kept = log.record_path.read_text(encoding="utf-8")
    log.record_path.unlink()                                                          # the log says submitted, the record that must verify it is gone: the hold comes back
    assert _modes(_open(world, credentials)) == []
    log.record_path.write_text(json.dumps({"record_type": ftm.RECORD_TYPE, "record_id": "forged"}), encoding="utf-8")
    assert _modes(_open(world, credentials)) == []
    log.record_path.write_text(kept, encoding="utf-8")
    assert _modes(_open(world, credentials)) != []
    other = page._faculty(world)
    assert [list(item.options) for item in _open(world, other, tone_hold=False).radio if item.label == "Review mode"] == [[page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.LIVE_MODE]], "the operator's switch"
    monkeypatch.setenv(tui.OPERATOR_FLAG, "ON")                                       # anything but 'off' leaves the hold in force
    assert _modes(page._open(world, other, mode="tone")) == []
    monkeypatch.setattr(ftm, "load_set", lambda *args, **kwargs: {"ok": False, "problems": ["unverifiable"], "digest": None, "items": {}, "sensitivity": [], "limitations": [], "audit": {}})
    monkeypatch.delenv(tui.OPERATOR_FLAG, raising=False)
    assert _modes(page._open(world, credentials, mode="tone")) == [], "an unverifiable set holds"


def test_p20c_the_hold_predicate_itself_fails_closed_for_no_store_no_faculty_account_and_an_unreadable_store(world, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.delenv(tui.OPERATOR_FLAG, raising=False)

    class Review:
        FACULTY_ROLES = ("faculty", "admin")

        def __init__(self, root):
            self.root = root

        def review_root(self):
            return self.root

    class Layer:
        bundles = None

        def __init__(self, root):
            self.review = Review(root)
    faculty = {"user": {"role": "faculty", "id": 7}}
    assert tui.other_modes_held(None, Layer(None), faculty) is True
    assert tui.other_modes_held(None, Layer(tmp_path), {"user": {"role": "resident", "id": 7}}) is True
    assert tui.other_modes_held(None, Layer(tmp_path), {"user": {"role": "faculty"}}) is True
    assert tui.other_modes_held(None, Layer(tmp_path), None) is True
    assert tui.other_modes_held(None, Layer(tmp_path), faculty) is True                              # a store with nothing completed
    monkeypatch.setenv(tui.OPERATOR_FLAG, tui.OPERATOR_OPEN)
    assert tui.other_modes_held(None, Layer(None), None) is False                                    # only the operator's switch releases it, whatever else is missing


# -- the optional check and the limitations wait for VERIFIED records (finding 2) ------------------------------------------------------------------------------------------
def test_p21_log_statuses_alone_open_neither_the_optional_check_nor_the_limitations(world):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS)
    for scenario_id in SCENARIOS:
        _log_of(world, credentials, scenario_id).record_path.unlink()                             # every log says submitted; no record verifies
    at = _open(world, credentials)
    snapshot = _snap(at)
    assert _modes(at) == [] and not [label for label, _ in snapshot["buttons"] if "Sensitivity" in label] and "0 / 5 scenarios reviewed so far" in snapshot["text"]
    assert tui.LIMITATIONS_HEADING not in snapshot["text"] and "REVIEW COMPLETE" not in snapshot["text"] and not [label for label, *_ in snapshot["radios"] if label == ftm.SENSITIVITY_QUESTION]
    at.session_state[tui.VIEW_KEY] = tui.SENSITIVITY_VIEW                                          # a forged route to the optional check
    at.run()
    _check(at)
    forged = _snap(at)
    assert "Sensitivity range check" not in forged["text"] and not re.search(r"\bLOW\b|\bHIGH\b", forged["text"] + forged["protos"]) and tui.LIMITATIONS_HEADING not in forged["text"]
    assert "0 / 5 scenarios reviewed so far" in forged["text"] and "COMMON_TONE" not in forged["text"]


# -- a malformed record never takes the summary down (finding 3) ------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("payload", ["[]", '"x"', "7", '{"linkage": "x"}', '{"overall": [1]}', '{"first_pass": 3, "overall": "x", "linkage": []}', "null", ""])
def test_p22_a_malformed_record_file_is_a_technical_problem_not_a_crash(world, payload):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS)
    _log_of(world, credentials, "ACS").record_path.write_text(payload, encoding="utf-8")
    at = _open(world, credentials)
    _check(at)
    text = _everything(at)
    assert "REVIEW COMPLETE" not in text and "4 / 5 scenarios reviewed so far" in text and "A technical check found something" in text
    assert not [item for item in at.exception] and "Traceback" not in text and "AttributeError" not in text


# -- a refused overall comment is not dropped in silence (finding 5) ---------------------------------------------------------------------------------------------------------------
def test_p23_a_refused_overall_comment_does_not_close_the_scenario_behind_the_reviewer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    _lock(at)
    _overall(at, "FR-F")
    next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value("call me at dr.someone@example.com").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    _button(at, tui.NEXT_LABEL).click().run()
    _check(at)
    assert "The overall comment in the box is not saved" in _everything(at) and not _log_of(world, credentials).state()["submitted"] and ITEMS["FR-F"]["title"] in _everything(at)
    next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value("MAP about 70 mmHg").run()
    _submit(at, "FR-F")
    assert _log_of(world, credentials).state()["submitted"] and _log_of(world, credentials).state()["overall_comment"] == "MAP about 70 mmHg" and ITEMS["SYNTH"]["title"] in _everything(at)


def test_p24_the_launcher_holds_the_tone_review_alone_fails_closed_and_changes_nothing_without_the_predicate():
    """The launcher itself, with no Streamlit: a predicate that raises or says True shows the tone page alone, one that says False offers the modes, and without a predicate nothing changes."""
    class Fake:
        def __init__(self):
            self.session_state, self.warnings, self.captions = {}, [], []

        def title(self, *args, **kwargs): pass

        def warning(self, text):
            self.warnings.append(text)

        def caption(self, text):
            self.captions.append(text)

        def expander(self, *args, **kwargs):
            raise AssertionError("no radio may be drawn while held")

    class Layer:
        review = object()

    def run(predicate, **extra):
        fake, drew = Fake(), []
        try:
            page.ui.launcher(fake, Layer, {}, None, None, None, trajectory_page=lambda *a: drew.append("first"), rereview_page=lambda *a: drew.append("re"), tone_page=lambda *a: drew.append("tone"),
                             default_mode=page.ui.TONE_MODE, hold_prior_modes=lambda *a: False, hold_other_modes=predicate, **extra)
        except AssertionError:
            drew.append("radio drawn")
        return fake, drew

    def raises(*args):
        raise RuntimeError("cannot tell")
    for predicate in (raises, lambda *args: True):
        fake, drew = run(predicate)
        assert drew == ["tone"] and fake.warnings == [page.ui.TONE_BANNER] and fake.captions == [page.ui.TONE_HELD_NOTE] and fake.session_state[page.ui.MODE_CHOICE_KEY] == page.ui.TONE_MODE
    fake, drew = run(lambda *args: False)
    assert drew == ["radio drawn"], "released: the launcher goes on to draw the mode selector"
    fake, drew = run(None)
    assert drew == ["radio drawn"], "without a predicate the launcher is what it was"
    # the re-review hold keeps its precedence
    fake, drew = Fake(), []
    page.ui.launcher(fake, Layer, {}, None, None, None, trajectory_page=lambda *a: drew.append("first"), rereview_page=lambda *a: drew.append("re"), tone_page=lambda *a: drew.append("tone"),
                     default_mode=page.ui.TONE_MODE, hold_prior_modes=lambda *a: True, hold_other_modes=lambda *a: True)
    assert drew == ["re"] and fake.warnings == [page.ui.BANNER] and fake.captions == [page.ui.HELD_NOTE]
