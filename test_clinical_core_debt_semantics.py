"""Phase 2 shadow core, P2I-2AC: the oxygen debt D is accumulated oxygen-delivery debt.

Faculty decision (P2I-2AC): while the effective oxygen deficit is positive, D does not fall (production goes on,
repayment is suspended, dD >= 0); with no deficit it may repay, gradually, with tau_D. Nothing else changed: not the
deficit, not delivery or extraction, not tau_D, the gains or the lactate recurrence. Each minute reads the deficit the
integrator reads: the delivery at its start against its own demand. Every probe here is synthetic (declared pump
drifts on the neutral arrival), never a case.
"""
import json
import math
from dataclasses import replace

import pytest

from clinical_core import oxygen_probes as op
from clinical_core.bands import Drift
from clinical_core.derived import DEFAULT_PROFILE, derive, effective_delivery, effective_oxygen_deficit
from clinical_core.integration import OXYGEN_DEBT, run, scenario_from_dict, scenario_to_dict
from clinical_core.provenance import attribution
from clinical_core.state import Channel, CoreState

ANCHORS = op.NEUTRAL
#: The same neutral arrival with a declared synthetic arrival debt, so that repayment has something to repay.
INDEBTED = replace(ANCHORS, arrival_oxygen_debt=5.0,
                   declared={**dict(ANCHORS.declared), "arrival_oxygen_debt": "synthetic_probe"})
#: Reserve 1 and 2.5 (synthetic): the deficit is demand - reserve x delivery either way.
RESERVES = (1.0, 2.5)


def _profile(reserve):
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=reserve)


def _minutes(contributors, minutes, reserve, anchors=ANCHORS):
    """Per minute: (deficit the core's D update reads, D before, D after, the D deltas recorded)."""
    profile = _profile(reserve)
    trajectory = run(anchors, contributors, minutes, profile)
    out = []
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        delivery = effective_delivery(derive(before, anchors, profile).delivery_rel, anchors)
        deficit = effective_oxygen_deficit(after.aux.oxygen_demand, delivery, reserve)
        deltas = [delta for delta in record.deltas if delta.channel is Channel.D]
        out.append((deficit, before.D, after.D, deltas))
    return trajectory, out


# 1-3: a critical deficit, whether worsening, stable or improving, never lets D fall ----------------------------------

#: Delivery follows the pump here (demand 1): critical below 1 / reserve.
WORSENING = (Drift("pump", "P", 0, 90, -0.01),)
STABLE = (Drift("pump", "P", 0, 10, -0.07),)
IMPROVING = (Drift("pump", "P", 0, 10, -0.08), Drift("recovery", "P", 20, 50, 0.005))


@pytest.mark.parametrize("reserve", RESERVES)
def test_a_worsening_critical_deficit_never_lets_d_fall(reserve):
    _, minutes = _minutes(WORSENING, 90, reserve, INDEBTED)
    critical = [(e, a, b) for e, a, b, _ in minutes if e > 0.0]
    assert len(critical) >= 25, "the probe reaches a sustained critical deficit"
    rising = [e for e, _, _ in critical]
    assert rising[-1] > rising[0], "the deficit worsens"
    assert all(after > before for _, before, after in critical)


@pytest.mark.parametrize("reserve", RESERVES)
def test_a_stable_critical_deficit_never_lets_d_fall(reserve):
    reserve_profile = _profile(reserve)
    _, minutes = _minutes(STABLE, 90, reserve, INDEBTED)
    late = minutes[11:]
    assert all(e > 0.0 for e, _, _, _ in late), "the probe holds a critical deficit"
    assert max(e for e, *_ in late) - min(e for e, *_ in late) < 1e-9, "the deficit is stable"
    assert all(after >= before for _, before, after, _ in late)
    # It accrues at g x deficit every minute: no settling, no repayment hidden in the step.
    for e, before, after, _ in late:
        assert after - before == pytest.approx(reserve_profile.debt_per_delivery_deficit * e, abs=1e-12)


@pytest.mark.parametrize("reserve", RESERVES)
def test_an_improving_but_still_critical_deficit_never_lets_d_fall(reserve):
    _, minutes = _minutes(IMPROVING, 50, reserve, INDEBTED)
    improving = [(e, a, b) for e, a, b, _ in minutes[20:50]]
    assert all(e > 0.0 for e, _, _ in improving), "still critical while it improves"
    assert all(later[0] < earlier[0] for earlier, later in zip(improving, improving[1:])), "the deficit improves"
    assert all(after >= before for _, before, after in improving)


