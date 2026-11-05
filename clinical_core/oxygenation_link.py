"""P2T-5: the minimum common hypoventilation -> oxygenation link (shadow only, off by default).

Faculty decisions after P2T-4 (A, MINIMAL_ALVEOLAR_GAS_LINK_SUPPORTED):
- SYMMETRIC_RELATIVE_ALVEOLAR_LINK and MINIMAL_RELATIVE_ALVEOLAR_GAS_LINK: dPAO2 = -dPaCO2 / R relative to the model's
  own arrival PaCO2 (the P2S-2 mechanics / W pathway, never the authored PaCO2 as a hidden anchor); Patm, PH2O,
  absolute PAO2 and altitude are not active inputs (they cancel).
- FULL_RELATIVE_ALVEOLAR_TRANSMISSION = ACCEPTED, RETAINED_G_AS_ALVEOLAR_TRANSMISSION = REJECTED: the shift is not
  multiplied by ``oxygen_response_retained(G)`` (the cross-term can make a worse G raise SpO2); G acts through the
  existing SpO2 path only. No new tau or gain.
- Serial composition through a latent PaO2: PaO2 = ODC^-1(SpO2_base) - dPaCO2 / R, SpO2 = ODC(PaO2), with the standard
  dissociation relation (no fitted parameter). PaO2 is never a state.
- ``CoreProfile.respiratory_quotient``: None (the link off) by default; a declared value needs the common mechanics
  candidate and refuses the hypoxaemic drive (HYPOXEMIC_FEEDBACK_LOOP_DEFERRED). R = 0.8 only as a
  SYNTHETIC_PHYSIOLOGIC_REFERENCE in probes; no clinical value is approved.

This module freezes the audit, the dissociation-relation checks, O1-O11, the family probes, the downstream directions,
the parameter state, the non-regression and the proof that every other file is P2T-3's, before the one evaluation run.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
import math
from dataclasses import fields, replace
from pathlib import Path

from . import asthma_distress_migration as tm
from . import asthma_migration as sm
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import distress_closure as xm
from . import edema_migration as pe
from . import edema_reference as er
from . import embolism_migration as em
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import respiratory_distress as dm
from . import respiratory_drive as rd
from . import respiratory_mechanics as mc
from .integration import step
from .state import AUXILIARY_FIELDS, CoreInvariantError, UnresolvedBoundary

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2T-5"
DECIDED = "2026-11-05"
OWN = ("clinical_core/oxygenation_link.py",)
REPORT = "clinical_core/oxygenation_link_report.py"
RECORD = ROOT / "docs" / "revision" / "P2T5_oxygenation_link.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2T5_ENLACE_HIPOVENTILACION_OXIGENACION.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py",)
NEW_PROFILE_FIELDS = ("respiratory_quotient",)
NEW_FUNCTIONS = ("arrival_paco2_reference", "hypoventilation_link_active", "oxygen_saturation_from_pao2",
                 "pao2_from_oxygen_saturation", "ventilated_oxygenation")
SYNTHETIC_R = 0.8
SYNTHETIC_R_LABEL = "SYNTHETIC_PHYSIOLOGIC_REFERENCE"

DECISIONS = {
    "link": "SYMMETRIC_RELATIVE_ALVEOLAR_LINK; MINIMAL_RELATIVE_ALVEOLAR_GAS_LINK (dPAO2 = -dPaCO2 / R)",
    "transmission": "FULL_RELATIVE_ALVEOLAR_TRANSMISSION = ACCEPTED; RETAINED_G_AS_ALVEOLAR_TRANSMISSION = REJECTED",
    "reference": "the model-derived arrival PaCO2 of the P2S-2 mechanics / W pathway; dPaCO2 = 0 at arrival",
    "mechanics": "the link needs the common mechanics candidate (refused with it off)",
    "respiratory_quotient": "None by default (off); finite positive when declared; 0.8 only SYNTHETIC_PHYSIOLOGIC_REFERENCE",
    "pao2": "latent only (no state); no ABG observable yet",
    "plateau": "ODC_PLATEAU_IDENTIFIABILITY_DEBT: SpO2_base 100 gives PaO2 +inf; no ceiling, no epsilon",
    "fio2": "the existing FiO2 rule unchanged (FIO2_RESPONSE_MAGNITUDE_DEBT)",
    "hypoxaemic_drive": "UNSET; refused with the link (HYPOXEMIC_FEEDBACK_LOOP_DEFERRED)",
    "out_of_scope": "opioid migration, the full alveolar gas equation, a PaO2 state, FiO2 recalibration, consciousness "
                    "integration, systemic_stress",
}

# Synthetic, predeclared probe values (SYNTHETIC_ONLY) -----------------------------------------------------------------------

EFFICIENCY_FACTORS = (0.7, 1.0, 1.3)      # a state's mechanics efficiency relative to arrival (W down, same, up)
G_VALUES = (0.0, 0.5, 1.0, 2.0)
FIO2_VALUES = (0.21, 0.30, 0.40, 0.50)
DPACO2_VALUES = (-10.0, 0.0, 10.0, 20.0, 30.0)
DEPRESSED_AVAILABILITY = 0.5              # P2T-5-5's synthetic central depression (fixed-state comparison)
OBSTRUCTION_RATE = sm.MID_WORSENING
RELIEF = sm.RELIEF
COURSE_MINUTES = 60
EDEMA_MECHANICS_FACTOR = 0.998       # per minute, minutes 0-60 (SYNTHETIC_ONLY)
DOWNSTREAM_FACTORS = {"probe": 0.993, "pe": 0.998}   # per minute, minutes 0-60 (SYNTHETIC_ONLY)
MASKING_FIO2 = 0.25                       # SpO2_base below 100: partial masking
PLATEAU_FIO2 = (0.5, 1.0)                 # SpO2_base 100: full masking (the plateau)


def probe_profile(r: float | None = SYNTHETIC_R) -> dv.CoreProfile:
    """P2S-2's probe profile (mechanics on) with P2O-1's SYNTHETIC_ONLY gas-exchange reference and the link at r."""
    return replace(go.gas_profile(mc.base_profile()), respiratory_quotient=r)


def probe_anchors(**changes):
    return dm.probe_anchors(**changes)


def _with(state, factor=1.0, G=None, fio2=None):
    s = state.evolve(aux=replace(state.aux, mechanics_efficiency=state.aux.mechanics_efficiency * factor))
    if G is not None:
        s = s.evolve(G=G)
    if fio2 is not None:
        s = s.evolve(fio2=fio2)
    return s


def spo2(state, anchors, profile) -> float:
    return dv.derive(state, anchors, profile).spo2


def paco2(state, anchors, profile) -> float:
    return dv.respiration(state, anchors, profile).paco2


def shift(spo2_base: float, dpaco2: float, r: float = SYNTHETIC_R) -> float:
    """The link's arithmetic on a SpO2_base and a PaCO2 change (the core's own functions)."""
    if dpaco2 == 0.0:
        return spo2_base
    return dv.oxygen_saturation_from_pao2(dv.pao2_from_oxygen_saturation(spo2_base) - dpaco2 / r)


# P2T-5-1: the changed functions, the dissociation relation and retained(G) --------------------------------------------------

def _function_dumps(text: str) -> dict:
    out = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef):
            out.setdefault(node.name, []).append(ast.dump(node))
    return out


def audit() -> dict:
    old, new = p2t3_text("clinical_core/derived.py"), _live("clinical_core/derived.py")
    old_d, new_d = _function_dumps(old), _function_dumps(new)
    funcs = mc._functions(new)
    link = funcs["ventilated_oxygenation"]
    reads = sorted(mc._names(link) & {"respiration", "arrival_paco2_reference", "oxygen_response_retained", "fio2", "G",
                                      "pao2_from_oxygen_saturation", "oxygen_saturation_from_pao2",
                                      "respiratory_quotient", "paco2_reference_mmhg", "arrival_paco2"})
    constants = {}
    for name in ("oxygen_saturation_from_pao2", "pao2_from_oxygen_saturation", "ventilated_oxygenation",
                 "arrival_paco2_reference"):
        constants[name] = sorted({n.value for n in ast.walk(funcs[name]) if isinstance(n, ast.Constant)
                                  and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    profile_fields = sorted(set(dm._class_fields(new, "CoreProfile")) - set(dm._class_fields(old, "CoreProfile")))
    absolute = sorted({n for f in NEW_FUNCTIONS for n in mc._names(funcs[f])
                       if any(k in n.lower() for k in ("patm", "ph2o", "barometric", "altitude", "pao2_state"))})
    out = {"added": sorted(set(new_d) - set(old_d)),
           "changed": sorted(k for k in old_d if k in new_d and old_d[k] != new_d[k]),
           "link_reads": reads, "constants": constants, "new_profile_fields": profile_fields,
           "absolute_alveolar_terms": absolute,
           "perfusion_calls_link": "ventilated_oxygenation" in mc._names(funcs["_perfusion"])}
    out["pass"] = (out["added"] == sorted(NEW_FUNCTIONS) and out["changed"] == ["__post_init__", "_perfusion"]
                   and "oxygen_response_retained" not in reads and "fio2" not in reads and "G" not in reads
                   and "arrival_paco2" not in reads and profile_fields == list(NEW_PROFILE_FIELDS)
                   and not absolute and out["perfusion_calls_link"]
                   and set(constants["oxygen_saturation_from_pao2"]) <= {0.0, 1.0, 3, 100.0, 150.0, 23400.0}
                   and set(constants["pao2_from_oxygen_saturation"]) <= {0.0, 1.0, 2.0, 3.0, 4.0, 50.0, 100.0,
                                                                          23400.0, 125000.0}
                   and set(constants["ventilated_oxygenation"]) <= {0.0}
                   and set(constants["arrival_paco2_reference"]) <= {1.0})
    return out


class _WithoutLink(ast.NodeTransformer):
    def visit_If(self, node):
        if "hypoventilation_link_active" in mc._names(node.test):
            return None
        return self.generic_visit(node)


def _perfusion_insertion_only() -> bool:
    """_perfusion is P2T-3's exactly once its one ``if hypoventilation_link_active(profile)`` block is removed: the FiO2
    rule, the G path and delivery are untouched, and the link only replaces the spo2 they produce."""
    old = mc._functions(p2t3_text("clinical_core/derived.py"))["_perfusion"]
    new = _WithoutLink().visit(mc._functions(_live("clinical_core/derived.py"))["_perfusion"])
    inserted = [n for n in ast.walk(mc._functions(_live("clinical_core/derived.py"))["_perfusion"])
                if isinstance(n, ast.If) and "hypoventilation_link_active" in mc._names(n.test)]
    body = inserted[0].body if len(inserted) == 1 else []
    replaces_spo2_only = (len(body) == 1 and isinstance(body[0], ast.Assign)
                          and [ast.unparse(x) for x in body[0].targets] == ["spo2"]
                          and ast.unparse(body[0].value) == "ventilated_oxygenation(spo2, state, anchors, profile)")
    return ast.dump(old) == ast.dump(new) and replaces_spo2_only


def odc() -> dict:
    grid = (1.0, 10.0, 30.0, 45.0, 57.0, 80.0, 120.0, 300.0, 600.0)
    forward = [dv.oxygen_saturation_from_pao2(p) for p in grid]
    sats = (0.5, 20.0, 50.0, 80.0, 89.0, 95.0, 99.0, 99.9)
    inverse = [dv.pao2_from_oxygen_saturation(s) for s in sats]
    round_trip = max(abs(dv.oxygen_saturation_from_pao2(p) - s) for p, s in zip(inverse, sats) if s >= 20.0)
    import clinical_cases
    pairs = {}
    for family in sorted(clinical_cases.FAMILIES):
        for v in clinical_cases.FAMILIES[family]["variants"]:
            pao2 = float(v["investigations"]["abg"]["result"]["pao2_mm_hg"])
            pairs[v["id"]] = {"pao2": pao2, "spo2": float(v["observable"]["spo2"]),
                              "odc": dv.oxygen_saturation_from_pao2(pao2)}
    out = {"forward": dict(zip(map(str, grid), forward)), "inverse": dict(zip(map(str, sats), inverse)),
           "forward_increasing": all(b > a for a, b in zip(forward, forward[1:])),
           "inverse_increasing": all(b > a for a, b in zip(inverse, inverse[1:])),
           "round_trip_max_abs": round_trip,
           "limits": {"pao2_0": dv.oxygen_saturation_from_pao2(0.0), "pao2_inf": dv.oxygen_saturation_from_pao2(math.inf),
                      "spo2_0": dv.pao2_from_oxygen_saturation(0.0), "spo2_100": str(dv.pao2_from_oxygen_saturation(100.0))},
           "authored_pairs": pairs,
           "authored_max_abs_gap": max(abs(v["odc"] - v["spo2"]) for v in pairs.values()),
           "domain": "forward: PaO2 > 0 (0 at or below 0, 100 only as PaO2 -> inf); inverse: 0 < SpO2 < 100 (0 at 0, "
                     "+inf at 100: ODC_PLATEAU_IDENTIFIABILITY_DEBT)", "fitted_parameters": []}
    out["pass"] = (out["forward_increasing"] and out["inverse_increasing"] and round_trip < 1e-9
                   and out["limits"]["pao2_inf"] == 100.0 and out["limits"]["spo2_100"] == "inf")
    return out


def retained_audit() -> dict:
    p = probe_profile()
    values = [dv.oxygen_response_retained(g, p) for g in (-1.0, 0.0, 0.5, 1.0, 2.0)]
    return {"values": values, "one_at_or_below_arrival": values[0] == values[1] == 1.0,
            "non_increasing": all(b <= a for a, b in zip(values, values[1:])),
            "semantics": "the share of the FiO2 benefit the existing G path keeps (P2O-1); stays in that path",
            "as_alveolar_transmission": "REJECTED (faculty): a retained(G) x dPAO2 cross-term can make a worse G raise "
                                        "SpO2 when PaCO2 rises (shown before implementation)",
            "link_reads_retained": "oxygen_response_retained" in mc._names(
                mc._functions(_live("clinical_core/derived.py"))["ventilated_oxygenation"]),
            "pass": values[0] == values[1] == 1.0 and all(b <= a for a, b in zip(values, values[1:]))}


# O1-O11 -----------------------------------------------------------------------------------------------------------------------

def _refused(build) -> bool:
    try:
        build()
    except (CoreInvariantError, UnresolvedBoundary):
        return True
    return False


def probes() -> dict:
    a, on, off = probe_anchors(), probe_profile(), probe_profile(None)
    s0 = dv.arrival_state(a, on)
    out = {}
    # O1: link off is the previous code path exactly (the link function is never called).
    called = []
    original = dv.ventilated_oxygenation
    dv.ventilated_oxygenation = lambda *args: called.append(1) or original(*args)
    try:
        for f in EFFICIENCY_FACTORS:
            for g in G_VALUES:
                spo2(_with(dv.arrival_state(a, off), f, g), a, off)
        for name, (anc, prof) in committed_pairs().items():
            spo2(dv.arrival_state(anc, prof), anc, prof)
    finally:
        dv.ventilated_oxygenation = original
    out["O1"] = {"link_calls_with_r_none": len(called), "committed_profiles_r": {k: p.respiratory_quotient for k, (_, p)
                                                                                 in committed_pairs().items()},
                 "pass": not called and all(p.respiratory_quotient is None for _, p in committed_pairs().values())}
    # O2: arrival exact with the link on, whatever the arrival mechanics, FiO2 and the gas-exchange path.
    rows = {}
    for e in (1.0, 0.5):
        for fio2 in (0.21, 0.4):
            anc = probe_anchors(arrival_mechanics_efficiency=e, fio2=fio2)
            rows[f"E{e}_F{fio2}"] = (spo2(dv.arrival_state(anc, on), anc, on), spo2(dv.arrival_state(anc, off), anc, off))
    refs = {}
    for e in (1.0, 0.5):
        anc = probe_anchors(arrival_mechanics_efficiency=e)
        refs[f"E{e}"] = (dv.arrival_paco2_reference(anc, on), paco2(dv.arrival_state(anc, on), anc, on))
    for name, (anc, prof) in structural_pairs().items():
        refs[name] = (dv.arrival_paco2_reference(anc, prof), paco2(dv.arrival_state(anc, prof), anc, prof))
    out["O2"] = {"rows": rows, "reference_equals_arrival_respiration": refs,
                 "pass": all(x == y for x, y in rows.values()) and all(x == y for x, y in refs.values())}
    # O3 / O4: G neutral, PaCO2 up -> SpO2 down; PaCO2 down -> SpO2 up.
    up, down = _with(s0, 0.7), _with(s0, 1.3)
    out["O3"] = {"paco2": [paco2(s0, a, on), paco2(up, a, on)], "spo2": [spo2(s0, a, on), spo2(up, a, on)],
                 "pass": paco2(up, a, on) > paco2(s0, a, on) and spo2(up, a, on) < spo2(s0, a, on)}
    out["O4"] = {"paco2": [paco2(s0, a, on), paco2(down, a, on)], "spo2": [spo2(s0, a, on), spo2(down, a, on)],
                 "pass": paco2(down, a, on) < paco2(s0, a, on) and spo2(down, a, on) > spo2(s0, a, on)}
    # O5 (revised) / O6: worse G never raises the final SpO2, at every PaCO2 change; the SpO2 change may grow with G.
    table, change = {}, {}
    for f in EFFICIENCY_FACTORS:
        row = [spo2(_with(s0, f, g), a, on) for g in G_VALUES]
        table[str(f)] = row
        change[str(f)] = [spo2(_with(s0, f, g), a, on) - spo2(_with(s0, 1.0, g), a, on) for g in G_VALUES]
    analytic = {str(d): [shift(a.spo2 - on.spo2_per_gas_exchange_unit * g, d) for g in G_VALUES] for d in DPACO2_VALUES}
    mono = lambda rows: all(all(b <= x for x, b in zip(r, r[1:])) for r in rows)        # noqa: E731
    out["O5"] = {"spo2_by_G": table, "spo2_change_from_paco2_by_G": change,
                 "statement": "with the same PaCO2 change a worse G never raises the final SpO2; the size of the SpO2 "
                              "change need not shrink (a lower PaO2 sits on a steeper part of the curve)",
                 "pass": mono(table.values())}
    out["O6"] = {"analytic_room_air": analytic, "pass": mono(analytic.values()) and mono(table.values())}
    # O7: more FiO2 never lowers SpO2 (at every G and PaCO2 change).
    fio2_rows = {f"{f}_{g}": [spo2(_with(s0, f, g, fi), a, on) for fi in FIO2_VALUES]
                 for f in EFFICIENCY_FACTORS for g in G_VALUES}
    out["O7"] = {"rows": fio2_rows, "pass": all(all(b >= x for x, b in zip(r, r[1:])) for r in fio2_rows.values())}
    # O8 / O9: no backward write; G moves no PaCO2.
    keys = ("intrinsic", "burden", "hco3", "drive", "rate", "efficiency", "ventilation", "resting", "paco2", "ph")
    same = all(dataclasses.astuple(dv.respiration(_with(s0, f, g), a, on))
               == dataclasses.astuple(dv.respiration(_with(s0, f, g), a, off)) for f in EFFICIENCY_FACTORS for g in G_VALUES)
    states_on = _course((sm.obstruction(OBSTRUCTION_RATE),), a, on)
    states_off = _course((sm.obstruction(OBSTRUCTION_RATE),), a, off)
    trail = lambda states, p: [(x.aux.mechanics_efficiency, x.aux.metabolic_acid_burden, x.aux.respiratory_distress,  # noqa: E731
                                dv.respiration(x, a, p).respiratory_rate, dv.respiration(x, a, p).paco2) for x in states]
    out["O8"] = {"respiration_same_with_and_without_link": same, "fields": list(keys),
                 "course_respiration_same": trail(states_on, on) == trail(states_off, off),
                 "note": "no direct write; a lower SpO2 can still reach the acid burden through the existing delivery "
                         "-> deficit -> acid path, one minute later, only when delivery falls below the extraction reserve",
                 "pass": same and trail(states_on, on) == trail(states_off, off)}
    out["O9"] = {"pass": len({paco2(_with(s0, 1.0, g), a, on) for g in G_VALUES}) == 1}
    # O10: the link moves only SpO2 (static: _perfusion's one insertion replaces spo2) and what reads SpO2 downstream.
    moved = set()
    for f in (0.7, 1.3):
        x = _with(s0, f, 0.5)
        d_on, d_off = dv.derive(x, a, on), dv.derive(x, a, off)
        moved |= {k for k in d_on.__dataclass_fields__ if getattr(d_on, k) != getattr(d_off, k)}
    stepped = set()
    for f in (0.7, 1.3):
        x = _with(s0, f, 0.5)
        for _ in range(3):
            n_on, _ = step(x, (), a, on)
            n_off, _ = step(x, (), a, off)
            stepped |= {fl.name for fl in fields(type(x)) if fl.name != "aux" and getattr(n_on, fl.name) != getattr(n_off, fl.name)}
            stepped |= {f"aux.{fl.name}" for fl in fields(type(x.aux)) if getattr(n_on.aux, fl.name) != getattr(n_off.aux, fl.name)}
            x = n_on
    course_on = _course((mc.SyntheticMechanics("p2t5-o10", 0.99, 0, COURSE_MINUTES),), a, on)
    course_off = _course((mc.SyntheticMechanics("p2t5-o10", 0.99, 0, COURSE_MINUTES),), a, off)
    channels = ("V", "T", "P", "R", "L", "G", "W", "D", "N", "hb", "fio2")
    course = sorted({c for x, y in zip(course_on, course_off) for c in channels if getattr(x, c) != getattr(y, c)}
                    | {f"aux.{fl.name}" for x, y in zip(course_on, course_off) for fl in fields(type(x.aux))
                       if getattr(x.aux, fl.name) != getattr(y.aux, fl.name)})
    allowed_step = {"D", "R", "N", "aux.sympathetic_drive", "aux.lactate_excess_mmol_l", "aux.metabolic_acid_burden"}
    out["O10"] = {"perfusion_insertion_only": _perfusion_insertion_only(), "derive_fields_moved": sorted(moved),
                  "one_step_state_fields_moved": sorted(stepped), "course_state_fields_moved": course,
                  "routes": "SpO2 -> delivery (D, lactate, acid burden one minute later when delivery falls below the "
                            "extraction reserve); SpO2 -> the sympathetic target's hypoxaemia term (HR); SpO2 -> the "
                            "ADOPTED consciousness ladder. No direct write to V, T, P, R, L, D, G, W or lactate",
                  "pass": _perfusion_insertion_only() and moved <= {"spo2", "delivery_rel", "consciousness_level"}
                  and stepped <= allowed_step and not ({"V", "L", "G", "W", "hb", "fio2"} & set(course))}
    # O11: no PaO2 state.
    state_fields = sorted(f.name for f in fields(type(s0))) + sorted(AUXILIARY_FIELDS)
    out["O11"] = {"pao2_in_state": any("pao2" in n.lower() for n in state_fields),
                  "state_files_untouched": tm_common_ok(("clinical_core/state.py", "clinical_core/integration.py",
                                                         "clinical_core/provenance.py")),
                  "pass": not any("pao2" in n.lower() for n in state_fields)
                  and tm_common_ok(("clinical_core/state.py", "clinical_core/integration.py", "clinical_core/provenance.py"))}
    out["guards"] = {"mechanics_off_refused": _refused(lambda: replace(dv.DEFAULT_PROFILE, respiratory_quotient=SYNTHETIC_R)),
                     "committed_pe_refused": _refused(lambda: replace(em.profile(), respiratory_quotient=SYNTHETIC_R)),
                     "hypoxaemic_refused": _refused(lambda: replace(rd.hypoxaemic(mc.base_profile(), rd.SYNTHETIC_GAINS[0]),
                                                                    respiratory_quotient=SYNTHETIC_R)),
                     "non_positive_refused": all(_refused(lambda v=v: probe_profile(v)) for v in (0.0, -0.8, math.nan, True)),
                     "apnoea_unresolved": _apnoea(a, on)}
    out["guards"]["pass"] = all(v for k, v in out["guards"].items())
    out["pass"] = all(v["pass"] for v in out.values())
    return out


def _apnoea(anchors, on) -> bool:
    """No alveolar ventilation (central availability 0): PaCO2 is undefined, so the link raises UnresolvedBoundary
    (APNOEA_BOUNDARY_UNRESOLVED) instead of choosing a value; with the link off the same state derives as before."""
    apnoeic = replace(on, central_drive_availability=0.0)
    try:
        spo2(dv.arrival_state(anchors, apnoeic), anchors, apnoeic)
    except UnresolvedBoundary as exc:
        raised = "APNOEA_BOUNDARY_UNRESOLVED" in str(exc)
    else:
        raised = False
    off = replace(apnoeic, respiratory_quotient=None)
    return raised and spo2(dv.arrival_state(anchors, off), anchors, off) == anchors.spo2


def tm_common_ok(names) -> bool:
    return all(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == COMMON_AT_P2T3[n] for n in names)


def structural_pairs() -> dict:
    """The mechanics-on structural probe pairs (link on) of the oedema, PE and asthma 49m / 24f."""
    out = {"edema": _mechanics_on(pe.profile(), er.anchors(), float(er.truth()["abg_paco2"])),
           "pe": _mechanics_on(em.profile(), mr.anchors(), float(mr.truth()["abg_paco2"]))}
    for case in (tm.PRIMARY, tm.SECONDARY):
        a, p, _ = _asthma(case)
        out[case] = (a, p)
    return out


def committed_pairs() -> dict:
    from . import acs_reference as ar
    from . import gi_reference as gr
    from . import blood_fluid_calibration as bfc
    return {"acs": (ar.anchors(), ar.common_profile()), "edema": (er.anchors(), pe.profile()),
            "pe": (mr.anchors(), em.profile()), "asthma": (sm.sr.anchors(), sm.profile())}


def _course(items, anchors, profile, minutes=COURSE_MINUTES, start=None):
    state = dv.arrival_state(anchors, profile) if start is None else start
    states = [state]
    for _ in range(minutes):
        state, _ = step(state, tuple(items), anchors, profile)
        states.append(state)
    return states


# P2T-5-5 to -9: family structural probes --------------------------------------------------------------------------------------

def opioid_probe() -> dict:
    """A synthetic central depression (fixed states, G neutral). The central availability is a profile constant in the
    core, so the depressed and restored PaCO2 are read by the core's respiration on the same state under each
    availability, and the link's own arithmetic is applied against the undepressed arrival reference. A time-varying
    availability (a writer) belongs to the opioid migration."""
    a, on = probe_anchors(), probe_profile()
    s0 = dv.arrival_state(a, on)
    ref = dv.arrival_paco2_reference(a, on)
    depressed = replace(on, central_drive_availability=DEPRESSED_AVAILABILITY)
    base = spo2(s0, a, on)
    rows = {}
    for label, prof in (("depressed", depressed), ("restored", on)):
        r = dv.respiration(s0, a, prof)
        rows[label] = {"availability": prof.central_drive_availability, "rr": r.respiratory_rate, "W": r.ventilation,
                       "paco2": r.paco2, "spo2": shift(base, r.paco2 - ref), "G": s0.G}
    out = {"rows": rows, "arrival_reference": ref, "spo2_base": base, "label": "FIXED_STATE_COMPARATIVE_PROBE",
           "no_opioid_writer": True,
           "gap": "CENTRAL_AVAILABILITY_IS_A_PROFILE_CONSTANT: depression / reversal over time needs an availability "
                  "writer (opioid migration)"}
    d, r = rows["depressed"], rows["restored"]
    out["pass"] = (d["rr"] < r["rr"] and d["W"] < r["W"] and d["paco2"] > r["paco2"] and d["spo2"] < base
                   and r["spo2"] == base and d["G"] == 0.0)
    # Ventilation improving after arrival, in the integrated core: a mechanics relief raises W, lowers PaCO2, raises SpO2.
    relief = mc.SyntheticMechanics("p2t5-relief", RELIEF["factor_per_min"], RELIEF["from_minute"], RELIEF["to_minute"])
    st = _course((relief,), a, on)
    m = RELIEF["to_minute"]
    out["integrated_improvement"] = {"paco2": [paco2(st[0], a, on), paco2(st[m], a, on)],
                                     "spo2": [spo2(st[0], a, on), spo2(st[m], a, on)]}
    out["pass"] = out["pass"] and paco2(st[m], a, on) < paco2(st[0], a, on) and spo2(st[m], a, on) > spo2(st[0], a, on)
    return out


def _asthma(case: str):
    w = json.loads(tm.RECORD.read_text(encoding="utf-8"))["witnesses"]["MID"]
    c = w["cases"][case]
    a = tm.witness_anchors(case, c["intrinsic_rr"], c["distress"])
    p = replace(tm.witness_profile(w["k"], w["rho"], w["g_rr"]), respiratory_quotient=SYNTHETIC_R)
    return a, p, replace(p, respiratory_quotient=None)


def asthma_probes() -> dict:
    out = {}
    for case in (tm.PRIMARY, tm.SECONDARY):
        a, on, off = _asthma(case)
        worse_on = _course((sm.obstruction(OBSTRUCTION_RATE),), a, on)
        worse_off = _course((sm.obstruction(OBSTRUCTION_RATE),), a, off)
        both = _course((sm.obstruction(OBSTRUCTION_RATE), tm.SyntheticAsthmaVQ("p2t5-vq", tm.G_PROBE_PER_MIN)), a, on)
        g_only = _course((tm.SyntheticAsthmaVQ("p2t5-vq", tm.G_PROBE_PER_MIN),), a, on)
        relief = mc.SyntheticMechanics("p2t5-relief", RELIEF["factor_per_min"], RELIEF["from_minute"], RELIEF["to_minute"])
        relieved = _course((relief,), a, on)
        end, m = COURSE_MINUTES, RELIEF["to_minute"]
        row = {"arrival_exact": spo2(worse_on[0], a, on) == spo2(worse_off[0], a, off) == float(sm.sr.truth(case)["spo2"]),
               "obstruction": {"paco2": [paco2(worse_on[0], a, on), paco2(worse_on[end], a, on)],
                               "spo2_link_on": [spo2(worse_on[0], a, on), spo2(worse_on[end], a, on)],
                               "spo2_link_off": [spo2(worse_off[0], a, off), spo2(worse_off[end], a, off)],
                               "G": worse_on[end].G},
               "serial_with_direct_G": {"both": spo2(both[end], a, on), "g_only": spo2(g_only[end], a, on),
                                        "mechanics_only": spo2(worse_on[end], a, on)},
               "relief": {"paco2": [paco2(relieved[0], a, on), paco2(relieved[m], a, on)],
                          "spo2": [spo2(relieved[0], a, on), spo2(relieved[m], a, on)]},
               "serial_composition": _decomposed(both, a, on) and _decomposed(worse_on, a, on)}
        o = row["obstruction"]
        row["pass"] = (row["arrival_exact"] and row["serial_composition"] and o["paco2"][1] > o["paco2"][0] and o["spo2_link_on"][1] < o["spo2_link_on"][0]
                       and o["spo2_link_off"][1] == o["spo2_link_off"][0] and o["G"] == 0.0
                       and row["serial_with_direct_G"]["both"] < min(row["serial_with_direct_G"]["g_only"],
                                                                     row["serial_with_direct_G"]["mechanics_only"])
                       and row["relief"]["paco2"][1] < row["relief"]["paco2"][0]
                       and row["relief"]["spo2"][1] > row["relief"]["spo2"][0])
        out[case] = row
    out["pass"] = all(out[c]["pass"] for c in (tm.PRIMARY, tm.SECONDARY))
    return out


def _mechanics_on(profile, anchors, paco2_value: float):
    """A committed mapping read with the mechanics candidate on (STRUCTURAL_PROBE only): its arrival efficiency is
    P2S-2-11's analytic form at the committed intrinsic RR and the model's own arrival RR, so the arrival PaCO2 is the
    authored one (the committed mappings under-express the authored RR; that is not this package's)."""
    intrinsic = dv.intrinsic_respiratory_rate(anchors)
    rr = dv.respiration(dv.arrival_state(anchors, profile), anchors, profile).respiratory_rate
    e = mc.implied_efficiency(rr, paco2_value, intrinsic)
    return (replace(anchors, arrival_mechanics_efficiency=e),
            replace(profile, respiratory_mechanics=True, ventilation_efficiency=1.0, respiratory_quotient=SYNTHETIC_R))


def _decomposed(states, anchors, on) -> bool:
    """Serial composition on the same states: the link's SpO2 is the link-off SpO2 (G's path) shifted by that state's
    PaCO2 change, nothing more (no double counting)."""
    off = replace(on, respiratory_quotient=None)
    ref = dv.arrival_paco2_reference(anchors, on)
    return all(spo2(s, anchors, on) == shift(spo2(s, anchors, off), paco2(s, anchors, on) - ref) for s in states)


def _paco2_trail(states, anchors, profile) -> list:
    return [paco2(s, anchors, profile) for s in states]


def pe_probe() -> dict:
    """PE's direct G physiology with the link on (STRUCTURAL_PROBE, mechanics on): G moves no PaCO2 on any state, the link
    adds only the state's model PaCO2 change and the composition is serial. Over a course, PE's low arrival delivery lets
    a lower SpO2 reach the acid burden through the existing delivery -> deficit -> acid path (one minute later), which
    raises the drive a little; that path predates P2T-5 (it acts with the link off too) and is reported, not added."""
    t = mr.truth()
    a, on = _mechanics_on(em.profile(), mr.anchors(), float(t["abg_paco2"]))
    off = replace(on, respiratory_quotient=None)
    g = em.gas()
    st_on, st_off = _course((g,), a, on), _course((g,), a, off)
    plain_on, plain_off = _course((), a, on), _course((), a, off)
    end = COURSE_MINUTES
    out = {"committed_mechanics_off_refused": _refused(lambda: replace(em.profile(), respiratory_quotient=SYNTHETIC_R)),
           "G": [st_on[0].G, st_on[end].G],
           "same_state_g_moves_no_paco2": all(paco2(s.evolve(G=0.0), a, on) == paco2(s, a, on) for s in st_on),
           "serial_composition": _decomposed(st_on, a, on),
           "spo2_on": [spo2(st_on[0], a, on), spo2(st_on[end], a, on)],
           "spo2_off": [spo2(st_off[0], a, off), spo2(st_off[end], a, off)],
           "spo2_plain_course_on": spo2(plain_on[end], a, on),
           "paco2_end": {"G_link_on": paco2(st_on[end], a, on), "G_link_off": paco2(st_off[end], a, off),
                         "plain_link_on": paco2(plain_on[end], a, on), "plain_link_off": paco2(plain_off[end], a, off)},
           "existing_indirect_route": "delivery -> deficit -> acid burden -> drive (minute-lagged; predates P2T-5)",
           "drift": "the committed mapping's arrival acid burden clears, the drive and RR fall and PaCO2 rises a little; "
                    "with the link on, that model PaCO2 rise lowers SpO2 too (the plain course shows it without G)",
           "label": "STRUCTURAL_PROBE (mechanics on)"}
    e = out["paco2_end"]
    out["indirect_route_compensatory"] = e["G_link_off"] <= e["plain_link_off"] and e["G_link_on"] <= e["G_link_off"]
    out["pass"] = (out["committed_mechanics_off_refused"] and out["G"][1] > 0.0 and out["same_state_g_moves_no_paco2"]
                   and out["serial_composition"] and out["spo2_on"][0] == out["spo2_off"][0] == float(t["spo2"])
                   and out["spo2_on"][1] < out["spo2_on"][0] and out["spo2_on"][1] < out["spo2_plain_course_on"]
                   and out["indirect_route_compensatory"])
    return out


def edema_probe() -> dict:
    """Oedema: L reaches SpO2 through G only, a mechanics worsening through PaCO2 only; together they compose serially
    (no double counting). STRUCTURAL_PROBE (mechanics on)."""
    t = er.truth()
    a, on = _mechanics_on(pe.profile(), er.anchors(), float(t["abg_paco2"]))
    worse = mc.SyntheticMechanics("p2t5-edema-mechanics", EDEMA_MECHANICS_FACTOR, 0, COURSE_MINUTES)
    end = COURSE_MINUTES
    plain, l_only = _course((), a, on), _course((pe.writer(),), a, on)
    m_only, both = _course((worse,), a, on), _course((pe.writer(), worse), a, on)
    out = {"l_only": {"L": l_only[end].L, "G": l_only[end].G, "paco2": [paco2(l_only[0], a, on), paco2(l_only[end], a, on)],
                      "spo2": spo2(l_only[end], a, on)},
           "mechanics_only": {"L": m_only[end].L, "G": m_only[end].G,
                              "paco2": [paco2(m_only[0], a, on), paco2(m_only[end], a, on)], "spo2": spo2(m_only[end], a, on)},
           "both": {"L": both[end].L, "G": both[end].G, "paco2": paco2(both[end], a, on), "spo2": spo2(both[end], a, on)},
           "plain": {"paco2": paco2(plain[end], a, on), "spo2": spo2(plain[end], a, on)},
           "arrival": spo2(l_only[0], a, on),
           "l_moves_no_paco2": _paco2_trail(l_only, a, on) == _paco2_trail(plain, a, on),
           "mechanics_moves_no_g": all(s.G == 0.0 and s.L == 0.0 for s in m_only),
           "serial_composition": all(_decomposed(s, a, on) for s in (l_only, m_only, both)),
           "label": "STRUCTURAL_PROBE (mechanics on)"}
    lo, mo, bo = out["l_only"], out["mechanics_only"], out["both"]
    out["pass"] = (out["arrival"] == float(t["spo2"]) and lo["G"] > 0.0 and out["l_moves_no_paco2"]
                   and out["mechanics_moves_no_g"] and mo["paco2"][1] > out["plain"]["paco2"]
                   and out["serial_composition"] and bo["L"] == lo["L"] and bo["G"] == lo["G"]
                   and bo["paco2"] == mo["paco2"][1] and lo["spo2"] < out["plain"]["spo2"]
                   and mo["spo2"] < out["plain"]["spo2"] and bo["spo2"] < min(lo["spo2"], mo["spo2"]))
    return out


# P2T-5-10 to -16: FiO2, downstream, causality ------------------------------------------------------------------------------

def fio2_masking() -> dict:
    a, on = probe_anchors(), probe_profile()
    s0 = dv.arrival_state(a, on)
    rows = {}
    for f in (0.21, MASKING_FIO2, *PLATEAU_FIO2):
        base, worse = _with(s0, 1.0, None, f), _with(s0, 0.7, None, f)
        rows[str(f)] = {"spo2_base_state": spo2(base, a, on), "spo2_hypoventilating": spo2(worse, a, on),
                        "drop": spo2(base, a, on) - spo2(worse, a, on)}
    out = {"rows": rows, "status": "FIO2_RESPONSE_MAGNITUDE_DEBT: the FiO2 rule is unchanged",
           "plateau": "ODC_PLATEAU_IDENTIFIABILITY_DEBT: a SpO2_base of 100 gives an unresolved PaO2 (+inf) and no change",
           "fio2_rule_unchanged": _perfusion_insertion_only() and "oxygenation" not in audit()["changed"]
           and "spo2_per_fio2" not in mc._names(mc._functions(_live("clinical_core/derived.py"))["ventilated_oxygenation"])}
    r = [rows[str(f)]["drop"] for f in (0.21, MASKING_FIO2, *PLATEAU_FIO2)]
    plateau = [rows[str(f)]["spo2_base_state"] for f in PLATEAU_FIO2]
    out["pass"] = (r[0] > r[1] > 0.0 and all(d == 0.0 for d in r[2:]) and all(s == 100.0 for s in plateau)
                   and rows[str(MASKING_FIO2)]["spo2_base_state"] < 100.0 and out["fio2_rule_unchanged"])
    return out


def _downstream_row(anchors, on, factor) -> dict:
    off = replace(on, respiratory_quotient=None)
    worse = mc.SyntheticMechanics("p2t5-worse", factor, 0, COURSE_MINUTES)
    st_on, st_off = _course((worse,), anchors, on), _course((worse,), anchors, off)
    x_on, x_off = st_on[COURSE_MINUTES], st_off[COURSE_MINUTES]
    d_on, d_off = dv.derive(x_on, anchors, on), dv.derive(x_off, anchors, off)
    return {"factor_per_min": factor, "paco2": paco2(x_on, anchors, on), "spo2": [d_on.spo2, d_off.spo2],
            "delivery": [dv.delivery_rel_of(x_on, anchors, on), dv.delivery_rel_of(x_off, anchors, off)],
            "D": [x_on.D, x_off.D], "lactate": [d_on.lactate, d_off.lactate],
            "hr": [d_on.pulse_rate_bpm, d_off.pulse_rate_bpm],
            "consciousness": [d_on.consciousness_level, d_off.consciousness_level]}


def downstream() -> dict:
    """SpO2 -> DO2 -> D / lactate, HR and consciousness through the existing readers only (link on against off, the same
    synthetic mechanics worsening). The probe patient keeps delivery above the extraction reserve (no D); PE's mapping,
    with arrival debt and a low arrival delivery, shows the D and lactate direction."""
    a, on = probe_anchors(), probe_profile()
    pe_a, pe_on = structural_pairs()["pe"]
    rows = {"probe": _downstream_row(a, on, DOWNSTREAM_FACTORS["probe"]),
            "pe": _downstream_row(pe_a, pe_on, DOWNSTREAM_FACTORS["pe"])}
    out = {"rows": rows,
           "hr_route": "existing: the sympathetic target's hypoxaemia term (relative to arrival); no new HR reader",
           "consciousness_status": ["CONSCIOUSNESS_INTEGRATION_DEBT",
                                    "HYPERCAPNIA_SIGNAL_STRUCTURALLY_SUPPORTED_BOUNDS_NOT_IDENTIFIABLE",
                                    "the ADOPTED ladder reads SpO2 only: a link-lowered SpO2 can move it; no CO2 narcosis "
                                    "is encoded"],
           "acid_base": "respiration (W, PaCO2, pH, HCO3, acid burden, drive) never reads the link (O8)",
           "hypoxaemic_loop": "HYPOXEMIC_FEEDBACK_LOOP_DEFERRED: the link refuses the hypoxaemic drive"}
    pr, pp = rows["probe"], rows["pe"]
    out["pass"] = (all(r["spo2"][0] < r["spo2"][1] and r["delivery"][0] < r["delivery"][1] and r["hr"][0] >= r["hr"][1]
                       and r["D"][0] >= r["D"][1] and r["lactate"][0] >= r["lactate"][1] for r in rows.values())
                   and pr["hr"][0] > pr["hr"][1] and pp["D"][0] > pp["D"][1] and pp["lactate"][0] > pp["lactate"][1])
    return out


def parameters() -> dict:
    committed = {**dm.committed_profiles(), "asthma_p2t3": sm.profile()}
    out = {"committed_r_none": {k: p.respiratory_quotient is None for k, p in committed.items()},
           "registry": list(dv.PARAMETERS["respiratory_quotient"]),
           "synthetic_r": {"value": SYNTHETIC_R, "label": SYNTHETIC_R_LABEL},
           "new_profile_fields": sorted(set(f.name for f in fields(dv.CoreProfile))
                                        - set(dm._class_fields(p2t3_text("clinical_core/derived.py"), "CoreProfile"))),
           "unset": ["respiratory_quotient (clinical value)", "hypoxaemic drive", "FiO2 magnitude (unchanged)",
                     "G parameters (unchanged)", "no tau / transmission / hypoventilation gain"]}
    out["pass"] = (all(out["committed_r_none"].values()) and out["registry"][0] == dv.PROVISIONAL
                   and out["registry"][1].startswith("UNSET (P2T-5)") and out["new_profile_fields"] == list(NEW_PROFILE_FIELDS))
    return out


def non_regression() -> dict:
    """With the link off (R None in every committed profile): P2T-3's record reproduced on its tree (which nests P2T-1A,
    P2T-1, P2S-3, P2S-2 and, through them, GI, ACS, the oedema, PE and P2P-2)."""
    with p2t3_view():
        p2t3 = tm.run()
    record = json.loads(tm.RECORD.read_text(encoding="utf-8"))
    out = {"p2t3_record_reproduced_on_its_tree": json.loads(json.dumps(p2t3, sort_keys=True, default=str)) == record,
           "p2t3_record_untouched": hashlib.sha256(tm.RECORD.read_bytes()).hexdigest() == P2T3_RECORD_SHA,
           "p2t3_verdict": p2t3["verdict"]["verdict"]}
    out["pass"] = out["p2t3_record_reproduced_on_its_tree"] and out["p2t3_record_untouched"]
    return out


# The proof: the P2T-3 tree plus P2T-5's declared insertions -------------------------------------------------------------------

P2T3_HEAD = "2c88e0d"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/asthma_distress_migration.py",\n'
                                     '                        "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                        "clinical_core/oxygenation_link.py", '
                                     '"clinical_core/oxygenation_link_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/asthma_distress_migration.py",\n'
                                     '                        "clinical_core/asthma_distress_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('    distress_to_sympathetic_gain: float | None = None\n'
                               '    # P2T-5: the common hypoventilation -> oxygenation link '
                               '(SYMMETRIC_RELATIVE_ALVEOLAR_LINK, full transmission), UNSET\n'
                               "    # (None) by default, so SpO2 is P2O-3's exactly. Declared, the PaCO2 change from "
                               "the model's own arrival PaCO2 moves\n"
                               '    # the alveolar oxygen by -dPaCO2 / respiratory_quotient, carried to SpO2 through '
                               'a latent PaO2 and the standard\n'
                               "    # dissociation relation; it needs the common mechanics candidate (PaCO2 is W's) "
                               'and refuses the hypoxaemic drive\n'
                               '    # (HYPOXEMIC_FEEDBACK_LOOP_DEFERRED). No value is chosen here.\n'
                               '    respiratory_quotient: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    distress_to_sympathetic_gain: float | None = None\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('                                     "physiology")\n'
                               '        rq = self.respiratory_quotient\n'
                               '        if rq is not None:\n'
                               '            if isinstance(rq, bool) or not isinstance(rq, (int, float)) or not '
                               'math.isfinite(rq) or rq <= 0.0:\n'
                               '                # P2T-5: UNSET is None (the link off); a declared link has a finite '
                               'positive respiratory quotient.\n'
                               '                raise CoreInvariantError("respiratory_quotient is None (UNSET: the '
                               'hypoventilation -> oxygenation link "\n'
                               '                                         "off) or a finite positive ratio")\n'
                               '            if not self.respiratory_mechanics:\n'
                               "                # P2T-5: the link reads W's PaCO2, never the retired P2K-2 arrival "
                               'PaCO2 anchor.\n'
                               '                raise CoreInvariantError("the hypoventilation -> oxygenation link '
                               'needs the common respiratory mechanics "\n'
                               '                                         "candidate (P2T-5): its PaCO2 must be '
                               'W\'s")\n'
                               '            if self.hypoxaemic_drive_mapping is not None:\n'
                               '                # P2T-5: SpO2 -> hypoxaemic drive -> RR -> PaCO2 -> SpO2 would be a '
                               'loop no audit has examined.\n'
                               '                raise CoreInvariantError("the hypoventilation -> oxygenation link '
                               'refuses the hypoxaemic drive "\n'
                               '                                         "(HYPOXEMIC_FEEDBACK_LOOP_DEFERRED)")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n',
                               '                                     "physiology")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n'),
                              ('                                                  "probes; not approved"),\n'
                               '    "respiratory_quotient": (PROVISIONAL, "UNSET (P2T-5): the respiratory quotient '
                               'of the common relative alveolar link "\n'
                               '                                          "(dPAO2 = -dPaCO2 / R, from the model\'s '
                               'own arrival PaCO2, full transmission "\n'
                               '                                          "to a latent PaO2 and the standard '
                               'dissociation relation); None by default "\n'
                               '                                          "(the link off); needs the mechanics '
                               'candidate; refuses the hypoxaemic drive; "\n'
                               '                                          "0.8 only as a '
                               'SYNTHETIC_PHYSIOLOGIC_REFERENCE in probes; not approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n',
                               '                                                  "probes; not approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n'),
                              ('        spo2 = oxygenation(state.G, state.fio2, anchors, profile, '
                               'lung_water_gas_credit(state.L, anchors, profile))\n'
                               '    if hypoventilation_link_active(profile):\n'
                               '        spo2 = ventilated_oxygenation(spo2, state, anchors, profile)\n'
                               '    delivery_rel = relative_delivery(output_rel, state.hb, spo2, anchors)\n',
                               '        spo2 = oxygenation(state.G, state.fio2, anchors, profile, '
                               'lung_water_gas_credit(state.L, anchors, profile))\n'
                               '    delivery_rel = relative_delivery(output_rel, state.hb, spo2, anchors)\n'),
                              ('\n'
                               'def oxygen_saturation_from_pao2(pao2: float) -> float:\n'
                               '    """P2T-5: the standard oxygen dissociation relation (Severinghaus 1979: pH 7.40, '
                               '37 C), SpO2 (%) from PaO2 (mmHg),\n'
                               '    with no fitted parameter: 100 / (1 + 23400 / (PaO2^3 + 150 PaO2)). Continuous '
                               'and strictly increasing on PaO2 > 0;\n'
                               '    0 at or below 0 (no oxygen); below 100 for every finite PaO2 and 100 only as '
                               'PaO2 -> inf (the plateau)."""\n'
                               '    if pao2 <= 0.0:\n'
                               '        return 0.0\n'
                               '    if math.isinf(pao2):\n'
                               '        return 100.0\n'
                               '    return 100.0 / (1.0 + 23400.0 / (pao2 ** 3 + 150.0 * pao2))\n'
                               '\n'
                               '\n'
                               'def pao2_from_oxygen_saturation(spo2: float) -> float:\n'
                               '    """P2T-5: the exact inverse of ``oxygen_saturation_from_pao2`` (the one real '
                               'root of PaO2^3 + 150 PaO2 = 23400 s /\n'
                               '    (100 - s), by Cardano): strictly increasing on 0 < SpO2 < 100; 0 at or below 0; '
                               '+inf at 100, where a saturated\n'
                               '    SpO2 does not identify the PaO2 (ODC_PLATEAU_IDENTIFIABILITY_DEBT: no PaO2 '
                               'ceiling and no epsilon is chosen; an\n'
                               '    alveolar change on the plateau then moves no SpO2)."""\n'
                               '    if spo2 <= 0.0:\n'
                               '        return 0.0\n'
                               '    if spo2 >= 100.0:\n'
                               '        return math.inf\n'
                               '    c = 23400.0 * spo2 / (100.0 - spo2)\n'
                               '    u = (c / 2.0 + math.sqrt(c * c / 4.0 + 125000.0)) ** (1.0 / 3.0)\n'
                               '    return u - 50.0 / u\n'
                               '\n'
                               '\n'
                               'def hypoventilation_link_active(profile: CoreProfile) -> bool:\n'
                               '    """P2T-5: whether the profile declares the hypoventilation -> oxygenation link '
                               '(off by default)."""\n'
                               '    return profile.respiratory_quotient is not None\n'
                               '\n'
                               '\n'
                               'def arrival_paco2_reference(anchors: Anchors, profile: CoreProfile) -> float:\n'
                               '    """P2T-5: the model-derived arrival PaCO2 of the common P2S-2 mechanics pathway '
                               '(the reference / W of the arrival\n'
                               '    state, computed from the anchors as ``respiration`` computes it there: the '
                               "arrival composition's RR, the arrival\n"
                               '    mechanics efficiency, the arrival demand ratio 1), never the authored PaCO2 as a '
                               'hidden anchor."""\n'
                               '    rate = arrival_drive_composition(anchors, profile).expressed_rr\n'
                               '    ventilation = alveolar_ventilation(rate, intrinsic_respiratory_rate(anchors), '
                               'anchors.arrival_mechanics_efficiency,\n'
                               '                                       1.0)\n'
                               '    return profile.paco2_reference_mmhg / ventilation\n'
                               '\n'
                               '\n'
                               'def ventilated_oxygenation(spo2_base: float, state: CoreState, anchors: Anchors, '
                               'profile: CoreProfile) -> float:\n'
                               '    """P2T-5 (SYMMETRIC_RELATIVE_ALVEOLAR_LINK, MINIMAL_RELATIVE_ALVEOLAR_GAS_LINK, '
                               'FULL_RELATIVE_ALVEOLAR_TRANSMISSION):\n'
                               '    the SpO2 of the existing G / L -> G / FiO2 path moved by the PaCO2 change from '
                               "the model's arrival PaCO2:\n"
                               '\n'
                               '        PaO2_latent = ODC^-1(SpO2_base);  dPaO2 = -(PaCO2 - PaCO2_arrival) / '
                               'respiratory_quotient;\n'
                               '        SpO2 = ODC(PaO2_latent + dPaO2)\n'
                               '\n'
                               '    Exact at arrival (dPaCO2 = 0 returns SpO2_base itself). Symmetric: more PaCO2 '
                               'never raises SpO2, less never lowers\n'
                               '    it. G is not a transmission coefficient here '
                               '(RETAINED_G_AS_ALVEOLAR_TRANSMISSION = REJECTED): it acts through\n'
                               '    SpO2_base only, so worse G and less FiO2 never raise SpO2. PaO2 is latent, never '
                               'a state; Patm, PH2O and the\n'
                               '    absolute alveolar gas equation are not used (they cancel in the relative form); '
                               'nothing is written back to PaCO2,\n'
                               '    W, RR, the drive or the acid burden. No ventilation (PaCO2 undefined) is an '
                               'undecided boundary."""\n'
                               '    paco2 = respiration(state, anchors, profile).paco2\n'
                               '    if paco2 is None:\n'
                               '        raise UnresolvedBoundary(f"minute {state.minute}: no alveolar ventilation, '
                               'so no PaCO2 for the hypoventilation -> "\n'
                               '                                 "oxygenation link (APNOEA_BOUNDARY_UNRESOLVED)")\n'
                               '    delta = paco2 - arrival_paco2_reference(anchors, profile)\n'
                               '    if delta == 0.0:\n'
                               '        return spo2_base\n'
                               '    return oxygen_saturation_from_pao2(pao2_from_oxygen_saturation(spo2_base) - '
                               'delta / profile.respiratory_quotient)\n'
                               '\n'
                               '\n'
                               'def sympathetic_target(state: CoreState, anchors: Anchors, profile: CoreProfile) -> '
                               'float:\n',
                               '\n'
                               'def sympathetic_target(state: CoreState, anchors: Anchors, profile: CoreProfile) -> '
                               'float:\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/distress_closure_report.py",\n'
                                     '                      "clinical_core/asthma_distress_migration_report.py",\n'
                                     '                      "clinical_core/oxygenation_link_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/distress_closure_report.py",\n'
                                     '                      "clinical_core/asthma_distress_migration_report.py")\n'
                                     '\n'),)}
