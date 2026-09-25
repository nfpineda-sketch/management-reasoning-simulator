"""A dose written as a solution or per kilogram, turned into a dose and shown.

Faculty decision 2 of 2026-09-25. "Glucosa al 30%, 50 mL" is 15 g and is given
as such, with the conversion in view. A dose per kilogram is accepted for the
medicines the engine supports and becomes a dose with the patient's weight;
when neither the case nor the resident has given one, the whole order is kept
and only the weight is asked for. Asking is the reader's question, not a
clinical minute: the clock does not move while it waits.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import weight_based_doses
from account_store import AccountStore
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def start(tmp_path, monkeypatch, variant, challenge):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 2, int(time.time())))
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
    widget(at.button, "Begin Encounter").click().run()
    assert at.session_state["state"]["encounter_spec"]["variant_id"] == variant
    return at


def submit(at, text):
    widget(at.radio, "Encounter").set_value("Treat").run()
    widget(at.text_area, "Enter your clinical reasoning and/or actions").set_value(text)
    widget(at.button, "Submit").click().run()
    assert not at.exception


def labels(at):
    return [s.get("label") for entry in at.session_state["management_trace"]
            for s in entry.get("action_summaries", [])]


GLUCOSE = ("Creo que es una hipoglicemia, porque esta somnoliento con glicemia baja. Mi prioridad es "
           "corregirla. Doy glucosa al 30% 50 ml ev. Espero que despierte. Reevaluo en 10 minutos "
           "conciencia y glicemia.")
ANTICOAGULATE = ("Creo que es un tromboembolismo pulmonar, porque tiene disnea subita y FC 124. Mi prioridad "
                 "es anticoagular. Doy enoxaparina 1 mg/kg sc. Espero que no progrese. Reevaluo en 20 "
                 "minutos saturacion y FC.")


def test_a_glucose_solution_is_given_as_its_grams(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "hypoglycemia_28m", "R1-06")
    submit(at, GLUCOSE)
    assert not at.session_state["pending_action"]
    assert "Glucose 15 g IV (30% × 50 mL)" in labels(at)


def test_a_dose_per_kilogram_asks_only_for_the_weight_and_keeps_the_order(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "pulmonary_embolism_33f", "R2-02")
    minute = at.session_state["state"]["sim_time"]
    submit(at, ANTICOAGULATE)
    pending = at.session_state["pending_action"]
    assert pending and pending["type"] == "family_bundle"
    # Nothing ran and the clock did not move while the reader asked.
    assert at.session_state["state"]["sim_time"] == minute
    assert not [s for s in labels(at) if s and "noxaparin" in s]
    submit(at, "60 kg")
    assert not at.session_state["pending_action"]
    given = [s for s in labels(at) if s and "noxaparin" in s]
    assert given and "(1 mg/kg × 60 kg)" in given[0] and "60 mg" in given[0], given
    assert at.session_state["state"]["stated_weight"]["kg"] == 60.0
    # The next dose per kilogram uses the weight already given, without asking.
    submit(at, "Mi prioridad es completar la anticoagulacion. Doy heparina 80 UI/kg ev. Espero que no "
               "progrese. Reevaluo en 20 minutos saturacion y FC.")
    assert not at.session_state["pending_action"]
    assert any("80 units/kg × 60 kg" in (s or "") for s in labels(at))


def test_a_weight_written_with_the_order_is_used(tmp_path, monkeypatch):
    at = start(tmp_path, monkeypatch, "pulmonary_embolism_33f", "R2-02")
    submit(at, ANTICOAGULATE.replace("sc.", "sc, pesa 62 kg."))
    assert not at.session_state["pending_action"]
    assert any("(1 mg/kg × 62 kg)" in (s or "") for s in labels(at))


@pytest.mark.parametrize("text, kind, field, value", [
    ("Doy enoxaparina 1 mg/kg sc", "anticoagulation", "dose_mg_per_kg", 1.0),
    ("Doy heparina 80 UI/kg ev", "anticoagulation", "dose_units_per_kg", 80.0),
    ("Give prednisone 1 mg/kg PO", "steroid", "dose_mg_per_kg", 1.0),
    ("Doy sulfato de magnesio 40 mg/kg ev", "magnesium", "dose_mg_per_kg", 40.0),
    ("Doy glucosa 0.5 g/kg ev", "dextrose", "dose_g_per_kg", 0.5),
])
def test_the_supported_doses_per_kilogram(text, kind, field, value):
    [action] = parse_family_actions(text)["actions"]
    assert action["type"] == kind and action[field] == value


@pytest.mark.parametrize("text, grams, basis", [
    ("Doy glucosa al 30% 50 ml ev", 15.0, "30% × 50 mL"),
    ("Doy 50 ml de glucosa al 50% ev", 25.0, "50% × 50 mL"),
    ("Doy D50 50 ml ev", 25.0, "50% × 50 mL"),
])
def test_a_glucose_solution_is_its_grams(text, grams, basis):
    [action] = parse_family_actions(text)["actions"]
    assert (action["dose_g"], action["dose_basis"]) == (grams, basis)


def test_what_cannot_be_converted_is_still_asked():
    # An ampoule's volume is not written, so its grams are not guessed.
    [action] = parse_family_actions("Doy 2 ampollas de glucosa al 30% ev")["actions"]
    assert action["dose_g"] is None
    # A rate per kilogram of a drug the engine does not carry is still refused.
    assert parse_family_actions("Start dopamine 5 mcg/kg/min")["actions"][0]["type"] == "clarification"


@pytest.mark.parametrize("reply, kg", [("60 kg", 60.0), ("pesa 60 kg", 60.0), ("60", 60.0),
                                       ("unos 75 kilos", 75.0), ("weighs 80 kg", 80.0), ("3 kg", None),
                                       ("no se", None)])
def test_the_weight_as_it_is_answered(reply, kg):
    assert weight_based_doses.from_reply(reply) == kg


def test_a_case_weight_comes_first_and_the_resident_s_is_kept():
    state = {"encounter_spec": {"clinical_case": {"patient": {"weight_kg": 70}}}}
    assert weight_based_doses.weight_of(state) == (70.0, "case")
    parsed = {"raw_text": "Doy enoxaparina 1 mg/kg sc", "actions": parse_family_actions("Doy enoxaparina 1 mg/kg sc")["actions"]}
    assert weight_based_doses.resolve(parsed, state) == []
    assert parsed["actions"][0]["dose"] == 70.0 and parsed["actions"][0]["weight_source"] == "case"
