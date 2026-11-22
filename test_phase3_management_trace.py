"""P3-503 to P3-514: the END-TO-END MANAGEMENT TRACE of the GI development encounter with live pressure and manual norepinephrine authority (FD-MTRACE-01 to FD-MTRACE-10).

TEST-SIDE. What is defended, in order:

* A  the trace module alone (pure): the encounter definition, provenance, the resident's reasoning never invented, the boundary exits, claims the model does not support, tampering;
* B  the ten paths through the LIVE development authority (both GI cases): every pressure is a committed authority minute under the norepinephrine grant and the two ratified snapshots, different sequences give
     different trajectories, the same sequence gives the same result, the causal ordering the faculty named holds, the boundary is reached as defined, serialization and re-extraction give the same trace;
* C  the source-control boundary and the educational-safety attacks (P3-513);
* D  the stored review set: it is the live regeneration, it is pinned, its items carry nothing of the mechanism, Q6 is asked, the proposed categories and the limitations appear only in the final summary;
* E  the launcher's hold (after the earlier holds; the operator's switch releases it).
"""
import json
import re
from pathlib import Path

import pytest

import development_management_trace as mt
import faculty_management_review as fmr
import faculty_management_review_ui as fmu
import faculty_review_ui as launcher
import faculty_trajectory_review as ftr
import test_gi_management_trace_paths as tp

pytestmark = pytest.mark.ordinary_configuration
ROOT = Path(__file__).resolve().parent
NE_GRANT = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"
PRESSURE_SNAPSHOT = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"
TONE_SNAPSHOT = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1"


# ============================================================================================================================================
# A. the trace module alone
# ============================================================================================================================================
def _turn(n, decision, response, orders, *, reasoning=None, events=(), source=mt.SCRIPTED, text=None, terminal=False):
    return {"text": text or f"turn {n}", "decision_minute": decision, "response_minute": response, "executed": True, "terminal_locked": terminal, "orders": list(orders), "events": list(events),
            "reasoning": dict(reasoning or {}), "text_source": source}


def _order(kind, *, canonical=None, rate=None, fate="EXECUTED", delay=None):
    return {"order_id": f"o-{kind}-{rate}", "class": kind, "canonical": canonical or kind, "span": canonical or kind, "rate": rate, "fate": fate, "reason": "executed",
            "timing": {"delay_min": delay} if delay is not None else None}


def _artifact(points, *, halted=False):
    return {"minutes": [{"minute": minute, "committed": ["dbp", "map", "sbp"], "outcome": "COMMITTED", "written_candidate": {"sbp": s, "dbp": d, "map": m}, "candidate_digest": f"c{minute}",
                         "grant_id": NE_GRANT, "snapshot_id": PRESSURE_SNAPSHOT} for minute, (s, d, m) in points.items()],
            "grant": {"grant_id": NE_GRANT, "fingerprint": "f"}, "snapshot_id": PRESSURE_SNAPSHOT, "norepinephrine_authority": {"tone_configuration": {"snapshot_id": TONE_SNAPSHOT}},
            "halted": halted, "halt_reason": "COLLAPSE_BOUNDARY_REACHED" if halted else "", "artifact_digest": "a", "case_id": "gi_bleed_57m"}


ARRIVAL = {"sbp": 88, "dbp": 54, "map": 65}


def test_a1_the_encounter_definition_is_data_with_its_own_digest_and_the_boundary_is_the_faculty_s():
    definition = mt.encounter_definition()
    body = {key: value for key, value in definition.items() if key != "definition_digest"}
    assert definition["definition_digest"] == mt.digest(body)
    assert definition["horizon_min"] == 120 and definition["horizon_provenance"] == mt.AUTHORED and definition["boundary_provenance"] == mt.FACULTY_DEFINED
    assert [exit_["id"] for exit_ in definition["exits"]] == list(mt.EXITS) and definition["cases"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert set(mt.PROVENANCE) == {"OBSERVED", "AUTHORED", "MODEL_DERIVED", "FACULTY_DEFINED", "RESIDENT_EXPRESSED", "UNKNOWN"}
    with pytest.raises(ValueError):
        mt.field(1, "GUESSED")


def test_a2_a_resident_reasoning_never_expressed_is_not_expressed_and_one_expressed_is_kept_exactly():
    silent = mt.extract([_turn(1, 0, 15, [_order("fluid"), _order("reassessment", delay=15)])], _artifact({15: (94, 58, 70)}), ARRIVAL)
    step = silent["steps"][0]
    assert [step[part]["resident"]["value"] for part in ("priority", "expected", "reassessment")] == [mt.NOT_EXPRESSED] * 3
    reasoning = {"management_priority": "Restore volume first.", "expected_effect": "A higher pressure within 15 minutes.", "reassessment_target": "Pressure in 15 minutes."}
    spoken = mt.extract([_turn(1, 0, 15, [_order("fluid")], reasoning=reasoning, source=mt.PAGE, text="Give fluid.")], _artifact({15: (94, 58, 70)}), ARRIVAL)
    step = spoken["steps"][0]
    assert step["priority"]["resident"] == {"value": "Restore volume first.", "provenance": mt.RESIDENT_EXPRESSED, "source": "reasoning.management_priority"}
    assert step["expected"]["resident"]["value"] == "A higher pressure within 15 minutes." and step["reassessment"]["resident"]["value"] == "Pressure in 15 minutes."
    assert step["action"]["text"] == {"value": "Give fluid.", "provenance": mt.RESIDENT_EXPRESSED, "source": mt.PAGE}
    assert mt.trace_problems(spoken, [_turn(1, 0, 15, [_order("fluid")], reasoning=reasoning, source=mt.PAGE, text="Give fluid.")]) == []


def test_a3_a_scenario_priority_is_authored_and_stored_apart_from_the_resident_s():
    trace = mt.extract([_turn(1, 0, 15, [_order("fluid")])], _artifact({15: (94, 58, 70)}), ARRIVAL, scenario={"id": "MT-X", "priorities": {1: "Restore volume."}, "category": "REASONABLE"})
    step = trace["steps"][0]
    assert step["priority"]["scenario"]["provenance"] == mt.AUTHORED and step["priority"]["resident"]["value"] == mt.NOT_EXPRESSED
    assert trace["scenario"]["category"]["provenance"] == mt.AUTHORED
    lines = {line["label"]: line for line in mt.render(trace)[0]["lines"]}
    assert lines["Resident reasoning"]["text"] == "Resident priority: not expressed"
    assert lines["Scenario priority (development path, proposed for faculty review)"]["provenance"] == mt.AUTHORED


@pytest.mark.parametrize("kind,orders,events,halted,terminal,minute", [
    ("DEFINITIVE_HAEMOSTASIS_REQUESTED", [_order("consult", canonical="consult gastroenterology")], (), False, False, 15),
    ("DEFINITIVE_HAEMOSTASIS_REQUESTED", [_order("consult", canonical="consult surgery")], (), False, False, 15),
    ("ENGINE_HAEMOSTASIS_EVENT", [_order("reassessment", delay=15)], ({"label": "Gastroenterology performed upper endoscopy: bleeding ulcer treated endoscopically; active bleeding controlled."},), False, False, 15),
    ("AUTHORITY_STOP", [_order("reassessment", delay=15)], (), True, False, 30),
    ("LEGACY_TERMINAL_STATE", [_order("reassessment", delay=15)], (), False, True, 30),
])
def test_a4_every_exit_of_the_boundary_is_deterministic_and_nothing_after_a_definitive_request_is_observed(kind, orders, events, halted, terminal, minute):
    turns = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, orders, events=events, terminal=terminal)]
    trace = mt.extract(turns, _artifact({15: (94, 58, 70), 30: (99, 60, 73)}, halted=halted), ARRIVAL)
    assert trace["boundary"]["kind"] == kind and trace["boundary"]["minute"] == minute and trace["boundary"]["provenance"] == mt.FACULTY_DEFINED
    if kind in ("DEFINITIVE_HAEMOSTASIS_REQUESTED", "ENGINE_HAEMOSTASIS_EVENT"):
        last = trace["steps"][-1]
        assert last["observed"]["pressure"]["value"] is None and last["observed"]["pressure"]["provenance"] == mt.UNKNOWN and last["new_state"]["pressure"]["value"] is None
        assert [point["minute"] for point in mt.trajectory(trace)] == [0, 15], "nothing after the boundary is part of the trajectory"
    assert mt.trace_problems(trace, turns) == []


