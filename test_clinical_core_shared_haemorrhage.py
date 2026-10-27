"""Phase 2 shadow core, P2I-2T: the shared haemorrhage / circulating-blood state.

One haemorrhage process takes whole blood -- volume and red cells together -- out of a shared blood
state; plasma refill, crystalloid and packed red cells act through the same state; Hb is red-cell
content over circulating volume and V is kappa x the circulating-volume deviation. These tests pin
the accounting (P2I-2T-12) and the behaviour the faculty asked for (P2I-2T-2..7), with the
provisional values of the canonical profile (SYNTHETIC/CANDIDATE, TBD) or synthetic ones.
"""
import json
import math
from copy import deepcopy
from dataclasses import dataclass, fields, replace
from pathlib import Path

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, CoreInvariantError, CoreState,
                           ProvenanceError, RhythmState, SourceKind, run, scenario_from_dict, scenario_to_dict)
from clinical_core.bands import Drift
from clinical_core import blood_probes as bp
from clinical_core.derived import (BLOOD_COMPOSITION, DEFAULT_PROFILE, PLASMA_REFILL, CoreProfile, blood_haemoglobin,
                                   plasma_refill)
from clinical_core.integration import _check_blood, check_blood_identity, step
from clinical_core.legacy_adapter import REFERENCE_ONLY
from clinical_core.interventions import Crystalloid, PackedRedCells, ProtonPumpInhibitor
from clinical_core.logistics import EndoscopicHemostasis
from clinical_core.modules import GIHaemorrhage
from clinical_core.provenance import BloodChange, BloodFlow, BloodProcess, Source, blood_attribution
from clinical_core.state import BLOOD_FIELDS, CHANNEL_DEFINITIONS, BloodState, UnresolvedBoundary

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2T_ESTADO_HEMORRAGICO_COMPARTIDO.md"
DATA = ROOT / "docs" / "revision" / "P2I2T_blood_probes.json"

ARRIVAL = Anchors(case_id="gi_bleed_72f", sbp=98.0, dbp=62.0, hr=112.0, spo2=96.0, respiratory_rate=24.0, crt_s=4.0,
                  lactate=3.4, hb=6.4, glucose=130.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(112.0),
                  consciousness_level=0)
B0 = DEFAULT_PROFILE.arrival_circulating_volume_ml
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.8, 0.1)


def saline(order_id="order-saline", start=0, volume=2000.0, duration=20.0):
    return Crystalloid(order_id, start, volume, duration, untimed_rate_ml_per_min=50.0, effective_ml_per_ml=0.125,
                       transient_share=0.6, leak_tau_min=30.0)


def red_cells(order_id="order-prbc", start=0, units=2.0, duration=60.0):
    return PackedRedCells(order_id, start, units, duration, untimed_units_per_min=1 / 30, volume_ml_per_unit=300.0,
                          unit_hb_g_dl=20.0)


#: Every process at once: the bleed slowed by a PPI and treated at 90 min, saline and red cells.
MIXED = (BLEED, ProtonPumpInhibitor("order-ppi", 10), EndoscopicHemostasis("endoscopy", 90),
         saline(start=5), red_cells(start=30))


@dataclass(frozen=True)
class Writer(Contributor):
    """A contributor of a given kind that writes one channel directly (test only)."""

    kind: SourceKind
    id: str
    channel: str = "hb"

    type_name = "test_blood_writer"

    @property
    def source(self):
        return Source(self.kind, self.id)

    def contribute(self, state, minute, signals, anchors, profile):
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), -0.01, self.source, minute, "a direct drift"),))


# P2I-2T-12: accounting -------------------------------------------------------------------------------

