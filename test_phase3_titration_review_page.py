"""P3-441 to P3-446 (page level): the NOREPINEPHRINE TITRATION REVIEW on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

It runs the human flow a faculty reviewer follows -- login (the titration review is where the launcher lands: nothing to choose), scenario 1 with no comparator and no mechanism, five answers, a refresh (state
restored), the lock (irreversible), the overall judgment, ONE submit, the automatic move to the next scenario, five scenarios in order, the completion screen with the counts, the table and the limitations (only
there) -- and attacks it: leakage of the configuration, the parameters, the other settings (LOW, HIGH), the other sets, the earlier judgments, the legacy comparator, heart rate or capillary refill, the limitations
before the end, a technical link; a locked answer edited; a refresh that loses answers; a failed submit that moves on; a forged route to the summary; a resident in the process; the earlier reviews' pages, sets and
records disturbed; the first-pass screens reading any file that holds another set or a source record.
"""
import json
import os
import re
from pathlib import Path

import pytest

import faculty_titration_review as ftt
import faculty_titration_review_ui as tui
import faculty_tone_review as ftm
import faculty_tone_review_ui as tone_ui
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr
import faculty_trajectory_rereview_ui as rui
import test_phase3_faculty_review_page as page
import test_phase3_trajectory_review_page as old
import test_phase3_trajectory_rereview_page as rp
from test_phase3_faculty_review_page import world  # noqa: F401  (the module's fixture: one review process, one store, individual accounts)

ROOT = Path(__file__).resolve().parent
LOADED = ftt.load_set()
ITEMS = LOADED["items"]
SCENARIOS = ftt.SCENARIOS
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No"}
JUDGMENT = {"TIT-1": "ACCEPT", "TIT-2": "ACCEPT_WITH_LIMITATION", "TIT-3": "RECALIBRATE", "TIT-4": "ACCEPT_WITH_LIMITATION", "TIT-5": "REJECT"}
QUESTION_LABELS = rp.QUESTION_LABELS
CHOICES = rp.CHOICES
LAST = SCENARIOS[-1]
#: Everything a reviewer must never be able to read before the review is complete (the identity of the configuration, the other settings, the sources, the mechanism, a technical link, the limitations).
FORBIDDEN = ("CENTER_REFERENCE", "witness", "legacy", "comparator", "candidate", "kernel", "parameter", "tone_gain", "half-effect", "half_effect", "onset", "offset", "snapshot", "grant", "bundle", "artifact", "digest",
             "phase3", "docs/", ".json", ".md", "http", "download", "sensitivity", "Common authority", "earlier trajectory", "conjunto", "joint region", "consciousness", "cardiac output", "oxygen", "debt",
             "amendment", "COMMON_TONE", "CONSCIOUSNESS_UNDER", "PUMP_DEPENDENCE", "MALFORMED_ORDER", "EXPLICIT_ABSOLUTE", "NO_WEIGHT", "NO_MAP", "mcg/kg", "map target", "titrat", "pump", "writer", "rate history",
             "rate_history", "dose-response", "steady")
FORBIDDEN_WORDS = (r"\bLOW\b", r"\bHIGH\b", r"\breveal\b", r"\btau\b")
HR_CRT = re.compile(r"heart[ _-]?rate|capillary|\bHR\b|\bcrt\b|\bCRT\b|\bhr\b|pulse", re.I)
OTHER_REVIEW_FILES = ("PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json", "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json", "PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json", "PHASE3_JOINT_REGION_V1_BLIND_KEY.json",
                      "PHASE3_JOINT_REGION_V1_FACULTY_REREVIEW_SET.json", "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json", "PHASE3_PRESSURE_AUTHORITY_SERIES.json", "PHASE3_GI_JOINT_REGION_V1.json",
                      "region_conjunta_v1", "PHASE3_COMMON_TONE_PROBES.json", "PHASE3_FRF_TONE_V1_CANDIDATE.json", "PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json", "test_tone_review_analysis",
                      "test_tone_pathway_analysis", "test_tone_titration_analysis", "test_titration_review_analysis")
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


def _open(world, credentials=None, *, hold=True, land=False):
    """Sign in. The earlier holds are released by the operator's switches (the re-review's and the tone review's), so the titration review is the only thing between the launcher and the other modes.
    ``hold=True`` (the default: what a reviewer lives) leaves the titration review's OWN hold in force: until the five scenarios are submitted and verified, the launcher offers nothing else."""
    world["mp"].setenv(rui.OPERATOR_FLAG, rui.OPERATOR_OPEN)
    world["mp"].setenv(tone_ui.OPERATOR_FLAG, tone_ui.OPERATOR_OPEN)
    if hold:
        world["mp"].delenv(tui.OPERATOR_FLAG, raising=False)
    else:
        world["mp"].setenv(tui.OPERATOR_FLAG, tui.OPERATOR_OPEN)
    at = page._open(world, credentials, mode="titration")
    radio = next((item for item in at.radio if item.label == "Review mode"), None)
    if not land and radio is not None and radio.value != page.ui.TITRATION_MODE:
        radio.set_value(page.ui.TITRATION_MODE).run()
        _check(at)
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


