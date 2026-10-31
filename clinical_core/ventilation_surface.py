"""Phase 2 shadow core, P2K-3: effective ventilation decoupled from RR, and the respiratory decision surface.

    python -m clinical_core.ventilation_surface --digest
    python -m clinical_core.ventilation_surface --design
    python -m clinical_core.ventilation_surface --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-31, recorded in FACULTY). P2K-2 made the effective ventilation W
proportional to RR / intrinsic RR, so the intrinsic RR fixed the resting PaCO2 (up to about 74 mmHg at 12-16 breaths/min:
FREQUENCY_TO_VENTILATION_OVERCONSTRAINT). The candidate now reads W from clinical_core.ventilation: the acid burden
recruits ventilatory capacity (implicit tidal volume) beside the RR response, W = capacity / demand ratio, PaCO2 =
40 / W; RR keeps P2K-2's structure. This module freezes the semantics and the supports (the faculty's ventilation gains,
P2K-2's RR and acid supports, the references and arrival tolerances), runs the structural probes A-I and the RR / W
decoupling proofs, builds the analytic arrival joint surface (RR, then PaCO2; the pH diagnostic), reconstructs R1-R4 for
both cases by factorized post-processing of the certified deficit trajectories (validated against full core runs,
upstream rows identical), and reads the key questions, identifiability, the upstream dependencies, the observable
decision pack and readiness. Nothing is selected or approved; no envelope filters any trajectory; the legacy RR is never
read. The core files are not changed by P2K-3 (pinned below), so no closure proof of the core is needed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import fields, replace
from pathlib import Path

from . import acid_base as ab
from . import baroreflex as br
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import rr_audit as ra
from . import vascular_tone as vt
from . import ventilation as vn
from .derived import DEFAULT_PROFILE, arrival_state, derive
from .state import RhythmState

DECIDED = "2026-10-31"
REVISION = "P2K-3"
ROOT = ab.ROOT
CASES = ab.CASES
C57, C72 = ab.C57, ab.C72
DEMANDS = ab.DEMANDS
LAMBDAS = ab.LAMBDAS
AFTERLOAD = ab.AFTERLOAD
P2K2_RECORD = ROOT / "docs" / "revision" / "P2K2_acid_base.json"
P2K2_DIGEST = "7540ee76a681d272e8ac290781771d83d19c1562ea152209c88809aa4e8b710c"

# 1. The faculty decisions (2026-10-31) -----------------------------------------------------------------------------------

FACULTY = {
    "decided": DECIDED,
    "closed": "P2K-2 accepted and closed: the acid burden explicit and independent of lactate and D, lactate -> RR "
              "retired in the candidate, no D -> RR, an explicit drive, PaCO2 and pH causal, RR and W distinguishable; "
              "numeric RR calibration NOT authorized",
    "issue": "FREQUENCY_TO_VENTILATION_OVERCONSTRAINT: W proportional to RR / intrinsic RR made a low intrinsic RR "
             "(12-16) imply a resting PaCO2 up to about 74 mmHg once the burden resolved; intrinsic RR 12 and 16 are not "
             "removed to hide it",
    "shared_driver": "the acid burden drives RR (frequency) and, independently, effective ventilation recruitment (W): "
                     "two responses to one driver, never an identity; RR must not determine W",
    "mapping": "ventilatory_capacity = ventilation_efficiency x (1 + acid_to_ventilation_gain x metabolic_acid_burden); "
               "W = ventilatory_capacity / metabolic_demand; W = 1 matches the BASELINE metabolic CO2 demand, above 1 "
               "relative hyperventilation, below 1 relative hypoventilation",
    "efficiency": "1 for the GI cases as a STRUCTURAL_REFERENCE; no clinical efficiency grid; below 1 only in synthetic "
                  "probes; not a universal constant (future mechanics, dead space or fatigue families may replace it)",
    "paco2": "PaCO2 = PaCO2_reference / W = PaCO2_reference x demand / capacity; PaCO2_reference 40 mmHg "
             "COMMON_REFERENCE_PROVISIONAL, not FACULTY_APPROVED; at no burden, demand 1 and efficiency 1 it is 40 "
             "independently of intrinsic RR (intentional)",
    "ventilation_gain": "0.03 / 0.04 / 0.05 / 0.06 / 0.08 per mEq/L, EXPLORATORY, not FACULTY_APPROVED, built from the "
                        "authored arrival gases (57m about 0.043, 72f about 0.050); no value added after results",
    "rr": "P2K-2's RR structure kept: intrinsic RR 12 / 16 / 20 per patient, the frozen drive-gain support, S = 25 "
          "semantics; no range changed",
    "acid": "the untreated burden is not forced to rise (production and clearance coexist; it may fall when clearance "
            "exceeds production); B 13.4 / 19.4 / 28 and tau 60 / 120 / 240 kept, none approved, no extension",
    "references": "HCO3_reference 24 and PaCO2_reference 40 COMMON_REFERENCE_PROVISIONAL; arrival RR +/- 3 "
                  "ARRIVAL_RR_TOLERANCE_PROVISIONAL; none FACULTY_APPROVED; unchanged after outcomes",
    "arrival_paco2": "57m 31, 72f 33 at +/- 3 mmHg (ARRIVAL_PACO2_TOLERANCE_PROVISIONAL): 28-34 and 30-36; one common "
                     "ventilation gain; zero common survivors is a stop, never a wider tolerance",
    "arrival_rr": "57m 26 +/- 3, 72f 24 +/- 3; patient-specific intrinsic RR, common drive gain, no residual offset",
    "arrival_ph": "57m 7.37, 72f 7.40; pH derived from HCO3 and PaCO2, never tuned; +/- 0.03 diagnostic only "
                  "(PH_CONSISTENT / PH_INCONSISTENT), never a filter (it would count the same HCO3 / PaCO2 twice)",
    "upstream": "carry only dimensions that reach the acid / respiratory physiology: demand (causal), tone g (small, "
                "through output and deficit); MAP_set, the baroreflex and the HR latent region have no path",
    "support": "spontaneous breathing only: no NIV, invasive ventilation, PEEP, modes, fatigue, mechanics or tidal-volume "
               "state; FUTURE_RESPIRATORY_GENERALIZATION",
    "non_regression": "BloodState, output, pressure / tone, DO2 / deficit, D, lactate and HR / baroreflex unchanged; an "
                      "upstream change stops the package",
    "decision_pack": "LOW / median / HIGH for nine observables, prepared, never approved; no late hard filter",
    "scope": "shadow only: no runtime integration, GI or second-family migration, final RR / acid / ventilation-gain "
             "approval, hard respiratory envelope, consciousness recalibration, collapse activation, mechanical "
             "ventilation or legacy fitting",
}
CARRIED = ab.CARRIED

# 2. The semantics (P2K-3-1 to P2K-3-5) -------------------------------------------------------------------------------------

SEMANTICS = {
    "old_mapping": "P2K-2 (derived.alveolar_ventilation): W = efficiency x (RR / intrinsic RR) / (demand / baseline), "
                   "PaCO2 = PaCO2_rest / W with PaCO2_rest anchored to the authored arrival PaCO2; kept in "
                   "derived.respiration only to reproduce the closed P2K-2 record, SUPERSEDED in the P2K-3 candidate",
    "capacity": "ventilation.ventilatory_capacity = efficiency x (1 + acid_to_ventilation_gain x A): the implicit "
                "tidal-volume / effective-ventilation recruitment by the acid burden; no tidal-volume state",
    "w": "ventilation.effective_ventilation = capacity / (aux.oxygen_demand / anchors.metabolic_demand_baseline); 0 "
         "without breathing (no pulse); no RR, intrinsic RR, drive gain, lactate, D or W-channel term",
    "demand": "BASELINE_RELATIVE: the metabolic demand is the minute's oxygen demand over the patient's baseline demand "
              "(which carries the 1.0 / 1.1 demand class), as in P2K-2: W = 1 is the ventilation of the patient's own "
              "baseline CO2 production, so the demand class reaches W only through the deficit and the burden. The "
              "absolute demand index is the alternative, reported analytically as a sensitivity (it would make the 1.1 "
              "class 10 % hypercapnic at rest), never used",
    "paco2": "PaCO2 = 40 / W (the profile's paco2_reference_mmhg): predicted at arrival, never anchored to the authored "
             "PaCO2, which only filters (+/- 3)",
    "ph": "pH = 6.1 + log10(HCO3 / (0.03 PaCO2)) (derived.carbonic_ph); HCO3 = arrival HCO3 - (A - A0) (P2K-2)",
    "rr": "P2K-2 unchanged: drive = acid_to_drive_gain x A, RR = intrinsic + S (1 - exp(-drive / S)), S = 25",
    "frequency_drive": "RR - intrinsic RR: the drive's share of the rate",
    "recruitment": "1 + acid_to_ventilation_gain x A: the ventilation side's response to the same burden",
    "burden": "P2K-2 unchanged: A' = A + (B / tau) x effective deficit - A / tau, never forced to rise",
    "efficiency": "the profile's ventilation_efficiency, 1 in every clinical evaluation (structural reference)",
    "candidate": "the P2K-2 profile with its three gains declared, plus ventilation.VentilationCandidate(gain); the core's "
                 "step, derive and arrival state never read it, so no core file changes",
}
STATUS = {"acid_to_ventilation_gain": "EXPLORATORY", "paco2_reference": "COMMON_REFERENCE_PROVISIONAL",
          "bicarbonate_reference": "COMMON_REFERENCE_PROVISIONAL", "ventilation_efficiency": "STRUCTURAL_REFERENCE",
          "arrival_rr_tolerance": "ARRIVAL_RR_TOLERANCE_PROVISIONAL",
          "arrival_paco2_tolerance": "ARRIVAL_PACO2_TOLERANCE_PROVISIONAL", "ph_tolerance": "DIAGNOSTIC_ONLY",
          "demand": "BASELINE_RELATIVE", "tidal_volume": "IMPLICIT", "approved": "none FACULTY_APPROVED"}
FUTURE_RESPIRATORY_GENERALIZATION = {
    "tidal_volume": "an explicit tidal-volume / dead-space state would replace the recruitment term (capacity = minute "
                    "ventilation x (1 - dead-space fraction) over the baseline)",
    "mechanics": "a mechanics family would lower ventilation_efficiency (compliance, resistance, dead space)",
    "fatigue": "a fatigue state would cap or erode the recruitment over time",
    "niv": "NOT_MODELED", "invasive": "NOT_MODELED", "peep": "NOT_MODELED", "modes": "NOT_MODELED",
    "override": "a mechanical ventilator would set the capacity (and RR) directly, bypassing the drive",
    "hypoxaemic_drive": "HYPOXEMIC_DRIVE_DEFERRED (P2K-2); a term would add to the drive",
    "status": "FUTURE_RESPIRATORY_GENERALIZATION: none of these is a GI blocker; the recruitment mapping is the minimal "
              "abstraction for spontaneously breathing GI patients",
}

# 3. Frozen supports and tolerances (P2K-3-2 to P2K-3-5) ------------------------------------------------------------------

INTRINSIC_RR = ab.INTRINSIC_RR
DRIVE_GAINS = ab.DRIVE_GAINS
STEADY_BURDENS = ab.STEADY_BURDENS
ACID_TAUS = ab.ACID_TAUS
SATURATION = ab.SATURATION
VENTILATION_GAINS = (0.03, 0.04, 0.05, 0.06, 0.08)
FACULTY_IMPLIED_GAINS = {C57: 0.043, C72: 0.050}
EFFICIENCY = 1.0
PACO2_REFERENCE = DEFAULT_PROFILE.paco2_reference_mmhg
HCO3_REFERENCE = DEFAULT_PROFILE.bicarbonate_reference_meq_l
RR_TOLERANCE = ab.ARRIVAL_TOLERANCE
PACO2_TOLERANCE = 3.0
PH_TOLERANCE = 0.03
AUTHORED_RR = ab.AUTHORED_RR
#: The faculty's arrival PaCO2 windows (authored 31 and 33, +/- 3).
PACO2_WINDOWS = {C57: (28.0, 34.0), C72: (30.0, 36.0)}
#: Structural plausibility of pH (life-compatible range): a value outside fails the verdict's ph_coherent criterion
#: ("pathological pH"); it never filters a trajectory.
PH_PLAUSIBLE = (6.8, 7.8)
#: Key question 3's reading band: RR within the RR tolerance of the intrinsic RR, PaCO2 within 5 mmHg of the reference
#: (DIAGNOSTIC_READING, not an envelope; nothing is filtered by it).
APPROACH_RR = RR_TOLERANCE
REASONABLE_PACO2 = 5.0
CANDIDATE_RULE = (
    "Predeclared before any count. RR side: P2K-2's frozen supports (intrinsic RR 12 / 16 / 20 per patient, drive gain "
    "1 to 4 at ratio sqrt 2, common), S = 25. Acid side: B 13.4 / 19.4 / 28 x tau 60 / 120 / 240 (P2K-2), never forced to "
    "rise. Ventilation side: the faculty's common gain 0.03 / 0.04 / 0.05 / 0.06 / 0.08 per mEq/L, efficiency 1, PaCO2 "
    "reference 40, the baseline-relative demand. Arrival: RR within +/- 3 of the authored RR (P2K-2's analytic test), "
    "then the predicted PaCO2 40 / (1 + gain x A0) within the faculty's window per case; pH diagnostic only. Factorized: "
    "the burden per (B, tau) and deficit trajectory, RR per (drive gain, intrinsic RR), W / PaCO2 / pH per ventilation "
    "gain; no product of dimensions an output does not read.")


def exact_ventilation_gains() -> dict:
    """The gain that would reproduce each case's authored arrival PaCO2 exactly: (40 / PaCO2 - 1) / A0."""
    return {case: (PACO2_REFERENCE / ab.authored_gas(case)["paco2"] - 1.0) / ab.arrival_burden(case) for case in CASES}


