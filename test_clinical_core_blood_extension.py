"""Phase 2 shadow core, P2I-2W: the limited extension of the P2I-2V-R open grid edges.

These tests pin that the faculty constraints are P2I-2V-R's byte for byte, that only the dimensions the committed
report flagged as open are extended, by a continuation of their own spacing that reads no count (an ambiguous
spacing is not extended), that the design is sparse, disjoint and centred on the surviving region, that grid
truncation is an edge status apart from identifiability, that every verdict is a frozen one, and that the
extension points, the design and the policy were frozen before any extended candidate was evaluated.
"""
import hashlib
import inspect
import json
import math
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_extension as be

ROOT = Path(__file__).resolve().parent
#: The P2I-2W freeze: the extension points, the design, the evaluation policy and every clinical_core source but
#: the two reports, committed before any extended candidate was evaluated.
FROZEN_DIGEST = "5257b2336caa76819bdc1f5f3a946dc440dbff88c9e101d9ed25c38287772f6e"
#: clinical_core/blood_extension.py as committed with that freeze (6a0d3b8). P2I-2W is closed (2026-10-28): its
#: record is not regenerated, and the live digest moved when P2I-2X added clinical_core sources (it has its own).
P2I2W_EXTENSION_SHA = "87429c2ed0b453bb33b2107fdfa453ffe6d78e5ffbb26364eab7e8228556ce47"
#: clinical_core/blood_constraints.py as P2I-2V-R froze it (7c073ad).
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
COMMON, POS57, POS72 = be.COMMON, be.POSITION["gi_bleed_57m"], be.POSITION["gi_bleed_72f"]
TARGET, TAU, BAG = "plasma_refill_target_share", "plasma_refill_tau_min", "crystalloid_effective_ml_per_ml"


@pytest.fixture(scope="module")
def data():
    return be.record()


def test_the_faculty_constraints_are_p2i2vr_byte_for_byte():
    assert hashlib.sha256((ROOT / "clinical_core" / "blood_constraints.py").read_bytes()).hexdigest() == (
        P2I2VR_CONSTRAINTS_SHA)
    assert bc.CONSTRAINTS == ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-04", "FD-BLD-05",
                              "FD-BLD-06", "FD-BLD-07", "FD-BLD-08", "FD-BLD-09")
    assert bc.DIAGNOSTIC_ONLY == ("FD-BLD-03",) and bc.U_HB_STATUS == "FACULTY_APPROVED v2"
    assert bc.FD_BLD_STATUS["FD-BLD-03"] == "FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER"


def test_the_extension_is_frozen():
    sources = be.freeze_sources()
    assert {"clinical_core/blood_constraints.py", "clinical_core/blood_extension.py",
            "clinical_core/calibration.py"} <= set(sources)
    assert not set(be.FREEZE_EXCLUDED) & set(sources)
    # P2I-2W is closed: the module that holds its rule, points, design and policy is the frozen one, byte for byte;
    # its record (below) keeps the digest it ran with.
    assert hashlib.sha256((ROOT / "clinical_core" / "blood_extension.py").read_bytes()).hexdigest() == (
        P2I2W_EXTENSION_SHA), "the P2I-2W extension changed after its freeze: record why"


def test_the_record_is_the_committed_p2i2vr_filter(data):
    assert data["freeze_digest"] == be.P2I2VR_DIGEST and data["revision"] == "P2I-2V-R"
    assert data["primary"]["joint"] == 4896


def test_only_the_dimensions_the_report_flagged_open_are_extended(data):
    assert be.reported_open_edges(data) == be.OPEN_EDGES
    assert set(be.OPEN_EDGES) == {COMMON, BAG, TARGET, TAU, POS57, POS72}
    assert set(be.OPEN_EDGES.values()) == {"upper"}
    # The POORLY_IDENTIFIED dimensions keep every explored value (both edges), but were neither flagged nor
    # authorized: they are reported as open on both edges and not extended.
    poor = [label for label, item in data["identifiability"]["classes"].items() if item["class"] == bc.POOR]
    assert len(poor) == 7 and not set(poor) & set(be.OPEN_EDGES)
    assert {be.edge_status(be.explored(data, label), be.surviving(data, label)) for label in poor} == {be.OPEN_BOTH}
    assert all(be.edge_status(be.explored(data, label), be.surviving(data, label)) == be.OPEN_UPPER
               for label in be.OPEN_EDGES)