def _log_of(world, credentials, scenario_id="TIT-1"):
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    return ftt.TitrationReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"])


def _complete_by_log(world, credentials, scenario_ids):
    for scenario_id in scenario_ids:
        log = _log_of(world, credentials, scenario_id)
        for question, value in ANSWERS.items():
            assert log.answer(question, value)["ok"]
        assert log.lock()["ok"] and log.set_overall(JUDGMENT[scenario_id])["ok"] and log.submit()["ok"]


@pytest.fixture(scope="module")
def journey(world):  # noqa: F811
    """ONE complete review by one faculty reviewer, with a snapshot of every stage of every scenario and the summary (the tests read these; they do not repeat the flow)."""
    credentials = page._faculty(world)
    at = _open(world, credentials)
    assert _modes(at) == [] and page.ui.TITRATION_HELD_NOTE in _everything(at), "the launcher lands on the titration review: there is nothing to choose and nothing else to open"
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
    result["at"] = at
    return result


# -- the flow --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p1_the_whole_human_flow_five_scenarios_in_order_to_the_completion_screen(journey):
    shown = []
    for scenario_id in SCENARIOS:
        text = journey["scenarios"][scenario_id]["blank"]["text"]
        shown.append(next(identifier for identifier, item in ITEMS.items() if item["title"] in text))
    assert shown == list(SCENARIOS) == ["TIT-1", "TIT-2", "TIT-3", "TIT-4", "TIT-5"]
    complete = journey["complete"]
    assert "REVIEW COMPLETE · 5 / 5" in complete["text"] and ftt.COMPLETION_NOTE in complete["text"]
    assert complete["metrics"] == [("Accept", "1"), ("Accept with limitation", "2"), ("Recalibrate", "1"), ("Reject", "1")]
    for scenario_id, following in zip(SCENARIOS, SCENARIOS[1:]):           # auto-next: right after each submit the next scenario (never the same, never a menu) is on screen
        after = journey["scenarios"][scenario_id]["after_submit"]
        assert ITEMS[following]["title"] in after["text"] and tui.LOCK_LABEL in " ".join(label for label, _ in after["buttons"]), scenario_id
        assert f"Scenario {SCENARIOS.index(following) + 1} of 5 · {SCENARIOS.index(following)} of 5 reviewed" in after["text"]


def test_p2_the_landing_page_is_the_titration_review_with_five_scenarios_in_order_and_only_the_first_open(journey):
    landing = journey["landing"]
    assert _nav(landing) == [(_label(1, "TIT-1"), False)] + [(_label(number, scenario_id), True) for number, scenario_id in enumerate(SCENARIOS[1:], 2)]
    assert "Scenario 1 of 5 · 0 of 5 reviewed" in landing["text"] and "Faculty Trajectory Review" in landing["text"] and "Norepinephrine rate changes" in landing["text"]
    assert page.ui.TITRATION_BANNER in landing["text"] and "GI pressure development authority" not in landing["text"], "the banner says what THIS review is"
    assert "Re-review ·" not in landing["text"] and ITEMS["TIT-1"]["title"] in landing["text"]
    assert [button for button, _ in landing["buttons"] if "Summary" in button] == [], "the summary does not exist before the fifth submit"
    assert [ITEMS[scenario_id]["short"] for scenario_id in SCENARIOS] == ["Increase", "Decrease", "Stop", "Sequence", "Restart"]


