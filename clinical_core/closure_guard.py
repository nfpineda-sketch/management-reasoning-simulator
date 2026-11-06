"""P2X-1A: the final Phase-2 closure guard repair (shadow only; adds no clinical physiology).

P2X-1's frozen rule returned PHASE2_DECLARED_PROPERTIES_CLOSED. Its adversarial review demonstrated two real closure
blockers, both reproduced independently, so the operative verdict became NOT_CLOSED. This package repairs exactly
those blockers, and the falsifiability and traceability defects the same review found. It is not a physiology package:
no clinical magnitude is selected, no new canonical state is added, nothing is integrated at runtime.

1. OWNERSHIP OF T WAS CONDITIONAL. ``step`` called ``_vascular_tone`` only when the core had a tone response to
   compute (a compensatory gain above 0, or a declared vasodilatory reader), and P2J-2's refusal of a second writer
   lived inside that function. The committed GI profile has both off, so a clinical writer of T reached the channel
   and its guard - a safety bound - shaped the value, with clamps recorded. ``integration._tone_ownership`` now runs
   on every minute of every profile, before the channel is rebuilt
   (T_CHANNEL_SINGLE_OWNER_INVARIANT_UNCONDITIONAL).

2. THE DOMAIN WAS INCLUSIVE, AND THE ACCEPTED MINUTE COULD CARRY A CLAMP. The per-minute admissibility accepted a
   target exactly on T's guard, and the channel's reconstruction then recorded a 2.8e-17 clamp inside an accepted
   minute. The supported domain is now the open interval and the value the channel will actually hold is checked, with
   no epsilon, margin or tolerance (TONE_DOMAIN_ENDPOINTS = UNRESOLVED_BOUNDARY,
   ACCEPTED_TONE_MINUTE_HAS_ZERO_CLAMP). The derived largest reachable target must also stay strictly inside, now for
   every profile and not only where the distributive reader is declared.

3. THREE CRITERIA COULD NOT FAIL, AND ONE RESULT WAS COMPUTED BUT NOT READ. P2X-1's ``contradictions``,
   ``debt_classification`` and ``supersession`` derived their verdict from lists they built empty or from non-empty
   prose, and its readiness rule never read the reversion proof. All four are executable and falsifiable here.

4. THE WRITER-CONTRACT SCAN WAS EVADABLE. It missed a qualified constructor, a helper function, positional access and
   the same-loop observables outside its list, and it read this package's modules only. The scan now follows aliases,
   qualified names and same-module helpers, covers every same-loop observable the core derives, and reads the
   repository's code.

P2X-1's analytic results are preserved unchanged: B(b) = (1 + k b0) / (1 + k b), b >= 0, a burden below the arrival
one is allowed recovery, Bmax = 1 + k b0, and the derived contraction bound. The frozen P2X-1 package, its record and
its digest are not recut: the operative correction is declared (P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A).
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
from . import integration as ig
from . import pressure_tone as pt
from . import tone_domain as x1
from . import vascular_tone as vt
from .integration import CHANNEL_BOUNDS, step
from .provenance import ProvenanceError, SourceKind
from .state import Channel, CoreInvariantError, UnresolvedBoundary

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2X-1A"
DECIDED = "2026-11-06"
OWN = ("clinical_core/closure_guard.py",)
REPORT = "clinical_core/closure_guard_report.py"
RECORD = ROOT / "docs" / "revision" / "P2X1A_closure_guard.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2X1A_REPARACION_GUARDAS_CIERRE.md"
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/integration.py", "clinical_core/provenance.py")
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]
READY = "PHASE2_DECLARED_PROPERTIES_CLOSED"
NOT_READY = "PHASE2_DECLARED_PROPERTIES_NOT_CLOSED"

#: The faculty's decisions this package implements, verbatim in substance.
DECISIONS = {
    "1_unconditional_ownership": "T_CHANNEL_SINGLE_OWNER_INVARIANT_UNCONDITIONAL: the common core is the only owner "
                                 "and writer of Channel.T for the certified Phase-2 architecture; the ownership "
                                 "invariant executes independently of whether the core has a tone response to "
                                 "compute, with no profile-dependent behaviour",
    "2_strict_domain": "TONE_DOMAIN_ENDPOINTS = UNRESOLVED_BOUNDARY: the supported tone domain is the open interval "
                       "T_lo < target < T_hi; the exact endpoints are unresolved boundaries, not accepted interior "
                       "physiology, and fail closed before the channel clamp - with no epsilon, clinical margin, "
                       "floating tolerance or alternative floor",
    "3_zero_clamp": "ACCEPTED_TONE_MINUTE_HAS_ZERO_CLAMP: no accepted Phase-2 tone update carries a clamp:bounds:T "
                    "or equivalent clipping; a floating adjustment of 2.8e-17 means the candidate reached the "
                    "boundary and should have been refused before the channel was rebuilt",
    "4_keep_p2x1_analysis": "the accepted P2X-1 analytic results stand: B(b) = (1 + k b0) / (1 + k b), b >= 0, "
                            "b < b0 is allowed recovery, Bmax = 1 + k b0, and the analytically derived contraction "
                            "bound; they are reopened only on an actual mathematical error, and this package found "
                            "none",
    "5_no_pressure_driven_writer": "PRESSURE_DRIVEN_FAMILY_VASODILATION_NOT_AUTHORIZED: a future VasodilationChange "
                                   "writer may not depend on the current MAP, pressure_rel, SBP, DBP, T or an "
                                   "equivalent same-loop observable; pressure -> tone stays a separate future common "
                                   "mechanism and is not implemented",
    "6_maldistribution": "the distributive CRT, extraction heterogeneity, maldistribution, distributive lactate, "
                         "plasma leak, upper airway and epinephrine targets stay FUTURE_RESEARCH_DEBT, outside the "
                         "Phase-2 closure scope",
    "7_p2x1_supersession": "P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A: P2X-1 is not recut; its frozen rule said CLOSED, "
                           "its review demonstrated two real blockers, its operative verdict became NOT_CLOSED, and "
                           "P2X-1A repairs those exact blockers with every P2X-1 digest and artifact preserved",
    "8_decision_file": "the eight faculty decisions behind P2X-1 and P2X-1A are recorded in the project's "
                       "authoritative Decision File, using the repository's existing convention",
    "scope": "a closure repair package: guards, falsifiability and traceability only. No new clinical physiology, no "
             "magnitude, no new canonical state, no runtime integration, no Phase 3",
}

#: The one place this package reads FACULTY DECISION 1 against a published repository classification, declared so the
#: faculty can confirm or overrule it. The decision says no family "or any other contribution" may write T. The
#: repository already classifies writers: ``_check_owned`` lets a scripted synthetic probe write V and Hb, which the
#: shared blood state otherwise owns (P2I-2T), and P2J-1's published TONE_RULE reads "a writer outside a synthetic
#: probe, a test or a bound is a clinical writer", naming bands.py, hemodynamic_probes.py and pressure_tone.py as the
#: non-clinical writers. So the unconditional guard refuses every CLINICAL source on every profile - which is the hole
#: the review demonstrated, with a disease module - and leaves the declared synthetic probes, which appear in no case
#: and no family trajectory, driving T as they did. Refusing them too would retire three band probes and move the
#: calibration evidence that several closed packages read, which is physiology work this package is not authorized to
#: do.
INTERPRETATION = {
    "decision": "FACULTY DECISION 1, 'a family or any other contribution must NOT directly write Channel.T'",
    "implemented_as": "every clinical source (disease module, treatment, intervention, case) is refused on every "
                      "profile, unconditionally; a declared synthetic probe (SourceKind.SCRIPTED_EVENT) still "
                      "writes T, as it still writes V and Hb",
    "repository_basis": "integration._check_owned (P2I-2T) and pressure_tone.TONE_RULE / PROBE_MODULES (P2J-1)",
    "what_the_review_demonstrated": "a DISEASE_MODULE writer of T accepted on the GI profile: refused now",
    "if_the_faculty_wants_the_wider_reading": "bands.PROBES['vasodilation'], "
                                              "bands.PROBES['vasodilation_with_demand'] and "
                                              "bands.HISTORICAL_PROBES['vasodilation_with_preload_loss'] are the "
                                              "only remaining T writers; refusing them retires those probes and the "
                                              "closed readings that cite them, and needs a separate authorization",
}

#: SYNTHETIC_ONLY probe values. None is a clinical magnitude and none appears in any committed profile.
TONE_GAIN = x1.TONE_GAIN
ENDPOINT_BURDEN = 9.0
INSIDE_BURDEN = 8.9
#: A burden the delayed loop can carry for a whole course without leaving the supported range: with k = 1 the target
#: is C(s) / 3, and C(s) stays inside [1 / (1 + g s0), (1 + g) / (1 + g s0)], so every minute is interior. Next to the
#: guard (INSIDE_BURDEN) a single minute is admissible but the loop walks out of the range, and fails closed there.
COURSE_BURDEN = 2.0
SEVERE_BURDEN = x1.SEVERE_BURDEN
WITNESS_READERS = ((0.25, 2.0), (1.0, 0.5), (1.0, 1.0))
#: The P2J-2 probe reading this package supersedes: at gain 2.0 the largest reachable target is exactly T's upper
#: guard on anchors whose arrival deficit is 0, which FACULTY DECISION 2 makes an unresolved boundary.
P2J2_ENDPOINT_GAIN = 2.0
P2J2_GAINS_INSIDE = tuple(g for g in vt.GAINS if g != P2J2_ENDPOINT_GAIN)


def _refused(build, expect: str, error=(CoreInvariantError, ProvenanceError)) -> dict:
    """Whether the call fails closed AND says why: P2X-1's helper ignored the message (its review's R-F13)."""
    try:
        build()
    except error as problem:
        return {"refused": True, "says_why": expect in str(problem), "message": str(problem)[:160]}
    return {"refused": False, "says_why": False, "message": ""}


def _clinical_writer(id_="fam"):
    """A disease module writing the T channel: the review's own witness, from the frozen P2W-1 package."""
    return dt._FamilyTone(id_)


def _clamps(record) -> list:
    return sorted({delta.source.key for delta in record.deltas if delta.source.kind is SourceKind.CLAMP})


def _tone_clamps(records) -> list:
    return [[key for key in _clamps(record) if key.endswith(f"bounds:{Channel.T.value}")] for record in records]


# 1. P2X-1A-1, P2X-1A-2 and P2X-1A-3: the repaired guards, read off the live core ---------------------------------------------

