"""P3-352 to P3-358 (page level): the FACULTY TRAJECTORY RE-REVIEW on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

It runs the human flow a faculty reviewer follows for the blind re-review -- login (the re-review is the landing page: no choice to make), FR-B with no comparator and no identity of the configuration, five answers,
a refresh (state restored), the lock (irreversible), the overall judgment, ONE submit, the automatic move to FR-C, FR-E and FR-G, the completion screen -- and attacks it: leakage of the configuration, the other sets, the
earlier trajectory, the earlier judgments, the legacy comparator or a technical link; a locked answer edited; a refresh that loses answers; a failed submit that moves on; a resident in the process; the first review's
page, set and records disturbed; the first-pass screens reading any file that holds another set or the earlier review.
"""
import json
import os
import re
import sys
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr
import faculty_trajectory_rereview_ui as rui
import test_phase3_faculty_review_page as page
import test_phase3_trajectory_review_page as old
from test_phase3_faculty_review_page import world  # noqa: F401  (the module's fixture: one review process, one store, individual accounts)

ROOT = Path(__file__).resolve().parent
LOADED = rr.load_set()
ITEMS = LOADED["items"]
CANDIDATES = json.loads(rr.CANDIDATE_SET_PATH.read_text(encoding="utf-8"))
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No"}
JUDGMENT = {"FR-B": "ACCEPT", "FR-C": "ACCEPT_WITH_LIMITATION", "FR-E": "RECALIBRATE", "FR-G": "REJECT"}
QUESTION_LABELS = {"Q1": "Q1 · DIRECTION: Does the physiologic evolution move in the expected direction?", "Q2": "Q2 · TIMING: Does the response occur:", "Q3": "Q3 · MAGNITUDE: Is the magnitude:",
                   "Q4": "Q4 · MANAGEMENT RESPONSE: Is the response to intervention:", "Q5": "Q5 · EDUCATIONAL RISK: Could this trajectory mislead a resident?"}
CHOICES = {"Q1": ["Expected", "Partly", "Wrong"], "Q2": ["Too early", "Plausible", "Too late"], "Q3": ["Too small", "Plausible", "Too large"], "Q4": ["Coherent", "Uncertain", "Incoherent"], "Q5": ["No", "Maybe", "Yes"]}
#: Everything a reviewer must never be able to read on these pages (the identity of the configuration, the other sets, the comparator, the earlier review, the sources, a technical link).
FORBIDDEN = ("CENTER_REFERENCE", "CONJUNTO", "JOINT_REGION", "joint region", "witness", "legacy", "comparator", "candidate", "kernel", "parameter", "bleed rate", "preload", "snapshot", "grant", "bundle", "artifact",
             "digest", "phase3", "PRESSURE_ONLY", "docs/", ".json", ".md", "http", "download", "reveal", "sensitivity", "Common authority", "earlier trajectory")
FORBIDDEN_WORDS = (r"\bLOW\b", r"\bHIGH\b")
OTHER_REVIEW_FILES = ("PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json", "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json", "PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json", "PHASE3_JOINT_REGION_V1_BLIND_KEY.json",
                      "PHASE3_PRESSURE_AUTHORITY_SERIES.json", "PHASE3_GI_JOINT_REGION_V1.json", "region_conjunta_v1")


# -- helpers --------------------------------------------------------------------------------------------------------------------------------------------------------------------
#: Every file the process opens while ``_OPENED["on"]`` is set. An audit hook sees ``open``, ``Path.open``, ``Path.read_text`` and ``os.open`` alike: there is no way to read a file that it does not see.
_OPENED = {"on": False, "paths": []}


def _audit(event, args):
    if _OPENED["on"] and event == "open":
        _OPENED["paths"].append(str(args[0]))


sys.addaudithook(_audit)


