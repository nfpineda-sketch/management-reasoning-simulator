"""UX-003 to UX-011 (page level): the FACULTY TRAJECTORY REVIEW on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

It runs the human flow a faculty reviewer follows -- login, the first scenario BLIND, five answers, a refresh (state restored), the lock, the comparator, the post-reveal answers, the overall judgment, ONE submit,
the automatic move to the next scenario, all the required scenarios, the summary -- and counts what the reviewer had to do. It also attacks the flow: comparator before the lock, first pass edited after the reveal,
a refresh that loses answers, a skipped scenario, a failed submit that must not advance, a tampered or stale review set, a corrupt saved log, a resident in the review process, technical metadata on screen.
"""
import json
import re
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as tui
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr
import test_phase3_faculty_review_page as page
from test_phase3_faculty_review_page import world  # noqa: F401  (the module's fixture: one review process, one store, individual accounts)

ITEMS = ftr.load_set(bundles=bundles, scenario_of=fr.scenario)["items"]
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No", "Q5H": "Understandable"}
TECHNICAL = ("bundle", "artifact", "digest", "grant", "snapshot", "lineage", "replay", "hash", "phase3", "PRESSURE_ONLY", "GRANT_V1", "feedback id", "experiment_id", "encounter_id", ".md", "markdown", "paper form")
DEATH_WORDS = ("death", "died", "dead", "cardiac arrest", "terminal", "moribund", "expired", "exitus", "fatal")
ACTIONS: dict = {}


def _open(world, credentials=None):
    return page._open(world, credentials, mode="trajectory")


def _everything(at):
    """All text the reviewer's browser would receive from the main area: labels, values, tables and the chart specifications."""
    out = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            for attribute in ("value", "label", "body"):
                value = getattr(child, attribute, None)
                if isinstance(value, str):
                    out.append(value)
            kind = getattr(child, "type", "")
            if kind == "dataframe":
                out.append(str(child.value))
            if kind == "vega_lite_chart":
                out.append(child.proto.spec)
            for option in getattr(child, "options", None) or ():
                out.append(str(option))
            walk(child)
    walk(at.main)
    return "\n".join(out)


def _radio(at, prefix):
    return next(item for item in at.radio if item.label.startswith(prefix))


def _button(at, prefix):
    return next((item for item in at.button if item.label.startswith(prefix)), None)


def _charts(at):
    found = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            if getattr(child, "type", "") == "vega_lite_chart":
                found.append(json.loads(child.proto.spec))
            walk(child)
    walk(at.main)
    return found


def _data_rows(spec):
    """Every (minute, variable, mmHg, source) the chart carries, wherever the serializer put it (inline per layer or hoisted to datasets)."""
    rows = set()

    def walk(node):
        if isinstance(node, dict):
            if "source" in node and "mmHg" in node:
                rows.add((node["minute"], node["variable"], node["mmHg"], node["source"]))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(spec)
    return rows


def _sources(spec):
    return {row[3] for row in _data_rows(spec)}


def _count(kind, amount=1):
    ACTIONS[kind] = ACTIONS.get(kind, 0) + amount


def _answer_blind(at, scenario_id):
    halted = ITEMS[scenario_id]["bundle"]["authority_view"]["halted"]
    for question in ("Q1", "Q2", "Q3", "Q4", "Q5") + (("Q5H",) if halted else ()):
        _radio(at, question + " ·").set_value(ANSWERS[question])
        _count("answers")
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _lock(at):
    _button(at, "LOCK FIRST IMPRESSION").click().run()
    _count("clicks")
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _post_and_submit(at, overall="ACCEPT", changed=0):
    _radio(at, "Did seeing the legacy comparator").set_value(ftr.CHANGED["choices"][changed])
    _radio(at, "Overall judgment").set_value(overall)
    _count("answers", 2)
    at.run()
    _button(at, "Submit").click().run()
    _count("clicks")
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _review(at, scenario_id, overall="ACCEPT"):
    assert at.subheader[0].value == ITEMS[scenario_id]["title"], (scenario_id, at.subheader[0].value)
    _answer_blind(at, scenario_id)
    _lock(at)
    _post_and_submit(at, overall)


