"""Phase 2 shadow core, P2I-2: the faculty's GI lactate behaviour constraints and their frozen tests.

The decisions FD-LAC-01..06 are FACULTY_APPROVED clinical constraints, kept apart from migration
authority, parameter provenance and the calibration registry: no hidden parameter is approved by
them. Their operationalization is checked here on synthetic trajectories, before and independently
of the region it filters.
"""
import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from clinical_core import calibration, decision_pack, faculty_constraints as fc, gi_reference
from clinical_core import lactate_constraints, lactate_slice
from clinical_core import migration_authority as authority
from clinical_core.decision_pack import MIDDLE
from clinical_core.faculty_constraints import Trajectory
from clinical_core.migration import gate_dry_run

ROOT = Path(__file__).resolve().parent
P = fc.params()
DOCUMENT = ROOT / "docs" / "revision" / "P2I2_RESTRICCIONES_LACTATO_GI.md"
DATA = ROOT / "docs" / "revision" / "P2I2_lactate_constraints.json"
DECISION_DOCUMENT = ROOT / "docs" / "revision" / "P2I_DECISION_LACTATO_GI.md"


def trajectory(lactate, delivery=None, demand=1.0, controlled_at=None, D=None):
    minutes = len(lactate)
    delivery = delivery if delivery is not None else [0.5] * minutes
    delivery = [delivery] * minutes if isinstance(delivery, float) else delivery
    return Trajectory(tuple(lactate), tuple(D or [0.0] * minutes), tuple(delivery), tuple([demand] * minutes),
                      controlled_at)


def linear(start, end, minutes=120):
    return [start + (end - start) * minute / minutes for minute in range(minutes + 1)]


# The decision records -----------------------------------------------------------------------------

def test_the_six_decisions_are_recorded_verbatim_with_their_clarifications_and_approve_no_parameter():
    assert fc.CONSTRAINT_IDS == tuple(f"FD-LAC-0{number}" for number in range(1, 7))
    for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
        assert item.status == fc.FACULTY_APPROVED and item.decided == "2026-10-25" and item.version == "FD-LAC v2"
        assert item.approves_parameter_values == () and "Approves no hidden parameter value" in item.scope_note
        assert item.decision and item.rationale in item.decision and item.observable
        assert bool(item.clarification) == bool(item.clarified) == (item.id in ("FD-LAC-01", "FD-LAC-04", "FD-LAC-05"))
    texts = {item.id: item.decision for item in fc.FACULTY_CLINICAL_CONSTRAINTS}
    assert "GENERALLY RISE" in texts["FD-LAC-01"] and "lactate must rise every minute" in texts["FD-LAC-01"]
    assert "4.4-7.0 mmol/L" in texts["FD-LAC-02"] and "3.4-5.5 mmol/L" in texts["FD-LAC-03"]
    assert "15-30 minutes" in texts["FD-LAC-04"] and "memory of prior debt" in texts["FD-LAC-05"]
    assert texts["FD-LAC-06"].startswith("ONLY IF OXYGEN DELIVERY IS ADEQUATE")
    clarified = {item.id: item.clarification for item in fc.FACULTY_CLINICAL_CONSTRAINTS}
    assert "Do NOT encode: L60 >= L0" in clarified["FD-LAC-01"] and "fixed percentage increase" in clarified["FD-LAC-01"]
    assert "L(T* + 30) < L(T*)" in clarified["FD-LAC-04"] and "SENSITIVITY ANALYSIS ONLY" in clarified["FD-LAC-04"]
    assert "1.5 <= L120 <= 4.0" in clarified["FD-LAC-05"] and "1.2 <= L120 <= 3.5" in clarified["FD-LAC-05"]
    assert "not universal human physiological limits" in clarified["FD-LAC-05"]
    assert fc.ENVELOPES_120 == {"gi_bleed_57m": {"minute": 120, "low": 1.5, "high": 4.0},
                                "gi_bleed_72f": {"minute": 120, "low": 1.2, "high": 3.5}}
    assert "inadequate delivery = oxygen delivery < oxygen demand" in fc.FACULTY_CONFIRMED_DEFINITIONS