def test_every_blood_field_changes_by_exactly_its_processes_and_never_falls():
    trajectory = run(ARRIVAL, MIXED, 180)
    owner = {BloodProcess.WHOLE_BLOOD_LOSS: ("shed_ml", "shed_red_cells"),
             BloodProcess.CRYSTALLOID_IN: ("crystalloid_in_ml", None),
             BloodProcess.CRYSTALLOID_OUT: ("crystalloid_out_ml", None),
             BloodProcess.RED_CELL_TRANSFUSION: ("transfused_ml", "transfused_red_cells"),
             BloodProcess.PLASMA_REFILL: ("refill_ml", None)}
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        for name in BLOOD_FIELDS:
            moved = math.fsum([c.volume_ml for c in record.blood if owner[c.process][0] == name]
                              + [c.red_cells for c in record.blood if owner[c.process][1] == name])
            assert getattr(after.blood, name) - getattr(before.blood, name) == pytest.approx(moved, abs=1e-9)
            assert getattr(after.blood, name) >= getattr(before.blood, name)
        assert {c.process for c in record.blood} <= set(owner)
    seen = {c.process for record in trajectory.records for c in record.blood}
    assert seen == set(BloodProcess), "the mixed run exercises every process"


def test_red_cells_change_only_with_whole_blood_loss_or_transfusion():
    trajectory = run(ARRIVAL, MIXED, 180)
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        carried = [c for c in record.blood if c.red_cells]
        assert {c.process for c in carried} <= {BloodProcess.WHOLE_BLOOD_LOSS, BloodProcess.RED_CELL_TRANSFUSION}
        assert after.blood.red_cells - before.blood.red_cells == pytest.approx(
            math.fsum(c.signed_red_cells for c in record.blood), abs=1e-12)
        assert all(c.red_cells == 0.0 and c.hb_g_dl == 0.0 for c in record.blood
                   if c.process in (BloodProcess.PLASMA_REFILL, BloodProcess.CRYSTALLOID_IN,
                                    BloodProcess.CRYSTALLOID_OUT))


def test_the_circulating_volume_changes_only_by_bleeding_fluids_refill_and_redistribution():
    trajectory = run(ARRIVAL, MIXED, 180)
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        assert after.blood.volume_ml - before.blood.volume_ml == pytest.approx(
            math.fsum(c.signed_volume_ml for c in record.blood), abs=1e-9)
    totals = blood_attribution(trajectory.records)
    assert set(totals) == {"whole_blood_loss disease_module:gi_haemorrhage", "crystalloid_in intervention:order-saline",
                           "crystalloid_out intervention:order-saline",
                           "red_cell_transfusion intervention:order-prbc", "plasma_refill core_coupling:plasma_refill"}
    assert math.fsum(item["volume_ml"] for item in totals.values()) == pytest.approx(trajectory.states[-1].blood.volume_ml)


@pytest.mark.parametrize("kappa", [1.0, 2.0, 0.5])
def test_v_is_kappa_times_the_circulating_volume_deviation_every_minute(kappa):
    trajectory = run(ARRIVAL, MIXED, 180, replace(DEFAULT_PROFILE, volume_preload_kappa=kappa))
    for state in trajectory.states:
        assert state.V == pytest.approx(kappa * state.blood.volume_ml, abs=1e-9)
    # Each blood change moves V once, by kappa x its volume, under its own source.
    for record in trajectory.records:
        volume = [d for d in record.deltas if d.channel is Channel.V]
        assert sorted((d.source.key, round(d.amount, 12)) for d in volume) == sorted(
            (c.source.key, round(kappa * c.signed_volume_ml, 12)) for c in record.blood)


def test_hb_never_moves_without_a_red_cell_or_volume_change_to_explain_it():
    trajectory = run(ARRIVAL, MIXED, 180)
    for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
        hb = [d for d in record.deltas if d.channel is Channel.HB]
        assert all(d.source == BLOOD_COMPOSITION for d in hb)
        if not record.blood:
            assert not hb and after.hb == before.hb
        else:
            assert {s for d in hb for s in d.modulated_by} <= {c.source for c in record.blood}
        assert after.hb == pytest.approx(blood_haemoglobin(after.blood, ARRIVAL, DEFAULT_PROFILE), abs=1e-12)


