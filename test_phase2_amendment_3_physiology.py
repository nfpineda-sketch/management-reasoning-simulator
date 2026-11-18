"""PHASE2_AMENDMENT_3: the common vasoconstrictor support and its first writer (the physiology, on the common core alone).

What the faculty decided (FD-TONE-01 to FD-TONE-06) is asserted here as behaviour, never as a number to match:

  * tone is a GENERAL state (the channel T, which only the core writes); the support is a general input to the tone the state
    calls for, and norepinephrine is only its first writer;
  * the support raises pressure in proportion to the flow there is, and creates no flow: no volume, no pump, nothing without
    a pulse;
  * the response is bounded by its own form, has a timing (never a step in the minute of the order) and depends on the
    patient's volume and pump;
  * more tone is not more delivery;
  * nothing here is a clinical dose-response: the magnitudes are a development region with three witnesses, none chosen.
"""
import ast
import dataclasses
import inspect
import math

import pytest

from clinical_core import blood_anchors as ba
from clinical_core import derived as dv
from clinical_core import integration as ig
from clinical_core import provenance as pv
from clinical_core import vascular_support as vs
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, Channel, CoreInvariantError, RhythmState, UnresolvedBoundary

CASE = "gi_bleed_72f"
W = vs.witness("CENTER_REFERENCE")
START = 10


def _setup(case=CASE):
    anchors, profile, values = ba.setup(case)
    return anchors, profile, ba.contributors(case, "untreated", values)


def _declared(profile, gain=None):
    return dataclasses.replace(profile, vasoconstrictor_support_to_tone_gain=W["tone_gain"] if gain is None else gain)


def _infusion(name="CENTER_REFERENCE", **changes):
    point = vs.witness(name)
    spec = {"id": "order-norepinephrine", "start_minute": START, "rate_mcg_min": 10.0,
            "half_effect_rate_mcg_min": point["half_effect_rate_mcg_min"], "onset_tau_min": point["onset_tau_min"],
            "offset_tau_min": point["offset_tau_min"]}
    spec.update(changes)
    return vs.Norepinephrine(**spec)


@pytest.fixture(scope="module")
def runs():
    anchors, profile, items = _setup()
    declared = _declared(profile)
    return {"anchors": anchors, "profile": profile, "declared": declared, "items": items,
            "base": ig.run(anchors, items, 60, profile),
            "silent": ig.run(anchors, items, 60, declared),
            "infused": ig.run(anchors, items + (_infusion(),), 60, declared)}


# -- off by default: nothing committed changes ------------------------------------------------------------------------------

def test_the_reader_is_unset_by_default_and_leaves_no_trace_in_anything_serialised(runs):
    assert dv.DEFAULT_PROFILE.vasoconstrictor_support_to_tone_gain is None
    assert runs["profile"].vasoconstrictor_support_to_tone_gain is None
    assert "vasoconstrictor_support_to_tone_gain" not in runs["profile"].to_dict()
    assert "vasoconstrictor_support" not in AUXILIARY_FIELDS
    for state, record in zip(runs["base"].states[1:], runs["base"].records):
        assert state.aux.vasoconstrictor_support is None and "vasoconstrictor_support" not in state.aux.to_dict()
        assert record.vasoconstriction == () and "vasoconstriction" not in record.to_dict()
    scenario = ig.scenario_to_dict(runs["anchors"], runs["items"], 60, runs["profile"])
    assert "vasoconstrictor_support_to_tone_gain" not in scenario["profile"]
    anchors, items, minutes, profile = ig.scenario_from_dict(scenario)
    assert profile == runs["profile"] and ig.run(anchors, items, minutes, profile).digest() == runs["base"].digest()


def test_the_parameter_is_registered_as_provisional_development_behaviour_and_never_as_approved():
    status, text = dv.PARAMETERS["vasoconstrictor_support_to_tone_gain"]
    assert status == dv.PROVISIONAL and "UNSET" in text and "not approved" in text and "never a clinical dose-response" in text
    assert set(dv.PARAMETERS) >= {field.name for field in dataclasses.fields(dv.CoreProfile)}


