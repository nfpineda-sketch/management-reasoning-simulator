"""Phase 2 shadow core, P2M-2: the frozen analysis of the minimal common collapse safety layer.

    python -m clinical_core.collapse_architecture --digest
    python -m clinical_core.collapse_architecture --design
    python -m clinical_core.collapse_architecture --run --out <directory outside the repository>

Shadow only (faculty brief of 2026-11-03, recorded in FACULTY). It freezes, before the evaluation run, the structural
probes C1-C14 of the candidate (clinical_core/collapse.py: collapse_signal = max(MAP failure, delivery failure), the
existing aux.collapse_burden with repaying kinetics, the terminal transition on persistence AND current non-viability,
the explicit lag), the seven-family generalization on fixed core states, the P2M-1 supersession, the parameter status,
the carried GI extreme subset (diagnostic, unclassified), the upstream non-regression, the criteria, the verdict and the
strategic exit rule. It changes no core file, writes no channel, approves no number and activates nothing: every
clinical slot stays UNSET and every number a probe declares is SYNTHETIC_ONLY.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import collapse as cx
from . import derived as dv
from . import lactate_rebuild as lr
from . import vascular_tone as vt
from . import ventilation_surface as vs
from .integration import step
from .modules.rhythm_events import ScriptedPumpChange, ScriptedRhythmEvent
from .state import CoreInvariantError, RhythmCode, RhythmState, UnresolvedBoundary

DECIDED = "2026-11-03"
REVISION = "P2M-2"
ROOT = vs.ROOT
CORE_DIR = ROOT / "clinical_core"
P2M1_RECORD = ROOT / "docs" / "revision" / "P2M1_collapse_audit.json"
P2M1_RECORD_SHA = "443df2b4d4a3bb5e04a28ddff2fb98ff7939ed375c3d9cc60cc14179657c8df5"
CANDIDATE_SOURCE = CORE_DIR / "collapse.py"

FACULTY = {
    "brief": "P2M-2 minimal common collapse safety layer (2026-11-03): structural; no clinical threshold chosen",
    "signal": "collapse_signal = MAX(perfusion_failure_signal, oxygen_delivery_failure_signal); never a sum; no Q, "
              "direct SpO2, P, R, lactate, D, pH, I or F as a graded input",
    "perfusion": "MAP is the source; its clinical mapping stays UNSET_CLINICAL_MAPPING; synthetic tests may inject the "
                 "normalized value",
    "delivery": "the certified effective oxygen-delivery deficit, not recalibrated, not replaced by D or lactate",
    "spo2": "direct SpO2 DEFERRED: oxygenation already reaches oxygen content and DO2; revisit in generalization",
    "q_p_r": "Q reaches MAP and DO2; P and R reach Q; rhythm stays authoritative for pulse_present; a no-pulse rhythm is "
             "arrest, not collapse",
    "pulse": "pulse_present is the effective perfusing rhythm state, not a guaranteed palpable pulse; pulse with an "
             "extremely low MAP is allowed as transient profound collapse; never derived from pressure",
    "zero_flow": "pulse=true + Q=0 stays an inconsistent state that fails loudly; not a clinical arrest rule; near-zero Q "
                 "with a pulse stays representable",
    "persistence": "the existing aux.collapse_burden; no second persistence variable, no consecutive-minute counter; "
                   "non-negative, 0 at arrival by default, arrival signal from the actual arrival physiology, rises "
                   "while the signal persists, repays as it improves, tends monotonically to 0 at zero signal, never "
                   "arrests alone, terminal needs persistence AND current non-viability, reset or frozen at the "
                   "transition; never from tau_D, lactate or the encephalopathy memory; numbers UNSET",
    "order": "EXPLICIT_LAG_REQUIRED: state(t) -> derive(t) -> collapse_signal(t) -> burden -> terminal decision -> "
             "terminal rhythm / pulse transition -> state(t+1); no recursive same-step loop",
    "terminal_rhythm": "TERMINAL_RHYTHM_PHENOTYPE_UNSET; the existing machinery only for structural tests",
    "rosc": "ROSC_NOT_CURRENTLY_MODELED; no ACLS; the architecture must not make a future ROSC impossible",
    "gi_subset": "57m, demand 1.1, 17,604 rows, untreated pH < 7.00, MAP about 32.5-46.3, pulse present: diagnostic "
                 "only, never used to choose a threshold, never classified as arrest / non-arrest while UNSET",
    "scope": "shadow only: no clinical threshold, GI collapse filtering, ROSC / ACLS, runtime activation, GI or "
             "second-family migration"}

# 1. Synthetic settings (SYNTHETIC_ONLY, never approvals) ----------------------------------------------------------------

#: The probe arrival's own MAP (90 mmHg: bands.ARRIVAL 120 / 75) and 0: a reference-anchored ramp that reads 0 at the
#: neutral reference (C1); not a clinical bound.
SYNTHETIC_MAP = (90.0, 0.0)
SYNTHETIC_TAU, SYNTHETIC_TERMINAL, SYNTHETIC_FLOOR, SYNTHETIC_RHYTHM = 30.0, 10.0, 0.5, "pea"
SYNTHETIC_RULE = ("SYNTHETIC_ONLY: perfusion mapping (viable 90, failed 0 mmHg) anchored to the neutral probe "
                  "arrival's own MAP; burden tau 30 min (P2E-3's committed synthetic repayment); terminal burden 10 "
                  "(P2E-3's synthetic limit, minutes at full signal); current non-viability floor 0.5; PEA only to "
                  "exercise the existing terminal machinery. None is a candidate, a range or an approval.")


def synthetic(terminal: bool = True) -> cx.CollapseProfile:
    mapping = cx.PerfusionMapping(*SYNTHETIC_MAP)
    if not terminal:
        return cx.CollapseProfile(mapping, SYNTHETIC_TAU)
    return cx.CollapseProfile(mapping, SYNTHETIC_TAU, SYNTHETIC_TERMINAL, SYNTHETIC_FLOOR, SYNTHETIC_RHYTHM)


ANCHORS, PROFILE = vs.PROBE_ANCHORS, vs.PROBE_PROFILE
PROBE_RULE = ("Fixed states on P2K-2's neutral probe arrival (bands.ARRIVAL with HCO3 20, extraction reserve 2.5), read "
              "through derive and derived.acute_deficit_signal: illustrative extremes, P2M-1's sizes where they exist; "
              "the respiratory probe is also read at the neutral extraction reserve 1 (DEFAULT_PROFILE's).")


def _state(spec: dict):
    """A fixed probe state: P / T / V / fio2 / D on the state, hb as a share of arrival, an aux burden, a rhythm."""
    spec = dict(spec)
    anchors, profile = ANCHORS, PROFILE
    if "arrival_fio2" in spec:
        anchors = replace(anchors, fio2=spec.pop("arrival_fio2"))
    if "arrival_pressure" in spec:
        sbp, dbp = spec.pop("arrival_pressure")
        anchors = replace(anchors, sbp=sbp, dbp=dbp)
    if "reserve" in spec:
        profile = replace(profile, oxygen_extraction_reserve=spec.pop("reserve"))
    if "hb_share" in spec:
        spec["hb"] = anchors.hb * spec.pop("hb_share")
    aux = {k: spec.pop(k) for k in ("collapse_burden", "lactate_excess_mmol_l", "metabolic_acid_burden") if k in spec}
    rhythm = spec.pop("rhythm", None)
    state = vs._probe_state(None, anchors, profile, **spec)
    if aux:
        state = state.evolve(aux=replace(state.aux, **aux))
    if rhythm is not None:
        state = state.evolve(R=rhythm, terminal_since=None if rhythm.pulse_present else state.minute)
    return state, anchors, profile


AVB = RhythmState(RhythmCode.COMPLETE_AV_BLOCK, 30.0, 0.5, True)
VT_PULSE = RhythmState(RhythmCode.VT_WITH_PULSE, 180.0, 0.3, True)


def reading(state, anchors, profile, collapse=None) -> dict:
    collapse = collapse or synthetic()
    d = dv.derive(state, anchors, profile)
    out = {"pulse": d.pulse_present, "rhythm": d.rhythm.value, "output_rel": d.output_rel, "map": d.map,
           "delivery_rel": d.delivery_rel, "spo2": d.spo2, "perfusion": None, "delivery": None, "signal": None,
           "dominant": [], "status": cx.ARREST}
    if d.pulse_present:
        signal = cx.signal_at(cx.readings(state, anchors, profile), collapse)
        out.update({"perfusion": signal.perfusion, "delivery": signal.delivery, "signal": signal.value,
                    "dominant": list(signal.dominant), "status": "COLLAPSE_SIGNAL" if signal.value > 0 else "NONE"})
    return out


# 2. C1-C14 ------------------------------------------------------------------------------------------------------------

STRUCTURAL = {
    "C1": "normal perfusion + normal delivery -> collapse_signal = 0",
    "C2": "perfusion failure only -> signal > 0", "C3": "delivery failure only -> signal > 0",
    "C4": "both abnormal -> signal = max, not sum", "C5": "Q changes with MAP / DO2 fixed -> no independent Q term",
    "C6": "SpO2 changes with effective delivery fixed -> no direct SpO2 term",
    "C7": "lactate / D / I / F (and pH) changed alone -> signal unchanged",
    "C8": "one transient severe insult -> burden rises, no terminal transition (persistence required)",
    "C9": "prolonged severe insult -> burden rises further and meets the synthetic terminal criterion",
    "C10": "near-threshold burden + physiology restored -> burden decays, no delayed arrest",
    "C11": "intermittent insults with recovery -> no indefinite accumulation",
    "C12": "pulse=false -> Q / pressure / DO2 terminal consistency", "C13": "pulse=true + Q=0 -> the invariant fires",
    "C14": "pulse=true + near-zero Q / MAP -> representable profound collapse before arrest"}
INJECTED = {"C1": (0.0, 0.0), "C2": (0.6, 0.0), "C3": (0.0, 0.5), "C4": (0.6, 0.5)}
STATE_PROBES = {"C1": {}, "C2": {"T": 0.45}, "C3": {"hb_share": 0.25}, "C4": {"P": 0.3}}
TRANSIENT = [1.0] * 3 + [0.0] * 60
PROLONGED = [0.9] * 60
RESTORED_FROM = (9.9, 12.0)
PARTIAL = 0.3
INTERMITTENT = ([1.0] * 5 + [0.0] * 25) * 48
TOL = 1e-9


def _solve(fn, target: float, lo: float, hi: float) -> float:
    """Bisection on a monotone increasing fn."""
    for _ in range(200):
        mid = (lo + hi) / 2.0
        lo, hi = (mid, hi) if fn(mid) < target else (lo, mid)
    return (lo + hi) / 2.0


def signal_cases() -> dict:
    out = {}
    for name in ("C1", "C2", "C3", "C4"):
        p, d = INJECTED[name]
        injected = cx.signal_value(p, d)
        row = reading(*_state(STATE_PROBES[name]))
        out[name] = {"injected": [p, d], "injected_signal": injected, "state": STATE_PROBES[name], "reading": row}
    c = out
    c["C1"]["pass"] = c["C1"]["injected_signal"] == 0.0 and c["C1"]["reading"]["signal"] == 0.0
    c["C2"]["pass"] = (c["C2"]["injected_signal"] == 0.6 and c["C2"]["reading"]["perfusion"] > 0.0
                       and c["C2"]["reading"]["delivery"] == 0.0 and c["C2"]["reading"]["signal"] > 0.0)
    c["C3"]["pass"] = (c["C3"]["injected_signal"] == 0.5 and c["C3"]["reading"]["perfusion"] == 0.0
                       and c["C3"]["reading"]["delivery"] > 0.0 and c["C3"]["reading"]["signal"] > 0.0)
    r4 = c["C4"]["reading"]
    c["C4"]["pass"] = (c["C4"]["injected_signal"] == 0.6 != 1.1
                       and r4["perfusion"] > 0.0 and r4["delivery"] > 0.0
                       and r4["signal"] == max(r4["perfusion"], r4["delivery"]) < r4["perfusion"] + r4["delivery"])
    return out


def no_q() -> dict:
    """C5: two states with different flow, the same MAP and the same delivery (tone and Hb solved), read alike; and
    P2M-1 review H2's flow-alone state (MAP kept, no deficit) reads no collapse signal."""
    a_state, anchors, profile = _state({"P": 0.5})
    a = reading(a_state, anchors, profile)
    pump = 0.4
    tone = _solve(lambda t: dv.derive(_state({"P": pump, "T": t})[0], anchors, profile).map, a["map"], 0.1, 3.0)
    b_flow = dv.derive(_state({"P": pump, "T": tone})[0], anchors, profile).output_rel
    hb_share = a["delivery_rel"] / b_flow
    b = reading(*_state({"P": pump, "T": tone, "hb_share": hb_share}))
    alone = reading(*_state({"P": 0.7, "T": 2.0}))
    return {"a": a, "b": b, "b_construction": {"P": pump, "T": tone, "hb_share": hb_share},
            "flow_difference": a["output_rel"] - b["output_rel"], "signal_difference": a["signal"] - b["signal"],
            "flow_alone_h2": alone,
            "pass": bool(abs(a["output_rel"] - b["output_rel"]) > 0.05 and abs(a["map"] - b["map"]) < 1e-6
                         and abs(a["delivery_rel"] - b["delivery_rel"]) < TOL and abs(a["signal"] - b["signal"]) < 1e-6
                         and a["signal"] > 0.0 and alone["output_rel"] < 0.7 and alone["signal"] == 0.0)}