def test_p3_the_first_pass_screen_has_what_the_reviewer_needs_and_nothing_else(journey):
    for scenario_id, stages in journey["scenarios"].items():
        blank, item = stages["blank"], ITEMS[scenario_id]
        text = blank["text"]
        assert f"**{tui.JUDGING_LABEL}.** {item['purpose']}" in text and item["title"] in text and item["context"] in text and item["intervention"] in text
        assert f"{item['banner']} · {item['note']}" in text and all(fact in text for fact in item["baseline_facts"])
        assert f"On arrival: BP {item['arrival']['sbp']}/{item['arrival']['dbp']} mmHg (MAP {item['arrival']['map']}) · SpO₂ {item['arrival']['spo2']}% · RR {item['arrival']['rr']}/min." in text
        timeline = _tables(blank, "What was done")[0]
        assert [(row["Minute"], row["What was done"], row["What the encounter did"]) for row in timeline] == [(row["minute"], row["action"], row["result"]) for row in item["timeline"]]
        assert len(timeline) == len(item["rate_changes"]) >= 2
        values = _tables(blank, "SBP")[0]
        assert [(row["Minute"], row["SBP"], row["DBP"], row["MAP"]) for row in values] == [(row["minute"], row["sbp"], row["dbp"], row["map"]) for row in ftt.values_table(item)]
        assert sorted(values[0]) == ["DBP", "MAP", "Minute", "SBP"] and tui.PRESSURE_ONLY_NOTE in text and tui.CHART_NOTE in text
        assert ("Heart rate and capillary refill are intentionally not displayed in this pressure-trajectory review: they were not recomputed for these trajectories." in text
                and "Dashed vertical lines mark each change of the norepinephrine rate (mcg/min); the number matches the table above." in text), "the notes, in their own words (not the module's constants)"
        radios = _scenario_radios(blank)
        assert [(label, options, value) for label, options, value in radios] == [(QUESTION_LABELS[q], CHOICES[q], None) for q in ANSWERS]
        assert [label for label, _ in blank["text_areas"]] == ["Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)"]
        assert [(label, disabled) for label, disabled in blank["buttons"] if label in (tui.LOCK_LABEL, tui.NEXT_LABEL, tui.FINISH_LABEL)] == [(tui.LOCK_LABEL, True)]
        assert not any("Q5H" in label or "STOPPING" in label for label, _, _ in radios) and "experiment stops" not in text
        assert len(blank["charts"]) == 1


def test_p3b_the_screens_speak_clinical_language_rate_in_mcg_min_and_nothing_else():
    for item in ITEMS.values():
        text = json.dumps(ftt.blind_view(item))
        assert set(re.findall(r"mcg/[a-z/]+", text)) == {"mcg/min"}, "only absolute rates in mcg/min are ever written"


def test_p3c_no_screen_of_the_flow_shows_heart_rate_or_capillary_refill_only_the_note_names_them(journey):
    snapshots = [("landing", journey["landing"])] + [(f"{sid}/{stage}", snap) for sid, stages in journey["scenarios"].items() for stage, snap in stages.items()] + [("complete", journey["complete"])]
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


def test_p4_every_chart_and_table_is_exactly_the_stored_trajectory_and_marks_each_rate_change(journey):
    for scenario_id, stages in journey["scenarios"].items():
        item = ITEMS[scenario_id]
        for stage in ("blank", "answered", "locked", "overall"):
            assert _chart_rows(stages[stage]) == _expected_chart_rows(item), (scenario_id, stage)
        specs = stages["blank"]["chart_specs"]
        assert len(specs) == 1 and '"domain": [0, 140]' in specs[0] and "Minutes since arrival" in specs[0], scenario_id
        assert max(point["sbp"] for point in item["common"]) <= ftt.y_axis_max(item), "nothing is clipped"
        marks = ftt.markers(item)
        for mark in marks:                                                              # (the chart specification is dumped with ASCII escapes: the middle dot is ·)
            assert f'"minute": {mark["minute"]}, "label": "{mark["label"]}"'.replace("·", "\\u00b7") in specs[0], (scenario_id, mark)
        drawn = set(re.findall(r'"label": "(\d \\u00b7[^"]*)"', specs[0]))                  # (the rule and the text layers both carry each marker)
        assert drawn == {mark["label"].replace("·", "\\u00b7") for mark in marks} and len(drawn) == len(item["rate_changes"]), "one marker per change of the rate and nothing else"
    assert ("1 \\u00b7 start 5" in journey["scenarios"]["TIT-4"]["blank"]["chart_specs"][0] and "4 \\u00b7 stop" in journey["scenarios"]["TIT-4"]["blank"]["chart_specs"][0]
            and "3 \\u00b7 restart 10" in journey["scenarios"]["TIT-5"]["blank"]["chart_specs"][0])


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


def test_p6_the_completion_screen_counts_tabulates_and_states_the_current_limitations_only_there(journey):
    complete = journey["complete"]
    text = complete["text"]
    assert "REVIEW COMPLETE · 5 / 5" in text and ftt.COMPLETION_NOTE in text and "not a score and not a clinical validation" in text
    summary = _tables(complete, "Overall")[0]
    assert [(row["Scenario"], row["Overall"]) for row in summary] == [(ITEMS[scenario_id]["short"], JUDGMENT[scenario_id]) for scenario_id in SCENARIOS]
    assert [[row[q] for q in ANSWERS] for row in summary] == [list(ANSWERS.values())] * 5
    for scenario_id in SCENARIOS:
        assert f"{ITEMS[scenario_id]['short']} ({JUDGMENT[scenario_id]}, overall): overall note for {scenario_id}" in text
    assert tui.LIMITATIONS_HEADING == "CURRENT LIMITATIONS" and tui.LIMITATIONS_HEADING in text
    for entry in LOADED["limitations"]:
        assert entry["text"] in " ".join(complete["markdown"]), entry["id"]
    for needle in ("explicit absolute norepinephrine rates in mcg/min", "mcg/kg/min", "pressure target", "ends the modelled infusion", "neither shown nor judged", "pump"):
        assert needle in text, needle
    assert [(label, disabled) for label, disabled in complete["buttons"] if label.startswith("✓") or label in ("Summary", "Sensitivity (optional)")] == [
        *[(_label(number, scenario_id, True), False) for number, scenario_id in enumerate(SCENARIOS, 1)], ("Summary", False)]
    for forbidden in ("parameter", "legacy", "Legacy", "comparator", "CENTER_REFERENCE", "sensitivity", "Sensitivity"):
        assert forbidden not in text, forbidden
    assert not re.search(r"\bLOW\b|\bHIGH\b", text), "the other settings are named nowhere on the summary"


