"""P2P-1: pulmonary_edema_58m migrated in shadow with a family L writer, on the unchanged common core.

    python -m clinical_core.edema_migration [--digest] [--out <json>]

The test of the architecture P2O-1 / P2O-3 left: a family-specific congestion writer -> L -> the common G -> SpO2 /
oxygen delivery, in a respiratory / congestive family, without changing any common file. The family writer
(``modules/pulmonary_edema.EdemaCongestion``) owns L for the run (P2O-3's authority), writes L only, and composes the
family's progression and its treatment-driven decongestion in one coordinator; everything downstream is common.
Nothing is calibrated: k, s and r stay UNSET in the core, the probes run on P2O-1's SYNTHETIC_ONLY gas-exchange reference
and the ACS package's predeclared common point, and the family's rates are a sparse span fixed before any run. L_rev
stays 0 (no authored observation after arrival asks for improvement below the arrival congestion). The legacy engine is
read last, as reference only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import acs_migration as an
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import edema_reference as er
from . import gas_exchange_architecture as go
from . import lung_water_reference as lw
from .bands import Drift
from .integration import _REGISTRY, step
from .interventions.oxygen import Oxygen
from .modules.acs_ischaemia import IschaemicCongestion
from .modules.pulmonary_edema import EDEMA_DECONGESTION, DecongestiveTreatment, EdemaCongestion
from .provenance import BloodProcess, ProvenanceError
from .state import Channel

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2P-1"
OWN = ("clinical_core/edema_migration.py", "clinical_core/edema_reference.py", "clinical_core/modules/pulmonary_edema.py")
REPORT = "clinical_core/edema_migration_report.py"
RECORD = ROOT / "docs" / "revision" / "P2P1_pulmonary_edema.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2P1_EDEMA_PULMONAR_SOMBRA.md"
#: The tuples P2P-1 extended (its analysis and report are downstream of every numerical artifact).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
#: The family's own types (registered by importing the module); the closed packages' registry view leaves them out.
FAMILY_TYPES = (EdemaCongestion.type_name, DecongestiveTreatment.type_name)


# The faculty's decisions (fixed) ---------------------------------------------------------------------------------------------

DECIDED = {
    "goal": "test family-specific congestion writer -> L -> common G -> SpO2 / oxygen delivery in a respiratory / "
            "congestive family without changing the common core; not to fit one case",
    "one_owner": "one authoritative L owner per run; several congestion mechanisms compose inside one family "
                 "writer / coordinator",
    "override": "FAMILY_CONGESTION_WRITER_OVERRIDES_COMMON_OVERLOAD_WRITER: with the family writer present the common "
                "overload generator adds no L, by design",
    "zero_gain_owner": "an owner with zero gain still suppresses the common overload writer (accepted)",
    "l_rev": "L_rev <= 0, default 0 (P2O-1 exactly); a declared case / family parameter with provenance only when a "
             "migrated family adopts a nonzero value; default 0 unless pulmonary_edema's authored truth requires otherwise",
    "g_guard": "the G guard behaviour stays as it is; no special exception is added for L_rev = 0",
    "v_l_apart": "V from preload evidence (IVC, filling context); L from pulmonary congestion evidence (B-lines, edema, "
                 "crackles, radiograph); B-lines never inform V",
    "acs_mapping_debt": "the ACS pump_reserve band citing B-lines is stale under the authority model: "
                        "MAPPING_DOCUMENTATION_DEBT; B-lines are never pump or preload evidence",
}


# P2P-1-1: the canonical case and its truth -----------------------------------------------------------------------------------

#: What each truth item is (AUTHORED_CASE_TRUTH, LEGACY_ENGINE_BEHAVIOR or MODEL_DERIVED).
TRUTH_CLASSES = {
    **{item: "AUTHORED_CASE_TRUTH" for item in er.TRUTH_PATHS},
    "definitive_actions": "AUTHORED_CASE_TRUTH (faculty-declared definitive actions; also the TDFC declarations)",
    "congestion_block": "LEGACY_ENGINE_BEHAVIOR (the case's input to the legacy engine: fluid sensitivity 1.0, no volume "
                        "overload; read as context for V, never as a rate)",
}
LEGACY_CONSTANTS = "family_engine.EDEMA (drift 0.003/min, NIV, nitrate, diuretic, recruitment): LEGACY_ENGINE_BEHAVIOR"
LATER_OBSERVATIONS = ("NONE_AUTHORED: the case states the arrival only; the TDFC declarations ask the resident to "
                      "reassess SpO2, respiratory rate and pressure and to judge the response, but no value after "
                      "arrival is authored")


def case() -> dict:
    t = er.truth()
    return {"case": er.CASE, "family": er.FAMILY, "source": "clinical_cases.py", "selection_rule": er.SELECTION_RULE,
            "other_variant": er.OTHER_VARIANT,
            "other_variant_diagnosis": er.bank_case(er.OTHER_VARIANT)["faculty"]["diagnosis"],
            "presentation": er.bank_case()["presentation"], "truth": t,
            "classes": {k: TRUTH_CLASSES[k] for k in t}, "legacy_constants": LEGACY_CONSTANTS,
            "later_observations": LATER_OBSERVATIONS, "available": all(v is not None for v in t.values())}


# The design (predeclared before any run) -------------------------------------------------------------------------------------

#: The family's progression: a sparse span, fixed before any run, on the scale of the ACS family writer's frozen untreated
#: course (L 0.508 at 120 min in the P2O-1 record, about 0.004 per minute), one x2 step either side; never the legacy
#: drift (0.003 of another index) and never fitted to an outcome (none is authored after arrival).
PROGRESSION = (0.0025, 0.005, 0.01)
MID = PROGRESSION[1]
#: Decongestion: the same scale, SYNTHETIC_ONLY; the treatment's signal at a declared minute (no magnitude is authored).
DECONGESTION = {"per_min": MID, "begins_at_minute": 60}
HORIZON = 120
READ = (0, 30, 60, 90, 120)
FIO2 = (0.4, 0.6)
#: The authority probes reuse P2O-3's overload scenario: preload fraction 0.7 and P 0.7 declared synthetic, 4000 mL.
OVERLOAD = {"preload_fraction": 0.7, "P": 0.7, "volume_ml": 4000.0}
#: The respiratory extension is expected when the authored arrival RR exceeds the common model's arrival RR by more than
#: this (breaths/min), or when a definitive action needs a deferred common extension.
RR_GAP = 5.0
DEFERRED_ACTIONS = {"niv": "VNI_COMMON_EXTENSION_DEFERRED"}
L_REV = 0.0


def profile(**changes) -> dv.CoreProfile:
    """The ACS package's predeclared common point with P2O-1's SYNTHETIC_ONLY gas-exchange reference (k 1, s 5, r 0.5)."""
    return go.gas_profile(er.common_profile(), **changes)


def writer(progression: float = MID, decongestion: float = 0.0) -> EdemaCongestion:
    return EdemaCongestion("edema-congestion", progression, decongestion)


def course(items, minutes: int = HORIZON, anchors=None, prof=None, start=None):
    anchors = er.anchors() if anchors is None else anchors
    prof = profile() if prof is None else prof
    return an.course(tuple(items), minutes, anchors, prof, start)


def reading(state, anchors, prof) -> dict:
    d = dv.derive(state, anchors, prof)
    r = dv.respiration(state, anchors, prof)
    return {"minute": state.minute, "L": state.L, "G": state.G, "V": state.V, "P": state.P,
            "fio2": state.fio2, "spo2": d.spo2, "hr": d.monitor_rate_bpm, "map": d.map, "rr": r.respiratory_rate,
            "paco2": r.paco2, "D": state.D, "lactate": d.lactate,
            "delivery_index": dv.effective_delivery(d.delivery_rel, anchors),
            "consciousness_level": d.consciousness_level}


def _rows(states, anchors, prof, minutes=READ) -> dict:
    return {str(m): reading(states[m], anchors, prof) for m in minutes}


def _nonincreasing(values) -> bool:
    return all(b <= a + 1e-12 for a, b in zip(values, values[1:]))


def _nondecreasing(values) -> bool:
    return all(b >= a - 1e-12 for a, b in zip(values, values[1:]))


# P2P-1-2 / 5: the arrival ---------------------------------------------------------------------------------------------------

def arrival() -> dict:
    a, prof = er.anchors(), profile()
    t = er.truth()
    s = dv.arrival_state(a, prof)
    r = reading(s, a, prof)
    authored = {"spo2": t["spo2"], "map": er.authored_map(t), "hr": t["hr"], "rr": t["respiratory_rate"],
                "paco2": t["abg_paco2"], "consciousness_level": er.LEVEL_OF[t["mental_status"]]}
    exact = {k: r[k] == authored[k] for k in ("spo2", "map", "paco2")}
    mismatches = {
        "hr": {"core": r["hr"], "authored": t["hr"],
               "class": "ARRIVAL_HR_COMMON_GAP (shared with ACS's M5): the intrinsic rate is the GI rule's band midpoint; "
                        "the common drive has no arrival term for respiratory distress or hypoxaemia, so the sympathetic "
                        "share of the arrival tachycardia is not reproduced (reported, not absorbed)"},
        "rr": {"core": r["rr"], "authored": t["respiratory_rate"],
               "class": "EXPECTED_RESPIRATORY_FAMILY_EXTENSION: the common RR is the acid-base drive's (HCO3 22.8), "
                        "with no congestion, hypoxaemia or mechanics drive"},
        "consciousness_level": {"core": r["consciousness_level"], "authored": authored["consciousness_level"],
                                "class": "LEGACY_SPO2_LADDER_ARRIVAL_MISREAD: derive's ADOPTED absolute SpO2 ladder "
                                         "(87 / 80) reads 81 % as drowsy against the authored alert patient; "
                                         "ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY must resolve it at integration"}}
    return {"anchors": a.to_dict(), "classes": er.ARRIVAL_CLASSES, "channel_roles": er.CHANNEL_ROLES,
            "observation_layer": er.OBSERVATION_LAYER, "core": r, "authored": authored, "exact": exact,
            "mismatches": mismatches, "arrival_L_is_arrival_congestion": s.L == 0.0 and s.G == 0.0,
            "l_rev": a.reversible_lung_water, "pass": all(exact.values()) and s.L == 0.0 and a.reversible_lung_water == 0.0}


# P2P-1-3 / 4: the family writer ----------------------------------------------------------------------------------------------

def writer_semantics() -> dict:
    """The writer writes L only (AST), owns it, is a registered disease module; the treatment writes nothing."""
    path = CORE_DIR / "modules" / "pulmonary_edema.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    written = sorted({node.args[0].attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                      and getattr(node.func, "id", None) == "ChannelDelta" and node.args
                      and isinstance(node.args[0], ast.Attribute)})
    flows = any(isinstance(n, ast.Name) and n.id == "BloodFlow" for n in ast.walk(tree))
    settings = any(isinstance(n, ast.Name) and n.id == "SettingChange" for n in ast.walk(tree))
    demand = any(isinstance(n, ast.Name) and n.id == "DemandModifier" for n in ast.walk(tree))
    w = writer()
    out = {"channels_written": written, "blood_flows": flows, "settings": settings, "demand": demand,
           "authority": EdemaCongestion.lung_water_authority, "kind": w.source.kind.value,
           "registered": _REGISTRY.get(w.type_name) is EdemaCongestion,
           "treatment_writes": DecongestiveTreatment("tx", 1).contribute(
               dv.arrival_state(er.anchors(), profile()), 1, (), er.anchors(), profile()).deltas == (),
           "signal": EDEMA_DECONGESTION, "never_written": list(an.NEVER_WRITTEN)}
    out["pass"] = (written == ["L"] and not flows and not settings and not demand and out["authority"] is True
                   and out["kind"] == "disease_module" and out["registered"] and out["treatment_writes"])
    return out


# P2P-1-7: L -> G -> SpO2, untreated ------------------------------------------------------------------------------------------

def untreated() -> dict:
    a, prof = er.anchors(), profile()
    plain, _ = course((), anchors=a, prof=prof)
    out = {"no_writer": _rows(plain, a, prof), "region": {}}
    for rate in PROGRESSION:
        states, records = course((writer(rate),), anchors=a, prof=prof)
        series = [reading(s, a, prof) for s in states]
        out["region"][f"{rate:g}"] = {
            "at": _rows(states, a, prof),
            "directions": {"L_up": _nondecreasing([x["L"] for x in series]) and series[-1]["L"] > 0.0,
                           "G_up": _nondecreasing([x["G"] for x in series]) and series[-1]["G"] > 0.0,
                           "spo2_down": _nonincreasing([x["spo2"] for x in series]) and series[-1]["spo2"] < a.spo2,
                           "G_is_lung_share": all(abs(x["G"] - prof.lung_water_to_gas_exchange_gain * max(0.0, x["L"]))
                                                  < 1e-9 for x in series),
                           "V_P_untouched": all(s.V == p.V and s.P == p.P for s, p in zip(states, plain))},
            "common_overload_writes": sum(1 for r in records for d in r.deltas if d.source == dv.PRELOAD_CONGESTION),
            "family_L_sources": sorted({d.source.key for r in records for d in r.deltas if d.channel is Channel.L})}
    out["pass"] = all(all(v["directions"].values()) and v["common_overload_writes"] == 0
                      for v in out["region"].values())
    return out


# P2P-1-8: oxygen through the common FiO2 path --------------------------------------------------------------------------------

def oxygen() -> dict:
    a, prof = er.anchors(), profile()
    room, _ = course((writer(),), anchors=a, prof=prof)
    out = {"room_air": _rows(room, a, prof), "fio2": {}}
    by_fio2 = {0.21: [reading(s, a, prof)["spo2"] for s in room]}
    for f in FIO2:
        states, _ = course((writer(), Oxygen("edema-o2", 0, f)), anchors=a, prof=prof)
        out["fio2"][f"{f:g}"] = _rows(states, a, prof)
        by_fio2[f] = [reading(s, a, prof)["spo2"] for s in states]
    minutes = range(1, HORIZON + 1)
    monotone = all(_nondecreasing([by_fio2[f][m] for f in sorted(by_fio2)]) for m in minutes)
    # The attenuation is the common r's: the same FiO2 step gains less at a later (worse) G.
    gain_early = by_fio2[0.6][30] - by_fio2[0.21][30]
    gain_late = by_fio2[0.6][120] - by_fio2[0.21][120]
    out.update({"monotone_in_fio2": monotone, "gain_at_30": gain_early, "gain_at_120": gain_late,
                "attenuated_as_G_worsens": gain_late < gain_early, "family_oxygen_function": False,
                "representable": True})
    out["pass"] = monotone and gain_late < gain_early
    return out


# P2P-1-12: the authority ------------------------------------------------------------------------------------------------------

def authority() -> dict:
    """With the overload condition present: the family owner alone writes L (no common writes, L equals the writer-alone
    course); without the family writer the common overload congests; a second owner is refused; a zero-gain owner still
    suppresses the common writer (accepted)."""
    a = er.anchors(preload_fraction=OVERLOAD["preload_fraction"])
    prof = profile()
    start = dv.arrival_state(a, prof).evolve(P=OVERLOAD["P"])
    bag = replace(an._bag(), volume_ml=OVERLOAD["volume_ml"],
                  untimed_rate_ml_per_min=OVERLOAD["volume_ml"] / an.FLUID["duration_min"])
    owned, owned_records = course((bag, writer()), anchors=a, prof=prof, start=start)
    alone, _ = course((writer(),), anchors=a, prof=prof, start=start)
    common, common_records = course((bag,), anchors=a, prof=prof, start=start)
    zero, zero_records = course((bag, writer(0.0)), anchors=a, prof=prof, start=start)
    key = dv.PRELOAD_CONGESTION
    second = False
    try:
        step(dv.arrival_state(a, prof), (writer(), IschaemicCongestion("acs-congestion", 0.05)), a, prof)
    except ProvenanceError:
        second = True
    out = {"owned": {"common_writes": sum(1 for r in owned_records for d in r.deltas if d.source == key),
                     "L_end": owned[-1].L, "L_equals_writer_alone": [s.L for s in owned] == [s.L for s in alone],
                     "V_moved": owned[-1].V > owned[0].V},
           "common_only": {"common_writes": sum(1 for r in common_records for d in r.deltas if d.source == key),
                           "L_end": common[-1].L},
           "zero_gain_owner": {"common_writes": sum(1 for r in zero_records for d in r.deltas if d.source == key),
                               "L_end": zero[-1].L},
           "second_owner_refused": second}
    out["pass"] = (out["owned"]["common_writes"] == 0 and out["owned"]["L_equals_writer_alone"] and out["owned"]["V_moved"]
                   and out["common_only"]["common_writes"] > 0 and out["common_only"]["L_end"] > 0.0
                   and out["zero_gain_owner"]["common_writes"] == 0 and out["zero_gain_owner"]["L_end"] == 0.0
                   and second)
    return out


# P2P-1-13: decongestion -------------------------------------------------------------------------------------------------------

def decongestion() -> dict:
    """L_rev = 0: decongestion takes L back to the arrival congestion and no further; G and SpO2 come back to arrival
    and never better; V and P do not move because L improved. A scripted push below arrival earns no credit."""
    a, prof = er.anchors(), profile()
    w = writer(MID, DECONGESTION["per_min"])
    tx = DecongestiveTreatment("edema-decongestion", DECONGESTION["begins_at_minute"])
    states, _ = course((w, tx), 180, a, prof)
    untreated_states, _ = course((w,), 180, a, prof)
    series = [reading(s, a, prof) for s in states]
    after = series[DECONGESTION["begins_at_minute"]:]
    below, _ = course((Drift("edema-below", "L", 0, 60, -0.01),), 60, a, prof)
    out = {"at": _rows(states, a, prof, (0, 60, 90, 120, 150, 180)), "l_rev": a.reversible_lung_water,
           "L_min": min(s.L for s in states), "spo2_max": max(x["spo2"] for x in series),
           "improves_after_treatment": _nonincreasing([x["L"] for x in after]) and _nondecreasing([x["spo2"] for x in after]),
           "back_to_arrival": states[-1].L == 0.0 and states[-1].G == 0.0 and series[-1]["spo2"] == a.spo2,
           "never_below_arrival": min(s.L for s in states) >= 0.0 and max(x["spo2"] for x in series) <= a.spo2,
           "V_P_unchanged": all(s.V == u.V and s.P == u.P for s, u in zip(states, untreated_states)),
           "scripted_below_arrival": {"L": below[-1].L, "G": below[-1].G,
                                      "spo2": reading(below[-1], a, prof)["spo2"]}}
    out["no_below_arrival_credit"] = (out["scripted_below_arrival"]["G"] == 0.0
                                      and out["scripted_below_arrival"]["spo2"] == a.spo2)
    out["pass"] = (out["improves_after_treatment"] and out["back_to_arrival"] and out["never_below_arrival"]
                   and out["V_P_unchanged"] and out["no_below_arrival_credit"])
    return out


# P2P-1-14 / 15 / 9 / 10: HR, consciousness, respiration ------------------------------------------------------------------------

def heart_rate() -> dict:
    """L -> G -> SpO2 -> HR: the sign stays physiological (worse SpO2, higher HR; oxygen takes it back); nothing retuned."""
    a, prof = er.anchors(), profile()
    plain, _ = course((), anchors=a, prof=prof)
    worse, _ = course((writer(PROGRESSION[-1]),), anchors=a, prof=prof)
    o2, _ = course((writer(PROGRESSION[-1]), Oxygen("edema-o2", 0, FIO2[-1])), anchors=a, prof=prof)
    hr = {name: [reading(s, a, prof)["hr"] for s in states] for name, states in
          (("no_writer", plain), ("untreated", worse), ("oxygen", o2))}
    target = {name: dv.sympathetic_target(states[-1], a, prof) for name, states in
              (("no_writer", plain), ("untreated", worse), ("oxygen", o2))}
    out = {"hr_120": {k: v[-1] for k, v in hr.items()}, "target_120": target,
           "untreated_minus_no_writer": hr["untreated"][-1] - hr["no_writer"][-1],
           "oxygen_minus_untreated": hr["oxygen"][-1] - hr["untreated"][-1],
           "threshold": prof.hypoxaemia_threshold_spo2, "gains_untouched": True}
    out["pass"] = out["untreated_minus_no_writer"] >= 0.0 and out["oxygen_minus_untreated"] <= 0.0 and \
        target["untreated"] >= target["no_writer"] and target["oxygen"] <= target["untreated"]
    return out


CONSCIOUSNESS_GUARD = ("ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY: derive's ADOPTED SpO2 ladder (87 / 80) and P2L-2's "
                       "hypoxaemia signal must never both act in one candidate pathway; P2P-1 is shadow only and runs "
                       "derive's ladder alone (the P2L-2 candidate is not wired into derive); at runtime integration one "
                       "source remains (LEGACY_SPO2_CONSCIOUSNESS_LADDER_MUST_BE_DISABLED_ON_P2L2_INTEGRATION)")


def consciousness() -> dict:
    a, prof = er.anchors(), profile()
    worse, _ = course((writer(),), anchors=a, prof=prof)
    o2, _ = course((writer(), Oxygen("edema-o2", 0, FIO2[-1])), anchors=a, prof=prof)
    levels = {name: sorted({reading(s, a, prof)["consciousness_level"] for s in states})
              for name, states in (("untreated", worse), ("oxygen", o2))}
    reads_candidate = "encephalopathy" in (CORE_DIR / "derived.py").read_text(encoding="utf-8")
    return {"arrival_level_core": reading(dv.arrival_state(a, prof), a, prof)["consciousness_level"],
            "arrival_level_authored": a.consciousness_level, "levels": levels,
            "ladder": [list(x) for x in prof.oxygen_levels], "derive_reads_p2l2_candidate": reads_candidate,
            "guard": CONSCIOUSNESS_GUARD, "pass": not reads_candidate}


def respiration() -> dict:
    """The common RR / W against the authored distress: an expected respiratory extension, never silently added."""
    a, prof = er.anchors(), profile()
    t = er.truth()
    worse, _ = course((writer(PROGRESSION[-1]),), anchors=a, prof=prof)
    plain, _ = course((), anchors=a, prof=prof)
    rr = [reading(s, a, prof)["rr"] for s in worse]
    rr_plain = [reading(s, a, prof)["rr"] for s in plain]
    gap = t["respiratory_rate"] - rr[0]
    deferred = sorted(DEFERRED_ACTIONS[x] for x in t["definitive_actions"] if x in DEFERRED_ACTIONS)
    out = {"authored_rr": t["respiratory_rate"], "core_rr_arrival": rr[0], "gap": gap,
           "rr_follows_L_or_G": rr != rr_plain, "work_of_breathing": t["work_of_breathing"],
           "paco2": t["abg_paco2"], "ph": t["abg_ph"], "deferred_actions": deferred,
           "needs": ["congestion / hypoxaemia respiratory drive", "respiratory mechanics and work of breathing",
                     "respiratory-muscle oxygen demand", "NIV (EPAP, recruitment, afterload, preload)"],
           "classification": "EXPECTED_RESPIRATORY_FAMILY_EXTENSION"}
    out["extension_expected"] = gap > RR_GAP or bool(deferred)
    return out


# P2P-1-11: treatments ---------------------------------------------------------------------------------------------------------

def treatments() -> dict:
    """Each authored definitive action, mapped to a common target (computed where the core can say so)."""
    a, prof = er.anchors(), profile()
    has_diuresis = any("urine" in p.value or "diures" in p.value for p in BloodProcess)
    # Read from the integrator's own rule (no probe here writes T): a writer of T is refused while the tone response is on.
    t_writer_refused = "write T while the vascular-tone response is on" in _live("clinical_core/integration.py") \
        and prof.deficit_to_tone_gain > 0.0
    return {
        "authored": er.truth()["definitive_actions"],
        "map": {
            "oxygen": {"class": "COMMON_TARGET_EXISTS", "target": "FiO2 (interventions.oxygen.Oxygen)"},
            "nitroglycerin": {"class": "NEW_COMMON_MECHANISM_REQUIRED",
                              "target": "T / V: a writer of T is refused while the common tone response is on "
                                        "(the integrator's rule; the profile's tone response is on); venodilation has no blood process; its decongestive effect on L "
                                        "is the family's (FAMILY_WRITER_REQUIRED, via the decongestion signal)",
                              "t_writer_refused": t_writer_refused},
            "diuretic": {"class": "FAMILY_WRITER_REQUIRED + NEW_COMMON_MECHANISM_REQUIRED",
                         "target": "L through the family writer's decongestion (the signal); V outflow needs a renal "
                                   "plasma-loss blood process the core does not have",
                         "diuresis_blood_process": has_diuresis},
            "niv": {"class": "VNI_COMMON_EXTENSION_DEFERRED", "target": "W, G, afterload and preload (outside P2P-1)"}},
        "magnitudes": "UNSET: no treatment magnitude is calibrated, to legacy or otherwise",
        "pass": t_writer_refused and not has_diuresis}


# P2P-1-16: the legacy engine, read last ----------------------------------------------------------------------------------------

LEGACY_MINUTES = (0, 30, 60, 90, 120)


def legacy() -> dict:
    """The family engine's untreated course, read as LEGACY_REFERENCE_ONLY."""
    from . import legacy_adapter as la
    engine = la._engine()
    current = la.bank_case(er.CASE, family=er.FAMILY)
    engine._initialize(current)
    out = {}
    for minute in range(max(LEGACY_MINUTES) + 1):
        if minute in LEGACY_MINUTES:
            o = current.get("observable", {})
            out[str(minute)] = {k: o.get(k) for k in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "mental_status",
                                                      "work_of_breathing")}
        if minute < max(LEGACY_MINUTES):
            engine.advance_clinical_time(current, 1)
    return out


