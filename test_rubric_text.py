"""The rubric descriptors in Spanish, shown only once the faculty approved them (2026-09-27).

The descriptors are the rubric's criteria, so their Spanish is a draft until a
faculty member approves it, domain by domain: nothing reads in Spanish on a
draft; an approval is a faculty member's, recorded under their account, for
the exact words they read; a later edit to either language, or to the rubric's
English, takes the domain back to English; and the scores and the AI proposal
keep the English criteria whatever is approved.
"""
import json
import re
import time
import uuid

import pytest

import rubric
import rubric_text
from account_store import AccountError, AccountStore
from rubric_analysis import build_rubric_source
from test_rubric_analysis import record_on_case


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


@pytest.fixture(autouse=True)
def nothing_installed():
    rubric_text._INSTALLED.clear()
    rubric_text._APPROVED.clear()
    yield
    rubric_text._INSTALLED.clear()
    rubric_text._APPROVED.clear()


def spanish_on_screen(accounts, domain):
    rubric_text._INSTALLED.clear()
    rubric_text.install(accounts, now=0)
    return rubric_text.descriptors(domain, "es")


def test_the_draft_translates_every_descriptor_the_rubric_has_today():
    drafts = rubric_text.drafts()
    assert set(drafts) == set(rubric.DOMAIN_IDS)
    for domain, rows in drafts.items():
        assert rubric_text.current(domain, rows), domain
        for key, row in rows.items():
            assert row["es"] != row["en"] and not re.search(r"\b(the|and|or|with)\b", row["es"]), (domain, key)
    file = json.loads((rubric_text.ROOT / "es" / "descriptors.json").read_text(encoding="utf-8"))
    assert file["rubric_version"] == rubric.VERSION


def test_nothing_is_spanish_until_a_faculty_member_approves_it(cohort):
    accounts, _ = cohort
    for domain in rubric.DOMAIN_IDS:
        shown = spanish_on_screen(accounts, domain)
        assert shown["language"] == "en"
        assert shown["asks"] == rubric.DOMAINS[domain]["asks"]
        assert shown["levels"] == rubric.DOMAINS[domain]["levels"]


def test_an_approval_is_the_faculty_member_s_names_what_they_read_and_speaks_for_its_domain(cohort):
    accounts, users = cohort
    reviews = rubric_text.RubricTextReviews(accounts)
    with pytest.raises(AccountError):
        reviews.record(users["resident"], "D1", "approved")
    with pytest.raises(AccountError):
        reviews.record(users["faculty"], "D1", "changes_requested", "")  # say what should change
    reviews.record(users["faculty"], "D1", "approved", "Revisado.")
    latest = reviews.latest()["D1"]
    assert latest["reviewer"] == "faculty" and latest["decision"] == "approved"
    assert latest["version"] == rubric_text.version("D1", rubric_text.drafts()["D1"])
    shown = spanish_on_screen(accounts, "D1")
    assert shown["language"] == "es"
    assert shown["asks"] == rubric_text.drafts()["D1"]["asks"]["es"]
    assert shown["levels"][0].startswith("Pasa por alto una amenaza observable")
    assert set(shown["levels"]) == set(rubric.LEVELS)
    # English readers, and every other domain, are untouched.
    assert rubric_text.descriptors("D1", "en")["asks"] == rubric.DOMAINS["D1"]["asks"]
    assert spanish_on_screen(accounts, "D2")["language"] == "en"


def test_a_request_for_changes_keeps_the_domain_in_english(cohort):
    accounts, users = cohort
    reviews = rubric_text.RubricTextReviews(accounts)
    reviews.record(users["faculty"], "D4", "approved", "")
    reviews.record(users["faculty"], "D4", "changes_requested", "«Metas» se confunde con las metas del programa.")
    assert rubric_text.status("D4", rubric_text.drafts()["D4"], reviews.latest()) == "changes_requested"
    assert spanish_on_screen(accounts, "D4")["language"] == "en"


