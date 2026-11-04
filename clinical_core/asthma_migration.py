"""P2S-3: asthma_49m (primary) and asthma_24f (secondary) migrated in shadow with a family mechanics writer, on the
unchanged common core with the P2S-2 respiratory mechanics candidate on.

    python -m clinical_core.asthma_migration [--digest] [--out <json>]

A family migration, not a common-core cycle. It tests whether asthma enters the closed common respiratory architecture
through a clean family writer: airflow obstruction -> the common mechanics efficiency -> W -> PaCO2, with every other
consequence (RR, pH, SpO2 and its FiO2 response, delivery, D, lactate, HR, consciousness, collapse) common. The arrival
mechanics efficiency is a FAMILY_CANDIDATE region read from the authored RR and PaCO2 with the carried intrinsic RR
(asthma_reference); the worsening rate is a SYNTHETIC_ONLY span on a scale already frozen (the ACS writer's, as a
fraction per hour); the P2P-2 drive is unchanged (hypoxaemic mapping UNSET, availability 1); no bronchodilator, steroid,
direct-G, fatigue, alveolar-gas or HR term is added. The legacy engine is read last, as reference only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import fields, replace
from pathlib import Path

from . import acs_migration as an
from . import acs_reference as ar
from . import asthma_reference as sr
from . import blood_fluid_calibration as bf
from . import collapse as cx
from . import derived as dv
from . import edema_migration as pe
from . import embolism_migration as em
from . import gas_exchange_architecture as go
from . import lung_water_reference as lw
from . import respiratory_drive as rd
from . import respiratory_mechanics as mc
from .integration import step
from .interventions.oxygen import Oxygen
from .modules.asthma import AirwayObstruction
from .provenance import ProvenanceError
from .state import Channel, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2S-3"
DECIDED = "2026-11-04"
OWN = ("clinical_core/asthma_reference.py", "clinical_core/modules/asthma.py", "clinical_core/asthma_migration.py")
REPORT = "clinical_core/asthma_migration_report.py"
RECORD = ROOT / "docs" / "revision" / "P2S3_asthma_migration.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2S3_ASMA_SOMBRA.md"
#: The tuples P2S-3 extended (its analysis and report are downstream of every numerical artifact).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[2], REPORT)}
FAMILY_FILE = "clinical_core/modules/asthma.py"
#: The family's own type (registered by importing the module); the closed packages' registry view leaves it out.
FAMILY_TYPES = (AirwayObstruction.type_name,)


# The faculty's decisions (fixed) ---------------------------------------------------------------------------------------------

DECISIONS = {
    "FAMILY_MIGRATION_ONLY": "no common-core change or retuning (intrinsic RR bands, acid and hypoxaemic gains, the "
                             "mechanics equation, the PaCO2 reference, G -> SpO2, D / lactate, HR, consciousness, "
                             "collapse); a true common-core need is COMMON_CORE_BLOCKER_FOUND",
    "MECHANICS_WRITER": "the family's airflow obstruction writes the common mechanics efficiency only; RR, PaCO2, SpO2, G, "
                        "DO2, D, lactate, HR and consciousness follow in the common core",
    "ARRIVAL_MECHANICS": "FAMILY_CANDIDATE / LATENT_ARRIVAL_STATE: a small region predeclared from the authored RR, PaCO2 "
                         "and the carried intrinsic RR, never one value chosen for reconstruction; none approved",
    "CONTRAST": "49m (high RR, high PaCO2, severe WOB, poor air entry, drowsy) and 24f (high RR, low PaCO2, compensated) "
                "differ by family mechanics severity only, never by a different common equation",
    "DIRECT_G": "optional, on the existing G interface, never L or L_rev; hypoventilatory hypoxaemia is not forced into G",
    "OXYGENATION_LINK": "HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED: PaCO2 may be right while part of the hypoxaemia "
                        "stays unexplained (EXPECTED_ALVEOLAR_GAS_EXTENSION)",
    "DRIVE": "P2P-2 unchanged: no asthma drive residual; the hypoxaemic mapping UNSET; no gain fitted to the asthma RR",
    "AVAILABILITY": "central drive availability 1: the hypercapnia is mechanics, never a reduced availability",
    "BRONCHODILATOR": "only if required and an existing treatment action exists; it would target the mechanics, never "
                      "script RR, PaCO2, SpO2 or HR",
    "STEROID": "STEROID_ACUTE_PHYSIOLOGY_DEFERRED", "OXYGEN": "the common FiO2 pathway; no asthma O2 response",
    "HR": "HR_GAP_DISTRESS_AROUSAL_DOMINANT untouched: no sympathetic input, no beta-agonist HR model",
    "CONSCIOUSNESS": "P2L-2 not integrated; 49m only diagnostic for hypercapnia; the legacy ladder never a target",
    "COLLAPSE": "structural only; no threshold, no asthma rule", "LEGACY": "read last; never a target",
}
TRUTH_CLASSES = {k: "AUTHORED_CASE_TRUTH" for k in sr.TRUTH_PATHS}
LEGACY_CONSTANTS = ("asthma: obstruction +0.002 per minute, exhaustion tracking, bronchodilator / magnesium / epinephrine "
                    "/ ketamine bronchodilation, beta side effects, oxygen shunt 0.30 (family_engine, asthma_complications): "
                    "LEGACY_ENGINE_BEHAVIOR")
MODEL_DERIVED = ("the expressed RR, W, PaCO2 and pH (the P2S-2 candidate), the predicted HR, the delivery and the "
                 "deficit, read from the common core at the mapped arrival")
LATER_OBSERVATIONS = ("NONE_AUTHORED: both cases state the arrival only; no peak flow, gas or vital sign after any "
                      "treatment is authored")


def case() -> dict:
    out = {"cases": {}, "selection_rule": sr.SELECTION_RULE, "source": "clinical_cases.py",
           "legacy_constants": LEGACY_CONSTANTS, "model_derived": MODEL_DERIVED, "later_observations": LATER_OBSERVATIONS}
    for name in sr.CASES:
        t = sr.truth(name)
        out["cases"][name] = {"truth": t, "peak_flow": sr.peak_flow(t), "classes": {k: TRUTH_CLASSES[k] for k in t},
                              "missing": sorted(k for k, v in t.items() if v is None),
                              "map": sr.authored_map(t)}
    out["available"] = all(not v["missing"] for v in out["cases"].values())
    return out


# The design (predeclared before any run) -------------------------------------------------------------------------------------

#: The obstruction's worsening: the ACS ischaemic writer's frozen span (acs_migration.LOSS_PER_MIN, 0.05 / 0.10 / 0.20 per
#: hour) read as the fraction of the mechanics efficiency lost per hour, and none. SYNTHETIC_ONLY; nothing authored after
#: arrival to fit.
WORSENING_PER_MIN = (0.0,) + tuple(an.LOSS_PER_MIN)
MID_WORSENING = an.LOSS_PER_MIN[1]
HORIZON = an.HORIZON
READ = (0, 30, 60, 90, 120)
POINTS = ("lower", "midpoint", "upper")
FIO2 = em.FIO2
#: A structural mechanics relief through the P2S-2 probe writer (no bronchodilator writer): 1 % per minute over a declared
#: window, SYNTHETIC_ONLY.
RELIEF = {"factor_per_min": 1.01, "from_minute": 30, "to_minute": 60}
HYPOXAEMIC_GAIN = rd.SYNTHETIC_GAINS[1]
#: Textbook constants used only to read the authored gas as a diagnostic (never a core path): barometric pressure, water
#: vapour, respiratory quotient.
DIAGNOSTIC_GAS = {"barometric_mmhg": 760.0, "water_vapour_mmhg": 47.0, "respiratory_quotient": 0.8}


def profile(**changes) -> dv.CoreProfile:
    """The asthma reference profile (the ACS common point, the mechanics candidate on) with P2O-1's SYNTHETIC_ONLY
    gas-exchange reference (k 1, s 5, r 0.5), as for the oedema and PE migrations."""
    return go.gas_profile(sr.common_profile(), **changes)


def obstruction(rate: float = MID_WORSENING) -> AirwayObstruction:
    return AirwayObstruction("asthma-obstruction", rate)


def course(items, minutes: int = HORIZON, anchors=None, prof=None, start=None):
    anchors = sr.anchors() if anchors is None else anchors
    prof = profile() if prof is None else prof
    return an.course(tuple(items), minutes, anchors, prof, start)


def reading(state, anchors, prof) -> dict:
    d = dv.derive(state, anchors, prof)
    b = mc.breakdown(state, anchors, prof)
    return {"minute": state.minute, "mechanics_efficiency": state.aux.mechanics_efficiency, "rr": b["rr"],
            "frequency_factor": b["frequency_factor"], "W": b["W"], "paco2": b["paco2"], "ph": b["ph"], "G": state.G,
            "L": state.L, "spo2": d.spo2, "delivery_index": dv.effective_delivery(d.delivery_rel, anchors), "D": state.D,
            "lactate": d.lactate, "hr": d.monitor_rate_bpm, "map": d.map, "consciousness_level": d.consciousness_level,
            "availability": b["availability"], "excitatory_drive": b["excitatory_drive"]}


def _rows(states, anchors, prof) -> dict:
    return {str(m): reading(states[m], anchors, prof) for m in READ if m < len(states)}


def _decreasing(values) -> bool:
    return all(b < a for a, b in zip(values, values[1:]))


def _increasing(values) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


# P2S-3-3 / P2S-3-16: the arrival ---------------------------------------------------------------------------------------------

def arrival() -> dict:
    out = {"cases": {}, "classes": sr.ARRIVAL_CLASSES, "channel_roles": sr.CHANNEL_ROLES,
           "observation_layer": sr.OBSERVATION_LAYER}
    prof = profile()
    for name in sr.CASES:
        t = sr.truth(name)
        band = sr.mechanics_band(name)
        rows = {}
        for point in POINTS:
            a = sr.anchors(name, point)
            s = dv.arrival_state(a, prof)
            r = reading(s, a, prof)
            conditional = mc.analytic_paco2(float(t["respiratory_rate"]), a.intrinsic_respiratory_rate,
                                            a.arrival_mechanics_efficiency)
            rows[point] = {**r, "intrinsic_rr": a.intrinsic_respiratory_rate,
                           "rr_gap": r["rr"] - float(t["respiratory_rate"]),
                           "paco2_bias": r["paco2"] - float(t["abg_paco2"]),
                           "bias_is_the_rr_ratio": math.isclose(r["paco2"], float(t["abg_paco2"])
                                                                * float(t["respiratory_rate"]) / r["rr"], rel_tol=1e-9),
                           "paco2_at_authored_rr": conditional,
                           "exact": {"sbp": dv.derive(s, a, prof).sbp == float(t["sbp"]),
                                     "spo2": r["spo2"] == float(t["spo2"]),
                                     "consciousness_level": r["consciousness_level"] == sr.LEVEL_OF[t["mental_status"]],
                                     "lactate": math.isclose(r["lactate"], float(t["lactate_mmol_l"]), rel_tol=1e-9)}}
        out["cases"][name] = {"band": {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper,
                                       "classification": band.classification, "rule": band.rule},
                              "authored": {"rr": t["respiratory_rate"], "paco2": t["abg_paco2"], "ph": t["abg_ph"],
                                           "spo2": t["spo2"], "hr": t["hr"], "wob": t["work_of_breathing"],
                                           "mental_status": t["mental_status"], "peak_flow": sr.peak_flow(t)},
                              "points": rows}
    c = out["cases"]
    out["mapping_coherent"] = all(
        all(v["exact"].values()) and v["L"] == 0.0 and v["G"] == 0.0 and v["availability"] == 1.0
        and math.isclose(v["paco2_at_authored_rr"], float(sr.truth(n)["abg_paco2"]), rel_tol=1e-9)
        and v["bias_is_the_rr_ratio"] for n in sr.CASES for v in c[n]["points"].values())
    out["drive_gap"] = {n: {p: c[n]["points"][p]["rr_gap"] for p in POINTS} for n in sr.CASES}
    out["pass"] = out["mapping_coherent"]
    return out


def contrast(found_arrival: dict) -> dict:
    """P2S-3-4: the two cases differ by the family mechanics severity only (one profile, one set of equations)."""
    c = found_arrival["cases"]
    p, s = c[sr.CASE]["points"], c[sr.SECONDARY]["points"]
    out = {"mechanics_ordered": {pt: p[pt]["mechanics_efficiency"] < s[pt]["mechanics_efficiency"] for pt in POINTS},
           "paco2_ordered_in_core": {pt: p[pt]["paco2"] > s[pt]["paco2"] for pt in POINTS},
           "primary_hypercapnic_in_core": {pt: p[pt]["paco2"] > 40.0 for pt in POINTS},
           "secondary_hypocapnic_in_core": {pt: s[pt]["paco2"] < 40.0 for pt in POINTS},
           "secondary_hypocapnic_at_authored_rr": {pt: s[pt]["paco2_at_authored_rr"] < 40.0 for pt in POINTS},
           "band_overlap": [max(c[sr.CASE]["band"]["lower"], c[sr.SECONDARY]["band"]["lower"]),
                            min(c[sr.CASE]["band"]["upper"], c[sr.SECONDARY]["band"]["upper"])],
           "same_profile_and_equations": True}
    out["secondary_compensation"] = ("COMMON_DRIVE_GAP: the 24f hypocapnia holds at the authored RR but not at the core's "
                                     "RR (P2P-2 drive, hypoxaemic mapping UNSET, no non-chemical excitatory input); "
                                     "reported, never deciding")
    out["pass"] = (all(out["mechanics_ordered"].values()) and all(out["paco2_ordered_in_core"].values())
                   and all(out["primary_hypercapnic_in_core"].values())
                   and all(out["secondary_hypocapnic_at_authored_rr"].values()))
    return out


# P2S-3-2: the family writer ----------------------------------------------------------------------------------------------------

def writer_semantics() -> dict:
    tree = ast.parse((ROOT / FAMILY_FILE).read_text(encoding="utf-8"))
    keywords = sorted({k.arg for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") ==
                       "Contribution" for k in n.keywords})
    names = {getattr(n, "id", getattr(n, "attr", None)) for n in ast.walk(tree) if isinstance(n, (ast.Name,
                                                                                                    ast.Attribute))}
    forbidden = sorted(names & {"ChannelDelta", "DemandModifier", "BloodFlow", "SettingChange", "RhythmTransition",
                                "Channel", "respiratory_rate", "paco2", "spo2", "fio2", "hr"})
    a, prof = sr.anchors(), profile()
    s = dv.arrival_state(a, prof)
    w = obstruction()
    c = w.contribute(s, 1, (), a, prof)
    refused = {}
    try:
        step(dv.arrival_state(sr.anchors(arrival_mechanics_efficiency=1.0), ar.common_profile()), (w,),
             sr.anchors(arrival_mechanics_efficiency=1.0), go.gas_profile(ar.common_profile()))
        refused["candidate_off"] = False
    except ProvenanceError:
        refused["candidate_off"] = True
    for label, value in (("negative", -0.01), ("one", 1.0), ("nan", float("nan")), ("boolean", True)):
        try:
            AirwayObstruction("x", value)
            refused[label] = False
        except CoreInvariantError:
            refused[label] = True
    from .integration import _REGISTRY
    out = {"contribution_keywords": keywords, "forbidden_names": forbidden,
           "writes": [(m.factor, m.source.key) for m in c.mechanics], "deltas": len(c.deltas),
           "zero_rate_writes_nothing": obstruction(0.0).contribute(s, 1, (), a, prof).mechanics == (),
           "registered": _REGISTRY.get(AirwayObstruction.type_name) is AirwayObstruction,
           "disease_module": AirwayObstruction.kind.value == "disease_module", "refused": refused}
    out["pass"] = (keywords == ["mechanics"] and not forbidden and out["writes"] == [(1.0 - MID_WORSENING,
                                                                                     "disease_module:asthma-obstruction")]
                   and not out["deltas"] and out["zero_rate_writes_nothing"] and out["registered"]
                   and out["disease_module"] and all(refused.values()))
    return out


# P2S-3-15: trajectories ---------------------------------------------------------------------------------------------------

def _without_mechanics(state) -> dict:
    return mc._without_mechanics(state)


def untreated() -> dict:
    out = {}
    prof = profile()
    for name in sr.CASES:
        a = sr.anchors(name)
        plain, _ = course((obstruction(0.0),), anchors=a, prof=prof)
        rows = {}
        for rate in WORSENING_PER_MIN:
            states, records = course((obstruction(rate),), anchors=a, prof=prof)
            series = [reading(x, a, prof) for x in states]
            base = [reading(x, a, prof) for x in plain]
            same = {k: [x[k] for x in series] == [y[k] for y in base] for k in ("rr", "spo2", "G", "L", "D", "lactate",
                                                                                 "hr", "delivery_index",
                                                                                 "consciousness_level", "map")}
            rows[f"{rate:.6g}"] = {
                "at": _rows(states, a, prof),
                "only_mechanics_moves": same, "states_identical_but_mechanics":
                    [_without_mechanics(x) for x in states] == [_without_mechanics(y) for y in plain],
                # Everything else equal: against the same case without worsening, minute by minute.
                "directions": ({"E_down": _decreasing([x["mechanics_efficiency"] for x in series]),
                                "W_below": all(x["W"] < y["W"] for x, y in zip(series[1:], base[1:])),
                                "paco2_above": all(x["paco2"] > y["paco2"] for x, y in zip(series[1:], base[1:])),
                                "ph_below": all(x["ph"] < y["ph"] for x, y in zip(series[1:], base[1:]))}
                               if rate > 0.0 else
                               {"E_constant": len({x["mechanics_efficiency"] for x in series}) == 1}),
                "family_writes": sorted({c.source.key for r in records for c in r.mechanics}),
                "pulse_kept": all(x.R.pulse_present for x in states)}
        out[name] = rows
    out["pass"] = all(all(v["only_mechanics_moves"].values()) and v["states_identical_but_mechanics"]
                      and all(v["directions"].values()) and v["pulse_kept"]
                      for name in sr.CASES for v in out[name].values())
    return out


def relief() -> dict:
    """A structural mechanics relief through the common target (the P2S-2 probe writer; BRONCHODILATOR_WRITER_DEFERRED)."""
    a, prof = sr.anchors(), profile()
    probe = mc.SyntheticMechanics("p2s3-relief", RELIEF["factor_per_min"], RELIEF["from_minute"], RELIEF["to_minute"])
    plain, _ = course((obstruction(),), anchors=a, prof=prof)
    relieved, _ = course((obstruction(), probe), anchors=a, prof=prof)
    w = (RELIEF["from_minute"], RELIEF["to_minute"])
    r0 = [reading(x, a, prof) for x in plain]
    r1 = [reading(x, a, prof) for x in relieved]
    out = {"at": {str(m): {"plain": {k: r0[m][k] for k in ("mechanics_efficiency", "W", "paco2", "rr", "spo2", "hr")},
                           "relieved": {k: r1[m][k] for k in ("mechanics_efficiency", "W", "paco2", "rr", "spo2", "hr")}}
                  for m in READ},
           "relief_raises_W_lowers_paco2": r1[w[1]]["W"] > r0[w[1]]["W"] and r1[w[1]]["paco2"] < r0[w[1]]["paco2"],
           "rr_spo2_hr_unchanged": all(r0[m][k] == r1[m][k] for m in range(len(r0)) for k in ("rr", "spo2", "hr")),
           "status": "BRONCHODILATOR_WRITER_DEFERRED: the shadow core has no bronchodilator action and no post-treatment "
                     "course is authored; relief is representable through the common mechanics target"}
    out["pass"] = out["relief_raises_W_lowers_paco2"] and out["rr_spo2_hr_unchanged"]
    return out


def oxygen() -> dict:
    a, prof = sr.anchors(), profile()
    room, _ = course((obstruction(),), anchors=a, prof=prof)
    base = [reading(x, a, prof) for x in room]
    out = {"fio2": {}, "room_air": {str(m): base[m]["spo2"] for m in READ}}
    same_ventilation = True
    higher = True
    for f in FIO2:
        states, _ = course((obstruction(), Oxygen("asthma-o2", 0, f)), anchors=a, prof=prof)
        r = [reading(x, a, prof) for x in states]
        out["fio2"][f"{f:g}"] = {str(m): r[m]["spo2"] for m in READ}
        same_ventilation &= all(r[m]["paco2"] == base[m]["paco2"] and r[m]["rr"] == base[m]["rr"]
                                for m in range(len(r)))
        higher &= all(r[m]["spo2"] > base[m]["spo2"] for m in range(1, len(r)))
    text = (ROOT / FAMILY_FILE).read_text(encoding="utf-8")
    family_oxygen = any(getattr(n, "id", getattr(n, "attr", "")) in ("fio2", "spo2", "oxygenation", "Oxygen",
                                                                      "SettingChange")
                        for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.Name, ast.Attribute)))
    out.update({"spo2_rises_with_fio2": higher, "paco2_rr_unchanged_by_oxygen": same_ventilation,
                "family_oxygen_function": family_oxygen})
    out["pass"] = higher and same_ventilation and not family_oxygen
    return out


# P2S-3-5 to 8: direct G, oxygenation link, drive, availability --------------------------------------------------------------

def direct_g() -> dict:
    out = {"used": False, "status": "DIRECT_G_NOT_REQUIRED: the arrival V/Q impairment is the anchored arrival (G = 0, "
                                    "the authored SpO2 exact); no later V/Q change is authored; the family writes no G "
                                    "and no L", "cases": {}}
    k = DIAGNOSTIC_GAS
    for name in sr.CASES:
        t = sr.truth(name)
        fio2 = t["abg_fio2_percent"] / 100.0
        alveolar = fio2 * (k["barometric_mmhg"] - k["water_vapour_mmhg"]) - float(t["abg_paco2"]) / k["respiratory_quotient"]
        eucapnic = fio2 * (k["barometric_mmhg"] - k["water_vapour_mmhg"]) - 40.0 / k["respiratory_quotient"]
        out["cases"][name] = {"pao2": t["abg_pao2"], "paco2": t["abg_paco2"], "alveolar_po2": alveolar,
                              "a_a_gradient": alveolar - float(t["abg_pao2"]),
                              "hypoventilatory_alveolar_loss": eucapnic - alveolar}
    states, records = course((obstruction(),))
    out["g_writes"] = sum(1 for r in records for d in r.deltas if d.channel is Channel.G)
    out["l_writes"] = sum(1 for r in records for d in r.deltas if d.channel is Channel.L)
    out["G_L_stay_zero"] = all(s.G == 0.0 and s.L == 0.0 for s in states)
    out["diagnostic_only"] = ("the alveolar arithmetic reads the authored gas with textbook constants; it is not a core "
                              "path (HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED)")
    out["unexplained"] = ("EXPECTED_ALVEOLAR_GAS_EXTENSION: in 49m part of the hypoxaemia is hypoventilatory; the core "
                          "keeps the arrival SpO2 and does not lower it as PaCO2 rises")
    out["pass"] = out["g_writes"] == 0 and out["l_writes"] == 0 and out["G_L_stay_zero"]
    return out


def drive() -> dict:
    prof = profile()
    synthetic = rd.hypoxaemic(prof, HYPOXAEMIC_GAIN)
    out = {"cases": {}}
    for name in sr.CASES:
        a = sr.anchors(name)
        unset = dv.arrival_drive_composition(a, prof)
        synth = dv.arrival_drive_composition(a, synthetic)
        out["cases"][name] = {"authored_rr": a.respiratory_rate, "unset": {"acid": unset.acid_drive,
                                                                           "hypoxaemic": unset.hypoxaemic_drive,
                                                                           "rr": unset.expressed_rr},
                              "synthetic_hypoxaemic": {"hypoxaemic": synth.hypoxaemic_drive, "rr": synth.expressed_rr},
                              "availability": unset.availability}
    out["unchanged"] = (prof.hypoxaemic_drive_mapping is None and prof.hypoxaemic_to_drive_gain is None
                        and prof.central_drive_availability == 1.0
                        and prof.acid_to_drive_gain == ar.common_profile().acid_to_drive_gain)
    out["synthetic_grows"] = all(v["synthetic_hypoxaemic"]["rr"] > v["unset"]["rr"] for v in out["cases"].values())
    out["classification"] = ("COMMON_DRIVE_GAP (EXPECTED_EXTENSION): the arrival tachypnoea is not expressed without a "
                             "non-chemical excitatory input; no asthma residual, no gain fitted")
    out["pass"] = out["unchanged"] and out["synthetic_grows"]
    return out


# P2S-3-12 to 14: HR, consciousness, collapse ---------------------------------------------------------------------------------

BETA_AGONIST_WORDS = ("reliever", "rescue inhaler", "bronchodilator")


def heart_rate() -> dict:
    out = {"cases": {}}
    prof = profile()
    for name in sr.CASES:
        decomposition = dv.heart_rate_decomposition(sr.anchors(name), prof)
        band = {point: dv.heart_rate_decomposition(sr.anchors(name, point), prof)["predicted_arrival_hr"]
                for point in POINTS}
        meds = " ".join(sr.truth(name)["medications"] or []).lower()
        out["cases"][name] = {"authored": decomposition["observed_arrival_hr"],
                              "predicted": decomposition["predicted_arrival_hr"],
                              "mismatch_bpm": decomposition["mismatch_bpm"], "predicted_over_bands": band,
                              "prehospital_beta_agonist": any(w in meds for w in BETA_AGONIST_WORDS)}
    base = ar.common_profile()
    out["gains_untouched"] = all(getattr(prof, f.name) == getattr(base, f.name) for f in fields(prof)
                                 if f.name not in go.REFERENCE and f.name != "respiratory_mechanics")
    out["classification"] = ("HR_GAP_DISTRESS_AROUSAL_DOMINANT carried forward (ACS, pulmonary oedema, PE, asthma); the "
                             "authored repeated beta-agonist use is a confounder in asthma only; nothing patched")
    out["pass"] = out["gains_untouched"]
    return out


def consciousness(found_untreated: dict) -> dict:
    at = found_untreated[sr.CASE][f"{MID_WORSENING:.6g}"]["at"]
    return {"authored_49m": sr.truth(sr.CASE)["mental_status"], "authored_24f": sr.truth(sr.SECONDARY)["mental_status"],
            "core_level": {m: at[m]["consciousness_level"] for m in at}, "paco2": {m: at[m]["paco2"] for m in at},
            "reading": "the core's level is the authored arrival plus derive's ADOPTED SpO2 / SBP ladder: the rising PaCO2 "
                       "does not reach it (P2L-2 not integrated); 49m is diagnostic evidence for a hypercapnic "
                       "encephalopathy, never a calibration target",
            "pass": len(set(at[m]["consciousness_level"] for m in at)) == 1}


def collapse() -> dict:
    a, prof = sr.anchors(), profile()
    states, _ = course((obstruction(an.LOSS_PER_MIN[-1]),), anchors=a, prof=prof)
    ramp = cx.CollapseProfile(perfusion_mapping=cx.PerfusionMapping(*an.STRUCTURAL_RAMP))
    rows = []
    for s in (states[m] for m in (0, 60, HORIZON)):
        r = cx.readings(s, a, prof)
        unset = cx.signal_at(r, cx.CollapseProfile())
        structural = cx.signal_at(r, ramp)
        rows.append({"minute": s.minute, "map": r["map"], "delivery": unset.delivery, "unset_complete": unset.complete,
                     "structural_value": structural.value,
                     "max_holds": structural.value == max(structural.perfusion, structural.delivery)})
    source = (CORE_DIR / "collapse.py").read_text(encoding="utf-8").lower()
    out = {"rows": rows, "max_holds": all(r["max_holds"] for r in rows),
           "unset_is_lower_bound": all(not r["unset_complete"] for r in rows),
           "mechanics_reach_output": len({round(r["map"], 9) for r in rows}) > 1,
           "no_family_rule": not any(w in source for w in ("asthma", "bronch", "airway", "obstruction")),
           "status": "EXPECTED_EXTENSION: the mechanics do not reach output in the core (no hypercapnic / hypoxic "
                     "arrest path); the collapse layer accepts the readings structurally"}
    out["pass"] = out["max_holds"] and out["unset_is_lower_bound"] and out["no_family_rule"]
    return out


# P2S-3-17: legacy, read last --------------------------------------------------------------------------------------------------

LEGACY_MINUTES = READ


def legacy() -> dict:
    """The family engine's untreated courses, read as LEGACY_REFERENCE_ONLY."""
    from . import legacy_adapter as la
    out = {}
    for name in sr.CASES:
        engine = la._engine()
        current = la.bank_case(name, family=sr.FAMILY)
        engine._initialize(current)
        rows = {}
        for minute in range(max(LEGACY_MINUTES) + 1):
            if minute in LEGACY_MINUTES:
                o = current.get("observable", {})
                rows[str(minute)] = {k: o.get(k) for k in ("sbp", "dbp", "hr", "spo2", "respiratory_rate",
                                                           "mental_status")}
            if minute < max(LEGACY_MINUTES):
                engine.advance_clinical_time(current, 1)
        out[name] = rows
    return out


