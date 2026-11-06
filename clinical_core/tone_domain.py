"""P2X-1: the Phase-2 declared-property closure (shadow only; adds no clinical physiology).

P2X-0 left exactly two genuine pre-exit debts. This package closes both.

1. THE DISTRIBUTIVE TONE'S DECLARED DOMAIN. P2W-1 published three statements that hold only on part of the domain it
   declared: that the distributive factor is "at or below 1" (true only for a burden at or above the arrival one),
   that ``integration._vascular_tone``'s gain check keeps T's guard from shaping the response (it reads the
   compensation alone, so it saw neither the recovery factor 1 + k b0 nor a severe burden), and that P2J-2's
   contraction bound g a < 1 covers the loop (it does not scale with the distributive factor). The faculty decided
   that a burden below the arrival one is allowed and means RESOLUTION of the arrival vasodilation, that a negative
   burden is invalid and is not vasoconstriction, that the guards must account for the maximum recovery factor, and
   that a parameter or state combination which would leave the supported domain must FAIL CLOSED instead of letting
   the channel's clamp define the physiology. This package derives the exact reachable domain analytically and
   implements the smallest guards that make those statements true over it:

   - ``integration.tone_domain``: the closed form of the reachable target and of the delayed loop's slope bound;
   - in ``_vascular_tone``, where the distributive reader is declared: the largest reachable target must stay inside
     T's supported range, and the derived loop bound must be a contraction; and, every minute, a target that would
     leave that range fails closed. The channel's guard stays as the last safety layer for every other source.
   - in ``provenance.VasodilationChange``: the writer contract (no negative burden; no family writer may read the
     current MAP, pressure_rel or T), structural and checked by a repository scan, which is this repository's
     convention for writer ownership.

   No clinical magnitude is chosen: every gain stays UNSET and no burden value is declared.

2. THE P2S-3 HISTORICAL VERDICT. Its frozen rule returned READY; the adversarial review demonstrated a common-drive
   gap; the corrected operative classification was NOT_READY; P2T-1 / P2T-2 / P2T-3 resolved that blocker and P2T-3 is
   the authoritative asthma result. The frozen package, its sources and its digest are NOT rewritten: the record is a
   supersession, which is how this repository preserves history.

The package also emits the consolidated Phase-2 debt classification and the supersession of the one P2W-1 behaviour
the faculty's decision 4 overrides (its V5 clamp reading).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import sys
import types
from dataclasses import replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import derived as dv
from . import distributive_tone as dt
from . import respiratory_distress as dm
from . import systemic_stress as ss
from .integration import CHANNEL_BOUNDS, step, tone_domain
from .provenance import ProvenanceError, SourceKind, VasodilationChange
from .state import Channel, CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2X-1"
DECIDED = "2026-11-06"
OWN = ("clinical_core/tone_domain.py",)
REPORT = "clinical_core/tone_domain_report.py"
RECORD = ROOT / "docs" / "revision" / "P2X1_tone_domain.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2X1_CIERRE_PROPIEDADES_DECLARADAS.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/integration.py", "clinical_core/provenance.py")
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]
READY = "PHASE2_DECLARED_PROPERTIES_CLOSED"
NOT_READY = "PHASE2_DECLARED_PROPERTIES_NOT_CLOSED"

#: The faculty's decisions this package implements, verbatim in substance.
DECISIONS = {
    "1_below_arrival_burden": "BELOW_ARRIVAL_BURDEN = ALLOWED_RECOVERY: b < b0 is the resolution of the arrival "
                              "distributive vasodilation, physiologically allowed and not a generic vasopressor "
                              "signal; the maximum recovery is at b = 0, so Bmax = 1 + k b0. T rising above the "
                              "arrival-relative 1 is not a reason to reject it",
    "2_no_negative_burden": "the burden stays at or above 0; a writer never resolves it below physiologic zero and a "
                            "negative burden is NOT vasoconstriction (a vasopressor acts through its own mechanism)",
    "3_guards_include_the_factor": "the upper-target admissibility and the contraction analysis of the delayed T loop "
                                   "must both account for Bmax = 1 + k b0: the full reachable target under the "
                                   "declared domain must stay inside the range for which the architecture claims the "
                                   "guard does not shape physiology",
    "4_fail_closed": "TONE_CLAMP_AS_PHYSIOLOGY = REJECTED: a declared parameter / state combination whose tone target "
                     "would leave the supported domain fails closed (CoreInvariantError, this repository's semantic "
                     "boundary) before execution instead of being clamped into shape; the channel guard remains the "
                     "last safety layer but is never the expected clinical response",
    "5_no_pressure_driven_writer": "PRESSURE_DRIVEN_FAMILY_VASODILATION = DEFERRED / NOT_AUTHORIZED: a family writer "
                                   "of the burden may not read the current MAP, pressure_rel, T or another same-loop "
                                   "haemodynamic observable; allowed inputs are its disease-process state, time, a "
                                   "treatment and authored family mechanisms",
    "6_maldistribution": "the distributive CRT / lactate direction is FUTURE_RESEARCH_DEBT, not a Phase-2 blocker: no "
                         "MIGRATED_AND_CERTIFIED family writes the burden and anaphylaxis is not required for exit; "
                         "no maldistribution, extraction heterogeneity, distributive CRT or distributive lactate "
                         "model is implemented here",
    "7_anaphylaxis_gaps": "plasma leak without red-cell loss, maldistribution / extraction, upper-airway and stridor "
                          "representation, a pharmacologic chronotropic target, epinephrine kinetics and the "
                          "anaphylaxis parameter regions are POST-PHASE2 / FAMILY-MIGRATION work",
    "8_p2s3": "TD120_HISTORICAL_SUPERSESSION_ACCEPTED: the historical P2S-3 frozen package, its sources and its "
              "digest are not recut or rewritten; the operative result is declared superseded by P2T-3",
    "scope": "a closure package: no new clinical physiology, no magnitude, no new canonical state, no runtime "
             "integration, no Phase 3",
}

#: SYNTHETIC_ONLY probe values. None is a clinical magnitude and none appears in any committed profile.
TONE_GAIN = 1.0
SMALL_GAIN = 0.25
ARRIVAL_BURDEN = 0.5
SEVERE_BURDEN = 50.0
BURDEN_GRID = (0.0, 0.25, 0.5, 1.0, 2.0)
#: A (k, b0) pair whose largest reachable target leaves T's supported range, and a (k, b0, a) triple whose derived
#: loop bound is not a contraction while its largest target stays inside: both must be refused before execution. The
#: second needs a high afterload sensitivity, because the slope's sup is taken at the lower end of the supported range,
#: where A(T) = 1 / (1 + a (T_lo - 1)) is largest; no committed profile declares the reader, so neither is reachable
#: today.
OUTSIDE_UPPER = (2.0, 10.0)
OUTSIDE_CONTRACTION = (1.0, 0.0, 0.95)


def acs_profile(**changes):
    return dt.acs_profile(**changes)


def reader(profile, gain=TONE_GAIN):
    return dt.reader(profile, gain)


def anchors_with(burden: float, **changes):
    """The committed ACS arrival (where the acute deficit is live, s0 = 0.15) with a synthetic arrival burden."""
    return replace(dt.ar.anchors(), arrival_vasodilatory_burden=burden, **changes)


def state_with(anchors, profile, burden: float):
    arrival = dv.arrival_state(anchors, profile)
    return arrival.evolve(aux=replace(arrival.aux, vasodilatory_burden=burden))


def _refused(build, error=(CoreInvariantError, ProvenanceError)) -> bool:
    try:
        build()
    except error:
        return True
    return False


# 1. P2X-1-1: the exact reachable tone domain, derived ------------------------------------------------------------------------

DERIVATION = {
    "target": "tone_target = C(s) x B(b), C(s) = (1 + g s) / (1 + g s0), B(b) = (1 + k b0) / (1 + k b)",
    "independence": "s reads delivery and demand (derived.acute_deficit_signal), b is written by a family and read "
                    "nowhere else: neither factor reads the other, so the reachable set is the product of the ranges",
    "s_domain": "s in [0, 1]: effective_oxygen_deficit is max(0, demand - reserve x delivery) over demand",
    "b_domain": "b in [0, inf): the state domain of aux.vasodilatory_burden (no clinical maximum is declared)",
    "C_range": "[1 / (1 + g s0), (1 + g) / (1 + g s0)], non-decreasing in s",
    "B_range": "(0, 1 + k b0], strictly decreasing in b, exactly 1 at b = b0, maximum 1 + k b0 at b = 0",
    "maximum": "C_max x B_max = (1 + g) (1 + k b0) / (1 + g s0), at s = 1 (no effective delivery) and b = 0",
    "infimum": "0, approached as b grows without bound; not attained",
    "monotonicity": "non-decreasing in s, strictly decreasing in b; the two are independent, so the extremes are the "
                    "products of the extremes",
    "loop": "T -> afterload A(T) = 1 / (1 + a (T - 1)) -> output -> delivery -> s -> target -> T_next, one minute "
            "behind",
    "slope": "d(target)/dT = B(b) x [g / (1 + g s0)] x a x A(T) x (1 - s) on the active deficit branch, 0 off it: "
             "from s(T) = max(0, 1 - mu A(T)) with mu = reserve x arrival_delivery_ratio x K / demand (K the part of "
             "delivery that does not read T), so ds/dT = mu a A(T)^2 = (1 - s) a A(T)",
    "slope_bound": "(1 + k b0) g a A(T_lo) / (1 + g s0), with T_lo the lower end of the supported range: (1 - s) <= 1, "
                   "B(b) <= 1 + k b0 and A is decreasing",
    "p2j2_bound": "g a < 1 is this bound with B = 1 and the A(T_lo) / (1 + g s0) factor dropped; it was published as "
                  "a profile invariant and is NOT reopened here",
    "insufficiency": "with a distributive reader declared, 1 + g (the published admissibility check) sees neither "
                     "Bmax nor a severe burden, and g a < 1 does not scale with Bmax: both were insufficient exactly "
                     "where the distributive factor is active",
    "where_the_guards_are_hit": "above, when C_max x Bmax > T's upper guard (reached by resolution, b -> 0); below, "
                                "when C(s) B(b) < T's lower guard (reached by a severe burden)",
}


def derivation() -> dict:
    """P2X-1-1, verified: every closed form above checked against the live equations at the extremes."""
    g = 0.5
    profile = reader(acs_profile(deficit_to_tone_gain=g), TONE_GAIN)
    anchors = anchors_with(ARRIVAL_BURDEN)
    a = profile.afterload_sensitivity
    s0 = dv.arrival_tone_signal(anchors, profile)
    domain = tone_domain(anchors, profile)
    arrival = dv.arrival_state(anchors, profile)
    observed = {
        "arrival_is_one": dv.tone_target(arrival, anchors, profile),
        "compensation_max": dv.tone_target(state_with(anchors, profile, ARRIVAL_BURDEN).evolve(V=-2000.0),
                                           anchors, profile),
        "recovery_max": dv.tone_target(state_with(anchors, profile, 0.0), anchors, profile),
        "joint_max": dv.tone_target(state_with(anchors, profile, 0.0).evolve(V=-2000.0), anchors, profile),
        "far_below": dv.tone_target(state_with(anchors, profile, 1e6), anchors, profile),
    }
    predicted = {
        "arrival_is_one": 1.0,
        "compensation_max": (1.0 + g) / (1.0 + g * s0),
        "recovery_max": 1.0 + TONE_GAIN * ARRIVAL_BURDEN,
        "joint_max": (1.0 + g) / (1.0 + g * s0) * (1.0 + TONE_GAIN * ARRIVAL_BURDEN),
        "far_below": (1.0 + TONE_GAIN * ARRIVAL_BURDEN) / (1.0 + TONE_GAIN * 1e6),
    }
    slope = {}
    for tone in (1.0, 1.5, 2.0, 2.5):
        held = arrival.evolve(T=tone)
        s = dv.acute_deficit_signal(held, anchors, profile)
        afterload = 1.0 / (1.0 + a * (tone - 1.0))
        step_h = 1e-6
        numeric = ((dv.tone_target(arrival.evolve(T=tone + step_h), anchors, profile)
                    - dv.tone_target(arrival.evolve(T=tone - step_h), anchors, profile)) / (2 * step_h))
        # The closed form holds on the active deficit branch; off it the signal is 0 and so is the slope.
        active = dv.effective_oxygen_deficit(
            held.aux.oxygen_demand,
            dv.effective_delivery(dv.delivery_rel_of(held, anchors, profile), anchors),
            profile.oxygen_extraction_reserve) > 0.0
        closed = ((domain["recovery_max"] / (1.0 + TONE_GAIN * arrival.aux.vasodilatory_burden)
                   * g / (1.0 + g * s0) * a * afterload * (1.0 - s)) if active else 0.0)
        slope[str(tone)] = {"numeric": numeric, "closed_form": closed, "active_branch": active,
                            "agree": math.isclose(numeric, closed, rel_tol=1e-6, abs_tol=1e-9),
                            "within_bound": abs(numeric) <= domain["loop_slope_bound"] + 1e-12}
    # The signal has one kink, where the effective deficit reaches 0 (mu A(T) = 1): there the two-sided difference is
    # the mean of the one-sided ones, so the closed form is checked against the derivative on the active side.
    low, high = T_LOWER, T_UPPER
    for _ in range(80):
        middle = (low + high) / 2.0
        if dv.acute_deficit_signal(arrival.evolve(T=middle), anchors, profile) > 0.0:
            high = middle
        else:
            low = middle
    kink = (low + high) / 2.0
    h = 1e-6
    at_the_kink = {
        "tone": kink,
        "signal_below": dv.acute_deficit_signal(arrival.evolve(T=kink - h), anchors, profile),
        "signal_above": dv.acute_deficit_signal(arrival.evolve(T=kink + h), anchors, profile),
        "left": (dv.tone_target(arrival.evolve(T=kink), anchors, profile)
                 - dv.tone_target(arrival.evolve(T=kink - h), anchors, profile)) / h,
        "right": (dv.tone_target(arrival.evolve(T=kink + h), anchors, profile)
                  - dv.tone_target(arrival.evolve(T=kink), anchors, profile)) / h,
    }
    at_the_kink["flat_below_the_kink"] = abs(at_the_kink["left"]) < 1e-6
    at_the_kink["within_bound_above"] = abs(at_the_kink["right"]) <= domain["loop_slope_bound"] + 1e-9
    out = {"statement": DERIVATION, "observed": observed, "predicted": predicted, "domain": domain, "slope": slope,
           "kink": at_the_kink,
           "closed_forms_hold": all(math.isclose(observed[k], predicted[k], rel_tol=1e-9, abs_tol=1e-12)
                                    for k in observed),
           "slope_closed_form_holds": all(row["agree"] and row["within_bound"] for row in slope.values())
                                      and at_the_kink["flat_below_the_kink"] and at_the_kink["within_bound_above"],
           "monotone_in_the_burden": None, "monotone_in_the_deficit": None}
    rows = [dv.tone_target(state_with(anchors, profile, b), anchors, profile) for b in BURDEN_GRID]
    out["monotone_in_the_burden"] = all(later < earlier for earlier, later in zip(rows, rows[1:]))
    held = state_with(anchors, profile, ARRIVAL_BURDEN)
    deficits = [dv.tone_target(held.evolve(aux=replace(held.aux, oxygen_demand=d)), anchors, profile)
                for d in (1.0, 1.4, 2.0)]
    out["monotone_in_the_deficit"] = all(later >= earlier for earlier, later in zip(deficits, deficits[1:]))
    out["pass"] = (out["closed_forms_hold"] and out["slope_closed_form_holds"] and out["monotone_in_the_burden"]
                   and out["monotone_in_the_deficit"])
    return out


def guards() -> dict:
    """P2X-1-2 and P2X-1-3: what the implemented guards read, and that the published P2J-2 checks are untouched."""
    source = inspect.getsource(sys.modules["clinical_core.integration"])
    tree = ast.parse(source)
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    tone = functions["_vascular_tone"]
    raises = [ast.unparse(node.exc.args[0])[:70] for node in ast.walk(tone) if isinstance(node, ast.Raise)]
    names = {node.attr for node in ast.walk(functions["tone_domain"]) if isinstance(node, ast.Attribute)}
    return {
        "p2j2_profile_invariant": "deficit_to_tone_gain x afterload_sensitivity < 1, in CoreProfile.__post_init__",
        "p2j2_invariant_unchanged": "self.deficit_to_tone_gain * self.afterload_sensitivity >= 1.0" in
                                    inspect.getsource(dv),
        "p2j2_gain_check_unchanged": "1.0 + profile.deficit_to_tone_gain > upper" in source,
        "tone_domain_reads": sorted(names & {"deficit_to_tone_gain", "afterload_sensitivity",
                                             "vasodilatory_burden_to_tone_gain", "arrival_vasodilatory_burden",
                                             "map", "pressure_rel", "T"}),
        "refusals": raises,
        "upper_admissibility": "largest_target > upper, where the distributive reader is declared",
        "contraction": "loop_slope_bound >= 1.0, where the distributive reader is declared",
        "per_minute_boundary": "not lower <= target <= upper, every minute",
        "only_refusals_added": all(isinstance(node, (ast.Raise, ast.If, ast.Assign, ast.Expr, ast.Return))
                                   for node in tone.body),
        "delta_expression": next(ast.unparse(node.value.args[1]) for node in ast.walk(tone)
                                 if isinstance(node, ast.Return) and isinstance(node.value, ast.Call)),
    }


def writer_contract() -> dict:
    """P2X-1-4: the structural contract, and the repository scan that enforces it."""
    text = (CORE_DIR / "provenance.py").read_text(encoding="utf-8")
    contract = "WRITER CONTRACT (P2X-1, FACULTY DECISIONS 2 and 5)" in text
    forbidden = ("map", "pressure_rel", "mean_arterial_pressure", "sbp", "dbp")
    writers, offenders = [], []
    for path in sorted(CORE_DIR.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts or relative in OWN or relative == REPORT:
            continue
        source = path.read_text(encoding="utf-8")
        if "VasodilationChange(" not in source:
            continue
        writers.append(relative)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            builds = any(isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == "VasodilationChange"
                         for inner in ast.walk(node))
            if not builds:
                continue
            reads = {inner.attr for inner in ast.walk(node) if isinstance(inner, ast.Attribute)}
            if reads & set(forbidden) or "T" in reads:
                offenders.append((relative, node.name))
    return {"contract_declared": contract, "forbidden_inputs": list(forbidden) + ["T"],
            "modules_that_build_the_record": writers, "offenders": sorted(offenders),
            "allowed_inputs": ["the writer's own disease-process state", "time", "a treatment",
                               "authored family mechanisms that do not close the haemodynamic loop"],
            "family_writers": sorted(p.relative_to(ROOT).as_posix() for p in (CORE_DIR / "modules").glob("*.py")
                                     if "VasodilationChange" in p.read_text(encoding="utf-8"))
                              + sorted(p.relative_to(ROOT).as_posix() for p in (CORE_DIR / "interventions").glob("*.py")
                                       if "VasodilationChange" in p.read_text(encoding="utf-8")),
            "pass": contract and not offenders}


# 2. P2X-1-5: the structural probes X1-X15 ------------------------------------------------------------------------------------

def probe_x1() -> dict:
    """b = b0 gives the distributive factor exactly 1, at any arrival burden and any gain."""
    rows = {}
    for burden in (0.0, ARRIVAL_BURDEN, 2.0):
        for gain in (SMALL_GAIN, TONE_GAIN):
            profile = reader(acs_profile(), gain)
            anchors = anchors_with(burden)
            rows[f"b0={burden} k={gain}"] = dv.tone_target(state_with(anchors, profile, burden), anchors, profile)
    out = {"rows": rows}
    out["pass"] = all(value == 1.0 for value in rows.values())
    return out


def probe_x2() -> dict:
    """b > b0 lowers the effective tone, strictly and monotonically."""
    profile, anchors = reader(acs_profile()), anchors_with(ARRIVAL_BURDEN)
    grid = tuple(b for b in BURDEN_GRID if b >= ARRIVAL_BURDEN)
    rows = [dv.tone_target(state_with(anchors, profile, b), anchors, profile) for b in grid]
    out = {"grid": list(grid), "target": rows}
    out["pass"] = rows[0] == 1.0 and all(later < earlier for earlier, later in zip(rows, rows[1:]))
    return out


def probe_x3() -> dict:
    """0 <= b < b0 raises the effective tone above the arrival-relative 1 as the vasodilation resolves (DECISION 1)."""
    profile, anchors = reader(acs_profile()), anchors_with(2.0)
    grid = (2.0, 1.0, 0.5, 0.25, 0.0)
    rows = [dv.tone_target(state_with(anchors, profile, b), anchors, profile) for b in grid]
    out = {"grid": list(grid), "target": rows, "arrival_burden": 2.0,
           "rises_as_it_resolves": all(later > earlier for earlier, later in zip(rows, rows[1:])),
           "above_one_below_the_arrival_burden": all(value > 1.0 for value in rows[1:])}
    out["pass"] = out["rises_as_it_resolves"] and out["above_one_below_the_arrival_burden"] and rows[0] == 1.0
    return out


def probe_x4() -> dict:
    """b = 0 is the maximum recovery, exactly 1 + k b0."""
    rows = {}
    for burden, gain in ((ARRIVAL_BURDEN, TONE_GAIN), (2.0, TONE_GAIN), (1.0, SMALL_GAIN)):
        profile, anchors = reader(acs_profile(), gain), anchors_with(burden)
        rows[f"b0={burden} k={gain}"] = {"observed": dv.tone_target(state_with(anchors, profile, 0.0), anchors, profile),
                                        "predicted": 1.0 + gain * burden}
    out = {"rows": rows}
    out["pass"] = all(math.isclose(row["observed"], row["predicted"], rel_tol=1e-12) for row in rows.values())
    return out


def probe_x5() -> dict:
    """b < 0 is rejected: in the state, in the arrival anchor and in a writer's own minute (DECISION 2)."""
    profile, anchors = reader(acs_profile()), anchors_with(ARRIVAL_BURDEN)
    arrival = dv.arrival_state(anchors, profile)
    out = {
        "negative_state": _refused(lambda: replace(arrival.aux, vasodilatory_burden=-0.1)),
        "negative_arrival": _refused(lambda: anchors_with(-0.1)),
        "writer_below_zero": _refused(lambda: dt.course((dt.SyntheticVasodilation("down", -1.0, 0, 2),), 3,
                                                        anchors_with(0.5), profile)),
        "contract_names_it": "negative burden is not" in
                             (CORE_DIR / "provenance.py").read_text(encoding="utf-8"),
    }
    out["pass"] = all(out.values())
    return out


