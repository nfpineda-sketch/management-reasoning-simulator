"""P2K-5: the final respiratory monotonicity closure (shadow only).

The analytic rule (pH non-increasing in the metabolic acid burden iff g_v <= 1 / HCO3_reference), the gain classes it
gives, the executable mapping it is about, the synthetic probes, the corrected treatment-response signal (P2K-4 review
M1 / M2), the exact reuse of P2K-4 (closure, certificates, the reached recomputation mirroring P2K-4's own functions),
the pruned support and the verdict. The record tests read the committed run.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from fractions import Fraction

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import respiratory_monotonicity as rm
from clinical_core import vascular_tone as vt
from clinical_core import ventilation as vn
from clinical_core import ventilation_filter as vf
from clinical_core import ventilation_surface as vs
from clinical_core.state import Channel

ROOT = rm.ROOT
SOURCE = ROOT / "clinical_core" / "respiratory_monotonicity.py"
#: The P2K-5 freeze: the analytic rule, the gain classes, the corrected signal, the reuse and reach rules, the support,
#: identifiability, verdict and recommendation rules and every clinical_core source but the downstream reports,
#: committed before any pruned count was computed by the run.
FROZEN_DIGEST = "561a8878ecf13899d660e9a11db530212678ba0f426f6f5aeb4dbd461efbc112"
C57, C72 = rm.C57, rm.C72
N = 121


# Synthetic, non-clinical blood records (the shape of P2J-3's cached records, as in P2K-4's tests) ---------------------------

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


def _bundle(burden, deficit, case=C57):
    pulse = [True] * len(burden)
    hco3 = vs.hco3_series(burden, case)
    return {"n": len(burden), "deficit": list(deficit), "pulse": pulse, "burden": list(burden), "hco3": hco3,
            "gas": {g: vs.gas_series(burden, hco3, pulse, g) for g in vf.VENTILATION_GAINS}}


# The frozen package and its closure --------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(rm.OWN) <= set(sources) and rm.REPORT not in sources
    assert rm.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {rm.OWN[0], rm.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    # The closed P2K-4 record and freeze it builds on, pinned (test_clinical_core_ventilation_filter.FROZEN_DIGEST).
    record = rm.p2k4_record()
    assert record["freeze_digest"] == rm.P2K4_DIGEST == "638b64f699ddd53afda7f2e11eebf77e418a28789da8c47e667343738c642773"
    # P2K-5 is closed (P2L-1): both freezes are recomputed with their own formulas on the sources they froze, P2L-1's
    # module left out and the tuple-only files at their P2K-5 hashes (consciousness_audit.p2k5_sources), after P2L-2's
    # modules and tuple entries are left out (encephalopathy_architecture.p2l1_sources).
    from clinical_core import consciousness_audit as ca
    from clinical_core import collapse_audit as cm
    from clinical_core import encephalopathy_architecture as ea
    sources = ca.p2k5_sources(ea.p2l1_sources(cm.p2l2_sources(bf.freeze_sources())))
    p2k4 = json.dumps({"revision": vf.REVISION, "p2k3": hashlib.sha256(vf.P2K3_RECORD.read_bytes()).hexdigest(),
                       "design": vf.design(), "sources": rm.p2k4_sources(sources)}, sort_keys=True, default=str)
    assert hashlib.sha256(p2k4.encode("utf-8")).hexdigest() == rm.P2K4_DIGEST
    # The recomputation is ventilation_filter.freeze_digest's own formula (its source unchanged since P2K-4).
    assert '"sources": bf.freeze_sources()}, sort_keys=True, default=str)' in inspect.getsource(vf.freeze_digest)
    assert '"design": vf.design(), "sources": p2k4_sources(bf.freeze_sources())}' in inspect.getsource(
        rm.p2k4_freeze_digest)
    assert '"design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)' in inspect.getsource(
        rm.freeze_digest)
    own = json.dumps({"revision": rm.REVISION, "p2k4": hashlib.sha256(rm.P2K4_RECORD.read_bytes()).hexdigest(),
                      "design": rm.design(), "sources": sources}, sort_keys=True, default=str)
    if FROZEN_DIGEST is not None:
        assert hashlib.sha256(own.encode("utf-8")).hexdigest() == FROZEN_DIGEST, \
            "a source, a rule or a support changed after the freeze"


def test_the_closed_files_keep_their_p2k4_bytes_and_nothing_imports_the_closure():
    assert all(rm.closed_unchanged().values()) and len(rm.CLOSED_AT_P2K4) == 7
    assert {k: v for k, v in rm.CLOSED_AT_P2K4.items() if k in vf.CLOSED_AT_P2K3} == vf.CLOSED_AT_P2K3
    for path in (ROOT / "clinical_core").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        if any("respiratory_monotonicity" in name for name in imported):
            assert path.name == "respiratory_monotonicity_report.py", path.name


def test_the_closed_packages_see_p2k4s_sources():
    sources = bf.freeze_sources()
    mapped = rm.p2k4_sources(sources)
    assert not set(rm.OWN) & set(mapped)
    for relative, sha in rm.TUPLE_AT_P2K4.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert rm.p2k4_sources(sources)["clinical_core/decision_pack.py"] == sources["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


# P2K-5-1: the analytic rule, exactly -------------------------------------------------------------------------------------

def test_the_slope_numerator_is_an_exact_identity():
    """d/dA ln[(h - A)(1 + gA)] = N(A) / [(1 + gA)(h - A)] with N = (gh - 1) - 2gA. Both sides are rational in A with a
    numerator of degree <= 2 once over the common denominator, so agreeing at three distinct points is a proof."""
    h = Fraction(24)
    for gain in rm.P2K4_GAINS + (0.08, 0.0, 1 / 24):
        g = rm.exact(gain)
        c, s = rm.numerator(gain)
        assert (c, s) == (g * h - 1, -2 * g)
        for a in (Fraction(0), Fraction(7, 3), Fraction(23, 2), Fraction(19)):
            lhs = g / (1 + g * a) - 1 / (h - a)
            assert lhs == (c + s * a) / ((1 + g * a) * (h - a))


def test_the_rule_decides_the_whole_domain_from_a_equals_zero():
    assert rm.critical_gain() == Fraction(1, 24) and rm.HCO3_REFERENCE == 24.0 and rm.PACO2_REFERENCE == 40.0
    for gain in rm.P2K4_GAINS + (0.08,):
        c, s = rm.numerator(gain)
        assert s <= 0  # N is non-increasing in A, so N(0) is its largest value on 0 <= A < 24
        assert rm.monotone(gain) == (c <= 0) == (rm.exact(gain) <= Fraction(1, 24))
    # Around the critical gain itself, exactly.
    assert rm.monotone(Fraction(1, 24)) and rm.monotone(Fraction(41, 1000)) and not rm.monotone(Fraction(42, 1000))
    assert rm.strictly_decreasing(Fraction(1, 24)) and rm.violation_interval(Fraction(1, 24)) is None


def test_the_gain_classes_come_from_the_analysis_alone():
    assert rm.GAIN_CLASSES == {"0.03": rm.ADMISSIBLE, "0.04": rm.ADMISSIBLE, "0.05": rm.REJECTED, "0.06": rm.REJECTED}
    assert rm.RETAINED_GAINS == (0.03, 0.04) and rm.REJECTED_GAINS == (0.05, 0.06)
    assert rm.PREVIOUSLY_EXCLUDED == {"0.08": rm.REJECTED}
    assert rm.violation_interval(0.05) == (0, Fraction(2)) and rm.violation_interval(0.06) == (0, Fraction(11, 3))
    assert rm.violation_interval(0.03) is None and rm.violation_interval(0.04) is None
    # The classifier's code names no count, record, region, trajectory or fit (its docstring aside).
    for fn in (rm.classify_gain, rm.monotone, rm.numerator, rm.exact, rm.critical_gain):
        tree = ast.parse(inspect.getsource(fn))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
            {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert names <= {"Fraction", "str", "value", "gain", "hco3_reference", "exact", "numerator", "monotone",
                         "constant", "slope", "g", "h", "ValueError", "ADMISSIBLE", "REJECTED", "HCO3_REFERENCE",
                         "float", "tuple", "bool"}, \
            (fn.__name__, names)


def test_the_closed_form_and_its_slope():
    for gain in rm.P2K4_GAINS:
        for a in (0.0, 0.5, 2.0, 6.7, 15.0, 22.0):
            step = 1e-6
            numeric = (rm.closed_form_ph(a + step, gain) - rm.closed_form_ph(a - step, gain)) / (2 * step) if a else \
                (rm.closed_form_ph(step, gain) - rm.closed_form_ph(0.0, gain)) / step
            assert abs(numeric - rm.slope(a, gain)) < 1e-5
    # The two rejected gains rise to a peak above the zero-burden pH; the admissible ones never do.
    proof = rm.analytic_proof()["gains"]
    assert proof["0.05"]["peak"]["ph"] > proof["0.05"]["peak"]["ph_at_0"] and proof["0.05"]["slope_at_0"] > 0
    assert proof["0.06"]["peak"]["ph"] > proof["0.06"]["peak"]["ph_at_0"] and proof["0.06"]["slope_at_0"] > 0
    assert proof["0.03"]["peak"] is None and proof["0.04"]["slope_at_0"] < 0
    # Efficiency and demand multiply PaCO2 by constants: pH shifts by a constant, the rule is unchanged.
    shift = [rm.closed_form_ph(a, 0.04, paco2_reference=40.0) - rm.closed_form_ph(a, 0.04, paco2_reference=44.0)
             for a in (0.0, 3.0, 9.0, 20.0)]
    assert max(shift) - min(shift) < 1e-12


def test_the_executable_mapping_is_the_analysed_one():
    check = rm.mapping_check()
    for case in vf.CASES:
        row = check[case]
        assert row["equal"] and row["reference_is_zero_burden"], case
        assert row["authored_hco3"] < rm.HCO3_REFERENCE and row["arrival_burden"] > 0
    assert "HCO3_reference" in rm.RULE_SCOPE and "generalization question" in rm.RULE_SCOPE
    # The core's own candidate function is the mapping the filter series use (efficiency 1, baseline demand).
    assert vn.ventilatory_capacity(3.0, 1.0, 0.04) == 1.0 + 0.04 * 3.0
    assert vn.paco2_from_ventilation(vn.effective_ventilation(1.12, 1.0), 40.0) == 40.0 / 1.12
    assert dv.CARBONIC_PK == 6.1 and dv.CO2_SOLUBILITY == 0.03


# P2K-5-2: the synthetic probes -------------------------------------------------------------------------------------------

def test_the_probes_show_attenuation_never_reversal():
    p = rm.probes()
    assert p["admissible_non_increasing"] and p["rejected_rise_at_low_burden"] and p["paco2_falls_with_burden"]
    for case in vf.CASES:
        for gain in ("0.03", "0.04"):
            row = p["rows"][case][gain]
            assert row["hco3_falls"] and row["paco2_falls"] and row["ph_non_increasing"] and not row["ph_rising_steps"]
            assert row["ph_change_0_to_arrival"] < 0
        for gain, top in (("0.05", 2.0), ("0.06", 11 / 3)):
            row = p["rows"][case][gain]
            assert row["ph_rising_steps"] and all(low < top for low, _ in row["ph_rising_steps"])
            assert row["ph_rising_steps"][0][0] == 0.0


# P2K-5-3: the corrected treatment-response signal (P2K-4 review M1 / M2) --------------------------------------------------

def test_the_correction_moves_only_the_declared_class():
    s = rm.semantics()
    assert s["only_perfusion_worse_higher_burden"] and s["never_unrejects"]
    assert [(r["perfusion"], r["burden"], r["ph"]) for r in s["changed"]] == [(-1, 1, 0), (-1, 1, 1)]
    assert s["paradox_directions"] == [(-1, -1), (1, 1)]
    assert s["rejecting"] == list(vf.REJECTING) and rm.PERFUSION_WORSE == (vf.CLASSES[2], vf.CLASSES[3], vf.WORSEN)
    # No numeric threshold is added: the only tolerance is P2J-3's.
    assert "1e-9" in rm.SEMANTIC_RULE
    tree = ast.parse(inspect.getsource(rm.corrected_signal))
    assert {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and not isinstance(n.value, str)} <= {0, 1, None}
    assert {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} == {"_sign"}


def test_m1_a_harmful_treatment_is_rejected_although_overcompensation_raises_ph():
    """The regression: at low burden with gain 0.06 a treatment that raises the burden and worsens perfusion raised pH, so
    P2K-4's conjunction could not reject it; the corrected signal does, and flags the paradox."""
    c, t = _bundle([1.0] * 3, [0.10] * 3), _bundle([1.6] * 3, [0.20] * 3)
    for gain in (0.05, 0.06):
        old, new = vf.reading(t, c, 1, gain), rm.corrected_reading(t, c, 1, gain)
        assert old["ph"] > 0 and old["burden"] > 0 and old["class"] == vf.CLASSES[3] and old["class"] not in vf.REJECTING
        assert new["class"] == vf.WORSEN and new["paradox"] == rm.PARADOX_HIGHER
    for gain in rm.RETAINED_GAINS:
        old, new = vf.reading(t, c, 1, gain), rm.corrected_reading(t, c, 1, gain)
        assert old["ph"] < 0 and old["class"] == new["class"] == vf.WORSEN and new["paradox"] is None


