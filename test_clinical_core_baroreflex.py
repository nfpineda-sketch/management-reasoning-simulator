"""Phase 2 shadow core, P2J-4: the direct baroreflex reconnected and the whole-patient HR recertified.

These tests pin the baroreflex in the core (off by default, never negative, 0 at or above MAP_set, reading only the MAP
the state resolves, never together with the relative-pressure term), its causal timing (acyclic, same step), the
structural probes A-D, the exact HR reconstruction and the non-regression of every non-HR channel, the reuse of
P2I-2AK's rules and latent region unchanged, the predeclared candidates, what P2J-4 changed outside its module (and the
closed packages' guards that rest on it), the frozen classifiers and verdict, and the policy: nothing approved.
"""
import ast
import hashlib
import inspect
import json
import math
from dataclasses import fields, replace

import pytest

from clinical_core import baroreflex as br
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import hr_envelope_filter as hf
from clinical_core import hr_primary as hp
from clinical_core import integration
from clinical_core import lactate_adequacy as la
from clinical_core import vascular_tone as vt
from clinical_core.derived import (DEFAULT_PROFILE, PARAMETERS, CoreProfile, arrival_state, baroreflex_drive,
                                   baroreflex_signal, derive, mean_arterial_pressure, sympathetic_target)
from clinical_core.integration import step
from clinical_core.state import CoreInvariantError

ROOT = br.ROOT
SOURCE = ROOT / "clinical_core" / "baroreflex.py"
#: The P2J-4 freeze: the faculty decisions, the signal, timing and retired-term rules, the MAP_set and gain candidates,
#: the carried region, the order and classes, the arrival rule and P2I-2AK's A-F, the probes, the classifiers, the
#: verdict and recommendation rules, the AST proof and every clinical_core source but the downstream reports,
#: committed before any survivor count was read.
FROZEN_DIGEST = "81ab565efb3170ee9e7e4683c3198495004d30c7dfdadce09f551d66547dedf6"
C57, C72 = br.C57, br.C72


@pytest.fixture(scope="module")
def source():
    return la.source_space(la.record_p2i2ab())


# The frozen package ------------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/baroreflex.py" in sources and "clinical_core/derived.py" in sources
    assert "clinical_core/baroreflex_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/baroreflex.py", "clinical_core/baroreflex_report.py"} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert br.p2j3_record()["freeze_digest"] == br.P2J3_DIGEST
    assert br.freeze_digest() == FROZEN_DIGEST, "a source, a range, a rule or the order changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(br.FACULTY) == {"decided", "region", "signal", "contribution", "map_set", "gain", "timing",
                               "orthogonality", "double_counting", "old_term", "latent", "arrival", "hr_rules",
                               "pressure", "upstream", "scope"}
    assert "none FACULTY_APPROVED" in br.FACULTY["region"] and "never in the primary" in br.FACULTY["region"]
    assert "never negative" in br.FACULTY["signal"] and "not case-specific" in br.FACULTY["map_set"]
    assert "DIAGNOSTIC_NO_BAROREFLEX_REFERENCE" in br.FACULTY["gain"]
    assert "BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR" in br.FACULTY["arrival"]


def test_the_candidates_are_the_faculty_s_and_nothing_is_approved():
    assert br.MAP_SETS == (80.0, 90.0, 100.0) and br.MAP_SET_STATUS == "EXPLORATORY_COMMON_REFERENCE"
    assert br.PRIMARY_BARO == (0.25, 0.5, 1.0, 1.5) and br.REFERENCE_BARO == 0.0
    assert br.BARO_STATUS == {0.0: "DIAGNOSTIC_NO_BAROREFLEX_REFERENCE", 0.25: "PRIMARY_EXPLORATORY_SUPPORT",
                              0.5: "PRIMARY_EXPLORATORY_SUPPORT", 1.0: "PRIMARY_EXPLORATORY_SUPPORT",
                              1.5: "PRIMARY_EXPLORATORY_SUPPORT"}
    assert br.POINTS[0] == br.REFERENCE_POINT and len(br.PRIMARY_POINTS) == 12
    assert set(br.PRIMARY_POINTS) == {(m, k) for m in br.MAP_SETS for k in br.PRIMARY_BARO}
    assert br.TONE_GAINS == (0.25, 0.5, 1.0) and br.AFTERLOAD == 0.3 and br.DEMANDS == (1.0, 1.1)
    assert not set(br.EXCLUDED_TONE) & set(br.TONE_GAINS)
    assert br.CARRIED["approved"] == [] and "APPROVED" not in {*br.BARO_STATUS.values(), br.MAP_SET_STATUS}


