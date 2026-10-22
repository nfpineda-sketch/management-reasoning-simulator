"""Phase 2 shadow core, P2C: the approved physiological constraints (Level 1, qualitative).

The decisions KD-S1, KD-S2 and KD-S4 fix directions, memory and saturation, not numbers:
every gain they touch is provisional (``clinical_core.derived.PARAMETERS``). These tests
assert only what the decisions approve -- directionality, monotonicity, memory,
saturation, no impossible state -- on GI bleeding and on synthetic states of other
families, so that nothing here is tuned to the GI-bleed golden.
"""
from dataclasses import dataclass

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, RhythmCode, RhythmState,
                           SourceKind, run)
from clinical_core.derived import SYMPATHETIC_DRIVE, lactate_excess, sympathetic_drive
from clinical_core.logistics import EndoscopicHemostasis
from clinical_core.modules import GIHaemorrhage
from clinical_core.provenance import SettingChange

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
    restore_hb: bool = False

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        deltas = (ChannelDelta(Channel.V, -state.V + self.surplus_ml, self.source, minute, "volume restored"),)
        if self.restore_hb:
            deltas += (ChannelDelta(Channel.HB, anchors.hb - state.hb, self.source, minute, "haemoglobin restored"),)
        return Contribution(deltas=deltas)


@dataclass(frozen=True)
class Replay(Contributor):
    """Writes given V and Hb changes minute by minute, with no knowledge of bleeding (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_replay"
    id: str
    changes: tuple  # ((minute, dV, dHb), ...)

    def contribute(self, state, minute, signals, anchors, profile):
        deltas = []
        for at, volume, hb in self.changes:
            if at == minute:
                deltas += [ChannelDelta(Channel.V, volume, self.source, minute, "replayed volume change"),
                           ChannelDelta(Channel.HB, hb, self.source, minute, "replayed haemoglobin change")]
        return Contribution(deltas=tuple(deltas))


@dataclass(frozen=True)
class OxygenLost(Contributor):
    """The supplemental oxygen a patient arrived on is lost at one minute (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_oxygen_lost"
    id: str
    at_minute: int

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(settings=(SettingChange("fio2", 0.21, self.source, minute, "oxygen supply lost"),))


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


# KD-S2 -- one common sympathetic drive for the heart rate ---------------------------------

HEMOSTASIS = EndoscopicHemostasis("endoscopy", 30)
#: A brisker bleed than BLEED, so that 30 minutes give a clear shock (the thresholds below are
#: relative to the rise it causes, not to any provisional gain).
BRISK = GIHaemorrhage("gi_haemorrhage", 10.0, 0.02, 0.8, 0.1)


def _rates(trajectory):
    return [item.pulse_rate_bpm for item in trajectory.derived()]


def test_kd_s2_hemostasis_never_writes_the_rate_it_acts_only_through_volume_and_haemoglobin():
    """The same V and Hb changes, replayed without any bleeding module, give the same rate every minute."""
    bleeding = run(BLEEDING, (BLEED, HEMOSTASIS), 120)
    for record in bleeding.records:
        assert {d.channel for d in record.deltas if d.source == BLEED.source} <= {Channel.V, Channel.HB}
    changes = tuple((record.minute, sum(d.amount for d in record.deltas if d.source == BLEED.source
                                        and d.channel is Channel.V),
                     sum(d.amount for d in record.deltas if d.source == BLEED.source and d.channel is Channel.HB))
                    for record in bleeding.records)
    replayed = run(BLEEDING, (Replay("replay", changes),), 120)
    assert _rates(replayed) == pytest.approx(_rates(bleeding), abs=1e-9)
    assert all(SYMPATHETIC_DRIVE.key in record.internal_updates for record in bleeding.records), \
        "the drive is the core's own memory, kept every minute"


def test_kd_s2_a_hemostasis_without_resuscitation_leaves_the_rate_up():
    rates = _rates(run(BLEEDING, (BRISK, HEMOSTASIS), 120))
    assert abs(rates[31] - rates[29]) < 1.0, "no step at the moment of hemostasis"
    assert min(rates[30:]) >= rates[29] - 1.0, "the rate does not fall because the source is controlled"
    assert min(rates[30:]) > BLEEDING.hr


def test_kd_s2_b_volume_without_hemostasis_lowers_the_rate_for_a_while_then_it_climbs_again():
    rates = _rates(run(BLEEDING, (BRISK, Restore("bolus", 30)), 120))
    rise = rates[29] - BLEEDING.hr
    assert rise > 5
    low = min(rates[30:45])
    assert low < rates[29] - rise / 2, "volume lowers the rate"
    assert rates[-1] > rates[29], "the bleeding goes on and the rate climbs again"


def test_kd_s2_c_hemostasis_and_resuscitation_bring_the_rate_down_gradually_through_pressure_and_debt():
    trajectory = run(BLEEDING, (BRISK, HEMOSTASIS, Restore("transfusion", 30, restore_hb=True)), 120)
    rates, derived, states = _rates(trajectory), trajectory.derived(), trajectory.states
    assert derived[30].map > derived[29].map, "output and pressure improve"
    debts = [state.D for state in states[30:60]]
    assert debts[0] > 0 and all(later < earlier for earlier, later in zip(debts, debts[1:])), "D repays gradually"
    drives = [sympathetic_drive(state, BLEEDING, trajectory.profile) for state in states[29:45]]
    assert all(later < earlier for earlier, later in zip(drives, drives[1:])), "the drive falls"
    fall = rates[29] - rates[44]
    assert fall > (rates[29] - BLEEDING.hr) / 2, "the rate comes down"
    assert rates[29] - rates[30] < fall / 2, "gradually, not in one step"


def test_kd_s2_d_beta_blockade_blunts_the_chronotropic_response_to_the_same_physiology():
    blocked_anchors = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 0.6})
    free, blocked = run(BLEEDING, (BLEED,), 90), run(blocked_anchors, (BLEED,), 90)
    assert [s.V for s in free.states] == [s.V for s in blocked.states], "the same physiology"
    for one, other in zip(free.derived()[1:], blocked.derived()[1:]):
        assert other.pulse_rate_bpm - BLEEDING.hr == pytest.approx(0.4 * (one.pulse_rate_bpm - BLEEDING.hr))
        assert (other.sbp, other.map) == (one.sbp, one.map)
    with pytest.raises(Exception):
        Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 1.5})


