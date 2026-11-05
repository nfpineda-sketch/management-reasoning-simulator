"""P2U-1: the opioid shadow migration (central respiratory depression through the common respiratory architecture).

The family is the stress test of the common respiratory chain without lung disease: central availability -> expressed RR
-> W -> PaCO2 -> (P2T-5's relative alveolar link) SpO2 -> delivery, with no family G, L, distress or oxygen equation.

Common change (proven against P2T-5's tree, 98a2bb0), the documented CENTRAL_AVAILABILITY_STATE_DEFERRED:
- ``AuxiliaryState.central_availability`` (0 to 1, default 1) and ``Anchors.arrival_central_availability`` (default 1):
  P2P-2's availability became writable by a family, as P2S-2's mechanics and P2T-1's distress; not a canonical channel;
- ``provenance.AvailabilityChange`` (additive, fail closed outside 0 to 1, P2T-1A's roundoff rule at both bounds);
- the composition expresses the profile's structural value times the state's availability (1 x 1 = 1 exactly by
  default, so every closed package is unchanged); it needs the P2K-2 acid-base physiology, as the profile value did.

Family (``modules/opioid.py``): ``OpioidCentralDepression`` (a declared fraction of the availability lost per minute) and
``NaloxoneReversal`` (a declared fraction of the missing availability returned per minute, never past 1). Both write the
availability only; rates SYNTHETIC_ONLY. Arrival (``opioid_reference.py``): the availability and the mechanics
efficiency as FAMILY_CANDIDATE latent arrival states at each carried intrinsic RR. The P2T-5 link stays UNSET in the
committed profile; its R = 0.8 enters only the probes, as P2T-5's SYNTHETIC_PHYSIOLOGIC_REFERENCE.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import derived as dv
from . import distress_closure as xm
from . import gas_exchange_architecture as go
from . import opioid_reference as orf
from . import oxygenation_link as om
from . import respiratory_distress as dm
from . import respiratory_mechanics as mc
from .integration import step
from .modules.opioid import NaloxoneReversal, OpioidCentralDepression

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2U-1"
DECIDED = "2026-11-05"
OWN = ("clinical_core/opioid_migration.py",)
REPORT = "clinical_core/opioid_migration_report.py"
FAMILY_FILES = ("clinical_core/modules/opioid.py", "clinical_core/opioid_reference.py")
RECORD = ROOT / "docs" / "revision" / "P2U1_opioid_migration.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2U1_OPIOIDE_SOMBRA.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
FAMILY_TYPES = (OpioidCentralDepression.type_name, NaloxoneReversal.type_name)
NEW_AUX = "central_availability"
NEW_ANCHOR = "arrival_central_availability"
#: P2U-1's candidate input, outside CASE_PARAMETERS until the faculty adopts this physiology (as P2K-2's, P2O-3's,
#: P2S-2's and P2T-1's): the arrival central drive availability.
CANDIDATE_INPUTS = (NEW_ANCHOR,)

DECISIONS = {
    "family": "central respiratory depression only: the family writes the common central availability, never RR, W, "
              "PaCO2, SpO2, G, L, the mechanics, the distress, HR, consciousness, delivery or D",
    "common_blocker": "CENTRAL_AVAILABILITY_STATE_DEFERRED (P2P-2 / P2T-5): the availability was a profile constant, so "
                      "no family writer or antagonist could move it in time; the minimum interface was added",
    "arrival": "availability and mechanics efficiency are FAMILY_CANDIDATE latent arrival states at each carried "
               "intrinsic RR (12 / 16 / 20); no value selected",
    "oxygenation": "P2T-5's link, R = 0.8 only as its SYNTHETIC_PHYSIOLOGIC_REFERENCE in probes; the committed profile "
                   "keeps R None; no opioid oxygen function; the common FiO2 rule (FIO2_RESPONSE_MAGNITUDE_DEBT)",
    "naloxone": "a family treatment signal restoring the availability toward 1; kinetics UNSET (SYNTHETIC_ONLY)",
    "hr": "no opioid HR term; the authored HR is tested against the common intrinsic-HR band",
    "consciousness": "diagnostic only (CONSCIOUSNESS_INTEGRATION_DEBT); N unread",
    "out_of_scope": "consciousness integration, systemic stress, CO2 kinetics, FiO2 recalibration, a hypoxaemic drive, "
                    "collapse thresholds, legacy fitting",
}

# Synthetic, predeclared probe values (SYNTHETIC_ONLY) -----------------------------------------------------------------------

DEEPENING_PER_MIN = 0.005             # the depression deepening untreated (U1-U4)
NALOXONE = {"recovery_per_min": 0.10, "from_minute": 10}        # the antagonist (U5)
RECURRENCE = {"naloxone_from": 10, "naloxone_to": 40, "deepening_per_min": 0.02, "deepening_from": 40}   # 67f
SEVERE_DEEPENING_PER_MIN = 0.03       # the structural collapse direction probe
COURSE_MINUTES = 60
LONG_COURSE_MINUTES = 120
FIO2_PROBE = 0.40
POINTS = ("lower", "midpoint", "upper")


def profile(**changes) -> dv.CoreProfile:
    """The committed opioid profile: the common reference point with the mechanics candidate on; the P2T-5 link, the
    distress readers and the hypoxaemic drive UNSET."""
    return orf.common_profile(**changes)


def link_profile(**changes) -> dv.CoreProfile:
    """The probe profile: the committed one with P2T-5's synthetic respiratory quotient."""
    return replace(profile(**changes), respiratory_quotient=om.SYNTHETIC_R)


def depression(rate: float = DEEPENING_PER_MIN, start: int = 0, stop=None) -> OpioidCentralDepression:
    return OpioidCentralDepression("p2u1-opioid", rate, start, stop)


def naloxone(rate: float = NALOXONE["recovery_per_min"], start: int = NALOXONE["from_minute"], stop=None):
    return NaloxoneReversal("p2u1-naloxone", rate, start, stop)


def course(items, anchors, prof, minutes=COURSE_MINUTES):
    state = dv.arrival_state(anchors, prof)
    states, records = [state], []
    for _ in range(minutes):
        state, record = step(state, tuple(items), anchors, prof)
        states.append(state)
        records.append(record)
    return states, records


def _row(state, anchors, prof) -> dict:
    r, d = dv.respiration(state, anchors, prof), dv.derive(state, anchors, prof)
    return {"minute": state.minute, "availability": state.aux.central_availability, "rr": r.respiratory_rate,
            "W": r.ventilation, "paco2": r.paco2, "ph": r.ph, "spo2": d.spo2,
            "delivery": dv.delivery_rel_of(state, anchors, prof), "D": state.D, "lactate": d.lactate,
            "hr": d.pulse_rate_bpm, "consciousness": d.consciousness_level, "G": state.G, "L": state.L,
            "distress": state.aux.respiratory_distress, "mechanics": state.aux.mechanics_efficiency}


def _monotone(values, direction) -> bool:
    pairs = list(zip(values, values[1:]))
    return all(b < a for a, b in pairs) if direction < 0 else all(b > a for a, b in pairs)


def _nonincreasing(values) -> bool:
    return all(b <= a for a, b in zip(values, values[1:]))


def _nondecreasing(values) -> bool:
    return all(b >= a for a, b in zip(values, values[1:]))


# P2U-1-1 / -16: the case truth and the legacy (read after) --------------------------------------------------------------------

def case_truth() -> dict:
    out = {}
    for case in orf.CASES:
        t = orf.truth(case)
        out[case] = {"authored": {k: t[k] for k in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "work_of_breathing",
                                                    "mental_status", "abg_paco2", "abg_pao2", "abg_ph", "abg_hco3",
                                                    "abg_fio2_percent", "lactate_mmol_l", "glucose_mg_dl", "hb_g_dl",
                                                    "rhythm", "temperature_c", "creatinine_mg_dl")},
                     "map": orf.authored_map(t), "exposure": t["exposure"], "medications": t["medications"],
                     "breathing": t["breathing"], "respiratory_exam": t["respiratory_exam"],
                     "neurological_exam": t["neurological_exam"], "lungs": [t["pocus_lungs"], t["chest_xray"]],
                     "definitive_actions": t["definitive_actions"], "recurrence_risk": t["recurrence_risk"],
                     "oxygen_authored": "room air (ABG FiO2 21 %); no oxygen therapy authored",
                     "later_observations": "none authored (no post-naloxone truth)"}
    out["classes"] = {"AUTHORED_CASE_TRUTH": "the bank values above", "LEGACY_ENGINE_BEHAVIOR": "legacy() below",
                      "MODEL_DERIVED": "every RR, W, PaCO2, pH, SpO2, delivery, HR and consciousness after arrival"}
    out["pass"] = all(out[c]["authored"]["rhythm"].lower().startswith("sinus") for c in orf.CASES)
    return out