def test_p6b_the_limitations_are_stated_nowhere_before_the_review_is_complete(journey):
    for scenario_id, stages in journey["scenarios"].items():
        for stage, snapshot in stages.items():
            if (scenario_id, stage) == (LAST, "after_submit"):                       # the screen after the fifth submit IS the completion screen
                continue
            blob = snapshot["text"] + snapshot["protos"]
            for token in ("CURRENT LIMITATIONS", "ends the modelled infusion", "neither shown nor judged", "pressure target", "mcg/kg/min", "not yet validated"):
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
    allowed = ("COMMON_TONE", "CONSCIOUSNESS_UNDER", "PUMP_DEPENDENCE", "consciousness", "mcg/kg", "pump", "map target", "titrat", "MALFORMED_ORDER", "EXPLICIT_ABSOLUTE", "NO_WEIGHT", "NO_MAP")
    leaks = [item for item in _leaks(snapshot) if item[1] not in allowed]
    assert leaks == [], leaks
    assert "titrat" in snapshot["text"].lower(), "(the limitations name titration to a pressure target: that is the allowed reason)"


def test_p7c_the_leak_detector_can_fail_it_sees_a_leak_in_the_sidebar_a_help_text_a_label_a_chart_and_a_limitation(world, monkeypatch):  # noqa: F811
    import streamlit as st
    real_header, real_chart = tui._header, tui.tui.pressure_chart
    injected = {"sidebar": lambda: st.sidebar.caption("CENTER_REFERENCE / half-effect"), "tooltip": lambda: st.button("x", help="the CENTER_REFERENCE configuration", key="leak_help"),
                "label": lambda: st.radio("legacy comparator", ["a", "b"], key="leak_label"), "markdown link": lambda: st.markdown("[the key](docs/revision/PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json)"),
                "limitation": lambda: st.caption("MALFORMED_ORDER_CLOSES_THE_MODELLED_INFUSION"), "other setting": lambda: st.caption("The LOW setting of the response."),
                "time constant": lambda: st.caption("The offset time constant is 2.5 minutes."), "weight": lambda: st.caption("Dosed at 0.1 mcg/kg/min.")}
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
    assert any(path.endswith("PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_SET.json") for path in reads), "the page must read its own set"


