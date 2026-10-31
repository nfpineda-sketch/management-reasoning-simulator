"""Phase 2 shadow core, P2K-1: the RR / ventilatory-drive structural audit and decision surface.

    python -m clinical_core.rr_audit --digest
    python -m clinical_core.rr_audit --design
    python -m clinical_core.rr_audit --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-31, recorded in FACULTY). The first respiratory package: it makes the
current RR derivation explicit, classifies every path into RR, audits W (C7) and the acid-base representation, runs the
structural probes A-E, audits respiratory support and the authored respiratory observations, reconstructs the current
RR trajectories of the certified physiology without changing a parameter, and reads the directional expectations, the
upstream dependencies and identifiability. The core is not changed: the audit finds no correction that is clear
without a new state (the lactate path is the only metabolic compensation the core has, and replacing it needs an
acid-base state the faculty has not authorized). No candidate surface is built while the structure is not coherent;
nothing is approved; the legacy RR is never read.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from . import baroreflex as br
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import gi_reference
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import vascular_tone as vt
from .derived import DEFAULT_PROFILE, arrival_state, derive, respiratory_rate
from .integration import step
from .interventions.oxygen import Oxygen

DECIDED = "2026-10-31"
REVISION = "P2K-1"
ROOT = br.ROOT
CASES = br.CASES
C57, C72 = br.C57, br.C72
DEMANDS = br.DEMANDS
TONE_GAINS = br.TONE_GAINS
AFTERLOAD = br.AFTERLOAD
LAMBDAS = br.LAMBDAS
RESERVE = vt.RESERVE
P2J4_RECORD = ROOT / "docs" / "revision" / "P2J4_baroreflex.json"
P2J4_DIGEST = "81ab565efb3170ee9e7e4683c3198495004d30c7dfdadce09f551d66547dedf6"

FACULTY = {
    "decided": DECIDED,
    "closed": "P2J-4 accepted (BAROREFLEX_HR_RECERTIFICATION_SATISFIED); BloodState, preload, P, T, the pressure mapping, "
              "D, lactate and HR / baroreflex stay closed and are not reopened or silently recalibrated",
    "carried": "MAP_set 80 / 90 / 100 not selected; baroreflex gain conditional on demand (1.0: 0.25 / 0.5; 1.1: 0.25 / "
               "0.5 / 1.0 / 1.5), not collapsed into one range; nothing FACULTY_APPROVED",
    "w_rr": "W is effective alveolar ventilation relative to physiologic need (drive, mechanics, fatigue where "
            "represented); RR is an observable; higher RR is not automatically higher effective ventilation",
    "lactate": "lactate concentration is a biomarker, not itself a respiratory controller; a lactate-related path is "
               "acceptable only as an explicit metabolic acid load, acidaemia or CO2-production signal in the state "
               "model; a direct lactate -> RR mapping is BIOMARKER_PROXY_REQUIRES_REFACTOR and its gain is not tuned",
    "kd_s1": "RR from ventilatory need / W plus metabolic / acidaemic drive; no lactate-clearance-induced bradypnoea while "
             "ventilatory need remains",
    "d": "D is not accepted as a direct ventilatory controller",
    "early_stop": "a needed new major state (mechanics, fatigue, PaCO2, acid-base controller) stops the package before "
                  "any numeric range; missing physiology is not hidden behind RR gains",
    "scope": "shadow only; no runtime integration, GI or second-family migration, final RR approval, RR hard envelope, "
             "consciousness recalibration, collapse activation, legacy fitting or upstream recalibration",
}
CARRIED = {"map_set": list(br.MAP_SETS), "baroreflex_gain": {"1": [0.25, 0.5], "1.1": [0.25, 0.5, 1.0, 1.5]},
           "tone_gain": list(TONE_GAINS), "afterload": AFTERLOAD, "demand": list(DEMANDS), "approved": []}

# 1. The current equation and every contributor (P2K-1-1, -2) ----------------------------------------------------------

EQUATION = (
    "derive(state) -> lactate L = max(min(floor, L_arrival), baseline + aux.lactate_excess); RR = "
    "respiratory_rate(state, anchors, profile, L). With M(x) = rr_metabolic_max x (1 - exp(-rr_per_lactate x max(0, x - "
    "lactate_drive_threshold) / rr_metabolic_max)): the arrival RR splits into an arrival metabolic share S = min(M(L0), "
    "max(0, RR0 - rr_ventilatory_floor)) and a ventilatory part (RR0 - S) x (1 + max(0, W)); the metabolic part is S + "
    "M(L) - M(L0) when M(L) >= M(L0), else S x M(L) / M(L0); RR = min(rr_max, max(0, 1 + min(0, W)) x (ventilatory + "
    "metabolic)); 0 without a pulse. L0 and RR0 are the authored arrival lactate and RR. The aux lactate excess follows "
    "dX = debt_to_lactate_gain x D - X / tau_lactate on the minute before's D.")
RR_PARAMETERS = ("rr_per_lactate", "lactate_drive_threshold_mmol_l", "rr_metabolic_max", "rr_ventilatory_floor", "rr_max")
CLASSES = ("VALID_CAUSAL_PATH", "BIOMARKER_PROXY", "SEMANTIC_LEAK", "LEGACY_ARTIFACT", "NOT_CURRENTLY_MODELED")
BIOMARKER_PROXY_REQUIRES_REFACTOR = "BIOMARKER_PROXY_REQUIRES_REFACTOR"
CONTRIBUTORS = (
    {"name": "baseline / intrinsic RR", "class": "VALID_CAUSAL_PATH",
     "path": "anchors.respiratory_rate, the authored arrival RR (26 / 24): the arrival fixed point and the ventilatory "
             "part's scale; no intrinsic or resting RR exists apart from it"},
    {"name": "arrival metabolic share", "class": "BIOMARKER_PROXY",
     "path": "S = min(M(arrival lactate), RR0 - floor): part of the authored arrival RR is attributed to the arrival "
             "lactate concentration, not to an acid load"},
    {"name": "W", "class": "SEMANTIC_LEAK",
     "path": "W > 0 multiplies the ventilatory part (read as load or drive), W < 0 scales the whole RR down (depressed "
             "drive); W is defined as ventilation relative to need, so the two signs read two different physiologies; no "
             "GI module writes W"},
    {"name": "effective oxygen deficit", "class": "NOT_CURRENTLY_MODELED",
     "path": "no direct path; it reaches RR only through D -> lactate production -> lactate concentration"},
    {"name": "D", "class": "BIOMARKER_PROXY",
     "path": "no direct read; D produces lactate (debt_to_lactate_gain x D, lactate_after_minute), and the lactate "
             "concentration drives RR: the P2I-2AC D change moved RR through this chain"},
    {"name": "lactate", "class": "BIOMARKER_PROXY",
     "path": "the derived lactate concentration drives the metabolic part directly (_metabolic_drive, documented as "
             "'acidaemia'); no acid load, pH or bicarbonate stands behind it: " + BIOMARKER_PROXY_REQUIRES_REFACTOR},
    {"name": "lactate gain value", "class": "LEGACY_ARTIFACT",
     "path": "rr_per_lactate 7.5 is the legacy GI RR gain (15 per circulation unit / lactate 2 per unit), PARAMETERS"},
    {"name": "pH", "class": "NOT_CURRENTLY_MODELED", "path": "no state or derived output; authored ABG only"},
    {"name": "pCO2", "class": "NOT_CURRENTLY_MODELED", "path": "no state or derived output; authored ABG only"},
    {"name": "metabolic demand", "class": "NOT_CURRENTLY_MODELED",
     "path": "no CO2-production path; demand reaches RR only through the deficit -> D -> lactate chain"},
    {"name": "hypoxaemia", "class": "NOT_CURRENTLY_MODELED",
     "path": "RR reads no SpO2; hypoxaemia drives the sympathetic HR drive only (sympathetic_target)"},
    {"name": "glucose", "class": "NOT_CURRENTLY_MODELED", "path": "RR reads no glucose (the sympathetic drive does)"},
    {"name": "drugs", "class": "NOT_CURRENTLY_MODELED",
     "path": "demand modifiers reach RR only through the lactate chain; respiratory depressants exist only as the "
             "synthetic W -0.7 probe (bands 'opioid')"},
    {"name": "respiratory support", "class": "NOT_CURRENTLY_MODELED",
     "path": "Oxygen sets FiO2, which moves SpO2 only; no NIV, invasive ventilation, PEEP or mode"},
    {"name": "mechanics", "class": "NOT_CURRENTLY_MODELED",
     "path": "no mechanics state; the synthetic W +0.5 'work' probe (bands 'bronchospasm') raises RR"},
    {"name": "fatigue", "class": "NOT_CURRENTLY_MODELED", "path": "no fatigue state"},
    {"name": "caps / floors", "class": "VALID_CAUSAL_PATH",
     "path": "rr_max (safety bound), rr_metabolic_max (saturation), rr_ventilatory_floor (split bound), max(0, ...) on "
             "the W < 0 scaling: bounds, not physiology"},
    {"name": "case-specific terms", "class": "VALID_CAUSAL_PATH",
     "path": "only the authored arrival RR and lactate of each case (anchors); no case gain"},
    {"name": "legacy terms", "class": "LEGACY_ARTIFACT",
     "path": "the lactate gain's value (above); no legacy RR is read at run time"},
)
D_PATH = (
    ("integration.step", "_oxygen_debt writes D for the minute from the delivery shortfall (demand, delivery, reserve)"),
    ("integration.step", "aux.lactate_excess_mmol_l = lactate_after_minute(state, profile): production "
                         "debt_to_lactate_gain x D of the minute before, clearance X / tau_lactate"),
    ("derived.derive", "lactate = max(min(lactate_floor, anchors.lactate), lactate_baseline + lactate_excess)"),
    ("derived.derive", "rr = respiratory_rate(state, anchors, profile, lactate)"),
    ("derived.respiratory_rate", "metabolic part from _metabolic_drive(lactate); state.W the only other state read"),
)


def _reads(function) -> dict:
    """The attributes and names a function reads (its source AST)."""
    import ast
    tree = ast.parse(inspect.getsource(function))
    attributes = sorted({f"{n.value.id}.{n.attr}" for n in ast.walk(tree)
                         if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)})
    calls = sorted({n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)})
    return {"attributes": attributes, "calls": calls}


def rr_reads() -> dict:
    return {"respiratory_rate": _reads(dv.respiratory_rate), "_metabolic_drive": _reads(dv._metabolic_drive),
            "lactate_after_minute": _reads(dv.lactate_after_minute)}


# 2. W (P2K-1-4) and the acid-base representation (P2K-1-3) -------------------------------------------------------------

W_CLASSES = ("COHERENT_EFFECTIVE_VENTILATION_STATE", "MIXED_DRIVE_AND_VENTILATION_CONSTRUCT", "INSUFFICIENTLY_SPECIFIED")
W_AUDIT = {
    "meaning": "C7, 'deviation of alveolar ventilation relative to need (drive, mechanics, fatigue)' (state.py), 0 at "
               "arrival; integration bounds it to [-10, 10] as a guard ('no module writes W yet')",
    "arrival": 0.0,
    "change": "only through contributor deltas; no core equation moves W",
    "writers": "no GI or core module; only the synthetic calibration probes (bands 'bronchospasm' W +0.5 as work, "
               "'opioid' W -0.7 as drive)",
    "readers": "derived.respiratory_rate only in the physiology (not SpO2, D, lactate or HR); the offline P2G "
               "decision pack keeps a copy of the RR split (decision_pack.rr_parts) and checks W = 0 at a GI arrival",
    "rr": "W > 0 multiplies the ventilatory part of RR; W < 0 scales the whole RR down",
    "pco2": "NOT_MODELED (no pCO2)",
    "ph": "NOT_MODELED (no pH)",
    "support": "oxygen (FiO2) does not touch W; NIV and invasive ventilation do not exist",
    "spontaneous_mechanical": "not representable: there is no mechanical ventilation",
    "class": "MIXED_DRIVE_AND_VENTILATION_CONSTRUCT",
    "why": "defined as ventilation relative to need, read as a drive / load: a bronchospasm load (less effective "
           "ventilation) is written as W > 0 and raises RR, a depressed drive (less ventilation) as W < 0 and lowers it; "
           "no output reports effective ventilation, and RR is the only ventilatory observable",
}
ACID_BASE_CLASSES = ("STATE_VARIABLE", "DERIVED_OUTPUT", "AUTHORED_OBSERVATION_ONLY", "NOT_MODELED")
ACID_BASE = {
    "pH": {"class": "AUTHORED_OBSERVATION_ONLY", "where": "arrival ABG of each case (gi_reference 'abg')"},
    "pCO2": {"class": "AUTHORED_OBSERVATION_ONLY", "where": "arrival ABG (PaCO2 31 / 33 mmHg)"},
    "bicarbonate": {"class": "AUTHORED_OBSERVATION_ONLY",
                    "where": "computed by the case bank from pH and PaCO2 (clinical_cases.py:251), not authored"},
    "metabolic acid load": {"class": "NOT_MODELED", "where": "no state; lactate concentration stands in for it in RR"},
    "respiratory compensation": {"class": "NOT_MODELED",
                                 "where": "only the lactate-concentration term of RR; no pCO2 to compensate"},
}
ACIDOSIS_TO_DRIVE = {"representable_without_lactate": False,
                     "why": "no state or derived quantity carries an acid load, pH, bicarbonate or pCO2; the only "
                            "metabolic input to RR is the lactate concentration"}

# 3. Structural probes A-E and the path probes (P2K-1-5, -6, -7) ------------------------------------------------------------

NOT_REPRESENTABLE = "NOT_REPRESENTABLE"
PROBE_PROFILE = {"oxygen_extraction_reserve": RESERVE}
PROBE_LACTATE = 6.0
#: The neutral arrival with its lactate above the drive threshold (2.0), so that a rise or a fall of lactate is read.
PROBE_ANCHORS = replace(vt.NEUTRAL, lactate=2.5)
PROBE_PUMP = 0.3
PROBE_MINUTES = 20
PROBE_RULE = (
    "Synthetic, structural only (no gain read from them), on the neutral arrival (RR0 16, demand met, FiO2 0.21) with its "
    "lactate at 2.5 (above the 2.0 drive threshold, so a change is read), at the default RR parameters with reserve 2.5. A: an acid load with normal delivery is not representable. "
    "B: the RR the core derives at lactate 6 with no deficit, no D and W 0, against arrival. C: the pump cut to 0.3 for "
    "20 minutes (an effective deficit, D accruing) with the default lactate production and with production 0 (lactate "
    "held), so any RR response is attributed to its path. D: pCO2 is not representable; W -0.5 (the only 'inadequate "
    "ventilation' the core can write) is read. E: an effective-ventilation output separate from RR does not exist; W "
    "+0.5 is read. Hypoxaemia: arrival SpO2 85 against 97. Oxygen: FiO2 0.6 from minute 1. Clearance: the same steady D "
    "with tau_lactate 30 and 120 min.")


def _profile(**changes):
    return replace(DEFAULT_PROFILE, **PROBE_PROFILE, **changes)


def _rr_at(state, anchors, profile, lactate=None) -> float:
    view = derive(state, anchors, profile)
    return view.respiratory_rate if lactate is None else respiratory_rate(state, anchors, profile, lactate)


def _pump_course(profile, minutes=PROBE_MINUTES) -> list:
    anchors = PROBE_ANCHORS
    state = arrival_state(anchors, profile).evolve(P=PROBE_PUMP)
    out = [derive(state, anchors, profile)]
    for _ in range(minutes):
        state, _ = step(state, (), anchors, profile)
        out.append(derive(state, anchors, profile))
    return [{"rr": v.respiratory_rate, "lactate": v.lactate} for v in out], state


def probes() -> dict:
    anchors, profile = PROBE_ANCHORS, _profile()
    start = arrival_state(anchors, profile)
    rr0 = _rr_at(start, anchors, profile)
    b = _rr_at(start, anchors, profile, PROBE_LACTATE)
    on, end_on = _pump_course(profile)
    off, end_off = _pump_course(_profile(debt_to_lactate_gain=0.0))
    low_w = _rr_at(start.evolve(W=-0.5), anchors, profile)
    high_w = _rr_at(start.evolve(W=0.5), anchors, profile)
    hypox = _rr_at(arrival_state(replace(anchors, spo2=85.0), profile), replace(anchors, spo2=85.0), profile)
    oxy_state, _ = step(start, (Oxygen("oxygen", 1, 0.6),), anchors, profile)
    oxy_state, _ = step(oxy_state, (Oxygen("oxygen", 1, 0.6),), anchors, profile)
    oxy = derive(oxy_state, anchors, profile)
    clearance = {}
    for tau in (30.0, 120.0):
        prof = _profile(lactate_clearance_tau_min=tau)
        state = start.evolve(D=20.0)
        for _ in range(60):
            excess = dv.lactate_after_minute(state, prof)
            state = state.evolve(aux=replace(state.aux, lactate_excess_mmol_l=excess))
        clearance[f"{tau:g}"] = {"lactate": derive(state, anchors, prof).lactate, "rr": _rr_at(state, anchors, prof)}
    return {
        "arrival_rr": rr0,
        "A": {"what": "normal oxygen delivery + metabolic acidosis", "result": NOT_REPRESENTABLE,
              "pathway": "none: no acid-load, pH or bicarbonate input exists; only a lactate rise would move RR (B)"},
        "B": {"what": "high lactate + normal acid-base / ventilatory need", "lactate": PROBE_LACTATE, "rr": b,
              "rise": b - rr0, "deficit": 0.0, "D": start.D, "W": start.W,
              "result": "RR_RISES_FROM_LACTATE_ALONE" if b > rr0 else "NO_RR_RISE",
              "pathway": "lactate concentration -> _metabolic_drive -> RR (BIOMARKER_PROXY)"},
        "C": {"what": "effective oxygen deficit + normal acid-base state", "minutes": PROBE_MINUTES,
              "with_lactate_production": {"rr": [r["rr"] for r in on], "lactate": [r["lactate"] for r in on],
                                          "D_end": end_on.D},
              "lactate_held": {"rr": [r["rr"] for r in off], "lactate": [r["lactate"] for r in off], "D_end": end_off.D},
              "first_minute_rr_change": on[1]["rr"] - on[0]["rr"],
              "rr_moves_only_with_lactate": all(r["rr"] == off[0]["rr"] for r in off) and on[-1]["rr"] > on[0]["rr"],
              "pathway": "deficit -> D -> lactate production -> lactate concentration -> RR; no direct deficit or D read"},
        "D": {"what": "high pCO2 / inadequate W", "result": NOT_REPRESENTABLE, "w_minus_half_rr": low_w,
              "pathway": "no pCO2; the only writable 'inadequate ventilation' is W < 0, read as depressed drive: RR falls "
                         "(no compensation)"},
        "E": {"what": "RR high + mechanical / fatigue limitation", "result": NOT_REPRESENTABLE, "w_plus_half_rr": high_w,
              "pathway": "no effective-ventilation output apart from RR; a load written as W > 0 raises RR and nothing "
                         "reports that ventilation stays inadequate"},
        "hypoxaemia": {"spo2_85_rr": hypox, "spo2_97_rr": rr0, "independent_drive": hypox != rr0},
        "oxygen": {"fio2": 0.6, "spo2": oxy.spo2, "spo2_room_air": derive(start, anchors, profile).spo2,
                   "rr": oxy.respiratory_rate, "rr_room_air": rr0, "W": oxy_state.W,
                   "oxygenation_only": oxy.spo2 > derive(start, anchors, profile).spo2
                   and oxy.respiratory_rate == rr0 and oxy_state.W == 0.0},
        "clearance": {**clearance, "same_D": 20.0,
                      "rr_follows_clearance": clearance["30"]["rr"] != clearance["120"]["rr"]},
    }


# 4. Respiratory support (P2K-1-7) and authored observations (P2K-1-8) ---------------------------------------------------

SUPPORT = {
    "supplemental oxygen": "Oxygen writes the FiO2 setting; SpO2 = arrival SpO2 + 30 x (FiO2 - arrival FiO2 above room "
                           "air); W, RR, D and lactate unchanged by it",
    "NIV / BiPAP": "NOT_MODELED", "invasive ventilation": "NOT_MODELED", "FiO2": "a setting; read by SpO2 only",
    "PEEP": "NOT_MODELED", "ventilation mode": "NOT_MODELED",
    "pCO2 / pH": "NOT_MODELED: no support can move them",
    "mechanical override": "NOT_REPRESENTABLE: with no mechanical ventilation, no controlled rate can override the "
                           "spontaneous RR; no current scenario ventilates, so there is no live contradiction",
    "gi_scenarios": "L1, L2, L3 without haemostasis and L3 carry no oxygen or ventilatory support (room air, FiO2 0.21)",
}
RESPIRATORY_ITEMS = ("respiratory_rate", "spo2", "abg", "oxygen_support", "lactate_mmol_l", "lungs")


def _origin(item) -> str:
    if item.source.startswith("family_engine.py"):
        return "LEGACY_REFERENCE"
    if "derived" in str(item.value) or "computed" in item.note:
        return "MODEL_DERIVED"
    return "AUTHORED_OBSERVATION"


def authored() -> dict:
    out = {case: {} for case in CASES}
    for item in gi_reference.INVENTORY:
        if item.case in out and item.item in RESPIRATORY_ITEMS:
            entry = {"value": item.value, "source": item.source, "origin": _origin(item)}
            if item.item == "abg":
                entry["parts"] = {"pH": "AUTHORED_OBSERVATION", "PaCO2": "AUTHORED_OBSERVATION",
                                  "PaO2": "AUTHORED_OBSERVATION", "HCO3": "MODEL_DERIVED (computed by the case bank)"}
                entry["origin"] = "AUTHORED_OBSERVATION"
            out[item.case][item.item] = entry
        out[item.case].setdefault("work_of_breathing", {"value": "not stated", "origin": "NOT_STATED"})
        out[item.case].setdefault("later_respiratory_observations", {"value": "none authored", "origin": "NOT_STATED"})
    return out


# 5. The current RR trajectories (P2K-1-9), reconstructed from the certified physiology ---------------------------------

R_SCENARIOS = {"R1": ("P1", "untreated haemorrhage (L1)"), "R2": ("P2", "crystalloid (L2)"),
               "R3": ("P3", "PRBC before haemostasis (L3 without haemostasis)"), "R4": ("P4", "definitive (L3)")}
MINUTES_REPORTED = (0, 15, 30, 60, 90, 120)
RECONSTRUCTION_RULE = (
    "RR is a pure function of W, the authored arrival RR and lactate, the RR parameters and the derived lactate "
    "(respiratory_rate). The certified physiology's lactate is P2J-3's: its primary region recomputed "
    "(baroreflex.pressure_tone_region), each survivor's blood trajectory rebuilt at its tone gain (vascular_tone.rebuild) "
    "and its D and lactate read by the lactate machinery (vascular_tone.debt_and_lactate), both exact against the core. "
    "RR is then derived with W = 0 and the default RR parameters, with no parameter changed; one full core run per "
    "scenario, case, demand and tone gain checks it. HR, MAP_set and the baroreflex gain do not reach RR, so they are not "
    "multiplied in.")


def rr_from_lactate(anchors, lactate: float, pulse: bool = True, w: float = 0.0, profile=DEFAULT_PROFILE) -> float:
    return respiratory_rate(SimpleNamespace(W=w), anchors, profile, lactate) if pulse else 0.0


def _ventilatory_part(anchors, profile=DEFAULT_PROFILE) -> float:
    share = min(dv._metabolic_drive(anchors.lactate, profile),
                max(0.0, anchors.respiratory_rate - profile.rr_ventilatory_floor))
    return anchors.respiratory_rate - share


def _blood_key(name: str, case: str, survivor: tuple):
    i, a, b, q, d = survivor
    return {"P1": ("P1", case, i), "P2": ("P2", case, (i, d)), "P3": ("P3", case, q), "P4": ("P4", case, q)}[name]


def _entry(name, survivor, source, support):
    i, a, b, q, d = survivor
    if name == "P1":
        return source["p1"][i], None
    if name == "P2":
        return source["p1"][i], support[d]["bag"]
    return source["p3"][q], None


def trajectory(blood: dict, case: str, lam: int, factor: float, gain: float, arrivals: dict) -> dict:
    anchors = vt.tone_anchors(case, vt.level_of(lam), factor)
    rebuilt = vt.rebuild(blood, anchors, gain, AFTERLOAD)
    series = vt.debt_and_lactate(blood, rebuilt, case, lam, factor, arrivals)
    rows = rebuilt["rows"]
    rr = [rr_from_lactate(anchors, series["lactate"][m], blood["pulse"][m]) for m in range(len(rows))]
    return {"rr": rr, "lactate": list(series["lactate"][:len(rows)]), "D": list(series["D"][:len(rows)]),
            "s": [row["s"] for row in rows], "metabolic": [dv._metabolic_drive(x, DEFAULT_PROFILE) for x in series["lactate"][:len(rows)]],
            "ventilatory": _ventilatory_part(anchors), "controlled_at": blood["controlled_at"], "stop": rebuilt["stop"]}


def reconstruct(region: dict, arrivals: dict, check=None) -> dict:
    """Every survivor's unique (scenario, blood set, lactate-side point) at its demand and tone gain."""
    out = {}
    for (gain, factor), survivors in sorted(region["survivors"].items()):
        for name in ("P1", "P2", "P3", "P4"):
            for case, position in ((C57, 1), (C72, 2)):
                seen = {}
                for survivor in survivors:
                    lam = survivor[position]
                    key = (_blood_key(name, case, survivor), lam)
                    if key not in seen:
                        seen[key] = (survivor, trajectory(region["bloods"][key[0]], case, lam, factor, gain, arrivals))
                out[(gain, factor, name, case)] = seen
    return out


