"""UX-002 to UX-010 and UX-012 (model level): the FACULTY TRAJECTORY REVIEW data model and the reviewer's durable state.

What it proves (the page-level flow is ``test_phase3_trajectory_review_page.py``):

* the stored review set verifies as a whole and scenario by scenario (digest, bundle id, evidence, certified series, comparator minutes); a changed set, a re-labelled or re-signed trajectory, or a failed
  replay is NEVER offered;
* the blind view carries no comparator; the comparator exists only for a LOCKED state (there is no other way to obtain it from the module);
* answers are saved as they are given and survive a refresh; a locked first pass cannot be changed (the writer refuses; the reader ignores a forged later event); the locked answers come from the log;
* a tampered, truncated or reordered log is unreadable and nothing more is written to it; an unacknowledged torn tail is ignored;
* a submit creates ONE record however many times and from however many threads it is asked, a crash between the record and the closing event is recovered without a second record;
* the record links reviewer (opaque), scenario, bundle, artifact, grant, snapshot, comparator, blind answers, the reveal and the post-reveal answers by itself, and carries no account name;
* a different bundle is a different log and inherits no answer; the summary counts exactly and detects a foreign or altered record;
* the review modules import nothing of the engine, the authority, the shadow, the grant or the common core, and never label the legacy comparator as truth.
"""
import ast
import copy
import json
import re
import threading
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import faculty_trajectory_review_ui as ui
import runtime_authority as ra
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr

ROOT = Path(__file__).resolve().parent
LOADED = ftr.load_set(bundles=bundles, scenario_of=fr.scenario)
ITEMS, DIGEST = LOADED["items"], LOADED["digest"]
REVIEWER = "0123456789ab"


def _log(tmp_path, item=None, reviewer=REVIEWER, scenario="FR-B"):
    return ftr.ReviewLog(tmp_path / "faculty_review", reviewer, item or ITEMS[scenario], set_digest=DIGEST, bundles=bundles, account={"role": "faculty"})


def _first_pass(log, choice=0):
    _, required = ftr.required_questions(log.item)
    for question in required:
        assert log.answer(question, ftr.choices_of(question)[choice])["ok"]


def _to_submitted(log, overall="ACCEPT", changed=0, comment=""):
    _first_pass(log)
    assert log.lock()["ok"]
    assert log.answer("R1", ftr.CHANGED["choices"][changed])["ok"] and log.set_overall(overall)["ok"]
    if comment:
        assert log.comment(comment, after_reveal=True)["ok"]
    result = log.submit()
    assert result["ok"], result
    return result


def _forge(log, kind, data):
    """Append a CORRECTLY CHAINED event the way an attacker with write access would, to prove the reader (not only the writer) refuses to be steered by it."""
    lines = [line for line in log.path.read_text().split("\n") if line]
    previous = json.loads(lines[-1])["hash"] if lines else "0" * 64
    event = {"seq": len(lines) + 1, "prev": previous, "kind": kind, "at": "2099-01-01T00:00:00+00:00", "data": data}
    with open(log.path, "a") as handle:
        handle.write(json.dumps({**event, "hash": ftr._digest(event)}, sort_keys=True, separators=(",", ":")) + "\n")


def _signed(record):
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    return {**rest, "record_digest": ftr._digest(rest)}


def _set_file(tmp_path, mutate):
    record = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(_signed(record)), encoding="utf-8")
    return path


def _resign_bundle(item):
    body = {key: value for key, value in item["bundle"].items() if key != "bundle_id"}
    item["bundle"]["bundle_id"] = ra.digest_of(json.loads(json.dumps(body, default=str)))[:16]


# -- the stored set -----------------------------------------------------------------------------------------------------------------------------------------------------
def test_m1_the_stored_set_verifies_as_a_whole_and_offers_every_scripted_scenario():
    assert LOADED["ok"] and LOADED["problems"] == [], LOADED["problems"]
    assert sorted(ITEMS) == sorted(item["id"] for item in fr.SCENARIOS) and len(ITEMS) == 7
    order = ftr.sequence(ITEMS)
    assert [entry["scenario_id"] for entry in order] == [name for name, _ in ftr.SEQUENCE] and [entry["required"] for entry in order] == [True] * 5 + [False] * 2
    series = json.loads(ftr.SERIES_PATH.read_text(encoding="utf-8"))["runs"]
    for identifier, item in ITEMS.items():
        assert ftr.item_problems(item, bundles=bundles, scenario_of=fr.scenario, series_runs=series) == [], identifier
        assert not bundles.bundle_problems(item["bundle"]) and not bundles.evidence_problems(item["bundle"]), identifier
        assert item["bundle"]["encounter"]["scenario_id"] == identifier and item["bundle"]["encounter"]["case_id"] == item["case_id"]


