"""Real SDK failure classification and bounded repair before patient launch."""
from copy import deepcopy
import json
from types import SimpleNamespace

import httpx
from openai import OpenAI
import pytest

from generated_case import generate_ai_encounter, GeneratedCaseError
from test_generated_case import AuthorClient, approval, clean_base, novel_payload


@pytest.mark.parametrize("status,body_code,param,expected", [
    (401, "invalid_api_key", None, "AUTH"),
    (403, "permission_denied", None, "ACCESS"),
    (404, "model_not_found", None, "MODEL"),
    (429, "insufficient_quota", None, "QUOTA"),
    (429, "rate_limit_exceeded", None, "RATE"),
    (400, "invalid_json_schema", "text.format.schema", "FORMAT"),
    (400, None, "max_output_tokens", "REQUEST"),
    (503, None, None, "PROVIDER"),
])
def test_actual_sdk_http_errors_are_distinguished_without_provider_body_leaks(status, body_code, param, expected, caplog):
    calls = []
    private = "sk-test-private-provider-message hidden fictional diagnosis"

    def respond(request):
        calls.append(json.loads(request.content))
        return httpx.Response(status, json={"error": {"message": private, "type": "invalid_request_error",
                                                      "code": body_code, "param": param}})

    base = clean_base()
    original = deepcopy(base)
    with OpenAI(api_key="local-test-only", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(GeneratedCaseError) as exc:
            generate_ai_encounter("R1-05", base, client=client)
    assert exc.value.reference == f"CASE-AUTHOR-{expected}"
    assert private not in str(exc.value) + caplog.text
    assert "sk-test" not in str(exc.value) + caplog.text
    assert len(calls) == 1
    assert calls[0]["store"] is False
    assert calls[0]["text"]["format"]["strict"] is True
    assert base == original


@pytest.mark.parametrize("transport_error,expected", [(httpx.ReadTimeout, "TIMEOUT"), (httpx.ConnectError, "CONNECTION")])
def test_actual_sdk_transport_failures_have_safe_distinct_references(transport_error, expected):
    def respond(request):
        raise transport_error("private network details", request=request)
    with OpenAI(api_key="local-test-only", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(GeneratedCaseError) as exc:
            generate_ai_encounter("R1-05", clean_base(), client=client)
    assert exc.value.reference == f"CASE-AUTHOR-{expected}"
    assert "private network details" not in str(exc.value)


class CorrectingClient(AuthorClient):
    def __init__(self, *, corrected=None, review=None):
        original = novel_payload()
        # The parser emits no route on fluid orders. A clinically natural IV
        # matcher passes the JSON schema but makes the rule unreachable.
        original["engine"]["response_rules"][0]["route"] = "IV"
        super().__init__(original, review)
        self.corrected = novel_payload() if corrected is None else corrected

    def create(self, **kwargs):
        if len(self.calls) == 1:
            self.payload = self.corrected
        return super().create(**kwargs)


def test_unreachable_rule_is_corrected_then_checked_by_independent_reviewer():
    client = CorrectingClient()
    base = clean_base()
    original = deepcopy(base)
    result = generate_ai_encounter("R1-05", base, client=client, seed=17)
    assert len(client.calls) == 3
    correction = json.loads(client.calls[1]["input"])
    assert correction["proposed_case"]["engine"]["response_rules"][0]["route"] == "IV"
    assert "cannot be reached" in correction["validation_feedback"]
    assert correction["variation_seed"] == 17
    reviewed_case = json.loads(client.calls[2]["input"])["case"]
    assert "route" not in reviewed_case["engine"]["response_rules"][0]
    assert client.calls[2]["text"]["format"]["name"] == "clinical_consistency_review"
    assert result["spec"]["provenance"]["authoring_requests"] == 2
    assert result["spec"]["provenance"]["correction_count"] == 1
    assert result["spec"]["provenance"]["author_usage"]["total_tokens"] == 1100
    assert base == original


def test_invalid_correction_stops_after_two_author_requests_without_review_or_launch():
    invalid = novel_payload()
    invalid["engine"]["response_rules"][0]["route"] = "IV"
    client = CorrectingClient(corrected=invalid)
    base = clean_base()
    original = deepcopy(base)
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", base, client=client)
    assert exc.value.reference == "CASE-CORRECTION-CONTRACT"
    assert len(client.calls) == 2
    assert all(call["text"]["format"]["name"] == "new_clinical_case" for call in client.calls)
    assert base == original


def test_corrected_case_still_cannot_launch_when_reviewer_rejects():
    review = approval()
    review.update(coherent=False, issues=["hidden diagnosis and contradictory physiology"])
    client = CorrectingClient(review=review)
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", clean_base(), client=client)
    assert exc.value.reference == "CASE-REVIEW-REVIEW"
    assert "hidden diagnosis" not in str(exc.value)
    # Author, one structural correction, one review. Under a single review round
    # a rejected case is reported rather than repaired and re-reviewed, so the
    # worst rejected encounter costs three requests instead of five.
    assert len(client.calls) == 3
    assert [call["max_output_tokens"] for call in client.calls] == [24000, 24000, 6000]


@pytest.mark.parametrize("client,reference", [
    (AuthorClient(status="incomplete"), "CASE-AUTHOR-INCOMPLETE"),
    (AuthorClient(refusal=True), "CASE-AUTHOR-REFUSED"),
    (AuthorClient(payload="{invalid json}"), "CASE-AUTHOR-JSON"),
    (AuthorClient(payload={"case": "missing fields"}), "CASE-AUTHOR-STRUCTURE"),
])
def test_invalid_author_responses_do_not_trigger_unbounded_retries(client, reference):
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", clean_base(), client=client)
    assert exc.value.reference == reference
    assert len(client.calls) == 1


def test_unfinished_review_is_identified_as_review_stage():
    class Client(AuthorClient):
        def create(self, **kwargs):
            if self.calls:
                self.status = "incomplete"
            return super().create(**kwargs)
    client = Client()
    with pytest.raises(GeneratedCaseError) as exc:
        generate_ai_encounter("R1-05", clean_base(), client=client)
    assert exc.value.reference == "CASE-REVIEW-INCOMPLETE"
    assert len(client.calls) == 2
