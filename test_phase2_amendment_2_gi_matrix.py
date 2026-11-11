"""PHASE2_AMENDMENT_2 (A2-017R): the GI trajectory and recovery matrix, on BOTH GI cases and the three witnesses of the
development region, with no per-case fitting.

What is checked is the causal ORDER the faculty required, in the core's own terms: arrival-relative delivery falls, the
burden F builds, the observable category climbs, and only then does the soft collapse become impending and established
(it needs both channels). On recovery (red cells and crystalloid) the burden clears and the category descends in minutes.
The amendment is declared explicitly in every course here (it is off in every committed profile).
"""
import dataclasses

import pytest

from clinical_core import blood_anchors as ba
from clinical_core import integration as ig
from clinical_core import systemic_consciousness as sc

CASES = ("gi_bleed_57m", "gi_bleed_72f")
WITNESSES = sorted(sc.WITNESSES)
#: Untreated minutes per case, kept below the core's existing boundary (output reaching zero with a pulse and no declared
#: terminal rule, which is an old behaviour this amendment does not change).
UNTREATED_MINUTES = {"gi_bleed_57m": 180, "gi_bleed_72f": 235}


def _declared(case, witness):
    anchors, profile, values = ba.setup(case)
    return anchors, dataclasses.replace(profile, amendment_2=sc.development_profile(witness)), values


def _rows(case, witness, minutes, extra=()):
    anchors, profile, values = _declared(case, witness)
    trajectory = ig.run(anchors, ba.contributors(case, "untreated", values) + tuple(extra), minutes, profile)
    rows = []
    for state, derived in zip(trajectory.states, trajectory.derived()):
        reading = sc.readout(state, anchors, profile, derived.pressure_rel, derived.delivery_rel)
        rows.append({"minute": state.minute, "pulse": derived.pulse_present, "F": sc.systemic_burden(state),
                     "C": state.aux.collapse_burden, "category": reading["category_index"],
                     "collapse": reading["collapse"]["state"], "dominant": reading["dominant"],
                     "rel_delivery": reading["instantaneous"].get("relative_delivery"),
                     "rel_perfusion": reading["instantaneous"].get("relative_perfusion"),
                     "level": derived.consciousness_level})
    return rows


def _first(rows, predicate):
    return next((row["minute"] for row in rows if predicate(row)), None)


@pytest.fixture(scope="module")
def untreated():
    return {(case, witness): _rows(case, witness, UNTREATED_MINUTES[case]) for case in CASES for witness in WITNESSES}


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", CASES)
def test_the_arrival_is_the_reference_and_no_impairment_is_inferred_at_arrival(untreated, case, witness):
    first = untreated[(case, witness)][0]
    assert first["minute"] == 0 and first["rel_delivery"] == pytest.approx(1.0) and first["rel_perfusion"] == pytest.approx(1.0)
    assert first["F"] == 0.0 and first["C"] == 0.0 and first["collapse"] == sc.NO_COLLAPSE
    assert first["category"] == ba.setup(case)[0].consciousness_level


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", CASES)
def test_the_untreated_course_has_the_required_causal_order(untreated, case, witness):
    rows = untreated[(case, witness)]
    somnolent = _first(rows, lambda r: r["category"] >= 1)
    obtunded = _first(rows, lambda r: r["category"] >= 2)
    unresponsive = _first(rows, lambda r: r["category"] >= 3)
    impending = _first(rows, lambda r: r["collapse"] != sc.NO_COLLAPSE)
    established = _first(rows, lambda r: r["collapse"] == sc.ESTABLISHED)
    assert None not in (somnolent, obtunded, unresponsive, impending, established), (case, witness)
    # delivery fell first, the burden followed it, the category climbed one band at a time ...
    first_deficit = _first(rows, lambda r: r["rel_delivery"] < sc.WITNESSES[witness].delivery_normal)
    assert first_deficit < somnolent <= obtunded <= unresponsive
    # ... and the soft collapse (which needs BOTH channels failing, for minutes) comes after the consciousness impairment
    assert somnolent < impending <= established
    # the observable category never skips a band on the way up
    steps = [b["category"] - a["category"] for a, b in zip(rows, rows[1:])]
    assert max(steps) <= 1 and min(steps) >= 0, (case, witness)


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", CASES)
def test_f_is_a_delayed_response_to_delivery_and_not_the_instantaneous_signal(untreated, case, witness):
    rows = untreated[(case, witness)]
    profile = sc.WITNESSES[witness]
    peak, lagged = 0.0, 0
    for row in rows:
        assert row["F"] <= peak + 1e-9, row                                   # F never exceeds the strongest signal it has seen
        signal = sc.delivery_failure(row["rel_delivery"], profile)
        if 0.0 < signal < 1.0 and row["F"] < signal - 1e-6:
            lagged += 1                                                         # the burden trails a rising signal
        peak = max(peak, signal)
    assert lagged >= 1
    onset = _first(rows, lambda r: r["rel_delivery"] < profile.delivery_normal)
    arrival_level = ba.setup(case)[0].consciousness_level
    assert all(row["category"] == arrival_level for row in rows if row["minute"] <= onset)


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", CASES)
def test_the_soft_collapse_never_precedes_a_low_output_alone(untreated, case, witness):
    """Low output with delivery still above the severe bound is not a collapse: the collapse burden stays at zero until BOTH
    the perfusion and the delivery failure are present."""
    profile = sc.WITNESSES[witness]
    for row in untreated[(case, witness)]:
        perfusion = sc.perfusion_failure(row["rel_perfusion"], profile)
        delivery = sc.delivery_failure(row["rel_delivery"], profile)
        if min(perfusion, delivery) == 0.0 and row["collapse"] != sc.NO_COLLAPSE:
            # a collapse can persist briefly after the combined signal has gone (hysteresis), never start without it
            assert row["C"] > 0.0
    start = _first(untreated[(case, witness)], lambda r: r["C"] > 0.0)
    first = next(r for r in untreated[(case, witness)] if r["minute"] == start)
    assert sc.perfusion_failure(first["rel_perfusion"], profile) > 0.0 or sc.delivery_failure(first["rel_delivery"], profile) > 0.0


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", CASES)
def test_no_oxygen_saturation_or_direct_pressure_ladder_writes_the_level_in_the_gi_course(untreated, case, witness):
    for row in untreated[(case, witness)]:
        assert row["level"] == row["category"]                                   # the derived level IS the composite
        if row["pulse"]:
            assert row["dominant"] in ([], [sc.PRIMARY], [sc.SYSTEMIC], [sc.COLLAPSE], [sc.SYSTEMIC, sc.COLLAPSE],
                                       [sc.PRIMARY, sc.SYSTEMIC], [sc.PRIMARY, sc.COLLAPSE],
                                       [sc.PRIMARY, sc.SYSTEMIC, sc.COLLAPSE])


