"""Phase 2 shadow core, P2O-1: the common lung-water / gas-exchange architecture (L -> G -> oxygenation -> delivery).

Shadow only. The core gains, off by default (three profile values None), the faculty's path (O3):

    lung water L  ->  gas exchange G  ->  SpO2 (oxygenation)  ->  oxygen content  ->  delivery  ->  deficit, D, lactate

- L stays a deviation from arrival (O1): L = 0 is the authored arrival lung state, never normal lungs.
- G is ONE effective gas-exchange impairment relative to arrival (O2): shunt, V/Q mismatch and diffusion stay latent.
- L -> G (derived.lung_water_gas_exchange, written by the integrator as a core coupling on G): G_from_L = gain x max(0, L),
  first order, monotone, zero at arrival, no threshold, no second time constant (O4).
- G -> oxygenation (derived.oxygenation): SpO2 = arrival SpO2 - scale x max(0, G) + spo2_per_fio2 x (benefit(FiO2) x
  retained(G) - benefit(arrival FiO2)), retained(G) = 1 / (1 + loss x max(0, G)): exact at G = 0, never better with G,
  never worse with FiO2, an incomplete FiO2 response with a severe G. Content and delivery follow through the core's
  existing delivery (output x Hb x SpO2), so D, lactate, the acid burden, the HR's hypoxaemia term, consciousness and
  the collapse layer's delivery signal see G only through oxygenation and delivery.
- No NIV (O5), no direct SpO2 collapse input (O6: DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED), no alveolar-gas hypoxaemia,
  no hypoxaemic drive, no P/V -> L, no RV / LV split, no ACS HR repair.

This module freezes, before any real case is evaluated: the audit, the semantics, the analytic comparison of the
L -> G forms, the G -> oxygenation structure, the SYNTHETIC_ONLY parameter region, the structural probes O1-O12, the
cross-family probes and criteria, the ACS and GI designs, the boundary checks, the verdict and recommendation rules,
and the proof that P2O-1 changed the two core files only by its declared, inert insertions, with the dependency map the
closed packages' freezes now rest on (``p2n2_sources``, ``p2n2_text``).

    python -m clinical_core.gas_exchange_architecture --digest
    python -m clinical_core.gas_exchange_architecture --out docs/revision/P2O1_gas_exchange.json
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import acs_migration as an
from . import acs_reference as ar
from . import blood_anchors as ba
from . import blood_fluid_calibration as bf
from . import collapse as cl
from . import derived as dv
from . import encephalopathy as enc
from . import vascular_tone as vt
from . import ventilation_surface as vs
from .bands import ARRIVAL, BloodLoss, Demand, Drift
from .interventions.oxygen import Oxygen
from .state import Anchors, Channel

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2O-1"
OWN = ("clinical_core/gas_exchange_architecture.py",)
REPORT = "clinical_core/gas_exchange_architecture_report.py"
RECORD = ROOT / "docs" / "revision" / "P2O1_gas_exchange.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2O1_INTERCAMBIO_GASEOSO_COMUN.md"
#: The analysis and its report leave the P2G pack digest; the report leaves the freeze sources (a downstream report).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
SYNTHETIC_ONLY, CANDIDATE, UNSET = "SYNTHETIC_ONLY", "CANDIDATE", "UNSET"

# The faculty's decisions (fixed for P2O-1) ---------------------------------------------------------------------------------

DECIDED = {
    "O1": "L remains a dynamic deviation from arrival: L = 0 is the authored arrival lung state (arrival congestion may "
          "already exist), L > 0 worsening, L < 0 improvement only if the channel domain allows it safely; arrival "
          "anchors are not changed to give L an absolute meaning",
    "O2": "G is one common gas-exchange impairment coordinate; shunt, V/Q mismatch and diffusion are not split (latent "
          "contributors to one effective G); a single-G causal contradiction across families stops the package",
    "O3": "the common path is L -> G -> oxygenation -> oxygen content / DO2; L writes no SpO2, DO2, D, lactate, RR, W, "
          "consciousness or collapse",
    "O4": "L -> G is monotonic, non-pathological, zero at L = 0 (arrival), never improves gas exchange when L worsens; "
          "clinical gain and thresholds UNSET; synthetic structural values for probes",
    "O5": "no NIV in P2O-1 (a future treatment-composition task)",
    "O6": "no direct SpO2 collapse input; collapse sees respiratory failure through oxygen delivery; P2M-2 unchanged",
}
CARRIED = {"M4": "COMMON_CONGESTION_GENERATION_GAP", "M5": "ACS_ARRIVAL_HR_COMMON_GAP_CANDIDATE",
           "RV_LV": "RV_LV_INTERDEPENDENCE_COMMON_GAP", "collapse_spo2": "DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED"}

# P2O-1A: the executable semantics before P2O-1 (85d18e6), audited from the code -------------------------------------------

AUDIT = {
    "L": {"writers": "core: derived.congestion_rate (excess preload above the knee x (1 - reserve x P)) and "
                     "lung_water_clearance (first order toward arrival, only above it); family: ACS IschaemicCongestion",
          "readers": "only its own clearance", "domain": "[-10, 10] guard (integration.CHANNEL_BOUNDS)",
          "arrival": "0", "kind": "deviation from arrival", "dynamic_family_use": "ACS (P2N-2 congestion writer)"},
    "G": {"writers": "none ('guard only; no module writes G yet')", "readers": "none",
          "domain": "[-10, 10] guard", "arrival": "0", "kind": "deviation from arrival ('shunt / V-Q impairment')",
          "dynamic_family_use": "none"},
    "W": {"writers": "none (channel); P2K-3 ventilation.ventilated_respiration computes an effective-ventilation W "
                     "(capacity / demand) that is not the channel",
          "readers": "the channel: only the pre-P2K-2 RR (derived.respiratory_rate); with the acid-base physiology on, "
                     "derived.respiration reads no W channel",
          "domain": "[-10, 10] guard", "arrival": "0 (channel); computed W 1 at baseline",
          "kind": "channel: deviation; computed W: ratio to need", "dynamic_family_use": "none"},
    "SpO2": {"writers": "derived (_perfusion): arrival SpO2 + spo2_per_fio2 x the oxygen benefit over arrival, cap 100",
             "readers": "delivery (relative_delivery), sympathetic hypoxaemia term, consciousness level (oxygen_levels), "
                        "encephalopathy hypoxaemia signal; collapse only through delivery",
             "domain": "[0, 100]", "arrival": "authored", "kind": "absolute observable anchored to arrival",
             "dynamic_family_use": "only through FiO2"},
    "FiO2": {"writers": "interventions.oxygen (SettingChange)", "readers": "SpO2", "domain": "[0.21, 1.0]",
             "arrival": "authored", "kind": "absolute setting", "dynamic_family_use": "orders"},
    "PaO2": {"writers": "none (authored at arrival only)", "readers": "none", "domain": "-", "arrival": "authored",
             "kind": "not represented", "dynamic_family_use": "none"},
    "PaCO2": {"writers": "derived.respiration (P2K-2: resting / ventilation, anchored to the arrival PaCO2); P2K-3 "
                         "closure: reference / W", "readers": "pH, encephalopathy hypercapnia",
              "domain": "positive or None without breathing", "arrival": "authored (anchored)",
              "kind": "absolute, derived", "dynamic_family_use": "none (through the acid burden only)"},
    "RR": {"writers": "derived (P2K-1 RR, or P2K-2 intrinsic + S(1 - exp(-drive / S)) with the acid drive)",
           "readers": "P2K-2 ventilation (RR x efficiency / intrinsic)", "domain": "[0, rr_max]",
           "arrival": "model (reported against the authored)", "kind": "absolute, derived",
           "dynamic_family_use": "none"},
    "acid_burden": {"writers": "integration._acid_burden (deficit_to_acid_gain x effective deficit, first-order "
                                "clearance)", "readers": "HCO3, respiratory drive",
                    "domain": ">= 0", "arrival": "max(0, reference - authored HCO3)", "kind": "absolute state",
                    "dynamic_family_use": "none (common)"},
    "oxygen_content": {"writers": "none as a state: Hb x SpO2 inside relative_delivery (dissolved O2 not modelled)",
                       "readers": "delivery", "domain": "-", "arrival": "relative 1",
                       "kind": "relative to arrival", "dynamic_family_use": "Hb through the blood state"},
    "DO2": {"writers": "derived.relative_delivery (output x Hb ratio x SpO2 ratio) x arrival_delivery_ratio",
            "readers": "deficit, D, lactate, acid burden, sympathetic acute term, encephalopathy, collapse",
            "domain": ">= 0", "arrival": "arrival_delivery_ratio", "kind": "relative to normal through the arrival "
                                                                            "layer", "dynamic_family_use": "all"},
}
AUDIT_COMPATIBLE = ("O1-O6 are compatible with the channel domains: L and G are already deviations from arrival on "
                    "[-10, 10] with no reader of G, SpO2 is derived in one place (derived._perfusion) and every reader "
                    "of oxygenation reads it there, collapse reads delivery only, and the respiratory closures read "
                    "neither L nor G")

# P2O-1B / C: the semantics P2O-1 accepts --------------------------------------------------------------------------------------

SEMANTICS = {
    "L": "lung water / congestion change: a dynamic deviation from the authored arrival lung state (O1); its own "
         "writers and clearance; it reaches oxygenation only through G",
    "G": "the effective gas-exchange impairment relative to arrival (O2, P2O-1C): G = 0 is the arrival gas exchange; "
         "a worse G never improves oxygenation; G changes no ventilation; L may raise it (the core coupling) and a "
         "family may write it through other mechanisms; no disease is named in it",
    "W": "ventilatory capacity / effective ventilation relative to need: unchanged by P2O-1 (P2K-2 / P2K-3); reads no "
         "L or G and is read by no oxygenation term",
    "RR": "the respiratory drive's observable rate (P2K-2): reads no L, G or SpO2 (no hypoxaemic drive in P2O-1)",
    "acid_burden": "metabolic acid physiology (P2K-2): produced by the effective oxygen deficit, read by HCO3 and the "
                   "drive; never written into or read from G",
    "SpO2": "the result of gas exchange G and inspired oxygen, anchored to the authored arrival",
}
SEMANTICS_BEFORE = {"L": AUDIT["L"]["kind"] + "; read by nothing but its clearance",
                    "G": AUDIT["G"]["kind"] + "; no writer, no reader", "W": AUDIT["W"]["kind"]}

# P2O-1D: L -> G, the forms compared analytically before any case -----------------------------------------------------------

L_TO_G_FORMS = {
    "linear_first_order": {"form": "G_L = k x max(0, L)", "parameters": ["k"], "status": "SELECTED",
                           "why": "the first-order term every smooth monotone L -> G with G(0) = 0 shares; continuous, "
                                  "monotone, zero at arrival, no threshold, one explicit gain, inactive at L = 0"},
    "saturating": {"form": "k x L / (1 + L / L_half)", "parameters": ["k", "L_half"], "status": "ELIMINATED",
                   "why": "reduces to the selected form to first order; L_half is a curvature with no authored data "
                          "(unidentifiable); the SpO2 mapping is already bounded"},
    "power": {"form": "k x max(0, L)^n", "parameters": ["k", "n"], "status": "ELIMINATED",
              "why": "n unidentifiable without authored courses; n = 1 is the selected form"},
    "threshold": {"form": "k x max(0, L - L0)", "parameters": ["k", "L0"], "status": "ELIMINATED",
                  "why": "needs a clinical threshold (O4: none) and is inert over a range of worsening lung water"},
    "lagged": {"form": "dG_L/dt = (k x max(0, L) - G_L) / tau", "parameters": ["k", "tau"], "status": "ELIMINATED",
               "why": "needs a new state for the L share of G and a second time constant: L's own writers and "
                      "clearance already carry the dynamics; tau is unidentifiable without authored courses"},
    "symmetric": {"form": "k x L (credits L < 0)", "parameters": ["k"], "status": "ELIMINATED",
                  "why": "an improvement below arrival needs a bound, the arrival congestion's share of the arrival "
                         "impairment, which O1 leaves unrepresented; any bound would be a new clinical value"},
}
L_TO_G_DECISION = ("NOT_A_SUBSTANTIVE_CHOICE: the selected form is the shared first-order term of the plausible forms; "
                   "every eliminated form adds an unidentifiable shape parameter, a threshold O4 forbids, a new state, "
                   "or an unbounded credit O1 leaves unrepresented. Curvature, lag and improvement below arrival stay "
                   "UNSET for the faculty")
G_TO_OXYGENATION = {
    "structure": "SpO2 = arrival SpO2 - s x max(0, G) + spo2_per_fio2 x (benefit(FiO2) x 1 / (1 + r x max(0, G)) - "
                 "benefit(arrival FiO2)), benefit(F) = max(0, F - 0.21), clamped to [0, 100]",
    "at_arrival": "exact: at G = 0 the expression is the core's SpO2 term by term",
    "monotone_in_G": "dSpO2/dG = -s + spo2_per_fio2 x benefit(FiO2) x d retained / dG <= -s < 0 for G > 0 (both terms "
                     "non-positive), whatever the arrival FiO2",
    "monotone_in_FiO2": "dSpO2/dFiO2 = spo2_per_fio2 x retained(G) > 0 above room air: never paradoxically worse",
    "incomplete_response": "retained(G) = 1 / (1 + r G) falls toward 0 with a severe G, never reaching it; r = 0 keeps "
                           "the full FiO2 response (a purely V/Q-like G)",
    "effective_shunt": "1 - retained(G): internal to the mapping (CANDIDATE / UNSET), never a shunt or V/Q state",
    "ventilation": "reads no ventilation, PaCO2, RR or acid burden: oxygenation impairment stays separable from "
                   "ventilation; hypoventilation reaches PaCO2, not G",
    "content_and_delivery": "unchanged: delivery = output x Hb ratio x SpO2 ratio (dissolved O2 not modelled); PaO2 "
                            "stays NOT_REPRESENTED (no dissociation curve)",
    "below_arrival": "G < 0 changes nothing (no credit below the arrival reference, as for L)",
}
FIO2_INTERACTION = ("FiO2 adds spo2_per_fio2 (ADOPTED, 30 points per unit) x its benefit over room air, scaled by the "
                    "share G keeps; the arrival FiO2's benefit is part of the authored arrival SpO2, so a patient who "
                    "arrived on oxygen loses part of it as G worsens, and a FiO2 rise always helps")
DEFERRED = {
    "alveolar_gas_hypoxaemia": "ALVEOLAR_GAS_OXYGENATION_DEFERRED: hypoventilation raises PaCO2 but lowers no SpO2 "
                               "(no alveolar gas equation; a faculty decision, TASK 3 (3))",
    "hypoxaemic_drive": "HYPOXAEMIC_DRIVE_DEFERRED: SpO2 reaches RR only through delivery and the acid burden",
    "pao2": "PAO2_NOT_REPRESENTED: no dissociation curve; SpO2 is the oxygenation observable",
    "family_oxygen_response": "SINGLE_G_OXYGEN_RESPONSE: one r for every family (O2); a family cannot declare a more "
                              "or less oxygen-responsive G at the same impairment",
    "dynamic_mechanics": "W_MECHANICS_DYNAMIC_WRITER_NOT_AVAILABLE: with the acid-base closure on, no channel carries "
                         "a dynamic ventilatory mechanics; the probes use the P2K-2 structural efficiency (static)",
    "niv": "NIV_NOT_MODELLED (O5)", "collapse_spo2": "DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED (O6)",
}

# P2O-1O: the SYNTHETIC_ONLY region, declared before any case ---------------------------------------------------------------

#: k: G per unit L above arrival; s: SpO2 points per unit G with no oxygen benefit; r: oxygen-benefit loss per unit G.
REFERENCE = {"lung_water_to_gas_exchange_gain": 1.0, "spo2_per_gas_exchange_unit": 5.0,
             "oxygen_response_loss_per_gas_exchange_unit": 0.5}
ONE_D = {"lung_water_to_gas_exchange_gain": (0.5, 1.0, 2.0), "spo2_per_gas_exchange_unit": (2.5, 5.0, 10.0),
         "oxygen_response_loss_per_gas_exchange_unit": (0.0, 0.5, 2.0)}
PARAMETER_STATUS = {
    "lung_water_to_gas_exchange_gain": {"default": UNSET, "probes": SYNTHETIC_ONLY, "approved": False},
    "spo2_per_gas_exchange_unit": {"default": UNSET, "probes": SYNTHETIC_ONLY, "approved": False},
    "oxygen_response_loss_per_gas_exchange_unit": {"default": UNSET, "probes": SYNTHETIC_ONLY, "approved": False,
                                                   "note": "its effective shunt-like share is CANDIDATE / UNSET"},
}
IDENTIFIABILITY = ("only k x s is identifiable from a lung-water course at room air; s alone from a family that writes "
                   "G; r only from an oxygen response; none is identifiable from the current authored truth (arrival "
                   "only)")


def gas_profile(base: dv.CoreProfile, **changes) -> dv.CoreProfile:
    return replace(base, **{**REFERENCE, **changes})


def off_profile(base: dv.CoreProfile) -> dv.CoreProfile:
    return replace(base, lung_water_to_gas_exchange_gain=None, spo2_per_gas_exchange_unit=None,
                   oxygen_response_loss_per_gas_exchange_unit=None)


def one_d_points() -> list:
    """The reference and each parameter's other values alone (no Cartesian product)."""
    points = [dict(REFERENCE)]
    for name, values in ONE_D.items():
        points.extend({**REFERENCE, name: value} for value in values if value != REFERENCE[name])
    return points