def _core_functions() -> dict:
    tree = ast.parse(inspect.getsource(sys.modules["clinical_core.integration"]))
    return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _unconditional_call(function: ast.FunctionDef, name: str) -> dict:
    """Whether ``name`` is called from the function's own statement list, under no condition or loop, and before the
    channel reconstruction."""
    positions, blocked, clamp_at = [], [], None
    for index, statement in enumerate(function.body):
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == name:
                positions.append(index)
                if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                        and getattr(statement.value.func, "id", None) == name):
                    blocked.append(ast.dump(statement)[:60])
        if isinstance(statement, ast.For) and "SCALAR_CHANNELS" in ast.unparse(statement.iter):
            clamp_at = index
    return {"called": bool(positions), "at_statement_level": bool(positions) and not blocked,
            "before_the_channel_rebuild": bool(positions) and clamp_at is not None and max(positions) < clamp_at,
            "inside_a_condition": blocked}


def _comparisons(function: ast.FunctionDef, text: str) -> list:
    return [ast.unparse(node) for node in ast.walk(function)
            if isinstance(node, ast.Compare) and text in ast.unparse(node)]


def _code_only(function: ast.FunctionDef) -> str:
    """The function's code with its docstring removed: a word in the prose is not an implementation."""
    body = [node for node in function.body if not (isinstance(node, ast.Expr)
                                                   and isinstance(node.value, ast.Constant)
                                                   and isinstance(node.value.value, str))]
    return "\n".join(ast.unparse(node) for node in body)


def _calls(function: ast.FunctionDef, name: str) -> bool:
    return any(isinstance(node, ast.Call) and getattr(node.func, "id", None) == name for node in ast.walk(function))


def _boundary_test(function: ast.FunctionDef, exception: str) -> str:
    """The test of the condition that fails closed with ``exception``."""
    for node in ast.walk(function):
        if not isinstance(node, ast.If):
            continue
        for inner in node.body:
            if isinstance(inner, ast.Raise) and getattr(inner.exc.func, "id", None) == exception:
                return ast.unparse(node.test)
    return ""


def guards() -> dict:
    """What each repaired invariant is, where it executes, and that nothing else in the coupling moved."""
    source = inspect.getsource(sys.modules["clinical_core.integration"])
    functions = _core_functions()
    tone, ownership, stepper = functions["_vascular_tone"], functions["_tone_ownership"], functions["step"]
    tone_text = _code_only(tone)
    literals = sorted({node.value for node in ast.walk(tone) if isinstance(node, ast.Constant)
                       and isinstance(node.value, float) and 0.0 < node.value < T_LOWER})
    boundary = [_boundary_test(tone, "UnresolvedBoundary")]
    out = {
        "ownership": {"function": "integration._tone_ownership", **_unconditional_call(stepper, "_tone_ownership"),
                      "refuses": "every clinical writer of T (a source whose kind is not SCRIPTED_EVENT)",
                      "out_of_the_response": not _calls(tone, "_tone_ownership")},
        "strict_domain": {"per_minute": boundary,
                          "strict": all(boundary) and all("<=" not in item and ">=" not in item
                                                          for item in boundary),
                          "parameter_level": "domain['largest_target'] >= upper" in tone_text,
                          "unconditional_parameter_level": any(
                              "largest_target" in ast.unparse(node.test) for node in ast.walk(tone)
                              if isinstance(node, ast.If) and "distributive_reader" not in ast.unparse(node.test)),
                          "reconstruction_checked": "reconstructed" in tone_text and
                          any("reconstructed" in item for item in boundary),
                          "exception": "UnresolvedBoundary" if "UnresolvedBoundary" in tone_text else "",
                          "no_tolerance_constant": not literals and not any(
                              name in tone_text for name in ("eps", "epsilon", "tol", "margin", "atol", "rtol")),
                          "floats_below_the_lower_guard": literals},
        "p2j2_untouched": {
            "profile_invariant": "self.deficit_to_tone_gain * self.afterload_sensitivity >= 1.0" in
                                 inspect.getsource(dv),
            "gain_check": "1.0 + profile.deficit_to_tone_gain > upper" in source,
            "composition_refusal": "write T while the vascular-tone response is on" in source},
        "p2x1_untouched": {
            "contraction_guard": "domain['loop_slope_bound'] >= 1.0" in tone_text,
            "reader_conditional_contraction": any("distributive_reader" in ast.unparse(node.test)
                                                  for node in ast.walk(tone) if isinstance(node, ast.If)),
            "tone_domain_closed_form": "tone_domain" in source},
        "clamp_still_the_last_layer": "held within [{lower:g}, {upper:g}] ({why})" in source,
        "delta_expression": next(ast.unparse(node.value.args[1]) for node in ast.walk(tone)
                                 if isinstance(node, ast.Return) and isinstance(node.value, ast.Call)),
        "refusals": {name: [ast.unparse(node.exc.args[0])[:60] for node in ast.walk(function)
                            if isinstance(node, ast.Raise)]
                     for name, function in (("_tone_ownership", ownership), ("_vascular_tone", tone))},
    }
    out["pass"] = (out["ownership"]["called"] and out["ownership"]["at_statement_level"]
                   and out["ownership"]["before_the_channel_rebuild"] and out["ownership"]["out_of_the_response"]
                   and out["strict_domain"]["strict"] and out["strict_domain"]["parameter_level"]
                   and out["strict_domain"]["unconditional_parameter_level"]
                   and out["strict_domain"]["reconstruction_checked"]
                   and out["strict_domain"]["exception"] == "UnresolvedBoundary"
                   and out["strict_domain"]["no_tolerance_constant"]
                   and all(out["p2j2_untouched"].values()) and all(out["p2x1_untouched"].values())
                   and out["clamp_still_the_last_layer"]
                   and out["delta_expression"] == "amount")
    return out


# 2. P2X-1A-8: the writer contract, materially enforceable --------------------------------------------------------------------

#: Every observable of the same haemodynamic loop the core derives. Reading one to compute a burden would close an
#: unaudited MAP -> burden -> T -> MAP path (FACULTY DECISION 5).
FORBIDDEN_READS = ("crt_s", "dbp", "delivery_rel", "map", "mean_arterial_pressure", "output_rel", "pressure_rel",
                   "sbp", "sympathetic_drive", "T")
RECORD_NAME = "VasodilationChange"
#: The bypasses P2X-1's review found, as source the scan must reject. Each is a complete module.
BYPASS_PATTERNS = {
    "qualified_constructor": "from clinical_core import provenance\n"
                             "def write(state, minute, source):\n"
                             "    return provenance.VasodilationChange(state.map * 0.01, source, minute, 'b')\n",
    "helper_function": "from clinical_core.provenance import VasodilationChange\n"
                       "def _amount(view):\n"
                       "    return view.pressure_rel * 0.1\n"
                       "def write(view, minute, source):\n"
                       "    return VasodilationChange(_amount(view), source, minute, 'b')\n",
    "alias": "from clinical_core.provenance import VasodilationChange as VC\n"
             "def write(state, minute, source):\n"
             "    return VC(state.sbp / 100.0, source, minute, 'b')\n",
    "positional_access": "from clinical_core.provenance import VasodilationChange\n"
                         "def write(view, minute, source):\n"
                         "    return VasodilationChange(getattr(view, 'map') * 0.01, source, minute, 'b')\n",
    "same_loop_observable": "from clinical_core.provenance import VasodilationChange\n"
                            "def write(view, minute, source):\n"
                            "    return VasodilationChange(view.output_rel - 1.0, source, minute, 'b')\n",
    "subscript_access": "from clinical_core.provenance import VasodilationChange\n"
                        "def write(row, minute, source):\n"
                        "    return VasodilationChange(row['map'] * 0.01, source, minute, 'b')\n",
    "tone_feedback": "from clinical_core.provenance import VasodilationChange\n"
                     "def write(state, minute, source):\n"
                     "    return VasodilationChange(1.0 - state.T, source, minute, 'b')\n",
}
#: Source the scan must accept: the allowed inputs (disease-process state, time, treatment, authored mechanism).
ALLOWED_PATTERN = ("from clinical_core.provenance import VasodilationChange\n"
                   "def write(process, minute, source):\n"
                   "    amount = process.severity * 0.1 if minute < process.until else 0.0\n"
                   "    return VasodilationChange(amount, source, minute, 'authored mechanism')\n")


def _record_names(tree: ast.AST) -> set:
    """Every name that denotes the record in this module: the import, an alias, or a qualified attribute."""
    names = {RECORD_NAME}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == RECORD_NAME and alias.asname:
                    names.add(alias.asname)
    return names


def _builds_record(function: ast.FunctionDef, names: set) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", None) in names or getattr(node.func, "attr", None) == RECORD_NAME:
            return True
    return False


def _reads(function: ast.FunctionDef) -> set:
    """Forbidden observables this function reads, through an attribute, a getattr, or a constant subscript."""
    found = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_READS:
            found.add(node.attr)
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and node.slice.value in FORBIDDEN_READS:
            found.add(node.slice.value)
        elif isinstance(node, ast.Call) and getattr(node.func, "id", None) == "getattr" and len(node.args) > 1 \
                and isinstance(node.args[1], ast.Constant) and node.args[1].value in FORBIDDEN_READS:
            found.add(node.args[1].value)
    return found


def _functions(tree: ast.AST) -> dict:
    """Every function and method by a qualified name, so two methods called ``contribute`` never collapse."""
    out = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                out[name] = child
                walk(child, f"{name}.")
            elif isinstance(child, ast.ClassDef):
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)

    walk(tree, "")
    return out


def _called(function: ast.FunctionDef, qualified: str, known: dict) -> set:
    """The module's own functions this one calls: a plain name, or a method of the same class through self / cls."""
    owner = qualified.rsplit(".", 1)[0] if "." in qualified else ""
    out = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in known:
            out.add(node.func.id)
        elif isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", None) in ("self", "cls"):
            candidate = f"{owner}.{node.func.attr}" if owner else node.func.attr
            if candidate in known:
                out.add(candidate)
        elif isinstance(node.func, ast.Attribute) and node.func.attr in known:
            out.add(node.func.attr)
    return out


def scan_text(source: str, relative: str = "<probe>") -> dict:
    """Every writer of the record in one module, and the forbidden observables it reads - its own, and those of the
    module's own helpers it calls, transitively."""
    tree = ast.parse(source)
    names = _record_names(tree)
    functions = _functions(tree)
    writers, offenders = [], []
    for name, function in sorted(functions.items()):
        if not _builds_record(function, names):
            continue
        writers.append(f"{relative}:{name}")
        seen, pending, reads = {name}, list(_called(function, name, functions)), set(_reads(function))
        while pending:
            helper = pending.pop()
            if helper in seen or helper not in functions:
                continue
            seen.add(helper)
            reads |= _reads(functions[helper])
            pending.extend(_called(functions[helper], helper, functions))
        if reads:
            offenders.append({"writer": f"{relative}:{name}", "reads": sorted(reads),
                              "through": sorted(seen - {name}) or ["itself"]})
    return {"writers": writers, "offenders": offenders}