def validate(region: dict, store: dict) -> dict:
    """One full core run per (tone gain, demand, scenario, case): RR, D and lactate equal to the reconstruction."""
    compared, equal = 0, True
    for (gain, factor, name, case), seen in sorted(store.items(), key=lambda kv: str(kv[0])):
        if not seen:
            continue
        (blood_key, lam), (survivor, traj) = sorted(seen.items(), key=lambda kv: str(kv[0]))[0]
        entry, bag = _entry(name, survivor, region["source"], region["support"])
        run_ = pt.full_run(entry, case, pt.SCENARIOS[name], factor, LAMBDAS[lam], bag, "midpoint",
                           {"deficit_to_tone_gain": gain, "afterload_sensitivity": AFTERLOAD})
        rows = run_["rows"]
        compared += 1
        equal = equal and len(rows) == len(traj["rr"]) and all(
            row["rr"] == traj["rr"][m] and row["D"] == traj["D"][m] and row["lactate"] == traj["lactate"][m]
            for m, row in enumerate(rows))
    return {"compared": compared, "equal": equal}


def _spread(values) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    values = sorted(values)
    n = len(values)
    median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
    return {"n": n, "low": values[0], "median": median, "high": values[-1]}


def summarize(store: dict) -> dict:
    out = {}
    for (gain, factor, name, case), seen in store.items():
        trajs = [t for _, t in seen.values()]
        table = {}
        for minute in MINUTES_REPORTED:
            def at(field):
                return [t[field][minute] for t in trajs if minute < len(t[field])]
            table[str(minute)] = {"rr": _spread(at("rr")), "lactate": _spread(at("lactate")), "D": _spread(at("D")),
                                  "deficit": _spread(at("s")), "metabolic_drive": _spread(at("metabolic")),
                                  "metabolic_part": _spread([t["rr"][minute] - t["ventilatory"] for t in trajs
                                                             if minute < len(t["rr"])])}
        out[f"x{factor:g} g{gain:g} {name} {case}"] = {"trajectories": len(trajs), "minutes": table,
                                                       "W": 0.0, "pH": "NOT_MODELED", "pCO2": "NOT_MODELED",
                                                       "hypoxaemic_drive": "NOT_MODELED", "support": "room air (FiO2 0.21)"}
    return out


