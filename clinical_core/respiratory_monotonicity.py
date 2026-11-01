"""Phase 2 shadow core, P2K-5: the final respiratory monotonicity closure for the current GI calibration.

    python -m clinical_core.respiratory_monotonicity --digest
    python -m clinical_core.respiratory_monotonicity --design
    python -m clinical_core.respiratory_monotonicity --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-11-01, recorded in FACULTY). P2K-4 found that with the linear ventilation
recruitment of P2K-3,

    HCO3 = HCO3_reference - A,  capacity = 1 + g_v x A,  PaCO2 = PaCO2_reference / capacity,
    pH = 6.1 + log10(HCO3 / (0.03 x PaCO2)),

the gains 0.05 and 0.06 make pH rise with the metabolic acid burden A at low A: compensation reversing the metabolic
load. The faculty requires pH non-increasing in A with the other physiology fixed. This module proves the rule
analytically (the sign of d pH / dA is that of a polynomial linear in A, so its value at A = 0 decides the whole domain:
g_v <= 1 / HCO3_reference), classifies the four P2K-4 gains by that rule alone, corrects the treatment-response signal so
that a pH rise beside a higher burden is never read as respiratory improvement, and then filters P2K-4's region by the
gain alone. P2K-4's outcomes are reused by exact filtering: its frozen code, its pinned record and its zero-failure and
gain-invariance certificates; only what the change reaches is recomputed (the R1 / R4 trajectories that decide the
survivors, the extreme acidemia and the A-I observables). No new respiratory parameter, functional form, envelope,
window or support value; nothing selected or approved; untreated pH never filters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

from . import acid_base as ab
from . import baroreflex as br
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import lactate_rebuild as lr
from . import vascular_tone as vt
from . import ventilation_filter as vf
from . import ventilation_surface as vs

DECIDED = "2026-11-01"
REVISION = "P2K-5"
ROOT = vf.ROOT
CASES = vf.CASES
C57, C72 = vf.C57, vf.C72
P2K4_RECORD = ROOT / "docs" / "revision" / "P2K4_ventilation_filter.json"
#: The P2K-4 freeze (46d009a) and its committed record (b6908e5), pinned byte for byte.
P2K4_DIGEST = "638b64f699ddd53afda7f2e11eebf77e418a28789da8c47e667343738c642773"
P2K4_RECORD_SHA = "faa5b3228dd5fccf3b41c765d5591bf02e04909f2f3562c52b576b01c4cfeb2f"


# 1. The faculty decisions, recorded --------------------------------------------------------------------------------------

FACULTY = {
    "decided": DECIDED,
    "closed": "P2K-4 accepted and closed; RR_VENTILATION_OBSERVABLE_FILTER_SATISFIED accepted and MOVE_FORWARD agreed; "
              "one structural respiratory contradiction to close before consciousness, collapse, GI migration or a "
              "second family",
    "goal": "remove the paradox in which a higher metabolic acid burden raises pH at low burden because ventilation "
            "recruitment is too strong; then, with a non-empty coherent region, close the respiratory domain for the "
            "current GI calibration",
    "priority": "a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good "
                "enough to migrate other families; not identifying every latent, a tighter fit of two GI cases or one "
                "best candidate",
    "rule": "for increasing metabolic acid burden A, other physiology fixed, pH must be non-increasing: compensation may "
            "reduce the fall in pH, never reverse the metabolic load into alkalinization",
    "analytic": "pH is log[(HCO3_reference - A)(1 + g_v A)] up to constants; at A = 0 a non-increasing pH requires "
                "g_v <= 1 / HCO3_reference = 1/24; 0.03 and 0.04 STRUCTURALLY_ADMISSIBLE_PRIMARY_SUPPORT, 0.05 and 0.06 "
                "REJECTED_BY_ACID_BASE_MONOTONICITY, by the analysis, never by counts or fit",
    "no_saturation": "no saturating recruitment and no new parameter now: the support already holds admissible values; "
                     "a saturating form may be reconsidered if a second respiratory family shows the linear form is "
                     "insufficient",
    "treatment": "a higher burden with a higher pH produced by excessive compensation is never respiratory improvement; "
                 "no new numeric treatment threshold; once 0.05 / 0.06 are removed the condition is unreachable",
    "retained": "intrinsic RR 12 / 16 / 20 per patient, the P2K-4 drive gains, B 13.4 / 19.4 / 28, tau 60 / 120 / 240, "
                "ventilation gain 0.03 / 0.04, HCO3_reference 24 and PaCO2_reference 40 provisional, arrival RR and "
                "PaCO2 +/- 3, BASELINE_RELATIVE demand; nothing else narrowed",
    "reuse": "P2K-4's survivors filtered by the gain alone when the subset is exact; never the full bitset pipeline again",
    "extreme_acidemia": "untreated pH < 7.00 kept, never filtered: CONSCIOUSNESS_COLLAPSE_REVIEW, carried forward",
    "r3_r4": "PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE retained while the underlying states stay distinct",
    "identifiability": "the gain narrowed by a structural rule is not WELL_CONSTRAINED; no choice of 0.03 or 0.04",
    "exit": "non-empty, pH monotone, A-I held, treatment responses coherent, R3 / R4 physiological, upstream unchanged: "
            "GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE and MOVE_FORWARD_TO_CONSCIOUSNESS; the remaining broad "
            "latents are propagated, never a reason for another respiratory cycle",
    "early_stop": "an empty region STOPs: no gain restored, no envelope widened, no HCO3 or PaCO2 reference, arrival "
                  "tolerance, B or tau changed, no legacy fitting",
    "scope": "shadow only; no runtime integration, migration, parameter approval, consciousness or collapse; the "
             "upstream physiology reused, never reopened",
}
STATUS = {"hco3_reference": "COMMON_REFERENCE_PROVISIONAL 24 mEq/L: the rule's critical gain is read from it; not "
                            "approved as physiology",
          "paco2_reference": "COMMON_REFERENCE_PROVISIONAL 40 mmHg: a constant factor of PaCO2, it never enters the rule",
          "latent": "EXPLORATORY (intrinsic RR, drive gain, B, tau, ventilation gain within 0.03 / 0.04)",
          "approved": "none FACULTY_APPROVED"}
NO_NEW_PARAMETERS = ("saturation parameter", "explicit tidal volume", "dead-space state", "fatigue state",
                     "mechanics state", "CO2 time constant", "hypoxaemic-drive gain", "saturating recruitment form")
STRATEGIC_NOTE = (
    "The current GI respiratory model is a MINIMAL spontaneous-breathing acid-compensation model. It does not yet "
    "establish general respiratory physiology for COPD, asthma, opioid hypoventilation, pneumonia, pulmonary edema or "
    "mechanical ventilation; those families will test whether the current RR / W / acid-base decomposition generalizes. "
    "Their physiology is not added preemptively.")


# 2. The analytic monotonicity rule (P2K-5-1) -----------------------------------------------------------------------------

HCO3_REFERENCE = vs.HCO3_REFERENCE
PACO2_REFERENCE = vs.PACO2_REFERENCE
P2K4_GAINS = vf.VENTILATION_GAINS
ADMISSIBLE = "STRUCTURALLY_ADMISSIBLE_PRIMARY_SUPPORT"
REJECTED = "REJECTED_BY_ACID_BASE_MONOTONICITY"
EQUATION = ("pH(A) = pK + log10[(HCO3_reference - A) x (1 + g_v x A) / (s x PaCO2_reference)], pK 6.1, s 0.03, "
            "for 0 <= A < HCO3_reference (the P2K-3 mapping at efficiency 1 and the baseline demand)")
INEQUALITY = (
    "d pH / dA = (1 / ln 10) x [g_v / (1 + g_v A) - 1 / (HCO3_reference - A)] = (1 / ln 10) x N(A) / "
    "[(1 + g_v A)(HCO3_reference - A)], with N(A) = (g_v x HCO3_reference - 1) - 2 g_v x A. On 0 <= A < "
    "HCO3_reference the denominator is positive (g_v >= 0), so the sign of the slope is the sign of N. N is linear in A "
    "with slope -2 g_v <= 0, so its largest value on the domain is N(0) = g_v x HCO3_reference - 1. pH is non-increasing "
    "on the whole domain if and only if N(0) <= 0, i.e. g_v <= 1 / HCO3_reference (strictly decreasing when g_v < 1 / "
    "HCO3_reference). When g_v > 1 / HCO3_reference, pH rises on 0 <= A < A* = (g_v x HCO3_reference - 1) / (2 g_v). "
    "Efficiency and demand ratio multiply PaCO2 by constants independent of A and drop out of the derivative.")
RULE_SCOPE = (
    "The bicarbonate at zero burden is the case's authored HCO3 plus its arrival burden: HCO3_reference when the authored "
    "HCO3 is at or below it (both GI cases). A family authored above the reference would carry 1 / its own zero-burden "
    "bicarbonate as the critical gain; that is a generalization question, not decided here.")


def exact(value) -> Fraction:
    """The value as written (0.04 -> 1/25), never its binary float."""
    return Fraction(str(value))


def critical_gain(hco3_reference: float = HCO3_REFERENCE) -> Fraction:
    return 1 / exact(hco3_reference)


def numerator(gain: float, hco3_reference: float = HCO3_REFERENCE) -> tuple:
    """N(A) = c + s x A, exactly: (g_v x HCO3_reference - 1, -2 g_v)."""
    g, h = exact(gain), exact(hco3_reference)
    return g * h - 1, -2 * g


def monotone(gain: float, hco3_reference: float = HCO3_REFERENCE) -> bool:
    """Non-increasing pH on 0 <= A < HCO3_reference: N's largest value, N(0), is not positive."""
    constant, slope = numerator(gain, hco3_reference)
    if slope > 0:
        raise ValueError("a negative ventilation gain is outside the candidate's domain")
    return constant <= 0


