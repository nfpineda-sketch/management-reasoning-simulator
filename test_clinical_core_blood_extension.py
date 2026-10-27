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
    assert be.freeze_digest() == FROZEN_DIGEST, (
        "a clinical_core source, the extension, the design or the policy changed after the freeze: record why")


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


def test_a_row_the_frozen_functions_cannot_read_is_unreadable_never_a_bound(monkeypatch):
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
