"""Phase 2 shadow core, P2K-4: the faculty's RR / ventilation observable-envelope filter.

These tests pin the frozen faculty rules (A-I, the arrival windows, untreated and arrival pH never filters, the support
unchanged and gain 0.08 excluded, the demand semantics), the matched comparators (each omits only its target exposure;
R3 is never compared with R4 as a red-cell counterfactual), the respiratory signal (burden and pH together, never RR
alone; RR and PaCO2 follow the burden), the bitset filter against its independent direct recomputation on synthetic
(non-clinical) bloods, the R3 / R4 classes, identifiability and cross-demand classes, the verdict, the recommendation, the
closure maps and the policy. No clinical count is read here.
"""
import ast
import hashlib
import inspect
import json

import pytest

from clinical_core import acid_base as ab
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import lactate_adequacy as la
from clinical_core import vascular_tone as vt
from clinical_core import ventilation_filter as vf
from clinical_core import ventilation_surface as vs

ROOT = vf.ROOT
SOURCE = ROOT / "clinical_core" / "ventilation_filter.py"
#: The P2K-4 freeze: the faculty rules, comparators, classes, order, criteria and every clinical_core source but the
#: downstream reports, committed before any survivor count was computed.
FROZEN_DIGEST = "638b64f699ddd53afda7f2e11eebf77e418a28789da8c47e667343738c642773"
C57, C72 = vf.C57, vf.C72
N = 121


# Synthetic, non-clinical blood records (shape of P2J-3's cached records) ----------------------------------------------------

def _record(output, crystalloid=None, prbc=None, controlled_at=None):
    return {"output1": list(output), "hb": [7.0] * N, "spo2": [0.97] * N, "pulse": [True] * N, "bleed": [1.0] * N,
            "crystalloid": crystalloid or [0.0] * N, "prbc": prbc or [0.0] * N, "controlled_at": controlled_at,
            "stop": None, "demand": [1.0] * N}


def _ramp(total, end, start=0):
    return [0.0 if m < start else min(total, total * (m - start) / (end - start)) for m in range(N)]


def _bloods():
    out = {}
    for case in vf.CASES:
        falling = [max(0.35, 0.75 - 0.003 * m) for m in range(N)]
        out.update({("P1", case, 0): _record(falling),
                    ("P2", case, (0, 0)): _record([min(1.2, x + 0.3) for x in falling], crystalloid=_ramp(1000.0, 20)),
                    ("P3", case, 1): _record([0.8] * N, prbc=_ramp(2.0, 60)),
                    ("P4", case, 1): _record([0.8 if m < 60 else 1.1 for m in range(N)], prbc=_ramp(2.0, 60),
                                             controlled_at=60),
                    ("CF1", case, 1): _record([0.75 if m < 60 else 1.0 for m in range(N)], prbc=_ramp(1.0, 60, 30),
                                              controlled_at=60),
                    ("CF2", case, 1): _record([0.75 if m < 60 else 1.0 for m in range(N)], prbc=_ramp(1.0, 30),
                                              controlled_at=60),
                    ("NP", case, 1): _record([0.55] * N)})
    return out


def _states():
    s3 = {"complete": True, "controlled_at": None, "bleed_rate": 1.0, "shed_ml": 242.0, "volume_ml": -300.0,
          "red_cells": 4.0, "hb": 7.0}
    s4 = {"complete": True, "controlled_at": 60, "bleed_rate": 0.0, "shed_ml": 135.0, "volume_ml": -150.0,
          "red_cells": 4.5, "hb": 7.0}
    return {(kind, case, 1): (s3 if kind == "P3" else s4) for case in vf.CASES for kind in ("P3", "P4")}


@pytest.fixture(scope="module")
def source_space():
    record = la.record_p2i2ab()
    return {"source": la.source_space(record), "support": record["crystalloid_support"]}


