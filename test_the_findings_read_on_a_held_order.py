"""MRS_AI_CUES=held, exercised: the findings a model reads on a held order.

Section 11 of the report of 2026-09-24 left it unexercised. What ``held`` means
in the code: the question about the findings rides on the one request the
second reader (MRS_AI_REASONING) makes about an order that would otherwise be
held. It costs nothing beyond that request, and without that reader there is no
request to ride, so ``held`` is ``off``.

What a model reads is only ever the resident's own words about their own
decision. The properties under test, through the same functions the page calls
and with a scripted provider (no key is sent anywhere, no socket is opened):

* the transitions -- held, completed in free text or in the form, cancelled,
  refused for want of budget, failed -- and one request at most per held order;
* the persistence -- the held order and its findings survive a saved and
  resumed encounter, and so does the budget, which used to start again;
* what the resident is shown -- nothing a model read is shown while they
  decide, and a word they never wrote, or wrote as an expectation, is never
  recorded as a finding they observed;
* the assessment -- the faculty brief, the rubric proposal and the record's
  screening are built from exactly the same input whether or not a model read
  any finding, so a finding can neither be credited nor penalised, and a held
  order that never ran leaves nothing behind.
"""
import json
from copy import deepcopy

import pytest

import reasoning_recognition
from test_cognitive_encounters import encounter as build_encounter
from test_curriculum_trajectories import initialize, load_engine

CASE, FAMILY = "hypoglycemia_28m", "hypoglycemia"
# The working model is missing, so the patterns hold this order. "pegajoso" is
# a finding the patterns do not know; "suba la glicemia" is an expectation.
HELD = ("Está pegajoso y confuso. Doy dextrosa 25 g ev. Espero que despierte y que suba "
        "la glicemia. Reevalúo glicemia en 10 minutos.")
ANSWER = "Creo que es una hipoglicemia."
COMPLETE = ("Está confuso y pegajoso, me preocupa que tenga hipoglicemia. Doy dextrosa 25 g ev. "
            "Espero que despierte. Reevalúo glicemia en 10 minutos.")
MODEL_CUES = [
    {"finding": "pegajoso", "polarity": "present", "linked": False, "link_marker": ""},
    # Written, but as an expectation: not something the resident observed.
    {"finding": "suba la glicemia", "polarity": "trend", "linked": False, "link_marker": ""},
    # Never written: a result the resident did not have.
    {"finding": "glicemia 40 mg/dl", "polarity": "present", "linked": False, "link_marker": ""},
]


class Provider:
    """A scripted second reader that counts what it is asked and answers from a script."""

    def __init__(self, working_model=False, fail=False):
        self.calls = []
        self.working_model = working_model
        self.fail = fail
        self.responses = self

    def create(self, **kwargs):
        schema = kwargs["text"]["format"]["schema"]["properties"]
        self.calls.append({"asked": sorted(name for name in schema if name != "cues"),
                           "cues": "cues" in schema})
        if self.fail:
            raise TimeoutError("scripted provider timeout")
        answer = {name: {"present": False, "quote": ""} for name in schema if name != "cues"}
        if self.working_model and "working_model" in answer:
            answer["working_model"] = {"present": True, "quote": "pegajoso y confuso"}
        if "cues" in schema:
            answer["cues"] = deepcopy(MODEL_CUES)
        return type("Response", (), {"output_text": json.dumps(answer)})()


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.fixture
def play(engine, monkeypatch):
    """Start the case with the given switches; return the session and the provider."""
    def start(cues="held", reader=True, fail=False, working_model=False):
        monkeypatch.delenv("MRS_OFFLINE_CASES", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "scripted-provider-no-key-is-sent")
        monkeypatch.setenv("MRS_AI_REASONING", "on" if reader else "off")
        if cues is None:
            monkeypatch.delenv("MRS_AI_CUES", raising=False)
        else:
            monkeypatch.setenv("MRS_AI_CUES", cues)
        provider = Provider(working_model=working_model, fail=fail)
        real = reasoning_recognition.recognize

        def scripted(text, fields, *, cues=False, api_key="", model="", **_):
            return real(text, fields, cues=cues, model="scripted", client=provider)

        monkeypatch.setattr(reasoning_recognition, "recognize", scripted)
        generated = build_encounter(engine, FAMILY, CASE)
        session = initialize(engine, deepcopy(generated["state"]))
        session["events"] = [{"kind": "presentation", "text": generated["presentation"], "time": 0}]
        session["ai_calls_spent"] = 0
        session["ai_call_ledger"] = []
        session["encounter_presentation"] = generated["presentation"]
        return session, provider
    return start


