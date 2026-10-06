"""What the page says about an order follows what the engine actually ran.

59O-03 of the cycle 5 trace audit, approved for cycle 6 (2026-09-28): the page
announced "Urgent intervention executed without waiting for the reasoning" and
offered to explain it afterwards before the engine had run anything, so a
bundle the engine refused -- held for a question, or for an item it could not
read -- was still reported as a decision taken. The announcement and the offer
now come from the execution itself.

The same end-to-end cases also hold the clarification safety the cycle asked
for: a question about a held order never loses it, and an answer that answers
nothing ("no se", "I don't know") keeps it held and asks again, where the
Spanish reply used to discard the whole held bundle without a word.

Six cases, in both languages, on the real page (Streamlit's in-process runner,
a throwaway SQLite database, no provider key):

A. recognised and executed: the page says so and offers the explanation;
B. held for its reasoning: nothing is claimed and nothing changes;
C. an unreadable item: named as not understood; the independent urgent order
   runs and is announced (Phase 0 bundle rule, 2026-10-06);
D. a question about one order: only that order waits; what ran is announced;
E. the answer completes it: now it runs;
F. an answer that answers nothing: still held, asked again, nothing given.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import faculty_analysis
import language
import urgent_interventions
from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))

ORDERS = {
    "es": {"urgent": "Ventilo con bolsa mascarilla con O2 100%",
           "held": "Doy naloxona 0.4 mg ev",
           "unreadable": "Ventilo con bolsa mascarilla y xyzzol 3 mg ev",
           "cancel": "cancelar",
           "question": "Ventilo con bolsa mascarilla y doy naloxona ev",
           "unsure": "no sé",
           "answer": "0,4 mg"},
    "en": {"urgent": "Bag-mask ventilate with 100% oxygen",
           "held": "Give naloxone 0.4 mg IV",
           "unreadable": "Bag-mask ventilate and give xyzzol 3 mg IV",
           "cancel": "cancel",
           "question": "Bag-mask ventilate and give naloxone IV",
           "unsure": "I don't know",
           "answer": "0.4 mg"},
}
URGENT_NOTE = "Urgent intervention executed"
OFFER = "Explain an urgent decision afterwards"


@pytest.fixture
def opioid(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 1, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "opioid_67f")):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": "R1-06", "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(token)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    return at


def submit(at, text):
    """Submit one turn; return what the page said in it and the patient before and after."""
    before = dict(at.session_state["state"].get("observable") or {})
    minute = at.session_state["state"].get("sim_time")
    count = len(at.session_state["events"])
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Send").click().run()
    assert not at.exception
    said = [(event["kind"], event["text"]) for event in list(at.session_state["events"])[count:]]
    return said, before, minute


def offered(at):
    return any(expander.label.startswith(OFFER) for expander in at.expander)


def unchanged(at, before, minute):
    return (dict(at.session_state["state"].get("observable") or {}) == before
            and at.session_state["state"].get("sim_time") == minute)


def claims_urgent_execution(said):
    return any(text.startswith(URGENT_NOTE) for _, text in said)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_a_an_urgent_order_that_runs_is_announced_and_offered_for_explanation(opioid, lang):
    at = opioid
    said, before, _ = submit(at, ORDERS[lang]["urgent"])
    entry = at.session_state["management_trace"][-1]
    assert entry["execution_status"] == "executed"
    assert entry["reasoning_gate"]["status"] == "urgent_unheld"
    assert any(summary.get("type") == "bag_mask" for summary in entry["action_summaries"])
    assert claims_urgent_execution(said)
    assert offered(at)
    # The physiology moved because the order ran, and only then.
    assert before.get("respiratory_support") is None
    assert at.session_state["state"]["observable"].get("respiratory_support") == "Bag-mask ventilation"


@pytest.mark.parametrize("lang", ["es", "en"])
def test_b_an_order_held_for_its_reasoning_claims_nothing(opioid, lang):
    at = opioid
    said, before, minute = submit(at, ORDERS[lang]["held"])
    assert at.session_state["pending_reasoning"]
    assert not claims_urgent_execution(said)
    assert any("has not been executed" in text for _, text in said)
    assert not offered(at)
    assert unchanged(at, before, minute)
    assert not any(entry.get("execution_status") == "executed"
                   for entry in at.session_state["management_trace"])


@pytest.mark.parametrize("lang", ["es", "en"])
def test_c_an_unreadable_item_is_named_and_the_urgent_order_runs(opioid, lang):
    # Phase 0 (0B, 2026-10-06): an item the reader cannot read no longer holds the
    # independent urgent order written with it (bundle rule). What the page says still
    # follows what ran: the ventilation ran and is announced; the unreadable item is named
    # as not understood, and nothing is claimed for it.
    at = opioid
    said, before, minute = submit(at, ORDERS[lang]["unreadable"])
    entry = at.session_state["management_trace"][-1]
    assert entry["execution_status"] == "executed"
    assert {summary.get("type") for summary in entry["action_summaries"]} == {"bag_mask"}
    assert any(kind == "prototype" and text.startswith('Not understood: "') and "xyzzol" in text
               for kind, text in said)
    assert any(kind == "clinical_update" and "Bag-mask" in text for kind, text in said)
    fates = {order["class"]: order["fate"] for order in entry["orders"]}
    assert fates["bag_mask"] == "EXECUTED" and fates["unrecognized"] == "UNRECOGNIZED"
    assert not at.session_state["pending_action"]
    # Nothing is left waiting: cancel finds nothing to cancel and administers nothing.
    said, before, minute = submit(at, ORDERS[lang]["cancel"])
    assert any(kind == "clarification" and "no pending orders" in text for kind, text in said)
    assert unchanged(at, before, minute)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_d_f_e_a_question_holds_only_the_order_it_is_about(opioid, lang):
    at = opioid
    # D (Phase 0, 0B): the ventilation runs now and is said to have run; only the
    # naloxone, whose dose is asked for, waits. It used to hold the ventilation too.
    said, before, minute = submit(at, ORDERS[lang]["question"])
    assert any("naloxone dose" in text for kind, text in said if kind == "clarification")
    assert at.session_state["pending_action"]
    entry = at.session_state["management_trace"][-1]
    assert entry["execution_status"] == "executed" and entry.get("execution_scope") == "partial"
    assert {summary.get("type") for summary in entry["action_summaries"]} == {"bag_mask"}
    assert claims_urgent_execution(said)
    held = [order for order in at.session_state["order_ledger"] if order["fate"] == "HELD_CLARIFICATION"]
    assert [order["class"] for order in held] == ["naloxone"]
    assert at.session_state["state"]["observable"].get("respiratory_support") == "Bag-mask ventilation"
    # F: an answer that answers nothing keeps the naloxone held and asks again. The
    # Spanish reply used to discard the held order without a word.
    said, before, minute = submit(at, ORDERS[lang]["unsure"])
    assert at.session_state["pending_action"]
    assert any("The held order is still waiting: naloxone" in text
               and "Nothing has been administered" in text for kind, text in said if kind == "clarification")
    assert unchanged(at, before, minute)
    # E: the answer completes it; the naloxone runs now, and only now is it given.
    said, before, _ = submit(at, ORDERS[lang]["answer"])
    assert not at.session_state["pending_action"]
    entry = at.session_state["management_trace"][-1]
    assert entry["execution_status"] == "executed"
    assert {summary.get("type") for summary in entry["action_summaries"]} >= {"naloxone"}
    assert {order["class"]: order["fate"] for order in entry["orders"]}["naloxone"] == "EXECUTED"
    # The record keeps the turns in the order they were decided.
    minutes = [e.get("decision_time_min") for e in at.session_state["management_trace"]]
    assert minutes == sorted(minutes)


def _urgent_entry(status):
    return {"execution_status": status,
            "reasoning_gate": {"status": "urgent_unheld", "noted": ["working_model", "expected_effect"]}}


@pytest.mark.parametrize("status, offered_again", [
    ("executed", True), ("clarification_required", False), ("not_executed", False), (None, False)])
def test_only_an_urgent_entry_that_ran_awaits_an_explanation(status, offered_again):
    trace = [_urgent_entry(status)]
    assert (urgent_interventions.awaiting_explanation(trace) == 0) is offered_again


@pytest.mark.parametrize("status, flagged", [("executed", True), ("clarification_required", False)])
def test_the_faculty_analysis_says_an_urgent_intervention_ran_only_when_it_did(status, flagged):
    assert faculty_analysis._prompted(_urgent_entry(status))["urgent_unheld"] is flagged


def test_only_a_reply_that_says_nothing_but_unsure_keeps_the_order_held():
    """The page reads the normalised reply: a doubt, not a negation followed by an order or a cancel."""
    import ast
    import re
    tree = ast.parse(Path(APP).read_text())

    def compiled(name):
        node = next(item for item in tree.body if isinstance(item, ast.Assign)
                    and any(getattr(target, "id", None) == name for target in item.targets))
        return eval(compile(ast.Expression(node.value), APP, "eval"), {"re": re})

    unsure, then_order = compiled("_UNSURE_REPLY"), compiled("_UNSURE_THEN_ORDER")

    def a_doubt(reply):
        match = unsure.match(reply)
        return bool(match) and not then_order.search(reply[match.end():])

    for reply in ("no se", "no se.", "mm no se", "no se la dosis", "i don't know", "not sure", "no estoy segura"):
        assert a_doubt(reply), reply
    for reply in ("no se administra adrenalina, sf 500 ml ev", "no se, cancelar", "not sure the dose, give 0.5 mg im"):
        assert not a_doubt(reply), reply


def test_the_repeated_question_reads_in_spanish():
    said = language.say("The held order is still waiting: bag mask + naloxone. Answer the question above, "
                        "or say cancel. Nothing has been administered.", "es")
    assert said.startswith("La orden retenida sigue esperando:")
    assert "Responde la pregunta de arriba" in said and "No se ha administrado nada." in said
