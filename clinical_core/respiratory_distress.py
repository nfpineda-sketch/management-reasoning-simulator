"""P2T-1: the minimum common respiratory distress architecture (shadow only, inert by default).

Faculty decision after P2T-0X (B, SEPARATE_RESPIRATORY_DISTRESS_AND_GENERAL_AROUSAL_SIGNALS_SUPPORTED): one common
auxiliary input, ``aux.respiratory_distress`` (non-chemical respiratory afferent / distress activation, 0 none, no upper
bound), HYBRID: a case / family latent arrival value (``Anchors.arrival_respiratory_distress``) plus additive family
changes (``provenance.DistressChange``). Two independent readers, both UNSET (None) by default:
- ``distress_to_respiratory_drive_gain`` adds gain x distress to the excitatory respiratory drive with the acid and
  hypoxaemic drives, before the common saturation; the central drive availability still gates what is expressed;
- ``distress_to_sympathetic_gain`` adds its own gain x distress to the sympathetic target, through the common
  saturation and beta-blockade.
No mechanics -> distress coupling is active (the slot is UNSET and off), no WOB mapping exists, no hypoxaemic value is
chosen, systemic stress is SYSTEMIC_STRESS_DEFERRED, and no family writes distress yet (asthma is not remigrated).

This module freezes the probes D1-D12, the case contrasts, the WOB ordering test, the mechanics / distress orthogonality,
the parameter state, the default non-regression and the proof that every other common file is P2S-3's, before the one
evaluation run. Every gain, distress value and band here is SYNTHETIC_ONLY; nothing is approved.
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
from . import asthma_migration as sm
from . import asthma_reference as sr
from . import bands
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import edema_migration as pe
from . import edema_reference as er
from . import embolism_migration as em
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import respiratory_drive as rd
from . import respiratory_mechanics as mc
from .integration import Contribution, Contributor, step
from .provenance import DistressChange, ProvenanceError, SourceKind
from .state import AUXILIARY_FIELDS, CASE_PARAMETERS, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2T-1"
DECIDED = "2026-11-04"
OWN = ("clinical_core/respiratory_distress.py",)
REPORT = "clinical_core/respiratory_distress_report.py"
RECORD = ROOT / "docs" / "revision" / "P2T1_respiratory_distress.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2T1_DISTRES_RESPIRATORIO_COMUN.md"
#: The two registry tuples gain this package's entries (proven against P2S-3's files below).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py", "clinical_core/state.py", "clinical_core/integration.py",
              "clinical_core/provenance.py")
#: P2T-1's new candidate input in the anchors (outside the case-parameter registry, as P2S-2's).
NEW_ANCHOR_KEY = "arrival_respiratory_distress"
CANDIDATE_INPUTS = (NEW_ANCHOR_KEY,)
NEW_PROFILE_FIELDS = ("distress_to_respiratory_drive_gain", "distress_to_sympathetic_gain")

DECISIONS = {
    "classification": "B, SEPARATE_RESPIRATORY_DISTRESS_AND_GENERAL_AROUSAL_SIGNALS_SUPPORTED (P2T-0X, accepted)",
    "rr_gap": "RR_GAP_RESPIRATORY_DISTRESS_DOMINANT",
    "hr_gap": "HR_GAP_MULTIFACTORIAL",
    "scope": "respiratory_distress only; systemic_stress / general arousal SYSTEMIC_STRESS_DEFERRED; no asthma "
             "remigration",
    "representation": "an auxiliary common input, never a canonical V/T/P/R/L/G/W/D/N channel",
    "hybrid": "arrival: a case / family latent value constrained by independent authored respiratory evidence; "
              "evolution: family DistressChange writes; no automatic derivation (never 1 - mechanics efficiency)",
    "wob": "authored work of breathing is evidence for ordering only: no universal numeric mapping, no approved value",
    "mechanics_coupling": "a future structural slot only: magnitude UNSET, default off, not implemented as active",
    "respiratory_reader": "distress_to_respiratory_drive_gain, UNSET; before the existing saturation; availability "
                          "unchanged as the expression gate",
    "acid_composition": "the existing common composition before saturation; no family exception",
    "hypoxaemic_drive": "mapping and gain UNSET, unchanged (identifiability of chemical vs non-chemical drive)",
    "sympathetic_reader": "distress_to_sympathetic_gain, UNSET; a separate gain; deficit, debt, baroreflex, "
                          "saturation and beta-blockade preserved",
    "central_depression": "no gate on the sympathetic reader is added",
}

SEMANTICS = {
    "represents": "non-chemical respiratory afferent / distress activation: the mismatch between respiratory demand and "
                  "the ability of the respiratory system to meet it, plus respiratory / pulmonary afferent stress the gas "
                  "chemistry does not carry (asthma, pulmonary oedema, pulmonary embolism, pneumonia)",
    "does_not_represent": ["SpO2", "PaCO2", "pH", "respiratory rate", "the work-of-breathing observable",
                           "mechanics efficiency", "G", "L", "oxygen deficit", "D", "shock", "pain",
                           "anxiety in general", "systemic stress", "central respiratory depression"],
    "state": "aux.respiratory_distress: finite, at or above 0, 0 none, no upper bound (no clinical bound is chosen)",
    "arrival": "Anchors.arrival_respiratory_distress: a case / family latent arrival value, 0 by default; refused "
               "other than 0 unless a reader is declared",
    "writer": "Contribution.distress: provenance.DistressChange(amount, source, minute, description); amounts add to "
              "the value the minute starts with (the distress has no reference above 0 to scale, so the convention "
              "is a channel delta's, not the mechanics factor's); a minute that would take it below 0 is refused; "
              "refused while both readers are UNSET",
    "core_kinetics": "none: the integration sums the minute's declared changes only (source "
                     "core_coupling:respiratory_distress)",
    "respiratory_reader": "excitatory drive = acid + hypoxaemic + distress_to_respiratory_drive_gain x distress, then "
                          "the common saturation (rate_from_drive), then the central drive availability",
    "sympathetic_reader": "sympathetic target += distress_to_sympathetic_gain x the absolute distress (never relative to "
                          "arrival), before max(0, .), then the common saturation and beta-blockade "
                          "(sympathetic_increment)",
    "observable": "WOB_OBSERVABLE_MAPPING_DEFERRED: no observable reads the distress",
    "systemic_stress": "SYSTEMIC_STRESS_DEFERRED: pain, hypoglycaemic counter-regulation, coronary stress, fever and "
                       "agitation / anxiety have no state or gain here",
}

# Synthetic, predeclared values (SYNTHETIC_ONLY, never approved) --------------------------------------------------------------

RESPIRATORY_GAIN = 1.0          # breaths/min-equivalent per distress unit
SYMPATHETIC_GAIN = 0.05         # sympathetic drive per distress unit
OTHER_GAINS = (2.0, 0.01)       # a second, different pair for D4
DISTRESS_GRID = (0.0, 2.5, 5.0, 10.0)
PROBE_DISTRESS = 5.0
AVAILABILITIES = (1.0, 0.5, 0.0)
OPIOID_AVAILABILITY = 0.3       # P2S-2's central-drive-failure reading (mc.probe of the opioid contrast)
ACID_BICARBONATE = 18.0         # an acid burden of 6 mEq/L (D10)
HYPOXAEMIC_SPO2 = 80.0          # a severe hypoxaemia (D7)
HYPOXAEMIC_GAIN = rd.SYNTHETIC_GAINS[1]
LOW_EFFICIENCY = mc.LOW_EFFICIENCY
MECHANICS_FACTOR = mc.MECHANICS_FACTOR
DISTRESS_STEP = 1.0             # one scripted writer: +1 per minute (D9)
COURSE_MINUTES = 10
BETA_BLOCKADES = (0.0, 0.5, 1.0)
PROBE_ANCHORS = replace(mc.PROBE_ANCHORS, case_id="p2t1_distress_probe")   # RR 16 and HR 80 read as intrinsic, MAP 90


def readers(profile: dv.CoreProfile, respiratory: float | None = RESPIRATORY_GAIN,
            sympathetic: float | None = SYMPATHETIC_GAIN) -> dv.CoreProfile:
    return replace(profile, distress_to_respiratory_drive_gain=respiratory, distress_to_sympathetic_gain=sympathetic)


def base_profile() -> dv.CoreProfile:
    """P2S-2's probe profile: the ACS common point, acid-base on, gas-exchange reference, mechanics candidate on."""
    return mc.base_profile()


def probe_anchors(**changes):
    """The probe anchors with the given changes; a changed case parameter is declared a synthetic probe value."""
    declared = {**dict(PROBE_ANCHORS.declared), **{k: "synthetic_probe" for k in changes if k in CASE_PARAMETERS}}
    return replace(PROBE_ANCHORS, declared=declared, **changes)


@dataclass(frozen=True)
class SyntheticDistress(Contributor):
    """SYNTHETIC_ONLY: a scripted distress writer, the amount every minute in (start, stop]. Not a family writer, not
    registered (no replay needed)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2t1_probe_distress"

    id: str
    amount: float
    start_minute: int = 0
    stop_minute: int = 10 ** 6

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(distress=(DistressChange(self.amount, self.source, minute,
                                                     "probe: declared change of the respiratory distress"),))


def course(items, minutes, anchors, profile):
    return an.course(tuple(items), minutes, anchors, profile)


def reading(state, anchors, profile) -> dict:
    """One state's reading: the composition, the RR, the HR and every quantity the distress must not move directly."""
    c = dv.respiratory_drive_composition(state, anchors, profile)
    d = dv.derive(state, anchors, profile)
    r = dv.respiration(state, anchors, profile)
    return {"distress": state.aux.respiratory_distress, "acid_drive": c.acid_drive,
            "hypoxaemic_drive": c.hypoxaemic_drive, "distress_drive": c.distress_drive,
            "excitatory_drive": c.excitatory_drive, "excitatory_rr": c.excitatory_rr, "availability": c.availability,
            "rr": c.expressed_rr, "sympathetic_target": dv.sympathetic_target(state, anchors, profile),
            "sympathetic_drive": state.aux.sympathetic_drive, "hr": d.pulse_rate_bpm, "W": r.ventilation,
            "paco2": r.paco2, "ph": r.ph, "spo2": d.spo2, "mechanics_efficiency": state.aux.mechanics_efficiency,
            "G": state.G, "L": state.L, "D": state.D, "lactate": d.lactate, "map": d.map, "P": state.P, "V": state.V,
            "T": state.T}


def at_arrival(anchors, profile) -> dict:
    return reading(dv.arrival_state(anchors, profile), anchors, profile)


def _increasing(values) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


