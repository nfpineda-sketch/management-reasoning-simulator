"""Treating the patient has to show on the patient (faculty decisions 2026-09-21).

Found by playing the 83-year-old with pneumonia, brought in by his daughter
because he had become "unusually sleepy". Two and a half hours later his
pressure, his capillary refill, his saturation and his lactate had all
recovered and he was still described as drowsy, with the same work of
breathing as on arrival: the two signs the case is built on could not answer
treatment.

Faculty decisions: the mental status recovers by one step, thirty minutes after
the perfusion and oxygenation that explain it have come back, and the work of
breathing follows the lung instead of sitting on one level.
"""
import pytest

from family_engine import (
    MENTAL_RECOVERY, PNEUMONIA_WOB_PER_EFFORT, _initialize, _minute, _surface,
    execute_family_bundle,
)
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

RESUSCITATE = ("Start oxygen 15 L/min non-rebreather mask. Give ceftriaxone 2 g IV. "
               "Give 1000 mL normal saline IV. Reassess in 30 minutes.")
WAIT = "Reassess in {} minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(engine, variant, *orders):
    state = encounter(engine, "pneumonia", "pneumonia_" + variant)["state"]
    snapshots = [dict(state["observable"])]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], (order, result.get("clarification"))
        snapshots.append(dict(state["observable"]))
    return state, snapshots


def test_the_drowsy_patient_wakes_once_the_perfusion_is_back(engine):
    state, snapshots = run(engine, "83m", RESUSCITATE, WAIT.format(20), WAIT.format(20), WAIT.format(20))
    assert snapshots[0]["mental_status"] == "Drowsy"
    # Perfusion recovers during the first order; the brain follows half an hour later.
    assert snapshots[1]["mental_status"] == "Drowsy"
    assert snapshots[2]["mental_status"] == "Alert"
    assert snapshots[-1]["mental_status"] == "Alert"
    o = snapshots[-1]
    assert o["sbp"] >= MENTAL_RECOVERY["sbp"] and o["spo2"] >= MENTAL_RECOVERY["spo2"]
    assert o["crt"] < MENTAL_RECOVERY["crt_s"]


def test_nothing_wakes_while_the_perfusion_is_still_bad(engine):
    # Oxygen alone leaves the circulation where it was; two hours change nothing.
    _, snapshots = run(engine, "83m", "Start oxygen 15 L/min non-rebreather mask. Reassess in 60 minutes.",
                       WAIT.format(60))
    assert [s["mental_status"] for s in snapshots] == ["Drowsy", "Drowsy", "Drowsy"]


def test_the_recovery_is_one_step_and_no_more(engine):
    state = encounter(engine, "pneumonia", "pneumonia_83m")["state"]
    # The case as if it had been written one step worse.
    state["encounter_spec"]["clinical_case"]["observable"]["mental_status"] = "Obtunded"
    state["observable"]["mental_status"] = "Obtunded"
    execute_family_bundle(state, parse_family_actions(RESUSCITATE))
    for _ in range(4):
        execute_family_bundle(state, parse_family_actions(WAIT.format(30)))
    # Two hours of recovered perfusion still buy exactly one step.
    assert state["observable"]["mental_status"] == "Drowsy"


def test_a_minute_without_perfusion_discounts_one(engine):
    # A one-mmHg wobble around the threshold must not restart the half hour, so
    # the count walks back instead of resetting.
    state = encounter(engine, "pneumonia", "pneumonia_83m")["state"]
    _initialize(state)
    f = state["family_state"]
    f["perfusion_recovered_min"] = MENTAL_RECOVERY["delay_min"] - 1
    state["observable"]["sbp"] = MENTAL_RECOVERY["sbp"] - 20
    _minute(state)
    assert f["perfusion_recovered_min"] == MENTAL_RECOVERY["delay_min"] - 2
    assert not f.get("mental_recovered")
    _surface(state)
    assert state["observable"]["mental_status"] == "Drowsy"


def test_waking_survives_a_dip_that_is_not_a_deterioration(engine):
    state, _ = run(engine, "83m", RESUSCITATE, WAIT.format(20), WAIT.format(20))
    assert state["observable"]["mental_status"] == "Alert"
    f = state["family_state"]
    f["perfusion_recovered_min"] = 0          # as a brief dip would leave it
    _surface(state)
    assert state["observable"]["mental_status"] == "Alert"