def test_p8b_the_file_read_detector_can_fail_it_sees_every_way_of_opening_a_file(world, monkeypatch):  # noqa: F811
    real_header = tui._header
    sources = ROOT / "docs" / "revision" / "PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json"
    readers = {"Path.open": lambda: sources.open("rb").read(1), "Path.read_text": lambda: ftr.SET_PATH.read_text(encoding="utf-8"), "open": lambda: open(ftm.SET_PATH, "rb").read(1),
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


# -- persistence ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p10_a_refresh_restores_answers_comment_lock_overall_and_progress_and_a_locked_answer_cannot_be_changed(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _radio(at, "Q1 ·").set_value("Partly")
    _radio(at, "Q2 ·").set_value("Too late")
    at.run()
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("the rise looks slow").run()
    _check(at)
    state = _log_of(world, credentials).state()
    assert state["blind"] == {"Q1": "Partly", "Q2": "Too late"} and state["blind_comment"] == "the rise looks slow" and state["status"] == "IN_PROGRESS"
    again = _open(world, credentials)                                                          # a refresh: a new session of the same account
    assert [value for _, _, value in _scenario_radios(_snap(again))][:2] == ["Partly", "Too late"] and next(item for item in again.text_area if item.label.startswith("Optional comment")).value == "the rise looks slow"
    for question in ("Q3", "Q4", "Q5"):
        _radio(again, question + " ·").set_value(ANSWERS[question])
    _radio(again, "Q1 ·").set_value("Expected")
    _radio(again, "Q2 ·").set_value("Plausible")
    again.run()
    _check(again)
    _lock(again)
    locked = _log_of(world, credentials).state()
    assert locked["locked"] and locked["locked_answers"] == ANSWERS and locked["locked_comment"] == "the rise looks slow"
    refreshed = _open(world, credentials)
    snapshot = _snap(refreshed)
    assert "Your first impression (locked)" in snapshot["expanders"] and [(label, options) for label, options, _ in _scenario_radios(snapshot)] == [("Overall judgment", list(ftr.OVERALL))]
    assert not _log_of(world, credentials).answer("Q1", "Wrong")["ok"] and _log_of(world, credentials).state()["locked_answers"] == ANSWERS
    _overall(refreshed, "TIT-1", comment="note")
    after = _open(world, credentials)
    assert _radio(after, "Overall judgment").value == JUDGMENT["TIT-1"] and _log_of(world, credentials).state()["overall"] == "ACCEPT"
    _submit(after, "TIT-1")
    done = _open(world, credentials)
    assert ITEMS["TIT-2"]["title"] in _everything(done) and "Scenario 2 of 5 · 1 of 5 reviewed" in _everything(done), "after a submit and a refresh, the next scenario is where the reviewer is"
    assert _nav(_snap(done))[0] == (_label(1, "TIT-1", True), False)
    assert len(list(_log_of(world, credentials).records.glob(_log_of(world, credentials).record_path.stem + "*"))) == 1


def test_p10b_a_second_submit_creates_no_second_record_and_a_failed_submit_moves_nothing_on(world, monkeypatch):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    _lock(at)
    _overall(at, "TIT-1")
    with monkeypatch.context() as patch:
        patch.setattr(ftt.TitrationReviewLog, "submit", lambda self: {"ok": False, "why": "disk full"})
        _button(at, tui.NEXT_LABEL).click().run()
        _check(at)
        assert "Your review could not be saved, so nothing moved on: disk full" in _everything(at) and ITEMS["TIT-1"]["title"] in _everything(at) and not _log_of(world, credentials).state()["submitted"]
    _submit(at, "TIT-1")
    assert _log_of(world, credentials).state()["submitted"]
    second = _log_of(world, credentials).submit()
    assert not second["ok"] and second["why"] == "already submitted" and len(list(_log_of(world, credentials).records.glob(_log_of(world, credentials).record_path.stem + "*"))) == 1


def test_p10c_a_refused_overall_comment_does_not_close_the_scenario_behind_the_reviewer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    _lock(at)
    _overall(at, "TIT-1")
    next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value("call me at dr.someone@example.com").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    _button(at, tui.NEXT_LABEL).click().run()
    _check(at)
    assert "The overall comment in the box is not saved" in _everything(at) and not _log_of(world, credentials).state()["submitted"] and ITEMS["TIT-1"]["title"] in _everything(at)
    next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value("the decay is gradual").run()
    _submit(at, "TIT-1")
    assert _log_of(world, credentials).state()["overall_comment"] == "the decay is gradual" and ITEMS["TIT-2"]["title"] in _everything(at)


def test_p10e_a_refused_first_pass_comment_is_not_locked_behind_the_reviewer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("patient MRN 12345678").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    _button(at, tui.LOCK_LABEL).click().run()
    _check(at)
    assert "The comment in the box is not saved" in _everything(at) and not _log_of(world, credentials).state()["locked"] and _log_of(world, credentials).state()["blind_comment"] == ""
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("the rise looks smooth").run()
    _lock(at)
    assert _log_of(world, credentials).state()["locked"] and _log_of(world, credentials).state()["locked_comment"] == "the rise looks smooth"


def test_p10d_a_lock_from_an_out_of_date_screen_locks_nothing(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    other = _log_of(world, credentials)                                                      # another window of the same account changes an answer after this screen was drawn
    assert other.answer("Q3", "Too large")["ok"]
    _button(at, tui.LOCK_LABEL).click().run()
    _check(at)
    assert not _log_of(world, credentials).state()["locked"] and "Nothing was locked" in _everything(at)


# -- the earlier reviews and the other modes ---------------------------------------------------------------------------------------------------------------------------------------
def test_p11_a_whole_review_leaves_the_earlier_reviews_pages_and_records_untouched(journey, world):  # noqa: F811
    store = Path(world["store"]) / "faculty_review"
    for name in (ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR, ftm.SUBDIR, ftm.RECORDS_SUBDIR, ftm.SENSITIVITY_SUBDIR):
        assert not (store / name).exists(), f"the titration review wrote into {name}"
    written = {path.parent.name for path in store.rglob("*") if path.is_file()}
    assert {ftt.SUBDIR, ftt.RECORDS_SUBDIR} <= written
    assert len(list((store / ftt.RECORDS_SUBDIR).glob("*.json"))) >= 5
    assert ftm.load_set()["digest"] == ftm.PINNED_SET_DIGEST and rr.load_set()["digest"] == rr.PINNED_SET_DIGEST


def test_p11b_after_completion_the_other_modes_return_by_an_explicit_choice_and_the_titration_data_is_intact(journey, world):  # noqa: F811
    at = _open(world, journey["credentials"], land=True)
    assert _modes(at) == [[page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.MANAGEMENT_MODE, page.ui.LIVE_MODE]]
    assert next(item for item in at.radio if item.label == "Review mode").value == page.ui.MANAGEMENT_MODE, "released, the landing page is the newest review, the management-trace review (P3-514)"
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TITRATION_MODE).run()
    _check(at)
    assert "REVIEW COMPLETE · 5 / 5" in _everything(at) and page.ui.TITRATION_HELD_NOTE not in _everything(at)
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TONE_MODE).run()
    _check(at)
    assert ITEMS["TIT-1"]["title"] not in _everything(at) and page.ui.TONE_BANNER in _everything(at), "the tone review is its own page again"
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.LIVE_MODE).run()
    _check(at)
    assert [item for item in at.selectbox if item.label == "Review encounter"] and page.ui.BANNER in _everything(at)
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TITRATION_MODE).run()
    _check(at)
    assert "REVIEW COMPLETE · 5 / 5" in _everything(at) and page.ui.TITRATION_BANNER in _everything(at)


