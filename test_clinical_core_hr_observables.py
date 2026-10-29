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
FROZEN_DIGEST = "2437e1b1c3075e180ef0fec912867974af43242a828c356190193820933fec4d"
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
    assert set(traj["fluid_vs_prbc_72f"]["first_input"]) == {"acute", "debt", "none"}
    json.dumps({"checked": checked, "trajectories": traj}, sort_keys=True)  # the record is written with sorted keys


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


# The evaluation, on the frozen package (freeze ac6608d, serialization fix 559fa11) -----------------------------------

RECORD = ROOT / "docs" / "revision" / "P2I2AJ_hr_observables.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AJ_PODA_SEVERIDAD_Y_OBSERVABLES_FC.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST
    p2i2ai = ho.p2i2ai_record()
    assert record["pair_semantics"] == _json(ho.pair_semantics(p2i2ai))
    assert record["case_truth"] == _json(ho.case_truth([tuple(map(tuple, c)) for c in p2i2ai["lactate_compatible"]]))
    for key, surface in record["hr_surfaces"].items():
        live = ho.surface(ho.arrival_table(float(key)))
        assert surface == _json(live), key
        assert record["identifiability"][key] == _json(ho.identifiability(live["survivors"]))
        assert record["observables"][key] == _json(ho.observable_table(live["survivors"]))


def test_the_case_truth_reuse_and_demand_the_report_states(record):
    assert [t["status"] for t in record["case_truth"]] == ["RETAINED", ho.CASE_TRUTH_REJECTION]
    reuse = record["reuse"]
    assert reuse["equal"] and reuse["dependency"]["equal"] and reuse["units_digest"] == ho.P2I2AI_RETAINED_UNITS
    assert reuse["survivors"] == {"0.9": 0, "1": 216, "1.1": 1092}
    demand = record["demand"]
    assert [demand[k]["status"] for k in ("0.9", "1", "1.1")] == [ho.DEMAND_INCOMPATIBLE, ho.DEMAND_COMPATIBLE,
                                                                  ho.DEMAND_COMPATIBLE]
    assert demand["robust_across_demand"] == 0 and not any(demand[k]["approved"] for k in ("0.9", "1", "1.1"))
    l3 = {stage["scenario"]: stage for stage in demand["0.9"]["stages"]}[ho.L3]
    assert (l3["entering"], l3["survivors"]) == (202140, 0)
    assert l3["first_failure"] == {"FD-LAC-04 gi_bleed_57m": 95580, "FD-LAC-05 gi_bleed_57m": 46944,
                                   "L3_RESUSCITATION_INADEQUATE gi_bleed_57m": 53136,
                                   "L3_RESUSCITATION_LOST gi_bleed_57m": 6480}
    assert record["efficiency"]["case_truth_rejected_lactate_survivors"] == 25613


def test_the_arrival_surfaces_and_identifiability_the_report_states(record):
    surfaces = record["hr_surfaces"]
    assert sorted(surfaces) == ["1", "1.1"]  # 0.9 is CURRENTLY_INCOMPATIBLE: no HR read there
    assert [(s["compatible_57m"], s["compatible_72f"], s["joint"]) for s in (surfaces["1"], surfaces["1.1"])] == [
        (33, 9, 2), (45, 78, 13)]
    assert surfaces["1.1"]["support"]["intrinsic_pairs"]["lower|midpoint"] == 7  # intrinsic 80 survives at 1.1
    union = record["identifiability"]["union"]
    assert {name: union[name]["status"] for name in ho.LATENTS} == {
        "intrinsic_57m": ho.POOR, "intrinsic_72f": ho.POOR, "acute": ho.POOR, "debt": ho.NON, "ceiling": ho.POOR}
    assert record["identifiability"]["1"]["acute"]["status"] == ho.PARTIAL