def test_stopping_the_bleeding_stops_new_losses_and_refill_continues():
    stopped = replace(BLEED, fraction_after_hemostasis=0.0)
    trajectory = run(ARRIVAL, (stopped, EndoscopicHemostasis("endoscopy", 60)), 240)
    states = trajectory.states
    assert all(state.blood.shed_ml == states[59].blood.shed_ml for state in states[60:])
    assert not any(c.process is BloodProcess.WHOLE_BLOOD_LOSS for record in trajectory.records[59:] for c in record.blood)
    assert states[240].blood.refill_ml > states[60].blood.refill_ml, "refill goes on after the bleed stops"
    assert states[240].blood.red_cells == states[60].blood.red_cells, "and brings no red cells"
    assert states[240].hb < states[60].hb and states[240].V > states[60].V, "so it dilutes while it restores volume"


def test_refill_and_saline_create_no_red_cells():
    for contributors in ((saline(),), (bp.ScriptedBloodLoss("loss", 0, 10, 30.0),)):
        trajectory = run(ARRIVAL, contributors, 240)
        created = [c for record in trajectory.records for c in record.blood
                   if c.process in (BloodProcess.PLASMA_REFILL, BloodProcess.CRYSTALLOID_IN)]
        assert created and all(c.red_cells == 0.0 for c in created)
        assert trajectory.states[-1].blood.transfused_red_cells == 0.0
        assert trajectory.states[-1].blood.red_cells <= 1.0


def test_red_cells_are_not_crystalloid():
    """The same circulating volume, as red cells or as crystalloid: only the red cells raise Hb."""
    @dataclass(frozen=True)
    class Infuse(Contributor):
        kind = SourceKind.SCRIPTED_EVENT
        type_name = "test_blood_infuse"
        id: str
        process: str

        def contribute(self, state, minute, signals, anchors, profile):
            if minute > 30:
                return Contribution()
            hb = 20.0 if self.process == "red_cell_transfusion" else None
            return Contribution(blood=(BloodFlow(self.process, 10.0, self.source, minute, "probe", hb_g_dl=hb),))

    cells = run(ARRIVAL, (Infuse("cells", "red_cell_transfusion"),), 30, replace(DEFAULT_PROFILE)).states[-1]
    water = run(ARRIVAL, (Infuse("water", "crystalloid_in"),), 30).states[-1]
    assert cells.V == pytest.approx(water.V) == pytest.approx(300.0)
    assert cells.hb > ARRIVAL.hb > water.hb
    assert cells.blood.red_cells > 1.0 == water.blood.red_cells


def test_no_legacy_drift_remains_active_in_parallel():
    """P2I-2T-12: the independent Hb drifts are gone, and nothing outside a probe may write V or Hb."""
    for cls in (GIHaemorrhage, Crystalloid, PackedRedCells):
        names = {item.name for item in fields(cls)}
        assert not names & {"hb_loss_g_dl_per_min", "volume_loss_ml_per_min", "hb_dilution_g_dl_per_ml",
                            "hb_g_dl_per_unit"}, cls
    trajectory = run(ARRIVAL, MIXED, 120)
    for record in trajectory.records:
        bleed = [d for d in record.deltas if d.source == BLEED.source]
        flows = [c for c in record.blood if c.source == BLEED.source]
        assert [d.channel for d in bleed] == [Channel.V] * len(flows) and len(flows) <= 1
        if flows:
            assert bleed[0].amount == pytest.approx(-flows[0].volume_ml), "one V effect per bleed minute"
    for kind in (SourceKind.DISEASE_MODULE, SourceKind.INTERVENTION, SourceKind.LOGISTIC_PROCESS):
        for channel in ("hb", "V"):
            with pytest.raises(ProvenanceError, match="shared blood state"):
                run(ARRIVAL, (Writer(kind, "drift", channel),), 1)
    run(ARRIVAL, (Writer(SourceKind.SCRIPTED_EVENT, "probe"),), 1)        # a declared probe still may
    # The legacy Hb literals are references only: no builder of the core reads them.
    import inspect
    from clinical_core import legacy_adapter
    from clinical_core.interventions import fluids
    from clinical_core.modules import gi_haemorrhage
    built = "".join(inspect.getsource(item) for item in (legacy_adapter.haemorrhage_from_legacy, legacy_adapter._build,
                                                        fluids, gi_haemorrhage))
    assert REFERENCE_ONLY and not any(name in built for name in REFERENCE_ONLY)
    assert "hemodilution_g_dl_per_ml" not in built


