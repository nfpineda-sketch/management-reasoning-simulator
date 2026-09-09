"""Regression coverage for the optional, non-executing AI normalization layer."""

import json

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
assert client.responses.last_request["text"]["format"]["strict"] is True
request_payload = json.loads(client.responses.last_request["input"])
assert request_payload["learner_message"] == "give dilt 5 iv, check hr in 5"
assert request_payload["visible_patient_state_context_only"]["hr"] == 162

try:
    normalize_with_ai("", {}, api_key="test-only", client=client)
except AIInterpretationError:
    pass
else:
    raise AssertionError("Empty learner input must be rejected")

print("PASS: v0.9.0 AI normalization is structured, conservative, and non-executing")