def _proto_text(at) -> str:
    """EVERY element the browser receives from the main area AND the sidebar, as its protobuf text (labels, values, help texts, options, placeholders, expander labels). A chart is its specification without the library's own schema URL."""
    out = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            proto = getattr(child, "proto", None)
            if getattr(child, "type", "") == "vega_lite_chart":
                out.append(json.dumps({key: value for key, value in json.loads(proto.spec).items() if key != "$schema"}))
            elif proto is not None:
                out.append(str(proto))
            walk(child)
    walk(at.main)
    walk(at.sidebar)
    return "\n".join(out)


def _leaks(snapshot) -> list:
    """What a screen shows that it must not: any forbidden token in the visible text or in any element's own text (help, labels, sidebar, chart), a forbidden word, a link, a download."""
    found = []
    for source in ("text", "protos"):
        lowered = snapshot[source].lower()
        found += [(source, token) for token in FORBIDDEN if token.lower() in lowered]
        found += [(source, pattern) for pattern in FORBIDDEN_WORDS if re.search(pattern, snapshot[source])]
    found += [("kinds", kind) for kind in snapshot["kinds"] & {"download_button", "link_button", "page_link", "iframe", "html", "code", "json"}]
    found += [("links", "markdown link") for _ in [0] if re.search(r"\]\(|<a |href", " ".join(snapshot["markdown"]))]
    return found


def _open(world, credentials=None):
    """Sign in. The re-review is the landing page of the launcher: the reviewer makes no choice at all."""
    at = page._open(world, credentials, mode="rereview")
    assert next(item for item in at.radio if item.label == "Review mode").value == page.ui.REREVIEW_MODE
    return at


def _everything(at) -> str:
    return old._everything(at)


def _visible_text(at) -> str:
    """What the browser shows as text: labels, values, tables and options of the main area (the chart specifications are inspected apart: they carry the library's own schema URL)."""
    out = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            for attribute in ("value", "label", "body"):
                value = getattr(child, attribute, None)
                if isinstance(value, str):
                    out.append(value)
            if getattr(child, "type", "") == "dataframe":
                out.append(str(child.value))
            for option in getattr(child, "options", None) or ():
                out.append(str(option))
            walk(child)
    walk(at.main)
    return "\n".join(out)


def _radio(at, prefix):
    return next(item for item in at.radio if item.label.startswith(prefix))


def _button(at, prefix):
    return next((item for item in at.button if item.label.startswith(prefix)), None)


def _disabled(button) -> bool:
    return bool(button.proto.disabled)


def _check(at):
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _answer(at, upto=5):
    for question in list(ANSWERS)[:upto]:
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    _check(at)


def _lock(at):
    _button(at, rui.LOCK_LABEL).click().run()
    _check(at)


def _overall(at, scenario_id, comment=None):
    _radio(at, "Overall judgment").set_value(JUDGMENT[scenario_id])
    at.run()
    if comment:
        next(item for item in at.text_area if item.label.startswith("Optional overall comment")).set_value(comment)
        at.run()
    _check(at)


def _submit(at, scenario_id):
    _button(at, rui.FINISH_LABEL if scenario_id == "FR-G" else rui.NEXT_LABEL).click().run()
    _check(at)


def _snap(at) -> dict:
    """What the browser would show at this moment: text, radios, buttons, text areas, charts, tables, expanders, metrics, element kinds, session keys."""
    kinds = set()

    def walk(node):
        for child in getattr(node, "children", {}).values():
            kinds.add(getattr(child, "type", ""))
            walk(child)
    walk(at.main)
    specs = [json.dumps({key: value for key, value in spec.items() if key != "$schema"}) for spec in old._charts(at)]      # the vega-lite schema URL is the library's, not a page element
    return {"text": _visible_text(at), "protos": _proto_text(at), "chart_specs": specs, "radios": [(item.label, list(item.options), item.value) for item in at.radio], "buttons": [(item.label, _disabled(item)) for item in at.button],
            "text_areas": [(item.label, item.value) for item in at.text_area], "charts": old._charts(at), "tables": [item.value.to_dict("records") for item in at.dataframe],
            "expanders": [item.label for item in at.expander], "metrics": [(item.label, item.value) for item in at.metric], "kinds": kinds,
            "session_keys": sorted(str(key) for key in at.session_state.keys()), "markdown": [item.value for item in at.markdown]}


