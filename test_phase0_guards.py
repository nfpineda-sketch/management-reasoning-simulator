"""Phase 0 (0I): the record never settles against the resident what a limitation decided.

Pre-pilot measurement safety, 2026-10-06. The screening reads the frozen trace and states which
conditions of each critical event the record settles; the proposal and the faculty read it. With
the order ledger (0A), the course's events (0H) and the arrest (0G), it can now tell an order
never written from one the simulator did not carry out, a delay of the resident's from one of
the simulator's, and a scripted event from a preventable one. Rules A-E of the Phase 0 request;
no score, weight or definition changes.
"""
import rubric_screening as screening


def _entry(minute, *, status="executed", summaries=(), orders=(), events=(), limitations=(), response=None):
    return {"execution_status": status, "decision_time_min": minute,
            "response_time_min": minute if response is None else response, "learner_input": "",
            "interpreted_action": [], "action_summaries": list(summaries), "orders": list(orders),
            "events": list(events), "limitations": list(limitations), "observation_snapshot": {}}


def _order(order_id, klass, fate, written, executed=None, span="", **extra):
    return {"order_id": order_id, "class": klass, "fate": fate, "written_at_min": written,
            "executed_at_min": executed, "span": span, "canonical": klass, **extra}


def _record(*entries):
    return {"payload": {"session": {"management_trace": list(entries)}}}


def _row(record, case_id, event_id):
    return {row["event_id"]: row for row in screening.screen_events(record, case_id)}[event_id]


FLUID = {"type": "fluid", "label": "Lactated Ringer's 1000 mL", "time_min": 0}


def test_rule_a_an_order_the_reader_did_not_understand_is_not_an_omission():
    # "Give 1 L LR, cefepime 2 g": the fluid ran, the antibiotic was written and not understood.
    record = _record(_entry(0, summaries=[FLUID], orders=[
        _order("s:0", "fluid", "EXECUTED", 0, 0, "1 L LR"),
        _order("s:1000", "unrecognized", "UNRECOGNIZED", 0, span="cefepime 2 g")]), _entry(70, response=70))
    row = _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")
    assert row["status"] == "reading", row
    text = " ".join(fact["en"] for fact in row["facts"])
    assert "not understood by the simulator's reader" in text


def test_rule_a_without_any_such_order_the_omission_stands():
    record = _record(_entry(0, summaries=[FLUID], orders=[_order("s:0", "fluid", "EXECUTED", 0, 0)]),
                     _entry(70, response=70))
    assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "met"


def test_rule_a_an_order_the_resident_cancelled_is_an_omission():
    record = _record(_entry(0, summaries=[FLUID], orders=[
        _order("s:0", "fluid", "EXECUTED", 0, 0), _order("s:1", "antibiotics", "CANCELLED", 0)]),
        _entry(70, response=70))
    assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "met"


def test_rule_a_an_order_held_or_recorded_is_not_an_omission():
    for fate in ("HELD_CLARIFICATION", "HELD_REASONING", "RECORDED_NOT_MODELLED", "TERMINAL_NOT_EXECUTABLE"):
        record = _record(_entry(0, summaries=[FLUID], orders=[
            _order("s:0", "fluid", "EXECUTED", 0, 0), _order("s:1", "antibiotics", fate, 5)]),
            _entry(70, response=70))
        assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "reading", fate


def test_rule_a_an_order_for_later_is_read_by_the_kinds_it_names():
    plan = _order("s:p2000", "plan", "RECORDED_NOT_MODELLED", 10, span="give ceftriaxone in 30 minutes",
                  planned_types=["antibiotics"], limitation="unsupported_future_execution")
    record = _record(_entry(10, summaries=[FLUID], orders=[_order("s:0", "fluid", "EXECUTED", 10, 10), plan]),
                     _entry(70, response=70))
    assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "reading"


def test_rule_b_an_order_written_in_time_and_run_late_by_the_simulator_is_not_a_delay():
    # Blood written at minute 5, held for a clarification, executed at minute 45 (window 0-40).
    record = _record(
        _entry(5, status="clarification_required", orders=[_order("s:0", "blood", "HELD_CLARIFICATION", 5)]),
        _entry(45, summaries=[{"type": "blood", "label": "Packed red cells 2 units", "time_min": 45}],
               orders=[_order("s:0", "blood", "EXECUTED", 5, 45)]))
    row = _row(record, "gi_bleed_57m", "gi_no_resuscitation")
    assert row["status"] == "reading", row
    assert "executed later" in " ".join(fact["en"] for fact in row["facts"])


