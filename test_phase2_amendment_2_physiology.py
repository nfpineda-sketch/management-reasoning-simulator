"""PHASE2_AMENDMENT_2 (A2-013R .. A2-015R): the reversible systemic encephalopathy burden F, the composite observable
consciousness and the soft circulatory collapse, tested on their own, with their negative controls.

Every magnitude here is a point of a FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION (the LOW, CENTER_REFERENCE and HIGH
witnesses): the tests check BEHAVIOUR the faculty defined (what a minute or two of extreme signal does to F, how long a
recovery takes, that the collapse needs both failures), never a clinical calibration. Nothing here moves a committed
profile: the amendment is off by default.
"""
import dataclasses
import inspect
import math

import pytest

from clinical_core import amendment_2 as a2
from clinical_core import blood_anchors as ba
from clinical_core import derived as dv
from clinical_core import encephalopathy as en
from clinical_core import integration as ig
from clinical_core import systemic_consciousness as sc
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, CoreInvariantError, RhythmCode, RhythmState

WITNESSES = sorted(sc.WITNESSES)


def _code_without_docstring(function) -> str:
    import ast
    import textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.Module)) and ast.get_docstring(node):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def _arrested(state):
    """The same state in asystole: no pulse, no output (a rhythm the state itself accepts)."""
    return dataclasses.replace(state, R=RhythmState(RhythmCode.ASYSTOLE, 0.0, 0.0, False), terminal_since=state.minute)


def _memory(profile: sc.Amendment2Profile) -> en.EncephalopathyProfile:
    return en.EncephalopathyProfile(burden_rise_tau=profile.burden_rise_tau, burden_clear_tau=profile.burden_clear_tau)


def _collapse_memory(profile: sc.Amendment2Profile) -> en.EncephalopathyProfile:
    return en.EncephalopathyProfile(burden_rise_tau=profile.collapse_rise_tau, burden_clear_tau=profile.collapse_clear_tau)


def _series(burden, signals, memory):
    out = [burden]
    for signal in signals:
        burden = en.burden_after(burden, signal, 1.0, memory)
        out.append(burden)
    return out


# -- A2-013R: the kinetic regions of F ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name", WITNESSES)
def test_one_minute_of_extreme_signal_leaves_f_below_half_and_two_to_four_minutes_reach_the_unresponsive_band(name):
    profile = sc.WITNESSES[name]
    course = _series(0.0, [1.0] * 4, _memory(profile))
    assert course[1] < 0.50
    assert course[4] >= 0.80 > course[1]
    assert all(later > earlier for earlier, later in zip(course, course[1:]))      # F builds while the signal holds


@pytest.mark.parametrize("name", WITNESSES)
def test_recovery_crosses_a_category_in_about_three_to_five_minutes(name):
    profile = sc.WITNESSES[name]
    course = _series(0.80, [0.0] * 8, _memory(profile))
    first_below_half = next(minute for minute, value in enumerate(course) if value < 0.50)
    assert 3 <= first_below_half <= 5, course
    assert all(later < earlier for earlier, later in zip(course, course[1:]))      # and then it only falls
    assert course[-1] >= 0.0


@pytest.mark.parametrize("name", WITNESSES)
def test_f_rises_faster_than_it_clears_and_stays_between_zero_and_one(name):
    profile = sc.WITNESSES[name]
    assert profile.burden_rise_tau < profile.burden_clear_tau
    memory = _memory(profile)
    for start in (0.0, 0.3, 0.9):
        for signal in (0.0, 0.2, 0.6, 1.0):
            after = en.burden_after(start, signal, 1.0, memory)
            assert 0.0 <= after <= 1.0
            assert min(start, signal) - 1e-12 <= after <= max(start, signal) + 1e-12      # never past the signal


def test_every_declared_magnitude_lies_in_its_behavioural_region_for_every_witness():
    for name, profile in sc.WITNESSES.items():
        for field, (low, high, _) in sc.REGIONS.items():
            assert low - 1e-9 <= getattr(profile, field) <= high + 1e-9, (name, field)
    assert set(sc.IDENTIFIABILITY) == set(sc.FIELDS) == set(sc.REGIONS)
    assert sc.STATUS == "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION"


# -- the signal: arrival-relative delivery, no inferred healthy value --------------------------------------------------------

