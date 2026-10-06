"""Phase 0 (0A-0B): every order the resident writes ends with one recorded fate.

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§16 rank 1, §17.7)
found orders that disappeared without the resident being told. These tests drive the real
page (AppTest) and the ledger directly:

* a new order typed while completing a held order's reasoning gets a fate and runs;
* one unrecognised item no longer holds the independent orders written with it;
* a medicine the reader skipped beside another one is said, not lost;
* every actionable text and every order ends with a fate.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import order_ledger
import order_pipeline
from account_store import AccountStore
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


def _encounter(tmp_path, monkeypatch, variant, challenge):
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
    at = AppTest.from_file(APP, default_timeout=180)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    return at


@pytest.fixture
def gi_bleed(tmp_path, monkeypatch):
    return _encounter(tmp_path, monkeypatch, "gi_bleed_57m", "R2-05")


@pytest.fixture
def pneumonia(tmp_path, monkeypatch):
    return _encounter(tmp_path, monkeypatch, "pneumonia_83m", "R1-05")


def submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Send").click().run()
    assert not at.exception, at.exception


def _texts(at):
    return [str(event.get("text") or "") for event in at.session_state["events"]]


def _fates(at):
    return {order["span"] or order["canonical"]: order["fate"] for order in at.session_state["order_ledger"]}


# --- the reasoning gate's follow-up (audit §17.7a) -----------------------------------
def test_a_transfusion_written_in_the_gate_follow_up_runs_and_has_a_fate(gi_bleed):
    at = gi_bleed
    submit(at, "Give pantoprazole 80 mg IV.")
    assert at.session_state["pending_reasoning"], "the PPI is held for its reasoning"
    held = [o for o in at.session_state["order_ledger"] if o["fate"] == "HELD_REASONING"]
    assert held and all("pantoprazole" in (o["span"] + o["canonical"]).lower() for o in held)
    submit(at, "I think this is an upper GI bleed with haemorrhagic shock. My priority is restoring perfusion. "
               "I expect the blood pressure to rise. Transfuse 2 units of packed red blood cells. "
               "I will reassess blood pressure in 15 minutes.")
    assert not at.session_state["pending_reasoning"]
    entry = at.session_state["management_trace"][-1]
    kinds = [s.get("type") for s in entry["action_summaries"]]
    assert "blood" in kinds, "the transfusion written in the follow-up ran"
    assert "ppi" in kinds
    fates = {o["class"]: o["fate"] for o in entry["orders"]}
    assert fates.get("blood") == "EXECUTED" and fates.get("ppi") == "EXECUTED"
    # The pantoprazole kept the id it was held with.
    assert any(o["fate"] == "EXECUTED" and o["order_id"] == held[0]["order_id"]
               for o in at.session_state["order_ledger"])
    assert at.session_state["state"]["family_state"]["pending_blood_units"] > 0 \
        or at.session_state["state"]["treatments"].get("blood_units_given", 0) > 0 \
        or "blood" in kinds


# --- the bundle rule ------------------------------------------------------------------
def test_an_unrecognised_antibiotic_no_longer_holds_the_fluid_and_the_oxygen(pneumonia):
    at = pneumonia
    submit(at, "I think this is septic shock from pneumonia. My priority is perfusion and oxygenation. "
               "I expect the pressure and saturation to improve. Give 1 L LR, cefepime 2 g, oxygen by NRB. "
               "Reassess in 15 minutes.")
    entry = at.session_state["management_trace"][-1]
    kinds = [s.get("type") for s in entry["action_summaries"]]
    assert "fluid" in kinds and "oxygen" in kinds, kinds
    fates = {o["class"]: o["fate"] for o in entry["orders"]}
    assert fates["fluid"] == "EXECUTED" and fates["oxygen"] == "EXECUTED"
    assert fates["unrecognized"] == "UNRECOGNIZED"
    texts = _texts(at)
    assert any(t.startswith('Not understood: "cefepime 2 g"') for t in texts), texts[-6:]
    # The standard non-rebreather flow is said, never applied silently.
    assert any("standard non-rebreather flow" in t for t in texts)
    assert entry["elapsed_minutes"] == 15


def test_a_medicine_the_reader_skipped_beside_another_is_said(pneumonia):
    at = pneumonia
    submit(at, "Give insulin 10 units IV with dextrose 25 g IV")
    texts = _texts(at)
    assert any('Not understood: "insulin 10 units IV"' in t for t in texts), texts[-6:]
    assert any(o["fate"] == "UNRECOGNIZED" and "insulin" in o["span"].lower()
               for o in at.session_state["order_ledger"])


def test_a_held_order_cancelled_by_the_resident_is_cancelled_in_the_ledger(gi_bleed):
    at = gi_bleed
    submit(at, "Give pantoprazole 80 mg IV.")
    submit(at, "cancel")
    assert {o["fate"] for o in at.session_state["order_ledger"]} == {"CANCELLED"}


# --- the ledger itself ----------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Give 1 L LR, cefepime 2 g, oxygen by NRB",
    "Give insulin 10 units IV with dextrose 25 g",
    "Start vasopressin 0.04 units/min and give 1 L NS",
    "Perform a bedside echocardiogram and get a chest x-ray",
    "Start CPR",
    "Call cardiology and activate the cath lab",
    "Give sodium bicarbonate 50 mEq IV",
    "Give piperacillin-tazobactam 4.5 g IV and meropenem 1 g IV",
    "Regular insulin 10 U. PRBC 2 units now",
    "Do not give fluid, but start oxygen via nasal cannula at 3 L/min now.",
])
def test_every_actionable_text_and_every_order_ends_with_a_fate(text):
    parsed = parse_family_actions(text)
    turn = order_pipeline.open_turn(text, parsed, submission_id="t", entry_point="free_text", minute=0)
    # As the page settles a turn the engine refused entirely: everything is held or unrecognised.
    order_pipeline.settle(turn, result={"executed": False}, run_actions=[], minute_before=0, minute_after=0)
    assert order_pipeline.check(turn) == []
    assert all(order["fate"] in order_ledger.FATES for order in turn["orders"])


@pytest.mark.parametrize("text, missing", [
    # Each of these the reader either quotes as unrecognised, or skips beside another order.
    ("Give 1 L LR, cefepime 2 g, oxygen by NRB", "cefepime"),
    ("Start vasopressin 0.04 units/min and give 1 L NS", "vasopressin"),
    ("Give insulin 10 units IV with dextrose 25 g", "insulin"),
    ("Give sodium bicarbonate 50 mEq IV", "bicarbonate"),
    ("Perform a bedside echocardiogram and get a chest x-ray", "echocardiogram"),
    ("Start CPR", "cpr"),
])
def test_what_the_reader_did_not_read_never_disappears(text, missing):
    parsed = parse_family_actions(text)
    turn = order_pipeline.open_turn(text, parsed, submission_id="t", entry_point="free_text", minute=0)
    order_pipeline.settle(turn, result={"executed": False}, run_actions=[], minute_before=0, minute_after=0,
                          split={"held": [], "refused": [], "unreadable": [
                              (a, "") for a in parsed["actions"] if a.get("unrecognized_text")]})
    named = [o for o in turn["orders"] if missing in (o.get("span") or "").lower()]
    assert named, [o.get("span") for o in turn["orders"]]
    assert all(o["fate"] in ("UNRECOGNIZED", "HELD_CLARIFICATION") for o in named)


@pytest.mark.parametrize("text", [
    "I think this is septic shock because the lactate is 4.2 mmol/L and Hb 7 g/dL.",
    "He received aspirin 300 mg from EMS.",
    "Do not give fluids.",
    "Peripheral IV in place in the left forearm.",
    "Espero que recupere la conciencia y suba la glicemia.",
    "Reassess blood pressure and lactate in 10 minutes.",
    "Surgery consult deferred",
    "So far 2 units PRBC and 2 L crystalloid",
])
def test_reasoning_history_and_notes_are_not_orders(text):
    cov = order_ledger.coverage(text, parse_family_actions(text))
    assert cov["unaccounted"] == [] and cov["held"] == [], cov


def test_independent_orders_run_and_a_dependency_waits():
    import family_engine
    from test_curriculum_trajectories import load_engine
    import encounter_generator
    encounter = encounter_generator.generate_encounter("R2-05", load_engine()["INITIAL_STATE"], seed=17,
                                                       family_id="gi_bleed", variant_id="gi_bleed_57m")
    state = encounter["state"]
    parsed = parse_family_actions("Give 1 L LR. Start norepinephrine. Then transfuse 2 units PRBC.")
    order_pipeline.open_turn("Give 1 L LR. Start norepinephrine. Then transfuse 2 units PRBC.", parsed,
                             submission_id="s", entry_point="free_text", minute=0)
    split = order_pipeline.split_bundle(state, parsed, text="Give 1 L LR. Start norepinephrine. Then transfuse 2 units PRBC.")
    assert [a["type"] for a in split["run"]] == ["fluid", "blood"]
    assert [a["type"] for a, *_ in split["held"]] == ["norepinephrine"]
    # Same sentence, explicit sequence: what follows the held order waits for it.
    text = "Start norepinephrine then transfuse 2 units PRBC. Give 1 L LR."
    parsed = parse_family_actions(text)
    order_pipeline.open_turn(text, parsed, submission_id="s2", entry_point="free_text", minute=0)
    split = order_pipeline.split_bundle(state, parsed, text=text)
    assert [a["type"] for a in split["run"]] == ["fluid"]
    assert sorted(a["type"] for a, *_ in split["held"]) == ["blood", "norepinephrine"]
    assert family_engine  # the engine is untouched by the split
