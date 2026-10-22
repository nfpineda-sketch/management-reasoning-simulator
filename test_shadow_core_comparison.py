"""Phase 2 shadow core, WP2-4: legacy-versus-core golden trajectories.

The family engine runs the scenario first and alone; the core runs from the same inputs.
Every difference must be one the registry explains (clinical_core.shadow.DIFFERENCES) and
every registered difference must still occur. Tolerances for displayed values are not
agreed (proposal Appendix A9): any displayed difference is reported, none is absorbed.
"""
import json
from copy import deepcopy

import pytest

from clinical_core.comparison import TBD, VARIABLES, compare, mismatching, summarize
from clinical_core.integration import run
from clinical_core.legacy_adapter import (anchors_from_legacy, bank_case, contributors_from_legacy, run_legacy)
from clinical_core.modules import GIHaemorrhage
from clinical_core.shadow import (DIFFERENCES, EXPECTED_DIFFERENCES, GOLDEN, SCENARIOS, VARIANTS, golden_report,
                                  run_shadow)

EXACT = [variable.name for variable in VARIABLES if variable.kind == "exact"]


@pytest.fixture(scope="module")
def results():
    return {f"{v}/{s}": run_shadow(v, s) for v in VARIANTS for s in SCENARIOS}


def test_the_committed_golden_report_is_the_one_the_engines_produce(results):
    produced = json.loads(json.dumps(golden_report(list(results.values())), allow_nan=False))
    assert produced == json.loads(GOLDEN.read_text(encoding="utf-8")), (
        "regenerate with `python -m clinical_core.shadow --write-golden` only after reviewing every difference")


def test_every_difference_is_explained_and_every_explanation_still_applies(results):
    for key, result in results.items():
        assert set(mismatching(result.summary)) == set(EXPECTED_DIFFERENCES[key]), key
    used = {reason for expected in EXPECTED_DIFFERENCES.values() for reason in expected.values()}
    assert used == set(DIFFERENCES)


def test_the_core_reproduces_the_engine_exactly_where_it_adopts_its_arithmetic(results):
    """Volume, haemoglobin, glucose, potassium, FiO2 and delivered amounts, minute by minute."""
    for key, result in results.items():
        allowed = set(EXPECTED_DIFFERENCES[key])
        for name in EXACT:
            if name in allowed:
                continue
            entry = result.summary[name]
            assert entry["mismatched"] == 0 and entry["compared"] == len(result.legacy.snapshots), (key, name)


def test_the_only_exact_quantity_allowed_to_differ_is_volume_past_the_engine_clamp(results):
    for key, result in results.items():
        differing = set(mismatching(result.summary)) & set(EXACT)
        assert differing <= {"V_ml_eq"}, (key, differing)
        if differing:
            first = result.summary["V_ml_eq"]["first_mismatch_minute"]
            assert result.legacy.snapshots[first]["circulation"] == pytest.approx(0.25)


def test_no_displayed_quantity_is_given_an_invented_tolerance():
    for variable in VARIABLES:
        if variable.kind == "display":
            assert variable.tolerance == TBD, variable.name


def test_rounding_ties_are_reported_separately_never_as_matches(results):
    for result in results.values():
        for name, entry in result.summary.items():
            for minute in entry["rounding_tie_minutes"]:
                row = result.rows[name][minute]
                assert row["status"] == "rounding_tie" and row["legacy"] != row["core"]
                assert abs(row["core"] - row["legacy"]) <= 1


def test_the_comparison_catches_a_core_that_drifts():
    """Control: a core bleeding 10 % faster than the engine must be reported, not absorbed."""
    legacy = run_legacy("gi_bleed_57m", {}, 30)
    contributors = list(contributors_from_legacy(legacy))
    bleed = contributors[0]
    contributors[0] = GIHaemorrhage(bleed.id, bleed.volume_loss_ml_per_min * 1.1, bleed.hb_loss_g_dl_per_min * 1.1,
                                    bleed.fraction_with_ppi, bleed.fraction_after_hemostasis)
    core = run(anchors_from_legacy(legacy.arrival), contributors, 30)
    summary = summarize(compare(legacy.snapshots, core.states, core.derived()))
    assert {"V_ml_eq", "hb_g_dl"} <= set(mismatching(summary))


