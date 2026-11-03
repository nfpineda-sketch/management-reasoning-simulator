"""P2O-3: lung-water reversibility (L_rev) and congestion-writer authority, shadow only.

    python -m clinical_core.lung_water_reference [--digest] [--out <json>]

A small structural package on the accepted P2O-2 decision B (congestion generation stays a family writer):

- authority: a family writer of lung water L may declare ``lung_water_authority``; while one is present the core's
  common overload coupling (``congestion_rate``) adds nothing, so L has one generator, never two. The common mechanism
  is kept for a future transfusion / volume-overload family (R8);
- L_rev: ``Anchors.reversible_lung_water``, a case / family reference parameter <= 0 (default 0) bounding how far below
  arrival lung water credits gas exchange: L -> G reads max(L_rev, L) in place of max(0, L);
- negative G: SpO2 credits G below arrival only down to the lung-water path's own share below arrival
  (``lung_water_gas_credit``), so writers of G directly inherit nothing (DIRECT_G_REVERSIBILITY_DEFERRED).

With L_rev = 0 and no owning writer, the core is P2O-1's exactly (R1). Every probe value here is SYNTHETIC_ONLY; no
value is approved, nothing is calibrated, no family is migrated. The live core files are proven to be the P2O-1 files
plus exactly the declared replacements (``REVERSAL``), byte for byte; the closed packages read the P2O-1 view.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

from . import acs_migration as an
from . import acs_reference as ar
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import gas_exchange_architecture as go
from .bands import ARRIVAL, Drift
from .integration import _REGISTRY, CHANNEL_BOUNDS, step
from .modules.acs_ischaemia import IschaemicCongestion
from .provenance import ProvenanceError, SourceKind
from .state import Anchors, Channel, UnresolvedBoundary

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2O-3"
OWN = ("clinical_core/lung_water_reference.py",)
REPORT = "clinical_core/lung_water_reference_report.py"
RECORD = ROOT / "docs" / "revision" / "P2O3_lung_water_reference.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2O3_REVERSIBILIDAD_L_Y_AUTORIDAD.md"
#: The tuples P2O-3 extended (its own files are downstream of every numerical artifact).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
#: P2O-3's candidate input of the anchors, outside the case-parameter / migration registry (as P2K-2's).
CANDIDATE_INPUTS = ("reversible_lung_water",)


# P2O-3-0: what the faculty decided (fixed) --------------------------------------------------------------------------------------

DECIDED = {
    "B": "CONGESTION_GENERATION_REMAINS_FAMILY_WRITER (P2O-2, accepted): no universal P-down -> L-up rule, because P has "
         "no side",
    "FILLING_PRESSURE": "NEW_COMMON_FILLING_PRESSURE_STATE_DEFERRED: no LA, PCWP, LVEDP, venous or hydrostatic pressure "
                        "is added",
    "V": "V is effective circulating volume / the preload coordinate, never left filling pressure: on the ACS arrival "
         "the IVC / preload evidence informs V; B-lines never do (they and pulmonary congestion inform L)",
    "AUTHORITY": "FAMILY_CONGESTION_WRITER_OVERRIDES_COMMON_OVERLOAD_WRITER: with an authoritative family L writer the "
                 "common overload coupling adds no second contribution; the common mechanism is not deleted (a future "
                 "TACO / volume-overload family)",
    "L": "L stays arrival-relative: L = 0 is the patient's arrival congestion, not normal dry lungs; never converted to "
         "an absolute",
    "L_REV": "L_rev: per case / per family, the reversible lower bound of L, <= 0, default 0; a CASE/FAMILY REFERENCE "
             "PARAMETER with no numerical value approved; the default reproduces P2O-1 exactly",
    "DIRECT_G": "DIRECT_G_REVERSIBILITY_DEFERRED: writers of G directly (pneumonia, PE) do not inherit L_rev",
}


# P2O-3-1: how L's mutation composes ---------------------------------------------------------------------------------------------

COMPOSITION = {
    "rule": "ADDS",
    "how": "integration.step gathers every delta of the minute in one list (the core's PRELOAD_CONGESTION and "
           "LUNG_WATER_CLEARANCE first, then each contributor's, in (kind, id) order); a channel's change is the "
           "math.fsum of its deltas, then CHANNEL_BOUNDS holds it (a recorded CLAMP). No writer overwrites, maxes or "
           "sequences another: the order changes the record, never the sum",
    "before_p2o3": "a family L writer and the common overload coupling both added in the same minute: P2O-2's latent "
                   "double count above the knee",
    "clearance": "LUNG_WATER_CLEARANCE removes L above arrival (-max(0, L) x (1 - e^(-1/tau))); it is no generator and "
                 "stays common under the authority",
}

AUTHORITY = {
    "declaration": "Contributor.lung_water_authority, a ClassVar, False by default; only a DISEASE_MODULE may set it "
                   "(integration._ordered refuses any other kind, any value but True or False, a value that differs "
                   "from its registered type's, and a second owner in the same run)",
    "effect": "while any present contributor declares it, step adds no PRELOAD_CONGESTION delta: congestion = 0.0 in "
              "place of congestion_rate(...)",
    "scope": "the run, by presence, not the minute: a family writer silent in a minute (P back at 1) still owns L, so "
             "the overload coupling never returns mid-course",
    "unchanged": "LUNG_WATER_CLEARANCE, every reader of L (the clearance, L -> G, the contracts export), L -> G and "
                 "G -> SpO2 stay active; any other writer of L (a scripted probe) still adds",
    "trace": "no new record field: the authority is a ClassVar of the contributor's registered type, so a replay from "
             "the run's spec reproduces it (a differing instance is refused); an owned minute's record simply carries "
             "no PRELOAD_CONGESTION delta",
    "one_owner": "at most one owner per run: a second is refused (one generator of L, never two); whether two families "
                 "may ever co-own L is a faculty decision",
    "volume": "under the authority the family's L no longer answers to volume through the core (the ACS writer has no V "
              "term): an owner with a zero gain suppresses every generation of L; a faculty decision, not a defect",
    "family": "acs_ischaemic_congestion (IschaemicCongestion) is the only writer that declares it",
}

L_REV = {
    "field": "Anchors.reversible_lung_water: a P2O-3 candidate input of the physiological-reference layer, outside the "
             "case-parameter / migration registry like P2K-2's until the faculty adopts L -> G",
    "class": "CASE/FAMILY REFERENCE PARAMETER",
    "domain": "finite and <= 0 (Anchors refuses a positive value); default 0",
    "values": "UNSET: no value but the default 0 is approved; the probe values are SYNTHETIC_ONLY",
    "readers": "the L -> G coupling (max(L_rev, L)) and the credit bound lung_water_gas_credit; no other consumer of L",
    "no_floor_on_L": "L has no floor at L_rev: its writers and its guard [-10, 10] act as before",
    "default": "with L_rev = 0, max(L_rev, L) = max(0, L) and the credit is 0: P2O-1 exactly (R1)",
}
L_TO_G = ("dG = k x (max(L_rev, L after) - max(L_rev, L before)); summed from arrival, G from L = k x max(L_rev, L): "
          "continuous, never decreasing in L, 0 at arrival, k x L_rev at most below it")

G_SIGN = {
    "before": "P2O-1 read max(0, G): any G below arrival counted as arrival, whoever wrote it",
    "form": "SpO2 = min(100, max(0, A - s x max(c, G) + 30 x (benefit(F) x retained(G) - benefit(F_a)))), with "
            "c = lung_water_gas_credit = k x min(0, max(L_rev, L)) <= 0 and retained(G) = 1 / (1 + r x max(0, G))",
    "proof": (
        "G = 0: max(c, 0) = 0 for every c <= 0 and retained(0) = 1, so SpO2 is the arrival value exactly, whatever "
        "L_rev",
        "monotone in G: max(c, G) never falls as G rises and retained never rises, with benefit >= 0, so SpO2 never "
        "rises with G; lowering G below 0 never worsens it",
        "bounded: the gain over G = 0 is s x (0 - max(c, G)) <= s x |c| <= s x k x |L_rev|, and min(100, .) caps it; "
        "with L_rev = 0 there is none",
        "FiO2: benefit(F) x retained(G) never falls as F rises (retained > 0); retained reads max(0, G), so the oxygen "
        "response is never better than at arrival",
        "direct G: c is the lung-water path's own share below arrival; G below c (a direct writer's negative G) earns "
        "nothing more, and with L >= 0 or L_rev = 0, c = 0: P2O-1's max(0, G)",
        "consistency: summed from arrival, lung water's share of G is k x max(L_rev, L); with L <= 0 that is c, so G "
        "written by lung water alone is credited exactly"),
    "reads_L": "c reads L (through _perfusion): at a fixed G, L moves SpO2 only where G < c <= 0, i.e. only to deny "
               "credit below arrival that lung water does not explain; at or above arrival c = 0. This holds for a run "
               "from arrival (G's lung share is then k x max(L_rev, L)) with G inside its guard: the core stops the run "
               "when the G guard acts while L_rev < 0; a run started away from arrival (L != 0 at G = 0) can credit a "
               "direct writer's G (a known limit, NON_ARRIVAL_START_CREDIT)",
}

DIRECT_G = ("DIRECT_G_REVERSIBILITY_DEFERRED: a writer of G directly (pneumonia, PE, anaphylaxis) has no reversible "
            "bound of its own; its G below arrival is not credited (c bounds the credit by lung water)")


# Probe constants (SYNTHETIC_ONLY) ---------------------------------------------------------------------------------------------

NEUTRAL = go.NEUTRAL
PROBE_LREV = (-0.5, -1.0)
L_GRID = (-3.0, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 3.0)
G_GRID = (-2.0, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0)
CREDITS = (0.0, -0.5, -1.0)
FIO2_GRID = (0.21, 0.3, 0.4, 0.6, 1.0)
DRIFT_MINUTES = 100
R_DRIFTS = {"R2": 0.02, "R3": -0.02, "R4": -0.005, "R5": -0.02}
#: R7 / R8: P2O-2's ACS scenario that reaches the knee (preload fraction 0.7 declared synthetic, 4000 mL, P = 0.7).
OVERLOAD = {"preload_fraction": 0.7, "volume_ml": 4000.0, "P": 0.7, "minutes": 120}
ACS_DECONGESTION = {"per_minute": -0.01, "minutes": 120, "L_rev": PROBE_LREV[0]}
RECOVERY = {"reperfusion": 60, "minutes": 360, "recovery": (0.5, 1.0)}
HYPOXAEMIC = dict(ARRIVAL, case_id="p2o3_hypoxaemic_arrival", spo2=90.0)
HR_PUMP = 0.7


def profile(**changes) -> dv.CoreProfile:
    """P2O-1's probe profile: the common reference with the gas-exchange reference (k 1, s 5, r 0.5), SYNTHETIC_ONLY."""
    return go.probe_profile(**changes)