def strictly_decreasing(gain: float, hco3_reference: float = HCO3_REFERENCE) -> bool:
    """N < 0 on the whole domain except possibly A = 0 (where N(0) = 0 at the critical gain itself)."""
    constant, slope = numerator(gain, hco3_reference)
    return constant < 0 or (constant == 0 and slope < 0)


def violation_interval(gain: float, hco3_reference: float = HCO3_REFERENCE):
    """None when monotone, else [0, A*) exactly, A* = (g_v x HCO3_reference - 1) / (2 g_v), where pH rises."""
    constant, slope = numerator(gain, hco3_reference)
    if constant <= 0:
        return None
    return Fraction(0), constant / -slope


def closed_form_ph(burden: float, gain: float, hco3_reference: float = HCO3_REFERENCE,
                   paco2_reference: float = PACO2_REFERENCE) -> float:
    return dv.CARBONIC_PK + math.log10((hco3_reference - burden) * (1.0 + gain * burden)
                                       / (dv.CO2_SOLUBILITY * paco2_reference))


def slope(burden: float, gain: float, hco3_reference: float = HCO3_REFERENCE) -> float:
    return (gain / (1.0 + gain * burden) - 1.0 / (hco3_reference - burden)) / math.log(10.0)


def classify_gain(gain: float, hco3_reference: float = HCO3_REFERENCE) -> str:
    """The analytic rule only: no count, trajectory or fit is read."""
    return ADMISSIBLE if monotone(gain, hco3_reference) else REJECTED


GAIN_CLASSES = {f"{g:g}": classify_gain(g) for g in P2K4_GAINS}
RETAINED_GAINS = tuple(g for g in P2K4_GAINS if classify_gain(g) == ADMISSIBLE)
REJECTED_GAINS = tuple(g for g in P2K4_GAINS if classify_gain(g) == REJECTED)
#: Outside P2K-4's support already (P2K-3 / P2K-4 excluded it on the arrival windows); the rule also rejects it.
PREVIOUSLY_EXCLUDED = {"0.08": classify_gain(0.08)}


def gain_row(gain: float, hco3_reference: float = HCO3_REFERENCE) -> dict:
    constant, slope_ = numerator(gain, hco3_reference)
    interval = violation_interval(gain, hco3_reference)
    row = {"gain": gain, "exact": str(exact(gain)), "n0": str(constant), "n_slope": str(slope_),
           "n0_float": float(constant), "monotone": monotone(gain, hco3_reference),
           "strictly_decreasing": strictly_decreasing(gain, hco3_reference), "class": classify_gain(gain, hco3_reference),
           "slope_at_0": slope(0.0, gain, hco3_reference), "rising_interval": None, "peak": None}
    if interval is not None:
        top = float(interval[1])
        row["rising_interval"] = [0.0, top]
        row["rising_interval_exact"] = [str(interval[0]), str(interval[1])]
        row["peak"] = {"burden": top, "ph": closed_form_ph(top, gain, hco3_reference),
                       "ph_at_0": closed_form_ph(0.0, gain, hco3_reference)}
    return row


def analytic_proof() -> dict:
    return {"equation": EQUATION, "inequality": INEQUALITY, "scope": RULE_SCOPE,
            "hco3_reference": HCO3_REFERENCE, "paco2_reference": PACO2_REFERENCE,
            "critical_gain": str(critical_gain()), "critical_gain_float": float(critical_gain()),
            "gains": {f"{g:g}": gain_row(g) for g in P2K4_GAINS + (0.08,)},
            "classes": GAIN_CLASSES, "retained": list(RETAINED_GAINS), "rejected": list(REJECTED_GAINS),
            "previously_excluded": PREVIOUSLY_EXCLUDED}


# 3. The executable mapping is the analysed one; the synthetic probes (P2K-5-2) ---------------------------------------------

#: Representative burdens (mEq/L) over the valid domain 0 <= A < 24, with the low-burden region the rule decides; each
#: case's arrival burden is added.
PROBE_BURDENS = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0,
                 22.0, 23.0)
MAPPING_TOLERANCE = 1e-12


def zero_burden_bicarbonate(case: str) -> float:
    """The bicarbonate the executable mapping gives at A = 0 (vs.hco3_series: authored HCO3 - (A - arrival burden))."""
    return ab.authored_gas(case)["hco3"] + ab.arrival_burden(case)


def _grid(case: str) -> list:
    return sorted(set(PROBE_BURDENS) | {ab.arrival_burden(case)})


def mapping_check() -> dict:
    """The filter's own HCO3 / PaCO2 / pH series (ventilation_surface.hco3_series and gas_series, the functions P2K-4
    read) equal the analysed closed form on the probe grid, for both cases and every P2K-4 gain."""
    out = {}
    for case in CASES:
        burdens = _grid(case)
        hco3 = vs.hco3_series(burdens, case)
        gas = {}
        for gain in P2K4_GAINS:
            _, paco2, ph = vs.gas_series(burdens, hco3, [True] * len(burdens), gain)
            gas[f"{gain:g}"] = {
                "ph": max(abs(p - closed_form_ph(a, gain)) for a, p in zip(burdens, ph)),
                "paco2": max(abs(q - PACO2_REFERENCE / (1.0 + gain * a)) for a, q in zip(burdens, paco2))}
        hco3_error = max(abs(c - (HCO3_REFERENCE - a)) for a, c in zip(burdens, hco3))
        zero = zero_burden_bicarbonate(case)
        out[case] = {"arrival_burden": ab.arrival_burden(case), "authored_hco3": ab.authored_gas(case)["hco3"],
                     "zero_burden_bicarbonate": zero, "hco3_error": hco3_error, "gas_error": gas,
                     "reference_is_zero_burden": abs(zero - HCO3_REFERENCE) <= MAPPING_TOLERANCE,
                     "equal": hco3_error <= MAPPING_TOLERANCE and all(
                         e <= MAPPING_TOLERANCE for row in gas.values() for e in row.values())}
    return out