def _records(world):
    return sorted((world["store"] / "faculty_review" / "trajectory_reviews").glob("*.json")) if (world["store"] / "faculty_review" / "trajectory_reviews").exists() else []


# -- the primary page, blind -----------------------------------------------------------------------------------------------------------------------------------------------
def test_u1_a_faculty_account_lands_on_the_blind_trajectory_review_and_sees_only_clinical_content(world):
    at = _open(world)
    assert not at.exception and at.header[0].value == "Faculty Trajectory Review" and at.subheader[0].value == "57-year-old man, early treatment"
    assert [item.label.replace("✓ ", "") for item in at.button if item.label.startswith("FR-")] == ["FR-B", "FR-A", "FR-E", "FR-G", "FR-F", "FR-D (optional)", "FR-C (optional)"]
    assert [item.disabled for item in at.button if item.label.startswith("FR-")] == [False] + [True] * 6, "only the first scenario can be entered"
    assert [item.label.split(":")[0] for item in at.radio if item.label[0] == "Q"] == ["Q1 · DIRECTION", "Q2 · TIMING", "Q3 · MAGNITUDE", "Q4 · MANAGEMENT RESPONSE", "Q5 · EDUCATIONAL RISK"]
    assert [item.options for item in at.radio if item.label.startswith("Q2")] == [["Too early", "Plausible", "Too late"]]
    assert not any(item.label == "Review encounter" for item in at.selectbox), "the live encounter launcher is not the primary page"
    assert _button(at, "LOCK FIRST IMPRESSION & REVEAL COMPARATOR").disabled is True
    text = _everything(at)
    for word in TECHNICAL:
        assert word.lower() not in text.lower(), word
    assert "Guided reasoning completion" not in text and "Working model" not in text
    assert "estimated time remaining ≈ 20 min (an estimate, not a measurement)" in text and "Scenario 1 of 5" in text
    # BEFORE THE LOCK nothing of the legacy comparator reaches the browser: not in a label, a table or the data of the chart
    assert "legacy" not in text.lower() and "comparator" not in text.replace("before the comparator is revealed", "").replace("REVEAL COMPARATOR", "").lower()
    charts = _charts(at)
    assert len(charts) == 3 and all(_sources(spec) <= {tui.COMMON_NAME} for spec in charts)
    rows = _data_rows(charts[0])
    assert len(rows) == 4 * 3 and {row[3] for row in rows} == {tui.COMMON_NAME}
    view = ftr.blind_view(ITEMS["FR-B"])
    assert {row[:3] for row in rows} == {(point["minute"], name, point[key]) for point in view["common"] for name, key in (("SBP", "sbp"), ("MAP", "map"), ("DBP", "dbp"))}


