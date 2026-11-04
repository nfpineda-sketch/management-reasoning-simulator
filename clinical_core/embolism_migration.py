"""P2Q-2: pulmonary_embolism_61m (primary) and pulmonary_embolism_33f (secondary) migrated in shadow with family writers,
on the unchanged common core.

    python -m clinical_core.embolism_migration [--digest] [--out <json>]

A family migration, not a redesign. P2Q-1 found the conflict: on the unsided P a common overload rule cannot tell LV
from RV / obstructive failure, so a plethoric-IVC mapping plus volume made false left pulmonary edema. The faculty
resolved it for this migration by family authority: the PE family owns L with zero generation (P2O-3's authority; one
owner per run), V is read from the authored underfilled LV, never from the plethoric IVC, and no sided common state is
added. The family writers (``modules/pulmonary_embolism``) write the obstruction on the unsided P, the embolic gas
exchange on G directly, and own L; everything downstream (output, MAP, delivery, the deficit, D, lactate, HR, tone,
SpO2 and the FiO2 response, the respiratory drive, collapse) is common. Nothing is calibrated: the rates are sparse
spans fixed before any run on scales already frozen (the ACS writer's P loss, P2O-1's PE probe for G), the gas-exchange
and hypoxaemic-drive values are SYNTHETIC_ONLY, the collapse slots stay UNSET. The legacy engine is read last, as
reference only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
from dataclasses import fields, replace
from pathlib import Path

from . import acs_migration as an
from . import acs_reference as ar
from . import blood_fluid_calibration as bf
from . import collapse as cx
from . import derived as dv
from . import edema_migration as pe
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import lung_water_reference as lw
from . import respiratory_drive as rd
from .integration import _REGISTRY, step
from .interventions.fluids import Crystalloid
from .interventions.oxygen import Oxygen
from .modules.pulmonary_edema import EdemaCongestion
from .modules.pulmonary_embolism import EmbolicGasExchange, EmbolicLungWater, ObstructiveForwardFlow
from .provenance import ProvenanceError
from .state import Channel, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2Q-2"
OWN = ("clinical_core/embolism_reference.py", "clinical_core/modules/pulmonary_embolism.py",
       "clinical_core/embolism_migration.py")
REPORT = "clinical_core/embolism_migration_report.py"
RECORD = ROOT / "docs" / "revision" / "P2Q2_pulmonary_embolism.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2Q2_TEP_SOMBRA.md"
#: The tuples P2Q-2 extended (its analysis and report are downstream of every numerical artifact).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[2], REPORT)}
FAMILY_FILE = "clinical_core/modules/pulmonary_embolism.py"
#: The family's own types (registered by importing the module); the closed packages' registry view leaves them out.
FAMILY_TYPES = (ObstructiveForwardFlow.type_name, EmbolicGasExchange.type_name, EmbolicLungWater.type_name)


# The faculty's decisions (fixed) ---------------------------------------------------------------------------------------------

DECIDED = {
    "goal": "a family migration on the closed common core; generalization over case fitting; a family mapping is "
            "acceptable where the disease mechanism has information the common channels do not hold",
    "p2q1": "TRUE_CROSS_FAMILY_CONFLICT accepted for the current unsided common congestion coupling, resolved for this "
            "migration by family authority",
    "l_owner": "PE_L_ZERO_OWNER_AUTHORIZED: the PE family owns L (lung_water_authority) with zero intrinsic congestion "
               "generation unless a case independently authors pulmonary edema; it suppresses the provisional common "
               "overload writer; a family authority decision over the common L channel, not a derived equation",
    "one_owner": "one authoritative L owner per run (P2O-3); two independent owners are never composed; common "
                 "downstream L readers unchanged",
    "preload": "IVC_IS_NOT_UNIVERSAL_V_MAPPING: V (effective forward preload) from the authored small / underfilled LV; "
               "the plethoric IVC is RIGHT_SIDED / OBSERVATIONAL evidence, never common V",
    "no_sided_state": "SIDED_PRELOAD_COMMON_STATE_DEFERRED: no RV / LV preload, RA / LA pressure, PCWP, sided P or "
                      "sided V as common state",
    "no_double_count": "the obstruction is never encoded as low V and low P at once without independent authored "
                       "mechanisms",
    "g": "direct G, never through L; no L_rev semantics on direct G; the common G -> SpO2 -> DO2 path; no G subtype; no "
         "PE oxygen-response function",
    "drive": "P2P-2 exercised structurally: the hypoxaemic drive UNSET or SYNTHETIC_ONLY; no threshold, gain or curve "
             "from PE; no PE RR residual; central depression preserved; no opioid code",
    "tone_hr": "no pressure -> tone compensation and no HR retuning (P2J not reopened); the gaps are recorded",
    "d_lactate": "arrival D a latent case state constrained by the authored physiology, never from lactate; common D / "
                 "lactate kinetics not retuned; lactate never forced monotonic",
    "collapse": "P2M-2 exercised structurally; no thresholds; no arrest calibration",
}


# P2Q-2-1: the canonical cases and their truth --------------------------------------------------------------------------------

#: What each truth item is (AUTHORED_CASE_TRUTH, LEGACY_ENGINE_BEHAVIOR or MODEL_DERIVED).
TRUTH_CLASSES = {
    **{item: "AUTHORED_CASE_TRUTH" for item in mr.TRUTH_PATHS},
    "definitive_actions": "AUTHORED_CASE_TRUTH (faculty-declared definitive actions: anticoagulation, consult, oxygen)",
    "tdfc_f1_volume": "LEGACY_ENGINE_BEHAVIOR (tdfc_declarations F1: 'the engine punishes rapid volume (the dilated right "
                      "ventricle lowers the output) and tolerates slow, bounded volume'; pe_obstruction's RV strain)",
    "assessment_cautious_volume": "AUTHORED_CASE_TRUTH as an assessment expectation (case_assessment_bank: 'cautious "
                                  "volume with a stated limit'), never a physiological rate",
    "arrival_hr_prediction": "MODEL_DERIVED (derived.heart_rate_decomposition)",
    "arrival_rr": "MODEL_DERIVED (the P2P-2 composition on the arrival acid burden)",
    "arrival_delivery_and_debt": "MODEL_DERIVED latent arrival states (bands, FAMILY_CANDIDATE)",
}
LEGACY_CONSTANTS = ("pe_obstruction (TOLERATED_ML_PER_MIN 10, RV_STRAIN_PER_ML 0.0006, RV_STRAIN_TAU_MIN 45, "
                    "RV_STRAIN_LUNG_SHARE 0.35, lysis targets 0.62 / 0.80): LEGACY_ENGINE_BEHAVIOR")
LATER_OBSERVATIONS = ("NONE_AUTHORED: both cases state the arrival only; the TDFC declarations and the assessment bank "
                      "describe the expected management (oxygen, anticoagulation, a reperfusion-capable team, cautious "
                      "bounded volume), not a physiological course")


def case() -> dict:
    out = {"cases": {}, "selection_rule": mr.SELECTION_RULE, "source": "clinical_cases.py",
           "legacy_constants": LEGACY_CONSTANTS, "later_observations": LATER_OBSERVATIONS}
    for name in mr.CASES:
        t = mr.truth(name)
        out["cases"][name] = {"presentation": mr.bank_case(name)["presentation"], "truth": t,
                              "classes": {k: TRUTH_CLASSES[k] for k in t},
                              "missing": sorted(k for k, v in t.items() if v is None)}
    # Every item is authored for the primary; the secondary may lack none of the arrival items the mapping reads.
    out["available"] = all(not v["missing"] for v in out["cases"].values())
    return out


# The design (predeclared before any run) -------------------------------------------------------------------------------------

#: The obstruction's loss of P: the ACS ischaemic writer's frozen span on the same P channel (acs_migration.LOSS_PER_MIN,
#: its floor), one x2 step either side; never fitted (no course after arrival is authored) and never the legacy drift.
LOSS_PER_MIN = an.LOSS_PER_MIN
FLOOR = an.FLOOR
MID_LOSS = LOSS_PER_MIN[1]
#: Direct G: P2O-1's PE family probe rate (gas_exchange_architecture.FAMILIES, 0.025 per min) as the top, halved twice.
_G_TOP = next(rate for kind, channel, rate in go.FAMILIES["pulmonary_embolism"]["items"] if channel == "G")
G_RATES = (_G_TOP / 4.0, _G_TOP / 2.0, _G_TOP)
MID_G = G_RATES[1]
HORIZON = 120
LONG_HORIZON = 240
READ = (0, 30, 60, 90, 120)
LONG_READ = (0, 30, 60, 90, 120, 180, 240)
FIO2 = (0.4, 0.6)
#: A deliberately large synthetic bolus during the obstruction, SYNTHETIC_ONLY. It repeats the critical stress of the
#: P2Q-1 read-only audit (accepted by the faculty; that audit ran in memory and left no repository artifact, so the
#: values are declared afresh here, not read from it).
FLUID_STRESS = {"volume_ml": 2000.0, "begins_at_minute": 30, "duration_min": 30.0}
#: A plethoric-IVC arrival position (the mapping the faculty rejected, IVC_IS_NOT_UNIVERSAL_V_MAPPING): a counterfactual
#: only, SYNTHETIC_ONLY, the value the P2Q-1 audit used (declared afresh, as above).
REJECTED_IVC_PRELOAD = 0.8
#: A synthetic negative L_rev, only to show the direct G path never receives the lung-water credit.
L_REV_PROBE = -0.5
#: P2P-2's SYNTHETIC_ONLY hypoxaemic mapping and the gain its own probes use (SYNTHETIC_GAINS[1], the larger of its two);
#: the strong central depression of its probes.
HYPOXAEMIC_GAIN = rd.SYNTHETIC_GAINS[1]
DEPRESSION = rd.STRONG_DEPRESSION
#: The secondary case: the G writer alone, then with the lowest obstruction rate (never the primary's strength).
SECONDARY_LOSS = (0.0, LOSS_PER_MIN[0])
RR_GAP = pe.RR_GAP


def profile(**changes) -> dv.CoreProfile:
    """The ACS package's predeclared common point with P2O-1's SYNTHETIC_ONLY gas-exchange reference (k 1, s 5, r 0.5)."""
    return go.gas_profile(mr.common_profile(), **changes)


def hypoxaemic_profile(**changes) -> dv.CoreProfile:
    return profile(hypoxaemic_drive_mapping=rd.SYNTHETIC_MAPPING, hypoxaemic_to_drive_gain=HYPOXAEMIC_GAIN, **changes)


def obstruction(loss: float = MID_LOSS) -> ObstructiveForwardFlow:
    return ObstructiveForwardFlow("pe-obstruction", loss, FLOOR)


def gas(rate: float = MID_G) -> EmbolicGasExchange:
    return EmbolicGasExchange("pe-gas-exchange", rate)


def owner(name: str = mr.CASE) -> EmbolicLungWater:
    return EmbolicLungWater("pe-lung-water", mr.lung_water_generation(name))


def writers(loss: float = MID_LOSS, rate: float = MID_G, name: str = mr.CASE) -> tuple:
    out = [owner(name)]
    if loss > 0.0:
        out.append(obstruction(loss))
    if rate > 0.0:
        out.append(gas(rate))
    return tuple(out)


def bolus() -> Crystalloid:
    volume, minutes = FLUID_STRESS["volume_ml"], FLUID_STRESS["duration_min"]
    return Crystalloid("pe-fluid-stress", FLUID_STRESS["begins_at_minute"], volume, minutes, volume / minutes,
                       an.CRYSTALLOID["crystalloid_effective_ml_per_ml"], an.CRYSTALLOID["crystalloid_transient_share"],
                       an.CRYSTALLOID["crystalloid_leak_tau_min"])


def course(items, minutes: int = HORIZON, anchors=None, prof=None, start=None):
    anchors = mr.anchors() if anchors is None else anchors
    prof = profile() if prof is None else prof
    return an.course(tuple(items), minutes, anchors, prof, start)


def reading(state, anchors, prof) -> dict:
    d = dv.derive(state, anchors, prof)
    r = dv.respiration(state, anchors, prof)
    return {"minute": state.minute, "V": state.V, "T": state.T, "P": state.P, "L": state.L, "G": state.G, "D": state.D,
            "hb": state.hb, "fio2": state.fio2, "spo2": d.spo2, "output_rel": d.output_rel, "map": d.map, "sbp": d.sbp,
            "dbp": d.dbp, "delivery_index": dv.effective_delivery(d.delivery_rel, anchors),
            "deficit": dv.acute_deficit_signal(state, anchors, prof), "lactate": d.lactate, "hr": d.monitor_rate_bpm,
            "rr": r.respiratory_rate, "paco2": r.paco2, "ph": r.ph, "consciousness_level": d.consciousness_level,
            "preload_position": dv.preload_position(state, anchors, prof)}


def _rows(states, anchors, prof, minutes=READ) -> dict:
    return {str(m): reading(states[m], anchors, prof) for m in minutes if m < len(states)}


def _nonincreasing(values) -> bool:
    return all(b <= a + 1e-12 for a, b in zip(values, values[1:]))


def _nondecreasing(values) -> bool:
    return all(b >= a - 1e-12 for a, b in zip(values, values[1:]))


def _writes(records, channel: Channel | None = None, source=None) -> int:
    return sum(1 for r in records for d in r.deltas
               if (channel is None or d.channel is channel) and (source is None or d.source == source))


def _sources(records, channel: Channel) -> list:
    return sorted({d.source.key for r in records for d in r.deltas if d.channel is channel})


def _family(records) -> dict:
    channels, others = set(), 0
    for record in records:
        for delta in record.deltas:
            if delta.source.kind.value == "disease_module":
                channels.add(delta.channel.value)
        others += sum(1 for x in (record.transitions + record.settings + record.demand + record.blood)
                      if getattr(x, "source", None) is not None and x.source.kind.value == "disease_module")
        others += sum(1 for c in record.auxiliary if c.source.kind.value == "disease_module")
    return {"channels": sorted(channels), "other_writes": others}


# P2Q-2-2 / 15: the arrival -----------------------------------------------------------------------------------------------------

def arrival(name: str = mr.CASE) -> dict:
    a, prof = mr.anchors(name), profile()
    t = mr.truth(name)
    s = dv.arrival_state(a, prof)
    r = reading(s, a, prof)
    try:
        dv.check_arrival_reconstruction(a, prof)
        reconstruction = "exact (SBP, DBP, SpO2, CRT, lactate, consciousness level)"
    except CoreInvariantError as error:                                           # reported, never forced
        reconstruction = f"FAILED: {error}"
    authored = {"sbp": t["sbp"], "dbp": t["dbp"], "map": mr.authored_map(t), "spo2": t["spo2"],
                "paco2": t["abg_paco2"], "ph": t["abg_ph"], "lactate": t["lactate_mmol_l"], "hr": t["hr"],
                "rr": t["respiratory_rate"], "consciousness_level": mr.LEVEL_OF[t["mental_status"]]}
    exact = {k: abs(r[k] - authored[k]) < 1e-9 for k in ("sbp", "dbp", "map", "spo2", "paco2", "lactate",
                                                          "consciousness_level")}
    # The core's carbonic pH from the authored HCO3 and PaCO2, against the authored pH (two decimals).
    ph_within_rounding = abs(r["ph"] - authored["ph"]) <= 0.005
    position = dv.arrival_preload(a, prof)
    out = {"case": name, "anchors": a.to_dict(), "classes": mr.ARRIVAL_CLASSES[name], "channel_roles": mr.CHANNEL_ROLES[name],
           "bands": {k: vars(v) for k, v in mr.bands(name).items()}, "core": r, "authored": authored, "exact": exact,
           "ph_within_rounding": ph_within_rounding, "reconstruction": reconstruction,
           "mapping": {"preload_position": position, "default_position": prof.arrival_preload_fraction,
                       "lv_underfilled": mr.lv_underfilled(name), "v_evidence": list(mr.V_EVIDENCE),
                       "ivc": t["pocus_ivc"], "ivc_status": "RIGHT_SIDED / OBSERVATIONAL (not mapped)",
                       "pump_reserve": a.pump_reserve, "reversible_lung_water": a.reversible_lung_water,
                       "authored_pulmonary_edema": mr.authored_pulmonary_edema(name),
                       "lung_water_generation": mr.lung_water_generation(name)},
           "channels_at_arrival": {"V": s.V, "P": s.P, "L": s.L, "G": s.G, "D": s.D, "T": s.T}}
    band = mr.preload_band(name)
    out["mapping"]["band_at_or_below_neutral"] = band is None or (
        band.upper <= mr.NEUTRAL_PRELOAD_POSITION == prof.arrival_preload_fraction)
    out["pass"] = (out["mapping"]["band_at_or_below_neutral"] and all(exact.values()) and ph_within_rounding
                   and reconstruction.startswith("exact")
                   and s.V == 0.0 and s.L == 0.0 and s.G == 0.0 and s.P == 1.0 and a.pump_reserve == 1.0
                   and a.reversible_lung_water == 0.0
                   and (position < prof.arrival_preload_fraction if mr.lv_underfilled(name) else
                        a.preload_fraction is None))
    return out


def arrival_position_invariance() -> dict:
    """The arrival preload position changes nothing the resident sees at arrival: it shapes only the response to volume,
    so it never encodes the obstruction's shock (the arrival is authored)."""
    band = mr.preload_band()
    prof = profile()
    points = (band.lower, band.midpoint, band.upper, prof.arrival_preload_fraction, REJECTED_IVC_PRELOAD)
    keys = ("sbp", "dbp", "map", "spo2", "hr", "lactate", "output_rel", "delivery_index", "deficit", "rr", "paco2")
    rows = {}
    for x in points:
        a = mr.anchors(preload_fraction=x)
        r = reading(dv.arrival_state(a, prof), a, prof)
        rows[f"{x:g}"] = {k: r[k] for k in keys}
    first = next(iter(rows.values()))
    return {"points": list(points), "rows": rows, "pass": all(v == first for v in rows.values())}