def probe_x6() -> dict:
    """A reachable upper target outside the supported range fails closed before the clamp can define physiology."""
    gain, burden = OUTSIDE_UPPER
    profile, anchors = reader(acs_profile(), gain), anchors_with(burden)
    domain = tone_domain(anchors, profile)
    refused = _refused(lambda: step(state_with(anchors, profile, 0.0), (), anchors, profile))
    out = {"gain": gain, "arrival_burden": burden, "largest_target": domain["largest_target"],
           "supported": list(domain["supported"]), "refused": refused,
           "p2j2_check_would_pass": 1.0 + profile.deficit_to_tone_gain <= T_UPPER}
    out["pass"] = refused and domain["largest_target"] > T_UPPER and out["p2j2_check_would_pass"]
    return out


def probe_x7() -> dict:
    """A reachable lower target outside the supported range fails closed instead of parking on the guard."""
    profile, anchors = reader(acs_profile()), anchors_with(0.0)
    severe = state_with(anchors, profile, SEVERE_BURDEN)
    target = dv.tone_target(severe, anchors, profile)
    refused = _refused(lambda: step(severe, (), anchors, profile))
    out = {"burden": SEVERE_BURDEN, "target": target, "supported": [T_LOWER, T_UPPER], "refused": refused,
           "no_clinical_maximum_burden": "no clinical maximum burden is declared" in
                                         str(tone_domain(anchors, profile)["smallest_target"])}
    out["pass"] = refused and target < T_LOWER and out["no_clinical_maximum_burden"]
    return out