#: What a distress change may move, by reader (P2T-1-5 D9): the RR's consequences (W, PaCO2, pH) through the respiratory
#: reader, the HR (and the drive behind it) through the sympathetic reader; nothing else.
RESPIRATORY_CONSEQUENCES = ("distress", "distress_drive", "excitatory_drive", "excitatory_rr", "rr", "W", "paco2", "ph")
SYMPATHETIC_CONSEQUENCES = ("distress", "sympathetic_target", "sympathetic_drive", "hr")
NEVER_MOVED = ("spo2", "G", "L", "mechanics_efficiency", "D", "lactate", "map", "P", "V", "T")


# P2T-1-1: the insertion points, read from the code -----------------------------------------------------------------------------

def audit() -> dict:
    """Who reads the distress and its gains, what the readers read, and that the integration only sums changes."""
    funcs = mc._functions((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    every = _every_function((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    readers_of = sorted({n for n, f in every if "respiratory_distress" in mc._names(f)})
    arrival_readers = sorted({n for n, f in every if NEW_ANCHOR_KEY in mc._names(f)})
    gain_readers = {g: sorted({n for n, f in every if g in mc._names(f) or g in _strings(f)})
                    for g in NEW_PROFILE_FIELDS}
    calls = sorted(ast.unparse(node.args[4]) for node in ast.walk(ast.parse((CORE_DIR / "derived.py").read_text(
        encoding="utf-8"))) if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_composition"
        and len(node.args) == 5)
    integration = mc._functions((CORE_DIR / "integration.py").read_text(encoding="utf-8"))
    after = integration["_distress_after"]
    out = {
        "distress_readers": readers_of,
        "arrival_distress_readers": arrival_readers,
        "gain_readers": gain_readers,
        "composition_distress_arguments": calls,
        "composition_distress_reads": sorted(mc._names(funcs["_composition"]) & {"spo2", "mechanics_efficiency",
                                                                                "acid", "distress"}),
        "sympathetic_target_new_reads": sorted(mc._names(funcs["sympathetic_target"])
                                               & {"respiratory_distress", "distress_to_sympathetic_gain",
                                                  "central_drive_availability", "respiratory_drive_composition",
                                                  "mechanics_efficiency", "ventilation", "paco2"}),
        "increment_reads_beta_blockade": "beta_blockade" in mc._names(funcs["sympathetic_increment"]),
        "integration_distress_reads": sorted(mc._names(after) & {"mechanics_efficiency", "spo2", "G", "L", "W",
                                                                 "oxygen_demand", "respiratory_distress", "amount"}),
        "integration_sums": [ast.unparse(n) for n in ast.walk(integration["step"]) if isinstance(n, ast.keyword)
                             and n.arg == "respiratory_distress"],
        "insertion_points": {
            "respiratory_drive": "derived._composition: excitatory = acid (+ hypoxaemic) (+ gain x distress), then "
                                 "rate_from_drive (saturation), then x central_drive_availability "
                                 "(expressed_respiratory_rate)",
            "arrival_drive": "derived.arrival_drive_composition: the anchors' arrival distress",
            "state_drive": "derived.respiratory_drive_composition: the state's aux.respiratory_distress",
            "sympathetic": "derived.sympathetic_target: after the acute-deficit, pressure, debt, hypoxaemia and "
                           "hypoglycaemia terms, before the baroreflex and max(0, .); beta-blockade downstream in "
                           "sympathetic_increment",
            "arrival_state": "derived.arrival_state: aux.respiratory_distress from the anchors, before the arrival "
                             "sympathetic target is read",
            "integration": "integration.step: Contribution.distress collected, summed by _distress_after, recorded in "
                           "MinuteRecord.distress, conserved by _check_conservation",
            "declared_unwired": "sympathetic_target's docstring: hypercapnia, pain or agitation, fever, withdrawal "
                                "(no state); hypoxaemia and hypoglycaemia relative to arrival (unchanged)",
        },
    }
    out["pass"] = (readers_of == ["respiratory_drive_composition", "sympathetic_target"]
                   and arrival_readers == ["arrival_drive_composition", "arrival_state"]
                   and gain_readers["distress_to_respiratory_drive_gain"] == ["__post_init__", "_composition",
                                                                              "respiratory_distress_read"]
                   and gain_readers["distress_to_sympathetic_gain"] == ["__post_init__", "respiratory_distress_read",
                                                                        "sympathetic_target"]
                   and "distress_drive" in mc._names(funcs["_composition"])
                   and calls == ["anchors.arrival_respiratory_distress", "state.aux.respiratory_distress"]
                   and out["sympathetic_target_new_reads"] == ["distress_to_sympathetic_gain", "respiratory_distress"]
                   and out["increment_reads_beta_blockade"]
                   and out["integration_distress_reads"] == ["amount", "respiratory_distress"]
                   and out["integration_sums"] == ["respiratory_distress=_distress_after(state, distress, profile, "
                                                   "minute)"])
    return out


def _every_function(text: str) -> list:
    return [(n.name, n) for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)]


def _strings(node) -> set:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


# P2T-1-2 / -3: representation and writer ---------------------------------------------------------------------------------------

def _refused(build, error=(CoreInvariantError, ProvenanceError)) -> bool:
    try:
        build()
    except error:
        return True
    return False


def representation() -> dict:
    on = readers(base_profile())
    off = base_profile()
    a = probe_anchors()
    state = dv.arrival_state(a, on)
    added = {"CoreProfile": sorted(set(f.name for f in fields(dv.CoreProfile))
                                   - set(f.name for f in fields(p2s3_core().CoreProfile))),
             "AuxiliaryState": sorted(set(AUXILIARY_FIELDS) - set(_p2s3_fields("clinical_core/state.py",
                                                                               "AuxiliaryState"))),
             "Anchors": sorted(set(f.name for f in fields(type(a))) - set(_p2s3_fields("clinical_core/state.py",
                                                                                       "Anchors"))),
             "Contribution": sorted(set(_live_fields("clinical_core/integration.py", "Contribution"))
                                    - set(_p2s3_fields("clinical_core/integration.py", "Contribution"))),
             "MinuteRecord": sorted(set(_live_fields("clinical_core/provenance.py", "MinuteRecord"))
                                    - set(_p2s3_fields("clinical_core/provenance.py", "MinuteRecord")))}
    refusals = {
        "negative_state": _refused(lambda: replace(state.aux, respiratory_distress=-0.1)),
        "nan_state": _refused(lambda: replace(state.aux, respiratory_distress=float("nan"))),
        "negative_arrival": _refused(lambda: probe_anchors(arrival_respiratory_distress=-1.0)),
        "infinite_arrival": _refused(lambda: probe_anchors(arrival_respiratory_distress=float("inf"))),
        "arrival_without_reader": _refused(lambda: dv.arrival_state(probe_anchors(arrival_respiratory_distress=1.0),
                                                                    off)),
        "change_without_reader": _refused(lambda: step(dv.arrival_state(a, off), (SyntheticDistress("x", 1.0),), a,
                                                      off)),
        "change_below_zero": _refused(lambda: step(dv.arrival_state(a, on), (SyntheticDistress("x", -1.0),), a, on)),
        "amount_nan": _refused(lambda: DistressChange(float("nan"), PROBE_SOURCE, 1, "x")),
        "amount_boolean": _refused(lambda: DistressChange(True, PROBE_SOURCE, 1, "x")),
        "gain_zero": _refused(lambda: readers(base_profile(), 0.0, None)),
        "gain_negative": _refused(lambda: readers(base_profile(), None, -0.1)),
        "gain_boolean": _refused(lambda: readers(base_profile(), True, None)),
        "respiratory_gain_without_acid_base": _refused(lambda: replace(dv.DEFAULT_PROFILE,
                                                                       distress_to_respiratory_drive_gain=1.0)),
    }
    # Additive and persistent: a writer that stops leaves the distress where it left it; two writers sum.
    states, records = course((SyntheticDistress("a", 1.0, 0, 3), SyntheticDistress("b", 0.5, 0, 2)), 6, a, on)
    trail = [s.aux.respiratory_distress for s in states]
    sources = sorted({c.source.key for r in records for c in r.auxiliary if c.quantity == "respiratory_distress"})
    sympathetic_only = replace(dv.DEFAULT_PROFILE, distress_to_sympathetic_gain=SYMPATHETIC_GAIN)
    out = {"added_fields": added, "refused": refusals, "trail": trail,
           "records": [len(r.distress) for r in records], "aux_source": sources,
           "default_profile_reads": dv.respiratory_distress_read(dv.DEFAULT_PROFILE),
           "sympathetic_reader_without_acid_base": dv.respiratory_distress_read(sympathetic_only),
           "family_writers": sorted(str(p.relative_to(ROOT)) for p in (CORE_DIR / "modules").glob("*.py")
                                    if "DistressChange" in p.read_text(encoding="utf-8"))}
    out["pass"] = (added == {"CoreProfile": list(NEW_PROFILE_FIELDS), "AuxiliaryState": ["respiratory_distress"],
                             "Anchors": [NEW_ANCHOR_KEY], "Contribution": ["distress"], "MinuteRecord": ["distress"]}
                   and all(refusals.values()) and trail == [0.0, 1.5, 3.0, 4.0, 4.0, 4.0, 4.0]
                   and out["records"] == [2, 2, 1, 0, 0, 0] and sources == ["core_coupling:respiratory_distress"]
                   and not out["default_profile_reads"] and out["sympathetic_reader_without_acid_base"]
                   and not out["family_writers"])
    return out


PROBE_SOURCE = SyntheticDistress("p2t1", 0.0).source


def _class_fields(text: str, name: str) -> list:
    node = next(n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.ClassDef) and n.name == name)
    return [s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]


def _p2s3_fields(relative: str, name: str) -> list:
    return _class_fields(p2s3_text(relative), name)


def _live_fields(relative: str, name: str) -> list:
    return _class_fields(_live(relative), name)


# P2T-1-5: the structural probes D1-D12 ---------------------------------------------------------------------------------------

def _unset_reading(states, anchors, profile) -> list:
    return [reading(s, anchors, profile) for s in states]


def probe_d1() -> dict:
    """distress 0: the readers declared change no RR and no HR (every reference course re-read, one course re-run)."""
    courses = mc.reference_courses()
    same = {}
    for name, (states, anchors, prof) in courses.items():
        declared = readers(prof)
        same[name] = all(reading(s, anchors, prof) == reading(s, anchors, declared) for s in states)
    states, anchors, prof = courses["acs"]
    rerun = an.course(an.writers(), anchors=anchors, profile=readers(prof))[0]
    out = {"re_read": same, "re_run_states_equal": [s.to_dict() for s in rerun] == [s.to_dict() for s in states]}
    out["pass"] = all(same.values()) and out["re_run_states_equal"]
    return out


def _grid(profile, anchors=None) -> list:
    a = PROBE_ANCHORS if anchors is None else anchors
    return [at_arrival(replace(a, arrival_respiratory_distress=d), profile) for d in DISTRESS_GRID]


def probe_d2() -> dict:
    rows = _grid(readers(base_profile(), RESPIRATORY_GAIN, None))
    out = {"rows": rows, "excitatory": [r["excitatory_drive"] for r in rows], "rr": [r["rr"] for r in rows],
           "hr": [r["hr"] for r in rows],
           "sum": all(math.isclose(r["excitatory_drive"], r["acid_drive"] + RESPIRATORY_GAIN * r["distress"])
                      for r in rows)}
    out["pass"] = (_increasing(out["excitatory"]) and _increasing(out["rr"]) and len(set(out["hr"])) == 1
                   and out["sum"])
    return out


def probe_d3() -> dict:
    rows = _grid(readers(base_profile(), None, SYMPATHETIC_GAIN))
    out = {"rows": rows, "target": [r["sympathetic_target"] for r in rows], "hr": [r["hr"] for r in rows],
           "rr": [r["rr"] for r in rows]}
    out["pass"] = _increasing(out["target"]) and _increasing(out["hr"]) and len(set(out["rr"])) == 1
    return out


def probe_d4() -> dict:
    """Same distress, two gain pairs: the effectors move independently; an UNSET reader leaves its effector alone."""
    a = probe_anchors(arrival_respiratory_distress=PROBE_DISTRESS)
    base = at_arrival(PROBE_ANCHORS, base_profile())
    pairs = {"A": (RESPIRATORY_GAIN, SYMPATHETIC_GAIN), "B": OTHER_GAINS, "rr_only": (RESPIRATORY_GAIN, None),
             "hr_only": (None, SYMPATHETIC_GAIN)}
    rows = {k: at_arrival(a, readers(base_profile(), *g)) for k, g in pairs.items()}
    delta = {k: {"rr": r["rr"] - base["rr"], "hr": r["hr"] - base["hr"]} for k, r in rows.items()}
    out = {"pairs": {k: list(v) for k, v in pairs.items()}, "delta": delta}
    out["pass"] = (delta["B"]["rr"] > delta["A"]["rr"] > 0.0 and 0.0 < delta["B"]["hr"] < delta["A"]["hr"]
                   and delta["rr_only"]["hr"] == 0.0 and delta["hr_only"]["rr"] == 0.0
                   and delta["rr_only"]["rr"] == delta["A"]["rr"] and delta["hr_only"]["hr"] == delta["A"]["hr"])
    return out


def probe_d5() -> dict:
    a = probe_anchors(arrival_respiratory_distress=PROBE_DISTRESS)
    rows = [at_arrival(a, readers(replace(base_profile(), central_drive_availability=v), RESPIRATORY_GAIN, None))
            for v in AVAILABILITIES]
    out = {"availability": list(AVAILABILITIES), "rr": [r["rr"] for r in rows],
           "excitatory_rr": [r["excitatory_rr"] for r in rows], "distress": [r["distress"] for r in rows],
           "distress_drive": [r["distress_drive"] for r in rows]}
    out["pass"] = (all(math.isclose(r["rr"], v * r["excitatory_rr"]) for r, v in zip(rows, AVAILABILITIES))
                   and out["rr"][-1] == 0.0 and len(set(out["excitatory_rr"])) == 1
                   and set(out["distress"]) == {PROBE_DISTRESS} and len(set(out["distress_drive"])) == 1
                   and out["distress_drive"][0] > 0.0)
    return out


def probe_d6() -> dict:
    a = probe_anchors(arrival_respiratory_distress=PROBE_DISTRESS)
    rows = [at_arrival(a, readers(replace(base_profile(), central_drive_availability=v), None, SYMPATHETIC_GAIN))
            for v in AVAILABILITIES]
    base = at_arrival(PROBE_ANCHORS, base_profile())["hr"]
    out = {"availability": list(AVAILABILITIES), "hr": [r["hr"] for r in rows], "rr": [r["rr"] for r in rows],
           "hr_without_distress": base}
    out["pass"] = len(set(out["hr"])) == 1 and out["hr"][0] > base and out["rr"][-1] == 0.0
    return out


def probe_d7() -> dict:
    """distress 0 with severe hypoxaemia: nothing is read from SpO2 into the distress, at arrival or on a G course."""
    a = probe_anchors(spo2=HYPOXAEMIC_SPO2)
    unset, declared = base_profile(), readers(base_profile())
    worsening = (bands.Drift("p2t1-g", "G", 0, COURSE_MINUTES, mc.G_PER_MIN),)
    s_unset, r_unset = course(worsening, COURSE_MINUTES, a, unset)
    s_declared, r_declared = course(worsening, COURSE_MINUTES, a, declared)
    rows = [(reading(x, a, unset), reading(y, a, declared)) for x, y in zip(s_unset, s_declared)]
    out = {"arrival": rows[0][1], "spo2": [y["spo2"] for _, y in rows],
           "distress": [y["distress"] for _, y in rows], "distress_drive": [y["distress_drive"] for _, y in rows],
           "records": sum(len(r.distress) for r in r_declared),
           "same_rr_hr": all(x["rr"] == y["rr"] and x["hr"] == y["hr"] for x, y in rows)}
    out["pass"] = (set(out["distress"]) == {0.0} and set(out["distress_drive"]) == {0.0} and out["records"] == 0
                   and out["same_rr_hr"] and rows[0][1]["spo2"] == HYPOXAEMIC_SPO2
                   and out["spo2"][-1] < out["spo2"][0])
    return out


def probe_d8() -> dict:
    """distress 0 with low and falling mechanics: no distress is fabricated from the mechanics."""
    a = probe_anchors(arrival_mechanics_efficiency=LOW_EFFICIENCY)
    unset, declared = base_profile(), readers(base_profile())
    writer = (mc.SyntheticMechanics("m", MECHANICS_FACTOR),)
    s_unset, _ = course(writer, COURSE_MINUTES, a, unset)
    s_declared, r_declared = course(writer, COURSE_MINUTES, a, declared)
    rows = [(reading(x, a, unset), reading(y, a, declared)) for x, y in zip(s_unset, s_declared)]
    out = {"mechanics": [y["mechanics_efficiency"] for _, y in rows], "distress": [y["distress"] for _, y in rows],
           "paco2": [y["paco2"] for _, y in rows], "records": sum(len(r.distress) for r in r_declared),
           "same_rr_hr": all(x["rr"] == y["rr"] and x["hr"] == y["hr"] for x, y in rows)}
    out["pass"] = (set(out["distress"]) == {0.0} and out["records"] == 0 and out["same_rr_hr"]
                   and out["mechanics"][-1] < out["mechanics"][0] and _increasing(out["paco2"]))
    return out


def _moved(a_rows, b_rows) -> list:
    return sorted({k for x, y in zip(a_rows, b_rows) for k in x if x[k] != y[k]})


def probe_d9() -> dict:
    """A distress change alone moves only what its declared readers move."""
    a = PROBE_ANCHORS
    writer = (SyntheticDistress("d", DISTRESS_STEP),)
    out = {}
    for name, prof in (("sympathetic_reader", readers(base_profile(), None, SYMPATHETIC_GAIN)),
                       ("respiratory_reader", readers(base_profile(), RESPIRATORY_GAIN, None)),
                       ("both", readers(base_profile()))):
        without = [reading(s, a, prof) for s in course((), COURSE_MINUTES, a, prof)[0]]
        with_ = [reading(s, a, prof) for s in course(writer, COURSE_MINUTES, a, prof)[0]]
        ratio = all(math.isclose(x["W"] / x["rr"], y["W"] / y["rr"]) for x, y in zip(without, with_) if x["rr"])
        out[name] = {"moved": _moved(without, with_), "w_follows_rr_only": ratio}
    allowed = {"sympathetic_reader": set(SYMPATHETIC_CONSEQUENCES),
               "respiratory_reader": set(RESPIRATORY_CONSEQUENCES),
               "both": set(SYMPATHETIC_CONSEQUENCES) | set(RESPIRATORY_CONSEQUENCES)}
    out["never_moved"] = list(NEVER_MOVED)
    out["pass"] = (all(set(out[k]["moved"]) <= allowed[k] and not set(out[k]["moved"]) & set(NEVER_MOVED)
                       and out[k]["w_follows_rr_only"] for k in allowed)
                   and "hr" in out["sympathetic_reader"]["moved"] and "rr" not in out["sympathetic_reader"]["moved"]
                   and "rr" in out["respiratory_reader"]["moved"] and "hr" not in out["respiratory_reader"]["moved"])
    return out


def probe_d10() -> dict:
    """Acid and distress drives sum before the common saturation (not after it)."""
    prof = readers(base_profile(), RESPIRATORY_GAIN, None)
    a = probe_anchors(arrival_bicarbonate=ACID_BICARBONATE, arrival_respiratory_distress=PROBE_DISTRESS)
    r = at_arrival(a, prof)
    intrinsic = dv.intrinsic_respiratory_rate(a)
    after = (dv.rate_from_drive(r["acid_drive"], intrinsic, prof) + dv.rate_from_drive(r["distress_drive"], intrinsic,
                                                                                         prof) - intrinsic)
    out = {"acid_drive": r["acid_drive"], "distress_drive": r["distress_drive"], "excitatory": r["excitatory_drive"],
           "rr": r["rr"], "rr_if_summed_after_saturation": after,
           "ceiling": intrinsic + prof.rr_drive_saturation}
    out["pass"] = (r["acid_drive"] > 0.0 and r["distress_drive"] > 0.0
                   and r["excitatory_drive"] == r["acid_drive"] + r["distress_drive"]
                   and r["rr"] == dv.rate_from_drive(r["excitatory_drive"], intrinsic, prof)
                   and r["rr"] < after and r["rr"] < out["ceiling"])
    return out


def probe_d11() -> dict:
    """The hypoxaemic and distress terms are independently addressable: each present only when its own term is."""
    a = probe_anchors(spo2=rd.HYPOXAEMIC_SPO2, arrival_respiratory_distress=PROBE_DISTRESS)
    rows = {}
    for hyp in (False, True):
        for dis in (False, True):
            prof = rd.hypoxaemic(base_profile(), HYPOXAEMIC_GAIN) if hyp else base_profile()
            prof = readers(prof, RESPIRATORY_GAIN if dis else None, SYMPATHETIC_GAIN if dis else None)
            if not dis:
                rows[(hyp, dis)] = at_arrival(replace(a, arrival_respiratory_distress=0.0), prof)
            else:
                rows[(hyp, dis)] = at_arrival(a, prof)
    table = {f"hypoxaemic_{'on' if h else 'unset'}_distress_{'on' if d else 'unset'}":
             {k: r[k] for k in ("acid_drive", "hypoxaemic_drive", "distress_drive", "excitatory_drive", "rr")}
             for (h, d), r in rows.items()}
    out = {"table": table,
           "committed_hypoxaemic_unset": all(p.hypoxaemic_drive_mapping is None for p in committed_profiles().values())}
    r = rows
    out["pass"] = (r[(False, False)]["hypoxaemic_drive"] == 0.0 and r[(False, False)]["distress_drive"] == 0.0
                   and r[(True, False)]["hypoxaemic_drive"] > 0.0 and r[(True, False)]["distress_drive"] == 0.0
                   and r[(False, True)]["hypoxaemic_drive"] == 0.0 and r[(False, True)]["distress_drive"] > 0.0
                   and r[(True, True)]["hypoxaemic_drive"] == r[(True, False)]["hypoxaemic_drive"]
                   and r[(True, True)]["distress_drive"] == r[(False, True)]["distress_drive"]
                   and math.isclose(r[(True, True)]["excitatory_drive"], r[(True, True)]["acid_drive"]
                                    + r[(True, True)]["hypoxaemic_drive"] + r[(True, True)]["distress_drive"])
                   and out["committed_hypoxaemic_unset"])
    return out


# D12: the default reading is P2S-3's ---------------------------------------------------------------------------------------

def p2s3_core():
    """The P2S-3 derived.py (proven by the reversal), executed as its own module beside the live one."""
    name = "clinical_core._derived_at_p2s3"
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    exec(compile(p2s3_text("clinical_core/derived.py"), "derived_at_p2s3.py", "exec"), module.__dict__)
    return module


def _old_profile(old, profile):
    names = {f.name for f in fields(old.CoreProfile)}
    if any(getattr(profile, n) is not None for n in NEW_PROFILE_FIELDS):
        raise AssertionError("the comparison holds the P2T-1 readers UNSET")
    return old.CoreProfile(**{n: getattr(profile, n) for n in names})


def _composition_view(c) -> tuple:
    return (c.baseline_rr, c.acid_drive, c.spo2, c.hypoxaemic_drive, c.excitatory_drive, c.excitatory_rr,
            c.availability, c.expressed_rr)


def _same_reading(states, anchors, profile, old) -> bool:
    op = _old_profile(old, profile)
    for s in states:
        if dv.derive(s, anchors, profile).to_dict() != old.derive(s, anchors, op).to_dict():
            return False
        if dv.sympathetic_target(s, anchors, profile) != old.sympathetic_target(s, anchors, op):
            return False
        if dv.acid_base_active(profile) and (
                astuple(dv.respiration(s, anchors, profile)) != astuple(old.respiration(s, anchors, op))
                or _composition_view(dv.respiratory_drive_composition(s, anchors, profile))
                != _composition_view(old.respiratory_drive_composition(s, anchors, op))):
            return False
    if dv.acid_base_active(profile) and (dv.respiratory_rate_decomposition(anchors, profile)
                                         != old.respiratory_rate_decomposition(anchors, op)):
        return False
    return (dv.arrival_state(anchors, profile).to_dict() == old.arrival_state(anchors, op).to_dict()
            and dv.heart_rate_decomposition(anchors, profile) == old.heart_rate_decomposition(anchors, op))


def reference_courses() -> dict:
    """P2S-2's reference courses (GI, ACS, oedema, PE, P2P-2) and the P2S-3 asthma course, with the readers UNSET."""
    out = dict(mc.reference_courses())
    out["asthma_49m"] = (sm.course((sm.obstruction(),))[0], sr.anchors(), sm.profile())
    out["p2s2_mechanics"] = (course((mc.SyntheticMechanics("m", MECHANICS_FACTOR),), 30,
                                    probe_anchors(arrival_mechanics_efficiency=0.5), base_profile())[0],
                             probe_anchors(arrival_mechanics_efficiency=0.5), base_profile())
    return out


def probe_d12() -> dict:
    old = p2s3_core()
    courses = reference_courses()
    exact = {name: _same_reading(states, anchors, prof, old) for name, (states, anchors, prof) in courses.items()}
    distress_zero = {name: {s.aux.respiratory_distress for s in states} == {0.0}
                     for name, (states, _, _) in courses.items()}
    out = {"exact_reading_p2s3_core": exact, "distress_zero": distress_zero}
    out["pass"] = all(exact.values()) and all(distress_zero.values())
    return out


PROBES = {
    "D1": "distress 0: the readers declared change no RR and no HR",
    "D2": "distress > 0 with the respiratory reader: the excitatory drive (and RR) increases; HR unchanged",
    "D3": "distress > 0 with the sympathetic reader: the sympathetic target (and HR) increases; RR unchanged",
    "D4": "same distress, different gains: the effectors respond independently",
    "D5": "distress > 0 with the central drive availability reduced: RR expression suppressed, the distress present",
    "D6": "central depression does not suppress the sympathetic reader (no gate added)",
    "D7": "distress 0 with severe hypoxaemia: no distress contribution from SpO2",
    "D8": "distress 0 with low mechanics efficiency: no distress contribution from the mechanics",
    "D9": "a distress change alone moves only its readers' effectors (RR -> W, PaCO2, pH; HR)",
    "D10": "acid and distress drives compose before the existing saturation",
    "D11": "the hypoxaemic and distress drives remain independently addressable",
    "D12": "with both readers UNSET every prior candidate reading is exact (the P2S-3 core)",
}


def structural_probes() -> dict:
    found = {"D1": probe_d1(), "D2": probe_d2(), "D3": probe_d3(), "D4": probe_d4(), "D5": probe_d5(),
             "D6": probe_d6(), "D7": probe_d7(), "D8": probe_d8(), "D9": probe_d9(), "D10": probe_d10(),
             "D11": probe_d11(), "D12": probe_d12()}
    return {k: {"requires": PROBES[k], **v} for k, v in found.items()}


# P2T-1-6 / -7: case contrasts and the beta-blockade guard (synthetic distress on committed mappings) -----------------------

def _contrast(anchors, profile) -> dict:
    zero = at_arrival(anchors, readers(profile))
    some = at_arrival(replace(anchors, arrival_respiratory_distress=PROBE_DISTRESS), readers(profile))
    return {"distress_0": zero, "distress_synthetic": some, "rr_up": some["rr"] > zero["rr"],
            "hr_up": some["hr"] > zero["hr"]}


def contrasts() -> dict:
    edema = _contrast(er.anchors(), pe.profile())
    pe_61 = _contrast(mr.anchors(), em.profile())
    shock = dv.heart_rate_decomposition(mr.anchors(), readers(em.profile()))
    shock_with = dv.heart_rate_decomposition(replace(mr.anchors(), arrival_respiratory_distress=PROBE_DISTRESS),
                                             readers(em.profile()))
    pe_61["shock_terms_unchanged"] = all(shock[k] == shock_with[k] for k in ("acute_deficit_signal",
                                                                             "acute_unconstrained_bpm",
                                                                             "debt_unconstrained_bpm"))
    pe_61["target_rise_is_the_reader"] = math.isclose(
        pe_61["distress_synthetic"]["sympathetic_target"] - pe_61["distress_0"]["sympathetic_target"],
        SYMPATHETIC_GAIN * PROBE_DISTRESS)
    pe_33 = _contrast(mr.anchors(mr.SECONDARY), em.profile())
    asthma = _contrast(sr.anchors(), sm.profile())
    asthma["mechanics_unchanged"] = (asthma["distress_0"]["mechanics_efficiency"]
                                     == asthma["distress_synthetic"]["mechanics_efficiency"])
    opioid_profile = replace(base_profile(), central_drive_availability=OPIOID_AVAILABILITY)
    opioid_anchors = probe_anchors(spo2=HYPOXAEMIC_SPO2)
    opioid = {"declared": at_arrival(opioid_anchors, readers(opioid_profile)),
              "unset": at_arrival(opioid_anchors, opioid_profile)}
    opioid["no_forced_tachycardia_or_tachypnoea"] = (opioid["declared"]["hr"] == opioid["unset"]["hr"]
                                                     and opioid["declared"]["rr"] == opioid["unset"]["rr"]
                                                     and opioid["declared"]["rr"] < PROBE_ANCHORS.respiratory_rate)
    acs_unset, acs_declared = at_arrival(ar.anchors(), ar.common_profile()), at_arrival(ar.anchors(),
                                                                                         readers(ar.common_profile()))
    acs = {"authored_hr": ar.anchors().hr, "core_hr": acs_declared["hr"], "residual": ar.anchors().hr - acs_declared["hr"],
           "unchanged": acs_unset["hr"] == acs_declared["hr"], "status": "SYSTEMIC_STRESS_DEFERRED"}
    unresolved = {}
    for name, a in (("hypoglycaemia_like", _authored_hr(112.0, glucose=34.0)), ("pain_like", _authored_hr(94.0))):
        u, d = at_arrival(a, base_profile()), at_arrival(a, readers(base_profile()))
        unresolved[name] = {"authored_hr": a.hr, "core_hr": d["hr"], "unchanged": u["hr"] == d["hr"],
                            "residual": a.hr - d["hr"]}
    out = {"pulmonary_edema_58m": edema, "pulmonary_embolism_61m": pe_61, "pulmonary_embolism_33f": pe_33,
           "asthma_49m": asthma, "opioid_contrast": opioid, "acs_70f_left_main": acs,
           "systemic_stress_residuals": unresolved,
           "note": "SYNTHETIC distress and gains on the committed arrival mappings; no value is calibrated or approved"}
    out["pass"] = (edema["rr_up"] and edema["hr_up"] and pe_61["rr_up"] and pe_61["hr_up"]
                   and pe_61["shock_terms_unchanged"] and pe_61["target_rise_is_the_reader"]
                   and pe_33["rr_up"] and pe_33["hr_up"] and asthma["rr_up"] and asthma["hr_up"]
                   and asthma["mechanics_unchanged"] and opioid["no_forced_tachycardia_or_tachypnoea"]
                   and acs["unchanged"] and acs["residual"] > 0.0
                   and all(v["unchanged"] and v["residual"] > 0.0 for v in unresolved.values()))
    return out


def _authored_hr(hr: float, **changes):
    """SYNTHETIC_ONLY stand-ins for a non-respiratory arousal arrival: an authored HR above the intrinsic 80, distress 0."""
    return probe_anchors(hr=hr, rhythm=replace(PROBE_ANCHORS.rhythm, rate_bpm=hr), intrinsic_sinus_rate=80.0, **changes)


def beta_blockade() -> dict:
    """The distress's sympathetic contribution goes through the common sympathetic_increment, beta-blockade included."""
    prof = readers(base_profile(), None, SYMPATHETIC_GAIN)
    rows = {}
    for beta in BETA_BLOCKADES:
        a = probe_anchors(beta_blockade=beta)
        zero = at_arrival(a, prof)
        some = at_arrival(replace(a, arrival_respiratory_distress=PROBE_DISTRESS), prof)
        expected = dv.sympathetic_increment(some["sympathetic_drive"], dv.intrinsic_sinus_rate(a), beta, prof) \
            - dv.sympathetic_increment(zero["sympathetic_drive"], dv.intrinsic_sinus_rate(a), beta, prof)
        rows[beta] = {"hr_rise": some["hr"] - zero["hr"], "through_increment": math.isclose(some["hr"] - zero["hr"],
                                                                                           expected, abs_tol=1e-12)}
    out = {"rows": {str(k): v for k, v in rows.items()}}
    out["pass"] = (all(v["through_increment"] for v in rows.values())
                   and rows[0.0]["hr_rise"] > rows[0.5]["hr_rise"] > 0.0 and rows[1.0]["hr_rise"] == 0.0)
    return out


# P2T-1-8: WOB ordering (evidence only, no numeric mapping) ----------------------------------------------------------------------

ORDERING_FAMILIES = ("pulmonary_edema", "pulmonary_embolism", "asthma", "pneumonia")
FACULTY_ORDER = ("Normal", "Increased", "Marked", "Severe")
#: authored vocabulary -> the faculty's ordinal labels; anything else is reported outside the order.
WOB_LABELS = {"Normal": "Normal", "Increased": "Increased", "Markedly increased": "Marked", "Severe": "Severe"}
#: FAMILY_CANDIDATE / SYNTHETIC_ONLY ordinal regions on a unitless scale, predeclared, never approved: only the order
#: matters (any strictly increasing relabelling gives the same result).
CANDIDATE_REGIONS = {"Normal": (0.0, 0.0), "Increased": (0.0, 1.0), "Marked": (1.0, 2.0), "Severe": (2.0, None)}


def wob_ordering() -> dict:
    import clinical_cases
    cases = {c["id"]: c["observable"]["work_of_breathing"] for family in ORDERING_FAMILIES
             for c in clinical_cases.FAMILIES[family]["variants"]}
    labels = {k: WOB_LABELS.get(v) for k, v in cases.items()}
    rank = {k: FACULTY_ORDER.index(v) for k, v in labels.items() if v is not None}
    regions = [CANDIDATE_REGIONS[k] for k in FACULTY_ORDER]
    ordered_regions = all((b[0] >= a[1]) and (a[1] is not None) for a, b in zip(regions, regions[1:]))
    ids = sorted(rank)
    identified = sorted(f"{x} < {y}" for x in ids for y in ids if rank[x] < rank[y])
    ties = sorted({tuple(sorted(k for k in ids if rank[k] == r)) for r in set(rank.values())
                   if sum(1 for k in ids if rank[k] == r) > 1})
    prof = readers(base_profile())
    reps = {"Increased": 0.5, "Marked": 1.5, "Severe": 3.0}       # one SYNTHETIC point per open region
    monotone = [at_arrival(probe_anchors(arrival_respiratory_distress=v), prof) for v in (0.0,) + tuple(reps.values())]
    out = {"authored": cases, "labels": labels, "ranks": rank, "candidate_regions": CANDIDATE_REGIONS,
           "regions_strictly_ordered": ordered_regions, "outside_order": sorted(k for k, v in labels.items()
                                                                                 if v is None),
           "identified_pairs": len(identified), "ties": [list(t) for t in ties],
           "readers_preserve_order": _increasing([r["rr"] for r in monotone]) and _increasing([r["hr"] for r in
                                                                                                monotone]),
           "fitted_to_rr_or_hr": False, "status": "ORDINAL_EVIDENCE_ONLY; WOB_NUMERIC_MAPPING_UNSET"}
    out["non_empty_ordering"] = (not out["outside_order"] and ordered_regions and bool(rank))
    out["pass"] = out["non_empty_ordering"] and out["readers_preserve_order"]
    return out


# P2T-1-9: mechanics / distress orthogonality ----------------------------------------------------------------------------------

def orthogonality() -> dict:
    prof = readers(sm.profile())
    a = sr.anchors()
    same_e = {d: at_arrival(replace(a, arrival_respiratory_distress=d), prof) for d in (0.0, PROBE_DISTRESS)}
    band = sr.mechanics_band(sr.CASE)
    same_d = {e: at_arrival(replace(a, arrival_mechanics_efficiency=e, arrival_respiratory_distress=PROBE_DISTRESS),
                            prof) for e in (band.lower, band.upper)}
    lo, hi = same_d[band.lower], same_d[band.upper]
    out = {"same_mechanics": {str(k): {x: v[x] for x in ("distress_drive", "rr", "hr", "W", "paco2")}
                              for k, v in same_e.items()},
           "same_distress": {str(k): {x: v[x] for x in ("distress_drive", "excitatory_drive", "rr", "hr", "W",
                                                        "paco2")} for k, v in same_d.items()}}
    zero, some = same_e[0.0], same_e[PROBE_DISTRESS]
    out["pass"] = (some["rr"] > zero["rr"] and some["hr"] > zero["hr"]
                   and lo["distress_drive"] == hi["distress_drive"] and lo["excitatory_drive"] == hi["excitatory_drive"]
                   and lo["rr"] == hi["rr"] and lo["hr"] == hi["hr"] and lo["W"] < hi["W"] and lo["paco2"] > hi["paco2"])
    return out


# P2T-1-10 / -11 / -4: observable, parameters, systemic stress ----------------------------------------------------------------

def observable() -> dict:
    texts = {rel: _live(rel) for rel in CORE_FILES}
    out = {"wob_read_by_core": sorted(rel for rel, t in texts.items() if "work_of_breathing" in t),
           "derived_fields": sorted(f.name for f in fields(dv.Derived) if "distress" in f.name or "wob" in f.name),
           "status": "WOB_OBSERVABLE_MAPPING_DEFERRED"}
    out["pass"] = not out["wob_read_by_core"] and not out["derived_fields"]
    return out


def committed_profiles() -> dict:
    gi_anchors, gi_base, _ = go.ba.setup("gi_bleed_57m")
    return {"default": dv.DEFAULT_PROFILE, "gi": go._acid(gi_base), "acs": ar.common_profile(), "edema": pe.profile(),
            "pe": em.profile(), "asthma": sm.profile(), "p2p2_probe": rd.base_profile(), "p2s2_probe": base_profile()}


PARAMETER_STATUS = {
    "distress_to_respiratory_drive_gain": "UNSET (None); SYNTHETIC_ONLY in probes",
    "distress_to_sympathetic_gain": "UNSET (None); SYNTHETIC_ONLY in probes",
    "arrival_distress_regions": "UNSET; FAMILY_CANDIDATE ordinal regions only in the WOB ordering test",
    "wob_to_distress_mapping": "UNSET (no numeric mapping)",
    "mechanics_to_distress_coupling": "UNSET, off (no structural term is active)",
    "hypoxaemic_gain_and_mapping": "UNSET (unchanged)",
    "systemic_stress_writers_and_gains": "SYSTEMIC_STRESS_DEFERRED",
    "fever_effect": "UNSET (deferred)",
    "beta_agonist_hr_effect": "UNSET (deferred)",
    "pain_effect": "UNSET (deferred)",
    "hypoglycaemia_absolute_mapping": "UNSET (the arrival-relative term unchanged)",
    "approved": "none",
}


def parameter_state() -> dict:
    profiles = committed_profiles()
    anchors = {"pulmonary_edema_58m": er.anchors(), "acs_70f_left_main": ar.anchors(),
               "pulmonary_embolism_61m": mr.anchors(), "pulmonary_embolism_33f": mr.anchors(mr.SECONDARY),
               **{f"{case}_{point}": sr.anchors(case, point) for case in sr.CASES for point in sr.INTRINSIC_POINTS}}
    out = {"status": PARAMETER_STATUS,
           "profiles_unset": {k: all(getattr(p, n) is None for n in NEW_PROFILE_FIELDS) for k, p in profiles.items()},
           "arrival_distress_zero": {k: a.arrival_respiratory_distress == 0.0 for k, a in anchors.items()},
           "registry": {n: dv.PARAMETERS[n] for n in NEW_PROFILE_FIELDS}}
    out["pass"] = (all(out["profiles_unset"].values()) and all(out["arrival_distress_zero"].values())
                   and all(v[1].startswith("UNSET") for v in out["registry"].values()))
    return out


SYSTEMIC_STRESS_TOKENS = ("systemic_stress", "pain", "fever", "anxiety", "agitation", "hypoglycaem", "coronary")


def systemic_stress() -> dict:
    """No systemic-stress input leaked in: the new fields are the distress's only, and no new identifier names one."""
    added = representation_fields()
    names = [n for group in added.values() for n in group]
    out = {"new_identifiers": names, "status": "SYSTEMIC_STRESS_DEFERRED",
           "leaked": sorted(n for n in names if any(t in n.lower() for t in SYSTEMIC_STRESS_TOKENS))}
    out["pass"] = not out["leaked"]
    return out


def representation_fields() -> dict:
    return {"CoreProfile": sorted(set(f.name for f in fields(dv.CoreProfile))
                                  - set(f.name for f in fields(p2s3_core().CoreProfile))),
            "AuxiliaryState": sorted(set(AUXILIARY_FIELDS) - set(_p2s3_fields("clinical_core/state.py",
                                                                              "AuxiliaryState"))),
            "Anchors": sorted(set(_live_fields("clinical_core/state.py", "Anchors"))
                              - set(_p2s3_fields("clinical_core/state.py", "Anchors"))),
            "sources": sorted(set(dv.AUXILIARY_SOURCES) - set(p2s3_core().AUXILIARY_SOURCES))}


# P2T-1-12: default non-regression of the closed packages ---------------------------------------------------------------------

def without_new_keys(value):
    """A closed record's view of a live section: every serialized Anchors (a dict naming its case) loses P2S-2's and
    P2T-1's new candidate inputs, which must be at their references (1 and 0) there; anything else as it is."""
    if isinstance(value, dict):
        if "case_id" in value and (mc.NEW_ANCHOR_KEY in value or NEW_ANCHOR_KEY in value):
            if value.get(mc.NEW_ANCHOR_KEY, 1.0) != 1.0 or value.get(NEW_ANCHOR_KEY, 0.0) != 0.0:
                raise AssertionError("a closed course read a new candidate input away from its reference")
            value = {k: v for k, v in value.items() if k not in (mc.NEW_ANCHOR_KEY, NEW_ANCHOR_KEY)}
        return {k: without_new_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_new_keys(v) for v in value]
    return value


def non_regression() -> dict:
    """With both readers UNSET: the P2S-2 and P2S-3 records are reproduced live through the closed views (which nest
    P2Q-2, P2P-2, P2P-1, ACS and GI), and P2S-3's record file is byte-identical (its historical verdict untouched)."""
    with p2s3_view():
        p2s3 = sm.run()
        with sm.p2s2_view():
            p2s2 = mc.run()
    p2s2_record = json.loads(mc.RECORD.read_text(encoding="utf-8"))
    p2s3_record = json.loads(sm.RECORD.read_text(encoding="utf-8"))
    out = {"p2s2_record_reproduced": without_new_keys(go._plain(p2s2)) == p2s2_record,
           "p2s3_record_reproduced": without_new_keys(go._plain(p2s3)) == p2s3_record,
           "p2s3_record_untouched": hashlib.sha256(sm.RECORD.read_bytes()).hexdigest() == P2S3_RECORD_SHA,
           "p2s3_historical_verdict": p2s3_record["verdict"]["verdict"],
           "p2s3_classification": "ASTHMA_SHADOW_MIGRATION_NOT_READY - COMMON_CORE_BLOCKER_FOUND (COMMON_DRIVE_GAP); "
                                  "P2S3_FROZEN_VERDICT_DOCUMENTATION_DEBT"}
    out["pass"] = (out["p2s2_record_reproduced"] and out["p2s3_record_reproduced"] and out["p2s3_record_untouched"])
    return out


# The proof: the P2S-3 tree plus P2T-1's declared insertions -------------------------------------------------------------------

P2S3_HEAD = "ce78b5d"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/respiratory_mechanics.py", '
                                     '"clinical_core/respiratory_mechanics_report.py",\n'
                                     '                        "clinical_core/asthma_migration.py", '
                                     '"clinical_core/asthma_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_distress.py", '
                                     '"clinical_core/respiratory_distress_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/respiratory_mechanics.py", '
                                     '"clinical_core/respiratory_mechanics_report.py",\n'
                                     '                        "clinical_core/asthma_migration.py", '
                                     '"clinical_core/asthma_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('AUXILIARY_SOURCES["mechanics_efficiency"] = RESPIRATORY_MECHANICS\n'
                               "#: P2T-1: the core's sum of the families' distress changes into the common "
                               'respiratory distress (the arrival value plus\n'
                               '#: every change since). It adds no kinetics and no coupling of its own. Read only '
                               'when a profile declares a reader.\n'
                               'RESPIRATORY_DISTRESS = Source(SourceKind.CORE_COUPLING, "respiratory_distress")\n'
                               'AUXILIARY_SOURCES["respiratory_distress"] = RESPIRATORY_DISTRESS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n',
                               'AUXILIARY_SOURCES["mechanics_efficiency"] = RESPIRATORY_MECHANICS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n'),
                              ('    respiratory_mechanics: bool = False\n'
                               '    # P2T-1: the two independent readers of the common respiratory distress '
                               '(aux.respiratory_distress, non-chemical\n'
                               '    # respiratory afferent / distress activation; 0 none), both UNSET (None) by '
                               'default, so the distress is read by\n'
                               "    # nothing and every value is P2S-2's. The respiratory reader adds gain x "
                               'distress to the excitatory respiratory drive,\n'
                               '    # with the acid and hypoxaemic drives, before the common saturation; the central '
                               'drive availability still gates what\n'
                               '    # is expressed. The sympathetic reader adds its own gain x distress to the '
                               'sympathetic target, through the common\n'
                               '    # saturation and beta-blockade. One upstream signal, two effectors, two gains: '
                               'no RR / HR ratio is implied. No\n'
                               '    # value is chosen here.\n'
                               '    distress_to_respiratory_drive_gain: float | None = None\n'
                               '    distress_to_sympathetic_gain: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    respiratory_mechanics: bool = False\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('                                     "mechanics efficiency, never also in the '
                               'profile")\n'
                               '        for name in ("distress_to_respiratory_drive_gain", '
                               '"distress_to_sympathetic_gain"):\n'
                               '            value = getattr(self, name)\n'
                               '            if value is not None and (isinstance(value, bool) or not '
                               'isinstance(value, (int, float))\n'
                               '                                      or not math.isfinite(value) or value <= 0.0):\n'
                               '                # P2T-1: UNSET is None; a declared reader has a finite positive gain '
                               '(0 would read nothing).\n'
                               '                raise CoreInvariantError(f"{name} is None (UNSET) or a finite '
                               'positive gain")\n'
                               '        if self.distress_to_respiratory_drive_gain is not None and '
                               'self.acid_to_drive_gain is None:\n'
                               '            # P2T-1: the respiratory reader lives in the P2P-2 composition, which '
                               'only the acid-base physiology has.\n'
                               '            raise CoreInvariantError("the respiratory distress reader of the '
                               'respiratory drive needs the P2K-2 acid-base "\n'
                               '                                     "physiology")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n',
                               '                                     "mechanics efficiency, never also in the '
                               'profile")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n'),
                              ('                                           "family mapping is UNSET; not '
                               'approved"),\n'
                               '    "distress_to_respiratory_drive_gain": (PROVISIONAL, "UNSET (P2T-1): respiratory '
                               'drive (breaths/min-equivalent) per "\n'
                               '                                                        "unit of the common '
                               'respiratory distress, added to the acid and "\n'
                               '                                                        "hypoxaemic drives before '
                               'the common saturation, expressed "\n'
                               '                                                        "through the central drive '
                               'availability; None by default (no "\n'
                               '                                                        "reader); SYNTHETIC_ONLY '
                               'values in probes; not approved"),\n'
                               '    "distress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2T-1): sympathetic drive '
                               'per unit of the common respiratory "\n'
                               '                                                  "distress, added to the '
                               'sympathetic target, through the common "\n'
                               '                                                  "saturation and beta-blockade; '
                               'independent of the respiratory "\n'
                               '                                                  "reader\'s gain; None by default '
                               '(no reader); SYNTHETIC_ONLY values in "\n'
                               '                                                  "probes; not approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n',
                               '                                           "family mapping is UNSET; not '
                               'approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n'),
                              ('\n'
                               'def respiratory_distress_read(profile: CoreProfile) -> bool:\n'
                               '    """Whether the profile declares either P2T-1 reader of the common respiratory '
                               'distress (both UNSET by default)."""\n'
                               '    return profile.distress_to_respiratory_drive_gain is not None or '
                               'profile.distress_to_sympathetic_gain is not None\n'
                               '\n'
                               '\n'
                               'def intrinsic_respiratory_rate(anchors: Anchors) -> float:\n',
                               '\ndef intrinsic_respiratory_rate(anchors: Anchors) -> float:\n'),
                              ('    availability and ``expressed_rr`` the RR the patient shows. ``spo2`` is the '
                               'absolute SpO2 the hypoxaemic drive\n'
                               '    read, None when its mapping is UNSET or there is no pulse. P2T-1: '
                               '``distress_drive`` is the respiratory distress\n'
                               "    reader's excitatory term (gain x distress), in the sum before the saturation; 0 "
                               'while that reader is UNSET."""\n'
                               '\n',
                               '    availability and ``expressed_rr`` the RR the patient shows. ``spo2`` is the '
                               'absolute SpO2 the hypoxaemic drive\n'
                               '    read, None when its mapping is UNSET or there is no pulse."""\n'
                               '\n'),
                              ('    expressed_rr: float\n'
                               '    distress_drive: float = 0.0\n'
                               '\n'
                               '\n'
                               'def _composition(intrinsic: float, acid: float, spo2: float | None, profile: '
                               'CoreProfile,\n'
                               '                 distress: float = 0.0) -> DriveComposition:\n'
                               '    hypoxaemic, excitatory = 0.0, acid\n',
                               '    expressed_rr: float\n'
                               '\n'
                               '\n'
                               'def _composition(intrinsic: float, acid: float, spo2: float | None, profile: '
                               'CoreProfile) -> DriveComposition:\n'
                               '    hypoxaemic, excitatory = 0.0, acid\n'),
                              ('        excitatory = acid + hypoxaemic\n'
                               '    distress_drive = 0.0\n'
                               '    if profile.distress_to_respiratory_drive_gain is not None:\n'
                               '        # P2T-1: the non-chemical excitatory term joins the chemical ones before the '
                               'common saturation.\n'
                               '        distress_drive = profile.distress_to_respiratory_drive_gain * distress\n'
                               '        excitatory = excitatory + distress_drive\n'
                               '    excitatory_rr = rate_from_drive(excitatory, intrinsic, profile)\n',
                               '        excitatory = acid + hypoxaemic\n'
                               '    excitatory_rr = rate_from_drive(excitatory, intrinsic, profile)\n'),
                              ('    return DriveComposition(intrinsic, acid, spo2, hypoxaemic, excitatory, '
                               'excitatory_rr, availability,\n'
                               '                            expressed_respiratory_rate(excitatory_rr, availability), '
                               'distress_drive)\n'
                               '\n',
                               '    return DriveComposition(intrinsic, acid, spo2, hypoxaemic, excitatory, '
                               'excitatory_rr, availability,\n'
                               '                            expressed_respiratory_rate(excitatory_rr, '
                               'availability))\n'
                               '\n'),
                              ('    spo2 = _perfusion(state, anchors, profile)[2] if '
                               'profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic, acid, spo2, profile, '
                               'state.aux.respiratory_distress)\n'
                               '\n',
                               '    spo2 = _perfusion(state, anchors, profile)[2] if '
                               'profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic, acid, spo2, profile)\n'
                               '\n'),
                              ('    return _composition(intrinsic_respiratory_rate(anchors),\n'
                               '                        respiratory_drive(arrival_acid_burden(anchors, profile), '
                               'profile), spo2, profile,\n'
                               '                        anchors.arrival_respiratory_distress)\n'
                               '\n',
                               '    return _composition(intrinsic_respiratory_rate(anchors),\n'
                               '                        respiratory_drive(arrival_acid_burden(anchors, profile), '
                               'profile), spo2, profile)\n'
                               '\n'),
                              ('                                 "(P2S-2); nothing else reads it")\n'
                               '    if anchors.arrival_respiratory_distress != 0.0 and not '
                               'respiratory_distress_read(profile):\n'
                               '        raise CoreInvariantError("an arrival respiratory distress other than 0 needs '
                               'a declared distress reader (P2T-1); "\n'
                               '                                 "nothing else reads it")\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n',
                               '                                 "(P2S-2); nothing else reads it")\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n'),
                              ('                                            '
                               'metabolic_acid_burden=arrival_acid_burden(anchors, profile),\n'
                               '                                            '
                               'mechanics_efficiency=anchors.arrival_mechanics_efficiency,\n'
                               '                                            '
                               'respiratory_distress=anchors.arrival_respiratory_distress))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n',
                               '                                            '
                               'metabolic_acid_burden=arrival_acid_burden(anchors, profile),\n'
                               '                                            '
                               'mechanics_efficiency=anchors.arrival_mechanics_efficiency))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n'),
                              ('    these stimuli.\n'
                               '\n'
                               '    P2T-1: the common respiratory distress (aux.respiratory_distress) through its '
                               'own gain, UNSET (None) by default; it\n'
                               '    is respiratory afferent activation only. Non-respiratory stress (pain, '
                               'hypoglycaemic counter-regulation, coronary\n'
                               '    stress, fever, agitation) is SYSTEMIC_STRESS_DEFERRED: no state or gain carries '
                               'it here.\n'
                               '    """\n',
                               '    these stimuli.\n    """\n'),
                              ('              + profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia)\n'
                               '    if profile.distress_to_sympathetic_gain is not None:\n'
                               "        # P2T-1: the respiratory distress reader: its own gain times the state's "
                               'absolute distress (never relative to\n'
                               '        # arrival), through the same saturation and beta-blockade as every term; '
                               'UNSET (None) by default.\n'
                               '        target += profile.distress_to_sympathetic_gain * '
                               'state.aux.respiratory_distress\n'
                               '    # P2J-4: the direct baroreflex, on the MAP of this same state, after the other '
                               'terms (0 with the gain off).\n',
                               '              + profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia)\n'
                               '    # P2J-4: the direct baroreflex, on the MAP of this same state, after the other '
                               'terms (0 with the gain off).\n')),
 'clinical_core/integration.py': (('                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active, '
                                   'respiratory_distress_read)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n',
                                   '                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n'),
                                  ('    mechanics: tuple[MechanicsChange, ...] = ()  # changes to the respiratory '
                                   'mechanics efficiency this minute (P2S-2)\n'
                                   '    distress: tuple[DistressChange, ...] = ()  # changes to the common '
                                   'respiratory distress this minute (P2T-1)\n'
                                   '\n',
                                   '    mechanics: tuple[MechanicsChange, ...] = ()  # changes to the respiratory '
                                   'mechanics efficiency this minute (P2S-2)\n'
                                   '\n'),
                                  ('                              "of MechanicsChange records")\n'
                                   '    if not isinstance(contribution.distress, tuple) or any(not isinstance(item, '
                                   'DistressChange)\n'
                                   '                                                           for item in '
                                   'contribution.distress):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the respiratory '
                                   'distress changes only by a tuple of "\n'
                                   '                              "DistressChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n',
                                   '                              "of MechanicsChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n'),
                                  ('    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress):\n'
                                   '        if item.source != contributor.source:\n',
                                   '    for item in (contribution.deltas + contribution.transitions + '
                                   'contribution.settings + contribution.events\n'
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics):\n'
                                   '        if item.source != contributor.source:\n'),
                                  ('                                   "lung water above arrival clearing slowly"))\n'
                                   '    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    internal = {}\n',
                                   '                                   "lung water above arrival clearing slowly"))\n'
                                   '    transitions, settings, events, modifiers, flows, mechanics = [], [], [], [], '
                                   '[], []\n'
                                   '    internal = {}\n'),
                                  ('        mechanics.extend(contribution.mechanics)\n'
                                   '        distress.extend(contribution.distress)\n'
                                   '        if contribution.internal is not None:\n',
                                   '        mechanics.extend(contribution.mechanics)\n'
                                   '        if contribution.internal is not None:\n'),
                                  ('                         mechanics_efficiency=state.aux.mechanics_efficiency * '
                                   'math.prod(item.factor\n'
                                   '                                                                                         '
                                   'for item in mechanics),\n'
                                   '                         respiratory_distress=_distress_after(state, distress, '
                                   'profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n',
                                   '                         mechanics_efficiency=state.aux.mechanics_efficiency * '
                                   'math.prod(item.factor\n'
                                   '                                                                                         '
                                   'for item in mechanics))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n'),
                                  ('                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress))\n'
                                   '    _check_conservation(state, new_state, record)\n',
                                   '                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics))\n'
                                   '    _check_conservation(state, new_state, record)\n'),
                                  ('\n'
                                   'def _distress_after(state: CoreState, distress: list, profile: CoreProfile, '
                                   'minute: int) -> float:\n'
                                   '    """P2T-1: the respiratory distress after the minute: the value it starts '
                                   "with plus the minute's changes. The core\n"
                                   '    adds no kinetics and no coupling of its own (the mechanics -> distress slot '
                                   'is UNSET and off). With both readers UNSET\n'
                                   '    nothing reads it, so a change is refused; a minute that would take it below '
                                   '0 is refused, never held."""\n'
                                   '    if distress and not respiratory_distress_read(profile):\n'
                                   '        raise ProvenanceError(f"minute {minute}: {distress[0].source.key} '
                                   'changed the respiratory distress while both of "\n'
                                   '                              "its readers are UNSET (P2T-1): nothing would read '
                                   'it")\n'
                                   '    value = state.aux.respiratory_distress + math.fsum(item.amount for item in '
                                   'distress)\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the respiratory distress '
                                   'changes take it to {value!r}, below 0 (P2T-1)")\n'
                                   '    return value\n'
                                   '\n'
                                   '\n'
                                   'def _check_conservation(before: CoreState, after: CoreState, record: '
                                   'MinuteRecord) -> None:\n',
                                   '\n'
                                   'def _check_conservation(before: CoreState, after: CoreState, record: '
                                   'MinuteRecord) -> None:\n'),
                                  ('        raise ProvenanceError("the respiratory mechanics efficiency changed by '
                                   'other than its recorded changes")\n'
                                   '    if after.aux.respiratory_distress != before.aux.respiratory_distress + '
                                   'math.fsum(item.amount\n'
                                   '                                                                                     '
                                   'for item in record.distress):\n'
                                   "        # P2T-1: the distress moves by exactly the minute's recorded changes, "
                                   'never otherwise.\n'
                                   '        raise ProvenanceError("the respiratory distress changed by other than '
                                   'its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n',
                                   '        raise ProvenanceError("the respiratory mechanics efficiency changed by '
                                   'other than its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/respiratory_mechanics_report.py",\n'
                                     '                      "clinical_core/asthma_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_distress_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/respiratory_mechanics_report.py",\n'
                                     '                      "clinical_core/asthma_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class DistressChange:\n'
                                  '    """P2T-1: one source\'s change to the common respiratory distress in one '
                                  'minute.\n'
                                  '\n'
                                  '    The amount adds to the distress the minute starts with (finite; 0 changes '
                                  'nothing), as a channel delta adds to its\n'
                                  '    channel: the distress has no reference above 0 to scale, so the changes are '
                                  'additive. It stays where its writers\n'
                                  '    leave it: it never moves, back to arrival or anywhere else, without a change '
                                  'that names its source, and the core adds\n'
                                  '    no kinetics of its own. The distress is a common input, never a disease term: '
                                  'a family declares what its own\n'
                                  '    process does to it, and the core only sums the changes. A minute whose '
                                  'changes would take it below 0 is refused. No\n'
                                  '    amount is approved; with both of its readers UNSET a change is refused, '
                                  'because nothing would read it.\n'
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
                                  '            raise ProvenanceError(f"a distress change is a finite number, not '
                                  '{self.amount!r}")\n'
                                  '        object.__setattr__(self, "amount", float(self.amount))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every distress change names its Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "distress", "amount": self.amount, "source": '
                                  'self.source.to_dict(), "minute": self.minute,\n'
                                  '                "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AuxiliaryChange:\n',
                                  '@dataclass(frozen=True)\nclass AuxiliaryChange:\n'),
                                 ('    mechanics: tuple[MechanicsChange, ...] = field(default=())\n'
                                  '    distress: tuple[DistressChange, ...] = field(default=())\n'
                                  '\n',
                                  '    mechanics: tuple[MechanicsChange, ...] = field(default=())\n\n'),
                                 ('        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress):\n'
                                  '            if item.minute != self.minute:\n',
                                  '        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics):\n'
                                  '            if item.minute != self.minute:\n'),
                                 ('                "blood": [item.to_dict() for item in self.blood],\n'
                                  '                "mechanics": [item.to_dict() for item in self.mechanics],\n'
                                  '                "distress": [item.to_dict() for item in self.distress]}\n'
                                  '\n',
                                  '                "blood": [item.to_dict() for item in self.blood],\n'
                                  '                "mechanics": [item.to_dict() for item in self.mechanics]}\n'
                                  '\n')),
 'clinical_core/state.py': (('                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2",\n'
                             '                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress"),\n'
                             '}\n',
                             '                              "arrival_delivery_ratio", "arrival_bicarbonate", '
                             '"arrival_paco2",\n'
                             '                              "arrival_mechanics_efficiency"),\n'
                             '}\n'),
                            ('    arrival_mechanics_efficiency: float = 1.0\n'
                             '    # P2T-1 candidate input, read only by the respiratory distress readers (both UNSET '
                             'by default) and outside the\n'
                             "    # case-parameter / migration registry, as P2S-2's: the arrival respiratory "
                             'distress, a case / family latent arrival\n'
                             '    # state constrained by independent authored respiratory evidence (never read from '
                             'the disease label, the RR or the\n'
                             '    # HR), at or above 0 with no upper bound. 0, the default, is none; no other value '
                             'is approved.\n'
                             '    arrival_respiratory_distress: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    arrival_mechanics_efficiency: float = 1.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the arrival respiratory mechanics efficiency is '
                             'above 0 (P2S-2)")\n'
                             '        if isinstance(self.arrival_respiratory_distress, bool) or not '
                             'isinstance(self.arrival_respiratory_distress,\n'
                             '                                                                                (int, '
                             'float)) \\\n'
                             '                or not math.isfinite(self.arrival_respiratory_distress) or '
                             'self.arrival_respiratory_distress < 0.0:\n'
                             '            raise CoreInvariantError("the arrival respiratory distress is finite and '
                             'at or above 0 (P2T-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the arrival respiratory mechanics efficiency is '
                             'above 0 (P2S-2)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'),
                            ('                            "while the mechanics candidate is off",\n'
                             '    "respiratory_distress": "the common respiratory distress (P2T-1): non-chemical '
                             'respiratory afferent / distress "\n'
                             '                            "activation, the mismatch between respiratory demand and '
                             'the respiratory system\'s ability to "\n'
                             '                            "meet it plus respiratory / pulmonary afferent stress the '
                             'gases do not carry; at or above 0 "\n'
                             '                            "with no upper bound, 0 none; the case\'s latent arrival '
                             'value plus every family change since "\n'
                             '                            "(provenance.DistressChange); not SpO2, PaCO2, pH, RR, the '
                             'work-of-breathing observable, the "\n'
                             '                            "mechanics efficiency, G, L, the oxygen deficit, D, shock, '
                             'pain, anxiety, systemic stress or "\n'
                             '                            "central depression; 0 and constant while both of its '
                             'readers are UNSET",\n'
                             '}\n',
                             '                            "while the mechanics candidate is off",\n}\n'),
                            ('    mechanics_efficiency: float = 1.0\n    respiratory_distress: float = 0.0\n\n',
                             '    mechanics_efficiency: float = 1.0\n\n'),
                            ('            raise CoreInvariantError("the respiratory mechanics efficiency is above '
                             '0")\n'
                             '        if self.respiratory_distress < 0:\n'
                             '            # P2T-1: 0 is none; there is no ceiling (no clinical upper bound is '
                             'chosen).\n'
                             '            raise CoreInvariantError("the respiratory distress is never negative")\n'
                             '\n',
                             '            raise CoreInvariantError("the respiratory mechanics efficiency is above '
                             '0")\n'
                             '\n'))}
