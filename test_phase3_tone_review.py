"""P3-404 to P3-409 and P3-412 (module level): the MULTIFAMILY TONE REVIEW set, its durable log, its optional sensitivity log and its summary.

What it proves (pure: no Streamlit, no engine):

* the stored set is pinned in code and holds exactly FR-F, SYNTH, ACS, PULM-EDEMA and PE, in that order, all required, with the faculty's own question for each and the exact labels of the synthetic probe;
* a re-signed, edited, extended, reordered or leaking set is refused, even when re-signed AND pinned; the loader never raises;
* what the reviewer is shown carries the clinical picture and the pressure trajectory and NOTHING of the mechanism: no other setting of the response, no parameter, no tone state, no flow, no delivery, no debt, no
  consciousness, no collapse state, no heart rate, no capillary refill, no comparator, no earlier trajectory; the limitations and the other settings leave the loader apart from the items;
* the review log is the blind re-review's (the lock is final, a second submit creates no second record, a forged log is unreadable), in files of its own, and a whole review leaves every earlier review's files untouched;
* the OPTIONAL sensitivity check cannot be reached before every scenario is submitted, offers only the scenarios the pre-declared rule says it should, and the main review is complete without it;
* the summary counts only records that verify against the log that closed them and states the limitations only when the review is complete.
"""
import ast
import hashlib
import json
import re
from pathlib import Path

import pytest

import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr
import historical_records as hr

ROOT = Path(__file__).resolve().parent
LOADED = ftm.load_set()
ITEMS = LOADED["items"]
ANSWERS = {"Q1": "Partly", "Q2": "Too late", "Q3": "Too small", "Q4": "Uncertain", "Q5": "Maybe"}
SCENARIOS = ("FR-F", "SYNTH", "ACS", "PULM-EDEMA", "PE")
#: The faculty's own wording (the assignment of 2026-11-18), copied here on purpose: the builder's text is not the reference of this test.
FACULTY_QUESTION = {
    "FR-F": "Does norepinephrine produce a pressure response with an appropriate direction, timing, and magnitude in this patient with ongoing hemorrhage, without implying that vasopressor support corrects the underlying volume loss?",
    "SYNTH": "Does vascular-tone support move pressure toward a more plausible state without creating flow or volume?",
    "ACS": "Does the pressure response to norepinephrine remain clinically defensible in a patient whose forward flow is limited, without implying that vasoconstriction corrects pump failure?",
    "PULM-EDEMA": "Does norepinephrine produce a pressure response that is directionally plausible without overstating benefit in a congested, pump-limited patient?",
    "PE": "Does norepinephrine produce a plausible pressure response in an obstructive low-flow state without implying correction of the underlying obstruction?"}
ORDER_MINUTE = {"FR-F": 2, "SYNTH": 10, "ACS": 5, "PULM-EDEMA": 5, "PE": 5}
#: What may never be in a reviewer-facing item or view (the first-pass blindness of the assignment).
MECHANISM = re.compile(r"center_reference|witness|legacy|comparator|tone_gain|half[ _-]?effect|onset|offset|parameter|amendment|candidate|kernel|consciousness|cardiac output|oxygen|debt|delivery|sensitivity|"
                       r"tone state|collapse state|heart rate|capillary", re.I)


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for entry in sorted(Path(path).rglob("*")):
        if entry.is_file():
            digest.update(str(entry.relative_to(path)).encode() + b"\0" + entry.read_bytes() + b"\0")
    return digest.hexdigest()


def _log(tmp_path, scenario_id="FR-F", reviewer="ref000000001"):
    return ftm.ToneReviewLog(tmp_path, reviewer, ITEMS[scenario_id], set_digest=LOADED["digest"], audit=LOADED["audit"], account={"role": "faculty"})


def _complete(log, overall="ACCEPT", comment="first impression note", overall_comment="overall note"):
    for question, value in ANSWERS.items():
        assert log.answer(question, value)["ok"]
    assert log.comment(comment)["ok"] and log.lock()["ok"]
    assert log.set_overall(overall)["ok"] and log.overall_comment(overall_comment)["ok"]
    return log.submit()


def _resign(record: dict) -> dict:
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    return {**rest, "record_digest": ftm._seal_digest(rest)}


