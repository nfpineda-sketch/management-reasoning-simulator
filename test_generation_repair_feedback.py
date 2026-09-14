"""A repair sees concurrent failures, and progress never implies an unapproved launch."""
from copy import deepcopy
import json

import pytest

from encounter_generator import generate_encounter
from generated_case import generate_ai_encounter, GeneratedCaseError
from generated_case_errors import generation_error
from test_generated_case import AuthorClient, clean_base, novel_payload


def multiple_faults():
    draft = novel_payload()
    draft["engine"]["response_rules"][0]["route"] = "IV"
    draft["engine"]["response_rules"][1]["delta"].append({"field": "spo2", "value": 5})
    draft["investigations"][2]["result"][2]["value"] = 10
    return draft


class RepairClient(AuthorClient):
    def __init__(self, *, corrected=None, stages=None):
        super().__init__(multiple_faults())
        self.corrected = novel_payload() if corrected is None else corrected
        self.stages = stages
        self.request_stages = []

    def create(self, **kwargs):
        if self.stages is not None:
            self.request_stages.append(self.stages[-1])
        if len(self.calls) == 1:
            self.payload = self.corrected
        return super().create(**kwargs)


def test_one_repair_receives_diagnostic_matcher_and_trajectory_faults_together():
    stages = []
    client = RepairClient(stages=stages)
    base = clean_base()
    before = deepcopy(base)
    result = generate_encounter("R1-05", base, client=client, progress=stages.append)

    assert len(client.calls) == 3
    repair = json.loads(client.calls[1]["input"])
    issues = repair["validation_issues"]
    paths = [issue["path"] for issue in issues]
    assert any("investigations" in path for path in paths)
    assert any("response_rules[0]" in path for path in paths)
    assert any("response_rules[1]" in path for path in paths)
    assert repair["proposed_case"] == multiple_faults()
    assert client.calls[2]["text"]["format"]["name"] == "clinical_consistency_review"
    assert stages == ["author", "validation", "correction", "validation", "review", "complete"]
    assert client.request_stages == ["author", "correction", "review"]
    assert base == before
    timing = result["spec"]["provenance"]["generation_timings"]
    assert all(timing[key] >= 0 for key in ("author_seconds", "correction_seconds", "review_seconds", "total_seconds"))


def test_failed_repair_has_actionable_safe_ids_without_case_content_or_false_completion(caplog):
    invalid = multiple_faults()
    private = "private rejected diagnosis and sk-test-secret"
    invalid["faculty"]["diagnosis"] = private
    invalid["engine"]["response_rules"][0]["id"] = "private-rejected-rule"
    stages = []
    client = RepairClient(corrected=invalid)
    base = clean_base()
    before = deepcopy(base)
    with pytest.raises(GeneratedCaseError) as caught:
        generate_ai_encounter("R1-05", base, client=client, progress=stages.append)
    assert caught.value.reference == "CASE-CORRECTION-CONTRACT"
    assert caught.value.validation_codes
    assert all(code in str(caught.value) and code in caplog.text for code in caught.value.validation_codes)
    assert private not in str(caught.value) + caplog.text
    assert "private-rejected-rule" not in str(caught.value) + caplog.text
    assert "validation_issues" not in str(caught.value) + caplog.text
    assert stages == ["author", "validation", "correction", "validation"]
    assert len(client.calls) == 2
    assert base == before


def test_public_diagnostic_codes_cannot_be_arbitrary_exception_text(caplog):
    bad = "sk-secret and unreviewed diagnosis"
    error = generation_error("CONTRACT", "CORRECTION", validation_codes=[bad])
    assert bad not in str(error) + caplog.text
    assert bad not in error.validation_codes


def test_clean_author_skips_repair_progress_and_request():
    stages = []
    client = AuthorClient()
    result = generate_ai_encounter("R1-05", clean_base(), client=client, progress=stages.append)
    assert stages == ["author", "validation", "review", "complete"]
    assert len(client.calls) == 2
    assert "correction_seconds" not in result["spec"]["provenance"]["generation_timings"]
