"""P2S-2: common respiratory mechanics and the closure of W's meaning (shadow only).

    python -m clinical_core.respiratory_mechanics [--digest] [--out <json>]

A common structural package, not an asthma migration and not a calibration. P2S-1 showed that neither earlier reading of
W is enough: P2K-2 tied the effective ventilation to RR (opioid hypoventilation, but no high RR with high PaCO2 in
pulmonary oedema or severe asthma, and the arrival PaCO2 anchor absorbed the arrival mechanics), P2K-3 freed it from RR
(low mechanics, but no low-RR hypoventilation). The faculty (W_SEMANTICS_COMMON_GAP) fixed one meaning: W is the
effective alveolar ventilation relative to the current metabolic ventilatory need, derived after the RR and never read
back into it:

    drive + central availability -> expressed RR                                      (P2P-2, unchanged)
    frequency factor = expressed RR / intrinsic RR
    capacity = frequency factor x mechanics efficiency
    W = capacity / metabolic demand ratio
    PaCO2 = PaCO2_reference / W          (40 mmHg, COMMON_REFERENCE_PROVISIONAL, never the authored arrival PaCO2)

The core gained one common state-like quantity, the respiratory mechanics efficiency (``aux.mechanics_efficiency``: the
effective alveolar ventilation one breath moves relative to the eupnoeic reference, above 0, no upper bound), its
latent arrival value (``Anchors.arrival_mechanics_efficiency``) and its family writer target (``provenance.
MechanicsChange`` in ``Contribution.mechanics``), all behind one profile switch that is off by default
(``respiratory_mechanics``). No family writer is implemented, no clinical value is chosen; 1 is only the structural
reference. This module freezes, before its evaluation, the path audit, the semantics, the synthetic probe values, probes
M1-M12, the contrasts, the arrival-efficiency diagnostic and its ordering rule, the readiness rule and the proof that the
core is the P2Q-2 core plus the declared insertions.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
import types
from dataclasses import astuple, dataclass, fields, replace
from pathlib import Path

from . import acs_migration as an
from . import acs_reference as ar
from . import acid_base as ab
from . import bands
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import edema_migration as pe
from . import edema_reference as er
from . import embolism_migration as em
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import respiratory_drive as rd
from .integration import Contribution, Contributor, step
from .provenance import MechanicsChange, ProvenanceError, SourceKind
from .state import AUXILIARY_FIELDS, Channel, CoreInvariantError, RhythmState

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2S-2"
DECIDED = "2026-11-04"
OWN = ("clinical_core/respiratory_mechanics.py",)
REPORT = "clinical_core/respiratory_mechanics_report.py"
RECORD = ROOT / "docs" / "revision" / "P2S2_respiratory_mechanics.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2S2_MECANICA_RESPIRATORIA_COMUN.md"
#: The tuples P2S-2 extended (its analysis and report are downstream of every numerical artifact).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py", "clinical_core/state.py", "clinical_core/integration.py",
              "clinical_core/provenance.py")
#: The candidate input P2S-2 gave the anchors (outside the case-parameter / migration registry, as P2K-2's and P2O-3's).
CANDIDATE_INPUTS = ("arrival_mechanics_efficiency",)


# The faculty's decisions (fixed) ---------------------------------------------------------------------------------------------

DECISIONS = {
    "W_SEMANTICS_COMMON_GAP": "P2K-2 (W tied to RR) loses high RR with high PaCO2; P2K-3 (W free of RR) loses low-RR "
                              "hypoventilation: neither pure reading is enough",
    "UNIQUE_W_SEMANTICS": "W = effective alveolar ventilation relative to the current metabolic ventilatory need, "
                          "derived; never drive, frequency, central availability or mechanics severity. Drive + "
                          "availability -> expressed RR; RR + mechanics efficiency + need -> W; W -> PaCO2; no W -> RR",
    "MINIMAL_MECHANICS_COORDINATE": "one common state-like quantity, mechanics_efficiency: the effectiveness of each "
                                    "expressed breath in producing alveolar ventilation relative to a eupnoeic "
                                    "reference; family-writable; distinct from drive, central depression, G and L; not a "
                                    "canonical channel",
    "DOMAIN": "mechanics_efficiency > 0 only; 1 is STRUCTURAL_REFERENCE / DEFAULT, never a universal normal value; no "
              "upper bound (a stricter one would need faculty review)",
    "COMBINED_FORM": "frequency factor = expressed RR / intrinsic RR; capacity = frequency factor x mechanics "
                     "efficiency; W = capacity / metabolic demand ratio; PaCO2 = PaCO2_reference / W",
    "PACO2_REFERENCE": "40 mmHg, COMMON_REFERENCE_PROVISIONAL, not FACULTY_APPROVED; the resting PaCO2 is never anchored "
                       "to the authored arrival PaCO2",
    "ARRIVAL_MECHANICS_LATENT": "a CASE / FAMILY LATENT ARRIVAL MAPPING constrained by the authored RR, the authored "
                                "PaCO2, the intrinsic-RR uncertainty and the demand; never from the disease label; "
                                "regions reported, no value selected",
    "STOP_BEFORE": "asthma migration; mechanics calibration; hypoventilation -> oxygenation; fatigue state; NIV; the "
                   "alveolar gas equation; HR / distress sympathetic implementation; opioid migration",
}


# P2S-2-1: the respiratory paths before this package, and where each stands now -----------------------------------------------

ACTIVE_CURRENT, SHADOW_CANDIDATE, LEGACY_ONLY, RETIRED = "ACTIVE_CURRENT", "SHADOW_CANDIDATE", "LEGACY_ONLY", "RETIRED"
RETIRED_FROM_CANDIDATE = "RETIRED_FROM_COMMON_MECHANICS_CANDIDATE"
PATHS = {
    "respiratory_drive": (ACTIVE_CURRENT, "P2P-2 composition: excitatory drive = acid drive (acid_to_drive_gain x "
                                          "burden) + hypoxaemic drive (UNSET by default); unchanged; reads no mechanics, "
                                          "W or PaCO2"),
    "expressed_rr": (ACTIVE_CURRENT, "availability x rate_from_drive(excitatory, intrinsic) whenever the acid-base "
                                     "physiology is on; P2S-2 begins after it"),
    "intrinsic_rr": (ACTIVE_CURRENT, "Anchors.intrinsic_respiratory_rate (None: the arrival RR), a P2K-2 candidate input "
                                     "(12 / 16 / 20 carried); the reference frequency of W, never a mechanics input"),
    "central_drive_availability": (ACTIVE_CURRENT, "P2P-2 STRUCTURAL_INPUT, 1 by default; family values UNSET; it moves "
                                                   "the RR only"),
    "ventilation_efficiency": (ACTIVE_CURRENT, "P2K-2 profile constant, STRUCTURAL_REFERENCE 1 in every migration; in the "
                                               "P2S-2 candidate " + RETIRED + ": it must be 1, mechanics live in the "
                                               "state"),
    "W_channel_P2K1_reader": (ACTIVE_CURRENT, "derived.respiratory_rate reads state.W (above 0 multiplies the "
                                              "ventilatory RR, below 0 depresses it) only with the acid-base physiology "
                                              "off (DEFAULT_PROFILE, the golden); with it on that RR is replaced by "
                                              "P2K-2's. In the P2S-2 candidate " + RETIRED_FROM_CANDIDATE + ": no source "
                                              "may write the W channel (the integration refuses it) and nothing reads "
                                              "it; historical behaviour kept"),
    "W_P2K2": (ACTIVE_CURRENT, "Respiration.ventilation = efficiency x RR / intrinsic / demand ratio with the profile "
                               "constant; the P2K-2 path whenever the mechanics candidate is off"),
    "PaCO2_P2K2": (ACTIVE_CURRENT, "resting PaCO2 = authored arrival PaCO2 x arrival W at the reference (the arrival "
                                   "anchor); the P2K-2 path whenever the mechanics candidate is off; the candidate never "
                                   "reads it"),
    "metabolic_demand": (ACTIVE_CURRENT, "aux.oxygen_demand / anchors.metabolic_demand_baseline (BASELINE_RELATIVE), "
                                         "shared by P2K-2, P2K-3 and the candidate; CO2 production read proportional to "
                                         "it (a constant respiratory quotient, implicit)"),
    "acid_drive": (ACTIVE_CURRENT, "P2K-2: the burden from the authored HCO3 and the effective oxygen deficit; "
                                   "unchanged"),
    "P2K2_path": (ACTIVE_CURRENT, "every migration profile (acid-base on, mechanics off); unchanged"),
    "P2K3_candidate": (SHADOW_CANDIDATE, "clinical_core/ventilation.py (W from the acid recruitment, no RR term), off, "
                                         "unchanged for its closed records; superseded as W semantics: " + RETIRED +
                                         " from the common candidate"),
    "P2P2_path": (ACTIVE_CURRENT, "the drive composition; unchanged"),
    "legacy_engine": (LEGACY_ONLY, "family_engine.py's respiratory model, the runtime source of truth; not read"),
    "P2S2_candidate": (SHADOW_CANDIDATE, "profile.respiratory_mechanics, off by default: W from RR, the state's mechanics "
                                         "efficiency and the demand; PaCO2 from W and the common reference"),
}


def _functions(text: str) -> dict:
    return {n.name: n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)}


def _names(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(node)
                                                                       if isinstance(n, ast.Attribute)}


def _reads_attribute(node, attr: str) -> bool:
    return any(isinstance(n, ast.Attribute) and n.attr == attr and isinstance(n.ctx, ast.Load) for n in ast.walk(node))


def _candidate_branch(funcs: dict):
    """The If of ``respiration`` whose test calls respiratory_mechanics_active: (body, orelse)."""
    for node in ast.walk(funcs["respiration"]):
        if isinstance(node, ast.If) and "respiratory_mechanics_active" in _names(node.test):
            return node
    raise AssertionError("respiration has no respiratory mechanics branch")


COMPOSITION = ("hypoxaemic_drive_signal", "hypoxaemic_drive", "expressed_respiratory_rate", "_composition",
               "respiratory_drive_composition", "arrival_drive_composition", "respiratory_drive", "rate_from_drive")
OXYGENATION = ("oxygenation", "_perfusion", "relative_delivery", "effective_delivery", "oxygen_response_retained",
               "lung_water_gas_credit")
HEART_RATE = ("sympathetic_target", "sympathetic_increment", "sympathetic_drive", "sympathetic_after_minute",
              "arrival_sympathetic_drive", "heart_rate_decomposition")


def audit() -> dict:
    """The live paths, read from the code: who reads the W channel, who reads the mechanics efficiency, what the drive,
    the oxygenation and the HR read, and that the integration composes mechanics only from contributions."""
    text = (CORE_DIR / "derived.py").read_text(encoding="utf-8")
    funcs = _functions(text)
    w_readers = sorted(n for n, f in funcs.items() if _reads_attribute(f, "W"))
    mechanics_readers = sorted(n for n, f in funcs.items() if "mechanics_efficiency" in _names(f))
    arrival_readers = sorted(n for n, f in funcs.items() if "arrival_mechanics_efficiency" in _names(f))
    branch = _candidate_branch(funcs)
    body = set().union(*(_names(s) for s in branch.body))
    orelse = set().union(*(_names(s) for s in branch.orelse))
    integration = (CORE_DIR / "integration.py").read_text(encoding="utf-8")
    step_node = _functions(integration)["step"]
    composed = [ast.unparse(n) for n in ast.walk(step_node) if isinstance(n, ast.keyword)
                and n.arg == "mechanics_efficiency"]
    out = {
        "w_channel_readers": w_readers,
        "integration_refuses_w_writes": [ast.unparse(n.test) for n in ast.walk(step_node) if isinstance(n, ast.If)
                                         and "respiratory_mechanics_active" in _names(n.test)
                                         and "W" in _names(n.test)],
        "mechanics_readers": mechanics_readers,
        "arrival_mechanics_readers": arrival_readers,
        "candidate_branch_reads": sorted(body & {"mechanics_efficiency", "paco2_reference_mmhg", "arrival_paco2",
                                                 "arrival_alveolar_ventilation", "ventilation_efficiency"}),
        "p2k2_branch_reads": sorted(orelse & {"mechanics_efficiency", "paco2_reference_mmhg", "arrival_paco2",
                                              "arrival_alveolar_ventilation", "ventilation_efficiency"}),
        "composition_reads_mechanics_or_w": {n: bool({"mechanics_efficiency", "ventilation", "W", "paco2"}
                                                     & _names(funcs[n])) for n in COMPOSITION},
        "oxygenation_reads_ventilation": {n: bool({"mechanics_efficiency", "ventilation", "W", "paco2", "respiration"}
                                                  & _names(funcs[n])) for n in OXYGENATION},
        "heart_rate_reads_respiration": {n: bool({"mechanics_efficiency", "ventilation", "W", "paco2", "respiration",
                                                  "respiratory_drive_composition", "central_drive_availability"}
                                                 & _names(funcs[n])) for n in HEART_RATE},
        "integration_composition": composed,
        "integration_reads_respiration": any(n in integration for n in ("respiration(", "drive_composition",
                                                                        "alveolar_ventilation")),
    }
    out["pass"] = (w_readers == ["respiratory_rate"] and len(out["integration_refuses_w_writes"]) == 1
                   and mechanics_readers == ["respiration"] and arrival_readers == ["arrival_state"]
                   and out["candidate_branch_reads"] == ["mechanics_efficiency", "paco2_reference_mmhg"]
                   and "mechanics_efficiency" in out["p2k2_branch_reads"]
                   and {"arrival_paco2", "arrival_alveolar_ventilation", "ventilation_efficiency"} <= set(
                       out["p2k2_branch_reads"])
                   and not any(out["composition_reads_mechanics_or_w"].values())
                   and not any(out["oxygenation_reads_ventilation"].values())
                   and not any(out["heart_rate_reads_respiration"].values())
                   and composed == ["mechanics_efficiency=state.aux.mechanics_efficiency * math.prod((item.factor "
                                    "for item in mechanics))"]
                   and not out["integration_reads_respiration"])
    return out


# The semantics (P2S-2-5, P2S-2-6) and the dimensions -----------------------------------------------------------------------------

SEMANTICS = {
    "W": "effective alveolar ventilation relative to the current metabolic ventilatory need (dimensionless; 1: the "
         "patient's need met at the eupnoeic reference); derived, never a state the drive reads",
    "frequency_factor": "expressed RR / intrinsic RR (bpm / bpm): the breaths taken relative to the reference rate",
    "mechanics_efficiency": "effective alveolar ventilation per breath relative to the eupnoeic reference (VT - VD over "
                            "its reference, implicitly): above 0, 1 the structural reference; the state's value, the "
                            "case's latent arrival value times every family change since",
    "capacity": "frequency factor x mechanics efficiency: the alveolar ventilation relative to its reference",
    "demand_ratio": "aux.oxygen_demand / metabolic_demand_baseline (BASELINE_RELATIVE): CO2 production relative to the "
                    "patient's baseline, read proportional to the oxygen demand (constant respiratory quotient, implicit)",
    "PaCO2": "PaCO2_reference / W: the alveolar ventilation equation relative to its reference (PaCO2 = k VCO2 / VA, so "
             "PaCO2 / PaCO2_ref = (VCO2 / VCO2_ref) / (VA / VA_ref)); 40 mmHg at W = 1",
    "pH": "carbonic_ph(HCO3, PaCO2), unchanged",
}
DIMENSIONS = {"frequency_factor": "1 (bpm / bpm)", "mechanics_efficiency": "1 (per-breath alveolar ventilation over its "
                                                                           "reference)",
              "capacity": "1 (VA / VA_ref)", "demand_ratio": "1 (VCO2 / VCO2_baseline, through VO2)", "W": "1",
              "PaCO2": "mmHg (the reference carries the unit)",
              "equivalence": "the core computes W = efficiency x RR / intrinsic / demand (alveolar_ventilation, the one "
                             "W formula, P2K-2's), algebraically the faculty's form; no dimensionally cleaner equivalent "
                             "exists"}
INTERFACE = {
    "target": "aux.mechanics_efficiency (AUXILIARY_FIELDS), arrival value Anchors.arrival_mechanics_efficiency",
    "writer": "Contribution.mechanics: a tuple of provenance.MechanicsChange(factor > 0, source, minute, description); "
              "any non-reserved source kind (a family module, an order, a scripted probe)",
    "composition": "the core multiplies the efficiency the minute starts with by every factor of the minute "
                   "(RESPIRATORY_MECHANICS, a core composition, no kinetics): it stays where its writers leave it",
    "provenance": "each change in MinuteRecord.mechanics with its source; the aux change under RESPIRATORY_MECHANICS; the "
                  "conservation check holds the efficiency to exactly its recorded factors",
    "off": "with the candidate off a change, an arrival value other than 1 and a state value other than 1 are refused "
           "(nothing would read them)",
    "families": "no family writer exists: no asthma obstruction, oedema mechanics or opioid writer (P2S-2-4)",
}


# The probe world (fixed before the evaluation) ---------------------------------------------------------------------------------

#: Synthetic mechanics efficiencies for the structural probes: a generic grid on the domain (quarters below the
#: reference), never fitted to a case or to an implied arrival region.
SYNTHETIC_EFFICIENCIES = (1.0, 0.75, 0.5, 0.25)
LOW_EFFICIENCY = SYNTHETIC_EFFICIENCIES[-1]    # the grid's lowest point: "markedly reduced"
MILD_EFFICIENCY = SYNTHETIC_EFFICIENCIES[1]    # the grid's highest point below the reference: "mildly reduced"
AVAILABILITIES = (1.0, 0.75, 0.5, 0.25, 0.1, 0.0)
DEPRESSED = 0.5                        # one synthetic central depression for M4
BICARBONATES = (24.0, 21.0, 18.0, 15.0)  # acid burdens 0, 3, 6, 9 mEq/L
STRONG_DRIVE = rd.STRONG_DRIVE         # P2P-2's large excitatory term, injected (option A): SYNTHETIC_EXCITATORY_INPUT
HYPOXAEMIC_SPO2S = rd.ABSOLUTE_ARRIVALS  # 97 / 91 / 85
HYPOXAEMIC_GAIN = rd.SYNTHETIC_GAINS[1]
MECHANICS_FACTOR = 0.98                # one synthetic writer: 2 % per minute
COURSE_MINUTES = 30
G_PER_MIN = 0.01                       # a scripted G drift (SYNTHETIC_ONLY)
L_PER_MIN = 0.02                       # a scripted L drift (SYNTHETIC_ONLY)
INTRINSIC_RR = ab.INTRINSIC_RR         # the carried intrinsic-RR uncertainty, 12 / 16 / 20
DEMAND_SENSITIVITY = (1.0, 1.2)        # the arrival demand ratio is 1 by construction; 1.2 a synthetic sensitivity
PROBE_ANCHORS = replace(go.NEUTRAL, case_id="p2s2_mechanics_probe")   # RR 16 read as intrinsic, HCO3 24, PaCO2 40


def candidate(profile: dv.CoreProfile, **changes) -> dv.CoreProfile:
    return replace(profile, respiratory_mechanics=True, **changes)


def base_profile(**changes) -> dv.CoreProfile:
    """P2O-1's probe profile (the ACS common point, acid-base on, gas-exchange reference) with the candidate on."""
    return candidate(rd.base_profile(), **changes)