def no_spo2() -> dict:
    """C6: SpO2 97 -> 73 with Hb raised in proportion: the same delivery, the same signal."""
    a_state, anchors, profile = _state({"P": 0.3, "arrival_fio2": 1.0})
    a = reading(a_state, anchors, profile)
    low_state, _, _ = _state({"P": 0.3, "arrival_fio2": 1.0, "fio2": 0.21})
    low_spo2 = dv.derive(low_state, anchors, profile).spo2
    b = reading(*_state({"P": 0.3, "arrival_fio2": 1.0, "fio2": 0.21, "hb_share": a["spo2"] / low_spo2}))
    return {"a": a, "b": b, "spo2_difference": a["spo2"] - b["spo2"],
            "pass": bool(a["spo2"] - b["spo2"] > 20.0 and abs(a["delivery_rel"] - b["delivery_rel"]) < TOL
                         and abs(a["signal"] - b["signal"]) < TOL and a["signal"] > 0.0)}


ALONE = {"D": {"D": 5.0}, "lactate": {"lactate_excess_mmol_l": 6.0}, "acid_pH": {"metabolic_acid_burden": 15.0}}
FORBIDDEN_READS = ("output_rel", "spo2", "lactate", "lactate_excess_mmol_l", "metabolic_acid_burden", "ph", "paco2", "D",
                   "P", "T", "output_factor", "consciousness_level", "sympathetic_drive", "pulse_rate_bpm",
                   "terminal_since", "glucose", "N", "oxygen_debt")
