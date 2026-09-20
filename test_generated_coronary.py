"""A generated case whose ECG shows an occluded artery runs the bank's pathway.

Faculty decision (2026-09-20): make the declaration mandatory. The gap this closes:
generated cases already executed the bank's orders, but nothing in the generated
engine read their effects, so activating the cath lab in an AI-authored STEMI did
nothing at all.
"""
import pytest

import acs_reperfusion as acs
import coupled_encounter as adapter
from generated_case_schema import collect_clinical_issues
from generated_coronary_consistency import issues
from test_coupled_encounter import patient, run

INFERIOR = {"omi": True, "active_occlusion": True, "territory": "inferior",
            "rv_involvement": False, "pci_capable": True, "symptom_onset_min": 60}


def coronary_case(profile="st_elevation_inferior", **overrides):
    state = patient()
    case = state["encounter_spec"]["clinical_case"]
    case["ecg_profile"] = profile
    case["investigations"].setdefault("troponin", {"duration_min": 10,
                                                   "result": {"value_ng_l": 90, "upper_reference_ng_l": 19}})
    case["engine"]["coronary"] = {**INFERIOR, **overrides}
    return state


def minutes(state, count):
    """Drive the adapter directly: the fixture's own core deteriorates on its own."""
    events = []
    for _ in range(count):
        adapter.tick(state)
        events += state["family_state"].pop("procedure_events", [])
    return events


def codes(case):
    return [issue["code"] for issue in issues(case)]


@pytest.mark.parametrize("profile", sorted(acs.TERRITORY_WALL) and
                         ["st_elevation_anterior", "st_elevation_inferior", "posterior_infarct",
                          "de_winter", "diffuse_st_depression_avr", "wellens"])
def test_an_occlusion_pattern_obliges_the_declaration(profile):
    case = {"ecg_profile": profile, "engine": {}, "investigations": {"troponin": {"result": {"value_ng_l": 90}}}}
    assert codes(case) == ["CORONARY_UNDECLARED"]


def test_a_declared_occlusion_needs_an_ecg_the_resident_can_read():
    case = {"ecg_profile": "baseline", "engine": {"coronary": INFERIOR},
            "investigations": {"troponin": {"result": {"value_ng_l": 90}}}}
    assert codes(case) == ["CORONARY_ECG_MISMATCH"]


@pytest.mark.parametrize("overrides, path", [
    ({"territory": "anterior"}, "case.engine.coronary.territory"),
    ({"active_occlusion": False}, "case.engine.coronary.active_occlusion"),
])
def test_the_declaration_must_match_the_pattern(overrides, path):
    case = {"ecg_profile": "st_elevation_inferior", "engine": {"coronary": {**INFERIOR, **overrides}},
            "investigations": {"troponin": {"result": {"value_ng_l": 90}}}}
    assert [issue["path"] for issue in issues(case)] == [path]


def test_wellens_must_declare_an_open_artery():
    case = {"ecg_profile": "wellens", "engine": {"coronary": {**INFERIOR, "territory": "anterior"}},
            "investigations": {"troponin": {"result": {"value_ng_l": 90}}}}
    assert "CORONARY_ECG_MISMATCH" in codes(case)
    case["engine"]["coronary"]["active_occlusion"] = False
    assert codes(case) == []


def test_right_ventricular_involvement_belongs_to_the_inferior_pattern():
    case = {"ecg_profile": "de_winter",
            "engine": {"coronary": {**INFERIOR, "territory": "anterior", "rv_involvement": True}},
            "investigations": {"troponin": {"result": {"value_ng_l": 90}}}}
    assert [issue["path"] for issue in issues(case)] == ["case.engine.coronary.rv_involvement"]


def test_an_occlusion_case_must_report_a_troponin():
    case = {"ecg_profile": "st_elevation_inferior", "engine": {"coronary": INFERIOR}, "investigations": {}}
    assert codes(case) == ["CORONARY_UNDISCOVERABLE"]


def test_the_gate_is_wired_into_the_contract_and_its_codes_are_reportable():
    import inspect
    from generated_case_validation import CLINICAL_ISSUE_CODES
    source = inspect.getsource(collect_clinical_issues)
    assert "generated_coronary_consistency" in source
    for code in ("CORONARY_UNDECLARED", "CORONARY_ECG_MISMATCH", "CORONARY_UNDISCOVERABLE"):
        assert code in CLINICAL_ISSUE_CODES


def test_activating_the_cath_lab_opens_the_artery_in_a_generated_case():
    state = coronary_case()
    result = run(state, {"type": "consult", "service": "cath lab"})
    note = " ".join(str(s.get("pathway_note") or "") for s in result["action_summaries"])
    assert f"door to balloon {acs.DOOR_TO_BALLOON_MIN} minutes" in note
    events = minutes(state, acs.DOOR_TO_BALLOON_MIN + 5)
    labels = " | ".join(e["label"] for e in events)
    assert state["family_state"]["artery_open_at"] == acs.DOOR_TO_BALLOON_MIN
    assert "atrioventricular block" in labels and "artery is open" in labels
    # The ECG the resident repeats has resolved.
    assert state["ecg_profile"] == acs.RESOLVED_PROFILE


def test_the_infarct_is_felt_as_pressure_and_rate_in_the_generated_surface():
    state = coronary_case()
    minutes(state, acs.AV_BLOCK_AT_MIN - 5)
    sbp, dbp, hr = acs.generated_effects(state["family_state"])
    # Before the block: the failing pump costs pressure and buys rate.
    assert sbp < -1 and dbp < 0 and hr > 0
    minutes(state, 20)
    blocked_sbp, _, blocked_hr = acs.generated_effects(state["family_state"])
    # After it: the rate falls instead, and the pressure falls further.
    assert blocked_hr < 0 and blocked_sbp < sbp
    untouched = patient()
    minutes(untouched, 60)
    assert untouched["family_state"].get("ischemic_min") is None


def test_the_troponin_follows_the_infarct(engine=None):
    state = coronary_case()
    minutes(state, 40)
    result = adapter.collect(state, "troponin", 10)
    assert result["result"]["value_ng_l"] > 90 + acs.TROPONIN_PER_MIN * 30


def test_the_pathway_authorises_its_own_orders_without_an_authored_rule():
    state = coronary_case()
    result = run(state, {"type": "thrombolysis", "agent": "tenecteplase", "dose_mg": 40, "route": "IV"})
    assert result["executed"]
    assert state["family_state"]["reperfusion_method"] == "thrombolysis"


def test_a_generated_case_without_the_declaration_still_refuses_those_orders():
    state = patient()
    from generated_engine import execute_generated_bundle
    result = execute_generated_bundle(state, {"actions": [
        {"type": "thrombolysis", "agent": "tenecteplase", "dose_mg": 40, "route": "IV"}]})
    assert not result["executed"] and "no declared disease-specific response" in result["clarification"]
