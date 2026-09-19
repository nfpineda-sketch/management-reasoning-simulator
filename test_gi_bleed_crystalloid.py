"""In active GI bleeding, crystalloid alone must do less than blood.

Faculty request (2026-09-18): 2 L of saline restored pressure and capillary
refill almost as well as a transfusion, with haemoglobin falling only 0.2 g/dL.
Crystalloid now buys less pressure, most of it fades as fluid leaves the
vessels, and it dilutes haemoglobin.
"""
import pytest

from family_engine import GI_BLEED, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

SALINE = "Give 2000 mL normal saline IV over 20 minutes. Order hemoglobin. Reassess in 20 minutes."
BLOOD = "Transfuse 2 units packed red blood cells over 60 minutes. Order hemoglobin. Reassess in 20 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, variant, first, minutes=(20, 20)):
    state = encounter(engine, "gi_bleed", variant)["state"]
    snapshots = []
    for index, order in enumerate([first] + [f"Order hemoglobin. Reassess in {m} minutes." for m in minutes]):
        execute_family_bundle(state, parse_family_actions(order))
        snapshots.append((dict(state["observable"]), state["family_state"]["hemoglobin"]))
    return snapshots


@pytest.mark.parametrize("variant", ["gi_bleed_57m", "gi_bleed_72f"])
def test_the_pressure_bought_by_crystalloid_fades_while_bleeding_continues(engine, variant):
    snapshots = course(engine, variant, SALINE)
    (early, _), (_, _), (late, _) = snapshots
    assert late["sbp"] < early["sbp"] and late["crt"] > early["crt"]


@pytest.mark.parametrize("variant", ["gi_bleed_57m", "gi_bleed_72f"])
def test_blood_does_more_than_crystalloid_by_the_hour(engine, variant):
    saline = course(engine, variant, SALINE)[-1]
    blood = course(engine, variant, BLOOD)[-1]
    assert blood[0]["sbp"] >= saline[0]["sbp"] + 10
    assert blood[1] > saline[1] + 1.5


def test_crystalloid_dilutes_haemoglobin(engine):
    state = encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]
    control = encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]
    execute_family_bundle(state, parse_family_actions("Give 1000 mL normal saline IV. Reassess in 20 minutes."))
    execute_family_bundle(control, parse_family_actions("Reassess in 20 minutes."))
    drop = control["family_state"]["hemoglobin"] - state["family_state"]["hemoglobin"]
    assert drop == pytest.approx(1000 * GI_BLEED["hemodilution_g_dl_per_ml"], abs=.05)


# Respiratory rate follows the circulation (2026-09-19) -------------------------

@pytest.mark.parametrize("variant", ["gi_bleed_57m", "gi_bleed_72f"])
def test_tachypnoea_eases_with_blood_and_worsens_without_treatment(engine, variant):
    treated = encounter(engine, "gi_bleed", variant)["state"]
    untreated = encounter(engine, "gi_bleed", variant)["state"]
    arrival = treated["observable"]["respiratory_rate"]
    execute_family_bundle(treated, parse_family_actions(
        "Transfuse 2 units packed red blood cells over 60 minutes. Reassess in 60 minutes."))
    execute_family_bundle(untreated, parse_family_actions("Reassess in 60 minutes."))
    assert treated["observable"]["respiratory_rate"] <= arrival - 5
    assert untreated["observable"]["respiratory_rate"] > arrival


def test_the_transfusion_reads_as_units_started():
    # Seen on the response card as "Packed red cells: 2 unit(s) ordered; transfusion started over 60 min".
    from test_timed_administration import bank, bank_case
    one = bank(bank_case("gi_bleed"), "Transfuse 1 unit packed red blood cells. Reassess in 5 minutes.")
    two = bank(bank_case("gi_bleed"), "Transfuse 2 units packed red blood cells over 60 minutes. Reassess in 5 minutes.")
    assert one["action_summaries"][0]["label"] == "Packed red cells 1 unit started"
    assert two["action_summaries"][0]["label"] == "Packed red cells 2 units started over 60 min"