# -- the hold ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p12_until_the_five_scenarios_are_submitted_and_verified_the_launcher_offers_nothing_else_and_a_forged_choice_reads_nothing_of_the_other_modes(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    text = _everything(at)
    assert _modes(at) == [] and page.ui.TITRATION_HELD_NOTE in text and page.ui.TITRATION_BANNER in text and ITEMS["TIT-1"]["title"] in text
    assert not [item for item in at.selectbox if item.label == "Review encounter"] and not _button(at, "Begin review encounter") and not _button(at, "Abandon the unfinished attempt")
    _OPENED["paths"].clear()
    _OPENED["on"] = True
    try:
        for key, value in ((page.ui.MODE_CHOICE_KEY, page.ui.TRAJECTORY_MODE), (page.ui.MODE_KEY, page.ui.LIVE_MODE), (page.ui.MODE_CHOICE_KEY, page.ui.REREVIEW_MODE), (page.ui.MODE_KEY, page.ui.TONE_MODE),
                           (page.ui.MODE_CHOICE_KEY, page.ui.TONE_MODE)):
            at.session_state[key] = value
            at.run()
            _check(at)
            snapshot = _snap(at)
            assert _modes(at) == [] and ITEMS["TIT-1"]["title"] in snapshot["text"] and "Re-review ·" not in snapshot["text"] and ITEMS["TIT-1"]["title"] in snapshot["text"], (key, value)
            assert at.session_state[page.ui.MODE_CHOICE_KEY] == page.ui.TITRATION_MODE and _leaks(snapshot) == [], (key, value)
    finally:
        _OPENED["on"] = False
    assert [path for path in _OPENED["paths"] if any(name in path for name in OTHER_REVIEW_FILES)] == [], "a forged choice of another mode read nothing of it"


def test_p12b_the_hold_is_released_only_by_five_verified_records_by_the_operators_switch_and_what_cannot_be_decided_is_held(world, monkeypatch):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS[:-1])
    assert _modes(_open(world, credentials)) == [], "four of five do not release it"
    _complete_by_log(world, credentials, (LAST,))
    done = _open(world, credentials, land=True)
    assert _modes(done) == [[page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.MANAGEMENT_MODE, page.ui.LIVE_MODE]] and page.ui.TITRATION_HELD_NOTE not in _everything(done)
    assert next(item for item in done.radio if item.label == "Review mode").value == page.ui.MANAGEMENT_MODE, "released, the landing page is the newest review (P3-514)"
    next(item for item in done.radio if item.label == "Review mode").set_value(page.ui.TITRATION_MODE).run()
    _check(done)
    assert "REVIEW COMPLETE · 5 / 5" in _everything(done)
    log = _log_of(world, credentials, "TIT-3")
    kept = log.record_path.read_text(encoding="utf-8")
    log.record_path.unlink()                                                          # the log says submitted, the record that must verify it is gone: the hold comes back
    assert _modes(_open(world, credentials)) == []
    log.record_path.write_text(json.dumps({"record_type": ftt.RECORD_TYPE, "record_id": "forged"}), encoding="utf-8")
    assert _modes(_open(world, credentials)) == []
    log.record_path.write_text(kept, encoding="utf-8")
    assert _modes(_open(world, credentials)) != []
    other = page._faculty(world)
    assert [list(item.options) for item in _open(world, other, hold=False, land=True).radio if item.label == "Review mode"] == [
        [page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.MANAGEMENT_MODE, page.ui.LIVE_MODE]], "the operator's switch"
    monkeypatch.setenv(tui.OPERATOR_FLAG, "ON")                                       # anything but 'off' leaves the hold in force
    assert _modes(page._open(world, other, mode="titration")) == []
    monkeypatch.setattr(ftt, "load_set", lambda *args, **kwargs: {"ok": False, "problems": ["unverifiable"], "digest": None, "items": {}, "limitations": [], "audit": {}})
    monkeypatch.delenv(tui.OPERATOR_FLAG, raising=False)
    at = page._open(world, credentials, mode="titration")
    assert _modes(at) == [] and "The stored trajectories cannot be verified" in _everything(at), "an unverifiable set holds"