def driven(profile: dv.CoreProfile, drive: float = STRONG_DRIVE) -> dv.CoreProfile:
    """A synthetic excitatory input injected through P2P-2's slot (constant normalized 1 at every SpO2 x drive)."""
    return rd.injected(profile, drive)


def hypoxaemic(profile: dv.CoreProfile) -> dv.CoreProfile:
    return rd.hypoxaemic(profile, HYPOXAEMIC_GAIN)


def probe_anchors(**changes):
    return replace(PROBE_ANCHORS, **changes)


@dataclass(frozen=True)
class SyntheticMechanics(Contributor):
    """SYNTHETIC_ONLY: a scripted mechanics writer, the factor every minute in (start, stop]. Not a family writer, not
    registered (no replay needed)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2s2_probe_mechanics"

    id: str
    factor: float
    start_minute: int = 0
    stop_minute: int = 10 ** 6

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(mechanics=(MechanicsChange(self.factor, self.source, minute,
                                                       "probe: declared change of the mechanics efficiency"),))


def course(items, minutes, anchors, profile):
    return an.course(tuple(items), minutes, anchors, profile)


def breakdown(state, anchors, profile) -> dict:
    """One state's respiratory reading, decomposed as the faculty's form."""
    r = dv.respiration(state, anchors, profile)
    c = dv.respiratory_drive_composition(state, anchors, profile)
    demand = state.aux.oxygen_demand / anchors.metabolic_demand_baseline
    frequency = r.respiratory_rate / r.intrinsic_rr
    capacity = frequency * r.efficiency
    return {"acid_drive": c.acid_drive, "hypoxaemic_drive": c.hypoxaemic_drive, "excitatory_drive": c.excitatory_drive,
            "availability": c.availability, "intrinsic_rr": r.intrinsic_rr, "rr": r.respiratory_rate,
            "frequency_factor": frequency, "mechanics_efficiency": r.efficiency, "capacity": capacity,
            "demand_ratio": demand, "W": r.ventilation, "form_matches": math.isclose(r.ventilation, capacity / demand,
                                                                                      rel_tol=1e-12, abs_tol=1e-15),
            "paco2_reference": r.resting_paco2, "paco2": r.paco2, "ph": r.ph,
            "respiratory_load_signal": demand / r.efficiency}


def at_arrival(anchors, profile) -> dict:
    return breakdown(dv.arrival_state(anchors, profile), anchors, profile)


def _increasing(values) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def _decreasing(values) -> bool:
    return all(b < a for a, b in zip(values, values[1:]))


# P2S-2-7: probes M1-M12 ---------------------------------------------------------------------------------------------------------

PROBES = {
    "M1": "normal drive + availability 1 + mechanics reference: the W reference state (W 1, PaCO2 the reference)",
    "M2": "RR up, mechanics fixed: W up, PaCO2 down",
    "M3": "RR high + mechanics sufficiently reduced: W can stay low, PaCO2 high (the asthma / oedema property)",
    "M4": "RR low from central depression + mechanics normal: W low, PaCO2 high (the opioid property)",
    "M5": "same RR, lower mechanics: higher PaCO2",
    "M6": "same mechanics, lower RR: higher PaCO2",
    "M7": "the acid drive raises RR; W responds through RR only, no direct lactate control",
    "M8": "the hypoxaemic drive raises RR; W responds through RR only, no SpO2 -> PaCO2 shortcut",
    "M9": "central depression suppresses RR: W falls, PaCO2 rises",
    "M10": "a mechanics change alone moves no drive, intrinsic RR, availability, G, SpO2, D or lactate",
    "M11": "a G impairment alone does not change the mechanics efficiency",
    "M12": "an L impairment alone does not change the mechanics efficiency unless a writer declares it",
}


def probe_m1() -> dict:
    prof = base_profile()
    b = at_arrival(PROBE_ANCHORS, prof)
    return {**b, "pass": b["rr"] == b["intrinsic_rr"] == PROBE_ANCHORS.respiratory_rate and b["excitatory_drive"] == 0.0
            and b["availability"] == 1.0 and b["mechanics_efficiency"] == 1.0 and b["demand_ratio"] == 1.0
            and b["W"] == 1.0 and b["paco2"] == prof.paco2_reference_mmhg == 40.0}


def probe_m2() -> dict:
    prof, out = base_profile(), {}
    for efficiency in (1.0, 0.5):
        rows = [at_arrival(probe_anchors(arrival_bicarbonate=h, arrival_mechanics_efficiency=efficiency), prof)
                for h in BICARBONATES]
        out[f"{efficiency:g}"] = {"rr": [r["rr"] for r in rows], "W": [r["W"] for r in rows],
                                  "paco2": [r["paco2"] for r in rows],
                                  "efficiency_fixed": {r["mechanics_efficiency"] for r in rows} == {efficiency}}
    out["pass"] = all(_increasing(v["rr"]) and _increasing(v["W"]) and _decreasing(v["paco2"]) and v["efficiency_fixed"]
                      for v in out.values())
    return out


def _efficiency_line(anchors, prof) -> list:
    return [at_arrival(replace(anchors, arrival_mechanics_efficiency=e), prof) for e in SYNTHETIC_EFFICIENCIES]


def probe_m3() -> dict:
    prof = driven(base_profile())
    rows = _efficiency_line(PROBE_ANCHORS, prof)
    boundary = rows[0]["demand_ratio"] * rows[0]["intrinsic_rr"] / rows[0]["rr"]
    points = [{"efficiency": e, "rr": r["rr"], "W": r["W"], "paco2": r["paco2"]} for e, r in zip(SYNTHETIC_EFFICIENCIES,
                                                                                                rows)]
    high = [p for p in points if p["rr"] >= 1.5 * PROBE_ANCHORS.respiratory_rate and p["W"] < 1.0 and p["paco2"] > 40.0]
    return {"points": points, "availability": rows[0]["availability"], "boundary_efficiency": boundary,
            "hypercapnic_points": [p["efficiency"] for p in high],
            "pass": bool(high) and rows[0]["availability"] == 1.0 and all((p["paco2"] > 40.0) == (p["efficiency"] < boundary)
                                                                          for p in points)}


def probe_m4() -> dict:
    prof = base_profile(central_drive_availability=DEPRESSED)
    b = at_arrival(PROBE_ANCHORS, prof)
    return {**b, "pass": b["rr"] < b["intrinsic_rr"] and b["mechanics_efficiency"] == 1.0 and b["W"] < 1.0
            and b["paco2"] > 40.0}


def probe_m5() -> dict:
    rows = _efficiency_line(PROBE_ANCHORS, driven(base_profile()))
    return {"efficiency": list(SYNTHETIC_EFFICIENCIES), "rr": [r["rr"] for r in rows], "paco2": [r["paco2"] for r in rows],
            "pass": len({r["rr"] for r in rows}) == 1 and _increasing([r["paco2"] for r in rows])}


def probe_m6() -> dict:
    out = {}
    for efficiency in (1.0, LOW_EFFICIENCY):
        rows = [at_arrival(probe_anchors(arrival_mechanics_efficiency=efficiency),
                           driven(base_profile(central_drive_availability=a))) for a in AVAILABILITIES[:-1]]
        out[f"{efficiency:g}"] = {"availability": list(AVAILABILITIES[:-1]), "rr": [r["rr"] for r in rows],
                                  "paco2": [r["paco2"] for r in rows],
                                  "efficiency_fixed": {r["mechanics_efficiency"] for r in rows} == {efficiency}}
    out["pass"] = all(_decreasing(v["rr"]) and _increasing(v["paco2"]) and v["efficiency_fixed"] for v in out.values())
    return out


def _matched(anchors_a, prof_a, anchors_b, prof_b) -> dict:
    """B's availability scaled so that its expressed RR equals A's: then W and PaCO2 must match (through RR only)."""
    a = at_arrival(anchors_a, prof_a)
    comp = dv.arrival_drive_composition(anchors_b, prof_b)
    prof_b = replace(prof_b, central_drive_availability=a["rr"] / comp.excitatory_rr)
    b = at_arrival(anchors_b, prof_b)
    return {"rr": [a["rr"], b["rr"]], "W": [a["W"], b["W"]], "paco2": [a["paco2"], b["paco2"]],
            "inputs_differ": (a["acid_drive"], a["hypoxaemic_drive"]) != (b["acid_drive"], b["hypoxaemic_drive"]),
            "same": math.isclose(a["W"], b["W"], rel_tol=1e-12) and math.isclose(a["paco2"], b["paco2"], rel_tol=1e-12)}


def probe_m7() -> dict:
    prof = base_profile()
    acid = [at_arrival(probe_anchors(arrival_bicarbonate=h), prof) for h in BICARBONATES]
    # The lactate is read by D and the lactate kinetics, never by the respiration: two arrivals that differ by lactate only.
    lactate = [at_arrival(probe_anchors(arrival_bicarbonate=BICARBONATES[2], lactate=x), prof) for x in (1.0, 6.0)]
    matched = _matched(probe_anchors(arrival_bicarbonate=BICARBONATES[1]), prof,
                       probe_anchors(arrival_bicarbonate=BICARBONATES[3]), prof)
    funcs = _functions((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    reads_lactate = bool({"lactate", "lactate_excess_mmol_l"} & _names(funcs["respiration"]))
    out = {"rr": [r["rr"] for r in acid], "W": [r["W"] for r in acid], "acid_drive": [r["acid_drive"] for r in acid],
           "lactate_independent": lactate[0] == lactate[1], "matched_rr": matched,
           "respiration_reads_lactate": reads_lactate}
    out["pass"] = (_increasing(out["acid_drive"]) and _increasing(out["rr"]) and _increasing(out["W"])
                   and out["lactate_independent"] and matched["inputs_differ"] and matched["same"] and not reads_lactate)
    return out


def probe_m8() -> dict:
    prof = hypoxaemic(base_profile())
    rows = [at_arrival(probe_anchors(spo2=s), prof) for s in HYPOXAEMIC_SPO2S]
    matched = _matched(probe_anchors(spo2=HYPOXAEMIC_SPO2S[1]), prof, probe_anchors(spo2=HYPOXAEMIC_SPO2S[2]), prof)
    funcs = _functions((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    branch = _candidate_branch(funcs)
    shortcut = bool({"spo2", "_perfusion", "oxygenation"} & set().union(*(_names(s) for s in branch.body)))
    out = {"spo2": list(HYPOXAEMIC_SPO2S), "hypoxaemic_drive": [r["hypoxaemic_drive"] for r in rows],
           "rr": [r["rr"] for r in rows], "W": [r["W"] for r in rows], "paco2": [r["paco2"] for r in rows],
           "matched_rr": matched, "ventilation_reads_spo2": shortcut}
    out["pass"] = (_increasing(out["hypoxaemic_drive"]) and _increasing(out["rr"]) and _increasing(out["W"])
                   and _decreasing(out["paco2"]) and matched["inputs_differ"] and matched["same"] and not shortcut)
    return out


def probe_m9() -> dict:
    rows = [at_arrival(PROBE_ANCHORS, base_profile(central_drive_availability=a)) for a in AVAILABILITIES]
    breathing = rows[:-1]
    return {"availability": list(AVAILABILITIES), "rr": [r["rr"] for r in rows], "W": [r["W"] for r in rows],
            "paco2": [r["paco2"] for r in rows], "intrinsic_rr": rows[0]["intrinsic_rr"],
            "pass": _decreasing([r["rr"] for r in breathing]) and _decreasing([r["W"] for r in breathing])
            and _increasing([r["paco2"] for r in breathing]) and rows[-1]["rr"] == 0.0 and rows[-1]["paco2"] is None
            and {r["mechanics_efficiency"] for r in rows} == {1.0} and {r["intrinsic_rr"] for r in rows} == {16.0}}


def _hypoxaemic_course(items, profile=None, anchors=None):
    anchors = probe_anchors(spo2=HYPOXAEMIC_SPO2S[2]) if anchors is None else anchors
    profile = hypoxaemic(base_profile()) if profile is None else profile
    states, records = course(items, COURSE_MINUTES, anchors, profile)
    return states, records, anchors, profile


def _without_mechanics(state) -> dict:
    data = state.to_dict()
    data["aux"] = {k: v for k, v in data["aux"].items() if k != "mechanics_efficiency"}
    return data


def probe_m10() -> dict:
    s1, _, a, prof = _hypoxaemic_course(())
    s2, r2, _, _ = _hypoxaemic_course((SyntheticMechanics("p2s2-mechanics", MECHANICS_FACTOR),))
    same_states = [_without_mechanics(x) for x in s1] == [_without_mechanics(x) for x in s2]
    d1 = [dv.derive(x, a, prof).to_dict() for x in s1]
    d2 = [dv.derive(x, a, prof).to_dict() for x in s2]
    b1 = [breakdown(x, a, prof) for x in s1]
    b2 = [breakdown(x, a, prof) for x in s2]
    unchanged = {k: [x[k] for x in b1] == [y[k] for y in b2] for k in ("acid_drive", "hypoxaemic_drive",
                                                                         "excitatory_drive", "intrinsic_rr",
                                                                         "availability", "rr", "demand_ratio")}
    unchanged.update({k: all(getattr(x, k) == getattr(y, k) for x, y in zip(s1, s2)) for k in ("G", "D", "L")})
    unchanged.update({k: all(x[k] == y[k] for x, y in zip(d1, d2)) for k in ("spo2", "lactate", "monitor_rate_bpm",
                                                                            "delivery_rel", "consciousness_level")})
    unchanged["acid_burden"] = all(x.aux.metabolic_acid_burden == y.aux.metabolic_acid_burden for x, y in zip(s1, s2))
    efficiency = [x.aux.mechanics_efficiency for x in s2]
    moved = _decreasing(efficiency) and _decreasing([y["W"] for y in b2]) and _increasing([y["paco2"] for y in b2])
    sources = sorted({c.source.key for r in r2 for c in r.mechanics})
    return {"states_identical_but_mechanics": same_states, "derived_identical": d1 == d2, "unchanged": unchanged,
            "efficiency_end": efficiency[-1], "paco2": [b1[-1]["paco2"], b2[-1]["paco2"]], "writer_sources": sources,
            "pass": same_states and d1 == d2 and all(unchanged.values()) and moved
            and sources == ["scripted_event:p2s2-mechanics"]}


def probe_m11() -> dict:
    out = {}
    for label, prof in (("hypoxaemic_drive_unset", base_profile()), ("synthetic_hypoxaemic_drive",
                                                                     hypoxaemic(base_profile()))):
        states, records, a, _ = _hypoxaemic_course((bands.Drift("p2s2-g", "G", 0, COURSE_MINUTES, G_PER_MIN),),
                                                   profile=prof, anchors=PROBE_ANCHORS)
        rows = [breakdown(s, a, prof) for s in states]
        spo2 = [dv.derive(s, a, prof).spo2 for s in states]
        out[label] = {"G_end": states[-1].G, "spo2": [spo2[0], spo2[-1]], "rr": [rows[0]["rr"], rows[-1]["rr"]],
                      "W": [rows[0]["W"], rows[-1]["W"]],
                      "efficiency_constant": {s.aux.mechanics_efficiency for s in states} == {1.0},
                      "no_mechanics_records": not any(r.mechanics for r in records),
                      "w_through_rr_only": all(math.isclose(r["W"], r["rr"] / r["intrinsic_rr"], rel_tol=1e-12)
                                               for r in rows)}
    out["pass"] = all(v["efficiency_constant"] and v["no_mechanics_records"] and v["w_through_rr_only"]
                      and v["G_end"] > 0.0 and v["spo2"][1] < v["spo2"][0] for v in out.values())
    out["pass"] = out["pass"] and out["hypoxaemic_drive_unset"]["W"][0] == out["hypoxaemic_drive_unset"]["W"][1] \
        and out["synthetic_hypoxaemic_drive"]["W"][1] > out["synthetic_hypoxaemic_drive"]["W"][0]
    return out


def probe_m12() -> dict:
    prof = base_profile()
    drift = bands.Drift("p2s2-l", "L", 0, COURSE_MINUTES, L_PER_MIN)
    plain, records, a, _ = _hypoxaemic_course((drift,), profile=prof, anchors=PROBE_ANCHORS)
    written, wrecords, _, _ = _hypoxaemic_course((drift, SyntheticMechanics("p2s2-mechanics", MECHANICS_FACTOR)),
                                                 profile=prof, anchors=PROBE_ANCHORS)
    spo2 = [dv.derive(s, a, prof).spo2 for s in plain]
    out = {"L_end": plain[-1].L, "G_end": plain[-1].G, "spo2": [spo2[0], spo2[-1]],
           "efficiency_constant": {s.aux.mechanics_efficiency for s in plain} == {1.0},
           "no_mechanics_records": not any(r.mechanics for r in records),
           "with_declared_writer": written[-1].aux.mechanics_efficiency,
           "writer_recorded": all(len(r.mechanics) == 1 for r in wrecords)}
    out["pass"] = (out["efficiency_constant"] and out["no_mechanics_records"] and out["L_end"] > 0.0
                   and out["G_end"] > 0.0 and out["spo2"][1] < out["spo2"][0]
                   and math.isclose(out["with_declared_writer"], MECHANICS_FACTOR ** COURSE_MINUTES, rel_tol=1e-12)
                   and out["writer_recorded"])
    return out


def structural_probes() -> dict:
    found = {"M1": probe_m1(), "M2": probe_m2(), "M3": probe_m3(), "M4": probe_m4(), "M5": probe_m5(), "M6": probe_m6(),
             "M7": probe_m7(), "M8": probe_m8(), "M9": probe_m9(), "M10": probe_m10(), "M11": probe_m11(),
             "M12": probe_m12()}
    return {"probes": found, "pass": {k: v["pass"] for k, v in found.items()}}


DEMAND_RATIOS = (1.0, 1.2, 1.5)          # synthetic demand ratios on one state (P2S-2-5)


def directions() -> dict:
    """P2S-2-5 / 6: the required directions on one state each, everything else held: RR up -> W up (M2); mechanics down
    -> W down (M5); demand up -> W down relative to need, RR unchanged; central depression -> W down (M9); W up ->
    PaCO2 down over every probe point (PaCO2 = reference / W, nothing else)."""
    prof = base_profile()
    state = dv.arrival_state(PROBE_ANCHORS, prof)
    demand = [breakdown(state.evolve(aux=replace(state.aux, oxygen_demand=state.aux.oxygen_demand * f)), PROBE_ANCHORS,
                        prof) for f in DEMAND_RATIOS]
    points = []
    for anchors, profile in ((probe_anchors(arrival_mechanics_efficiency=e, arrival_bicarbonate=h), driven(base_profile(
            central_drive_availability=a))) for e in SYNTHETIC_EFFICIENCIES for h in BICARBONATES[::3]
            for a in AVAILABILITIES[:3]):
        b = at_arrival(anchors, profile)
        points.append((b["W"], b["paco2"], b["form_matches"]))
    ordered = sorted(points)
    out = {"demand": {"ratio": list(DEMAND_RATIOS), "rr": [d["rr"] for d in demand], "W": [d["W"] for d in demand],
                      "paco2": [d["paco2"] for d in demand]},
           "paco2_against_w": {"points": len(points), "strictly_decreasing": all(
               (b[1] < a[1]) if b[0] > a[0] else (b[1] == a[1]) for a, b in zip(ordered, ordered[1:])),
               "reference_over_w": all(math.isclose(p, 40.0 / w, rel_tol=1e-12) for w, p, _ in points),
               "form_matches": all(f for _, _, f in points)}}
    out["pass"] = (len(set(out["demand"]["rr"])) == 1 and _decreasing(out["demand"]["W"])
                   and _increasing(out["demand"]["paco2"]) and out["paco2_against_w"]["strictly_decreasing"]
                   and out["paco2_against_w"]["reference_over_w"] and out["paco2_against_w"]["form_matches"])
    return out


# P2S-2-4: the family writer interface ------------------------------------------------------------------------------------------

def interface() -> dict:
    prof = base_profile()
    # Persistence: a writer that stops leaves the efficiency where it put it (no return to arrival, no core kinetics).
    stop = SyntheticMechanics("p2s2-burst", 0.9, 0, 5)
    states, records = course((stop,), 10, PROBE_ANCHORS, prof)
    burst = [s.aux.mechanics_efficiency for s in states]
    two = (SyntheticMechanics("p2s2-a", 0.9), SyntheticMechanics("p2s2-b", 1.2))
    s2, r2 = course(two, 3, PROBE_ANCHORS, prof)
    refused = {}
    try:
        course((SyntheticMechanics("p2s2-off", 0.9),), 1, PROBE_ANCHORS, rd.base_profile())
        refused["change_when_off"] = False
    except ProvenanceError:
        refused["change_when_off"] = True
    try:
        dv.arrival_state(probe_anchors(arrival_mechanics_efficiency=0.5), rd.base_profile())
        refused["arrival_when_off"] = False
    except CoreInvariantError:
        refused["arrival_when_off"] = True
    try:
        dv.respiration(dv.arrival_state(PROBE_ANCHORS, rd.base_profile()).evolve(
            aux=replace(dv.arrival_state(PROBE_ANCHORS, rd.base_profile()).aux, mechanics_efficiency=0.5)),
            PROBE_ANCHORS, rd.base_profile())
        refused["state_when_off"] = False
    except CoreInvariantError:
        refused["state_when_off"] = True
    for name, factor in (("zero", 0.0), ("negative", -0.5), ("infinite", float("inf")), ("nan", float("nan")),
                         ("boolean", True)):
        try:
            MechanicsChange(factor, stop.source, 1, "x")
            refused[f"factor_{name}"] = False
        except ProvenanceError:
            refused[f"factor_{name}"] = True
    for name, build in (("needs_acid_base", lambda: candidate(dv.DEFAULT_PROFILE)),
                        ("needs_reference_efficiency", lambda: base_profile(ventilation_efficiency=0.5))):
        try:
            build()
            refused[f"profile_{name}"] = False
        except CoreInvariantError:
            refused[f"profile_{name}"] = True
    auxiliary = [c for r in records for c in r.auxiliary if c.quantity == "mechanics_efficiency"]
    family_writers = sorted(str(p.relative_to(ROOT)) for p in (CORE_DIR / "modules").rglob("*.py")
                            if "MechanicsChange" in p.read_text(encoding="utf-8") or "mechanics" in
                            p.read_text(encoding="utf-8"))
    out = {"burst": burst, "persists": burst[5:] == [burst[5]] * 6 and math.isclose(burst[5], 0.9 ** 5, rel_tol=1e-12)
           and _decreasing(burst[:6]),
           "two_writers": [s.aux.mechanics_efficiency for s in s2],
           "compose": all(math.isclose(s.aux.mechanics_efficiency, (0.9 * 1.2) ** s.minute, rel_tol=1e-12) for s in s2),
           "records": [len(r.mechanics) for r in r2], "aux_source": sorted({c.source.key for c in auxiliary}),
           "refused": refused, "family_writers": family_writers}
    out["pass"] = (out["persists"] and out["compose"] and out["records"] == [2, 2, 2] and all(refused.values())
                   and out["aux_source"] == ["core_coupling:respiratory_mechanics"] and not family_writers)
    return out


# P2S-2-8 / 9 / 10: contrasts ---------------------------------------------------------------------------------------------------

HIGH_RR_CASES = ("pulmonary_edema_58m", "asthma_49m")
COMPENSATED_CASE = "asthma_24f"
OPIOID_CASE = "opioid_35m"
DIAGNOSTIC_CASES = ("pulmonary_edema_58m", "asthma_49m", "asthma_24f", "opioid_35m", "gi_bleed_57m", "gi_bleed_72f",
                    "acs_70f_left_main", "pulmonary_embolism_61m", "pulmonary_embolism_33f")
TRUTH_PATHS = {"rr": ("observable", "respiratory_rate"), "paco2": ("investigations", "abg", "result", "paco2_mm_hg"),
               "hco3": ("investigations", "abg", "result", "bicarbonate_mmol_l"),
               "fio2_percent": ("investigations", "abg", "result", "fio2_percent"), "spo2": ("observable", "spo2"),
               "work_of_breathing": ("observable", "work_of_breathing"), "mental_status": ("observable", "mental_status")}


def _bank() -> dict:
    import clinical_cases
    return {c["id"]: c for family in clinical_cases.FAMILIES.values() for c in family["variants"]}


def truth(case_id: str) -> dict:
    """AUTHORED_CASE_TRUTH, read by path from the case bank (never retyped); used only as diagnostics."""
    case = _bank()[case_id]
    out = {}
    for name, path in TRUTH_PATHS.items():
        value = case
        for key in path:
            value = value[key]
        out[name] = value
    return out


def implied_efficiency(rr: float, paco2: float, intrinsic: float, demand_ratio: float = 1.0,
                       reference: float = dv.DEFAULT_PROFILE.paco2_reference_mmhg) -> float:
    """The mechanics efficiency the candidate needs for an RR and a PaCO2: W = reference / PaCO2 and W = (RR / intrinsic)
    x E / demand, so E = reference x demand x intrinsic / (PaCO2 x RR). Analytic, a diagnostic, never a selection."""
    return reference * demand_ratio * intrinsic / (paco2 * rr)


def analytic_paco2(rr: float, intrinsic: float, efficiency: float, demand_ratio: float = 1.0,
                   reference: float = dv.DEFAULT_PROFILE.paco2_reference_mmhg) -> float:
    """The candidate's PaCO2 at an RR, through the core's one W formula."""
    return reference / dv.alveolar_ventilation(rr, intrinsic, efficiency, demand_ratio)


def high_rr_high_paco2() -> dict:
    """P2S-2-8: oedema 58m and asthma 49m at their authored (high) RR, availability 1: the synthetic efficiencies below the
    boundary intrinsic / RR give PaCO2 above the reference; the same holds end to end in the core (the oedema case's
    committed arrival and the neutral probe, a synthetic excitatory input, no central depression)."""
    cases = {}
    for case_id in HIGH_RR_CASES:
        t = truth(case_id)
        rows = {f"{i:g}": {f"{e:g}": analytic_paco2(t["rr"], i, e) for e in SYNTHETIC_EFFICIENCIES} for i in INTRINSIC_RR}
        boundary = {f"{i:g}": i / t["rr"] for i in INTRINSIC_RR}
        cases[case_id] = {"authored_rr": t["rr"], "authored_paco2": t["paco2"], "paco2_by_intrinsic": rows,
                          "boundary_efficiency": boundary,
                          "hypercapnic_at_every_intrinsic": all(any(p > 40.0 for p in r.values()) for r in rows.values()),
                          "rr_above_intrinsic_band": t["rr"] > max(INTRINSIC_RR)}
    core = {}
    edema = replace(er.anchors(), arrival_mechanics_efficiency=LOW_EFFICIENCY)
    for label, anchors, prof in (("pulmonary_edema_58m_committed_arrival", edema, driven(candidate(pe.profile()))),
                                 ("neutral_probe", probe_anchors(arrival_mechanics_efficiency=LOW_EFFICIENCY),
                                  driven(base_profile()))):
        b = at_arrival(anchors, prof)
        core[label] = {k: b[k] for k in ("rr", "intrinsic_rr", "availability", "mechanics_efficiency", "W", "paco2")}
        core[label]["pass"] = b["rr"] > max(INTRINSIC_RR) and b["paco2"] > 40.0 and b["availability"] == 1.0
    ok = all(v["hypercapnic_at_every_intrinsic"] and v["rr_above_intrinsic_band"] for v in cases.values()) and all(
        v["pass"] for v in core.values())
    return {"cases": cases, "core": core, "class": "HIGH_RR_HIGH_PACO2_STRUCTURALLY_REPRESENTABLE" if ok else
            "HIGH_RR_HIGH_PACO2_NOT_REPRESENTABLE", "pass": ok}


def compensated_contrast() -> dict:
    """P2S-2-9: asthma 24f at its authored RR with a less reduced (synthetic) efficiency gives a low / normal PaCO2, and
    asthma 49m with a markedly reduced one a high PaCO2, at every carried intrinsic RR; no efficiency is selected."""
    mild, severe = truth(COMPENSATED_CASE), truth("asthma_49m")
    rows = {}
    for i in INTRINSIC_RR:
        rows[f"{i:g}"] = {"asthma_24f_mild": analytic_paco2(mild["rr"], i, MILD_EFFICIENCY),
                          "asthma_49m_low": analytic_paco2(severe["rr"], i, LOW_EFFICIENCY),
                          "boundary_24f": i / mild["rr"], "boundary_49m": i / severe["rr"]}
    ok = all(r["asthma_24f_mild"] <= 40.0 < r["asthma_49m_low"] for r in rows.values())
    return {"authored": {COMPENSATED_CASE: mild, "asthma_49m": severe}, "efficiencies": {"mild": MILD_EFFICIENCY,
                                                                                        "low": LOW_EFFICIENCY},
            "by_intrinsic": rows, "pass": ok and mild["rr"] > max(INTRINSIC_RR)}


def opioid_contrast() -> dict:
    """P2S-2-10: central availability low with mechanics preserved gives low RR and high PaCO2, mechanics unchanged;
    mechanics low with availability 1 gives high RR and high PaCO2, availability unchanged. Two failures, one W."""
    central = at_arrival(PROBE_ANCHORS, base_profile(central_drive_availability=rd.STRONG_DEPRESSION))
    mechanical = at_arrival(probe_anchors(arrival_mechanics_efficiency=LOW_EFFICIENCY), driven(base_profile()))
    reference = at_arrival(PROBE_ANCHORS, base_profile())
    keep = ("rr", "availability", "mechanics_efficiency", "W", "paco2")
    t = truth(OPIOID_CASE)
    out = {"CENTRAL_DRIVE_FAILURE": {k: central[k] for k in keep},
           "MECHANICAL_VENTILATORY_FAILURE": {k: mechanical[k] for k in keep},
           "reference": {k: reference[k] for k in keep},
           "opioid_35m_authored": {"rr": t["rr"], "paco2": t["paco2"],
                                   "implied_efficiency": {f"{i:g}": implied_efficiency(t["rr"], t["paco2"], i)
                                                          for i in INTRINSIC_RR}}}
    out["pass"] = (central["rr"] < reference["rr"] and central["paco2"] > 40.0 and central["mechanics_efficiency"] == 1.0
                   and central["availability"] < 1.0 and mechanical["rr"] > reference["rr"] and mechanical["paco2"] > 40.0
                   and mechanical["availability"] == 1.0 and mechanical["mechanics_efficiency"] < 1.0)
    return out


# P2S-2-11: arrival-efficiency diagnostic regions (authored truth as diagnostics only) ------------------------------------------

ORDERING_RULE = ("Predeclared, at each carried intrinsic RR (12 / 16 / 20, the same for every case): (a) the severe "
                 "cases (oedema 58m, asthma 49m) below compensated asthma 24f; (b) asthma 24f below every reference "
                 "without major mechanics impairment (GI 57m, GI 72f, ACS 70f); (c) opioid 35m not below the lowest of "
                 "those references (mechanics relatively preserved). PE is informative only. Coherent when (a), (b) and "
                 "(c) hold at every level; otherwise STOP with a semantic problem. Regions across different intrinsic "
                 "RRs may overlap; that is reported as an identifiability limit, never decided here")
SEVERE = ("pulmonary_edema_58m", "asthma_49m")
REFERENCES = ("gi_bleed_57m", "gi_bleed_72f", "acs_70f_left_main")
INFORMATIVE = ("pulmonary_embolism_61m", "pulmonary_embolism_33f")


def model_arrival_rr(case_id: str, intrinsic: float, profile: dv.CoreProfile | None = None) -> float:
    """The arrival RR the committed common point gives a case (acid drive only, hypoxaemic drive UNSET, availability 1):
    the counterfactual reading, never the diagnostic."""
    profile = ar.common_profile() if profile is None else profile
    burden = max(0.0, profile.bicarbonate_reference_meq_l - float(truth(case_id)["hco3"]))
    return profile.central_drive_availability * dv.rate_from_drive(dv.respiratory_drive(burden, profile), intrinsic,
                                                                   profile)


def arrival_regions() -> dict:
    regions = {}
    for case_id in DIAGNOSTIC_CASES:
        t = truth(case_id)
        by = {f"{i:g}": implied_efficiency(t["rr"], t["paco2"], i) for i in INTRINSIC_RR}
        model = {f"{i:g}": implied_efficiency(model_arrival_rr(case_id, i), t["paco2"], i) for i in INTRINSIC_RR}
        regions[case_id] = {"authored_rr": t["rr"], "authored_paco2": t["paco2"], "authored_hco3": t["hco3"],
                            "fio2_percent": t["fio2_percent"], "work_of_breathing": t["work_of_breathing"],
                            "by_intrinsic": by, "region": [min(by.values()), max(by.values())],
                            "demand_sensitivity": {f"{d:g}": [implied_efficiency(t["rr"], t["paco2"], i, d)
                                                              for i in (min(INTRINSIC_RR), max(INTRINSIC_RR))]
                                                   for d in DEMAND_SENSITIVITY},
                            "counterfactual_model_rr": {f"{i:g}": model_arrival_rr(case_id, i) for i in INTRINSIC_RR},
                            "counterfactual_efficiency_at_model_rr": model}
    levels = [f"{i:g}" for i in INTRINSIC_RR]
    e = {c: regions[c]["by_intrinsic"] for c in DIAGNOSTIC_CASES}
    a = {lv: max(e[c][lv] for c in SEVERE) < e[COMPENSATED_CASE][lv] for lv in levels}
    b = {lv: e[COMPENSATED_CASE][lv] < min(e[c][lv] for c in REFERENCES) for lv in levels}
    c = {lv: e[OPIOID_CASE][lv] >= min(e[x][lv] for x in REFERENCES) for lv in levels}
    overlaps = {}
    for one, two in ((SEVERE[0], COMPENSATED_CASE), (SEVERE[1], COMPENSATED_CASE), (COMPENSATED_CASE, REFERENCES[0]),
                     (COMPENSATED_CASE, REFERENCES[2])):
        low, high = max(regions[one]["region"][0], regions[two]["region"][0]), min(regions[one]["region"][1],
                                                                                    regions[two]["region"][1])
        overlaps[f"{one}|{two}"] = [low, high] if low <= high else None
    coherent = all(a.values()) and all(b.values()) and all(c.values())
    return {"regions": regions, "rule": ORDERING_RULE, "ordering": {"severe_below_compensated": a,
                                                                     "compensated_below_references": b,
                                                                     "opioid_preserved": c},
            "overlaps_across_intrinsic": overlaps, "coherent": coherent,
            "class": "CLINICALLY_COHERENT_ORDERING" if coherent else "SEMANTIC_PROBLEM_STOP",
            "references_below_1": {x: [lv for lv in levels if e[x][lv] < 1.0] for x in REFERENCES},
            "reading": "the arrival efficiency is read with the authored RR: a region per case over the intrinsic RR, "
                       "linear in it and in the demand ratio. With the model's arrival RR (acid drive only) the reading "
                       "would absorb the drive gap (the opioid would read as a mechanical failure); the asthma migration "
                       "must map availability and the excitatory drive before it maps mechanics",
            "pass": coherent}


# P2S-2-12 to 15 ---------------------------------------------------------------------------------------------------------------

def no_anchor_absorption() -> dict:
    """The candidate's arrival PaCO2 is the common reference over W: the authored arrival PaCO2 moves nothing (the P2K-2
    path, off, still reads it as its anchor)."""
    on, off = base_profile(), rd.base_profile()
    rows = {f"{p:g}": {"candidate": at_arrival(probe_anchors(arrival_paco2=p), on)["paco2"],
                       "p2k2": at_arrival(probe_anchors(arrival_paco2=p), off)["paco2"]} for p in (30.0, 40.0, 60.0)}
    edema = er.anchors()
    edema_on = at_arrival(edema, candidate(pe.profile()))
    funcs = _functions((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    branch = _candidate_branch(funcs)
    reads = set().union(*(_names(s) for s in branch.body))
    out = {"by_authored_paco2": rows, "references": sorted({at_arrival(probe_anchors(arrival_paco2=p), on)
                                                            ["paco2_reference"] for p in (30.0, 60.0)}),
           "edema_candidate_arrival": {"authored_paco2": edema.arrival_paco2, "candidate_paco2": edema_on["paco2"],
                                       "model_rr": edema_on["rr"], "authored_rr": edema.respiratory_rate,
                                       "mismatch_reported": edema_on["paco2"] - edema.arrival_paco2},
           "candidate_reads_anchor": bool({"arrival_paco2", "arrival_alveolar_ventilation"} & reads)}
    out["pass"] = (len({r["candidate"] for r in rows.values()}) == 1 and rows["40"]["candidate"] == 40.0
                   and [r["p2k2"] for r in rows.values()] == [30.0, 40.0, 60.0] and out["references"] == [40.0]
                   and not out["candidate_reads_anchor"])
    return out


def oxygenation_deferred(found_m10: dict) -> dict:
    a = audit()
    return {"status": "HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED",
            "spo2_unchanged_by_mechanics": found_m10["unchanged"]["spo2"],
            "oxygenation_reads_ventilation": a["oxygenation_reads_ventilation"],
            "pass": found_m10["unchanged"]["spo2"] and not any(a["oxygenation_reads_ventilation"].values())}


FORBIDDEN_NAMES = ("fatigue", "compliance", "resistance", "dead_space", "deadspace", "tidal", "muscle", "asthma",
                   "bronch", "opioid", "oedema", "edema")


def _fields_of(text: str, cls: str) -> list:
    tree = ast.parse(text)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
    return [n.target.id for n in node.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]


def no_extra_state() -> dict:
    added = {}
    for relative, cls in (("clinical_core/state.py", "AuxiliaryState"), ("clinical_core/state.py", "Anchors"),
                          ("clinical_core/derived.py", "CoreProfile"), ("clinical_core/integration.py", "Contribution"),
                          ("clinical_core/provenance.py", "MinuteRecord")):
        old, new = _fields_of(p2q2_text(relative), cls), _fields_of(_live(relative), cls)
        added[cls] = sorted(set(new) - set(old))
    inserted = "\n".join(live for relative in CORE_FILES for live, _ in REVERSAL[relative]).lower()
    channels = [c.value for c in Channel]
    out = {"added_fields": added, "forbidden_in_insertions": sorted(n for n in FORBIDDEN_NAMES if n in inserted),
           "channels": channels, "auxiliary": list(AUXILIARY_FIELDS),
           "core_kinetics": "none: the integration composes the minute's declared factors only"}
    out["pass"] = (added == {"AuxiliaryState": ["mechanics_efficiency"], "Anchors": ["arrival_mechanics_efficiency"],
                             "CoreProfile": ["respiratory_mechanics"], "Contribution": ["mechanics"],
                             "MinuteRecord": ["mechanics"]}
                   and not out["forbidden_in_insertions"] and channels == ["V", "T", "P", "R", "L", "G", "W", "D", "N",
                                                                           "hb", "glucose", "k"])
    return out


def w_uniqueness() -> dict:
    """One W in the candidate: no source may write the W channel (refused) and nothing reads it (a state carrying one
    reads exactly as without it), the RR is P2P-2's (never read from W), and W is computed after the RR from RR,
    mechanics and demand. The P2K-1 reader keeps its historical behaviour with the acid-base physiology off."""
    on = base_profile()
    state = dv.arrival_state(PROBE_ANCHORS, on)
    try:
        step(state, (bands.Drift("p2s2-w", "W", 0, 1, 0.2),), PROBE_ANCHORS, on)
        refused = False
    except ProvenanceError:
        refused = True
    carrying = state.evolve(W=0.2)
    inert = (astuple(dv.respiration(carrying, PROBE_ANCHORS, on)) == astuple(dv.respiration(state, PROBE_ANCHORS, on))
             and dv.derive(carrying, PROBE_ANCHORS, on).to_dict() == dv.derive(state, PROBE_ANCHORS, on).to_dict())
    derived_rr = dv.derive(state, PROBE_ANCHORS, on).respiratory_rate
    historical = dv.arrival_state(PROBE_ANCHORS)
    p2k1 = [dv.derive(historical.evolve(W=w), PROBE_ANCHORS).respiratory_rate for w in (-0.5, 0.0, 0.5)]
    a = audit()
    out = {"w_channel_write_refused": refused, "w_channel_inert": inert,
           "derive_rr_is_respiration_rr": derived_rr == dv.respiration(
        state, PROBE_ANCHORS, on).respiratory_rate, "p2k1_reader_default_profile": p2k1,
           "p2k1_status": RETIRED_FROM_CANDIDATE + " (still ACTIVE_CURRENT with the acid-base physiology off)",
           "w_channel_readers": a["w_channel_readers"],
           "drive_reads_w_or_mechanics": a["composition_reads_mechanics_or_w"]}
    out["pass"] = (refused and inert and out["derive_rr_is_respiration_rr"] and _increasing(p2k1)
                   and not any(out["drive_reads_w_or_mechanics"].values())
                   and out["w_channel_readers"] == ["respiratory_rate"])
    return out


def respiratory_load_signal() -> dict:
    """The demand over the mechanics efficiency: the frequency factor the patient needs for W = 1 (W = frequency factor x
    E / demand). It follows from the equations, needs no parameter and has no reader: exposed here only."""
    rows = {f"{e:g}": 1.0 / e for e in SYNTHETIC_EFFICIENCIES}
    readers = sorted(str(p.relative_to(ROOT)) for p in CORE_DIR.rglob("*.py")
                     if "respiratory_load_signal" in p.read_text(encoding="utf-8") and p.name not in
                     ("respiratory_mechanics.py", "respiratory_mechanics_report.py"))
    return {"status": "EXPOSED_DIAGNOSTIC_ONLY", "definition": "demand_ratio / mechanics_efficiency (dimensionless)",
            "required_frequency_factor_at_baseline_demand": rows, "readers": readers, "pass": not readers}


def heart_rate() -> dict:
    """P2S-2-18: no HR change. The sinus rate reads no respiration, W, PaCO2 or mechanics; the HR the candidate gives a
    mechanics change is the HR it gives without it (M10); the HR gap is carried forward as a hypothesis."""
    a = audit()
    return {"carried_forward": "HR_GAP_DISTRESS_AROUSAL_DOMINANT (diagnostic hypothesis; no sympathetic gain, no reader)",
            "hr_reads_respiration": a["heart_rate_reads_respiration"],
            "pass": not any(a["heart_rate_reads_respiration"].values())}


PARAMETER_STATUS = {
    "mechanics_efficiency_clinical_values": "UNSET (1 the STRUCTURAL_REFERENCE; synthetic values in probes only)",
    "arrival_mechanics_efficiency": "CASE / FAMILY LATENT ARRIVAL MAPPING, UNSET in every committed case",
    "respiratory_mechanics": "STRUCTURAL_SWITCH, off by default",
    "paco2_reference_mmhg": "40, COMMON_REFERENCE_PROVISIONAL, not approved",
    "hypoxaemic_drive_mapping_and_gain": "UNSET",
    "central_drive_availability_family_values": "UNSET",
    "acid_parameters": "unchanged (the P2N-2 common point)",
    "k_s_r": "UNSET (P2O-1 gas-exchange values SYNTHETIC_ONLY)",
    "approved": "none",
}


def parameter_state() -> dict:
    committed = {"pulmonary_edema_58m": er.anchors().arrival_mechanics_efficiency,
                 "acs_70f_left_main": ar.anchors().arrival_mechanics_efficiency,
                 "pulmonary_embolism_61m": mr.anchors().arrival_mechanics_efficiency,
                 "pulmonary_embolism_33f": mr.anchors(mr.SECONDARY).arrival_mechanics_efficiency}
    profiles = {"default": dv.DEFAULT_PROFILE.respiratory_mechanics, "acs": ar.common_profile().respiratory_mechanics,
                "edema": pe.profile().respiratory_mechanics, "pe": em.profile().respiratory_mechanics}
    return {"status": PARAMETER_STATUS, "committed_arrival_efficiency": committed, "committed_profiles_on": profiles,
            "registry": dv.PARAMETERS["respiratory_mechanics"],
            "pass": set(committed.values()) == {1.0} and not any(profiles.values())
            and dv.DEFAULT_PROFILE.paco2_reference_mmhg == 40.0}


# P2S-2-16: default non-regression ----------------------------------------------------------------------------------------------

def p2q2_core():
    """The P2Q-2 derived.py (proven by the reversal), executed as its own module beside the live one."""
    name = "clinical_core._derived_at_p2q2"
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    exec(compile(p2q2_text("clinical_core/derived.py"), "derived_at_p2q2.py", "exec"), module.__dict__)
    return module


def _old_profile(old, profile):
    names = {f.name for f in fields(old.CoreProfile)}
    if any(getattr(profile, n) != getattr(dv.DEFAULT_PROFILE, n) for n in {f.name for f in fields(dv.CoreProfile)} - names):
        raise AssertionError("the comparison holds the P2S-2 inputs at their defaults")
    return old.CoreProfile(**{n: getattr(profile, n) for n in names})


def _same_reading(states, anchors, profile, old) -> bool:
    op = _old_profile(old, profile)
    for s in states:
        if dv.derive(s, anchors, profile).to_dict() != old.derive(s, anchors, op).to_dict():
            return False
        if dv.acid_base_active(profile) and astuple(dv.respiration(s, anchors, profile)) != astuple(
                old.respiration(s, anchors, op)):
            return False
    return dv.arrival_state(anchors, profile).to_dict() == old.arrival_state(anchors, op).to_dict()


def reference_courses() -> dict:
    """The reference courses each family froze, run by the live integrator with the candidate off."""
    gi_anchors, gi_base, values = go.ba.setup("gi_bleed_57m")
    scenario, volume = go.GI_SCENARIOS[0]
    gi_profile = go._acid(gi_base)
    return {"gi_57m": (course(go.ba.contributors("gi_bleed_57m", scenario, values, volume), 120, gi_anchors,
                              gi_profile)[0], gi_anchors, gi_profile),
            "acs": (an.course(an.writers())[0], ar.anchors(), ar.common_profile()),
            "pulmonary_edema": (pe.course((pe.writer(),))[0], er.anchors(), pe.profile()),
            "pulmonary_embolism": (em.course(em.writers())[0], mr.anchors(), em.profile()),
            "p2p2_hypoxaemic": (course((), 60, rd._hypoxaemic_anchors(), rd.hypoxaemic(rd.base_profile(),
                                                                                     rd.SYNTHETIC_GAINS[1]))[0],
                                rd._hypoxaemic_anchors(), rd.hypoxaemic(rd.base_profile(), rd.SYNTHETIC_GAINS[1]))}


NEW_ANCHOR_KEY = "arrival_mechanics_efficiency"


def without_new_anchor_key(value):
    """A closed record's view of a live section: every serialized Anchors (a dict naming its case) loses P2S-2's new
    candidate input, which must be the structural reference 1 there; anything else is compared as it is."""
    if isinstance(value, dict):
        if "case_id" in value and NEW_ANCHOR_KEY in value:
            if value[NEW_ANCHOR_KEY] != 1.0:
                raise AssertionError("a closed course read an arrival mechanics efficiency other than 1")
            value = {k: v for k, v in value.items() if k != NEW_ANCHOR_KEY}
        return {k: without_new_anchor_key(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_new_anchor_key(v) for v in value]
    return value


def non_regression() -> dict:
    """With the candidate off: the P2Q-2 core reads every reference course exactly as the live one; the records of GI,
    ACS, the oedema, P2P-2 and PE are reproduced (P2Q-2's own non-regression and its course sections); the golden differs
    only by the new registry entry (checked by the golden test)."""
    old = p2q2_core()
    courses = reference_courses()
    exact = {name: _same_reading(states, anchors, prof, old) for name, (states, anchors, prof) in courses.items()}
    mechanics_constant = {name: {s.aux.mechanics_efficiency for s in states} == {1.0}
                          for name, (states, _, _) in courses.items()}
    p2q2 = json.loads(em.RECORD.read_text(encoding="utf-8"))
    with p2q2_view():
        upstream = em.non_regression()
        sections = {name: without_new_anchor_key(em._json(build())) == p2q2[name]
                    for name, build in (("untreated", em.untreated), ("respiratory_drive", em.respiratory_drive),
                                        ("central_depression", em.central_depression), ("oxygen", em.oxygen),
                                        ("secondary", em.secondary), ("arrival", em.arrival))}
    out = {"exact_reading_p2q2_core": exact, "mechanics_constant": mechanics_constant,
           "p2q2_non_regression": {k: v for k, v in upstream.items() if k != "common_files_untouched"},
           "p2q2_common_files_untouched": all(upstream["common_files_untouched"].values()), "p2q2_sections": sections}
    out["pass"] = (all(exact.values()) and all(mechanics_constant.values()) and upstream["pass"]
                   and all(sections.values()))
    return out


# The proof: the P2Q-2 tree plus P2S-2's declared insertions ---------------------------------------------------------------------

P2Q2_HEAD = "100d541"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/respiratory_drive.py", '
                                     '"clinical_core/respiratory_drive_report.py",\n'
                                     '                        "clinical_core/embolism_migration.py", '
                                     '"clinical_core/embolism_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_mechanics.py", '
                                     '"clinical_core/respiratory_mechanics_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/respiratory_drive.py", '
                                     '"clinical_core/respiratory_drive_report.py",\n'
                                     '                        "clinical_core/embolism_migration.py", '
                                     '"clinical_core/embolism_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('AUXILIARY_SOURCES["metabolic_acid_burden"] = ACID_BASE\n'
                               "#: P2S-2: the core's composition of the families' mechanics changes into the common "
                               'respiratory mechanics efficiency\n'
                               '#: (the arrival value times every factor since). It adds no kinetics of its own. Off '
                               'unless a profile declares it.\n'
                               'RESPIRATORY_MECHANICS = Source(SourceKind.CORE_COUPLING, "respiratory_mechanics")\n'
                               'AUXILIARY_SOURCES["mechanics_efficiency"] = RESPIRATORY_MECHANICS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n',
                               'AUXILIARY_SOURCES["metabolic_acid_burden"] = ACID_BASE\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n'),
                              ('    central_drive_availability: float = 1.0\n'
                               '    # P2S-2: the common respiratory mechanics candidate, off by default (False: '
                               "every value is P2K-2's and P2P-2's). On,\n"
                               '    # it needs the acid-base physiology and the structural-reference efficiency 1, '
                               'and gives W one meaning: the effective\n'
                               '    # alveolar ventilation relative to the current metabolic ventilatory need, '
                               'derived after the RR and never read back\n'
                               '    # into it. Frequency factor = expressed RR / intrinsic RR; capacity = frequency '
                               "factor x the state's mechanics\n"
                               '    # efficiency (aux.mechanics_efficiency, family-written); W = capacity / demand '
                               'ratio; PaCO2 = paco2_reference_mmhg / W\n'
                               '    # (the PaCO2 at W = 1, never anchored to the authored arrival PaCO2). The W '
                               'channel holds no meaning there: no source\n'
                               '    # may write it (the integration refuses it) and nothing in the candidate reads '
                               'it.\n'
                               '    respiratory_mechanics: bool = False\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    central_drive_availability: float = 1.0\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('            raise CoreInvariantError("the ventilation efficiency is above 0 and at '
                               'most 1")\n'
                               '        if not isinstance(self.respiratory_mechanics, bool):\n'
                               '            raise CoreInvariantError("the respiratory mechanics candidate is on '
                               '(True) or off (False)")\n'
                               '        if self.respiratory_mechanics and (self.acid_to_drive_gain is None or '
                               'self.ventilation_efficiency != 1.0):\n'
                               '            # P2S-2: W lives in the acid-base respiration, and mechanics in one '
                               "coordinate (the state's), never two.\n"
                               '            raise CoreInvariantError("the respiratory mechanics candidate needs the '
                               'acid-base physiology and the "\n'
                               '                                     "structural-reference ventilation efficiency 1: '
                               'mechanics live in the state\'s "\n'
                               '                                     "mechanics efficiency, never also in the '
                               'profile")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n',
                               '            raise CoreInvariantError("the ventilation efficiency is above 0 and at '
                               'most 1")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n'),
                              ('                                                "in synthetic probes; no family '
                               'mapping approved"),\n'
                               '    "respiratory_mechanics": (PROVISIONAL, "STRUCTURAL_SWITCH (P2S-2): the common '
                               'respiratory mechanics candidate, off "\n'
                               '                                           "(False) by default. On: W = (expressed '
                               'RR / intrinsic RR) x the state\'s "\n'
                               '                                           "mechanics efficiency / demand ratio, and '
                               'PaCO2 = paco2_reference_mmhg / W "\n'
                               '                                           "(the PaCO2 at W = 1, '
                               'COMMON_REFERENCE_PROVISIONAL, never the authored "\n'
                               '                                           "arrival PaCO2). Mechanics efficiency 1 '
                               'is the STRUCTURAL_REFERENCE; every "\n'
                               '                                           "family mapping is UNSET; not '
                               'approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n',
                               '                                                "in synthetic probes; no family '
                               'mapping approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n'),
                              ('\n'
                               'def respiratory_mechanics_active(profile: CoreProfile) -> bool:\n'
                               '    """Whether the profile declares the P2S-2 common respiratory mechanics candidate '
                               '(it needs the acid-base physiology)."""\n'
                               '    return profile.respiratory_mechanics\n'
                               '\n'
                               '\n'
                               'def intrinsic_respiratory_rate(anchors: Anchors) -> float:\n',
                               '\ndef intrinsic_respiratory_rate(anchors: Anchors) -> float:\n'),
                              ('    the arrival ventilation at the reference efficiency (anchored, not a parameter; '
                               'eucapnic only when the authored\n'
                               '    arrival makes it so). PaCO2 and pH are None without breathing.\n'
                               '\n'
                               '    P2S-2, with the respiratory mechanics candidate on: ``efficiency`` is the '
                               "state's mechanics efficiency and\n"
                               '    ``resting_paco2`` the common reference (paco2_reference_mmhg), the PaCO2 at W = '
                               '1, read from no arrival value."""\n'
                               '\n',
                               '    the arrival ventilation at the reference efficiency (anchored, not a parameter; '
                               'eucapnic only when the authored\n'
                               '    arrival makes it so). PaCO2 and pH are None without breathing."""\n'
                               '\n'),
                              ('    No term reads lactate, D or the W channel; the ventilation feeds back into '
                               'nothing (no CO2 chemoreflex in P2K-2).\n'
                               '    ``drive`` is the excitatory drive; with the hypoxaemic drive UNSET and '
                               "availability 1 every value is P2K-2's.\n"
                               '\n'
                               '    P2S-2, with the respiratory mechanics candidate on: the same drive and RR; W = '
                               "(RR / intrinsic RR) x the state's\n"
                               '    mechanics efficiency / demand ratio (the one W formula, '
                               '``alveolar_ventilation``), and PaCO2 = the common reference\n'
                               "    / W, so the arrival mechanics are a case's latent state, never absorbed by an "
                               'arrival PaCO2 anchor; the W channel is\n'
                               '    not read. Off, a mechanics efficiency other than 1 is refused (nothing would '
                               'read it)."""\n'
                               '    if not acid_base_active(profile):\n',
                               '    No term reads lactate, D or the W channel; the ventilation feeds back into '
                               'nothing (no CO2 chemoreflex in P2K-2).\n'
                               '    ``drive`` is the excitatory drive; with the hypoxaemic drive UNSET and '
                               'availability 1 every value is P2K-2\'s."""\n'
                               '    if not acid_base_active(profile):\n'),
                              ('    demand_ratio = state.aux.oxygen_demand / anchors.metabolic_demand_baseline\n'
                               '    if respiratory_mechanics_active(profile):\n'
                               '        efficiency = state.aux.mechanics_efficiency\n'
                               '        resting = profile.paco2_reference_mmhg\n'
                               '    else:\n'
                               '        if state.aux.mechanics_efficiency != 1.0:\n'
                               '            raise CoreInvariantError(f"minute {state.minute}: a mechanics efficiency '
                               'other than 1 needs the respiratory "\n'
                               '                                     "mechanics candidate (P2S-2); nothing else '
                               'reads it")\n'
                               '        efficiency = profile.ventilation_efficiency\n'
                               '        resting = arrival_paco2(anchors, profile) * '
                               'arrival_alveolar_ventilation(anchors, profile)\n'
                               '    ventilation = alveolar_ventilation(rate, intrinsic, efficiency, demand_ratio)\n'
                               '    paco2 = resting / ventilation if ventilation > 0.0 else None\n'
                               '    return Respiration(intrinsic, burden, hco3, drive, rate, efficiency, '
                               'ventilation, resting,\n'
                               '                       paco2, None if paco2 is None else carbonic_ph(hco3, paco2))\n',
                               '    demand_ratio = state.aux.oxygen_demand / anchors.metabolic_demand_baseline\n'
                               '    ventilation = alveolar_ventilation(rate, intrinsic, '
                               'profile.ventilation_efficiency, demand_ratio)\n'
                               '    resting = arrival_paco2(anchors, profile) * '
                               'arrival_alveolar_ventilation(anchors, profile)\n'
                               '    paco2 = resting / ventilation if ventilation > 0.0 else None\n'
                               '    return Respiration(intrinsic, burden, hco3, drive, rate, '
                               'profile.ventilation_efficiency, ventilation, resting,\n'
                               '                       paco2, None if paco2 is None else carbonic_ph(hco3, '
                               'paco2))\n'),
                              ('    """\n'
                               '    if anchors.arrival_mechanics_efficiency != 1.0 and not '
                               'respiratory_mechanics_active(profile):\n'
                               '        raise CoreInvariantError("an arrival mechanics efficiency other than 1 needs '
                               'the respiratory mechanics candidate "\n'
                               '                                 "(P2S-2); nothing else reads it")\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n',
                               '    """\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n'),
                              ('                                            sympathetic_drive=0.0, '
                               'oxygen_demand=anchors.metabolic_demand_baseline,\n'
                               '                                            '
                               'metabolic_acid_burden=arrival_acid_burden(anchors, profile),\n'
                               '                                            '
                               'mechanics_efficiency=anchors.arrival_mechanics_efficiency))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n',
                               '                                            sympathetic_drive=0.0, '
                               'oxygen_demand=anchors.metabolic_demand_baseline,\n'
                               '                                            '
                               'metabolic_acid_burden=arrival_acid_burden(anchors, profile)))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n')),
 'clinical_core/integration.py': (('                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n',
                                   '                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n'),
                                  ('    blood: tuple[BloodFlow, ...] = ()        # what enters or leaves the '
                                   'circulation this minute (P2I-2T)\n'
                                   '    mechanics: tuple[MechanicsChange, ...] = ()  # changes to the respiratory '
                                   'mechanics efficiency this minute (P2S-2)\n'
                                   '\n',
                                   '    blood: tuple[BloodFlow, ...] = ()        # what enters or leaves the '
                                   'circulation this minute (P2I-2T)\n'
                                   '\n'),
                                  ('        raise ProvenanceError(f"{contributor.source.key}: the circulation '
                                   'changes only by a tuple of BloodFlow records")\n'
                                   '    if not isinstance(contribution.mechanics, tuple) or any(not isinstance(item, '
                                   'MechanicsChange)\n'
                                   '                                                            for item in '
                                   'contribution.mechanics):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the respiratory '
                                   'mechanics efficiency changes only by a tuple "\n'
                                   '                              "of MechanicsChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n',
                                   '        raise ProvenanceError(f"{contributor.source.key}: the circulation '
                                   'changes only by a tuple of BloodFlow records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n'),
                                  ('    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics):\n'
                                   '        if item.source != contributor.source:\n',
                                   '    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood):\n'
                                   '        if item.source != contributor.source:\n'),
                                  ('                                   "lung water above arrival clearing slowly"))\n'
                                   '    transitions, settings, events, modifiers, flows, mechanics = [], [], [], [], '
                                   '[], []\n'
                                   '    internal = {}\n',
                                   '                                   "lung water above arrival clearing slowly"))\n'
                                   '    transitions, settings, events, modifiers, flows = [], [], [], [], []\n'
                                   '    internal = {}\n'),
                                  ('        flows.extend(contribution.blood)\n'
                                   '        mechanics.extend(contribution.mechanics)\n'
                                   '        if contribution.internal is not None:\n'
                                   '            internal[contributor.source.key] = contribution.internal\n'
                                   '    if respiratory_mechanics_active(profile) and any(delta.channel is Channel.W '
                                   'for delta in deltas):\n'
                                   '        # P2S-2: W is derived in the respiratory mechanics candidate; the W '
                                   'channel holds no meaning there.\n'
                                   '        raise ProvenanceError(f"minute {minute}: the W channel was written while '
                                   'the respiratory mechanics candidate is "\n'
                                   '                              "on (P2S-2): W is derived from the RR, the '
                                   'mechanics efficiency and the demand")\n'
                                   '    # V and Hb written directly this minute: only a scripted probe may '
                                   '(``_check_owned``).\n',
                                   '        flows.extend(contribution.blood)\n'
                                   '        if contribution.internal is not None:\n'
                                   '            internal[contributor.source.key] = contribution.internal\n'
                                   '    # V and Hb written directly this minute: only a scripted probe may '
                                   '(``_check_owned``).\n'),
                                  ('    # demand (its acute deficit signal), so the demand is set before the drive '
                                   'is.\n'
                                   '    if mechanics and not respiratory_mechanics_active(profile):\n'
                                   '        # P2S-2: with the candidate off nothing reads the mechanics efficiency; '
                                   'a change would be silently inert.\n'
                                   '        raise ProvenanceError(f"minute {minute}: {mechanics[0].source.key} '
                                   'changed the respiratory mechanics efficiency "\n'
                                   '                              "while the respiratory mechanics candidate is off '
                                   '(P2S-2)")\n'
                                   '    # P2S-2: the mechanics efficiency stays where its writers leave it: the '
                                   "minute's factors compose on the value the\n"
                                   '    # minute starts with, and the core adds no kinetics of its own.\n'
                                   '    aux = AuxiliaryState(lactate_excess_mmol_l=lactate_after_minute(state, '
                                   'profile),\n'
                                   '                         sympathetic_drive=state.aux.sympathetic_drive, '
                                   'oxygen_demand=demand, collapse_burden=burden,\n'
                                   '                         metabolic_acid_burden=_acid_burden(state, anchors, '
                                   'profile, demand),\n'
                                   '                         mechanics_efficiency=state.aux.mechanics_efficiency * '
                                   'math.prod(item.factor\n'
                                   '                                                                                         '
                                   'for item in mechanics))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n',
                                   '    # demand (its acute deficit signal), so the demand is set before the drive '
                                   'is.\n'
                                   '    aux = AuxiliaryState(lactate_excess_mmol_l=lactate_after_minute(state, '
                                   'profile),\n'
                                   '                         sympathetic_drive=state.aux.sympathetic_drive, '
                                   'oxygen_demand=demand, collapse_burden=burden,\n'
                                   '                         metabolic_acid_burden=_acid_burden(state, anchors, '
                                   'profile, demand))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n'),
                                  ('                          settings=tuple(settings), events=tuple(events), '
                                   'internal_updates=tuple(sorted(internal)),\n'
                                   '                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics))\n'
                                   '    _check_conservation(state, new_state, record)\n',
                                   '                          settings=tuple(settings), events=tuple(events), '
                                   'internal_updates=tuple(sorted(internal)),\n'
                                   '                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes)\n'
                                   '    _check_conservation(state, new_state, record)\n'),
                                  ('            raise ProvenanceError(f"auxiliary {name} changed without a record of '
                                   'the change")\n'
                                   '    if after.aux.mechanics_efficiency != before.aux.mechanics_efficiency * '
                                   'math.prod(item.factor\n'
                                   '                                                                                   '
                                   'for item in record.mechanics):\n'
                                   "        # P2S-2: the mechanics efficiency moves by exactly the minute's recorded "
                                   'changes, never otherwise.\n'
                                   '        raise ProvenanceError("the respiratory mechanics efficiency changed by '
                                   'other than its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n',
                                   '            raise ProvenanceError(f"auxiliary {name} changed without a record of '
                                   'the change")\n'
                                   '    for channel in SCALAR_CHANNELS:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/respiratory_drive_report.py",\n'
                                     '                      "clinical_core/embolism_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_mechanics_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/respiratory_drive_report.py",\n'
                                     '                      "clinical_core/embolism_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class MechanicsChange:\n'
                                  '    """P2S-2: one source\'s change to the common respiratory mechanics efficiency '
                                  'in one minute.\n'
                                  '\n'
                                  '    The factor multiplies the efficiency the minute starts with (above 0; 1 '
                                  'changes nothing), so the efficiency stays\n'
                                  '    where its writers leave it: it never moves, back to arrival or anywhere else, '
                                  'without a change that names its\n'
                                  '    source. The efficiency is a common coordinate, never a disease term: a family '
                                  'declares what its own mechanism does\n'
                                  '    to it, and the core only composes the factors. No factor is approved; with '
                                  'the mechanics candidate off a change is\n'
                                  '    refused, because nothing would read it.\n'
                                  '    """\n'
                                  '\n'
                                  '    factor: float\n'
                                  '    source: Source\n'
                                  '    minute: int\n'
                                  '    description: str\n'
                                  '\n'
                                  '    def __post_init__(self):\n'
                                  '        if isinstance(self.factor, bool) or not isinstance(self.factor, (int, '
                                  'float)) \\\n'
                                  '                or not math.isfinite(self.factor) or self.factor <= 0:\n'
                                  '            raise ProvenanceError(f"a mechanics factor is a finite positive '
                                  'number, not {self.factor!r}")\n'
                                  '        object.__setattr__(self, "factor", float(self.factor))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every mechanics change names its Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "mechanics", "factor": self.factor, "source": '
                                  'self.source.to_dict(), "minute": self.minute,\n'
                                  '                "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AuxiliaryChange:\n',
                                  '@dataclass(frozen=True)\nclass AuxiliaryChange:\n'),
                                 ('    blood: tuple[BloodChange, ...] = field(default=())\n'
                                  '    mechanics: tuple[MechanicsChange, ...] = field(default=())\n'
                                  '\n',
                                  '    blood: tuple[BloodChange, ...] = field(default=())\n\n'),
                                 ('        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics):\n'
                                  '            if item.minute != self.minute:\n',
                                  '        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood):\n'
                                  '            if item.minute != self.minute:\n'),
                                 ('                "demand": [item.to_dict() for item in self.demand],\n'
                                  '                "blood": [item.to_dict() for item in self.blood],\n'
                                  '                "mechanics": [item.to_dict() for item in self.mechanics]}\n'
                                  '\n',
                                  '                "demand": [item.to_dict() for item in self.demand],\n'
                                  '                "blood": [item.to_dict() for item in self.blood]}\n'
                                  '\n')),
 'clinical_core/state.py': (('    "arrival_dynamic_state": ("preload_fraction", "arrival_oxygen_debt", '
                             '"arrival_lactate_excess",\n'
                             '                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2",\n'
                             '                              "arrival_mechanics_efficiency"),\n'
                             '}\n',
                             '    "arrival_dynamic_state": ("preload_fraction", "arrival_oxygen_debt", '
                             '"arrival_lactate_excess",\n'
                             '                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2"),\n'
                             '}\n'),
                            ('    reversible_lung_water: float = 0.0\n'
                             '    # P2S-2 candidate input, read only by the common respiratory mechanics candidate '
                             '(off by default) and outside the\n'
                             '    # case-parameter / migration registry until the faculty adopts that physiology, as '
                             "P2K-2's: the arrival respiratory\n"
                             '    # mechanics efficiency, a case / family latent arrival state (never read from the '
                             'disease label), above 0 with no\n'
                             '    # upper bound. 1, the default, is the structural reference; no other value is '
                             'approved.\n'
                             '    arrival_mechanics_efficiency: float = 1.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    reversible_lung_water: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the reversible lung water is at or below arrival '
                             '(L_rev <= 0, P2O-3)")\n'
                             '        if not self.arrival_mechanics_efficiency > 0.0:\n'
                             '            raise CoreInvariantError("the arrival respiratory mechanics efficiency is '
                             'above 0 (P2S-2)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the reversible lung water is at or below arrival '
                             '(L_rev <= 0, P2O-3)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'),
                            ('                             "clearance (P2K-2); not lactate, D or pH; constant while '
                             'the acid-base physiology is off",\n'
                             '    "mechanics_efficiency": "the common respiratory mechanics efficiency (P2S-2): the '
                             'effective alveolar ventilation one "\n'
                             '                            "breath at the intrinsic-RR frequency moves, relative to '
                             'the structural reference 1, above "\n'
                             '                            "0 with no upper bound; the case\'s latent arrival value '
                             'times every family change since "\n'
                             '                            "(provenance.MechanicsChange); not drive, central '
                             'depression, RR, G or L; 1 and constant "\n'
                             '                            "while the mechanics candidate is off",\n'
                             '}\n',
                             '                             "clearance (P2K-2); not lactate, D or pH; constant while '
                             'the acid-base physiology is off",\n'
                             '}\n'),
                            ('    metabolic_acid_burden: float = 0.0\n    mechanics_efficiency: float = 1.0\n\n',
                             '    metabolic_acid_burden: float = 0.0\n\n'),
                            ('            raise CoreInvariantError("the metabolic acid burden is never negative")\n'
                             '        if not self.mechanics_efficiency > 0:\n'
                             '            # P2S-2: the domain is above 0 only; 1 is the structural reference, not a '
                             'ceiling.\n'
                             '            raise CoreInvariantError("the respiratory mechanics efficiency is above '
                             '0")\n'
                             '\n',
                             '            raise CoreInvariantError("the metabolic acid burden is never negative")\n'
                             '\n'))}