def _summary(tmp_path, reviewer="ref000000001", ids=None):
    order = ftm.sequence(ITEMS)
    offered = ids if ids is not None else [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    return ftm.summarize(tmp_path, reviewer, ITEMS, order, LOADED["digest"], LOADED["audit"], LOADED["limitations"], offered)


# -- the set ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t1_the_set_verifies_is_pinned_and_holds_exactly_the_five_scenarios_in_order():
    assert LOADED["ok"] and LOADED["problems"] == [] and LOADED["digest"] == ftm.PINNED_SET_DIGEST
    assert list(ITEMS) == list(SCENARIOS) == list(ftm.SCENARIOS)
    assert [entry["scenario_id"] for entry in ftm.sequence(ITEMS)] == list(SCENARIOS) and all(entry["required"] for entry in ftm.sequence(ITEMS))
    assert ftm.SET_ID == "COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW" and ftm.PINNED_SET_DIGEST != "0" * 64
    record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
    assert record["record_digest"] == ftm.PINNED_SET_DIGEST and record["set_id"] == ftm.SET_ID and record["order"] == list(SCENARIOS)
    assert ftm._seal_digest({key: value for key, value in record.items() if key != "record_digest"}) == record["record_digest"] and hr.record_problems(record) == []


def test_t1b_the_loaders_seal_digest_is_the_historical_record_digest():
    for value in ({"a": 1, "b": [1, 2, {"c": "é"}]}, [], "x", {"k": 1.5}):
        assert ftm._seal_digest(value) == hr.digest_of(value)


def test_t2_what_you_are_judging_is_the_question_the_faculty_asked_and_the_probe_is_labelled_as_one():
    for scenario_id in SCENARIOS:
        assert ITEMS[scenario_id]["purpose"] == FACULTY_QUESTION[scenario_id]
        assert ftm.blind_view(ITEMS[scenario_id])["purpose"] == FACULTY_QUESTION[scenario_id]
    probe = ITEMS["SYNTH"]
    assert probe["kind"] == ftm.KIND_PROBE and probe["banner"] == "SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE" and probe["note"] == "This is a synthetic development physiology probe, not a clinical case."
    assert "SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE" in probe["title"]
    assert [ITEMS[scenario_id]["kind"] for scenario_id in SCENARIOS] == [ftm.KIND_CASE, ftm.KIND_PROBE, ftm.KIND_CASE, ftm.KIND_CASE, ftm.KIND_CASE]


def test_t3_every_scenario_states_its_baseline_its_one_intervention_and_a_trajectory_from_that_baseline():
    for scenario_id in SCENARIOS:
        item = ITEMS[scenario_id]
        rows = [row for row in item["timeline"] if row["intervention"]]
        assert len(rows) == 1 and rows[0]["minute"] == ORDER_MINUTE[scenario_id] and "norepinephrine 10 mcg/min" in rows[0]["action"].lower()
        assert item["common"][0]["minute"] == 0 and (item["common"][0]["sbp"], item["common"][0]["dbp"], item["common"][0]["map"]) == (item["arrival"]["sbp"], item["arrival"]["dbp"], item["arrival"]["map"])
        assert item["baseline_facts"] and item["intervention"] and item["table_minutes"][0] == 0 and item["table_minutes"][-1] == item["common"][-1]["minute"]
        assert f"minute {ORDER_MINUTE[scenario_id]}" in item["intervention"]
        # the pressure is the baseline until the order and then moves: the response comes after the order, never before it
        before = [point for point in item["common"] if point["minute"] <= ORDER_MINUTE[scenario_id] and scenario_id != "SYNTH"]
        assert all((point["sbp"], point["dbp"]) == (item["common"][0]["sbp"], item["common"][0]["dbp"]) for point in before[:1])
    assert ITEMS["PULM-EDEMA"]["arrival"]["sbp"] == 218 and ITEMS["SYNTH"]["arrival"] == {"sbp": 120, "dbp": 75, "map": 90, "spo2": None, "rr": None}


def test_t3b_the_hypertensive_scenario_is_not_clipped_by_the_axis_and_the_others_keep_the_usual_one():
    assert ftm.y_axis_max(ITEMS["PULM-EDEMA"]) >= max(point["sbp"] for point in ITEMS["PULM-EDEMA"]["common"]) and ftm.y_axis_max(ITEMS["PULM-EDEMA"]) % 20 == 0
    assert all(ftm.y_axis_max(ITEMS[scenario_id]) == 140 for scenario_id in ("FR-F", "SYNTH", "ACS", "PE"))


def test_t4_the_values_table_is_the_trajectory_at_the_named_minutes_and_nothing_else():
    for scenario_id, item in ITEMS.items():
        table = ftm.values_table(item)
        assert [row["minute"] for row in table] == item["table_minutes"] and all(sorted(row) == ["dbp", "map", "minute", "sbp"] for row in table)
        by_minute = {point["minute"]: point for point in item["common"]}
        assert all(row == {"minute": row["minute"], **{key: int(by_minute[row["minute"]][key]) for key in ("sbp", "dbp", "map")}} for row in table)


def test_t5_the_questions_are_the_five_the_reviews_use_with_the_same_choices_and_no_stop_question():
    for item in ITEMS.values():
        view = ftm.blind_view(item)
        assert [question["id"] for question in view["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"] and view["halted"] is False and view["stop_minute"] is None
        assert [(question["topic"], question["text"], question["choices"]) for question in view["questions"]] == [(q["topic"], q["text"], list(q["choices"])) for q in ftr.FIRST_PASS]


def test_t6_the_first_pass_view_carries_nothing_of_the_mechanism_the_other_settings_or_the_limitations():
    for scenario_id, item in ITEMS.items():
        view = ftm.blind_view(item)
        assert sorted(view) == sorted(["scenario_id", "short", "title", "kind", "banner", "note", "context", "baseline_facts", "purpose", "arrival", "intervention", "timeline", "halted", "stop_minute", "common", "questions"])
        assert sorted(view["arrival"]) == sorted(ftm.ARRIVAL_SHOWN) and "hr" not in view["arrival"] and "crt" not in view["arrival"]
        dumped = json.dumps(view, sort_keys=True)
        assert not MECHANISM.search(dumped) and not ftm._LEAK_NAMES.search(dumped), (scenario_id, MECHANISM.search(dumped))
        assert not re.search(r"COMMON_TONE_PUMP|CONSCIOUSNESS_UNDER|TITRATION_AND_STOP|limitation", dumped, re.I)
    stored = json.dumps(ITEMS, sort_keys=True)
    assert not MECHANISM.search(stored), "nothing of the mechanism is even stored with the items"
    assert all(sorted(row) == ["dbp", "map", "minute", "sbp"] for item in ITEMS.values() for row in ftm.values_table(item))


def test_t7_the_limitations_and_the_other_settings_are_stored_apart_from_the_items():
    assert [entry["id"] for entry in LOADED["limitations"]] == ["COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "TITRATION_AND_STOP_NOT_SUPPORTED"]
    assert "do not support educational promotion" in LOADED["limitations"][0]["text"] and "neither shown nor judged" in LOADED["limitations"][1]["text"]
    assert "Titration" in LOADED["limitations"][2]["text"] and "stopping" in LOADED["limitations"][2]["text"]
    assert not any(key in item for item in ITEMS.values() for key in ("sensitivity", "limitations", "audit", "points", "witnesses"))
    assert set(LOADED["audit"]) >= {"witness", "sources", "selection", "sensitivity_rule"} and LOADED["audit"]["witness"] == "CENTER_REFERENCE"


@pytest.mark.parametrize("name,mutate,expected", [
    ("edited value", lambda r: r["items"][0]["common"][1].update(sbp=99.0), "does not recompute"),
    ("extra scenario", lambda r: r["items"].append(dict(r["items"][0], scenario_id="ACS")), "does not recompute"),
    ("edited limitation", lambda r: r["limitations"][0].update(text="x"), "does not recompute"),
    ("edited sensitivity", lambda r: r["sensitivity"]["scenarios"][0]["points"]["LOW"][3].update(sbp=1.0), "does not recompute"),
])
def test_t8a_an_edited_or_extended_set_is_refused(tmp_path, name, mutate, expected):
    record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = ftm.load_set(path)
    assert not result["ok"] and result["items"] == {} and result["sensitivity"] == [] and result["limitations"] == [] and expected in result["problems"][0], name


def test_t8b_a_re_signed_set_is_refused_until_its_digest_is_pinned_in_code(tmp_path):
    record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
    record["items"][0]["common"][1]["sbp"] = 99.0
    record["items"][0]["common"][1]["map"] = round((99 + 2 * record["items"][0]["common"][1]["dbp"]) / 3)
    path = tmp_path / "set.json"
    path.write_text(json.dumps(_resign(record)), encoding="utf-8")
    result = ftm.load_set(path)
    assert not result["ok"] and "not the pinned one" in result["problems"][0]
    assert ftm.load_set(tmp_path / "missing.json")["ok"] is False and ftm.load_set(tmp_path / "missing.json")["items"] == {}


@pytest.mark.parametrize("mutate,expected", [
    (lambda r: r["items"].reverse(), "exactly its scenarios in order"),
    (lambda r: r["items"].pop(), "exactly its scenarios in order"),
    (lambda r: r["items"][0].update(stopped=True), "draws no stop"),
    (lambda r: r["items"][0]["common"][1].update(map=1.0), "MAP"),
    (lambda r: r["items"][0]["common"][1].update(sbp=89.5), "whole mmHg"),
    (lambda r: r["items"][0]["common"][0].update(sbp=77.0), "baseline pressure"),
    (lambda r: r["items"][0].update(context="the CENTER_REFERENCE configuration"), "carries"),
    (lambda r: r["items"][1].update(purpose="Compare with the legacy engine."), "carries"),
    (lambda r: r["items"][2].update(title="Candidate trajectory"), "carries"),
    (lambda r: r["items"][2].update(context="The LOW setting of the response."), "carries"),
    (lambda r: r["items"][2]["baseline_facts"].append("tone_gain 0.6"), "carries"),
    (lambda r: r["items"][3]["baseline_facts"].append("Consciousness is preserved."), "carries"),
    (lambda r: r["items"][4]["baseline_facts"].append("Sensitivity range 10 to 20."), "carries"),
    (lambda r: r["items"][3]["timeline"][0].pop("executed"), "exactly the stored keys"),
    (lambda r: r["items"][3]["timeline"][0].update(executed="yes"), "marker flags"),
    (lambda r: r["items"][0].update(legacy_comparator=[{"minute": 5, "sbp": 99}]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(heart_rate=[124]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(extra_params={"half_effect": 10}), "exactly the stored keys"),
    (lambda r: r["items"][0]["arrival"].update(hr=124), "exactly the stored keys"),
    (lambda r: r["items"][0]["arrival"].update(crt=5), "exactly the stored keys"),
    (lambda r: r["items"][0]["common"][1].update(note="legacy 112"), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common=["x", "x", "x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(timeline=["x"]), "exactly the stored keys"),
    (lambda r: r["items"][0].update(common="not a list"), "wrong type"),
    (lambda r: r["items"][0].update(baseline_facts=[1]), "wrong type"),
    (lambda r: r["items"][1].update(banner="Synthetic case"), "labelled as one"),
    (lambda r: r["items"][1].update(note="A synthetic probe."), "labelled as one"),
    (lambda r: r["items"][0].update(banner=r["items"][1]["banner"]), "its own label"),
    (lambda r: r["items"][1]["arrival"].update(spo2=97), "no saturation"),
    (lambda r: r["items"][0]["arrival"].update(spo2=None), "states its arrival"),
    (lambda r: r["items"][0].update(kind="OTHER"), "neither an authored case"),
    (lambda r: r["items"][0].update(table_minutes=[0, 3]), "table minutes"),
    (lambda r: r["items"][0].update(table_minutes=[1, 2, 32]), "table minutes"),
    (lambda r: r["items"][0]["timeline"][0].update(minute=999), "not at a minute"),
    (lambda r: r.update(items=[1, 2, 3, 4, 5]), "exactly its scenarios"),
    (lambda r: r.update(items="five"), "exactly its scenarios"),
    (lambda r: r["items"][0].update(title=""), "title is missing"),
    (lambda r: r["items"][0].update(short=""), "short is missing"),
    (lambda r: r["sensitivity"]["scenarios"][0].update(material=False), "pre-declared rule"),
    (lambda r: r["sensitivity"]["scenarios"][0]["points"]["LOW"].pop(), "minutes of the scenario"),
    (lambda r: r["sensitivity"]["scenarios"][0]["points"]["HIGH"][0].update(sbp=99.0, map=69), "same baseline"),
    (lambda r: r["sensitivity"]["scenarios"][0]["points"].update(MID=[]), "exactly the stored keys"),
    (lambda r: r["sensitivity"]["scenarios"][0].update(parameters={"tone_gain": 0.9}), "exactly the stored keys"),
    (lambda r: r["sensitivity"]["scenarios"].pop(), "one entry per scenario"),
    (lambda r: r["limitations"].pop(), "three the review states"),
    (lambda r: r["limitations"].reverse(), "three the review states"),
    (lambda r: r["limitations"][0].update(extra=1), "three the review states"),
])
def test_t8c_a_set_that_leaks_is_not_the_package_or_does_not_hold_is_refused_even_when_re_signed_and_pinned(tmp_path, mutate, expected):
    record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
    mutate(record)
    path = tmp_path / "set.json"
    signed = _resign(record)
    path.write_text(json.dumps(signed), encoding="utf-8")
    result = ftm.load_set(path, expected_digest=signed["record_digest"])
    assert not result["ok"] and result["items"] == {} and result["sensitivity"] == [] and any(expected in problem for problem in result["problems"]), result["problems"]


def test_t8d_the_loader_never_raises_on_a_malformed_set(tmp_path):
    for broken in (None, [], "x", {"record_type": ftm.SET_TYPE}, {"record_type": ftm.SET_TYPE, "set_id": ftm.SET_ID, "items": None}, {"record_type": ftm.SET_TYPE, "set_id": ftm.SET_ID, "items": [], "x": float("nan")}):
        path = tmp_path / "set.json"
        path.write_text(json.dumps(_resign(broken) if isinstance(broken, dict) and "x" not in broken else broken), encoding="utf-8")
        result = ftm.load_set(path, expected_digest=None)
        assert result["ok"] is False and result["items"] == {} and result["problems"], broken
    assert ftm.item_problems(None) and ftm.item_problems("x") and ftm.item_problems({}) and ftm.item_problems({"scenario_id": "FR-F"})


# -- the optional sensitivity check --------------------------------------------------------------------------------------------------------------------------------
def test_t9_the_other_settings_cannot_be_obtained_before_every_scenario_is_submitted(tmp_path):
    with pytest.raises(ftr.Locked):
        ftm.sensitivity_view(LOADED["sensitivity"], ITEMS, {})
    with pytest.raises(ftr.Locked):
        ftm.sensitivity_view(LOADED["sensitivity"], ITEMS, {"required_done": False})
    logs = {scenario_id: _log(tmp_path, scenario_id) for scenario_id in SCENARIOS}
    for scenario_id in SCENARIOS[:-1]:
        assert _complete(logs[scenario_id])["ok"]
        with pytest.raises(ftr.Locked):
            ftm.sensitivity_view(LOADED["sensitivity"], ITEMS, ftm.progress(logs, ftm.sequence(ITEMS)))
    assert _complete(logs["PE"])["ok"]
    offered = ftm.sensitivity_view(LOADED["sensitivity"], ITEMS, ftm.progress(logs, ftm.sequence(ITEMS)))
    assert [entry["scenario_id"] for entry in offered] == [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    for entry in offered:
        assert sorted(entry["witnesses"]) == ["CENTER", "HIGH", "LOW"] and entry["witnesses"]["CENTER"] == ITEMS[entry["scenario_id"]]["common"]
        assert entry["witnesses"]["LOW"][0] == entry["witnesses"]["HIGH"][0] == entry["witnesses"]["CENTER"][0], "every setting starts from the same baseline"
        assert entry["map_range"][0] < min(point["map"] for name in entry["witnesses"] for point in entry["witnesses"][name]) and entry["map_range"][1] > max(point["map"] for name in entry["witnesses"] for point in entry["witnesses"][name])


def test_t9b_a_scenario_whose_settings_barely_differ_is_not_offered_and_the_rule_is_the_predeclared_one():
    assert (ftm.MATERIAL_MAP_SPAN, ftm.MATERIAL_SBP_SPAN) == (10, 15) and LOADED["audit"]["sensitivity_rule"]["map_span_mmhg"] == 10 and LOADED["audit"]["sensitivity_rule"]["sbp_span_mmhg"] == 15
    flat = [{"minute": 0, "sbp": 100, "dbp": 60, "map": 73}, {"minute": 1, "sbp": 101, "dbp": 61, "map": 74}]
    near = [{"minute": 0, "sbp": 100, "dbp": 60, "map": 73}, {"minute": 1, "sbp": 103, "dbp": 62, "map": 76}]
    far = [{"minute": 0, "sbp": 100, "dbp": 60, "map": 73}, {"minute": 1, "sbp": 101, "dbp": 61, "map": 84}]
    tall = [{"minute": 0, "sbp": 100, "dbp": 60, "map": 73}, {"minute": 1, "sbp": 118, "dbp": 61, "map": 75}]
    assert not ftm.is_material(flat, near) and ftm.is_material(flat, far) and ftm.is_material(flat, tall)
    assert all(entry["material"] for entry in LOADED["sensitivity"]), "all five of this set differ materially: nothing was dropped"


def test_t10_the_sensitivity_answers_autosave_refuse_bad_input_survive_a_refresh_and_never_gate_the_review(tmp_path):
    ids = [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    log = ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=LOADED["digest"])
    assert log.state()["status"] == "NEW" and log.state()["answers"] == {}
    assert log.set_envelope("ACS", "BORDERLINE")["ok"] and log.set_envelope("ACS", "NO")["ok"] and log.set_note("ACS", "pump sensitivity wide")["ok"] and log.set_envelope("PE", "YES")["ok"]
    for refused in (log.set_envelope("ACS", "MAYBE"), log.set_envelope("OPIOID", "YES"), log.set_note("OPIOID", "x"), log.set_note("ACS", "patient MRN 12345678"), log.set_note("ACS", "x" * (ftr.MAX_COMMENT + 1)),
                    log.answer("Q1", "Expected"), log.comment("x"), log.lock(), log.set_overall("ACCEPT"), log.submit()):
        assert not refused["ok"]
    again = ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=LOADED["digest"])
    assert again.state()["answers"] == {"ACS": "NO", "PE": "YES"} and again.state()["comments"] == {"ACS": "pump sensitivity wide"}
    assert ftm.SensitivityLog(tmp_path, "ref000000002", ids, set_digest=LOADED["digest"]).state()["status"] == "NEW"
    assert log.path.parent.parent.name == ftm.SENSITIVITY_SUBDIR != ftm.SUBDIR and not (tmp_path / ftm.SUBDIR).exists() and not (tmp_path / ftm.RECORDS_SUBDIR).exists()
    # an altered log is unreadable and nothing more is written
    lines = log.path.read_text(encoding="utf-8").split("\n")
    log.path.write_text(lines[0].replace("BORDERLINE", "YES") + "\n" + "\n".join(lines[1:]), encoding="utf-8")
    broken = ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=LOADED["digest"])
    assert broken.state()["status"] == "UNREADABLE" and not broken.set_envelope("DOES", "YES")["ok"] and not broken.set_envelope("ACS", "YES")["ok"]


# -- the durable log ---------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t11_the_whole_review_of_one_scenario_writes_one_verified_record(tmp_path):
    log = _log(tmp_path)
    assert log.state()["status"] == "NEW"
    outcome = _complete(log, overall="ACCEPT_WITH_LIMITATION")
    assert outcome["ok"] and outcome["record_id"] and Path(outcome["path"]) == log.record_path
    state = log.state()
    assert state["status"] == "SUBMITTED" and state["locked"] and state["overall"] == "ACCEPT_WITH_LIMITATION" and state["overall_comment"] == "overall note"
    record = json.loads(log.record_path.read_text(encoding="utf-8"))
    assert record["record_type"] == ftm.RECORD_TYPE and record["set_id"] == ftm.SET_ID and record["comparator_shown"] is False and record["scenario_id"] == "FR-F"
    assert record["first_pass"]["answers"] == ANSWERS == record["first_pass"]["answers_at_lock"] and record["first_pass"]["comment"] == "first impression note"
    assert record["overall"] == {"judgment": "ACCEPT_WITH_LIMITATION", "comment": "overall note"} and "post_reveal" not in record
    assert record["linkage"]["witness"] == "CENTER_REFERENCE" and record["linkage"]["set_digest"] == ftm.PINNED_SET_DIGEST
    assert record["linkage"]["source_record_id"] == "FR-F_TONE_V1_CANDIDATE" and len(record["linkage"]["source_record_digest"]) == 64
    assert ftm.record_problems(record, state, log) == [] and record["reviewer_ref"] == "ref000000001" and record["reviewer_role"] == "faculty"
    assert Path(outcome["path"]).parent.name == ftm.RECORDS_SUBDIR and log.path.parent.parent.name == ftm.SUBDIR


def test_t11b_the_first_impression_locks_and_can_never_change(tmp_path):
    log = _log(tmp_path, "ACS")
    assert not log.lock()["ok"] and "answer Q1" in log.lock()["why"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.set_overall("ACCEPT")["ok"] and not log.overall_comment("x")["ok"], "the overall judgment waits for the lock"
    assert log.lock()["ok"] and not log.lock()["ok"]
    for refused in (log.answer("Q1", "Wrong"), log.comment("changed my mind"), log.answer("Q5", "Yes")):
        assert not refused["ok"] and "locked" in refused["why"]
    assert log.state()["locked_answers"] == ANSWERS
    forged = {"seq": log.state()["events"] + 1, "prev": log.state()["head"], "kind": "blind", "at": "2026-11-18T00:00:00+00:00", "data": {"id": "Q1", "value": "Wrong"}}
    with open(log.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    assert log.state()["blind"]["Q1"] == ANSWERS["Q1"] and log.state()["locked_answers"] == ANSWERS and log.state()["status"] == "LOCKED"


def test_t11c_there_is_no_comparator_step_no_stop_question_and_the_submit_needs_only_the_overall_judgment(tmp_path):
    log = _log(tmp_path, "PE")
    for question, value in ANSWERS.items():
        log.answer(question, value)
    assert not log.answer("R1", "No")["ok"] and not log.comment("x", after_reveal=True)["ok"] and not log.answer("Q5H", "Understandable")["ok"]
    assert not log.submit()["ok"]
    log.lock()
    assert not log.submit()["ok"] and "overall" in log.submit()["why"]
    log.set_overall("REJECT")
    assert log.submit()["ok"] and not log.set_overall("ACCEPT")["ok"] and log.state()["overall"] == "REJECT"


def test_t11d_a_second_submit_creates_no_second_record_and_a_forged_closed_log_is_unreadable(tmp_path):
    log = _log(tmp_path, "PULM-EDEMA")
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.set_overall("MAYBE")["ok"]
    log.set_overall("RECALIBRATE")
    first, second = log.submit(), log.submit()
    assert first["ok"] and not second["ok"] and second["why"] == "already submitted" and second["record_id"] == first["record_id"]
    assert len(list(log.records.glob("*.json"))) == 1 and not list(log.records.glob("*.superseded-*"))
    other = _log(tmp_path, "ACS")
    for question, value in ANSWERS.items():
        other.answer(question, value)
    other.lock()
    forged = {"seq": other.state()["events"] + 1, "prev": other.state()["head"], "kind": "submitted", "at": "2026-11-18T00:00:00+00:00", "data": {"record_id": "forged"}}
    with open(other.path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({**forged, "hash": ftr._digest(forged)}, sort_keys=True, separators=(",", ":")) + "\n")
    broken = _log(tmp_path, "ACS")
    assert broken.state()["status"] == "UNREADABLE" and "overall" in broken.state()["why"] and not broken.set_overall("ACCEPT")["ok"] and not broken.submit()["ok"]


def test_t12_a_refresh_restores_everything_and_a_corrupt_log_refuses_writes(tmp_path):
    log = _log(tmp_path, "SYNTH")
    log.answer("Q1", "Wrong"); log.answer("Q2", "Too late"); log.comment("partial note")
    again = _log(tmp_path, "SYNTH")
    assert again.state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"} and again.state()["blind_comment"] == "partial note" and again.state()["status"] == "IN_PROGRESS"
    with open(log.path, "ab") as handle:
        handle.write(b'{"seq": 4, "prev": "x"')
    assert _log(tmp_path, "SYNTH").state()["blind"] == {"Q1": "Wrong", "Q2": "Too late"}
    lines = log.path.read_text(encoding="utf-8").split("\n")
    log.path.write_text(lines[0].replace("Wrong", "Expected") + "\n" + "\n".join(lines[1:]), encoding="utf-8")
    broken = _log(tmp_path, "SYNTH")
    assert broken.state()["status"] == "UNREADABLE" and not broken.answer("Q3", "Plausible")["ok"]


def test_t13_the_review_advances_scenario_by_scenario_in_order_and_is_complete_after_the_fifth(tmp_path):
    logs = {scenario_id: _log(tmp_path, scenario_id) for scenario_id in SCENARIOS}
    order = ftm.sequence(ITEMS)
    for position, scenario_id in enumerate(SCENARIOS):
        prog = ftm.progress(logs, order)
        assert prog["current"] == scenario_id and prog["enterable"] == set(SCENARIOS[:position]) | {scenario_id} and not prog["required_done"]
        assert prog["remaining_required"] == 5 - position and prog["estimated_minutes_left"] == ftr.MINUTES_PER_SCENARIO * (5 - position)
        assert _complete(logs[scenario_id])["ok"]
    prog = ftm.progress(logs, order)
    assert prog["current"] is None and prog["required_done"] and prog["all_done"] and prog["submitted"] == list(SCENARIOS)


def test_t14_each_scenario_is_its_own_log_and_the_identities_are_unique(tmp_path):
    logs = [_log(tmp_path, scenario_id) for scenario_id in SCENARIOS]
    assert len({log.path for log in logs}) == len({log.record_path for log in logs}) == len({log.item_digest for log in logs}) == 5
    for log in logs:
        assert ftm.SET_ID in log.path.name and log.item["scenario_id"] in log.path.name
    assert _complete(logs[0])["ok"] and all(log.state()["status"] == "NEW" for log in logs[1:])
    assert _log(tmp_path, "FR-F", reviewer="ref000000002").state()["status"] == "NEW"


# -- the summary --------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t15_the_summary_counts_only_records_that_verify_states_the_limitations_only_when_complete_and_needs_no_sensitivity(tmp_path):
    for scenario_id, overall in (("FR-F", "ACCEPT"), ("SYNTH", "ACCEPT_WITH_LIMITATION"), ("ACS", "RECALIBRATE"), ("PULM-EDEMA", "ACCEPT_WITH_LIMITATION")):
        assert _complete(_log(tmp_path, scenario_id), overall=overall, overall_comment=f"note {scenario_id}")["ok"]
    summary = _summary(tmp_path)
    assert not summary["complete"] and summary["scenarios_reviewed"] == ["FR-F", "SYNTH", "ACS", "PULM-EDEMA"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 2, "RECALIBRATE": 1, "REJECT": 0}
    assert summary["limitations"] == [] and summary["sensitivity"] == [], "the limitations belong to the completed review only"
    assert [comment["text"] for comment in summary["comments"] if comment["stage"] == "overall"] == ["note FR-F", "note SYNTH", "note ACS", "note PULM-EDEMA"]
    assert _complete(_log(tmp_path, "PE"), overall="REJECT")["ok"]
    summary = _summary(tmp_path)
    assert summary["complete"] and summary["judgments"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 2, "RECALIBRATE": 1, "REJECT": 1} and summary["technical_problems"] == []
    assert [entry["id"] for entry in summary["limitations"]] == [entry["id"] for entry in LOADED["limitations"]]
    assert all(row["answer"] is None for row in summary["sensitivity"]), "an unanswered optional check does not block or change the summary"
    assert [row["overall"] for row in summary["scenarios"]] == ["ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "ACCEPT_WITH_LIMITATION", "REJECT"]
    assert all(sorted(row["first_pass"]) == ["Q1", "Q2", "Q3", "Q4", "Q5"] for row in summary["scenarios"])
    written = ftm.write_summary(tmp_path, summary)
    assert written["written"] and Path(written["path"]).parent.name == ftm.SUBDIR and not (tmp_path / ftr.SUBDIR).exists()
    assert "software has not interpreted" in summary["statement"] and "not a clinical validation" in summary["statement"]
    # the optional answers appear, when they exist
    ids = [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    sens = ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=LOADED["digest"])
    sens.set_envelope("ACS", "NO"); sens.set_note("ACS", "pump coupling too strong")
    shown = {row["scenario_id"]: row for row in _summary(tmp_path)["sensitivity"]}
    assert shown["ACS"] == {"scenario_id": "ACS", "answer": "NO", "comment": "pump coupling too strong"} and shown["PE"]["answer"] is None
    # a record that does not agree with the log that closed it is NOT counted
    altered = _log(tmp_path, "ACS")
    record = json.loads(altered.record_path.read_text(encoding="utf-8"))
    record["overall"]["judgment"] = "ACCEPT"
    altered.record_path.write_text(json.dumps(record), encoding="utf-8")
    summary = _summary(tmp_path)
    assert not summary["complete"] and "ACS" not in summary["scenarios_reviewed"] and any("ACS" in problem for problem in summary["technical_problems"]) and summary["judgments"]["ACCEPT"] == 1
    assert summary["limitations"] == [], "an incomplete review does not state the limitations"


def test_t15b_a_comment_that_looks_like_an_identifier_is_refused_and_a_long_one_too(tmp_path):
    log = _log(tmp_path)
    assert not log.comment("patient MRN 12345678")["ok"] and not log.comment("x" * (ftr.MAX_COMMENT + 1))["ok"]
    for question, value in ANSWERS.items():
        log.answer(question, value)
    log.lock()
    assert not log.overall_comment("write to dr.someone@example.com")["ok"] and not log.overall_comment("y" * (ftr.MAX_COMMENT + 1))["ok"]
    assert log.overall_comment("MAP about 65 to 75 mmHg")["ok"] and log.state()["overall_comment"] == "MAP about 65 to 75 mmHg"


# -- boundaries ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_t16_the_new_modules_import_nothing_of_the_engine_the_authority_the_shadow_or_the_core():
    forbidden = ("runtime_authority", "runtime_shadow", "runtime_pressure_grant", "clinical_core", "family_engine", "clinical_physiology", "app", "runtime_faculty", "faculty_review_ui", "historical_records",
                 "test_tone_review_analysis", "test_tone_pathway_analysis", "clinical_cases", "streamlit")
    for name, banned in (("faculty_tone_review.py", forbidden), ("faculty_tone_review_ui.py", forbidden[:-1])):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {str(node.module).split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not imported & set(banned), (name, imported & set(banned))
    launcher = ast.parse((ROOT / "faculty_review_ui.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(launcher) if isinstance(node, ast.Import) for alias in node.names} | {str(node.module) for node in ast.walk(launcher) if isinstance(node, ast.ImportFrom)}
    assert not any("trajectory" in name or "rereview" in name or "tone" in name for name in imports), imports
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "tone_page=_faculty_tone_ui.draw" in app and "default_mode=_faculty_review_ui.MANAGEMENT_MODE" in app and "rereview_page=_faculty_rereview_ui.draw" in app and "hold_prior_modes=_faculty_rereview_ui.prior_modes_held" in app      # P3-514 (declared adaptation): the landing page after the earlier reviews is now the GI management-trace review


def test_t17_the_earlier_reviews_are_preserved_and_share_no_file_with_this_one(tmp_path):
    assert ftr.PINNED_SET_DIGEST == "f65d1127f3fb97926334d695aeab37b92f3a44236cec2ae025025eec90ba1649" and rr.PINNED_SET_DIGEST == "c30ab7f1fae514ff7e7c4de50e1d11b60f08efc6021804e162b70100d52b344f"
    assert rr.load_set()["ok"] and rr.load_set()["digest"] == rr.PINNED_SET_DIGEST
    first_set = json.loads(ftr.SET_PATH.read_text(encoding="utf-8"))
    assert first_set["record_digest"] == ftr.PINNED_SET_DIGEST
    human = json.loads((ROOT / "docs" / "revision" / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json").read_text(encoding="utf-8"))
    assert human["record_digest"] == "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3" and ftr._digest({key: value for key, value in human.items() if key != "record_digest"}) == human["record_digest"]
    assert len({ftm.SET_PATH, rr.SET_PATH, ftr.SET_PATH}) == 3 and len({ftm.SUBDIR, rr.SUBDIR, ftr.SUBDIR, ftm.SENSITIVITY_SUBDIR}) == 4 and len({ftm.RECORDS_SUBDIR, rr.RECORDS_SUBDIR, ftr.RECORDS_SUBDIR}) == 3
    seeds = [tmp_path / name for name in (ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR)]
    for directory in seeds:
        directory.mkdir(parents=True)
        (directory / "seed.json").write_text('{"kept": true}', encoding="utf-8")
    before = [_tree_digest(directory) for directory in seeds]
    for scenario_id in SCENARIOS:
        log = _log(tmp_path, scenario_id)
        assert _complete(log)["ok"] and not any(directory in log.path.parents or directory in log.record_path.parents for directory in seeds)
    assert [_tree_digest(directory) for directory in seeds] == before
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted([ftr.SUBDIR, ftr.RECORDS_SUBDIR, rr.SUBDIR, rr.RECORDS_SUBDIR, ftm.SUBDIR, ftm.RECORDS_SUBDIR])
    assert ftr.ReviewLog.SUBDIR_NAME == ftr.SUBDIR and rr.ReReviewLog.SUBDIR_NAME == rr.SUBDIR and rr.ReReviewLog.RECORDS_NAME == rr.RECORDS_SUBDIR


def test_t18_the_only_chart_helper_change_keeps_every_earlier_review_axis():
    import inspect
    import faculty_trajectory_review_ui as tui
    signature = inspect.signature(tui.pressure_chart)
    assert signature.parameters["y_max"].default == 140 and signature.parameters["x_title"].default == "Minutes since arrival"
    sample = [{"minute": 0, "sbp": 100.0, "dbp": 60.0, "map": 73.0}, {"minute": 5, "sbp": 110.0, "dbp": 65.0, "map": 80.0}]
    default = json.dumps(tui.pressure_chart(sample, None, [], None).to_dict())
    assert '"domain": [0, 140]' in default and "Minutes since arrival" in default and "[0, 280]" not in default
    wide = json.dumps(tui.pressure_chart(sample, None, [], None, y_max=280, x_title="Minutes").to_dict())
    assert '"domain": [0, 280]' in wide and '"title": "Minutes"' in wide and "[0, 140]" not in wide


# -- the findings of the independent adversarial review ----------------------------------------------------------------------------------------------------------------------------
def test_t19_a_log_belongs_to_the_set_that_produced_it_another_digest_is_another_log(tmp_path):
    other = "b" * 64
    main_a, main_b = _log(tmp_path), ftm.ToneReviewLog(tmp_path, "ref000000001", ITEMS["FR-F"], set_digest=other, audit=LOADED["audit"])
    assert main_a.path != main_b.path and main_a.record_path != main_b.record_path and LOADED["digest"][:12] in main_a.path.name and other[:12] in main_b.path.name
    assert main_a.answer("Q1", "Wrong")["ok"] and main_b.state()["status"] == "NEW" and main_b.state()["blind"] == {}
    ids = [entry["scenario_id"] for entry in LOADED["sensitivity"] if entry["material"]]
    sens_a, sens_b = ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=LOADED["digest"]), ftm.SensitivityLog(tmp_path, "ref000000001", ids, set_digest=other)
    assert sens_a.path != sens_b.path and sens_a.set_envelope("ACS", "YES")["ok"] and sens_b.state()["answers"] == {}


def test_t20_the_loader_never_raises_even_for_a_re_signed_and_pinned_set_with_a_malformed_section(tmp_path):
    for name, mutate in (("sensitivity list", lambda r: r.update(sensitivity=[1, 2])), ("sensitivity text", lambda r: r.update(sensitivity="abc")), ("audit list", lambda r: r.update(audit=[1])),
                         ("audit text", lambda r: r.update(audit="x")), ("sensitivity entries", lambda r: r["sensitivity"].update(scenarios=[None] * 5)), ("limitations text", lambda r: r.update(limitations="x")),
                         ("sensitivity missing", lambda r: r.pop("sensitivity")), ("audit missing", lambda r: r.pop("audit"))):
        record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
        mutate(record)
        signed = _resign(record)
        path = tmp_path / "set.json"
        path.write_text(json.dumps(signed), encoding="utf-8")
        result = ftm.load_set(path, expected_digest=signed["record_digest"])
        assert result["ok"] is False and result["items"] == {} and result["problems"], name


@pytest.mark.parametrize("text", ["Heart rate 128/min", "Capillary refill 4 s", "HR 128", "CRT 5 s", "Lactate 6.1 mmol/L", "Mental status: drowsy", "Cardiac index is low", "The tone state is high", "Collapse state: soft",
                                  "Oxygen delivery falls", "Consciousness is preserved"])
def test_t21_the_text_forms_of_what_the_faculty_forbade_are_refused_even_when_re_signed_and_pinned(tmp_path, text):
    for field in ("baseline_facts", "context"):
        record = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
        if field == "context":
            record["items"][0]["context"] += " " + text
        else:
            record["items"][0]["baseline_facts"].append(text)
        signed = _resign(record)
        path = tmp_path / "set.json"
        path.write_text(json.dumps(signed), encoding="utf-8")
        result = ftm.load_set(path, expected_digest=signed["record_digest"])
        assert not result["ok"] and any("carries" in problem for problem in result["problems"]), (field, text)


@pytest.mark.parametrize("payload", ["[]", '"x"', "7", '{"linkage": "x"}', '{"overall": [1]}', '{"first_pass": 3, "overall": "x", "linkage": []}', "null", "", "{"])
def test_t22_a_malformed_record_file_is_a_technical_problem_never_an_exception(tmp_path, payload):
    for scenario_id in SCENARIOS:
        assert _complete(_log(tmp_path, scenario_id))["ok"]
    _log(tmp_path, "ACS").record_path.write_text(payload, encoding="utf-8")
    summary = _summary(tmp_path)
    assert not summary["complete"] and "ACS" not in summary["scenarios_reviewed"] and any("ACS" in problem for problem in summary["technical_problems"]) and summary["limitations"] == []
    assert ftm.record_problems(json.loads(payload) if payload.strip() in ("[]", '"x"', "7", "null") else {}, _log(tmp_path, "ACS").state(), _log(tmp_path, "ACS"))
