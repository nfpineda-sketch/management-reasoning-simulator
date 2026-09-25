"""A medicine the simulator does not model is the resident's decision, never a dose.

Faculty decision 3 of 2026-09-25 ("Medicamentos sin efecto modelado: mantener
A, mejorando el análisis"). An antihistamine, a benzodiazepine, an antiemetic
or an adrenaline auto-injector is recognised and not executed. It is recorded
as "indicated by the resident; execution/effect not modelled" so that whoever
evaluates can read it as a decision -- an adjunct chosen, another treatment
omitted -- without anything being marked as given. A prescription for home is a
prescription. One phrase used to say all of this and also cover conditional
plans and advice; each now says what it is.
"""
import json
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rubric_screening
import unexecuted_items
from account_store import AccountStore
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


def details(text):
    return parse_family_actions(text)["future_details"]


@pytest.mark.parametrize("text, kind, category", [
    ("Doy clorfenamina 10 mg ev", "not_modelled", "antihistamine"),
    ("Doy lorazepam 1 mg vo", "not_modelled", "benzodiazepine"),
    ("Doy ondansetron 4 mg ev", "not_modelled", "antiemetic"),
    ("Le indico autoinyector al alta", "prescription", "adrenaline_autoinjector"),
    ("Indico loratadina 10 mg al dia al alta", "prescription", "antihistamine"),
])
def test_each_unmodelled_medicine_says_what_it_is(text, kind, category):
    [item] = details(text)
    assert (item["kind"], item["category"]) == (kind, category)


@pytest.mark.parametrize("text, kind", [
    ("Lo doy de alta y regresar si tiene fiebre", "advice"),
    ("Le doy colacion oral y la doy de alta si la tolera", "conditional"),
])
def test_plans_and_advice_are_not_called_unmodelled(text, kind):
    [item] = details(text)
    assert item["kind"] == kind


def test_the_page_says_indicated_or_prescribed_and_never_given():
    parsed = parse_family_actions("Doy clorfenamina 10 mg ev y hidrocortisona 200 mg ev. "
                                  "Le indico autoinyector al alta.")
    said, unclassified = unexecuted_items.messages(parsed)
    assert unclassified == []
    assert any(line.startswith("Indicated and recorded as your decision: doy clorfenamina 10 mg ev")
               and "not modelled" in line for line in said)
    assert any(line.startswith("Prescription for home recorded: indico autoinyector al alta") for line in said)
    assert not any("administered" in line.lower() for line in said)


def _trace_entry(text, minute, executed=()):
    parsed = parse_family_actions(text)
    return {"execution_status": "executed", "decision_time_min": minute, "response_time_min": minute + 5,
            "learner_input": text, "interpreted_action": parsed["actions"],
            "action_summaries": [{"type": kind, "label": kind} for kind in executed],
            "recognized_future_actions": parsed["recognized_future_actions"],
            "future_details": parsed["future_details"]}


def _record(*entries):
    return {"payload": {"session": {"management_trace": list(entries)}}}


def test_an_antihistamine_alone_without_adrenaline_is_the_faculty_s_reading():
    record = _record(_trace_entry("Creo que es una alergia. Doy clorfenamina 10 mg ev. Reevaluo en 10 minutos.", 0))
    row = {r["event_id"]: r for r in rubric_screening.screen_events(record, "anaphylaxis_29f")}[
        "anaphylaxis_antihistamine_only"]
    assert row["status"] == "reading"
    text = " ".join(fact["en"] for fact in row["facts"])
    assert "Indicated by the resident, with no administration or effect modelled: an antihistamine" in text


def test_an_indicated_antihistamine_beside_an_executed_steroid_is_shown_and_not_given():
    record = _record(_trace_entry("Doy clorfenamina 10 mg ev y hidrocortisona 200 mg ev. Reevaluo en 10 minutos.",
                                  0, executed=("steroid",)))
    row = {r["event_id"]: r for r in rubric_screening.screen_events(record, "anaphylaxis_29f")}[
        "anaphylaxis_antihistamine_only"]
    assert row["status"] == "met"
    assert any("antihistamine" in fact["en"] and "no administration" in fact["en"] for fact in row["facts"])


def test_the_model_reads_the_indications_as_decisions():
    record = _record(_trace_entry("Doy lorazepam 1 mg vo. Reevaluo en 30 minutos.", 0))
    sent = rubric_screening.for_model(rubric_screening.screening(record, "acs_66f_nonst"))
    [item] = sent["indicated_not_modelled"]
    assert item["evidence_ref"] == "trace:0" and "a benzodiazepine" in item["fact"]


def test_an_older_record_without_kinds_is_read_the_same_way():
    entry = _trace_entry("Doy lorazepam 1 mg vo. Reevaluo en 30 minutos.", 0)
    entry.pop("future_details")
    [row] = rubric_screening.facts(_record(entry))["indicated"]
    assert row["category"] == "benzodiazepine" and row["prescription"] is False


# --- end to end ---------------------------------------------------------------------

@pytest.fixture
def anaphylaxis(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 1, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "anaphylaxis_29f")):
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


def test_the_encounter_records_the_indication_and_gives_nothing(anaphylaxis):
    at = anaphylaxis
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(
        "Creo que es una reaccion alergica, porque tiene rash y edema facial. Mi prioridad es la alergia. "
        "Doy clorfenamina 10 mg ev y hidrocortisona 200 mg ev. Espero que ceda el rash. Reevaluo en 10 "
        "minutos rash y PA.")
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception
    [entry] = at.session_state["management_trace"]
    assert [d["kind"] for d in entry["future_details"]] == ["not_modelled"]
    given = [s.get("type") for s in entry["action_summaries"]]
    assert "steroid" in given and not any("clorfenamina" in json.dumps(s) for s in entry["action_summaries"])
    said = [e["text"] for e in at.session_state["events"] if e.get("kind") == "prototype"]
    assert any(text.startswith("Indicated and recorded as your decision") for text in said)
