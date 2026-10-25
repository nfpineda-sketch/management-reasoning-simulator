"""Phase 2 shadow core, P2I-1: the GI lactate decision slice is decision support only.

It reruns P2G's admissible region in four trajectory questions, decomposes lactate exactly
given the deficit path, and never reads the family engine's lactate except as a separate,
labelled reference. Nothing is approved and no registry, band or golden changes.
"""
import json
from dataclasses import replace
from pathlib import Path

import pytest

from clinical_core import calibration, decision_pack, gi_reference, lactate_slice
from clinical_core import migration_authority as authority
from clinical_core.decision_pack import MIDDLE
from clinical_core.migration import gate_dry_run

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I_DECISION_LACTATO_GI.md"
DATA = ROOT / "docs" / "revision" / "P2I_lactate_slice.json"


@pytest.fixture(scope="module")
def quick():
    return lactate_slice.report(quick=True)


def test_the_scenarios_use_existing_orders_and_l4_is_a_labelled_composition():
    assert lactate_slice.ORDERS[lactate_slice.L3] is lactate_slice.GI_SCENARIOS["definitive_management"]
    for case in gi_reference.GI_CASES:
        minute = lactate_slice.endoscopy_minute(case)
        l4 = lactate_slice.scenario_inputs(case, lactate_slice.L4)
        composed = [item for item in l4 if type(item).__name__ == "EndoscopicHemostasis"]
        assert len(composed) == 1 and composed[0].completes_at_minute == minute
        assert composed[0].id == lactate_slice.COUNTERFACTUAL_HEMOSTASIS_ID != "gastroenterology_endoscopy"
        natural = [item for item in lactate_slice.scenario_inputs(case, lactate_slice.L3)
                   if type(item).__name__ == "EndoscopicHemostasis"]
        assert [item.id for item in natural] == ["gastroenterology_endoscopy"], "L3's haemostasis is the engine's own"
        assert natural[0].completes_at_minute == minute
        assert not any(type(item).__name__ in ("Crystalloid", "PackedRedCells")
                       for item in l4), "L4 has no volume"
        legacy_l4 = calibration._legacy_run(case, lactate_slice.ORDERS[lactate_slice.L4])
        assert legacy_l4.final_state["family_state"].get("endoscopy_at") is None, "the engine defers it"


@pytest.mark.parametrize("scenario", ["L1", "L3", "L4"])
def test_the_decomposition_adds_up_to_the_core_s_lactate(scenario):
    for case in gi_reference.GI_CASES:
        for candidate in decision_pack.admissible(quick=True):
            split = lactate_slice.decomposition(case, candidate, scenario)
            for row in split["rows"].values():
                total = (row["baseline"] + row["arrival_excess_left"] + row["from_arrival_debt"]
                         + row["from_deficit_since_arrival"])
                assert abs(total - row["lactate"]) < 1e-9
                assert abs(row["D_arrival_left"] + row["D_since_arrival"] - row["D"]) < 1e-9


def test_the_tables_are_consistent_and_complete(quick):
    for case in gi_reference.GI_CASES:
        data = quick["cases"][case]
        for scenario, table in data["trajectories"].items():
            assert list(table) == list(lactate_slice.TIMES)
            for minute, row in table.items():
                if row["n"]:
                    assert row["min"] <= row["p10"] <= row["median"] <= row["p90"] <= row["max"]
                    assert row["rising"] + row["falling"] <= 1.0 + 1e-12
                    assert row["changed_more_than_2"] <= row["changed_more_than_1"]
        for window, entry in data["classes"].items():
            counted = sum(item["n"] for item in entry["classes"].values())
            assert counted == len(decision_pack.admissible(quick=True)), window
        for rows in data["sensitivity"].values():
            assert {row["factor"] for row in rows} >= {
                "arrival_oxygen_debt", "arrival_lactate_excess", "debt_clearance_tau_min",
                "debt_per_delivery_deficit", "lactate_per_output_deficit", "lactate_clearance_tau_min",
                "arrival_delivery_ratio", "metabolic_demand_baseline"}
            assert [row["spread"] for row in rows] == sorted((row["spread"] for row in rows), reverse=True)
            assert all(row["impact"] in ("HIGH", "MEDIUM", "LOW") for row in rows)


