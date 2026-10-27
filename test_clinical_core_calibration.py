"""Phase 2 shadow core, P2C: the approved physiological constraints (Level 1, qualitative).

The decisions KD-S1, KD-S2 and KD-S4 fix directions, memory and saturation, not numbers:
every gain they touch is provisional (``clinical_core.derived.PARAMETERS``). These tests
assert only what the decisions approve -- directionality, monotonicity, memory,
saturation, no impossible state -- on GI bleeding and on synthetic states of other
families, so that nothing here is tuned to the GI-bleed golden.
"""
import math
from dataclasses import dataclass

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, RhythmCode, RhythmState,
                           SourceKind, run)
from clinical_core.derived import (DEFAULT_PROFILE, PRELOAD_CONGESTION, SYMPATHETIC_DRIVE, derive, lactate_excess,
                                   preload_position, sympathetic_drive)
from clinical_core.logistics import EndoscopicHemostasis
from clinical_core.modules import GIHaemorrhage
from clinical_core.provenance import SettingChange
from clinical_core.state import UnresolvedBoundary

BLEEDING = Anchors(case_id="synthetic_gi", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0,
                   crt_s=5.0, lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21,
                   rhythm=RhythmState.sinus(124.0), consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.8, 0.1)


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
    """Volume lost at a constant rate until it stops, without changing Hb (test only).

    A scripted probe of the preload coordinate alone: since P2I-2T only a probe may move V
    directly; a disease module loses whole blood through the shared blood state.
    """

    kind = SourceKind.SCRIPTED_EVENT
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


#: The same arrival with part of its lactate declared clearable (P2E-2), a synthetic value.
CLEARABLE = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "arrival_lactate_excess": 2.4,
                       "declared": {"arrival_lactate_excess": "synthetic_probe"}})


def test_kd_s1_residual_lactate_keeps_rr_up_for_a_while_and_clearing_it_never_causes_bradypnoea():
    """Corrected perfusion, even beyond arrival: RR trends down and never below the ventilatory part.

    Since P2E-2 delivery above demand is no credit, so lactate clears below arrival only to the
    baseline the case declares (here 4.4 - 2.4 mmol/L, a synthetic value).
    """
    trajectory = run(CLEARABLE, (Loss("loss", 2.5, 60), Restore("restore", 61, surplus_ml=600.0)), 600)
    derived = trajectory.derived()
    after = [item.respiratory_rate for item in derived[61:]]
    assert after[0] > after[-1], "RR is transiently higher while lactate is still elevated"
    assert derived[-1].lactate < CLEARABLE.lactate, "the declared arrival excess clears"
    assert min(item.lactate for item in derived) >= CLEARABLE.lactate - CLEARABLE.arrival_lactate_excess
    floor = min(CLEARABLE.respiratory_rate, trajectory.profile.rr_ventilatory_floor)
    assert min(item.respiratory_rate for item in derived) >= floor >= 10


def test_kd_s1_without_a_declared_arrival_excess_lactate_never_falls_below_arrival():
    """P2E-2: the debt repays only what it accrued; undeclared, the arrival lactate is the baseline."""
    trajectory = run(BLEEDING, (Loss("loss", 2.5, 60), Restore("restore", 61, surplus_ml=600.0)), 600)
    derived = trajectory.derived()
    assert min(state.D for state in trajectory.states) >= 0.0
    assert min(item.lactate for item in derived) >= BLEEDING.lactate
    assert derived[-1].lactate == pytest.approx(BLEEDING.lactate, abs=1e-3), "back to arrival, not below"


@pytest.mark.parametrize("arrival_rr,arrival_lactate", [(14.0, 9.0), (26.0, 4.4), (30.0, 12.0), (18.0, 1.0)])
def test_kd_s1_no_lactate_clearance_ever_takes_rr_below_ten(arrival_rr, arrival_lactate):
    # The whole arrival lactate declared clearable (P2E-2), so clearing goes as far as the floor.
    arrival = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "respiratory_rate": arrival_rr,
                         "lactate": arrival_lactate, "arrival_lactate_excess": arrival_lactate,
                         "declared": {"arrival_lactate_excess": "synthetic_probe"}})
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
BRISK = GIHaemorrhage("gi_haemorrhage", 10.0, 0.8, 0.1)


def _rates(trajectory):
    return [item.pulse_rate_bpm for item in trajectory.derived()]