def legacy() -> dict:
    """The legacy engine's opioid behaviour, read from its source only to classify it (never fitted)."""
    text = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    found = {"spontaneous_rr_formula": "spontaneous_rr = 14 - (14 - float(base.get(\"respiratory_rate\", 6)))" in text,
             "oxygen_shunt_opioid": "\"opioid\": .10" in text,
             "fio2_gain_22_for_opioid": "(30 if family not in {\"opioid\"} else 22)" in text,
             "opioid_depot_field": "opioid_depot" in text, "naloxone_decay_module": "opioid_reversal" in text}
    return {"found": found, "classification": "LEGACY_ENGINE_BEHAVIOR",
            "differences": {"restored_rr": "legacy restores toward 14 breaths/min; the core toward the case's intrinsic RR "
                                           "(a carried 12 / 16 / 20)",
                            "oxygen": "legacy uses its own shunt (0.10) and an opioid FiO2 gain of 22; the core uses the "
                                      "common FiO2 rule (30) and P2T-5's link, no opioid oxygen term",
                            "naloxone": "legacy scripts a naloxone pool and decay; the core has only a structural "
                                        "availability recovery (kinetics UNSET)",
                            "depot": "legacy's opioid depot is not mapped (no authored course)"},
            "fitted": False, "pass": all(found.values())}


# P2U-1-2 / -4: channel map and the arrival region -------------------------------------------------------------------------------

def channel_map() -> dict:
    out = {"roles": orf.CHANNEL_ROLES, "classes": orf.ARRIVAL_CLASSES}
    checks = {}
    for case in orf.CASES:
        a = orf.anchors(case)
        s = dv.arrival_state(a, profile())
        checks[case] = {"V": s.V, "T": s.T, "P": s.P, "L": s.L, "G": s.G, "D": s.D, "N": s.N,
                        "distress": s.aux.respiratory_distress, "availability": s.aux.central_availability,
                        "mechanics": s.aux.mechanics_efficiency}
    out["arrival_channels"] = checks
    out["pass"] = all(c["V"] == 0.0 and c["T"] == 1.0 and c["P"] == 1.0 and c["L"] == 0.0 and c["G"] == 0.0
                      and c["D"] == 0.0 and c["distress"] == 0.0 and 0.0 < c["availability"] < 1.0
                      for c in checks.values())
    return out


def arrival_region() -> dict:
    """At each carried intrinsic RR: the latent availability and efficiency, the arrival exactness on the live core, the
    HR against the common intrinsic-HR band, and the steady-state counterfactual (availability restored to 1)."""
    out = {}
    for case in orf.CASES:
        t = orf.truth(case)
        rows = {}
        for point in POINTS:
            a = orf.anchors(case, point)
            for name, prof in (("committed", profile()), ("link", link_profile())):
                s = dv.arrival_state(a, prof)
                r, d = dv.respiration(s, a, prof), dv.derive(s, a, prof)
                if name == "committed":
                    row = {"intrinsic_rr": a.intrinsic_respiratory_rate, "availability": a.arrival_central_availability,
                           "efficiency": a.arrival_mechanics_efficiency, "rr": r.respiratory_rate, "paco2": r.paco2,
                           "ph": r.ph, "spo2": d.spo2, "hr": d.pulse_rate_bpm,
                           "acid_burden": s.aux.metabolic_acid_burden, "drive": r.drive}
                else:
                    row["spo2_link_on"] = d.spo2
            restored = mc.analytic_paco2(float(t["respiratory_rate"]) / a.arrival_central_availability,
                                         a.intrinsic_respiratory_rate, a.arrival_mechanics_efficiency)
            row["restored_paco2"] = restored
            row["efficiency_above_reference"] = a.arrival_mechanics_efficiency > 1.0
            rows[point] = row
        hrs = [rows[p]["hr"] for p in POINTS]
        out[case] = {"points": rows, "authored": {"rr": float(t["respiratory_rate"]), "paco2": float(t["abg_paco2"]),
                                                  "ph": float(t["abg_ph"]), "spo2": float(t["spo2"]), "hr": float(t["hr"])},
                     "hr_band": [min(hrs), max(hrs)],
                     "authored_hr_in_band": min(hrs) <= float(t["hr"]) <= max(hrs),
                     "rr_paco2_product": float(t["respiratory_rate"]) * float(t["abg_paco2"]),
                     "intrinsic_over_efficiency": float(t["respiratory_rate"]) * float(t["abg_paco2"])
                     / dv.DEFAULT_PROFILE.paco2_reference_mmhg}
        out[case]["exact"] = all(abs(rows[p]["rr"] - float(t["respiratory_rate"])) <= 1e-9
                                 and abs(rows[p]["paco2"] - float(t["abg_paco2"])) <= 1e-9
                                 and rows[p]["spo2"] == rows[p]["spo2_link_on"] == float(t["spo2"])
                                 and round(rows[p]["ph"], 2) == float(t["abg_ph"]) and rows[p]["acid_burden"] == 0.0
                                 and 0.0 < rows[p]["availability"] < 1.0 for p in POINTS)
    out["tension"] = {
        "label": "STEADY_STATE_W_ARRIVAL_TENSION",
        "statement": "the common PaCO2 is algebraic (PaCO2 = 40 x I / (E x RR) with no excitatory drive): the authored "
                     "RR x PaCO2 sets I / E; at the carried I in 12-20, 35m needs E 1.16-1.93 (above the reference, "
                     "against the authored 'shallow breaths') and its availability restored to 1 gives a hypocapnic "
                     "PaCO2 (34.5 to 20.7); 67f is near E 1 only at I 12. Ways out, none chosen: an intrinsic RR below "
                     "the carried band, CO2 kinetics (the arrival not at steady state), or E above 1 as read (P2S-2's "
                     "accepted region, 'mechanics not reduced')",
        "decision": "FACULTY (no threshold, band or tau chosen here)"}
    out["pass"] = all(out[c]["exact"] for c in orf.CASES)
    return out


# P2U-1-3 / -14: the writers and U1-U12 -----------------------------------------------------------------------------------------

def writer_audit() -> dict:
    tree = ast.parse((CORE_DIR / "modules" / "opioid.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    built = sorted({n.func.id for n in calls if isinstance(n.func, ast.Name) and n.func.id[0].isupper()})
    keywords = sorted({k.arg for n in calls if isinstance(n.func, ast.Name) and n.func.id == "Contribution"
                       for k in n.keywords})
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree)
                                                                          if isinstance(n, ast.Attribute)}
    forbidden = sorted(names & {"ChannelDelta", "MechanicsChange", "DistressChange", "SettingChange", "BloodFlow",
                                "DemandModifier", "spo2", "paco2", "fio2", "G", "L", "W", "hr", "consciousness_level"})
    out = {"constructed": built, "contribution_keywords": keywords, "forbidden_names": forbidden,
           "registered": FAMILY_TYPES,
           "reads": sorted(names & {"central_availability", "pulse_present"})}
    out["pass"] = (set(built) <= {"Contribution", "AvailabilityChange", "CoreInvariantError"} and keywords == ["availability"]
                   and not forbidden)
    return out


def _records_only_availability(records) -> bool:
    family = {"p2u1-opioid", "p2u1-naloxone"}
    for r in records:
        if any(d.source.id in family for d in r.deltas) or r.mechanics or r.distress or r.blood or r.settings:
            return False
        if any(c.source.id not in family for c in r.availability):
            return False
    return True


