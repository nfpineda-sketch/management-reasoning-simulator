"""Phase 2 shadow core, P2I-2AJ: case-truth pruning of the arrival severity and the HR observable decision pack.

These tests pin the faculty decisions as frozen before evaluation: 72f's normalized-delivery arrival is rejected by case
truth (read from its arrival delivery level only, never HR or a survivor count); the retained pair (57m severe, 72f D0 20
/ delivery 0.85) keeps its P2I-2AI D / lactate rows only on exact reproduction; demand is uncertainty (robustness
diagnostic, no value approved, every currently compatible value read); the HR surface is P2I-2AI's, unchanged; the
trajectory machinery reproduces the core; envelopes are proposals, never applied; nothing is approved.
"""
import ast
import inspect
import json

import pytest

from clinical_core import arrival_severity as asv
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, gi_reference, lactate_slice
from clinical_core import hr_observables as ho
from clinical_core import hr_primary as hp
from clinical_core import hr_shock as hk
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_closure as lc
from clinical_core import lactate_rebuild as lr

ROOT = ho.ROOT
SOURCE = ROOT / "clinical_core" / "hr_observables.py"
#: The P2I-2AJ freeze: faculty decisions, the P2I-2AI record, the case-truth rule, the reuse, demand, HR,
#: identifiability, trajectory and envelope rules, the verdict, the policy and every clinical_core source but the
#: downstream reports, committed before any HR trajectory distribution was read.
FROZEN_DIGEST = "6f17319a522ccfd3b376671a0623ab071343a6d32e3af7c699e506d4ccd8e4ff"
C57, C72 = ho.C57, ho.C72


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/hr_observables.py", "clinical_core/arrival_severity.py"} <= set(sources)
    assert "clinical_core/hr_observables_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/hr_observables.py", "clinical_core/hr_observables_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert ho.p2i2ai_record()["freeze_digest"] == ho.P2I2AI_DIGEST
    assert ho.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(ho.FACULTY) == {"decided", "case_truth", "retained", "demand", "intrinsic", "hr", "scope"}
    assert "REJECTED_BY_CASE_TRUTH_COMPATIBILITY" in ho.FACULTY["case_truth"].replace("_\n", "_")
    assert "not rejected because of HR or of its survivor count" in ho.FACULTY["case_truth"]
    assert "not a universal GI default" in ho.FACULTY["retained"]
    assert "ROBUST_ACROSS_DEMAND stays diagnostic" in ho.FACULTY["demand"]
    assert "80 stays in the support" in ho.FACULTY["intrinsic"]


def test_the_retained_pairs_exact_semantics_and_provenance():
    semantics = ho.pair_semantics(ho.p2i2ai_record())
    assert all(semantics["checks"].values()), semantics["checks"]
    first, second = semantics[C57], semantics[C72]
    assert (first["pair"], first["D0"], first["delivery"], first["x0"]) == (["upper", "lower"], 60.0, 0.6, 0.4)
    assert first["delivery_reanchored"] == pytest.approx(0.24, abs=1e-15)
    assert (second["pair"], second["D0"], second["delivery"]) == (["midpoint", "midpoint"], 20.0, 0.85)
    assert second["delivery_reanchored"] == pytest.approx(0.34, abs=1e-15)
    assert second["x0"] == pytest.approx(0.15, abs=1e-15)
    reads = semantics["band_reads"]
    assert reads["arrival_oxygen_debt"]["cited_items"] == ["active_bleeding", "crt_s", "lactate_mmol_l"]
    assert reads["arrival_delivery_ratio"]["cited_items"] == ["crt_s", "hb_g_dl", "peripheral_perfusion"]
    assert all(r["literal_values"] and not r["reads_authored_value"] for r in reads.values())


