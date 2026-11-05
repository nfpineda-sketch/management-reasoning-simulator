"""P2T-3: the asthma shadow migration retried with the common respiratory distress region (shadow only).

It supersedes P2S-3 prospectively; P2S-3's history is not rewritten (ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_DRIVE_GAP,
P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT). It adds no common physiology: the P2S-2 mechanics, the P2T-1 / P2T-1A distress
architecture and P2S-3's ``AirwayObstruction`` writer are used unchanged; only the two registry tuples gain this
package's entries.

- Distress scale: ABSOLUTE_DISTRESS_SCALE_NONIDENTIFIABLE (P2T-2), so d(asthma_49m) = 1 is an ANALYTIC_NORMALIZATION_ONLY
  convention, never a clinical value; every conclusion is shown invariant under d -> lambda d, gains -> gains / lambda.
- The arrival distress is a FAMILY_CANDIDATE region from the authored respiratory evidence (49m "Severe" above 24f
  "Markedly increased", above normal): with the normalization, d(24f) in (0, 1). RR and HR only test which part of it is
  compatible; they never define it.
- Gains stay region-valued: the acid gain k in [1, 2] (P2T3_ANALYSIS_SUBREGION_OF_EXISTING_ACID_UNCERTAINTY, at P2K-4's
  support points 1, sqrt 2, 2), rho = g_HR / g_RR in its conditional interval rho_allowed(k), and the normalized drive
  product g_RR d(49m). PE 33f's HR is upper-bound evidence only (faculty decision). No optimizer, no best point:
  witnesses are drawn by a predeclared rule only after the region is shown non-empty (REGION_WITNESS_ONLY).
- The hypoxaemic drive, the beta-agonist HR effect, systemic stress and every clinical gain stay UNSET.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import dataclass, fields, replace
from pathlib import Path

from . import acs_reference as ar
from . import asthma_migration as sm
from . import asthma_reference as sr
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import distress_closure as xm
from . import edema_migration as pe
from . import edema_reference as er
from . import embolism_migration as em
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import gi_reference
from . import respiratory_distress as dm
from . import respiratory_drive as rd
from . import respiratory_mechanics as mc
from .integration import Contribution, Contributor, step
from .provenance import ChannelDelta, DistressChange, ProvenanceError, SourceKind
from .state import Channel, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2T-3"
DECIDED = "2026-11-05"
OWN = ("clinical_core/asthma_distress_migration.py",)
REPORT = "clinical_core/asthma_distress_migration_report.py"
RECORD = ROOT / "docs" / "revision" / "P2T3_asthma_distress_migration.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2T3_ASMA_DISTRES_SOMBRA.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
PRIMARY, SECONDARY = sr.CASE, sr.SECONDARY

DECISIONS = {
    "supersedes": "P2S-3 prospectively; its record and verdict stay (ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_DRIVE_GAP; "
                  "P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT)",
    "l1": "ACCUMULATED_FLOAT_CANCELLATION_DEBT: fail closed; a writer returning distress to a target writes the exact "
          "difference from the current state; the P2T-1A tolerance is not broadened",
    "scale": "ANALYTIC_NORMALIZATION_ONLY: d(asthma_49m) = 1; not a clinical value, a universal scale, 'severe = 1' or a "
             "WOB mapping",
    "acid_gain": "P2T3_ANALYSIS_SUBREGION_OF_EXISTING_ACID_UNCERTAINTY: k in [1, 2] at P2K-4's support points; the "
                 "parameter stays PROVISIONAL / POORLY_IDENTIFIED",
    "rho": "carried as the conditional interval rho_allowed(k), never a point",
    "pe33_hr": "COMPATIBILITY / UPPER-BOUND evidence only (pleuritic pain, unmodelled arousal)",
    "hypoxaemic_drive": "UNSET in the primary region; a sensitivity only after the primary region succeeds",
    "central_availability": "structurally normal (1): 49m's hypercapnia is MECHANICAL VENTILATORY FAILURE",
    "heart_rate": "a compatibility constraint; no beta-agonist HR physiology, no systemic_stress",
    "writers": "P2S-3's AirwayObstruction reused unchanged (mechanics only); bronchodilator and distress evolution only as "
               "SYNTHETIC_ONLY direction probes; no mechanics -> distress coupling",
    "direct_g": "the existing G interface, never L or L_rev; HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED",
}

# The carried region and the predeclared witness rule ------------------------------------------------------------------------

NORMALIZATION = {"case": PRIMARY, "value": 1.0, "class": "ANALYTIC_NORMALIZATION_ONLY"}
K_REGION = (1.0, 2.0)
K_POINTS = (1.0, 2.0 ** 0.5, 2.0)                 # P2K-4's support points inside [1, 2]
I_RR = (sr.INTRINSIC_POINTS["lower"], sr.INTRINSIC_POINTS["upper"])   # 12 - 20 (P2K-4 / P2S-2)
I_HR = (gi_reference.RESTING_HR[0], gi_reference.RESTING_HR[2])       # 60 - 100, at most the observed HR
WITNESS_I_HR = gi_reference.RESTING_HR[0]          # the band end the HR upper bound is computed at
LAMBDAS = (0.5, 1.0, 2.0, 10.0)        # powers of two are exact in binary64; 10 shows the invariance to roundoff
#: REGION_WITNESS_ONLY, applied after non-emptiness: (k, fraction of the effective rho interval); x(49m) and x(24f) at the
#: middle of their admissible intervals there (x(24f) below x(49m)). Not a fit, not a prior.
WITNESS_RULE = {"LOW": (K_POINTS[0], 0.25), "MID": (K_POINTS[1], 0.5), "HIGH": (K_POINTS[2], 0.75)}
HYPOXAEMIC_SENSITIVITY_GAIN = rd.SYNTHETIC_GAINS[0]     # P2P-2's SYNTHETIC_ONLY gain, sensitivity only
COURSE_MINUTES = 60
OBSTRUCTION_RATE = sm.MID_WORSENING
RELIEF = sm.RELIEF                                      # P2S-3's structural mechanics relief window
DISTRESS_RELIEF = {"from_minute": 10, "to_minute": 40, "target_fraction": 0.5, "fraction_per_min": 0.1}
G_PROBE_PER_MIN = 0.002

WOB_TIER = {"Reduced": 0, "Normal": 0, "Mildly increased": 1, "Increased": 2, "Markedly increased": 3, "Severe": 4}
TIER_NAMES = ("Reduced / Normal", "Mildly increased", "Increased", "Markedly increased", "Severe")
FAMILIES = ("pulmonary_edema", "pulmonary_embolism", "asthma", "pneumonia", "opioid", "anaphylaxis", "acs", "gi_bleed",
            "renal_colic", "hypoglycemia")
TWO_SIDED_HR = ("pulmonary_edema_58m", "pulmonary_embolism_61m")
HR_EXCLUDED = ("anaphylaxis_63m_betablocked",)          # authored atenolol: the HR is not distress evidence
CROSS_FAMILY = ("pulmonary_edema_58m", "pulmonary_embolism_61m", "pulmonary_embolism_33f")
CONTROLS = ("opioid_35m", "opioid_67f", "gi_bleed_57m", "gi_bleed_72f")
ANAPHYLAXIS = ("anaphylaxis_29f", "anaphylaxis_63m_betablocked")
ACS_RESIDUAL = "acs_70f_left_main"


def profile() -> dv.CoreProfile:
    """P2S-3's asthma reference profile (mechanics on, the gas-exchange reference), distress readers UNSET."""
    return sm.profile()


# P2T-3-1: case truth (re-read) -------------------------------------------------------------------------------------------------

LATER_TREATMENT = "NONE_AUTHORED: no oxygen, bronchodilator or steroid response and no later observation is authored"


def case_truth() -> dict:
    out = {}
    for name in sr.CASES:
        t = sr.truth(name)
        meds = " ".join(t["medications"] or []).lower()
        out[name] = {"authored": t, "map": sr.authored_map(t), "peak_flow": sr.peak_flow(t),
                     "prehospital_beta_agonist": any(w in meds for w in sm.BETA_AGONIST_WORDS),
                     "later": LATER_TREATMENT}
    p2s3 = json.loads(sm.RECORD.read_text(encoding="utf-8"))["case"]
    out["same_as_p2s3"] = go._plain(sm.case()) == p2s3
    out["classes"] = {"AUTHORED_CASE_TRUTH": sorted(sr.TRUTH_PATHS), "LEGACY_ENGINE_BEHAVIOR": sm.LEGACY_CONSTANTS,
                      "MODEL_DERIVED": sm.MODEL_DERIVED, "later_observations": sm.LATER_OBSERVATIONS}
    out["pass"] = out["same_as_p2s3"] and all(out[n]["prehospital_beta_agonist"] for n in sr.CASES)
    return out


# P2T-3-2: the family writer (P2S-3's, unchanged) -----------------------------------------------------------------------------

def writer() -> dict:
    found = sm.writer_semantics()
    unchanged = xm.common_untouched()
    out = {"p2s3_writer_semantics": found, "files_at_p2t1a": {f: unchanged[f] for f in sm.OWN},
           "status": "REUSED_UNCHANGED: AirwayObstruction writes the common mechanics target only"}
    out["pass"] = found["pass"] and all(out["files_at_p2t1a"].values())
    return out


# P2T-3-3: the authored respiratory evidence and its order ----------------------------------------------------------------------

