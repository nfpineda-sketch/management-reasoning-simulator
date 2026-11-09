"""P3-68D: the GI pressure calibration REGION preview. Analysis only, no authority, no approval.

    python -m gi_pressure_calibration_preview --committed
    python -m gi_pressure_calibration_preview --slope 8 14 --plateau 1.6 2.2

What this module is for: faculty are asked about clinically interpretable BEHAVIOUR, never about a
parameter. This turns their answers into the admissible parameter region, exactly, and shows where the
current development point falls. It computes a REGION; it never picks a point.

Why it is safe to add here: it lives OUTSIDE ``clinical_core`` and outside the authority registry, it
imports NEITHER the frozen core NOR any authority module, it writes nothing, and it approves nothing. A
test enforces each of those, and the repository's own isolation guard enforces the first: only the
declared shadow bridge may reach ``clinical_core``, and an analysis module is not that bridge, so the
faculty verdict is injected by the caller (``untreated_output_verdict``).

The closed form it inverts (P3-58, verified against ``clinical_core.derived`` to 2.2e-16 on the GI
courses, where the engine fixes P = 1, T = 1 and the rhythm factor 1, and neither GI case declares its
own arrival preload position):

    g(dV) = (1 - (1 - f) * exp(-nu * dV)) / f      SBP = SBP_arrival * g      DBP = DBP_arrival * g
    nu = volume_preload_kappa / preload_curve_scale_ml        (the ratio the registry declares)

Three facts this module keeps in front of the reader, because every one of them is a trap:

* g(0) = 1 for every (nu, f): the arrival pressure carries ZERO information about these parameters;
* near arrival the only visible combination is m = (1 - f) * nu / f;
* the asymptotic plateau is 1/f relative to arrival, so the plateau alone identifies f.
"""
from __future__ import annotations

import argparse
import json
import math

#: The Phase-2 declared region of the two coordinates, read as data (``clinical_core.calibration``).
SCALE_LOW, SCALE_CANONICAL, SCALE_HIGH = 600.0, 833.3333333333334, 1500.0
FRACTION_LOW, FRACTION_CANONICAL, FRACTION_HIGH = 0.3, 0.5, 0.7
#: ``volume_preload_kappa``: 1.0 today, and absent from the calibration registry (it has no declared
#: region). Only kappa / scale is identifiable, so it is carried explicitly and never hidden.
KAPPA = 1.0
#: The authored arrival pressures of the two certified GI cases. Clinical data; they convert the common
#: dimensionless curve into case-specific mmHg, and they constrain nothing by themselves.
ARRIVAL = {"gi_bleed_57m": {"sbp": 88.0, "dbp": 54.0}, "gi_bleed_72f": {"sbp": 98.0, "dbp": 62.0}}
#: The development-authority point. Descriptive only: it is NEVER a default answer for faculty, and its
#: own provenance is a legacy reconstruction (the registry's rationale for the scale).
COMMITTED = {"preload_curve_scale_ml": SCALE_CANONICAL, "arrival_preload_fraction": FRACTION_CANONICAL}

EMPTY = "EMPTY_INTERSECTION"
NONEMPTY = "NONEMPTY_REGION"
OUTSIDE = "OUTSIDE_THE_DECLARED_REGION"


# -- the forward map and its exact inverse -----------------------------------------------------------

def g(delta_volume_ml: float, nu: float, fraction: float) -> float:
    """The frozen core's GI pressure factor, relative to arrival."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("the arrival preload position is strictly between 0 and 1")
    if not nu > 0.0:
        raise ValueError("nu is positive")
    return (1.0 - (1.0 - fraction) * math.exp(-nu * delta_volume_ml)) / fraction


def slope_per_100ml(nu: float, fraction: float, sbp_arrival: float) -> float:
    """dSBP/d(dVol) at arrival, in mmHg per 100 mL of the volume coordinate."""
    return sbp_arrival * (1.0 - fraction) * nu / fraction * 100.0


def plateau_multiplier(fraction: float) -> float:
    """SBP_max / SBP_arrival = 1 / f."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("the arrival preload position is strictly between 0 and 1")
    return 1.0 / fraction


def fraction_from_plateau(multiplier: float) -> float:
    """The exact inverse of ``plateau_multiplier``."""
    if not multiplier > 1.0:
        raise ValueError("a plateau multiplier is above 1: the curve rises from arrival")
    return 1.0 / multiplier