# The baroreflex in the core ------------------------------------------------------------------------------------------------

def test_the_baroreflex_is_off_by_default_and_then_changes_nothing():
    assert DEFAULT_PROFILE.baroreflex_to_sympathetic_gain == 0.0 and DEFAULT_PROFILE.baroreflex_map_set_mmhg is None
    for name in br.BARO_NAMES:
        assert PARAMETERS[name][0] == dv.PROVISIONAL and name in {f.name for f in fields(CoreProfile)}
    anchors = vt.NEUTRAL
    declared = replace(DEFAULT_PROFILE, baroreflex_map_set_mmhg=90.0)
    state = arrival_state(anchors, DEFAULT_PROFILE).evolve(P=0.4)
    assert baroreflex_drive(0.4, anchors, declared) == 0.0
    assert step(state, (), anchors, DEFAULT_PROFILE) == step(state, (), anchors, declared)
    assert sympathetic_target(state, anchors, DEFAULT_PROFILE) == sympathetic_target(state, anchors, declared)


def test_the_signal_is_never_negative_zero_at_or_above_the_set_point_and_reaches_one():
    for map_set in br.MAP_SETS:
        assert baroreflex_signal(0.0, map_set) == 1.0
        assert baroreflex_signal(map_set, map_set) == 0.0
        previous = math.inf
        for mean in [i * 0.5 for i in range(0, 400)]:
            value = baroreflex_signal(mean, map_set)
            assert 0.0 <= value <= 1.0 and value <= previous
            assert (value > 0.0) == (mean < map_set)
            previous = value
    for bad in (0.0, -10.0):
        with pytest.raises(CoreInvariantError):
            baroreflex_signal(50.0, bad)


def test_the_profile_refuses_two_pressure_signals_a_missing_set_point_and_negative_values():
    with pytest.raises(CoreInvariantError, match="never active together"):
        replace(DEFAULT_PROFILE, baroreflex_to_sympathetic_gain=0.5, baroreflex_map_set_mmhg=90.0)
    with pytest.raises(CoreInvariantError, match="declared MAP set point"):
        replace(DEFAULT_PROFILE, sympathetic_per_pressure_deficit=0.0, baroreflex_to_sympathetic_gain=0.5)
    for value in (0.0, -1.0):
        with pytest.raises(CoreInvariantError):
            replace(DEFAULT_PROFILE, baroreflex_map_set_mmhg=value)
    with pytest.raises(CoreInvariantError):
        replace(DEFAULT_PROFILE, sympathetic_per_pressure_deficit=0.0, baroreflex_to_sympathetic_gain=-0.1,
                baroreflex_map_set_mmhg=90.0)
    ok = replace(DEFAULT_PROFILE, sympathetic_per_pressure_deficit=0.0, baroreflex_to_sympathetic_gain=1.5,
                 baroreflex_map_set_mmhg=100.0)
    assert ok.baroreflex_to_sympathetic_gain == 1.5