def test_a5_the_horizon_is_the_boundary_and_its_message_says_what_it_does_not_mean():
    turns = [_turn(1, 0, 60, [_order("fluid")]), _turn(2, 60, 120, [_order("reassessment", delay=60)])]
    trace = mt.extract(turns, _artifact({60: (94, 58, 70), 120: (80, 50, 60)}), ARRIVAL)
    assert trace["boundary"]["kind"] == mt.EXIT_HORIZON and trace["boundary"]["minute"] == 120
    for words in ("does not mean that the patient has recovered", "that the bleeding has stopped", "that management is complete", "discharge is safe", "has not been controlled"):
        assert words in trace["boundary"]["message"]
    assert fmr.BOUNDARY_MESSAGES == (mt.BOUNDARY_MESSAGE, mt.BOUNDARY_MESSAGE_REQUEST), "the review's copies of the boundary texts are the trace module's own"


@pytest.mark.parametrize("claim", ["the patient was resuscitated", "shock corrected after the vasopressor", "the bleeding is controlled", "haemodynamically stabilized", "patient is stable",
                                   "recovered", "safe for discharge", "management complete", "successful resuscitation"])
def test_a6_a_generated_reading_that_claims_more_than_the_model_supports_is_refused(claim):
    trace = mt.extract([_turn(1, 0, 15, [_order("fluid")])], _artifact({15: (94, 58, 70)}), ARRIVAL)
    assert mt.claim_problems(trace) == []
    trace["steps"][0]["reassessment"]["reading"]["value"] = claim
    assert mt.claim_problems(trace), claim


def test_a7_a_tampered_trace_an_invented_reasoning_or_a_substituted_action_is_refused():
    turns = [_turn(1, 0, 15, [_order("fluid")])]
    trace = mt.extract(turns, _artifact({15: (94, 58, 70)}), ARRIVAL)
    assert mt.trace_problems(trace, turns) == []
    forged = json.loads(json.dumps(trace))
    forged["steps"][0]["priority"]["resident"] = mt.field("Restore volume.", mt.RESIDENT_EXPRESSED)
    forged["trace_digest"] = mt.digest({key: value for key, value in forged.items() if key != "trace_digest"})
    assert any("not exactly what the resident expressed" in problem for problem in mt.trace_problems(forged, turns))
    forged = json.loads(json.dumps(trace))
    forged["steps"][0]["action"]["text"]["value"] = "Give blood."
    forged["trace_digest"] = mt.digest({key: value for key, value in forged.items() if key != "trace_digest"})
    assert any("not the turn's own text" in problem for problem in mt.trace_problems(forged, turns))
    forged = json.loads(json.dumps(trace))
    forged["steps"][0]["observed"]["pressure"]["value"] = {"sbp": 140, "dbp": 90, "map": 107}
    assert "the trace digest does not recompute" in mt.trace_problems(forged, turns)
    unbound = mt.extract(turns, _artifact({}), ARRIVAL)
    assert unbound["steps"][0]["observed"]["pressure"]["provenance"] == mt.UNKNOWN, "no committed authority minute, no observed pressure"


def test_a8_the_page_s_own_management_trace_event_is_read_exactly():
    event = {"trace_schema": "management_trace_v1", "learner_input": "Give 1 litre of saline.", "decision_time_min": 0, "response_time_min": 15, "execution_status": "executed",
             "reasoning": {"management_priority": "Volume first."}, "orders": [_order("fluid")], "events": []}
    turn = mt.turn_from_page_event(event)
    assert turn["text_source"] == mt.PAGE and turn["reasoning"] == {"management_priority": "Volume first."} and turn["executed"] is True and turn["response_minute"] == 15
    assert mt.turn_from_runner_entry({"text": "x", "decision_time_min": 0, "response_time_min": 0, "orders": []})["reasoning"] == {}, "a scripted path expresses no reasoning"