FORBIDDEN_IMPORTS = ("encephalopathy", "encephalopathy_architecture", "consciousness_audit", "collapse_audit",
                     "family_engine", "legacy_adapter", "lactate_slice", "lactate_rebuild")
FORBIDDEN_TERMS = ("gi", "bleed", "haemorrhag", "hemorrhag", "sepsis", "septic", "distributive", "anaphyla",
                   "cardiogenic", "obstructive", "embol", "tamponade", "asthma", "copd", "57m", "72f")


def candidate_scan() -> dict:
    """The candidate read as code: what it reads, writes, imports and how it aggregates."""
    tree = ast.parse(CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    attributes = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)})
    calls = sorted({getattr(n.func, "id", None) or getattr(n.func, "attr", None) for n in ast.walk(tree)
                    if isinstance(n, ast.Call)} - {None})
    imports = sorted({(n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
                     | {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names})
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    writes = sorted({k.arg for n in ast.walk(tree) if isinstance(n, ast.Call)
                     and (getattr(n.func, "id", None) or getattr(n.func, "attr", None)) in ("evolve", "replace")
                     for k in n.keywords if k.arg})
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | set(functions) | set(attributes) | {
        n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    order = functions["shadow_step"]
    calls_in_order = [(getattr(n.func, "id", None) or getattr(n.func, "attr", None), n.lineno) for n in ast.walk(order)
                      if isinstance(n, ast.Call)]
    first = {name: min(line for c, line in calls_in_order if c == name) for name in ("evaluate", "step")}
    return {"forbidden_reads": [a for a in attributes if a in FORBIDDEN_READS],
            "forbidden_imports": [i for i in imports if i.split(".")[-1] in FORBIDDEN_IMPORTS],
            "state_writes": writes, "sum_calls": "sum" in calls or "fsum" in calls,
            "signal_adds": any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add)
                               for x in ast.walk(functions["signal_value"])),
            "signal_by_max": any(isinstance(x, ast.Call) and getattr(x.func, "id", None) == "max"
                                 for x in ast.walk(functions["signal_value"])),
            "disease_terms": sorted({t for t in FORBIDDEN_TERMS for i in names
                                     if t in i.lower().split("_") or (len(t) > 3 and t in i.lower())}),
            "evaluate_calls_in_shadow_step": sum(c == "evaluate" for c, _ in calls_in_order),
            "evaluate_before_step": first["evaluate"] < first["step"],
            "evaluate_reads_start_state": all(getattr(n.args[0], "id", None) == "state" for n in ast.walk(order)
                                              if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "evaluate"),
            "imports": imports}


def no_markers() -> dict:
    """C7: lactate, D and the acid burden (pH) changed alone leave the signal; I and F cannot reach it (not read)."""
    base_state, anchors, profile = _state({"P": 0.3})
    base = reading(base_state, anchors, profile)
    rows = {}
    for name, spec in ALONE.items():
        row = reading(*_state({"P": 0.3, **spec}))
        rows[name] = {"spec": spec, "signal": row["signal"], "same": row["signal"] == base["signal"]}
    scan = candidate_scan()
    return {"base_signal": base["signal"], "rows": rows,
            "I_F": "not readable: the candidate imports neither the encephalopathy candidate nor any consciousness code",
            "pass": bool(all(r["same"] for r in rows.values()) and base["signal"] > 0.0
                         and not scan["forbidden_reads"] and not scan["forbidden_imports"])}


def persistence() -> dict:
    prof = synthetic()
    ceiling = cx.one_minute_ceiling(SYNTHETIC_TAU)
    transient = cx.burden_course(TRANSIENT, prof)
    prolonged = cx.burden_course(PROLONGED, prof)
    restored = {str(b): cx.burden_course([0.0] * 120, prof, b) for b in RESTORED_FROM}
    partial = cx.burden_course([PARTIAL] * 120, prof, RESTORED_FROM[1])
    intermittent = cx.burden_course(INTERMITTENT, prof)
    peaks = [max(intermittent[i:i + 31]) for i in range(0, len(INTERMITTENT), 30)]
    floor_refused = False
    try:
        cx.CollapseProfile(cx.PerfusionMapping(*SYNTHETIC_MAP), SYNTHETIC_TAU, ceiling, SYNTHETIC_FLOOR)
    except CoreInvariantError:
        floor_refused = True
    without_floor = False
    try:
        cx.CollapseProfile(cx.PerfusionMapping(*SYNTHETIC_MAP), SYNTHETIC_TAU, SYNTHETIC_TERMINAL)
    except CoreInvariantError:
        without_floor = True
    monotone = lambda s: all(b > a for a, b in zip(s, s[1:]))  # noqa: E731
    falling = lambda s: all(b < a for a, b in zip(s, s[1:]))  # noqa: E731
    c8 = {"peak": max(transient), "one_minute_ceiling": ceiling, "terminal": cx.first_terminal(TRANSIENT, prof),
          "single_minute_limit_refused": floor_refused}
    c8["pass"] = bool(transient[3] > 0.0 and c8["peak"] < SYNTHETIC_TERMINAL and c8["terminal"] is None
                      and floor_refused and ceiling < 1.0)
    c9 = {"terminal_minute": cx.first_terminal(PROLONGED, prof), "burden_at_3": prolonged[3],
          "burden_at_14": prolonged[14], "burden_at_60": prolonged[60]}
    c9["pass"] = bool(monotone(prolonged) and prolonged[14] > max(transient) and c9["terminal_minute"] is not None)
    c10 = {"from": {b: {"after_60": s[60], "after_120": s[120], "falls_monotonically": falling(s),
                        "terminal": cx.first_terminal([0.0] * 120, prof, float(b))} for b, s in restored.items()},
           "partial_signal": PARTIAL, "partial_after_120": partial[120], "partial_ceiling": PARTIAL * SYNTHETIC_TAU,
           "partial_terminal": cx.first_terminal([PARTIAL] * 120, prof, RESTORED_FROM[1]),
           "terminal_without_floor_refused": without_floor}
    c10["pass"] = bool(all(v["falls_monotonically"] and v["terminal"] is None for v in c10["from"].values())
                       and c10["partial_terminal"] is None and partial[120] < RESTORED_FROM[1] and without_floor)
    c11 = {"pattern": "5 min at 1.0, 25 min at 0, for 24 h", "cycle_peaks_first_last": [peaks[0], peaks[-1]],
           "peak_growth_last_cycle": peaks[-1] - peaks[-2], "max": max(intermittent), "bound": SYNTHETIC_TAU,
           "terminal": cx.first_terminal(INTERMITTENT, prof)}
    c11["pass"] = bool(abs(c11["peak_growth_last_cycle"]) < 1e-6 and max(intermittent) < SYNTHETIC_TAU
                       and c11["terminal"] is None)
    return {"C8": c8, "C9": c9, "C10": c10, "C11": c11,
            "burden_updates": sum(len(s) - 1 for s in [transient, prolonged, partial, intermittent, *restored.values()]),
            "form": "b(t+1) = b(t) e^(-1/tau) + s(t) tau (1 - e^(-1/tau)): exact first-order relaxation toward s tau"}


def no_pulse() -> dict:
    """C12-C14 on fixed states."""
    vf_state, anchors, profile = _state({"rhythm": RhythmState.vf(), "collapse_burden": 4.0})
    d = dv.derive(vf_state, anchors, profile)
    m = cx.evaluate(vf_state, anchors, profile, synthetic())
    after, _, shadow = cx.shadow_step(vf_state, (), anchors, profile, synthetic())
    c12 = {"output_rel": d.output_rel, "map": d.map, "delivery_rel": d.delivery_rel, "spo2": d.spo2,
           "status": m.status, "burden_after": m.burden_after, "next_minute_pulse": after.R.pulse_present,
           "next_minute_burden": after.aux.collapse_burden, "transition": shadow.applied}
    c12["pass"] = bool(d.output_rel == 0.0 and d.map is None and d.delivery_rel == 0.0 and d.spo2 is None
                       and m.status == cx.ARREST and m.burden_after == 0.0 and not after.R.pulse_present
                       and after.aux.collapse_burden == 0.0 and shadow.applied is None)
    zero_state, _, _ = _state({"P": 1e-12})
    fired = {}
    for label, fn in (("evaluate", lambda: cx.evaluate(zero_state, anchors, profile, synthetic())),
                      ("shadow_step", lambda: cx.shadow_step(zero_state, (), anchors, profile, synthetic())),
                      ("rhythm", lambda: RhythmState(RhythmCode.SINUS, 80.0, 0.0, True))):
        try:
            fn()
            fired[label] = "NOT_FIRED"
        except (UnresolvedBoundary, CoreInvariantError) as error:
            fired[label] = type(error).__name__
    c13 = {"fired": fired, "pass": all(v != "NOT_FIRED" for v in fired.values())}
    near = {label: reading(*_state(spec)) for label, spec in (("P_0_02", {"P": 0.02}),
                                                              ("P_0_1_avb", {"P": 0.1, "rhythm": AVB}))}
    first = cx.evaluate(_state({"P": 0.02})[0], anchors, profile, synthetic())
    c14 = {"rows": near, "first_minute_terminal": first.terminal_due, "first_minute_burden": first.burden_after}
    c14["pass"] = bool(all(r["pulse"] and r["status"] == "COLLAPSE_SIGNAL" and r["map"] < 5.0 for r in near.values())
                       and not first.terminal_due)
    return {"C12": c12, "C13": c13, "C14": c14, "readings": 6, "steps": 1}


# 3. Event order, deferral, arrival, ROSC (trajectories on fixed probe physiology) ----------------------------------------

ORDER_MINUTES = 20


def _course(state, anchors, profile, collapse, minutes, contributors=()):
    rows = []
    for _ in range(minutes):
        before = state
        state, record, shadow = cx.shadow_step(state, contributors, anchors, profile, collapse)
        c = shadow.collapse
        rows.append({"minute": state.minute, "read_minute": c.minute, "status": c.status, "signal": c.signal,
                     "burden_before": c.burden_before, "burden": state.aux.collapse_burden,
                     "due": c.terminal_due, "applied": shadow.applied, "deferred": shadow.deferred,
                     "rhythm": state.R.code.value, "pulse": state.R.pulse_present,
                     "transitions": len(record.transitions), "start_pulse": before.R.pulse_present})
    return state, rows


def event_order() -> dict:
    state, anchors, profile = _state({"P": 0.1})
    _, rows = _course(state, anchors, profile, synthetic(), ORDER_MINUTES)
    applied = [r for r in rows if r["applied"]]
    after = [r for r in rows if applied and r["minute"] > applied[0]["minute"]]
    scan = candidate_scan()
    deferral_event = ScriptedRhythmEvent(id="probe_avb", at_minute=14, target=AVB, preventability="not assessed")
    _, deferred = _course(state, anchors, profile, synthetic(), 16, (deferral_event,))
    vf_event = ScriptedRhythmEvent(id="probe_vf", at_minute=5, target=RhythmState.vf(), preventability="not assessed")
    _, scripted = _course(state, anchors, profile, synthetic(), 6, (vf_event,))
    stale_state, _, _ = _state({"collapse_burden": 10.5})
    stale, _, stale_minute = cx.shadow_step(stale_state, (), anchors, profile, synthetic())
    out = {"terminal_minute": applied[0]["minute"] if applied else None, "transitions": len(applied),
           "burden_when_met": rows[applied[0]["minute"] - 1]["burden_before"] if applied else None,
           "reads_start_state": all(r["read_minute"] == r["minute"] - 1 for r in rows),
           "after_transition": {"statuses": sorted({r["status"] for r in after}),
                                "burdens": sorted({r["burden"] for r in after}), "pulse": any(r["pulse"] for r in after)},
           "code": {k: scan[k] for k in ("evaluate_calls_in_shadow_step", "evaluate_before_step",
                                         "evaluate_reads_start_state")},
           "deferral": {"minute_14": {k: deferred[13][k] for k in ("due", "deferred", "applied", "rhythm")},
                        "minute_15": {k: deferred[14][k] for k in ("status", "signal", "due", "applied", "rhythm")}},
           "scripted_arrest": {"burden_before": scripted[4]["burden_before"], "burden_after": scripted[4]["burden"],
                               "pulse": scripted[4]["pulse"]},
           "stale_burden_normal_physiology": {"burden_before": 10.5, "signal": stale_minute.collapse.signal,
                                              "burden_after": stale.aux.collapse_burden,
                                              "pulse": stale.R.pulse_present, "transition": stale_minute.applied},
           "trajectory_steps": ORDER_MINUTES + 16 + 6 + 1, "rows": rows}
    out["pass"] = bool(
        out["transitions"] == 1 and out["terminal_minute"] == cx.first_terminal([0.9] * ORDER_MINUTES, synthetic())
        and out["reads_start_state"] and out["after_transition"]["statuses"] == [cx.ARREST]
        and out["after_transition"]["burdens"] == [0.0] and not out["after_transition"]["pulse"]
        and scan["evaluate_calls_in_shadow_step"] == 1 and scan["evaluate_before_step"]
        and scan["evaluate_reads_start_state"]
        and deferred[13]["due"] and deferred[13]["deferred"] and deferred[13]["applied"] is None
        and deferred[13]["rhythm"] == "complete_av_block" and deferred[14]["status"] == cx.EVALUATED
        and deferred[14]["applied"] == SYNTHETIC_RHYTHM
        and scripted[4]["burden_before"] > 0.0 and scripted[4]["burden"] == 0.0 and not scripted[4]["pulse"]
        and stale_minute.collapse.signal == 0.0 and stale.aux.collapse_burden < 10.5 and stale.R.pulse_present
        and stale_minute.applied is None)
    return out


ARRIVAL_LOW = (95.0, 57.5)
ARRIVAL_MINUTES = 30


def arrival() -> dict:
    """The arrival burden is 0 by default and the arrival signal is the arrival physiology's, never forced to 0."""
    rows = {}
    for label, spec in (("reference", {}), ("authored_map_70", {"arrival_pressure": ARRIVAL_LOW})):
        state, anchors, profile = _state(spec)
        first = cx.evaluate(state, anchors, profile, synthetic())
        final, course = _course(state, anchors, profile, synthetic(), ARRIVAL_MINUTES)
        rows[label] = {"arrival_burden": state.aux.collapse_burden, "arrival_map": dv.derive(state, anchors, profile).map,
                       "arrival_signal": first.signal, "burden_after_30": final.aux.collapse_burden,
                       "terminal": any(r["applied"] for r in course)}
    low = rows["authored_map_70"]
    expected = (SYNTHETIC_MAP[0] - 70.0) / (SYNTHETIC_MAP[0] - SYNTHETIC_MAP[1])
    return {"rows": rows, "expected_low_signal": expected, "steps": 2 * ARRIVAL_MINUTES,
            "pass": bool(rows["reference"]["arrival_burden"] == 0.0 == rows["reference"]["arrival_signal"]
                         and rows["reference"]["burden_after_30"] == 0.0 and low["arrival_burden"] == 0.0
                         and abs(low["arrival_signal"] - expected) < 1e-9 and low["burden_after_30"] > 0.0
                         and not low["terminal"] and cx.DEFAULT_COLLAPSE == cx.CollapseProfile())}


def rosc() -> dict:
    """ROSC is not modelled; after a shadow terminal transition the burden is 0, and a state a future return of
    circulation would produce (a perfusing rhythm, terminal_since cleared by that future core rule) is evaluated like any
    other from that reset burden: the candidate reads no terminal_since, so nothing here makes a future return
    impossible."""
    state, anchors, profile = _state({"P": 0.1})
    arrested, _ = _course(state, anchors, profile, synthetic(), 15)
    post = arrested.evolve(R=state.R, terminal_since=None, P=0.6)
    m = cx.evaluate(post, anchors, profile, synthetic())
    source = (CORE_DIR / "integration.py").read_text(encoding="utf-8")
    scan = candidate_scan()
    return {"status": cx.ROSC_NOT_CURRENTLY_MODELED, "post_arrest_pulse_state": m.status, "burden": m.burden_before,
            "candidate_reads_terminal_since": "terminal_since" in scan["forbidden_reads"],
            "core_guards": {"return_of_pulse_raises": "return of a pulse after arrest is not modelled" in source,
                            "terminal_since_never_cleared": "terminal_since if state.terminal_since is not None" in source},
            "steps": 15, "pass": bool(m.status == cx.EVALUATED and m.burden_before == 0.0
                         and "terminal_since" not in scan["forbidden_reads"])}


# 4. Generalization --------------------------------------------------------------------------------------------------------

#: family -> (what its writer moves, the fixed state, the structural logic expected).
FAMILIES = {
    "hemorrhagic": ("V and Hb fall", {"V": -300.0, "hb_share": 0.6}, "MAP + delivery failure"),
    "cardiogenic": ("P falls", {"P": 0.3}, "derived MAP / DO2 failure"),
    "obstructive": ("effective preload falls, Hb kept (no obstruction channel: the writer lowers preload)",
                    {"V": -400.0}, "derived MAP / DO2 failure"),
    "distributive": ("T falls: flow kept or raised", {"T": 0.45}, "MAP failure dominates despite preserved flow"),
    "anaphylaxis": ("T falls and V leaks", {"T": 0.45, "V": -150.0}, "the same distributive / common path"),
    "malignant_arrhythmia": ("a non-perfusing rhythm; a perfusing VT with a low output factor",
                             {"pulseless": {"rhythm": RhythmState.vf()}, "with_pulse": {"rhythm": VT_PULSE}},
                             "no-pulse rhythm = arrest; pulse-present rhythm collapses through MAP / DO2"),
    "respiratory_failure": ("SpO2 falls (FiO2 1.0 withdrawn), flow and Hb kept",
                            {"neutral_reserve": {"arrival_fio2": 1.0, "fio2": 0.21, "reserve": 1.0},
                             "probe_reserve": {"arrival_fio2": 1.0, "fio2": 0.21}},
                            "delivery failure may drive collapse without a direct SpO2 input")}


def generalization() -> dict:
    rows = {}
    for name, (what, spec, logic) in FAMILIES.items():
        if name in ("malignant_arrhythmia", "respiratory_failure"):
            rows[name] = {"what": what, "logic": logic,
                          "variants": {k: reading(*_state(v)) for k, v in spec.items()}}
        else:
            rows[name] = {"what": what, "logic": logic, "reading": reading(*_state(spec))}
    r = {k: v.get("reading") for k, v in rows.items()}
    both = lambda x: x["pulse"] and x["perfusion"] > 0.0 and x["delivery"] > 0.0  # noqa: E731
    arr, resp = rows["malignant_arrhythmia"]["variants"], rows["respiratory_failure"]["variants"]
    checks = {
        "hemorrhagic": both(r["hemorrhagic"]), "cardiogenic": both(r["cardiogenic"]),
        "obstructive": both(r["obstructive"]),
        "distributive": bool(r["distributive"]["perfusion"] > 0.0 and r["distributive"]["delivery"] == 0.0
                             and r["distributive"]["output_rel"] >= 1.0
                             and r["distributive"]["dominant"] == ["perfusion_failure"]),
        "anaphylaxis": bool(r["anaphylaxis"]["perfusion"] > 0.0 and r["anaphylaxis"]["dominant"] == ["perfusion_failure"]),
        "malignant_arrhythmia": bool(arr["pulseless"]["status"] == cx.ARREST and arr["pulseless"]["signal"] is None
                                     and both(arr["with_pulse"])),
        "respiratory_failure": bool(resp["neutral_reserve"]["perfusion"] == 0.0 and resp["neutral_reserve"]["delivery"] > 0.0
                                    and resp["neutral_reserve"]["dominant"] == ["oxygen_delivery_failure"]
                                    and resp["neutral_reserve"]["spo2"] < 80.0 and resp["probe_reserve"]["signal"] == 0.0)}
    scan = candidate_scan()
    return {"rows": rows, "checks": checks, "disease_terms": scan["disease_terms"],
            "one_function": "every family is read by the same collapse.readings / signal_at; no family branch",
            "pass": bool(all(checks.values()) and not scan["disease_terms"])}


# 5. Supersession, parameters, the carried subset, non-regression ------------------------------------------------------------

SUPERSEDED = "SUPERSEDED_BY_P2M2"
SUPERSESSION = {
    "incomplete_persistence_invariants": (
        "P2M-1 minimum: a persistence floor and a mandatory repayment, still to decide (review MEDIUM-7)",
        "the nine burden semantics formalized: repayment by construction (relaxation toward signal x tau), the floor "
        "enforced by the profile, the terminal criterion needs current non-viability", "C8-C11"),
    "stale_burden_on_rhythm_deferral": (
        "P2M-1 review HIGH-1: a burden left at the limit arrests a patient with normal output the next minute",
        "any loss of the pulse resets the burden; the terminal criterion reads the current signal, so a stale burden "
        "never arrests normal physiology", "event_order.deferral / stale_burden_normal_physiology / C10"),
    "ambiguous_arrival_zero_semantics": (
        "P2M-1 minimum 3: require a null signal at arrival (review MEDIUM-6)",
        "the arrival burden is 0 by default; the arrival signal is the arrival physiology's, never forced to 0",
        "arrival"),
    "flow_only_overstatement": (
        "P2M-1 redundancy: 'the low flow never fails alone', which held only for the chosen probes (review HIGH-2)",
        "Q is not a graded input by decision; a flow fall that keeps MAP and delivery reads no collapse signal",
        "C5 (flow_alone_h2)"),
    "probe_dependent_frozen_verdict": (
        "P2M-1's frozen redundancy_resolved / persistence_classified leaned on the probe choice (review HIGH-2, MEDIUM-7)",
        "each P2M-2 criterion is a property of the candidate checked by construction (its profile invariants and code "
        "scan) and on probes; the probes illustrate, they do not define the property", "criteria")}
PARAMETERS = {
    "map_failure_mapping": cx.UNSET_CLINICAL_MAPPING,
    "delivery_failure_threshold": "UNSET (the structural signal is the certified normalized deficit itself)",
    "burden_tau_repayment_kinetics": cx.UNSET, "terminal_burden_threshold": cx.UNSET,
    "minimum_current_nonviability": cx.UNSET, "terminal_rhythm_phenotype": cx.TERMINAL_RHYTHM_PHENOTYPE_UNSET,
    "rosc": "NOT_MODELED", "test_numbers": cx.SYNTHETIC_ONLY}


def _record(path: Path, sha: str) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"{path.name} changed after it was pinned")
    return json.loads(data)


