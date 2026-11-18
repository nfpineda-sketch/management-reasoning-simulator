"""P3-350 to P3-355, P3-358 (module level): the FACULTY TRAJECTORY RE-REVIEW set, its adapter, its durable log and its summary.

What it proves (pure: no Streamlit, no engine):

* the stored set is the certified candidate review set's FIRST set, unchanged, in the shape the review page draws -- the same values as the certified static kit, key by key and table by table;
* it holds exactly FR-B, FR-C, FR-E and FR-G in that order, nothing of the other two sets, no comparator, no earlier trajectory and no parameter; a re-signed, edited, reordered or leaking set is refused;
* the log is the first review's: the first impression locks and can never change, a forged blind answer after the lock is ignored, a second submit creates no second record, a corrupt log refuses writes;
* it shares NO file with the first review: another directory, another record directory, another identity, and a whole re-review leaves the first review's files byte-for-byte as they were;
* the summary counts only records that verify against the log that closed them.
"""
import ast
import hashlib
import json
import os
import re
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

ROOT = Path(__file__).resolve().parent
KIT = ROOT / "faculty_review_kit" / "region_conjunta_v1" / "conjunto_1.md"
CANDIDATES = json.loads(rr.CANDIDATE_SET_PATH.read_text(encoding="utf-8"))
FIRST_SET = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
LOADED = rr.load_set()
ITEMS = LOADED["items"]
ANSWERS = {"Q1": "Partly", "Q2": "Too late", "Q3": "Too small", "Q4": "Uncertain", "Q5": "Maybe"}
#: What the faculty asked the reviewer to be asked (FD-REREVIEW-07). FR-G: the static kit, which FD-REREVIEW-07 names as the source, says "A single order THAT spans"; the faculty text drops the word.
FD_PURPOSE = {"FR-B": "Does early volume and blood replacement produce a pressure response that begins at an appropriate time and has a plausible size?",
              "FR-C": "After two hours without treatment, is the deterioration and then the response to the same treatment plausible, and does a resident risk being misled by the trajectory?",
              "FR-E": "Is the recovery after delayed treatment coherent in direction, timing and magnitude?",
              "FR-G": "A single order spans a long interval: is the pressure trajectory across the whole infusion plausible, and is the response timed with the volume given?"}


def _tree_digest(path: Path) -> str:
    """A digest of every file under ``path`` (names and bytes): the proof that a directory was not touched."""
    digest = hashlib.sha256()
    for entry in sorted(Path(path).rglob("*")):
        if entry.is_file():
            digest.update(str(entry.relative_to(path)).encode() + b"\0" + entry.read_bytes() + b"\0")
    return digest.hexdigest()


