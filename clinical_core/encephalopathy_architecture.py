"""Phase 2 shadow core, P2L-2: the common systemic-encephalopathy architecture, its structural evaluation.

    python -m clinical_core.encephalopathy_architecture --digest
    python -m clinical_core.encephalopathy_architecture --design
    python -m clinical_core.encephalopathy_architecture --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-11-01, recorded in FACULTY). P2L-1 found no recovery memory; the faculty
authorized the systemic memory and fixed the composition (encephalopathy.py). This module evaluates that architecture
without a clinical number: the probes N1-N12 run on synthetic normalized signals with a synthetic probe memory
(SYNTHETIC_PROBE_ONLY, time in synthetic units); the orthogonality and isolation probes read fixed core states through
the candidate's readings and classify each signal threshold-free (admissible_support), at both retained ventilation gains;
the carried extreme-acidemia subset, the tone loop and N's audit are read from the committed P2L-1 record and P2L-1's
frozen scan. It changes no core file, writes no state, chooses no bound or time constant, maps no impairment to an
observed category, generates no GI trajectory and calibrates nothing; collapse stays off.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import consciousness_audit as ca
from . import encephalopathy as enc
from . import lactate_rebuild as lr
from . import ventilation_surface as vs
from . import vascular_tone as vt

DECIDED = "2026-11-01"
REVISION = "P2L-2"
ROOT = vs.ROOT
P2L1_RECORD = ROOT / "docs" / "revision" / "P2L1_consciousness_audit.json"
P2L1_RECORD_SHA = "dcb1b40ae92cd785bec0723d6262948ab616d7b2513656ecd3cf81e2fadf607b"

FACULTY = {
    "brief": "P2L-2 common systemic-encephalopathy architecture (2026-11-01): structural; no numeric fit to the GI cases",
    "n": "N is reserved for the primary neurologic state / injury or reserve (structural CNS injury, seizure / postictal, "
         "primary encephalopathy, other primary neurologic pathology); shock, hypoperfusion, hypoxaemia, acidemia, "
         "hypercapnia and hypoglycaemia are never written into N",
    "pharmacologic": "no pharmacologic CNS depression in N and no drug-depression state here: "
                     "FUTURE_COMMON_SYSTEMIC_OR_PHARMACOLOGIC_MODIFIER",
    "memory": "a new auxiliary dynamic state, systemic_encephalopathy_burden, not a canonical channel: reversible "
              "accumulated cerebral dysfunction from systemic insults; non-negative; rises with severe systemic brain "
              "stress, may persist after it, clears gradually; cannot create N; never alters upstream physiology",
    "d": "D stays the oxygen-delivery debt; never the consciousness memory (it misses isolated hypotension, hypercapnia, "
         "hypoglycaemia and primary injury); at most diagnostic",
    "signals": "cerebral hypoperfusion (MAP), effective oxygen-delivery deficit, hypoxaemia (SpO2), metabolic acidemia "
               "(pH), hypercapnia (PaCO2, apart from pH), hypoglycaemia (glucose); primary N apart; no lactate, no HR",
    "map": "MAP, not SBP; the SBP 80 / 65 and SpO2 87 / 80 ladders and the arrival floor retired from candidate "
           "physiology, kept LEGACY_REFERENCE_ONLY; no MAP threshold selected",
    "aggregation": "systemic_acute_brain_stress = MAX of the six signals; observable = MAX(primary N, acute, memory); "
                   "no sum, no synergy",
    "thresholds": "no threshold from the GI cases (no authored post-arrival neurologic observation): synthetic normalized "
                  "inputs or committed common ranges only; STOP before choosing a new number",
    "trajectories": "GI consciousness trajectories only if signal mappings exist independently of GI outcomes",
    "identifiability": "STRUCTURALLY_DEFINED BUT_CLINICALLY_UNIDENTIFIED where appropriate; never WELL_CONSTRAINED from "
                       "synthetic probes",
    "collapse": "not calibrated, not activated"}
STATUS = {"approved": "none FACULTY_APPROVED", "collapse": "OFF (not calibrated)",
          "probe_values": "SYNTHETIC_PROBE_ONLY (normalized intensities, synthetic time units, synthetic memory)"}

# 1. The synthetic probe design (P2L-2-1, P2L-2-3), fixed before any run ------------------------------------------------------

#: Synthetic, structural only: time in synthetic units, the rise constant the unit, clearance slower. Never minutes, never
#: derived from tau_D, never fitted. The qualitative results are re-checked at every ratio in CLEAR_RATIOS.
PROBE_RISE_TAU = 1.0
CLEAR_RATIOS = (2.0, 4.0, 8.0)
PROBE_CLEAR_RATIO = 4.0
PROBE_DT = 0.25
INTENSITY = 0.6
SEVERE = 0.9
BRIEF, PROLONGED, RECOVERY = 1.0, 6.0, 40.0
#: A reporting tolerance for the synthetic recovery time only (the memory's residual on the synthetic scale); the
#: threshold-free comparison is the memory's area after restoration.
RESIDUAL = 0.05


def probe_profile(ratio: float = PROBE_CLEAR_RATIO) -> enc.EncephalopathyProfile:
    return enc.EncephalopathyProfile(burden_rise_tau=PROBE_RISE_TAU, burden_clear_tau=PROBE_RISE_TAU * ratio)


def _steps(duration: float) -> int:
    return int(round(duration / PROBE_DT))


COURSE_STEPS = []


def course(phases, primary: float = 0.0, ratio: float = PROBE_CLEAR_RATIO, initial: float = 0.0) -> dict:
    """A synthetic course: phases of (duration, {signal: value}); S held per step; F integrated exactly; I = max(N, S, F).
    Every step is counted in COURSE_STEPS (the run's efficiency record)."""
    profile = probe_profile(ratio)
    stresses, signal_rows = [], []
    for duration, signals in phases:
        full = {name: signals.get(name, 0.0) for name in enc.SIGNALS}
        for _ in range(_steps(duration)):
            stresses.append(enc.systemic_acute_brain_stress(full))
            signal_rows.append(full)
    stresses.append(stresses[-1] if stresses else 0.0)
    burden = enc.burden_course(stresses[:-1], PROBE_DT, profile, initial)
    COURSE_STEPS.append(len(stresses) - 1)
    p = enc.primary_neurologic_impairment(primary)
    impairment = [enc.observable_impairment(p, s, f)["impairment"] for s, f in zip(stresses, burden)]
    return {"stress": stresses, "burden": burden, "impairment": impairment, "primary": p}


def _restoration(c: dict, insult_steps: int) -> dict:
    """What the course shows from the step physiology is restored: the residual memory, its monotone decay, its area
    (threshold-free) and the synthetic time below RESIDUAL."""
    after_f, after_i = c["burden"][insult_steps:], c["impairment"][insult_steps:]
    below = next((k for k, f in enumerate(after_f) if f < RESIDUAL), None)
    return {"stress_at_restoration": c["stress"][insult_steps], "burden_at_restoration": after_f[0],
            "impairment_at_restoration": after_i[0],
            "burden_monotone_decay": all(b <= a for a, b in zip(after_f, after_f[1:])),
            "burden_non_negative": min(c["burden"]) >= 0.0,
            "memory_area": sum(after_f) * PROBE_DT,
            "time_to_residual": None if below is None else below * PROBE_DT}


# 2. The probes N1-N12 on synthetic normalized signals (P2L-2-7) ----------------------------------------------------------------

SHOCK = {"cerebral_hypoperfusion": SEVERE, "oxygen_deficit": 0.8, "acidemia": 0.7}
SINGLE = {"N3": "oxygen_deficit", "N4": "cerebral_hypoperfusion", "N5": "acidemia", "N6": "hypercapnia",
          "N7": "hypoglycaemia", "N8": "hypoxaemia"}
MULTIPLE = {"cerebral_hypoperfusion": 0.5, "oxygen_deficit": INTENSITY, "acidemia": 0.4, "hypoxaemia": 0.3}
N12_PRIMARY, N12_SYSTEMIC = 0.4, 0.7
NEURO_PROBES = {
    "N1": "normal N and every systemic signal normal: normal consciousness",
    "N2": f"primary N {INTENSITY} only: consciousness worsens; the systemic memory stays 0",
    "N3": f"oxygen deficit {INTENSITY} only", "N4": f"cerebral hypoperfusion {INTENSITY} only",
    "N5": f"metabolic acidemia {INTENSITY} only", "N6": f"hypercapnia {INTENSITY} only",
    "N7": f"hypoglycaemia {INTENSITY} only", "N8": f"severe hypoxaemia {INTENSITY} only",
    "N9": "hypoperfusion 0.5, deficit 0.6, acidemia 0.4, hypoxaemia 0.3 together: the maximum, not the sum",
    "N10": f"a prolonged severe insult (hypoperfusion {SEVERE}, deficit 0.8, acidemia 0.7, {PROLONGED:g} units), then "
           f"physiology restored ({RECOVERY:g} units)",
    "N11": f"brief ({BRIEF:g}) vs prolonged ({PROLONGED:g}) vs repeated brief (3 x {BRIEF:g}, gaps {BRIEF:g}) insults of "
           f"equal intensity {SEVERE}",
    "N12": f"primary N {N12_PRIMARY} with a systemic insult {N12_SYSTEMIC} ({PROLONGED:g} units), then restored"}


def neuro_probes(ratio: float = PROBE_CLEAR_RATIO) -> dict:
    rows = {}
    n1 = course([(PROLONGED, {})], ratio=ratio)
    rows["N1"] = {"max_impairment": max(n1["impairment"]), "max_burden": max(n1["burden"]),
                  "passes": max(n1["impairment"]) == 0.0 and max(n1["burden"]) == 0.0}
    n2 = course([(PROLONGED, {})], primary=INTENSITY, ratio=ratio)
    rows["N2"] = {"impairment": n2["impairment"][-1], "max_burden": max(n2["burden"]), "stress": n2["stress"][-1],
                  "passes": n2["impairment"][-1] == INTENSITY and max(n2["burden"]) == 0.0}
    for name, signal in SINGLE.items():
        c = course([(PROLONGED, {signal: INTENSITY})], ratio=ratio)
        rows[name] = {"signal": signal, "stress": c["stress"][-1], "impairment": c["impairment"][-1],
                      "burden_end": c["burden"][-1], "primary": c["primary"],
                      "passes": c["stress"][-1] == INTENSITY == c["impairment"][-1] and c["burden"][-1] > 0.0
                      and c["primary"] == 0.0}
    n9 = course([(PROLONGED, MULTIPLE)], ratio=ratio)
    total = sum(MULTIPLE.values())
    rows["N9"] = {"stress": n9["stress"][-1], "maximum": max(MULTIPLE.values()), "sum_would_be": total,
                  "passes": n9["stress"][-1] == max(MULTIPLE.values()) < total}
    k = _steps(PROLONGED)
    n10 = course([(PROLONGED, SHOCK), (RECOVERY, {})], ratio=ratio)
    r10 = _restoration(n10, k)
    rows["N10"] = {**r10, "stress_during": n10["stress"][k - 1],
                   "passes": r10["stress_at_restoration"] == 0.0 and r10["burden_at_restoration"] > 0.0
                   and r10["impairment_at_restoration"] == r10["burden_at_restoration"]
                   and r10["burden_monotone_decay"] and r10["burden_non_negative"]
                   and n10["burden"][-1] < r10["burden_at_restoration"]}
    brief = _restoration(course([(BRIEF, {"cerebral_hypoperfusion": SEVERE}), (RECOVERY, {})], ratio=ratio),
                         _steps(BRIEF))
    prolonged = _restoration(course([(PROLONGED, {"cerebral_hypoperfusion": SEVERE}), (RECOVERY, {})], ratio=ratio),
                             _steps(PROLONGED))
    pulse = (BRIEF, {"cerebral_hypoperfusion": SEVERE})
    repeated = _restoration(course([pulse, (BRIEF, {}), pulse, (BRIEF, {}), pulse, (RECOVERY, {})], ratio=ratio),
                            _steps(5 * BRIEF))
    rows["N11"] = {"brief": brief, "prolonged": prolonged, "repeated": repeated,
                   "passes": brief["burden_at_restoration"] < prolonged["burden_at_restoration"]
                   and brief["memory_area"] < prolonged["memory_area"]
                   and brief["time_to_residual"] < prolonged["time_to_residual"]
                   and brief["burden_at_restoration"] < repeated["burden_at_restoration"]
                   and brief["memory_area"] < repeated["memory_area"]}
    with_n = course([(PROLONGED, {"oxygen_deficit": N12_SYSTEMIC}), (RECOVERY, {})], primary=N12_PRIMARY, ratio=ratio)
    without_n = course([(PROLONGED, {"oxygen_deficit": N12_SYSTEMIC}), (RECOVERY, {})], ratio=ratio)
    rows["N12"] = {"impairment_during": with_n["impairment"][k - 1], "impairment_after": with_n["impairment"][-1],
                   "primary_throughout": with_n["primary"],
                   "burden_independent_of_n": with_n["burden"] == without_n["burden"],
                   "passes": with_n["impairment"][k - 1] == N12_SYSTEMIC
                   and min(with_n["impairment"][k:]) == N12_PRIMARY == with_n["primary"]
                   and with_n["burden"] == without_n["burden"]}
    return {"rows": rows, "all_pass": all(r["passes"] for r in rows.values())}


def ratio_robustness() -> dict:
    """The same probes at each synthetic clearance ratio: the qualitative results must not hang on the synthetic value."""
    out = {f"{r:g}": {name: row["passes"] for name, row in neuro_probes(r)["rows"].items()} for r in CLEAR_RATIOS}
    return {"by_ratio": out, "all_pass": all(all(v.values()) for v in out.values())}


#: Why the memory has the properties the faculty required, from its equation (no simulation needed for the proof).
MEMORY_PROOF = {
    "non_negative": "F_next = S + (F - S) e^(-dt/tau) is a convex combination of F and S, both in [0, 1]",
    "persists": "with S = 0, F_next = F e^(-dt/tau_clear) > 0 for F > 0: zero stress never zeroes the memory at once",
    "monotone_recovery": "with S < F, F_next lies strictly between S and F: the memory falls monotonically",
    "worsens": "with S > F, F_next lies strictly between F and S: acute stress raises the memory",
    "prolonged_greater": "after a constant S from F = 0, F = S (1 - e^(-t/tau_rise)) rises with the duration t, so a "
                         "longer insult leaves a larger residual, a larger area F_end x tau_clear and a longer recovery",
    "bounded_by_stress": "F never exceeds the largest S it has seen: the memory delays recovery, it never adds an "
                         "impairment the acute signals did not reach",
    "no_n": "burden_after reads no N, D, lactate or authored level, and nothing writes N",
    "distinct_from_d": "D integrates the delivery deficit alone, without bound, and repays on tau_D (lactate and the "
                       "sympathetic drive); F relaxes toward the maximum of six signals on its own constants and never "
                       "exceeds it; F reads no D and D reads no F"}


# 3. The physiological probes: wiring, isolation and orthogonality (P2L-2-8) -------------------------------------------------

#: P2K-5's retained ventilation gains: the respiratory uncertainty reaches pH and PaCO2, never reopened here.
GAINS = (0.03, 0.04)
PHYSIOLOGY_RULE = (
    "Fixed states on P2K-2's neutral probe arrival (bands.ARRIVAL with the probe gas: HCO3 20, PaCO2 36, intrinsic RR 16; "
    "extraction reserve 2.5), read through the candidate's readings with the ventilation candidate at each retained gain. "
    "The reference is the arrival itself (N1 requires it to read normal); each signal is classified threshold-free: zero "
    "under every admissible mapping, or positive under some. The sizes are illustrative extremes, P2L-1's probes.")
#: name -> (what, construction, the signals that may read positive, P2L-2-8 / P2L-2-7 role).
PHYSIOLOGY_PROBES = {
    "reference": ("the neutral probe arrival", {}, (), "D: neither"),
    "A_low_map_no_deficit": ("tone 0.45 (vasodilation; output rises)", {"T": 0.45}, ("cerebral_hypoperfusion",),
                             "A; N4"),
    "B_normal_map_high_deficit": ("Hb at 30 % (anaemia; pressure kept)", {"hb_share": 0.3}, ("oxygen_deficit",), "B"),
    "C_low_map_and_deficit": ("pump 0.3 (low-output shock)", {"P": 0.3},
                              ("cerebral_hypoperfusion", "oxygen_deficit"), "C"),
    "E_low_spo2_adequate_delivery": ("authored arrival SpO2 82 % (delivery index 1)", {"arrival_spo2": 82.0},
                                     ("hypoxaemia",), "E"),
    "E2_fio2_falls_to_room_air": ("arrival on FiO2 1, then room air", {"arrival_fio2": 1.0, "fio2": 0.21},
                                  ("hypoxaemia",), "E; N8"),
    "F_normal_spo2_critical_deficit": ("Hb at 25 %", {"hb_share": 0.25}, ("oxygen_deficit",), "F; N3"),
    "G_low_ph_normal_paco2": ("metabolic acid burden 15", {"burden": 15.0}, ("acidemia",), "G; N5"),
    "H_high_paco2_near_normal_ph": ("arrival HCO3 32 authored (compensated), ventilation efficiency 0.8",
                                    {"arrival_bicarbonate": 32.0, "efficiency": 0.8}, ("hypercapnia",), "H; N6"),
    "acute_hypercapnia": ("ventilation efficiency 0.6 (uncompensated)", {"efficiency": 0.6},
                          ("acidemia", "hypercapnia"), "acute respiratory acidemia: both read, the maximum keeps one"),
    "hypoglycaemia": ("glucose 30 mg/dL", {"glucose": 30.0}, ("hypoglycaemia",), "N7"),
    "shock_and_acidemia": ("pump 0.3 and acid burden 15", {"P": 0.3, "burden": 15.0},
                           ("cerebral_hypoperfusion", "oxygen_deficit", "acidemia"), "N9: several at once"),
    "primary_n_only": ("primary N 0.5 (synthetic), physiology normal", {"N": 0.5}, (),
                       "N2 / N12: N leaks into no systemic signal"),
    "arrival_label_obtunded": ("an authored arrival level 2 (obtunded), physiology normal",
                               {"arrival_level": 2}, (), "P2L-2-4: the label is never read; no floor")}


@dataclass(frozen=True)
class Gas:
    """The respiratory closure's pH and PaCO2 at a state (ventilation_surface._vr: the P2K-3 candidate at one gain)."""

    ph: float | None
    paco2: float | None


def _probe(spec: dict, gain: float):
    spec = dict(spec)
    anchors = vs.PROBE_ANCHORS
    if "arrival_spo2" in spec:
        anchors = replace(anchors, spo2=spec.pop("arrival_spo2"))
    if "arrival_fio2" in spec:
        anchors = replace(anchors, fio2=spec.pop("arrival_fio2"))
    if "arrival_level" in spec:
        anchors = replace(anchors, consciousness_level=spec.pop("arrival_level"))
    if "arrival_bicarbonate" in spec:
        anchors = replace(anchors, arrival_bicarbonate=spec.pop("arrival_bicarbonate"))
    profile = replace(vs.PROBE_PROFILE, ventilation_efficiency=spec.pop("efficiency", 1.0))
    burden = spec.pop("burden", None)
    if "hb_share" in spec:
        spec["hb"] = anchors.hb * spec.pop("hb_share")
    state = vs._probe_state(burden, anchors, profile, **spec)
    gas = vs._vr(state, anchors, profile, gain)
    return state, anchors, profile, Gas(gas["ph"], gas["paco2"])


def physiology_probes() -> dict:
    out = {}
    for gain in GAINS:
        rows = {}
        for name, (what, spec, expected, role) in PHYSIOLOGY_PROBES.items():
            state, anchors, profile, gas = _probe(spec, gain)
            reading = enc.readings(state, anchors, profile, gas)
            # The wiring against the certified readings P2L-1 used (derive, the deficit, the ventilation candidate).
            certified = ca.reading(state, anchors, profile)
            wired = (reading["map"] == certified["map"] and reading["spo2"] == certified["spo2"]
                     and reading["glucose"] == certified["glucose"]
                     and reading["deficit_fraction"] == certified["deficit_fraction"]
                     and (reading["ph"], reading["paco2"]) == (gas.ph, gas.paco2))
            committed = enc.acute_signals(reading, enc.DEFAULT_ENCEPHALOPATHY)
            rows[name] = {"what": what, "role": role, "reading": reading, "primary_n": enc.primary_from_state(state),
                          "expected_positive": list(expected), "wired": wired,
                          "committed_profile": dict(committed.reasons)}
        reference = rows["reference"]["reading"]
        for name, row in rows.items():
            support = enc.admissible_support(row["reading"], reference)
            positive = sorted(k for k, v in support.items() if v.startswith("POSITIVE"))
            row.update({"support": support, "positive": positive,
                        "isolated_as_declared": positive == sorted(row["expected_positive"])})
        out[f"{gain:g}"] = rows
    return out


ORTHOGONALITY = {"map_deficit": ("reference", "A_low_map_no_deficit", "B_normal_map_high_deficit",
                                 "C_low_map_and_deficit"),
                 "spo2_delivery": ("E_low_spo2_adequate_delivery", "F_normal_spo2_critical_deficit"),
                 "ph_paco2": ("G_low_ph_normal_paco2", "H_high_paco2_near_normal_ph")}


def orthogonality(physiology: dict) -> dict:
    out = {}
    for group, names in ORTHOGONALITY.items():
        patterns = {gain: [tuple(rows[n]["positive"]) for n in names] for gain, rows in physiology.items()}
        out[group] = {"probes": list(names),
                      "positive_by_gain": {g: [list(p) for p in v] for g, v in patterns.items()},
                      "distinguishable": all(len(set(v)) == len(v) for v in patterns.values()),
                      "isolated_as_declared": all(physiology[g][n]["isolated_as_declared"]
                                                  for g in physiology for n in names)}
    return out


# 4. The legacy paths, N and the retirements (P2L-2-4, P2L-2-5, P2L-2-6) ------------------------------------------------------

PHYSIOLOGY_SOURCE = ROOT / "clinical_core" / "encephalopathy.py"
#: Attributes the candidate physiology must never read: the legacy ladders and arrival floor, lactate, D, the heart rate.
FORBIDDEN_READS = ("consciousness_level", "pressure_levels", "oxygen_levels", "sbp", "dbp", "lactate", "D",
                   "lactate_excess_mmol_l", "pulse_rate_bpm", "monitor_rate_bpm", "sympathetic_drive",
                   "collapse_burden", "debt")
FORBIDDEN_TERMS = ("gi", "bleed", "haemorrhag", "hemorrhag", "opioid", "stroke", "sepsis", "septic", "distributive",
                   "57m", "72f")


def candidate_scan() -> dict:
    """The candidate physiology, read as code: what it reads, writes, imports and aggregates."""
    tree = ast.parse(PHYSIOLOGY_SOURCE.read_text(encoding="utf-8"))
    attributes = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)})
    keywords = sorted({k.arg for k in ast.walk(tree) if isinstance(k, ast.keyword) and k.arg})
    calls = sorted({getattr(n.func, "id", None) or getattr(n.func, "attr", None) for n in ast.walk(tree)
                    if isinstance(n, ast.Call)} - {None})
    imports = sorted({(n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
                     | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))} | set(attributes) | {
        a.arg for n in ast.walk(tree) if isinstance(n, ast.arguments) for a in n.args + n.kwonlyargs}
    identifiers = sorted(names | set(enc.SIGNALS) | {v[0] for v in enc.SIGNALS.values()})
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    aggregation_adds = {name: any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add) for x in ast.walk(functions[name]))
                        for name in ("systemic_acute_brain_stress", "observable_impairment")}
    max_calls = {name: any(isinstance(x, ast.Call) and getattr(x.func, "id", None) == "max"
                           for x in ast.walk(functions[name]))
                 for name in ("systemic_acute_brain_stress", "observable_impairment")}
    return {"forbidden_reads": [a for a in attributes if a in FORBIDDEN_READS],
            "writes_state": [c for c in calls if c in ("evolve", "replace", "ChannelDelta", "Drift")]
            + [k for k in keywords if k in ("N", "T", "P", "V", "hb", "glucose")],
            "imports": imports, "sum_calls": "sum" in calls,
            "aggregation_adds": aggregation_adds, "aggregation_by_max": max_calls,
            "disease_terms": sorted({t for t in FORBIDDEN_TERMS for i in identifiers
                                     if t in i.lower().split("_") or (len(t) > 3 and t in i.lower())}),
            "signals": {k: [v[0], v[1]] for k, v in enc.SIGNALS.items()},
            "reads_n_only_through": "primary_from_state" if "primary_from_state" in functions else None}