# 6. Directional expectations (P2K-1-10), dependencies (P2K-1-14), identifiability (P2K-1-13) ----------------------------

DIRECTIONS = {
    1: "greater ventilatory need must not reduce RR if mechanics permit",
    2: "resolving metabolic / acidaemic drive permits RR recovery",
    3: "lactate decline alone must not force RR down while ventilatory need remains",
    4: "high RR must not imply adequate W when mechanics or fatigue limit ventilation",
    5: "mechanical-ventilation semantics override the spontaneous frequency where appropriate",
    6: "oxygen therapy may improve oxygenation without correcting ventilation",
    7: "CO2 clearance follows effective ventilation rather than RR alone",
    8: "no instantaneous RR normalization merely from haemostasis",
}
DIRECTION_STATUS = ("PASSES", "PASSES_FOR_THE_PROXY_ONLY", "VIOLATED_BY_THE_PROXY", NOT_REPRESENTABLE)
DIRECTION_RULE = (
    "Structural, no RR range: 1 reads RR's monotonicity in lactate and W > 0 (the only 'need' the core has); 2 the RR at "
    "the clearance baseline against the ventilatory part; 3 the clearance probe (same D, different tau_lactate); 4, 5, 7 "
    "need an effective-ventilation output, mechanical ventilation and CO2, absent; 6 the oxygen probe; 8 the R4 "
    "trajectories: no RR term reads haemostasis, and the RR change across the haemostasis minute is compared with the "
    "largest one-minute RR change of the same trajectory.")