def test_u2_the_whole_flow_of_one_scenario_refresh_lock_reveal_submit_and_the_automatic_next_scenario(world):
    credentials = page._faculty(world)
    item, link = ITEMS["FR-B"], ITEMS["FR-B"]["bundle"]
    at = _open(world, credentials)
    for question in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _radio(at, question + " ·").set_value(ANSWERS[question])
    at.run()
    assert _button(at, "LOCK FIRST IMPRESSION").disabled is False
    # REFRESH: a brand-new browser session of the same account: the answers are restored, nothing is locked, no comparator is visible
    again = _open(world, credentials)
    assert {question: _radio(again, question + " ·").value for question in ("Q1", "Q2", "Q3", "Q4", "Q5")} == {key: ANSWERS[key] for key in ("Q1", "Q2", "Q3", "Q4", "Q5")}
    assert _button(again, "LOCK FIRST IMPRESSION").disabled is False and "legacy" not in _everything(again).lower() and not again.exception
    # the lock reveals the comparator on the same axes, neutrally labelled, and the first pass is no longer editable
    _lock(again)
    text = _everything(again)
    assert "Legacy comparator — nonauthoritative comparison" in text and "not a reference standard" in text
    assert not any(item.label.startswith("Q1 ·") for item in again.radio) and "LOCK FIRST IMPRESSION" not in "".join(button.label for button in again.button)
    assert [sorted(_sources(spec)) for spec in _charts(again)[:1]] == [[tui.COMMON_NAME, tui.LEGACY_NAME]]
    legacy = {row[:3] for row in _data_rows(_charts(again)[0]) if row[3] == tui.LEGACY_NAME}
    assert {point["sbp"] for point in ftr.comparator_view(item, {"locked": True})["legacy"][1:]} <= {value for (_, variable, value) in legacy if variable == "SBP"} and len(legacy) == 4 * 3
    # a refresh after the lock: still locked, comparator still shown, nothing can be unlocked
    after_lock = _open(world, credentials)
    assert "Legacy comparator — nonauthoritative comparison" in _everything(after_lock) and not any(radio.label.startswith("Q1 ·") for radio in after_lock.radio)
    # the submit button is disabled until the post-reveal questions are answered; nothing moves on before that
    assert _button(after_lock, "Submit").disabled is True and after_lock.subheader[0].value == item["title"]
    _post_and_submit(after_lock, "ACCEPT_WITH_LIMITATION", changed=2)
    assert after_lock.subheader[0].value == ITEMS["FR-A"]["title"], "after the submit the reviewer is moved to the next scenario, with no special menu path"
    assert [item.label for item in after_lock.button if item.label.startswith("✓")] == ["✓ FR-B"]
    assert "1 of 5 required scenarios reviewed" in _everything(after_lock) and "≈ 16 min" in _everything(after_lock)
    # the submitted scenario is shown read-only from the navigation; there is nothing to edit and nothing to submit again
    next(item for item in after_lock.button if item.label == "✓ FR-B").click().run()
    readonly = _everything(after_lock).replace("**", "")
    assert "This scenario is submitted. It is shown read-only." in readonly and "Overall: ACCEPT_WITH_LIMITATION" in readonly
    assert not any(radio.label[0] == "Q" for radio in after_lock.radio) and _button(after_lock, "Submit") is None and _button(after_lock, "LOCK") is None
    # exactly one record, linked by itself; no identifier was ever shown to the reviewer
    records = [json.loads(path.read_text()) for path in _records(world) if json.loads(path.read_text())["scenario_id"] == "FR-B"
               and path.name.startswith(ftr.reviewer_ref(_user_id(world, credentials)))]
    assert len(records) == 1 and records[0]["linkage"]["bundle_id"] == link["bundle_id"] and records[0]["post_reveal"]["overall"] == "ACCEPT_WITH_LIMITATION"
    for hidden in (link["bundle_id"], link["evidence"]["artifact_id"], link["evidence"]["artifact_digest"], link["faculty_review_configuration"]["grant_id"], link["authority_view"]["snapshot_id"], records[0]["reviewer_ref"]):
        assert hidden not in text and hidden not in readonly
    assert any(link["bundle_id"] in path.name for path in (world["store"] / "faculty_review" / "bundles").glob("*.json")), "the package is kept in the reviewer's store without the reviewer doing anything"


def _user_id(world, credentials):
    """The account id the page hashes into the reviewer reference (read straight from the account database: the test is not the page)."""
    import sqlite3
    row = sqlite3.connect(world["secrets"]["MRS_DATABASE_URL"].replace("sqlite:///", "")).execute("select id from mrs_users where username = ?", (credentials[0],)).fetchone()
    return row[0]