# The probe world: the synthetic neutral arrival and the common acid-base reference --------------------------------------------

NEUTRAL = Anchors(**ARRIVAL)
ON_OXYGEN = replace(NEUTRAL, case_id="band_probe_on_oxygen", fio2=0.4)
HORIZON = 60
VENTILATION_GAIN = vs.VENTILATION_GAINS[2]


def probe_profile(**changes) -> dv.CoreProfile:
    """The common reference profile P2N-2 predeclared (GI-carried uncertainty, the acid-base candidate on) with the
    gas-exchange reference: no ACS value enters it."""
    return gas_profile(ar.common_profile(), **changes)


def gas(state, anchors, profile) -> dict:
    """The respiratory readings at one state: the P2K-2 closure and the P2K-3 effective ventilation."""
    core = dv.respiration(state, anchors, profile)
    closure = vs._vr(state, anchors, profile, VENTILATION_GAIN)
    return {"rr": core.respiratory_rate, "ventilation_p2k2": core.ventilation, "paco2_p2k2": core.paco2,
            "ventilation": closure["w"], "paco2": closure["paco2"], "ph": closure["ph"], "burden": core.acid_burden}


def reading(state, anchors, profile) -> dict:
    d = dv.derive(state, anchors, profile)
    out = {"minute": state.minute, "L": state.L, "G": state.G, "fio2": state.fio2, "spo2": d.spo2, "D": state.D,
           "lactate": d.lactate, "delivery_index": dv.effective_delivery(d.delivery_rel, anchors),
           "deficit": dv.acute_deficit_signal(state, anchors, profile), "hr": d.monitor_rate_bpm, "map": d.map,
           "consciousness_level": d.consciousness_level}
    if dv.acid_base_active(profile):
        out.update(gas(state, anchors, profile))
    return out