def probe(case: str, gain: float) -> dict:
    """One case and gain over the probe grid, through the executable series: the direction of each step."""
    burdens = _grid(case)
    hco3 = vs.hco3_series(burdens, case)
    _, paco2, ph = vs.gas_series(burdens, hco3, [True] * len(burdens), gain)
    steps = range(len(burdens) - 1)
    rising = [[burdens[k], burdens[k + 1]] for k in steps if ph[k + 1] > ph[k]]
    return {"burdens": burdens, "hco3": hco3, "paco2": paco2, "ph": ph,
            "hco3_falls": all(hco3[k + 1] < hco3[k] for k in steps),
            "paco2_falls": all(paco2[k + 1] < paco2[k] for k in steps),
            "ph_non_increasing": not rising, "ph_rising_steps": rising,
            "ph_change_0_to_arrival": ph[burdens.index(ab.arrival_burden(case))] - ph[0]}


def probes() -> dict:
    rows = {case: {f"{gain:g}": probe(case, gain) for gain in P2K4_GAINS} for case in CASES}
    admissible = all(rows[case][f"{g:g}"]["ph_non_increasing"] and rows[case][f"{g:g}"]["hco3_falls"]
                     for case in CASES for g in RETAINED_GAINS)
    # Each rejected gain shows a rising step, and every rising step starts inside its analytic interval [0, A*).
    shown = all(rows[case][f"{g:g}"]["ph_rising_steps"]
                and all(low < float(violation_interval(g)[1]) for low, _ in rows[case][f"{g:g}"]["ph_rising_steps"])
                for case in CASES for g in REJECTED_GAINS)
    return {"rows": rows, "admissible_non_increasing": admissible, "rejected_rise_at_low_burden": shown,
            "paco2_falls_with_burden": all(r["paco2_falls"] for c in rows.values() for r in c.values())}


# 4. The treatment-response signal, corrected (P2K-5-3; P2K-4 review M1 / M2) -------------------------------------------------

PARADOX_HIGHER = "PH_RISES_WITH_HIGHER_ACID_BURDEN"
PARADOX_LOWER = "PH_FALLS_WITH_LOWER_ACID_BURDEN"
SEMANTIC_RULE = (
    "Frozen before any recount. The respiratory signal of a matched reading follows the metabolic acid load: a higher "
    "burden is respiratory worsening whatever the pH does (a pH rise beside it is excessive compensation, flagged "
    "PH_RISES_WITH_HIGHER_ACID_BURDEN, never improvement); a lower burden is improvement only when pH is also higher (a "
    "pH fall beside it is flagged PH_FALLS_WITH_LOWER_ACID_BURDEN and is not improvement); no burden change is no "
    "respiratory change. Perfusion, the classes, the rejecting classes (RESPIRATORY_AND_PERFUSION_WORSEN and a treated "
    "arrest), the comparators, the minutes and P2J-3's no-change tolerance (1e-9 of the scale) are P2K-4's; no numeric "
    "threshold is added. Against P2K-4 the only class that moves is RESPIRATORY_UNCHANGED_WITH_PERFUSION_WORSENING with "
    "a higher burden, which becomes RESPIRATORY_AND_PERFUSION_WORSEN (M1: the conjunction could not fire when "
    "overcompensation raised pH). M2: the pH direction is now read, through the paradox flags.")
#: The classes with a worse perfusion: the only ones the correction can move (to the rejecting class).
PERFUSION_WORSE = (vf.CLASSES[2], vf.CLASSES[3], vf.WORSEN)
#: Rounding of a computed pH difference (|pH| < 8, a few ulp) is far below P2J-3's tolerance floor (1e-9 x max(1, scale)).
FLOAT_MARGIN = 1e-12
TOLERANCE_FLOOR = 1e-9


def corrected_signal(d_burden: float, d_ph: float, burden_scale: float, ph_scale: float) -> tuple:
    """(respiratory signal, paradox flag or None)."""
    lower, higher_ph = -vf._sign(d_burden, burden_scale), vf._sign(d_ph, ph_scale)
    if lower < 0:
        return -1, (PARADOX_HIGHER if higher_ph > 0 else None)
    if lower > 0:
        if higher_ph > 0:
            return 1, None
        return 0, (PARADOX_LOWER if higher_ph < 0 else None)
    return 0, None


def corrected_reading(t: dict, c: dict, minute: int, gain: float) -> dict:
    """P2K-4's reading of one comparison minute with the corrected respiratory signal (arrests and impossible values as
    P2K-4 classes them)."""
    out = vf.reading(t, c, minute, gain)
    if "burden_t" not in out:
        out["paradox"] = None
        return out
    signal, paradox = corrected_signal(out["burden"], out["ph"], c["burden"][minute], c["gas"][gain][2][minute])
    out.update({"class": vf.classify(out["perfusion"], signal), "respiratory": signal, "paradox": paradox})
    return out


def transitions() -> list:
    """Every (perfusion, burden, pH) direction: P2K-4's class and the corrected one."""
    rows = []
    for perfusion in (-1, 0, 1):
        for burden in (-1, 0, 1):
            for ph in (-1, 0, 1):
                old = vf.classify(perfusion, vf.respiratory_signal(float(burden), float(ph), 1.0, 1.0))
                signal, paradox = corrected_signal(float(burden), float(ph), 1.0, 1.0)
                new = vf.classify(perfusion, signal)
                rows.append({"perfusion": perfusion, "burden": burden, "ph": ph, "p2k4": old, "p2k5": new,
                             "paradox": paradox, "changed": old != new,
                             "rejecting": [old in vf.REJECTING, new in vf.REJECTING]})
    return rows


def semantics() -> dict:
    rows = transitions()
    changed = [r for r in rows if r["changed"]]
    return {"rule": SEMANTIC_RULE, "transitions": rows, "changed": changed,
            "only_perfusion_worse_higher_burden": all(r["perfusion"] < 0 and r["burden"] > 0
                                                      and r["p2k4"] == vf.CLASSES[3] and r["p2k5"] == vf.WORSEN
                                                      for r in changed) and bool(changed),
            "never_unrejects": not any(r["rejecting"][0] and not r["rejecting"][1] for r in rows),
            "paradox_directions": sorted({(r["burden"], r["ph"]) for r in rows if r["paradox"]}),
            "rejecting": list(vf.REJECTING), "classes": list(vf.CLASSES) + [PARADOX_HIGHER, PARADOX_LOWER]}


def paradox_unreachable() -> dict:
    """For a retained gain pH is strictly decreasing in the burden (section 2), and both arms of a reading share the gain
    and the case: a burden difference beyond tolerance has a pH difference of the opposite sign or within tolerance, never
    the same sign beyond it (rounding is below FLOAT_MARGIN, far under the tolerance floor). So neither paradox flag can
    be raised, and the corrected and P2K-4 signals differ only where a pH difference is within tolerance."""
    return {f"{g:g}": strictly_decreasing(g) and FLOAT_MARGIN < TOLERANCE_FLOOR for g in RETAINED_GAINS}


