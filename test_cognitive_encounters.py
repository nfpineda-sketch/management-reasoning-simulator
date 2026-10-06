"""Cross-module encounters use the actual case bank, parser, engine and UI.

These are regression checks of authored simulation behaviour, not clinical
validation of the numerical trajectories. No paid AI or image call is made.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

from clinical_cases import FAMILIES
from clinical_scene import answer_history, history_facts, history_topic_facts
from cognitive_catalog import BIAS_CHALLENGES
from encounter_generator import generate_encounter
from test_curriculum_trajectories import execute_turn, initialize, load_engine


VARIANTS = [(family, case["id"]) for family, bank in FAMILIES.items()
            for case in bank["variants"]]
# DF-23 row 7 (faculty, 2026-09-29): this patient's own rhythm is atrial fibrillation,
# rate-controlled by the beta-blocker -- authored in the case from arrival, never an AF
# state the encounter enters. Every other bank patient stays out of AF.
AUTHORED_AF = {"anaphylaxis_63m_betablocked"}
ORDERS = {
    "pneumonia": "Give ceftriaxone 2 g IV; start oxygen via nasal cannula 4 L/min",
    "pulmonary_edema": "Start CPAP 8 FiO2 40%; start nitroglycerin 30 mcg/min",
    "acs": "Give aspirin 324 mg PO; consult cardiology",
    "pulmonary_embolism": "Give heparin 5000 units IV; consult PERT",
    "asthma": "Give salbutamol 5 mg nebulized",
    "gi_bleed": "Transfuse 1 unit packed red blood cells",
    # Faculty decision 8 of 2026-09-21: one of these patients arrives with a line
    # that is not in the vein, so the management of a hypoglycaemia now includes
    # making sure the dextrose can reach them.
    "hypoglycemia": "Place a peripheral IV line; give dextrose 25 g IV",
    "opioid": "Give naloxone 0.4 mg IV",
    # The three families of 2026-09-23, each ordered the way its own treatment
    # is written: a route that is the order, a service that is the treatment,
    # and an antidote the rate alone would not have suggested.
    "anaphylaxis": "Give epinephrine 0.5 mg IM",
    "renal_colic": "Give ceftriaxone 2 g IV; consult urology",
    "bradycardia": "Give calcium gluconate 2 g IV",
    # The x of xABCDE: this is the order that comes before the others.
    "trauma": "Apply a tourniquet to the limb",
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
    if variant_id in AUTHORED_AF:
        assert before["observable"]["rhythm"] == after["observable"]["rhythm"] == "AF"
    else:
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
        # Glucose that reaches the patient wakes them, thiamine or no thiamine.
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
    # Since 2026-09-23 a study the resident sends away does not hold them until
    # it is back: requesting costs a minute and the result arrives on its own.
    # The bedside one is there at once; the others need their own minutes.
    _, _, _, after = execute_turn(engine, "Reassess blood pressure and perfusion in 15 minutes.")
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


def test_unsupported_second_order_does_not_hold_the_supported_first_order(engine):
    # Phase 0 (0B, 2026-10-06), bundle rule: the independent aspirin runs; the colchicine the
    # reader cannot read gets its own fate (UNRECOGNIZED) and holds nothing. It used to hold
    # the aspirin too, so a reasonable unknown item delayed a time-critical drug.
    session = initialize(engine, encounter(engine, "acs")["state"])
    before = deepcopy(session.state)
    parsed, result, _, _ = execute_turn(engine, "Give aspirin 324 mg PO and colchicine 0.5 mg PO")
    assert any(a["type"] == "clarification" for a in parsed["actions"])
    assert result["executed"] and not result["clarification"]
    assert [s.get("type") for s in result["action_summaries"]] == ["aspirin"]
    split = result["_split"]
    assert [a.get("unrecognized_text") for a, _ in split["unreadable"]] == ["colchicine 0.5 mg PO"]
    assert session.state != before


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


def authored_replay_fixture(monkeypatch):
    """Historical authored-family integration is an explicit replay fixture.

    Both aliases of the generator are loaded before either is patched, as in
    ``test_curriculum_app``. ``curriculum_runtime`` binds ``generate_encounter``
    when it is imported; imported for the first time inside the patched window
    (the app's first run imports it), it kept the replay after teardown, and a
    later test in the same process launched a bank case where it expected a
    newly authored one (test_problem_launch, 2026-09-26).
    """
    import curriculum_runtime
    from encounter_generator import generate_encounter as real_generate
    def authored_replay(*args, **kwargs):
        kwargs["generation_mode"] = "authored"
        return real_generate(*args, **kwargs)
    monkeypatch.setattr("encounter_generator.generate_encounter", authored_replay)
    monkeypatch.setattr(curriculum_runtime, "generate_encounter", authored_replay)


@pytest.fixture
def shared_app(monkeypatch):
    authored_replay_fixture(monkeypatch)
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30)
    app.secrets["APP_PASSWORD"] = "test-only"
    app.session_state["_shared_access_granted"] = True
    app.run()
    assert not app.exception
    return app


def test_the_replay_fixture_leaves_no_generator_behind():
    # The order-dependent failure of 2026-09-26 (C-2026-09-26-20): the replay
    # ends with the fixture even when curriculum_runtime is first imported
    # inside it, as the app's first run imports it. A fresh interpreter, because
    # this process has long since imported both modules.
    source = """
import sys
import pytest
from test_cognitive_encounters import authored_replay_fixture
assert "curriculum_runtime" not in sys.modules
with pytest.MonkeyPatch.context() as patch:
    authored_replay_fixture(patch)
    import curriculum_runtime
    import encounter_generator
    assert curriculum_runtime.generate_encounter.__name__ == "authored_replay"
    assert encounter_generator.generate_encounter.__name__ == "authored_replay"
assert curriculum_runtime.generate_encounter is encounter_generator.generate_encounter
assert encounter_generator.generate_encounter.__name__ == "generate_encounter"
"""
    result = subprocess.run([sys.executable, "-c", source], cwd=Path(__file__).resolve().parent,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-2000:]


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
            widget(shared_app.button, "Send")
            assert shared_app.text_area
    assert shared_app.session_state.state == generated["state"]
    # Exercise the ordinary submission/rerun/chart path as well as the mode
    # switches. Different lab schemas used to crash the legacy chart renderer.
    widget(shared_app.radio, "Encounter").set_value("Tests").run()
    shared_app.text_area[0].set_value("Order POCUS; order arterial blood gas; order basic labs")
    widget(shared_app.button, "Send").click().run()
    assert not shared_app.exception, (family, shared_app.exception)
    # The laboratory and the gas come back on their own minutes; the resident is
    # not held waiting for them (2026-09-23).
    shared_app.text_area[0].set_value("Reassess blood pressure and perfusion in 15 minutes.")
    widget(shared_app.button, "Send").click().run()
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
    widget(shared_app.button, "Send").click().run()
    assert not shared_app.exception
    assert shared_app.session_state.pending_reasoning
    assert shared_app.session_state.state == generated["state"]
    widget(shared_app.text_area, "What do you think is going on?").set_value(
        "A reversible metabolic cause may explain the altered consciousness.")
    widget(shared_app.text_area, "Which problem are you addressing first? (optional)").set_value(
        "Restore glucose availability while monitoring breathing.")
    widget(shared_app.text_area, "What do you expect to happen, or what are you trying to clarify?").set_value(
        "Improved alertness; persistent abnormalities would require further evaluation.")
    widget(shared_app.text_area, "What will you check, and when?").set_value(
        "Mental status, glucose, respiratory rate and blood pressure.")
    widget(shared_app.number_input, "I will check in… minutes").set_value(5)
    widget(shared_app.button, "Complete reasoning & execute held order").click().run()
    assert not shared_app.exception
    assert not shared_app.session_state.pending_reasoning
    assert shared_app.session_state.state["observable"]["mental_status"] == "Alert"
    medications = shared_app.session_state.state["treatments"]["administered_medications"]
    assert len(medications) == 1 and medications[0]["dose_g"] == 25
    assert shared_app.session_state.management_trace[-1]["execution_status"] == "executed"


def test_a_consult_or_admission_reads_as_part_of_the_patient_response(shared_app, engine):
    # Reported: "After ICU contacted; definitive intervention has not yet occurred, BP ...".
    widget(shared_app.selectbox, "Clinical problem").set_value(challenge_for("pneumonia")).run()
    widget(shared_app.button, "Begin Encounter").click().run()
    generated = encounter(engine, "pneumonia")
    shared_app.session_state.state = deepcopy(generated["state"])
    shared_app.run()
    widget(shared_app.radio, "Encounter").set_value("Treat").run()
    for order, lead in (
        ("Sepsis from pneumonia. My priority is the right level of care. Consult ICU. "
         "I expect a stable blood pressure. Reassess in 15 minutes BP and HR.",
         "After contacting ICU (no intervention yet), BP "),
        ("Sepsis from pneumonia. My priority is the right level of care. Admit to ICU. "
         "I expect a stable blood pressure. Reassess in 15 minutes BP and HR.",
         "After requesting admission to ICU, BP "),
    ):
        shared_app.text_area[0].set_value(order)
        widget(shared_app.button, "Send").click().run()
        assert not shared_app.exception
        updates = [e["text"] for e in shared_app.session_state.events if e["kind"] == "clinical_update"]
        assert updates, (shared_app.session_state.events, shared_app.session_state.pending_reasoning)
        update = updates[-1]
        assert update.startswith(lead), update
        assert "definitive intervention" not in update
    assert any(item.value.startswith("Cumulative crystalloid: ") and item.value.endswith(" mL")
               and ".0 mL" not in item.value for item in shared_app.markdown), \
        [item.value for item in shared_app.markdown if "crystalloid" in item.value]


def test_a_finished_timed_bolus_leaves_no_pending_crystalloid_line(shared_app, engine):
    # Paced delivery in a generated case left 1e-13 mL, shown as "Crystalloid pending: 0 mL".
    from generated_case import generate_ai_encounter
    from test_generated_case import AuthorClient
    widget(shared_app.selectbox, "Clinical problem").set_value(challenge_for("pneumonia")).run()
    widget(shared_app.button, "Begin Encounter").click().run()
    generated = generate_ai_encounter("R1-05", deepcopy(engine["INITIAL_STATE"]), client=AuthorClient(), seed=7)
    shared_app.session_state.state = deepcopy(generated["state"])
    shared_app.run()
    widget(shared_app.radio, "Encounter").set_value("Treat").run()
    shared_app.text_area[0].set_value(
        "Adrenal crisis. My priority is perfusion. Give 1000 mL normal saline IV over 15 minutes. "
        "I expect a higher blood pressure. Reassess in 10 minutes BP and HR.")
    widget(shared_app.button, "Send").click().run()
    shared_app.text_area[0].set_value(
        "Adrenal crisis. My priority is perfusion. Give 500 mL normal saline IV over 10 minutes. "
        "I expect a higher blood pressure. Reassess in 20 minutes BP and HR.")
    widget(shared_app.button, "Send").click().run()
    assert not shared_app.exception
    assert shared_app.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 1500
    assert not any("Crystalloid pending" in item.value for item in shared_app.markdown), \
        shared_app.session_state.state["family_state"]["pending_fluid_ml"]