def neutral(l_rev: float = 0.0) -> Anchors:
    return replace(NEUTRAL, reversible_lung_water=l_rev)


def _spo2(state, anchors, prof) -> float:
    return dv.derive(state, anchors, prof).spo2


def _p2o1_oxygenation(g: float, fio2: float, anchors: Anchors, prof: dv.CoreProfile) -> float:
    """P2O-1's oxygenation as frozen (max(0, G)), re-stated to compare."""
    retained = 1.0 / (1.0 + prof.oxygen_response_loss_per_gas_exchange_unit * max(0.0, g))
    oxygen = max(0.0, fio2 - prof.room_air_fio2) * retained - max(0.0, anchors.fio2 - prof.room_air_fio2)
    return min(100.0, max(0.0, anchors.spo2 - prof.spo2_per_gas_exchange_unit * max(0.0, g)
                          + prof.spo2_per_fio2 * oxygen))


@dataclass(frozen=True)
class NonOwningCongestion(IschaemicCongestion):
    """SYNTHETIC_ONLY: the ACS congestion writer without the authority, to show the composition before P2O-3 (its own
    type, never registered: a replay cannot turn it into the owner)."""

    type_name = "p2o3_probe_non_owning_congestion"
    lung_water_authority = False


@dataclass(frozen=True)
class ScriptedOwner(Drift):
    """SYNTHETIC_ONLY: a scripted event that claims the authority; the core refuses it."""

    type_name = "p2o3_probe_scripted_owner"
    lung_water_authority = True


@dataclass(frozen=True)
class UnregisteredClaim(IschaemicCongestion):
    """SYNTHETIC_ONLY: the ACS writer's registered type with the authority withdrawn; the core refuses it."""

    lung_water_authority = False


# P2O-3-5: probes R1-R8 --------------------------------------------------------------------------------------------------------

def _drift(per_minute: float):
    return (Drift("p2o3-l", "L", 0, DRIFT_MINUTES, per_minute),)


def _run(items, minutes, anchors, prof, start=None):
    return an.course(tuple(items), minutes, anchors, prof, start)


def _series(states, anchors, prof) -> dict:
    return {"L": [s.L for s in states], "G": [s.G for s in states], "spo2": [_spo2(s, anchors, prof) for s in states]}


def probe_r1() -> dict:
    """L = 0, L_rev = 0: P2O-1 identical. The functions equal P2O-1's on grids; P2O-1's frozen probe sections reproduce
    exactly on the live core; L = 0 reads arrival whatever L_rev."""
    prof = profile()
    k = prof.lung_water_to_gas_exchange_gain
    coupling = all(dv.lung_water_gas_exchange(b, a, prof) == dv.lung_water_gas_exchange(b, a, prof, 0.0)
                   == k * (max(0.0, a) - max(0.0, b)) for b in L_GRID for a in L_GRID)
    oxygen = all(dv.oxygenation(g, f, NEUTRAL, prof) == dv.oxygenation(g, f, NEUTRAL, prof, 0.0)
                 == _p2o1_oxygenation(g, f, NEUTRAL, prof) for g in G_GRID for f in FIO2_GRID)
    credit = all(dv.lung_water_gas_credit(l, neutral(), prof) == 0.0 for l in L_GRID)
    record = json.loads(go.RECORD.read_text(encoding="utf-8"))
    sections = {"probes": go.structural_probes, "cross_family": go.cross_family, "acs": go.acs_evaluation,
                "layers": go.layers}
    frozen = {name: go._plain(fn()) == record[name] for name, fn in sections.items()}
    arrival = {}
    for l_rev in (0.0,) + PROBE_LREV:
        a = neutral(l_rev)
        states, _ = _run((), 30, a, prof)
        arrival[str(l_rev)] = {s.G for s in states} == {0.0} and {_spo2(s, a, prof) for s in states} == {a.spo2}
    return {"coupling_equals_p2o1": coupling, "oxygenation_equals_p2o1": oxygen, "credit_zero_at_default": credit,
            "p2o1_sections_reproduced": frozen, "arrival_any_l_rev": arrival,
            "pass": coupling and oxygen and credit and all(frozen.values()) and all(arrival.values())}


def _r_course(name: str, l_rev: float) -> dict:
    prof, a = profile(), neutral(l_rev)
    states, _ = _run(_drift(R_DRIFTS[name]), DRIFT_MINUTES, a, prof)
    return {"l_rev": l_rev, **{k: v[-1] for k, v in _series(states, a, prof).items()}, "series": _series(states, a, prof)}


def probe_r2() -> dict:
    """L > 0 worsens G and SpO2, the same whatever L_rev (L_rev acts only below arrival)."""
    runs = {str(l_rev): _r_course("R2", l_rev) for l_rev in (0.0,) + PROBE_LREV}
    base = runs["0.0"]
    worse = base["G"] > 0.0 and base["spo2"] < NEUTRAL.spo2 and go._worse(base["series"]["spo2"])
    same = all(r["series"] == base["series"] for r in runs.values())
    return {"end": {k: {x: r[x] for x in ("L", "G", "spo2")} for k, r in runs.items()}, "worse": worse,
            "l_rev_irrelevant_above_arrival": same, "pass": worse and same}


def probe_r3() -> dict:
    """L < 0 with L_rev = 0: no credit (G and SpO2 stay at arrival)."""
    r = _r_course("R3", 0.0)
    ok = r["L"] < 0.0 and set(r["series"]["G"]) == {0.0} and set(r["series"]["spo2"]) == {NEUTRAL.spo2}
    return {"L": r["L"], "G": r["G"], "spo2": r["spo2"], "pass": ok}


def probe_r4() -> dict:
    """L < 0 above L_rev < 0: G = k x L below 0 and SpO2 improves, never falling while L falls."""
    prof = profile()
    r = _r_course("R4", PROBE_LREV[1])
    k, s = prof.lung_water_to_gas_exchange_gain, prof.spo2_per_gas_exchange_unit
    spo2 = r["series"]["spo2"]
    ok = (PROBE_LREV[1] < r["L"] < 0.0 and abs(r["G"] - k * r["L"]) < 1e-12 and r["spo2"] > NEUTRAL.spo2
          and all(b >= a for a, b in zip(spo2, spo2[1:])) and abs(r["spo2"] - min(100.0, NEUTRAL.spo2 - s * r["G"])) < 1e-9)
    return {"L": r["L"], "G": r["G"], "spo2": r["spo2"], "l_rev": PROBE_LREV[1], "pass": ok}