def probes() -> dict:
    out = {}
    for case in orf.CASES:
        a = orf.anchors(case)
        down_states, down_records = course((depression(),), a, link_profile())
        up_states, up_records = course((naloxone(),), a, link_profile())
        down = [_row(s, a, link_profile()) for s in down_states]
        up = [_row(s, a, link_profile()) for s in up_states[NALOXONE["from_minute"]:]]
        key = lambda rows, k: [r[k] for r in rows]   # noqa: E731
        u = {"U1": _monotone(key(down, "availability"), -1) and _monotone(key(down, "rr"), -1),
             "U2": _monotone(key(down, "W"), -1),
             "U3": _monotone(key(down, "paco2"), +1),
             "U4": _monotone(key(down, "spo2"), -1) and all(r["G"] == 0.0 for r in down),
             "U5": (_monotone(key(up, "availability"), +1) and _monotone(key(up, "rr"), +1)
                    and _monotone(key(up, "W"), +1) and _monotone(key(up, "paco2"), -1)
                    and _nondecreasing(key(up, "spo2")) and up[-1]["spo2"] > up[0]["spo2"]
                    and max(key(up, "availability")) <= 1.0),
             "U6": all(r["distress"] == 0.0 for r in down + up),
             "U7": all(r["G"] == 0.0 for r in down + up),
             "U8": all(r["L"] == 0.0 for r in down + up),
             "U9": all(r["mechanics"] == a.arrival_mechanics_efficiency for r in down + up)}
        out[case] = {"U": u, "untreated": {k: [down[0][k], down[-1][k]] for k in ("availability", "rr", "W", "paco2",
                                                                                   "spo2", "ph", "delivery")},
                     "naloxone": {k: [up[0][k], up[-1][k]] for k in ("availability", "rr", "W", "paco2", "spo2", "ph",
                                                                      "hr", "consciousness")},
                     "records_only_availability": _records_only_availability(down_records)
                     and _records_only_availability(up_records)}
    audit = writer_audit()
    inserted = "".join(live for relative in ("clinical_core/derived.py", "clinical_core/integration.py",
                                              "clinical_core/state.py", "clinical_core/provenance.py")
                       for live, _ in REVERSAL[relative]).lower()
    identifiers = {n.id.lower() for relative in ("clinical_core/derived.py", "clinical_core/integration.py")
                   for n in ast.walk(ast.parse(_live(relative))) if isinstance(n, ast.Name)}
    out["U10"] = {"no_opioid_term_in_core": "opioid" not in inserted and "naloxone" not in inserted
                  and not any("opioid" in n or "naloxone" in n for n in identifiers),
                  "oxygen_path": "P2T-5's ventilated_oxygenation on the common FiO2 / G SpO2 (no opioid function)"}
    out["U10"]["pass"] = out["U10"]["no_opioid_term_in_core"]
    out["U11"] = {"writer_audit": audit,
                  "pass": audit["pass"] and all(out[c]["records_only_availability"] for c in orf.CASES)}
    out["U12"] = {"note": "non_regression(): P2T-5's record on its tree (P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2, P2Q-2, P2P-2, "
                          "P2P-1, ACS, GI); the committed profiles' availability is 1 (default)"}
    for case in orf.CASES:
        out[case]["pass"] = all(out[case]["U"].values()) and out[case]["records_only_availability"]
    out["pass"] = all(out[c]["pass"] for c in orf.CASES) and out["U10"]["pass"] and out["U11"]["pass"]
    return out


# P2U-1-10 / -13 / -15: naloxone, contrast, recurrence, collapse direction --------------------------------------------------------

def contrast() -> dict:
    rows = {}
    for point in POINTS:
        a35, a67 = orf.anchors(orf.CASE, point), orf.anchors(orf.SECONDARY, point)
        rows[point] = {"availability": [a35.arrival_central_availability, a67.arrival_central_availability],
                       "efficiency": [a35.arrival_mechanics_efficiency, a67.arrival_mechanics_efficiency]}
    out = {"rows": rows, "same_writer_types": True, "same_common_equations": True,
           "ordering": all(r["availability"][0] < r["availability"][1] for r in rows.values()),
           "statement": "one family mechanism (the availability) at two severities: 35m deeper than 67f at every "
                        "carried intrinsic RR, same writers, same common equations, no case residual writer"}
    out["pass"] = out["ordering"]
    return out


def recurrence() -> dict:
    """67f (long-acting morphine, recurrence risk authored): the antagonist stops and the depression resumes."""
    a, p = orf.anchors(orf.SECONDARY), link_profile()
    items = (naloxone(start=RECURRENCE["naloxone_from"], stop=RECURRENCE["naloxone_to"]),
             depression(RECURRENCE["deepening_per_min"], RECURRENCE["deepening_from"]))
    states, records = course(items, a, p, minutes=LONG_COURSE_MINUTES)
    rows = [_row(s, a, p) for s in states]
    peak = rows[RECURRENCE["naloxone_to"]]
    out = {"arrival": rows[0], "at_antagonist_stop": peak, "end": rows[-1],
           "kinetics": "RECURRENCE_KINETICS_UNSET (synthetic rates only)"}
    out["pass"] = (peak["availability"] > rows[0]["availability"] and rows[-1]["availability"] < peak["availability"]
                   and rows[-1]["paco2"] > peak["paco2"] and rows[-1]["spo2"] < peak["spo2"]
                   and _records_only_availability(records))
    return out


def collapse_direction() -> dict:
    """Structural only: a severe synthetic deepening lowers delivery through the oxygenation; no opioid collapse rule."""
    a, p = orf.anchors(orf.CASE), link_profile()
    states, _ = course((depression(SEVERE_DEEPENING_PER_MIN),), a, p, minutes=LONG_COURSE_MINUTES)
    rows = [_row(s, a, p) for s in states]
    collapse_text = (CORE_DIR / "collapse.py").read_text(encoding="utf-8").lower()
    out = {"delivery": [rows[0]["delivery"], rows[-1]["delivery"]], "spo2": [rows[0]["spo2"], rows[-1]["spo2"]],
           "D": [rows[0]["D"], rows[-1]["D"]], "paco2": [rows[0]["paco2"], rows[-1]["paco2"]],
           "no_opioid_collapse_rule": "opioid" not in collapse_text,
           "status": "STRUCTURAL_ONLY (no threshold calibrated; P2T-5's M2 floor applies at the deepest PaCO2)"}
    out["pass"] = (_nonincreasing([r["delivery"] for r in rows]) and rows[-1]["delivery"] < rows[0]["delivery"]
                   and rows[-1]["D"] > rows[0]["D"] and out["no_opioid_collapse_rule"])
    return out


# P2U-1-8 / -9 / -11 / -12: HR, consciousness, oxygen, acid-base -------------------------------------------------------------------

def heart_rate(region: dict) -> dict:
    out = {c: {"authored": region[c]["authored"]["hr"], "model_band": region[c]["hr_band"],
               "within": region[c]["authored_hr_in_band"]} for c in orf.CASES}
    for c in orf.CASES:
        low, high = out[c]["model_band"]
        out[c]["residual_bpm"] = 0.0 if out[c]["within"] else (out[c]["authored"] - low if out[c]["authored"] < low
                                                               else out[c]["authored"] - high)
    gaps = [c for c in orf.CASES if not out[c]["within"]]
    out["gap"] = ("OPIOID_HR_FAMILY_GAP: " + ", ".join(f"{c} {out[c]['residual_bpm']:+.2f} bpm outside the common band"
                                                       for c in gaps)) if gaps else "none"
    out["opioid_hr_term"] = False
    out["rule"] = "diagnostic: the authored HR against the model HR over the common intrinsic-HR band; a residual is " \
                  "carried, never patched (no opioid HR term)"
    out["pass"] = out["opioid_hr_term"] is False
    return out


def consciousness() -> dict:
    out = {}
    for case in orf.CASES:
        t = orf.truth(case)
        a = orf.anchors(case)
        states, _ = course((naloxone(),), a, link_profile())
        levels = [dv.derive(s, a, link_profile()).consciousness_level for s in states]
        out[case] = {"authored": t["mental_status"], "neurological_exam": t["neurological_exam"],
                     "arrival_level": levels[0], "levels_under_naloxone": sorted(set(levels)),
                     "reading": "the ADOPTED ladder reads SpO2 only; the toxidrome (obtundation, small pupils) and "
                                "hypercapnic encephalopathy are not separated: CONSCIOUSNESS_INTEGRATION_DEBT"}
    out["N_written"] = False
    out["pass"] = all(out[c]["arrival_level"] == orf.LEVEL_OF[out[c]["authored"]] for c in orf.CASES)
    return out