def test_a8b_the_transcript_the_page_appends_after_its_gate_is_not_the_resident_s_action():
    entry = ("Give fluid. I expect a higher pressure.\n\nGuided reasoning completion: **Working model:** shock  \n**Management priority:** improve arterial pressure and tissue perfusion  \n"
             "**Expected effect:** a higher pressure  \n**Reassessment:** pressure in 15 minutes\n\nReasoning clarification: because of the bleeding")
    turn = mt.turn_from_page_event({"learner_input": entry, "execution_status": "executed", "orders": [], "reasoning": {}})
    assert turn["text"] == "Give fluid. I expect a higher pressure.\n\nReasoning clarification: because of the bleeding"
    assert mt.resident_text("Give fluid.") == "Give fluid."


def test_a9_a_phrase_the_application_composed_is_never_the_resident_s_and_a_slot_from_another_moment_keeps_its_label():
    """P3-515 M1 (reproduced before the repair): the page composes a priority from the resident's other words and marks it (``derived_slots``, ``slot_provenance`` = composed); the trace showed it as
    'Resident priority (as expressed)'. A composed slot is NOT_EXPRESSED, with a note; a slot written at another moment keeps the page's own label; and a trace that shows a composed slot as expressed is refused."""
    composed = {"expected_effect": "the blood pressure and perfusion to improve", "management_priority": "improve arterial pressure and tissue perfusion",
                "derived_slots": ["management_priority"], "slot_provenance": {"management_priority": "composed", "expected_effect": "stated"}}
    turns = [_turn(1, 0, 15, [_order("fluid")], reasoning=composed, source=mt.PAGE, text="Give fluid.")]
    trace = mt.extract(turns, _artifact({15: (94, 58, 70)}), ARRIVAL)
    step = trace["steps"][0]
    assert step["priority"]["resident"]["value"] == mt.NOT_EXPRESSED and step["priority"]["resident"]["note"] == mt.COMPOSED_NOTE
    assert step["expected"]["resident"]["value"] == "the blood pressure and perfusion to improve" and "as" not in step["expected"]["resident"]
    lines = {line["label"]: line["text"] for line in mt.render(trace)[0]["lines"]}
    assert "improve arterial pressure" not in " ".join(lines.values()) and lines["Resident reasoning"].startswith("Resident priority: not expressed")
    assert mt.trace_problems(trace, turns) == []
    forged = json.loads(json.dumps(trace))
    forged["steps"][0]["priority"]["resident"] = mt.field("improve arterial pressure and tissue perfusion", mt.RESIDENT_EXPRESSED, "reasoning.management_priority")
    forged["trace_digest"] = mt.digest({key: value for key, value in forged.items() if key != "trace_digest"})
    assert any("not exactly what the resident expressed" in problem for problem in mt.trace_problems(forged, turns))
    carried = {"management_priority": "Volume first.", "slot_provenance": {"management_priority": "carried"}}
    step = mt.extract([_turn(1, 0, 15, [_order("fluid")], reasoning=carried, source=mt.PAGE)], _artifact({15: (94, 58, 70)}), ARRIVAL)["steps"][0]
    assert step["priority"]["resident"]["value"] == "Volume first." and step["priority"]["resident"]["as"] == "stated earlier in this encounter"
    retro = {"expected_effect": "Pressure up.", "slot_provenance": {"expected_effect": "retrospective"}}
    trace = mt.extract([_turn(1, 0, 15, [_order("fluid")], reasoning=retro, source=mt.PAGE)], _artifact({15: (94, 58, 70)}), ARRIVAL)
    assert "explained afterwards, as a retrospective" in {line["label"]: line for line in mt.render(trace)[0]["lines"]}["Expected (resident, as expressed; explained afterwards, as a retrospective)"]["label"]


@pytest.mark.parametrize("order", [
    {"class": "consult", "canonical": "consult", "span": "Consult GI", "fate": "RECORDED_NOT_MODELLED"},
    {"class": "consult", "canonical": "consult", "span": "Consult interventional radiology for embolization", "fate": "RECORDED_NOT_MODELLED"},
    {"class": "consult", "canonical": "consult gastroenterology", "span": "Call GI for urgent endoscopy", "fate": "EXECUTED"},
    {"class": "consult", "canonical": "consult surgery", "span": "Consult general surgery", "fate": "HELD"},
    {"class": "unrecognized", "canonical": "unrecognized", "span": "Page the gastroenterologist", "fate": "UNRECOGNIZED"},
    {"class": "plan", "canonical": "plan:future_timed", "span": "Consult gastroenterology in 30 minutes", "fate": "RECORDED_NOT_MODELLED"},
    {"class": "endoscopy", "canonical": "endoscopy", "span": "Upper endoscopy", "fate": "RECORDED_NOT_MODELLED"},
])
def test_a10_any_request_for_definitive_control_ends_the_encounter_at_its_decision_whatever_the_ledger_did_with_it(order):
    """P3-515 M2 (reproduced before the repair): 'Consult GI.' and the interventional-radiology request are RECORDED_NOT_MODELLED and the encounter went on for two hours past them."""
    assert mt.is_definitive_request(order)
    turns = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, [order, _order("reassessment", delay=15)])]
    trace = mt.extract(turns, _artifact({15: (94, 58, 70), 30: (99, 60, 73)}), ARRIVAL)
    assert (trace["boundary"]["kind"], trace["boundary"]["minute"]) == (mt.EXIT_DEFINITIVE_HAEMOSTASIS, 15) and [point["minute"] for point in mt.trajectory(trace)] == [0, 15]


@pytest.mark.parametrize("order", [
    {"class": "blood", "canonical": "blood 2 units", "span": "Transfuse 2 units for the GI bleed", "fate": "EXECUTED"},
    {"class": "fluid", "canonical": "fluid normal saline 1000 mL", "span": "Give 1 litre of saline", "fate": "EXECUTED"},
    {"class": "consult", "canonical": "consult cardiology", "span": "Consult cardiology", "fate": "EXECUTED"},
    {"class": "reassessment", "canonical": "reassessment 15 min", "span": "Reassess the GI bleed in 15 minutes", "fate": "EXECUTED"},
])
def test_a10b_a_treatment_or_another_service_that_names_the_bleed_is_not_a_request(order):
    assert not mt.is_definitive_request(order)


