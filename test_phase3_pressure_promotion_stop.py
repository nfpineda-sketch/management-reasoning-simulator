"""P3-383: the effective stop, the reopening and the pre-commit abort of the pressure experiment, replayed under the PROMOTED configuration (FD-PROMOTE-01).

TEST-SIDE. The proofs are the ones of ``test_phase3_stop_page.py`` -- the real page (Streamlit ``AppTest``), both GI cases, the real grant, an artifact store -- imported, not copied. The only thing this module
changes is which approved snapshot the authorized development configuration names: the ratified ``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`` (grant version 2) instead of the older committed point. Every one of
the behaviours below must hold under the promoted configuration exactly as it held under the older one: nothing here is a new behaviour, and nothing weakens an assertion of the original.

What is NOT mirrored, and why: ``test_s12`` (a configuration fault at the arrival) names the older point by hand in its own environment; the promoted configuration's own fail-closed behaviour is tested, by name and
with mutations, in ``test_phase3_pressure_promotion.py``.
"""
import pytest

import runtime_pressure_grant as grants
import test_phase3_pair_page as page
# The proofs, imported by name so that pytest collects them here and runs them under the fixture below. Their parametrization (cases, flags) travels with the functions.
from test_phase3_stop_page import (stopped, test_s1_normal_authority_progress_is_unaffected_by_the_guard, test_s2_an_unsupported_action_after_the_first_commit_stops_the_session_and_nothing_can_move_it,  # noqa: F401
                                   test_s3_a_pending_durable_submission_is_claimed_and_blocked_not_run_and_does_not_loop, test_s4_reading_stays_available_on_the_stopped_page,
                                   test_s4b_leaving_the_session_is_the_operators_way_out_and_a_new_encounter_is_a_new_experiment, test_s5_an_injected_validation_failure_after_a_commit_stops_the_session,
                                   test_s6_the_collapse_boundary_stops_the_session_before_committing_it_and_is_not_a_patient_outcome, test_s7_the_record_travels_with_a_saved_encounter,
                                   test_s8_a_reopened_stopped_encounter_stays_stopped_with_the_authority_flags_on_or_off,
                                   test_s9_a_reopened_encounter_that_was_ACTIVE_and_lost_its_site_is_stopped_never_continued_on_the_legacy_engine,
                                   test_s10_a_new_browser_session_is_a_new_encounter_and_the_stopped_one_stays_on_record,
                                   test_s11_an_unsupported_first_action_aborts_before_any_commit_and_the_legacy_encounter_continues, test_s13_collapse_already_established_at_the_first_minute_aborts_before_any_commit_and_the_legacy_encounter_continues,  # noqa: E501
                                   test_s14_a_validation_failure_at_the_first_minute_aborts_before_any_commit, test_s15_every_post_commit_failure_is_a_stop_with_its_exact_state_recorded_and_nothing_can_continue,
                                   test_s17_a_click_that_arrives_with_the_failing_submission_is_not_handled_and_the_failing_run_already_says_so,
                                   test_s18_a_complete_click_that_arrives_with_the_failing_submission_does_not_close_the_stopped_encounter,
                                   test_s19_removing_the_authority_configuration_mid_encounter_stops_the_clock_route_too, test_s16_the_notice_is_operational_and_the_stopped_page_leaks_nothing_of_the_common_core)


@pytest.fixture(scope="module", autouse=True)
def under_the_promoted_snapshot():
    """Every page of this module runs the ratified snapshot. Module scope and autouse: the module-scoped ``stopped`` fixture is built after it, so it too runs the promoted configuration."""
    patch = pytest.MonkeyPatch()
    patch.setattr(page, "AUTHORITY_SNAPSHOT_ID", grants.PRESSURE_SNAPSHOT_ID_V2)
    try:
        yield
    finally:
        patch.undo()


def test_m0_this_module_really_runs_the_promoted_snapshot(monkeypatch, tmp_path):
    """The mirror is only worth anything if the page it opens is the promoted one: the site names the ratified snapshot and grant version 2."""
    import runtime_authority as ra
    at = page._open(monkeypatch, "gi_bleed_57m", shadow=True, dry=False, authority=str(tmp_path / "store"))
    page._ask(at, "What brought you in today?")
    site = at.session_state.get(ra.SITE_KEY)
    assert site is not None and site.snapshot_id == grants.PRESSURE_SNAPSHOT_ID_V2 and site.grant["grant_id"] == grants.GRANT_ID_V2 and site.minutes_committed and not site.halted