def test_u3_all_required_scenarios_in_order_then_the_summary_the_optional_scenarios_and_the_reviewer_action_count(world):
    credentials = page._faculty(world)
    at = _open(world, credentials)
    ACTIONS.clear()
    per_scenario, judgments = {}, {"FR-B": "ACCEPT", "FR-A": "ACCEPT_WITH_LIMITATION", "FR-E": "RECALIBRATE", "FR-G": "ACCEPT", "FR-F": "REJECT"}
    for identifier, overall in judgments.items():
        before = dict(ACTIONS)
        text = _everything(at)
        if ITEMS[identifier]["bundle"]["authority_view"]["halted"]:
            note = tui.STOP_NOTES[ITEMS[identifier]["bundle"]["authority_view"]["stop_class"]]
            scanned = re.sub(r"What to judge here:[^\n]*", "", text)           # the scenario's own purpose line may NAME the wording it asks faculty to check ("free of ... terminal wording")
            assert note in text and "Not executed: the experiment stopped here" in text and "Q5H · STOPPING POINT" in text and not any(word in scanned.lower() for word in DEATH_WORDS)
            assert at.subheader[0].value == ITEMS[identifier]["title"]
        else:
            assert "Q5H" not in text and "the experiment stopped" not in text
        assert ".md" not in text and "markdown" not in text.lower()
        _review(at, identifier, overall)
        per_scenario[identifier] = {key: ACTIONS.get(key, 0) - before.get(key, 0) for key in ("answers", "clicks")}
    # five required scenarios, all submitted: the summary appears by itself
    text = _everything(at)
    assert "REVIEW COMPLETE · 5/5 required scenarios reviewed" in text
    metrics = {item.label: item.value for item in at.metric}
    assert metrics == {"Accept": "2", "Accept with limitation": "1", "Recalibrate": "1", "Reject": "1"}
    assert "No comments were written." in text and "Review optional scenario FR-D" in text and "Review optional scenario FR-C" in text
    assert "The technical session summary was created automatically" in text and not at.exception
    reviewer = ftr.reviewer_ref(_user_id(world, credentials))
    summary_file = world["store"] / "faculty_review" / "trajectory" / f"session_summary_{reviewer}.json"
    summary = json.loads(summary_file.read_text())
    assert summary["complete"] and summary["judgments"]["REJECT"] == 1 and summary["technical_problems"] == [] and summary["scenarios_reviewed"] == list(judgments)
    # one optional scenario on top: it joins the counts and the reviewer returns to the summary
    next(item for item in at.button if item.label.startswith("Review optional scenario FR-D")).click().run()
    assert at.subheader[0].value == ITEMS["FR-D"]["title"] and "Optional scenario 1 of 2" in _everything(at)
    _review(at, "FR-D", "ACCEPT")
    assert "REVIEW COMPLETE · 5/5 required scenarios reviewed" in _everything(at) and {item.label: item.value for item in at.metric}["Accept"] == "3"
    # the reviewer's work, counted: blind answers + the two post-reveal answers, ONE reveal click and ONE submit click per scenario, no file, no menu path
    for identifier, counts in per_scenario.items():
        halted = ITEMS[identifier]["bundle"]["authority_view"]["halted"]
        assert counts == {"answers": 8 if halted else 7, "clicks": 2}, (identifier, counts)
    assert sum(counts["answers"] for counts in per_scenario.values()) == 7 * 3 + 8 * 2 and sum(counts["clicks"] for counts in per_scenario.values()) == 10
    own = [path for path in _records(world) if path.name.startswith(reviewer)]
    assert len(own) == 6 and ftr.summarize(world["store"] / "faculty_review", reviewer, ITEMS, ftr.sequence(ITEMS), ftr.load_set(bundles=bundles, scenario_of=fr.scenario)["digest"], bundles=bundles)["technical_problems"] == []


