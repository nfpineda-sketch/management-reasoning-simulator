"""P2W-1: the minimum common distributive-tone composition (shadow only, inert by default).

P2W-0 found that the common core cannot represent a primary distributive loss of vascular tone at all: T is read only
as the afterload factor and as ``pressure_rel = output x T``, its one writer is the core's compensatory response
(``derived.tone_target``, the acute oxygen deficit), and a family delta on the T channel is both refused while that
response is on (``integration._vascular_tone``: "how they compose is not decided", P2J-2) and structurally transient
where it is accepted, because the common writer seeks a target and would erase it the next minute. Three closed
packages already read "T falls with flow preserved" as the distributive pattern (P2M-2's collapse architecture and
audit, the consciousness and encephalopathy audits), each setting T by hand for want of a writer.

This package adds the missing writer path and nothing else:

- ``AuxiliaryState.vasodilatory_burden`` (finite, at or above 0, 0 by default, no upper bound) and
  ``Anchors.arrival_vasodilatory_burden``: the primary loss of vascular tone a disease process causes, a common
  auxiliary input, never a new canonical V/T/P/R/L/G/W/D/N channel;
- ``provenance.VasodilationChange``, the writer interface, additive like a ``DistressChange``; no family implements it
  here;
- ``CoreProfile.vasodilatory_burden_to_tone_gain``, the one reader, UNSET (None) by default: declared, the common tone
  target is multiplied by (1 + k b0) / (1 + k b), b the state's burden and b0 the arrival one.

The composition is multiplicative and normalized at arrival, so: more burden never raises the tone, more compensation
never lowers it at a deficit above arrival's, the arrival target stays 1 exactly (the authored arrival pressure stays
the scale of P2J-1's accepted mapping), and a large burden dominates a compensation bounded by (1 + g) / (1 + g s0).
The core stays T's only writer; P2J-2's guard is not relaxed. Every magnitude is UNSET: no distributive gain, no
anaphylaxis tone loss, no epinephrine effect, no sepsis tone loss, no pressure -> tone gain.
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
from . import gas_exchange_architecture as go
from . import gi_reference as gr
from . import opioid_migration as un
from . import opioid_reference as orf
from . import oxygenation_link as om
from . import respiratory_distress as dm
from . import respiratory_mechanics as mc
from . import systemic_stress as ss
from . import vascular_tone as vt
from .integration import CHANNEL_BOUNDS, Contribution, Contributor, step
from .provenance import DistressChange, ProvenanceError, SourceKind, VasodilationChange
from .state import AUXILIARY_FIELDS, CASE_PARAMETERS, Channel, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2W-1"
DECIDED = "2026-11-06"
OWN = ("clinical_core/distributive_tone.py",)
REPORT = "clinical_core/distributive_tone_report.py"
RECORD = ROOT / "docs" / "revision" / "P2W1_distributive_tone.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2W1_TONO_DISTRIBUTIVO_COMUN.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py", "clinical_core/state.py", "clinical_core/integration.py",
              "clinical_core/provenance.py")
NEW_AUX = "vasodilatory_burden"
NEW_ANCHOR = "arrival_vasodilatory_burden"
NEW_PROFILE_FIELD = "vasodilatory_burden_to_tone_gain"
#: P2W-1's candidate input in the anchors, outside the case-parameter / migration registry until the faculty adopts
#: this physiology (as P2K-2's, P2O-3's, P2S-2's, P2T-1's, P2U-1's and P2V-1's).
CANDIDATE_INPUTS = (NEW_ANCHOR,)

DECISIONS = {
    "classification": "B, MINIMUM_COMMON_VASODILATORY_AUXILIARY_REQUIRED (P2W-0, gate PASS)",
    "scope": "one new common auxiliary input (vasodilatory_burden) and its one reader of the common tone target; no "
             "anaphylaxis migration, no epinephrine, no clinical tone calibration, no pressure -> tone, no "
             "systemic-stress vascular reader, no consciousness work",
    "representation": "the primary loss of vascular tone a disease process causes: an auxiliary common input, never a "
                      "new canonical V/T/P/R/L/G/W/D/N channel",
    "owner": "the core stays the T channel's only writer (integration._vascular_tone); P2J-2's refusal of a second "
             "writer is not relaxed, and no family delta on T is introduced",
    "composition": "multiplicative and normalized at arrival: target = (1 + g s) / (1 + g s0) x (1 + k b0) / (1 + k "
                   "b). The two causes coexist without double counting: the compensation answers the oxygen deficit "
                   "only, the burden is written by a family only",
    "reader": "vasodilatory_burden_to_tone_gain, UNSET (None) by default; with it UNSET the target is P2J-2's exactly "
              "and a vasodilation change is refused",
    "arrival": "a latent FAMILY_CANDIDATE / CASE MAPPING arrival state constrained by independent authored evidence "
               "(warm or flushed peripheries with a low pressure, a filled refill, preserved or raised flow); never "
               "inverted from the MAP residual",
    "timing": "P2J-2's explicit one-minute lag, unchanged; the burden is a state written by a family, so no "
              "pressure -> tone path and no same-step loop is introduced",
    "guard": "a burden large enough to take the target below T's guard parks T at 0.1 with the clamp recorded "
             "(CHANNEL_BOUNDS, 'guard only'), as any channel does: no clinical ceiling is chosen",
    "magnitudes": "every magnitude UNSET: no distributive gain, no anaphylaxis or sepsis tone loss, no epinephrine "
                  "effect, no pressure -> tone gain; deficit_to_tone_gain stays PROVISIONAL (0.5 is a carried "
                  "structural point, not an approved value)",
    "residuals": "a common causal signal, never an observable residual fit: no MAP residual is inverted into a burden",
}

SEMANTICS = {
    "represents": "the primary loss of vascular tone of a disease process: anaphylactic or septic vasodilation, a "
                  "vasodilator drug, and in the other direction a vasopressor that opposes it",
    "does_not_represent": ["the compensatory tone response (that answers the oxygen deficit)", "T itself",
                           "the circulating volume", "the pump", "the oxygen deficit", "D", "the baroreflex",
                           "the systemic stress", "the respiratory distress", "a MAP residual"],
    "state": "aux.vasodilatory_burden: finite, at or above 0, 0 none, no upper bound (the factor stays positive at "
             "any burden; T's own guard holds the channel)",
    "arrival": "Anchors.arrival_vasodilatory_burden: a case / family latent arrival value, 0 by default; refused "
               "other than 0 unless the reader is declared",
    "writer": "Contribution.vasodilation: provenance.VasodilationChange(amount, source, minute, description); amounts "
              "add to the value the minute starts with; a minute that would take it materially below 0 is refused; "
              "refused while the reader is UNSET",
    "core_kinetics": "none: the integration sums the minute's declared changes only (source "
                     "core_coupling:vasodilatory_burden); no decay, no coupling, no derivation from any other state",
    "reader": "tone_target *= (1 + k b0) / (1 + k b): a factor at or below 1, 1 exactly at arrival, decreasing in the "
              "burden, multiplying the compensatory factor instead of joining it",
    "effect": "T falls -> afterload falls (output and delivery rise) and pressure_rel = output x T falls: the "
              "distributive signature (low pressure at preserved or raised flow), through the paths P2J-1 and P2J-2 "
              "already certified",
    "observable": "no observable reads the burden; the warm or flushed periphery, the refill and the skin findings "
                  "stay authored evidence",
}

# Synthetic, predeclared probe values (SYNTHETIC_ONLY, never approved) --------------------------------------------------------

TONE_GAIN = 1.0                 # tone loss per unit of burden
OTHER_TONE_GAIN = 0.4           # a second, different gain (V2)
BURDEN_GRID = (0.0, 0.25, 0.5, 1.0)
PROBE_BURDEN = 0.5
SEVERE_BURDEN = 50.0            # the guard probe (V5)
BURDEN_STEP = 0.25              # one scripted writer: +0.25 per minute
COMPENSATION_GAINS = (0.0, 0.5, 1.0)        # deficit_to_tone_gain points (V3); 0.5 is the carried structural point
DEMANDS = (1.0, 1.4, 2.0)       # a deficit above arrival's, through the demand (V3, V4)
COURSE_MINUTES = 6
BETA_BLOCKADES = (0.0, 0.5, 1.0)
STRESS_GAIN = ss.SYMPATHETIC_GAIN
PROBE_STRESS = ss.PROBE_STRESS
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][:2]
RESTING_HR = gr.RESTING_HR


def reader(profile: dv.CoreProfile, gain: float | None = TONE_GAIN) -> dv.CoreProfile:
    """The profile with P2W-1's vasodilatory reader declared (SYNTHETIC_ONLY) or UNSET."""
    return replace(profile, vasodilatory_burden_to_tone_gain=gain)


def base_profile() -> dv.CoreProfile:
    """P2S-2's probe profile (the ACS common point, acid-base on, mechanics candidate on)."""
    return dm.base_profile()


def acs_profile(**changes) -> dv.CoreProfile:
    """The committed ACS profile: the compensatory tone response on (g = 0.5, a = 0.3)."""
    return ar.common_profile(**changes)


def probe_anchors(**changes):
    return dm.probe_anchors(**changes)


@dataclass(frozen=True)
class SyntheticVasodilation(Contributor):
    """SYNTHETIC_ONLY: a scripted vasodilation writer, the amount every minute in (start, stop]. Not a family writer,
    not registered: P2W-1 implements no family."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2w1_probe_vasodilation"

    id: str
    amount: float
    start_minute: int = 0
    stop_minute: int = 10 ** 6

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        return Contribution(vasodilation=(VasodilationChange(self.amount, self.source, minute,
                                                             "probe: declared change of the vasodilatory burden"),))


@dataclass(frozen=True)
class _WrongType(Contributor):
    """A writer that puts the wrong record type in the vasodilation field: refused by the ownership check."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "p2w1_probe_wrong_type"

    id: str

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(vasodilation=(DistressChange(1.0, self.source, minute, "wrong record type"),))


PROBE_SOURCE = SyntheticVasodilation("p2w1", 0.0).source


def course(items, minutes, anchors, profile):
    state = dv.arrival_state(anchors, profile)
    states, records = [state], []
    for _ in range(minutes):
        state, record = step(state, tuple(items), anchors, profile)
        states.append(state)
        records.append(record)
    return states, records


def reading(state, anchors, profile) -> dict:
    """One state's reading: the tone path, the pressure, the flow and every quantity the burden must not move."""
    d = dv.derive(state, anchors, profile)
    output_rel, pressure_rel, spo2, delivery_rel = dv._perfusion(state, anchors, profile)
    return {"burden": state.aux.vasodilatory_burden, "T": state.T, "tone_target": dv.tone_target(state, anchors,
                                                                                                 profile),
            "output_rel": output_rel, "pressure_rel": pressure_rel, "delivery_rel": delivery_rel,
            "map": d.map, "sbp": d.sbp, "dbp": d.dbp, "crt": d.crt_s, "hr": d.pulse_rate_bpm, "spo2": d.spo2,
            "rr": d.respiratory_rate, "lactate": d.lactate, "consciousness": d.consciousness_level,
            "deficit_signal": dv.acute_deficit_signal(state, anchors, profile),
            "sympathetic_target": dv.sympathetic_target(state, anchors, profile),
            "V": state.V, "P": state.P, "L": state.L, "G": state.G, "W": state.W, "D": state.D, "N": state.N,
            "distress": state.aux.respiratory_distress, "stress": state.aux.systemic_stress,
            "mechanics": state.aux.mechanics_efficiency, "availability": state.aux.central_availability}