def test_m2_a_changed_set_or_a_scenario_that_does_not_match_the_certified_series_is_never_offered(tmp_path):
    def edited(path):
        return ftr.load_set(path, bundles=bundles, scenario_of=fr.scenario, expected_digest=None)       # the pin is tested in m21; here the item-level checks are
    assert edited(ftr.SET_PATH)["ok"]
    assert ftr.load_set(ftr.SET_PATH, bundles=bundles, scenario_of=fr.scenario)["ok"], "the stored set is the pinned one"
    # the set no longer matches its own digest
    raw = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    raw["items"][0]["title"] = "changed"
    (tmp_path / "unsigned.json").write_text(json.dumps(raw), encoding="utf-8")
    result = edited(tmp_path / "unsigned.json")
    assert not result["ok"] and result["items"] == {} and "digest" in result["problems"][0]
    # a trajectory edited, its bundle id recomputed and the whole set re-signed: only the certified series can catch it, and it does
    def move_pressure(record):
        item = next(item for item in record["items"] if item["scenario_id"] == "FR-B")
        item["bundle"]["authority_view"]["authoritative_pressure_timeline"][0]["sbp"] += 20
        _resign_bundle(item)
    result = edited(_set_file(tmp_path, move_pressure))
    assert "FR-B" not in result["items"] and len(result["items"]) == 6 and any("certified series" in problem for problem in result["problems"])
    # a bundle presented as another scenario
    def relabel(record):
        item = next(item for item in record["items"] if item["scenario_id"] == "FR-B")
        item["bundle"]["encounter"]["scenario_id"] = "FR-E"
        _resign_bundle(item)
    result = edited(_set_file(tmp_path, relabel))
    assert "FR-B" not in result["items"] and any("another scenario" in problem for problem in result["problems"])
    # a comparator that is not on the minutes of the trajectory
    def shift_comparator(record):
        item = next(item for item in record["items"] if item["scenario_id"] == "FR-G")
        item["bundle"]["comparator"]["legacy_counterfactual_pressure_timeline"][0]["minute"] += 1
        _resign_bundle(item)
    assert "FR-G" not in edited(_set_file(tmp_path, shift_comparator))["items"]
    # evidence that fails its own replay
    def fail_replay(record):
        item = next(item for item in record["items"] if item["scenario_id"] == "FR-A")
        item["bundle"]["evidence"]["replay"]["reproduces"] = False
        _resign_bundle(item)
    assert "FR-A" not in edited(_set_file(tmp_path, fail_replay))["items"]
    # a file that is not there, or not JSON, offers nothing and does not raise
    assert not ftr.load_set(tmp_path / "missing.json", bundles=bundles, scenario_of=fr.scenario)["ok"]
    (tmp_path / "junk.json").write_text("not json")
    assert not ftr.load_set(tmp_path / "junk.json", bundles=bundles, scenario_of=fr.scenario)["ok"]


# -- blind and comparator --------------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("identifier", sorted(ITEMS))
def test_m3_the_blind_view_carries_no_comparator_and_no_audit_identifier(identifier):
    item = ITEMS[identifier]
    text = json.dumps(ftr.blind_view(item), default=str)
    for forbidden in ("legacy", "comparator", "difference", "counterfactual", "bundle", "artifact", "digest", "grant", "snapshot", "lineage", item["bundle"]["bundle_id"],
                      item["bundle"]["evidence"]["artifact_digest"], "Guided reasoning completion"):
        assert forbidden.lower() not in text.lower(), (identifier, forbidden)
    figure = ui.pressure_chart(ftr.blind_view(item)["common"], None, ui.interventions(ftr.blind_view(item)["timeline"]), None).to_json()
    assert "legacy" not in figure.lower() and "Legacy" not in figure


def test_m4_the_comparator_is_available_only_for_a_locked_state(tmp_path):
    item = ITEMS["FR-B"]
    for unlocked in (None, {}, {"locked": False}, {"locked": 0, "blind": {"Q1": "Expected"}}, _log(tmp_path).state()):
        with pytest.raises(ftr.Locked):
            ftr.comparator_view(item, unlocked)
    log = _log(tmp_path)
    _first_pass(log)
    assert log.lock()["ok"]
    comparison = ftr.comparator_view(item, log.state())
    assert comparison["label"] == "Legacy comparator — nonauthoritative comparison" and comparison["legacy"][0]["minute"] == 0
    assert [row["minute"] for row in comparison["legacy"][1:]] == [row["minute"] for row in ftr.blind_view(item)["common"][1:]]
    assert all(set(row) == {"minute", "sbp", "dbp", "map"} for row in comparison["differences"])


