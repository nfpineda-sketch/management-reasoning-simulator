"""Phase 2 shadow core, P2E-3/4/5: terminal collapse, low-output pressure, pump failure and congestion.

Structure only. The collapse rule is off by default; the thresholds, limits and repayment
used here are synthetic test values, not a clinical arrest threshold or dwell time (TBD).
Since P2J-1 pressure is proportional to output x tone over the whole range (no knee). Nothing here is
tuned to the GI-bleed golden.
"""
import json
import math
from dataclasses import dataclass, replace

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, RhythmCode, RhythmState,
                           SourceKind, attribution, run, scenario_from_dict, scenario_to_dict)
from clinical_core.bands import ARRIVAL, Drift
from clinical_core.derived import (COLLAPSE, DEFAULT_PROFILE, LUNG_WATER_CLEARANCE, PRELOAD_CONGESTION,
                                   arrival_state, arterial_pressures, congestion_rate, derive)
from clinical_core.modules.rhythm_events import ScriptedRhythmEvent
from clinical_core.state import CoreInvariantError, UnresolvedBoundary

NEUTRAL = Anchors(**ARRIVAL)
#: Synthetic collapse rule: burden accrues below 40% of arrival output, transition at 10.
RULE = replace(DEFAULT_PROFILE, collapse_output_threshold=0.4, collapse_burden_limit=10.0)


def pump(to, start=0, stop=None):
    """P moved to ``to`` at minute ``start + 1`` and, if ``stop``, back to 1 at minute ``stop + 1``."""
    drop = (Drift("pump_down", "P", start, start + 1, to - 1.0),)
    return drop + ((Drift("pump_up", "P", stop, stop + 1, 1.0 - to),) if stop is not None else ())


def burdens(trajectory):
    return [state.aux.collapse_burden for state in trajectory.states]


# P2E-3 -- terminal collapse ------------------------------------------------------------------

def test_mild_transient_low_output_does_not_arrest():
    trajectory = run(NEUTRAL, pump(0.35, 0, 5), 60, RULE)
    assert all(state.R.pulse_present for state in trajectory.states)
    assert 0.0 < max(burdens(trajectory)) < RULE.collapse_burden_limit
    assert burdens(trajectory)[-1] == burdens(trajectory)[7], "held once output recovers (no repayment declared)"


def test_deeper_or_longer_low_output_accumulates_more_burden():
    shallow, deep = run(NEUTRAL, pump(0.3, 0, 5), 10, RULE), run(NEUTRAL, pump(0.2, 0, 5), 10, RULE)
    short, long_ = run(NEUTRAL, pump(0.3, 0, 4), 10, RULE), run(NEUTRAL, pump(0.3, 0, 8), 10, RULE)
    assert burdens(deep)[-1] > burdens(shallow)[-1] > 0.0
    assert burdens(long_)[-1] > burdens(short)[-1] > 0.0


def test_recovery_before_the_criterion_prevents_the_transition():
    held = run(NEUTRAL, pump(0.1, 0, 8), 120, RULE)
    assert all(state.R.pulse_present for state in held.states)
    assert max(burdens(held)) < RULE.collapse_burden_limit
    repaid = run(NEUTRAL, pump(0.1, 0, 8), 120, replace(RULE, collapse_repayment_tau_min=30.0))
    after = burdens(repaid)[10:]
    assert all(later < earlier for earlier, later in zip(after, after[1:])), "repaid when declared"
    # The same low output sustained crosses the criterion.
    assert not run(NEUTRAL, pump(0.1), 30, RULE).states[-1].R.pulse_present


