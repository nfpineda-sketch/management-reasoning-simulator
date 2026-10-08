"""The bank cases' narrative in Spanish, shown only once the faculty approved it (2026-09-26).

Nothing is shown in Spanish on a draft; an approval is a faculty member's,
recorded under their account, for the exact words they read, and speaks for
that case only, even where another case says the same sentence; a later edit
to either language takes the case back to pending; and a sentence is replaced
whole or not at all, so no line mixes the two languages.

The pilot candidate also carries the faculty's approvals of the 30 pilot cases
(``case_text/es/approvals.json``, B-5, 2026-10-08; ``test_case_text_approvals``).
The tests of what a review in the app does run without that file (``no_pack``),
so that they still show a case before and after its approval.
"""
import json
import time
import uuid

import pytest

import case_text
import language
import tools_case_text
from account_store import AccountError, AccountStore

VARIANT = "anaphylaxis_63m_betablocked"
ANSWER = "His wife lists atenolol and apixaban, taken every morning; he took both today."


@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty", "faculty", None), ("resident", "resident", 1)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = accounts._new_session(connection, user_id)
    return accounts, users


@pytest.fixture
def no_pack(monkeypatch):
    """The app as it is with no approvals carried in the repository: only the reviews in its database."""
    monkeypatch.setattr(case_text, "pack_approvals", lambda language="es": [])


@pytest.fixture(autouse=True)
def nothing_installed():
    language.set_narrative({})
    language.narrate(None)
    case_text._INSTALLED.clear()
    yield
    language.set_narrative({})
    language.narrate(None)
    case_text._INSTALLED.clear()


def test_every_drafted_passage_translates_what_its_case_says_today():
    """If a case's English changes, run tools_case_text.py extract and redo the passages it marks."""
    assert tools_case_text.problems() == []
    drafts = case_text.passages()
    assert len(drafts) == 31


@pytest.mark.usefixtures("no_pack")
def test_nothing_is_spanish_until_a_faculty_member_approves_it(cohort):
    accounts, _ = cohort
    case_text.install(accounts, now=0)
    assert language.narrative(ANSWER, "es", case=VARIANT) == ANSWER


@pytest.mark.usefixtures("no_pack")
def test_an_approval_is_the_faculty_member_s_and_names_what_they_read(cohort):
    accounts, users = cohort
    reviews = case_text.CaseTextReviews(accounts)
    with pytest.raises(AccountError):
        reviews.record(users["resident"], VARIANT, "approved")
    with pytest.raises(AccountError):
        reviews.record(users["faculty"], VARIANT, "changes_requested", "")  # say what should change
    reviews.record(users["faculty"], VARIANT, "approved", "Revisado.")
    latest = reviews.latest()[VARIANT]
    assert latest["reviewer"] == "faculty" and latest["decision"] == "approved"
    assert latest["version"] == case_text.version(case_text.passages()[VARIANT])
    case_text.install(accounts, now=0)
    spanish = language.narrative(ANSWER, "es", case=VARIANT)
    assert spanish != ANSWER and "atenolol" in spanish
    assert language.narrative(ANSWER, "en", case=VARIANT) == ANSWER
    # Another case, not approved, stays in English, whole -- even the sentences
    # it shares word for word with the approved one.
    other = case_text.passages()["asthma_24f"]
    shared = "Compressible bilaterally"
    assert any(row["en"] == shared for row in other.values())
    assert language.narrative(shared, "es", case=VARIANT) != shared
    assert language.narrative(shared, "es", case="asthma_24f") == shared
    assert language.narrative(other["/presentation"]["en"], "es", case="asthma_24f") == other["/presentation"]["en"]
    # Without a case named, nothing is replaced.
    assert language.narrative(ANSWER, "es") == ANSWER


def test_an_edit_after_the_approval_takes_the_case_back_to_pending(cohort):
    accounts, users = cohort
    reviews = case_text.CaseTextReviews(accounts)
    reviews.record(users["faculty"], VARIANT, "approved")
    rows = json.loads(json.dumps(case_text.passages()[VARIANT]))
    assert case_text.status(VARIANT, rows, reviews.latest(), []) == "approved"
    rows["/presentation"]["es"] += " (editado)"
    assert case_text.status(VARIANT, rows, reviews.latest(), []) == "outdated"


@pytest.mark.usefixtures("no_pack")
def test_the_room_s_arrival_line_is_whole_in_one_language(cohort):
    """The presentation event wraps the case's history source in fixed words (arrival_brief)."""
    import arrival_brief
    from clinical_cases import FAMILIES
    accounts, users = cohort
    variant = next(item for spec in FAMILIES.values() for item in spec["variants"] if item["id"] == VARIANT)
    text = variant["presentation"] + arrival_brief.handover({"encounter_spec": {"clinical_case": variant}})
    assert "History from: " in text
    case_text.install(accounts, now=0)
    assert language.narrative(text, "es", case=VARIANT) == text  # not approved: English, whole
    case_text.CaseTextReviews(accounts).record(users["faculty"], VARIANT, "approved")
    case_text.install(accounts, now=0)
    spanish = language.narrative(text, "es", case=VARIANT)
    assert "Fuente de la historia: Esposa." in spanish and "History from" not in spanish
    assert case_text.passages()[VARIANT]["/presentation"]["es"] in spanish
    # The conversation panel names the same source in its own frame; the bare
    # word is never matched alone.
    assert language.narrative("History source: Wife", "es", case=VARIANT) == "Fuente de la historia: Esposa"
    assert language.narrative("Wife", "es", case=VARIANT) == "Wife"


