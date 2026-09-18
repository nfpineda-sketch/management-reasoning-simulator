"""Two gaps seen in the paid sildenafil case.

1. Its POCUS read "At arrival: normal contractility. Current physiology:
   Moderately to severely reduced global contraction". The author wrote a normal
   LV, but the drivers it chose (cardiac_function 0.7, contractile_reserve 0.6)
   make the core read a weak LV from the first minute. A scan now keeps the
   authored finding until the core's own reading changes, and then reports the
   current finding alone.
2. "Chest pressure suggests acute coronary syndrome" was not a working model.
"""
import pytest

import coupled_encounter as adapter
from test_coupled_encounter import patient
from test_curriculum_trajectories import load_engine

AUTHORED = {"lv": "normal contractility", "ivc": "1.2 cm; >50% inspiratory collapse", "lungs": "no B-lines",
            "rv": "smaller than LV; no D-sign; no McConnell sign"}


def weak_core_normal_words():
    state = patient(cardiac_function=.7, contractile_reserve=.6)
    case = state["encounter_spec"]["clinical_case"]
    case["investigations"]["pocus"] = {"duration_min": 2, "result": dict(AUTHORED), "result_bindings": {}}
    return state


def scan(state):
    return adapter.collect(state, "pocus", 2)["result"]


def test_the_core_arrival_reading_is_derived_from_the_authored_drivers():
    state = weak_core_normal_words()
    assert adapter.arrival_core_pocus(state["encounter_spec"]["clinical_case"])["lv"] == \
        "Moderately to severely reduced global contraction"


def test_an_unchanged_physiology_keeps_the_authored_findings_without_an_arrival_prefix():
    result = scan(weak_core_normal_words())
    for key in ("lv", "ivc", "lungs", "rv"):
        assert result[key] == AUTHORED[key]
    assert not any("At arrival" in str(value) for value in result.values())


def test_a_real_change_reports_the_current_finding_alone():
    state = weak_core_normal_words()
    state["coupled_state"]["hidden"].update(cardiac_function=1.0, contractile_reserve=1.0, effective_contractility=1.0)
    result = scan(state)
    assert result["lv"] == "Preserved to hyperdynamic contraction"
    assert result["rv"] == AUTHORED["rv"]


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("text, model", [
    ("Chest pressure suggests acute coronary syndrome. My priority is relieving ischemia.",
     "Chest pressure suggests acute coronary syndrome"),
    ("Hypotension after sildenafil points to vasodilatory shock. My priority is perfusion.",
     "Hypotension after sildenafil points to vasodilatory shock"),
    ("The POCUS is consistent with hypovolemia. My priority is volume.", "The POCUS is consistent with hypovolemia"),
    ("La hipotensión sugiere shock vasodilatador. Mi prioridad es la perfusión.", "La hipotensión sugiere shock vasodilatador"),
])
def test_a_finding_that_suggests_a_diagnosis_is_a_working_model(engine, text, model):
    # The whole statement is kept: the finding the learner reasons from is part of the model.
    assert engine["extract_explicit_reasoning"](text)["problem_representation"] == model


def test_an_order_is_never_the_subject_of_a_suggestion(engine):
    reasoning = engine["extract_explicit_reasoning"]("Give 500 mL NS as the IVC suggests volume responsiveness.")
    assert reasoning.get("problem_representation") is None


# Generation gate ------------------------------------------------------------

import json
from generated_case_schema import compile_case
from generated_case_validation import ContractValidationError
from generated_pocus_consistency import issues as pocus_core_issues
from test_generated_case import novel_payload


def gate_codes(raw):
    try:
        compile_case(raw)
    except ContractValidationError as error:
        return [issue for issue in error.issues if issue["code"] == "POCUS_CORE_MISMATCH"]
    return []


def with_drivers(**hidden):
    raw = novel_payload()
    raw["engine"]["core_profile"]["initial_hidden"].update(hidden)
    return raw


def test_the_default_payload_agrees_with_its_drivers():
    assert gate_codes(novel_payload()) == []


