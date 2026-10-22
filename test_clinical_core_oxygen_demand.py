"""Phase 2 shadow core, P2E-2: metabolic oxygen demand as typed auxiliary input.

delivery = f(output, Hb, SaO2); demand = the case's baseline x the factors sources declare for
the minute; deficit = max(0, demand - delivery); D integrates the deficit and repays at its
own rate. These tests assert the structure only: every factor here is a synthetic probe value,
not a sepsis, fever or seizure multiplier (those are TBD), and no family is migrated.
"""
import math
from dataclasses import dataclass

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, ProvenanceError, SourceKind,
                           run, scenario_from_dict, scenario_to_dict)
from clinical_core.bands import ARRIVAL, Demand, Drift
from clinical_core.derived import DEFAULT_PROFILE, OXYGEN_DEMAND, arrival_state, derive, lactate_baseline
from clinical_core.integration import OXYGEN_DEBT
from clinical_core.provenance import DemandModifier, Source
from clinical_core.state import CoreInvariantError, CoreState

NEUTRAL = Anchors(**ARRIVAL)
TAU = DEFAULT_PROFILE.debt_clearance_tau_min


def case(**declared):
    """The neutral synthetic arrival with case parameters declared as synthetic probes."""
    return Anchors(**{**ARRIVAL, **declared, "declared": {name: "synthetic_probe" for name in declared}})


def debts(trajectory):
    return [state.D for state in trajectory.states]


def deliveries(trajectory):
    return [item.delivery_rel for item in trajectory.derived()]


def test_more_demand_at_identical_delivery_never_improves_d():
    runs = {factor: run(NEUTRAL, (Demand("demand", 0, 60, factor),), 60) for factor in (0.8, 1.0, 1.2, 1.5)}
    reference = deliveries(runs[1.0])
    for trajectory in runs.values():
        assert deliveries(trajectory) == reference, "demand does not change delivery"
    for low, high in ((0.8, 1.0), (1.0, 1.2), (1.2, 1.5)):
        assert all(d_high >= d_low for d_low, d_high in zip(debts(runs[low]), debts(runs[high])))
    assert debts(runs[1.5])[-1] > debts(runs[1.2])[-1] > 0.0
    assert max(debts(runs[0.8])) == max(debts(runs[1.0])) == 0.0, "demand below delivery is no credit"


def test_more_delivery_at_identical_demand_reduces_the_accumulation_of_d():
    demand = Demand("demand", 0, 60, 1.3)
    runs = [run(NEUTRAL, (demand, Drift("hb", "hb", 0, 1, gain)), 60) for gain in (0.0, 1.0, 2.0)]
    for lower, higher in zip(runs, runs[1:]):
        assert all(d_up > d_down for d_down, d_up in zip(deliveries(lower)[1:], deliveries(higher)[1:]))
        assert all(d_more < d_less for d_less, d_more in zip(debts(lower)[2:], debts(higher)[2:]))


def test_elevated_demand_maintains_or_worsens_d_despite_preserved_or_higher_output():
    # Haemoglobin raises delivery to above arrival; output itself is untouched (preserved).
    trajectory = run(NEUTRAL, (Demand("demand", 0, 60, 1.3), Drift("hb", "hb", 0, 1, 1.3)), 60)
    derived = trajectory.derived()
    assert all(item.output_rel >= 1.0 for item in derived) and derived[-1].delivery_rel > 1.0
    assert all(later > earlier for earlier, later in zip(debts(trajectory)[1:], debts(trajectory)[2:]))
    # Higher output, from lower afterload, does not prevent it either (a synthetic sepsis-like probe).
    from clinical_core import bands
    rows = bands.probe("vasodilation_with_demand")
    arrival, during = rows[0], [row for row in rows if 0 < row["minute"] <= 60]
    assert all(row["output_rel"] > arrival["output_rel"] and row["D"] > 0.0 for row in during)
    assert during[-1]["D"] > during[0]["D"]


def test_removing_the_source_lets_d_repay_at_its_existing_rate():
    trajectory = run(NEUTRAL, (Demand("demand", 0, 30, 1.3),), 90)
    debt = debts(trajectory)
    assert debt[30] == max(debt)
    assert trajectory.states[30].aux.oxygen_demand == pytest.approx(1.3)
    assert trajectory.states[31].aux.oxygen_demand == NEUTRAL.metabolic_demand_baseline
    for minute in range(31, 91):
        assert debt[minute] == pytest.approx(debt[minute - 1] * (1.0 - 1.0 / TAU), rel=1e-12), \
            "no deficit: only the repayment D / tau_D acts"