def test_m2_a_lower_burden_with_a_lower_ph_is_never_improvement():
    c, t = _bundle([1.6] * 3, [0.20] * 3), _bundle([1.0] * 3, [0.10] * 3)
    for gain in (0.05, 0.06):
        new = rm.corrected_reading(t, c, 1, gain)
        assert new["ph"] < 0 and new["class"] == vf.CLASSES[1] and new["paradox"] == rm.PARADOX_LOWER
    for gain in rm.RETAINED_GAINS:
        old, new = vf.reading(t, c, 1, gain), rm.corrected_reading(t, c, 1, gain)
        assert old["class"] == new["class"] == vf.CLASSES[0] and new["paradox"] is None
    # Arrests and impossible values are classified as P2K-4 classifies them.
    dead = _bundle([1.0] * 3, [0.1] * 3)
    dead["pulse"] = [True, False, False]
    assert rm.corrected_reading(dead, c, 1, 0.03)["class"] == vf.TREATED_ARREST


def test_no_paradox_is_reachable_at_a_retained_gain_on_a_dense_grid():
    """The analytic unreachability of the paradox flags, shown on a grid of matched readings (burden steps of 0.1 mEq/L,
    far above the no-change tolerance): no flag and no class change at 0.03 / 0.04, both at 0.05 / 0.06."""
    grid = [k / 10 for k in range(0, 231)]
    for gain in rm.P2K4_GAINS:
        hco3 = vs.hco3_series(grid, C57)
        ph = vs.gas_series(grid, hco3, [True] * len(grid), gain)[2]
        paradox = changed = 0
        for i, (a_t, p_t) in enumerate(zip(grid, ph)):
            for a_c, p_c in zip(grid, ph):
                signal, flag = rm.corrected_signal(a_t - a_c, p_t - p_c, a_c, p_c)
                paradox += flag is not None
                old = vf.respiratory_signal(a_t - a_c, p_t - p_c, a_c, p_c)
                changed += vf.classify(-1, old) != vf.classify(-1, signal)
        if gain in rm.RETAINED_GAINS:
            assert paradox == changed == 0, gain
        else:
            assert paradox > 0 and changed > 0, gain
    assert all(rm.paradox_unreachable().values()) and rm.FLOAT_MARGIN < rm.TOLERANCE_FLOOR


