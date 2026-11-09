"""P3-68D: the calibration-region preview is exact, computes a REGION, and touches no authority.

It is analysis infrastructure: faculty are asked about behaviour, the region follows from algebra, and
nothing here approves, selects or ranks a parameter point. These tests are what keeps that true.
"""
import ast
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

import gi_pressure_calibration_preview as preview

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "gi_pressure_calibration_preview.py"
CASES = ("gi_bleed_57m", "gi_bleed_72f")


# -- D1: the inverse is the exact inverse -------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("fraction", (0.30, 0.42, 0.5, 0.61, 0.70))
@pytest.mark.parametrize("scale", (600.0, 833.3333333333334, 1100.0, 1500.0))
def test_d1_the_inverse_round_trips_exactly(case, fraction, scale):
    sbp = preview.ARRIVAL[case]["sbp"]
    nu = preview.KAPPA / scale
    slope = preview.slope_per_100ml(nu, fraction, sbp)
    multiplier = preview.plateau_multiplier(fraction)
    assert preview.fraction_from_plateau(multiplier) == pytest.approx(fraction, abs=0, rel=1e-15)
    assert preview.nu_from_slope(slope, fraction, sbp) == pytest.approx(nu, abs=0, rel=1e-15)


def test_d1b_the_closed_form_is_the_frozen_core(monkeypatch):
    """The module's whole claim: in GI the frozen equation IS this closed form."""
    import runtime_shadow as rs
    monkeypatch.setenv(rs.FLAG, rs.MODE_SHADOW_COMPARE)
    import pilot_acceptance as acceptance
    from clinical_core import derived
    encounter = acceptance.Encounter(CASES[0])
    anchors = encounter.shadow.runner.anchors
    profile = encounter.shadow.runner.profile
    assert anchors.preload_fraction is None, "the GI case reads the profile's arrival position"
    nu = profile.volume_preload_kappa / profile.preload_curve_scale_ml
    fraction = profile.arrival_preload_fraction

    class _State:
        P = 1.0

    worst = 0.0
    for volume in (-400.0, -200.0, -50.0, 0.0, 50.0, 200.0, 500.0, 1000.0):
        _State.V = volume
        core = (derived.preload_position(_State, anchors, profile)
                / derived.preload_position(_State, anchors, profile, volume=0.0))
        worst = max(worst, abs(core - preview.g(volume, nu, fraction)))
    assert worst < 1e-12, worst


# -- D2: the interval mapping ------------------------------------------------------------------------

def test_d2_the_plateau_interval_maps_to_f_with_the_ends_swapped():
    out = preview.region(slope_low=8.0, slope_high=14.0, plateau_low=1.6, plateau_high=2.4,
                         case=CASES[0])
    low, high = out["fraction_from_plateau"]
    assert low == pytest.approx(1 / 2.4) and high == pytest.approx(1 / 1.6)
    assert low < high, "the map plateau -> f is decreasing, so the ends swap"
    # Every corner reproduces the faculty bound it came from.
    for corner in out["corners"]:
        assert corner["slope_per_100ml"] in (8.0, 14.0)
        assert preview.slope_per_100ml(corner["nu"], corner["fraction"],
                                       out["sbp_arrival"]) == pytest.approx(corner["slope_per_100ml"])
        assert corner["plateau_multiplier"] == pytest.approx(1 / corner["fraction"])


def test_d2b_an_interval_with_crossed_bounds_is_refused():
    with pytest.raises(ValueError):
        preview.region(slope_low=14.0, slope_high=8.0, plateau_low=1.6, plateau_high=2.4, case=CASES[0])
    with pytest.raises(ValueError):
        preview.region(slope_low=8.0, slope_high=14.0, plateau_low=2.4, plateau_high=1.6, case=CASES[0])
    with pytest.raises(ValueError):
        preview.plateau_multiplier(0.0)
    with pytest.raises(ValueError):
        preview.fraction_from_plateau(0.9)


# -- D3: an empty intersection is said -----------------------------------------------------------------