def directions(probes_: dict, store: dict) -> dict:
    anchors, profile = PROBE_ANCHORS, _profile()
    grid = [i * 0.25 for i in range(0, 61)]
    monotone = all(rr_from_lactate(anchors, x, profile=profile) <= rr_from_lactate(anchors, y, profile=profile)
                   for x, y in zip(grid, grid[1:]))
    w_monotone = all(rr_from_lactate(anchors, 1.0, w=x, profile=profile) <= rr_from_lactate(anchors, 1.0, w=y,
                                                                                             profile=profile)
                     for x, y in zip(grid, grid[1:]))
    recovered = rr_from_lactate(anchors, anchors.lactate, profile=profile) >= _ventilatory_part(anchors, profile)
    worst = {"haemostasis_step": None, "largest_step": 0.0}
    for (gain, factor, name, case), seen in store.items():
        if name != "P4":
            continue
        for _, t in seen.values():
            h = t["controlled_at"]
            steps = [abs(b - a) for a, b in zip(t["rr"], t["rr"][1:])]
            if steps:
                worst["largest_step"] = max(worst["largest_step"], max(steps))
            if h is not None and h + 1 < len(t["rr"]):
                value = abs(t["rr"][h + 1] - t["rr"][h])
                worst["haemostasis_step"] = value if worst["haemostasis_step"] is None else max(
                    worst["haemostasis_step"], value)
    no_step = worst["haemostasis_step"] is not None and worst["haemostasis_step"] <= worst["largest_step"]
    return {
        1: {"status": "PASSES_FOR_THE_PROXY_ONLY" if monotone and w_monotone else "VIOLATED_BY_THE_PROXY",
            "lactate_monotone": monotone, "w_monotone": w_monotone,
            "note": "true ventilatory need (CO2, acid load) is not represented"},
        2: {"status": "PASSES" if recovered else "VIOLATED_BY_THE_PROXY", "recovers_to_ventilatory_part": recovered},
        3: {"status": "VIOLATED_BY_THE_PROXY" if probes_["clearance"]["rr_follows_clearance"] else "PASSES",
            "clearance": {k: v for k, v in probes_["clearance"].items() if k != "rr_follows_clearance"},
            "note": "with the same D, faster lactate clearance lowers RR: RR tracks the concentration, and the core cannot "
                    "tell a resolving acid load from a persisting one; KD-S1's guard only bounds the fall to the "
                    "arrival metabolic share"},
        4: {"status": NOT_REPRESENTABLE, "note": "no effective-ventilation output apart from RR"},
        5: {"status": NOT_REPRESENTABLE, "note": "no mechanical ventilation in the core; no current scenario ventilates"},
        6: {"status": "PASSES" if probes_["oxygen"]["oxygenation_only"] else "VIOLATED_BY_THE_PROXY",
            "note": "FiO2 moves SpO2 only"},
        7: {"status": NOT_REPRESENTABLE, "note": "no CO2"},
        8: {"status": "PASSES" if no_step else "VIOLATED_BY_THE_PROXY", **worst,
            "note": "RR follows lactate, which lags D by first-order clearance; no RR term reads haemostasis"},
    }