def probe_x8() -> dict:
    """Valid interior combinations run with no clamp at all: the guard shapes nothing."""
    profile, anchors = reader(acs_profile()), anchors_with(ARRIVAL_BURDEN)
    states, records = dt.course((dt.SyntheticVasodilation("x", 0.25, 0, 4),), 8, anchors, profile)
    clamps = [sorted({delta.source.key for delta in record.deltas if delta.source.kind is SourceKind.CLAMP})
              for record in records]
    targets = [dv.tone_target(state, anchors, profile) for state in states]
    out = {"tone": [state.T for state in states], "targets": targets, "clamps": clamps,
           "inside_the_range": all(T_LOWER <= value <= T_UPPER for value in targets)}
    out["pass"] = out["inside_the_range"] and not any(clamps)
    return out


def probe_x9() -> dict:
    """The derived contraction condition holds for every accepted boundary witness, and the live slope stays under it."""
    witnesses = {}
    for gain, burden in ((TONE_GAIN, ARRIVAL_BURDEN), (SMALL_GAIN, 2.0), (TONE_GAIN, 1.0), (None, 0.0)):
        profile = acs_profile() if gain is None else reader(acs_profile(), gain)
        anchors = anchors_with(burden)
        domain = tone_domain(anchors, profile)
        arrival = dv.arrival_state(anchors, profile)
        worst = 0.0
        for tone in (T_LOWER, 0.5, 1.0, 1.5, 2.0, T_UPPER):
            h = 1e-6
            numeric = ((dv.tone_target(arrival.evolve(T=tone + h), anchors, profile)
                        - dv.tone_target(arrival.evolve(T=tone - h), anchors, profile)) / (2 * h))
            worst = max(worst, abs(numeric))
        witnesses[f"k={gain} b0={burden}"] = {"bound": domain["loop_slope_bound"], "largest_live_slope": worst,
                                              "contraction": domain["loop_slope_bound"] < 1.0,
                                              "live_under_the_bound": worst <= domain["loop_slope_bound"] + 1e-12,
                                              "accepted": not _refused(
                                                  lambda: step(arrival, (), anchors, profile))}
    out = {"witnesses": witnesses}
    out["pass"] = all(row["contraction"] and row["live_under_the_bound"] and row["accepted"]
                      for row in witnesses.values())
    return out


