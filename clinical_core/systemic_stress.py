"""P2V-1: the minimum common systemic stress architecture (shadow only, inert by default).

P2V-0 classified the non-respiratory HR gap as B, COMMON_SYSTEMIC_STRESS_WITH_DISTINCT_FAMILY_WRITERS_SUPPORTED: the
authored tachycardias of hypoglycaemia, coronary stress, fever and pain are not oxygen deficit, not debt, not
baroreflex and not respiratory distress, and the common sympathetic target has no input that carries them. This package
adds that one input and nothing else:

- ``AuxiliaryState.systemic_stress`` (finite, at or above 0, 0 by default, no upper bound) and
  ``Anchors.arrival_systemic_stress`` (the latent arrival activation, 0 by default), a common auxiliary input, never a
  canonical V/T/P/R/L/G/W/D/N channel;
- ``provenance.SystemicStressChange``, the writer interface, additive like a ``DistressChange``; no family implements it
  here;
- ``CoreProfile.systemic_stress_to_sympathetic_gain``, the one reader, UNSET (None) by default: it adds its own gain
  times the state's absolute stress to the sympathetic HR target, upstream of the common saturation and of the
  beta-blockade, and it is the only reader of the stress. Nothing respiratory reads it: the stress never reaches the
  respiratory drive, the RR, W, the PaCO2 or the SpO2.

The respiratory distress (P2T-1) and the systemic stress stay two independent signals, by the faculty's decision:
distress is respiratory afferent / work-of-breathing activation, stress is non-respiratory central / adrenergic
activation. Neither is derived from the other, and neither is solved from an observed HR.

This module freezes the sympathetic-path audit, the representation and writer audit, the structural probes S1-S10, the
case contrasts, the arrival-region methodology, the parameter state, the carried debts, the default non-regression and
the proof that every other common file is P2U-1's, before the one evaluation run. Every gain, stress value and region
here is SYNTHETIC_ONLY or UNSET; nothing is calibrated and nothing is approved.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
import math
import sys
import types
from dataclasses import astuple, dataclass, fields, replace
from pathlib import Path

from . import acs_reference as ar
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import distress_closure as xm
from . import gas_exchange_architecture as go
from . import gi_reference as gr
from . import opioid_migration as un
from . import opioid_reference as orf
from . import oxygenation_link as om
from . import respiratory_distress as dm
from . import respiratory_mechanics as mc
from .integration import Contribution, Contributor, step
from .provenance import DistressChange, ProvenanceError, SourceKind, SystemicStressChange
from .state import AUXILIARY_FIELDS, CASE_PARAMETERS, CoreInvariantError, RhythmCode, RhythmState

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2V-1"
DECIDED = "2026-11-05"
OWN = ("clinical_core/systemic_stress.py",)
REPORT = "clinical_core/systemic_stress_report.py"
RECORD = ROOT / "docs" / "revision" / "P2V1_systemic_stress.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2V1_ESTRES_SISTEMICO_COMUN.md"
#: The two registry tuples gain this package's entries (proven against P2U-1's files below).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py", "clinical_core/state.py", "clinical_core/integration.py",
              "clinical_core/provenance.py")
NEW_AUX = "systemic_stress"
NEW_ANCHOR = "arrival_systemic_stress"
NEW_PROFILE_FIELD = "systemic_stress_to_sympathetic_gain"
#: P2V-1's candidate input in the anchors, outside the case-parameter / migration registry until the faculty adopts
#: this physiology (as P2K-2's, P2O-3's, P2S-2's, P2T-1's and P2U-1's).
CANDIDATE_INPUTS = (NEW_ANCHOR,)

DECISIONS = {
    "classification": "B, COMMON_SYSTEMIC_STRESS_WITH_DISTINCT_FAMILY_WRITERS_SUPPORTED (P2V-0, accepted)",
    "scope": "one new common auxiliary input (systemic_stress) and its one sympathetic reader; no anaphylaxis "
             "migration, no distributive tone, no clinical calibration, no consciousness integration, no hypoxaemic "
             "drive",
    "representation": "non-respiratory central / adrenergic stress activation: an auxiliary common input, never a new "
                      "canonical V/T/P/R/L/G/W/D/N channel",
    "independence": "systemic_stress raises the sympathetic HR drive independently of the oxygen deficit, D, the "
                    "baroreflex, the respiratory distress, hypoxaemia and hypercapnia",
    "reader": "the SYMPATHETIC HR TARGET ONLY: systemic_stress_to_sympathetic_gain, UNSET (None) by default, upstream "
              "of the common saturation and of the beta-blockade, never a respiratory reader",
    "separation": "respiratory_distress and systemic_stress stay TWO independent signals and are never merged: "
                  "distress = respiratory afferent / work-of-breathing activation; stress = non-respiratory "
                  "sympathetic / adrenergic activation",
    "arrival": "a latent FAMILY_CANDIDATE / CASE MAPPING arrival state constrained by independent authored evidence; "
               "never inferred from the HR residual alone",
    "glucose": "GLUCOSE_CAN_ANCHOR_FAMILY_STRESS_REGION; NOT GLUCOSE_TO_STRESS_MAPPING_APPROVED",
    "temperature": "TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION; no universal numeric mapping",
    "hypoglycaemia_term": "the existing sympathetic_per_hypoglycaemia_mg_dl is neither removed nor reinterpreted: it "
                          "is classified below, unchanged",
    "magnitudes": "every magnitude UNSET: no gain, no arrival value, no glucose / temperature / pain number",
    "residuals": "a common causal signal, never an observable residual fit: no family-specific bpm term closes an HR "
                 "residual here",
}

SEMANTICS = {
    "represents": "non-respiratory central / adrenergic stress activation: the sympathetic activation of pain, "
                  "hypoglycaemic counter-regulation, coronary / ischaemic stress, fever and agitation, which raises "
                  "the sympathetic HR drive without an oxygen deficit, a debt, a pressure fall or respiratory "
                  "afferent traffic",
    "does_not_represent": ["the respiratory distress", "the oxygen deficit", "D", "the baroreflex", "hypoxaemia",
                           "hypercapnia", "the respiratory drive", "the RR", "W", "pain itself", "the temperature",
                           "the glucose", "an HR residual solved from the observed HR"],
    "state": "aux.systemic_stress: finite, at or above 0, 0 none, no upper bound (no clinical bound is chosen)",
    "arrival": "Anchors.arrival_systemic_stress: a case / family latent arrival value, 0 by default; refused other "
               "than 0 unless the reader is declared",
    "writer": "Contribution.systemic_stress: provenance.SystemicStressChange(amount, source, minute, description); "
              "amounts add to the value the minute starts with (the stress has no reference above 0 to scale, so the "
              "convention is a channel delta's, as the distress's); a minute that would take it below 0 is refused; "
              "refused while the reader is UNSET",
    "core_kinetics": "none: the integration sums the minute's declared changes only (source "
                     "core_coupling:systemic_stress); no decay, no coupling, no derivation from any other state",
    "sympathetic_reader": "sympathetic target += systemic_stress_to_sympathetic_gain x the absolute stress (never "
                          "relative to arrival), before max(0, .), then the common saturation and beta-blockade "
                          "(sympathetic_increment)",
    "respiratory_reader": "none, by decision: no respiratory function reads the stress (NO_RESPIRATORY_STRESS_READER)",
    "observable": "no observable reads the stress; the diaphoresis, tremor, pain, fever and agitation descriptors stay "
                  "authored evidence",
}

# Synthetic, predeclared probe values (SYNTHETIC_ONLY, never approved) --------------------------------------------------------

SYMPATHETIC_GAIN = 0.05         # sympathetic drive per stress unit (the same synthetic scale P2T-1 used for distress)
OTHER_GAIN = 0.2                # a second, different gain for S2 / S8
STRESS_GRID = (0.0, 2.5, 5.0, 10.0)
PROBE_STRESS = 5.0
DISTRESS_GAIN = dm.SYMPATHETIC_GAIN            # P2T-1's synthetic distress -> sympathetic gain (S4, S9)
RESPIRATORY_GAIN = dm.RESPIRATORY_GAIN         # P2T-1's synthetic distress -> respiratory gain (S3, S4)
PROBE_DISTRESS = dm.PROBE_DISTRESS
STRESS_STEP = 1.0               # one scripted writer: +1 per minute
COURSE_MINUTES = 10
BETA_BLOCKADES = (0.0, 0.5, 1.0)
LOW_SPO2 = 80.0                 # a severe hypoxaemia (S8)
LOW_GLUCOSE = 34.0              # the authored hypoglycaemia (the term audit, never a mapping)
RECOVERED_GLUCOSE = 90.0
LOW_MAP_SET = 75.0              # a declared baroreflex set point (S8)
PROBE_ANCHORS = replace(dm.PROBE_ANCHORS, case_id="p2v1_stress_probe")   # RR 16 and HR 80 intrinsic, MAP 90
#: The authored HR band the common architecture reaches with no stress: the intrinsic sinus band (P2V-0's reading).
RESTING_HR = gr.RESTING_HR


def reader(profile: dv.CoreProfile, gain: float | None = SYMPATHETIC_GAIN) -> dv.CoreProfile:
    """The profile with P2V-1's systemic-stress reader declared (SYNTHETIC_ONLY) or UNSET."""
    return replace(profile, systemic_stress_to_sympathetic_gain=gain)


def base_profile() -> dv.CoreProfile:
    """P2S-2's probe profile: the ACS common point, acid-base on, gas-exchange reference, mechanics candidate on."""
    return dm.base_profile()


def probe_anchors(**changes):
    """The probe anchors with the given changes; a changed case parameter is declared a synthetic probe value."""
    declared = {**dict(PROBE_ANCHORS.declared), **{k: "synthetic_probe" for k in changes if k in CASE_PARAMETERS}}
    return replace(PROBE_ANCHORS, declared=declared, **changes)


@dataclass(frozen=True)
class SyntheticStress(Contributor):
    """SYNTHETIC_ONLY: a scripted systemic-stress writer, the amount every minute in (start, stop]. Not a family
    writer, not registered (no replay needed): P2V-1 implements no family."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2v1_probe_systemic_stress"

    id: str
    amount: float
    start_minute: int = 0
    stop_minute: int = 10 ** 6

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(systemic_stress=(SystemicStressChange(self.amount, self.source, minute,
                                                                  "probe: declared change of the systemic stress"),))


PROBE_SOURCE = SyntheticStress("p2v1", 0.0).source


def course(items, minutes, anchors, profile):
    state = dv.arrival_state(anchors, profile)
    states, records = [state], []
    for _ in range(minutes):
        state, record = step(state, tuple(items), anchors, profile)
        states.append(state)
        records.append(record)
    return states, records


def reading(state, anchors, profile) -> dict:
    """One state's reading: the sympathetic path, the HR, the respiratory chain and every quantity the stress must not
    move directly."""
    d = dv.derive(state, anchors, profile)
    r = dv.respiration(state, anchors, profile)
    c = dv.respiratory_drive_composition(state, anchors, profile)
    return {"stress": state.aux.systemic_stress, "distress": state.aux.respiratory_distress,
            "sympathetic_target": dv.sympathetic_target(state, anchors, profile),
            "sympathetic_drive": state.aux.sympathetic_drive, "hr": d.pulse_rate_bpm,
            "acid_drive": c.acid_drive, "hypoxaemic_drive": c.hypoxaemic_drive, "distress_drive": c.distress_drive,
            "excitatory_drive": c.excitatory_drive, "excitatory_rr": c.excitatory_rr, "availability": c.availability,
            "rr": c.expressed_rr, "W": r.ventilation, "paco2": r.paco2, "ph": r.ph, "spo2": d.spo2,
            "delivery": dv.delivery_rel_of(state, anchors, profile), "lactate": d.lactate, "map": d.map,
            "mechanics_efficiency": state.aux.mechanics_efficiency,
            "central_availability": state.aux.central_availability,
            "G": state.G, "L": state.L, "D": state.D, "P": state.P, "V": state.V, "T": state.T}


def at_arrival(anchors, profile) -> dict:
    return reading(dv.arrival_state(anchors, profile), anchors, profile)


#: What a systemic-stress change may move (S5): the sympathetic target, the drive behind the HR and the HR; nothing
#: else. The respiratory chain and every canonical channel stay where they were.
STRESS_CONSEQUENCES = ("stress", "sympathetic_target", "sympathetic_drive", "hr")
NEVER_MOVED = ("distress", "acid_drive", "hypoxaemic_drive", "distress_drive", "excitatory_drive", "excitatory_rr",
               "availability", "rr", "W", "paco2", "ph", "spo2", "delivery", "lactate", "map",
               "mechanics_efficiency", "central_availability", "G", "L", "D", "P", "V", "T")

#: The respiratory functions of the core: none of them may name the stress (P2V-1-5).
RESPIRATORY_FUNCTIONS = ("_composition", "arrival_drive_composition", "respiratory_drive_composition",
                         "respiratory_rate_decomposition", "expressed_respiratory_rate", "rate_from_drive",
                         "respiration", "acid_drive", "hypoxaemic_drive", "ventilation_of", "paco2_of")


def _refused(build, error=(CoreInvariantError, ProvenanceError)) -> bool:
    try:
        build()
    except error:
        return True
    return False


# P2V-1-1: the sympathetic path, read from the code --------------------------------------------------------------------------

def _target_terms(text: str) -> list:
    """The ordered terms of ``sympathetic_target``, as the code composes them: the sum, then each conditional reader,
    then the baroreflex, then the floor."""
    node = mc._functions(text)["sympathetic_target"]
    order = []

    def sum_terms(value, into):
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            sum_terms(value.left, into)
            sum_terms(value.right, into)
        else:
            into.append(ast.unparse(value))

    for stmt in node.body:
        if isinstance(stmt, ast.Assign) and getattr(stmt.targets[0], "id", None) == "target":
            sum_terms(stmt.value, order)
        elif isinstance(stmt, ast.AugAssign) and getattr(stmt.target, "id", None) == "target":
            order.append(ast.unparse(stmt.value))
        elif isinstance(stmt, ast.If):
            for sub in stmt.body:
                if isinstance(sub, ast.AugAssign) and getattr(sub.target, "id", None) == "target":
                    order.append(f"if {ast.unparse(stmt.test)}: {ast.unparse(sub.value)}")
        elif isinstance(stmt, ast.Return):
            order.append(f"return {ast.unparse(stmt.value)}")
    return order


def audit() -> dict:
    """P2V-1-1: who feeds the sympathetic target, in what order, what the effector does with it, and where the new
    reader goes in. Read from the live code and from P2U-1's (the insertion is the only difference)."""
    live = _live("clinical_core/derived.py")
    funcs = mc._functions(live)
    every = dm._every_function(live)
    terms = _target_terms(live)
    before = _target_terms(p2u1_text("clinical_core/derived.py"))
    stress_readers = sorted({n for n, f in every if NEW_AUX in mc._names(f)})
    anchor_readers = sorted({n for n, f in every if NEW_ANCHOR in mc._names(f)})
    gain_readers = sorted({n for n, f in every if NEW_PROFILE_FIELD in mc._names(f)
                           or NEW_PROFILE_FIELD in dm._strings(f)})
    integration = mc._functions(_live("clinical_core/integration.py"))
    out = {
        "target_terms_before": before,
        "target_terms": terms,
        "terms_added": [t for t in terms if t not in before],
        "terms_removed": [t for t in before if t not in terms],
        "inputs": {
            "acute_deficit": "profile.acute_deficit_to_sympathetic_gain x acute_deficit_signal (absolute: the "
                             "effective oxygen deficit over the demand; 0 when availability is adequate)",
            "pressure_deficit": "profile.sympathetic_per_pressure_deficit x (1 - pressure_rel), relative to arrival "
                                "(0 at arrival; 0 in every primary HR calibration since P2I-2AG)",
            "debt": "profile.debt_to_sympathetic_gain x state.D (absolute: the memory, 0 at D = 0)",
            "hypoxaemia": "profile.sympathetic_per_hypoxaemia_point x (threshold - SpO2 now, minus the same at "
                          "arrival): relative to arrival, so 0 at arrival",
            "hypoglycaemia": "profile.sympathetic_per_hypoglycaemia_mg_dl x (threshold - glucose now, minus the same "
                             "at arrival): relative to arrival, so 0 at arrival (classified below)",
            "respiratory_distress": "profile.distress_to_sympathetic_gain x aux.respiratory_distress (absolute), "
                                    "UNSET by default (P2T-1)",
            "systemic_stress": "profile.systemic_stress_to_sympathetic_gain x aux.systemic_stress (absolute), UNSET "
                               "by default (P2V-1, this package)",
            "baroreflex": "baroreflex_drive(pressure_rel, anchors, profile): the MAP of this state against a declared "
                          "MAP_set, after the other terms, 0 with the gain off (P2J-4)",
            "floor": "max(0, .): the drive is never negative (P2D-3)",
            "declared_without_state": "hypercapnia and withdrawal: declared inputs of the same drive with no core "
                                      "state (the docstring); fever, pain and agitation now reach it through the "
                                      "systemic stress, whose arrival value and gain stay UNSET",
        },
        "effector": {
            "held_drive": "integration.step: aux.sympathetic_drive = sympathetic_after_minute(before, after), which "
                          "reads sympathetic_target on the state after the minute and decays toward it; derive reads "
                          "the held drive, never the target",
            "saturation": "sympathetic_increment(drive, base_rate, beta, profile) = reserve x tanh(unconstrained / "
                          "reserve), reserve = sinus_rate_ceiling_bpm - base_rate",
            "beta_blockade": "unconstrained_increment = hr_per_sympathetic_drive x (1 - beta) x drive",
            "rhythm": "the increment applies to a sinus rate only; in another rhythm the rate is the rhythm's",
        },
        "insertion_point": "derived.sympathetic_target, after the distress reader and before the baroreflex and the "
                           "max(0, .) floor: one additive term on the same target, so the common saturation and the "
                           "beta-blockade stay downstream and are never bypassed",
        "stress_readers": stress_readers,
        "arrival_readers": anchor_readers,
        "gain_readers": gain_readers,
        "respiratory_functions_reading_stress": sorted(n for n in RESPIRATORY_FUNCTIONS
                                                       if n in funcs and NEW_AUX in mc._names(funcs[n])),
        "integration_readers": sorted(n for n, f in dm._every_function(_live("clinical_core/integration.py"))
                                      if NEW_AUX in mc._names(f)),
        "integration_sums": [ast.unparse(n) for n in ast.walk(integration["step"]) if isinstance(n, ast.keyword)
                             and n.arg == NEW_AUX],
        "increment_reads_beta_blockade": "beta_blockade" in mc._names(funcs["sympathetic_increment"]),
    }
    out["pass"] = (out["terms_added"] == [f"if profile.{NEW_PROFILE_FIELD} is not None: "
                                          f"profile.{NEW_PROFILE_FIELD} * state.aux.{NEW_AUX}"]
                   and not out["terms_removed"]
                   and terms[-1] == "return max(0.0, target)"
                   and terms.index(out["terms_added"][0]) == len(terms) - 3      # before the baroreflex and the floor
                   and stress_readers == ["sympathetic_target"]      # the one reader; arrival_state only writes it
                   and anchor_readers == ["arrival_state"]
                   and gain_readers == ["__post_init__", "arrival_state", "sympathetic_target"]
                   and not out["respiratory_functions_reading_stress"]
                   and out["integration_readers"] == ["_check_conservation", "_check_owned", "_systemic_stress_after",
                                                      "step"]
                   and out["integration_sums"] == [f"{NEW_AUX}=_systemic_stress_after(state, {NEW_AUX}, profile, "
                                                   "minute)", f"{NEW_AUX}=tuple({NEW_AUX})"]
                   and out["increment_reads_beta_blockade"])
    return out