def submit(engine, text):
    """One submission, in the order the page takes it (app.py, the Submit branch)."""
    session = engine["st"].session_state
    engine["add_event"]("you", text)
    before = engine["management_state_snapshot"](session.state)
    resolution = engine["resolve_pending_reasoning"](text)
    if resolution and resolution.get("clarification"):
        return {"held": True, "prompt": resolution["clarification"]}
    parsed = resolution["parsed"] if resolution and resolution.get("parsed") else \
        engine["clinical_interpreter"](text)
    missing = engine["reasoning_still_missing"](parsed)
    gate_status = (parsed.get("reasoning_gate") or {}).get("status")
    if missing and gate_status != "overridden":
        engine["hold_pending_reasoning"](parsed, missing)
        prompt = engine["upsert_reasoning_gate_clarification"](parsed, missing)
        return {"held": True, "prompt": prompt, "missing": missing}
    if gate_status is None and any(action.get("type") in engine["REASONING_GATE_ACTION_TYPES"]
                                   for action in parsed.get("actions", [])):
        parsed["reasoning_gate"] = {"required": True, "status": "complete", "missing": [],
                                    "noted": engine["reasoning_gate_noted"](parsed)}
    engine["recognize_cues_for"](parsed)
    result = engine["execute_bundle"](parsed)
    after = engine["management_state_snapshot"](session.state)
    event = engine["record_management_trace"](parsed.get("raw_text") or text, parsed, result,
                                              before, after)
    return {"held": False, "event": event, "result": result}


def findings(rows):
    # A row the patterns wrote carries no source until something else is merged
    # beside it; every reader treats it as the patterns' (reasoning_cues.sanitise).
    return [(row["finding"], row.get("source", "pattern")) for row in rows or []]


# --- what "held" is ----------------------------------------------------------

def test_held_without_the_second_reader_is_off_and_asks_nothing(engine, play):
    session, provider = play(cues="held", reader=False)
    assert engine["ai_cue_mode"]() == "off"
    outcome = submit(engine, HELD)
    assert outcome["held"] and provider.calls == []
    assert "cue_recognition" not in session["pending_reasoning"]["parsed"]


def test_an_order_that_is_not_held_costs_nothing_in_held_mode(engine, play):
    session, provider = play()
    assert engine["ai_cue_mode"]() == "held"
    outcome = submit(engine, COMPLETE)
    assert not outcome["held"] and outcome["result"]["executed"]
    assert provider.calls == [] and session["ai_call_ledger"] == []
    event = outcome["event"]
    assert event["cue_recognition"] is None
    assert findings(event["reasoning"]["mentioned_findings"]) == [("confuso", "pattern")]


def test_always_reads_every_decision_at_one_request_each(engine, play):
    session, provider = play(cues="always")
    outcome = submit(engine, COMPLETE)
    assert provider.calls == [{"asked": [], "cues": True}]
    assert [row["purpose"] for row in session["ai_call_ledger"]] == ["cue recognition"]
    assert ("pegajoso", "model") in findings(outcome["event"]["reasoning"]["mentioned_findings"])


def test_without_the_cue_setting_the_held_request_reads_no_findings(engine, play):
    session, provider = play(cues=None)
    outcome = submit(engine, HELD)
    assert outcome["held"]
    assert [call["cues"] for call in provider.calls] == [False]
    held = session["pending_reasoning"]["parsed"]
    assert "cue_recognition" not in held
    assert findings(held["reasoning"]["mentioned_findings"]) == [("confuso", "pattern")]


# --- the transitions -----------------------------------------------------------

