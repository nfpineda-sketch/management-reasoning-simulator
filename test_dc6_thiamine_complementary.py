"""DC6 (faculty, 2026-09-30, P-01 A): thiamine is a complementary measure of D3.

Its omission alone does not lower D3 below 2 when the correction of the glucose, which comes first, was
adequate; given appropriately, it can contribute to D3 = 3 when the rest of the management also justifies it.
Only prospective: an encounter judges against the declaration frozen at its start, so one launched before the
change keeps the wording it was launched with, and no confirmed evaluation is re-read.
"""
import json

import evaluation_basis
import hypoglycemia_catalog as catalog
from case_assessment_bank import CANDIDATES, CASES

PREVIOUS = (" Thiamine is executable and belongs to the plan as a second objective: its omission alone does not "
            "make the correction of the glucose inadequate, and it is never a reason to delay it.")


def _declaration(configuration):
    return CASES.get(configuration["id"]) or CANDIDATES[configuration["id"]]


def test_thiamine_is_a_complementary_measure_of_d3_wherever_the_deficit_is_declared():
    deficient = [c for c in catalog.configurations() if c["conditions"]["thiamine_deficient"]]
    assert "hypoglycemia_54m_thiamine" in {c["id"] for c in deficient}
    for configuration in catalog.configurations():
        d3 = _declaration(configuration)["domains"]["D3"]
        if configuration["conditions"]["thiamine_deficient"]:
            assert "a complementary measure of D3" in d3["opportunity"]
            assert "its omission alone does not lower D3 below 2" in d3["opportunity"]
            assert "the correction of the glucose, which comes first, was adequate" in d3["opportunity"]
            assert "can contribute to D3 = 3 when the rest of the management also justifies it" in d3["opportunity"]
            assert "never a reason to delay the glucose" in d3["opportunity"]
            assert d3["expected"][0] == "Gives dextrose"
            assert "adds thiamine, as a complementary measure towards D3 = 3" in d3["expected"]
            assert PREVIOUS.strip() not in d3["opportunity"]
        else:
            assert "thiamine" not in d3["opportunity"].lower()


def test_an_encounter_launched_before_the_change_keeps_the_wording_it_was_launched_with():
    basis = evaluation_basis.freeze("hypoglycemia_54m_thiamine", code_version="before-p01")
    earlier = json.loads(json.dumps(basis))
    d3 = earlier["declaration"]["domains"]["D3"]
    d3["opportunity"] = d3["opportunity"].split(" Thiamine is executable")[0] + PREVIOUS
    earlier["fingerprint"] = evaluation_basis.fingerprint(earlier["declaration"])
    record = {"id": "attempt-before", "encounter": {"evaluation_basis": earlier}, "payload": {"session": {
        "state": {"encounter_spec": {"clinical_case": {"id": "hypoglycemia_54m_thiamine"}}}}}}
    resolved = evaluation_basis.resolve(record)
    assert resolved["status"] == "frozen"
    assert resolved["declaration"]["domains"]["D3"]["opportunity"].endswith(PREVIOUS)
    # Today's declaration is the new one; the record above is not moved to it.
    assert "a complementary measure of D3" in CASES["hypoglycemia_54m_thiamine"]["domains"]["D3"]["opportunity"]