# P2V-1-2 / -3: the representation and the writer interface --------------------------------------------------------------------

def _p2u1_fields(relative: str, name: str) -> list:
    return dm._class_fields(p2u1_text(relative), name)


def _live_fields(relative: str, name: str) -> list:
    return dm._class_fields(_live(relative), name)


def representation() -> dict:
    """The one auxiliary field, the one arrival anchor, the one writer record and their refusals; the writer is
    additive and persistent, and its changes carry the core-coupling source."""
    on, off = reader(base_profile()), base_profile()
    a = probe_anchors()
    state = dv.arrival_state(a, on)
    added = {"CoreProfile": sorted(set(f.name for f in fields(dv.CoreProfile))
                                   - set(_p2u1_fields("clinical_core/derived.py", "CoreProfile"))),
             "AuxiliaryState": sorted(set(AUXILIARY_FIELDS) - set(_p2u1_fields("clinical_core/state.py",
                                                                               "AuxiliaryState"))),
             "Anchors": sorted(set(f.name for f in fields(type(a)))
                               - set(_p2u1_fields("clinical_core/state.py", "Anchors"))),
             "Contribution": sorted(set(_live_fields("clinical_core/integration.py", "Contribution"))
                                    - set(_p2u1_fields("clinical_core/integration.py", "Contribution"))),
             "MinuteRecord": sorted(set(_live_fields("clinical_core/provenance.py", "MinuteRecord"))
                                    - set(_p2u1_fields("clinical_core/provenance.py", "MinuteRecord")))}
    refusals = {
        "negative_state": _refused(lambda: replace(state.aux, systemic_stress=-0.1)),
        "nan_state": _refused(lambda: replace(state.aux, systemic_stress=float("nan"))),
        "infinite_state": _refused(lambda: replace(state.aux, systemic_stress=float("inf"))),
        "boolean_arrival": _refused(lambda: probe_anchors(arrival_systemic_stress=True)),
        "negative_arrival": _refused(lambda: probe_anchors(arrival_systemic_stress=-1.0)),
        "infinite_arrival": _refused(lambda: probe_anchors(arrival_systemic_stress=float("inf"))),
        "arrival_without_reader": _refused(lambda: dv.arrival_state(probe_anchors(arrival_systemic_stress=1.0), off)),
        "change_without_reader": _refused(lambda: step(dv.arrival_state(a, off), (SyntheticStress("x", 1.0),), a,
                                                       off)),
        "change_below_zero": _refused(lambda: step(dv.arrival_state(a, on), (SyntheticStress("x", -1.0),), a, on)),
        "amount_nan": _refused(lambda: SystemicStressChange(float("nan"), PROBE_SOURCE, 1, "x")),
        "amount_infinite": _refused(lambda: SystemicStressChange(float("inf"), PROBE_SOURCE, 1, "x")),
        "amount_boolean": _refused(lambda: SystemicStressChange(True, PROBE_SOURCE, 1, "x")),
        "amount_without_source": _refused(lambda: SystemicStressChange(1.0, "core", 1, "x")),
        "amount_without_description": _refused(lambda: SystemicStressChange(1.0, PROBE_SOURCE, 1, "")),
        "foreign_change_type": _refused(lambda: step(dv.arrival_state(a, on), (_WrongType("w"),), a, on)),
    }
    # Additive and persistent: a writer that stops leaves the stress where it left it; two writers sum; a negative
    # amount from one writer is a declared fall, never a reset.
    states, records = course((SyntheticStress("a", 1.0, 0, 3), SyntheticStress("b", 0.5, 0, 2)), 6, a, on)
    trail = [s.aux.systemic_stress for s in states]
    sources = sorted({c.source.key for r in records for c in r.auxiliary if c.quantity == NEW_AUX})
    down, _ = course((SyntheticStress("a", 1.0, 0, 3), SyntheticStress("b", -0.5, 3, 5)), 6, a, on)
    out = {"added_fields": added, "refused": refusals, "trail": trail,
           "records": [len(r.systemic_stress) for r in records], "aux_source": sources,
           "down_trail": [s.aux.systemic_stress for s in down],
           "writer_interface": {"record": "provenance.SystemicStressChange(amount, source, minute, description)",
                                "contribution_field": "systemic_stress",
                                "same_shape_as": "provenance.DistressChange (P2T-1)",
                                "fields_match": [f.name for f in fields(SystemicStressChange)]
                                == [f.name for f in fields(DistressChange)]},
           "family_writers": sorted(str(p.relative_to(ROOT)) for p in (CORE_DIR / "modules").glob("*.py")
                                    if "SystemicStressChange" in p.read_text(encoding="utf-8")),
           "default_state": dv.arrival_state(probe_anchors(), off).aux.systemic_stress,
           "no_upper_bound": replace(state.aux, systemic_stress=1e6).systemic_stress == 1e6}
    out["pass"] = (added == {"CoreProfile": [NEW_PROFILE_FIELD], "AuxiliaryState": [NEW_AUX], "Anchors": [NEW_ANCHOR],
                             "Contribution": [NEW_AUX], "MinuteRecord": [NEW_AUX]}
                   and all(refusals.values()) and trail == [0.0, 1.5, 3.0, 4.0, 4.0, 4.0, 4.0]
                   and out["records"] == [2, 2, 1, 0, 0, 0] and sources == [f"core_coupling:{NEW_AUX}"]
                   and out["down_trail"] == [0.0, 1.0, 2.0, 3.0, 2.5, 2.0, 2.0]
                   and out["writer_interface"]["fields_match"] and not out["family_writers"]
                   and out["default_state"] == 0.0 and out["no_upper_bound"])
    return out