def test_hr_never_enters_the_semantics_or_the_case_truth(monkeypatch):
    record = ho.p2i2ai_record()
    compatible = [tuple(map(tuple, c)) for c in record["lactate_compatible"]]
    semantics, truth = ho.pair_semantics(record), ho.case_truth(compatible)
    authored = gi_reference.authored
    monkeypatch.setattr(gi_reference, "authored", lambda case, item: authored(case, item) + (50 if item == "hr" else 0))
    assert gi_reference.authored(C72, "hr") == authored(C72, "hr") + 50
    assert ho.pair_semantics(record) == semantics and ho.case_truth(compatible) == truth
    names = {node.id if isinstance(node, ast.Name) else node.attr for node in ast.walk(ast.parse(inspect.getsource(
        ho.case_truth))) if isinstance(node, (ast.Name, ast.Attribute))}
    for word in ("hr", "survivor", "tolerance", "gain", "ceiling", "pressure", "legacy", "authored", "hp", "hk"):
        assert not [name for name in names if word == name.lower() or name.lower().startswith(word + "_")], word


def test_the_case_truth_rejects_only_72f_normalized_delivery():
    record = ho.p2i2ai_record()
    truth = ho.case_truth([tuple(map(tuple, c)) for c in record["lactate_compatible"]])
    assert [(t["pair_72f"], t["status"]) for t in truth] == [
        (["midpoint", "midpoint"], "RETAINED"), (["upper", "upper"], ho.CASE_TRUTH_REJECTION)]
    # The rule is on 72f's current delivery level, whatever its debt; 57m's pair plays no part.
    synthetic = ho.case_truth([(("upper", "lower"), ("lower", "upper")), (("upper", "lower"), ("lower", "lower")),
                               (("lower", "upper"), ("upper", "upper")), (("upper", "upper"), ("midpoint", "midpoint"))])
    assert [t["status"] for t in synthetic] == [ho.CASE_TRUTH_REJECTION, "RETAINED", ho.CASE_TRUTH_REJECTION,
                                                "RETAINED"]
    assert ho.RETAINED_KEY == "upper/lower|midpoint/midpoint"


def test_the_reuse_guards_hold_on_the_committed_inputs():
    record = ho.p2i2ai_record()
    item = record["recertification"][ho.RETAINED_KEY]
    assert item["digest"] == ho.P2I2AI_RETAINED_UNITS and item["survivors_by_demand"] == {"0.9": 0, "1": 216,
                                                                                          "1.1": 1092}
    assert ho.dependency_digest() == ho.DEPENDENCIES_AT_P2I2AI, "a source the reused rows depend on changed"
    assert ho.DEMANDS == (0.9, 1.0, 1.1) and lc.PRIMARY_DEMAND == 1.0


# The retained pair's rows: P2I-2AD's checks, each case at its own pair ------------------------------------------------

def _mini(i, support_points):
    record = la.record_p2i2ab()
    source, support = la.source_space(record), record["crystalloid_support"]
    kids = source["children"][i]
    mini = {"p1": [source["p1"][i]], "p3": [{**source["p3"][q], "p1": 0} for q in kids],
            "children": [list(range(len(kids)))]}
    return mini, [support[k] for k in support_points]


@pytest.fixture(scope="module")
def mini_physiology():
    pick = ho.p2i2ai_record()["recertification"][ho.RETAINED_KEY]["representatives"]["MID"]["pick"]
    with lr.P2FGuard(), lr.LegacyLock():
        arrivals = lr.arrival_table()
        mini, support = _mini(pick["p1"], (0, 11))
        tasks = lc.haemodynamic_tasks(mini, support)
        store = lc.haemodynamics(tasks)
    return mini, support, arrivals, tasks, store


def test_the_retained_rows_equal_p2i2ai_s_per_case_filter_on_a_subset(mini_physiology):
    mini, support, arrivals, tasks, store = mini_physiology
    with lr.P2FGuard(), lr.LegacyLock():
        for factor in (1.0, 1.1):
            mine = ho.retained_region(mini, support, arrivals, tasks, store, factor)
            per = asv.per_case_filter(mini, support, arrivals, tasks, store, factor)
            assert mine["units"] == asv.combine(per, mini, len(support), *ho.RETAINED), factor
            stages = {stage["scenario"]: stage for stage in mine["stages"]}
            assert stages[ho.L1]["entering"] == mine["candidates"] == len(mini["p3"]) * 2 * len(ho.BASES)
            assert stages[ho.L2]["survivors"] == mine["survivors"]
            assert sum(mine["first_failures"].values()) == mine["candidates"] - mine["survivors"]


