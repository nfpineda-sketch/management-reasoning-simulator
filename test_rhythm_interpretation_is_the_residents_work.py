"""The app must not name the rhythm for the resident.

The bedside monitor shows a rate and a sweeping lead II trace; the 12-lead is
acquired on request and carries only its acquisition time. Naming the rhythm in
the vitals panel, in every response after an order, or in the arrival narrative
hands over the interpretation the encounter exists to observe.

The rhythm stays in the engine, in the Management Trace and in the faculty
report, where naming it is a record of what happened rather than a shortcut.

No paid calls: the author client is a local stub.
"""
import ast
from pathlib import Path
import re

import pytest
from streamlit.testing.v1 import AppTest

from test_problem_launch import install_author

APP = str(Path(__file__).with_name("app.py"))
ROOT = Path(__file__).resolve().parent
RHYTHM_NAMES = ("sinus rhythm", "sinus tachycardia", "sinus bradycardia",
                "atrial fibrillation", "AF", "PEA", "ventricular tachycardia")


def names_a_rhythm(text):
    """Whole words only: "PEA" must not match inside "speaking"."""
    found = []
    for name in RHYTHM_NAMES:
        if re.search(r"\b" + re.escape(name) + r"\b", text, re.I):
            found.append(name)
    return found


@pytest.fixture
def encounter(tmp_path, monkeypatch):
    from account_store import AccountStore, hash_password
    install_author(monkeypatch)
    url = "sqlite:///" + str(tmp_path / "rhythm.sqlite3")
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("teacher", hash_password("local-test-password"))
    teacher = store.authenticate("teacher", "local-test-password")
    invite = store.create_invite(teacher, "resident", 1)
    token = store.register("rhythm-resident", "local-resident-password", invite)
    app = AppTest.from_file(APP, default_timeout=120)
    app.session_state["_account_token"] = token
    app.run()
    assert not app.exception
    next(b for b in app.button if b.label == "Begin Encounter").click().run()
    assert not app.exception
    return app


def visible_text(app):
    return "\n".join(str(item.value) for kind in ("markdown", "caption", "info", "subheader")
                     for item in app.get(kind))


def test_the_bedside_surface_never_names_the_rhythm(encounter):
    app = encounter
    rhythm = app.session_state.state["observable"]["rhythm"]
    # The engine still knows it; the resident has to read it off the trace.
    assert rhythm
    assert not names_a_rhythm(visible_text(app))
    assert not names_a_rhythm("\n".join(str(e["text"]) for e in app.session_state.events))


def test_the_response_card_after_an_order_never_names_the_rhythm(encounter):
    """The first version of this file only inspected the screen before any order.

    The card rendered after a reassessment still read "HR · RHYTHM: 121 · Sinus
    tachycardia", and a resident testing locally found it.
    """
    app = encounter
    app.text_area[0].set_value(
        "Acute pulmonary edema. My priority is oxygenation. Start oxygen 4 L/min nasal cannula. "
        "I expect SpO2 to rise. Reassess SpO2 in 5 minutes.")
    next(b for b in app.button if b.label == "Submit").click().run()
    assert not app.exception
    assert any(e["kind"] == "clinical_update" for e in app.session_state.events)
    rendered = visible_text(app)
    assert "HR · RHYTHM" not in rendered
    assert not names_a_rhythm(rendered), names_a_rhythm(rendered)
    # Still recorded, where naming it is a record rather than a shortcut.
    update = next(e for e in app.session_state.events if e["kind"] == "clinical_update")
    assert update["learner_vitals"].get("rhythm")


def test_the_vitals_panel_reports_a_rate_and_not_a_diagnosis():
    source = (ROOT / "app.py").read_text()
    # The line is now read in the presentation language (faculty decision 16),
    # which changes how it is written and not what it says.
    assert "st.write(_lang.say(f'HR: {o[\"hr\"]}/min'))" in source
    assert "{o[\"hr\"]}/min · {o[\"rhythm\"]}" not in source
    # Arrest is an interpretation too: report the finding, not the label.
    assert "organized electrical activity at {o[\"hr\"]}/min, no palpable pulse" in source
    assert "· {o[\"rhythm\"]}')" not in source


def test_the_response_after_an_order_reports_a_rate_and_not_a_rhythm():
    source = (ROOT / "app.py").read_text()
    tree = ast.parse(source)
    function = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == "format_clinical_update")
    body = ast.get_source_segment(source, function)
    assert "HR is {o[\"hr\"]}/min," in body
    assert "rhythm" not in body


def test_the_rhythm_strip_describes_the_trace_without_reading_it():
    source = (ROOT / "app.py").read_text()
    tree = ast.parse(source)
    function = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == "_ecg_strip_svg")
    body = ast.get_source_segment(source, function)
    assert "accessible_label" in body
    assert "complexes per minute" in body
    # The rhythm-naming helper is gone, not merely unused: an unwired function
    # that produces a diagnosis next to the learner surface invites reconnection.
    assert "_ecg_interpretation" not in source


@pytest.mark.parametrize("constant", ["PRESENTATION", "PS002_PRESENTATION"])
def test_the_arrival_narrative_does_not_interpret_the_first_ecg(constant):
    source = (ROOT / "app.py").read_text()
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == constant for t in n.targets))
    assert not names_a_rhythm(ast.literal_eval(node.value)), constant


def test_the_generated_ps001_arrival_narrative_does_not_interpret_it_either():
    from encounter_generator import generate_encounter
    import app  # noqa: F401  -- only to ensure module imports resolve
    source = (ROOT / "encounter_generator.py").read_text()
    assert "atrial fibrillation with rapid ventricular response" not in source


def test_the_management_trace_still_records_the_rhythm():
    """Naming it afterwards is a record, not a shortcut during care."""
    source = (ROOT / "app.py").read_text()
    assert '("Rhythm", b.get("rhythm"), a.get("rhythm")' in source