def probe_r5() -> dict:
    """L below L_rev: the credit stops at L_rev (G = k x L_rev, SpO2 constant once L passes it); L itself goes on."""
    prof = profile()
    r = _r_course("R5", PROBE_LREV[0])
    k, s = prof.lung_water_to_gas_exchange_gain, prof.spo2_per_gas_exchange_unit
    series = r["series"]
    past = [i for i, l in enumerate(series["L"]) if l <= PROBE_LREV[0]]
    capped = {round(series["G"][i], 12) for i in past} == {round(k * PROBE_LREV[0], 12)}
    ok = (r["L"] < PROBE_LREV[0] and capped and abs(r["spo2"] - min(100.0, NEUTRAL.spo2 - s * k * PROBE_LREV[0])) < 1e-9
          and len({round(series["spo2"][i], 9) for i in past}) == 1)
    return {"L": r["L"], "G": r["G"], "spo2": r["spo2"], "l_rev": PROBE_LREV[0], "cap_spo2": NEUTRAL.spo2
            - s * k * PROBE_LREV[0], "pass": ok}


def probe_r6() -> dict:
    """Raising FiO2 never worsens SpO2: at arrival, at G > 0 (R2), at credited G < 0 (R4) and at G below the credit."""
    prof = profile()
    points = {"arrival": (0.0, 0.0, 0.0), "R2": (1.0, 1.0, 0.0), "R4": (-0.5, -0.5, -1.0), "R5": (-2.0, -0.5, -0.5),
              "direct_G_below_credit": (0.0, -1.0, -1.0)}
    rows, ok = {}, True
    for name, (l, g, l_rev) in points.items():
        a = neutral(l_rev)
        state = dv.arrival_state(a, prof).evolve(L=l, G=g)
        values = [_spo2(state.evolve(fio2=f), a, prof) for f in FIO2_GRID]
        rows[name] = values
        ok = ok and all(b >= a_ for a_, b in zip(values, values[1:]))
    return {"fio2": list(FIO2_GRID), "spo2": rows, "pass": ok}


def _overload_course(items) -> tuple:
    a = ar.anchors(preload_fraction=OVERLOAD["preload_fraction"])
    prof = go.gas_profile(ar.common_profile())
    bag = replace(an._bag(), volume_ml=OVERLOAD["volume_ml"],
                  untimed_rate_ml_per_min=OVERLOAD["volume_ml"] / an.FLUID["duration_min"])
    start = dv.arrival_state(a, prof).evolve(P=OVERLOAD["P"])
    states, records = _run((bag,) + tuple(items), OVERLOAD["minutes"], a, prof, start)
    return states, records


def _l_sources(records) -> list:
    return sorted({d.source.key for r in records for d in r.deltas if d.channel is Channel.L})


def _both_in_one_minute(records, family_key: str) -> int:
    return sum(1 for r in records if {dv.PRELOAD_CONGESTION.key, family_key}
               <= {d.source.key for d in r.deltas if d.channel is Channel.L})


def probe_r7_r8() -> dict:
    """R7: an owning family writer and the overload condition: only the family (and the common clearance) moves L; L is
    the family-alone course's exactly. R8: without a family writer the common overload coupling still congests.
    Composition: a non-owning clone shows the pre-P2O-3 double write (ADDS)."""
    gain = an.writers()[1].lung_water_per_shortfall_per_min
    owner, clone = IschaemicCongestion("acs-congestion", gain), NonOwningCongestion("acs-congestion", gain)
    owned_states, owned = _overload_course((owner,))
    none_states, none = _overload_course(())
    clone_states, cloned = _overload_course((clone,))
    a = ar.anchors(preload_fraction=OVERLOAD["preload_fraction"])
    prof = go.gas_profile(ar.common_profile())
    alone, _ = _run((owner,), OVERLOAD["minutes"], a, prof, dv.arrival_state(a, prof).evolve(P=OVERLOAD["P"]))
    family_key, common_key = owner.source.key, dv.PRELOAD_CONGESTION.key
    r7 = {"L_sources": _l_sources(owned), "L_end": owned_states[-1].L, "G_end": owned_states[-1].G,
          "common_writes": sum(1 for r in owned for d in r.deltas if d.source.key == common_key),
          "L_equals_family_alone": [s.L for s in owned_states] == [s.L for s in alone],
          "V_moved": owned_states[-1].V > owned_states[0].V}
    r7["pass"] = (r7["common_writes"] == 0 and r7["L_equals_family_alone"] and r7["V_moved"]
                  and set(r7["L_sources"]) == {family_key, dv.LUNG_WATER_CLEARANCE.key})
    r8 = {"L_sources": _l_sources(none), "L_end": none_states[-1].L, "G_end": none_states[-1].G,
          "common_writes": sum(1 for r in none for d in r.deltas if d.source.key == common_key)}
    r8["pass"] = r8["common_writes"] > 0 and r8["L_end"] > 0.0 and r8["G_end"] > 0.0
    composition = {"rule": COMPOSITION["rule"], "minutes_with_both": _both_in_one_minute(cloned, family_key),
                   "L_end_non_owning": clone_states[-1].L, "L_end_owning": owned_states[-1].L,
                   "L_end_common_alone": none_states[-1].L}
    composition["adds"] = (composition["minutes_with_both"] > 0
                           and composition["L_end_non_owning"] > max(composition["L_end_owning"],
                                                                     composition["L_end_common_alone"]))
    return {"R7": r7, "R8": r8, "composition": composition}


def _refused(items, anchors=None, prof=None, error=ProvenanceError) -> bool:
    anchors = NEUTRAL if anchors is None else anchors
    prof = profile() if prof is None else prof
    try:
        step(dv.arrival_state(anchors, prof), tuple(items), anchors, prof)
    except error:
        return True
    return False


def authority_guard() -> dict:
    """Only the ACS congestion writer's registered type declares the authority; the core refuses the claim outside a
    disease module, a second owner, and an instance whose authority differs from its registered type's."""
    gain = an.writers()[1].lung_water_per_shortfall_per_min
    declaring = sorted(name for name, cls in _REGISTRY.items() if getattr(cls, "lung_water_authority", False) is not False)
    kinds = sorted({_REGISTRY[name].kind.value for name in declaring})
    out = {"declaring": declaring, "declaring_kinds": kinds,
           "refused_outside_disease_module": _refused((ScriptedOwner("p2o3-owner", "L", 0, 1, 0.0),)),
           "second_owner_refused": _refused((IschaemicCongestion("acs-congestion", gain),
                                             IschaemicCongestion("acs-congestion-2", gain))),
           "registry_mismatch_refused": _refused((UnregisteredClaim("acs-congestion", gain),)),
           "unregistered_probe_accepted": not _refused((NonOwningCongestion("acs-congestion", gain),))}
    out["pass"] = (declaring == ["acs_ischaemic_congestion"] and kinds == [SourceKind.DISEASE_MODULE.value]
                   and out["refused_outside_disease_module"] and out["second_owner_refused"]
                   and out["registry_mismatch_refused"] and out["unregistered_probe_accepted"])
    return out


def edges() -> dict:
    """The review's edges: the G guard stops the run while L_rev < 0 (and clamps as in P2O-1 at L_rev = 0); a minute
    crossing arrival is recorded as such; a run started away from arrival can credit a direct writer (a known limit);
    an owner with a zero gain suppresses every generation of L (a faculty decision)."""
    prof = profile()
    push = (Drift("p2o3-g-up", "G", 0, 20, 0.6),)
    stops = False
    try:
        _run(push, 20, neutral(PROBE_LREV[0]), prof)
    except UnresolvedBoundary:
        stops = True
    states, records = _run(push, 20, neutral(), prof)
    clamps_at_default = any(d.source.kind is SourceKind.CLAMP and d.channel is Channel.G for r in records
                            for d in r.deltas) and states[-1].G == CHANNEL_BOUNDS[Channel.G][1]
    labels = {}
    for l_rev in (0.0, PROBE_LREV[0]):
        a = neutral(l_rev)
        start = dv.arrival_state(a, prof).evolve(L=0.1, G=prof.lung_water_to_gas_exchange_gain * 0.1)
        _, record = step(start, (Drift("p2o3-cross", "L", 0, 1, -0.3),), a, prof)
        labels[str(l_rev)] = [d.description for d in record.deltas if d.source == dv.LUNG_WATER_GAS_EXCHANGE]
    a = neutral(PROBE_LREV[0])
    start = dv.arrival_state(a, prof).evolve(L=PROBE_LREV[0])
    away, _ = _run((Drift("p2o3-g-down", "G", 0, 25, -0.02),), 25, a, prof, start)
    gain = an.writers()[1].lung_water_per_shortfall_per_min
    zero_owner, _ = _overload_course((IschaemicCongestion("acs-congestion", 0.0),))
    common, _ = _overload_course(())
    out = {"g_guard_stops_with_l_rev": stops, "g_guard_clamps_at_default": clamps_at_default,
           "labels": labels, "across_label": any("across arrival" in n for n in labels[str(PROBE_LREV[0])])
           and not any("across arrival" in n for n in labels["0.0"]),
           "non_arrival_start_credit": {"G": away[-1].G, "spo2": _spo2(away[-1], a, prof), "arrival_spo2": a.spo2},
           "zero_gain_owner": {"L_end": zero_owner[-1].L, "L_end_common_alone": common[-1].L, "gain_reference": gain}}
    out["pass"] = out["g_guard_stops_with_l_rev"] and out["g_guard_clamps_at_default"] and out["across_label"]
    return out