def test_a_flow_declares_only_what_its_source_may_and_no_haemoglobin_of_its_own():
    module = Source(SourceKind.DISEASE_MODULE, "bleed")
    order = Source(SourceKind.INTERVENTION, "order")
    with pytest.raises(ProvenanceError):
        BloodFlow(BloodProcess.PLASMA_REFILL, 1.0, module, 1, "refill is the core's own")
    with pytest.raises(ProvenanceError):
        BloodFlow(BloodProcess.WHOLE_BLOOD_LOSS, 1.0, module, 1, "loss", hb_g_dl=12.0)
    with pytest.raises(ProvenanceError):
        BloodFlow(BloodProcess.RED_CELL_TRANSFUSION, 300.0, order, 1, "a unit without its composition")
    with pytest.raises(ProvenanceError):
        BloodFlow(BloodProcess.CRYSTALLOID_IN, -5.0, order, 1, "volumes are positive; the process says the way")
    with pytest.raises(ProvenanceError):
        BloodFlow(BloodProcess.WHOLE_BLOOD_LOSS, 1.0, order, 1, "an order does not bleed")
    with pytest.raises(ProvenanceError):
        BloodChange(BloodProcess.PLASMA_REFILL, 5.0, 0.1, 0.0, PLASMA_REFILL, 1, "refill carrying red cells")


def test_the_accounting_check_refuses_a_state_its_records_do_not_explain():
    state, record = step(run(ARRIVAL, (), 0).states[0], (BLEED,), ARRIVAL)
    arrival = run(ARRIVAL, (), 0).states[0]
    _check_blood(arrival, state, record, ARRIVAL, DEFAULT_PROFILE)
    forged = state.evolve(blood=replace(state.blood, shed_ml=state.blood.shed_ml + 1.0))
    with pytest.raises(ProvenanceError, match="shed_ml"):
        _check_blood(arrival, forged, record, ARRIVAL, DEFAULT_PROFILE)
    doubled = replace(record, deltas=record.deltas + (ChannelDelta(Channel.V, -2.5, BLEED.source, 1, "again"),))
    with pytest.raises(ProvenanceError, match="V moved"):
        _check_blood(arrival, state, doubled, ARRIVAL, DEFAULT_PROFILE)
    drift = replace(record, deltas=record.deltas + (ChannelDelta(Channel.HB, -0.009, BLEED.source, 1, "drift"),))
    with pytest.raises(ProvenanceError, match="blood composition"):
        _check_blood(arrival, state, drift, ARRIVAL, DEFAULT_PROFILE)
    # A record whose whole blood left without its red cells (review F9), even with a state forged to match.
    (loss,) = [c for c in record.blood if c.process is BloodProcess.WHOLE_BLOOD_LOSS]
    bare = replace(loss, red_cells=0.0)
    forged = state.evolve(blood=replace(state.blood, shed_red_cells=0.0),
                          hb=blood_haemoglobin(replace(state.blood, shed_red_cells=0.0), ARRIVAL, DEFAULT_PROFILE))
    with pytest.raises(ProvenanceError, match="composition does not give"):
        _check_blood(arrival, forged, replace(record, blood=(bare,)), ARRIVAL, DEFAULT_PROFILE)


def test_probes_and_bounds_are_accounted_so_the_identities_hold_every_minute():
    """Review F2/F4: a declared probe may still move V or Hb directly; what it moves is accounted, so
    V = kappa x C + outside_v and Hb = composition + outside_hb hold every minute."""
    probes = (BLEED, Drift("preload", "V", 0, 30, -4.0), Drift("anaemia", "hb", 10, 20, -0.02), saline(start=5))
    trajectory = run(ARRIVAL, probes, 90)
    for state in trajectory.states:
        check_blood_identity(state, ARRIVAL, DEFAULT_PROFILE)
    end = trajectory.states[-1].blood
    assert end.outside_v == pytest.approx(-120.0) and end.outside_hb == pytest.approx(-0.2)
    clamped = run(ARRIVAL, (Drift("anaemia", "hb", 0, 60, -0.5),), 20).states[-1]
    assert clamped.hb == 3.0 and clamped.blood.outside_hb == pytest.approx(3.0 - ARRIVAL.hb)