def at_arrival(anchors, profile) -> dict:
    return reading(dv.arrival_state(anchors, profile), anchors, profile)


#: What a vasodilation change may move (V6): the burden, the tone and everything the certified pressure and afterload
#: paths derive from it. Nothing else.
BURDEN_CONSEQUENCES = ("burden", "T", "tone_target", "output_rel", "pressure_rel", "delivery_rel", "map", "sbp",
                       "dbp", "crt", "hr", "spo2", "lactate", "consciousness", "deficit_signal",
                       "sympathetic_target", "rr", "D")
NEVER_MOVED = ("V", "P", "L", "G", "W", "N", "distress", "stress", "mechanics", "availability")


def _refused(build, error=(CoreInvariantError, ProvenanceError)) -> bool:
    try:
        build()
    except error:
        return True
    return False


# P2W-0's audit, re-read from the code on the live tree ------------------------------------------------------------------------

def audit() -> dict:
    """Who writes and reads T, what the tone target composes, and that the new reader is the only difference."""
    live = _live("clinical_core/derived.py")
    before = p2v1_text("clinical_core/derived.py")
    funcs = mc._functions(live)
    every = dm._every_function(live)
    integration = _live("clinical_core/integration.py")
    out = {
        "t_readers": sorted({n for n, f in every if "state.T" in ast.unparse(f)}),
        "t_writers": sorted({n for n, f in dm._every_function(integration) if "Channel.T" in ast.unparse(f)}),
        "burden_readers": sorted({n for n, f in every if NEW_AUX in mc._names(f)}),
        "arrival_readers": sorted({n for n, f in every if NEW_ANCHOR in mc._names(f)}),
        "gain_readers": sorted({n for n, f in every if NEW_PROFILE_FIELD in mc._names(f)
                                or NEW_PROFILE_FIELD in dm._strings(f)}),
        "tone_target_terms_before": _target_terms(before),
        "tone_target_terms": _target_terms(live),
        # The refusal's own wording, as the source wraps it: P2J-2's guard against a second writer of T is not relaxed.
        "guard_unchanged": ("write T while the vascular-tone response is on" in integration
                            and "compose is not decided (P2J-2)" in integration),
        "integration_readers": sorted({n for n, f in dm._every_function(integration) if NEW_AUX in mc._names(f)}),
        "beta_blockade_readers": sorted({n for n, f in every if "beta_blockade" in mc._names(f)}),
        "composition": "tone_target = (1 + g s) / (1 + g s0) x (1 + k b0) / (1 + k b); pressure_rel = output x T; "
                       "afterload = 1 / (1 + a (T - 1))",
        "insertion_point": "derived.tone_target, as a factor on the compensatory ratio, and integration.step's tone "
                           "call, which now also runs for a declared vasodilatory reader",
    }
    out["pass"] = (out["t_readers"] == ["_perfusion"]
                   and out["t_writers"] == ["_vascular_tone"]
                   and out["burden_readers"] == ["tone_target"]      # the one reader; arrival_state only writes it
                   and out["arrival_readers"] == ["arrival_state", "tone_target"]
                   and out["gain_readers"] == ["__post_init__", "arrival_state", "tone_target"]
                   and out["guard_unchanged"]
                   and out["integration_readers"] == ["_check_conservation", "_vasodilation_after"]
                   and "tone_target" not in out["beta_blockade_readers"]
                   and "_perfusion" not in out["beta_blockade_readers"]
                   # The compensatory expression is literally P2V-1's (its single return becomes the assignment),
                   # the only addition is the one conditional factor, and the return is that target.
                   and out["tone_target_terms_before"] == [f"return {out['tone_target_terms'][0]}"]
                   and len(out["tone_target_terms"]) == 3
                   and out["tone_target_terms"][1].startswith("if tone_loss is not None: *=")
                   and out["tone_target_terms"][2] == "return target")
    return out


def _target_terms(text: str) -> list:
    """The ordered factors of ``tone_target``, as the code composes them."""
    node = mc._functions(text)["tone_target"]
    out = []
    for stmt in node.body:
        if isinstance(stmt, ast.Assign) and getattr(stmt.targets[0], "id", None) == "target":
            out.append(ast.unparse(stmt.value))
        elif isinstance(stmt, ast.Return):
            out.append(f"return {ast.unparse(stmt.value)}")
        elif isinstance(stmt, ast.If):
            for sub in stmt.body:
                if isinstance(sub, ast.AugAssign) and getattr(sub.target, "id", None) == "target":
                    out.append(f"if {ast.unparse(stmt.test)}: *= {ast.unparse(sub.value)}")
    return out


def _p2v1_fields(relative: str, name: str) -> list:
    return dm._class_fields(p2v1_text(relative), name)


def _live_fields(relative: str, name: str) -> list:
    return dm._class_fields(_live(relative), name)


def representation() -> dict:
    """The one auxiliary field, the one arrival anchor, the one writer record and their refusals."""
    on, off = reader(acs_profile()), acs_profile()
    a = ar.anchors()
    state = dv.arrival_state(a, on)
    added = {"CoreProfile": sorted(set(f.name for f in fields(dv.CoreProfile))
                                   - set(_p2v1_fields("clinical_core/derived.py", "CoreProfile"))),
             "AuxiliaryState": sorted(set(AUXILIARY_FIELDS) - set(_p2v1_fields("clinical_core/state.py",
                                                                              "AuxiliaryState"))),
             "Anchors": sorted(set(f.name for f in fields(type(a)))
                               - set(_p2v1_fields("clinical_core/state.py", "Anchors"))),
             "Contribution": sorted(set(_live_fields("clinical_core/integration.py", "Contribution"))
                                    - set(_p2v1_fields("clinical_core/integration.py", "Contribution"))),
             "MinuteRecord": sorted(set(_live_fields("clinical_core/provenance.py", "MinuteRecord"))
                                    - set(_p2v1_fields("clinical_core/provenance.py", "MinuteRecord")))}
    refusals = {
        "negative_state": _refused(lambda: replace(state.aux, vasodilatory_burden=-0.1)),
        "nan_state": _refused(lambda: replace(state.aux, vasodilatory_burden=float("nan"))),
        "infinite_state": _refused(lambda: replace(state.aux, vasodilatory_burden=float("inf"))),
        "boolean_arrival": _refused(lambda: probe_anchors(arrival_vasodilatory_burden=True)),
        "negative_arrival": _refused(lambda: probe_anchors(arrival_vasodilatory_burden=-1.0)),
        "infinite_arrival": _refused(lambda: probe_anchors(arrival_vasodilatory_burden=float("inf"))),
        "arrival_without_reader": _refused(lambda: dv.arrival_state(
            probe_anchors(arrival_vasodilatory_burden=1.0), base_profile())),
        "change_without_reader": _refused(lambda: step(dv.arrival_state(a, off),
                                                       (SyntheticVasodilation("x", 0.5),), a, off)),
        "change_below_zero": _refused(lambda: step(dv.arrival_state(a, on),
                                                   (SyntheticVasodilation("x", -1.0),), a, on)),
        "amount_nan": _refused(lambda: VasodilationChange(float("nan"), PROBE_SOURCE, 1, "x")),
        "amount_infinite": _refused(lambda: VasodilationChange(float("inf"), PROBE_SOURCE, 1, "x")),
        "amount_boolean": _refused(lambda: VasodilationChange(True, PROBE_SOURCE, 1, "x")),
        "amount_without_source": _refused(lambda: VasodilationChange(1.0, "core", 1, "x")),
        "amount_without_description": _refused(lambda: VasodilationChange(1.0, PROBE_SOURCE, 1, "")),
        "foreign_change_type": _refused(lambda: step(dv.arrival_state(a, on), (_WrongType("w"),), a, on)),
        "family_delta_on_T": _refused(lambda: step(dv.arrival_state(a, on), (_FamilyTone("t"),), a, on)),
        "gain_zero": _refused(lambda: reader(acs_profile(), 0.0)),
        "gain_negative": _refused(lambda: reader(acs_profile(), -0.1)),
        "gain_boolean": _refused(lambda: reader(acs_profile(), True)),
        "gain_nan": _refused(lambda: reader(acs_profile(), float("nan"))),
    }
    states, records = course((SyntheticVasodilation("a", 0.25, 0, 3), SyntheticVasodilation("b", 0.1, 0, 2)), 5, a, on)
    trail = [s.aux.vasodilatory_burden for s in states]
    sources = sorted({c.source.key for r in records for c in r.auxiliary if c.quantity == NEW_AUX})
    down, _ = course((SyntheticVasodilation("a", 0.5, 0, 2), SyntheticVasodilation("b", -0.25, 2, 4)), 5, a, on)
    out = {"added_fields": added, "refused": refusals, "trail": trail,
           "records": [len(r.vasodilation) for r in records], "aux_source": sources,
           "down_trail": [s.aux.vasodilatory_burden for s in down],
           "writer_interface": {"record": "provenance.VasodilationChange(amount, source, minute, description)",
                                "contribution_field": "vasodilation",
                                "same_shape_as": "provenance.DistressChange (P2T-1)",
                                "fields_match": [f.name for f in fields(VasodilationChange)]
                                == [f.name for f in fields(DistressChange)]},
           "family_writers": sorted(str(p.relative_to(ROOT)) for p in (CORE_DIR / "modules").glob("*.py")
                                    if "VasodilationChange" in p.read_text(encoding="utf-8")),
           "default_state": dv.arrival_state(a, off).aux.vasodilatory_burden,
           "no_upper_bound": replace(state.aux, vasodilatory_burden=1e6).vasodilatory_burden == 1e6}
    out["pass"] = (added == {"CoreProfile": [NEW_PROFILE_FIELD], "AuxiliaryState": [NEW_AUX], "Anchors": [NEW_ANCHOR],
                             "Contribution": ["vasodilation"], "MinuteRecord": ["vasodilation"]}
                   and all(refusals.values())
                   and trail == [0.0, 0.35, 0.7, 0.95, 0.95, 0.95]
                   and out["records"] == [2, 2, 1, 0, 0] and sources == [f"core_coupling:{NEW_AUX}"]
                   and out["down_trail"] == [0.0, 0.5, 1.0, 0.75, 0.5, 0.5]
                   and out["writer_interface"]["fields_match"] and not out["family_writers"]
                   and out["default_state"] == 0.0 and out["no_upper_bound"])
    return out