def g_sign() -> dict:
    """The audit of G's sign on grids: G = 0 exact, monotone in G and FiO2, bounded improvement, direct G uncredited."""
    prof = profile()
    s = prof.spo2_per_gas_exchange_unit
    at_zero = all(dv.oxygenation(0.0, f, NEUTRAL, prof, c) == dv.oxygenation(0.0, f, NEUTRAL, prof)
                  for f in FIO2_GRID for c in CREDITS)
    exact = dv.oxygenation(0.0, NEUTRAL.fio2, NEUTRAL, prof, -1.0) == NEUTRAL.spo2
    monotone_g, monotone_f, bounded, uncredited = True, True, True, True
    for c in CREDITS:
        for f in FIO2_GRID:
            values = [dv.oxygenation(g, f, NEUTRAL, prof, c) for g in G_GRID]
            monotone_g &= all(b <= a for a, b in zip(values, values[1:]))
            ref = dv.oxygenation(0.0, f, NEUTRAL, prof, c)
            bounded &= all(v <= min(100.0, ref + s * abs(c)) + 1e-12 and 0.0 <= v <= 100.0 for v in values)
            uncredited &= all(dv.oxygenation(g, f, NEUTRAL, prof, c) == dv.oxygenation(c, f, NEUTRAL, prof, c)
                              for g in G_GRID if g < c)
        for g in G_GRID:
            values = [dv.oxygenation(g, f, NEUTRAL, prof, c) for f in FIO2_GRID]
            monotone_f &= all(b >= a for a, b in zip(values, values[1:]))
    positive_refused = False
    try:
        dv.oxygenation(0.0, 0.21, NEUTRAL, prof, 0.1)
    except dv.CoreInvariantError:
        positive_refused = True
    ok = at_zero and exact and monotone_g and monotone_f and bounded and uncredited and positive_refused
    return {"g_zero_exact": at_zero and exact, "monotone_in_g": monotone_g, "monotone_in_fio2": monotone_f,
            "bounded": bounded, "below_credit_uncredited": uncredited, "positive_credit_refused": positive_refused,
            "verdict": "NEGATIVE_G_SUPPORTED_BOUNDED" if ok else "NEGATIVE_G_SUPPORT_REQUIRED", "pass": ok}


def direct_g() -> dict:
    """A writer of G directly, L at arrival, L_rev < 0: its negative G earns no credit (DIRECT_G_REVERSIBILITY_DEFERRED)."""
    prof, a = profile(), neutral(PROBE_LREV[1])
    states, _ = _run((Drift("p2o3-g", "G", 0, 50, -0.02),), 50, a, prof)
    end = states[-1]
    ok = end.G < -0.5 and end.L == 0.0 and {_spo2(s, a, prof) for s in states} == {a.spo2}
    return {"G": end.G, "L": end.L, "spo2": _spo2(end, a, prof), "pass": ok}


def probes() -> dict:
    owned = probe_r7_r8()
    out = {"R1": probe_r1(), "R2": probe_r2(), "R3": probe_r3(), "R4": probe_r4(), "R5": probe_r5(),
           "R6": probe_r6(), "R7": owned["R7"], "R8": owned["R8"]}
    return {"probes": out, "composition": owned["composition"], "authority": authority_guard(), "g_sign": g_sign(),
            "direct_g": direct_g(), "edges": edges(), "pass": {k: v["pass"] for k, v in out.items()}}


# P2O-3-6 / 7 / 8: the ACS arrival mapping, its decongestion and a partial recovery of P -------------------------------------