def test_d3_an_empty_intersection_is_explicit_and_not_nudged():
    # A plateau interval entirely above the declared region of the arrival position (f < 0.3).
    out = preview.region(slope_low=8.0, slope_high=14.0, plateau_low=4.0, plateau_high=6.0, case=CASES[0])
    assert out["status"] == preview.EMPTY, out
    assert "do not overlap" in out["why"]
    assert "corners" not in out, "an empty region has no corners to tempt anyone"
    assert preview.trajectory_envelope(out) == []
    # A slope interval whose implied scale is entirely outside the declared region.
    narrow = preview.region(slope_low=0.1, slope_high=0.2, plateau_low=1.9, plateau_high=2.1,
                            case=CASES[0])
    assert narrow["status"] == preview.EMPTY, narrow
    assert any(note.get("note") == preview.OUTSIDE for note in narrow["boundary_warnings"])


# -- D4: a region stays a region -----------------------------------------------------------------------

def test_d4_a_nonempty_region_is_preserved_as_a_region():
    out = preview.region(slope_low=8.0, slope_high=14.0, plateau_low=1.8, plateau_high=2.2,
                         case=CASES[0])
    assert out["status"] == preview.NONEMPTY
    assert len({round(c["fraction"], 12) for c in out["corners"]}) == 2, "two distinct f bounds"
    assert len({round(c["nu"], 15) for c in out["corners"]}) == 4, "four distinct corners"
    low, high = out["scale_over_kappa_span"]
    assert high > low, "the region has width in scale / kappa"
    assert out["geometry"] == "RECTANGULAR_IN_(m,f)_AND_CURVED_IN_(nu,f)"
    band = preview.trajectory_envelope(out)
    assert band, "a nonempty region implies a band over the GI volume range"
    arrival = next(row for row in band if row["delta_volume_ml"] == 0.0)
    assert arrival["sbp_low"] == pytest.approx(out["sbp_arrival"])
    assert arrival["sbp_high"] == pytest.approx(out["sbp_arrival"]), \
        "g(0) = 1 for every (nu, f): the band has ZERO width at arrival"
    away = next(row for row in band if row["delta_volume_ml"] == 400.0)
    assert away["sbp_high"] > away["sbp_low"], "away from arrival the region has width in mmHg"


def test_d4b_nothing_optimizes_ranks_or_picks_a_point():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.name for node in ast.walk(tree)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for forbidden in ("minimize", "optimize", "best", "fit", "midpoint", "rank", "score", "loss"):
        assert not any(forbidden in name for name in names), forbidden
    flat = source.lower()
    for forbidden in ("approved_snapshots", "faculty_approved", "scipy.optimize", "curve_fit"):
        assert forbidden not in flat, forbidden


# -- D5: the development point, in behavioural coordinates ---------------------------------------------

@pytest.mark.parametrize("case,slope,plateau", ((CASES[0], 10.56, 176.0), (CASES[1], 11.76, 196.0)))
def test_d5_the_committed_point_is_located_correctly(case, slope, plateau):
    point = preview.committed_in_behavioural_coordinates(case)
    assert point["fraction"] == 0.5 and point["scale_over_kappa_ml"] == pytest.approx(833.3333333333334)
    assert point["slope_sbp_per_100ml"] == pytest.approx(slope, abs=1e-9)
    assert point["plateau_sbp_mmhg"] == pytest.approx(plateau)
    assert point["plateau_multiplier"] == 2.0
    assert "legacy" in point["provenance"].lower(), "its provenance is stated, not hidden"
    # And it is NOT silently inside an arbitrary region.
    inside = preview.region(slope_low=slope - 1, slope_high=slope + 1, plateau_low=1.9,
                            plateau_high=2.1, case=case)
    assert inside["committed_location"] == "INSIDE", inside["committed_location"]
    outside = preview.region(slope_low=slope + 5, slope_high=slope + 9, plateau_low=1.9,
                             plateau_high=2.1, case=case)
    assert outside["committed_location"] == "OUTSIDE", outside["committed_location"]


def test_d5b_the_committed_point_is_never_a_default_answer():
    """``region`` has no default for either faculty interval: an answer must be supplied."""
    with pytest.raises(TypeError):
        preview.region(case=CASES[0])
    with pytest.raises(TypeError):
        preview.region(slope_low=8.0, slope_high=14.0, case=CASES[0])


# -- D6: no authority, by import and by AST ------------------------------------------------------------