CORE_AT_P2Q2 = {'clinical_core/decision_pack.py': '6937b6e427a4340b0fe6519eea7a5422f38a052870ba300d53d8eaf6d75c8da8',
 'clinical_core/derived.py': 'e701e99bfa4a2ad2e1d17a7408d91b566abf6d76fa7da1678213c54db0ecbedb',
 'clinical_core/integration.py': 'c725fbe8ab4daa69952dfd06a8f584e303ef6ff66bd67441deaa70e4cce887af',
 'clinical_core/lactate_slice.py': 'a113894726dea752b99de300adf4e78372bd34c03bf10ea4632121934ee07f6c',
 'clinical_core/provenance.py': '3e670fc4aebb296232e8418f448cb14f6da46c387d4af4fc2ae7b95ba1e328d8',
 'clinical_core/state.py': '141cd5a2aada89a58e7de9ee1436b2f52fd68141df132bcb26e934e6e9ddc7d1'}
# </reversal>
# <common>
COMMON_AT_P2Q2 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
 'clinical_core/a9.py': '64006b57e37ab69dd9dfd61d5c87b01112779f19e7007b96440cfad345ad5b92',
 'clinical_core/acid_base.py': '9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954',
 'clinical_core/acid_base_report.py': '9f0b9f5b03369066e4ac7916b372453c41ef7793b36c20553b88d726b83afa78',
 'clinical_core/acs_migration.py': '4fae25400e94b7c1f3b6b77f277dd5e04b72d150c52da738faddf95b37edd971',
 'clinical_core/acs_migration_report.py': 'dbe33c01e165f9471dcb720919c3fac257f3d0903972117a420e91632b4c2d6b',
 'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/arrival_severity.py': 'c5c0e4c125303b463ec1d2a5373464c09576f7d83ca975834e6b059c67b2b229',
 'clinical_core/arrival_severity_report.py': 'a1806dc772a4f0a540a621271e8dd24b4c77b36da2b55af5e1da623cf30ac2eb',
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
 'clinical_core/modules/gi_haemorrhage.py': 'edb61d903bc9f4607c1d3b819f28ac065ba86656b75ba29c89d3a7c124777673',
 'clinical_core/modules/pulmonary_edema.py': '01e68556c919efa24ff6186eacf22c98e2ec882bf5cd52109bbafaffd8351679',
 'clinical_core/modules/pulmonary_embolism.py': '147881394c9208b35e2e2fdb7bb0ab42d589785000784379a8b1c1460df204c7',
 'clinical_core/modules/rhythm_events.py': '1036a2443e44fe5e2fde80736984b6828542b69454cc49a36e660ee8d436c86b',
 'clinical_core/oxygen_probes.py': '450cec663ae0c47ba32b6df8b4fadc136cad6c9a2e14f8f08d649d166651febd',
 'clinical_core/pressure_tone.py': '2e350c8a42bcacfa31e8e5349d284c7d276808e396d36421e1dc369dbcb9ec26',
 'clinical_core/pressure_tone_filter.py': '54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650',
 'clinical_core/pressure_tone_filter_report.py': '6eebe11b816eeb901f10d9f1431182b71ab26db84652771af741076f33734f92',
 'clinical_core/pressure_tone_report.py': 'bc0fe73c681a35432baec5acf8062027b63f0e5821146133fb9211ae9240d7ac',
 'clinical_core/respiratory_drive.py': '246f4ad5070fb50a64eec686ee4441e896d79c6d717303e1a43c11f7bf5af21b',
 'clinical_core/respiratory_drive_report.py': '7bb2ee04e3204b4de2bf542cac2f8166d72de7af4892cc7f098699f5adc94f2a',
 'clinical_core/respiratory_monotonicity.py': 'ba6bac3ea1f4f1f9b0bff5503b4ff846f1ae5a097ee88d8480dd3ee52fbba672',
 'clinical_core/respiratory_monotonicity_report.py': '373cdac40c02f1e0bd4683f9ab6329ce08805b4a41e38939e89ff28a8fc83fcb',
 'clinical_core/rr_audit.py': '4b663ffad81ff88f728707e7c96a255d882cbf62247107980652331fff885bf1',
 'clinical_core/rr_audit_report.py': 'f3951b39f4b0b9d6b82a6fffa687457f68257743e6e86fb4d5c10c0dc81797e5',
 'clinical_core/shadow.py': '66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35',
 'clinical_core/signals.py': 'f02f5494a8aac0361ace94a40e15a4df81970f456de7af0f6762a1196a27ee7f',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>