def test_the_continuation_follows_each_spacing_and_reads_no_count():
    assert be.spacing((1.25, 2.5, 5.0)) == (be.GEOMETRIC, 2.0)
    assert be.spacing((60.0, 120.0, 240.0)) == (be.GEOMETRIC, 2.0)
    assert be.spacing((0.25, 0.5, 0.75)) == (be.ARITHMETIC, 0.25)
    assert be.spacing((0.2, 0.35, 0.5))[0] == be.ARITHMETIC
    assert be.spacing((0.125, 0.2, 0.3)) == (be.AMBIGUOUS, None)
    ext = be.extension()
    assert {label: item["points"] for label, item in ext.items()} == {
        COMMON: [10.0, 20.0], BAG: [], TARGET: [1.0], TAU: [480.0, 960.0], POS57: [0.65, 0.8], POS72: [0.75, 0.9]}
    assert ext[TARGET]["dropped"] == [1.25], "a share of the loss above 1 is outside the domain: dropped, not moved"
    assert ext[BAG]["spacing"] == be.AMBIGUOUS and ext[BAG]["not_evaluated"] == {
        "by the last difference": [0.4, 0.5], "by the last ratio": [0.45, 0.675]}
    for function in (be.spacing, be.continuation):
        source = inspect.getsource(function)
        assert "marginal" not in source and "record" not in source and "surviv" not in source
    assert inspect.signature(be.continuation).parameters.keys() == {"values", "side", "parameter"}


def test_the_design_is_sparse_disjoint_and_centred_on_the_survivors(data):
    boxes = be.design(data)
    base = be.base_box(data)
    kinds = [box["kind"] for box in boxes]
    assert (kinds.count("base"), kinds.count("one"), kinds.count("pair"), kinds.count("corner")) == (1, 9, 32, 1)
    assert len({json.dumps(box["fixed"], sort_keys=True) for box in boxes}) == len(boxes), "disjoint boxes"
    points = be.extended()
    pairs = {tuple(sorted(box["fixed"])) for box in boxes if box["kind"] == "pair"}
    assert len(pairs) == math.comb(len(points), 2) == 10 and all(box["why"] for box in boxes if box["kind"] == "pair")
    for box in boxes:
        assert all(value in points[label] for label, value in box["fixed"].items())
        values = be._box_values(box, base)
        for label in be.COORDS:
            if label not in box["fixed"]:
                assert values[label] == tuple(be.surviving(data, label)), "no rejected value is re-explored"
    assert boxes[-1]["fixed"] == {label: values[0] for label, values in points.items()}
    extended = sum(box["size"] for box in boxes if box["kind"] != "base")
    assert extended == 2_375_082
    full = math.prod(len(be.explored(data, label)) + len(points.get(label, ())) for label in be.COORDS)
    assert full == 49_207_500 and extended < 0.05 * full, "not a full Cartesian sweep of the extended grid"
    assert all(len(box["fixed"]) <= 2 for box in boxes if box["kind"] != "corner")


def test_edge_status_is_orthogonal_to_identifiability(data):
    assert be.edge_status([1, 2, 3], [2]) == be.INTERIOR
    assert be.edge_status([1, 2, 3], [1, 2]) == be.OPEN_LOWER
    assert be.edge_status([1, 2, 3], [2, 3]) == be.OPEN_UPPER
    assert be.edge_status([1, 2, 3], [1, 2, 3]) == be.OPEN_BOTH
    assert be.edge_status([1, 2, 3], []) is None
    # One surviving value at the edge: WELL_CONSTRAINED by the frozen count rule, never identified.
    assert (be.identifiability("x", [1, 2, 3], [3]), be.edge_status([1, 2, 3], [3])) == (bc.WELL, be.OPEN_UPPER)
    for label, item in data["identifiability"]["classes"].items():
        if item.get("left"):
            parameter = label.partition("|")[0]
            assert be.identifiability(parameter, be.explored(data, label), be.surviving(data, label)) == item["class"]