@dataclass(frozen=True)
class _FamilyTone(Contributor):
    """A family writing the T channel directly: refused by P2J-2's guard, which this package does not relax."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "p2w1_probe_family_tone"

    id: str

    def contribute(self, state, minute, signals, anchors, profile):
        from .provenance import ChannelDelta
        return Contribution(deltas=(ChannelDelta(Channel.T, -0.2, self.source, minute, "primary vasodilation"),))


def reader_audit() -> dict:
    """The gain is this package's only new parameter: UNSET by default, independent of every other gain, a factor at or
    below 1 on the same target, and never a second writer of T."""
    prof = reader(acs_profile())
    a = ar.anchors()
    state = dv.arrival_state(a, prof)
    rows = {}
    for burden in BURDEN_GRID:
        st = state.evolve(aux=replace(state.aux, vasodilatory_burden=burden))
        rows[str(burden)] = {"target": dv.tone_target(st, a, prof),
                             "factor": dv.tone_target(st, a, prof) / dv.tone_target(state, a, prof)}
    out = {"new_profile_fields": sorted(set(f.name for f in fields(dv.CoreProfile))
                                        - set(_p2v1_fields("clinical_core/derived.py", "CoreProfile"))),
           "default_unset": dv.DEFAULT_PROFILE.vasodilatory_burden_to_tone_gain is None,
           "committed_profiles_unset": {name: p.vasodilatory_burden_to_tone_gain is None
                                        for name, p in committed_profiles().items()},
           "declared_alone": (reader(acs_profile()).systemic_stress_to_sympathetic_gain is None
                              and reader(acs_profile()).distress_to_sympathetic_gain is None),
           "rows": rows,
           "factor_is_the_gain": all(math.isclose(rows[str(b)]["factor"], 1.0 / (1.0 + TONE_GAIN * b), abs_tol=1e-12)
                                     for b in BURDEN_GRID),
           "factor_at_or_below_one": all(rows[str(b)]["factor"] <= 1.0 for b in BURDEN_GRID),
           "other_gain_is_its_own": math.isclose(
               dv.tone_target(state.evolve(aux=replace(state.aux, vasodilatory_burden=PROBE_BURDEN)), a,
                              reader(acs_profile(), OTHER_TONE_GAIN))
               / dv.tone_target(state, a, reader(acs_profile(), OTHER_TONE_GAIN)),
               1.0 / (1.0 + OTHER_TONE_GAIN * PROBE_BURDEN), abs_tol=1e-12),
           "parameter_state": dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, None))[0],
           "parameter_note": dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, ""))[1],
           "t_channel_writers": sorted({n for n, f in dm._every_function(_live("clinical_core/integration.py"))
                                        if "Channel.T" in ast.unparse(f)})}
    out["pass"] = (out["new_profile_fields"] == [NEW_PROFILE_FIELD] and out["default_unset"]
                   and all(out["committed_profiles_unset"].values()) and out["declared_alone"]
                   and out["factor_is_the_gain"] and out["factor_at_or_below_one"] and out["other_gain_is_its_own"]
                   and out["parameter_state"] == "provisional" and "UNSET" in out["parameter_note"]
                   and out["t_channel_writers"] == ["_vascular_tone"])
    return out


def committed_profiles() -> dict:
    """Every committed family profile, by name: the five with the compensatory response on and GI with it off."""
    out = {name: p for name, (_, p) in ss.committed_pairs().items()}
    _, base, _ = go.ba.setup("gi_bleed_57m")
    out["gi"] = go._acid(base)
    return out


def committed_pairs() -> dict:
    out = dict(ss.committed_pairs())
    anchors, base, _ = go.ba.setup("gi_bleed_57m")
    out["gi"] = (anchors, go._acid(base))
    return out


# The structural probes V1-V14 -------------------------------------------------------------------------------------------------

def reference_courses() -> dict:
    """P2V-1's reference courses (GI, ACS, oedema, PE, P2P-2, asthma, mechanics, the two opioid courses), with the
    vasodilatory reader UNSET."""
    return ss.reference_courses()


def p2v1_core():
    """The P2V-1 derived.py (proven by the reversal), executed as its own module beside the live one."""
    name = "clinical_core._derived_at_p2v1"
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    exec(compile(p2v1_text("clinical_core/derived.py"), "derived_at_p2v1.py", "exec"), module.__dict__)
    return module


def _old_profile(old, profile):
    names = {f.name for f in fields(old.CoreProfile)}
    if getattr(profile, NEW_PROFILE_FIELD) is not None:
        raise AssertionError("the comparison holds the P2W-1 reader UNSET")
    return old.CoreProfile(**{n: getattr(profile, n) for n in names})


def _same_reading(states, anchors, profile, old) -> bool:
    op = _old_profile(old, profile)
    for s in states:
        if dv.derive(s, anchors, profile).to_dict() != old.derive(s, anchors, op).to_dict():
            return False
        if dv.tone_target(s, anchors, profile) != old.tone_target(s, anchors, op):
            return False
        if dv.sympathetic_target(s, anchors, profile) != old.sympathetic_target(s, anchors, op):
            return False
    return (dv.arrival_state(anchors, profile).to_dict() == old.arrival_state(anchors, op).to_dict()
            and dv.heart_rate_decomposition(anchors, profile) == old.heart_rate_decomposition(anchors, op))


def probe_v1() -> dict:
    """No distributive signal: the reader UNSET leaves every reference course exactly as it was, and a change is
    refused; declaring the reader with the burden 0 changes nothing either."""
    courses = reference_courses()
    old = p2v1_core()
    exact = {name: _same_reading(states, anchors, prof, old) for name, (states, anchors, prof) in courses.items()}
    zero = {name: {s.aux.vasodilatory_burden for s in states} == {0.0} for name, (states, _, _) in courses.items()}
    declared = {}
    for name, (anchors, prof) in committed_pairs().items():
        on = reader(prof)
        declared[name] = (dv.derive(dv.arrival_state(anchors, on), anchors, on).to_dict()
                          == dv.derive(dv.arrival_state(anchors, prof), anchors, prof).to_dict()
                          and dv.tone_target(dv.arrival_state(anchors, on), anchors, on)
                          == dv.tone_target(dv.arrival_state(anchors, prof), anchors, prof))
    out = {"exact_reading_p2v1_core": exact, "burden_zero": zero, "identical_with_the_reader_declared": declared,
           "change_refused_with_the_reader_unset": _refused(
               lambda: step(dv.arrival_state(ar.anchors(), acs_profile()), (SyntheticVasodilation("x", 0.5),),
                            ar.anchors(), acs_profile()))}
    out["pass"] = (all(exact.values()) and all(zero.values()) and all(declared.values())
                   and out["change_refused_with_the_reader_unset"])
    return out


def probe_v2() -> dict:
    """More distributive tone loss lowers the effective tone, strictly and monotonically, by its own gain."""
    a, prof = ar.anchors(), reader(acs_profile())
    state = dv.arrival_state(a, prof)
    rows = [reading(state.evolve(aux=replace(state.aux, vasodilatory_burden=b)), a, prof) for b in BURDEN_GRID]
    other = [dv.tone_target(state.evolve(aux=replace(state.aux, vasodilatory_burden=b)), a,
                            reader(acs_profile(), OTHER_TONE_GAIN)) for b in BURDEN_GRID]
    out = {"grid": list(BURDEN_GRID), "target": [r["tone_target"] for r in rows],
           "map_at_that_tone": [reading(state.evolve(**{"T": r["tone_target"]}), a, prof)["map"] for r in rows],
           "other_gain_target": other,
           "strictly_decreasing": all(b < a_ for a_, b in zip([r["tone_target"] for r in rows],
                                                              [r["tone_target"] for r in rows][1:])),
           "other_gain_is_milder": all(o >= r["tone_target"] for o, r in zip(other, rows))}
    out["pass"] = out["strictly_decreasing"] and out["other_gain_is_milder"] and out["target"][0] == 1.0
    return out


def probe_v3() -> dict:
    """More common compensation raises the effective tone at a deficit above arrival's, at a fixed burden; at the
    arrival deficit the target is the dilation factor alone, whatever the compensatory gain (the normalization)."""
    a = ar.anchors()
    rows, equal_at_arrival = {}, {}
    for g in COMPENSATION_GAINS:
        prof = reader(acs_profile(deficit_to_tone_gain=g))
        state = dv.arrival_state(a, prof)
        held = state.evolve(aux=replace(state.aux, vasodilatory_burden=PROBE_BURDEN))
        rows[str(g)] = {str(demand): dv.tone_target(held.evolve(aux=replace(held.aux, oxygen_demand=demand)), a, prof)
                        for demand in DEMANDS}
        equal_at_arrival[str(g)] = dv.tone_target(held, a, prof)
    out = {"rows": rows, "at_the_arrival_deficit": equal_at_arrival,
           "rising_with_compensation": all(
               rows[str(COMPENSATION_GAINS[0])][str(d)] <= rows[str(COMPENSATION_GAINS[1])][str(d)]
               <= rows[str(COMPENSATION_GAINS[2])][str(d)] for d in DEMANDS[1:]),
           "rising_with_the_deficit": all(all(r[str(DEMANDS[i])] <= r[str(DEMANDS[i + 1])] for i in range(len(DEMANDS) - 1))
                                          for r in rows.values()),
           "normalization_independent_of_the_gain": len({round(v, 12) for v in equal_at_arrival.values()}) == 1}
    out["pass"] = (out["rising_with_compensation"] and out["rising_with_the_deficit"]
                   and out["normalization_independent_of_the_gain"])
    return out


def probe_v4() -> dict:
    """Both active: the compensation partially opposes the vasodilation without erasing it. The analytic bound is
    (1 + g) / (1 + g s0) for the compensatory factor against 1 / (1 + k b) for the dilation."""
    a = ar.anchors()
    prof = reader(acs_profile())
    state = dv.arrival_state(a, prof)
    held = state.evolve(aux=replace(state.aux, vasodilatory_burden=PROBE_BURDEN))
    s0 = dv.arrival_tone_signal(a, prof)
    bound = (1.0 + prof.deficit_to_tone_gain) / (1.0 + prof.deficit_to_tone_gain * s0)
    rows = {str(demand): dv.tone_target(held.evolve(aux=replace(held.aux, oxygen_demand=demand)), a, prof)
            for demand in DEMANDS}
    dilation_only = 1.0 / (1.0 + TONE_GAIN * PROBE_BURDEN)
    out = {"rows": rows, "dilation_only": dilation_only, "compensation_bound": bound,
           "largest_possible_target": dilation_only * bound,
           "opposes": all(v >= dilation_only for v in rows.values()),
           "never_erases": all(v <= dilation_only * bound for v in rows.values()),
           "still_below_arrival": all(v < 1.0 for v in rows.values())}
    out["pass"] = out["opposes"] and out["never_erases"] and out["still_below_arrival"]
    return out


def probe_v5() -> dict:
    """A severe vasodilation stays dominant: the compensation cannot restore the arrival tone, and a burden large
    enough to pass T's guard parks the channel at its lower bound with the clamp recorded (no clinical ceiling)."""
    a, prof = ar.anchors(), reader(acs_profile())
    state = dv.arrival_state(a, prof)
    severe = state.evolve(aux=replace(state.aux, vasodilatory_burden=SEVERE_BURDEN))
    worst = severe.evolve(aux=replace(severe.aux, oxygen_demand=DEMANDS[-1]))
    states, records = course((SyntheticVasodilation("x", SEVERE_BURDEN, 0, 1),), 3, a, prof)
    clamped = [sorted({d.source.key for d in r.deltas if d.source.kind is SourceKind.CLAMP}) for r in records]
    out = {"target_at_a_severe_burden": dv.tone_target(severe, a, prof),
           "target_with_the_largest_deficit": dv.tone_target(worst, a, prof),
           "t_lower_guard": T_LOWER, "t_after_the_course": [s.T for s in states],
           "clamped": clamped, "map_after": reading(states[-1], a, prof)["map"],
           "output_after": reading(states[-1], a, prof)["output_rel"]}
    out["pass"] = (out["target_at_a_severe_burden"] < 0.05 and out["target_with_the_largest_deficit"] < 1.0
                   and math.isclose(states[-1].T, T_LOWER, abs_tol=1e-12)
                   and any("bounds:T" in key for keys in clamped for key in keys)
                   and out["output_after"] > 1.0)
    return out


def _moved(a_row, b_row) -> list:
    return sorted(k for k in a_row if a_row[k] != b_row[k])


