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
    blocked = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 0.5,
                         "declared": {"beta_blockade": "synthetic_probe"}})
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


# P2D-4 -- D and lactate: comparative monotonicity -----------------------------------------------

@dataclass(frozen=True)
class Window(Contributor):
    """Volume lost at a constant rate within (start, stop], Hb untouched (test only)."""

    kind = SourceKind.DISEASE_MODULE
    type_name = "test_window_loss"
    id: str
    per_minute: float
    start: int
    stop: int

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start < minute <= self.stop:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.V, -self.per_minute, self.source, minute, "volume loss"),))


@dataclass(frozen=True)
class Refill(Contributor):
    """Sets V back to a level at one minute (an idealised resuscitation, test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_refill"
    id: str
    at_minute: int
    level_ml: float = 0.0

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.V, self.level_ml - state.V, self.source, minute,
                                                 "volume set back"),))


def _excess(trajectory):
    return [state.aux.lactate_excess_mmol_l for state in trajectory.states]


def test_p2d4_a_greater_debt_never_gives_less_lactate():
    less = run(BLEEDING, (Window("loss", 2.0, 0, 60), Refill("back", 61)), 240)
    more = run(BLEEDING, (Window("loss", 3.0, 0, 60), Refill("back", 61)), 240)
    assert all(m.D >= l.D for m, l in zip(more.states, less.states))
    assert all(m >= l for m, l in zip(_excess(more), _excess(less)))
    assert _excess(more)[60] > _excess(less)[60]


def test_p2d4_sustained_severe_debt_takes_lactate_above_arrival():
    trajectory = run(BLEEDING, (Window("loss", 15.0, 0, 30),), 240)        # V held at -450 mL-eq
    lactate = [d.lactate for d in trajectory.derived()]
    assert lactate[-1] > BLEEDING.lactate and lactate[-1] > lactate[60] > lactate[30]


def test_p2d4_restored_delivery_starts_clearance_but_does_not_erase_the_lactate_at_once():
    trajectory = run(BLEEDING, (Window("loss", 5.0, 0, 60), Refill("back", 61)), 400)
    excess = _excess(trajectory)
    assert excess[61] > 0 and excess[62] > 0, "not erased by restoring flow"
    peak = max(range(len(excess)), key=excess.__getitem__)
    assert peak >= 61 and excess[-1] < excess[peak], "clearance follows, with a lag"


def test_p2d4_a_transient_improvement_does_not_erase_prior_debt():
    """Same course from minute 61 on; only one of them was in shock before."""
    later = (Refill("brief_refill", 61), Window("again", 5.0, 66, 120))
    shocked = run(BLEEDING, (Window("first", 5.0, 0, 60),) + later, 200)
    fresh = run(BLEEDING, later, 200)
    for minute in range(66, 201):
        assert shocked.states[minute].D > fresh.states[minute].D
        assert _excess(shocked)[minute] > _excess(fresh)[minute]


# P2D-5 -- the pump shapes the preload response ---------------------------------------------------

PUMPS = (1.0, 0.7, 0.4)
GRID = [-300.0 + 100.0 * step for step in range(34)]     # -300 .. +3000 mL-eq


def _output(V, P):
    return _at(BLEEDING, V, P).output_rel


def _at(anchors, V, P=1.0):
    return derive(run(anchors, (), 0).states[0].evolve(V=float(V), P=float(P)), anchors)


def test_p2d5_a_weaker_pump_gives_less_output_at_the_same_volume():
    for V in GRID:
        outputs = [_output(V, P) for P in PUMPS]
        assert outputs[0] > outputs[1] > outputs[2], V


def test_p2d5_a_depressed_pump_never_gains_more_per_ml_than_a_normal_one():
    for P in PUMPS[1:]:
        for V, W in zip(GRID, GRID[1:]):
            assert _output(W, P) - _output(V, P) <= _output(W, 1.0) - _output(V, 1.0), (P, V)


def test_p2d5_a_modest_bolus_does_not_make_a_depressed_pump_whole():
    assert _output(500.0, 0.7) < 1.0, "moderate depression: 500 mL does not restore arrival output"
    assert max(_output(V, 0.4) for V in GRID) < 1.0, "severe depression: no volume within bounds does"


def test_p2d5_severe_depression_lowers_and_flattens_the_usable_curve():
    ceilings = [_output(3000.0, P) for P in PUMPS]
    gains = [_output(500.0, P) - _output(0.0, P) for P in PUMPS]
    relative = [gain / _output(0.0, P) for gain, P in zip(gains, PUMPS)]
    assert ceilings[0] > ceilings[1] > ceilings[2]
    assert gains[0] > gains[1] > gains[2] and relative[0] > relative[1] > relative[2]


def test_p2d5_p_keeps_meaning_the_output_at_arrival_filling():
    for P in (0.4, 0.7, 1.0, 1.3):
        assert _output(0.0, P) == pytest.approx(P)


# P2D-6 -- lung water clears slowly without a source ---------------------------------------------

LIMITED = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "pump_reserve": 0.3,
                     "declared": {"pump_reserve": "synthetic_probe"}})


def _lung_water(contributors, minutes, anchors=LIMITED):
    return [state.L for state in run(anchors, contributors, minutes).states]


def test_p2d6_no_source_no_rise():
    assert set(_lung_water((), 300)) == {0.0}


def test_p2d6_removing_the_source_lets_lung_water_recover_slowly_and_monotonically():
    L = _lung_water((Refill("fill", 1, 2000.0), Refill("drain", 60, 0.0)), 400)
    assert L[59] > 0
    after = L[60:]
    assert all(later < earlier for earlier, later in zip(after, after[1:])), "monotonic recovery"
    assert after[1] > 0 and min(after) > 0, "slow: not erased at once, never below arrival"
    from clinical_core.derived import LUNG_WATER_CLEARANCE
    trajectory = run(LIMITED, (Refill("fill", 1, 2000.0), Refill("drain", 60, 0.0)), 80)
    clearing = [d for record in trajectory.records[60:] for d in record.deltas if d.channel is Channel.L]
    assert clearing and all(d.source == LUNG_WATER_CLEARANCE and d.amount < 0 for d in clearing)


def test_p2d6_a_persisting_source_keeps_lung_water_up_and_more_overload_makes_it_worse():
    persisting = _lung_water((Refill("fill", 1, 2000.0),), 300)
    worse = _lung_water((Refill("fill", 1, 2000.0), Refill("more", 30, 2800.0)), 300)
    assert all(later >= earlier for earlier, later in zip(persisting[1:], persisting[2:]))
    assert all(w >= p for w, p in zip(worse, persisting)) and worse[-1] > persisting[-1]



# P2D-8 -- case-parameter provenance ------------------------------------------------------------

def test_p2d8_a_non_neutral_case_parameter_must_name_its_source():
    with pytest.raises(CoreInvariantError, match="names no source"):
        Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "pump_reserve": 0.5, "declared": {}})
    for declared in ({"pump_reserve": "inferred_from_text"}, {"heart_failure": "explicit_case"}):
        with pytest.raises(CoreInvariantError):
            Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "pump_reserve": 0.5, "declared": declared})


def test_p2d8_provenance_says_value_source_and_calibration():
    from clinical_core.derived import case_parameter_provenance
    plain = case_parameter_provenance(BLEEDING)
    assert {name: entry["source"] for name, entry in plain.items()} == {
        "beta_blockade": "default", "preload_fraction": "default", "pump_reserve": "default"}
    assert plain["preload_fraction"]["value"] == DEFAULT_PROFILE.arrival_preload_fraction
    assert not any(entry["calibrated"] for entry in plain.values())
    declared = Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "beta_blockade": 0.4,
                          "declared": {"beta_blockade": "explicit_case", "pump_reserve": "explicit_case"}})
    provenance = case_parameter_provenance(declared)
    assert provenance["beta_blockade"] == {"value": 0.4, "source": "explicit_case", "calibrated": False,
                                           "note": "declared by the case; not calibrated"}
    assert provenance["pump_reserve"]["source"] == "explicit_case", "a declared neutral value keeps its source"
    assert Anchors.from_dict(json.loads(json.dumps(declared.to_dict()))) == declared


def test_p2d8_the_gi_golden_uses_the_neutral_defaults_and_says_so():
    import json as json_module
    from clinical_core.shadow import GOLDEN
    golden = json_module.loads(GOLDEN.read_text(encoding="utf-8"))
    assert set(golden["case_parameter_rules"]) == {"gi_bleed"}
    for entry in golden["scenarios"].values():
        assert {item["source"] for item in entry["case_parameters"].values()} == {"default"}


def test_p2d8_a_family_without_a_rule_cannot_be_migrated():
    from clinical_core.legacy_adapter import UnsupportedScenario, anchors_from_legacy, bank_case
    case = bank_case("gi_bleed_57m")
    case["engine_family"] = "pulmonary_oedema"
    with pytest.raises(UnsupportedScenario, match="no case mapping or approved default rule"):
        anchors_from_legacy(case)


# P2D-7 -- sepsis / afterload: a diagnostic, not a fix ---------------------------------------------

def test_p2d7_lower_afterload_may_raise_output_but_does_not_normalize_pressure():
    from clinical_core import bands
    rows = bands.probe("vasodilation")
    arrival, late = rows[0], rows[-1]
    assert late["output_rel"] > arrival["output_rel"], "a rise in output from lower afterload is allowed"
    assert late["map"] < arrival["map"], "it does not normalize MAP"
    # Delivery follows flow; D, measured against arrival delivery (no demand state), falls.
    assert late["delivery_rel"] > arrival["delivery_rel"] and late["D"] < 0
    assert bands.DIAGNOSTICS["vasodilation"]["classification"] == \
        "PHYSIOLOGICALLY_PLAUSIBLE_PENDING_MULTI_FAMILY_CALIBRATION"


def test_p2d7_a_rise_in_output_is_not_automatic_in_sepsis_with_preload_loss():
    from clinical_core import bands
    rows = bands.probe("vasodilation_with_preload_loss")
    arrival, late = rows[0], rows[-1]
    assert late["output_rel"] < arrival["output_rel"] and late["delivery_rel"] < arrival["delivery_rel"]
    assert late["map"] < bands.probe("vasodilation")[-1]["map"] and late["D"] > 0 and late["crt_s"] > arrival["crt_s"]


# After the adversarial review of P2D -------------------------------------------------------------

def test_review_m1_a_depressed_pump_without_added_volume_does_not_congest():
    from clinical_core.bands import ARRIVAL, Drift
    neutral = Anchors(**ARRIVAL)
    for drop in (-0.7, -0.8):
        assert run(neutral, (Drift("pump", "P", 0, 1, drop),), 200).states[-1].L == 0.0
        bleeding = run(neutral, (Drift("pump", "P", 0, 1, drop), Window("loss", 5.0, 0, 40)), 120)
        assert bleeding.states[-1].L == 0.0
    weak = run(LIMITED, (Step("pump", "P", 1, -0.5), Refill("fill", 2, 3000.0)), 60)
    assert weak.states[-1].L > 0, "added volume on a failing pump still congests"


def test_review_m2_the_mental_status_attribution_survives_a_pulseless_minute_and_never_overreaches():
    from clinical_core.comparison import compare
    from clinical_core.modules import ScriptedRhythmEvent
    from clinical_core.shadow import EXPECTED_DIFFERENCES, classify, consciousness_attribution, run_shadow
    result = run_shadow("gi_bleed_57m", "untreated_60")
    arrest = ScriptedRhythmEvent("pea", 50, RhythmState.pea(40.0), "probe")
    core = run(result.core.anchors, tuple(result.core.contributors) + (arrest,), 60)
    probe = replace(result, core=core, rows=compare(result.legacy.snapshots, core.states, core.derived()))
    rows = consciousness_attribution(probe)
    pulseless = [row for row in rows if row["minute"] >= 50]
    assert pulseless and all(row["candidate_causes"] == [] for row in pulseless)
    summary = {name: dict(entry) for name, entry in result.summary.items()}
    summary["consciousness_level"]["mismatched"] = 1
    assert classify(result.key, summary, rows)["consciousness_level"]["classification"] == "UNRESOLVED"
    other = run_shadow("gi_bleed_72f", "untreated_60")
    assert "consciousness_level" not in EXPECTED_DIFFERENCES[other.key]
    fake = [{"minute": 1, "legacy": 0, "core": 1, "candidate_causes": ["KD-S3", "KD-S4"], "mode": "each_sufficient"}]
    summary = {name: dict(entry) for name, entry in other.summary.items()}
    summary["consciousness_level"]["mismatched"] = 1
    assert classify(other.key, summary, fake)["consciousness_level"]["classification"] == "UNRESOLVED", \
        "an attribution never approves a difference the run was not expected to have"


def test_review_m2_a_difference_the_pressure_does_not_explain_is_not_attributed_to_it():
    from clinical_core.shadow import consciousness_attribution, run_shadow
    result = run_shadow("gi_bleed_57m", "untreated_60")
    snapshots = [dict(snap) for snap in result.legacy.snapshots]
    snapshots[55]["spo2"] = 80          # the engines no longer read the same oxygen level
    probe = replace(result, legacy=replace(result.legacy, snapshots=tuple(snapshots)))
    row = next(r for r in consciousness_attribution(probe) if r["minute"] == 55)
    assert row["candidate_causes"] == [] and row["mode"] == "not explained by the pressure threshold"


@pytest.mark.parametrize("coupling", [0.0, 0.5, 1.0])
def test_review_l1_the_pump_guarantees_hold_for_every_allowed_coupling(coupling):
    from clinical_core.derived import CoreProfile
    profile = CoreProfile(pump_preload_coupling=coupling)
    base = run(BLEEDING, (), 0, profile=profile).states[0]
    empty = profile.preload_curve_scale_ml * __import__("math").log1p(-profile.arrival_preload_fraction)
    volumes = [empty + 1.0, empty + 20.0, -300.0, 0.0, 500.0, 3000.0]
    out = lambda V, P: derive(base.evolve(V=V, P=P), BLEEDING, profile).output_rel
    for V, W in zip(volumes, volumes[1:]):
        for P in (0.1, 0.4, 0.7):
            assert out(V, P) < out(V, 1.0) and out(W, P) - out(V, P) <= out(W, 1.0) - out(V, 1.0) + 1e-12
    with pytest.raises(CoreInvariantError):
        CoreProfile(pump_preload_coupling=2.0)


def test_review_l2_a_declared_case_parameter_has_a_value():
    with pytest.raises(CoreInvariantError, match="declared but has no value"):
        Anchors(**{**BLEEDING.to_dict(), "rhythm": BLEEDING.rhythm, "declared": {"preload_fraction": "explicit_case"}})


def test_review_l3_a_state_from_before_p2d1_is_not_resumed_silently():
    data = run(BLEEDING, (BLEED,), 3).states[-1].to_dict()
    with_old_memory = {**data, "internal": {**data["internal"], "core_coupling:sympathetic_drive": {"drive": 0.4}}}
    without_aux = {key: value for key, value in data.items() if key != "aux"}
    partial = {**data, "aux": {"lactate_excess_mmol_l": 0.1}}
    for bad in (with_old_memory, without_aux, partial):
        with pytest.raises(CoreInvariantError):
            CoreState.from_dict(bad)
    arrival = run(BLEEDING, (), 0).states[0].to_dict()
    arrival.pop("aux")
    assert CoreState.from_dict(arrival).aux == AuxiliaryState()


def test_review_the_level_2_probes_replay_from_their_specification():
    from clinical_core import bands
    from clinical_core.integration import scenario_from_dict, scenario_to_dict
    family, drives, declared, contributors, minutes = bands.PROBES["vasodilation"]
    anchors = Anchors(**{**bands.ARRIVAL})
    again = scenario_from_dict(json.loads(json.dumps(scenario_to_dict(anchors, contributors, max(minutes)))))
    assert run(*again[:3]).states[-1] == run(anchors, contributors, max(minutes)).states[-1]
