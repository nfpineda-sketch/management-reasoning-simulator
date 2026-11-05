"""P2T-1A: the respiratory distress semantic / numerical closure (shadow only; two authorized issues, M1 and L1).

Faculty decisions after P2T-1 (COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_READY, accepted and closed):
- M1, option 1 (DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT): a respiratory distress above 0 read by the
  respiratory reader needs the P2S-2 common respiratory mechanics candidate. With the candidate off, the RR effect would
  move the PaCO2 through the retired P2K-2 arrival PaCO2 anchor, so the core refuses it at arrival, for an evolving
  writer and for any state (``derived.check_distress_respiratory_effect``). The sympathetic reader alone and a distress
  of 0 are accepted. Option 2 is not used: DISTRESS_IN_ANCHOR = REJECTED (no anchor, PaCO2 reference or case PaCO2
  absorbs the distress).
- L1 (numerical precision only): the minute's distress is one math.fsum over the value it starts with and every change;
  a negative sum within the roundoff of those operands (math.ulp(1.0) x the sum of their magnitudes) is 0 exactly;
  anything below is refused as before (``integration.distress_sum``). No clinical epsilon, no physiology threshold.

No other physiology changes. This module freezes the M1 and L1 probes, the audit of the changed functions, the
non-regression (P2T-1's D1-D12 live, P2T-1's record on its own tree) and the proof that every other common file is
P2T-1's, before the one evaluation run. Every gain and distress value here is SYNTHETIC_ONLY; nothing is approved.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import math
from dataclasses import fields, replace
from pathlib import Path

from . import asthma_migration as sm
from . import asthma_reference as sr
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import edema_migration as pe
from . import edema_reference as er
from . import embolism_migration as em
from . import embolism_reference as mr
from . import gas_exchange_architecture as go
from . import integration as ig
from . import respiratory_distress as dm
from . import respiratory_drive as rd
from . import respiratory_mechanics as mc
from .provenance import ProvenanceError
from .state import CoreInvariantError

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "clinical_core"
REVISION = "P2T-1A"
DECIDED = "2026-11-05"
OWN = ("clinical_core/distress_closure.py",)
REPORT = "clinical_core/distress_closure_report.py"
RECORD = ROOT / "docs" / "revision" / "P2T1A_distress_closure.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2T1A_CIERRE_DISTRES.md"
#: The two registry tuples gain this package's entries (proven against P2T-1's files below).
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
CORE_FILES = ("clinical_core/derived.py", "clinical_core/integration.py")
GUARD = "check_distress_respiratory_effect"
SUM = "distress_sum"
M1_CLASS = "DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT"
ANCHOR_CLASS = "DISTRESS_IN_ANCHOR = REJECTED"

DECISIONS = {
    "p2t1": "COMMON_RESPIRATORY_DISTRESS_ARCHITECTURE_READY, accepted and closed; its physiology is not reopened",
    "scope": "M1 and L1 only; no other physiology change; no asthma remigration; systemic stress deferred",
    "m1": "option 1: arrival distress > 0 with the respiratory reader needs the common mechanics candidate; an evolving "
          "distress above 0 read by the respiratory drive likewise; the sympathetic reader alone and distress 0 are "
          f"accepted; default unchanged; {M1_CLASS}",
    "m1_option_2": f"{ANCHOR_CLASS}: the distress is not put in the P2K-2 arrival PaCO2 anchor, no case PaCO2 reference "
                   "is recomputed to absorb it, and patient-specific arrival PaCO2 anchoring is not restored",
    "l1": "numerical precision only: math.fsum plus a tolerance at floating-point roundoff scale (math.ulp(1.0) x the "
          "sum of the operands' magnitudes); a negative within it is 0 exactly, a material negative is refused; no "
          "clinical epsilon",
    "p2t1_record": "not refrozen: P2T-1's record is reproduced on its own tree (the M1 guard and the L1 sum read as "
                   "P2T-1 had them); its edema and PE contrasts are the M1 combination and are refused live",
}

# Synthetic, predeclared values (SYNTHETIC_ONLY, never approved) --------------------------------------------------------------

RESPIRATORY_GAIN = dm.RESPIRATORY_GAIN
SYMPATHETIC_GAIN = dm.SYMPATHETIC_GAIN
PROBE_DISTRESS = dm.PROBE_DISTRESS
ARRIVAL_PACO2_VALUES = (30.0, 60.0)          # two authored arrival PaCO2 values the mechanics-on PaCO2 must ignore
TRIAD = (0.3, -0.1, -0.2)                     # L1-A
#: L1-C: (value the minute starts with, changes) whose binary64 sum is a negative at roundoff scale.
ROUNDOFF_NEGATIVES = ((0.3, (-(0.1 + 0.2),)), (0.7, (-0.1, -0.6)))
#: L1-D: material negatives (relative to the operands), refused as before.
MATERIAL_NEGATIVES = ((0.3, (-0.31,)), (0.0, (-1e-12,)), (0.0, (-1e-300,)), (1.0, (-(1.0 + 4.0 * math.ulp(1.0)),)))
#: L1-E: small legitimate positives, kept as they are.
SMALL_POSITIVES = ((0.0, (1e-12,)), (0.0, (5e-324,)), (0.3, (-0.2999999999,)))
#: L1 scale invariance: every case scaled by these powers of two decides the same (no absolute epsilon).
SCALES = (2.0 ** -40, 1.0, 2.0 ** 40)


def mechanics_off() -> dv.CoreProfile:
    """P2P-2's probe profile: acid-base on (the respiratory reader's prerequisite), mechanics candidate off."""
    return rd.base_profile()


def mechanics_on() -> dv.CoreProfile:
    """P2S-2's probe profile (P2T-1's base profile): the same, mechanics candidate on."""
    return dm.base_profile()


def readers(profile, respiratory=RESPIRATORY_GAIN, sympathetic=SYMPATHETIC_GAIN):
    return dm.readers(profile, respiratory, sympathetic)


def _refused(build) -> bool:
    try:
        build()
    except (CoreInvariantError, ProvenanceError):
        return True
    return False


def _writers(amounts, minute: int) -> tuple:
    """Scripted SYNTHETIC_ONLY writers, one per amount, all in the given minute."""
    return tuple(dm.SyntheticDistress(f"p2t1a-{minute}-{i}", a, start_minute=minute - 1, stop_minute=minute)
                 for i, a in enumerate(amounts))


def _course(start_state, minutes, anchors, profile):
    """Steps a state through the given minutes (each a tuple of amounts); returns the distress after each."""
    state, trail = start_state, []
    for amounts in minutes:
        state, _ = ig.step(state, _writers(amounts, state.minute + 1), anchors, profile)
        trail.append(state.aux.respiratory_distress)
    return state, trail


# P2T-1A-1: the changed functions, read from the code ---------------------------------------------------------------------------

ANCHOR_NAMES = ("arrival_paco2", "paco2_reference_mmhg", "arrival_alveolar_ventilation")


def _function_dumps(text: str) -> dict:
    out = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef):
            out.setdefault(node.name, []).append(ast.dump(node))
    return out


def _callers(text: str, name: str) -> list:
    return sorted({n.name for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)
                   and any(isinstance(c, ast.Call) and getattr(c.func, "id", None) == name for c in ast.walk(n))})


def _changed(relative: str) -> dict:
    old, new = _function_dumps(p2t1_text(relative)), _function_dumps(_live(relative))
    return {"changed": sorted(k for k in old if k in new and old[k] != new[k]),
            "added": sorted(set(new) - set(old)), "removed": sorted(set(old) - set(new))}


def audit() -> dict:
    """The functions P2T-1A changed or added, what the guard and the sum read, and that every PaCO2-anchor reader is
    P2T-1's."""
    live_d, live_i = _live("clinical_core/derived.py"), _live("clinical_core/integration.py")
    guard = mc._functions(live_d)[GUARD]
    total = mc._functions(live_i)[SUM]
    constants = sorted({n.value for n in ast.walk(total) if isinstance(n, ast.Constant)
                        and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    calls = sorted({ast.unparse(n.func) for n in ast.walk(total) if isinstance(n, ast.Call)})
    old_d, new_d = _function_dumps(p2t1_text("clinical_core/derived.py")), _function_dumps(live_d)
    anchor_readers = sorted(k for k, dumps in new_d.items() if any(a in d for d in dumps for a in ANCHOR_NAMES))
    out = {
        "derived": _changed("clinical_core/derived.py"),
        "integration": _changed("clinical_core/integration.py"),
        "guard_callers": {"derived": _callers(live_d, GUARD), "integration": _callers(live_i, GUARD)},
        "guard_reads": sorted(mc._names(guard) & {"distress", "distress_to_respiratory_drive_gain",
                                                  "respiratory_mechanics", "distress_to_sympathetic_gain",
                                                  "mechanics_efficiency", "spo2", "paco2", *ANCHOR_NAMES}),
        "sum_callers": _callers(live_i, SUM),
        "sum_constants": constants,
        "sum_calls": calls,
        "anchor_readers": anchor_readers,
        "anchor_readers_are_p2t1s": all(new_d[k] == old_d.get(k) for k in anchor_readers),
        "guard_reads_no_anchor": not (mc._names(guard) & {*ANCHOR_NAMES, "paco2"}),
    }
    out["pass"] = (out["derived"] == {"changed": ["_composition", "arrival_state"], "added": [GUARD], "removed": []}
                   and out["integration"] == {"changed": ["_check_conservation", "_distress_after"], "added": [SUM],
                                              "removed": []}
                   and out["guard_callers"] == {"derived": ["_composition", "arrival_state"],
                                                "integration": ["_distress_after"]}
                   and out["guard_reads"] == ["distress", "distress_to_respiratory_drive_gain", "respiratory_mechanics"]
                   and out["sum_callers"] == ["_check_conservation", "_distress_after"]
                   and set(out["sum_constants"]) <= {0.0, 1.0}
                   and out["sum_calls"] == ["abs", "math.fsum", "math.ulp"]
                   and out["anchor_readers_are_p2t1s"] and out["guard_reads_no_anchor"])
    return out


# P2T-1A-2: M1 (DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT) ------------------------------------------------------

def _committed_m1_cases() -> dict:
    """The committed mappings P2T-1's contrasts read with mechanics off (the M1 combination), and asthma's (on)."""
    return {"pulmonary_edema_58m": (er.anchors(), pe.profile()), "pulmonary_embolism_61m": (mr.anchors(), em.profile()),
            "pulmonary_embolism_33f": (mr.anchors(mr.SECONDARY), em.profile()), "asthma_49m": (sr.anchors(), sm.profile())}


def m1() -> dict:
    anchors = dm.PROBE_ANCHORS
    some = dm.probe_anchors(arrival_respiratory_distress=PROBE_DISTRESS)
    off, on = mechanics_off(), mechanics_on()
    zero_state = dv.arrival_state(anchors, readers(off))
    forced = zero_state.evolve(aux=replace(zero_state.aux, respiratory_distress=PROBE_DISTRESS))
    refused = {
        "arrival_both_readers": _refused(lambda: dv.arrival_state(some, readers(off))),
        "arrival_respiratory_reader_only": _refused(lambda: dv.arrival_state(some, readers(off, sympathetic=None))),
        "evolving_writer": _refused(lambda: ig.step(zero_state, _writers((1.0,), 1), anchors, readers(off))),
        "any_state_composition": _refused(lambda: dv.derive(forced, anchors, readers(off))),
        "arrival_drive_composition": _refused(lambda: dv.arrival_drive_composition(some, readers(off))),
    }
    committed = {}
    for name, (a, p) in _committed_m1_cases().items():
        with_distress = replace(a, arrival_respiratory_distress=PROBE_DISTRESS)
        committed[name] = {"mechanics_candidate": p.respiratory_mechanics,
                           "refused": _refused(lambda: dv.arrival_state(with_distress, readers(p))),
                           "sympathetic_only_accepted": not _refused(
                               lambda: dv.arrival_state(with_distress, readers(p, respiratory=None)))}
    # Accepted: the sympathetic reader alone (arrival and evolving), distress 0 with both readers, mechanics on.
    symp = readers(off, respiratory=None)
    base, lifted = dm.at_arrival(anchors, symp), dm.at_arrival(some, symp)
    _, symp_trail = _course(dv.arrival_state(anchors, symp), ((1.0,), (1.0,)), anchors, symp)
    sympathetic_only = {"arrival": lifted, "distress_0": base, "evolving_trail": symp_trail,
                        "hr_up": lifted["hr"] > base["hr"],
                        "rr_paco2_unchanged": all(lifted[k] == base[k] for k in ("rr", "paco2", "ph", "W"))}
    unset_reading, zero_reading = dm.at_arrival(anchors, off), dm.at_arrival(anchors, readers(off))
    distress_zero = {"same_as_unset": all(zero_reading[k] == unset_reading[k] for k in dm.RESPIRATORY_CONSEQUENCES
                                          + dm.SYMPATHETIC_CONSEQUENCES + dm.NEVER_MOVED),
                     "evolving_zero_change_accepted": not _refused(
                         lambda: ig.step(zero_state, _writers((0.0,), 1), anchors, readers(off)))}
    on_rows = {p: dm.at_arrival(dm.probe_anchors(arrival_respiratory_distress=PROBE_DISTRESS, arrival_paco2=p),
                                readers(on)) for p in ARRIVAL_PACO2_VALUES}
    on_zero = dm.at_arrival(anchors, readers(on))
    _, on_trail = _course(dv.arrival_state(anchors, readers(on)), ((1.0,), (1.0,)), anchors, readers(on))
    mechanics = {"rows": {str(k): v for k, v in on_rows.items()}, "evolving_trail": on_trail,
                 "rr_up": all(r["rr"] > on_zero["rr"] for r in on_rows.values()),
                 "paco2_ignores_the_arrival_paco2": len({r["paco2"] for r in on_rows.values()}) == 1}
    default = {"readers_unset": not dv.respiratory_distress_read(dv.DEFAULT_PROFILE),
               "default_arrival_accepted": not _refused(lambda: dv.arrival_state(anchors, dv.DEFAULT_PROFILE))}
    out = {"classification": M1_CLASS, "option_2": ANCHOR_CLASS, "refused": refused, "committed": committed,
           "sympathetic_only": sympathetic_only, "distress_zero": distress_zero, "mechanics_on": mechanics,
           "default": default}
    out["pass"] = (all(refused.values())
                   and all(c["refused"] == (not c["mechanics_candidate"]) and c["sympathetic_only_accepted"]
                           for c in committed.values())
                   and sympathetic_only["hr_up"] and sympathetic_only["rr_paco2_unchanged"]
                   and sympathetic_only["evolving_trail"] == [1.0, 2.0]
                   and all(distress_zero.values()) and mechanics["rr_up"] and mechanics["paco2_ignores_the_arrival_paco2"]
                   and mechanics["evolving_trail"] == [1.0, 2.0] and all(default.values()))
    return out


# P2T-1A-3: L1 (numerical precision) ----------------------------------------------------------------------------------------

def _raw(before, amounts) -> float:
    return math.fsum((before, *amounts))


def _decide(before, amounts):
    """The integration's decision for one minute: the normalized value, or "refused"."""
    value = ig.distress_sum(before, amounts)
    return "refused" if value < 0.0 else value


def _exact_zero(value) -> bool:
    return value == 0.0 and math.copysign(1.0, value) == 1.0


def l1() -> dict:
    on = readers(mechanics_on())
    anchors = dm.PROBE_ANCHORS
    start = dv.arrival_state(anchors, on)
    # A: +0.3 -0.1 -0.2, in one minute and in three, through the integration.
    one = _course(start, (TRIAD,), anchors, on)[1]
    three = _course(start, tuple((a,) for a in TRIAD), anchors, on)[1]
    a = {"raw_one_minute": _raw(0.0, TRIAD), "one_minute": one, "three_minutes": three,
         "pass": _exact_zero(one[-1]) and _exact_zero(three[-1]) and _raw(0.0, TRIAD) < 0.0}
    # B: every order in one minute; every minute-by-minute order and grouping whose running value stays at or above 0.
    in_one = {str(p): _decide(0.0, p) for p in itertools.permutations(TRIAD)}
    sequences, refused = {}, []
    for order in itertools.permutations(TRIAD):
        for parts in range(2, len(order) + 1):
            for groups in _groupings(order, parts):
                try:
                    sequences[str(groups)] = _course(start, groups, anchors, on)[1][-1]
                except ProvenanceError:
                    # a minute that ends materially below 0 (a negative change first) is refused, whatever follows
                    refused.append(str(groups))
    expected = sorted(str(groups) for order in itertools.permutations(TRIAD) for parts in range(2, len(order) + 1)
                      for groups in _groupings(order, parts) if _ends_materially_below_0(groups))
    b = {"one_minute": in_one, "sequences": sequences, "refused_sequences": sorted(refused),
         "refused_exactly_when_a_minute_ends_materially_below_0": sorted(refused) == expected,
         "pass": all(_exact_zero(v) for v in in_one.values()) and bool(sequences)
         and all(_exact_zero(v) for v in sequences.values()) and sorted(refused) == expected}
    # C: roundoff-scale negatives are 0 exactly.
    c_rows = {str(case): {"raw": _raw(*case), "bound": _bound(*case), "decided": _decide(*case)}
              for case in ROUNDOFF_NEGATIVES}
    c = {"rows": c_rows, "pass": all(r["raw"] < 0.0 and _exact_zero(r["decided"]) for r in c_rows.values())}
    # D: material negatives are refused, in the sum and through the integration.
    d_rows = {}
    for before, amounts in MATERIAL_NEGATIVES:
        state = start if before == 0.0 else _course(start, ((before,),), anchors, on)[0]
        d_rows[str((before, amounts))] = {"raw": _raw(before, amounts), "bound": _bound(before, amounts),
                                          "decided": _decide(before, amounts),
                                          "integration_refuses": _refused(
                                              lambda: ig.step(state, _writers(amounts, state.minute + 1), anchors, on))}
    d = {"rows": d_rows, "pass": all(r["decided"] == "refused" and r["integration_refuses"] for r in d_rows.values())}
    # E: small legitimate positives are kept.
    e_rows = {str(case): {"raw": _raw(*case), "decided": _decide(*case)} for case in SMALL_POSITIVES}
    e = {"rows": e_rows, "pass": all(r["decided"] == r["raw"] > 0.0 for r in e_rows.values())}
    # F: no clinical parameter or threshold; the decision is invariant to rescaling every operand by a power of two.
    scaled = {}
    for k in SCALES:
        scaled[str(k)] = {"triad": _decide(0.0, tuple(k * x for x in TRIAD)),
                          "material": _decide(0.3 * k, (-0.31 * k,)),
                          "roundoff": [_decide(b * k, tuple(k * x for x in am)) for b, am in ROUNDOFF_NEGATIVES]}
    profile_fields = sorted(f.name for f in fields(dv.CoreProfile))
    p2t1_fields = sorted(dm._class_fields(p2t1_text("clinical_core/derived.py"), "CoreProfile"))
    f = {"scaled": scaled, "profile_fields_are_p2t1s": profile_fields == p2t1_fields,
         "parameter_names_are_p2t1s": sorted(dv.PARAMETERS) == sorted(_p2t1_parameter_names()),
         "sum_constants": audit_sum_constants(),
         "pass": profile_fields == p2t1_fields and sorted(dv.PARAMETERS) == sorted(_p2t1_parameter_names())
         and set(audit_sum_constants()) <= {0.0, 1.0}
         and all(_exact_zero(v["triad"]) and v["material"] == "refused" and all(_exact_zero(x) for x in v["roundoff"])
                 for v in scaled.values())}
    out = {"A": a, "B": b, "C": c, "D": d, "E": e, "F": f,
           "tolerance": "math.ulp(1.0) x fsum(|operands|): each operand's rounding plus the sum's (binary64)"}
    out["pass"] = all(out[k]["pass"] for k in "ABCDEF")
    return out


def _bound(before, amounts) -> float:
    return math.ulp(1.0) * math.fsum(abs(t) for t in (before, *amounts))


def _ends_materially_below_0(groups) -> bool:
    """Whether some minute of the sequence ends below 0 by more than the roundoff of that minute's operands."""
    value = 0.0
    for amounts in groups:
        raw = _raw(value, amounts)
        if raw < -_bound(value, amounts):
            return True
        value = max(raw, 0.0)
    return False


def _groupings(order, parts):
    """Every split of the order into the given number of consecutive non-empty minutes."""
    n = len(order)
    for cuts in itertools.combinations(range(1, n), parts - 1):
        edges = (0, *cuts, n)
        yield tuple(tuple(order[edges[i]:edges[i + 1]]) for i in range(parts))


def audit_sum_constants() -> list:
    total = mc._functions(_live("clinical_core/integration.py"))[SUM]
    return sorted({n.value for n in ast.walk(total) if isinstance(n, ast.Constant)
                   and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})


def _p2t1_parameter_names() -> list:
    tree = ast.parse(p2t1_text("clinical_core/derived.py"))
    node = next(n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.AnnAssign))
                and any(getattr(t, "id", None) == "PARAMETERS"
                        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])))
    return [k.value for k in node.value.keys]