def dependencies(store: dict) -> dict:
    by_gain, by_demand = [], []
    index = {}
    for (gain, factor, name, case), seen in store.items():
        for (blood_key, lam), (_, t) in seen.items():
            index[(gain, factor, name, case, str(blood_key), lam)] = t["rr"]
    for (gain, factor, name, case, key, lam), rr in index.items():
        others = [index.get((g, factor, name, case, key, lam)) for g in TONE_GAINS]
        if gain == TONE_GAINS[0] and all(o is not None for o in others):
            n = min(len(o) for o in others)
            by_gain.append(max(max(o[m] for o in others) - min(o[m] for o in others) for m in range(n)))
        if factor == DEMANDS[0] and (gain, DEMANDS[1], name, case, key, lam) in index:
            other = index[(gain, DEMANDS[1], name, case, key, lam)]
            n = min(len(rr), len(other))
            by_demand.append(max(abs(other[m] - rr[m]) for m in range(n)))
    reads = rr_reads()
    return {
        "demand": {"path": "demand -> effective deficit -> D -> lactate -> RR", "max_rr_difference": _spread(by_demand)},
        "tone_gain": {"path": "g -> T -> afterload / output -> delivery -> deficit -> D -> lactate -> RR",
                      "max_rr_difference": _spread(by_gain)},
        "map_set": {"path": "NONE: the baroreflex moves only the sympathetic drive, which RR, lactate and D never read",
                    "evidence": "P2J-4: every non-HR row, rr included, equal with the baroreflex on and off (654 units)"},
        "baroreflex_gain": {"path": "NONE (as MAP_set)", "evidence": "P2J-4 rows_equal"},
        "hr_latent": {"path": "NONE: HR reaches no output, D, lactate or RR (P2I-2AG, P2J-1)",
                      "evidence": "respiratory_rate reads " + ", ".join(reads["respiratory_rate"]["attributes"])},
    }