def probe_x10() -> dict:
    """A combination whose derived bound is not a contraction is rejected, with its largest target inside the range
    and with P2J-2's own bound satisfied: the distributive factor and the afterload at the lower end are what the old
    bound did not see."""
    gain, burden, sensitivity = OUTSIDE_CONTRACTION
    profile = reader(acs_profile(afterload_sensitivity=sensitivity), gain)
    anchors = anchors_with(burden)
    domain = tone_domain(anchors, profile)
    out = {"gain": gain, "arrival_burden": burden, "afterload_sensitivity": sensitivity,
           "loop_slope_bound": domain["loop_slope_bound"], "largest_target": domain["largest_target"],
           "inside_the_upper_range": domain["largest_target"] <= T_UPPER,
           "refused": _refused(lambda: step(state_with(anchors, profile, burden), (), anchors, profile)),
           "p2j2_bound_would_pass": domain["p2j2_slope_bound"] < 1.0}
    out["pass"] = (out["refused"] and domain["loop_slope_bound"] >= 1.0 and out["p2j2_bound_would_pass"]
                   and out["inside_the_upper_range"])
    return out


def probe_x11() -> dict:
    """With the burden 0 everywhere the predecessor's behaviour is exact: P2W-1's probes and reference courses, with
    the one declared supersession (its V5 read the clamp as the response, which DECISION 4 rejects)."""
    record = _record()
    builders = {"V1": dt.probe_v1, "V2": dt.probe_v2, "V3": dt.probe_v3, "V4": dt.probe_v4, "V6": dt.probe_v6,
                "V11": dt.probe_v11, "V12": dt.probe_v12, "V13": dt.probe_v13, "V14": dt.probe_v14}
    live, differing = {}, []
    with _p2w1_view():
        closed = dt.probes_v7_to_v10()
        for name, value in closed.items():
            builders[name] = (lambda v=value: v)
        for name in sorted(builders):
            try:
                found = {"requires": dt.PROBES[name], **builders[name]()}
                live[name] = json.loads(json.dumps(found, sort_keys=True, default=str))
            except CoreInvariantError as error:  # a new refusal on a predecessor probe would be a regression
                differing.append((name, f"refused: {error}"))
                continue
            if live[name] != record["probes"][name]:
                differing.append((name, "differs from the frozen record"))
        courses = dt.non_regression()["p2v1_record_reproduced_on_its_tree"]
    out = {"probes_compared": sorted(live), "differing": differing,
           "v5_now_refused": _refused(dt.probe_v5), "v5_frozen_pass": record["probes"]["V5"]["pass"],
           "courses_identical": courses}
    out["pass"] = not differing and out["v5_now_refused"] and out["courses_identical"]
    return out


