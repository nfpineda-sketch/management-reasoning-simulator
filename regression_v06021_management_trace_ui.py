from pathlib import Path

text = Path("app.py").read_text()

required = [
    'st.session_state.management_trace = []',
    'def management_state_snapshot',
    'def record_management_trace',
    '"learner_input": learner_input',
    '"interpreted_action": deepcopy(parsed.get("actions", []))',
    '"state_before": deepcopy(state_before)',
    '"state_after": deepcopy(state_after)',
    'with st.expander("Developer: Management Trace", expanded=False):',
    'st.json(st.session_state.management_trace)',
]

missing = [item for item in required if item not in text]
assert not missing, f"Missing Management Trace hooks: {missing}"
print("PASS: Management Trace v1 schema + developer view present")