def acs_mapping() -> dict:
    """V from the IVC (preload_fraction), L from the congestion (B-lines): B-lines never reach preload_fraction."""
    a = ar.anchors()
    tree = ast.parse((CORE_DIR / "acs_reference.py").read_text(encoding="utf-8"))
    readers = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            text = ast.dump(node)
            readers[node.name] = {"lungs": "pocus_lungs" in text or "'lungs'" in text, "preload": "preload" in text}
    preload_class = ar.ARRIVAL_CLASSES["preload_fraction"]
    reserve_note = ar.bands()["pump_reserve"].rule
    derived_tree = ast.parse((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    reserve_readers = sorted(node.name for node in derived_tree.body if isinstance(node, ast.FunctionDef)
                             and any(isinstance(n, ast.Attribute) and n.attr == "pump_reserve"
                                     for n in ast.walk(node)))
    out = {"preload_fraction": a.preload_fraction, "preload_declared": "preload_fraction" in a.declared,
           "preload_class": preload_class, "ivc_informs_v": "IVC" in preload_class,
           "b_lines_not_in_v": "B-line" not in preload_class and not any(v["lungs"] and v["preload"]
                                                                          for v in readers.values()),
           "b_lines_inform_l": ar.OBSERVATION_LAYER["b_lines_congestion"].startswith("an observation of L"),
           "functions_reading_lungs": sorted(k for k, v in readers.items() if v["lungs"]),
           "l_rev_at_acs": a.reversible_lung_water,
           "pump_reserve_note_cites_b_lines": "B-lines" in reserve_note, "pump_reserve_readers": reserve_readers,
           "pump_reserve_inert_under_authority": reserve_readers == ["arrival_layers", "congestion_rate"]}
    out["pass"] = (out["preload_fraction"] is None and not out["preload_declared"] and out["ivc_informs_v"]
                   and out["b_lines_not_in_v"] and out["b_lines_inform_l"] and out["l_rev_at_acs"] == 0.0)
    return out


def acs_representation() -> dict:
    """Uncalibrated: arrival L = 0, congestion L > 0 (untreated), decongestion L < 0 down to L_rev (a scripted probe,
    not a diuretic), V unchanged by the decongestion."""
    prof = go.gas_profile(ar.common_profile())
    a = ar.anchors()
    arrival = dv.arrival_state(a, prof)
    untreated, _ = _run(an.writers(), an.HORIZON, a, prof)
    l_rev = ACS_DECONGESTION["L_rev"]
    ad = ar.anchors(reversible_lung_water=l_rev)
    probe = (Drift("p2o3-decongest", "L", 0, ACS_DECONGESTION["minutes"], ACS_DECONGESTION["per_minute"]),)
    decongested, _ = _run(probe, ACS_DECONGESTION["minutes"], ad, prof)
    reference, _ = _run((), ACS_DECONGESTION["minutes"], ad, prof)
    k, s = prof.lung_water_to_gas_exchange_gain, prof.spo2_per_gas_exchange_unit
    end = decongested[-1]
    out = {"arrival": {"L": arrival.L, "G": arrival.G, "spo2": _spo2(arrival, a, prof)},
           "congestion": {"L": untreated[-1].L, "G": untreated[-1].G, "spo2": _spo2(untreated[-1], a, prof)},
           "decongestion": {"L": end.L, "G": end.G, "spo2": _spo2(end, ad, prof), "l_rev": l_rev,
                            "cap": min(100.0, a.spo2 - s * k * l_rev)},
           "v_unchanged": [x.V for x in decongested] == [x.V for x in reference],
           "p_unchanged": [x.P for x in decongested] == [x.P for x in reference]}
    out["pass"] = (out["arrival"] == {"L": 0.0, "G": 0.0, "spo2": a.spo2} and out["congestion"]["L"] > 0.0
                   and out["congestion"]["spo2"] < a.spo2 and end.L < l_rev and abs(end.G - k * l_rev) < 1e-12
                   and abs(out["decongestion"]["spo2"] - out["decongestion"]["cap"]) < 1e-9
                   and out["v_unchanged"] and out["p_unchanged"])
    return out


def partial_recovery() -> dict:
    """A recovery of P never clears L at once: after reperfusion each minute's fall of L is at most the clearance's
    first-order share (the family writer only adds), so congestion persists (CONGESTION_CLEARANCE_KINETICS_UNSET)."""
    prof = go.gas_profile(ar.common_profile())
    a = ar.anchors()
    out = {}
    for recovery in RECOVERY["recovery"]:
        states, _ = _run(an.writers(recovery=recovery, reperfusion=RECOVERY["reperfusion"]), RECOVERY["minutes"], a,
                         prof)
        after = states[RECOVERY["reperfusion"]:]
        share = -math.expm1(-1.0 / prof.lung_water_clearance_tau_min)
        bounded = all(x.L - y.L <= max(0.0, x.L) * share + 1e-12 for x, y in zip(after, after[1:]))
        out[str(recovery)] = {"P_at_reperfusion": after[0].P, "P_end": states[-1].P, "L_at_reperfusion": after[0].L,
                              "L_peak": max(x.L for x in states), "L_end": states[-1].L,
                              "max_fall_per_min": max(x.L - y.L for x, y in zip(after, after[1:])),
                              "clearance_share": share, "fall_bounded_by_clearance": bounded,
                              "persists": states[-1].L > 0.0}
    out["pass"] = all(v["fall_bounded_by_clearance"] and v["persists"] for v in out.values() if isinstance(v, dict))
    return out


# P2O-3-10 / 11 / 12 / 13 / 14 ---------------------------------------------------------------------------------------------

def heart_rate_sign() -> dict:
    """G -> SpO2 -> HR stays valid: a credited G below arrival never raises the drive target (no sign error)."""
    prof = profile()
    threshold = prof.hypoxaemia_threshold_spo2
    rows = {}
    for name, base in (("neutral_97", NEUTRAL), ("hypoxaemic_90", Anchors(**HYPOXAEMIC))):
        a = replace(base, reversible_lung_water=PROBE_LREV[1])
        # A state with a positive drive (P = 0.7): the drive never falls below 0 (P2D-3), so a sign is read above it.
        state = dv.arrival_state(a, prof).evolve(P=HR_PUMP)
        improved = state.evolve(L=-0.5, G=-0.5)
        spo2 = _spo2(improved, a, prof)
        rows[name] = {"target_at_arrival_lungs": dv.sympathetic_target(state, a, prof),
                      "target_improved": dv.sympathetic_target(improved, a, prof), "spo2_improved": spo2,
                      "hypoxaemia_term": max(0.0, threshold - spo2) - max(0.0, threshold - a.spo2)}
    ok = (all(r["target_improved"] <= r["target_at_arrival_lungs"] and r["hypoxaemia_term"] <= 0.0
              for r in rows.values())
          and rows["hypoxaemic_90"]["target_improved"] < rows["hypoxaemic_90"]["target_at_arrival_lungs"]
          and rows["hypoxaemic_90"]["target_at_arrival_lungs"] > 0.0)
    return {"rows": rows, "pump": HR_PUMP, "threshold": threshold, "pass": ok}


CONSCIOUSNESS_GUARD = ("LEGACY_SPO2_CONSCIOUSNESS_LADDER_MUST_BE_DISABLED_ON_P2L2_INTEGRATION: derive keeps the "
                       "ADOPTED SpO2 ladder (87 / 80) that P2L-2's candidate does not read; when P2L-2 is integrated it "
                       "must be retired with the PAS ladder (CONSCIOUSNESS_SINGLE_SOURCE_GUARD). Runtime consciousness "
                       "is not touched here; a SpO2 above arrival can only keep or lower the ladder's level")
SUBTYPES = ("FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT: one G response (s, r) serves cardiogenic congestion, pneumonia, "
            "PE and anaphylaxis alike; splitting G into subtypes (shunt-like, V/Q, diffusion) is deferred")
DEBTS = {
    "TRANSFUSION_OR_VOLUME_OVERLOAD_CONGESTION": "TACO, volume overload and renal congestion: the common overload "
                                                 "coupling (KD-S4) stays available to a future family (R8); no family, "
                                                 "no calibration; its knee, gain and pump_reserve stay provisional and "
                                                 "its division by zero at the curve edge (P2O-2) a known debt",
    "CONGESTION_CLEARANCE_KINETICS_UNSET": "the clearance tau (240 min, P2D-6) is provisional; nothing pulls L below "
                                           "arrival back toward it; diuretic and NIV kinetics are not modelled",
    "DIRECT_G_REVERSIBILITY_DEFERRED": DIRECT_G,
    "L_REV_REGISTRY_ENTRY_DEFERRED": "L_rev is a candidate input outside CASE_PARAMETERS (no 'declared' source is "
                                     "enforced for it) until the faculty adopts L -> G, as P2K-2's inputs",
    "PUMP_RESERVE_INERT_UNDER_AUTHORITY": "pump_reserve is read only by the common overload coupling (and reported); "
                                          "under the ACS writer's authority it acts nowhere in ACS",
    "L_GUARD_REASON_TEXT_OUTDATED": "CHANNEL_BOUNDS[L]'s reason still says only the core writes L (ACS writes it since "
                                    "P2N-2), and G's still says no module writes G (TD-113 (11)); text only, unchanged",
    "G_GUARD_WITH_L_TO_G": "TD-113 (10), redeclared: with L_rev < 0 the core now stops the run when the G guard acts "
                           "(UnresolvedBoundary, as V and Hb); at L_rev = 0 the guard still holds G as in P2O-1 and can "
                           "part G from lung water (no credit is possible there)",
    "NON_ARRIVAL_START_CREDIT": "a run started away from arrival (L != 0 with G = 0) can credit a direct writer's G below "
                                "arrival, down to k x L_rev: the credit is read from L, not from the G lung water wrote",
    "OWNER_SUPPRESSES_VOLUME_RESPONSE": "under the authority the family's L no longer answers to volume through the core; "
                                        "an owner with a zero gain suppresses every generation of L (faculty decision)",
    "SINGLE_OWNER": "a second owner of L is refused; whether two families may co-own L is a faculty decision",
    "LEGACY_SPO2_CONSCIOUSNESS_LADDER_MUST_BE_DISABLED_ON_P2L2_INTEGRATION": CONSCIOUSNESS_GUARD,
    "FUTURE_GAS_EXCHANGE_SUBTYPE_REQUIREMENT": SUBTYPES,
}
PARAMETER_STATUS = {
    "lung_water_to_gas_exchange_gain": "k: UNSET (None by default); STRUCTURALLY_DEFINED / CLINICALLY_UNIDENTIFIED",
    "spo2_per_gas_exchange_unit": "s: UNSET (None by default); STRUCTURALLY_DEFINED / CLINICALLY_UNIDENTIFIED",
    "oxygen_response_loss_per_gas_exchange_unit": "r: UNSET (None by default); STRUCTURALLY_DEFINED / "
                                                  "CLINICALLY_UNIDENTIFIED",
    "reversible_lung_water": "L_rev: semantics approved (P2O-3); default 0; every other value UNSET",
    "lung_water_clearance_tau_min": "CONGESTION_CLEARANCE_KINETICS_UNSET (240 min, provisional, P2D-6)",
    "family_writer_rates": "IschaemicCongestion's gain (share 0.5 / 1 / 2 x congestion_per_excess_preload): "
                           "FAMILY_CANDIDATE, UNSET",
}


def parameters() -> dict:
    default = dv.DEFAULT_PROFILE
    unset = {name: getattr(default, name) is None for name in go.REFERENCE}
    out = {"k_s_r_unset": unset, "l_rev_default": Anchors(**ARRIVAL).reversible_lung_water,
           "l_rev_at_acs": ar.anchors().reversible_lung_water, "status": PARAMETER_STATUS}
    out["pass"] = all(unset.values()) and out["l_rev_default"] == 0.0 == out["l_rev_at_acs"]
    return out


def arrival_relative() -> dict:
    """L stays arrival-relative: arrival L = 0 whatever L_rev; the guard unchanged; a positive L_rev refused."""
    prof = profile()
    zero = all(dv.arrival_state(neutral(l), prof).L == 0.0 for l in (0.0,) + PROBE_LREV)
    refused = False
    try:
        neutral(0.1)
    except dv.CoreInvariantError:
        refused = True
    bounds = CHANNEL_BOUNDS[Channel.L][:2]
    return {"arrival_L_zero": zero, "guard": list(bounds), "positive_refused": refused,
            "pass": zero and tuple(bounds) == (-10.0, 10.0) and refused}


def boundaries() -> dict:
    """What P2O-3 lets read L_rev and L in the core, and that its core text names no disease."""
    text = _live("clinical_core/derived.py")
    tree = ast.parse(text)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    l_rev = sorted(n.name for n in functions if any(isinstance(x, ast.Attribute) and x.attr == "reversible_lung_water"
                                                    for x in ast.walk(n)))
    naming_l = sorted(n.name for n in functions if any(isinstance(x, ast.Attribute) and x.attr == "L"
                                                       and isinstance(x.value, ast.Name) for x in ast.walk(n)))
    inserted = "\n".join(live for relative in ("clinical_core/derived.py", "clinical_core/integration.py",
                                                "clinical_core/state.py") for live, _ in REVERSAL[relative])
    disease = go.disease_terms(inserted)
    out = {"derived_readers_of_l_rev": l_rev, "derived_readers_of_L": naming_l, "disease_terms_in_core": disease}
    out["pass"] = (l_rev == ["lung_water_gas_credit"] and naming_l == ["_perfusion", "lung_water_clearance"]
                   and not disease)
    return out


def gi() -> dict:
    """GI exactly unchanged: P2O-1's GI probe (O12) reproduces; no GI writer owns L; L_rev is 0 there."""
    record = json.loads(go.RECORD.read_text(encoding="utf-8"))
    o12 = go._plain(go.probe_o12()) == record["probes"]["O12"]
    owners = [d for d in authority_guard()["declaring"] if d != "acs_ischaemic_congestion"]
    return {"o12_reproduced": o12, "other_owners": owners, "pass": o12 and not owners}


# The P2O-3 proof: the live files are the P2O-1 files plus exactly the declared replacements ----------------------------------

P2O1_HEAD = "96b9d65"
P2O1_RECORD = go.RECORD
P2O1_RECORD_SHA = "3db6c7c6c6c13a4f9bf637047eefd929a2886a2e331433be9f2f4c9253247605"
P2O1_FREEZE_DIGEST = "22bb29b95714b28044c418cd8e4b5f0058d1f5065eafffc509e656ff8c6db733"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/acs_migration.py", '
                                     '"clinical_core/acs_migration_report.py",\n'
                                     '                        "clinical_core/gas_exchange_architecture.py", '
                                     '"clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                        "clinical_core/lung_water_reference.py", '
                                     '"clinical_core/lung_water_reference_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/acs_migration.py", '
                                     '"clinical_core/acs_migration_report.py",\n'
                                     '                        "clinical_core/gas_exchange_architecture.py", '
                                     '"clinical_core/gas_exchange_architecture_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('    if gas_exchange_active(profile):\n'
                               '        spo2 = oxygenation(state.G, state.fio2, anchors, profile, '
                               'lung_water_gas_credit(state.L, anchors, profile))\n'
                               '    delivery_rel = relative_delivery(output_rel, state.hb, spo2, anchors)\n',
                               '    if gas_exchange_active(profile):\n'
                               '        spo2 = oxygenation(state.G, state.fio2, anchors, profile)\n'
                               '    delivery_rel = relative_delivery(output_rel, state.hb, spo2, anchors)\n'),
                              ('\n'
                               'def lung_water_gas_exchange(before_l: float, after_l: float, profile: CoreProfile, '
                               'reversible: float = 0.0) -> float:\n'
                               '    """The change of G one minute\'s lung water makes (P2O-1, P2O-3): gain x '
                               '(max(L_rev, L after) - max(L_rev, L before)).\n'
                               '\n'
                               '    Summed from arrival (L = 0, G = 0) it is G_from_L = gain x max(L_rev, L): '
                               'continuous, never decreasing in L, zero at\n'
                               '    arrival, no threshold. It follows L both ways, so lung water clearing toward '
                               'arrival never worsens G. Lung water\n'
                               "    below arrival moves G below 0 only down to the case's reversible lung water "
                               'L_rev (``Anchors.reversible_lung_water``,\n'
                               "    <= 0): the arrival congestion's reversible share, which L, a deviation from "
                               'arrival, does not carry by itself (O1).\n'
                               "    With the default L_rev = 0 it is P2O-1's gain x max(0, L) exactly. L itself has "
                               'no floor at L_rev. Its dynamics are\n'
                               "    L's own (the writers, the clearance), with no second time constant. L reaches "
                               'nothing else through it: SpO2,\n'
                               '    delivery, D, lactate, RR, ventilation, consciousness and collapse see lung water '
                               'through G, and SpO2 also through\n'
                               '    the bound of the credit below arrival (``lung_water_gas_credit``), which only '
                               'ever denies credit."""\n'
                               '    return profile.lung_water_to_gas_exchange_gain * (max(reversible, after_l) - '
                               'max(reversible, before_l))\n'
                               '\n'
                               '\n'
                               'def lung_water_gas_credit(lung_water: float, anchors: Anchors, profile: CoreProfile) '
                               '-> float:\n'
                               '    """How far below arrival gas exchange G is credited (P2O-3): the lung-water '
                               "path's own share below arrival,\n"
                               '    gain x min(0, max(L_rev, L)), never above 0.\n'
                               '\n'
                               '    0 without the L -> G coupling, with the default L_rev = 0, or with L at or above '
                               'arrival: G below 0 then counts as\n'
                               '    arrival, as in P2O-1. A direct writer of G gets no credit below arrival from it: '
                               'only lung water below arrival,\n'
                               '    down to L_rev, is credited (direct G reversibility is deferred)."""\n'
                               '    if not lung_water_gas_exchange_active(profile):\n'
                               '        return 0.0\n'
                               '    return profile.lung_water_to_gas_exchange_gain * min(0.0, '
                               'max(anchors.reversible_lung_water, lung_water))\n'
                               '\n',
                               '\n'
                               'def lung_water_gas_exchange(before_l: float, after_l: float, profile: CoreProfile) '
                               '-> float:\n'
                               '    """The change of G one minute\'s lung water makes (P2O-1): gain x (max(0, L '
                               'after) - max(0, L before)).\n'
                               '\n'
                               '    Summed from arrival (L = 0, G = 0) it is G_from_L = gain x max(0, L): '
                               'continuous, never decreasing in L, zero at\n'
                               '    arrival, no threshold. It follows L both ways above arrival, so lung water '
                               'clearing back toward arrival never worsens\n'
                               '    G. Lung water below arrival moves no G: crediting it would need the arrival '
                               "congestion's share of the arrival\n"
                               '    impairment, which L, a deviation from arrival, does not carry (O1). Its dynamics '
                               "are L's own (the writers, the\n"
                               '    clearance), with no second time constant. L reaches nothing else through it: '
                               'SpO2, delivery, D, lactate, RR,\n'
                               '    ventilation, consciousness and collapse see lung water only through G."""\n'
                               '    return profile.lung_water_to_gas_exchange_gain * (max(0.0, after_l) - max(0.0, '
                               'before_l))\n'
                               '\n'),
                              ('\n'
                               'def oxygenation(gas_exchange: float, fio2: float, anchors: Anchors, profile: '
                               'CoreProfile, credit: float = 0.0) -> float:\n'
                               '    """SpO2 from gas exchange G and inspired oxygen (P2O-1, P2O-3), anchored to the '
                               'authored arrival:\n'
                               '\n'
                               '        SpO2 = arrival SpO2 - scale x max(credit, G) + spo2_per_fio2 x '
                               '(benefit(FiO2) x retained(G) - benefit(arrival FiO2))\n'
                               '\n'
                               '    with benefit(F) = max(0, F - room air) and credit <= 0 '
                               "(``lung_water_gas_credit``; 0 by default, P2O-1's max(0, G)).\n"
                               "    At G = 0 it is the core's SpO2 exactly; it never rises with G and never falls "
                               'with FiO2; above the authored arrival\n'
                               '    through FiO2, or by at most scale x |credit| for lung water below arrival, '
                               'always within [0, 100]. The oxygen response\n'
                               '    is never better than at arrival (retained reads max(0, G)). It reads no '
                               'ventilation, PaCO2, RR, acid burden, D or\n'
                               '    lactate: hypoventilation reaches PaCO2, never G (alveolar-gas hypoxaemia is not '
                               'modelled)."""\n'
                               '    if credit > 0.0:\n'
                               '        raise CoreInvariantError("the gas-exchange credit below arrival is never '
                               'positive (P2O-3)")\n'
                               '    oxygen = (max(0.0, fio2 - profile.room_air_fio2) * '
                               'oxygen_response_retained(gas_exchange, profile)\n'
                               '              - max(0.0, anchors.fio2 - profile.room_air_fio2))\n'
                               '    return min(100.0, max(0.0, anchors.spo2 - profile.spo2_per_gas_exchange_unit * '
                               'max(credit, gas_exchange)\n'
                               '                          + profile.spo2_per_fio2 * oxygen))\n',
                               '\n'
                               'def oxygenation(gas_exchange: float, fio2: float, anchors: Anchors, profile: '
                               'CoreProfile) -> float:\n'
                               '    """SpO2 from gas exchange G and inspired oxygen (P2O-1), anchored to the '
                               'authored arrival:\n'
                               '\n'
                               '        SpO2 = arrival SpO2 - scale x max(0, G) + spo2_per_fio2 x (benefit(FiO2) x '
                               'retained(G) - benefit(arrival FiO2))\n'
                               '\n'
                               "    with benefit(F) = max(0, F - room air). At G = 0 it is the core's SpO2 exactly; "
                               'it never rises with G and never falls\n'
                               '    with FiO2; above the authored arrival only through FiO2. It reads no L, '
                               'ventilation, PaCO2, RR, acid burden, D or\n'
                               '    lactate: hypoventilation reaches PaCO2, never G (alveolar-gas hypoxaemia is not '
                               'modelled)."""\n'
                               '    oxygen = (max(0.0, fio2 - profile.room_air_fio2) * '
                               'oxygen_response_retained(gas_exchange, profile)\n'
                               '              - max(0.0, anchors.fio2 - profile.room_air_fio2))\n'
                               '    return min(100.0, max(0.0, anchors.spo2 - profile.spo2_per_gas_exchange_unit * '
                               'max(0.0, gas_exchange)\n'
                               '                          + profile.spo2_per_fio2 * oxygen))\n')),
 'clinical_core/integration.py': (('    responds_to: ClassVar[frozenset[str]] = frozenset()\n'
                                   "    #: P2O-3: a family writer of lung water L that owns L's generation for the "
                                   "whole run. While one is present the core's\n"
                                   '    #: common overload coupling (``congestion_rate``) adds nothing: one '
                                   'generator of L, never two. Only a disease module\n'
                                   '    #: may declare it; the clearance and every reader of L stay common.\n'
                                   '    lung_water_authority: ClassVar[bool] = False\n'
                                   '\n',
                                   '    responds_to: ClassVar[frozenset[str]] = frozenset()\n\n'),
                                  ('            raise ProvenanceError(f"{item.source.key}: only the integrator '
                                   'writes {item.source.kind.value} changes")\n'
                                   '        if item.lung_water_authority is not False and (item.lung_water_authority '
                                   'is not True\n'
                                   '                                                       or item.source.kind is '
                                   'not SourceKind.DISEASE_MODULE):\n'
                                   '            raise ProvenanceError(f"{item.source.key}: only a disease module (a '
                                   'family writer) owns lung water (P2O-3)")\n'
                                   '        registered = _REGISTRY.get(item.type_name)\n'
                                   '        if registered is not None and registered.lung_water_authority is not '
                                   'item.lung_water_authority:\n'
                                   '            raise ProvenanceError(f"{item.source.key}: its authority over lung '
                                   'water differs from its registered type\'s, "\n'
                                   '                                  "so a replay would not reproduce it (P2O-3)")\n'
                                   '    ordered = tuple(sorted(contributors, key=lambda item: '
                                   '(item.source.kind.value, item.source.id)))\n',
                                   '            raise ProvenanceError(f"{item.source.key}: only the integrator '
                                   'writes {item.source.kind.value} changes")\n'
                                   '    ordered = tuple(sorted(contributors, key=lambda item: '
                                   '(item.source.kind.value, item.source.id)))\n'),
                                  ('        raise ProvenanceError("the core\'s own coupling is not a contributor")\n'
                                   '    owners = [item.source.key for item in ordered if item.lung_water_authority]\n'
                                   '    if len(owners) > 1:\n'
                                   '        raise ProvenanceError(f"more than one owner of lung water {owners}: one '
                                   'generator of L, never two (P2O-3)")\n'
                                   '    return ordered\n',
                                   '        raise ProvenanceError("the core\'s own coupling is not a contributor")\n'
                                   '    return ordered\n'),
                                  ('    deltas = []\n'
                                   '    # P2O-3: a family writer that owns lung water replaces the common overload '
                                   'coupling for the run (never both).\n'
                                   '    owned = any(contributor.lung_water_authority for contributor in ordered)\n'
                                   '    congestion = 0.0 if owned else congestion_rate(state, anchors, profile)\n'
                                   '    if congestion:\n',
                                   '    deltas = []\n'
                                   '    congestion = congestion_rate(state, anchors, profile)\n'
                                   '    if congestion:\n'),
                                  ("            # P2O-1: G follows the minute's bounded lung water (L precedes G "
                                   'here), recorded as a core coupling.\n'
                                   '            coupling = lung_water_gas_exchange(state.L, values[Channel.L.value], '
                                   'profile, anchors.reversible_lung_water)\n'
                                   '            if coupling:\n'
                                   '                low, high = sorted((state.L, values[Channel.L.value]))\n'
                                   '                deltas.append(ChannelDelta(Channel.G, coupling, '
                                   'LUNG_WATER_GAS_EXCHANGE, minute,\n'
                                   '                                           "gas exchange following lung water '
                                   'across arrival, down to L_rev (L -> G)"\n'
                                   '                                           if high > 0.0 and low < 0.0 and '
                                   'anchors.reversible_lung_water < 0.0 else\n'
                                   '                                           "gas exchange following lung water '
                                   'above arrival (L -> G)" if high > 0.0 else\n'
                                   '                                           "gas exchange following lung water '
                                   'below arrival, down to L_rev (L -> G)"))\n'
                                   '        proposed = before + math.fsum(delta.amount for delta in deltas if '
                                   'delta.channel is channel)\n',
                                   "            # P2O-1: G follows the minute's bounded lung water (L precedes G "
                                   'here), recorded as a core coupling.\n'
                                   '            coupling = lung_water_gas_exchange(state.L, values[Channel.L.value], '
                                   'profile)\n'
                                   '            if coupling:\n'
                                   '                deltas.append(ChannelDelta(Channel.G, coupling, '
                                   'LUNG_WATER_GAS_EXCHANGE, minute,\n'
                                   '                                           "gas exchange following lung water '
                                   'above arrival (L -> G)"))\n'
                                   '        proposed = before + math.fsum(delta.amount for delta in deltas if '
                                   'delta.channel is channel)\n'),
                                  ('        if bounded != proposed:\n'
                                   '            if channel is Channel.G and lung_water_gas_exchange_active(profile) '
                                   'and anchors.reversible_lung_water < 0.0:\n'
                                   '                # P2O-3: a held G would part G from lung water and let another '
                                   'writer take the credit below arrival.\n'
                                   '                raise UnresolvedBoundary(f"minute {minute}: G reaches its guard '
                                   '[{lower:g}, {upper:g}] while lung water "\n'
                                   '                                         "is credited below arrival (L_rev < 0); '
                                   'no rule for that boundary is decided")\n'
                                   '            if channel in BLOOD_CHANNELS and any(delta.channel is channel and '
                                   'delta.source.kind not in _OUTSIDE_BLOOD\n',
                                   '        if bounded != proposed:\n'
                                   '            if channel in BLOOD_CHANNELS and any(delta.channel is channel and '
                                   'delta.source.kind not in _OUTSIDE_BLOOD\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/acs_migration_report.py",\n'
                                     '                      "clinical_core/gas_exchange_architecture_report.py",\n'
                                     '                      "clinical_core/lung_water_reference_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/acs_migration_report.py",\n'
                                     '                      "clinical_core/gas_exchange_architecture_report.py")\n'
                                     '\n'),),
 'clinical_core/modules/acs_ischaemia.py': (("  water added per minute in proportion to the pump's shortfall below "
                                             'arrival (1 - P). It writes L only; the common\n'
                                             "  clearance (``derived.lung_water_clearance``) stays the core's. Since "
                                             'P2O-3 it owns L (``lung_water_authority``):\n'
                                             "  while it is present the core's common preload congestion "
                                             '(``derived.congestion_rate``) adds nothing (decision B:\n'
                                             '  congestion generation stays a family writer).\n'
                                             '- ``CoronaryReperfusion`` is the logistic process (a PCI completed at '
                                             'a declared minute): it publishes the signal and\n',
                                             "  water added per minute in proportion to the pump's shortfall below "
                                             'arrival (1 - P). It writes L only; the common\n'
                                             '  clearance (``derived.lung_water_clearance``) and the common preload '
                                             'congestion (``derived.congestion_rate``) stay\n'
                                             "  the core's. Whether a common P -> L coupling should exist is a "
                                             "pending common decision; this is the family's.\n"
                                             '- ``CoronaryReperfusion`` is the logistic process (a PCI completed at '
                                             'a declared minute): it publishes the signal and\n'),
                                            ('    type_name = "acs_ischaemic_congestion"\n'
                                             "    #: P2O-3: the family owns lung water; the core's common overload "
                                             'coupling adds nothing while this writer is present.\n'
                                             '    lung_water_authority = True\n'
                                             '\n',
                                             '    type_name = "acs_ischaemic_congestion"\n\n')),
 'clinical_core/state.py': (('    "physiological_reference": ("intrinsic_sinus_rate", "metabolic_demand_baseline", '
                             '"reference_preload_fraction",\n'
                             '                                "beta_blockade", "pump_reserve", '
                             '"intrinsic_respiratory_rate", "reversible_lung_water"),\n'
                             '    "arrival_dynamic_state": ("preload_fraction", "arrival_oxygen_debt", '
                             '"arrival_lactate_excess",\n',
                             '    "physiological_reference": ("intrinsic_sinus_rate", "metabolic_demand_baseline", '
                             '"reference_preload_fraction",\n'
                             '                                "beta_blockade", "pump_reserve", '
                             '"intrinsic_respiratory_rate"),\n'
                             '    "arrival_dynamic_state": ("preload_fraction", "arrival_oxygen_debt", '
                             '"arrival_lactate_excess",\n'),
                            ('    arrival_paco2: float | None = None\n'
                             '    # P2O-3 candidate input, read only by the lung-water coupling L -> G (off by '
                             'default) and outside the case-parameter /\n'
                             "    # migration registry until the faculty adopts that physiology, as P2K-2's: "
                             '``reversible_lung_water`` (L_rev) is how far\n'
                             "    # below arrival the case's lung water can reversibly go (L is arrival-relative, so "
                             'L_rev <= 0). Gas exchange is\n'
                             '    # credited for lung water below arrival only down to it; L itself has no floor '
                             'there. 0, the default, credits nothing\n'
                             '    # below arrival (P2O-1). No value other than 0 is approved: a case or family '
                             'reference, never inferred.\n'
                             '    reversible_lung_water: float = 0.0\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n',
                             '    arrival_paco2: float | None = None\n'
                             '    declared: FrozenRecord = field(default=EMPTY)\n'),
                            ('            raise CoreInvariantError("the reference preload fraction is strictly '
                             'between 0 and 1")\n'
                             '        if not self.reversible_lung_water <= 0.0:\n'
                             '            raise CoreInvariantError("the reversible lung water is at or below arrival '
                             '(L_rev <= 0, P2O-3)")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n',
                             '            raise CoreInvariantError("the reference preload fraction is strictly '
                             'between 0 and 1")\n'
                             '        for name in ("intrinsic_respiratory_rate", "arrival_bicarbonate", '
                             '"arrival_paco2"):\n'))}