def nu_from_slope(slope_per_100: float, fraction: float, sbp_arrival: float) -> float:
    """The exact inverse of ``slope_per_100ml`` at a given f."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("the arrival preload position is strictly between 0 and 1")
    return slope_per_100 / 100.0 * fraction / ((1.0 - fraction) * sbp_arrival)


def m_of(nu: float, fraction: float) -> float:
    """The near-arrival combination m = (1 - f) nu / f, per mL of the volume coordinate."""
    return (1.0 - fraction) * nu / fraction


# -- the region -------------------------------------------------------------------------------------

def region(*, slope_low: float, slope_high: float, plateau_low: float, plateau_high: float,
           case: str, scale_bounds: tuple = (SCALE_LOW, SCALE_HIGH),
           fraction_bounds: tuple = (FRACTION_LOW, FRACTION_HIGH)) -> dict:
    """The admissible region implied by two faculty intervals, intersected with the declared region.

    No optimization, no midpoint, no ranking and no best point: the four corners and the shape are
    returned as they come out of the algebra. An empty intersection is said, never nudged.
    """
    if slope_low > slope_high or plateau_low > plateau_high:
        raise ValueError("an interval's low bound is not above its high bound")
    sbp = float(ARRIVAL[case]["sbp"])
    # The plateau interval maps to f by a strictly decreasing bijection, so the ends swap.
    f_low_raw, f_high_raw = fraction_from_plateau(plateau_high), fraction_from_plateau(plateau_low)
    f_low = max(f_low_raw, float(fraction_bounds[0]))
    f_high = min(f_high_raw, float(fraction_bounds[1]))
    out = {
        "case": case, "sbp_arrival": sbp, "kappa": KAPPA,
        "faculty": {"slope_per_100ml": [slope_low, slope_high],
                    "plateau_multiplier": [plateau_low, plateau_high]},
        "fraction_from_plateau": [f_low_raw, f_high_raw],
        "fraction_after_declared_region": [f_low, f_high],
        "m_per_ml": [slope_low / 100.0 / sbp, slope_high / 100.0 / sbp],
        "geometry": "RECTANGULAR_IN_(m,f)_AND_CURVED_IN_(nu,f)",
        "why_curved": "nu = m f / (1 - f), so a rectangle in (m, f) is a curved quadrilateral in (nu, f)",
    }
    if f_low > f_high:
        out["status"] = EMPTY
        out["why"] = ("the plateau interval and the declared region of the arrival preload position "
                      "do not overlap")
        return out
    corners, scales = [], []
    for f in (f_low, f_high):
        for slope in (slope_low, slope_high):
            nu = nu_from_slope(slope, f, sbp)
            scale = KAPPA / nu
            corners.append({"fraction": f, "nu": nu, "scale_over_kappa_ml": scale,
                            "m_per_ml": m_of(nu, f), "slope_per_100ml": slope,
                            "plateau_multiplier": plateau_multiplier(f),
                            "plateau_sbp_mmhg": sbp * plateau_multiplier(f),
                            "inside_declared_scale": scale_bounds[0] <= scale <= scale_bounds[1]})
            scales.append(scale)
    out["corners"] = corners
    out["scale_over_kappa_span"] = [min(scales), max(scales)]
    out["scale_span_inside_declared"] = [max(min(scales), float(scale_bounds[0])),
                                         min(max(scales), float(scale_bounds[1]))]
    out["status"] = NONEMPTY if any(c["inside_declared_scale"] for c in corners) else EMPTY
    if out["status"] == EMPTY:
        out["why"] = "every corner's implied scale / kappa falls outside the declared Phase-2 region"
    out["boundary_warnings"] = _boundaries(out)
    out["committed_point"] = committed_in_behavioural_coordinates(case)
    out["committed_location"] = _where(out)
    return out


def _boundaries(out: dict) -> list:
    """What a reader must be told about this region, in the repository's own terms."""
    notes = []
    for corner in out.get("corners") or []:
        empty_at = math.log(1.0 - corner["fraction"]) / corner["nu"]
        notes.append({"fraction": corner["fraction"], "scale_over_kappa_ml": corner["scale_over_kappa_ml"],
                      "empty_point_delta_volume_ml": empty_at,
                      "note": "below this volume change the model's pressure reaches 0; the certified GI "
                              "courses visit about -430 mL"})
        if not corner["inside_declared_scale"]:
            notes.append({"fraction": corner["fraction"],
                          "scale_over_kappa_ml": corner["scale_over_kappa_ml"],
                          "note": OUTSIDE})
    return notes


