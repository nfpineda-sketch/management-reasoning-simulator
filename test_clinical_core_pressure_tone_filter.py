"""Phase 2 shadow core, P2J-3: the faculty pressure / tone observable-envelope filter.

These tests pin the faculty's decisions as frozen (support, envelopes A-I, comparison times, classes, filter order), the
matched comparators (each changes only its intervention), G and H on rebuilt trajectories, the reconstruction of the
counterfactual runs against the core, the filter's accounting, the closure of P2J-2 and the policy: HR never filters,
pressure never feeds HR, sensitivity never rescues, nothing is approved.
"""
import ast
import hashlib
import inspect
import json

import pytest

from clinical_core import acid_base as ab
from clinical_core import baroreflex as br
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import hr_envelope_filter as hf
from clinical_core import hr_primary as hp
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr
from clinical_core import pressure_tone_filter as pf
from clinical_core import vascular_tone as vt

ROOT = pf.ROOT
SOURCE = ROOT / "clinical_core" / "pressure_tone_filter.py"
#: The P2J-3 freeze: the faculty decisions, the P2J-2 record, the support statuses, envelopes A-I, the comparison times
#: and classes, the filter order, the demand, identifiability and verdict rules, the policy and every clinical_core
#: source but the downstream reports, committed before any survivor count on the retained physiology.
FROZEN_DIGEST = "611e1702d44d97ec19c42a78ab1bf1f97de8f0001ec6eb148ed376990ebf2d28"
#: P2J-3 is closed (P2J-4): its module and record are pinned byte for byte, and its freeze is recomputed from the live
#: sources without the later modules, with derived.py and the two tuple-only files at their P2J-3 hashes while only
#: their declared statements changed (baroreflex.p2j3_sources).
P2J3_MODULE_SHA = "54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650"
P2J3_RECORD_SHA = "bcecbe1651df99b9351f58162e99b312b01b23a109e785722d282faeae3151de"
LATER_MODULES = ("clinical_core/baroreflex.py", "clinical_core/rr_audit.py", "clinical_core/acid_base.py")
C57, C72 = pf.C57, pf.C72


@pytest.fixture(scope="module")
def source():
    record = la.record_p2i2ab()
    return la.source_space(record), record["crystalloid_support"]


# The frozen package ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/pressure_tone_filter.py" in sources
    assert "clinical_core/pressure_tone_filter_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/pressure_tone_filter.py", "clinical_core/pressure_tone_filter_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert pf.p2j2_record()["freeze_digest"] == pf.P2J2_DIGEST
    assert hashlib.sha256((vt.ROOT / "clinical_core" / "pressure_tone_filter.py").read_bytes()).hexdigest() == \
        P2J3_MODULE_SHA, "the closed P2J-3 module changed"
    assert hashlib.sha256((vt.ROOT / "docs" / "revision" / "P2J3_pressure_tone_filter.json").read_bytes()).hexdigest() \
        == P2J3_RECORD_SHA
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in LATER_MODULES}
    text = json.dumps({"revision": pf.REVISION, "p2j2": hashlib.sha256(pf.P2J2_RECORD.read_bytes()).hexdigest(),
                       "design": pf.design(), "sources": ab.p2j3_sources(sources)}, sort_keys=True, default=str)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == FROZEN_DIGEST, "a source P2J-3 froze changed"


def test_the_faculty_decisions_are_recorded():
    assert set(pf.FACULTY) == {"decided", "normalization", "timing", "gain", "afterload", "output", "envelopes",
                               "demand", "hr", "scope"}
    assert "not a measured absolute SVR" in pf.FACULTY["normalization"]
    assert "no tone memory" in pf.FACULTY["timing"] and "never rescuing" in pf.FACULTY["gain"]
    assert "not a normal resting output" in pf.FACULTY["output"]


# Support, envelopes, order --------------------------------------------------------------------------------------------

def test_the_support_is_the_faculty_s_and_sensitivity_never_overlaps_the_primary():
    assert pf.GAIN_STATUS == {0.0: "DIAGNOSTIC_NO_RESPONSE_REFERENCE", 0.25: "PRIMARY", 0.5: "PRIMARY",
                              1.0: "PRIMARY", 1.5: "SENSITIVITY_ONLY", 2.0: "SENSITIVITY_ONLY"}
    assert pf.AFTERLOAD_STATUS == {0.3: "PRIMARY_PROVISIONAL_REFERENCE", 0.1: "SENSITIVITY_ONLY",
                                   0.5: "SENSITIVITY_ONLY"}
    assert pf.PRIMARY_PAIRS == ((0.25, 0.3), (0.5, 0.3), (1.0, 0.3))
    assert not set(pf.PRIMARY_PAIRS) & set(pf.SENSITIVITY_PAIRS)
    assert set(pf.PRIMARY_PAIRS) | set(pf.SENSITIVITY_PAIRS) <= set(vt.admissible())
    assert "APPROVED" not in {*pf.GAIN_STATUS.values(), *pf.AFTERLOAD_STATUS.values()}


