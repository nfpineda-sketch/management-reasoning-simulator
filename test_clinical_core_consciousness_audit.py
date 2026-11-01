"""P2L-1: the structural audit of consciousness / neurologic response (shadow only, read-only).

N's writers, readers and class; the observable consciousness equation and every causal path, each checked by a
perturbation through the certified core; the double-counting and orthogonality probes; the recovery lag; the probes
N1-N9; the authored GI neurologic observations; the carried extreme-acidemia subset; the upstream dependency; the
qualitative generalization; the structural verdict; the closure. The record tests read the committed run.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import consciousness_audit as ca
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt

ROOT = ca.ROOT
SOURCE = ROOT / "clinical_core" / "consciousness_audit.py"
#: The P2L-1 freeze: the faculty decisions, the path classes, the probes, the criteria, the verdict and next rules, the
#: smallest structure and every clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "a7de4d6c7b9183759299631da2e1b9717d346f0eb8a04b974911ad702e07cef6"


# The frozen package and its closure --------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(ca.OWN) <= set(sources) and ca.REPORT not in sources
    assert ca.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {ca.OWN[0], ca.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert ca._record(ca.P2K5_RECORD, ca.P2K5_RECORD_SHA)["verdict"]["verdict"] == \
        "GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE"
    assert ca._record(ca.P2J3_RECORD, ca.P2J3_RECORD_SHA)["support"]
    if FROZEN_DIGEST is not None:
        assert ca.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_closed_files_keep_their_p2k5_bytes_and_nothing_imports_the_audit():
    assert all(ca.closed_unchanged().values()) and len(ca.CLOSED_AT_P2K5) == 8
    for path in (ROOT / "clinical_core").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        if any("consciousness_audit" in name for name in imported):
            assert path.name == "consciousness_audit_report.py", path.name
    own = {alias.name for node in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))
           if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not own & {"family_engine", "legacy_adapter", "ventilation_filter", "respiratory_monotonicity", "ventilation"}


def test_the_closed_packages_see_p2k5s_sources():
    sources = bf.freeze_sources()
    mapped = ca.p2k5_sources(sources)
    assert not set(ca.OWN) & set(mapped)
    for relative, sha in ca.TUPLE_AT_P2K5.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert ca.p2k5_sources(sources)["clinical_core/decision_pack.py"] == sources["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


# P2L-1-1: N --------------------------------------------------------------------------------------------------------------

def test_n_is_an_unused_placeholder():
    n = ca.n_audit()
    assert n["classification"] == "UNUSED_PLACEHOLDER" and n["arrival_value"] == 0.0
    refs = n["references"]
    assert refs["keyword_writes"] == n["writers"] and all(w.startswith("state.py") for w in refs["keyword_writes"])
    assert refs["attribute_reads"] == []
    assert {r.split(":")[0] for r in refs["channel_constant"]} <= {"state.py", "integration.py"}
    assert set(n["observable_effect"].values()) == {0}
    assert "contracts_output" in n["serialization"] and "MIXED_NEUROLOGIC_CONSTRUCT" in n["declared_semantics"]


# P2L-1-2: the equation and every causal path ------------------------------------------------------------------------------

def test_the_equation_is_the_cores_and_reads_only_pressure_saturation_and_the_arrival_floor():
    e = ca.equation_audit()
    assert e["source_line_present"] and e["pulseless_level"]
    assert e["pressure_levels"] == [[80.0, 1], [65.0, 2]] and e["oxygen_levels"] == [[87.0, 1], [80.0, 2]]
    assert all(row[0] == "adopted" and "family_engine" in row[1] for row in e["provenance"].values())


def test_every_path_is_classified_and_checked_by_a_perturbation():
    table = ca.path_table()
    assert set(row["class"] for row in table.values()) <= set(ca.PATH_CLASSES)
    moving = {name for name, row in table.items() if row.get("moves_level")}
    assert moving == {"sbp", "spo2", "arrival_level"}
    assert table["pulse"]["class"] == "VALID_CAUSAL_PATH"
    assert table["sbp"]["class"] == table["spo2"]["class"] == "LEGACY_ARTIFACT"
    assert table["arrival_level"]["class"] == "SEMANTIC_LEAK"
    for name in ("N", "effective_oxygen_deficit", "D", "glucose", "ph", "paco2", "lactate", "hr", "demand", "map"):
        assert table[name]["class"] == "NOT_CURRENTLY_MODELED" and not table[name].get("moves_level"), name
    # No direct lactate path: nothing to refactor as a biomarker proxy.
    assert all(row["class"] not in ("BIOMARKER_PROXY", "BIOMARKER_PROXY_REQUIRES_REFACTOR") for row in table.values())
    assert "lactate" not in inspect.getsource(dv.derive).split("level = max(")[1].split(")")[0]


# P2L-1-3 to -6: double counting and orthogonality ---------------------------------------------------------------------------

def test_map_and_deficit_are_distinct_signals_but_only_pressure_is_read():
    p = ca.deficit_map_probes()
    assert p["signals_distinguish_a_from_b"] and p["current_a_impaired"] and p["current_b_alert"]
    rows = p["rows"]
    assert rows["A_low_map_no_deficit"]["deficit"] == 0.0 and rows["B_adequate_map_high_deficit_anaemia"]["sbp"] == 120.0
    assert rows["C_low_map_and_high_deficit"]["level"] == 2 and rows["D_neither"]["level"] == 0


def test_a_direct_spo2_path_double_counts_delivery():
    p = ca.oxygenation_probes()
    assert p["direct_path_double_counts"] and p["current_a_impaired_b_alert"]
    rows = p["rows"]
    assert rows["A_low_spo2_adequate_delivery"]["do2"] == 1.0 and rows["A_low_spo2_adequate_delivery"]["level"] == 1
    assert rows["B_normal_spo2_critical_deficit"]["deficit"] > 0.0 and rows["B_normal_spo2_critical_deficit"]["level"] == 0


def test_metabolic_acidemia_and_hypercapnia_are_kept_apart_and_compensation_is_not_representable():
    p = ca.acid_base_probes()
    assert p["distinguishes"] and not p["compensated_hypercapnia_representable"]
    assert p["compensated_hypercapnia_ph_ceiling"] == pytest.approx(7.3041, abs=1e-4)
    rows = p["rows"]
    assert rows["A_metabolic_acidemia"]["paco2"] < 30.0 < 50.0 < rows["B_hypercapnia"]["paco2"]
    assert {row["level"] for row in rows.values()} == {0}


def test_glucose_is_orthogonal_and_unread():
    p = ca.glucose_probe()
    assert p["level_unchanged"] and p["rows"]["severe_hypoglycaemia"]["deficit"] == 0.0
    writes = set()
    for path in ca._python():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.keyword) and node.arg == "glucose":
                writes.add(path.name)
    assert writes <= {"state.py", "legacy_adapter.py", "bands.py"}  # constructors only: nothing moves glucose


# P2L-1-7, -10: recovery lag and the neurologic probes -----------------------------------------------------------------------

def test_no_memory_can_carry_a_neurologic_recovery_lag():
    r = ca.recovery_lag()
    assert r["insult_level"] == 2 and r["restored_level"] == 0
    assert not any(r["d_accrues_without_deficit"].values()) and not r["d_sufficient"] and r["new_state_required"]
    assert r["verdict"] == ca.BLOCKER and "D" in r["memories"]


def test_the_neurologic_probes():
    p = ca.neuro_probes()
    assert p["represented"] == ["N1", "N4", "N8"] and p["signal_missing"] == ["N9"]
    rows = p["rows"]
    for name in ("N2", "N3", "N5", "N6", "N7"):
        assert rows[name]["level"] == 0 and rows[name]["gap"] == "the observable does not read the signal", name
    assert rows["N9"]["gap"] == "a memory state (none exists)"


# P2L-1-8, -9: authored observations and the extreme-acidemia subset -----------------------------------------------------------

def test_the_authored_gi_neurologic_observations():
    bank = (ROOT / "clinical_cases.py").read_text(encoding="utf-8")
    for case in ca.CASES:
        a = ca.authored(case)
        assert a["presentation"]["value"] in bank and a["presentation"]["class"] == "AUTHORED_OBSERVATION"
        assert a["mental_status"]["value"] == "Alert" and a["core_arrival_level"]["value"] == 0
        assert a["map"]["class"] == "MODEL_DERIVED" and a["legacy_arrival"]["class"] == "LEGACY_REFERENCE"
        assert a["absent"]["later_neurologic_anchors"].startswith("none authored")
    assert "Awake and oriented" in ca.authored(ca.C57)["neurological_exam"]["value"]


def test_the_extreme_acidemia_subset_is_carried_and_already_reads_obtunded():
    x = ca.extreme_acidemia()
    assert x["flagged"] == 17604 and x["by_case"] == {ca.C57: 17604, ca.C72: 0}
    assert x["classification"] == "CONSCIOUSNESS_COLLAPSE_REVIEW" and x["lowest"]["ph"] < 7.0
    assert x["highest_untreated_sbp120"] < 65.0 and x["current_level_at_120"] == 2
    assert not x["fully_alert_plausible"] and not x["filtered"]


# P2L-1-12, -13: generalization and upstream ----------------------------------------------------------------------------------

def test_the_upstream_dependency_and_the_generalization():
    u = ca.upstream()
    assert u["evidence"] == {"hr_moves_level": False, "demand_moves_level": False, "sbp_moves_level": True}
    assert u["table"]["map_set"]["current"] == u["table"]["baroreflex_gain"]["current"] == "no"
    assert u["table"]["tone_gain"]["current"].startswith("yes")
    g = ca.generalization()
    assert g["result"] == "STRUCTURAL_GAP" and set(g["families"]) == {
        "hemorrhagic_shock", "hypoglycaemia", "hypercapnia_opioid", "primary_neurologic_injury", "severe_hypoxaemia",
        "distributive_shock"}
    text = json.dumps(ca.design())
    assert "gi_bleed" not in json.dumps({k: ca.design()[k] for k in ("smallest_structure", "decision_surface")})
    assert "maximum" in text and "no lactate term" in text


# P2L-1-15: the verdict, the early stop, the scope ------------------------------------------------------------------------------

def test_the_verdict_names_the_early_stop_blocker():
    good = {name: True for name in ca.CRITERIA}
    assert ca.verdict(good)["verdict"] == ca.READY
    assert ca.recommendation(ca.verdict(good))["recommendation"] == "PREPARE_OBSERVABLE_CONSCIOUSNESS_DECISION_PACK"
    lagged = ca.verdict({**good, "recovery_lag_coherent": False, "causal_modifiers_explicit": False})
    assert lagged["verdict"] == f"{ca.NOT_READY} - {ca.BLOCKER}"
    assert ca.recommendation(lagged)["recommendation"] == "STOP_FOR_FACULTY_STRUCTURAL_DECISION"
    assert ca.verdict({**good, "lactate_not_proxy": False})["verdict"] == f"{ca.NOT_READY} - LACTATE_NOT_PROXY"


def test_a_changed_closed_file_stops_before_any_probe(monkeypatch):
    monkeypatch.setattr(ca, "closed_unchanged", lambda: {"clinical_core/derived.py": False})
    monkeypatch.setattr(ca, "n_audit", lambda: pytest.fail("no probe after a STOP"))
    out = ca.run()
    assert out["stopped"].startswith("a closed file changed") and out["verdict"]["checks"]["upstream_unchanged"] is False


def test_the_scope_adds_and_reads_nothing_it_should_not():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("import family_engine", "legacy_adapter", "snapshot("):
        assert forbidden not in source
    assert "nothing selected or approved" in ca.POLICY and ca.MIGRATION_GATE.startswith("MIGRATION_GATE_CLOSED")
    assert ca.SMALLEST_STRUCTURE["not_added_here"].startswith("no state")
    assert ca.DECISION_SURFACE["numeric"].startswith("none")
    # The legacy reference is quoted from the engine as text (never imported, never fitted).
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    for name in ("_PRESSURE_LEVELS", "_OXYGEN_LEVELS", "_anchored_levels", "_RECOVERY_MARGIN", "MENTAL_RECOVERY"):
        assert name in engine and name in ca.LEGACY[{"_PRESSURE_LEVELS": "thresholds", "_OXYGEN_LEVELS": "thresholds",
                                                     "_anchored_levels": "dc1", "_RECOVERY_MARGIN": "margin",
                                                     "MENTAL_RECOVERY": "recovery"}[name]]