CORE_AT_P2T3 = {'clinical_core/decision_pack.py': '7a51cece643da475edd7b70fd3588f84094db4f0c954512161b83587157a2375',
 'clinical_core/derived.py': '6ebc433e0e6373c605caa465f2f71f3940f55011e7b52ccf1d52fea001c15368',
 'clinical_core/lactate_slice.py': '754fee1097ed77a458c0b6f84575a65006798c03fdb61653a6a725c341d320c0'}
# </reversal>
# <common>
COMMON_AT_P2T3 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
P2T3_FREEZE_DIGEST = "3a648a9e055c9182fe670f5360f1cc73d1d799b9f1bd3d557df2ffdf67e2efb2"
P2T3_RECORD_SHA = "6fa395eaaf70dbf1f11c91e08d5758495e907b68b02e79ad83b509aae8ae13ac"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2T3[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2T3.items()}


def p2t3_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2T-3 file plus P2T-5's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2t3_bytes(relative: str) -> bytes:
    return p2t3_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2t3_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2T3.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def _tm_common_untouched() -> dict:
    return {relative: hashlib.sha256(p2t3_bytes(relative)).hexdigest() == sha
            for relative, sha in tm.COMMON_AT_P2T1A.items()}


def _fields_at_p2t3(cls):
    """dataclasses.fields as the P2T-3 tree had them: CoreProfile without P2T-5's new field."""
    out = dataclasses.fields(cls)
    return tuple(f for f in out if f.name not in NEW_PROFILE_FIELDS) if cls is dv.CoreProfile else out