def _log(tmp_path, scenario_id="FR-B", reviewer="ref000000001"):
    return rr.ReReviewLog(tmp_path, reviewer, ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"], account={"role": "faculty"})


def _complete(log, overall="ACCEPT", comment="first impression note", overall_comment="overall note"):
    for question, value in ANSWERS.items():
        assert log.answer(question, value)["ok"]
    assert log.comment(comment)["ok"] and log.lock()["ok"]
    assert log.set_overall(overall)["ok"] and log.overall_comment(overall_comment)["ok"]
    return log.submit()


def _resign(record: dict) -> dict:
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    return {**rest, "record_digest": ftr._digest(rest)}


# -- the set ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_r1_the_set_verifies_is_pinned_and_holds_exactly_the_four_scenarios_in_order():
    assert LOADED["ok"] and LOADED["problems"] == [] and LOADED["digest"] == rr.PINNED_SET_DIGEST
    assert list(ITEMS) == ["FR-B", "FR-C", "FR-E", "FR-G"] == list(rr.SCENARIOS)
    assert [entry["scenario_id"] for entry in rr.sequence(ITEMS)] == ["FR-B", "FR-C", "FR-E", "FR-G"] and all(entry["required"] for entry in rr.sequence(ITEMS))
    record = json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
    assert record["set_id"] == rr.SET_ID == "GI_JOINT_REGION_V1_FACULTY_REREVIEW" and record["record_type"] == rr.SET_TYPE
    assert not any(item["stopped"] for item in ITEMS.values())


def test_r2_the_interactive_data_is_the_certified_candidate_review_set_unchanged():
    chosen = {item["scenario_id"]: item for item in CANDIDATES["items"] if item["set"] == "CONJUNTO-1"}
    assert CANDIDATES["record_digest"] == LOADED["audit"]["candidate_review_set_digest"]
    for scenario_id, item in ITEMS.items():
        source = chosen[scenario_id]
        for key in ("title", "context", "purpose", "arrival", "common"):
            assert item[key] == source[key], (scenario_id, key)
        assert [{key: row[key] for key in ("n", "minute", "advance", "action", "result")} for row in item["timeline"]] == source["timeline"], scenario_id
        assert [{"minute": row["minute"], "hr": row["hr"], "crt": row["crt"]} for row in item["context_vitals"]] == source["heart_rate_and_capillary_refill"], scenario_id
        assert item["stopped"] == source["stopped"] is False and item["required"] is True
        assert LOADED["audit"]["candidate_item_ids"][scenario_id] == source["item_id"]
    # the stored file is what the certified sources produce, byte for byte (the build tool's own check)
    first = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    blind_key = json.loads(rr.BLIND_KEY_PATH.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(rr.build_set(CANDIDATES, first, blind_key))) == json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
    assert rr.SET_PATH.read_text(encoding="utf-8") == json.dumps(rr.build_set(CANDIDATES, first, blind_key), indent=1, sort_keys=True) + "\n"


def _kit_sections() -> dict:
    """The static kit's first set, parsed: per scenario its question, arrival line, the 'what was done' rows and the pressure table (the document the reviewer would otherwise have read)."""
    text = KIT.read_text(encoding="utf-8")
    sections = {}
    for block in re.split(r"\n## (?=FR-)", text)[1:]:
        scenario_id = block.split(" ·", 1)[0]
        tables = re.findall(r"((?:^\|.*\n)+)", block, re.M)
        done = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in tables[0].splitlines()[2:]]
        values = [[cell.strip().replace("**", "").replace("(llegada)", "").strip() for cell in line.strip().strip("|").split("|")] for line in tables[1].splitlines()[2:]]
        sections[scenario_id] = {"purpose": re.search(r"\*\*Qué se juzga:\*\* (.*)", block).group(1).strip(), "arrival": re.search(r"\*\*Llegada:\*\* (.*)", block).group(1).strip(), "done": done, "values": values}
    return sections


def test_r3_the_interactive_values_equal_the_static_kit_table_by_table():
    sections = _kit_sections()
    assert list(sections) == ["FR-B", "FR-C", "FR-E", "FR-G"]
    for scenario_id, item in ITEMS.items():
        kit = sections[scenario_id]
        assert kit["purpose"] == item["purpose"]
        assert [[str(row["minute"]), row["action"], row["result"]] for row in item["timeline"]] == kit["done"], scenario_id
        # what the reviewer is shown: minute, SBP, DBP, MAP (FD-REREVIEW-23); the same four columns of the kit's table
        assert [[str(row["minute"]), str(row["sbp"]), str(row["dbp"]), str(row["map"])] for row in rr.values_table(item)] == [row[:4] for row in kit["values"]], scenario_id
        # what the set keeps (it is pinned and certified): the heart rate and capillary refill of the kit, which the page no longer shows
        kept = [[str(row["hr"]), ("—" if row["crt"] is None else f"{float(row['crt']):.1f}".rstrip("0").rstrip(".").replace(".", ","))] for row in item["context_vitals"]]
        assert kept == [row[4:] for row in kit["values"]], scenario_id
        arrival = item["arrival"]
        assert f"PA {arrival['sbp']}/{arrival['dbp']} mmHg (PAM {arrival['map']})" in kit["arrival"]


def test_r4_what_you_are_judging_is_the_question_the_faculty_asked():
    for scenario_id in rr.SCENARIOS:
        shown = ITEMS[scenario_id]["purpose"]
        if scenario_id != "FR-G":
            assert shown == FD_PURPOSE[scenario_id]
    # the one divergence between two sources, kept visible: the faculty text drops the word "that" the certified kit has; the page shows the kit's (FD-REREVIEW-07 names the kit as the source)
    assert ITEMS["FR-G"]["purpose"] == "A single order that spans a long interval: is the pressure trajectory across the whole infusion plausible, and is the response timed with the volume given?"
    assert ITEMS["FR-G"]["purpose"].replace("order that spans", "order spans") == FD_PURPOSE["FR-G"]


