"""P3-424 to P3-434: norepinephrine as ONE infusion whose rate can be started, increased, decreased and stopped, through the SAME common vasoconstrictor support.

What it proves (the documents, the decisions and the sealed records are tested apart, in test_phase3_tone_titration_records.py):

* THE WRITER. ``NorepinephrineRateHistory`` IS the core's writer (a subclass: the same constants, change, state and grid). For a start and for a start followed by a stop its arithmetic is the
  core's own closed form BIT FOR BIT; for any history it approaches the steady support of the rate ordered with the onset constant while it rises and the offset constant while it falls -- so it
  never moves in the minute of an order, never passes the ordered rate's steady support, moves toward it and never away from it (in ALL three witnesses), is never negative, sums exactly
  on the writers' grid, and an earlier minute never depends on a later order. It reads no state at all, refuses a history it cannot represent, and survives its own specification.
* THE ORDERS. One infusion and one ordered rate: each order replaces the one before it and the infusion carries ONE order a minute, with what it did; an order replaced within its minute is a
  declared gap; the same rate again changes nothing; the FIRST order the mapping cannot read closes the infusion (fail closed), a weight-based rate is never converted, a pressure target is
  refused; and the run never carries two writers of the kind.
* THE REVIEW (P3-435). What the independent adversarial review found and what repairs it: an order that names no drug closes the infusion while the norepinephrine runs; the order is read as
  written; a refused order in the minute of a valid one; gaps that never go stale; a writer that validates its own accounting; malformed input that is declared and never raised.
* THE TRAJECTORIES. Through the REAL encounter (real order text, the real parser and engine, the real mirror), the GI hemorrhage probes behave as predicted BEFORE they were run: timing, direction,
  ordering, smoothness, persistence and decay, untouched state, and the engine's own active rate equal to the rate the run carries.
* THE EDGE CASES, each with the outcome written before the matrix was executed; the other families (the same support in every one, the certified single start unchanged, no reading changed with no
  order); and the negative-control scenario, whose physiology is the one the faculty reviewed.
* NOTHING ELSE MOVED. The core is the certified one, no registered adapter declares the reader, the live authority still does not accept the order, and no tone constant changed.
"""
import ast
import itertools
import json
import math
import random
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_shadow as rs
import runtime_shadow_families as fam
import runtime_tone_support as ts
import test_tone_pathway_analysis as ta
import test_tone_titration_analysis as tt
from clinical_core import integration
from clinical_core import vascular_support as vs
from clinical_core.provenance import ProvenanceError
from clinical_core.state import CoreInvariantError

ROOT = Path(__file__).resolve().parent
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
CENTER = {"half_effect_rate_mcg_min": 10.0, "offset_tau_min": 2.5, "onset_tau_min": 1.5, "tone_gain": 0.6}
QUANTUM = vs.SUPPORT_QUANTUM


def _constants(name="CENTER_REFERENCE"):
    point = vs.witness(name)
    return {key: point[key] for key in ("half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min")}


def _outcomes(history):
    """The accounting a plain history makes: one order per change, read against the rate before it."""
    out, last = [], None
    for index, (minute, rate) in enumerate(history):
        label = ts.STARTED if last is None else ts.STOPPED if rate == 0.0 else ts.RESTARTED if last == 0.0 else ts.INCREASED if rate > last else ts.DECREASED
        out.append((f"o{index + 1}", minute, float(rate), label))
        last = rate
    return tuple(out)


def _writer(history, name="CENTER_REFERENCE"):
    (start, rate), changes = history[0], tuple((minute, float(value)) for minute, value in history[1:])
    return ts.NorepinephrineRateHistory("o1", start, float(rate), changes=changes, orders=_outcomes(history), **_constants(name))


def _event(minute, order_id, operation="start", rate=10.0, units="mcg/min"):
    return rs.MirroredAction(order_id, minute, "norepinephrine", {"type": "norepinephrine", "operation": operation, "rate": rate, "units": units}, {}, 0.21)


def _stop(minute, order_id):
    return _event(minute, order_id, "stop", None, None)


def _role(minute, order_id, operation="stop", rate=None, units=None):
    """An order that names no drug, as the mirror hands it over: the parsed action and an empty receipt."""
    return rs.MirroredAction(order_id, minute, "infusion_adjustment", {"type": "infusion_adjustment", "operation": operation, "rate_value": rate, "rate_units": units}, {}, 0.21)


HISTORIES = (((2, 5.0), (10, 10.0)), ((2, 10.0), (10, 4.0)), ((2, 10.0), (10, 0.0)), ((2, 5.0), (10, 10.0), (18, 4.0), (25, 0.0)), ((2, 10.0), (10, 0.0), (18, 10.0)),
             ((0, 3.0), (1, 30.0), (2, 0.5), (3, 0.0), (4, 12.0)), ((5, 10.0), (6, 0.0), (7, 10.0), (8, 0.0)), ((1, 0.25), (40, 90.0), (41, 1.0)))


# ---------------------------------------------------------------------------------------------------------------------------------------- the writer
@pytest.mark.parametrize("name", vs.WITNESS_NAMES)
def test_w1_a_start_and_a_start_then_stop_are_the_cores_own_closed_form_bit_for_bit(name):
    constants = _constants(name)
    for start, rate, stop in itertools.product((0, 2, 5), (0.5, 4.0, 5.0, 10.0, 37.3), (1, 2, 7, 30)):
        core = vs.Norepinephrine("o1", start, rate, stop_minute=start + stop, **constants)
        history = _writer(((start, rate), (start + stop, 0.0)), name)
        running = vs.Norepinephrine("o1", start, rate, **constants)
        idle = ts.NorepinephrineRateHistory("o1", start, rate, orders=(("o1", start, rate, ts.STARTED), ("o2", start + 3, rate, ts.IDEMPOTENT)), **constants)
        for minute in range(0, start + stop + 90):
            assert history.support_at(minute) == core.support_at(minute), (name, start, rate, stop, minute)
            assert idle.support_at(minute) == running.support_at(minute), "a history without a change of rate IS the core's own closed form"
            if minute <= start + stop:
                assert history.support_at(minute) == running.support_at(minute), "until the stop the stopped infusion is the running one"


def test_w2_it_is_the_cores_writer_and_writes_one_change_to_the_one_common_state():
    writer = _writer(HISTORIES[3])
    assert isinstance(writer, vs.Norepinephrine) and issubclass(ts.NorepinephrineRateHistory, vs.Norepinephrine) and writer.kind is vs.Norepinephrine.kind
    assert ts.NorepinephrineRateHistory.type_name == "norepinephrine_rate_history" != vs.Norepinephrine.type_name
    assert integration._REGISTRY[ts.NorepinephrineRateHistory.type_name] is ts.NorepinephrineRateHistory and integration._REGISTRY["norepinephrine"] is vs.Norepinephrine
    assert ts.NorepinephrineRateHistory.lung_water_authority is False and ts.NorepinephrineRateHistory.responds_to == frozenset()
    for minute in range(1, 40):
        made = writer.contribute(None, minute, (), None, None)          # no state, no signals, no anchors, no profile: it reads none of them
        fields = {field: getattr(made, field) for field in made.__dataclass_fields__}
        changed = {field for field, value in fields.items() if value not in ((), None)}
        assert changed <= {"vasoconstriction"}, (minute, changed)
        if made.vasoconstriction:
            (change,) = made.vasoconstriction
            assert change.source == writer.source and change.minute == minute and change.amount == writer.support_at(minute) - writer.support_at(minute - 1)
    # the description names the rate ordered for the interval, and a stop says so
    assert "5 mcg/min" in writer.contribute(None, 3, (), None, None).vasoconstriction[0].description
    assert "10 mcg/min" in writer.contribute(None, 11, (), None, None).vasoconstriction[0].description
    assert "4 mcg/min" in writer.contribute(None, 19, (), None, None).vasoconstriction[0].description
    assert writer.contribute(None, 26, (), None, None).vasoconstriction[0].description == "norepinephrine stopped: its support decaying"
    core = vs.Norepinephrine("o1", 2, 10.0, stop_minute=10, **_constants())
    same = _writer(((2, 10.0), (10, 0.0)))
    for minute in (3, 10, 11, 20):
        assert same.contribute(None, minute, (), None, None).vasoconstriction[0].description == core.contribute(None, minute, (), None, None).vasoconstriction[0].description


@pytest.mark.parametrize("name", vs.WITNESS_NAMES)
def test_w3_an_order_never_moves_the_support_in_its_own_minute_and_no_minute_depends_on_a_later_order(name):
    for history in HISTORIES:
        writer = _writer(history, name)
        for cut in range(1, len(history)):
            earlier = _writer(history[:cut], name) if cut > 1 else vs.Norepinephrine("o1", history[0][0], history[0][1], **_constants(name))
            for minute in range(0, history[cut][0] + 1):
                assert writer.support_at(minute) == earlier.support_at(minute), (name, history, cut, minute)
        assert all(writer.support_at(minute) == 0.0 for minute in range(0, history[0][0] + 1)), "an order at minute s first acts over (s, s + 1]"
        assert writer.support_at(history[0][0] + 1) > 0.0