def extreme_subset() -> dict:
    """Carried diagnostically from the pinned P2M-1 record: never filtered, never classified while the slots are UNSET."""
    e = _record(P2M1_RECORD, P2M1_RECORD_SHA)["extreme_subset"]
    return {"flagged": e["flagged"], "by_case": e["by_case"], "filtered": e["filtered"], "map120": e["map120"],
            "pulse": e["pulse"], "inputs_available": ["MAP", "effective deficit"],
            "status": "EVALUABLE_ONCE_MAPPINGS_DEFINED", "classification": None,
            "reading": "the rows keep a pulse with MAP and an effective deficit, the two inputs the layer reads; with "
                       "the MAP mapping, the kinetics and the terminal criterion UNSET no row is classified as arrest or "
                       "non-arrest and no number was chosen from them"}


OWN = ("clinical_core/collapse.py", "clinical_core/collapse_architecture.py")
REPORT = "clinical_core/collapse_architecture_report.py"
#: The two tuple-only files at P2M-1 (61628ec): P2M-2 adds its analysis module and report to their tuples, nothing else.
TUPLE_AT_P2M1 = {"clinical_core/lactate_slice.py": "c81b5ecbf6307fc30c7f2adb2e1669d397ef65d9b4c5f5d7ea2043363de5b3bb",
                 "clinical_core/decision_pack.py": "94d7ba269af29fa65e246115a1217c3f948564e904d767462d54df4f24157b57"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[1], REPORT)}
