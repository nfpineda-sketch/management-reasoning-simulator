"""The leads a resident asks for, and the effort the patient is actually making.

Faculty decisions 7 and 9 of 2026-09-21. Asking for right-sided or posterior
leads returned an ordinary twelve-lead without a word, so recognising an
inferior infarct with right ventricular involvement earned exactly what missing
it earned. And the proportional work of breathing reached only the pneumonia, so
a thrombolysed pulmonary embolism still reported the word the case was written
with while its rate and saturation moved.
"""
import pytest

import work_of_breathing as effort
from acs_reperfusion import additional_leads
from clinical_cases import FAMILIES
from family_parser import parse_family_actions


def studies(text):
    return [a["diagnostic"] for a in parse_family_actions(text)["actions"] if a.get("type") == "diagnostic"]


# 7 · The additional leads

@pytest.mark.parametrize("text, study", [
    ("Pide un electrocardiograma con derivadas derechas.", "ecg_right"),
    ("Pide derivaciones derechas.", "ecg_right"),
    ("Pide V4R.", "ecg_right"),
    ("Order a right-sided ECG.", "ecg_right"),
    ("Pide derivaciones posteriores V7 V8 V9.", "ecg_posterior"),
    ("Order posterior leads.", "ecg_posterior"),
])
def test_the_additional_leads_are_their_own_study(text, study):
    assert studies(text) == [study]


def test_asking_for_both_returns_both():
    assert studies("Pide un ECG derecho y derivaciones posteriores.") == ["ecg_right", "ecg_posterior"]


def test_a_plain_twelve_lead_is_still_a_plain_twelve_lead():
    assert studies("Pide un electrocardiograma de 12 derivaciones.") == ["ecg"]
    assert studies("Repite el electrocardiograma.") == ["ecg"]


def test_only_a_coronary_case_can_record_them():
    coronary = {v["id"]: v for v in FAMILIES["acs"]["variants"]}["acs_54m_inferior"]
    assert {"ecg_right", "ecg_posterior"} <= set(coronary["investigations"])
    pneumonia = FAMILIES["pneumonia"]["variants"][0]
    assert not {"ecg_right", "ecg_posterior"} & set(pneumonia["investigations"])


def _state(spec, opened=False):
    family = {"elapsed": 10}
    if opened:
        family["artery_open_at"] = 5
    return {"family_state": family,
            "encounter_spec": {"clinical_case": {"engine": {"coronary": spec}}}}


def test_the_finding_follows_the_case_and_not_the_request():
    rv = {"territory": "inferior", "rv_involvement": True}
    anterior = {"territory": "anterior"}
    assert "ST elevation of 1.5 mm in V4R" in additional_leads(_state(rv), "ecg_right")["report"]
    assert "No ST elevation in V3R or V4R" in additional_leads(_state(anterior), "ecg_right")["report"]
    posterior = {"territory": "posterior"}
    assert "ST elevation of 1 mm in V7 to V9" in additional_leads(_state(posterior), "ecg_posterior")["report"]
    assert "No ST elevation in V7" in additional_leads(_state(rv), "ecg_posterior")["report"]


def test_an_opened_artery_resolves_what_the_leads_showed():
    rv = {"territory": "inferior", "rv_involvement": True}
    assert "resolved" in additional_leads(_state(rv, opened=True), "ecg_right")["report"]


def test_the_report_says_it_is_a_textual_substitute():
    rv = {"territory": "inferior", "rv_involvement": True}
    assert "Textual report" in additional_leads(_state(rv), "ecg_right")["report"]


# 9 · The effort

def test_every_family_has_a_coefficient_and_the_pneumonia_keeps_its_own():
    assert effort.LEVELS_PER_UNIT["pneumonia"] == 6.0
    for family in ("pulmonary_embolism", "gi_bleed", "acs", "asthma", "pulmonary_edema"):
        assert effort.LEVELS_PER_UNIT[family] > 0


def test_the_authored_word_stands_only_while_the_patient_has_not_moved():
    assert effort.describe("pulmonary_embolism", "Markedly increased", 1.0) == "Markedly increased"
    assert effort.describe("pulmonary_embolism", "Markedly increased", .85) == "Moderately increased"
    assert effort.describe("pulmonary_embolism", "Markedly increased", 1.3) == "Severe"


def test_exhaustion_is_not_a_lower_rung_of_the_same_ladder():
    f = {"high_load_min": effort.EXHAUSTION_MIN, "respiratory_load": 1.4}
    assert effort.describe("asthma", "Severe", 1.4, f, supported=False) == effort.EXHAUSTED
    assert effort.EXHAUSTED not in effort.LEVELS


def test_a_supported_patient_is_not_tiring_and_the_clock_resets():
    f = {"respiratory_load": 1.5, "high_load_min": 20}
    effort.count_minute(f, supported=True)
    assert f["high_load_min"] == 0
    effort.count_minute(f, supported=False)
    assert f["high_load_min"] == 1


def test_a_load_below_the_threshold_does_not_tire_anyone():
    f = {"respiratory_load": 1.1, "high_load_min": 10}
    effort.count_minute(f, supported=False)
    assert f["high_load_min"] == 0