# -- answers, lock, refresh ------------------------------------------------------------------------------------------------------------------------------------------
def test_m5_answers_are_saved_as_given_survive_a_refresh_and_wrong_answers_are_refused(tmp_path):
    log = _log(tmp_path)
    assert log.state()["status"] == "NEW" and log.answer("Q1", "Expected")["ok"] and log.answer("Q2", "Too late")["ok"]
    assert log.comment("a short note")["ok"]
    refreshed = _log(tmp_path).state()                                      # a new object over the same file: what a refresh does
    assert refreshed["status"] == "IN_PROGRESS" and refreshed["blind"] == {"Q1": "Expected", "Q2": "Too late"} and refreshed["blind_comment"] == "a short note" and not refreshed["locked"]
    assert log.answer("Q1", "Partly")["ok"] and _log(tmp_path).state()["blind"]["Q1"] == "Partly"          # changing an answer BEFORE the lock is allowed
    for question, value in (("Q1", "Maybe"), ("Q9", "Expected"), ("Q5H", "Understandable"), ("Q1", "")):            # outside the choices / a halt question on a scenario that did not stop
        assert not log.answer(question, value)["ok"], (question, value)
    assert not log.answer("R1", ftr.CHANGED["choices"][0])["ok"] and not log.set_overall("ACCEPT")["ok"] and not log.comment("late", after_reveal=True)["ok"]      # nothing post-reveal before the lock
    assert not log.lock()["ok"] and "Q3" in log.lock()["why"]


def test_m6_a_locked_first_pass_is_final_it_comes_from_the_log_and_a_forged_later_event_is_ignored(tmp_path):
    log = _log(tmp_path)
    _first_pass(log)
    locked = log.lock()
    assert locked["ok"] and locked["state"]["locked_answers"] == locked["state"]["blind"] and locked["state"]["locked_at"]
    before = dict(locked["state"]["locked_answers"])
    assert not log.answer("Q1", "Wrong")["ok"] and not log.comment("changed my mind")["ok"] and not log.lock()["ok"]
    assert log.state()["locked_answers"] == before
    _forge(log, "blind", {"id": "Q1", "value": "Wrong"})                         # an attacker's valid-looking event after the lock
    _forge(log, "lock", {"answers": {"Q1": "Wrong"}, "comment": "forged"})
    forged = log.state()
    assert forged["status"] == "LOCKED" and forged["locked_answers"] == before and forged["blind"]["Q1"] == before["Q1"] and forged["locked_comment"] == ""


def test_m7_a_tampered_truncated_or_reordered_log_is_unreadable_and_nothing_more_is_written(tmp_path):
    log = _log(tmp_path)
    _first_pass(log)
    original = log.path.read_text()
    lines = original.split("\n")
    log.path.write_text(original.replace("Expected", "Wrong", 1))                 # an answer edited in place
    state = log.state()
    assert state["status"] == "UNREADABLE" and not log.answer("Q1", "Partly")["ok"] and log.path.read_text() == original.replace("Expected", "Wrong", 1)
    log.path.write_text("\n".join(lines[1:]))                                    # the first event deleted
    assert log.state()["status"] == "UNREADABLE"
    log.path.write_text("\n".join([lines[1], lines[0]] + lines[2:]))               # two events swapped
    assert log.state()["status"] == "UNREADABLE"
    log.path.write_text(original)
    assert log.state()["status"] == "IN_PROGRESS"
    with open(log.path, "a") as handle:                                          # a torn tail: written, never acknowledged (no newline)
        handle.write('{"seq": 99, "kind": "blind", "da')
    assert log.state()["status"] == "IN_PROGRESS" and log.state()["blind"]["Q1"] == "Expected"
    assert log.answer("Q1", "Partly")["ok"] and log.state()["blind"]["Q1"] == "Partly" and b"seq\": 99" not in log.path.read_bytes()      # the torn tail was dropped before appending