def oxygen() -> dict:
    a, p = orf.anchors(orf.CASE), link_profile()
    s0 = dv.arrival_state(a, p)
    air, o2 = dv.derive(s0, a, p).spo2, dv.derive(s0.evolve(fio2=FIO2_PROBE), a, p).spo2
    states_air, _ = course((depression(),), a, p)
    worse = states_air[-1]
    masked = dv.derive(worse.evolve(fio2=FIO2_PROBE), a, p).spo2
    out = {"room_air": air, "fio2_0.4": o2, "hypoventilating_room_air": dv.derive(worse, a, p).spo2,
           "hypoventilating_fio2_0.4": masked, "rule": "the common FiO2 rule (spo2_per_fio2 30), no opioid gain",
           "debt": "FIO2_RESPONSE_MAGNITUDE_DEBT", "paco2_unchanged_by_fio2": dv.respiration(worse.evolve(fio2=FIO2_PROBE), a, p).paco2
           == dv.respiration(worse, a, p).paco2}
    out["pass"] = o2 > air and masked > out["hypoventilating_room_air"] and out["paco2_unchanged_by_fio2"]
    return out


def acid_base() -> dict:
    out = {}
    for case in orf.CASES:
        a = orf.anchors(case)
        states, _ = course((naloxone(),), a, link_profile())
        r0, r1 = dv.respiration(states[0], a, link_profile()), dv.respiration(states[-1], a, link_profile())
        out[case] = {"ph": [r0.ph, r1.ph], "paco2": [r0.paco2, r1.paco2], "hco3": [r0.bicarbonate, r1.bicarbonate],
                     "burden": [r0.acid_burden, r1.acid_burden]}
    out["rule"] = "pH from the common PaCO2 and HCO3 (P2K-2); no opioid acid-base rule"
    out["pass"] = all(out[c]["ph"][1] > out[c]["ph"][0] and out[c]["hco3"][0] == out[c]["hco3"][1] for c in orf.CASES)
    return out


# Interface audit (the common change) --------------------------------------------------------------------------------------------

def interface_audit() -> dict:
    changed = {}
    for relative in ("clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py",
                     "clinical_core/provenance.py"):
        old, new = om._function_dumps(p2t5_text(relative)), om._function_dumps(_live(relative))
        changed[relative] = {"added": sorted(set(new) - set(old)),
                             "changed": sorted(k for k in old if k in new and old[k] != new[k])}
    readers = sorted(n for n, f in mc._functions(_live("clinical_core/derived.py")).items()
                     if "central_availability" in mc._names(f) or "arrival_central_availability" in mc._names(f))
    out = {"functions": changed, "availability_readers": readers,
           "aux_fields_new": sorted(set(_aux_fields_live()) - set(dm._class_fields(p2t5_text("clinical_core/state.py"),
                                                                                    "AuxiliaryState"))),
           "anchor_fields_new": sorted(set(dm._class_fields(_live("clinical_core/state.py"), "Anchors"))
                                       - set(dm._class_fields(p2t5_text("clinical_core/state.py"), "Anchors"))),
           "profile_fields_new": sorted(set(dm._class_fields(_live("clinical_core/derived.py"), "CoreProfile"))
                                        - set(dm._class_fields(p2t5_text("clinical_core/derived.py"), "CoreProfile"))),
           "rr_formula": "expressed RR = (profile availability x state availability) x excitatory RR (P2P-2's form)"}
    out["pass"] = (out["aux_fields_new"] == [NEW_AUX] and out["anchor_fields_new"] == [NEW_ANCHOR]
                   and not out["profile_fields_new"]
                   and changed["clinical_core/derived.py"]["added"] == ["central_availability"]
                   and set(changed["clinical_core/derived.py"]["changed"]) == {"_composition", "arrival_drive_composition",
                                                                               "arrival_state",
                                                                               "respiratory_drive_composition"}
                   and set(readers) == {"_composition", "arrival_drive_composition", "arrival_state",
                                        "respiratory_drive_composition"})
    return out


def _aux_fields_live() -> list:
    return dm._class_fields(_live("clinical_core/state.py"), "AuxiliaryState")


def non_regression() -> dict:
    """With no opioid writer: P2T-5's record reproduced on its tree (which nests P2T-3 and every earlier closed record),
    and the committed profiles' arrival availability 1."""
    with p2t5_view():
        p2t5 = om.run()
    record = json.loads(om.RECORD.read_text(encoding="utf-8"))
    out = {"p2t5_record_reproduced_on_its_tree": json.loads(json.dumps(p2t5, sort_keys=True, default=str)) == record,
           "p2t5_record_untouched": hashlib.sha256(om.RECORD.read_bytes()).hexdigest() == P2T5_RECORD_SHA,
           "p2t5_verdict": p2t5["readiness"]["verdict"],
           "committed_arrival_availability_1": all(dv.arrival_state(a, p).aux.central_availability == 1.0
                                                   for a, p in om.committed_pairs().values())}
    out["pass"] = (out["p2t5_record_reproduced_on_its_tree"] and out["p2t5_record_untouched"]
                   and out["committed_arrival_availability_1"])
    return out


# The proof: the P2T-5 tree plus P2U-1's declared insertions -------------------------------------------------------------------