def _scanned_files() -> list:
    """The repository's own python, not only this package's modules: the core, its modules, and the suites that may
    carry a probe writer. The external validation folder is never read."""
    out = []
    for path in sorted(ROOT.glob("*.py")) + sorted(CORE_DIR.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts or relative in OWN or relative == REPORT:
            continue
        out.append(path)
    return out


def writer_contract() -> dict:
    """The published contract, the scan that enforces it, and the bypasses the scan now rejects."""
    text = (CORE_DIR / "provenance.py").read_text(encoding="utf-8")
    writers, offenders, files = [], [], 0
    for path in _scanned_files():
        source = path.read_text(encoding="utf-8")
        if RECORD_NAME not in source:
            continue
        files += 1
        found = scan_text(source, path.relative_to(ROOT).as_posix())
        writers.extend(found["writers"])
        offenders.extend(found["offenders"])
    rejected = {name: bool(scan_text(source)["offenders"]) for name, source in sorted(BYPASS_PATTERNS.items())}
    allowed = scan_text(ALLOWED_PATTERN)
    out = {"contract_declared": "WRITER CONTRACT (P2X-1, FACULTY DECISIONS 2 and 5)" in text,
           "p2x1a_strengthening_declared": "P2X-1A makes that scan materially enforceable" in text,
           "forbidden_reads": list(FORBIDDEN_READS),
           "files_scanned": files, "writers": sorted(writers), "offenders": offenders,
           "bypasses_rejected": rejected, "allowed_pattern_accepted": not allowed["offenders"],
           "allowed_inputs": "the writer's own disease-process state, time, a treatment, and authored family "
                             "mechanisms that do not close the haemodynamic loop"}
    out["pass"] = (out["contract_declared"] and out["p2x1a_strengthening_declared"] and not offenders
                   and all(rejected.values()) and out["allowed_pattern_accepted"] and bool(allowed["writers"]))
    return out


# 3. P2X-1A structural probes A1-A22 -----------------------------------------------------------------------------------------

def _endpoint_reader():
    """The witness the P2X-1 review used for the inclusive boundary: k = 1, b0 = 0, so B(b) = 1 / (1 + b) and a burden
    of exactly 9 puts the target exactly on T's lower guard, with the whole parameter domain admissible."""
    return x1.reader(x1.acs_profile(), gain=1.0), x1.anchors_with(0.0)


def probe_a1() -> dict:
    """GI, the committed profile with the compensation off and no distributive reader, plus a clinical writer of T:
    refused before the channel is rebuilt. This is the exact case P2X-1's review demonstrated as accepted."""
    anchors, profile = dt.committed_pairs()["gi"]
    out = {"profile": "gi", "gain": profile.deficit_to_tone_gain, "reader": profile.vasodilatory_burden_to_tone_gain,
           "response_runs": profile.deficit_to_tone_gain > 0.0
           or profile.vasodilatory_burden_to_tone_gain is not None}
    out.update(_refused(lambda: dt.course((_clinical_writer(),), 6, anchors, profile), "only clinical owner"))
    out["pass"] = out["refused"] and out["says_why"] and not out["response_runs"]
    return out


def probe_a2() -> dict:
    """ACS, where the response does run: the same writer, the same refusal, from the same guard."""
    anchors, profile = dt.committed_pairs()["acs"]
    out = {"profile": "acs", "gain": profile.deficit_to_tone_gain, "response_runs": True}
    out.update(_refused(lambda: dt.course((_clinical_writer(),), 6, anchors, profile), "only clinical owner"))
    out["pass"] = out["refused"] and out["says_why"]
    return out


def probe_a3() -> dict:
    """Every committed profile: one ownership invariant, one message, no profile-dependent behaviour."""
    rows, messages = {}, set()
    for name, (anchors, profile) in sorted(dt.committed_pairs().items()):
        found = _refused(lambda a=anchors, p=profile: dt.course((_clinical_writer(),), 4, a, p),
                         "only clinical owner")
        rows[name] = {"refused": found["refused"], "says_why": found["says_why"],
                      "response_runs": profile.deficit_to_tone_gain > 0.0
                      or profile.vasodilatory_burden_to_tone_gain is not None}
        messages.add(found["message"].split(":", 1)[-1].strip())
    out = {"profiles": rows, "one_message": len(messages) == 1,
           "both_regimes_present": {row["response_runs"] for row in rows.values()} == {True, False}}
    out["pass"] = all(row["refused"] and row["says_why"] for row in rows.values()) and out["one_message"] \
        and out["both_regimes_present"]
    return out


def probe_a4() -> dict:
    """A target exactly on the lower guard is an unresolved boundary, not accepted physiology."""
    profile, anchors = _endpoint_reader()
    state = x1.state_with(anchors, profile, ENDPOINT_BURDEN)
    target = dv.tone_target(state, anchors, profile)
    out = {"burden": ENDPOINT_BURDEN, "target": target, "is_the_endpoint": target == T_LOWER,
           "domain_admissible": ig.tone_domain(anchors, profile)["largest_target"] < T_UPPER}
    out.update(_refused(lambda: step(state, (), anchors, profile), "unresolved boundaries"))
    out["pass"] = out["is_the_endpoint"] and out["domain_admissible"] and out["refused"] and out["says_why"]
    return out


def probe_a5() -> dict:
    """Below the lower guard, refused, with no clinical maximum burden declared anywhere."""
    profile, anchors = _endpoint_reader()
    state = x1.state_with(anchors, profile, SEVERE_BURDEN)
    target = dv.tone_target(state, anchors, profile)
    out = {"burden": SEVERE_BURDEN, "target": target, "below_the_guard": target < T_LOWER,
           "no_maximum_burden_declared": x1.state_with(anchors, profile, 1e6).aux.vasodilatory_burden == 1e6}
    out.update(_refused(lambda: step(state, (), anchors, profile), "unresolved boundaries"))
    out["pass"] = out["below_the_guard"] and out["refused"] and out["says_why"] \
        and out["no_maximum_burden_declared"]
    return out


def probe_a6() -> dict:
    """A parameter domain whose largest reachable target is exactly the upper guard: refused before execution, now on
    a profile with no distributive reader. This is the P2J-2 probe reading P2X-1A supersedes."""
    profile = vt.tone_profile(P2J2_ENDPOINT_GAIN, vt.PRIMARY_AFTERLOAD)
    domain = ig.tone_domain(vt.NEUTRAL, profile)
    state = dv.arrival_state(vt.NEUTRAL, profile)
    out = {"gain": P2J2_ENDPOINT_GAIN, "reader": profile.vasodilatory_burden_to_tone_gain,
           "largest_target": domain["largest_target"], "is_the_endpoint": domain["largest_target"] == T_UPPER,
           "p2j2_gain_check_would_pass": not 1.0 + P2J2_ENDPOINT_GAIN > T_UPPER}
    out.update(_refused(lambda: step(state, (), vt.NEUTRAL, profile), "reaches or passes"))
    out["pass"] = out["is_the_endpoint"] and out["refused"] and out["says_why"] \
        and out["p2j2_gain_check_would_pass"] and out["reader"] is None
    return out


def probe_a7() -> dict:
    """Above the upper guard, refused before execution (P2X-1's X6, kept)."""
    gain, burden = x1.OUTSIDE_UPPER
    profile, anchors = x1.reader(x1.acs_profile(), gain=gain), x1.anchors_with(burden)
    domain = ig.tone_domain(anchors, profile)
    out = {"gain": gain, "arrival_burden": burden, "largest_target": domain["largest_target"],
           "above_the_guard": domain["largest_target"] > T_UPPER}
    out.update(_refused(lambda: step(dv.arrival_state(anchors, profile), (), anchors, profile), "reaches or passes"))
    out["pass"] = out["above_the_guard"] and out["refused"] and out["says_why"]
    return out


def probe_a8() -> dict:
    """An interior target - including one next to the lower guard - runs, and the channel holds exactly it."""
    profile, anchors = _endpoint_reader()
    state = x1.state_with(anchors, profile, INSIDE_BURDEN)
    target = dv.tone_target(state, anchors, profile)
    after, record = step(state, (), anchors, profile)
    rebuilt = state.T + (target - state.T)
    out = {"burden": INSIDE_BURDEN, "target": target, "interior": T_LOWER < target < T_UPPER,
           "rebuilt": rebuilt, "rebuilt_interior": T_LOWER < rebuilt < T_UPPER,
           "channel_holds_the_rebuilt_value": after.T == rebuilt,
           "rebuild_difference": rebuilt - target, "clamps": _clamps(record),
           "distance_to_the_guard": target - T_LOWER}
    # The channel holds the value the guard checked, not the unrounded target: that difference is exactly what left a
    # clamp inside an accepted minute before, and it is now part of the admissibility test.
    out["pass"] = out["interior"] and out["rebuilt_interior"] and out["channel_holds_the_rebuilt_value"] \
        and not out["clamps"]
    return out


def probe_a9() -> dict:
    """The accepted minutes themselves, not the arithmetic of the target: no clamp record of any kind on T, over a
    course that walks the burden from the arrival value to next to the lower guard and back."""
    profile, anchors = _endpoint_reader()
    items = (dt.SyntheticVasodilation("down", COURSE_BURDEN, 0, 1),
             dt.SyntheticVasodilation("up", -COURSE_BURDEN, 3, 4))
    states, records = dt.course(items, 6, anchors, profile)
    out = {"burden_trail": [state.aux.vasodilatory_burden for state in states],
           "tone": [state.T for state in states], "clamps": [_clamps(record) for record in records],
           "tone_clamps": _tone_clamps(records),
           "interior": all(T_LOWER < dv.tone_target(state, anchors, profile) < T_UPPER for state in states[:-1])}
    out["pass"] = out["interior"] and not any(out["clamps"]) and not any(out["tone_clamps"])
    return out


def probe_a10() -> dict:
    """A negative burden stays invalid everywhere: the state, the arrival anchor and a writer's minute (P2X-1's X5)."""
    return x1.probe_x5()


def probe_a11() -> dict:
    """A burden below the arrival one is still allowed recovery, and the target still rises as it resolves."""
    return x1.probe_x3()


def probe_a12() -> dict:
    """The maximum recovery factor is still exactly 1 + k b0."""
    return x1.probe_x4()


def _live_slope(anchors, profile, state, tone: float) -> float:
    held = state.evolve(T=tone)
    h = 1e-6
    return (dv.tone_target(held.evolve(T=tone + h), anchors, profile)
            - dv.tone_target(held.evolve(T=tone - h), anchors, profile)) / (2 * h)


def probe_a13() -> dict:
    """The contraction guard exercised with an arrival burden above 0, so the distributive factor is really in it: the
    derived bound scales with 1 + k b0 and every accepted witness is a contraction."""
    rows = {}
    for gain, arrival in WITNESS_READERS:
        profile, anchors = x1.reader(x1.acs_profile(), gain=gain), x1.anchors_with(arrival)
        domain = ig.tone_domain(anchors, profile)
        without = domain["loop_slope_bound"] / domain["recovery_max"]
        accepted = not _refused(lambda a=anchors, p=profile: step(dv.arrival_state(a, p), (), a, p),
                                "")["refused"]
        rows[f"k{gain:g}_b{arrival:g}"] = {
            "arrival_burden": arrival, "recovery_max": domain["recovery_max"],
            "bound": domain["loop_slope_bound"], "bound_without_the_factor": without,
            "factor_is_in_the_bound": domain["recovery_max"] > 1.0
            and math.isclose(domain["loop_slope_bound"], without * domain["recovery_max"], rel_tol=1e-12),
            "contraction": domain["loop_slope_bound"] < 1.0, "accepted": accepted}
    out = {"witnesses": rows, "any_arrival_burden_above_zero": any(row["arrival_burden"] > 0.0
                                                                   for row in rows.values())}
    out["pass"] = out["any_arrival_burden_above_zero"] and all(
        row["factor_is_in_the_bound"] and row["contraction"] and row["accepted"] for row in rows.values())
    return out


def probe_a14() -> dict:
    """The LIVE slope where the distributive factor is not 1: measured on the real equations, at a state whose burden
    is 0 while the arrival burden is above it (B = Bmax), and compared with the analytic bound."""
    rows = {}
    for gain, arrival in WITNESS_READERS:
        if arrival <= 0.0:
            continue
        profile, anchors = x1.reader(x1.acs_profile(), gain=gain), x1.anchors_with(arrival)
        domain = ig.tone_domain(anchors, profile)
        resolved = x1.state_with(anchors, profile, 0.0)
        at_arrival = x1.state_with(anchors, profile, arrival)
        factor = (1.0 + gain * arrival) / (1.0 + gain * 0.0)
        measured = {str(tone): _live_slope(anchors, profile, resolved, tone) for tone in (1.0, 1.5, 2.0)}
        at_one = {str(tone): _live_slope(anchors, profile, at_arrival, tone) for tone in (1.0, 1.5, 2.0)}
        ratios = [measured[k] / at_one[k] for k in measured if at_one[k]]
        rows[f"k{gain:g}_b{arrival:g}"] = {
            "distributive_factor": factor, "factor_is_not_one": factor != 1.0,
            "live_slope": measured, "live_slope_at_the_arrival_burden": at_one,
            "ratio_matches_the_factor": all(math.isclose(r, factor, rel_tol=1e-6) for r in ratios),
            "under_the_bound": all(abs(value) < domain["loop_slope_bound"] for value in measured.values()),
            "bound": domain["loop_slope_bound"]}
    out = {"witnesses": rows}
    out["pass"] = bool(rows) and all(row["factor_is_not_one"] and row["ratio_matches_the_factor"]
                                     and row["under_the_bound"] for row in rows.values())
    return out


def probe_a15() -> dict:
    """A combination whose derived bound is not a contraction is refused, with its largest target inside the range."""
    return x1.probe_x10()


def probe_a16() -> dict:
    """Each bypass the P2X-1 review found, rejected by the scan; the allowed pattern still accepted."""
    rejected = {name: scan_text(source) for name, source in sorted(BYPASS_PATTERNS.items())}
    allowed = scan_text(ALLOWED_PATTERN)
    out = {"bypasses": {name: {"writers": found["writers"], "reads": sorted({read for item in found["offenders"]
                                                                            for read in item["reads"]})}
                        for name, found in rejected.items()},
           "allowed": {"writers": allowed["writers"], "offenders": allowed["offenders"]}}
    out["pass"] = all(found["offenders"] for found in rejected.values()) and not allowed["offenders"] \
        and all(found["writers"] for found in rejected.values()) and bool(allowed["writers"])
    return out


# 4. P2X-1A-6: the supersession record, verified against the repository's own artifacts ----------------------------------------

#: Each superseded result: the historical artifacts, the authoritative ones, and the immutable references that must
#: still hold. Every path and digest here is checked, not asserted (P2X-1's review found two names that did not exist).
HISTORY = {
    "TD120_HISTORICAL_SUPERSESSION_ACCEPTED": {
        "status": "P2S3_FROZEN_VERDICT_SUPERSEDED_BY_P2T3",
        "historical": {"document": "docs/revision/P2S3_ASMA_SOMBRA.md",
                       "record": "docs/revision/P2S3_asthma_migration.json",
                       "freeze_digest": "652d7138ff672fa9e43c92e06ac3042486e8f47ab504736726b0d53f42a7649b",
                       "record_sha": "709e6389365c49b010abdfedbf05ac42e51533d855eff9f2b50ff0e37081e4dd"},
        "superseding": {"document": "docs/revision/P2T3_ASMA_DISTRES_SOMBRA.md",
                        "record": "docs/revision/P2T3_asthma_distress_migration.json",
                        "freeze_digest": "3a648a9e055c9182fe670f5360f1cc73d1d799b9f1bd3d557df2ffdf67e2efb2",
                        "record_sha": "6fa395eaaf70dbf1f11c91e08d5758495e907b68b02e79ad83b509aae8ae13ac"},
        "what_happened": "P2S-3's frozen rule returned ASTHMA_SHADOW_MIGRATION_READY; its adversarial review "
                         "demonstrated a COMMON_DRIVE_GAP and the corrected operative classification was NOT_READY; "
                         "P2T-1, P2T-2 and P2T-3 closed that blocker and P2T-3 is the authoritative asthma result",
        "history_preserved": "no P2S-3 source, record or digest is recut or rewritten",
    },
    "P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A": {
        "status": "P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A",
        "historical": {"document": "docs/revision/P2X1_CIERRE_PROPIEDADES_DECLARADAS.md",
                       "record": "docs/revision/P2X1_tone_domain.json",
                       "freeze_digest": "3afa71b2dfa0f47eb1a00e8987c79cd18b246788e366ac07fe58eacc21815a0e",
                       "record_sha": "dd37487c3689076822180c262b5cb7f93cf06ed889ce8f99e73b0a4a733120d1"},
        "superseding": {"document": DOCUMENT.relative_to(ROOT).as_posix(),
                        "record": RECORD.relative_to(ROOT).as_posix(),
                        "freeze_digest": None, "record_sha": None},
        "what_happened": "P2X-1's frozen rule returned PHASE2_DECLARED_PROPERTIES_CLOSED; its adversarial review "
                         "demonstrated two real closure blockers - the ownership guard did not run with the tone "
                         "response off, and the inclusive boundary left a 2.8e-17 clamp inside an accepted minute - "
                         "so the operative verdict became NOT_CLOSED; P2X-1A repairs those exact blockers",
        "history_preserved": "no P2X-1 source, record or digest is recut or rewritten; its two P2W-1 supersession "
                             "rows stand as it published them",
    },
    "P2J2_UPPER_ENDPOINT_PROBE_SUPERSEDED_BY_P2X1A": {
        "status": "P2J2_ENDPOINT_PROBE_READING_SUPERSEDED",
        "historical": {"document": "docs/revision/P2J2_TONO_VASCULAR_DINAMICO.md",
                       "record": "docs/revision/P2J2_vascular_tone.json",
                       "freeze_digest": "baa2ee124decc7c84a48b0b8fe5031a9dab774e3587176c79e1907df94904545",
                       "record_sha": "0c5c9feda158d9d799a0d12f900a9776fcca917ea0b80bfd7b580ec604031924"},
        "superseding": {"document": DOCUMENT.relative_to(ROOT).as_posix(),
                        "record": RECORD.relative_to(ROOT).as_posix(),
                        "freeze_digest": None, "record_sha": None},
        "what_happened": "P2J-2's probe grid includes the gain 2.0, whose largest reachable target is exactly T's "
                         "upper guard on anchors with no arrival deficit. P2J-2 accepted that reading (its check is "
                         "1 + g > upper); FACULTY DECISION 2 makes the endpoint an unresolved boundary, so the "
                         "combination is refused and that probe row is superseded. Every gain below it is unchanged",
        "history_preserved": "the P2J-2 record and digest are not recut; the superseded reading is declared here and "
                             "its suite reads the grid without the endpoint gain",
    },
}


def _json_at(relative: str):
    path = ROOT / relative
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


#: This package's own record and document, written by the evaluation run after the freeze. Their existence is NOT
#: read here: the record would then depend on whether it had already been written, and could not reproduce.
_OWN_ARTIFACTS = (RECORD.relative_to(ROOT).as_posix(), DOCUMENT.relative_to(ROOT).as_posix())


def _artifact(entry: dict) -> dict:
    document, record = ROOT / entry["document"], ROOT / entry["record"]
    data = _json_at(entry["record"])
    own = entry["document"] in _OWN_ARTIFACTS or entry["record"] in _OWN_ARTIFACTS
    out = {"document": entry["document"],
           "document_exists": "written by the evaluation run" if own else document.exists(),
           "record": entry["record"],
           "record_exists": "written by the evaluation run" if own else record.exists(),
           "freeze_digest_matches": None, "record_sha_matches": None}
    if entry.get("freeze_digest"):
        out["freeze_digest_matches"] = bool(data) and data.get("freeze_digest") == entry["freeze_digest"]
    if entry.get("record_sha"):
        out["record_sha_matches"] = hashlib.sha256(record.read_bytes()).hexdigest() == entry["record_sha"] \
            if record.exists() else False
    return out


def supersession() -> dict:
    """Every superseded verdict, with its artifacts and immutable references checked on disk."""
    rows, problems = {}, []
    for name, entry in sorted(HISTORY.items()):
        historical, superseding = _artifact(entry["historical"]), _artifact(entry["superseding"])
        row = {"status": entry["status"], "what_happened": entry["what_happened"],
               "history_preserved": entry["history_preserved"],
               "historical": historical, "superseding": superseding}
        for side, found in (("historical", historical), ("superseding", superseding)):
            for key in ("document_exists", "record_exists"):
                if found[key] is False:
                    problems.append(f"{name}: {side} {key.replace('_exists', '')} "
                                    f"{found[key.replace('_exists', '')]} does not exist")
            for key in ("freeze_digest_matches", "record_sha_matches"):
                if found[key] is False:
                    problems.append(f"{name}: {side} {key.replace('_matches', '')} moved")
        rows[name] = row
    live = {"p2x1_freeze_digest_recomputed": _p2x1_digest(),
            "p2x1_freeze_digest_expected": HISTORY["P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A"]["historical"]
            ["freeze_digest"],
            "p2w1_record_sha": hashlib.sha256(dt.RECORD.read_bytes()).hexdigest(),
            "p2w1_record_sha_expected": "1ad221db80ed989b9a5f35a199fdb88962533db05c70a3666705f3ab8437e645"}
    live["p2x1_digest_holds"] = live["p2x1_freeze_digest_recomputed"] == live["p2x1_freeze_digest_expected"]
    live["p2w1_record_untouched"] = live["p2w1_record_sha"] == live["p2w1_record_sha_expected"]
    out = {"rows": rows, "live": live, "problems": sorted(set(problems))}
    out["pass"] = not out["problems"] and live["p2x1_digest_holds"] and live["p2w1_record_untouched"]
    return out


def probe_a17() -> dict:
    """P2S-3 -> P2T-3: both artifacts on disk, both digests where they were, nothing recut."""
    found = supersession()["rows"]["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"]
    out = {"status": found["status"], "historical": found["historical"], "superseding": found["superseding"]}
    out["pass"] = (found["historical"]["document_exists"] and found["historical"]["record_exists"]
                   and found["historical"]["freeze_digest_matches"] and found["historical"]["record_sha_matches"]
                   and found["superseding"]["document_exists"] is True
                   and found["superseding"]["record_exists"] is True
                   and found["superseding"]["freeze_digest_matches"] and found["superseding"]["record_sha_matches"])
    return out


def probe_a18() -> dict:
    """P2X-1 -> P2X-1A: the historical artifacts exist, its freeze digest still recomputes to the frozen value on the
    tree it was frozen against, and its record is byte-identical."""
    found = supersession()
    row = found["rows"]["P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A"]
    out = {"status": row["status"], "historical": row["historical"], "live": found["live"]}
    out["pass"] = (row["historical"]["document_exists"] and row["historical"]["record_exists"]
                   and row["historical"]["freeze_digest_matches"] and row["historical"]["record_sha_matches"]
                   and found["live"]["p2x1_digest_holds"] and found["live"]["p2w1_record_untouched"])
    return out


# 5. P2X-1A-4 and P2X-1A-5: contradictions and debt, both executable ----------------------------------------------------------

#: Each causal statement the closure claims, with the probe that decides it. A row is a contradiction when its probe
#: fails, so the criterion can become false - P2X-1 built this list empty and read the empty list as a pass.
CONTRADICTION_CHECKS = {
    "incompatible_writer_ownership": ("T keeps exactly one clinical owner on every profile, the core's response, and "
                                      "a clinical delta on T is refused before the channel is rebuilt",
                                      ("a1", "a2", "a3")),
    "clamp_defines_physiology": ("no accepted tone minute carries a clamp on T: the boundary is refused before the "
                                "channel reconstruction, the rounding included", ("a8", "a9")),
    "endpoint_accepted_as_interior": ("the exact endpoints of T's supported range fail closed, above and below, at "
                                      "the parameter level and at the minute", ("a4", "a5", "a6", "a7")),
    "negative_burden_as_vasoconstriction": ("a burden below physiologic zero is refused everywhere and is never read "
                                            "as vasoconstriction", ("a10",)),
    "unstable_feedback": ("the delayed loop's derived bound carries the distributive factor, holds for every accepted "
                          "witness against the live slope, and refuses a combination that is not a contraction",
                          ("a13", "a14", "a15")),
    "pressure_driven_vasodilation": ("no writer of the burden reads a same-loop pressure or tone observable, and the "
                                     "scan rejects each bypass the review found", ("a16",)),
    "prior_families_change": ("every committed family trajectory is byte-identical to the predecessor's",
                              ("a21",)),
    "hidden_point_calibration": ("no clinical magnitude is selected: every value this package adds is declared "
                                 "synthetic and every committed profile keeps the reader UNSET", ("a22",)),
}
#: Statements that remain prose, declared as prose instead of being published as the result of a search that never
#: ran. P2X-1 published seven such rows as findings.
DECLARED_NOT_EXECUTABLE = {
    "disease_specific_rule_in_the_common_core": "the tone equation names no family; read from the source by P2W-1 "
                                                "and P2X-1, not re-derived here",
    "same_mechanism_double_counted": "the compensation reads the oxygen deficit and the burden is written by a "
                                     "family: independent factors, multiplied once (P2W-1's reader audit)",
    "impossible_ordering": "the tone answers the previous minute's signal and the burden is written before it is "
                           "read (P2J-2's timing probe)",
    "worse_state_improves_output": "the distributive regime where a rising burden raises output is reachable only "
                                   "with a declared reader, which no migrated family declares: FUTURE_RESEARCH_DEBT "
                                   "(FACULTY DECISION 6)",
}


def contradictions(probes: dict | None = None) -> dict:
    """P2X-1A-4: each row decided by its probes. Break any one of those properties and this becomes false."""
    found = probes if probes is not None else structural_probes()
    rows, inside = {}, []
    for name, (statement, keys) in sorted(CONTRADICTION_CHECKS.items()):
        decided = {key.upper(): bool(found[key.upper()]["pass"]) for key in keys}
        holds = all(decided.values())
        rows[name] = {"statement": statement, "probes": decided, "holds": holds}
        if not holds:
            inside.append(f"{name}: {sorted(k for k, ok in decided.items() if not ok)}")
    out = {"checks": rows, "declared_not_executable": DECLARED_NOT_EXECUTABLE,
           "inside_certified_scope": sorted(inside)}
    out["pass"] = not out["inside_certified_scope"]
    return out


#: The consolidated Phase-2 debt. Each entry names the technical-debt row it comes from, so the classification is
#: checked against the repository's own register instead of being prose. P2X-1's version could not fail.
DEBT = {
    "ACCEPTABLE_PHASE2_DEBT": {
        "STEADY_STATE_W_ARRIVAL_TENSION": "TD-124",
        "OPIOID_HR_RESIDUAL": "TD-124",
        "COLLAPSE_THRESHOLDS": "TD-109",
        "FIO2_MAGNITUDE": "TD-123",
        "RESPIRATORY_DISTRESS_CALIBRATION": "TD-121",
        "SYSTEMIC_STRESS_CALIBRATION": "TD-125",
        "PRESSURE_TO_TONE": "TD-118",
        "SIDED_PRELOAD_AND_INTERDEPENDENCE": "TD-118",
        "CUMULATIVE_FLOATING_POINT_CANCELLATION": "TD-121",
        "PHYSICAL_PAO2_BOUNDARY": "TD-123",
        "HYPOXAEMIC_FEEDBACK_STABILITY": "TD-117",
        "DISTRIBUTIVE_TONE_MAGNITUDE": "TD-126",
        "TONE_DOMAIN_LIMITS": "TD-127",
    },
    "NEXT_PHASE_INTEGRATION_DEBT": {
        "CONSCIOUSNESS_WIRING": "TD-107",
        "RUNTIME_INTEGRATION": "TD-127",
        "RESIDENT_VISIBLE_BEHAVIOUR": "TD-127",
    },
    "FUTURE_RESEARCH_DEBT": {
        "MALDISTRIBUTION_AND_EXTRACTION": "TD-126",
        "PLASMA_LEAK": "TD-126",
        "UPPER_AIRWAY": "TD-126",
        "DRUG_KINETICS": "TD-126",
        "ADDITIONAL_FAMILY_MIGRATIONS": "TD-126",
    },
}
#: The two closure blockers P2X-1's review demonstrated. Each must be resolved by an executable probe; an unresolved
#: one is a blocker and may not be classified as acceptable debt.
#: Every entry the closure must classify. Dropping one from DEBT is a blocker, not a smaller table.
REQUIRED_DEBT = frozenset(item for items in DEBT.values() for item in items)
CLOSURE_BLOCKERS = {
    "P2X1_R_F1_CONDITIONAL_T_OWNERSHIP": ("a1", "a2", "a3"),
    "P2X1_R_F4_CLAMP_IN_AN_ACCEPTED_MINUTE": ("a4", "a8", "a9"),
}
DEBT_REGISTER = ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md"


def _register_ids() -> set:
    text = DEBT_REGISTER.read_text(encoding="utf-8")
    return {part.split("|")[0].strip() for part in text.split("| TD-")[1:]} | \
           {f"TD-{part.split('|')[0].strip()}" for part in text.split("| TD-")[1:]}


def debt_classification(probes: dict | None = None) -> dict:
    """P2X-1A-5: every entry in exactly one class, every entry traced to a row of the repository's own register, and
    no demonstrated closure blocker classified as nonblocking."""
    found = probes if probes is not None else structural_probes()
    known = _register_ids()
    counts = {name: len(items) for name, items in DEBT.items()}
    seen, duplicated, untraced = {}, [], []
    for class_name, items in DEBT.items():
        for item, source in items.items():
            if item in seen:
                duplicated.append(f"{item}: {seen[item]} and {class_name}")
            seen[item] = class_name
            if source not in known:
                untraced.append(f"{item}: {source} is not a row of {DEBT_REGISTER.name}")
    blockers = [f"{item}: required by the closure and classified nowhere"
                for item in sorted(REQUIRED_DEBT - set(seen))]
    for name, keys in sorted(CLOSURE_BLOCKERS.items()):
        resolved = all(bool(found[key.upper()]["pass"]) for key in keys)
        if not resolved:
            blockers.append(f"{name}: unresolved, so it is a blocker and not acceptable debt")
    out = {"classes": {name: dict(sorted(items.items())) for name, items in sorted(DEBT.items())},
           "counts": counts, "classes_are_disjoint": not duplicated, "duplicated": sorted(duplicated),
           "every_entry_traced": not untraced, "untraced": sorted(untraced),
           "every_required_entry_classified": not REQUIRED_DEBT - set(seen),
           "required": sorted(REQUIRED_DEBT),
           "closure_blockers_resolved": {name: all(bool(found[key.upper()]["pass"]) for key in keys)
                                         for name, keys in sorted(CLOSURE_BLOCKERS.items())},
           "unset_is_not_a_blocker": "an UNSET magnitude leaves its term inert, which is the design",
           "blockers": sorted(blockers)}
    out["pass"] = (not out["blockers"] and out["classes_are_disjoint"] and out["every_entry_traced"]
                   and out["every_required_entry_classified"])
    return out


# 6. Probes A19-A22 ----------------------------------------------------------------------------------------------------------

def probe_a19() -> dict:
    """The reversion criterion is read, not merely computed: with a protected predecessor source mutated, the
    readiness rule fails. Run here, inside the record, not only in a test."""
    intact = upstream_unchanged()
    patch = x1._Patcher()
    try:
        patch.setattr(sys.modules[__name__], "_live",
                      lambda relative: _live_text(relative) + "\n# mutated predecessor\n")
        mutated = upstream_unchanged()
        verdict = _verdict_from(mutated, True)
    finally:
        patch.restore()
    out = {"intact": {"proofs": intact["proofs"], "pass": intact["pass"]},
           "mutated": {"proofs": mutated["proofs"], "pass": mutated["pass"]},
           "readiness_with_the_mutation": verdict["verdict"], "blocker": verdict["blocker"],
           "criterion_reads_it": verdict["verdict"].startswith(NOT_READY) and verdict["blocker"] is not None
           and "upstream" in verdict["blocker"]}
    out["pass"] = intact["pass"] and not mutated["pass"] and out["criterion_reads_it"] \
        and upstream_unchanged()["pass"]
    return out


def probe_a20() -> dict:
    """A known debt removed or misclassified makes the readiness rule fail."""
    patch = x1._Patcher()
    module = sys.modules[__name__]
    removed = {name: dict(items) for name, items in DEBT.items()}
    removed["ACCEPTABLE_PHASE2_DEBT"].pop("PRESSURE_TO_TONE")
    misclassified = {name: dict(items) for name, items in DEBT.items()}
    misclassified["FUTURE_RESEARCH_DEBT"]["PRESSURE_TO_TONE"] = "TD-118"
    untraced = {name: dict(items) for name, items in DEBT.items()}
    untraced["ACCEPTABLE_PHASE2_DEBT"]["PRESSURE_TO_TONE"] = "TD-999"
    rows = {}
    # Stubs for the blocker probes: A20 is about the debt table's own falsifiability, and resolving the blockers is
    # A1-A9's job, decided there.
    probes = {key.upper(): {"pass": True} for keys in CLOSURE_BLOCKERS.values() for key in keys}
    for name, table in (("removed", removed), ("misclassified_twice", misclassified), ("untraced", untraced)):
        try:
            patch.setattr(module, "DEBT", table)
            found = debt_classification(probes)
            rows[name] = {"pass": found["pass"], "counts": found["counts"],
                          "duplicated": found["duplicated"], "untraced": found["untraced"]}
        finally:
            patch.restore()
    out = {"mutations": rows, "intact": debt_classification(probes)["pass"],
           "every_mutation_fails": not any(row["pass"] for row in rows.values())}
    out["pass"] = out["intact"] and out["every_mutation_fails"]
    return out


def probe_a21() -> dict:
    """Every committed family keeps its default trajectory exactly, by digest, against the predecessor's record."""
    found = x1.probe_x12()
    expected = (_json_at("docs/revision/P2X1_tone_domain.json") or {}).get("probes", {}).get("X12", {})
    digests = expected.get("course_digests", {})
    same = {name: found["course_digests"].get(name) == digest for name, digest in sorted(digests.items())}
    out = {"courses": sorted(found["courses"]), "digests_match_the_predecessor": same,
           "no_refusal_in_any_committed_course": found["no_refusal_in_any_committed_course"],
           "committed_profiles_unset": found["committed_profiles_unset"],
           "compared_against": "docs/revision/P2X1_tone_domain.json: X12"}
    out["pass"] = bool(same) and all(same.values()) and found["no_refusal_in_any_committed_course"] \
        and all(found["committed_profiles_unset"].values())
    return out


#: The shape of the state at P2X-1, pinned: this package adds no field to any of them, and a field added anywhere
#: makes A22 fail.
FIELDS_AT_P2X1 = {"CoreProfile": 70, "AuxiliaryState": 10, "Anchors": 33}
#: The calibration registry at P2X-1: no entry is added, so no magnitude enters the harness.
CALIBRATION_ENTRIES_AT_P2X1 = 58


def probe_a22() -> dict:
    """No clinical magnitude: no new state, no new profile field, no new calibration entry, every value this package
    adds declared synthetic, and the distributive gain still UNSET in every committed profile."""
    from dataclasses import fields
    from . import calibration
    live = {name: len(fields(getattr(dv, name))) for name in FIELDS_AT_P2X1}
    values = {"TONE_GAIN": TONE_GAIN, "ENDPOINT_BURDEN": ENDPOINT_BURDEN, "INSIDE_BURDEN": INSIDE_BURDEN,
              "COURSE_BURDEN": COURSE_BURDEN, "SEVERE_BURDEN": SEVERE_BURDEN,
              "WITNESS_READERS": [list(pair) for pair in WITNESS_READERS],
              "P2J2_ENDPOINT_GAIN": P2J2_ENDPOINT_GAIN}
    out = {"declared_synthetic": "SYNTHETIC_ONLY probe values" in inspect.getsource(sys.modules[__name__]),
           "probe_values": values,
           "state_shape": live, "state_shape_at_p2x1": dict(FIELDS_AT_P2X1),
           "no_field_added": live == FIELDS_AT_P2X1,
           "calibration_entries": len(calibration.REGISTRY),
           "no_calibration_entry_added": len(calibration.REGISTRY) == CALIBRATION_ENTRIES_AT_P2X1,
           "committed_readers_unset": {name: profile.vasodilatory_burden_to_tone_gain is None
                                       for name, (_, profile) in sorted(dt.committed_pairs().items())}}
    out["pass"] = (out["declared_synthetic"] and out["no_field_added"] and out["no_calibration_entry_added"]
                   and all(out["committed_readers_unset"].values()))
    return out


PROBES = {f"A{index}": globals()[f"probe_a{index}"] for index in range(1, 23)}


def structural_probes() -> dict:
    return {name: probe() for name, probe in PROBES.items()}


# 7. The P2X-1 tree: the predecessor reads the files it left, and every closed listing leaves this package out -------------

P2X1_HEAD = 'e0e520d'

#: P2X-1A's declared replacements, live -> the P2X-1 file at e0e520d.
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py",\n'
                                     '                        "clinical_core/distributive_tone.py",\n'
                                     '                        "clinical_core/distributive_tone_report.py",\n'
                                     '                        "clinical_core/tone_domain.py", '
                                     '"clinical_core/tone_domain_report.py",\n'
                                     '                        "clinical_core/closure_guard.py", '
                                     '"clinical_core/closure_guard_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def pack_sources() -> dict[str, str]:\n',
                                     '                        "clinical_core/systemic_stress.py", '
                                     '"clinical_core/systemic_stress_report.py",\n'
                                     '                        "clinical_core/distributive_tone.py",\n'
                                     '                        "clinical_core/distributive_tone_report.py",\n'
                                     '                        "clinical_core/tone_domain.py", '
                                     '"clinical_core/tone_domain_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def pack_sources() -> dict[str, str]:\n'),),
 'clinical_core/integration.py': (('            "p2j2_slope_bound": gain * sensitivity}\n'
                                   '\n'
                                   '\n'
                                   'def _tone_ownership(deltas: Sequence[ChannelDelta], minute: int) -> None:\n'
                                   '    """P2X-1A: T has exactly one owner in the certified Phase-2 architecture, '
                                   "the core's vascular-tone response.\n"
                                   '\n'
                                   '    This refusal lived inside ``_vascular_tone``, which ``step`` calls only when '
                                   'the core has a tone response to\n'
                                   '    compute (a compensatory gain above 0, or a declared vasodilatory reader). '
                                   'With both off - the committed GI\n'
                                   '    profile - a foreign writer of T reached the channel and its guard, a safety '
                                   'bound, shaped the value instead.\n'
                                   '    Ownership is a statement about who may write the channel, not about whether '
                                   'the response runs, so it is checked\n'
                                   '    here on every minute of every profile, before the channel is reconstructed\n'
                                   '    (T_CHANNEL_SINGLE_OWNER_INVARIANT_UNCONDITIONAL, FACULTY DECISION 1).\n'
                                   '\n'
                                   "    Who counts as a writer is the repository's own classification, not a new "
                                   'one: a scripted synthetic probe is\n'
                                   '    outside the owner for T exactly as it is for V and Hb (``_check_owned``, '
                                   "P2I-2T), and P2J-1's published TONE_RULE\n"
                                   '    already reads "a writer outside a synthetic probe, a test or a bound is a '
                                   'clinical writer", naming\n'
                                   '    ``bands.py``, ``hemodynamic_probes.py`` and ``pressure_tone.py`` as the '
                                   'non-clinical ones. So every clinical\n'
                                   '    source - a disease module, a treatment, an intervention, a case - is refused '
                                   'here on every profile, which is the\n'
                                   '    hole the P2X-1 review demonstrated, while the declared synthetic probes keep '
                                   'driving T as they did, in no case\n'
                                   '    and no family trajectory.\n'
                                   '    """\n'
                                   '    clinical = sorted({delta.source.key for delta in deltas if delta.channel is '
                                   'Channel.T\n'
                                   '                       and delta.source.kind is not SourceKind.SCRIPTED_EVENT})\n'
                                   '    if clinical:\n'
                                   '        raise CoreInvariantError(f"minute {minute}: {clinical} write T, whose '
                                   'only clinical owner is the core\'s "\n'
                                   '                                 "vascular-tone response; how a family, a '
                                   'disease module or a drug would compose "\n'
                                   '                                 "with it is not decided, on any profile (P2J-2, '
                                   'unconditional since P2X-1A)")\n'
                                   '\n'
                                   '\n'
                                   'def _vascular_tone(state: CoreState, deltas: Sequence[ChannelDelta], anchors: '
                                   'Anchors, profile: CoreProfile,\n'
                                   '                   minute: int) -> ChannelDelta:\n'
                                   '    """P2J-2: T moves to the tone the state at the start of the minute calls for '
                                   '(``tone_target``).\n',
                                   '            "p2j2_slope_bound": gain * sensitivity}\n'
                                   '\n'
                                   '\n'
                                   'def _vascular_tone(state: CoreState, deltas: Sequence[ChannelDelta], anchors: '
                                   'Anchors, profile: CoreProfile,\n'
                                   '                   minute: int) -> ChannelDelta:\n'
                                   '    """P2J-2: T moves to the tone the state at the start of the minute calls for '
                                   '(``tone_target``).\n'),
                                  ('    algebraic loop, and no solver is used. The minute after arrival keeps T at 1 '
                                   "(arrival is the target's fixed point).\n"
                                   '    Fails closed where nothing is decided: another source writing T in the same '
                                   'minute (how a drug or a disease module\n'
                                   '    would compose with the response is not decided), or a gain whose largest '
                                   'target, 1 + g at no delivery, is outside\n'
                                   "    T's guard (so the guard never shapes the response). That refusal covers "
                                   'every source while the response runs;\n'
                                   '    ``_tone_ownership``, which ``step`` runs whether or not this response does, '
                                   'covers every clinical source always.\n'
                                   '\n'
                                   '    P2X-1 closes that last claim over the whole declared domain '
                                   '(``tone_domain``). The P2J-2 check reads the\n'
                                   '    compensation alone, so with a distributive reader declared it saw neither '
                                   'the recovery factor 1 + k b0 above nor a\n'
                                   "    severe burden below, and the channel's guard - a safety bound, never "
                                   'physiology - decided the response instead.\n'
                                   '    Now, where that reader is declared, a parameter domain whose largest '
                                   "reachable target reaches or leaves T's\n"
                                   '    supported range, or whose derived loop bound is not a contraction, is '
                                   'refused before execution.\n'
                                   '\n'
                                   '    P2X-1A makes the per-minute admissibility STRICT and checks the value the '
                                   'channel will actually hold. The supported\n'
                                   '    domain is the open interval: the endpoints are unresolved boundaries, not '
                                   'accepted interior physiology, so a target\n'
                                   '    at or outside either end fails closed - and so does one whose reconstruction '
                                   'does, which is what left a 2.8e-17\n'
                                   '    clamp inside an accepted minute. No epsilon, margin, tolerance or '
                                   'alternative floor is introduced\n'
                                   '    (TONE_DOMAIN_ENDPOINTS = UNRESOLVED_BOUNDARY and '
                                   'ACCEPTED_TONE_MINUTE_HAS_ZERO_CLAMP, FACULTY DECISIONS 2 and 3).\n'
                                   '    The guard stays as the last safety layer for every other channel '
                                   '(TONE_CLAMP_AS_PHYSIOLOGY = REJECTED).\n'
                                   '    """\n'
                                   '    lower, upper = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]\n'
                                   '    if 1.0 + profile.deficit_to_tone_gain > upper:\n'
                                   '        raise CoreInvariantError(f"the tone response\'s largest target 1 + '
                                   '{profile.deficit_to_tone_gain!r} is above "\n'
                                   '                                 f"T\'s guard {upper!r}")\n'
                                   '    domain = tone_domain(anchors, profile)\n'
                                   '    if domain["largest_target"] >= upper:\n'
                                   '        # P2X-1A: the derived largest reachable target, strictly inside, for '
                                   'every profile. P2X-1 asked this only\n'
                                   '        # where the distributive reader is declared; the supported domain is '
                                   'interior whatever the reader\n'
                                   '        # (FACULTY DECISION 2), and the derived value already carries the '
                                   'arrival normalization and the recovery\n'
                                   "        # factor, so this is both broader than P2X-1's check and exact where "
                                   "P2J-2's 1 + g is conservative.\n"
                                   '        raise CoreInvariantError(\n'
                                   '            f"the tone target\'s largest reachable value '
                                   '{domain[\'largest_target\']!r} (the compensation\'s "\n'
                                   '            f"{domain[\'compensation_max\']!r} times the distributive recovery '
                                   '{domain[\'recovery_max\']!r}) reaches "\n'
                                   '            f"or passes T\'s guard {upper!r}: the guard would shape the response '
                                   '(P2X-1, strict and unconditional "\n'
                                   '            "since P2X-1A)")\n'
                                   '    if domain["distributive_reader"]:\n'
                                   '        if domain["loop_slope_bound"] >= 1.0:\n'
                                   '            raise CoreInvariantError(\n'
                                   '                f"the tone loop\'s derived bound with the distributive factor, '
                                   '{domain[\'loop_slope_bound\']!r}, is not "\n',
                                   '    algebraic loop, and no solver is used. The minute after arrival keeps T at 1 '
                                   "(arrival is the target's fixed point).\n"
                                   '    Fails closed where nothing is decided: another source writing T in the same '
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
                                   '{domain[\'loop_slope_bound\']!r}, is not "\n'),
                                  ('        raise CoreInvariantError(f"minute {minute}: {writers} write T while the '
                                   'vascular-tone response is on; how they "\n'
                                   '                                 "compose is not decided (P2J-2)")\n'
                                   '    target = tone_target(state, anchors, profile)\n'
                                   "    # T's single owner (``_tone_ownership``) makes this the whole channel: "
                                   'exactly what ``step`` rebuilds for T, with\n'
                                   '    # the same arithmetic (``math.fsum`` over one amount is that amount), so an '
                                   'accepted minute cannot reach a clamp.\n'
                                   '    amount = target - state.T\n'
                                   '    reconstructed = state.T + amount\n'
                                   '    if not lower < target < upper or not lower < reconstructed < upper:\n'
                                   '        raise UnresolvedBoundary(f"minute {minute}: the tone target {target!r} '
                                   'is not inside T\'s supported range "\n'
                                   '                                 f"{(lower, upper)!r} (the channel rebuilds it '
                                   'as {reconstructed!r}); the endpoints "\n'
                                   '                                 "are unresolved boundaries, not accepted '
                                   'interior physiology, and the channel\'s "\n'
                                   '                                 "guard is a safety bound (TONE_DOMAIN_ENDPOINTS '
                                   '= UNRESOLVED_BOUNDARY, P2X-1A)")\n'
                                   '    return ChannelDelta(Channel.T, amount, VASCULAR_TONE, minute,\n'
                                   '                        "the tone the acute shock signal at the start of the '
                                   'minute calls for")\n'
                                   '\n'
                                   '\n',
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
                                   '\n'),
                                  ('        events.append(CoreEvent("terminal_collapse", COLLAPSE, minute, '
                                   '"critical", "physiological_collapse",\n'
                                   '                                "not assessed", f"terminal collapse from '
                                   'sustained critically low output: "\n'
                                   '                                                f"{target.code.value}"))\n'
                                   '    _tone_ownership(deltas, minute)\n'
                                   '    if profile.deficit_to_tone_gain > 0.0 or '
                                   'profile.vasodilatory_burden_to_tone_gain is not None:\n'
                                   '        # P2W-1: the tone response also runs for a declared vasodilatory reader, '
                                   "so a family's burden always reaches T\n"
                                   '        # where its reader exists, even with the compensatory gain at 0 (with '
                                   "the reader UNSET this is P2J-2's\n",
                                   '        events.append(CoreEvent("terminal_collapse", COLLAPSE, minute, '
                                   '"critical", "physiological_collapse",\n'
                                   '                                "not assessed", f"terminal collapse from '
                                   'sustained critically low output: "\n'
                                   '                                                f"{target.code.value}"))\n'
                                   '    if profile.deficit_to_tone_gain > 0.0 or '
                                   'profile.vasodilatory_burden_to_tone_gain is not None:\n'
                                   '        # P2W-1: the tone response also runs for a declared vasodilatory reader, '
                                   "so a family's burden always reaches T\n"
                                   '        # where its reader exists, even with the compensatory gain at 0 (with '
                                   "the reader UNSET this is P2J-2's\n")),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py",\n'
                                     '                      "clinical_core/distributive_tone_report.py",\n'
                                     '                      "clinical_core/tone_domain_report.py",\n'
                                     '                      "clinical_core/closure_guard_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def slice_sources() -> dict[str, str]:\n',
                                     '                      "clinical_core/opioid_migration_report.py",\n'
                                     '                      "clinical_core/systemic_stress_report.py",\n'
                                     '                      "clinical_core/distributive_tone_report.py",\n'
                                     '                      "clinical_core/tone_domain_report.py")\n'
                                     '\n'
                                     '\n'
                                     'def slice_sources() -> dict[str, str]:\n'),),
 'clinical_core/provenance.py': (('      allowed inputs are its own disease-process state, time, a treatment, and '
                                  'authored family mechanisms that do not\n'
                                  '      close that loop. The contract is structural, not enforced at runtime: the '
                                  'repository checks it by scanning every\n'
                                  '      module that builds a VasodilationChange, as it checks the other writer '
                                  'ownerships.\n'
                                  '\n'
                                  '    P2X-1A makes that scan materially enforceable (its P2X-1 version was '
                                  'evadable). It now follows the construction\n'
                                  '    through an alias or a qualified name (``provenance.VasodilationChange``), '
                                  "through the module's own helper\n"
                                  '    functions that feed the amount, and through positional arguments; it covers '
                                  'every observable of the same loop the\n'
                                  '    core derives, not only the pressures - the MAP, pressure_rel, SBP, DBP, T, '
                                  'the relative output and delivery, the\n'
                                  "    capillary refill and the sympathetic drive; and it reads the repository's own "
                                  "code, not only this package's\n"
                                  '    modules. What it does not do is decide the question in general: it names the '
                                  'patterns a writer must not use.\n'
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n',
                                  '      allowed inputs are its own disease-process state, time, a treatment, and '
                                  'authored family mechanisms that do not\n'
                                  '      close that loop. The contract is structural, not enforced at runtime: the '
                                  'repository checks it by scanning every\n'
                                  '      module that builds a VasodilationChange, as it checks the other writer '
                                  'ownerships.\n'
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n'),)}

CORE_AT_P2X1 = {'clinical_core/decision_pack.py': '19a00c71916aea1498e4fd0dfd5ea300a060e47a63ef45fe92def098419efdb0',
 'clinical_core/integration.py': 'eba54ff3ccc59e11aafbad084470e3db5a4180853d1ed8e4e8ecfcdc0637ed30',
 'clinical_core/lactate_slice.py': '0ea03272ba79c063f4af53c6420e78f1e381db44034c9f5dd1f60b97034bf36c',
 'clinical_core/provenance.py': '5102644f9f8beda5dfefe2d9e363256135fc21bf2a02200eeffd26a2433471e5'}

COMMON_AT_P2X1 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
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
 'clinical_core/tone_domain.py': '833d355f3d30ac494045c819693d00a3dc9de858f87a24f568dfe3afeee5463b',
 'clinical_core/tone_domain_report.py': '733de089369a3395c63a17048d42c88125c85e508a8609363ed0c16b12309ac5',
 'clinical_core/vascular_tone.py': '8314c34accd082511b8e5cbe73da90c054fdbd2a0b8a6f3a56ab0aa0c12f7cf5',
 'clinical_core/vascular_tone_report.py': '19db9e1005755fbb229f1e739c3c1607f97e376df784c929f63c0cb97440ba4a',
 'clinical_core/ventilation.py': '260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9',
 'clinical_core/ventilation_filter.py': '9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9',
 'clinical_core/ventilation_filter_report.py': '6d5789040d650c2b7241d18399c6fe2038fd91eb1ca58e5f7c93e29f63a39c49',
 'clinical_core/ventilation_surface.py': 'd361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825',
 'clinical_core/ventilation_surface_report.py': '64de449f56f34cc77ec3a6ca663ee2389ea32f3c3373a289237e69f212d16a3c'}


P2X1_FREEZE_DIGEST = "3afa71b2dfa0f47eb1a00e8987c79cd18b246788e366ac07fe58eacc21815a0e"


def _live_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _live(relative: str) -> str:
    """Indirect on purpose: a probe replaces this to mutate a protected predecessor source (A19)."""
    return _live_text(relative)


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2X1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2X1.items()}


