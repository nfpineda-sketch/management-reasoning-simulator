"""Phase 2 shadow core, P2I-2V: the faculty's shared-blood anchors as frozen operational constraints.

These tests pin that the faculty decisions are transcribed as approved, that their readings and the
filter were frozen before any candidate of the region was evaluated (and the reported filter ran with
that freeze), that the blood reading's premise holds, that no lactate, legacy trajectory or direct V /
Hb drift enters a constraint, and that no hidden parameter is approved.
"""
import ast
import itertools
import json
from pathlib import Path

import pytest

from clinical_core import blood_anchors, blood_constraints as bc, blood_filter_report as report, calibration
from clinical_core import migration_authority
from clinical_core.provenance import SourceKind
from clinical_core.state import Channel

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2V_ANCLAS_APROBADAS_FILTRO.md"
SENSITIVITY = ROOT / "docs" / "revision" / "P2I2V_blood_sensitivity.json"

#: The P2I-2V freeze, recorded before the filter ran on any candidate of the region (P2I-2V-1). It pins
#: the transcribed decisions, the readings, the variants and every clinical_core source but the report.
#: A change needs a recorded reason, and the filter must be run again under the new freeze.
FROZEN_DIGEST = "cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26"


def test_the_decisions_and_their_readings_are_frozen():
    assert bc.FREEZE_EXCLUDED == ("clinical_core/blood_filter_report.py",)
    assert "clinical_core/blood_constraints.py" in bc.freeze_sources()
    assert "clinical_core/blood_anchors.py" in bc.freeze_sources()
    assert bc.freeze_digest() == FROZEN_DIGEST, (
        "the frozen decisions, readings or a clinical_core source changed: record why, then refreeze and refilter")