def legacy_comparison(found_untreated: dict, legacy_rows: dict) -> dict:
    core = found_untreated[sr.CASE][f"{MID_WORSENING:.6g}"]["at"]
    rows = {m: {"legacy": legacy_rows[sr.CASE].get(m, {}),
                "core": {k: core[m][k] for k in ("map", "spo2", "hr", "rr", "paco2", "consciousness_level")}}
            for m in ("0", "60", "120")}
    classes = {
        "rr": "EXPECTED_EXTENSION: the legacy shows the authored RR; the core's RR is the P2P-2 drive's (COMMON_DRIVE_GAP)",
        "spo2": "EXPECTED_EXTENSION: the legacy moves SpO2 with its obstruction (oxygen shunt 0.30); the core keeps the "
                "arrival SpO2 as PaCO2 rises (HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED)",
        "hr": "POSSIBLE_COMMON_CORE_GAP: the legacy holds the authored HR (with beta side effects); the core's arrival HR "
              "is the common physiology's (HR_GAP_DISTRESS_AROUSAL_DOMINANT)",
        "fatigue_obstruction_drift": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both worsen untreated; the size is the "
                                     "family span's and the legacy drift's, neither authored; no fatigue memory",
        "bronchodilator": "EXPECTED_EXTENSION: the legacy's bronchodilation family is not migrated "
                          "(BRONCHODILATOR_WRITER_DEFERRED)",
        "consciousness": "POSSIBLE_COMMON_CORE_GAP: the core's level does not read PaCO2 (P2L-2 not integrated)"}
    return {"rows": rows, "secondary_legacy": legacy_rows[sr.SECONDARY], "classes": classes,
            "possible_common_core_gap": sorted(k for k, v in classes.items() if v.startswith("POSSIBLE_COMMON_CORE_GAP")),
            "used_for_parameters": False}