def legacy_comparison(untreated_out: dict, legacy_rows: dict) -> dict:
    core = untreated_out["region"][f"{MID:g}"]["at"]
    rows = {m: {"legacy": legacy_rows.get(m, {}), "core": {k: core[m][k] for k in ("spo2", "hr", "rr", "map",
                                                                                   "consciousness_level")}}
            for m in ("0", "60", "120")}
    classes = {
        "spo2_course": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both fall untreated; the size is the family span's "
                       "and the legacy drift's, neither authored",
        "rr_course": "EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy RR follows its lung index; the common RR has no "
                     "congestion or hypoxaemia drive (EXPECTED_RESPIRATORY_FAMILY_EXTENSION)",
        "hr_arrival": "EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy shows the authored HR; the core's is the common HR "
                      "physiology's at the GI-rule intrinsic rate (ARRIVAL_HR_COMMON_GAP, shared with ACS)",
        "consciousness": "POSSIBLE_COMMON_CORE_GAP: the legacy shows the authored alert patient at arrival and its own "
                         "ladder afterwards (obtunded from minute 30, SpO2 79); derive's absolute SpO2 ladder already "
                         "reads 81 % as drowsy at arrival (no arrival anchoring; ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY)",
        "niv_nitrate_diuretic": "EXPECTED_EXTENSION_NOT_YET_MODELED: legacy treatment effects (NIV recruitment, nitrate "
                                "pressure, delayed diuretic) are not migrated"}
    return {"rows": rows, "classes": classes,
            "possible_common_core_gap": [k for k, v in classes.items() if v.startswith("POSSIBLE_COMMON_CORE_GAP")],
            "used_for_parameters": False}