def course(items, minutes, anchors, profile):
    return an.course(tuple(items), minutes, anchors, profile)


def at(state, **values):
    return state.evolve(**values)


# P2O-1G: structural probes O1-O12 ---------------------------------------------------------------------------------------------

G_LEVELS = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)
FIO2_LEVELS = (0.21, 0.3, 0.4, 0.6, 1.0)
PROBES = {
    "O1": "L = 0, G = 0: the arrival oxygenation (and every derived reading) is the core's without P2O-1",
    "O2": "L worsens (a declared lung-water drift): G never improves and equals k x max(0, L)",
    "O3": "G worsens with the ventilation fixed: oxygenation worsens",
    "O4": "G worsens with PaCO2 fixed: oxygenation worsens independently of ventilation",
    "O5": "FiO2 rises with a fixed mild G: oxygenation improves",
    "O6": "FiO2 rises with a severe G: the improvement is incomplete, never paradoxically worse",
    "O7": "RR changes (the intrinsic RR) with W and G fixed: the oxygenation path does not change",
    "O8": "W changes (the structural efficiency) with G fixed: PaCO2 changes, G and SpO2 do not",
    "O9": "the acid burden rises with G fixed: G unchanged",
    "O10": "lactate and D rise with G fixed: G unchanged",
    "O11": "L improves back toward arrival: G never worsens; L below arrival moves no G",
    "O12": "GI with L = 0: every respiratory and downstream reading is exactly the one without P2O-1",
}


def _strictly_down(values) -> bool:
    return all(b < a for a, b in zip(values, values[1:]))


def _worse(spo2) -> bool:
    """Never higher with a worse G, strictly lower wherever SpO2 is off its bounds (the 100 cap, the 0 floor)."""
    pairs = list(zip(spo2, spo2[1:]))
    return all(b <= a for a, b in pairs) and all(b < a for a, b in pairs if 0.0 < a < 100.0) and spo2[-1] < spo2[0]


def probe_o1() -> dict:
    out = {}
    for anchors in (NEUTRAL, ON_OXYGEN):
        for point in one_d_points():
            on = probe_profile(**point)
            off = off_profile(on)
            a_on, a_off = dv.arrival_state(anchors, on), dv.arrival_state(anchors, off)
            d_on, d_off = dv.derive(a_on, anchors, on), dv.derive(a_off, anchors, off)
            same = (d_on == d_off and a_on == a_off and gas(a_on, anchors, on) == gas(a_off, anchors, off)
                    and d_on.spo2 == anchors.spo2)
            out.setdefault(anchors.case_id, []).append(same)
    return {"anchors": {k: all(v) for k, v in out.items()}, "points": len(one_d_points()),
            "pass": all(all(v) for v in out.values())}


def probe_o2() -> dict:
    rows = []
    for k in ONE_D["lung_water_to_gas_exchange_gain"]:
        profile = probe_profile(lung_water_to_gas_exchange_gain=k)
        states, records = course((Drift("o2-l", "L", 0, HORIZON, 0.02),), HORIZON, NEUTRAL, profile)
        gs, ls = [s.G for s in states], [s.L for s in states]
        spo2 = [dv.derive(s, NEUTRAL, profile).spo2 for s in states]
        writers = sorted({d.source.key for r in records for d in r.deltas if d.channel is Channel.G})
        rows.append({"k": k, "L_end": ls[-1], "G_end": gs[-1], "spo2_end": spo2[-1],
                     "g_never_down": all(b >= a for a, b in zip(gs, gs[1:])),
                     "g_is_k_l": all(abs(g - k * max(0.0, l)) <= 1e-12 for g, l in zip(gs, ls)),
                     "spo2_never_up": all(b <= a for a, b in zip(spo2, spo2[1:])), "g_writers": writers})
    return {"rows": rows, "pass": all(r["g_never_down"] and r["g_is_k_l"] and r["spo2_never_up"]
                                      and r["g_writers"] == ["core_coupling:lung_water_gas_exchange"] for r in rows)}


def _static(anchors, profile, values) -> list:
    base = dv.arrival_state(anchors, profile)
    return [at(base, **v) for v in values]