@dataclass(frozen=True)
class _WrongType(Contributor):
    """A writer that puts the wrong record type in the stress field: refused by the ownership check."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2v1_probe_wrong_type"

    id: str

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(systemic_stress=(DistressChange(1.0, self.source, minute, "wrong record type"),))


# P2V-1-4: the reader and its gain ---------------------------------------------------------------------------------------------

def committed_pairs() -> dict:
    """Every committed arrival mapping and its profile: P2T-5's four families and P2U-1's two opioid cases."""
    pairs = dict(om.committed_pairs())
    for case in orf.CASES:
        pairs[case] = (orf.anchors(case), orf.common_profile())
    return pairs


def reader_audit() -> dict:
    """The gain is this package's only new parameter: UNSET by default, independent of every other gain, additive on
    the same target, and never a bypass of the saturation or of the beta-blockade."""
    prof = reader(base_profile())
    a = probe_anchors()
    zero, some = at_arrival(a, prof), at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), prof)
    base = dv.intrinsic_sinus_rate(a)
    huge = at_arrival(replace(a, arrival_systemic_stress=1e4), prof)
    refusals = {"zero": _refused(lambda: reader(base_profile(), 0.0)),
                "negative": _refused(lambda: reader(base_profile(), -0.1)),
                "boolean": _refused(lambda: reader(base_profile(), True)),
                "nan": _refused(lambda: reader(base_profile(), float("nan"))),
                "infinite": _refused(lambda: reader(base_profile(), float("inf")))}
    out = {"new_profile_fields": sorted(set(f.name for f in fields(dv.CoreProfile))
                                        - set(_p2u1_fields("clinical_core/derived.py", "CoreProfile"))),
           "default_unset": dv.DEFAULT_PROFILE.systemic_stress_to_sympathetic_gain is None,
           "base_profile_unset": base_profile().systemic_stress_to_sympathetic_gain is None,
           "committed_profiles_unset": {name: p.systemic_stress_to_sympathetic_gain is None
                                        for name, (_, p) in committed_pairs().items()},
           "declared_alone": (reader(base_profile()).distress_to_sympathetic_gain is None
                              and reader(base_profile()).distress_to_respiratory_drive_gain is None),
           "target_rise_is_the_gain": math.isclose(some["sympathetic_target"] - zero["sympathetic_target"],
                                                   SYMPATHETIC_GAIN * PROBE_STRESS, abs_tol=1e-12),
           "hr_rise_through_the_increment": math.isclose(
               some["hr"] - zero["hr"],
               dv.sympathetic_increment(some["sympathetic_drive"], base, a.beta_blockade, prof)
               - dv.sympathetic_increment(zero["sympathetic_drive"], base, a.beta_blockade, prof), abs_tol=1e-12),
           "sinus_ceiling": base + dv.sinus_rate_reserve(base, prof), "hr_at_a_huge_stress": huge["hr"],
           "saturated_at_or_below_the_ceiling": huge["hr"] <= base + dv.sinus_rate_reserve(base, prof),
           "saturation_is_sublinear": (huge["hr"] - zero["hr"]) < SYMPATHETIC_GAIN * 1e4 * prof.hr_per_sympathetic_drive,
           "refused_gains": refusals,
           "parameter_state": dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, None))[0],
           "parameter_note": dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, ""))[1]}
    out["pass"] = (out["new_profile_fields"] == [NEW_PROFILE_FIELD] and out["default_unset"]
                   and out["base_profile_unset"] and all(out["committed_profiles_unset"].values())
                   and out["declared_alone"] and out["target_rise_is_the_gain"]
                   and out["hr_rise_through_the_increment"] and out["saturated_at_or_below_the_ceiling"]
                   and out["saturation_is_sublinear"] and all(refusals.values())
                   and out["parameter_state"] == "provisional" and "UNSET" in out["parameter_note"])
    return out


# P2V-1-5: no respiratory reader ------------------------------------------------------------------------------------------------

def respiratory_isolation() -> dict:
    """The stress never reaches the respiratory side: no respiratory function names it (read from the code), and a
    stress change alone leaves the whole respiratory chain where it was (read from the model)."""
    live = _live("clinical_core/derived.py")
    funcs = mc._functions(live)
    both = reader(dm.readers(base_profile(), RESPIRATORY_GAIN, DISTRESS_GAIN))
    a = probe_anchors()
    rows = {str(s): at_arrival(replace(a, arrival_systemic_stress=s), both) for s in STRESS_GRID}
    chain = ("acid_drive", "hypoxaemic_drive", "distress_drive", "excitatory_drive", "excitatory_rr", "availability",
             "rr", "W", "paco2", "ph", "spo2")
    first = rows[str(STRESS_GRID[0])]
    out = {"respiratory_functions_reading_stress": sorted(n for n in RESPIRATORY_FUNCTIONS
                                                          if n in funcs and NEW_AUX in mc._names(funcs[n])),
           "stress_in_the_drive_composition": NEW_AUX in mc._names(funcs["_composition"]),
           "composition_arguments": sorted(ast.unparse(node.args[4]) for node in ast.walk(ast.parse(live))
                                           if isinstance(node, ast.Call)
                                           and getattr(node.func, "id", None) == "_composition"
                                           and len(node.args) >= 5),
           "respiratory_chain_fixed": {k: all(math.isclose(rows[str(s)][k], first[k], rel_tol=0.0, abs_tol=0.0)
                                              for s in STRESS_GRID) for k in chain},
           "hr_moves": [rows[str(s)]["hr"] for s in STRESS_GRID],
           "integration_guard": "a SystemicStressChange is refused while the reader is UNSET; no respiratory guard "
                                "reads it (check_distress_respiratory_effect is the distress's, not the stress's)",
           "integration_functions_reading_stress": sorted(
               n for n, f in dm._every_function(_live("clinical_core/integration.py")) if NEW_AUX in mc._names(f))}
    out["pass"] = (not out["respiratory_functions_reading_stress"] and not out["stress_in_the_drive_composition"]
                   and out["composition_arguments"] == ["anchors.arrival_respiratory_distress",
                                                        "state.aux.respiratory_distress"]
                   and all(out["respiratory_chain_fixed"].values())
                   and out["hr_moves"] == sorted(out["hr_moves"]) and out["hr_moves"][0] < out["hr_moves"][-1]
                   and out["integration_functions_reading_stress"] == ["_check_conservation", "_check_owned",
                                                                       "_systemic_stress_after", "step"])
    return out


# P2V-1-6: the existing hypoglycaemia term -------------------------------------------------------------------------------------

HYPOGLYCAEMIA_CLASSIFICATION = "CHANGE_TERM"
HYPOGLYCAEMIA_STATUS = ("HYPOGLYCAEMIA_SYMPATHETIC_TERM_IS_A_CHANGE_TERM: sympathetic_per_hypoglycaemia_mg_dl reads "
                        "the glucose of this state against the glucose at arrival, so it is 0 at arrival whatever the "
                        "arrival glucose, positive only while the glucose falls further and negative while it "
                        "recovers (a recovery term). It cannot carry an arrival stress, and it is not the "
                        "systemic-stress reader. P2V-1 neither removes it nor reinterprets it: it stays exactly as "
                        "P2U-1 left it, and the two terms are independently addressable.")


def hypoglycaemia_term() -> dict:
    """What the existing term is, read from the code and from the model: a change / recovery term, kept unchanged."""
    live = _live("clinical_core/derived.py")
    node = mc._functions(live)["sympathetic_target"]
    expression = next(ast.unparse(s.value) for s in node.body
                      if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", None) == "hypoglycaemia")
    before = mc._functions(p2u1_text("clinical_core/derived.py"))["sympathetic_target"]
    same = next(ast.unparse(s.value) for s in before.body
                if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", None) == "hypoglycaemia")
    prof = base_profile()
    a = probe_anchors(glucose=LOW_GLUCOSE)
    arrival = dv.arrival_state(a, prof)
    falling = arrival.evolve(glucose=LOW_GLUCOSE - 10.0)
    recovering = arrival.evolve(glucose=RECOVERED_GLUCOSE)
    neutral = probe_anchors()
    out = {"expression": expression, "unchanged_since_p2u1": expression == same,
           "threshold_mg_dl": prof.hypoglycaemia_threshold_mg_dl,
           "gain_per_mg_dl": prof.sympathetic_per_hypoglycaemia_mg_dl,
           "classification": HYPOGLYCAEMIA_CLASSIFICATION, "status": HYPOGLYCAEMIA_STATUS,
           "at_arrival_with_glucose_34": dv.sympathetic_target(arrival, a, prof),
           "falling_further": dv.sympathetic_target(falling, a, prof),
           "recovering_to_90": dv.sympathetic_target(recovering, a, prof),
           "arrival_hr_with_glucose_34": dv.derive(arrival, a, prof).pulse_rate_bpm,
           "arrival_hr_with_glucose_100": at_arrival(neutral, prof)["hr"],
           "removed_or_rewritten": False,
           "independently_addressable": None}
    stress = reader(prof)
    with_stress = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), stress)
    without = at_arrival(a, stress)
    out["independently_addressable"] = (with_stress["hr"] > without["hr"]
                                        and dv.sympathetic_target(dv.arrival_state(a, stress), a, stress)
                                        == dv.sympathetic_target(arrival, a, prof))
    out["pass"] = (out["unchanged_since_p2u1"] and out["at_arrival_with_glucose_34"] == 0.0
                   and out["falling_further"] > 0.0 and out["recovering_to_90"] == 0.0
                   and out["arrival_hr_with_glucose_34"] == out["arrival_hr_with_glucose_100"]
                   and out["independently_addressable"])
    return out


# P2V-1-7: the structural probes S1-S10 -----------------------------------------------------------------------------------------

BARO_GAIN = 0.02                # SYNTHETIC_ONLY: a declared baroreflex gain (S8)
BARO_MAP_SET = 100.0            # SYNTHETIC_ONLY: a declared MAP set point above the probe's MAP of 90 (S8)
DEFICIT_DELIVERY = 0.3          # SYNTHETIC_ONLY: an arrival delivery ratio past the extraction reserve, so
#                                 the acute-deficit term is above 0 (S8)
ARRIVAL_DEBT = 4.0              # SYNTHETIC_ONLY: an arrival oxygen debt (S8)


def reference_courses() -> dict:
    """P2T-1's reference courses (GI, ACS, oedema, PE, P2P-2, asthma, the mechanics probe) and P2U-1's two opioid
    courses, with the stress reader UNSET."""
    out = dict(dm.reference_courses())
    for case in orf.CASES:
        a, p = orf.anchors(case), orf.common_profile()
        out[f"{case}_opioid"] = (un.course((un.depression(),), a, p)[0], a, p)
    return out


def p2u1_core():
    """The P2U-1 derived.py (proven by the reversal), executed as its own module beside the live one."""
    name = "clinical_core._derived_at_p2u1"
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    exec(compile(p2u1_text("clinical_core/derived.py"), "derived_at_p2u1.py", "exec"), module.__dict__)
    return module


def _old_profile(old, profile):
    names = {f.name for f in fields(old.CoreProfile)}
    if getattr(profile, NEW_PROFILE_FIELD) is not None:
        raise AssertionError("the comparison holds the P2V-1 reader UNSET")
    return old.CoreProfile(**{n: getattr(profile, n) for n in names})


def _composition_view(c) -> tuple:
    return (c.baseline_rr, c.acid_drive, c.spo2, c.hypoxaemic_drive, c.distress_drive, c.excitatory_drive,
            c.excitatory_rr, c.availability, c.expressed_rr)


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


def _declared(old_profile, gain=SYMPATHETIC_GAIN):
    return reader(old_profile, gain)


def probe_s1() -> dict:
    """stress 0: declaring the reader changes no HR and no reading at all (every reference course)."""
    courses = reference_courses()
    same, zero = {}, {}
    for name, (states, anchors, prof) in courses.items():
        on = reader(prof)
        same[name] = all(dv.derive(s, anchors, on).to_dict() == dv.derive(s, anchors, prof).to_dict()
                         and dv.sympathetic_target(s, anchors, on) == dv.sympathetic_target(s, anchors, prof)
                         for s in states)
        zero[name] = {s.aux.systemic_stress for s in states} == {0.0}
    out = {"identical_with_the_reader_declared": same, "stress_zero": zero}
    out["pass"] = all(same.values()) and all(zero.values())
    return out


def _grid(profile, anchors=None) -> list:
    a = anchors or probe_anchors()
    return [at_arrival(replace(a, arrival_systemic_stress=s), profile) for s in STRESS_GRID]


def probe_s2() -> dict:
    """stress > 0 with the reader declared: the sympathetic target and the HR increase, strictly and monotonically;
    the rise is the gain times the stress, and a different gain gives a different rise on the same stress."""
    rows = _grid(reader(base_profile()))
    other = _grid(reader(base_profile(), OTHER_GAIN))
    out = {"grid": list(STRESS_GRID), "target": [r["sympathetic_target"] for r in rows], "hr": [r["hr"] for r in rows],
           "target_other_gain": [r["sympathetic_target"] for r in other],
           "target_is_the_gain": all(math.isclose(r["sympathetic_target"] - rows[0]["sympathetic_target"],
                                                  SYMPATHETIC_GAIN * s, abs_tol=1e-12)
                                     for r, s in zip(rows, STRESS_GRID)),
           "other_gain_is_its_own": all(math.isclose(r["sympathetic_target"] - other[0]["sympathetic_target"],
                                                     OTHER_GAIN * s, abs_tol=1e-12)
                                        for r, s in zip(other, STRESS_GRID))}
    out["pass"] = (dm._increasing(out["target"]) and dm._increasing(out["hr"]) and out["target_is_the_gain"]
                   and out["other_gain_is_its_own"]
                   and out["target_other_gain"][-1] > out["target"][-1])
    return out


def probe_s3() -> dict:
    """The RR (and the whole respiratory chain) is unchanged by the stress, with the respiratory distress reader
    declared as well: the stress reaches no respiratory reader."""
    found = respiratory_isolation()
    rr_only_reader = reader(dm.readers(base_profile(), RESPIRATORY_GAIN, None))
    a = probe_anchors()
    rows = [at_arrival(replace(a, arrival_systemic_stress=s), rr_only_reader) for s in STRESS_GRID]
    out = {"isolation": {k: found[k] for k in ("respiratory_functions_reading_stress", "respiratory_chain_fixed",
                                               "composition_arguments")},
           "rr": [r["rr"] for r in rows], "excitatory_drive": [r["excitatory_drive"] for r in rows],
           "W": [r["W"] for r in rows], "paco2": [r["paco2"] for r in rows]}
    out["pass"] = (found["pass"] and len(set(out["rr"])) == 1 and len(set(out["excitatory_drive"])) == 1
                   and len(set(out["W"])) == 1 and len(set(out["paco2"])) == 1)
    return out


def probe_s4() -> dict:
    """The two signals stay independent: a stress writer never moves the distress, a distress writer never moves the
    stress, and neither reader reads the other's state."""
    a = probe_anchors()
    both = reader(dm.readers(base_profile(), RESPIRATORY_GAIN, DISTRESS_GAIN))
    stress_states, stress_records = course((SyntheticStress("s", STRESS_STEP),), COURSE_MINUTES, a, both)
    distress_states, distress_records = course((dm.SyntheticDistress("d", dm.DISTRESS_STEP),), COURSE_MINUTES, a, both)
    stress_only = reader(base_profile())
    distress_only = dm.readers(base_profile(), None, DISTRESS_GAIN)
    out = {"stress_course_distress": sorted({s.aux.respiratory_distress for s in stress_states}),
           "stress_course_stress": [s.aux.systemic_stress for s in stress_states],
           "distress_course_stress": sorted({s.aux.systemic_stress for s in distress_states}),
           "distress_course_distress": [s.aux.respiratory_distress for s in distress_states],
           "records_are_separate": (all(not r.distress for r in stress_records)
                                    and all(not r.systemic_stress for r in distress_records)),
           # Each guard refuses the other signal's arrival anchor without its own reader, so the cross-reads are taken
           # on the state itself: the stress reader never reads the distress, and the distress reader never reads the
           # stress.
           "stress_reader_ignores_distress": _ignores(a, stress_only, "respiratory_distress", PROBE_DISTRESS),
           "distress_reader_ignores_stress": _ignores(a, distress_only, NEW_AUX, PROBE_STRESS),
           "each_guard_refuses_the_others_anchor": (
               _refused(lambda: dv.arrival_state(replace(a, arrival_respiratory_distress=PROBE_DISTRESS),
                                                 stress_only))
               and _refused(lambda: dv.arrival_state(replace(a, arrival_systemic_stress=PROBE_STRESS),
                                                     distress_only))),
           "semantics": {"distress": "respiratory afferent / work-of-breathing activation (P2T-1)",
                         "systemic_stress": "non-respiratory sympathetic / adrenergic activation (P2V-1)",
                         "merged": False}}
    out["pass"] = (out["each_guard_refuses_the_others_anchor"]
                   and out["stress_course_distress"] == [0.0] and out["distress_course_stress"] == [0.0]
                   and out["stress_course_stress"][-1] == STRESS_STEP * COURSE_MINUTES
                   and out["distress_course_distress"][-1] == dm.DISTRESS_STEP * COURSE_MINUTES
                   and out["records_are_separate"] and out["stress_reader_ignores_distress"]
                   and out["distress_reader_ignores_stress"])
    return out


def _ignores(anchors, profile, field: str, value: float) -> bool:
    """Whether a profile's declared reader leaves the sympathetic target where it was when the OTHER signal moves on
    the state (the arrival guards refuse the anchor, so the state carries it)."""
    state = dv.arrival_state(anchors, profile)
    moved = state.evolve(aux=replace(state.aux, **{field: value}))
    return dv.sympathetic_target(moved, anchors, profile) == dv.sympathetic_target(state, anchors, profile)


def _moved(a_row, b_row) -> list:
    return sorted(k for k in a_row if a_row[k] != b_row[k])


def probe_s5() -> dict:
    """A stress change alone moves only the sympathetic target, the drive and the HR: V, T, P, L, G, W, D, the RR, the
    SpO2, the lactate, the MAP, the mechanics and the central availability stay where they were."""
    a = probe_anchors()
    prof = reader(base_profile())
    zero = at_arrival(a, prof)
    some = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), prof)
    states, _ = course((SyntheticStress("s", STRESS_STEP, 0, 1),), 2, a, prof)
    rows = [reading(s, a, prof) for s in states]
    out = {"arrival_moved": _moved(zero, some), "course_moved": _moved(rows[0], rows[1]),
           "never_moved_at_arrival": {k: zero[k] == some[k] for k in NEVER_MOVED},
           "never_moved_in_the_course": {k: rows[0][k] == rows[1][k] for k in NEVER_MOVED}}
    out["pass"] = (set(out["arrival_moved"]) <= set(STRESS_CONSEQUENCES)
                   and set(out["course_moved"]) <= set(STRESS_CONSEQUENCES)
                   and all(out["never_moved_at_arrival"].values()) and all(out["never_moved_in_the_course"].values())
                   and "hr" in out["arrival_moved"] and "hr" in out["course_moved"])
    return out