def test_demand_support_is_diagnostic_and_approves_nothing():
    units = {0.9: [], 1.0: [(0, 1, 2, (3,), (4, 5))], 1.1: [(0, 1, 2, (3,), (5,))]}
    regions = {f: {"units": u, "survivors": asv._survivors(u), "candidates": 10, "dominant_failure": "L1: x",
                   "first_failures": {"L1: x": 10 - asv._survivors(u)}, "stages": []} for f, u in units.items()}
    out = ho.demand_support(regions)
    assert [out[k]["status"] for k in ("0.9", "1", "1.1")] == [ho.DEMAND_INCOMPATIBLE, ho.DEMAND_COMPATIBLE,
                                                               ho.DEMAND_COMPATIBLE]
    assert out["robust_across_demand"] == 0 and out["robust_is_filter"] is False
    assert not any(out[k]["approved"] for k in ("0.9", "1", "1.1"))


# The arrival HR surface -----------------------------------------------------------------------------------------------

def test_the_surface_at_demand_1_is_p2i2ai_s_and_demand_reaches_the_acute_signal():
    for case, pair in zip(ho.CASES, ho.RETAINED):
        for level in hp.INTRINSIC:
            assert ho.anchors_at(case, level, pair, 1.0) == hk.analysis_anchors(case, level, *pair)
    table = ho.arrival_table(1.0)
    surface = ho.surface(table)
    assert (surface["decompositions"], surface["joint_candidates"]) == (450, 675)
    assert [{k: s[k] for k in ("intrinsic", "acute", "debt", "ceiling", "predicted")}
            for s in surface["survivors"]] == ho._p2i2ai_joint(ho.p2i2ai_record())
    # The acute signal is the effective deficit over demand: 1 - 2.5 x re-anchored delivery / demand.
    high = ho.arrival_table(1.1)
    assert high[(C57, "upper", hp.ACUTE[0], hp.DEBT[0], 150.0)]["x0"] == pytest.approx(1 - 0.6 / 1.1, abs=1e-12)
    assert high[(C72, "upper", hp.ACUTE[0], hp.DEBT[0], 150.0)]["x0"] == pytest.approx(1 - 0.85 / 1.1, abs=1e-12)
    assert all(row["D0"] == table[key]["D0"] for key, row in high.items())


def test_the_identifiability_rule_never_calls_a_narrow_grid_identification(monkeypatch):
    def s(a, b, acute, debt, ceiling):
        return {"intrinsic": [a, b], "acute": acute, "debt": debt, "ceiling": ceiling}
    joint = [s("upper", "midpoint", hp.ACUTE[2], hp.DEBT[2], 150.0), s("upper", "midpoint", hp.ACUTE[2], hp.DEBT[2],
                                                                        175.0)]
    out = ho.identifiability(joint)
    assert out["intrinsic_57m"]["status"] == ho.POOR  # an edge of the explored support
    assert out["intrinsic_72f"]["status"] == ho.PARTIAL and out["acute"]["status"] == ho.PARTIAL
    assert out["acute"]["bracket_rejected_neighbours"] == [hp.ACUTE[1], hp.ACUTE[3]]
    assert out["debt"]["status"] == ho.NON and out["ceiling"]["status"] == ho.POOR
    assert ho.identifiability([])["acute"]["status"] == ho.NOT_EVALUABLE
    monkeypatch.setattr(ho, "OBSERVATIONS", tuple(f"o{n}" for n in range(5)))
    assert ho.identifiability(joint)["acute"]["status"] == ho.WELL


# The trajectories ----------------------------------------------------------------------------------------------------

def _one_survivor():
    record = ho.p2i2ai_record()
    pick = record["recertification"][ho.RETAINED_KEY]["representatives"]["MID"]["pick"]
    units = [(pick["p1"], pick["lambda_57m"], pick["lambda_72f"], (pick["p3"],), (pick["support"],))]
    joint = [{**s, "acute": s["acute"], "intrinsic": s["intrinsic"]} for s in ho._p2i2ai_joint(record)]
    return units, joint


