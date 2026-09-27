"""The Decision Review record is written in the language its encounter was played in (2026-09-26).

"If the encounter is run in Spanish, the PDFs are generated in Spanish." The
fourth PDF, the complete original encounter record with its Markdown, was
still English only. It now follows the encounter's language unless its reader
chooses the other one; the JSON stays the stored record. Its own words come
from the reviewed catalog; the review prompts and the expert comparison are
composed again from the same evidence; the resident's words stay as written,
quoted when a sentence cites them. English is unchanged.
"""
import ast
import re
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

import cognitive_review
import language
import report_language
from test_curriculum_trajectories import load_engine
from test_management_trace_report import report_example

ROOT = Path(__file__).resolve().parent
EXPECTATION = "Oxygenation should improve while I reassess the breathing effort."
#: The record's own English, which a Spanish record must not print.
ENGLISH_CHROME = (
    "Management Reasoning Decision Review", "Patient state", "Management reasoning", "Original learner input",
    "Observed response", "Decision Review", "Expert Comparison", "Adaptation Plan", "Not answered",
    "Key cues", "Expert framing", "One defensible action", "Trade-off to manage", "Your recorded expected effect was",
    "Learner-stated", "Recorded executed actions", "The decision began at", "Review your first management decision",
    "How has your working model changed?", "Where did your reasoning align", "PATIENT STATE", "Page 1",
)


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.fixture
def record(engine):
    """A curriculum encounter's record (case id CE-), reviewed and compared, as the app builds it."""
    _, payload = report_example()
    trace = deepcopy(payload["trace"])
    for event in trace:
        for key in ("state_before", "state_after"):
            event[key]["case_id"] = "CE-review0001"
    prompts = engine["_review_prompt_records"](trace)
    responses = {prompt["review_id"]: {field: f"Mi respuesta sobre {field}." for field, _ in engine["REVIEW_RESPONSE_FIELDS"]}
                 for prompt in prompts}
    plan = {field: f"Mi plan: {field}." for field, _ in engine["ADAPTATION_PLAN_FIELDS"]}
    comparisons = {prompt["review_id"]: {field: f"Mi comparación: {field}." for field, _ in engine["EXPERT_COMPARISON_FIELDS"]}
                   for prompt in prompts}
    return engine["_review_payload"]("respiratory_distress", 14, trace, deepcopy(trace[-1]["state_after"]), prompts,
                                     responses, plan, comparisons, True, 1, {}, None, encounter_language="es")


def pdf_text(blob):
    return " ".join(" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages).split())


def test_the_record_follows_its_encounter_s_language_unless_its_reader_chooses(engine, record):
    assert record["encounter"]["encounter_language"] == "es"
    assert engine["_review_markdown"](record).startswith("# Revisión de decisiones")
    assert engine["_review_markdown"](record, language="en").startswith("# Management Reasoning Decision Review")
    older = deepcopy(record)
    del older["encounter"]["encounter_language"]  # closed before 2026-09-26: the reader's language
    assert engine["_review_markdown"](older).startswith("# Management Reasoning Decision Review")
    with language.presenting("es"):
        assert engine["_review_markdown"](older).startswith("# Revisión de decisiones")


def test_a_spanish_record_says_its_own_words_in_spanish(engine, record):
    markdown = engine["_review_markdown"](record)
    text = pdf_text(engine["_review_pdf"](record))
    for document in (markdown, text):
        left = [phrase for phrase in ENGLISH_CHROME if phrase in document]
        assert not left, left
    assert "Estado del paciente" in markdown and "ESTADO DEL PACIENTE" in text
    assert "Oxígeno 3 L/min por naricera" in markdown  # an order written as the Management Trace writes it
    assert "Página 1" in text


def test_the_resident_s_words_stay_as_written_and_are_quoted_when_cited(engine, record):
    markdown = engine["_review_markdown"](record)
    assert f"Tu efecto esperado registrado fue: «{EXPECTATION}» ¿Qué observaciones" in markdown
    assert f"Efecto esperado declarado por el residente: «{EXPECTATION}»" in markdown
    assert f"- **Efecto esperado:** {EXPECTATION}" in markdown  # the slot itself, unquoted, as in English
    assert "Mi respuesta sobre working_model_update." in markdown and "Mi plan: cue." in markdown
    english = engine["_review_markdown"](record, language="en")
    assert f"Your recorded expected effect was: {EXPECTATION}. Which" in english


def test_the_expert_model_is_composed_again_from_the_same_evidence(engine, record):
    markdown = engine["_review_markdown"](record)
    assert "Acciones ejecutadas registradas: Oxígeno 3 L/min por naricera." in markdown
    assert "La decisión comenzó a los 0 min con PA sistólica 102 mmHg" in markdown
    # Written for this case in English nowhere: nothing to declare.
    assert report_language.t(
        "Some reflection prompts or expert models were written for this case in English and are shown as written.",
        "es") not in markdown


def test_a_prompt_written_in_english_for_its_case_is_shown_as_written_and_said_so(engine, record):
    legacy = deepcopy(record)
    legacy["decision_review"]["prompts"][0]["prompt"] = "Why did the diltiazem not restore perfusion?"
    markdown = engine["_review_markdown"](legacy)
    assert "Why did the diltiazem not restore perfusion?" in markdown
    assert report_language.t(
        "Some reflection prompts or expert models were written for this case in English and are shown as written.",
        "es") in markdown


def test_the_review_says_its_prompts_in_spanish_from_their_own_templates():
    _, payload = report_example()
    for kind, _, _, label, prompt in cognitive_review.reflection_items(payload["trace"]):
        assert cognitive_review.LABELS_ES[label]
        spanish = cognitive_review.prompt_in(prompt, "es")
        assert spanish and "Your recorded" not in spanish and "«" in spanish
    assert cognitive_review.prompt_in("An unknown prompt.", "es") is None
    assert cognitive_review.prompt_in("An unknown prompt.", "en") == "An unknown prompt."


def test_the_english_review_model_is_unchanged_by_the_spanish_one():
    _, payload = report_example()
    event = payload["trace"][0]
    english = cognitive_review.trajectory_review(event, source_decision=1)
    assert english["framing"].startswith("Learner-stated explanation: ")
    assert english["action"].startswith("Recorded executed actions: ")
    spanish = cognitive_review.trajectory_review(event, source_decision=1, language="es")
    assert set(spanish) == set(english) and spanish["source_action_types"] == english["source_action_types"]


RECORD_FUNCTIONS = ("_review_markdown_in", "_review_pdf_in", "_render_export_controls", "render_decision_review")


def record_strings():
    """Every literal the record's own functions can print, minus docstrings and markup."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    found = []
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.name in RECORD_FUNCTIONS):
            continue
        docstring = ast.get_docstring(node, clean=False)
        for inner in ast.walk(node):
            if not (isinstance(inner, ast.Constant) and isinstance(inner.value, str)) or inner.value == docstring:
                continue
            words = re.sub(r"<[^>]*>?", "", inner.value).strip(" #*")
            # The product's and its documents' names are written the same in Spanish (report_language.KEEP).
            if any(words.startswith(name) for name in report_language.KEEP):
                continue
            if len(words) > 12 and " " in words and any(c.isalpha() for c in words):
                found.append(inner.value)
    return list(dict.fromkeys(found))


def test_every_word_the_record_writes_can_be_said_in_spanish():
    strings = record_strings()
    assert len(strings) > 30
    absent = report_language.missing(strings, "es")
    assert not absent, absent