def _chart_rows(snapshot) -> set:
    rows = set()
    for spec in snapshot["charts"]:
        rows |= old._data_rows(spec)
    return rows


def _expected_chart_rows(item, source=rui.SERIES_NAME) -> set:
    return {(point["minute"], variable, point[key], source) for point in item["common"] for variable, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))}


def _scenario_radios(snapshot):
    """The question radios on screen (the first radio of every page is the launcher's 'Review mode')."""
    return [entry for entry in snapshot["radios"] if entry[0] != "Review mode"]


@pytest.fixture(scope="module")
def journey(world):  # noqa: F811
    """ONE complete re-review by one faculty reviewer, with a snapshot of every stage of every scenario (the tests read these; they do not repeat the flow)."""
    credentials = page._faculty(world)
    at = _open(world, credentials)
    result = {"credentials": credentials, "landing": _snap(at), "scenarios": {}}
    for scenario_id in rr.SCENARIOS:
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
def test_p1_the_whole_human_flow_four_scenarios_in_order_to_the_completion_screen(journey):
    shown = []
    for scenario_id in rr.SCENARIOS:
        text = journey["scenarios"][scenario_id]["blank"]["text"]
        shown.append(next(identifier for identifier, item in ITEMS.items() if item["title"] in text))
    assert shown == ["FR-B", "FR-C", "FR-E", "FR-G"]
    complete = journey["complete"]
    assert "RE-REVIEW COMPLETE · 4 / 4" in complete["text"] and rr.COMPLETION_NOTE in complete["text"]
    assert complete["metrics"] == [("Accept", "1"), ("Accept with limitation", "1"), ("Recalibrate", "1"), ("Reject", "1")]
    # auto-next: right after each submit the next scenario (never the same, never a menu) is on screen
    for scenario_id, following in zip(rr.SCENARIOS, rr.SCENARIOS[1:]):
        assert ITEMS[following]["title"] in journey["scenarios"][scenario_id]["after_submit"]["text"] and rui.LOCK_LABEL in " ".join(label for label, _ in journey["scenarios"][scenario_id]["after_submit"]["buttons"])


def test_p2_the_landing_page_is_the_re_review_with_four_scenarios_in_order_and_only_the_first_open(journey):
    landing = journey["landing"]
    nav = [(label, disabled) for label, disabled in landing["buttons"] if label in rr.SCENARIOS]
    assert nav == [("FR-B", False), ("FR-C", True), ("FR-E", True), ("FR-G", True)]
    assert "Re-review · scenario 1 of 4 · 0 of 4 reviewed" in landing["text"] and "Faculty Trajectory Review" in landing["text"]
    assert [value for label, _, value in landing["radios"] if label == "Review mode"] == [page.ui.REREVIEW_MODE]
    assert "Scenario 1 of 5" not in landing["text"] and "Optional scenario" not in landing["text"]            # the first review's page is not what the reviewer lands on