def test_the_faculty_envelopes_are_transcribed_as_approved():
    d = bc.DECISIONS
    assert d["untreated_output"]["gi_bleed_57m"] == {30: (0.85, 0.95), 60: (0.70, 0.85), 120: (0.45, 0.65)}
    assert d["untreated_output"]["gi_bleed_72f"] == {30: (0.90, 0.98), 60: (0.80, 0.92), 120: (0.60, 0.78)}
    assert d["untreated_hb_fall"]["gi_bleed_57m"] == {60: (0.2, 0.5), 120: (0.4, 0.9)}
    assert d["untreated_hb_fall"]["gi_bleed_72f"] == {60: (0.1, 0.4), 120: (0.3, 0.7)}
    assert d["FD-BLD-01"]["envelope"] == (0.7, 1.2)
    assert (d["FD-BLD-02"]["gi_bleed_57m"], d["FD-BLD-02"]["gi_bleed_72f"]) == ((0.15, 0.40), (0.10, 0.30))
    assert d["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert d["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert d["FD-BLD-06"]["envelopes"] == {1000: (0.2, 0.5), 2000: (0.4, 0.8)}
    assert d["FD-BLD-07"]["envelopes"] == {60: (0.10, 0.25), 120: (0.20, 0.45), 240: (0.30, 0.60)}
    assert "not approved as a physiological constant" in d["second_unit"]["meaning"]
    assert "no fixed g/dL decrement" in d["FD-BLD-09"]["meaning"]
    policy = d["bleed_rate_authority"]
    assert (policy["parameter"], policy["policy"]) == ("blood_loss_ml_per_min", "CASE_OVERRIDES_FAMILY_DEFAULT")
    assert "no numeric bleed rate is approved" in policy["meaning"]


def test_fd_bld_is_approved_as_behaviour_and_no_hidden_parameter_is_approved():
    assert bc.FD_BLD_STATUS == {f"FD-BLD-0{index}": "FACULTY_APPROVED" for index in range(1, 10)}
    assert bc.APPROVAL_SCOPE == "clinical behavior/envelope approved; hidden model parameters remain unapproved"
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert [(p.family, p.parameter, p.policy) for p in migration_authority.AUTHORITY_POLICIES] == [
        ("gi_bleed", "blood_loss_ml_per_min", "CASE_OVERRIDES_FAMILY_DEFAULT")]
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()


def test_the_region_is_the_p2i2u_grid_and_the_probes_are_off_it():
    assert bc.REGION == {name: tuple(blood_anchors.EXPLORATION[name]) for name in blood_anchors.PARAMETERS}
    assert set(bc.SHARED) | set(bc.CASE_DIMS) == set(bc.PARAMETERS)
    assert all(bc.off_grid(point) for point in bc.PROBES.values())
    assert not bc.off_grid({**bc.PROBES["P1"], "bleed_ml_per_min": 2.5})
    assert set(bc.VARIANTS) == set(report.VARIANTS_ES) and set(bc.CONSTRAINTS) == set(report.OPERATIONAL_ES)


def test_the_blood_reading_premise_holds_on_the_probes():
    assert bc.dependencies()["largest_blood_difference"] == 0.0


def test_no_lactate_no_legacy_and_no_direct_v_or_hb_drift_enters_a_constraint():
    tree = ast.parse(Path(bc.__file__).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names} | {node.module for node in ast.walk(tree)
                                            if isinstance(node, ast.ImportFrom) and node.module}
    assert not imported & {"faculty_constraints", "lactate_constraints", "lactate_slice", "legacy_adapter",
                           "contracts_legacy", "comparison", "family_engine", "decision_pack"}
    text = json.dumps(bc.IMPLEMENTATION) + json.dumps(bc.VARIANTS)
    assert "lactate" not in text.lower() and "legacy" not in text.lower()
    from clinical_core.integration import run
    values = {**blood_anchors.REFERENCE, **bc.PROBES["P1"]}
    for case in bc.CASES:
        for scenario, extra in (("untreated", {}), ("red_cells", {}), ("crystalloid", {"volume_ml": 1000.0}),
                                ("acute_loss", {"loss_ml": bc.ACUTE_LOSS_ML}), ("stopped_bleed", {})):
            anchors, profile, full = bc._setup(case, values)
            result = run(anchors, bc._items(case, scenario, full, **extra), 60, profile)
            # Every V and Hb change goes through the shared blood state: nothing is written outside it.
            end = result.states[-1].blood
            assert end.outside_v == 0.0 and end.outside_hb == 0.0, (case, scenario)
            assert not any(delta.channel is Channel.HB and delta.source.kind is SourceKind.SCRIPTED_EVENT
                           for record in result.records for delta in record.deltas), (case, scenario)


def test_the_probe_evaluation_reads_every_constraint_and_variant():
    result = bc.evaluate(bc.CASES[0], bc.PROBES["P2"])
    assert set(result["verdicts"]) == {"primary", *(v for v in bc.VARIANTS if v != "V8_common_bleed_rate")}
    assert all(set(verdicts) == set(bc.CONSTRAINTS) for verdicts in result["verdicts"].values())
    assert result["rows"]["red_cells"]["output"][0] == pytest.approx(1.0)


def test_the_count_matches_brute_force_on_an_off_grid_region():
    p1, p2 = bc.PROBES["P1"], bc.PROBES["P2"]
    region = {name: (p1[name],) for name in bc.PARAMETERS}
    for name in ("bleed_ml_per_min", "preload_fraction", "arrival_circulating_volume_ml", "plasma_refill_tau_min"):
        region[name] = tuple(sorted({p1[name], p2[name]}))
    table = bc.tables(region)
    sets = [(name,) for name in bc.CONSTRAINTS] + [bc.CONSTRAINTS, ("U-OUT", "U-HB", "FD-BLD-03")]
    for names in sets:
        joint = common = 0
        alone = {case: 0 for case in bc.CASES}
        for combination in itertools.product(*(region[n] for n in bc.SHARED)):
            shared = dict(zip(bc.SHARED, combination))
            ok = {}
            for case in bc.CASES:
                ok[case] = []
                for bleed in region[bc.BLEED]:
                    for position in region[bc.POS]:
                        values = {**shared, bc.BLEED: bleed, bc.POS: position}
                        if all(bc.passes(n, case, *bc._row(table, case, n, values, None)[:1], None,
                                         bc._row(table, case, n, values, None)[1]) for n in names):
                            ok[case].append(bleed)
                alone[case] += len(ok[case])
            joint += len(ok[bc.CASES[0]]) * len(ok[bc.CASES[1]])
            common += sum(1 for a in ok[bc.CASES[0]] for b in ok[bc.CASES[1]] if a == b)
        counted = bc.count(table, region, None, names)
        assert (counted["joint"], counted["alone"]) == (joint, alone), names
        assert bc.count(table, region, "V8_common_bleed_rate", names)["joint"] == common, names


def test_the_sensitivity_was_computed_with_the_frozen_code_on_probes_only():
    data = json.loads(SENSITIVITY.read_text(encoding="utf-8"))
    assert data["freeze_digest"] == FROZEN_DIGEST
    assert set(data["sensitivity"]) == {f"{label}|{case}" for label in bc.PROBES for case in bc.CASES}
    assert data["dependencies"]["largest_blood_difference"] == 0.0


def test_the_document_definitions_and_sensitivity_are_generated():
    document = DOCUMENT.read_text(encoding="utf-8")
    assert report.apply(document, "definiciones", report.render_definitions()) == document
    data = json.loads(SENSITIVITY.read_text(encoding="utf-8"))
    assert report.apply(document, "sensibilidad", report.render_sensitivity(data)) == document