# P2Q-2-3 / 4 / 6: the family writers -----------------------------------------------------------------------------------------

FORBIDDEN_NAMES = ("BloodFlow", "SettingChange", "DemandModifier", "Signal", "RhythmTransition", "reversible_lung_water",
                   "lung_water_gas_credit", "fio2", "spo2", "oxygenation", "Oxygen", "lactate", "respiration",
                   "central_drive_availability", "hypoxaemic_drive", "sympathetic_target", "congestion_rate")


def _class_writes(tree) -> dict:
    out = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        calls = [n for n in ast.walk(cls) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", getattr(n.func, "attr", None)) == "ChannelDelta"]
        literal = [c for c in calls if c.args and isinstance(c.args[0], ast.Attribute)
                   and isinstance(c.args[0].value, ast.Name) and c.args[0].value.id == "Channel"
                   and not any(k.arg == "channel" for k in c.keywords)]
        written = sorted({c.args[0].attr for c in literal}) + (
            ["<not a literal channel>"] if len(literal) != len(calls) else [])
        reads = sorted({n.attr for n in ast.walk(cls) if isinstance(n, ast.Attribute)
                        and isinstance(n.value, ast.Name) and n.value.id == "state"})
        out[cls.name] = {"writes": written, "reads_state": reads}
    return out


def writer_semantics() -> dict:
    """Each writer writes one channel (AST): the obstruction P, the gas exchange G, the owner L; no blood flow, setting,
    demand, signal or rhythm; nothing reads oxygen, lactate, the L credit or the drive; registered disease modules."""
    text = (ROOT / FAMILY_FILE).read_text(encoding="utf-8")
    tree = ast.parse(text)
    classes = _class_writes(tree)
    names = {getattr(n, "id", getattr(n, "attr", None)) for n in ast.walk(tree) if isinstance(n, (ast.Name, ast.Attribute))}
    a, prof = mr.anchors(), profile()
    start = dv.arrival_state(a, prof)
    out = {"classes": classes, "forbidden_names_used": sorted(set(FORBIDDEN_NAMES) & names),
           "writes_v": any("V" in c["writes"] for c in classes.values()),
           "authority": {cls.__name__: cls.lung_water_authority for cls in
                         (ObstructiveForwardFlow, EmbolicGasExchange, EmbolicLungWater)},
           "kinds": {cls.__name__: cls.kind.value for cls in (ObstructiveForwardFlow, EmbolicGasExchange,
                                                               EmbolicLungWater)},
           "registered": all(_REGISTRY.get(name) is cls for name, cls in zip(
               FAMILY_TYPES, (ObstructiveForwardFlow, EmbolicGasExchange, EmbolicLungWater))),
           "zero_owner_writes": EmbolicLungWater("pe-l", 0.0).contribute(start, 1, (), a, prof).deltas == (),
           "refusals": _refusals(), "never_written": list(an.NEVER_WRITTEN), "opioid_code": "opioid" in text.lower()}
    out["pass"] = (classes == {"ObstructiveForwardFlow": {"writes": ["P"], "reads_state": ["P", "R"]},
                               "EmbolicGasExchange": {"writes": ["G"], "reads_state": ["R"]},
                               "EmbolicLungWater": {"writes": ["L"], "reads_state": ["R"]}}
                   and not out["forbidden_names_used"] and not out["writes_v"] and not out["opioid_code"]
                   and out["authority"] == {"ObstructiveForwardFlow": False, "EmbolicGasExchange": False,
                                            "EmbolicLungWater": True}
                   and set(out["kinds"].values()) == {"disease_module"} and out["registered"]
                   and out["zero_owner_writes"] and all(out["refusals"].values()))
    return out


def _refusals() -> dict:
    def refused(build) -> bool:
        try:
            build()
        except CoreInvariantError:
            return True
        return False
    return {"negative_loss": refused(lambda: ObstructiveForwardFlow("x", -0.001, FLOOR)),
            "floor_zero": refused(lambda: ObstructiveForwardFlow("x", MID_LOSS, 0.0)),
            "floor_above_one": refused(lambda: ObstructiveForwardFlow("x", MID_LOSS, 1.5)),
            "negative_g": refused(lambda: EmbolicGasExchange("x", -0.01)),
            "negative_l": refused(lambda: EmbolicLungWater("x", -0.01)),
            "nan_g": refused(lambda: EmbolicGasExchange("x", float("nan")))}


# P2Q-2-3 / 19: the obstruction through the common core --------------------------------------------------------------------------

def obstruction_course() -> dict:
    """The obstruction alone (with the L owner) over the predeclared span: P -> Q -> MAP -> DO2 -> deficit -> D, through
    the common core, with V, Hb and L untouched."""
    a, prof = mr.anchors(), profile()
    out = {"region": {}}
    for loss in LOSS_PER_MIN:
        states, records = course((owner(), obstruction(loss)), anchors=a, prof=prof)
        series = [reading(s, a, prof) for s in states]
        first, last = series[0], series[-1]
        out["region"][f"{loss:.6g}"] = {
            "at": _rows(states, a, prof),
            "directions": {"P_nonincreasing": _nonincreasing([x["P"] for x in series]) and last["P"] < 1.0,
                           "Q_down": last["output_rel"] < first["output_rel"], "map_down": last["map"] < first["map"],
                           "delivery_down": last["delivery_index"] < first["delivery_index"],
                           "deficit_up": last["deficit"] > first["deficit"], "D_up": last["D"] > first["D"]},
            "V_zero": all(s.V == 0.0 for s in states), "hb_constant": all(s.hb == states[0].hb for s in states),
            "L_zero": all(s.L == 0.0 for s in states), "G_zero": all(s.G == 0.0 for s in states),
            "family": _family(records), "common_overload_writes": _writes(records, source=dv.PRELOAD_CONGESTION),
            "lactate": an.lactate_coherence(states, records, a, prof)}
    out["pass"] = all(all(v["directions"].values()) and v["V_zero"] and v["hb_constant"] and v["L_zero"]
                      and v["family"] == {"channels": ["P"], "other_writes": 0} and v["common_overload_writes"] == 0
                      and v["lactate"]["core_lactate_every_minute"] and v["lactate"]["no_family_lactate_write"]
                      for v in out["region"].values())
    return out


def untreated() -> dict:
    """The primary's untreated reference course (every writer at the span's middle), to 240 min."""
    a, prof = mr.anchors(), profile()
    states, records = course(writers(), LONG_HORIZON, anchors=a, prof=prof)
    series = [reading(s, a, prof) for s in states]
    return {"at": _rows(states, a, prof, LONG_READ), "family": _family(records),
            "common_overload_writes": _writes(records, source=dv.PRELOAD_CONGESTION),
            "L_max": max(abs(s.L) for s in states), "V_max": max(abs(s.V) for s in states),
            "lactate": an.lactate_coherence(states, records, a, prof),
            "pulse_kept": all(s.R.pulse_present for s in states),
            "minimum_lactate_minute": min(range(len(series)), key=lambda m: series[m]["lactate"])}


# P2Q-2 (no double count) -------------------------------------------------------------------------------------------------------

def no_double_count(found_untreated: dict, position: dict) -> dict:
    """The obstruction is P only: no PE source writes V or the blood state; V moves only with an authored fluid; the
    arrival position never changes the arrival; the V mapping reads the LV, never the IVC."""
    a, prof = mr.anchors(), profile()
    _, records = course(writers(), anchors=a, prof=prof)
    _, wet_records = course(writers() + (bolus(),), anchors=a, prof=prof)
    keys = set()
    for function in (mr.lv_underfilled, mr.preload_band):
        tree = ast.parse(inspect.getsource(function))
        keys |= {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                 and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)}
    source = inspect.getsource(mr.lv_underfilled) + inspect.getsource(mr.preload_band).split('"""')[-1]
    out = {"v_sources_untreated": _sources(records, Channel.V), "p_sources_untreated": _sources(records, Channel.P),
           "v_sources_with_fluid": _sources(wet_records, Channel.V), "p_sources_with_fluid": _sources(wet_records, Channel.P),
           "untreated_family_channels": found_untreated["family"]["channels"],
           "arrival_position_invariant": position["pass"], "v_mapping_reads": sorted(keys),
           "v_mapping_reads_right_side": any(item in source for item in mr.RIGHT_SIDED_OBSERVATION)}
    out["pass"] = (out["v_sources_untreated"] == [] and out["p_sources_untreated"] == ["disease_module:pe-obstruction"]
                   and out["v_sources_with_fluid"] == ["intervention:pe-fluid-stress"]
                   and out["p_sources_with_fluid"] == ["disease_module:pe-obstruction"]
                   and set(out["untreated_family_channels"]) == {"P", "G"} and out["arrival_position_invariant"]
                   and out["v_mapping_reads"] == ["pocus_lv"] and not out["v_mapping_reads_right_side"])
    return out