def test_the_correction_reaches_a_retained_gain_only_in_the_tolerance_gap():
    """Review M-1: at 0.03 / 0.04 the corrected signal still moves one reading class, a burden higher beyond its
    tolerance with a pH change within its own (a burden difference below about 1e-5 mEq/L) and a worse perfusion:
    P2K-4 does not reject it, P2K-5 does. No paradox is flagged. No survivor reading of the P2K-4 record has a worse
    perfusion, so the region is not reached; the case is pinned here so the claim stays exact."""
    for gain, a_c in ((0.04, 1.0), (0.03, 10.0)):
        c, t = _bundle([a_c] * 3, [0.10] * 3), _bundle([a_c + 1e-7] * 3, [0.20] * 3)
        old, new = vf.reading(t, c, 1, gain), rm.corrected_reading(t, c, 1, gain)
        assert old["burden"] > 0 and abs(old["ph"]) <= 1e-9 * max(1.0, abs(c["gas"][gain][2][1]))
        assert old["class"] == vf.CLASSES[3] and new["class"] == vf.WORSEN and new["paradox"] is None
    # The same readings with a perfusion that is not worse keep their class.
    c, t = _bundle([1.0] * 3, [0.20] * 3), _bundle([1.0 + 1e-7] * 3, [0.10] * 3)
    assert vf.reading(t, c, 1, 0.04)["class"] == rm.corrected_reading(t, c, 1, 0.04)["class"] == vf.CLASSES[1]