# P2P-1-17: GI and ACS unchanged ------------------------------------------------------------------------------------------------

def non_regression() -> dict:
    """With the edema writer inactive nothing common moves: P2O-1's frozen GI probe (O12) and ACS evaluation reproduce,
    and P2O-3's frozen authority probes (R7, R8) reproduce."""
    p2o1 = json.loads(go.RECORD.read_text(encoding="utf-8"))
    p2o3 = json.loads(lw.RECORD.read_text(encoding="utf-8"))
    r78 = go._plain(lw.probe_r7_r8())
    out = {"gi_o12": go._plain(go.probe_o12()) == p2o1["probes"]["O12"],
           "acs_evaluation": go._plain(go.acs_evaluation()) == p2o1["acs"],
           "acs_authority_r7": r78["R7"] == p2o3["probes"]["probes"]["R7"],
           "common_overload_r8": r78["R8"] == p2o3["probes"]["probes"]["R8"],
           "common_files_untouched": common_untouched()}
    out["pass"] = all(v for k, v in out.items() if k != "common_files_untouched") and all(
        out["common_files_untouched"].values())
    return out


# The closed packages' view: the files P2O-3 left, P2P-1's tuple entries undone (proven) -----------------------------------------

P2O3_HEAD = "4178a95"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/gas_exchange_architecture.py", '
                                     '"clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                        "clinical_core/lung_water_reference.py", '
                                     '"clinical_core/lung_water_reference_report.py",\n'
                                     '                        "clinical_core/edema_migration.py", '
                                     '"clinical_core/edema_migration_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/gas_exchange_architecture.py", '
                                     '"clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                        "clinical_core/lung_water_reference.py", '
                                     '"clinical_core/lung_water_reference_report.py")\n'
                                     '\n'),),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                      "clinical_core/lung_water_reference_report.py",\n'
                                     '                      "clinical_core/edema_migration_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                      "clinical_core/lung_water_reference_report.py")\n'
                                     '\n'),)}
