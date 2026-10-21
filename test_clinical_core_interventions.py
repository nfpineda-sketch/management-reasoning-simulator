"""Phase 2 shadow core, WP2-3: interventions keep their order's identity and their timing.

Fluid magnitudes are the family engine's GI_BLEED values converted to mL-equivalents
(0.00015 circulation/mL x 833.3 = 0.125 mL-eq/mL; 60 % transient, tau 30 min; 0.0006 g/dL
per mL), and one red-cell unit is 300 mL-eq and 0.85 g/dL (family_engine._minute).
"""
import json

import pytest

from clinical_core import Anchors, Channel, CoreInvariantError, RhythmState, SourceKind, attribution, run
from clinical_core.integration import scenario_from_dict, scenario_to_dict
from clinical_core.interventions import Crystalloid, Oxygen, PackedRedCells, ProtonPumpInhibitor
from clinical_core.modules import GIHaemorrhage

ARRIVAL = Anchors(case_id="gi_bleed_72f", sbp=98.0, dbp=62.0, hr=112.0, spo2=96.0, respiratory_rate=24.0, crt_s=4.0,
                  lactate=3.4, hb=6.4, glucose=130.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(112.0),
                  consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.009, 0.8, 0.1)


def saline(order_id="order-saline", start=0, volume=1000.0, duration=None, stop=None, ahead=0.0):
    return Crystalloid(order_id, start, volume, duration, untimed_rate_ml_per_min=50.0, effective_ml_per_ml=0.125,
                       transient_share=0.6, leak_tau_min=30.0, hb_dilution_g_dl_per_ml=0.0006, stop_minute=stop,
                       stopped_by=None if stop is None else "order-stop", queued_ahead_ml=ahead)


def blood(order_id="order-prbc", start=0, units=2.0, duration=None, stop=None):
    return PackedRedCells(order_id, start, units, duration, untimed_units_per_min=1 / 30, volume_ml_per_unit=300.0,
                          hb_g_dl_per_unit=0.85, stop_minute=stop)


def from_order(trajectory, order_id, channel):
    return [sum(d.amount for d in record.deltas if d.channel is channel and d.source.id == order_id)
            for record in trajectory.records]


def delivered(trajectory, order_id, field="delivered_ml"):
    return trajectory.states[-1].internal_for(f"intervention:{order_id}").get(field, 0.0)


def test_an_order_acts_only_from_the_minute_after_it_is_given():
    trajectory = run(ARRIVAL, (saline(start=5, duration=20.0),), 40)
    hb = from_order(trajectory, "order-saline", Channel.HB)
    assert hb[:5] == [0.0] * 5 and all(value == pytest.approx(-0.03) for value in hb[5:25]) and hb[25:] == [0.0] * 15
    assert delivered(trajectory, "order-saline") == pytest.approx(1000.0)
    volume = from_order(trajectory, "order-saline", Channel.V)
    assert volume[:5] == [0.0] * 5 and volume[5] > 0
    assert all(later < 0 for later in volume[25:]), "after the bag, only redistribution remains"


def test_an_untimed_litre_runs_at_the_default_rate():
    trajectory = run(ARRIVAL, (saline(),), 30)
    hb = from_order(trajectory, "order-saline", Channel.HB)
    assert all(value == pytest.approx(-0.03) for value in hb[:20]) and hb[20:] == [0.0] * 10


def test_a_stopped_bag_keeps_what_it_delivered():
    trajectory = run(ARRIVAL, (saline(start=5, duration=20.0, stop=10),), 30)
    assert delivered(trajectory, "order-saline") == pytest.approx(250.0)
    assert from_order(trajectory, "order-saline", Channel.HB)[10:] == [0.0] * 20


def test_crystalloid_dilutes_and_redistributes():
    trajectory = run(ARRIVAL, (saline(),), 240)
    assert trajectory.states[-1].hb == pytest.approx(6.4 - 0.6)
    retained = trajectory.states[-1].V
    assert retained == pytest.approx(1000 * 0.125 * 0.4, rel=1e-3), "40 % of the expansion stays"
    assert attribution(trajectory.records, Channel.V) == {"intervention:order-saline": pytest.approx(retained)}