def test_demand_changes_are_recorded_with_their_source():
    demand = Demand("demand", 0, 30, 1.3)
    trajectory = run(NEUTRAL, (demand,), 40)
    for record in trajectory.records:
        modifiers = record.demand
        debt = next(delta for delta in record.deltas if delta.source == OXYGEN_DEBT)
        if record.minute <= 30:
            assert [(item.factor, item.source) for item in modifiers] == [(1.3, demand.source)]
            assert debt.modulated_by == (demand.source,), "the debt names who changed its size"
        else:
            assert modifiers == () and debt.modulated_by == ()
    changes = [(record.minute, change.before, change.after, change.source)
               for record in trajectory.records for change in record.auxiliary if change.quantity == "oxygen_demand"]
    assert changes == [(1, 1.0, pytest.approx(1.3), OXYGEN_DEMAND), (31, pytest.approx(1.3), 1.0, OXYGEN_DEMAND)]
    serialized = trajectory.records[0].to_dict()["demand"]
    assert serialized == [{"type": "demand", "factor": 1.3, "kind": "disease", "source": demand.source.to_dict(),
                           "minute": 1, "description": "probe: declared factor on oxygen demand"}]


def test_factors_multiply_and_the_order_of_contributors_does_not_matter():
    disease, transient = Demand("sepsis_like", 0, 20, 1.2), Demand("seizure_like", 0, 20, 1.5, "transient")
    forward, backward = run(NEUTRAL, (disease, transient), 20), run(NEUTRAL, (transient, disease), 20)
    assert forward.digest() == backward.digest()
    assert forward.states[-1].aux.oxygen_demand == pytest.approx(1.8)
    assert {item.kind for item in forward.records[0].demand} == {"disease", "transient"}


def test_demand_survives_replay():
    scenario = scenario_to_dict(NEUTRAL, (Demand("demand", 0, 30, 1.3), Drift("hb", "hb", 0, 1, 0.5)), 45)
    anchors, contributors, minutes, profile = scenario_from_dict(scenario)
    original = run(NEUTRAL, (Demand("demand", 0, 30, 1.3), Drift("hb", "hb", 0, 1, 0.5)), 45)
    replayed = run(anchors, contributors, minutes, profile)
    assert replayed.digest() == original.digest()
    last = original.states[-1]
    assert CoreState.from_dict(last.to_dict()) == last