CORE_AT_P2O3 = {'clinical_core/decision_pack.py': 'a176cb385e896bbc96c39e66f7e9b9c07bdcf25c491b82df71480f6162578d2d',
 'clinical_core/lactate_slice.py': '27fa0e3b3df18e796bd32ce311313c4569ca2a11df19b6df90c24462e85e35c1'}
# </reversal>
#: The common files P2P-1 never changes, at their P2O-3 bytes.
COMMON_AT_P2O3 = {'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/bands.py': '9facbd34dc643d45f7ad3d668619f344717824c921924247f65396fae6aa81bc',
 'clinical_core/collapse.py': '6076dd315f8bd335af8a425ac4d78e3bcbbd5f1198b45e511b4f122532d65fc9',
 'clinical_core/contracts_output.py': 'bc7371c7ccb57ea2f138a6bbc58c266851f6dbf0fbdb5eb2d625b1ea70ab3751',
 'clinical_core/derived.py': '99faa383feca1d78a129ddc0b7fcaacdcd8427a0f4514f62f118f9bcdbc92c08',
 'clinical_core/encephalopathy.py': '04aea64d6f2a23cf5a77a530114b3174eab9c9adc527708a97ac25f9c5ce3539',
 'clinical_core/gi_reference.py': 'ee3114ce9eeeb426a7b843943819aa88095b6cb09674e4c895c93a6ad1de0867',
 'clinical_core/integration.py': 'c725fbe8ab4daa69952dfd06a8f584e303ef6ff66bd67441deaa70e4cce887af',
 'clinical_core/interventions/__init__.py': 'd0dedb08f0d35bff6ba458af009b3a35f85018e9ea2a76373158d9c373551b79',
 'clinical_core/interventions/fluids.py': '7dc615d2eea80e3afdab0774bb1f234f7ea887be1654ae02e6ca312513fb9aef',
 'clinical_core/interventions/modifiers.py': '46c8970630a77960d7ba2e81023d31b96b2b08f611a87eae9f94cb85f1b1aa6a',
 'clinical_core/interventions/oxygen.py': 'd7bcc0393ed562d02d6070f09ab8d501c506e6931f5efd33b3492d7e34664095',
 'clinical_core/interventions/timing.py': '498493e6143d691d582b68f568491b9275eef49bb13bcf94e251f17aea49c6a1',
 'clinical_core/legacy_adapter.py': 'f8fafd17bcda03a4293e5717145c6f4672760a07d553c965fa7c2505b69ad115',
 'clinical_core/modules/__init__.py': '1cf73c2ddf4fe370c8d34fff2ea8132149c02239ee81f3329bd87cfec729f23d',
 'clinical_core/modules/acs_ischaemia.py': '3199b9173594aea07c905e55b46e8705621b5c9ed7e936987024aa2d2079993d',
 'clinical_core/modules/gi_haemorrhage.py': 'edb61d903bc9f4607c1d3b819f28ac065ba86656b75ba29c89d3a7c124777673',
 'clinical_core/modules/rhythm_events.py': '1036a2443e44fe5e2fde80736984b6828542b69454cc49a36e660ee8d436c86b',
 'clinical_core/provenance.py': '3e670fc4aebb296232e8418f448cb14f6da46c387d4af4fc2ae7b95ba1e328d8',
 'clinical_core/shadow.py': '66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35',
 'clinical_core/signals.py': 'f02f5494a8aac0361ace94a40e15a4df81970f456de7af0f6762a1196a27ee7f',
 'clinical_core/state.py': '141cd5a2aada89a58e7de9ee1436b2f52fd68141df132bcb26e934e6e9ddc7d1',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9'}


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2O3[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2O3.items()}


def p2o3_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2O-3 file plus P2P-1's declared tuple entries")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2o3_bytes(relative: str) -> bytes:
    return p2o3_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2o3_sources(sources: dict) -> dict:
    """A P2O-3 dependency map: P2P-1's files removed, each tuple file at its P2O-3 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2O3.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def p2o3_registry() -> dict:
    return {k: v for k, v in _REGISTRY.items() if k not in FAMILY_TYPES}


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2O-3's view reads the P2O-3 files (proven) and the registry as P2O-3
    left it (the edema family's types removed)."""
    patch.setattr(lw, "_live", p2o3_text)
    patch.setattr(lw, "_REGISTRY", p2o3_registry())


def upstream_unchanged() -> dict:
    text = json.dumps({"revision": lw.REVISION, "p2o1": hashlib.sha256(lw.P2O1_RECORD.read_bytes()).hexdigest(),
                       "design": lw.design(), "sources": p2o3_sources(bf.freeze_sources())}, sort_keys=True, default=str)
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2o3_freeze_digest": hashlib.sha256(text.encode("utf-8")).hexdigest() == P2O3_FREEZE_DIGEST,
            "p2o3_record": hashlib.sha256(lw.RECORD.read_bytes()).hexdigest() == P2O3_RECORD_SHA}


