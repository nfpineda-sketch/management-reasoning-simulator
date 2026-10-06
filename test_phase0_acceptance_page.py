"""Phase 0 (0J): every bank case through the page itself, and a reload in the middle of it.

Pre-pilot measurement safety, 2026-10-06. The engine-level battery (pilot_acceptance) runs the
family branch of the order path without Streamlit; this one plays every bank case on the real
page (AppTest, a throwaway SQLite database, no provider key): the reasoning gate, the order
ledger, the time words, the Trace's Phase 0 fields and the save. One order the simulator does
not carry out is written with the correct bundle, so rule D must keep every later event of the
course from counting against the resident.
"""
import pytest

import order_ledger
import pilot_acceptance as acceptance
import rubric_screening
import time_semantics
from test_phase0_order_ledger import _encounter, submit
from test_phase0_submission_guard import _resume

REASONING = ("I think this is the problem the presentation shows. My priority is to stabilise the patient. "
             "I expect the vital signs to improve. ")
LOOK = " I will reassess the vital signs in 15 minutes."


@pytest.mark.parametrize("variant", acceptance.variants())
def test_the_case_on_the_page(variant, tmp_path, monkeypatch):
    family = acceptance.family_of(variant)
    at = _encounter(tmp_path, monkeypatch, variant, acceptance.LAUNCH[family])
    bundle = acceptance.scripts(variant)["correct"]
    submit(at, REASONING + acceptance.UNMODELLED_ORDER + " " + bundle + LOOK)
    if at.session_state.get("pending_reasoning"):
        # The gate asked for what this wording did not give: give it, as a resident would.
        submit(at, REASONING + "I will check the blood pressure, the heart rate and the saturation in 15 minutes.")
    first = at.session_state["management_trace"][-1]
    assert first["execution_status"] in ("executed", "terminal_locked"), first.get("clarification")
    fates = {order["class"]: order["fate"] for order in first["orders"]}
    assert fates.get("unrecognized") in ("UNRECOGNIZED", "RECORDED_NOT_MODELLED") or any(
        "ondansetron" in str(order.get("span")).lower() and order["fate"] != "EXECUTED" for order in first["orders"])

    minute = at.session_state["state"]["sim_time"]
    submit(at, "Wait 20 minutes.")
    waited = at.session_state["management_trace"][-1]
    stopped = (waited.get("interrupted") or {}).get("minute")
    arrested = waited["execution_status"] == "terminal_locked" or (waited["observation_snapshot"] or {}).get("arrest")
    assert at.session_state["state"]["sim_time"] == minute + 20 or stopped == at.session_state["state"]["sim_time"] \
        or arrested
    before_look = at.session_state["state"]["sim_time"]
    submit(at, "Reassess.")
    looked = at.session_state["management_trace"][-1]
    if looked["execution_status"] == "executed":
        assert at.session_state["state"]["sim_time"] == before_look + time_semantics.BEDSIDE_LOOK_MIN

    # Every turn carries the Phase 0 record, and every order of the encounter has its fate.
    for entry in at.session_state["management_trace"]:
        assert {"submission", "orders", "events", "observation_snapshot", "limitations", "versions"} <= set(entry)
        assert entry["versions"]["variant_id"] == variant
        assert entry["observation_snapshot"]["inconsistencies"] == []
        assert all(order["fate"] in order_ledger.FATES for order in entry["orders"])
        assert not [item for item in entry["limitations"] if item["kind"] == "engine_inconsistency"]
    assert all(order["fate"] in order_ledger.FATES for order in at.session_state["order_ledger"])

    # Rule D: after an order the simulator did not carry out, nothing in the course counts
    # against the resident.
    record = {"payload": {"session": {key: at.session_state[key]
                                      for key in ("management_trace", "order_ledger")}}}
    events = rubric_screening.screening(record, variant)["course_events"]
    assert not [e for e in events if e["may_support_negative_feedback"]], events

    # A reload resumes the same encounter and runs nothing again.
    token, turns = at.session_state["_account_token"], len(at.session_state["management_trace"])
    minute = at.session_state["state"]["sim_time"]
    again = _resume(token)
    assert again.session_state["state"]["sim_time"] == minute
    assert len(again.session_state["management_trace"]) == turns
    assert again.session_state["state"]["observable"] == at.session_state["state"]["observable"]