# P2S-3-18: prior families unchanged ---------------------------------------------------------------------------------------------

def non_regression() -> dict:
    """With the asthma writer absent nothing common moves: P2S-2's probes, its interface, its arrival regions and its
    non-regression (which carries GI, ACS, the oedema, PE and P2P-2) reproduce its frozen record; every common file is at
    its P2S-2 bytes."""
    p2s2 = json.loads(mc.RECORD.read_text(encoding="utf-8"))
    with p2s2_view():
        out = {"p2s2_probes": go._plain(mc.structural_probes()) == p2s2["probes"],
               "p2s2_interface": go._plain(mc.interface()) == p2s2["interface"],
               "p2s2_arrival_regions": go._plain(mc.arrival_regions()) == p2s2["arrival_regions"],
               "p2s2_non_regression": go._plain(mc.non_regression()) == p2s2["non_regression"],
               "p2s2_directions": go._plain(mc.directions()) == p2s2["directions"]}
    out["common_files_untouched"] = common_untouched()
    out["pass"] = all(v for k, v in out.items() if k != "common_files_untouched") and all(
        out["common_files_untouched"].values())
    return out


# The closed packages' view: the files P2S-2 left, P2S-3's tuple entries undone (proven) -------------------------------------------

P2S2_HEAD = "daa23d6"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/embolism_migration.py", '
                                     '"clinical_core/embolism_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_mechanics.py", '
                                     '"clinical_core/respiratory_mechanics_report.py",\n'
                                     '                        "clinical_core/asthma_migration.py", '
                                     '"clinical_core/asthma_migration_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/embolism_migration.py", '
                                     '"clinical_core/embolism_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_mechanics.py", '
                                     '"clinical_core/respiratory_mechanics_report.py")\n'
                                     '\n'),),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/embolism_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_mechanics_report.py",\n'
                                     '                      "clinical_core/asthma_migration_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/embolism_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_mechanics_report.py")\n'
                                     '\n'),)}