# P2Q-2-4: the L owner ----------------------------------------------------------------------------------------------------------

def lung_water_owner() -> dict:
    """With the owner: the common overload writes nothing and nothing writes L; a second owner is refused; without the
    owner, the rejected plethoric-IVC mapping with volume reproduces P2Q-1's false edema (the conflict the owner closes)."""
    prof = profile()
    a = mr.anchors()
    owned, owned_records = course(writers() + (bolus(),), anchors=a, prof=prof)
    ivc = mr.anchors(preload_fraction=REJECTED_IVC_PRELOAD)
    without = (obstruction(), gas())
    false_states, false_records = course(without + (bolus(),), anchors=ivc, prof=prof)
    ivc_owned, ivc_owned_records = course(without + (owner(), bolus()), anchors=ivc, prof=prof)
    mapped_states, mapped_records = course(without + (bolus(),), anchors=a, prof=prof)
    second = False
    try:
        step(dv.arrival_state(a, prof), (owner(), EdemaCongestion("edema-congestion", 0.005)), a, prof)
    except ProvenanceError:
        second = True
    key = dv.PRELOAD_CONGESTION
    out = {"owned": {"common_writes": _writes(owned_records, source=key), "L_writes": _writes(owned_records, Channel.L),
                     "L_max": max(abs(s.L) for s in owned)},
           "rejected_ivc_owned": {"common_writes": _writes(ivc_owned_records, source=key),
                                  "L_max": max(abs(s.L) for s in ivc_owned)},
           "knee": prof.congestion_preload_knee, "rejected_ivc_preload": REJECTED_IVC_PRELOAD,
           "counterfactual_rejected_ivc_no_owner": {"common_writes": _writes(false_records, source=key),
                                                    "L_max": max(s.L for s in false_states),
                                                    "spo2_end": dv.derive(false_states[-1], ivc, prof).spo2},
           "counterfactual_lv_mapping_no_owner": {"common_writes": _writes(mapped_records, source=key),
                                                  "L_max": max(s.L for s in mapped_states),
                                                  "position_max": max(dv.preload_position(s, a, prof)
                                                                      for s in mapped_states)},
           "second_owner_refused": second,
           "generation": {n: mr.lung_water_generation(n) for n in mr.CASES},
           "authored_pulmonary_edema": {n: mr.authored_pulmonary_edema(n) for n in mr.CASES}}
    # The counterfactuals are reported, never required: they show what the owner closes.
    out["pass"] = (out["owned"] == {"common_writes": 0, "L_writes": 0, "L_max": 0.0}
                   and out["rejected_ivc_owned"] == {"common_writes": 0, "L_max": 0.0} and second
                   and set(out["generation"].values()) == {0.0} and not any(out["authored_pulmonary_edema"].values()))
    return out