def test_the_baroreflex_reads_only_the_resolved_map():
    reads = {n.attr for n in ast.walk(ast.parse(inspect.getsource(dv.baroreflex_drive)))
             if isinstance(n, ast.Attribute)}
    assert reads == {"baroreflex_to_sympathetic_gain", "baroreflex_map_set_mmhg"}
    names = {n.id for n in ast.walk(ast.parse(inspect.getsource(dv.baroreflex_drive))) if isinstance(n, ast.Name)}
    assert {"mean_arterial_pressure", "baroreflex_signal", "pressure_rel"} <= names
    assert not names & {"D", "deficit", "acute", "tone_target", "deficit_to_tone_gain", "hr", "legacy"}
    anchors = vt.NEUTRAL
    for p in (0.0, 0.3, 0.77, 1.0, 1.4):
        state = arrival_state(anchors, DEFAULT_PROFILE)
        assert mean_arterial_pressure(p, anchors, DEFAULT_PROFILE) == (anchors.sbp * p + 2 * (anchors.dbp * p)) / 3
    view = derive(arrival_state(anchors, DEFAULT_PROFILE).evolve(P=0.6), anchors, DEFAULT_PROFILE)
    assert mean_arterial_pressure(view.pressure_rel, anchors, DEFAULT_PROFILE) == view.map


def test_the_target_adds_the_baroreflex_after_the_other_terms():
    source = inspect.getsource(dv.sympathetic_target)
    assert source.index("hypoglycaemia)") < source.index("target += baroreflex_drive(pressure_rel, anchors, profile)") \
        < source.index("return max(0.0, target)")


# Timing --------------------------------------------------------------------------------------------------------------------

def test_the_timing_is_acyclic_in_the_same_step():
    assert br.TIMING == "ACYCLIC_SAME_STEP"
    body = inspect.getsource(integration.step)
    assert body.index("new_state = state.evolve(minute=minute") < body.index("sympathetic_after_minute(state, new_state")
    for function in (dv._perfusion, dv.relative_delivery, dv.effective_oxygen_deficit, dv.tone_target,
                     dv.acute_deficit_signal, dv.arterial_pressures, dv.collapse_burden_after_minute):
        text = inspect.getsource(function)
        assert "sympathetic" not in text and "pulse_rate" not in text and "baroreflex" not in text
    # Behaviour: the baroreflex moves the drive and the rate, nothing else, in the same minute.
    anchors = vt.NEUTRAL
    on = replace(DEFAULT_PROFILE, sympathetic_per_pressure_deficit=0.0, baroreflex_to_sympathetic_gain=1.0,
                 baroreflex_map_set_mmhg=100.0)
    off = replace(on, baroreflex_to_sympathetic_gain=0.0)
    state_on, state_off = arrival_state(anchors, on), arrival_state(anchors, off)
    assert state_on.aux.sympathetic_drive > state_off.aux.sympathetic_drive
    for _ in range(5):
        state_on, _ = step(state_on.evolve(P=state_on.P * 0.9), (), anchors, on)
        state_off, _ = step(state_off.evolve(P=state_off.P * 0.9), (), anchors, off)
        assert state_on.evolve(aux=replace(state_on.aux, sympathetic_drive=0.0)) == \
            state_off.evolve(aux=replace(state_off.aux, sympathetic_drive=0.0))
        view = derive(state_on, anchors, on)
        assert state_on.aux.sympathetic_drive >= sympathetic_target(state_on, anchors, on)
        assert baroreflex_drive(view.pressure_rel, anchors, on) == baroreflex_signal(view.map, 100.0)


# Structural probes ------------------------------------------------------------------------------------------------------------

def test_probes_a_to_d_prove_two_distinct_signals():
    probes = br.probes()
    assert all(probes[name]["passed"] for name in br.PROBES)
    a, b, c, d = (probes[n] for n in "ABCD")
    assert a["acute_drive"] == 0.0 and a["baroreflex_drive"] > 0.0
    assert b["baroreflex_drive"] == 0.0 and b["acute_drive"] > 0.0
    assert c["baroreflex_drive"] > 0.0 and c["acute_drive"] > 0.0
    assert d["baroreflex_drive"] == 0.0 and d["acute_drive"] == 0.0
    assert b["map"] >= max(br.MAP_SETS) and a["map"] < min(br.MAP_SETS)
    for name in br.PROBES:
        for m, item in probes[name]["by_map_set"].items():
            assert item["sum_equal"] and (item["baroreflex_drive"] > 0.0) == (item["map"] < float(m))
    assert probes["high_pressure"]["never_negative"]
    assert "T=" not in inspect.getsource(br.probe) and ".T" not in inspect.getsource(br.probe)


