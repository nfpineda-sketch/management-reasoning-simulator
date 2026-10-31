"""Phase 2 shadow core, P2I-2AK: the faculty HR observable-envelope filter.

These tests pin the faculty rules as frozen before any survivor count: demand 1.0 and 1.1 filtered apart (0.9 out),
envelopes A-F with their exact bounds (no 220 - age), the PRBC units judged against matched counterfactuals that omit
only the target unit, the primary ceilings 150 / 175 (200 sensitivity only), the frozen order, the reuse guards, the
reconstruction against the full core and the pressure guard; nothing is approved and the legacy HR is never read.
"""
import ast
import hashlib
import inspect
import json

import pytest

from clinical_core import blood_anchors
from clinical_core import baroreflex as br
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import hr_envelope_filter as hf
from clinical_core import hr_observables as ho
from clinical_core import hr_primary as hp
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr

ROOT = hf.ROOT
SOURCE = ROOT / "clinical_core" / "hr_envelope_filter.py"
#: The P2I-2AK freeze: faculty decisions, the P2I-2AJ record, demand handling, envelopes A-F, the comparator, the
#: primary ceilings and the sensitivity status, the filter order, the candidate, reuse, identifiability and verdict
#: rules, the policy and every clinical_core source but the downstream reports, committed before any survivor count.
FROZEN_DIGEST = "31f092650ee73ff4134fc9e5cc79b3a171fb7bb54de553fc2a7de2081f309dc3"
#: P2I-2AK is closed (P2J-1): its module is pinned byte for byte and its P2I-2AJ input record by its bytes, since a later
#: clinical_core module changes the live digest's source list; later packages' own modules leave its dependency digest,
#: and P2J-1's pressure-only change of derived.py and P2J-2's tone statements in derived.py and integration.py are
#: checked, not ignored (vascular_tone.p2i2ak_sources).
P2I2AK_MODULE_SHA = "6bfe0ef46ed1f2b1a4555b7322ca7d3747c237f2cc185caf3dcd479e8a50d885"
P2I2AJ_RECORD_SHA = "209db24136e478dc3bd2c392db4459b0fa9c3506b361eff6ab91053ebed9f66e"
LATER_MODULES = ("clinical_core/pressure_tone.py", "clinical_core/vascular_tone.py",
                 "clinical_core/pressure_tone_filter.py",
                 "clinical_core/baroreflex.py", "clinical_core/rr_audit.py", "clinical_core/acid_base.py")
#: derived.py, integration.py and shadow.py as P2J-2 left them (P2J-1 pinned derived.py and shadow.py, P2J-2 added
#: integration.py): the AST proofs (pressure_tone for shadow.py, vascular_tone.p2i2ak_sources for derived.py and
#: integration.py) cover what P2J-1 and P2J-2 changed; the pin makes any later change fail the guard until proven again.
from test_clinical_core_vascular_tone import P2J2_SOURCES  # noqa: E402
C57, C72 = hf.C57, hf.C72


# The frozen rules ---------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/hr_envelope_filter.py", "clinical_core/hr_observables.py"} <= set(sources)
    assert "clinical_core/hr_envelope_filter_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/hr_envelope_filter.py", "clinical_core/hr_envelope_filter_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert hf.p2i2aj_record()["freeze_digest"] == hf.P2I2AJ_DIGEST
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == P2I2AK_MODULE_SHA, "the closed P2I-2AK module changed"
    assert hashlib.sha256(hf.P2I2AJ_RECORD.read_bytes()).hexdigest() == P2I2AJ_RECORD_SHA


def test_the_faculty_decisions_are_recorded():
    assert set(hf.FACULTY) == {"decided", "demand", "untreated", "prbc", "definitive", "ceiling", "scope"}
    assert "never pooled before filtering" in hf.FACULTY["demand"]
    assert "never an acceptance criterion" in hf.FACULTY["demand"]
    assert "not a universal or 220 - age limit" in hf.FACULTY["untreated"]
    assert "only the target unit omitted" in hf.FACULTY["prbc"] and "zero allowed" in hf.FACULTY["prbc"]
    assert "never rescuing a primary rejection" in hf.FACULTY["ceiling"]