def imported_by() -> list:
    """Every clinical_core file that imports the candidate physiology (none of the core's)."""
    out = []
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | {
            n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        if any(name == "encephalopathy" or name.endswith(".encephalopathy") for name in names):
            out.append(path.relative_to(ROOT).as_posix())
    return out


def n_audit() -> dict:
    """N after P2L-2, with P2L-1's frozen recursive scan (this analysis module's synthetic probes left out)."""
    refs = ca.channel_references("N", "N")
    own = Path(__file__).name
    keep = lambda rows: [r for r in rows if not r.startswith(own)]  # noqa: E731
    return {"writers": keep(refs["writes"]), "readers": keep(refs["reads"]), "files_scanned": refs["files_scanned"],
            "semantics": enc.STATUS["N"], "scale": "the common impairment scale [0, 1]: 0 intact, 1 maximal primary "
                                                   "impairment; outside it the candidate stops (CoreInvariantError)",
            "dynamics": "static in the encounter (no recovery or healing kinetics)",
            "gi_values": "none: no GI case declares N (the legacy adapter builds N = 0)",
            "closed_wording": "state.CHANNEL_DEFINITIONS keeps 'CNS depression / neurological state' and the guard "
                              "(-10, 10) for the closed records: DOCUMENTED_SEMANTIC_DEBT until runtime integration"}


LEGACY = {"arrival_floor": "RETIRED_FROM_CANDIDATE: the candidate has no arrival floor; derive keeps "
                           "max(anchors.consciousness_level, ...) as LEGACY_REFERENCE_ONLY for the closed records",
          "sbp_ladder": "RETIRED_FROM_CANDIDATE: SBP 80 / 65 never read (MAP is the pressure signal); "
                        "LEGACY_REFERENCE_ONLY in derive",
          "spo2_ladder": "RETIRED_FROM_CANDIDATE: SpO2 87 / 80 never read; SpO2 enters only as the hypoxaemia signal "
                         "through its own (unmapped) ramp; LEGACY_REFERENCE_ONLY in derive",
          "lactate": "ABSENT: no lactate path (faculty); never read",
          "d": "ABSENT_AS_CONTROLLER: D is never read by the candidate; it stays the oxygen-delivery debt, diagnostic",
          "hr": "ABSENT: the heart rate is never read",
          "arrival_label": "an authored mental-status label (the GI cases' default 'Alert') is never read and never "
                           "calibration evidence; an arrival impairment needs N, S, a declared pre-arrival burden F0 or "
                           "another declared cause",
          "derived_wording": "derived.PARAMETERS keeps the ladders' closed status text ('adopted'): DOCUMENTED_SEMANTIC_"
                             "DEBT until runtime integration"}


# 5. The tone loop and the carried extreme-acidemia subset, from the committed P2L-1 record (P2L-2-9) -------------------------

def tone_loop() -> dict:
    """P2L-1's inversion (the SBP ladder read a compensated, worse deficit as less impairment), re-read by the candidate:
    the deficit now has its own signal, monotone in the deficit, so along every recorded tone-loop row the candidate's
    oxygen-deficit signal is non-decreasing under every admissible mapping; the rising pressure lowers only the perfusion
    signal, which is what tone compensation physiologically restores."""
    rows = ca._record(P2L1_RECORD, P2L1_RECORD_SHA)["tone_loop"]["rows"]
    out = {}
    for name, minutes in rows.items():
        deficits = [m["deficit"] for m in minutes]
        sbps = [m["sbp"] for m in minutes]
        out[name] = {"deficit_non_decreasing": all(b >= a for a, b in zip(deficits, deficits[1:])),
                     "pressure_non_decreasing": all(b >= a for a, b in zip(sbps, sbps[1:])),
                     "legacy_level_fell": minutes[-1]["level"] < minutes[0]["level"]}
    inverted = sorted(k for k, v in out.items() if v["legacy_level_fell"])
    return {"rows": out, "legacy_inverted": inverted,
            "candidate_inversion_removed": all(out[k]["deficit_non_decreasing"] for k in out)}


def extreme_acidemia() -> dict:
    """The carried P2K-5 subset, classified structurally by the candidate's signals (no bound chosen, nothing filtered)."""
    p2l1 = ca._record(P2L1_RECORD, P2L1_RECORD_SHA)
    x = p2l1["extreme_acidemia"]
    lowest = x["lowest"]
    pressure = x["untreated_pressure_57m_d1.1"]
    map_low = min(p["map120"]["low"] for p in pressure.values())
    map_high = max(p["map120"]["high"] for p in pressure.values())
    subset_ceiling = 7.0
    arrival_abg = p2l1["authored"][lowest["case"]]["abg"]["value"]
    return {"flagged": x["flagged"], "by_case": x["by_case"], "survivors": x["survivors"], "unit": x["unit"],
            "classification": x["classification"], "filtered": False,
            "ph_range": [lowest["ph"], subset_ceiling], "lowest": lowest, "map120_range": [map_low, map_high],
            "arrival_abg": arrival_abg,
            "signals": {
                "acidemia": "POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: every row lies below pH 7.00, the most acidemic "
                            "rows of the candidate set, so their acidemia signal is the set's highest under every "
                            "admissible mapping; it is 0 for every row only if the normal bound is at or below the lowest "
                            "pH (6.961) and positive for every row once the normal bound is at or above 7.00",
                "hypercapnia": "ZERO_UNDER_EVERY_ADMISSIBLE_MAPPING at the lowest row (PaCO2 "
                               f"{lowest['paco2']:.1f}, below the case's authored arrival PaCO2 ({arrival_abg})): a "
                               "metabolic acidemia with respiratory compensation; pH and PaCO2 kept apart",
                "cerebral_hypoperfusion": "POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: untreated MAP at minute 120 between "
                                          f"{map_low:.1f} and {map_high:.1f} mmHg",
                "oxygen_deficit": "POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: the lowest row carries a deficit of "
                                  f"{lowest['deficit']:.3f}"},
            "aggregation": "three independent signals can read positive in these rows; the observable is their "
                           "maximum, so one shock is not counted three times",
            "reading": "kept as CONSCIOUSNESS_COLLAPSE_REVIEW, never filtered: once bounds exist these rows read impaired "
                       "through acidemia, perfusion and delivery alike; no bound is fitted to make them impaired, and "
                       "their collapse question belongs to the collapse architecture"}


# 6. Generalization (P2L-2-11), the pharmacologic note (P2L-2-12), identifiability (P2L-2-13) -----------------------------------

GENERALIZATION = {
    "A_hemorrhagic_shock": ({"cerebral_hypoperfusion": 0.6, "oxygen_deficit": 0.7, "acidemia": 0.5}, 0.0,
                            "shock_and_acidemia", "the bleed's own writers (volume, Hb); shared perfusion and delivery"),
    "B_severe_hypoglycaemia": ({"hypoglycaemia": 0.8}, 0.0, "hypoglycaemia",
                               "a glucose writer and dextrose: none in the core yet (the family's own contributor)"),
    "C_hypercapnic_opioid_physiology": ({"hypercapnia": 0.7, "acidemia": 0.3}, 0.0, "acute_hypercapnia",
                                        "the ventilation efficiency or drive the family lowers; its primary CNS "
                                        "depression is a future pharmacologic modifier, not N"),
    "D_primary_stroke": ({}, 0.7, None, "N, the primary neurologic family's own writer (no kinetics here)"),
    "E_severe_hypoxaemia": ({"hypoxaemia": 0.8}, 0.0, "E2_fio2_falls_to_room_air",
                            "a gas-exchange writer (SpO2 moves only with FiO2 in the core today)"),
    "F_distributive_shock": ({"cerebral_hypoperfusion": 0.6}, 0.0, "A_low_map_no_deficit",
                             "tone (vasodilation): the MAP path apart from the deficit")}
GENERALIZATION_CLASSES = ("COMMON_NEUROLOGIC_ARCHITECTURE_PLAUSIBLE", "STRUCTURAL_GAP")


def generalization(physiology: dict, scan: dict) -> dict:
    rows = {}
    k = _steps(PROLONGED)
    for name, (signals, primary, carrier, writer) in GENERALIZATION.items():
        c = course([(PROLONGED, signals), (RECOVERY, {})], primary=primary)
        systemic = bool(signals)
        lag = c["burden"][k] > 0.0 and c["impairment"][k] > primary
        carried = carrier is None or all(set(physiology[g][carrier]["positive"]) >= set(signals) for g in physiology)
        rows[name] = {"signals": signals, "primary": primary, "stress": c["stress"][k - 1],
                      "impairment_during": c["impairment"][k - 1], "impairment_after_restoration": c["impairment"][k],
                      "lag": lag, "physiological_carrier": carrier, "carrier_reads_the_signals": carried,
                      "writer": writer,
                      "represented": c["impairment"][k - 1] == max([primary, *signals.values()]) and carried
                      and (lag if systemic else c["burden"][-1] == 0.0)}
    plausible = all(r["represented"] for r in rows.values()) and not scan["disease_terms"]
    return {"rows": rows, "result": GENERALIZATION_CLASSES[0 if plausible else 1],
            "reading": "one composition for every family: the systemic families through the six generic signals and the "
                       "one memory, the primary family through N without loading the memory; no family term in the "
                       "physiology; what each family still needs is its own writer of the signal, not a consciousness "
                       "rule"}


PHARMACOLOGIC = enc.FUTURE_MODIFIERS["pharmacologic_cns_depression"]
IDENTIFIABILITY = {
    "signal_bounds": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: twelve bounds (normal, severe per signal), "
                     "UNMAPPED; the GI cases carry no post-arrival neurologic observation",
    "ramp_shape": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED (linear provisional)",
    "memory_time_constants": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: tau_rise < tau_clear, UNSET; never "
                             "derived from tau_D",
    "n_scale": "STRUCTURALLY_DEFINED (the common scale); no case value",
    "arrival_burden": "STRUCTURALLY_DEFINED: 0 unless a case declares a pre-arrival insult; never from an authored label",
    "category_mapping": "UNDEFINED: no impairment-to-category mapping (pending faculty)",
    "well_constrained": "none: synthetic probes constrain structure only"}
TRAJECTORIES = ("NOT_GENERATED: no signal mapping or memory constant exists independently of GI outcomes (P2L-2-10); "
                "inventing them to draw C1-C4 would be the fitting the faculty forbade: STRUCTURAL_ONLY")


# 7. Non-regression, readiness, next step ----------------------------------------------------------------------------------------

OWN = ("clinical_core/encephalopathy.py", "clinical_core/encephalopathy_architecture.py")
REPORT = "clinical_core/encephalopathy_architecture_report.py"
#: The two tuple-only files at P2L-1 (d88f125): P2L-2 adds its analysis modules to their tuples, nothing else.
TUPLE_AT_P2L1 = {"clinical_core/lactate_slice.py": "1cd8288640d38159c71e109fd0a8412c510b3c160041e852ed6e809f27111650",
                 "clinical_core/decision_pack.py": "39a7ed9b3ac9ccfef4263f6d9c1f4cd7268e7214d71c0ce2be01ece856f380a4"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[1], REPORT)}