def test_an_edit_to_the_spanish_after_the_approval_takes_the_domain_back_to_english(cohort, monkeypatch):
    accounts, users = cohort
    rubric_text.RubricTextReviews(accounts).record(users["faculty"], "D3", "approved", "")
    assert spanish_on_screen(accounts, "D3")["language"] == "es"
    edited = json.loads(json.dumps(rubric_text.drafts()))
    edited["D3"]["levels/2"]["es"] = "Prescribe un manejo apropiado, suficientemente especificado y seguro."
    monkeypatch.setattr(rubric_text, "drafts", lambda language="es": edited)
    latest = rubric_text.RubricTextReviews(accounts).latest()
    assert rubric_text.status("D3", edited["D3"], latest) == "outdated"
    assert spanish_on_screen(accounts, "D3")["language"] == "en"


def test_a_change_to_the_rubric_s_english_takes_the_domain_back_to_english(cohort, monkeypatch):
    accounts, users = cohort
    reviews = rubric_text.RubricTextReviews(accounts)
    reviews.record(users["faculty"], "D5", "approved", "")
    changed = json.loads(json.dumps(rubric.DOMAINS["D5"]["levels"]))
    changed = {int(level): text for level, text in changed.items()}
    changed[1] = "Recognises the course but adjusts late."
    monkeypatch.setitem(rubric.DOMAINS["D5"], "levels", changed)
    shown = spanish_on_screen(accounts, "D5")
    assert shown["language"] == "en" and shown["levels"][1] == "Recognises the course but adjusts late."
    with pytest.raises(AccountError, match="English changed"):
        reviews.record(users["faculty"], "D5", "approved", "")


def test_the_criteria_the_scores_and_the_ai_use_stay_english_whatever_is_approved(cohort):
    accounts, users = cohort
    reviews = rubric_text.RubricTextReviews(accounts)
    before = build_rubric_source(record_on_case())["rubric"]
    for domain in rubric.DOMAIN_IDS:
        reviews.record(users["faculty"], domain, "approved", "")
    assert all(spanish_on_screen(accounts, domain)["language"] == "es" for domain in rubric.DOMAIN_IDS)
    after = build_rubric_source(record_on_case())["rubric"]
    assert after == before
    assert [row["asks"] for row in after] == [rubric.DOMAINS[domain]["asks"] for domain in rubric.DOMAIN_IDS]


def test_approvals_carried_from_another_deployment_name_the_words_they_approved(monkeypatch):
    rows = rubric_text.drafts()["D2"]
    carried = [{"domain_id": "D2", "version": rubric_text.version("D2", rows), "decision": "approved",
                "reviewer": "faculty elsewhere"}]
    monkeypatch.setattr(rubric_text, "pack_approvals", lambda language="es": carried)
    assert rubric_text.status("D2", rows, {}, carried) == "approved"
    rubric_text.install(None, now=0)
    assert rubric_text.descriptors("D2", "es")["language"] == "es"
    assert rubric_text.descriptors("D1", "es")["language"] == "en"


def test_no_approval_is_carried_by_default():
    assert rubric_text.pack_approvals() == []



@pytest.fixture
def screen_cohort(tmp_path):
    """Accounts shaped as the rubric screen's tests use them (test_rubric_portal.page)."""
    accounts = AccountStore(f"sqlite:///{tmp_path / 'screen.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty", "faculty", None), ("resident", "resident", 1)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, None, users


def test_the_rubric_screen_reads_an_approved_domain_in_spanish_and_the_others_in_english(screen_cohort):
    from test_rubric_portal import attempt_on_case, page
    accounts, _, users = screen_cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])

    def captions(language):
        rubric_text._INSTALLED.clear()
        app = page(screen_cohort, attempt_id, language=language)
        return " ".join(str(item.value) for item in app.caption)

    before = captions("es")
    assert rubric.DOMAINS["D1"]["asks"] in before
    # D4 and D5 are told apart for the faculty, in the language on screen (2026-09-27).
    assert ("D4 evalúa monitorización y reevaluación; D5 evalúa cómo se utiliza esa información para adaptar "
            "o mantener justificadamente el manejo y asegurar su continuidad.") in before
    assert "Los descriptores que un docente aún no aprueba en español se muestran en inglés." in before
    rubric_text.RubricTextReviews(accounts).record(users["faculty"]["token"], "D1", "approved", "")
    after = captions("es")
    assert rubric_text.drafts()["D1"]["asks"]["es"] in after and rubric.DOMAINS["D1"]["asks"] not in after
    assert rubric.DOMAINS["D2"]["asks"] in after
    english = captions("en")
    assert rubric.DOMAINS["D1"]["asks"] in english and "se muestran en inglés" not in english
    assert "D4 assesses monitoring and reassessment; D5 assesses how that information is used" in english