def test_the_burden_never_leaves_the_analysed_domain():
    """Review L-7: the rule is proved on 0 <= A < 24; the burden algebra keeps A >= 0 for any non-negative deficit
    (first-order clearance with tau >= 60, arrival burden max(0, 24 - HCO3)), and A >= 24 would fail SIMULATION."""
    patterns = ([0.0] * N, [0.8] * N, [max(0.0, 0.9 - 0.01 * m) for m in range(N)], [0.0 if m % 7 else 2.0 for m in range(N)])
    for case in vf.CASES:
        a0 = vf.ab.arrival_burden(case)
        assert a0 >= 0.0
        for b in vf.STEADY_BURDENS:
            for tau in vf.ACID_TAUS:
                for deficit in patterns:
                    assert min(vf.ab.burden_series(deficit, a0, b, tau)) >= 0.0


def test_the_admissibility_of_0_04_depends_on_the_provisional_reference():
    """Review L-2: 0.04 is at 96 % of 1/24; with the reference above 25 mEq/L it would be rejected, below 20 the gain
    0.05 would be admissible. The classes are conditional on HCO3_reference 24, which stays provisional."""
    assert rm.classify_gain(0.04, 25.0) == rm.ADMISSIBLE and rm.classify_gain(0.04, 25.5) == rm.REJECTED
    assert rm.classify_gain(0.05, 20.0) == rm.ADMISSIBLE and rm.classify_gain(0.03, 24.0) == rm.ADMISSIBLE