# -- submit ----------------------------------------------------------------------------------------------------------------------------------------------------------
def test_m8_a_submit_creates_one_record_however_often_and_from_however_many_threads_it_is_asked(tmp_path):
    log = _log(tmp_path)
    _first_pass(log)
    assert log.lock()["ok"]
    assert not log.submit()["ok"]                                                # not before the post-reveal answers
    assert log.answer("R1", ftr.CHANGED["choices"][1])["ok"] and log.set_overall("RECALIBRATE")["ok"]
    outcomes, barrier = [], threading.Barrier(8)

    def go():
        barrier.wait()
        outcomes.append(_log(tmp_path).submit())
    threads = [threading.Thread(target=go) for _ in range(8)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    assert sum(1 for outcome in outcomes if outcome["ok"]) == 1 and all(outcome.get("record_id") for outcome in outcomes if not outcome["ok"])
    records = list((tmp_path / "faculty_review" / "trajectory_reviews").glob("*.json"))
    events = [json.loads(line)["kind"] for line in log.path.read_text().split("\n") if line]
    assert len(records) == 1 and events.count("submitted") == 1 and events.count("lock") == 1
    state = log.state()
    assert state["status"] == "SUBMITTED" and not log.answer("Q1", "Wrong")["ok"] and not log.set_overall("ACCEPT")["ok"] and not log.submit()["ok"]
    assert len(list((tmp_path / "faculty_review" / "trajectory_reviews").glob("*.json"))) == 1


def test_m9_a_crash_between_the_record_and_the_closing_event_is_recovered_without_a_second_record(tmp_path):
    log = _log(tmp_path)
    _first_pass(log)
    assert log.lock()["ok"] and log.answer("R1", ftr.CHANGED["choices"][0])["ok"] and log.set_overall("ACCEPT")["ok"]
    record = log._record(log.state())
    assert log._write_record(record)["stored"]                                   # the record is on disk, the log was never closed
    assert log.state()["status"] == "LOCKED"
    retried = log.submit()
    assert retried["ok"] and retried["record_id"] == record["record_id"] and log.state()["status"] == "SUBMITTED"
    assert len(list((tmp_path / "faculty_review" / "trajectory_reviews").glob("*.json"))) == 1


def test_m10_the_record_links_everything_by_itself_and_names_no_account(tmp_path):
    item = ITEMS["FR-B"]
    result = _to_submitted(_log(tmp_path), overall="ACCEPT_WITH_LIMITATION", changed=2, comment="the rise is slightly early")
    record = json.loads(Path(result["path"]).read_text())
    link, bundle = record["linkage"], item["bundle"]
    assert link["bundle_id"] == bundle["bundle_id"] and link["artifact_id"] == bundle["evidence"]["artifact_id"] and link["artifact_digest"] == bundle["evidence"]["artifact_digest"]
    assert link["grant_id"] == bundle["faculty_review_configuration"]["grant_id"] and link["snapshot_id"] == bundle["authority_view"]["snapshot_id"] and link["review_set_digest"] == DIGEST
    assert link["legacy_comparator"] and record["scenario_id"] == "FR-B" and record["case_id"] == item["case_id"] and record["reviewer_ref"] == REVIEWER and record["reviewer_role"] == "faculty"
    assert record["first_pass"]["answers"] == record["first_pass"]["answers_at_lock"] and set(record["first_pass"]["answers"]) == {"Q1", "Q2", "Q3", "Q4", "Q5"}
    assert record["comparator_revealed_at"] == record["first_pass"]["locked_at"] and record["post_reveal"]["overall"] == "ACCEPT_WITH_LIMITATION"
    assert record["post_reveal"]["changed_judgment"] == ftr.CHANGED["choices"][2] and record["post_reveal"]["after_reveal_comment"] == "the rise is slightly early"
    assert record["record_id"] == ftr._digest({key: value for key, value in record.items() if key != "record_id"})[:16]
    assert "not a clinical validation" in record["statement"] and not any(word in json.dumps(record).lower() for word in ("username", "password", "email"))
    assert re.fullmatch(r"[0-9a-f]{12}", ftr.reviewer_ref(42)) and ftr.reviewer_ref(42) != ftr.reviewer_ref(43) and "42" != ftr.reviewer_ref(42)


def test_m11_a_different_bundle_is_a_different_log_and_inherits_no_answer(tmp_path):
    first = _log(tmp_path)
    _first_pass(first)
    other = copy.deepcopy(ITEMS["FR-B"])
    other["bundle"]["limitations"] = list(other["bundle"]["limitations"]) + ["a later revision"]
    _resign_bundle(other)
    assert other["bundle"]["bundle_id"] != ITEMS["FR-B"]["bundle"]["bundle_id"]
    second = ftr.ReviewLog(tmp_path / "faculty_review", REVIEWER, other, set_digest=DIGEST, bundles=bundles)
    assert second.path != first.path and second.state()["status"] == "NEW" and second.state()["blind"] == {}
    assert first.state()["status"] == "IN_PROGRESS"                              # the earlier package's answers are left exactly as they were
    scenario_other = _log(tmp_path, scenario="FR-E")                              # and another scenario never shares a log either
    assert scenario_other.path != first.path and scenario_other.state()["status"] == "NEW"


# -- progress and summary -----------------------------------------------------------------------------------------------------------------------------------------
def _all_logs(tmp_path):
    order = ftr.sequence(ITEMS)
    return order, {entry["scenario_id"]: _log(tmp_path, scenario=entry["scenario_id"]) for entry in order}


def test_m12_progress_follows_the_sequence_and_the_summary_counts_exactly(tmp_path):
    order, logs = _all_logs(tmp_path)
    prog = ftr.progress(logs, order)
    assert prog["current"] == "FR-B" and prog["remaining_required"] == 5 and prog["estimated_minutes_left"] == 5 * ftr.MINUTES_PER_SCENARIO and not prog["required_done"]
    judgments = {"FR-B": "ACCEPT", "FR-A": "ACCEPT_WITH_LIMITATION", "FR-E": "RECALIBRATE", "FR-G": "ACCEPT", "FR-F": "REJECT"}
    for identifier, overall in judgments.items():
        _to_submitted(logs[identifier], overall=overall, comment=f"note on {identifier}" if overall != "ACCEPT" else "")
        prog = ftr.progress(logs, order)
        assert identifier in prog["submitted"]
    assert prog["required_done"] and not prog["all_done"] and prog["current"] == "FR-D" and prog["remaining_required"] == 0 and prog["estimated_minutes_left"] == 0
    summary = ftr.summarize(tmp_path / "faculty_review", REVIEWER, ITEMS, order, DIGEST)
    assert summary["judgments"] == {"ACCEPT": 2, "ACCEPT_WITH_LIMITATION": 1, "RECALIBRATE": 1, "REJECT": 1} and summary["complete"] and summary["required_reviewed"] == 5
    assert summary["technical_problems"] == [] and summary["scenarios_reviewed"] == ["FR-B", "FR-A", "FR-E", "FR-G", "FR-F"]
    assert sorted(comment["scenario_id"] for comment in summary["comments"]) == ["FR-A", "FR-E", "FR-F"] and all(comment["stage"] == "after reveal" for comment in summary["comments"])
    assert "not interpreted" in summary["statement"] or "not interpreted" in summary["statement"].replace("has not", "not")
    _to_submitted(logs["FR-D"], overall="ACCEPT")                                # an optional scenario adds to the counts and nothing else
    after = ftr.summarize(tmp_path / "faculty_review", REVIEWER, ITEMS, order, DIGEST)
    assert after["judgments"]["ACCEPT"] == 3 and after["required_reviewed"] == 5 and len(after["scenarios_reviewed"]) == 6 and ftr.progress(logs, order)["current"] == "FR-C"
    written = ftr.write_summary(tmp_path / "faculty_review", after)
    assert written["written"] and json.loads(Path(written["path"]).read_text())["summary_digest"] == after["summary_digest"]


def test_m13_the_summary_detects_an_altered_or_foreign_record(tmp_path):
    order, logs = _all_logs(tmp_path)
    result = _to_submitted(logs["FR-B"], overall="ACCEPT")
    path = Path(result["path"])
    good = json.loads(path.read_text())
    root = tmp_path / "faculty_review"
    assert ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)["technical_problems"] == []
    altered = copy.deepcopy(good)
    altered["post_reveal"]["overall"] = "REJECT"                                 # edited after the fact: its identity no longer recomputes
    path.write_text(json.dumps(altered))
    assert any("identity" in problem for problem in ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)["technical_problems"])
    foreign = copy.deepcopy(good)
    foreign["linkage"]["review_set_digest"] = "0" * 64
    foreign["record_id"] = ftr._digest({key: value for key, value in foreign.items() if key != "record_id"})[:16]
    path.write_text(json.dumps(foreign))
    problems = ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)["technical_problems"]
    assert any("another package or review set" in problem for problem in problems) and any("event log" in problem for problem in problems)
    path.write_text(json.dumps(good))
    assert ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)["technical_problems"] == []
    assert ftr.summarize(root, "ffffffffffff", ITEMS, order, DIGEST)["scenarios_reviewed"] == []            # another reviewer's records are not this reviewer's


