"""Phase 0 (0E, 0F): the resident can wait and look again, and a critical event ends the wait.

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§5.2-§5.4) found that
"Wait 20 minutes" was not understood, "reassess" took 0 minutes and printed the vital
signs from before a treatment under "After ...", an order for later ran at once, and no
event interrupted a turn: one 120-minute wait in the inferior STEMI reported the AV block
of minute 45 and the VF of minute 120 together, at the end.
"""
from copy import deepcopy

import pytest

import encounter_generator
import event_provenance
import family_engine
import time_semantics
from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine
from test_phase0_order_ledger import _encounter, submit


def _read(text):
    return time_semantics.apply(text, parse_family_actions(text))


def keep_waiting(state, result):
    """What a resident who keeps waiting after each interruption sees: the rest of the interval.

    For the tests whose subject is what a whole interval brings: a wait now stops at a
    critical event (0F), and the engine is step-invariant, so waiting out the rest reaches
    the same state as one uninterrupted wait did. Stops at an arrest (nothing more runs).
    Returns the summaries the further waits produced.
    """
    summaries = []
    while result.get("interrupted"):
        stop = result["interrupted"]
        left = int(stop["requested_until_min"]) - int(stop["minute"])
        if left <= 0:
            break
        result = family_engine.execute_family_bundle(state, {"actions": [{"type": "reassessment", "delay_min": left}]})
        if not result.get("executed"):
            break
        summaries += result["action_summaries"]
    return summaries


def _looks(parsed):
    return [a for a in parsed["actions"] if a.get("type") == "reassessment"]


def _state(challenge, family, variant):
    return encounter_generator.generate_encounter(challenge, load_engine()["INITIAL_STATE"], seed=17,
                                                  family_id=family, variant_id=variant)["state"]


# --- 0E: waiting ----------------------------------------------------------------------
@pytest.mark.parametrize("text, minutes", [
    ("Wait 20 minutes.", 20),
    ("Observe for 20 minutes.", 20),
    ("Let's wait 20 minutes and repeat the blood pressure.", 20),
    ("Wait half an hour.", 30),
    ("Observe for 2 hours.", 120),
    ("Esperar 20 minutos.", 20),
    ("Observar por 20 minutos y reevaluar.", 20),
    ("Observar media hora.", 30),
])
def test_a_wait_is_a_reassessment_after_its_minutes(text, minutes):
    parsed = _read(text)
    assert [a["delay_min"] for a in _looks(parsed)] == [minutes]
    assert not parsed.get("clarification")
    assert not [a for a in parsed["actions"] if a.get("type") == "clarification"]


def test_a_wait_longer_than_the_step_is_refused_and_explained_never_shortened():
    state = _state("R2-05", "gi_bleed", "gi_bleed_57m")
    result = family_engine.execute_family_bundle(state, _read("Wait 3 hours."))
    assert not result["executed"] and state["sim_time"] == 0
    assert "at most 120 minutes in one step" in result["clarification"]


# --- 0E: an immediate look --------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Reassess.", "Reassess now.", "Repeat vitals.", "Repeat the vital signs.", "Reevaluar.",
    "Repetir signos vitales.", "Repita la presión arterial.",
])
def test_reassess_without_a_number_is_a_look_at_the_bedside(text):
    parsed = _read(text)
    looks = _looks(parsed)
    assert len(looks) == 1 and looks[0]["immediate"] is True
    assert looks[0]["delay_min"] == time_semantics.BEDSIDE_LOOK_MIN > 0
    assert not parsed.get("future_details") and not parsed.get("recognized_future_actions")


def test_an_explicit_reassessment_keeps_its_interval():
    looks = _looks(_read("Give 1 L LR and reassess in 15 minutes."))
    assert [(a["delay_min"], a.get("immediate")) for a in looks] == [(15, None)]


def test_give_and_reassess_starts_the_treatment_and_looks_at_once_honestly():
    parsed = _read("Give 1 L LR and reassess.")
    state = _state("R2-05", "gi_bleed", "gi_bleed_57m")
    result = family_engine.execute_family_bundle(state, parsed)
    assert result["executed"] and result["elapsed_min"] == time_semantics.BEDSIDE_LOOK_MIN
    lead = time_semantics.update_lead(result, parsed, ["lactated Ringer's 1000 mL"])
    assert not lead.startswith("After ") and "2 minutes after the order" in lead


# --- 0E: later -------------------------------------------------------------------------
@pytest.mark.parametrize("text, minutes, kind", [
    ("Repeat ECG in 30 minutes.", 30, "diagnostic"),
    ("Recheck glucose in 15 minutes.", 15, "diagnostic"),
    ("Give aspirin 300 mg in 30 minutes.", 30, "aspirin"),
    ("Repeat troponin in 3 hours.", 180, "diagnostic"),
    ("Repetir ECG en 30 minutos.", 30, "diagnostic"),
    ("After 10 minutes give aspirin 300 mg PO.", 10, "aspirin"),
])
def test_an_order_for_later_never_runs_now(text, minutes, kind):
    parsed = _read(text)
    assert not [a for a in parsed["actions"] if a.get("type") == kind]
    plans = [p for p in parsed.get("ledger_plans") or [] if p["kind"] == "future_timed"]
    assert [p["in_min"] for p in plans] == [minutes]
    assert "not carried out in this pilot" in plans[0]["receipt"]