def test_a_failing_probe_is_noticed():
    item = dict(br.probe("A"))
    assert br.probe_verdict("A", item)
    assert not br.probe_verdict("A", {**item, "acute_drive": 0.1})
    assert not br.probe_verdict("D", {**br.probe("D"), "baroreflex_drive": 0.01})
    assert not br.probe_verdict("B", {**br.probe("B"), "sum_equal": False})


# Reconstruction, non-regression, reused rules --------------------------------------------------------------------------------

def test_the_rebuilt_hr_equals_the_core_and_every_non_hr_channel_is_unchanged(source):
    combos = br.latent_region()["combos"][1.1]
    for case, lam, position, check in ((C57, 0, 0, (2, (100.0, 1.5))), (C72, 611, 1, (5, (80.0, 0.25)))):
        task = (("t",), source["p3"][0], br.LAMBDAS[lam], case, 1.1, 1.0, combos, position, check)
        _, result = br._unit_task(task)
        v = result["validation"]
        assert v["hr_equal"] and v["rows_equal"] and v["states_equal"] and v["baroreflex_moved_drive"]
        assert v["min_drive"] >= 0.0
        assert len(result["readings"]) == len(combos) * len(br.POINTS)


def test_gain_zero_reads_exactly_what_p2i2ak_read(source):
    combos = br.latent_region()["combos"][1.0]
    base = {"deficit_to_tone_gain": 0.25, "afterload_sensitivity": 0.3, **hp.PRIMARY_HR_CALIBRATION}
    runs = {sc: hf.full_run({"entry": source["p3"][1], "point": br.LAMBDAS[612], "bag": None}, C57, sc, 1.0,
                            "midpoint", base) for sc in br.SCENARIOS}
    for combo in combos:
        rate = br.hs.intrinsic_levels(C57)[combo["intrinsic"][0]]
        mine, theirs = br.readings(runs, rate, combo, None, 0.0), hf.readings(runs, rate, combo)
        assert {k: mine[k] for k in theirs} == theirs


def test_the_rules_are_p2i2ak_s_unchanged():
    assert br.ENVELOPES is hf.ENVELOPES
    assert br.ARRIVAL == {case: {"authored": hp.AUTHORED[case], "low": hp.WINDOWS[case][0],
                                 "high": hp.WINDOWS[case][1]} for case in br.CASES}
    assert hp.TOLERANCE_BPM == 5.0 and hp.AUTHORED == {C57: 124.0, C72: 112.0}
    assert "hf.failures(r57, r72)" in inspect.getsource(br.rules)
    assert br.ORDER == ("SUPPORT", "DOMAIN", "SIMULATION", "ARRIVAL", "A", "B", "F", "E", "C", "D")
    assert set(br.REJECTION_CLASS.values()) == {"HR_PRIOR_REGION_REJECTION", "DOMAIN_REJECTION", "SIMULATION_REJECTION",
                                                "BAROREFLEX_REJECTION", "HR_ENVELOPE_REJECTION"}
    good = {"complete": True, "arrival": 124.0, "l1_120": 150.0, "residual": 5.0, "onset": 30, "l3_60": 110.0,
            "l3_90": 105.0, "l3_120": 104.0, "with_unit_1": 120.0, "without_unit_1": 125.0, "with_unit_2": 110.0,
            "without_unit_2": 112.0}
    assert br.rules(good, {**good, "arrival": 112.0, "l1_120": 130.0}) == []
    assert br.rules({**good, "arrival": 129.5}, {**good, "arrival": 112.0, "l1_120": 130.0}) == ["ARRIVAL"]
    assert br.rules({"complete": False}, good) == ["SIMULATION"]