def test_rule_d_a_scripted_unpreventable_event_never_supports_negative_feedback():
    block = {"kind": "av_block", "label": "complete atrioventricular block", "minute": 45,
             "cause_class": "SCRIPTED_NATURAL_HISTORY", "preventability": "NOT_PREVENTABLE_IN_SIMULATOR",
             "severity": "critical", "terminal": False}
    fibrillation = {"kind": "ventricular_fibrillation", "label": "ventricular fibrillation", "minute": 120,
                    "cause_class": "SCRIPTED_NATURAL_HISTORY", "preventability": "PREVENTABLE",
                    "severity": "terminal", "terminal": True}
    record = _record(_entry(0, events=[block]), _entry(45, events=[fibrillation], response=120))
    sent = screening.for_model(screening.screening(record, "acs_54m_inferior"))
    marks = {row["kind"]: row["may_support_negative_feedback"] for row in sent["course_events"]}
    # Neither: a scripted course is the simulator's clock, preventable or not (Phase 0, 0J). Whether
    # the reperfusion came in time is read from the decision, not from the scripted minute.
    assert marks == {"av_block": False, "ventricular_fibrillation": False}
    assert sent["nothing_assessable_after_min"] == 120


def test_rule_d_a_preventable_natural_event_can_support_negative_feedback_unless_an_order_was_not_carried_out():
    arrest = {"kind": "cardiac_arrest", "label": "cardiac arrest", "minute": 20, "cause_class": "NATURAL_DISEASE",
              "preventability": "PREVENTABLE", "severity": "terminal", "terminal": True}
    plain = _record(_entry(0, events=[arrest], response=20))
    [row] = screening.screening(plain, "opioid_35m")["course_events"]
    assert row["may_support_negative_feedback"] is True
    # The naloxone the reader did not understand, written before the arrest: not the resident's to answer for.
    unread = _record(_entry(5, orders=[_order("s:1000", "unrecognized", "UNRECOGNIZED", 5, span="narcan 0.4")],
                            events=[arrest], response=20))
    [row] = screening.screening(unread, "opioid_35m")["course_events"]
    assert row["may_support_negative_feedback"] is False


def test_rule_d_an_order_held_for_its_reasoning_and_never_answered_is_read_from_the_encounter_ledger():
    # The held turn writes no Trace entry; the encounter's ledger keeps the order (Phase 0, 0J).
    held = _order("s:0", "antibiotics", "HELD_REASONING", 5, span="ceftriaxone 2 g IV")
    record = _record(_entry(0, summaries=[FLUID], orders=[_order("f:0", "fluid", "EXECUTED", 0, 0)]),
                     _entry(70, response=70))
    record["payload"]["session"]["order_ledger"] = [held]
    assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "reading"


def test_rule_e_nothing_after_an_unmodelled_arrest_is_assessable():
    arrest = {"kind": "cardiac_arrest", "label": "cardiac arrest", "minute": 20, "cause_class": "NATURAL_DISEASE",
              "preventability": "PREVENTABLE", "severity": "terminal", "terminal": True}
    # The opioid patient arrests at minute 20; the antibiotic window of another case would run on.
    record = _record(_entry(0, events=[arrest], response=20, summaries=[FLUID]), _entry(20, status="terminal_locked"))
    row = _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")
    assert row["status"] == "reading" and row["not_assessable"] == ["resuscitation_not_modelled"]


def test_rule_e_an_engine_inconsistency_in_the_window_makes_the_event_not_assessable():
    record = _record(_entry(0, summaries=[FLUID], limitations=[{"kind": "engine_inconsistency", "detail": "x"}]),
                     _entry(70, response=70))
    row = _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")
    assert row["status"] == "reading" and "engine_inconsistency" in row["not_assessable"]


def test_a_record_from_before_phase_0_is_read_as_before():
    # No orders, events or limitations recorded: the guards add nothing.
    old = {"execution_status": "executed", "decision_time_min": 0, "response_time_min": 0, "learner_input": "",
           "interpreted_action": [], "action_summaries": [FLUID]}
    record = _record(old, {**old, "decision_time_min": 70, "response_time_min": 70, "action_summaries": []})
    assert _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"] == "met"
