"""Cross-module encounters use the actual case bank, parser, engine and UI.

These are regression checks of authored simulation behaviour, not clinical
validation of the numerical trajectories. No paid AI or image call is made.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from clinical_cases import FAMILIES
from clinical_scene import answer_history, history_facts, history_topic_facts
from cognitive_catalog import BIAS_CHALLENGES
from encounter_generator import generate_encounter
from test_curriculum_trajectories import execute_turn, initialize, load_engine


VARIANTS = [(family, case["id"]) for family, bank in FAMILIES.items()
            for case in bank["variants"]]
ORDERS = {
    "pneumonia": "Give ceftriaxone 2 g IV; start oxygen via nasal cannula 4 L/min",
    "pulmonary_edema": "Start CPAP 8 FiO2 40%; start nitroglycerin 30 mcg/min",
    "acs": "Give aspirin 324 mg PO; consult cardiology",
    "pulmonary_embolism": "Give heparin 5000 units IV; consult PERT",
    "asthma": "Give salbutamol 5 mg nebulized",
    "gi_bleed": "Transfuse 1 unit packed red blood cells",
    "hypoglycemia": "Give dextrose 25 g IV",
    "opioid": "Give naloxone 0.4 mg IV",
}


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def challenge_for(family):
    return next(key for key, item in BIAS_CHALLENGES.items()
                if family in item["families"])


def encounter(engine, family, variant_id=None):
    return generate_encounter(challenge_for(family), engine["INITIAL_STATE"],
                              seed=17, family_id=family,
                              variant_id=variant_id or FAMILIES[family]["variants"][0]["id"])


@pytest.mark.parametrize(("family", "variant_id"), VARIANTS)
def test_real_patient_variants_execute_their_management_without_af_state(engine, family, variant_id):
    generated = encounter(engine, family, variant_id)
    frozen = deepcopy(generated["state"])
    session = initialize(engine, frozen)
    parsed, result, before, after = execute_turn(engine, ORDERS[family])
    assert result["executed"], (parsed, result)
    assert result["clarification"] is None
    assert session.state["engine_family"] == family
    assert session.state["family_state"]["version"]
    assert session.state["sim_time"] > 0
    assert all(action["type"] not in {"cardioversion", "diltiazem", "amiodarone"}
               for action in parsed["actions"])
    assert session.state["treatments"]["cardioversions"] == 0
    assert "AF" not in after["observable"]["rhythm"]
    assert session.state["encounter_spec"] == frozen["encounter_spec"]
    assert generated["state"] == frozen
    assert "encounter_spec" not in after and "challenge_id" not in after
    assert "glucose_mg_dl" not in after["observable"]  # not measured yet
    assert not any(word in engine["format_clinical_update"]().lower()
                   for word in ("dysuria", "urinary", "atrial fibrillation"))

    old, current = before["observable"], after["observable"]
    if family in {"pneumonia", "pulmonary_edema", "asthma", "opioid"}:
        assert current["spo2"] > old["spo2"]
    if family in {"pulmonary_edema", "asthma"}:
        assert current["respiratory_rate"] < old["respiratory_rate"]
    if family == "gi_bleed":
        assert current["sbp"] > old["sbp"] and current["crt"] < old["crt"]
    if family in {"hypoglycemia", "opioid"}:
        assert current["mental_status"] == "Alert"
    if family in {"acs", "pulmonary_embolism"}:
        # Giving an antithrombotic or calling a specialist is not reperfusion.
        assert session.state["ecg_profile"] == frozen["ecg_profile"]
        assert current["sbp"] <= old["sbp"]
        assert any("not yet occurred" in s.get("label", "")
                   for s in result["action_summaries"])


@pytest.mark.parametrize(("family", "variant_id"), VARIANTS)
def test_real_case_diagnostics_preserve_discriminating_findings(engine, family, variant_id):
    generated = encounter(engine, family, variant_id)
    case = generated["spec"]["clinical_case"]
    session = initialize(engine, generated["state"])
    _, result, _, after = execute_turn(engine, "Order POCUS; order arterial blood gas; order basic labs")
    assert result["executed"], result
    studies = session.state["diagnostics"]
    assert {"pocus", "abg", "basic_labs"} <= studies.keys()
    # A structured update must not erase the source's ventricular findings.
    for key in ("lv", "rv", "pericardium", "venous_compression"):
        if key in case["investigations"]["pocus"]["result"]:
            assert studies["pocus"][key] == case["investigations"]["pocus"]["result"][key]
    for summary in result["action_summaries"]:
        if summary.get("type") == "diagnostic":
            rendered = engine["format_diagnostic_summary"](summary)
            assert rendered and "None" not in rendered
            assert "Diagnostic result available." != rendered
    gas = studies["abg"]
    assert not ({"pH", "pCO2_mmHg", "pO2_mmHg", "FiO2"} & gas.keys())
    if family == "opioid":
        assert gas["paco2_mm_hg"] > 55
    if variant_id == "asthma_24f":
        assert gas["paco2_mm_hg"] < 36
    assert after["diagnostics"] == studies
    assert "clinical_case" not in json.dumps(after)


@pytest.mark.parametrize("family", FAMILIES)
def test_questions_use_the_chosen_patients_facts_and_do_not_mutate_clinical_state(engine, family):
    generated = encounter(engine, family)
    state = generated["state"]
    before = deepcopy(state)
    facts = history_facts("Previous patient with rapid AF and dysuria.", "PS001", state=state)
    reply = answer_history("What brought you in today?", facts, state=state)
    assert reply == " ".join(history_topic_facts(state, "chief_complaint"))
    medications = answer_history("What medications do you take?", facts, state=state)
    assert medications == " ".join(history_topic_facts(state, "medications"))
    assert "Previous patient" not in reply and "PRIVATE" not in reply
    assert state == before


def test_repeated_measurements_keep_the_old_result_and_observe_the_new_state(engine):
    session = initialize(engine, encounter(engine, "hypoglycemia")["state"])
    _, first_result, _, first_snapshot = execute_turn(engine, "Check capillary glucose")
    assert first_result["executed"]
    first = deepcopy(session.state["diagnostics"]["poc_glucose"])
    assert first["glucose_mg_dl"] < 50
    execute_turn(engine, ORDERS["hypoglycemia"])
    _, second_result, _, second_snapshot = execute_turn(engine, "Check capillary glucose")
    assert second_result["executed"]
    latest = session.state["diagnostics"]["poc_glucose"]
    assert latest["glucose_mg_dl"] >= 70
    assert latest["time_min"] > first["time_min"]
    assert session.state["diagnostic_history"][0]["result"] == first
    assert first_snapshot["diagnostics"]["poc_glucose"] == first
    assert second_snapshot["diagnostics"]["poc_glucose"] == latest


def test_unsupported_second_order_does_not_partially_execute_supported_first_order(engine):
    session = initialize(engine, encounter(engine, "acs")["state"])
    before = deepcopy(session.state)
    parsed, result, _, _ = execute_turn(engine, "Give aspirin 324 mg PO and clopidogrel 300 mg PO")
    assert any(a["type"] == "clarification" for a in parsed["actions"])
    assert not result["executed"] and result["clarification"]
    assert session.state == before


def test_review_uses_observed_trajectory_without_importing_sepsis_explanations(engine):
    session = initialize(engine, encounter(engine, "hypoglycemia")["state"])
    execute_turn(engine, ORDERS["hypoglycemia"])
    event = deepcopy(session.management_trace[-1])
    # No glucose test has been requested. Neither physiology nor the answer key
    # may be converted into a discovered laboratory result or bias attribution.
    model = engine["_trajectory_expert_model"]({"decision": 1}, event)
    assert model["trajectory_grounded"]
    text = json.dumps(model).lower()
    assert "dextrose" in text or "glucose" in text
    assert "alert" in text and "drowsy" in text
    assert "sepsis" not in text and "urinary" not in text
    assert "impaired perfusion" not in text
    assert "premature closure" not in text and "anchoring" not in text
    assert "mg/dl" not in text


def widget(elements, label):
    return next(item for item in elements if item.label == label)


@pytest.fixture
def shared_app(monkeypatch):
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30)
    app.secrets["APP_PASSWORD"] = "test-only"
    app.session_state["_shared_access_granted"] = True
    app.run()
    assert not app.exception
    return app


def test_shared_selector_prioritizes_new_challenges_without_legacy_case_identifiers(shared_app):
    selector = widget(shared_app.selectbox, "Clinical problem")
    assert selector.options[0].startswith("R1-05")
    assert len(selector.options) == 11
    assert all("PS001" not in label and "PS002" not in label for label in selector.options)
    assert all(any(label.startswith(key + " ") for label in selector.options)
               for key in BIAS_CHALLENGES)


@pytest.mark.parametrize("family", FAMILIES)
def test_each_family_keeps_all_encounter_modes_reachable_without_render_errors(shared_app, engine, family):
    widget(shared_app.selectbox, "Clinical problem").set_value(challenge_for(family)).run()
    widget(shared_app.button, "Begin Encounter").click().run()
    assert not shared_app.exception
    # Use a fixed real variant so every family is exercised, independent of
    # the random selection performed by the normal entry flow just above.
    generated = encounter(engine, family)
    shared_app.session_state.state = deepcopy(generated["state"])
    shared_app.session_state.events = [{"kind": "presentation", "time": 0,
                                       "text": generated["presentation"]}]
    shared_app.run()
    for mode in ("Talk", "Examine", "Tests", "Treat"):
        widget(shared_app.radio, "Encounter").set_value(mode).run()
        assert not shared_app.exception, (family, mode, shared_app.exception)
        assert any('class="clinical-scene' in item.value for item in shared_app.markdown)
        widget(shared_app.button, "ECG")
        if mode in {"Tests", "Treat"}:
            widget(shared_app.button, "Submit")
            assert shared_app.text_area
    assert shared_app.session_state.state == generated["state"]
    # Exercise the ordinary submission/rerun/chart path as well as the mode
    # switches. Different lab schemas used to crash the legacy chart renderer.
    widget(shared_app.radio, "Encounter").set_value("Tests").run()
    shared_app.text_area[0].set_value("Order POCUS; order arterial blood gas; order basic labs")
    widget(shared_app.button, "Submit").click().run()
    assert not shared_app.exception, (family, shared_app.exception)
    assert {"pocus", "abg", "basic_labs"} <= shared_app.session_state.state["diagnostics"].keys()
    assert any(event["kind"] == "diagnostic_result" for event in shared_app.session_state.events)
    widget(shared_app.button, "ECG").click().run()
    assert not shared_app.exception
    recordings = shared_app.session_state.state["diagnostics"]["ecg"]
    assert recordings[-1]["status"] == "available"
    assert recordings[-1]["heart_rate"] == shared_app.session_state.state["observable"]["hr"]


def test_new_treatment_requires_reasoning_then_executes_the_held_order_once(shared_app, engine):
    widget(shared_app.selectbox, "Clinical problem").set_value("R1-06").run()
    widget(shared_app.button, "Begin Encounter").click().run()
    generated = encounter(engine, "hypoglycemia")
    shared_app.session_state.state = deepcopy(generated["state"])
    shared_app.run()
    widget(shared_app.radio, "Encounter").set_value("Treat").run()
    shared_app.text_area[0].set_value("Give dextrose 25 g IV")
    widget(shared_app.button, "Submit").click().run()
    assert not shared_app.exception
    assert shared_app.session_state.pending_reasoning
    assert shared_app.session_state.state == generated["state"]
    widget(shared_app.text_area, "My working model is…").set_value(
        "A reversible metabolic cause may explain the altered consciousness.")
    widget(shared_app.text_area, "My management priority is…").set_value(
        "Restore glucose availability while monitoring breathing.")
    widget(shared_app.text_area, "I expect…").set_value(
        "Improved alertness; persistent abnormalities would require further evaluation.")
    widget(shared_app.text_area, "I will reassess these variables…").set_value(
        "Mental status, glucose, respiratory rate and blood pressure.")
    widget(shared_app.number_input, "I will reassess in… minutes").set_value(5)
    widget(shared_app.button, "Complete reasoning & execute held order").click().run()
    assert not shared_app.exception
    assert not shared_app.session_state.pending_reasoning
    assert shared_app.session_state.state["observable"]["mental_status"] == "Alert"
    medications = shared_app.session_state.state["treatments"]["administered_medications"]
    assert len(medications) == 1 and medications[0]["dose_g"] == 25
    assert shared_app.session_state.management_trace[-1]["execution_status"] == "executed"