def test_crossing_the_criterion_gives_a_coherent_pulseless_state_with_nothing_measurable():
    trajectory = run(NEUTRAL, pump(0.1), 40, RULE)
    at = next(state.minute for state in trajectory.states if not state.R.pulse_present)
    before, after = trajectory.states[at - 1], trajectory.states[at]
    assert burdens(trajectory)[at] >= RULE.collapse_burden_limit > burdens(trajectory)[at - 1]
    record = trajectory.records[at - 1]
    assert [(t.source, t.before, t.after.code) for t in record.transitions] == [(COLLAPSE, before.R, RhythmCode.PEA)]
    assert [(e.kind, e.source, e.severity) for e in record.events] == [("terminal_collapse", COLLAPSE, "critical")]
    assert after.terminal_since == at
    for state in trajectory.states[at:]:
        derived = derive(state, NEUTRAL, RULE)
        assert not derived.pulse_present and derived.output_rel == 0.0
        assert (derived.sbp, derived.dbp, derived.map, derived.spo2, derived.crt_s, derived.pulse_rate_bpm) == \
            (None,) * 6
        assert derived.consciousness_level == 3 and derived.respiratory_rate == 0.0
        assert state.aux.sympathetic_drive == 0.0 and state.aux.collapse_burden == burdens(trajectory)[at]


def test_pea_keeps_an_organized_rhythm_without_a_pulse_and_asystole_has_none():
    trajectory = run(NEUTRAL, pump(0.1), 40, RULE)
    at = next(state.minute for state in trajectory.states if not state.R.pulse_present)
    pea = trajectory.states[at].R
    shown = derive(trajectory.states[at - 1], NEUTRAL, RULE).monitor_rate_bpm
    assert (pea.code, pea.pulse_present, pea.output_factor, pea.rate_bpm) == (RhythmCode.PEA, False, 0.0, shown)
    assert derive(trajectory.states[at], NEUTRAL, RULE).monitor_rate_bpm == shown > 0, "the monitor still counts"
    flat = run(NEUTRAL, pump(0.1), 40, replace(RULE, collapse_terminal_rhythm="asystole")).states[-1]
    assert flat.R == RhythmState.asystole() and derive(flat, NEUTRAL, RULE).monitor_rate_bpm == 0.0


def test_the_collapse_rule_is_off_by_default_and_zero_output_still_stops_the_run():
    low = run(NEUTRAL, pump(0.1), 60)
    assert all(state.R.pulse_present for state in low.states) and max(burdens(low)) == 0.0
    loss = (Drift("loss", "V", 0, 1, -3000.0),)
    with pytest.raises(UnresolvedBoundary):
        run(NEUTRAL, loss, 2)
    with pytest.raises(UnresolvedBoundary):
        run(NEUTRAL, loss, 2, RULE), "output gone before the criterion is met: the boundary, not an invented rule"


def test_a_contributor_moving_the_rhythm_defers_the_collapse_by_one_minute():
    plain = run(NEUTRAL, pump(0.1), 40, RULE)
    at = next(state.minute for state in plain.states if not state.R.pulse_present)
    af = RhythmState(RhythmCode.AF, 110.0, 0.85, True)
    event = ScriptedRhythmEvent("af", at, af, "not applicable")
    trajectory = run(NEUTRAL, pump(0.1) + (event,), 40, RULE)
    assert trajectory.states[at].R == af
    assert trajectory.states[at + 1].R.code is RhythmCode.PEA and trajectory.states[at + 1].R.rate_bpm == 110.0
    assert trajectory.records[at].transitions[0].before == af


@pytest.mark.parametrize("changes", [{"collapse_output_threshold": 0.4}, {"collapse_burden_limit": 5.0},
                                     {"collapse_output_threshold": -0.4, "collapse_burden_limit": 5.0},
                                     {"collapse_output_threshold": 0.4, "collapse_burden_limit": 0.0},
                                     {"collapse_repayment_tau_min": 30.0},
                                     {"collapse_output_threshold": 0.4, "collapse_burden_limit": 5.0,
                                      "collapse_terminal_rhythm": "vf"},
                                     {"collapse_output_threshold": 1.0, "collapse_burden_limit": 5.0},
                                     {"collapse_output_threshold": 1.2, "collapse_burden_limit": 5.0},
                                     {"low_output_pressure_knee": 0.0}, {"low_output_pressure_knee": 1.0}])
def test_an_incomplete_or_impossible_rule_is_refused(changes):
    with pytest.raises(CoreInvariantError):
        replace(DEFAULT_PROFILE, **changes)


