"""Phase 2 shadow core, P2F: GI repository truth, candidate bands, the Level-2 registry, the frozen
qualitative rules, the deterministic sweep, Appendix A9 and the GI migration-gate dry run.

Nothing here approves a number, migrates GI or reads the family engine to accept a candidate.
"""
import hashlib
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import a9, calibration, gi_reference
from clinical_core.derived import DEFAULT_PROFILE, CoreProfile
from clinical_core.migration import FACULTY, FAMILY_DEFAULT, NOT_REQUIRED, gate_dry_run
from clinical_core.shadow import GOLDEN

#: The digest of everything acceptance depends on, recorded when the rules were re-frozen after the
#: review (docs/PHASE2_SHADOW_CORE.md §12.6; the first freeze, 594e895d..., covered less).
FROZEN_DIGEST = "c7b2f4bb410af2b622f6ed6adc0baf365ab8f2ab618831f087b21880d83a5634"


# P2F-2 / P2F-5 -- repository truth, candidate inference, faculty decision ---------------------

def test_every_inventoried_value_is_on_the_line_it_cites_and_in_the_bank():
    assert gi_reference.verify_inventory() == []
    for case in gi_reference.GI_CASES:
        items = {entry.item for entry in gi_reference.INVENTORY if entry.case == case}
        assert {"rhythm", "hr", "sbp", "dbp", "map", "spo2", "respiratory_rate", "mental_status", "crt_s", "hb_g_dl",
                "lactate_mmol_l", "glucose_mg_dl", "oxygen_support", "pocus_ivc", "active_bleeding",
                "prehospital_therapy", "medications", "temperature_c", "pain"} <= items


def test_the_inventory_says_what_the_cases_do_not_state():
    rows = {(entry.case, entry.item): entry for entry in gi_reference.INVENTORY}
    for case in gi_reference.GI_CASES:
        assert rows[(case, "prehospital_therapy")].value == "not stated"
        assert "not authored by the case" in rows[(case, "potassium")].value
        assert "not stated" in rows[(case, "medications")].note or "does not state" in rows[(case, "medications")].note


def test_truth_candidates_and_decisions_are_kept_apart():
    for case in gi_reference.GI_CASES:
        mapping = gi_reference.reference_mapping(case)
        truth_items = {row["item"] for row in mapping["repository_truth"]}
        assert not truth_items & set(mapping["candidate_inference"]), "no candidate is reported as truth"
        assert all(band["status"] == "CANDIDATE" for band in mapping["candidate_inference"].values())
        assert {"intrinsic_sinus_rate", "arrival_sympathetic_drive", "arrival_oxygen_debt", "arrival_lactate_excess",
                "metabolic_demand_baseline"} <= set(mapping["faculty_decision_required"])


def test_the_arrival_bands_are_independent_of_the_kinetics_and_of_any_history():
    from dataclasses import replace
    for case in gi_reference.GI_CASES:
        canonical = gi_reference.case_bands(case)
        other = gi_reference.case_bands(case, replace(DEFAULT_PROFILE, lactate_per_output_deficit=12.0,
                                                      debt_clearance_tau_min=30.0))
        for name in ("arrival_oxygen_debt", "arrival_lactate_excess", "arrival_delivery_ratio",
                     "intrinsic_sinus_rate", "metabolic_demand_baseline"):
            assert canonical[name] == other[name]
        excess = canonical["arrival_lactate_excess"]
        lactate = gi_reference.authored(case, "lactate_mmol_l")
        assert (excess.lower, excess.upper) == pytest.approx((lactate - 2.0, lactate - 0.8))


def test_reconstructed_histories_are_only_a_labelled_plausibility_probe(monkeypatch):
    histories = gi_reference.pre_arrival_plausibility_probe(3.4, DEFAULT_PROFILE)
    assert all(item.status == "SYNTHETIC_PLAUSIBILITY_PROBE" for item in histories)
    candidate = calibration.GICandidate({"debt_clearance_tau_min": 60.0, "lactate_per_output_deficit": 2.0,
                                         "lactate_clearance_tau_min": 60.0})
    expected = calibration.gi_physiology(candidate)
    assert expected["valid"], "the canonical kinetics are not rejected because no history reproduces the lactate"

    def unavailable(*args, **kwargs):
        raise AssertionError("acceptance must not read the plausibility probe")

    monkeypatch.setattr(gi_reference, "pre_arrival_plausibility_probe", unavailable)
    assert calibration.gi_physiology(candidate) == expected