# -- attacks and integrity -------------------------------------------------------------------------------------------------------------------------------------------------
def test_u4_a_scenario_cannot_be_entered_out_of_turn_and_a_failed_submit_does_not_move_on(world, monkeypatch):
    credentials = page._faculty(world)
    at = _open(world, credentials)
    at.session_state[tui.VIEW_KEY] = "FR-F"                                       # the reviewer (or a script) tries to jump ahead before the lock
    at.run()
    assert at.subheader[0].value == ITEMS["FR-B"]["title"], "a scenario that is not the reviewer's turn is never shown"
    _answer_blind(at, "FR-B")
    _lock(at)
    _radio(at, "Did seeing the legacy comparator").set_value(ftr.CHANGED["choices"][0])
    _radio(at, "Overall judgment").set_value("ACCEPT")
    at.run()
    original = ftr.ReviewLog.submit
    monkeypatch.setattr(ftr.ReviewLog, "submit", lambda self: {"ok": False, "why": "the disk is full", "state": self.state()})
    _button(at, "Submit").click().run()
    assert at.subheader[0].value == ITEMS["FR-B"]["title"] and any("could not be saved, so nothing moved on" in item.value for item in at.error)
    assert not [path for path in _records(world) if path.name.startswith(ftr.reviewer_ref(_user_id(world, credentials)))]
    monkeypatch.setattr(ftr.ReviewLog, "submit", original)
    _button(at, "Submit").click().run()
    assert at.subheader[0].value == ITEMS["FR-A"]["title"]


def test_u5_a_resident_account_in_the_review_process_gets_no_trajectory_review(world):
    at = _open(world, page.RESIDENT)
    text = _everything(at)
    assert page.ui.GENERIC_REFUSAL in text
    for word in ("Trajectory", "FR-B", "legacy", "comparator", "Q1"):
        assert word not in text, word
    assert not at.radio and not at.metric and not _charts(at)
    reviewer = ftr.reviewer_ref(_user_id(world, page.RESIDENT))
    assert not [path for path in (world["store"] / "faculty_review").rglob("*") if reviewer in path.name], "nothing is created for a resident"


def test_u6_the_live_review_mode_is_unchanged_and_one_choice_away(world):
    at = page._open(world)                                                       # the helper's default: the live launcher
    assert [item.label for item in at.selectbox if item.label == "Review encounter"] and any(item.label == "Begin review encounter" for item in at.button)
    assert len(next(item for item in at.selectbox if item.label == "Review encounter").options) == 7
    next(item for item in at.radio if item.label == "Review mode").set_value(page.ui.TRAJECTORY_MODE).run()
    assert at.header[0].value == "Faculty Trajectory Review" and not any(item.label == "Review encounter" for item in at.selectbox)


def test_u7_an_ordinary_deployment_without_the_review_flag_has_no_trajectory_review(world, monkeypatch):
    monkeypatch.delenv(fr.FLAG)
    at = page._open(world, mode="trajectory")
    text = _everything(at)
    assert not any(item.label == "Review mode" for item in at.radio) and "Trajectory Review" not in text and "FR-B" not in text and not _charts(at)