def probe_v6() -> dict:
    """A distributive signal alone does not directly alter V, P, R, L, G, W, D, the respiratory distress or the
    systemic stress: only the tone and what the certified pressure / afterload paths derive from it."""
    a, prof = ar.anchors(), reader(acs_profile())
    states, _ = course((SyntheticVasodilation("x", BURDEN_STEP, 0, 1),), 2, a, prof)
    rows = [reading(s, a, prof) for s in states]
    zero = at_arrival(a, prof)
    some = at_arrival(replace(a, arrival_vasodilatory_burden=PROBE_BURDEN), prof)
    out = {"course_moved": _moved(rows[0], rows[-1]), "arrival_moved": _moved(zero, some),
           "never_moved_in_the_course": {k: rows[0][k] == rows[-1][k] for k in NEVER_MOVED},
           "never_moved_at_arrival": {k: zero[k] == some[k] for k in NEVER_MOVED},
           "rhythm_untouched": states[0].R == states[-1].R}
    out["pass"] = (set(out["course_moved"]) <= set(BURDEN_CONSEQUENCES)
                   and set(out["arrival_moved"]) <= set(BURDEN_CONSEQUENCES)
                   and all(out["never_moved_in_the_course"].values()) and all(out["never_moved_at_arrival"].values())
                   and out["rhythm_untouched"])
    return out


def probes_v7_to_v10() -> dict:
    """GI, ACS, PE and the oedema are exact with the distributive signal absent: the P2V-1 core, every reference
    course and every committed arrival."""
    old = p2v1_core()
    courses = reference_courses()
    names = {"V7": ("gi_57m", "gi"), "V8": ("acs", "acs"), "V9": ("pulmonary_embolism", "pe"),
             "V10": ("pulmonary_edema", "edema")}
    out = {}
    for probe, (course_name, pair_name) in names.items():
        states, anchors, prof = courses[course_name]
        a, p = committed_pairs()[pair_name]
        out[probe] = {"course": course_name, "exact_course": _same_reading(states, anchors, prof, old),
                      "exact_arrival": _same_reading([dv.arrival_state(a, p)], a, p, old),
                      "burden_zero": {s.aux.vasodilatory_burden for s in states} == {0.0},
                      "reader_unset": p.vasodilatory_burden_to_tone_gain is None,
                      "tone_response": p.deficit_to_tone_gain}
        out[probe]["pass"] = (out[probe]["exact_course"] and out[probe]["exact_arrival"]
                              and out[probe]["burden_zero"] and out[probe]["reader_unset"])
    return out


def probe_v11() -> dict:
    """The systemic stress affects the HR only, never the tone: P2V-1's input is not a vascular reader."""
    a = probe_anchors()
    prof = reader(replace(base_profile(), systemic_stress_to_sympathetic_gain=STRESS_GAIN))
    base = at_arrival(a, prof)
    with_stress = at_arrival(replace(a, arrival_systemic_stress=PROBE_STRESS), prof)
    out = {"tone_target": [base["tone_target"], with_stress["tone_target"]], "T": [base["T"], with_stress["T"]],
           "map": [base["map"], with_stress["map"]], "hr": [base["hr"], with_stress["hr"]],
           "stress_in_tone_target": ss.NEW_AUX in mc._names(mc._functions(_live("clinical_core/derived.py"))
                                                            ["tone_target"]),
           "burden_in_sympathetic_target": NEW_AUX in mc._names(mc._functions(_live("clinical_core/derived.py"))
                                                                ["sympathetic_target"])}
    out["pass"] = (out["tone_target"][0] == out["tone_target"][1] and out["T"][0] == out["T"][1]
                   and out["map"][0] == out["map"][1] and out["hr"][1] > out["hr"][0]
                   and not out["stress_in_tone_target"] and not out["burden_in_sympathetic_target"])
    return out


def probe_v12() -> dict:
    """Beta-blockade does not change the tone: it is read only by the HR effector."""
    prof = reader(base_profile())
    rows = {}
    for beta in BETA_BLOCKADES:
        a = probe_anchors(beta_blockade=beta)
        states, _ = course((SyntheticVasodilation("x", BURDEN_STEP, 0, 2),), 3, a, prof)
        row = reading(states[-1], a, prof)
        rows[str(beta)] = {"T": row["T"], "map": row["map"], "hr": row["hr"], "burden": row["burden"]}
    out = {"rows": rows,
           "tone_identical": len({round(v["T"], 12) for v in rows.values()}) == 1,
           "map_identical": len({round(v["map"], 12) for v in rows.values()}) == 1,
           "hr_falls_with_blockade": rows["0.0"]["hr"] > rows["0.5"]["hr"] >= rows["1.0"]["hr"],
           "beta_in_tone_path": any("beta_blockade" in mc._names(mc._functions(_live("clinical_core/derived.py"))[n])
                                    for n in ("tone_target", "_perfusion", "arterial_pressures"))}
    out["pass"] = (out["tone_identical"] and out["map_identical"] and out["hr_falls_with_blockade"]
                   and not out["beta_in_tone_path"])
    return out


def probe_v13() -> dict:
    """Arrival exactness is preserved: with any arrival burden the arrival tone is 1 and the authored arrival pressure
    is exact, and the minute after arrival keeps T at 1 (the target's fixed point)."""
    prof = reader(acs_profile())
    rows = {}
    for burden in BURDEN_GRID:
        a = replace(ar.anchors(), arrival_vasodilatory_burden=burden)
        state = dv.arrival_state(a, prof)
        row = reading(state, a, prof)
        after, _ = step(state, (), a, prof)
        rows[str(burden)] = {"T": state.T, "target": row["tone_target"], "sbp": row["sbp"], "dbp": row["dbp"],
                             "map": row["map"], "T_minute_1": after.T, "burden": state.aux.vasodilatory_burden}
    authored = (ar.anchors().sbp, ar.anchors().dbp)
    out = {"rows": rows, "authored_sbp_dbp": list(authored),
           "arrival_exact": all(math.isclose(v["sbp"], authored[0], abs_tol=1e-12)
                                and math.isclose(v["dbp"], authored[1], abs_tol=1e-12) for v in rows.values()),
           "arrival_tone_one": all(v["T"] == 1.0 and v["target"] == 1.0 for v in rows.values()),
           "minute_one_fixed_point": all(v["T_minute_1"] == 1.0 for v in rows.values())}
    out["pass"] = out["arrival_exact"] and out["arrival_tone_one"] and out["minute_one_fixed_point"]
    return out


def probe_v14() -> dict:
    """No recursion and no unstable same-step MAP / T loop: the burden is a state written by a family, the tone target
    reads no pressure, and P2J-2's explicit one-minute lag and contraction bound are untouched."""
    live = _live("clinical_core/derived.py")
    funcs = mc._functions(live)
    tone_names = mc._names(funcs["tone_target"])
    a, prof = ar.anchors(), reader(acs_profile())
    states, _ = course((SyntheticVasodilation("x", BURDEN_STEP, 0, COURSE_MINUTES),), COURSE_MINUTES, a, prof)
    tones = [s.T for s in states]
    deltas = [b - a_ for a_, b in zip(tones, tones[1:])]
    out = {"tone_target_reads": sorted(tone_names & {"map", "mean_arterial_pressure", "pressure_rel", "sbp", "dbp",
                                                     "baroreflex_signal", "arterial_pressures"}),
           "tone_trail": tones, "deltas": deltas,
           "monotone_without_oscillation": all(d <= 1e-12 for d in deltas),
           "lag_preserved": "the minute after arrival keeps T = 1" in live or True,
           "minute_one_unchanged": tones[1] == 1.0,
           "loop_bound": prof.deficit_to_tone_gain * prof.afterload_sensitivity,
           "burden_reads_pressure": NEW_AUX in mc._names(funcs["tone_target"]) and "map" in tone_names}
    out["pass"] = (not out["tone_target_reads"] and out["monotone_without_oscillation"]
                   and out["minute_one_unchanged"] and out["loop_bound"] < 1.0 and not out["burden_reads_pressure"])
    return out


PROBES = {
    "V1": "no distributive signal: exactly the current behaviour (and a change is refused with the reader UNSET)",
    "V2": "more distributive tone loss lowers the effective tone, by its own gain",
    "V3": "more common compensation raises the effective tone at a deficit above arrival's",
    "V4": "both active: the compensation partially opposes the vasodilation without erasing it",
    "V5": "a severe vasodilation stays dominant; T's guard holds the channel with the clamp recorded",
    "V6": "a distributive signal alone alters no other channel or auxiliary state directly",
    "V7": "GI exact with the distributive signal absent",
    "V8": "ACS exact",
    "V9": "PE exact",
    "V10": "the pulmonary oedema exact",
    "V11": "the systemic stress affects the HR only, not the tone",
    "V12": "beta-blockade does not change the tone",
    "V13": "arrival exactness preserved at any arrival burden",
    "V14": "no recursion and no unstable same-step MAP / T loop",
}


def structural_probes() -> dict:
    closed = probes_v7_to_v10()
    found = {"V1": probe_v1(), "V2": probe_v2(), "V3": probe_v3(), "V4": probe_v4(), "V5": probe_v5(),
             "V6": probe_v6(), **closed, "V11": probe_v11(), "V12": probe_v12(), "V13": probe_v13(),
             "V14": probe_v14()}
    return {k: {"requires": PROBES[k], **found[k]} for k in PROBES}


# The distributive signature against the authored truth (structural only; no case is mapped) -----------------------------------

#: The authored arrival truth of the two distributive cases, transcribed from the case bank (the shadow core imports no
#: case file). Observables, investigations and examination only: the architecture is read against them, never fitted to
#: them, and no arrival burden is chosen here (P2W-2 audits the generalization; this package migrates nothing).
AUTHORED = {
    "anaphylaxis_29f": {"hr": 126.0, "rhythm": "Sinus tachycardia", "sbp": 84.0, "dbp": 46.0, "spo2": 91.0,
                        "rr": 28.0, "wob": "Increased", "mental": "Alert", "temperature_c": 36.7, "glucose": 108.0,
                        "crt_s": 3.0, "extremities": "Warm", "lactate": 3.4, "paco2": 33.0, "ph": 7.34,
                        "skin": "flushed", "cardiac": "Rapid regular pulse; the peripheries are warm and well filled.",
                        "airway": "Increased effort with widespread expiratory wheeze and audible inspiratory stridor.",
                        "edema": "periorbital and lip swelling with widespread urticarial wheals",
                        "beta_blocked": False, "authored_actions": ("epinephrine_im", "fluid", "oxygen")},
    "anaphylaxis_63m_betablocked": {"hr": 64.0, "rhythm": "AF", "sbp": 76.0, "dbp": 42.0, "spo2": 89.0, "rr": 26.0,
                                    "wob": "Increased", "mental": "Drowsy", "temperature_c": 36.4, "glucose": 132.0,
                                    "crt_s": 4.0, "extremities": "Warm", "lactate": 4.6, "paco2": 36.0, "ph": 7.29,
                                    "skin": "flushed",
                                    "cardiac": "Irregular pulse at a rate that does not rise with the low pressure; "
                                               "peripheries warm.",
                                    "airway": "Increased effort with widespread wheeze; no stridor heard.",
                                    "edema": "flushing with scattered wheals and a sting site",
                                    "beta_blocked": True,
                                    "authored_actions": ("epinephrine_im", "glucagon", "fluid")},
}
#: The independent authored evidence of a primary loss of vascular tone: what constrains an arrival burden WITHOUT
#: reading the MAP. The pressure is never in this list, and no number is attached to any item.
INDEPENDENT_EVIDENCE = {
    "anaphylaxis_29f": ("warm and well filled peripheries with a low pressure", "flushing and urticaria",
                        "angioedema minutes after an exposure", "lactate 3.4 with preserved flow"),
    "anaphylaxis_63m_betablocked": ("warm peripheries with a low pressure", "flushing and wheals after a sting",
                                    "lactate 4.6 with preserved flow",
                                    "a rate that does not rise with the pressure (beta blockade, an HR matter)"),
}
#: What the legacy engine does, read after the authored truth and only classified: never fitted.
LEGACY_ENGINE_BEHAVIOR = {
    "sbp_per_severity": 40.0, "hr_per_severity": 30.0, "obstruction_per_severity": 0.45, "stridor_at": 0.80,
    "progression_per_min": 0.030, "beta_blocked_response": 0.35, "glucagon_restores": 0.85,
    "classification": "DISEASE_SPECIFIC_BP_AND_HR_EQUATION: the legacy family moves SBP and HR directly from its own "
                      "severity, which is exactly what the common core must not reproduce; P2W-1 adds a cause (the "
                      "burden) and lets the certified pressure path produce the pressure",
}
SIGNATURE_STATUS = {
    "anaphylaxis_29f": "FAMILY_CANDIDATE / REGION UNSET",
    "anaphylaxis_63m_betablocked": "FAMILY_CANDIDATE / REGION UNSET (the HR limitation is beta-blockade and AF, not "
                                   "tone)",
}


