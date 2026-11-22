"""P3-440 to P3-443 and P3-446 (module level): the NOREPINEPHRINE TITRATION REVIEW set, its durable log and its summary.

What it proves (pure: no Streamlit, no engine):

* the stored set is pinned in code and holds exactly TIT-1 to TIT-5, in that order, all required, with the faculty's own question for each and the rate changes the faculty named (the START-only case is NOT in it);
* a re-signed, edited, extended, reordered or leaking set is refused, even when re-signed AND pinned; the loader never raises;
* what the reviewer is shown carries the clinical picture, every change of the rate (in a table and as a marker on the graph) and the pressure trajectory, and NOTHING of the mechanism: no other setting of the
  response (no LOW, no HIGH), no parameter, no time constant, no tone state, no writer, no rate history, no flow, no delivery, no debt, no consciousness, no collapse state, no heart rate, no capillary refill, no
  comparator, no earlier trajectory or judgment; the limitations leave the loader apart from the items;
* the review log is the blind re-review's (the lock is final, a second submit creates no second record, a forged log is unreadable), in files of its own, and a whole review leaves every earlier review's files untouched;
* the summary counts only records that verify against the log that closed them and states the limitations only when the review is complete.
"""
import ast
import hashlib
import json
import re
from pathlib import Path

import pytest

import faculty_titration_review as ftt
import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr
import historical_records as hr

ROOT = Path(__file__).resolve().parent
LOADED = ftt.load_set()
ITEMS = LOADED["items"]
ANSWERS = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No"}
SCENARIOS = ("TIT-1", "TIT-2", "TIT-3", "TIT-4", "TIT-5")
#: The faculty's own wording (the assignment of 2026-11-19, FD-TITREV-07), copied here on purpose: the builder's and the module's text are not the reference of this test.
FACULTY_QUESTION = {
    "TIT-1": "Does the pressure response increase smoothly and at an appropriate time after the norepinephrine rate is increased?",
    "TIT-2": "Does the pressure response decrease smoothly and at an appropriate time after the norepinephrine rate is reduced?",
    "TIT-3": "After norepinephrine is stopped, does the pressure effect decay with a clinically plausible delay rather than disappearing instantly?",
    "TIT-4": "Across sequential rate changes, does the pressure trajectory follow the ordered norepinephrine dose changes in the correct direction and sequence?",
    "TIT-5": "After norepinephrine is stopped and later restarted at an explicit valid rate, does the pressure response reappear causally without retaining an inappropriate residual effect?"}
#: What each scenario IS (FD-TITREV-04), written here by hand: ``(minute, rate after the change in mcg/min)``; 0 is a stop.
FACULTY_PLAN = {"TIT-1": [(2, 5.0), (10, 10.0)], "TIT-2": [(2, 10.0), (10, 4.0)], "TIT-3": [(2, 10.0), (10, 0.0)], "TIT-4": [(2, 5.0), (10, 10.0), (18, 4.0), (25, 0.0)], "TIT-5": [(2, 10.0), (10, 0.0), (18, 10.0)]}
OPERATIONS = {"TIT-1": ["START", "INCREASE"], "TIT-2": ["START", "DECREASE"], "TIT-3": ["START", "STOP"], "TIT-4": ["START", "INCREASE", "DECREASE", "STOP"], "TIT-5": ["START", "STOP", "RESTART"]}
#: What may never be in a reviewer-facing item or view (the first-pass blindness of the assignment).
MECHANISM = re.compile(r"center_reference|witness|legacy|comparator|tone_gain|half[ _-]?effect|onset|offset|\btau\b|parameter|amendment|candidate|kernel|consciousness|cardiac output|oxygen|debt|delivery|sensitivity|"
                       r"tone state|collapse state|heart rate|capillary|writer|rate[ _]history|snapshot|lineage|mcg/kg|\bLOW\b|\bHIGH\b", re.I)


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for entry in sorted(Path(path).rglob("*")):
        if entry.is_file():
            digest.update(str(entry.relative_to(path)).encode() + b"\0" + entry.read_bytes() + b"\0")
    return digest.hexdigest()