# P2T-1A-4: non-regression -------------------------------------------------------------------------------------------------------

def non_regression() -> dict:
    """P2T-1's D1-D12 and its other sections live (its sources read on its tree for its own proofs, behaviour live);
    P2T-1's contrasts live (the mechanics-off ones are the M1 combination); P2T-1's record reproduced on its own tree
    (which nests P2S-3, P2S-2 and every earlier closed record)."""
    with p2t1_view(historical=False):
        probes = dm.structural_probes()
        sections = {"representation": dm.representation()["pass"], "beta_blockade": dm.beta_blockade()["pass"],
                    "orthogonality": dm.orthogonality()["pass"], "observable": dm.observable()["pass"],
                    "parameters": dm.parameter_state()["pass"], "systemic_stress": dm.systemic_stress()["pass"],
                    "ordering": dm.wob_ordering()["pass"]}
        contrasts_refused = _refused(dm.contrasts)
    with p2t1_view():
        p2t1 = dm.run()
        p2t1_digest = dm.freeze_digest()
    record = json.loads(dm.RECORD.read_text(encoding="utf-8"))
    out = {"p2t1_probes_live": {k: v["pass"] for k, v in probes.items()},
           "p2t1_sections_live": sections,
           "p2t1_contrasts_live_refused_by_m1": contrasts_refused,
           "p2t1_record_reproduced_on_its_tree": json.loads(json.dumps(p2t1, sort_keys=True, default=str)) == record,
           "p2t1_freeze_digest_on_its_tree": p2t1_digest == P2T1_FREEZE_DIGEST,
           "p2t1_record_untouched": hashlib.sha256(dm.RECORD.read_bytes()).hexdigest() == P2T1_RECORD_SHA,
           "p2s2_p2s3_records_reproduced": bool(p2t1["non_regression"]["p2s2_record_reproduced"]
                                                and p2t1["non_regression"]["p2s3_record_reproduced"]),
           "p2s3_historical_verdict": p2t1["non_regression"]["p2s3_historical_verdict"],
           "p2s3_classification": p2t1["non_regression"]["p2s3_classification"],
           "committed_profiles_unset": all(not dv.respiratory_distress_read(p) for p in dm.committed_profiles().values()),
           "systemic_stress": "SYSTEMIC_STRESS_DEFERRED (nothing added)"}
    out["pass"] = (all(out["p2t1_probes_live"].values()) and all(sections.values()) and contrasts_refused
                   and out["p2t1_record_reproduced_on_its_tree"] and out["p2t1_freeze_digest_on_its_tree"]
                   and out["p2t1_record_untouched"] and out["p2s2_p2s3_records_reproduced"]
                   and out["committed_profiles_unset"])
    return out