def test_a_bound_never_cuts_what_the_blood_state_moved():
    """Review F2: Hb or V driven past their guards by the blood state stops the run instead of
    parting the channel from it; a probe's own excursion is still clamped and accounted."""
    with pytest.raises(UnresolvedBoundary, match="shared blood state takes hb"):
        run(replace(ARRIVAL, hb=17.0), (red_cells(units=10.0, duration=30.0),), 40)
    with pytest.raises(UnresolvedBoundary, match="shared blood state takes V"):
        run(ARRIVAL, (red_cells(units=12.0, duration=60.0),), 70)


def test_the_volume_guard_keeps_kappa_and_the_curve_scale_together():
    """Review F3: the V guard is on circulating volume, so (kappa, lambda) and (3 kappa, 3 lambda) stay
    the same patient up to it."""
    units = (red_cells(units=6.0, duration=60.0),)
    one = run(ARRIVAL, units, 70)
    three = run(ARRIVAL, units, 70, replace(DEFAULT_PROFILE, volume_preload_kappa=3.0,
                                            preload_curve_scale_ml=3 * DEFAULT_PROFILE.preload_curve_scale_ml))
    assert three.states[-1].V == pytest.approx(3 * one.states[-1].V) == pytest.approx(5400.0)
    assert three.derived()[-1].output_rel == pytest.approx(one.derived()[-1].output_rel, abs=1e-12)


def test_a_state_its_blood_state_does_not_explain_is_refused():
    """Review F4: a hand-made, edited or re-profiled state is refused at the start of a run or a step."""
    trajectory = run(ARRIVAL, (BLEED,), 60)
    middle = trajectory.states[30]
    with pytest.raises(CoreInvariantError, match="not explained by its blood state"):
        run(ARRIVAL, (BLEED,), 10, initial=run(ARRIVAL, (), 0).states[0].evolve(minute=30, V=-100.0))
    edited = middle.to_dict()
    edited["blood"]["shed_ml"] += 50.0
    with pytest.raises(CoreInvariantError, match="not explained by its blood state"):
        run(ARRIVAL, (BLEED,), 10, initial=CoreState.from_dict(edited))
    for changes in ({"volume_preload_kappa": 2.0}, {"arrival_circulating_volume_ml": 3000.0}):
        with pytest.raises(CoreInvariantError, match="not explained by its blood state"):
            run(ARRIVAL, (BLEED,), 10, replace(DEFAULT_PROFILE, **changes), initial=middle)
    with pytest.raises(CoreInvariantError, match="not explained by its blood state"):
        step(middle.evolve(hb=middle.hb - 0.5), (BLEED,), ARRIVAL)
    assert run(ARRIVAL, (BLEED,), 30, initial=middle).states[-1] == trajectory.states[60]


# Persistence ------------------------------------------------------------------------------------------

def test_the_blood_state_serializes_replays_and_deepcopies():
    trajectory = run(ARRIVAL, MIXED, 120)
    state = trajectory.states[-1]
    assert CoreState.from_dict(json.loads(json.dumps(state.to_dict()))) == state
    assert deepcopy(state) == state and deepcopy(state.blood) == state.blood
    assert BloodState.from_dict(state.blood.to_dict()) == state.blood
    stored = json.loads(json.dumps(scenario_to_dict(ARRIVAL, MIXED, 120)))
    arrival, rebuilt, minutes, profile = scenario_from_dict(stored)
    assert run(arrival, rebuilt, minutes, profile).digest() == trajectory.digest()
    resumed = run(ARRIVAL, MIXED, 60, initial=trajectory.states[60])
    assert resumed.states[-1] == state
    data = state.to_dict()
    del data["blood"]
    with pytest.raises(CoreInvariantError, match="blood state"):
        CoreState.from_dict(data)
    with pytest.raises(CoreInvariantError):
        BloodState.from_dict({**state.blood.to_dict(), "extra": 0.0})