def test_a_collapse_run_replays_exactly():
    contributors = pump(0.1)
    data = json.loads(json.dumps(scenario_to_dict(NEUTRAL, contributors, 40, RULE)))
    anchors, rebuilt, minutes, profile = scenario_from_dict(data)
    assert profile == RULE
    assert run(anchors, rebuilt, minutes, profile).digest() == run(NEUTRAL, contributors, 40, RULE).digest()


def test_the_gi_golden_declares_no_collapse_rule():
    from clinical_core.shadow import GOLDEN, SCENARIOS, VARIANTS, run_shadow
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["parameters"]["collapse_output_threshold"][0] == "provisional"
    assert DEFAULT_PROFILE.collapse_output_threshold is None and DEFAULT_PROFILE.collapse_burden_limit is None
    result = run_shadow(VARIANTS[0], "untreated_60")
    assert max(burdens(result.core)) == 0.0 and all(state.R.pulse_present for state in result.core.states)


# P2E-4 -- pressure at low output ---------------------------------------------------------------

LEVELS = [1.3 - index * 0.0013 for index in range(1001)]   # pressure_rel from 1.3 down to 0


@pytest.mark.parametrize("arrival", [NEUTRAL, Anchors(**{**ARRIVAL, "sbp": 88.0, "dbp": 54.0}),
                                     Anchors(**{**ARRIVAL, "sbp": 40.0, "dbp": 20.0})])
def test_pressures_fall_monotonically_with_output_and_reach_zero(arrival):
    readings = [arterial_pressures(level, arrival, DEFAULT_PROFILE) for level in LEVELS]
    for (sbp_hi, dbp_hi), (sbp_lo, dbp_lo) in zip(readings, readings[1:]):
        assert sbp_lo <= sbp_hi and dbp_lo <= dbp_hi
        assert (sbp_lo + 2 * dbp_lo) / 3 <= (sbp_hi + 2 * dbp_hi) / 3
    assert all(sbp >= dbp >= 0.0 for sbp, dbp in readings)
    assert arterial_pressures(0.0, arrival, DEFAULT_PROFILE) == (0.0, 0.0), "no output, no pressure"
    assert max(arterial_pressures(1e-6, arrival, DEFAULT_PROFILE)) < 1.0, "it approaches zero"


def test_the_mapping_is_proportional_to_flow_times_tone_over_the_whole_range():
    """P2J-1: what P2E-4 made true below the knee holds everywhere, at the arrival's resistance."""
    for level in (1.3, 1.0, 0.8, 0.5, 0.4, 0.2, 0.05):
        assert arterial_pressures(level, NEUTRAL, DEFAULT_PROFILE) == (NEUTRAL.sbp * level, NEUTRAL.dbp * level)


def test_no_legacy_floor_remains_at_low_output():
    sbp, dbp = arterial_pressures(0.05, NEUTRAL, DEFAULT_PROFILE)
    old_floor = NEUTRAL.sbp - DEFAULT_PROFILE.sbp_per_pressure_deficit
    assert sbp < old_floor / 2, "the adopted linear relation alone never fell below arrival - 45"


def test_since_p2j1_the_adopted_linear_relation_and_the_knee_are_not_read():
    for level in (0.5, 0.8, 1.2):
        sbp, dbp = arterial_pressures(level, NEUTRAL, DEFAULT_PROFILE)
        assert (sbp, dbp) == (NEUTRAL.sbp * level, NEUTRAL.dbp * level)
        assert sbp != NEUTRAL.sbp - 45.0 * (1 - level), "the linear relation of P2E-4 is gone"
    for changes in ({"sbp_per_pressure_deficit": 30.0}, {"dbp_per_pressure_deficit": 10.0},
                    {"low_output_pressure_knee": 0.3}):
        assert arterial_pressures(0.7, NEUTRAL, replace(DEFAULT_PROFILE, **changes)) == arterial_pressures(
            0.7, NEUTRAL, DEFAULT_PROFILE)


def test_the_golden_runs_read_their_pressures_as_the_arrival_pressure_times_output_x_tone():
    from clinical_core.shadow import SCENARIOS, VARIANTS, run_shadow
    for variant in VARIANTS:
        for scenario in SCENARIOS:
            result = run_shadow(variant, scenario).core
            arrival = result.anchors
            for state, item in zip(result.states, result.derived()):
                assert item.pressure_rel == item.output_rel * state.T
                assert (item.sbp, item.dbp) == (arrival.sbp * item.pressure_rel, arrival.dbp * item.pressure_rel)


