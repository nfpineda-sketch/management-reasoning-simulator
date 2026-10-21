"""Legacy-versus-core trajectory comparison. Pure: it reads two trajectories and reports.

Three kinds of comparison, never mixed:

- ``exact``: quantities both engines compute with the same arithmetic from the same
  inputs (haemoglobin, delivered volumes, FiO2, the volume channel against the family
  engine's circulation). Equality within floating-point noise is expected; any other
  difference is a mismatch.
- ``display``: vital signs and labs the family engine shows rounded and held in a
  display range. The core's raw value is projected through the *same* display
  convention (rounding and range only, no physiology) and compared for equality. The
  project has no agreed tolerance for these (proposal Appendix A9), so every
  difference is reported as a mismatch with tolerance "TBD"; nothing is hidden.
  One exception is reported separately, never as a match: a difference of exactly
  one display step where the core's raw value sits on a .5 rounding boundary within
  floating-point noise (``rounding_tie``) -- the two engines then hold the same value
  and differ only in which side of the boundary their last bit fell.
- ``categorical``: pulse, rhythm family and consciousness level.

``core_only`` and ``legacy_only`` quantities are reported for explanation, never compared.
Nothing here tunes either engine.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .derived import LEGACY_ML_PER_CIRCULATION_UNIT, Derived
from .state import CoreState

FLOAT_NOISE = 1e-9
TBD = "TBD (no agreed tolerance; proposal Appendix A9)"
SAMPLE_MINUTES = (0, 1, 5, 10, 15, 20, 30, 45, 60, 75, 90, 105, 120)
LEVEL_OF = {"Alert": 0, "Drowsy": 1, "Obtunded": 2, "Unresponsive": 3}

#: The family engine's display convention (family_engine._surface): integer rounding with
#: Python's round(), and these ranges. Only the observation layer would apply them; the
#: comparison applies them to the core's raw values so like is compared with like.
DISPLAY_RANGE = {"sbp": (50, 240), "hr": (42, 180), "spo2": (55, 99), "respiratory_rate": (3, 45), "crt": (2, 8)}


def _int_display(value, name):
    lower, upper = DISPLAY_RANGE[name]
    return int(round(min(upper, max(lower, value))))


#: Display variables, their rounding step and the raw core value they are projected from.
_RAW = {"sbp": (1, lambda d: d.sbp), "dbp": (1, lambda d: d.dbp), "hr": (1, lambda d: d.pulse_rate_bpm),
        "spo2": (1, lambda d: d.spo2), "respiratory_rate": (1, lambda d: d.respiratory_rate),
        "crt_s": (0.1, lambda d: d.crt_s), "lactate_mmol_l": (0.1, lambda d: d.lactate)}


def _on_rounding_boundary(value, step) -> bool:
    """Whether a raw value sits on a rounding boundary (x.5 of its display step) within float noise."""
    if value is None:
        return False
    scaled = value / step
    return abs(abs(scaled - math.floor(scaled)) - 0.5) <= FLOAT_NOISE * max(1.0, abs(scaled))


def _neighbours(value, step) -> tuple:
    """The two display values a raw value on a .5 boundary can round to."""
    low = math.floor(value / step) * step
    return (round(low, 1), round(low + step, 1)) if step != 1 else (int(low), int(low) + 1)


def _is_tie(name, legacy, core, derived, ties_this_minute) -> bool:
    """A one-step display difference that comes only from where a shared raw value fell on a .5 boundary.

    Both sides must be one of the two values that boundary rounds to: a legacy value outside
    that pair cannot come from the same raw value, so it stays a mismatch.
    """
    if not derived.pulse_present or not isinstance(legacy, (int, float)) or not isinstance(core, (int, float)):
        return False
    if name == "map":
        if not ties_this_minute & {"sbp", "dbp"}:
            return False
        sbp = _neighbours(derived.sbp, 1) if "sbp" in ties_this_minute else (_int_display(derived.sbp, "sbp"),)
        dbp = _neighbours(derived.dbp, 1) if "dbp" in ties_this_minute else (int(round(derived.dbp)),)
        return legacy in {int(round((s + 2 * d) / 3)) for s in sbp for d in dbp}
    if name not in _RAW:
        return False
    step, raw = _RAW[name]
    value = raw(derived)
    if not _on_rounding_boundary(value, step):
        return False
    pair = _neighbours(value, step)
    return legacy in pair and core in pair and legacy != core


def _display(derived: Derived) -> dict:
    """The core's derived values projected through the family engine's display convention."""
    if not derived.pulse_present:
        return {"sbp": 0, "dbp": 0, "map": 0, "hr": 0, "spo2": 0, "respiratory_rate": 0, "crt": 8.0}
    sbp = _int_display(derived.sbp, "sbp")
    dbp = int(round(min(min(140, sbp - 15), max(25, derived.dbp))))
    return {"sbp": sbp, "dbp": dbp, "map": int(round((sbp + 2 * dbp) / 3)), "hr": _int_display(derived.pulse_rate_bpm, "hr"),
            "spo2": _int_display(derived.spo2, "spo2"),
            "respiratory_rate": _int_display(derived.respiratory_rate, "respiratory_rate"),
            "crt": round(min(8, max(2, derived.crt_s)), 1)}


def _rhythm_family(label):
    """The legacy label reduced to the core's rhythm code; an unknown label stays itself and so mismatches."""
    if label is None:
        return None
    text = str(label).lower()
    if text.startswith("sinus"):
        return "sinus"
    return {"af": "af", "vf": "vf", "asystole": "asystole", "pea": "pea"}.get(text, f"unmapped:{label}")