def test_kd_s2_hemostasis_never_writes_the_rate_it_acts_only_through_volume_and_haemoglobin():
    """The same V and Hb changes, replayed without any bleeding module, give the same rate every minute.

    Since P2I-2T the module moves V through the shared blood state, refill moves V too and Hb is
    the blood composition's: every V and Hb change of the run is replayed.
    """
    bleeding = run(BLEEDING, (BLEED, HEMOSTASIS), 120)
    for record in bleeding.records:
        assert {d.channel for d in record.deltas if d.source == BLEED.source} <= {Channel.V}
        assert {d.source.key for d in record.deltas if d.channel in (Channel.V, Channel.HB)} <= {
            BLEED.source.key, "core_coupling:plasma_refill", "core_coupling:blood_composition"}
    changes = tuple((record.minute, sum(d.amount for d in record.deltas if d.channel is Channel.V),
                     sum(d.amount for d in record.deltas if d.channel is Channel.HB))
                    for record in bleeding.records)
    replayed = run(BLEEDING, (Replay("replay", changes),), 120)
    assert _rates(replayed) == pytest.approx(_rates(bleeding), abs=1e-9)
    drives = [change for record in bleeding.records for change in record.auxiliary
              if change.quantity == "sympathetic_drive"]
    assert drives and all(change.source == SYMPATHETIC_DRIVE for change in drives), \
        "the drive is the core's own auxiliary state, and every change of it is recorded"


def test_kd_s2_a_hemostasis_without_resuscitation_leaves_the_rate_up():
    rates = _rates(run(BLEEDING, (BRISK, HEMOSTASIS), 120))
    assert abs(rates[31] - rates[29]) < 1.0, "no step at the moment of hemostasis"
    assert min(rates[30:]) >= rates[29] - 1.0, "the rate does not fall because the source is controlled"
    assert min(rates[30:]) > BLEEDING.hr


def test_kd_s2_b_volume_without_hemostasis_lowers_the_rate_for_a_while_then_it_climbs_again():
    # 80 minutes: the bleeding goes on, short of emptying the ventricle (P2D-2 stops a run there).
    rates = _rates(run(BLEEDING, (BRISK, Restore("bolus", 30)), 80))
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
    blocked_anchors = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 0.6,
                                 "declared": {"beta_blockade": "synthetic_probe"}})
    free, blocked = run(BLEEDING, (BLEED,), 90), run(blocked_anchors, (BLEED,), 90)
    assert [s.V for s in free.states] == [s.V for s in blocked.states], "the same physiology"
    for one, other in zip(free.derived()[1:], blocked.derived()[1:]):
        assert other.pulse_rate_bpm - BLEEDING.hr == pytest.approx(0.4 * (one.pulse_rate_bpm - BLEEDING.hr))
        assert (other.sbp, other.map) == (one.sbp, one.map)
    with pytest.raises(Exception):
        Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 1.5,
                   "declared": {"beta_blockade": "synthetic_probe"}})


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
    drop, back = Step("drop", "V", 5, -400.0), Step("back", "V", 15, 400.0)
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


# KD-S4 -- one smooth, saturating preload curve --------------------------------------------

