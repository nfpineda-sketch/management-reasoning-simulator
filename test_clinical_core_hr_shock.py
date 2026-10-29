"""Phase 2 shadow core, P2I-2AF: HR acute-shock drive and smooth sinus saturation.

These tests pin the faculty decisions as frozen before evaluation: no arrival residual (the arrival HR is predicted from
the arrival physiology and its mismatch reported; the authored HR reaches no dynamics); the acute drive is the
acute_deficit_to_sympathetic_gain times the effective deficit over demand, 0 at no deficit and resolving with it; the
memory is debt_to_sympathetic_gain x D, read with D's latent scale; tau_D only repays D; the sinus increment saturates
smoothly toward the ceiling (tanh, never a clip); the rhythm stays authoritative; HR reaches no D, lactate or RR; the
candidate points, flags, invariants and verdict rule were frozen before any HR outcome; the legacy HR is read only after
the verdict and the P2F region never.
"""
import ast
import inspect
import json
import math
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import derived, gi_reference, lactate_slice
from clinical_core import hr_shock as hk
from clinical_core import hr_structure as hs
from clinical_core import lactate_rebuild as lr
from clinical_core.bands import Drift
from clinical_core.derived import DEFAULT_PROFILE, CoreProfile, derive
from clinical_core.integration import run
from clinical_core.modules.rhythm_events import ScriptedRhythmEvent
from clinical_core.state import RhythmCode, RhythmState
from test_clinical_core_lactate_rebuild import OFF_GRID, OFF_GRID_UNIT

ROOT = hk.ROOT
SOURCE = ROOT / "clinical_core" / "hr_shock.py"
#: The P2I-2AF freeze: faculty decisions, the P2I-2AD and P2I-2AE records, the residual audit, the candidate points of
#: both gains and the ceiling, the mismatch rule, the scenarios, the factorization, the scan, the flags, the invariants,
#: the legacy and verdict rules, the next-package design, the policy and every clinical_core source but the downstream
#: reports, committed before any HR outcome was evaluated.
FROZEN_DIGEST = "70106108285ced1556e746548fa79480d903a0495f6f65b6792cb17d9155eb2d"
CASES = hk.CASES
FALLING = (Drift("pump", "P", 0, 90, -0.005),)


def _anchors(case=CASES[0], intrinsic="midpoint", debt="midpoint", delivery="midpoint"):
    return hk.analysis_anchors(case, intrinsic, debt, delivery)


def _profile(acute=None, debt=None, ceiling=None, **changes):
    return replace(hk.analysis_profile(acute, debt, ceiling), **changes)


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_records_are_the_committed_ones():
    assert hs.p2i2ad_record()["freeze_digest"] == hs.P2I2AD_DIGEST
    assert hk.p2i2ae_record()["freeze_digest"] == hk.P2I2AE_DIGEST


def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/hr_shock.py", "clinical_core/derived.py", "clinical_core/integration.py"} <= set(sources)
    assert "clinical_core/hr_shock_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert hk.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(hk.FACULTY) == {"decided", "shock_recoverable", "acute_signal", "d_scale", "saturation", "intrinsic",
                               "scope"}
    assert "no fixed case-specific offset" in hk.FACULTY["shock_recoverable"]
    assert "never an anchor" in hk.FACULTY["d_scale"] and "no hard clip" in hk.FACULTY["saturation"]


# The core: the acute drive, the memory, the saturation ----------------------------------------------------------------

def test_the_new_parameters_are_their_own_and_provisional():
    profile = CoreProfile()
    assert profile.acute_deficit_to_sympathetic_gain == 0.0 and profile.sinus_rate_ceiling_bpm == 175.0
    for name in ("acute_deficit_to_sympathetic_gain", "sinus_rate_ceiling_bpm"):
        status, text = derived.PARAMETERS[name]
        assert status == derived.PROVISIONAL and ("not approved" in text or "nothing is chosen here" in text)
    with pytest.raises(derived.CoreInvariantError):
        replace(DEFAULT_PROFILE, sinus_rate_ceiling_bpm=0.0)


def test_the_target_has_no_arrival_residual_and_reads_the_current_state_only():
    audit = hk.live_audit()
    assert audit["no_residual"] and audit["acute_term"] and audit["no_tau_d_in_hr"] and audit["smooth_saturation"]
    assert not hasattr(derived, "arrival_non_debt_drive")
    # The authored arrival HR reaches no dynamics: same physiology, other authored HR, the same run.
    assert hk.authored_hr_probe()["holds"]