def test_the_lactate_gain_band_is_not_inferred_from_the_arrival_lactate():
    entry = calibration.REGISTRY["lactate_per_output_deficit"]
    assert entry.lower == 2.0, "the family engine's 2 stays inside the band"
    assert "not inferred from fitting" in entry.rationale
    assert not any("AR2" in item.constraints for item in calibration.REGISTRY.values())


def test_arrival_is_not_required_to_be_in_steady_state():
    candidate = calibration.GICandidate({"debt_clearance_tau_min": 60.0, "lactate_per_output_deficit": 6.0,
                                         "lactate_clearance_tau_min": 120.0}, debt="upper", delivery="lower")
    diagnostics = calibration.gi_diagnostics(candidate)
    assert all(row["steady_state_required"] is False and abs(row["arrival_dD_per_min"]) > 1e-6
               for row in diagnostics.values())
    assert calibration.gi_physiology(candidate)["valid"], "a dynamically evolving arrival is accepted"


# P2F-6 -- oxygen delivery ---------------------------------------------------------------------

def test_delivery_is_dimensionless_relative_and_each_factor_lowers_it():
    assert "dimensionless relative delivery" in calibration.DELIVERY_MODEL
    assert "not an indexed physical DO2" in calibration.DELIVERY_MODEL
    rows = {row["probe"]: row for row in calibration.delivery_probes()}
    for single in ("isolated low output", "isolated anaemia", "isolated hypoxaemia"):
        assert rows[single]["delivery"] < 1.0
    assert rows["low output + anaemia"]["delivery"] == pytest.approx(0.6 * 0.6)
    assert rows["all three"]["delivery"] == pytest.approx(0.6 * 0.6 * 0.85)
    assert rows["all three"]["delivery"] < rows["low output + anaemia"]["delivery"] < rows["isolated anaemia"][
        "delivery"]
    for row in rows.values():
        assert row["deficit_at_demand_1_2"] > row["deficit_at_demand_1"], "higher demand, higher deficit"


def test_hypoxaemia_in_a_run_comes_only_from_fio2_and_lowers_delivery():
    probe = calibration.hypoxaemia_trajectory_probe()
    assert probe["spo2"][1] < probe["spo2"][0] and probe["delivery"][1] < 1.0 and probe["D_at_60"] > 0


# P2F-7 -- registry ----------------------------------------------------------------------------

REQUIRED = {"debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_per_output_deficit",
            "lactate_clearance_tau_min", "arrival_oxygen_debt", "arrival_lactate_excess", "rr_per_lactate",
            "rr_metabolic_max", "rr_ventilatory_floor", "rr_max", "sympathetic_per_pressure_deficit",
            "sympathetic_per_debt", "sympathetic_per_hypoxaemia_point", "sympathetic_per_hypoglycaemia_mg_dl",
            "sympathetic_decay_tau_min", "intrinsic_sinus_rate", "arrival_sympathetic_drive",
            "preload_curve_scale_ml", "preload_fraction", "pump_preload_coupling", "afterload_sensitivity",
            "pump_reserve", "congestion_preload_knee", "congestion_per_excess_preload",
            "lung_water_clearance_tau_min", "collapse_output_threshold", "collapse_burden_per_minute",
            "collapse_burden_limit", "collapse_repayment_tau_min", "collapse_terminal_rhythm",
            "low_output_pressure_knee", "sbp_per_pressure_deficit", "dbp_per_pressure_deficit",
            "metabolic_demand_baseline", "sepsis_demand_multiplier"}


