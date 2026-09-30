"""Two engine findings the faculty settled on 2026-09-30.

TD-47: through an endotracheal tube there is no stridor to hear or to pay for. The anaphylaxis goes on --
its bronchospasm, its circulation and its course are unchanged -- and nothing here models a difficult airway.

R-4, row 3: «Persisten crépitos bilaterales, con menor esfuerzo respiratorio» reads as improvement, and the
engine writes it only while the congestion improves: never at a minute the patient is exhausted.
"""
import pytest

import anaphylaxis_reaction
import work_of_breathing
from family_engine import advance_clinical_time, current_findings, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

OXYGEN = "Oxygen 15 L/min by non-rebreather mask"
TUBE = "Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5"
REDUCED = "Bilateral crackles remain, with reduced respiratory effort."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def played(engine, case, orders, minutes, family="anaphylaxis"):
    state = encounter(engine, family, case)["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
    advance_clinical_time(state, minutes)
    return state


def test_no_stridor_is_heard_or_charged_through_the_tube(engine):
    tubed = played(engine, "anaphylaxis_29f", [OXYGEN, TUBE], 6)
    f = tubed["family_state"]
    assert f["invasive"] is True and f["upper_airway_stridor"] is False
    exam = current_findings(tubed)["Respiratory"]
    assert exam.startswith("Endotracheal tube in place: no stridor through the tube")
    assert "audible" not in exam and "wheeze" in exam           # the bronchospasm is still there
    # The reaction is not resolved by the tube: it goes on, and so does the shock.
    assert f["reaction"] > anaphylaxis_reaction.STRIDOR_AT and tubed["observable"]["sbp"] < 90


def test_without_a_tube_the_stridor_and_its_price_are_as_before(engine):
    breathing = played(engine, "anaphylaxis_29f", [OXYGEN], 6)
    assert breathing["family_state"]["upper_airway_stridor"] is True
    assert "audible inspiratory stridor" in current_findings(breathing)["Respiratory"]
    assert anaphylaxis_reaction.stridor_heard(1.0, intubated=False)
    assert not anaphylaxis_reaction.stridor_heard(1.0, intubated=True)
    assert not anaphylaxis_reaction.stridor_heard(.5, intubated=False)


def test_the_intubated_chest_keeps_each_case_s_own_wheeze():
    assert anaphylaxis_reaction.intubated_chest(
        "Increased effort with widespread expiratory wheeze and audible inspiratory stridor.") == (
        "Endotracheal tube in place: no stridor through the tube; widespread expiratory wheeze.")
    assert anaphylaxis_reaction.intubated_chest("Increased effort with widespread wheeze; no stridor heard.") == (
        "Endotracheal tube in place: no stridor through the tube; widespread wheeze.")


@pytest.mark.parametrize("case", ["pulmonary_edema_58m", "pulmonary_edema_75f"])
@pytest.mark.parametrize("orders, improves", [
    ([], False),
    (["Oxygen 15 L/min by non-rebreather mask"], False),
    (["Start CPAP 10 cmH2O FiO2 60%. Give nitroglycerin 400 mcg IV bolus."], True),
    (["Start CPAP 10 cmH2O FiO2 60%. Start nitroglycerin infusion 100 mcg/min. Give furosemide 40 mg IV."], True),
    # Treated only once exhausted: the change from one state to the other is watched minute by minute.
    (["Reassess in 75 minutes.", "Start CPAP 10 cmH2O FiO2 60%. Start nitroglycerin infusion 100 mcg/min."], True),
])
def test_reduced_effort_is_never_written_beside_exhaustion(engine, case, orders, improves):
    state = encounter(engine, "pulmonary_edema", case)["state"]
    seen = {"reduced": 0, "exhausted": 0}

    def check():
        respiratory = current_findings(state)["Respiratory"]
        exhausted = state["observable"]["work_of_breathing"] == work_of_breathing.EXHAUSTED
        seen["reduced"] += respiratory == REDUCED
        seen["exhausted"] += exhausted
        assert not (respiratory == REDUCED and exhausted), state["sim_time"]

    for order in orders:
        before = int(state.get("sim_time", 0))
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
        if int(state.get("sim_time", 0)) > before:
            check()
    for _ in range(120):
        advance_clinical_time(state, 1)
        if not state["observable"].get("pulse_present", True):
            break
        check()
    # Neither side of the rule is vacuous: treated patients reach the reduced effort, untreated ones tire.
    assert (seen["reduced"] > 0) == improves and (improves or seen["exhausted"] > 0), seen
