"""Phase 2 shadow core, P2B-2: the core's inputs come from the final Phase-1 Contracts v2.

The contracts are built with Phase 1's own constructors from Phase-0 shaped records, the
way the order pipeline builds them. The adapter must keep the ledger's identity and
timing, account for every order, and refuse what the core does not model.
"""
import pytest

import family_engine
from contracts_v2 import events, fates, orders, timing
from clinical_core.contracts_input import (ContractInputError, UnsupportedContract, adapt, logistics_from_events)
from clinical_core.interventions import Crystalloid, Oxygen, PackedRedCells

TABLES = {"gi_bleed": family_engine.GI_BLEED, "devices": family_engine._DEVICES}


def action(order_id, submission, **fields):
    tagged = {**fields, "_order_id": order_id, "_submission_id": submission}
    return orders.from_reader_action(tagged, submission_id=submission, index=0)


def receipt(order_id, submission, kind, fate="EXECUTED", minute=0, **extra):
    return fates.from_legacy_order({"order_id": order_id, "submission_id": submission, "class": kind, "fate": fate,
                                    "executed_at_min": minute if fate == "EXECUTED" else None, **extra})


def turn_time(*items, interrupted=None, before=0):
    return timing.from_legacy_turn({"decision_time_min": before, "response_time_min": before + 1,
                                    "interrupted": interrupted,
                                    "orders": [{"order_id": order_id, "written_at_min": before,
                                                "executed_at_min": minute, "timing": None}
                                               for order_id, minute in items]})


def event_turn(*payloads, interrupted=None):
    return events.from_legacy_turn({"events": list(payloads), "interrupted": interrupted})


SALINE = {"type": "fluid", "volume_ml": 1000.0, "fluid_type": "normal saline", "route": "IV"}


def test_ids_submissions_and_minutes_come_from_the_ledger():
    acts = [action("t3:0", "t3", **SALINE), action("t3:1", "t3", type="ppi", agent="pantoprazole", dose_mg=80.0,
                                                    route="IV")]
    rec = [receipt("t3:0", "t3", "fluid", minute=3), receipt("t3:1", "t3", "ppi", minute=3)]
    adapted = adapt(acts, rec, [turn_time(("t3:0", 3), ("t3:1", 3), before=3)], **TABLES)
    ids = {contributor.id for contributor in adapted.contributors}
    assert ids == {"t3:0", "t3:1"}
    for binding in adapted.bindings:
        assert binding.submission_id == "t3" and binding.executed_at_min == 3
        assert binding.source_key == f"intervention:{binding.order_id}" and binding.start_minute == 3
    saline = next(c for c in adapted.contributors if isinstance(c, Crystalloid))
    assert saline.start_minute == 3 and saline.volume_ml == 1000.0


def test_an_order_carried_forward_keeps_its_identity_and_runs_once():
    """Held in t1, released in t3: one intervention, written in t1, starting when it ran."""
    acts = [action("t1:0", "t1", **SALINE), action("t1:0", "t1", **SALINE)]
    rec = [receipt("t1:0", "t1", "fluid", fate="HELD_REASONING"), receipt("t1:0", "t1", "fluid", minute=7)]
    adapted = adapt(acts, rec, **TABLES)
    assert [c.id for c in adapted.contributors] == ["t1:0"] and adapted.contributors[0].start_minute == 7
    assert [(b.order_id, b.submission_id, b.fate) for b in adapted.bindings] == [("t1:0", "t1", "EXECUTED")]


def test_a_carried_forward_order_cannot_change_what_it_is():
    acts = [action("t1:0", "t1", **SALINE), action("t1:0", "t1", **{**SALINE, "volume_ml": 2000.0})]
    with pytest.raises(ContractInputError):
        adapt(acts, [receipt("t1:0", "t1", "fluid")], **TABLES)


def test_a_second_timed_bag_queues_behind_the_first_and_a_stop_names_itself():
    timed = {**SALINE, "administration_duration_min": 15.0}
    acts = [action("t0:0", "t0", **timed), action("t0:1", "t0", **timed),
            action("t5:0", "t5", type="fluid", operation="stop", fluid_type=None)]
    rec = [receipt("t0:0", "t0", "fluid"), receipt("t0:1", "t0", "fluid"), receipt("t5:0", "t5", "fluid", minute=5)]
    adapted = adapt(acts, rec, **TABLES)
    first, second = adapted.contributors
    assert (first.start_minute, second.start_minute) == (0.0, 15.0)
    assert first.stop_minute == second.stop_minute == 5 and first.stopped_by == second.stopped_by == "t5:0"
    stop = adapted.binding("t5:0")
    assert stop.disposition == "core_stop" and stop.affects == ("t0:0", "t0:1")