def test_u8_a_tampered_review_set_makes_the_page_refuse_and_a_single_bad_scenario_is_not_offered(world, monkeypatch, tmp_path):
    def sign(record):
        rest = {key: value for key, value in record.items() if key != "record_digest"}
        return {**rest, "record_digest": ftr._digest(rest)}
    raw = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    unsigned = json.loads(json.dumps(raw))
    unsigned["items"][0]["title"] = "changed after signing"
    (tmp_path / "unsigned.json").write_text(json.dumps(unsigned))
    monkeypatch.setattr(ftr, "SET_PATH", tmp_path / "unsigned.json")
    at = _open(world)
    assert any("cannot be verified" in item.value for item in at.error) and not any(radio.label.startswith("Q1 ·") for radio in at.radio) and not _charts(at)
    one_bad = json.loads(json.dumps(raw))
    item = next(entry for entry in one_bad["items"] if entry["scenario_id"] == "FR-B")
    item["bundle"]["authority_view"]["authoritative_pressure_timeline"][0]["sbp"] += 25
    body = {key: value for key, value in item["bundle"].items() if key != "bundle_id"}
    import runtime_authority as ra
    item["bundle"]["bundle_id"] = ra.digest_of(json.loads(json.dumps(body, default=str)))[:16]
    (tmp_path / "one_bad.json").write_text(json.dumps(sign(one_bad)))
    monkeypatch.setattr(ftr, "SET_PATH", tmp_path / "one_bad.json")
    at = _open(world)
    assert any("cannot be verified" in item.value for item in at.error), "a re-signed set is refused by the pin in code, whatever it contains"
    monkeypatch.setattr(ftr, "PINNED_SET_DIGEST", None)                              # lift the pin to exercise the item-level checks on the page
    at = _open(world)
    assert not at.exception and at.subheader[0].value == ITEMS["FR-A"]["title"] and any("Not offered: FR-B (its stored trajectory could not be verified)" in item.value for item in at.caption)
    assert "FR-B" not in [button.label.replace("✓ ", "") for button in at.button if button.label.startswith("FR-")]
    assert not any(word in _everything(at).lower() for word in ("bundle", "digest", "certified series"))


def test_u9_a_corrupt_saved_log_stops_that_scenario_and_nothing_is_overwritten(world):
    credentials = page._faculty(world)
    at = _open(world, credentials)
    _answer_blind(at, "FR-B")
    reviewer = ftr.reviewer_ref(_user_id(world, credentials))
    log_path = next((world["store"] / "faculty_review" / "trajectory" / reviewer).glob("FR-B__*.jsonl"))
    damaged = log_path.read_text().replace("Expected", "Wrong", 1)
    log_path.write_text(damaged)
    again = _open(world, credentials)
    assert any("cannot be read, so nothing more is recorded" in item.value for item in again.error) and not any(radio.label.startswith("Q1 ·") for radio in again.radio)
    assert log_path.read_text() == damaged, "an unreadable log is never repaired or overwritten by the page"


# -- findings of the independent adversarial review (UX-012), each reproduced before it was fixed ----------------------------------------------------------------------------
DIGEST = ftr.load_set(bundles=bundles, scenario_of=fr.scenario)["digest"]


def _model_log(world, credentials, scenario_id):
    return ftr.ReviewLog(world["store"] / "faculty_review", ftr.reviewer_ref(_user_id(world, credentials)), ITEMS[scenario_id], set_digest=DIGEST, bundles=bundles, account={"role": "faculty"})


def _finish(log, overall="ACCEPT"):
    for question in ftr.required_questions(log.item)[1]:
        assert log.answer(question, ftr.choices_of(question)[0])["ok"]
    assert log.lock()["ok"] and log.answer("R1", ftr.CHANGED["choices"][0])["ok"] and log.set_overall(overall)["ok"] and log.submit()["ok"]


def test_u10_two_tabs_a_stale_widget_never_overwrites_a_newer_saved_answer(world):
    """F4: tab A restored Q1=Expected, tab B changed it to Wrong, tab A then touched only Q2 and the sync wrote the stale Q1 back."""
    credentials = page._faculty(world)
    first = _open(world, credentials)
    _radio(first, "Q1 ·").set_value("Expected")
    first.run()
    second = _open(world, credentials)                                           # restored: Q1 = Expected
    assert _radio(second, "Q1 ·").value == "Expected"
    _radio(second, "Q1 ·").set_value("Wrong")
    second.run()
    _radio(first, "Q2 ·").set_value("Plausible")                                 # tab A touches ONLY Q2
    first.run()
    state = _model_log(world, credentials, "FR-B").state()
    assert state["blind"] == {"Q1": "Wrong", "Q2": "Plausible"}, state["blind"]