def beta_blockade() -> dict:
    """S6 / S7: the stress's HR effect goes through the common effector, beta-blockade included; beta = 1 suppresses
    it exactly, as it does every other drive."""
    prof = reader(base_profile())
    rows = {}
    for beta in BETA_BLOCKADES:
        a = probe_anchors(beta_blockade=beta)
        zero = at_arrival(a, prof)
        some = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), prof)
        base = dv.intrinsic_sinus_rate(a)
        expected = (dv.sympathetic_increment(some["sympathetic_drive"], base, beta, prof)
                    - dv.sympathetic_increment(zero["sympathetic_drive"], base, beta, prof))
        rows[beta] = {"target_rise": some["sympathetic_target"] - zero["sympathetic_target"],
                      "drive_rise": some["sympathetic_drive"] - zero["sympathetic_drive"],
                      "hr_rise": some["hr"] - zero["hr"],
                      "through_increment": math.isclose(some["hr"] - zero["hr"], expected, abs_tol=1e-12)}
    out = {"rows": {str(k): v for k, v in rows.items()},
           "target_rise_is_beta_independent": len({round(v["target_rise"], 12) for v in rows.values()}) == 1}
    out["pass"] = (all(v["through_increment"] for v in rows.values())
                   and rows[0.0]["hr_rise"] > rows[0.5]["hr_rise"] > 0.0 and rows[1.0]["hr_rise"] == 0.0
                   and out["target_rise_is_beta_independent"])
    return out


def probe_s8() -> dict:
    """The deficit, the debt and the baroreflex stay independently addressable: each moves the target by its own term
    with the stress held, and the stress moves it by its own gain in every one of those configurations."""
    prof = reader(base_profile())
    baro = reader(replace(base_profile(), baroreflex_to_sympathetic_gain=BARO_GAIN,
                          baroreflex_map_set_mmhg=BARO_MAP_SET))
    configs = {"neutral": (probe_anchors(), prof),
               "acute_deficit": (probe_anchors(arrival_delivery_ratio=DEFICIT_DELIVERY), prof),
               "debt": (probe_anchors(arrival_oxygen_debt=ARRIVAL_DEBT), prof),
               "baroreflex": (probe_anchors(), baro),
               "hypoxaemia_arrival": (probe_anchors(spo2=LOW_SPO2), prof)}
    rows = {}
    for name, (a, p) in configs.items():
        without = at_arrival(a, p)
        with_stress = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), p)
        rows[name] = {"target": without["sympathetic_target"], "target_with_stress": with_stress["sympathetic_target"],
                      "rise": with_stress["sympathetic_target"] - without["sympathetic_target"],
                      "hr": without["hr"], "hr_with_stress": with_stress["hr"]}
    neutral = rows["neutral"]["target"]
    out = {"rows": rows,
           "each_term_addressable": {k: rows[k]["target"] > neutral for k in ("acute_deficit", "debt", "baroreflex")},
           "arrival_hypoxaemia_is_relative": rows["hypoxaemia_arrival"]["target"] == neutral,
           "stress_rise_is_always_its_own": all(math.isclose(v["rise"], SYMPATHETIC_GAIN * PROBE_STRESS,
                                                             abs_tol=1e-12) for v in rows.values())}
    out["pass"] = (all(out["each_term_addressable"].values()) and out["arrival_hypoxaemia_is_relative"]
                   and out["stress_rise_is_always_its_own"])
    return out


def probe_s9() -> dict:
    """The distress and the stress compose additively on the same target, each through its own gain, with no
    interaction term and no merging."""
    a = probe_anchors()
    both = reader(dm.readers(base_profile(), RESPIRATORY_GAIN, DISTRESS_GAIN))
    base = at_arrival(a, both)
    only_d = at_arrival(replace(a, arrival_respiratory_distress=PROBE_DISTRESS), both)
    only_s = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), both)
    together = at_arrival(replace(a, arrival_respiratory_distress=PROBE_DISTRESS,
                                  arrival_systemic_stress=PROBE_STRESS), both)
    out = {"base": base["sympathetic_target"], "distress_only": only_d["sympathetic_target"],
           "stress_only": only_s["sympathetic_target"], "together": together["sympathetic_target"],
           "additive": math.isclose(together["sympathetic_target"] - base["sympathetic_target"],
                                    (only_d["sympathetic_target"] - base["sympathetic_target"])
                                    + (only_s["sympathetic_target"] - base["sympathetic_target"]), abs_tol=1e-12),
           "distress_also_moves_the_rr": only_d["rr"] > base["rr"],
           "stress_never_moves_the_rr": only_s["rr"] == base["rr"],
           "together_rr_is_the_distress_only": together["rr"] == only_d["rr"],
           "hr": {"base": base["hr"], "distress_only": only_d["hr"], "stress_only": only_s["hr"],
                  "together": together["hr"]}}
    out["pass"] = (out["additive"] and out["distress_also_moves_the_rr"] and out["stress_never_moves_the_rr"]
                   and out["together_rr_is_the_distress_only"] and together["hr"] > only_d["hr"] > base["hr"]
                   and together["hr"] > only_s["hr"] > base["hr"])
    return out


def probe_s10() -> dict:
    """With the reader UNSET (the default) every prior reading is exact: the P2U-1 core, on every reference course and
    every committed arrival mapping."""
    old = p2u1_core()
    courses = reference_courses()
    exact = {name: _same_reading(states, anchors, prof, old) for name, (states, anchors, prof) in courses.items()}
    arrival = {name: _same_reading([dv.arrival_state(a, p)], a, p, old) for name, (a, p) in committed_pairs().items()}
    stress_zero = {name: {s.aux.systemic_stress for s in states} == {0.0}
                   for name, (states, _, _) in courses.items()}
    out = {"exact_reading_p2u1_core": exact, "exact_arrival_p2u1_core": arrival, "stress_zero": stress_zero,
           "committed_arrival_stress_zero": {name: dv.arrival_state(a, p).aux.systemic_stress == 0.0
                                             for name, (a, p) in committed_pairs().items()}}
    out["pass"] = (all(exact.values()) and all(arrival.values()) and all(stress_zero.values())
                   and all(out["committed_arrival_stress_zero"].values()))
    return out


PROBES = {
    "S1": "systemic stress 0: the HR and every reading are exactly today's, with the reader declared",
    "S2": "stress > 0 with the synthetic reader: the sympathetic target (and the HR) rises by its own gain",
    "S3": "the RR and the whole respiratory chain are unchanged by the stress",
    "S4": "the respiratory distress is unchanged by the stress, and the stress by the distress: two signals",
    "S5": "V, T, P, L, G, W and D are not changed directly by a stress change",
    "S6": "the beta-blockade attenuates the stress's HR effect through the existing downstream pathway",
    "S7": "beta-blockade = 1 suppresses the stress's HR increment, as it does every other drive",
    "S8": "the acute deficit, D and the baroreflex stay independently addressable",
    "S9": "the distress and the systemic stress compose additively, each through its own gain",
    "S10": "with the gain UNSET (the default) every prior behaviour is exact (the P2U-1 core)",
}


def structural_probes() -> dict:
    beta = beta_blockade()
    found = {"S1": probe_s1(), "S2": probe_s2(), "S3": probe_s3(), "S4": probe_s4(), "S5": probe_s5(),
             "S6": {"pass": beta["pass"] and beta["rows"]["0.5"]["hr_rise"] < beta["rows"]["0.0"]["hr_rise"],
                    **beta},
             "S7": {"pass": beta["rows"]["1.0"]["hr_rise"] == 0.0, "row": beta["rows"]["1.0"]},
             "S8": probe_s8(), "S9": probe_s9(), "S10": probe_s10()}
    return {k: {"requires": PROBES[k], **v} for k, v in found.items()}


# P2V-1-8 to -12: the case contrasts (structural only, on the authored truth) ----------------------------------------------

#: The authored arrival truth of the contrast cases, transcribed from the case bank (the shadow core imports no case
#: file). Observables and investigations only: the common architecture is read against them, never fitted to them.
AUTHORED = {
    "hypoglycemia_28m": {"hr": 112.0, "rhythm": "Sinus tachycardia", "sbp": 128.0, "dbp": 76.0, "spo2": 98.0,
                         "rr": 20.0, "wob": "Normal", "mental": "Drowsy", "temperature_c": 36.7, "glucose": 34.0,
                         "crt_s": 2.0, "extremities": "Warm", "lactate": 1.7, "paco2": 39.0, "ph": 7.41,
                         "diaphoresis": "marked", "expression": "uncomfortable", "skin": "mild pallor",
                         "history": "shaking and sweating before the confusion; type 1 diabetes on insulin"},
    "acs_70f_left_main": {"hr": 112.0, "rhythm": "Sinus tachycardia", "sbp": 104.0, "dbp": 66.0, "spo2": 94.0,
                          "rr": 26.0, "wob": "Mildly increased", "mental": "Alert", "temperature_c": 36.9,
                          "glucose": 168.0, "crt_s": 3.0, "extremities": "Cool", "lactate": 3.1, "paco2": 33.0,
                          "ph": 7.36, "diaphoresis": "marked", "expression": "uncomfortable", "skin": "mild pallor",
                          "history": "chest pressure, breathlessness and sweating for an hour"},
    "renal_colic_34m": {"hr": 94.0, "rhythm": "Sinus rhythm", "sbp": 142.0, "dbp": 84.0, "spo2": 98.0, "rr": 18.0,
                        "wob": "Normal", "mental": "Alert", "temperature_c": 36.8, "glucose": 104.0, "crt_s": 2.0,
                        "extremities": "Warm", "lactate": 1.4, "paco2": 38.0, "ph": 7.41, "diaphoresis": "absent",
                        "expression": "markedly uncomfortable", "skin": "natural",
                        "history": "severe colicky flank pain in waves, cannot stay still, vomiting"},
    "pneumonia_46f": {"hr": 118.0, "rhythm": "Sinus tachycardia", "sbp": 92.0, "dbp": 58.0, "spo2": 89.0, "rr": 30.0,
                      "wob": "Increased", "mental": "Alert", "temperature_c": 39.1, "glucose": 152.0, "crt_s": 4.0,
                      "extremities": "Cool", "lactate": 3.8, "paco2": 31.0, "ph": 7.42, "diaphoresis": "absent",
                      "expression": "uncomfortable", "skin": "mild pallor",
                      "history": "cough with sputum, chills, pleuritic pain, breathless and weak"},
    "pneumonia_83m": {"hr": 108.0, "rhythm": "Sinus tachycardia", "sbp": 96.0, "dbp": 60.0, "spo2": 91.0, "rr": 28.0,
                      "wob": "Increased", "mental": "Drowsy", "temperature_c": 37.8, "glucose": 126.0, "crt_s": 4.0,
                      "extremities": "Cool", "lactate": 3.1, "paco2": 33.0, "ph": 7.41, "diaphoresis": "absent",
                      "expression": "uncomfortable", "skin": "mild pallor",
                      "history": "sleepy, new cough, reduced intake, breathing faster"},
    "anaphylaxis_63m_betablocked": {"hr": 64.0, "rhythm": "AF", "sbp": 76.0, "dbp": 42.0, "spo2": 89.0, "rr": 26.0,
                                    "wob": "Increased", "mental": "Drowsy", "temperature_c": 36.4, "glucose": 132.0,
                                    "crt_s": 4.0, "extremities": "Warm", "lactate": 4.6, "paco2": 36.0, "ph": 7.29,
                                    "diaphoresis": "mild", "expression": "uncomfortable", "skin": "flushed",
                                    "history": "wasp sting, rash, throat tightness, beta-blocker on the family's "
                                               "medication list"},
}

#: The independent authored evidence of a non-respiratory sympathetic activation, per case: what constrains an arrival
#: stress region WITHOUT reading the HR. The HR is never in this list, and no number is attached to any item.
INDEPENDENT_EVIDENCE = {
    "hypoglycemia_28m": ("measured glucose 34 mg/dL", "marked diaphoresis", "tremor reported before the confusion",
                         "warm extremities with CRT 2 and lactate 1.7 (no shock)", "SpO2 98 (no hypoxaemia)",
                         "normal work of breathing"),
    "acs_70f_left_main": ("marked diaphoresis", "ischaemic chest pressure", "pallor",
                          "cool extremities with CRT 3 and lactate 3.1 (shock terms also present)"),
    "renal_colic_34m": ("markedly uncomfortable expression with severe colicky pain", "diaphoresis ABSENT",
                        "MAP above normal", "warm extremities with CRT 2 and lactate 1.4", "SpO2 98, RR 18"),
    "pneumonia_46f": ("temperature 39.1", "chills", "CRT 4 and lactate 3.8 (sepsis)", "SpO2 89 with RR 30 and "
                      "increased work of breathing"),
    "pneumonia_83m": ("temperature 37.8", "CRT 4 and lactate 3.1 (sepsis)", "SpO2 91 with RR 28 and increased work "
                      "of breathing", "drowsiness"),
    "anaphylaxis_63m_betablocked": ("beta-blocker on the medication list", "AF at 64 (a non-sinus rhythm)",
                                    "MAP 53 with CRT 4 and lactate 4.6", "flushing and warm extremities"),
}

#: The status P2V-1 assigns each contrast. No case receives an arrival stress value here.
CONTRAST_STATUS = {
    "hypoglycemia_28m": "FAMILY_CANDIDATE / REGION UNSET",
    "acs_70f_left_main": "FAMILY_CANDIDATE / REGION UNSET",
    "renal_colic_34m": "COMPATIBILITY / POSSIBLE WRITER",
    "pneumonia_46f": "NOT_SEPARABLE / STRUCTURAL_ONLY",
    "pneumonia_83m": "NOT_SEPARABLE / STRUCTURAL_ONLY",
    "anaphylaxis_63m_betablocked": "BETA_BLOCKADE_GUARD",
}


def _authored_anchors(case: str, **changes):
    """SYNTHETIC_ONLY probe anchors carrying one case's authored HR and rhythm against the common intrinsic band: a
    structural stand-in, never a case mapping (no case is mapped here)."""
    row = AUTHORED[case]
    sinus = row["rhythm"] != "AF"
    rhythm = RhythmState(RhythmCode.SINUS if sinus else RhythmCode.AF, row["hr"], 1.0, True)
    # The intrinsic sinus rate is declared only for a sinus arrival (the anchors refuse it otherwise): in another
    # rhythm the rate is the rhythm's and no sympathetic increment applies.
    intrinsic = {"intrinsic_sinus_rate": RESTING_HR[1]} if sinus else {}
    return probe_anchors(hr=row["hr"], rhythm=rhythm, **intrinsic, **changes)


def _neutral_band(case: str) -> list:
    """What the common architecture reaches at arrival with no stress: the intrinsic sinus band, at most the observed
    HR (P2V-0's reading). The residual is reported, never absorbed."""
    hr = AUTHORED[case]["hr"]
    return [RESTING_HR[0], min(RESTING_HR[2], hr)]