@pytest.mark.parametrize("name", vs.WITNESS_NAMES)
def test_w4_it_rises_with_the_onset_constant_falls_with_the_offset_constant_and_never_passes_the_ordered_rate(name):
    constants = _constants(name)
    half, onset, offset = constants["half_effect_rate_mcg_min"], constants["onset_tau_min"], constants["offset_tau_min"]
    for history in HISTORIES:
        writer = _writer(history, name)
        end = history[-1][0] + 60
        series = [writer.support_at(minute) for minute in range(end + 1)]
        assert series == tt.closed_form(history, end) if name == "CENTER_REFERENCE" else True, "the harness's independent arithmetic gives the same support"
        assert min(series) >= 0.0
        bounds = list(history) + [(end, None)]
        for (at, rate), (until, _next) in zip(bounds, bounds[1:]):
            target, level = rate / half, series[at]
            segment = series[at:until + 1]
            steps = [b - a for a, b in zip(segment, segment[1:])]
            if target > level:
                assert all(step >= 0.0 for step in steps) and max(segment) <= target + QUANTUM, ("an increase never dips and never passes its steady support", name, history, at)
            elif target < level:
                assert all(step <= 0.0 for step in steps) and min(segment) >= target - QUANTUM, ("a decrease never rises and never passes its steady support", name, history, at)
            for index, value in enumerate(segment):
                tau = onset if target > level else offset
                expected = target + (level - target) * math.exp(-index / tau)
                assert abs(value - expected) <= 4 * QUANTUM + 1e-12 * max(1.0, abs(expected)), (name, history, at, index)
        # sixty minutes are twelve of the slowest constant of the region (HIGH's offset, 5 min): what is left of the approach is below 1e-4 of a half-effect
        assert series[-1] == pytest.approx(history[-1][1] / half, abs=1e-4), "left alone, it reaches the steady support of the last rate ordered"


def test_w5_the_two_models_the_design_rejected_would_have_overshot_or_moved_the_wrong_way():
    """Why the rule is ONE contribution approaching ONE ordered rate: stopping the old infusion and starting a new one (two streams) breaks direction with the same constants."""
    constants = _constants("CENTER_REFERENCE")
    old = vs.Norepinephrine("old", 0, 10.0, stop_minute=40, **constants)
    for new_rate, wrong in ((12.0, "above the new steady support"), (9.0, "above the support it had before a DECREASE")):
        new = vs.Norepinephrine("new", 40, new_rate, **constants)
        two_streams = [old.support_at(minute) + new.support_at(minute) for minute in range(40, 60)]
        one = _writer(((0, 10.0), (40, new_rate)))
        single = [one.support_at(minute) for minute in range(40, 60)]
        assert max(two_streams) > max(new_rate / 10.0, two_streams[0]) + 0.05, wrong
        low, high = min(single[0], new_rate / 10.0), max(single[0], new_rate / 10.0)          # between where it was at the order and the new rate's steady support
        assert all(low - QUANTUM <= value <= high + QUANTUM for value in single)


@pytest.mark.parametrize("name", vs.WITNESS_NAMES)
def test_w6_a_decrease_to_almost_nothing_is_almost_a_stop_and_the_changes_sum_exactly_on_the_grid(name):
    stop, nearly = _writer(((2, 10.0), (12, 0.0)), name), _writer(((2, 10.0), (12, 0.001)), name)
    half = _constants(name)["half_effect_rate_mcg_min"]
    assert all(abs(nearly.support_at(minute) - stop.support_at(minute)) <= 0.001 / half + 2 * QUANTUM for minute in range(0, 80)), "the rule is continuous at a stop"
    for history in HISTORIES:
        writer = _writer(history, name)
        total = 0.0
        for minute in range(1, history[-1][0] + 400):
            made = writer.contribute(None, minute, (), None, None)
            total += sum(change.amount for change in made.vasoconstriction)
            assert total == writer.support_at(minute) and total >= 0.0, "the state is exactly what the writer holds, minute after minute"
            assert writer.support_at(minute) / QUANTUM == round(writer.support_at(minute) / QUANTUM)
        if history[-1][1] == 0.0:
            assert total == 0.0, "a stopped infusion returns to exactly nothing"


def test_w7_it_refuses_a_history_it_cannot_represent_or_that_its_orders_do_not_explain():
    constants = _constants()
    good = dict(changes=((10, 10.0),), orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, ts.INCREASED)), **constants)
    assert ts.NorepinephrineRateHistory("o1", 2, 5.0, **good)
    bad = {
        "a stop minute": dict(good, stop_minute=20), "other units": dict(good, rate_units="mcg/kg/min"), "another writer version": dict(good, writer_version="norepinephrine_rate_history/P3-000"),
        "a change at the start minute": dict(good, changes=((2, 10.0),), orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 2, 10.0, ts.INCREASED))),
        "minutes out of order": dict(good, changes=((10, 10.0), (8, 4.0)), orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, ts.INCREASED), ("o3", 8, 4.0, ts.DECREASED))),
        "the same rate as a change": dict(good, changes=((10, 5.0),)), "a negative rate": dict(good, changes=((10, -1.0),)), "a rate that is not a number": dict(good, changes=((10, math.nan),)),
        "a rate in words": dict(good, changes=((10, "ten"),)), "a rate past what the writer represents": dict(good, changes=((10, vs.SUPPORT_LIMIT * 10.0 * 2),)),
        "a minute that is not whole": dict(good, changes=((10.5, 10.0),)), "a malformed change": dict(good, changes=((10,),)),
        "no orders": dict(good, orders=()), "orders that make another history": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 8.0, ts.INCREASED))),
        "an order missing from the accounting": dict(good, orders=(("o1", 2, 5.0, ts.STARTED),)), "an unknown outcome": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, "TITRATED"))),
        "an order accounted twice": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o1", 10, 10.0, ts.INCREASED))), "an id that is not the first order's": dict(good, orders=(("x", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, ts.INCREASED))),
    }
    for label, fields in bad.items():
        with pytest.raises(CoreInvariantError):
            ts.NorepinephrineRateHistory("o1", 2, 5.0, **fields)
        assert label
    for refused_by_the_core in (dict(good, half_effect_rate_mcg_min=None), dict(good, onset_tau_min=0.0), dict(good, offset_tau_min=-1.0)):
        with pytest.raises(CoreInvariantError):
            ts.NorepinephrineRateHistory("o1", 2, 5.0, **refused_by_the_core)
    with pytest.raises(CoreInvariantError):
        ts.NorepinephrineRateHistory("o1", 2, 0.0, **good)                                  # the core's own rule: an infusion starts at a positive rate


def test_w8_its_specification_names_the_whole_history_and_rebuilds_the_same_writer():
    writer = _writer(HISTORIES[3])
    spec = json.loads(json.dumps(writer.to_spec()))
    assert spec["type"] == "norepinephrine_rate_history" and (spec["start_minute"], spec["rate_mcg_min"], spec["changes"]) == (2, 5.0, [[10, 10.0], [18, 4.0], [25, 0.0]])
    assert spec["rate_units"] == "mcg/min" and spec["writer_version"] == ts.WRITER_VERSION == "norepinephrine_rate_history/P3-431" and spec["stop_minute"] is None
    assert [row[0] for row in spec["orders"]] == ["o1", "o2", "o3", "o4"] and [row[3] for row in spec["orders"]] == [ts.STARTED, ts.INCREASED, ts.DECREASED, ts.STOPPED]
    assert (spec["half_effect_rate_mcg_min"], spec["onset_tau_min"], spec["offset_tau_min"]) == (CENTER["half_effect_rate_mcg_min"], CENTER["onset_tau_min"], CENTER["offset_tau_min"])
    rebuilt = integration.from_spec(spec)
    assert rebuilt == writer and type(rebuilt) is ts.NorepinephrineRateHistory and rebuilt.carried_order_ids == ("o1", "o2", "o3", "o4")
    for tampered in ({**spec, "writer_version": "another"}, {**spec, "rate_units": "mcg/kg/min"}, {**spec, "changes": [[10, 10.0]]}):
        with pytest.raises(CoreInvariantError):
            integration.from_spec(tampered)
    assert writer.ordered_rate_over(2) == 0.0 and writer.ordered_rate_over(3) == 5.0 and writer.ordered_rate_over(10) == 5.0 and writer.ordered_rate_over(11) == 10.0
    assert writer.ordered_rate_over(25) == 4.0 and writer.ordered_rate_over(26) == 0.0


# ---------------------------------------------------------------------------------------------------------------------------------------- the orders
def test_m1_one_infusion_and_one_ordered_rate_each_order_replaces_the_one_before_it():
    point = vs.witness("CENTER_REFERENCE")
    events = [_event(2, "a", "start", 5.0), _event(6, "b", "adjust", 10.0), _event(9, "c", "continue", 10.0), _event(12, "d", "start", 12.0), _event(15, "e", "adjust", 4.0),
              _stop(20, "f"), _stop(22, "g"), _event(25, "h", "adjust", 8.0), _event(30, "i", "start", 8.0)]
    physical, carried, declared = ts.infusion_history(events, point)
    assert [row[3] for row in carried] == [ts.STARTED, ts.INCREASED, ts.IDEMPOTENT, ts.INCREASED, ts.DECREASED, ts.STOPPED, ts.IDEMPOTENT, ts.RESTARTED, ts.IDEMPOTENT] and declared == ()
    assert physical == ((2, 5.0), (6, 10.0), (12, 12.0), (15, 4.0), (20, 0.0), (25, 8.0)), "one rate at a time: the same rate again and a stop of a stopped infusion change nothing"
    built, gaps = ts.map_orders(events, (), [], point)
    assert len(built) == 1 and gaps == [] and built[0].id == "a" and built[0].carried_order_ids == tuple("abcdefghi")
    assert ((built[0].start_minute, built[0].rate_mcg_min),) + built[0].changes == physical
    assert set(ts.OUTCOMES) == {ts.STARTED, ts.INCREASED, ts.DECREASED, ts.STOPPED, ts.RESTARTED, ts.IDEMPOTENT} and ts.MAPPED_OPERATIONS == ("start", "adjust", "continue", "stop")


