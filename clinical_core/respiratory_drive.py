"""Phase 2 shadow core, P2P-2: the common respiratory-drive composition (structural, uncalibrated).

Shadow only. P2P-2 makes the P2K-2 RR a composition of two layers the faculty separated (2026-11-04):

    excitatory_drive = acid_drive + hypoxaemic_drive            (breaths/min-equivalent; P2K-2's declared slot)
    excitatory_rr    = intrinsic_rr + S (1 - exp(-excitatory_drive / S))     (P2K-2's rate_from_drive, unchanged)
    expressed_rr     = central_drive_availability x excitatory_rr

The intrinsic RR is the baseline spontaneous drive; the hypoxaemic drive reads the CURRENT absolute SpO2 through a
mapping that stays UNSET; the availability (0 to 1, default 1) is the central machinery's share. With the mapping UNSET
and availability 1 every value is P2K-2's, bit for bit. No threshold, gain, curve or opioid mapping is chosen: every
value below is SYNTHETIC_ONLY and declared before any run. Mechanics, fatigue, NIV, alveolar gas and every family
migration stay outside.

This module freezes, before any evaluation: the audit of the P2P-1 respiratory drive (read from the P2P-1 core, proven),
the composition's semantics, the synthetic probe values, probes D1-D10, the pulmonary-edema, opioid and acidosis
diagnostics, the non-regression, the readiness rule, and the proof that the live core is the P2P-1 core plus exactly
these insertions. Closed packages read the P2P-1 tree through ``chain`` / ``p2p1_sources``.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import types
from dataclasses import astuple, fields, replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import derived as dv
from . import edema_migration as pe
from . import edema_reference as er
from . import gas_exchange_architecture as go
from . import lung_water_reference as lw
from .interventions.oxygen import Oxygen

ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2P-2"
DECIDED = "2026-11-04"
OWN = ("clinical_core/respiratory_drive.py",)
REPORT = "clinical_core/respiratory_drive_report.py"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
RECORD = ROOT / "docs" / "revision" / "P2P2_respiratory_drive.json"
DOC = ROOT / "docs" / "revision" / "P2P2_IMPULSO_RESPIRATORIO_COMUN.md"
CORE_FILE = "clinical_core/derived.py"

#: The faculty's decisions this package implements (2026-11-04), as classifications.
DECISIONS = {
    "ARRIVAL_RELATIVE_HYPOXEMIC_DRIVE": "REJECTED: a patient arriving at SpO2 81 % already has hypoxaemic drive",
    "ABSOLUTE_HYPOXEMIC_DRIVE": "STRUCTURALLY_AUTHORIZED: the drive reads the current absolute oxygenation",
    "hypoxaemia_clinical_mapping": "UNSET: no SpO2 or PaO2 threshold, gain or saturation curve is approved",
    "layers": "excitatory drive (baseline + acid + hypoxaemic + future excitatory terms) separate from the central drive "
              "availability; the expressed drive is availability x excitatory drive",
    "central_depression_reaches_baseline": "required: it lowers the intrinsic share too, never only the increments",
    "OPIOID_FAMILY_WRITER_DEFERRED": "only the common composition point is formalized; no opioid case is migrated",
    "RESPIRATORY_MECHANICS_EFFICIENCY_GAP": "drive and effective ventilation stay distinct; high RR with high PaCO2 "
                                            "(pulmonary_edema_58m) is not solved by drive",
    "EXPECTED_RESPIRATORY_MECHANICS_EXTENSION": "no fatigue, compliance, resistance, dead-space or dynamic work-of-"
                                                "breathing state",
    "L_rev": "0 for pulmonary_edema_58m (no authored post-arrival observation sets a reversible reserve; 'can be "
             "reduced' supports the concept, not a value); never fitted from the legacy",
    "COMMON_IVC_TO_PRELOAD_RULE_DEFERRED": "no universal IVC -> V; a family arrival mapping may read the IVC",
    "G_GUARD_SEMANTICS_DEBT": "the G guard is not modified; its current behaviour is recorded (G_GUARD below)",
    "ARRIVAL_HR_COMMON_GAP": "observed independently in ACS and pulmonary edema; HR is not reopened",
}

#: The G guard as it is (not modified by P2P-2): what P2P-1 recorded and P2O-3 implemented.
G_GUARD = ("integration bounds G with the channel guard; with L_rev = 0 the gas-exchange credit holds G at the P2O-1 "
           "value (no credit below arrival), with L_rev < 0 a G below 0 stops the run (UnresolvedBoundary). Decision 5 "
           "of P2P-1 (no special exception for L_rev = 0) and decision 4 (L_rev 0 preserves P2O-1) read differently "
           "for L_rev = 0: G_GUARD_SEMANTICS_DEBT, not blocking the drive architecture")


# P2P-2-1: the audit of the respiratory drive as P2P-1 left it (the P2P-1 core, proven) ------------------------------------------

PATH_AT_P2P1 = {
    "p2k2_candidate": [
        "intrinsic_rr = anchors.intrinsic_respiratory_rate, else the arrival RR (intrinsic_respiratory_rate)",
        "metabolic_acid_burden: aux state, dA = deficit_to_acid_gain x effective O2 deficit - A / acid_clearance_tau "
        "(integration._acid_burden); arrival burden = max(0, HCO3_reference - arrival HCO3)",
        "drive = acid_to_drive_gain x burden (respiratory_drive): the only driver; 'a hypoxaemic term is deferred, and "
        "later terms would add here'",
        "RR = min(rr_max, intrinsic + S (1 - exp(-drive / S))) (rate_from_drive), 0 without a pulse",
        "ventilation = ventilation_efficiency x RR / intrinsic / demand ratio (alveolar_ventilation); PaCO2 = arrival "
        "PaCO2 x arrival ventilation / ventilation; pH from HCO3 and PaCO2",
        "derive uses it whenever the acid-base physiology is declared (ACS and edema common profile)"],
    "p2k1_path": [
        "acid-base off (the default profile, the GI golden): respiratory_rate(state, anchors, profile, lactate)",
        "RR = max(0, 1 + min(0, W)) x (ventilatory + metabolic): ventilatory = (arrival RR - metabolic share) x (1 + "
        "max(0, W)); metabolic from lactate, anchored to arrival",
        "W below 0 is 'depressed drive: opioid, CNS', the only route to bradypnoea there; W above 0 is load"],
    "p2k3_candidate": [
        "shadow only (ventilation.py, never read by derive): W = efficiency x (1 + acid_to_ventilation_gain x burden) / "
        "demand ratio, PaCO2 = reference / W; W reads no RR"],
}
DEPRESSION_AT_P2P1 = {
    "p2k1_W_below_zero": "MIXED_DRIVE_AND_OUTPUT: W, the ventilation-relative-to-need channel, read as drive; blunts the "
                         "whole RR (intrinsic share included); only on the acid-base-off path",
    "bands_opioid_probe": "synthetic W -0.7 at minute 1 (bands 'opioid'): the P2K-1 route, a probe, not a family",
    "p2o1_cross_family_opioid": "ventilation_efficiency 0.5 (output side): PaCO2 up, RR unchanged, SpO2 unchanged "
                                "(alveolar gas deferred); no drive term",
    "p2k2_candidate": "NONE: the P2K-2 RR reads no W and no central-depression input",
}
HYPOXAEMIA_READERS_AT_P2P1 = {
    "heart_rate": "sympathetic_target: 0.02 x [max(0, 94 - SpO2) - max(0, 94 - arrival SpO2)]: ARRIVAL-RELATIVE (P2I-2AF)",
    "consciousness": "derive's ADOPTED absolute SpO2 ladder (87 / 80); P2L-2's hypoxaemia signal is a candidate not wired "
                     "into derive (ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY)",
    "respiratory_rate": "NONE (rr_audit: NOT_CURRENTLY_MODELED; acid_base: HYPOXEMIC_DRIVE_DEFERRED)",
    "oxygen_delivery": "SpO2 enters delivery (relative_delivery), hence the effective deficit and the acid burden: a "
                       "tissue route, not a chemoreflex",
}
CLASSIFICATION_AT_P2P1 = {
    "p2k2_candidate": "EXCITATORY_DRIVE_EXPLICIT (acid only) without a central-availability layer; the hypoxaemic slot "
                      "declared and empty; drive (-> RR) and effective ventilation (efficiency) separate",
    "p2k1_path": "MIXED_DRIVE_AND_OUTPUT (W read as both load and depression; lactate as the acid proxy)",
}


def _functions(text: str) -> dict:
    return {n.name: n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)}


def _names(node) -> set:
    out = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Attribute):
            out.add(x.attr)
        elif isinstance(x, ast.Name):
            out.add(x.id)
    return out


def audit() -> dict:
    """What the P2P-1 core's RR reads, from its text (the P2P-1 file, proven by the reversal)."""
    old = _functions(p2p1_text(CORE_FILE))
    resp, drive, rate, legacy = (_names(old[n]) for n in ("respiration", "respiratory_drive", "rate_from_drive",
                                                            "respiratory_rate"))
    reads = {"respiration_reads_spo2": "spo2" in resp or "_perfusion" in resp, "respiration_reads_W": "W" in resp,
             "drive_reads": sorted(drive - {"burden", "profile", "acid_to_drive_gain", "float", "CoreProfile"}),
             "drive_terms": sorted({"acid_to_drive_gain"} & drive),
             "rate_reads_availability": any("availab" in n for n in rate),
             "p2k1_reads_W": "W" in legacy, "p2k1_depression_factor": "max(0, 1 + min(0, W))"}
    out = {"path": PATH_AT_P2P1, "central_depression": DEPRESSION_AT_P2P1, "hypoxaemia_readers":
           HYPOXAEMIA_READERS_AT_P2P1, "classification": CLASSIFICATION_AT_P2P1, "reads": reads}
    out["pass"] = (not reads["respiration_reads_spo2"] and not reads["respiration_reads_W"]
                   and reads["drive_terms"] == ["acid_to_drive_gain"] and not reads["rate_reads_availability"]
                   and reads["p2k1_reads_W"])
    return out


