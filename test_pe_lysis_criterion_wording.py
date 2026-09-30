"""P-06 (faculty, 2026-09-30): the declarations state the criterion the engine applies to thrombolysis.

«Obstructive shock attributable to the PE, or sustained hypotension (SBP < 90 mmHg for 15 consecutive
minutes)», in D3 and the critical event of pulmonary_embolism_33f, D3 of pulmonary_embolism_61m and its TDFC
row for C1. New encounters only: the TDFC and case declarations are frozen with each encounter. The engine
and its notes do not change, since the screening of encounters recorded before 2026-09-29 reads those notes.
"""
import json
import re
from pathlib import Path

import evaluation_basis
from case_assessment_bank import CASES

ROOT = Path(__file__).resolve().parent
CRITERION = "obstructive shock attributable to the PE, or sustained hypotension (SBP < 90 mmHg for 15 consecutive minutes)"


def _texts(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _texts(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _texts(item)


def test_every_mention_of_sustained_hypotension_carries_the_obstructive_shock_beside_it():
    for case_id in ("pulmonary_embolism_33f", "pulmonary_embolism_61m"):
        for text in _texts(CASES[case_id]):
            for match in re.finditer(r"sustained hypotension", text, re.I):
                before = text[:match.start()]
                assert re.search(r"obstructive shock attributable to\s+the PE,? (or|nor) $", before), (case_id, text)


def test_the_criterion_is_stated_in_d3_the_event_and_c1():
    submassive, massive = CASES["pulmonary_embolism_33f"], CASES["pulmonary_embolism_61m"]
    assert CRITERION in submassive["domains"]["D3"]["opportunity"]
    event = next(e for e in submassive["critical_events"] if e["event_id"] == "pe_unindicated_thrombolysis")
    assert CRITERION in " ".join(_texts(event)).replace("  ", " ")
    assert "(SBP < 90 mmHg for 15 consecutive minutes)" in massive["domains"]["D3"]["opportunity"]
    assert any(CRITERION in text for text in massive["domains"]["D3"]["alternatives"])
    assert massive["objectives"]["C1"]["expected_evidence"][0] == "recognises " + CRITERION


def test_an_encounter_frozen_before_keeps_its_approved_tdfc_wording():
    basis = json.loads(json.dumps(evaluation_basis.freeze("pulmonary_embolism_61m", code_version="before-p06")))
    evidence = basis["declaration"]["objectives"]["C1"]["expected_evidence"]
    evidence[0] = "recognises the sustained hypotension"
    basis["fingerprint"] = evaluation_basis.fingerprint(basis["declaration"])
    record = {"id": "attempt-before", "encounter": {"evaluation_basis": basis}, "payload": {"session": {
        "state": {"encounter_spec": {"clinical_case": {"id": "pulmonary_embolism_61m"}}}}}}
    resolved = evaluation_basis.resolve(record)
    assert resolved["status"] == "frozen"
    assert resolved["declaration"]["objectives"]["C1"]["expected_evidence"][0] == "recognises the sustained hypotension"


def test_the_engine_and_the_notes_the_screening_reads_are_unchanged():
    engine = (ROOT / "pe_obstruction.py").read_text(encoding="utf-8")
    assert "this is sustained hypotension from the obstruction." in engine
    assert "Systemic thrombolysis given for sustained hypotension" in engine
    screening = (ROOT / "rubric_screening.py").read_text(encoding="utf-8")
    assert 're.search(r"sustained hypotension", n["text"], re.I)' in screening