# P2Q-2-5: the fluid stress ----------------------------------------------------------------------------------------------------

def fluid_stress() -> dict:
    """Obstruction + the large synthetic bolus with the owner, at each point of the LV preload band: no false L, no SpO2
    change from L; the forward-flow response is reported against the unobstructed control (it may be limited)."""
    prof = profile()
    band = mr.preload_band()
    out = {"design": FLUID_STRESS, "points": {}}
    for point in ("lower", "midpoint", "upper"):
        a = mr.anchors(preload_fraction=getattr(band, point))
        dry, _ = course(writers(), anchors=a, prof=prof)
        wet, wet_records = course(writers() + (bolus(),), anchors=a, prof=prof)
        open_dry, _ = course(writers(loss=0.0), anchors=a, prof=prof)
        open_wet, _ = course(writers(loss=0.0) + (bolus(),), anchors=a, prof=prof)
        bare, bare_records = course((obstruction(), gas(), bolus()), anchors=a, prof=prof)
        end = FLUID_STRESS["begins_at_minute"] + int(FLUID_STRESS["duration_min"])
        row = {}
        for minute in (end, HORIZON):
            d, w = reading(dry[minute], a, prof), reading(wet[minute], a, prof)
            od, ow = reading(open_dry[minute], a, prof), reading(open_wet[minute], a, prof)
            row[str(minute)] = {"output_without": d["output_rel"], "output_with": w["output_rel"],
                                "output_gain": w["output_rel"] - d["output_rel"], "map_gain": w["map"] - d["map"],
                                "unobstructed_output_gain": ow["output_rel"] - od["output_rel"],
                                "position_with": w["preload_position"], "spo2_with": w["spo2"],
                                "spo2_without": d["spo2"]}
        out["points"][point] = {
            "preload_fraction": getattr(band, point), "at": row,
            "L_max": max(abs(s.L) for s in wet), "L_writes": _writes(wet_records, Channel.L),
            "common_overload_writes": _writes(wet_records, source=dv.PRELOAD_CONGESTION),
            "spo2_unchanged_by_fluid": all(reading(x, a, prof)["spo2"] == reading(y, a, prof)["spo2"]
                                           for x, y in zip(dry, wet)),
            "G_unchanged_by_fluid": all(x.G == y.G for x, y in zip(dry, wet)),
            "response_limited_vs_unobstructed": row[str(HORIZON)]["output_gain"]
            < row[str(HORIZON)]["unobstructed_output_gain"],
            # Reported, never required: without the owner, does the common overload write here at all?
            "no_owner": {"common_writes": _writes(bare_records, source=dv.PRELOAD_CONGESTION),
                         "L_max": max(abs(s.L) for s in bare),
                         "position_max": max(dv.preload_position(s, a, prof) for s in bare)}}
    out["pass"] = all(v["L_max"] == 0.0 and v["L_writes"] == 0 and v["common_overload_writes"] == 0
                      and v["spo2_unchanged_by_fluid"] and v["G_unchanged_by_fluid"] for v in out["points"].values())
    return out


# P2Q-2-6: direct G ------------------------------------------------------------------------------------------------------------

def direct_g() -> dict:
    """The gas-exchange writer alone (with the owner): G linear, SpO2 = arrival - s x G at room air, delivery down, L 0,
    no lung-water credit, even with a negative L_rev declared."""
    prof = profile()
    a = mr.anchors()
    lrev = mr.anchors(reversible_lung_water=L_REV_PROBE)
    out = {"rates": {}}
    for rate in G_RATES:
        states, records = course(writers(loss=0.0, rate=rate), anchors=a, prof=prof)
        lrev_states, _ = course(writers(loss=0.0, rate=rate), anchors=lrev, prof=prof)
        series = [reading(s, a, prof) for s in states]
        out["rates"][f"{rate:g}"] = {
            "at": {m: {k: series[int(m)][k] for k in ("G", "spo2", "delivery_index", "deficit", "map", "L")}
                   for m in map(str, READ)},
            "G_linear": all(abs(s.G - rate * s.minute) < 1e-9 for s in states),
            "spo2_is_common_mapping": all(abs(x["spo2"] - max(0.0, a.spo2 - prof.spo2_per_gas_exchange_unit * x["G"]))
                                          < 1e-9 for x in series),
            "spo2_down": _nonincreasing([x["spo2"] for x in series]) and series[-1]["spo2"] < a.spo2,
            "delivery_down": series[-1]["delivery_index"] < series[0]["delivery_index"],
            "L_zero": all(s.L == 0.0 for s in states),
            "credit_zero": all(dv.lung_water_gas_credit(s.L, x, prof) == 0.0 for s, x in
                               [(s, a) for s in states] + [(s, lrev) for s in lrev_states]),
            "negative_l_rev_changes_nothing": [reading(s, lrev, prof)["spo2"] for s in lrev_states]
            == [x["spo2"] for x in series],
            "g_sources": _sources(records, Channel.G)}
    out["pass"] = all(v["G_linear"] and v["spo2_is_common_mapping"] and v["spo2_down"] and v["delivery_down"]
                      and v["L_zero"] and v["credit_zero"] and v["negative_l_rev_changes_nothing"]
                      and v["g_sources"] == ["disease_module:pe-gas-exchange"] for v in out["rates"].values())
    return out


# P2Q-2-7: oxygen ---------------------------------------------------------------------------------------------------------------

def oxygen() -> dict:
    a, prof = mr.anchors(), profile()
    room, _ = course(writers(), anchors=a, prof=prof)
    by_fio2 = {0.21: [reading(s, a, prof)["spo2"] for s in room]}
    out = {"fio2": {}}
    for f in FIO2:
        states, _ = course(writers() + (Oxygen("pe-o2", 0, f),), anchors=a, prof=prof)
        by_fio2[f] = [reading(s, a, prof)["spo2"] for s in states]
        out["fio2"][f"{f:g}"] = {m: by_fio2[f][int(m)] for m in map(str, READ)}
    out["room_air"] = {m: by_fio2[0.21][int(m)] for m in map(str, READ)}
    minutes = range(1, HORIZON + 1)
    monotone = all(_nondecreasing([by_fio2[f][m] for f in sorted(by_fio2)]) for m in minutes)
    gain_early, gain_late = by_fio2[0.6][30] - by_fio2[0.21][30], by_fio2[0.6][120] - by_fio2[0.21][120]
    text = (ROOT / FAMILY_FILE).read_text(encoding="utf-8")
    family_oxygen = any(getattr(n, "id", getattr(n, "attr", "")) in ("fio2", "spo2", "oxygenation", "Oxygen",
                                                                      "SettingChange")
                        for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.Name, ast.Attribute)))
    out.update({"monotone_in_fio2": monotone, "gain_at_30": gain_early, "gain_at_120": gain_late,
                "attenuated_as_G_worsens": gain_late < gain_early, "family_oxygen_function": family_oxygen})
    out["pass"] = monotone and gain_late < gain_early and not family_oxygen
    return out


# P2Q-2-8 / 9: the respiratory drive ------------------------------------------------------------------------------------------

def _drive_series(states, a, prof) -> list:
    out = []
    for s in states:
        c = dv.respiratory_drive_composition(s, a, prof)
        r = dv.respiration(s, a, prof)
        out.append({"acid": c.acid_drive, "hypoxaemic": c.hypoxaemic_drive, "excitatory": c.excitatory_drive,
                    "excitatory_rr": c.excitatory_rr, "expressed_rr": c.expressed_rr, "intrinsic": c.baseline_rr,
                    "paco2": r.paco2, "ph": r.ph, "spo2": c.spo2})
    return out