def candidate(gain: float) -> vn.VentilationCandidate:
    return vn.VentilationCandidate(gain)


# 4. The decoupling proofs (P2K-3-1) --------------------------------------------------------------------------------------

W_FUNCTIONS = ("ventilation_recruitment", "ventilatory_capacity", "effective_ventilation", "paco2_from_ventilation")
W_TARGETS = ("demand_ratio", "recruitment", "capacity", "ventilation", "paco2")
#: The W-side fields of the returned VentilatedRespiration (the RR-side fields may read the rate).
W_RETURNED = ("efficiency", "recruitment", "capacity", "demand_ratio", "ventilation", "paco2_reference", "paco2", "ph")
#: Names W may never read: the rate, the intrinsic rate, the drive and its parameters, lactate, D, the W channel.
W_FORBIDDEN = frozenset({"rate", "respiratory_rate", "intrinsic", "intrinsic_rr", "intrinsic_respiratory_rate",
                         "frequency_drive", "drive", "acid_to_drive_gain", "rr_drive_saturation", "rate_from_drive",
                         "respiratory_drive", "rr_max", "lactate", "lactate_excess_mmol_l", "D", "W"})


def _read(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | \
        {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)} | \
        {n.arg for n in ast.walk(node) if isinstance(n, ast.arg)}


def _targets(node) -> list:
    """The names an assignment binds (plain, tuple-unpacked, augmented or annotated)."""
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    out = []
    for target in targets:
        out += [n.id for n in ast.walk(target) if isinstance(n, ast.Name)]
    return out


