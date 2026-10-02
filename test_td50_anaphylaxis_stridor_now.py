"""TD-50 (faculty, 2026-10-02): the anaphylaxis examination hears the stridor the engine hears now.

* The 29f's written stridor is no longer said once the reaction falls below the
  stridor threshold -- after adrenaline, for instance -- and it stays while the
  reaction does, whatever the oxygen does to the saturation.
* Through a tube there is no stridor (TD-47), and the reaction goes on.
* The arrival numbers already contain the stridor the patient arrived with: it
  is not charged again at the first minute. A stridor that appears costs oxygen
  and effort; one that goes gives the oxygen back.
* ``anaphylaxis_63m_betablocked`` declares no upper-airway involvement: its
  examination never heard a stridor, and none is charged for.
"""
import pytest

import anaphylaxis_reaction
from family_engine import advance_clinical_time, current_findings, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

EPINEPHRINE = "Give epinephrine 0.5 mg IM. Oxygen 15 L/min by non-rebreather mask. Reassess in 10 minutes."
OXYGEN = "Oxygen 15 L/min by non-rebreather mask"
TUBE = "Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5"
WRITTEN = "Increased effort with widespread expiratory wheeze and audible inspiratory stridor."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def played(engine, case, orders=(), minutes=0):
    state = encounter(engine, "anaphylaxis", case)["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
    if minutes:
        advance_clinical_time(state, minutes)
    return state


def test_the_written_stridor_goes_when_the_reaction_falls_below_it(engine):
    state = played(engine, "anaphylaxis_29f", [EPINEPHRINE])
    f = state["family_state"]
    assert f["reaction"] < anaphylaxis_reaction.STRIDOR_AT and f["upper_airway_stridor"] is False
    respiratory = current_findings(state)["Respiratory"]
    assert respiratory == "Increased effort with widespread expiratory wheeze; no stridor heard now."
    assert "audible" not in respiratory


def test_a_normal_saturation_does_not_settle_the_stridor(engine):
    state = played(engine, "anaphylaxis_29f", [OXYGEN], minutes=6)
    assert state["observable"]["spo2"] >= 95
    assert state["family_state"]["reaction"] >= anaphylaxis_reaction.STRIDOR_AT
    assert current_findings(state)["Respiratory"] == WRITTEN


def test_after_a_successful_intubation_the_tube_is_heard_and_the_reaction_goes_on(engine):
    state = played(engine, "anaphylaxis_29f", [OXYGEN, TUBE], minutes=6)
    f = state["family_state"]
    assert f["invasive"] is True and f["upper_airway_stridor"] is False
    assert current_findings(state)["Respiratory"].startswith(anaphylaxis_reaction.INTUBATED_AIRWAY)
    assert f["reaction"] > anaphylaxis_reaction.STRIDOR_AT and state["observable"]["sbp"] < 90


def test_the_stridor_the_patient_arrived_with_is_not_charged_twice(engine):
    arrival = encounter(engine, "anaphylaxis", "anaphylaxis_29f")["state"]["observable"]
    state = played(engine, "anaphylaxis_29f", minutes=1)
    assert state["family_state"]["upper_airway_stridor"] is True
    assert state["observable"]["spo2"] == arrival["spo2"]
    assert state["observable"]["mental_status"] == arrival["mental_status"]
    assert current_findings(state)["Respiratory"] == WRITTEN


def test_a_stridor_that_appears_costs_and_one_that_goes_returns():
    f = {"reaction": .5, "reaction_baseline": .5}
    assert anaphylaxis_reaction.observables(f)["stridor_change"] == 0
    f["reaction"] = 1.0
    assert anaphylaxis_reaction.observables(f)["stridor_change"] == 1
    arrived = {"reaction": 1.0, "reaction_baseline": 1.0}
    assert anaphylaxis_reaction.observables(arrived)["stridor_change"] == 0
    arrived["reaction"] = .2
    assert anaphylaxis_reaction.observables(arrived)["stridor_change"] == -1


def test_the_63m_has_no_upper_airway_and_pays_for_none(engine):
    arrival = encounter(engine, "anaphylaxis", "anaphylaxis_63m_betablocked")["state"]["observable"]
    state = played(engine, "anaphylaxis_63m_betablocked", minutes=1)
    f = state["family_state"]
    assert f["reaction"] >= anaphylaxis_reaction.STRIDOR_AT and f["upper_airway_stridor"] is False
    assert state["observable"]["spo2"] == arrival["spo2"]
    assert current_findings(state)["Respiratory"] == "Increased effort with widespread wheeze; no stridor heard."


def test_a_case_that_never_heard_a_stridor_keeps_its_words():
    assert anaphylaxis_reaction.chest_without_stridor(
        "Increased effort with widespread wheeze; no stridor heard.") == (
        "Increased effort with widespread wheeze; no stridor heard.")
    assert anaphylaxis_reaction.chest_without_stridor(WRITTEN) == (
        "Increased effort with widespread expiratory wheeze; no stridor heard now.")