IDENTIFIABILITY_CLASSES = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE",
                           "NOT_APPLICABLE")
IDENTIFIABILITY_RULE = (
    "Frozen. A quantity on a path classified BIOMARKER_PROXY, SEMANTIC_LEAK or NOT_CURRENTLY_MODELED is NOT_APPLICABLE "
    "(no candidate surface stands on it). The baseline is PARTIALLY_CONSTRAINED: the authored arrival RR fixes the sum "
    "of the ventilatory part and the arrival metabolic share, not the split. A bound is NON_IDENTIFIABLE when no "
    "reconstructed trajectory reaches it, POORLY_IDENTIFIED when some do.")


def identifiability(store: dict) -> dict:
    profile = DEFAULT_PROFILE
    peak_rr = max(max(t["rr"]) for seen in store.values() for _, t in seen.values())
    peak_metabolic = max(max(t["metabolic"]) for seen in store.values() for _, t in seen.values())
    floor_binds = {case: gi_reference.canonical_anchors(case).respiratory_rate - profile.rr_ventilatory_floor
                   < dv._metabolic_drive(gi_reference.canonical_anchors(case).lactate, profile) for case in CASES}
    return {
        "baseline_rr": {"class": "PARTIALLY_CONSTRAINED", "why": "authored arrival RR 26 / 24 fixes the sum only"},
        "metabolic_gain": {"class": "NOT_APPLICABLE", "why": BIOMARKER_PROXY_REQUIRES_REFACTOR},
        "hypoxaemic_gain": {"class": "NOT_APPLICABLE", "why": "not modeled"},
        "w_drive_coupling": {"class": "NOT_APPLICABLE", "why": "MIXED_DRIVE_AND_VENTILATION_CONSTRUCT, no writer"},
        "rr_max": {"class": "NON_IDENTIFIABLE" if peak_rr < profile.rr_max else "POORLY_IDENTIFIED", "peak_rr": peak_rr},
        "rr_metabolic_max": {"class": "NOT_APPLICABLE", "why": "on the lactate proxy", "peak_metabolic_drive": peak_metabolic},
        "rr_ventilatory_floor": {"class": "NOT_APPLICABLE", "why": "splits the arrival RR by the lactate proxy",
                                 "binds": floor_binds},
        "d_lactate_pathway": {"class": "NOT_APPLICABLE", "why": BIOMARKER_PROXY_REQUIRES_REFACTOR},
        "rule": IDENTIFIABILITY_RULE,
    }