def test_a_held_order_asks_once_and_keeps_only_what_the_resident_observed(engine, play):
    session, provider = play()
    outcome = submit(engine, HELD)
    assert outcome["held"] and outcome["missing"] == ["working_model"]
    # One request, carrying both questions: the categories and the findings.
    assert len(provider.calls) == 1 and provider.calls[0]["cues"] is True
    assert "working_model" in provider.calls[0]["asked"]
    assert [row["purpose"] for row in session["ai_call_ledger"]] == ["held-order recognition"]
    held = session["pending_reasoning"]["parsed"]
    assert findings(held["reasoning"]["mentioned_findings"]) == [("confuso", "pattern"),
                                                                 ("pegajoso", "model")]
    # The expectation and the value nobody wrote are refused, and counted.
    assert held["cue_recognition"] == {"status": "read", "added_by_model": 1, "rejected": 2,
                                       "not_an_observation": 1}
    assert held["reasoning_recognition"]["status"] == "read"


def test_what_the_resident_is_shown_while_held_names_no_finding(engine, play):
    session, _ = play()
    outcome = submit(engine, HELD)
    # Everything the application said, as opposed to what the resident typed.
    shown = " ".join([outcome["prompt"]] + [str(event.get("text") or "")
                                            for event in session["events"]
                                            if event.get("kind") != "you"])
    for word in ("pegajoso", "glicemia 40", "suba la glicemia", "model"):
        assert word not in shown.lower()


def test_completed_in_free_text_the_decision_keeps_its_findings(engine, play):
    session, provider = play()
    submit(engine, HELD)
    outcome = submit(engine, ANSWER)
    assert not outcome["held"] and outcome["result"]["executed"]
    event = outcome["event"]
    assert findings(event["reasoning"]["mentioned_findings"]) == [("confuso", "pattern"),
                                                                  ("pegajoso", "model")]
    assert event["cue_recognition"]["added_by_model"] == 1
    gate = event["reasoning_gate"]
    assert gate["asked_for"] == ["working_model"] and gate["answered_via"] == "free_text"
    # Completing the order is not a second request.
    assert len(provider.calls) == 1 and session["ai_calls_spent"] == 1
    assert session["pending_reasoning"] is None


def test_completed_in_the_form_the_decision_keeps_its_findings(engine, play):
    session, provider = play()
    submit(engine, HELD)
    completed = engine["complete_pending_reasoning_fields"](
        "hipoglicemia", "", "que despierte", "glicemia", 10)
    assert completed and completed.get("parsed"), completed
    parsed = completed["parsed"]
    assert findings(parsed["reasoning"]["mentioned_findings"]) == [("confuso", "pattern"),
                                                                   ("pegajoso", "model")]
    assert parsed["reasoning_gate"]["answered_via"] == "form"
    assert len(provider.calls) == 1


def test_a_cancelled_held_order_leaves_nothing_behind(engine, play):
    session, _ = play()
    submit(engine, HELD)
    assert engine["cancel_pending_order"]() is True
    assert session["pending_reasoning"] is None
    assert session["management_trace"] == []
    # What remains is what the resident typed, as they typed it; nothing a
    # model read survives anywhere in what the encounter saves.
    import curriculum_runtime
    saved = json.dumps({key: session[key] for key in curriculum_runtime.SESSION_FIELDS
                        if key in session}, ensure_ascii=False)
    assert '"source": "model"' not in saved and "cue_recognition" not in saved


def test_an_exhausted_budget_holds_the_order_exactly_as_before(engine, play):
    session, provider = play()
    session["ai_calls_spent"] = engine["ai_call_budget"]()
    outcome = submit(engine, HELD)
    assert outcome["held"] and provider.calls == []
    held = session["pending_reasoning"]["parsed"]
    assert held["reasoning_recognition"]["status"] == "budget_exhausted"
    assert "cue_recognition" not in held
    assert findings(held["reasoning"]["mentioned_findings"]) == [("confuso", "pattern")]