CORE_AT_P2S2 = {'clinical_core/decision_pack.py': '2e32a6b377c882505b34a8529a9097d653cde9a8e26eb6654ed226ce1262cf2c',
 'clinical_core/lactate_slice.py': 'b8d08c6cf3bb13d0d8f7fbcd7ab42e9c5b738845e67783d002aa88b220316c15'}
# </reversal>
# <common>
COMMON_AT_P2S2 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/derived.py': '9c9cc2b1540c8e93896f78d4922456bfa611869d9c902274fc39a8fde0c1c6d5',
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
 'clinical_core/integration.py': 'd8b43a492b3f545feb52f0e2d3654c64284573c2e458003c12c7c988e75fe1b7',
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
 'clinical_core/provenance.py': '71bb736121bc9950e43864b348f67694c14145a54944b01ab90187ddf0979e60',
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
 'clinical_core/state.py': 'fff5380826b06c35b98d2f8a2da1808e8dd284df6234fd06114431776eb89a7e',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>
P2S2_FREEZE_DIGEST = "ba6e9997495dd2009526841189e622fc6c6b9b92f0c987535cfff2e8a8462e64"
P2S2_RECORD_SHA = "a63f0900d34af07dd8d2e94095e50954764edd310c0ccf51f01b10137979d1e6"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2S2[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2S2.items()}