def test_r5_the_set_holds_nothing_of_the_other_sets_the_comparator_or_the_earlier_trajectory():
    text = rr.SET_PATH.read_text(encoding="utf-8")
    record = json.loads(text)
    assert sorted(record) == ["audit", "items", "order", "record_digest", "record_type", "set_id", "statement", "version", "what_it_is"]
    assert len(record["items"]) == 4 and all(sorted(item) == sorted(["scenario_id", "title", "context", "purpose", "arrival", "timeline", "common", "context_vitals", "stopped", "required"]) for item in record["items"])
    assert not re.search(r"\bLOW\b|\bHIGH\b|CONJUNTO-2|CONJUNTO-3", text)                      # the whole file: no witness name of the other sets
    assert not re.search(r"comparator|legacy|candidate|witness|conjunto|center_reference", json.dumps(record["items"]), re.I)      # what the reviewer is shown: no comparator, no identity
    for token in ("CONJUNTO-2", "CONJUNTO-3", "LOW", "HIGH", "binding", "bleed_rate", "preload", "kernel", "crystalloid_kernel"):
        assert token not in text, token
    assert record["audit"]["witness"] == "CENTER_REFERENCE" and record["audit"]["candidate"] == "JOINT_REGION_V1_CANDIDATE"
    # the other two sets' trajectories are nowhere in the file
    others = {tuple((point["minute"], point["sbp"], point["dbp"]) for point in item["common"]) for item in CANDIDATES["items"] if item["set"] != "CONJUNTO-1"}
    mine = {tuple((point["minute"], point["sbp"], point["dbp"]) for point in item["common"]) for item in record["items"]}
    assert not (others & mine)
    # and the earlier reviewed trajectories (the first review set's) are not the ones in this set
    earlier = {tuple((point["minute"], point["sbp"], point["dbp"]) for point in ftr.blind_view(item)["common"]) for item in FIRST_SET["items"]}
    assert not (earlier & mine)


@pytest.mark.parametrize("name,mutate,expected", [
    ("edited value", lambda r: r["items"][0]["common"][1].update(sbp=99.0), "does not recompute"),
    ("extra scenario", lambda r: r["items"].append(dict(r["items"][0], scenario_id="FR-A")), "does not recompute"),
])
def test_r6a_an_edited_or_extended_set_is_refused(tmp_path, name, mutate, expected):
    record = json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = rr.load_set(path)
    assert not result["ok"] and result["items"] == {} and expected in result["problems"][0], name


def test_r6b_a_re_signed_set_is_refused_until_its_digest_is_pinned_in_code(tmp_path):
    record = json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
    record["items"][0]["common"][1]["sbp"] = 99.0
    record["items"][0]["common"][1]["map"] = round((99 + 2 * record["items"][0]["common"][1]["dbp"]) / 3)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(_resign(record)), encoding="utf-8")
    result = rr.load_set(path)
    assert not result["ok"] and "not the pinned one" in result["problems"][0]
    assert rr.load_set(tmp_path / "missing.json")["ok"] is False and rr.load_set(tmp_path / "missing.json")["items"] == {}