def respiratory_drive() -> dict:
    """P2P-2 exercised structurally: UNSET gives no hypoxaemic drive; the SYNTHETIC_ONLY mapping makes the absolute
    hypoxaemia drive and grow as G worsens; nothing else in the state moves (the RR feeds nothing back); no PE term."""
    a = mr.anchors()
    unset_prof, synthetic_prof = profile(), hypoxaemic_profile()
    unset_states, _ = course(writers(), anchors=a, prof=unset_prof)
    synthetic_states, _ = course(writers(), anchors=a, prof=synthetic_prof)
    unset, synthetic = _drive_series(unset_states, a, unset_prof), _drive_series(synthetic_states, a, synthetic_prof)
    t = mr.truth()
    out = {"unset": {m: unset[int(m)] for m in map(str, READ)}, "synthetic": {m: synthetic[int(m)] for m in map(str, READ)},
           "authored_rr": t["respiratory_rate"], "arrival_rr": {"unset": unset[0]["expressed_rr"],
                                                                "synthetic": synthetic[0]["expressed_rr"]},
           "unset_no_hypoxaemic_drive": all(x["hypoxaemic"] == 0.0 for x in unset),
           "synthetic_drives_at_arrival": synthetic[0]["hypoxaemic"] > 0.0,
           "synthetic_rises_with_G": _nondecreasing([x["hypoxaemic"] for x in synthetic])
           and synthetic[-1]["hypoxaemic"] > synthetic[0]["hypoxaemic"],
           "excitatory_at_least_acid": all(x["excitatory"] >= x["acid"] for x in synthetic),
           "rr_at_least_unset": all(s["expressed_rr"] >= u["expressed_rr"] - 1e-12 for s, u in zip(synthetic, unset)),
           "states_identical": [s.to_dict() for s in unset_states] == [s.to_dict() for s in synthetic_states],
           "family_writes_w": "W" in {c for v in _class_writes(ast.parse((ROOT / FAMILY_FILE).read_text(
               encoding="utf-8"))).values() for c in v["writes"]},
           "parameter_status": {"hypoxaemic_drive_mapping": "UNSET by default; SYNTHETIC_ONLY here (P2P-2's)",
                                "hypoxaemic_to_drive_gain": f"UNSET by default; SYNTHETIC_ONLY {HYPOXAEMIC_GAIN:g} here",
                                "chosen_from_pe": False}}
    out["arrival_rr_gap"] = {k: t["respiratory_rate"] - v for k, v in out["arrival_rr"].items()}
    out["pass"] = (out["unset_no_hypoxaemic_drive"] and out["synthetic_drives_at_arrival"]
                   and out["synthetic_rises_with_G"] and out["excitatory_at_least_acid"] and out["rr_at_least_unset"]
                   and out["states_identical"] and not out["family_writes_w"])
    return out


def central_depression() -> dict:
    """P2P-2's guard on the PE course: a strong central depression keeps the expressed RR at or below the intrinsic RR
    whatever the hypoxaemic drive, raises PaCO2, and moves nothing else; the composition is P2P-2's file unchanged."""
    a = mr.anchors()
    intact_prof, depressed_prof = hypoxaemic_profile(), hypoxaemic_profile(central_drive_availability=DEPRESSION)
    intact_states, _ = course(writers(), anchors=a, prof=intact_prof)
    depressed_states, _ = course(writers(), anchors=a, prof=depressed_prof)
    intact, depressed = _drive_series(intact_states, a, intact_prof), _drive_series(depressed_states, a, depressed_prof)
    bound = DEPRESSION * (depressed[0]["intrinsic"] + depressed_prof.rr_drive_saturation)
    out = {"availability": DEPRESSION, "bound": bound,
           "depressed": {m: depressed[int(m)] for m in map(str, READ)},
           "intact": {m: intact[int(m)] for m in map(str, READ)},
           "at_or_below_intrinsic": all(x["expressed_rr"] <= x["intrinsic"] for x in depressed),
           "within_bound": all(x["expressed_rr"] <= bound + 1e-12 for x in depressed),
           "paco2_higher": all(d["paco2"] > i["paco2"] for d, i in zip(depressed, intact)),
           "hypoxaemic_drive_unchanged": [x["hypoxaemic"] for x in depressed] == [x["hypoxaemic"] for x in intact],
           "states_identical": [s.to_dict() for s in intact_states] == [s.to_dict() for s in depressed_states],
           "composition_file_unchanged": common_untouched()["clinical_core/derived.py"]}
    out["pass"] = (out["at_or_below_intrinsic"] and out["within_bound"] and out["paco2_higher"]
                   and out["hypoxaemic_drive_unchanged"] and out["states_identical"] and out["composition_file_unchanged"])
    return out


# P2Q-2-10 / 11 / 12: tone, HR, D and lactate ---------------------------------------------------------------------------------

def tone(found_untreated: dict) -> dict:
    """The current tone architecture carried: T rises only with the deficit; the MAP falls nearly with Q; the missing
    pressure -> tone compensation is recorded, not added; the 1-D tone sensitivity is the ACS package's."""
    at = found_untreated["at"]
    first, last = at["0"], at[str(HORIZON)]
    a = mr.anchors()
    sensitivity = {}
    for gain in ar.TONE_SENSITIVITY:
        q = profile(deficit_to_tone_gain=gain)
        states, _ = course(writers(), anchors=a, prof=q)
        r = reading(states[-1], a, q)
        sensitivity[f"{gain:g}"] = {k: r[k] for k in ("T", "output_rel", "map", "deficit", "D")}
    # The ACS package's point itself (acs_reference, pinned by hash in COMMON_AT_P2P2), never this package's wrapper.
    base = ar.common_profile()
    prof = profile()
    out = {"T_change": last["T"] / first["T"] - 1.0, "output_change": last["output_rel"] / first["output_rel"] - 1.0,
           "map_change": last["map"] / first["map"] - 1.0, "sensitivity": sensitivity,
           "family_writes_T": "T" in found_untreated["family"]["channels"],
           "tone_gain": prof.deficit_to_tone_gain,
           "gains_untouched": all(getattr(prof, f.name) == getattr(base, f.name) for f in fields(prof)
                                  if f.name not in go.REFERENCE),
           "classification": "CROSS_FAMILY_COMMON_REFINEMENT_EVIDENCE_INCREASED (the missing pressure -> tone "
                             "compensation, now independently in ACS and PE); P2J not reopened"}
    out["pass"] = (not out["family_writes_T"] and out["gains_untouched"] and out["T_change"] > 0.0
                   and out["map_change"] < 0.0)
    return out


def heart_rate(found_untreated: dict) -> dict:
    out = {"cases": {}}
    prof = profile()
    for name in mr.CASES:
        decomposition = dv.heart_rate_decomposition(mr.anchors(name), prof)
        band = {point: dv.heart_rate_decomposition(mr.anchors(name, point), prof)["predicted_arrival_hr"]
                for point in ("lower", "midpoint", "upper")}
        out["cases"][name] = {"authored": decomposition["observed_arrival_hr"],
                              "predicted": decomposition["predicted_arrival_hr"],
                              "mismatch_bpm": decomposition["mismatch_bpm"], "decomposition": decomposition,
                              "predicted_over_bands": band,
                              "authored_inside_band": min(band.values()) <= decomposition["observed_arrival_hr"]
                              <= max(band.values())}
    at = found_untreated["at"]
    out["hr_rises_with_deterioration"] = at[str(HORIZON)]["hr"] > at["0"]["hr"]
    out["classification"] = ("MULTI_FAMILY_COMMON_HR_GAP (ACS, pulmonary edema, PE): the arrival sympathetic share is "
                             "not reproduced; no arrival hypoxaemia, distress, pain or RV-load term; not retuned")
    base = ar.common_profile()
    out["gains_untouched"] = all(getattr(prof, f.name) == getattr(base, f.name) for f in fields(prof)
                                 if f.name not in go.REFERENCE)
    out["pass"] = out["hr_rises_with_deterioration"] and out["gains_untouched"]
    return out


def d_lactate(found_untreated: dict) -> dict:
    """Arrival D latent (never from lactate); lactate the core's every minute; whether the arrival excess clears before
    the new debt dominates is reported, never forced."""
    base = mr.anchors()
    prof = profile()
    # The whole arrival mapping rebuilt from a truth whose lactate is doubled: the lactate reaches the anchors (its
    # clearable excess changes) and the arrival D does not.
    doubled = dict(mr.truth())
    doubled["lactate_mmol_l"] = doubled["lactate_mmol_l"] * 2.0
    other = mr.anchors(t=doubled)
    at = found_untreated["at"]
    lactate = {m: at[m]["lactate"] for m in at}
    debt = {m: at[m]["D"] for m in at}
    out = {"arrival_D": dv.arrival_state(base, prof).D, "arrival_D_band": vars(mr.bands()["arrival_oxygen_debt"]),
           "d_independent_of_lactate": dv.arrival_state(base, prof).D == dv.arrival_state(other, prof).D
           and other.lactate != base.lactate and other.arrival_lactate_excess != base.arrival_lactate_excess,
           "lactate": lactate, "D": debt, "lactate_core_only": found_untreated["lactate"],
           "minimum_lactate_minute": found_untreated["minimum_lactate_minute"],
           "arrival_excess_clears_first": lactate["60"] < lactate["0"] and debt["60"] > debt["0"],
           "rises_after_minimum": lactate[str(LONG_HORIZON)] > min(lactate.values()),
           "secondary_arrival_D": dv.arrival_state(mr.anchors(mr.SECONDARY), prof).D,
           "kinetics_untouched": all(getattr(prof, k) == getattr(ar.common_profile(), k)
                                     for k in ("debt_clearance_tau_min", "debt_per_delivery_deficit",
                                               "debt_to_lactate_gain", "lactate_clearance_tau_min"))}
    out["pass"] = (out["d_independent_of_lactate"] and out["lactate_core_only"]["core_lactate_every_minute"]
                   and out["lactate_core_only"]["no_family_lactate_write"] and out["kinetics_untouched"]
                   and out["secondary_arrival_D"] == 0.0)
    return out