# P2K-5-4 / -5: the reuse, its certificates and the reached recomputation ---------------------------------------------------

def test_the_certificates_hold_and_the_algebra_is_exact():
    record = rm.p2k4_record()
    certified = rm.certificates(record)
    assert set(certified) == {"1", "1.1"} and all(c["holds"] for c in certified.values())
    for c in certified.values():
        assert all(c["certified_full"].values()) and all(c["recomputed_never_failed"].values()) and c["gain_invariant"]
        assert c["perfusion_worse_readings"] == 0 and c["rejecting_readings"] == 0 and c["readings"] > 0
    algebra = rm.record_algebra(record)
    for key, a in algebra.items():
        assert a["exact"] and a["kept"] + a["rejected"] == a["entering"] == record["demands"][key]["filter"]["survivors"]
        assert set(a["by_value"][rm.GAIN_DIM]) == {"0.03", "0.04"}


def test_the_reached_recomputation_mirrors_p2k4_on_synthetic_bloods():
    bloods, survivor, arrival = _bloods(), (0, 0, 0, 1, 0), vf.arrival_bits()
    full = vf.evaluate_parts(bloods, [survivor], 1.0, 0.5)
    reached = rm.reached_parts(bloods, [survivor], 1.0, 0.5)
    assert set(reached) == set(full)
    assert {k[0] for k, p in reached.items() if "summary" in p} == set(rm.REACHED_KINDS)
    a, b = vf.unit_rules(full, survivor, arrival), vf.unit_rules(reached, survivor, arrival)
    for name in vf.ORDER:
        if name not in rm.CERTIFIED_FULL:
            assert a[name] == b[name], name
    assert b["E"] == b["F"] == vf.FULL and a["SIMULATION"] & ~b["SIMULATION"] == 0
    # Seen reproduces P2K-4's observe for the tags it keeps, on the same parts and bitset.
    obs = vf.Observed()
    vf.observe(obs, full, [(survivor, vf.FULL)], _states(), bloods)
    seen = rm.Seen()
    rm.see(seen, reached, [(survivor, vf.FULL)])
    assert rm.seen_reproduced(seen.public(), obs.public()) == {"observables": True, "extreme_acidemia": True}
    # Pruned: only the admissible gains are seen, the extreme-acidemia survivors are the pruned bits.
    pruned = rm.Seen()
    rm.see(pruned, reached, [(survivor, vf.FULL & rm.ADMISSIBLE_MASK)])
    public = pruned.public()
    for case in vf.CASES:
        assert public["observables"][f"arrival_paco2 {case}"]["n"] == len(rm.RETAINED_GAINS)
    assert public["extreme_acidemia"]["survivors"] == (vf.FULL & rm.ADMISSIBLE_MASK).bit_count() == vf.N_LATENT // 2