# 7. Correction, candidate surface, readiness ---------------------------------------------------------------------------------

CORRECTION = {"made": False,
              "why": "no defect is clear to fix without a new state: removing the lactate term would leave the core "
                     "without any metabolic compensation (KD-S1, patient-like compensation) and replacing it needs an "
                     "acid-base state the faculty has not authorized; W has no GI writer, so its mixed reading moves "
                     "nothing now; there is no mechanical ventilation to override. Nothing in the core changes."}
CANDIDATE_SURFACE = {"built": False, "why": "the structure is not coherent (readiness blockers): no numeric RR surface"}
READY = "RR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"
NOT_READY = "RR_STRUCTURE_NOT_READY"
BLOCKERS = ("ACID_BASE_STATE_REQUIRED", "LACTATE_BIOMARKER_PROXY", "W_MIXED_DRIVE_AND_VENTILATION",
            "VENTILATION_FREQUENCY_CONFLATED", "CO2_NOT_REPRESENTABLE", "MECHANICAL_VENTILATION_NOT_MODELED")
VERDICT_RULE = (
    "READY when: the RR contributors are explicit; W is a COHERENT_EFFECTIVE_VENTILATION_STATE; no lactate path is a "
    "BIOMARKER_PROXY; metabolic acidosis -> drive is representable without lactate; ventilation and frequency are "
    "separate; respiratory-support overrides are coherent; the directional probes pass (none violated or not "
    "representable); the candidate surface is explicit; nothing is approved. Otherwise NOT_READY with the first blocker "
    "in BLOCKERS order.")
MISSING_STRUCTURE = (
    "Smallest missing physiology, in order: (1) a metabolic acid-load state (a base-deficit-like quantity with an "
    "explicit source tied to the delivery shortfall and an explicit clearance), from which acidaemia is read, so that "
    "metabolic acidosis drives ventilation causally and lactate stays a biomarker beside it; (2) a CO2 representation: "
    "PaCO2 from CO2 production (demand) against effective alveolar ventilation W, algebraic unless kinetics are needed; "
    "(3) W split into ventilatory drive (acidaemia, PaCO2, hypoxaemia, depressants) and effective ventilation (drive "
    "limited by mechanics / fatigue), with RR the observable of the drive; (4) respiratory-support semantics separating "
    "oxygenation (FiO2) from ventilatory support (NIV, controlled ventilation) that sets W or the rate. (1) and (2) are "
    "the first step; each needs faculty authorization before any number.")
DECISIONS = (
    "authorize the metabolic acid-load state (1): its meaning, source and clearance, and lactate's relation to it",
    "decide PaCO2 (2): algebraic from production and W, or a state with its own time constant",
    "decide W's semantics (3): effective ventilation as an output, drive as its own signal",
    "decide whether the lactate term stays as a flagged interim proxy until (1) exists, or is removed (RR would lose all "
    "metabolic compensation)",
    "decide the respiratory-support scope (4) and whether mechanical ventilation enters the GI family",
)
POLICY = ("Shadow only. The core is unchanged; P2J-3's region recomputed through P2J-4's machinery; legacy RR never read "
          "(LegacyLock), the P2F region never consumed (P2FGuard); no RR range, candidate or approval; the HR / baroreflex "
          "uncertainty is carried, not multiplied, since it does not reach RR.")