def test_a_stop_closes_a_bag_so_the_next_one_does_not_queue_behind_it():
    timed = {**SALINE, "administration_duration_min": 30.0}
    acts = [action("t0:0", "t0", **timed), action("t5:0", "t5", type="fluid", operation="stop", fluid_type=None),
            action("t6:0", "t6", **timed)]
    rec = [receipt("t0:0", "t0", "fluid"), receipt("t5:0", "t5", "fluid", minute=5),
           receipt("t6:0", "t6", "fluid", minute=6)]
    assert adapt(acts, rec, **TABLES).contributors[1].start_minute == 6.0


def test_blood_and_oxygen_take_the_engine_s_rules():
    acts = [action("t0:0", "t0", type="blood", units=2.0, administration_duration_min=60.0),
            action("t0:1", "t0", type="oxygen", device="nasal cannula", flow_lpm=4.0),
            action("t2:0", "t2", type="oxygen", device="non-rebreather mask", flow_lpm=15.0)]
    rec = [receipt("t0:0", "t0", "blood"), receipt("t0:1", "t0", "oxygen"), receipt("t2:0", "t2", "oxygen", minute=2)]
    adapted = adapt(acts, rec, **TABLES)
    oxygen = [c for c in adapted.contributors if isinstance(c, Oxygen)]
    assert [round(o.fio2, 6) for o in oxygen] == [0.37, 0.85]
    blood = next(c for c in adapted.contributors if isinstance(c, PackedRedCells))
    assert blood.units == 2.0 and blood.duration_min == 60.0


def test_every_order_ends_in_exactly_one_binding():
    acts = [action("t0:0", "t0", **SALINE), action("t0:1", "t0", type="reassessment", delay_min=1.0),
            action("t0:2", "t0", type="consult", service="gastroenterology"),
            action("t0:3", "t0", **SALINE)]
    rec = [receipt("t0:0", "t0", "fluid"), receipt("t0:1", "t0", "reassessment"),
           receipt("t0:2", "t0", "consult"), receipt("t0:3", "t0", "fluid", fate="DUPLICATE_IGNORED"),
           receipt("t0:w5000", "t0", "unread_words", fate="UNRECOGNIZED")]
    adapted = adapt(acts, rec, **TABLES)
    assert [(b.order_id, b.disposition) for b in adapted.bindings] == [
        ("t0:0", "core_contributor"), ("t0:1", "no_physiology"), ("t0:2", "no_physiology"),
        ("t0:3", "not_acted_by_engine"), ("t0:w5000", "not_acted_by_engine")]
    assert [c.id for c in adapted.contributors] == ["t0:0"]


@pytest.mark.parametrize("fate", ["HELD_CLARIFICATION", "HELD_REASONING", "SCHEDULED"])
def test_a_future_or_conditional_order_is_refused_not_given_now(fate):
    with pytest.raises(UnsupportedContract):
        adapt([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "fluid", fate=fate)], **TABLES)


@pytest.mark.parametrize("acts,rec", [
    # A fate the core does not follow, a limitation, an order without a fate, a fate without what ran.
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "fluid", fate="CANCELLED")]),
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "fluid", limitation="unsupported_future_execution")]),
    ([action("t0:0", "t0", **SALINE)], []),
    ([], [receipt("t0:0", "t0", "fluid")]),
    # Classes, fields and products the core does not model.
    ([action("t0:0", "t0", type="vasopressor", agent="norepinephrine")], [receipt("t0:0", "t0", "vasopressor")]),
    ([action("t0:0", "t0", **{**SALINE, "after_result": "lactate"})], [receipt("t0:0", "t0", "fluid")]),
    ([action("t0:0", "t0", **{**SALINE, "fluid_type": "albumin"})], [receipt("t0:0", "t0", "fluid")]),
    ([action("t0:0", "t0", **{**SALINE, "route": "PO"})], [receipt("t0:0", "t0", "fluid")]),
    ([action("t0:0", "t0", **{**SALINE, "rate_ml_h": 125.0})], [receipt("t0:0", "t0", "fluid")]),
    ([action("t0:0", "t0", type="fluid", operation="adjust", fluid_type="normal saline")],
     [receipt("t0:0", "t0", "fluid")]),
    ([action("t0:0", "t0", type="oxygen", device="high-flow nasal cannula", flow_lpm=40.0)],
     [receipt("t0:0", "t0", "oxygen")]),
])
def test_what_the_core_does_not_model_is_refused(acts, rec):
    with pytest.raises(UnsupportedContract):
        adapt(acts, rec, **TABLES)