def p2x1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2X-1 file plus P2X-1A's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2x1_bytes(relative: str) -> bytes:
    return p2x1_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def p2x1_sources(sources: dict) -> dict:
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2X1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


#: The closed packages whose own hash list of unchanged files still reads the live bytes: P2X-1's.
CLOSED_COMMON = ("tone_domain",)
PATH_READERS = x1.PATH_READERS
_NEW_FILES = OWN + (REPORT,)
_FREEZE_SOURCES = bf.freeze_sources


def _closed_common_untouched(module):
    name = next(n for n in vars(module) if n.startswith("COMMON_AT_"))
    expected = getattr(module, name)

    def untouched() -> dict:
        return {relative: hashlib.sha256(p2x1_bytes(relative)).hexdigest() == sha
                for relative, sha in expected.items()}

    return untouched


class _InspectView:
    """``inspect`` for a closed package reading the live core by source: the P2X-1 text of the files P2X-1A changed,
    the real thing for everything else. P2X-1's guards read ``inspect.getsource`` of the integration module, so
    without this its frozen record could not reproduce on the tree it was frozen against."""

    _BY_MODULE = {f"clinical_core/{Path(relative).name}": relative for relative in REVERSAL}

    def getsource(self, obj):
        name = getattr(obj, "__name__", "")
        if isinstance(obj, types.ModuleType):
            relative = f"{name.replace('.', '/')}.py"
            if relative in REVERSAL:
                return p2x1_text(relative)
        return inspect.getsource(obj)

    def __getattr__(self, name):
        return getattr(inspect, name)