# P2P-2-2 / 3 / 4 / 5: the composition's semantics -----------------------------------------------------------------------------

SEMANTICS = {
    "baseline_drive": "the intrinsic RR (anchors.intrinsic_respiratory_rate, else the arrival RR): the patient's RR "
                      "with no excitatory drive and an intact central machinery; never rewritten by the availability",
    "acid_drive": "acid_to_drive_gain x metabolic acid burden (P2K-2, unchanged); positive, excitatory",
    "hypoxaemic_drive": "hypoxaemic_to_drive_gain x the normalized signal of the CURRENT absolute SpO2 (the profile's "
                        "(SpO2, 0-1) points, linear between them); 0 when UNSET; it reads the SpO2 of the state, never "
                        "the arrival's: ABSOLUTE_HYPOXEMIC_DRIVE",
    "excitatory_drive": "acid_drive + hypoxaemic_drive, in breaths/min-equivalent, before the common saturation",
    "excitatory_rr": "rate_from_drive(excitatory_drive): the RR the excitatory drive gives with the central machinery "
                     "intact (intrinsic + S (1 - exp(-drive / S)), at most rr_max)",
    "central_drive_availability": "0 to 1, default 1 (no central depression): the central machinery's share of the "
                                  "excitatory drive it expresses; a profile-level structural input, as the ventilation "
                                  "efficiency is on the output side",
    "expressed_rr": "availability x excitatory_rr: below the intrinsic RR when the availability is low, 0 at 0",
}
AGGREGATION = ("FACULTY_CONCEPTUAL_SUM: the excitatory terms add in drive units in the slot P2K-2 declared ('later "
               "terms would add here'), then pass the one common saturation, so the RR response is sub-additive. "
               "Whether the clinical response to acid plus hypoxaemia is additive, maximal or synergistic is "
               "ACID_HYPOXAEMIA_INTERACTION_UNSET: with the hypoxaemic gain UNSET nothing numeric is decided, and the "
               "structural probes need only a monotone composition (D4 holds for a sum or a maximum alike)")
PLACEMENT = {
    "chosen": "POST_SATURATION: expressed_rr = availability x rate_from_drive(excitatory_drive). The saturation "
              "belongs to the excitatory (chemoreflex) response; the availability scales the central output. The RR is "
              "then never above availability x (intrinsic + S), whatever the excitatory drive: a depression of "
              "availability <= intrinsic / (intrinsic + S) keeps the RR at or below the intrinsic RR for every "
              "hypoxaemic or acid drive, without any value of the UNSET gains",
    "alternative": "PRE_SATURATION: RR = f(availability x (intrinsic + excitatory)) with f linear below the baseline. "
                   "It also lowers the baseline, but a large enough hypoxaemic drive would overcome any fixed "
                   "depression, so whether hypoxaemia forces tachypnoea would depend on the UNSET hypoxaemic gain",
    "shape": "PROPORTIONAL_ATTENUATION (the faculty's product): the availability scales the whole expressed drive, so "
             "relative responses are kept; whether central depression blunts the chemoreflex more than "
             "proportionally is CENTRAL_DEPRESSION_RESPONSE_SHAPE_UNSET",
    "rejected": ["subtracting from the hypoxaemic drive", "blocking only the increment above the intrinsic RR",
                 "competing with hypoxaemia after the intrinsic RR is added", "rewriting the intrinsic RR"],
}
ARRIVAL_ANCHOR = ("ARRIVAL_PACO2_ANCHOR_AT_THE_P2K2_REFERENCE: the resting PaCO2 stays read at P2K-2's arrival "
                  "ventilation (the acid drive only, availability 1, the reference efficiency), the rule P2K-2's review "
                  "set for the efficiency applied to the drive side: a central depression or a hypoxaemic drive moves "
                  "PaCO2 from the anchor, never absorbed by it, so central hypoventilation raises PaCO2 and lowers pH and "
                  "the same current RR gives the same PaCO2 whatever the arrival SpO2. The arrival PaCO2 is exact with "
                  "the defaults; with the new inputs active it departs from the authored one, reported (as a lower "
                  "efficiency's). The alternative, absorbing the arrival composition into the anchor, left a depressed "
                  "patient eucapnic (adversarial review, H1) and is rejected")
DEFERRED = {
    "OPIOID_FAMILY_WRITER_DEFERRED": "no opioid writer, case or mapping",
    "CENTRAL_AVAILABILITY_PER_MINUTE_ROUTE_DEFERRED": "the availability is static per run (a profile input); a writer "
                                                     "changing it over time (and its reversal) needs a state slot a "
                                                     "later package decides",
    "ONE_CENTRAL_DEPRESSION_SOURCE_ONLY": "the P2K-1 path's W < 0 depression stays on the acid-base-off path (closed, "
                                          "the GI golden); the two never act together (the profile refuses the "
                                          "composition without the P2K-2 physiology); at runtime integration one "
                                          "source remains",
    "DRIVE_TO_VENTILATION_SEMANTICS_SPLIT": "P2K-2 (derive) reads ventilation from RR x efficiency; P2K-3 (shadow) "
                                            "recruits W from the acid burden without RR; the drive layer is the same "
                                            "for both, the output link is a later decision",
    "HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED": "no alveolar gas: a lower RR raises PaCO2 but never lowers SpO2",
    "EXPECTED_RESPIRATORY_MECHANICS_EXTENSION": "no fatigue, compliance, resistance, dead-space or work state",
    "VNI_COMMON_EXTENSION_DEFERRED": "no NIV",
}

#: P2P-2-12: every respiratory parameter's state after P2P-2. None is approved.
PARAMETER_STATUS = {
    "hypoxaemic_drive_mapping": "UNSET (None)", "hypoxaemic_to_drive_gain": "UNSET (None)",
    "central_depression_family_mapping": "UNSET (no family maps an availability)",
    "central_drive_availability": "default 1 (no central depression)",
    "acid_drive_parameters": "unchanged (P2K-2: acid_to_drive_gain, deficit_to_acid_gain, acid_clearance_tau_min, "
                             "rr_drive_saturation)",
    "k": "UNSET (SYNTHETIC_ONLY reference 1 in P2O-1 probes only)",
    "s": "UNSET (SYNTHETIC_ONLY reference 5)", "r": "UNSET (SYNTHETIC_ONLY reference 0.5)",
}

# SYNTHETIC_ONLY probe values, declared before any run. None becomes approved.
#: A full-range linear table with no knee, so no clinical threshold appears: 0 at 100 %, 1 at 50 %.
SYNTHETIC_MAPPING = ((100.0, 0.0), (50.0, 1.0))
SYNTHETIC_GAINS = (5.0, 10.0)          # breaths/min-equivalent at the full normalized hypoxaemic drive
PROBE_INTRINSIC = 16.0                 # the band probe's RR (bands.ARRIVAL), read as intrinsic
PROBE_DRIVE = 6.0                      # one excitatory term (breaths/min-equivalent)
STRONG_DRIVE = 40.0                    # a large excitatory term
HUGE_DRIVE = 1.0e6                     # the bound's test: any excitatory input
AVAILABILITIES = (1.0, 0.75, 0.5, 0.25, 0.0)
STRONG_DEPRESSION = 0.3                # below intrinsic / (intrinsic + S) for the probe (16 / 41)
TOWARD_ZERO = (0.1, 0.01, 0.001, 0.0)
HYPOXAEMIC_SPO2 = 82.0                 # the synthetic depression probe's arrival SpO2
ACIDOSIS_BICARBONATE = 14.0            # P2O-1's cross-family metabolic acidosis probe
PROBE_MINUTES = 30
PE_FIO2 = 0.6


def base_profile(**changes) -> dv.CoreProfile:
    """P2O-1's probe profile (the ACS common point, acid-base on, gas-exchange reference) with the given changes."""
    return go.probe_profile(**changes)