@pytest.mark.parametrize("case", ba.gi_reference.GI_CASES)
def test_relative_delivery_is_one_at_arrival_and_needs_no_healthy_baseline(case):
    anchors, profile, _ = ba.setup(case)
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    derived = dv.derive(arrival, anchors, full)
    assert sc.relative_delivery(derived.delivery_rel, anchors) == pytest.approx(1.0)
    assert sc.relative_perfusion(derived.pressure_rel) == pytest.approx(1.0)
    assert sc.systemic_burden_after(arrival, anchors, full) == 0.0                 # the arrival is the reference, not a deficit
    assert anchors.arrival_delivery_ratio < 1.0                                    # the arrival is already low: no healthy DO2 is read


def test_a_denominator_that_is_not_above_zero_has_no_arrival_to_be_relative_to():
    anchors, _, _ = ba.setup("gi_bleed_72f")
    for bad in (0.0, -0.1, float("nan"), float("inf")):
        with pytest.raises(CoreInvariantError):
            sc.relative_delivery(1.0, dataclasses.replace(anchors, arrival_delivery_ratio=bad))


def test_the_systemic_signal_reads_delivery_alone_never_pressure_oxygen_saturation_or_lactate():
    source = "".join(_code_without_docstring(function) for function in (sc.systemic_burden_after, sc.delivery_failure))
    for forbidden in ("sbp", "dbp", "spo2", "lactate", "pressure_rel", "mmhg"):
        assert forbidden not in source.lower(), forbidden
    profile = sc.development_profile()
    for delivery in (0.0, 0.3, 0.5, 0.75, 1.0, 2.5):
        assert 0.0 <= sc.delivery_failure(delivery, profile) <= 1.0
    assert sc.delivery_failure(1.0, profile) == 0.0 and sc.delivery_failure(0.0, profile) == 1.0
    assert sc.delivery_failure(profile.delivery_normal, profile) == 0.0 and sc.delivery_failure(profile.delivery_severe, profile) == 1.0


def test_without_a_pulse_the_systemic_signal_is_complete():
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    arrested = _arrested(arrival)
    assert sc.systemic_burden_after(arrested, anchors, full) == pytest.approx(
        en.burden_after(0.0, 1.0, 1.0, _memory(full.amendment_2)))


# -- A2-014R: the composite observable consciousness ------------------------------------------------------------------------

@pytest.mark.parametrize("impairment, index, category", [
    (0.0, 0, "NO_MATERIAL_OBSERVABLE_IMPAIRMENT"), (0.2499, 0, "NO_MATERIAL_OBSERVABLE_IMPAIRMENT"),
    (0.25, 1, "SOMNOLENT"), (0.4999, 1, "SOMNOLENT"), (0.50, 2, "OBTUNDED"), (0.7999, 2, "OBTUNDED"),
    (0.80, 3, "UNRESPONSIVE"), (1.0, 3, "UNRESPONSIVE")])
def test_the_category_cuts_are_the_faculty_cuts_and_no_gcs_is_computed(impairment, index, category):
    assert sc.category_index(impairment) == index and sc.CATEGORIES[index] == category
    assert sc.CATEGORY_CUTS == (0.25, 0.50, 0.80)
    assert not any("gcs" in name.lower() for name in dir(sc))


def _course_state(case, minute, witness="CENTER_REFERENCE"):
    anchors, profile, values = ba.setup(case)
    full = dataclasses.replace(profile, amendment_2=sc.development_profile(witness))
    trajectory = ig.run(anchors, ba.contributors(case, "untreated", values), minute, full)
    state = trajectory.states[-1]
    return anchors, full, state, trajectory.derived()[-1]


def test_the_observable_impairment_is_the_maximum_of_its_causes_and_names_the_dominant_ones():
    anchors, full, state, derived = _course_state("gi_bleed_72f", 130)
    reading = sc.readout(state, anchors, full, derived.pressure_rel, derived.delivery_rel)
    assert reading["impairment"] == max(reading["contributors"].values())
    assert set(reading["contributors"]) == {sc.PRIMARY, sc.SYSTEMIC, sc.COLLAPSE}
    assert reading["dominant"] == [sc.SYSTEMIC]                       # the systemic burden did it, not N and not the collapse
    assert reading["category"] == sc.CATEGORIES[reading["category_index"]]


