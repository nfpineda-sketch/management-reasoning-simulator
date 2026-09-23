"""Every case's declared opportunities are ones the case actually offers.

Five fields in a report are not five opportunities. These checks read each
declaration against the case it describes: a study named has to be among its
investigations, an action has to be one the engine executes, an examination has
to be a region the case authors.
"""
import pytest

import case_assessment as coverage
import rubric
from clinical_cases import FAMILIES

CASES = [(family, case) for family, bank in sorted(FAMILIES.items())
         for case in bank["variants"]]
IDS = [case["id"] for _, case in CASES]


@pytest.mark.parametrize("case_id", IDS)
def test_the_declaration_matches_the_case_it_describes(case_id):
    assert coverage.verify(case_id) == []


@pytest.mark.parametrize("case_id", IDS)
def test_every_bank_case_offers_all_five_domains(case_id):
    """Not a requirement of the rubric, but the goal for the bank."""
    assert coverage.assessable_domains(case_id) == rubric.DOMAIN_IDS


@pytest.mark.parametrize("case_id", IDS)
def test_every_case_defines_at_least_one_critical_event(case_id):
    events = coverage.events(case_id)
    assert events, f"{case_id} defines no critical event"
    for event in events:
        assert event["kind"] in rubric.CRITICAL_EVENT_KINDS
        assert event["alternatives"], "a valid different choice could be penalised"
        assert event["exclusions"], "an engine limitation could be read as the resident's failure"
        assert event["evidence_required"].strip()
        start, end = event["window_min"]
        assert start < end


def test_an_event_identifier_is_stable_and_means_the_same_thing_everywhere():
    """The same id in two cases must define the same event, or be a different id."""
    by_id = {}
    for case_id in IDS:
        for event in coverage.events(case_id):
            previous = by_id.setdefault(event["event_id"], event)
            assert previous["kind"] == event["kind"], event["event_id"]
            assert previous["action"] == event["action"], event["event_id"]


def test_a_missing_declaration_is_named_rather_than_assumed_complete():
    """Silence must not read as full coverage."""
    with pytest.raises(coverage.CoverageError):
        coverage.verify("no_such_case")
    # A case the bank carries but nobody declared is reported, not skipped.
    saved = coverage.CASES.pop("acs_48m_wellens")
    try:
        assert coverage.assessable_domains("acs_48m_wellens") == ()
        assert any("no rubric coverage is declared" in p
                   for p in coverage.verify("acs_48m_wellens"))
    finally:
        coverage.CASES["acs_48m_wellens"] = saved


def test_the_matrix_reports_coverage_and_its_gaps():
    rows = coverage.matrix()
    assert len(rows) == len(IDS)
    assert all(row["problems"] == [] for row in rows)
    assert {row["case_id"] for row in rows} == set(IDS)
    assert all(row["complete"] for row in rows)


def test_a_window_is_a_clinical_interval_not_the_whole_encounter():
    """A window that never closes cannot separate an omission from a late choice."""
    for case_id in IDS:
        entry = coverage.declared(case_id)
        for domain, item in entry["domains"].items():
            start, end = item["window_min"]
            assert 0 <= start < end <= 180, (case_id, domain)


def test_the_published_matrix_is_the_one_the_code_declares():
    """A matrix typed by hand drifts from the code it describes."""
    from pathlib import Path
    import tools_coverage_matrix
    published = Path(__file__).with_name("docs") / "COBERTURA_CASOS.md"
    assert published.read_text(encoding="utf-8") == tools_coverage_matrix.build(), (
        "docs/COBERTURA_CASOS.md is out of date; run tools_coverage_matrix.py")


def test_the_worked_example_is_the_one_the_code_produces():
    """It is generated, so an edit made on top of it would be lost silently."""
    from pathlib import Path
    import tools_rubric_example
    published = Path(__file__).with_name("docs") / "EJEMPLO_RUBRICA.md"
    body = published.read_text(encoding="utf-8")
    assert tools_rubric_example.REAL_RUN in body, "the real run section is missing"
    assert "ILLUSTRATIVE-NOT-A-MODEL-CALL" in body, "the illustrative proposal is not labelled"