#: The whole P2M-1 tree's source map (67 files, 61628ec): every core and closed analysis file byte-identical.
SOURCES_AT_P2M1 = ("ecbcfefce945843ad063317c9ce30cb99fac50bbbf898f373cff89c438c92e2c", 67)


def p2m1_sources(sources: dict) -> dict:
    """A P2M-1 dependency map: P2M-2's modules removed, the two tuple-only files at their P2M-1 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2M1.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def imported_by() -> list:
    """Every clinical_core file that imports the candidate."""
    out = []
    for path in sorted(CORE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | {
            n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        if any(name == "collapse" or name.endswith(".collapse") for name in names):
            out.append(path.relative_to(ROOT).as_posix())
    return out


def upstream_unchanged() -> dict:
    mapped = p2m1_sources(bf.freeze_sources())
    digest = hashlib.sha256(json.dumps(mapped, sort_keys=True).encode("utf-8")).hexdigest()
    return {"digest": digest, "files": len(mapped), "unchanged": (digest, len(mapped)) == SOURCES_AT_P2M1,
            "imported_by": imported_by()}


NONREG_MINUTES = 30
PUMP_DECLINE = ("probe_pump_decline", 0, 20, -0.03)
#: The ten upstream items and the fields that carry them in a state and its derive.
NONREG_ITEMS = {"BloodState": ("blood", "V", "hb"), "output": ("output_rel",),
                "pressure_tone": ("T", "pressure_rel", "sbp", "dbp", "map"), "DO2_deficit": ("delivery_rel", "deficit"),
                "D": ("D",), "lactate": ("lactate", "lactate_excess_mmol_l"),
                "HR_baroreflex": ("pulse_rate_bpm", "sympathetic_drive"), "acid_base": ("metabolic_acid_burden",),
                "RR_W": ("respiratory_rate",), "consciousness": ("consciousness_level",)}


def _fields(state, anchors, profile) -> dict:
    d = dv.derive(state, anchors, profile)
    return {"blood": state.blood, "V": state.V, "hb": state.hb, "output_rel": d.output_rel, "T": state.T,
            "pressure_rel": d.pressure_rel, "sbp": d.sbp, "dbp": d.dbp, "map": d.map, "delivery_rel": d.delivery_rel,
            "deficit": dv.acute_deficit_signal(state, anchors, profile), "D": state.D, "lactate": d.lactate,
            "lactate_excess_mmol_l": state.aux.lactate_excess_mmol_l, "pulse_rate_bpm": d.pulse_rate_bpm,
            "sympathetic_drive": state.aux.sympathetic_drive, "metabolic_acid_burden": state.aux.metabolic_acid_burden,
            "respiratory_rate": d.respiratory_rate, "consciousness_level": d.consciousness_level}


def nonregression() -> dict:
    """The shadow layer running (kinetics declared, no terminal criterion) leaves every core field of a moving
    trajectory identical to the plain core's; only aux.collapse_burden, its own field, differs."""
    state, anchors, profile = _state({})
    contributors = (ScriptedPumpChange(*PUMP_DECLINE[:4], preventability="not assessed"),)
    plain = shadow = state
    identical = {item: True for item in NONREG_ITEMS}
    whole_state, records, burden = True, True, []
    for _ in range(NONREG_MINUTES):
        plain, plain_record = step(plain, contributors, anchors, profile)
        shadow, shadow_record, _ = cx.shadow_step(shadow, contributors, anchors, profile, synthetic(terminal=False))
        a, b = _fields(plain, anchors, profile), _fields(shadow, anchors, profile)
        for item, keys in NONREG_ITEMS.items():
            identical[item] = identical[item] and all(a[k] == b[k] for k in keys)
        whole_state = whole_state and shadow.evolve(aux=replace(shadow.aux, collapse_burden=plain.aux.collapse_burden)) \
            == plain
        records = records and shadow_record == plain_record
        burden.append(shadow.aux.collapse_burden)
    return {"minutes": NONREG_MINUTES, "contributor": list(PUMP_DECLINE), "identical": identical,
            "whole_state_but_burden": whole_state, "records_identical": records,
            "plain_burden": plain.aux.collapse_burden, "shadow_burden_last": burden[-1],
            "shadow_burden_moved": burden[-1] > 0.0, "steps": 2 * NONREG_MINUTES,
            "pass": bool(all(identical.values()) and whole_state and records and burden[-1] > 0.0
                         and plain.aux.collapse_burden == 0.0)}