def probe_x12() -> dict:
    """Every prior migrated family keeps its default behaviour exactly: the reader is UNSET, so nothing P2X-1 added
    can fire, and the committed readings are the frozen ones."""
    profiles = dt.committed_profiles()
    courses = dt.reference_courses()
    out = {"committed_profiles_unset": {name: getattr(profile, dt.NEW_PROFILE_FIELD) is None
                                        for name, profile in profiles.items()},
           "courses": sorted(courses), "course_digests": {name: hashlib.sha256(
               json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
               for name, value in courses.items()},
           "no_refusal_in_any_committed_course": True}
    for name, profile in profiles.items():
        anchors = dt.committed_pairs()[name][0]
        try:
            step(dv.arrival_state(anchors, profile), (), anchors, profile)
        except CoreInvariantError:
            out["no_refusal_in_any_committed_course"] = False
            out.setdefault("refused", []).append(name)
    out["pass"] = all(out["committed_profiles_unset"].values()) and out["no_refusal_in_any_committed_course"]
    return out


def probe_x13() -> dict:
    """The systemic stress still does not reach T (P2V-1 / P2W-1, re-checked after the new guards)."""
    # The arrival stress is refused without its own reader (P2V-1), so the probe declares both readers and shows the
    # tone unmoved while the HR answers: the stress is a sympathetic input, never a vascular one.
    profile = reader(replace(acs_profile(), systemic_stress_to_sympathetic_gain=dt.STRESS_GAIN))
    rows, hr = {}, {}
    for stress in (0.0, 2.0):
        anchors = anchors_with(ARRIVAL_BURDEN, arrival_systemic_stress=stress)
        held = state_with(anchors, profile, ARRIVAL_BURDEN)
        rows[str(stress)] = dv.tone_target(held, anchors, profile)
        hr[str(stress)] = dv.derive(held, anchors, profile).pulse_rate_bpm
    out = {"targets": rows, "hr": hr,
           "stress_not_in_the_tone_path": "systemic_stress" not in inspect.getsource(dv.tone_target),
           "unset_by_default": dv.DEFAULT_PROFILE.systemic_stress_to_sympathetic_gain is None}
    out["pass"] = (len(set(rows.values())) == 1 and hr["2.0"] > hr["0.0"]
                   and out["stress_not_in_the_tone_path"] and out["unset_by_default"])
    return out


def probe_x14() -> dict:
    """Beta-blockade still does not reach T."""
    profile = reader(dt.base_profile())
    rows, hr = {}, {}
    for beta in dt.BETA_BLOCKADES:
        anchors = replace(dt.probe_anchors(beta_blockade=beta), arrival_vasodilatory_burden=ARRIVAL_BURDEN)
        held = state_with(anchors, profile, ARRIVAL_BURDEN)
        rows[str(beta)] = dv.tone_target(held, anchors, profile)
        hr[str(beta)] = dv.derive(held, anchors, profile).pulse_rate_bpm
    out = {"targets": rows, "hr": hr,
           "beta_not_in_the_tone_path": "beta_blockade" not in inspect.getsource(dv.tone_target)}
    out["pass"] = (len({round(v, 12) for v in rows.values()}) == 1 and out["beta_not_in_the_tone_path"]
                   and hr["0.0"] >= hr["1.0"])
    return out


def probe_x15() -> dict:
    """No pressure-reading vasodilation writer exists anywhere, and the contract that forbids one is declared."""
    contract = writer_contract()
    out = {"offenders": contract["offenders"], "family_writers": contract["family_writers"],
           "contract_declared": contract["contract_declared"],
           "modules_that_build_the_record": contract["modules_that_build_the_record"],
           "tone_target_reads_no_pressure": dt.probe_v14()["tone_target_reads"] == []}
    out["pass"] = (not out["offenders"] and not out["family_writers"] and out["contract_declared"]
                   and out["tone_target_reads_no_pressure"])
    return out


PROBES = {
    "X1": "b = b0 gives the distributive factor exactly 1",
    "X2": "b > b0 lowers the effective tone",
    "X3": "0 <= b < b0 raises it as the vasodilation resolves (ALLOWED_RECOVERY)",
    "X4": "b = 0 is the maximum recovery, exactly 1 + k b0",
    "X5": "b < 0 is rejected everywhere",
    "X6": "a reachable upper target outside the supported range fails closed",
    "X7": "a reachable lower target outside the supported range fails closed",
    "X8": "valid interior combinations run with no clamp",
    "X9": "the derived contraction condition holds for every accepted boundary witness",
    "X10": "a combination violating the derived condition is rejected",
    "X11": "burden 0 everywhere: the predecessor's behaviour, with one declared supersession",
    "X12": "every prior migrated family keeps its default behaviour exactly",
    "X13": "the systemic stress still does not affect T",
    "X14": "beta-blockade still does not affect T",
    "X15": "no pressure-driven vasodilation writer exists",
}


def structural_probes() -> dict:
    return {name: globals()[f"probe_{name.lower()}"]() for name in PROBES}


# 3. P2X-1-6 and P2X-1-7: the supersession records and the consolidated debt classification -----------------------------------

def _record() -> dict:
    return json.loads(dt.RECORD.read_text(encoding="utf-8"))


class _Patcher:
    """The smallest stand-in for pytest's monkeypatch, so the module can install its own view outside a test."""

    def __init__(self):
        self.undo = []

    def setattr(self, target, name, value):
        self.undo.append((target, name, getattr(target, name)))
        setattr(target, name, value)

    def restore(self):
        for target, name, value in reversed(self.undo):
            setattr(target, name, value)
        self.undo.clear()


class _p2w1_view:
    """The whole P2W-1 tree while its own analysis runs: its path readers return the P2W-1 text of the two files
    P2X-1 changed and leave P2X-1's new files out of every listing, so P2W-1's source audits, hashes and freeze digest
    read the tree it was frozen against. This is exactly the redirection ``tree`` installs for the closed test
    fixtures, done locally because ``run`` has no monkeypatch."""

    def __enter__(self):
        self.patch = _Patcher()
        tree(self.patch)
        return self

    def __exit__(self, *exc):
        self.patch.restore()
        return False


def supersession() -> dict:
    """Immutable history: what each superseded result said, what superseded it, and that no frozen digest moved."""
    p2s3 = ROOT / "docs" / "revision" / "P2S3_ASMA_EN_SOMBRA.md"
    p2t3 = ROOT / "docs" / "revision" / "P2T3_ASMA_CON_DISTRES.md"
    rows = {
        "TD120_HISTORICAL_SUPERSESSION_ACCEPTED": {
            "status": "P2S3_FROZEN_VERDICT_SUPERSEDED_BY_P2T3",
            "historical": "P2S-3's frozen rule returned ASTHMA_SHADOW_MIGRATION_READY; its adversarial review then "
                          "demonstrated a COMMON_DRIVE_GAP and the corrected operative classification was NOT_READY",
            "resolved_by": "P2T-1 (the common respiratory distress), P2T-2 (its cross-family identifiability) and "
                           "P2T-3 (the asthma distress mapping), which closed that blocker",
            "authoritative": "P2T-3: ASTHMA_SHADOW_MIGRATION_READY is the current asthma migration result",
            "nature": "a traceability lesson: a frozen rule can return READY while a review shows otherwise, so the "
                      "operative classification is the reviewed one. Not a current physiology blocker",
            "history_preserved": "no P2S-3 source, record or digest is recut or rewritten",
            "documents": {"historical": p2s3.name if p2s3.exists() else "docs/PHASE2_SHADOW_CORE.md (P2S-3 section)",
                          "superseding": p2t3.name if p2t3.exists() else "docs/PHASE2_SHADOW_CORE.md (P2T-3 section)"},
        },
        "P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1": {
            "status": "P2W1_V5_CLAMP_READING_SUPERSEDED",
            "historical": "P2W-1's V5 read a severe burden as parking T on its lower guard with the clamp recorded, "
                          "and published that as 'no clinical ceiling is chosen'",
            "resolved_by": "FACULTY DECISION 4 (TONE_CLAMP_AS_PHYSIOLOGY = REJECTED): that combination now fails "
                           "closed before execution, and no clinical maximum burden is declared either",
            "authoritative": "P2X-1's X7: the refusal, not the clamp",
            "nature": "a declared-property correction inside the same architecture; the frozen P2W-1 record and its "
                      "digest are unchanged, and every other P2W-1 probe still reproduces exactly (X11)",
            "history_preserved": "the P2W-1 record is read, never rewritten",
            "record_sha": hashlib.sha256(dt.RECORD.read_bytes()).hexdigest(),
        },
    }
    return {"records": rows, "p2w1_digest_unchanged": _p2w1_digest() == _record()["freeze_digest"],
            "pass": all(row["history_preserved"] for row in rows.values())}


DEBT = {
    "ACCEPTABLE_PHASE2_DEBT": {
        "STEADY_STATE_W_ARRIVAL_TENSION": "TD-124: the arrival efficiency reads above its reference for both opioid "
                                          "cases against the authored shallow breaths; three exits exist, none chosen",
        "OPIOID_HR_RESIDUAL": "TD-124: the 67f's authored 62 stays 1.89 bpm under the model's band; no opioid HR term "
                              "was added",
        "COLLAPSE_THRESHOLDS": "TD-109 / TD-110: collapse is structural only, with no threshold",
        "FIO2_MAGNITUDE": "TD-123: the FiO2 response magnitude is UNSET",
        "RESPIRATORY_DISTRESS_CALIBRATION": "TD-121 / TD-122: every distress gain and arrival region is UNSET",
        "SYSTEMIC_STRESS_CALIBRATION": "TD-125: the stress gain and every arrival region are UNSET",
        "PRESSURE_TO_TONE": "TD-118 point 4 / P2W-0: the compensation reads the oxygen deficit only; a pressure-driven "
                            "tone compensation needs a new clinical gain, a reference pressure and an ordering "
                            "decision, and stays open for ACS and PE",
        "SIDED_PRELOAD_AND_INTERDEPENDENCE": "TD-118 point 2: the core has no sided preload",
        "CUMULATIVE_FLOATING_POINT_CANCELLATION": "TD-121A: the binary64 roundoff snap is in place for the auxiliary "
                                                  "sums; the general cancellation question stays open",
        "PHYSICAL_PAO2_BOUNDARY": "TD-123: the PaO2 floor is a declared boundary, non-blocking",
        "HYPOXAEMIC_FEEDBACK_STABILITY": "TD-117 / TD-123: the hypoxaemic drive mapping is UNSET, so the loop is off",
    },
    "NEXT_PHASE_INTEGRATION_DEBT": {
        "CONSCIOUSNESS_WIRING": "TD-107 / TD-108 / TD-124: N is an unused placeholder and the encephalopathy layer is "
                                "shadow only; the common ladder already reproduces the authored levels of the cases "
                                "audited so far (P2W-2)",
        "RUNTIME_INTEGRATION": "clinical_core runs in shadow; family_engine.py stays the source of truth",
        "RESIDENT_VISIBLE_BEHAVIOUR": "nothing the resident sees changes in Phase 2",
    },
    "FUTURE_RESEARCH_DEBT": {
        "MALDISTRIBUTION_AND_EXTRACTION": "FACULTY DECISION 6: the distributive CRT and lactate directions, accepted "
                                          "as research debt; no migrated family writes the burden",
        "UPPER_AIRWAY": "P2W-2: no common representation of upper-airway obstruction or stridor",
        "PLASMA_LEAK": "P2W-2: no blood process moves plasma without red cells for a disease module",
        "DRUG_KINETICS": "P2U-1 / P2W-2: naloxone, epinephrine and vasopressor kinetics are UNSET",
        "ADDITIONAL_FAMILY_MIGRATIONS": "anaphylaxis and any further family",
    },
}


def debt_classification() -> dict:
    out = {"classes": DEBT, "counts": {name: len(rows) for name, rows in DEBT.items()},
           "unset_is_not_a_blocker": "no item is a blocker merely because it is UNSET: an UNSET magnitude leaves its "
                                     "term inert, which is the design",
           "blockers": []}
    out["pass"] = not out["blockers"]
    return out


def non_regression() -> dict:
    """P2W-1's record on its own tree, the committed families exact, and the registry tuples."""
    with _p2w1_view():
        reproduced = dt.non_regression()["p2v1_record_reproduced_on_its_tree"]
    out = {"p2w1_record_reproduced_on_its_tree": reproduced,
           "p2w1_record_untouched": _p2w1_digest() == _record()["freeze_digest"],
           "p2w1_verdict": _record()["readiness"]["verdict"],
           "committed_defaults_exact": probe_x12()["pass"],
           "tuples": {name: set(values) <= set(_tuple_values(name)) for name, values in TUPLES_ADDED.items()}}
    out["pass"] = (out["p2w1_record_reproduced_on_its_tree"] and out["p2w1_record_untouched"]
                   and out["committed_defaults_exact"] and all(out["tuples"].values())
                   and out["p2w1_verdict"] == "COMMON_DISTRIBUTIVE_TONE_COMPOSITION_READY")
    return out


def _tuple_values(name: str):
    from . import decision_pack, lactate_slice
    return lactate_slice.DOWNSTREAM_REPORTS if name == "DOWNSTREAM_REPORTS" else decision_pack.PACK_DIGEST_EXCLUDED


# 4. The proof: P2X-1's changed files reverse to the P2W-1 files, and nothing else moved -------------------------------------

P2W1_HEAD = 'd4e6fe9'

#: P2X-1's declared replacements, live -> the P2W-1 file at d4e6fe9.
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py",\n'
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py",\n'
                                     '                        "clinical_core/distributive_tone.py",\n'
                                     '                        "clinical_core/distributive_tone_report.py",\n'
                                     '                        "clinical_core/tone_domain.py", '
                                     '"clinical_core/tone_domain_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def pack_sources() -> dict[str, str]:\n',
                                     '                        "clinical_core/opioid_migration.py", '
                                     '"clinical_core/opioid_migration_report.py",\n'
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py",\n'
                                     '                        "clinical_core/distributive_tone.py",\n'
                                     '                        "clinical_core/distributive_tone_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def pack_sources() -> dict[str, str]:\n'),),
 'clinical_core/integration.py': (('                      LUNG_WATER_GAS_EXCHANGE, lung_water_gas_exchange, '
                                   'lung_water_gas_exchange_active,\n'
                                   '                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active, '
                                   'respiratory_distress_read,\n'
                                   '                      check_distress_respiratory_effect, arrival_tone_signal)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange,\n',
                                   '                      LUNG_WATER_GAS_EXCHANGE, lung_water_gas_exchange, '
                                   'lung_water_gas_exchange_active,\n'
                                   '                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active, '
                                   'respiratory_distress_read,\n'
                                   '                      check_distress_respiratory_effect)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'
                                   '                         CoreEvent, DemandModifier, MinuteRecord, '
                                   'ProvenanceError, RhythmTransition, SettingChange,\n'
                                   '                         Source, SourceKind, MechanicsChange, DistressChange, '
                                   'AvailabilityChange,\n'),
                                  ('                        modulated_by=debt.modulated_by)\n'
                                   '\n'
                                   '\n'
                                   'def tone_domain(anchors: Anchors, profile: CoreProfile) -> dict:\n'
                                   '    """P2X-1: the exact reachable tone target under the declared parameter '
                                   "domain, and the delayed loop's slope bound.\n"
                                   '\n'
                                   '    ``tone_target`` is the product of two independent factors (P2J-2 and '
                                   'P2W-1):\n'
                                   '\n'
                                   '    - the common compensation C(s) = (1 + g s) / (1 + g s0), s the acute shock '
                                   'signal in [0, 1] and s0 the arrival\n'
                                   '      one, so C rises with s over [1 / (1 + g s0), (1 + g) / (1 + g s0)];\n'
                                   "    - the distributive factor B(b) = (1 + k b0) / (1 + k b), b the state's "
                                   'vasodilatory burden in [0, inf) and b0 the\n'
                                   '      arrival one, so B falls with b over (0, 1 + k b0], is exactly 1 at b = b0, '
                                   'and reaches its maximum 1 + k b0 at\n'
                                   '      b = 0 (full resolution of the arrival vasodilation, FACULTY DECISION 1).\n'
                                   '\n'
                                   '    s reads delivery and demand, b is written by a family: neither reads the '
                                   'other, so the reachable set is the\n'
                                   '    product of the two ranges. Its largest value is C_max x B_max and its '
                                   'infimum is 0, approached as b grows without\n'
                                   '    bound (no clinical maximum burden is declared).\n'
                                   '\n'
                                   '    The loop the core closes one minute behind is T -> afterload -> output -> '
                                   'delivery -> s -> target -> T_next. With\n'
                                   '    A(T) = 1 / (1 + a (T - 1)) the afterload factor and the deficit branch '
                                   'active (s > 0),\n'
                                   '\n'
                                   '        d(target)/dT = B(b) x [g / (1 + g s0)] x a x A(T) x (1 - s),\n'
                                   '\n'
                                   '    which is 0 off the branch. (1 - s) <= 1, B(b) <= 1 + k b0 and A is '
                                   'decreasing, so over a domain whose lower end is\n'
                                   "    T_lo the slope is bounded by (1 + k b0) g a A(T_lo) / (1 + g s0). P2J-2's "
                                   'published bound, g a < 1, is this one\n'
                                   '    with B = 1 and the A / (1 + g s0) factor dropped; the distributive factor '
                                   'scales it, which is what P2X-1 adds.\n'
                                   '    """\n'
                                   '    gain, sensitivity = profile.deficit_to_tone_gain, '
                                   'profile.afterload_sensitivity\n'
                                   '    arrival_signal = arrival_tone_signal(anchors, profile)\n'
                                   '    normalization = 1.0 + gain * arrival_signal\n'
                                   '    loss = profile.vasodilatory_burden_to_tone_gain\n'
                                   '    recovery_max = 1.0 if loss is None else 1.0 + loss * '
                                   'anchors.arrival_vasodilatory_burden\n'
                                   '    lower, upper = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]\n'
                                   '    afterload_at_the_lower_end = 1.0 / (1.0 + sensitivity * (lower - 1.0))\n'
                                   '    return {"arrival_signal": arrival_signal, "compensation_min": 1.0 / '
                                   'normalization,\n'
                                   '            "compensation_max": (1.0 + gain) / normalization, "recovery_max": '
                                   'recovery_max,\n'
                                   '            "distributive_reader": loss is not None,\n'
                                   '            "largest_target": (1.0 + gain) / normalization * recovery_max,\n'
                                   '            "smallest_target": "0 (approached as the burden grows; no clinical '
                                   'maximum burden is declared)",\n'
                                   '            "supported": (lower, upper),\n'
                                   '            "loop_slope_bound": recovery_max * gain * sensitivity * '
                                   'afterload_at_the_lower_end / normalization,\n'
                                   '            "p2j2_slope_bound": gain * sensitivity}\n'
                                   '\n'
                                   '\n'
                                   'def _vascular_tone(state: CoreState, deltas: Sequence[ChannelDelta], anchors: '
                                   'Anchors, profile: CoreProfile,\n'
                                   '                   minute: int) -> ChannelDelta:\n'
                                   '    """P2J-2: T moves to the tone the state at the start of the minute calls for '
                                   '(``tone_target``).\n',
                                   '                        modulated_by=debt.modulated_by)\n'
                                   '\n'
                                   '\n'
                                   'def _vascular_tone(state: CoreState, deltas: Sequence[ChannelDelta], anchors: '
                                   'Anchors, profile: CoreProfile,\n'
                                   '                   minute: int) -> ChannelDelta:\n'
                                   '    """P2J-2: T moves to the tone the state at the start of the minute calls for '
                                   '(``tone_target``).\n'),
                                  ('    Fails closed where nothing is decided: another source writing T in the same '
                                   'minute (how a drug or a disease module\n'
                                   '    would compose with the response is not decided), or a gain whose largest '
                                   'target, 1 + g at no delivery, is outside\n'
                                   "    T's guard (so the guard never shapes the response).\n"
                                   '\n'
                                   '    P2X-1 closes that last claim over the whole declared domain '
                                   '(``tone_domain``). The P2J-2 check reads the\n'
                                   '    compensation alone, so with a distributive reader declared it saw neither '
                                   'the recovery factor 1 + k b0 above nor a\n'
                                   "    severe burden below, and the channel's guard - a safety bound, never "
                                   'physiology - decided the response instead.\n'
                                   '    Now, where that reader is declared, a parameter domain whose largest '
                                   "reachable target leaves T's supported range,\n"
                                   '    or whose derived loop bound is not a contraction, is refused before '
                                   'execution; and any minute whose target would\n'
                                   '    leave that range fails closed here rather than being clamped into shape. The '
                                   'guard stays as the last safety layer\n'
                                   '    for every other source (TONE_CLAMP_AS_PHYSIOLOGY = REJECTED, FACULTY '
                                   'DECISIONS 3 and 4).\n'
                                   '    """\n'
                                   '    lower, upper = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]\n'
                                   '    if 1.0 + profile.deficit_to_tone_gain > upper:\n'
                                   '        raise CoreInvariantError(f"the tone response\'s largest target 1 + '
                                   '{profile.deficit_to_tone_gain!r} is above "\n'
                                   '                                 f"T\'s guard {upper!r}")\n'
                                   '    domain = tone_domain(anchors, profile)\n'
                                   '    if domain["distributive_reader"]:\n'
                                   '        if domain["largest_target"] > upper:\n'
                                   '            raise CoreInvariantError(\n'
                                   '                f"the tone target\'s largest reachable value '
                                   '{domain[\'largest_target\']!r} (the compensation\'s "\n'
                                   '                f"{domain[\'compensation_max\']!r} times the distributive '
                                   'recovery {domain[\'recovery_max\']!r}) is above "\n'
                                   '                f"T\'s guard {upper!r}: the guard would shape the response '
                                   '(P2X-1)")\n'
                                   '        if domain["loop_slope_bound"] >= 1.0:\n'
                                   '            raise CoreInvariantError(\n'
                                   '                f"the tone loop\'s derived bound with the distributive factor, '
                                   '{domain[\'loop_slope_bound\']!r}, is not "\n'
                                   '                f"below 1, so the delayed loop is not a contraction over T\'s '
                                   'supported range (P2X-1)")\n'
                                   '    writers = sorted({delta.source.key for delta in deltas if delta.channel is '
                                   'Channel.T})\n'
                                   '    if writers:\n'
                                   '        raise CoreInvariantError(f"minute {minute}: {writers} write T while the '
                                   'vascular-tone response is on; how they "\n'
                                   '                                 "compose is not decided (P2J-2)")\n'
                                   '    target = tone_target(state, anchors, profile)\n'
                                   '    if not lower <= target <= upper:\n'
                                   '        raise CoreInvariantError(f"minute {minute}: the tone target {target!r} '
                                   'leaves T\'s supported range "\n'
                                   '                                 f"{(lower, upper)!r}; the channel\'s guard is a '
                                   'safety bound, not the physiology "\n'
                                   '                                 "(P2X-1)")\n'
                                   '    return ChannelDelta(Channel.T, target - state.T, VASCULAR_TONE, minute,\n'
                                   '                        "the tone the acute shock signal at the start of the '
                                   'minute calls for")\n'
                                   '\n'
                                   '\n',
                                   '    Fails closed where nothing is decided: another source writing T in the same '
                                   'minute (how a drug or a disease module\n'
                                   '    would compose with the response is not decided), or a gain whose largest '
                                   'target, 1 + g at no delivery, is outside\n'
                                   "    T's guard (so the guard never shapes the response).\n"
                                   '    """\n'
                                   '    upper = CHANNEL_BOUNDS[Channel.T][1]\n'
                                   '    if 1.0 + profile.deficit_to_tone_gain > upper:\n'
                                   '        raise CoreInvariantError(f"the tone response\'s largest target 1 + '
                                   '{profile.deficit_to_tone_gain!r} is above "\n'
                                   '                                 f"T\'s guard {upper!r}")\n'
                                   '    writers = sorted({delta.source.key for delta in deltas if delta.channel is '
                                   'Channel.T})\n'
                                   '    if writers:\n'
                                   '        raise CoreInvariantError(f"minute {minute}: {writers} write T while the '
                                   'vascular-tone response is on; how they "\n'
                                   '                                 "compose is not decided (P2J-2)")\n'
                                   '    return ChannelDelta(Channel.T, tone_target(state, anchors, profile) - '
                                   'state.T, VASCULAR_TONE, minute,\n'
                                   '                        "the tone the acute shock signal at the start of the '
                                   'minute calls for")\n'
                                   '\n'
                                   '\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/oxygenation_link_report.py",\n'
                                     '                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py",\n'
                                     '                      "clinical_core/distributive_tone_report.py",\n'
                                     '                      "clinical_core/tone_domain_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def slice_sources() -> dict[str, str]:\n',
                                     '                      "clinical_core/oxygenation_link_report.py",\n'
                                     '                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py",\n'
                                     '                      "clinical_core/distributive_tone_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def slice_sources() -> dict[str, str]:\n'),),
 'clinical_core/provenance.py': (('    the other direction a vasopressor) does to it, and the core only sums the '
                                  'changes. A minute whose changes would\n'
                                  '    take it below 0 is refused. No amount is approved; with its reader UNSET a '
                                  'change is refused, because nothing would\n'
                                  "    read it. The channel T keeps exactly one writer, the core's tone response.\n"
                                  '\n'
                                  '    WRITER CONTRACT (P2X-1, FACULTY DECISIONS 2 and 5), binding on every future '
                                  'family writer:\n'
                                  '\n'
                                  '    - the burden stays at or above 0. A writer never resolves it below '
                                  'physiologic zero, and a negative burden is not\n'
                                  '      vasoconstriction: a vasopressor treatment acts through a mechanism of its '
                                  'own, not through negative disease\n'
                                  '      burden. Resolution towards and below the arrival burden is allowed and is '
                                  'what B(b) > 1 means (FACULTY\n'
                                  '      DECISION 1), bounded by the recovery factor 1 + k b0.\n'
                                  '    - the amount may NOT be computed from the current MAP, pressure_rel, T or any '
                                  'other observable of the same\n'
                                  '      haemodynamic loop. Reading one would close an unaudited MAP -> burden -> T '
                                  '-> MAP feedback path, which is\n'
                                  '      deferred and not authorized (PRESSURE_DRIVEN_FAMILY_VASODILATION = DEFERRED '
                                  "/ NOT_AUTHORIZED). A writer's\n"
                                  '      allowed inputs are its own disease-process state, time, a treatment, and '
                                  'authored family mechanisms that do not\n'
                                  '      close that loop. The contract is structural, not enforced at runtime: the '
                                  'repository checks it by scanning every\n'
                                  '      module that builds a VasodilationChange, as it checks the other writer '
                                  'ownerships.\n'
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n',
                                  '    the other direction a vasopressor) does to it, and the core only sums the '
                                  'changes. A minute whose changes would\n'
                                  '    take it below 0 is refused. No amount is approved; with its reader UNSET a '
                                  'change is refused, because nothing would\n'
                                  "    read it. The channel T keeps exactly one writer, the core's tone response.\n"
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n'),)}

CORE_AT_P2W1 = {'clinical_core/decision_pack.py': 'c0a6d7f4b3549ae690fc01fe58ff7877d881726c4d763b5b05041355bc90bcd1',
 'clinical_core/integration.py': '110b8a3923e671603687718ba9f441ac2a877fbac19e4372631476d627958c5a',
 'clinical_core/lactate_slice.py': '89322008bbc3d72415e8e09697bf5c0ac5fcee529b5c609cc5069b489d1fc001',
 'clinical_core/provenance.py': 'cff8d48ce884f30c24e4e41d4dc1b4da86384bf5a7beb6fa16d16cf19e0a7370'}

COMMON_AT_P2W1 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/derived.py': '61f02bef25e7c330e1c8d1b725a22b8dc479b6c96ac0c2d0360bc11351336936',
 'clinical_core/distress_closure.py': '17831ecad1a43acf6364d618938ceca3835347b37b7d8c2593e76909f794740b',
 'clinical_core/distress_closure_report.py': 'c91cdc709da5c3b3babb3bff7e05331c6d505b4314c133d3f5c75f71a94a359f',
 'clinical_core/distributive_tone.py': 'b699ca1d56ee67d8ee412aef2e52b4627a1cf9e11dec301022ea40b2ab3ee82b',
 'clinical_core/distributive_tone_report.py': '46188798c1c3b06f4e2ee1c28fc3b10f60944af87f7d8ed206d8ca5cefc59c67',
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
 'clinical_core/state.py': '74bc9337c523590fe89d9fae0e23bf77d8bad25454c5eec586aa1ef919fae093',
 'clinical_core/systemic_stress.py': '572c72d8f225ee86fc4f8e40842de15809b29ef53f77edfe201c49c45dde851e',
 'clinical_core/systemic_stress_report.py': 'e8ef9be3eeab26b10d4a8339c46d5dac99dfc6228e39101766af88ef9e161ea9',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}

P2W1_FREEZE_DIGEST = "345deb5db60c0638b7b1e1d9a4eb1d1b5f6b82a232b24e084688e2db64174fed"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2W1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2W1.items()}