@pytest.mark.parametrize("factor", [1.0, 1.1])
def test_the_trajectory_machinery_reproduces_the_core_on_one_survivor(factor):
    units, joint = _one_survivor()
    record = la.record_p2i2ab()
    source, support = la.source_space(record), record["crystalloid_support"]
    with lr.P2FGuard(), lr.LegacyLock():
        if factor != 1.0:
            # Off the reference demand the analytic arrival is rebuilt at that demand (the validation's minute-0 check).
            table = ho.arrival_table(factor)
            joint = [{**s, "predicted": [table[(C57, s["intrinsic"][0], s["acute"], s["debt"], s["ceiling"])]
                                         ["predicted"], table[(C72, s["intrinsic"][1], s["acute"], s["debt"],
                                                               s["ceiling"])]["predicted"]]} for s in joint]
        checked = ho.validate_trajectories(source, support, units, joint, factor)
        traj = ho.trajectories(source, support, units, joint, factor)
    assert checked["exact"] and all(checked["checks"].values())
    assert set(checked["checks"]) == ({"lactate_closure", "hr", "arrival", "hr_shock"} if factor == 1.0
                                      else {"lactate_closure", "hr", "arrival"})
    assert traj["lactate_survivors"] == 1 and traj["readings_per_case"] == len(joint)
    assert traj["full_runs"] == 2 * 3 and traj["naive_full_runs"] == 6
    names = {f"{block}.{name}" for block, names in ho.READINGS.items() for name in names}
    assert set(traj["distributions"][C57]) == names == set(traj["distributions"][C72])
    assert traj["fluid_vs_prbc_72f"]["pairs"] == len(joint)


def test_the_fluid_prbc_contrast_names_the_first_diverging_input():
    def rows(deficit, debt):
        return [{"deficit": x, "demand": 1.0, "D": d} for x, d in zip(deficit, debt)]
    runs = {ho.L2: {"rows": rows([0.2, 0.2, 0.1], [5.0, 5.0, 5.0])},
            ho.L3: {"rows": rows([0.2, 0.1, 0.1], [5.0, 5.0, 4.0])}}
    out = ho.fluid_vs_prbc(runs, {ho.L2: [110.0, 110.0, 108.0], ho.L3: [110.0, 109.5, 106.0]})
    assert (out["diverges_at"], out["diverges_by_1_bpm_at"], out["largest_at"]) == (1, 2, 2)
    assert (out["acute_signal_diverges_at"], out["debt_diverges_at"], out["first_input"]) == (1, 2, "acute")
    assert out["prbc_minus_fluid_at_largest"] == -2.0


def test_the_envelopes_are_proposals_written_before_counts_and_never_applied():
    assert set(ho.ENVELOPES) == set("ABCDEFG")
    for envelope in ho.ENVELOPES.values():
        assert envelope["basis"].split(" ")[0] in (ho.PHYSIOLOGICAL, ho.EXPLORATION, ho.DATA_DRIVEN)
        assert envelope["proposal"] and envelope["interpretation"]
    traj = {"distributions": {c: {} for c in ho.CASES}, "by_intrinsic": {c: {} for c in ho.CASES}}
    table = ho.envelope_table({"1": traj})
    assert not any(table[key]["approved"] for key in "ABCDEFG")
    assert "no pass count" in table["rule"] and "no envelope applied" in ho.TRAJECTORY_RULE


def test_the_verdict_stops_without_a_joint_arrival_candidate():
    semantics = {"checks": {"x": True}}
    surfaces = {1.0: {"joint": 0, "survivors": [], "decompositions": 450}}
    out = ho.verdict(semantics, True, {"equal": True}, {}, surfaces, {}, {})
    assert out["verdict"] == f"{ho.NOT_READY} — {ho.BLOCKED}" and not out["approved"]


def test_no_legacy_no_p2f_region_pressure_deferred_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("_legacy_run", "legacy_reference", "gi_candidates", "admissible_p2f", "region_runs", "p2f_rejection",
                 "gi_physiology"):
        assert not any(name in call for call in called), name
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(ho.run)
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    assert "**hp.PRIMARY_HR_CALIBRATION" in inspect.getsource(ho.validate_trajectories)
    assert "hp.primary_series" in inspect.getsource(ho.readings) and "hp.primary_profile" in inspect.getsource(
        ho.arrival_table)
    assert hp.TOLERANCE_BPM == 5.0 and hp.CEILINGS == (150.0, 175.0, 200.0) and len(hp.INTRINSIC) == 3
    text = json.dumps(ho.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text