def hypoxaemic(profile: dv.CoreProfile, gain: float, mapping=SYNTHETIC_MAPPING) -> dv.CoreProfile:
    return replace(profile, hypoxaemic_drive_mapping=mapping, hypoxaemic_to_drive_gain=gain)


def injected(profile: dv.CoreProfile, drive: float) -> dv.CoreProfile:
    """Option A: a hypoxaemic drive injected directly, a constant normalized 1 at every SpO2 times ``drive``."""
    return hypoxaemic(profile, drive, ((100.0, 1.0), (0.0, 1.0)))


def compose(acid: float, hypoxaemic_drive: float, availability: float, intrinsic: float = PROBE_INTRINSIC,
            spo2: float = HYPOXAEMIC_SPO2) -> dv.DriveComposition:
    """The core's own composition (dv._composition) with the given acid drive, an injected hypoxaemic drive (0: UNSET)
    and the availability."""
    profile = replace(base_profile(), central_drive_availability=availability)
    if hypoxaemic_drive:
        profile = injected(profile, hypoxaemic_drive)
    return dv._composition(intrinsic, acid, spo2 if hypoxaemic_drive else None, profile)


def _saturation() -> float:
    return base_profile().rr_drive_saturation


# P2P-2-6: probes D1-D10 ---------------------------------------------------------------------------------------------------------

PROBES = {
    "D1": "normal acid, normal oxygenation, availability 1: the baseline spontaneous drive (the intrinsic RR)",
    "D2": "acid drive only: the drive increases",
    "D3": "hypoxaemic drive only: the drive increases",
    "D4": "acid + hypoxaemia: never lower than either alone",
    "D5": "lower availability, excitatory inputs fixed: the expressed drive decreases",
    "D6": "strong central depression + hypoxaemia: no tachypnoea",
    "D7": "strong central depression + acid drive: no tachypnoea",
    "D8": "availability 1, hypoxaemic drive UNSET: the P2K / P2P respiratory behaviour reproduced exactly",
    "D9": "availability toward 0: severe bradypnoea / apnoea tendency, the intrinsic RR unchanged",
    "D10": "central depression changes drive only: G, SpO2, acid burden, DO2, D and lactate unchanged",
}


def probe_d1_d4() -> dict:
    d1 = compose(0.0, 0.0, 1.0)
    d2, d3, d4 = compose(PROBE_DRIVE, 0.0, 1.0), compose(0.0, PROBE_DRIVE, 1.0), compose(PROBE_DRIVE, PROBE_DRIVE, 1.0)
    unset = dv._composition(PROBE_INTRINSIC, 0.0, None, base_profile())
    return {"D1": {"expressed_rr": d1.expressed_rr, "baseline_rr": d1.baseline_rr, "unset": unset.expressed_rr,
                   "pass": d1.expressed_rr == PROBE_INTRINSIC == unset.expressed_rr and d1.excitatory_drive == 0.0},
            "D2": {"expressed_rr": d2.expressed_rr, "acid_drive": d2.acid_drive,
                   "pass": d2.expressed_rr > d1.expressed_rr and d2.hypoxaemic_drive == 0.0},
            "D3": {"expressed_rr": d3.expressed_rr, "hypoxaemic_drive": d3.hypoxaemic_drive,
                   "pass": d3.expressed_rr > d1.expressed_rr and d3.acid_drive == 0.0},
            "D4": {"expressed_rr": d4.expressed_rr, "excitatory_drive": d4.excitatory_drive,
                   "sub_additive": d4.expressed_rr - d1.expressed_rr < (d2.expressed_rr - d1.expressed_rr)
                   + (d3.expressed_rr - d1.expressed_rr),
                   "pass": d4.expressed_rr >= max(d2.expressed_rr, d3.expressed_rr)}}


def probe_d5() -> dict:
    rows = [compose(PROBE_DRIVE, PROBE_DRIVE, a) for a in AVAILABILITIES]
    rr = [r.expressed_rr for r in rows]
    fixed = len({(r.acid_drive, r.hypoxaemic_drive, r.excitatory_rr) for r in rows}) == 1
    return {"availability": list(AVAILABILITIES), "expressed_rr": rr, "excitatory_fixed": fixed,
            "pass": fixed and all(b < a for a, b in zip(rr, rr[1:]))}


def _depression(acid: float, hypox: float) -> dict:
    bound_availability = PROBE_INTRINSIC / (PROBE_INTRINSIC + _saturation())
    strong = compose(acid, hypox, STRONG_DEPRESSION)
    huge = compose(HUGE_DRIVE if acid else 0.0, HUGE_DRIVE if hypox else 0.0, STRONG_DEPRESSION)
    full = compose(acid, hypox, 1.0)
    bound = STRONG_DEPRESSION * (PROBE_INTRINSIC + _saturation())
    return {"availability": STRONG_DEPRESSION, "uniform_bound_availability": bound_availability,
            "full_availability_rr": full.expressed_rr, "depressed_rr": strong.expressed_rr,
            "depressed_rr_any_drive": huge.expressed_rr, "bound_rr": bound,
            "pass": full.expressed_rr > PROBE_INTRINSIC and strong.expressed_rr < PROBE_INTRINSIC
            and huge.expressed_rr <= bound + 1e-12 and bound <= PROBE_INTRINSIC
            and STRONG_DEPRESSION <= bound_availability}


def probe_d6_d7() -> dict:
    return {"D6": _depression(0.0, STRONG_DRIVE), "D7": _depression(STRONG_DRIVE, 0.0)}


def probe_d9() -> dict:
    rows = [compose(PROBE_DRIVE, PROBE_DRIVE, a) for a in TOWARD_ZERO]
    linear = all(abs(r.expressed_rr - a * r.excitatory_rr) <= 1e-12 for r, a in zip(rows, TOWARD_ZERO)) and \
        len({r.excitatory_rr for r in rows}) == 1
    a = er.anchors()
    states = []
    for availability in TOWARD_ZERO:
        prof = replace(pe.profile(), central_drive_availability=availability)
        states.append(dv.respiratory_drive_composition(dv.arrival_state(a, prof), a, prof))
    intrinsic_kept = all(s.baseline_rr == dv.intrinsic_respiratory_rate(a) for s in states)
    return {"availability": list(TOWARD_ZERO), "expressed_rr": [r.expressed_rr for r in rows], "linear": linear,
            "at_zero": rows[-1].expressed_rr, "edema_arrival_rr": [s.expressed_rr for s in states],
            "intrinsic_rr_unchanged": intrinsic_kept,
            "pass": linear and rows[-1].expressed_rr == 0.0 and intrinsic_kept and states[-1].expressed_rr == 0.0}


def _hypoxaemic_anchors():
    return replace(go.NEUTRAL, case_id="p2p2_hypoxaemic_probe", spo2=HYPOXAEMIC_SPO2)


def _state_view(state) -> dict:
    return state.to_dict()


def probe_d10() -> dict:
    """Two runs of one synthetic hypoxaemic state, availability 1 and strong depression: every state and every derived
    reading but RR identical; the respiratory readings that differ are RR, ventilation, PaCO2 and pH only, and the
    depressed run hypoventilates (lower RR, higher PaCO2, lower pH)."""
    a = _hypoxaemic_anchors()
    runs = {}
    for availability in (1.0, STRONG_DEPRESSION):
        prof = replace(hypoxaemic(base_profile(), SYNTHETIC_GAINS[1]), central_drive_availability=availability)
        states, _ = go.course((), PROBE_MINUTES, a, prof)
        runs[availability] = (states, prof)
    (s1, p1), (s2, p2) = runs[1.0], runs[STRONG_DEPRESSION]
    same_states = [_state_view(x) for x in s1] == [_state_view(x) for x in s2]
    d1 = [dv.derive(x, a, p1).to_dict() for x in s1]
    d2 = [dv.derive(x, a, p2).to_dict() for x in s2]
    differing = sorted({k for x, y in zip(d1, d2) for k in x if x[k] != y[k]})
    unchanged = {k: all(getattr(x, k) == getattr(y, k) for x, y in zip(s1, s2)) for k in ("G", "D", "L")}
    unchanged["acid_burden"] = all(x.aux.metabolic_acid_burden == y.aux.metabolic_acid_burden for x, y in zip(s1, s2))
    unchanged.update({k: all(x[k] == y[k] for x, y in zip(d1, d2)) for k in ("spo2", "delivery_rel", "lactate",
                                                                            "monitor_rate_bpm", "consciousness_level")})
    r1, r2 = dv.respiration(s1[-1], a, p1), dv.respiration(s2[-1], a, p2)
    hypoventilation = r2.respiratory_rate < r1.respiratory_rate and r2.paco2 > r1.paco2 and r2.ph < r1.ph
    return {"states_identical": same_states, "derived_fields_differing": differing, "unchanged": unchanged,
            "rr": [r1.respiratory_rate, r2.respiratory_rate], "paco2": [r1.paco2, r2.paco2], "ph": [r1.ph, r2.ph],
            "depression_raises_paco2_lowers_ph": hypoventilation,
            "pass": same_states and differing == ["respiratory_rate"] and all(unchanged.values()) and hypoventilation}