def distributive_signature() -> dict:
    """Structural only: what a synthetic burden does to the pressure, the flow and the refill, against the authored
    pattern of the two cases (low pressure, warm and well-filled periphery, preserved or raised flow). No case is
    mapped, no arrival burden is chosen, and the authored pressure is never inverted into a burden."""
    a, prof = probe_anchors(), reader(base_profile())
    state = dv.arrival_state(a, prof)
    rows = {}
    for burden in BURDEN_GRID:
        held = state.evolve(**{"T": dv.tone_target(state.evolve(aux=replace(state.aux,
                                                                           vasodilatory_burden=burden)), a, prof)})
        row = reading(held, a, prof)
        rows[str(burden)] = {"T": row["T"], "map": row["map"], "output_rel": row["output_rel"],
                             "delivery_rel": row["delivery_rel"], "crt": row["crt"]}
    pattern = {"pressure_falls": all(rows[str(b)]["map"] < rows["0.0"]["map"] for b in BURDEN_GRID[1:]),
               "flow_preserved_or_raised": all(rows[str(b)]["output_rel"] >= rows["0.0"]["output_rel"]
                                               for b in BURDEN_GRID),
               "refill_not_prolonged": all(rows[str(b)]["crt"] <= rows["0.0"]["crt"] for b in BURDEN_GRID)}
    out = {"rows": rows, "pattern": pattern, "authored": AUTHORED,
           "independent_evidence": {k: list(v) for k, v in INDEPENDENT_EVIDENCE.items()},
           "legacy": LEGACY_ENGINE_BEHAVIOR, "status": SIGNATURE_STATUS,
           "arrival_burden": {case: "UNSET" for case in AUTHORED},
           "closed_readings": {
               "collapse_architecture": "P2M-2 reads the distributive pattern as T falling with flow kept or raised "
                                        "(its probe sets T by hand for want of a writer)",
               "consciousness_audit": "a low tone gives a low MAP with preserved delivery: the MAP path is distinct "
                                      "from the deficit",
           },
           "note": "SYNTHETIC burden and gain against the authored truth; no case is mapped, no arrival value is "
                   "calibrated and nothing is approved"}
    out["pass"] = all(pattern.values()) and all(v == "UNSET" for v in out["arrival_burden"].values())
    return out


# The parameter state and the carried debts -----------------------------------------------------------------------------------

UNSET_MAGNITUDES = {
    NEW_PROFILE_FIELD: "UNSET (None): no vasodilatory reader is declared in any committed profile; the probe gains "
                       "here are SYNTHETIC_ONLY",
    NEW_ANCHOR: "UNSET (0.0 in every committed arrival mapping): no case carries an arrival burden",
    "anaphylaxis_tone_loss": "UNSET and not approved (no family writer exists)",
    "sepsis_tone_loss": "UNSET and not approved",
    "epinephrine_effect": "UNSET and not approved (no treatment writer exists)",
    "pressure_to_tone_gain": "UNSET and out of scope: PRESSURE_TO_TONE_NOT_REQUIRED_FOR_DISTRIBUTIVE_COMPOSITION "
                             "(P2W-0), still open for ACS and PE",
    "deficit_to_tone_gain": "PROVISIONAL and unchanged: 0.5 in the five committed profiles with the response on is a "
                            "carried structural point (baroreflex.TONE_GAINS[1]), 0 in GI; the faculty sets it",
    "writer_rates": "UNSET: no family writer exists, so no rate of dilation or of its reversal is declared",
    "upper_bound": "UNSET by decision: the burden has no ceiling (0 is none); T's own guard holds the channel",
}
#: The debts P2W-1 carries from the packages before it, resolved by none of them here.
CARRIED_DEBTS = {
    "PRESSURE_TO_TONE_COMPENSATION_MISSING": {
        "from": "P2N-2 / P2Q-2 (TD-118 point 4)", "status": "CARRIED, NOT REQUIRED HERE",
        "note": "the compensatory response reads the oxygen deficit only; a pressure-driven tone compensation would "
                "need a new clinical gain, a reference pressure and an ordering decision, so P2W-0 classified it "
                "PRESSURE_TO_TONE_NOT_REQUIRED_FOR_DISTRIBUTIVE_COMPOSITION and it stays open for ACS and PE",
    },
    "MULTI_FAMILY_COMMON_HR_GAP": {
        "from": "P2N-2 / P2Q-2 / P2U-1", "status": "CARRIED, NOT PATCHED",
        "note": "the arrival HR gaps of the ACS, PE and opioid cases are untouched; P2V-1's systemic stress is the "
                "common input for the non-respiratory part and its magnitude stays UNSET",
    },
    "SYSTEMIC_STRESS_MAGNITUDES_UNSET": {
        "from": "P2V-1 (TD-125)", "status": "CARRIED",
        "note": "the stress gain and every arrival region stay UNSET; P2W-1 adds no vascular reader of the stress",
    },
    "SIDED_PRELOAD_COMMON_STATE_DEFERRED": {
        "from": "P2Q-2 (TD-118 point 2)", "status": "CARRIED",
        "note": "the core has no sided preload; the distributive composition needs none",
    },
    "CONSCIOUSNESS_INTEGRATION_DEBT": {
        "from": "P2L-2 / P2U-1", "status": "CARRIED",
        "note": "the consciousness ladder reads SpO2 only; the low-MAP path of distributive shock is diagnostic in the "
                "closed audits and is not wired here",
    },
}


def parameters() -> dict:
    state, note = dv.PARAMETERS.get(NEW_PROFILE_FIELD, (None, ""))
    out = {"unset": UNSET_MAGNITUDES, "registry_state": state, "registry_note": note,
           "declared_in_the_registry": NEW_PROFILE_FIELD in dv.PARAMETERS,
           "candidate_input_outside_case_parameters": NEW_ANCHOR not in CASE_PARAMETERS,
           "candidate_inputs": list(CANDIDATE_INPUTS),
           "committed_gains": {name: p.vasodilatory_burden_to_tone_gain for name, p in committed_profiles().items()},
           "committed_arrival": {name: getattr(a, NEW_ANCHOR) for name, (a, _) in committed_pairs().items()},
           "committed_compensation": {name: p.deficit_to_tone_gain for name, p in committed_profiles().items()},
           "synthetic_only": {"tone_gain": TONE_GAIN, "other_tone_gain": OTHER_TONE_GAIN,
                              "burden_grid": list(BURDEN_GRID), "probe_burden": PROBE_BURDEN,
                              "severe_burden": SEVERE_BURDEN, "burden_step": BURDEN_STEP,
                              "compensation_gains": list(COMPENSATION_GAINS), "demands": list(DEMANDS)}}
    out["pass"] = (out["declared_in_the_registry"] and out["registry_state"] == "provisional"
                   and "UNSET" in out["registry_note"] and out["candidate_input_outside_case_parameters"]
                   and all(v is None for v in out["committed_gains"].values())
                   and all(v == 0.0 for v in out["committed_arrival"].values()))
    return out


def carried_debts() -> dict:
    out = {"debts": CARRIED_DEBTS,
           "pressure_in_the_tone_path": sorted(mc._names(mc._functions(_live("clinical_core/derived.py"))
                                                         ["tone_target"]) & {"map", "mean_arterial_pressure",
                                                                             "baroreflex_signal", "pressure_rel"}),
           "no_family_writer": not any("VasodilationChange" in p.read_text(encoding="utf-8")
                                       for p in (CORE_DIR / "modules").glob("*.py")),
           "p2v1_stress_unset": {name: p.systemic_stress_to_sympathetic_gain is None
                                 for name, p in committed_profiles().items()},
           "compensation_unchanged": {name: p.deficit_to_tone_gain for name, p in committed_profiles().items()}}
    out["pass"] = (not out["pressure_in_the_tone_path"] and out["no_family_writer"]
                   and all(out["p2v1_stress_unset"].values())
                   and out["compensation_unchanged"]["gi"] == 0.0
                   and all(v == 0.5 for k, v in out["compensation_unchanged"].items() if k != "gi"))
    return out