def test_one_minute_steps_do_not_change_the_family_engine():
    """The harness drives the engine a minute at a time; a single turn of the same length gives the same patient."""
    from family_engine import execute_family_bundle
    from family_parser import parse_family_actions
    stepped = run_legacy("gi_bleed_72f", SCENARIOS["prbc_2u_over_60"]["orders"], 90).final_state
    chunked = bank_case("gi_bleed_72f")
    execute_family_bundle(chunked, parse_family_actions(
        SCENARIOS["prbc_2u_over_60"]["orders"][0] + " Reassess in 90 minutes."))
    assert chunked["sim_time"] == stepped["sim_time"] == 90
    for name in ("circulation", "hemoglobin", "glucose", "fluid_delivered_ml", "blood_delivered_units", "lactate"):
        assert chunked["family_state"][name] == pytest.approx(stepped["family_state"][name], abs=1e-9), name
    for name in ("sbp", "dbp", "map", "hr", "spo2", "respiratory_rate", "crt", "mental_status", "rhythm"):
        assert chunked["observable"][name] == stepped["observable"][name], name


def test_the_shadow_runs_are_deterministic():
    one, two = run_shadow("gi_bleed_57m", "definitive_management"), run_shadow("gi_bleed_57m", "definitive_management")
    assert one.core.digest() == two.core.digest()
    assert one.legacy.snapshots == two.legacy.snapshots and one.rows == two.rows


def test_unsupported_orders_are_refused_not_dropped():
    from clinical_core.legacy_adapter import UnsupportedScenario
    with pytest.raises(UnsupportedScenario):
        contributors_from_legacy(run_legacy("gi_bleed_57m", {0: "Give tranexamic acid 1 g IV."}, 2))


def test_the_scenarios_cover_the_first_family_and_its_interventions():
    kinds = {spec["type"] for result_key in ("gi_bleed_57m/definitive_management", "gi_bleed_57m/saline_then_blood",
                                             "gi_bleed_57m/oxygen_non_rebreather")
             for spec in json.loads(GOLDEN.read_text(encoding="utf-8"))["scenarios"][result_key]["core_inputs"]}
    assert kinds == {"gi_haemorrhage", "packed_red_cells", "proton_pump_inhibitor", "endoscopic_hemostasis",
                     "crystalloid", "oxygen"}
    assert deepcopy(SCENARIOS) == SCENARIOS


# Hardening found by the adversarial review of 2026-10-21 -----------------------------

def test_an_order_held_until_a_result_is_refused_not_misplaced():
    from clinical_core.legacy_adapter import UnsupportedScenario
    legacy = run_legacy("gi_bleed_57m", {0: "Order a lactate and wait for the result, then give pantoprazole 80 mg IV."}, 3)
    with pytest.raises(UnsupportedScenario):
        contributors_from_legacy(legacy)


@pytest.mark.parametrize("orders", [{"0": "Give 1000 mL normal saline IV."}, {30: "Give 1000 mL normal saline IV."},
                                    {-1: "Give 1000 mL normal saline IV."}, {0: "  "}])
def test_an_order_the_run_would_never_reach_is_refused(orders):
    from clinical_core.legacy_adapter import UnsupportedScenario
    with pytest.raises(UnsupportedScenario):
        run_legacy("gi_bleed_57m", orders, 30)


def test_a_rounding_tie_needs_both_sides_on_the_same_boundary(results):
    """Any tie the runs produce (which variable and minute follows the physiology) stops being one 2 units away."""
    result, name, row = next((result, name, row) for result in results.values()
                             for name, rows in result.rows.items() for row in rows
                             if row["status"] == "rounding_tie")
    minute = row["minute"]
    snapshots = [dict(snap) for snap in result.legacy.snapshots]
    snapshots[minute][name] = row["legacy"] + 2     # x.5 cannot round to two units away
    rows = compare(snapshots, result.core.states, result.core.derived())
    assert rows[name][minute]["status"] == "mismatch"


def test_an_unknown_legacy_label_is_a_mismatch_not_silence(results):
    result = results["gi_bleed_57m/untreated_60"]
    snapshots = [dict(snap) for snap in result.legacy.snapshots]
    snapshots[10]["rhythm"], snapshots[11]["mental_status"] = "Atrial flutter", "Confused"
    rows = compare(snapshots, result.core.states, result.core.derived())
    assert rows["rhythm"][10]["status"] == "mismatch" and rows["consciousness_level"][11]["status"] == "mismatch"


def test_untimed_orders_queued_bags_and_stops_follow_the_engine_exactly(results):
    for variant in VARIANTS:
        for scenario in ("untimed_shared_line", "queued_timed_bags", "stop_fluids"):
            summary = results[f"{variant}/{scenario}"].summary
            assert all(summary[name]["mismatched"] == 0 for name in EXACT), (variant, scenario)
