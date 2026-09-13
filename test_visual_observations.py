"""Visible cues follow source findings, never success/failure of a learner order."""
from copy import deepcopy

from visual_observations import hypoperfusion_visual_profile, visual_observations, visual_profile


def patient():
    return {
        "observable": {
            "mental_status": "Alert", "work_of_breathing": "Mildly increased",
            "extremities": "Cool", "peripheral_perfusion": "impaired",
            "hr": 174, "sbp": 94, "dbp": 56, "crt": 4,
        },
        "encounter_spec": {"visual_profile": hypoperfusion_visual_profile()},
        "hidden": {}, "treatments": {},
    }


def test_alert_pilot_is_uncomfortable_with_authored_pallor():
    observed = visual_observations(patient())
    assert observed["mental_status"] == "alert"
    assert observed["expression"] == "uncomfortable"
    assert observed["skin_color"] == "mild pallor"
    assert observed["diaphoresis"] == "not recorded"


def test_numerical_hypotension_and_tactile_cold_do_not_invent_unprofiled_color():
    state = patient()
    state.pop("encounter_spec")
    state["observable"].update(sbp=40, dbp=20, hr=220, crt=7, extremities="Very cold")
    observed = visual_observations(state)
    assert observed["skin_color"] == "not recorded"
    assert observed["diaphoresis"] == "not recorded"
    assert observed["mottling"] is False


def test_serial_perfusion_changes_update_authored_skin_both_directions():
    state = patient()
    expected = [
        ("impaired", "mild pallor"), ("severely impaired", "pallor"),
        ("critical", "pallor"), ("mildly impaired", "mild pallor"),
        ("preserved", "natural"), ("impaired", "mild pallor"),
    ]
    for category, skin in expected:
        state["observable"]["peripheral_perfusion"] = category
        assert visual_observations(state)["skin_color"] == skin


def test_restoring_pressure_or_warm_temperature_alone_does_not_clear_pallor():
    state = patient()
    before = visual_observations(state)
    state["observable"].update(sbp=128, dbp=78, extremities="Warm")
    assert visual_observations(state) == before


def test_sedation_reduces_engagement_without_claiming_perfusion_recovery():
    state = patient()
    state["observable"]["peripheral_perfusion"] = "severely impaired"
    before = visual_observations(state)
    state["observable"]["mental_status"] = "Sedated"
    after = visual_observations(state)
    assert after["expression"] == "sedated"
    assert after["skin_color"] == before["skin_color"] == "pallor"


def test_passive_mentation_and_respiration_are_independent():
    state = patient()
    state["observable"].update(mental_status="Obtunded", work_of_breathing="Severe")
    observed = visual_observations(state)
    assert observed["expression"] == "passive"
    assert observed["work_of_breathing"] == "severe"
    assert observed["skin_color"] == "mild pallor"


def test_perfusion_recovery_does_not_override_ongoing_respiratory_distress():
    state = patient()
    state["observable"].update(peripheral_perfusion="preserved", work_of_breathing="Severe")
    observed = visual_observations(state)
    assert observed["skin_color"] == "natural"
    assert observed["expression"] == "uncomfortable"


def test_mottling_is_drawn_only_when_explicitly_authored_or_observed():
    state = patient()
    state["observable"]["peripheral_perfusion"] = "critical"
    assert visual_observations(state)["mottling"] is False
    state["observable"]["extremities"] = "Mottled/Cold"
    assert visual_observations(state)["mottling"] is True
    state["observable"]["extremities"] = "Cold"
    state["observable"]["visual"] = {"mottling": True}
    assert visual_observations(state)["mottling"] is True


def test_explicit_case_visual_findings_override_profile_without_free_text():
    state = patient()
    state["observable"]["visual"] = {"skin_color": "natural", "diaphoresis": "mild"}
    assert visual_observations(state)["skin_color"] == "natural"
    assert visual_observations(state)["diaphoresis"] == "mild"
    state["observable"]["visual"] = {"skin_color": "INJECT", "diaphoresis": "INJECT"}
    assert "INJECT" not in str(visual_observations(state))
    assert visual_observations(state)["skin_color"] == "not recorded"


def test_learner_actions_time_and_hidden_diagnoses_do_not_change_contract():
    state = patient()
    before = deepcopy(state)
    expected = visual_observations(state)
    assert state == before
    state.update(sim_time=120, pending_order="Give the wrong drug", assessment={"passed": False})
    state["hidden"] = {"diagnosis": "secret", "tissue_perfusion": .01}
    state["treatments"] = {"cardioversions": 4}
    assert visual_observations(state) == expected