P2O3_FREEZE_DIGEST = "3ae766808ce23a0b166afc68f7f1d1165ff30a5a993f1274ccdd86bf9ac8244d"
P2O3_RECORD_SHA = "efc8882c5c8bf3d7c8d18e7f9b1d61f80e713d0fd1d2f2a0d1b7149587834f8b"


# P2P-1-18: the verdict (predeclared) -------------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "case truth sufficient (every item read)",
    "arrival exact where the core models it (SpO2, MAP, PaCO2; L = 0 is the arrival congestion; L_rev 0)",
    "family writer writes L only and owns it (no SpO2, G, DO2, RR or lactate scripting)",
    "L worsening -> G worsening -> SpO2 worsening (every progression rate)",
    "oxygen through the common FiO2 path (monotone, attenuated by the common r, no family function)",
    "decongestion back to arrival improves G and SpO2, none below arrival (L_rev 0), V and P unchanged",
    "authority: no double writing; common overload without the family; second owner refused",
    "HR sign physiological",
    "GI and ACS unchanged; no common file changed",
)
VERDICTS = {"A": "PULMONARY_EDEMA_MIGRATES_WITH_FAMILY_L_WRITER",
            "B": "PULMONARY_EDEMA_NEEDS_EXPECTED_RESPIRATORY_EXTENSION",
            "C": "COMMON_L_TO_G_PATH_INSUFFICIENT", "D": "TRUE_CROSS_FAMILY_CONFLICT", "E": "INSUFFICIENT_CASE_TRUTH"}
