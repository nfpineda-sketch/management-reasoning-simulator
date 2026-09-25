"""Regenerate the documents, analyse again, or run again: decided from the records.

After the faculty decisions of 2026-09-25 the batch is not repeated
automatically. A new run is for an encounter whose clinical course changes; a
new analysis for one whose saved record the analyses now read differently; and
the rest only regenerate their documents from the saved data.
"""
import json
from copy import deepcopy

import tools_reclassify as tool
from test_assistance_autonomy_and_what_waits_for_the_faculty import cohort, completed  # noqa: F401


def _entry(minute, summaries, *, status="executed", text="Doy salbutamol 5 mg nbz", sbp=120, asked=()):
    return {"execution_status": status, "decision_time_min": minute, "response_time_min": minute + 5,
            "learner_input": text, "action_summaries": summaries,
            "interpreted_action": [{"type": s["type"]} for s in summaries],
            "state_after": {"observable": {"hr": 90, "sbp": sbp, "dbp": 70, "spo2": 97}},
            "reasoning_gate": {"status": "complete", "asked_for": list(asked)}}


def _record(*entries, closed=30, disposition=None, code="abc1234"):
    return {"id": "attempt-1", "revision": 2, "encounter": {"assignment": {"code_version": code}},
            "payload": {"session": {"management_trace": list(entries), "encounter_closed_time_min": closed,
                                    "state": {"disposition": disposition}}}}


SALBUTAMOL = {"type": "bronchodilator", "agent": "salbutamol", "dose_mg": 5, "label": "Salbutamol 5 mg"}


def test_the_same_course_said_differently_is_not_a_new_run():
    before = _record(_entry(0, [SALBUTAMOL]))
    after = deepcopy(before)
    after["payload"]["session"]["management_trace"][0]["action_summaries"][0]["label"] = (
        "Salbutamol 5 mg nebulised (label rewritten)")
    after["id"] = "attempt-2"
    row = tool.classify(before, after, old_reading={"x": 1}, new_reading={"x": 1})
    assert row["class"] == tool.DOCUMENTS and row["trajectory"] == []


def test_a_different_execution_is_a_new_run_and_says_where():
    before = _record(_entry(0, [SALBUTAMOL]), _entry(20, [{"type": "monitoring", "label": "Monitor"}]))
    after = _record(_entry(0, [SALBUTAMOL]),
                    _entry(20, [{"type": "disposition", "destination": "ED observation", "duration_h": 6}]),
                    disposition="ED observation")
    row = tool.classify(before, after)
    assert row["class"] == tool.RERUN
    assert any(line.startswith("decision 2: executed [monitoring] before, [disposition (ED observation)] after")
               for line in row["trajectory"])
    assert "disposition: None before, ED observation after" in row["trajectory"]


def test_a_different_state_or_closing_minute_is_a_new_run():
    before = _record(_entry(0, [SALBUTAMOL], sbp=120))
    assert tool.classify(before, _record(_entry(0, [SALBUTAMOL], sbp=90)))["class"] == tool.RERUN
    assert tool.classify(before, _record(_entry(0, [SALBUTAMOL]), closed=45))["class"] == tool.RERUN


def test_a_question_no_longer_asked_is_reported_and_decides_nothing():
    before = _record(_entry(0, [SALBUTAMOL], asked=("reassessment_target",)))
    after = _record(_entry(0, [SALBUTAMOL]))
    row = tool.classify(before, after, old_reading={"x": 1}, new_reading={"x": 1})
    assert row["class"] == tool.DOCUMENTS
    assert row["interaction"] == ["decision 1: asked for ['reassessment_target'] (complete) before, "
                                  "nothing (complete) after"]


def test_the_same_course_read_differently_is_a_new_analysis_and_names_it():
    before = _record(_entry(0, [SALBUTAMOL]))
    old = {"rubric proposal": {"facts": {"indicated": []}}, "faculty brief": {"a": 1}}
    new = {"rubric proposal": {"facts": {"indicated": [{"category": "antihistamine"}]}}, "faculty brief": {"a": 1}}
    row = tool.classify(before, deepcopy(before), old_reading=old, new_reading=new)
    assert row["class"] == tool.REANALYSE and list(row["analyses"]) == ["rubric proposal"]
    assert row["analyses"]["rubric proposal"] == ["/facts/indicated: 0 items before, 1 after"]


