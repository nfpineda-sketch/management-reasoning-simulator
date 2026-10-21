"""Phase 2 shadow core, P2B-3: the core's results in Contracts v2 shapes, as shadow only.

The records go through Phase 1's own constructors and equivalence checks, keep the ledger
identity and the core's provenance, never build a fate or a receipt, never carry what a
resident sees, and mark what the core does not model.
"""
import json
from copy import deepcopy

import pytest

import family_engine
from contracts_v2 import events, fates, observations, orders, trace
from clinical_core import Anchors, RhythmState, SourceKind, derive, run
from clinical_core.contracts_input import adapt
from clinical_core.contracts_output import (RESIDENT_VISIBLE_KEYS, SHADOW_NAMESPACE, ShadowOutputError,
                                            check_shadow_payload, shadow_events, shadow_observation, shadow_trace)
from clinical_core.modules import GIHaemorrhage
from clinical_core.modules.rhythm_events import ScriptedRhythmEvent

ARRIVAL = Anchors(case_id="gi_bleed_72f", sbp=98.0, dbp=62.0, hr=112.0, spo2=96.0, respiratory_rate=24.0, crt_s=4.0,
                  lactate=3.4, hb=6.4, glucose=130.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(112.0),
                  consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.009, 0.8, 0.1)
TABLES = {"gi_bleed": family_engine.GI_BLEED, "devices": family_engine._DEVICES}


def _action(order_id, submission, **fields):
    tagged = {**fields, "_order_id": order_id, "_submission_id": submission}
    return orders.from_reader_action(tagged, submission_id=submission, index=0)


def _receipt(order_id, submission, kind, minute=0):
    return fates.from_legacy_order({"order_id": order_id, "submission_id": submission, "class": kind,
                                    "fate": "EXECUTED", "executed_at_min": minute})


@pytest.fixture(scope="module")
def shadow():
    acts = (_action("t0:0", "t0", type="blood", units=2.0, administration_duration_min=60.0),
            _action("t0:1", "t0", type="ppi", agent="pantoprazole", dose_mg=80.0, route="IV"),
            _action("t0:2", "t0", type="consult", service="gastroenterology"),
            _action("t4:0", "t4", type="fluid", volume_ml=1000.0, fluid_type="normal saline", route="IV"))
    rec = (_receipt("t0:0", "t0", "blood"), _receipt("t0:1", "t0", "ppi"), _receipt("t0:2", "t0", "consult"),
           _receipt("t4:0", "t4", "fluid", minute=4))
    logistic = events.from_legacy_turn({"events": [
        {"kind": "endoscopy", "cause_class": "LOGISTIC", "minute": 60},
        {"kind": "hemorrhagic_shock", "cause_class": "PHYSIOLOGY", "minute": 20}], "interrupted": None})
    before = deepcopy(([a.as_record() for a in acts], [r.as_record() for r in rec], logistic.as_record()))
    adapted = adapt(acts, rec, (), (logistic,), **TABLES)
    trajectory = run(ARRIVAL, (BLEED,) + adapted.contributors, 75)
    return {"acts": acts, "rec": rec, "logistic": logistic, "before": before, "adapted": adapted,
            "trajectory": trajectory}


def test_shadow_events_are_an_event_interruption_v2_that_round_trips(shadow):
    contract = shadow_events(shadow["trajectory"])
    events.assert_shadow_equivalent(contract, {"events": [e.payload for e in contract.events], "interrupted": None})
    rebuilt = events.from_legacy_turn(json.loads(json.dumps(contract.as_record())))
    assert rebuilt.legacy_projection() == contract.legacy_projection() and contract.interrupted is None
    assert [(e.payload["kind"], e.minute, e.payload["source_key"]) for e in contract.events] == [
        ("source_controlled", 60, "disease_module:gi_haemorrhage"),
        ("procedure_completed", 60, "logistic_process:gastroenterology_endoscopy")]
    assert all(e.payload["namespace"] == SHADOW_NAMESPACE and e.payload["authoritative"] is False
               for e in contract.events)
    assert shadow_events(shadow["trajectory"], minutes=range(0, 60)).events == ()


def test_a_shadow_observation_is_an_observation_v2_of_raw_numbers(shadow):
    trajectory = shadow["trajectory"]
    snapshot = shadow_observation(trajectory, 30)
    assert observations.shadow_from_legacy_turn({"observation_snapshot": snapshot.payload}) == snapshot
    assert (snapshot.minute, snapshot.arrested, snapshot.arrest_minute) == (30, False, None)
    assert snapshot.payload["derived"] == derive(trajectory.states[30], ARRIVAL, trajectory.profile).to_dict()
    assert snapshot.payload["channels"]["hb"] == trajectory.states[30].hb
    with pytest.raises(ShadowOutputError):
        shadow_observation(trajectory, 76)


