"""Phase 2 shadow core, P2I-2U: patient-level faculty anchors for the shared haemorrhage state.

Decision support only: these tests pin that the committed surfaces are the current code's, that the
internal constants are never offered for approval on their own, that kappa and lambda (and the
extraction reserve) stay non-identifiable separately, and that no lactate filter runs.
"""
import ast
import json
import math
from pathlib import Path

import pytest

from clinical_core import blood_anchors as ba, blood_probes, calibration, migration_authority
from clinical_core.derived import DEFAULT_PROFILE

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2U_ANCLAS_HEMORRAGIA_COMPARTIDA.md"
DATA = ROOT / "docs" / "revision" / "P2I2U_blood_anchors.json"


@pytest.fixture(scope="module")
def data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_current_code(data):
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["anchors_digest"] == ba.anchors_digest(), "the anchors are stale: regenerate them"
    assert data["anchors_digest"] in document
    assert ba.apply(document, ba.render(data)) == document, (
        "the document differs from the anchors: run python -m clinical_core.blood_anchors --write")


@pytest.mark.parametrize("case", ba.CASES)
def test_the_committed_references_are_the_current_cores(data, case):
    anchors, profile, values = ba.setup(case)
    states, stop = ba.trajectory(anchors, ba.contributors(case, "untreated", values), 120, profile)
    assert stop is None and data["untreated"][case]["reference_stop"] is None
    assert data["untreated"][case]["reference"]["120"] == _plain(ba.reading(states[120], anchors, profile))
    assert data["red_cells"][case]["reference"] == _plain(dict(zip(("before", "one", "two"),
                                                                  ba._red_cell_rows(case)[0])))
    assert data["crystalloid"][case]["1000"]["reference"] == _plain(ba._crystalloid_pair(case, 1000.0, {}))
    assert data["refill"][case]["acute_loss"]["reference"] == _plain(ba._refill_pair(case, "acute_loss", {}))


def test_the_reference_is_the_canonical_provisional_profile_and_inside_every_exploration():
    anchors, profile, values = ba.setup(ba.CASES[0])
    for name in ("arrival_circulating_volume_ml", "plasma_refill_target_share", "plasma_refill_tau_min",
                 "plasma_refill_capacity_ml", "preload_curve_scale_ml", "volume_preload_kappa"):
        assert getattr(profile, name) == getattr(DEFAULT_PROFILE, name), name
    for name, reference in ba.REFERENCE.items():
        assert reference in ba.EXPLORATION[name], name
    assert set(ba.PARAMETERS) == set(ba.EXPLORATION)


def test_kappa_with_lambda_and_the_reserve_change_no_anchor(data):
    gauge = ba.gauge()
    assert all(value < 1e-9 for value in gauge["kappa_lambda_largest_change"].values())
    assert all(value < 1e-9 for value in gauge["reserve_largest_change"].values())
    classes = data["identifiability"]["classes"]
    assert classes["volume_preload_kappa"] == classes["preload_curve_scale_ml"] == classes["reserve"] == \
        ba.SEPARATELY
    assert set(classes) == set(ba.PARAMETERS) | {"volume_preload_kappa", "preload_curve_scale_ml"}
    assert set(classes.values()) <= {ba.WELL, ba.PARTIAL, ba.POOR, ba.SEPARATELY}


def test_the_classes_follow_the_declared_criterion(data):
    ident = data["identifiability"]
    for parameter in ba.PARAMETERS:
        if parameter in ba.COMBINATIONS:
            continue
        shares = [ident["shares"][anchor][parameter] for anchor in ba.ANCHORS]
        dominant = any(ident["shares"][a][parameter] == 1.0 and sorted(ident["shares"][a].values())[-2] < ba.DOMINANT
                       for a in ba.ANCHORS)
        expected = ba.WELL if dominant else ba.PARTIAL if max(shares) >= ba.NOTICEABLE else ba.POOR
        assert ident["classes"][parameter] == expected, parameter


def test_the_second_units_smaller_output_gain_is_structural(data):
    """Not a finding: with the exponential preload curve, the second unit's output gain over the first's is
    exp(-unit volume / (lambda / kappa)) whatever the position, B0 or unit Hb (P2I-2U adversarial review)."""
    for case in ba.CASES:
        for changes in ba._grid(ba.RED_CELL_GRID):
            (before, one, two), _, values = ba._red_cell_rows(case, **changes)
            ratio = (two["output_rel"] - one["output_rel"]) / (one["output_rel"] - before["output_rel"])
            assert ratio == pytest.approx(math.exp(-values["red_cell_unit_volume_ml"]
                                                   / values["preload_scale_over_kappa_ml"]), abs=1e-9)
        item = data["red_cells"][case]
        assert item["diminishing_output"] == 1.0
        reference = item["reference"]
        assert (reference["two"]["output_rel"] - reference["one"]["output_rel"]
                < reference["one"]["output_rel"] - reference["before"]["output_rel"])
        assert reference["one"]["responsiveness"] < reference["before"]["responsiveness"]


