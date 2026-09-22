"""What the record can and cannot settle, checked before any report says it.

Faculty review of 2026-09-23. The corrections written by hand for one
encounter were three instances of one failure: stating, as something the
resident did or failed to do, something the record does not establish. These
controls run on every encounter so the next one does not need them.
"""
import pytest

import record_findings as findings

TRACE = [
    {"decision_time_min": 0, "response_time_min": 15,
     "interpreted_action": [{"type": "diagnostic", "diagnostic": "lactate"},
                            {"type": "diagnostic", "diagnostic": "troponin"},
                            {"type": "reassessment", "delay_min": 15}],
     "action_summaries": [],
     "state_before": {"observable": {"respiratory_rate": 28, "hr": 118}},
     "state_after": {"observable": {"respiratory_rate": 28, "hr": 111}}},
    {"decision_time_min": 15, "response_time_min": 35,
     "interpreted_action": [],
     "action_summaries": [{"type": "diagnostic", "diagnostic_type": "lactate",
                           "result": {"collected_at_min": 0, "time_min": 20}}],
     "state_before": {"observable": {"respiratory_rate": 28, "hr": 111}},
     "state_after": {"observable": {"respiratory_rate": 28, "hr": 105}}},
    {"decision_time_min": 55, "response_time_min": 60,
     "interpreted_action": [{"type": "diagnostic", "diagnostic": "lactate"}],
     "action_summaries": [{"type": "procedure", "time_min": 55,
                           "label": "Urine is collected and measured from now on; the catheter does not make any."}],
     "state_before": {"observable": {"respiratory_rate": 28, "hr": 105}},
     "state_after": {"observable": {"respiratory_rate": 28, "hr": 105}}},
]


# --- request, sample and report are three moments ---------------------------

def test_a_study_reported_later_is_still_the_first_decision_s_order():
    stages = findings.order_stages(TRACE)
    reported = stages["trace:1"]["reported"][0]
    assert reported["study"] == "lactate"
    assert reported["requested_at_decision"] == 1
    assert reported["requested_here"] is False
    assert stages["trace:1"]["requested"] == []


def test_the_sample_and_the_report_keep_their_own_times():
    reported = findings.order_stages(TRACE)["trace:1"]["reported"][0]
    assert reported["sampled_at_min"] == 0
    assert reported["reported_at_min"] == 20


def test_a_second_request_for_the_same_study_is_its_own_order():
    # The first lactate was answered at decision 2; the one asked for at
    # decision 3 has no report of its own.
    stages = findings.order_stages(TRACE)
    assert stages["trace:2"]["requested"] == ["lactate"]
    assert stages["trace:2"]["awaiting"] == ["lactate"]


def test_a_request_that_was_answered_is_not_awaiting():
    # Lactate was answered; troponin never was, and only troponin waits here.
    assert findings.order_stages(TRACE)["trace:0"]["awaiting"] == ["troponin"]
    assert set(findings.orders_without_result(TRACE)) == {"troponin", "lactate"}


# --- urine: measured, narrated, or absent -----------------------------------

def test_an_engine_sentence_is_a_narrative_and_not_a_measurement():
    evidence = findings.urine_evidence(TRACE)
    assert evidence["kind"] == "narrative" and evidence["at_min"] == 55
    statement = findings.urine_statement(TRACE)
    assert "no urine volume was recorded" in statement
    assert "60 min" in statement


def test_a_measured_volume_is_reported_as_a_measurement_even_when_it_is_zero():
    trace = [dict(TRACE[0]), {**TRACE[1], "state_after": {"observable": {"urine_ml": 0}}}]
    evidence = findings.urine_evidence(trace)
    assert evidence["kind"] == "measured" and evidence["value_ml"] == 0
    assert "0 mL" in findings.urine_statement(trace)


def test_no_evidence_at_all_is_not_turned_into_zero():
    trace = [{"decision_time_min": 0, "response_time_min": 10, "interpreted_action": [],
              "action_summaries": [], "state_before": {}, "state_after": {}}]
    assert findings.urine_evidence(trace)["kind"] == "absent"
    assert findings.urine_statement(trace) == "No urine volume was recorded before the encounter ended at 10 min."


# --- what the record cannot settle ------------------------------------------