def test_the_trajectories_contrast_envelopes_and_verdict_the_report_states(record):
    assert all(v["exact"] for v in record["validation"].values())
    assert sum(v["full_runs"] for v in record["validation"].values()) == 360
    by_demand = record["trajectories"]["by_demand"]
    assert {k: (t["lactate_survivors"], t["joint_survivors"]) for k, t in by_demand.items()} == {
        "1": (216, 2), "1.1": (1092, 13)}
    for t in by_demand.values():
        contrast = t["fluid_vs_prbc_72f"]
        assert contrast["never_diverge"] == 0 and contrast["first_input"]["acute"] == contrast["pairs"]
        assert contrast["prbc_minus_fluid_at_largest"]["high"] < 0
        assert t["distributions"][C57]["H3.delta_unit_1"]["high"] < 0 and t["distributions"][C72][
            "H3.delta_unit_1"]["high"] < 0
    assert not any(record["envelopes"][key]["approved"] for key in "ABCDEFG")
    verdict = record["verdict"]
    assert verdict["verdict"] == ho.READY and all(verdict["checks"].values()) and not verdict["approved"]
    stripped = json.loads(json.dumps(record))
    for pick in stripped["reuse"]["reused_from_record"]["representatives"].values():
        del pick["rank"]  # the representatives' positions under P2I-2AD's LOW / MID / HIGH rule
    text = json.dumps(stripped, default=str).lower()
    found = [word for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank")
             if word in text]
    assert not found


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import hr_observables_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    hr_observables_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"


# The retained rows at every demand, recertified live on the full source (adversarial review, MEDIA-2) -----------------

#: The retained pair's units digest at demand 1.1: P2I-2AI kept only its count (1092), so these rows are recertified
#: here with P2I-2AI's own per-case filter, statistics and representative review at that demand.
UNITS_AT_1_1 = "515a157e21181013c631d4ff879dcb18986b9be89d40ad44654105781f1e2db0"
BAD_FLAGS = ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL", "INSTANT_NORMALIZATION", "INCOMPATIBLE_WITH_SURVIVAL")


@pytest.fixture(scope="module")
def full_physiology():
    with lr.P2FGuard(), lr.LegacyLock():
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks)
    return source, support, arrivals, tasks, store


def test_the_retained_rows_are_recertified_at_every_demand_on_the_full_source(record, full_physiology):
    source, support, arrivals, tasks, store = full_physiology
    with lr.P2FGuard(), lr.LegacyLock():
        for factor, key in ((0.9, "0.9"), (1.0, "1"), (1.1, "1.1")):
            region = ho.retained_region(source, support, arrivals, tasks, store, factor)
            assert region["survivors"] == record["reuse"]["survivors"][key]
            assert _json(region["stages"]) == record["demand"][key]["stages"], key
            if not region["survivors"]:
                continue
            per = asv.per_case_filter(source, support, arrivals, tasks, store, factor)
            units = asv.combine(per, source, len(support), *ho.RETAINED)
            assert units == region["units"], key
            assert set(asv.statistics(per, units).values()) == {region["survivors"]}, key
            for pick in asv.representatives(per, source, units).values():
                entry = source["p3"][pick["p3"]]
                for case, index in ((C57, pick["lambda_57m"]), (C72, pick["lambda_72f"])):
                    point = ho.LAMBDAS[index]
                    for scenario in (ho.L1, ho.L3):
                        full = lc.full_run(entry, case, scenario, point, factor=factor)
                        unit = entry["p1"] if scenario == ho.L1 else pick["p3"]
                        lactate, debt, _ = lc.factorized(store[tasks[(scenario, unit, case)]], arrivals[case], point,
                                                         factor)
                        series = {"lactate": full["lactate"], "deficit": full["deficit"], "D": full["D"],
                                  "stop": full["stop"], "output": full["output"],
                                  "hb": [state.hb for state, _ in full["views"]]}
                        flags, checks = lr._flags(series, scenario), lc.debt_checks(full)
                        assert not any(flags[name] for name in BAD_FLAGS), (key, case, scenario)
                        assert not checks["falls_outside_adequate_minutes"]
                        assert checks["critical_minutes_below_arrival"] == 0
                        assert lactate == full["lactate"] and debt == full["D"]
            if factor == 1.0:
                assert region["digest"] == ho.P2I2AI_RETAINED_UNITS
            if factor == 1.1:
                assert region["digest"] == UNITS_AT_1_1