def test_m2_within_one_minute_the_last_order_is_the_one_a_modelled_interval_carries():
    """P3-435, REVISED after the adversarial review. The earlier rule carried EVERY valid order of a minute and reported the replaced ones as built, with an effective minute they never had;
    and a history that began with orders nothing ever carried kept the id of the first of them. Now the infusion carries ONE order a minute -- the last valid one -- and an order replaced
    within its minute is a declared gap that says so. What the test protected holds: the last order of the minute is the one a modelled interval carries, whatever the ids are spelled."""
    point = vs.witness("CENTER_REFERENCE")
    replaced = lambda operation: ts.GAP_REPLACED.format(operation=operation)
    # the position in the mirror decides within a minute, never the spelling of the order id
    events = [_event(5, "z-first", "start", 5.0), _event(5, "a-second", "adjust", 10.0)]
    built, gaps = ts.map_orders(events, (), [], point)
    assert built == (vs.Norepinephrine("a-second", 5, 10.0, **_constants()),) and type(built[0]) is vs.Norepinephrine, "ONE carried order is the core's own writer, at the rate that ran"
    assert gaps == [{"order_id": "z-first", "kind": "norepinephrine", "why": replaced("start")}]
    log = ts.order_log(events, point)
    assert [(row["order_id"], row["outcome"], row["carried"], row["replaced_within_its_minute"]) for row in log] == [("z-first", ts.REPLACED, False, True), ("a-second", ts.STARTED, True, False)]
    assert log[0]["first_acts_over"] is None and log[1]["first_acts_over"] == [5, 6]
    # a stop and a new rate in the same minute of a running infusion: ONE change to the new rate, never a decay followed by a restart
    built, gaps = ts.map_orders([_event(2, "a", "start", 5.0), _stop(9, "b"), _event(9, "c", "start", 10.0)], (), [], point)
    assert gaps == [{"order_id": "b", "kind": "norepinephrine", "why": replaced("stop")}] and built[0].changes == ((9, 10.0),)
    assert built[0].orders == (("a", 2, 5.0, ts.STARTED), ("c", 9, 10.0, ts.INCREASED)), "what the order DID is read against the rate that ran before it"
    # the net of a minute that leaves the rate where it was is no change at all
    built, gaps = ts.map_orders([_event(2, "a", "start", 5.0), _event(9, "b", "adjust", 10.0), _event(9, "c", "adjust", 5.0)], (), [], point)
    assert [gap["order_id"] for gap in gaps] == ["b"] and built[0].changes == () and built[0].orders == (("a", 2, 5.0, ts.STARTED), ("c", 9, 5.0, ts.IDEMPOTENT))
    # started and stopped within one minute, then started: nothing ran before minute 7, and the infusion has the id of the order that started what ran
    built, gaps = ts.map_orders([_event(2, "a", "start", 5.0), _stop(2, "b"), _stop(4, "b2"), _event(7, "c", "start", 10.0)], (), [], point)
    assert built == (vs.Norepinephrine("c", 7, 10.0, **_constants()),)
    assert [(gap["order_id"], gap["why"]) for gap in gaps] == [("a", replaced("start")), ("b", ts.GAP_NOTHING_TO_BUILD.format(operation="stop")), ("b2", ts.GAP_NOTHING_TO_BUILD.format(operation="stop"))]
    assert ts.physical_history((("a", 2, 5.0, ts.STARTED), ("b", 6, 5.0, ts.IDEMPOTENT), ("c", 7, 10.0, ts.INCREASED))) == ((2, 5.0), (7, 10.0))
    # a bare continuation keeps the rate ordered before it; one that gives a number without units is refused like any other
    built, gaps = ts.map_orders([_event(2, "a", "start", 5.0), _event(6, "b", "continue", None, None), _event(9, "c", "continue", 12.0, None)], (), [], point)
    assert built[0].orders == (("a", 2, 5.0, ts.STARTED), ("b", 6, 5.0, ts.IDEMPOTENT)) and [gap["order_id"] for gap in gaps] == ["c"] and "gives no units" in gaps[0]["why"]


def test_m3_the_first_order_the_mapping_cannot_read_closes_the_infusion_and_nothing_after_it_is_applied():
    point = vs.witness("CENTER_REFERENCE")
    refusals = {"other units": _event(12, "bad", "adjust", 8.0, "mg/h"), "a weight-based rate": _event(12, "bad", "adjust", 0.2, "mcg/kg/min"), "a negative rate": _event(12, "bad", "adjust", -5.0),
                "a zero rate that is not a stop": _event(12, "bad", "adjust", 0.0), "a pressure target": _event(12, "bad", "titrate to MAP 65", None, None),
                "a pressure target as the parser really hands it over (a bare number)": _event(12, "bad", "adjust", 65.0, None), "a rate without units": _event(12, "bad", "adjust", 12.0, None),
                "a rate past what the core's writer represents": _event(12, "bad", "adjust", vs.SUPPORT_LIMIT * 10.0 * 2.0),
                "a rate too large to be a number": _event(12, "bad", "adjust", 10 ** 400), "a rate in words": _event(12, "bad", "adjust", "eight"),
                "no action": rs.MirroredAction("bad", 12, "norepinephrine", None, {}, 0.21), "an action that is not an order": rs.MirroredAction("bad", 12, "norepinephrine", "start 10", {}, 0.21),
                "an action that says it is another drug": rs.MirroredAction("bad", 12, "norepinephrine", {"type": "dobutamine", "operation": "adjust", "rate": 8.0, "units": "mcg/min"}, {}, 0.21),
                "two different rates": rs.MirroredAction("bad", 12, "norepinephrine", {"type": "norepinephrine", "operation": "adjust", "rate": 8.0, "units": "mcg/min", "rate_mcg_min": 80.0}, {}, 0.21),
                "a receipt that says another rate": rs.MirroredAction("bad", 12, "norepinephrine", dict(_event(12, "x", "adjust", 8.0).action), {"operation": "adjust", "rate": 80.0, "units": "mcg/min"}, 0.21),
                "a receipt that says other units": rs.MirroredAction("bad", 12, "norepinephrine", dict(_event(12, "x", "adjust", 8.0).action), {"operation": "adjust", "rate": 8.0, "units": "mcg/kg/min"}, 0.21),
                "a receipt that says another operation": rs.MirroredAction("bad", 12, "norepinephrine", dict(_event(12, "x", "adjust", 8.0).action), {"operation": "stop"}, 0.21),
                "a bare continuation the engine ran at another rate": rs.MirroredAction("bad", 12, "norepinephrine", dict(_event(12, "x", "continue", None, None).action), {"operation": "continue", "rate": 12.0, "units": "mcg/min"}, 0.21)}
    alone = ts.map_orders([_event(5, "o1")], (), [], point)[0]
    for label, bad in refusals.items():
        built, gaps = ts.map_orders([_event(5, "o1"), bad, _event(15, "later", "adjust", 6.0), _stop(20, "stop")], (), [], point)
        assert built == alone, (label, "the run keeps the history it had mapped, and nothing after the refused order is applied")
        assert [gap["order_id"] for gap in gaps] == ["bad", "later", "stop"] and gaps[0]["why"].endswith(ts.NO_LONGER_MIRRORED), label
        assert all("after an order the run could not map" in gap["why"] and "no longer mirrors" in gap["why"] for gap in gaps[1:]), label
        assert ". From this order on" in gaps[0]["why"], "the reason and what follows from it are two sentences"
        log = ts.order_log([_event(5, "o1"), bad, _event(15, "later", "adjust", 6.0)], point)
        assert [row["outcome"] for row in log] == [ts.STARTED, ts.REFUSED, ts.REFUSED] and log[1]["why"] == gaps[0]["why"]
    # the run must have SEEN the infusion start: an adjustment, a continuation or a stop first is refused, and no later start is put in its place
    for first in (_stop(3, "first"), _event(3, "first", "adjust", 6.0), _event(3, "first", "continue", 6.0), _event(3, "first", "start", 0.1, "mcg/kg/min")):
        built, gaps = ts.map_orders([first, _event(9, "second")], (), [], point)
        assert built == () and [gap["order_id"] for gap in gaps] == ["first", "second"] and gaps[0]["why"].endswith(ts.NOT_MIRRORED) and gaps[1]["why"] == ts.GAP_NOT_MIRRORED
    # an order without a whole minute at or after the arrival: no order of the infusion can be established, so none is mapped
    for minute in (5.5, -1, None, True, "5"):
        built, gaps = ts.map_orders([rs.MirroredAction("odd", minute, "norepinephrine", dict(_event(5, "x").action), {}, 0.21), _event(9, "second")], (), [], point)
        assert built == () and [gap["order_id"] for gap in gaps] == ["odd", "second"] and all(ts.GAP_CHRONOLOGY in gap["why"] for gap in gaps), minute
    # ... nor an order without an identity (P3-435: an id that is not text used to raise instead of being declared)
    for order_id in (None, "", 7, ["x"], {"a": 1}):
        built, gaps = ts.map_orders([_event(5, "first"), rs.MirroredAction(order_id, 9, "norepinephrine", dict(_event(9, "x", "adjust", 6.0).action), {}, 0.21)], ("a-fluid",), [], point)
        assert built == ("a-fluid",) and [gap["order_id"] for gap in gaps] == ["first", order_id] and all(ts.GAP_CHRONOLOGY in gap["why"] for gap in gaps), order_id
        assert [row["outcome"] for row in ts.order_log([_event(5, "first"), rs.MirroredAction(order_id, 9, "norepinephrine", None, {}, 0.21)], point)] == [ts.REFUSED, ts.REFUSED]