def _distress_to_close(anchors, profile, target_hr: float):
    """The respiratory distress a declared distress reader would need to close an HR residual, and what it does to the
    RR: the measure of why a respiratory signal must not absorb a non-respiratory one."""
    low, high = 0.0, 400.0
    if at_arrival(replace(anchors, arrival_respiratory_distress=high), profile)["hr"] < target_hr:
        return None
    for _ in range(80):
        mid = (low + high) / 2.0
        if at_arrival(replace(anchors, arrival_respiratory_distress=mid), profile)["hr"] < target_hr:
            low = mid
        else:
            high = mid
    row = at_arrival(replace(anchors, arrival_respiratory_distress=high), profile)
    return {"distress": high, "hr": row["hr"], "rr": row["rr"]}


def contrast_hypoglycaemia() -> dict:
    """P2V-1-8: the structural contrast of hypoglycemia_28m. No calibration: the arrival stress stays
    FAMILY_CANDIDATE / REGION UNSET."""
    row = AUTHORED["hypoglycemia_28m"]
    a = _authored_anchors("hypoglycemia_28m", glucose=row["glucose"], spo2=row["spo2"], crt_s=row["crt_s"])
    prof = reader(base_profile())
    unset = at_arrival(a, base_profile())
    declared = at_arrival(a, prof)
    band = _neutral_band("hypoglycemia_28m")
    out = {"authored": row, "evidence": list(INDEPENDENT_EVIDENCE["hypoglycemia_28m"]),
           "neutral_band": band, "forced_bpm": round(row["hr"] - band[1], 2),
           "model_hr_unset": unset["hr"], "model_hr_with_the_reader_and_no_stress": declared["hr"],
           "shock_terms": {"delivery": unset["delivery"], "D": unset["D"], "target": unset["sympathetic_target"]},
           "hypoglycaemia_term_at_arrival": 0.0,
           "with_synthetic_stress": at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), prof)["hr"],
           "arrival_stress": "UNSET", "status": CONTRAST_STATUS["hypoglycemia_28m"],
           "why": "the authored HR 112 sits above the whole intrinsic band with no deficit, no debt, no pressure fall "
                  "and no respiratory distress, and the existing hypoglycaemia term is 0 at arrival: the gap needs a "
                  "common non-respiratory input. Its size is not a calibration and no value is chosen here."}
    out["pass"] = (out["forced_bpm"] >= 12.0 and out["model_hr_unset"] == out["model_hr_with_the_reader_and_no_stress"]
                   and out["shock_terms"]["target"] == 0.0 and out["with_synthetic_stress"] > declared["hr"]
                   and out["arrival_stress"] == "UNSET")
    return out


def contrast_acs() -> dict:
    """P2V-1-9: the structural contrast of acs_70f_left_main on its committed mapping. The residual must not be closed
    by the respiratory distress."""
    a, prof = ar.anchors(), ar.common_profile()
    on = reader(prof)
    unset, declared = at_arrival(a, prof), at_arrival(a, on)
    authored = AUTHORED["acs_70f_left_main"]
    residual = authored["hr"] - unset["hr"]
    # The respiratory reader needs P2T-1A's M1 guard satisfied (the mechanics candidate on), so the measure is
    # taken on the committed profile with the candidate declared: the RR cost of closing an HR gap with distress.
    distress_profile = dm.readers(mc.candidate(prof), RESPIRATORY_GAIN, DISTRESS_GAIN)
    closing = _distress_to_close(a, distress_profile, authored["hr"])
    distress_base = at_arrival(a, distress_profile)
    out = {"authored": authored, "evidence": list(INDEPENDENT_EVIDENCE["acs_70f_left_main"]),
           # The transcription above is checked against the committed mapping itself, so the contrast cannot drift from
           # the authored truth the ACS package froze.
           "transcription_matches_the_mapping": (a.hr == authored["hr"] and a.spo2 == authored["spo2"]
                                                 and a.glucose == authored["glucose"]),
           "model_hr": unset["hr"], "residual_bpm": round(residual, 2),
           "unchanged_with_the_reader_declared": unset["hr"] == declared["hr"],
           "shock_terms": dv.heart_rate_decomposition(a, prof),
           "model_arrival_rr": unset["rr"], "authored_rr": authored["rr"],
           "distress_probe_base_rr": distress_base["rr"], "closing_with_distress": closing,
           "distress_cost_on_the_rr": None if closing is None else round(closing["rr"] - distress_base["rr"], 2),
           "with_synthetic_stress": at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), on)["hr"],
           "arrival_stress": "UNSET", "status": CONTRAST_STATUS["acs_70f_left_main"],
           "why": "the residual is non-respiratory (marked diaphoresis and ischaemic stress, with the shock terms "
                  "already carried by the deficit and D). Closing it with the distress reader would take the RR far "
                  "past the authored 26, so the respiratory signal must not absorb it; the stress reader leaves the "
                  "RR untouched. No value is chosen."}
    out["pass"] = (out["transcription_matches_the_mapping"]
                   and out["residual_bpm"] > 0.0 and out["unchanged_with_the_reader_declared"]
                   and closing is not None and closing["rr"] > authored["rr"]
                   and out["with_synthetic_stress"] > declared["hr"] and out["arrival_stress"] == "UNSET")
    return out


def contrast_renal_colic() -> dict:
    """P2V-1-10: the negative / weak control. Severe pain does NOT force a non-zero stress."""
    row = AUTHORED["renal_colic_34m"]
    band = _neutral_band("renal_colic_34m")
    a = _authored_anchors("renal_colic_34m", glucose=row["glucose"], spo2=row["spo2"], crt_s=row["crt_s"])
    prof = reader(base_profile())
    declared, unset = at_arrival(a, prof), at_arrival(a, base_profile())
    out = {"authored": row, "evidence": list(INDEPENDENT_EVIDENCE["renal_colic_34m"]), "neutral_band": band,
           "forced_bpm": round(row["hr"] - band[1], 2), "model_hr": unset["hr"],
           "unchanged_with_the_reader_declared": unset["hr"] == declared["hr"],
           "zero_stress_is_compatible": row["hr"] >= band[0] and row["hr"] <= RESTING_HR[2],
           "arrival_stress": "UNSET", "status": CONTRAST_STATUS["renal_colic_34m"],
           "why": "the authored HR 94 is inside the intrinsic sinus band with no autonomic markers (diaphoresis "
                  "absent, MAP above normal, lactate 1.4), so the architecture needs no stress here: pain is "
                  "COMPATIBLE with a writer and forces nothing. A pain -> stress number is not approved and not "
                  "proposed."}
    out["pass"] = (out["forced_bpm"] <= 0.0 and out["zero_stress_is_compatible"]
                   and out["unchanged_with_the_reader_declared"] and out["arrival_stress"] == "UNSET")
    return out


def contrast_pneumonia() -> dict:
    """P2V-1-11: structural only. Fever, sepsis and respiratory stress are not separated numerically."""
    rows = {}
    for case in ("pneumonia_46f", "pneumonia_83m"):
        row = AUTHORED[case]
        band = _neutral_band(case)
        a = _authored_anchors(case, glucose=row["glucose"], spo2=row["spo2"], crt_s=row["crt_s"])
        prof = reader(base_profile())
        rows[case] = {"authored": row, "evidence": list(INDEPENDENT_EVIDENCE[case]), "neutral_band": band,
                      "gap_bpm": round(row["hr"] - band[1], 2),
                      "candidate_contributors": ["fever", "sepsis / hypoperfusion (CRT 4, lactate above 3)",
                                                 "hypoxaemia", "respiratory distress (RR and work of breathing)"],
                      "unchanged_with_the_reader_declared":
                          at_arrival(a, base_profile())["hr"] == at_arrival(a, prof)["hr"],
                      "arrival_stress": "UNSET", "status": CONTRAST_STATUS[case],
                      "separation": "NOT_ATTEMPTED: no numeric split of fever, sepsis and respiratory stress"}
    out = {"cases": rows,
           "why": "both cases carry several candidate contributors at once, so a stress value fitted to the HR gap "
                  "would be an identifiability failure, not physiology. The temperature can only CONSTRAIN a family "
                  "region (TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION); no universal temperature -> stress "
                  "mapping exists."}
    out["pass"] = all(r["gap_bpm"] > 0.0 and r["unchanged_with_the_reader_declared"]
                      and r["arrival_stress"] == "UNSET" for r in rows.values())
    return out


def contrast_anaphylaxis() -> dict:
    """P2V-1-12: the beta-blockade guard. No anaphylaxis writer, no tone change, no epinephrine."""
    row = AUTHORED["anaphylaxis_63m_betablocked"]
    prof = reader(base_profile())
    af = _authored_anchors("anaphylaxis_63m_betablocked", spo2=row["spo2"], crt_s=row["crt_s"],
                           glucose=row["glucose"])
    af_stress = replace(af, arrival_systemic_stress=PROBE_STRESS)
    blocked = probe_anchors(beta_blockade=1.0)
    blocked_stress = replace(blocked, arrival_systemic_stress=PROBE_STRESS)
    partial = probe_anchors(beta_blockade=0.5)
    out = {"authored": row, "evidence": list(INDEPENDENT_EVIDENCE["anaphylaxis_63m_betablocked"]),
           "af_rate_is_the_rhythms": (at_arrival(af, prof)["hr"] == row["hr"]
                                      and at_arrival(af_stress, prof)["hr"] == row["hr"]),
           "full_blockade_suppresses": (at_arrival(blocked_stress, prof)["hr"] == at_arrival(blocked, prof)["hr"]),
           "partial_blockade_attenuates": (
               at_arrival(replace(partial, arrival_systemic_stress=PROBE_STRESS), prof)["hr"]
               - at_arrival(partial, prof)["hr"]
               < at_arrival(replace(probe_anchors(), arrival_systemic_stress=PROBE_STRESS), prof)["hr"]
               - at_arrival(probe_anchors(), prof)["hr"]),
           "target_still_rises_under_blockade": (
               at_arrival(blocked_stress, prof)["sympathetic_target"]
               > at_arrival(blocked, prof)["sympathetic_target"]),
           "not_implemented": ["anaphylaxis family writer", "distributive tone physiology", "epinephrine",
                               "an anaphylaxis arrival mapping"],
           "arrival_stress": "UNSET", "status": CONTRAST_STATUS["anaphylaxis_63m_betablocked"],
           "why": "a beta-blocked patient in AF at 64 is the structural guard: whatever the stress, the sympathetic "
                  "target rises and the rate does not, because the beta-blockade is downstream and a non-sinus rate "
                  "is the rhythm's. The architecture cannot manufacture tachycardia, which is what a residual fit "
                  "would have done."}
    out["pass"] = (out["af_rate_is_the_rhythms"] and out["full_blockade_suppresses"]
                   and out["partial_blockade_attenuates"] and out["target_still_rises_under_blockade"]
                   and out["arrival_stress"] == "UNSET")
    return out


def contrasts() -> dict:
    found = {"hypoglycemia_28m": contrast_hypoglycaemia(), "acs_70f_left_main": contrast_acs(),
             "renal_colic_34m": contrast_renal_colic(), "pneumonia": contrast_pneumonia(),
             "anaphylaxis_63m_betablocked": contrast_anaphylaxis()}
    out = {**found, "note": "SYNTHETIC stress and gains against the authored truth; no case is mapped, no arrival "
                            "value is calibrated and nothing is approved"}
    out["pass"] = all(v["pass"] for v in found.values())
    return out


# P2V-1-13 / -14: the arrival-region methodology (no lookup table) -------------------------------------------------------------

ARRIVAL_METHODOLOGY = (
    "1. The arrival systemic stress is a latent FAMILY_CANDIDATE / CASE MAPPING state: part of a case's arrival "
    "mapping when its family is migrated, never a canonical channel and never a number read off the HR.",
    "2. It may be declared only where INDEPENDENT authored evidence constrains it: a measured metabolic cause "
    "(glucose), autonomic markers (diaphoresis, tremor), an ischaemic or painful stimulus, fever, agitation. The "
    "observed HR is not evidence for its own explanation.",
    "3. The evidence constrains a REGION, not a point: a non-empty interval of arrival values compatible with every "
    "authored observable of that case, as P2S-3, P2T-3 and P2U-1 did for their own latent states.",
    "4. The HR may be used only to TEST a region (is it empty? does it overshoot the authored HR?), never to generate "
    "the value: a region solved from the residual is a fit, not physiology.",
    "5. Where the authored evidence does not separate the stress from another candidate contributor (fever vs sepsis "
    "vs respiratory stress), the case stays NOT_SEPARABLE and no region is proposed.",
    "6. No universal lookup table, in any direction: no glucose -> stress number, no temperature -> stress number, no "
    "pain descriptor -> stress number. A family may anchor its own region; the anchor is not a formula.",
    "7. Every magnitude stays UNSET until the faculty approves one. The AI proposes a method and a region; it never "
    "approves a value, and it never fits one to an observable.",
)

ANCHOR_STATUS = {
    "glucose": "GLUCOSE_CAN_ANCHOR_FAMILY_STRESS_REGION (approved as an anchor of a family region); "
               "GLUCOSE_TO_STRESS_MAPPING_APPROVED = False (no universal numeric mapping)",
    "temperature": "TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION (approved as a constraint on a family region); no "
                   "universal numeric mapping",
    "pain": "COMPATIBILITY only: a pain descriptor may justify a writer in a migrated family; it forces no value and "
            "maps to no number (renal_colic_34m is the control)",
    "autonomic_markers": "diaphoresis, tremor and agitation are ordinal authored evidence: they constrain a region's "
                         "ordering, never its magnitude",
    "hr_residual": "NEVER_AN_ANCHOR: the residual tests a region, it never generates one",
}
GLUCOSE_TO_STRESS_MAPPING_APPROVED = False
TEMPERATURE_TO_STRESS_MAPPING_APPROVED = False
PAIN_TO_STRESS_MAPPING_APPROVED = False
#: The only literals this module ever writes into the stress or its arrival anchor, by repr: the boolean and the 1.0
#: of the refusal probes, the 1e4 of the saturation probe and the 1e6 of the no-upper-bound probe. No case value, no
#: glucose, temperature or pain number: every case value stays the string UNSET.
ALLOWED_STRESS_LITERALS = ("1.0", "10000.0", "1000000.0", "True")


def _stress_literals() -> list:
    """Every numeric literal this module ever puts in the stress or its arrival anchor, read from its own source: the
    structural proof that no case, glucose, temperature or pain value is written anywhere here."""
    text = _live(OWN[0])
    return sorted({repr(node.value.value) for node in ast.walk(ast.parse(text)) if isinstance(node, ast.keyword)
                   and node.arg in (NEW_AUX, NEW_ANCHOR) and isinstance(node.value, ast.Constant)
                   and isinstance(node.value.value, (int, float, bool))})