def p2s2_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2S-2 file plus P2S-3's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2s2_sources(sources: dict) -> dict:
    """A P2S-2 dependency map: P2S-3's files removed, each changed file at its P2S-2 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2S2.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def p2s2_registry(registry: dict) -> dict:
    """A registry as P2S-2 left it: the asthma family's type removed."""
    return {k: v for k, v in registry.items() if k not in FAMILY_TYPES}


_MC_INTERFACE = mc.interface


def p2s2_interface() -> dict:
    """P2S-2's interface check as the P2S-2 tree reads: the asthma family module (the first family writer of the mechanics,
    by design) left out of its scan of family modules, the pass recomputed from the same items."""
    out = dict(_MC_INTERFACE())
    writers = [m for m in out["family_writers"] if m not in OWN]
    out["family_writers"] = writers
    out["pass"] = (out["persists"] and out["compose"] and out["records"] == [2, 2, 2] and all(out["refused"].values())
                   and out["aux_source"] == ["core_coupling:respiratory_mechanics"] and not writers)
    return out


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2S-2's view reads the P2S-2 files (proven), the registry without the
    asthma family's type and P2S-2's family-module scan without the asthma module, so every closed guard still reads the
    tree it froze."""
    patch.setattr(mc, "_live", p2s2_text)
    patch.setattr(mc, "interface", p2s2_interface)
    # P2S-2's own view of P2Q-2 reads the sources through the function it captured: it now sees the P2S-2 sources.
    patch.setattr(mc, "_FREEZE_SOURCES", lambda: p2s2_sources(_FREEZE_SOURCES()))
    patch.setattr(pe, "_REGISTRY", p2s2_registry(pe._REGISTRY))
    patch.setattr(lw, "_REGISTRY", p2s2_registry(lw._REGISTRY))


_FREEZE_SOURCES = bf.freeze_sources


class p2s2_view:
    """P2S-2's analysis reading the tree P2S-2 froze (its sources, its family-module scan), for its own proofs."""

    def __enter__(self):
        self._patch = mc._Patch()
        chain(self._patch)
        self._patch.setattr(bf, "freeze_sources", lambda: p2s2_sources(_FREEZE_SOURCES()))
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2s2_view():
        p2s2_digest = mc.freeze_digest()
        p2s2_proof = mc.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2s2_freeze_digest": p2s2_digest == P2S2_FREEZE_DIGEST,
            "p2s2_proof": all(p2s2_proof["proofs"].values()) and p2s2_proof["p2q2_freeze_digest"]
            and p2s2_proof["p2q2_proof"] and p2s2_proof["p2q2_record"],
            "p2s2_record": hashlib.sha256(mc.RECORD.read_bytes()).hexdigest() == P2S2_RECORD_SHA}