def test_an_arrest_is_shown_as_an_explicit_terminal_state():
    trajectory = run(ARRIVAL, (BLEED, ScriptedRhythmEvent("vf", 5, RhythmState.vf(), "not_preventable")), 10)
    snapshot = shadow_observation(trajectory, 10)
    assert snapshot.arrested is True and snapshot.arrest_minute == 5
    assert snapshot.payload["derived"]["sbp"] is None and snapshot.payload["derived"]["consciousness_level"] == 3


def test_the_shadow_trace_round_trips_and_keeps_the_ledger_identity(shadow):
    contract = shadow_trace(shadow["trajectory"], shadow["adapted"])
    assert trace.shadow_from_legacy_trace(json.loads(json.dumps(contract.payload))).payload == contract.payload
    assert [o["order_id"] for o in contract.orders] == ["t0:0", "t0:1", "t0:2", "t4:0"]
    assert contract.submission == {"submission_ids": ["t0", "t4"], "order_ids": ["t0:0", "t0:1", "t0:2", "t4:0"]}
    cited = {o["order_id"]: o["cited_fate"] for o in contract.orders}
    assert cited == {r.order_id: r.fate for r in shadow["rec"]}


def test_provenance_runs_from_each_order_to_each_change(shadow):
    contract = shadow_trace(shadow["trajectory"], shadow["adapted"])
    bound = {o["order_id"]: o for o in contract.orders}
    changed = {delta["source"]["id"] for minute in contract.payload["minutes"] for delta in minute["deltas"]
               if delta["source"]["kind"] == SourceKind.INTERVENTION.value}
    assert changed == {"t0:0", "t4:0"}
    for order_id in changed:
        assert bound[order_id]["disposition"] == "core_contributor"
        assert bound[order_id]["source_key"] == f"intervention:{order_id}"
    assert bound["t0:1"]["source_key"] == "intervention:t0:1", "a PPI acts through the bleeding it modulates"
    assert bound["t0:2"]["disposition"] == "no_physiology"


def test_no_fate_or_receipt_is_manufactured_and_nothing_a_resident_sees_is_produced(shadow):
    trajectory, adapted = shadow["trajectory"], shadow["adapted"]
    payloads = [shadow_trace(trajectory, adapted).payload, shadow_observation(trajectory, 0).payload,
                *[e.payload for e in shadow_events(trajectory).events]]
    for payload in payloads:
        text = json.dumps(payload)
        assert '"fate"' not in text and '"receipt' not in text
        for key in RESIDENT_VISIBLE_KEYS:
            assert f'"{key}"' not in text, key


@pytest.mark.parametrize("change", [
    {"visible": {"sbp": 90}}, {"orders": [{"label": "Normal saline started"}]}, {"receipt": "Given"},
    {"authoritative": True}, {"namespace": "phase0"}, {"lactate": float("nan")}])
def test_a_payload_that_could_pass_for_authoritative_or_visible_is_refused(shadow, change):
    payload = {**shadow_observation(shadow["trajectory"], 0).payload, **change}
    with pytest.raises(ShadowOutputError):
        check_shadow_payload(payload)


def test_what_the_core_does_not_model_is_marked(shadow):
    limitations = shadow_trace(shadow["trajectory"], shadow["adapted"]).limitations
    assert {"shadow_only", "turn_interruption_not_modelled"} <= {item["kind"] for item in limitations}
    assert {"kind": "legacy_event_not_consumed", "event": "hemorrhagic_shock", "cause_class": "PHYSIOLOGY",
            "minute": 20} in limitations


def test_a_binding_to_a_contributor_that_did_not_run_is_refused(shadow):
    without_saline = run(ARRIVAL, tuple(c for c in (BLEED,) + shadow["adapted"].contributors if c.id != "t4:0"), 10)
    with pytest.raises(ShadowOutputError):
        shadow_trace(without_saline, shadow["adapted"])


def test_the_authoritative_records_are_not_changed(shadow):
    shadow_trace(shadow["trajectory"], shadow["adapted"])
    shadow_events(shadow["trajectory"])
    after = ([a.as_record() for a in shadow["acts"]], [r.as_record() for r in shadow["rec"]],
             shadow["logistic"].as_record())
    assert after == shadow["before"]