# 4-6: with no deficit D may repay, gradually, never below 0 ---------------------------------------------------------

RESTORED = (Drift("pump", "P", 0, 10, -0.08), Drift("restore", "P", 20, 21, 0.8))


@pytest.mark.parametrize("reserve", RESERVES)
def test_d_may_repay_once_the_deficit_reaches_zero(reserve):
    _, minutes = _minutes(RESTORED, 120, reserve)
    accrued = [after for e, _, after, _ in minutes if e > 0.0]
    assert accrued and max(accrued) > 0.0
    adequate = [(before, after) for e, before, after, _ in minutes if e == 0.0 and before > 0.0]
    assert adequate, "the deficit reaches zero with debt to repay"
    assert all(after < before for before, after in adequate)
    # The only minutes in which D falls are those with no deficit.
    assert all(e == 0.0 for e, before, after, _ in minutes if after < before)


@pytest.mark.parametrize("reserve", RESERVES)
def test_sustained_adequacy_repays_gradually_with_tau_d(reserve):
    profile = _profile(reserve)
    _, minutes = _minutes(RESTORED, 120, reserve)
    start = next(m for m, (e, before, _, _) in enumerate(minutes) if e == 0.0 and before > 0.0 and m > 20)
    tail = minutes[start:]
    assert all(e == 0.0 for e, *_ in tail), "adequacy is sustained to the end"
    keep = 1.0 - 1.0 / profile.debt_clearance_tau_min
    for e, before, after, _ in tail:
        assert after == pytest.approx(before * keep, rel=1e-12)
    d0, last = tail[0][1], tail[-1][2]
    assert last == pytest.approx(d0 * keep ** len(tail), rel=1e-9)
    assert 0.0 < last < d0, "gradual: not erased at once"
    largest_step = max((before - after) / before for _, before, after, _ in tail)
    assert largest_step == pytest.approx(1.0 / profile.debt_clearance_tau_min)


@pytest.mark.parametrize("reserve", RESERVES)
def test_d_is_never_negative(reserve):
    for contributors in ((), WORSENING, STABLE, IMPROVING, RESTORED, (Drift("pump", "P", 0, 30, 0.01),)):
        trajectory, minutes = _minutes(contributors, 120, reserve, INDEBTED)
        assert min(state.D for state in trajectory.states) >= 0.0
        assert all(after >= 0.0 for _, _, after, _ in minutes)
    # Without debt and without deficit nothing accrues and nothing is repaid below zero.
    trajectory, minutes = _minutes((), 60, reserve)
    assert {state.D for state in trajectory.states} == {0.0}


# 7: replay, serialization and provenance stay exact ----------------------------------------------------------------

@pytest.mark.parametrize("reserve", RESERVES)
def test_replay_serialization_and_provenance_are_exact(reserve):
    profile = _profile(reserve)
    arrival = INDEBTED
    contributors = RESTORED + (Drift("hb", "hb", 40, 60, -0.05),)
    original = run(arrival, contributors, 120, profile)
    stored = json.loads(json.dumps(scenario_to_dict(arrival, contributors, 120, profile)))
    replayed = run(*scenario_from_dict(stored))
    assert replayed.digest() == original.digest()
    middle = original.states[45]
    resumed = run(arrival, contributors, 75, profile, initial=CoreState.from_dict(json.loads(json.dumps(
        middle.to_dict()))))
    assert resumed.states[-1] == original.states[-1]
    _, minutes = _minutes(contributors, 120, reserve, arrival)
    for e, before, after, deltas in minutes:
        assert [delta.source for delta in deltas if delta.source.kind is OXYGEN_DEBT.kind] == [OXYGEN_DEBT]
        debt = next(delta for delta in deltas if delta.source == OXYGEN_DEBT)
        if e > 0.0:
            assert debt.amount == profile.debt_per_delivery_deficit * e and "not repaid" in debt.description
        else:
            assert debt.amount == -before / profile.debt_clearance_tau_min and "repayment" in debt.description
        assert after - before == pytest.approx(math.fsum(delta.amount for delta in deltas), abs=1e-12)
    total = math.fsum(attribution(original.records, Channel.D).values())
    assert original.states[-1].D - original.states[0].D == pytest.approx(total, abs=1e-9)
