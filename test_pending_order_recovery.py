"""Recover a persisted pre-fix held order through the resident UI."""
from copy import deepcopy

from test_curriculum_app import cohort, open_app, click


ORIGINAL = (
    "Reassess blood pressure, heart rate and rhythm, capillary refill, mental status, "
    "oxygen saturation, and work of breathing now. My priority is to establish the "
    "current perfusion and respiratory status. I do not expect reassessment alone "
    "to improve the patient's physiology; I will use the findings to determine my "
    "next management action."
)


def submit(at, text):
    next(w for w in at.text_area if w.label == "Enter your clinical reasoning and/or actions").set_value(text)
    click(at, "Submit")


def test_saved_attempt_recovers_without_treatment_or_evidence_loss(cohort):
    store, _, token = cohort
    at = open_app(token)
    click(at, "Begin Encounter")
    at.session_state.attempt_number = 2
    at.session_state.carry_forward_plan = {"cue": "Reassess perfusion after each action."}
    # Reproduce a saved payload from v0.12.1: the faulty oxygen interpretation
    # remains pending across app deployments; the new parser cannot erase it.
    at.session_state.pending_reasoning = {
        "parsed": {
            "raw_text": ORIGINAL,
            "actions": [
                {"type": "oxygen", "device": None, "flow_lpm": None},
                {"type": "reassessment", "delay_min": 0, "focus": "perfusion"},
            ],
            "reasoning": {
                "management_priority": "establish the current perfusion and respiratory status",
                "expected_effect": "reassessment alone not to improve the patient's physiology",
                "reassessment_target": "blood pressure, heart rate, capillary refill and mental status now",
            },
        },
        "missing": ["working_model"],
        "gate_id": 1,
    }
    at.session_state.reasoning_gate_counter = 1
    at.session_state.events = list(at.session_state.events) + [
        {"kind": "you", "text": ORIGINAL, "time": 0},
        {"kind": "clarification", "text": "ORDER HELD — REASONING REQUIRED", "time": 0},
    ]
    click(at, "Save & return to dashboard")
    record = store.list_attempts(token)[0]
    attempt_id = record["id"]
    before = deepcopy(record["payload"]["session"])

    # New browser/session restores the same attempt and offers cancellation.
    at = open_app(token)
    click(at, "Resume encounter")
    delay = next(w for w in at.number_input if w.label == "I will reassess in… minutes")
    assert delay.value == 0
    click(at, "Cancel held order")
    assert at.session_state["_attempt_id"] == attempt_id
    for key in ("state", "management_trace", "rng_counter", "attempt_number", "carry_forward_plan"):
        assert at.session_state[key] == before[key]
    assert at.session_state.pending_reasoning is None
    assert at.session_state.pending_action is None
    assert at.session_state.pending_bundle is None
    assert not at.session_state.state["treatments"]["oxygen"]
    assert any(e["text"] == ORIGINAL for e in at.session_state.events)
    assert sum(e["kind"] == "order_cancelled" for e in at.session_state.events) == 1
    assert not any("ORDER HELD" in e["text"] for e in at.session_state.events)
    saved = store.get_attempt(token, attempt_id)
    assert saved["status"] == "active"
    assert saved["payload"]["session"]["pending_reasoning"] is None
    at.run()
    assert sum(e["kind"] == "order_cancelled" for e in at.session_state.events) == 1

    submit(at, ORIGINAL)
    assert not at.session_state.pending_reasoning
    assert not at.session_state.state["treatments"]["oxygen"]
    assert at.session_state.state["sim_time"] == 0
    assert len(at.session_state.management_trace) == 1
    assert {a["type"] for a in at.session_state.last_parse["actions"]} == {"reassessment"}
    click(at, "Complete Encounter & Begin Review")
    assert at.session_state.review_prompts
    assert not at.session_state.review_completed
    # Complete the actual review UI; administrative completion still requires
    # every reflection stage, rather than cancelling or merely ending the case.
    for w in at.text_area:
        if str(w.key).startswith("decision_review__"):
            w.set_value("Test reflection: reassessment collected findings without administering treatment.")
    at.run()
    click(at, "Lock Decision Review & Reveal Expert Comparison")
    for w in at.text_area:
        if str(w.key).startswith("expert_comparison__"):
            w.set_value("Test comparison: distinguish collecting observations from treating the patient.")
    click(at, "Continue to Adaptation Plan")
    for w in at.text_area:
        if str(w.key).startswith("adaptation_plan__"):
            w.set_value("Test plan: use observed perfusion to choose and reassess a management action.")
    click(at, "Continue to Final Summary")
    assert at.session_state.review_completed
    # The persisted completed review may render read-only on the next rerun.
    label = "Save & return to dashboard" if any(b.label == "Save & return to dashboard" for b in at.button) else "Return to dashboard"
    click(at, label)
    saved = store.get_attempt(token, attempt_id)
    assert saved["status"] == "completed"
    assert len(store.list_attempts(token)) == 1
    assert saved["payload"]["session"]["attempt_number"] == 2
    assert not saved["payload"]["session"]["state"]["treatments"]["oxygen"]


def test_guided_order_keeps_immediate_reassessment(cohort):
    _, _, token = cohort
    at = open_app(token)
    click(at, "Begin Encounter")
    submit(at, "Start oxygen via nasal cannula at 3 L/min. My priority is to support oxygenation. I expect improved SpO2. Reassess SpO2 and breathing now.")
    assert at.session_state.pending_reasoning
    delay = next(w for w in at.number_input if w.label == "I will reassess in… minutes")
    assert delay.value == 0
    next(w for w in at.text_area if w.label == "My working model is…").set_value("I think reduced oxygenation contributes to the patient's current condition.")
    click(at, "Complete reasoning & execute held order")
    assert not at.session_state.pending_reasoning
    assert at.session_state.state["treatments"]["oxygen_flow_lpm"] == 3
    # Applying oxygen takes one minute in the existing engine; reassessment
    # must add zero further minutes, rather than the old forced five.
    assert at.session_state.state["sim_time"] == 1
    assert next(a for a in at.session_state.last_parse["actions"] if a["type"] == "reassessment")["delay_min"] == 0
    assert len(at.session_state.management_trace) == 1