VERDICT_RULE = ("Predeclared. E if the case truth is insufficient; D if the authority or the GI / ACS non-regression "
                "fails; C if the writer, the L -> G -> SpO2 direction, oxygen or decongestion fails; otherwise B when an "
                "expected respiratory extension is required (authored RR above the common arrival RR by more than "
                "RR_GAP, or a definitive action needing a deferred common extension), else A")
RECOMMENDATIONS = {"A": "PROCEED_TO_NEXT_FAMILY_OR_TREATMENT_EXTENSION",
                   "B": "IMPLEMENT_ONLY_THE_MINIMUM_RESPIRATORY_EXTENSION_REQUIRED"}


def verdict(found: dict) -> dict:
    criteria = dict(zip(VERDICT_CRITERIA, (
        found["case"]["available"], found["arrival"]["pass"], found["writer"]["pass"], found["untreated"]["pass"],
        found["oxygen"]["pass"], found["decongestion"]["pass"], found["authority"]["pass"], found["heart_rate"]["pass"],
        found["non_regression"]["pass"] and all(found["proof"]["proofs"].values()))))
    if not criteria[VERDICT_CRITERIA[0]]:
        letter = "E"
    elif not (criteria[VERDICT_CRITERIA[6]] and criteria[VERDICT_CRITERIA[8]]):
        letter = "D"
    elif not all(criteria[VERDICT_CRITERIA[i]] for i in (2, 3, 4, 5)):
        letter = "C"
    elif found["respiration"]["extension_expected"]:
        letter = "B"
    else:
        letter = "A"
    return {"criteria": criteria, "letter": letter, "verdict": VERDICTS[letter],
            "architecture_successful": letter in ("A", "B"), "recommendation": RECOMMENDATIONS.get(letter)}