def test_blood_stays_in_the_vessels_and_carries_oxygen():
    trajectory = run(ARRIVAL, (blood(units=1.0),), 40)
    assert trajectory.states[-1].V == pytest.approx(300.0) and trajectory.states[-1].hb == pytest.approx(6.4 + 0.85)
    assert delivered(trajectory, "order-prbc", "delivered_units") == pytest.approx(1.0)
    assert from_order(trajectory, "order-prbc", Channel.V)[30:] == [0.0] * 10


def test_in_active_bleeding_blood_does_more_than_crystalloid_by_the_hour():
    """The family engine's faculty request of 2026-09-18, checked here as a directional assertion."""
    with_saline = run(ARRIVAL, (BLEED, saline(volume=2000.0, duration=20.0)), 60).derived()
    with_blood = run(ARRIVAL, (BLEED, blood(units=2.0, duration=60.0)), 60).derived()
    assert with_saline[60].sbp < with_saline[20].sbp, "the pressure bought by crystalloid fades"
    assert with_blood[60].sbp >= with_saline[60].sbp + 10
    hb_saline = run(ARRIVAL, (BLEED, saline(volume=2000.0, duration=20.0)), 60).states[-1].hb
    hb_blood = run(ARRIVAL, (BLEED, blood(units=2.0, duration=60.0)), 60).states[-1].hb
    assert hb_blood > hb_saline + 1.5


def test_oxygen_is_a_setting_with_its_own_start_and_stop():
    trajectory = run(ARRIVAL, (Oxygen("order-o2", 3, 0.28, stop_minute=10),), 15)
    settings = [(s.minute, s.value, s.source.id) for record in trajectory.records for s in record.settings]
    assert settings == [(4, 0.28, "order-o2"), (11, 0.21, "order-o2")]
    spo2 = [d.spo2 for d in trajectory.derived()]
    assert spo2[3] == 96.0 and spo2[4] == pytest.approx(96.0 + 30 * 0.07) and spo2[11] == 96.0
    assert all(not record.deltas or all(d.source.kind is not SourceKind.INTERVENTION for d in record.deltas)
               for record in trajectory.records)


def test_a_proton_pump_inhibitor_acts_only_through_the_bleeding_it_slows():
    trajectory = run(ARRIVAL, (BLEED, ProtonPumpInhibitor("order-ppi", 10)), 20)
    assert all(d.source.kind is not SourceKind.INTERVENTION for record in trajectory.records for d in record.deltas)
    bleed = [d for d in trajectory.records[15].deltas if d.channel is Channel.V and d.source.id == "gi_haemorrhage"]
    assert bleed[0].amount == pytest.approx(-2.0) and bleed[0].modulated_by == (ProtonPumpInhibitor("order-ppi", 10).source,)
    alone = run(ARRIVAL, (ProtonPumpInhibitor("order-ppi", 10),), 20)
    assert alone.states[-1].V == 0.0, "with nothing bleeding, a PPI changes nothing"


def test_every_change_names_the_order_that_caused_it():
    orders = (saline("order-a", 0, 500.0, 15.0), blood("order-b", 5, 1.0), Oxygen("order-c", 2, 0.4),
              ProtonPumpInhibitor("order-d", 0))
    trajectory = run(ARRIVAL, (BLEED,) + orders, 60)
    sources = {d.source.key for record in trajectory.records for d in record.deltas}
    assert sources == {"core_coupling:oxygen_debt", "disease_module:gi_haemorrhage", "intervention:order-a",
                       "intervention:order-b"}
    volume = attribution(trajectory.records, Channel.V)
    assert volume["intervention:order-b"] == pytest.approx(300.0)
    assert sum(volume.values()) == pytest.approx(trajectory.states[-1].V)