CORE_AT_P2S3 = {'clinical_core/decision_pack.py': 'b4f3794ff153ec69cbe10bd1e643066ba38eb341e62b35d106e2f94d73e375d5',
 'clinical_core/derived.py': '9c9cc2b1540c8e93896f78d4922456bfa611869d9c902274fc39a8fde0c1c6d5',
 'clinical_core/integration.py': 'd8b43a492b3f545feb52f0e2d3654c64284573c2e458003c12c7c988e75fe1b7',
 'clinical_core/lactate_slice.py': '439e439eb456c76fad7020fb125190b337bf9e953a66d19251521258ba1ffdfb',
 'clinical_core/provenance.py': '71bb736121bc9950e43864b348f67694c14145a54944b01ab90187ddf0979e60',
 'clinical_core/state.py': 'fff5380826b06c35b98d2f8a2da1808e8dd284df6234fd06114431776eb89a7e'}
# </reversal>
# <common>
COMMON_AT_P2S3 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/pressure_tone.py': '2e350c8a42bcacfa31e8e5349d284c7d276808e396d36421e1dc369dbcb9ec26',
 'clinical_core/pressure_tone_filter.py': '54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650',
 'clinical_core/pressure_tone_filter_report.py': '6eebe11b816eeb901f10d9f1431182b71ab26db84652771af741076f33734f92',
 'clinical_core/pressure_tone_report.py': 'bc0fe73c681a35432baec5acf8062027b63f0e5821146133fb9211ae9240d7ac',
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
P2S3_FREEZE_DIGEST = "652d7138ff672fa9e43c92e06ac3042486e8f47ab504736726b0d53f42a7649b"
P2S3_RECORD_SHA = "709e6389365c49b010abdfedbf05ac42e51533d855eff9f2b50ff0e37081e4dd"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2S3[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2S3.items()}