def probe_o3_o4() -> dict:
    rows = []
    for point in one_d_points():
        profile = probe_profile(**point)
        for anchors in (NEUTRAL, ON_OXYGEN):
            for fio2 in (anchors.fio2, 0.6):
                states = _static(anchors, profile, [{"G": g, "fio2": fio2} for g in G_LEVELS])
                spo2 = [dv.derive(s, anchors, profile).spo2 for s in states]
                gases = [gas(s, anchors, profile) for s in states]
                rows.append({"point": point, "anchors": anchors.case_id, "fio2": fio2, "spo2": spo2,
                             "ventilation_fixed": len({(g["ventilation"], g["ventilation_p2k2"]) for g in gases}) == 1,
                             "paco2_fixed": len({(g["paco2"], g["paco2_p2k2"]) for g in gases}) == 1,
                             "rr_fixed": len({g["rr"] for g in gases}) == 1,
                             "worse": _worse(spo2)})
    o3 = all(r["ventilation_fixed"] and r["rr_fixed"] and r["worse"] for r in rows)
    o4 = all(r["paco2_fixed"] and r["worse"] for r in rows)
    return {"rows": rows, "O3": o3, "O4": o4}


def probe_o5_o6() -> dict:
    rows = []
    for point in one_d_points():
        profile = probe_profile(**point)
        for anchors in (NEUTRAL, ON_OXYGEN):
            curves = {}
            for g in (0.0, 0.5, 8.0):
                states = _static(anchors, profile, [{"G": g, "fio2": f} for f in FIO2_LEVELS if f >= anchors.fio2])
                curves[g] = [dv.derive(s, anchors, profile).spo2 for s in states]
            first_step = {g: c[1] - c[0] for g, c in curves.items()}
            rows.append({"point": point, "anchors": anchors.case_id, "curves": curves, "first_step": first_step,
                         "mild_improves": all(b >= a for a, b in zip(curves[0.5], curves[0.5][1:]))
                         and curves[0.5][-1] > curves[0.5][0],
                         "severe_never_worse": all(b >= a for a, b in zip(curves[8.0], curves[8.0][1:])),
                         "severe_incomplete": curves[8.0][-1] < curves[0.0][-1],
                         "severe_attenuated": first_step[8.0] < first_step[0.0]})
    o5 = all(r["mild_improves"] for r in rows)
    o6 = all(r["severe_never_worse"] and r["severe_incomplete"] for r in rows)
    strict = [r for r in rows if r["point"]["oxygen_response_loss_per_gas_exchange_unit"] > 0.0]
    return {"rows": rows, "O5": o5, "O6": o6,
            "attenuated_when_r_positive": all(r["severe_attenuated"] for r in strict)}


def probe_o7() -> dict:
    profile = probe_profile()
    rows = []
    for intrinsic in (12.0, 16.0, 20.0):
        anchors = replace(NEUTRAL, intrinsic_respiratory_rate=intrinsic)
        state = at(dv.arrival_state(anchors, profile), G=1.0)
        g = gas(state, anchors, profile)
        d = dv.derive(state, anchors, profile)
        rows.append({"intrinsic_rr": intrinsic, "rr": g["rr"], "ventilation": g["ventilation"], "spo2": d.spo2,
                     "delivery_rel": d.delivery_rel})
    return {"rows": rows, "rr_changes": len({r["rr"] for r in rows}) == 3,
            "w_fixed": len({r["ventilation"] for r in rows}) == 1,
            "pass": len({r["rr"] for r in rows}) == 3 and len({r["ventilation"] for r in rows}) == 1
            and len({(r["spo2"], r["delivery_rel"]) for r in rows}) == 1}


def probe_o8() -> dict:
    rows = []
    for efficiency in (1.0, 0.8, 0.6):
        profile = probe_profile(ventilation_efficiency=efficiency)
        state = at(dv.arrival_state(NEUTRAL, profile), G=1.0)
        g = gas(state, NEUTRAL, profile)
        rows.append({"efficiency": efficiency, "ventilation": g["ventilation"], "paco2": g["paco2"],
                     "paco2_p2k2": g["paco2_p2k2"], "G": state.G, "spo2": dv.derive(state, NEUTRAL, profile).spo2})
    return {"rows": rows, "paco2_rises": _strictly_down([-r["paco2"] for r in rows]),
            "pass": _strictly_down([-r["paco2"] for r in rows]) and len({(r["G"], r["spo2"]) for r in rows}) == 1,
            "deferred": DEFERRED["alveolar_gas_hypoxaemia"]}


def probe_o9_o10() -> dict:
    profile = probe_profile()
    states, records = course((BloodLoss("o9-bleed", 0, HORIZON, 8.0), Demand("o9-demand", 0, HORIZON, 1.5)),
                             HORIZON, NEUTRAL, profile)
    first, last = states[0], states[-1]
    return {"burden": [first.aux.metabolic_acid_burden, last.aux.metabolic_acid_burden], "D": [first.D, last.D],
            "lactate": [dv.derive(first, NEUTRAL, profile).lactate, dv.derive(last, NEUTRAL, profile).lactate],
            "G_max": max(abs(s.G) for s in states), "L_max": max(abs(s.L) for s in states),
            "G_writes": sum(1 for r in records for d in r.deltas if d.channel is Channel.G),
            "O9": last.aux.metabolic_acid_burden > first.aux.metabolic_acid_burden
            and all(s.G == 0.0 for s in states),
            "O10": last.D > first.D and all(s.G == 0.0 for s in states)}


def probe_o11() -> dict:
    profile = probe_profile()
    states, _ = course((Drift("o11-up", "L", 0, 30, 0.03),), 120, NEUTRAL, profile)
    ls, gs = [s.L for s in states], [s.G for s in states]
    falling = [(a, b) for (la, a), (lb, b) in zip(zip(ls, gs), zip(ls[1:], gs[1:])) if lb < la]
    below, _ = course((Drift("o11-down", "L", 0, 30, -0.03),), 60, NEUTRAL, profile)
    return {"L_peak": max(ls), "L_end": ls[-1], "G_peak": max(gs), "G_end": gs[-1], "falling_minutes": len(falling),
            "g_never_worse_while_l_improves": all(b <= a for a, b in falling),
            "below_arrival_L_min": min(s.L for s in below), "below_arrival_G": sorted({s.G for s in below}),
            "pass": bool(falling) and all(b <= a for a, b in falling) and {s.G for s in below} == {0.0}}


GI_CASES = (an.C57, "gi_bleed_72f")
GI_SCENARIOS = (("untreated", None), ("red_cells", None), ("crystalloid", 1000.0), ("stopped_bleed", None))


def _acid(profile):
    gain, b, tau = ar.COMMON_REFERENCE["acid"][0]
    return replace(profile, deficit_to_acid_gain=b / tau, acid_clearance_tau_min=tau, acid_to_drive_gain=gain,
                   ventilation_efficiency=1.0)


def _gi_reading(state, anchors, profile) -> tuple:
    d = dv.derive(state, anchors, profile)
    out = (state.to_dict(), d, enc.readings(state, anchors, profile, None), cl.readings(state, anchors, profile))
    if dv.acid_base_active(profile):
        out += (gas(state, anchors, profile),)
    return out


def probe_o12() -> dict:
    rows = []
    for case in GI_CASES:
        for scenario, volume in GI_SCENARIOS:
            anchors, base, values = ba.setup(case)
            items = ba.contributors(case, scenario, values, volume)
            for label, profile in (("certified", base), ("acid_base_on", _acid(base))):
                plain, _ = course(items, 120, anchors, profile)
                with_gas, records = course(items, 120, anchors, gas_profile(profile))
                same = [_gi_reading(s, anchors, profile) for s in plain] == \
                    [_gi_reading(s, anchors, gas_profile(profile)) for s in with_gas]
                rows.append({"case": case, "scenario": scenario, "profile": label, "identical": same,
                             "L_max": max(abs(s.L) for s in with_gas),
                             "G_writes": sum(1 for r in records for d in r.deltas if d.channel is Channel.G)})
    return {"rows": rows, "pass": all(r["identical"] and r["L_max"] == 0.0 and r["G_writes"] == 0 for r in rows)}


def structural_probes() -> dict:
    o34, o56, o910 = probe_o3_o4(), probe_o5_o6(), probe_o9_o10()
    results = {"O1": probe_o1(), "O2": probe_o2(), "O3_O4": o34, "O5_O6": o56, "O7": probe_o7(), "O8": probe_o8(),
               "O9_O10": o910, "O11": probe_o11(), "O12": probe_o12()}
    results["pass"] = {"O1": results["O1"]["pass"], "O2": results["O2"]["pass"], "O3": o34["O3"], "O4": o34["O4"],
                       "O5": o56["O5"], "O6": o56["O6"], "O7": results["O7"]["pass"], "O8": results["O8"]["pass"],
                       "O9": o910["O9"], "O10": o910["O10"], "O11": results["O11"]["pass"],
                       "O12": results["O12"]["pass"]}
    return results