def test_orders_listed_in_any_order_give_the_same_patient():
    orders = (BLEED, saline("order-a", 0, 500.0, 15.0), blood("order-b", 5, 1.0), Oxygen("order-c", 2, 0.4),
              ProtonPumpInhibitor("order-d", 0))
    assert run(ARRIVAL, orders, 60).digest() == run(ARRIVAL, tuple(reversed(orders)), 60).digest()


def test_a_scenario_with_orders_replays_from_its_serialized_form():
    orders = (BLEED, saline("order-a", 0, 500.0, 15.0, stop=12), blood("order-b", 5, 2.0, 60.0),
              Oxygen("order-c", 2, 0.4, 30), ProtonPumpInhibitor("order-d", 0))
    stored = json.loads(json.dumps(scenario_to_dict(ARRIVAL, orders, 90)))
    arrival, rebuilt, minutes, profile = scenario_from_dict(stored)
    assert run(arrival, rebuilt, minutes, profile).digest() == run(ARRIVAL, orders, 90).digest()


def test_impossible_orders_are_refused():
    for build in (lambda: saline(volume=-1.0), lambda: saline(duration=0.0), lambda: saline(stop=-1),
                  lambda: saline(ahead=-5.0), lambda: saline(duration=20.0, ahead=100.0),
                  lambda: Crystalloid("x", 0, 500.0, None, 50.0, .125, .6, 30.0, .0006, stop_minute=4),
                  lambda: blood(units=0.0), lambda: Oxygen("o", 0, 0.1), lambda: Oxygen("o", -1, 0.4),
                  lambda: Oxygen("o", 5, 0.4, stop_minute=5), lambda: Oxygen("o", 1.5, 0.4),
                  lambda: ProtonPumpInhibitor("p", 3, 2)):
        with pytest.raises(CoreInvariantError):
            build()


def test_untimed_orders_share_one_line():
    """A second untimed litre given at minute 5 waits for the 750 mL still running: 50 mL/min in all."""
    first, second = saline("order-a"), saline("order-b", start=5, ahead=750.0)
    trajectory = run(ARRIVAL, (first, second), 50)
    total = [-(a + b) / 0.0006 for a, b in zip(from_order(trajectory, "order-a", Channel.HB),
                                                 from_order(trajectory, "order-b", Channel.HB))]
    assert all(value == pytest.approx(50.0) for value in total[:40]) and total[40:] == [0.0] * 10
    assert from_order(trajectory, "order-b", Channel.HB)[:20] == [0.0] * 20


def test_a_queued_bag_starts_where_its_receipt_says_even_mid_minute():
    trajectory = run(ARRIVAL, (saline("order-q", start=7.5, duration=10.0),), 20)
    hb = from_order(trajectory, "order-q", Channel.HB)
    assert hb[:7] == [0.0] * 7 and hb[7] == pytest.approx(-0.0006 * 50.0) and hb[8] == pytest.approx(-0.0006 * 100.0)
    assert delivered(trajectory, "order-q") == pytest.approx(1000.0)


def test_a_stop_names_the_order_that_stopped_the_bag():
    trajectory = run(ARRIVAL, (saline(start=0, duration=40.0, stop=10),), 20)
    assert delivered(trajectory, "order-saline") == pytest.approx(250.0)
    assert saline(stop=10).to_spec()["stopped_by"] == "order-stop"


def test_oxygen_held_by_the_latest_order_and_a_stop_never_guesses():
    two = run(ARRIVAL, (Oxygen("order-a", 0, 0.4), Oxygen("order-b", 10, 0.6)), 15)
    assert [s.value for record in two.records for s in record.settings] == [0.4, 0.6]
    assert two.states[-1].fio2 == 0.6
    with pytest.raises(CoreInvariantError):
        run(ARRIVAL, (Oxygen("order-a", 0, 0.4, stop_minute=20), Oxygen("order-b", 10, 0.6)), 25)
    alone = run(ARRIVAL, (Oxygen("order-a", 0, 0.4, stop_minute=20),), 25)
    assert alone.states[-1].fio2 == ARRIVAL.fio2