def test_the_envelopes_have_the_faculty_bounds_and_no_age_rule():
    env = hf.ENVELOPES
    assert (env["A"]["case"], env["A"]["scenario"], env["A"]["minute"], env["A"]["low"], env["A"]["high"]) == (
        C57, hf.L1, 120, 124.0, 160.0)
    assert (env["B"]["case"], env["B"]["scenario"], env["B"]["minute"], env["B"]["low"], env["B"]["high"]) == (
        C72, hf.L1, 120, 112.0, 150.0)
    assert (env["F"]["low"], env["F"]["high"], env["F"]["minute"]) == (0.0, 15.0, 120)
    assert (env["E"]["minutes"], env["E"]["onset_by"]) == ((60, 90, 120), 60)
    assert (env["C"]["counterfactual"], env["C"]["unit"], env["D"]["counterfactual"], env["D"]["unit"]) == (
        hf.CF1, 1, hf.CF2, 2)
    # The rules carry the faculty's bounds, never an age formula (the faculty text only says it is not one).
    assert "220" not in json.dumps(hf.ENVELOPES, default=str) and "220" not in hf.ORDER_RULE + hf.COMPARATOR_RULE
    assert hf.ORDER == ("ARRIVAL", "PRIMARY_CEILING", "A", "B", "F", "E", "C", "D")
    assert hf.PRIMARY_CEILINGS == (150.0, 175.0) and hf.SENSITIVITY_CEILINGS == (200.0,)
    assert hf.DEMANDS == (1.0, 1.1) and hf.EXCLUDED_DEMAND == 0.9


def _reading(**overrides):
    base = {"complete": True, "l1_120": 130.0, "residual": 2.0, "onset": 60, "l3_60": 110.0, "l3_90": 105.0,
            "l3_120": 102.0, "with_unit_1": 120.0, "without_unit_1": 121.0, "with_unit_2": 110.0,
            "without_unit_2": 112.0}
    return {**base, **overrides}


def test_the_rules_are_the_frozen_inequalities_in_the_frozen_order():
    assert hf.failures(_reading(), _reading(l1_120=120.0)) == []
    assert hf.failures(_reading(l1_120=123.9), _reading(l1_120=150.1)) == ["A", "B"]
    assert hf.failures(_reading(l1_120=124.0), _reading(l1_120=112.0)) == []  # inclusive bounds
    assert hf.failures(_reading(l1_120=160.0), _reading(l1_120=150.0)) == []
    assert hf.failures(_reading(l1_120=160.01), _reading(l1_120=111.99)) == ["A", "B"]
    assert hf.failures(_reading(residual=15.01), _reading(residual=-0.01)) == [f"F {C57}", f"F {C72}"]
    assert hf.failures(_reading(residual=15.0), _reading(residual=0.0)) == []
    # E: no tolerance; equal values pass, any rise fails; adequacy must be sustained from minute 60 at the latest.
    assert hf.failures(_reading(l3_90=110.0, l3_120=110.0), _reading()) == []
    assert hf.failures(_reading(l3_90=110.0001), _reading(onset=61)) == [f"E {C57}", f"E {C72}"]
    assert hf.failures(_reading(onset=None), _reading()) == [f"E {C57}"]
    # C and D: direction only against the counterfactual; a zero benefit passes; no comparison between the units.
    assert hf.failures(_reading(with_unit_1=121.0), _reading(with_unit_2=112.0)) == []
    assert hf.failures(_reading(with_unit_1=121.001), _reading(with_unit_2=112.001)) == [f"C {C57}", f"D {C72}"]
    assert hf.failures(_reading(with_unit_1=100.0, without_unit_1=100.0, with_unit_2=99.0,
                                without_unit_2=110.0), _reading()) == []
    # Every failing rule is listed, in ORDER: A, B, F, E, C, D.
    labels = hf.failures(_reading(l1_120=200.0, residual=20.0, onset=None, with_unit_1=130.0, with_unit_2=120.0),
                         _reading(l1_120=100.0))
    assert labels == ["A", "B", f"F {C57}", f"E {C57}", f"C {C57}", f"D {C57}"]
    assert hf.failures({"complete": False}, _reading()) == [hf.SIMULATION_REJECTION]