def committed_in_behavioural_coordinates(case: str) -> dict:
    """The development point expressed as behaviour. Descriptive; never a default faculty answer."""
    sbp = float(ARRIVAL[case]["sbp"])
    dbp = float(ARRIVAL[case]["dbp"])
    f = float(COMMITTED["arrival_preload_fraction"])
    nu = KAPPA / float(COMMITTED["preload_curve_scale_ml"])
    return {"case": case, "nu": nu, "fraction": f, "m_per_ml": m_of(nu, f),
            "scale_over_kappa_ml": KAPPA / nu,
            "slope_sbp_per_100ml": slope_per_100ml(nu, f, sbp),
            "slope_dbp_per_100ml": slope_per_100ml(nu, f, dbp),
            "plateau_multiplier": plateau_multiplier(f),
            "plateau_sbp_mmhg": sbp * plateau_multiplier(f),
            "plateau_dbp_mmhg": dbp * plateau_multiplier(f),
            "provenance": "the scale's declared rationale is that it keeps the LEGACY slope, so this "
                          "point is a legacy reconstruction, not clinical evidence"}


def _where(out: dict) -> str:
    point = out["committed_point"]
    f_low, f_high = out["fraction_after_declared_region"]
    slope_low, slope_high = out["faculty"]["slope_per_100ml"]
    inside_f = f_low <= point["fraction"] <= f_high
    inside_slope = slope_low <= point["slope_sbp_per_100ml"] <= slope_high
    if inside_f and inside_slope:
        return "INSIDE"
    if abs(point["fraction"] - f_low) < 1e-12 or abs(point["fraction"] - f_high) < 1e-12 \
            or abs(point["slope_sbp_per_100ml"] - slope_low) < 1e-9 \
            or abs(point["slope_sbp_per_100ml"] - slope_high) < 1e-9:
        return "BOUNDARY"
    return "OUTSIDE"


def trajectory_envelope(out: dict, deltas: tuple = (-400.0, -200.0, 0.0, 200.0, 400.0)) -> list:
    """The SBP band the region implies at a few volume changes, for the certified GI range."""
    if out.get("status") != NONEMPTY:
        return []
    sbp = out["sbp_arrival"]
    rows = []
    for delta in deltas:
        values = [sbp * g(delta, c["nu"], c["fraction"]) for c in out["corners"]]
        rows.append({"delta_volume_ml": delta, "sbp_low": min(values), "sbp_high": max(values)})
    return rows


# -- the frozen faculty oracle, used and never duplicated --------------------------------------------

def untreated_output_verdict(scale_over_kappa_ml: float, fraction: float, *, oracle,
                             bleed_ml_per_min: float | None = None) -> dict:
    """Whether a point satisfies the faculty's approved untreated-output envelope, per GI case.

    This module imports NOTHING from the frozen core, by design and by the repository's own isolation
    guard: ``test_shadow_core_isolation`` allows only the declared shadow bridge to reach
    ``clinical_core``, and an analysis module is not that bridge. So the verdict is INJECTED. ``oracle``
    is a callable the caller supplies, taking the candidate values and returning
    ``{case: bool}``; the natural one is a two-line wrapper over the frozen, read-only
    ``blood_constraints`` filter, and the tests supply exactly that.

    Why the verdict matters here at all: that filter is the repository's own operationalization of the
    faculty's approved envelopes, it reads output and Hb and never SBP or a legacy trajectory, and in GI
    pressure_rel = output_rel -- so it is a verdict on the pressure trajectory obtained without ever
    fitting pressure. Nothing of it is reimplemented in this module.
    """
    values = {"preload_scale_over_kappa_ml": float(scale_over_kappa_ml),
              "preload_fraction": float(fraction)}
    if bleed_ml_per_min is not None:
        values["bleed_ml_per_min"] = float(bleed_ml_per_min)
    out = {str(case): bool(verdict) for case, verdict in dict(oracle(values)).items()}
    out["both"] = all(out.values()) if out else False
    return out


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--slope", nargs=2, type=float, metavar=("LOW", "HIGH"),
                        help="faculty interval for dSBP per 100 mL at arrival")
    parser.add_argument("--plateau", nargs=2, type=float, metavar=("LOW", "HIGH"),
                        help="faculty interval for SBP_max / SBP_arrival")
    parser.add_argument("--case", default=None, help="one GI case (default: both)")
    parser.add_argument("--committed", action="store_true", help="the development point as behaviour")
    args = parser.parse_args(argv)
    cases = [args.case] if args.case else sorted(ARRIVAL)
    if args.committed or not args.slope:
        print(json.dumps({case: committed_in_behavioural_coordinates(case) for case in cases},
                         indent=2, sort_keys=True))
    if args.slope and args.plateau:
        for case in cases:
            out = region(slope_low=args.slope[0], slope_high=args.slope[1],
                         plateau_low=args.plateau[0], plateau_high=args.plateau[1], case=case)
            out["trajectory_envelope"] = trajectory_envelope(out)
            print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