# P2O-1H: cross-family structural probes (synthetic writers, common physiology only) ----------------------------------------

#: Each family's respiratory mechanism as declared synthetic inputs of the common core: which channels or structural
#: settings it moves, never a disease term in the core. SYNTHETIC_ONLY magnitudes, declared before any run.
FAMILIES = {
    "cardiogenic": {"writes": ("L",), "items": (("Drift", "L", 0.02),), "efficiency": 1.0, "bicarbonate": None,
                    "expect": {"L": "up", "G": "from L", "spo2": "down", "paco2": "not from G"}},
    "pneumonia": {"writes": ("G",), "items": (("Drift", "G", 0.02),), "efficiency": 1.0, "bicarbonate": None,
                  "expect": {"L": "none", "G": "written", "spo2": "down", "fio2": "responds, incompletely"}},
    "asthma": {"writes": ("W (structural efficiency)", "G"), "items": (("Drift", "G", 0.005),), "efficiency": 0.6,
               "bicarbonate": None, "expect": {"L": "none", "G": "secondary", "paco2": "up (dominant)"}},
    "opioid": {"writes": ("W (structural efficiency)",), "items": (), "efficiency": 0.5, "bicarbonate": None,
               "expect": {"L": "none", "G": "none", "paco2": "up", "spo2": "unchanged (alveolar-gas DEFERRED)"}},
    "pulmonary_embolism": {"writes": ("G", "W (dead space)"), "items": (("Drift", "G", 0.025),), "efficiency": 0.85,
                           "bicarbonate": None, "expect": {"L": "none", "G": "written (dominant)", "spo2": "down"}},
    # The core refuses a family T writer while its tone response is on (their composition is undecided, P2J-2): the
    # anaphylaxis probe turns the response off to let the family's vasoplegia write T.
    "anaphylaxis": {"writes": ("W (airway)", "G", "T"), "items": (("Drift", "G", 0.01), ("Drift", "T", -0.003)),
                    "efficiency": 0.7, "bicarbonate": None, "profile": {"deficit_to_tone_gain": 0.0},
                    "expect": {"L": "none", "G": "written", "paco2": "up", "MAP": "down (through T)"}},
    "metabolic_acidosis": {"writes": ("acid burden (arrival HCO3)",), "items": (), "efficiency": 1.0,
                           "bicarbonate": 14.0, "expect": {"L": "none", "G": "none", "rr": "up", "paco2": "down",
                                                           "spo2": "unchanged"}},
}


def _family_items(name: str) -> tuple:
    return tuple(Drift(f"xf-{name}-{i}", channel, 0, HORIZON, rate)
                 for i, (_, channel, rate) in enumerate(FAMILIES[name]["items"]))


def family_probe(name: str) -> dict:
    spec = FAMILIES[name]
    profile = probe_profile(ventilation_efficiency=spec["efficiency"], **spec.get("profile", {}))
    anchors = NEUTRAL if spec["bicarbonate"] is None else replace(NEUTRAL, case_id="band_probe_acidosis",
                                                                  arrival_bicarbonate=spec["bicarbonate"])
    states, records = course(_family_items(name), HORIZON, anchors, profile)
    first, last = reading(states[0], anchors, profile), reading(states[-1], anchors, profile)
    reference = reading(dv.arrival_state(NEUTRAL, probe_profile()), NEUTRAL, probe_profile())
    oxygen, _ = course(_family_items(name) + (Oxygen(f"xf-{name}-o2", HORIZON - 10, 0.6),), HORIZON, anchors, profile)
    with_o2 = reading(oxygen[-1], anchors, profile)
    g_from_l = all(abs(s.G - REFERENCE["lung_water_to_gas_exchange_gain"] * max(0.0, s.L)) <= 1e-12 for s in states) \
        if "L" in spec["writes"] else None
    return {"writes": list(spec["writes"]), "first": first, "last": last, "with_oxygen": with_o2,
            "reference_paco2": reference["paco2"], "reference_rr": reference["rr"],
            "L_max": max(s.L for s in states), "G_max": max(s.G for s in states), "g_from_l": g_from_l,
            "g_writers": sorted({d.source.key for r in records for d in r.deltas if d.channel is Channel.G}),
            "expect": spec["expect"]}


def cross_family() -> dict:
    rows = {name: family_probe(name) for name in FAMILIES}
    c, p, a, o, e, x, m = (rows[k] for k in FAMILIES)
    arrival = NEUTRAL.spo2
    checks = {
        "cardiogenic": c["L_max"] > 0.0 and c["g_from_l"] and c["last"]["spo2"] < arrival
        and c["g_writers"] == ["core_coupling:lung_water_gas_exchange"],
        "pneumonia": p["L_max"] == 0.0 and p["G_max"] > 0.0 and p["last"]["spo2"] < arrival
        and p["with_oxygen"]["spo2"] > p["last"]["spo2"],
        "asthma": a["L_max"] == 0.0 and 0.0 < a["G_max"] < p["G_max"] and a["last"]["paco2"] > a["reference_paco2"],
        "opioid": o["L_max"] == 0.0 and o["G_max"] == 0.0 and o["last"]["paco2"] > o["reference_paco2"]
        and o["last"]["spo2"] == arrival,
        "pulmonary_embolism": e["L_max"] == 0.0 and e["G_max"] > a["G_max"] and e["last"]["spo2"] < a["last"]["spo2"],
        "anaphylaxis": x["L_max"] == 0.0 and x["G_max"] > 0.0 and x["last"]["paco2"] > x["reference_paco2"]
        and x["last"]["map"] < x["first"]["map"],
        "metabolic_acidosis": m["L_max"] == 0.0 and m["G_max"] == 0.0 and m["first"]["rr"] > m["reference_rr"]
        and m["first"]["paco2"] < m["reference_paco2"] and m["first"]["spo2"] == arrival,
    }
    fingerprints = {name: (r["L_max"] > 0.0, r["G_max"] > 0.0, round(r["last"]["paco2"] - r["reference_paco2"], 6) > 0,
                           round(r["first"]["paco2"] - r["reference_paco2"], 6) < 0, r["last"]["spo2"] < arrival)
                    for name, r in rows.items()}
    distinct_inputs = len({tuple(FAMILIES[n]["writes"]) for n in FAMILIES}) == len(FAMILIES)
    return {"rows": rows, "checks": checks, "fingerprints": fingerprints, "distinct_inputs": distinct_inputs,
            "pass": all(checks.values()) and distinct_inputs,
            "single_g_note": DEFERRED["family_oxygen_response"]}


# P2O-1I: the cardiogenic case, evaluated only after the freeze -------------------------------------------------------------

ACS_MINUTES = (0, 30, 60, 90, 120)
LEGACY_SPO2 = {60: 90, 90: 88}          # an.LEGACY reference only (P2N-2 §11), never a target
ACS_OXYGEN = (60, 0.4)


def _acs_rows(states, anchors, profile) -> list:
    return [reading(states[m], anchors, profile) for m in ACS_MINUTES]