def test_p3_the_first_pass_screen_has_what_the_reviewer_needs_and_nothing_else(journey):
    for scenario_id, stages in journey["scenarios"].items():
        blank, item = stages["blank"], ITEMS[scenario_id]
        text = blank["text"]
        assert f"**{rui.JUDGING_LABEL}.** {item['purpose']}" in text and f"**Clinical context.** {item['context']}" in text and item["title"] in text
        assert f"BP {item['arrival']['sbp']}/{item['arrival']['dbp']} mmHg" in text and f"capillary refill {item['arrival']['crt']} s" in text
        # interventions: the table the first review drew, row for row
        timeline = [table for table in blank["tables"] if table and "What was done" in table[0]][0]
        assert [(row["Minute"], row["What was done"], row["What the encounter did"]) for row in timeline] == [(row["minute"], row["action"], row["result"]) for row in item["timeline"]]
        # the values table: the trajectory and the two context variables, labelled as such
        values = [table for table in blank["tables"] if table and "SBP" in table[0]][0]
        assert [(row["Minute"], row["SBP"], row["DBP"], row["MAP"]) for row in values] == [(row["minute"], row["sbp"], row["dbp"], row["map"]) for row in rr.values_table(item)]
        assert "Heart rate (context)" in values[0] and "Capillary refill, s (context)" in values[0] and "they are not part of the pressure trajectory, and they were not recomputed for it" in text
        # five questions with their exact choices, one comment box and ONE lock button that waits for the five answers
        radios = _scenario_radios(blank)
        assert [(label, options, value) for label, options, value in radios] == [(QUESTION_LABELS[q], CHOICES[q], None) for q in ANSWERS]
        assert [label for label, _ in blank["text_areas"]] == ["Optional comment on the trajectory (a short note helps most when Q5 is Maybe or Yes)"]
        assert [(label, disabled) for label, disabled in blank["buttons"] if label in (rui.LOCK_LABEL, rui.NEXT_LABEL, rui.FINISH_LABEL)] == [(rui.LOCK_LABEL, True)]
        assert not any("Q5H" in label or "STOPPING" in label for label, _, _ in radios) and "experiment stops" not in text
        assert len(blank["charts"]) == 1


def test_p4_the_interactive_pressures_are_exactly_the_certified_static_kits(journey):
    certified = {item["scenario_id"]: item for item in CANDIDATES["items"] if item["set"] == "CONJUNTO-1"}
    for scenario_id, stages in journey["scenarios"].items():
        source = certified[scenario_id]
        expected = {(point["minute"], variable, point[key], rui.SERIES_NAME) for point in source["common"] for variable, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))}
        for stage in ("blank", "answered", "locked", "overall"):
            assert _chart_rows(stages[stage]) == expected, (scenario_id, stage)
        values = [table for table in stages["blank"]["tables"] if table and "SBP" in table[0]][0]
        hr_crt = {row["minute"]: (row["hr"], row["crt"]) for row in source["heart_rate_and_capillary_refill"]}
        assert [(row["Minute"], row["SBP"], row["DBP"], row["MAP"], row["Heart rate (context)"], row["Capillary refill, s (context)"]) for row in values] == [
            (point["minute"], int(point["sbp"]), int(point["dbp"]), int(point["map"]), hr_crt[point["minute"]][0], hr_crt[point["minute"]][1]) for point in source["common"]], scenario_id
        timeline = [table for table in stages["blank"]["tables"] if table and "What was done" in table[0]][0]
        assert [(row["#"], row["Minute"], row["What was done"], row["What the encounter did"]) for row in timeline] == [(row["n"], row["minute"], row["action"], row["result"]) for row in source["timeline"]]


def test_p5_the_lock_waits_for_the_five_answers_and_then_nothing_of_the_first_impression_can_be_changed(journey):
    for scenario_id, stages in journey["scenarios"].items():
        assert dict(stages["answered"]["buttons"])[rui.LOCK_LABEL] is False
        assert [value for _, _, value in _scenario_radios(stages["answered"])] == list(ANSWERS.values())
        locked = stages["locked"]
        # after the lock there is no question radio any more: only the overall judgment, whose choices are the four of the first review
        assert [(label, options) for label, options, _ in _scenario_radios(locked)] == [("Overall judgment", list(ftr.OVERALL))]
        assert rui.LOCK_LABEL not in [label for label, _ in locked["buttons"]] and "Your first impression (locked)" in locked["expanders"]
        assert [f"{topic}: **{value}**" for topic, value in zip(("Direction", "Timing", "Magnitude", "Management Response", "Educational Risk"), ANSWERS.values())] == [line for line in locked["markdown"] if re.fullmatch(r"(Direction|Timing|Magnitude|Management Response|Educational Risk): \*\*.*\*\*", line)]
        # the SUBMIT stays off until an overall judgment is chosen
        assert dict(locked["buttons"])[rui.FINISH_LABEL if scenario_id == "FR-G" else rui.NEXT_LABEL] is True
        assert dict(stages["overall"]["buttons"])[rui.FINISH_LABEL if scenario_id == "FR-G" else rui.NEXT_LABEL] is False
        assert [label for label, _ in locked["text_areas"]] == ["Optional overall comment"]