def test_every_verdict_is_a_frozen_reading_and_no_probe_is_read():
    assert "bc.passes(name, case, row, None, off)" in inspect.getsource(be.verdict)
    source = inspect.getsource(be)
    assert "def passes" not in source and "VARIANTS" not in source
    for module in (bc, be):
        text = inspect.getsource(module)
        assert "HISTORICAL" not in text and "bands.probe" not in text and "import bands" not in text
    assert be.SOURCES == ("untreated", "untreated_blood", "red_cells", "retained", "crystalloid", "acute_200",
                          "acute_off_200", "stopped")


def test_a_row_the_frozen_functions_cannot_read_is_recorded_as_unreadable(monkeypatch):
    """A row the frozen functions cannot read is UNREADABLE with its message, and its verdict is None (never False).
    How candidates and edges treat it is pinned on the run's record (test_no_joint_candidate_is_unreadable...)."""
    def stops(*_, **__):
        raise AssertionError("the blood reading's haemodynamics stopped at 3")
    monkeypatch.setattr(bc, "untreated_blood", stops)
    task = ("gi_bleed_57m", "untreated_blood", (20.0, 3000.0, 0.5, 960.0, 100.0))
    assert be._compute(task)[1] == {be.UNREADABLE: "AssertionError: the blood reading's haemodynamics stopped at 3"}
    table = {"gi_bleed_57m": {"untreated_blood": {task[2]: be._compute(task)[1]}}}
    values = dict(zip(bc.TABLE_KEYS["untreated_blood"], task[2]))
    assert be.verdict(table, "gi_bleed_57m", "U-HB", values) is None
    assert "never counted as a faculty bound" in be.POLICY


def test_the_extension_rows_are_the_frozen_tables_rows():
    """The design's rows are computed by the same frozen functions as blood_constraints.tables (one point)."""
    case = "gi_bleed_72f"
    region = {name: (values[1],) for name, values in bc.REGION.items()}
    region[bc.POS] = ("upper",)
    frozen = bc.tables(region, (case,))[case]
    numeric = be.positions(case)["upper"]
    for source in be.SOURCES:
        (key, row), = frozen[source].items()
        key = tuple(numeric if value == "upper" else value for value in key)
        assert be._compute((case, source, key))[1] == row, source


# After the freeze commit: the extension's record ---------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2W_blood_extension.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2W_EXTENSION_BORDES_AUDITORIA.md"


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_the_extension_ran_with_the_frozen_code_on_the_declared_design(result, data):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["record_digest"] == be.P2I2VR_DIGEST
    assert result["revision"] == "P2I-2W" and result["open_edges"] == be.OPEN_EDGES == result["reported_open_edges"]
    assert result["extension"] == _plain(be.extension(data)) and result["design"] == _plain(be.design(data))
    assert result["base"] == _plain({label: list(values) for label, values in be.base_box(data).items()})
    assert set(result["boxes"]) == {box["name"] for box in result["design"]}
    assert result["candidates"] == {"extended": 2_375_082, "base": 104_976}
    assert result["policy"] == be.POLICY and result["rule"] == be.RULE


def test_the_surviving_box_reproduces_the_frozen_filter(result, data):
    base = result["boxes"]["base"]
    assert base["survives"] == data["primary"]["joint"] == 4896 and base["unreadable"] == 0
    for label in be.COORDS:
        parameter = label.partition("|")[0]
        for value, raw in zip(be.explored(data, label), data["region"][parameter]):
            if value in result["base"][label]:
                assert base["marginal"][label][str(value)] == data["primary"]["marginal"][label][str(raw)], label
    assert base["with_fd_bld_03"] == data["fd_bld_03"]["primary"]["joint"]