def test_a_normal_lv_with_weak_drivers_is_rejected_with_the_rule_to_fix_it():
    [issue] = gate_codes(with_drivers(cardiac_function=.7, contractile_reserve=.6))
    assert issue["details"] == {"field": "lv", "authored_level": "preserved or hyperdynamic",
                                "core_level": "moderately to severely reduced"}
    assert "cardiac_function x contractile_reserve" in issue["message"]


def test_one_category_apart_is_left_to_the_reviewer():
    # 0.8 x 0.75 = 0.60: the core reads mildly reduced, the author wrote hyperdynamic.
    assert gate_codes(with_drivers(cardiac_function=.8, contractile_reserve=.75)) == []


def test_a_collapsing_ivc_with_full_drivers_is_rejected():
    assert [i["details"]["field"] for i in gate_codes(with_drivers(effective_volume=.8))] == ["ivc"]


def test_no_b_lines_with_heavy_congestion_is_rejected_but_focal_b_lines_are_not_judged():
    assert [i["details"]["field"] for i in gate_codes(with_drivers(pulmonary_congestion=.6))] == ["lungs"]
    raw = with_drivers(pulmonary_congestion=.6)
    pocus = next(study for study in raw["investigations"] if study["id"] == "pocus")
    next(item for item in pocus["result"] if item["field"] == "lungs")["value"] = "Focal B-lines at the right base"
    assert gate_codes(raw) == []


@pytest.mark.parametrize("hidden", [
    {"cardiac_function": .7, "contractile_reserve": .6, "effective_volume": .3, "pulmonary_congestion": .2},
    {"cardiac_function": .9, "contractile_reserve": 1.0, "effective_volume": .7, "pulmonary_congestion": .6},
    {"cardiac_function": .6, "contractile_reserve": .9, "effective_volume": .5, "pulmonary_congestion": .1},
])
def test_the_gate_thresholds_mirror_the_core(hidden):
    # The gate's categories must match the core's own arrival findings.
    from coupled_encounter import arrival_core_pocus
    from generated_pocus_consistency import _b_line_level, _ivc_level, _lv_level
    raw = with_drivers(**hidden)
    case = {"engine": raw["engine"]}
    core = arrival_core_pocus(case)
    for field, classify in (("lv", _lv_level), ("ivc", _ivc_level), ("lungs", _b_line_level)):
        pocus = next(study for study in raw["investigations"] if study["id"] == "pocus")
        next(item for item in pocus["result"] if item["field"] == field)["value"] = core[field]
    assert gate_codes(raw) == []
    assert all(classify(core[field]) is not None for field, classify in
               (("lv", _lv_level), ("ivc", _ivc_level), ("lungs", _b_line_level)))


def test_the_paid_sildenafil_case_would_now_be_sent_back_for_its_lv():
    case = {"engine": {"core_profile": {"initial_hidden": {"cardiac_function": .7, "contractile_reserve": .6,
                                                           "effective_volume": .3, "pulmonary_congestion": .2}}},
            "investigations": {"pocus": {"result": {"lv": "normal contractility", "ivc": "1.2 cm; >50% inspiratory collapse",
                                                    "lungs": "no B-lines"}}}}
    assert [i["details"]["field"] for i in pocus_core_issues(case)] == ["lv"]


# SpO2 anchored to the authored arrival value ---------------------------------

def spo2_patient(authored=96, **hidden):
    state = patient(**hidden)
    case = state["encounter_spec"]["clinical_case"]
    case["observable"]["spo2"] = authored
    state["observable"]["spo2"] = authored
    state["coupled_state"] = {}
    adapter.initialize(state)
    return state


def test_an_authored_room_air_spo2_is_kept_instead_of_falling_to_the_core_equilibrium():
    # The core's room-air target was 94 - 16 x burden: an authored 96% fell to 91%.
    from test_coupled_encounter import run
    from test_generated_engine import wait
    state = spo2_patient(96, pulmonary_congestion=.2, primary_respiratory_burden=.1)
    assert adapter.core_spo2_target(state["coupled_state"]) < 92
    run(state, wait(15))
    assert state["observable"]["spo2"] >= 95


def test_oxygen_still_raises_the_anchored_spo2():
    from test_coupled_encounter import run
    from test_generated_engine import wait
    state = spo2_patient(92, pulmonary_congestion=.2, primary_respiratory_burden=.1)
    run(state, wait(5))
    before = state["observable"]["spo2"]
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4}, wait(10))
    assert state["observable"]["spo2"] > before


