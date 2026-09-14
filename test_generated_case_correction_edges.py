"""Failures during the bounded correction cannot start or leak an encounter."""
from copy import deepcopy
import json

import httpx
from openai import OpenAI
import pytest

from generated_case import GeneratedCaseError, generate_ai_encounter
from test_generated_case import clean_base, novel_payload
from test_generated_case_failures import CorrectingClient


def test_actual_sdk_provider_failure_during_correction_preserves_state_and_stops(caplog):
    original_draft = novel_payload()
    original_draft["engine"]["response_rules"][0]["route"] = "IV"
    private = "private provider diagnostic and unreviewed patient facts"
    calls = []

    def respond(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(200, json={
                "id": "resp_local_test", "object": "response", "created_at": 1,
                "status": "completed", "model": "gpt-5-mini",
                "output": [{"id": "msg_local_test", "type": "message", "role": "assistant",
                            "status": "completed", "content": [{"type": "output_text",
                            "text": json.dumps(original_draft), "annotations": []}]}],
            })
        return httpx.Response(429, json={"error": {
            "type": "insufficient_quota", "code": "insufficient_quota", "message": private,
        }})

    base = clean_base()
    original = deepcopy(base)
    with OpenAI(api_key="local-test-only", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(GeneratedCaseError) as exc:
            generate_ai_encounter("R1-05", base, client=client)
    assert exc.value.reference == "CASE-CORRECTION-QUOTA"
    assert len(calls) == 2
    assert all(call["text"]["format"]["name"] == "new_clinical_case" for call in calls)
    assert private not in str(exc.value) + caplog.text
    assert base == original


@pytest.mark.parametrize("corrected,reference", [
    ("{private broken JSON", "CASE-CORRECTION-JSON"),
    ({"private": "missing required patient structure"}, "CASE-CORRECTION-STRUCTURE"),
])
def test_malformed_correction_does_not_retry_again_or_reach_reviewer(corrected, reference, caplog):
    client = CorrectingClient(corrected=corrected)
    base = clean_base()
    original = deepcopy(base)
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", base, client=client)
    assert exc.value.reference == reference
    assert len(client.calls) == 2
    assert all(call["text"]["format"]["name"] == "new_clinical_case" for call in client.calls)
    assert "private" not in str(exc.value) + caplog.text
    assert base == original
