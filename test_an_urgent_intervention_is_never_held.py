"""An urgent intervention runs without being held; its reasoning may come afterwards.

Faculty decision 12 of 2026-09-25 ("Procedimientos urgentes: opción B"). The
manoeuvre is executed at once; the categories the resident stated with it and
those they did not are recorded; the explanation may be completed later and is
then marked retrospective, with the minute it was written. Nothing reconstructs
a working model the resident never expressed. The same holds for every urgent
intervention, not only trauma.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import urgent_interventions
from account_store import AccountStore
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


@pytest.mark.parametrize("text, urgent", [
    ("Ventilo con bolsa mascarilla con O2 100%", True),
    ("Descompresion con aguja del hemitorax derecho", True),
    # Prepared procedures and medicines keep the four: an elective cardioversion
    # of a stable atrial fibrillation is not urgent (regression v0.8.14).
    ("Intuba en secuencia rapida con ketamina 2 mg/kg y rocuronio 1.2 mg/kg", False),
    ("Cardioversion sincronizada 100 J", False),
    ("Doy naloxona 0.4 mg ev", False),
])
def test_what_counts_as_urgent(text, urgent):
    assert urgent_interventions.is_urgent(parse_family_actions(text)) is urgent


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
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception


def test_the_manoeuvre_runs_and_records_what_was_not_stated(opioid):
    at = opioid
    submit(at, "Creo que es una intoxicacion por opioides, porque tiene miosis y FR 8.")
    submit(at, "Ventilo con bolsa mascarilla con O2 100%")
    assert not at.session_state["pending_reasoning"]
    entry = at.session_state["management_trace"][-1]
    assert any(s.get("type") == "bag_mask" for s in entry["action_summaries"])
    gate = entry["reasoning_gate"]
    assert gate["status"] == "urgent_unheld"
    assert {"working_model", "expected_effect", "reassessment_target"} <= set(gate["noted"])
    # The interpretation written in the entry before is not carried into this one.
    assert not entry["reasoning"].get("problem_representation")


def test_the_explanation_afterwards_is_marked_retrospective(opioid):
    at = opioid
    submit(at, "Ventilo con bolsa mascarilla con O2 100%")
    expander = next(e for e in at.expander if e.label.startswith("Explain an urgent decision afterwards"))
    assert expander
    fields = {a.label: a for a in at.text_area}
    fields["What do you think is going on?"].set_value("Depresion respiratoria por opioides")
    fields["What will you check, and when?"].set_value("FR y saturacion")
    next(b for b in at.button if b.label == "Save retrospective explanation").click().run()
    assert not at.exception
    entry = at.session_state["management_trace"][-1]
    reasoning = entry["reasoning"]
    assert reasoning["problem_representation"] == "Depresion respiratoria por opioides"
    assert reasoning["slot_provenance"]["problem_representation"] == "retrospective"
    assert entry["retrospective"]["fields"] == ["problem_representation", "reassessment_target"]
    assert entry["retrospective"]["written_at_min"] >= entry["decision_time_min"]


def test_a_medicine_that_is_not_urgent_is_still_asked_about(opioid):
    at = opioid
    submit(at, "Doy naloxona 0.4 mg ev")
    assert at.session_state["pending_reasoning"]