@dataclass(frozen=True)
class Infuse(Contributor):
    """Volume given at a constant rate until it stops (test only; a scripted probe of V, as ``Loss``)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_infuse"
    id: str
    per_minute: float
    stop_minute: int

    def contribute(self, state, minute, signals, anchors, profile):
        if minute > self.stop_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.V, self.per_minute, self.source, minute, "volume given"),))


def _case(**declared):
    return Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, **declared,
                      "declared": {name: "synthetic_probe" for name in declared}})


def _at(anchors, V=0.0, P=1.0, T=1.0):
    state = run(anchors, (), 0).states[0].evolve(V=float(V), P=float(P), T=float(T))
    return derive(state, anchors)


def _gain(anchors, V, bolus=250.0, **channels):
    return _at(anchors, V + bolus, **channels).output_rel - _at(anchors, V, **channels).output_rel


VOLUMES = [-500.0 + 250.0 * step for step in range(17)]   # -500 .. +3500 mL-eq


@pytest.mark.parametrize("position", [0.25, 0.5, 0.8])
@pytest.mark.parametrize("pump,tone", [(1.0, 1.0), (0.5, 1.0), (1.0, 1.8)])
def test_kd_s4_each_ml_helps_less_than_the_one_before(position, pump, tone):
    """d(output)/dV falls as V rises, on every curve: any arrival position, pump or tone."""
    anchors = _case(preload_fraction=position)
    # Below the empty point the ventricle gives nothing, and a pulse without output is refused
    # (P2D-2); above it, every step helps less.
    empty = DEFAULT_PROFILE.preload_curve_scale_ml * math.log1p(-position)      # V at the empty point
    with pytest.raises(UnresolvedBoundary):
        _at(anchors, empty - 1.0, P=pump, T=tone)
    filling = [_at(anchors, V, P=pump, T=tone).output_rel for V in VOLUMES if V > empty]
    assert all(0.0 < item < pump / position for item in filling), "above 0, below the plateau"
    gains = [later - earlier for earlier, later in zip(filling, filling[1:])]
    assert len(filling) >= 14 and all(gain > 0 for gain in gains), "more preload never lowers output"
    assert all(later < earlier for earlier, later in zip(gains, gains[1:])), "the curve is concave"


def test_kd_s4_1_and_2_the_first_bolus_helps_and_the_second_helps_less():
    deficit = -400.0
    first, second = _gain(BLEEDING, deficit), _gain(BLEEDING, deficit + 250.0)
    assert first > 0.25, "a marked deficit with a normal pump: meaningful improvement"
    assert 0 < second < first


def test_kd_s4_3_near_euvolaemia_more_volume_adds_little_output_or_pressure():
    first, late = _gain(BLEEDING, -400.0), _gain(BLEEDING, 2500.0)
    assert late < first / 10
    assert _at(BLEEDING, 2750.0).map - _at(BLEEDING, 2500.0).map < 1.0


def test_kd_s4_4_a_weaker_pump_gains_less_from_the_same_fluid_and_cannot_be_made_whole():
    for V in (-400.0, 0.0, 1000.0):
        assert _gain(BLEEDING, V, P=0.5) < _gain(BLEEDING, V)
    cardiogenic = _case(preload_fraction=0.8)          # a failing pump sits high on its curve
    assert max(_at(cardiogenic, V, P=0.6).output_rel for V in VOLUMES + [10000.0]) < 0.6 / 0.8 < 1.0


def test_kd_s4_5_a_preload_dependent_patient_is_more_sensitive_early_and_still_saturates():
    dependent = _case(preload_fraction=0.25)
    assert _gain(dependent, 0.0) > _gain(BLEEDING, 0.0)
    assert _gain(dependent, 3000.0) < _gain(dependent, 0.0) / 5


def test_kd_s4_6_high_tone_the_same_volume_does_not_give_the_same_output():
    for V in (-400.0, 0.0, 1000.0):
        constricted, normal = _at(BLEEDING, V, T=1.8), _at(BLEEDING, V)
        assert constricted.output_rel < normal.output_rel, "afterload lowers output"
        assert constricted.map > normal.map, "while tone still raises pressure"
        assert _gain(BLEEDING, V, T=1.8) < _gain(BLEEDING, V)


def test_kd_s4_7_overload_volume_rises_output_barely_and_lungs_congest_only_without_pump_reserve():
    infusion = (Infuse("overload", 8.0, 120),)          # about 1 L over two hours, from an already full circulation
    arrival_slope = 0.36 / 300.0                          # output per mL near arrival (see the last test)
    limited, normal = _case(pump_reserve=0.3), _case()
    for anchors in (limited, normal):
        trajectory = run(anchors, (Restore("filled", 1, surplus_ml=2000.0),) + infusion, 120)
        derived, states = trajectory.derived(), trajectory.states
        added = states[-1].V - states[1].V
        assert added > 900, "V rises substantially"
        assert derived[-1].output_rel - derived[1].output_rel < 0.1 * arrival_slope * added, "output barely moves"
        assert derived[-1].map - derived[1].map < 3.0, "nor does pressure"
        congestion = [d for record in trajectory.records for d in record.deltas if d.source == PRELOAD_CONGESTION]
        if anchors is limited:
            assert states[-1].L > 0 and all(d.channel is Channel.L and d.amount > 0 for d in congestion)
            assert all(later.L >= earlier.L for earlier, later in zip(states, states[1:]))
        else:
            assert states[-1].L == 0 and not congestion, "a pump with full reserve does not congest from preload"


def test_kd_s4_a_failing_pump_congests_from_excess_preload_even_with_a_normal_reserve():
    trajectory = run(_case(), (Restore("filled", 1, surplus_ml=3000.0), Step("ischaemia", "P", 2, -0.5)), 30)
    assert trajectory.states[-1].L > 0


def test_kd_s4_no_congestion_below_the_knee_and_none_in_shock():
    knee = DEFAULT_PROFILE.congestion_preload_knee
    limited = _case(pump_reserve=0.0)
    below = run(limited, (Restore("filled", 1, surplus_ml=600.0),), 60).states
    assert preload_position(below[-1], limited, DEFAULT_PROFILE) < knee and below[-1].L == 0
    assert run(limited, (BRISK,), 50).states[-1].L == 0


def test_kd_s4_the_curve_keeps_the_family_engine_s_slope_at_the_default_arrival_position():
    """The one adopted anchor of the curve: near arrival, 1/833.33 of output per mL (300 mL / 0.36)."""
    slope = (_at(BLEEDING, 0.5).output_rel - _at(BLEEDING, -0.5).output_rel) / 1.0
    assert slope == pytest.approx(0.36 / 300.0, rel=1e-6)


# Level 2 -- probes across families, prepared for faculty bands ----------------------------

def test_level_2_every_band_is_left_to_faculty_and_the_probes_are_deterministic():
    from clinical_core import bands
    assert set(bands.BANDS) == set(bands.PROBES) and all(band is None for band in bands.BANDS.values())
    assert bands.report() == bands.report()
    assert {family for family, *_ in bands.PROBES.values()} >= {"GI bleed / trauma", "sepsis", "asthma", "opioid"}
    # P2I-2V-R: the probes that wrote V directly are historical, outside the active harness.
    assert {family for family, *_ in bands.HISTORICAL_PROBES.values()} == {"sepsis", "ACS", "RV infarct / PE",
                                                                          "pulmonary oedema"}
    assert not set(bands.HISTORICAL_PROBES) & set(bands.PROBES) and set(bands.HISTORICAL_REASONS) == set(
        bands.HISTORICAL_PROBES)


def test_level_2_probes_move_the_way_the_decisions_say():
    from clinical_core import bands
    haemorrhage = bands.probe("haemorrhage")
    assert haemorrhage[-1]["map"] < haemorrhage[1]["map"] < haemorrhage[0]["map"] and haemorrhage[-1]["D"] > 0
    # P2I-2U: one synthetic whole-blood flow through the shared blood state; plasma refill restores part of
    # the shed volume, so the ventricle no longer empties within the hour, and Hb falls only by that dilution.
    assert [row["minute"] for row in haemorrhage] == [0, 30, 60] and haemorrhage[-1]["shed_ml"] == 600.0
    assert haemorrhage[-1]["V"] == pytest.approx(DEFAULT_PROFILE.volume_preload_kappa
                                                 * haemorrhage[-1]["circulating_ml"])
    assert haemorrhage[-1]["circulating_ml"] > -600.0
    assert 12.5 < haemorrhage[-1]["hb"] < haemorrhage[0]["hb"] == 13.0
    overload = bands.probe("overload")  # a HISTORICAL_PROBE since P2I-2V-R: still runnable, as a record
    assert overload[-1]["L"] > 0 and overload[-1]["output_rel"] - overload[1]["output_rel"] < 0.2
    assert bands.probe("opioid")[-1]["respiratory_rate"] < 10 < bands.probe("bronchospasm")[-1]["respiratory_rate"]


def test_the_haemorrhage_band_probe_is_one_synthetic_whole_blood_flow():
    """P2I-2U-1: the Level-2 haemorrhage probe moves neither V nor Hb itself and claims no clinical rate."""
    from clinical_core import bands
    from clinical_core.integration import run
    family, drives, declared, contributors, minutes = bands.PROBES["haemorrhage"]
    assert bands.PROBE_KINDS["haemorrhage"] == "SYNTHETIC_CROSS_FAMILY_HAEMORRHAGE_PROBE"
    assert all(isinstance(item, bands.BloodLoss) for item in contributors)
    assert "synthetic" in drives and "not a GI or trauma rate" in drives
    trajectory = run(Anchors(**bands.ARRIVAL), contributors, max(minutes))
    end = trajectory.states[-1]
    assert end.blood.outside_v == 0.0 and end.blood.outside_hb == 0.0, "nothing moved V or Hb outside the blood state"
    assert not any(delta.channel is Channel.HB and delta.source.kind is SourceKind.SCRIPTED_EVENT
                   for record in trajectory.records for delta in record.deltas)
    assert {c.process.value for record in trajectory.records for c in record.blood} == {"whole_blood_loss",
                                                                                         "plasma_refill"}


def test_no_active_level_2_probe_bypasses_the_shared_blood_state():
    """P2I-2V-R: every active probe moves V and Hb only through the shared blood state; the four that wrote V
    directly are HISTORICAL_PROBES, outside the active harness and its report table, each with its reason."""
    from clinical_core import bands
    for name, (_, _, _, contributors, _) in bands.PROBES.items():
        assert not any(isinstance(item, bands.Drift) and item.channel in ("V", "HB", "Hb") for item in contributors), name
        assert all(row.get("outside_v", 0.0) == 0.0 for row in bands.probe(name)), name
    for name in bands.HISTORICAL_PROBES:
        assert any(row.get("outside_v", 0.0) != 0.0 for row in bands.probe(name)), name
        assert bands.HISTORICAL_REASONS[name]
    report = bands.report()
    table = [line for line in report.splitlines() if line.startswith("| ")]
    assert not any("†" in line for line in table)
    assert not any(line.startswith(f"| {name} ") for name in bands.HISTORICAL_PROBES for line in table)
    assert all(f"- {name} (" in report for name in bands.HISTORICAL_PROBES)


# After the adversarial review of P2C ------------------------------------------------------

def _neutral(**values):
    base = dict(case_id="synthetic", sbp=110.0, dbp=70.0, hr=90.0, spo2=97.0, respiratory_rate=16.0, crt_s=2.0,
                lactate=1.0, hb=13.0, glucose=100.0, k=4.0, fio2=0.21, rhythm=RhythmState.sinus(90.0),
                consciousness_level=0)
    case = {name: "synthetic_probe" for name in values if name in ("beta_blockade", "preload_fraction",
                                                                       "pump_reserve")}
    return Anchors(**{**base, **values, "declared": case})


def _rr(anchors, lactate):
    from clinical_core.derived import respiratory_rate
    return respiratory_rate(run(anchors, (), 0).states[0], anchors, DEFAULT_PROFILE, lactate)


@pytest.mark.parametrize("arrival_rr", [10.0, 12.0, 16.0])
def test_kd_s1_the_metabolic_response_is_continuous_in_the_arrival_lactate(arrival_rr):
    """Arrival lactate just at or just above the drive threshold gives the same response."""
    at, above = _neutral(respiratory_rate=arrival_rr, lactate=2.0), _neutral(respiratory_rate=arrival_rr,
                                                                             lactate=2.001)
    for lactate in (4.0, 6.0, 10.0):
        assert _rr(above, lactate) == pytest.approx(_rr(at, lactate), abs=0.05)
        assert _rr(above, lactate) > arrival_rr + 5


def test_kd_s1_a_rise_above_arrival_gets_the_whole_metabolic_drive_whatever_the_arrival():
    from clinical_core.derived import _metabolic_drive
    acidotic = _neutral(respiratory_rate=16.0, lactate=8.0)
    rise = _rr(acidotic, 10.0) - _rr(acidotic, 8.0)
    assert rise == pytest.approx(_metabolic_drive(10.0, DEFAULT_PROFILE) - _metabolic_drive(8.0, DEFAULT_PROFILE))
    assert _rr(acidotic, 8.0) == 16.0 and _rr(acidotic, 1.0) >= DEFAULT_PROFILE.rr_ventilatory_floor


def test_kd_s4_a_tiny_arrival_position_still_reproduces_arrival():
    anchors = _neutral(preload_fraction=1e-17)
    assert derive(run(anchors, (), 0).states[0], anchors).output_rel == pytest.approx(1.0)


def test_kd_s4_arrival_is_a_fixed_point_and_only_added_preload_congests():
    congested = _neutral(preload_fraction=0.9, pump_reserve=0.5)
    assert run(congested, (), 60).states[-1].L == 0.0, "no input, no change"
    assert run(congested, (Restore("more", 1, surplus_ml=500.0),), 60).states[-1].L > 0


def test_kd_s2_without_a_pulse_no_drive_is_kept():
    from clinical_core.derived import sympathetic_after_minute
    trajectory = run(BLEEDING, (BRISK,), 20)
    before = trajectory.states[-1]
    assert sympathetic_drive(before, BLEEDING, DEFAULT_PROFILE) > 0
    arrested = before.evolve(minute=21, R=RhythmState.vf(), terminal_since=21)
    assert sympathetic_after_minute(before, arrested, BLEEDING, DEFAULT_PROFILE) == 0.0