#: The whole P2L-1 tree's source map (64 files, d88f125): every core and closed analysis file byte-identical.
SOURCES_AT_P2L1 = ("f63cbb93ace102622b46de7f62bc6e6d1473bf8e78f63fe6a515d4859cc924fa", 64)


def p2l1_sources(sources: dict) -> dict:
    """A P2L-1 dependency map: P2L-2's modules removed, the two tuple-only files at their P2L-1 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2L1.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def upstream_unchanged() -> dict:
    mapped = p2l1_sources(bf.freeze_sources())
    digest = hashlib.sha256(json.dumps(mapped, sort_keys=True).encode("utf-8")).hexdigest()
    return {"digest": digest, "files": len(mapped), "unchanged": (digest, len(mapped)) == SOURCES_AT_P2L1,
            "imported_by": imported_by()}


READY = "COMMON_CONSCIOUSNESS_ARCHITECTURE_READY"
NOT_READY = "COMMON_CONSCIOUSNESS_ARCHITECTURE_NOT_READY"
CRITERIA = ("n_reserved_for_primary", "systemic_acute_separate", "memory_gives_recovery_lag", "signals_causally_explicit",
            "maximum_aggregation", "lactate_not_controller", "legacy_retired_from_candidate", "primary_n_independent",
            "generalization_passes", "upstream_unchanged", "nothing_approved")
VERDICT_RULE = ("Predeclared. READY iff every criterion holds; otherwise NOT_READY - the first failing criterion as the "
                "blocker, every failing criterion listed. A changed upstream file stops the run before any probe.")
NEXT_RULE = (
    "Predeclared. READY: additional numeric consciousness calibration is not required before testing generalization "
    "(the GI cases cannot identify it): DO_NOT_OVERFIT_GI. Next by causal necessity: COLLAPSE_SAFETY_ARCHITECTURE if the "
    "carried subset still needs collapse review with collapse off (every shock family, GI included, needs it before "
    "migration), else SECOND_FAMILY_GENERALIZATION. NOT_READY: the blocker and the smallest correction.")
DECISIONS = (
    "the twelve signal bounds (normal, severe) as clinical decisions from general physiology, never from the GI cases; "
    "MAP absolute or relative to the patient's autoregulation (chronic hypertension)",
    "the memory's tau_rise and tau_clear, and whether one memory serves every insult or the clearance differs by cause",
    "the mapping from the impairment I to an observed mental-status category (or a GCS-like scale): needed before any "
    "observable",
    "the acidemia signal on total pH (as decided: an acute hypercapnia co-signals it, the maximum keeps one) or on the "
    "metabolic component",
    "the future pharmacologic CNS-depression signal: whether it loads the systemic memory or carries its own kinetics",
    "how a case declares an arrival impairment (N, a pre-arrival burden F0, another cause) instead of a mental-status "
    "label",
    "the closed wording of N (state.py) and of derive's ladders (derived.PARAMETERS), updated at runtime integration",
    "the carried extreme-acidemia subset: stays CONSCIOUSNESS_COLLAPSE_REVIEW for the collapse architecture")
POLICY = ("Shadow only: one candidate physiology module no core step reads (encephalopathy.py) and this analysis; no core "
          "file, channel, rule or parameter changed; synthetic normalized probes and fixed core states read through the "
          "certified core; committed records read with pinned hashes; the legacy ladder kept as reference, never fitted; "
          "the extreme-acidemia rows kept; nothing selected or approved; collapse off.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no runtime integration, GI or second-family migration, consciousness threshold "
                  "or parameter approval, numeric consciousness filtering or collapse activation is authorized")


def verdict(checks: dict) -> dict:
    failing = [c for c in CRITERIA if checks.get(c) is False]
    missing = [c for c in CRITERIA if c not in checks]
    if not failing and not missing:
        return {"verdict": READY, "checks": checks, "failing": [], "not_evaluated": []}
    return {"verdict": f"{NOT_READY} - {(failing + missing)[0].upper()}", "checks": checks, "failing": failing,
            "not_evaluated": missing}


def recommendation(v: dict, acidemia: dict | None) -> dict:
    if v["verdict"] != READY:
        return {"recommendation": "STOP_FOR_STRUCTURAL_CORRECTION", "blocker": v["verdict"], "rule": NEXT_RULE,
                "decisions": list(DECISIONS)}
    collapse = bool(acidemia and acidemia["flagged"] > 0 and not acidemia["filtered"])
    return {"numeric_calibration_required_before_generalization": False, "strategy": "DO_NOT_OVERFIT_GI",
            "recommendation": "COLLAPSE_SAFETY_ARCHITECTURE" if collapse else "SECOND_FAMILY_GENERALIZATION",
            "why": "the consciousness architecture needs no more GI numbers to be tested; the carried subset (untreated "
                   "pH below 7.00, MAP 32-46 at minute 120) keeps a pulse because collapse is off, and every shock family "
                   "needs a collapse safety architecture before migration; a non-shock second family (hypoglycaemia, "
                   "hypercapnia) is causally independent of collapse and can follow" if collapse else
                   "no carried subset needs collapse review",
            "rule": NEXT_RULE, "decisions": list(DECISIONS)}


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "status": STATUS,
            "physiology_status": enc.STATUS, "signals": {k: list(v) for k, v in enc.SIGNALS.items()},
            "future_modifiers": enc.FUTURE_MODIFIERS,
            "probe": {"rise_tau": PROBE_RISE_TAU, "clear_ratios": list(CLEAR_RATIOS), "clear_ratio": PROBE_CLEAR_RATIO,
                      "dt": PROBE_DT, "intensity": INTENSITY, "severe": SEVERE, "brief": BRIEF, "prolonged": PROLONGED,
                      "recovery": RECOVERY, "residual": RESIDUAL, "shock": SHOCK, "single": SINGLE,
                      "multiple": MULTIPLE, "n12": [N12_PRIMARY, N12_SYSTEMIC]},
            "neuro_probes": NEURO_PROBES, "memory_proof": MEMORY_PROOF, "gains": list(GAINS),
            "physiology_rule": PHYSIOLOGY_RULE,
            "physiology_probes": {k: [v[0], v[1], list(v[2]), v[3]] for k, v in PHYSIOLOGY_PROBES.items()},
            "orthogonality": {k: list(v) for k, v in ORTHOGONALITY.items()},
            "forbidden_reads": list(FORBIDDEN_READS), "forbidden_terms": list(FORBIDDEN_TERMS), "legacy": LEGACY,
            "generalization": {k: [v[0], v[1], v[2], v[3]] for k, v in GENERALIZATION.items()},
            "pharmacologic": PHARMACOLOGIC, "identifiability": IDENTIFIABILITY, "trajectories": TRAJECTORIES,
            "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE, "next_rule": NEXT_RULE,
            "decisions": list(DECISIONS), "policy": POLICY, "migration_gate": MIGRATION_GATE, "own": list(OWN),
            "report": REPORT, "tuple_at_p2l1": TUPLE_AT_P2L1, "tuples_added": {k: list(v) for k, v in
                                                                              TUPLES_ADDED.items()},
            "sources_at_p2l1": list(SOURCES_AT_P2L1), "records": {"p2l1": P2L1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2l1": hashlib.sha256(P2L1_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    with lr.P2FGuard(), lr.LegacyLock():
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "design": design(), "approval": STATUS["approved"], "migration_gate": MIGRATION_GATE,
               "upstream": upstream_unchanged()}
        checks = {"nothing_approved": True,
                  "upstream_unchanged": out["upstream"]["unchanged"]
                  and set(out["upstream"]["imported_by"]) <= {OWN[1], REPORT}}
        if not checks["upstream_unchanged"]:
            out["stopped"] = "an upstream file changed or a core module reads the candidate: STOP"
            out["verdict"] = verdict(checks)
            out["recommendation"] = recommendation(out["verdict"], None)
            return out
        COURSE_STEPS.clear()
        scan = candidate_scan()
        physiology = physiology_probes()
        out.update({"scan": scan, "n": n_audit(), "legacy": LEGACY, "neuro_probes": neuro_probes(),
                    "ratio_robustness": ratio_robustness(), "memory_proof": MEMORY_PROOF, "physiology": physiology,
                    "orthogonality": orthogonality(physiology), "tone_loop": tone_loop(),
                    "extreme_acidemia": extreme_acidemia(), "generalization": generalization(physiology, scan),
                    "pharmacologic": PHARMACOLOGIC, "identifiability": IDENTIFIABILITY, "trajectories": TRAJECTORIES})
        probes = out["neuro_probes"]["rows"]
        wired = all(row["wired"] for rows in physiology.values() for row in rows.values())
        checks["n_reserved_for_primary"] = (scan["reads_n_only_through"] == "primary_from_state"
                                            and not scan["writes_state"] and "N" not in enc.SIGNALS
                                            and all(v[0] != "N" for v in enc.SIGNALS.values())
                                            and probes["N12"]["burden_independent_of_n"])
        checks["systemic_acute_separate"] = probes["N2"]["passes"] and probes["N12"]["passes"]
        checks["memory_gives_recovery_lag"] = (probes["N10"]["passes"] and probes["N11"]["passes"]
                                               and out["ratio_robustness"]["all_pass"])
        checks["signals_causally_explicit"] = wired and all(
            o["distinguishable"] and o["isolated_as_declared"] for o in out["orthogonality"].values()) and all(
            row["isolated_as_declared"] for rows in physiology.values() for row in rows.values())
        checks["maximum_aggregation"] = (probes["N9"]["passes"] and not scan["sum_calls"]
                                         and not any(scan["aggregation_adds"].values())
                                         and all(scan["aggregation_by_max"].values()))
        checks["lactate_not_controller"] = not ({"lactate", "lactate_excess_mmol_l"} & set(scan["forbidden_reads"]))
        checks["legacy_retired_from_candidate"] = (not scan["forbidden_reads"]
                                                   and out["tone_loop"]["candidate_inversion_removed"]
                                                   and all(rows["arrival_label_obtunded"]["positive"] == []
                                                           and rows["arrival_label_obtunded"]["reading"]
                                                           == rows["reference"]["reading"]
                                                           for rows in physiology.values()))
        checks["primary_n_independent"] = (probes["N2"]["passes"] and out["n"]["readers"] != []
                                           and all(rows["primary_n_only"]["positive"] == []
                                                   and rows["primary_n_only"]["primary_n"] == 0.5
                                                   for rows in physiology.values()))
        checks["generalization_passes"] = out["generalization"]["result"] == GENERALIZATION_CLASSES[0]
        checks["nothing_approved"] = (enc.DEFAULT_ENCEPHALOPATHY.mappings == ()
                                      and not enc.DEFAULT_ENCEPHALOPATHY.memory_declared
                                      and all(set(row["committed_profile"].values()) == {"UNMAPPED"}
                                              for rows in physiology.values() for row in rows.values()))
        out["efficiency"] = {"fixed_state_readings": sum(len(rows) for rows in physiology.values()),
                             "synthetic_memory_steps": sum(COURSE_STEPS), "synthetic_courses": len(COURSE_STEPS),
                             "records_read": ["P2L1_consciousness_audit.json"], "integrator_steps": 0,
                             "trajectory_simulations": 0, "gi_trajectories": 0, "cartesian_sweep": False,
                             "region_rebuilt": False, "legacy_read": False}
        out["verdict"] = verdict(checks)
        out["recommendation"] = recommendation(out["verdict"], out["extreme_acidemia"])
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
        return 0
    if args.run:
        if args.out is None or ROOT in args.out.resolve().parents or args.out.resolve() == ROOT:
            parser.error("--run needs --out, a directory outside the repository")
        args.out.mkdir(parents=True, exist_ok=True)
        result = run()
        (args.out / "P2L2_encephalopathy_architecture.json").write_text(
            json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
