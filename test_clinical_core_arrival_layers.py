"""Phase 2 shadow core, P2F-1/3: authored arrival, physiological reference and arrival dynamic state.

The arrival observation is what the resident sees; the reference is the patient's non-acute
normal; the dynamic state is the acute physiology already present. Every value here is a
synthetic probe value, not a GI mapping.
"""
from dataclasses import fields, replace

import pytest

from clinical_core import Anchors, run
from clinical_core.bands import ARRIVAL, Drift
from clinical_core.derived import (DEFAULT_PROFILE, arrival_layers, arrival_state, check_arrival_reconstruction,
                                   derive)
from clinical_core.state import ARRIVAL_LAYERS, CASE_PARAMETERS, CoreInvariantError, RhythmState

#: A synthetic shocked arrival (not a bank case) with every arrival layer declared.
SHOCKED = dict(ARRIVAL, case_id="synthetic_shock", sbp=88.0, dbp=54.0, hr=124.0, rhythm=RhythmState.sinus(124.0),
               lactate=4.4, hb=6.7, crt_s=5.0, respiratory_rate=26.0)
REFERENCES = {"intrinsic_sinus_rate": 80.0, "arrival_lactate_excess": 3.4, "arrival_oxygen_debt": 60.0,
              "arrival_delivery_ratio": 0.8, "reference_preload_fraction": 0.75, "preload_fraction": 0.4}


def shocked(**declared):
    values = {**REFERENCES, **declared}
    return Anchors(**{**SHOCKED, **values, "declared": {name: "synthetic_probe" for name in values}})


def test_every_arrival_field_belongs_to_exactly_one_layer_and_no_layer_is_a_channel():
    names = [item.name for item in fields(Anchors) if item.name not in ("case_id", "declared")]
    layered = [name for layer in ARRIVAL_LAYERS.values() for name in layer]
    assert sorted(layered) == sorted(names) and len(layered) == len(set(layered))
    assert set(CASE_PARAMETERS) == set(ARRIVAL_LAYERS["physiological_reference"]) | set(
        ARRIVAL_LAYERS["arrival_dynamic_state"])


def test_the_three_layers_are_reported_apart():
    layers = arrival_layers(shocked())
    assert (layers.authored.hr, layers.authored.lactate, layers.authored.map) == (124.0, 4.4, (88 + 2 * 54) / 3)
    assert layers.reference.intrinsic_sinus_rate == 80.0
    assert layers.reference.lactate_clearance_baseline == pytest.approx(1.0)
    assert layers.dynamic.sympathetic_bpm == 44.0 and layers.dynamic.oxygen_debt == 60.0
    assert layers.dynamic.lactate_excess == 3.4 and layers.dynamic.delivery_deficit == pytest.approx(0.2)
    assert layers.dynamic.volume_deficit_ml > 0, "arriving below the euvolemic reference"
    assert layers.dynamic.sources["arrival_oxygen_debt"] == "synthetic_probe"
    plain = arrival_layers(Anchors(**SHOCKED))
    assert plain.dynamic.volume_deficit_ml is None and plain.dynamic.oxygen_debt == 0.0
    assert set(plain.dynamic.sources.values()) == {"default_unmapped"}
    assert set(layers.to_dict()) == set(ARRIVAL_LAYERS)


@pytest.mark.parametrize("declared", [{}, {"arrival_oxygen_debt": 0.0}, {"arrival_delivery_ratio": 0.5},
                                      {"intrinsic_sinus_rate": 60.0, "arrival_oxygen_debt": 200.0},
                                      {"arrival_lactate_excess": 4.4}])
def test_the_arrival_observation_is_reconstructed_exactly_whatever_the_reference(declared):
    anchors = shocked(**declared)
    derived = check_arrival_reconstruction(anchors)
    assert (derived.pulse_rate_bpm, derived.sbp, derived.dbp, derived.lactate) == (124.0, 88.0, 54.0, 4.4)


def test_the_arrival_debt_is_the_arrival_value_of_d_and_never_negative():
    assert arrival_state(shocked()).D == 60.0
    assert arrival_state(Anchors(**SHOCKED)).D == 0.0
    with pytest.raises(CoreInvariantError):
        shocked(arrival_oxygen_debt=-1.0)
    with pytest.raises(CoreInvariantError):
        shocked(arrival_delivery_ratio=0.0)
    with pytest.raises(CoreInvariantError, match="names no source"):
        Anchors(**{**SHOCKED, "arrival_oxygen_debt": 10.0})


def test_an_ongoing_arrival_deficit_accrues_and_adequate_delivery_repays_without_going_negative():
    untreated = run(shocked(arrival_oxygen_debt=5.0), (), 600)
    debts = [state.D for state in untreated.states]
    assert all(later > earlier for earlier, later in zip(debts, debts[1:])), "deficit 0.2 continues"
    tau = DEFAULT_PROFILE.debt_clearance_tau_min
    assert debts[-1] == pytest.approx(tau * 0.2, rel=1e-3), "toward tau x deficit"
    # An arrival debt above what the arrival deficit sustains falls toward it, still never below 0.
    assert run(shocked(arrival_oxygen_debt=60.0), (), 600).states[-1].D == pytest.approx(tau * 0.2, rel=1e-3)
    # Haemoglobin up by a third: effective delivery 0.8 x 1.33 > 1, the deficit stops.
    treated = run(shocked(), (Drift("blood", "hb", 0, 1, SHOCKED["hb"] / 3),), 600)
    debts = [state.D for state in treated.states]
    assert all(later < earlier for earlier, later in zip(debts[1:], debts[2:])) and min(debts) >= 0.0
    lactates = [item.lactate for item in treated.derived()]
    assert lactates[-1] < SHOCKED["lactate"] and min(lactates) >= 1.0 - 1e-9, "clears to its baseline, no further"


def test_a_debt_the_patient_arrives_with_is_already_in_the_arrival_drive():
    """Arrival HR is exact; repaying the arrival debt lowers the rate toward intrinsic, never below."""
    anchors = shocked(arrival_delivery_ratio=1.0)
    rates = [item.pulse_rate_bpm for item in run(anchors, (), 240).derived()]
    assert rates[0] == 124.0
    assert rates[-1] < 124.0 and min(rates) >= 80.0
    assert all(later <= earlier + 1e-9 for earlier, later in zip(rates, rates[1:]))


def test_the_deficit_to_debt_gain_scales_accrual_and_defaults_to_one():
    assert DEFAULT_PROFILE.debt_per_delivery_deficit == 1.0 and DEFAULT_PROFILE.collapse_burden_per_minute == 1.0
    anchors = shocked(arrival_oxygen_debt=0.0)
    single = run(anchors, (), 1).states[1].D
    double = run(anchors, (), 1, replace(DEFAULT_PROFILE, debt_per_delivery_deficit=2.0)).states[1].D
    assert double == pytest.approx(2 * single) and single == pytest.approx(0.2)
    with pytest.raises(CoreInvariantError):
        replace(DEFAULT_PROFILE, debt_per_delivery_deficit=0.0)


def test_the_gi_golden_declares_none_of_the_new_arrival_layers():
    import json
    from clinical_core.shadow import GOLDEN
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for scenario in golden["scenarios"].values():
        for name in ("arrival_oxygen_debt", "arrival_delivery_ratio", "reference_preload_fraction"):
            assert scenario["case_parameters"][name]["source"] == "default_unmapped"