def test_the_first_interval_is_the_earliest_anything_can_be_shown():
    assert findings.first_interval(TRACE) == 15


def test_a_descriptor_that_never_moves_is_named():
    assert "respiratory rate" in findings.inert_observables(TRACE)
    assert "heart rate" not in findings.inert_observables(TRACE)


def test_a_timing_claim_that_rests_on_the_first_interval_is_unsettled():
    limits = findings.encounter_limits(TRACE)
    reasons = findings.unsettled(
        "No immediate support was started; support began 15 minutes later.", limits)
    assert reasons and "15 min" in reasons[0]


def test_an_unrelated_claim_is_left_alone():
    limits = findings.encounter_limits(TRACE)
    assert findings.unsettled("The working model was stated explicitly.", limits) == []


def test_a_claim_about_an_order_with_no_result_is_unsettled():
    limits = findings.encounter_limits(TRACE)
    assert findings.unsettled("No repeat lactate was recorded.", limits)


def test_a_claim_about_urine_without_a_measurement_is_unsettled():
    limits = findings.encounter_limits(TRACE)
    assert findings.unsettled("Urine output was not documented.", limits)


# --- holding a suggestion, never overturning it ------------------------------

def test_a_negative_suggestion_the_record_cannot_settle_is_held():
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement",
            "rationale": "Support began 15 minutes later despite hypoxemia."}
    assert findings.hold_for_review(item, limits)
    assert findings.HELD_STATUS == "Requires faculty review"


def test_a_favourable_suggestion_is_never_held():
    limits = findings.encounter_limits(TRACE)
    assert findings.hold_for_review({"recommendation": "satisfactory",
                                     "rationale": "Support began 15 minutes later."}, limits) == []


def test_a_negative_suggestion_on_settled_ground_stands():
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement",
            "rationale": "The working model was never revised after the response."}
    assert findings.hold_for_review(item, limits) == []


def test_holding_does_not_change_the_recommendation():
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement", "rationale": "Support began 15 minutes later."}
    findings.hold_for_review(item, limits)
    assert item["recommendation"] == "needs_improvement"


# --- the same question asked of the evidence, not of the wording -------------

def test_a_judgment_is_held_however_it_is_phrased():
    # Nothing in this sentence trips the textual check; the evidence does.
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement",
            "rationale": "The opening approach could have been stronger.",
            "evidence_refs": ["trace:0"]}
    assert findings.unsettled(item["rationale"], limits) == []
    assert findings.hold_for_review(item, limits)


def test_the_first_interval_reason_needs_the_first_decision_alone():
    limits = findings.encounter_limits(TRACE)
    alone = findings.unsettled_by_evidence(["trace:0"], limits)
    with_later = findings.unsettled_by_evidence(["trace:0", "trace:1"], limits)
    assert any("interval the encounter advances in" in reason for reason in alone)
    assert not any("interval the encounter advances in" in reason for reason in with_later)


def test_a_decision_whose_order_was_never_answered_is_held():
    limits = findings.encounter_limits(TRACE)
    reasons = findings.unsettled_by_evidence(["trace:2"], limits)
    assert reasons and "never answered" in reasons[0]


def test_a_favourable_suggestion_is_not_held_by_the_evidence_rule():
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "satisfactory", "rationale": "Well sequenced.",
            "evidence_refs": ["trace:0"]}
    assert findings.hold_for_review(item, limits) == []


def test_a_claim_with_no_decision_anchor_is_not_held_structurally():
    limits = findings.encounter_limits(TRACE)
    assert findings.unsettled_by_evidence([], limits) == []
    assert findings.unsettled_by_evidence(["reflection:1"], limits) == []


def test_the_two_rules_do_not_report_the_same_reason_twice():
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement",
            "rationale": "Support began 15 minutes later.",
            "evidence_refs": ["trace:0"]}
    reasons = findings.hold_for_review(item, limits)
    assert len(reasons) == len(set(reasons))


def test_the_structural_rule_adds_no_hold_where_the_record_settles_it():
    # A negative judgment anchored on decisions the record does settle stands.
    limits = findings.encounter_limits(TRACE)
    item = {"recommendation": "needs_improvement",
            "rationale": "The working model was never revised.",
            "evidence_refs": ["trace:1"]}
    assert findings.hold_for_review(item, limits) == []