def _log(tmp_path, scenario_id="TIT-1", reviewer="ref000000001"):
    return ftt.TitrationReviewLog(tmp_path, reviewer, ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"], account={"role": "faculty"})


def _complete(log, overall="ACCEPT", comment="first impression note", overall_comment="overall note"):
    for question, value in ANSWERS.items():
        assert log.answer(question, value)["ok"]
    assert log.comment(comment)["ok"] and log.lock()["ok"]
    assert log.set_overall(overall)["ok"] and log.overall_comment(overall_comment)["ok"]
    return log.submit()


def _resign(record: dict) -> dict:
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    return {**rest, "record_digest": ftt._seal_digest(rest)}


def _summary(tmp_path, reviewer="ref000000001"):
    return ftt.summarize(tmp_path, reviewer, ITEMS, ftt.sequence(ITEMS), LOADED["digest"], LOADED["audit"], LOADED["limitations"])


# -- the set ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t1_the_set_verifies_is_pinned_and_holds_exactly_the_five_scenarios_in_order():
    assert LOADED["ok"] and LOADED["problems"] == [] and LOADED["digest"] == ftt.PINNED_SET_DIGEST
    assert list(ITEMS) == list(SCENARIOS) == list(ftt.SCENARIOS)
    assert [entry["scenario_id"] for entry in ftt.sequence(ITEMS)] == list(SCENARIOS) and all(entry["required"] for entry in ftt.sequence(ITEMS))
    assert ftt.SET_ID == "NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW" and ftt.PINNED_SET_DIGEST != "0" * 64 and not ftt.PINNED_SET_DIGEST.startswith("PENDING")
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    assert record["record_digest"] == ftt.PINNED_SET_DIGEST and record["set_id"] == ftt.SET_ID and record["order"] == list(SCENARIOS)
    assert ftt._seal_digest({key: value for key, value in record.items() if key != "record_digest"}) == record["record_digest"] and hr.record_problems(record) == []


def test_t1b_the_loaders_seal_digest_is_the_historical_record_digest():
    for value in ({"a": 1, "b": [1, 2, {"c": "é"}]}, [], "x", {"k": 1.5}):
        assert ftt._seal_digest(value) == hr.digest_of(value)


def test_t2_what_you_are_judging_is_the_question_the_faculty_asked_for_each_scenario():
    for scenario_id in SCENARIOS:
        assert ITEMS[scenario_id]["purpose"] == FACULTY_QUESTION[scenario_id] == ftt.QUESTIONS[scenario_id]
        assert ftt.blind_view(ITEMS[scenario_id])["purpose"] == FACULTY_QUESTION[scenario_id]
    assert all(ITEMS[scenario_id]["kind"] == ftt.KIND_CASE and ITEMS[scenario_id]["banner"] == "SYNTHETIC DEVELOPMENT CASE" for scenario_id in SCENARIOS)


def test_t3_every_scenario_is_the_gi_hemorrhage_case_with_the_rate_changes_the_faculty_named_and_a_trajectory_from_that_baseline():
    contexts = {ITEMS[scenario_id]["context"] for scenario_id in SCENARIOS}
    assert len(contexts) == 1 and "57-year-old man" in next(iter(contexts)) and "gastrointestinal" in next(iter(contexts)).lower(), "one hemorrhage case, the one the reviewer already knows (FD-TITREV-03)"
    for scenario_id in SCENARIOS:
        item = ITEMS[scenario_id]
        changes = item["rate_changes"]
        assert [(change["minute"], change["rate_mcg_min"]) for change in changes] == FACULTY_PLAN[scenario_id] and [change["operation"] for change in changes] == OPERATIONS[scenario_id]
        assert [change["n"] for change in changes] == list(range(1, len(changes) + 1)) and all(isinstance(change["rate_mcg_min"], float) for change in changes)
        rows = item["timeline"]
        assert [(row["n"], row["minute"], row["executed"], row["intervention"]) for row in rows] == [(change["n"], change["minute"], True, True) for change in changes]
        assert [row["action"] for row in rows] == [ftt.change_text(change) for change in changes]
        assert item["common"][0]["minute"] == 0 and (item["common"][0]["sbp"], item["common"][0]["dbp"], item["common"][0]["map"]) == (item["arrival"]["sbp"], item["arrival"]["dbp"], item["arrival"]["map"])
        assert item["common"][-1]["minute"] == 32 and len(item["common"]) == 33 and item["table_minutes"][0] == 0 and item["table_minutes"][-1] == 32
        assert all(change["minute"] in item["table_minutes"] for change in changes)
        assert item["baseline_facts"] and item["intervention"] and "left untreated" in item["intervention"]
    assert all(len(ITEMS[scenario_id]["rate_changes"]) >= 2 for scenario_id in SCENARIOS), "a start-only scenario is not part of this review (FD-TITREV-05)"
    assert {ITEMS[scenario_id]["arrival"]["sbp"] for scenario_id in SCENARIOS} == {88}


def test_t3b_the_texts_say_what_was_done_in_clinical_words_with_the_rate_in_mcg_min_only():
    expected = {"TIT-1": ["Start norepinephrine 5 mcg/min", "Increase norepinephrine to 10 mcg/min"], "TIT-2": ["Start norepinephrine 10 mcg/min", "Decrease norepinephrine to 4 mcg/min"],
                "TIT-3": ["Start norepinephrine 10 mcg/min", "Stop norepinephrine"], "TIT-4": ["Start norepinephrine 5 mcg/min", "Increase norepinephrine to 10 mcg/min", "Decrease norepinephrine to 4 mcg/min", "Stop norepinephrine"],
                "TIT-5": ["Start norepinephrine 10 mcg/min", "Stop norepinephrine", "Restart norepinephrine at 10 mcg/min"]}
    for scenario_id, actions in expected.items():
        assert [row["action"] for row in ITEMS[scenario_id]["timeline"]] == actions
        text = json.dumps(ITEMS[scenario_id], sort_keys=True)
        assert "mcg/kg" not in text and "weight" not in text.lower() and "MAP 65" not in text and "titrate" not in text.lower(), "no weight-based dose and no pressure target anywhere"
    stop = ITEMS["TIT-3"]["timeline"][1]
    assert stop["result"] == "Infusion off to minute 32" and ITEMS["TIT-5"]["timeline"][1]["result"] == "Infusion off until minute 18"


def test_t3c_the_graph_marks_the_time_of_every_rate_change_and_nothing_else():
    for scenario_id in SCENARIOS:
        item = ITEMS[scenario_id]
        marks = ftt.markers(item)
        assert [mark["minute"] for mark in marks] == [change["minute"] for change in item["rate_changes"]] == [row["minute"] for row in item["timeline"]]
        assert [mark["label"].split(" · ")[0] for mark in marks] == [str(row["n"]) for row in item["timeline"]], "the number on the graph is the number in the table"
        assert ftt.blind_view(item)["markers"] == marks
    assert [mark["label"] for mark in ftt.markers(ITEMS["TIT-4"])] == ["1 · start 5", "2 · up to 10", "3 · down to 4", "4 · stop"]
    assert [mark["label"] for mark in ftt.markers(ITEMS["TIT-5"])] == ["1 · start 10", "2 · stop", "3 · restart 10"]
    assert [mark["label"] for mark in ftt.markers(ITEMS["TIT-1"])] == ["1 · start 5", "2 · up to 10"] and [mark["label"] for mark in ftt.markers(ITEMS["TIT-2"])] == ["1 · start 10", "2 · down to 4"]


def test_t3d_every_scenario_is_told_apart_by_its_title_and_its_short_name_and_no_title_contains_another():
    titles = [ITEMS[scenario_id]["title"] for scenario_id in SCENARIOS]
    assert len(set(titles)) == 5 and not [(a, b) for a in titles for b in titles if a != b and a in b], "a title that is a prefix of another would let a screen be taken for the wrong scenario"
    assert [ITEMS[scenario_id]["short"] for scenario_id in SCENARIOS] == ["Increase", "Decrease", "Stop", "Sequence", "Restart"]


def test_t4_the_values_table_is_the_trajectory_at_the_named_minutes_and_nothing_else():
    for scenario_id, item in ITEMS.items():
        table = ftt.values_table(item)
        assert [row["minute"] for row in table] == item["table_minutes"] and all(sorted(row) == ["dbp", "map", "minute", "sbp"] for row in table)
        by_minute = {point["minute"]: point for point in item["common"]}
        assert all(row == {"minute": row["minute"], **{key: int(by_minute[row["minute"]][key]) for key in ("sbp", "dbp", "map")}} for row in table)
        assert ftt.y_axis_max(item) == 140 and max(point["sbp"] for point in item["common"]) <= 140


def test_t5_the_questions_are_the_five_the_reviews_use_with_the_same_choices_and_no_stop_question():
    for item in ITEMS.values():
        view = ftt.blind_view(item)
        assert [question["id"] for question in view["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"] and view["halted"] is False and view["stop_minute"] is None
        assert [(question["topic"], question["text"], question["choices"]) for question in view["questions"]] == [(q["topic"], q["text"], list(q["choices"])) for q in ftr.FIRST_PASS]
    assert ftr.OVERALL == ("ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT")


def test_t6_the_first_pass_view_carries_nothing_of_the_mechanism_the_other_settings_or_the_limitations():
    for scenario_id, item in ITEMS.items():
        view = ftt.blind_view(item)
        assert sorted(view) == sorted(["scenario_id", "short", "title", "kind", "banner", "note", "context", "baseline_facts", "purpose", "arrival", "intervention", "timeline", "halted", "stop_minute", "common",
                                       "markers", "questions"])
        assert sorted(view["arrival"]) == sorted(ftt.ARRIVAL_SHOWN) and "hr" not in view["arrival"] and "crt" not in view["arrival"]
        dumped = json.dumps(view, sort_keys=True)
        assert not MECHANISM.search(dumped) and not ftt._LEAK_NAMES.search(dumped), (scenario_id, MECHANISM.search(dumped))
        assert not re.search(r"PUMP_DEPENDENCE|CONSCIOUSNESS_UNDER|MALFORMED_ORDER|limitation", dumped, re.I)
    stored = json.dumps(ITEMS, sort_keys=True)
    assert not MECHANISM.search(stored), "nothing of the mechanism is even stored with the items"
    assert all(sorted(row) == ["dbp", "map", "minute", "sbp"] for item in ITEMS.values() for row in ftt.values_table(item))


def test_t7_the_limitations_are_the_six_the_review_states_and_are_stored_apart_from_the_items():
    assert [entry["id"] for entry in LOADED["limitations"]] == ["EXPLICIT_ABSOLUTE_MCG_MIN_ONLY", "NO_WEIGHT_BASED_DOSING", "NO_MAP_TARGET_TITRATION", "MALFORMED_ORDER_CLOSES_THE_MODELLED_INFUSION",
                                                                "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED"]
    texts = [entry["text"] for entry in LOADED["limitations"]]
    assert "explicit absolute norepinephrine rates in mcg/min" in texts[0] and "mcg/kg/min" in texts[1] and "pressure target" in texts[2] and "ends the modelled infusion" in texts[3]
    assert "neither shown nor judged" in texts[4] and "pump" in texts[5]
    assert not any(key in item for item in ITEMS.values() for key in ("sensitivity", "limitations", "audit", "points", "witnesses", "LOW", "HIGH"))
    assert set(LOADED["audit"]) >= {"witness", "sources", "selection"} and LOADED["audit"]["witness"] == "CENTER_REFERENCE"
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    assert "sensitivity" not in record and not re.search(r'"(LOW|HIGH)"', json.dumps(record)), "no other setting of the response is stored with the set (FD-TITREV-06)"


@pytest.mark.parametrize("name,mutate", [
    ("edited value", lambda r: r["items"][0]["common"][1].update(sbp=99.0)),
    ("extra scenario", lambda r: r["items"].append(dict(r["items"][0], scenario_id="TIT-2"))),
    ("edited limitation", lambda r: r["limitations"][0].update(text="x")),
    ("edited rate", lambda r: r["items"][0]["rate_changes"][1].update(rate_mcg_min=20.0)),
])
def test_t8a_an_edited_or_extended_set_is_refused(tmp_path, name, mutate):
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = ftt.load_set(path)
    assert not result["ok"] and result["items"] == {} and result["limitations"] == [] and "does not recompute" in result["problems"][0], name


def test_t8b_a_re_signed_set_is_refused_until_its_digest_is_pinned_in_code(tmp_path):
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    record["items"][0]["common"][1]["sbp"] = 99.0
    record["items"][0]["common"][1]["map"] = round((99 + 2 * record["items"][0]["common"][1]["dbp"]) / 3)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(_resign(record)), encoding="utf-8")
    result = ftt.load_set(path)
    assert not result["ok"] and "not the pinned one" in result["problems"][0]
    assert ftt.load_set(tmp_path / "missing.json")["ok"] is False and ftt.load_set(tmp_path / "missing.json")["items"] == {}


@pytest.mark.parametrize("mutate,expected", [
    (lambda r: r["items"].reverse(), "exactly its scenarios in order"),
    (lambda r: r["items"].pop(), "exactly its scenarios in order"),
    (lambda r: r["items"][0].update(stopped=True), "draws no stop"),
    (lambda r: r["items"][0].update(required=False), "draws no stop"),
    (lambda r: r["items"][0]["common"][1].update(map=1.0), "MAP"),
    (lambda r: r["items"][0]["common"][1].update(sbp=89.5), "whole mmHg"),
    (lambda r: r["items"][0]["common"][0].update(sbp=77.0), "baseline pressure"),
    (lambda r: r["items"][0].update(context="the CENTER_REFERENCE configuration"), "carries"),
    (lambda r: r["items"][1].update(intervention="Compare with the legacy engine."), "carries"),
    (lambda r: r["items"][2].update(title="Candidate trajectory"), "carries"),
    (lambda r: r["items"][2].update(context="The LOW setting of the response."), "carries"),
    (lambda r: r["items"][2]["baseline_facts"].append("tone_gain 0.6"), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("Consciousness is preserved."), "carries"),
    (lambda r: r["items"][4]["baseline_facts"].append("Sensitivity range 10 to 20."), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("The onset time constant is 1.5 minutes."), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("The offset tau is 2.5."), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("Dosed at 0.1 mcg/kg/min."), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("Titrate to a MAP target of 65."), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("The rate history of the writer."), "carries"),
    (lambda r: r["items"][3]["timeline"][0].pop("executed"), "exactly the stored keys"),
    (lambda r: r["items"][3]["timeline"][0].update(executed="yes"), "every row of the timeline"),
    (lambda r: r["items"][3]["timeline"][0].update(intervention=False), "every row of the timeline"),
    (lambda r: r["items"][0].update(legacy_comparator=[{"minute": 5, "sbp": 99}]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(heart_rate=[124]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(extra_params={"half_effect": 10}), "exactly the stored keys"),
    (lambda r: r["items"][0].update(other_settings={"LOW": [], "HIGH": []}), "exactly the stored keys"),
    (lambda r: r["items"][0].update(support=[0.1, 0.2]), "exactly the stored keys"),
    (lambda r: r["items"][0]["arrival"].update(hr=124), "exactly the stored keys"),
    (lambda r: r["items"][0]["arrival"].update(crt=5), "exactly the stored keys"),
    (lambda r: r["items"][0]["common"][1].update(note="legacy 112"), "exactly the stored keys"),
    (lambda r: r["items"][0]["rate_changes"][0].update(support=0.3), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common=["x", "x", "x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(timeline=["x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(rate_changes=["x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common="not a list"), "wrong type"),
    (lambda r: r["items"][0].update(baseline_facts=[1]), "wrong type"),
    (lambda r: r["items"][0].update(banner="Synthetic probe"), "its own label"),
    (lambda r: r["items"][0].update(kind="SYNTHETIC_PROBE"), "its own label"),
    (lambda r: r["items"][0]["arrival"].update(spo2=None), "states its arrival"),
    (lambda r: r["items"][0].update(purpose=r["items"][1]["purpose"]), "the faculty's own"),
    (lambda r: r["items"][0].update(purpose="Is it smooth?"), "the faculty's own"),
    (lambda r: r["items"][0]["rate_changes"][1].update(rate_mcg_min=20.0), "plan is fixed in code"),
    (lambda r: r["items"][0]["rate_changes"][1].update(minute=11), "plan is fixed in code"),
    (lambda r: r["items"][0]["rate_changes"][1].update(operation="DECREASE"), "plan is fixed in code"),
    (lambda r: r["items"][0]["rate_changes"].pop(), "plan is fixed in code"),
    (lambda r: r["items"][0]["rate_changes"].append({"n": 3, "minute": 20, "operation": "STOP", "rate_mcg_min": 0.0}), "plan is fixed in code"),
    (lambda r: r["items"][3]["rate_changes"].reverse(), "plan is fixed in code"),
    (lambda r: r["items"][0]["timeline"][1].update(action="Increase norepinephrine to 20 mcg/min"), "table of what was done"),
    (lambda r: r["items"][0]["timeline"][1].update(minute=11), "table of what was done"),
    (lambda r: r["items"][0]["timeline"].pop(), "table of what was done"),
    (lambda r: r["items"][4]["timeline"].reverse(), "every row of the timeline"),
    (lambda r: r["items"][0].update(table_minutes=[0, 3]), "table minutes"),
    (lambda r: r["items"][0].update(table_minutes=[1, 2, 32]), "table minutes"),
    (lambda r: r["items"][0].update(table_minutes=[0, 2, 32]), "including every change"),
    (lambda r: r["items"][0].update(table_minutes=[0, 2, 10, 33]), "table minutes"),
    (lambda r: r.update(items=[1, 2, 3, 4, 5]), "exactly its scenarios"),
    (lambda r: r.update(items="five"), "exactly its scenarios"),
    (lambda r: r["items"][0].update(title=""), "title is missing"),
    (lambda r: r["items"][0].update(short=""), "short is missing"),
    (lambda r: r["limitations"].pop(), "limitations of the review"),
    (lambda r: r["limitations"].reverse(), "limitations of the review"),
    (lambda r: r["limitations"][0].update(extra=1), "limitations of the review"),
])
def test_t8c_a_set_that_leaks_is_not_the_package_or_does_not_hold_is_refused_even_when_re_signed_and_pinned(tmp_path, mutate, expected):
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    signed = _resign(record)
    path.write_text(json.dumps(signed), encoding="utf-8")
    result = ftt.load_set(path, expected_digest=signed["record_digest"])
    assert not result["ok"] and result["items"] == {} and result["limitations"] == [] and any(expected in problem for problem in result["problems"]), result["problems"]


@pytest.mark.parametrize("name,operation,previous,rate", [("start from a running infusion", "START", 5.0, 10.0), ("increase to a lower rate", "INCREASE", 10.0, 4.0), ("decrease to a higher rate", "DECREASE", 4.0, 10.0),
                                                          ("stop to a rate", "STOP", 10.0, 5.0), ("stop with nothing running", "STOP", 0.0, 0.0), ("restart while running", "RESTART", 5.0, 10.0),
                                                          ("increase from nothing", "INCREASE", 0.0, 10.0)])
def test_t8e_a_change_that_is_not_what_its_name_says_is_refused(name, operation, previous, rate):
    assert ftt._transition_problem(previous, operation, rate), name
    for operation_ok, before, after in (("START", 0.0, 5.0), ("RESTART", 0.0, 10.0), ("INCREASE", 5.0, 10.0), ("DECREASE", 10.0, 4.0), ("STOP", 10.0, 0.0)):
        assert ftt._transition_problem(before, operation_ok, after) is None


def test_t8d_the_loader_never_raises_on_a_malformed_set(tmp_path):
    for broken in (None, [], "x", {"record_type": ftt.SET_TYPE}, {"record_type": ftt.SET_TYPE, "set_id": ftt.SET_ID, "items": None}, {"record_type": ftt.SET_TYPE, "set_id": ftt.SET_ID, "items": [], "x": float("nan")}):
        path = tmp_path / "set.json"
        path.write_text(json.dumps(_resign(broken) if isinstance(broken, dict) and "x" not in broken else broken), encoding="utf-8")
        result = ftt.load_set(path, expected_digest=None)
        assert result["ok"] is False and result["items"] == {} and result["problems"], broken
    assert ftt.item_problems(None) and ftt.item_problems("x") and ftt.item_problems({}) and ftt.item_problems({"scenario_id": "TIT-1"})


def test_t20_the_loader_never_raises_even_for_a_re_signed_and_pinned_set_with_a_malformed_section(tmp_path):
    for name, mutate in (("audit list", lambda r: r.update(audit=[1])), ("audit text", lambda r: r.update(audit="x")), ("limitations text", lambda r: r.update(limitations="x")),
                         ("audit missing", lambda r: r.pop("audit")), ("limitations missing", lambda r: r.pop("limitations")), ("limitations nulls", lambda r: r.update(limitations=[None] * 6))):
        record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
        mutate(record)
        signed = _resign(record)
        path = tmp_path / "set.json"
        path.write_text(json.dumps(signed), encoding="utf-8")
        result = ftt.load_set(path, expected_digest=signed["record_digest"])
        assert result["ok"] is False and result["items"] == {} and result["problems"], name


@pytest.mark.parametrize("text", ["Heart rate 128/min", "Capillary refill 4 s", "HR 128", "CRT 5 s", "Lactate 6.1 mmol/L", "Mental status: drowsy", "Cardiac index is low", "The tone state is high", "Collapse state: soft",
                                  "Oxygen delivery falls", "Consciousness is preserved", "Dose-response is steep", "Steady-state support is reached", "A MAP target of 65", "The tau is 2.5 min.", "Cardiac flow is reduced.",
                                  "delivery of O2 is low", "Soft collapse", "Titrate to MAP 65", "Dosed at 0.1 mg/kg", "Pulse 120", "The gain is 0.6", "The time constant is long"])
def test_t21_the_text_forms_of_what_the_faculty_forbade_are_refused_even_when_re_signed_and_pinned(tmp_path, text):
    for field in ("baseline_facts", "context"):
        record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
        if field == "context":
            record["items"][0]["context"] += " " + text
        else:
            record["items"][0]["baseline_facts"].append(text)
        signed = _resign(record)
        path = tmp_path / "set.json"
        path.write_text(json.dumps(signed), encoding="utf-8")
        result = ftt.load_set(path, expected_digest=signed["record_digest"])
        assert not result["ok"] and any("carries" in problem for problem in result["problems"]), (field, text)


# -- the durable review ------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t11_the_whole_review_of_one_scenario_writes_one_verified_record(tmp_path):
    log = _log(tmp_path)
    assert log.state()["status"] == "NEW"
    outcome = _complete(log, overall="ACCEPT_WITH_LIMITATION")
    assert outcome["ok"] and outcome["record_id"] and Path(outcome["path"]) == log.record_path
    state = log.state()
    assert state["status"] == "SUBMITTED" and state["locked"] and state["overall"] == "ACCEPT_WITH_LIMITATION" and state["overall_comment"] == "overall note"
    record = json.loads(log.record_path.read_text(encoding="utf-8"))
    assert record["record_type"] == ftt.RECORD_TYPE and record["set_id"] == ftt.SET_ID and record["comparator_shown"] is False and record["scenario_id"] == "TIT-1"
    assert record["first_pass"]["answers"] == ANSWERS == record["first_pass"]["answers_at_lock"] and record["first_pass"]["comment"] == "first impression note"
    assert record["overall"] == {"judgment": "ACCEPT_WITH_LIMITATION", "comment": "overall note"} and "post_reveal" not in record
    assert record["linkage"]["witness"] == "CENTER_REFERENCE" and record["linkage"]["set_digest"] == ftt.PINNED_SET_DIGEST
    assert record["linkage"]["source_record_id"] == "NOREPINEPHRINE_TITRATION_PROBES_V1" and len(record["linkage"]["source_record_digest"]) == 64
    assert ftt.record_problems(record, state, log) == [] and record["reviewer_ref"] == "ref000000001" and record["reviewer_role"] == "faculty"
    assert Path(outcome["path"]).parent.name == ftt.RECORDS_SUBDIR and log.path.parent.parent.name == ftt.SUBDIR


def test_t11b_the_first_impression_locks_and_can_never_change(tmp_path):
    log = _log(tmp_path, "TIT-3")
    assert not log.lock()["ok"] and "answer Q1" in log.lock()["why"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.set_overall("ACCEPT")["ok"] and not log.overall_comment("x")["ok"], "the overall judgment waits for the lock"
    assert log.lock()["ok"] and not log.lock()["ok"]
    for refused in (log.answer("Q1", "Wrong"), log.comment("changed my mind"), log.answer("Q5", "Yes")):
        assert not refused["ok"] and "locked" in refused["why"]
    assert log.state()["locked_answers"] == ANSWERS
    forged = {"seq": log.state()["events"] + 1, "prev": log.state()["head"], "kind": "blind", "at": "2026-11-19T00:00:00+00:00", "data": {"id": "Q1", "value": "Wrong"}}
    with open(log.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    assert log.state()["blind"]["Q1"] == ANSWERS["Q1"] and log.state()["locked_answers"] == ANSWERS and log.state()["status"] == "LOCKED"


def test_t11c_there_is_no_comparator_step_no_stop_question_and_the_submit_needs_only_the_overall_judgment(tmp_path):
    log = _log(tmp_path, "TIT-5")
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.answer("R1", "No")["ok"] and not log.comment("x", after_reveal=True)["ok"] and not log.answer("Q5H", "Understandable")["ok"]
    assert not log.submit()["ok"]
    log.lock()
    assert not log.submit()["ok"] and "overall" in log.submit()["why"]
    log.set_overall("REJECT")
    assert log.submit()["ok"] and not log.set_overall("ACCEPT")["ok"] and log.state()["overall"] == "REJECT"


def test_t11d_a_second_submit_creates_no_second_record_and_a_forged_closed_log_is_unreadable(tmp_path):
    log = _log(tmp_path, "TIT-4")
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.set_overall("MAYBE")["ok"]
    log.set_overall("RECALIBRATE")
    first, second = log.submit(), log.submit()
    assert first["ok"] and not second["ok"] and second["why"] == "already submitted" and second["record_id"] == first["record_id"]
    assert len(list(log.records.glob("*.json"))) == 1 and not list(log.records.glob("*.superseded-*"))
    other = _log(tmp_path, "TIT-2")
    for question, value in ANSWERS.items():
        other.answer(question, value)
    other.lock()
    forged = {"seq": other.state()["events"] + 1, "prev": other.state()["head"], "kind": "submitted", "at": "2026-11-19T00:00:00+00:00", "data": {"record_id": "forged"}}
    with open(other.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    broken = _log(tmp_path, "TIT-2")
    assert broken.state()["status"] == "UNREADABLE" and "overall" in broken.state()["why"] and not broken.set_overall("ACCEPT")["ok"] and not broken.submit()["ok"]


def test_t12_a_refresh_restores_everything_and_a_corrupt_log_refuses_writes(tmp_path):
    log = _log(tmp_path, "TIT-2")
    log.answer("Q1", "Wrong"); log.answer("Q2", "Too late"); log.comment("partial note")
    again = _log(tmp_path, "TIT-2")
    assert again.state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"} and again.state()["blind_comment"] == "partial note" and again.state()["status"] == "IN_PROGRESS"
    with open(log.path, "ab") as handle:
        handle.write(b'{"seq": 4, "prev": "x"')
    assert _log(tmp_path, "TIT-2").state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"}
    lines = log.path.read_text(encoding="utf-8").split("\n")
    log.path.write_text(lines[0].replace("Wrong", "Expected") + "\n" + "\n".join(lines[1:]), encoding="utf-8")
    broken = _log(tmp_path, "TIT-2")
    assert broken.state()["status"] == "UNREADABLE" and not broken.answer("Q3", "Plausible")["ok"]


def test_t13_the_review_advances_scenario_by_scenario_in_order_and_is_complete_after_the_fifth(tmp_path):
    logs = {scenario_id: _log(tmp_path, scenario_id) for scenario_id in SCENARIOS}
    order = ftt.sequence(ITEMS)
    for position, scenario_id in enumerate(SCENARIOS):
        prog = ftt.progress(logs, order)
        assert prog["current"] == scenario_id and prog["enterable"] == set(SCENARIOS[:position]) | {scenario_id} and not prog["required_done"]
        assert prog["remaining_required"] == 5 - position and prog["estimated_minutes_left"] == ftr.MINUTES_PER_SCENARIO * (5 - position)
        assert _complete(logs[scenario_id])["ok"]
    prog = ftt.progress(logs, order)
    assert prog["current"] is None and prog["required_done"] and prog["all_done"] and prog["submitted"] == list(SCENARIOS)


def test_t14_each_scenario_is_its_own_log_and_the_identities_are_unique(tmp_path):
    logs = [_log(tmp_path, scenario_id) for scenario_id in SCENARIOS]
    assert len({log.path for log in logs}) == len({log.record_path for log in logs}) == len({log.item_digest for log in logs}) == 5
    for log in logs:
        assert ftt.SET_ID in log.path.name and log.item["scenario_id"] in log.path.name
    assert _complete(logs[0])["ok"] and all(log.state()["status"] == "NEW" for log in logs[1:])
    assert _log(tmp_path, "TIT-1", reviewer="ref000000002").state()["status"] == "NEW"


def test_t19_a_log_belongs_to_the_set_that_produced_it_another_digest_is_another_log(tmp_path):
    other = "b" * 64
    main_a, main_b = _log(tmp_path), ftt.TitrationReviewLog(tmp_path, "ref000000001", ITEMS["TIT-1"], set_digest=other, audit=LOADED["audit"])
    assert main_a.path != main_b.path and main_a.record_path != main_b.record_path and LOADED["digest"][:12] in main_a.path.name and other[:12] in main_b.path.name
    assert main_a.answer("Q1", "Wrong")["ok"] and main_b.state()["status"] == "NEW" and main_b.state()["blind"] == {}


@pytest.mark.parametrize("field,value", [("overall", "REJECT"), ("overall_comment", "another comment"), ("locked_comment", "another first-pass note"), ("locked_at", "2020-01-01T00:00:00+00:00"),
                                         ("locked_answers", {"Q1": "Wrong", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No"}), ("submitted_prev", "0" * 64), ("record_id", "forged-id")])
def test_t15a_the_record_is_checked_field_by_field_against_the_log_that_closed_it(tmp_path, field, value):
    """White box: each field is held to the log on its own (a record whose identity was recomputed after a change still disagrees with the log)."""
    log = _log(tmp_path, "TIT-2")
    assert _complete(log, overall="ACCEPT", comment="first impression note", overall_comment="overall note")["ok"]
    record, state = json.loads(log.record_path.read_text(encoding="utf-8")), dict(log.state())
    assert ftt.record_problems(record, state, log) == []
    assert ftt.record_problems(record, {**state, field: value}, log), field


@pytest.mark.parametrize("field", ["reviewer_ref", "scenario_id", "set_id", "set_digest", "item_digest"])
def test_t15c_a_record_that_belongs_to_another_reviewer_scenario_set_or_item_is_not_counted_even_when_its_identity_is_recomputed(tmp_path, field):
    log = _log(tmp_path, "TIT-3")
    assert _complete(log)["ok"]
    state, record = log.state(), json.loads(log.record_path.read_text(encoding="utf-8"))
    forged = json.loads(json.dumps(record))
    if field in ("set_digest", "item_digest"):
        forged["linkage"][field] = "f" * 64
    else:
        forged[field] = "TIT-4" if field == "scenario_id" else "other"
    forged["record_id"] = ftr._digest({key: value for key, value in forged.items() if key != "record_id"})[:16]
    problems = ftt.record_problems(forged, {**state, "record_id": forged["record_id"]}, log)
    assert any("another" in problem for problem in problems), (field, problems)


# -- the summary --------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t15_the_summary_counts_only_records_that_verify_and_states_the_limitations_only_when_complete(tmp_path):
    for scenario_id, overall in (("TIT-1", "ACCEPT"), ("TIT-2", "ACCEPT_WITH_LIMITATION"), ("TIT-3", "RECALIBRATE"), ("TIT-4", "ACCEPT_WITH_LIMITATION")):
        assert _complete(_log(tmp_path, scenario_id), overall=overall, overall_comment=f"note {scenario_id}")["ok"]
    summary = _summary(tmp_path)
    assert not summary["complete"] and summary["scenarios_reviewed"] == ["TIT-1", "TIT-2", "TIT-3", "TIT-4"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 2, "RECALIBRATE": 1, "REJECT": 0}
    assert summary["limitations"] == [], "the limitations belong to the completed review only"
    assert "sensitivity" not in summary, "there is no sensitivity check in this review (FD-TITREV-06)"
    assert [comment["text"] for comment in summary["comments"] if comment["stage"] == "overall"] == ["note TIT-1", "note TIT-2", "note TIT-3", "note TIT-4"]
    assert _complete(_log(tmp_path, "TIT-5"), overall="REJECT")["ok"]
    summary = _summary(tmp_path)
    assert summary["complete"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 2, "RECALIBRATE": 1, "REJECT": 1} and summary["technical_problems"] == []
    assert [entry["id"] for entry in summary["limitations"]] == [entry["id"] for entry in LOADED["limitations"]] and len(summary["limitations"]) == 6
    assert [row["overall"] for row in summary["scenarios"]] == ["ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "ACCEPT_WITH_LIMITATION", "REJECT"]
    assert all(sorted(row["first_pass"]) == ["Q1", "Q2", "Q3", "Q4", "Q5"] for row in summary["scenarios"])
    written = ftt.write_summary(tmp_path, summary)
    assert written["written"] and Path(written["path"]).parent.name == ftt.SUBDIR and not (tmp_path / ftr.SUBDIR).exists()
    assert "software has not interpreted" in summary["statement"] and "not a clinical validation" in summary["statement"] and "not a dose-response" in summary["statement"]
    # a record that does not agree with the log that closed it is NOT counted
    altered = _log(tmp_path, "TIT-3")
    record = json.loads(altered.record_path.read_text(encoding="utf-8"))
    record["overall"]["judgment"] = "ACCEPT"
    altered.record_path.write_text(json.dumps(record), encoding="utf-8")
    summary = _summary(tmp_path)
    assert not summary["complete"] and "TIT-3" not in summary["scenarios_reviewed"] and any("TIT-3" in problem for problem in summary["technical_problems"]) and summary["judgments"]["ACCEPT"] == 1
    assert summary["limitations"] == [], "an incomplete review does not state the limitations"


def test_t15b_a_comment_that_looks_like_an_identifier_is_refused_and_a_long_one_too(tmp_path):
    log = _log(tmp_path)
    assert not log.comment("patient MRN 12345678")["ok"] and not log.comment("x" * (ftr.MAX_COMMENT + 1))["ok"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.overall_comment("write to dr.someone@example.com")["ok"] and not log.overall_comment("y" * (ftr.MAX_COMMENT + 1))["ok"]
    assert log.overall_comment("the decay after the stop is gradual")["ok"] and log.state()["overall_comment"] == "the decay after the stop is gradual"


@pytest.mark.parametrize("payload", ["[]", '"x"', "7", '{"linkage": "x"}', '{"overall": [1]}', '{"first_pass": 3, "overall": "x", "linkage": []}', "null", "", "{"])
def test_t22_a_malformed_record_file_is_a_technical_problem_never_an_exception(tmp_path, payload):
    for scenario_id in SCENARIOS:
        assert _complete(_log(tmp_path, scenario_id))["ok"]
    _log(tmp_path, "TIT-3").record_path.write_text(payload, encoding="utf-8")
    summary = _summary(tmp_path)
    assert not summary["complete"] and "TIT-3" not in summary["scenarios_reviewed"] and any("TIT-3" in problem for problem in summary["technical_problems"]) and summary["limitations"] == []
    assert ftt.record_problems(json.loads(payload) if payload.strip() in ("[]", '"x"', "7", "null") else {}, _log(tmp_path, "TIT-3").state(), _log(tmp_path, "TIT-3"))


# -- boundaries ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t16_the_new_modules_import_nothing_of_the_engine_the_authority_the_shadow_or_the_core():
    forbidden = ("runtime_authority", "runtime_shadow", "runtime_tone_support", "runtime_pressure_grant", "clinical_core", "family_engine", "clinical_physiology", "app", "runtime_faculty", "faculty_review_ui",
                 "historical_records", "test_tone_review_analysis", "test_tone_pathway_analysis", "test_tone_titration_analysis", "test_titration_review_analysis", "clinical_cases", "streamlit")
    for name, banned in (("faculty_titration_review.py", forbidden), ("faculty_titration_review_ui.py", forbidden[:-1])):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {str(node.module).split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not imported & set(banned), (name, imported & set(banned))
    launcher = ast.parse((ROOT / "faculty_review_ui.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(launcher) if isinstance(node, ast.Import) for alias in node.names} | {str(node.module) for node in ast.walk(launcher) if isinstance(node, ast.ImportFrom)}
    assert not any("trajectory" in name or "rereview" in name or "tone" in name or "titration" in name for name in imports), imports
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "titration_page=_faculty_titration_ui.draw" in app and "hold_titration=_faculty_titration_ui.other_modes_held" in app and "default_mode=_faculty_review_ui.MANAGEMENT_MODE" in app      # P3-514 (declared adaptation): the landing page after the earlier reviews is now the GI management-trace review
    assert "tone_page=_faculty_tone_ui.draw" in app and "rereview_page=_faculty_rereview_ui.draw" in app and "hold_prior_modes=_faculty_rereview_ui.prior_modes_held" in app


def test_t17_the_earlier_reviews_are_preserved_and_share_no_file_with_this_one(tmp_path):
    assert ftr.PINNED_SET_DIGEST == "f65d1127f3fb97926334d695aeab37b92f3a44236cec2ae025025eec90ba1649" and rr.PINNED_SET_DIGEST == "c30ab7f1fae514ff7e7c4de50e1d11b60f08efc6021804e162b70100d52b344f"
    assert ftm.PINNED_SET_DIGEST == "22ed59069e441aca96939ccf359ceec00a8bd55ddc0b182ff7bbcfcdd6e91487"
    assert rr.load_set()["ok"] and ftm.load_set()["ok"] and ftm.load_set()["digest"] == ftm.PINNED_SET_DIGEST
    first_set = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    assert first_set["record_digest"] == ftr.PINNED_SET_DIGEST
    paths = {ftt.SET_PATH, ftm.SET_PATH, rr.SET_PATH, ftr.SET_PATH}
    assert len(paths) == 4 and len({ftt.SUBDIR, ftm.SUBDIR, rr.SUBDIR, ftr.SUBDIR, ftm.SENSITIVITY_SUBDIR}) == 5 and len({ftt.RECORDS_SUBDIR, ftm.RECORDS_SUBDIR, rr.RECORDS_SUBDIR, ftr.RECORDS_SUBDIR}) == 4
    for earlier in (ftm.SET_ID, rr.SET_ID):
        assert ftt.SET_ID != earlier
    seeds = [tmp_path / name for name in (ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR, ftm.SUBDIR, ftm.RECORDS_SUBDIR, ftm.SENSITIVITY_SUBDIR)]
    for directory in seeds:
        directory.mkdir()
        (directory / "earlier_review_log.jsonl").write_text('{"kept": true}\n', encoding="utf-8")
    before = {directory.name: _tree_digest(directory) for directory in seeds}
    for scenario_id in SCENARIOS:
        assert _complete(_log(tmp_path, scenario_id))["ok"]
    ftt.write_summary(tmp_path, _summary(tmp_path))
    assert {directory.name: _tree_digest(directory) for directory in seeds} == before, "a whole review of this set leaves every earlier review's files untouched"
    created = {path.parent.name for path in tmp_path.rglob("*") if path.is_file() and path.parent.name in (ftt.SUBDIR, ftt.RECORDS_SUBDIR)}
    assert created == {ftt.SUBDIR, ftt.RECORDS_SUBDIR}


def test_t18_the_chart_helper_is_the_reviews_own_and_the_tone_reviews_axis_choice_is_unchanged():
    import inspect
    import faculty_trajectory_review_ui as tui
    signature = inspect.signature(tui.pressure_chart)
    assert signature.parameters["y_max"].default == 140 and signature.parameters["x_title"].default == "Minutes since arrival"
    marked = json.dumps(tui.pressure_chart(ITEMS["TIT-4"]["common"], None, ftt.markers(ITEMS["TIT-4"]), None, y_max=140).to_dict(), ensure_ascii=False)
    for label in ("1 · start 5", "2 · up to 10", "3 · down to 4", "4 · stop"):
        assert label in marked, label
    assert '"domain": [0, 140]' in marked and "legacy" not in marked.lower()
