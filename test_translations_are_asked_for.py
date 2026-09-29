"""TD-41 (faculty, 2026-09-29): opening a page never buys a translation.

Opening or reloading a page, opening an encounter's review, or consulting or generating a
PDF reads the stored translations of the model's prose and nothing more. A document
whose prose is not all stored says so, in its English original, and its reader may ask:
that request alone calls the provider, once, only for what is missing, and what comes
back is kept. A document whose English changed since its translation was asked for is
out of date and is not translated again until asked. Every provider here is a stub.
"""
from pathlib import Path

import pytest

import portfolio
import prose_translation
from test_prose_translation import Provider, accounts  # noqa: F401 (fixture)
from test_resident_pages import program  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
KEYED = lambda name, default="": "sk-a-configured-key" if name == "OPENAI_API_KEY" else default  # noqa: E731


@pytest.fixture
def session(monkeypatch):
    state = {}
    monkeypatch.setattr(prose_translation, "_session", lambda: state)
    return state


@pytest.fixture
def provider(monkeypatch):
    stub = Provider()
    real = prose_translation.translate
    # As the provider does: without a key nothing is asked for; with one, the stub answers.
    monkeypatch.setattr(prose_translation, "translate",
                        lambda texts, language="es", **kwargs: real(texts, language, client=stub)
                        if kwargs.get("api_key") else {})
    return stub


def test_a_page_reads_what_is_stored_and_buys_nothing(accounts, session, provider):  # noqa: F811
    context = {"store": accounts}
    texts = ["The expectation was stated before the trial.", "Oxygenation improved."]
    page = prose_translation.for_page(context, "trace:r1:es", secret=KEYED)
    assert page(texts) == {} and page.status == "english" and provider.calls == []
    prose_translation.ProseTranslations(accounts).save({texts[0]: "[es] " + texts[0]}, "es", "stub")
    page = prose_translation.for_page(context, "trace:r1:es", secret=KEYED)
    assert page(texts) == {texts[0]: "[es] " + texts[0]} and page.status == "partial"
    assert provider.calls == []
    # An English document asks for nothing at all.
    assert prose_translation.for_page(context, "trace:r1:en", secret=KEYED)(texts, "en") == {}


def test_the_reader_s_request_buys_only_what_is_missing_once_and_it_is_kept(accounts, session, provider):  # noqa: F811
    context = {"store": accounts}
    texts = ["The expectation was stated before the trial.", "Oxygenation improved."]
    prose_translation.ProseTranslations(accounts).save({texts[0]: "[es] " + texts[0]}, "es", "stub")
    before = prose_translation.generation("trace:r1:es")
    prose_translation.ask("trace:r1:es", forget=("cached-pdf",))
    assert prose_translation.generation("trace:r1:es") == before + 1
    asked = prose_translation.for_page(context, "trace:r1:es", secret=KEYED)
    assert asked(texts) == {text: "[es] " + text for text in texts} and asked.status == "complete"
    assert [item["text"] for item in provider.calls[-1]] == [texts[1]]
    # The request is spent: the next build reads the store and asks for nothing.
    again = prose_translation.for_page(context, "trace:r1:es", secret=KEYED)
    assert again(texts) == {text: "[es] " + text for text in texts} and again.status == "complete"
    assert len(provider.calls) == 1


def test_an_english_original_that_changed_is_out_of_date_until_asked_again(accounts, session, provider):  # noqa: F811
    context = {"store": accounts}
    first = ["The expectation was stated before the trial.", "Oxygenation improved."]
    prose_translation.ask("brief:b1:full:es")
    prose_translation.for_page(context, "brief:b1:full:es", secret=KEYED)(first)
    changed = [first[0], "Oxygenation improved after the second trial."]
    page = prose_translation.for_page(context, "brief:b1:full:es", secret=KEYED)
    known = page(changed)
    assert page.status == "outdated" and len(provider.calls) == 1
    # What did not change keeps its translation; what changed is shown in English.
    assert known == {first[0]: "[es] " + first[0]}


def test_without_a_key_a_request_can_buy_nothing(accounts, session, provider):  # noqa: F811
    prose_translation.ask("rubric:r1:es")
    page = prose_translation.for_page({"store": accounts}, "rubric:r1:es", secret=lambda name, default="": "")
    assert page(["Oxygenation improved."]) == {} and provider.calls == []


def test_every_page_and_document_uses_the_page_translation_or_the_stored_one():
    """No page builds the paying translator on its own (TD-41)."""
    for path in ROOT.glob("*.py"):
        if path.name.startswith("test_") or path.name == "prose_translation.py":
            continue
        assert "prose_translation.translator(" not in path.read_text(encoding="utf-8"), path.name
    for name in ("management_trace_portal.py", "faculty_portal.py", "portfolio.py"):
        assert "prose_translation.for_page(" in (ROOT / name).read_text(encoding="utf-8"), name


def test_preparing_a_resident_s_documents_in_spanish_buys_nothing(program, session, provider, monkeypatch):  # noqa: F811
    store, _, _, people, reviewed = program
    resident = people["resident-one"]
    monkeypatch.setenv("OPENAI_API_KEY", "sk-never-used-in-this-test")
    context = {"store": store, "token": resident["token"], "user": store.get_user(resident["token"])}
    record = next(row["record"] for row in portfolio.entries(context)[1] if row["record"]["id"] == reviewed)
    page = prose_translation.for_page(context, f"portfolio:{reviewed}:es")
    found = portfolio.documents(context, record, context["user"], language="es", translate=page)
    assert found and provider.calls == []
    assert page.status in {"english", "partial"}
