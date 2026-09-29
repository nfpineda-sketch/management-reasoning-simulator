"""Every word a screen writes can be said in Spanish (faculty, 2026-09-26).

The same guard the documents have: the portals' own literals are collected
from their source, and each must be in the reviewed catalog. Editing an
English sentence breaks this until its Spanish is updated too.
"""
import ast
import re
from pathlib import Path

import pytest

import report_language

ROOT = Path(__file__).resolve().parent
SCREENS = ("resident_portal.py", "management_trace_portal.py", "faculty_portal.py", "rubric_portal.py",
           "progress_portal.py", "image_bank_portal.py", "account_portal.py", "curriculum_runtime.py",
           "faculty_cohort.py", "evidence_views.py", "portfolio.py", "resident_pages.py")


def screen_strings(name):
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    docstrings = {ast.get_docstring(node, clean=False) for node in ast.walk(tree)
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module))}
    raised = {inner.value for node in ast.walk(tree) if isinstance(node, ast.Raise)
              for inner in ast.walk(node) if isinstance(inner, ast.Constant) and isinstance(inner.value, str)}
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if node.value in docstrings or node.value in raised or re.search(r"\\[sdwb]|\.\*|\(\?:|%[YmdHM]", node.value):
            continue
        if re.search(r"\b(margin|display|font-size|width|color)\s*:", node.value):  # a stylesheet, no words
            continue
        words = re.sub(r"<[^>]*>?", "", node.value).strip(" *#")
        if any(words.startswith(name) for name in report_language.KEEP):
            continue
        if len(words) > 12 and " " in words and any(c.isalpha() for c in words):
            found.append(node.value)
    return list(dict.fromkeys(found))


@pytest.mark.parametrize("name", SCREENS)
def test_every_word_the_screen_writes_can_be_said_in_spanish(name):
    # A literal may be said whole, or without the bold or heading marks around it.
    absent = [text for text in screen_strings(name)
              if report_language.missing([text], "es") and report_language.missing([text.strip(" *#")], "es")]
    assert not absent, f"{len(absent)} string(s) in {name} have no Spanish:\n  " + "\n  ".join(map(repr, absent[:40]))


def test_english_is_returned_untouched():
    import screen_language
    assert screen_language.t("Your Management Trace") == "Your Management Trace"


@pytest.mark.parametrize("name", SCREENS)
def test_every_wrapped_phrase_is_in_the_catalog_as_written(name):
    """What a screen asks the catalog for is looked up exactly, so it must be there exactly, with its values."""
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    asked = {node.args[0].value for node in ast.walk(tree)
             if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_t"
             and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)}
    absent = report_language.missing(asked, "es")
    assert not absent, absent
    for text in asked - set(report_language.KEEP):
        assert sorted(re.findall(r"\{[^}]*\}", text)) == sorted(re.findall(r"\{[^}]*\}", report_language.ES[text])), text