def test_the_envelopes_carry_the_faculty_bounds():
    env = pf.ENVELOPES
    assert (env["A"]["case"], env["A"]["sbp"], env["A"]["map"], env["A"]["minute"]) == (C57, (40.0, 70.0),
                                                                                         (30.0, 50.0), 120)
    assert (env["B"]["case"], env["B"]["sbp"], env["B"]["map"]) == (C72, (60.0, 95.0), (45.0, 70.0))
    assert (env["F"]["scenario"], env["F"]["sbp"], env["F"]["map"]) == ("P4", (90.0, 140.0), (65.0, 105.0))
    assert "dbp" not in env["F"] and env["G"]["t_abs"] == (1.0, 2.0)
    assert pf.COMPARISON_TIMES == {"C": ("crystalloid volume complete", 120), "D": ("unit 1 complete", 120),
                                   "E": ("unit 2 complete", 120)}
    assert pf.ORDER == ("SUPPORT", "SIMULATION", "G", "H", "A", "B", "F", "C", "D", "E", "I")
    assert {pf.REJECTION_CLASS[n] for n in "ABFCDE"} == {"PRESSURE_ENVELOPE_REJECTION"}
    assert pf.REJECTION_CLASS["I"] == "FD_LAC_REJECTION" and pf.REJECTION_CLASS["G"] == "DOMAIN_REJECTION"
    assert pf.interval(40.0, (40.0, 70.0)) and pf.interval(70.0, (40.0, 70.0)) and not pf.interval(70.01, (40.0, 70.0))
    assert not pf.interval(None, (40.0, 70.0))


def test_only_a_joint_pressure_and_perfusion_worsening_rejects():
    assert pf.classify(-1.0, -0.01, 60.0, 0.5) == pf.WORSEN
    assert pf.classify(-1.0, 0.01, 60.0, 0.5) == "PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT"
    assert pf.classify(0.0, 0.01, 60.0, 0.5) == "PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT"
    assert pf.classify(1.0, 0.01, 60.0, 0.5) == "PRESSURE_AND_PERFUSION_IMPROVE"
    assert pf.classify(1.0, -0.01, 60.0, 0.5) == "PRESSURE_IMPROVING_WITH_PERFUSION_WORSENING"
    assert pf.classify(-1.0, 1e-12, 60.0, 0.5) == "NO_PERFUSION_CHANGE"     # noise is no change
    assert pf.classify(-1e-12, -0.01, 60.0, 0.5) == "PRESSURE_UNCHANGED_WITH_PERFUSION_WORSENING"


def test_hr_never_filters_and_no_dbp_or_delivery_threshold_is_added():
    assert set(pf.RULES) == {"SIMULATION", "G", "H", "A", "B", "F", "C", "D", "E", "I"}
    names = {n.id for n in ast.walk(ast.parse(inspect.getsource(pf.candidate_rules))) if isinstance(n, ast.Name)}
    assert not {name for name in names if "hr" in name.lower() or "reading" in name.lower()}
    assert set(pf.ENVELOPES["I"]) == {"text"} and set(pf.ENVELOPES["C"]) == {"scenario", "comparator", "text"}


# Comparators, domain, reconstruction ------------------------------------------------------------------------------------

def test_each_comparator_changes_only_its_intervention(source):
    src, support = source
    checks = pf.comparator_checks(src, support)
    assert checks["valid"]
    for case in pf.CASES:
        assert checks["cases"][case]["unit_minutes"] == [30, 60]


def test_the_comparators_hold_with_the_tone_response_on(source):
    src, _ = source
    entry, point = src["p3"][src["children"][0][0]], vt.LAMBDAS[612]
    changes = {"deficit_to_tone_gain": 1.0, "afterload_sensitivity": 0.3}
    with lr.P2FGuard(), lr.LegacyLock():
        runs = {sc: hf.full_run({"entry": entry, "point": point, "bag": None}, C57, sc, 1.0, "midpoint", changes)
                for sc in (pf.L3, pf.CF1, pf.CF2)}
    l3, cf1, cf2 = (runs[sc]["rows"] for sc in (pf.L3, pf.CF1, pf.CF2))
    assert cf2[:31] == l3[:31] and cf2[31] != l3[31]
    assert cf1[0] == l3[0] and len(l3) == len(cf1) == len(cf2) == pf.MINUTES + 1
    assert runs[pf.L3]["controlled_at"] == runs[pf.CF1]["controlled_at"] == runs[pf.CF2]["controlled_at"] == 60