def test_a_rereading_names_the_decisions_the_reader_now_executes_differently():
    record = _record(_entry(20, [{"type": "monitoring"}], text="La dejo en observacion 6 horas"),
                     _entry(30, [SALBUTAMOL]))
    [flag] = tool.reread(record)
    assert flag["decision"] == 1 and flag["recorded"] == ["monitoring"] and flag["now"] == ["disposition"]


def test_records_of_the_same_inputs_are_paired_by_case(monkeypatch):
    monkeypatch.setattr(tool, "case_of", lambda record: record["case"])
    before = [{"case": "a"}, {"case": "b"}]
    after = [{"case": "b", "n": 2}, {"case": "a", "n": 1}]
    assert [(x["case"], y["n"]) for x, y in tool.pair(before, after)] == [("a", 1), ("b", 2)]


def test_what_the_analyses_read_is_computed_by_the_code_named_and_ignores_identity(cohort):
    accounts, users = cohort
    token = users["resident"]["token"]
    record = accounts.get_attempt(token, completed(accounts, token))
    session = record["payload"]["session"]
    session.update(encounter_ended=True, expert_comparison_unlocked=True,
                   encounter_closed_trace=session["management_trace"])
    [here] = tool.readings([record])
    assert set(here) == {"rubric proposal", "faculty brief", "Management Trace analysis"}
    assert not any("unavailable" in reading for reading in (here["rubric proposal"], here["faculty brief"]))
    # The same record under a checkout of this revision, with another identity: the same reading.
    [again] = tool.readings([dict(record, id="attempt-y", revision=record["revision"] + 1)], "HEAD")
    assert json.dumps(here, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_the_table_counts_each_class():
    rows = [{"case": "a", "class": tool.RERUN, "trajectory": ["decision 1: x"], "interaction": []},
            {"case": "b", "class": tool.REANALYSE, "analyses": {"faculty brief": ["/x: 1 -> 2"]}},
            {"case": "c", "class": tool.DOCUMENTS, "analyses": {}}]
    text = tool.as_markdown(rows)
    assert "Volver a ejecutar: 1 · Nuevo análisis: 1 · Sólo documentos: 1" in text


def test_a_detail_only_the_newer_code_records_is_noted_and_not_a_new_run():
    infusion = {"type": "dextrose_infusion", "operation": "start", "label": "Dextrose 10% at 100 mL/h started"}
    before = _record(_entry(0, [infusion]))
    after = _record(_entry(0, [{**infusion, "rate_ml_h": 100.0}]))
    row = tool.classify(before, after, old_reading={}, new_reading={})
    assert row["class"] == tool.DOCUMENTS and row["details"] == ["decision 1: now also records rate_ml_h"]


def test_a_rhythm_strip_drawn_again_is_the_same_study():
    def ecg(seed):
        return {"type": "diagnostic", "diagnostic_type": "ecg",
                "result": {"profile": "st_elevation_inferior", "seed": seed, "recording_id": str(seed)}}
    row = tool.classify(_record(_entry(0, [ecg(1)])), _record(_entry(0, [ecg(2)])), old_reading={}, new_reading={})
    assert row["class"] == tool.DOCUMENTS


def test_an_empty_field_the_newer_code_adds_is_not_a_new_reading():
    assert tool.differences({"a": 1}, {"a": 1, "indicated_not_modelled": [], "urgent_unheld": False}) == []
    assert tool.differences({"a": 1}, {"a": 1, "indicated_not_modelled": [{"x": 1}]}) == [
        '/indicated_not_modelled: added [{"x":1}]']


def test_a_change_in_the_shared_instructions_is_reported_apart_and_decides_nothing():
    before = _record(_entry(0, [SALBUTAMOL]))
    old = {"rubric proposal": {"record_screening_rule": "1.1 wording", "facts": {"a": 1}}}
    new = {"rubric proposal": {"record_screening_rule": "1.2 wording", "facts": {"a": 1}}}
    row = tool.classify(before, deepcopy(before), old_reading=old, new_reading=new)
    assert row["class"] == tool.DOCUMENTS
    assert row["instructions"] == {"rubric proposal": ["record_screening_rule"]}
    assert "record_screening_rule" in tool.as_markdown([row])


def test_the_encounters_can_be_read_from_the_application_s_database(cohort):
    accounts, users = cohort
    completed(accounts, users["resident"]["token"])
    url = "sqlite:///" + str(accounts._path)
    [row] = tool.records_from_database(url, ["resident"])
    assert row["username"] == "resident" and row["status"] == "completed"
    assert tool.records_from_database(url, ["nobody"]) == []