def p2s3_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2S-3 file plus P2T-1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2s3_bytes(relative: str) -> bytes:
    return p2s3_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2s3_sources(sources: dict) -> dict:
    """A P2S-3 dependency map: P2T-1's files removed, each changed file at its P2S-3 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2S3.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def _sm_common_untouched() -> dict:
    return {relative: hashlib.sha256(p2s3_bytes(relative)).hexdigest() == sha
            for relative, sha in sm.COMMON_AT_P2S2.items()}


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2S-3's view reads the P2S-3 files (proven) and their bytes, its captured
    source map is P2S-3's, and every closed comparison of serialized anchors ignores the new P2T-1 candidate input at
    its reference 0, so every closed guard still reads the tree it froze."""
    patch.setattr(sm, "_live", p2s3_text)
    patch.setattr(sm, "common_untouched", _sm_common_untouched)
    patch.setattr(sm, "_FREEZE_SOURCES", lambda: p2s3_sources(_FREEZE_SOURCES()))
    patch.setattr(mc, "without_new_anchor_key", without_new_keys)
    # P2S-2 lists the auxiliary fields live (its no-extra-state section): it reads them as P2S-3 left them.
    patch.setattr(mc, "AUXILIARY_FIELDS", P2S3_AUXILIARY_FIELDS)