def test_the_envelopes_state_the_repository_arrival_lactate():
    truth = {entry.case: float(entry.value) for entry in gi_reference.INVENTORY if entry.item == "lactate_mmol_l"}
    for case, envelope in fc.ENVELOPES.items():
        assert envelope["arrival"] == truth[case] == envelope["low"], "the band starts at the arrival lactate"
    assert fc.ENVELOPES["gi_bleed_57m"]["high"] == 7.0 and fc.ENVELOPES["gi_bleed_72f"]["high"] == 5.5


def test_the_constraints_stay_out_of_authority_provenance_and_the_registry():
    for name in ("migration.py", "migration_authority.py", "calibration.py", "bands.py", "derived.py",
                 "integration.py", "decision_pack.py", "lactate_slice.py"):
        tree = ast.parse((ROOT / "clinical_core" / name).read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        assert not any("faculty_constraints" in item or "lactate_constraints" in item for item in imported), name
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    for parameter in fc.HIDDEN_PARAMETERS:
        assert calibration.REGISTRY[parameter].status != calibration.FACULTY_APPROVED
    assert authority.AUTHORITY_POLICIES == () and authority.TRUSTED_CASE_MAPPINGS == ()
    assert authority.APPROVED_FAMILY_DEFAULTS == ()
    for case in gi_reference.GI_CASES:
        assert gate_dry_run(case)["passes_gate"] is False


def test_the_definitions_pipeline_and_reporting_rules_are_frozen():
    assert fc.definitions_digest() == lactate_constraints.FROZEN_DEFINITIONS_DIGEST
    assert lactate_constraints.pipeline_digest() == lactate_constraints.FROZEN_PIPELINE_DIGEST
    assert lactate_constraints.reporting_digest() == lactate_constraints.FROZEN_REPORTING_DIGEST
    lactate_constraints.check_frozen()


def test_the_filter_refuses_changed_definitions(monkeypatch):
    monkeypatch.setattr(fc, "definitions_digest", lambda: "0" * 64)
    with pytest.raises(AssertionError, match="changed after they were frozen"):
        lactate_constraints.report(quick=True)


def test_every_sensitivity_variant_changes_one_known_setting():
    for case in gi_reference.GI_CASES:
        severe = calibration.case_values(case, replace(MIDDLE, debt="upper"))["arrival_oxygen_debt"]
        assert fc.PRIMARY["fd05_reference_debt"] == severe, "the upper end of the arrival-debt band"
    for name, overrides in fc.SENSITIVITY.items():
        assert len(overrides) == 1 and fc.params(**overrides) != fc.PRIMARY, name
    # No fixed 30-min fall is primary: the faculty's rule is any decrease; 5-15 % are sensitivity only.
    assert fc.PRIMARY["fd04_required_fall"] == 0.0 and fc.REPORTED_FALL_THRESHOLDS == (0.0, 0.05, 0.10, 0.15)
    with pytest.raises(KeyError):
        fc.params(not_a_setting=1)


# The operational tests, on synthetic trajectories -------------------------------------------------

def test_adequacy_is_delivery_against_demand_never_D():
    run_ = trajectory([4.0] * 3, delivery=[1.0, 0.99, 1.2], D=[0.0, 50.0, 90.0])
    assert [fc.adequate(run_, minute, P) for minute in range(3)] == [True, False, True]
    assert fc.adequate(run_, 1, fc.params(adequacy_tolerance=0.05))
    assert fc.inadequate_bleeding_windows(run_, P) == [(1, 1)]
    stopped = trajectory([4.0] * 3, delivery=0.5, controlled_at=1)
    assert fc.inadequate_bleeding_windows(stopped, P) == [(0, 0)], "after haemostasis bleeding is not active"


def test_reassessment_points_and_sustained_decline():
    assert fc.reassessments(1, 120, P) == [1, 15, 30, 45, 60, 75, 90, 105, 120]
    falls_10 = trajectory(linear(4.0, 3.58, 30) + [3.58] * 90)
    assert fc.sustained_declines(falls_10, 0, 120, P), "10 % over 30 min is a sustained decline"
    falls_9 = trajectory(linear(4.0, 3.65, 30) + [3.65] * 90)
    assert not fc.sustained_declines(falls_9, 0, 120, P), "below the meaningful change"
    dip = trajectory(linear(4.0, 3.5, 15) + linear(3.5, 4.1, 15)[1:] + linear(4.1, 5.0, 90)[1:])
    assert not fc.sustained_declines(dip, 0, 120, P), "a dip recovered within 30 min is transient"
    slow = trajectory(linear(4.0, 3.0))
    assert fc.sustained_declines(slow, 0, 120, P), "a slow fall that persists is sustained"


def test_fd_lac_01_refuses_only_a_substantial_sustained_decline_before_60_min():
    assert fc.fd_lac_01(trajectory(linear(4.4, 5.1)), P)["passes"], "a slow steady rise"
    assert fc.fd_lac_01(trajectory([4.4] * 121), P)["passes"], "no rise and no fixed increase are required"
    small = trajectory(linear(4.4, 4.1, 30) + linear(4.1, 4.3, 30)[1:] + [4.3] * 60)
    assert fc.fd_lac_01(small, P)["passes"], "a small decrease (7 %) is not a substantial decline"
    transient = trajectory(linear(4.4, 3.9, 15) + linear(3.9, 4.5, 15)[1:] + [4.5] * 90)
    assert fc.fd_lac_01(transient, P)["passes"], "a transient dip recovered within 30 min"
    u_shape = trajectory(linear(4.4, 3.8, 45) + linear(3.8, 6.0, 75)[1:])
    result = fc.fd_lac_01(u_shape, P)
    assert not result["passes"] and result["status"] == fc.FAIL and result["windows"][0]["sustained_declines"]
    assert fc.fd_lac_01(u_shape, fc.params(meaningful_change=0.15))["passes"], "the threshold is exposed"
    late = trajectory([4.4] * 61 + linear(4.4, 3.5, 59)[1:] + [3.5])
    assert fc.fd_lac_01(late, P)["passes"], "after 60 min it is FD-LAC-06's to judge"
    assert not fc.fd_lac_06({"L1": late}, P)["passes"]
    adequate_all_along = trajectory(linear(4.4, 3.0), delivery=1.1)
    result = fc.fd_lac_01(adequate_all_along, P)
    assert result["status"] == fc.NOT_APPLICABLE and result["passes"]
    assert not fc.fd_lac_01(adequate_all_along, fc.params(fd01_unapplicable_passes=False))["passes"]


def test_fd_lac_02_03_are_inclusive_hard_envelopes():
    for value, passes in ((4.4, True), (7.0, True), (4.39, False), (7.01, False), (5.7, True)):
        run_ = trajectory([4.4] * 60 + [value] + [value] * 60)
        assert fc.fd_lac_envelope(run_, "gi_bleed_57m", P)["passes"] is passes, value
    run_ = trajectory([3.4] * 60 + [3.36] + [3.4] * 60)
    assert not fc.fd_lac_envelope(run_, "gi_bleed_72f", P)["passes"]
    assert fc.fd_lac_envelope(run_, "gi_bleed_72f", fc.params(fd0203_display_decimals=1))["passes"]
    assert not fc.fd_lac_envelope(trajectory([4.4] * 50), "gi_bleed_57m", P)["passes"], "no value at 60"


def test_fd_lac_04_t_star_is_the_later_of_haemostasis_and_sustained_adequate_delivery():
    restored = [1.1] * 121
    early = trajectory(linear(5.0, 3.0), delivery=[0.6] * 10 + [1.1] * 111, controlled_at=60)
    assert fc.restoration_trigger(early, P) == 60, "delivery adequate since minute 10: T* is haemostasis"
    late = trajectory(linear(5.0, 3.0), delivery=[0.6] * 70 + [1.1] * 51, controlled_at=60)
    assert fc.restoration_trigger(late, P) == 70, "not while delivery is still inadequate"
    brief = trajectory(linear(5.0, 3.0), delivery=[0.6] * 70 + [1.1] * 20 + [0.6] * 31, controlled_at=60)
    assert fc.restoration_trigger(brief, P) is None, "20 min of adequacy is not sustained"
    assert fc.restoration_trigger(trajectory(linear(5.0, 3.0), delivery=restored), P) is None, "no haemostasis"


def test_fd_lac_04_requires_a_fall_by_t_star_plus_30_with_ongoing_clearance():
    restored = [1.1] * 121
    falling = trajectory(linear(5.0, 3.0), delivery=restored, controlled_at=60)
    result = fc.fd_lac_04(falling, P)
    assert result["trigger"] == 60 and result["status"] == fc.PASS, "already falling before T*: no new peak needed"
    assert abs(result["reduction_at_window"] - (4.0 - 3.5) / 4.0) < 1e-12
    slight = trajectory([5.0] * 60 + linear(5.0, 4.9, 30) + [4.9] * 30, delivery=restored, controlled_at=60)
    assert fc.fd_lac_04(slight, P)["passes"], "any decrease (2 %) is the faculty's rule"
    assert not fc.fd_lac_04(slight, fc.params(fd04_required_fall=0.05))["passes"], "5 % is sensitivity only"
    rising = trajectory([5.0] * 60 + linear(5.0, 5.3, 30) + [5.3] * 30, delivery=restored, controlled_at=60)
    assert fc.fd_lac_04(rising, P)["status"] == fc.FAIL
    rebound = trajectory([5.0] * 60 + linear(5.0, 4.0, 15) + linear(4.0, 4.6, 15)[1:] + [4.6] * 30,
                         delivery=restored, controlled_at=60)
    assert not fc.fd_lac_04(rebound, P)["passes"], "lower at 30 min but rising again: not ongoing clearance"
    assert fc.fd_lac_04(rebound, fc.params(fd04_ongoing_clearance=False))["passes"]


def test_fd_lac_04_already_normalized_and_not_evaluable():
    restored = [1.1] * 121
    normal = trajectory([1.8] * 121, delivery=restored, controlled_at=60)
    result = fc.fd_lac_04(normal, P)
    assert result["status"] == fc.ALREADY_NORMALIZED and result["passes"], "no further fall from a normal lactate"
    short = trajectory(linear(5.0, 3.0), delivery=[0.6] * 100 + [1.1] * 21, controlled_at=60)
    assert fc.fd_lac_04(short, P)["status"] == fc.NOT_EVALUABLE, "no sustained span to define T*"
    tail = trajectory(linear(5.0, 3.0), delivery=restored, controlled_at=100)
    result = fc.fd_lac_04(tail, P)
    assert result["trigger"] == 100 and result["status"] == fc.NOT_EVALUABLE and "follow-up" in result["reason"]
    ceases = trajectory(linear(5.0, 3.0), delivery=[1.1] * 75 + [0.6] * 46, controlled_at=60)
    result = fc.fd_lac_04(ceases, P)
    assert result["trigger"] == 60 and result["status"] == fc.NOT_EVALUABLE and "ceased" in result["reason"]
    assert result["passes"] and not fc.fd_lac_04(ceases, fc.params(fd04_unevaluable_passes=False))["passes"]


def test_fd_lac_05_debt_memory_is_the_core_s_own_arrival_debt_term():
    for case in gi_reference.GI_CASES:
        split = lactate_slice.decomposition(case, MIDDLE, "L3")
        p = split["parameters"]
        assert p["arrival_oxygen_debt"] > 0
        coefficient = fc.debt_memory_coefficient(p["debt_clearance_tau_min"], p["lactate_clearance_tau_min"],
                                                 p["lactate_per_output_deficit"], 120)
        assert abs(coefficient * p["arrival_oxygen_debt"] - split["rows"][120]["from_arrival_debt"]) < 1e-9


KINETICS = {"debt_clearance_tau_min": 60.0, "lactate_clearance_tau_min": 120.0, "lactate_per_output_deficit": 6.0}


def test_fd_lac_05_is_the_120_min_envelope_below_t_star_with_sustained_delivery():
    restored = [1.1] * 121
    for value, passes in ((1.5, True), (4.0, True), (1.49, False), (4.01, False), (1.9, True)):
        run_ = trajectory(linear(5.0, value), delivery=restored, controlled_at=60)
        assert fc.fd_lac_05(run_, 60, KINETICS, 4.4, P, "gi_bleed_57m")["passes"] is passes, value
    run_ = trajectory(linear(5.0, 1.25), delivery=restored, controlled_at=60)
    assert fc.fd_lac_05(run_, 60, KINETICS, 3.4, P, "gi_bleed_72f")["passes"], "below 2 mmol/L is allowed"
    flat = trajectory([3.0] * 121, delivery=restored, controlled_at=60)
    result = fc.fd_lac_05(flat, 60, KINETICS, 4.4, P, "gi_bleed_57m")
    assert result["inside_envelope"] and not result["below_trigger"] and not result["passes"], "L120 < L(T*)"
    normal = trajectory([1.8] * 121, delivery=restored, controlled_at=60)
    assert not fc.fd_lac_05(normal, 60, KINETICS, 4.4, P, "gi_bleed_57m")["passes"], "as written: L120 < L(T*)"
    assert fc.fd_lac_05(normal, 60, KINETICS, 4.4, fc.params(fd05_normalized_exception=True), "gi_bleed_57m")["passes"]
    lapse = trajectory(linear(5.0, 3.0), delivery=[1.1] * 100 + [0.6] * 21, controlled_at=60)
    result = fc.fd_lac_05(lapse, 60, KINETICS, 4.4, P, "gi_bleed_57m")
    assert result["status"] == fc.NOT_EVALUABLE and result["passes"]
    assert fc.fd_lac_05(run_, None, KINETICS, 3.4, P, "gi_bleed_72f")["status"] == fc.NOT_EVALUABLE
    rounded = trajectory(linear(5.0, 4.04), delivery=restored, controlled_at=60)
    assert not fc.fd_lac_05(rounded, 60, KINETICS, 4.4, P, "gi_bleed_57m")["passes"]
    assert fc.fd_lac_05(rounded, 60, KINETICS, 4.4, fc.params(fd05_display_decimals=1), "gi_bleed_57m")["passes"]


def test_fd_lac_06_allows_falls_only_with_adequate_delivery():
    falling = linear(4.4, 3.0)
    assert fc.fd_lac_06({"L2": trajectory(falling, delivery=1.05)}, P)["passes"], "adequate delivery, bleeding"
    assert not fc.fd_lac_06({"L1": trajectory(falling, delivery=0.8)}, P)["passes"]
    restored_late = trajectory(falling, delivery=[0.8] * 20 + [1.1] * 101)
    assert fc.fd_lac_06({"L2": restored_late}, P)["passes"], "the inadequate span is too short to sustain"
    after = trajectory(falling, delivery=0.8, controlled_at=10)
    assert fc.fd_lac_06({"L3": after}, P)["passes"], "after haemostasis bleeding is no longer active"


def test_identifiability_rule():
    region = {"a": 0.5, "b": 0.5}
    assert fc.identifiability(region, {"a": 1.0, "b": 0.0}, True) == "WELL CONSTRAINED"
    three = {"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}
    assert fc.identifiability(three, {"a": 0.5, "b": 0.5, "c": 0.0}, True) == "PARTIALLY CONSTRAINED"
    assert fc.identifiability(region, {"a": 0.6, "b": 0.4}, True) == "POORLY IDENTIFIED"
    assert fc.identifiability(region, {"a": 0.52, "b": 0.48}, True) == "NOT IDENTIFIED"
    assert fc.identifiability({"x": 1.0}, {"x": 1.0}, False) == "NOT IDENTIFIED"
    assert fc.identifiability(region, {}, True).startswith("NOT ASSESSABLE")


# The pipeline, structurally (no candidate's verdict is read here) ---------------------------------

def test_the_pipeline_reads_the_core_and_only_engine_produced_runs():
    members = lactate_constraints.region(quick=True)
    assert set(members) == {candidate.key() for candidate in decision_pack.admissible(quick=True)}
    for item in members.values():
        for case in gi_reference.GI_CASES:
            runs = item["runs"][case]
            assert set(runs) == {"L1", "L2", "L3"}, "L4, the counterfactual, never enters"
            assert all(run_.end == 120 for run_ in runs.values())
            assert runs["L1"].controlled_at is None and runs["L2"].controlled_at is None
            assert runs["L3"].controlled_at == lactate_slice.endoscopy_minute(case)
    verdicts = lactate_constraints.evaluate_region(members, P)
    assert set(verdicts) == set(members)
    for verdict in verdicts.values():
        assert set(verdict["passes"]) == set(fc.CONSTRAINT_IDS)
        assert verdict["all"] == all(verdict["passes"].values())


def test_the_engine_lactate_never_reaches_the_filter(monkeypatch):
    """The engine's run is still made (it supplies the scenarios' inputs, as in P2I-1) and it
    computes its own lactate; poisoning that lactate, with the engine-run caches emptied, changes
    no trajectory, no verdict and nothing in the report but the legacy reference itself. The core's
    arrival lactate is the case's authored value (repository truth), not an engine trajectory."""
    clean_report = lactate_constraints.report(quick=True)
    clean = lactate_constraints.region(quick=True)
    truth = {entry.case: float(entry.value) for entry in gi_reference.INVENTORY if entry.item == "lactate_mmol_l"}
    for item in clean.values():
        for case in gi_reference.GI_CASES:
            assert all(run_.lactate[0] == truth[case] for run_ in item["runs"][case].values())
    import clinical_core.legacy_adapter as adapter
    poisoned_reads = []

    def poisoned(state):
        poisoned_reads.append(1)
        return 99.0
    monkeypatch.setattr(adapter, "_lactate_lab", poisoned)
    monkeypatch.setattr(calibration, "_RUNS", {})
    monkeypatch.setattr(lactate_slice, "_INPUTS", {})
    again = lactate_constraints.region(quick=True)
    assert poisoned_reads, "the engine's runs were really recomputed with the poisoned lactate"
    for key, item in clean.items():
        assert again[key]["runs"] == item["runs"]
    poisoned_report = lactate_constraints.report(quick=True)
    assert poisoned_report["legacy_position"] != clean_report["legacy_position"], "the poison reached the reference"
    # The calibration freeze pins the engine's materialized runs, so it (and the filter digest that
    # includes it) correctly reports a changed engine; every result is unchanged.
    provenance = {"legacy_position", "freeze_digest", "filter_digest"}
    assert all(poisoned_report[key] != clean_report[key] for key in provenance)
    assert {key: value for key, value in poisoned_report.items() if key not in provenance} == {
        key: value for key, value in clean_report.items() if key not in provenance}


def test_the_reporting_rules_are_pinned():
    assert lactate_constraints.reporting_digest() == lactate_constraints.FROZEN_REPORTING_DIGEST


# The artifacts ------------------------------------------------------------------------------------

def test_the_results_document_is_generated_from_the_current_code():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["filter_digest"] == lactate_constraints.filter_digest(), "the results are stale: regenerate them"
    assert data["definitions_digest"] == lactate_constraints.FROZEN_DEFINITIONS_DIGEST
    assert data["pipeline_digest"] == lactate_constraints.FROZEN_PIPELINE_DIGEST
    assert data["freeze_digest"] == calibration.frozen_digest() and not data["quick"]
    assert data["admissible_candidates"] == len(decision_pack.admissible()) == data["counts"]["before"]
    assert data["settings"] == fc.PRIMARY
    for digest in ("filter_digest", "definitions_digest", "pipeline_digest", "freeze_digest"):
        assert data[digest] in document
    assert lactate_constraints.apply(document, lactate_constraints.render(data)) == document, (
        "the document differs from the results: run python -m clinical_core.lactate_constraints --write")


def test_the_results_are_a_constrained_candidate_region_not_an_approval():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    keys = {candidate.key() for candidate in decision_pack.admissible()}
    survivors = set(data["faculty_constrained_region"])
    assert survivors <= keys and len(survivors) == data["counts"]["all_six"]
    assert data["counts"]["all_six"] <= min(data["counts"]["survivors"].values())
    assert [row["id"] for row in data["decisions"]] == list(fc.CONSTRAINT_IDS)
    assert all(row["status"] == fc.FACULTY_APPROVED and row["approves_parameter_values"] == []
               for row in data["decisions"])
    classes = {row["factor"]: row["classification"] for row in data["parameter_region"]}
    assert set(classes) == set(fc.HIDDEN_PARAMETERS)
    assert classes["debt_per_delivery_deficit"] == classes["metabolic_demand_baseline"] == "NOT IDENTIFIED"
    document = DOCUMENT.read_text(encoding="utf-8")
    assert "REGIÓN CANDIDATA RESTRINGIDA POR LA DOCENCIA" in document and "No aprueban ningún" in document


def test_the_decision_record_is_generated_from_the_registry():
    document = DECISION_DOCUMENT.read_text(encoding="utf-8")
    assert lactate_constraints.apply_block(document, lactate_constraints.render_decisions(),
                                           lactate_constraints.DECISIONS_OPENING,
                                           lactate_constraints.DECISIONS_CLOSING) == document, (
        "run python -m clinical_core.lactate_constraints --decisions docs/revision/P2I_DECISION_LACTATO_GI.md")
    for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
        assert f"«{item.decision}»" in document and item.status in document