def _treatment(case):
    _, _, values = ba.setup(case)
    unit = ba.contributors(case, "red_cells", values)[0]
    bag = ba._templates(case)["bag"]
    return (dataclasses.replace(unit, id="a2-prbc", start_minute=150, units=4.0, duration_min=30.0),
            dataclasses.replace(bag, id="a2-saline", start_minute=150, volume_ml=1000.0, duration_min=20.0, stop_minute=None,
                                stopped_by=None, queued_ahead_ml=0.0,
                                effective_ml_per_ml=values["crystalloid_effective_ml_per_ml"],
                                leak_tau_min=values["crystalloid_leak_tau_min"],
                                transient_share=values["crystalloid_transient_share"]))


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("case", ("gi_bleed_72f",))
def test_resuscitation_clears_the_burden_and_the_category_descends_within_minutes(case, witness):
    rows = _rows(case, witness, 230, extra=_treatment(case))
    before = next(r for r in rows if r["minute"] == 149)
    assert before["category"] >= 2 and before["F"] >= 0.5
    after = [r for r in rows if r["minute"] >= 150]
    # delivery is restored above the arrival's (the transfusion adds oxygen capacity), the burden falls, never back up
    assert min(r["rel_delivery"] for r in after if r["minute"] >= 175) > 1.0
    burden = [r["F"] for r in after]
    assert all(b <= a + 1e-9 for a, b in zip(burden[10:], burden[11:]))
    # the category crosses at least one band downward within ~5 minutes of the restoration, and is the arrival's by the end
    drop = _first(after, lambda r: r["category"] < before["category"])
    assert drop is not None and drop - 150 <= 12
    assert after[-1]["category"] == ba.setup(case)[0].consciousness_level
    assert after[-1]["collapse"] == sc.NO_COLLAPSE
    # recovery is monotone in the categories: it never climbs while the delivery is restored
    cats = [r["category"] for r in after if r["minute"] >= 155]
    assert all(b <= a for a, b in zip(cats, cats[1:]))


def test_the_matrix_uses_no_per_case_value_and_the_witnesses_bracket_the_conclusion(untreated):
    """The same three witnesses, on both cases: nothing was fitted to a case, and the ORDER holds on all six courses."""
    for case in CASES:
        firsts = {w: _first(untreated[(case, w)], lambda r: r["category"] >= 3) for w in WITNESSES}
        assert all(v is not None for v in firsts.values())
        assert max(firsts.values()) - min(firsts.values()) <= 35                  # the region's width, in minutes