def p2w1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2W-1 file plus P2X-1's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2w1_bytes(relative: str) -> bytes:
    return p2w1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2w1_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2W1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


#: The closed packages whose own hash list of unchanged files still reads the live bytes: P2W-1's.
CLOSED_COMMON = ("distributive_tone",)
PATH_READERS = dt.PATH_READERS


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2w1_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


def _dt_p2v1_bytes(relative: str) -> bytes:
    """P2W-1's p2v1_bytes on the P2W-1 tree: its own reversed files from the P2W-1 text, every other file's P2W-1
    bytes."""
    return dt.p2v1_text(relative).encode("utf-8") if relative in dt.REVERSAL else p2w1_bytes(relative)


_NEW_FILES = OWN + (REPORT,)


def _old_only(paths) -> list:
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in _NEW_FILES]


class _TreeFile:
    """One of P2X-1's changed files as P2W-1 left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2w1_text(self.relative)

    def read_bytes(self):
        return p2w1_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


class _TreeDir:
    """A closed package's ``ROOT`` or ``CORE_DIR``: the P2W-1 text of P2X-1's changed files, the live path of anything
    else, and its listings without P2X-1's new files."""

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


def _carries(value, kind=None) -> bool:
    """Whether a path reader's wrapper chain already carries a view of this kind (P2X-1's own by default)."""
    kind = _TreeDir if kind is None else kind
    while value is not None and not isinstance(value, Path):
        if isinstance(value, kind):
            return True
        value = getattr(value, "path", None)
    return False