def test_an_impossible_blood_state_or_profile_is_refused():
    with pytest.raises(CoreInvariantError):
        BloodState(shed_ml=-1.0)
    with pytest.raises(CoreInvariantError):
        BloodState(crystalloid_in_ml=10.0, crystalloid_out_ml=11.0)
    with pytest.raises(CoreInvariantError):
        BloodState(shed_red_cells=1.0)
    with pytest.raises(CoreInvariantError, match="circulating volume"):
        blood_haemoglobin(BloodState(shed_ml=B0, shed_red_cells=0.5), ARRIVAL, DEFAULT_PROFILE)
    for changes in ({"plasma_refill_target_share": 1.5}, {"plasma_refill_tau_min": 0.5},
                    {"volume_preload_kappa": 0.0}, {"arrival_circulating_volume_ml": 0.0},
                    {"plasma_refill_capacity_ml": -1.0}):
        with pytest.raises(CoreInvariantError):
            CoreProfile(**changes)


# P2I-2T-2..7: behaviour ----------------------------------------------------------------------------

def test_one_bleed_drives_volume_and_red_cells_at_the_current_composition():
    trajectory = run(ARRIVAL, (BLEED, ProtonPumpInhibitor("order-ppi", 10), EndoscopicHemostasis("endoscopy", 60)), 90)
    for before, record in zip(trajectory.states, trajectory.records):
        (loss,) = [c for c in record.blood if c.process is BloodProcess.WHOLE_BLOOD_LOSS]
        assert loss.red_cells == pytest.approx(loss.volume_ml * before.blood.red_cells / (B0 + before.blood.volume_ml))
        assert loss.hb_g_dl == pytest.approx(before.hb)
    rates = [c.volume_ml for record in trajectory.records for c in record.blood
             if c.process is BloodProcess.WHOLE_BLOOD_LOSS]
    assert rates[:10] == [2.5] * 10 and rates[11:59] == [pytest.approx(2.0)] * 48 and rates[59:] == [
        pytest.approx(0.25)] * 31
    modulated = {c.minute: c.modulated_by for record in trajectory.records for c in record.blood
                 if c.process is BloodProcess.WHOLE_BLOOD_LOSS}
    assert modulated[5] == () and modulated[30] == (ProtonPumpInhibitor("order-ppi", 10).source,)
    assert modulated[70] == (EndoscopicHemostasis("endoscopy", 60).source,)


def test_acute_whole_blood_loss_does_not_lower_hb_and_refill_does_gradually():
    loss = bp.ScriptedBloodLoss("acute", 0, 10, 30.0)
    alone = run(ARRIVAL, (loss,), 240, replace(DEFAULT_PROFILE, plasma_refill_target_share=0.0))
    assert all(state.hb == pytest.approx(ARRIVAL.hb, abs=1e-12) for state in alone.states)
    assert alone.states[-1].V == pytest.approx(-300.0)
    refilled = run(ARRIVAL, (loss,), 240).states
    hb = [state.hb for state in refilled]
    assert all(later <= earlier for earlier, later in zip(hb, hb[1:])) and hb[240] < hb[10] < ARRIVAL.hb
    assert refilled[240].V > refilled[10].V > -300.0


def test_refill_is_gradual_bounded_never_backwards_and_has_a_finite_capacity():
    loss = bp.ScriptedBloodLoss("loss", 0, 10, 30.0)
    trajectory = run(ARRIVAL, (loss,), 600)
    profile = DEFAULT_PROFILE
    for before, after in zip(trajectory.states, trajectory.states[1:]):
        target = min(profile.plasma_refill_capacity_ml, profile.plasma_refill_target_share * before.blood.shed_ml)
        assert before.blood.refill_ml <= after.blood.refill_ml <= max(target, before.blood.refill_ml) + 1e-9
        assert after.blood.refill_ml - before.blood.refill_ml == pytest.approx(plasma_refill(before.blood, profile))
    small = replace(DEFAULT_PROFILE, plasma_refill_capacity_ml=50.0)
    capped = run(ARRIVAL, (loss,), 600, small).states
    assert max(state.blood.refill_ml for state in capped) <= 50.0
    assert capped[-1].blood.refill_ml == pytest.approx(50.0, abs=0.5)
    assert plasma_refill(BloodState(shed_ml=100.0, refill_ml=80.0), DEFAULT_PROFILE) == 0.0, "never past the target"


