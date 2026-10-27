"""Phase 2 shadow core, P2I-2V and P2I-2V-R: the faculty's shared-blood anchors as frozen constraints.

These tests pin that the faculty decisions are transcribed as approved (U-HB v2 with no minimum, FD-BLD-03
qualitative and not filtering), that the readings and the filter were frozen before the region was
filtered (and each reported filter ran with its freeze), that V5 reads exactly what P2I-2V declared, that
the primary uses one common bleed rate, that the blood reading's premise holds, that no lactate, legacy
trajectory or direct V / Hb drift enters a constraint, and that no hidden parameter is approved. P2I-2V's
own filter, diagnostic and document stay its historical record: they are not regenerated.
"""
import ast
import itertools
import json
from pathlib import Path

import pytest

from clinical_core import blood_anchors, blood_constraints as bc, blood_filter_report as report, calibration
from clinical_core import migration_authority
from clinical_core.integration import run
from clinical_core.provenance import BloodProcess, SourceKind
from clinical_core.state import Channel

ROOT = Path(__file__).resolve().parent
REVISION = ROOT / "docs" / "revision"
DOCUMENT = REVISION / "P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md"
SENSITIVITY = REVISION / "P2I2VR_blood_sensitivity.json"
FILTER = REVISION / "P2I2VR_blood_filter.json"

#: The P2I-2V-R freeze, recorded before the refilter ran (P2I-2V-R "freeze before refilter"). It pins the
#: transcribed decisions, the readings, the variants and every clinical_core source but the report. Its
#: reason: the faculty withdrew U-HB's minimum and demoted FD-BLD-03 from filtering; V5 is implemented as
#: declared; the common bleed rate is primary; the Level-2 direct-V probes are historical. A change needs a
#: recorded reason, and the filter must be run again under the new freeze.
FROZEN_DIGEST = "a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893"
#: P2I-2V's freeze (commit 3f86464): its filter, diagnostic and document are a historical record.
P2I2V_DIGEST = "cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26"


def test_the_decisions_and_their_readings_are_frozen():
    assert bc.FREEZE_EXCLUDED == ("clinical_core/blood_filter_report.py",)
    assert "clinical_core/blood_constraints.py" in bc.freeze_sources()
    assert "clinical_core/blood_anchors.py" in bc.freeze_sources() and "clinical_core/bands.py" in bc.freeze_sources()
    assert bc.freeze_digest() == FROZEN_DIGEST, (
        "the frozen decisions, readings or a clinical_core source changed: record why, then refreeze and refilter")