def test_a_failed_reader_holds_the_order_and_keeps_what_the_patterns_read(engine, play):
    session, provider = play(fail=True)
    outcome = submit(engine, HELD)
    assert outcome["held"] and len(provider.calls) == 1
    held = session["pending_reasoning"]["parsed"]
    assert held["reasoning_recognition"]["status"] == "unavailable"
    assert "TimeoutError" in held["reasoning_recognition"]["reason"]
    assert "cue_recognition" not in held
    assert findings(held["reasoning"]["mentioned_findings"]) == [("confuso", "pattern")]


# --- persistence ---------------------------------------------------------------

def test_the_held_order_and_the_budget_survive_a_saved_and_resumed_encounter(engine, play):
    import curriculum_runtime
    session, provider = play()
    submit(engine, HELD)
    saved = json.loads(json.dumps({key: session[key] for key in curriculum_runtime.SESSION_FIELDS
                                   if key in session}))
    assert saved["ai_calls_spent"] == 1 and saved["pending_reasoning"]
    # A fresh browser session resumes the saved encounter.
    resumed = initialize(engine, saved["state"])
    resumed.update(deepcopy(saved))
    assert engine["ai_calls_spent"]() == 1
    outcome = submit(engine, ANSWER)
    assert not outcome["held"] and outcome["result"]["executed"]
    assert ("pegajoso", "model") in findings(outcome["event"]["reasoning"]["mentioned_findings"])
    assert len(provider.calls) == 1


# --- the assessment reads the record, never the findings ------------------------

def _record(session, presentation):
    return {
        "id": "held-cues", "revision": 1, "status": "completed", "username": "resident",
        "challenge_id": FAMILY, "updated_at": 1790100000, "is_sandbox": False,
        "encounter": {"presentation": presentation},
        "payload": {"session": {
            "selected_case": FAMILY, "review_completed": True,
            "encounter": {"authored_case_id": CASE},
            "management_trace": deepcopy(session["management_trace"]),
            "events": deepcopy(session["events"]),
            "precomparison_decision_review": {"decision-1": {
                "working_model_update": "Hipoglicemia.", "priority_trigger": "Confusión.",
                "alternative_action": "Glucagón.", "expected_response_reassessment": "Glicemia."}},
            "review_prompts": [{"review_id": "decision-1", "decision": 1, "time": "00:00"}],
            "adaptation_plan": {},
        }},
    }


def _played(engine, play, cues):
    session, _ = play(cues=cues)
    submit(engine, HELD)
    submit(engine, ANSWER)
    submit(engine, "Reevalúo en 10 minutos.")
    return _record(session, session["encounter_presentation"])


def test_the_brief_the_rubric_and_the_screening_read_the_same_input_either_way(engine, play):
    from faculty_analysis import build_analysis_source
    from rubric_analysis import build_rubric_source
    from rubric_screening import screening
    read = _played(engine, play, "held")
    unread = _played(engine, play, None)
    rows = read["payload"]["session"]["management_trace"][0]["reasoning"]["mentioned_findings"]
    assert ("pegajoso", "model") in findings(rows)
    assert ("pegajoso", "model") not in findings(
        unread["payload"]["session"]["management_trace"][0]["reasoning"]["mentioned_findings"])
    assert build_analysis_source(read) == build_analysis_source(unread)
    assert build_rubric_source(read) == build_rubric_source(unread)
    assert screening(read, CASE) == screening(unread, CASE)


def test_the_resident_s_own_trace_analysis_says_which_reader_saw_each_finding(engine, play):
    from management_trace_analysis import build_analysis_source
    from management_trace_store import analysis_payload_from_session
    record = _played(engine, play, "held")
    session = dict(record["payload"]["session"])
    session.update(encounter_ended=True, expert_comparison_unlocked=True,
                   encounter_closed_trace=session["management_trace"],
                   encounter_closed_events=session["events"])
    source = build_analysis_source(analysis_payload_from_session(session))
    [first] = [row for row in source["timeline"] if row["execution_status"] == "executed"][:1]
    named = {row["finding"]: row["source"] for row in first["mentioned_findings"]}
    assert named == {"confuso": "pattern", "pegajoso": "model"}
