"""KD-31 (faculty, 2026-09-29): the screening cites the treatment reported as received before.

"Aspirin 300 mg given by EMS" is history the resident wrote (TD-36): not their order and not
an administration of this encounter. Beside an omission of the same kind the screening now
quotes it, with the source and the time the reader recorded -- none is invented -- and says
that the reading is the faculty's. The event's definition, weight and result do not change.
"""
import pytest

import rubric_screening
from family_parser import parse_family_actions
from test_rubric_analysis import record_on_case


def written(case_id, *orders, minute=4):
    """A record whose trace holds what the reader kept of each order, nothing executed."""
    record = record_on_case(case_id)
    trace = []
    for order in orders:
        parsed = parse_family_actions(order)
        trace.append({"execution_status": "executed", "decision_time_min": minute, "response_time_min": minute,
                      "learner_input": order, "interpreted_action": [], "action_summaries": [],
                      "future_details": parsed.get("future_details", [])})
    record["payload"]["session"]["management_trace"] = trace
    return record


def without_accounts(record):
    """The same record, as it read before the reader kept prior treatment."""
    from copy import deepcopy
    record = deepcopy(record)
    for event in record["payload"]["session"]["management_trace"]:
        event.pop("future_details", None)
    return record


def row(record, case_id, event_id):
    [found] = [r for r in rubric_screening.screen_events(record, case_id) if r["event_id"] == event_id]
    return found


@pytest.mark.parametrize("case_id, event_id, account, source", [
    ("acs_48m_wellens", "acs_no_antiplatelet", "Aspirin 300 mg given by EMS. Reassess in 10 minutes.", "by ems"),
    ("acs_48m_wellens", "acs_no_antiplatelet", "Aspirina 300 mg dada por SAMU. Reevaluar en 10 minutos.", "por samu"),
    ("anaphylaxis_29f", "anaphylaxis_no_epinephrine",
     "Epinephrine 0.5 mg IM given at OSH at 10:40. Reassess in 5 minutes.", "at osh"),
])
def test_a_reported_prior_treatment_is_quoted_and_the_result_does_not_move(case_id, event_id, account, source):
    record = written(case_id, account)
    before, after = row(without_accounts(record), case_id, event_id), row(record, case_id, event_id)
    assert after["status"] == before["status"]
    assert after["facts"][:len(before["facts"])] == before["facts"]
    context = after["facts"][-1]
    assert "history, not an order or an administration of this encounter" in context["en"]
    assert "historia, no una orden ni una administración de este encuentro" in context["es"]
    assert f"source recorded: {source}" in context["en"] and f"fuente registrada: {source}" in context["es"]
    assert "faculty's call" in context["en"] and "lo decide el docente" in context["es"]
    assert after["faculty_interpretation"] is True and "trace:0" in after["refs"]
    assert [item["source"] for item in after["prior_treatment"]] == [source]


def test_no_time_is_invented_and_the_written_one_stays_in_the_quote():
    after = row(written("anaphylaxis_29f", "Epinephrine 0.5 mg IM given at OSH at 10:40."),
                "anaphylaxis_29f", "anaphylaxis_no_epinephrine")
    [item] = after["prior_treatment"]
    context = after["facts"][-1]
    assert item["reported_time"] is None
    assert "no time recorded apart from the text" in context["en"] and "at 10:40" in context["en"]
    assert "sin hora registrada aparte del texto" in context["es"]
    assert "written at 4 min" in context["en"] and "escrito a los 4 min" in context["es"]


def test_a_prior_treatment_of_another_kind_or_a_record_without_any_changes_nothing():
    other = written("acs_48m_wellens", "Epinephrine 0.5 mg IM given by EMS.")
    plain = without_accounts(other)
    assert row(other, "acs_48m_wellens", "acs_no_antiplatelet") == row(plain, "acs_48m_wellens", "acs_no_antiplatelet")
    assert "prior_treatment" not in row(plain, "acs_48m_wellens", "acs_no_antiplatelet")


def test_the_same_account_written_twice_is_quoted_once():
    record = written("acs_48m_wellens", "Aspirin 300 mg given by EMS.", "Aspirin 300 mg given by EMS.")
    assert len(row(record, "acs_48m_wellens", "acs_no_antiplatelet")["prior_treatment"]) == 1


def test_the_model_reads_the_context_but_never_a_new_status():
    record = written("acs_48m_wellens", "Aspirin 300 mg given by EMS.")
    model = rubric_screening.for_model(rubric_screening.screening(record, "acs_48m_wellens"))
    [event] = [e for e in model["events"] if e["event_id"] == "acs_no_antiplatelet"]
    assert event["status"] == row(without_accounts(record), "acs_48m_wellens", "acs_no_antiplatelet")["status"]
    assert any("received before their care" in fact for fact in event["facts"])