def test_p6_the_completion_screen_counts_lists_and_says_clearly_that_nothing_is_compared(journey):
    complete = journey["complete"]
    text = complete["text"]
    assert "RE-REVIEW COMPLETE · 4 / 4" in text and rr.COMPLETION_NOTE in text and "not a score and not a clinical validation" in text
    summary = [table for table in complete["tables"] if table and "Overall" in table[0]][0]
    assert [(row["Scenario"], row["Overall"]) for row in summary] == list(JUDGMENT.items())
    assert [(row["Scenario"], [row[q] for q in ANSWERS]) for row in summary] == [(scenario_id, list(ANSWERS.values())) for scenario_id in rr.SCENARIOS]
    for scenario_id in rr.SCENARIOS:
        assert f"{scenario_id} ({JUDGMENT[scenario_id]}, overall): overall note for {scenario_id}" in text
    nav = [(label, disabled) for label, disabled in complete["buttons"] if label.endswith(tuple(rr.SCENARIOS)) or label == "Summary"]
    assert nav == [("✓ FR-B", False), ("✓ FR-C", False), ("✓ FR-E", False), ("✓ FR-G", False), ("Summary", False)]
    assert "Optional scenario" not in text and not [label for label, _ in complete["buttons"] if "optional" in label.lower()]
    for forbidden in ("earlier", "other trajectory", "other set", "LOW", "HIGH", "parameter", "legacy", "Legacy", "sensitivity", "engine"):
        assert forbidden not in text, forbidden


# -- blindness ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p7_no_screen_of_the_whole_flow_carries_the_configuration_the_other_sets_the_comparator_or_a_technical_link(journey):
    snapshots = [("landing", journey["landing"])] + [(f"{scenario_id}/{stage}", snapshot) for scenario_id, stages in journey["scenarios"].items() for stage, snapshot in stages.items()] + [("complete", journey["complete"])]
    for name, snapshot in snapshots:
        assert _leaks(snapshot) == [], name
        for spec in snapshot["chart_specs"]:                                                                       # the chart data and its tooltips carry no identity either
            for token in ("CENTER_REFERENCE", "CONJUNTO", "witness", "legacy", "comparator", "candidate", "Common authority", "Legacy"):
                assert token not in spec, (name, token)
        assert not [key for key in snapshot["session_keys"] if re.search(r"center|conjunto|witness|candidate|legacy|comparator|low|high", key, re.I)], (name, snapshot["session_keys"])
        assert not [label for label, *_ in snapshot["radios"] if re.search(r"set|witness|candidate|legacy", label, re.I) and label != "Review mode"], name
    # the sidebar is the account portal and nothing else: it was walked like the main area
    assert "reviewer" in journey["landing"]["protos"].lower() and "Signed in" in journey["landing"]["protos"]


