"""The four categories belong to the management plan, not to each drug.

Faculty decision 6 of 2026-09-25. Several orders can share one working model,
one expectation and one reassessment: an antipyretic or a snack inside a plan
the resident already explained, or a repeat of what the plan ordered, does not
open another full form. What it shares is recorded as shared with that plan --
never as stated again for this order. A relevant new decision is still asked
about, with the plan's answers offered in the form so that the resident
confirms or changes them.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import reasoning_provenance
from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))


def start(tmp_path, monkeypatch, variant, challenge):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 3, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", variant)):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": challenge, "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(token)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    return at


def submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception


PNEUMONIA_PLAN = ("Creo que es una neumonia con sepsis, porque tiene fiebre, FR 30 y llene lento. Mi prioridad "
                  "es el antibiotico. Doy ceftriaxona 2 g ev y azitromicina 500 mg ev. Espero que baje la "
                  "fiebre y mejore la perfusion. Reevaluo en 30 minutos temperatura, FR y llene capilar.")


def test_an_antipyretic_inside_the_plan_shares_it(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "pneumonia_46f", "R1-05")
    submit(at, PNEUMONIA_PLAN)
    submit(at, "Doy paracetamol 1 g ev")
    assert not at.session_state["pending_reasoning"]
    entry = at.session_state["management_trace"][-1]
    reasoning = entry["reasoning"]
    assert reasoning["expected_effect"] == "baje la fiebre y mejore la perfusion"
    assert reasoning["slot_provenance"]["expected_effect"] == reasoning_provenance.SHARED
    assert reasoning["slot_provenance"]["reassessment_target"] == reasoning_provenance.SHARED
    assert reasoning["shared_from"]["decision"] == 1


def test_a_repeat_of_what_the_plan_ordered_shares_it(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "asthma_24f", "R3-01")
    submit(at, "Creo que es una crisis asmatica grave, porque habla en frases cortas. Mi prioridad es "
               "broncodilatar. Doy salbutamol 5 mg nbz. Espero que baje la FR. Reevaluo en 15 minutos FR.")
    submit(at, "Repito salbutamol 5 mg nbz")
    assert not at.session_state["pending_reasoning"]
    assert at.session_state["management_trace"][-1]["reasoning"]["slot_provenance"][
        "reassessment_target"] == reasoning_provenance.SHARED


def test_a_relevant_new_decision_is_asked_with_the_plan_offered(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "pneumonia_46f", "R1-05")
    submit(at, PNEUMONIA_PLAN)
    submit(at, "Inicio VMNI CPAP 8 con FiO2 40%")
    pending = at.session_state["pending_reasoning"]
    assert pending, "a new ventilatory support is a decision of its own"
    assert pending["parsed"]["plan_suggestion"] == {
        "expected_effect": "baje la fiebre y mejore la perfusion",
        "reassessment_target": "temperatura, FR y llene capilar"}
    # Offered, not answered: nothing is recorded as the resident's until confirmed.
    assert not pending["parsed"]["reasoning"].get("expected_effect")
