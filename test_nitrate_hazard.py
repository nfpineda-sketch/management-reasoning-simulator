"""Nitroglycerin in a preload-dependent patient, only when a generated case includes one.

Faculty decision (2026-09-18): severe hypotension from nitroglycerin in
valvular disease, PDE5-inhibitor use and similar conditions is modeled only when
the AI-generated case includes such a condition. The case declares it in
engine.nitrate_hazard and leaves a discoverable cue; the gate rejects a hazard
declared without a cue and a condition described without being declared. The
engine then gives nitroglycerin a rapid, deep fall that is best rescued by
stopping it and giving volume. Bank cases and PS001 are unchanged.
"""
from copy import deepcopy

import pytest

import coupled_encounter as adapter
import generated_case
from generated_case_schema import CASE_SCHEMA, compile_case
from generated_case_validation import ContractValidationError, safe_validation_codes
from nitrate_hazard import CAUSES
from test_coupled_encounter import patient, run
from test_generated_case import novel_payload
from test_generated_engine import wait


def codes(raw):
    try:
        compile_case(raw)
    except ContractValidationError as error:
        return {issue["code"] for issue in error.issues}
    return set()


def with_hazard(cause, **history):
    raw = novel_payload()
    raw["engine"]["nitrate_hazard"] = {"cause": cause} if cause else None
    raw["history"].update(history)
    return raw


def exam(raw, cardiac):
    for item in raw["examination"]:
        if item["area"] == "Cardiac":
            item["finding"] = cardiac
    return raw


def test_the_field_is_part_of_the_contract_and_names_every_cause():
    field = CASE_SCHEMA["properties"]["engine"]["properties"]["nitrate_hazard"]
    assert "nitrate_hazard" in CASE_SCHEMA["properties"]["engine"]["required"]
    assert set(field["anyOf"][0]["properties"]["cause"]["enum"]) == set(CAUSES)
    for cause in CAUSES:
        assert f"- {cause} (" in generated_case.AUTHOR_INSTRUCTIONS


def test_a_case_without_the_condition_compiles_unchanged():
    assert not codes(novel_payload()) & {"NITRATE_HAZARD_UNDISCOVERABLE", "NITRATE_HAZARD_UNDECLARED"}


def test_a_declared_pde5_inhibitor_with_its_cue_compiles():
    raw = with_hazard("pde5_inhibitor", medications=["I took sildenafil 100 mg last night; I also stopped my prednisone five days ago."])
    assert not codes(raw) & {"NITRATE_HAZARD_UNDISCOVERABLE", "NITRATE_HAZARD_UNDECLARED"}


def test_a_declared_hazard_the_resident_cannot_discover_is_rejected():
    assert "NITRATE_HAZARD_UNDISCOVERABLE" in codes(with_hazard("pde5_inhibitor"))


def test_a_described_condition_that_is_not_declared_is_rejected():
    raw = with_hazard(None, medications=["I took tadalafil yesterday evening and stopped my prednisone five days ago."])
    assert "NITRATE_HAZARD_UNDECLARED" in codes(raw)


def test_a_negated_mention_is_not_a_condition():
    raw = with_hazard(None, medications=["I stopped my prednisone five days ago.", "I have not taken sildenafil or similar drugs."])
    assert "NITRATE_HAZARD_UNDECLARED" not in codes(raw)


def test_aortic_stenosis_is_discoverable_from_a_murmur():
    raw = exam(with_hazard("severe_aortic_stenosis"), "Slow-rising pulse; harsh ejection systolic murmur at the right upper sternal edge.")
    assert "NITRATE_HAZARD_UNDISCOVERABLE" not in codes(raw)
    assert "NITRATE_HAZARD_UNDISCOVERABLE" in codes(with_hazard("severe_aortic_stenosis"))


def test_rv_infarction_needs_both_the_inferior_ecg_and_an_abnormal_rv():
    raw = with_hazard("right_ventricular_infarction")
    raw["ecg_profile"] = "st_elevation_inferior"
    pocus = next(study for study in raw["investigations"] if study["id"] == "pocus")
    assert "NITRATE_HAZARD_UNDISCOVERABLE" in codes(raw)
    next(item for item in pocus["result"] if item["field"] == "rv")["value"] = "Dilated and hypokinetic; larger than the LV; no D-sign"
    assert "NITRATE_HAZARD_UNDISCOVERABLE" not in codes(raw)


def test_the_new_codes_are_safe_to_log():
    error = ContractValidationError([{"code": "NITRATE_HAZARD_UNDECLARED", "path": "case", "message": "x", "details": {}}])
    assert safe_validation_codes(error) == ["NITRATE_HAZARD_UNDECLARED"]


# Engine ---------------------------------------------------------------------

NITRO = {"type": "nitroglycerin", "rate_mcg_min": 100, "operation": "start"}
STOP = {"type": "nitroglycerin", "operation": "stop"}
FLUID = {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}