def arrival_methodology() -> dict:
    """The method, the anchor statuses and the proof that no numeric mapping exists in this package."""
    rows = contrasts()
    cases = {k: v for k, v in rows.items() if k != "note" and k != "pass"}
    statuses = {k: (v.get("status") if "status" in v else {c: r["status"] for c, r in v["cases"].items()})
                for k, v in cases.items()}
    out = {"methodology": list(ARRIVAL_METHODOLOGY), "anchor_status": ANCHOR_STATUS,
           "mappings_approved": {"glucose": GLUCOSE_TO_STRESS_MAPPING_APPROVED,
                                 "temperature": TEMPERATURE_TO_STRESS_MAPPING_APPROVED,
                                 "pain": PAIN_TO_STRESS_MAPPING_APPROVED},
           "case_status": statuses, "stress_literals": _stress_literals(),
           "authored_rows_carry_no_stress": all(NEW_AUX not in row and "stress" not in row for row in
                                                AUTHORED.values()),
           "every_case_unset": all(v.get("arrival_stress", "UNSET") == "UNSET" for v in cases.values()
                                   if "arrival_stress" in v)
           and all(r["arrival_stress"] == "UNSET" for r in cases["pneumonia"]["cases"].values()),
           "no_lookup_table": "no function here maps an authored observable to a stress value; the only numeric "
                              "literals the stress ever receives are the refusal and saturation probes"}
    out["pass"] = (not any(out["mappings_approved"].values()) and out["authored_rows_carry_no_stress"]
                   and out["every_case_unset"]
                   and set(out["stress_literals"]) <= set(ALLOWED_STRESS_LITERALS))
    return out


# P2V-1-15: the parameter state -------------------------------------------------------------------------------------------------

UNSET_MAGNITUDES = {
    NEW_PROFILE_FIELD: "UNSET (None): no systemic-stress reader is declared in any committed profile; the probe gains "
                       "here are SYNTHETIC_ONLY",
    NEW_ANCHOR: "UNSET (0.0 in every committed arrival mapping): no case carries an arrival stress",
    "glucose_to_stress": "UNSET and not approved (no mapping)",
    "temperature_to_stress": "UNSET and not approved (no mapping)",
    "pain_to_stress": "UNSET and not approved (no mapping)",
    "writer_rates": "UNSET: no family writer exists, so no rate of rise or resolution is declared",
    "upper_bound": "UNSET by decision: the stress has no clinical ceiling (0 is none)",
}


def parameters() -> dict:
    """Every magnitude this package could have chosen, and the evidence that none of them is set."""
    state, note = dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, ""))
    out = {"unset": UNSET_MAGNITUDES, "registry_state": state,
           "registry_note": note,
           "declared_in_the_registry": NEW_PROFILE_FIELD in dv.PARAMETERS,
           "candidate_input_outside_case_parameters": NEW_ANCHOR not in CASE_PARAMETERS,
           "candidate_inputs": list(CANDIDATE_INPUTS),
           "committed_gains": {name: p.systemic_stress_to_sympathetic_gain
                               for name, (_, p) in committed_pairs().items()},
           "committed_arrival": {name: getattr(a, NEW_ANCHOR) for name, (a, _) in committed_pairs().items()},
           "synthetic_only": {"sympathetic_gain": SYMPATHETIC_GAIN, "other_gain": OTHER_GAIN,
                              "stress_grid": list(STRESS_GRID), "probe_stress": PROBE_STRESS,
                              "stress_step": STRESS_STEP, "baroreflex_gain": BARO_GAIN,
                              "baroreflex_map_set": BARO_MAP_SET, "deficit_delivery": DEFICIT_DELIVERY,
                              "arrival_debt": ARRIVAL_DEBT}}
    out["pass"] = (out["declared_in_the_registry"] and out["registry_state"] == "provisional"
                   and "UNSET" in out["registry_note"] and out["candidate_input_outside_case_parameters"]
                   and all(v is None for v in out["committed_gains"].values())
                   and all(v == 0.0 for v in out["committed_arrival"].values()))
    return out


# P2V-1-17 / -18: the debts carried from P2T-5 and P2U-1 -----------------------------------------------------------------------

CARRIED_DEBTS = {
    "HYPOXEMIC_FEEDBACK_STABILITY_AUDIT_DEFERRED": {
        "from": "P2T-5", "status": "DEFERRED, untouched",
        "note": "the hypoxaemic respiratory drive stays UNSET and unactivated; P2V-1 adds no feedback and the stress "
                "never feeds the respiratory drive, so the audit stays deferred to its own package",
    },
    "P2T5_LATENT_PAO2_PHYSICAL_FLOOR": {
        "from": "P2T-5", "status": "NOT_REQUIRED_BY_P2V1",
        "note": "the latent PaO2 floor max(0, .) would be declared PHYSICAL_FLOOR only if a live implementation "
                "forced the decision. P2V-1 touches no oxygenation code and no P2T-5 file, so nothing is decided and "
                "P2T-5 is not modified for it",
    },
    "P2T5_R_CLINICAL_UNSET": {
        "from": "P2T-5", "status": "UNSET",
        "note": "the respiratory quotient stays UNSET in every committed profile; 0.8 remains "
                "SYNTHETIC_PHYSIOLOGIC_REFERENCE and is used only in probes",
    },
    "STEADY_STATE_W_ARRIVAL_TENSION": {
        "from": "P2U-1", "status": "ACCEPTED_MODELING_DEBT / NOT_A_PHASE2_BLOCKER",
        "note": "carried as the faculty accepted it: the arrival efficiency the algebraic PaCO2 reads against the "
                "carried intrinsic RR is not resolved here and does not block Phase 2",
    },
    "OPIOID_ARRIVAL_AVAILABILITY_UNSET": {
        "from": "P2U-1", "status": "FAMILY_CANDIDATE / REGION",
        "note": "the arrival central availability stays a region per carried intrinsic RR (35m 0.30-0.50, 67f "
                "0.40-0.67); no value is chosen",
    },
    "OPIOID_HR_FAMILY_GAP": {
        "from": "P2U-1", "status": "CARRIED, NOT PATCHED",
        "note": "the authored HR of opioid_67f stays below the model's band. P2V-1 adds no opioid stress writer and "
                "no opioid HR term: a common input exists now, but using it to close this gap would be the residual "
                "fit the methodology forbids",
    },
}


def carried_debts() -> dict:
    """The carried debts and the evidence that this package did not quietly resolve any of them."""
    link_unset = {name: p.respiratory_quotient is None for name, (_, p) in committed_pairs().items()}
    hypoxaemic_unset = {name: p.hypoxaemic_drive_mapping is None for name, (_, p) in committed_pairs().items()}
    gap = {}
    for case in orf.CASES:
        a, p = orf.anchors(case), orf.common_profile()
        authored = a.hr
        model = at_arrival(a, p)["hr"]
        gap[case] = {"authored_hr": authored, "model_hr": round(model, 2), "gap_bpm": round(authored - model, 2),
                     "stress_writer": False, "opioid_hr_term": False}
    out = {"debts": CARRIED_DEBTS, "p2t5_link_unset": link_unset, "hypoxaemic_drive_unset": hypoxaemic_unset,
           "opioid_hr_gap": gap,
           "p2t5_files_untouched": all(v for k, v in common_untouched().items()
                                       if k in ("clinical_core/oxygenation_link.py",
                                                "clinical_core/oxygenation_link_report.py")),
           "no_opioid_stress_writer": not any("SystemicStressChange" in (CORE_DIR / "modules" / p.name).read_text(
               encoding="utf-8") for p in (CORE_DIR / "modules").glob("*.py"))}
    out["pass"] = (all(link_unset.values()) and all(hypoxaemic_unset.values()) and out["p2t5_files_untouched"]
                   and out["no_opioid_stress_writer"]
                   and all(not v["stress_writer"] and not v["opioid_hr_term"] for v in gap.values()))
    return out


# P2V-1-16: the default non-regression -----------------------------------------------------------------------------------------