def test_a_real_deterioration_still_puts_the_patient_down(engine):
    state, _ = run(engine, "83m", RESUSCITATE, WAIT.format(20), WAIT.format(20))
    assert state["observable"]["mental_status"] == "Alert"
    state["family_state"]["circulation"] = 2.2      # shock again
    _surface(state)
    assert state["observable"]["mental_status"] in {"Drowsy", "Obtunded"}


def test_the_families_that_own_mental_status_keep_it(engine):
    # Glucose and opioid write the mental status themselves; the step-up must not
    # reach over them and wake a patient whose brain is still without sugar.
    state = encounter(engine, "hypoglycemia", "hypoglycemia_28m")["state"]
    _initialize(state)
    state["family_state"]["perfusion_recovered_min"] = 999
    _surface(state)
    assert state["observable"]["mental_status"] in {"Drowsy", "Obtunded", "Unresponsive"}


def test_the_work_of_breathing_follows_the_lung(engine):
    state, snapshots = run(engine, "46f", RESUSCITATE, *[WAIT.format(45)] * 8)
    efforts = [s["work_of_breathing"] for s in snapshots]
    assert efforts[0] == "Increased", efforts  # the wording the case was written with
    # It worsens while the antibiotic has not yet taken hold, and improves after.
    assert "Markedly increased" in efforts, efforts
    assert efforts[-1] == "Mildly increased", efforts
    assert efforts.index("Markedly increased") < efforts.index("Mildly increased"), efforts


def test_the_scale_is_the_one_the_faculty_set():
    # One level per ~8% of lung burden, so the bedside sign moves within an encounter.
    assert PNEUMONIA_WOB_PER_EFFORT == 6


def test_the_other_families_keep_their_own_scale(engine):
    # Oedema already had its own proportional rule; it is untouched.
    state = encounter(engine, "pulmonary_edema", "pulmonary_edema_58m")["state"]
    before = state["observable"]["work_of_breathing"]
    execute_family_bundle(state, parse_family_actions(
        "Start BiPAP IPAP 14 EPAP 8 FiO2 60%. Start nitroglycerin 60 mcg/min IV. Reassess in 20 minutes."))
    assert before == "Severe"
    assert state["observable"]["work_of_breathing"] in {"Mildly increased", "Moderately increased"}


# The faculty's own sentence, 2026-09-21: a brain without sugar never wakes,
# however well everything else has been resolved. The step-up above reads the
# circulation and the oxygenation, so it must never reach over the mechanisms
# that own the mental status for their own reason.

def test_a_brain_without_sugar_never_wakes(engine):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_28m")["state"]
    _initialize(state)
    f = state["family_state"]
    # Perfect circulation, perfect oxygenation, and hours of both.
    state["observable"].update(sbp=130, dbp=80, spo2=99, crt=2.0)
    for _ in range(240):
        _minute(state)
    assert f["mental_recovered"] is True     # the circulation did recover
    _surface(state)
    assert state["observable"]["glucose_mg_dl"] < 70
    assert state["observable"]["mental_status"] != "Alert"


def test_the_thiamine_depleted_brain_stays_confused_too(engine):
    # Glucose normal, circulation normal, and still not awake: the deficit is
    # not one the perfusion can answer.
    state = encounter(engine, "hypoglycemia", "hypoglycemia_54m_thiamine")["state"]
    execute_family_bundle(state, parse_family_actions("Give 25 g dextrose IV. Reassess in 30 minutes."))
    for _ in range(3):
        execute_family_bundle(state, parse_family_actions(WAIT.format(30)))
    o = state["observable"]
    assert o["glucose_mg_dl"] >= 70 and o["sbp"] >= MENTAL_RECOVERY["sbp"]
    assert state["family_state"].get("mental_recovered") is True
    assert o["mental_status"] == "Confused"


def test_a_generated_case_keeps_its_own_metabolic_brain():
    # The same rule on the AI-authored path, where the declared mechanism owns
    # the glucose and the brain that depends on it.
    import coupled_encounter as adapter
    from test_generated_metabolic import hypoglycaemic, minutes

    state = hypoglycaemic(glucose=38)
    state["observable"].update(sbp=130, dbp=80, spo2=99, crt=2.0)
    minutes(state, 120)
    adapter.project(state)
    assert state["observable"]["glucose_mg_dl"] < 70
    assert state["observable"]["mental_status"] != "Alert"