CORE_AT_P2O1 = {'clinical_core/decision_pack.py': '199987b69b200fd1cef7a1275279e64da7b0e88e64ef2e8d2a2dcabd4db37ece',
 'clinical_core/derived.py': '6bc0d392df3a49c0c4251131a58292d45a12e0d509b0e77a0d51a0d1d8cbddb8',
 'clinical_core/integration.py': 'c5ad9593408a89df6b5f5d69a4a2730364e1238db2644b2239d1cf2187774e6b',
 'clinical_core/lactate_slice.py': '99ecea50b43fd031e79d094a3c4e0671577e1089f43a56fa57cc8ba1c66a783a',
 'clinical_core/modules/acs_ischaemia.py': '03b8acbf2007deead2d8318976b65da1ce519f2090f14b2bb6be7026131ee554',
 'clinical_core/state.py': '578d32abad60fcda31a4d3344532b709c8c8f8b71ea2f4bdb2f88c37265a6d13'}
# </reversal>


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
    """The file (live, or ``text``) is the P2O-1 file byte for byte once P2O-3's declared replacements are undone."""
    back, problems = _reverse(relative, _live(relative) if text is None else text)
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2O1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def p2o1_text(relative: str) -> str:
    """The file as P2O-1 left it (proven), or any other file as it is: the closed packages read this."""
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2O-1 file plus P2O-3's declared replacements")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2o1_bytes(relative: str) -> bytes:
    return p2o1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2o1_unchanged(pinned: dict) -> dict:
    return {relative: hashlib.sha256(p2o1_bytes(relative)).hexdigest() == sha for relative, sha in pinned.items()}