P2T5_HEAD = "98a2bb0"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                        "clinical_core/oxygenation_link.py", '
                                     '"clinical_core/oxygenation_link_report.py",\n'
                                     '                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                        "clinical_core/oxygenation_link.py", '
                                     '"clinical_core/oxygenation_link_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('AUXILIARY_SOURCES["respiratory_distress"] = RESPIRATORY_DISTRESS\n'
                               "#: P2U-1: the core's sum of the families' availability changes into the common "
                               'central respiratory drive availability\n'
                               '#: (the arrival value plus every change since). It adds no kinetics and no coupling '
                               'of its own.\n'
                               'CENTRAL_AVAILABILITY = Source(SourceKind.CORE_COUPLING, "central_availability")\n'
                               'AUXILIARY_SOURCES["central_availability"] = CENTRAL_AVAILABILITY\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n',
                               'AUXILIARY_SOURCES["respiratory_distress"] = RESPIRATORY_DISTRESS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n'),
                              ('def _composition(intrinsic: float, acid: float, spo2: float | None, profile: '
                               'CoreProfile,\n'
                               '                 distress: float = 0.0, central: float = 1.0) -> DriveComposition:\n'
                               '    hypoxaemic, excitatory = 0.0, acid\n',
                               'def _composition(intrinsic: float, acid: float, spo2: float | None, profile: '
                               'CoreProfile,\n'
                               '                 distress: float = 0.0) -> DriveComposition:\n'
                               '    hypoxaemic, excitatory = 0.0, acid\n'),
                              ('    excitatory_rr = rate_from_drive(excitatory, intrinsic, profile)\n'
                               "    # P2U-1: the profile's structural value times the state's common central "
                               'availability (1 unless a family writes it).\n'
                               '    availability = central_availability(profile, central)\n'
                               '    return DriveComposition(intrinsic, acid, spo2, hypoxaemic, excitatory, '
                               'excitatory_rr, availability,\n'
                               '                            expressed_respiratory_rate(excitatory_rr, availability), '
                               'distress_drive)\n'
                               '\n'
                               '\n'
                               'def central_availability(profile: CoreProfile, central: float) -> float:\n'
                               '    """P2U-1: the central drive availability the composition expresses: the '
                               "profile's structural value (P2P-2, 1 except in\n"
                               "    synthetic probes) times the state's common central availability (1 unless a "
                               'family writes it). With both at 1 it is\n'
                               '    1 exactly; nothing here chooses a value."""\n'
                               '    return profile.central_drive_availability * central\n'
                               '\n',
                               '    excitatory_rr = rate_from_drive(excitatory, intrinsic, profile)\n'
                               '    availability = profile.central_drive_availability\n'
                               '    return DriveComposition(intrinsic, acid, spo2, hypoxaemic, excitatory, '
                               'excitatory_rr, availability,\n'
                               '                            expressed_respiratory_rate(excitatory_rr, availability), '
                               'distress_drive)\n'
                               '\n'),
                              ('    if not state.R.pulse_present:\n'
                               '        return DriveComposition(intrinsic, acid, None, 0.0, acid, 0.0,\n'
                               '                                central_availability(profile, '
                               'state.aux.central_availability), 0.0)\n'
                               '    spo2 = _perfusion(state, anchors, profile)[2] if '
                               'profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic, acid, spo2, profile, '
                               'state.aux.respiratory_distress, state.aux.central_availability)\n'
                               '\n',
                               '    if not state.R.pulse_present:\n'
                               '        return DriveComposition(intrinsic, acid, None, 0.0, acid, 0.0, '
                               'profile.central_drive_availability, 0.0)\n'
                               '    spo2 = _perfusion(state, anchors, profile)[2] if '
                               'profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic, acid, spo2, profile, '
                               'state.aux.respiratory_distress)\n'
                               '\n'),
                              ('                        respiratory_drive(arrival_acid_burden(anchors, profile), '
                               'profile), spo2, profile,\n'
                               '                        anchors.arrival_respiratory_distress, '
                               'anchors.arrival_central_availability)\n'
                               '\n',
                               '                        respiratory_drive(arrival_acid_burden(anchors, profile), '
                               'profile), spo2, profile,\n'
                               '                        anchors.arrival_respiratory_distress)\n'
                               '\n'),
                              ('    check_distress_respiratory_effect(profile, '
                               'anchors.arrival_respiratory_distress)\n'
                               '    if anchors.arrival_central_availability != 1.0 and profile.acid_to_drive_gain is '
                               'None:\n'
                               '        raise CoreInvariantError("an arrival central drive availability other than 1 '
                               'needs the P2K-2 acid-base physiology "\n'
                               '                                 "(P2U-1); nothing else reads it")\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n',
                               '    check_distress_respiratory_effect(profile, '
                               'anchors.arrival_respiratory_distress)\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n'),
                              ('                                            '
                               'mechanics_efficiency=anchors.arrival_mechanics_efficiency,\n'
                               '                                            '
                               'respiratory_distress=anchors.arrival_respiratory_distress,\n'
                               '                                            '
                               'central_availability=anchors.arrival_central_availability))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n',
                               '                                            '
                               'mechanics_efficiency=anchors.arrival_mechanics_efficiency,\n'
                               '                                            '
                               'respiratory_distress=anchors.arrival_respiratory_distress))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n')),
 'clinical_core/integration.py': (('                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n',
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n'),
                                  ('    distress: tuple[DistressChange, ...] = ()  # changes to the common '
                                   'respiratory distress this minute (P2T-1)\n'
                                   '    availability: tuple[AvailabilityChange, ...] = ()  # changes to the common '
                                   'central availability this minute (P2U-1)\n'
                                   '\n',
                                   '    distress: tuple[DistressChange, ...] = ()  # changes to the common '
                                   'respiratory distress this minute (P2T-1)\n'
                                   '\n'),
                                  ('                              "DistressChange records")\n'
                                   '    if not isinstance(contribution.availability, tuple) or any(not '
                                   'isinstance(item, AvailabilityChange)\n'
                                   '                                                               for item in '
                                   'contribution.availability):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the central drive '
                                   'availability changes only by a tuple of "\n'
                                   '                              "AvailabilityChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n',
                                   '                              "DistressChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n'),
                                  ('    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress\n'
                                   '                 + contribution.availability):\n'
                                   '        if item.source != contributor.source:\n',
                                   '    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress):\n'
                                   '        if item.source != contributor.source:\n'),
                                  ('    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    availability = []\n'
                                   '    internal = {}\n',
                                   '    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    internal = {}\n'),
                                  ('        distress.extend(contribution.distress)\n'
                                   '        availability.extend(contribution.availability)\n'
                                   '        if contribution.internal is not None:\n',
                                   '        distress.extend(contribution.distress)\n'
                                   '        if contribution.internal is not None:\n'),
                                  ('                                                                                         '
                                   'for item in mechanics),\n'
                                   '                         respiratory_distress=_distress_after(state, distress, '
                                   'profile, minute),\n'
                                   '                         central_availability=_availability_after(state, '
                                   'availability, profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n',
                                   '                                                                                         '
                                   'for item in mechanics),\n'
                                   '                         respiratory_distress=_distress_after(state, distress, '
                                   'profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n'),
                                  ('                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress), '
                                   'availability=tuple(availability))\n'
                                   '    _check_conservation(state, new_state, record)\n',
                                   '                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress))\n'
                                   '    _check_conservation(state, new_state, record)\n'),
                                  ('\n'
                                   'def _availability_after(state: CoreState, availability: list, profile: '
                                   'CoreProfile, minute: int) -> float:\n'
                                   '    """P2U-1: the central drive availability after the minute: the value it '
                                   "starts with plus the minute's changes. The\n"
                                   '    core adds no kinetics and no coupling of its own. With the acid-base '
                                   'physiology off nothing reads it, so a change is\n'
                                   '    refused; a minute that would take it outside 0 to 1 is refused, never '
                                   'held."""\n'
                                   '    if availability and profile.acid_to_drive_gain is None:\n'
                                   '        raise ProvenanceError(f"minute {minute}: {availability[0].source.key} '
                                   'changed the central drive availability "\n'
                                   '                              "while the P2K-2 acid-base physiology is off '
                                   '(P2U-1): nothing would read it")\n'
                                   '    value = availability_sum(state.aux.central_availability, [item.amount for '
                                   'item in availability])\n'
                                   '    if not 0.0 <= value <= 1.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the central drive availability '
                                   'changes take it to {value!r}, outside 0 "\n'
                                   '                              "to 1 (P2U-1)")\n'
                                   '    return value\n'
                                   '\n'
                                   '\n'
                                   'def availability_sum(before: float, amounts) -> float:\n'
                                   '    """P2U-1: the central drive availability after a minute\'s changes, summed '
                                   "once (math.fsum, order-free). As P2T-1A's\n"
                                   '    distress sum at 0, a value outside 0 to 1 by no more than the roundoff of '
                                   'the operands (math.ulp(1.0) times the sum of\n'
                                   '    their magnitudes) cannot be told from the bound and is the bound exactly; '
                                   'beyond that it is returned as it is and\n'
                                   '    refused by the caller. No clinical threshold: the bounds are the domain and '
                                   'floating-point precision."""\n'
                                   '    terms = (before, *amounts)\n'
                                   '    value = math.fsum(terms)\n'
                                   '    roundoff = math.ulp(1.0) * math.fsum(abs(term) for term in terms)\n'
                                   '    if value < 0.0 and -value <= roundoff:\n'
                                   '        return 0.0\n'
                                   '    if value > 1.0 and value - 1.0 <= roundoff:\n'
                                   '        return 1.0\n'
                                   '    return value + 0.0\n'
                                   '\n'
                                   '\n'
                                   'def _check_conservation(before: CoreState, after: CoreState, record: '
                                   'MinuteRecord) -> None:\n',
                                   '\n'
                                   'def _check_conservation(before: CoreState, after: CoreState, record: '
                                   'MinuteRecord) -> None:\n'),
                                  ('        raise ProvenanceError("the respiratory distress changed by other than '
                                   'its recorded changes")\n'
                                   '    if after.aux.central_availability != '
                                   'availability_sum(before.aux.central_availability,\n'
                                   '                                                          [item.amount for item '
                                   'in record.availability]):\n'
                                   "        # P2U-1: the availability moves by exactly the minute's recorded "
                                   'changes, never otherwise.\n'
                                   '        raise ProvenanceError("the central drive availability changed by other '
                                   'than its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n',
                                   '        raise ProvenanceError("the respiratory distress changed by other than '
                                   'its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                      "clinical_core/oxygenation_link_report.py",\n'
                                     '                      "clinical_core/opioid_migration_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                      "clinical_core/oxygenation_link_report.py")\n'
                                     '\n'),),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class AvailabilityChange:\n'
                                  '    """P2U-1: one source\'s change to the common central respiratory drive '
                                  'availability in one minute.\n'
                                  '\n'
                                  '    The amount adds to the availability the minute starts with (finite; 0 changes '
                                  'nothing), as a distress change adds to\n'
                                  '    the distress. It stays where its writers leave it: it never moves, back to '
                                  'arrival or anywhere else, without a change\n'
                                  '    that names its source, and the core adds no kinetics of its own. The '
                                  'availability is a common input, never a drug\n'
                                  '    term: a family declares what its own process (a depressant, an antagonist) '
                                  'does to it, and the core only sums the\n'
                                  '    changes. A minute whose changes would take it outside 0 to 1 is refused. No '
                                  'amount is approved; with the acid-base\n'
                                  '    physiology off a change is refused, because nothing would read it.\n'
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n'
                                  '    source: Source\n'
                                  '    minute: int\n'
                                  '    description: str\n'
                                  '\n'
                                  '    def __post_init__(self):\n'
                                  '        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, '
                                  'float)) \\\n'
                                  '                or not math.isfinite(self.amount):\n'
                                  '            raise ProvenanceError(f"an availability change is a finite number, '
                                  'not {self.amount!r}")\n'
                                  '        object.__setattr__(self, "amount", float(self.amount))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every availability change names its Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "availability", "amount": self.amount, "source": '
                                  'self.source.to_dict(), "minute": self.minute,\n'
                                  '                "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AuxiliaryChange:\n',
                                  '@dataclass(frozen=True)\nclass AuxiliaryChange:\n'),
                                 ('    distress: tuple[DistressChange, ...] = field(default=())\n'
                                  '    availability: tuple[AvailabilityChange, ...] = field(default=())\n'
                                  '\n',
                                  '    distress: tuple[DistressChange, ...] = field(default=())\n\n'),
                                 ('        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress + '
                                  'self.availability):\n'
                                  '            if item.minute != self.minute:\n',
                                  '        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress):\n'
                                  '            if item.minute != self.minute:\n'),
                                 ('                "mechanics": [item.to_dict() for item in self.mechanics],\n'
                                  '                "distress": [item.to_dict() for item in self.distress],\n'
                                  '                "availability": [item.to_dict() for item in self.availability]}\n'
                                  '\n',
                                  '                "mechanics": [item.to_dict() for item in self.mechanics],\n'
                                  '                "distress": [item.to_dict() for item in self.distress]}\n'
                                  '\n')),
 'clinical_core/state.py': (('                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2",\n'
                             '                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress",\n'
                             '                              "arrival_central_availability"),\n'
                             '}\n',
                             '                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2",\n'
                             '                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress"),\n'
                             '}\n'),
                            ('    arrival_respiratory_distress: float = 0.0\n'
                             '    # P2U-1 candidate input, read only by the P2K-2 drive composition (the acid-base '
                             'physiology on) and outside the\n'
                             "    # case-parameter / migration registry, as P2S-2's and P2T-1's: the arrival central "
                             'respiratory drive availability, a\n'
                             '    # case / family latent arrival state (never read from the disease label), 0 (no '
                             'spontaneous drive) to 1 (no central\n'
                             '    # depression). 1, the default, is none; no other value is approved.\n'
                             '    arrival_central_availability: float = 1.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    arrival_respiratory_distress: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the arrival respiratory distress is finite and '
                             'at or above 0 (P2T-1)")\n'
                             '        if isinstance(self.arrival_central_availability, bool) or not '
                             'isinstance(self.arrival_central_availability,\n'
                             '                                                                                (int, '
                             'float)) \\\n'
                             '                or not 0.0 <= self.arrival_central_availability <= 1.0:\n'
                             '            raise CoreInvariantError("the arrival central drive availability is '
                             'between 0 and 1 (P2U-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the arrival respiratory distress is finite and '
                             'at or above 0 (P2T-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'),
                            ('                            "central depression; 0 and constant while both of its '
                             'readers are UNSET",\n'
                             '    "central_availability": "the common central respiratory drive availability '
                             '(P2U-1): the share of the excitatory "\n'
                             '                            "respiratory drive the central machinery expresses, 0 (no '
                             'spontaneous drive) to 1 (no central "\n'
                             '                            "depression), multiplying the profile\'s structural value; '
                             'the case\'s latent arrival value plus "\n'
                             '                            "every family change since '
                             '(provenance.AvailabilityChange); not the drive, RR, W, PaCO2, "\n'
                             '                            "SpO2, mechanics, distress, consciousness or N; 1 and '
                             'constant unless a family writes it",\n'
                             '}\n',
                             '                            "central depression; 0 and constant while both of its '
                             'readers are UNSET",\n'
                             '}\n'),
                            ('    respiratory_distress: float = 0.0\n    central_availability: float = 1.0\n\n',
                             '    respiratory_distress: float = 0.0\n\n'),
                            ('            raise CoreInvariantError("the respiratory distress is never negative")\n'
                             '        if not 0.0 <= self.central_availability <= 1.0:\n'
                             '            # P2U-1: 0 is no spontaneous drive, 1 no central depression; nothing is '
                             'above 1.\n'
                             '            raise CoreInvariantError("the central drive availability is between 0 and '
                             '1")\n'
                             '\n',
                             '            raise CoreInvariantError("the respiratory distress is never negative")\n'
                             '\n'))}