def test_the_acute_contribution_is_gain_times_deficit_over_demand_and_zero_at_no_deficit():
    anchors = _anchors()
    arrival = derived.arrival_state(anchors, _profile())
    for acute in (0.0, 0.5, 3.0, 20.0):
        profile = _profile(acute=acute)
        signal = derived.acute_deficit_signal(arrival, anchors, profile)
        base = derived.sympathetic_target(arrival, anchors, _profile(acute=0.0))
        assert derived.sympathetic_target(arrival, anchors, profile) - base == pytest.approx(acute * signal, abs=1e-12)
    restored = arrival.evolve(hb=anchors.hb * 2.0, D=0.0)
    assert derived.acute_deficit_signal(restored, anchors, _profile()) == 0.0
    assert derived.sympathetic_target(restored, anchors, _profile(acute=20.0)) == derived.sympathetic_target(
        restored, anchors, _profile(acute=0.0))


def test_a_larger_deficit_or_debt_never_lowers_the_drive_or_hr():
    for case in CASES:
        anchors = _anchors(case)
        profile = _profile()
        arrival = derived.arrival_state(anchors, profile)
        for states in ([arrival.evolve(hb=anchors.hb - d) for d in (0.0, 0.3, 1.0, 2.5)],
                       [arrival.evolve(D=d) for d in (0.0, 1.0, 20.0, 60.0, 600.0)]):
            drives = [derived.sympathetic_after_minute(arrival, s, anchors, profile) for s in states]
            rates = [derive(s.evolve(aux=replace(s.aux, sympathetic_drive=d)), anchors, profile).pulse_rate_bpm
                     for s, d in zip(states, drives)]
            assert drives == sorted(drives) and rates == sorted(rates)


def test_tau_d_at_fixed_d_changes_no_drive_and_no_hr():
    anchors = _anchors()
    arrival = derived.arrival_state(anchors, _profile())
    for debt in (0.0, 20.0, 300.0):
        readings = {(derived.sympathetic_target(arrival.evolve(D=debt), anchors, _profile(debt_clearance_tau_min=t)),
                     derived.sympathetic_after_minute(arrival, arrival.evolve(D=debt), anchors,
                                                      _profile(debt_clearance_tau_min=t)))
                    for t in (1.0, 30.0, 60.0, 120.0, 480.0)}
        assert len(readings) == 1


def test_d_scale_and_debt_gain_are_one_observable():
    assert hk.d_scale_probe()["holds"]
    anchors = _anchors()
    for c in (0.1, 2.0, 7.0):
        scaled = replace(anchors, arrival_oxygen_debt=c * anchors.arrival_oxygen_debt)
        a = run(anchors, FALLING, 60, _profile()).derived()
        b = run(scaled, FALLING, 60, _profile(debt=hk.ANCHOR["debt"] / c,
                                              debt_per_delivery_deficit=c * DEFAULT_PROFILE.debt_per_delivery_deficit)
                ).derived()
        assert max(abs(x.pulse_rate_bpm - y.pulse_rate_bpm) for x, y in zip(a, b)) <= 1e-9


def test_the_saturation_is_smooth_monotone_linear_near_zero_and_below_the_reserve():
    profile = _profile(ceiling=150.0)
    for base in (60.0, 80.0, 100.0, 124.0):
        reserve = 150.0 - base
        drives = [i * 0.01 for i in range(10001)]
        values = [derived.sympathetic_increment(d, base, 0.0, profile) for d in drives]
        assert values[0] == 0.0 and all(b >= a for a, b in zip(values, values[1:]))
        # Below the reserve wherever tanh is below 1 in floating point (unconstrained < 19 reserves); never above.
        assert all(v < reserve for d, v in zip(drives, values) if 25.0 * d < 18.0 * reserve)
        assert all(v <= reserve for v in values) and values[-1] > 0.99 * reserve
        assert max(b - a for a, b in zip(values, values[1:])) <= 25.0 * 0.01 + 1e-12, "Lipschitz: no jump"
        assert values[1] / (25.0 * 0.01) == pytest.approx(1.0, abs=1e-4), "slope 1 at zero"
    assert "math.tanh" in inspect.getsource(derived.sympathetic_increment)
    with pytest.raises(derived.CoreInvariantError, match="not below the sinus-rate ceiling"):
        derived.sympathetic_increment(1.0, 175.0, 0.0, DEFAULT_PROFILE)


def test_the_arrival_is_predicted_and_its_mismatch_reported():
    anchors = _anchors()
    split = derived.heart_rate_decomposition(anchors, _profile())
    state = derived.arrival_state(anchors, _profile())
    assert split["predicted_arrival_hr"] == derive(state, anchors, _profile()).pulse_rate_bpm
    assert split["mismatch_bpm"] == split["predicted_arrival_hr"] - anchors.hr
    assert split["acute_bpm"] + split["debt_bpm"] == pytest.approx(split["saturated_bpm"])
    derived.check_arrival_reconstruction(anchors, _profile())  # every other authored value stays exact