def _old_only(paths) -> list:
    return [p for p in paths if p.relative_to(ROOT).as_posix() not in _NEW_FILES]


class _TreeFile:
    """One of P2X-1A's changed files as P2X-1 left it, for a closed audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2x1_text(self.relative)

    def read_bytes(self):
        return p2x1_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


class _TreeDir:
    """A closed package's ``ROOT`` or ``CORE_DIR``: the P2X-1 text of P2X-1A's changed files, the live path of
    anything else, and its listings without P2X-1A's new files."""

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
    kind = _TreeDir if kind is None else kind
    while value is not None and not isinstance(value, Path):
        if isinstance(value, kind):
            return True
        value = getattr(value, "path", None)
    return False


def _rebuilt(value):
    if isinstance(value, Path):
        return _TreeDir(value)
    inner = getattr(value, "path", None)
    rebuilt = None if inner is None else _rebuilt(inner)
    return None if rebuilt is None else type(value)(rebuilt)


def _imported_closed_modules() -> list:
    return [__import__(f"clinical_core.{name}", fromlist=["ROOT"]) for name in PATH_READERS] + [dt, x1]


def chain(patch) -> None:
    """For the closed packages' test fixtures: P2X-1's view reads the P2X-1 files (proven), by path and by source, and
    every closed listing of clinical_core leaves P2X-1A's new files out. P2X-1A adds no state and no accepted
    reading: only refusals."""
    patch.setattr(x1, "_live", p2x1_text)
    patch.setattr(x1, "_FREEZE_SOURCES", lambda: p2x1_sources(_FREEZE_SOURCES()))
    patch.setattr(x1, "inspect", _InspectView())
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


