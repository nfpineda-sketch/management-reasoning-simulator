"""A held order must not become a dead end, and one radiograph needs no surname.

Found by playing the pulmonary oedema case (faculty decisions 2026-09-20).
"Pídele una radiografía" was refused because the pattern demanded "de tórax",
and the four complete orders that followed were refused one after another with
"Name one supported order to replace that item" while the patient stayed at
218/116 with a saturation of 81%.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from family_parser import parse_family_actions
from pending_family_orders import complete_bundle, hold_incomplete_bundle

APP = str(Path(__file__).with_name("app.py"))


def actions(text):
    return parse_family_actions(text)["actions"]


@pytest.mark.parametrize("text", [
    "Pídele una radiografía.", "Pide una placa de tórax.", "Pide una radiografía portátil.",
    "Order an X-ray.", "Order a chest X-ray.", "Pide rx de tórax.",
])
def test_a_radiograph_with_no_region_is_the_chest_film(text):
    # It is the only radiograph in the build, and this is how it is asked for.
    assert actions(text) == [{"type": "diagnostic", "diagnostic": "chest_xray"}]


@pytest.mark.parametrize("text", [
    "Pide una radiografía de abdomen.",
    "Order an abdominal X-ray.",
])
def test_a_film_of_another_region_is_still_not_supported(text):
    assert actions(text)[0]["type"] == "clarification"


def test_the_abdominal_ct_is_untouched():
    assert actions("Pide una TAC de abdomen.") == [{"type": "diagnostic", "diagnostic": "abdominal_ct"}]


def held_bundle():
    parsed = parse_family_actions(
        "Conéctalo a BiPAP 14/8 con FiO2 60% y pásale nitroglicerina 60 mcg/min IV. "
        "Pídele una resonancia magnética."
    )
    pending = hold_incomplete_bundle(parsed)
    assert pending, parsed
    return pending


def test_a_replacement_still_completes_the_held_bundle():
    resolved = complete_bundle(held_bundle(), "Radiografía de tórax.")
    kinds = [a["type"] for a in resolved["parsed"]["actions"]]
    assert kinds == ["niv", "nitroglycerin", "diagnostic"]


def test_cancel_still_drops_the_item_and_keeps_the_rest():
    # "Cancela" alone is caught earlier, by the app's own cancel path; this is
    # the bundle's own branch, which keeps everything else in the turn.
    resolved = complete_bundle(held_bundle(), "cancel")
    assert [a["type"] for a in resolved["parsed"]["actions"]] == ["niv", "nitroglycerin"]


def test_a_new_complete_order_supersedes_the_held_one():
    # The resident moved on. The turn runs instead of being refused again.
    resolved = complete_bundle(held_bundle(), "Dale furosemida 40 mg IV. Reevalúa en 30 minutos.")
    assert resolved == {"superseded": True}


def test_an_answer_that_is_not_an_order_is_still_a_question():
    assert complete_bundle(held_bundle(), "No sé.")["clarification"].startswith("Name one supported order")


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


def test_the_discarded_order_is_named_and_the_new_one_runs(edema):
    at = edema
    submit(at, "Edema pulmonar agudo por poscarga, porque el ventrículo no eyecta. Prioridad: descargar "
               "el ventrículo. Conéctalo a BiPAP 14/8 con FiO2 60% y pídele una resonancia magnética. "
               "Espero que suba la saturación. Reevalúa en 10 minutos saturación y presión arterial.")
    assert [e["kind"] for e in at.session_state.events][-1] == "clarification"
    submit(at, "Prefiero tratar primero, porque el trabajo respiratorio manda. Prioridad: descargar. "
               "Pásale nitroglicerina 60 mcg/min IV. Espero que suba la saturación. Reevalúa en 10 "
               "minutos saturación y presión arterial.")
    texts = [e["text"] for e in at.session_state.events]
    discarded = next(t for t in texts if "discarded to run this one" in t)
    assert "BiPAP 14/8" in discarded and "None of it was administered." in discarded
    assert any("Nitroglycerin start at 60 mcg/min" in t for t in texts)
    assert at.session_state.state["treatments"]["nitroglycerin"] is True
    assert at.session_state.state["treatments"]["niv"] is False