# The PRBC counterfactual comparator ------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def one_unit():
    record = ho.p2i2ai_record()
    pick = record["recertification"][ho.RETAINED_KEY]["representatives"]["MID"]["pick"]
    source_record = la.record_p2i2ab()
    source, support = la.source_space(source_record), source_record["crystalloid_support"]
    return pick, source, support


def test_the_counterfactual_inputs_differ_from_l3_in_the_target_unit_only(one_unit):
    pick, source, _ = one_unit
    for case, index in ((C57, pick["lambda_57m"]), (C72, pick["lambda_72f"])):
        values = {**lr.blood_values(source["p3"][pick["p3"]], case, None), "reserve": hf.RESERVE}
        _, _, full = blood_anchors.setup(case, **values)
        l3 = lr.scenario_items(case, hf.L3, full)
        for omit in (1, 2):
            items = hf.counterfactual_items(case, full, omit)
            assert [type(i).__name__ for i in items] == [type(i).__name__ for i in l3]
            for mine, theirs in zip(items, l3):
                if type(mine).__name__ == "PackedRedCells":
                    same = {k: v for k, v in vars(mine).items() if k not in ("start_minute", "units", "duration_min")}
                    assert same == {k: v for k, v in vars(theirs).items()
                                    if k not in ("start_minute", "units", "duration_min")}
                    assert theirs.units / theirs.duration_min == mine.units / mine.duration_min  # same rate
                    expected = ((30.0, 1.0, 30.0) if omit == 1 else (0.0, 1.0, 30.0))
                    assert (mine.start_minute, mine.units, mine.duration_min) == expected
                else:
                    assert vars(mine) == vars(theirs)
        with pytest.raises(ValueError):
            hf.counterfactual_items(case, full, 3)


def test_the_comparator_runs_equal_l3_outside_the_omitted_unit(one_unit):
    pick, source, _ = one_unit
    with lr.P2FGuard(), lr.LegacyLock():
        for case, index in ((C57, pick["lambda_57m"]), (C72, pick["lambda_72f"])):
            inputs = {"entry": source["p3"][pick["p3"]], "bag": None, "point": hf.LAMBDAS[index]}
            runs = {sc: hf.full_run(inputs, case, sc, 1.0) for sc in (hf.L3, hf.CF1, hf.CF2)}
            l3, cf1, cf2 = (runs[sc]["rows"] for sc in (hf.L3, hf.CF1, hf.CF2))
            assert l3 == ho.full_run(inputs, case, hf.L3, 1.0)["rows"]
            assert len(l3) == len(cf1) == len(cf2) == hf.MINUTES + 1  # elapsed time
            assert runs[hf.L3]["controlled_at"] == runs[hf.CF1]["controlled_at"] == runs[hf.CF2]["controlled_at"] == 60
            units = {name: [round(r["prbc_units"], 9) for r in rows] for name, rows in (("l3", l3), ("cf1", cf1),
                                                                                       ("cf2", cf2))}
            assert [units["l3"][m] for m in (0, 30, 60, 120)] == [0.0, 1.0, 2.0, 2.0]
            assert [units["cf1"][m] for m in (0, 30, 60, 120)] == [0.0, 0.0, 1.0, 1.0]
            assert [units["cf2"][m] for m in (0, 30, 60, 120)] == [0.0, 1.0, 1.0, 1.0]
            # Without unit 2 the run is L3 minute for minute until unit 2 starts.
            assert cf2[:31] == l3[:31] and cf2[31] != l3[31]
            # Without unit 1 nothing else changes at minute 0 (same arrival, haemorrhage and PPI).
            assert cf1[0] == l3[0]


