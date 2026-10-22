"""Phase 2 shadow core, WP2-1: state, provenance and the minute integrator.

These tests use small synthetic contributors defined here; the disease modules and the
interventions have their own files. None of this touches the family engine.
"""
import json
import math
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, CoreInvariantError, CoreState,
                           Derived, FrozenRecord, ProvenanceError, RhythmCode, RhythmState, RhythmTransition, Signal,
                           Source, SourceKind, attribution, derive, initial_state, register, run, scenario_from_dict,
                           scenario_to_dict, step)
from clinical_core.derived import check
from clinical_core.integration import CHANNEL_BOUNDS, OXYGEN_DEBT
from clinical_core.state import SCALAR_CHANNELS, canonical_json


def anchors(**changes):
    values = dict(case_id="synthetic", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0, crt_s=5.0,
                  lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(124.0),
                  consciousness_level=0)
    values.update(changes)
    return Anchors(**values)


@register
@dataclass(frozen=True)
class Drift(Contributor):
    """A constant per-minute change of one channel between two minutes (test only)."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_drift"
    id: str
    channel: str
    per_minute: float
    start_minute: int = 0
    stop_minute: int | None = None

    def contribute(self, state, minute, signals, anchors, profile):
        if minute <= self.start_minute or (self.stop_minute is not None and minute > self.stop_minute):
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), self.per_minute, self.source, minute,
                                                 f"synthetic drift of {self.channel}"),))


@register
@dataclass(frozen=True)
class Counter(Contributor):
    """Remembers how many minutes it has run, only through CoreState.internal (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_counter"
    id: str

    def contribute(self, state, minute, signals, anchors, profile):
        seen = int(self.own(state).get("minutes", 0))
        return Contribution(internal=self.own(state).updated(minutes=seen + 1))


@register
@dataclass(frozen=True)
class RhythmAt(Contributor):
    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_rhythm_at"
    id: str
    at_minute: int
    target: dict

    @classmethod
    def from_spec_data(cls, data):
        return cls(id=data["id"], at_minute=data["at_minute"], target=data["target"])

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        after = RhythmState.from_dict(self.target)
        return Contribution(transitions=(RhythmTransition(state.R, after, self.source, minute, "synthetic"),))


def test_the_rhythm_state_cannot_hold_an_impossible_combination():
    for build in (lambda: RhythmState(RhythmCode.SINUS, 80.0, 1.0, False),       # pulseless sinus
                  lambda: RhythmState(RhythmCode.ASYSTOLE, 30.0, 0.0, False),    # asystole with a rate
                  lambda: RhythmState(RhythmCode.SINUS, 0.0, 1.0, True),         # a rate of 0 that is not asystole
                  lambda: RhythmState(RhythmCode.VF, 180.0, 0.0, False),         # VF with a counted rate
                  lambda: RhythmState(RhythmCode.PEA, 40.0, 0.4, False),         # PEA producing output
                  lambda: RhythmState(RhythmCode.SINUS, 80.0, 0.0, True),        # perfusing without output
                  lambda: RhythmState(RhythmCode.VF, None, 0.0, True)):          # VF with a pulse
        with pytest.raises(CoreInvariantError):
            build()
    assert not RhythmState.asystole().pulse_present and RhythmState.asystole().rate_bpm == 0.0
    assert RhythmState.vf().rate_bpm is None and RhythmState.pea(40.0).output_factor == 0.0


def test_arrival_is_anchored_and_never_in_arrest():
    state = initial_state(anchors())
    assert all(getattr(state, name) == 0.0 for name in ("V", "L", "G", "W", "D", "N"))
    assert state.T == state.P == 1.0 and (state.hb, state.glucose, state.k) == (6.7, 118.0, 4.1)
    assert state.terminal_since is None
    with pytest.raises(CoreInvariantError):
        anchors(rhythm=RhythmState.asystole())
    with pytest.raises(CoreInvariantError):
        anchors(sbp=50.0, dbp=60.0)


def test_arrival_is_a_fixed_point_of_the_core():
    """With nothing acting, an hour later the patient is exactly as authored."""
    trajectory = run(anchors(), (), 60)
    first, last = trajectory.derived()[0], trajectory.derived()[-1]
    assert last.sbp == first.sbp == 88.0 and last.dbp == 54.0 and last.pulse_rate_bpm == 124.0
    assert last.spo2 == 97.0 and last.crt_s == 5.0 and last.lactate == 4.4 and last.respiratory_rate == 26.0
    assert trajectory.states[-1].D == 0.0
    assert all(record.deltas and all(delta.source == OXYGEN_DEBT for delta in record.deltas)
               for record in trajectory.records)


def test_same_inputs_give_an_identical_trajectory():
    contributors = (Drift("bleed", "V", -2.5), Drift("anaemia", "hb", -0.009), Counter("clock"))
    one = run(anchors(), contributors, 90)
    two = run(anchors(), deepcopy(contributors), 90)
    assert one.digest() == two.digest()
    assert canonical_json(one.to_dict()) == canonical_json(two.to_dict())


def test_the_order_contributors_are_listed_in_cannot_change_the_result():
    contributors = (Drift("bleed", "V", -2.5), Drift("anaemia", "hb", -0.009), Drift("tone", "T", .001),
                    Counter("clock"))
    forward = run(anchors(), contributors, 45)
    backward = run(anchors(), tuple(reversed(contributors)), 45)
    assert forward.digest() == backward.digest()


def test_one_long_run_equals_two_shorter_runs():
    contributors = (Drift("bleed", "V", -2.5, stop_minute=40), Counter("clock"))
    whole = run(anchors(), contributors, 60)
    first = run(anchors(), contributors, 25)
    second = run(anchors(), contributors, 35, initial=first.states[-1])
    assert first.states + second.states[1:] == whole.states
    assert first.records + second.records == whole.records


def test_nothing_the_integrator_is_given_is_changed():
    arrival = anchors()
    contributors = (Drift("bleed", "V", -2.5), Counter("clock"))
    state = initial_state(arrival)
    snapshot = (arrival.to_dict(), [item.to_spec() for item in contributors], state.to_dict())
    new_state, _ = step(state, contributors, arrival)
    assert new_state is not state and state.minute == 0 and new_state.minute == 1
    assert (arrival.to_dict(), [item.to_spec() for item in contributors], state.to_dict()) == snapshot
    with pytest.raises(FrozenInstanceError):
        state.V = 1.0
    with pytest.raises(AttributeError):
        new_state.internal.minutes = 3


def test_a_contributor_remembers_only_through_the_state():
    trajectory = run(anchors(), (Counter("clock"),), 12)
    assert trajectory.states[-1].internal_for("scripted_event:clock")["minutes"] == 12
    # Only the contributor's key is updated; the core's own memory is auxiliary state (P2D-1).
    assert trajectory.records[-1].internal_updates == ("scripted_event:clock",)


def test_a_serialized_scenario_replays_identically():
    contributors = (Drift("bleed", "V", -2.5), Counter("clock"),
                    RhythmAt("block", 30, RhythmState(RhythmCode.COMPLETE_AV_BLOCK, 40.0, .7, True).to_dict()))
    original = run(anchors(), contributors, 60)
    stored = json.loads(json.dumps(scenario_to_dict(anchors(), contributors, 60)))
    arrival, rebuilt, minutes, profile = scenario_from_dict(stored)
    assert run(arrival, rebuilt, minutes, profile).digest() == original.digest()
    state = original.states[-1]
    assert CoreState.from_dict(json.loads(json.dumps(state.to_dict()))) == state


def test_every_change_has_a_source_and_the_sources_add_up_to_the_change():
    contributors = (Drift("bleed", "V", -2.5), Drift("anaemia", "hb", -0.009), Drift("tone", "T", -.002))
    trajectory = run(anchors(), contributors, 80)
    for record in trajectory.records:
        for delta in record.deltas:
            assert isinstance(delta.source, Source) and delta.source.kind in SourceKind and delta.source.id
            assert delta.minute == record.minute and delta.description
    first, last = trajectory.states[0], trajectory.states[-1]
    for channel in SCALAR_CHANNELS:
        total = math.fsum(attribution(trajectory.records, channel).values())
        assert last.value(channel) - first.value(channel) == pytest.approx(total, abs=1e-9)
    assert attribution(trajectory.records, Channel.V) == {"disease_module:bleed": pytest.approx(-200.0)}


def test_a_bound_that_acts_is_recorded_as_a_clamp():
    trajectory = run(anchors(), (Drift("anaemia", "hb", -0.5),), 20)
    assert trajectory.states[-1].hb == CHANNEL_BOUNDS[Channel.HB][0]
    clamps = [delta for record in trajectory.records for delta in record.deltas if delta.source.kind is SourceKind.CLAMP]
    assert clamps and all(delta.channel is Channel.HB and delta.amount > 0 for delta in clamps)
    assert sum(attribution(trajectory.records, Channel.HB).values()) == pytest.approx(3.0 - 6.7)


def test_changes_without_a_valid_source_fail_closed():
    module = Source(SourceKind.DISEASE_MODULE, "bleed")
    with pytest.raises(ProvenanceError):
        ChannelDelta(Channel.R, 1.0, module, 1, "rhythm is not additive")
    with pytest.raises(ProvenanceError):
        ChannelDelta(Channel.V, float("nan"), module, 1, "not a number")
    with pytest.raises(ProvenanceError):
        ChannelDelta(Channel.V, 1.0, module, 1, "")
    with pytest.raises(ProvenanceError):
        ChannelDelta(Channel.V, 1.0, module, 0, "minute 0 is arrival; nothing is applied there")
    with pytest.raises(ProvenanceError):
        Source(SourceKind.INTERVENTION, " ")

    @dataclass(frozen=True)
    class Forger(Contributor):
        kind = SourceKind.INTERVENTION
        type_name = "test_forger"
        id: str

        def contribute(self, state, minute, signals, anchors, profile):
            return Contribution(deltas=(ChannelDelta(Channel.V, 100.0, Source(SourceKind.DISEASE_MODULE, "bleed"),
                                                     minute, "attributed to someone else"),))

    with pytest.raises(ProvenanceError):
        run(anchors(), (Forger("order-1"),), 1)
    with pytest.raises(ProvenanceError):
        run(anchors(), (Drift("same", "V", 1.0), Drift("same", "hb", 1.0)), 1)


def test_a_contributor_reads_only_the_signals_it_declares():
    @dataclass(frozen=True)
    class Curious(Contributor):
        kind = SourceKind.DISEASE_MODULE
        type_name = "test_curious"
        id: str

        def contribute(self, state, minute, signals, anchors, profile):
            self.heard(signals, "ppi")
            return Contribution()

    with pytest.raises(ProvenanceError):
        run(anchors(), (Curious("x"),), 1)


def test_an_arrest_is_one_consistent_terminal_state():
    trajectory = run(anchors(), (RhythmAt("collapse", 5, RhythmState.asystole().to_dict()),), 12)
    before, after = trajectory.derived()[4], trajectory.derived()[5]
    assert before.pulse_present and before.sbp is not None
    assert not after.pulse_present and after.rhythm is RhythmCode.ASYSTOLE and after.monitor_rate_bpm == 0.0
    assert (after.sbp, after.dbp, after.map, after.spo2, after.crt_s, after.pulse_rate_bpm) == (None,) * 6
    assert after.consciousness_level == 3 and after.respiratory_rate == 0.0
    assert trajectory.states[5].terminal_since == 5 and trajectory.states[-1].terminal_since == 5
    vf = run(anchors(), (RhythmAt("vf", 3, RhythmState.vf().to_dict()),), 4).derived()[-1]
    assert vf.monitor_rate_bpm is None and vf.pulse_rate_bpm is None and not vf.pulse_present


def test_a_pulse_cannot_return_without_modelled_resuscitation():
    contributors = (RhythmAt("collapse", 5, RhythmState.asystole().to_dict()),
                    RhythmAt("revival", 8, RhythmState.sinus(90.0).to_dict()))
    with pytest.raises(CoreInvariantError):
        run(anchors(), contributors, 10)


def test_conflicting_or_impossible_rhythm_transitions_fail_closed():
    conflicting = (RhythmAt("a", 3, RhythmState.asystole().to_dict()), RhythmAt("b", 3, RhythmState.vf().to_dict()))
    with pytest.raises(CoreInvariantError):
        run(anchors(), conflicting, 3)

    @dataclass(frozen=True)
    class Stale(Contributor):
        kind = SourceKind.SCRIPTED_EVENT
        type_name = "test_stale"
        id: str

        def contribute(self, state, minute, signals, anchors, profile):
            return Contribution(transitions=(RhythmTransition(RhythmState.sinus(60.0), RhythmState.vf(), self.source,
                                                              minute, "from a rhythm the patient is not in"),))

    with pytest.raises(CoreInvariantError):
        run(anchors(), (Stale("x"),), 1)


def test_derived_values_that_contradict_each_other_fail_closed():
    good = derive(initial_state(anchors()), anchors())
    values = good.to_dict()
    values["rhythm"] = good.rhythm
    for changes in ({"pulse_present": False},                                # pulse gone, pressures still there
                    {"monitor_rate_bpm": 0.0},                               # rate 0 on a sinus rhythm
                    {"sbp": 40.0},                                           # systolic below diastolic
                    {"rhythm": RhythmCode.ASYSTOLE}):                        # asystole with a rate
        with pytest.raises(CoreInvariantError):
            check(Derived(**{**values, **changes}))


def test_the_core_derives_no_narrative():
    derived = derive(initial_state(anchors()), anchors()).to_dict()
    assert all(isinstance(value, (int, float, bool)) or value is None or value in {code.value for code in RhythmCode}
               for value in derived.values())


def test_internal_state_is_immutable_and_serializable():
    record = FrozenRecord({"pool": 1.5, "nested": {"a": [1, 2]}})
    assert record["nested"]["a"] == (1, 2) and record.to_dict() == {"nested": {"a": [1, 2]}, "pool": 1.5}
    assert record.updated(pool=2.0)["pool"] == 2.0 and record["pool"] == 1.5
    with pytest.raises(CoreInvariantError):
        FrozenRecord({"bad": float("inf")})
    with pytest.raises(CoreInvariantError):
        FrozenRecord({"bad": object()})


def test_signals_are_ordered_and_owned():
    signal = Signal("ppi", Source(SourceKind.INTERVENTION, "o1"), 3)
    assert signal.to_dict() == {"name": "ppi", "source": {"kind": "intervention", "id": "o1"}, "since_minute": 3}


# Hardening found by the adversarial review of 2026-10-21 -----------------------------

def test_only_frozen_contributors_with_their_own_kind_are_accepted():
    from clinical_core.integration import RESERVED_KINDS

    @dataclass(frozen=True)
    class FakeClamp(Contributor):
        kind = SourceKind.CLAMP
        type_name = "test_fake_clamp"
        id: str

    @dataclass
    class Mutable(Contributor):
        kind = SourceKind.DISEASE_MODULE
        type_name = "test_mutable"
        id: str

    assert SourceKind.CLAMP in RESERVED_KINDS and SourceKind.CORE_COUPLING in RESERVED_KINDS
    for contributor in (FakeClamp("bounds:V"), Mutable("m")):
        with pytest.raises(ProvenanceError):
            run(anchors(), (contributor,), 1)


def test_a_contributor_is_handed_only_the_signals_it_declares():
    seen = []

    @dataclass(frozen=True)
    class Listener(Contributor):
        kind = SourceKind.DISEASE_MODULE
        type_name = "test_listener"
        responds_to = frozenset({"wanted"})
        id: str

        def contribute(self, state, minute, signals, anchors, profile):
            seen.append(tuple(signal.name for signal in signals))
            return Contribution()

    @dataclass(frozen=True)
    class Talker(Contributor):
        kind = SourceKind.INTERVENTION
        type_name = "test_talker"
        id: str

        def signals(self, minute):
            return (Signal("wanted", self.source, 0), Signal("other", self.source, 0))

    run(anchors(), (Listener("l"), Talker("t")), 2)
    assert seen == [("wanted",), ("wanted",)]


def test_an_arrival_below_the_lactate_floor_is_still_a_fixed_point():
    arrival = anchors(lactate=0.5)
    derived = run(arrival, (), 30).derived()
    assert derived[0].lactate == derived[-1].lactate == 0.5
    assert derived[0].respiratory_rate == derived[-1].respiratory_rate == 26.0


def test_nested_internal_state_serializes():
    record = FrozenRecord({"queue": [{"a": 1}, {"b": [2, 3]}]})
    assert json.loads(canonical_json(record.to_dict())) == {"queue": [{"a": 1}, {"b": [2, 3]}]}


def test_a_scenario_rebuilds_in_a_fresh_process_without_prior_imports():
    """from_spec must not depend on which contributor modules the caller happened to import."""
    import subprocess
    import sys
    from pathlib import Path
    from clinical_core.interventions import Crystalloid, Oxygen, PackedRedCells, ProtonPumpInhibitor
    from clinical_core.logistics import EndoscopicHemostasis
    from clinical_core.modules import GIHaemorrhage, ScriptedRhythmEvent
    contributors = (GIHaemorrhage("bleed", 2.5, .009, .8, .1), Crystalloid("c", 0, 500.0, 20.0, 50.0, .125, .6, 30.0, .0006),
                    PackedRedCells("b", 0, 1.0, None, 1 / 30, 300.0, .85), Oxygen("o", 1, .4),
                    ProtonPumpInhibitor("p", 0), EndoscopicHemostasis("e", 30),
                    ScriptedRhythmEvent("r", 40, RhythmState.asystole(), preventability="not preventable"))
    stored = json.dumps(scenario_to_dict(anchors(), contributors, 45))
    expected = run(anchors(), contributors, 45).digest()
    code = ("import json, sys, clinical_core\n"
            "from clinical_core.integration import run, scenario_from_dict\n"
            "arrival, rebuilt, minutes, profile = scenario_from_dict(json.loads(sys.stdin.read()))\n"
            "print(run(arrival, rebuilt, minutes, profile).digest())\n")
    root = Path(__file__).resolve().parent
    done = subprocess.run([sys.executable, "-c", code], cwd=root, input=stored, capture_output=True, text=True,
                          timeout=120)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == expected


def test_reloading_a_contributor_module_does_not_break_the_registry():
    import importlib
    import clinical_core.interventions.fluids as fluids
    importlib.reload(fluids)
    from clinical_core.integration import from_spec
    spec = fluids.Crystalloid("x", 0, 100.0, None, 50.0, .125, .6, 30.0, .0006).to_spec()
    assert from_spec(spec).to_spec() == spec