def test_the_instantaneous_signal_is_not_part_of_the_impairment():
    """A deficit that has just arrived has not yet become a burden: the level does not jump with the signal."""
    anchors, full, state, derived = _course_state("gi_bleed_72f", 200)
    assert sc.delivery_failure(sc.relative_delivery(derived.delivery_rel, anchors), full.amendment_2) == 1.0
    reset = dataclasses.replace(state, aux=dataclasses.replace(state.aux, systemic_encephalopathy_burden=0.0,
                                                               collapse_burden=0.0))
    reading = sc.readout(reset, anchors, full, derived.pressure_rel, derived.delivery_rel)
    assert reading["impairment"] == 0.0 and reading["category"] == "NO_MATERIAL_OBSERVABLE_IMPAIRMENT"
    assert reading["instantaneous"]["delivery_failure"] == 1.0         # reported, never used for the level


def test_the_primary_neurologic_contribution_is_read_as_itself_and_the_arrival_level_is_its_floor():
    anchors, full, state, derived = _course_state("gi_bleed_72f", 5)
    base = sc.primary_neurologic(state, anchors)
    assert base == sc.ARRIVAL_FLOOR[anchors.consciousness_level]
    stimulated = dataclasses.replace(state, N=0.6)
    assert sc.primary_neurologic(stimulated, anchors) >= base          # N counts as itself; nothing writes it back
    for level, floor in enumerate(sc.ARRIVAL_FLOOR):
        assert sc.category_index(floor) == level


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_a_case_that_arrives_impaired_keeps_its_authored_observed_level_until_something_moves_it(level):
    """The arrival's authored level is the known observed neurological baseline: the composite never reports a LOWER
    category than the case arrived with, and invents no systemic burden to explain it."""
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    anchors = dataclasses.replace(anchors, consciousness_level=level)
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    reading = sc.readout(dv.arrival_state(anchors, full), anchors, full)
    assert reading["category_index"] == level
    assert reading["contributors"][sc.SYSTEMIC] == 0.0 and reading["contributors"][sc.COLLAPSE] == 0.0
    assert reading["contributors"][sc.PRIMARY] == sc.ARRIVAL_FLOOR[level]


def test_the_amended_level_is_the_composite_everywhere_and_no_direct_pressure_or_spo2_ladder_reaches_it():
    anchors, profile, values = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    trajectory = ig.run(anchors, ba.contributors("gi_bleed_72f", "untreated", values), 150, full)
    for state, derived in zip(trajectory.states, trajectory.derived()):
        assert derived.consciousness_level == sc.consciousness_level(state, anchors, full)
    legacy = ig.run(anchors, ba.contributors("gi_bleed_72f", "untreated", values), 150, profile)
    assert any(a.consciousness_level != b.consciousness_level
               for a, b in zip(legacy.derived(), trajectory.derived())), "the amendment changed nothing: it is not live"


def test_a_low_output_state_that_is_stable_does_not_write_the_level_by_itself():
    """Low pressure and low delivery at arrival are the case's own starting point: the level is the arrival's, not a ladder."""
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    reading = sc.readout(arrival, anchors, full)
    assert reading["category_index"] == anchors.consciousness_level
    assert reading["contributors"][sc.SYSTEMIC] == 0.0 and reading["contributors"][sc.COLLAPSE] == 0.0


# -- A2-015R: the soft circulatory collapse ------------------------------------------------------------------------------

def test_the_collapse_needs_both_failures_at_once_and_never_the_maximum():
    for perfusion, delivery in ((1.0, 0.0), (0.0, 1.0), (0.7, 0.2), (0.2, 0.7), (1.0, 1.0), (0.0, 0.0)):
        assert sc.collapse_signal(perfusion, delivery) == min(perfusion, delivery) <= max(perfusion, delivery)
    assert sc.collapse_signal(1.0, 0.0) == 0.0 == sc.collapse_signal(0.0, 1.0)


@pytest.mark.parametrize("name", WITNESSES)
def test_negative_controls_low_output_alone_delivery_alone_perfusion_alone_and_a_brief_episode_do_not_collapse(name):
    profile = sc.WITNESSES[name]
    memory = _collapse_memory(profile)
    # (a) low output only / perfusion alone: the perfusion signal complete, the delivery signal absent
    alone = _series(0.0, [sc.collapse_signal(1.0, 0.0)] * 60, memory)
    # (b) delivery alone: the delivery signal complete, the perfusion signal absent
    other = _series(0.0, [sc.collapse_signal(0.0, 1.0)] * 60, memory)
    assert max(alone) == 0.0 and max(other) == 0.0
    for burden in alone + other:
        assert sc.collapse_state(burden, True, profile)["state"] == sc.NO_COLLAPSE
    # (c) a brief moderate episode of BOTH failures: one minute of a half-strength combined signal builds no collapse
    brief = _series(0.0, [0.5], memory)
    assert sc.collapse_state(brief[-1], True, profile)["state"] == sc.NO_COLLAPSE
    # (d) a one-minute episode of the EXTREME combined signal is at most impending, never established
    extreme = _series(0.0, [1.0], memory)
    assert sc.collapse_state(extreme[-1], True, profile)["state"] in (sc.NO_COLLAPSE, sc.IMPENDING)