def test_a_passage_whose_english_changed_is_not_used_even_in_an_approved_case():
    rows = json.loads(json.dumps(case_text.passages()[VARIANT]))
    english = case_text.current_english()
    rows["/presentation"]["en"] = "A different presentation the case no longer says."
    usable = case_text.usable_rows(VARIANT, rows, english)
    assert "/presentation" not in usable and len(usable) == len(rows) - 1


def test_a_sentence_is_replaced_whole_or_not_at_all():
    language.set_narrative({VARIANT: {ANSWER: "Su esposa enumera atenolol y apixabán.", "Son": "Hijo"}})
    mixed = ANSWER + " An unapproved sentence stays as it is."
    assert language.narrative(mixed, "es", case=VARIANT) == (
        "Su esposa enumera atenolol y apixabán. An unapproved sentence stays as it is.")
    # Never inside a longer word.
    assert language.narrative("Sonographic windows. Son", "es", case=VARIANT) == "Sonographic windows. Hijo"


def test_the_room_reads_the_approved_narrative_of_its_own_case():
    language.set_narrative({VARIANT: {ANSWER: "Su esposa enumera atenolol y apixabán."}})
    language.narrate("asthma_24f")
    assert language.say(ANSWER, "es") == ANSWER
    language.narrate(VARIANT)
    assert language.say(ANSWER, "es") == "Su esposa enumera atenolol y apixabán."
    # A document names its own encounter's case, whatever the room shows.
    with language.narrating("asthma_24f"):
        assert language.say(ANSWER, "es") == ANSWER
    assert language.say(ANSWER, "es") == "Su esposa enumera atenolol y apixabán."


def test_approvals_carried_from_another_deployment_count_for_the_same_words(tmp_path, monkeypatch):
    version = case_text.version(case_text.passages()[VARIANT])
    folder = tmp_path / "es"
    folder.mkdir()
    for path in case_text._files("es"):
        (folder / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (folder / "approvals.json").write_text(json.dumps([
        {"variant_id": VARIANT, "version": version, "decision": "approved", "reviewer": "faculty"}]))
    monkeypatch.setattr(case_text, "ROOT", tmp_path)
    case_text._LOADED.clear()
    tables = case_text.approved_table({}, case_text.pack_approvals())
    assert list(tables) == [VARIANT] and ANSWER in tables[VARIANT]


def test_the_documents_use_the_approved_narrative_in_spanish_only():
    from io import BytesIO
    from pypdf import PdfReader
    from management_trace_analysis import source_fingerprint
    from management_trace_report import render_management_trace_pdf
    from management_trace_store import analysis_payload_from_session
    from test_history_is_part_of_the_record import asked
    from test_management_trace_report import report_example
    report, fixture = report_example()
    payload = analysis_payload_from_session({
        "encounter_ended": True, "expert_comparison_unlocked": True,
        "encounter_closed_trace": fixture["trace"],
        "precomparison_decision_review": fixture["reflections"],
        "review_prompts": fixture["reflection_prompts"],
        "encounter_closed_events": list(asked("¿Qué medicamentos toma?", ANSWER)),
        "encounter_closed_state": {"encounter_spec": {"clinical_case": {"id": VARIANT}}},
    })
    report["source_hash"] = source_fingerprint(payload)

    def text_of(blob):
        return " ".join(" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages).split())
    translation = "Su esposa enumera atenolol y apixabán; hoy tomó ambos."
    language.set_narrative({VARIANT: {ANSWER: translation}})
    language.narrate("asthma_24f")  # the room around the document shows another case
    spanish = text_of(render_management_trace_pdf(report, payload, language="es"))
    english = text_of(render_management_trace_pdf(report, payload, language="en"))
    assert "Su esposa enumera atenolol" in spanish and ANSWER not in spanish
    assert "His wife lists atenolol" in english and "Su esposa" not in english
    # Approved for another case only: this encounter's document keeps its English.
    language.set_narrative({"asthma_24f": {ANSWER: translation}})
    assert "Su esposa" not in text_of(render_management_trace_pdf(report, payload, language="es"))


REVIEW_PAGE = """
import streamlit as st
from account_store import AccountStore
from case_text_portal import render_case_text_review
store = AccountStore(st.session_state['url'], allow_sqlite=True)
token = st.session_state['token']
render_case_text_review({'store': store, 'token': token, 'user': store.get_user(token)})
"""


@pytest.mark.usefixtures("no_pack")
def test_the_review_page_records_the_approval_of_whoever_signs_it(cohort):
    from streamlit.testing.v1 import AppTest
    accounts, users = cohort
    app = AppTest.from_string(REVIEW_PAGE, default_timeout=30)
    app.session_state["url"] = accounts._url
    app.session_state["token"] = users["faculty"]
    app.run()
    assert not app.exception
    next(item for item in app.selectbox if item.label.startswith("Case to review")).set_value(VARIANT).run()
    next(item for item in app.button if item.label.startswith("Approve this case")).click().run()
    assert not app.exception
    assert case_text.CaseTextReviews(accounts).latest()[VARIANT]["reviewer"] == "faculty"
    # A resident is shown nothing of it.
    resident = AppTest.from_string(REVIEW_PAGE, default_timeout=30)
    resident.session_state["url"] = accounts._url
    resident.session_state["token"] = users["resident"]
    resident.run()
    assert not resident.exception and not resident.selectbox and not resident.button