# D8: the P2P-1 core, executed beside the live one ---------------------------------------------------------------------------

def p2p1_core():
    """The P2P-1 derived.py (proven by the reversal), executed as its own module beside the live one."""
    name = "clinical_core._derived_at_p2p1"
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    exec(compile(p2p1_text(CORE_FILE), "derived_at_p2p1.py", "exec"), module.__dict__)
    return module


def _old_profile(old, profile):
    names = {f.name for f in fields(old.CoreProfile)}
    extra = {f.name for f in fields(dv.CoreProfile)} - names
    if any(getattr(profile, n) != getattr(dv.DEFAULT_PROFILE, n) for n in extra):
        raise AssertionError("D8 compares profiles with the P2P-2 inputs at their defaults only")
    return old.CoreProfile(**{n: getattr(profile, n) for n in names})


def _equivalent(states, anchors, profile, old) -> bool:
    op = _old_profile(old, profile)
    for s in states:
        if dv.derive(s, anchors, profile).to_dict() != old.derive(s, anchors, op).to_dict():
            return False
        if dv.acid_base_active(profile) and astuple(dv.respiration(s, anchors, profile)) != \
                astuple(old.respiration(s, anchors, op)):
            return False
    if dv.acid_base_active(profile):
        if dv.respiratory_rate_decomposition(anchors, profile) != old.respiratory_rate_decomposition(anchors, op):
            return False
        if dv.arrival_alveolar_ventilation(anchors, profile) != old.arrival_alveolar_ventilation(anchors, op):
            return False
    return True


def probe_d8() -> dict:
    """The P2P-1 derive and respiration on the same courses as the live ones. The states come from the live integrator,
    which P2P-2 never changes (integration.py is pinned at its P2P-1 bytes) and which reads none of the changed
    functions: the courses are the P2P-1 courses, so only the readings can differ."""
    old = p2p1_core()
    rows = []
    for case in go.GI_CASES:
        for scenario, volume in go.GI_SCENARIOS:
            anchors, base, values = go.ba.setup(case)
            items = go.ba.contributors(case, scenario, values, volume)
            for label, profile in (("certified", base), ("acid_base_on", go._acid(base))):
                states, _ = go.course(items, 120, anchors, profile)
                rows.append({"family": "gi", "case": case, "scenario": scenario, "profile": label,
                             "identical": _equivalent(states, anchors, profile, old)})
    acs_anchors, acs_profile = go.ar.anchors(), go.gas_profile(go.ar.common_profile())
    states, _ = go.course(go.an.writers(), go.an.HORIZON, acs_anchors, acs_profile)
    rows.append({"family": "acs", "case": go.ar.CASE, "identical": _equivalent(states, acs_anchors, acs_profile, old)})
    for rate in pe.PROGRESSION:
        for fio2 in (None, PE_FIO2):
            items = (pe.writer(rate),) + (() if fio2 is None else (Oxygen("p2p2-o2", 0, fio2),))
            states, _ = pe.course(items)
            rows.append({"family": "pulmonary_edema", "progression": rate, "fio2": fio2,
                         "identical": _equivalent(states, er.anchors(), pe.profile(), old)})
    acidosis = replace(go.NEUTRAL, case_id="p2p2_acidosis_probe", arrival_bicarbonate=ACIDOSIS_BICARBONATE)
    states, _ = go.course((), PROBE_MINUTES, acidosis, base_profile())
    rows.append({"family": "metabolic_acidosis_probe", "identical": _equivalent(states, acidosis, base_profile(), old)})
    return {"rows": rows, "compared": len(rows), "pass": all(r["identical"] for r in rows)}


def structural_probes() -> dict:
    d14 = probe_d1_d4()
    d67 = probe_d6_d7()
    out = {**d14, "D5": probe_d5(), **d67, "D8": probe_d8(), "D9": probe_d9(), "D10": probe_d10()}
    out["pass"] = {k: out[k]["pass"] for k in PROBES}
    return out


# P2P-2-3: the hypoxaemic input is absolute -------------------------------------------------------------------------------------

ABSOLUTE_ARRIVALS = (97.0, 91.0, 85.0)
ABSOLUTE_CURRENT_SPO2 = 85.0


def absolute_check() -> dict:
    """The same current SpO2 drives the same whatever the arrival SpO2 (states built to read 85 % from arrivals at 97,
    91 and 85 %, the gap made by G); an arrival at 81 % already drives, and the arrival composition is the arrival
    state's; the core's hypoxaemic functions read no arrival value."""
    prof = hypoxaemic(base_profile(), SYNTHETIC_GAINS[1])
    same_now = {}
    for arrival in ABSOLUTE_ARRIVALS:
        a = replace(go.NEUTRAL, case_id=f"p2p2_absolute_{arrival:g}", spo2=arrival)
        state = dv.arrival_state(a, prof).evolve(G=(arrival - ABSOLUTE_CURRENT_SPO2) / prof.spo2_per_gas_exchange_unit)
        c = dv.respiratory_drive_composition(state, a, prof)
        same_now[f"{arrival:g}"] = {"current_spo2": c.spo2, "hypoxaemic_drive": c.hypoxaemic_drive,
                                    "rr": c.expressed_rr, "paco2": dv.respiration(state, a, prof).paco2}
    drives = [v["hypoxaemic_drive"] for v in same_now.values()]
    paco2 = [v["paco2"] for v in same_now.values()]
    a81 = replace(_hypoxaemic_anchors(), spo2=81.0)
    at_81 = dv.arrival_drive_composition(a81, prof)
    at_81_state = dv.respiratory_drive_composition(dv.arrival_state(a81, prof), a81, prof)
    live = _functions((ROOT / CORE_FILE).read_text(encoding="utf-8"))
    reads_arrival = {n: bool({"anchors", "Anchors"} & _names(live[n])) for n in ("hypoxaemic_drive_signal",
                                                                                  "hypoxaemic_drive", "_composition",
                                                                                  "expressed_respiratory_rate")}
    same_spo2 = all(abs(v["current_spo2"] - ABSOLUTE_CURRENT_SPO2) <= 1e-9 for v in same_now.values())
    return {"current_85_from_arrivals": same_now, "arrival_81_drive": at_81.hypoxaemic_drive,
            "arrival_composition_is_state_composition": at_81 == at_81_state, "reads_arrival": reads_arrival,
            "same_paco2": max(paco2) - min(paco2) <= 1e-9,
            "pass": same_spo2 and max(drives) - min(drives) <= 1e-12 and max(paco2) - min(paco2) <= 1e-9
            and at_81.hypoxaemic_drive > 0.0
            and at_81 == at_81_state and not any(reads_arrival.values())}


# P2P-2-7 / 8: pulmonary edema, diagnostic only ------------------------------------------------------------------------------------

def _pe_rows(states, prof) -> dict:
    a = er.anchors()
    rows = {}
    for m in pe.READ:
        d, r = dv.derive(states[m], a, prof), dv.respiration(states[m], a, prof)
        c = dv.respiratory_drive_composition(states[m], a, prof)
        rows[str(m)] = {"spo2": d.spo2, "rr": r.respiratory_rate, "paco2": r.paco2, "acid_drive": c.acid_drive,
                        "hypoxaemic_drive": c.hypoxaemic_drive, "hr": d.monitor_rate_bpm,
                        "consciousness_level": d.consciousness_level}
    return rows