P2Q2_FREEZE_DIGEST = "6eabb72188b5aa9e8b6c0c17f9234fbf1ce5413cc01841a58a33ca79da797e6e"
P2Q2_RECORD_SHA = "bc743e79bfe3bee845dc56411089993b5da091e4a1a2ce4fb31447afbc4f9ada"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2Q2[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2Q2.items()}


def p2q2_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2Q-2 file plus P2S-2's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2q2_bytes(relative: str) -> bytes:
    return p2q2_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2q2_sources(sources: dict) -> dict:
    """A P2Q-2 dependency map: P2S-2's files removed, each changed file at its P2Q-2 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2Q2.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def _p2q2_common_untouched() -> dict:
    return {relative: hashlib.sha256(p2q2_bytes(relative)).hexdigest() == sha
            for relative, sha in em.COMMON_AT_P2P2.items()}


def _p2p2_bytes(relative: str) -> bytes:
    return em.p2p2_text(relative).encode("utf-8") if relative in em.REVERSAL else p2q2_bytes(relative)


def _p2p1_bytes(relative: str) -> bytes:
    return rd.p2p1_text(relative).encode("utf-8") if relative in rd.REVERSAL else _p2p2_bytes(relative)


def _p2p2_common_untouched_of_p2p1() -> dict:
    return {relative: hashlib.sha256(_p2p2_bytes(relative)).hexdigest() == sha
            for relative, sha in rd.COMMON_AT_P2P1.items()}


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2Q-2's view reads the P2Q-2 files (proven), so every closed guard still
    reads the core it froze. P2Q-2 changed no common file, so its own chain left P2P-2's direct byte reads (its common
    files and the bytes behind P2P-1's view) on the live tree; they now read the P2Q-2 bytes too."""
    patch.setattr(em, "_live", p2q2_text)
    patch.setattr(em, "common_untouched", _p2q2_common_untouched)
    patch.setattr(em, "p2p2_bytes", _p2p2_bytes)
    patch.setattr(rd, "common_untouched", _p2p2_common_untouched_of_p2p1)
    patch.setattr(rd, "p2p1_bytes", _p2p1_bytes)


