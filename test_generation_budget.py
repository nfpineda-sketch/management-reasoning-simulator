"""Request limits must not bypass review or silently discard failed usage."""
import json
import pytest
import generated_case as generation
from test_generated_case import AuthorClient, clean_base, novel_payload
from generated_case_schema import compile_case
from coupled_encounter import preview


def test_default_effort_preserves_independent_review_and_request_limits():
    client = AuthorClient()
    result = generation.generate_ai_encounter('R1-03', clean_base(), client=client, seed=31)
    assert [c['reasoning']['effort'] for c in client.calls] == ['low', 'medium']
    assert all(0 < c['timeout'] <= 120 for c in client.calls)
    assert json.loads(client.calls[1]['input'])['challenge_id'] == 'R1-03'
    assert json.loads(client.calls[1]['input'])['shared_engine_preview'] == preview(compile_case(client.payload), seed=31)
    assert len(result['spec']['provenance']['requests']) == 2


def test_budget_prevents_additional_paid_call_without_approval(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(generation, 'monotonic', lambda: clock[0])
    # Leave less than one stage, so the mandatory review cannot finish and must
    # be refused rather than paid for. Derive it from the budget constants: the
    # old literal 295 silently stopped refusing when the budget was recalibrated.
    exhausted = generation.REQUEST_BUDGET_SECONDS - generation.STAGE_BUDGET_SECONDS + 5
    class SlowClient(AuthorClient):
        def create(self, **kwargs):
            response = super().create(**kwargs)
            clock[0] = exhausted
            return response
    client = SlowClient()
    images = []
    with pytest.raises(generation.GeneratedCaseError) as caught:
        generation.generate_ai_encounter('R1-03', clean_base(), client=client,
            on_case_compiled=lambda *args: images.append(args))
    assert caught.value.code == 'BUDGET'
    assert len(client.calls) == 1
    assert not images
    assert caught.value.diagnostic['requests'][0]['usage']['total_tokens'] == 550
    assert caught.value.diagnostic['draft'] == client.payload


def test_incomplete_first_response_keeps_usage_without_public_content():
    client = AuthorClient(status='incomplete')
    with pytest.raises(generation.GeneratedCaseError) as caught:
        generation.generate_ai_encounter('R1-03', clean_base(), client=client)
    assert caught.value.diagnostic['requests'][0]['status'] == 'incomplete'
    assert caught.value.diagnostic['requests'][0]['usage']['output_tokens'] == 500
    assert 'draft' not in str(caught.value)


def test_custom_model_does_not_receive_unverified_reasoning_parameters():
    client = AuthorClient()
    generation.generate_ai_encounter('R1-03', clean_base(), client=client, model='custom-model')
    assert all('reasoning' not in call for call in client.calls)


def test_preview_covers_full_horizon_or_terminal_event_without_mutating_draft():
    case = compile_case(novel_payload())
    before = json.dumps(case, sort_keys=True)
    result = preview(case, seed=42)
    assert result[-1]['time_min'] == case['engine']['horizon_min'] or result[-1]['observable']['pulse_present'] is False
    assert json.dumps(case, sort_keys=True) == before