# P2Q-2-13: collapse, structural only -----------------------------------------------------------------------------------------

def collapse() -> dict:
    a, prof = mr.anchors(), profile()
    states, _ = course(writers(), LONG_HORIZON, anchors=a, prof=prof)
    ramp = cx.CollapseProfile(perfusion_mapping=cx.PerfusionMapping(*an.STRUCTURAL_RAMP))
    rows = []
    for s in (states[m] for m in (0, 60, HORIZON, LONG_HORIZON)):
        r = cx.readings(s, a, prof)
        unset = cx.signal_at(r, cx.CollapseProfile())
        structural = cx.signal_at(r, ramp)
        rows.append({"minute": s.minute, "map": r["map"], "delivery": unset.delivery, "unset_perfusion": unset.perfusion,
                     "unset_complete": unset.complete, "structural_perfusion": structural.perfusion,
                     "structural_value": structural.value,
                     "max_holds": structural.value == max(structural.perfusion, structural.delivery)})
    source = (CORE_DIR / "collapse.py").read_text(encoding="utf-8").lower()
    out = {"rows": rows, "max_holds": all(r["max_holds"] for r in rows),
           "unset_is_lower_bound": all(not r["unset_complete"] for r in rows),
           "delivery_signal_rises": _nondecreasing([r["delivery"] for r in rows]) and rows[-1]["delivery"] > rows[0]["delivery"],
           "perfusion_signal_rises": _nondecreasing([r["structural_perfusion"] for r in rows])
           and rows[-1]["structural_perfusion"] > rows[0]["structural_perfusion"],
           "no_family_rule": not any(w in source for w in ("embol", "obstruct", "pulmonary_embolism", "thromb")),
           "active": False, "thresholds_selected": False, "terminal_transition": False}
    out["pass"] = (out["max_holds"] and out["unset_is_lower_bound"] and out["delivery_signal_rises"]
                   and out["perfusion_signal_rises"] and out["no_family_rule"])
    return out


# P2Q-2-14: the secondary case ------------------------------------------------------------------------------------------------

def secondary() -> dict:
    name = mr.SECONDARY
    a, prof = mr.anchors(name), profile()
    out = {"arrival": arrival(name), "runs": {}}
    for loss in SECONDARY_LOSS:
        states, records = course(writers(loss=loss, name=name), anchors=a, prof=prof)
        series = [reading(s, a, prof) for s in states]
        out["runs"][f"{loss:.6g}"] = {
            "at": {m: {k: series[int(m)][k] for k in ("P", "G", "L", "spo2", "map", "output_rel", "delivery_index",
                                                       "deficit", "D", "lactate", "hr", "consciousness_level")}
                   for m in map(str, READ)},
            "spo2_down": series[-1]["spo2"] < series[0]["spo2"], "L_zero": all(s.L == 0.0 for s in states),
            "map_unchanged": all(abs(x["map"] - series[0]["map"]) < 1e-9 for x in series),
            "common_overload_writes": _writes(records, source=dv.PRELOAD_CONGESTION), "family": _family(records)}
    g_only = out["runs"][f"{SECONDARY_LOSS[0]:.6g}"]
    out["hypoxaemia_without_hypotension"] = g_only["spo2_down"] and g_only["map_unchanged"]
    out["pass"] = (out["arrival"]["pass"] and out["hypoxaemia_without_hypotension"]
                   and all(v["L_zero"] and v["common_overload_writes"] == 0 for v in out["runs"].values()))
    return out


# P2Q-2-15: observable reconstruction -------------------------------------------------------------------------------------------

def observable_support(name: str, found_arrival: dict, found_hr: dict, found_drive: dict | None) -> dict:
    t = mr.truth(name)
    core, exact = found_arrival["core"], found_arrival["exact"]
    hr = found_hr["cases"][name]
    rows = {
        "sbp": {"authored": t["sbp"], "core": core["sbp"], "status": "EXACT_ANCHORED" if exact["sbp"] else "MISMATCH"},
        "dbp": {"authored": t["dbp"], "core": core["dbp"], "status": "EXACT_ANCHORED" if exact["dbp"] else "MISMATCH"},
        "map": {"authored": mr.authored_map(t), "core": core["map"],
                "status": "EXACT_ANCHORED" if exact["map"] else "MISMATCH"},
        "spo2": {"authored": t["spo2"], "core": core["spo2"],
                 "status": "EXACT_ANCHORED" if exact["spo2"] else "MISMATCH"},
        "lactate": {"authored": t["lactate_mmol_l"], "core": core["lactate"],
                    "status": "EXACT_ANCHORED" if exact["lactate"] else "MISMATCH"},
        "paco2": {"authored": t["abg_paco2"], "core": core["paco2"],
                  "status": "EXACT_ANCHORED" if exact["paco2"] else "MISMATCH"},
        "ph": {"authored": t["abg_ph"], "core": core["ph"],
               "status": "WITHIN_ROUNDING" if found_arrival["ph_within_rounding"] else "MISMATCH"},
        "pao2": {"authored": t["abg_pao2"], "core": None, "status": "NOT_MODELLED (the core carries SpO2, not PaO2)"},
        "hr": {"authored": t["hr"], "core": hr["predicted"], "band": hr["predicted_over_bands"],
               "status": "GAP: MULTI_FAMILY_COMMON_HR_GAP (outside the mapped bands)" if not hr["authored_inside_band"]
               else "WITHIN_BANDS"},
        "rr": {"authored": t["respiratory_rate"], "core": core["rr"],
               "synthetic_hypoxaemic": None if found_drive is None else found_drive["arrival_rr"]["synthetic"],
               "status": "GAP: EXPECTED_RESPIRATORY_FAMILY_EXTENSION (no dead-space, mechanics or receptor drive; the "
                         "hypoxaemic drive UNSET)" if t["respiratory_rate"] - core["rr"] > RR_GAP else "WITHIN_GAP"},
        "mental_status": {"authored": t["mental_status"], "core": core["consciousness_level"],
                          "status": "EXACT_ANCHORED" if exact["consciousness_level"] else "MISMATCH"},
        "rv": {"authored": t["pocus_rv"], "status": "OBSERVATION_LAYER (the obstruction, P = 1 at arrival)"},
        "lv": {"authored": t["pocus_lv"], "status": "OBSERVATION_LAYER (the arrival preload position, V_EVIDENCE)"},
        "ivc": {"authored": t["pocus_ivc"], "status": "RIGHT_SIDED / OBSERVATIONAL (never V or L)"},
        "lungs": {"authored": t["pocus_lungs"], "status": "OBSERVATION_LAYER (L = 0, family-owned, zero generation)"}}
    contradictions = [k for k, v in rows.items() if v["status"] == "MISMATCH"]
    return {"rows": rows, "contradictions": contradictions, "pass": not contradictions}


# P2Q-2-16: the legacy engine, read last ----------------------------------------------------------------------------------------

LEGACY_MINUTES = READ


def legacy() -> dict:
    """The family engine's untreated courses, read as LEGACY_REFERENCE_ONLY."""
    from . import legacy_adapter as la
    out = {}
    for name in mr.CASES:
        engine = la._engine()
        current = la.bank_case(name, family=mr.FAMILY)
        engine._initialize(current)
        rows = {}
        for minute in range(max(LEGACY_MINUTES) + 1):
            if minute in LEGACY_MINUTES:
                o = current.get("observable", {})
                rows[str(minute)] = {k: o.get(k) for k in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt",
                                                           "mental_status")}
            if minute < max(LEGACY_MINUTES):
                engine.advance_clinical_time(current, 1)
        out[name] = rows
    return out


def legacy_comparison(found_untreated: dict, legacy_rows: dict) -> dict:
    core = found_untreated["at"]
    rows = {m: {"legacy": legacy_rows[mr.CASE].get(m, {}),
                "core": {k: core[m][k] for k in ("sbp", "dbp", "map", "spo2", "hr", "rr", "consciousness_level")}}
            for m in ("0", "60", "120")}
    classes = {
        "bp_spo2_course": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both worsen untreated; the size is the family "
                          "span's (the ACS P scale, P2O-1's G scale) and the legacy drift's, neither authored",
        "hr": "POSSIBLE_COMMON_CORE_GAP: the legacy shows the authored HR and lets it drift; the core's arrival HR is the "
              "common physiology's (MULTI_FAMILY_COMMON_HR_GAP); it rises with the deficit afterwards",
        "rr": "EXPECTED_EXTENSION: the legacy holds the authored RR; the common RR is the P2P-2 composition with the "
              "hypoxaemic drive UNSET and no dead-space or mechanics drive",
        "consciousness": "POSSIBLE_COMMON_CORE_GAP: the legacy stays alert; derive's ADOPTED absolute SpO2 ladder (87 / 80) "
                         "reads the worsening SpO2 as drowsy (ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY, shared with "
                         "pulmonary edema)",
        "rapid_volume": "EXPECTED_EXTENSION: the legacy punishes volume above 10 mL/min (RV strain, part of it as worse "
                        "oxygenation); the core's unsided P gives a forward-flow response that may be limited, never "
                        "harm: ventricular interdependence needs sided state (SIDED_PRELOAD_COMMON_STATE_DEFERRED)",
        "thrombolysis_reperfusion": "EXPECTED_EXTENSION: the legacy lysis and its bleeding are not migrated (reperfusion "
                                    "writer deferred)"}
    return {"rows": rows, "secondary_legacy": legacy_rows[mr.SECONDARY], "classes": classes,
            "possible_common_core_gap": sorted(k for k, v in classes.items() if v.startswith("POSSIBLE_COMMON_CORE_GAP")),
            "used_for_parameters": False}