_FREEZE_SOURCES = bf.freeze_sources
#: The auxiliary fields as P2S-3 left them: P2T-1's one new field (respiratory_distress, 0 in every closed course) out.
P2S3_AUXILIARY_FIELDS = {k: v for k, v in AUXILIARY_FIELDS.items() if k != "respiratory_distress"}


class p2s3_view:
    """P2S-3's analysis reading the tree P2S-3 froze (its sources and its common files), for its own proofs; P2S-2's
    reads nest inside it through ``sm.p2s2_view``."""

    def __enter__(self):
        self._patch = mc._Patch()
        chain(self._patch)
        self._patch.setattr(bf, "freeze_sources", lambda: p2s3_sources(_FREEZE_SOURCES()))
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2s3_view():
        p2s3_digest = sm.freeze_digest()
        p2s3_proof = sm.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2s3_freeze_digest": p2s3_digest == P2S3_FREEZE_DIGEST,
            "p2s3_proof": all(p2s3_proof["proofs"].values()) and all(p2s3_proof["common_untouched"].values())
            and p2s3_proof["p2s2_freeze_digest"] and p2s3_proof["p2s2_proof"] and p2s3_proof["p2s2_record"],
            "p2s3_record": hashlib.sha256(sm.RECORD.read_bytes()).hexdigest() == P2S3_RECORD_SHA}