# 6. Criteria, verdict, the strategic exit -----------------------------------------------------------------------------------

READY = "COMMON_COLLAPSE_SAFETY_ARCHITECTURE_READY_FOR_GENERALIZATION"
NOT_READY = "COMMON_COLLAPSE_SAFETY_ARCHITECTURE_NOT_READY"
CRITERIA = ("max_of_map_and_delivery", "no_duplicate_inputs", "persistence_repays", "historical_burden_cannot_arrest",
            "arrival_semantics", "event_order_acyclic", "no_pulse_consistent", "future_rosc_possible",
            "seven_family_probes_pass", "upstream_unchanged", "no_clinical_threshold_approved")
VERDICT_RULE = ("Predeclared. READY iff every criterion holds; otherwise NOT_READY - the first failing criterion as the "
                "blocker, every failing criterion listed. A changed upstream file stops the run before any probe.")
NEXT_RULE = ("Predeclared. READY: numeric collapse calibration is not required before second-family generalization while "
             "the layer stays shadow / inactive and can be exercised structurally without enforcing a clinical arrest: "
             "MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET; no GI collapse-calibration package "
             "is opened because thresholds stay UNSET. NOT_READY: the blocker and the smallest correction.")
DECISIONS = (
    "the MAP failure mapping (viable and failed bounds; absolute or relative to the patient's autoregulation), from "
    "general physiology, never from the GI cases",
    "whether the delivery-failure signal needs an onset threshold above the certified normalized deficit",
    "the burden time constant (one tau for accrual and repayment, as structured) and the terminal burden",
    "the minimum current non-viability floor",
    "the terminal rhythm phenotype (PEA / asystole) or its selection rule",
    "direct SpO2: stays DEFERRED unless a respiratory family shows delivery is insufficient",
    "runtime integration: the core's own collapse source replacing the scripted-rhythm primitive, and the P2E-3 output "
    "rule's retirement",
    "ROSC in a later package (the reset burden and the candidate's indifference to terminal_since keep it possible)")