def test_m4_a_weight_based_rate_is_never_converted_and_a_run_never_carries_two_writers_of_the_kind():
    point = vs.witness("CENTER_REFERENCE")
    source = (ROOT / "runtime_tone_support.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not names & {"weight_kg", "infusion_weight", "weight", "kg", "weight_based_doses"}, "the mapping reads no weight: there is nothing to convert with"
    assert not names & {"sbp", "dbp", "map", "pressure_rel", "output_rel", "delivery_rel", "target_map", "mmhg"}, "no pressure is read and none is written: no drug -> mmHg shortcut"
    writer = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "NorepinephrineRateHistory")
    read = {node.attr for node in ast.walk(writer) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in ("state", "signals", "anchors", "profile")}
    assert read == set(), "the writer reads nothing of the state it is handed (the writer contract)"
    already = vs.Norepinephrine("family-built", 1, 5.0, **_constants())
    with pytest.raises(ts.ToneSupportUnavailable, match="one writer of the kind, never two"):
        ts.map_orders([_event(5, "o1")], (already,), [], point)
    for events in ([_event(5, "a"), _event(9, "b", "adjust", 20.0), _stop(12, "c"), _event(15, "d")], [_event(5, "a"), _event(5, "b")], [_event(5, "a")]):
        built, _gaps = ts.map_orders(events, ("a-fluid",), [], point)
        assert len([item for item in built if isinstance(item, vs.Norepinephrine)]) == 1


@pytest.mark.parametrize("family", sorted(fam.ADAPTERS))
def test_m5_every_order_is_reported_built_or_declared_never_dropped(family):
    adapter = ts.with_tone_support(fam.ADAPTERS[family], "CENTER_REFERENCE")
    cases = {"a history": ([_event(5, "a", "start", 5.0), _event(9, "b", "adjust", 10.0), _event(11, "c", "continue", 10.0), _stop(14, "d"), _event(20, "e")], [fam.BUILT] * 5),
             # P3-435: an order replaced within its minute used to be reported BUILT, with an effective minute it never had
             "replaced within its minute": ([_event(5, "a", "start", 5.0), _event(9, "b", "adjust", 10.0), _event(9, "c", "adjust", 7.0), _stop(14, "d")], [fam.BUILT, fam.DECLARED_GAP, fam.BUILT, fam.BUILT]),
             "a refusal": ([_event(5, "a"), _event(9, "b", "adjust", 0.1, "mcg/kg/min"), _stop(14, "c")], [fam.BUILT, fam.DECLARED_GAP, fam.DECLARED_GAP]),
             "never seen to start": ([_stop(5, "a"), _event(9, "b")], [fam.DECLARED_GAP, fam.DECLARED_GAP]),
             "started and stopped within a minute": ([_event(5, "a"), _stop(5, "b")], [fam.DECLARED_GAP, fam.DECLARED_GAP])}
    for label, (events, expected) in cases.items():
        rows = [row for row in fam.action_dispositions(adapter, events, None) if row["kind"] == "norepinephrine"]
        assert [row["disposition"] for row in rows] == expected, (family, label, rows)
        assert all(row["effective_minute"] == row["order_minute"] + 1 for row in rows if row["disposition"] == fam.BUILT)
        assert fam.UNACCOUNTED not in [row["disposition"] for row in fam.action_dispositions(adapter, events, None)]
    assert len(fam.DISPOSITIONS) == 8, "the vocabulary of dispositions did not grow: a carried order is BUILT"


