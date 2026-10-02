"""R-2 and R-3 (faculty, 2026-09-30): three observation rows, for new encounters only.

R-3 · T-1: C3 in anaphylaxis_29f observes the anticipation of the airway -- the threat named, help able to
manage it called or the airway prepared, the stridor reassessed -- and never its execution, which the
engine cannot show. R-2: two C14 criteria. In acs_61m_posterior recognising a subtle wall-motion finding
the report already states is not required, and a non-dilated aorta never excludes a dissection; in
acs_70f_left_main a small justified bolus with reassessment is judged in context, not penalised by itself.
An encounter frozen before keeps the rows it started with.
"""
import json

import evaluation_basis
import observation_opportunities as opportunities
from case_assessment_bank import CASES


def test_the_29f_c3_row_observes_the_anticipation_and_says_what_it_cannot():
    row = CASES["anaphylaxis_29f"]["objectives"]["C3"]
    assert row["opportunity"] == "yes"
    evidence = " ".join(row["expected_evidence"])
    for part in ("airway threat", "calls for help", "prepares the airway", "reassesses the stridor"):
        assert part in evidence, part
    assert "orders oxygen" not in evidence                      # oxygen is F1's evidence
    assert "never for the epinephrine and the oxygen alone" in row["rationale"]
    assert "evidence of anticipation, not of execution" in row["outside_the_encounter"]
    assert "intubating always succeeds" in row["outside_the_encounter"]
    assert row["reviewed"]["revised"]["id"] == "R-3" and row["reviewed"]["version"] == "TDFC-REVIEW-1"


def test_the_61m_c14_row_does_not_require_the_subtle_finding():
    row = CASES["acs_61m_posterior"]["objectives"]["C14"]
    assert not any("names the posterior hypokinesis" in item for item in row["expected_evidence"])
    assert "recognising it is not required" in row["rationale"]
    assert "do not exclude an aortic dissection" in row["rationale"]
    assert row["reviewed"]["revised"]["id"] == "R-2"


def test_the_70f_c14_row_accepts_a_justified_small_bolus():
    row = CASES["acs_70f_left_main"]["objectives"]["C14"]
    evidence = " ".join(row["expected_evidence"])
    assert "a small bolus with its limit stated and reassesses it" in evidence
    assert "adapts the plan to the response" in evidence
    assert "No single answer follows" in row["rationale"]
    assert "limits or withholds volume, or escalates support, because of it" not in row["expected_evidence"]
    # D-8 (2026-10-02) revised it after R-2: judged on the signals the room shows.
    assert row["reviewed"]["revised"]["id"] == "D-8" and row["reviewed"]["revised"]["after"] == "R-2"
    assert "that part of the observation is not evaluable rather than missing" in row["rationale"]


def test_an_encounter_frozen_before_keeps_the_rows_it_started_with():
    for case_id, objective in (("anaphylaxis_29f", "C3"), ("acs_70f_left_main", "C14")):
        basis = json.loads(json.dumps(evaluation_basis.freeze(case_id, code_version="before-r2-r3")))
        row = basis["declaration"]["objectives"][objective]
        row["expected_evidence"] = ["the evidence approved before 2026-09-30"]
        row["reviewed"].pop("revised", None)
        basis["fingerprint"] = evaluation_basis.fingerprint(basis["declaration"])
        record = {"id": "attempt-before", "encounter": {"evaluation_basis": basis}, "payload": {"session": {
            "state": {"encounter_spec": {"clinical_case": {"id": case_id}}}}}}
        resolved = opportunities.resolve(objective, record)
        assert resolved["state"] == "yes"
        assert list(resolved["expected_evidence"]) == ["the evidence approved before 2026-09-30"], case_id