# The proof: the P2T-1 tree plus P2T-1A's declared insertions ----------------------------------------------------------------------

P2T1_HEAD = "851a835"
# <reversal>
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/asthma_migration.py", '
                                     '"clinical_core/asthma_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_distress.py", '
                                     '"clinical_core/respiratory_distress_report.py",\n'
                                     '                        "clinical_core/distress_closure.py", '
                                     '"clinical_core/distress_closure_report.py")\n'
                                     '\n',
                                     '                        "clinical_core/asthma_migration.py", '
                                     '"clinical_core/asthma_migration_report.py",\n'
                                     '                        "clinical_core/respiratory_distress.py", '
                                     '"clinical_core/respiratory_distress_report.py")\n'
                                     '\n'),),
 'clinical_core/derived.py': (('\n'
                               'def check_distress_respiratory_effect(profile: CoreProfile, distress: float) -> '
                               'None:\n'
                               '    """P2T-1A (M1, faculty option 1; '
                               'DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT): a respiratory distress\n'
                               '    above 0 read by the respiratory reader needs the P2S-2 common respiratory '
                               'mechanics candidate, so its RR effect reaches\n'
                               '    the PaCO2 through W and never through the retired P2K-2 arrival PaCO2 anchor '
                               '(DISTRESS_IN_ANCHOR = REJECTED: the\n'
                               '    anchor is not changed to absorb it). The sympathetic reader alone, and a '
                               'distress of 0, need nothing."""\n'
                               '    if distress > 0.0 and profile.distress_to_respiratory_drive_gain is not None and '
                               'not profile.respiratory_mechanics:\n'
                               '        raise CoreInvariantError("a respiratory distress above 0 read by the '
                               'respiratory drive needs the common "\n'
                               '                                 "respiratory mechanics candidate (P2T-1A, M1): with '
                               'it off, its RR effect would move the "\n'
                               '                                 "PaCO2 through the retired arrival PaCO2 anchor")\n'
                               '\n'
                               '\n'
                               'def intrinsic_respiratory_rate(anchors: Anchors) -> float:\n',
                               '\ndef intrinsic_respiratory_rate(anchors: Anchors) -> float:\n'),
                              ('        # P2T-1: the non-chemical excitatory term joins the chemical ones before the '
                               'common saturation.\n'
                               '        check_distress_respiratory_effect(profile, distress)\n'
                               '        distress_drive = profile.distress_to_respiratory_drive_gain * distress\n',
                               '        # P2T-1: the non-chemical excitatory term joins the chemical ones before the '
                               'common saturation.\n'
                               '        distress_drive = profile.distress_to_respiratory_drive_gain * distress\n'),
                              ('                                 "nothing else reads it")\n'
                               '    check_distress_respiratory_effect(profile, '
                               'anchors.arrival_respiratory_distress)\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n',
                               '                                 "nothing else reads it")\n'
                               '    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)\n')),
 'clinical_core/integration.py': (('                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active, '
                                   'respiratory_distress_read,\n'
                                   '                      check_distress_respiratory_effect)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n',
                                   '                      oxygen_demand, plasma_refill, red_cell_content, '
                                   'sympathetic_after_minute, terminal_rhythm,\n'
                                   '                      tone_target, respiratory_mechanics_active, '
                                   'respiratory_distress_read)\n'
                                   'from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, '
                                   'BloodFlow, BloodProcess, ChannelDelta,\n'),
                                  ('                              "its readers are UNSET (P2T-1): nothing would read '
                                   'it")\n'
                                   '    value = distress_sum(state.aux.respiratory_distress, [item.amount for item '
                                   'in distress])\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the respiratory distress '
                                   'changes take it to {value!r}, below 0 (P2T-1)")\n'
                                   '    check_distress_respiratory_effect(profile, value)\n'
                                   '    return value\n'
                                   '\n'
                                   '\n'
                                   'def distress_sum(before: float, amounts) -> float:\n'
                                   '    """P2T-1A (L1): the respiratory distress after a minute\'s changes, summed '
                                   'once (math.fsum over the value it starts\n'
                                   '    with and every change, so the order of the changes does not matter). A '
                                   'negative sum no larger in size than the\n'
                                   '    roundoff of the operands (the binary64 epsilon, math.ulp(1.0), times the sum '
                                   "of their magnitudes: each operand's own\n"
                                   "    rounding plus the sum's) cannot be told from 0 and is 0 exactly; a sum below "
                                   'that is returned as it is and refused by\n'
                                   '    the caller. No clinical threshold: the bound is floating-point precision at '
                                   'the operands\' scale."""\n'
                                   '    terms = (before, *amounts)\n'
                                   '    value = math.fsum(terms)\n'
                                   '    if value < 0.0 and -value <= math.ulp(1.0) * math.fsum(abs(term) for term in '
                                   'terms):\n'
                                   '        return 0.0\n'
                                   '    return value + 0.0\n'
                                   '\n',
                                   '                              "its readers are UNSET (P2T-1): nothing would read '
                                   'it")\n'
                                   '    value = state.aux.respiratory_distress + math.fsum(item.amount for item in '
                                   'distress)\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the respiratory distress '
                                   'changes take it to {value!r}, below 0 (P2T-1)")\n'
                                   '    return value\n'
                                   '\n'),
                                  ('        raise ProvenanceError("the respiratory mechanics efficiency changed by '
                                   'other than its recorded changes")\n'
                                   '    if after.aux.respiratory_distress != '
                                   'distress_sum(before.aux.respiratory_distress,\n'
                                   '                                                     [item.amount for item in '
                                   'record.distress]):\n'
                                   "        # P2T-1: the distress moves by exactly the minute's recorded changes, "
                                   'never otherwise.\n',
                                   '        raise ProvenanceError("the respiratory mechanics efficiency changed by '
                                   'other than its recorded changes")\n'
                                   '    if after.aux.respiratory_distress != before.aux.respiratory_distress + '
                                   'math.fsum(item.amount\n'
                                   '                                                                                     '
                                   'for item in record.distress):\n'
                                   "        # P2T-1: the distress moves by exactly the minute's recorded changes, "
                                   'never otherwise.\n')),
 'clinical_core/lactate_slice.py': (('                      "clinical_core/asthma_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_distress_report.py",\n'
                                     '                      "clinical_core/distress_closure_report.py")\n'
                                     '\n',
                                     '                      "clinical_core/asthma_migration_report.py",\n'
                                     '                      "clinical_core/respiratory_distress_report.py")\n'
                                     '\n'),)}