def test_a11_the_arrival_is_authored_until_the_authority_commits_a_minute_and_a_mislabel_is_refused():
    """P3-515 M3 (reproduced before the repair): a turn that does not move the clock carried the authored arrival forward labelled as a live-authority observation."""
    turns = [_turn(1, 0, 0, [_order("vascular_access")]), _turn(2, 0, 15, [_order("fluid")])]
    trace = mt.extract(turns, _artifact({15: (94, 58, 70)}), ARRIVAL)
    first, second = trace["steps"]
    assert (first["state"]["pressure"]["provenance"], first["state"]["pressure"]["source"]) == (mt.AUTHORED, "authored arrival")
    assert (first["new_state"]["pressure"]["provenance"], first["new_state"]["pressure"]["source"]) == (mt.AUTHORED, "authored arrival")
    assert first["observed"]["pressure"]["provenance"] == mt.AUTHORED and first["observed"]["authority"]["value"] is None
    assert (second["state"]["pressure"]["provenance"], second["new_state"]["pressure"]["provenance"]) == (mt.AUTHORED, mt.OBSERVED)
    assert second["new_state"]["pressure"]["source"] == "live development authority" and second["observed"]["authority"]["value"]["minute"] == 15
    assert mt.trace_problems(trace, turns) == []
    forged = json.loads(json.dumps(trace))
    forged["steps"][1]["state"]["pressure"] = mt.field(dict(ARRIVAL), mt.OBSERVED, "live development authority")
    forged["trace_digest"] = mt.digest({key: value for key, value in forged.items() if key != "trace_digest"})
    assert any("the state is not the new state of the step before it" in problem for problem in mt.trace_problems(forged, turns))
    forged = json.loads(json.dumps(trace))
    forged["steps"][0]["new_state"]["pressure"] = mt.field(dict(ARRIVAL), mt.OBSERVED, "live development authority")
    forged["trace_digest"] = mt.digest({key: value for key, value in forged.items() if key != "trace_digest"})
    assert any("labelled as the live authority's without its committed minute" in problem for problem in mt.trace_problems(forged, turns))
    assert first["reassessment"]["timing"]["provenance"] == mt.MODEL_DERIVED, "the turn rule is the engine's, read, not observed"


def _halted_artifact(committed, aborted, reason="UNSUPPORTED_AUTHORITY_ACTION"):
    artifact = _artifact(committed, halted=True)
    artifact["halt_reason"] = reason
    artifact["minutes"] += [{"minute": minute, "committed": [], "outcome": "ABORTED", "written_candidate": None} for minute in aborted]
    return artifact


def test_a12_the_first_exit_in_time_is_the_boundary_the_others_of_the_same_turn_are_named_and_no_turn_follows_a_stop():
    """P3-515 (reproduced before the repair): an authority stop at minute 30 followed by a request at minute 30 read as the request; a request and a stop in one turn hid the stop."""
    later = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, [_order("norepinephrine", canonical="norepinephrine start 0.1 mcg/kg/min")]),
             _turn(3, 30, 45, [_order("consult", canonical="consult gastroenterology")])]
    trace = mt.extract(later, _halted_artifact({15: (94, 58, 70)}, [30, 45]), ARRIVAL)
    assert (trace["boundary"]["kind"], trace["boundary"]["minute"]) == (mt.EXIT_AUTHORITY_STOP, 30) and len(trace["steps"]) == 2
    assert trace["steps"][-1]["observed"]["pressure"]["source"] == "the live development authority stopped at this turn" and mt.trace_problems(trace, later) == []
    same = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, [_order("consult", canonical="consult gastroenterology"), _order("norepinephrine", canonical="norepinephrine start 0.1 mcg/kg/min")])]
    trace = mt.extract(same, _halted_artifact({15: (94, 58, 70)}, [30]), ARRIVAL)
    assert (trace["boundary"]["kind"], trace["boundary"]["minute"], trace["boundary"]["also"]) == (mt.EXIT_DEFINITIVE_HAEMOSTASIS, 15, [mt.EXIT_AUTHORITY_STOP])
    assert {"label": "Also in this turn", "text": mt.ALSO_WORDS[mt.EXIT_AUTHORITY_STOP], "provenance": mt.OBSERVED} in mt.render(trace)[-1]["lines"]


def test_a13_each_exit_says_its_own_words():
    engine = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, [_order("reassessment", delay=15)], events=({"label": "Upper endoscopy: active bleeding controlled endoscopically."},))]
    assert mt.extract(engine, _artifact({15: (94, 58, 70), 30: (99, 60, 73)}), ARRIVAL)["boundary"]["message"] == mt.HAEMOSTASIS_EVENT_MESSAGE
    terminal = [_turn(1, 0, 15, [_order("fluid")], terminal=True)]
    assert mt.extract(terminal, _artifact({15: (94, 58, 70)}), ARRIVAL)["boundary"]["message"] == mt.TERMINAL_MESSAGE
    crossed = [_turn(1, 0, 90, [_order("fluid")]), _turn(2, 90, 150, [_order("blood")])]
    boundary = mt.extract(crossed, _artifact({90: (94, 58, 70), 150: (80, 50, 60)}), ARRIVAL)["boundary"]
    assert (boundary["kind"], boundary["minute"]) == (mt.EXIT_HORIZON, 150) and boundary["message"] == mt.BOUNDARY_MESSAGE + mt.HORIZON_CROSSED_NOTE
    for message in (mt.HAEMOSTASIS_EVENT_MESSAGE,):
        for words in ("does not mean that the patient has recovered", "that the bleeding has stopped", "has not been reviewed"):
            assert words in message
    assert "operational reason" not in mt.TERMINAL_MESSAGE and "has been recorded" not in mt.HAEMOSTASIS_EVENT_MESSAGE


def test_a14_a_minute_the_authority_committed_and_then_disowned_is_not_an_observation():
    artifact = _artifact({15: (94, 58, 70), 30: (99, 60, 73)}, halted=True)
    artifact["minutes"].append({"minute": 30, "committed": [], "outcome": "ABORTED", "written_candidate": None})
    assert sorted(mt.authority_points(artifact)) == [15] and mt.halt_minute(artifact) == 30
    turns = [_turn(1, 0, 15, [_order("fluid")]), _turn(2, 15, 30, [_order("reassessment", delay=15)])]
    trace = mt.extract(turns, artifact, ARRIVAL)
    assert trace["boundary"]["kind"] == mt.EXIT_AUTHORITY_STOP and trace["steps"][-1]["observed"]["pressure"]["value"] is None


