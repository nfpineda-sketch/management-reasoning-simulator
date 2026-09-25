"""After a discharge, the reassessment is the follow-up the resident arranged.

Faculty decision 1 of 2026-09-25 ("Alta y seguimiento: opción B"). A discharge
asks for the four categories, and "what will you check" was read only as a
check inside the encounter: "Lo envio a su casa con control en policlinico en
48 horas" was held asking what the resident would check. The follow-up, its
interval and the return instructions are that answer. Passing the form says
the resident stated a follow-up -- not that the discharge was safe -- and what
is recorded is always the resident's own words.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountStore
from discharge_follow_up import adopt, dated, phrase

APP = str(Path(__file__).with_name("app.py"))
MODEL = "Creo que fue una hipoglicemia por ayuno, ya resuelta. Mi prioridad es un alta segura. "


def widget(elements, label):
    return next(item for item in elements if item.label == label)


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
    widget(at.button, "Begin Encounter").click().run()
    assert at.session_state["state"]["encounter_spec"]["variant_id"] == "hypoglycemia_28m"
    return at


def submit(at, text):
    widget(at.radio, "Encounter").set_value("Treat").run()
    widget(at.text_area, "Enter your clinical reasoning and/or actions").set_value(text)
    widget(at.button, "Submit").click().run()
    assert not at.exception


def discharges(at):
    return [entry for entry in at.session_state["management_trace"]
            if any(s.get("type") == "disposition" for s in entry.get("action_summaries", []))]


def test_a_discharge_with_a_dated_follow_up_runs(encounter):
    submit(encounter, MODEL + "Lo envio a su casa con control en policlinico en 48 horas. "
                              "Espero que no se repita.")
    assert not encounter.session_state["pending_reasoning"]
    [entry] = discharges(encounter)
    reasoning = entry["reasoning"]
    assert reasoning["reassessment_target"] == "control en policlinico en 48 horas"
    assert reasoning["slot_provenance"]["reassessment_target"] == "stated"
    # The 48 hours are the follow-up's, not a reassessment the clock runs to.
    assert encounter.session_state["state"]["sim_time"] < 60
    assert "reassessment_timing" not in entry["reasoning_gate"]["noted"]


def test_a_held_discharge_is_released_by_the_follow_up(encounter):
    submit(encounter, MODEL + "Lo envio a su casa. Espero que no se repita.")
    assert encounter.session_state["pending_reasoning"]
    submit(encounter, "Control en policlinico en 48 horas y volver si se siente mal.")
    assert not encounter.session_state["pending_reasoning"]
    [entry] = discharges(encounter)
    assert "control en policlinico en 48 horas" in entry["reasoning"]["reassessment_target"].lower()


def test_a_discharge_with_no_follow_up_is_still_asked(encounter):
    submit(encounter, MODEL + "Lo envio a su casa. Espero que no se repita.")
    assert encounter.session_state["pending_reasoning"]
    assert discharges(encounter) == []


@pytest.mark.parametrize("text, found, when", [
    ("La doy de alta con control ambulatorio", "control ambulatorio", False),
    ("Lo doy de alta con analgesia, control urologico y regresar si tiene fiebre o dolor incontrolable.",
     "control urologico y regresar si tiene fiebre o dolor incontrolable", False),
    ("Alta con signos de alarma y control en 1 semana", "signos de alarma y control en 1 semana", True),
    ("Discharge home with follow-up with GP in 2 days", "follow-up with GP in 2 days", True),
])
def test_the_follow_up_is_the_resident_s_own_words(text, found, when):
    parsed = {"raw_text": text, "actions": [{"type": "disposition", "destination": "home"}], "reasoning": {}}
    assert adopt(parsed) == found
    assert dated(parsed) is when


def test_only_a_discharge_home_and_only_what_is_missing():
    admitted = {"raw_text": "Lo hospitalizo en sala, control de signos vitales cada 4 horas",
                "actions": [{"type": "disposition", "destination": "ward"}], "reasoning": {}}
    assert adopt(admitted) == "" and "reassessment_target" not in admitted["reasoning"]
    stated = {"raw_text": "Lo envio a su casa con control en 48 horas. Reevaluo en 15 minutos la glicemia.",
              "actions": [{"type": "disposition", "destination": "home"}],
              "reasoning": {"reassessment_target": "la glicemia"}}
    assert adopt(stated) == "" and stated["reasoning"]["reassessment_target"] == "la glicemia"
    # "Mi prioridad es controlar la alergia" is not an appointment.
    assert phrase("Mi prioridad es controlar la alergia. La envio a su casa.") == ""