def test_g_and_h_are_read_on_every_minute(source):
    src, _ = source
    q = src["children"][0][0]
    _, blood = vt._blood_task(("P4", src["p3"][q], C57, pf.L3, None))
    anchors = vt.tone_anchors(C57, "lower", 1.0)
    rebuilt = vt.rebuild(blood, anchors, 1.0, 0.3)
    domain = pf._domain(rebuilt["rows"], 1.0, rebuilt["s0"])
    assert domain["G"] and domain["H"] and domain["zero_minutes"] > 0 and domain["same_minute_lag"] >= 1
    broken = [dict(row) for row in rebuilt["rows"]]
    m = next(m for m, row in enumerate(broken[:-1]) if row["deficit"] == 0.0)
    broken[m + 1]["T_abs"] = 1.0 + 1e-9
    assert not pf._domain(broken, 1.0, rebuilt["s0"])["H"]
    broken[5]["T_abs"] = 2.1
    assert not pf._domain(broken, 1.0, rebuilt["s0"])["G"]


def test_the_counterfactual_reconstruction_equals_the_core(source):
    src, _ = source
    q = src["children"][0][0]
    point = vt.LAMBDAS[611]
    with lr.P2FGuard(), lr.LegacyLock():
        for name, omit, scenario in (("CF1", 1, pf.CF1), ("CF2", 2, pf.CF2)):
            _, blood = pf._cf_blood_task(((name, C72, q), src["p3"][q], C72, omit))
            mine = vt.rebuild(blood, vt.tone_anchors(C72, vt.level_of(611), 1.1), 1.0, 0.3)["rows"]
            core = hf.full_run({"entry": src["p3"][q], "point": point, "bag": None}, C72, scenario, 1.1, "midpoint",
                               {"deficit_to_tone_gain": 1.0, "afterload_sensitivity": 0.3})["rows"]
            assert [[r["output"], r["p"], r["deficit"]] for r in mine] == [
                [r["output"], r["pressure_rel"], r["deficit"]] for r in core]


# The filter's accounting ---------------------------------------------------------------------------------------------------

def _fake(passes: dict):
    unit = (0, 3, 1, (7,), (0,))
    g = "1"
    base = {"simulation": False, "G": True, "H": True, "A": True, "B": True, "F": True, "C": True, "D": True,
            "E": True}
    p1 = {**base, "A": passes.get("A", True), "B": True}
    results = {("P1", 0, C57, vt.level_of(3), 1.0): {g: p1}, ("P1", 0, C72, vt.level_of(1), 1.0): {g: dict(base)},
               ("P2", (0, 0), C57, vt.level_of(3), 1.0): {g: dict(base)},
               ("P2", (0, 0), C72, vt.level_of(1), 1.0): {g: dict(base)},
               ("P4", 7, C57, vt.level_of(3), 1.0): {g: dict(base)}, ("P4", 7, C72, vt.level_of(1), 1.0): {g: dict(base)}}
    fd = {(1.0, 0, 3, 1): {g: {"l1": True, "q_ok": [7] if passes.get("I", True) else [], "d_ok": [0]}}}
    return unit, results, fd


def test_the_first_failure_every_failure_and_the_overlaps_are_counted():
    unit, results, fd = _fake({"A": False, "I": False})
    item = pf.filter_point([unit], 1.0, 1.0, results, fd)
    assert item["entering"] == 1 and item["survivors"] == 0
    assert item["first_failure"]["A"] == 1 and item["any_failure"]["I"] == 1 and item["overlap"] == {"A+I": 1}
    assert item["rejection_classes"]["PRESSURE_ENVELOPE_REJECTION"] == 1 and item["cross_domain_incompatible"]
    unit, results, fd = _fake({})
    assert pf.filter_point([unit], 1.0, 1.0, results, fd)["survivors"] == 1


def test_demand_classes_are_diagnostic():
    assert pf.demand_class({"1": {"survivors": 3}, "1.1": {"survivors": 1}}) == "ROBUST_ACROSS_DEMAND"
    assert pf.demand_class({"1": {"survivors": 3}, "1.1": {"survivors": 0}}) == "DEMAND_1_0_ONLY"
    assert pf.demand_class({"1": {"survivors": 0}, "1.1": {"survivors": 2}}) == "DEMAND_1_1_ONLY"
    assert pf.demand_class({"1": {"survivors": 0}, "1.1": {"survivors": 0}}) == "DEMAND_INCOMPATIBLE"