CORE_AT_P2T5 = {'clinical_core/decision_pack.py': '8fce930b62974effb2601a8b2ee55524db8d33fd601ff5cca99248c3d5c45f16',
 'clinical_core/derived.py': 'b84a87a44392fec273eef37d65fb5a94cf00a19805a529ed2dccfbd5f2797951',
 'clinical_core/integration.py': '8640b4621cb2d6946d4606f9938f9310c7481d5866d919070bb7b89e6b193c0f',
 'clinical_core/lactate_slice.py': '397d3be87424205db1403486fe635013744f096d6f4e76074461e73d272e8aa6',
 'clinical_core/provenance.py': '619a4cba9c0b8d3c7d41de29165dfaab9ead59627c77fe3daab21e21c5bec2f4',
 'clinical_core/state.py': '90194bf77313fe178123e986b69378cfeeafe1e12531e382e79a71c0be5d0487'}
# </reversal>
# <common>
COMMON_AT_P2T5 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
 'clinical_core/a9.py': '64006b57e37ab69dd9dfd61d5c87b01112779f19e7007b96440cfad345ad5b92',
 'clinical_core/acid_base.py': '9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954',
 'clinical_core/acid_base_report.py': '9f0b9f5b03369066e4ac7916b372453c41ef7793b36c20553b88d726b83afa78',
 'clinical_core/acs_migration.py': '4fae25400e94b7c1f3b6b77f277dd5e04b72d150c52da738faddf95b37edd971',
 'clinical_core/acs_migration_report.py': 'dbe33c01e165f9471dcb720919c3fac257f3d0903972117a420e91632b4c2d6b',
 'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/arrival_severity.py': 'c5c0e4c125303b463ec1d2a5373464c09576f7d83ca975834e6b059c67b2b229',
 'clinical_core/arrival_severity_report.py': 'a1806dc772a4f0a540a621271e8dd24b4c77b36da2b55af5e1da623cf30ac2eb',
 'clinical_core/asthma_distress_migration.py': 'feacb1fc6bc5cc29fd76fa4584b22fa16476aec6e685880dab4fd15264b2e168',
 'clinical_core/asthma_distress_migration_report.py': '81925051cca752dc9a37c1cc79b82ffc14ca1c3484c90b40c238ead1a545f315',
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
 'clinical_core/oxygenation_link.py': 'e6cf3ce8ed5bdce43573ea35dab45df141eb251e744c07f765d43e0e230bc824',
 'clinical_core/oxygenation_link_report.py': 'c621080d5bfae14df8e920f6095b82abce84b007c591579ac6c33f09b82b9e59',
 'clinical_core/pressure_tone.py': '2e350c8a42bcacfa31e8e5349d284c7d276808e396d36421e1dc369dbcb9ec26',
 'clinical_core/pressure_tone_filter.py': '54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650',
 'clinical_core/pressure_tone_filter_report.py': '6eebe11b816eeb901f10d9f1431182b71ab26db84652771af741076f33734f92',
 'clinical_core/pressure_tone_report.py': 'bc0fe73c681a35432baec5acf8062027b63f0e5821146133fb9211ae9240d7ac',
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
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>
P2T5_FREEZE_DIGEST = "3a042f0fabeecff58f97e198fc3d65cb878eeada63d01039c89d0e0564798f2e"
P2T5_RECORD_SHA = "87b753188255c28d0ae159bb30ca785dd7cb44c948d56ffcac26997ad2c7f8a3"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2T5[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2T5.items()}


