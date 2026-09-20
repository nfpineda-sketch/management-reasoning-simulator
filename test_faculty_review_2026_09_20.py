"""The twelve magnitudes the faculty reviewed on 2026-09-20.

Each test pins one decision, so a later change cannot quietly undo the review.
"""
import pytest

import acs_reperfusion as acs
import asthma_ventilation as vent
import family_engine as fe
import glucose_rescue as glu
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


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


def test_1_no_bronchodilator_works_in_one_minute(engine):
    """Decision 1: the nebulized dose arrives over an onset."""
    state, _ = course(engine, "asthma", "asthma_24f",
                      ["Give albuterol 5 mg nebulized. Reassess in 1 minute."])
    assert state["family_state"]["bronchodilator_pending"] > .5
    early = state["family_state"]["bronchodilation"]
    execute_family_bundle(state, parse_family_actions("Reassess in 8 minutes."))
    assert state["family_state"]["bronchodilation"] > early * 2
    assert vent and fe.BRONCHODILATOR_ONSET_MIN >= 5


def test_2_a_single_dose_fades_before_ninety_minutes(engine):
    """Decision 2: accelerate the fade so continuous nebulization earns its place."""
    single, _ = course(engine, "asthma", "asthma_24f",
                       ["Give albuterol 5 mg nebulized and methylprednisolone 125 mg IV. Reassess in 10 minutes.",
                        "Reassess in 30 minutes."])
    continuous, _ = course(engine, "asthma", "asthma_24f",
                           ["Start continuous albuterol nebulization. Give methylprednisolone 125 mg IV. "
                            "Reassess in 10 minutes.", "Reassess in 30 minutes."])
    # At forty minutes, not ninety, the two courses already differ.
    assert single["observable"]["respiratory_rate"] > continuous["observable"]["respiratory_rate"] + 3
    assert fe.BRONCHODILATOR_DECAY_PER_MIN < .986


def test_3_magnesium_helps_but_not_as_much(engine):
    """Decision 3: it works, and less than the other interventions."""
    magnesium, _ = course(engine, "asthma", "asthma_24f",
                          ["Give magnesium sulfate 2 g IV. Reassess in 20 minutes."])
    nothing, _ = course(engine, "asthma", "asthma_24f", ["Reassess in 20 minutes."])
    albuterol, _ = course(engine, "asthma", "asthma_24f",
                          ["Give albuterol 5 mg nebulized. Reassess in 20 minutes."])
    residual = lambda s: s["family_state"]["obstruction"] - s["family_state"]["bronchodilation"]
    assert residual(magnesium) < residual(nothing)
    assert residual(magnesium) > residual(albuterol)
    assert fe.MAGNESIUM["max_bronchodilation"] <= .12


def test_4_the_practical_target_is_a_ph_of_seven_twenty(engine):
    """Decision 4: pH 7.20 is the target; the PaCO2 has no rigid ceiling."""
    assert vent.PH_PRACTICAL_TARGET == 7.20 and vent.PACO2_CLASSIC_REFERENCE == 90
    note = vent.hypercapnia_note(7.06, 96)
    assert "practical target" in note and "does not by itself mean raising the minute ventilation" in note
    assert "reference and not a rigid limit" in note
    assert vent.hypercapnia_note(7.28, 70) == ""


def test_5_the_av_block_is_conditional(engine):
    """Decision 5: conditional, but not rare."""
    state, labels = course(engine, "acs", "acs_54m_inferior", ["Reassess in 50 minutes."])
    assert "atrioventricular block" in labels
    spared = {"omi": True, "active_occlusion": True, "territory": "inferior",
              "rv_involvement": False, "pci_capable": True, "av_block_risk": False}
    other = encounter(engine, "acs", "acs_54m_inferior")["state"]
    other["encounter_spec"]["clinical_case"]["engine"]["coronary"] = spared
    execute_family_bundle(other, parse_family_actions("Reassess in 50 minutes."))
    assert other["family_state"].get("av_block_at") is None


