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
    click(at, "Cancel pending orders")
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