def test_a_state_saved_before_the_anchor_behaves_as_before():
    state = spo2_patient(96)
    state["generated_state"].pop("spo2_anchor")
    adapter.prepare_inputs(state)
    assert state["coupled_state"]["physiology_inputs"]["spo2"] == 0


# Respiratory floors at arrival ------------------------------------------------

def respiratory_codes(raw):
    try:
        compile_case(raw)
    except ContractValidationError as error:
        return [issue for issue in error.issues if issue["code"] == "RESPIRATORY_CORE_MISMATCH"]
    return []


def test_the_default_payload_respects_the_core_floors():
    assert respiratory_codes(novel_payload()) == []


def test_normal_breathing_with_congestion_that_forces_tachypnoea_is_rejected():
    # The paid sildenafil case: RR 18 and congestion 0.20; the core raised RR to 24 at once.
    raw = with_drivers(pulmonary_congestion=.2)
    raw["observable"]["respiratory_rate"] = 18
    [issue] = respiratory_codes(raw)
    assert (issue["details"]["field"], issue["details"]["authored"]) == ("respiratory_rate", 18)
    assert "at least 24/min" in issue["message"]


def test_a_high_spo2_under_a_core_cap_is_rejected():
    raw = with_drivers(pulmonary_congestion=.45)
    raw["observable"]["respiratory_rate"] = 34
    fields = {issue["details"]["field"] for issue in respiratory_codes(raw)}
    assert fields == {"spo2"}  # authored 97% against a core cap of 89%


def test_authored_breathing_that_matches_the_floor_passes():
    raw = with_drivers(pulmonary_congestion=.2)
    raw["observable"]["respiratory_rate"] = 24
    assert respiratory_codes(raw) == []


@pytest.mark.parametrize("congestion, minimum_rr", [(.19, 24), (.31, 28), (.43, 32)])
def test_the_gate_floors_mirror_the_core(congestion, minimum_rr):
    from test_coupled_encounter import run
    from test_generated_engine import wait
    state = patient(pulmonary_congestion=congestion)
    state["observable"]["respiratory_rate"] = 12
    run(state, wait(1))
    assert state["observable"]["respiratory_rate"] >= minimum_rr


# LV dip during recovery -------------------------------------------------------

def preserved_heart_state():
    state = patient(cardiac_function=.7, contractile_reserve=1.0, tissue_perfusion=.3)
    state["encounter_spec"]["clinical_case"]["investigations"]["pocus"] = {
        "duration_min": 2, "result": dict(AUTHORED), "result_bindings": {}}
    return state


def test_a_one_category_lv_dip_while_perfusion_recovers_is_not_reported():
    # Sildenafil case: reserve 1.0 -> 0.8 during early low flow read as "mildly reduced"
    # just as pressure, refill and lactate recovered.
    state = preserved_heart_state()
    state["coupled_state"]["hidden"].update(contractile_reserve=.8, effective_contractility=.8, tissue_perfusion=.7)
    assert scan(state)["lv"] == AUTHORED["lv"]


def test_the_same_dip_without_better_perfusion_is_reported():
    state = preserved_heart_state()
    state["coupled_state"]["hidden"].update(contractile_reserve=.8, effective_contractility=.8, tissue_perfusion=.25)
    assert scan(state)["lv"] == "Mildly reduced global contraction"


def test_a_two_category_fall_is_always_reported():
    state = preserved_heart_state()
    state["coupled_state"]["hidden"].update(contractile_reserve=.5, effective_contractility=.5, tissue_perfusion=.7)
    assert scan(state)["lv"] == "Moderately to severely reduced global contraction"


# Repeated consult / admission --------------------------------------------------

def test_a_repeated_consult_or_admission_is_recorded_as_not_repeated():
    from family_engine import execute_family_bundle
    from family_parser import parse_family_actions
    state = patient()
    order = "Consult cardiology. Admit to ICU. Reassess in 5 minutes."
    execute_family_bundle(state, parse_family_actions(order))
    result = execute_family_bundle(state, parse_family_actions(order))
    assert [s.get("repeated") for s in result["action_summaries"] if s["type"] in {"consult", "disposition"}] == [True, True]
    assert [c["service"] for c in state["family_state"]["consultations"]] == ["cardiology"]