# ============================================================================================================================================
# B. the ten paths through the LIVE development authority
# ============================================================================================================================================
@pytest.fixture(scope="module")
def played():
    return {path_id: tp.run_path(path_id) for path_id in tp.PATH_IDS}


@pytest.fixture(scope="module")
def played_72f():
    return {path_id: tp.run_path(path_id, "gi_bleed_72f") for path_id in ("A", "B", "F", "H")}


def _maps(play):
    return {point["minute"]: point["map"] for point in mt.trajectory(play["trace"])}


def _sbps(play):
    return {point["minute"]: point["sbp"] for point in mt.trajectory(play["trace"])}


def test_b1_every_path_reaches_the_horizon_with_a_trace_that_holds_and_every_pressure_is_a_committed_live_authority_minute(played):
    for path_id, play in played.items():
        trace = play["trace"]
        assert mt.trace_problems(trace, play["turns"]) == [], path_id
        assert trace["boundary"]["kind"] == mt.EXIT_HORIZON and trace["boundary"]["minute"] == 120 and not trace["authority"]["halted"], path_id
        assert (trace["authority"]["grant_id"], trace["authority"]["snapshot_id"], trace["authority"]["tone_snapshot_id"]) == (NE_GRANT, PRESSURE_SNAPSHOT, TONE_SNAPSHOT), path_id
        assert trace["authority"]["authority_label"] == "REAL_DEVELOPMENT_PRESSURE_AUTHORITY"
        committed = mt.authority_points(play["artifact"])
        for point in mt.trajectory(trace)[1:]:
            assert committed[point["minute"]]["pressure"] == {key: point[key] for key in ("sbp", "dbp", "map")}, (path_id, point)
        for step in trace["steps"]:
            authority = step["observed"]["authority"]["value"]
            if step["response_minute"]["value"] > step["decision_minute"]["value"]:
                assert authority and authority["grant_id"] == NE_GRANT and authority["candidate_digest"], (path_id, step["n"])


def test_b2_different_action_sequences_give_different_trajectories_from_the_same_arrival(played):
    arrivals = {json.dumps(mt.trajectory(play["trace"])[0], sort_keys=True) for play in played.values()}
    assert len(arrivals) == 1, "every path starts from the same arrival"
    trajectories = {path_id: json.dumps(mt.trajectory(play["trace"]), sort_keys=True) for path_id, play in played.items()}
    assert len(set(trajectories.values())) == len(trajectories), "two different sequences gave the same trajectory"


def test_b3_the_same_arrival_and_the_same_sequence_give_the_same_result(played):
    for path_id in ("B", "E", "I"):
        again = tp.run_path(path_id)
        assert mt.trajectory(again["trace"]) == mt.trajectory(played[path_id]["trace"]), path_id
        assert again["trace"]["trace_digest"] == played[path_id]["trace"]["trace_digest"], path_id
        assert again["given"] == played[path_id]["given"]


def test_b4_the_causal_ordering_the_faculty_named_holds(played):
    """P3-511A: volume and blood address the volume state; norepinephrine supports the pressure; norepinephrine alone does not control the bleeding; continuing bleeding erodes temporary gains; reducing or
    stopping norepinephrine reduces the support causally. Any violation is a material contradiction."""
    m = {path_id: _maps(play) for path_id, play in played.items()}
    A, B, C, D, E, F, G, H, I, J = (m[key] for key in "ABCDEFGHIJ")
    given = {path_id: {step["text"].split(".")[0]: step["minute"] for step in play["given"]} for path_id, play in played.items()}
    # volume and blood address the volume state, and the gain erodes while the bleeding continues
    assert max(A.values()) > A[0] and A[120] < max(A.values()) and A[120] > H[120]
    # the untreated course falls throughout and is lowest at the boundary
    assert all(later <= earlier for earlier, later in zip(list(H.values()), list(H.values())[1:])) and H[120] == min(H.values())
    # norepinephrine supports the pressure: at the first reading after a start it is above the course without it
    start_b = given["B"]["Start norepinephrine at 5 mcg/min"]
    assert B[start_b + 15] > A[start_b + 15] and B[120] >= A[120]
    assert F[15] > H[15] and C[15] > H[15]
    # norepinephrine alone does not control the bleeding: without volume the pressure keeps falling below the volume-only course
    assert F[120] < A[120] and F[120] > H[120] and max(F.values()) > F[120]
    assert I[120] < A[120] and max(I.values()) > I[120]
    # every vasopressor gain erodes: the pressure at the boundary is below the path's own peak
    for course in (B, C, D, F, I):
        assert course[120] < max(course.values())
    # an increase given while the pressure is low again raises it at the next reading
    up_d = given["D"]["Increase norepinephrine to 8 mcg/min"]
    assert D[up_d + 15] > D[up_d]
    # reducing or stopping norepinephrine takes the support away: after it wears off the course IS the volume-only course
    stop_e, stop_j = given["E"]["Stop norepinephrine"], given["J"]["Stop norepinephrine"]
    assert E[stop_e + 15] < E[stop_e] and E[120] == A[120]
    assert J[stop_j + 15] < J[stop_j] and J[stop_j + 15] == A[stop_j + 15] and J[120] == A[120]
    # slow crystalloid alone does not keep up with the bleeding
    assert G[120] < A[120] and G[120] >= H[120]
    # volume and blood after a vasopressor first raise the pressure again
    assert C[45] > C[30]