class _TreeFile:
    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2t3_text(self.relative)


class _TreeDir:
    """P2S-2's ``CORE_DIR`` (its audit lists who reads the arrival mechanics anchor from derived.py): the P2T-3 text of
    P2T-5's changed files, the live path of anything else (P2T-5's arrival PaCO2 reference is a new reader there)."""

    def __truediv__(self, name):
        relative = f"clinical_core/{name}"
        return _TreeFile(relative) if relative in REVERSAL else CORE_DIR / name

    def rglob(self, pattern):
        return CORE_DIR.rglob(pattern)


P2T3_PARAMETERS = {k: v for k, v in dv.PARAMETERS.items() if k not in NEW_PROFILE_FIELDS}
_FREEZE_SOURCES = bf.freeze_sources


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2T-3's view reads the P2T-3 files (proven) and their bytes, its captured
    source map is P2T-3's, P2S-2's audit reads derived.py as P2T-3 left it, and the closed listings of the profile and
    its registry read them as P2T-3 left them (P2T-5's one new field, None in every closed profile, out). P2T-5 changes no
    behaviour with the link off."""
    patch.setattr(tm, "_live", p2t3_text)
    patch.setattr(tm, "common_untouched", _tm_common_untouched)
    patch.setattr(tm, "_FREEZE_SOURCES", lambda: p2t3_sources(_FREEZE_SOURCES()))
    for module in (dm, xm, tm):
        patch.setattr(module, "fields", _fields_at_p2t3)
    patch.setattr(dv, "PARAMETERS", P2T3_PARAMETERS)
    patch.setattr(mc, "CORE_DIR", _TreeDir())


def tree(patch) -> None:
    """The whole P2T-3 tree, for P2T-3's own analysis and tests: the chain, the source map, and P2T-1A's reader (which
    read the live tree while P2T-3 was the live tree) reading the P2T-3 files."""
    chain(patch)
    patch.setattr(xm, "_live", p2t3_text)
    patch.setattr(bf, "freeze_sources", lambda: p2t3_sources(_FREEZE_SOURCES()))


class p2t3_view:
    """P2T-3's analysis reading the tree P2T-3 froze, for its own proofs and its record."""

    def __enter__(self):
        self._patch = mc._Patch()
        tree(self._patch)
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2t3_view():
        digest = tm.freeze_digest()
        proof = tm.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2t3_freeze_digest": digest == P2T3_FREEZE_DIGEST,
            "p2t3_proof": all(proof["proofs"].values()) and all(proof["common_untouched"].values())
            and proof["p2t1a_freeze_digest"] and proof["p2t1a_proof"] and proof["p2t1a_record"],
            "p2t3_record": hashlib.sha256(tm.RECORD.read_bytes()).hexdigest() == P2T3_RECORD_SHA}