def test_the_faculty_envelopes_are_transcribed_as_approved():
    d = bc.DECISIONS
    assert d["untreated_output"]["gi_bleed_57m"] == {30: (0.85, 0.95), 60: (0.70, 0.85), 120: (0.45, 0.65)}
    assert d["untreated_output"]["gi_bleed_72f"] == {30: (0.90, 0.98), 60: (0.80, 0.92), 120: (0.60, 0.78)}
    # U-HB v2 (P2I-2V-R): no minimum decline; the v1 envelopes are kept only as withdrawn.
    assert d["untreated_hb_fall"]["gi_bleed_57m"] == {60: (0.0, 0.5), 120: (0.0, 0.9)}
    assert d["untreated_hb_fall"]["gi_bleed_72f"] == {60: (0.0, 0.4), 120: (0.0, 0.7)}
    assert "must not rise" in d["untreated_hb_fall"]["invariant"]
    assert d["untreated_hb_fall_v1_withdrawn"]["gi_bleed_57m"] == {60: (0.2, 0.5), 120: (0.4, 0.9)}
    assert d["FD-BLD-01"]["envelope"] == (0.7, 1.2)
    assert (d["FD-BLD-02"]["gi_bleed_57m"], d["FD-BLD-02"]["gi_bleed_72f"]) == ((0.15, 0.40), (0.10, 0.30))
    assert d["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert d["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert d["FD-BLD-06"]["envelopes"] == {1000: (0.2, 0.5), 2000: (0.4, 0.8)}
    # FD-BLD-07 is unchanged: refill is not weakened to satisfy Hb.
    assert d["FD-BLD-07"]["envelopes"] == {60: (0.10, 0.25), 120: (0.20, 0.45), 240: (0.30, 0.60)}
    assert "not approved as a physiological constant" in d["second_unit"]["meaning"]
    assert "no fixed g/dL decrement" in d["FD-BLD-09"]["meaning"]
    assert "never used to reject a candidate" in d["FD-BLD-03"]["revision"]
    policy = d["bleed_rate_authority"]
    assert (policy["parameter"], policy["policy"]) == ("blood_loss_ml_per_min", "CASE_OVERRIDES_FAMILY_DEFAULT")
    assert "no numeric bleed rate is approved" in policy["meaning"]
    assert "one common GI-family candidate rate" in d["bleed_rate_analysis"]["meaning"]


def test_the_decision_record_and_no_hidden_parameter_is_approved():
    expected = {f"FD-BLD-0{index}": "FACULTY_APPROVED" for index in range(1, 10)}
    expected["FD-BLD-03"] = "FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER"
    assert bc.FD_BLD_STATUS == expected and bc.U_HB_STATUS == "FACULTY_APPROVED v2"
    assert bc.APPROVAL_SCOPE == "clinical behavior/envelope approved; hidden model parameters remain unapproved"
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert [(p.family, p.parameter, p.policy) for p in migration_authority.AUTHORITY_POLICIES] == [
        ("gi_bleed", "blood_loss_ml_per_min", "CASE_OVERRIDES_FAMILY_DEFAULT")]
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()


def test_fd_bld_03_is_reported_and_never_filters():
    assert "FD-BLD-03" not in bc.CONSTRAINTS and bc.DIAGNOSTIC_ONLY == ("FD-BLD-03",)
    assert bc.READINGS == bc.CONSTRAINTS + ("FD-BLD-03",)
    # No filtering constraint reads the preload position (FD-BLD-03's only input): in passes(), row["position"]
    # appears only inside the FD-BLD-03 branch.
    import inspect
    source = inspect.getsource(bc.passes)
    start = source.index('if name == "FD-BLD-03":')
    end = source.index("if name ==", start + 1)
    assert source.count('row["position"]') == source[start:end].count('row["position"]') == 1


def test_the_region_is_the_p2i2u_grid_and_the_probes_are_off_it():
    assert bc.REGION == {name: tuple(blood_anchors.EXPLORATION[name]) for name in blood_anchors.PARAMETERS}
    assert set(bc.SHARED) | set(bc.CASE_DIMS) == set(bc.PARAMETERS)
    assert all(bc.off_grid(point) for point in bc.PROBES.values())
    assert not bc.off_grid({**bc.PROBES["P1"], "bleed_ml_per_min": 2.5})
    assert set(bc.VARIANTS) == set(report.VARIANTS_ES) and set(bc.READINGS) == set(report.OPERATIONAL_ES)


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


def test_u_hb_v2_has_no_minimum_and_untreated_haemorrhage_never_raises_hb():
    m57 = "gi_bleed_57m"
    assert bc.passes("U-HB", m57, {"fall": {60: 0.0, 120: 0.0}, "max_rise": 0.0})
    assert not bc.passes("U-HB", m57, {"fall": {60: 0.0, 120: 0.95}, "max_rise": 0.0})
    assert not bc.passes("U-HB", m57, {"fall": {60: -0.01, 120: 0.1}, "max_rise": 0.0})
    assert not bc.passes("U-HB", m57, {"fall": {60: 0.1, 120: 0.2}, "max_rise": 1e-6}), "a rise fails the invariant"
    for point in bc.PROBES.values():
        for case in bc.CASES:
            assert bc.untreated_blood(case, {**blood_anchors.REFERENCE, **point})["max_rise"] <= bc.HB_RISE_TOLERANCE
    # Wherever Hb rises in any surface, a volume / red-cell process explains it (crystalloid leaving, a unit).
    values = {**blood_anchors.REFERENCE, **bc.PROBES["P1"]}
    explains = {BloodProcess.CRYSTALLOID_OUT, BloodProcess.RED_CELL_TRANSFUSION}
    for case in bc.CASES:
        for scenario, extra in (("untreated", {}), ("red_cells", {}), ("crystalloid", {"volume_ml": 1000.0}),
                                ("stopped_bleed", {})):
            anchors, profile, full = bc._setup(case, values, blood=True)
            result = run(anchors, bc._items(case, scenario, full, **extra), 120, profile)
            for record, before, after in zip(result.records, result.states, result.states[1:]):
                if after.hb - before.hb > bc.HB_RISE_TOLERANCE:
                    assert {change.process for change in record.blood} & explains, (case, scenario, record.minute)


def test_v5_reads_exactly_what_p2i2v_declared():
    """V5 was declared in P2I-2V ('FD-BLD-04: early contribution read as the bag's net effect on C (with -
    without)') and is implemented in P2I-2V-R without redefinition: the largest net effect on C over minutes
    0-30, same bleeding, over the litre infused, read from the crystalloid table."""
    assert bc.VARIANTS["V5_fd04_net_effect"] == ("FD-BLD-04: early contribution read as the bag's net effect on C "
                                                 "(with - without)")
    m57 = "gi_bleed_57m"
    inside_retained_outside_net = {"early": 0.20, 1000.0: {"net_early": 0.10}}
    assert bc.passes("FD-BLD-04", m57, inside_retained_outside_net)
    assert not bc.passes("FD-BLD-04", m57, inside_retained_outside_net, "V5_fd04_net_effect")
    assert bc._source("FD-BLD-04", "V5_fd04_net_effect") == "crystalloid" and bc._source("FD-BLD-04", None) == "retained"
    point = {**blood_anchors.REFERENCE, **bc.PROBES["P1"]}
    row = bc.crystalloid(m57, point, 1000.0)
    anchors, _, _, with_bag, _ = bc._run(m57, point, "crystalloid", 30, blood=True, volume_ml=1000.0)
    without = bc._run(m57, point, "untreated", 30, blood=True)[3]
    assert row["net_early"] == pytest.approx(max((a.blood.volume_ml - b.blood.volume_ml) / 1000.0
                                                 for a, b in zip(with_bag, without)))
    assert row["net_early"] != row["retained_early"]
    verdicts = bc.evaluate(m57, bc.PROBES["P1"])["verdicts"]
    assert verdicts["V5_fd04_net_effect"]["FD-BLD-04"] == bc.passes(
        "FD-BLD-04", m57, {1000.0: {"net_early": row["net_early"]}}, "V5_fd04_net_effect")


def test_each_declared_variant_changes_a_reading():
    m57, f72 = "gi_bleed_57m", "gi_bleed_72f"
    out = {"output": {30: 0.955, 60: 0.80, 120: 0.50}}
    assert not bc.passes("U-OUT", m57, out) and bc.passes("U-OUT", m57, out, "V1_envelope_tolerance")
    assert not bc.passes("FD-BLD-03", m57, {"position": [0.4, 0.65, 0.7]})
    assert bc.passes("FD-BLD-03", m57, {"position": [0.4, 0.65, 0.7]}, "V2_fd03_both_midpoint")
    assert bc.passes("FD-BLD-03", f72, {"position": [0.4, 0.65, 0.7]})
    assert not bc.passes("FD-BLD-03", f72, {"position": [0.4, 0.65, 0.7]}, "V3_fd03_both_lower")
    weak = {"output": [1.0, 1.05, 1.08], "challenge_gain": 0.2}
    assert bc.passes("FD-BLD-02", m57, weak)
    assert not bc.passes("FD-BLD-02", m57, weak, "V4_fd02_lower_bound_when_responsive")
    row = {"early": 0.20, 1000.0: {"net_early": 0.10}}
    assert bc.passes("FD-BLD-04", m57, row) != bc.passes("FD-BLD-04", m57, row, "V5_fd04_net_effect")
    dilution = {1000.0: {"peak": 0.3, "at_120": 0.1, "peak_from_arrival": 0.6, "from_arrival_120": 0.5},
                2000.0: {"peak": 0.5, "at_120": 0.2, "peak_from_arrival": 0.6, "from_arrival_120": 0.5}}
    assert bc.passes("FD-BLD-06", m57, dilution) and not bc.passes("FD-BLD-06", m57, dilution, "V6_fd06_from_arrival_hb")
    retained = {"early": 0.2, "share": {30: 0.2, 60: 0.15, 120: 0.1, 50: 0.3, 80: 0.3, 140: 0.3}}
    assert bc.passes("FD-BLD-05", m57, retained) and not bc.passes("FD-BLD-05", m57, retained,
                                                                  "V9_fd05_from_end_of_infusion")
    refill = {"share": {60: 0.2, 120: 0.3, 240: 0.4, 70: 0.5, 130: 0.5, 250: 0.5}}
    assert bc.passes("FD-BLD-07", m57, refill) and not bc.passes("FD-BLD-07", m57, refill, "V10_fd07_from_end_of_loss")
    key = (0.5, 120.0, 500.0, 4000.0)
    table = {m57: {"acute_200": {key: "200"}, "acute_500": {key: "500"},
                   "acute_off_200": {(4000.0,): "off200"}, "acute_off_500": {(4000.0,): "off500"}}}
    values = dict(zip(bc.TABLE_KEYS["acute"], key))
    assert bc._row(table, m57, "FD-BLD-07", values, None)[0] == "200"
    assert bc._row(table, m57, "FD-BLD-07", values, "V7_fd07_500_ml")[0] == "500"
    assert bc.CASE_SPECIFIC == "V8_case_specific_bleed_rate" in bc.VARIANTS


def test_the_probe_evaluation_reads_every_reading_and_variant():
    result = bc.evaluate(bc.CASES[0], bc.PROBES["P2"])
    assert set(result["verdicts"]) == {"primary", *(v for v in bc.VARIANTS if v != bc.CASE_SPECIFIC)}
    assert all(set(verdicts) == set(bc.READINGS) for verdicts in result["verdicts"].values())
    assert result["rows"]["red_cells"]["output"][0] == pytest.approx(1.0)


def test_the_count_matches_brute_force_with_a_common_and_a_case_specific_rate():
    p1, p2 = bc.PROBES["P1"], bc.PROBES["P2"]
    region = {name: (p1[name],) for name in bc.PARAMETERS}
    for name in ("bleed_ml_per_min", "preload_fraction", "arrival_circulating_volume_ml", "plasma_refill_tau_min"):
        region[name] = tuple(sorted({p1[name], p2[name]}))
    table = bc.tables(region)
    sets = [(name,) for name in bc.READINGS] + [bc.CONSTRAINTS, ("U-OUT", "U-HB", "FD-BLD-03")]
    for names in sets:
        specific = common = 0
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
            specific += len(ok[bc.CASES[0]]) * len(ok[bc.CASES[1]])
            common += sum(1 for a in ok[bc.CASES[0]] for b in ok[bc.CASES[1]] if a == b)
        counted = bc.count(table, region, None, names)
        assert (counted["joint"], counted["alone"]) == (common, alone), names
        assert bc.count(table, region, bc.CASE_SPECIFIC, names)["joint"] == specific, names
    assert bc.region_size(region, common=True)["joint"] * 2 == bc.region_size(region)["joint"]


def test_the_sensitivity_was_computed_with_the_frozen_code_on_probes_only():
    data = json.loads(SENSITIVITY.read_text(encoding="utf-8"))
    assert data["freeze_digest"] == FROZEN_DIGEST
    assert set(data["sensitivity"]) == {f"{label}|{case}" for label in bc.PROBES for case in bc.CASES}
    assert data["dependencies"]["largest_blood_difference"] == 0.0
    assert all(item["untreated_hb_max_rise"] <= bc.HB_RISE_TOLERANCE for item in data["sensitivity"].values())


def test_the_document_definitions_and_sensitivity_are_generated():
    document = DOCUMENT.read_text(encoding="utf-8")
    assert report.apply(document, "definiciones", report.render_definitions()) == document
    data = json.loads(SENSITIVITY.read_text(encoding="utf-8"))
    assert report.apply(document, "sensibilidad", report.render_sensitivity(data)) == document


# P2I-2V's historical record (freeze cfb8e508...): never regenerated ------------------------------------

def test_the_p2i2v_record_is_kept_as_it_ran():
    for name in ("P2I2V_blood_filter.json", "P2I2V_blood_diagnostic.json", "P2I2V_blood_sensitivity.json"):
        assert json.loads((REVISION / name).read_text(encoding="utf-8"))["freeze_digest"] == P2I2V_DIGEST, name
    document = (REVISION / "P2I2V_ANCLAS_APROBADAS_FILTRO.md").read_text(encoding="utf-8")
    assert P2I2V_DIGEST in document and "Sustituido en parte por P2I-2V-R" in document
    p2i2v = json.loads((REVISION / "P2I2V_blood_filter.json").read_text(encoding="utf-8"))
    diagnosed = json.loads((REVISION / "P2I2V_blood_diagnostic.json").read_text(encoding="utf-8"))
    assert p2i2v["primary"]["joint"] == 0 and diagnosed["dropped"] == "U-HB"
    assert diagnosed["count"]["joint"] == p2i2v["without"]["U-HB"]["joint"]
