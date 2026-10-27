"""Phase 2 shadow core, WP2-4: legacy-versus-core golden trajectories.

The family engine runs the scenario first and alone; the core runs from the same inputs.
Every difference must be one the registry explains (clinical_core.shadow.DIFFERENCES) and
every registered difference must still occur. Tolerances for displayed values are not
agreed (proposal Appendix A9): any displayed difference is reported, none is absorbed.
"""
import json
from copy import deepcopy
from dataclasses import replace

import pytest

from clinical_core.comparison import TBD, VARIABLES, compare, mismatching, summarize
from clinical_core.derived import DEFAULT_PROFILE
from clinical_core.integration import run
from clinical_core.legacy_adapter import (anchors_from_legacy, bank_case, contributors_from_legacy, run_legacy)
from clinical_core.modules import GIHaemorrhage
from clinical_core.shadow import (DECISIONS, DIFFERENCES, DORMANT, EXPECTED_DIFFERENCES, GOLDEN, SCENARIOS, VARIANTS,
                                  ShadowResult, acting_mechanisms, classify, consciousness_attribution,
                                  expected_causes, golden_report, run_shadow)

EXACT = [variable.name for variable in VARIABLES if variable.kind == "exact"]


@pytest.fixture(scope="module")
def results():
    return {f"{v}/{s}": run_shadow(v, s) for v in VARIANTS for s in SCENARIOS}


NO_REFILL = replace(DEFAULT_PROFILE, plasma_refill_target_share=0.0)


def _without_refill(result) -> ShadowResult:
    """The same run with plasma refill off (P2I-2T): V then moves only with the bleed and the orders."""
    core = run(result.core.anchors, result.core.contributors, len(result.core.states) - 1, NO_REFILL)
    rows = compare(result.legacy.snapshots, core.states, core.derived())
    return ShadowResult(result.variant_id, result.scenario, result.legacy, core, rows, summarize(rows))


@pytest.fixture(scope="module")
def without_refill(results):
    return {key: _without_refill(result) for key, result in results.items()}


def test_the_committed_golden_report_is_the_one_the_engines_produce(results):
    produced = json.loads(json.dumps(golden_report(list(results.values())), allow_nan=False))
    assert produced == json.loads(GOLDEN.read_text(encoding="utf-8")), (
        "regenerate with `python -m clinical_core.shadow --write-golden` only after reviewing every difference")


def test_every_difference_is_explained_and_every_explanation_still_applies(results):
    for key, result in results.items():
        assert set(mismatching(result.summary)) == set(EXPECTED_DIFFERENCES[key]), key
    # Run-dependent mechanisms (P2E-2) count where they acted.
    used = {cause for key, result in results.items()
            for causes in expected_causes(key, acting_mechanisms(result.core)).values() for cause in causes}
    assert used == set(DIFFERENCES) - set(DORMANT) and set(DORMANT) <= set(DIFFERENCES)


def test_the_core_reproduces_the_engine_exactly_where_it_adopts_its_arithmetic(results):
    """Volume, haemoglobin, glucose, potassium, FiO2 and delivered amounts, minute by minute."""
    for key, result in results.items():
        allowed = set(EXPECTED_DIFFERENCES[key])
        for name in EXACT:
            if name in allowed:
                continue
            entry = result.summary[name]
            assert entry["mismatched"] == 0 and entry["compared"] == len(result.legacy.snapshots), (key, name)


def test_the_only_exact_quantities_allowed_to_differ_are_the_shared_blood_states(results, without_refill):
    """V and Hb come from the shared blood state (P2I-2T); glucose, K, FiO2 and delivered amounts
    keep the engine's arithmetic. With refill off, V follows the engine's circulation exactly,
    except past the engine's clamp (KD-S4)."""
    for key, result in results.items():
        differing = set(mismatching(result.summary)) & set(EXACT)
        assert differing <= {"V_ml_eq", "hb_g_dl"}, (key, differing)
        alone = without_refill[key].summary
        if "V_ml_eq" in mismatching(alone):
            first = alone["V_ml_eq"]["first_mismatch_minute"]
            assert key.endswith("aggressive_volume"), key
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
    """Control: a core bleeding 10 % faster than the engine must be reported, not absorbed.

    Since P2I-2T refill and the blood composition move V and Hb away from the engine in every
    bleeding run, so the control switches refill off: the core's V then follows the engine's
    circulation exactly, and only the faster bleed can move it.
    """
    legacy = run_legacy("gi_bleed_57m", {}, 30)
    anchors, no_refill = anchors_from_legacy(legacy.arrival), replace(DEFAULT_PROFILE, plasma_refill_target_share=0.0)
    contributors = list(contributors_from_legacy(legacy))
    same = run(anchors, contributors, 30, no_refill)
    assert "V_ml_eq" not in mismatching(summarize(compare(legacy.snapshots, same.states, same.derived())))
    bleed = contributors[0]
    contributors[0] = GIHaemorrhage(bleed.id, bleed.blood_loss_ml_per_min * 1.1, bleed.fraction_with_ppi,
                                    bleed.fraction_after_hemostasis)
    core = run(anchors, contributors, 30, no_refill)
    summary = summarize(compare(legacy.snapshots, core.states, core.derived()))
    assert "V_ml_eq" in mismatching(summary)


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