# P2Q-2-17: GI, ACS, pulmonary edema and P2P-2 unchanged -------------------------------------------------------------------------

def _json(value):
    return json.loads(json.dumps(go._plain(value), sort_keys=True, default=str))


def non_regression() -> dict:
    """With the PE writers inactive nothing common moves: P2O-1's GI probe and ACS evaluation, P2O-3's authority probes,
    P2P-1's edema courses and P2P-2's drive probes reproduce their frozen records; every common file is at its P2P-2
    bytes."""
    p2o1 = json.loads(go.RECORD.read_text(encoding="utf-8"))
    p2o3 = json.loads(lw.RECORD.read_text(encoding="utf-8"))
    p2p1 = json.loads(pe.RECORD.read_text(encoding="utf-8"))
    p2p2 = json.loads(rd.RECORD.read_text(encoding="utf-8"))
    r78 = _json(lw.probe_r7_r8())
    d14, d67 = _json(rd.probe_d1_d4()), _json(rd.probe_d6_d7())
    out = {"gi_o12": _json(go.probe_o12()) == p2o1["probes"]["O12"],
           "acs_evaluation": _json(go.acs_evaluation()) == p2o1["acs"],
           "acs_authority_r7": r78["R7"] == p2o3["probes"]["probes"]["R7"],
           "common_overload_r8": r78["R8"] == p2o3["probes"]["probes"]["R8"],
           "edema_untreated": _json(pe.untreated()) == p2p1["untreated"],
           "edema_oxygen": _json(pe.oxygen()) == p2p1["oxygen"],
           "edema_authority": _json(pe.authority()) == p2p1["authority"],
           "edema_respiration": _json(pe.respiration()) == p2p1["respiration"],
           "edema_heart_rate": _json(pe.heart_rate()) == p2p1["heart_rate"],
           "p2p2_d1_d7_d9_d10": all(v == p2p2["probes"][k] for k, v in {**d14, **d67, "D5": _json(rd.probe_d5()),
                                                                          "D9": _json(rd.probe_d9()),
                                                                          "D10": _json(rd.probe_d10())}.items()),
           "p2p2_opioid": _json(rd.opioid_probe()) == p2p2["opioid"],
           "p2p2_acidosis": _json(rd.acidosis_probe()) == p2p2["acidosis"],
           "p2p2_edema_diagnostic": _json(rd.pulmonary_edema_diagnostic()) == p2p2["pulmonary_edema"],
           "common_files_untouched": common_untouched()}
    out["pass"] = all(v for k, v in out.items() if k != "common_files_untouched") and all(
        out["common_files_untouched"].values())
    return out


# The closed packages' view: the files P2P-2 left, P2Q-2's tuple entries undone (proven) -------------------------------------------

P2P2_HEAD = "2a44327"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/edema_migration.py", '
                                     '"clinical_core/edema_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_drive.py", '
                                     '"clinical_core/respiratory_drive_report.py",\n'
                                     '                        "clinical_core/embolism_migration.py", '
                                     '"clinical_core/embolism_migration_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/edema_migration.py", '
                                     '"clinical_core/edema_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_drive.py", '
                                     '"clinical_core/respiratory_drive_report.py")\n'
                                     '\n'),),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/edema_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_drive_report.py",\n'
                                     '                      "clinical_core/embolism_migration_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/edema_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_drive_report.py")\n'
                                     '\n'),)}
CORE_AT_P2P2 = {'clinical_core/decision_pack.py': '46d4465a6fe51ac41bd41569017ffc4d94e12b05165b58c0d68bf179afa5303d',
 'clinical_core/lactate_slice.py': 'c9cd9ec1c1af6906a58a9a3f48136d415297935a64d7c2dc6435d642b118bfbd'}
# </reversal>
# <common>
COMMON_AT_P2P2 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/derived.py': 'e701e99bfa4a2ad2e1d17a7408d91b566abf6d76fa7da1678213c54db0ecbedb',
 'clinical_core/edema_migration.py': '7d2bd34a883c0253aed4d254f025b400bf178346e348fd3982986c228ef2b464',
 'clinical_core/edema_migration_report.py': '02c20561397d1d4ab7b9a83e1e1be1ce8abe5b027a7f8679cd5ba9af0b418467',
 'clinical_core/edema_reference.py': 'fd8702e4d5ed03cf6dbe72cf0053ad9af6966e40e2b197cf42261bf61a66eb76',
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
 'clinical_core/integration.py': 'c725fbe8ab4daa69952dfd06a8f584e303ef6ff66bd67441deaa70e4cce887af',
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
 'clinical_core/modules/rhythm_events.py': '1036a2443e44fe5e2fde80736984b6828542b69454cc49a36e660ee8d436c86b',
 'clinical_core/oxygen_probes.py': '450cec663ae0c47ba32b6df8b4fadc136cad6c9a2e14f8f08d649d166651febd',
 'clinical_core/pressure_tone.py': '2e350c8a42bcacfa31e8e5349d284c7d276808e396d36421e1dc369dbcb9ec26',
 'clinical_core/pressure_tone_filter.py': '54bff406686b2b8e47757f10c5ec42cb6e0a0d170f2627cb926f99eea1c7e650',
 'clinical_core/pressure_tone_filter_report.py': '6eebe11b816eeb901f10d9f1431182b71ab26db84652771af741076f33734f92',
 'clinical_core/pressure_tone_report.py': 'bc0fe73c681a35432baec5acf8062027b63f0e5821146133fb9211ae9240d7ac',
 'clinical_core/provenance.py': '3e670fc4aebb296232e8418f448cb14f6da46c387d4af4fc2ae7b95ba1e328d8',
 'clinical_core/respiratory_drive.py': '246f4ad5070fb50a64eec686ee4441e896d79c6d717303e1a43c11f7bf5af21b',
 'clinical_core/respiratory_drive_report.py': '7bb2ee04e3204b4de2bf542cac2f8166d72de7af4892cc7f098699f5adc94f2a',
 'clinical_core/respiratory_monotonicity.py': 'ba6bac3ea1f4f1f9b0bff5503b4ff846f1ae5a097ee88d8480dd3ee52fbba672',
 'clinical_core/respiratory_monotonicity_report.py': '373cdac40c02f1e0bd4683f9ab6329ce08805b4a41e38939e89ff28a8fc83fcb',
 'clinical_core/rr_audit.py': '4b663ffad81ff88f728707e7c96a255d882cbf62247107980652331fff885bf1',
 'clinical_core/rr_audit_report.py': 'f3951b39f4b0b9d6b82a6fffa687457f68257743e6e86fb4d5c10c0dc81797e5',
 'clinical_core/shadow.py': '66ef25c952509f0765731cfc0c0b97274bc5a4d263dcb486b595a8585a99ef35',
 'clinical_core/signals.py': 'f02f5494a8aac0361ace94a40e15a4df81970f456de7af0f6762a1196a27ee7f',
 'clinical_core/state.py': '141cd5a2aada89a58e7de9ee1436b2f52fd68141df132bcb26e934e6e9ddc7d1',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}
# </common>


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2P2[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2P2.items()}


def p2p2_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2P-2 file plus P2Q-2's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2p2_bytes(relative: str) -> bytes:
    return p2p2_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2p2_sources(sources: dict) -> dict:
    """A P2P-2 dependency map: P2Q-2's files removed, each changed file at its P2P-2 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2P2.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def p2p2_registry(registry: dict) -> dict:
    """A registry as P2P-2 left it: the PE family's types removed."""
    return {k: v for k, v in registry.items() if k not in FAMILY_TYPES}


_GO_BOUNDARIES = go.boundaries