# The frozen package ---------------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(vf.OWN) <= set(sources) and vf.REPORT not in sources
    assert vf.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/ventilation_filter.py", vf.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    # The closed P2K-3 record it builds on (its frozen digest, test_clinical_core_ventilation_surface.FROZEN_DIGEST).
    assert vf.p2k3_record()["freeze_digest"] == vf.P2K3_DIGEST == \
        "23f1673fe24fe6a49a9fed13e60088eb05f5f15c8cf5eec2700618bca2a897e3"
    # P2K-4 is closed (P2K-5): its freeze is recomputed with its own formula on the sources it froze, P2K-5's module
    # left out and the two tuple-only files at their P2K-4 hashes while only their tuples changed
    # (respiratory_monotonicity.p2k4_freeze_digest; the formula is pinned in test_clinical_core_respiratory_monotonicity).
    # Since P2L-1 the sources also drop P2L-1's module (consciousness_audit.p2k5_sources) before P2K-5's map.
    from clinical_core import consciousness_audit as ca
    from clinical_core import respiratory_monotonicity as rm
    assert '"sources": p2k4_sources(bf.freeze_sources())}' in inspect.getsource(rm.p2k4_freeze_digest)
    text = json.dumps({"revision": vf.REVISION, "p2k3": hashlib.sha256(vf.P2K3_RECORD.read_bytes()).hexdigest(),
                       "design": vf.design(), "sources": rm.p2k4_sources(ca.p2k5_sources(bf.freeze_sources()))},
                      sort_keys=True, default=str)
    if FROZEN_DIGEST is not None:
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == FROZEN_DIGEST, \
            "a source, a rule or a support changed after the freeze"


def test_the_closed_files_keep_their_ef2cfe8_bytes_and_nothing_imports_the_filter():
    assert all(vf.closed_unchanged().values()) and len(vf.CLOSED_AT_P2K3) == 6
    for path in (ROOT / "clinical_core").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        if any("ventilation_filter" in name for name in imported):
            # P2K-5's closure module and its report reuse the frozen filter (analysis only; no core step does).
            assert path.name in ("ventilation_filter_report.py", "respiratory_monotonicity.py",
                                 "respiratory_monotonicity_report.py"), path.name