def test_the_admissible_mask_keeps_exactly_the_two_gains():
    assert rm.ADMISSIBLE_MASK.bit_count() == vf.N_LATENT // 2
    for index in range(vf.N_LATENT):
        kept = bool(rm.ADMISSIBLE_MASK >> index & 1)
        assert kept == (vf.latent_values(index)[rm.GAIN_DIM] in rm.RETAINED_GAINS)


# P2K-5-9: the pruned support never calls the structurally narrowed gain constrained ----------------------------------------

def test_the_pruned_gain_is_structurally_bounded_never_well_constrained():
    gm = vf.DIM_MASKS[rm.GAIN_DIM]
    one = vf.mask(("drive_gain", "intrinsic_57m", "intrinsic_72f", "B", "tau"), (1, 0, 2, 1, 0))
    invariant = one & (gm[0] | gm[1])
    s = rm.pruned_support(invariant, [invariant])
    assert s[rm.GAIN_DIM]["class"] == "STRUCTURALLY_BOUNDED_NON_IDENTIFIABLE" and s[rm.GAIN_DIM]["values"] == [0.03, 0.04]
    assert not s[rm.GAIN_DIM]["filter_reads_it_within_support"]
    read = (one & gm[0]) | (vf.mask(("drive_gain",), (2,)) & gm[1])
    assert rm.pruned_support(read, [read])[rm.GAIN_DIM]["class"] == "STRUCTURALLY_BOUNDED_POORLY_IDENTIFIED"
    single = one & gm[0]
    assert rm.pruned_support(single, [single])[rm.GAIN_DIM]["class"] == "STRUCTURALLY_BOUNDED_PARTIALLY_CONSTRAINED"
    for bits in (invariant, read, single):
        assert rm.pruned_support(bits, [bits])[rm.GAIN_DIM]["class"] != "WELL_CONSTRAINED"
    # The other parameters read P2K-4's rule unchanged.
    assert s["B"] == vf.latent_support(invariant, [invariant])["B"]
    cross = rm.pruned_cross_demand({1.0: invariant, 1.1: invariant})
    assert cross["ROBUST_ACROSS_DEMAND"]["count"] == 2 and cross[rm.REJECTED]["count"] == vf.N_LATENT // 2
    assert sum(item["count"] for item in cross.values()) == vf.N_LATENT


# The verdict, the early stops, the scope ------------------------------------------------------------------------------------

def test_the_verdict_and_the_recommendation():
    good = {name: True for name in rm.CRITERIA}
    assert rm.verdict(good)["verdict"] == rm.CLOSED
    assert rm.recommendation(rm.verdict(good))["recommendation"] == "MOVE_FORWARD_TO_CONSCIOUSNESS"
    assert rm.verdict({**good, "region_nonempty": False})["verdict"] == rm.EMPTY
    blocked = rm.verdict({**good, "envelopes_hold": False})
    assert blocked["verdict"] == f"{rm.NOT_READY} - ENVELOPES_HOLD"
    assert rm.recommendation(blocked)["recommendation"] == "STOP_FOR_FACULTY_REVIEW"
    assert rm.verdict({"nothing_approved": True})["verdict"] == f"{rm.NOT_READY} - NOT_EVALUATED"


def test_a_changed_closed_file_stops_before_any_trajectory(monkeypatch):
    monkeypatch.setattr(rm, "closed_unchanged", lambda: {"clinical_core/derived.py": False})
    monkeypatch.setattr(rm.br, "pressure_tone_region", lambda *a, **k: pytest.fail("no region after a STOP"))
    out = rm.run()
    assert out["stopped"].startswith("a closed file changed") and out["verdict"]["checks"]["upstream_unchanged"] is False


def test_a_broken_certificate_stops_the_reuse_without_a_rerun(monkeypatch):
    monkeypatch.setattr(rm, "certificates", lambda record: {"1": {"holds": False}, "1.1": {"holds": True}})
    monkeypatch.setattr(rm.br, "pressure_tone_region", lambda *a, **k: pytest.fail("no region after a STOP"))
    out = rm.run()
    assert "exact reuse is invalid" in out["stopped"] and out["verdict"]["checks"]["reuse_exact"] is False
    assert out["verdict"]["checks"]["ph_monotone"] is True