# Heart rate and lactate adjustments -------------------------------------------

def test_the_heart_rate_falls_as_perfusion_recovers_beyond_arrival():
    state = patient(tissue_perfusion=.3)
    assert state["generated_state"]["arrival_tissue_perfusion"] == .3
    state["coupled_state"]["hidden"]["tissue_perfusion"] = 1.0
    assert adapter.hr_relief(state) == -adapter.HR_RELIEF_MAX
    state["coupled_state"]["hidden"]["tissue_perfusion"] = .7
    assert adapter.hr_relief(state) == pytest.approx(-12.0)
    state["coupled_state"]["hidden"]["tissue_perfusion"] = .2
    assert adapter.hr_relief(state) == 0


def test_a_state_saved_before_the_adjustments_behaves_as_before():
    state = patient()
    state["generated_state"].pop("arrival_tissue_perfusion")
    assert adapter.hr_relief(state) == 0


def lactate_after(monkeypatch, core_change, minutes, perfusion=.8):
    """Authored lactate 3.2; the core's lactate has moved by core_change after ``minutes``."""
    state = patient()
    state["coupled_state"]["hidden"]["tissue_perfusion"] = perfusion
    g = state["generated_state"]
    state["encounter_spec"]["clinical_case"]["engine"]["initial_labs"]["lactate_mmol_l"] = 3.2
    reference = dict(g["lab_reference"])
    g["lactate_shown"], g["lactate_shown_at"] = 3.2, g["elapsed"]
    g["elapsed"] += minutes
    monkeypatch.setattr(adapter.diagnostic_core, "vbg_transition",
                        lambda s, delay: {"result": {**reference, "lactate_mmol_l": reference["lactate_mmol_l"] + core_change}})
    adapter.project(state)
    return g["values"]["lactate_mmol_l"]


def test_a_falling_lactate_clears_with_a_time_constant(monkeypatch):
    import math
    # The core would show 0.5 mmol/L at once; the displayed value falls with tau 45 min.
    expected = 3.2 - 2.7 * (1 - math.exp(-20 / adapter.LACTATE_CLEARANCE_TAU_MIN))
    assert lactate_after(monkeypatch, -2.7, 20) == pytest.approx(expected)


def test_a_rising_lactate_is_shown_at_once(monkeypatch):
    assert lactate_after(monkeypatch, +1.0, 5) == pytest.approx(4.2)


def test_hypoperfused_tissue_keeps_producing_lactate_whatever_the_core_shows(monkeypatch):
    # Perfusion 0.2 is 0.3 below the threshold: +0.1 x 0.3 mmol/L per minute for 20 minutes.
    assert lactate_after(monkeypatch, -2.7, 20, perfusion=.2) == pytest.approx(3.2 + 0.6)


def test_lactate_starts_from_the_authored_value():
    state = patient()
    g = state["generated_state"]
    assert g["lactate_shown"] == state["encounter_spec"]["clinical_case"]["engine"]["initial_labs"]["lactate_mmol_l"]


def mental_state(history, before, now):
    state = patient()
    g = state["generated_state"]
    g["recent_tissue_perfusion"] = list(history[:-1])
    state["coupled_state"]["hidden"]["tissue_perfusion"] = history[-1]
    state["coupled_state"]["observable"]["mental_status"] = now
    adapter.hold_mental_while_perfusion_falls(state, before)
    return state["coupled_state"]["observable"]["mental_status"]


def test_mental_status_does_not_improve_while_perfusion_falls():
    # Path C: the core woke the patient to Alert at 86/51 as perfusion fell 0.52 -> 0.37.
    assert mental_state([.52, .5, .47, .44, .40, .37], "Drowsy", "Alert") == "Drowsy"


def test_mental_status_improves_while_perfusion_holds_or_rises():
    assert mental_state([.60, .63, .66, .68, .70, .71], "Drowsy", "Alert") == "Alert"


def test_deterioration_is_never_held():
    assert mental_state([.52, .5, .47, .44, .40, .37], "Drowsy", "Obtunded") == "Obtunded"