def test_the_legacy_reference_is_never_an_input(monkeypatch, quick):
    """Classes, tables and sensitivity are computed without the engine's lactate."""
    def refuse(*args, **kwargs):
        raise AssertionError("the family engine's lactate was read")
    monkeypatch.setattr(lactate_slice, "legacy_reference", refuse)
    import clinical_core.legacy_adapter as adapter
    clean = lactate_slice.region_runs(quick=True)
    # P2I-2: the engine's runs supply the inputs and compute their own lactate, so refusing that
    # read cannot be tested with the runs cached; poison it instead, with every cache emptied.
    reads = []
    monkeypatch.setattr(adapter, "_lactate_lab", lambda state: reads.append(1) or 99.0)
    monkeypatch.setattr(calibration, "_RUNS", {})
    monkeypatch.setattr(lactate_slice, "_INPUTS", {})
    runs = lactate_slice.region_runs(quick=True)
    assert reads and runs == clean, "the engine's lactate changed a run"
    for case in gi_reference.GI_CASES:
        assert lactate_slice.classes(runs, case) == json.loads(json.dumps(lactate_slice.classes(runs, case)))
        lactate_slice.sensitivity(runs, case)
        lactate_slice.trajectory_table(runs, case, lactate_slice.L1)
    assert set(quick["legacy_reference"]) == set(gi_reference.GI_CASES)
    assert all(quick["legacy_reference"][case]["L4"] is None for case in gi_reference.GI_CASES)


def test_repository_truth_is_cited_and_free_of_inference(quick):
    for case, rows in quick["repository_truth"].items():
        items = {row["item"] for row in rows}
        assert {"lactate_mmol_l", "sbp", "hr", "hb_g_dl", "spo2", "crt_s", "active_bleeding",
                "prehospital_therapy"} <= items
        assert all(row["source"].startswith("clinical_cases.py:") for row in rows)
    assert gi_reference.verify_inventory() == []


def test_nothing_is_approved_and_gi_still_fails_the_gate():
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert authority.AUTHORITY_POLICIES == () and authority.TRUSTED_CASE_MAPPINGS == ()
    assert authority.APPROVED_FAMILY_DEFAULTS == ()
    for case in gi_reference.GI_CASES:
        assert gate_dry_run(case)["passes_gate"] is False


def test_the_slice_is_not_part_of_the_pack_or_the_freeze():
    assert "clinical_core/lactate_slice.py" in decision_pack.PACK_DIGEST_EXCLUDED
    assert "clinical_core/lactate_slice.py" not in calibration.HARNESS_SOURCES
    assert "clinical_core/lactate_slice.py" in lactate_slice.slice_sources()


def test_the_faculty_document_is_generated_from_the_current_code():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["slice_digest"] == lactate_slice.slice_digest(), "the slice is stale: regenerate it"
    assert data["freeze_digest"] == calibration.frozen_digest() and not data["quick"]
    assert data["admissible_candidates"] == len(decision_pack.admissible())
    assert data["slice_digest"] in document and data["freeze_digest"] in document
    assert lactate_slice.apply(document, lactate_slice.render(data)) == document, (
        "the document's tables differ from the slice: run python -m clinical_core.lactate_slice --write")


def test_the_worksheet_records_the_faculty_answers_without_approving_a_value():
    """P2I-1 left the six questions open; the faculty answered them (P2I-2). The worksheet now
    records each as FACULTY_APPROVED; the decision text itself is generated from the registry
    (checked in test_clinical_core_faculty_constraints.py) and no parameter value is approved."""
    from clinical_core import lactate_constraints
    document = DOCUMENT.read_text(encoding="utf-8")
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in document.split("<!-- generado:decisiones-lactato -->")[0].splitlines()
            if line.startswith("| FD-LAC-")]
    assert [row[0] for row in rows] == [f"FD-LAC-0{number}" for number in range(1, 7)]
    assert all(len(row) == 5 and row[4] == "FACULTY_APPROVED" for row in rows)
    assert {row[0]: row[3] for row in rows} == lactate_constraints.SELECTION_ES
    assert "no aprueban\nningún valor de parámetro oculto" in document
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0


def test_l4_is_labelled_a_manual_counterfactual_everywhere(quick):
    kinds = {name: item["trajectory_kind"] for name, item in quick["scenarios"].items()}
    assert kinds["L4"] == lactate_slice.COUNTERFACTUAL and quick["scenarios"]["L4"]["counterfactual"]
    assert {kinds[name] for name in ("L1", "L2", "L3")} == {lactate_slice.ENGINE_PRODUCED}
    assert not any(quick["scenarios"][name]["counterfactual"] for name in ("L1", "L2", "L3"))
    rendered = lactate_slice.render(json.loads(json.dumps(quick)))
    for line in rendered.splitlines():
        if "L4" in line:
            assert "contrafactual" in line.lower(), line
    document = DOCUMENT.read_text(encoding="utf-8")
    for line in document.split("<!-- generado:lactato -->")[0].splitlines():
        if line.startswith("| L4 "):
            assert "contrafactual" in line.lower()


def test_no_worksheet_question_reads_the_counterfactual(quick):
    """FD-LAC support comes from L1 and L3 only: removing L4 changes nothing in it."""
    runs = lactate_slice.region_runs(quick=True)
    without = {key: run_ for key, run_ in runs.items() if key[2] != lactate_slice.L4}
    for case in gi_reference.GI_CASES:
        assert lactate_slice.worksheet_support(runs, case) == lactate_slice.worksheet_support(without, case)
        sensitivity = lactate_slice.sensitivity(runs, case)
        assert all(not readout.startswith("L4") for readout in sensitivity)