def test_the_readings_compare_with_the_counterfactual_at_each_units_completion(one_unit):
    pick, source, _ = one_unit
    candidate = {**ho._p2i2ai_joint(ho.p2i2ai_record())[0]}
    with lr.P2FGuard(), lr.LegacyLock():
        inputs = {"entry": source["p3"][pick["p3"]], "bag": None, "point": hf.LAMBDAS[pick["lambda_57m"]]}
        runs = {sc: hf.full_run(inputs, C57, sc, 1.0) for sc in (hf.L1, hf.L3, hf.CF1, hf.CF2)}
    rate = 100.0
    values = hf.readings(runs, rate, candidate)
    series = {sc: [p["hr"] for p in hp.primary_series(runs[sc], rate, candidate["acute"], candidate["debt"],
                                                      candidate["ceiling"])] for sc in runs}
    assert (values["unit_1_minute"], values["unit_2_minute"]) == (30, 60)
    assert values["benefit_1"] == series[hf.CF1][30] - series[hf.L3][30]
    assert values["benefit_2"] == series[hf.CF2][60] - series[hf.L3][60]
    assert values["l1_120"] == series[hf.L1][120] and values["residual"] == series[hf.L3][120] - rate
    assert values["max_hr"] == max(max(series[hf.L1]), max(series[hf.L3]))  # counterfactuals are comparators only
    assert values["structural"]


# Pools, reuse, reconstruction ---------------------------------------------------------------------------------------

def test_the_reuse_guards_and_the_arrival_pools_hold_on_the_committed_inputs():
    from clinical_core import pressure_tone as pt
    # P2K-2 changed derived.py and integration.py only by its off-by-default insertions (acid_base's AST proof): the
    # pin reads their P2K-1 hashes while that proof holds.
    from clinical_core import acid_base as _ab
    assert all(_ab.proofs().values())
    assert {
        k: (_ab.CORE_AT_P2K1[k] if k in _ab.CORE_FILES and _ab.proved(k)
            else hashlib.sha256((ROOT / k).read_bytes()).hexdigest()) for k in P2J2_SOURCES} == \
        P2J2_SOURCES
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in hf.TUPLE_ONLY + hf.OWN + LATER_MODULES}
    from clinical_core import vascular_tone as vt
    from clinical_core import acid_base as ab
    digest = hashlib.sha256(json.dumps(ab.p2i2ak_sources(sources), sort_keys=True).encode("utf-8")).hexdigest()
    assert digest == hf.DEPENDENCIES_AT_P2I2AJ, "an executable dependency changed since P2I-2AJ"
    record = hf.p2i2aj_record()
    assert record["reuse"]["units_digest"] == hf.UNITS[1.0]
    pools = {f: hf.arrival_pool(record, f) for f in hf.DEMANDS}
    assert [(len(p["primary"]), len(p["sensitivity"])) for p in (pools[1.0], pools[1.1])] == [(2, 0), (9, 4)]
    assert all(s["ceiling"] in hf.PRIMARY_CEILINGS for p in pools.values() for s in p["primary"])
    assert all(s["ceiling"] == 200.0 for p in pools.values() for s in p["sensitivity"])
    assert pools[1.0]["universe"] == 450 and pools[1.0]["arrival_rejected"] == 448


def test_the_reconstruction_reproduces_the_full_core_on_one_unit(one_unit):
    pick, source, support = one_unit
    units = [(pick["p1"], pick["lambda_57m"], pick["lambda_72f"], (pick["p3"],), (pick["support"],))]
    record = hf.p2i2aj_record()
    with lr.P2FGuard(), lr.LegacyLock():
        for factor in hf.DEMANDS:
            pool = hf.arrival_pool(record, factor)
            checked = hf.validate(source, support, units, pool["primary"][:2], factor)
            assert checked["exact"] and all(checked["checks"].values()), (factor, checked["checks"])
            assert {"comparator_prefix", "comparator_units", "comparator_haemostasis", "hr", "arrival",
                    "lactate_closure", "hr_observables", "lactate_unchanged_by_hr"} == set(checked["checks"])
    json.dumps(checked, sort_keys=True)


# Summaries, cross-demand, identifiability, verdict -------------------------------------------------------------------

