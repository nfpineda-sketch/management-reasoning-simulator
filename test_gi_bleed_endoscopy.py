"""Hemostasis in the bank GI bleed (faculty decision 2026-09-19).

The bleeding used to run at the same rate forever: calling gastroenterology never
led to an endoscopy and pantoprazole did nothing. Now gastroenterology performs
the endoscopy 60 minutes after the call once SBP >= 90 and hemoglobin >= 7 (or
blood is running); before that it is deferred and re-checked every 15 minutes,
telling the resident once per order. Endoscopy leaves 10% of the bleeding;
pantoprazole leaves 80% before endoscopy only. Once the bleeding is controlled
and hemoglobin is at least 7 the compensatory tachycardia eases, and a heparin
bolus given in error is cleared.
"""
import pytest

from family_engine import GI_BLEED, _gi_bleeding_fraction, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

BLOOD_PPI_GI = ("Transfuse 2 units packed red blood cells over 60 minutes. Give pantoprazole 80 mg IV. "
                "Consult gastroenterology for urgent endoscopy. Reassess in 30 minutes.")


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(engine, variant, orders):
    state = encounter(engine, "gi_bleed", variant)["state"]
    procedures = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        procedures += [s for s in result["action_summaries"] if s.get("type") == "procedure"]
    return state, procedures


@pytest.mark.parametrize("variant", ["gi_bleed_57m", "gi_bleed_72f"])
def test_a_resuscitated_patient_gets_endoscopy_an_hour_after_the_call(engine, variant):
    state, procedures = run(engine, variant, [BLOOD_PPI_GI, "Reassess in 30 minutes.", "Reassess in 30 minutes."])
    assert state["family_state"]["endoscopy_at"] == GI_BLEED["endoscopy_after_consult_min"]
    assert [p["time_min"] for p in procedures] == [60]
    assert "bleeding controlled" in procedures[0]["label"]


@pytest.mark.parametrize("variant", ["gi_bleed_57m", "gi_bleed_72f"])
def test_hemostasis_stops_the_fall_in_hemoglobin(engine, variant):
    state, _ = run(engine, variant, [BLOOD_PPI_GI, "Reassess in 60 minutes."])
    after_transfusion = state["family_state"]["hemoglobin"]
    execute_family_bundle(state, parse_family_actions("Reassess in 60 minutes."))
    assert after_transfusion - state["family_state"]["hemoglobin"] < .1


def test_an_unresuscitated_patient_is_deferred_then_scoped_after_blood(engine):
    state, procedures = run(engine, "gi_bleed_57m", [
        "Consult gastroenterology for urgent endoscopy. Reassess in 60 minutes.",
        "Reassess in 30 minutes.",
        "Transfuse 2 units packed red blood cells over 60 minutes. Reassess in 60 minutes.",
    ])
    deferrals = [p for p in procedures if "defers" in p["label"]]
    # One notice per order, not one for each 15-minute re-check.
    assert [p["time_min"] for p in deferrals] == [60, 75, 105]
    assert "SBP" in deferrals[0]["label"]
    assert state["family_state"]["endoscopy_at"] > 90
    assert state["family_state"]["endoscopy_at"] % GI_BLEED["endoscopy_retry_min"] == 0


def test_without_a_call_there_is_no_endoscopy(engine):
    state, procedures = run(engine, "gi_bleed_57m", [
        "Transfuse 2 units packed red blood cells over 60 minutes. Reassess in 120 minutes."])
    assert procedures == [] and state["family_state"].get("endoscopy_at") is None


def test_pantoprazole_slows_the_bleeding_only_before_endoscopy():
    assert _gi_bleeding_fraction({}) == 1.0
    assert _gi_bleeding_fraction({"ppi": True}) == GI_BLEED["bleeding_with_ppi"]
    assert _gi_bleeding_fraction({"ppi": True, "endoscopy_at": 70}) == GI_BLEED["bleeding_after_hemostasis"]


def test_pantoprazole_leaves_hemoglobin_higher(engine):
    without, _ = run(engine, "gi_bleed_57m", ["Reassess in 60 minutes."])
    with_ppi, _ = run(engine, "gi_bleed_57m", ["Give pantoprazole 80 mg IV. Reassess in 60 minutes."])
    assert with_ppi["family_state"]["hemoglobin"] > without["family_state"]["hemoglobin"]


def test_the_tachycardia_eases_once_bleeding_is_controlled(engine):
    state, _ = run(engine, "gi_bleed_57m", [BLOOD_PPI_GI, "Reassess in 60 minutes."])
    controlled = state["observable"]["hr"]
    for _ in range(3):
        execute_family_bundle(state, parse_family_actions("Reassess in 60 minutes."))
    assert state["observable"]["hr"] < controlled - 8
    assert state["family_state"]["hemostasis_relief"] > .4


def test_returning_anemia_reverses_the_relief(engine):
    """One unit lifts hemoglobin over 7 briefly; the residual bleeding takes it back."""
    state, _ = run(engine, "gi_bleed_57m", [
        "Transfuse 1 unit packed red blood cells over 30 minutes. Consult gastroenterology. Reassess in 90 minutes."])
    early = state["family_state"]["hemostasis_relief"]
    execute_family_bundle(state, parse_family_actions("Reassess in 120 minutes."))
    assert state["family_state"]["hemoglobin"] < GI_BLEED["recovery_min_hemoglobin"]
    assert state["family_state"]["hemostasis_relief"] < early


def test_a_heparin_bolus_is_cleared(engine):
    state, _ = run(engine, "gi_bleed_57m", ["Give heparin 5000 units IV. Reassess in 60 minutes."])
    after_one_hour = state["family_state"]["anticoagulant_exposure"]
    execute_family_bundle(state, parse_family_actions("Reassess in 120 minutes."))
    assert state["family_state"]["anticoagulant_exposure"] < after_one_hour * .2