def evidence() -> dict:
    import clinical_cases
    rows = {}
    for family in FAMILIES:
        for v in clinical_cases.FAMILIES[family]["variants"]:
            o, gas = v["observable"], v["investigations"]["abg"]["result"]
            rows[v["id"]] = {"family": family, "wob": o["work_of_breathing"], "tier": WOB_TIER[o["work_of_breathing"]],
                             "rr": float(o["respiratory_rate"]), "hr": float(o["hr"]), "spo2": float(o["spo2"]),
                             "hco3": float(gas["bicarbonate_mmol_l"]), "paco2": float(gas["paco2_mm_hg"]),
                             "exam": v["examination"].get("Respiratory"), "presentation": v.get("presentation")}
    order = {"primary_above_secondary": rows[PRIMARY]["tier"] > rows[SECONDARY]["tier"] > 0,
             "primary": {k: rows[PRIMARY][k] for k in ("wob", "exam", "presentation")},
             "secondary": {k: rows[SECONDARY][k] for k in ("wob", "exam", "presentation")},
             "prior_region_secondary": "d(24f) in (0, 1) under d(49m) = 1: FAMILY_CANDIDATE + ANALYTIC_NORMALIZATION_ONLY "
                                       "(below 49m's 'Severe', above normal); RR and HR only test it"}
    return {"cases": rows, "tiers": TIER_NAMES, "asthma_order": order, "pass": order["primary_above_secondary"]}


# P2T-3-4 / -14: the region (analytic intervals, monotone elimination, one greedy order check per point) ------------------

def _constants(prof=None) -> dict:
    p = profile() if prof is None else prof
    return {"S": p.rr_drive_saturation, "hco3_ref": p.bicarbonate_reference_meq_l, "hr_gain": p.hr_per_sympathetic_drive,
            "ceiling": p.sinus_rate_ceiling_bpm}


def drive_needed(rr: float, intrinsic: float, c: dict) -> float:
    """The excitatory drive the common saturation needs for this RR (inverse of rate_from_drive; inf beyond it)."""
    frac = (rr - intrinsic) / c["S"]
    if frac <= 0.0:
        return 0.0
    if frac >= 1.0:
        return math.inf
    return -c["S"] * math.log(1.0 - frac)


def target_needed(hr: float, intrinsic: float, c: dict) -> float:
    """The sympathetic target the common saturation needs for this HR (inverse of sympathetic_increment, beta 0)."""
    reserve = c["ceiling"] - intrinsic
    share = (hr - intrinsic) / reserve
    return 0.0 if share <= 0.0 else reserve / c["hr_gain"] * math.atanh(share)


def intrinsic_for(rr: float, x: float, burden: float, k: float, c: dict) -> float:
    """The intrinsic RR at which the drive k * burden + x gives exactly this RR."""
    return rr - c["S"] * (1.0 - math.exp(-(k * burden + x) / c["S"]))


def existing_targets() -> dict:
    """The sympathetic target the committed arrival mappings already call for (readers UNSET): never double counted."""
    rows = {"pulmonary_edema_58m": (er.anchors(), pe.profile()), "pulmonary_embolism_61m": (mr.anchors(), em.profile()),
            "pulmonary_embolism_33f": (mr.anchors(mr.SECONDARY), em.profile()),
            PRIMARY: (sr.anchors(PRIMARY), profile()), SECONDARY: (sr.anchors(SECONDARY), profile()),
            ACS_RESIDUAL: (ar.anchors(), ar.common_profile())}
    return {k: dv.arrival_state(a, p).aux.sympathetic_drive for k, (a, p) in rows.items()}


def hr_role(case: str, tier: int) -> str:
    if case in TWO_SIDED_HR:
        return "two_sided"
    if case in HR_EXCLUDED:
        return "excluded"
    if tier == 0:
        return "control"
    return "upper_only"


def rows_at(k: float, ev: dict, existing: dict, c: dict, hypoxaemic_gain: float = 0.0) -> dict:
    """Per case: x = g_RR d and y = g_HR d compatible with the authored RR and HR over the intrinsic bands at acid gain k."""
    out = {}
    for case, t in ev["cases"].items():
        burden = max(0.0, c["hco3_ref"] - t["hco3"])
        h = hypoxaemic_gain * min(1.0, max(0.0, (100.0 - t["spo2"]) / 50.0))    # P2P-2's synthetic mapping
        top = min(I_RR[1], t["rr"])
        xhi = drive_needed(t["rr"], I_RR[0], c) - k * burden - h
        xlo = max(0.0, drive_needed(t["rr"], top, c) - k * burden - h)
        if t["family"] == "opioid":            # central availability not authored: distress 0 is always admissible
            xlo, xhi = 0.0, max(xhi, 0.0)
        p = existing.get(case, 0.0)
        ylo = max(0.0, target_needed(t["hr"], min(I_HR[1], t["hr"]), c) - p)
        yhi = max(0.0, target_needed(t["hr"], I_HR[0], c) - p)
        out[case] = {"x": [xlo, xhi], "y": [ylo, yhi], "tier": t["tier"], "role": hr_role(case, t["tier"]),
                     "burden": burden, "existing_target": p, "acid_overshoot": xhi < 0.0, "h": h}
    return out


def rho_bounds(rows: dict) -> dict:
    lo, hi, why = 0.0, math.inf, {"lo": None, "hi": None}
    for case, r in rows.items():
        (xlo, xhi), (ylo, yhi) = r["x"], r["y"]
        if r["acid_overshoot"] or r["role"] in ("excluded", "control"):
            continue
        if r["role"] == "two_sided" and xhi > 0.0 and ylo / xhi > lo:
            lo, why["lo"] = ylo / xhi, case
        if xlo > 0.0 and yhi / xlo < hi:
            hi, why["hi"] = yhi / xlo, case
    return {"rho": [lo, hi], "binding": why}


def order(rows: dict, rho: float) -> dict:
    """The evidence order (weak, across tiers) with every case at the lowest x its RR, its HR (via rho) and the tiers below
    allow; exact for interval constraints. Acid-overshoot cases (acid alone above the authored RR) are reported, not
    blamed on distress."""
    floors, chosen, failing = [0.0] * 5, {}, None
    floor = 0.0
    for tier in range(5):
        top = floor
        for case, r in rows.items():
            if r["tier"] != tier or r["acid_overshoot"]:
                continue
            (xlo, xhi), (ylo, yhi) = r["x"], r["y"]
            if r["role"] == "two_sided":
                xlo, xhi = max(xlo, ylo / rho), min(xhi, yhi / rho)
            elif r["role"] == "upper_only":
                xhi = min(xhi, yhi / rho)
            lo = max(xlo, floor) if tier > 0 else xlo
            if lo > xhi:
                failing = failing or {"case": case, "need": lo, "allowed": xhi}
                continue
            chosen[case] = lo
            top = max(top, lo)
        floors[tier] = top
        floor = top
    return {"feasible": failing is None, "failing": failing, "floors": floors, "chosen": chosen}


def asthma_subregion(rows: dict, rho: float, found_order: dict, ev: dict, k: float, c: dict) -> dict:
    """The asthma part of the region at (k, rho), with d(49m) = 1 (ANALYTIC_NORMALIZATION_ONLY): the normalized drive
    product x(49m) = g_RR, d(24f) = x(24f) / x(49m) below 1, and each case's mechanics efficiency (P2S-2-11's analytic
    form at the intrinsic RR its x implies)."""
    r49, r24 = rows[PRIMARY], rows[SECONDARY]
    floors = found_order["floors"]
    x49 = [max(r49["x"][0], floors[3]), min(r49["x"][1], r49["y"][1] / rho)]
    x24 = [max(r24["x"][0], floors[2]), min(r24["x"][1], r24["y"][1] / rho, x49[1])]
    ok = found_order["feasible"] and x49[0] <= x49[1] and x24[0] < x24[1] and x24[0] < x49[1]
    t49, t24 = sr.truth(PRIMARY), sr.truth(SECONDARY)

    def e(case, t, x, burden):
        return sr.implied_efficiency(t, intrinsic_for(float(t["respiratory_rate"]), x, burden, k, c))

    out = {"feasible": ok, "x49": x49, "x24": x24}
    if ok:
        out["d24"] = [x24[0] / x49[1], min(1.0, x24[1] / x49[0]) if x49[0] > 0 else 1.0]
        out["g_rr_d49"] = x49
        out["g_hr_d49"] = [rho * x49[0], rho * x49[1]]
        out["E49"] = [e(PRIMARY, t49, x49[1], r49["burden"]), e(PRIMARY, t49, x49[0], r49["burden"])]
        out["E24"] = [e(SECONDARY, t24, x24[1], r24["burden"]), e(SECONDARY, t24, x24[0], r24["burden"])]
        out["mechanics_order_admissible"] = out["E24"][1] > out["E49"][0]
    return out


def _feasible(rows, rho, ev, k, c) -> bool:
    o = order(rows, rho)
    return asthma_subregion(rows, rho, o, ev, k, c)["feasible"]


def _boundary(rows, ev, k, c, good: float, bad: float) -> float:
    for _ in range(60):
        mid = 0.5 * (good + bad)
        if _feasible(rows, mid, ev, k, c):
            good = mid
        else:
            bad = mid
    return good


