"""Phase 2 shadow core, P2D: structural physiology invariants before Level-2 calibration.

Each test checks a structure the decisions of 2026-10-22 (P2D) require: what the core keeps
as memory, what states are forbidden, which directions hold. None checks a calibrated number:
every gain and time constant stays provisional (``clinical_core.derived.PARAMETERS``).
"""
import json
from copy import deepcopy
from dataclasses import dataclass, replace

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, CoreInvariantError, RhythmState,
                           SourceKind, run)
from clinical_core.derived import DEFAULT_PROFILE, LACTATE_KINETICS, SYMPATHETIC_DRIVE, derive
from clinical_core.integration import step
from clinical_core.modules import GIHaemorrhage
from clinical_core.provenance import AuxiliaryChange, MinuteRecord, ProvenanceError, Source
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, CoreState, UnresolvedBoundary

BLEEDING = Anchors(case_id="synthetic_gi", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0,
                   crt_s=5.0, lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21,
                   rhythm=RhythmState.sinus(124.0), consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.009, 0.8, 0.1)


@dataclass(frozen=True)
class Step(Contributor):
    """A one-off change of one channel at one minute (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_structural_step"
    id: str
    channel: str
    at_minute: int
    amount: float

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), self.amount, self.source, minute,
                                                 f"synthetic step of {self.channel}"),))


# P2D-1 -- explicit auxiliary dynamic state ------------------------------------------------

def test_p2d1_the_core_memory_is_typed_auxiliary_state_not_a_channel_or_a_contributor_record():
    trajectory = run(BLEEDING, (BLEED,), 30)
    last = trajectory.states[-1]
    assert isinstance(last.aux, AuxiliaryState) and set(last.aux.to_dict()) == set(AUXILIARY_FIELDS)
    assert last.aux.lactate_excess_mmol_l > 0 and last.aux.sympathetic_drive > 0
    assert not any(key.startswith("core_coupling:") for key in last.internal), "no hidden memory in internal"
    contributors = {item.source.key for item in trajectory.contributors}
    assert all(set(record.internal_updates) <= contributors for record in trajectory.records), \
        "internal holds only the contributors' own records"
    assert {name for name in AUXILIARY_FIELDS} & {channel.value for channel in Channel} == set()


def test_p2d1_every_change_of_auxiliary_state_is_recorded_with_its_source():
    trajectory = run(BLEEDING, (BLEED,), 30)
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        for change in record.auxiliary:
            assert change.source in (LACTATE_KINETICS, SYMPATHETIC_DRIVE) and change.minute == record.minute
            assert (getattr(before.aux, change.quantity), getattr(after.aux, change.quantity)) == (change.before,
                                                                                                    change.after)
        unrecorded = {name for name in AUXILIARY_FIELDS} - {change.quantity for change in record.auxiliary}
        assert all(getattr(before.aux, name) == getattr(after.aux, name) for name in unrecorded)


def test_p2d1_only_the_core_writes_an_auxiliary_change():
    with pytest.raises(ProvenanceError):
        AuxiliaryChange("sympathetic_drive", 0.0, 1.0, Source(SourceKind.DISEASE_MODULE, "x"), 1, "not the core")
    with pytest.raises(ProvenanceError):
        AuxiliaryChange("heart_rate", 0.0, 1.0, SYMPATHETIC_DRIVE, 1, "not an auxiliary quantity")


def test_p2d1_serialization_is_deterministic_and_round_trips():
    state = run(BLEEDING, (BLEED,), 40).states[-1]
    data = json.loads(json.dumps(state.to_dict()))
    assert CoreState.from_dict(data) == state and CoreState.from_dict(data).digest() == state.digest()
    with pytest.raises(CoreInvariantError):
        AuxiliaryState.from_dict({"hidden_memory": 1.0})


def test_p2d1_a_run_resumed_from_a_serialized_state_is_the_same_run():
    whole = run(BLEEDING, (BLEED,), 80)
    middle = CoreState.from_dict(json.loads(json.dumps(whole.states[40].to_dict())))
    resumed = run(BLEEDING, (BLEED,), 40, initial=middle)
    assert [s.digest() for s in resumed.states] == [s.digest() for s in whole.states[40:]]
    assert [r.to_dict() for r in resumed.records] == [r.to_dict() for r in whole.records[40:]]


def test_p2d1_deepcopy_and_pickle_are_safe_for_the_whole_state():
    import pickle
    state = run(BLEEDING, (BLEED,), 20).states[-1]       # internal holds the bleeding module's record
    assert state.internal and deepcopy(state) == state and pickle.loads(pickle.dumps(state)) == state


def test_p2d1_deepcopy_is_safe_and_changes_nothing():
    trajectory = run(BLEEDING, (BLEED,), 20)
    copied = deepcopy(trajectory.states[-1])
    assert copied == trajectory.states[-1] and copied.aux is not None
    with pytest.raises(Exception):
        copied.aux.sympathetic_drive = 5.0           # frozen
    assert step(copied, (BLEED,), BLEEDING)[0] == step(trajectory.states[-1], (BLEED,), BLEEDING)[0]


def test_p2d1_an_unrecorded_auxiliary_change_is_refused():
    from clinical_core.integration import _check_conservation
    before = run(BLEEDING, (), 0).states[0]
    after = before.evolve(minute=1, aux=AuxiliaryState(lactate_excess_mmol_l=0.5))
    with pytest.raises(ProvenanceError):
        _check_conservation(before, after, MinuteRecord(minute=1))


def test_p2d1_the_shadow_trace_carries_it_as_non_authoritative_core_state():
    from clinical_core.contracts_shadow import run_contract_shadow
    payload = run_contract_shadow("gi_bleed_57m", "untreated_60").trace().payload
    block = payload["core_auxiliary_state"]
    assert block["authoritative"] is False and block["layer"] == "core_internal_state"
    assert set(block["end"]) == set(AUXILIARY_FIELDS) and block["arrival"] == AuxiliaryState().to_dict()
    assert any(change["type"] == "auxiliary" for minute in payload["minutes"] for change in minute["auxiliary"])


# P2D-2 -- no pulse without output; no pressure without output --------------------------------

BRISK = GIHaemorrhage("gi_haemorrhage", 10.0, 0.02, 0.8, 0.1)


def _derived_with_pulse():
    return derive(run(BLEEDING, (BLEED,), 5).states[-1], BLEEDING)


def test_p2d2_zero_output_with_a_pulse_is_rejected():
    from clinical_core.derived import check
    with pytest.raises(CoreInvariantError):
        check(replace(_derived_with_pulse(), output_rel=0.0))
    empty = run(BLEEDING, (), 0).states[0].evolve(V=-1000.0)
    with pytest.raises(UnresolvedBoundary, match="effective output reached zero"):
        derive(empty, BLEEDING)


def test_p2d2_zero_output_with_a_measurable_pressure_is_rejected():
    from clinical_core.derived import check
    pulseless = derive(run(BLEEDING, (), 0).states[0].evolve(minute=1, R=RhythmState.vf(), terminal_since=1),
                       BLEEDING)
    with pytest.raises(CoreInvariantError):
        check(replace(pulseless, sbp=60.0, dbp=30.0, map=40.0))
    with pytest.raises(CoreInvariantError):
        check(replace(_derived_with_pulse(), output_rel=0.0, sbp=60.0, dbp=30.0, map=40.0))


def test_p2d2_a_pulseless_state_has_no_measurable_pressure_or_perfusion():
    for rhythm in (RhythmState.vf(), RhythmState.asystole(), RhythmState.pea(40.0)):
        derived = derive(run(BLEEDING, (), 0).states[0].evolve(minute=1, R=rhythm, terminal_since=1), BLEEDING)
        assert (derived.sbp, derived.dbp, derived.map, derived.spo2, derived.crt_s, derived.pulse_rate_bpm) == \
            (None,) * 6
        assert derived.output_rel == 0.0 and not derived.pulse_present


def test_p2d2_pea_keeps_electrical_activity_without_a_pulse():
    derived = derive(run(BLEEDING, (), 0).states[0].evolve(minute=1, R=RhythmState.pea(40.0), terminal_since=1),
                     BLEEDING)
    assert derived.monitor_rate_bpm == 40.0 and derived.pulse_rate_bpm is None and derived.sbp is None


def test_p2d2_a_run_that_empties_the_ventricle_fails_closed_at_that_minute():
    with pytest.raises(UnresolvedBoundary, match="minute 5[0-9]"):
        run(BLEEDING, (BRISK,), 90)


def test_p2d2_an_explicit_terminal_transition_is_used_when_one_applies():
    """A declared arrest before the boundary: the run goes on, pulseless, with nothing measurable."""
    from clinical_core.modules import ScriptedRhythmEvent
    arrest = ScriptedRhythmEvent("arrest", 50, RhythmState.pea(30.0), "not preventable here")
    trajectory = run(BLEEDING, (BRISK, arrest), 70)
    after = trajectory.derived()[60]
    assert not after.pulse_present and after.sbp is None and after.monitor_rate_bpm == 30.0


# P2D-3 -- the sympathetic term is never negative ---------------------------------------------------

def _sinus_rates(trajectory):
    return [(d.pulse_rate_bpm, s.R.rate_bpm) for s, d in zip(trajectory.states, trajectory.derived())
            if s.R.pulse_present]


def test_p2d3_elevated_drive_raises_the_rate_above_the_intrinsic_rate():
    trajectory = run(BLEEDING, (BLEED,), 60)
    last = trajectory.states[-1]
    assert last.aux.sympathetic_drive > 0 and trajectory.derived()[-1].pulse_rate_bpm > last.R.rate_bpm


def test_p2d3_as_the_drive_decays_the_rate_approaches_the_intrinsic_rate_and_never_crosses_it():
    trajectory = run(BLEEDING, (Step("drop", "V", 5, -300.0), Step("back", "V", 15, 900.0)), 120)
    rates = _sinus_rates(trajectory)
    assert all(rate >= intrinsic for rate, intrinsic in rates)
    assert rates[-1][0] - rates[-1][1] < rates[15][0] - rates[15][1], "approaching the intrinsic rate"


def test_p2d3_no_drive_means_the_intrinsic_rate():
    arrival = run(BLEEDING, (), 0).states[0]
    surplus = arrival.evolve(V=800.0)                     # pressure above arrival: nothing to drive
    assert arrival.aux.sympathetic_drive == 0.0 and derive(arrival, BLEEDING).pulse_rate_bpm == BLEEDING.hr
    trajectory = run(BLEEDING, (Step("fill", "V", 1, 800.0),), 30)
    assert trajectory.states[-1].aux.sympathetic_drive == 0.0
    assert trajectory.derived()[-1].pulse_rate_bpm == BLEEDING.hr
    assert derive(surplus, BLEEDING).pulse_rate_bpm == BLEEDING.hr


def test_p2d3_beta_blockade_reduces_the_gain_and_never_turns_withdrawal_negative():
    blocked = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 0.5})
    free, beta = run(BLEEDING, (BLEED,), 60).derived(), run(blocked, (BLEED,), 60).derived()
    for one, other in zip(free[1:], beta[1:]):
        assert other.pulse_rate_bpm - BLEEDING.hr == pytest.approx(0.5 * (one.pulse_rate_bpm - BLEEDING.hr))
    filled = run(blocked, (Step("fill", "V", 1, 800.0),), 30).derived()
    assert min(item.pulse_rate_bpm for item in filled) == BLEEDING.hr


def test_p2d3_a_rate_below_the_intrinsic_rate_needs_an_explicit_chronotropic_source():
    from clinical_core.modules import ScriptedRhythmEvent
    slowed = ScriptedRhythmEvent("negative_chronotrope", 10, RhythmState.sinus(70.0), "declared drug effect")
    trajectory = run(BLEEDING, (Step("fill", "V", 1, 800.0), slowed), 40)
    rates = _sinus_rates(trajectory)
    assert min(rate for rate, _ in rates[:10]) == BLEEDING.hr, "the drive alone never goes below"
    assert rates[-1] == (70.0, 70.0), "below 124 only because R changed, explicitly"
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(sympathetic_drive=-0.1)


def test_p2d3_no_golden_run_puts_a_sinus_rate_below_its_intrinsic_rate():
    from clinical_core.shadow import SCENARIOS, VARIANTS, run_shadow
    for variant in VARIANTS:
        for scenario in SCENARIOS:
            assert all(rate >= intrinsic for rate, intrinsic in _sinus_rates(run_shadow(variant, scenario).core))