def test_d6_the_module_never_touches_authority_or_the_frozen_core():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
    for forbidden in ("runtime_authority", "runtime_authority_store", "app", "family_engine"):
        assert not any(name == forbidden or name.startswith(f"{forbidden}.") for name in imported), \
            (forbidden, sorted(imported))
    # And NOT the frozen core either: the repository's isolation guard allows only the declared shadow
    # bridge to reach it, and an analysis module is not that bridge, so the faculty verdict is injected.
    assert not any("clinical_core" in name for name in imported), sorted(imported)
    # Nothing writes: no open(), no Path.write_text, no json.dump.
    calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for forbidden in ("open", "json.dump", "Path.write_text", "os.environ.__setitem__"):
        assert forbidden not in calls, forbidden
    assert "json.dumps" in calls, "it prints, it does not write"


def test_d6b_a_fresh_process_importing_the_module_loads_no_authority():
    code = ("import sys; import gi_pressure_calibration_preview as p; "
            "p.committed_in_behavioural_coordinates('gi_bleed_57m'); "
            "print(sorted(n for n in sys.modules if 'authority' in n))")
    out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True, text=True,
                         timeout=300)
    assert out.returncode == 0, out.stderr[-600:]
    assert out.stdout.strip().endswith("[]"), out.stdout


def _frozen_faculty_oracle(values):
    """The natural oracle: the frozen, read-only faculty filter. It lives in the TEST, not the module.

    This is the whole wrapper -- two calls into ``blood_constraints``, which is the repository's own
    operationalization of the faculty's approved envelopes. Nothing of it is reimplemented anywhere.
    """
    from clinical_core import blood_anchors, blood_constraints
    full = {**blood_anchors.REFERENCE, **values}
    return {case: blood_constraints.passes("U-OUT", case, blood_constraints.untreated(case, full),
                                           None, None)
            for case in blood_constraints.CASES}


def test_d6c_the_frozen_faculty_oracle_is_injected_not_reimplemented():
    """The module computes no envelope of its own, and cannot reach the filter by itself."""
    source = MODULE.read_text(encoding="utf-8")
    for forbidden in ("blood_constraints.passes", "blood_constraints.untreated", "import clinical_core",
                      "from clinical_core", "importlib"):
        assert forbidden not in source, forbidden
    with pytest.raises(TypeError):
        preview.untreated_output_verdict(833.3333333333334, 0.5)  # no oracle, no verdict
    verdict = preview.untreated_output_verdict(833.3333333333334, 0.5, oracle=_frozen_faculty_oracle,
                                               bleed_ml_per_min=2.5)
    assert set(verdict) == {"gi_bleed_57m", "gi_bleed_72f", "both"}
    assert all(isinstance(verdict[key], bool) for key in verdict)
    # Measured in P3-68B: at the reference bleed rate the committed point satisfies 72f and not 57m.
    assert verdict["gi_bleed_72f"] is True and verdict["gi_bleed_57m"] is False, verdict
    assert verdict["both"] is False


def test_d6d_the_committed_point_meets_the_envelope_at_exactly_one_tested_bleed_rate():
    """P3-68B's measurement, pinned: it is a fact about the development point, not a defect to fix."""
    rates = [1.0, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5, 4.0]
    both = [rate for rate in rates
            if preview.untreated_output_verdict(833.3333333333334, 0.5, oracle=_frozen_faculty_oracle,
                                                bleed_ml_per_min=rate)["both"]]
    assert both == [2.75], both


# -- D7: nothing else moved -----------------------------------------------------------------------------

def test_d7_the_phase_two_digest_and_the_snapshot_did_not_move():
    import runtime_authority as ra
    import runtime_shadow as rs
    assert rs.PHASE2_DIGEST == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert list(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    values = dict(dict(ra.APPROVED_SNAPSHOTS["gi_pressure_committed"])["parameters"])
    assert values == {"preload_curve_scale_ml": 833.3333333333334, "arrival_preload_fraction": 0.5,
                      "pump_preload_coupling": 1.0, "afterload_sensitivity": 0.3,
                      "low_output_pressure_knee": 0.5, "sbp_per_pressure_deficit": 45.0,
                      "dbp_per_pressure_deficit": 25.0}
    # And the preview's own copy of the development point agrees with the registry it describes.
    assert preview.COMMITTED["preload_curve_scale_ml"] == values["preload_curve_scale_ml"]
    assert preview.COMMITTED["arrival_preload_fraction"] == values["arrival_preload_fraction"]
