"""Phase 0 closure (F0-12): an order written beside the answer to a held order's question.

Pre-pilot measurement safety, closure pass of 2026-10-06. The answer to a held order's question
completed that order, and an order written after it in the same box was not run: its receipt
said so (0J). The faculty preferred entry-point parity where it is small and safe. The answer
alone now completes the held order, and the order written after it is written down as a
submission of its own (``submission_guard.derive``) and read next like any order the resident
sends: through the reasoning gate, its own questions, its own fate and receipt. The record keeps
the minute it was written in the answer, so a later run is the simulator's, never a delay of the
resident's (rule B of 0I). It never completes or changes the held order. When the answer leaves
part of the held order still waiting, the order after it keeps the protected receipt.
"""
import pytest

import order_pipeline
import submission_guard
from test_phase0_order_ledger import _encounter, _fates, _texts, submit

REASONING = ("I think this is the problem the presentation shows. My priority is to stabilise the patient. "
             "I expect the vital signs to improve. ")
LOOK = " I will check the blood pressure, the heart rate and the saturation in 15 minutes."


@pytest.mark.parametrize("text, answer, new", [
    ("0.1 mcg/kg/min. Also give 500 mL LR.", "0.1 mcg/kg/min", "give 500 mL LR."),
    ("1000 mL, and give ceftriaxone 2 g IV.", "1000 mL", "give ceftriaxone 2 g IV."),
    ("0,1 mcg/kg/min y además pasar 500 mL de Ringer.", "0,1 mcg/kg/min", "pasar 500 mL de Ringer."),
])
def test_the_answer_and_the_order_after_it_are_told_apart(text, answer, new):
    assert order_pipeline.split_answer(text) == (answer, new)


@pytest.mark.parametrize("text", ["1000 mL", "1000 mL. Reassess in 10 minutes.", "500 mL of normal saline",
                                  "0.1 mcg/kg/min, then check the blood pressure in 10 minutes."])
def test_an_answer_with_no_order_after_it_is_only_an_answer(text):
    assert order_pipeline.split_answer(text) is None


def test_a_bundle_with_an_order_still_waiting_is_not_complete():
    complete = {"actions": [{"type": "fluid", "fluid_type": "Normal saline", "volume_ml": 1000},
                            {"type": "reassessment", "delay_min": 15}]}
    assert order_pipeline.bundle_complete(complete)
    waiting = {"actions": complete["actions"] + [{"type": "norepinephrine", "rate": None}]}
    assert not order_pipeline.bundle_complete(waiting)


def test_the_new_order_is_written_down_once():
    session = {"submission_log": [{"id": "abc", "status": "processing"}]}
    first = submission_guard.derive(session, {"id": "abc"}, "give 500 mL LR.", minute=4)
    again = submission_guard.derive(session, {"id": "abc"}, "give 500 mL LR.", minute=4)
    assert first is again and [entry["id"] for entry in session["submission_log"]] == ["abc", "abc:new"]
    assert first["status"] == "received" and first["derived_from"] == "abc" and first["received_at_min"] == 4
    assert submission_guard.pending(session) == [first] and submission_guard.waiting(session)


def _held(tmp_path, monkeypatch, first):
    at = _encounter(tmp_path, monkeypatch, "pneumonia_83m", "R1-05")
    submit(at, REASONING + first + LOOK)
    if at.session_state.get("pending_reasoning"):
        submit(at, REASONING + LOOK)
    assert at.session_state.get("pending_action"), _fates(at)
    return at


def _ledger(at):
    return {order["span"]: order for order in at.session_state["order_ledger"]}


def test_the_held_order_resolves_and_the_new_order_enters_the_normal_pipeline(tmp_path, monkeypatch):
    """The faculty's example: held "Start norepinephrine.", answered "0.1 mcg/kg/min. Also give 500 mL LR."."""
    at = _held(tmp_path, monkeypatch, "Start norepinephrine.")
    written = len(_texts(at))
    submit(at, "0.1 mcg/kg/min. Also give 500 mL LR.")
    ledger = _ledger(at)
    norepinephrine = ledger["Start norepinephrine"]
    assert norepinephrine["fate"] == "EXECUTED" and norepinephrine["rate"] == 0.1
    lr = ledger["give 500 mL LR"]
    # Read like any order the resident sends: a new treatment order asks for its reasoning.
    assert lr["fate"] == "HELD_REASONING" and lr["canonical"].startswith("fluid")
    assert lr["written_at_min"] == 0 and lr["derived_from"] and lr["submission_id"].endswith(":new")
    said = "\n".join(_texts(at)[written:])
    assert 'Also in your answer: "give 500 mL LR". The answer completes the held order only' in said
    assert "I understood: **500 mL lactated Ringer's**" in said
    assert "Not understood" not in said and "Not run" not in said
    log = at.session_state["submission_log"]
    assert [entry["status"] for entry in log] == ["processed"] * len(log)
    assert sum(1 for entry in log if entry.get("derived_from")) == 1


def test_the_new_order_never_completes_or_changes_the_held_one(tmp_path, monkeypatch):
    at = _held(tmp_path, monkeypatch, "Give normal saline.")
    submit(at, "1000 mL, and also give 2 L of LR.")
    ledger = _ledger(at)
    saline = ledger["Give normal saline"]
    assert saline["fate"] == "EXECUTED" and saline["dose"] == 1000
    lr = ledger["give 2 L of LR"]
    # Its own order, with its own fate (the pipeline decides it, as for any order sent).
    assert lr["order_id"] != saline["order_id"] and lr["dose"] == 2000 and lr["derived_from"]
    assert lr["fate"] in ("EXECUTED", "HELD_REASONING") and lr["written_at_min"] == saline["written_at_min"] == 0


def test_an_answer_that_leaves_the_held_order_waiting_keeps_the_protected_receipt(tmp_path, monkeypatch):
    """Two held orders, one answered: the order after the answer is said not run, as before."""
    at = _held(tmp_path, monkeypatch, "Give normal saline. Start norepinephrine.")
    written = len(_texts(at))
    submit(at, "1000 mL, and give ceftriaxone 2 g IV.")
    said = "\n".join(_texts(at)[written:])
    assert not any(entry.get("derived_from") for entry in at.session_state["submission_log"])
    assert 'Not run: "ceftriaxone 2 g IV" was written in the answer to the question above' in said
    assert _fates(at)["ceftriaxone 2 g IV"] == "UNRECOGNIZED"