# P2T-1-13: readiness (predeclared) --------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "auxiliary distress exists (aux.respiratory_distress, its arrival value, its conservation and refusals)",
    "it is distinct from mechanics, gases and shock (D7, D8, D9, orthogonality, the readers' audit)",
    "a family writer interface exists (DistressChange; additive, persistent, recorded; no family writer yet)",
    "the respiratory reader exists structurally (D2, D10)",
    "the sympathetic reader exists structurally (D3)",
    "the gains are separate and UNSET (D4; the parameter state)",
    "the acid composition is structurally coherent (D10, D11)",
    "the central availability still gates the RR, and not the HR (D5, D6)",
    "beta-blockade remains downstream (the beta-blockade guard)",
    "the default behaviour is exact (D1, D12, the closed records reproduced, the P2S-3 tree proven)",
    "no systemic_stress implementation leaked in",
)
READY = "COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_READY"
NOT_READY = "COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_NOT_READY"
READINESS_RULE = ("Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion as "
                  "the blocker. The case contrasts, the WOB ordering and the residual HR gaps are reported; the "
                  "composition is classified STRUCTURAL_COMPOSITION_READY and CLINICAL_COMPOSITION_MAGNITUDE_UNSET")
RECOMMENDATION = {READY: "RETRY_ASTHMA_SHADOW_MIGRATION_AFTER_DISTRESS_ARCHITECTURE (a new package superseding P2S-3; not "
                         "started here)"}