POLICY = ("Shadow only: one candidate physiology module no core step reads (collapse.py) and this analysis; no core file, "
          "channel, rule or parameter changed; synthetic numbers labelled SYNTHETIC_ONLY; fixed core states and short "
          "probe trajectories read through the certified core; the P2M-1 record read with a pinned hash; the extreme "
          "subset kept and unclassified; nothing selected, approved or activated.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no clinical collapse threshold, GI collapse filtering, ROSC / ACLS, runtime "
                  "activation, GI or second-family migration is authorized")


def verdict(checks: dict) -> dict:
    failing = [c for c in CRITERIA if checks.get(c) is False]
    missing = [c for c in CRITERIA if c not in checks]
    if not failing and not missing:
        return {"verdict": READY, "checks": checks, "failing": [], "not_evaluated": []}
    return {"verdict": f"{NOT_READY} - {(failing + missing)[0].upper()}", "checks": checks, "failing": failing,
            "not_evaluated": missing}


def recommendation(v: dict) -> dict:
    if v["verdict"] != READY:
        return {"recommendation": "STOP_FOR_STRUCTURAL_CORRECTION", "blocker": v["verdict"], "rule": NEXT_RULE}
    return {"numeric_collapse_calibration_required_before_second_family": False,
            "recommendation": "MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET",
            "why": "the layer is shadow and inactive; a second family is exercised structurally with synthetic numbers, "
                   "and no family needs a clinical arrest enforced to be migrated in shadow; the clinical numbers stay "
                   "faculty decisions from general physiology",
            "rule": NEXT_RULE}


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "candidate_status": cx.STATUS,
            "inputs": {k: list(v) for k, v in cx.INPUTS.items()}, "excluded": cx.EXCLUDED,
            "synthetic": {"map": list(SYNTHETIC_MAP), "tau": SYNTHETIC_TAU, "terminal_burden": SYNTHETIC_TERMINAL,
                          "current_nonviability": SYNTHETIC_FLOOR, "terminal_rhythm": SYNTHETIC_RHYTHM,
                          "rule": SYNTHETIC_RULE},
            "probe_rule": PROBE_RULE, "structural": STRUCTURAL,
            "injected": {k: list(v) for k, v in INJECTED.items()}, "state_probes": STATE_PROBES,
            "sequences": {"transient": TRANSIENT, "prolonged": PROLONGED, "restored_from": list(RESTORED_FROM),
                          "partial": PARTIAL, "intermittent": "([1.0] * 5 + [0.0] * 25) * 48"},
            "alone": ALONE, "forbidden_reads": list(FORBIDDEN_READS), "forbidden_imports": list(FORBIDDEN_IMPORTS),
            "forbidden_terms": list(FORBIDDEN_TERMS), "order_minutes": ORDER_MINUTES,
            "arrival_low": list(ARRIVAL_LOW), "arrival_minutes": ARRIVAL_MINUTES,
            "families": {k: [v[0], json.loads(json.dumps(v[1], default=str)), v[2]] for k, v in FAMILIES.items()},
            "supersession": {k: list(v) for k, v in SUPERSESSION.items()}, "parameters": PARAMETERS,
            "nonregression": {"minutes": NONREG_MINUTES, "contributor": list(PUMP_DECLINE),
                              "items": {k: list(v) for k, v in NONREG_ITEMS.items()}},
            "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE, "next_rule": NEXT_RULE,
            "decisions": list(DECISIONS), "policy": POLICY, "migration_gate": MIGRATION_GATE, "own": list(OWN),
            "report": REPORT, "tuple_at_p2m1": TUPLE_AT_P2M1,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}, "sources_at_p2m1": list(SOURCES_AT_P2M1),
            "records": {"p2m1": P2M1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2m1": hashlib.sha256(P2M1_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    with lr.P2FGuard(), lr.LegacyLock():
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "design": design(), "approval": cx.STATUS["approved"], "migration_gate": MIGRATION_GATE,
               "upstream": upstream_unchanged()}
        checks = {"upstream_unchanged": bool(out["upstream"]["unchanged"]
                                             and set(out["upstream"]["imported_by"]) <= {OWN[1], REPORT})}
        if not checks["upstream_unchanged"]:
            out["stopped"] = "an upstream file changed or a core module reads the candidate: STOP"
            out["verdict"] = verdict(checks)
            out["recommendation"] = recommendation(out["verdict"])
            return out
        out.update({"candidate_scan": candidate_scan(), "signals": signal_cases(), "no_q": no_q(),
                    "no_spo2": no_spo2(), "no_markers": no_markers(), "persistence": persistence(),
                    "no_pulse": no_pulse(), "event_order": event_order(), "arrival": arrival(), "rosc": rosc(),
                    "generalization": generalization(), "extreme_subset": extreme_subset(),
                    "nonregression": nonregression(), "supersession": {k: {"status": SUPERSEDED, "p2m1": v[0],
                                                                           "p2m2": v[1], "evidence": v[2]}
                                                                       for k, v in SUPERSESSION.items()},
                    "parameters": PARAMETERS})
        s, per, np_, scan = out["signals"], out["persistence"], out["no_pulse"], out["candidate_scan"]
        out["structural"] = {**{k: s[k]["pass"] for k in ("C1", "C2", "C3", "C4")}, "C5": out["no_q"]["pass"],
                             "C6": out["no_spo2"]["pass"], "C7": out["no_markers"]["pass"],
                             **{k: per[k]["pass"] for k in ("C8", "C9", "C10", "C11")},
                             **{k: np_[k]["pass"] for k in ("C12", "C13", "C14")}}
        st = out["structural"]
        checks["max_of_map_and_delivery"] = all(st[k] for k in ("C1", "C2", "C3", "C4")) and scan["signal_by_max"] \
            and not scan["signal_adds"]
        checks["no_duplicate_inputs"] = all(st[k] for k in ("C5", "C6", "C7")) and not scan["sum_calls"]
        checks["persistence_repays"] = all(st[k] for k in ("C8", "C9", "C10", "C11"))
        order = out["event_order"]
        checks["historical_burden_cannot_arrest"] = bool(
            st["C10"] and order["stale_burden_normal_physiology"]["transition"] is None
            and order["scripted_arrest"]["burden_after"] == 0.0)
        checks["arrival_semantics"] = out["arrival"]["pass"]
        checks["event_order_acyclic"] = order["pass"]
        checks["no_pulse_consistent"] = all(st[k] for k in ("C12", "C13", "C14"))
        checks["future_rosc_possible"] = out["rosc"]["pass"]
        checks["seven_family_probes_pass"] = out["generalization"]["pass"]
        checks["upstream_unchanged"] = checks["upstream_unchanged"] and out["nonregression"]["pass"] and \
            dv.DEFAULT_PROFILE.collapse_output_threshold is None and dv.DEFAULT_PROFILE.collapse_burden_limit is None
        checks["no_clinical_threshold_approved"] = bool(
            cx.DEFAULT_COLLAPSE == cx.CollapseProfile(perfusion_mapping=None, burden_tau_min=None, terminal_burden=None,
                                                      current_nonviability=None, terminal_rhythm=None)
            and cx.STATUS["approved"] == "none FACULTY_APPROVED" and out["extreme_subset"]["classification"] is None
            and not out["extreme_subset"]["filtered"])
        out["efficiency"] = {"fixed_state_sections": ["signals", "no_q", "no_spo2", "no_markers", "no_pulse",
                                                      "generalization"],
                             "shadow_minutes": np_["steps"] + order["trajectory_steps"] + out["arrival"]["steps"]
                             + out["rosc"]["steps"] + out["nonregression"]["steps"],
                             "burden_updates": per["burden_updates"], "records_read": ["P2M1_collapse_audit.json"],
                             "gi_trajectories": 0, "cartesian_sweep": False, "legacy_engine_fitted": False,
                             "region_rebuilt": False}
        out["verdict"] = verdict(checks)
        out["recommendation"] = recommendation(out["verdict"])
        out["decisions"] = list(DECISIONS)
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
        (args.out / "P2M2_collapse_architecture.json").write_text(
            json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
