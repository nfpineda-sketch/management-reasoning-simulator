"""The model's prose in the reader's language, translated once and kept (faculty, 2026-09-26).

The English analysis stays the record; a Spanish document asks for the
translation of exactly the model sentences it prints, stores it by the hash of
that English, and reuses it. Nothing here opens a socket: the provider is a
stub, and without a key nothing is translated at all.
"""
from io import BytesIO
import json
import time
import uuid
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

import prose_translation
import report_language
from account_store import AccountStore


def text_of(blob):
    return " ".join(" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages).split())


class Provider:
    """Answers every item with "[es] " + its English, and counts the calls."""

    def __init__(self):
        self.responses = self
        self.calls = []

    def create(self, **kwargs):
        items = json.loads(kwargs["input"])["items"]
        self.calls.append(items)
        return SimpleNamespace(status="completed", output_text=json.dumps(
            {"items": [{"id": item["id"], "text": "[es] " + item["text"]} for item in items]}))


class Recorder:
    """The translate callable a document is handed, recording what it was asked."""

    def __init__(self):
        self.asked = []

    def __call__(self, texts, language="es"):
        self.asked.append(list(texts))
        return {text: "[es] " + text for text in texts}


@pytest.fixture
def accounts(tmp_path):
    return AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)


def test_a_translation_is_paid_for_once_and_reused(accounts):
    store = prose_translation.ProseTranslations(accounts)
    provider = Provider()
    texts = ["The expectation was stated before the trial.", "Oxygenation improved."]
    first = prose_translation.ensure(texts, "es", store=store, client=provider)
    assert first == {text: "[es] " + text for text in texts} and len(provider.calls) == 1
    again = prose_translation.ensure(texts + ["A new sentence."], "es", store=store, client=provider)
    assert again["Oxygenation improved."] == "[es] Oxygenation improved."
    # Only the new sentence was asked for.
    assert [item["text"] for item in provider.calls[-1]] == ["A new sentence."]


def test_english_asks_for_nothing_and_no_key_translates_nothing(accounts):
    store = prose_translation.ProseTranslations(accounts)
    provider = Provider()
    assert prose_translation.ensure(["A sentence."], "en", store=store, client=provider) == {}
    assert prose_translation.ensure(["A sentence."], "es", store=store, api_key="") == {}
    assert provider.calls == []


def test_a_bad_answer_leaves_the_english_rather_than_guessing(accounts):
    class Broken(Provider):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(status="completed", output_text=json.dumps(
                {"items": [{"id": 7, "text": "fuera de rango"}, {"id": 0, "text": "   "}]}))
    assert prose_translation.ensure(["One.", "Two."], "es", client=Broken()) == {}

    class Failing(Provider):
        def create(self, **kwargs):
            raise RuntimeError("provider unavailable; key sk-test-not-real")
    assert prose_translation.ensure(["One."], "es", client=Failing()) == {}


def test_a_stored_translation_answers_only_for_its_own_english(accounts):
    store = prose_translation.ProseTranslations(accounts)
    store.save({"Exactly this.": "Exactamente esto."}, "es", "stub")
    assert store.known(["Exactly this.", "Something else."], "es") == {"Exactly this.": "Exactamente esto."}


def test_the_management_trace_sends_only_the_model_s_sentences():
    from management_trace_report import render_management_trace_pdf
    from test_management_trace_report import report_example
    report, payload = report_example()
    recorder = Recorder()
    english = text_of(render_management_trace_pdf(report, payload, language="en", translate=recorder))
    assert recorder.asked == []  # an English document asks nothing
    spanish = text_of(render_management_trace_pdf(report, payload, language="es", translate=recorder))
    [asked] = recorder.asked
    assert asked and all(text not in report_language.ES for text in asked)
    overview = report["analysis"]["overview"]["text"]
    assert any(overview[:40] in text for text in asked)
    # The resident's own entries are never sent: they are quoted as written.
    entries = [entry.get("learner_input") for entry in payload.get("trace", []) if entry.get("learner_input")]
    assert entries and not any(entry in text for entry in entries for text in asked)
    assert "[es]" in spanish and "[es]" not in english
    assert report_language.t(prose_translation_note(), "es")[:40] in spanish


def prose_translation_note():
    from faculty_report import TRANSLATED_NOTE
    return TRANSLATED_NOTE


def test_the_faculty_brief_sends_only_the_model_s_sentences():
    from faculty_report import render_faculty_brief_pdf
    from test_faculty_report import brief_example
    report, record = brief_example()
    for compact in (True, False):
        recorder = Recorder()
        spanish = text_of(render_faculty_brief_pdf(report, record, compact=compact, language="es",
                                                   translate=recorder))
        [asked] = recorder.asked
        assert asked and all(text not in report_language.ES for text in asked)
        assert any(report["analysis"]["summary"][:30] in text for text in asked)
        assert "[es]" in spanish
    assert "Síntesis del desempeño" in spanish  # the document's own words still come from the catalog


def test_the_rubric_document_sends_the_proposal_s_prose_and_never_the_learner_s_words():
    from rubric_report import render_rubric_report_pdf
    from test_rubric_document import RECORD, proposal
    from test_rubric_reports import review
    recorder = Recorder()
    spanish = text_of(render_rubric_report_pdf(review(), proposal(), RECORD, language="es", translate=recorder))
    [asked] = recorder.asked
    assert any("Why" in text for text in asked)
    assert not any("the learner's own words" in text for text in asked)
    assert "[es]" in spanish
    recorder = Recorder()
    render_rubric_report_pdf(review(), proposal(), RECORD, language="en", translate=recorder)
    assert recorder.asked == []


def test_a_document_without_translations_keeps_the_english_and_says_so():
    from faculty_report import LANGUAGE_NOTE
    from management_trace_report import render_management_trace_pdf
    from test_management_trace_report import report_example
    report, payload = report_example()
    spanish = text_of(render_management_trace_pdf(report, payload, language="es", translate=lambda texts, lang: {}))
    assert report_language.t(LANGUAGE_NOTE, "es")[:40] in spanish