def test_sensitivity_results_never_reach_the_primary_counts_or_the_verdict():
    """In run(), sensitivity comes from its own _evaluate pass and is read only into the sensitivity entries."""
    body = inspect.getsource(pf.run)
    tree = ast.parse(body.lstrip())
    uses = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "sensitive"]
    assert len(uses) == 2       # assigned once, read once (the sensitivity dict comprehension)
    primary_line = next(line for line in body.splitlines() if line.strip().startswith("primary = {"))
    assert "evaluated[" in primary_line and "sensitive" not in primary_line
    verdict_calls = [line for line in body.splitlines() if "verdict(" in line]
    assert verdict_calls and not any("sensitiv" in line for line in verdict_calls)


def test_an_empty_primary_region_stops():
    primary = {"0.25": {"1": {"survivors": 0}, "1.1": {"survivors": 0}}}
    item = pf.verdict(primary, {})
    assert item["verdict"] == pf.EMPTY and item["approved"] == []
    assert "no sensitivity, no HR" in inspect.getsource(pf.run)


# Closure of P2J-2 and the policy ------------------------------------------------------------------------------------------

def test_p2j2_tuple_files_stand_at_their_p2j2_hashes_only_while_only_their_tuples_changed():
    sources = {k: "live" for k in pf.TUPLE_AT_P2J2}
    assert pf.p2j2_sources(sources) == pf.TUPLE_AT_P2J2
    for relative, item in vt.TUPLE_CHANGES.items():
        text = vt._live(relative)
        assert vt.outside_digest(text.replace("from __future__ import annotations",
                                              "from __future__ import annotations\nX = 1"),
                                 item["changed"]) != item["outside_p2j1"]


def test_no_legacy_no_p2f_no_pressure_feedback_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"shadow", "legacy_adapter", "comparison", "family_engine", "contracts_shadow",
                           "contracts_legacy", "hemodynamic_probes"}
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(pf.run)
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    text = json.dumps(pf.design(), default=str).lower()
    for word in ("\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


# The evaluation, on the frozen package (freeze 3d558fd) ---------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2J3_pressure_tone_filter.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2J3_FILTRO_PRESION_TONO.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == pf.P2J2_DIGEST
    assert record["design"] == json.loads(json.dumps(pf.design(), sort_keys=True, default=str))
    assert record["reuse"]["units_digests"] == {"1": vt.UNITS[1.0], "1.1": vt.UNITS[1.1]}
    assert record["reuse"]["units_equal"] and record["reuse"]["p2j2_tables_reproduced"]
    assert record["comparators"]["valid"] and record["hr"]["validation"]["equal"]


def test_the_primary_filter_the_report_states(record):
    primary = record["primary"]
    assert {g: {f: v["survivors"] for f, v in by.items()} for g, by in primary.items()} == {
        "0.25": {"1": 216, "1.1": 1092}, "0.5": {"1": 181, "1.1": 1092}, "1": {"1": 134, "1.1": 1092}}
    for by in primary.values():
        for item in by.values():
            assert all(item["any_failure"][n] == 0 for n in ("SIMULATION", "G", "H", "A", "B", "F", "C", "D", "E"))
            assert item["entering"] == record["entering_per_point"][next(f for f in by if by[f] is item)]
    assert set(record["demand_class"].values()) == {"ROBUST_ACROSS_DEMAND"}
    for by_case in record["support"].values():
        for item in by_case.values():
            for name in "CDE":
                assert set(item[name]["classes"]) == {"PRESSURE_AND_PERFUSION_IMPROVE"}
            assert item["t_abs120_after_adequacy"]["high"] - 1.0 < 1e-9


def test_sensitivity_never_rescues_and_the_verdict_holds(record):
    assert record["sensitivity_demand_class"]["g2 a0.3"] == "DEMAND_INCOMPATIBLE"
    assert record["sensitivity"]["g1.5 a0.3"]["1.1"]["survivors"] == 0
    assert record["verdict"]["verdict"] == pf.READY and record["verdict"]["approved"] == []
    assert all(record["verdict"]["checks"].values())
    assert record["identifiability"]["tone gain"]["class"] == "NON_IDENTIFIABLE"
    assert all(not item["failures"] for item in record["hr"]["by_point"].values())


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import pressure_tone_filter_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    pressure_tone_filter_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"