def test_refill_never_takes_the_circulation_above_arrival():
    """Refill restores part of a deficit: with fluids or red cells above arrival it waits (review F1)."""
    for contributors in ((BLEED, red_cells(units=3.0, duration=30.0)), (bp.ScriptedBloodLoss("loss", 0, 10, 40.0),
                                                                       red_cells(start=10, units=3.0))):
        trajectory = run(ARRIVAL, contributors, 300)
        for before, after, record in zip(trajectory.states, trajectory.states[1:], trajectory.records):
            refill = [c.volume_ml for c in record.blood if c.process is BloodProcess.PLASMA_REFILL]
            if before.blood.volume_ml >= 0:
                assert not refill, before.minute
            else:
                assert sum(refill) <= -before.blood.volume_ml + 1e-12
    assert plasma_refill(BloodState(shed_ml=400.0, transfused_ml=600.0, transfused_red_cells=0.4),
                         DEFAULT_PROFILE) == 0.0
    small = plasma_refill(BloodState(shed_ml=400.0, transfused_ml=399.0, transfused_red_cells=0.4), DEFAULT_PROFILE)
    assert 0.0 < small <= 1.0


def test_crystalloid_dilutes_and_its_dilution_partly_reverses():
    trajectory = run(ARRIVAL, (saline(volume=1000.0),), 240)
    hb = [state.hb for state in trajectory.states]
    lowest = min(range(len(hb)), key=hb.__getitem__)
    assert 0 < lowest < 240 and hb[lowest] < hb[240] < ARRIVAL.hb
    retained = trajectory.states[-1].blood.volume_ml
    assert hb[240] == pytest.approx(ARRIVAL.hb * B0 / (B0 + retained)) and trajectory.states[-1].blood.red_cells == 1.0


def test_a_red_cell_unit_brings_its_content_and_volume_from_one_composition():
    one = run(ARRIVAL, (red_cells(units=1.0, duration=30.0),), 60).states[-1]
    content = 300.0 * 20.0 / (ARRIVAL.hb * B0)
    assert one.blood.transfused_ml == pytest.approx(300.0) and one.blood.transfused_red_cells == pytest.approx(content)
    assert one.hb == pytest.approx(ARRIVAL.hb * (1 + content) * B0 / (B0 + 300.0))
    # The rise depends on the circulation it enters: the same unit raises a higher Hb by less.
    higher = replace(ARRIVAL, hb=12.0)
    rise_low = one.hb - ARRIVAL.hb
    rise_high = run(higher, (red_cells(units=1.0, duration=30.0),), 60).states[-1].hb - 12.0
    assert rise_high < rise_low


def test_only_kappa_over_lambda_reaches_the_haemodynamics():
    """P2I-2T-7/8: V = kappa x C; output reads V / lambda, so (kappa, lambda) and (2 kappa, 2 lambda)
    give the same patient; Hb reads C / B0 and never kappa."""
    base = run(ARRIVAL, MIXED, 120)
    scaled = run(ARRIVAL, MIXED, 120, replace(DEFAULT_PROFILE, volume_preload_kappa=2.0,
                                              preload_curve_scale_ml=2 * DEFAULT_PROFILE.preload_curve_scale_ml))
    for one, two, d1, d2 in zip(base.states, scaled.states, base.derived(), scaled.derived()):
        assert two.V == pytest.approx(2 * one.V, abs=1e-9) and two.hb == pytest.approx(one.hb, abs=1e-12)
        assert d2.output_rel == pytest.approx(d1.output_rel, abs=1e-12) and d2.sbp == pytest.approx(d1.sbp, abs=1e-9)
    assert "Effective circulating volume / preload coordinate (V)" == CHANNEL_DEFINITIONS[Channel.V][2]
    assert "not a measured blood volume" in CHANNEL_DEFINITIONS[Channel.V][1]