@pytest.mark.parametrize("bad", [0.0, -0.5, float("nan"), float("inf"), True, "0.6"])
def test_a_declared_reader_is_a_finite_positive_gain_and_nothing_else(bad):
    with pytest.raises((CoreInvariantError, TypeError)):
        dataclasses.replace(dv.DEFAULT_PROFILE, vasoconstrictor_support_to_tone_gain=bad)


def test_a_declared_reader_with_no_writer_changes_no_physiology(runs):
    """Declaring the reader alone tracks a support of 0 and leaves every channel, every other memory and every derived
    quantity exactly where the undeclared run has them."""
    for minute, (plain, silent) in enumerate(zip(runs["base"].states, runs["silent"].states)):
        assert all(plain.value(channel) == silent.value(channel) for channel in Channel if channel is not Channel.R), minute
        assert plain.R == silent.R and plain.blood == silent.blood
        assert {name: getattr(plain.aux, name) for name in AUXILIARY_FIELDS} == {name: getattr(silent.aux, name) for name in AUXILIARY_FIELDS}
        assert silent.aux.vasoconstrictor_support == (None if minute == 0 else 0.0)
    assert [item.to_dict() for item in runs["base"].derived()] == [item.to_dict() for item in runs["silent"].derived()]


# -- the factor ---------------------------------------------------------------------------------------------------------------

def test_the_factor_is_one_with_no_support_increasing_and_bounded_by_its_own_form():
    gain = 0.6
    assert vs.tone_factor(None, gain) == 1.0 == vs.tone_factor(0.0, gain)
    assert vs.tone_factor(1.0, gain) == pytest.approx(1.0 + gain / 2)           # a support of 1 is half of the largest effect
    values = [vs.tone_factor(u, gain) for u in (0.0, 0.1, 0.5, 1.0, 2.0, 10.0, 1e3, 1e9, 1e300)]
    assert values == sorted(values) and all(1.0 <= value < 1.0 + gain for value in values[:-1]) and values[-1] <= 1.0 + gain
    assert vs.saturation(1e300) <= 1.0 and vs.saturation(0.0) == 0.0
    for bad in (-1e-9, float("nan"), float("inf")):
        with pytest.raises(CoreInvariantError):
            vs.saturation(bad)
    for bad in (0.0, -1.0, float("nan"), True):
        with pytest.raises(CoreInvariantError):
            vs.tone_factor(1.0, bad)


def test_arrival_stays_the_scale_whatever_is_declared(runs):
    """K(0) is 1, so the arrival tone target is 1 exactly and the authored arrival pressure is still what the model shows."""
    arrival = dv.arrival_state(runs["anchors"], runs["declared"])
    assert dv.tone_target(arrival, runs["anchors"], runs["declared"]) == 1.0
    assert dv.derive(arrival, runs["anchors"], runs["declared"]).to_dict() == dv.derive(
        dv.arrival_state(runs["anchors"], runs["profile"]), runs["anchors"], runs["profile"]).to_dict()


# -- the writer: order, timing, provenance ----------------------------------------------------------------------------------------

def test_the_order_first_acts_in_the_minute_after_it_and_tone_follows_one_minute_behind(runs):
    states, base = runs["infused"].states, runs["base"].states
    assert all(states[m].aux.vasoconstrictor_support == 0.0 for m in range(1, START + 1))
    assert states[START + 1].aux.vasoconstrictor_support > 0.0
    assert all(states[m].T == 1.0 for m in range(START + 2))                    # nothing in the minute of the order, nor the next
    assert states[START + 2].T > 1.0                                             # the core answers the state it saw a minute before
    derived, plain = runs["infused"].derived(), runs["base"].derived()
    assert all(derived[m].sbp == plain[m].sbp for m in range(START + 2))        # no pressure step at the order
    assert derived[START + 2].sbp > plain[START + 2].sbp
    assert base[START + 2].T == 1.0


def test_the_support_approaches_its_steady_value_monotonically_and_the_tone_approaches_its_factor(runs):
    infusion, states = _infusion(), runs["infused"].states
    steady = infusion.steady_support()
    assert steady == pytest.approx(10.0 / W["half_effect_rate_mcg_min"])
    support = [states[m].aux.vasoconstrictor_support for m in range(START, 61)]
    assert support == sorted(support) and support[-1] == pytest.approx(steady, abs=1e-9) and all(value <= steady + 1e-12 for value in support)
    assert all(states[m].aux.vasoconstrictor_support == pytest.approx(infusion.support_at(m), abs=1e-12) for m in range(1, 61))
    assert states[60].T == pytest.approx(vs.tone_factor(steady, W["tone_gain"]), abs=1e-9)
    assert all(states[m + 1].T == pytest.approx(vs.tone_factor(states[m].aux.vasoconstrictor_support, W["tone_gain"]), abs=1e-12) for m in range(1, 60))
    after_one_tau = infusion.support_at(START + W["onset_tau_min"]) / steady
    assert after_one_tau == pytest.approx(1 - math.exp(-1))                     # a first-order onset, minutes not seconds