def region(ev: dict | None = None, hypoxaemic_gain: float = 0.0) -> dict:
    ev = evidence() if ev is None else ev
    c, existing = _constants(), existing_targets()
    out = {"constants": c, "k_points": list(K_POINTS), "i_rr": list(I_RR), "i_hr": list(I_HR), "points": {}}
    for k in K_POINTS:
        rows = rows_at(k, ev, existing, c, hypoxaemic_gain)
        bounds = rho_bounds(rows)
        lo, hi = bounds["rho"]
        probes = [lo + f * (hi - lo) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        flags = [_feasible(rows, p, ev, k, c) for p in probes]
        if not any(flags):
            out["points"][f"{k:.6g}"] = {"rows": rows, "bounds": bounds, "effective": None, "nonempty": False}
            continue
        first, last = flags.index(True), len(flags) - 1 - flags[::-1].index(True)
        eff_lo = probes[first] if first == 0 else _boundary(rows, ev, k, c, probes[first], probes[first - 1])
        eff_hi = probes[last] if last == len(probes) - 1 else _boundary(rows, ev, k, c, probes[last], probes[last + 1])
        contiguous = all(flags[first:last + 1])
        at = {}
        for label, f in (("lo", 0.0), ("mid", 0.5), ("hi", 1.0)):
            rho = eff_lo + f * (eff_hi - eff_lo)
            o = order(rows, rho)
            at[label] = {"rho": rho, "order": o, "asthma": asthma_subregion(rows, rho, o, ev, k, c)}
        out["points"][f"{k:.6g}"] = {"rows": rows, "bounds": bounds, "effective": [eff_lo, eff_hi], "nonempty": True,
                                     "contiguous_at_probes": contiguous, "at": at,
                                     "acid_overshoot": sorted(cs for cs, r in rows.items() if r["acid_overshoot"])}
    pts = [v for v in out["points"].values() if v["nonempty"]]
    out["nonempty"] = bool(pts)
    out["every_carried_k"] = len(pts) == len(K_POINTS)
    effs = [out["points"][f"{k:.6g}"]["effective"] for k in K_POINTS if out["points"][f"{k:.6g}"]["nonempty"]]
    out["rho_conditional"] = {f"{k:.6g}": out["points"][f"{k:.6g}"]["effective"] for k in K_POINTS}
    out["monotone_in_k"] = all(b[0] >= a[0] and b[1] >= a[1] for a, b in zip(effs, effs[1:]))
    out["diagnostic_robust_intersection"] = ([max(e[0] for e in effs), min(e[1] for e in effs)] if effs else None)
    out["diagnostic_label"] = "DIAGNOSTIC_ONLY: the k-robust rho intersection; not a clinical prior"
    out["status"] = "ASTHMA_FEASIBLE_SUBREGION_NONEMPTY" if out["nonempty"] else "ASTHMA_FEASIBLE_SUBREGION_EMPTY"
    return out


# P2T-3-15: witnesses (only after non-emptiness) and the live core ------------------------------------------------------------

def witnesses(found_region: dict) -> dict:
    if not found_region["nonempty"]:
        return {"drawn": False}
    ev = evidence()
    c, existing = _constants(), existing_targets()
    out = {"drawn": True, "rule": {k: list(v) for k, v in WITNESS_RULE.items()}, "label": "REGION_WITNESS_ONLY"}
    for label, (k, frac) in WITNESS_RULE.items():
        pt = found_region["points"][f"{k:.6g}"]
        lo, hi = pt["effective"]
        rho = lo + frac * (hi - lo)
        rows = rows_at(k, ev, existing, c)
        o = order(rows, rho)
        a = asthma_subregion(rows, rho, o, ev, k, c)
        x49 = 0.5 * (a["x49"][0] + a["x49"][1])
        x24 = 0.5 * (a["x24"][0] + min(a["x24"][1], x49))
        out[label] = {"k": k, "rho": rho, "x49": x49, "x24": x24, "d49": 1.0, "d24": x24 / x49,
                      "g_rr": x49, "g_hr": rho * x49, "cases": {}}
        for case, x in ((PRIMARY, x49), (SECONDARY, x24)):
            out[label]["cases"][case] = arrival_witness(case, k, rho, x49, x / x49, rows[case]["burden"], c)
    out["pass"] = all(all(w["cases"][cs]["supported"] for cs in sr.CASES) for w in (out[lab] for lab in WITNESS_RULE))
    return out


def witness_profile(k: float, rho: float, g_rr: float, mechanics: bool = True) -> dv.CoreProfile:
    return replace(profile(), acid_to_drive_gain=k, distress_to_respiratory_drive_gain=g_rr,
                   distress_to_sympathetic_gain=rho * g_rr, respiratory_mechanics=mechanics)


def witness_anchors(case: str, intrinsic: float, d: float):
    t = sr.truth(case)
    return sr.anchors(case, "midpoint", intrinsic_respiratory_rate=intrinsic,
                      arrival_mechanics_efficiency=sr.implied_efficiency(t, intrinsic),
                      intrinsic_sinus_rate=WITNESS_I_HR, arrival_respiratory_distress=d)


def arrival_witness(case: str, k: float, rho: float, g_rr: float, d: float, burden: float, c: dict) -> dict:
    t = sr.truth(case)
    intrinsic = intrinsic_for(float(t["respiratory_rate"]), g_rr * d, burden, k, c)
    a, p = witness_anchors(case, intrinsic, d), witness_profile(k, rho, g_rr)
    r = dm.at_arrival(a, p)
    unset = dm.at_arrival(replace(a, arrival_respiratory_distress=0.0),
                          replace(p, distress_to_respiratory_drive_gain=None, distress_to_sympathetic_gain=None))
    hr_80 = 80.0 + (c["ceiling"] - 80.0) * math.tanh(c["hr_gain"] * rho * g_rr * d / (c["ceiling"] - 80.0))
    out = {"intrinsic_rr": intrinsic, "mechanics_efficiency": r["mechanics_efficiency"], "distress": r["distress"],
           "rr": r["rr"], "paco2": r["paco2"], "ph": r["ph"], "W": r["W"], "spo2": r["spo2"], "hr": r["hr"],
           "hr_if_intrinsic_80": hr_80, "authored": {"rr": float(t["respiratory_rate"]), "paco2": float(t["abg_paco2"]),
                                                     "ph": float(t["abg_ph"]), "hr": float(t["hr"]),
                                                     "spo2": float(t["spo2"])},
           "rr_without_distress": unset["rr"], "hr_without_distress": unset["hr"],
           "mechanics_off_refused": sm_refused(case, intrinsic, d, k, rho, g_rr)}
    out["hr_share_not_explained_bpm"] = out["authored"]["hr"] - out["hr"]
    out["supported"] = (abs(out["rr"] - out["authored"]["rr"]) < 1e-9 and abs(out["paco2"] - out["authored"]["paco2"]) < 1e-6
                        and abs(out["ph"] - out["authored"]["ph"]) < 0.01 and out["hr"] <= out["authored"]["hr"] + 1e-9
                        and out["hr"] > out["hr_without_distress"] and out["rr"] > out["rr_without_distress"]
                        and out["spo2"] == out["authored"]["spo2"] and out["mechanics_off_refused"])
    return out


def sm_refused(case, intrinsic, d, k, rho, g_rr) -> bool:
    """P2T-1A's M1 holds: the same witness with the mechanics candidate off is refused."""
    try:
        dv.arrival_state(witness_anchors(case, intrinsic, d), witness_profile(k, rho, g_rr, mechanics=False))
    except CoreInvariantError:
        return True
    return False


# P2T-3-5 / -6 / -12 / -13 / -8: structural courses at the MID witness (direction only) ------------------------------------

@dataclass(frozen=True)
class SyntheticAsthmaDistress(Contributor):
    """SYNTHETIC_ONLY asthma distress evolution (direction only; no kinetics approved, not registered): between the two
    minutes it moves the distress a fraction of the way to an explicit target and, at the last minute, by exactly the
    remaining difference from the current state (no repeated decimal deltas; ACCUMULATED_FLOAT_CANCELLATION_DEBT)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2t3_probe_asthma_distress"

    id: str
    target: float
    fraction_per_min: float
    from_minute: int
    to_minute: int

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.from_minute < minute <= self.to_minute:
            return Contribution()
        gap = self.target - state.aux.respiratory_distress
        amount = gap if minute == self.to_minute else self.fraction_per_min * gap
        return Contribution(distress=(DistressChange(amount, self.source, minute,
                                                     "probe: asthma distress toward an explicit target"),))


@dataclass(frozen=True)
class SyntheticAsthmaVQ(Contributor):
    """SYNTHETIC_ONLY direct G (V/Q mismatch worsening) through the existing G interface; never L, never L_rev."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2t3_probe_asthma_vq"

    id: str
    per_min: float

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(deltas=(ChannelDelta(Channel.G, self.per_min, self.source, minute,
                                                 "probe: asthma V/Q mismatch worsening (direct G)"),))


def _course(items, a, p, minutes=COURSE_MINUTES):
    state, states, records = dv.arrival_state(a, p), [], []
    states.append(state)
    for _ in range(minutes):
        state, rec = step(state, tuple(items), a, p)
        states.append(state)
        records.append(rec)
    return states, records


def courses(found_witnesses: dict) -> dict:
    w = found_witnesses["MID"]
    c = _constants()
    out = {}
    for case in sr.CASES:
        cw = w["cases"][case]
        a = witness_anchors(case, cw["intrinsic_rr"], cw["distress"])
        p = witness_profile(w["k"], w["rho"], w["g_rr"])
        read = lambda s: dm.reading(s, a, p)                                        # noqa: E731
        plain = [read(s) for s in _course((), a, p)[0]]
        worse_states, worse_records = _course((sm.obstruction(OBSTRUCTION_RATE),), a, p)
        worse = [read(s) for s in worse_states]
        relief_probe = mc.SyntheticMechanics("p2t3-relief", RELIEF["factor_per_min"], RELIEF["from_minute"],
                                             RELIEF["to_minute"])
        relieved = [read(s) for s in _course((relief_probe,), a, p)[0]]
        target = DISTRESS_RELIEF["target_fraction"] * cw["distress"]
        calm_states, calm_records = _course((SyntheticAsthmaDistress("p2t3-calm", target, DISTRESS_RELIEF[
            "fraction_per_min"], DISTRESS_RELIEF["from_minute"], DISTRESS_RELIEF["to_minute"]),), a, p)
        calm = [read(s) for s in calm_states]
        vq = [read(s) for s in _course((SyntheticAsthmaVQ("p2t3-vq", G_PROBE_PER_MIN),), a, p)[0]]
        end, t = COURSE_MINUTES, DISTRESS_RELIEF["to_minute"]
        out[case] = {
            "untreated": {"E_down": worse[end]["mechanics_efficiency"] < plain[end]["mechanics_efficiency"],
                          "rr_unchanged_by_obstruction": all(x["rr"] == y["rr"] for x, y in zip(worse, plain)),
                          "paco2_up": worse[end]["paco2"] > plain[end]["paco2"],
                          "distress_unchanged_by_obstruction": all(x["distress"] == y["distress"]
                                                                   for x, y in zip(worse, plain)),
                          "family_writes_mechanics_only": all(
                              not r.distress and all(d.source.kind is SourceKind.CORE_COUPLING for d in r.deltas)
                              and {m.source.key for m in r.mechanics} == {"disease_module:asthma-obstruction"}
                              for r in worse_records),
                          "at": {m: {k: worse[m][k] for k in ("rr", "paco2", "W", "mechanics_efficiency", "hr", "spo2")}
                                 for m in (0, 30, end)}},
            "mechanics_relief": {"W_up_paco2_down": relieved[RELIEF["to_minute"]]["W"] > plain[RELIEF["to_minute"]]["W"]
                                 and relieved[RELIEF["to_minute"]]["paco2"] < plain[RELIEF["to_minute"]]["paco2"],
                                 "distress_rr_hr_unchanged": all(x["distress"] == y["distress"] and x["rr"] == y["rr"]
                                                                 and x["hr"] == y["hr"]
                                                                 for x, y in zip(relieved, plain)),
                                 "status": "BRONCHODILATOR_WRITER_DEFERRED: relief through the common mechanics target "
                                           "only (SYNTHETIC_ONLY); no mechanics -> distress coupling"},
            "distress_relief": {"exact_target": calm[t]["distress"] == target,
                                "rr_down": calm[t]["rr"] < plain[t]["rr"], "hr_down": calm[end]["hr"] < plain[end]["hr"],
                                "mechanics_unchanged": all(x["mechanics_efficiency"] == y["mechanics_efficiency"]
                                                           for x, y in zip(calm, plain)),
                                "paco2_up_with_less_ventilation": calm[t]["paco2"] > plain[t]["paco2"],
                                "writes": sorted({d.source.key for r in calm_records for d in r.distress}),
                                "status": "SYNTHETIC_ONLY direction probe; kinetics UNSET"},
            "direct_g": {"spo2_down": vq[end]["spo2"] < plain[end]["spo2"], "L_zero": all(x["L"] == 0.0 for x in vq),
                         "rr_paco2_unchanged": all(x["rr"] == y["rr"] and x["paco2"] == y["paco2"]
                                                   for x, y in zip(vq, plain)),
                         "status": "DIRECT_G_STRUCTURAL_PROBE_ONLY (SYNTHETIC_ONLY); arrival G anchored (0); "
                                   "HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED"}}
        u = out[case]
        u["pass"] = (all(v for k, v in u["untreated"].items() if k != "at") and u["mechanics_relief"]["W_up_paco2_down"]
                     and u["mechanics_relief"]["distress_rr_hr_unchanged"] and u["distress_relief"]["exact_target"]
                     and u["distress_relief"]["rr_down"] and u["distress_relief"]["hr_down"]
                     and u["distress_relief"]["mechanics_unchanged"] and u["direct_g"]["spo2_down"]
                     and u["direct_g"]["L_zero"] and u["direct_g"]["rr_paco2_unchanged"])
    out["pass"] = all(out[cs]["pass"] for cs in sr.CASES)
    return out


# P2T-3-11 / normalization / orthogonality / no optimization ------------------------------------------------------------------

def scale_invariance(found_witnesses: dict, found_region: dict) -> dict:
    w = found_witnesses["MID"]
    rows = {}
    for lam in LAMBDAS:
        r = {}
        for case in sr.CASES:
            cw = w["cases"][case]
            a = witness_anchors(case, cw["intrinsic_rr"], lam * cw["distress"])
            p = witness_profile(w["k"], w["rho"], w["g_rr"] / lam)
            reading = dm.at_arrival(a, p)
            r[case] = {k: reading[k] for k in ("rr", "hr", "paco2", "ph", "spo2", "W")}
        rows[f"{lam:g}"] = r
    base = rows["1"]

    def diff(lams):
        return max(abs(rows[f"{lam:g}"][cs][k] - base[cs][k]) for lam in lams for cs in sr.CASES for k in base[cs])

    exact = diff([lam for lam in LAMBDAS if math.log2(lam).is_integer()])
    other = diff([lam for lam in LAMBDAS if not math.log2(lam).is_integer()])
    scale = max(abs(v) for cs in sr.CASES for v in base[cs].values())
    # The region in invariant terms: rho = g_HR / g_RR and d(24f) / d(49m) do not involve the normalization.
    k1 = found_region["points"][f"{K_POINTS[1]:.6g}"]["at"]["mid"]["asthma"]
    ratio = {f"{lam:g}": {"d49": lam, "d24": [lam * k1["d24"][0], lam * k1["d24"][1]],
                          "d24_over_d49": [lam * k1["d24"][0] / lam, lam * k1["d24"][1] / lam]} for lam in LAMBDAS}
    return {"rows": rows, "powers_of_two_max_abs_difference": exact, "other_max_abs_difference": other,
            "roundoff_bound": 16 * math.ulp(scale), "d24_over_d49_by_lambda": ratio,
            "statement": "outputs depend on g_RR d and g_HR d only (two readers, no other reader of d): (lambda d, g / "
                         "lambda) is the same physiology; rho and d(24f) / d(49m) are invariant",
            "pass": exact == 0.0 and other <= 16 * math.ulp(scale) and all(all(math.isclose(a, b) for a, b in zip(v["d24_over_d49"], k1["d24"]))
                                         for v in ratio.values())}


def orthogonality(found_region: dict, found_witnesses: dict) -> dict:
    """Distress and mechanics are separate latent states: inside the region one moves while the other stays, and the core
    reads neither from the other."""
    c, ev = _constants(), evidence()
    t24 = sr.truth(SECONDARY)
    rows = rows_at(K_POINTS[0], ev, existing_targets(), c)
    # 24f at one fixed intrinsic RR (one mechanics efficiency): distress moves with k (acid share) at fixed E.
    i_fixed = 16.0
    e_fixed = sr.implied_efficiency(t24, i_fixed)
    fixed_e = {f"{k:.6g}": drive_needed(34.0, i_fixed, c) - k * rows[SECONDARY]["burden"] for k in K_POINTS}
    # 24f at one fixed distress product: the mechanics efficiency moves with k and the intrinsic RR.
    x_fixed = 20.0
    fixed_d = {f"{k:.6g}": sr.implied_efficiency(t24, intrinsic_for(34.0, x_fixed, rows[SECONDARY]["burden"], k, c))
               for k in K_POINTS}
    w = found_witnesses["MID"]["cases"]
    p2t1 = dm.orthogonality()["pass"]
    audit = sorted(mc._names(mc._functions(xm._live("clinical_core/derived.py"))["_composition"])
                   & {"mechanics_efficiency", "W", "ventilation"})
    out = {"secondary_distress_at_fixed_mechanics": {"E": e_fixed, "x_by_k": fixed_e},
           "secondary_mechanics_at_fixed_distress": {"x": x_fixed, "E_by_k": fixed_d},
           "witness": {cs: {"E": w[cs]["mechanics_efficiency"], "d": w[cs]["distress"]} for cs in sr.CASES},
           "both_differ": (w[PRIMARY]["mechanics_efficiency"] < w[SECONDARY]["mechanics_efficiency"]
                           and w[PRIMARY]["distress"] > w[SECONDARY]["distress"]),
           "p2t1_orthogonality_live": p2t1, "composition_reads_mechanics": audit,
           "coupling": "no mechanics -> distress coupling (UNSET, off); distress is never f(mechanics_efficiency)"}
    out["pass"] = (len(set(round(v, 9) for v in fixed_e.values())) == len(K_POINTS)
                   and len(set(round(v, 9) for v in fixed_d.values())) == len(K_POINTS)
                   and out["both_differ"] and p2t1 and not audit)
    return out


FORBIDDEN_FIT_NAMES = ("minimize", "least_squares", "argmin", "curve_fit", "optimize", "loss", "posterior", "best")


def no_optimization() -> dict:
    tree = ast.parse((ROOT / OWN[0]).read_text(encoding="utf-8"))
    names = {getattr(n, "id", getattr(n, "attr", None)) for n in ast.walk(tree) if isinstance(n, (ast.Name, ast.Attribute))}
    imports = sorted({a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
                     | {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                        and n.level == 0})
    used = sorted(n for n in names if n and any(f in n.lower() for f in FORBIDDEN_FIT_NAMES))
    out = {"imports": imports, "fit_names": used, "witness_rule": {k: list(v) for k, v in WITNESS_RULE.items()},
           "witnesses_after_nonempty": True, "region_carried_as_intervals": True}
    out["pass"] = not used and not set(imports) & {"scipy", "numpy", "sklearn", "statistics"}
    return out


# Controls, heart rate, hypoxaemia, consciousness, collapse, legacy ---------------------------------------------------------------

#: The authored RR is an integer count per minute: +/- 0.5 is its observation resolution (not a clinical tolerance).
RR_RESOLUTION = 0.5
ACS_INTRINSIC_HR = gi_reference.RESTING_HR[1]


def zero_admissible(case: str, k: float, ev: dict) -> bool:
    """Whether the acid drive alone reaches the authored RR (within its resolution) at some intrinsic RR in the band."""
    c, t = _constants(), ev["cases"][case]
    if t["family"] == "opioid":
        return True                              # central availability not authored: any RR below intrinsic is reachable
    burden = max(0.0, c["hco3_ref"] - t["hco3"])
    low = drive_needed(t["rr"] - RR_RESOLUTION, min(I_RR[1], t["rr"]), c) - k * burden
    high = drive_needed(t["rr"] + RR_RESOLUTION, I_RR[0], c) - k * burden
    return low <= 0.0 <= high


def cross_family(found_region: dict) -> dict:
    ev, c = evidence(), _constants()
    out = {}
    for key, pt in found_region["points"].items():
        if not pt["nonempty"]:
            out[key] = {"nonempty": False}
            continue
        rows, mid = pt["rows"], pt["at"]["mid"]
        chosen = mid["order"]["chosen"]
        rho = mid["rho"]
        floors = mid["order"]["floors"]
        row = {"rho_binding": pt["bounds"]["binding"], "effective_rho": pt["effective"]}
        for case in CROSS_FAMILY:
            r = rows[case]
            row[case] = {"x": r["x"], "y": r["y"], "role": r["role"], "chosen_x_at_mid": chosen.get(case),
                         "compatible": case in chosen}
        for case in CONTROLS:
            r = rows[case]
            row[case] = {"x": r["x"], "distress_zero_admissible": zero_admissible(case, float(key), ev),
                         "normalized_floor": r["x"][0] / mid["asthma"]["x49"][1]}
        for case in ANAPHYLAXIS:
            r = rows[case]
            need = floors[1]                  # the Mildly-increased tier's floor: the least the order asks of 'Increased'
            row[case] = {"x": r["x"], "least_required": need, "acid_overshoot": r["acid_overshoot"],
                         "forced_overprediction": r["acid_overshoot"] or need > r["x"][1]}
        r = rows[ACS_RESIDUAL]
        least = max(r["x"][0], floors[0])
        residual = target_needed(ev["cases"][ACS_RESIDUAL]["hr"], ACS_INTRINSIC_HR, c) - r["existing_target"]
        row[ACS_RESIDUAL] = {"x": r["x"], "least_admissible_x": least, "residual_target_at_intrinsic_80": residual,
                             "share_of_residual_at_least_distress": rho * least / residual,
                             "not_closed": rho * least < residual,
                             "status": "SYSTEMIC_STRESS_DEFERRED: the least distress the evidence and RR admit explains a "
                                       "small share of the residual; respiratory distress is not used to close it"}
        out[key] = row
    out["pass"] = all(all(v[c]["compatible"] for c in CROSS_FAMILY) and all(v[c]["distress_zero_admissible"]
                                                                              for c in CONTROLS)
                      and not any(v[c]["forced_overprediction"] for c in ANAPHYLAXIS)
                      and v[ACS_RESIDUAL]["not_closed"]
                      for k, v in out.items() if k != "pass" and v.get("nonempty", True))
    return out


def heart_rate(found_witnesses: dict) -> dict:
    rows = {label: {cs: {k: found_witnesses[label]["cases"][cs][k] for k in
                         ("hr", "hr_without_distress", "hr_if_intrinsic_80", "hr_share_not_explained_bpm")}
                    for cs in sr.CASES} for label in WITNESS_RULE}
    return {"rows": rows, "authored": {cs: float(sr.truth(cs)["hr"]) for cs in sr.CASES},
            "treatment": "COMPATIBILITY / UPPER-BOUND: distress may explain part of the tachycardia; the remainder is the "
                         "incompletely authored beta-agonist exposure and other arousal, not modelled "
                         "(BETA_AGONIST_HR_EFFECT_UNSET; SYSTEMIC_STRESS_DEFERRED)",
            "pass": all(found_witnesses[lab]["cases"][cs]["hr"] <= float(sr.truth(cs)["hr"]) + 1e-9
                        for lab in WITNESS_RULE for cs in sr.CASES)}


def hypoxaemic_sensitivity(found_region: dict) -> dict:
    if not found_region["nonempty"]:
        return {"performed": False, "reason": "the primary region failed; hypoxaemia is never used to rescue it"}
    alt = region(hypoxaemic_gain=HYPOXAEMIC_SENSITIVITY_GAIN)
    return {"performed": True, "gain": HYPOXAEMIC_SENSITIVITY_GAIN, "label": "SENSITIVITY_ONLY (P2P-2 SYNTHETIC_ONLY)",
            "primary": found_region["rho_conditional"], "with_hypoxaemic": alt["rho_conditional"],
            "still_nonempty": alt["nonempty"], "used_for_the_verdict": False}


def consciousness(found_witnesses: dict) -> dict:
    w = found_witnesses["MID"]["cases"][PRIMARY]
    a = witness_anchors(PRIMARY, w["intrinsic_rr"], w["distress"])
    p = witness_profile(found_witnesses["MID"]["k"], found_witnesses["MID"]["rho"], found_witnesses["MID"]["g_rr"])
    states = _course((sm.obstruction(OBSTRUCTION_RATE),), a, p)[0]
    levels = sorted({dv.derive(s, a, p).consciousness_level for s in states})
    return {"authored": {cs: sr.truth(cs)["mental_status"] for cs in sr.CASES}, "core_levels": levels,
            "status": ["HYPERCAPNIA_SIGNAL_STRUCTURALLY_SUPPORTED_BOUNDS_NOT_IDENTIFIABLE", "CONSCIOUSNESS_INTEGRATION_DEBT",
                       "P2L-2 not integrated; 49m's drowsiness is diagnostic only"],
            "pass": len(levels) == 1}


def collapse() -> dict:
    found = sm.collapse()
    return {"p2s3_structural_collapse": found, "status": "STRUCTURAL_ONLY: no asthma-specific rule, no threshold",
            "pass": found["pass"]}


def legacy(found_witnesses: dict) -> dict:
    """LEGACY_REFERENCE_ONLY, read last: the family engine's untreated rows as P2S-3 froze them (frozen evidence reused)."""
    rows = json.loads(sm.RECORD.read_text(encoding="utf-8"))["legacy"]
    w = found_witnesses["MID"]["cases"]
    classes = {
        "rr": "RESOLVED_AT_ARRIVAL: the core now carries the authored RR through the distress region (P2S-3's "
              "COMMON_DRIVE_GAP); the legacy's RR drift with time is not authored and not fitted",
        "paco2": "MODEL_DERIVED: the core's PaCO2 is the P2S-2 mechanics' (authored at arrival); the legacy has none",
        "spo2": "EXPECTED_EXTENSION: the legacy moves SpO2 with obstruction; the core keeps the arrival SpO2 "
                "(HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED)",
        "hr": "COMPATIBILITY: the core explains part of the arrival tachycardia; the legacy's bronchodilator HR is not "
              "migrated (BETA_AGONIST_HR_EFFECT_UNSET)",
        "fatigue_obstruction_drift": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: neither is authored; no fatigue memory",
        "consciousness": "CONSCIOUSNESS_INTEGRATION_DEBT: the core's level does not read PaCO2",
        "deterioration_timing": "NOT_AUTHORED: not fitted"}
    return {"legacy_rows": rows, "core_arrival": {cs: {k: w[cs][k] for k in ("rr", "hr", "spo2", "paco2")}
                                                   for cs in sr.CASES},
            "classes": classes, "used_for_parameters": False}


def parameters() -> dict:
    committed = {**{k: v for k, v in dm.committed_profiles().items()}, "asthma_p2t3": profile()}
    unset = {name: (p.distress_to_respiratory_drive_gain is None and p.distress_to_sympathetic_gain is None
                    and p.hypoxaemic_drive_mapping is None and p.hypoxaemic_to_drive_gain is None)
             for name, p in committed.items()}
    profile_fields = {f.name for f in fields(dv.CoreProfile)} - set(dm._class_fields(xm.p2t1_text(
        "clinical_core/derived.py"), "CoreProfile"))                            # fields added since P2T-1 (none)
    out = {"committed_profiles_unset": unset,
           "new_profile_fields": sorted(profile_fields),
           "beta_agonist_parameter": sorted(n for n in {f.name for f in fields(dv.CoreProfile)} if "agonist" in n),
           "systemic_stress_parameter": sorted(n for n in profile_fields if any(t in n.lower() for t in
                                                                                dm.SYSTEMIC_STRESS_TOKENS)),
           "committed_arrival_distress": {cs: sr.anchors(cs).arrival_respiratory_distress for cs in sr.CASES},
           "still_unset": ["distress_to_respiratory_drive_gain", "distress_to_sympathetic_gain",
                           "numeric arrival distress (any case)", "WOB -> distress mapping", "mechanics -> distress coupling",
                           "hypoxaemic drive gain and mapping", "beta-agonist HR effect", "systemic_stress gains",
                           "bronchodilator / distress kinetics"]}
    out["pass"] = (all(unset.values()) and not out["beta_agonist_parameter"] and not out["systemic_stress_parameter"]
                   and all(v == 0.0 for v in out["committed_arrival_distress"].values()))
    return out


def non_regression() -> dict:
    with p2t1a_view():
        p2t1a = xm.run()
    record = json.loads(xm.RECORD.read_text(encoding="utf-8"))
    out = {"p2t1a_record_reproduced_on_its_tree": json.loads(json.dumps(p2t1a, sort_keys=True, default=str)) == record,
           "p2t1a_record_untouched": hashlib.sha256(xm.RECORD.read_bytes()).hexdigest() == P2T1A_RECORD_SHA,
           "p2s3_record_untouched": hashlib.sha256(sm.RECORD.read_bytes()).hexdigest() == dm.P2S3_RECORD_SHA,
           "p2s3_classification": "ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_DRIVE_GAP; "
                                  "P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT (carried, not rewritten)",
           "asthma_profile_mechanics_on": profile().respiratory_mechanics}
    out["pass"] = all(v for k, v in out.items() if k != "p2s3_classification")
    return out


# The proof: the P2T-1A tree plus this package's two tuple entries ------------------------------------------------------------

P2T1A_HEAD = "a2e6227"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/respiratory_distress.py", '
                                     '"clinical_core/respiratory_distress_report.py",\n'
                                     '                        "clinical_core/distress_closure.py", '
                                     '"clinical_core/distress_closure_report.py",\n'
                                     '                        "clinical_core/asthma_distress_migration.py",\n'
                                     '                        "clinical_core/asthma_distress_migration_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/respiratory_distress.py", '
                                     '"clinical_core/respiratory_distress_report.py",\n'
                                     '                        "clinical_core/distress_closure.py", '
                                     '"clinical_core/distress_closure_report.py")\n'
                                     '\n'),),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/respiratory_distress_report.py",\n'
                                     '                      "clinical_core/distress_closure_report.py",\n'
                                     '                      "clinical_core/asthma_distress_migration_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/respiratory_distress_report.py",\n'
                                     '                      "clinical_core/distress_closure_report.py")\n'
                                     '\n'),)}