# Freeze and record -------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "case": er.CASE, "selection_rule": er.SELECTION_RULE,
            "truth_paths": {k: list(v) for k, v in er.TRUTH_PATHS.items()}, "truth_classes": TRUTH_CLASSES,
            "arrival_classes": er.ARRIVAL_CLASSES, "channel_roles": er.CHANNEL_ROLES,
            "observation_layer": er.OBSERVATION_LAYER, "progression": list(PROGRESSION), "decongestion": DECONGESTION,
            "horizon": HORIZON, "read": list(READ), "fio2": list(FIO2), "overload": OVERLOAD, "rr_gap": RR_GAP,
            "deferred_actions": DEFERRED_ACTIONS, "l_rev": L_REV, "consciousness_guard": CONSCIOUSNESS_GUARD,
            "legacy_constants": LEGACY_CONSTANTS, "later_observations": LATER_OBSERVATIONS,
            "legacy_minutes": list(LEGACY_MINUTES), "verdict_criteria": list(VERDICT_CRITERIA), "verdicts": VERDICTS,
            "verdict_rule": VERDICT_RULE, "recommendations": RECOMMENDATIONS, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}, "family_types": list(FAMILY_TYPES),
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2o3": CORE_AT_P2O3,
            "common_at_p2o3": COMMON_AT_P2O3,
            "p2o3": {"head": P2O3_HEAD, "freeze_digest": P2O3_FREEZE_DIGEST, "record": P2O3_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2o3": hashlib.sha256(lw.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "case": case(), "arrival": arrival(), "writer": writer_semantics(),
             "untreated": untreated(), "oxygen": oxygen(), "authority": authority(), "decongestion": decongestion(),
             "heart_rate": heart_rate(), "consciousness": consciousness(), "respiration": respiration(),
             "treatments": treatments(), "non_regression": non_regression()}
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