def non_regression() -> dict:
    """With the reader UNSET and no stress writer: P2U-1's record reproduced on its tree (which nests P2T-5, P2T-3,
    P2T-1A, P2T-1, P2S-3, P2S-2 and, through them, GI, ACS, the oedema, PE, the asthma and the opioids)."""
    with p2u1_view():
        p2u1 = un.run()
    record = json.loads(un.RECORD.read_text(encoding="utf-8"))
    out = {"p2u1_record_reproduced_on_its_tree": json.loads(json.dumps(p2u1, sort_keys=True, default=str)) == record,
           "p2u1_record_untouched": hashlib.sha256(un.RECORD.read_bytes()).hexdigest() == P2U1_RECORD_SHA,
           "p2u1_verdict": p2u1["readiness"]["verdict"],
           "committed_arrival_stress_zero": {name: dv.arrival_state(a, p).aux.systemic_stress == 0.0
                                             for name, (a, p) in committed_pairs().items()},
           "tuples": {"DOWNSTREAM_REPORTS": REPORT in _downstream_reports(),
                      "PACK_DIGEST_EXCLUDED": set(TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(_pack_excluded())}}
    out["pass"] = (out["p2u1_record_reproduced_on_its_tree"] and out["p2u1_record_untouched"]
                   and all(out["committed_arrival_stress_zero"].values()) and all(out["tuples"].values()))
    return out


def _downstream_reports() -> tuple:
    from . import lactate_slice
    return lactate_slice.DOWNSTREAM_REPORTS


def _pack_excluded() -> tuple:
    from . import decision_pack
    return decision_pack.PACK_DIGEST_EXCLUDED


# The proof: the P2U-1 tree plus P2V-1's declared insertions --------------------------------------------------------------------

P2U1_HEAD = "53c2102"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/oxygenation_link.py", '
                                     '"clinical_core/oxygenation_link_report.py",\n'
                                     '                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py",\n'
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/oxygenation_link.py", '
                                     '"clinical_core/oxygenation_link_report.py",\n'
                                     '                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('AUXILIARY_SOURCES["central_availability"] = CENTRAL_AVAILABILITY\n'
                               "#: P2V-1: the core's sum of the families' systemic-stress changes into the common "
                               'systemic stress (the arrival value\n'
                               '#: plus every change since). It adds no kinetics and no coupling of its own. Read '
                               'only when a profile declares the gain.\n'
                               'SYSTEMIC_STRESS = Source(SourceKind.CORE_COUPLING, "systemic_stress")\n'
                               'AUXILIARY_SOURCES["systemic_stress"] = SYSTEMIC_STRESS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n',
                               'AUXILIARY_SOURCES["central_availability"] = CENTRAL_AVAILABILITY\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n'),
                              ('    respiratory_quotient: float | None = None\n'
                               '    # P2V-1: the systemic-stress reader of the sympathetic HR target, UNSET (None) '
                               'by default. Declared, it is the drive\n'
                               "    # per unit of the state's common systemic stress, added to the target like the "
                               'distress reader: upstream of the\n'
                               '    # common saturation and of the beta-blockade, never a respiratory reader (the '
                               'stress never feeds the respiratory\n'
                               '    # drive) and never solved from an observed HR. No value is chosen here.\n'
                               '    systemic_stress_to_sympathetic_gain: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    respiratory_quotient: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('                                     "physiology")\n'
                               '        gain = self.systemic_stress_to_sympathetic_gain\n'
                               '        if gain is not None and (isinstance(gain, bool) or not isinstance(gain, '
                               '(int, float))\n'
                               '                                 or not math.isfinite(gain) or gain <= 0.0):\n'
                               '            # P2V-1: UNSET is None (no reader); declared, the gain is finite and '
                               'positive (a stress never lowers the\n'
                               '            # drive).\n'
                               '            raise CoreInvariantError("systemic_stress_to_sympathetic_gain is None '
                               '(UNSET: no systemic-stress reader) "\n'
                               '                                     "or a finite positive drive per unit of '
                               'stress")\n'
                               '        rq = self.respiratory_quotient\n',
                               '                                     "physiology")\n'
                               '        rq = self.respiratory_quotient\n'),
                              ('                                                  "probes; not approved"),\n'
                               '    "systemic_stress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2V-1): sympathetic '
                               'drive per unit of the common "\n'
                               '                                                         "systemic stress '
                               '(non-respiratory adrenergic activation), "\n'
                               '                                                         "added to the HR target '
                               'upstream of the common saturation and "\n'
                               '                                                         "the beta-blockade; None by '
                               'default (no reader); it never "\n'
                               '                                                         "feeds the respiratory '
                               'drive and is never solved from an "\n'
                               '                                                         "observed HR; '
                               'SYNTHETIC_ONLY in probes; not approved"),\n'
                               '    "respiratory_quotient": (PROVISIONAL, "UNSET (P2T-5): the respiratory quotient '
                               'of the common relative alveolar link "\n',
                               '                                                  "probes; not approved"),\n'
                               '    "respiratory_quotient": (PROVISIONAL, "UNSET (P2T-5): the respiratory quotient '
                               'of the common relative alveolar link "\n'),
                              ('    check_distress_respiratory_effect(profile, '
                               'anchors.arrival_respiratory_distress)\n'
                               '    if anchors.arrival_systemic_stress != 0.0 and '
                               'profile.systemic_stress_to_sympathetic_gain is None:\n'
                               '        raise CoreInvariantError("an arrival systemic stress other than 0 needs a '
                               'declared systemic-stress reader "\n'
                               '                                 "(P2V-1); nothing else reads it")\n'
                               '    if anchors.arrival_central_availability != 1.0 and profile.acid_to_drive_gain is '
                               'None:\n',
                               '    check_distress_respiratory_effect(profile, '
                               'anchors.arrival_respiratory_distress)\n'
                               '    if anchors.arrival_central_availability != 1.0 and profile.acid_to_drive_gain is '
                               'None:\n'),
                              ('                                            '
                               'respiratory_distress=anchors.arrival_respiratory_distress,\n'
                               '                                            '
                               'central_availability=anchors.arrival_central_availability,\n'
                               '                                            '
                               'systemic_stress=anchors.arrival_systemic_stress))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n',
                               '                                            '
                               'respiratory_distress=anchors.arrival_respiratory_distress,\n'
                               '                                            '
                               'central_availability=anchors.arrival_central_availability))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n'),
                              ('    P2T-1: the common respiratory distress (aux.respiratory_distress) through its '
                               'own gain, UNSET (None) by default; it\n'
                               '    is respiratory afferent activation only. P2V-1: non-respiratory stress (pain, '
                               'hypoglycaemic counter-regulation,\n'
                               '    coronary stress, fever, agitation) is its own input (aux.systemic_stress) '
                               'through its own gain, UNSET (None) by\n'
                               '    default and independent of the distress reader; it never feeds the respiratory '
                               'drive.\n'
                               '    """\n',
                               '    P2T-1: the common respiratory distress (aux.respiratory_distress) through its '
                               'own gain, UNSET (None) by default; it\n'
                               '    is respiratory afferent activation only. Non-respiratory stress (pain, '
                               'hypoglycaemic counter-regulation, coronary\n'
                               '    stress, fever, agitation) is SYSTEMIC_STRESS_DEFERRED: no state or gain carries '
                               'it here.\n'
                               '    """\n'),
                              ('        target += profile.distress_to_sympathetic_gain * '
                               'state.aux.respiratory_distress\n'
                               '    if profile.systemic_stress_to_sympathetic_gain is not None:\n'
                               "        # P2V-1: the systemic-stress reader: its own gain times the state's absolute "
                               'stress (never relative to arrival),\n'
                               '        # independent of the distress reader and of every other term, through the '
                               'same saturation and beta-blockade;\n'
                               '        # UNSET (None) by default. It is the only reader of the stress: nothing '
                               'respiratory reads it.\n'
                               '        target += profile.systemic_stress_to_sympathetic_gain * '
                               'state.aux.systemic_stress\n'
                               '    # P2J-4: the direct baroreflex, on the MAP of this same state, after the other '
                               'terms (0 with the gain off).\n',
                               '        target += profile.distress_to_sympathetic_gain * '
                               'state.aux.respiratory_distress\n'
                               '    # P2J-4: the direct baroreflex, on the MAP of this same state, after the other '
                               'terms (0 with the gain off).\n')),
 'clinical_core/integration.py': (('                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange,\n'
                                   '                         SystemicStressChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n',
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n'),
                                  ('    availability: tuple[AvailabilityChange, ...] = ()  # changes to the common '
                                   'central availability this minute (P2U-1)\n'
                                   '    systemic_stress: tuple[SystemicStressChange, ...] = ()  # changes to the '
                                   'common systemic stress this minute (P2V-1)\n'
                                   '\n',
                                   '    availability: tuple[AvailabilityChange, ...] = ()  # changes to the common '
                                   'central availability this minute (P2U-1)\n'
                                   '\n'),
                                  ('                              "AvailabilityChange records")\n'
                                   '    if not isinstance(contribution.systemic_stress, tuple) or any(not '
                                   'isinstance(item, SystemicStressChange)\n'
                                   '                                                                  for item in '
                                   'contribution.systemic_stress):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the systemic stress '
                                   'changes only by a tuple of "\n'
                                   '                              "SystemicStressChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n',
                                   '                              "AvailabilityChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n'),
                                  ('                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress\n'
                                   '                 + contribution.availability + contribution.systemic_stress):\n'
                                   '        if item.source != contributor.source:\n',
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress\n'
                                   '                 + contribution.availability):\n'
                                   '        if item.source != contributor.source:\n'),
                                  ('    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    availability, systemic_stress = [], []\n'
                                   '    internal = {}\n',
                                   '    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    availability = []\n'
                                   '    internal = {}\n'),
                                  ('        availability.extend(contribution.availability)\n'
                                   '        systemic_stress.extend(contribution.systemic_stress)\n'
                                   '        if contribution.internal is not None:\n',
                                   '        availability.extend(contribution.availability)\n'
                                   '        if contribution.internal is not None:\n'),
                                  ('                         respiratory_distress=_distress_after(state, distress, '
                                   'profile, minute),\n'
                                   '                         central_availability=_availability_after(state, '
                                   'availability, profile, minute),\n'
                                   '                         systemic_stress=_systemic_stress_after(state, '
                                   'systemic_stress, profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n',
                                   '                         respiratory_distress=_distress_after(state, distress, '
                                   'profile, minute),\n'
                                   '                         central_availability=_availability_after(state, '
                                   'availability, profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n'),
                                  ('                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress), '
                                   'availability=tuple(availability),\n'
                                   '                          systemic_stress=tuple(systemic_stress))\n'
                                   '    _check_conservation(state, new_state, record)\n',
                                   '                          auxiliary=changes, demand=tuple(modifiers), '
                                   'blood=blood_changes,\n'
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress), '
                                   'availability=tuple(availability))\n'
                                   '    _check_conservation(state, new_state, record)\n'),
                                  ('\n'
                                   'def _systemic_stress_after(state: CoreState, stress: list, profile: CoreProfile, '
                                   'minute: int) -> float:\n'
                                   '    """P2V-1: the systemic stress after the minute: the value it starts with '
                                   "plus the minute's changes, summed once by\n"
                                   "    P2T-1A's rule (``distress_sum``: math.fsum and the binary64 roundoff bound "
                                   'at 0). The core adds no kinetics and no\n'
                                   '    coupling of its own. With its reader UNSET nothing reads it, so a change is '
                                   'refused; a minute that would take it\n'
                                   '    materially below 0 is refused, never held."""\n'
                                   '    if stress and profile.systemic_stress_to_sympathetic_gain is None:\n'
                                   '        raise ProvenanceError(f"minute {minute}: {stress[0].source.key} changed '
                                   'the systemic stress while its reader is "\n'
                                   '                              "UNSET (P2V-1): nothing would read it")\n'
                                   '    value = distress_sum(state.aux.systemic_stress, [item.amount for item in '
                                   'stress])\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the systemic stress changes '
                                   'take it to {value!r}, below 0 (P2V-1)")\n'
                                   '    return value\n'
                                   '\n'
                                   '\n'
                                   'def _availability_after(state: CoreState, availability: list, profile: '
                                   'CoreProfile, minute: int) -> float:\n',
                                   '\n'
                                   'def _availability_after(state: CoreState, availability: list, profile: '
                                   'CoreProfile, minute: int) -> float:\n'),
                                  ('        raise ProvenanceError("the central drive availability changed by other '
                                   'than its recorded changes")\n'
                                   '    if after.aux.systemic_stress != distress_sum(before.aux.systemic_stress,\n'
                                   '                                                 [item.amount for item in '
                                   'record.systemic_stress]):\n'
                                   "        # P2V-1: the systemic stress moves by exactly the minute's recorded "
                                   'changes, never otherwise.\n'
                                   '        raise ProvenanceError("the systemic stress changed by other than its '
                                   'recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n',
                                   '        raise ProvenanceError("the central drive availability changed by other '
                                   'than its recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/oxygenation_link_report.py",\n'
                                     '                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/oxygenation_link_report.py",\n'
                                     '                      "clinical_core/opioid_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class SystemicStressChange:\n'
                                  '    """P2V-1: one source\'s change to the common systemic stress in one minute.\n'
                                  '\n'
                                  '    The amount adds to the stress the minute starts with (finite; 0 changes '
                                  'nothing), as a distress change adds to the\n'
                                  '    distress: the stress has no reference above 0 to scale, so the changes are '
                                  'additive. It stays where its writers\n'
                                  '    leave it: it never moves, back to arrival or anywhere else, without a change '
                                  'that names its source, and the core\n'
                                  '    adds no kinetics of its own. The stress is a common input, never a disease '
                                  'term: a family declares what its own\n'
                                  '    process (counter-regulation, ischaemic stress, pain, fever) does to it, and '
                                  'the core only sums the changes. A minute\n'
                                  '    whose changes would take it below 0 is refused. No amount is approved; with '
                                  'its reader UNSET a change is refused,\n'
                                  '    because nothing would read it.\n'
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
                                  '            raise ProvenanceError(f"a systemic stress change is a finite number, '
                                  'not {self.amount!r}")\n'
                                  '        object.__setattr__(self, "amount", float(self.amount))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every systemic stress change names its '
                                  'Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "systemic_stress", "amount": self.amount, "source": '
                                  'self.source.to_dict(),\n'
                                  '                "minute": self.minute, "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AvailabilityChange:\n',
                                  '@dataclass(frozen=True)\nclass AvailabilityChange:\n'),
                                 ('    availability: tuple[AvailabilityChange, ...] = field(default=())\n'
                                  '    systemic_stress: tuple[SystemicStressChange, ...] = field(default=())\n'
                                  '\n',
                                  '    availability: tuple[AvailabilityChange, ...] = field(default=())\n\n'),
                                 ('        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress + '
                                  'self.availability + self.systemic_stress):\n'
                                  '            if item.minute != self.minute:\n',
                                  '        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress + '
                                  'self.availability):\n'
                                  '            if item.minute != self.minute:\n'),
                                 ('                "distress": [item.to_dict() for item in self.distress],\n'
                                  '                "availability": [item.to_dict() for item in self.availability],\n'
                                  '                "systemic_stress": [item.to_dict() for item in '
                                  'self.systemic_stress]}\n'
                                  '\n',
                                  '                "distress": [item.to_dict() for item in self.distress],\n'
                                  '                "availability": [item.to_dict() for item in self.availability]}\n'
                                  '\n')),
 'clinical_core/state.py': (('                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress",\n'
                             '                              "arrival_central_availability", '
                             '"arrival_systemic_stress"),\n'
                             '}\n',
                             '                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress",\n'
                             '                              "arrival_central_availability"),\n'
                             '}\n'),
                            ('    arrival_central_availability: float = 1.0\n'
                             '    # P2V-1 candidate input, read only by the systemic-stress reader of the '
                             'sympathetic target (UNSET by default) and\n'
                             "    # outside the case-parameter / migration registry, as P2S-2's, P2T-1's and "
                             "P2U-1's: the arrival non-respiratory\n"
                             '    # sympathetic / adrenergic activation, a case / family latent arrival state '
                             'constrained by independent authored\n'
                             '    # evidence (measured hypoglycaemia, diaphoresis / tremor, severe pain, fever, '
                             'agitation, ischaemic descriptors),\n'
                             '    # never inverted from the HR residual. At or above 0 with no upper bound; 0, the '
                             'default, is none.\n'
                             '    arrival_systemic_stress: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    arrival_central_availability: float = 1.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the arrival central drive availability is '
                             'between 0 and 1 (P2U-1)")\n'
                             '        if isinstance(self.arrival_systemic_stress, bool) or not '
                             'isinstance(self.arrival_systemic_stress, (int, float)) \\\n'
                             '                or not math.isfinite(self.arrival_systemic_stress) or '
                             'self.arrival_systemic_stress < 0.0:\n'
                             '            raise CoreInvariantError("the arrival systemic stress is finite and at or '
                             'above 0 (P2V-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the arrival central drive availability is '
                             'between 0 and 1 (P2U-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'),
                            ('                            "SpO2, mechanics, distress, consciousness or N; 1 and '
                             'constant unless a family writes it",\n'
                             '    "systemic_stress": "the common systemic stress (P2V-1): non-respiratory central / '
                             'adrenergic stress activation "\n'
                             '                       "(hypoglycaemic counter-regulation, ischaemic / coronary '
                             'stress, severe pain, fever or "\n'
                             '                       "inflammatory stress, authored agitation), at or above 0 with '
                             'no upper bound, 0 none; the case\'s "\n'
                             '                       "latent arrival value plus every family change since '
                             '(provenance.SystemicStressChange); it "\n'
                             '                       "raises the sympathetic HR target only, through its own UNSET '
                             'gain, upstream of the common "\n'
                             '                       "saturation and the beta-blockade. Not the respiratory distress '
                             '(that is respiratory afferent "\n'
                             '                       "activation), not the oxygen deficit, D, the baroreflex, '
                             'hypoxaemia, hypercapnia, the "\n'
                             '                       "respiratory drive, RR, pain, temperature or glucose '
                             'themselves, and never a residual solved "\n'
                             '                       "from the observed HR; 0 and constant unless a family writes '
                             'it",\n'
                             '}\n',
                             '                            "SpO2, mechanics, distress, consciousness or N; 1 and '
                             'constant unless a family writes it",\n'
                             '}\n'),
                            ('    central_availability: float = 1.0\n    systemic_stress: float = 0.0\n\n',
                             '    central_availability: float = 1.0\n\n'),
                            ('            raise CoreInvariantError("the central drive availability is between 0 and '
                             '1")\n'
                             '        if self.systemic_stress < 0:\n'
                             '            # P2V-1: 0 is none; there is no ceiling (no clinical upper bound is '
                             'chosen).\n'
                             '            raise CoreInvariantError("the systemic stress is never negative")\n'
                             '\n',
                             '            raise CoreInvariantError("the central drive availability is between 0 and '
                             '1")\n'
                             '\n'))}
CORE_AT_P2U1 = {'clinical_core/decision_pack.py': '3ccef16c92fd6b5913710a1904456a99eb66e2613b5046c02bbb4c3401f010fd',
 'clinical_core/derived.py': '2359dbc3dd8b631b0d127eb3fc87268095ebfb6034ae2261c390ecf42adb094c',
 'clinical_core/integration.py': 'ea3af770c5e7d1f4212554b4273c9b1f16ef512ad2bf5fc598b6f441febf72a3',
 'clinical_core/lactate_slice.py': 'bba510a03bfe7af540adc71228b82f2238c7541de99da7c4da60a44f459329bd',
 'clinical_core/provenance.py': '08a35345d261ee1e66e6f7fb3503b23d0237ce66b3282cfa2d97f554b1597811',
 'clinical_core/state.py': '614bf2a9cef139b46dfb146d474a0103f04a2f876a7c045d8132f2a9ca543ee2'}
# </reversal>
# <common>
COMMON_AT_P2U1 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/modules/opioid.py': '479b0ceb756b52db2abf6576d9feea0d650fd75943e8504a17a8304574e565c4',
 'clinical_core/modules/pulmonary_edema.py': '01e68556c919efa24ff6186eacf22c98e2ec882bf5cd52109bbafaffd8351679',
 'clinical_core/modules/pulmonary_embolism.py': '147881394c9208b35e2e2fdb7bb0ab42d589785000784379a8b1c1460df204c7',
 'clinical_core/modules/rhythm_events.py': '1036a2443e44fe5e2fde80736984b6828542b69454cc49a36e660ee8d436c86b',
 'clinical_core/opioid_migration.py': '272e6aa0327e06d84fe082bb677972db4a8017a001660d0e1d62c441add482b6',
 'clinical_core/opioid_migration_report.py': '529f273d2354889fc09547371e990b23f27f7f40f30a9779c66e59b36a73e246',
 'clinical_core/opioid_reference.py': 'db32552a049ecb8d19ebf5ee4cadb5d9613432666ec48420315cd8e62482f4d7',
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
P2U1_FREEZE_DIGEST = "6638a22d34afcdef746f9718291b346b07d51e91d1e848dd82952f034178d2e5"
P2U1_RECORD_SHA = "409f9870f237cc286339f0340780f1be30fbe7cc2204eeb71327d80f02ca8a2b"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2U1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2U1.items()}


def p2u1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2U-1 file plus P2V-1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2u1_bytes(relative: str) -> bytes:
    return p2u1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2u1_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2U1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


#: The closed packages whose hash list of unchanged files still reads the live bytes: P2U-1's. Every older package's
#: list is already redirected by its own newer neighbour's chain, and those readers compose the whole chain of
#: reversals, which this one must not override.
CLOSED_COMMON = ("opioid_migration",)


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2u1_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


def _un_p2t5_bytes(relative: str) -> bytes:
    """P2U-1's p2t5_bytes on the P2U-1 tree: its own reversed files from the P2U-1 text, every other file's P2U-1
    bytes."""
    return un.p2t5_text(relative).encode("utf-8") if relative in un.REVERSAL else p2u1_bytes(relative)


