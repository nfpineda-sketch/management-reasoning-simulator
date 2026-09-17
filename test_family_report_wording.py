"""Investigation reports and medication records read as a clinician writes them.

Seen in a local sepsis encounter: "Chest X-ray: Sample obtained at minute 0",
"Lactate 3.4 mmol/L · Lactate (mmol/L): 3.4", and "azithromycin 291.667 mg".
"""
import pytest

from family_reports import format_administration, format_result


@pytest.mark.parametrize("test_id, verb", [
    ("chest_xray", "Performed"), ("ecg", "Performed"), ("ctpa", "Performed"),
    ("head_ct", "Performed"), ("temperature", "Measured"),
    ("lactate", "Sample obtained"), ("vbg", "Sample obtained"), ("blood_cultures", "Sample obtained"),
])
def test_only_a_specimen_is_a_sample(test_id, verb):
    text = format_result(test_id, {"report": "Reported finding.", "collected_at_min": 0})
    assert text.split(": ", 1)[1].startswith(f"{verb} at minute 0")


def test_a_value_already_in_the_report_is_not_repeated():
    text = format_result("lactate", {"lactate_mmol_l": 3.4, "report": "Lactate 3.4 mmol/L", "collected_at_min": 30})
    assert text == "Lactate: Sample obtained at minute 30 · Lactate 3.4 mmol/L"


def test_a_value_the_report_does_not_state_is_kept():
    text = format_result("troponin", {"value_ng_l": 12, "upper_reference_ng_l": 14,
                                      "report": "Troponin 12 ng/L", "collected_at_min": 0})
    assert text.endswith("Troponin 12 ng/L · Upper reference (ng/L): 14")
    gas = format_result("vbg", {"ph": 7.38, "pco2_mm_hg": 38, "collected_at_min": 0})
    assert gas == "Venous blood gas: Sample obtained at minute 0 · pH: 7.38 · pCO₂ (mmHg): 38"


@pytest.mark.parametrize("amount, text", [(291.666667, "292 mg"), (2000.0, "2000 mg"), (0.4, "0.4 mg"), (1.25, "1.25 mg")])
def test_a_dose_is_shown_without_spurious_decimals(amount, text):
    record = {"agent": "drug", "dose_mg": amount, "route": "IV", "time_min": 0}
    assert format_administration(record) == f"drug {text} IV · minute 0"


def test_a_timed_dose_in_progress_is_rounded_too():
    record = {"agent": "azithromycin", "dose_mg": 291.666667, "route": "IV", "time_min": 0,
              "ordered_dose_mg": 500, "administration_duration_min": 60, "administration_status": "in_progress"}
    assert format_administration(record) == \
        "azithromycin 292 mg IV · minute 0 · over 60 min · 292 of 500 mg given so far"
