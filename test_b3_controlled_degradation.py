"""Faculty decision B3: a Management Trace analysis degrades by section.

A pivotal decision that cites outside its own rules is withheld whole, with
its reason, and the rest of the analysis is shown as partial; nothing that
cites outside the rules reaches the resident. Provenance, structure, the
chronology of the decisions and a report with no decision left still refuse
it. Two of the first four encounters of the synthetic batch (2026-09-25) lost
their document A to one such decision each.
"""
from copy import deepcopy

import pytest

from management_trace_analysis import (
    CITATION_REASON, NUMERAL_REASON, ManagementTraceAnalysisError, usable_analysis,
    validate_management_trace_analysis,
)
from test_management_trace_analysis import claim, sample_payload, sample_report


def two_decisions():
    report = sample_report()
    second = {
        "decision_ref": "trace:1", "title": "Checking the response before more fluid",
        "interpretation": claim("The response was read as incomplete before more fluid.", "trace:1"),
        "expected_vs_observed": claim("No expectation was recorded for this check.", "trace:1"),
        "adaptation": claim("No later adjustment was recorded.", "trace:1"),
        "reflection_insight": None,
    }
    report["analysis"]["pivotal_decisions"].append(second)
    validate_management_trace_analysis(report, sample_payload())
    return report


def _insight(moment):
    moment["reflection_insight"] = claim("A later reflection.", "reflection:decision-1")


# Each fault is one the request schema still allows (it offers every encounter
# reference to the three parts and every reflection to the insight); the rule
# is per decision, so only the validator can see it.
@pytest.mark.parametrize("position, fault, message", [
    (0, lambda moment: moment["adaptation"]["evidence_refs"].remove("trace:0"),
     "An adaptation must cite encounter evidence"),
    (0, lambda moment: moment["interpretation"]["evidence_refs"].append("trace:1"),
     "A decision-time interpretation cites later"),
    (0, lambda moment: moment["expected_vs_observed"]["evidence_refs"].append("trace:1"),
     "An expected-versus-observed response must cite its own decision"),
    (1, _insight, "A retrospective insight must cite a reflection"),
])
def test_a_decision_citing_outside_its_rules_is_withheld_whole(position, fault, message):
    report = two_decisions()
    fault(report["analysis"]["pivotal_decisions"][position])
    with pytest.raises(ManagementTraceAnalysisError, match=message):
        validate_management_trace_analysis(report, sample_payload())
    shown, withheld = usable_analysis(report, sample_payload())
    kept = [moment["decision_ref"] for moment in shown["analysis"]["pivotal_decisions"]]
    assert kept == ["trace:0", "trace:1"][:position] + ["trace:0", "trace:1"][position + 1:]
    assert [item["section"] for item in withheld] == [f"pivotal_decisions[{position}]"]
    assert message in withheld[0]["reason"]
    assert withheld[0]["reason"].startswith(CITATION_REASON.split("(")[0])
    # The rest of the analysis is shown untouched.
    assert shown["analysis"]["overview"] == report["analysis"]["overview"]
    assert shown["analysis"]["trajectory"] == report["analysis"]["trajectory"]


def test_no_decision_left_refuses_the_report():
    report = sample_report()
    report["analysis"]["pivotal_decisions"][0]["adaptation"]["evidence_refs"].remove("trace:0")
    with pytest.raises(ManagementTraceAnalysisError, match="Too little"):
        usable_analysis(report, sample_payload())


def test_provenance_and_chronology_still_refuse_the_report():
    stale = two_decisions()
    stale["prompt_version"] = "0.9"
    with pytest.raises(ManagementTraceAnalysisError, match="does not match"):
        usable_analysis(stale, sample_payload())
    reversed_order = two_decisions()
    reversed_order["analysis"]["pivotal_decisions"].reverse()
    with pytest.raises(ManagementTraceAnalysisError, match="chronological"):
        usable_analysis(reversed_order, sample_payload())


def test_a_numeral_is_still_withheld_for_its_own_reason():
    report = two_decisions()
    report["analysis"]["strengths"][0]["text"] = "An expected effect was stated 5 minutes early."
    shown, withheld = usable_analysis(report, sample_payload())
    assert withheld == [{"section": "strengths[0]", "reason": NUMERAL_REASON,
                         "text": "An expected effect was stated 5 minutes early."}]
    assert len(shown["analysis"]["pivotal_decisions"]) == 2


def test_a_valid_report_is_returned_as_it_is():
    report = two_decisions()
    shown, withheld = usable_analysis(deepcopy(report), sample_payload())
    assert withheld == [] and shown == report
