"""Regression coverage for the optional, non-executing AI normalization layer."""

import ast
import json
from pathlib import Path
import re

from ai_interpreter import AIInterpretationError, _INSTRUCTIONS, normalize_with_ai


class FakeResponses:
    def __init__(self, payload):
        self.payload = payload
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return type("Response", (), {"output_text": json.dumps(self.payload)})()


class FakeClient:
    def __init__(self, payload):
        self.responses = FakeResponses(payload)


client = FakeClient({
    "canonical_text": "Give diltiazem 5 mg IV and reassess HR in 5 minutes.",
    "confidence": "high",
    "ambiguities": [],
})
result = normalize_with_ai(
    "give dilt 5 iv, check hr in 5",
    {"hr": 162, "rhythm": "AF"},
    api_key="test-only",
    client=client,
)
assert result.canonical_text.startswith("Give diltiazem 5 mg IV")
assert result.confidence == "high"
assert 'exact starter "I expect..."' in _INSTRUCTIONS
assert "Always write canonical_text in English" in _INSTRUCTIONS
assert '"1rio"/"primario" means "primary"' in _INSTRUCTIONS
assert "Do not list a missing optional detail as an" in _INSTRUCTIONS
assert "Preserve each numeric digit string exactly" in _INSTRUCTIONS
assert client.responses.last_request["text"]["format"]["strict"] is True
request_payload = json.loads(client.responses.last_request["input"])
assert request_payload["learner_message"] == "give dilt 5 iv, check hr in 5"
assert request_payload["visible_patient_state_context_only"]["hr"] == 162

# The local numeric guard must protect clinical quantities without mistaking
# Spanish ordinal shorthand ("1rio" = "primary") for a dose or energy value.
app_tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
numeric_node = next(
    node for node in app_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_numeric_tokens"
)
numeric_namespace = {"re": re}
exec(compile(ast.Module(body=[numeric_node], type_ignores=[]), "app.py", "exec"), numeric_namespace)
numeric_tokens = numeric_namespace["_numeric_tokens"]
assert numeric_tokens("problema 1rio; cardioversion 200J; etomidate 8 mg; midazolam 2 mg") == ["200", "8", "2"]
assert numeric_tokens("primary problem; cardioversion 200 J; etomidate 8 mg; midazolam 2 mg") == ["200", "8", "2"]
assert numeric_tokens("1000 cc; reassess in 15 minutes; ceftriaxone 2 g") == ["1000", "15", "2"]
assert numeric_tokens("1,000 cc; reassess in 15 minutes; ceftriaxone 2 g") == ["1000", "15", "2"]

try:
    normalize_with_ai("", {}, api_key="test-only", client=client)
except AIInterpretationError:
    pass
else:
    raise AssertionError("Empty learner input must be rejected")

print("PASS: v0.9.0 AI normalization is structured, conservative, and non-executing")