def _level(label):
    return None if label is None else LEVEL_OF.get(label, f"unmapped:{label}")


@dataclass(frozen=True)
class Variable:
    name: str
    kind: str
    unit: str
    legacy: Callable[[Mapping], object] | None
    core: Callable[[CoreState, Derived, dict], object] | None
    tolerance: str
    note: str = ""


def _delivered(state: CoreState, field: str) -> float:
    return math.fsum(float(value.get(field, 0.0)) for key, value in state.internal.items()
                     if key.startswith("intervention:") and hasattr(value, "get"))


VARIABLES: tuple[Variable, ...] = (
    Variable("V_ml_eq", "exact", "mL-eq", lambda s: (1.0 - s["circulation"]) * LEGACY_ML_PER_CIRCULATION_UNIT,
             lambda c, d, p: c.V, f"float noise {FLOAT_NOISE:g}",
             "legacy circulation converted at 300 mL per 0.36 circulation; legacy clamps circulation to [.25, 1.9]"),
    Variable("hb_g_dl", "exact", "g/dL", lambda s: s["hemoglobin"], lambda c, d, p: c.hb, f"float noise {FLOAT_NOISE:g}"),
    Variable("glucose_mg_dl", "exact", "mg/dL", lambda s: s["glucose"], lambda c, d, p: c.glucose,
             f"float noise {FLOAT_NOISE:g}"),
    Variable("k_mmol_l", "exact", "mmol/L", lambda s: s["potassium_lab"], lambda c, d, p: c.k,
             f"float noise {FLOAT_NOISE:g}", "legacy has no potassium state in this family: the authored lab value"),
    Variable("fio2", "exact", "fraction", lambda s: s["oxygen_fio2"], lambda c, d, p: c.fio2,
             f"float noise {FLOAT_NOISE:g}"),
    Variable("fluid_delivered_ml", "exact", "mL", lambda s: s["fluid_delivered_ml"],
             lambda c, d, p: _delivered(c, "delivered_ml"), f"float noise {FLOAT_NOISE:g}"),
    Variable("blood_delivered_units", "exact", "units", lambda s: s["blood_delivered_units"],
             lambda c, d, p: _delivered(c, "delivered_units"), f"float noise {FLOAT_NOISE:g}"),
    Variable("sbp", "display", "mmHg", lambda s: s["sbp"], lambda c, d, p: p["sbp"], TBD),
    Variable("dbp", "display", "mmHg", lambda s: s["dbp"], lambda c, d, p: p["dbp"], TBD),
    Variable("map", "display", "mmHg", lambda s: s["map"], lambda c, d, p: p["map"], TBD,
             "the family engine leaves MAP unset until its first surface"),
    Variable("hr", "display", "/min", lambda s: s["hr"], lambda c, d, p: p["hr"], TBD),
    Variable("spo2", "display", "%", lambda s: s["spo2"], lambda c, d, p: p["spo2"], TBD),
    Variable("respiratory_rate", "display", "/min", lambda s: s["respiratory_rate"],
             lambda c, d, p: p["respiratory_rate"], TBD),
    Variable("crt_s", "display", "s", lambda s: s["crt"], lambda c, d, p: p["crt"], TBD),
    Variable("lactate_mmol_l", "display", "mmol/L", lambda s: s["lactate_lab"], lambda c, d, p: round(d.lactate, 1),
             TBD, "legacy: the lab the engine would report now"),
    Variable("pulse_present", "categorical", "", lambda s: bool(s["pulse_present"]), lambda c, d, p: d.pulse_present,
             "categorical equality"),
    Variable("rhythm", "categorical", "", lambda s: _rhythm_family(s["rhythm"]), lambda c, d, p: d.rhythm.value,
             "categorical equality", "legacy label reduced to its rhythm family"),
    Variable("consciousness_level", "categorical", "0-3", lambda s: _level(s["mental_status"]),
             lambda c, d, p: d.consciousness_level, "categorical equality"),
    Variable("D", "core_only", "index-min", None, lambda c, d, p: c.D, "not compared",
             "oxygen-delivery debt; the family engine has no equivalent state"),
    Variable("delivery_rel", "core_only", "of arrival", None, lambda c, d, p: d.delivery_rel, "not compared"),
    Variable("hemostasis_relief", "legacy_only", "0-1", lambda s: s["hemostasis_relief"], None, "not compared",
             "legacy subtracts 20 bpm x this value from the displayed HR"),
    Variable("transfusion_overload_units", "legacy_only", "units", lambda s: s["transfusion_overload_units"], None,
             "not compared", "legacy lung-water consequence of transfusing a non-anaemic patient"),
)