def test_arrival_infers_no_pre_arrival_loss_from_hb():
    state = run(ARRIVAL, (), 0).states[0]
    assert state.blood == BloodState() and state.V == 0.0 and state.hb == ARRIVAL.hb
    assert blood_haemoglobin(state.blood, ARRIVAL, DEFAULT_PROFILE) == ARRIVAL.hb
    anaemic = replace(ARRIVAL, hb=4.0)
    assert run(anaemic, (), 0).states[0].blood == BloodState(), "the arrival Hb sets the composition, not a loss"


# The probes (P2I-2T-11) ------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return bp.results()


def test_the_probes_show_what_the_faculty_asked(probes):
    def at(name, minute, key):
        return probes[name]["points"][str(minute)][key]
    assert all(at("A", m, "hb") == pytest.approx(6.4) for m in bp.TIMES)                       # A: no refill
    assert at("B", 240, "hb") < at("B", 10, "hb") < 6.4 and at("B", 240, "refill_ml") > 0     # B
    assert at("C", 240, "shed_ml") == pytest.approx(600.0) and at("C", 240, "hb") < at("C", 120, "hb")
    assert at("D", 240, "shed_ml") == at("D", 120, "shed_ml") and at("D", 240, "refill_ml") > at("D", 120, "refill_ml")
    assert at("D", 240, "red_cells") == at("D", 120, "red_cells") and at("D", 240, "hb") < at("D", 120, "hb")
    for name in ("E", "F"):
        assert probes[name]["hb_lowest"] < at(name, 240, "hb") < 6.4 and at(name, 240, "red_cells") == 1.0
    assert at("F", 30, "crystalloid_ml") > at("E", 30, "crystalloid_ml")
    assert 6.4 < at("G", 240, "hb") < at("H", 240, "hb") and at("H", 240, "transfused_ml") == pytest.approx(600.0)
    # I: the bleed goes on after the units; whole-blood loss alone keeps Hb, and refill waits for a deficit.
    assert at("I", 60, "hb") > 6.4 and at("I", 240, "hb") <= at("I", 60, "hb") + 1e-12
    assert at("I", 240, "shed_ml") > at("I", 60, "shed_ml") and at("I", 240, "V") < at("I", 60, "V")
    assert at("J", 240, "hb") < at("C", 240, "hb") and at("J", 240, "V") > at("C", 240, "V")
    k = [at("K", m, "shed_ml") for m in (120, 180, 240)]
    assert (k[2] - k[1]) == pytest.approx(0.1 * 2.5 * 60) and at("K", 240, "V") > at("K", 120, "V")
    for probe in probes.values():
        for row in probe["points"].values():
            assert row["hb"] == pytest.approx(row["hb_from_blood"], abs=1e-12)
            assert row["V"] == pytest.approx(row["circulating_ml"], abs=1e-9)


def test_the_probes_change_nothing_canonical_and_run_no_fd_lac_rule():
    import ast
    tree = ast.parse(Path(bp.__file__).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"faculty_constraints", "lactate_constraints", "decision_pack"}
    assert DEFAULT_PROFILE.oxygen_extraction_reserve == 1.0
    assert DEFAULT_PROFILE.preload_curve_scale_ml == pytest.approx(300.0 / 0.36)


def test_the_probe_document_is_generated_from_the_current_code():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["probes_digest"] == bp.probes_digest(), "the probes are stale: regenerate them"
    assert data["probes_digest"] in document
    assert data["probes"] == json.loads(json.dumps(bp.results(), sort_keys=True))
    assert data["golden"]["after_sha256"] in document
    assert bp.apply(document, bp.render(data)) == document, (
        "the document differs from the probes: run python -m clinical_core.blood_probes --write")