CORE_AT_P2T1A = {'clinical_core/decision_pack.py': 'd34fe1ff51cd387bca2dfe56ced994729c7aeca06d05f4f47f28c3275c058be8',
 'clinical_core/lactate_slice.py': 'f3b13db5dc44978c59951a256f7c75ba06e5d4e72af024df14182c026c742bf6'}
# </reversal>
# <common>
COMMON_AT_P2T1A = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
 'clinical_core/a9.py': '64006b57e37ab69dd9dfd61d5c87b01112779f19e7007b96440cfad345ad5b92',
 'clinical_core/acid_base.py': '9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954',
 'clinical_core/acid_base_report.py': '9f0b9f5b03369066e4ac7916b372453c41ef7793b36c20553b88d726b83afa78',
 'clinical_core/acs_migration.py': '4fae25400e94b7c1f3b6b77f277dd5e04b72d150c52da738faddf95b37edd971',
 'clinical_core/acs_migration_report.py': 'dbe33c01e165f9471dcb720919c3fac257f3d0903972117a420e91632b4c2d6b',
 'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/arrival_severity.py': 'c5c0e4c125303b463ec1d2a5373464c09576f7d83ca975834e6b059c67b2b229',
 'clinical_core/arrival_severity_report.py': 'a1806dc772a4f0a540a621271e8dd24b4c77b36da2b55af5e1da623cf30ac2eb',
 'clinical_core/asthma_migration.py': 'ddbbfb562a93595985fe189c2d88e7a05a845ca7cee02282cca90f56dd044ca8',
 'clinical_core/asthma_migration_report.py': 'f9580ac9d821e4ba33e202f664b0de076df0fe5fb3c0d3792eae8decd26d1880',
 'clinical_core/asthma_reference.py': 'b6ed2ee6a495d8868a2cbb3039ecb3d7a8876928ad02e0eaeb4d90d699c1dcbe',
 'clinical_core/bands.py': '9facbd34dc643d45f7ad3d668619f344717824c921924247f65396fae6aa81bc',
 'clinical_core/baroreflex.py': 'cd9072b8c97bfc3a15e8d314c88aae7ec6a622a8c4b7e1fad9fa73c38e5aca6e',
 'clinical_core/baroreflex_report.py': '0044b585240c36e9fd5e049c394f053f443d1408c23c77299d9cc5a65efef405',
 'clinical_core/blood_anchors.py': 'bd870314a723dc420ef6d27189275cb3a2b4bba0fd3515fac166c017fb69b89e',
 'clinical_core/blood_constraints.py': '2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8',
 'clinical_core/blood_extension.py': '87429c2ed0b453bb33b2107fdfa453ffe6d78e5ffbb26364eab7e8228556ce47',
 'clinical_core/blood_extension_report.py': '028efe15446ddc8d9b424465cbcdb74732f00361efea09de3225cea9f3bbde54',
 'clinical_core/blood_filter_report.py': '4667b87efb27cfef4a1f705c9767bb6dd311d6c67625b9505dead9ef3293c394',
 'clinical_core/blood_fluid_calibration.py': '46e73e3314190dd6fc18695346a16e9c6c55059606ac80a16081695f1d9fdd19',
 'clinical_core/blood_fluid_readiness.py': '40b93a69c8b70190e7d92a056f0987b81a30ee32331629d18132f0aa534a15cf',
 'clinical_core/blood_fluid_readiness_report.py': '8bcf365b433ba584760775d23a23bbf4b750e6f2253b67fcf818df2a679dc650',
 'clinical_core/blood_fluid_report.py': '6ba467991a3e7ac9c8193f1ecff225541c069c89073872e8dc4ffca4487edc0a',
 'clinical_core/blood_fluid_tau_closure.py': 'c16a56a77c3957ae1186f4e2b016ddbadd8fee7bae0d405414fb031af735621b',
 'clinical_core/blood_fluid_tau_closure_report.py': '16d703dfa0ecf52a29763d7a94a4dc0534ae1ff886021444e4884d3a0477af46',
 'clinical_core/blood_probes.py': '846de76dbfe99f3dd7fc6ace431dc1d1325441e13bc0c1148c009f33016bf3d5',
 'clinical_core/blood_rate_boundary.py': '435db3cf1d1fdba4e9ff059b889a2e8180ca80db1d2fdbeff433663692ee9f83',
 'clinical_core/blood_rate_report.py': '3bcf35d15d3611f2564e23bf0392703bd31236c21ff128836c6201b45e6e380f',
 'clinical_core/calibration.py': 'f3fa65375ddaa48bac9ecf850838c78606bb46c3a15f12f968b146b84592ace5',
 'clinical_core/collapse.py': '6076dd315f8bd335af8a425ac4d78e3bcbbd5f1198b45e511b4f122532d65fc9',
 'clinical_core/collapse_architecture.py': '0d6ed0d28695c016c1834bd931e4bfbcac561b8d94c70f8d316c999d3e2d6699',
 'clinical_core/collapse_architecture_report.py': '3b116d0a28933ccbbc2c5f45c97d1cdfb822bee5f79a4877320bd67464c6ebbf',
 'clinical_core/collapse_audit.py': '7c1fb59a26bfda77ba84e0a38640e3aabcccdf69d41b222e93ad48cf414e1521',
 'clinical_core/collapse_audit_report.py': '08b63fa519e985eea0619becdd5d9b21bb92b0e8def1f72a4d89d34847af5061',
 'clinical_core/comparison.py': 'fd1dbb232399f6eae33cfe758670b80a551161fea183e5dd4820575636a2b0d4',
 'clinical_core/consciousness_audit.py': '534bc27d96f7ffd31da70e9ff90ffdf92e82c62fe8e015fb3fd6df040885fe8c',
 'clinical_core/consciousness_audit_report.py': '8f769dbafb2b76a6013b518038f842aa3d23be482a6ff7d355472ca75eaa0e53',
 'clinical_core/contracts_input.py': '2185469e423f2104ec81705849e57d6fffe01a316f1a7b35eba6883467f89117',
 'clinical_core/contracts_legacy.py': '1afe36c5ccbf07df3f3e632916fd083d0fcfc8258ede6bf56eef70fb98f7d80a',
 'clinical_core/contracts_output.py': 'bc7371c7ccb57ea2f138a6bbc58c266851f6dbf0fbdb5eb2d625b1ea70ab3751',
 'clinical_core/contracts_shadow.py': 'bd2fc07a7b91f05c89c96294f440b0510c2896a7666cb77fd97a5bdab001cf65',
 'clinical_core/decision_pack_markdown.py': 'e0f9471a8e21284a1cf8976b3d7f89002d0d4fb023d02c087240d45ef6836328',
 'clinical_core/derived.py': '6ebc433e0e6373c605caa465f2f71f3940f55011e7b52ccf1d52fea001c15368',
 'clinical_core/distress_closure.py': '17831ecad1a43acf6364d618938ceca3835347b37b7d8c2593e76909f794740b',
 'clinical_core/distress_closure_report.py': 'c91cdc709da5c3b3babb3bff7e05331c6d505b4314c133d3f5c75f71a94a359f',
 'clinical_core/edema_migration.py': '7d2bd34a883c0253aed4d254f025b400bf178346e348fd3982986c228ef2b464',
 'clinical_core/edema_migration_report.py': '02c20561397d1d4ab7b9a83e1e1be1ce8abe5b027a7f8679cd5ba9af0b418467',
 'clinical_core/edema_reference.py': 'fd8702e4d5ed03cf6dbe72cf0053ad9af6966e40e2b197cf42261bf61a66eb76',
 'clinical_core/embolism_migration.py': '1f67472c5fa7079989973f11cb2df356ef048efa3d64acad97ca02b38650c22f',
 'clinical_core/embolism_migration_report.py': 'ad307663a3f2f73fbde5d771cbfc57896cddf5d43f5a3e291e52ade3ce448b0c',
 'clinical_core/embolism_reference.py': '55ecc2418844c05185d8e933d3c62456da31fd73c7704a6877c396f221469d74',
 'clinical_core/encephalopathy.py': '04aea64d6f2a23cf5a77a530114b3174eab9c9adc527708a97ac25f9c5ce3539',
 'clinical_core/encephalopathy_architecture.py': '55d47c033d381fb2b1cb69fab67adb27a05d7393807575561bc8d7a4d5e58a2c',
 'clinical_core/encephalopathy_architecture_report.py': 'e35278b85196763ef1b87f30acb19c20d8dc5a007cdc55dad266bcf07b0c990a',
 'clinical_core/faculty_constraints.py': '092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a',
 'clinical_core/gas_exchange_architecture.py': 'b9dcfe241f91e0ef973ca77b32e149b0ddbc76ac09f19092f7cfca5a16601835',
 'clinical_core/gas_exchange_architecture_report.py': '2a4a589ae2c40f7ffa856a7daf4405c066ed26998d5f25a849cc59646742dd48',
 'clinical_core/gi_reference.py': 'ee3114ce9eeeb426a7b843943819aa88095b6cb09674e4c895c93a6ad1de0867',
 'clinical_core/haemorrhage_probes.py': 'df55cdcd16e5ea091a0b27042c22723029c9f19722a332c98c64bf606ef2df00',
 'clinical_core/hemodynamic_probes.py': '1e6e96a0397f379aa4a8112aef8198963b9120fd239d2444c22ad2db22ea2ebb',
 'clinical_core/hr_envelope_filter.py': '6bfe0ef46ed1f2b1a4555b7322ca7d3747c237f2cc185caf3dcd479e8a50d885',
 'clinical_core/hr_envelope_filter_report.py': 'e85579aed3751aafb11cc9a5abd5b38176c2bc126692384db80192cf787232bf',
 'clinical_core/hr_observables.py': '47c21f35d7a38ccee60df3df2053edcc776e86d8fdeb5ff8881bf4e105764f05',
 'clinical_core/hr_observables_report.py': '705578a792a9aeb28aaf75cd1f47b61254f55f381df325b010f33fa03d3d4a9f',
 'clinical_core/hr_primary.py': 'f9c5807fb6ddb6f2ced9ee8b209a047eed60b229ba450ccde56454cb0d8812f9',
 'clinical_core/hr_primary_report.py': '9551cab1a2e068a2c6cfb977160bae38d50bb96b17335504a47176d25144cf92',
 'clinical_core/hr_shock.py': '2fbf78d2ed5a0fd0592ef48b90fd4dc385a5c27c6fd523b1dbc195ae2ca2b419',
 'clinical_core/hr_shock_report.py': '64043971e9d2404924dc3251e53c52b5ddc356cdff9a367ce9d0ba48a483e9c5',
 'clinical_core/hr_structure.py': '1109ca9dded7b8e67c588932326f510e10e0ad51f6091f0a17fe9ef09f218f16',
 'clinical_core/hr_structure_report.py': 'bdf83176d06b212a877a423724425dcbbe18287d823fec84a13a6c0d87a0d384',
 'clinical_core/integration.py': '8640b4621cb2d6946d4606f9938f9310c7481d5866d919070bb7b89e6b193c0f',
 'clinical_core/interventions/__init__.py': 'd0dedb08f0d35bff6ba458af009b3a35f85018e9ea2a76373158d9c373551b79',
 'clinical_core/interventions/fluids.py': '7dc615d2eea80e3afdab0774bb1f234f7ea887be1654ae02e6ca312513fb9aef',
 'clinical_core/interventions/modifiers.py': '46c8970630a77960d7ba2e81023d31b96b2b08f611a87eae9f94cb85f1b1aa6a',
 'clinical_core/interventions/oxygen.py': 'd7bcc0393ed562d02d6070f09ab8d501c506e6931f5efd33b3492d7e34664095',
 'clinical_core/interventions/timing.py': '498493e6143d691d582b68f568491b9275eef49bb13bcf94e251f17aea49c6a1',
 'clinical_core/lactate_adequacy.py': 'ec49d1da4ca2494d804605669fe59617f7a1d7841572ae4be9f2e6e2b6ef7638',
 'clinical_core/lactate_adequacy_report.py': '4f50500d46ea3a4eb1aebc545f718a8e7f78ea77f532041736fbd4cd54881044',
 'clinical_core/lactate_closure.py': '2ae56c334031da561a9d402795c1a81ec70646ea15ed0e71cc8b6991bc04dbc3',
 'clinical_core/lactate_closure_report.py': 'e8a62c16b97d9800a357150e69f9ecb97ad0a8796f1db2c31a7c2995ee267b3f',
 'clinical_core/lactate_constraints.py': 'cf9522168fd7012e52ca797752ce8d5ab9456db7ff54422f917ccf0628d021be',
 'clinical_core/lactate_rebuild.py': 'd969a8c89b678204b4b258c35731f64b0e87ef3cf97b80ef5b92b073ccc9733f',
 'clinical_core/lactate_rebuild_report.py': '22948e39f94661d3ef66e7a129be1be8cbded1dc124ff581fbf9b9144c56b162',
 'clinical_core/legacy_adapter.py': 'f8fafd17bcda03a4293e5717145c6f4672760a07d553c965fa7c2505b69ad115',
 'clinical_core/logistics.py': '8b7b28c7cee688d38bbaa124e9bc83f760e3b952d7f34b0df0cf6ba6159855b9',
 'clinical_core/lung_water_reference.py': '23a6f40d17dcf51bd1fa42ec4dc5151297c4f3a47fed241b2edaec64f069ddff',
 'clinical_core/lung_water_reference_report.py': '1c7da3d2797237e24dbd085edcf2780a4b26f1fbc9658bf383982a910e1c289f',
 'clinical_core/migration.py': 'aa5d5c8001514994dda67a8dbfbf60e18f9048e1b18edc599ddf0399f80b349e',
 'clinical_core/migration_authority.py': 'baf342106c2a611ddc5b8f43e75a9726c11ce1a53465c5bd3d2761a0e9a8f907',
 'clinical_core/modules/__init__.py': '1cf73c2ddf4fe370c8d34fff2ea8132149c02239ee81f3329bd87cfec729f23d',
 'clinical_core/modules/acs_ischaemia.py': '3199b9173594aea07c905e55b46e8705621b5c9ed7e936987024aa2d2079993d',
 'clinical_core/modules/asthma.py': '44cbb45b5781d85c927c66892377518d9c15244deafc58ed66ef6e391f26af6d',
 'clinical_core/modules/gi_haemorrhage.py': 'edb61d903bc9f4607c1d3b819f28ac065ba86656b75ba29c89d3a7c124777673',
 'clinical_core/modules/pulmonary_edema.py': '01e68556c919efa24ff6186eacf22c98e2ec882bf5cd52109bbafaffd8351679',
 'clinical_core/modules/pulmonary_embolism.py': '147881394c9208b35e2e2fdb7bb0ab42d589785000784379a8b1c1460df204c7',
 'clinical_core/modules/rhythm_events.py': '1036a2443e44fe5e2fde80736984b6828542b69454cc49a36e660ee8d436c86b',
 'clinical_core/oxygen_probes.py': '450cec663ae0c47ba32b6df8b4fadc136cad6c9a2e14f8f08d649d166651febd',
 'clinical_core/pressure_tone.py': '2e350c8a42bcacfa31e8e5349d284c7d276808e396d36421e1dc369dbcb9ec26',
 'clinical_core/pressure_tone_filter.py': '54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650',
 'clinical_core/pressure_tone_filter_report.py': '6eebe11b816eeb901f10d9f1431182b71ab26db84652771af741076f33734f92',
 'clinical_core/pressure_tone_report.py': 'bc0fe73c681a35432baec5acf8062027b63f0e5821146133fb9211ae9240d7ac',
 'clinical_core/provenance.py': '619a4cba9c0b8d3c7d41de29165dfaab9ead59627c77fe3daab21e21c5bec2f4',
 'clinical_core/respiratory_distress.py': '111b07fc869b4eed143f601db29da76287b95004e066a5a9bc721a798b2a5f2a',
 'clinical_core/respiratory_distress_report.py': 'a07dd0bf18e890633410e4c36da85e532082698c874788e2f48bccee63b017d8',
 'clinical_core/respiratory_drive.py': '246f4ad5070fb50a64eec686ee4441e896d79c6d717303e1a43c11f7bf5af21b',
 'clinical_core/respiratory_drive_report.py': '7bb2ee04e3204b4de2bf542cac2f8166d72de7af4892cc7f098699f5adc94f2a',
 'clinical_core/respiratory_mechanics.py': '71c991ffc0217e478e2510bdb31849ac3ae82be8dfbb9b53b9d3d27df12b65e7',
 'clinical_core/respiratory_mechanics_report.py': 'cfd4fa9369da7e65c33090db48193b761135c69355c206fd76534a5070a49f9c',
 'clinical_core/respiratory_monotonicity.py': 'ba6bac3ea1f4f1f9b0bff5503b4ff846f1ae5a097ee88d8480dd3ee52fbba672',
 'clinical_core/respiratory_monotonicity_report.py': '373cdac40c02f1e0bd4683f9ab6329ce08805b4a41e38939e89ff28a8fc83fcb',
 'clinical_core/rr_audit.py': '4b663ffad81ff88f728707e7c96a255d882cbf62247107980652331fff885bf1',
 'clinical_core/rr_audit_report.py': 'f3951b39f4b0b9d6b82a6fffa687457f68257743e6e86fb4d5c10c0dc81797e5',
 'clinical_core/shadow.py': '66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35',
 'clinical_core/signals.py': 'f02f5494a8aac0361ace94a40e15a4df81970f456de7af0f6762a1196a27ee7f',
 'clinical_core/state.py': '90194bf77313fe178123e986b69378cfeeafe1e12531e382e79a71c0be5d0487',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>