def test_no_joint_candidate_is_unreadable_and_each_case_s_unreadables_are_reported(result):
    """The edge table counts survivors only: a value whose candidates were all UNREADABLE would read as a bound,
    against the policy. In this run no joint candidate is UNREADABLE, so the table is not affected; each case's own
    UNREADABLE candidates (sensitivity) are reported in the document, never as a rejection."""
    assert all(stats["unreadable"] == 0 for stats in result["boxes"].values())
    unreadable = {(name, case): n for name, stats in result["boxes"].items()
                  for case, n in stats["alone_unreadable"].items() if n}
    assert unreadable == {("bleed_ml_per_min|common=10 & preload_fraction|gi_bleed_57m=0.65", "gi_bleed_57m"): 1944,
                          ("bleed_ml_per_min|common=20 & preload_fraction|gi_bleed_72f=0.9", "gi_bleed_72f"): 1836}
    assert sum(result["unreadable_rows"].values()) == 5514
    document = DOCUMENT.read_text(encoding="utf-8")
    assert "0 (+1944 ilegibles)" in document and "0 (+1836 ilegibles)" in document


def test_the_counts_are_coherent(result):
    assert result["contradictions"] == []
    for name, stats in result["boxes"].items():
        assert stats["survives"] + stats["rejected"] + stats["unreadable"] == stats["size"], name
        assert stats["survives"] <= min(stats["alone"].values()), name
        assert sum(stats["marginal"][be.COMMON].values()) == stats["survives"], name
        assert stats["with_fd_bld_03"] <= stats["survives"], name
        assert max(stats["failing"].values()) <= stats["rejected"] <= sum(stats["failing"].values()), name
        assert all(stats["sole"][n] <= stats["failing"][n] for n in bc.CONSTRAINTS), name


def test_the_edge_table_is_recomputed_from_the_boxes(result, data):
    assert result["edges"] == _plain(be.edges(data, result["extension"], result["boxes"]))
    for label in be.COORDS:
        item = result["edges"][label]
        assert item["edge"] == be.edge_status(item["explored"], item["left"])
        assert item["class"] == be.identifiability(label.partition("|")[0], item["explored"], item["left"])


def test_the_moved_representatives_are_the_frozen_evaluation(result, data):
    """Each moved representative differs from its P2I-2V-R original in one coordinate, and the design's cached
    verdicts for the middle one are the frozen blood_constraints.evaluate verdicts, run live."""
    for point, item in result["representatives"].items():
        label, _, value = point.rpartition("=")
        parameter, case_of = label.partition("|")[0], label.partition("|")[2]
        for tag, entry in item.items():
            original = data["representatives"][tag]["values"]
            for case in bc.CASES:
                before = {**original[case], bc.POS: be.positions(case)[original[case][bc.POS]]}
                changed = {n for n in before if before[n] != entry["values"][case][n]}
                expected = {parameter} if case_of in ("common", "", case) and float(value) != before[parameter] else set()
                assert changed == expected, (point, tag, case)
        middle = item["middle"]
        for case in bc.CASES:
            if None in middle["verdicts"][case].values():
                with pytest.raises(Exception):  # an UNREADABLE row: the frozen evaluation cannot read it either
                    bc.evaluate(case, middle["values"][case])
                continue
            live = bc.evaluate(case, middle["values"][case])["verdicts"]["primary"]
            assert {n: live[n] for n in be.READINGS} == middle["verdicts"][case], (point, case)


def test_nothing_is_selected_approved_or_lactate_filtered(result):
    from clinical_core import migration_authority
    text = json.dumps(result)
    assert "FACULTY_APPROVED" not in text and "selected" not in text
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()
    source = inspect.getsource(be)
    assert "lactate_constraints" not in source and "FD-LAC" not in source and "faculty_constraints" not in source


def test_the_document_blocks_are_generated(result):
    """The record's numbers stay generated from its JSON; its Level-1 audit block is the record as it ran (the live
    registry moved on in P2I-2X, which owns the current audit)."""
    from clinical_core import blood_extension_report as report, calibration
    document = DOCUMENT.read_text(encoding="utf-8")
    for block, rendered in (("regla", report.render_rule(result)), ("extension", report.render_extension(result))):
        assert report.apply(document, block, rendered) == document, block
    assert set(report.AUDIT_ES) == set(calibration.LEVEL1_DIRECT_WRITES)
    assert "Ampliado por P2I-2X" in document and FROZEN_DIGEST in document