@pytest.mark.parametrize("acts,rec,times", [
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t1", "fluid")], ()),
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "fluid", minute=2)], (turn_time(("t0:0", 0)),)),
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "fluid", minute=1.5)], ()),
    ([action("t0:0", "t0", **SALINE)], [receipt("t0:0", "t0", "blood")], ()),
])
def test_contracts_that_contradict_each_other_are_refused(acts, rec, times):
    with pytest.raises(ContractInputError):
        adapt(acts, rec, times, **TABLES)


def test_an_interrupted_turn_is_refused():
    with pytest.raises(UnsupportedContract):
        adapt([], [], [turn_time(interrupted={"kind": "cardiac_arrest"})], **TABLES)
    with pytest.raises(UnsupportedContract):
        logistics_from_events([event_turn(interrupted={"kind": "cardiac_arrest"})])


ENDOSCOPY = {"kind": "endoscopy", "cause_class": "LOGISTIC", "minute": 60, "label": "endoscopy performed"}


def test_the_endoscopy_comes_from_its_logistic_event():
    built, not_consumed = logistics_from_events([event_turn(ENDOSCOPY, {"kind": "shock", "cause_class": "PHYSIOLOGY",
                                                                        "minute": 12})])
    assert [(item.id, item.completes_at_minute) for item in built] == [("gastroenterology_endoscopy", 60)]
    assert not_consumed == ({"kind": "shock", "cause_class": "PHYSIOLOGY", "minute": 12},)


@pytest.mark.parametrize("payloads", [
    [{"kind": "surgery", "cause_class": "LOGISTIC", "minute": 30}],
    [{"kind": "rebleed", "cause_class": "SCRIPTED_NATURAL_HISTORY", "minute": 30}],
    [ENDOSCOPY, ENDOSCOPY],
    [{**ENDOSCOPY, "minute": None}],
])
def test_event_inputs_the_core_does_not_model_are_refused(payloads):
    with pytest.raises(ContractInputError):
        logistics_from_events([event_turn(*payloads)])


def test_the_contracts_given_are_not_changed():
    acts = [action("t0:0", "t0", **{**SALINE, "administration_duration_min": 20.0})]
    rec = [receipt("t0:0", "t0", "fluid")]
    before = ([a.as_record() for a in acts], [r.as_record() for r in rec])
    adapt(acts, rec, **TABLES)
    assert ([a.as_record() for a in acts], [r.as_record() for r in rec]) == before


# Hardening found by the adversarial review of the P2B adapters ------------------------

def test_a_carried_forward_order_queues_where_it_actually_ran():
    """t0:0 is held, t0:1 runs at minute 0, t0:0 runs at minute 3: the bag that ran first is first in line."""
    timed = {**SALINE, "administration_duration_min": 30.0}
    acts = [action("t0:0", "t0", **timed), action("t0:1", "t0", **timed), action("t0:0", "t0", **timed)]
    rec = [receipt("t0:0", "t0", "fluid", fate="HELD_REASONING"), receipt("t0:1", "t0", "fluid"),
           receipt("t0:0", "t0", "fluid", minute=3)]
    starts = {c.id: c.start_minute for c in adapt(acts, rec, **TABLES).contributors}
    assert starts == {"t0:1": 0.0, "t0:0": 30.0}


def test_a_carried_forward_untimed_order_shares_the_line_in_execution_order():
    acts = [action("t0:0", "t0", **SALINE), action("t0:1", "t0", **SALINE), action("t0:0", "t0", **SALINE)]
    rec = [receipt("t0:0", "t0", "fluid", fate="HELD_REASONING"), receipt("t0:1", "t0", "fluid"),
           receipt("t0:0", "t0", "fluid", minute=2)]
    ahead = {c.id: c.queued_ahead_ml for c in adapt(acts, rec, **TABLES).contributors}
    assert ahead == {"t0:1": 0.0, "t0:0": 900.0}


@pytest.mark.parametrize("later", [
    {"fate": "EXECUTED", "minute": 5},
    {"fate": "DUPLICATE_IGNORED"},
    {"fate": "HELD_REASONING"},
])
def test_an_executed_order_cannot_be_reported_again_as_something_else(later):
    acts = [action("t0:0", "t0", **SALINE)]
    rec = [receipt("t0:0", "t0", "fluid"), receipt("t0:0", "t0", "fluid", **later)]
    with pytest.raises(ContractInputError):
        adapt(acts, rec, **TABLES)


def test_the_same_executed_receipt_seen_twice_is_one_order():
    acts = [action("t0:0", "t0", **SALINE)]
    rec = [receipt("t0:0", "t0", "fluid"), receipt("t0:0", "t0", "fluid")]
    assert [c.id for c in adapt(acts, rec, **TABLES).contributors] == ["t0:0"]