# P2S-3-19: the migration verdict (predeclared) ------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "the family mechanics writer cleanly targets the common mechanics (mechanics changes only; refused with the "
    "candidate off; no RR, PaCO2, SpO2, G, DO2, D, lactate, HR or consciousness writes)",
    "the arrival mapping is coherent (truth by path; the authored arrival exact where the core models it; the intrinsic "
    "RR declared with its own efficiency; L and G 0; availability 1; the arrival PaCO2 differs from the authored by "
    "exactly the RR ratio, the mechanics mapping consistent at the authored RR)",
    "the 49m / 24f distinction is representable by family mechanics severity only (mechanics and core PaCO2 ordered at "
    "every point; 49m hypercapnic; 24f hypocapnic at its authored RR; one profile, one set of equations)",
    "W / PaCO2 behave coherently (worsening: E, W, pH down, PaCO2 up, nothing else moved; relief: the reverse; oxygen: "
    "SpO2 up, PaCO2 and RR unchanged)",
    "no common retuning (the P2P-2 drive unchanged, hypoxaemic UNSET, availability 1, the PaCO2 reference 40, the gains "
    "untouched; the P2S-2 tree proven)",
    "direct G optional and clean, no false L (no G or L write; G and L stay 0)",
    "the HR gap stays diagnostic (no sympathetic input; residual reported)",
    "prior families unchanged (P2S-2's probes, interface, regions, directions and non-regression reproduced; every common "
    "file at its P2S-2 bytes)",
    "collapse accepts the readings structurally (max holds, UNSET a lower bound, no family rule)",
)
READY = "ASTHMA_SHADOW_MIGRATION_READY"
NOT_READY = "ASTHMA_SHADOW_MIGRATION_NOT_READY"
VERDICT_RULE = ("Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion as "
                "the blocker. Reported and never deciding, as in every migration since P2P-1: the arrival RR gap "
                "(COMMON_DRIVE_GAP) and, new with the mechanics candidate, its 1:1 propagation into the arrival PaCO2 "
                "(the 24f compensated hypocapnia is not reached at the core's RR); the hypoventilatory share of the "
                "hypoxaemia; the HR gap; consciousness; the legacy differences")
