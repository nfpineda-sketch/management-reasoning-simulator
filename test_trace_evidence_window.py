"""A decision's recorded response window must contain its own response.

Found preparing the learner report from the first paid case (2026-09-22). The
Management Trace records each decision immediately after execution, and the
learner-facing events that describe the response are appended afterwards, so
``state_after`` carried the cursor of ``state_before``. The analysis is
validated against that window: the model cited the clinical update it was
describing, and the whole report was rejected for citing evidence the resident
supposedly had not seen yet.
"""
import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).with_name("app.py"))
ORDER = ("Hipotension con mala perfusion, debido a hipovolemia. La prioridad ahora es reponer "
         "volumen. Pasa 500 mL de suero fisiologico endovenoso. Espero que suba la presion. "
         "Reevalua en 20 minutos presion y llene capilar.")
SECOND = ("Sigue hipotenso, debido a perdida persistente. La prioridad ahora es seguir reponiendo. "
          "Pasa 500 mL de suero fisiologico endovenoso. Espero que suba la presion. "
          "Reevalua en 20 minutos presion y llene capilar.")


@pytest.fixture
def encounter(monkeypatch):
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("MRS_REPLAY_CASE", raising=False)
    app = AppTest.from_file(APP, default_timeout=300)
    app.secrets["APP_PASSWORD"] = "x"
    app.session_state["_shared_access_granted"] = True
    app.run()
    next(b for b in app.button if b.label == "Begin Encounter").click().run()
    assert not app.exception, app.exception
    return app


def submit(app, text):
    next(w for w in app.radio if w.label == "Encounter").set_value("Treat").run()
    app.text_area[0].set_value(text)
    next(b for b in app.button if b.label == "Submit").click().run()
    assert not app.exception, app.exception


def test_the_response_window_grows_with_the_response(encounter):
    submit(encounter, ORDER)
    submit(encounter, SECOND)
    trace = encounter.session_state.management_trace
    assert len(trace) == 2
    for event in trace:
        before = event["state_before"]["encounter_event_count"]
        after = event["state_after"]["encounter_event_count"]
        assert after > before, (before, after)


def test_no_evidence_is_lost_between_one_decision_and_the_next(encounter):
    submit(encounter, ORDER)
    submit(encounter, SECOND)
    trace = encounter.session_state.management_trace
    # What a decision could see when it ended is what the next one starts with.
    assert trace[0]["state_after"]["encounter_event_count"] <= trace[1]["state_before"]["encounter_event_count"]
    # And the last window reaches the end of the record.
    assert trace[-1]["state_after"]["encounter_event_count"] == len(encounter.session_state.events)