def test_m14_comments_are_checked_for_identifiers_and_length(tmp_path):
    log = _log(tmp_path)
    for text in ("contact me at someone@example.org", "MRN: 12345678", "admitted on 05/03/2024", "x" * (ftr.MAX_COMMENT + 1)):
        assert not log.comment(text)["ok"], text
    assert log.comment("The recovery looks slightly early for the volume given.")["ok"]
    assert ftr.comment_problem("plain clinical remark", bundles=None) is None


# -- isolation and wording -----------------------------------------------------------------------------------------------------------------------------------------
def test_m15_the_review_modules_import_nothing_of_the_engine_the_authority_the_shadow_or_the_core():
    forbidden = ("runtime_authority", "runtime_shadow", "runtime_pressure_grant", "clinical_core", "family_engine", "clinical_physiology", "app", "runtime_faculty", "faculty_review_ui")
    for name in ("faculty_trajectory_review.py", "faculty_trajectory_review_ui.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {str(node.module).split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not imported & set(forbidden), (name, imported & set(forbidden))
    # the launcher module imports NOTHING of the review page (it is handed in by app.py, as the review layer is), so the P3-300 record of its imports stays true
    launcher_tree = ast.parse((ROOT / "faculty_review_ui.py").read_text(encoding="utf-8"))
    launcher_imports = {alias.name for node in ast.walk(launcher_tree) if isinstance(node, ast.Import) for alias in node.names} | {str(node.module) for node in ast.walk(launcher_tree) if isinstance(node, ast.ImportFrom)}
    assert not any("trajectory" in name for name in launcher_imports), launcher_imports
    assert "trajectory_page=_faculty_trajectory_ui.draw" in (ROOT / "app.py").read_text(encoding="utf-8")


def test_m16_the_legacy_comparator_is_never_called_truth_correct_or_a_reference_standard():
    source = (ROOT / "faculty_trajectory_review.py").read_text() + (ROOT / "faculty_trajectory_review_ui.py").read_text()
    for phrase in ("ground truth", "gold standard", "correct answer", "the correct", "true value", "right answer"):
        assert phrase not in source.lower(), phrase
    assert ftr.COMPARATOR_LABEL == "Legacy comparator — nonauthoritative comparison" and "nonauthoritative" in ftr.COMPARATOR_LABEL.lower()
    assert "not a reference standard" in ftr.COMPARATOR_NOTE and "not an error" in ftr.COMPARATOR_NOTE
    for stop in ui.STOP_NOTES.values():
        assert "operational stop" in stop and "not an outcome of the patient" in stop and not any(word in stop.lower() for word in ("death", "died", "dead", "cardiac arrest", "terminal", "fatal", "moribund"))


# -- findings of the independent adversarial review (UX-012): each was reproduced with a probe BEFORE it was fixed -------------------------------------------------------------
def test_m17_the_record_and_the_log_cannot_disagree_because_submit_is_one_critical_section(tmp_path):
    """F1: a ``set_overall`` from another tab landing between the record and the closing event left the log saying REJECT and the record ACCEPT, and nothing flagged it."""
    for trial in range(25):
        root = tmp_path / f"t{trial}"
        log = _log(root)
        _first_pass(log)
        assert log.lock()["ok"] and log.answer("R1", ftr.CHANGED["choices"][0])["ok"] and log.set_overall("ACCEPT")["ok"]
        stop, flips = threading.Event(), []

        def flip():
            other = _log(root)
            while not stop.is_set():
                flips.append(other.set_overall("REJECT")["ok"] or other.set_overall("ACCEPT")["ok"])
        thread = threading.Thread(target=flip)
        thread.start()
        outcome = log.submit()
        stop.set()
        thread.join()
        state = log.state()
        assert state["status"] == "SUBMITTED", (trial, outcome)
        records = list((root / "faculty_review" / "trajectory_reviews").glob("*.json"))
        assert len(records) == 1
        record = json.loads(records[0].read_text())
        assert record["post_reveal"]["overall"] == state["overall"] and record["record_id"] == state["record_id"], (trial, record["post_reveal"], state["overall"])
        order = ftr.sequence(ITEMS)
        assert ftr.summarize(root / "faculty_review", REVIEWER, ITEMS, order, DIGEST)["technical_problems"] == [], trial


def test_m18_a_crash_between_the_record_and_the_closing_event_never_locks_the_reviewer_out(tmp_path):
    """F2: after the record was written and before the log was closed, ANY later change moved the log head, the retry built a different record and ``os.link`` refused it for ever."""
    log = _log(tmp_path)
    _first_pass(log)
    assert log.lock()["ok"] and log.answer("R1", ftr.CHANGED["choices"][0])["ok"] and log.set_overall("ACCEPT")["ok"]
    assert log._write_record(log._record(log.state()))["stored"]                   # the crash: the record is on disk, the log was never closed
    assert log.comment("a note after the reveal", after_reveal=True)["ok"] and log.set_overall("REJECT")["ok"]       # the reviewer still sees the form and changes it
    retried = log.submit()
    assert retried["ok"], retried
    state = log.state()
    assert state["status"] == "SUBMITTED" and state["overall"] == "REJECT"
    records = sorted((tmp_path / "faculty_review" / "trajectory_reviews").glob("*"))
    active = [path for path in records if "superseded" not in path.name]
    assert len(active) == 1 and json.loads(active[0].read_text())["post_reveal"]["overall"] == "REJECT" and json.loads(active[0].read_text())["record_id"] == state["record_id"]
    assert len(records) == 2, "the interrupted record is kept aside for audit, never deleted"


def test_m19_the_summary_counts_only_records_that_verify_and_flags_a_missing_one(tmp_path):
    """F3: an altered record was counted under a green REVIEW COMPLETE; a record of another scenario or reviewer was counted when the file name matched; a missing record went unflagged."""
    order, logs = _all_logs(tmp_path)
    paths = {}
    for identifier in ("FR-B", "FR-A", "FR-E", "FR-G", "FR-F"):
        paths[identifier] = Path(_to_submitted(logs[identifier], overall="ACCEPT")["path"])
    root = tmp_path / "faculty_review"
    assert ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)["complete"]
    altered = json.loads(paths["FR-B"].read_text())
    altered["post_reveal"]["overall"] = "REJECT"
    altered["record_id"] = ftr._digest({key: value for key, value in altered.items() if key != "record_id"})[:16]      # even RE-SIGNED, the log is the witness
    paths["FR-B"].write_text(json.dumps(altered))
    summary = ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)
    assert not summary["complete"] and "FR-B" not in summary["scenarios_reviewed"] and summary["judgments"]["REJECT"] == 0 and summary["judgments"]["ACCEPT"] == 4 and summary["technical_problems"]
    foreign = json.loads(paths["FR-A"].read_text())
    foreign["scenario_id"], foreign["reviewer_ref"] = "FR-E", "ffffffffffff"
    foreign["record_id"] = ftr._digest({key: value for key, value in foreign.items() if key != "record_id"})[:16]
    paths["FR-A"].write_text(json.dumps(foreign))
    paths["FR-B"].write_text(json.dumps(json.loads(paths["FR-B"].read_text()) | {"post_reveal": json.loads(paths["FR-E"].read_text())["post_reveal"]}))
    summary = ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)
    assert "FR-A" not in summary["scenarios_reviewed"] and not summary["complete"]
    paths["FR-G"].unlink()                                                          # a record that is simply gone while its log says SUBMITTED
    summary = ftr.summarize(root, REVIEWER, ITEMS, order, DIGEST)
    assert "FR-G" not in summary["scenarios_reviewed"] and any("FR-G" in problem and "missing" in problem for problem in summary["technical_problems"]) and not summary["complete"]