def test_the_worksheet_asks_patient_level_questions_and_records_only_the_faculty_selection():
    """P2I-2V: FD-BLD-01..09 and the untreated anchors A and B are FACULTY_APPROVED as clinical behaviour /
    envelopes (hidden parameters unapproved); C and D were not decided."""
    document = DOCUMENT.read_text(encoding="utf-8")
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in document.splitlines() if line.startswith("| FD-BLD-")]
    assert [row[0] for row in rows] == [f"FD-BLD-0{index}" for index in range(1, 10)]
    assert all(row[4] and row[5] == "FACULTY_APPROVED" for row in rows)
    assert "conducta clínica / envolvente aprobada; los parámetros ocultos del modelo siguen sin aprobar" in document
    untreated = [[cell.strip() for cell in line.strip().strip("|").split("|")]
                 for line in document.splitlines() if line[:4] in ("| A ", "| B ", "| C ", "| D ")]
    assert [row[0] for row in untreated] == ["A", "B", "C", "D"]
    assert [row[5] for row in untreated] == ["FACULTY_APPROVED", "FACULTY_APPROVED", "ABIERTA", "ABIERTA"]
    assert untreated[2][4] == untreated[3][4] == ""
    internal = ("B0", "κ", "λ", "τ del relleno", "meta del relleno", "capacidad del relleno", "Hb de la unidad",
                "volumen de la unidad")
    assert not any(name in row[1] for row in rows for name in internal), "a question asks for an internal constant"
    assert "RETIRED — INVALIDATED BY SHARED HAEMORRHAGE STATE" in document


def test_no_internal_constant_is_approved_or_offered_alone_and_no_authority_is_populated():
    statuses = {entry.status for entry in calibration.REGISTRY.values()}
    assert calibration.FACULTY_APPROVED not in statuses
    for name in ("arrival_circulating_volume_ml", "plasma_refill_target_share", "plasma_refill_tau_min",
                 "plasma_refill_capacity_ml", "red_cell_unit_hb_g_dl"):
        assert "not decided directly" in calibration.REGISTRY[name].rationale, name
    assert "bookkeeping only" in calibration.REGISTRY["volume_preload_kappa"].rationale
    assert "never decided alone" in calibration.REGISTRY["preload_curve_scale_ml"].rationale
    assert ba.PREFERRED_POLICY == "CASE_OVERRIDES_FAMILY_DEFAULT"
    assert set(ba.POLICY_COMPARISON) == {"CASE_OVERRIDES_FAMILY_DEFAULT", "CASE_REQUIRED", "FAMILY_FIXED_VALUE",
                                         "FAMILY_ALLOWED_RANGE"} == set(ba.POLICIES_ES)
    # P2I-2V: the bleed rate's policy category is decided; no family default (no rate) is approved.
    assert [(p.family, p.parameter, p.policy) for p in migration_authority.AUTHORITY_POLICIES] == [
        ("gi_bleed", "blood_loss_ml_per_min", "CASE_OVERRIDES_FAMILY_DEFAULT")]
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == ()


def test_no_lactate_filter_runs_and_lactate_is_context_only():
    tree = ast.parse(Path(ba.__file__).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"faculty_constraints", "lactate_constraints", "decision_pack", "oxygen_probes"}
    assert "lactate" not in " ".join(ba.ANCHORS)


def test_the_untreated_surfaces_count_the_stopped_runs(data):
    """A stopped run is never silently dropped: the envelopes say how many still perfuse, and the "with
    stopped" envelopes and the identifiability anchors give it output 0 and the deficit it stopped with."""
    for case in ba.CASES:
        item = data["untreated"][case]
        assert item["perfusing"]["120"] == item["runs"] - item["stopped_before_120"]
        assert item["envelopes"]["120"]["output_rel"]["n"] == item["perfusing"]["120"]
        assert item["with_stopped"]["120"]["output_rel"]["n"] == item["runs"]
        if item["stopped_before_120"]:
            assert item["with_stopped"]["120"]["output_rel"]["min"] == 0.0
            assert (item["with_stopped"]["120"]["effective_deficit"]["max"]
                    >= item["envelopes"]["120"]["effective_deficit"]["max"])
    for case in ba.CASES:
        for item in data["crystalloid"][case].values():
            assert item["times"]["20"]["output_rel"]["n"] == item["runs"]
            assert item["times"]["120"]["output_rel"]["n"] <= item["runs"] - max(item["stopped_with"],
                                                                                 item["stopped_without"])
    stopped = ba.anchor_values(ba.CASES[0], bleed_ml_per_min=5.0)
    assert stopped["untreated_output_120"] == 0.0 and stopped["untreated_hb_change_120"] is None
    assert stopped["untreated_deficit_120"] is not None


def test_each_worksheet_row_constrains_what_its_evidence_shows(data):
    """FD-BLD-04 shows the output response, so it names the output anchor (the arrival position drives it);
    FD-BLD-05 shows what remains, absolute and as a share of the peak, so it names both anchors."""
    ident = data["identifiability"]
    rows = {identifier: anchors for identifier, _, anchors in ba.WORKSHEET}
    assert "crystalloid_1l_output_gain_20" in rows["FD-BLD-04"]
    assert "preload_fraction" in ba._drivers(ident, rows["FD-BLD-04"])
    assert set(rows["FD-BLD-05"]) == {"crystalloid_1l_retained_60", "crystalloid_1l_retained_share_60"}
    assert ident["shares"]["crystalloid_1l_retained_share_60"]["crystalloid_effective_ml_per_ml"] < 1e-9
    assert "preload_fraction" in ba.CRYSTALLOID_GRID
    assert all(anchor in ba.ANCHORS for _, _, anchors in (*ba.WORKSHEET, *ba.UNTREATED_QUESTIONS) for anchor in anchors)


def test_the_anchors_digest_is_its_own():
    assert ba.anchors_digest() != blood_probes.probes_digest()
