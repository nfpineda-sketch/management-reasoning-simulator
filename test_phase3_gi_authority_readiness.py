"""P3-193 to P3-198: the authority surface inventory, the future experiment's design, the failure contract, the UnresolvedBoundary audit, the
counterfactual harness and the readiness checkpoint.

Nothing here enables authority. ``COMMON_CORE_RUNTIME_AUTHORITY`` stays False, the gate stays closed, no snapshot is registered, no terminal
rule is declared and no encounter is terminated. What is proved is that the RECORD says what the code says: each claim of the record that can
be recomputed from the code or from a live encounter is recomputed here.
"""
import inspect
import json
import types
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_gi_amendment_2_series as series
import test_gi_authority_surface as surface
import test_gi_counterfactual as cf
import test_gi_snapshot_analysis as an
from clinical_core import comparison

ROOT = Path(__file__).resolve().parent
READINESS = json.loads((ROOT / surface.READINESS_FILE).read_text(encoding="utf-8"))
COUNTERFACTUAL = json.loads((ROOT / cf.COUNTERFACTUAL_FILE).read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / an.SNAPSHOT_FILE).read_text(encoding="utf-8"))
REQUIRED = COUNTERFACTUAL["required_runs"]


# -- nothing is enabled ------------------------------------------------------------------------------------------------------------------------