def test_b5_the_second_case_satisfies_the_same_relations_and_a_step_whose_state_never_comes_is_not_given(played_72f):
    m = {path_id: _maps(play) for path_id, play in played_72f.items()}
    assert max(m["A"].values()) > m["A"][0] and m["A"][120] < max(m["A"].values()) and m["A"][120] > m["H"][120]
    assert m["F"][15] > m["H"][15] and m["F"][120] < m["A"][120] and m["F"][120] > m["H"][120]
    # in the 72-year-old woman the pressure is never low again within two hours after volume and blood: the state-contingent vasopressor is not given, and B is the volume-only course
    assert played_72f["B"]["not_given"] == [["hypotensive_from", 15]] and m["B"] == m["A"]
    for play in played_72f.values():
        assert mt.trace_problems(play["trace"], play["turns"]) == [] and play["trace"]["boundary"]["kind"] == mt.EXIT_HORIZON


def test_b5b_no_scripted_action_is_one_the_ledger_ignores_as_already_done(played):
    """P3-515 #1 (reproduced before the repair): every path began with 'Place an IV line.', which the ledger ignores because the arrival already has access -- an action that does not fit the state."""
    for path_id, play in played.items():
        for entry in play["entries"]:
            assert not [order for order in entry["orders"] if str(order.get("fate")) == "DUPLICATE_IGNORED"], (path_id, entry["text"])


def test_b5c_the_view_of_the_artifact_the_trace_persists_gives_the_same_trace_as_the_whole_artifact(played):
    for path_id in ("B", "E", "I"):
        play = played[path_id]
        arrival = {key: play["arrival"][key] for key in ("sbp", "dbp", "map")}
        assert mt.extract(play["turns"], mt.artifact_view(play["artifact"]), arrival)["steps"] == mt.extract(play["turns"], play["artifact"], arrival)["steps"]


def test_b6_a_step_is_given_only_when_the_state_it_answers_is_there(played):
    """No state/action mismatch: a state-contingent step was given at a reading that satisfied its condition, and the scenario priority of that step answers that state."""
    for path_id, play in played.items():
        readings = {point["minute"]: point for point in mt.trajectory(play["trace"])}
        for given in play["given"]:
            kind = given["when"][0]
            if kind in ("hypotensive_from", "hypotensive_after"):
                assert mt.hypotensive(readings[given["minute"]]), (path_id, given)
            if kind == "not_hypotensive_after":
                assert not mt.hypotensive(readings[given["minute"]]), (path_id, given)


def test_b7_the_authority_artifacts_verify_and_replay(played):
    import runtime_authority as ra
    for path_id in ("B", "E", "J"):
        artifact = played[path_id]["artifact"]
        check = ra.verify_artifact(artifact)
        assert check["digest_matches"] and check["outcomes_consistent"] and not check["missing_fields"], (path_id, check)
        replay = ra.replay_site_artifact(artifact)
        assert replay.get("ok", True) and not replay.get("problems"), (path_id, {key: replay.get(key) for key in ("ok", "problems")})


def test_b7b_the_runner_leaves_the_process_environment_exactly_as_it_found_it(monkeypatch):
    """The development configuration is in the process environment ONLY while the runner works: a runner that leaked the live-authority flags would turn every later test of the same process (a page test,
    a review test) into a test under the live authority."""
    import os
    import runtime_authority as ra
    names = sorted(set(ra.PILOT_FLAGS) | set(ra.PILOT_REQUIRED_ON) | set(tp.environment()))
    monkeypatch.setenv(ra.AUTHORITY_FLAG, "shadow_only_sentinel")
    before = {name: os.environ.get(name) for name in names}
    run = tp.DevelopmentEncounter(tp.CASE_ID)
    assert {name: os.environ.get(name) for name in names} == before
    run.order(tp.VOL)
    assert {name: os.environ.get(name) for name in names} == before
    assert sorted(mt.authority_points(run.artifact())) == [15], "and the runner still ran under the live authority"


def test_b8_the_trace_survives_serialization_and_re_extraction_from_its_persisted_inputs(played):
    """The trace is a pure function of the persisted turns, the persisted artifact and the arrival: a session that restarts from them reads the same trace."""
    for path_id in ("A", "D", "I"):
        play = played[path_id]
        stored = json.loads(json.dumps(tp.portable(play), default=str))
        assert stored["trace"] == play["trace"] and mt.trace_problems(stored["trace"], stored["turns"]) == []
        scenario = {"id": f"MT-{path_id}", "case_id": tp.CASE_ID, "plan_digest": tp.plan_digest(path_id), "category": tp.PATHS[path_id]["category"],
                    "priorities": {int(key): value for key, value in {step["n"]: step["priority"]["scenario"]["value"] for step in play["trace"]["steps"] if step["priority"]["scenario"]["value"]}.items()}}
        again = mt.extract(stored["turns"], stored["artifact"], {key: stored["arrival"][key] for key in ("sbp", "dbp", "map")}, scenario=scenario)
        assert again["trace_digest"] == play["trace"]["trace_digest"], path_id


# ============================================================================================================================================
# C. the source-control boundary and the educational-safety attacks (P3-513)
# ============================================================================================================================================
def test_c1_a_request_for_definitive_control_of_the_bleeding_ends_the_development_encounter_before_any_haemostasis():
    run = tp.DevelopmentEncounter()
    run.order(tp.VOL)
    run.order("Consult gastroenterology for urgent endoscopy. Start norepinephrine at 10 mcg/min. Reassess in 15 minutes.")
    turns = [mt.turn_from_runner_entry(entry) for entry in run.entries]
    trace = mt.extract(turns, run.artifact(), {"sbp": 88, "dbp": 54, "map": 65})
    assert trace["boundary"]["kind"] == mt.EXIT_DEFINITIVE_HAEMOSTASIS and trace["boundary"]["minute"] == 15 and trace["boundary"]["message"] == mt.BOUNDARY_MESSAGE_REQUEST
    assert run.enc.state["family_state"].get("endoscopy_at") is None, "no haemostasis happened inside the development encounter"
    assert mt.trajectory(trace)[-1]["minute"] == 15 and mt.trace_problems(trace, turns) == []