def test_p7b_the_leak_detector_can_fail_it_sees_a_leak_in_the_sidebar_a_help_text_a_label_and_a_chart(world, monkeypatch):  # noqa: F811
    """The detector of p7 is itself tested: each of these injected leaks (the ones a text-only scan of the main area would miss) must be reported."""
    import streamlit as st
    real_header, real_chart = rui._header, rui.tui.pressure_chart
    injected = {"sidebar": lambda: st.sidebar.caption("CENTER_REFERENCE / CONJUNTO-1"), "tooltip": lambda: st.button("x", help="the CENTER_REFERENCE configuration", key="leak_help"),
                "label": lambda: st.radio("legacy comparator", ["a", "b"], key="leak_label"), "markdown link": lambda: st.markdown("[the key](docs/revision/PHASE3_JOINT_REGION_V1_BLIND_KEY.json)")}
    for name, leak in injected.items():
        with monkeypatch.context() as patch:
            patch.setattr(rui, "_header", lambda *args, _leak=leak, **kwargs: (_leak(), real_header(*args, **kwargs))[1])
            at = _open(world)
            assert _leaks(_snap(at)), f"the detector missed a leak in the {name}"
    with monkeypatch.context() as patch:
        patch.setattr(rui.tui, "pressure_chart", lambda *args, **kwargs: real_chart(*args, **kwargs).properties(title="CENTER_REFERENCE trajectory"))
        assert _leaks(_snap(_open(world))), "the detector missed a leak in the chart"


def test_p8_the_first_pass_screens_read_no_file_of_another_set_the_earlier_review_or_the_sources(world):  # noqa: F811
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
    assert any(path.endswith("PHASE3_JOINT_REGION_V1_FACULTY_REREVIEW_SET.json") for path in reads), "the page must read its own set"


def test_p8b_the_file_read_detector_can_fail_it_sees_every_way_of_opening_a_file(world, monkeypatch):  # noqa: F811
    real_header = rui._header
    readers = {"Path.open": lambda: ftr.SET_PATH.open("rb").read(1), "Path.read_text": lambda: ftr.SET_PATH.read_text(encoding="utf-8"), "open": lambda: open(rr.BLIND_KEY_PATH, "rb").read(1),
               "os.open": lambda: os.close(os.open(str(rr.CANDIDATE_SET_PATH), os.O_RDONLY))}
    for name, reader in readers.items():
        with monkeypatch.context() as patch:
            patch.setattr(rui, "_header", lambda *args, _read=reader, **kwargs: (_read(), real_header(*args, **kwargs))[1])
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
    assert [label for label, _ in snapshot["buttons"] if label not in (*rr.SCENARIOS, rui.LOCK_LABEL, "Sign out") and "password" not in label.lower()] == []


# -- persistence --------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p10_a_refresh_restores_the_partial_answers_the_lock_the_overall_choice_and_the_progress(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    for question in ("Q1", "Q2", "Q3"):
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("partial first-pass note")
    at.run()
    # a refresh closes the account session (the app's way with individual accounts): the reviewer signs in again and finds everything
    again = _open(world, credentials)
    assert [value for _, _, value in _scenario_radios(_snap(again))] == ["Expected", "Plausible", "Plausible", None, None]
    assert next(item for item in again.text_area if item.label.startswith("Optional comment")).value == "partial first-pass note"
    assert dict(_snap(again)["buttons"])[rui.LOCK_LABEL] is True
    for question in ("Q4", "Q5"):
        _radio(again, question + " ·").set_value(ANSWERS[question])
    again.run()
    _lock(again)
    locked = _open(world, credentials)
    snapshot = _snap(locked)
    assert [(label, value) for label, _, value in _scenario_radios(snapshot)] == [("Overall judgment", None)] and "Your first impression (locked)" in snapshot["expanders"] and "partial first-pass note" in snapshot["text"]
    _overall(locked, "FR-B")
    chosen = _open(world, credentials)
    assert [value for label, _, value in _scenario_radios(_snap(chosen))] == ["ACCEPT"]
    _submit(chosen, "FR-B")
    submitted = _open(world, credentials)
    text = _everything(submitted)
    assert ITEMS["FR-C"]["title"] in text and "Re-review · scenario 2 of 4 · 1 of 4 reviewed" in text
    assert dict((label, disabled) for label, disabled in _snap(submitted)["buttons"] if label.replace("✓ ", "") in rr.SCENARIOS) == {"✓ FR-B": False, "FR-C": False, "FR-E": True, "FR-G": True}


