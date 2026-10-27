"""Phase 2 shadow core, WP2-2: the GI haemorrhage module and the scripted rhythm/pump events.

Magnitudes are the family engine's (family_engine._minute and GI_BLEED), converted to the
core's units: 0.003 circulation/min x 833.3 mL per unit = 2.5 mL-equivalent/min of whole blood;
80 % of the rate with a proton-pump inhibitor; 10 % after hemostasis. Since P2I-2T the module
declares one whole-blood flow: Hb follows from the shared blood state, not from a drift of its own.
"""
from dataclasses import dataclass

import pytest

from clinical_core import (Anchors, Channel, Contribution, Contributor, CoreInvariantError, RhythmCode, RhythmState,
                           Signal, SourceKind, attribution, run)
from clinical_core.derived import DEFAULT_PROFILE, blood_haemoglobin
from clinical_core.provenance import BloodProcess
from clinical_core import signals as names
from clinical_core.integration import register
from clinical_core.logistics import EndoscopicHemostasis
from clinical_core.modules import GIHaemorrhage, ScriptedPumpChange, ScriptedRhythmEvent

ARRIVAL = Anchors(case_id="gi_bleed_57m", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0, crt_s=5.0,
                  lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(124.0),
                  consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", blood_loss_ml_per_min=2.5, fraction_with_ppi=0.8,
                      fraction_after_hemostasis=0.1)


@register
@dataclass(frozen=True)
class PPIStub(Contributor):
    """Publishes the PPI signal from a minute; the real intervention is in WP2-3 (test only)."""

    kind = SourceKind.INTERVENTION
    type_name = "test_ppi_stub"
    id: str
    start_minute: int

    def signals(self, minute):
        return (Signal(names.PPI, self.source, self.start_minute),) if minute > self.start_minute else ()


def deltas_of(trajectory, channel, source_kind=SourceKind.DISEASE_MODULE):
    return [sum(d.amount for d in record.deltas if d.channel is channel and d.source.kind is source_kind)
            for record in trajectory.records]


def test_untreated_bleeding_is_the_same_loss_every_minute():
    trajectory = run(ARRIVAL, (BLEED,), 120)
    assert deltas_of(trajectory, Channel.V) == [-2.5] * 120
    assert deltas_of(trajectory, Channel.HB) == [0.0] * 120, "the module has no Hb drift of its own (P2I-2T)"
    flows = [[(c.process, c.volume_ml) for c in record.blood if c.source == BLEED.source]
             for record in trajectory.records]
    assert flows == [[(BloodProcess.WHOLE_BLOOD_LOSS, 2.5)]] * 120
    sixty = trajectory.states[60]
    assert sixty.blood.shed_ml == pytest.approx(150.0)
    assert sixty.V == pytest.approx(sixty.blood.volume_ml) and sixty.V > -150.0, "refill restores part of it"
    assert sixty.hb == pytest.approx(blood_haemoglobin(sixty.blood, ARRIVAL, DEFAULT_PROFILE)) and sixty.hb < 6.7
    assert run(ARRIVAL, (BLEED,), 120).digest() == trajectory.digest()


def test_bleeding_reaches_perfusion_through_the_core():
    """Proposal §2.4: blood loss must reach perfusion. Here it does, in every derived quantity."""
    derived = run(ARRIVAL, (BLEED,), 90).derived()
    for earlier, later in zip(derived, derived[1:]):
        assert later.sbp < earlier.sbp and later.pulse_rate_bpm > earlier.pulse_rate_bpm
        assert later.crt_s > earlier.crt_s and later.delivery_rel < earlier.delivery_rel
        assert later.lactate >= earlier.lactate
    assert derived[-1].lactate > ARRIVAL.lactate and derived[-1].respiratory_rate > ARRIVAL.respiratory_rate


def test_only_the_module_and_the_core_coupling_change_anything():
    trajectory = run(ARRIVAL, (BLEED,), 60)
    volume = attribution(trajectory.records, Channel.V)
    assert set(volume) == {"disease_module:gi_haemorrhage", "core_coupling:plasma_refill"}
    assert volume["disease_module:gi_haemorrhage"] == pytest.approx(-150.0)
    assert volume["core_coupling:plasma_refill"] == pytest.approx(trajectory.states[-1].blood.refill_ml)
    assert set(attribution(trajectory.records, Channel.HB)) == {"core_coupling:blood_composition"}
    assert set(attribution(trajectory.records, Channel.D)) == {"core_coupling:oxygen_debt"}
    untouched = (Channel.T, Channel.P, Channel.L, Channel.G, Channel.W, Channel.N, Channel.GLUCOSE, Channel.K)
    assert all(attribution(trajectory.records, channel) == {} for channel in untouched)


def test_a_proton_pump_inhibitor_slows_the_bleeding_from_the_minute_after_it_starts():
    trajectory = run(ARRIVAL, (BLEED, PPIStub("order-ppi", 10)), 30)
    assert deltas_of(trajectory, Channel.V)[:10] == [-2.5] * 10
    assert deltas_of(trajectory, Channel.V)[10:] == [pytest.approx(-2.0)] * 20
    slowed = [d for d in trajectory.records[10].deltas if d.source.kind is SourceKind.DISEASE_MODULE]
    assert slowed and all(d.modulated_by == (PPIStub("order-ppi", 10).source,) for d in slowed)
    assert all(c.modulated_by == (PPIStub("order-ppi", 10).source,) for c in trajectory.records[10].blood
               if c.source == BLEED.source)
    assert all(d.modulated_by == () for record in trajectory.records[:10] for d in record.deltas
               if d.source.kind is SourceKind.DISEASE_MODULE)