def p2p2_go_boundaries() -> dict:
    """P2O-1's boundary audit as the P2P-2 tree reads: the PE family module (the first family writer of G, a direct
    G writer by design) left out of its scan of family modules, the pass recomputed from the same items."""
    out = dict(_GO_BOUNDARIES())
    modules = [m for m in out["family_modules_writing_G"] if m not in OWN]
    out["family_modules_writing_G"] = modules
    out["pass"] = (out["readers_in_derived"]["G"] == ["_perfusion"]
                   and all(out["respiration_and_downstream_read_no_L_or_G"].values())
                   and out["ventilation_reads_no_L_or_G"] and not out["oxygenation_reads"] and not out["coupling_reads"]
                   and out["core_G_writers"] == 1 and not out["disease_terms_in_core_insertions"] and not modules)
    return out


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2P-2's view reads the P2P-2 files (proven), the registry without the PE
    family's types and P2O-1's family-module scan without the PE module, so every closed guard still reads the tree it
    froze."""
    patch.setattr(rd, "_live", p2p2_text)
    patch.setattr(pe, "_REGISTRY", p2p2_registry(pe._REGISTRY))
    patch.setattr(lw, "_REGISTRY", p2p2_registry(lw._REGISTRY))
    patch.setattr(go, "boundaries", p2p2_go_boundaries)


def upstream_unchanged() -> dict:
    text = json.dumps({"revision": rd.REVISION, "p2p1": hashlib.sha256(pe.RECORD.read_bytes()).hexdigest(),
                       "design": rd.design(), "sources": p2p2_sources(bf.freeze_sources())}, sort_keys=True, default=str)
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2p2_freeze_digest": hashlib.sha256(text.encode("utf-8")).hexdigest() == P2P2_FREEZE_DIGEST,
            "p2p2_record": hashlib.sha256(rd.RECORD.read_bytes()).hexdigest() == P2P2_RECORD_SHA}


P2P2_FREEZE_DIGEST = "5e705336b733be87c4bf1cc16fd8fdb664a11050aa9bed32ea82b539afe5f449"
P2P2_RECORD_SHA = "e362f67b073726cdb89520a25302ee3795c5eb2bfe654b75861adb556858e659"


# P2Q-2-18: the verdict (predeclared) -------------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "PE arrival mapping coherent (arrival exact where the core models it; V from the underfilled LV, the IVC not read; "
    "L 0; pump reserve neutral; the secondary neutral)",
    "obstructive / forward-flow failure uses existing channels cleanly (the writer writes P only; Q, MAP, DO2, the "
    "deficit and D follow in the common core; V, Hb and L untouched)",
    "no V / P double counting (no PE source writes V or the blood state; the arrival position never changes the arrival; "
    "the V mapping reads only the LV)",
    "PE owns L with zero generation (no common overload write, no L write; a second owner refused)",
    "fluid stress creates no false L (every LV-band point; SpO2 and G unchanged by the fluid)",
    "direct G path works (G linear, the common SpO2 mapping, delivery down, no L_rev credit)",
    "oxygen response common (monotone in FiO2, attenuated as G worsens, no family oxygen function)",
    "P2P-2 respiratory-drive architecture accepts hypoxaemia structurally (UNSET none, synthetic drives and grows; "
    "central depression still dominates)",
    "D / lactate remain common (arrival D latent, never from lactate; lactate the core's; kinetics untouched)",
    "collapse accepts the outputs structurally (signals rise, max holds, UNSET stays a lower bound, no family rule)",
    "no prior family retuned (GI, ACS, pulmonary edema, P2P-2 reproduced; tone and HR gains untouched; every common "
    "file at its P2P-2 bytes; the P2P-2 tree proven)",
)
READY = "PE_SHADOW_MIGRATION_READY"
NOT_READY = "PE_SHADOW_MIGRATION_NOT_READY"
VERDICT_RULE = ("Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion as "
                "the blocker. The HR, RR, consciousness and tone gaps, the lactate shape and the legacy differences are "
                "reported and never decide it")
RECOMMENDATION = {READY: "PROCEED_TO_P2R0_CROSS_FAMILY_GENERALIZATION_CHECKPOINT (read-only; do not tune PE)"}


def verdict(found: dict) -> dict:
    proof = found["proof"]
    values = (
        found["case"]["available"] and found["arrival"]["pass"] and found["secondary"]["arrival"]["pass"],
        found["writer"]["pass"] and found["obstruction"]["pass"],
        found["no_double_count"]["pass"],
        found["lung_water_owner"]["pass"],
        found["fluid_stress"]["pass"],
        found["direct_g"]["pass"],
        found["oxygen"]["pass"],
        found["respiratory_drive"]["pass"] and found["central_depression"]["pass"],
        found["d_lactate"]["pass"],
        found["collapse"]["pass"],
        found["non_regression"]["pass"] and found["tone"]["pass"] and found["heart_rate"]["pass"]
        and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2p2_freeze_digest"] and proof["p2p2_record"],
    )
    criteria = dict(zip(VERDICT_CRITERIA, values))
    blocker = next((name for name, ok in criteria.items() if not ok), None)
    return {"criteria": criteria, "ready": blocker is None, "blocker": blocker,
            "verdict": READY if blocker is None else f"{NOT_READY} — {blocker}",
            "recommendation": RECOMMENDATION[READY] if blocker is None else None}


def repeated_gaps(found: dict) -> dict:
    """The common gaps this migration met again, with the families each now appears in (data for P2R-0; nothing here is
    implemented or ranked)."""
    hr = found["heart_rate"]["cases"]
    return {
        "MULTI_FAMILY_COMMON_HR_GAP": {"families": ["acs", "pulmonary_edema", "pulmonary_embolism"],
                                       "pe": {n: hr[n]["mismatch_bpm"] for n in hr}},
        "PRESSURE_TONE_COMPENSATION": {"families": ["acs", "pulmonary_embolism"],
                                       "pe": {k: found["tone"][k] for k in ("T_change", "output_change", "map_change")},
                                       "class": "CROSS_FAMILY_COMMON_REFINEMENT_EVIDENCE_INCREASED"},
        "SIDED_PRELOAD_RIGHT_LEFT": {"families": ["pulmonary_embolism"],
                                     "status": "SIDED_PRELOAD_COMMON_STATE_DEFERRED: the false L is closed by family "
                                               "authority; ventricular interdependence (volume harm) is not representable"},
        "RESPIRATORY_DRIVE_AND_MECHANICS": {"families": ["pulmonary_edema", "pulmonary_embolism"],
                                            "pe_arrival_rr_gap": found["respiratory_drive"]["arrival_rr_gap"]},
        "ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE": {"families": ["pulmonary_edema", "pulmonary_embolism"]},
        "ARRIVAL_EXCESS_LACTATE_CLEARS_FIRST": {"families": ["pulmonary_edema", "pulmonary_embolism"],
                                                "pe": found["d_lactate"]["arrival_excess_clears_first"],
                                                "status": "reported, not a gap: the common kinetics are not retuned"}}


# Freeze and record -------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "cases": list(mr.CASES), "selection_rule": mr.SELECTION_RULE,
            "truth_paths": {k: list(v) for k, v in mr.TRUTH_PATHS.items()}, "truth_classes": TRUTH_CLASSES,
            "arrival_classes": mr.ARRIVAL_CLASSES, "channel_roles": mr.CHANNEL_ROLES,
            "observation_layer": mr.OBSERVATION_LAYER, "v_evidence": list(mr.V_EVIDENCE),
            "right_sided_observation": list(mr.RIGHT_SIDED_OBSERVATION), "l_evidence": list(mr.L_EVIDENCE),
            "loss_per_min": list(LOSS_PER_MIN), "floor": FLOOR, "g_rates": list(G_RATES), "horizon": HORIZON,
            "long_horizon": LONG_HORIZON, "read": list(READ), "long_read": list(LONG_READ), "fio2": list(FIO2),
            "fluid_stress": FLUID_STRESS, "rejected_ivc_preload": REJECTED_IVC_PRELOAD, "l_rev_probe": L_REV_PROBE,
            "hypoxaemic": {"mapping": [list(p) for p in rd.SYNTHETIC_MAPPING], "gain": HYPOXAEMIC_GAIN},
            "depression": DEPRESSION, "secondary_loss": list(SECONDARY_LOSS), "rr_gap": RR_GAP,
            "structural_ramp": list(an.STRUCTURAL_RAMP), "legacy_constants": LEGACY_CONSTANTS,
            "later_observations": LATER_OBSERVATIONS, "legacy_minutes": list(LEGACY_MINUTES),
            "forbidden_names": list(FORBIDDEN_NAMES), "verdict_criteria": list(VERDICT_CRITERIA),
            "verdict_rule": VERDICT_RULE, "recommendation": RECOMMENDATION, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}, "family_types": list(FAMILY_TYPES),
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2p2": CORE_AT_P2P2,
            "common_at_p2p2": COMMON_AT_P2P2,
            "p2p2": {"head": P2P2_HEAD, "freeze_digest": P2P2_FREEZE_DIGEST, "record": P2P2_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2p2": hashlib.sha256(rd.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "case": case(), "arrival": arrival(), "writer": writer_semantics(),
             "position": arrival_position_invariance(), "obstruction": obstruction_course(), "untreated": untreated()}
    found["no_double_count"] = no_double_count(found["untreated"], found["position"])
    found.update({"lung_water_owner": lung_water_owner(), "fluid_stress": fluid_stress(), "direct_g": direct_g(),
                  "oxygen": oxygen(), "respiratory_drive": respiratory_drive(),
                  "central_depression": central_depression()})
    found["tone"] = tone(found["untreated"])
    found["heart_rate"] = heart_rate(found["untreated"])
    found["d_lactate"] = d_lactate(found["untreated"])
    found["collapse"] = collapse()
    found["secondary"] = secondary()
    found["observables"] = {mr.CASE: observable_support(mr.CASE, found["arrival"], found["heart_rate"],
                                                        found["respiratory_drive"]),
                            mr.SECONDARY: observable_support(mr.SECONDARY, found["secondary"]["arrival"],
                                                             found["heart_rate"], None)}
    found["non_regression"] = non_regression()
    found["legacy"] = legacy()
    found["legacy_comparison"] = legacy_comparison(found["untreated"], found["legacy"])
    found["verdict"] = verdict(found)
    found["repeated_gaps"] = repeated_gaps(found)
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