def test_legacy_generated_pilot_gets_explicit_compatibility_profile():
    state = patient()
    state["encounter_spec"] = {
        "schema_version": "mrs.ps001.encounter.v1", "case_family": "PS001",
        "challenge_id": "R1-03", "profile_id": "rhythm_contributor",
    }
    assert visual_observations(state)["expression"] == "uncomfortable"
    state["encounter_spec"]["visual_profile"] = {}
    assert visual_observations(state)["skin_color"] == "not recorded"
    state["encounter_spec"].pop("visual_profile")
    state["encounter_spec"]["case_family"] = "different_case"
    assert visual_observations(state)["skin_color"] == "not recorded"


def test_profile_copy_and_invalid_findings_cannot_mutate_original():
    state = patient()
    before = deepcopy(state)
    visual_profile(state)["baseline"]["skin_color"] = "INJECT"
    assert state == before
    state["observable"].update(mental_status="INJECT", work_of_breathing="INJECT",
                               peripheral_perfusion="INJECT")
    assert "INJECT" not in str(visual_observations(state))


def legacy_patient():
    state = patient()
    state["observable"].pop("peripheral_perfusion")
    state["encounter_spec"] = {
        "schema_version": "mrs.ps001.encounter.v1", "case_family": "PS001",
        "challenge_id": "R1-03", "profile_id": "rhythm_contributor",
        "content_sha256": "unchanged-original-digest",
    }
    return state


def test_legacy_initial_entry_ignores_stale_base_flow_without_mutation():
    state = legacy_patient()
    state["sim_time"] = 0
    state["hidden"]["peripheral_flow"] = .95
    before = deepcopy(state)
    visible = visual_observations(state)
    assert visible["expression"] == "uncomfortable"
    assert visible["skin_color"] == "mild pallor"
    assert state == before


def test_legacy_severe_and_recovered_snapshots_reuse_existing_flow_without_a_tick():
    for flow, expected_skin, expression in (
        (.08, "pallor", "markedly uncomfortable"),
        (.22, "pallor", "markedly uncomfortable"),
        (.23, "mild pallor", "uncomfortable"),
        (.52, "mild pallor", "uncomfortable"),
        (.70, "natural", "neutral"),
    ):
        state = legacy_patient()
        state["sim_time"] = 20
        state["hidden"]["peripheral_flow"] = flow
        before = deepcopy(state)
        visible = visual_observations(state)
        assert visible["skin_color"] == expected_skin
        assert visible["expression"] == expression
        assert state == before


def test_legacy_arrest_is_critical_even_if_retained_flow_is_stale():
    state = legacy_patient()
    state["sim_time"] = 0
    state["hidden"]["peripheral_flow"] = .95
    state["observable"].update(pulse_present=False, mental_status="Unresponsive")
    before = deepcopy(state)
    visible = visual_observations(state)
    assert visible["skin_color"] == "pallor"
    assert visible["expression"] == "passive"
    assert state == before


def test_legacy_migration_does_not_read_flow_for_unknown_or_explicitly_unprofiled_cases():
    for update in ({"visual_profile": {}}, {"case_family": "different_case"},
                   {"schema_version": "future_schema"}):
        state = legacy_patient()
        state["sim_time"] = 20
        state["hidden"]["peripheral_flow"] = .01
        state["encounter_spec"].update(update)
        assert visual_observations(state)["skin_color"] == "not recorded"


def test_legacy_migration_rejects_invalid_flow_and_preserves_explicit_category():
    for flow in (float("nan"), float("inf"), -.1, 1.1, True, ".01", None):
        state = legacy_patient()
        state["sim_time"] = 20
        state["hidden"]["peripheral_flow"] = flow
        assert visual_observations(state)["skin_color"] == "mild pallor"
    state = legacy_patient()
    state["sim_time"] = 20
    state["hidden"]["peripheral_flow"] = .01
    state["observable"]["peripheral_perfusion"] = "preserved"
    assert visual_observations(state)["skin_color"] == "natural"


def test_explicit_current_absence_of_mottling_overrides_profile_and_extremity_label():
    state = patient()
    state["encounter_spec"]["visual_profile"]["baseline"]["mottling"] = True
    state["observable"].update(extremities="Mottled/Cold", visual={"mottling": False})
    assert visual_observations(state)["mottling"] is False