def test_every_change_of_the_support_is_a_named_change_of_its_writer_and_tone_keeps_one_owner(runs):
    key = _infusion().source.key
    for record in runs["infused"].records:
        assert all(delta.source.key != key for delta in record.deltas)          # the drug writes no channel at all
        tone = [delta for delta in record.deltas if delta.channel is Channel.T]
        assert [delta.source for delta in tone] == [ig.VASCULAR_TONE]            # T's only writer is the core's response
        for change in record.vasoconstriction:
            assert type(change) is pv.VasoconstrictionChange and change.source.key == key and change.minute == record.minute
    changes = [change for record in runs["infused"].records for change in record.vasoconstriction]
    assert changes and math.fsum(change.amount for change in changes) == pytest.approx(runs["infused"].states[60].aux.vasoconstrictor_support, abs=1e-12)
    assert runs["infused"].records[START - 1].vasoconstriction == () and "vasoconstriction" in runs["infused"].records[START].to_dict()


def test_a_clinical_source_that_writes_the_channel_itself_is_still_refused_with_the_reader_declared(runs):
    @dataclasses.dataclass(frozen=True)
    class Rogue(ig.Contributor):
        kind = pv.SourceKind.INTERVENTION
        type_name = "rogue_direct_tone_writer_test_only"
        id: str = "rogue"

        def contribute(self, state, minute, signals, anchors, profile):
            return ig.Contribution(deltas=(pv.ChannelDelta(Channel.T, 0.2, self.source, minute, "a drug writing tone directly"),))

    # With the reader declared the core's tone response runs every minute, and it refuses ANY other writer of T in that minute (a test's own contributor included, which the
    # ownership rule alone would have let through as non-clinical): how a second writer would compose with the response is not decided, and this stage decides nothing about it.
    with pytest.raises(CoreInvariantError, match="write T while the vascular-tone response is on"):
        ig.run(runs["anchors"], runs["items"] + (Rogue(),), 3, runs["declared"])


def test_a_writer_with_the_reader_unset_is_refused_never_silently_inert(runs):
    with pytest.raises(pv.ProvenanceError, match="reader is UNSET"):
        ig.run(runs["anchors"], runs["items"] + (_infusion(),), START + 2, runs["profile"])