REVIEW_APP = """
import streamlit as st
from account_store import AccountStore
from rubric_text_portal import render_rubric_text_review
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
render_rubric_text_review({'store': store, 'token': token, 'user': store.get_user(token)})
"""


def test_the_review_panel_records_the_faculty_member_s_decision_and_shows_nothing_to_a_resident(screen_cohort):
    from streamlit.testing.v1 import AppTest
    accounts, _, users = screen_cohort

    def panel(actor):
        app = AppTest.from_string(REVIEW_APP, default_timeout=20)
        app.session_state["database_url"] = accounts._url
        app.session_state["test_token"] = users[actor]["token"]
        app.run()
        assert not app.exception
        return app

    assert not panel("resident").expander
    app = panel("faculty")
    assert "**0** approved" in " ".join(item.value for item in app.markdown)
    notices = " ".join(str(item.value) for item in app.caption)
    assert "no implica validación del instrumento ni equivalencia demostrada entre idiomas" in notices
    shown = " ".join(item.value for item in app.markdown)
    assert rubric_text.drafts()["D1"]["levels/3"]["es"] in shown and rubric.DOMAINS["D1"]["levels"][3] in shown
    next(button for button in app.button if button.label.startswith("Approve")).click().run()
    assert not app.exception
    latest = rubric_text.RubricTextReviews(accounts).latest()
    assert latest["D1"]["decision"] == "approved" and latest["D1"]["reviewer"] == "faculty"
    assert set(latest) == {"D1"}


def test_the_review_document_shows_the_words_on_file():
    """docs/TRADUCCION_RUBRICA.md is what a reviewer reads away from the app: it must be the draft on file."""
    document = (rubric_text.ROOT.parent / "docs" / "TRADUCCION_RUBRICA.md").read_text(encoding="utf-8")
    for domain, rows in rubric_text.drafts().items():
        for key, row in rows.items():
            assert f"| {row['en']} | {row['es']} |" in document, (domain, key)


def test_the_faculty_review_of_2026_09_27_is_applied_word_for_word():
    drafts = rubric_text.drafts()
    expected = {
        ("D1", "levels/1"): "o requiere orientación correctiva importante.",
        ("D1", "levels/3"): "prepara planes de contingencia",
        ("D3", "levels/2"): "Indica un manejo apropiado",
        ("D4", "levels/3"): "establece objetivos clínicos y umbrales de alarma",
        ("D4", "levels/3", "signs"): "busca activamente signos de fracaso terapéutico o complicaciones",
        ("D5", "levels/3"): "un traspaso de la atención o un seguimiento que explicite los asuntos pendientes",
    }
    for (domain, key, *_), words in expected.items():
        assert words in drafts[domain][key]["es"], (domain, key)
    spanish = " ".join(row["es"] for rows in drafts.values() for row in rows.values())
    for gone in ("indicación correctiva", "Ordena un manejo", "prepara contingencias", "fija metas",
                 "la falla del tratamiento", "pendientes explícitos"):
        assert gone not in spanish, gone


def test_indicacion_is_kept_for_clinical_orders_and_orientacion_is_the_help_a_resident_receives():
    import report_language
    prompts = {key: said for key, said in report_language.ES.items() if "prompt" in key.lower()}
    assert prompts and not [key for key, said in prompts.items() if re.search(r"indicaci[oó]n", said, re.I)]
    assert report_language.ES["Prompted"] == "Con orientación"
    assert not re.search(r"\bindicaci[oó]n", " ".join(row["es"] for rows in rubric_text.drafts().values()
                                                     for row in rows.values()), re.I)
    # The clinical sense stays: orders, an indication for a drug, advice to the patient.
    assert "indicaciones" in report_language.ES[next(key for key in report_language.ES
                                                     if key.startswith("You may enter your reasoning and orders"))]