def test_the_latent_region_is_p2i2ak_s_and_the_grid_is_not_reopened():
    latent = br.latent_region()
    assert latent["equal_to_arrival_pool"] and {f: len(v) for f, v in latent["combos"].items()} == {1.0: 2, 1.1: 9}
    assert latent["prior_region_rejection"] == {"1": 448, "1.1": 441} and latent["universe"] == 450
    for combos in latent["combos"].values():
        for combo in combos:
            assert combo["ceiling"] in hf.PRIMARY_CEILINGS


def test_the_relative_pressure_term_is_out_of_every_profile_used():
    assert br.OLD_TERM == "RETIRED_FROM_PRIMARY_HR"
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    for function in (br.hr_series, br._unit_task, br.domain_ok):
        assert "hp.PRIMARY_HR_CALIBRATION" in inspect.getsource(function)
    combo = br.latent_region()["combos"][1.0][0]
    assert all(br.domain_ok(combo, point, 0.5) for point in br.POINTS)
    assert not br.domain_ok(combo, (80.0, -0.1), 0.5) and not br.domain_ok(combo, (None, 0.5), 0.5)
    assert not br.domain_ok(combo, (80.0, 0.5), 1.5) and not br.domain_ok(combo, (80.0, 0.5), 2.0)


def test_one_task_per_unit_and_case_no_cartesian_runs():
    region = {"survivors": {(0.5, 1.0): [(0, 3, 4, 7, 0), (1, 3, 4, 7, 2), (0, 5, 4, 8, 0)]},
              "source": {"p3": {7: "e7", 8: "e8"}}}
    latent = {"combos": {1.0: [{"intrinsic": ["upper", "upper"]}] * 2}}
    tasks = br.unit_tasks(region, latent)
    assert len(tasks) == 2 * 2 and br.hr_units(region["survivors"][(0.5, 1.0)]) == [((7, 3, 4), 2), ((8, 5, 4), 1)]
    assert {t[-1][1] for t in tasks} <= set(br.PRIMARY_POINTS)


# What P2J-4 changed outside its module ------------------------------------------------------------------------------------------

def test_p2j4_changed_only_the_declared_statements_of_derived():
    item = br.P2J4_CHANGES[br.DERIVED]
    live = vt._live(br.DERIVED)
    assert hashlib.sha256(live.encode("utf-8")).hexdigest() != item["sha_at_p2j3"]
    assert vt.outside_digest(live, item["changed"]) == item["outside_p2j3"]
    assert vt.outside_digest(live, item["since_p2j1"]) == item["outside_p2j1"]
    assert vt.outside_digest(live, item["since_p2i2ak"]) == item["outside_p2i2ak"]
    assert vt.outside_digest(live.replace("OUTPUT_EPSILON = 1e-9", "OUTPUT_EPSILON = 1e-8"), item["changed"]) != \
        item["outside_p2j3"], "the proof must notice a change outside the baroreflex statements"
    for name, expected in br.INSIDE_AT_P2J3.items():
        assert br.inside_digest(live, name) == expected, name
    mutated = live.replace("debt_to_sympathetic_gain * state.D", "debt_to_sympathetic_gain * 2.0 * state.D")
    assert br.inside_digest(mutated, "sympathetic_target") != br.INSIDE_AT_P2J3["sympathetic_target"]
    mutated = live.replace("sinus_rate_ceiling_bpm: float = 175.0", "sinus_rate_ceiling_bpm: float = 180.0")
    assert br.inside_digest(mutated, "CoreProfile") != br.INSIDE_AT_P2J3["CoreProfile"]
    from test_clinical_core_vascular_tone import P2J2_SOURCES
    assert {k: hashlib.sha256((ROOT / k).read_bytes()).hexdigest() for k in P2J2_SOURCES} == P2J2_SOURCES
    for relative in ("clinical_core/integration.py", "clinical_core/shadow.py", "clinical_core/state.py"):
        assert relative not in br.P2J4_CHANGES