def test_the_scope_adds_nothing_and_narrows_nothing_else():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("family_engine", "legacy_adapter", "snapshot("):
        assert forbidden not in source
    assert "nothing selected or approved" in rm.POLICY and "untreated pH never filters" in rm.POLICY
    assert rm.MIGRATION_GATE.startswith("MIGRATION_GATE_CLOSED")
    assert rm.STATUS["hco3_reference"].startswith("COMMON_REFERENCE_PROVISIONAL") and "not" in rm.STATUS["hco3_reference"]
    assert rm.STATUS["paco2_reference"].startswith("COMMON_REFERENCE_PROVISIONAL")
    assert {"saturation parameter", "CO2 time constant", "hypoxaemic-drive gain"} <= set(rm.NO_NEW_PARAMETERS)
    for family in ("COPD", "asthma", "opioid hypoventilation", "pneumonia", "pulmonary edema", "mechanical ventilation"):
        assert family in rm.STRATEGIC_NOTE
    # Every other support is P2K-4's; the frozen filter is untouched.
    assert vf.VALUES[rm.GAIN_DIM] == (0.03, 0.04, 0.05, 0.06) and rm.P2K4_GAINS == vf.VENTILATION_GAINS
    design = rm.p2k4_record()["design"]
    for dim in vf.DIMS:
        assert design["values"][dim] == list(vf.VALUES[dim])
    assert design["envelopes"] == json.loads(json.dumps(vf.ENVELOPES, default=str))
    assert hashlib.sha256((ROOT / "clinical_core" / "ventilation_filter.py").read_bytes()).hexdigest() == \
        rm.CLOSED_AT_P2K4["clinical_core/ventilation_filter.py"]


def test_the_n_inventory_names_existing_signals_and_adds_no_rule():
    assert {Channel.D, Channel.N, Channel.GLUCOSE} <= set(Channel)
    for name in ("effective_oxygen_deficit", "acute_deficit_signal", "respiration", "_perfusion"):
        assert callable(getattr(dv, name))
    assert callable(vn.ventilated_respiration)
    from clinical_core import integration
    assert "no module writes N yet" in integration.CHANNEL_BOUNDS[Channel.N][3]
    signals = {row["signal"] for row in rm.N_INVENTORY}
    assert {"effective oxygen deficit", "pH / acidemia", "PaCO2", "glucose", "oxygenation", "neurologic channel N"} <= \
        {s.split(" (")[0] for s in signals}
    assert "no rule" in rm.N_NOTE and "nothing reaches N today" in rm.N_NOTE


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2K5_respiratory_monotonicity.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2K5_CIERRE_MONOTONIA_RESPIRATORIA.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == rm.P2K4_DIGEST and "stopped" not in record
    assert record["design"] == _json(rm.design()) and record["closed_unchanged"] == _json(rm.closed_unchanged())
    assert record["analytic"] == _json(rm.analytic_proof()) and record["semantics"] == _json(rm.semantics())
    assert record["mapping"] == _json(rm.mapping_check()) and record["probes"] == _json(rm.probes())
    p2k4 = rm.p2k4_record()
    assert record["equivalence"]["certificates"] == _json(rm.certificates(p2k4))
    assert record["equivalence"]["p2k4_freeze_digest"] is True and record["algebra"] == _json(rm.record_algebra(p2k4))


def test_the_verdict_closes_the_gi_respiratory_domain(record):
    v = record["verdict"]
    assert v["verdict"] == rm.CLOSED and not v["failing"] and not v["not_evaluated"]
    assert set(v["checks"]) == set(rm.CRITERIA) and all(v["checks"].values())
    assert record["recommendation"]["recommendation"] == "MOVE_FORWARD_TO_CONSCIOUSNESS"
    assert all(record["region_unchanged"].values()) and set(record["non_regression"]) == set(rm.DOMAINS)
    assert all(d["unchanged"] for d in record["non_regression"].values())