_X1_TREE = x1.tree


def _x1_tree(patch) -> None:
    """P2X-1's own whole-tree view, nested inside P2X-1A's."""
    _X1_TREE(patch)
    for module in _imported_closed_modules():
        if module is x1:
            continue
        for attribute in ("ROOT", "CORE_DIR", "CORE", "CANDIDATE_SOURCE"):
            value = getattr(module, attribute, None)
            if _carries(value) and not _carries(value, x1._TreeDir):
                patch.setattr(module, attribute, x1._TreeDir(value))


def tree(patch) -> None:
    """The whole P2X-1 tree, for P2X-1's own analysis and tests."""
    chain(patch)
    patch.setattr(x1, "tree", _x1_tree)
    patch.setattr(bf, "freeze_sources", lambda: p2x1_sources(_FREEZE_SOURCES()))


class _p2x1_view:
    """The whole P2X-1 tree while its own analysis runs, done locally because ``run`` has no monkeypatch."""

    def __enter__(self):
        self.patch = x1._Patcher()
        tree(self.patch)
        return self

    def __exit__(self, *exc):
        self.patch.restore()
        return False


def _p2x1_digest() -> str:
    """P2X-1's own freeze digest, computed on the tree it was frozen against."""
    with _p2x1_view():
        return x1.freeze_digest()