def test_kd_s2_e_persistent_hypoxaemia_after_hemostasis_keeps_the_rate_up():
    on_oxygen = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "fio2": 0.6, "spo2": 96.0})
    treated = (BRISK, HEMOSTASIS, Restore("transfusion", 30, restore_hb=True))
    recovered = run(on_oxygen, treated, 120).derived()
    hypoxaemic = run(on_oxygen, treated + (OxygenLost("oxygen_lost", 30),), 120).derived()
    assert hypoxaemic[60].spo2 < on_oxygen.spo2 - 5 and recovered[60].spo2 == on_oxygen.spo2
    for minute in (45, 60, 90, 120):
        assert hypoxaemic[minute].pulse_rate_bpm > recovered[minute].pulse_rate_bpm + 3
        assert hypoxaemic[minute].pulse_rate_bpm > on_oxygen.hr


def test_kd_s2_other_families_drive_the_same_rate_hypoglycaemia():
    """A synthetic hypoglycaemia, with no bleeding: the same drive raises the rate."""
    rates = _rates(run(BLEEDING, (Step("insulin_excess", "glucose", 1, -80.0),), 30))
    assert rates[1] > BLEEDING.hr + 3 and rates[-1] > BLEEDING.hr + 3


def test_kd_s2_the_drive_rises_at_once_and_falls_with_its_own_memory():
    drop, back = Step("drop", "V", 5, -600.0), Step("back", "V", 15, 600.0)
    trajectory = run(BLEEDING, (drop, back), 60)
    rates = _rates(trajectory)
    assert rates[5] - rates[4] > 0.9 * (max(rates) - rates[4]), "the rise is immediate"
    assert rates[15] > rates[16] > rates[20] > rates[40] and rates[15] - rates[16] < rates[15] - rates[40]
    # Pressure is back at arrival: what is left of the rise is the debt not yet repaid (memory of D),
    # held a little above it because the drive follows the falling debt with its own lag.
    profile, last = trajectory.profile, trajectory.states[-1]
    residual = profile.hr_per_sympathetic_drive * profile.sympathetic_per_debt * last.D / profile.debt_clearance_tau_min
    assert last.D > 0 and residual <= rates[-1] - BLEEDING.hr < 1.5 * residual


def test_kd_s2_a_rate_the_rhythm_owns_does_not_answer_to_the_drive():
    """A paced or blocked rhythm holds its own rate; the drive acts on the sinus rate only."""
    paced = Anchors(**{**BLEEDING.to_dict(), "rhythm": RhythmState(RhythmCode.PACED, 70.0, 1.0, True), "hr": 70.0})
    assert {item.pulse_rate_bpm for item in run(paced, (BLEED,), 60).derived()} == {70.0}