class _TreeFile:
    """One of P2V-1's changed files as P2U-1 left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2u1_text(self.relative)

    def read_bytes(self):
        return p2u1_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


_NEW_FILES = OWN + (REPORT,)


def _old_only(paths) -> list:
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in _NEW_FILES]


class _TreeDir:
    """A closed package's ``ROOT`` or ``CORE_DIR`` (or a directory under either): the P2U-1 text of P2V-1's changed
    files, the live path of anything else, and its listings without P2V-1's new files."""

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

    def __str__(self):
        # P2U-1's own view wraps this one (its ``__fspath__`` reads str(path)), so the text of a wrapped directory is
        # the real path, never this object's repr.
        return str(self.path)


def without_new_keys(value):
    """A closed record's view of a live serialization: P2V-1's new arrival anchor (in an Anchors dict, naming its case)
    and new auxiliary field (in an AuxiliaryState dict) dropped where they hold their reference 0, and a minute
    record's empty systemic-stress list dropped; anything else as it is."""
    if isinstance(value, dict):
        if "case_id" in value and NEW_ANCHOR in value:
            if value[NEW_ANCHOR] != 0.0:
                raise AssertionError("a closed course read a new candidate input away from its reference")
            value = {k: v for k, v in value.items() if k != NEW_ANCHOR}
        # The auxiliary state and a minute record are told apart by the type the new name holds, and by keys no
        # reversal removes (an older package's filter may already have dropped the newer names).
        if NEW_AUX in value and "sympathetic_drive" in value and "oxygen_demand" in value:
            if value[NEW_AUX] != 0.0:
                raise AssertionError("a closed course moved the systemic stress")
            value = {k: v for k, v in value.items() if k != NEW_AUX}
        if NEW_AUX in value and "minute" in value and "deltas" in value and value[NEW_AUX] == []:
            value = {k: v for k, v in value.items() if k != NEW_AUX}
        return {k: without_new_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_new_keys(v) for v in value]
    return value


#: Every closed analysis module whose listings of the representation (``fields``, the auxiliary fields,
#: ``dataclasses``) must read P2V-1's new field and anchor as P2U-1 left them.
CLOSED_LIVE = ("opioid_migration",) + un.CLOSED_LIVE
#: P2V-1's new names, dropped where a closed listing of the representation reads them.
NEW_NAMES = (NEW_AUX, NEW_ANCHOR, NEW_PROFILE_FIELD)


def _fields_at_p2u1(cls):
    """dataclasses.fields as the tree a closed package was frozen against had them: without P2V-1's new names, and
    then P2U-1's own filter, so the two compose whichever chain is applied last."""
    return tuple(f for f in un._fields_at_p2t5(cls) if f.name not in NEW_NAMES)


def _raw_fields_at_p2u1(cls):
    """Only P2V-1's own filter. The composed ``_fields_at_p2u1`` would recurse here through P2U-1's filter."""
    return tuple(f for f in dataclasses.fields(cls) if f.name not in NEW_NAMES)


class _DataclassesAtP2U1:
    """``dataclasses`` as a closed module sees it on the P2U-1 tree: ``fields`` filtered, everything else untouched."""

    fields = staticmethod(_raw_fields_at_p2u1)

    def __getattr__(self, name):
        return getattr(dataclasses, name)


_FREEZE_SOURCES = bf.freeze_sources
#: The auxiliary fields and sources as P2U-1 left them: P2V-1's one new field (0 in every closed course) out. Patched
#: only so a closed listing of the representation reads them as P2U-1 did.
P2U1_AUXILIARY_FIELDS = {k: v for k, v in mc.AUXILIARY_FIELDS.items() if k != NEW_AUX}
P2U1_AUXILIARY_SOURCES = {k: v for k, v in dv.AUXILIARY_SOURCES.items() if k != NEW_AUX}
#: The closed modules' import-time snapshots, each taken while P2V-1's names were already live: the module, the
#: attribute and the key that must go. Patched from the module's current value, so the order the chains are applied in
#: does not matter.
CLOSED_SNAPSHOTS = (("opioid_migration", "P2T5_AUXILIARY_FIELDS", NEW_AUX),
                    ("opioid_migration", "P2T5_AUXILIARY_SOURCES", NEW_AUX),
                    ("oxygenation_link", "P2T3_PARAMETERS", NEW_PROFILE_FIELD),
                    ("respiratory_distress", "P2S3_AUXILIARY_FIELDS", NEW_AUX))

#: Every closed analysis module that reads a core file by path rather than through its own ``_live``: on the P2U-1 tree
#: each must read P2V-1's changed files as P2U-1 left them, and list clinical_core without P2V-1's new files. P2U-1's
#: own paths are not redirected: it reads P2V-1's changed files through its ``_live`` (redirected here) and its own path
#: reads touch no file this package changed, while its view's path arithmetic needs its ROOT to stay a plain path.
PATH_READERS = un.PATH_READERS


def _imported_closed_modules() -> list:
    """The closed analysis modules whose path readers a closed view must redirect, imported by name (never through the
    interpreter's module table, so the shadow core imports nothing a shadow does not need)."""
    return [__import__(f"clinical_core.{name}", fromlist=["ROOT"]) for name in PATH_READERS]


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2U-1's view reads the P2U-1 files (proven) and their bytes, its
    captured source map is P2U-1's; the closed listings of the auxiliary state and the closed serializations read them
    as P2U-1 left them (P2V-1's new field and anchor at their reference 0 out, an empty stress list out). P2V-1 changes
    no behaviour without a declared reader."""
    patch.setattr(un, "_live", p2u1_text)
    patch.setattr(un, "p2t5_bytes", _un_p2t5_bytes)
    patch.setattr(un, "_FREEZE_SOURCES", lambda: p2u1_sources(_FREEZE_SOURCES()))
    for module_name in CLOSED_COMMON:
        module = __import__(f"clinical_core.{module_name}", fromlist=["common_untouched"])
        patch.setattr(module, "common_untouched", _closed_common_untouched(module))
    # Every closed analysis module that reads a core file by path reads the P2U-1 text, and its listings of
    # clinical_core leave P2V-1's new files out: the tree as P2U-1 left it. A reader a newer chain already wrapped is
    # left alone (it composes the whole chain of reversals through the redirected ``_live``).
    for module in _imported_closed_modules():
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                # The tree as P2U-1 left it: P2V-1's changed files reversed, its new files out of every listing, the
                # opioid files (P2U-1's own) in.
                patch.setattr(module, attribute, _TreeDir(value))
            elif isinstance(value, un._TreeDir) and isinstance(getattr(value, "path", None), Path):
                # P2U-1's chain ran first and left its own wrapper (its own chain skips a reader that is no longer a
                # plain path): its view is rebuilt over P2V-1's, so the text stays the one P2U-1 was frozen against and
                # both views' new files stay out of the listings.
                patch.setattr(module, attribute, un._TreeDir(_TreeDir(value.path)))
    for module_name in CLOSED_LIVE:
        module = __import__(f"clinical_core.{module_name}", fromlist=["_live"])
        if hasattr(module, "fields"):
            # P2U-1 is the newest closed package: its own listings still see its new field and anchor, only P2V-1's
            # names go. Every older package's listing composes both filters.
            patch.setattr(module, "fields", _raw_fields_at_p2u1 if module is un else _fields_at_p2u1)
        if hasattr(module, "dataclasses"):
            patch.setattr(module, "dataclasses", _DataclassesAtP2U1())
        if hasattr(module, "AUXILIARY_FIELDS"):
            # Derived from whatever a newer chain already put there, so the order the chains are applied in does not
            # matter.
            patch.setattr(module, "AUXILIARY_FIELDS",
                          {k: v for k, v in module.AUXILIARY_FIELDS.items() if k != NEW_AUX})
    for module_name, attribute, key in CLOSED_SNAPSHOTS:
        module = __import__(f"clinical_core.{module_name}", fromlist=[attribute])
        patch.setattr(module, attribute, {k: v for k, v in getattr(module, attribute).items() if k != key})
    patch.setattr(dv, "AUXILIARY_SOURCES", {k: v for k, v in dv.AUXILIARY_SOURCES.items() if k != NEW_AUX})
    # The live registry and P2T-5's snapshot of it (which P2T-5's chain installs) both read P2V-1's new parameter, so
    # both are filtered from whatever a newer chain already put there.
    patch.setattr(dv, "PARAMETERS", {k: v for k, v in dv.PARAMETERS.items() if k != NEW_PROFILE_FIELD})
    # Composed with whatever a newer chain already put there (P2U-1's view drops the availability), and with P2U-1's
    # own filter, which a nested P2U-1 view rebuilds from the captured original: P2V-1's names go first, there too.
    dm_without, mc_without = dm.without_new_keys, mc.without_new_anchor_key
    un_without = un.without_new_keys
    patch.setattr(un, "without_new_keys", lambda value: un_without(without_new_keys(value)))
    patch.setattr(dm, "without_new_keys", lambda value: dm_without(without_new_keys(value)))
    patch.setattr(mc, "without_new_anchor_key", lambda value: mc_without(without_new_keys(value)))


_UN_TREE = un.tree


def _un_tree(patch) -> None:
    """P2U-1's own whole-tree view, nested inside P2V-1's: its chain, and then the path readers P2V-1 already wrapped
    (which its own chain leaves alone, because they are no longer plain paths) wrapped again by its view, so a nested
    P2U-1 view reads the P2T-5 tree exactly as it did at P2U-1's head."""
    _UN_TREE(patch)
    for module in _imported_closed_modules():
        if module is un:
            continue
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if isinstance(value, _TreeDir):
                patch.setattr(module, attribute, un._TreeDir(value))


def tree(patch) -> None:
    """The whole P2U-1 tree, for P2U-1's own analysis and tests: the chain, the source map, and P2U-1's own nested view
    composed with this one."""
    chain(patch)
    patch.setattr(un, "tree", _un_tree)
    patch.setattr(bf, "freeze_sources", lambda: p2u1_sources(_FREEZE_SOURCES()))


class p2u1_view:
    """P2V-1's analysis reading the tree P2U-1 froze, for its own proofs and its record."""

    def __enter__(self):
        self._patch = mc._Patch()
        tree(self._patch)
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2u1_view():
        digest = un.freeze_digest()
        proof = un.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2u1_freeze_digest": digest == P2U1_FREEZE_DIGEST,
            "p2u1_proof": all(proof["proofs"].values()) and all(proof["common_untouched"].values())
            and proof["p2t5_freeze_digest"] and proof["p2t5_proof"] and proof["p2t5_record"],
            "p2u1_record": hashlib.sha256(un.RECORD.read_bytes()).hexdigest() == P2U1_RECORD_SHA}


# P2V-1-19: readiness (predeclared) --------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "the architecture is minimal and declared: one auxiliary field, one arrival anchor, one writer record, one gain, "
    "with their refusals (representation, reader audit)",
    "the reader feeds the sympathetic HR target only: no respiratory function reads the stress and the whole "
    "respiratory chain is unchanged by it (S3, isolation)",
    "the respiratory distress and the systemic stress stay two independent signals and compose additively (S4, S9)",
    "the common effector is untouched: the stress enters upstream of the saturation and of the beta-blockade and "
    "never bypasses them (S2, S6, S7)",
    "the other sympathetic terms stay independently addressable and the existing hypoglycaemia term is unchanged and "
    "classified (S8, the hypoglycaemia audit)",
    "every magnitude stays UNSET and no observable is mapped to a stress number (the parameter state, the arrival "
    "methodology, every contrast UNSET)",
    "the case contrasts hold structurally, the negative control forces nothing and the beta-blockade guard holds "
    "(the five contrasts)",
    "nothing prior changes by default: with the gain UNSET every prior reading is exact and P2U-1's record reproduces "
    "on its tree (S1, S10, the non-regression, the proof)",
)
READY = "COMMON_SYSTEMIC_STRESS_ARCHITECTURE_READY"
NOT_READY = "NOT_READY"
READINESS_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def readiness(found: dict) -> dict:
    p, proof = found["probes"], found["proof"]
    checks = (
        found["representation"]["pass"] and found["reader"]["pass"],
        p["S3"]["pass"] and found["isolation"]["pass"],
        p["S4"]["pass"] and p["S9"]["pass"],
        p["S2"]["pass"] and p["S6"]["pass"] and p["S7"]["pass"],
        p["S8"]["pass"] and found["hypoglycaemia"]["pass"],
        found["parameters"]["pass"] and found["arrival_methodology"]["pass"],
        found["contrasts"]["pass"],
        p["S1"]["pass"] and p["S10"]["pass"] and found["non_regression"]["pass"]
        and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2u1_freeze_digest"] and proof["p2u1_proof"] and proof["p2u1_record"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    return {"criteria": rows, "blocker": blocker, "rule": READINESS_RULE,
            "verdict": READY if blocker is None else f"{NOT_READY} - {blocker}"}


def design() -> dict:
    return {"decisions": DECISIONS, "semantics": SEMANTICS, "probes": PROBES,
            "synthetic": {"sympathetic_gain": SYMPATHETIC_GAIN, "other_gain": OTHER_GAIN,
                          "stress_grid": list(STRESS_GRID), "probe_stress": PROBE_STRESS,
                          "stress_step": STRESS_STEP, "course_minutes": COURSE_MINUTES,
                          "beta_blockades": list(BETA_BLOCKADES), "distress_gain": DISTRESS_GAIN,
                          "respiratory_gain": RESPIRATORY_GAIN, "probe_distress": PROBE_DISTRESS,
                          "baroreflex_gain": BARO_GAIN, "baroreflex_map_set": BARO_MAP_SET,
                          "deficit_delivery": DEFICIT_DELIVERY, "arrival_debt": ARRIVAL_DEBT,
                          "low_spo2": LOW_SPO2, "low_glucose": LOW_GLUCOSE, "recovered_glucose": RECOVERED_GLUCOSE},
            "authored": AUTHORED, "independent_evidence": {k: list(v) for k, v in INDEPENDENT_EVIDENCE.items()},
            "contrast_status": CONTRAST_STATUS, "methodology": list(ARRIVAL_METHODOLOGY),
            "anchor_status": ANCHOR_STATUS, "unset": UNSET_MAGNITUDES, "carried_debts": CARRIED_DEBTS,
            "hypoglycaemia_status": HYPOGLYCAEMIA_STATUS, "resting_hr": list(RESTING_HR),
            "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2u1": CORE_AT_P2U1, "common_at_p2u1": COMMON_AT_P2U1,
            "p2u1": {"head": P2U1_HEAD, "freeze_digest": P2U1_FREEZE_DIGEST, "record": P2U1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2u1": hashlib.sha256(un.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "representation": representation(),
             "reader": reader_audit(), "isolation": respiratory_isolation(), "hypoglycaemia": hypoglycaemia_term(),
             "probes": structural_probes(), "contrasts": contrasts(),
             "arrival_methodology": arrival_methodology(), "parameters": parameters(),
             "carried_debts": carried_debts(), "non_regression": non_regression()}
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