# 5. Closure and dependency equivalence: P2K-4 at b6908e5 -------------------------------------------------------------------

CLOSED_AT_P2K4 = {**vf.CLOSED_AT_P2K3,
                  "clinical_core/ventilation_filter.py":
                      "9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9"}
OWN = ("clinical_core/respiratory_monotonicity.py",)
REPORT = "clinical_core/respiratory_monotonicity_report.py"
#: The two tuple-only files at P2K-4 (b6908e5): P2K-5 adds its modules to their tuples, nothing else.
TUPLE_AT_P2K4 = {"clinical_core/lactate_slice.py": "5b12c7c6a46f09089eb3f0b7b776762dc31491ebb3a23e0e031628f9bc8378da",
                 "clinical_core/decision_pack.py": "8812ec2e07dba978a2253d8da1fccaa79a0146cd07e05a78d8ad30ce4604486d"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}


def closed_unchanged() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in CLOSED_AT_P2K4.items()}


def p2k4_sources(sources: dict) -> dict:
    """A P2K-4 dependency map: P2K-5's module removed, the two tuple-only files at their P2K-4 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2K4.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def p2k4_freeze_digest() -> str:
    """ventilation_filter.freeze_digest's own formula on the sources P2K-4 froze: the rule digest of the reused code."""
    text = json.dumps({"revision": vf.REVISION, "p2k3": hashlib.sha256(vf.P2K3_RECORD.read_bytes()).hexdigest(),
                       "design": vf.design(), "sources": p2k4_sources(bf.freeze_sources())}, sort_keys=True,
                      default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def p2k4_record() -> dict:
    data = P2K4_RECORD.read_bytes()
    record = json.loads(data.decode("utf-8"))
    if hashlib.sha256(data).hexdigest() != P2K4_RECORD_SHA or record["freeze_digest"] != P2K4_DIGEST \
            or record["verdict"]["verdict"] != vf.READY:
        raise AssertionError("the P2K-4 record is not the committed one")
    return record


# 6. The reuse certificates, read from P2K-4's record -----------------------------------------------------------------------

#: Rules P2K-5 does not recompute: certified FULL for every upstream unit by P2K-4's zero any-failure counts (a rule's
#: any-failure count is the sum over units of its failing bits, so zero means every unit's bitset is FULL).
CERTIFIED_FULL = ("SIMULATION", "E", "F")
#: Rules P2K-5 recomputes on the reached trajectories although they never failed (a consistency check).
RECOMPUTED_NEVER_FAILED = ("ARRIVAL_PACO2", "C", "D", "H_PACO2", "H_PH")
GAIN_DIM = "ventilation_gain"
GAIN_INDEX = {g: vf.VALUES[GAIN_DIM].index(g) for g in P2K4_GAINS}
ADMISSIBLE_MASK = 0
for _g in RETAINED_GAINS:
    ADMISSIBLE_MASK |= vf.DIM_MASKS[GAIN_DIM][GAIN_INDEX[_g]]
del _g
REUSE_RULE = (
    "Frozen. P2K-5's region is P2K-4's survivors with the ventilation gain in the admissible support. The reuse is exact "
    "when (1) the closed files keep their P2K-4 bytes and P2K-4's freeze digest recomputes (the rule digest of the reused "
    "code), (2) the P2K-4 record is the pinned one, (3) its certificates hold at both demands: SIMULATION, E and F never "
    "failed (so their bitsets are FULL for every unit), the ventilation gain is NON_IDENTIFIABLE with the filter not "
    "reading it (every unit's survivors identical at every gain), no survivor reading has a worse perfusion (the only "
    "class the corrected signal can move), R3 / R4 has no state-collapse bug; and (4) the reached recomputation, P2K-4's "
    "own functions on the R1 / R4 trajectories with the certified rules FULL, reproduces P2K-4's tally exactly at every "
    "demand (candidate identity). The pruned region is then those survivors masked by the gain; nothing else is rerun.")


def _classes_total(observed: dict, names) -> int:
    return sum(counts.get(c, 0) for counts in observed["classes"].values() for c in names)


def certificates(record: dict) -> dict:
    out = {}
    for factor, data in sorted(record["demands"].items()):
        f, support, observed = data["filter"], data["latent_support"][GAIN_DIM], data["observed"]
        out[factor] = {
            "certified_full": {name: f["any_failure"][name] == 0 for name in CERTIFIED_FULL},
            "recomputed_never_failed": {name: f["any_failure"][name] == 0 for name in RECOMPUTED_NEVER_FAILED},
            "gain_invariant": support["class"] == "NON_IDENTIFIABLE" and support["filter_reads_it"] is False
            and support["values"] == list(P2K4_GAINS),
            "perfusion_worse_readings": _classes_total(observed, PERFUSION_WORSE),
            "readings": _classes_total(observed, vf.CLASSES),
            "rejecting_readings": _classes_total(observed, vf.REJECTING),
            "r3r4_bug": observed["r3r4"]["bug"]}
        row = out[factor]
        row["holds"] = all(row["certified_full"].values()) and row["gain_invariant"] and \
            row["perfusion_worse_readings"] == 0 and row["rejecting_readings"] == 0 and not row["r3r4_bug"]
    return out


def record_algebra(record: dict) -> dict:
    """The pruned counts from P2K-4's record alone, by the gain invariance: every unit's survivors are the same at each of
    the four gains, so the admissible two keep exactly half of every count, per value of every other parameter."""
    share = Fraction(len(RETAINED_GAINS), len(P2K4_GAINS))
    out = {}
    for factor, data in sorted(record["demands"].items()):
        f, support = data["filter"], data["latent_support"]
        kept = f["survivors"] * share
        out[factor] = {"entering": f["survivors"], "kept": int(kept), "exact": kept.denominator == 1,
                       "rejected": f["survivors"] - int(kept),
                       "by_tone_gain": {t: int(row["survivors"] * share) for t, row in sorted(f["by_tone_gain"].items())},
                       "latent_combinations": int(f["latent_survivors"] * share),
                       "by_value": {dim: {v: int(n * share) if dim != GAIN_DIM else n
                                          for v, n in s["latent_combinations_by_value"].items()
                                          if dim != GAIN_DIM or float(v) in RETAINED_GAINS}
                                    for dim, s in support.items()},
                       "classes_other": {dim: s["class"] for dim, s in support.items() if dim != GAIN_DIM}}
    return out


# 7. The reached recomputation: P2K-4's own functions on the R1 / R4 trajectories ------------------------------------------

REACHED_KINDS = ("P1", "P4")
STUBBED_KINDS = ("P2", "P3", "CF1", "CF2", vf.NO_PRBC)
REACH_RULE = (
    "Frozen. Only what the pruning reaches is rebuilt: the R1 and R4 trajectories of every P2J-3 upstream survivor (R1 "
    "decides A-D and the extreme acidemia, R4 G, G2, H and I), by P2K-4's trajectory and summarize; their rule bitsets by "
    "P2K-4's unit_rules, with the certified rules (SIMULATION of the other trajectories, E, F) FULL. The crystalloid, "
    "red-cell, counterfactual and no-red-cell trajectories, the no-red-cell blood runs, the R3 / R4 core states, the "
    "P2K-3 reconstruction and the comparator validation are not rerun.")


def _stub() -> dict:
    """A trajectory P2K-5 does not rebuild: the bitsets P2K-4's record certifies FULL for every unit."""
    return {"bits": {"SIM": vf.FULL, "E": vf.FULL, f"F {vf.NO_PRBC}": vf.FULL, "F CF1": vf.FULL, "F CF2": vf.FULL}}


def reached_parts(bloods: dict, survivors: list, factor: float, gain: float) -> dict:
    """ventilation_filter.evaluate_parts restricted to R1 and R4: the same keys, trajectories and summaries."""
    parts = {}
    need = vf.needed(survivors)
    for (case, level, i), ds in sorted(need["P1"].items(), key=str):
        p1 = vf.trajectory(bloods, ("P1", case, i), level, factor, gain)
        parts[("P1", case, level, i)] = {"summary": vf.summarize(p1["bundles"], p1["structural"])}
        for d in sorted(ds):
            parts[("P2", case, level, (i, d))] = _stub()
    for case, level, q in sorted(need["Q"], key=str):
        p4 = vf.trajectory(bloods, ("P4", case, q), level, factor, gain)
        part = {"summary": vf.summarize(p4["bundles"], p4["structural"])}
        part["bits"] = {name: vf.FULL for name in ("F CF1", "F CF2")}
        parts[("P4", case, level, q)] = part
        for kind in ("P3", "CF1", "CF2", vf.NO_PRBC):
            parts[(kind, case, level, q)] = _stub()
    return parts


class Seen:
    """Per demand: the observables of one bitset per unit over unique (trajectory, latent sub-combination) entries, the
    extreme acidemia and the lowest untreated pH, with ventilation_filter.observe's own definitions for the tags it
    keeps (arrival, R1, R4)."""

    def __init__(self):
        self.values = {}
        self.extreme = {"survivors": 0, "flagged": 0, "by_case": {C57: 0, C72: 0}, "lowest": None}

    def add(self, name: str, case: str, value) -> None:
        if value is not None:
            self.values.setdefault(f"{name} {case}", []).append(value)

    def public(self) -> dict:
        return {"observables": {k: ab._spread(v) for k, v in sorted(self.values.items())},
                "extreme_acidemia": self.extreme}


def see(obs: Seen, parts: dict, units: list) -> None:
    """units: (upstream survivor, bitset) at one (tone gain, demand); ventilation_filter.observe's arrival, R1 and R4
    branches, line for line."""
    seen = set()
    for survivor, bits in units:
        if not bits:
            continue
        keys = vf.unit_keys(survivor)
        flagged = 0
        for case in CASES:
            x = vf._extreme_bits(parts[keys[case]["P1"]])
            obs.extreme["by_case"][case] += (bits & x).bit_count()
            flagged |= x
        obs.extreme["survivors"] += bits.bit_count()
        obs.extreme["flagged"] += (bits & flagged).bit_count()
        for case in CASES:
            k = keys[case]
            for c in vf._surviving(bits, vf.RR_DIMS[case]):
                seen.add(("arrival_rr", case, c[:2]))
                for tag, kind in (("untreated_rr", "P1"), ("definitive_rr", "P4")):
                    seen.add((tag, k[kind], c))
            for c in vf._surviving(bits, vf.GAS_DIMS):
                seen.add(("arrival_gas", case, c[:1]))
                for tag, kind in (("untreated_gas", "P1"), ("definitive_gas", "P4")):
                    seen.add((tag, k[kind], c))
    rr_of = {}
    for tag, where, c in seen:
        if tag == "untreated_rr":
            rr_of.setdefault(where, set()).add(c)
    lowest = obs.extreme["lowest"]
    for tag, where, c in sorted(seen, key=str):
        if tag == "arrival_rr":
            obs.add("arrival_rr", where, ab.arrival_rr(vf.DRIVE_GAINS[c[0]], vf.INTRINSIC_RR[c[1]], where))
        elif tag == "arrival_gas":
            gain = vf.VENTILATION_GAINS[c[0]]
            obs.add("arrival_paco2", where, vs.predicted_paco2(gain, where))
            obs.add("arrival_ph_diagnostic", where, vs.predicted_ph(gain, where))
        elif tag in ("untreated_rr", "definitive_rr"):
            g, i, b, t = c
            rr = vf.rr_at_120(parts[where]["summary"], (b, t), vf.DRIVE_GAINS[g], vf.INTRINSIC_RR[i])
            obs.add(f"{tag}_120", where[1], rr)
            if tag == "definitive_rr":
                obs.add("residual_rr_above_intrinsic_120", where[1], rr - vf.INTRINSIC_RR[i])
        else:
            v, b, t = c
            g_ = parts[where]["summary"][(b, t)]["gas"][v]
            obs.add(f"{tag.split('_')[0]}_paco2_120", where[1], g_["paco2_120"])
            obs.add(f"{tag.split('_')[0]}_ph_120", where[1], g_["ph_120"])
            if tag == "untreated_gas":
                obs.add("untreated_ph_lowest_0_120", where[1], g_["ph_low"])
                if g_["ph_low"] is not None and (lowest is None or g_["ph_low"] < lowest["ph"]):
                    lowest = {"ph": g_["ph_low"], "case": where[1], "minute": g_["ph_low_minute"], **g_["at_low"],
                              "_where": where, "_acid": (b, t)}
    if lowest is not None and "_where" in lowest:
        where, (b, t) = lowest.pop("_where"), lowest.pop("_acid")
        burden = lowest["burden"]
        lowest["rr"] = ab._spread([vs.rr_series([burden], [True], vf.DRIVE_GAINS[g], vf.INTRINSIC_RR[i])[0]
                                   for g, i, b_, t_ in rr_of.get(where, ()) if (b_, t_) == (b, t)])
        lowest["flag"] = "CONSCIOUSNESS_COLLAPSE_REVIEW" if lowest["ph"] < vf.EXTREME_ACIDEMIA else None
    obs.extreme["lowest"] = lowest


#: The tags Seen keeps: the P2K-4 record's observables with these names are reproduced from the unpruned bitsets.
SEEN_TAGS = ("arrival_rr", "arrival_paco2", "arrival_ph_diagnostic", "untreated_rr_120", "definitive_rr_120",
             "residual_rr_above_intrinsic_120", "untreated_paco2_120", "untreated_ph_120", "untreated_ph_lowest_0_120",
             "definitive_paco2_120", "definitive_ph_120")


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def seen_reproduced(public: dict, observed: dict) -> dict:
    """The unpruned Seen against P2K-4's observed record: every kept tag and the extreme acidemia, exactly."""
    mine = {k: v for k, v in public["observables"].items() if k.split(" ")[0] in SEEN_TAGS}
    theirs = {k: v for k, v in observed["observables"].items() if k.split(" ")[0] in SEEN_TAGS}
    return {"observables": _plain(mine) == _plain(theirs) and len(mine) == 2 * len(SEEN_TAGS),
            "extreme_acidemia": _plain(public["extreme_acidemia"]) == _plain(observed["extreme_acidemia"])}


# 8. Support, identifiability and demand after the pruning (P2K-5-9) --------------------------------------------------------

STRUCTURAL_CLASSES = ("STRUCTURALLY_BOUNDED_NON_IDENTIFIABLE", "STRUCTURALLY_BOUNDED_POORLY_IDENTIFIED",
                      "STRUCTURALLY_BOUNDED_PARTIALLY_CONSTRAINED")
IDENTIFIABILITY_RULE = (
    "Frozen. The other parameters: P2K-4's rule on the pruned bitsets. The ventilation gain: its support is fixed by the "
    "structural rule, not by the cases, so it is never WELL_CONSTRAINED. Within the admissible support it is "
    "STRUCTURALLY_BOUNDED_NON_IDENTIFIABLE when the filter does not read it (every unit's survivors identical at 0.03 and "
    "0.04), STRUCTURALLY_BOUNDED_POORLY_IDENTIFIED when both values survive although it is read, and "
    "STRUCTURALLY_BOUNDED_PARTIALLY_CONSTRAINED when one does. No value is chosen; the cross-demand classes are read inside "
    "the admissible support, the rejected gains counted apart.")


def invariant_within(bits: int, dim: str, indices: tuple) -> bool:
    k = vf.DIMS.index(dim)
    stride = vf.STRIDES[k]
    base = (bits & vf.DIM_MASKS[dim][indices[0]]) >> (indices[0] * stride)
    return all((bits & vf.DIM_MASKS[dim][v]) >> (v * stride) == base for v in indices[1:])


def pruned_support(union: int, units: list) -> dict:
    out = vf.latent_support(union, units)
    indices = tuple(GAIN_INDEX[g] for g in RETAINED_GAINS)
    values = [vf.VALUES[GAIN_DIM][v] for v in indices if union & vf.DIM_MASKS[GAIN_DIM][v]]
    reads = not all(invariant_within(bits, GAIN_DIM, indices) for bits in units)
    if not values:
        klass = "NON_IDENTIFIABLE"
    elif len(values) < len(indices):
        klass = STRUCTURAL_CLASSES[2]
    else:
        klass = STRUCTURAL_CLASSES[1] if reads else STRUCTURAL_CLASSES[0]
    out[GAIN_DIM] = {"class": klass, "values": values, "admissible_support": list(RETAINED_GAINS),
                     "rejected_support": {f"{g:g}": REJECTED for g in REJECTED_GAINS},
                     "latent_combinations_by_value": {f"{vf.VALUES[GAIN_DIM][v]:g}":
                                                      (union & vf.DIM_MASKS[GAIN_DIM][v]).bit_count() for v in indices},
                     "filter_reads_it_within_support": reads, "narrowed_by": "ACID_BASE_MONOTONICITY (structural)"}
    return out


def pruned_cross_demand(unions: dict) -> dict:
    one, other = unions.get(1.0, 0), unions.get(1.1, 0)
    sets = {"ROBUST_ACROSS_DEMAND": one & other, "DEMAND_1_0_ONLY": one & ~other & ADMISSIBLE_MASK,
            "DEMAND_1_1_ONLY": other & ~one & ADMISSIBLE_MASK,
            "DEMAND_INCOMPATIBLE": ADMISSIBLE_MASK & ~(one | other), REJECTED: vf.FULL & ~ADMISSIBLE_MASK}
    return {name: {"count": bits.bit_count(),
                   "support": {dim: [vf.VALUES[dim][v] for v in range(len(vf.VALUES[dim])) if bits & vf.DIM_MASKS[dim][v]]
                               for dim in vf.DIMS}} for name, bits in sets.items()}


# 9. R3 / R4, non-regression and the observables of the pruned region (P2K-5-6, -8) -----------------------------------------

R3R4_RULE = (
    "Not reopened. The underlying states (bleeding state, BloodState, chronology) read no respiratory latent, so P2K-4's "
    "result (no SCENARIO_STATE_COLLAPSE_BUG) holds for every pruned candidate; the respiratory gap is a maximum over the "
    "pair's surviving latent combinations, so the pruning can only keep a pair's class or move it from "
    "RESPIRATORY_OUTPUTS_DISTINCT to PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE. P2K-4's counts are carried as the bound.")
DOMAINS = ("blood_state", "output", "pressure_tone", "delivery_deficit", "D", "lactate", "hr_baroreflex")


def r3r4_status(record: dict) -> dict:
    out = {}
    for factor, data in sorted(record["demands"].items()):
        r = data["observed"]["r3r4"]
        out[factor] = {"p2k4_classes": r["classes"], "bug": r["bug"],
                       "status": vf.R3R4_CLASSES[2] if r["bug"] else vf.R3R4_CLASSES[0]}
    return out


def non_regression(record: dict, region_unchanged: dict, closed: dict) -> dict:
    """Every upstream domain unchanged: no core or upstream file changed (P2K-4's closed bytes), the P2J-3 region
    reproduces its record, and P2K-4's comparator validation (the same bytes) found every domain equal."""
    base = all(closed.values()) and all(region_unchanged.values())
    validated = record["comparator_validation"]["domains"]
    return {d: {"unchanged": base and bool(validated.get(d)) and record["comparator_validation"]["equal"],
                "evidence": "closed files at P2K-4 bytes; P2J-3 region reproduced; P2K-4 comparator validation"}
            for d in DOMAINS}


def envelope_checks(observables: dict) -> dict:
    """ventilation_filter.survivor_checks' envelope and arrival lines on the pruned survivors' own observables."""
    get = lambda name, case: observables.get(f"{name} {case}", {})
    held, arrival = True, True
    for case, (a, g) in ((C57, ("A", "G")), (C72, ("B", "G2"))):
        e = vf.ENVELOPES
        held &= vf._within(get("untreated_rr_120", case), e[a]["rr"])
        held &= vf._within(get("untreated_paco2_120", case), e["C" if case == C57 else "D"]["paco2"])
        held &= vf._within(get("definitive_rr_120", case), e[g]["rr"])
        held &= vf._within(get("definitive_paco2_120", case), e["H"]["paco2"])
        held &= vf._within(get("definitive_ph_120", case), e["H"]["ph"])
        held &= vf._within(get("residual_rr_above_intrinsic_120", case), e["I"]["residual"][case])
        arrival &= vf._within(get("arrival_rr", case), vf.ARRIVAL_RR[case])
        arrival &= vf._within(get("arrival_paco2", case), vf.ARRIVAL_PACO2[case])
    return {"envelopes_hold": held, "arrival_compatible": arrival}


# 10. The next domain: what may reach consciousness / neurologic response N (P2K-5-11; inventory only) -----------------------

N_INVENTORY = (
    {"signal": "effective oxygen deficit", "source": "derived.effective_oxygen_deficit, derived.acute_deficit_signal",
     "status": "CORE: drives the acid burden and the sympathetic drive"},
    {"signal": "D (accumulated oxygen-delivery debt)", "source": "state Channel.D (C8)",
     "status": "CORE: drives lactate and the sympathetic drive"},
    {"signal": "pH / acidemia", "source": "derived.respiration (P2K-2), ventilation.ventilated_respiration (P2K-3)",
     "status": "SHADOW_CANDIDATE: output only; the untreated extreme-acidemia rows are carried to "
               "CONSCIOUSNESS_COLLAPSE_REVIEW"},
    {"signal": "PaCO2", "source": "ventilation.ventilated_respiration (PaCO2_reference / W)",
     "status": "SHADOW_CANDIDATE: output only"},
    {"signal": "glucose", "source": "state Channel.GLUCOSE (C11, absolute from the case)",
     "status": "CORE: the hypoglycaemia term of the sympathetic drive (threshold PROVISIONAL)"},
    {"signal": "oxygenation", "source": "SpO2 in derived._perfusion (FiO2 and gas exchange G); PaO2 authored only",
     "status": "CORE: the hypoxaemia term of the sympathetic drive (threshold PROVISIONAL)"},
    {"signal": "neurologic channel N", "source": "state Channel.N (C9, CNS depression level, deviation from arrival)",
     "status": "EXISTS: integration guard only; no module writes N yet"},
    {"signal": "MAP / cerebral perfusion (not in the faculty's list)", "source": "derived._perfusion (pressure_rel)",
     "status": "CORE: offered for the faculty's decision, not assumed"},
)
N_NOTE = ("Inventory only: no consciousness calibration, no rule, no N writer; nothing reaches N today. The next brief "
          "decides which of these may.")


# 11. Verdict, recommendation, design, freeze ---------------------------------------------------------------------------------

CLOSED = "GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE"
NOT_READY = "GI_RESPIRATORY_MONOTONICITY_CLOSURE_NOT_READY"
EMPTY = "RESPIRATORY_MONOTONICITY_REGION_EMPTY"
CRITERIA = ("upstream_unchanged", "reuse_exact", "region_nonempty", "ph_monotone", "envelopes_hold",
            "treatment_responses_coherent", "r3_r4_physiological", "latent_uncertainty_kept",
            "extreme_acidemia_carried", "nothing_approved")
VERDICT_RULE = (
    "Frozen. EMPTY when no candidate survives the pruning at either demand (a STOP: no gain restored, nothing widened). "
    "CLOSED when every criterion holds: the upstream is unchanged (closed files at P2K-4's bytes, the P2J-3 region "
    "reproduced, every domain equal); the reuse is exact (REUSE_RULE, and the record's algebra equals the recomputed "
    "pruning); some candidate survives; pH is non-increasing in the burden for every retained gain (the analytic rule, "
    "the executable mapping equal to the analysed one, the probes); every pruned survivor's observables lie in A-I and "
    "its arrival windows; the treatment responses stay coherent under the corrected signal (no rejecting or "
    "perfusion-worse reading among the survivors, the declared transition only, no paradox reachable); no R3 / R4 "
    "state collapse; every other latent keeps its P2K-4 support and both admissible gains survive (no value chosen); the "
    "extreme-acidemia candidates stay in the region; nothing is approved. Otherwise NOT_READY with the first failing "
    "criterion as the blocker; an early stop lists what it never reached as not evaluated.")
NEXT_RULE = (
    "Predeclared. When CLOSED: MOVE_FORWARD_TO_CONSCIOUSNESS (consciousness / neurologic response N, not begun here), "
    "the untreated extreme acidemia carried to CONSCIOUSNESS_COLLAPSE_REVIEW, the cross-demand classes to the demand "
    "question, the remaining latent uncertainty (intrinsic RR, drive gain, B, tau, 0.03 against 0.04) propagated, never "
    "a reason for another respiratory cycle. Otherwise STOP_FOR_FACULTY_REVIEW with the blocker.")
POLICY = ("Shadow only. P2K-4's frozen code and record reused, never edited; the gain rejected by the analysis alone; no "
          "envelope, window, reference, tolerance, B, tau or other support changed; no new respiratory parameter or "
          "functional form; untreated pH never filters and the extreme-acidemia rows stay; the legacy never read; "
          "nothing selected or approved.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no runtime integration, GI or second-family migration or parameter approval "
                  "is authorized; consciousness and collapse are not calibrated")


def verdict(checks: dict) -> dict:
    failing = [name for name in CRITERIA if checks.get(name) is False]
    unevaluated = [name for name in CRITERIA if name not in checks]
    if checks.get("region_nonempty") is False:
        result = EMPTY
    elif failing:
        result = f"{NOT_READY} - {failing[0].upper()}"
    else:
        result = CLOSED if not unevaluated else f"{NOT_READY} - NOT_EVALUATED"
    return {"verdict": result, "checks": checks, "failing": failing, "not_evaluated": unevaluated}


def recommendation(result: dict) -> dict:
    if result["verdict"] == CLOSED:
        return {"recommendation": "MOVE_FORWARD_TO_CONSCIOUSNESS",
                "next": "CONSCIOUSNESS / NEUROLOGIC RESPONSE N (not begun)",
                "forwarded": {"untreated_extreme_acidemia": "CONSCIOUSNESS_COLLAPSE_REVIEW",
                              "cross_demand": "the demand question (diagnostic)",
                              "latent": "explicit uncertainty propagated; no respiratory cycle for identifiability"},
                "rule": NEXT_RULE}
    return {"recommendation": "STOP_FOR_FACULTY_REVIEW", "blocker": result["verdict"], "rule": NEXT_RULE}


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "status": STATUS,
            "no_new_parameters": list(NO_NEW_PARAMETERS), "strategic_note": STRATEGIC_NOTE, "equation": EQUATION,
            "inequality": INEQUALITY, "rule_scope": RULE_SCOPE, "hco3_reference": HCO3_REFERENCE,
            "paco2_reference": PACO2_REFERENCE, "p2k4_gains": list(P2K4_GAINS), "gain_classes": GAIN_CLASSES,
            "retained_gains": list(RETAINED_GAINS), "previously_excluded": PREVIOUSLY_EXCLUDED,
            "probe_burdens": list(PROBE_BURDENS), "mapping_tolerance": MAPPING_TOLERANCE,
            "semantic_rule": SEMANTIC_RULE, "paradox": [PARADOX_HIGHER, PARADOX_LOWER],
            "perfusion_worse": list(PERFUSION_WORSE), "float_margin": FLOAT_MARGIN, "tolerance_floor": TOLERANCE_FLOOR,
            "certified_full": list(CERTIFIED_FULL), "recomputed_never_failed": list(RECOMPUTED_NEVER_FAILED),
            "reuse_rule": REUSE_RULE, "reached_kinds": list(REACHED_KINDS), "stubbed_kinds": list(STUBBED_KINDS),
            "reach_rule": REACH_RULE, "seen_tags": list(SEEN_TAGS), "structural_classes": list(STRUCTURAL_CLASSES),
            "identifiability_rule": IDENTIFIABILITY_RULE, "r3r4_rule": R3R4_RULE, "domains": list(DOMAINS),
            "n_inventory": list(N_INVENTORY), "n_note": N_NOTE, "criteria": list(CRITERIA),
            "verdict_rule": VERDICT_RULE, "next_rule": NEXT_RULE, "policy": POLICY, "migration_gate": MIGRATION_GATE,
            "p2k4_digest": P2K4_DIGEST, "p2k4_record_sha": P2K4_RECORD_SHA, "closed_at_p2k4": CLOSED_AT_P2K4,
            "own": list(OWN), "report": REPORT, "tuple_at_p2k4": TUPLE_AT_P2K4,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2k4": hashlib.sha256(P2K4_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# 12. Run -----------------------------------------------------------------------------------------------------------------------

def _stopped(out: dict, checks: dict, why: str) -> dict:
    out["stopped"] = why
    out["verdict"] = verdict(checks)
    out["recommendation"] = recommendation(out["verdict"])
    return out


def _demand(factor: float, record: dict, tally, full: Seen, pruned: Seen, union: int, bits: list, tone: dict,
            algebra: dict, certificate: dict) -> dict:
    rec = record["demands"][f"{factor:g}"]
    public = tally.public()
    kept = sum(b.bit_count() for b in bits)
    observed = pruned.public()
    support = pruned_support(union, bits)
    reproduced = {"tally": _plain(public) == _plain(rec["filter"]), **seen_reproduced(full.public(), rec["observed"])}
    by_value = {dim: s["latent_combinations_by_value"] for dim, s in support.items()}
    algebra_equal = (algebra["exact"] and algebra["kept"] == kept and algebra["rejected"] == public["survivors"] - kept
                     and algebra["by_tone_gain"] == {t: row["survivors"] for t, row in sorted(tone.items())}
                     and algebra["latent_combinations"] == union.bit_count() and algebra["by_value"] == by_value
                     and algebra["classes_other"] == {d: s["class"] for d, s in support.items() if d != GAIN_DIM})
    return {"entering": public["survivors"], "rejected_by_monotonicity": public["survivors"] - kept,
            "failed_by_semantic_correction": 0 if certificate["perfusion_worse_readings"] == 0 else None,
            "survivors": kept, "by_tone_gain": tone, "upstream_units": public["upstream_units"],
            "upstream_units_with_survivors": sum(1 for b in bits if b), "latent_combinations": union.bit_count(),
            "latent_support": support, "observed": observed, "envelopes": envelope_checks(observed["observables"]),
            "reproduced": reproduced, "algebra_equal": algebra_equal}


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2k4_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "record": P2K4_DIGEST, "design": design(), "closed_unchanged": closed_unchanged(),
               "approval": STATUS["approved"], "migration_gate": MIGRATION_GATE, "strategic_note": STRATEGIC_NOTE}
        checks = {"nothing_approved": True}
        if not all(out["closed_unchanged"].values()):
            checks["upstream_unchanged"] = False
            return _stopped(out, checks, "a closed file changed: STOP")
        say("analytic rule, executable mapping, probes, corrected signal")
        out.update({"analytic": analytic_proof(), "mapping": mapping_check(), "probes": probes(),
                    "semantics": semantics(), "paradox_unreachable": paradox_unreachable()})
        checks["ph_monotone"] = (all(monotone(g) for g in RETAINED_GAINS) and not any(monotone(g) for g in REJECTED_GAINS)
                                 and all(row["equal"] and row["reference_is_zero_burden"]
                                         for row in out["mapping"].values())
                                 and out["probes"]["admissible_non_increasing"]
                                 and out["probes"]["rejected_rise_at_low_burden"])
        certified = certificates(record)
        out["equivalence"] = {"p2k4_freeze_digest": p2k4_freeze_digest() == P2K4_DIGEST, "record_pinned": True,
                              "certificates": certified}
        if not (out["equivalence"]["p2k4_freeze_digest"] and all(c["holds"] for c in certified.values())):
            checks["reuse_exact"] = False
            return _stopped(out, checks, "P2K-4's code or certificates do not hold: the exact reuse is invalid (STOP)")
        out["algebra"] = record_algebra(record)
        say("certified physiology (P2J-3 region)")
        region = br.pressure_tone_region(map_, say)
        out["region_unchanged"] = region["unchanged"]
        out["non_regression"] = non_regression(record, region["unchanged"], out["closed_unchanged"])
        checks["upstream_unchanged"] = all(d["unchanged"] for d in out["non_regression"].values())
        if not checks["upstream_unchanged"]:
            return _stopped(out, checks, "the upstream physiology is not reproduced: STOP")
        arrival = vf.arrival_bits()
        say("reached R1 / R4 trajectories")
        tallies, full, pruned, unions, bits, tones = {}, {}, {}, {}, {}, {}
        built = stubbed = 0
        for (gain, factor), survivors in sorted(region["survivors"].items()):
            say(f"tone {gain:g}, demand {factor:g}")
            survivors = sorted(survivors)
            parts = reached_parts(region["bloods"], survivors, factor, gain)
            built += sum(1 for p in parts.values() if "summary" in p)
            stubbed += sum(1 for p in parts.values() if "summary" not in p)
            tally = tallies.setdefault(factor, vf.Tally())
            units, kept = [], []
            for survivor in survivors:
                b = tally.add(vf.unit_rules(parts, survivor, arrival), gain)
                units.append((survivor, b))
                kept.append((survivor, b & ADMISSIBLE_MASK))
            see(full.setdefault(factor, Seen()), parts, units)
            see(pruned.setdefault(factor, Seen()), parts, kept)
            for _, b in kept:
                unions[factor] = unions.get(factor, 0) | b
            bits.setdefault(factor, []).extend(b for _, b in kept)
            row = tones.setdefault(factor, {}).setdefault(f"{gain:g}", {"entering": 0, "survivors": 0, "units": 0})
            row["entering"] += sum(b.bit_count() for _, b in units)
            row["survivors"] += sum(b.bit_count() for _, b in kept)
            row["units"] += len(units)
        demands = {f"{factor:g}": _demand(factor, record, tallies[factor], full[factor], pruned[factor],
                                          unions.get(factor, 0), bits[factor], tones[factor],
                                          out["algebra"][f"{factor:g}"], certified[f"{factor:g}"])
                   for factor in sorted(tallies)}
        out["demands"] = demands
        out["cross_demand"] = pruned_cross_demand(unions)
        out["r3r4"] = r3r4_status(record)
        out["n_inventory"] = {"signals": list(N_INVENTORY), "note": N_NOTE}
        checks["reuse_exact"] = len(demands) == len(record["demands"]) and all(
            d["reproduced"]["tally"] and d["reproduced"]["observables"] and d["reproduced"]["extreme_acidemia"]
            and d["algebra_equal"] for d in demands.values())
        checks["region_nonempty"] = any(d["survivors"] for d in demands.values())
        if not checks["region_nonempty"]:
            return _stopped(out, checks, "no candidate survives the pruning: STOP (RESPIRATORY_MONOTONICITY_REGION_EMPTY)")
        checks["envelopes_hold"] = all(d["envelopes"]["envelopes_hold"] and d["envelopes"]["arrival_compatible"]
                                       for d in demands.values() if d["survivors"])
        s = out["semantics"]
        checks["treatment_responses_coherent"] = (
            all(c["perfusion_worse_readings"] == 0 and c["rejecting_readings"] == 0 for c in certified.values())
            and all(d["failed_by_semantic_correction"] == 0 for d in demands.values())
            and s["only_perfusion_worse_higher_burden"] and s["never_unrejects"]
            and all(out["paradox_unreachable"].values()))
        checks["r3_r4_physiological"] = not any(r["bug"] for r in out["r3r4"].values())
        checks["latent_uncertainty_kept"] = all(
            d["latent_support"][dim]["values"] == record["demands"][f]["latent_support"][dim]["values"]
            for f, d in demands.items() if d["survivors"] for dim in vf.DIMS if dim != GAIN_DIM) and all(
            d["latent_support"][GAIN_DIM]["values"] == list(RETAINED_GAINS) for d in demands.values() if d["survivors"])
        checks["extreme_acidemia_carried"] = all(d["observed"]["extreme_acidemia"]["survivors"] == d["survivors"]
                                                 for d in demands.values())
        p2k4 = record["efficiency"]
        out["efficiency"] = {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs":
                             region["counterfactual_runs"], "reached_trajectories": built,
                             "trajectories_not_rebuilt": stubbed, "candidates_retallied": sum(
                                 t.entering for t in tallies.values()),
                             "upstream_units": sum(t.units for t in tallies.values()),
                             "not_rerun": {"no_prbc_runs": p2k4["no_prbc_runs"],
                                           "r3r4_state_runs": p2k4["r3r4_state_runs"],
                                           "comparator_core_runs": p2k4["comparator_core_runs"],
                                           "p2k3_validation_runs": p2k4["p2k3_validation_runs"],
                                           "direct_check_candidates": p2k4["direct_check_candidates"]},
                             "analytic_rejections": sum(d["rejected_by_monotonicity"] for d in demands.values()),
                             "cartesian_sweep": False, "legacy_read": False}
        out["verdict"] = verdict(checks)
        out["recommendation"] = recommendation(out["verdict"])
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
    if args.run:
        if args.out is None:
            parser.error("--run needs --out")
        args.out.mkdir(parents=True, exist_ok=True)
        result = run(progress=lambda *m: print(*m, flush=True))
        (args.out / "respiratory_monotonicity.json").write_text(
            json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