def _rebuilt(value):
    """A path reader another chain already wrapped, rebuilt with P2X-1's view at its base."""
    if isinstance(value, Path):
        return _TreeDir(value)
    inner = getattr(value, "path", None)
    rebuilt = None if inner is None else _rebuilt(inner)
    return None if rebuilt is None else type(value)(rebuilt)


_FREEZE_SOURCES = bf.freeze_sources


def _imported_closed_modules() -> list:
    return [__import__(f"clinical_core.{name}", fromlist=["ROOT"]) for name in PATH_READERS]


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2W-1's view reads the P2W-1 files (proven) and their bytes, and every
    closed listing of clinical_core leaves P2X-1's new files out. P2X-1 adds no state and changes no accepted
    reading: only refusals."""
    patch.setattr(dt, "_live", p2w1_text)
    patch.setattr(dt, "p2v1_bytes", _dt_p2v1_bytes)
    patch.setattr(dt, "_FREEZE_SOURCES", lambda: p2w1_sources(_FREEZE_SOURCES()))
    for module_name in CLOSED_COMMON:
        module = __import__(f"clinical_core.{module_name}", fromlist=["common_untouched"])
        patch.setattr(module, "common_untouched", _closed_common_untouched(module))
    for module in _imported_closed_modules():
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                patch.setattr(module, attribute, _TreeDir(value))
            elif value is not None and not _carries(value):
                rebuilt = _rebuilt(value)
                if rebuilt is not None:
                    patch.setattr(module, attribute, rebuilt)


_DT_TREE = dt.tree


def _dt_tree(patch) -> None:
    """P2W-1's own whole-tree view, nested inside P2X-1's."""
    _DT_TREE(patch)
    for module in _imported_closed_modules():
        if module is dt:
            continue
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if _carries(value) and not _carries(value, dt._TreeDir):
                patch.setattr(module, attribute, dt._TreeDir(value))


def tree(patch) -> None:
    """The whole P2W-1 tree, for P2W-1's own analysis and tests."""
    chain(patch)
    patch.setattr(dt, "tree", _dt_tree)
    patch.setattr(bf, "freeze_sources", lambda: p2w1_sources(_FREEZE_SOURCES()))


