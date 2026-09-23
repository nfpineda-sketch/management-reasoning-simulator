"""The documents follow the language the reader chose, and stay that way.

Faculty decision of 2026-09-23. English is the default and its path is
untouched. What is translated is the document's **own** words -- section
titles, labels, captions, notices. Three things are deliberately not:

  * the resident's own words, quoted verbatim in whichever language they wrote;
  * the model's prose, generated in English by contract, which is why a Spanish
    document says on the page that the reasoning is in English;
  * the clinical identifiers -- doses, units, drug names, times, event ids --
    so that a change of language cannot alter physiology, timing or assessment.

The test that matters here is the last one. A table of translations keyed on
English sentences rots the moment somebody edits an English sentence, and the
rot is silent: the Spanish document quietly prints an English line. So this
walks the renderers, collects every string they can put on a page, and fails
when the table cannot say one of them.
"""
import ast
from pathlib import Path

import pytest

import report_language


ROOT = Path(__file__).resolve().parent
RENDERERS = ("management_trace_report.py", "faculty_report.py")


def visible_strings(name):
    """Every literal these renderers can print, minus their own docstrings."""
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            raw = ast.get_docstring(node, clean=False)
            if raw:
                docstrings.add(raw)
    # What a raise carries is for a developer reading a traceback, not for a
    # reader of the document. Translating it would put Spanish in a log.
    raised = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    raised.add(inner.value)
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if node.value in docstrings or node.value in raised:
            continue
        text = node.value.strip()
        # A string of pure markup has no words to translate, and a regular
        # expression is not prose. What is measured is the visible text left
        # once the tags are gone.
        import re as _re
        if _re.search(r"\\[sdwb]|\.\*|\(\?:", node.value):
            continue
        words = _re.sub(r"<[^>]*>?", "", text).strip()
        if len(words) > 12 and " " in words and any(c.isalpha() for c in words) \
                and not text.startswith("%"):
            found.append(text)
    return list(dict.fromkeys(found))


@pytest.mark.parametrize("name", RENDERERS)
def test_every_word_the_document_writes_can_be_said_in_spanish(name):
    absent = report_language.missing(visible_strings(name), "es")
    assert not absent, (
        f"{len(absent)} string(s) in {name} have no Spanish. A reader who chose "
        "Spanish would get these lines in English without being told.\n  "
        + "\n  ".join(repr(text) for text in absent[:12]))


def test_english_is_returned_untouched():
    for name in RENDERERS:
        for text in visible_strings(name):
            assert report_language.t(text) is text
            assert report_language.t(text, "en") is text


def test_a_string_the_table_does_not_know_passes_through():
    # The model's prose and the resident's quoted words are exactly this case.
    for language in ("en", "es"):
        assert report_language.t("Le doy aspirina 300 mg vo", language) \
            == "Le doy aspirina 300 mg vo"
        assert report_language.t("The learner named the pattern at minute 0.", language) \
            == "The learner named the pattern at minute 0."


def test_nothing_empty_or_missing_breaks_it():
    for value in ("", None, 0, False):
        assert report_language.t(value, "es") == value


def test_an_unknown_language_falls_back_to_the_source():
    assert report_language.t("Decisions worth revisiting", "fr") == "Decisions worth revisiting"


def test_the_table_translates_rather_than_repeating():
    """A Spanish entry equal to its English key is a placeholder, not a translation."""
    same = [key for key, value in report_language.ES.items() if key == value]
    assert not same, f"{len(same)} entries are still their English source: {same[:5]}"


def test_what_is_kept_untranslated_is_declared_and_small():
    """Only names, and few. A growing KEEP is a table going quietly English."""
    assert len(report_language.KEEP) <= 8
    for text in report_language.KEEP:
        assert text not in report_language.ES


def test_every_entry_is_a_string_pair():
    for key, value in report_language.ES.items():
        assert isinstance(key, str) and isinstance(value, str) and value.strip()


def composed_prose(name):
    """f-strings that put words on the page around a value.

    A table keyed on whole strings cannot translate one of these: the string
    that reaches the renderer is assembled at run time and matches no key. The
    fix is to make the whole sentence the key --
    ``t("{n} selected review priorities").format(n=...)`` -- so the Spanish can
    put the number where Spanish puts it.

    This lists the ones still to convert, so that a half-translated document
    cannot pass for a translated one.
    """
    import re
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    found = []
    pieces = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            pieces.append([p.value for p in node.values
                           if isinstance(p, ast.Constant) and isinstance(p.value, str)])
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # "a literal " + value is the same failure as an f-string, and it
            # is the one that slipped through first: eight strings were in the
            # table and still printed in English (2026-09-23).
            sides = [node.left, node.right]
            literals = [side.value for side in sides
                        if isinstance(side, ast.Constant) and isinstance(side.value, str)]
            if literals and len(literals) < len(sides):
                pieces.append(literals)
    for parts in pieces:
        prose = "".join(parts)
        # Two or more words of prose around a value, and not a path, a style
        # name or a font file.
        prose = re.sub(r"<[^>]*>?", "", prose)
        if len(re.findall(r"[A-Za-z]{3,}", prose)) < 2:
            continue
        if any(token in prose for token in (".ttf", "Faculty", "Trace", "://", "%")):
            continue
        found.append(prose.strip())
    return sorted(dict.fromkeys(found))