def test_m20_a_forged_lock_cannot_reveal_the_comparator_and_a_malformed_event_is_unreadable_never_a_crash(tmp_path):
    """F9: a chained forged ``lock`` carrying one fake answer produced LOCKED and the comparator; a chained event with no ``kind`` or a non-dict ``data`` raised out of ``_fold``."""
    log = _log(tmp_path)
    assert log.answer("Q1", "Expected")["ok"]
    _forge(log, "lock", {"answers": {"Q1": "Wrong"}, "comment": "x"})
    state = log.state()
    assert state["status"] != "LOCKED" and not state["locked"], "a lock with unanswered required questions is not a lock"
    with pytest.raises(ftr.Locked):
        ftr.comparator_view(log.item, state)
    for number, malformed in enumerate(("abc", [1], 5)):
        other = _log(tmp_path, reviewer=f"{number + 10:012x}")
        assert other.answer("Q1", "Expected")["ok"]
        _forge(other, "blind", malformed)
        assert other.state()["status"] == "UNREADABLE"
    nokind = _log(tmp_path, reviewer="bbbbbbbbbbbb")
    assert nokind.answer("Q1", "Expected")["ok"]
    lines = [line for line in nokind.path.read_text().split("\n") if line]
    event = {"seq": 2, "prev": json.loads(lines[-1])["hash"], "at": "x", "data": {}}
    with open(nokind.path, "a") as handle:
        handle.write(json.dumps({**event, "hash": ftr._digest(event)}, sort_keys=True, separators=(",", ":")) + "\n")
    assert nokind.state()["status"] == "UNREADABLE"
    honest = _log(tmp_path, reviewer="cccccccccccc")
    _first_pass(honest)
    assert honest.lock()["ok"] and honest.state()["locked_answers"] == honest.state()["blind"] and len(honest.state()["locked_answers"]) == 5