def non_regression() -> dict:
    """The predecessor reproduces on its own tree, and its record is untouched."""
    with _p2x1_view():
        found = x1.run()
        record = json.loads(x1.RECORD.read_text(encoding="utf-8"))
        reproduced = record == json.loads(json.dumps(found, sort_keys=True, default=str))
    out = {"p2x1_record_reproduced_on_its_tree": reproduced,
           "p2x1_record_untouched": hashlib.sha256(x1.RECORD.read_bytes()).hexdigest() ==
           HISTORY["P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A"]["historical"]["record_sha"],
           "p2x1_frozen_verdict": record.get("readiness", {}).get("verdict"),
           "tuples": {name: all(value in _tuple_values(name) for value in values)
                      for name, values in sorted(TUPLES_ADDED.items())}}
    out["pass"] = (out["p2x1_record_reproduced_on_its_tree"] and out["p2x1_record_untouched"]
                   and all(out["tuples"].values()))
    return out


def _tuple_values(name: str):
    from . import decision_pack, lactate_slice
    return {"DOWNSTREAM_REPORTS": lactate_slice.DOWNSTREAM_REPORTS,
            "PACK_DIGEST_EXCLUDED": decision_pack.PACK_DIGEST_EXCLUDED}[name]


def upstream_unchanged() -> dict:
    out = {"proofs": proofs(), "common_untouched": common_untouched(),
           "p2x1_freeze_digest": _p2x1_digest() == P2X1_FREEZE_DIGEST}
    out["pass"] = all(out["proofs"].values()) and all(out["common_untouched"].values()) and out["p2x1_freeze_digest"]
    return out


