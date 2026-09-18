"""Pulmonary oedema responds to the resident's decisions as faculty specified.

Faculty decisions (2026-09-18) on docs/PULMONARY_EDEMA_PHYSIOLOGY_PROPOSAL.md:
1. NIV's benefit outweighs a moderate fluid bolus; without positive pressure the
   same bolus visibly worsens the patient.
2. Nitroglycerin lowers pressure up to 30% of baseline, and may be given as IV
   boluses (1000-2000 mcg) alone or with an infusion.
3. EPAP recruits more and lowers pressure a little.
4. With NIV and nitroglycerin the patient improves quickly.
5. Furosemide has almost no effect before the oedema resolves, and acts in
   patients with expanded circulating volume.
"""
import pytest

from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

NIV = "Start BiPAP IPAP 10 EPAP 5 FiO2 60%. "
WEAN = "Stop nitroglycerin. Start oxygen 4 L/min nasal cannula. Reassess in 30 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(engine, variant, *orders):
    state = encounter(engine, "pulmonary_edema", "pulmonary_edema_" + variant)["state"]
    snapshots = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], (order, result["clarification"])
        snapshots.append(dict(state["observable"]))
    return state, snapshots


@pytest.mark.parametrize("variant", ["58m", "75f"])
def test_niv_benefit_outweighs_a_500_ml_bolus(engine, variant):
    _, (before, after, later) = run(
        engine, variant,
        NIV + "Give nitroglycerin 2000 mcg IV bolus. Start nitroglycerin infusion 100 mcg/min. Reassess in 10 minutes.",
        "Give 500 mL normal saline IV over 15 minutes. Reassess in 15 minutes.",
        "Reassess in 15 minutes.")
    assert after["respiratory_rate"] <= before["respiratory_rate"]
    assert after["spo2"] >= 97 and later["respiratory_rate"] <= after["respiratory_rate"]


@pytest.mark.parametrize("variant", ["58m", "75f"])
def test_without_positive_pressure_the_same_bolus_worsens_the_patient(engine, variant):
    _, (before, after) = run(engine, variant,
                             "Start oxygen 15 L/min non-rebreather mask. Reassess in 5 minutes.",
                             "Give 500 mL normal saline IV over 15 minutes. Reassess in 15 minutes.")
    assert after["spo2"] <= before["spo2"] - 4
    assert after["respiratory_rate"] >= before["respiratory_rate"] + 4
    assert after["work_of_breathing"] == "Severe"


@pytest.mark.parametrize("variant, baseline", [("58m", 218), ("75f", 164)])
def test_nitroglycerin_lowers_pressure_at_most_30_percent_plus_congestion_relief(engine, variant, baseline):
    _, snapshots = run(engine, variant, NIV + "Start nitroglycerin infusion 200 mcg/min. Reassess in 30 minutes.")
    # Nitroglycerin up to 30% of baseline and relief of congestion up to 10%.
    assert snapshots[-1]["sbp"] >= round(baseline * .6)


def test_an_iv_bolus_acts_fast_and_wears_off(engine):
    _, (early, late) = run(engine, "58m", NIV + "Give nitroglycerin 2000 mcg IV bolus. Reassess in 5 minutes.",
                           "Reassess in 30 minutes.")
    assert early["sbp"] < 160 < late["sbp"]


@pytest.mark.parametrize("text, dose", [
    ("Give nitroglycerin 2000 mcg IV bolus.", 2000.0),
    ("Nitroglycerin 1 mg IV push.", 1000.0),
    ("Administra bolo de nitroglicerina 1000 mcg IV.", 1000.0),
])
def test_an_iv_bolus_is_understood(text, dose):
    assert parse_family_actions(text)["actions"] == [{"type": "nitroglycerin_bolus", "dose_mcg": dose, "route": "IV"}]


def test_a_sublingual_dose_is_still_questioned_and_names_both_supported_forms():
    [action] = parse_family_actions("Give nitroglycerin 400 mcg sublingual.")["actions"]
    assert action["type"] == "clarification"
    assert "continuous IV infusion or an IV bolus" in action["message"]


def test_the_pressure_is_no_longer_a_step_function_of_the_rate(engine):
    # Returning to 100 mcg/min after recovery no longer restores the 10-minute value exactly.
    _, snapshots = run(engine, "58m",
                       NIV + "Start nitroglycerin infusion 100 mcg/min. Reassess in 10 minutes.",
                       "Increase nitroglycerin to 200 mcg/min. Reassess in 30 minutes.",
                       "Decrease nitroglycerin to 100 mcg/min. Reassess in 20 minutes.")
    assert snapshots[2]["sbp"] != snapshots[0]["sbp"]


@pytest.mark.parametrize("variant", ["58m", "75f"])
def test_higher_epap_recruits_more(engine, variant):
    _, (low,) = run(engine, variant, "Start BiPAP IPAP 10 EPAP 5 FiO2 60%. Start nitroglycerin infusion 100 mcg/min. Reassess in 20 minutes.")
    _, (high,) = run(engine, variant, "Start BiPAP IPAP 14 EPAP 8 FiO2 60%. Start nitroglycerin infusion 100 mcg/min. Reassess in 20 minutes.")
    assert high["respiratory_rate"] < low["respiratory_rate"]
    assert high["sbp"] < low["sbp"]


@pytest.mark.parametrize("variant", ["58m", "75f"])
def test_niv_and_nitroglycerin_resolve_the_oedema_within_half_an_hour(engine, variant):
    _, snapshots = run(engine, variant,
                       NIV + "Give nitroglycerin 2000 mcg IV bolus. Reassess in 5 minutes.",
                       "Give nitroglycerin 1000 mcg IV bolus. Start nitroglycerin infusion 100 mcg/min. Reassess in 25 minutes.")
    assert snapshots[-1]["respiratory_rate"] <= 18
    assert snapshots[-1]["work_of_breathing"] in {"Normal", "Mildly increased"}
    _, untreated = run(engine, variant, "Reassess in 30 minutes.")
    assert untreated[-1]["respiratory_rate"] > 30


def weaned(engine, variant, furosemide_first, furosemide_after):
    first = NIV + "Give nitroglycerin 2000 mcg IV bolus. Start nitroglycerin infusion 100 mcg/min. "
    first += "Give furosemide 80 mg IV. " if furosemide_first else ""
    wean = ("Give furosemide 80 mg IV. " if furosemide_after else "") + WEAN
    return run(engine, variant, first + "Reassess in 45 minutes.", wean,
               "Reassess in 30 minutes.", "Reassess in 30 minutes.")[1][-1]


def test_furosemide_after_resolution_prevents_relapse_in_volume_overload(engine):
    none = weaned(engine, "75f", False, False)
    early = weaned(engine, "75f", True, False)
    late = weaned(engine, "75f", False, True)
    assert late["respiratory_rate"] < none["respiratory_rate"] and late["spo2"] > none["spo2"]
    # Given before the oedema resolved, it has almost no effect.
    assert abs(early["respiratory_rate"] - none["respiratory_rate"]) <= 1


def test_without_excess_volume_there_is_little_relapse_to_prevent(engine):
    none = weaned(engine, "58m", False, False)
    late = weaned(engine, "58m", False, True)
    assert none["respiratory_rate"] <= 22 and abs(late["respiratory_rate"] - none["respiratory_rate"]) <= 1