def test_hr2_resolves_an_arrival_share_and_leaves_an_arrival_at_intrinsic_there():
    """With no residual, an arrival with no debt and no deficit drive (default acute gain 0) sits at its intrinsic rate:
    HR2 asks it to end there (HR4 forbids below), and still asks an arrival with a share to end below it."""
    from clinical_core import calibration
    from clinical_core import decision_pack as dp
    for debt, delivery, share in (("lower", "upper", False), ("upper", "lower", True)):
        candidate = replace(dp.MIDDLE, debt=debt, delivery=delivery)
        arrivals = {case: gi_reference.candidate_anchors(case, calibration.case_values(case, candidate))
                    for case in CASES}
        for case, anchors in arrivals.items():
            first = run(anchors, (), 0, DEFAULT_PROFILE).derived()[0].pulse_rate_bpm
            assert (first > anchors.intrinsic_sinus_rate) is share, case
        calibration.check_hr(DEFAULT_PROFILE, arrivals)
    assert dp.assess(replace(dp.MIDDLE, debt="lower", delivery="upper"))["status"] == dp.ADMISSIBLE


def test_the_rhythm_stays_authoritative_and_non_sinus_arrivals_with_a_debt_run():
    anchors = _anchors()
    paced = run(anchors, FALLING + (ScriptedRhythmEvent("paced", 10, RhythmState(RhythmCode.PACED, 70.0, 1.0, True),
                                                        "probe"),), 30, _profile())
    assert {d.pulse_rate_bpm for d in paced.derived()[10:]} == {70.0}
    arrest = run(anchors, FALLING + (ScriptedRhythmEvent("pea", 10, RhythmState.pea(40.0), "probe"),), 20, _profile())
    assert all(d.pulse_rate_bpm is None for d in arrest.derived()[10:])
    probe = hk.non_sinus_probe()
    assert probe["status"] == "RESOLVED_BY_P2I2AF" and probe["classification"] == "GENERALIZATION_BLOCKER_ONLY"


def test_hr_reaches_no_output_delivery_debt_lactate_or_rr():
    anchors = _anchors()
    runs = [run(anchors, FALLING, 90, _profile(acute=a, debt=g, ceiling=c))
            for a, g, c in ((0.0, 0.0, 150.0), (hk.ACUTE[-1], hk.DEBT[-1], 200.0), (1.0, 0.01, 175.0))]
    readings = [[(v.output_rel, v.delivery_rel, v.lactate, v.respiratory_rate, s.D)
                 for s, v in zip(r.states, r.derived())] for r in runs]
    assert readings[0] == readings[1] == readings[2]


# The design (frozen before any HR outcome) ------------------------------------------------------------------------

def test_the_residual_is_audited_from_the_p2i2ae_record():
    assert hk.RESIDUAL_AUDIT["class"] == hk.CASE_CALIBRATION_OFFSET
    assert hk.RESIDUAL_AUDIT["case_specific"] and hk.RESIDUAL_AUDIT["persists_indefinitely"]
    amounts = hk.residual_amounts(hk.p2i2ae_record())
    assert amounts["gi_bleed_57m"]["residual_share_max"] == 1.0 and amounts["gi_bleed_72f"]["residual_share_max"] == 1.0


def test_the_candidate_points_follow_their_rules_and_read_no_outcome():
    acute, debt, ceiling = hk.acute_gain_design(), hk.debt_gain_design(), hk.ceiling_design()
    assert acute["low"] == 1.0 / (25.0 * 0.4) and debt["low"] == 1.0 / (25.0 * 60.0)
    for design in (acute, debt):
        points = design["points"]
        assert len(points) == 5 and points[0] == design["low"] and points[-1] == design["high"]
        ratios = [b / a for a, b in zip(points, points[1:])]
        assert max(ratios) - min(ratios) < 1e-12
    reserve = 150.0 - 60.0
    assert acute["high"] == pytest.approx(reserve * math.atanh(64.0 / reserve) / (25.0 * 0.15))
    assert debt["high"] == pytest.approx(reserve * math.atanh(64.0 / reserve) / (25.0 * 20.0))
    assert ceiling["ceilings"] == (150.0, 175.0, 200.0) and ceiling["above_authored_and_intrinsic"]
    assert ceiling["near_linear"] and ceiling["smallest_share_bpm"] == 12.0
    for function in (hk._gain_design, hk.ceiling_design, hk.arrival_support):
        body = inspect.getsource(function)
        for word in ("legacy", "debt_clearance_tau_min", "lactate", "run(", "trajectory"):
            assert word not in body, (function.__name__, word)
    assert hk.ANCHOR == {"acute": hk.ACUTE[2], "debt": hk.DEBT[2], "ceiling": 175.0, "intrinsic": "midpoint"}


