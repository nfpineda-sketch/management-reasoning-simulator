"""Hypoglycaemia beyond the ampoule, and naloxone titrated to ventilation.

Faculty decisions 2026-09-20: octreotide for sulfonylurea, glucagon without a line,
oral carbohydrate only for a protected airway, a 10% infusion, thiamine where it
matters, a seizure for neuroglycopenia left too long; and for opioids, a long-acting
drug that outlasts boluses, withdrawal when the antidote is pushed past ventilation,
and an arrest for apnoea nobody supports.
"""
import pytest

import glucose_rescue as glu
import opioid_reversal as opi
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

DEXTROSE = "Give dextrose 25 g IV. Reassess in 20 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, family, variant, orders):
    state = encounter(engine, family, variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += result["action_summaries"]
    return state, " | ".join(str(e.get("label", "")) for e in events)


@pytest.mark.parametrize("text, expected", [
    ("Give octreotide 100 mcg SC.", {"type": "octreotide", "dose_mg": .1, "route": "SC"}),
    ("Administra octreótido 100 mcg subcutáneo.", {"type": "octreotide", "dose_mg": .1, "route": "SC"}),
    ("Give glucagon 1 mg IM.", {"type": "glucagon", "dose_mg": 1.0, "route": "IM"}),
    ("Give thiamine 100 mg IV.", {"type": "thiamine", "dose_mg": 100.0, "route": "IV"}),
])
def test_the_new_medicines_are_parsed(text, expected):
    action = parse_family_actions(text)["actions"][0]
    for field, value in expected.items():
        assert action[field] == value


@pytest.mark.parametrize("text, expected", [
    ("Start D10 at 100 mL/h.", {"type": "dextrose_infusion", "rate_ml_h": 100.0}),
    ("Inicia suero glucosado 10% a 100 mL/h.", {"type": "dextrose_infusion", "rate_ml_h": 100.0}),
    ("Give oral glucose gel.", {"type": "oral_carbohydrate"}),
    ("Dale carbohidrato oral.", {"type": "oral_carbohydrate"}),
    ("Start a naloxone infusion at 0.4 mg/h.", {"type": "naloxone_infusion", "rate_mg_h": .4}),
    ("Inicia infusión de naloxona a 400 mcg/h.", {"type": "naloxone_infusion", "rate_mg_h": .4}),
])
def test_the_new_infusions_are_parsed(text, expected):
    action = parse_family_actions(text)["actions"][0]
    for field, value in expected.items():
        assert action[field] == value


def test_sulfonylurea_recurs_through_repeated_ampoules(engine):
    state, _ = course(engine, "hypoglycemia", "hypoglycemia_76f",
                      [DEXTROSE, "Reassess in 40 minutes.", "Reassess in 40 minutes."])
    assert state["family_state"]["glucose"] < 85


def test_octreotide_stops_the_recurrence(engine):
    state, _ = course(engine, "hypoglycemia", "hypoglycemia_76f",
                      ["Give dextrose 25 g IV and octreotide 100 mcg SC. Reassess in 20 minutes.",
                       "Reassess in 40 minutes.", "Reassess in 40 minutes."])
    assert state["family_state"]["glucose"] > 115
    assert glu.octreotide_active(state["family_state"])


def test_glucagon_is_slower_and_smaller_than_the_ampoule(engine):
    glucagon, _ = course(engine, "hypoglycemia", "hypoglycemia_28m", ["Give glucagon 1 mg IM. Reassess in 20 minutes."])
    ampoule, _ = course(engine, "hypoglycemia", "hypoglycemia_28m", [DEXTROSE])
    assert glucagon["family_state"]["glucose"] < ampoule["family_state"]["glucose"]
    assert glucagon["observable"]["mental_status"] != "Alert"
    execute_family_bundle(glucagon, parse_family_actions("Reassess in 20 minutes."))
    assert glucagon["observable"]["mental_status"] == "Alert"


def test_the_glycogen_runs_out(engine):
    state, _ = course(engine, "hypoglycemia", "hypoglycemia_28m",
                      ["Give glucagon 1 mg IM. Reassess in 40 minutes.",
                       "Give glucagon 1 mg IM. Reassess in 40 minutes."])
    assert state["family_state"]["glucagon_doses"] == 2
    assert glu.treatment_gain(state["family_state"]) <= glu.GLUCAGON_MG_DL_PER_MIN * glu.GLYCOGEN_SECOND_DOSE_SHARE


def test_oral_carbohydrate_needs_a_protected_airway(engine):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_76f")["state"]
    refused = execute_family_bundle(state, parse_family_actions("Give oral glucose gel."))
    assert not refused["executed"] and "cannot safely swallow" in refused["clarification"]
    execute_family_bundle(state, parse_family_actions(DEXTROSE))
    accepted = execute_family_bundle(state, parse_family_actions("Give oral glucose gel. Reassess in 20 minutes."))
    assert accepted["executed"]
    assert state["family_state"]["oral_carbohydrate_at"] is not None


def test_a_ten_percent_infusion_offsets_the_recurrence(engine):
    state, _ = course(engine, "hypoglycemia", "hypoglycemia_76f",
                      ["Give dextrose 25 g IV. Start D10 at 400 mL/h. Reassess in 40 minutes.",
                       "Reassess in 40 minutes."])
    assert state["family_state"]["glucose"] > 100


def test_neuroglycopenia_left_alone_seizes(engine):
    state, labels = course(engine, "hypoglycemia", "hypoglycemia_28m", ["Reassess in 25 minutes."])
    assert state["family_state"]["seizure_at"] == glu.SEIZURE_AFTER_MIN
    assert "Generalized tonic-clonic seizure" in labels
    assert state["observable"]["mental_status"] == "Unresponsive"


def test_glucose_without_thiamine_leaves_the_brain_confused(engine):
    state, labels = course(engine, "hypoglycemia", "hypoglycemia_54m_thiamine", [DEXTROSE, "Reassess in 30 minutes."])
    assert state["family_state"]["glucose"] > 110
    assert state["observable"]["mental_status"] == "Confused"
    assert "thiamine-depleted brain" in labels
    execute_family_bundle(state, parse_family_actions("Give thiamine 500 mg IV. Reassess in 60 minutes."))
    assert state["observable"]["mental_status"] == "Alert"


def test_thiamine_with_the_glucose_prevents_it(engine):
    state, labels = course(engine, "hypoglycemia", "hypoglycemia_54m_thiamine",
                           ["Give thiamine 100 mg IV and dextrose 25 g IV. Reassess in 20 minutes.",
                            "Reassess in 40 minutes."])
    assert state["observable"]["mental_status"] == "Alert"
    assert "thiamine-depleted brain" not in labels


def test_a_titrated_dose_reverses_without_withdrawal(engine):
    state, labels = course(engine, "opioid", "opioid_35m",
                           ["Start bag-mask ventilation. Give naloxone 0.4 mg IV. Reassess in 5 minutes."])
    assert state["observable"]["respiratory_rate"] >= 12
    assert opi.withdrawal(state["family_state"]) == 0
    assert "Acute withdrawal" not in labels


def test_too_much_antidote_precipitates_withdrawal(engine):
    state, labels = course(engine, "opioid", "opioid_35m", ["Give naloxone 2 mg IV. Reassess in 5 minutes."])
    assert "Acute withdrawal" in labels
    assert state["observable"]["mental_status"] == "Agitated"
    assert state["observable"]["hr"] > 90 and state["observable"]["sbp"] > 125


def test_a_long_acting_opioid_outlasts_a_bolus(engine):
    short, _ = course(engine, "opioid", "opioid_35m",
                      ["Give naloxone 0.4 mg IV. Reassess in 30 minutes.", "Reassess in 30 minutes."])
    long_acting, _ = course(engine, "opioid", "opioid_67f",
                            ["Give naloxone 0.4 mg IV. Reassess in 30 minutes.", "Reassess in 30 minutes."])
    assert long_acting["family_state"]["opioid"] > short["family_state"]["opioid"]
    assert long_acting["observable"]["respiratory_rate"] <= 9


def test_an_infusion_holds_what_the_bolus_cannot(engine):
    state, _ = course(engine, "opioid", "opioid_67f",
                      ["Give naloxone 0.4 mg IV and start a naloxone infusion at 0.4 mg/h. Reassess in 30 minutes.",
                       "Reassess in 60 minutes."])
    assert state["observable"]["respiratory_rate"] >= 12 and state["observable"]["spo2"] >= 95
    assert state["family_state"]["naloxone"] > .9


def test_unsupported_apnoea_ends_in_arrest(engine):
    state, labels = course(engine, "opioid", "opioid_35m", ["Reassess in 25 minutes."])
    assert state["family_state"]["arrest_at"] == opi.ARREST_AFTER_MIN
    assert "Respiratory arrest" in labels
    assert state["observable"]["pulse_present"] is False
    held = execute_family_bundle(state, parse_family_actions("Give naloxone 0.4 mg IV."))
    assert held.get("terminal_locked") is True


def test_ventilation_prevents_the_arrest(engine):
    state, labels = course(engine, "opioid", "opioid_35m", ["Start bag-mask ventilation. Reassess in 25 minutes."])
    assert state["family_state"].get("arrest_at") is None
    assert "Respiratory arrest" not in labels
    assert state["observable"]["pulse_present"] is True


# Faculty review of the opioid magnitudes, 2026-09-21.

def test_withdrawal_is_measured_against_the_opioid_on_board():
    # Reversing what is there is the treatment; only the excess over it withdraws.
    heavy = {"opioid": 2.5, "naloxone": 1.3}
    light = {"opioid": 0.5, "naloxone": 0.9}
    assert opi.withdrawal(heavy) == 0
    assert opi.suppression(heavy) > 0          # still depressed, and not withdrawing
    assert opi.withdrawal(light) == pytest.approx(0.2)
    assert opi.suppression(light) == 0


def test_a_patient_is_never_depressed_and_withdrawing_at_once():
    for opioid in (0.5, 1.0, 2.0, 3.0):
        for naloxone in (0.0, 0.5, 1.0, 2.0, 4.0):
            f = {"opioid": opioid, "naloxone": naloxone}
            assert not (opi.suppression(f) > 0 and opi.withdrawal(f) > 0), (opioid, naloxone)


def test_the_case_that_arrives_at_one_unit_withdraws_where_it_always_did():
    assert opi.WITHDRAWAL_LEVEL == pytest.approx(1.0 + opi.WITHDRAWAL_MARGIN)
    assert opi.withdrawal({"opioid": 1.0, "naloxone": opi.WITHDRAWAL_LEVEL}) == 0
    assert opi.withdrawal({"opioid": 1.0, "naloxone": opi.WITHDRAWAL_LEVEL + .1}) == pytest.approx(.1)


def test_the_short_acting_opioid_halves_within_the_encounter():
    # Eleven hours meant nothing the resident watched ever wore off.
    assert opi.DECAY_PER_MIN ** 240 == pytest.approx(0.5, rel=.02)
    assert opi.LONG_ACTING_DECAY_PER_MIN ** 240 > .9


def test_it_is_still_slow_enough_to_arrest_unsupported(engine):
    # Four hours is the most acceleration that keeps the arrest: at twenty
    # minutes the suppression has not yet lifted the patient off the floor.
    state, _ = course(engine, "opioid", "opioid_35m", ["Reassess in 25 minutes."])
    assert state["family_state"]["arrest_at"] == opi.ARREST_AFTER_MIN