def test_the_closed_packages_see_derived_at_their_own_hash_only_while_proven():
    sources = {br.DERIVED: "live", **{k: "live" for k in br.TUPLE_AT_P2J3}, "clinical_core/state.py": "s"}
    item = br.P2J4_CHANGES[br.DERIVED]
    assert br.p2j3_sources(sources) == {br.DERIVED: item["sha_at_p2j3"], **br.TUPLE_AT_P2J3,
                                        "clinical_core/state.py": "s"}
    assert br.p2j1_sources({br.DERIVED: "live"})[br.DERIVED] == item["sha_at_p2j1"]
    assert br.p2i2ak_sources({br.DERIVED: "live"})[br.DERIVED] == item["sha_at_p2i2ak"]


# Frozen classifiers, verdict, recommendation ----------------------------------------------------------------------------

def _fake(signals):
    return {("u",): {"signals": {br.L1: signals, br.L3: []}, "readings": {}}}


def test_the_double_counting_classes_follow_the_frozen_rule():
    probes = br.probes()
    same = [(50.0, 0.2), (60.0, 0.1), (120.0, 0.0)]
    split = same + [(70.0, 0.0), (130.0, 0.3)]
    assert br.double_counting(_fake(same), probes, {})["class"] == "FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES"
    result = br.double_counting(_fake(split), probes, {})
    assert result["class"] == "STRUCTURALLY_DISTINCT_BUT_CORRELATED"
    assert result["by_map_set"]["80"]["baroreflex_only"] == pytest.approx(1 / 5)
    broken = {**probes, "A": {**probes["A"], "passed": False}}
    assert br.double_counting(_fake(split), broken, {})["class"] == "PATHOLOGICAL_DOUBLE_COUNTING"
    assert "threshold" in br.DOUBLE_COUNTING_RULE and "never thresholded" in br.DOUBLE_COUNTING_RULE


def test_the_identifiability_classifier():
    assert br._classify({"80": {1}, "90": set(), "100": set()}) == "WELL_CONSTRAINED"
    assert br._classify({"80": {1}, "90": {2}, "100": set()}) == "PARTIALLY_CONSTRAINED"
    assert br._classify({"80": {1}, "90": {1, 2}, "100": {1}}) == "POORLY_IDENTIFIED"
    assert br._classify({"80": {1}, "90": {1}, "100": {1}}) == "NON_IDENTIFIABLE"
    assert br._classify({"80": set(), "90": set()}) == "NOT_EVALUABLE"


def test_the_verdict_and_the_recommendation_follow_their_rules():
    checks = {"a": True, "b": True}
    assert br.verdict(checks, True, True)["verdict"] == br.READY
    assert br.verdict({**checks, "b": False}, True, True)["verdict"] == f"{br.NOT_READY} — b"
    assert br.verdict(checks, False, False)["verdict"] == f"{br.NOT_READY} — {br.ARRIVAL_STOP}"
    assert br.verdict(checks, True, False)["verdict"] == f"{br.NOT_READY} — NO_PRIMARY_SURVIVOR"
    assert br.verdict(checks, True, True)["approved"] == []
    tables = {"incompatible_tone_branches": [], "by": {"demand": {"1": {"survivors": 3}, "1.1": {"survivors": 1}}}}
    ident = {"map_set": {"class": "POORLY_IDENTIFIED"}, "gain": {"class": "NON_IDENTIFIABLE"}}
    dc = {"class": "STRUCTURALLY_DISTINCT_BUT_CORRELATED"}
    assert br.recommendation(tables, dc, ident)["recommendation"] == "RR_NEXT"
    assert br.recommendation({**tables, "incompatible_tone_branches": ["1"]}, dc, ident)["decisions"] == ["tone_branch"]
    assert br.recommendation(tables, {"class": "FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES"}, ident)["decisions"] == \
        ["redundant"]
    assert br.recommendation(tables, dc, {**ident, "gain": {"class": "PARTIALLY_CONSTRAINED"}})["decisions"] == \
        ["level_emptied"]