class _Patch:
    def __init__(self):
        self._undo = []

    def setattr(self, target, name, value):
        self._undo.append((target, name, getattr(target, name)))
        setattr(target, name, value)

    def undo(self):
        while self._undo:
            target, name, value = self._undo.pop()
            setattr(target, name, value)


_FREEZE_SOURCES = bf.freeze_sources


class p2q2_view:
    """P2Q-2's analysis reading the tree P2Q-2 froze (its sources and its common files), for its own proofs."""

    def __enter__(self):
        self._patch = _Patch()
        chain(self._patch)
        self._patch.setattr(bf, "freeze_sources", lambda: p2q2_sources(_FREEZE_SOURCES()))
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2q2_view():
        p2q2_digest = em.freeze_digest()
        p2q2_proof = em.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(), "p2q2_common_untouched": _p2q2_common_untouched(),
            "p2q2_freeze_digest": p2q2_digest == P2Q2_FREEZE_DIGEST,
            "p2q2_proof": p2q2_proof["p2p2_freeze_digest"] and p2q2_proof["p2p2_record"] and all(
                p2q2_proof["proofs"].values()),
            "p2q2_record": hashlib.sha256(em.RECORD.read_bytes()).hexdigest() == P2Q2_RECORD_SHA}


# P2S-2-19: readiness (predeclared) ------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "RR and mechanics are distinct (M5, M6, M10; the drive reads no mechanics; the mechanics read no drive)",
    "both contribute to W (M1, M2, M3, M5; the directions, demand included; the faculty's form reproduced)",
    "W has one meaning (W channel writes refused and the channel inert, RR never read from W, W after RR; P2K-1 "
    "retired from the candidate)",
    "high RR / high PaCO2 representable (M3; oedema 58m and asthma 49m; availability 1)",
    "low RR / high PaCO2 representable (M4, M9; the opioid contrast)",
    "central depression remains distinct from mechanics (the opioid contrast; M10, M11, M12)",
    "arrival PaCO2 not hidden in a case-specific reference anchor (no anchor absorption; arrival ordering coherent)",
    "default prior behaviour unchanged (exact P2Q-2 reading; GI, ACS, oedema, PE and P2P-2 reproduced; the P2Q-2 tree "
    "proven)",
    "no clinical mechanics value approved (no family writer; committed arrivals at the reference; parameter state)",
)
READY = "COMMON_RESPIRATORY_MECHANICS_ARCHITECTURE_READY"
NOT_READY = "COMMON_RESPIRATORY_MECHANICS_ARCHITECTURE_NOT_READY"
READINESS_RULE = ("Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion as "
                  "the blocker. An incoherent arrival ordering (P2S-2-11) is a STOP: it fails the seventh criterion. The "
                  "region overlaps, the frequency-factor linearity and the HR gap are reported and never decide it")