# Readiness (predeclared) ------------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "the relative symmetric alveolar link works (O3, O4) with full transmission and no new parameter (audit)",
    "no new PaO2 state is required (O11) and the dissociation relation is the standard one, monotone, unfitted",
    "arrival exact with the link on (O2) and the default off exact (O1)",
    "G and hypoventilation compose independently and monotonically (O5, O6, O7, O9; asthma serial; edema)",
    "opioid-like hypoventilation lowers SpO2 without G and better ventilation raises it (opioid probe)",
    "asthma mixed physiology is representable (49m and 24f probes)",
    "PE's G physiology stays orthogonal and edema avoids double counting",
    "no feedback into PaCO2 or the drive (O8, the hypoxaemic loop refused) and the guards hold",
    "the downstream SpO2 -> delivery -> D / lactate / HR directions hold through existing paths",
    "the parameters stay UNSET clinically (R None everywhere committed; 0.8 synthetic only)",
    "non-regression: P2T-3's record on its tree, every other file proven",
)
READY = "COMMON_HYPOVENTILATION_OXYGENATION_LINK_READY"
NOT_READY = "COMMON_HYPOVENTILATION_OXYGENATION_LINK_NOT_READY"
READINESS_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def readiness(found: dict) -> dict:
    p, proof = found["probes"], found["proof"]
    checks = (
        p["O3"]["pass"] and p["O4"]["pass"] and found["audit"]["pass"],
        p["O11"]["pass"] and found["odc"]["pass"],
        p["O1"]["pass"] and p["O2"]["pass"],
        p["O5"]["pass"] and p["O6"]["pass"] and p["O7"]["pass"] and p["O9"]["pass"] and found["asthma"]["pass"]
        and found["edema"]["pass"],
        found["opioid"]["pass"],
        found["asthma"]["pass"],
        found["pe"]["pass"] and found["edema"]["pass"],
        p["O8"]["pass"] and p["guards"]["pass"] and found["retained"]["pass"],
        found["downstream"]["pass"] and found["fio2"]["pass"] and p["O10"]["pass"],
        found["parameters"]["pass"],
        found["non_regression"]["pass"] and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2t3_freeze_digest"] and proof["p2t3_proof"] and proof["p2t3_record"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    return {"criteria": rows, "blocker": blocker, "rule": READINESS_RULE,
            "verdict": READY if blocker is None else f"{NOT_READY} - {blocker}"}