def test_no_legacy_no_p2f_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {(n.module or "") + ":" + a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                for a in n.names}
    assert not any(x in name for name in imported for x in ("family_engine", "legacy_adapter", "contracts_legacy",
                                                             ":shadow"))
    assert "lr.P2FGuard(), lr.LegacyLock()" in inspect.getsource(br.run)
    assert '"nothing_approved": True' in inspect.getsource(br.run) and "approved\": []" in inspect.getsource(br.verdict)
    assert "RR is not started" in br.RECOMMENDATION_RULE


# The committed record ---------------------------------------------------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2J4_baroreflex.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2J4_BARORREFLEJO_Y_RECERTIFICACION_FC.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == br.P2J3_DIGEST
    assert record["design"] == _json(br.design()) and record["probes"] == _json(br.probes())
    latent = br.latent_region()
    assert record["latent"]["combos"] == _json({f"{f:g}": v for f, v in latent["combos"].items()})
    assert record["latent"]["HR_PRIOR_REGION_REJECTION"] == latent["prior_region_rejection"]


def test_the_verdict_follows_its_checks_on_the_recorded_inputs(record):
    checks = record["verdict"]["checks"]
    assert all(checks.values()) and record["verdict"]["verdict"] == br.READY and record["verdict"]["approved"] == []
    assert record["pressure_tone"]["unchanged"] == {"units": True, "primary": True, "support": True,
                                                    "demand_class": True}
    v = record["validation"]
    assert v["hr_equal"] and v["rows_equal"] and v["states_equal"] and v["baroreflex_moved_drive"] == v["tasks"] == 654
    assert len(v["checked_points"]) == len(br.PRIMARY_POINTS)
    primary = {k: x for k, x in record["filter"].items() if not k.endswith("reference")}
    arrival = any(x["entering"] - x["first_failure"]["ARRIVAL"] for x in primary.values())
    survivors = any(x["survivors"] for x in primary.values())
    assert br.verdict(checks, arrival, survivors)["verdict"] == record["verdict"]["verdict"]
    assert br.recommendation(record["support"], record["double_counting"],
                             record["identifiability"])["recommendation"] == record["recommendation"]["recommendation"]


def test_the_filter_counts_add_up_and_the_reference_is_p2j3_s(record):
    for key, x in record["filter"].items():
        assert x["entering"] == x["survivors"] + sum(x["first_failure"].values()), key
        assert x["first_failure"]["DOMAIN"] == x["first_failure"]["SIMULATION"] == 0
        if key.endswith("reference"):
            assert x["survivors"] == x["entering"]
    p2j3 = br.p2j3_record()["hr"]["by_point"]
    assert {k: v["candidate_rows"] for k, v in record["reference"].items()} == \
        {k: v["candidate_rows"] for k, v in p2j3.items()}
    assert all(v["failures"] == {} for v in record["reference"].values())
    assert record["support"]["incompatible_tone_branches"] == []
    assert record["double_counting"]["class"] == "STRUCTURALLY_DISTINCT_BUT_CORRELATED"
    assert all(x["sign_violations"] == 0 for x in record["double_counting"]["by_map_set"].values())


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import baroreflex_report as rp
    copy = tmp_path / "doc.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    assert rp.main(["--write", str(copy), "--data", str(RECORD)]) == 0
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8")
    text = DOCUMENT.read_text(encoding="utf-8")
    assert "BAROREFLEX_HR_RECERTIFICATION_SATISFIED" in text and "RR_NEXT" in text
    for name in rp.NAMES:
        assert f"<!-- generado:{name} -->" in text