def acs_evaluation() -> dict:
    anchors = ar.anchors()
    base = ar.common_profile()
    items = an.writers()
    control, _ = course(items, an.HORIZON, anchors, base)
    runs = {}
    for point in one_d_points():
        key = json.dumps(point, sort_keys=True)
        profile = gas_profile(base, **point)
        states, records = course(items, an.HORIZON, anchors, profile)
        rows = _acs_rows(states, anchors, profile)
        ctrl = _acs_rows(control, anchors, base)
        k = point["lung_water_to_gas_exchange_gain"]
        runs[key] = {"point": point, "rows": rows,
                     "g_is_k_l": all(abs(s.G - k * max(0.0, s.L)) <= 1e-12 for s in states),
                     "spo2_never_up": all(b <= a for a, b in zip([dv.derive(s, anchors, profile).spo2 for s in states],
                                                                  [dv.derive(s, anchors, profile).spo2
                                                                   for s in states[1:]])),
                     "delivery_not_above_control": all(r["delivery_index"] <= c["delivery_index"] + 1e-12
                                                       for r, c in zip(rows, ctrl)),
                     "d_not_below_control": all(r["D"] >= c["D"] - 1e-12 for r, c in zip(rows, ctrl)),
                     "lactate_not_below_control": all(r["lactate"] >= c["lactate"] - 1e-12 for r, c in zip(rows, ctrl)),
                     "spo2_drop_120": rows[0]["spo2"] - rows[-1]["spo2"],
                     "pulse_kept": all(s.R.pulse_present for s in states),
                     "writes": sorted({d.source.key for r in records for d in r.deltas if d.channel is Channel.G})}
    reference = runs[json.dumps(REFERENCE, sort_keys=True)]
    minute, fio2 = ACS_OXYGEN
    profile = gas_profile(base)
    oxygen, _ = course(items + (Oxygen("acs-o2", minute, fio2),), an.HORIZON, anchors, profile)
    full, _ = course(items + (Oxygen("acs-o2", minute, fio2),), an.HORIZON, anchors,
                     gas_profile(base, oxygen_response_loss_per_gas_exchange_unit=0.0))
    return {"control": _acs_rows(control, anchors, base), "runs": runs,
            "arrival_exact": reference["rows"][0]["spo2"] == anchors.spo2 == ar.truth()["spo2"],
            "oxygen": {"order": {"minute": minute, "fio2": fio2}, "rows": _acs_rows(oxygen, anchors, profile),
                       "full_response_rows": _acs_rows(full, anchors,
                                                       gas_profile(base, oxygen_response_loss_per_gas_exchange_unit=0.0))},
            "legacy_reference_only": LEGACY_SPO2,
            "pass": all(r["g_is_k_l"] and r["spo2_never_up"] and r["delivery_not_above_control"]
                        and r["d_not_below_control"] and r["lactate_not_below_control"] and r["pulse_kept"]
                        for r in runs.values())}


# P2O-1L / K: consciousness and collapse compatibility (their modules unchanged) ---------------------------------------------

UNCHANGED_LAYERS = {"clinical_core/collapse.py": "6076dd315f8bd335af8a425ac4d78e3bcbbd5f1198b45e511b4f122532d65fc9",
                    "clinical_core/encephalopathy.py": "04aea64d6f2a23cf5a77a530114b3174eab9c9adc527708a97ac25f9c5ce3539",
                    "clinical_core/ventilation.py": "260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9"}
HYPOXAEMIA_MAPPING = enc.SignalMapping(normal=94.0, severe=80.0)      # SYNTHETIC_ONLY, the probe's ramp


def layers() -> dict:
    """The readers downstream of oxygenation at a state with an effective deficit (the O9 course's end: bleeding and
    a raised demand), G set from 0 to severe: the consciousness signal reads the one SpO2, the collapse layer reads
    the deficit only."""
    profile = probe_profile()
    mapping = enc.EncephalopathyProfile(mappings=(("hypoxaemia", HYPOXAEMIA_MAPPING),))
    states, _ = course((BloodLoss("layers-bleed", 0, HORIZON, 8.0), Demand("layers-demand", 0, HORIZON, 1.5)),
                       HORIZON, NEUTRAL, profile)
    rows = []
    for g in G_LEVELS:
        state = at(states[-1], G=g)
        reading_ = enc.readings(state, NEUTRAL, profile, None)
        signals = enc.acute_signals(reading_, mapping)
        collapse = cl.readings(state, NEUTRAL, profile)
        rows.append({"G": g, "spo2": dv.derive(state, NEUTRAL, profile).spo2, "enc_spo2": reading_["spo2"],
                     "hypoxaemia_signal": signals.value("hypoxaemia"),
                     "collapse_deficit": collapse["deficit_fraction"], "collapse_map": collapse["map"]})
    hashes = {k: hashlib.sha256((ROOT / k).read_bytes()).hexdigest() == v for k, v in UNCHANGED_LAYERS.items()}
    return {"rows": rows, "unchanged": hashes,
            "consciousness": all(r["spo2"] == r["enc_spo2"] for r in rows)
            and all(b >= a for a, b in zip([r["hypoxaemia_signal"] for r in rows],
                                           [r["hypoxaemia_signal"] for r in rows[1:]])),
            "collapse": all(b >= a for a, b in zip([r["collapse_deficit"] for r in rows],
                                                   [r["collapse_deficit"] for r in rows[1:]]))
            and rows[-1]["collapse_deficit"] > rows[0]["collapse_deficit"]
            and len({r["collapse_map"] for r in rows}) == 1 and "spo2" not in {v[0] for v in cl.INPUTS.values()}
            and all(hashes.values()),
            "direct_spo2_collapse": CARRIED["collapse_spo2"]}


# Boundaries: what reads and writes L and G (AST over the live core) ---------------------------------------------------------

DERIVED, INTEGRATION = "clinical_core/derived.py", "clinical_core/integration.py"
CORE_FILES = (DERIVED, INTEGRATION)
DISEASE_WORDS = ("cardiogenic", "pneumonia", "asthma", "opioid", "edema", "oedema", "acs", "coronary", "sepsis", "copd",
                 "ards", "heart")
DISEASE_PREFIXES = ("embol", "anaphyla", "infarct", "pulmonary_embol")


def disease_terms(text: str) -> list:
    """Whole words of ``text`` that name a disease (a word or a word prefix), case-insensitive."""
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    return sorted({w for w in words if w in DISEASE_WORDS or w.startswith(DISEASE_PREFIXES)})


def _functions(relative: str) -> dict:
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _attrs(node) -> set:
    """The names and attributes a function's body reads (its signature's annotations left out)."""
    body = node.body if isinstance(node, ast.FunctionDef) else [node]
    return {n.attr for item in body for n in ast.walk(item) if isinstance(n, ast.Attribute)} | \
        {n.id for item in body for n in ast.walk(item) if isinstance(n, ast.Name)}


def boundaries() -> dict:
    derived = _functions(DERIVED)
    readers_of = {name: sorted(fn for fn, node in derived.items() if name in _attrs(node))
                  for name in ("L", "G")}
    respiration_free = {fn: not ({"L", "G", "oxygenation", "lung_water_gas_exchange"} & _attrs(derived[fn]))
                        for fn in ("respiration", "respiratory_drive", "rate_from_drive", "alveolar_ventilation",
                                   "respiratory_rate", "acid_burden_after_minute", "lactate_after_minute",
                                   "congestion_rate", "relative_delivery", "effective_oxygen_deficit",
                                   "sympathetic_target")}
    ventilation = _functions("clinical_core/ventilation.py")
    ventilation_free = all(not ({"L", "G"} & _attrs(node)) for node in ventilation.values())
    oxygenation_reads = sorted(_attrs(derived["oxygenation"]) & {"L", "W", "D", "lactate", "respiratory_rate",
                                                                "paco2", "ventilation", "metabolic_acid_burden"})
    coupling_reads = sorted(_attrs(derived["lung_water_gas_exchange"]) - {"profile", "lung_water_to_gas_exchange_gain",
                                                                          "max", "before_l", "after_l"})
    integration = (ROOT / INTEGRATION).read_text(encoding="utf-8")
    g_deltas = integration.count("ChannelDelta(Channel.G")
    inserted = "\n".join(_inserted_sources(r) for r in CORE_FILES).lower()
    disease = disease_terms(inserted)
    modules = sorted(p.relative_to(ROOT).as_posix() for p in (CORE_DIR / "modules").glob("*.py")
                     if "Channel.G" in p.read_text(encoding="utf-8"))
    return {"readers_in_derived": readers_of, "respiration_and_downstream_read_no_L_or_G": respiration_free,
            "ventilation_reads_no_L_or_G": ventilation_free, "oxygenation_reads": oxygenation_reads,
            "coupling_reads": coupling_reads, "core_G_writers": g_deltas, "disease_terms_in_core_insertions": disease,
            "family_modules_writing_G": modules,
            "pass": readers_of["G"] == ["_perfusion"] and all(respiration_free.values()) and ventilation_free
            and not oxygenation_reads and not coupling_reads and g_deltas == 1 and not disease and not modules}


