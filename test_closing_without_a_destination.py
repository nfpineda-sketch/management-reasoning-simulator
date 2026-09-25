"""Closing without a destination: a warning that never blocks, and the kind of close.

Faculty decision 9 of 2026-09-25 ("Cierre temprano: opción B"). "No has
registrado un destino. ¿Quieres continuar o finalizar?" -- one click continues,
one click finishes. Whether it was a clinical close, an interruption or an early
finish is recorded. No destination is invented and the record is frozen exactly
as it stood, omissions included.
"""
import time
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import language
from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))


@pytest.fixture
def encounter(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 1, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "hypoglycemia_28m")):
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


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception


def submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    click(at, "Submit")


def test_no_destination_warns_and_lets_the_resident_continue(encounter):
    at = encounter
    submit(at, "Pido glicemia capilar")
    click(at, "Complete Encounter & Begin Review")
    assert not at.session_state["encounter_ended"]
    assert any(w.value == language.say("You have not recorded a destination. Do you want to continue or finish?", "en")
               for w in at.warning)
    click(at, "Continue the encounter")
    assert not at.session_state["encounter_ended"] and not at.session_state["close_pending"]


def test_finishing_records_the_kind_and_invents_nothing(encounter):
    at = encounter
    submit(at, "Pido glicemia capilar")
    trace = deepcopy(at.session_state["management_trace"])
    click(at, "Complete Encounter & Begin Review")
    next(r for r in at.radio if r.label == "How is this encounter ending?").set_value("interruption").run()
    click(at, "Finish now")
    assert at.session_state["encounter_ended"]
    close = at.session_state["encounter_close"]
    assert (close["kind"], close["destination_recorded"], close["warned"]) == ("interruption", False, True)
    assert at.session_state["encounter_closed_trace"] == trace
    assert not at.session_state["state"].get("disposition")


def test_with_a_destination_the_close_is_clinical_and_unwarned(encounter):
    at = encounter
    submit(at, "Creo que fue una hipoglicemia por ayuno, ya resuelta. Mi prioridad es un alta segura. "
               "Lo envio a su casa con control en policlinico en 48 horas. Espero que no se repita.")
    click(at, "Complete Encounter & Begin Review")
    assert at.session_state["encounter_ended"]
    assert at.session_state["encounter_close"]["kind"] == "clinical_close"
    assert at.session_state["encounter_close"]["destination_recorded"] is True


def test_the_spanish_warning_is_the_faculty_s_sentence():
    assert language.say("You have not recorded a destination. Do you want to continue or finish?", "es") == \
        "No has registrado un destino. ¿Quieres continuar o finalizar?"