def _row(n, failures, weight=1):
    r = _reading()
    r.update({"max_hr": 140.0, "reserve_utilization": 0.5, "intrinsic": 100.0, "structural": True, "arrival": 125.0,
              "benefit_1": 1.0, "benefit_2": 2.0})
    return {"candidate": n, "q": 0, "a": 1, "b": 2, "weight": weight, "ds": (0,) * weight, "failures": failures,
            "r57": r, "r72": r}


def test_summaries_count_first_failures_overlaps_and_survivors():
    candidates = [{"intrinsic": ["upper", "upper"], "acute": hp.ACUTE[2], "debt": hp.DEBT[2], "ceiling": 150.0,
                   "predicted": [125.0, 110.0]},
                  {"intrinsic": ["lower", "midpoint"], "acute": hp.ACUTE[3], "debt": hp.DEBT[1], "ceiling": 175.0,
                   "predicted": [122.0, 109.0]}]
    filtered = {"rows": [_row(0, [], 2), _row(0, ["A", f"F {C57}"], 3), _row(1, [f"E {C72}", f"C {C57}"], 4)]}
    out = hf.summarize(filtered, candidates)
    assert (out["entering"], out["surviving"], out["surviving_candidates"]) == (9, 2, 1)
    assert out["first_failure"] == {"A": 3, f"E {C72}": 4}
    assert out["any_failure"] == {"A": 3, f"F {C57}": 3, f"E {C72}": 4, f"C {C57}": 4}
    assert out["failure_patterns"] == {"A+F": 3, "E+C": 4}
    assert [c["status"] for c in out["candidates"]] == [hf.SURVIVES, hf.REJECTED]
    assert not out["candidates"][0]["row_robust"]
    cross = hf.cross_demand({1.0: out, 1.1: {"candidates": [{**out["candidates"][0]},
                                                            {**out["candidates"][1], "status": hf.SURVIVES}]}})
    assert cross["counts"][hf.ROBUST] == 1 and cross["counts"][hf.ONLY_1_1] == 1 and not cross["is_filter"]
    assert sum(cross["counts"].values()) == cross["universe"] == 450


def test_the_identifiability_uses_the_primary_ceiling_grid():
    out = hf.identifiability([("upper", "midpoint", hp.ACUTE[2], hp.DEBT[2], 150.0)])
    assert out["ceiling"]["of"] == [150.0, 175.0] and out["ceiling"]["status"] == ho.POOR  # an edge either way
    assert out["intrinsic_72f"]["status"] == ho.PARTIAL and out["debt"]["status"] == ho.NON
    assert out["intrinsic_57m"]["status"] == ho.POOR
    assert out["ceiling"]["support"] == {"150.0": 1, "175.0": 0} and out["intrinsic_72f"]["support"]["midpoint"] == 1
    assert "never called identification" in hf.IDENTIFIABILITY_RULE


def test_the_verdict_stops_on_an_empty_filter_and_never_requires_robustness():
    empty = {1.0: {"filtered": {"rows": [_row(0, ["A"])]}, "summary": {"candidates": []}}}
    out = hf.verdict(empty, {"1": {"checks": {"lactate_closure": True, "lactate_unchanged_by_hr": True},
                                    "exact": True}}, True)
    assert out["verdict"] == f"{hf.NOT_READY} — {hf.EMPTY}" and not out["cross_demand_required"]
    alive = {1.0: {"filtered": {"rows": [_row(0, [])]}, "summary": {"candidates": []}}}
    out = hf.verdict(alive, {"1": {"checks": {"lactate_closure": True, "lactate_unchanged_by_hr": True},
                                    "exact": True}}, True)
    assert out["verdict"] == hf.READY and not out["approved"]