def test_the_pruning_is_the_exact_gain_subset_of_p2k4(record):
    p2k4 = rm.p2k4_record()
    for key, d in record["demands"].items():
        f = p2k4["demands"][key]["filter"]
        assert d["reproduced"] == {"tally": True, "observables": True, "extreme_acidemia": True} and d["algebra_equal"]
        assert d["entering"] == f["survivors"] and d["rejected_by_monotonicity"] + d["survivors"] == d["entering"]
        assert 2 * d["survivors"] == d["entering"] and d["failed_by_semantic_correction"] == 0
        assert d["upstream_units_with_survivors"] == d["upstream_units"] == f["upstream_units"]
        assert sum(t["survivors"] for t in d["by_tone_gain"].values()) == d["survivors"]
        assert sum(t["entering"] for t in d["by_tone_gain"].values()) == d["entering"]
        assert d["latent_combinations"] == f["latent_survivors"] // 2
    cross = record["cross_demand"]
    assert sum(item["count"] for item in cross.values()) == vf.N_LATENT
    assert cross[rm.REJECTED]["count"] == vf.N_LATENT // 2
    assert cross["DEMAND_1_0_ONLY"]["count"] == cross["DEMAND_1_1_ONLY"]["count"] == 0
    assert cross[rm.REJECTED]["support"]["ventilation_gain"] == [0.05, 0.06]
    assert cross["ROBUST_ACROSS_DEMAND"]["support"]["ventilation_gain"] == [0.03, 0.04]


def test_the_latent_uncertainty_is_kept(record):
    p2k4 = rm.p2k4_record()
    for key, d in record["demands"].items():
        s = d["latent_support"]
        assert s["ventilation_gain"]["class"] == "STRUCTURALLY_BOUNDED_NON_IDENTIFIABLE"
        assert s["ventilation_gain"]["values"] == [0.03, 0.04]
        for dim in vf.DIMS:
            if dim != "ventilation_gain":
                old = p2k4["demands"][key]["latent_support"][dim]
                assert s[dim]["values"] == old["values"] and s[dim]["class"] == old["class"] != "WELL_CONSTRAINED"


def test_every_pruned_survivor_observable_lies_in_its_envelope_and_ph_never_alkalinizes(record):
    e, zero = vf.ENVELOPES, rm.closed_form_ph(0.0, 0.03)
    for d in record["demands"].values():
        o = d["observed"]["observables"]
        within = lambda name, case, bounds: bounds[0] <= o[f"{name} {case}"]["low"] <= o[f"{name} {case}"]["high"] <= \
            bounds[1]
        for case, a, g in ((C57, "A", "G"), (C72, "B", "G2")):
            assert within("untreated_rr_120", case, e[a]["rr"]) and within("definitive_rr_120", case, e[g]["rr"])
            assert within("untreated_paco2_120", case, e["C" if case == C57 else "D"]["paco2"])
            assert within("definitive_paco2_120", case, e["H"]["paco2"]) and within("definitive_ph_120", case, e["H"]["ph"])
            assert within("residual_rr_above_intrinsic_120", case, e["I"]["residual"][case])
            assert within("arrival_rr", case, vf.ARRIVAL_RR[case]) and within("arrival_paco2", case, vf.ARRIVAL_PACO2[case])
            for name in ("arrival_ph_diagnostic", "untreated_ph_120", "untreated_ph_lowest_0_120", "definitive_ph_120"):
                assert o[f"{name} {case}"]["high"] < zero, (name, case)


def test_untreated_extreme_acidemia_is_carried_never_filtered(record):
    p2k4 = rm.p2k4_record()
    for key, d in record["demands"].items():
        x, old = d["observed"]["extreme_acidemia"], p2k4["demands"][key]["observed"]["extreme_acidemia"]
        # Review M-3: the run's criterion only checks that the region keeps its own rows; that every P2K-4 flagged row
        # is still there is the record's observation, pinned here.
        assert x["survivors"] == d["survivors"] and x["flagged"] == old["flagged"] and x["by_case"] == old["by_case"]
        assert x["lowest"] == old["lowest"]
    x = record["demands"]["1.1"]["observed"]["extreme_acidemia"]
    assert x["flagged"] > 0 and x["by_case"][C72] == 0 and x["lowest"]["flag"] == "CONSCIOUSNESS_COLLAPSE_REVIEW"


def test_r3_r4_is_carried_and_the_efficiency_is_recorded(record):
    for r in record["r3r4"].values():
        assert not r["bug"] and r["status"] == vf.R3R4_CLASSES[0]
    e = record["efficiency"]
    assert e["cartesian_sweep"] is False and e["legacy_read"] is False
    assert e["trajectories_not_rebuilt"] > e["reached_trajectories"] > 0
    assert e["analytic_rejections"] == sum(d["rejected_by_monotonicity"] for d in record["demands"].values())


def test_the_document_is_generated_from_the_record():
    from clinical_core import respiratory_monotonicity_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(data)) == document, name
    assert "GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE" in document and "MOVE_FORWARD_TO_CONSCIOUSNESS" in document