@pytest.mark.parametrize("mutate,expected", [
    (lambda r: r["items"].reverse(), "exactly its four scenarios in order"),
    (lambda r: r["items"].pop(), "exactly its four scenarios in order"),
    (lambda r: r["items"][0].update(stopped=True), "draws no stop"),
    (lambda r: r["items"][0]["common"][1].update(map=1.0), "MAP"),
    (lambda r: r["items"][0]["common"][1].update(sbp=89.5), "whole mmHg"),
    (lambda r: r["items"][0]["common"][0].update(sbp=77.0), "arrival"),
    (lambda r: r["items"][0].update(context="the CENTER_REFERENCE configuration"), "carries"),
    (lambda r: r["items"][1].update(purpose="Compare with the legacy engine."), "carries"),
    (lambda r: r["items"][2].update(title="Candidate trajectory"), "carries"),
    (lambda r: r["items"][3]["timeline"][0].pop("executed"), "exactly the stored keys"),
    (lambda r: r["items"][3]["timeline"][0].update(executed="yes"), "marker flags"),
    (lambda r: r["items"][0].update(legacy_comparator=[{"minute": 5, "sbp": 99}]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(extra_params={"bleed_rate": 8.97, "witness": "x"}), "exactly the stored keys"),
    (lambda r: r["items"][0].update(bundle={"authority_view": {"halted": True}}), "exactly the stored keys"),
    (lambda r: r["items"][0]["arrival"].update(secret=1), "exactly the stored keys"),
    (lambda r: r["items"][0]["common"][1].update(note="legacy 112"), "exactly the stored keys"),
    (lambda r: r["items"][0]["context_vitals"][0].update(source="x"), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common=["x", "x", "x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(timeline=["x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common="not a list"), "wrong type"),
    (lambda r: r.update(items=[1, 2, 3, 4]), "exactly its four scenarios"),
    (lambda r: r.update(items="four"), "exactly its four scenarios"),
    (lambda r: r["items"][0].update(title=""), "title is missing"),
])
def test_r6c_a_set_that_leaks_is_not_the_package_or_does_not_hold_is_refused_even_when_re_signed_and_pinned(tmp_path, mutate, expected):
    record = json.loads(rr.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    signed = _resign(record)
    path.write_text(json.dumps(signed), encoding="utf-8")
    result = rr.load_set(path, expected_digest=signed["record_digest"])
    assert not result["ok"] and result["items"] == {} and any(expected in problem for problem in result["problems"]), result["problems"]


def test_r6d_the_loader_never_raises_on_a_malformed_set(tmp_path):
    for broken in (None, [], "x", {"record_type": rr.SET_TYPE}, {"record_type": rr.SET_TYPE, "set_id": rr.SET_ID, "items": None}):
        path = tmp_path / "set.json"
        path.write_text(json.dumps(_resign(broken) if isinstance(broken, dict) else broken), encoding="utf-8")
        result = rr.load_set(path, expected_digest=None)
        assert result["ok"] is False and result["items"] == {} and result["problems"], broken
    assert rr.item_problems(None) and rr.item_problems("x") and rr.item_problems({}) and rr.item_problems({"scenario_id": "FR-B"})


def test_r7_the_view_has_no_comparator_no_reveal_and_only_the_five_questions():
    view = rr.blind_view(ITEMS["FR-B"])
    assert sorted(view) == sorted(["scenario_id", "title", "context", "purpose", "arrival", "timeline", "halted", "stop_minute", "common", "questions"])
    assert [question["id"] for question in view["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"] and view["halted"] is False
    assert [question["choices"] for question in view["questions"]] == [list(question["choices"]) for question in ftr.FIRST_PASS]
    # nothing in the module can return a comparator, a legacy number or another set
    public = {name for name in dir(rr) if not name.startswith("_")}
    assert not {name for name in public if "comparator" in name.lower() or "legacy" in name.lower() or "reveal" in name.lower()}
    tree = ast.parse((ROOT / "faculty_trajectory_rereview_ui.py").read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not {name for name in names if name in ("comparator_view", "CHANGED", "COMPARATOR_LABEL", "COMPARATOR_NOTE", "Locked")}


def test_r7b_the_view_and_the_values_table_carry_no_heart_rate_and_no_capillary_refill_while_the_set_is_unchanged():
    """FD-REREVIEW-23: the reviewer is shown pressure only. The stored, pinned set still holds the values of the earlier encounter (they are not recomputed, not fabricated and not removed from the set)."""
    for scenario_id, item in ITEMS.items():
        view = rr.blind_view(item)
        assert sorted(view["arrival"]) == sorted(rr.ARRIVAL_SHOWN) and "hr" not in view["arrival"] and "crt" not in view["arrival"]
        dumped = json.dumps(view, sort_keys=True).lower()
        assert not re.search(r'"hr"|"crt"|heart|capillary|context_vitals', dumped), scenario_id
        assert all(sorted(row) == ["dbp", "map", "minute", "sbp"] for row in rr.values_table(item))
        assert item["arrival"]["hr"] is not None and item["context_vitals"], "the stored set keeps them: nothing was regenerated or repinned"
    assert LOADED["digest"] == rr.PINNED_SET_DIGEST == "c30ab7f1fae514ff7e7c4de50e1d11b60f08efc6021804e162b70100d52b344f"


# -- the durable log ---------------------------------------------------------------------------------------------------------------------------------------------------------
def test_r8_the_whole_review_of_one_scenario_writes_one_verified_record(tmp_path):
    log = _log(tmp_path)
    assert log.state()["status"] == "NEW"
    outcome = _complete(log, overall="ACCEPT_WITH_LIMITATION")
    assert outcome["ok"] and outcome["record_id"] and Path(outcome["path"]) == log.record_path
    state = log.state()
    assert state["status"] == "SUBMITTED" and state["locked"] and state["overall"] == "ACCEPT_WITH_LIMITATION" and state["overall_comment"] == "overall note"
    record = json.loads(log.record_path.read_text(encoding="utf-8"))
    assert record["record_type"] == rr.RECORD_TYPE and record["set_id"] == rr.SET_ID and record["comparator_shown"] is False and record["scenario_id"] == "FR-B"
    assert record["first_pass"]["answers"] == ANSWERS == record["first_pass"]["answers_at_lock"] and record["first_pass"]["comment"] == "first impression note"
    assert record["overall"] == {"judgment": "ACCEPT_WITH_LIMITATION", "comment": "overall note"} and "post_reveal" not in record
    assert record["linkage"]["witness"] == "CENTER_REFERENCE" and record["linkage"]["candidate"] == "JOINT_REGION_V1_CANDIDATE" and record["linkage"]["set_digest"] == rr.PINNED_SET_DIGEST
    assert rr.record_problems(record, state, log) == []
    assert "ref000000001" == record["reviewer_ref"] and record["reviewer_role"] == "faculty"


def test_r8b_the_first_impression_locks_and_can_never_change(tmp_path):
    log = _log(tmp_path)
    assert not log.lock()["ok"] and "answer Q1" in log.lock()["why"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.set_overall("ACCEPT")["ok"] and not log.overall_comment("x")["ok"], "the overall judgment waits for the lock"
    assert log.lock()["ok"] and not log.lock()["ok"]
    for refused in (log.answer("Q1", "Wrong"), log.comment("changed my mind"), log.answer("Q5", "Yes")):
        assert not refused["ok"] and "locked" in refused["why"]
    assert log.state()["locked_answers"] == ANSWERS
    # a forged blind answer written after the lock (a well-formed chained event) is IGNORED by the reader
    forged = {"seq": log.state()["events"] + 1, "prev": log.state()["head"], "kind": "blind", "at": "2026-11-16T00:00:00+00:00", "data": {"id": "Q1", "value": "Wrong"}}
    with open(log.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    assert log.state()["blind"]["Q1"] == ANSWERS["Q1"] and log.state()["locked_answers"] == ANSWERS and log.state()["status"] == "LOCKED"


def test_r8c_there_is_no_comparator_step_and_the_submit_needs_only_the_overall_judgment(tmp_path):
    log = _log(tmp_path)
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.answer("R1", "No")["ok"] and not log.comment("x", after_reveal=True)["ok"] and not log.answer("Q5H", "Understandable")["ok"]
    assert not log.submit()["ok"]                                              # nothing locked
    log.lock()
    assert not log.submit()["ok"] and "overall" in log.submit()["why"]
    assert not log.answer("R1", "No")["ok"]
    log.set_overall("REJECT")
    assert log.submit()["ok"]
    assert not log.set_overall("ACCEPT")["ok"] and log.state()["overall"] == "REJECT"       # submitted: closed


def test_r8d_a_second_submit_creates_no_second_record_and_the_overall_choice_must_be_valid(tmp_path):
    log = _log(tmp_path)
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.set_overall("MAYBE")["ok"]
    log.set_overall("RECALIBRATE")
    first = log.submit()
    second = log.submit()
    assert first["ok"] and not second["ok"] and second["why"] == "already submitted" and second["record_id"] == first["record_id"]
    assert len(list(log.records.glob("*.json"))) == 1 and not list(log.records.glob("*.superseded-*"))


def test_r8e_a_forged_chained_log_closed_without_an_overall_judgment_is_unreadable_and_refuses_writes(tmp_path):
    log = _log(tmp_path)
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    forged = {"seq": log.state()["events"] + 1, "prev": log.state()["head"], "kind": "submitted", "at": "2026-11-16T00:00:00+00:00", "data": {"record_id": "forged"}}
    with open(log.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    broken = _log(tmp_path)
    assert broken.state()["status"] == "UNREADABLE" and "overall" in broken.state()["why"]
    assert not broken.set_overall("ACCEPT")["ok"] and not broken.submit()["ok"]


def test_r9_a_refresh_restores_everything_and_a_corrupt_log_refuses_writes(tmp_path):
    log = _log(tmp_path)
    log.answer("Q1", "Wrong"); log.answer("Q2", "Too late"); log.comment("partial note")
    again = _log(tmp_path)                                                    # a refresh: a new object over the same files
    assert again.state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"} and again.state()["blind_comment"] == "partial note" and again.state()["status"] == "IN_PROGRESS"
    # a torn tail (a crash mid-write) was never acknowledged and is ignored
    with open(log.path, "ab") as handle:
        handle.write(b'{"seq": 4, "prev": "x"')
    assert _log(tmp_path).state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"}
    # an altered log is unreadable and nothing more is written
    lines = log.path.read_text(encoding="utf-8").split("\n")
    log.path.write_text(lines[0].replace("Wrong", "Expected") + "\n" + "\n".join(lines[1:]), encoding="utf-8")
    broken = _log(tmp_path)
    assert broken.state()["status"] == "UNREADABLE" and not broken.answer("Q3", "Plausible")["ok"]


def test_r10_the_re_review_shares_no_file_with_the_first_review_and_leaves_it_untouched(tmp_path):
    first_logs, first_records = tmp_path / ftr.SUBDIR, tmp_path / ftr.RECORDS_SUBDIR
    for directory in (first_logs, first_records):
        directory.mkdir(parents=True)
        (directory / "seed.json").write_text('{"kept": true}', encoding="utf-8")
    before = (_tree_digest(first_logs), _tree_digest(first_records))
    for scenario_id in rr.SCENARIOS:
        log = _log(tmp_path, scenario_id)
        assert _complete(log)["ok"]
        assert first_logs not in log.path.parents and first_records not in log.record_path.parents
        assert log.path.parent.parent.name == rr.SUBDIR != ftr.SUBDIR and log.records.name == rr.RECORDS_SUBDIR != ftr.RECORDS_SUBDIR
    assert (_tree_digest(first_logs), _tree_digest(first_records)) == before
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted([ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR])


def test_r10b_identities_are_unique_and_cannot_collide_with_the_first_reviews(tmp_path):
    logs = [_log(tmp_path, scenario_id) for scenario_id in rr.SCENARIOS]
    assert len({log.path for log in logs}) == len({log.record_path for log in logs}) == len({log.item_digest for log in logs}) == 4
    for log in logs:
        assert rr.SET_ID in log.path.name and log.item["scenario_id"] in log.path.name
    # the first review's own log of the same scenario, same reviewer, same root: another file, another state
    first = ftr.ReviewLog(tmp_path, "ref000000001", next(item for item in FIRST_SET["items"] if item["scenario_id"] == "FR-B"), set_digest=ftr.PINNED_SET_DIGEST)
    assert first.path != logs[0].path and first.record_path != logs[0].record_path
    assert _complete(logs[0])["ok"] and first.state()["status"] == "NEW" and not first.path.exists()
    # and the two reviewers are two logs
    assert _log(tmp_path, "FR-B", reviewer="ref000000002").state()["status"] == "NEW"


def test_r11_the_summary_counts_only_records_that_verify_and_reports_the_rest(tmp_path):
    order = rr.sequence(ITEMS)
    for scenario_id, overall in (("FR-B", "ACCEPT"), ("FR-C", "ACCEPT_WITH_LIMITATION"), ("FR-E", "RECALIBRATE")):
        assert _complete(_log(tmp_path, scenario_id), overall=overall, overall_comment=f"note {scenario_id}")["ok"]
    summary = rr.summarize(tmp_path, "ref000000001", ITEMS, order, LOADED["digest"], LOADED["audit"])
    assert not summary["complete"] and summary["scenarios_reviewed"] == ["FR-B", "FR-C", "FR-E"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 1, "RECALIBRATE": 1, "REJECT": 0}
    assert summary["technical_problems"] == [] and {row["scenario_id"] for row in summary["scenarios"]} == {"FR-B", "FR-C", "FR-E"}
    assert [comment["text"] for comment in summary["comments"] if comment["stage"] == "overall"] == ["note FR-B", "note FR-C", "note FR-E"]
    assert _complete(_log(tmp_path, "FR-G"), overall="REJECT")["ok"]
    summary = rr.summarize(tmp_path, "ref000000001", ITEMS, order, LOADED["digest"], LOADED["audit"])
    assert summary["complete"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 1, "RECALIBRATE": 1, "REJECT": 1}
    written = rr.write_summary(tmp_path, summary)
    assert written["written"] and Path(written["path"]).parent.name == rr.SUBDIR and not (tmp_path / ftr.SUBDIR).exists()
    # a record that does not agree with the log that closed it is NOT counted
    altered = _log(tmp_path, "FR-E")
    record = json.loads(altered.record_path.read_text(encoding="utf-8"))
    record["overall"]["judgment"] = "ACCEPT"
    altered.record_path.write_text(json.dumps(record), encoding="utf-8")
    summary = rr.summarize(tmp_path, "ref000000001", ITEMS, order, LOADED["digest"], LOADED["audit"])
    assert not summary["complete"] and "FR-E" not in summary["scenarios_reviewed"] and any("FR-E" in problem for problem in summary["technical_problems"])
    assert summary["judgments"]["ACCEPT"] == 1                                # FR-B only: the altered FR-E was not counted as an ACCEPT


def test_r11b_a_comment_that_looks_like_an_identifier_is_refused_and_a_long_one_too(tmp_path):
    log = _log(tmp_path)
    assert not log.comment("patient MRN 12345678")["ok"] and not log.comment("x" * (ftr.MAX_COMMENT + 1))["ok"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.overall_comment("write to dr.someone@example.com")["ok"] and not log.overall_comment("y" * (ftr.MAX_COMMENT + 1))["ok"]
    assert log.overall_comment("MAP about 65 to 75 mmHg")["ok"] and log.state()["overall_comment"] == "MAP about 65 to 75 mmHg"


# -- boundaries ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_r12_the_new_modules_import_nothing_of_the_engine_the_authority_the_shadow_or_the_core():
    forbidden = ("runtime_authority", "runtime_shadow", "runtime_pressure_grant", "clinical_core", "family_engine", "clinical_physiology", "app", "runtime_faculty", "faculty_review_ui", "streamlit")
    for name, banned in (("faculty_trajectory_rereview.py", forbidden), ("faculty_trajectory_rereview_ui.py", forbidden[:-1])):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {str(node.module).split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not imported & set(banned), (name, imported & set(banned))
    launcher = ast.parse((ROOT / "faculty_review_ui.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(launcher) if isinstance(node, ast.Import) for alias in node.names} | {str(node.module) for node in ast.walk(launcher) if isinstance(node, ast.ImportFrom)}
    assert not any("trajectory" in name or "rereview" in name for name in imports), imports
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "rereview_page=_faculty_rereview_ui.draw" in app and "trajectory_page=_faculty_trajectory_ui.draw" in app and "default_mode=_faculty_review_ui.TONE_MODE" in app and "hold_prior_modes=_faculty_rereview_ui.prior_modes_held" in app      # (the landing page after the re-review is the tone review: P3-406)


def test_r13_the_first_review_and_the_first_human_review_are_preserved():
    assert ftr.PINNED_SET_DIGEST == "f65d1127f3fb97926334d695aeab37b92f3a44236cec2ae025025eec90ba1649" and FIRST_SET["record_digest"] == ftr.PINNED_SET_DIGEST
    human = json.loads((ROOT / "docs" / "revision" / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json").read_text(encoding="utf-8"))
    assert human["record_digest"] == "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
    rest = {key: value for key, value in human.items() if key != "record_digest"}
    assert ftr._digest(rest) == human["record_digest"]                       # the preserved record still recomputes: nothing of it was rewritten
    assert rr.SET_PATH != ftr.SET_PATH and rr.SUBDIR != ftr.SUBDIR and rr.RECORDS_SUBDIR != ftr.RECORDS_SUBDIR
    # the shared base class still behaves as it did for the first review (the hooks are additive)
    assert ftr.ReviewLog.SUBDIR_NAME == ftr.SUBDIR and ftr.ReviewLog.RECORDS_NAME == ftr.RECORDS_SUBDIR


def test_r14_the_build_tool_refuses_a_candidate_whose_timeline_is_not_the_one_the_page_draws():
    first = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    blind_key = json.loads(rr.BLIND_KEY_PATH.read_text(encoding="utf-8"))
    broken = json.loads(json.dumps(CANDIDATES))
    next(item for item in broken["items"] if item["set"] == "CONJUNTO-1" and item["scenario_id"] == "FR-B")["timeline"][1]["action"] = "Give 2 litres."
    with pytest.raises(ValueError, match="timeline"):
        rr.build_set(broken, first, blind_key)
    short = json.loads(json.dumps(CANDIDATES))
    short["items"] = [item for item in short["items"] if not (item["set"] == "CONJUNTO-1" and item["scenario_id"] == "FR-G")]
    with pytest.raises(ValueError, match="exactly"):
        rr.build_set(short, first, blind_key)