RECOMMENDATION = {READY: "PROCEED_TO_ASTHMA_SHADOW_MIGRATION (no numerical mechanics calibration before it; the family "
                         "provides the mechanics writer and its arrival mapping, after availability and the excitatory "
                         "drive)"}


def readiness(found: dict) -> dict:
    p, proof = found["probes"]["pass"], found["proof"]
    values = (
        p["M5"] and p["M6"] and p["M10"] and found["audit"]["pass"],
        p["M2"] and p["M3"] and p["M5"] and p["M1"] and found["directions"]["pass"],
        found["w_uniqueness"]["pass"] and p["M7"] and p["M8"],
        p["M3"] and found["high_rr_high_paco2"]["pass"] and found["compensated"]["pass"],
        p["M4"] and p["M9"] and found["opioid"]["pass"],
        found["opioid"]["pass"] and p["M10"] and p["M11"] and p["M12"],
        found["no_anchor_absorption"]["pass"] and found["arrival_regions"]["coherent"],
        found["non_regression"]["pass"] and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and all(proof["p2q2_common_untouched"].values()) and proof["p2q2_freeze_digest"] and proof["p2q2_proof"]
        and proof["p2q2_record"],
        found["interface"]["pass"] and found["parameter_state"]["pass"] and found["no_extra_state"]["pass"]
        and found["oxygenation"]["pass"] and found["heart_rate"]["pass"] and found["respiratory_load"]["pass"],
    )
    criteria = dict(zip(READINESS_CRITERIA, values))
    blocker = next((name for name, ok in criteria.items() if not ok), None)
    return {"criteria": criteria, "ready": blocker is None, "blocker": blocker,
            "verdict": READY if blocker is None else f"{NOT_READY} — {blocker}",
            "recommendation": RECOMMENDATION[READY] if blocker is None else None}


