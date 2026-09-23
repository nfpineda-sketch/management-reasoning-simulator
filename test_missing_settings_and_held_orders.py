"""What the engine asks for when something is missing, and what it says it is holding.

Found by playing the pulmonary oedema case in Spanish (faculty decisions of
2026-09-20). An order for CPAP 8 cm H2O with nitroglycerin was held with the
single line "Specify NIV expiratory pressure and FiO₂": the expiratory pressure
had in fact been given, the FiO₂ was the only gap, and the nitrate disappeared
without a word. So a message now names only what is missing, an NIV order
without a stated FiO₂ runs at 100% and says so, and a held turn declares the
rest of itself wherever the hold comes from — the parser or the engine.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from family_engine import NIV_ASSUMED_FIO2, _validate
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


def check(text, family="pulmonary_edema"):
    state = {
        "engine_family": family, "family_state": {},
        "observable": {"pulse_present": True, "mental_status": "Alert", "rhythm": "AF"},
        "encounter_spec": {"clinical_case": {"investigations": {}}},
    }
    return _validate(state, parse_family_actions(text))


def test_niv_without_a_stated_fio2_runs_at_full_oxygen():
    actions, error = check("Start CPAP 8 cm H2O and nitroglycerin 40 mcg/min IV.")
    assert error is None
    niv = next(a for a in actions if a["type"] == "niv")
    assert niv["epap_cmh2o"] == 8.0
    assert niv["fio2_percent"] == float(NIV_ASSUMED_FIO2) == 100.0
    assert niv["fio2_assumed"] is True
    # The nitrate in the same order is no longer lost to the missing FiO₂.
    assert [a["type"] for a in actions] == ["niv", "nitroglycerin"]


def test_a_stated_fio2_is_never_overwritten():
    actions, error = check("Start BiPAP 16/8 with FiO2 40%.")
    assert error is None
    niv = actions[0]
    assert niv["fio2_percent"] == 40.0 and not niv.get("fio2_assumed")


@pytest.mark.parametrize("text, expected, family", [
    # Only the gap is named, never the parameter that was given.
    ("Start CPAP with FiO2 60%.", "Specify the NIV expiratory pressure in cm H₂O, from 0 to 20.", "pulmonary_edema"),
    ("Give normal saline IV.", "Confirm the bolus volume in mL, up to 3000 mL per order.", "pulmonary_edema"),
    ("Give 1000 mL of fluid IV.", "Which crystalloid would you like to give (for example, normal saline or LR)?", "pulmonary_edema"),
    ("Perform synchronized cardioversion.", "Specify the cardioversion energy in joules, from 1 to 360.", "generated"),
    ("Intubate with FiO2 100% and PEEP 5.", "Specify the ventilator mode.", "asthma"),
    ("Intubate with volume control, PEEP 5 cm H2O.", "Specify the ventilator FiO₂ as a percentage.", "asthma"),
    ("Intubate.", "Specify the ventilator mode, FiO₂ as a percentage and PEEP in cm H₂O.", "asthma"),
    ("Give heparin 5000 units.", "Specify the route.", "pulmonary_embolism"),
    ("Give heparin IV.", "Specify the dose and the dose units.", "pulmonary_embolism"),
])
def test_the_message_names_only_what_is_missing(text, expected, family):
    actions, error = check(text, family)
    assert error == expected, error
    assert actions is None


@pytest.fixture
def edema(monkeypatch):
    from test_curriculum_app import authored_replay_fixture
    authored_replay_fixture(monkeypatch)
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["APP_PASSWORD"] = "test-shared-password"
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert not at.exception
    for _ in range(40):
        next(b for b in at.button if b.label == "Begin Encounter").click().run()
        assert not at.exception
        if at.session_state.state.get("engine_family") == "pulmonary_edema":
            return at
        next(b for b in at.button if b.label == "Reset scenario").click().run()
    pytest.skip("the challenge did not draw the pulmonary oedema family")


def submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(i for i in at.text_area if i.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception


REASONED = (" Priority: unload the ventricle and support oxygenation. I expect the saturation to rise "
            "and the work of breathing to fall. Reassess in 10 minutes saturation, blood pressure and "
            "work of breathing.")
MODEL = "Acute pulmonary oedema from afterload redistribution, because the ventricle cannot eject against that pressure."


def test_the_assumed_fio2_is_declared_in_the_record(edema):
    at = edema
    submit(at, MODEL + " Start CPAP 8 cm H2O and nitroglycerin 40 mcg/min IV." + REASONED)
    updates = [e["text"] for e in at.session_state.events if e["kind"] == "clinical_update"]
    assert updates, [e["kind"] for e in at.session_state.events]
    assert "FiO₂ 100% (assumed; titrate as needed)" in updates[-1]
    assert "Nitroglycerin start at 40 mcg/min" in updates[-1]


def test_a_turn_held_by_the_engine_declares_what_it_holds(edema):
    at = edema
    submit(at, MODEL + " Start CPAP with FiO2 60% and nitroglycerin 40 mcg/min IV, and order POCUS and lactate." + REASONED)
    held = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"]
    assert held, [e["kind"] for e in at.session_state.events]
    text = held[-1]
    assert "ORDER HELD — CLARIFICATION REQUIRED" in text
    for item in ("CPAP", "start nitroglycerin 40 mcg/min", "POCUS", "Lactate"):
        assert item in text, (item, text)
    assert "Specify the NIV expiratory pressure in cm H₂O, from 0 to 20." in text
    assert at.session_state.state["sim_time"] == 0


def test_one_incomplete_order_alone_is_not_dressed_as_a_held_bundle(edema):
    # Nothing else was at stake, so the engine's own question stands by itself.
    at = edema
    submit(at, MODEL + " Start CPAP with FiO2 60%." + REASONED)
    held = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"]
    assert held[-1] == "Specify the NIV expiratory pressure in cm H₂O, from 0 to 20."


# These two turns state the working model and the reassessment and leave out the
# expectation, so the gate still fires. Until 2026-09-23 they also left out the
# management priority, which was enough on its own to hold an order that named
# everything else; it no longer is, and the gate is exercised here by a gap the
# resident really left.
HELD_TURN = ("El paciente está hipoperfundido, porque el llene está prolongado. "
             "Pásale 1000 mL de suero fisiológico IV{extras}. "
             "Reevalúa en 20 minutos presión arterial.")


def test_the_reasoning_gate_names_the_investigations_it_holds(edema):
    # The two holds must describe a turn the same way. The gate used to list the
    # interventions only, so a resident who also ordered tests saw half the turn.
    at = edema
    submit(at, HELD_TURN.format(extras=" y pídele un lactato y una radiografía"))
    held = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"]
    assert held, [e["kind"] for e in at.session_state.events]
    text = held[-1]
    assert "ORDER HELD — REASONING REQUIRED" in text
    assert "1000 mL normal saline" in text
    assert "Lactate" in text and "Chest X-ray" in text
    assert at.session_state.state["sim_time"] == 0


def test_a_turn_with_no_investigations_still_reads_cleanly(edema):
    at = edema
    submit(at, HELD_TURN.format(extras=""))
    text = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"][-1]
    assert "I understood: **1000 mL normal saline**." in text


def test_a_stated_priority_is_no_longer_what_holds_an_order(edema):
    """The order that was held for a heading it did not need.

    The resident names the problem, the order, the expectation and the
    reassessment. Nothing here says the word "prioridad", and until 2026-09-23
    that alone stopped the encounter.
    """
    at = edema
    submit(at, "El paciente está hipoperfundido, porque el llene está prolongado. Pásale 1000 mL de "
               "suero fisiológico IV. Espero que suba la presión. Reevalúa en 20 minutos presión arterial.")
    held = [e["text"] for e in at.session_state.events if e["kind"] == "clarification"]
    assert not [text for text in held if "REASONING REQUIRED" in text], held
    assert at.session_state.state["sim_time"] > 0
    # What was missing is still recorded where the faculty reads it.
    gate = at.session_state.management_trace[-1]["reasoning_gate"]
    assert gate["status"] == "complete"
    assert gate["noted"] == ["management_priority"]
