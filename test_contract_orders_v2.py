"""Phase 1 WP1: OrderAction v2 describes the reader output without serving it."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import orders as v2
import order_ledger
import order_pipeline


def _tagged(*actions):
    parsed = {"actions": [deepcopy(action) for action in actions]}
    order_ledger.tag(parsed, "submission-1", "Give the orders.", minute=7)
    return parsed


def test_order_action_v2_has_identity_class_fields_and_version():
    parsed = _tagged({
        "type": "fluid", "volume_ml": 500, "fluid_type": "normal saline",
        "route": "IV", "administration_duration_min": 20,
    })
    original = deepcopy(parsed)
    [contract] = v2.from_parsed(parsed, submission_id="submission-1")

    assert contract.schema == "order_action_v2" and contract.version == 2
    assert contract.order_id == "submission-1:0"
    assert contract.submission_id == "submission-1"
    assert contract.action_class == "fluid"
    assert contract.fields == order_ledger.strip_tags(parsed["actions"][0])
    assert contract.engine_payload() == order_ledger.strip_tags(parsed["actions"][0])
    assert parsed == original


@pytest.mark.parametrize("action, expected", [
    ({"type": "reassessment", "delay_min": 15}, "reassessment"),
    ({"type": "clarification", "message": "Which dose?"}, "clarification"),
    ({"type": "clarification", "unrecognized_text": "zyvox"}, "unrecognized"),
    ({"type": "aspirin", "dose_mg": 300, "route": "PO"}, "aspirin"),
])
def test_order_action_v2_class_matches_the_existing_ledger_class(action, expected):
    parsed = _tagged(action)
    [contract] = v2.from_parsed(parsed, submission_id="submission-1")
    legacy = order_ledger.order_from_action(
        parsed["actions"][0], submission_id="submission-1", index=0,
        text="Give the orders.", minute=7,
    )
    assert contract.action_class == legacy["class"] == expected


def test_engine_payload_is_a_deep_copy_and_carries_no_ledger_keys():
    parsed = _tagged({
        "type": "procedural_sedation",
        "medications": [{"agent": "ketamine", "dose_mg": 20, "route": "IV"}],
    })
    [contract] = v2.from_parsed(parsed, submission_id="submission-1")
    payload = contract.engine_payload()
    payload["medications"][0]["dose_mg"] = 999
    assert contract.fields["medications"][0]["dose_mg"] == 20
    assert not [key for key in contract.fields if key.startswith("_")]


def test_v2_must_be_built_after_stable_identity_is_assigned():
    with pytest.raises(v2.OrderContractError, match="after order_ledger.tag"):
        v2.from_parsed({"actions": [{"type": "aspirin"}]}, submission_id="s")


def test_shadow_validator_detects_a_seeded_contract_difference():
    parsed = _tagged({"type": "aspirin", "dose_mg": 300, "route": "PO"})
    contracts = v2.from_parsed(parsed, submission_id="submission-1")
    changed = replace(contracts[0], fields={**contracts[0].fields, "dose_mg": 301})
    with pytest.raises(v2.OrderContractMismatch, match="dose_mg"):
        v2.assert_shadow_equivalent((changed,), parsed)


def test_open_turn_builds_the_shadow_contract_after_tagging(monkeypatch):
    seen = {}

    def spy(parsed, *, submission_id):
        seen["submission_id"] = submission_id
        seen["actions"] = deepcopy(parsed["actions"])
        return ()

    monkeypatch.setattr(order_pipeline.order_contracts_v2, "shadow_from_reader", spy)
    parsed = {"actions": [{"type": "aspirin", "dose_mg": 300, "route": "PO"}]}
    order_pipeline.open_turn(
        "Give aspirin 300 mg PO.", parsed,
        submission_id="send-7", entry_point="free_text", minute=12,
    )
    assert seen["submission_id"] == "send-7"
    assert seen["actions"][0]["_order_id"] == "send-7:0"
    assert seen["actions"][0]["_submission_id"] == "send-7"
    assert seen["actions"][0]["_written_at_min"] == 12

def test_v2_preserves_a_carried_forward_actions_original_submission_identity():
    parsed = _tagged({
        "type": "pantoprazole",
        "dose_mg": 80,
        "route": "IV",
    })
    original_order_id = parsed["actions"][0]["_order_id"]

    # This models Phase-0 follow-up behavior: the current turn has a new
    # submission id while an action in the bundle retains the stable identity
    # assigned when it was originally written.
    [contract] = v2.from_parsed(parsed, submission_id="follow-up-submission")

    assert contract.submission_id == "submission-1"
    assert contract.order_id == original_order_id
    assert contract.engine_payload() == order_ledger.strip_tags(parsed["actions"][0])
