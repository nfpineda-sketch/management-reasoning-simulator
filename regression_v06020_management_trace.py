from pathlib import Path
s = Path("app.py").read_text()
# Phase 0 (a6ab3a6, 0A-0B) changed two of these lines, and the behaviour they protect stayed: the record takes
# an optional ``turn`` (the order ledger of the turn) after the same five arguments, and keeps the reader's
# actions with only the ledger's own "_" keys removed (``_untag`` is ``order_ledger.strip_tags``).
# Pre-deployment readiness, B-6, 2026-10-06.
required = [
    "st.session_state.management_trace = []",
    "def management_state_snapshot(state):",
    "def record_management_trace(learner_input, parsed, result, state_before, state_after, turn=None):",
    '"trace_schema": "management_trace_v1"',
    '"learner_input": learner_input',
    '"interpreted_action": [_untag(a) for a in deepcopy(parsed.get("actions", []))]',
    '"state_before": deepcopy(state_before)',
    '"state_after": deepcopy(state_after)',
    '"effective_map": h.get("effective_map")',
    '"forward_flow_state": h.get("forward_flow_state")',
    '"tissue_perfusion": h.get("tissue_perfusion")',
]
for token in required:
    assert token in s, token
assert s.index("trace_state_before = management_state_snapshot") < s.index("result = execute_bundle(parsed)")
assert s.index("result = execute_bundle(parsed)") < s.index("trace_state_after = management_state_snapshot")
print("PASS v0.6.0.20 structured Management Trace regression")