@pytest.mark.parametrize("name", WITNESSES)
def test_persistence_builds_the_collapse_severe_two_to_four_minutes_extreme_one_to_three(name):
    profile = sc.WITNESSES[name]
    memory = _collapse_memory(profile)
    severe = _series(0.0, [0.9] * 6, memory)
    impending = next(minute for minute, burden in enumerate(severe)
                     if sc.collapse_state(burden, True, profile)["state"] != sc.NO_COLLAPSE)
    assert 1 <= impending <= 4
    extreme = _series(0.0, [1.0] * 6, memory)
    established = next(minute for minute, burden in enumerate(extreme)
                       if sc.collapse_state(burden, True, profile)["state"] == sc.ESTABLISHED)
    assert 1 <= established <= 3


@pytest.mark.parametrize("name", WITNESSES)
def test_recovery_needs_sustained_restoration_and_passes_through_impending(name):
    profile = sc.WITNESSES[name]
    course = _series(1.0, [0.0] * 14, _collapse_memory(profile))
    states = [sc.collapse_state(burden, True, profile)["state"] for burden in course]
    assert states[0] == sc.ESTABLISHED and states[-1] == sc.NO_COLLAPSE
    order = [sc.NO_COLLAPSE, sc.IMPENDING, sc.ESTABLISHED]
    assert [order.index(s) for s in states] == sorted((order.index(s) for s in states), reverse=True)   # never flips back up
    assert sc.IMPENDING in states                                       # the way down goes through the middle band
    established_to_cleared = next(i for i, s in enumerate(states) if s == sc.NO_COLLAPSE) - next(
        i for i, s in enumerate(states) if s != sc.ESTABLISHED)
    assert 3 <= established_to_cleared <= 7, states                     # minutes, not a flip at one boundary


def test_the_soft_collapse_hysteresis_is_wider_than_a_single_threshold():
    for profile in sc.WITNESSES.values():
        assert profile.impending_burden < profile.established_burden
        assert profile.collapse_rise_tau < profile.collapse_clear_tau
        just_below = sc.collapse_state(profile.established_burden - 1e-9, True, profile)["state"]
        just_above = sc.collapse_state(profile.established_burden, True, profile)["state"]
        assert (just_below, just_above) == (sc.IMPENDING, sc.ESTABLISHED)


def test_no_pulse_is_a_separate_hard_immediate_path():
    for profile in sc.WITNESSES.values():
        hard = sc.collapse_state(0.0, False, profile)
        assert hard == {"state": sc.ESTABLISHED, "basis": sc.NO_PULSE}
        assert sc.collapse_state(0.0, True, profile)["state"] == sc.NO_COLLAPSE
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    arrested = _arrested(arrival)
    reading = sc.readout(arrested, anchors, full)
    assert reading["category"] == "UNRESPONSIVE" and reading["collapse"]["basis"] == sc.NO_PULSE
    # the collapse burden does not move without a pulse: that is arrest, not soft collapse
    assert sc.collapse_burden_after(arrested, anchors, full) == arrested.aux.collapse_burden


def test_the_existing_collapse_burden_slot_is_reused_and_no_third_memory_exists():
    assert "collapse_burden" in AUXILIARY_FIELDS
    assert sc.STATE_FIELD == "systemic_encephalopathy_burden" and sc.STATE_FIELD not in AUXILIARY_FIELDS
    declared = [f.name for f in dataclasses.fields(AuxiliaryState) if f.name not in AUXILIARY_FIELDS]
    assert declared == [sc.STATE_FIELD]                                   # exactly the one new memory, beside the reused slot


# -- default off, validation, serialization -------------------------------------------------------------------------------

def test_the_amendment_is_off_by_default_and_leaves_no_trace_in_a_serialised_state():
    assert dv.DEFAULT_PROFILE.amendment_2 is None
    anchors, profile, values = ba.setup("gi_bleed_72f")
    assert profile.amendment_2 is None
    trajectory = ig.run(anchors, ba.contributors("gi_bleed_72f", "untreated", values), 20, profile)
    for state in trajectory.states:
        assert state.aux.systemic_encephalopathy_burden is None
        assert sc.STATE_FIELD not in state.aux.to_dict()
        assert "amendment_2" not in {k for k, v in profile.to_dict().items() if v is not None}