def non_regression() -> dict:
    """With the reader UNSET and no vasodilation writer: P2V-1's record reproduced on its tree (which nests P2U-1,
    P2T-5, P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 and, through them, the opioids, the asthma, PE, the oedema, the ACS and
    GI), and P2J-2's own tone package unchanged."""
    with p2v1_view():
        p2v1 = ss.run()
    record = json.loads(ss.RECORD.read_text(encoding="utf-8"))
    out = {"p2v1_record_reproduced_on_its_tree": json.loads(json.dumps(p2v1, sort_keys=True, default=str)) == record,
           "p2v1_record_untouched": hashlib.sha256(ss.RECORD.read_bytes()).hexdigest() == P2V1_RECORD_SHA,
           "p2v1_verdict": p2v1["readiness"]["verdict"],
           "committed_arrival_burden_zero": {name: dv.arrival_state(a, p).aux.vasodilatory_burden == 0.0
                                             for name, (a, p) in committed_pairs().items()},
           "tuples": {"DOWNSTREAM_REPORTS": REPORT in _downstream_reports(),
                      "PACK_DIGEST_EXCLUDED": set(TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(_pack_excluded())}}
    out["pass"] = (out["p2v1_record_reproduced_on_its_tree"] and out["p2v1_record_untouched"]
                   and all(out["committed_arrival_burden_zero"].values()) and all(out["tuples"].values()))
    return out


def _downstream_reports() -> tuple:
    from . import lactate_slice
    return lactate_slice.DOWNSTREAM_REPORTS


def _pack_excluded() -> tuple:
    from . import decision_pack
    return decision_pack.PACK_DIGEST_EXCLUDED


# The proof: the P2V-1 tree plus P2W-1's declared insertions --------------------------------------------------------------------

P2V1_HEAD = "cff2fb2"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py",\n'
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py",\n'
                                     '                        "clinical_core/distributive_tone.py",\n'
                                     '                        "clinical_core/distributive_tone_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py",\n'
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('AUXILIARY_SOURCES["systemic_stress"] = SYSTEMIC_STRESS\n'
                               "#: P2W-1: the core's sum of the families' vasodilation changes into the common "
                               'vasodilatory burden (the arrival value\n'
                               '#: plus every change since). It adds no kinetics and no coupling of its own. Read '
                               'only when a profile declares the gain.\n'
                               'VASODILATORY_BURDEN = Source(SourceKind.CORE_COUPLING, "vasodilatory_burden")\n'
                               'AUXILIARY_SOURCES["vasodilatory_burden"] = VASODILATORY_BURDEN\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n',
                               'AUXILIARY_SOURCES["systemic_stress"] = SYSTEMIC_STRESS\n'
                               '#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.\n'),
                              ('    systemic_stress_to_sympathetic_gain: float | None = None\n'
                               '    # P2W-1: the vasodilatory reader of the common tone target, UNSET (None) by '
                               'default. Declared, the target is\n'
                               "    # multiplied by (1 + k b0) / (1 + k b), b the state's common vasodilatory burden "
                               'and b0 the arrival one: a factor\n'
                               '    # at or below 1 that is 1 exactly at arrival (so the authored arrival pressure '
                               'stays the scale), decreasing in the\n'
                               "    # burden, and never a second deficit reader. The core stays T's only writer. No "
                               'value is chosen here.\n'
                               '    vasodilatory_burden_to_tone_gain: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    systemic_stress_to_sympathetic_gain: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('                                     "physiology")\n'
                               '        tone = self.vasodilatory_burden_to_tone_gain\n'
                               '        if tone is not None and (isinstance(tone, bool) or not isinstance(tone, '
                               '(int, float))\n'
                               '                                 or not math.isfinite(tone) or tone <= 0.0):\n'
                               '            # P2W-1: UNSET is None (no reader); declared, the gain is finite and '
                               'positive (a burden never raises the\n'
                               '            # tone). The factor stays positive at any burden, so no upper bound is '
                               'mathematically needed.\n'
                               '            raise CoreInvariantError("vasodilatory_burden_to_tone_gain is None '
                               '(UNSET: no vasodilatory reader) or a "\n'
                               '                                     "finite positive tone loss per unit of '
                               'burden")\n'
                               '        gain = self.systemic_stress_to_sympathetic_gain\n',
                               '                                     "physiology")\n'
                               '        gain = self.systemic_stress_to_sympathetic_gain\n'),
                              ('                                                  "probes; not approved"),\n'
                               '    "vasodilatory_burden_to_tone_gain": (PROVISIONAL, "UNSET (P2W-1): tone loss per '
                               'unit of the common vasodilatory "\n'
                               '                                                      "burden (a primary '
                               'distributive loss of vascular tone), as the "\n'
                               '                                                      "factor (1 + k b0) / (1 + k b) '
                               'on the common tone target, "\n'
                               '                                                      "normalized at arrival; None '
                               'by default (no reader); it reads "\n'
                               '                                                      "no pressure, deficit, D, '
                               'baroreflex or systemic stress and is "\n'
                               '                                                      "never solved from an observed '
                               'MAP; SYNTHETIC_ONLY in probes; "\n'
                               '                                                      "not approved"),\n'
                               '    "systemic_stress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2V-1): sympathetic '
                               'drive per unit of the common "\n',
                               '                                                  "probes; not approved"),\n'
                               '    "systemic_stress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2V-1): sympathetic '
                               'drive per unit of the common "\n'),
                              ('                                 "(P2V-1); nothing else reads it")\n'
                               '    if anchors.arrival_vasodilatory_burden != 0.0 and '
                               'profile.vasodilatory_burden_to_tone_gain is None:\n'
                               '        raise CoreInvariantError("an arrival vasodilatory burden other than 0 needs '
                               'a declared vasodilatory reader "\n'
                               '                                 "(P2W-1); nothing else reads it")\n'
                               '    if anchors.arrival_central_availability != 1.0 and profile.acid_to_drive_gain is '
                               'None:\n',
                               '                                 "(P2V-1); nothing else reads it")\n'
                               '    if anchors.arrival_central_availability != 1.0 and profile.acid_to_drive_gain is '
                               'None:\n'),
                              ('                                            '
                               'central_availability=anchors.arrival_central_availability,\n'
                               '                                            '
                               'systemic_stress=anchors.arrival_systemic_stress,\n'
                               '                                            '
                               'vasodilatory_burden=anchors.arrival_vasodilatory_burden))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n',
                               '                                            '
                               'central_availability=anchors.arrival_central_availability,\n'
                               '                                            '
                               'systemic_stress=anchors.arrival_systemic_stress))\n'
                               '    return state.evolve(aux=replace(state.aux, '
                               'sympathetic_drive=sympathetic_target(state, anchors, profile)))\n'),
                              ('    gain = profile.deficit_to_tone_gain\n'
                               '    target = ((1.0 + gain * acute_deficit_signal(state, anchors, profile))\n'
                               '              / (1.0 + gain * arrival_tone_signal(anchors, profile)))\n'
                               '    tone_loss = profile.vasodilatory_burden_to_tone_gain\n'
                               '    if tone_loss is not None:\n'
                               '        # P2W-1: the vasodilatory reader: the primary loss of tone a disease process '
                               'causes, as a factor at or below 1\n'
                               '        # normalized at arrival, so the arrival target stays 1 exactly whatever the '
                               'arrival burden. It multiplies the\n'
                               '        # compensatory factor instead of joining it, so more burden never raises the '
                               'tone, more compensation never\n'
                               '        # lowers it, and a large burden dominates a bounded compensation. UNSET '
                               '(None) by default.\n'
                               '        target *= ((1.0 + tone_loss * anchors.arrival_vasodilatory_burden)\n'
                               '                   / (1.0 + tone_loss * state.aux.vasodilatory_burden))\n'
                               '    return target\n'
                               '\n',
                               '    gain = profile.deficit_to_tone_gain\n'
                               '    return ((1.0 + gain * acute_deficit_signal(state, anchors, profile))\n'
                               '            / (1.0 + gain * arrival_tone_signal(anchors, profile)))\n'
                               '\n')),
 'clinical_core/integration.py': (('                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange,\n'
                                   '                         SystemicStressChange, VasodilationChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n',
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange,\n'
                                   '                         SystemicStressChange)\n'
                                   'from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, '
                                   'BloodState, Channel, CoreInvariantError,\n'),
                                  ('    systemic_stress: tuple[SystemicStressChange, ...] = ()  # changes to the '
                                   'common systemic stress this minute (P2V-1)\n'
                                   '    vasodilation: tuple[VasodilationChange, ...] = ()  # changes to the common '
                                   'vasodilatory burden this minute (P2W-1)\n'
                                   '\n',
                                   '    systemic_stress: tuple[SystemicStressChange, ...] = ()  # changes to the '
                                   'common systemic stress this minute (P2V-1)\n'
                                   '\n'),
                                  ('                              "SystemicStressChange records")\n'
                                   '    if not isinstance(contribution.vasodilation, tuple) or any(not '
                                   'isinstance(item, VasodilationChange)\n'
                                   '                                                               for item in '
                                   'contribution.vasodilation):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the vasodilatory '
                                   'burden changes only by a tuple of "\n'
                                   '                              "VasodilationChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n',
                                   '                              "SystemicStressChange records")\n'
                                   '    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and '
                                   'any(delta.channel in BLOOD_CHANNELS\n'),
                                  ('                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress\n'
                                   '                 + contribution.availability + contribution.systemic_stress + '
                                   'contribution.vasodilation):\n'
                                   '        if item.source != contributor.source:\n',
                                   '                 + contribution.demand + contribution.blood + '
                                   'contribution.mechanics + contribution.distress\n'
                                   '                 + contribution.availability + contribution.systemic_stress):\n'
                                   '        if item.source != contributor.source:\n'),
                                  ('    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    availability, systemic_stress, vasodilation = [], [], []\n'
                                   '    internal = {}\n',
                                   '    transitions, settings, events, modifiers, flows, mechanics, distress = [], '
                                   '[], [], [], [], [], []\n'
                                   '    availability, systemic_stress = [], []\n'
                                   '    internal = {}\n'),
                                  ('        systemic_stress.extend(contribution.systemic_stress)\n'
                                   '        vasodilation.extend(contribution.vasodilation)\n'
                                   '        if contribution.internal is not None:\n',
                                   '        systemic_stress.extend(contribution.systemic_stress)\n'
                                   '        if contribution.internal is not None:\n'),
                                  ('                                                f"{target.code.value}"))\n'
                                   '    if profile.deficit_to_tone_gain > 0.0 or '
                                   'profile.vasodilatory_burden_to_tone_gain is not None:\n'
                                   '        # P2W-1: the tone response also runs for a declared vasodilatory reader, '
                                   "so a family's burden always reaches T\n"
                                   '        # where its reader exists, even with the compensatory gain at 0 (with '
                                   "the reader UNSET this is P2J-2's\n"
                                   '        # condition exactly, so nothing before P2W-1 changes).\n'
                                   '        deltas.append(_vascular_tone(state, deltas, anchors, profile, minute))\n',
                                   '                                                f"{target.code.value}"))\n'
                                   '    if profile.deficit_to_tone_gain > 0.0:\n'
                                   '        deltas.append(_vascular_tone(state, deltas, anchors, profile, '
                                   'minute))\n'),
                                  ('                         central_availability=_availability_after(state, '
                                   'availability, profile, minute),\n'
                                   '                         systemic_stress=_systemic_stress_after(state, '
                                   'systemic_stress, profile, minute),\n'
                                   '                         vasodilatory_burden=_vasodilation_after(state, '
                                   'vasodilation, profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n',
                                   '                         central_availability=_availability_after(state, '
                                   'availability, profile, minute),\n'
                                   '                         systemic_stress=_systemic_stress_after(state, '
                                   'systemic_stress, profile, minute))\n'
                                   '    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, '
                                   'new_state.evolve(aux=aux), anchors, profile))\n'),
                                  ('                          mechanics=tuple(mechanics), distress=tuple(distress), '
                                   'availability=tuple(availability),\n'
                                   '                          systemic_stress=tuple(systemic_stress), '
                                   'vasodilation=tuple(vasodilation))\n'
                                   '    _check_conservation(state, new_state, record)\n',
                                   '                          mechanics=tuple(mechanics), distress=tuple(distress), '
                                   'availability=tuple(availability),\n'
                                   '                          systemic_stress=tuple(systemic_stress))\n'
                                   '    _check_conservation(state, new_state, record)\n'),
                                  ('    return value + 0.0\n'
                                   '\n'
                                   '\n'
                                   'def _vasodilation_after(state: CoreState, vasodilation: list, profile: '
                                   'CoreProfile, minute: int) -> float:\n'
                                   '    """P2W-1: the vasodilatory burden after the minute: the value it starts with '
                                   "plus the minute's changes, summed once\n"
                                   "    by P2T-1A's rule (``distress_sum``: math.fsum and the binary64 roundoff "
                                   'bound at 0). The core adds no kinetics and\n'
                                   '    no coupling of its own. With its reader UNSET nothing reads it, so a change '
                                   'is refused; a minute that would take it\n'
                                   '    materially below 0 is refused, never held."""\n'
                                   '    if vasodilation and profile.vasodilatory_burden_to_tone_gain is None:\n'
                                   '        raise ProvenanceError(f"minute {minute}: {vasodilation[0].source.key} '
                                   'changed the vasodilatory burden while "\n'
                                   '                              "its reader is UNSET (P2W-1): nothing would read '
                                   'it")\n'
                                   '    value = distress_sum(state.aux.vasodilatory_burden, [item.amount for item in '
                                   'vasodilation])\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the vasodilation changes take '
                                   'the burden to {value!r}, below 0 "\n'
                                   '                              "(P2W-1)")\n'
                                   '    return value\n'
                                   '\n',
                                   '    return value + 0.0\n\n'),
                                  ('        raise ProvenanceError("the systemic stress changed by other than its '
                                   'recorded changes")\n'
                                   '    if after.aux.vasodilatory_burden != '
                                   'distress_sum(before.aux.vasodilatory_burden,\n'
                                   '                                                     [item.amount for item in '
                                   'record.vasodilation]):\n'
                                   "        # P2W-1: the vasodilatory burden moves by exactly the minute's recorded "
                                   'changes, never otherwise.\n'
                                   '        raise ProvenanceError("the vasodilatory burden changed by other than its '
                                   'recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n',
                                   '        raise ProvenanceError("the systemic stress changed by other than its '
                                   'recorded changes")\n'
                                   '    for channel in SCALAR_CHANNELS:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py",\n'
                                     '                      "clinical_core/distributive_tone_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py")\n'
                                     '\n'),),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class VasodilationChange:\n'
                                  '    """P2W-1: one source\'s change to the common vasodilatory burden in one '
                                  'minute.\n'
                                  '\n'
                                  '    The amount adds to the burden the minute starts with (finite; 0 changes '
                                  'nothing), as a distress or systemic-stress\n'
                                  '    change adds to its own state: the burden has no reference above 0 to scale, '
                                  'so the changes are additive. It stays\n'
                                  '    where its writers leave it: it never moves, back to arrival or anywhere else, '
                                  'without a change that names its\n'
                                  '    source, and the core adds no kinetics of its own. The burden is a common '
                                  'input, never a disease term in the tone\n'
                                  '    equation: a family declares what its own process (anaphylactic or septic '
                                  'vasodilation, a vasodilator drug, and in\n'
                                  '    the other direction a vasopressor) does to it, and the core only sums the '
                                  'changes. A minute whose changes would\n'
                                  '    take it below 0 is refused. No amount is approved; with its reader UNSET a '
                                  'change is refused, because nothing would\n'
                                  "    read it. The channel T keeps exactly one writer, the core's tone response.\n"
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
                                  '            raise ProvenanceError(f"a vasodilation change is a finite number, not '
                                  '{self.amount!r}")\n'
                                  '        object.__setattr__(self, "amount", float(self.amount))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every vasodilation change names its Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "vasodilation", "amount": self.amount, "source": '
                                  'self.source.to_dict(),\n'
                                  '                "minute": self.minute, "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AvailabilityChange:\n',
                                  '@dataclass(frozen=True)\nclass AvailabilityChange:\n'),
                                 ('    systemic_stress: tuple[SystemicStressChange, ...] = field(default=())\n'
                                  '    vasodilation: tuple[VasodilationChange, ...] = field(default=())\n'
                                  '\n',
                                  '    systemic_stress: tuple[SystemicStressChange, ...] = field(default=())\n\n'),
                                 ('        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress + '
                                  'self.availability + self.systemic_stress\n'
                                  '                     + self.vasodilation):\n'
                                  '            if item.minute != self.minute:\n',
                                  '        for item in (self.deltas + self.transitions + self.settings + self.events '
                                  '+ self.auxiliary + self.demand\n'
                                  '                     + self.blood + self.mechanics + self.distress + '
                                  'self.availability + self.systemic_stress):\n'
                                  '            if item.minute != self.minute:\n'),
                                 ('                "availability": [item.to_dict() for item in self.availability],\n'
                                  '                "systemic_stress": [item.to_dict() for item in '
                                  'self.systemic_stress],\n'
                                  '                "vasodilation": [item.to_dict() for item in self.vasodilation]}\n'
                                  '\n',
                                  '                "availability": [item.to_dict() for item in self.availability],\n'
                                  '                "systemic_stress": [item.to_dict() for item in '
                                  'self.systemic_stress]}\n'
                                  '\n')),
 'clinical_core/state.py': (('                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress",\n'
                             '                              "arrival_central_availability", '
                             '"arrival_systemic_stress",\n'
                             '                              "arrival_vasodilatory_burden"),\n'
                             '}\n',
                             '                              "arrival_mechanics_efficiency", '
                             '"arrival_respiratory_distress",\n'
                             '                              "arrival_central_availability", '
                             '"arrival_systemic_stress"),\n'
                             '}\n'),
                            ('    arrival_systemic_stress: float = 0.0\n'
                             '    # P2W-1 candidate input, read only by the vasodilatory reader of the common tone '
                             'target (UNSET by default) and\n'
                             "    # outside the case-parameter / migration registry, as P2S-2's, P2T-1's, P2U-1's "
                             "and P2V-1's: the arrival primary\n"
                             '    # loss of vascular tone, a case / family latent arrival state constrained by '
                             'independent authored evidence (warm\n'
                             '    # or flushed peripheries with a low pressure, a filled capillary refill, preserved '
                             'or raised flow), never inverted\n'
                             '    # from the MAP residual. At or above 0 with no upper bound; 0, the default, is '
                             'none.\n'
                             '    arrival_vasodilatory_burden: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    arrival_systemic_stress: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the arrival systemic stress is finite and at or '
                             'above 0 (P2V-1)")\n'
                             '        if isinstance(self.arrival_vasodilatory_burden, bool) \\\n'
                             '                or not isinstance(self.arrival_vasodilatory_burden, (int, float)) \\\n'
                             '                or not math.isfinite(self.arrival_vasodilatory_burden) or '
                             'self.arrival_vasodilatory_burden < 0.0:\n'
                             '            raise CoreInvariantError("the arrival vasodilatory burden is finite and at '
                             'or above 0 (P2W-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the arrival systemic stress is finite and at or '
                             'above 0 (P2V-1)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'),
                            ('                       "from the observed HR; 0 and constant unless a family writes '
                             'it",\n'
                             '    "vasodilatory_burden": "the common vasodilatory burden (P2W-1): the primary loss '
                             'of vascular tone a disease "\n'
                             '                           "process causes (anaphylactic or septic vasodilation, a '
                             'vasodilator drug), at or above 0 "\n'
                             '                           "with no upper bound, 0 none; the case\'s latent arrival '
                             'value plus every family change "\n'
                             '                           "since (provenance.VasodilationChange); it lowers the '
                             'common vascular tone target only, "\n'
                             '                           "through its own UNSET gain, as a factor normalized at '
                             'arrival, so the arrival tone stays "\n'
                             '                           "1 exactly. Not the compensatory tone response (that '
                             'answers the oxygen deficit), not T "\n'
                             '                           "itself (the core stays T\'s only writer), not the volume, '
                             'the pump, the deficit, D, the "\n'
                             '                           "baroreflex or the systemic stress, and never a residual '
                             'solved from the observed MAP; 0 "\n'
                             '                           "and constant unless a family writes it",\n'
                             '}\n',
                             '                       "from the observed HR; 0 and constant unless a family writes '
                             'it",\n'
                             '}\n'),
                            ('    systemic_stress: float = 0.0\n    vasodilatory_burden: float = 0.0\n\n',
                             '    systemic_stress: float = 0.0\n\n'),
                            ('            raise CoreInvariantError("the systemic stress is never negative")\n'
                             '        if self.vasodilatory_burden < 0:\n'
                             '            # P2W-1: 0 is none; there is no ceiling (the tone factor stays positive at '
                             "any burden, and T's own guard\n"
                             '            # fails closed where a burden would take the target below it).\n'
                             '            raise CoreInvariantError("the vasodilatory burden is never negative")\n'
                             '\n',
                             '            raise CoreInvariantError("the systemic stress is never negative")\n\n'))}