@dataclass(frozen=True)
class Impostor(Contributor):
    """Declares a demand factor in another source's name, or for another minute (test only)."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_demand_impostor"
    id: str
    other_minute: bool = False

    def contribute(self, state, minute, signals, anchors, profile):
        if self.other_minute:
            return Contribution(demand=(DemandModifier(1.2, "disease", self.source, minute + 1, "wrong minute"),))
        return Contribution(demand=(DemandModifier(1.2, "disease", Source(SourceKind.DISEASE_MODULE, "sepsis"),
                                                   minute, "someone else's demand"),))


@dataclass(frozen=True)
class NotAModifier(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "test_demand_not_a_modifier"
    id: str

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(demand=(ChannelDelta(Channel.D, 1.0, self.source, minute, "a delta posing as demand"),))


@pytest.mark.parametrize("contributor", [Impostor("impostor"), Impostor("late", other_minute=True),
                                         NotAModifier("delta")])
def test_only_a_source_declares_its_own_demand_for_its_minute(contributor):
    with pytest.raises(ProvenanceError):
        run(NEUTRAL, (contributor,), 1)


@pytest.mark.parametrize("factor,kind", [(0.0, "disease"), (-1.0, "disease"), (math.nan, "disease"),
                                         (math.inf, "disease"), (True, "disease"), (1.2, "fever")])
def test_a_demand_factor_is_positive_finite_and_of_a_declared_kind(factor, kind):
    with pytest.raises(ProvenanceError):
        DemandModifier(factor, kind, Source(SourceKind.DISEASE_MODULE, "x"), 1, "probe")


def test_delivery_above_demand_is_no_credit():
    trajectory = run(NEUTRAL, (Drift("hb", "hb", 0, 1, 2.0), Drift("fluid", "V", 0, 1, 300.0)), 120)
    assert deliveries(trajectory)[-1] > 1.0
    assert max(debts(trajectory)) == min(debts(trajectory)) == 0.0
    assert all(item.lactate == NEUTRAL.lactate for item in trajectory.derived())


def test_a_contributor_cannot_take_d_below_zero():
    trajectory = run(NEUTRAL, (Drift("credit", "D", 0, 1, -5.0),), 2)
    assert debts(trajectory) == [0.0, 0.0, 0.0]
    clamps = [delta for delta in trajectory.records[0].deltas if delta.source.kind is SourceKind.CLAMP]
    assert [(delta.channel, delta.amount) for delta in clamps] == [(Channel.D, 5.0)], "never silent"


def test_a_declared_demand_baseline_puts_arrival_in_deficit():
    deficit = case(metabolic_demand_baseline=1.2)
    assert arrival_state(deficit).aux.oxygen_demand == 1.2
    assert derive(arrival_state(deficit), deficit).lactate == deficit.lactate, "the arrival reads as authored"
    trajectory = run(deficit, (), 60)
    assert all(later > earlier for earlier, later in zip(debts(trajectory), debts(trajectory)[1:]))
    assert debts(trajectory)[-1] < TAU * 0.2, "settling toward tau x the arrival deficit"
    assert max(debts(run(NEUTRAL, (), 60))) == 0.0, "undeclared, arrival is a fixed point"


def test_an_undeclared_or_impossible_demand_baseline_is_refused():
    with pytest.raises(CoreInvariantError, match="names no source"):
        Anchors(**{**ARRIVAL, "metabolic_demand_baseline": 1.2})
    for value in (0.0, -0.5):
        with pytest.raises(CoreInvariantError):
            case(metabolic_demand_baseline=value)


def test_a_declared_arrival_lactate_excess_clears_to_its_baseline_and_no_further():
    clearable = Anchors(**{**ARRIVAL, "lactate": 4.0, "arrival_lactate_excess": 2.0,
                           "declared": {"arrival_lactate_excess": "synthetic_probe"}})
    assert lactate_baseline(clearable) == 2.0
    derived = run(clearable, (), 600).derived()
    assert derived[0].lactate == 4.0, "the arrival reads as authored"
    lactates = [item.lactate for item in derived]
    assert all(later < earlier for earlier, later in zip(lactates, lactates[1:]))
    assert lactates[-1] > 2.0 and lactates[-1] == pytest.approx(2.0, abs=0.01)


def test_an_undeclared_or_impossible_arrival_lactate_excess_is_refused():
    with pytest.raises(CoreInvariantError, match="names no source"):
        Anchors(**{**ARRIVAL, "arrival_lactate_excess": 0.5})
    for value in (-0.1, ARRIVAL["lactate"] + 0.1):
        with pytest.raises(CoreInvariantError):
            case(arrival_lactate_excess=value)


def test_the_gi_golden_declares_neither_reference():
    import json
    from clinical_core.shadow import GOLDEN
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for scenario in golden["scenarios"].values():
        for name in ("metabolic_demand_baseline", "arrival_lactate_excess"):
            assert scenario["case_parameters"][name]["source"] == "default_unmapped"
            assert scenario["case_parameters"][name]["calibrated"] is False


# After the adversarial review of P2E ------------------------------------------------------------

@dataclass(frozen=True)
class LooseDemand(Contributor):
    """Returns something other than a tuple of DemandModifier records as its demand (test only)."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_loose_demand"
    id: str
    as_list: bool = False

    def contribute(self, state, minute, signals, anchors, profile):
        if self.as_list:
            return Contribution(demand=[DemandModifier(1.2, "disease", self.source, minute, "a list, not a tuple")])
        return Contribution(demand=(1.3,))


@pytest.mark.parametrize("as_list", [False, True])
def test_review_f6_malformed_demand_fails_as_a_provenance_error(as_list):
    with pytest.raises(ProvenanceError, match="DemandModifier"):
        run(NEUTRAL, (LooseDemand("loose", as_list),), 1)


def test_review_f7_a_factor_is_named_on_the_debt_only_when_it_changed_the_debt():
    def modulators(trajectory):
        return [next(d for d in record.deltas if d.source == OXYGEN_DEBT).modulated_by for record in trajectory.records]
    calm = Demand("calm", 0, 5, 0.8)
    assert modulators(run(NEUTRAL, (calm,), 5)) == [()] * 5, "no deficit either way: the factor changed nothing"
    # With delivery at 0.9 of arrival, baseline demand would leave a deficit; the factor 0.8 removes it.
    anaemic = (Drift("hb", "hb", 0, 1, -0.1 * NEUTRAL.hb), Demand("calm", 1, 6, 0.8))
    named = modulators(run(NEUTRAL, anaemic, 6))
    assert named[0] == () and all(item == (calm.source,) for item in named[2:])


def test_review_f5_debt_and_cleared_lactate_are_never_negative_and_time_constants_cover_the_step():
    from dataclasses import replace as _replace
    from clinical_core.state import AuxiliaryState
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(lactate_excess_mmol_l=-0.1)
    with pytest.raises(CoreInvariantError):
        arrival_state(NEUTRAL).evolve(D=-1.0)
    for name in ("lactate_clearance_tau_min", "debt_clearance_tau_min"):
        with pytest.raises(CoreInvariantError, match="one minute"):
            _replace(DEFAULT_PROFILE, **{name: 0.5})