CORE_AT_P2T1 = {'clinical_core/decision_pack.py': '757b82454f242c8b8bc81173d091601a4d294f2ed286230bfd343e14cc9dcc5a',
 'clinical_core/derived.py': '10dfe67ca7688f65a9dd0d3467b48cca1b196530ea57e9dd60d5040a2a83033c',
 'clinical_core/integration.py': 'af472bc96c920fce76e9ca49f06a539f244c761ced236953e6652a4347b7e343',
 'clinical_core/lactate_slice.py': '4b7544878316cfe2f01c2c45e6bf19bad8bafe97fdcfae629e01e5cd6431ab29'}
# </reversal>
# <common>
COMMON_AT_P2T1 = {'clinical_core/__init__.py': 'acb1d8137d2dab84a0c3f5b4d68b3e904d8e85564a657233bb0e622e539338c2',
 'clinical_core/a9.py': '64006b57e37ab69dd9dfd61d5c87b01112779f19e7007b96440cfad345ad5b92',
 'clinical_core/acid_base.py': '9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954',
 'clinical_core/acid_base_report.py': '9f0b9f5b03369066e4ac7916b372453c41ef7793b36c20553b88d726b83afa78',
 'clinical_core/acs_migration.py': '4fae25400e94b7c1f3b6b77f277dd5e04b72d150c52da738faddf95b37edd971',
 'clinical_core/acs_migration_report.py': 'dbe33c01e165f9471dcb720919c3fac257f3d0903972117a420e91632b4c2d6b',
 'clinical_core/acs_reference.py': 'b7b69c7892314375de236aec35016178218dfa4b114874b165c7191a0de2cfa1',
 'clinical_core/arrival_severity.py': 'c5c0e4c125303b463ec1d2a5373464c09576f7d83ca975834e6b059c67b2b229',
 'clinical_core/arrival_severity_report.py': 'a1806dc772a4f0a540a621271e8dd24b4c77b36da2b55af5e1da623cf30ac2eb',
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
P2T1_FREEZE_DIGEST = "773188d100813d0cced871f007d35c18bdeff18d95e7d4cecab160cc46c0fc2c"
P2T1_RECORD_SHA = "dd32bc6dc02e5fdfe3dd6e35dff00df559730a62573faf9c0ea7cbca29bdecea"


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
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_P2T1[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def common_untouched() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in COMMON_AT_P2T1.items()}


def p2t1_text(relative: str) -> str:
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the P2T-1 file plus P2T-1A's declared insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def p2t1_sources(sources: dict) -> dict:
    """A P2T-1 dependency map: P2T-1A's files removed, each changed file at its P2T-1 hash when proven."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_P2T1.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


class _TreeFile:
    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return p2t1_text(self.relative)


class _TreeDir:
    """P2T-1's ``CORE_DIR`` (its audit reads derived.py and integration.py from it): the P2T-1 text of P2T-1A's changed
    files, the live path of anything else."""

    def __truediv__(self, name):
        relative = f"clinical_core/{name}"
        return _TreeFile(relative) if relative in REVERSAL else CORE_DIR / name


def _p2t1_guard(profile, distress) -> None:
    """P2T-1 had no M1 guard."""


def _p2t1_sum(before, amounts) -> float:
    """P2T-1's sum: the value the minute starts with plus math.fsum of the changes, never normalized."""
    return before + math.fsum(amounts)


_FREEZE_SOURCES = bf.freeze_sources


def chain(patch, historical: bool = True) -> None:
    """For the closed packages' test fixtures: P2T-1's view reads the P2T-1 files (proven) and its captured source map
    is P2T-1's. ``historical`` (the default, for closed records) also reads the two new helpers as P2T-1 had them: no
    M1 guard and the unnormalized sum; without it the behaviour is live and only the sources are P2T-1's."""
    patch.setattr(dm, "_live", p2t1_text)
    patch.setattr(dm, "CORE_DIR", _TreeDir())
    patch.setattr(dm, "_FREEZE_SOURCES", lambda: p2t1_sources(_FREEZE_SOURCES()))
    if historical:
        patch.setattr(dv, GUARD, _p2t1_guard)
        patch.setattr(ig, GUARD, _p2t1_guard)
        patch.setattr(ig, SUM, _p2t1_sum)


class p2t1_view:
    """P2T-1's analysis reading the tree P2T-1 froze, for its own proofs and (historical) its own record."""

    def __init__(self, historical: bool = True):
        self.historical = historical

    def __enter__(self):
        self._patch = mc._Patch()
        chain(self._patch, self.historical)
        self._patch.setattr(bf, "freeze_sources", lambda: p2t1_sources(_FREEZE_SOURCES()))
        return self

    def __exit__(self, *exc):
        self._patch.undo()
        return False


def upstream_unchanged() -> dict:
    with p2t1_view():
        p2t1_digest = dm.freeze_digest()
        p2t1_proof = dm.upstream_unchanged()
    return {"proofs": proofs(), "common_untouched": common_untouched(),
            "p2t1_freeze_digest": p2t1_digest == P2T1_FREEZE_DIGEST,
            "p2t1_proof": all(p2t1_proof["proofs"].values()) and all(p2t1_proof["common_untouched"].values())
            and p2t1_proof["p2s3_freeze_digest"] and p2t1_proof["p2s3_proof"] and p2t1_proof["p2s3_record"],
            "p2t1_record": hashlib.sha256(dm.RECORD.read_bytes()).hexdigest() == P2T1_RECORD_SHA}


# P2T-1A-5: readiness (predeclared) ----------------------------------------------------------------------------------------------

READINESS_CRITERIA = (
    f"M1: the respiratory effect of a distress above 0 is refused with the mechanics candidate off, at arrival, for an "
    f"evolving writer and for any state ({M1_CLASS})",
    "M1: the sympathetic reader alone, a distress of 0, the mechanics candidate on and the default are accepted",
    f"M1: no PaCO2 anchoring returns: every anchor reader is P2T-1's and the mechanics-on PaCO2 ignores the arrival "
    f"PaCO2 ({ANCHOR_CLASS})",
    "L1: A-F (roundoff negatives are 0 exactly in any order; material negatives refused; small positives kept; no "
    "clinical parameter or threshold; scale invariant)",
    "only the declared functions changed (the audit; the P2T-1 files and every common file proven)",
    "non-regression: P2T-1's D1-D12 live, its record and digest on its tree, the P2S-2 / P2S-3 records, the committed "
    "profiles UNSET, no systemic stress",
)
READY = "P2T1A_SEMANTIC_CLOSURE_READY"
NOT_READY = "P2T1A_SEMANTIC_CLOSURE_NOT_READY"
READINESS_RULE = "Predeclared. READY when every criterion holds; otherwise NOT_READY with the first failing criterion"


def readiness(found: dict) -> dict:
    m, proof = found["m1"], found["proof"]
    checks = (
        all(m["refused"].values()) and all(c["refused"] == (not c["mechanics_candidate"])
                                           for c in m["committed"].values()),
        m["sympathetic_only"]["hr_up"] and m["sympathetic_only"]["rr_paco2_unchanged"]
        and all(c["sympathetic_only_accepted"] for c in m["committed"].values())
        and all(m["distress_zero"].values()) and m["mechanics_on"]["rr_up"] and all(m["default"].values()),
        found["audit"]["anchor_readers_are_p2t1s"] and found["audit"]["guard_reads_no_anchor"]
        and m["mechanics_on"]["paco2_ignores_the_arrival_paco2"],
        found["l1"]["pass"],
        found["audit"]["pass"] and all(proof["proofs"].values()) and all(proof["common_untouched"].values())
        and proof["p2t1_freeze_digest"] and proof["p2t1_proof"] and proof["p2t1_record"],
        found["non_regression"]["pass"],
    )
    rows = [{"criterion": c, "holds": bool(h)} for c, h in zip(READINESS_CRITERIA, checks)]
    blocker = next((r["criterion"] for r in rows if not r["holds"]), None)
    verdict = READY if blocker is None else f"{NOT_READY} - {blocker}"
    return {"criteria": rows, "blocker": blocker, "verdict": verdict, "rule": READINESS_RULE,
            "m1": M1_CLASS, "option_2": ANCHOR_CLASS}


def design() -> dict:
    return {"decisions": DECISIONS,
            "synthetic": {"respiratory_gain": RESPIRATORY_GAIN, "sympathetic_gain": SYMPATHETIC_GAIN,
                          "probe_distress": PROBE_DISTRESS, "arrival_paco2_values": list(ARRIVAL_PACO2_VALUES),
                          "triad": list(TRIAD), "roundoff_negatives": [[b, list(a)] for b, a in ROUNDOFF_NEGATIVES],
                          "material_negatives": [[b, list(a)] for b, a in MATERIAL_NEGATIVES],
                          "small_positives": [[b, list(a)] for b, a in SMALL_POSITIVES], "scales": list(SCALES)},
            "readiness": {"criteria": list(READINESS_CRITERIA), "rule": READINESS_RULE},
            "reversal": REVERSAL, "core_at_p2t1": CORE_AT_P2T1, "common_at_p2t1": COMMON_AT_P2T1,
            "p2t1": {"head": P2T1_HEAD, "freeze_digest": P2T1_FREEZE_DIGEST, "record": P2T1_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2t1": hashlib.sha256(dm.RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    found = {"proof": upstream_unchanged(), "audit": audit(), "m1": m1(), "l1": l1(),
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
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