def p2t5_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2T-5 file plus P2U-1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2t5_bytes(relative: str) -> bytes:
    return p2t5_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2t5_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN and k not in FAMILY_FILES}
    for relative, sha in CORE_AT_P2T5.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


#: The closed packages whose hash list of unchanged files still reads the live bytes on the P2T-5 tree, so each must read
#: P2U-1's changed files as P2T-5 left them. Every other closed package's list is already redirected by its own newer
#: neighbour's chain (respiratory_mechanics, respiratory_distress, respiratory_drive and oxygenation_link do that), and
#: those readers compose the whole chain of reversals, which this one must not override.
CLOSED_COMMON = ("oxygenation_link", "distress_closure")


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2t5_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


def _om_p2t3_bytes(relative: str) -> bytes:
    """P2T-5's p2t3_bytes on the P2T-5 tree: its own reversed files from the P2T-5 text, every other file's P2T-5 bytes."""
    return om.p2t3_text(relative).encode("utf-8") if relative in om.REVERSAL else p2t5_bytes(relative)


def _om_common_ok(names) -> bool:
    return all(hashlib.sha256(p2t5_bytes(n)).hexdigest() == om.COMMON_AT_P2T3[n] for n in names)


class _TreeFile:
    """One of P2U-1's changed files as P2T-5 left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2t5_text(self.relative)

    def read_bytes(self):
        return p2t5_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


_NEW_FILES = OWN + FAMILY_FILES + (REPORT,)
#: P2U-1's own modules: their path readers are never redirected (they read the live tree, as the newest package must).
_OWN_MODULES = ("clinical_core.opioid_migration", "clinical_core.opioid_migration_report",
                "clinical_core.opioid_reference", "clinical_core.modules.opioid")


def _old_only(paths) -> list:
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in _NEW_FILES]


class _TreeDir:
    """A closed package's ``ROOT`` or ``CORE_DIR`` (or a directory under either): the P2T-5 text of P2U-1's changed
    files, the live path of anything else, and its listings without P2U-1's new files. Only the path arithmetic a closed
    module does is supported; anything else delegates to the live path."""

    def __init__(self, path=CORE_DIR):
        self.path = path

    def __truediv__(self, name):
        target = self.path / name
        relative = target.relative_to(ROOT).as_posix() if ROOT in target.parents or target == ROOT else None
        if relative in REVERSAL:
            return _TreeFile(relative)
        return _TreeDir(target) if target.is_dir() else target

    def glob(self, pattern):
        return iter(_old_only(sorted(self.path.glob(pattern))))

    def rglob(self, pattern):
        return iter(_old_only(sorted(self.path.rglob(pattern))))

    def __getattr__(self, name):
        return getattr(self.path, name)

    def __fspath__(self):
        return str(self.path)


def without_new_keys(value):
    """A closed record's view of a live serialization: P2U-1's new arrival anchor (in an Anchors dict, naming its case)
    and new auxiliary field (in an AuxiliaryState dict) dropped where they hold their reference 1, and a minute record's
    empty availability list dropped; anything else as it is (then the earlier packages' own view)."""
    if isinstance(value, dict):
        if "case_id" in value and NEW_ANCHOR in value:
            if value[NEW_ANCHOR] != 1.0:
                raise AssertionError("a closed course read a new candidate input away from its reference")
            value = {k: v for k, v in value.items() if k != NEW_ANCHOR}
        if NEW_AUX in value and "mechanics_efficiency" in value and "respiratory_distress" in value:
            if value[NEW_AUX] != 1.0:
                raise AssertionError("a closed course moved the central availability")
            value = {k: v for k, v in value.items() if k != NEW_AUX}
        if "availability" in value and "distress" in value and "mechanics" in value and value["availability"] == []:
            value = {k: v for k, v in value.items() if k != "availability"}
        return {k: without_new_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_new_keys(v) for v in value]
    return value


#: Every closed analysis module whose listings of the representation (``fields``, the auxiliary fields, ``dataclasses``)
#: must read P2U-1's new field and anchor as P2T-5 left them. Their ``_live`` needs no patch: each is redirected by its
#: own newer neighbour's chain, and the newest (``oxygenation_link``) reads the P2T-5 text here.
CLOSED_LIVE = ("oxygenation_link", "asthma_distress_migration", "distress_closure", "respiratory_distress",
               "asthma_migration", "respiratory_mechanics", "embolism_migration", "respiratory_drive",
               "edema_migration", "lung_water_reference")
#: P2U-1's new names, dropped where a closed listing of the representation reads them.
NEW_NAMES = (NEW_AUX, NEW_ANCHOR)


def _fields_at_p2t5(cls):
    """dataclasses.fields as the tree a closed package was frozen against had them: Anchors without P2U-1's new arrival
    anchor, AuxiliaryState without its new field (both at their reference 1 in every closed course), and then P2T-5's own
    filter (CoreProfile without its new field), so the two compose whichever chain is applied last."""
    return tuple(f for f in om._fields_at_p2t3(cls) if f.name not in NEW_NAMES)


def _raw_fields_at_p2t5(cls):
    """Only P2U-1's own filter: dataclasses.fields without its new field and anchor. The composed ``_fields_at_p2t5``
    would recurse here through P2T-5's filter, which reads this one."""
    return tuple(f for f in dataclasses.fields(cls) if f.name not in NEW_NAMES)


class _DataclassesAtP2T5:
    """``dataclasses`` as a closed module sees it on the P2T-5 tree: ``fields`` filtered, everything else untouched."""

    fields = staticmethod(_raw_fields_at_p2t5)

    def __getattr__(self, name):
        return getattr(dataclasses, name)


_DM_WITHOUT = dm.without_new_keys
#: The auxiliary fields as P2T-5 left them: P2U-1's one new field (1 in every closed course) out.
P2T5_AUXILIARY_FIELDS = {k: v for k, v in mc.AUXILIARY_FIELDS.items() if k != NEW_AUX}
#: The auxiliary sources as P2T-5 left them: P2U-1's one new core coupling out. Patched only so a closed listing of the
#: representation reads it as P2T-5 did; no closed course writes an availability change, so nothing looks the source up.
P2T5_AUXILIARY_SOURCES = {k: v for k, v in dv.AUXILIARY_SOURCES.items() if k != NEW_AUX}
_FREEZE_SOURCES = bf.freeze_sources


def _dm_without(value):
    return _DM_WITHOUT(without_new_keys(value))


def _closed_registry(registry: dict) -> dict:
    return {k: v for k, v in registry.items() if k not in FAMILY_TYPES}


#: Every closed analysis module that reads a core file by path (a ``ROOT``, ``CORE_DIR``, ``CORE`` or
#: ``CANDIDATE_SOURCE`` of its own) rather than through its ``_live``: on the P2T-5 tree each must read P2U-1's changed
#: files as P2T-5 left them, and list clinical_core without P2U-1's new files.
PATH_READERS = ("acid_base", "acs_migration", "arrival_severity", "asthma_distress_migration", "asthma_migration",
                "baroreflex", "blood_anchors", "blood_constraints", "blood_extension", "blood_fluid_calibration",
                "blood_fluid_readiness", "blood_fluid_tau_closure", "blood_probes", "blood_rate_boundary",
                "calibration", "collapse_architecture", "collapse_audit", "consciousness_audit", "contracts_shadow",
                "decision_pack_markdown", "distress_closure", "edema_migration", "embolism_migration",
                "encephalopathy_architecture", "faculty_constraints", "gas_exchange_architecture", "gi_reference",
                "haemorrhage_probes", "hemodynamic_probes", "hr_envelope_filter", "hr_observables", "hr_primary",
                "hr_shock", "hr_structure", "lactate_adequacy", "lactate_closure", "lactate_constraints",
                "lactate_rebuild", "lactate_slice", "lung_water_reference", "migration_authority", "oxygen_probes",
                "oxygenation_link", "pressure_tone", "pressure_tone_filter", "respiratory_distress",
                "respiratory_drive", "respiratory_mechanics", "respiratory_monotonicity", "rr_audit", "shadow",
                "vascular_tone", "ventilation_filter", "ventilation_surface")


def _imported_closed_modules() -> list:
    """The closed analysis modules whose path readers a closed view must redirect, imported by name (never through the
    interpreter's module table, so the shadow core imports nothing a shadow does not need)."""
    out = []
    for name in PATH_READERS:
        out.append(__import__(f"clinical_core.{name}", fromlist=["ROOT"]))
    return out


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2T-5's view reads the P2T-5 files (proven) and their bytes, its captured
    source map is P2T-5's; the closed listings of the auxiliary state and the closed serializations read them as P2T-5 left
    them (P2U-1's new field and anchor at their reference 1 out, an empty availability list out); the closed registry views
    hold no opioid type. P2U-1 changes no behaviour without an opioid writer or a declared availability."""
    patch.setattr(om, "_live", p2t5_text)
    patch.setattr(om, "tm_common_ok", _om_common_ok)
    for module_name in CLOSED_COMMON:
        module = __import__(f"clinical_core.{module_name}", fromlist=["common_untouched"])
        patch.setattr(module, "common_untouched", _closed_common_untouched(module))
    # Every closed analysis module that reads a core file by path (not through its own ``_live``) reads the P2T-5 text,
    # and its listings of clinical_core leave P2U-1's new files out: the tree as P2T-5 left it.
    for module in _imported_closed_modules():
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            if isinstance(getattr(module, attribute, None), Path):
                patch.setattr(module, attribute, _TreeDir(getattr(module, attribute)))
    for module_name in CLOSED_LIVE:
        module = __import__(f"clinical_core.{module_name}", fromlist=["_live"])
        if hasattr(module, "fields"):
            # P2T-5 is the newest closed package: its own listings still see its new profile field, only P2U-1's names
            # go. Every older package's listing composes both filters, whichever chain is applied last.
            patch.setattr(module, "fields", _raw_fields_at_p2t5 if module is om else _fields_at_p2t5)
        if hasattr(module, "dataclasses"):
            patch.setattr(module, "dataclasses", _DataclassesAtP2T5())
        if hasattr(module, "AUXILIARY_FIELDS"):
            # Composed with whatever a newer chain already put there (P2T-1's view drops the distress), so the order the
            # chains are applied in does not matter.
            patch.setattr(module, "AUXILIARY_FIELDS",
                          {k: v for k, v in module.AUXILIARY_FIELDS.items() if k != NEW_AUX})
    patch.setattr(om, "p2t3_bytes", _om_p2t3_bytes)
    patch.setattr(om, "_FREEZE_SOURCES", lambda: p2t5_sources(_FREEZE_SOURCES()))
    patch.setattr(dv, "AUXILIARY_SOURCES", P2T5_AUXILIARY_SOURCES)
    # P2T-1's own snapshot of the auxiliary fields (taken at import, so it holds P2U-1's new field).
    patch.setattr(dm, "P2S3_AUXILIARY_FIELDS", {k: v for k, v in dm.P2S3_AUXILIARY_FIELDS.items() if k != NEW_AUX})
    patch.setattr(dm, "without_new_keys", _dm_without)
    patch.setattr(mc, "without_new_anchor_key", _dm_without)
    for module_name in ("edema_migration", "lung_water_reference", "embolism_migration"):
        module = __import__(f"clinical_core.{module_name}", fromlist=["_REGISTRY"])
        if hasattr(module, "_REGISTRY"):
            patch.setattr(module, "_REGISTRY", _closed_registry(module._REGISTRY))


def tree(patch) -> None:
    """The whole P2T-5 tree, for P2T-5's own analysis and tests: the chain, the source map, and P2T-3's reader (which read
    the live tree while P2T-5 was the live tree) reading the P2T-5 files."""
    chain(patch)
    patch.setattr(bf, "freeze_sources", lambda: p2t5_sources(_FREEZE_SOURCES()))


class p2t5_view:
    """P2T-5's analysis reading the tree P2T-5 froze, for its own proofs and its record."""

    def __enter__(self):
        self._patch = mc._Patch()
        tree(self._patch)
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2t5_view():
        digest = om.freeze_digest()
        proof = om.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2t5_freeze_digest": digest == P2T5_FREEZE_DIGEST,
            "p2t5_proof": all(proof["proofs"].values()) and all(proof["common_untouched"].values())
            and proof["p2t3_freeze_digest"] and proof["p2t3_proof"] and proof["p2t3_record"],
            "p2t5_record": hashlib.sha256(om.RECORD.read_bytes()).hexdigest() == P2T5_RECORD_SHA}


# Readiness (predeclared) ------------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "central depression maps cleanly to the common availability (non-empty arrival region at every carried intrinsic "
    "RR for both cases, arrival exact, G / L / distress neutral)",
    "the RR / W / PaCO2 / SpO2 cascade works (U1-U4)",
    "no G is required without lung pathology (U7, arrival G 0)",
    "the distress stays inactive (U6)",
    "naloxone reverses the common cascade structurally (U5, both cases; the recurrence direction for 67f)",
    "the common equations are unchanged but the declared availability interface; no opioid term, no direct scripting, "
    "mechanics untouched (U8-U11, interface audit)",
    "prior respiratory families unchanged (U12: P2T-5's record on its tree, every other file proven)",
)
READY = "OPIOID_SHADOW_MIGRATION_READY"
NOT_READY = "OPIOID_SHADOW_MIGRATION_NOT_READY"
READINESS_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def readiness(found: dict) -> dict:
    p, proof = found["probes"], found["proof"]
    cases = orf.CASES
    checks = (
        found["arrival_region"]["pass"] and found["channel_map"]["pass"],
        all(p[c]["U"]["U1"] and p[c]["U"]["U2"] and p[c]["U"]["U3"] and p[c]["U"]["U4"] for c in cases),
        all(p[c]["U"]["U7"] for c in cases) and found["channel_map"]["pass"],
        all(p[c]["U"]["U6"] for c in cases),
        all(p[c]["U"]["U5"] for c in cases) and found["recurrence"]["pass"],
        all(p[c]["U"]["U8"] and p[c]["U"]["U9"] for c in cases) and p["U10"]["pass"] and p["U11"]["pass"]
        and found["interface"]["pass"],
        found["non_regression"]["pass"] and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2t5_freeze_digest"] and proof["p2t5_proof"] and proof["p2t5_record"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    return {"criteria": rows, "blocker": blocker, "rule": READINESS_RULE,
            "verdict": READY if blocker is None else f"{NOT_READY} - {blocker}"}