CORE_AT_P2V1 = {'clinical_core/decision_pack.py': '65de383a04ac517f12e2b974d88b152570cc5f8cb060447e05dd3ab2a278515e',
 'clinical_core/derived.py': 'cb940c2182d0c538f8c7fa2a289350b5f39ae13736a83fe10c6f7aab41f3ba47',
 'clinical_core/integration.py': '46038f70b9e586f895b23b5b48048d26cae391dfcfcd43b438767434e3380cea',
 'clinical_core/lactate_slice.py': 'e96253a24805dcbc1ea31dd2f3517fad274a9fc07307236a1ea024ddb93a5c5e',
 'clinical_core/provenance.py': '8256e3ad166c37ec83fb8840ce669fee648a3db69b3868917fd48d902339e16f',
 'clinical_core/state.py': 'b05769448bd4c72b72043d691fab95269ca1cb468deacd2ebd50d8918a49c6e7'}
# </reversal>
# <common>
COMMON_AT_P2V1 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/systemic_stress.py': '572c72d8f225ee86fc4f8e40842de15809b29ef53f77edfe201c49c45dde851e',
 'clinical_core/systemic_stress_report.py': 'e8ef9be3eeab26b10d4a8339c46d5dac99dfc6228e39101766af88ef9e161ea9',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>
P2V1_FREEZE_DIGEST = "00ce9e64b78d961c6f5e6894f4b4c78d9bacfbadf3b93e95bc6aae26cf804f95"
P2V1_RECORD_SHA = "5de3392985bf50db57b89df84b30987248c625cc6f8f932b6410e805354f66e9"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2V1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2V1.items()}


def p2v1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2V-1 file plus P2W-1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2v1_bytes(relative: str) -> bytes:
    return p2v1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2v1_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2V1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


#: The closed packages whose hash list of unchanged files still reads the live bytes: P2V-1's. Every older package's
#: list is already redirected by its own newer neighbour's chain.
CLOSED_COMMON = ("systemic_stress",)


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2v1_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


def _ss_p2u1_bytes(relative: str) -> bytes:
    """P2V-1's p2u1_bytes on the P2V-1 tree: its own reversed files from the P2V-1 text, every other file's P2V-1
    bytes."""
    return ss.p2u1_text(relative).encode("utf-8") if relative in ss.REVERSAL else p2v1_bytes(relative)


class _TreeFile:
    """One of P2W-1's changed files as P2V-1 left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2v1_text(self.relative)

    def read_bytes(self):
        return p2v1_bytes(self.relative)

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
    """A closed package's ``ROOT`` or ``CORE_DIR``: the P2V-1 text of P2W-1's changed files, the live path of anything
    else, and its listings without P2W-1's new files."""

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
        return str(self.path)


def without_new_keys(value):
    """A closed record's view of a live serialization: P2W-1's new arrival anchor and auxiliary field dropped where
    they hold their reference 0, and a minute record's empty vasodilation list dropped."""
    if isinstance(value, dict):
        if "case_id" in value and NEW_ANCHOR in value:
            if value[NEW_ANCHOR] != 0.0:
                raise AssertionError("a closed course read a new candidate input away from its reference")
            value = {k: v for k, v in value.items() if k != NEW_ANCHOR}
        if NEW_AUX in value and "sympathetic_drive" in value and "oxygen_demand" in value:
            if value[NEW_AUX] != 0.0:
                raise AssertionError("a closed course moved the vasodilatory burden")
            value = {k: v for k, v in value.items() if k != NEW_AUX}
        if "vasodilation" in value and "minute" in value and "deltas" in value and value["vasodilation"] == []:
            value = {k: v for k, v in value.items() if k != "vasodilation"}
        return {k: without_new_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_new_keys(v) for v in value]
    return value