class P2O1Path(type(Path())):
    """A clinical_core path whose text is the P2O-1 file's for the files P2O-3 changed (proven)."""

    def read_text(self, *args, **kwargs):
        relative = self.relative_to(ROOT).as_posix()
        return p2o1_text(relative) if relative in REVERSAL else super().read_text(*args, **kwargs)

    def read_bytes(self):
        relative = self.relative_to(ROOT).as_posix()
        return p2o1_bytes(relative) if relative in REVERSAL else super().read_bytes()


def p2o1_sources(sources: dict) -> dict:
    """A P2O-1 dependency map: P2O-3's module removed, each changed file at its P2O-1 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2O1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2O-1's view of the P2N-2 core reads the P2O-1 files (proven), so every
    closed guard still reads the core it froze."""
    patch.setattr(go, "_live", p2o1_text)
    patch.setattr(go, "_functions", lambda relative: {n.name: n for n in ast.walk(ast.parse(p2o1_text(relative)))
                                                       if isinstance(n, ast.FunctionDef)})
    patch.setattr(go, "p2n2_bytes", lambda relative: go.p2n2_text(relative).encode("utf-8")
                  if relative in go.CORE_FILES else p2o1_bytes(relative))
    patch.setattr(go.P2N2Path, "read_text", lambda self, *args, **kwargs: go.p2n2_text(self.relative_to(ROOT).as_posix()))
    patch.setattr(go.P2N2Path, "read_bytes", lambda self: go.p2n2_bytes(self.relative_to(ROOT).as_posix()),
                  raising=False)