def pulmonary_edema_diagnostic() -> dict:
    """pulmonary_edema_58m with P2P-1's writer (middle progression), room air and FiO2 0.6: the P2P-1 baseline (UNSET)
    and each synthetic gain. The question is the direction of RR, never its value; no gain is chosen from the case. Each
    excitatory share is read apart (the hypoxaemic share as SpO2 falls, the acid share as the arrival burden clears)
    and the net RR beside them; the drive-to-PaCO2 relation is read across the runs."""
    a, authored = er.anchors(), er.truth()
    out = {"authored": {"rr": authored["respiratory_rate"], "paco2": authored["abg_paco2"]}, "runs": {}}
    for label, gain in (("unset", None),) + tuple((f"synthetic_{g:g}", g) for g in SYNTHETIC_GAINS):
        prof = pe.profile() if gain is None else hypoxaemic(pe.profile(), gain)
        room, _ = pe.course((pe.writer(),), prof=prof)
        o2, _ = pe.course((pe.writer(), Oxygen("p2p2-pe-o2", 0, PE_FIO2)), prof=prof)
        comp = [dv.respiratory_drive_composition(s, a, prof) for s in room]
        rr_room = [c.expressed_rr for c in comp]
        rr_o2 = [dv.respiration(s, a, prof).respiratory_rate for s in o2]
        hypox = [c.hypoxaemic_drive for c in comp]
        out["runs"][label] = {"room_air": _pe_rows(room, prof), "fio2": _pe_rows(o2, prof),
                              "arrival_rr": rr_room[0], "gap_to_authored_rr_at_arrival":
                              authored["respiratory_rate"] - rr_room[0],
                              "hypoxaemic_share_rises_as_spo2_falls": pe._nondecreasing(hypox) and hypox[-1] > hypox[0],
                              "acid_share_trend": comp[-1].acid_drive - comp[0].acid_drive,
                              "net_rr_trend": rr_room[-1] - rr_room[0],
                              "oxygen_lowers_rr": all(x <= y + 1e-12 for x, y in zip(rr_o2[1:], rr_room[1:]))
                              and rr_o2[-1] < rr_room[-1]}
    labels = ["unset"] + [f"synthetic_{g:g}" for g in SYNTHETIC_GAINS]
    runs = [out["runs"][k] for k in labels]
    synth = runs[1:]
    arrival_rr = [r["arrival_rr"] for r in runs]
    last = [(r["room_air"][str(pe.READ[-1])]["rr"], r["room_air"][str(pe.READ[-1])]["paco2"]) for r in runs]
    out["arrival_rr_rises_with_hypoxaemic_drive"] = all(b > a for a, b in zip(arrival_rr, arrival_rr[1:]))
    out["higher_drive_lower_paco2"] = all(b[0] > a[0] and b[1] < a[1] for a, b in zip(last, last[1:]))
    out["direction_sensible"] = out["arrival_rr_rises_with_hypoxaemic_drive"] and all(
        r["hypoxaemic_share_rises_as_spo2_falls"] and r["oxygen_lowers_rr"] for r in synth)
    out["net_rr_rises"] = {k: out["runs"][k]["net_rr_trend"] > 0.0 for k in labels}
    out["net_direction"] = ("NET_RR_TREND_DEPENDS_ON_UNSET_GAIN: the hypoxaemic share rises as SpO2 falls while the "
                            "acid share falls as the arrival burden clears; which wins over the untreated course is a "
                            "matter of the UNSET hypoxaemic gain, not of the architecture")
    out["mechanics_gap"] = out["higher_drive_lower_paco2"]
    out["classification"] = ("RESPIRATORY_MECHANICS_EFFICIENCY_GAP: a stronger drive gives a higher RR and a LOWER PaCO2 "
                             "through P2K-2's ventilation, while the authored patient has RR 38 with PaCO2 49: drive "
                             "alone cannot give high RR with high PaCO2 (EXPECTED_RESPIRATORY_MECHANICS_EXTENSION)")
    out["gain_from_case"] = False
    out["pass"] = out["direction_sensible"]
    return out


# P2P-2-9 / 10: cross-family structural probes ---------------------------------------------------------------------------------------

def opioid_probe() -> dict:
    """A synthetic state with marked central depression and hypoxaemia, otherwise the band probe's physiology; no opioid
    term, writer or case."""
    a = _hypoxaemic_anchors()
    out = {}
    for label, gain, availability in (("hypoxaemia_intact", SYNTHETIC_GAINS[1], 1.0),
                                      ("hypoxaemia_depressed", SYNTHETIC_GAINS[1], STRONG_DEPRESSION),
                                      ("strong_hypoxaemic_drive_depressed", HUGE_DRIVE, STRONG_DEPRESSION)):
        prof = replace(hypoxaemic(base_profile(), gain), central_drive_availability=availability)
        states, _ = go.course((), PROBE_MINUTES, a, prof)
        c = dv.respiratory_drive_composition(states[-1], a, prof)
        d = dv.derive(states[-1], a, prof)
        out[label] = {"spo2": d.spo2, "hypoxaemic_drive": c.hypoxaemic_drive, "excitatory_rr": c.excitatory_rr,
                      "expressed_rr": c.expressed_rr, "intrinsic_rr": c.baseline_rr,
                      "paco2": dv.respiration(states[-1], a, prof).paco2, "hr": d.monitor_rate_bpm,
                      "consciousness_level": d.consciousness_level}
    intact, depressed, strong = (out[k] for k in ("hypoxaemia_intact", "hypoxaemia_depressed",
                                                  "strong_hypoxaemic_drive_depressed"))
    out["checks"] = {"hypoxaemia_drives_when_intact": intact["expressed_rr"] > intact["intrinsic_rr"],
                     "depression_dominates": depressed["expressed_rr"] < depressed["intrinsic_rr"],
                     "dominates_any_hypoxaemic_drive": strong["expressed_rr"] < strong["intrinsic_rr"],
                     "spo2_unchanged_by_depression": intact["spo2"] == depressed["spo2"],
                     "depression_raises_paco2": depressed["paco2"] > intact["paco2"],
                     "hr_consciousness_unchanged": (intact["hr"], intact["consciousness_level"])
                     == (depressed["hr"], depressed["consciousness_level"])}
    out["pass"] = all(out["checks"].values())
    return out


def acidosis_probe() -> dict:
    """P2O-1's synthetic metabolic acidosis (arrival HCO3 14): acid drive at availability 1, then lower availability."""
    a = replace(go.NEUTRAL, case_id="p2p2_acidosis_probe", arrival_bicarbonate=ACIDOSIS_BICARBONATE)
    rows = []
    for availability in AVAILABILITIES[:-1]:
        prof = replace(base_profile(), central_drive_availability=availability)
        c = dv.arrival_drive_composition(a, prof)
        rows.append({"availability": availability, "acid_drive": c.acid_drive, "expressed_rr": c.expressed_rr,
                     "intrinsic_rr": c.baseline_rr, "hypoxaemic_drive": c.hypoxaemic_drive})
    rr = [r["expressed_rr"] for r in rows]
    return {"rows": rows, "acid_drives": rows[0]["acid_drive"] > 0.0 and rr[0] > rows[0]["intrinsic_rr"],
            "depression_attenuates": all(b < a for a, b in zip(rr, rr[1:])),
            "pass": rows[0]["acid_drive"] > 0.0 and rr[0] > rows[0]["intrinsic_rr"]
            and all(b < a for a, b in zip(rr, rr[1:])) and all(r["hypoxaemic_drive"] == 0.0 for r in rows)}


# P2P-2-11: HR and consciousness; the composition writes nothing ---------------------------------------------------------------------

def downstream() -> dict:
    """The composition's functions return values only; the integrator never reads RR; HR and consciousness read no drive."""
    live = (ROOT / CORE_FILE).read_text(encoding="utf-8")
    funcs = _functions(live)
    writes = {n: any(isinstance(t, (ast.Attribute, ast.Subscript)) for x in ast.walk(funcs[n])
                     if isinstance(x, (ast.Assign, ast.AugAssign, ast.AnnAssign))
                     for t in (x.targets if isinstance(x, ast.Assign) else [x.target])) for n in COMPOSITION}
    integration = (CORE_DIR / "integration.py").read_text(encoding="utf-8")
    hr_names = _names(funcs["sympathetic_target"]) | _names(funcs["sympathetic_increment"])
    reads = {"integration_reads_respiration": any(n in integration for n in ("respiration(", "drive_composition",
                                                                             "expressed_respiratory_rate")),
             "hr_reads_drive": bool({"respiration", "respiratory_drive_composition", "central_drive_availability",
                                     "hypoxaemic_drive"} & hr_names)}
    out = {"attribute_writes": writes, "reads": reads}
    out["pass"] = not any(writes.values()) and not any(reads.values())
    return out


# Mechanics stays separate; no clinical value chosen; no disease term ---------------------------------------------------------------

COMPOSITION = ("hypoxaemic_drive_signal", "hypoxaemic_drive", "expressed_respiratory_rate", "_composition",
               "respiratory_drive_composition", "arrival_drive_composition")


def _value_literals(node) -> set:
    """Numeric constants of a function that are values, not subscript indices."""
    indices = {id(c) for x in ast.walk(node) if isinstance(x, ast.Subscript) for c in ast.walk(x.slice)}
    return {x.value for x in ast.walk(node) if isinstance(x, ast.Constant) and id(x) not in indices
            and isinstance(x.value, (int, float)) and not isinstance(x.value, bool)}


def boundaries() -> dict:
    inserted = "\n".join(live for live, _ in REVERSAL[CORE_FILE])
    funcs = _functions((ROOT / CORE_FILE).read_text(encoding="utf-8"))
    literals = sorted(set().union(*(_value_literals(funcs[n]) for n in COMPOSITION)))
    reads_efficiency = {n: "ventilation_efficiency" in _names(funcs[n]) for n in COMPOSITION}
    defaults = {"hypoxaemic_drive_mapping": dv.DEFAULT_PROFILE.hypoxaemic_drive_mapping,
                "hypoxaemic_to_drive_gain": dv.DEFAULT_PROFILE.hypoxaemic_to_drive_gain,
                "central_drive_availability": dv.DEFAULT_PROFILE.central_drive_availability}
    out = {"composition_literals": literals, "composition_reads_efficiency": reads_efficiency, "defaults": defaults,
           "disease_terms_in_core_insertions": go.disease_terms(inserted), "new_state": _new_state()}
    out["mechanics_separate"] = not any(reads_efficiency.values()) and not out["new_state"]
    out["no_values"] = (set(literals) <= {0, 0.0, 1, 1.0} and not out["disease_terms_in_core_insertions"]
                        and defaults == {"hypoxaemic_drive_mapping": None, "hypoxaemic_to_drive_gain": None,
                                         "central_drive_availability": 1.0})
    out["pass"] = out["mechanics_separate"] and out["no_values"]
    return out