def test_m6_nothing_else_moved_no_registered_adapter_no_authority_no_constant_and_the_core_is_the_certified_one():
    from clinical_core import amendment_3 as a3
    assert a3.amended_core_digest_now() == CORE_DIGEST and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert vs.witness("CENTER_REFERENCE") == CENTER and vs.WITNESSES["LOW"]["tone_gain"] == 0.3 and vs.WITNESSES["HIGH"]["tone_gain"] == 0.9
    assert ts.ORDER_KIND not in ra.SUPPORTED_ACTIONS and "norepinephrine" in grants.LIVE_GRANT["not_granted"] and "titration" not in " ".join(ra.SUPPORTED_ACTIONS)
    assert grants.LIVE_GRANT["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"
    for family, adapter in fam.ADAPTERS.items():
        assert adapter.tone_support_witness is None and ts.ORDER_KIND not in adapter.maps, family
        built, gaps = adapter.interventions([_event(5, "a"), _event(9, "b", "adjust", 20.0)], None)
        assert not [item for item in built if isinstance(item, vs.Norepinephrine)] and len([gap for gap in gaps if gap.get("kind") == "norepinephrine"]) == 2, family
    summary = ts.summary()
    assert summary["status"] == "DEVELOPMENT_SHADOW_ONLY" and summary["registered_adapters_declaring_it"] == [] and summary["chosen_witness"] is None
    assert any("automatic titration" in item for item in summary["not_granted"]) and "a weight-based dose" in summary["not_granted"] and "runtime authority" in summary["not_granted"]
    assert summary["mapped"]["units"] == "mcg/min" and summary["mapped"]["operations"] == ["start", "adjust", "continue", "stop"]
    import runtime_faculty_review as review
    assert review.scenario("FR-F")["expected"] == "HALTED_BY_UNSUPPORTED_ACTION", "the live GI pressure authority still stops on the order"
    readers = [path.name for path in sorted(ROOT.glob("*.py")) if not path.name.startswith("test_") and path.name not in ("conftest.py", "runtime_tone_support.py")
               and "NorepinephrineRateHistory" in path.read_text(encoding="utf-8")]
    assert readers == [], "no page, no engine, no authority and no scoring names the rate-history writer"
    assert "carried_order_ids" in (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8") and "import runtime_tone_support" not in (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------------------------------- the GI trajectories
@pytest.fixture(scope="module")
def gi():
    return tt.gi_probes()


def test_g1_the_predictions_were_written_before_the_runs_and_every_one_holds(gi):
    assert set(gi["checks"]) == set(tt.GI_PREDICTIONS) == {"TIMING", "DIRECTION", "ORDERING", "SMOOTHNESS", "PERSISTENCE_AND_DECAY", "UNTOUCHED_STATE", "HISTORICAL"}
    for name, held in gi["checks"].items():
        assert held is True, f"the prediction {name} did not hold: {tt.GI_PREDICTIONS[name]}"
    assert gi["all_as_predicted"] is True and gi["witness"] == "CENTER_REFERENCE" and gi["case_id"] == "gi_bleed_57m"
    assert gi["named_probes"] == {"A": "A_START", "B": "B_START_INCREASE", "C": "C_START_DECREASE", "D": "D_START_STOP", "E": "E_START_INCREASE_DECREASE_STOP", "RESTART": "F_START_STOP_RESTART"}


def test_g2_the_real_engine_executed_these_orders_and_runs_the_rate_the_shadow_carries(gi):
    """Real order text through the real parser and engine: the mirror hands over a start, absolute-rate adjustments and a stop, and the engine's own active rate is the run's ordered rate."""
    for name, probe in gi["probes"].items():
        history = tt.GI_HISTORIES[name]
        assert all(turn["executed"] for turn in probe["turns"]) and [turn["to_minute"] for turn in probe["turns"]] == list(tt.READS), name
        assert [(row["minute"], row["ordered_rate_mcg_min"]) for row in probe["orders"]] == [(minute, rate) for minute, rate in history], name
        assert probe["legacy_engine_active_rate_at_the_end_mcg_min"] == (history[-1][1] if history else 0.0), (name, "the engine and the run hold the same ordered rate")
        operations = [row["operation"] for row in probe["orders"]]
        assert operations[:1] in ([], ["start"]) and set(operations[1:]) <= {"adjust", "stop", "start"}, (name, operations)
        assert all(row["units"] == "mcg/min" for row in probe["orders"] if row["operation"] != "stop")
    e = gi["probes"]["E_START_INCREASE_DECREASE_STOP"]
    assert [(row["operation"], row["outcome"]) for row in e["orders"]] == [("start", ts.STARTED), ("adjust", ts.INCREASED), ("adjust", ts.DECREASED), ("stop", ts.STOPPED)]
    assert [row["first_acts_over"] for row in e["orders"]] == [[2, 3], [10, 11], [18, 19], [25, 26]]
    assert [row["outcome"] for row in gi["probes"]["F_START_STOP_RESTART"]["orders"]] == [ts.STARTED, ts.STOPPED, ts.RESTARTED]


def test_g3_each_probe_has_one_writer_every_order_built_no_gap_and_replays_exactly(gi):
    for name, probe in gi["probes"].items():
        orders = len(tt.GI_HISTORIES[name])
        assert probe["writers"] == ([] if orders == 0 else ["norepinephrine"] if orders == 1 else ["norepinephrine_rate_history"]), name
        assert probe["dispositions"] == ["BUILT"] * orders and probe["gaps"] == [] and probe["failures"] == [] and probe["replays_exactly"] is True, name
        assert probe["support_is_the_closed_form"] and probe["support_never_negative"] and probe["support_never_moves_in_the_minute_of_an_order"] and probe["every_step_within_its_first_order_bound"], name
        assert all(probe["untouched_state"].values()) and probe["unmapped_run_is_the_no_order_run"], name
        if orders > 1:
            spec = probe["writer_spec"]
            assert [[spec["start_minute"], spec["rate_mcg_min"]]] + spec["changes"] == [list(item) for item in tt.GI_HISTORIES[name]] and spec["rate_units"] == "mcg/min"
            assert (spec["half_effect_rate_mcg_min"], spec["onset_tau_min"], spec["offset_tau_min"]) == (10.0, 1.5, 2.5), "the ratified constants, unchanged"


def test_g4_each_order_acts_one_minute_later_in_the_right_direction_and_never_before(gi):
    assert [(pair["with"], pair["order"], pair["order_minute"]) for pair in gi["pairs"]] == [(a, d, c) for a, _b, c, d in tt.GI_PAIRS]
    for pair in gi["pairs"]:
        s = pair["order_minute"]
        assert (pair["support_first_differs_at"], pair["tone_first_differs_at"], pair["pressure_first_differs_at"]) == (s + 1, s + 2, s + 2), pair["with"]
        assert pair["states_identical_through_the_order_minute"] and pair["never_on_the_wrong_side"] and pair["on_the_right_side_somewhere"], pair["with"]


def test_g5_the_plateaus_order_as_the_rates_and_a_stop_decays_and_is_never_a_step(gi):
    e = {row["minute"]: row for row in gi["probes"]["E_START_INCREASE_DECREASE_STOP"]["at_the_reads"]}
    assert e[18]["support"] > e[10]["support"] > e[25]["support"] > e[32]["support"] > 0.0
    assert e[18]["pressure_against_the_unmapped_run"] > e[10]["pressure_against_the_unmapped_run"] > e[25]["pressure_against_the_unmapped_run"] > e[32]["pressure_against_the_unmapped_run"] > 1.0
    d = gi["probes"]["D_START_STOP"]
    support = [row["support"] or 0.0 for row in d["per_minute"]]
    assert support[10] > 0.99 and support[11] == pytest.approx(support[10] * math.exp(-1 / 2.5), abs=1e-9), "one minute after the stop most of the support is still there"
    assert all(b < a for a, b in zip(support[10:], support[11:])) and support[22] < 0.01 * support[10]
    tone = [row["T"] for row in d["per_minute"]]
    assert tone[11] == pytest.approx(gi["probes"]["A10_START"]["per_minute"][11]["T"]), "the tone has not yet moved the minute after the stop: it follows the state one minute behind"
    ratio = {row["minute"]: row["pressure_against_the_unmapped_run"] for row in d["at_the_reads"]}
    assert ratio[10] > 1.15 and abs(ratio[32] - 1.0) < 0.001, "the pressure effect is gone 22 minutes after the stop, and it went gradually"
    start = gi["probes"]["A10_START"]["largest_one_minute_change_of_the_tone_against_the_unmapped_run"]
    assert all(probe["largest_one_minute_change_of_the_tone_against_the_unmapped_run"] <= start + 1e-12 for probe in gi["probes"].values()), "no change of rate moves the tone faster than the reviewed start did"
    f = {row["minute"]: row for row in gi["probes"]["F_START_STOP_RESTART"]["at_the_reads"]}
    assert f[18]["support"] < 0.05 and f[25]["support"] > 0.99 and f[32]["support"] <= 1.0 + QUANTUM, "a restart rises again and does not pass its steady support"


def test_g6_the_plain_start_is_the_run_the_faculty_reviewed_minute_by_minute(gi):
    """Historical compatibility on the reviewed case: the same start at minute 2 gives, minute by minute, the pressure the certified FR-F candidate stores -- whatever the turns were."""
    stored = ta.load(ta.CANDIDATE_PATH)["witnesses"]["CENTER_REFERENCE"]["per_minute"]
    run = tt.gi_run("A10_START")
    assert len(stored) == len(run["rows"]) == 33
    for old, new in zip(stored, run["rows"]):
        assert {key: old[key] for key in ("minute", "support", "T", "V", "P", "hb", "pressure_rel", "sbp", "dbp", "map")} == {key: new[key] for key in ("minute", "support", "T", "V", "P", "hb", "pressure_rel", "sbp", "dbp", "map")}
    assert [type(item).type_name for item in tt.writers_of(run)] == ["norepinephrine"]


# ---------------------------------------------------------------------------------------------------------------------------------------- the edge cases
@pytest.fixture(scope="module")
def edges():
    return tt.edge_matrix()


def test_e1_every_edge_case_has_the_outcome_written_before_it_was_executed(edges):
    assert [row["case"] for row in edges] == list(tt.EDGE_EXPECTED) and len(edges) == 21, "the seventeen of the first matrix and the four the adversarial review added"
    required = ("START_FROM_ZERO", "INCREASE", "DECREASE", "STOP", "RESTART_AFTER_STOP", "DUPLICATE_IDENTICAL_RATE", "TWO_ORDERS_IN_ONE_MINUTE", "INVALID_UNIT", "NEGATIVE_DOSE",
                "STOP_WITHOUT_PRIOR_START", "WEIGHT_BASED", "MALFORMED_ORDER", "NO_PULSE_STATE", "SESSION_RESTART_AND_REPLAY")
    assert all(any(name in row["case"] for row in edges) for name in required), "the fourteen cases the assignment names"
    for row in edges:
        assert row["as_expected"] is True, (row["case"], row["expected_before_executing"], row["observed"])
        assert row["expected_before_executing"] == tt.EDGE_EXPECTED[row["case"]] and row["what"] == tt.EDGE_DESCRIPTIONS[row["case"]]
    # what the review changed is said in the rows, and the expectation it replaced is kept: nothing was quietly adjusted to pass
    assert [row["case"] for row in edges if "revised_after_the_adversarial_review" in row] == ["07_TWO_ORDERS_IN_ONE_MINUTE"]
    was = next(row for row in edges if row["case"] == "07_TWO_ORDERS_IN_ONE_MINUTE")["revised_after_the_adversarial_review"]["expected_before_the_review"]
    assert was["outcomes"] == ["STARTED", "INCREASED"] and was["writer"] == "norepinephrine_rate_history" and was["gaps"] == 0 and was != tt.EDGE_EXPECTED["07_TWO_ORDERS_IN_ONE_MINUTE"]
    assert [row["case"] for row in edges if row.get("added_after_the_adversarial_review")] == tt.EDGE_ADDED_AFTER_THE_REVIEW["cases"] and len(tt.EDGE_ADDED_AFTER_THE_REVIEW["cases"]) == 4


def test_e2_the_edge_cases_that_matter_most_read_as_they_should(edges):
    seen = {row["case"]: row["observed"] for row in edges}
    assert seen["04_STOP"]["bit_identical_to_the_cores_own_stopped_writer"] and seen["04_STOP"]["support_at_the_stop_minute_is_not_erased"] and seen["04_STOP"]["support_returns_to_exactly_zero"]
    assert seen["06_DUPLICATE_IDENTICAL_RATE"]["states_equal_to"] == "THE_SINGLE_START" and seen["07_TWO_ORDERS_IN_ONE_MINUTE"]["states_equal_to"] == "A_SINGLE_START_AT_THE_LAST_RATE"
    assert seen["11B_WEIGHT_BASED_RATE_CHANGE"]["never_converted"] and seen["11A_WEIGHT_BASED_FIRST_ORDER"]["writers"] == 0
    assert set(seen["12_MALFORMED_ORDER"]["variants"]) >= {"A_PRESSURE_TARGET", "NO_ACTION"} and all(item["writers"] == 1 for item in seen["12_MALFORMED_ORDER"]["variants"].values())
    assert seen["13_NO_PULSE_STATE"]["the_run_completes"] and seen["13_NO_PULSE_STATE"]["no_pressure_is_reported_without_a_pulse"] and seen["13_NO_PULSE_STATE"]["first_minute_without_a_pulse"] == 9
    replay = seen["14_SESSION_RESTART_AND_REPLAY"]
    assert replay["the_artifact_survives_json_and_replays_exactly"] and replay["orders_mirrored_as_they_are_given_give_the_same_states"] and replay["any_division_into_turns_gives_the_same_states"]
    assert seen["15B_ORDER_DATED_BEFORE_A_RECORDED_MINUTE"]["the_runner_refuses_it"] == "HistoryRewritten"
    assert replay["orders_mirrored_as_they_are_given_declare_the_same_gaps"] is True
    assert set(seen["12_MALFORMED_ORDER"]["variants"]) >= set(tt.EDGE_ADDED_AFTER_THE_REVIEW["variants_of_12"])
    assert seen["16_ORDER_THAT_NAMES_NO_DRUG"]["the_order_that_names_no_drug_says_why"] and seen["16_ORDER_THAT_NAMES_NO_DRUG"]["left_alone_while_no_norepinephrine_runs"]
    assert seen["17_REFUSED_ORDER_IN_THE_MINUTE_OF_A_VALID_ONE"]["states_equal_to"] == "THE_SINGLE_START", "the rate ordered in the minute of the refusal never ran, and is not carried"
    assert seen["18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN"]["the_gaps_recorded_turn_by_turn_are_the_gaps_of_the_whole"] and seen["18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN"]["no_order_is_both_declared_and_built"]


def test_e3_a_rate_history_artifact_is_refused_by_name_where_its_writer_is_not_registered(monkeypatch):
    """A process that has not loaded the development mapping does not approximate the history: the artifact is refused, by the type's name."""
    run = tt._edge_run((tt.event(5, "start", 5.0), tt.event(12, "adjust", 10.0)))
    artifact = json.loads(json.dumps(run["runner"].replay_input().to_dict()))
    assert fam.replay_shadow_encounter(artifact)["final_digest"] == run["runner"].digests()[-1]
    monkeypatch.setattr(integration, "_REGISTRY", {key: value for key, value in integration._REGISTRY.items() if key != ts.NorepinephrineRateHistory.type_name})
    with pytest.raises(Exception, match="no contributor type 'norepinephrine_rate_history'"):
        fam.replay_shadow_encounter(artifact)
    single = tt._edge_run((tt.event(5, "start", 10.0),))
    old = json.loads(json.dumps(single["runner"].replay_input().to_dict()))
    assert fam.replay_shadow_encounter(old)["final_digest"] == single["runner"].digests()[-1], "a single-start artifact replays without the new writer: it never names it"
    assert [item["type"] for item in old["scenario"]["contributors"] if "norepinephrine" in item["type"]] == ["norepinephrine"]


# ---------------------------------------------------------------------------------------------------------------------------------------- the adversarial review (P3-435)
def test_r1_an_order_that_names_no_drug_closes_the_infusion_while_the_norepinephrine_runs():
    """BLOCKER of the review. 'Stop the infusion' is resolved by the engine to the running norepinephrine and mirrored as an infusion adjustment with an empty receipt: the mapping ignored it and
    the shadow kept the pressor running without a word. It cannot know which infusion the engine changed, so it fails closed and says so."""
    point = vs.witness("CENTER_REFERENCE")
    alone = ts.map_orders([_event(5, "o1")], (), [], point)[0]
    family_gap = {"order_id": "role", "kind": "infusion_adjustment", "why": "no core intervention for this order type yet"}
    for role in (_role(12, "role", "stop"), _role(12, "role", "adjust", 20.0, "mcg/min")):
        events = [_event(5, "o1"), role, _event(15, "later", "adjust", 6.0), _stop(20, "stop")]
        built, gaps = ts.map_orders(events, (), [family_gap], point)
        assert built == alone, "the run keeps the history it had mapped"
        assert [(gap["order_id"], gap["kind"]) for gap in gaps] == [("role", "infusion_adjustment"), ("later", "norepinephrine"), ("stop", "norepinephrine")], "its own gap replaces the family's, once"
        assert gaps[0]["why"] == f"{ts.GAP_ROLE_NAMED}. {ts.NO_LONGER_MIRRORED}" and "names no drug" in gaps[0]["why"] and "nothing is guessed" in gaps[0]["why"]
        assert [(row["kind"], row["outcome"], row["carried"]) for row in ts.order_log(events, point)] == [("norepinephrine", ts.STARTED, True), ("infusion_adjustment", ts.REFUSED, False),
                                                                                                         ("norepinephrine", ts.REFUSED, False), ("norepinephrine", ts.REFUSED, False)]
    # in the minute of a valid order, that order never ran: it is replaced, and the history ends before that minute
    built, gaps = ts.map_orders([_event(5, "o1"), _event(12, "o2", "adjust", 20.0), _role(12, "role")], (), [family_gap], point)
    assert built == alone and [(gap["order_id"], gap["why"].split(":")[0]) for gap in gaps][0] == ("o2", ts.GAP_REPLACED.format(operation="adjust").split(":")[0]) and gaps[1]["order_id"] == "role"
    built, gaps = ts.map_orders([_event(5, "o1"), _role(5, "role")], (), [family_gap], point)
    assert built == () and [gap["order_id"] for gap in gaps] == ["o1", "role"], "started and closed within one minute: nothing ran"
    # while no norepinephrine runs as far as the run knows, the order is another infusion's: it is left exactly as the family declared it, and the infusion goes on
    for events, outcomes in (([_role(3, "role")], []), ([_role(3, "role"), _event(5, "o1")], [ts.STARTED]), ([_event(5, "o1"), _stop(9, "o2"), _role(12, "role"), _event(15, "o3")], [ts.STARTED, ts.STOPPED, ts.RESTARTED]),
                             ([_event(5, "o1"), _stop(5, "o2"), _role(5, "role"), _event(9, "o3")], [ts.REPLACED, ts.NOTHING_TO_BUILD, ts.STARTED])):
        built, gaps = ts.map_orders(events, (), [family_gap], point)
        assert family_gap in gaps and not [gap for gap in gaps if "names no drug" in gap["why"]] and [row["outcome"] for row in ts.order_log(events, point)] == outcomes, events
    # every family's development copy reports it: declared, with the reason, never dropped
    for family in sorted(fam.ADAPTERS):
        rows = fam.action_dispositions(ts.with_tone_support(fam.ADAPTERS[family], "CENTER_REFERENCE"), [_event(5, "o1"), _role(12, "role"), _stop(20, "stop")], None)
        assert [(row["kind"], row["disposition"]) for row in rows] == [("norepinephrine", fam.BUILT), ("infusion_adjustment", fam.DECLARED_GAP), ("norepinephrine", fam.DECLARED_GAP)], family
        assert "names no drug" in rows[1]["why"] and "no longer mirrors" in rows[1]["why"] and "no longer mirrors" in rows[2]["why"]


@pytest.fixture(scope="module")
def real_text():
    return tt.real_text_probes()


def test_r2_the_reviews_own_sentences_through_the_real_encounter_never_leave_the_run_silently_wrong(real_text):
    """The order is read AS WRITTEN. Through the real parser, engine and mirror: an order that names no drug and a rate without units close the infusion and SAY so; a pressure target is never
    read as a rate; a weight-based dose is never converted; a bare continuation and a stop that carries a rate are read for what they are."""
    assert set(real_text["probes"]) == set(tt.REAL_TEXT_SCRIPTS) == set(tt.REAL_TEXT_EXPECTED) and len(real_text["probes"]) == 8
    # ADAPTED (P3-455, 2026-11-20). The expectations the harness holds for R3 and R5 were written about LEGACY DEFECTS of the unit-less rate: the reader emits "Increase norepinephrine to 12" and "Titrate norepinephrine to
    # MAP 65" as rates WITHOUT units, the engine completed the missing unit from the running infusion and ran 12 and 65 mcg/min, and the shadow (which reads the order as written) refused them. FD-NR-05 repaired it before
    # the engine, in the order pipeline (the reader and the engine are frozen): a rate without units is held as a question and never reaches the engine or the mirror. So R3 and R5 no longer behave as those historical
    # expectations say. The harness and its sealed records are NOT edited: they stay as the record of what was observed. What this test protects is unchanged and now stronger: a number without units is never read as a
    # rate, the run and the engine agree, and the later stop of R3 is followed. The other six probes are held exactly as before.
    historical_defects = {
        "R3_INCREASE_WITHOUT_UNITS_THEN_STOP": {"kinds": ["norepinephrine", "norepinephrine"], "outcomes": [ts.STARTED, ts.STOPPED], "writer": "norepinephrine_rate_history", "states_equal_to": "DIFFERENT_STATES",
                                                "engine_rate_at_the_end": 0.0, "run_rate_at_the_end": 0.0, "says_it_no_longer_mirrors": False},
        "R5_PRESSURE_TARGET": {"kinds": ["norepinephrine"], "outcomes": [ts.STARTED], "writer": "norepinephrine", "states_equal_to": "A10_START", "engine_rate_at_the_end": 10.0, "run_rate_at_the_end": 10.0,
                               "says_it_no_longer_mirrors": False}}
    for name, probe in real_text["probes"].items():
        if name in historical_defects:
            assert probe["as_expected"] is False, f"the historical expectation of {name} described the defect that was repaired"
            assert probe["observed"] == historical_defects[name], (name, probe["observed"])
            assert probe["failures"] == [] and probe["replays_exactly"] is True and probe["gaps"] == [] and probe["the_run_and_the_engine_run_the_same_rate"] is True
            continue
        assert probe["as_expected"] is True and probe["observed"] == tt.REAL_TEXT_EXPECTED[name] and probe["failures"] == [] and probe["replays_exactly"] is True, (name, probe["observed"])
        if not probe["the_run_and_the_engine_run_the_same_rate"]:
            assert probe["observed"]["says_it_no_longer_mirrors"] or probe["observed"]["outcomes"] == [ts.REFUSED], (name, "a run that no longer shows what the engine runs says so")
    assert real_text["all_as_expected"] is False and sorted(name for name, probe in real_text["probes"].items() if not probe["as_expected"]) == sorted(historical_defects)
    assert real_text["no_run_differs_from_the_engine_without_saying_so"] is True
    handed = {name: probe["as_the_mirror_hands_it_over"] for name, probe in real_text["probes"].items()}
    # how the mirror really hands these orders over: this is what the first audit missed
    assert handed["R1_STOP_THE_INFUSION"][1] == {"minute": 10, "kind": "infusion_adjustment", "action": {"type": "infusion_adjustment", "operation": "stop", "rate_value": None, "rate_units": None}, "receipt": {}}
    assert [item["action"]["operation"] for item in handed["R3_INCREASE_WITHOUT_UNITS_THEN_STOP"]] == ["start", "stop"], "the order without units is held before the engine: only the start and the stop are handed over"
    assert len(handed["R5_PRESSURE_TARGET"]) == 1 and handed["R5_PRESSURE_TARGET"][0]["action"]["operation"] == "start", "a pressure target no longer reaches the mirror at all: only the start is handed over"
    assert real_text["probes"]["R5_PRESSURE_TARGET"]["observed"]["engine_rate_at_the_end"] == 10.0 and real_text["probes"]["R5_PRESSURE_TARGET"]["observed"]["run_rate_at_the_end"] == 10.0
    assert handed["R6_WEIGHT_BASED_START"][0]["action"]["units"] == "mcg/kg/min" and real_text["probes"]["R6_WEIGHT_BASED_START"]["observed"]["writer"] is None
    assert handed["R7_STOP_THAT_CARRIES_A_RATE"][1]["action"] == {"type": "norepinephrine", "operation": "stop", "rate": 10.0, "units": "mcg/min"}, "a stop may carry a rate and units, and is a stop"
    assert real_text["probes"]["R3_INCREASE_WITHOUT_UNITS_THEN_STOP"]["gaps"] == [], "the order without units never reaches the mirror, so there is nothing to refuse"
    assert ts.order_disposition({"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": None}, {"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": "mcg/min"}) == (None, ts.GAP_NO_UNITS.format(operation="adjust")), "the belt and braces of the shadow: a rate without units is still refused as written"


def test_r3_a_refused_order_in_the_minute_of_a_valid_one_leaves_the_history_that_ran_before_that_minute():
    """MAJOR of the review: the rate ordered just before the refusal, in the same minute, was carried for the rest of the encounter though it never ran for one modelled interval."""
    point = vs.witness("CENTER_REFERENCE")
    alone = ts.map_orders([_event(5, "o1")], (), [], point)[0]
    events = [_event(5, "o1"), _event(12, "o2", "adjust", 20.0), _event(12, "bad", "adjust", 8.0, "mg/h"), _stop(15, "o4")]
    built, gaps = ts.map_orders(events, (), [], point)
    assert built == alone and [gap["order_id"] for gap in gaps] == ["o2", "bad", "o4"] and gaps[0]["why"] == ts.GAP_REPLACED.format(operation="adjust") and gaps[1]["why"].endswith(ts.NO_LONGER_MIRRORED)
    assert [(row["outcome"], row["replaced_within_its_minute"]) for row in ts.order_log(events, point)] == [(ts.STARTED, False), (ts.REPLACED, True), (ts.REFUSED, False), (ts.REFUSED, False)]
    built, gaps = ts.map_orders([_event(5, "o1"), _event(5, "bad", "adjust", 8.0, "mg/h")], (), [], point)
    assert built == () and [gap["order_id"] for gap in gaps] == ["o1", "bad"], "the start and the refusal in one minute: nothing ever ran"


def _random_stream(rng):
    """A stream of orders as a session could hand them over: minutes that never go back, several orders in a minute, valid and invalid ones, and orders that name no drug."""
    minute, out = rng.randrange(0, 4), []
    for index in range(rng.randrange(1, 9)):
        minute += rng.choice((0, 0, 1, 3))
        pick = rng.random()
        if pick < 0.12:
            out.append(_role(minute, f"r{index}", rng.choice(("stop", "adjust")), rng.choice((None, 20.0)), rng.choice((None, "mcg/min"))))
        elif pick < 0.24:
            out.append(_event(minute, f"n{index}", rng.choice(("adjust", "start", "continue", "titrate")), rng.choice((8.0, -1.0, None, 10 ** 400)), rng.choice(("mg/h", None, "mcg/kg/min", "mcg/min"))))
        elif pick < 0.44:
            out.append(_stop(minute, f"n{index}"))
        elif pick < 0.52:
            out.append(_event(minute, f"n{index}", "continue", None, None))
        else:
            out.append(_event(minute, f"n{index}", rng.choice(("start", "start", "adjust", "continue")), rng.choice((0.5, 5.0, 10.0, 10.0, 20.0))))
    return out


def test_r4_a_declared_order_never_becomes_a_carried_one_and_no_gap_goes_stale():
    """MAJOR of the review: the session's gaps only accumulate, and three orders arriving turn by turn left 'nothing to build' gaps beside the SAME orders reported as built. Now every order is
    carried or declared, never both, and what a prefix of the stream declares the whole stream still declares, word for word."""
    point = vs.witness("CENTER_REFERENCE")
    rng, streams = random.Random(435), [[_event(2, "a", "start", 5.0), _stop(2, "b"), _event(7, "c", "start", 10.0)]]       # the review's own case first
    streams += [_random_stream(rng) for _ in range(1500)]
    shapes = set()
    for stream in streams:
        recorded, declared_before = [], set()
        for cut in range(1, len(stream) + 1):
            built, gaps = ts.map_orders(stream[:cut], (), [], point)
            recorded += [gap for gap in gaps if gap not in recorded]                    # as ShadowPhysiologyRunner.contributors accumulates them
            writers = [item for item in built if isinstance(item, vs.Norepinephrine)]
            assert len(writers) <= 1 and len(built) == len(writers), "one writer of the kind, never two"
            carried = set(getattr(writers[0], "carried_order_ids", (writers[0].id,))) if writers else set()
            declared = {gap["order_id"] for gap in gaps}
            ours = {event.order_id for event in stream[:cut] if event.kind == "norepinephrine"}
            assert not carried & declared and carried | (declared & ours) == ours, "every order of the kind is carried or declared, never both and never neither"
            assert not carried & declared_before, "an order once declared is never carried afterwards"
            declared_before |= declared
            log = ts.order_log(stream[:cut], point)
            assert {row["order_id"] for row in log if row["carried"]} == carried and {row["order_id"] for row in log if not row["carried"]} == declared
            if writers:
                rebuilt = integration.from_spec(json.loads(json.dumps(writers[0].to_spec())))
                assert rebuilt == writers[0] and all(rebuilt.support_at(minute) >= 0.0 for minute in range(0, 40))
        built, gaps = ts.map_orders(stream, (), [], point)
        assert sorted(recorded, key=repr) == sorted(gaps, key=repr), "what the turns recorded is what the whole stream declares: nothing stale"
        shapes.add(tuple(row["outcome"] for row in ts.order_log(stream, point)))
    seen = {outcome for shape in shapes for outcome in shape}
    assert seen == set(ts.OUTCOMES) | set(ts.NOT_CARRIED) and len(shapes) > 150, "the streams reached every outcome an order can have"


def test_r5_malformed_input_is_declared_and_never_raised():
    """MINOR of the review: a rate too large to be a number, an action that is not a mapping and an order id that is not text raised instead of being declared."""
    point = vs.witness("CENTER_REFERENCE")
    start = {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"}
    for action in (None, "start 10", 5, ["start"], {"operation": "start", "rate": 10 ** 400, "units": "mcg/min"}, {"operation": {"a": 1}}, {"operation": "start", "rate": [1.0], "units": "mcg/min"},
                   {"operation": "start", "rate": 5.0, "units": ["mcg/min"]}, {"operation": "start", "rate": 5.0, "units": "mcg/min", "rate_mcg_min": "five"}, {**start, "type": 7}):
        rate, why = ts.order_disposition(action)
        assert rate is None and isinstance(why, str) and why, action
        events = [_event(5, "o1"), rs.MirroredAction("odd", 9, "norepinephrine", action, {}, 0.21), _stop(12, "o3")]
        built, gaps = ts.map_orders(events, (), [], point)
        assert [item.id for item in built] == ["o1"] and [gap["order_id"] for gap in gaps] == ["odd", "o3"] and [row["outcome"] for row in ts.order_log(events, point)] == [ts.STARTED, ts.REFUSED, ts.REFUSED]
    for receipt in (None, "a receipt", 5, ["x"]):                    # a receipt that is not a mapping is no receipt: the order stands on what it says
        assert ts.order_disposition(start, receipt) == (10.0, None)
    assert ts.order_disposition(start, {"operation": "start", "rate": 10, "units": "mcg/min"}) == (10.0, None), "a receipt that agrees changes nothing"
    assert ts.order_disposition({**start, "operation": "stop"}, {"operation": "stop", "rate": None, "units": None}) == (0.0, None)
    assert ts.order_disposition({"type": "norepinephrine", "operation": "continue", "rate": None, "units": None}) == (None, None), "a bare continuation: the rate ordered before it"
    assert ts.infusion_history([], point) == ((), (), ()) and ts.map_orders([], ("a-fluid",), [{"kind": "dopamine", "order_id": "x", "why": "w"}], point) == (("a-fluid",), [{"kind": "dopamine", "order_id": "x", "why": "w"}])


def test_r6_the_writer_checks_its_own_accounting_and_a_specification_cut_short_is_refused():
    """MINOR of the review: the writer validated only the (minute, rate) projection of its orders, so a mislabelled outcome was accepted, and a specification without its units or its writer's
    version was rebuilt with the defaults."""
    constants = _constants()
    good = dict(changes=((10, 10.0),), orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, ts.INCREASED)), **constants)
    assert ts.NorepinephrineRateHistory("o1", 2, 5.0, **good)
    bad = {"an outcome the rates do not give": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 10.0, ts.DECREASED))),
           "a first order that is not the start": dict(good, orders=(("o1", 2, 5.0, ts.INCREASED), ("o2", 10, 10.0, ts.INCREASED))),
           "a first order at another rate": dict(good, orders=(("o1", 2, 4.0, ts.STARTED), ("o2", 10, 10.0, ts.INCREASED))),
           "two orders in one minute": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 10, 7.0, ts.INCREASED), ("o3", 10, 10.0, ts.INCREASED))),
           "an order id that is not text": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), (7, 10, 10.0, ts.INCREASED))),
           "an empty order id": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("", 10, 10.0, ts.INCREASED))),
           "an idle order labelled as a change": dict(good, orders=(("o1", 2, 5.0, ts.STARTED), ("o2", 6, 5.0, ts.INCREASED), ("o3", 10, 10.0, ts.INCREASED)))}
    for label, fields in bad.items():
        with pytest.raises(CoreInvariantError):
            ts.NorepinephrineRateHistory("o1", 2, 5.0, **fields)
        assert label
    writer = ts.NorepinephrineRateHistory("o1", 2, 5.0, **good)
    spec = json.loads(json.dumps(writer.to_spec()))
    assert integration.from_spec(spec) == writer and ts.SPEC_NAMES == ("changes", "orders", "rate_units", "writer_version")
    for name in ts.SPEC_NAMES:
        with pytest.raises(CoreInvariantError, match=name):
            integration.from_spec({key: value for key, value in spec.items() if key != name})
    with pytest.raises(CoreInvariantError):
        integration.from_spec({**spec, "orders": [["o1", 2, 5.0, ts.STARTED], ["o2", 10, 10.0, ts.RESTARTED]]})
    with pytest.raises(TypeError):
        integration.from_spec({**spec, "target_map": 65})                              # nothing the writer does not know is read from a specification