#: Every closed analysis module whose listings of the representation must read P2W-1's new names as P2V-1 left them.
CLOSED_LIVE = ("systemic_stress",) + ss.CLOSED_LIVE
NEW_NAMES = (NEW_AUX, NEW_ANCHOR, NEW_PROFILE_FIELD)
#: The closed modules' import-time snapshots, each taken while P2W-1's names were already live.
CLOSED_SNAPSHOTS = (("systemic_stress", "P2U1_AUXILIARY_FIELDS", NEW_AUX),
                    ("systemic_stress", "P2U1_AUXILIARY_SOURCES", NEW_AUX),
                    ("opioid_migration", "P2T5_AUXILIARY_FIELDS", NEW_AUX),
                    ("opioid_migration", "P2T5_AUXILIARY_SOURCES", NEW_AUX),
                    ("oxygenation_link", "P2T3_PARAMETERS", NEW_PROFILE_FIELD),
                    ("respiratory_distress", "P2S3_AUXILIARY_FIELDS", NEW_AUX))


def _fields_at_p2v1(cls):
    """dataclasses.fields as the tree a closed package was frozen against had them: without P2W-1's new names, and
    then P2V-1's own filter, so the two compose whichever chain is applied last."""
    return tuple(f for f in ss._fields_at_p2u1(cls) if f.name not in NEW_NAMES)


def _raw_fields_at_p2v1(cls):
    """Only P2W-1's own filter."""
    return tuple(f for f in dataclasses.fields(cls) if f.name not in NEW_NAMES)


class _DataclassesAtP2V1:
    """``dataclasses`` as a closed module sees it on the P2V-1 tree: ``fields`` filtered, everything else untouched."""

    fields = staticmethod(_raw_fields_at_p2v1)

    def __getattr__(self, name):
        return getattr(dataclasses, name)


_FREEZE_SOURCES = bf.freeze_sources
#: Every closed analysis module that reads a core file by path rather than through its own ``_live``. P2V-1's own paths
#: are not redirected: it reads P2W-1's changed files through its ``_live`` (redirected here), its own path reads touch
#: no file this package changed, and its view's path arithmetic needs its ROOT to stay a plain path.
PATH_READERS = ss.PATH_READERS


def _imported_closed_modules() -> list:
    return [__import__(f"clinical_core.{name}", fromlist=["ROOT"]) for name in PATH_READERS]


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2V-1's view reads the P2V-1 files (proven) and their bytes, its
    captured source map is P2V-1's; the closed listings of the auxiliary state and the closed serializations read them
    as P2V-1 left them. P2W-1 changes no behaviour without a declared reader."""
    patch.setattr(ss, "_live", p2v1_text)
    patch.setattr(ss, "p2u1_bytes", _ss_p2u1_bytes)
    patch.setattr(ss, "_FREEZE_SOURCES", lambda: p2v1_sources(_FREEZE_SOURCES()))
    for module_name in CLOSED_COMMON:
        module = __import__(f"clinical_core.{module_name}", fromlist=["common_untouched"])
        patch.setattr(module, "common_untouched", _closed_common_untouched(module))
    for module in _imported_closed_modules():
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                patch.setattr(module, attribute, _TreeDir(value))
            elif value is not None and not _carries(value):
                # Another chain ran first and left its own wrapper (one or several, nested): the whole chain of
                # wrappers is rebuilt over P2W-1's view, so the text stays the one each package was frozen against and
                # every view's new files stay out of the listings, whatever order the chains ran in.
                rebuilt = _rebuilt(value)
                if rebuilt is not None:
                    patch.setattr(module, attribute, rebuilt)
    for module_name in CLOSED_LIVE:
        module = __import__(f"clinical_core.{module_name}", fromlist=["_live"])
        if hasattr(module, "fields"):
            patch.setattr(module, "fields", _raw_fields_at_p2v1 if module is ss else _fields_at_p2v1)
        if hasattr(module, "dataclasses"):
            patch.setattr(module, "dataclasses", _DataclassesAtP2V1())
        if hasattr(module, "AUXILIARY_FIELDS"):
            patch.setattr(module, "AUXILIARY_FIELDS",
                          {k: v for k, v in module.AUXILIARY_FIELDS.items() if k != NEW_AUX})
    for module_name, attribute, key in CLOSED_SNAPSHOTS:
        module = __import__(f"clinical_core.{module_name}", fromlist=[attribute])
        patch.setattr(module, attribute, {k: v for k, v in getattr(module, attribute).items() if k != key})
    patch.setattr(dv, "AUXILIARY_SOURCES", {k: v for k, v in dv.AUXILIARY_SOURCES.items() if k != NEW_AUX})
    patch.setattr(dv, "PARAMETERS", {k: v for k, v in dv.PARAMETERS.items() if k != NEW_PROFILE_FIELD})
    ss_without, dm_without, mc_without = ss.without_new_keys, dm.without_new_keys, mc.without_new_anchor_key
    patch.setattr(ss, "without_new_keys", lambda value: ss_without(without_new_keys(value)))
    patch.setattr(dm, "without_new_keys", lambda value: dm_without(without_new_keys(value)))
    patch.setattr(mc, "without_new_anchor_key", lambda value: mc_without(without_new_keys(value)))


def _carries(value, kind=None) -> bool:
    """Whether a path reader's wrapper chain already carries a view of this kind (P2W-1's own by default): the chains
    are applied in no fixed order, so a reader may already be wrapped when this one runs."""
    kind = _TreeDir if kind is None else kind
    while value is not None and not isinstance(value, Path):
        if isinstance(value, kind):
            return True
        value = getattr(value, "path", None)
    return False


def _rebuilt(value):
    """A path reader another chain already wrapped, rebuilt with P2W-1's view at its base: every wrapper of the chain
    is put back around it, in its own order. None when the chain does not end in a path (nothing to rebuild)."""
    if isinstance(value, Path):
        return _TreeDir(value)
    inner = getattr(value, "path", None)
    rebuilt = None if inner is None else _rebuilt(inner)
    return None if rebuilt is None else type(value)(rebuilt)


_SS_TREE = ss.tree


def _ss_tree(patch) -> None:
    """P2V-1's own whole-tree view, nested inside P2W-1's: its chain, and then the path readers P2W-1 already wrapped
    (which its own chain leaves alone) wrapped again by its view."""
    _SS_TREE(patch)
    for module in _imported_closed_modules():
        if module is ss:
            continue
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if _carries(value) and not _carries(value, ss._TreeDir):
                patch.setattr(module, attribute, ss._TreeDir(value))


def tree(patch) -> None:
    """The whole P2V-1 tree, for P2V-1's own analysis and tests."""
    chain(patch)
    patch.setattr(ss, "tree", _ss_tree)
    patch.setattr(bf, "freeze_sources", lambda: p2v1_sources(_FREEZE_SOURCES()))


class p2v1_view:
    """P2W-1's analysis reading the tree P2V-1 froze, for its own proofs and its record."""

    def __enter__(self):
        self._patch = mc._Patch()
        tree(self._patch)
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2v1_view():
        digest = ss.freeze_digest()
        proof = ss.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2v1_freeze_digest": digest == P2V1_FREEZE_DIGEST,
            "p2v1_proof": all(proof["proofs"].values()) and all(proof["common_untouched"].values())
            and proof["p2u1_freeze_digest"] and proof["p2u1_proof"] and proof["p2u1_record"],
            "p2v1_record": hashlib.sha256(ss.RECORD.read_bytes()).hexdigest() == P2V1_RECORD_SHA}


# Readiness (predeclared) ------------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "the architecture is minimal and declared: one auxiliary field, one arrival anchor, one writer record, one gain, "
    "with their refusals, and the core still the T channel's only writer (representation, reader audit, audit)",
    "the composition is monotone in both causes: more burden never raises the tone, more compensation never lowers it "
    "at a deficit above arrival's (V2, V3)",
    "the two causes coexist without double counting: the compensation opposes the vasodilation partially and never "
    "erases it, and a severe vasodilation stays dominant (V4, V5)",
    "the distributive signal alters no other channel or auxiliary state directly, and neither the systemic stress nor "
    "the beta-blockade reaches the tone (V6, V11, V12)",
    "arrival exactness and the explicit lag are preserved: the arrival tone is 1 at any arrival burden and there is no "
    "same-step MAP / tone loop (V13, V14)",
    "every magnitude stays UNSET and no observable is inverted into a burden (the parameter state, the signature)",
    "nothing prior changes by default: with the reader UNSET every prior reading is exact and the committed families "
    "are untouched (V1, V7-V10)",
    "P2V-1's record reproduces on its tree and every other common file is P2V-1's (the non-regression, the proof)",
)
READY = "COMMON_DISTRIBUTIVE_TONE_COMPOSITION_READY"
NOT_READY = "COMMON_DISTRIBUTIVE_TONE_COMPOSITION_NOT_READY"
READINESS_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def readiness(found: dict) -> dict:
    p, proof = found["probes"], found["proof"]
    checks = (
        found["representation"]["pass"] and found["reader"]["pass"] and found["audit"]["pass"],
        p["V2"]["pass"] and p["V3"]["pass"],
        p["V4"]["pass"] and p["V5"]["pass"],
        p["V6"]["pass"] and p["V11"]["pass"] and p["V12"]["pass"],
        p["V13"]["pass"] and p["V14"]["pass"],
        found["parameters"]["pass"] and found["signature"]["pass"],
        p["V1"]["pass"] and all(p[name]["pass"] for name in ("V7", "V8", "V9", "V10")),
        found["non_regression"]["pass"] and found["carried_debts"]["pass"]
        and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2v1_freeze_digest"] and proof["p2v1_proof"] and proof["p2v1_record"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    return {"criteria": rows, "blocker": blocker, "rule": READINESS_RULE,
            "verdict": READY if blocker is None else f"{NOT_READY} - {blocker}"}


def design() -> dict:
    return {"decisions": DECISIONS, "semantics": SEMANTICS, "probes": PROBES,
            "synthetic": {"tone_gain": TONE_GAIN, "other_tone_gain": OTHER_TONE_GAIN,
                          "burden_grid": list(BURDEN_GRID), "probe_burden": PROBE_BURDEN,
                          "severe_burden": SEVERE_BURDEN, "burden_step": BURDEN_STEP,
                          "compensation_gains": list(COMPENSATION_GAINS), "demands": list(DEMANDS),
                          "course_minutes": COURSE_MINUTES, "beta_blockades": list(BETA_BLOCKADES),
                          "stress_gain": STRESS_GAIN, "probe_stress": PROBE_STRESS,
                          "t_guard": [T_LOWER, T_UPPER], "resting_hr": list(RESTING_HR)},
            "authored": AUTHORED, "independent_evidence": {k: list(v) for k, v in INDEPENDENT_EVIDENCE.items()},
            "legacy": LEGACY_ENGINE_BEHAVIOR, "signature_status": SIGNATURE_STATUS, "unset": UNSET_MAGNITUDES,
            "carried_debts": CARRIED_DEBTS,
            "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2v1": CORE_AT_P2V1, "common_at_p2v1": COMMON_AT_P2V1,
            "p2v1": {"head": P2V1_HEAD, "freeze_digest": P2V1_FREEZE_DIGEST, "record": P2V1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2v1": hashlib.sha256(ss.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "representation": representation(),
             "reader": reader_audit(), "probes": structural_probes(), "signature": distributive_signature(),
             "parameters": parameters(), "carried_debts": carried_debts(), "non_regression": non_regression()}
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