P2T1A_FREEZE_DIGEST = "476e18f0e30f80745d2426d264bcf2e9a8617f7cdc585cc506f6c4e143c71982"
P2T1A_RECORD_SHA = "daacac03d8d4d7356ea3aceed6a01e44fb28d8452c610a510c11deffd6ae7611"


def _live(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _reverse(relative: str, text: str) -> tuple[str, list]:
    problems = []
    for live, before in REVERSAL[relative]:
        if text.count(live) != 1:
            problems.append(f"{relative}: a declared replacement occurs {text.count(live)} times")
            continue
        text = text.replace(live, before)
    return text, problems


def proved(relative: str, text: str | None = None) -> bool:
    back, problems = _reverse(relative, _live(relative) if text is None else text)
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2T1A[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2T1A.items()}


def p2t1a_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2T-1A file plus P2T-3's declared entries")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2t1a_sources(sources: dict) -> dict:
    """A P2T-1A dependency map: P2T-3's file removed, each changed tuple file at its P2T-1A hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2T1A.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


_FREEZE_SOURCES = bf.freeze_sources


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2T-1A's view reads the P2T-1A files (proven) and its captured source map
    is P2T-1A's; P2T-3 changes no behaviour."""
    patch.setattr(xm, "_live", p2t1a_text)
    patch.setattr(xm, "_FREEZE_SOURCES", lambda: p2t1a_sources(_FREEZE_SOURCES()))


class p2t1a_view:
    """P2T-1A's analysis reading the tree P2T-1A froze, for its own proofs and its record."""

    def __enter__(self):
        self._patch = mc._Patch()
        chain(self._patch)
        self._patch.setattr(bf, "freeze_sources", lambda: p2t1a_sources(_FREEZE_SOURCES()))
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2t1a_view():
        digest = xm.freeze_digest()
        proof = xm.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2t1a_freeze_digest": digest == P2T1A_FREEZE_DIGEST,
            "p2t1a_proof": all(proof["proofs"].values()) and all(proof["common_untouched"].values())
            and proof["p2t1_freeze_digest"] and proof["p2t1_proof"] and proof["p2t1_record"],
            "p2t1a_record": hashlib.sha256(xm.RECORD.read_bytes()).hexdigest() == P2T1A_RECORD_SHA}