def test_r7_the_rate_history_registers_again_where_the_registry_was_swapped(monkeypatch):
    """MINOR of the review: the registration made at import is lost where the registry is swapped for a while (a historical view of an earlier tree). The mapping asks again each time it builds."""
    point = vs.witness("CENTER_REFERENCE")
    writer = _writer(HISTORIES[0])
    spec = json.loads(json.dumps(writer.to_spec()))
    monkeypatch.setattr(integration, "_REGISTRY", {key: value for key, value in integration._REGISTRY.items() if key != ts.NorepinephrineRateHistory.type_name})
    with pytest.raises(ProvenanceError, match="no contributor type 'norepinephrine_rate_history'"):
        integration.from_spec(spec)
    built, _gaps = ts.map_orders([_event(2, "o1", "start", 5.0), _event(10, "o2", "adjust", 10.0)], (), [], point)
    assert integration._REGISTRY[ts.NorepinephrineRateHistory.type_name] is ts.NorepinephrineRateHistory and integration.from_spec(spec) == writer == built[0]
    ts.ensure_registered()
    ts.ensure_registered()
    assert integration._REGISTRY[ts.NorepinephrineRateHistory.type_name] is ts.NorepinephrineRateHistory and integration._REGISTRY["norepinephrine"] is vs.Norepinephrine