def test_u11_an_edit_made_in_the_same_run_as_a_navigation_click_is_saved(world):
    """F5: the navigation rerun happened before the widgets were synchronised, so a radio and a comment changed in the same run as a click on a submitted scenario were lost."""
    credentials = page._faculty(world)
    _finish(_model_log(world, credentials, "FR-B"))
    at = _open(world, credentials)
    assert at.subheader[0].value == ITEMS["FR-A"]["title"]
    _radio(at, "Q1 ·").set_value("Partly")
    next(area for area in at.text_area if area.label.startswith("Optional comment on the trajectory")).set_value("kept")
    next(button for button in at.button if button.label == "✓ FR-B").click().run()
    state = _model_log(world, credentials, "FR-A").state()
    assert state["blind"].get("Q1") == "Partly" and state["blind_comment"] == "kept", state


def test_u12_each_optional_scenario_opens_by_itself_from_the_summary(world):
    """F6: 'Review optional scenario FR-C' opened FR-D, because only the first pending scenario was allowed."""
    credentials = page._faculty(world)
    for identifier in ("FR-B", "FR-A", "FR-E", "FR-G", "FR-F"):
        _finish(_model_log(world, credentials, identifier))
    at = _open(world, credentials)
    assert "REVIEW COMPLETE · 5/5 required scenarios reviewed" in _everything(at)
    next(button for button in at.button if button.label.startswith("Review optional scenario FR-C")).click().run()
    assert at.subheader[0].value == ITEMS["FR-C"]["title"] and "Optional scenario 2 of 2" in _everything(at)
    _finish(_model_log(world, credentials, "FR-C"))
    again = _open(world, credentials)
    assert "The counts include 1 optional scenario(s)" in _everything(again) and {item.label: item.value for item in again.metric}["Accept"] == "6"


def test_u13_a_disk_error_while_saving_shows_no_traceback_no_path_and_nothing_half_saved(world, monkeypatch):
    """F8: an OSError in the log surfaced a raw traceback with the store path, the reviewer reference and the file name."""
    credentials = page._faculty(world)
    at = _open(world, credentials)
    monkeypatch.setattr(ftr.ReviewLog, "answer", lambda self, question, value: (_ for _ in ()).throw(OSError("No space left on device: /secret/store/faculty_review/trajectory/abc/FR-B.jsonl")))
    _radio(at, "Q1 ·").set_value("Expected")
    at.run()
    assert not at.exception, [str(item.value)[:200] for item in at.exception]
    text = _everything(at) + "\n".join(item.value for item in at.error)
    assert "Not saved:" in text and "/secret" not in text and ".jsonl" not in text and "No space left" not in text
    monkeypatch.undo()
    assert _model_log(world, credentials, "FR-B").state()["blind"] == {}


def test_u14_the_purpose_line_asks_only_what_this_page_shows_and_a_refused_comment_is_said_to_be_unsaved(world):
    """Nits of the review: FR-E's certified purpose also asked about a consciousness comparison this page never shows; a comment refused by the identifier tripwire was lost in silence."""
    assert "consciousness" not in ftr.blind_view(ITEMS["FR-E"])["purpose"].lower() and "recovery" in ftr.blind_view(ITEMS["FR-E"])["purpose"].lower()
    credentials = page._faculty(world)
    at = _open(world, credentials)
    area = next(item for item in at.text_area if item.label.startswith("Optional comment on the trajectory"))
    area.set_value("seen at 120 130 140 min")
    at.run()
    assert any("This comment is not saved yet" in item.value for item in at.warning) and area.value == "seen at 120 130 140 min"
    assert _model_log(world, credentials, "FR-B").state()["blind_comment"] == ""
    next(item for item in at.text_area if item.label.startswith("Optional comment on the trajectory")).set_value("MAP about 65 to 75 mmHg")
    at.run()
    assert not any("This comment is not saved yet" in item.value for item in at.warning) and _model_log(world, credentials, "FR-B").state()["blind_comment"] == "MAP about 65 to 75 mmHg"