def test_m21_the_review_set_is_pinned_and_what_the_reviewer_sees_is_cross_checked(tmp_path):
    """F7: the digest was self-attested; a re-signed edit of arrival, title or script was offered; legacy values edited without the differences were offered; the log did not know the set revision."""
    assert ftr.PINNED_SET_DIGEST == LOADED["digest"], "the stored set is pinned in code: changing it is a deliberate, reviewed act"
    def offered(mutate, identifier):
        return identifier in ftr.load_set(_set_file(tmp_path, mutate), bundles=bundles, scenario_of=fr.scenario, expected_digest=None)["items"]
    def edit(field, value):
        def mutate(record):
            next(item for item in record["items"] if item["scenario_id"] == "FR-B")[field] = value
        return mutate
    assert offered(lambda record: None, "FR-B")
    assert not offered(edit("arrival", {"sbp": 60, "dbp": 54, "map": 56, "hr": 124, "rr": 26, "spo2": 97, "crt": 5}), "FR-B"), "the arrival must be the certified minute-0 pressure"
    assert not offered(edit("title", "CHANGED"), "FR-B") and not offered(edit("script", [["order", "Place an IV line."]]), "FR-B") and not offered(edit("reason", "x" * 80), "FR-B")
    def legacy_only(record):
        item = next(item for item in record["items"] if item["scenario_id"] == "FR-B")
        item["bundle"]["comparator"]["legacy_counterfactual_pressure_timeline"][0]["sbp"] += 30
        _resign_bundle(item)
    assert not offered(legacy_only, "FR-B"), "legacy values must match the certified counterfactual of the series and the stored differences"
    shifted = tmp_path / "other_digest.json"
    shifted.write_text(json.dumps(_signed({**json.loads(ftr.SET_PATH.read_text()), "statement": "a re-signed set"})))
    assert not ftr.load_set(shifted, bundles=bundles, scenario_of=fr.scenario)["ok"], "with the code pin in force a re-signed set is refused"
    item = copy.deepcopy(ITEMS["FR-B"])
    item["title"] = "a display-only revision of the same bundle"
    assert ftr.item_digest(item) != ftr.item_digest(ITEMS["FR-B"])
    first = _log(tmp_path)
    _first_pass(first)
    revised = ftr.ReviewLog(tmp_path / "faculty_review", REVIEWER, item, set_digest=DIGEST, bundles=bundles)
    assert revised.path != first.path and revised.state()["status"] == "NEW", "a revised item never inherits answers given on the previous revision"