def test_every_compared_variable_is_classified_and_none_is_left_unresolved(results):
    """Level 3 (P2D-9): MATCH, or a difference whose direction is approved and whose size is TBD."""
    assert set(DECISIONS) == set(DIFFERENCES)
    for key, result in results.items():
        classes = classify(key, result.summary, consciousness_attribution(result), acting_mechanisms(result.core))
        compared = {name for name, entry in result.summary.items() if entry["compared"]}
        different = set(mismatching(result.summary))
        assert set(classes) == compared, key
        assert {n for n, c in classes.items() if c["classification"] == "APPROVED_DIRECTION_MAGNITUDE_TBD"} \
            == different, key
        assert {n for n, c in classes.items() if c["classification"] == "MATCH"} == compared - different, key
        assert all(c["candidate_causes"] for n, c in classes.items() if n in different), key
        assert all(not c["candidate_causes"] for n, c in classes.items() if n not in different), key


def test_no_class_claims_an_approved_magnitude():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    labels = {item["classification"] for entry in golden["scenarios"].values()
              for item in entry["classification"].values()}
    assert labels <= {"MATCH", "APPROVED_DIRECTION_MAGNITUDE_TBD", "UNRESOLVED"}
    assert "APPROVED DIFFERENCE" not in GOLDEN.read_text(encoding="utf-8")


def test_a_difference_without_an_approved_decision_stays_unresolved(results):
    result = results["gi_bleed_72f/oxygen_non_rebreather"]
    summary = {name: dict(entry) for name, entry in result.summary.items()}
    summary["spo2"]["mismatched"] = 1              # a difference no decision explains
    summary["hr"]["mismatched"] = 1                # an expected variable elsewhere, but not in this run
    classes = classify(result.key, summary)
    assert classes["spo2"] == {"classification": "UNRESOLVED", "candidate_causes": []}
    assert classes["hr"]["classification"] == "UNRESOLVED"


def test_the_mental_status_difference_is_attributed_minute_by_minute(without_refill):
    """57m untreated with refill off (the pressure path before P2I-2T), minutes 55-60: the raw
    reading (KD-S3) and the lower pressure (KD-S4). The golden run no longer crosses the threshold
    (``DORMANT``), so the attribution is exercised here."""
    result = without_refill["gi_bleed_57m/untreated_60"]
    rows = {row["minute"]: row for row in consciousness_attribution(result)}
    assert sorted(rows) == [55, 56, 57, 58, 59, 60]
    assert {m: rows[m]["mode"] for m in rows} == {55: "jointly_necessary", 56: "jointly_necessary",
                                                 57: "jointly_necessary", 58: "sufficient_alone",
                                                 59: "sufficient_alone", 60: "each_sufficient"}
    assert rows[58]["candidate_causes"] == rows[59]["candidate_causes"] == ["KD-S4"]
    assert all(rows[m]["candidate_causes"] == ["KD-S3", "KD-S4"] for m in (55, 56, 57, 60))
    entry = classify("gi_bleed_57m/untreated_60", result.summary, list(rows.values()))["consciousness_level"]
    assert entry["candidate_causes"] == ["KD-S3", "KD-S4"] and len(entry["by_minute"]) == 6


def test_the_engine_raw_pressure_the_attribution_uses_rounds_to_what_the_engine_shows(results):
    for key, result in results.items():
        arrival = result.legacy.snapshots[0]
        for snap in result.legacy.snapshots:
            raw = result.core.anchors.sbp - 45.0 * (snap["circulation"] - arrival["circulation"])
            if snap["pulse_present"] and 50 < raw < 240 and key.endswith("untreated_60"):
                assert abs(raw - snap["sbp"]) <= 0.5 + 1e-9, (key, snap["minute"])


def test_a_rounding_tie_needs_both_sides_on_the_same_boundary(results):
    """A raw value on a .5 boundary ties with either neighbour, and with nothing further away.

    Whether the runs produce a tie follows the physiology, so the tie is placed here by hand:
    the core's diastolic at minute 20 is set to 52.5.
    """
    from dataclasses import replace
    result = results["gi_bleed_57m/untreated_60"]
    derived = list(result.core.derived())
    derived[20] = replace(derived[20], dbp=52.5)
    snapshots = [dict(snap) for snap in result.legacy.snapshots]
    statuses = {}
    for legacy in (52, 53, 54):
        snapshots[20]["dbp"] = legacy
        statuses[legacy] = compare(snapshots, result.core.states, derived)["dbp"][20]["status"]
    assert statuses == {52: "match", 53: "rounding_tie", 54: "mismatch"}


def test_an_unknown_legacy_label_is_a_mismatch_not_silence(results):
    result = results["gi_bleed_57m/untreated_60"]
    snapshots = [dict(snap) for snap in result.legacy.snapshots]
    snapshots[10]["rhythm"], snapshots[11]["mental_status"] = "Atrial flutter", "Confused"
    rows = compare(snapshots, result.core.states, result.core.derived())
    assert rows["rhythm"][10]["status"] == "mismatch" and rows["consciousness_level"][11]["status"] == "mismatch"


def test_untimed_orders_queued_bags_and_stops_follow_the_engine_exactly(results, without_refill):
    """Delivered amounts always; and with refill off, V too (Hb is the blood state's, P2I-2T)."""
    for variant in VARIANTS:
        for scenario in ("untimed_shared_line", "queued_timed_bags", "stop_fluids"):
            key = f"{variant}/{scenario}"
            assert all(results[key].summary[name]["mismatched"] == 0 for name in EXACT
                       if name not in ("V_ml_eq", "hb_g_dl")), key
            assert all(without_refill[key].summary[name]["mismatched"] == 0 for name in EXACT
                       if name != "hb_g_dl"), key
