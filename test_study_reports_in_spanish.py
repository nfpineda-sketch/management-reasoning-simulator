"""A study report read in Spanish says its own structure in Spanish (faculty, 2026-09-26).

The room's catalog named the studies and when they were taken, and left the
rest of the report's structure in English: the POCUS sections and labels
("HEART", "LV contractility:"), and laboratory fields such as "WBC (K/µL)".
With a case's findings in Spanish once the faculty approves them (case_text),
every line of a POCUS report would have read "LV contractility: Contracción
conservada...". The findings themselves stay as the case says them until
their case is approved; this is only the report's own words.
"""
import pytest

import case_text
import family_reports
import language
import pocus_report
from clinical_cases import FAMILIES

#: Written the same in both languages: abbreviations and names a Spanish report uses too.
SAME_IN_SPANISH = {
    "POCUS", "ECG", "E-FAST", "Cortisol", "pH", "TSH (mIU/L)", "Na (mmol/L)", "K (mmol/L)", "BUN (mg/dL)",
    "FiO₂ (%)", "SaO₂ (%)", "pCO₂ (mmHg)", "PaCO₂ (mmHg)", "PaO₂ (mmHg)", "HCO₃ (mmol/L)", "Cortisol (µg/dL)",
    "Aorta",
}


@pytest.fixture(autouse=True)
def nothing_installed():
    language.set_narrative({})
    language.narrate(None)
    yield
    language.set_narrative({})
    language.narrate(None)


def test_every_study_name_and_field_label_has_its_spanish():
    """Each name and label where a report writes it, since the rules are anchored there."""
    missing = []
    for test_id, label in family_reports.TEST_LABELS.items():
        spanish = language.say(family_reports.format_result(test_id, {"collected_at_min": 1}), "es")
        if label not in SAME_IN_SPANISH and spanish.startswith(label + ":"):
            missing.append(label)
    for key, label in family_reports.FIELDS.items():
        spanish = language.say(family_reports.format_result("basic_labs", {key: 1.5}), "es")
        if label not in SAME_IN_SPANISH and f"{label}:" in spanish:
            missing.append(label)
    assert not missing, missing


def test_a_pocus_report_has_no_english_structure():
    result = {"collected_at_min": 12, **{key: "finding" for key in pocus_report.POCUS_KEYS}}
    for compact in (False, True):
        spanish = language.say(pocus_report.format_pocus(result, compact=compact), "es")
        for section, items in pocus_report.SECTIONS:
            if section.upper() not in {name.upper() for name in SAME_IN_SPANISH}:
                assert section.upper() not in spanish
            for _key, label in items:
                assert f"{label}:" not in spanish, (label, compact)
        assert "performed at minute" not in spanish and "realizada en el minuto 12" in spanish
    assert "No documentado" in language.say(pocus_report.format_pocus({}), "es")


def test_imaging_is_performed_and_only_a_specimen_is_sampled_in_both_languages():
    for test_id in ("renal_ultrasound", "efast", "pelvis_xray"):
        english = family_reports.format_result(test_id, {"report": "A finding.", "collected_at_min": 3})
        assert "Performed at minute 3" in english
        assert "Realizado en el minuto 3" in language.say(english, "es")


def test_an_approved_case_reads_its_reports_wholly_in_spanish():
    """Every report of every bank case, as if all were approved: no English label is left."""
    tables = {variant: {row["en"]: row["es"] for path, row in rows.items() if path != "/history_source"}
              for variant, rows in case_text.passages().items()}
    language.set_narrative(tables)
    labels = [label for label in list(family_reports.FIELDS.values())
              if label not in SAME_IN_SPANISH]
    labels += [label for _, items in pocus_report.SECTIONS for _, label in items]
    left = set()
    for spec in FAMILIES.values():
        for variant in spec["variants"]:
            for key, investigation in (variant.get("investigations") or {}).items():
                result = dict((investigation or {}).get("result") or {})
                if not result:
                    continue
                result.setdefault("collected_at_min", 12)
                english = family_reports.format_result(key, result)
                with language.narrating(variant["id"]):
                    spanish = language.say(english, "es")
                left.update(f"{key}: {label}" for label in labels if f"{label}:" in spanish)
    assert not left, sorted(left)