def preload_dependent(cause):
    state = patient(effective_volume=.7, vasomotor_tone=.7, inflammatory_drive=0.0, sympathetic_drive=.5,
                    tissue_perfusion=.8, cardiac_function=.8, vasoplegia_severity=0.0, af_burden=0.0,
                    af_causal_weight=0.0, pulmonary_congestion=.05, low_flow_burden=0.0)
    case = state["encounter_spec"]["clinical_case"]
    case["engine"]["core_profile"]["infection_active"] = False
    case["engine"]["nitrate_hazard"] = {"cause": cause} if cause else None
    for observable in (state["observable"], case["observable"]):
        observable["rhythm"] = "Sinus rhythm"
    adapter.initialize(state)
    return state


def after_nitroglycerin(cause):
    state = preload_dependent(cause)
    run(state, NITRO, wait(10))
    return state


def test_without_a_declared_hazard_nitroglycerin_is_modest():
    state = after_nitroglycerin(None)
    untreated = preload_dependent(None)
    run(untreated, wait(10))
    assert abs(untreated["observable"]["sbp"] - state["observable"]["sbp"]) < 10
    assert not state["generated_state"].get("nitrate_drop")


@pytest.mark.parametrize("cause", sorted(CAUSES))
def test_with_a_declared_hazard_the_fall_is_rapid_and_deep(cause):
    # The same dose, the same minute, the same patient without the condition.
    assert after_nitroglycerin(None)["observable"]["sbp"] - after_nitroglycerin(cause)["observable"]["sbp"] >= 30


def test_stopping_with_volume_restores_pressure_faster_than_stopping_alone():
    stopped = after_nitroglycerin("pde5_inhibitor")
    rescued = deepcopy(stopped)
    run(stopped, STOP, wait(10))
    run(rescued, STOP, FLUID, wait(10))
    assert rescued["observable"]["sbp"] >= stopped["observable"]["sbp"] + 10
    run(stopped, wait(30))
    assert stopped["generated_state"]["nitrate_drop"] < 5  # it still resolves, only slowly


def test_continuing_nitroglycerin_keeps_the_pressure_down_despite_volume():
    state = after_nitroglycerin("pde5_inhibitor")
    run(state, FLUID, wait(20))
    assert state["generated_state"]["nitrate_drop"] > 40


def test_a_negated_finding_elsewhere_in_the_cardiac_exam_does_not_hide_the_murmur():
    raw = exam(with_hazard("severe_aortic_stenosis"), "No carotid bruit; harsh ejection systolic murmur radiating to the carotids.")
    assert "NITRATE_HAZARD_UNDISCOVERABLE" not in codes(raw)
    raw = exam(with_hazard("severe_aortic_stenosis"), "Regular rhythm; no systolic murmur.")
    assert "NITRATE_HAZARD_UNDISCOVERABLE" in codes(raw)


# Provenance -----------------------------------------------------------------

def test_a_launched_case_records_which_rules_its_draft_had_to_repair():
    # The paid sildenafil run needed one correction and did not say why.
    from test_generated_case import AuthorClient, clean_base
    from generated_case import generate_ai_encounter

    class Client(AuthorClient):
        def create(self, **kwargs):
            drafts = sum(c["text"]["format"]["name"] != "clinical_consistency_review" for c in self.calls)
            if kwargs["text"]["format"]["name"] != "clinical_consistency_review":
                self.payload = with_hazard(None, medications=["I took sildenafil last night and stopped my prednisone five days ago."]) \
                    if drafts == 0 else with_hazard("pde5_inhibitor", medications=["I took sildenafil last night and stopped my prednisone five days ago."])
            return super().create(**kwargs)

    result = generate_ai_encounter("R1-05", clean_base(), client=Client(), seed=7)
    provenance = result["spec"]["provenance"]
    assert provenance["correction_count"] == 1
    assert provenance["correction_validation_codes"] == ["NITRATE_HAZARD_UNDECLARED"]
    assert result["spec"]["clinical_case"]["engine"]["nitrate_hazard"] == {"cause": "pde5_inhibitor"}


def test_a_case_that_needed_no_repair_records_no_codes():
    from test_generated_case import AuthorClient, clean_base
    from generated_case import generate_ai_encounter
    provenance = generate_ai_encounter("R1-05", clean_base(), client=AuthorClient(), seed=7)["spec"]["provenance"]
    assert provenance["correction_count"] == 0 and provenance["correction_validation_codes"] == []


def test_even_a_usual_low_dose_collapses_the_pressure():
    # With sildenafil, 20 mcg/min is not a safe small dose: the fall saturates early.
    low = {"type": "nitroglycerin", "rate_mcg_min": 20, "operation": "start"}
    control, hazard = preload_dependent(None), preload_dependent("pde5_inhibitor")
    run(control, low, wait(10))
    run(hazard, low, wait(10))
    assert control["observable"]["sbp"] - hazard["observable"]["sbp"] >= 25