def _new_state() -> list:
    """Files of the state and integrator P2P-2 changed (none: no new canonical state)."""
    return sorted(r for r in REVERSAL if r in ("clinical_core/state.py", "clinical_core/integration.py"))


# Non-regression: GI, ACS and the P2P-1 baseline ---------------------------------------------------------------------------------------

def non_regression() -> dict:
    p2o1 = json.loads(go.RECORD.read_text(encoding="utf-8"))
    p2o3 = json.loads(lw.RECORD.read_text(encoding="utf-8"))
    p2p1 = json.loads(pe.RECORD.read_text(encoding="utf-8"))
    r78 = go._plain(lw.probe_r7_r8())
    out = {"gi_o12": go._plain(go.probe_o12()) == p2o1["probes"]["O12"],
           "acs_evaluation": go._plain(go.acs_evaluation()) == p2o1["acs"],
           "acs_authority_r7": r78["R7"] == p2o3["probes"]["probes"]["R7"],
           "common_overload_r8": r78["R8"] == p2o3["probes"]["probes"]["R8"],
           "p2p1_untreated": go._plain(pe.untreated()) == p2p1["untreated"],
           "p2p1_oxygen": go._plain(pe.oxygen()) == p2p1["oxygen"],
           "p2p1_respiration": go._plain(pe.respiration()) == p2p1["respiration"],
           "p2p1_heart_rate": go._plain(pe.heart_rate()) == p2p1["heart_rate"],
           "p2p1_consciousness": go._plain(pe.consciousness()) == p2p1["consciousness"],
           "common_files_untouched": common_untouched()}
    out["pass"] = all(v for k, v in out.items() if k != "common_files_untouched") and all(
        out["common_files_untouched"].values())
    return out


# The closed packages' view: the P2P-1 files, P2P-2's insertions undone (proven) ------------------------------------------------------