def test_the_record_enables_no_authority_and_the_gate_stays_closed():
    assert READINESS["authority"] == {"enabled": False, "common_core_runtime_authority": False, "granted_by_this_record": False}
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    decision = authority.gate({}, environ={}, unsupported=())
    assert decision.granted is False
    assert sorted(authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    assert authority.AUTHORITY_DOMAIN == ("sbp", "dbp", "map")
    assert COUNTERFACTUAL["non_interference"] == {"common_core_runtime_authority": False, "authority_gate_granted_without_flags": False,
                                                  "gate_refusal_reasons_count": 4}


def test_no_runtime_module_imports_or_names_the_analysis_modules_or_the_snapshot():
    names = ("test_gi_snapshot_analysis", "test_gi_counterfactual", "test_gi_authority_surface", "GI_DEVELOPMENT_SNAPSHOT")
    for path in ROOT.glob("*.py"):
        if path.name.startswith(("test_", "regression_")):
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(name in text for name in names), path.name


# -- P3-193: the inventory, checked against the code ---------------------------------------------------------------------------------------------

def test_the_inventory_covers_every_required_output_with_a_legal_class():
    rows = READINESS["inventory"]
    assert set(READINESS["classes"]) == set(surface.CLASSES)
    assert all(row["common_class"] in surface.CLASSES for row in rows)
    text = " ".join(row["output"].lower() for row in rows)
    for needle in ("sbp", "heart rate", "pulse", "spo2", "lactate", "haemoglobin", "consciousness", "collapse", "terminal", "respiratory support"):
        assert needle in text, needle
    by_output = {row["output"]: row["common_class"] for row in rows}
    assert by_output["terminal state (arrest / terminalisation from the common core)"] == surface.UNRESOLVED_BOUNDARY
    assert by_output["consciousness category (mental status)"] == surface.CERTIFIED_NOT_AUTHORIZED
    assert by_output["respiratory support / work of breathing / extremities"] == surface.MISSING


def test_the_ownership_contract_today_gives_pressure_to_the_common_core_and_everything_else_to_the_legacy_engine():
    owners = authority.ownership()
    assert (owners["sbp"], owners["dbp"], owners["map"]) == (authority.COMMON, authority.COMMON, authority.DERIVED_IN_DISPLAY)
    for name in ("hr", "spo2", "respiratory_rate", "lactate_mmol_l", "hb_g_dl", "crt_s", "consciousness_level", "pulse_present", "rhythm"):
        assert owners[name] == authority.LEGACY, name
    assert {owners[name] for name in ("D", "delivery_rel", "hemostasis_relief", "transfusion_overload_units")} == {authority.COMPARISON_ONLY}
    assert "consciousness_level" in {variable.name for variable in comparison.VARIABLES}


def test_the_transaction_machinery_is_pressure_specific_exactly_where_the_record_says_it_is():
    source = inspect.getsource(authority.AuthorityTransaction.commit)
    assert "isinstance(value, bool) or not isinstance(value, (int, float))" in source        # a categorical field is rejected today
    names = [item for item in ("snapshot_approved", "domain_coherent", "case_eligible", "candidate_complete", "invariants_hold", "no_core_failure",
                               "no_unresolved_boundary", "supported_management", "minute_reproducible", "no_legacy_arrest")
             if f'"{item}"' in inspect.getsource(authority.AuthorityTransaction.validate)]
    assert len(names) == 10
    assert "tuple(self.domain) == AUTHORITY_DOMAIN" in inspect.getsource(authority.AuthorityTransaction.validate)


def test_the_readers_of_mental_status_are_exactly_the_recorded_modules():
    assert surface.mental_status_consumers(str(ROOT)) == READINESS["mental_status_consumers"]
    assert {"family_engine.py", "app.py", "management_trace_analysis.py", "image_consistency.py"} <= set(READINESS["mental_status_consumers"])
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert "glucose_rescue.ORAL_SAFE_MENTAL" in engine and 'validation_state.get("observable", {}).get("mental_status")' in engine
    # the oral route is not one of the actions a pressure authority supports: the engine's own reader is out of the supported set
    assert "oral_carbohydrate" not in authority.SUPPORTED_ACTIONS


# -- P3-193A and P3-194A: the prior experiment and the ranking -------------------------------------------------------------------------------------

def test_the_prior_pressure_authority_is_reconciled_with_what_the_code_holds_today():
    prior = READINESS["prior_pressure_authority"]
    assert prior["registry_today"] == sorted(authority.APPROVED_SNAPSHOTS)
    assert authority.FAILURE_POLICY == "HARD_FAIL_VISIBLE_TO_FACULTY" and "HARD_FAIL_VISIBLE_TO_FACULTY" in " ".join(prior["validated"])
    assert authority.AUTHORITY_CASES == ("gi_bleed_57m", "gi_bleed_72f") and authority.ALLOWED_ENVIRONMENTS == ("development", "faculty")
    assert rs.PHASE2_DIGEST.startswith("22b90a6f") and "22b90a6f" in prior["ran_on"]
    assert rs.CORE_LINEAGE[-1].version_id == "PHASE2_AMENDMENT_2" and "a0af7d08" in prior["ran_on"]
    assert any("consciousness, collapse or any other output" in item for item in prior["not_established"])


def test_the_ranking_puts_pressure_first_consciousness_only_with_it_collapse_record_only_and_the_terminal_state_last():
    ranking = READINESS["candidate_domain_ranking"]
    assert [item["rank"] for item in ranking] == [1, 2, 3, 4, 5]
    assert ranking[0]["domain"].startswith("pressure") and ranking[0]["readiness"] == "MACHINERY_READY"
    assert "ONLY together with pressure" in ranking[1]["domain"]
    assert ranking[2]["readiness"] == "RECORD_ONLY" and ranking[3]["readiness"] == "BLOCKED"


# -- P3-194 and P3-195: the design and the failure contract ----------------------------------------------------------------------------------------------

def test_the_design_is_bounded_bound_to_the_snapshot_and_writes_only_the_declared_pair():
    design = READINESS["design"]
    assert design["scope"]["cases"] == list(authority.AUTHORITY_CASES) and design["scope"]["environments"] == list(authority.ALLOWED_ENVIRONMENTS)
    assert design["scope"]["pilot"] == "excluded" and design["scope"]["resident"] == "excluded" and design["scope"]["scoring"].startswith("legacy")
    assert design["scope"]["record_only"] == ["collapse state"]
    assert not set(design["scope"]["never_written"]) & {"sbp", "dbp", "mental_status"}
    binding = design["snapshot_binding"]
    assert binding["snapshot_id"] == an.SNAPSHOT_ID == SNAPSHOT["snapshot_id"] and binding["registered_as_authority"] is False
    assert {"snapshot_id", "identity_digest", "record_digest"} <= set(binding["bound_by"])
    assert "never from the names" in binding["no_implicit_defaults"]
    assert len(design["stages"]) == 4 and design["stages"][0].startswith("0.") and "WITHOUT commit" in design["stages"][2]
    assert "one transaction or not at all" in design["no_mixed_trajectory"]


def test_the_failure_contract_covers_the_eight_required_failures_and_fails_closed_in_both_phases():
    rows = {row["failure"]: row for row in READINESS["failure_contract"]["rows"]}
    assert set(rows) == {"lineage mismatch", "snapshot mismatch", "unsupported action", "unresolved boundary", "common-core invariant failure", "replay mismatch",
                         "partial output failure", "trace persistence failure"}
    for row in rows.values():
        assert row["before_first_commit"] and row["after_first_commit"] and row["detects"]
        assert row["exists"] in (True, "partly")
        # after authority begins: a halt, never a switch back to the legacy engine
        assert "halt" in row["after_first_commit"].lower() or "HALT" in row["after_first_commit"] or "ABORTED" in row["after_first_commit"]
        assert "legacy" not in row["after_first_commit"].lower().replace("no silent switch to legacy", "")
    assert any("fails CLOSED" in rule for rule in READINESS["failure_contract"]["rules"])
    assert any("no silent fallback after the first authoritative commit" in rule for rule in READINESS["failure_contract"]["rules"])
    # the constants the contract names exist
    for name in ("EXPERIMENT_HALTED", "INVALID_FOR_CONTINUATION", "CONFIGURATION_CHANGED", "UNSUPPORTED_AUTHORITY_ACTION", "FAILURE_POLICY"):
        assert hasattr(authority, name), name
    assert callable(getattr(authority, "unsupported_among"))
    assert {"phase2_digest", "no_unsupported_action"} <= set(authority.GATE_CONDITIONS)


def test_a_transaction_that_meets_an_unresolved_boundary_aborts_writes_nothing_and_leaves_a_rollback_artifact():
    transaction = authority.AuthorityTransaction(minute=349, case_id="gi_bleed_57m")
    failure = types.SimpleNamespace(classification=rs.BOUNDARY)
    assert transaction.validate(failures=[failure]) is False
    assert "no_unresolved_boundary" in transaction.failures
    assert transaction.state == authority.ABORTED and transaction.committed == ()
    assert transaction.rollback is not None and transaction.rollback["failure_policy"] == "HARD_FAIL_VISIBLE_TO_FACULTY"
    assert transaction.rollback["committed"] == [] and "never continue the same encounter with the other engine" in transaction.rollback["rescue"]
    with pytest.raises(authority.AuthorityRefused):
        transaction.commit({"sim_time": 349})


# -- P3-196: the boundary --------------------------------------------------------------------------------------------------------------------------------

def test_the_boundary_audit_record_says_where_it_falls_who_reaches_it_and_why_the_window_can_be_bounded():
    audit = READINESS["boundary_audit"]
    assert audit["verdict"] == surface.BOUNDARY_VERDICT == "AUTHORITY_WINDOW_CAN_BE_SAFELY_BOUNDED_BEFORE_BOUNDARY"
    assert audit["verdict"] in audit["verdict_options"] and audit["proposed_window_minutes"] == 240
    assert [(item["case"], item["scenario"]) for item in audit["scenarios_reaching_it"]] == [("gi_bleed_57m", "untreated_long"), ("gi_bleed_72f", "untreated_long")]
    assert len(audit["scenarios_not_reaching_it"]) == 16
    for case, item in audit["cases"].items():
        assert (item["boundary_minute"], item["exception"], item["classification"]) == (349, "UnresolvedBoundary", "COMMON_BOUNDARY")
        assert item["margin_to_the_proposed_window_minutes"] == 109 and item["boundary_after_established_collapse_minutes"] == 142
        assert item["snapshot_witness_unresponsive_at"] == 158 and item["snapshot_witness_established_collapse_at"] == 207
        assert item["last_recorded_minute_of_every_common_run"] == 348
        assert item["legacy_at_the_boundary"]["arrested"] is False and item["legacy_at_the_boundary"]["pulse_present"] is True
        assert item["message_start"].startswith("minute 349: effective output reached zero while a pulse is present")
        assert set(item["failing_runs"]) == {"core", "ensemble:LOW:core", "ensemble:CENTER_REFERENCE:core", "ensemble:HIGH:core"}
    # the common pressure is already below the legacy engine's own minimum long before the boundary
    assert audit["cases"]["gi_bleed_57m"]["legacy_sbp_minimum"] == 50 and audit["cases"]["gi_bleed_72f"]["legacy_sbp_minimum"] == 58
    assert audit["cases"]["gi_bleed_57m"]["common_sbp_first_below"]["40"] == 194 and audit["cases"]["gi_bleed_72f"]["common_sbp_first_below"]["40"] == 211
    assert "no terminal rule" not in audit["reading"].lower() or "none is invented here" in audit["reading"]


def test_a_live_untreated_course_reaches_the_boundary_at_minute_349_and_nothing_terminates_the_legacy_encounter():
    captured = an.capture("gi_bleed_57m", "untreated_long", SNAPSHOT["values"])
    assert captured["minutes_played"] == 349
    failures = {item["where"]: item for item in captured["failures"]}
    assert set(failures) == {"core", "ensemble:LOW:core", "ensemble:CENTER_REFERENCE:core", "ensemble:HIGH:core"}
    assert {item["minute"] for item in failures.values()} == {349} and {item["classification"] for item in failures.values()} == {"COMMON_BOUNDARY"}
    assert failures["core"]["message"].startswith("minute 349: effective output reached zero while a pulse is present")
    assert max(row["minute"] for row in captured["session"]) == 348 and captured["legacy_arrested"] is False
    assert captured["legacy"][-1]["pulse_present"] is True and captured["legacy"][-1]["arrested"] is False
    middle = captured["witnesses"]["CENTER_REFERENCE"]
    assert next(row["minute"] for row in middle if row["collapse_state_index"] >= 2) == 207
    assert next(row["minute"] for row in middle if row["category_index"] >= 3) == 158


# -- P3-197: the counterfactual ----------------------------------------------------------------------------------------------------------------------------

def test_the_record_covers_both_cases_and_all_seven_scenarios_plus_the_two_extras_and_names_the_snapshot():
    assert sorted(REQUIRED) == sorted(f"{case}/{scenario}" for case in an.CASES for scenario in an.SCENARIOS)
    assert sorted(COUNTERFACTUAL["extra_runs"]) == sorted(f"{case}/{scenario}" for case in an.CASES for scenario in an.EXTRA_SCENARIOS)
    assert COUNTERFACTUAL["snapshot_id"] == an.SNAPSHOT_ID and COUNTERFACTUAL["snapshot_record_digest"] == SNAPSHOT["immutability"]["record_digest"]
    assert set(COUNTERFACTUAL["class_codes"].values()) == set("MSPEU")
    assert set(cf.DOMAINS) == set(next(iter(REQUIRED.values()))["domains"])
    for domain, spec in COUNTERFACTUAL["domains"].items():
        assert spec["candidate_source"] and spec["legacy_source"], domain


def test_every_class_code_of_every_run_and_domain_re_derives_from_the_stored_columns():
    for runs in (REQUIRED, COUNTERFACTUAL["extra_runs"]):
        for key, run in runs.items():
            for domain, item in run["domains"].items():
                again = cf.classify_columns(domain, run["minutes"], item["legacy"], item["candidate"], run["first_order_minute"], run["legacy_pulse"])
                assert again == item["class_codes"], (key, domain)
                assert {cf.CLASS_OF[code]: again.count(code) for code in set(again)} == item["counts"], (key, domain)
                for label, windows in item["flagged_windows"].items():
                    wanted = cf.CODE[label]
                    assert windows == cf.windows_of(run["minutes"], again, wanted), (key, domain, label)


def test_the_summary_is_the_sum_of_the_runs_and_the_required_minutes_are_1930():
    totals = {}
    for run in REQUIRED.values():
        for domain, item in run["domains"].items():
            for label, count in item["counts"].items():
                totals.setdefault(domain, {}).setdefault(label, 0)
                totals[domain][label] += count
    assert totals == COUNTERFACTUAL["summary_required"]["minutes_by_class"]
    assert sum(len(run["minutes"]) for run in REQUIRED.values()) == 1930
    for domain, counts in totals.items():
        assert sum(counts.values()) == 1930, domain


def test_the_classification_is_structural_and_the_pulse_and_the_oxygen_saturation_agree_everywhere():
    totals = COUNTERFACTUAL["summary_required"]["minutes_by_class"]
    assert totals["pulse_present"] == {"MATCH": 1930} and totals["spo2"] == {"MATCH": 1930}
    assert totals["consciousness_category"] == {"MATCH": 1224, "POTENTIAL_EDUCATIONAL_PROBLEM": 461, "EXPECTED_MECHANISTIC_DIFFERENCE": 245}
    assert totals["respiratory_rate"]["STRUCTURAL_CONTRADICTION"] == 55 and totals["lactate"]["STRUCTURAL_CONTRADICTION"] == 62
    assert totals["hr"]["STRUCTURAL_CONTRADICTION"] == 3 and totals["sbp"]["STRUCTURAL_CONTRADICTION"] == 12 and totals["crt"]["STRUCTURAL_CONTRADICTION"] == 8
    assert "STRUCTURAL_CONTRADICTION" not in totals["hb"] and totals["hb"] == {"EXPECTED_MECHANISTIC_DIFFERENCE": 1930}
    assert set(totals["collapse_state"]) == {"MATCH", "UNRESOLVED"}


def test_the_two_engines_never_disagree_on_a_deterioration_and_every_opposite_direction_follows_a_first_order():
    for key, run in REQUIRED.items():
        for domain, item in run["domains"].items():
            windows = item["flagged_windows"]["STRUCTURAL_CONTRADICTION"]
            if run["first_order_minute"] is None:
                assert windows == [], (key, domain)
            for start, _ in windows:
                assert run["first_order_minute"] is not None and start > run["first_order_minute"], (key, domain)


def test_collapse_is_unresolved_exactly_where_the_snapshot_reads_impending_or_established_and_matches_where_it_reads_none():
    for key, run in REQUIRED.items():
        item = run["domains"]["collapse_state"]
        for minute, code, candidate in zip(run["minutes"], item["class_codes"], item["candidate"]):
            assert (code == "U") == (candidate in (1, 2)), (key, minute)
            assert (code == "M") == (candidate == 0), (key, minute)


def test_an_early_treatment_leaves_both_engines_alert_and_the_consciousness_differences_live_in_the_untreated_and_deteriorating_courses():
    for key in ("gi_bleed_57m/early_treatment", "gi_bleed_72f/early_treatment", "gi_bleed_57m/blood_focused", "gi_bleed_72f/blood_focused"):
        assert REQUIRED[key]["domains"]["consciousness_category"]["counts"] == {"MATCH": len(REQUIRED[key]["minutes"])}, key
    untreated = REQUIRED["gi_bleed_57m/untreated"]["domains"]["consciousness_category"]
    assert untreated["flagged_windows"]["POTENTIAL_EDUCATIONAL_PROBLEM"][0] == [63, 108]
    assert untreated["first_difference_minute"] == 63


@pytest.mark.parametrize("scenario", ["early_treatment", "severe_deterioration"])
def test_a_live_encounter_reproduces_the_stored_columns_and_codes_for_every_domain(scenario):
    captured = an.capture("gi_bleed_57m", scenario, SNAPSHOT["values"])
    again = json.loads(json.dumps(cf.compare_run(captured)))
    stored = REQUIRED[f"gi_bleed_57m/{scenario}"]
    assert again["minutes"] == stored["minutes"] and again["first_order_minute"] == stored["first_order_minute"]
    for domain, item in again["domains"].items():
        assert item["legacy"] == stored["domains"][domain]["legacy"], domain
        assert item["candidate"] == stored["domains"][domain]["candidate"], domain
        assert item["class_codes"] == stored["domains"][domain]["class_codes"], domain


def test_reading_the_shadow_beside_the_legacy_engine_does_not_change_the_legacy_trajectory():
    def run(mode):
        samples = []
        with ev.shadow(mode):
            encounter = acceptance.Encounter("gi_bleed_57m")
            samples.append(series._legacy_sample(encounter))
            encounter.order(" ".join((series.ACCESS, series.SALINE, series.BLOOD)))
            samples.append(series._legacy_sample(encounter))
            while int(encounter.minute) < 100:
                before = int(encounter.minute)
                encounter.wait_until(before + 1, step=1)
                samples.append(series._legacy_sample(encounter))
                if int(encounter.minute) == before:
                    break
        return samples, encounter.shadow
    observed, session = run(rs.MODE_SHADOW_COMPARE)
    alone, nothing = run(rs.MODE_OFF)
    assert session is not None and nothing is None
    assert observed == alone and len(observed) > 40


# -- P3-198: the checkpoint ---------------------------------------------------------------------------------------------------------------------------------

def test_the_checkpoint_returns_exactly_one_legal_verdict_and_grants_nothing():
    checkpoint = READINESS["checkpoint"]
    assert checkpoint["verdict"] == surface.READINESS_VERDICT and checkpoint["verdict"] in checkpoint["options"]
    assert len(checkpoint["options"]) == 4 and checkpoint["verdict"] == checkpoint["options"][0]
    assert "not an authority grant" in checkpoint["reading"]
    assert [item["id"] for item in READINESS["blockers"]] == [f"B{n}" for n in range(1, 11)]
    kinds = {item["kind"] for item in READINESS["blockers"]}
    assert {"faculty decision", "technical", "audit", "boundary", "evidence", "faculty reading"} <= kinds
    assert READINESS["snapshot_id"] == an.SNAPSHOT_ID