CONVERTED = {
    # Whole-sentence templates already in the table, with the value named.
    "{id} · revision {n} · Faculty judgment required",
    "DECISION {n} · CONTINUED",
    "Learner report · AI interpretation · Renderer {v}",
}


@pytest.mark.parametrize("name", RENDERERS)
def test_the_sentences_built_around_a_value_are_listed(name):
    """Not yet whole-sentence templates. Recorded so the gap is visible.

    Every one of these prints an English word in a Spanish document. They are
    counted rather than ignored, and the count is what should fall.
    """
    remaining = [text for text in composed_prose(name) if text not in CONVERTED]
    assert len(remaining) <= LEFT_TO_CONVERT[name], (
        f"{name} grew a new sentence built around a value: "
        f"{len(remaining)} > {LEFT_TO_CONVERT[name]}")


# The count today, so that it can only fall. Each one prints an English word
# in a Spanish document; they are listed by ``composed_prose`` and converting
# one means making its whole sentence the key.
# Zero, and it stays zero: every sentence built around a value is now a whole
# template whose Spanish can put the value where Spanish puts it.
LEFT_TO_CONVERT = {"management_trace_report.py": 0, "faculty_report.py": 0}


def placeholders(text):
    """The named values a template expects, ignoring any format spec."""
    import string
    return {name.split("!")[0].split(":")[0]
            for _, name, _, _ in string.Formatter().parse(text) if name}


def test_a_translation_keeps_every_value_its_sentence_needs():
    """A dropped or misspelled placeholder is a crash, not a typo.

    These are ``.format()`` templates: the renderer passes the values by name.
    A Spanish sentence that loses one raises KeyError while a document is being
    built, which is a failure in front of a reader rather than in a test.
    """
    wrong = []
    for english, spanish in report_language.ES.items():
        if placeholders(english) != placeholders(spanish):
            wrong.append((english[:60], sorted(placeholders(english)),
                          sorted(placeholders(spanish))))
    assert not wrong, wrong


def test_every_template_can_actually_be_formatted():
    """Formatting each one with its own names, in both languages."""
    for english, spanish in report_language.ES.items():
        names = placeholders(english)
        if not names:
            continue
        # A numeric format spec needs a number; everything else takes a string.
        values = {name: 1 for name in names}
        for text in (english, spanish):
            try:
                text.format(**values)
            except (KeyError, IndexError, ValueError) as error:
                raise AssertionError(f"{text[:70]!r} cannot be formatted: {error}") from None


# --- the documents themselves ----------------------------------------------

def rendered(language):
    """The three documents as text, in one language."""
    import io
    import os
    from unittest import mock
    from pypdf import PdfReader

    def text_of(blob):
        return " ".join(" ".join(page.extract_text() or ""
                                 for page in PdfReader(io.BytesIO(blob)).pages).split())

    with mock.patch.dict(os.environ, {"MRS_LANGUAGE": language}):
        from faculty_report import render_faculty_brief_pdf
        from management_trace_report import render_management_trace_pdf
        from test_faculty_report import brief_example
        from test_management_trace_report import report_example
        report, record = brief_example()
        trace_report, payload = report_example()
        return {
            "compact": text_of(render_faculty_brief_pdf(report, record, compact=True)),
            "full": text_of(render_faculty_brief_pdf(report, record, compact=False)),
            "trace": text_of(render_management_trace_pdf(trace_report, payload,
                                                         case_label="c", learner_label="l")),
        }


# The curriculum's own objective titles stay in English: they carry official
# competency wording, and translating them would change what the programme
# says rather than how a document labels a section. The Spanish pages say so.
CURRICULUM_ENGLISH = ("Recognize instability",)


def test_no_document_word_stays_english_when_the_reader_chose_spanish():
    """The test that would have caught the misses.

    A table can be complete and the page still English: a sentence assembled
    from pieces never matches a key. Eight strings were in the table and still
    printed in English until this rendered the documents and looked.
    """
    for name, text in rendered("es").items():
        leaks = [source for source in report_language.ES
                 if "{" not in source and len(source) > 20 and source in text
                 and not source.startswith(CURRICULUM_ENGLISH)]
        assert not leaks, f"{name}: {leaks[:5]}"


def test_the_english_documents_are_unchanged_by_any_of_this():
    english = rendered("en")
    for name, text in english.items():
        assert text, name
    # The words the English documents are built from are still in them.
    assert "Decisions worth revisiting" in english["trace"]
    assert "Performance synthesis" in english["full"]


def test_the_spanish_documents_say_what_is_still_in_english():
    from faculty_report import LANGUAGE_NOTE
    spanish = rendered("es")
    said = report_language.t(LANGUAGE_NOTE, "es")[:40]
    assert said in spanish["full"] and said in spanish["trace"]
    for text in rendered("en").values():
        assert LANGUAGE_NOTE not in text