def test_the_mismatch_rule_applies_no_tolerance_and_rejects_only_domain_violations():
    assert "No tolerance exists" in hk.MISMATCH_RULE and hk.BINS == (1.0, 5.0, 10.0, 20.0)
    surface = hk.mismatch_surface()
    assert surface["analytic_rejections"] == 0 and sum(len(t) for t in surface["table"].values()) == 2 * 3 * 5 * 6 * 6 * 3


def test_the_intrinsic_band_stays_a_candidate_range():
    assert hs.intrinsic_audit()["status"] == hs.STILL_VALID
    assert "STILL_VALID_CANDIDATE_RANGE" in hk.FACULTY["intrinsic"] and "no value approved" in hk.FACULTY["intrinsic"]


# The factorization (off-grid physiology) ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario", [hk.L1, hk.L2, hk.L3])
def test_hr_post_processes_exactly_as_the_core_on_an_off_grid_physiology(scenario):
    inputs = {"entry": {**OFF_GRID, **OFF_GRID_UNIT}, "bag": bf.bag(0.22, 0.07, 75.0),
              "point": (45.0, 1.5, 4e-4, 90.0, "upper", "midpoint", "lower")}
    for case in CASES:
        base = hk.full_run(inputs, case, scenario)
        for level, acute, gain, ceiling in (("midpoint", 0.0, 0.0, 150.0), ("lower", 3.3, 2e-3, 165.0),
                                            ("upper", 19.0, 0.12, 199.0)):
            changes = {"acute_deficit_to_sympathetic_gain": acute, "debt_to_sympathetic_gain": gain,
                       "sinus_rate_ceiling_bpm": ceiling}
            full = hk.full_run(inputs, case, scenario, level, changes)
            series = hk.hr_series(base, hs.intrinsic_levels(case)[level], acute, gain, ceiling)
            assert [p["drive"] for p in series] == [r["drive"] for r in full["rows"]], (case, level)
            assert [p["hr"] for p in series] == [r["hr"] for r in full["rows"]]
            assert [r["rr"] for r in full["rows"]] == [r["rr"] for r in base["rows"]]
            assert [r["D"] for r in full["rows"]] == [r["D"] for r in base["rows"]]


# Policy ------------------------------------------------------------------------------------------------------------

def test_the_flags_invariants_and_verdict_rule_are_declared_before_any_run():
    assert set(hk.FLAG_RULES) == {"HR_BELOW_INTRINSIC", "HR_ABOVE_CEILING", "NEGATIVE_INCREMENT",
                                  "ACUTE_WITHOUT_DEFICIT", "DRIVE_FALLS_FASTER_THAN_ITS_DECAY",
                                  "INSTANT_NORMALIZATION_AT_HAEMOSTASIS", "NO_DEBT_RECOVERY_AFTER_ADEQUACY",
                                  "ACUTE_PERSISTS_AFTER_ADEQUACY"}
    assert sorted(hk.INVARIANTS) == list(range(1, 13))
    assert "never a gate" in hk.VERDICT_RULE and hk.NEXT_DESIGN["status"] == "PREPARED_NOT_EXECUTED"


def test_the_legacy_hr_is_read_only_after_the_verdict_and_the_p2f_region_never():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    readers = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
               and "_legacy_run" in ast.unparse(node)}
    assert readers == {"legacy_reference"}
    with lr.LegacyLock():
        with pytest.raises(AssertionError, match="only after the verdict"):
            hk.legacy_reference({})
    body = inspect.getsource(hk.run)
    assert body.index("legacy_reference(") > body.index("verdict(audit") and "with lr.P2FGuard(), lr.LegacyLock():" in body
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("gi_candidates", "admissible", "region_runs", "p2f_rejection", "runnable"):
        assert not any(name in call for call in called), name


def test_nothing_is_selected_or_approved_and_no_pressure_or_rr_parameter_is_set():
    text = json.dumps(hk.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text
    assert DEFAULT_PROFILE == CoreProfile()
    source = SOURCE.read_text(encoding="utf-8")
    for word in ("sbp_per_pressure_deficit=", "rr_per_lactate=", "sympathetic_per_pressure_deficit=",
                 "rr_metabolic_max=", "lactate_clearance_tau_min=tau_l * "):
        assert word not in source