def test_p11_a_submitted_scenario_can_be_viewed_but_not_changed_and_a_locked_one_is_not_open_to_the_edit_route(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    _lock(at)
    _overall(at, "FR-B", comment="kept as written")
    _submit(at, "FR-B")
    _button(at, "✓ FR-B").click().run()
    _check(at)
    snapshot = _snap(at)
    assert "This scenario is submitted. It is shown read-only." in snapshot["text"] and "Overall: **ACCEPT**" in snapshot["text"] and "Overall comment: kept as written" in snapshot["text"]
    assert _scenario_radios(snapshot) == [] and not snapshot["text_areas"] and not [label for label, _ in snapshot["buttons"] if label in (rui.LOCK_LABEL, rui.NEXT_LABEL, rui.FINISH_LABEL)]
    # the log itself refuses what the page does not offer
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    log = rr.ReReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ITEMS["FR-B"], set_digest=LOADED["digest"], audit=LOADED["audit"])
    assert log.state()["status"] == "SUBMITTED" and not log.answer("Q1", "Wrong")["ok"] and not log.set_overall("REJECT")["ok"] and not log.comment("late")["ok"] and not log.overall_comment("late")["ok"]


def test_p11b_a_lock_never_fixes_what_the_screen_does_not_show_two_windows_of_the_same_account(world):  # noqa: F811
    credentials = page._faculty(world)
    window_a = _open(world, credentials)
    _answer(window_a)
    window_b = _open(world, credentials)                                          # another window of the same account: it changes Q1 in the log
    _radio(window_b, "Q1 ·").set_value("Wrong")
    window_b.run()
    _check(window_b)
    _radio(window_a, "Q2 ·").set_value("Too late")                                # window A, which still shows Q1 = Expected, changes Q2 and then asks to lock
    window_a.run()
    _check(window_a)
    assert _radio(window_a, "Q1 ·").value == "Expected"
    _button(window_a, rui.LOCK_LABEL).click().run()
    _check(window_a)
    log = _log_of(world, credentials)
    assert not log.state()["locked"], "the lock must not fix an answer the reviewer never saw"
    snapshot = _snap(window_a)
    assert "Nothing was locked: this screen was out of date" in snapshot["text"] and [value for _, _, value in _scenario_radios(snapshot)] == ["Wrong", "Too late", "Plausible", "Coherent", "No"], "the screen is rebuilt from the log"
    _lock(window_a)                                                               # now what is shown is what the log holds: the lock goes through, with exactly those answers
    assert log.state()["locked"] and log.state()["locked_answers"] == {"Q1": "Wrong", "Q2": "Too late", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No"}


def test_p11c_a_comment_the_log_refused_does_not_lock_silently_behind_the_reviewer(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer(at)
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("patient MRN 12345678").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    _button(at, rui.LOCK_LABEL).click().run()
    _check(at)
    assert "The comment in the box is not saved" in _everything(at) and not _log_of(world, credentials).state()["locked"]
    next(item for item in at.text_area if item.label.startswith("Optional comment")).set_value("").run()
    _lock(at)
    assert _log_of(world, credentials).state()["locked"]


def _log_of(world, credentials, scenario_id="FR-B"):
    user = world["accounts"].get_user(world["accounts"].authenticate(*credentials))
    return rr.ReReviewLog(Path(world["store"]) / "faculty_review", ftr.reviewer_ref(user["id"]), ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"])


def test_p12_a_failed_submit_does_not_advance_and_says_so(world, monkeypatch):  # noqa: F811
    at = _open(world)
    _answer(at)
    _lock(at)
    _overall(at, "FR-B")
    monkeypatch.setattr(rr.ReReviewLog, "submit", lambda self: {"ok": False, "why": "it could not be saved (a disk error): nothing was changed", "state": self.state()})
    _button(at, rui.NEXT_LABEL).click().run()
    _check(at)
    text = _everything(at)
    assert "Your review could not be saved, so nothing moved on" in text and ITEMS["FR-B"]["title"] in text and ITEMS["FR-C"]["title"] not in text and "Re-review · scenario 1 of 4 · 0 of 4 reviewed" in text


def test_p13_comments_are_saved_refused_when_they_look_like_identifiers_and_reach_the_record_and_the_summary(world):  # noqa: F811
    credentials = page._faculty(world)
    at = _open(world, credentials)
    comment_box = next(item for item in at.text_area if item.label.startswith("Optional comment"))
    comment_box.set_value("patient MRN 12345678 looked unwell").run()
    _check(at)
    assert "This comment is not saved yet" in _everything(at)
    comment_box = next(item for item in at.text_area if item.label.startswith("Optional comment"))
    comment_box.set_value("MAP rises about 4 mmHg per litre: fine").run()
    assert "This comment is not saved yet" not in _everything(_open(world, credentials)) and next(item for item in _open(world, credentials).text_area if item.label.startswith("Optional comment")).value == "MAP rises about 4 mmHg per litre: fine"


# -- boundaries ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_p14_the_whole_re_review_leaves_the_first_reviews_files_and_set_untouched(journey, world):  # noqa: F811
    store = Path(world["store"]) / "faculty_review"
    assert not (store / ftr.SUBDIR).exists() and not (store / ftr.RECORDS_SUBDIR).exists(), "the re-review must not create the first review's directories"
    assert (store / rr.SUBDIR).is_dir() and (store / rr.RECORDS_SUBDIR).is_dir()
    records = sorted((store / rr.RECORDS_SUBDIR).glob("*.json"))
    assert len(records) >= 4 and all(rr.SET_ID in record.name for record in records)
    assert json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))["record_digest"] == ftr.PINNED_SET_DIGEST
    # the summary the page wrote is the re-review's, in the re-review's directory
    assert list((store / rr.SUBDIR).glob("session_summary_*.json"))


def test_p15_the_first_review_is_still_there_by_an_explicit_choice_and_the_two_do_not_share_state(journey, world):  # noqa: F811
    at = _open(world, journey["credentials"])
    assert "RE-REVIEW COMPLETE · 4 / 4" in _everything(at)
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TRAJECTORY_MODE).run()
    _check(at)
    text = _everything(at)
    assert "Scenario 1 of 5" in text and "RE-REVIEW COMPLETE" not in text and "Re-review ·" not in text          # the first review, with its own five scenarios and its own (empty) progress
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.REREVIEW_MODE).run()
    _check(at)
    assert "RE-REVIEW COMPLETE · 4 / 4" in _everything(at)


def test_p16_a_resident_never_reaches_the_re_review_and_nothing_is_created_for_them(world):  # noqa: F811
    at = _open_resident(world)
    text = _everything(at)
    assert not any(item.label == "Review mode" for item in at.radio) and "Faculty Trajectory Review" not in text and not old._charts(at) and "FR-B" not in text and "re-review" not in text.lower()

    class Fake:
        def __init__(self):
            self.errors, self.session_state = [], {}

        def error(self, text):
            self.errors.append(text)

    class Layer:
        review = page.fr
        bundles = page.bundles
    fake = Fake()
    rui.draw(fake, Layer, {"user": {"role": "resident", "id": 99}})
    assert fake.errors == [rui.GENERIC_REFUSAL] and fake.session_state == {}
    assert not any(ftr.reviewer_ref(99) in str(path) for path in (Path(world["store"]) / "faculty_review").rglob("*"))


def _open_resident(world):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=600)
    at.secrets.update(world["secrets"])
    at.run()
    next(item for item in at.text_input if item.label == "Username").set_value(page.RESIDENT[0])
    next(item for item in at.text_input if item.label == "Password").set_value(page.RESIDENT[1])
    next(item for item in at.button if item.label == "Sign in").click().run()
    _check(at)
    return at
