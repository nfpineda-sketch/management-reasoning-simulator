"""P-06 (faculty, 2026-09-30, corrected the same day): the declarations state the rule the engine applies.

Obstructive shock attributable to the PE -- a systolic below 90 mmHg, or a vasopressor needed to reach
90 mmHg despite adequate filling, with signs of hypoperfusion -- counts as soon as it is present; sustained
hypotension -- the same low pressure, or a vasopressor needed to keep it at 90 mmHg or above, without
hypoperfusion -- needs 15 consecutive minutes; a vasopressor the pressure does not need is neither. In D3
and the critical event of pulmonary_embolism_33f, D3 of pulmonary_embolism_61m and its TDFC row for C1.
New encounters only: the TDFC and case declarations are frozen with each encounter. The notes the
screening reads for encounters recorded before 2026-09-29 keep their words.
"""
import json
import re
from pathlib import Path

import evaluation_basis
import pe_obstruction as pe
from case_assessment_bank import CASES

ROOT = Path(__file__).resolve().parent
CRITERION = ("obstructive shock attributable to the PE (SBP < 90 mmHg, or a vasopressor needed to reach 90 mmHg "
             "despite adequate filling, with signs of hypoperfusion), recognised as soon as it is present, or "
             "sustained hypotension (SBP < 90 mmHg, or a vasopressor needed to keep it at 90 mmHg or above, for 15 "
             "consecutive minutes)")
NEITHER = "A vasopressor the pressure does not need, or a pressure lowered by bleeding or a drug, is neither."


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
                assert "obstructive shock attributable to the PE" in before, (case_id, text)
                # Obstructive shock is never stated without its hypoperfusion where the rule is written out.
                if "(SBP < 90" in text:
                    assert "with signs of hypoperfusion" in before, (case_id, text)


def test_the_criterion_is_stated_in_d3_the_event_and_c1():
    submassive, massive = CASES["pulmonary_embolism_33f"], CASES["pulmonary_embolism_61m"]
    assert pe.CRITERION_TEXT == CRITERION and pe.NEITHER_TEXT == NEITHER
    assert CRITERION in submassive["domains"]["D3"]["opportunity"]
    assert NEITHER in submassive["domains"]["D3"]["opportunity"]
    event = next(e for e in submassive["critical_events"] if e["event_id"] == "pe_unindicated_thrombolysis")
    assert CRITERION in " ".join(_texts(event)).replace("  ", " ")
    assert CRITERION in massive["domains"]["D3"]["opportunity"] and NEITHER in massive["domains"]["D3"]["opportunity"]
    assert any(CRITERION in text for text in massive["domains"]["D3"]["alternatives"])
    assert massive["objectives"]["C1"]["expected_evidence"][0] == "recognises " + CRITERION


def _minutes(f, current, count):
    for minute in range(count):
        f["elapsed"] = minute
        pe.track_hypotension(f, current)
    return pe.basis(f, current)


def test_the_engine_applies_the_rule_the_declarations_state():
    """Concordance of text, engine and evaluation (P-06, 2026-09-30)."""
    # A shock held up by a vasopressor it needs, with hypoperfusion: no wait at all.
    held_shock = pe.assessment(84, 4.0, 3.1, False, vasopressor_running=True)
    assert held_shock["low"] and held_shock["vasopressor_needed"]
    assert _minutes({}, held_shock, 1) == "obstructive_shock"
    # The same needed vasopressor without hypoperfusion: sustained hypotension, at 15 consecutive minutes only.
    held = pe.assessment(84, 2.5, 1.4, False, vasopressor_running=True)
    assert _minutes({}, held, 14) is None
    assert _minutes({}, held, 15) == "persistent_hypotension"
    # A vasopressor the pressure does not need proves nothing, however long it runs.
    unneeded = pe.assessment(104, 2.5, 1.4, False, vasopressor_running=True)
    assert not unneeded["low"] and not unneeded["vasopressor_needed"]
    assert _minutes({}, unneeded, 60) is None
    # And the screening names the same rule when it explains its reading.
    from test_pe_thrombolysis_screening import lysis_row, synthetic
    row = lysis_row(synthetic({"thrombolysis_indication": {"version": 3, "minute": 20, "basis": "obstructive_shock",
                                                           "data": {}}, "indication_basis": "obstructive_shock"}))
    assert row["status"] == "excluded" and "a vasopressor it needed to reach 90 mmHg" in str(row)
    row = lysis_row(synthetic({"thrombolysis_indication": {"version": 3, "minute": 20, "basis": None,
                                                           "data": {"vasopressor_running": True}},
                               "indication_basis": "none"}))
    assert row["status"] == "met" and "A vasopressor was running that the pressure did not need" in str(row)


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