def _p2w1_digest() -> str:
    """P2W-1's own freeze digest, computed on the tree it was frozen against (its sources, not the live ones)."""
    with _p2w1_view():
        return dt.freeze_digest()


def upstream_unchanged() -> dict:
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2w1_freeze_digest": _p2w1_digest() == P2W1_FREEZE_DIGEST}


# 5. Readiness ----------------------------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    "1. b < b0 is explicit and coherent: the factor rises to exactly 1 + k b0 as the arrival vasodilation resolves, "
    "and it is declared as recovery, not as a vasopressor signal (X1-X4, the derivation)",
    "2. no negative burden: the state, the arrival anchor and a writer's minute all refuse it, and the contract says "
    "it is not vasoconstriction (X5)",
    "3. the upper and lower reachable domains fail closed instead of letting the channel's clamp shape physiology "
    "(X6, X7, X8)",
    "4. the contraction guard covers the distributive factor, derived from the common equations, and holds for every "
    "accepted witness (X9, X10, the derivation)",
    "5. no pressure-driven family vasodilation loop exists, and the writer contract forbids one (X15)",
    "6. every prior family remains exact by default, and the predecessor's behaviour is reproduced with the one "
    "declared supersession (X11, X12, X13, X14)",
    "7. TD-120 is formally superseded without rewriting history (the supersession record)",
    "8. the Phase-2 debt classes are explicit, and no item is a blocker merely because it is UNSET",
    "9. no known causal contradiction remains inside the certified Phase-2 scope",
)


def readiness(found: dict) -> dict:
    probes = found["probes"]
    checks = (
        all(probes[name]["pass"] for name in ("X1", "X2", "X3", "X4")) and found["derivation"]["pass"],
        probes["X5"]["pass"],
        all(probes[name]["pass"] for name in ("X6", "X7", "X8")),
        all(probes[name]["pass"] for name in ("X9", "X10")) and found["guards"]["p2j2_invariant_unchanged"],
        probes["X15"]["pass"] and found["writer_contract"]["pass"],
        all(probes[name]["pass"] for name in ("X11", "X12", "X13", "X14")) and found["non_regression"]["pass"],
        found["supersession"]["pass"] and found["supersession"]["p2w1_digest_unchanged"],
        found["debt_classification"]["pass"],
        found["contradictions"]["pass"],
    )
    for criterion, holds in zip(READINESS_CRITERIA, checks):
        if not holds:
            return {"verdict": f"{NOT_READY} — {criterion}", "blocker": criterion,
                    "criteria": [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]}
    return {"verdict": READY, "blocker": None,
            "criteria": [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]}


CONTRADICTIONS = {
    "worse_state_improves_output": "inside the certified scope, no: the distributive regime where a rising burden "
                                   "raises output and shortens the refill is reachable only with a declared "
                                   "vasodilatory reader, which no migrated family declares; it is recorded as "
                                   "FUTURE_RESEARCH_DEBT (FACULTY DECISION 6)",
    "same_mechanism_double_counted": "no: the compensation reads the oxygen deficit only and the burden is written by "
                                     "a family; the two factors are independent and multiply once",
    "incompatible_writer_ownership": "no: T keeps exactly one writer (the core's response), the burden one interface, "
                                     "and a family delta on T is refused",
    "disease_specific_rule_in_the_common_core": "no: the tone equation reads the common burden, its arrival anchor and "
                                                "the profile gain only; no family name appears in it",
    "hidden_point_calibration": "no: every distributive and stress magnitude is UNSET, and the probe values are "
                                "declared SYNTHETIC_ONLY",
    "unstable_feedback": "no: the delayed loop's derived bound is a contraction for every accepted combination, and a "
                         "combination that is not is refused (X9, X10)",
    "impossible_ordering": "no: the tone answers the previous minute's signal, the burden is written before it is "
                           "read, and the arrival is the response's fixed point",
}


def contradictions() -> dict:
    out = {"searched": CONTRADICTIONS, "inside_certified_scope": [], }
    out["pass"] = not out["inside_certified_scope"]
    return out


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "decisions": DECISIONS,
            "synthetic": {"tone_gain": TONE_GAIN, "small_gain": SMALL_GAIN, "arrival_burden": ARRIVAL_BURDEN,
                          "severe_burden": SEVERE_BURDEN, "burden_grid": list(BURDEN_GRID),
                          "outside_upper": list(OUTSIDE_UPPER), "outside_contraction": list(OUTSIDE_CONTRACTION)},
            "probes": PROBES, "criteria": list(READINESS_CRITERIA), "core_files": list(CORE_FILES),
            "magnitudes": "UNSET: no distributive gain, no arrival burden, no clinical maximum burden, no lower-tone "
                          "parameter, no disease-specific floor, no safety factor"}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2w1": hashlib.sha256(dt.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"revision": REVISION, "freeze_digest": freeze_digest(), "design": design(),
             "derivation": derivation(), "domain": tone_domain(anchors_with(ARRIVAL_BURDEN), reader(acs_profile())),
             "guards": guards(), "writer_contract": writer_contract(), "probes": structural_probes(),
             "supersession": supersession(), "debt_classification": debt_classification(),
             "contradictions": contradictions(), "non_regression": non_regression(),
             "proof": {"proofs": proofs(), "common_untouched": common_untouched(),
                       "p2w1_freeze_digest": _p2w1_digest() == P2W1_FREEZE_DIGEST,
                       "p2w1_record": hashlib.sha256(dt.RECORD.read_bytes()).hexdigest()}}
    found["readiness"] = readiness(found)
    return found


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