def test_c2_declared_finding_in_the_live_page_a_consultation_can_lead_to_an_unreviewed_engine_haemostasis():
    """NOT a property this package relies on: the pre-existing live behaviour it declares (SOURCE_CONTROL_REACHABLE_IN_THE_LIVE_PAGE_NOT_REVIEWED). Pinned so that a change of it is seen."""
    run = tp.DevelopmentEncounter()
    run.order(tp.VOL)
    run.order("Consult gastroenterology for urgent endoscopy. Start norepinephrine at 10 mcg/min. Reassess in 30 minutes.")
    run.order("Reassess in 60 minutes.")
    assert run.enc.state["family_state"].get("endoscopy_at") is not None, "the engine performed the endoscopy once the pressure allowed it"
    assert any(mt.is_haemostasis_event(event) for entry in run.entries for event in entry["events"]) or run.enc.state["family_state"].get("endoscopy_at") is not None
    assert "SOURCE_CONTROL_REACHABLE_IN_THE_LIVE_PAGE_NOT_REVIEWED" in fmr.LIMITATION_IDS


def test_c3_no_path_says_more_than_the_model_supports_and_every_step_carries_the_caveats_of_its_state(played):
    for path_id, play in played.items():
        trace = play["trace"]
        assert mt.claim_problems(trace) == [], path_id
        running = False
        for step in trace["steps"]:
            limitations = set(step["limitations"]["value"])
            assert {"BLEEDING_NOT_CONTROLLED", "LEGACY_FIELDS_NOT_AUTHORITATIVE", "OBSERVED_AT_REASSESSMENT_ONLY"} <= limitations, (path_id, step["n"])
            operations = [row.get("operation") for row in step["action"]["orders"]["value"] if row["class"] == "norepinephrine"]
            if any(op in ("NE_START", "NE_RESTART", "NE_INCREASE", "NE_DECREASE") for op in operations):
                running = True
            if running:
                assert {"VASOPRESSOR_SUPPORT_IS_TEMPORARY", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED"} <= limitations, (path_id, step["n"])
                if step["response_minute"]["value"] > step["decision_minute"]["value"] and "NE_STOP" not in operations:
                    assert "temporary, not control of the bleeding" in step["reassessment"]["reading"]["value"], (path_id, step["n"])
            if "NE_STOP" in operations:
                running = False
            assert "bleeding is not controlled" in step["reassessment"]["reading"]["value"] or step["response_minute"]["value"] == step["decision_minute"]["value"]


def test_c4_the_ten_misleading_lessons_are_not_taught(played):
    """P3-513: each attack, measured on the paths."""
    m = {path_id: _maps(play) for path_id, play in played.items()}
    texts = json.dumps([mt.render(play["trace"]) for play in played.values()]).lower()
    # 1 norepinephrine replaces volume resuscitation: no -- without volume (F, I) the pressure ends below the volume-only course
    assert m["F"][120] < m["A"][120] and m["I"][120] < m["A"][120]
    # 2 red cells stop active bleeding: no -- after volume and blood the pressure erodes and every step says the bleeding is not controlled
    assert m["A"][120] < max(m["A"].values()) and "bleeding is not controlled" in texts
    # 3 a normal pressure means resuscitation is complete: no -- a 'not hypotensive' reading always carries 'bleeding not controlled'
    for play in played.values():
        for step in play["trace"]["steps"]:
            reading = step["new_state"]["reading"]["value"]
            if "not hypotensive" in reading:
                assert "bleeding not controlled" in reading
    # 4 pressor-driven pressure means consciousness improves: no -- no mental status, consciousness or heart rate is in any rendered trace or item
    for word in ("mental status", "alert", "drowsy", "consciousness", "heart rate", "capillary"):
        assert word not in texts, word
    # 5 prolonged observation of shock is acceptable: no -- the untreated course falls throughout and its category is proposed as clearly nonbeneficial
    assert m["H"][120] == min(m["H"].values()) and tp.PATHS["H"]["category"] == "CLEARLY_NONBENEFICIAL"
    # 6 source control happens silently: no -- no haemostasis inside any path, and a request ends the encounter at a boundary that says so
    assert all(play["run"].enc.state["family_state"].get("endoscopy_at") is None for play in played.values())
    # 7 an unsupported action is treated as successful management: no path executes one (the authority would stop), and no stop happened
    assert all(not play["trace"]["authority"]["halted"] for play in played.values())
    # 8 the trace attributes reasoning the resident never stated: every resident field of every scripted path is NOT_EXPRESSED
    for play in played.values():
        for step in play["trace"]["steps"]:
            assert all(step[part]["resident"]["value"] == mt.NOT_EXPRESSED for part in ("priority", "expected", "reassessment"))
            assert step["action"]["text"]["provenance"] == mt.AUTHORED
    # 9 a temporary response is labelled definitive: no generated text claims it
    assert all(mt.claim_problems(play["trace"]) == [] for play in played.values())
    # 10 the model rewards the pressure alone: nothing is scored; the review asks the reviewer to classify the management (Q6) and the readings never call a pressure a success
    assert "success" not in texts and "score" not in texts


# ============================================================================================================================================
# D. the stored review set
# ============================================================================================================================================
LOADED = fmr.load_set()


def test_d1_the_stored_set_is_pinned_verified_and_holds_the_ten_paths_in_order():
    assert LOADED["ok"], LOADED["problems"]
    assert fmr.PINNED_SET_DIGEST is not None and LOADED["digest"] == fmr.PINNED_SET_DIGEST
    assert list(LOADED["items"]) == list(fmr.SCENARIOS) == [f"MT-{path}" for path in "ABCDEFGHIJ"]
    assert set(LOADED["categories"]) == set(fmr.SCENARIOS)


def test_d2_the_stored_set_is_what_the_live_authority_regenerates(played):
    stored = json.loads(fmr.SET_PATH.read_text(encoding="utf-8"))
    regenerated = tp.reproduce({path_id: tp.portable(play) for path_id, play in played.items()})
    assert {key: value for key, value in stored.items() if key not in ("provenance", "record_digest")} == json.loads(json.dumps(regenerated, default=str))
    import historical_records as hr
    assert hr.same_generating_code(stored, tp.generating_code()), "the stored set names the generating code that is in the tree (P3-515 M4)"


def test_d2b_every_stored_trace_re_extracts_from_the_record_alone():
    """P3-515 #10: the record carries the persisted inputs of each trace (the turns and the part of the authority artifact the extraction reads); a reader with nothing but the record re-extracts the SAME
    trace, as a session restarting from its persisted inputs would."""
    stored = json.loads(fmr.SET_PATH.read_text(encoding="utf-8"))
    for scenario_id, path in stored["audit"]["paths"].items():
        inputs = path["persisted_inputs"]
        trace = path["trace"]
        scenario = {"id": scenario_id, "case_id": stored["audit"]["case_id"], "plan_digest": path["plan_digest"], "category": path["category_proposed"],
                    "priorities": {step["n"]: step["priority"]["scenario"]["value"] for step in trace["steps"] if step["priority"]["scenario"]["value"]}}
        again = mt.extract(inputs["turns"], inputs["artifact_view"], inputs["arrival"], scenario=scenario)
        assert again["trace_digest"] == trace["trace_digest"] == path["trace_digest"], scenario_id
        assert mt.trace_problems(again, inputs["turns"]) == []


def test_d3_an_item_carries_nothing_of_the_mechanism_and_the_audit_and_categories_stay_apart():
    for identifier, item in LOADED["items"].items():
        view = fmr.blind_view(item)
        text = json.dumps(view).lower()
        for token in ("grant", "snapshot", "digest", "fingerprint", "tone", "gain", "authority", "legacy", "candidate", "lineage", "artifact", "category", "reasonable", "temporizing", "nonbeneficial", "incomplete"):
            if token in ("reasonable", "temporizing", "nonbeneficial", "incomplete"):
                text_without_q6 = json.dumps({key: value for key, value in view.items() if key != "questions"}).lower()
                assert not re.search(rf"\b{token}\b", text_without_q6), (identifier, token)
                continue
            assert not re.search(rf"\b{token}", text), (identifier, token)
        assert [question["id"] for question in view["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
        assert view["trace"][-1].get("boundary") and view["boundary"]["message"] in fmr.BOUNDARY_MESSAGES


def test_d4_q6_is_required_before_the_lock_and_an_earlier_set_is_asked_exactly_what_it_was(tmp_path):
    item = LOADED["items"]["MT-A"]
    log = fmr.ManagementReviewLog(tmp_path, "reviewer-1", item, set_digest=LOADED["digest"], audit=LOADED["audit"])
    for question, value in (("Q1", "Expected"), ("Q2", "Plausible"), ("Q3", "Plausible"), ("Q4", "Coherent"), ("Q5", "No")):
        assert log.answer(question, value)["ok"]
    assert not log.lock()["ok"], "the lock waits for Q6"
    assert not log.answer("Q6", "Excellent")["ok"]
    assert log.answer("Q6", "Reasonable")["ok"] and log.lock()["ok"]
    assert [question["id"] for question in ftr.required_questions({"scenario_id": "FR-B"})[0]] == ["Q1", "Q2", "Q3", "Q4", "Q5"], "an item that does not ask for Q6 is asked the five"


def test_d5_the_proposed_categories_and_the_limitations_appear_only_in_a_complete_summary(tmp_path):
    order = fmr.sequence(LOADED["items"])
    answers = {"Q1": "Expected", "Q2": "Plausible", "Q3": "Plausible", "Q4": "Coherent", "Q5": "No", "Q6": "Temporizing"}
    for count, entry in enumerate(order, 1):
        log = fmr.ManagementReviewLog(tmp_path, "reviewer-2", LOADED["items"][entry["scenario_id"]], set_digest=LOADED["digest"], audit=LOADED["audit"])
        for question, value in answers.items():
            assert log.answer(question, value)["ok"]
        assert log.lock()["ok"] and log.set_overall("ACCEPT_WITH_LIMITATION")["ok"] and log.submit()["ok"]
        summary = fmr.summarize(tmp_path, "reviewer-2", LOADED["items"], order, LOADED["digest"], LOADED["audit"], LOADED["limitations"], LOADED["categories"])
        if count < len(order):
            assert not summary["complete"] and summary["limitations"] == [] and all(row["proposed_category"] is None for row in summary["scenarios"])
    assert summary["complete"] and [entry["id"] for entry in summary["limitations"]] == list(fmr.LIMITATION_IDS)
    assert {row["scenario_id"]: row["proposed_category"] for row in summary["scenarios"]} == LOADED["categories"]
    assert all(row["first_pass"]["Q6"] == "Temporizing" for row in summary["scenarios"])


def test_d6_a_regenerated_or_re_signed_set_is_refused_until_its_digest_is_pinned(tmp_path):
    record = json.loads(fmr.SET_PATH.read_text(encoding="utf-8"))
    record["items"][0]["purpose"] = record["items"][0]["purpose"] + " "
    record["record_digest"] = fmr._seal_digest({key: value for key, value in record.items() if key != "record_digest"})
    path = tmp_path / "set.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert not fmr.load_set(path)["ok"]
    leak = json.loads(fmr.SET_PATH.read_text(encoding="utf-8"))
    leak["items"][0]["purpose"] = "The grant and the snapshot decide."
    assert fmr.item_problems(leak["items"][0])


# ============================================================================================================================================
# E. the launcher's hold
# ============================================================================================================================================
def test_e1_the_management_review_is_offered_after_the_earlier_holds_and_the_operator_s_switch_releases_it(monkeypatch):
    assert launcher.MANAGEMENT_MODE not in (launcher.TRAJECTORY_MODE, launcher.REREVIEW_MODE, launcher.TONE_MODE, launcher.TITRATION_MODE, launcher.LIVE_MODE)
    source = (ROOT / "faculty_review_ui.py").read_text(encoding="utf-8")
    assert source.index("hold_titration(st, layer, context)") < source.index("hold_management(st, layer, context)"), "the earlier holds come first"
    monkeypatch.setenv(fmu.OPERATOR_FLAG, fmu.OPERATOR_OPEN)
    assert fmu.other_modes_held(None, None, None) is False
    monkeypatch.delenv(fmu.OPERATOR_FLAG)

    class Review:
        FACULTY_ROLES = ("faculty", "admin")

        @staticmethod
        def review_root():
            return None
    assert fmu.other_modes_held(None, type("L", (), {"review": Review, "bundles": None}), {"user": {"role": "faculty", "id": 1}}) is True, "whatever cannot be decided is held"
    assert fmu.other_modes_held(None, type("L", (), {"review": Review, "bundles": None}), {"user": {"role": "resident", "id": 2}}) is True
