"""Phase 2 shadow core, P2C: the approved physiological constraints (Level 1, qualitative).

The decisions KD-S1, KD-S2 and KD-S4 fix directions, memory and saturation, not numbers:
every gain they touch is provisional (``clinical_core.derived.PARAMETERS``). These tests
assert only what the decisions approve -- directionality, monotonicity, memory,
saturation, no impossible state -- on GI bleeding and on synthetic states of other
families, so that nothing here is tuned to the GI-bleed golden.
"""
from dataclasses import dataclass

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, RhythmState, SourceKind, run)
from clinical_core.derived import lactate_excess
from clinical_core.modules import GIHaemorrhage

BLEEDING = Anchors(case_id="synthetic_gi", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0,
                   crt_s=5.0, lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21,
                   rhythm=RhythmState.sinus(124.0), consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.009, 0.8, 0.1)


@dataclass(frozen=True)
class Step(Contributor):
    """A one-off change of one channel at one minute (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_step"
    id: str
    channel: str
    at_minute: int
    amount: float

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), self.amount, self.source, minute,
                                                 f"synthetic step of {self.channel}"),))


@dataclass(frozen=True)
class Loss(Contributor):
    """Volume lost at a constant rate until it stops, without changing Hb (test only)."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_loss"
    id: str
    per_minute: float
    stop_minute: int

    def contribute(self, state, minute, signals, anchors, profile):
        if minute > self.stop_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.V, -self.per_minute, self.source, minute, "volume loss"),))


@dataclass(frozen=True)
class Restore(Contributor):
    """Gives back, in one minute, all the volume lost so far (an idealised resuscitation, test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_restore"
    id: str
    at_minute: int
    surplus_ml: float = 0.0

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.V, -state.V + self.surplus_ml, self.source, minute,
                                                 "volume restored"),))


# KD-S1 -- oxygen-delivery debt, lactate and RR -------------------------------------------

def test_kd_s1_untreated_shock_builds_a_debt_and_lactate_follows_it_with_a_lag():
    trajectory = run(BLEEDING, (BLEED,), 120)
    debts = [state.D for state in trajectory.states]
    excess = [lactate_excess(state) for state in trajectory.states]
    assert all(later > earlier for earlier, later in zip(debts[1:], debts[2:])), "D rises progressively"
    assert all(later > earlier for earlier, later in zip(excess[2:], excess[3:])), "lactate rises"
    profile = trajectory.profile
    # Lactate is produced from the previous minute's debt: from minute 3 on, it lags behind it.
    for state, held in zip(trajectory.states[3:], excess[3:]):
        steady = profile.lactate_per_output_deficit * state.D / profile.debt_clearance_tau_min
        assert 0 < held < steady, "lactate lags the debt that produces it"


def test_kd_s1_abrupt_restoration_leaves_the_debt_and_the_lactate_to_clear_gradually():
    trajectory = run(BLEEDING, (Loss("loss", 2.5, 60), Restore("restore", 61)), 300)
    derived = trajectory.derived()
    at = 61
    assert trajectory.states[at].V == 0.0, "perfusion restored at once"
    assert trajectory.states[at].D > 0 and derived[at].lactate > BLEEDING.lactate
    debts = [state.D for state in trajectory.states[at:at + 30]]
    assert all(later < earlier for earlier, later in zip(debts, debts[1:])), "D repays gradually, not at once"
    assert derived[at + 10].lactate > BLEEDING.lactate, "lactate does not normalise at once"


def test_kd_s1_residual_lactate_keeps_rr_up_for_a_while_and_clearing_it_never_causes_bradypnoea():
    """Corrected perfusion, even beyond arrival: RR trends down and never below the ventilatory part."""
    trajectory = run(BLEEDING, (Loss("loss", 2.5, 60), Restore("restore", 61, surplus_ml=600.0)), 600)
    derived = trajectory.derived()
    after = [item.respiratory_rate for item in derived[61:]]
    assert after[0] > after[-1], "RR is transiently higher while lactate is still elevated"
    assert derived[-1].lactate < BLEEDING.lactate, "the debt is repaid beyond arrival"
    floor = min(BLEEDING.respiratory_rate, trajectory.profile.rr_ventilatory_floor)
    assert min(item.respiratory_rate for item in derived) >= floor >= 10


@pytest.mark.parametrize("arrival_rr,arrival_lactate", [(14.0, 9.0), (26.0, 4.4), (30.0, 12.0), (18.0, 1.0)])
def test_kd_s1_no_lactate_clearance_ever_takes_rr_below_ten(arrival_rr, arrival_lactate):
    arrival = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "respiratory_rate": arrival_rr,
                         "lactate": arrival_lactate})
    derived = run(arrival, (Restore("restore", 1, surplus_ml=900.0),), 720).derived()
    assert derived[0].respiratory_rate == arrival_rr, "anchored to arrival"
    assert min(item.respiratory_rate for item in derived) >= min(arrival_rr, 10.0)


def test_kd_s1_shock_and_respiratory_disease_add_rather_than_overwrite():
    disease = Step("respiratory_disease", "W", 1, 0.3)
    none, shock = run(BLEEDING, (), 90).derived(), run(BLEEDING, (BLEED,), 90).derived()
    lung, both = run(BLEEDING, (disease,), 90).derived(), run(BLEEDING, (BLEED, disease), 90).derived()
    for minute in (30, 60, 90):
        assert both[minute].respiratory_rate > max(shock[minute].respiratory_rate, lung[minute].respiratory_rate)
        metabolic = shock[minute].respiratory_rate - none[minute].respiratory_rate
        assert both[minute].respiratory_rate - lung[minute].respiratory_rate == pytest.approx(metabolic)


def test_kd_s1_bradypnoea_comes_only_from_an_explicit_ventilation_mechanism():
    depressed = run(BLEEDING, (Step("opioid_drive", "W", 1, -0.7),), 5).derived()
    assert depressed[-1].respiratory_rate < 10, "a W mechanism (depressed drive) may cause bradypnoea"