def test_tone_still_holds_diastolic_and_mean_pressure_without_meaning_perfusion():
    """Pressure is not perfusion: more tone, less output, higher DBP and MAP, more debt."""
    plain = run(NEUTRAL, pump(0.4), 30)
    squeezed = run(NEUTRAL, pump(0.4) + (Drift("tone", "T", 0, 1, 0.8),), 30)
    a, b = plain.derived()[-1], squeezed.derived()[-1]
    assert b.output_rel < a.output_rel and b.dbp > a.dbp and b.map > a.map
    assert b.delivery_rel < a.delivery_rel and squeezed.states[-1].D > plain.states[-1].D
    assert b.crt_s > a.crt_s, "refill reads output, not pressure"


# P2E-5 -- pump failure and congestion ---------------------------------------------------------

def lung_water(trajectory):
    return [state.L for state in trajectory.states]


def test_a_low_pump_with_low_volume_creates_no_lung_water():
    trajectory = run(NEUTRAL, pump(0.5) + (Drift("loss", "V", 0, 1, -500.0),), 120)
    assert max(lung_water(trajectory)) == 0.0
    assert not any(delta.source == PRELOAD_CONGESTION for record in trajectory.records for delta in record.deltas)


def test_the_same_added_preload_congests_more_with_less_reserve():
    fluid = (Drift("fluid", "V", 0, 1, 1500.0),)
    final = {}
    for reserve in (1.0, 0.6, 0.3):
        arrival = Anchors(**{**ARRIVAL, "pump_reserve": reserve, "declared": {"pump_reserve": "synthetic_probe"}})
        final[reserve] = run(arrival, fluid, 60).states[-1].L
    assert final[1.0] == 0.0 < final[0.6] < final[0.3]


def test_a_failing_pump_tolerates_less_added_preload_before_it_congests():
    arrival = Anchors(**{**ARRIVAL, "pump_reserve": 0.5, "declared": {"pump_reserve": "synthetic_probe"}})

    def tolerated(pump_level):
        state = arrival_state(arrival).evolve(P=pump_level)
        low, high = 0.0, 3000.0
        for _ in range(60):
            middle = (low + high) / 2
            low, high = (middle, high) if congestion_rate(state.evolve(V=middle), arrival, DEFAULT_PROFILE) == 0 \
                else (low, middle)
        return high

    assert tolerated(0.7) < tolerated(1.0) < 3000.0, "low P alone writes no L, but lowers the preload it tolerates"


@dataclass(frozen=True)
class CapillaryLeak(Contributor):
    """A declared disease source of lung water (test only): a leak, not preload."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_capillary_leak"
    id: str
    per_minute: float

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(deltas=(ChannelDelta(Channel.L, self.per_minute, self.source, minute,
                                                 "declared capillary leak into the lungs"),))


def test_lung_water_sources_are_distinguishable_by_provenance():
    arrival = Anchors(**{**ARRIVAL, "pump_reserve": 0.3, "declared": {"pump_reserve": "synthetic_probe"}})
    leak = CapillaryLeak("capillary_leak", 0.005)
    trajectory = run(arrival, (leak, Drift("fluid", "V", 0, 1, 1500.0)), 90)
    by_source = attribution(trajectory.records, Channel.L)
    assert set(by_source) == {leak.source.key, PRELOAD_CONGESTION.key, LUNG_WATER_CLEARANCE.key}
    assert by_source[leak.source.key] == pytest.approx(0.005 * 90)
    assert by_source[PRELOAD_CONGESTION.key] > 0 > by_source[LUNG_WATER_CLEARANCE.key]
    assert math.fsum(by_source.values()) == pytest.approx(trajectory.states[-1].L)
    only_leak = attribution(run(NEUTRAL, (leak,), 90).records, Channel.L)
    assert PRELOAD_CONGESTION.key not in only_leak, "a leak is not counted as preload congestion"