# The verdict (predeclared) ---------------------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "a non-empty asthma feasible subregion exists in the carried (k, rho) region: both cases, the evidence order, RR, "
    "PaCO2 / mechanics, HR compatibility and the cross-family order",
    "mechanics and distress stay orthogonal (independent variation inside the region; no reader of the mechanics in the "
    "distress path; P2T-1's orthogonality live)",
    "both asthma cases are supported at every region witness by the live core (authored RR and PaCO2 reproduced, HR at "
    "or below the authored, SpO2 anchored, M1 satisfied) and the structural courses hold",
    "no common-core change is required (only the two tuple files differ from P2T-1A; every other file proven)",
    "the previous respiratory families stay compatible (pulmonary edema 58m, PE 61m, PE 33f upper bound) and the "
    "anaphylaxis cases are not forced to overpredict",
    "the opioid and GI controls stay valid (distress 0 admissible); the ACS residual is not closed",
    "no clinical point calibration is required (the region carried as intervals; no optimization; witnesses after "
    "non-emptiness; scale invariance shown)",
    "the hypoxaemic gain, the beta-agonist HR effect and the distress gains stay UNSET; systemic stress deferred",
    "non-regression: P2T-1A's record on its tree, P2S-3's record untouched, the case truth P2S-3's",
)
READY = "ASTHMA_SHADOW_MIGRATION_READY"
NOT_READY = "ASTHMA_SHADOW_MIGRATION_NOT_READY"
VERDICT_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def verdict(found: dict) -> dict:
    proof = found["proof"]
    checks = (
        found["region"]["nonempty"] and found["evidence"]["pass"],
        found["orthogonality"]["pass"],
        found["witnesses"].get("pass", False) and found["courses"]["pass"] and found["heart_rate"]["pass"]
        and found["writer"]["pass"],
        all(proof["proofs"].values()) and all(proof["common_untouched"].values()) and proof["p2t1a_freeze_digest"]
        and proof["p2t1a_proof"] and proof["p2t1a_record"],
        found["cross_family"]["pass"],
        found["cross_family"]["pass"],
        found["no_optimization"]["pass"] and found["scale_invariance"]["pass"],
        found["parameters"]["pass"],
        found["non_regression"]["pass"] and found["case_truth"]["pass"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(VERDICT_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    return {"criteria": rows, "blocker": blocker, "rule": VERDICT_RULE,
            "verdict": READY if blocker is None else f"{NOT_READY} - {blocker}",
            "region_status": found["region"]["status"]}


def design() -> dict:
    return {"decisions": DECISIONS, "normalization": NORMALIZATION, "k_region": list(K_REGION), "k_points": list(K_POINTS),
            "i_rr": list(I_RR), "i_hr": list(I_HR), "witness_i_hr": WITNESS_I_HR, "lambdas": list(LAMBDAS),
            "witness_rule": {k: list(v) for k, v in WITNESS_RULE.items()},
            "hypoxaemic_sensitivity_gain": HYPOXAEMIC_SENSITIVITY_GAIN, "course_minutes": COURSE_MINUTES,
            "obstruction_rate": OBSTRUCTION_RATE, "relief": RELIEF, "distress_relief": DISTRESS_RELIEF,
            "g_probe_per_min": G_PROBE_PER_MIN, "wob_tier": WOB_TIER, "two_sided_hr": list(TWO_SIDED_HR),
            "hr_excluded": list(HR_EXCLUDED), "verdict": {"criteria": list(VERDICT_CRITERIA), "rule": VERDICT_RULE},
            "reversal": REVERSAL, "core_at_p2t1a": CORE_AT_P2T1A, "common_at_p2t1a": COMMON_AT_P2T1A,
            "p2t1a": {"head": P2T1A_HEAD, "freeze_digest": P2T1A_FREEZE_DIGEST, "record": P2T1A_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2t1a": hashlib.sha256(xm.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "case_truth": case_truth(), "writer": writer(), "evidence": evidence()}
    found["region"] = region(found["evidence"])
    found["witnesses"] = witnesses(found["region"])
    found["courses"] = courses(found["witnesses"]) if found["witnesses"]["drawn"] else {"pass": False}
    found["scale_invariance"] = scale_invariance(found["witnesses"], found["region"])
    found["orthogonality"] = orthogonality(found["region"], found["witnesses"])
    found["no_optimization"] = no_optimization()
    found["cross_family"] = cross_family(found["region"])
    found["heart_rate"] = heart_rate(found["witnesses"])
    found["hypoxaemic_sensitivity"] = hypoxaemic_sensitivity(found["region"])
    found["consciousness"] = consciousness(found["witnesses"])
    found["collapse"] = collapse()
    found["parameters"] = parameters()
    found["non_regression"] = non_regression()
    found["legacy"] = legacy(found["witnesses"])          # read last, after the authored-truth evaluation
    found["verdict"] = verdict(found)
    return go._plain({"freeze_digest": freeze_digest(), "revision": REVISION, "design": design(), **found})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    text = json.dumps(run(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