# The P2O-1 proof: the live core files are the P2N-2 files plus exactly the declared, inert insertions ------------------------

P2N2_HEAD = "85d18e6"
CORE_AT_P2N2 = {DERIVED: "b9056ada72f4c651974eccd1069a67097d31814a5d691cbfc883e33d85bb77a6",
                INTEGRATION: "dad171baff07805997272310f4f33545ed38956b531585ae246c0e26e8c07b7a"}
TUPLE_AT_P2N2 = {"clinical_core/lactate_slice.py": "e16c7a1590422df8f065923abd2579f797e323dd7493987f1663404e65b42cb2",
                 "clinical_core/decision_pack.py": "c9508f384b9d8e8266773b39cb2726321021717e81cd4ace19e85a462dfeca7b"}
P2N2_RECORD = ROOT / "docs" / "revision" / "P2N2_acs_migration.json"
P2N2_RECORD_SHA = "ef91ccc593669e73af615a1e57454ffa85fc0ee1af9100eb906e0f831d7b6816"
NAMES = frozenset({"LUNG_WATER_GAS_EXCHANGE", "gas_exchange_active", "lung_water_gas_exchange_active",
                   "lung_water_gas_exchange", "oxygen_response_retained", "oxygenation",
                   "lung_water_to_gas_exchange_gain", "spo2_per_gas_exchange_unit",
                   "oxygen_response_loss_per_gas_exchange_unit"})
NEW = {DERIVED: ("LUNG_WATER_GAS_EXCHANGE", "gas_exchange_active", "lung_water_gas_exchange_active",
                 "lung_water_gas_exchange", "oxygen_response_retained", "oxygenation"), INTEGRATION: ()}
CHANGED = {DERIVED: ("CoreProfile", "PARAMETERS", "_perfusion"), INTEGRATION: ("from .derived", "step")}
#: The only inserted checks inside an existing statement: raise-only, or guarded by an activation predicate that the
#: default profile (all three values None) keeps false.
GUARDS = {DERIVED: ast.dump(ast.parse("gas_exchange_active(profile)", mode="eval").body),
          INTEGRATION: ast.dump(ast.parse("lung_water_gas_exchange_active(profile)", mode="eval").body)}
#: What P2O-1 inserted in each file (``insertions_digest``), as frozen.
INSERTIONS_AT_P2O1 = {DERIVED: "4320e0dad01a1a330a2ee978bddb86018ba0efd3518b1b7e346bb1bd06c32cda",
                      INTEGRATION: "d5b9bf7251f1945cbb6b3b2db87e4a3173749c94f634b81194382848920f25ea"}


def _mentions(node) -> bool:
    return any((isinstance(n, ast.Name) and n.id in NAMES) or (isinstance(n, ast.Attribute) and n.attr in NAMES)
               for n in ast.walk(node))


def _key(node) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.ImportFrom):
        return f"from {'.' * node.level}{node.module or ''}"
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        return names[0] if names else None
    return None


def _raise_only(node) -> bool:
    return isinstance(node, ast.If) and not node.orelse and all(isinstance(item, ast.Raise) for item in node.body)


def _guarded(relative: str, node) -> bool:
    test = node.test
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        test = test.values[-1]
    return not node.orelse and ast.dump(test) == GUARDS[relative]


def _strip(relative: str, text: str) -> dict:
    lines = text.split("\n")
    tree = ast.parse(text)
    spans, dumps, problems = [], [], []

    def span(node, top=False):
        start, end = node.lineno, node.end_lineno
        while start > 1 and lines[start - 2].lstrip().startswith("#"):
            start -= 1
        if top and start > 1 and not lines[start - 2].strip() and end < len(lines) and not lines[end].strip():
            while start > 1 and not lines[start - 2].strip():
                start -= 1
        spans.append((start, end))
        dumps.append(ast.dump(node))

    for node in tree.body:
        key = _key(node)
        if key in NEW[relative]:
            span(node, top=True)
            continue
        if key not in CHANGED[relative]:
            if _mentions(node):
                problems.append(f"undeclared statement {key!r} names P2O-1")
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name) and sub.target.id in NAMES:
                if not (isinstance(sub.value, ast.Constant) and sub.value.value is None):
                    problems.append(f"{sub.target.id} is not None by default")
                span(sub)
            elif isinstance(sub, ast.Dict):
                for k, v in zip(sub.keys, sub.values):
                    if isinstance(k, ast.Constant) and k.value in NAMES:
                        spans.append((k.lineno, v.end_lineno))
                        dumps.append(ast.dump(k) + ast.dump(v))
            elif isinstance(sub, ast.If) and _mentions(sub.test):
                if not (_raise_only(sub) or _guarded(relative, sub)):
                    problems.append(f"an inserted check in {key} is neither raise-only nor guarded")
                span(sub)
            elif isinstance(sub, ast.ImportFrom):
                for line in sorted({a.lineno for a in sub.names if a.name in NAMES}):
                    on_line = [a for a in sub.names if a.lineno == line]
                    if not all(a.name in NAMES for a in on_line):
                        problems.append(f"line {line} mixes P2O-1 names with others")
                    spans.append((line, line))
                    dumps.append("|".join(a.name for a in on_line))
    drop = {i for start, end in spans for i in range(start, end + 1)}
    kept = "\n".join(line for i, line in enumerate(lines, 1) if i not in drop)
    return {"text": kept, "insertions": hashlib.sha256("\n".join(dumps).encode("utf-8")).hexdigest(),
            "problems": problems, "removed": [lines[i - 1] for i in sorted(drop)]}