P2P1_HEAD = "2cd0a12"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/lung_water_reference.py", '
                                     '"clinical_core/lung_water_reference_report.py",\n'
                                     '                        "clinical_core/edema_migration.py", '
                                     '"clinical_core/edema_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_drive.py", '
                                     '"clinical_core/respiratory_drive_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/lung_water_reference.py", '
                                     '"clinical_core/lung_water_reference_report.py",\n'
                                     '                        "clinical_core/edema_migration.py", '
                                     '"clinical_core/edema_migration_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('    ventilation_efficiency: float = 1.0\n'
                               "    # P2P-2: the common respiratory-drive composition of P2K-2's RR. The excitatory "
                               'drive is the acid drive plus a\n'
                               '    # hypoxaemic drive read from the CURRENT absolute SpO2, never from its change '
                               'since arrival; the expressed RR is the\n'
                               '    # central drive availability times the RR that excitatory drive gives with the '
                               'central machinery intact (the\n'
                               '    # intrinsic RR plus the common saturating response), so central depression '
                               'lowers the intrinsic share too and never\n'
                               '    # rewrites the intrinsic RR. The hypoxaemic mapping is a table of (SpO2, '
                               'normalized drive) points read by linear\n'
                               '    # interpolation (no threshold or curve is chosen here) with its gain: both None, '
                               'UNSET (no hypoxaemic drive). The\n'
                               '    # availability is 1 (no central depression); no value below 1 is approved. The '
                               "arrival PaCO2 anchor stays P2K-2's\n"
                               '    # (the acid drive only, availability 1, the reference efficiency): a central '
                               'depression or a hypoxaemic drive moves\n'
                               '    # PaCO2 from that anchor, never absorbed by it, as a lower efficiency does.\n'
                               '    hypoxaemic_drive_mapping: tuple[tuple[float, float], ...] | None = None\n'
                               '    hypoxaemic_to_drive_gain: float | None = None\n'
                               '    central_drive_availability: float = 1.0\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n',
                               '    ventilation_efficiency: float = 1.0\n'
                               '    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))\n'),
                              ('            raise CoreInvariantError("the ventilation efficiency is above 0 and at '
                               'most 1")\n'
                               '        if (self.hypoxaemic_drive_mapping is None) != (self.hypoxaemic_to_drive_gain '
                               'is None):\n'
                               '            # P2P-2: the hypoxaemic drive is one structure; a mapping without its '
                               'gain, or the reverse, is half-defined.\n'
                               '            raise CoreInvariantError("the hypoxaemic drive declares its oxygenation '
                               'mapping and its gain together, or "\n'
                               '                                     "neither")\n'
                               '        if self.hypoxaemic_drive_mapping is not None:\n'
                               '            points = self.hypoxaemic_drive_mapping\n'
                               '            if len(points) < 2 or any(len(point) != 2 or any(isinstance(x, bool) or '
                               'not isinstance(x, (int, float))\n'
                               '                                                             or not math.isfinite(x) '
                               'for x in point)\n'
                               '                                      for point in points):\n'
                               '                raise CoreInvariantError("the hypoxaemic mapping is at least two '
                               'finite (SpO2, normalized drive) points")\n'
                               '            if not all(0.0 <= spo2 <= 100.0 and 0.0 <= drive <= 1.0 for spo2, drive '
                               'in points):\n'
                               '                raise CoreInvariantError("the hypoxaemic mapping reads SpO2 from 0 '
                               'to 100 into a drive from 0 to 1")\n'
                               '            if any(low >= high or at_low < at_high for (high, at_high), (low, '
                               'at_low) in zip(points, points[1:])):\n'
                               '                # Monotone: a lower SpO2 never drives less.\n'
                               '                raise CoreInvariantError("the hypoxaemic mapping lists SpO2 strictly '
                               'decreasing with a drive that "\n'
                               '                                         "never decreases")\n'
                               '        if not 0.0 <= self.central_drive_availability <= 1.0:\n'
                               '            raise CoreInvariantError("the central drive availability is between 0 '
                               '(no spontaneous drive) and 1 (no "\n'
                               '                                     "central depression)")\n'
                               '        if (self.hypoxaemic_drive_mapping is not None or '
                               'self.central_drive_availability != 1.0) \\\n'
                               '                and self.acid_to_drive_gain is None:\n'
                               "            # P2P-2: the composition is P2K-2's RR; with the acid-base physiology "
                               "off, P2K-1's RR would ignore it.\n"
                               '            raise CoreInvariantError("the respiratory-drive composition (hypoxaemic '
                               'drive, central availability) needs "\n'
                               '                                     "the P2K-2 acid-base physiology")\n'
                               '        if (self.spo2_per_gas_exchange_unit is None) != '
                               '(self.oxygen_response_loss_per_gas_exchange_unit is None):\n',
                               '            raise CoreInvariantError("the ventilation efficiency is above 0 and at '
                               'most 1")\n'
                               '        if (self.spo2_per_gas_exchange_unit is None) != '
                               '(self.oxygen_response_loss_per_gas_exchange_unit is None):\n'),
                              ('                                            "preserved), below 1 only in synthetic '
                               'probes; not an approved value"),\n'
                               '    "hypoxaemic_drive_mapping": (PROVISIONAL, "UNSET (P2P-2): (SpO2, normalized '
                               'hypoxaemic drive 0-1) points, linear "\n'
                               '                                              "between them, read on the CURRENT '
                               'absolute SpO2, never relative to "\n'
                               '                                              "arrival; no threshold, curve or '
                               'saturation is chosen; None by default "\n'
                               '                                              "(no hypoxaemic drive); SYNTHETIC_ONLY '
                               'tables in probes; not approved"),\n'
                               '    "hypoxaemic_to_drive_gain": (PROVISIONAL, "UNSET (P2P-2): respiratory drive '
                               '(breaths/min-equivalent) at the full "\n'
                               '                                              "normalized hypoxaemic drive, added to '
                               'the acid drive before the common "\n'
                               '                                              "saturation; None by default; not '
                               'approved"),\n'
                               '    "central_drive_availability": (PROVISIONAL, "STRUCTURAL_INPUT (P2P-2): the share '
                               'of the excitatory respiratory "\n'
                               '                                                "drive the central machinery '
                               'expresses, 0 to 1; it multiplies the RR "\n'
                               '                                                "the excitatory drive gives, '
                               'intrinsic share included, never the "\n'
                               '                                                "intrinsic RR itself; 1 (no central '
                               'depression) by default, lower only "\n'
                               '                                                "in synthetic probes; no family '
                               'mapping approved"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n',
                               '                                            "preserved), below 1 only in synthetic '
                               'probes; not an approved value"),\n'
                               '    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 '
                               'anchoring or the recovery "\n'),
                              ('\n'
                               '# P2P-2: the common respiratory-drive composition '
                               '---------------------------------------------------------------------------\n'
                               '\n'
                               'def hypoxaemic_drive_signal(spo2: float, profile: CoreProfile) -> float:\n'
                               '    """The normalized hypoxaemic drive (0 to 1) of an absolute SpO2: the profile\'s '
                               'points, linear between them, held at\n'
                               '    the end values outside them. It reads only the SpO2 it is given, never the '
                               "arrival's: 81 % drives the same at arrival\n"
                               '    as later. 0 when the mapping is UNSET."""\n'
                               '    points = profile.hypoxaemic_drive_mapping\n'
                               '    if points is None:\n'
                               '        return 0.0\n'
                               '    if spo2 >= points[0][0]:\n'
                               '        return float(points[0][1])\n'
                               '    for (high, at_high), (low, at_low) in zip(points, points[1:]):\n'
                               '        if spo2 >= low:\n'
                               '            return at_low + (at_high - at_low) * (spo2 - low) / (high - low)\n'
                               '    return float(points[-1][1])\n'
                               '\n'
                               '\n'
                               'def hypoxaemic_drive(spo2: float, profile: CoreProfile) -> float:\n'
                               '    """The hypoxaemic respiratory drive (breaths/min-equivalent): the gain times the '
                               'normalized signal; 0 when UNSET."""\n'
                               '    if profile.hypoxaemic_drive_mapping is None:\n'
                               '        return 0.0\n'
                               '    return profile.hypoxaemic_to_drive_gain * hypoxaemic_drive_signal(spo2, '
                               'profile)\n'
                               '\n'
                               '\n'
                               'def expressed_respiratory_rate(excitatory_rr: float, availability: float) -> float:\n'
                               '    """The expressed spontaneous RR: the central drive availability times the RR the '
                               'excitatory drive gives with the\n'
                               '    central machinery intact. Availability 1 is that RR exactly; a lower one lowers '
                               'all of it, the intrinsic share\n'
                               '    included, so central depression can take the RR below the intrinsic RR and '
                               'toward apnoea at 0, whatever the\n'
                               '    excitatory drive: the RR is never above availability x (intrinsic RR + the drive '
                               'saturation)."""\n'
                               '    return availability * excitatory_rr\n'
                               '\n'
                               '\n'
                               '@dataclass(frozen=True)\n'
                               'class DriveComposition:\n'
                               '    """One minute of the respiratory-drive composition (P2P-2).\n'
                               '\n'
                               '    ``baseline_rr`` is the intrinsic RR, the baseline spontaneous drive; '
                               '``acid_drive`` and ``hypoxaemic_drive`` are\n'
                               '    the excitatory terms (breaths/min-equivalent) and ``excitatory_drive`` their '
                               'sum; ``excitatory_rr`` is the RR they\n'
                               "    give with the central machinery intact (P2K-2's ``rate_from_drive``); "
                               '``availability`` is the central drive\n'
                               '    availability and ``expressed_rr`` the RR the patient shows. ``spo2`` is the '
                               'absolute SpO2 the hypoxaemic drive\n'
                               '    read, None when its mapping is UNSET or there is no pulse."""\n'
                               '\n'
                               '    baseline_rr: float\n'
                               '    acid_drive: float\n'
                               '    spo2: float | None\n'
                               '    hypoxaemic_drive: float\n'
                               '    excitatory_drive: float\n'
                               '    excitatory_rr: float\n'
                               '    availability: float\n'
                               '    expressed_rr: float\n'
                               '\n'
                               '\n'
                               'def _composition(intrinsic: float, acid: float, spo2: float | None, profile: '
                               'CoreProfile) -> DriveComposition:\n'
                               '    hypoxaemic, excitatory = 0.0, acid\n'
                               '    if profile.hypoxaemic_drive_mapping is not None:\n'
                               '        hypoxaemic = hypoxaemic_drive(spo2, profile)\n'
                               '        excitatory = acid + hypoxaemic\n'
                               '    excitatory_rr = rate_from_drive(excitatory, intrinsic, profile)\n'
                               '    availability = profile.central_drive_availability\n'
                               '    return DriveComposition(intrinsic, acid, spo2, hypoxaemic, excitatory, '
                               'excitatory_rr, availability,\n'
                               '                            expressed_respiratory_rate(excitatory_rr, '
                               'availability))\n'
                               '\n'
                               '\n'
                               'def respiratory_drive_composition(state: CoreState, anchors: Anchors, profile: '
                               'CoreProfile) -> DriveComposition:\n'
                               '    """The minute\'s composition: the acid drive from the burden, the hypoxaemic '
                               "drive from the state's current SpO2 (read\n"
                               '    only when its mapping is declared), the availability from the profile. No '
                               'breathing without a pulse."""\n'
                               '    intrinsic = intrinsic_respiratory_rate(anchors)\n'
                               '    acid = respiratory_drive(state.aux.metabolic_acid_burden, profile)\n'
                               '    if not state.R.pulse_present:\n'
                               '        return DriveComposition(intrinsic, acid, None, 0.0, acid, 0.0, '
                               'profile.central_drive_availability, 0.0)\n'
                               '    spo2 = _perfusion(state, anchors, profile)[2] if '
                               'profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic, acid, spo2, profile)\n'
                               '\n'
                               '\n'
                               'def arrival_drive_composition(anchors: Anchors, profile: CoreProfile) -> '
                               'DriveComposition:\n'
                               '    """The composition of the arrival state without building it: the arrival acid '
                               'burden and the authored arrival SpO2,\n'
                               '    which the arrival state reads exactly (P2F-1), each read like any later value '
                               '(the hypoxaemic mapping is absolute)."""\n'
                               '    spo2 = anchors.spo2 if profile.hypoxaemic_drive_mapping is not None else None\n'
                               '    return _composition(intrinsic_respiratory_rate(anchors),\n'
                               '                        respiratory_drive(arrival_acid_burden(anchors, profile), '
                               'profile), spo2, profile)\n'
                               '\n'
                               '\n'
                               'def respiration(state: CoreState, anchors: Anchors, profile: CoreProfile) -> '
                               'Respiration:\n'
                               '    """Drive from the acid burden (and, P2P-2, the hypoxaemic drive), RR from the '
                               'drive times the central drive\n'
                               '    availability, effective ventilation from RR x efficiency relative to need, PaCO2 '
                               'from the ventilation anchored to\n'
                               '    the arrival PaCO2 at the P2K-2 reference (efficiency 1, availability 1, no '
                               'hypoxaemic drive: exact at arrival with\n'
                               '    those, moved from the anchor by any of them), pH from HCO3 and PaCO2.\n'
                               '\n'
                               '    No term reads lactate, D or the W channel; the ventilation feeds back into '
                               'nothing (no CO2 chemoreflex in P2K-2).\n'
                               '    ``drive`` is the excitatory drive; with the hypoxaemic drive UNSET and '
                               'availability 1 every value is P2K-2\'s."""\n'
                               '    if not acid_base_active(profile):\n',
                               '\n'
                               'def respiration(state: CoreState, anchors: Anchors, profile: CoreProfile) -> '
                               'Respiration:\n'
                               '    """Drive from the acid burden, RR from the drive, effective ventilation from RR '
                               'x efficiency relative to need,\n'
                               '    PaCO2 from the ventilation anchored to the arrival PaCO2 (exact at arrival by '
                               'construction), pH from HCO3 and PaCO2.\n'
                               '\n'
                               '    No term reads lactate, D or the W channel; the ventilation feeds back into '
                               'nothing (no CO2 chemoreflex in P2K-2)."""\n'
                               '    if not acid_base_active(profile):\n'),
                              ('                                 "no bicarbonate is left and no rule for that '
                               'boundary is decided")\n'
                               '    composition = respiratory_drive_composition(state, anchors, profile)\n'
                               '    drive, rate = composition.excitatory_drive, composition.expressed_rr\n'
                               '    demand_ratio = state.aux.oxygen_demand / anchors.metabolic_demand_baseline\n',
                               '                                 "no bicarbonate is left and no rule for that '
                               'boundary is decided")\n'
                               '    drive = respiratory_drive(burden, profile)\n'
                               '    rate = rate_from_drive(drive, intrinsic, profile) if state.R.pulse_present else '
                               '0.0\n'
                               '    demand_ratio = state.aux.oxygen_demand / anchors.metabolic_demand_baseline\n'),
                              ('    burden = arrival_acid_burden(anchors, profile)\n'
                               '    composition = arrival_drive_composition(anchors, profile)\n'
                               '    drive, rate = composition.excitatory_drive, composition.expressed_rr\n'
                               '    return {"authored_rr": anchors.respiratory_rate, "intrinsic_rr": intrinsic, '
                               '"arrival_acid_burden": burden,\n',
                               '    burden = arrival_acid_burden(anchors, profile)\n'
                               '    drive = respiratory_drive(burden, profile)\n'
                               '    rate = rate_from_drive(drive, intrinsic, profile)\n'
                               '    return {"authored_rr": anchors.respiratory_rate, "intrinsic_rr": intrinsic, '
                               '"arrival_acid_burden": burden,\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/lung_water_reference_report.py",\n'
                                     '                      "clinical_core/edema_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_drive_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/lung_water_reference_report.py",\n'
                                     '                      "clinical_core/edema_migration_report.py")\n'
                                     '\n'),)}