def design() -> dict:
    return {"decisions": DECISIONS, "new_profile_fields": list(NEW_PROFILE_FIELDS), "new_functions": list(NEW_FUNCTIONS),
            "synthetic_r": SYNTHETIC_R, "efficiency_factors": list(EFFICIENCY_FACTORS), "g_values": list(G_VALUES),
            "fio2_values": list(FIO2_VALUES), "dpaco2_values": list(DPACO2_VALUES),
            "depressed_availability": DEPRESSED_AVAILABILITY, "obstruction_rate": OBSTRUCTION_RATE, "relief": RELIEF,
            "course_minutes": COURSE_MINUTES, "edema_mechanics_factor": EDEMA_MECHANICS_FACTOR,
            "masking_fio2": MASKING_FIO2, "plateau_fio2": list(PLATEAU_FIO2), "downstream_factors": DOWNSTREAM_FACTORS,
            "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2t3": CORE_AT_P2T3, "common_at_p2t3": COMMON_AT_P2T3,
            "p2t3": {"head": P2T3_HEAD, "freeze_digest": P2T3_FREEZE_DIGEST, "record": P2T3_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2t3": hashlib.sha256(tm.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "odc": odc(), "retained": retained_audit(),
             "probes": probes(), "opioid": opioid_probe(), "asthma": asthma_probes(), "pe": pe_probe(),
             "edema": edema_probe(), "fio2": fio2_masking(), "downstream": downstream(), "parameters": parameters(),
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