def test_the_closed_packages_see_p2k3s_sources():
    sources = bf.freeze_sources()
    mapped = vf.p2k3_sources(sources)
    assert not set(vf.OWN) & set(mapped)
    for relative, sha in vf.TUPLE_AT_P2K3.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert vf.p2k3_sources(sources)["clinical_core/decision_pack.py"] == sources["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


# The faculty rules, exactly ------------------------------------------------------------------------------------------------

def test_the_envelopes_and_windows_are_the_faculty_numbers():
    e = vf.ENVELOPES
    assert (e["A"]["rr"], e["B"]["rr"], e["C"]["paco2"], e["D"]["paco2"]) == ((24, 38), (20, 36), (18, 35), (22, 38))
    assert (e["G"]["rr"], e["G2"]["rr"], e["H"]["paco2"], e["H"]["ph"]) == ((12, 27), (12, 24), (30, 42), (7.35, 7.45))
    assert e["I"]["residual"] == {C57: (0, 12), C72: (0, 10)} and vf.MINUTE == 120
    assert vf.ARRIVAL_RR == {C57: (23, 29), C72: (21, 27)} and vf.ARRIVAL_PACO2 == {C57: (28, 34), C72: (30, 36)}
    assert (e["A"]["case"], e["B"]["case"], e["G"]["case"], e["G2"]["case"]) == (C57, C72, C57, C72)
    assert vf.EXTREME_ACIDEMIA == 7.00 and "never a rejection" in vf.EXTREME_RULE
    assert "not required to be at or above the arrival RR" in e["B"]["text"]


def test_the_support_is_p2k3s_without_gain_0_08_and_the_references_are_unchanged():
    assert vf.VENTILATION_GAINS == (0.03, 0.04, 0.05, 0.06) and 0.08 in vs.VENTILATION_GAINS
    assert vf.DRIVE_GAINS == ab.DRIVE_GAINS and vf.INTRINSIC_RR == (12.0, 16.0, 20.0)
    assert vf.STEADY_BURDENS == (13.4, 19.4, 28.0) and vf.ACID_TAUS == (60.0, 120.0, 240.0)
    assert vf.N_LATENT == 1620 and vs.PACO2_REFERENCE == 40.0 and vs.HCO3_REFERENCE == 24.0
    assert vf.DEMAND_NORMALIZATION["semantics"].startswith("BASELINE_RELATIVE")
    assert vf.STATUS["approved"] == "none FACULTY_APPROVED"


def test_the_order_and_its_classes():
    assert vf.ORDER == ("SIMULATION", "ARRIVAL_RR", "ARRIVAL_PACO2", "A", "B", "G", "G2", "H_PACO2", "H_PH", "I", "C",
                        "D", "E", "F")
    assert set(vf.REJECTION_CLASS) == set(vf.ORDER) and set(vf.REJECTION_CLASS.values()) == set(vf.REJECTION_CLASSES)
    assert vf.REJECTION_CLASS["H_PH"] == "PH_ENVELOPE_REJECTION"
    # Arrival pH and untreated pH never filter: no rule reads them.
    assert not any("ARRIVAL_PH" in name or "UNTREATED" in name for name in vf.ORDER)
    assert {r for r in vf.ORDER if vf.REJECTION_CLASS[r] == "PH_ENVELOPE_REJECTION"} == {"H_PH"}


def test_the_bitset_layout():
    for index in (0, 1, 811, vf.N_LATENT - 1):
        assert vf.latent_index(vf.latent_digits(index)) == index
    assert vf.bits_of(("tau",), [(t,) for t in range(3)]) == vf.FULL
    assert (vf.mask(("B", "tau"), (0, 0)) & vf.mask(("B", "tau"), (0, 1))) == 0


def test_the_arrival_bits_are_p2k3s_analytic_arrival():
    rr = ab.arrival_compatibility()["compatible"]
    assert vf.arrival_rr_bits() == vf.bits_of(vf.ARRIVAL_RR_DIMS, [(vf.DRIVE_GAINS.index(g), vf.INTRINSIC_RR.index(a),
                                                                     vf.INTRINSIC_RR.index(b)) for g, a, b in rr])
    assert vf.arrival_paco2_bits() == vf.FULL
    assert set(vf.arrival_ph_diagnostic()) == {"0.03", "0.04", "0.05", "0.06"}


# The matched comparators -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", [C57, C72])
def test_each_comparator_omits_only_its_target_exposure(source_space, case):
    for treated, comparator, k1, k2 in (("P2", "P1", (0, 0), 0), ("P2", "P1", (5, 11), 5), ("P3", "NP", 1, 1),
                                         ("P3", "NP", 400, 400), ("P4", "CF1", 1, 1), ("P4", "CF2", 1, 1),
                                         ("P4", "CF2", 457, 457)):
        result = vf.comparator_inputs(source_space, treated, comparator, case, k1, k2)
        assert result["matched"], (treated, comparator, k1, result)
    assert not vf.comparator_inputs(source_space, "P2", "P1", case, (0, 0), 1)["matched"]
    assert not vf.comparator_inputs(source_space, "P3", "NP", case, 1, 2)["matched"]


def test_r3_is_never_a_red_cell_counterfactual_of_r4():
    pairs = {(t, c) for rows in vf.COMPARATORS.values() for t, c, *_ in rows}
    assert pairs == {("P2", "P1"), ("P3", "NP"), ("P4", "CF1"), ("P4", "CF2")}
    assert ("P3", "P4") not in pairs and ("P4", "P3") not in pairs
    with pytest.raises(ValueError):
        vf.comparison_minutes("P3", "P4", {"prbc": [0.0] * N})


def test_the_comparison_minutes_reuse_p2j3s_rule():
    blood = {"crystalloid": _ramp(1000.0, 20), "prbc": _ramp(2.0, 60)}
    assert vf.comparison_minutes("P2", "P1", blood) == (20, 120)
    assert vf.comparison_minutes("P4", "CF1", blood) == (30, 120) and vf.comparison_minutes("P4", "CF2", blood) == (60, 120)
    assert vf.comparison_minutes("P3", "NP", blood) == (30, 60, 120)


# The respiratory signal -----------------------------------------------------------------------------------------------------

def test_the_signal_reads_burden_and_ph_together_never_rr_alone():
    assert vf.classify(-1, -1) == vf.WORSEN and vf.classify(1, 0) == vf.CLASSES[1] and vf.classify(0, -1) == vf.CLASSES[5]
    assert vf.respiratory_signal(0.5, -0.01, 5.0, 7.3) == -1 and vf.respiratory_signal(0.5, 0.01, 5.0, 7.3) == 0
    assert vf.respiratory_signal(-0.5, 0.01, 5.0, 7.3) == 1 and vf.perfusion_signal(1e-12, 0.4) == 0
    assert set(vf.REJECTING) == {vf.WORSEN, vf.TREATED_ARREST}
    assert "RR alone never classifies" in vf.SIGNAL_RULE
    import inspect
    assert "rr" not in inspect.signature(vf.respiratory_signal).parameters


def test_rr_and_paco2_follow_the_burden_off_grid():
    for burden_t, burden_c in ((0.0, 0.0), (1.0, 0.5), (30.0, 2.0), (2.0, 30.0)):
        assert vf.rr_follows_burden(burden_t, burden_c)
        for gain in (0.01, 0.07, 0.2):
            d = 40.0 / (1 + gain * burden_t) - 40.0 / (1 + gain * burden_c)
            assert vf.paco2_follows_burden(burden_t - burden_c, burden_c, d)
    assert not vf.paco2_follows_burden(1.0, 5.0, 0.5)


def test_a_reading_handles_arrest_and_impossible_values():
    rows = [{"deficit": 0.2}] * N
    t = vf.bundle(rows, [True] * N, C57, 19.4, 120.0)
    dead = vf.bundle(rows, [True] * 60 + [False] * 61, C57, 19.4, 120.0)
    assert vf.reading(dead, t, 90, 0.05)["class"] == vf.TREATED_ARREST
    assert vf.reading(t, dead, 90, 0.05)["class"] == "COMPARATOR_ARREST_WITH_TREATED_BREATHING"
    huge = vf.bundle([{"deficit": 5.0}] * N, [True] * N, C57, 28.0, 60.0)
    assert vf.reading(huge, t, 120, 0.05)["class"] == "NO_COMPARISON_IMPOSSIBLE_VALUE"


# The filter against its direct recomputation (synthetic bloods) ---------------------------------------------------------------

def test_the_bitset_filter_equals_the_direct_recomputation_on_synthetic_bloods():
    bloods, states = _bloods(), _states()
    survivor = (0, 0, 0, 1, 0)
    tally, obs = vf.Tally(), vf.Observed()
    arrival = vf.arrival_bits()
    units, sample = vf.filter_point(bloods, [survivor], 1.0, 0.5, arrival, tally, obs, states)
    direct = vf.direct_check(bloods, sample, arrival)
    assert direct["equal"] and direct["candidates"] == vf.N_LATENT and direct["mismatches"] == 0
    assert tally.entering == vf.N_LATENT and sum(tally.first.values()) + tally.survivors == vf.N_LATENT
    # The observation path on the same parts, every bit set.
    parts = vf.evaluate_parts(bloods, [survivor], 1.0, 0.5)
    seen = vf.Observed()
    vf.observe(seen, parts, [(survivor, vf.FULL)], states, bloods)
    public = seen.public()
    assert public["comparison_minutes"] == {"crystalloid": [20, 120], "prbc_R3": [30, 60, 120],
                                            "prbc_R4_unit1": [30, 120], "prbc_R4_unit2": [60, 120]}
    assert all(s["checked"] == s["held"] > 0 for s in public["signs"].values())
    assert sum(public["r3r4"]["classes"].values()) == 2 and not public["r3r4"]["bug"]
    json.dumps(public, default=str)



def test_e_and_f_reject_a_harmful_treatment_and_the_direct_check_agrees():
    """Review L3: on real data E and F never fail, so a synthetic harm shows they can (and that the filter's bits equal
    the direct recomputation when they do)."""
    bloods = _bloods()
    for case in vf.CASES:
        falling = bloods[("P1", case, 0)]["output1"]
        bloods[("P2", case, (0, 0))]["output1"] = [x - 0.15 for x in falling]
        bloods[("P3", case, 1)]["output1"] = [0.45] * N
    arrival = vf.arrival_bits()
    tally, obs = vf.Tally(), vf.Observed()
    _, sample = vf.filter_point(bloods, [(0, 0, 0, 1, 0)], 1.0, 0.5, arrival, tally, obs, _states())
    assert tally.any["E"] > 0 and tally.any["F"] > 0
    direct = vf.direct_check(bloods, sample, arrival)
    assert direct["equal"] and direct["mismatches"] == 0

def test_the_tally_counts_first_sole_and_paired_failures():
    t = vf.Tally()
    rules = {name: vf.FULL for name in vf.ORDER}
    rules["A"], rules["C"] = vf.FULL & ~1, vf.FULL & ~3
    t.add(rules, 0.5)
    assert (t.first["A"], t.first["C"], t.any["C"], t.only["A"], t.only["C"]) == (1, 1, 2, 0, 1)
    assert t.pairs["A+C"] == 1 and t.survivors == vf.N_LATENT - 2
    assert t.class_first["RR_ENVELOPE_REJECTION"] == 1 and t.class_any["PACO2_ENVELOPE_REJECTION"] == 2


# R3 / R4 ------------------------------------------------------------------------------------------------------------------------

def test_r3_r4_convergence_needs_distinct_underlying_states():
    states = _states()
    rows = [{"output": 1.4, "delivery_rel": 1.0, "deficit": 0.0}] * N
    blood = {"prbc": [0.0] * N, "crystalloid": [0.0] * N}
    zero = {k: 0.0 for k in vf.R3R4_NEAR}
    pair = vf.underlying(states[("P3", C57, 1)], states[("P4", C57, 1)], blood, blood, rows, rows)
    assert vf.r3r4_class(pair, zero) == "PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE"
    assert vf.r3r4_class(pair, {**zero, "rr": 0.5}) == "RESPIRATORY_OUTPUTS_DISTINCT"
    same = vf.underlying(states[("P4", C57, 1)], states[("P4", C57, 1)], blood, blood, rows, rows)
    assert vf.r3r4_class(same, zero) == "SCENARIO_STATE_COLLAPSE_BUG"
    shifted = vf.underlying(states[("P3", C57, 1)], states[("P4", C57, 1)], blood, {**blood, "prbc": [1.0] * N}, rows,
                            rows)
    assert vf.r3r4_class(shifted, zero) == "SCENARIO_STATE_COLLAPSE_BUG"
    # Hb is reported, never required to differ (whole-blood loss keeps the concentration).
    assert not pair["hb_differs"] and pair["distinct"]


# Identifiability and demand classes ------------------------------------------------------------------------------------------

def test_identifiability_and_cross_demand_classes():
    b0 = vf.DIM_MASKS["B"][0]
    support = vf.latent_support(b0, [b0])
    assert support["B"]["class"] == "WELL_CONSTRAINED" and support["tau"]["class"] == "NON_IDENTIFIABLE"
    assert all(v["class"] == "NON_IDENTIFIABLE" for v in vf.latent_support(vf.FULL, [vf.FULL]).values())
    two = vf.DIM_MASKS["drive_gain"][0] | vf.DIM_MASKS["drive_gain"][1]
    assert vf.latent_support(two, [two])["drive_gain"]["class"] == "PARTIALLY_CONSTRAINED"
    assert vf.latent_support(0, [0])["B"]["class"] == "NON_IDENTIFIABLE"
    cross = vf.cross_demand({1.0: b0, 1.1: vf.FULL})
    assert (cross["ROBUST_ACROSS_DEMAND"]["count"], cross["DEMAND_1_1_ONLY"]["count"]) == (540, 1080)
    assert vf.DEMAND_CLASSES == ("ROBUST_ACROSS_DEMAND", "DEMAND_1_0_ONLY", "DEMAND_1_1_ONLY", "DEMAND_INCOMPATIBLE")


# Verdict, recommendation, policy -------------------------------------------------------------------------------------------------

def test_the_verdict_rule_and_the_recommendation():
    assert vf.verdict({name: True for name in vf.CRITERIA})["verdict"] == vf.READY
    assert vf.verdict({"upstream_unchanged": True, "survivors_exist": False})["verdict"] == vf.EMPTY
    assert vf.verdict({"upstream_unchanged": False})["verdict"] == f"{vf.NOT_READY} - UPSTREAM_UNCHANGED"
    assert vf.verdict({"upstream_unchanged": True})["verdict"] == f"{vf.NOT_READY} - NOT_EVALUATED"
    assert "robustness across demands is diagnostic, never required" in vf.VERDICT_RULE
    assert vf.recommendation({"verdict": vf.READY})["recommendation"] == "MOVE_FORWARD"
    assert vf.recommendation({"verdict": vf.EMPTY})["recommendation"] == "STOP_FOR_FACULTY_REVIEW"
    assert "never call for another respiratory package" in vf.NEXT_RULE


def test_a_changed_closed_file_stops_before_any_trajectory(monkeypatch):
    monkeypatch.setattr(vf, "closed_unchanged", lambda: {"clinical_core/derived.py": False})
    out = vf.run()
    assert out["verdict"]["verdict"] == f"{vf.NOT_READY} - UPSTREAM_UNCHANGED" and "STOP" in out["stopped"]
    assert "demands" not in out and "survivors_exist" in out["verdict"]["not_evaluated"]


def test_the_policy_approves_nothing_and_reads_no_legacy():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("family_engine", "legacy_adapter", "snapshot("):
        assert forbidden not in source
    assert "nothing selected or approved" in vf.POLICY and "untreated and arrival pH never filter" in vf.POLICY
    assert vf.MIGRATION_GATE.startswith("MIGRATION_GATE_CLOSED")
    assert json.loads(json.dumps(vf.design(), default=str))["values"]["ventilation_gain"] == [0.03, 0.04, 0.05, 0.06]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2K4_ventilation_filter.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2K4_FILTRO_ENVOLVENTES_RESPIRATORIAS.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == vf.P2K3_DIGEST
    assert record["design"] == _json(vf.design()) and record["closed_unchanged"] == _json(vf.closed_unchanged())
    assert record["arrival_ph_diagnostic"] == _json(vf.arrival_ph_diagnostic()) and "stopped" not in record


def test_the_verdict_and_the_upstream_non_regression_the_report_states(record):
    v = record["verdict"]
    assert v["verdict"] == vf.READY and not v["failing"] and not v["not_evaluated"]
    assert set(v["checks"]) == set(vf.CRITERIA) and all(v["checks"].values())
    assert record["recommendation"]["recommendation"] == "MOVE_FORWARD"
    assert all(record["p2k3_reproduced"].values()) and all(record["arrival_reproduced"].values())
    c = record["comparator_validation"]
    assert c["compared"] == 18 and c["equal"] and c["max_abs_diff"] == 0.0 and c["upstream_equal"]
    assert all(c["domains"].values()) and set(c["domains"]) == set(vs.UPSTREAM_DOMAINS)
    assert record["comparators_matched"]["matched"] and record["comparators_matched"]["checked"] > 0
    d = record["direct_check"]
    assert d["equal"] and d["mismatches"] == 0 and d["units"] == 12 and d["candidates"] == 12 * vf.N_LATENT
    assert record["efficiency"]["cartesian_sweep"] is False and record["efficiency"]["legacy_read"] is False


def test_the_filter_counts_add_up(record):
    for key, data in record["demands"].items():
        f = data["filter"]
        assert f["entering"] == f["upstream_units"] * vf.N_LATENT
        assert sum(f["first_failure"].values()) + f["survivors"] == f["entering"]
        assert sum(f["rejection_classes_first"].values()) == sum(f["first_failure"].values())
        assert sum(v["survivors"] for v in f["by_tone_gain"].values()) == f["survivors"] > 0
        for rule in ("SIMULATION", "ARRIVAL_PACO2", "C", "D", "H_PACO2", "H_PH", "E", "F"):
            assert f["any_failure"][rule] == 0, (key, rule)
    cross = record["cross_demand"]
    assert sum(item["count"] for item in cross.values()) == vf.N_LATENT
    assert cross["ROBUST_ACROSS_DEMAND"]["count"] == 312 and cross["DEMAND_1_0_ONLY"]["count"] == 0


def test_every_survivor_observable_lies_in_its_envelope(record):
    e = vf.ENVELOPES
    for data in record["demands"].values():
        o = data["observed"]["observables"]
        within = lambda name, case, bounds: bounds[0] <= o[f"{name} {case}"]["low"] <= o[f"{name} {case}"]["high"] <= bounds[1]
        for case, a, g in ((C57, "A", "G"), (C72, "B", "G2")):
            assert within("untreated_rr_120", case, e[a]["rr"]) and within("definitive_rr_120", case, e[g]["rr"])
            assert within("untreated_paco2_120", case, e["C" if case == C57 else "D"]["paco2"])
            assert within("definitive_paco2_120", case, e["H"]["paco2"]) and within("definitive_ph_120", case, e["H"]["ph"])
            assert within("residual_rr_above_intrinsic_120", case, e["I"]["residual"][case])
            assert within("arrival_rr", case, vf.ARRIVAL_RR[case]) and within("arrival_paco2", case, vf.ARRIVAL_PACO2[case])


def test_untreated_ph_is_reported_never_filtered(record):
    x = record["demands"]["1.1"]["observed"]["extreme_acidemia"]
    assert x["flagged"] > 0 and x["lowest"]["ph"] < vf.EXTREME_ACIDEMIA
    assert x["lowest"]["flag"] == "CONSCIOUSNESS_COLLAPSE_REVIEW"


def test_r3_r4_converge_physiologically_and_the_counterfactuals_never_worsen(record):
    for data in record["demands"].values():
        r = data["observed"]["r3r4"]
        assert not r["bug"] and r["classes"]["SCENARIO_STATE_COLLAPSE_BUG"] == 0
        assert r["classes"]["PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE"] > 0
        for pair in r["pairs"]:
            u = pair["underlying"]
            assert u["bleeding_differs"] and u["blood_state_differs"] and u["chronology_same"]
        for counts in data["observed"]["classes"].values():
            assert not any(counts.get(c) for c in vf.REJECTING)
        assert all(s["checked"] == s["held"] > 0 for s in data["observed"]["signs"].values())


def test_the_document_is_generated_from_the_record():
    from clinical_core import ventilation_filter_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    rendered = document
    for name, render in rep.RENDERERS.items():
        rendered = rep.apply(rendered, name, render(data))
    assert rendered == document, "the generated blocks are stale: regenerate the report"
    assert vf.READY in document and "## 13. Lo que se pide a la docencia" in document
    assert "## 14. Limitaciones" in document and "## 15. Revisión adversarial" in document