CORE_AT_P2P1 = {'clinical_core/decision_pack.py': 'a99d49eec6d3ec1f4b1e125d87db77ae123d1470d82f909da1748a885b921787',
 'clinical_core/derived.py': '99faa383feca1d78a129ddc0b7fcaacdcd8427a0f4514f62f118f9bcdbc92c08',
 'clinical_core/lactate_slice.py': '1119da624153dc251d7bc84344312a4ab1dc2ba3fd10f51a453cdc5125474613'}
# </reversal>
#: The common files P2P-2 never changes (P2P-1's common set and P2P-1's own files), at their P2P-1 bytes.
COMMON_AT_P2P1 = {'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/bands.py': '9facbd34dc643d45f7ad3d668619f344717824c921924247f65396fae6aa81bc',
 'clinical_core/collapse.py': '6076dd315f8bd335af8a425ac4d78e3bcbbd5f1198b45e511b4f122532d65fc9',
 'clinical_core/contracts_output.py': 'bc7371c7ccb57ea2f138a6bbc58c266851f6dbf0fbdb5eb2d625b1ea70ab3751',
 'clinical_core/edema_migration.py': '7d2bd34a883c0253aed4d254f025b400bf178346e348fd3982986c228ef2b464',
 'clinical_core/edema_reference.py': 'fd8702e4d5ed03cf6dbe72cf0053ad9af6966e40e2b197cf42261bf61a66eb76',
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
 'clinical_core/modules/pulmonary_edema.py': '01e68556c919efa24ff6186eacf22c98e2ec882bf5cd52109bbafaffd8351679',
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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2P1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2P1.items()}


def p2p1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2P-1 file plus P2P-2's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2p1_bytes(relative: str) -> bytes:
    return p2p1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2p1_sources(sources: dict) -> dict:
    """A P2P-1 dependency map: P2P-2's files removed, each changed file at its P2P-1 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2P1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def _p2p1_common_untouched() -> dict:
    return {relative: hashlib.sha256(p2p1_bytes(relative)).hexdigest() == sha
            for relative, sha in pe.COMMON_AT_P2O3.items()}


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2P-1's view reads the P2P-1 files (proven), so every closed guard still
    reads the core it froze."""
    patch.setattr(pe, "_live", p2p1_text)
    patch.setattr(pe, "common_untouched", _p2p1_common_untouched)
    patch.setattr(pe, "p2o3_bytes", lambda relative: pe.p2o3_text(relative).encode("utf-8")
                  if relative in pe.REVERSAL else p2p1_bytes(relative))


def upstream_unchanged() -> dict:
    text = json.dumps({"revision": pe.REVISION, "p2o3": hashlib.sha256(lw.RECORD.read_bytes()).hexdigest(),
                       "design": pe.design(), "sources": p2p1_sources(bf.freeze_sources())}, sort_keys=True,
                      default=str)
    return {"proofs": proofs(), "common_untouched": common_untouched(), "p2p1_common_untouched": _p2p1_common_untouched(),
            "p2p1_freeze_digest": hashlib.sha256(text.encode("utf-8")).hexdigest() == P2P1_FREEZE_DIGEST,
            "p2p1_record": hashlib.sha256(pe.RECORD.read_bytes()).hexdigest() == P2P1_RECORD_SHA}


P2P1_FREEZE_DIGEST = "2c7dc8b184529edea5a77c6beb8bf9b270391d4ae49f5a0d4221aa1a7a3a5c2e"
P2P1_RECORD_SHA = "d8545cb5a072f529d6cb518c53c5f3b206e125633e8d4050688dcbcadf818b0b"


# P2P-2-13: readiness (predeclared) ---------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "absolute hypoxaemic drive can enter (D3; same current SpO2, same drive; an 81 % arrival already drives)",
    "baseline, acid and hypoxaemic drive separable (D1, D2, D4; acidosis probe)",
    "central depression suppresses baseline and excitatory drive (D5, D7, D9; acidosis attenuation)",
    "opioid-like hypoxaemia does not force tachypnoea (D6; cross-family probe)",
    "default behaviour unchanged (D8)",
    "mechanics explicitly separate (D10; no new state; the composition reads no efficiency)",
    "no clinical gain, threshold or curve selected; no disease term in the core",
    "prior families unchanged (GI, ACS, the P2P-1 baseline; HR and consciousness; the P2P-1 tree proven and audited)",
)
READY = "COMMON_RESPIRATORY_DRIVE_ARCHITECTURE_READY"
NOT_READY = "COMMON_RESPIRATORY_DRIVE_ARCHITECTURE_NOT_READY"
READINESS_RULE = ("Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion "
                  "as the blocker. The pulmonary-edema diagnostic informs the mechanics gap and never decides it")
RECOMMENDATION = {READY: "PROCEED_TO_PE_GENERALIZATION_AUDIT"}
PE_AUDIT_SCOPE = ("direct G without L; obstructive / RV physiology without false pulmonary congestion; whether the "
                  "hypoxaemic-drive architecture generalizes structurally. No PE migration in P2P-2")


def readiness(found: dict) -> dict:
    p, proof = found["probes"]["pass"], found["proof"]
    values = (
        p["D3"] and found["absolute"]["pass"],
        p["D1"] and p["D2"] and p["D4"] and found["acidosis"]["pass"],
        p["D5"] and p["D7"] and p["D9"] and found["acidosis"]["depression_attenuates"],
        p["D6"] and found["opioid"]["pass"],
        p["D8"],
        p["D10"] and found["boundaries"]["mechanics_separate"],
        found["boundaries"]["no_values"],
        found["non_regression"]["pass"] and found["downstream"]["pass"] and found["audit"]["pass"]
        and all(proof["proofs"].values())
        and proof["p2p1_freeze_digest"] and proof["p2p1_record"] and all(proof["p2p1_common_untouched"].values()),
    )
    criteria = dict(zip(READINESS_CRITERIA, values))
    blocker = next((name for name, ok in criteria.items() if not ok), None)
    verdict = READY if blocker is None else f"{NOT_READY} — {blocker}"
    return {"criteria": criteria, "verdict": verdict, "ready": blocker is None, "blocker": blocker,
            "recommendation": RECOMMENDATION.get(READY) if blocker is None else None,
            "pe_audit_scope": PE_AUDIT_SCOPE if blocker is None else None}


# Freeze and record --------------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "decisions": DECISIONS, "g_guard": G_GUARD,
            "path_at_p2p1": PATH_AT_P2P1, "depression_at_p2p1": DEPRESSION_AT_P2P1,
            "hypoxaemia_readers_at_p2p1": HYPOXAEMIA_READERS_AT_P2P1, "classification_at_p2p1": CLASSIFICATION_AT_P2P1,
            "semantics": SEMANTICS, "aggregation": AGGREGATION, "placement": PLACEMENT, "arrival_anchor": ARRIVAL_ANCHOR,
            "deferred": DEFERRED, "parameter_status": PARAMETER_STATUS,
            "synthetic": {"mapping": [list(p) for p in SYNTHETIC_MAPPING], "gains": list(SYNTHETIC_GAINS),
                          "intrinsic": PROBE_INTRINSIC, "drive": PROBE_DRIVE, "strong_drive": STRONG_DRIVE,
                          "huge_drive": HUGE_DRIVE, "availabilities": list(AVAILABILITIES),
                          "strong_depression": STRONG_DEPRESSION, "toward_zero": list(TOWARD_ZERO),
                          "hypoxaemic_spo2": HYPOXAEMIC_SPO2, "acidosis_bicarbonate": ACIDOSIS_BICARBONATE,
                          "probe_minutes": PROBE_MINUTES, "pe_fio2": PE_FIO2},
            "probes": PROBES, "readiness_criteria": list(READINESS_CRITERIA), "readiness_rule": READINESS_RULE,
            "recommendation": RECOMMENDATION, "pe_audit_scope": PE_AUDIT_SCOPE, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "reversal": {k: [list(pair) for pair in v] for k, v in REVERSAL.items()}, "core_at_p2p1": CORE_AT_P2P1,
            "common_at_p2p1": COMMON_AT_P2P1,
            "p2p1": {"head": P2P1_HEAD, "freeze_digest": P2P1_FREEZE_DIGEST, "record": P2P1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2p1": hashlib.sha256(pe.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "probes": structural_probes(),
             "absolute": absolute_check(), "pulmonary_edema": pulmonary_edema_diagnostic(), "opioid": opioid_probe(),
             "acidosis": acidosis_probe(), "downstream": downstream(), "boundaries": boundaries(),
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
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
