"""Phase 0 (0J): every bank case passes the acceptance battery its decision says it passes.

Pre-pilot measurement safety, 2026-10-06. ``pilot_acceptance.battery`` plays each case through
the request's scenarios (A-K) and course properties; ``pilot_freeze`` holds each case's
decision. An accepted case passes every category. The excluded case fails exactly where its
exclusion says it does, so the exclusion is the battery's finding and not an opinion.
"""
import pytest

import pilot_acceptance as acceptance
import pilot_freeze

CATEGORIES = ("A_correct_management", "B_delayed_management", "C_omission", "D_incorrect_treatment",
              "E_excessive_treatment", "F_start_stop", "G_duplicate_treatment", "H_unexpected_reasonable",
              "I_waiting", "J_reassessment", "K_combined_interventions", "terminal_deterioration", "recovery",
              "reload_resume", "deterministic_replay", "action_ledger_completeness", "event_provenance",
              "observation_consistency", "trace_safety_guards")

#: What the excluded case fails, and why that is its exclusion (pilot_freeze.CASES).
EXCLUSION_FINDINGS = {"trauma_hemothorax_41m": {"A_correct_management", "recovery"}}


def test_the_battery_and_the_freeze_cover_the_same_cases():
    assert set(pilot_freeze.CASES) == set(acceptance.variants())
    assert len(acceptance.variants()) == 31


@pytest.mark.parametrize("variant", acceptance.variants())
def test_every_category_is_run(variant):
    assert set(acceptance.battery(variant)) == set(CATEGORIES)


@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("variant", pilot_freeze.accepted_variants())
def test_an_accepted_case_passes(variant, category):
    result = acceptance.battery(variant)[category]
    assert result["ok"], f"{variant} {category}: {result['detail']}"


@pytest.mark.parametrize("variant", pilot_freeze.excluded_variants())
def test_an_excluded_case_fails_where_its_exclusion_says_and_nowhere_else(variant):
    failed = {name for name, result in acceptance.battery(variant).items() if not result["ok"]}
    assert failed == EXCLUSION_FINDINGS[variant], failed


def test_the_table_row_says_the_battery_and_the_decision():
    row = acceptance.summary("acs_54m_inferior")
    assert row["battery"] == "PASS" and row["decision"] == "ACCEPT WITH DECLARED LIMITATION"
    assert row["challenges"] == ["R1-07", "R2-02", "R2-04"]
    assert {"C-SCRIPTED-AV-BLOCK", "C-SCRIPTED-VF"} <= set(row["limitations"])
    excluded = acceptance.summary("trauma_hemothorax_41m")
    assert excluded["decision"] == "EXCLUDE" and excluded["battery"].startswith("FAIL: ")
