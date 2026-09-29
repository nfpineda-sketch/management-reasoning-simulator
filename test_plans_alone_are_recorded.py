"""An order that carries only plans is said as recorded, with no generic question after it (TD-38).

Cycle 10, C10-07. A conditional order, advice to the patient or treatment
received before the resident's care, written alone, runs nothing and holds
nothing. The room said each one as recorded and then added "Please specify a
question, investigation, treatment, or reassessment.", as if nothing had been
read. Now the Trace records it as not executed, with no question, and no
minute passes. The reader is untouched: what it recognises is the same.
"""
import pytest

import language
import unexecuted_items
from test_doses_by_solution_and_by_weight import start, submit

GENERIC = "Please specify a question, investigation, treatment, or reassessment."


@pytest.mark.parametrize("played, text, kind, said", [
    ("en", "If the glucose falls below 70 mg/dL, give 25 g of dextrose 50% IV.", "conditional",
     "Recorded as a conditional plan, not executed now:"),
    ("es", "Si la glicemia baja de 70 mg/dL, doy 25 g de glucosa al 50% IV.", "conditional",
     "Recorded as a conditional plan, not executed now:"),
    ("es", "Le indico que vuelva si tiene síntomas de hipoglicemia.", "advice",
     "Recorded as advice to the patient:"),
    ("en", "EMS gave 25 g of dextrose 50% IV before arrival.", "prior_treatment",
     "Recorded as treatment received before your care, as reported:"),
    # The two examples of KD-25 in validation/KNOWN_DEFECTS_V3.md: a discharge for later, and history.
    ("es", "Alta en 2 horas.", "conditional", "Recorded as a disposition plan, not carried out now:"),
    ("en", "Epinephrine 0.5 mg IM given by EMS.", "prior_treatment",
     "Recorded as treatment received before your care, as reported:"),
])
def test_a_plan_alone_is_said_as_recorded_and_nothing_asks_after_it(tmp_path, monkeypatch, played, text, kind, said):
    monkeypatch.setenv("MRS_LANGUAGE", played)
    at = start(tmp_path, monkeypatch, "hypoglycemia_28m", "R1-06", language=played)
    minute = at.session_state["state"]["sim_time"]
    count = len(at.session_state["events"])
    submit(at, text)
    added = at.session_state["events"][count:]
    assert [event["kind"] for event in added] == ["you", "prototype"]
    assert added[1]["text"].startswith(said)
    assert not any(GENERIC in str(event["text"]) for event in at.session_state["events"])
    entry = at.session_state["management_trace"][-1]
    assert [detail["kind"] for detail in entry["future_details"]] == [kind]
    assert entry["interpreted_action"] == [] and entry["action_summaries"] == []
    assert entry["execution_status"] == "not_executed" and entry["clarification"] is None
    assert at.session_state["state"]["sim_time"] == minute
    assert not at.session_state["pending_action"]
    if played == "es":
        # The room reads the sentence in the encounter's language, and nothing follows it.
        shown = language.say(added[1]["text"], "es")
        assert shown != added[1]["text"] and shown.startswith("Registrad")


def test_an_order_to_run_now_beside_a_plan_is_still_read_and_run(tmp_path, monkeypatch):
    monkeypatch.setenv("MRS_LANGUAGE", "en")
    at = start(tmp_path, monkeypatch, "hypoglycemia_28m", "R1-06", language="en")
    submit(at, "Check a capillary glucose now. If it is below 70 mg/dL, give 25 g of dextrose 50% IV.")
    entry = at.session_state["management_trace"][-1]
    assert entry["execution_status"] == "executed"
    assert [detail["kind"] for detail in entry["future_details"]] == ["conditional"]


@pytest.mark.parametrize("parsed, expected", [
    ({"actions": [], "recognized_future_actions": ["x"], "future_details": [{"kind": "conditional"}]}, True),
    ({"actions": [], "recognized_future_actions": ["x"], "future_details": [{"kind": "repeat"}]}, True),
    # Something to run now, a question, an indicated medicine or an unclassified item: not only plans.
    ({"actions": [{"type": "reassessment"}], "recognized_future_actions": ["x"],
      "future_details": [{"kind": "conditional"}]}, False),
    ({"actions": [], "clarification": "Which dose?", "recognized_future_actions": ["x"],
      "future_details": [{"kind": "conditional"}]}, False),
    ({"actions": [], "recognized_future_actions": ["x"], "future_details": [{"kind": "not_modelled"}]}, False),
    ({"actions": [], "recognized_future_actions": ["x"], "future_details": []}, False),
    ({"actions": [], "recognized_future_actions": [], "future_details": []}, False),
])
def test_only_plans_are_told_apart_from_everything_else(parsed, expected):
    assert unexecuted_items.plans_only(parsed) is expected
