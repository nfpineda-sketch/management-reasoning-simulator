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
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, CoreState

BLEEDING = Anchors(case_id="synthetic_gi", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0,
                   crt_s=5.0, lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21,
                   rhythm=RhythmState.sinus(124.0), consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.009, 0.8, 0.1)


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