def w_inputs(source: str | None = None) -> dict:
    """Static proof: every name the W-side functions read; every assignment to a W-side name anywhere in
    ventilated_respiration (plain, augmented or annotated, at any depth), with the value it reads; and every W-side field
    of the VentilatedRespiration it returns (review B2: augmented assignments and the return were not covered)."""
    tree = ast.parse(source if source is not None else Path(vn.__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    reads = {name: sorted(_read(functions[name])) for name in W_FUNCTIONS}
    found = set()
    for node in ast.walk(functions["ventilated_respiration"]):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and node.value is not None:
            for name in _targets(node):
                if name in W_TARGETS:
                    found.add(name)
                    key = f"ventilated_respiration.{name}"
                    extra = {name} if isinstance(node, ast.AugAssign) else set()
                    reads[key] = sorted(set(reads.get(key, [])) | _read(node.value) | extra)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
            for field, arg in zip([f.name for f in fields(vn.VentilatedRespiration)], node.value.args):
                if field in W_RETURNED:
                    reads[f"return.{field}"] = sorted(_read(arg))
    return {"reads": reads, "targets_found": sorted(found),
            "returned_found": sorted(k.split(".")[1] for k in reads if k.startswith("return.")),
            "leaks": sorted({name for values in reads.values() for name in values if name in W_FORBIDDEN})}


# 5. Structural probes A-I (P2K-3-6) ---------------------------------------------------------------------------------------

PROBE_ANCHORS = ab.PROBE_ANCHORS
PROBE_PROFILE = ab.PROBE_PROFILE
PROBE_GAIN = 0.05
PROBE_RULE = (
    "Synthetic, structural only: P2K-2's neutral probe arrival (no deficit; HCO3 20, so A0 = 4; intrinsic RR 16) and probe "
    "profile (drive gain 2, B 19.4, tau 120, efficiency 1), ventilation gain 0.05. A: burden 4 -> 8. B: RR alone (drive "
    "gain 2 -> 4, and S 25 -> 15) at burden 8. C: intrinsic RR 12 / 16 / 20 at burden 8. D: ventilation gain 0.03 -> 0.08 "
    "at burden 8. E: lactate alone. F: D alone. G: efficiency 0.5 with a high RR (drive gain 4, burden 8), and a 20-minute "
    "course with efficiency 1 -> 0.5 while the burden rises 4 -> 10. H: burden 0 at the baseline demand, every intrinsic "
    "RR, drive gain and ventilation gain. I: demand ratio 1.25 at burden 8, and the burden whose recruitment compensates "
    "it. W channel: state W +/- 0.5. Not candidates, not clinical values.")


def _probe_state(burden=None, anchors=PROBE_ANCHORS, profile=PROBE_PROFILE, **changes):
    state = arrival_state(anchors, profile)
    aux = state.aux if burden is None else replace(state.aux, metabolic_acid_burden=burden)
    for name in ("lactate_excess_mmol_l", "oxygen_demand"):
        if name in changes:
            aux = replace(aux, **{name: changes.pop(name)})
    return state.evolve(aux=aux, **changes)


def _vr(state, anchors=PROBE_ANCHORS, profile=PROBE_PROFILE, gain=PROBE_GAIN) -> dict:
    r = vn.ventilated_respiration(state, anchors, profile, candidate(gain))
    d = derive(state, anchors, profile)
    return {"burden": r.acid_burden, "hco3": r.bicarbonate, "drive": r.drive, "rr": r.respiratory_rate,
            "frequency_drive": r.frequency_drive, "recruitment": r.recruitment, "capacity": r.capacity,
            "efficiency": r.efficiency, "demand_ratio": r.demand_ratio, "w": r.ventilation, "paco2": r.paco2, "ph": r.ph,
            "core_rr": d.respiratory_rate, "lactate": d.lactate, "D": state.D}


def _same_w(a: dict, b: dict) -> bool:
    return a["w"] == b["w"] and a["paco2"] == b["paco2"]


def probes() -> dict:
    base, high = _vr(_probe_state()), _vr(_probe_state(8.0))
    intrinsic = dv.intrinsic_respiratory_rate(PROBE_ANCHORS)
    b_gain = _vr(_probe_state(8.0), profile=replace(PROBE_PROFILE, acid_to_drive_gain=4.0))
    b_sat = _vr(_probe_state(8.0), profile=replace(PROBE_PROFILE, rr_drive_saturation=15.0))
    c = {f"{i:g}": _vr(_probe_state(8.0, anchors=replace(PROBE_ANCHORS, intrinsic_respiratory_rate=i)),
                       anchors=replace(PROBE_ANCHORS, intrinsic_respiratory_rate=i)) for i in INTRINSIC_RR}
    d_low, d_high = _vr(_probe_state(8.0), gain=0.03), _vr(_probe_state(8.0), gain=0.08)
    e = _vr(_probe_state(lactate_excess_mmol_l=4.0))
    f = _vr(_probe_state(D=40.0))
    fast = replace(PROBE_PROFILE, acid_to_drive_gain=4.0)
    g_ref = _vr(_probe_state(8.0, profile=fast), profile=fast)
    weak = replace(fast, ventilation_efficiency=0.5)
    g_low = _vr(_probe_state(8.0, profile=weak), profile=weak)
    course = []
    for minute in range(21):
        burden, efficiency = 4.0 + 0.3 * minute, 1.0 - 0.025 * minute
        rate = dv.rate_from_drive(dv.respiratory_drive(burden, PROBE_PROFILE), intrinsic, PROBE_PROFILE)
        w = vn.effective_ventilation(vn.ventilatory_capacity(burden, efficiency, PROBE_GAIN), 1.0)
        course.append({"minute": minute, "burden": burden, "efficiency": efficiency, "rr": rate, "w": w,
                       "paco2": vn.paco2_from_ventilation(w, PACO2_REFERENCE)})
    rest = []
    for i in INTRINSIC_RR:
        anchors = replace(PROBE_ANCHORS, intrinsic_respiratory_rate=i)
        for drive_gain in DRIVE_GAINS:
            profile = replace(PROBE_PROFILE, acid_to_drive_gain=drive_gain)
            for gain in VENTILATION_GAINS:
                r = _vr(_probe_state(0.0, anchors=anchors, profile=profile), anchors, profile, gain)
                rest.append({"intrinsic": i, "drive_gain": drive_gain, "gain": gain, "rr": r["rr"], "w": r["w"],
                             "paco2": r["paco2"]})
    baseline = PROBE_ANCHORS.metabolic_demand_baseline
    i_up = _vr(_probe_state(8.0, oxygen_demand=1.25 * baseline))
    compensating = (1.25 * vn.ventilation_recruitment(8.0, PROBE_GAIN) - 1.0) / PROBE_GAIN
    i_comp = _vr(_probe_state(compensating, oxygen_demand=1.25 * baseline))
    w_up, w_down = _vr(_probe_state(W=0.5)), _vr(_probe_state(W=-0.5))
    return {
        "rule": PROBE_RULE, "base": base,
        "A": {"result": high, "rr_rises": high["rr"] > base["rr"], "w_rises": high["w"] > base["w"],
              "paco2_falls": high["paco2"] < base["paco2"],
              "rr_by_frequency_gain": high["rr"] == dv.rate_from_drive(PROBE_PROFILE.acid_to_drive_gain * 8.0, intrinsic,
                                                                       PROBE_PROFILE),
              "w_by_ventilation_gain": abs((high["w"] - base["w"]) - PROBE_GAIN * 4.0) < 1e-12},
        "B": {"drive_gain_4": b_gain, "saturation_15": b_sat,
              "rr_changes": b_gain["rr"] != high["rr"] and b_sat["rr"] != high["rr"],
              "w_unchanged": _same_w(b_gain, high) and _same_w(b_sat, high)},
        "C": {"by_intrinsic": c, "rr_changes": len({v["rr"] for v in c.values()}) == len(c),
              "w_paco2_unchanged": all(_same_w(v, c["16"]) for v in c.values())},
        "D": {"gain_0.03": d_low, "gain_0.08": d_high, "w_rises": d_high["w"] > d_low["w"],
              "paco2_falls": d_high["paco2"] < d_low["paco2"], "rr_unchanged": d_high["rr"] == d_low["rr"]},
        "E": {"result": e, "lactate_raised": e["lactate"] > base["lactate"],
              "unchanged": e["rr"] == base["rr"] and e["core_rr"] == base["core_rr"] and _same_w(e, base)},
        "F": {"result": f, "d_raised": f["D"] > base["D"],
              "unchanged": f["rr"] == base["rr"] and f["core_rr"] == base["core_rr"] and _same_w(f, base)},
        "G": {"efficiency_1": g_ref, "efficiency_0.5": g_low, "w_falls": g_low["w"] < g_ref["w"],
              "paco2_rises": g_low["paco2"] > g_ref["paco2"], "rr_high_and_unchanged": g_low["rr"] == g_ref["rr"]
              and g_low["rr"] > intrinsic + 10.0, "hypercapnic_despite_tachypnoea": g_low["paco2"] > PACO2_REFERENCE,
              "course": course, "course_rr_rises": course[-1]["rr"] > course[0]["rr"],
              "course_paco2_rises": course[-1]["paco2"] > course[0]["paco2"]},
        "H": {"rows": rest, "w_is_1": all(r["w"] == 1.0 for r in rest),
              "paco2_is_reference": all(r["paco2"] == PACO2_REFERENCE for r in rest),
              "rr_is_intrinsic": all(r["rr"] == r["intrinsic"] for r in rest)},
        "I": {"demand_1.25": i_up, "w_falls": i_up["w"] < high["w"], "paco2_rises": i_up["paco2"] > high["paco2"],
              "rr_unchanged": i_up["rr"] == high["rr"], "compensating_burden": compensating, "compensated": i_comp,
              "recruitment_compensates": abs(i_comp["w"] - high["w"]) < 1e-12},
        "W_channel": {"unchanged": w_up["rr"] == base["rr"] == w_down["rr"] and _same_w(w_up, base)
                      and _same_w(w_down, base)},
        "pH": {"formula": abs(high["ph"] - dv.carbonic_ph(high["hco3"], high["paco2"])) < 1e-12},
        "no_pulse": _vr(_probe_state(8.0, R=RhythmState.asystole(), terminal_since=0)),
    }


def probes_pass(p: dict) -> dict:
    return {"A": p["A"]["rr_rises"] and p["A"]["w_rises"] and p["A"]["paco2_falls"] and p["A"]["rr_by_frequency_gain"]
            and p["A"]["w_by_ventilation_gain"],
            "B": p["B"]["rr_changes"] and p["B"]["w_unchanged"],
            "C": p["C"]["rr_changes"] and p["C"]["w_paco2_unchanged"],
            "D": p["D"]["w_rises"] and p["D"]["paco2_falls"] and p["D"]["rr_unchanged"],
            "E": p["E"]["lactate_raised"] and p["E"]["unchanged"],
            "F": p["F"]["d_raised"] and p["F"]["unchanged"],
            "G": p["G"]["w_falls"] and p["G"]["paco2_rises"] and p["G"]["rr_high_and_unchanged"]
            and p["G"]["course_rr_rises"] and p["G"]["course_paco2_rises"],
            "H": p["H"]["w_is_1"] and p["H"]["paco2_is_reference"] and p["H"]["rr_is_intrinsic"],
            "I": p["I"]["w_falls"] and p["I"]["paco2_rises"] and p["I"]["rr_unchanged"]
            and p["I"]["recruitment_compensates"],
            "W_channel": p["W_channel"]["unchanged"], "pH": p["pH"]["formula"],
            "no_pulse": p["no_pulse"]["w"] == 0.0 and p["no_pulse"]["paco2"] is None and p["no_pulse"]["rr"] == 0.0}


# 6. The arrival joint surface (P2K-3-3, -4, -5, -9) ---------------------------------------------------------------------

def predicted_paco2(gain: float, case: str, demand_ratio: float = 1.0) -> float:
    return vn.arrival_paco2(ab.arrival_burden(case), DEFAULT_PROFILE, candidate(gain), demand_ratio)


def predicted_ph(gain: float, case: str, demand_ratio: float = 1.0) -> float:
    return dv.carbonic_ph(ab.authored_gas(case)["hco3"], predicted_paco2(gain, case, demand_ratio))


def ph_class(error: float) -> str:
    return "PH_CONSISTENT" if abs(error) <= PH_TOLERANCE else "PH_INCONSISTENT"


def paco2_compatibility(demand_ratio: float = 1.0) -> dict:
    """Per common ventilation gain: the predicted arrival PaCO2 of each case in its faculty window, and the derived pH
    against the authored one (diagnostic only)."""
    rows, compatible = [], []
    for gain in VENTILATION_GAINS:
        paco2 = {case: predicted_paco2(gain, case, demand_ratio) for case in CASES}
        ok = {case: PACO2_WINDOWS[case][0] <= paco2[case] <= PACO2_WINDOWS[case][1] for case in CASES}
        ph = {case: predicted_ph(gain, case, demand_ratio) for case in CASES}
        error = {case: ph[case] - ab.authored_gas(case)["ph"] for case in CASES}
        rows.append({"gain": gain, "paco2": paco2,
                     "mismatch": {case: paco2[case] - ab.authored_gas(case)["paco2"] for case in CASES},
                     "recruitment": {case: vn.ventilation_recruitment(ab.arrival_burden(case), gain) for case in CASES},
                     "compatible_by_case": ok, "compatible": all(ok.values()), "ph": ph, "ph_error": error,
                     "ph_class": {case: ph_class(error[case]) for case in CASES}})
        if all(ok.values()):
            compatible.append(gain)
    return {"rows": rows, "compatible": compatible, "count": len(compatible), "of": len(rows)}


def demand_semantics_sensitivity() -> dict:
    """The alternative (absolute demand index) at arrival: W = capacity / demand class; reported, never used."""
    return {f"{factor:g}": {"compatible": paco2_compatibility(factor)["compatible"],
                            "paco2": {f"{row['gain']:g}": row["paco2"] for row in paco2_compatibility(factor)["rows"]}}
            for factor in DEMANDS}


def arrival_rejections() -> dict:
    """ANALYTIC_REJECTION at arrival: invalid gains or intrinsic RR, a saturated ceiling the guard would clip, W <= 0,
    PaCO2 <= 0 or HCO3 <= 0. Counted separately from the arrival filters (which are compatibility, not impossibility)."""
    rejected = 0
    for gain in DRIVE_GAINS:
        for intrinsic in INTRINSIC_RR:
            for vgain in VENTILATION_GAINS:
                for case in CASES:
                    w = vn.ventilatory_capacity(ab.arrival_burden(case), EFFICIENCY, vgain)
                    if gain < 0 or vgain < 0 or not intrinsic > 0 or intrinsic + SATURATION > DEFAULT_PROFILE.rr_max \
                            or not w > 0 or not ab.authored_gas(case)["hco3"] > 0:
                        rejected += 1
    return {ab.ANALYTIC_REJECTION: rejected}


def joint_surface(rr: dict, paco2: dict) -> dict:
    """RR compatibility (P2K-2's analytic test, per (drive gain, intrinsic 57m, intrinsic 72f)), then PaCO2 compatibility
    (per common ventilation gain). (B, tau) is part of the acid support but no arrival output reads it: carried whole,
    counted with and without it, never multiplied further (no upstream dimension reaches the arrival outputs)."""
    pairs = len(ab.acid_pairs())
    joint = [(g, i57, i72, v) for g, i57, i72 in rr["compatible"] for v in paco2["compatible"]]
    read = {"total": rr["of"] * paco2["of"], "rr_compatible": rr["count"] * paco2["of"],
            "paco2_compatible": rr["of"] * paco2["count"], "joint": len(joint)}
    def counts(index, support):
        return {f"{value:g}": sum(1 for j in joint if j[index] == value) for value in support}
    return {"arrival_read": read, "with_acid_support": {k: v * pairs for k, v in read.items()},
            "acid_pairs": pairs, "joint": joint,
            "support": {"intrinsic_57m": counts(1, INTRINSIC_RR), "intrinsic_72f": counts(2, INTRINSIC_RR),
                        "drive_gain": counts(0, DRIVE_GAINS), "ventilation_gain": counts(3, VENTILATION_GAINS),
                        "B": {f"{b:g}": len(joint) * len(ACID_TAUS) for b in STEADY_BURDENS} if joint else {},
                        "tau": {f"{t:g}": len(joint) * len(STEADY_BURDENS) for t in ACID_TAUS} if joint else {},
                        "acid": "NOT_READ_BY_ARRIVAL: the arrival burden is the authored HCO3's; every (B, tau) is "
                                "carried with every joint arrival candidate"}}


# 7. The clinical scenarios R1-R4, factorized (P2K-3-7, P2K-3-10) ------------------------------------------------------------

R_SCENARIOS = ab.R_SCENARIOS
MINUTES_REPORTED = ab.MINUTES_REPORTED
RECONSTRUCTION_RULE = (
    "The P2J-3 region recomputed with P2J-3's own functions and the deficit, D and lactate of every unique (scenario, "
    "blood set, lactate-side point) rebuilt as P2K-1 / P2K-2 did (acid_base.reconstruct). The burden per (B, tau) is the "
    "core's acid_burden_after_minute (acid_base.burden_series); RR is the core's algebra per (drive gain, intrinsic RR); "
    "W, PaCO2 and pH the ventilation module's algebra per ventilation gain at efficiency 1 and the baseline demand. Each "
    "observable is read over the factors it depends on only (RR never multiplied by the ventilation gain, W never by the "
    "drive gain or intrinsic RR). Validated against full core runs with the candidate declared (every upstream row equal "
    "to the run without it).")
SENSITIVITY_FACTORS = ("intrinsic_rr", "drive_gain", "ventilation_gain", "acid_pair", "demand", "tone_gain")
RR_FACTORS = ("intrinsic_rr", "drive_gain", "acid_pair", "demand", "tone_gain")
GAS_FACTORS = ("ventilation_gain", "acid_pair", "demand", "tone_gain")


# The factorized algebra: one function per series, the same in evaluate (the tables, the questions, the pack) and in
# validate (against the core), so the validation certifies the code that produced the record (review M2).

def hco3_series(series: list, case: str) -> list:
    a0, hco3_0 = ab.arrival_burden(case), ab.authored_gas(case)["hco3"]
    return [hco3_0 - (x - a0) for x in series]


def rr_series(series: list, pulse: list, drive_gain: float, intrinsic: float) -> list:
    return [dv.rate_from_drive(drive_gain * x, intrinsic, DEFAULT_PROFILE) if p else 0.0 for x, p in zip(series, pulse)]


def frequency_drive_series(rr: list, pulse: list, intrinsic: float) -> list:
    return [r - intrinsic if p else 0.0 for r, p in zip(rr, pulse)]


def recruitment_series(series: list, gain: float) -> list:
    return [vn.ventilation_recruitment(x, gain) for x in series]


def gas_series(series: list, hco3: list, pulse: list, gain: float) -> tuple:
    """W, PaCO2 and pH per minute at efficiency 1 and the baseline demand; 0 / None without breathing."""
    w = [vn.effective_ventilation(vn.ventilatory_capacity(x, EFFICIENCY, gain), 1.0) if p else 0.0
         for x, p in zip(series, pulse)]
    paco2 = [vn.paco2_from_ventilation(v, PACO2_REFERENCE) if v > 0.0 else None for v in w]
    ph = [dv.carbonic_ph(c, q) if q is not None and c > 0.0 else None for c, q in zip(hco3, paco2)]
    return w, paco2, ph


def _directions(values: list) -> tuple:
    n = len(values)
    known = [m for m in range(1, n) if values[m] is not None and values[m - 1] is not None]
    return ({m for m in known if values[m] - values[m - 1] > 1e-12}, {m for m in known if values[m] - values[m - 1] < -1e-12})


class _Pack:
    """The decision pack's values, grouped as they arrive by each factor they depend on (no trajectory kept)."""

    def __init__(self):
        self.all, self.by = {}, {}

    def add(self, item: str, value: float, factors: dict) -> None:
        self.all.setdefault(item, []).append(value)
        for name, level in factors.items():
            self.by.setdefault(item, {}).setdefault(name, {}).setdefault(level, []).append(value)

    def summary(self, item: str) -> dict:
        out = {"distribution": ab._spread(self.all.get(item, []))}
        groups = self.by.get(item, {})
        for name in SENSITIVITY_FACTORS:
            if name not in groups:
                out[name] = {"path": "NONE", "range": 0.0}
                continue
            medians = {str(level): ab._spread(values)["median"] for level, values in sorted(groups[name].items())}
            out[name] = {"medians": medians, "range": max(medians.values()) - min(medians.values())}
        return out


def _levels(case_factor, tgain, b, tau):
    return {"acid_pair": f"{b:g}/{tau:g}", "demand": f"{case_factor:g}", "tone_gain": f"{tgain:g}"}


def evaluate(store: dict, joint: list) -> dict:
    """Per (tone gain, demand, scenario, case): the burden per (B, tau), RR per (drive gain, intrinsic RR) and W / PaCO2 /
    pH per ventilation gain, at the reported minutes and over every trajectory's minutes; the key questions, the decision
    pack and the plausibility checks tallied on the way."""
    rr_set = {C57: sorted({(g, i57) for g, i57, _, _ in joint}), C72: sorted({(g, i72) for g, _, i72, _ in joint})}
    gains = sorted({v for *_, v in joint})
    lowest = {case: min(i for _, i in rr_set[case]) for case in CASES}
    tables, tally, pack = {}, ab._Tally(), _Pack()
    rejections = {ab.ANALYTIC_REJECTION: 0, ab.SIMULATION_REJECTION: 0}
    plausible = {"ph_low": math.inf, "ph_high": -math.inf, "paco2_low": math.inf, "w_low": math.inf,
                 "outside": 0, "non_positive": 0}
    demand_of = {}
    for (tgain, factor, name, case), seen in sorted(store.items(), key=lambda kv: str(kv[0])):
        key = f"x{factor:g} g{tgain:g} {name} {case}"
        a0, hco3_0 = ab.arrival_burden(case), ab.authored_gas(case)["hco3"]
        rr_cells = {str(m): {q: [] for q in ("rr", "intrinsic", "frequency_drive", "drive")} for m in MINUTES_REPORTED}
        acid_cells = {str(m): {q: [] for q in ("burden", "hco3")} for m in MINUTES_REPORTED}
        gas_cells = {str(m): {q: [] for q in ("recruitment", "efficiency", "w", "paco2", "ph")} for m in MINUTES_REPORTED}
        upstream = {str(m): {q: [] for q in ("lactate", "D", "deficit", "crystalloid_ml", "prbc_units")}
                    for m in MINUTES_REPORTED}
        demand = {str(m): {q: [] for q in ("metabolic_demand", "demand_ratio")} for m in MINUTES_REPORTED}
        haemostasis = {str(m): 0 for m in MINUTES_REPORTED}
        summary = {q: [] for q in ("rr_120", "rr_peak", "rr_min", "rr_change_0_120", "paco2_120", "paco2_low",
                                   "paco2_high", "ph_120", "ph_low", "ph_high", "w_120", "burden_120", "burden_peak")}
        for (_, lam), (_, t) in seen.items():
            if (case, lam, factor) not in demand_of:
                demand_of[(case, lam, factor)] = vt.tone_anchors(case, vt.level_of(lam), factor).metabolic_demand_baseline
            baseline = demand_of[(case, lam, factor)]
            n = len(t["deficit"])
            pulse = t["pulse"][:n]
            for m in MINUTES_REPORTED:
                if m < n:
                    row = upstream[str(m)]
                    row["lactate"].append(t["lactate"][m])
                    row["D"].append(t["D"][m])
                    row["deficit"].append(t["deficit"][m])
                    row["crystalloid_ml"].append(t["crystalloid"][m])
                    row["prbc_units"].append(t["prbc"][m])
                    demand[str(m)]["metabolic_demand"].append(baseline)
                    demand[str(m)]["demand_ratio"].append(1.0)
                    haemostasis[str(m)] += 1 if t["controlled_at"] is not None and m >= t["controlled_at"] else 0
            d_max, h = max(t["deficit"]), t["controlled_at"]
            lactate = t["lactate"][:n]
            for b, tau in ab.acid_pairs():
                levels = _levels(factor, tgain, b, tau)
                series = ab.burden_series(t["deficit"], a0, b, tau)[:n]
                hco3 = hco3_series(series, case)
                if min(hco3) <= 0.0:
                    rejections[ab.SIMULATION_REJECTION] += 1
                    continue
                for m in MINUTES_REPORTED:
                    if m < n:
                        acid_cells[str(m)]["burden"].append(series[m])
                        acid_cells[str(m)]["hco3"].append(hco3[m])
                summary["burden_peak"].append(max(series))
                if 120 < n:
                    summary["burden_120"].append(series[120])
                # W side: per ventilation gain.
                gas, directions = {}, {}
                for gain in gains:
                    w, paco2, ph = gas_series(series, hco3, pulse, gain)
                    gas[gain] = (w, paco2, ph)
                    directions[gain] = _directions(paco2)
                    recruitment = recruitment_series(series, gain)
                    breathing = [v for v, p in zip(w, pulse) if p]
                    if breathing and (min(breathing) <= 0.0 or not all(math.isfinite(v) for v in breathing)):
                        plausible["non_positive"] += 1
                    known = [x for x in ph if x is not None]
                    if known:
                        plausible["ph_low"] = min(plausible["ph_low"], min(known))
                        plausible["ph_high"] = max(plausible["ph_high"], max(known))
                        plausible["outside"] += sum(1 for x in known if not PH_PLAUSIBLE[0] <= x <= PH_PLAUSIBLE[1])
                        plausible["paco2_low"] = min(plausible["paco2_low"], min(p for p in paco2 if p is not None))
                        plausible["w_low"] = min(plausible["w_low"], min(breathing))
                        summary["ph_low"].append(min(known))
                        summary["ph_high"].append(max(known))
                        summary["paco2_low"].append(min(p for p in paco2 if p is not None))
                        summary["paco2_high"].append(max(p for p in paco2 if p is not None))
                    for m in MINUTES_REPORTED:
                        if m < n:
                            cell = gas_cells[str(m)]
                            cell["recruitment"].append(recruitment[m])
                            cell["efficiency"].append(EFFICIENCY)
                            cell["w"].append(w[m])
                            cell["paco2"].append(paco2[m])
                            cell["ph"].append(ph[m])
                    gas_levels = {**levels, "ventilation_gain": f"{gain:g}"}
                    if 120 < n:
                        summary["paco2_120"].append(paco2[120])
                        summary["ph_120"].append(ph[120])
                        summary["w_120"].append(w[120])
                        if name == "P1":
                            pack.add(f"C {case}" if case == C57 else f"D {case}", paco2[120], gas_levels)
                            pack.add(f"C {case} pH" if case == C57 else f"D {case} pH", ph[120], gas_levels)
                        if name == "P4":
                            pack.add(f"H {case}", paco2[120], gas_levels)
                            pack.add(f"H {case} pH", ph[120], gas_levels)
                            toward = abs(paco2[120] - PACO2_REFERENCE) <= abs(paco2[0] - PACO2_REFERENCE)
                            tally.count("q2_toward", toward)
                            tally.count(f"q2_toward {case}", toward)
                            tally.add(f"q2_paco2_120 {case}", paco2[120])
                            tally.add(f"q2_distance_120 {case}", abs(paco2[120] - PACO2_REFERENCE))
                        if name == "P1":
                            tally.add(f"q2_untreated_paco2_120 {case}", paco2[120])
                    if name == "P4" and h is not None and h + 1 < n:
                        steps = [abs(y - x) for x, y in zip(paco2, paco2[1:]) if x is not None and y is not None]
                        if len(steps) == n - 1:
                            tally.count("paco2_haemostasis_step", steps[h] <= max(steps[:h] + steps[h + 1:]))
                # Question 3's PaCO2 side depends on the ventilation gain only: counted once per (trajectory, pair).
                reasonable = (sum(1 for gain in gains if abs(gas[gain][1][120] - PACO2_REFERENCE) <= REASONABLE_PACO2)
                              if 120 < n else 0)
                # RR side: per (drive gain, intrinsic RR).
                for drive_gain, intrinsic in rr_set[case]:
                    if ab.analytic_rejections(drive_gain, intrinsic, b, tau, d_max, case):
                        rejections[ab.ANALYTIC_REJECTION] += 1
                        continue
                    rr = rr_series(series, pulse, drive_gain, intrinsic)
                    frequency = frequency_drive_series(rr, pulse, intrinsic)
                    rr_levels = {**levels, "intrinsic_rr": f"{intrinsic:g}", "drive_gain": f"{drive_gain:g}"}
                    for m in MINUTES_REPORTED:
                        if m < n:
                            cell = rr_cells[str(m)]
                            cell["rr"].append(rr[m])
                            cell["intrinsic"].append(intrinsic)
                            cell["frequency_drive"].append(frequency[m])
                            cell["drive"].append(drive_gain * series[m])
                    summary["rr_peak"].append(max(rr))
                    summary["rr_min"].append(min(rr))
                    if 120 < n:
                        summary["rr_120"].append(rr[120])
                        summary["rr_change_0_120"].append(rr[120] - rr[0])
                        if name == "P1":
                            pack.add("A " + case if case == C57 else "B " + case, rr[120], rr_levels)
                        if name == "P2":
                            pack.add(f"E {case}", rr[120] - rr[0], rr_levels)
                            pack.add(f"E {case} RR120", rr[120], rr_levels)
                        if name == "P3":
                            pack.add(f"F {case}", rr[120] - rr[0], rr_levels)
                            pack.add(f"F {case} RR120", rr[120], rr_levels)
                        if name == "P4":
                            pack.add(f"G {case}", rr[120], rr_levels)
                            pack.add(f"I {case}", rr[120] - intrinsic, rr_levels)
                    # Key questions on the RR side.
                    if name == "P1" and case == C72:
                        dip = rr[0] - min(rr[:31])
                        tally.count("q4_dip", dip > 1e-9)
                        tally.count(f"q4_dip {b:g}", dip > 1e-9)
                        tally.add("q4_dip_depth", dip)
                    tally.count("q5_opposite", any((lactate[m] - lactate[m - 1]) * (rr[m] - rr[m - 1]) < -1e-12
                                                   for m in range(1, n)))
                    up, down = _directions(rr)
                    for gain in gains:
                        p_up, p_down = directions[gain]
                        tally.count("q6_same_direction", bool((up & p_up) | (down & p_down)))
                        tally.count("q6_opposite_direction", bool((up & p_down) | (down & p_up)))
                    if name == "P4":
                        if h is not None and h + 1 < n:
                            steps = [abs(y - x) for x, y in zip(rr, rr[1:])]
                            tally.count("rr_haemostasis_step", steps[h] <= max(steps[:h] + steps[h + 1:]))
                            above = rr[min(h + 15, n - 1)] - intrinsic
                            tally.add("rr_15_after_haemostasis_above_intrinsic", above)
                            tally.count("no_instant_normalization", above >= 1.0)
                        if 120 < n and intrinsic == lowest[case]:
                            near = rr[120] - intrinsic <= APPROACH_RR
                            n_, true = tally.counts.get(f"q3 {case}", (0, 0))
                            tally.counts[f"q3 {case}"] = (n_ + len(gains), true + (reasonable if near else 0))
                            tally.count(f"q3_rr_near {case}", near)
                            tally.add(f"q3_rr_120_above_intrinsic {case}", rr[120] - intrinsic)
        tables[key] = {"trajectories": len(seen),
                       "minutes": {m: {**{q: ab._spread(v) for q, v in rr_cells[m].items()},
                                       **{q: ab._spread(v) for q, v in acid_cells[m].items()},
                                       **{q: ab._spread(v) for q, v in gas_cells[m].items()},
                                       **{q: ab._spread(v) for q, v in demand[m].items()}} for m in rr_cells},
                       "upstream": {m: {q: ab._spread(v) for q, v in upstream[m].items()} for m in upstream},
                       "haemostasis": haemostasis, "summary": {q: ab._spread(v) for q, v in summary.items()},
                       "efficiency": EFFICIENCY, "rr_candidates": [list(c) for c in rr_set[case]],
                       "ventilation_gains": gains}
    plausible = {k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in plausible.items()}
    return {"tables": tables, "tally": tally, "pack": pack, "rejections": rejections, "plausible": plausible,
            "rr_set": rr_set, "gains": gains, "lowest_intrinsic": lowest}


# 8. Validation against the core, upstream non-regression (P2K-3-10, P2K-3-14) ----------------------------------------------

VALIDATION_CANDIDATE = (2.0, 16.0, 16.0, 19.4, 120.0, 0.05)
#: The upstream domains P2K-3-14 names, each read from the run's rows and states (with the candidate against without it).
UPSTREAM_DOMAINS = {"blood_state": (("bleed_ml_per_min", "crystalloid_in_ml", "prbc_units"), ("blood", "V", "hb")),
                    "output": (("pulse", "output"), ("R",)),
                    "pressure_tone": (("T", "P", "p", "sbp", "dbp", "map", "pp"), ("T", "P")),
                    "delivery_deficit": (("delivery_rel", "demand"), ("aux.oxygen_demand",)),
                    "D": (("D",), ("D",)), "lactate": (("lactate",), ("aux.lactate_excess_mmol_l",)),
                    "hr_baroreflex": (("hr",), ("aux.sympathetic_drive",))}


def _domain_equal(plain: dict, live: dict, rows: tuple, fields: tuple) -> bool:
    def part(state, name):
        data = state.to_dict()
        return data["aux"][name[4:]] if name.startswith("aux.") else data[name]
    return len(plain["rows"]) == len(live["rows"]) and all(p[k] == q[k] for p, q in zip(plain["rows"], live["rows"])
                                                           for k in rows) and \
        all(part(s, f) == part(t, f) for s, t in zip(plain["states"], live["states"]) for f in fields)


def validate(region: dict, store: dict) -> dict:
    """One full core run per (tone gain, demand, scenario, case) with the acid-base candidate declared, and the same run
    without it. At every state the ventilation module equals the factorized algebra (the series functions evaluate
    uses, on the trajectory's own deficit and pulse); recomputed on the same states with
    another drive gain or another intrinsic RR its W and PaCO2 are identical (RR alone moves no W); recomputed in reverse
    order it is identical (no order dependence); every upstream row equals the run without the candidate; the default
    RR equals P2K-1's."""
    drive_gain, i57, i72, b, tau, gain = VALIDATION_CANDIDATE
    vc = candidate(gain)
    out = {"compared": 0, "equal": True, "max_abs_diff": 0.0, "upstream_equal": True, "default_rr_equal": True,
           "rr_alone_moves_no_w": True, "intrinsic_alone_moves_no_w": True, "rr_moved": False, "order_independent": True,
           "demand_ratio_one": True, "core_rr_equal": True, "pulse_equal": True, "candidate": list(VALIDATION_CANDIDATE),
           "domains": {name: True for name in UPSTREAM_DOMAINS}}
    for (tgain, factor, name, case), seen in sorted(store.items(), key=lambda kv: str(kv[0])):
        if not seen:
            continue
        (_, lam), (survivor, traj) = sorted(seen.items(), key=lambda kv: str(kv[0]))[0]
        entry, bag = ra._entry(name, survivor, region["source"], region["support"])
        intrinsic = i57 if case == C57 else i72
        gas = {**ab.authored_gas(case), "intrinsic": intrinsic}
        tone = {"deficit_to_tone_gain": tgain, "afterload_sensitivity": AFTERLOAD}
        plain = ab._run_states(entry, case, pt.SCENARIOS[name], factor, LAMBDAS[lam], bag, tone)
        live = ab._run_states(entry, case, pt.SCENARIOS[name], factor, LAMBDAS[lam], bag,
                              {**tone, "deficit_to_acid_gain": b / tau, "acid_clearance_tau_min": tau,
                               "acid_to_drive_gain": drive_gain, "ventilation_efficiency": EFFICIENCY}, gas)
        out["compared"] += 1
        out["default_rr_equal"] &= [row["rr"] for row in plain["rows"]] == traj["rr"][:len(plain["rows"])]
        series = ab.burden_series(traj["deficit"], ab.arrival_burden(case), b, tau)
        states = live["states"]
        out["equal"] &= len(series) >= len(states) and len(traj["pulse"]) >= len(states)
        n = min(len(states), len(series), len(traj["pulse"]))
        burden, pulse = series[:n], list(traj["pulse"][:n])
        out["pulse_equal"] &= pulse == [state.R.pulse_present for state in states[:n]]
        hco3 = hco3_series(burden, case)
        rr = rr_series(burden, pulse, drive_gain, intrinsic)
        frequency = frequency_drive_series(rr, pulse, intrinsic)
        recruitment = recruitment_series(burden, gain)
        w, paco2, ph = gas_series(burden, hco3, pulse, gain)
        anchors, profile = live["anchors"], live["profile"]
        other_rate = replace(profile, acid_to_drive_gain=4.0)
        other_intrinsic = replace(anchors, intrinsic_respiratory_rate=12.0 if intrinsic != 12.0 else 20.0)
        forward = []
        for m, state in enumerate(states[:n]):
            r = vn.ventilated_respiration(state, anchors, profile, vc)
            forward.append(r)
            for got, exp in ((r.acid_burden, burden[m]), (r.respiratory_rate, rr[m]), (r.frequency_drive, frequency[m]),
                             (r.recruitment, recruitment[m]), (r.ventilation, w[m]), (r.paco2, paco2[m]),
                             (r.ph, ph[m]), (r.bicarbonate, hco3[m]), (r.demand_ratio, 1.0)):
                if got is None or exp is None:
                    out["equal"] &= got is exp
                    continue
                out["max_abs_diff"] = max(out["max_abs_diff"], abs(got - exp))
            out["demand_ratio_one"] &= r.demand_ratio == 1.0
            out["core_rr_equal"] &= live["rows"][m]["rr"] == r.respiratory_rate
            s = vn.ventilated_respiration(state, anchors, other_rate, vc)
            u = vn.ventilated_respiration(state, other_intrinsic, profile, vc)
            out["rr_alone_moves_no_w"] &= (s.ventilation, s.paco2, s.ph) == (r.ventilation, r.paco2, r.ph)
            out["intrinsic_alone_moves_no_w"] &= (u.ventilation, u.paco2, u.ph) == (r.ventilation, r.paco2, r.ph)
            out["rr_moved"] |= s.respiratory_rate != r.respiratory_rate and u.respiratory_rate != r.respiratory_rate
        backward = [vn.ventilated_respiration(state, anchors, profile, vc) for state in reversed(states[:n])]
        out["order_independent"] &= backward[::-1] == forward
        out["upstream_equal"] &= len(plain["rows"]) == len(live["rows"]) and all(
            {k: v for k, v in p.items() if k != "rr"} == {k: v for k, v in q.items() if k != "rr"}
            for p, q in zip(plain["rows"], live["rows"])) and all(
            ab._upstream(s) == ab._upstream(t) for s, t in zip(plain["states"], live["states"]))
        for domain, (rows, fields) in UPSTREAM_DOMAINS.items():
            out["domains"][domain] &= _domain_equal(plain, live, rows, fields)
    out["equal"] = out["equal"] and out["max_abs_diff"] <= 1e-9 and out["core_rr_equal"] and out["demand_ratio_one"] \
        and out["pulse_equal"]
    return out


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def p2k2_record() -> dict:
    record = json.loads(P2K2_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2K2_DIGEST or record["verdict"]["verdict"] != ab.READY:
        raise AssertionError("the P2K-2 record is not the committed one")
    return record


def p2k2_reproduced(tables: dict) -> dict:
    """The closed P2K-2 analysis reproduced on the live code: its arrival compatibility and probes, and every table's
    upstream rows (lactate, D, deficit, crystalloid, PRBC) and haemostasis counts."""
    record = p2k2_record()
    upstream = all(tables[key]["upstream"] == _json(record["reconstruction"][key]["upstream"]) and
                   tables[key]["haemostasis"] == record["reconstruction"][key]["haemostasis"]
                   for key in record["reconstruction"]) and set(tables) == set(record["reconstruction"])
    return {"arrival_compatibility": _json(ab.arrival_compatibility()) == record["arrival_compatibility"],
            "probes": _json(ab.probes()) == record["probes"], "upstream_tables": upstream}


# 9. Key questions, identifiability, dependencies, decision pack, readiness (P2K-3-8, -11, -12, -15, -16) ---------------------

def resting_paco2_table(joint: list, probes_: dict) -> dict:
    """Question 1: the PaCO2 at no burden and the baseline demand, computed by the ventilation module on core states with
    each intrinsic RR declared on the anchors, every drive gain and every ventilation gain (probe H's rows; review B1: it
    was the bare algebra, which never read the intrinsic RR), and P2K-2's resting PaCO2 over the same RR candidates."""
    rows = {}
    for row in probes_["H"]["rows"]:
        rows.setdefault(f"{row['intrinsic']:g}", {}).setdefault(f"{row['gain']:g}", set()).add(row["paco2"])
    old = {case: ab._spread([ab.resting_paco2(g, i57 if case == C57 else i72, case) for g, i57, i72, _ in joint])
           for case in CASES}
    return {"p2k3": {i: {g: sorted(v) for g, v in by.items()} for i, by in rows.items()},
            "all_reference": bool(probes_["H"]["rows"]) and all(r["paco2"] == PACO2_REFERENCE and r["w"] == 1.0
                                                                 for r in probes_["H"]["rows"]),
            "intrinsic_covered": sorted({r["intrinsic"] for r in probes_["H"]["rows"]}) == sorted(INTRINSIC_RR),
            "p2k2_over_the_same_rr_candidates": old}


def key_questions(evaluated: dict, probes_: dict, joint: list) -> dict:
    tally = evaluated["tally"]
    return {
        "1_resting_hypercapnia": resting_paco2_table(joint, probes_),
        "2_paco2_toward_40": {"r4_toward": tally.share("q2_toward"),
                              "by_case": {case: tally.share(f"q2_toward {case}") for case in CASES},
                              "r4_paco2_120": {case: tally.spread(f"q2_paco2_120 {case}") for case in CASES},
                              "r4_distance_120": {case: tally.spread(f"q2_distance_120 {case}") for case in CASES},
                              "r1_paco2_120": {case: tally.spread(f"q2_untreated_paco2_120 {case}") for case in CASES},
                              "structural": "probe H: no burden -> W 1, PaCO2 40 at every intrinsic RR"},
        "3_rr_near_intrinsic_with_reasonable_paco2": {
            "lowest_intrinsic": evaluated["lowest_intrinsic"],
            "joint_share": {case: tally.share(f"q3 {case}") for case in CASES},
            "rr_near": {case: tally.share(f"q3_rr_near {case}") for case in CASES},
            "rr_120_above_intrinsic": {case: tally.spread(f"q3_rr_120_above_intrinsic {case}") for case in CASES},
            "band": f"RR - intrinsic <= {APPROACH_RR:g} and |PaCO2 - 40| <= {REASONABLE_PACO2:g} (diagnostic reading)"},
        "4_72f_early_dip": {"dip": tally.share("q4_dip"),
                            "by_b": {f"{b:g}": tally.share(f"q4_dip {b:g}") for b in STEADY_BURDENS},
                            "depth": tally.spread("q4_dip_depth"),
                            "mechanism": "acid clearance A0 / tau above production B / tau x d0 (B x d0 < A0); lactate "
                                         "reaches no RR term (probe E)"},
        "5_lactate_rr_opposite": tally.share("q5_opposite"),
        "6_rr_paco2_directions": {"same_direction": tally.share("q6_same_direction"),
                                  "opposite_direction": tally.share("q6_opposite_direction"),
                                  "probe_G_course": probes_["G"]["course_rr_rises"] and probes_["G"]["course_paco2_rises"],
                                  "probe_I": probes_["I"]["paco2_rises"] and probes_["I"]["rr_unchanged"],
                                  "probe_B_and_D": probes_["B"]["w_unchanged"] and probes_["D"]["rr_unchanged"]},
        "post_resuscitation": {"rr_haemostasis_step": tally.share("rr_haemostasis_step"),
                               "paco2_haemostasis_step": tally.share("paco2_haemostasis_step"),
                               "no_instant_normalization": tally.share("no_instant_normalization"),
                               "rr_15_after_haemostasis_above_intrinsic":
                                   tally.spread("rr_15_after_haemostasis_above_intrinsic")},
    }


IDENTIFIABILITY_CLASSES = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE")
IDENTIFIABILITY_RULE = (
    "Frozen. The arrival RR and PaCO2 (+/- 3, provisional) are the only authored respiratory constraints; pH is derived "
    "from them. A latent parameter is WELL_CONSTRAINED when one value survives jointly, PARTIALLY_CONSTRAINED when some "
    "but not all do, POORLY_IDENTIFIED when every value survives in some joint combination although the arrival reads it "
    "(a trade-off with another parameter), NON_IDENTIFIABLE when the arrival does not read it (B, tau: no authored "
    "observation after arrival). A composite is WELL_CONSTRAINED when its spread over the joint survivors is at most its "
    "tolerance half-width (RR 3, PaCO2 3, pH 0.03; the recruitment through the PaCO2 it implies), PARTIALLY_CONSTRAINED "
    "when at most the full window, POORLY_IDENTIFIED above, NON_IDENTIFIABLE without survivors. No best set.")


def _latent(values, support) -> str:
    values = set(values)
    if not values:
        return "NON_IDENTIFIABLE"
    if len(values) == 1:
        return "WELL_CONSTRAINED"
    return "POORLY_IDENTIFIED" if values == set(support) else "PARTIALLY_CONSTRAINED"


def _composite(values, tolerance) -> dict:
    values = list(values)
    if not values:
        return {"class": "NON_IDENTIFIABLE"}
    width = max(values) - min(values)
    klass = ("WELL_CONSTRAINED" if width <= tolerance else "PARTIALLY_CONSTRAINED" if width <= 2 * tolerance
             else "POORLY_IDENTIFIED")
    return {"class": klass, "spread": ab._spread(values), "width": width, "tolerance": tolerance}


def identifiability(joint: list) -> dict:
    out = {"intrinsic_rr_57m": {"class": _latent([j[1] for j in joint], INTRINSIC_RR), "values": sorted({j[1] for j in joint})},
           "intrinsic_rr_72f": {"class": _latent([j[2] for j in joint], INTRINSIC_RR), "values": sorted({j[2] for j in joint})},
           "acid_to_drive_gain": {"class": _latent([j[0] for j in joint], DRIVE_GAINS), "values": sorted({j[0] for j in joint})},
           "acid_to_ventilation_gain": {"class": _latent([j[3] for j in joint], VENTILATION_GAINS),
                                        "values": sorted({j[3] for j in joint})},
           "B": {"class": "NON_IDENTIFIABLE", "why": "no authored observation after arrival; the arrival burden is the "
                                                     "authored HCO3's"},
           "acid_clearance_tau": {"class": "NON_IDENTIFIABLE", "why": "as B"},
           "rule": IDENTIFIABILITY_RULE, "composites": {}}
    for case, index in ((C57, 1), (C72, 2)):
        a0 = ab.arrival_burden(case)
        increments = [ab.arrival_rr(j[0], j[index], case) - j[index] for j in joint]
        paco2 = [predicted_paco2(j[3], case) for j in joint]
        out["composites"][case] = {
            "arrival_rr_increment": _composite(increments, RR_TOLERANCE),
            "arrival_recruitment": {"class": _composite(paco2, PACO2_TOLERANCE)["class"],
                                    "spread": ab._spread([vn.ventilation_recruitment(a0, j[3]) for j in joint]),
                                    "why": "the recruitment implies the predicted PaCO2 (40 / recruitment): its class"},
            "predicted_arrival_paco2": _composite(paco2, PACO2_TOLERANCE),
            "predicted_arrival_ph": _composite([predicted_ph(j[3], case) for j in joint], PH_TOLERANCE)}
    return out


def dependencies(evaluated: dict) -> dict:
    """Which upstream uncertainty reaches the respiratory candidate: demand and tone gain through the deficit and the
    burden (medians at 120 compared); MAP_set, the baroreflex and the HR latent region have no path."""
    def medians(quantity):
        return {key: table["minutes"]["120"][quantity].get("median") for key, table in evaluated["tables"].items()}
    out = {}
    for quantity in ("burden", "rr", "paco2", "ph"):
        values = medians(quantity)
        by_demand, by_tone = {}, {}
        for key, value in values.items():
            factor, tgain, name, case = key.split()
            by_demand.setdefault((tgain, name, case), {})[factor] = value
            by_tone.setdefault((factor, name, case), {})[tgain] = value
        demand = [abs(v["x1.1"] - v["x1"]) for v in by_demand.values() if {"x1", "x1.1"} <= set(v)
                  and None not in v.values()]
        tone = [max(v.values()) - min(v.values()) for v in by_tone.values() if len(v) > 1 and None not in v.values()]
        out[quantity] = {"demand_median_difference": ab._spread(demand), "tone_median_spread": ab._spread(tone)}
    return {"by_quantity": out,
            "demand": {"path": "demand -> effective deficit -> acid burden -> drive (RR) and recruitment (W) -> PaCO2 / "
                               "pH; the baseline-relative W reads no demand class directly"},
            "tone_gain": {"path": "g -> T -> output -> delivery -> deficit -> acid burden"},
            "map_set": {"path": "NONE", "proof": "P2J-4 rows_equal: the baroreflex moves only the sympathetic drive; no "
                                                 "deficit, burden, RR or W term reads it"},
            "baroreflex_gain": {"path": "NONE", "proof": "as MAP_set"},
            "hr_latent": {"path": "NONE", "proof": "HR reaches no output, delivery, deficit, D, lactate or burden "
                                                   "(P2I-2AG, P2J-1)"},
            "multiplied": ["demand", "tone_gain"], "semantics_sensitivity": demand_semantics_sensitivity()}


DECISION_ITEMS = {
    "A": ("untreated 57m RR at 120 (R1)", "the acid burden of an uncontrolled haemorrhage drives the rate; how high RR "
                                          "is at 120 min depends on the burden's production and clearance (B, tau), the "
                                          "frequency gain and the intrinsic RR"),
    "B": ("untreated 72f RR at 120 (R1)", "as A for the smaller arrival burden and deficit of 72f; an early dip is "
                                          "possible when clearance exceeds production"),
    "C": ("untreated 57m PaCO2 / pH at 120 (R1)", "compensatory hyperventilation by recruitment (common ventilation "
                                                  "gain) lowers PaCO2 as the burden rises; pH follows HCO3 and PaCO2"),
    "D": ("untreated 72f PaCO2 / pH at 120 (R1)", "as C for 72f"),
    "E": ("RR response to crystalloid (R2: RR120 - RR0)", "crystalloid restores preload and delivery for a while; the "
                                                          "deficit falls, production with it, and RR follows the burden"),
    "F": ("RR response to PRBC without haemostasis (R3: RR120 - RR0)", "red cells restore oxygen content; without "
                                                                       "haemostasis the deficit can return"),
    "G": ("RR at 120 after definitive management (R4)", "with haemostasis and resuscitation the deficit ends and the "
                                                        "burden clears over tau; RR descends toward the intrinsic RR"),
    "H": ("PaCO2 / pH at 120 after definitive management (R4)", "as the burden clears, recruitment fades and PaCO2 "
                                                                "returns toward 40 while HCO3 recovers"),
    "I": ("residual RR above intrinsic at 120 after adequate resuscitation (R4)", "the RR share still driven by the "
                                                                                  "uncleared burden"),
}


def decision_pack(evaluated: dict) -> dict:
    pack = evaluated["pack"]
    out = {}
    for letter, (title, rationale) in DECISION_ITEMS.items():
        items = sorted(name for name in pack.all if name.split()[0] == letter)
        out[letter] = {"title": title, "rationale": rationale, "status": "PREPARED_NOT_APPROVED",
                       "distributions": {name: pack.summary(name) for name in items}}
    return out


ENVELOPE_REQUEST = (
    "untreated RR at 120 min per case (A, B): an educational LOW-HIGH envelope, or none",
    "untreated PaCO2 / pH at 120 per case (C, D): an envelope, or none",
    "RR, PaCO2 and pH at 120 after definitive management (G, H): envelopes, or none",
    "residual RR above intrinsic after adequate resuscitation (I): an envelope, or none",
    "whether the crystalloid and PRBC RR responses (E, F) are constrained or only reported")
FACULTY_QUESTIONS = (
    "confirm the baseline-relative demand semantics of W (the absolute index would make the 1.1 class hypercapnic at "
    "rest)",
    "keep the ventilation gain EXPLORATORY over its joint support, or adopt one (no value is proposed)",
    "the envelopes above, if READY; none is applied in P2K-3")

READY = "RR_VENTILATION_DECISION_SURFACE_READY"
NOT_READY = "RR_VENTILATION_NOT_READY"
CRITERIA = ("rr_not_determining_w", "intrinsic_not_determining_rest", "lactate_d_retired", "arrival_rr_reproduced",
            "arrival_paco2_reproduced", "ph_coherent", "patient_like", "factorization_valid", "upstream_unchanged",
            "nothing_approved")
VERDICT_RULE = (
    "Frozen. READY when every criterion holds: RR does not determine W (probes A, B, D, G, I and no pulse; the static "
    "proof that no assignment to a W-side name and no returned W-side field reads a rate, intrinsic RR or drive name; and "
    "the full-core recomputation with another drive gain); the intrinsic RR determines "
    "neither W nor the resting PaCO2 (probes C and H, question 1: 40 at every intrinsic RR, and the full-core "
    "recomputation with another intrinsic RR); lactate and D reach no RR or W term (probes E, F, the W channel); the "
    "arrival RR is reproduced (at least one RR-compatible candidate) and the arrival PaCO2 with one common ventilation "
    "gain (at least one joint candidate; none is a STOP); pH is coherent (derived by the bicarbonate relation: the formula "
    "probe, and the factorized pH equal to the core's in the validation; every value within the plausible 6.8-7.8; the "
    "bank's reconstruction within 0.005); the trajectories are patient-like (W > 0 and "
    "PaCO2 > 0 wherever breathing; in every R4 combination RR stays at least 1 breath/min above intrinsic 15 min after "
    "haemostasis, and the haemostasis minute moves RR and PaCO2 no more than another minute); the factorization is valid "
    "(the core equals it, order independent); the upstream is unchanged (rows and states equal, the P2J-3 region, P2K-1 "
    "and P2K-2 reproduced, the default RR, the core files at their P2K-2 hashes); nothing is approved. Otherwise "
    "NOT_READY with the first failing criterion as the blocker; an early stop "
    "evaluates only the criteria it reached and lists the others as not evaluated. The acid burden is never required to "
    "rise.")


def verdict(checks: dict) -> dict:
    """READY when every criterion is evaluated and holds; otherwise the first failing criterion, in CRITERIA order, is the
    blocker. A criterion an early stop never reached is listed as not evaluated, never counted as failing (review M1)."""
    failing = [name for name in CRITERIA if checks.get(name) is False]
    unevaluated = [name for name in CRITERIA if name not in checks]
    if failing:
        result = f"{NOT_READY} - {failing[0].upper()}"
    else:
        result = READY if not unevaluated else f"{NOT_READY} - NOT_EVALUATED"
    return {"verdict": result, "checks": checks, "failing": failing, "not_evaluated": unevaluated}


POLICY = ("Shadow only. The P2K-3 candidate is the P2K-2 acid-base profile plus a ventilation gain read by "
          "clinical_core.ventilation, which no core step reads; the core files are unchanged. Supports predeclared and "
          "exploratory; nothing selected or approved; no envelope filters any trajectory (ANALYTIC_REJECTION and "
          "SIMULATION_REJECTION mark only impossible values); pH never filters; the legacy RR is never read.")

# 10. Closure: the core untouched, P2K-2's freeze map ------------------------------------------------------------------------

CORE_AT_P2K2 = {"clinical_core/derived.py": "b9056ada72f4c651974eccd1069a67097d31814a5d691cbfc883e33d85bb77a6",
                "clinical_core/integration.py": "dad171baff07805997272310f4f33545ed38956b531585ae246c0e26e8c07b7a",
                "clinical_core/state.py": "578d32abad60fcda31a4d3344532b709c8c8f8b71ea2f4bdb2f88c37265a6d13",
                "clinical_core/acid_base.py": "9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954"}
OWN = ("clinical_core/ventilation.py", "clinical_core/ventilation_surface.py")
REPORT = "clinical_core/ventilation_surface_report.py"
#: The two tuple-only files at P2K-2 (cbec249): P2K-3 adds its modules to their tuples, nothing else.
TUPLE_AT_P2K2 = {"clinical_core/lactate_slice.py": "5a3144db140b9263c53ed6862cf07015ff20e514d7e1b53a7fdd91f71a38df34",
                 "clinical_core/decision_pack.py": "dd6ca89a86c14454001e63795b27fc9f6c9767bdafa1f5a8986e48c13623b5e2"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": ("clinical_core/ventilation_surface.py", REPORT)}


def core_unchanged() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in CORE_AT_P2K2.items()}


def p2k2_sources(sources: dict) -> dict:
    """A P2K-2 dependency map: P2K-3's modules removed, the two tuple-only files at their P2K-2 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2K2.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


# 11. Design, freeze, run ----------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "carried": CARRIED, "semantics": SEMANTICS,
            "status": STATUS, "ventilation_status": vn.STATUS, "future": FUTURE_RESPIRATORY_GENERALIZATION,
            "intrinsic_rr": list(INTRINSIC_RR), "drive_gains": list(DRIVE_GAINS), "steady_burdens": list(STEADY_BURDENS),
            "acid_taus": list(ACID_TAUS), "saturation": SATURATION, "ventilation_gains": list(VENTILATION_GAINS),
            "faculty_implied_gains": FACULTY_IMPLIED_GAINS, "efficiency": EFFICIENCY, "paco2_reference": PACO2_REFERENCE,
            "hco3_reference": HCO3_REFERENCE, "rr_tolerance": RR_TOLERANCE, "paco2_tolerance": PACO2_TOLERANCE,
            "ph_tolerance": PH_TOLERANCE, "authored_rr": AUTHORED_RR, "paco2_windows": PACO2_WINDOWS,
            "ph_plausible": list(PH_PLAUSIBLE), "approach_rr": APPROACH_RR, "reasonable_paco2": REASONABLE_PACO2,
            "candidate_rule": CANDIDATE_RULE, "w_functions": list(W_FUNCTIONS), "w_targets": list(W_TARGETS),
            "w_returned": list(W_RETURNED),
            "w_forbidden": sorted(W_FORBIDDEN), "probe_gain": PROBE_GAIN, "probe_rule": PROBE_RULE,
            "reconstruction_rule": RECONSTRUCTION_RULE, "sensitivity_factors": list(SENSITIVITY_FACTORS),
            "validation_candidate": list(VALIDATION_CANDIDATE), "upstream_domains": UPSTREAM_DOMAINS,
            "identifiability_rule": IDENTIFIABILITY_RULE,
            "decision_items": DECISION_ITEMS, "envelope_request": list(ENVELOPE_REQUEST),
            "faculty_questions": list(FACULTY_QUESTIONS), "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE,
            "policy": POLICY, "core_at_p2k2": CORE_AT_P2K2, "own": list(OWN), "report": REPORT,
            "tuple_at_p2k2": TUPLE_AT_P2K2, "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2k2": hashlib.sha256(P2K2_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stopped(out: dict, checks: dict, why: str) -> dict:
    out["stopped"] = why
    out["verdict"] = verdict(checks)
    return out


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2k2_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2K2_DIGEST, "design": design()}
        say("structure, proofs and probes")
        proof = w_inputs()
        probes_ = probes()
        passed = probes_pass(probes_)
        core = core_unchanged()
        # The criteria the structure alone can fail, before any count (each completed after the trajectories).
        checks = {"rr_not_determining_w": all(passed[k] for k in ("A", "B", "D", "G", "I", "no_pulse"))
                  and not proof["leaks"] and proof["targets_found"] == sorted(W_TARGETS)
                  and proof["returned_found"] == sorted(W_RETURNED),
                  "intrinsic_not_determining_rest": passed["C"] and passed["H"],
                  "lactate_d_retired": passed["E"] and passed["F"] and passed["W_channel"],
                  "ph_coherent": passed["pH"], "upstream_unchanged": all(core.values()), "nothing_approved": True}
        out.update({"w_inputs": proof, "probes": probes_, "probes_pass": passed, "core_unchanged": core})
        if not all(checks.values()):
            return _stopped(out, checks, "a structural probe or proof failed, or a core file changed")
        say("arrival joint surface")
        rr = ab.arrival_compatibility()
        paco2 = paco2_compatibility()
        surface = joint_surface(rr, paco2)
        out.update({"authored_gas": {case: ab.authored_gas(case) for case in CASES},
                    "arrival_burden": {case: ab.arrival_burden(case) for case in CASES},
                    "exact_ventilation_gains": exact_ventilation_gains(), "arrival_rr": rr, "arrival_paco2": paco2,
                    "arrival_rejections": arrival_rejections(), "joint_surface": surface,
                    "demand_semantics": demand_semantics_sensitivity()})
        checks["arrival_rr_reproduced"] = rr["count"] > 0
        checks["arrival_paco2_reproduced"] = bool(surface["joint"])
        if not surface["joint"]:
            return _stopped(out, checks, "no common arrival candidate (P2K-3-3): STOP, the tolerance is not widened")
        say("certified physiology (P2J-3 region)")
        region = br.pressure_tone_region(map_, say)
        arrivals = lr.arrival_table()
        say("deficit trajectories")
        store = ab.reconstruct(region, arrivals)
        say("validation against the core")
        validation = validate(region, store)
        out["validation"] = validation
        checks["factorization_valid"] = validation["equal"] and validation["order_independent"]
        if not checks["factorization_valid"]:
            return _stopped(out, checks, "the factorization does not reproduce the core (P2K-3-10): STOP")
        say("respiratory reconstruction")
        evaluated = evaluate(store, surface["joint"])
        reproduced = p2k2_reproduced(evaluated["tables"])
        p2k1 = ab.p2k1_unchanged(store)
        questions = key_questions(evaluated, probes_, surface["joint"])
        plausible = evaluated["plausible"]
        post = questions["post_resuscitation"]
        checks.update({
            "rr_not_determining_w": checks["rr_not_determining_w"] and validation["rr_alone_moves_no_w"]
            and validation["rr_moved"],
            "intrinsic_not_determining_rest": checks["intrinsic_not_determining_rest"]
            and questions["1_resting_hypercapnia"]["all_reference"]
            and questions["1_resting_hypercapnia"]["intrinsic_covered"] and validation["intrinsic_alone_moves_no_w"],
            "ph_coherent": checks["ph_coherent"] and plausible["outside"] == 0
            and all(abs(ab.ph_reconstruction(case)["error"]) <= 0.005 for case in CASES),
            "patient_like": plausible["non_positive"] == 0 and plausible["paco2_low"] is not None
            and plausible["paco2_low"] > 0.0
            and post["no_instant_normalization"]["n"] > 0
            and post["no_instant_normalization"]["true"] == post["no_instant_normalization"]["n"]
            and post["rr_haemostasis_step"]["true"] == post["rr_haemostasis_step"]["n"] > 0
            and post["paco2_haemostasis_step"]["true"] == post["paco2_haemostasis_step"]["n"] > 0,
            "upstream_unchanged": checks["upstream_unchanged"] and validation["upstream_equal"]
            and validation["default_rr_equal"]
            and all(validation["domains"].values())
            and all(region["unchanged"].values()) and p2k1 and all(reproduced.values())})
        out.update({
            "pressure_tone_unchanged": region["unchanged"], "p2k1_unchanged": p2k1,
            "p2k2_reproduced": reproduced, "reconstruction": evaluated["tables"],
            "rejections": evaluated["rejections"], "plausible": plausible, "key_questions": questions,
            "identifiability": identifiability(surface["joint"]), "dependencies": dependencies(evaluated),
            "decision_pack": decision_pack(evaluated),
            "efficiency": {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs": region["counterfactual_runs"],
                           "deficit_trajectories": sum(len(seen) for seen in store.values()),
                           "acid_pairs": len(ab.acid_pairs()), "rr_candidates": {c: len(v) for c, v in
                                                                                 evaluated["rr_set"].items()},
                           "ventilation_gains": len(evaluated["gains"]), "core_validation_runs": 2 * validation["compared"],
                           "cartesian_sweep": False, "legacy_read": False,
                           "rr_w_crossed_only_for": ["key question 3 (RR near intrinsic with PaCO2 near 40)",
                                                     "key question 6 (RR and PaCO2 directions)"],
                           "arrival_combinations": surface["with_acid_support"]["total"]}})
        out["verdict"] = verdict(checks)
        if out["verdict"]["verdict"] == READY:
            out["envelope_request"] = list(ENVELOPE_REQUEST)
        out["faculty_questions"] = list(FACULTY_QUESTIONS)
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
        (args.out / "ventilation_surface.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str)
                                                           + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