def verdict(checks: dict) -> dict:
    blockers = [name for name in BLOCKERS if not checks[name]]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}", "blockers": blockers,
            "checks": checks, "approved": [], "rule": VERDICT_RULE}


# 8. Closure of P2J-4 and the core's non-regression ---------------------------------------------------------------------------

#: The two tuple-only files at P2J-4: P2K-1 adds its modules to their tuples, nothing else.
TUPLE_AT_P2J4 = {"clinical_core/lactate_slice.py": "0a1b0e05b7b9f7f3f4288a914c9b2b5ce7e1c1a1d3c208171b1f86c0ac0c7c58",
                 "clinical_core/decision_pack.py": "bb0ed190f33bf31ecaef47498dd5a7fec8b7325669769afb20b9029f18ac5f22"}
#: derived.py, integration.py, state.py and shadow.py as P2J-4 left them: P2K-1 changes none of them.
CORE_AT_P2J4 = {"clinical_core/derived.py": "87f773f54d6bc4d125ef7817eb79383e7b77d792d9879a9a90d8caa82efe275c",
                "clinical_core/integration.py": "cb54d2eec3754eecdd7267dba58b0389203b233b16a86455f5280d1eafa520f0",
                "clinical_core/state.py": "6029be144a0db6639cf83e728b01191285a7cb09a30e1253884dd8fe47f41415",
                "clinical_core/shadow.py": "66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35"}


def p2j4_sources(sources: dict) -> dict:
    """A P2J-4 dependency map: the two tuple-only files at their P2J-4 hashes while only their tuples changed."""
    out = dict(sources)
    for relative, sha in TUPLE_AT_P2J4.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def core_unchanged() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in CORE_AT_P2J4.items()}


def w_references() -> list:
    """Every clinical_core line that names the W channel (Channel.W, a 'W' target, state.W), report modules aside."""
    out = []
    pattern = re.compile(r'Channel\.W\b|state\.W\b|"W"|\bW=')
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative.endswith("_report.py") or relative == "clinical_core/rr_audit.py":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                out.append(relative)
    return sorted(set(out))


# 9. Design, freeze, run ----------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "carried": CARRIED, "equation": EQUATION,
            "rr_parameters": list(RR_PARAMETERS), "classes": list(CLASSES), "contributors": list(CONTRIBUTORS),
            "d_path": [list(p) for p in D_PATH], "w_audit": W_AUDIT, "acid_base": ACID_BASE,
            "acidosis_to_drive": ACIDOSIS_TO_DRIVE, "probe_rule": PROBE_RULE, "support": SUPPORT,
            "respiratory_items": list(RESPIRATORY_ITEMS), "r_scenarios": R_SCENARIOS,
            "minutes_reported": list(MINUTES_REPORTED), "reconstruction_rule": RECONSTRUCTION_RULE,
            "directions": DIRECTIONS, "direction_rule": DIRECTION_RULE, "identifiability_rule": IDENTIFIABILITY_RULE,
            "correction": CORRECTION, "candidate_surface": CANDIDATE_SURFACE, "blockers": list(BLOCKERS),
            "verdict_rule": VERDICT_RULE, "missing_structure": MISSING_STRUCTURE, "decisions": list(DECISIONS),
            "policy": POLICY, "tuple_at_p2j4": TUPLE_AT_P2J4, "core_at_p2j4": CORE_AT_P2J4}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2j4": hashlib.sha256(P2J4_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def p2j4_record() -> dict:
    record = json.loads(P2J4_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2J4_DIGEST or record["verdict"]["verdict"] != br.READY:
        raise AssertionError("the P2J-4 record is not the committed one")
    return record


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2j4_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2J4_DIGEST, "design": design()}
        say("audit and probes")
        probes_ = probes()
        say("certified physiology (P2J-3 region)")
        region = br.pressure_tone_region(map_, say)
        arrivals = lr.arrival_table()
        say("RR reconstruction")
        store = reconstruct(region, arrivals)
        validation = validate(region, store)
        directions_ = directions(probes_, store)
        dependencies_ = dependencies(store)
        checks = {"ACID_BASE_STATE_REQUIRED": ACIDOSIS_TO_DRIVE["representable_without_lactate"],
                  "LACTATE_BIOMARKER_PROXY": not any(c["class"] == "BIOMARKER_PROXY" and "lactate" in c["name"]
                                                     for c in CONTRIBUTORS),
                  "W_MIXED_DRIVE_AND_VENTILATION": W_AUDIT["class"] == W_CLASSES[0],
                  "VENTILATION_FREQUENCY_CONFLATED": not directions_[4]["status"] == NOT_REPRESENTABLE,
                  "CO2_NOT_REPRESENTABLE": not directions_[7]["status"] == NOT_REPRESENTABLE,
                  "MECHANICAL_VENTILATION_NOT_MODELED": not directions_[5]["status"] == NOT_REPRESENTABLE}
        out.update({
            "reads": rr_reads(), "w_references": w_references(), "probes": probes_, "authored": authored(),
            "pressure_tone_unchanged": region["unchanged"],
            "reconstruction": summarize(store), "validation": validation, "directions": directions_,
            "dependencies": dependencies_, "identifiability": identifiability(store),
            "core_unchanged": core_unchanged(), "p2j4_verdict": record["verdict"]["verdict"],
            "efficiency": {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs": region["counterfactual_runs"],
                           "rr_trajectories_rebuilt": sum(len(seen) for seen in store.values()),
                           "core_validation_runs": validation["compared"], "candidate_runs": 0,
                           "cartesian_sweep": False, "legacy_read": False}})
        out["verdict"] = verdict(checks)
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
        path = args.out / "rr_audit.json"
        path.write_text(json.dumps(run(lambda s: print(s, flush=True)), sort_keys=True, separators=(",", ":"),
                                   default=str), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