def test_the_registry_holds_every_required_parameter_with_its_fields():
    assert REQUIRED <= set(calibration.REGISTRY)
    for entry in calibration.REGISTRY.values():
        assert entry.status in calibration.STATUSES and entry.rationale and entry.units


def test_nothing_in_the_registry_is_faculty_approved():
    statuses = {entry.status for entry in calibration.REGISTRY.values()}
    assert calibration.FACULTY_APPROVED not in statuses
    assert {name for name, entry in calibration.REGISTRY.items() if entry.status == calibration.SYNTHETIC_ONLY} == {
        "collapse_rule_test_values", "vasodilation_with_demand_probe_factor"}
    assert all(entry.status == calibration.DEFAULT_UNMAPPED for name, entry in calibration.REGISTRY.items()
               if name.endswith("_demand_multiplier"))


def test_every_profile_band_contains_the_canonical_value_or_says_it_is_off():
    for entry in calibration.REGISTRY.values():
        if entry.target == "profile" and entry.lower is not None and entry.canonical is not None:
            assert entry.lower <= entry.canonical <= entry.upper, entry.name


# P2F-8 / P2F-9 -- frozen rules, sweep, no legacy optimization ---------------------------------

def test_the_rules_are_frozen():
    assert calibration.frozen_digest() == FROZEN_DIGEST, (
        "an acceptance rule or a check changed after the rules were frozen: record why, then update the digest")
    covered = {part for name in calibration.CHECKS for part in name.replace("-", "/").split("/")}
    assert {"DL1", "DL2", "DL3", "DL4", "RR1", "HR1", "PL1", "PL4", "PR1", "CO1", "DM1"} <= covered | {"HR1"}
    assert set(calibration.FROZEN_RULES) >= {"DL1", "DL2", "DL3", "DL4", "RR1", "HR1", "HR2", "HR3", "HR4", "PL1",
                                             "PL2", "PL3", "PL4", "PR1", "PR2", "PR3", "CO1", "CO2", "DM1", "AC1",
                                             "AC2"}
    assert "reverted" in calibration.FROZEN_RULES["CO1"].rationale


def test_the_hr_rules_read_the_candidates_full_declared_arrival():
    # Review finding: HR1-HR4 used to run on an arrival that declared only the intrinsic rate. A
    # 72f arrival debt of 60 with a 30-min repayment is above what any deficit can sustain, so the
    # debt's share of the drive falls during the bleed and HR does not rise: the full arrival fails.
    profile = {"debt_clearance_tau_min": 30.0}
    failing = calibration.GICandidate(profile, debt="upper")
    arrivals = {case: gi_reference.candidate_anchors(case, calibration.case_values(case, failing))
                for case in gi_reference.GI_CASES}
    with pytest.raises(calibration.Failed, match=r"HR1 \(gi_bleed_72f\)"):
        calibration.check_hr(replace(DEFAULT_PROFILE, **profile), arrivals=arrivals)
    assert "HR1-HR4" in calibration.gi_physiology(failing)["failed"]
    assert "HR1-HR4" not in calibration.gi_physiology(calibration.GICandidate(profile))["failed"]


def test_dm1_runs_through_the_integrator_and_reads_the_profile():
    # Review finding: DM1 used to test only the arithmetic of max(0, .), whatever the profile.
    source = inspect.getsource(calibration.check_demand)
    assert "run(" in source and "Demand(" in source
    calibration.check_demand(DEFAULT_PROFILE)
    trajectories = []
    original = calibration.run

    def spy(*args, **kwargs):
        trajectories.append(args[3] if len(args) > 3 else kwargs.get("profile"))
        return original(*args, **kwargs)

    calibration.run = spy
    try:
        calibration.check_demand(replace(DEFAULT_PROFILE, debt_clearance_tau_min=30.0))
    finally:
        calibration.run = original
    assert trajectories and all(item.debt_clearance_tau_min == 30.0 for item in trajectories)


def test_the_rules_say_which_ones_construction_already_guarantees():
    guaranteed = {name for name, rule in calibration.FROZEN_RULES.items() if rule.guaranteed}
    assert {"DL1", "DL2", "DL4", "HR3", "HR4", "PR1", "PR2", "DM1", "CO1", "AC1"} <= guaranteed
    assert not {"HR1", "HR2", "PL2", "PL3", "PR3"} & guaranteed