def design() -> dict:
    return {"decisions": DECISIONS, "deepening_per_min": DEEPENING_PER_MIN, "naloxone": NALOXONE,
            "recurrence": RECURRENCE, "severe_deepening_per_min": SEVERE_DEEPENING_PER_MIN,
            "course_minutes": COURSE_MINUTES, "long_course_minutes": LONG_COURSE_MINUTES, "fio2_probe": FIO2_PROBE,
            "points": list(POINTS), "synthetic_r": om.SYNTHETIC_R,
            "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2t5": CORE_AT_P2T5, "common_at_p2t5": COMMON_AT_P2T5,
            "p2t5": {"head": P2T5_HEAD, "freeze_digest": P2T5_FREEZE_DIGEST, "record": P2T5_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2t5": hashlib.sha256(om.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    region = arrival_region()
    found = {"proof": upstream_unchanged(), "case_truth": case_truth(), "legacy": legacy(), "channel_map": channel_map(),
             "arrival_region": region, "interface": interface_audit(), "probes": probes(), "contrast": contrast(),
             "recurrence": recurrence(), "collapse": collapse_direction(), "heart_rate": heart_rate(region),
             "consciousness": consciousness(), "oxygen": oxygen(), "acid_base": acid_base(),
             "non_regression": non_regression()}
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
    text = json.dumps(run(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