def test_hemostasis_takes_effect_in_the_minute_the_procedure_completes():
    endoscopy = EndoscopicHemostasis("endoscopy", completes_at_minute=60)
    trajectory = run(ARRIVAL, (BLEED, PPIStub("order-ppi", 0), endoscopy), 90)
    volume = deltas_of(trajectory, Channel.V)
    assert volume[58] == pytest.approx(-2.0) and volume[59] == pytest.approx(-0.25) and volume[89] == pytest.approx(-0.25)
    assert trajectory.states[59].internal_for("disease_module:gi_haemorrhage")["controlled_at"] is None
    assert trajectory.states[60].internal_for("disease_module:gi_haemorrhage")["controlled_at"] == 60
    kinds = [(e.kind, e.minute) for record in trajectory.records for e in record.events]
    assert kinds == [("source_controlled", 60), ("procedure_completed", 60)]
    after = [d for d in trajectory.records[60].deltas if d.source.kind is SourceKind.DISEASE_MODULE]
    assert all(d.modulated_by == (endoscopy.source,) for d in after)


def test_the_module_never_writes_an_observable_or_the_rhythm():
    trajectory = run(ARRIVAL, (BLEED,), 30)
    assert all(not record.transitions and not record.settings for record in trajectory.records)
    assert {d.channel for record in trajectory.records for d in record.deltas
            if d.source.kind is SourceKind.DISEASE_MODULE} == {Channel.V}
    assert {c.process for record in trajectory.records for c in record.blood
            if c.source.kind is SourceKind.DISEASE_MODULE} == {BloodProcess.WHOLE_BLOOD_LOSS}


def test_an_impossible_bleeding_specification_is_refused():
    with pytest.raises(CoreInvariantError):
        GIHaemorrhage("x", blood_loss_ml_per_min=-1.0, fraction_with_ppi=.8, fraction_after_hemostasis=.1)
    with pytest.raises(CoreInvariantError):
        GIHaemorrhage("x", blood_loss_ml_per_min=1.0, fraction_with_ppi=1.2, fraction_after_hemostasis=.1)
    with pytest.raises(CoreInvariantError):
        EndoscopicHemostasis("x", completes_at_minute=0)


# Rhythm and pump: the coupling through which a module will act on output (B) ------------

STABLE = Anchors(case_id="synthetic_inferior", sbp=120.0, dbp=75.0, hr=72.0, spo2=96.0, respiratory_rate=16.0,
                 crt_s=2.0, lactate=1.2, hb=13.5, glucose=110.0, k=4.2, fio2=0.21, rhythm=RhythmState.sinus(72.0),
                 consciousness_level=0)
BLOCK = RhythmState(RhythmCode.COMPLETE_AV_BLOCK, 40.0, 0.7, True)


def test_a_scripted_block_changes_rate_and_output_together():
    event = ScriptedRhythmEvent("av_block", 20, BLOCK, preventability="not preventable in this simulator")
    derived = run(STABLE, (event,), 30).derived()
    assert derived[19].rhythm is RhythmCode.SINUS and derived[19].pulse_rate_bpm == 72.0
    assert derived[20].rhythm is RhythmCode.COMPLETE_AV_BLOCK and derived[20].pulse_rate_bpm == 40.0
    assert derived[20].sbp == pytest.approx(120.0 - 45 * 0.3) and derived[20].output_rel == pytest.approx(0.7)
    events = [e for record in run(STABLE, (event,), 30).records for e in record.events]
    assert [(e.kind, e.cause_class, e.preventability, e.severity) for e in events] == [
        ("rhythm_change", "natural_history", "not preventable in this simulator", "significant")]


def test_pump_depression_and_a_block_multiply():
    pump = ScriptedPumpChange("ischaemia", 0, 30, -0.01, preventability="preventable by reperfusion before minute 30")
    event = ScriptedRhythmEvent("av_block", 20, BLOCK, preventability="not preventable in this simulator")
    trajectory = run(STABLE, (pump, event), 40)
    assert trajectory.states[30].P == pytest.approx(0.7) and trajectory.states[40].P == pytest.approx(0.7)
    assert trajectory.derived()[40].output_rel == pytest.approx(0.7 * 0.7)
    assert attribution(trajectory.records, Channel.P) == {"scripted_event:ischaemia": pytest.approx(-0.3)}


def test_a_scripted_arrest_is_terminal_and_a_later_event_does_not_revive():
    arrest = ScriptedRhythmEvent("collapse", 10, RhythmState.asystole(), preventability="not preventable in this simulator")
    later = ScriptedRhythmEvent("block_after", 15, BLOCK, preventability="not preventable in this simulator")
    trajectory = run(STABLE, (arrest, later), 20)
    final = trajectory.derived()[-1]
    assert not final.pulse_present and final.sbp is None and final.monitor_rate_bpm == 0.0
    assert trajectory.states[-1].terminal_since == 10 and trajectory.states[-1].R == RhythmState.asystole()
    events = [(e.kind, e.minute, e.severity) for record in trajectory.records for e in record.events]
    assert events == [("rhythm_change", 10, "critical"), ("rhythm_event_not_applied", 15, "info")]


def test_a_scripted_event_must_declare_its_preventability():
    with pytest.raises(CoreInvariantError):
        ScriptedRhythmEvent("x", 5, BLOCK, preventability="")
    with pytest.raises(CoreInvariantError):
        ScriptedPumpChange("x", 5, 5, -.01, preventability="not preventable")