def _matches(kind, legacy, core):
    if legacy is None or core is None:
        return None
    if kind == "exact":
        scale = max(1.0, abs(float(legacy)), abs(float(core)))
        return abs(float(legacy) - float(core)) <= FLOAT_NOISE * scale
    return legacy == core


def compare(legacy_snapshots: Sequence[Mapping], states: Sequence[CoreState], derived: Sequence[Derived]) -> dict:
    """Per-variable, per-minute comparison of two trajectories of the same length."""
    if not (len(legacy_snapshots) == len(states) == len(derived)):
        raise ValueError("the trajectories cover different minutes")
    for minute, (snap, state) in enumerate(zip(legacy_snapshots, states)):
        if snap["minute"] != state.minute or state.minute != minute:
            raise ValueError("the trajectories are not aligned minute by minute")
    rows = {variable.name: [] for variable in VARIABLES}
    for snap, state, values in zip(legacy_snapshots, states, derived):
        projected = _display(values)
        ties = set()
        for variable in VARIABLES:
            legacy = variable.legacy(snap) if variable.legacy else None
            core = variable.core(state, values, projected) if variable.core else None
            match = _matches(variable.kind, legacy, core) if variable.kind in {"exact", "display", "categorical"} else None
            if variable.kind in {"core_only", "legacy_only"}:
                status = "not_compared"
            elif match is None:
                status = "not_comparable"
            elif match:
                status = "match"
            elif variable.kind == "display" and _is_tie(variable.name, legacy, core, values, ties):
                status = "rounding_tie"
                ties.add(variable.name)
            else:
                status = "mismatch"
            rows[variable.name].append({"minute": state.minute, "legacy": legacy, "core": core, "status": status})
    return rows


def _rounded(value):
    if isinstance(value, float):
        return round(value, 6)
    return value


def summarize(rows: Mapping[str, Sequence[Mapping]]) -> dict:
    """The per-variable digest the golden file keeps: counts, first mismatch, worst difference, samples."""
    summary = {}
    for variable in VARIABLES:
        series = rows[variable.name]
        compared = [row for row in series if row["status"] in {"match", "mismatch", "rounding_tie"}]
        mismatched = [row for row in compared if row["status"] == "mismatch"]
        ties = [row["minute"] for row in compared if row["status"] == "rounding_tie"]
        numeric = [abs(float(row["core"]) - float(row["legacy"])) for row in compared
                   if isinstance(row["core"], (int, float)) and not isinstance(row["core"], bool)
                   and isinstance(row["legacy"], (int, float)) and not isinstance(row["legacy"], bool)]
        summary[variable.name] = {
            "kind": variable.kind, "unit": variable.unit, "tolerance": variable.tolerance,
            "compared": len(compared), "mismatched": len(mismatched), "rounding_tie_minutes": ties,
            "first_mismatch_minute": mismatched[0]["minute"] if mismatched else None,
            "max_abs_diff": _rounded(max(numeric)) if numeric else None,
            "samples": {str(row["minute"]): [_rounded(row["legacy"]), _rounded(row["core"])]
                        for row in series if row["minute"] in SAMPLE_MINUTES},
        }
    return summary


def mismatching(summary: Mapping[str, Mapping]) -> tuple[str, ...]:
    return tuple(sorted(name for name, entry in summary.items() if entry["mismatched"]))