RECOMMENDATION = {READY: "P2T-0: COMMON SYMPATHETIC / ARRIVAL-HR GAP AUDIT (read-only); no further executable physiology"}


def verdict(found: dict) -> dict:
    proof = found["proof"]
    values = (
        found["writer"]["pass"],
        found["case"]["available"] and found["arrival"]["pass"],
        found["contrast"]["pass"],
        found["untreated"]["pass"] and found["relief"]["pass"] and found["oxygen"]["pass"],
        found["drive"]["pass"] and found["heart_rate"]["gains_untouched"] and all(proof["proofs"].values())
        and proof["p2s2_freeze_digest"] and proof["p2s2_proof"] and proof["p2s2_record"],
        found["direct_g"]["pass"],
        found["heart_rate"]["pass"],
        found["non_regression"]["pass"] and all(proof["common_untouched"].values()),
        found["collapse"]["pass"],
    )
    criteria = dict(zip(VERDICT_CRITERIA, values))
    blocker = next((name for name, ok in criteria.items() if not ok), None)
    return {"criteria": criteria, "ready": blocker is None, "blocker": blocker,
            "verdict": READY if blocker is None else f"{NOT_READY} — {blocker}",
            "recommendation": RECOMMENDATION[READY] if blocker is None else None}


# Freeze and record -------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "decisions": DECISIONS, "cases": list(sr.CASES),
            "selection_rule": sr.SELECTION_RULE, "truth_paths": {k: list(v) for k, v in sr.TRUTH_PATHS.items()},
            "truth_classes": TRUTH_CLASSES, "arrival_classes": sr.ARRIVAL_CLASSES, "channel_roles": sr.CHANNEL_ROLES,
            "observation_layer": sr.OBSERVATION_LAYER, "intrinsic_points": sr.INTRINSIC_POINTS,
            "worsening_per_min": list(WORSENING_PER_MIN), "horizon": HORIZON, "read": list(READ),
            "points": list(POINTS), "fio2": list(FIO2), "relief": RELIEF, "hypoxaemic_gain": HYPOXAEMIC_GAIN,
            "hypoxaemic_mapping": [list(p) for p in rd.SYNTHETIC_MAPPING], "diagnostic_gas": DIAGNOSTIC_GAS,
            "beta_agonist_words": list(BETA_AGONIST_WORDS), "legacy_constants": LEGACY_CONSTANTS,
            "model_derived": MODEL_DERIVED, "later_observations": LATER_OBSERVATIONS,
            "legacy_minutes": list(LEGACY_MINUTES), "verdict_criteria": list(VERDICT_CRITERIA),
            "verdict_rule": VERDICT_RULE, "recommendation": RECOMMENDATION, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}, "family_types": list(FAMILY_TYPES),
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2s2": CORE_AT_P2S2,
            "common_at_p2s2": COMMON_AT_P2S2,
            "p2s2": {"head": P2S2_HEAD, "freeze_digest": P2S2_FREEZE_DIGEST, "record": P2S2_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2s2": hashlib.sha256(mc.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "case": case(), "arrival": arrival(), "writer": writer_semantics()}
    found["contrast"] = contrast(found["arrival"])
    found.update({"untreated": untreated(), "relief": relief(), "oxygen": oxygen(), "direct_g": direct_g(),
                  "drive": drive(), "heart_rate": heart_rate(), "collapse": collapse()})
    found["consciousness"] = consciousness(found["untreated"])
    found["non_regression"] = non_regression()
    found["legacy"] = legacy()
    found["legacy_comparison"] = legacy_comparison(found["untreated"], found["legacy"])
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
    data = run()
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