# 8. Readiness: eleven criteria, each executable and falsifiable --------------------------------------------------------------

READINESS_CRITERIA = (
    ("1. the T single-owner invariant is unconditional: every clinical writer of T is refused on every profile, "
     "before the channel is rebuilt, whether or not the core has a response to compute",
     ("guards", "A1", "A2", "A3")),
    ("2. the supported tone domain is the open interval: both endpoints fail closed, at the parameter level and at "
     "the minute, with no epsilon, margin or tolerance", ("guards", "A4", "A5", "A6", "A7")),
    ("3. no accepted tone minute carries a clamp on T, the floating reconstruction included", ("A8", "A9")),
    ("4. the contraction guard carries the distributive factor and holds against the live slope with B != 1, and a "
     "combination that is not a contraction is refused", ("A13", "A14", "A15")),
    ("5. the pressure-driven vasodilation contract is enforced by a scan that rejects each bypass the P2X-1 review "
     "found", ("writer_contract", "A16")),
    ("6. the predecessor and reversion integrity holds, and the readiness rule reads it", ("upstream", "A19")),
    ("7. the contradictions check is executable: each row is decided by its probes and can become false",
     ("contradictions",)),
    ("8. the debt classification is executable: disjoint classes, every entry traced to the register, no demonstrated "
     "blocker classified as acceptable, and a mutation makes it fail", ("debt", "A20")),
    ("9. the supersession check verifies the repository's own artifacts and immutable references",
     ("supersession", "A17", "A18")),
    ("10. every prior migrated family keeps its default trajectory exactly", ("non_regression", "A21")),
    ("11. no new clinical magnitude is selected", ("A22",)),
)


def _evidence(found: dict) -> dict:
    """Every leaf the criteria read, by name. Each is the ``pass`` of something that runs."""
    probes = found.get("probes", {})
    out = {"guards": found.get("guards", {}).get("pass"),
           "writer_contract": found.get("writer_contract", {}).get("pass"),
           "contradictions": found.get("contradictions", {}).get("pass"),
           "debt": found.get("debt_classification", {}).get("pass"),
           "supersession": found.get("supersession", {}).get("pass"),
           "non_regression": found.get("non_regression", {}).get("pass"),
           "upstream": found.get("upstream_unchanged", {}).get("pass")}
    out.update({name: row.get("pass") for name, row in probes.items()})
    return out


def readiness(found: dict) -> dict:
    """P2X-1A's verdict. Every criterion reads an executable result; none is a constant."""
    evidence = _evidence(found)
    rows, blockers = [], []
    for statement, keys in READINESS_CRITERIA:
        missing = [key for key in keys if evidence.get(key) is None]
        holds = not missing and all(evidence[key] is True for key in keys)
        failed = sorted(key for key in keys if evidence.get(key) is not True)
        rows.append({"criterion": statement, "reads": list(keys), "holds": holds, "failed": failed})
        if not holds:
            blockers.append(f"{statement.split('.')[0]}: {failed}")
    verdict = READY if not blockers else f"{NOT_READY} - {'; '.join(blockers)}"
    return {"criteria": rows, "evidence": evidence, "blocker": blockers[0] if blockers else None,
            "verdict": READY if not blockers else verdict}


def _verdict_from(upstream: dict, everything_else_holds: bool = True) -> dict:
    """The verdict with one piece of evidence replaced: how a probe shows a criterion really reads its result."""
    stub = {"pass": everything_else_holds}
    found = {"guards": stub, "writer_contract": stub, "contradictions": stub, "debt_classification": stub,
             "supersession": stub, "non_regression": stub, "upstream_unchanged": upstream,
             "probes": {f"A{index}": stub for index in range(1, 23)}}
    return readiness(found)


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "decisions": DECISIONS, "interpretation": INTERPRETATION,
            "own": list(OWN), "report": REPORT, "record": RECORD.relative_to(ROOT).as_posix(),
            "document": DOCUMENT.relative_to(ROOT).as_posix(), "core_files": list(CORE_FILES),
            "predecessor": {"revision": x1.REVISION, "head": P2X1_HEAD, "freeze_digest": P2X1_FREEZE_DIGEST},
            "criteria": [statement for statement, _ in READINESS_CRITERIA],
            "probes": {name: (probe.__doc__ or "").strip().split("\n")[0] for name, probe in sorted(PROBES.items())},
            "forbidden_reads": list(FORBIDDEN_READS), "debt_register": DEBT_REGISTER.relative_to(ROOT).as_posix()}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2x1": hashlib.sha256(x1.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    probes = structural_probes()
    found = {"revision": REVISION, "freeze_digest": freeze_digest(), "design": design(), "guards": guards(),
             "writer_contract": writer_contract(), "probes": probes, "supersession": supersession(),
             "debt_classification": debt_classification(probes), "contradictions": contradictions(probes),
             "non_regression": non_regression(), "upstream_unchanged": upstream_unchanged(),
             "proof": {"proofs": proofs(), "common_untouched": common_untouched(),
                       "p2x1_record_sha": hashlib.sha256(x1.RECORD.read_bytes()).hexdigest()}}
    found["readiness"] = readiness(found)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-record", action="store_true", help=f"rewrite {RECORD.name}")
    args = parser.parse_args()
    found = run()
    print(json.dumps(found["readiness"], indent=1, ensure_ascii=False, default=str))
    if args.write_record:
        RECORD.write_text(json.dumps(found, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n",
                          encoding="utf-8")
        print(f"wrote {RECORD.relative_to(ROOT)}")
    return 0 if found["readiness"]["verdict"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