def test_6_two_hours_without_reperfusion_still_fibrillates(engine):
    state, labels = course(engine, "acs", "acs_54m_inferior",
                           ["Reassess in 60 minutes.", "Reassess in 60 minutes."])
    assert "Ventricular fibrillation" in labels
    assert acs.VF_AT_MIN == 120


def test_7_the_troponin_follows_the_faculty_curve():
    """Decision 7: the illustrative hs-cTnI curve, timed from the pain."""
    for minutes, expected in acs.TROPONIN_CURVE:
        assert round(acs._curve(minutes)) == expected
    # It rises within the window and holds at its peak rather than growing for ever.
    assert acs._curve(90) < acs._curve(150) < acs._curve(300)
    assert acs._curve(1440) == acs.TROPONIN_CURVE[-1][1]


def test_7b_a_case_with_no_artery_shut_keeps_its_authored_value(engine):
    state, _ = course(engine, "acs", "acs_66f_nonst", ["Order troponin. Reassess in 60 minutes."])
    assert state["diagnostics"]["troponin"]["value_ng_l"] == 180


def test_7c_reperfusion_is_washout_not_failure(engine):
    state, labels = course(engine, "acs", "acs_54m_inferior",
                           ["Activate the cath lab. Reassess in 60 minutes.", "Reassess in 40 minutes."])
    assert "washout, which is not a failed procedure" in labels


def test_8_a_long_occlusion_ends_in_shock_and_a_lost_wall(engine):
    """Decision 8: it goes towards cardiogenic shock and a permanently lost wall."""
    state, _ = course(engine, "acs", "acs_61m_posterior",
                      ["Reassess in 60 minutes.", "Reassess in 55 minutes."])
    f = state["family_state"]
    assert f["lv_function"] <= acs.SHOCK_LV and acs.in_shock(f)
    execute_family_bundle(state, parse_family_actions("Activate the cath lab. Reassess in 95 minutes."))
    # The wall recovers only partly: the ceiling is below normal.
    assert state["family_state"]["lv_function"] < acs.LV_RECOVERY_CEILING


def test_11_the_relief_after_haemostasis_is_faster_now(engine):
    """Decision 11: accelerate it."""
    assert fe.GI_BLEED["recovery_tau_min"] <= 45
    state, _ = course(engine, "gi_bleed", "gi_bleed_57m",
                      ["Transfuse 2 units packed red blood cells over 60 minutes. Give pantoprazole 80 mg IV. "
                       "Consult gastroenterology for urgent endoscopy. Reassess in 60 minutes.",
                       "Transfuse 1 unit packed red blood cells over 30 minutes. Reassess in 60 minutes."])
    assert state["observable"]["hr"] < 100


def test_12_overcorrection_buys_a_rebound_when_the_pancreas_works(engine):
    """Decision 12: the punishment is the rebound, not the number."""
    overshoot, labels = course(engine, "hypoglycemia", "hypoglycemia_76f",
                               ["Give dextrose 50 g IV. Reassess in 10 minutes."])
    assert "correction overshot" in labels
    assert overshoot["family_state"]["rebound_at"] is not None
    execute_family_bundle(overshoot, parse_family_actions("Reassess in 60 minutes."))
    measured, _ = course(engine, "hypoglycemia", "hypoglycemia_76f",
                         ["Give dextrose 25 g IV. Reassess in 10 minutes.", "Reassess in 60 minutes."])
    assert glu.rebound_fall(overshoot["family_state"]) > 0
    assert glu.rebound_fall(measured["family_state"]) == 0


def test_12b_type_one_diabetes_has_no_rebound(engine):
    state, labels = course(engine, "hypoglycemia", "hypoglycemia_28m",
                           ["Give dextrose 50 g IV. Reassess in 40 minutes."])
    assert "correction overshot" not in labels
    assert state["family_state"].get("rebound_at") is None