def test_p12c_the_hold_predicate_itself_fails_closed_for_no_store_no_faculty_account_and_an_unreadable_store(world, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.delenv(tui.OPERATOR_FLAG, raising=False)

    class Review:
        FACULTY_ROLES = ("faculty", "administrator")

        def __init__(self, root):
            self.root = root

        def review_root(self):
            return self.root

    class Layer:
        bundles = None

        def __init__(self, root):
            self.review = Review(root)
    faculty = {"user": {"role": "faculty", "id": 7}}
    assert tui.other_modes_held(None, Layer(tmp_path), None) is True and tui.other_modes_held(None, Layer(tmp_path), {"user": {"role": "resident", "id": 1}}) is True
    assert tui.other_modes_held(None, Layer(None), faculty) is True, "no review store"
    assert tui.other_modes_held(None, Layer(tmp_path), faculty) is True, "nothing submitted"
    monkeypatch.setenv(tui.OPERATOR_FLAG, "off")
    assert tui.other_modes_held(None, Layer(None), None) is False, "the operator's switch releases it"
    monkeypatch.setenv(tui.OPERATOR_FLAG, "ON")
    assert tui.other_modes_held(None, Layer(tmp_path), faculty) is True


def test_p13_a_resident_in_the_process_sees_none_of_it(world):  # noqa: F811
    at = page._open(world, page.RESIDENT, mode="titration")
    text = _everything(at)
    for token in ("Faculty Trajectory Review", "Norepinephrine rate changes", ITEMS["TIT-1"]["title"], "REVIEW COMPLETE", tui.LOCK_LABEL, "titration review"):
        assert token not in text, token
    assert not _modes(at)


def test_p14_nothing_of_the_authority_the_shadow_or_the_pressure_grant_reaches_the_review_screens(journey):
    for scenario_id, stages in journey["scenarios"].items():
        for stage, snapshot in stages.items():
            if (scenario_id, stage) == (LAST, "after_submit"):                       # the screen after the fifth submit IS the completion screen (its limitations say "not supported")
                continue
            blob = snapshot["text"] + snapshot["protos"]
            for token in page.INTERNALS + ("authority", "Authority", "shadow", "GRANT", "norepinephrine_rate"):
                assert token not in blob, (scenario_id, stage, token)
            assert not re.search(r"\bsupport\b|\bwriter\b", blob), (scenario_id, stage)
    complete = journey["complete"]["text"] + journey["complete"]["protos"]
    for token in page.INTERNALS + ("authority", "Authority", "shadow", "GRANT", "norepinephrine_rate"):
        assert token not in complete, token


def test_p15_the_launcher_orders_the_three_holds_and_changes_nothing_without_the_titration_predicate():
    """The launcher itself, with no Streamlit: the re-review hold has precedence over the tone hold and the tone hold over the titration hold; a predicate that raises or says True shows the titration page alone;
    one that says False offers the five modes; without the predicate nothing changes."""
    class Fake:
        def __init__(self, state=None, choose=None):
            self.session_state, self.warnings, self.captions, self.choose = dict(state or {}), [], [], choose

        def title(self, *args, **kwargs): pass

        def warning(self, text):
            self.warnings.append(text)

        def caption(self, text):
            self.captions.append(text)

        def expander(self, *args, **kwargs):
            import contextlib
            return contextlib.nullcontext()

        def radio(self, label, modes, index=0, **kwargs):
            self.modes = list(modes)
            return self.choose or modes[index]

    class Layer:
        review = object()

    def run(*, re_hold=False, tone_hold=False, titration_hold=None, choose=None, state=None, default=page.ui.TITRATION_MODE, with_titration=True):
        fake, drew = Fake(state, choose), []
        extra = dict(titration_page=lambda *a: drew.append("titration"), hold_titration=titration_hold) if with_titration else {}
        page.ui.launcher(fake, Layer, {}, None, None, None, trajectory_page=lambda *a: drew.append("first"), rereview_page=lambda *a: drew.append("re"), tone_page=lambda *a: drew.append("tone"),
                         default_mode=default, hold_prior_modes=lambda *a: re_hold, hold_other_modes=lambda *a: tone_hold, **extra)
        return fake, drew

    def raises(*args):
        raise RuntimeError("cannot tell")
    for predicate in (raises, lambda *args: True):
        fake, drew = run(titration_hold=predicate)
        assert drew == ["titration"] and fake.warnings == [page.ui.TITRATION_BANNER] and fake.captions == [page.ui.TITRATION_HELD_NOTE] and fake.session_state[page.ui.MODE_CHOICE_KEY] == page.ui.TITRATION_MODE
    fake, drew = run(titration_hold=lambda *args: False)
    assert drew == ["titration"] and fake.warnings == [page.ui.TITRATION_BANNER] and fake.modes == [page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.TITRATION_MODE, page.ui.LIVE_MODE]
    fake, drew = run(titration_hold=lambda *args: False, choose=page.ui.TONE_MODE, default=page.ui.TONE_MODE)
    assert drew == ["tone"] and fake.warnings == [page.ui.TONE_BANNER]
    fake, drew = run(titration_hold=lambda *args: False, choose=page.ui.TRAJECTORY_MODE, state={page.ui.MODE_KEY: page.ui.TRAJECTORY_MODE})
    assert drew == ["first"] and fake.warnings == [page.ui.BANNER]
    # the precedence of the holds
    fake, drew = run(re_hold=True, tone_hold=True, titration_hold=lambda *args: True)
    assert drew == ["re"] and fake.warnings == [page.ui.BANNER] and fake.captions == [page.ui.HELD_NOTE]
    fake, drew = run(re_hold=False, tone_hold=True, titration_hold=lambda *args: True)
    assert drew == ["tone"] and fake.warnings == [page.ui.TONE_BANNER] and fake.captions == [page.ui.TONE_HELD_NOTE]
    # without the titration page or its predicate the launcher is exactly what it was
    fake, drew = run(with_titration=False, default=page.ui.TONE_MODE)
    assert drew == ["tone"] and fake.warnings == [page.ui.TONE_BANNER] and fake.modes == [page.ui.TRAJECTORY_MODE, page.ui.REREVIEW_MODE, page.ui.TONE_MODE, page.ui.LIVE_MODE]
    fake, drew = run(titration_hold=None)
    assert drew == ["titration"] and fake.modes[-2:] == [page.ui.TITRATION_MODE, page.ui.LIVE_MODE], "a page without a predicate is offered as a mode and never held"


def test_p17_a_forged_route_to_the_summary_or_to_a_scenario_that_is_not_open_shows_nothing_of_the_summary_and_nothing_of_the_later_scenarios(world):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS[:-1])
    at = _open(world, credentials)
    for forged in (tui.SUMMARY_VIEW, "TIT-9", "TIT-5", None, 7):
        at.session_state[tui.VIEW_KEY] = forged
        at.run()
        _check(at)
        snapshot = _snap(at)
        text = snapshot["text"]
        assert ITEMS[LAST]["title"] in text and tui.LOCK_LABEL in " ".join(label for label, _ in snapshot["buttons"]), forged
        assert tui.LIMITATIONS_HEADING not in text and "REVIEW COMPLETE" not in text and "Comments to follow up" not in text and _leaks(snapshot) == [], forged
        assert [label for label, _ in snapshot["buttons"] if "Summary" in label] == [], "no summary button before the fifth submit"
    fresh = page._faculty(world)
    at = _open(world, fresh)
    for forged in (tui.SUMMARY_VIEW, "TIT-3", "TIT-5"):
        at.session_state[tui.VIEW_KEY] = forged
        at.run()
        _check(at)
        text = _everything(at)
        assert ITEMS["TIT-1"]["title"] in text and ITEMS["TIT-3"]["title"] not in text and ITEMS["TIT-5"]["title"] not in text and "REVIEW COMPLETE" not in text, forged