def test_r7b_the_cores_own_writer_is_registered_again_too_so_a_single_start_replays_after_a_view_lost_it(monkeypatch):
    """Found by the full certification, and NOT caused by this package (the same order fails on the base commit): a module-scoped historical view swaps the registry, a replay
    under it first imports the core's vascular_support module, the core's writer registers into the swapped registry, and when the view ends the live registry has lost
    'norepinephrine' for the rest of the process. A later tone run then built a writer its own artifact could not rebuild. The mapping now registers both writers it builds."""
    point = vs.witness("CENTER_REFERENCE")
    core = vs.Norepinephrine("o1", 5, 10.0, **_constants())
    spec = json.loads(json.dumps(core.to_spec()))
    monkeypatch.setattr(integration, "_REGISTRY", {key: value for key, value in integration._REGISTRY.items() if key not in ("norepinephrine", ts.NorepinephrineRateHistory.type_name)})
    with pytest.raises(ProvenanceError, match="no contributor type 'norepinephrine'"):
        integration.from_spec(spec)                                    # the state the view leaves behind: the module is imported, so from_spec's own import does not register it again
    built, gaps = ts.map_orders([_event(5, "o1")], (), [], point)
    assert built == (core,) and gaps == [] and integration._REGISTRY["norepinephrine"] is vs.Norepinephrine and integration.from_spec(spec) == core
    # the whole path, as the failing test ran it: a tone run of a registered family replays exactly with the registry in that state
    monkeypatch.setattr(integration, "_REGISTRY", {key: value for key, value in integration._REGISTRY.items() if key not in ("norepinephrine", ts.NorepinephrineRateHistory.type_name)})
    run = tt._edge_run((tt.event(5, "start", 10.0),))
    assert run["replay_equal"] is True and run["failures"] == [] and [type(item).type_name for item in tt.writers_of(run)] == ["norepinephrine"]


