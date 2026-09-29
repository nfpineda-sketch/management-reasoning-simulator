"""The POCUS of a bleeding patient reads the filling the engine models (faculty, 2026-09-29).

Replacement fills the IVC and the LV cavity; bleeding that goes on and crystalloid
that has left the vessels empty them again; a vasopressor holds the pressure without
filling anything. The cavity and the contraction are separate findings.
"""
import pytest

import language
from family_engine import GI_BLEED_POCUS, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import VARIANTS, encounter
from test_curriculum_trajectories import load_engine

SCAN = "Perform bedside POCUS."
TWO_UNITS = "Transfuse 2 units packed red cells over 30 minutes. Reassess in 35 minutes."
ARRIVAL = {"gi_bleed_57m": ("0.9 cm; near-complete inspiratory collapse",
                            "Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole"),
           "gi_bleed_72f": ("1.1 cm; >50% inspiratory collapse", "Hyperdynamic contraction")}


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def scans(engine, orders, variant="gi_bleed_57m", family="gi_bleed"):
    state = encounter(engine, family, variant)["state"]
    found = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        if order == SCAN:
            found.append(dict(state["diagnostics"]["pocus"]))
    return state, found


def ivc_position(scan):
    return GI_BLEED_POCUS["ivc"].index(scan["ivc"])


@pytest.mark.parametrize("variant", sorted(ARRIVAL))
def test_the_arrival_scan_is_the_one_the_case_wrote(engine, variant):
    _, (scan,) = scans(engine, [SCAN], variant)
    assert (scan["ivc"], scan["lv"]) == ARRIVAL[variant]


def test_blood_fills_the_cava_and_ends_the_obliteration_without_calming_the_heart(engine):
    _, (scan,) = scans(engine, [TWO_UNITS, SCAN])
    assert scan["ivc"] == "1.5 cm; about 50% inspiratory collapse"
    assert scan["lv"] == "Cavity of normal size with hyperdynamic contraction"


def test_the_contraction_settles_only_once_the_bleeding_is_controlled_and_the_patient_recovers(engine):
    state, (before, after) = scans(engine, [
        TWO_UNITS.replace("Reassess in 35 minutes.", "Give pantoprazole 80 mg IV. "
                          "Consult gastroenterology for urgent endoscopy. Reassess in 35 minutes."),
        SCAN, "Reassess in 60 minutes.", SCAN])
    assert state["family_state"]["endoscopy_at"] is not None
    assert "hyperdynamic" in before["lv"] and after["lv"] == "Cavity of normal size with normal contraction"


def test_crystalloid_that_leaves_the_vessels_leaves_the_cava_empty_again(engine):
    state, (early, late) = scans(engine, ["Give 1000 mL normal saline IV over 15 minutes. Reassess in 15 minutes.",
                                          SCAN, "Reassess in 62 minutes.", SCAN])
    assert state["family_state"]["fluid_delivered_ml"] == pytest.approx(1000)
    # A litre that the model keeps only briefly never showed as a refilled cava, and an
    # hour later the patient is emptier than on arrival (the old rule said 1.5 cm).
    assert ivc_position(early) == ivc_position({"ivc": ARRIVAL["gi_bleed_57m"][0]})
    assert late["ivc"] == "0.7 cm; complete inspiratory collapse"
    assert "complete obliteration" in late["lv"]


def test_bleeding_that_goes_on_empties_the_cava(engine):
    _, (scan,) = scans(engine, ["Reassess in 60 minutes.", SCAN], "gi_bleed_72f")
    assert scan["ivc"] == "0.9 cm; near-complete inspiratory collapse"
    assert scan["lv"] == "Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole"


def test_a_vasopressor_raises_the_pressure_without_filling_anything(engine):
    state, (scan,) = scans(engine, ["Start norepinephrine 0.1 mcg/kg/min. Reassess in 15 minutes.", SCAN])
    assert state["observable"]["sbp"] > 95
    assert (scan["ivc"], scan["lv"]) == ARRIVAL["gi_bleed_57m"]


def test_positive_pressure_keeps_the_diameter_and_withholds_the_respiratory_variation(engine):
    _, (scan,) = scans(engine, ["Give ketamine 50 mg IV and intubate VC/AC FiO2 100% PEEP 5. Reassess in 5 minutes.",
                                SCAN])
    assert scan["ivc"] == "0.9 cm; respiratory variation not assessable during positive-pressure support"


def test_other_families_keep_their_own_rule(engine):
    pneumonia = next(variant for family, variant in VARIANTS if family == "pneumonia")
    _, (scan,) = scans(engine, ["Give 1500 mL normal saline IV over 30 minutes. Reassess in 30 minutes.", SCAN],
                       pneumonia, "pneumonia")
    assert scan["ivc"] == "2.0 cm; <50% inspiratory collapse"


def test_every_recomputed_finding_is_said_in_spanish():
    findings = list(GI_BLEED_POCUS["ivc"]) + [
        text.format(contraction=contraction) for text in GI_BLEED_POCUS["lv"]
        for contraction in ("hyperdynamic contraction", "normal contraction")]
    findings.append("0.9 cm; respiratory variation not assessable during positive-pressure support")
    for finding in findings:
        spanish = language.say(finding, "es")
        assert spanish != finding and not any(word in spanish for word in ("collapse", "cavity", "contraction")), spanish