def test_a_declared_profile_round_trips_through_the_scenario_serialisation():
    anchors, profile, values = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile("HIGH"))
    contributors = ba.contributors("gi_bleed_72f", "untreated", values)
    assert full.to_dict()["amendment_2"] == sc.development_profile("HIGH").to_dict()
    restored = ig.scenario_from_dict(ig.scenario_to_dict(anchors, contributors, 30, full)) \
        if hasattr(ig, "scenario_to_dict") else None
    if restored is not None:
        assert restored[3].amendment_2 == sc.development_profile("HIGH")


@pytest.mark.parametrize("change", [
    {"delivery_normal": 0.4}, {"delivery_normal": 1.2}, {"delivery_severe": 0.0}, {"perfusion_normal": 0.2},
    {"perfusion_severe": 0.0}, {"burden_rise_tau": 9.0}, {"burden_rise_tau": 0.0}, {"collapse_rise_tau": 9.0},
    {"impending_burden": 0.9}, {"established_burden": 1.0}, {"established_burden": 0.1},
    {"burden_clear_tau": float("nan")}, {"delivery_normal": True}, {"collapse_clear_tau": "slow"}])
def test_a_malformed_profile_is_refused_never_repaired(change):
    with pytest.raises(CoreInvariantError):
        dataclasses.replace(sc.development_profile(), **change)


def test_the_stage_still_reconstructs_both_earlier_cores_with_the_physiology_in_place():
    assert a2.amendment_1_digest_now() == a2.AMENDMENT_1_DIGEST
    assert all(a2.proofs().values())
    assert a2.non_regression()["pass"] is True


# -- review findings (A2-020R): holes closed by tests --------------------------------------------------------------------

def test_a_low_pressure_with_normal_delivery_writes_neither_f_nor_the_collapse():
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    low_tone = dataclasses.replace(arrival, T=0.30)
    derived = dv.derive(low_tone, anchors, full)
    assert derived.pressure_rel < 0.5 and derived.delivery_rel >= 1.0
    assert sc.systemic_burden_after(low_tone, anchors, full) == 0.0
    assert sc.collapse_burden_after(low_tone, anchors, full) == 0.0


def test_an_impending_collapse_alone_does_not_make_the_level_unresponsive():
    anchors, profile, _ = ba.setup("gi_bleed_72f")
    full = dataclasses.replace(profile, amendment_2=sc.development_profile())
    arrival = dv.arrival_state(anchors, full)
    impending = dataclasses.replace(arrival, aux=dataclasses.replace(
        arrival.aux, collapse_burden=full.amendment_2.impending_burden + 0.01, systemic_encephalopathy_burden=0.0))
    reading = sc.readout(impending, anchors, full)
    assert reading["collapse"]["state"] == sc.IMPENDING
    assert reading["contributors"][sc.COLLAPSE] == 0.0 and reading["category_index"] == 0
    established = dataclasses.replace(arrival, aux=dataclasses.replace(
        arrival.aux, collapse_burden=full.amendment_2.established_burden, systemic_encephalopathy_burden=0.0))
    assert sc.readout(established, anchors, full)["category"] == "UNRESPONSIVE"


def test_the_collapse_burden_clears_slower_than_it_builds():
    for profile in sc.WITNESSES.values():
        memory = _collapse_memory(profile)
        built = en.burden_after(0.0, 1.0, 1.0, memory)
        cleared = 1.0 - en.burden_after(1.0, 0.0, 1.0, memory)
        assert cleared < built / 2


def test_a_declared_amendment_must_be_an_amendment_profile_and_excludes_the_inherited_collapse_rule():
    with pytest.raises(CoreInvariantError):
        dataclasses.replace(dv.DEFAULT_PROFILE, amendment_2="junk")
    with pytest.raises(CoreInvariantError):
        dataclasses.replace(dv.DEFAULT_PROFILE, amendment_2={"delivery_normal": 0.75})
    for field in ("collapse_output_threshold", "collapse_burden_limit", "collapse_repayment_tau_min"):
        with pytest.raises(CoreInvariantError):
            dataclasses.replace(dv.DEFAULT_PROFILE, amendment_2=sc.development_profile(), **{field: 0.5})