def _live(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _inserted_sources(relative: str) -> str:
    return "\n".join(_strip(relative, _live(relative))["removed"])


def insertions_digest(relative: str, text: str | None = None) -> str:
    return _strip(relative, _live(relative) if text is None else text)["insertions"]


def proved(relative: str, text: str | None = None) -> bool:
    """The file (live, or ``text``) is the P2N-2 file byte for byte once P2O-1's declared insertions are removed, every
    inserted check inert under the default profile, the insertions what was frozen."""
    result = _strip(relative, _live(relative) if text is None else text)
    frozen = INSERTIONS_AT_P2O1[relative]
    return (not result["problems"] and hashlib.sha256(result["text"].encode("utf-8")).hexdigest()
            == CORE_AT_P2N2[relative] and (frozen is None or result["insertions"] == frozen))


def proofs() -> dict:
    return {relative: proved(relative) for relative in CORE_FILES}


def p2n2_text(relative: str) -> str:
    """The core file as P2N-2 left it (byte-identical, proven), or any other file as it is: the closed packages' text-
    based proofs read this in place of the live file."""
    if relative in CORE_FILES:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2N-2 file plus P2O-1's declared insertions")
        return _strip(relative, _live(relative))["text"]
    return _live(relative)


def p2n2_bytes(relative: str) -> bytes:
    return p2n2_text(relative).encode("utf-8") if relative in CORE_FILES else (ROOT / relative).read_bytes()


def p2n2_unchanged(pinned: dict) -> dict:
    """A closed package's byte check (its ``closed_unchanged`` / ``core_unchanged``) read through the P2N-2 view: each
    pinned file's hash, a core file's taken from its proven P2N-2 bytes."""
    return {relative: hashlib.sha256(p2n2_bytes(relative)).hexdigest() == sha for relative, sha in pinned.items()}


class P2N2Path(type(Path())):
    """A clinical_core path whose text is the P2N-2 file's for the two core files: the closed packages' AST scans (by
    path, file:line) read the core as P2N-2 left it, proven."""

    def read_text(self, *args, **kwargs):
        relative = self.relative_to(ROOT).as_posix()
        return p2n2_text(relative) if relative in CORE_FILES else super().read_text(*args, **kwargs)


def p2n2_path(path: Path) -> Path:
    return P2N2Path(path)


def p2n2_sources(sources: dict) -> dict:
    """A P2N-2 dependency map: P2O-1's module removed, the two tuple-only files at their P2N-2 hashes while only their
    tuples changed, and each core file at its P2N-2 hash when P2O-1 only inserted its declared, inert names there."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2N2.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(_live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    for relative in CORE_FILES:
        if relative in out and proved(relative):
            out[relative] = CORE_AT_P2N2[relative]
    return out


def upstream_unchanged() -> dict:
    mapped = p2n2_sources(bf.freeze_sources())
    return {"proofs": proofs(), "files": len(mapped),
            "digest": hashlib.sha256(json.dumps(mapped, sort_keys=True).encode("utf-8")).hexdigest(),
            "p2n2_record": hashlib.sha256(P2N2_RECORD.read_bytes()).hexdigest() == P2N2_RECORD_SHA}


# Verdict and recommendation (predeclared) -------------------------------------------------------------------------------------

VERDICT_CRITERIA = (
    "L, G and W causally distinct (boundaries, O3, O4, O7, O8)",
    "L can worsen G (O2, cardiogenic)",
    "G can worsen oxygenation (O3, O4)",
    "FiO2 response coherent (O5, O6)",
    "hypoventilation occurs independently of G (O8, opioid)",
    "pneumonia and PE use G without cardiogenic L",
    "metabolic acidosis needs no G (O9, metabolic acidosis)",
    "GI unchanged (O1, O12)",
    "consciousness coherent (one SpO2, its hypoxaemia signal monotone)",
    "collapse unchanged (P2M-2 untouched; delivery only)",
    "no clinical value approved (every new value UNSET by default, SYNTHETIC_ONLY in probes)",
)
RECOMMENDATION_RULE = (
    "Predeclared. With READY: A (CARDIOGENIC_CONGESTION_GENERATION) when the cardiogenic L -> G -> SpO2 chain acts only "
    "on a family-written L, i.e. the common P / V coupling still produces no lung water in the frozen P2N-2 fluid "
    "probe (COMMON_CONGESTION_GENERATION_GAP open); B (RESPIRATORY_TREATMENT_COMPOSITION) when the common coupling "
    "already produces L there; C and D are outside what P2O-1 can show and are never chosen by it")


def verdict(probes: dict, families: dict, acs: dict, layer: dict, bounds: dict, proof: dict) -> dict:
    p = probes["pass"]
    criteria = {
        VERDICT_CRITERIA[0]: bounds["pass"] and p["O3"] and p["O4"] and p["O7"] and p["O8"],
        VERDICT_CRITERIA[1]: p["O2"] and families["checks"]["cardiogenic"],
        VERDICT_CRITERIA[2]: p["O3"] and p["O4"],
        VERDICT_CRITERIA[3]: p["O5"] and p["O6"],
        VERDICT_CRITERIA[4]: p["O8"] and families["checks"]["opioid"],
        VERDICT_CRITERIA[5]: families["checks"]["pneumonia"] and families["checks"]["pulmonary_embolism"],
        VERDICT_CRITERIA[6]: p["O9"] and families["checks"]["metabolic_acidosis"],
        VERDICT_CRITERIA[7]: p["O1"] and p["O12"] and all(proof["proofs"].values()),
        VERDICT_CRITERIA[8]: layer["consciousness"],
        VERDICT_CRITERIA[9]: layer["collapse"],
        VERDICT_CRITERIA[10]: all(not s["approved"] for s in PARAMETER_STATUS.values())
        and all(getattr(dv.DEFAULT_PROFILE, k) is None for k in REFERENCE),
    }
    extra = {"O10": p["O10"], "O11": p["O11"], "cross_family": families["pass"], "acs_direction": acs["pass"],
             "acs_arrival_exact": acs["arrival_exact"]}
    ready = all(criteria.values()) and all(extra.values())
    failed = [k for k, v in {**criteria, **extra}.items() if not v]
    return {"criteria": criteria, "extra": extra,
            "verdict": "COMMON_GAS_EXCHANGE_ARCHITECTURE_READY_FOR_GENERALIZATION" if ready
            else "COMMON_GAS_EXCHANGE_ARCHITECTURE_NOT_READY — " + "; ".join(failed)}


def congestion_generation() -> dict:
    """The P2N-2 fluid probe re-read: does the common P / V coupling produce L on the cardiogenic arrival (M4)?"""
    anchors, profile = ar.anchors(), gas_profile(ar.common_profile())
    out = {}
    for volume in (1000.0, 4000.0):
        bag = replace(an._bag(), volume_ml=volume, untimed_rate_ml_per_min=volume / an.FLUID["duration_min"])
        states, _ = course((bag,), an.HORIZON, anchors, profile)
        out[str(volume)] = {"L_max": max(s.L for s in states), "G_max": max(s.G for s in states),
                            "position_max": max(dv.preload_position(s, anchors, profile) for s in states),
                            "knee": profile.congestion_preload_knee}
    return {"fluid": out, "gap_open": all(v["L_max"] == 0.0 for v in out.values())}


def recommendation(ready: bool, generation: dict) -> str | None:
    if not ready:
        return None
    return "CARDIOGENIC_CONGESTION_GENERATION" if generation["gap_open"] else "RESPIRATORY_TREATMENT_COMPOSITION"


# Freeze and record -------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "carried": CARRIED, "audit": AUDIT, "compatible": AUDIT_COMPATIBLE,
            "semantics": SEMANTICS, "semantics_before": SEMANTICS_BEFORE, "forms": L_TO_G_FORMS,
            "form_decision": L_TO_G_DECISION, "oxygenation": G_TO_OXYGENATION, "fio2": FIO2_INTERACTION,
            "deferred": DEFERRED, "reference": REFERENCE, "one_d": {k: list(v) for k, v in ONE_D.items()},
            "parameter_status": PARAMETER_STATUS, "identifiability": IDENTIFIABILITY, "probes": PROBES,
            "g_levels": list(G_LEVELS), "fio2_levels": list(FIO2_LEVELS), "horizon": HORIZON,
            "ventilation_gain": VENTILATION_GAIN, "families": {k: {**v, "items": [list(i) for i in v["items"]],
                                                                   "writes": list(v["writes"])}
                                                               for k, v in FAMILIES.items()},
            "gi": {"cases": list(GI_CASES), "scenarios": [list(s) for s in GI_SCENARIOS]},
            "acs": {"minutes": list(ACS_MINUTES), "oxygen": list(ACS_OXYGEN), "legacy_reference_only": LEGACY_SPO2},
            "hypoxaemia_mapping": [HYPOXAEMIA_MAPPING.normal, HYPOXAEMIA_MAPPING.severe],
            "verdict_criteria": list(VERDICT_CRITERIA), "recommendation_rule": RECOMMENDATION_RULE,
            "core": {"files": list(CORE_FILES), "at_p2n2": CORE_AT_P2N2, "new": {k: list(v) for k, v in NEW.items()},
                     "changed": {k: list(v) for k, v in CHANGED.items()}, "names": sorted(NAMES)},
            "own": list(OWN), "report": REPORT, "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "tuple_at_p2n2": TUPLE_AT_P2N2, "p2n2_record": P2N2_RECORD_SHA, "unchanged_layers": UNCHANGED_LAYERS}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2n2": hashlib.sha256(P2N2_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def run() -> dict:
    proof = upstream_unchanged()
    probes = structural_probes()
    families = cross_family()
    bounds = boundaries()
    layer = layers()
    acs = acs_evaluation()
    generation = congestion_generation()
    judged = verdict(probes, families, acs, layer, bounds, proof)
    ready = judged["verdict"].startswith("COMMON_GAS_EXCHANGE_ARCHITECTURE_READY")
    return _plain({"freeze_digest": freeze_digest(), "revision": REVISION, "design": design(), "proof": proof,
                   "probes": probes, "cross_family": families, "boundaries": bounds, "layers": layer, "acs": acs,
                   "congestion_generation": generation, "verdict": judged,
                   "recommendation": recommendation(ready, generation)})


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