# Freeze and record ---------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "decisions": DECISIONS, "paths": PATHS, "semantics": SEMANTICS,
            "dimensions": DIMENSIONS, "interface": INTERFACE, "probes": PROBES,
            "synthetic": {"efficiencies": list(SYNTHETIC_EFFICIENCIES), "demand_ratios": list(DEMAND_RATIOS), "low": LOW_EFFICIENCY, "mild": MILD_EFFICIENCY,
                          "availabilities": list(AVAILABILITIES), "depressed": DEPRESSED,
                          "bicarbonates": list(BICARBONATES), "strong_drive": STRONG_DRIVE,
                          "hypoxaemic_spo2s": list(HYPOXAEMIC_SPO2S), "hypoxaemic_gain": HYPOXAEMIC_GAIN,
                          "hypoxaemic_mapping": [list(p) for p in rd.SYNTHETIC_MAPPING],
                          "mechanics_factor": MECHANICS_FACTOR, "course_minutes": COURSE_MINUTES, "g_per_min": G_PER_MIN,
                          "l_per_min": L_PER_MIN, "intrinsic_rr": list(INTRINSIC_RR),
                          "demand_sensitivity": list(DEMAND_SENSITIVITY)},
            "cases": {"high_rr": list(HIGH_RR_CASES), "compensated": COMPENSATED_CASE, "opioid": OPIOID_CASE,
                      "diagnostic": list(DIAGNOSTIC_CASES), "severe": list(SEVERE), "references": list(REFERENCES),
                      "informative": list(INFORMATIVE)},
            "truth_paths": {k: list(v) for k, v in TRUTH_PATHS.items()}, "ordering_rule": ORDERING_RULE,
            "candidate_inputs": list(CANDIDATE_INPUTS),
            "forbidden_names": list(FORBIDDEN_NAMES), "parameter_status": PARAMETER_STATUS,
            "readiness_criteria": list(READINESS_CRITERIA), "readiness_rule": READINESS_RULE,
            "recommendation": RECOMMENDATION, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2q2": CORE_AT_P2Q2,
            "common_at_p2q2": COMMON_AT_P2Q2,
            "p2q2": {"head": P2Q2_HEAD, "freeze_digest": P2Q2_FREEZE_DIGEST, "record": P2Q2_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2q2": hashlib.sha256(em.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "probes": structural_probes(), "directions": directions(),
             "interface": interface(),
             "high_rr_high_paco2": high_rr_high_paco2(), "compensated": compensated_contrast(),
             "opioid": opioid_contrast(), "arrival_regions": arrival_regions(),
             "no_anchor_absorption": no_anchor_absorption(), "no_extra_state": no_extra_state(),
             "w_uniqueness": w_uniqueness(), "respiratory_load": respiratory_load_signal(),
             "heart_rate": heart_rate(), "parameter_state": parameter_state(), "non_regression": non_regression()}
    found["oxygenation"] = oxygenation_deferred(found["probes"]["probes"]["M10"])
    found["readiness"] = readiness(found)
    return go._plain({"freeze_digest": freeze_digest(), "revision": REVISION, "design": design(), **found})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    data = run()
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