@pytest.mark.parametrize("name", vs.WITNESS_NAMES)
def test_r8_the_support_is_the_first_order_equation_integrated_without_the_writers_arithmetic(name):
    """NOTE of the review: the harness's 'independent' closed form is a transcription of the writer's. This is not: dx/dt = (target - x) / tau by Runge-Kutta steps, no exponential taken."""
    constants = _constants(name)
    half, onset, offset = constants["half_effect_rate_mcg_min"], constants["onset_tau_min"], constants["offset_tau_min"]
    for history in HISTORIES:
        writer, end = _writer(history, name), history[-1][0] + 30
        x, steps = 0.0, 400
        h = 1.0 / steps
        slope = lambda value, target: (target - value) / (onset if target > value else offset)
        for minute in range(1, end + 1):
            target = next((rate for at, rate in reversed(history) if at < minute), 0.0) / half
            for _ in range(steps):
                k1 = slope(x, target)
                k2 = slope(x + 0.5 * h * k1, target)
                k3 = slope(x + 0.5 * h * k2, target)
                k4 = slope(x + h * k3, target)
                x += h * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
            assert abs(writer.support_at(minute) - x) <= 1e-7, (name, history, minute)
    if name == "CENTER_REFERENCE":
        assert all(max(abs(a - b) for a, b in zip(tt.closed_form(history, 60), tt.integrated(history, 60))) <= 1e-7 for history in HISTORIES)


def test_r9_what_direction_means_a_decrease_before_the_steady_effect_still_rises_but_never_above_the_run_without_it():
    """NOTE of the review: 'never rises on a decrease' is false as a statement about orders. What holds: the contribution moves toward the rate ordered and never past it, and against the same
    history WITHOUT its last order it is never above after a decrease or a stop and never below after an increase or a restart."""
    early = _writer(((0, 10.0), (1, 6.0)))
    assert early.support_at(1) < early.support_at(8) < 0.6 and all(b >= a for a, b in zip([early.support_at(m) for m in range(0, 30)], [early.support_at(m) for m in range(1, 31)])), \
        "a decrease ordered before the steady effect keeps rising, toward the lower rate"
    rng = random.Random(9)
    for name in vs.WITNESS_NAMES:
        half = _constants(name)["half_effect_rate_mcg_min"]
        for _ in range(300):
            minutes = sorted(rng.sample(range(0, 30), rng.randrange(2, 6)))
            rates = [rng.choice((0.5, 2.0, 5.0, 10.0, 20.0))]
            for _minute in minutes[1:]:
                rates.append(rng.choice([rate for rate in (0.0, 0.5, 2.0, 5.0, 10.0, 20.0) if rate != rates[-1]]))
            history = tuple(zip(minutes, rates))
            with_it = _writer(history, name)
            without = _writer(history[:-1], name) if len(history) > 2 else vs.Norepinephrine("o1", history[0][0], history[0][1], **_constants(name))
            sign = 1.0 if rates[-1] > rates[-2] else -1.0
            target = rates[-1] / half
            series = [(with_it.support_at(minute), without.support_at(minute)) for minute in range(0, minutes[-1] + 40)]
            assert all(a == b for a, b in series[:minutes[-1] + 1]) and all(sign * (a - b) >= 0.0 for a, b in series) and any(sign * (a - b) > 0.0 for a, b in series), (name, history)
            after = [a for a, _b in series[minutes[-1]:]]
            low, high = min(after[0], target), max(after[0], target)
            # the value carried between segments never passes the target (the bound is held exactly); what is READ is on the writers' grid, so it may sit within one quantum of it
            assert all(low - QUANTUM <= value <= high + QUANTUM for value in after), (name, history, "between where it was at the order and the ordered rate's steady support, never past it")
            assert all((b - a) * (target - after[0]) >= 0.0 for a, b in zip(after, after[1:])), (name, history, "it moves toward the rate ordered, never away from it")


# ---------------------------------------------------------------------------------------------------------------------------------------- the other families and the negative control
@pytest.fixture(scope="module")
def families():
    return tt.multifamily()


def test_f1_the_same_orders_give_the_same_support_in_every_family_and_nothing_certified_moved(families):
    assert families["no_regression"] is True and families["the_support_is_the_same_in_every_family"] is True and families["pump_limited_use_is_not_promoted"] is True
    assert set(families["families"]) == {"gi_bleed", "pulmonary_embolism", "acs", "pulmonary_edema"} and families["low_tone_synthetic_probe"]["as_expected"] is True
    for family, item in families["families"].items():
        assert item["orders"] == [ts.STARTED, ts.INCREASED, ts.DECREASED, ts.STOPPED] and item["writers"] == ["norepinephrine_rate_history"] and item["gaps"] == [] and item["failures"] == [], family
        assert item["replays_exactly"] and item["support_is_the_closed_form"] and all(item["untouched_state"].values()), family
        assert item["no_tone_action_the_trajectory_is_unchanged"] is True, (family, "with no order nothing reads differently")
        certified = item["the_certified_single_start_is_unchanged"]
        assert certified["writer"] == ["norepinephrine"] and certified["equal_to_the_certified_probe_record"] is True, (family, "the single start the faculty reviewed is the same, number by number")
        assert item["pump_limited"] is (family in ("acs", "pulmonary_edema")) and item["educational_promotion"].startswith("BLOCKED" if item["pump_limited"] else "NOT_CLAIMED")
    low = families["low_tone_synthetic_probe"]
    assert low["support_is_the_closed_form"] and low["ordering_as_the_rates"] and low["the_certified_single_start_probe_is_unchanged"] and low["pressure_never_above_arrival"]


def test_n1_the_negative_control_is_the_trajectory_the_faculty_rejected_with_its_physiology_untouched():
    record = tt.build_negative_control()
    assert record["scenario_id"] == "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI" and record["classification"] == record["record_type"] == "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO"
    assert record["mechanism_failure"] is False and record["human_evidence"]["overall"] == "REJECT" and record["human_evidence"]["first_pass"] == {"Q1": "Expected", "Q2": "Plausible", "Q3": "Too large", "Q4": "Incoherent", "Q5": "Yes"}
    assert "not a mechanism failure" in record["human_evidence"]["the_reject_is_not_converted"] and record["earlier_classification"]["classification"] == "INAPPROPRIATE_INTERVENTION_CONTEXT"
    physiology = record["physiology"]
    assert physiology["altered"] is False and physiology["the_trajectory_recomputed_now_is_the_one_the_faculty_reviewed"] is True and physiology["writer"] == ["norepinephrine"]
    assert physiology["displayed_pressure"]["at_the_order"] == {"minute": 5, "sbp": 218, "dbp": 116, "map": 150} and physiology["displayed_pressure"]["at_the_end"]["sbp"] == 260
    assert physiology["displayed_pressure"]["without_the_order_at_the_end"]["sbp"] == 218, "a physiologically understandable pressor response"
    assert record["use"] == {**record["use"], "built_into_the_application": False, "resident_visible": False, "scored": False, "norepinephrine_made_unavailable": False}
    assert "Physiologic response is not appropriate management." in record["purpose"] and "a mechanism failure" in record["is_not"] and "a change of the case's physiology" in record["is_not"]
