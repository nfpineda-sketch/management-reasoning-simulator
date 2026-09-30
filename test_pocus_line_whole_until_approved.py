"""TD-46 (faculty, 2026-09-30): a POCUS line of an unapproved case is whole in English.

Until a faculty member approves a case's Spanish, a line of its POCUS or E-FAST
report that states the case's own findings is shown entirely in English, its
label included, instead of being translated word by word into a line of two
languages. An approved case reads its line entirely in Spanish; the findings
the engine composes are said as before. No translation is requested anywhere.
"""
import pytest

import case_text
import clinical_cases
import family_reports
import language
from pocus_report import format_pocus

CASE = "pulmonary_edema_58m"
LV = "Moderately reduced global contraction"


@pytest.fixture(autouse=True)
def nothing_installed():
    language.set_narrative({})
    language.narrate(None)
    yield
    language.set_narrative({})
    language.narrate(None)


def _pocus(case):
    return clinical_cases.variant_by_id(case)["investigations"]["pocus"]["result"]


def test_the_case_s_own_line_stays_whole_in_english_until_its_case_is_approved():
    with language.narrating(CASE):
        spanish = language.say(format_pocus(_pocus(CASE)), "es")
    lines = spanish.splitlines()
    assert "· LV contractility: " + LV in lines
    assert "· IVC: 2.4 cm; <50% inspiratory collapse" in lines
    # What is not the case's words is still said in Spanish: the headings.
    assert "CORAZÓN" in lines and "VENA CAVA INFERIOR" in lines
    assert not any("reducido" in line or "Contractilidad" in line for line in lines)


def test_an_approved_case_reads_the_whole_line_in_spanish():
    drafted = case_text.passages("es")[CASE]["/investigations/pocus/result/lv"]
    assert drafted["en"] == LV
    language.set_narrative({CASE: {LV: drafted["es"]}})
    with language.narrating(CASE):
        spanish = language.say(format_pocus(_pocus(CASE)), "es")
    assert "· Contractilidad del VI: " + drafted["es"] in spanish.splitlines()
    # The other passages of the case were not approved in this table: whole in English.
    assert "· IVC: 2.4 cm; <50% inspiratory collapse" in spanish.splitlines()


def test_the_findings_the_engine_composes_are_said_as_before():
    engine_value = dict(_pocus(CASE), ivc="1.3 cm; >50% inspiratory collapse")
    with language.narrating(CASE):
        spanish = language.say(format_pocus(engine_value), "es")
    assert "· VCI: 1.3 cm; colapso inspiratorio >50%" in spanish.splitlines()


def test_the_trace_keeps_each_section_whole_in_one_language():
    sections = format_pocus(_pocus(CASE), compact=True).splitlines()[1:]
    with language.narrating(CASE):
        spanish = language.say(" | ".join(sections), "es")
    assert spanish.split(" | ") == sections


def test_the_e_fast_line_is_whole_in_english_too():
    case = "trauma_hemothorax_41m"
    result = dict(clinical_cases.variant_by_id(case)["investigations"]["efast"]["result"], collected_at_min=0)
    english = family_reports.format_result("efast", result)
    with language.narrating(case):
        assert language.say(english, "es") == english


def test_no_bank_case_leaves_a_line_in_two_languages():
    cases = [variant["id"] for family in clinical_cases.FAMILIES.values() for variant in family["variants"]]
    for case in cases:
        words = language._study_words(case)
        with language.narrating(case):
            for study in ("pocus", "efast"):
                result = (clinical_cases.variant_by_id(case)["investigations"].get(study) or {}).get("result")
                if not result:
                    continue
                english = family_reports.format_result(study, dict(result, collected_at_min=4))
                spanish = language.say(english, "es")
                assert "" not in spanish and "" not in spanish
                for line_en, line_es in zip(english.splitlines(), spanish.splitlines()):
                    if line_en.partition(": ")[2] in words:
                        assert line_es == line_en, (case, line_en, line_es)


def test_without_a_case_nothing_is_set_aside():
    body, kept = language._keep_case_findings("· LV contractility: " + LV)
    assert kept == [] and body == "· LV contractility: " + LV