def test_a_volume_in_minutes_is_a_rate_and_the_rest_of_the_order_runs_now():
    assert [a["type"] for a in _read("Give 500 mL NS in 20 minutes.")["actions"]] == ["fluid"]
    parsed = _read("Give aspirin 300 mg now and repeat the ECG in 30 minutes.")
    assert [a["type"] for a in parsed["actions"]] == ["aspirin"]
    assert [p["in_min"] for p in parsed["ledger_plans"]] == [30]


# --- 0F: a critical event ends the wait -----------------------------------------------------
def test_a_long_wait_stops_at_the_first_critical_event():
    state = _state("R2-02", "acs", "acs_54m_inferior")
    result = family_engine.execute_family_bundle(state, _read("Reassess in 120 minutes."))
    stop = result["interrupted"]
    assert stop and stop["kind"] == "av_block" and stop["minute"] == state["sim_time"] == result["elapsed_min"]
    assert stop["minute"] < 120 and stop["requested_until_min"] == 120
    # A scripted course, declared as such: never the resident's to prevent here (0H).
    assert stop["cause_class"] == "SCRIPTED_NATURAL_HISTORY"
    assert stop["preventability"] == "NOT_PREVENTABLE_IN_SIMULATOR"
    assert [event["kind"] for event in result["events"]] == ["av_block"]
    assert state["observable"]["rhythm"] == "Complete AV block"
    # The next wait goes on from there, and stops at the next one.
    again = family_engine.execute_family_bundle(state, _read("Reassess in 120 minutes."))
    assert again["interrupted"]["kind"] == "ventricular_fibrillation"
    assert again["interrupted"]["severity"] == "terminal"
    assert state["observable"]["pulse_present"] is False


def test_a_wait_without_an_event_runs_its_whole_interval():
    state = _state("R2-05", "gi_bleed", "gi_bleed_57m")
    result = family_engine.execute_family_bundle(state, _read("Wait 30 minutes."))
    assert result["interrupted"] is None and result["elapsed_min"] == 30 == state["sim_time"]


def test_the_opioid_arrest_ends_the_wait_at_its_minute():
    state = _state("R1-06", "opioid", "opioid_35m")
    result = family_engine.execute_family_bundle(state, _read("Wait 60 minutes."))
    stop = result["interrupted"]
    assert stop and stop["kind"] == "cardiac_arrest" and stop["severity"] == "terminal"
    assert stop["minute"] < 60 and state["sim_time"] == stop["minute"]


def test_vital_sign_changes_stop_a_wait_only_when_severe_changed_and_persistent():
    watch = event_provenance.Watch({"observable": {"sbp": 90, "spo2": 95, "pulse_present": True}})
    one = watch.step({"sim_time": 1, "observable": {"sbp": 65, "spo2": 95, "pulse_present": True}})
    assert one == []  # one minute is not yet a collapse
    two = watch.step({"sim_time": 2, "observable": {"sbp": 64, "spo2": 95, "pulse_present": True}})
    assert [e["kind"] for e in two] == ["circulatory_collapse"]
    assert two[0]["preventability"] == "UNKNOWN"
    steady = event_provenance.Watch({"observable": {"sbp": 68, "spo2": 84, "pulse_present": True}})
    for minute in range(1, 6):  # low from the start, and not falling: not a new event
        assert steady.step({"sim_time": minute, "observable": {"sbp": 66, "spo2": 83, "pulse_present": True}}) == []


def test_waits_are_deterministic_on_replay():
    runs = []
    for _ in range(2):
        state = _state("R2-02", "acs", "acs_54m_inferior")
        results = [family_engine.execute_family_bundle(state, _read(text))
                   for text in ("Wait 20 minutes.", "Reassess.", "Reassess in 120 minutes.")]
        runs.append((deepcopy(state["observable"]), state["sim_time"],
                     [(r["elapsed_min"], r["interrupted"], r["events"]) for r in results]))
    assert runs[0] == runs[1]


# --- the real page -------------------------------------------------------------------------
@pytest.fixture
def acs(tmp_path, monkeypatch):
    return _encounter(tmp_path, monkeypatch, "acs_54m_inferior", "R2-02")


def _texts(at):
    return [str(event.get("text") or "") for event in at.session_state["events"]]


def test_the_page_lets_time_pass_looks_again_and_stops_at_the_event(acs):
    at = acs
    submit(at, "Wait 20 minutes.")
    assert at.session_state["state"]["sim_time"] == 20
    submit(at, "Repeat the vital signs.")
    assert at.session_state["state"]["sim_time"] == 20 + time_semantics.BEDSIDE_LOOK_MIN
    assert _texts(at)[-1].startswith("On reassessment at the bedside, 2 minutes later")
    submit(at, "Repeat ECG in 30 minutes.")
    assert at.session_state["state"]["sim_time"] == 22
    later = [o for o in at.session_state["order_ledger"] if o.get("limitation") == "unsupported_future_execution"]
    assert later and later[0]["fate"] == "RECORDED_NOT_MODELLED"
    assert any(text.startswith('Not done now: "Repeat ECG in 30 minutes"') for text in _texts(at))
    assert not any("Please specify a question" in text for text in _texts(at))
    submit(at, "Reassess in 120 minutes.")
    entry = at.session_state["management_trace"][-1]
    assert entry["interrupted"]["kind"] == "av_block"
    assert at.session_state["state"]["sim_time"] == entry["interrupted"]["minute"] < 22 + 120
    assert any(text.startswith("The wait was interrupted after") for text in _texts(at))
    assert [event["cause_class"] for event in entry["events"]] == ["SCRIPTED_NATURAL_HISTORY"]