def test_the_writer_reads_only_its_order_and_time(runs):
    """The writer contract, checked on the source: the infusion's closed form touches no state, anchors, profile or signal
    (so it cannot read a pressure, close a loop or titrate), and it builds nothing but a vasoconstriction change."""
    tree = ast.parse(inspect.getsource(vs.Norepinephrine))
    forbidden = {"state", "anchors", "profile", "signals"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert node.value.id not in forbidden, ast.dump(node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # (the vasodilation record's name is assembled, not spelled: P2X-1A's frozen writer-contract scan counts every root file that spells it)
            assert node.func.id not in {"derive", "ChannelDelta", "BloodFlow", "Vasodilation" + "Change"}, node.func.id
    source = inspect.getsource(vs)
    for name in ("pressure_rel", "mean_arterial_pressure", "derive(", "ChannelDelta", "BloodFlow", "Channel.V", "Channel.P", "Channel.T"):
        assert name not in source.split('"""', 2)[2], name                       # outside the module docstring, the words are not code


# -- no volume, no pump, no pulse created -----------------------------------------------------------------------------------------------

def test_the_support_adds_no_volume_no_red_cells_and_no_pump(runs):
    for minute, (plain, infused) in enumerate(zip(runs["base"].states, runs["infused"].states)):
        assert (plain.V, plain.hb, plain.P, plain.L, plain.G, plain.W, plain.N) == (infused.V, infused.hb, infused.P, infused.L, infused.G, infused.W, infused.N), minute
        assert plain.blood == infused.blood and plain.R.code == infused.R.code


def test_without_a_pulse_no_tone_makes_a_circulation(runs):
    """Hard no-pulse semantics are unchanged: whatever the tone or the support, a pulseless state has no pressure, output or
    delivery, and the tone target is never asked to rescue it."""
    state = runs["infused"].states[30]
    assert state.T > 1.0 and state.aux.vasoconstrictor_support > 0.0
    for rhythm in (RhythmState.asystole(), RhythmState.pea(90.0)):
        for tone in (state.T, 2.5):
            arrested = dataclasses.replace(state, R=rhythm, T=tone, terminal_since=state.minute)
            derived = dv.derive(arrested, runs["anchors"], runs["declared"])
            assert derived.pulse_present is False and derived.sbp is None and derived.dbp is None and derived.map is None
            assert derived.output_rel == 0.0 and derived.pressure_rel == 0.0 and derived.delivery_rel == 0.0
            assert dv.delivery_rel_of(arrested, runs["anchors"], runs["declared"]) == 0.0


def test_no_flow_is_no_pressure_at_any_tone(runs):
    empty = dataclasses.replace(runs["infused"].states[30], V=-dv.arrival_filling(runs["anchors"], runs["declared"]) - 50.0)
    for tone in (1.0, 1.3, 2.5):
        output, pressure, _, delivery = dv._perfusion(dataclasses.replace(empty, T=tone), runs["anchors"], runs["declared"])
        assert output == 0.0 and pressure == 0.0 and delivery == 0.0


# -- bounded, and bounded by form ---------------------------------------------------------------------------------------------------

def test_the_response_saturates_far_below_any_guard_and_is_never_clipped(runs):
    # the largest rate the writer represents: just below SUPPORT_LIMIT half-effect rates (a rate at or past it is refused at construction)
    largest = (vs.SUPPORT_LIMIT - 1.0) * W["half_effect_rate_mcg_min"]
    huge = ig.run(runs["anchors"], runs["items"] + (_infusion(rate_mcg_min=largest),), 40, runs["declared"])
    ceiling = 1.0 + W["tone_gain"]
    assert all(state.T < ceiling for state in huge.states) and huge.states[40].T == pytest.approx(ceiling, rel=2e-3)
    assert not any(delta.source.kind is pv.SourceKind.CLAMP for record in huge.records for delta in record.deltas if delta.channel is Channel.T)
    usual = [item.pressure_rel for item in runs["infused"].derived()]
    assert all(a <= b + 1e-12 for a, b in zip(usual, [item.pressure_rel for item in huge.derived()]))
    doubled = ig.run(runs["anchors"], runs["items"] + (_infusion(rate_mcg_min=20.0),), 40, runs["declared"])
    gain_10 = runs["infused"].states[40].T - 1.0
    assert gain_10 < doubled.states[40].T - 1.0 < 2 * gain_10                    # twice the dose is less than twice the effect


def test_a_gain_whose_largest_target_would_reach_the_guard_is_refused_before_execution(runs):
    lower, upper = ig.CHANNEL_BOUNDS[Channel.T][0], ig.CHANNEL_BOUNDS[Channel.T][1]
    assert ig.tone_domain(runs["anchors"], _declared(runs["profile"], upper - 1.0 - 1e-6))["largest_target"] < upper
    for gain in (upper - 1.0, upper, 10.0):
        with pytest.raises(CoreInvariantError, match="guard"):
            ig.run(runs["anchors"], runs["items"], 1, _declared(runs["profile"], gain))
    unset = ig.tone_domain(runs["anchors"], runs["profile"])
    declared = ig.tone_domain(runs["anchors"], runs["declared"])
    assert declared["largest_target"] == pytest.approx(unset["largest_target"] * (1.0 + W["tone_gain"]))
    assert set(unset) == set(declared) and lower < 1.0


def test_the_compensation_and_the_support_compose_as_independent_factors_and_the_loop_stays_a_contraction(runs):
    compensating = dataclasses.replace(runs["declared"], deficit_to_tone_gain=0.5)
    domain = ig.tone_domain(runs["anchors"], compensating)
    assert domain["loop_slope_bound"] < 1.0 and domain["largest_target"] < ig.CHANNEL_BOUNDS[Channel.T][1]
    run = ig.run(runs["anchors"], runs["items"] + (_infusion(),), 60, compensating)
    for before, after in zip(run.states[1:-1], run.states[2:]):
        without = dataclasses.replace(compensating, vasoconstrictor_support_to_tone_gain=None)
        expected = dv.tone_target(dataclasses.replace(before, aux=dataclasses.replace(before.aux, vasoconstrictor_support=None)), runs["anchors"], without) \
            * vs.tone_factor(before.aux.vasoconstrictor_support, W["tone_gain"])
        assert after.T == pytest.approx(expected, rel=1e-12)
    with pytest.raises(CoreInvariantError):                                     # a product that is not a contraction is refused, never run
        ig.run(runs["anchors"], runs["items"], 1, dataclasses.replace(runs["profile"], deficit_to_tone_gain=1.9, afterload_sensitivity=0.5,
                                                                    vasoconstrictor_support_to_tone_gain=0.5))


# -- it depends on the flow there is ------------------------------------------------------------------------------------------------

def _response(state, anchors, profile, tone):
    plain = dv.derive(dataclasses.replace(state, T=1.0), anchors, profile)
    raised = dv.derive(dataclasses.replace(state, T=tone), anchors, profile)
    return plain, raised


def test_the_same_tone_buys_fewer_mmhg_with_less_volume_and_with_less_pump(runs):
    anchors, profile = runs["anchors"], runs["declared"]
    arrival = dv.arrival_state(anchors, profile)
    tone = vs.tone_factor(1.0, W["tone_gain"])
    filling = dv.arrival_filling(anchors, profile)                               # the effective preload arrival has to lose before the curve is empty
    gains = {}
    for label, state in (("replete", arrival), ("depleted", dataclasses.replace(arrival, V=-0.4 * filling)), ("very_depleted", dataclasses.replace(arrival, V=-0.8 * filling)),
                         ("failing_pump", dataclasses.replace(arrival, P=0.5)), ("depleted_failing_pump", dataclasses.replace(arrival, V=-0.4 * filling, P=0.5))):
        plain, raised = _response(state, anchors, profile, tone)
        gains[label] = (raised.map - plain.map, raised.map / plain.map, plain.map)
    assert gains["replete"][0] > gains["depleted"][0] > gains["very_depleted"][0] > 0.0
    assert gains["replete"][0] > gains["failing_pump"][0] > gains["depleted_failing_pump"][0] > 0.0
    ratios = [value[1] for value in gains.values()]
    assert max(ratios) - min(ratios) < 1e-12                                     # the factor is the tone's; the flow sets what it multiplies
    assert gains["very_depleted"][2] < gains["depleted"][2] < gains["replete"][2]


def test_more_tone_is_more_pressure_and_never_more_flow_or_delivery(runs):
    anchors, profile = runs["anchors"], runs["declared"]
    state = runs["base"].states[30]
    rows = [dv.derive(dataclasses.replace(state, T=tone), anchors, profile) for tone in (1.0, 1.1, 1.3, 1.6, 2.0, 2.5)]
    assert [row.pressure_rel for row in rows] == sorted(row.pressure_rel for row in rows)
    assert [row.output_rel for row in rows] == sorted((row.output_rel for row in rows), reverse=True)
    assert [row.delivery_rel for row in rows] == sorted((row.delivery_rel for row in rows), reverse=True)
    assert len({row.pressure_rel for row in rows}) == len(rows) == len({row.output_rel for row in rows})


def test_the_debt_accrues_faster_under_the_infusion_than_without_it(runs):
    """Pressure support is not perfusion: with the bleed untreated the infusion holds a higher pressure while the delivery is
    lower and the oxygen debt larger at every later minute. A benefit is not assumed, and none is manufactured."""
    plain, infused = runs["base"], runs["infused"]
    for minute in range(START + 3, 61):
        assert infused.derived()[minute].map > plain.derived()[minute].map
        assert infused.derived()[minute].delivery_rel < plain.derived()[minute].delivery_rel
        assert infused.states[minute].D > plain.states[minute].D
    late, early = infused.derived()[60].map, infused.derived()[START + 6].map
    assert late < early                                                          # the bleed still wins: the support does not hold what volume loses


# -- stopping, adding, replaying -------------------------------------------------------------------------------------------------------

def test_a_stopped_infusion_decays_with_its_own_time_constant_and_never_below_zero(runs):
    stopped = ig.run(runs["anchors"], runs["items"] + (_infusion(stop_minute=30),), 70, runs["declared"])
    support = [state.aux.vasoconstrictor_support for state in stopped.states[1:]]
    assert all(value >= 0.0 for value in support)
    assert support[29] == pytest.approx(_infusion().support_at(30)) and support[30] < support[29]
    assert support[30] / support[29] == pytest.approx(math.exp(-1.0 / W["offset_tau_min"]))
    assert stopped.states[70].T == pytest.approx(1.0, abs=1e-6) and stopped.derived()[70].sbp == pytest.approx(runs["base"].derived()[60].sbp, abs=10.0)
    with pytest.raises(CoreInvariantError):
        _infusion(stop_minute=START)


def test_two_writers_add_in_the_one_common_state_and_saturate_together(runs):
    first, second = _infusion(), _infusion(id="order-second-infusion", start_minute=20, rate_mcg_min=5.0)
    both = ig.run(runs["anchors"], runs["items"] + (first, second), 60, runs["declared"])
    total = first.support_at(60) + second.support_at(60)
    assert both.states[60].aux.vasoconstrictor_support == pytest.approx(total, abs=1e-12)
    assert both.states[60].T == pytest.approx(vs.tone_factor(total, W["tone_gain"]), abs=1e-9) and both.states[60].T < 1.0 + W["tone_gain"]
    sources = {change.source.key for record in both.records for change in record.vasoconstriction}
    assert sources == {first.source.key, second.source.key}


def test_the_run_replays_exactly_from_its_own_specification(runs):
    items = runs["items"] + (_infusion(stop_minute=40),)
    scenario = ig.scenario_to_dict(runs["anchors"], items, 60, runs["declared"])
    assert scenario["profile"]["vasoconstrictor_support_to_tone_gain"] == W["tone_gain"]
    assert [spec for spec in scenario["contributors"] if spec["type"] == "norepinephrine"][0]["rate_mcg_min"] == 10.0
    anchors, rebuilt, minutes, profile = ig.scenario_from_dict(scenario)
    first, again = ig.run(runs["anchors"], items, 60, runs["declared"]), ig.run(anchors, rebuilt, minutes, profile)
    assert first.digest() == again.digest() and first.to_dict() == again.to_dict()
    state = AuxiliaryState.from_dict(first.states[30].aux.to_dict())
    assert state == first.states[30].aux and state.vasoconstrictor_support > 0.0


def test_an_undeclared_magnitude_or_a_nonsense_order_is_refused():
    for missing in ("half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min"):
        with pytest.raises(CoreInvariantError, match="no value is approved"):
            _infusion(**{missing: None})
    for field, bad in (("rate_mcg_min", 0.0), ("rate_mcg_min", -1.0), ("rate_mcg_min", float("nan")), ("rate_mcg_min", True),
                       ("onset_tau_min", 0.0), ("start_minute", -1), ("start_minute", 1.5)):
        with pytest.raises(CoreInvariantError):
            _infusion(**{field: bad})
    with pytest.raises(pv.ProvenanceError):
        pv.VasoconstrictionChange(float("nan"), _infusion().source, 1, "x")
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(vasoconstrictor_support=-0.1)


def test_a_minute_that_would_take_the_support_below_zero_is_refused(runs):
    @dataclasses.dataclass(frozen=True)
    class Withdrawal(ig.Contributor):
        kind = pv.SourceKind.INTERVENTION
        type_name = "withdrawal_test_only"
        id: str = "withdrawal"

        def contribute(self, state, minute, signals, anchors, profile):
            return ig.Contribution(vasoconstriction=(pv.VasoconstrictionChange(-0.5, self.source, minute, "more than there is"),))

    with pytest.raises(pv.ProvenanceError, match="below 0"):
        ig.run(runs["anchors"], runs["items"] + (Withdrawal(),), 2, runs["declared"])


# -- the writers' grid, the conservation of the support and what is refused (independent review, P3-399) -----------------------------------

def test_the_state_is_exactly_the_sum_of_its_writers_every_minute_and_exactly_zero_after_they_decay(runs):
    """Review finding F1: with free binary64 contributions the per-minute differences did not sum back, a stopped infusion left a residue and, with the LOW offset, the residue went
    negative and the core refused the run at minute 48. On the writers' grid the differences and the sums are exact."""
    low = vs.witness("LOW")
    cases = {"LOW, one stopped": (_infusion("LOW", stop_minute=12),),
             "CENTER, one stopped": (_infusion(stop_minute=30),),
             "three, two stopped": (_infusion("HIGH", stop_minute=25), _infusion("LOW", id="second", start_minute=14, rate_mcg_min=7.3, stop_minute=31),
                                    _infusion(id="third", start_minute=22, rate_mcg_min=0.37))}
    for name, writers in cases.items():
        run = ig.run(runs["anchors"], runs["items"] + writers, 240, dataclasses.replace(runs["profile"], vasoconstrictor_support_to_tone_gain=low["tone_gain"]))
        for state in run.states[1:]:
            assert state.aux.vasoconstrictor_support == math.fsum(writer.support_at(state.minute) for writer in writers), (name, state.minute)
        stopped = [writer for writer in writers if writer.stop_minute is not None]
        if len(stopped) == len(writers):
            assert run.states[240].aux.vasoconstrictor_support == 0.0, name                      # exactly none, not a residue
            assert run.states[240].T == pytest.approx(ig.run(runs["anchors"], runs["items"], 240, runs["profile"]).states[240].T, abs=1e-9), name
    for writer in cases["three, two stopped"]:
        for minute in range(0, 241):
            value = writer.support_at(minute)
            assert value >= 0.0 and value == vs.on_the_grid(value) and (value / vs.SUPPORT_QUANTUM).is_integer(), (writer.id, minute)


def test_a_rate_past_what_the_writer_represents_is_refused_at_construction():
    half = W["half_effect_rate_mcg_min"]
    assert _infusion(rate_mcg_min=(vs.SUPPORT_LIMIT - 1.0) * half).steady_support() < vs.SUPPORT_LIMIT
    for rate in (vs.SUPPORT_LIMIT * half, 1e9, 1e300):
        with pytest.raises(CoreInvariantError, match="not an order this writer represents"):
            _infusion(rate_mcg_min=rate)
    assert vs.SUPPORT_QUANTUM == 2.0 ** -40 and vs.SUPPORT_LIMIT == 2.0 ** 10 and vs.on_the_grid(0.0) == 0.0 and vs.on_the_grid(vs.SUPPORT_QUANTUM * 0.49) == 0.0


def test_a_state_that_carries_a_support_is_refused_under_an_unset_reader_never_dropped_in_silence(runs):
    carried = runs["infused"].states[30]
    assert carried.aux.vasoconstrictor_support > 0.0
    with pytest.raises(pv.ProvenanceError, match="dropped in silence"):
        ig.run(runs["anchors"], runs["items"], 1, runs["profile"], initial=carried)
    # the declared reader takes the same state on, and an untracked state under the UNSET reader stays untracked
    assert ig.run(runs["anchors"], runs["items"] + (_infusion(),), 1, runs["declared"], initial=carried).states[-1].aux.vasoconstrictor_support > 0.0
    assert ig.run(runs["anchors"], runs["items"], 1, runs["profile"], initial=runs["base"].states[30]).states[-1].aux.vasoconstrictor_support is None


def test_the_support_moves_by_exactly_its_recorded_changes(runs):
    """The conservation invariant of the minute: a support that changed by other than the record's named changes is refused (an untracked state and a support of 0 are the same)."""
    before, after, record = runs["infused"].states[19], runs["infused"].states[20], runs["infused"].records[19]
    assert record.minute == 20 and record.vasoconstriction
    ig._check_conservation(before, after, record)
    for wrong in (after.aux.vasoconstrictor_support + vs.SUPPORT_QUANTUM, 0.0, None):
        tampered = dataclasses.replace(after, aux=dataclasses.replace(after.aux, vasoconstrictor_support=wrong))
        with pytest.raises(pv.ProvenanceError, match="vasoconstrictor support changed by other than its recorded changes"):
            ig._check_conservation(before, tampered, record)
    quiet_before, quiet_after, quiet = runs["base"].states[19], runs["base"].states[20], runs["base"].records[19]
    ig._check_conservation(quiet_before, quiet_after, quiet)
    with pytest.raises(pv.ProvenanceError, match="vasoconstrictor support changed by other than its recorded changes"):
        ig._check_conservation(quiet_before, dataclasses.replace(quiet_after, aux=dataclasses.replace(quiet_after.aux, vasoconstrictor_support=0.25)), quiet)


def test_changes_that_do_not_sum_to_a_finite_support_are_a_refusal_not_a_crash(runs):
    @dataclasses.dataclass(frozen=True)
    class Flood(ig.Contributor):
        kind = pv.SourceKind.INTERVENTION
        type_name = "flood_test_only"
        id: str = "flood"

        def contribute(self, state, minute, signals, anchors, profile):
            return ig.Contribution(vasoconstriction=(pv.VasoconstrictionChange(1.7e308, self.source, minute, "a"), pv.VasoconstrictionChange(1.7e308, self.source, minute, "b")))

    with pytest.raises(pv.ProvenanceError, match="do not sum to a finite support"):
        ig.run(runs["anchors"], runs["items"] + (Flood(),), 1, runs["declared"])


def test_a_refusal_names_the_factor_that_is_declared(runs):
    with pytest.raises(CoreInvariantError, match=r"times the vasoconstrictor ceiling 3\.0\)"):
        ig.run(runs["anchors"], runs["items"], 1, _declared(runs["profile"], 2.0))
    with pytest.raises(CoreInvariantError, match="derived bound with the vasoconstrictor ceiling") as caught:
        # a target inside the guard whose delayed loop is not a contraction: the bound is refused, and it is the vasoconstrictor ceiling that is named
        ig.run(runs["anchors"], runs["items"], 1, dataclasses.replace(runs["profile"], deficit_to_tone_gain=0.5, afterload_sensitivity=0.9, vasoconstrictor_support_to_tone_gain=0.3))
    assert "distributive" not in str(caught.value)
    # with the reader UNSET the guard's refusal reads as it always did
    with pytest.raises(CoreInvariantError) as plain:
        ig.run(runs["anchors"], runs["items"], 1, dataclasses.replace(runs["profile"], deficit_to_tone_gain=2.5))
    assert "vasoconstrictor" not in str(plain.value)


# -- the development region ------------------------------------------------------------------------------------------------------------

def test_the_region_is_broad_declared_and_no_point_of_it_is_chosen():
    assert vs.STATUS == "DEVELOPMENT_BEHAVIOURAL_REGION" and vs.WITNESS_NAMES == ("LOW", "CENTER_REFERENCE", "HIGH")
    assert set(vs.REGION) == {"tone_gain", "half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min"}
    for name, spec in vs.REGION.items():
        low, high = spec["bounds"]
        assert low < high and high / low >= 2.0, name                           # broad behavioural bounds, never a narrow region
        assert spec["confidence"] < 0.80, name                                   # FD-TONE-06: below 0.80, so no narrow region is adopted
        assert all(spec[key] for key in ("evidence", "assumption", "uncertainty", "falsifier", "what", "unit")), name
    for name in vs.WITNESS_NAMES:
        assert vs.region_problems(vs.witness(name)) == []
    assert vs.region_problems({**vs.witness(), "tone_gain": 5.0}) and vs.region_problems({"tone_gain": 0.5})
    with pytest.raises(CoreInvariantError):
        vs.witness("CALIBRATED")
    text = inspect.getsource(vs).upper()
    for claim in ("CLINICALLY_VALIDATED", "CLINICALLY_CALIBRATED", "APPROVED_FOR_PRODUCTION", "SELECTED_POINT"):
        assert claim not in text


def test_the_three_witnesses_order_the_response_and_bracket_it(runs):
    at = START + 20
    maps = {}
    for name in vs.WITNESS_NAMES:
        profile = _declared(runs["profile"], vs.witness(name)["tone_gain"])
        run = ig.run(runs["anchors"], runs["items"] + (_infusion(name),), at, profile)
        maps[name] = run.derived()[at].map
        assert max(state.T for state in run.states) < 1.0 + vs.witness(name)["tone_gain"]
    plain = runs["base"].derived()[at].map
    assert plain < maps["LOW"] < maps["CENTER_REFERENCE"] < maps["HIGH"]
    assert maps["HIGH"] / plain < 1.6                                            # bounded magnitude even at the strongest witness