@pytest.mark.parametrize("payload", ["[]", '"x"', "7", '{"linkage": "x"}', '{"overall": [1]}', '{"first_pass": 3, "overall": "x", "linkage": []}', "null", ""])
def test_p16_a_malformed_record_file_is_a_technical_problem_not_a_crash(world, payload):  # noqa: F811
    credentials = page._faculty(world)
    _complete_by_log(world, credentials, SCENARIOS)
    _log_of(world, credentials, "TIT-3").record_path.write_text(payload, encoding="utf-8")
    at = _open(world, credentials)
    _check(at)
    text = _everything(at)
    assert "REVIEW COMPLETE" not in text and "4 / 5 scenarios reviewed so far" in text and "A technical check found something" in text
    assert tui.LIMITATIONS_HEADING not in text and not [entry["text"] for entry in LOADED["limitations"] if entry["text"][:40] in text], "the limitations belong to the completed review only, at the page too"
    at.session_state[tui.VIEW_KEY] = tui.SUMMARY_VIEW
    at.run()
    _check(at)
    assert tui.LIMITATIONS_HEADING not in _everything(at) and "ends the modelled infusion" not in _everything(at)
    assert not [item for item in at.exception] and "Traceback" not in text and "AttributeError" not in text
    assert _modes(at) == [], "a record that does not verify keeps the hold"