COMPOSITION_CLASSES = ("STRUCTURAL_COMPOSITION_READY", "CLINICAL_COMPOSITION_MAGNITUDE_UNSET")


def readiness(found: dict) -> dict:
    p = found["probes"]
    proof = found["proof"]
    checks = (
        found["representation"]["pass"],
        p["D7"]["pass"] and p["D8"]["pass"] and p["D9"]["pass"] and found["orthogonality"]["pass"]
        and found["audit"]["pass"],
        found["representation"]["pass"],
        p["D2"]["pass"] and p["D10"]["pass"],
        p["D3"]["pass"],
        p["D4"]["pass"] and found["parameters"]["pass"],
        p["D10"]["pass"] and p["D11"]["pass"],
        p["D5"]["pass"] and p["D6"]["pass"],
        found["beta_blockade"]["pass"],
        p["D1"]["pass"] and p["D12"]["pass"] and found["non_regression"]["pass"] and all(proof["proofs"].values())
        and all(proof["common_untouched"].values()) and proof["p2s3_freeze_digest"] and proof["p2s3_proof"]
        and proof["p2s3_record"],
        found["systemic_stress"]["pass"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    verdict = READY if blocker is None else f"{NOT_READY} - {blocker}"
    return {"criteria": rows, "blocker": blocker, "verdict": verdict, "rule": READINESS_RULE,
            "composition": list(COMPOSITION_CLASSES) if checks[6] else ["STRUCTURAL_COMPOSITION_NOT_READY"],
            "recommendation": RECOMMENDATION.get(verdict, "faculty review of the blocker")}


def design() -> dict:
    return {"decisions": DECISIONS, "semantics": SEMANTICS, "probes": PROBES,
            "synthetic": {"respiratory_gain": RESPIRATORY_GAIN, "sympathetic_gain": SYMPATHETIC_GAIN,
                          "other_gains": list(OTHER_GAINS), "distress_grid": list(DISTRESS_GRID),
                          "probe_distress": PROBE_DISTRESS, "availabilities": list(AVAILABILITIES),
                          "opioid_availability": OPIOID_AVAILABILITY, "acid_bicarbonate": ACID_BICARBONATE,
                          "hypoxaemic_spo2": HYPOXAEMIC_SPO2, "hypoxaemic_gain": HYPOXAEMIC_GAIN,
                          "low_efficiency": LOW_EFFICIENCY, "mechanics_factor": MECHANICS_FACTOR,
                          "distress_step": DISTRESS_STEP, "course_minutes": COURSE_MINUTES,
                          "beta_blockades": list(BETA_BLOCKADES)},
            "ordering": {"families": list(ORDERING_FAMILIES), "faculty_order": list(FACULTY_ORDER),
                         "labels": WOB_LABELS, "candidate_regions": {k: list(v) for k, v in CANDIDATE_REGIONS.items()}},
            "parameters": PARAMETER_STATUS, "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2s3": CORE_AT_P2S3, "common_at_p2s3": COMMON_AT_P2S3,
            "p2s3": {"head": P2S3_HEAD, "freeze_digest": P2S3_FREEZE_DIGEST, "record": P2S3_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2s3": hashlib.sha256(sm.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "representation": representation(),
             "probes": structural_probes(), "contrasts": contrasts(), "beta_blockade": beta_blockade(),
             "ordering": wob_ordering(), "orthogonality": orthogonality(), "observable": observable(),
             "parameters": parameter_state(), "systemic_stress": systemic_stress(),
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
    data = run()
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