def test_no_legacy_no_p2f_pressure_deferred_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("_legacy_run", "legacy_reference", "gi_candidates", "admissible_p2f", "region_runs", "p2f_rejection",
                 "gi_physiology"):
        assert not any(name in call for call in called), name
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(hf.run)
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    assert "**hp.PRIMARY_HR_CALIBRATION" in inspect.getsource(hf.validate)
    assert "hp.primary_series" in inspect.getsource(hf.readings) and hp.TOLERANCE_BPM == 5.0
    text = json.dumps(hf.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


# The evaluation, on the frozen package (freeze 9de09fa) ---------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2I2AK_hr_envelope_filter.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AK_FILTRO_ENVOLVENTES_FC.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST
    p2i2aj = hf.p2i2aj_record()
    for key, factor in (("1", 1.0), ("1.1", 1.1)):
        pool = hf.arrival_pool(p2i2aj, factor)
        demand = record["demands"][key]
        assert demand["entering_latent_combinations"] == len(pool["primary"])
        assert [c["latent"] for c in demand["summary"]["candidates"]] == [list(hf.latent(s)) for s in pool["primary"]]
        assert record["counts"][hf.ARRIVAL_HR_REJECTION][key] == pool["arrival_rejected"]
    assert record["reuse"]["units_digests"] == {"1": hf.UNITS[1.0], "1.1": hf.UNITS[1.1]}
    assert record["reuse"]["dependency"]["equal"]


def test_the_filter_counts_the_report_states(record):
    d1, d11 = record["demands"]["1"], record["demands"]["1.1"]
    assert (d1["summary"]["entering"], d1["summary"]["surviving"], d1["summary"]["surviving_candidates"]) == (432, 432, 2)
    assert (d11["summary"]["entering"], d11["summary"]["surviving"], d11["summary"]["surviving_candidates"]) == (
        9828, 9828, 9)
    for demand in (d1, d11):
        assert not demand["summary"]["first_failure"] and not demand["summary"]["any_failure"]
        assert all(c["row_robust"] for c in demand["summary"]["candidates"])
        assert demand["margins"]["D_benefit gi_bleed_72f"]["high"] == 0.0  # the second unit cannot move 72f's HR
        assert demand["margins"]["A_l1_120"]["high"] <= 160.0 and demand["margins"]["B_l1_120"]["high"] <= 150.0
    assert record["counts"][hf.OUT_OF_PRIMARY] == {"1": 0, "1.1": 4}
    sens = d11["sensitivity_200"]
    assert sens["status"] == hf.SENSITIVITY and not sens["rescues"] and len(sens["summary"]["candidates"]) == 4
    assert record["cross_demand"]["counts"] == {hf.ROBUST: 1, hf.ONLY_1_0: 1, hf.ONLY_1_1: 8, hf.INCOMPATIBLE: 440}
    assert not record["cross_demand"]["is_filter"]


def test_the_identifiability_contrast_validation_and_verdict_the_report_states(record):
    union = record["identifiability"]["union"]
    assert {name: union[name]["status"] for name in ho.LATENTS} == {
        "intrinsic_57m": ho.POOR, "intrinsic_72f": ho.POOR, "acute": ho.POOR, "debt": ho.NON, "ceiling": ho.POOR}
    for demand in record["demands"].values():
        contrast = demand["fluid_vs_prbc_72f"]
        assert contrast["never_diverge"] == 0 and contrast["first_input"]["acute"] == contrast["pairs"] > 0
    assert all(v["exact"] and all(v["checks"].values()) for v in record["validation"].values())
    verdict = record["verdict"]
    assert verdict["verdict"] == hf.READY and all(verdict["checks"].values())
    assert not verdict["cross_demand_required"] and not verdict["approved"]
    text = json.dumps(record, default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import hr_envelope_filter_report
    assert "clinical_core/hr_envelope_filter_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    hr_envelope_filter_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"


# Review fixes (adversarial review of P2I-2AK) ------------------------------------------------------------------------

def test_the_runs_equal_hr_shock_at_demand_1_and_hr_reaches_no_haemodynamics(one_unit):
    from clinical_core import hr_shock as hk
    pick, source, _ = one_unit
    candidate = ho._p2i2ai_joint(ho.p2i2ai_record())[0]
    changes = {"acute_deficit_to_sympathetic_gain": candidate["acute"], "debt_to_sympathetic_gain": candidate["debt"],
               "sinus_rate_ceiling_bpm": candidate["ceiling"], **hp.PRIMARY_HR_CALIBRATION}
    with lr.P2FGuard(), lr.LegacyLock():
        for case, index in ((C57, pick["lambda_57m"]), (C72, pick["lambda_72f"])):
            inputs = {"entry": source["p3"][pick["p3"]], "bag": None, "point": hf.LAMBDAS[index]}
            for scenario in (hf.L1, hf.L3):
                assert hf.full_run(inputs, case, scenario, 1.0)["rows"] == hk.full_run(inputs, case, scenario)["rows"]
            for scenario in (hf.L1, hf.L3, hf.CF1, hf.CF2):
                base = hf.full_run(inputs, case, scenario, 1.0)["rows"]
                profiled = hf.full_run(inputs, case, scenario, 1.0, "upper", changes)["rows"]
                for name in ("output", "delivery", "deficit", "demand", "D", "lactate", "rr", "bleed_ml_per_min",
                             "prbc_units"):
                    assert [r[name] for r in base] == [r[name] for r in profiled], (case, scenario, name)


@pytest.mark.parametrize("factor", [1.0, 1.1])
def test_the_72f_second_unit_cannot_move_its_hr(one_unit, factor):
    pick, source, _ = one_unit
    inputs = {"entry": source["p3"][pick["p3"]], "bag": None, "point": hf.LAMBDAS[pick["lambda_72f"]]}
    with lr.P2FGuard(), lr.LegacyLock():
        runs = {sc: hf.full_run(inputs, C72, sc, factor) for sc in (hf.L1, hf.L3, hf.CF1, hf.CF2)}
    l3, cf2 = runs[hf.L3]["rows"], runs[hf.CF2]["rows"]
    # 72f's effective deficit is zero through the second unit, with and without it; D, SpO2 and glucose are equal.
    assert all(l3[m]["deficit"] == 0.0 == cf2[m]["deficit"] for m in range(31, 61))
    assert all(l3[m][name] == cf2[m][name] for m in range(61) for name in ("D", "spo2", "glucose"))
    assert l3[60]["delivery"] != cf2[60]["delivery"]  # the unit does change delivery
    candidate = ho._p2i2ai_joint(ho.p2i2ai_record())[0]
    assert hf.readings(runs, 100.0, candidate)["benefit_2"] == 0.0


def test_ceiling_200_stays_out_of_every_primary_result(record):
    for demand in record["demands"].values():
        assert all(c["latent"][4] in hf.PRIMARY_CEILINGS for c in demand["summary"]["candidates"])
        sens = demand["sensitivity_200"]
        if sens:
            assert all(c["latent"][4] == 200.0 for c in sens["summary"]["candidates"])
    assert all(item[4] in hf.PRIMARY_CEILINGS for items in record["cross_demand"]["surviving"].values()
               for item in items)
    assert all(record["identifiability"][k]["ceiling"]["of"] == [150.0, 175.0] for k in record["identifiability"])
    rows = [{"candidate": n, "failures": []} for n in range(5)]
    assert [r["candidate"] for r in hf.subset({"rows": rows}, 2, 3)["rows"]] == [0, 1, 2]
    assert [r["candidate"] for r in hf.subset({"rows": rows}, 0, 2)["rows"]] == [0, 1]


def test_the_demand_1_filter_is_reproduced_live(record):
    """The demand-1.0 half recomputed end to end (about 3 minutes): units, every row's verdict, the summary, margins."""
    with lr.P2FGuard(), lr.LegacyLock():
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = hf.lc.haemodynamic_tasks(source, support)
        store = hf.lc.haemodynamics(tasks)
        region = ho.retained_region(source, support, arrivals, tasks, store, 1.0)
        assert region["digest"] == hf.UNITS[1.0]
        pool = hf.arrival_pool(hf.p2i2aj_record(), 1.0)
        filtered = hf.filter_demand(source, support, region["units"], pool["primary"], 1.0)
    demand = record["demands"]["1"]
    assert json.loads(json.dumps(hf.summarize(filtered, pool["primary"]))) == demand["summary"]
    assert json.loads(json.dumps(hf.margins(filtered))) == demand["margins"]
    assert filtered["physiology_units"] == demand["physiology_units"]