def upstream_unchanged() -> dict:
    """P2O-1's freeze digest reproduces through the P2O-1 view; its record is unchanged."""
    text = json.dumps({"revision": go.REVISION, "p2n2": hashlib.sha256(go.P2N2_RECORD.read_bytes()).hexdigest(),
                       "design": go.design(), "sources": p2o1_sources(bf.freeze_sources())}, sort_keys=True,
                      default=str)
    return {"proofs": proofs(), "p2o1_freeze_digest": hashlib.sha256(text.encode("utf-8")).hexdigest()
            == P2O1_FREEZE_DIGEST, "p2o1_record": hashlib.sha256(P2O1_RECORD.read_bytes()).hexdigest()
            == P2O1_RECORD_SHA}


# Verdict and recommendation (predeclared) -------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "L stays arrival-relative",
    "L_rev = 0 preserves P2O-1 (R1)",
    "below-arrival improvement representable (R4, R5)",
    "negative G coherent (G sign, R6, direct G uncredited)",
    "authority prevents double writing (R7, one owner)",
    "common overload available without authority (R8)",
    "ACS V and L stay separate",
    "GI unchanged",
    "no value approved",
)
RECOMMENDATION_RULE = ("Predeclared. With READY: MIGRATE_PULMONARY_EDEMA_SHADOW (a family writer of L under the "
                       "authority, on L_rev's approved semantics); it is recommended, never started here")


def verdict(found: dict, mapping: dict, representation: dict, relative: dict, params: dict, gi_: dict,
            proof: dict) -> dict:
    p = found["pass"]
    criteria = {
        VERDICT_CRITERIA[0]: relative["pass"],
        VERDICT_CRITERIA[1]: p["R1"] and p["R2"] and p["R3"] and all(proof["proofs"].values()),
        VERDICT_CRITERIA[2]: p["R4"] and p["R5"],
        VERDICT_CRITERIA[3]: found["g_sign"]["pass"] and p["R6"] and found["direct_g"]["pass"] and found["edges"]["pass"],
        VERDICT_CRITERIA[4]: p["R7"] and found["authority"]["pass"],
        VERDICT_CRITERIA[5]: p["R8"],
        VERDICT_CRITERIA[6]: mapping["pass"] and representation["pass"],
        VERDICT_CRITERIA[7]: gi_["pass"],
        VERDICT_CRITERIA[8]: params["pass"],
    }
    ready = all(criteria.values())
    failed = [k for k, v in criteria.items() if not v]
    return {"criteria": criteria, "verdict": "L_REFERENCE_AND_WRITER_AUTHORITY_READY" if ready
            else "L_REFERENCE_AND_WRITER_AUTHORITY_NOT_READY — " + "; ".join(failed)}


def recommendation(ready: bool) -> str | None:
    return "MIGRATE_PULMONARY_EDEMA_SHADOW" if ready else None


# Freeze and record -------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "composition": COMPOSITION, "authority": AUTHORITY,
            "l_rev": L_REV, "l_to_g": L_TO_G, "g_sign": G_SIGN, "direct_g": DIRECT_G,
            "candidate_inputs": list(CANDIDATE_INPUTS), "probe_l_rev": list(PROBE_LREV), "l_grid": list(L_GRID),
            "g_grid": list(G_GRID), "credits": list(CREDITS), "fio2_grid": list(FIO2_GRID),
            "drift_minutes": DRIFT_MINUTES, "r_drifts": R_DRIFTS, "overload": OVERLOAD,
            "acs_decongestion": ACS_DECONGESTION, "recovery": {k: list(v) if isinstance(v, tuple) else v
                                                               for k, v in RECOVERY.items()},
            "hypoxaemic": {k: v for k, v in HYPOXAEMIC.items() if k != "rhythm"}, "hr_pump": HR_PUMP,
            "consciousness_guard": CONSCIOUSNESS_GUARD, "subtypes": SUBTYPES, "debts": DEBTS,
            "parameter_status": PARAMETER_STATUS, "verdict_criteria": list(VERDICT_CRITERIA),
            "recommendation_rule": RECOMMENDATION_RULE, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2o1": CORE_AT_P2O1,
            "p2o1": {"head": P2O1_HEAD, "record": P2O1_RECORD_SHA, "freeze_digest": P2O1_FREEZE_DIGEST}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2o1": hashlib.sha256(P2O1_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    proof = upstream_unchanged()
    found = probes()
    mapping = acs_mapping()
    representation = acs_representation()
    recovery = partial_recovery()
    hr = heart_rate_sign()
    relative = arrival_relative()
    params = parameters()
    gi_ = gi()
    bounds = boundaries()
    judged = verdict(found, mapping, representation, relative, params, gi_, proof)
    ready = judged["verdict"] == "L_REFERENCE_AND_WRITER_AUTHORITY_READY"
    return go._plain({"freeze_digest": freeze_digest(), "revision": REVISION, "design": design(), "proof": proof,
                      "probes": found, "acs_mapping": mapping, "acs_representation": representation,
                      "partial_recovery": recovery, "heart_rate": hr, "arrival_relative": relative,
                      "parameters": params, "gi": gi_, "boundaries": bounds, "verdict": judged, "recommendation": recommendation(ready)})


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