def test_m22_a_disk_error_is_reported_without_a_path_and_nothing_is_half_saved(tmp_path, monkeypatch):
    """F8: an OSError in the log surfaced a raw traceback with the absolute store path, the reviewer reference and the file name."""
    log = _log(tmp_path)
    assert log.answer("Q1", "Expected")["ok"]
    real_open = ftr.os.open

    def failing(path, *args, **kwargs):
        if str(path).endswith(".jsonl"):
            raise OSError(28, "No space left on device", str(path))
        return real_open(path, *args, **kwargs)
    monkeypatch.setattr(ftr.os, "open", failing)
    outcome = log.answer("Q2", "Plausible")
    assert not outcome["ok"] and "/" not in outcome["why"] and REVIEWER not in outcome["why"] and ".jsonl" not in outcome["why"] and "could not be saved" in outcome["why"]
    state = log.state()                                                           # reading is a different call: the earlier answers are intact
    monkeypatch.undo()
    assert log.state()["blind"] == {"Q1": "Expected"} and state["status"] in ("IN_PROGRESS", "UNREADABLE")
    unreadable = _log(tmp_path, reviewer="dddddddddddd")
    unreadable.directory.mkdir(parents=True, exist_ok=True)
    unreadable.path.mkdir()                                                       # a directory where the log should be: an OSError on read, never an exception out of ``state``
    assert unreadable.state()["status"] == "UNREADABLE"