def test_the_canonical_profile_passes_every_frozen_rule():
    assert calibration.physiology({}) == {"valid": True, "failed": {}, "passed": list(calibration.CHECKS)}


def test_a_rejected_candidate_says_why():
    rows = calibration.group_sweep("preload", quick=True)["rows"]
    rejected = [row for row in rows if not row["valid"]]
    assert all(row["failed"] and all(reason for reason in row["failed"].values()) for row in rejected)


def test_acceptance_reads_only_the_physiology():
    results = [{"key": "a", "physiology": {"valid": True}, "legacy_difference": {"x": {"hr": {"mismatched": 99}}},
                "diagnostics": {}},
               {"key": "b", "physiology": {"valid": False}, "legacy_difference": {}, "diagnostics": {}}]
    accepted = calibration.acceptable(results)
    results[0]["legacy_difference"] = {}
    results[1]["legacy_difference"] = {"x": {"hr": {"mismatched": 0}}}
    assert calibration.acceptable(results) == accepted == ["a"]


def test_a_quick_gi_sweep_never_changes_the_canonical_defaults_or_the_golden():
    before = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()
    sweep = calibration.gi_sweep(quick=True, scenarios=("untreated_60", "definitive_management"))
    assert sweep["evaluated"] == 8 and set(sweep) >= {"accepted", "rejected", "rejection_reasons"}
    assert not any(key in json.dumps(sweep["results"][0]) for key in ("best", "selected", "rank"))
    assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == before
    assert DEFAULT_PROFILE == CoreProfile()
    assert dict(gi_reference.canonical_anchors("gi_bleed_57m").declared) == {}
    for result in sweep["results"]:
        assert set(result) == {"key", "candidate", "physiology", "trajectories", "legacy_difference", "diagnostics"}


# P2F-10 -- Appendix A9 ------------------------------------------------------------------------

def test_every_compared_variable_has_a_type_and_no_tolerance():
    assert set(a9.RESIDENT_VISIBLE) == {"sbp", "dbp", "map", "hr", "respiratory_rate", "spo2", "crt_s",
                                        "consciousness_level", "lactate", "hb", "event_timing", "pulse_arrest_state"}
    assert set(a9.INTERNAL) == {"V", "D", "L", "effective_output", "oxygen_demand", "sympathetic_drive",
                                "collapse_burden"}
    assert all(row["tolerance"] == "TBD" for row in a9.table())
    assert {row.comparison for row in a9.A9.values()} <= set(a9.COMPARISON_TYPES)
    with pytest.raises(ValueError):
        a9.Comparison("x", True, a9.BOUNDED_ABSOLUTE, (), "", tolerance=1.0)


# P2F-11 -- GI migration-gate dry run ----------------------------------------------------------

@pytest.mark.parametrize("case", gi_reference.GI_CASES)
def test_the_gi_dry_run_classifies_every_parameter_and_never_migrates(case):
    result = gate_dry_run(case)
    assert result["passes_gate"] is False
    categories = {name: row["category"] for name, row in result["parameters"].items()}
    for name in ("intrinsic_sinus_rate", "arrival_oxygen_debt", "arrival_lactate_excess", "arrival_delivery_ratio",
                 "metabolic_demand_baseline", "preload_fraction"):
        assert categories[name] == FACULTY
    for name in ("beta_blockade", "pump_reserve", "volume_loss_ml_per_min", "fraction_with_ppi"):
        assert categories[name] == FAMILY_DEFAULT
    assert result["not_required"]["reference_preload_fraction"]["category"] == NOT_REQUIRED
    assert len(result["blockers"]) == 12 and set(result["blockers"]) == set(result["parameters"])
    assert "hr" in result["anchors_from_case_truth"] and result["anchors_from_bank_defaults"] == ["k", "rhythm", "fio2"]
    assert not {"rhythm", "fio2"} & set(result["anchors_from_case_truth"])
