"""The resident's pages, the evidence views and the portfolio (cycle 9, §154Q–§154AL). Synthetic accounts only.

A resident reads their own record, read-only, in several kinds of evidence and
never one score: the assigned case is announced and not described; each
observation leads back to its encounter and Management Trace; the portfolio
holds only finalized documents and is built without a paid call. Faculty read
the same views of a resident they open, and no one reaches another resident's
documents by naming them.
"""
import io
import json
import re
import zipfile

import pytest

import evidence_views
import portfolio
import prose_translation
import rubric
from account_store import AccountError, AccountStore, hash_password
from conftest import onboarded
from encounter_directives import DirectiveStore
from management_trace_store import ManagementTraceStore
from progress_store import ProgressStore
from rubric_store import RubricStore
from test_curriculum_app import authored_replay_fixture, open_app
from test_management_trace_analysis import sample_report
from test_management_trace_store import session_payload

CASE = "acs_48m_wellens"
REASON = "Does she stop to look for the second explanation"
RANKING = r"\b(?:ranked|rank\s*#?\d|top\s+\d|best|worst|percentile|leaderboard)\b|overall score:|% complete"


def _completed(store, token, challenge="R1-03"):
    payload = session_payload()
    payload["session"]["encounter"] = {"authored_case_id": CASE}
    attempt_id = store.create_attempt(token, challenge, {"presentation": "Synthetic chest pain encounter"})
    store.save_attempt(token, attempt_id, payload, status="completed")
    return attempt_id


def _observe(store, faculty, attempt_id, objective_id, satisfactory=True):
    ProgressStore(store).assess(faculty, attempt_id, objective_id, {
        "satisfactory": satisfactory, "depth": "integrated", "autonomy": "independent",
        "context": "Chest pain with dynamic ECG changes", "evidence_refs": ["trace:0"],
        "notes": "Synthetic feedback on " + objective_id})


@pytest.fixture
def program(tmp_path, monkeypatch):
    authored_replay_fixture(monkeypatch)
    url = "sqlite:///" + str(tmp_path / "accounts.sqlite3")
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("teacher", hash_password("local-test-password"))
    admin = store.authenticate("teacher", "local-test-password")
    people = {}
    for name, year in (("resident-one", 2), ("resident-two", 1)):
        token = store.register(name, "local-resident-password", store.create_invite(admin, "resident", year))
        onboarded(store, token)
        people[name] = {"token": token, "id": store.get_user(token)["id"]}
    faculty = store.register("faculty-one", "local-faculty-password", store.create_invite(admin, "faculty"))
    token = people["resident-one"]["token"]
    reviewed = _completed(store, token)
    ManagementTraceStore(store).save(token, reviewed, sample_report())
    _observe(store, faculty, reviewed, "TD1")
    _observe(store, faculty, reviewed, "R1-03")
    RubricStore(store).save_review(faculty, reviewed, scores={d: 2 for d in rubric.DOMAIN_IDS},
                                   status="confirmed", events=[{
                                       "event_id": "acs_provocation_test", "status": "confirmed",
                                       "justification": "Synthetic: a stress test was ordered."}])
    return store, admin, faculty, people, reviewed


def text_of(at):
    parts = []
    for kind in ("title", "header", "subheader", "markdown", "caption", "info", "success", "warning", "error"):
        parts += [str(getattr(item, "value", "")) for item in getattr(at, kind)]
    parts += [str(item.label) for item in at.expander]
    return " ".join(parts)


def navigate(at, view):
    next(widget for widget in at.sidebar.radio if widget.label == "Navigation").set_value(view).run()
    assert not at.exception


def show(at, key, value):
    next(widget for widget in at.radio if widget.key == key).set_value(value).run()
    assert not at.exception


# --- the assigned case: announced, never described (§154E, §154R) -----------------------------------

def test_the_home_says_a_case_is_assigned_and_nothing_about_it(program):
    store, admin, _, people, _ = program
    resident = people["resident-one"]
    DirectiveStore(store).direct(admin, resident["id"], "R2-05", "gi_bleed_72f", REASON)
    assert set(DirectiveStore(store).assigned(resident["token"])) == {"assigned_at"}
    # Nobody else's assignment is read through it.
    assert DirectiveStore(store).assigned(people["resident-two"]["token"]) is None
    at = open_app(resident["token"])
    text = text_of(at)
    assert any(item.value == "Assigned to me" for item in at.subheader)
    assert "New clinical encounter · assigned " in text
    for hidden in ("R2-05", "gi_bleed_72f", REASON, "teacher", "directive", "chosen", "directed"):
        assert hidden not in text, hidden
    assert any(button.label == "Begin Encounter" for button in at.button)


def test_without_an_assignment_the_home_is_as_before(program):
    at = open_app(program[3]["resident-two"]["token"])
    assert any(item.value == "Your next clinical encounter" for item in at.subheader)
    assert not any(item.value == "Assigned to me" for item in at.subheader)


# --- my progress: several kinds of evidence, read-only (§154S–§154AA, §154AF) ------------------------

def test_my_progress_keeps_each_kind_of_evidence_apart(program):
    at = open_app(program[3]["resident-one"]["token"])
    navigate(at, "My progress")
    assert any(item.value == "My progress" for item in at.subheader)
    # The objective record stays the first table, as before.
    assert "Objective" in at.dataframe[0].value.columns
    assert "Areas with limited evidence" in text_of(at)
    show(at, "_my_progress_view", "Management reasoning")
    assert "Your profile is based on faculty-confirmed observations" in text_of(at)
    show(at, "_my_progress_view", "Decision challenges")
    text = text_of(at)
    assert "R1-03 · Relate tachycardia" in text and "1 faculty-confirmed observation(s) (1 satisfactory)" in text
    show(at, "_my_progress_view", "Royal College EPAs")
    text = text_of(at)
    assert "TD1 · Recognize instability" in text and "Local observation target: 10" in text
    assert "What remains outside this simulator" in text
    show(at, "_my_progress_view", "ACGME Milestones")
    table = at.dataframe[0].value
    pc4 = table[table["Code"] == "PC4"].iloc[0]
    assert (pc4["Direct"], pc4["Partial"]) == (1, 0)
    assert "No Milestone level is assigned or inferred" in text_of(at)
    show(at, "_my_progress_view", "Safety")
    assert "acs_provocation_test" in text_of(at)
    for view in ("Overview", "Management reasoning", "Decision challenges", "Royal College EPAs",
                 "ACGME Milestones", "Safety"):
        show(at, "_my_progress_view", view)
        assert not re.search(RANKING, text_of(at).lower()), view
        # Read-only: no control that records, confirms or edits evidence.
        assert not any(b.label in {"Record objective assessment", "Save program target", "Save review",
                                   "Confirm simulated-component achievement"} for b in at.button)


def test_an_observation_leads_to_its_encounter_and_its_management_trace(program):
    store, _, _, people, reviewed = program
    at = open_app(people["resident-one"]["token"])
    navigate(at, "My progress")
    show(at, "_my_progress_view", "Decision challenges")
    next(b for b in at.button if b.label == "Open this encounter and its Management Trace").click().run()
    assert not at.exception
    assert at.session_state["_resident_dashboard_view"] == "My encounters"
    assert at.session_state["_my_encounter"] == reviewed
    text = text_of(at)
    # The Trace comes first, the score after it (§154AC).
    assert text.index("1 · Management Trace") < text.index("3 · Management reasoning rubric")
    assert "Synthetic feedback on R1-03" in text
    next(b for b in at.button if b.label == "Prepare the documents").click().run()
    assert not at.exception
    # The Trace and the confirmed rubric, the same documents faculty download.
    assert len(at.get("download_button")) == 2
    # In the other language when the reader chooses it, as before (faculty, 2026-09-26).
    choice = next(widget for widget in at.radio if widget.key == "_portfolio_language_mine_" + reviewed)
    choice.set_value("es").run()
    assert not at.exception
    next(b for b in at.button if b.label == "Prepare the documents").click().run()
    assert not at.exception and len(at.get("download_button")) == 2


def test_encounters_of_the_same_case_and_minute_still_read_apart(program):
    # Found on the first visual review: three encounters read alike, and a request for one
    # encounter's documents landed on another between reruns.
    store, _, faculty, people, reviewed = program
    token = people["resident-one"]["token"]
    twin = _completed(store, token)
    RubricStore(store).save_review(faculty, twin, scores={d: 1 for d in rubric.DOMAIN_IDS}, status="confirmed")
    records = [store.get_attempt(token, reviewed), store.get_attempt(token, twin)]
    for record in records:
        record["created_at"] = 1_790_000_000
    labels = evidence_views.encounter_labels(records)
    assert len(set(labels.values())) == 2 and all(label.endswith(("#1", "#2")) for label in labels.values())
    at = open_app(token)
    navigate(at, "My encounters")
    selector = next(widget for widget in at.selectbox if widget.key == "_my_encounter")
    assert len(set(selector.options)) == len(selector.options) == 2
    selector.set_value(twin).run()
    next(b for b in at.button if b.label == "Prepare the documents").click().run()
    assert not at.exception
    assert at.session_state["_my_encounter"] == twin
    # The twin has a confirmed rubric and no saved reading: exactly its one document.
    assert len(at.get("download_button")) == 1


def test_my_encounters_does_not_name_a_target_before_review(program):
    store, _, _, people, _ = program
    _completed(store, people["resident-one"]["token"], challenge="R2-05")
    at = open_app(people["resident-one"]["token"])
    navigate(at, "My encounters")
    table = at.dataframe[0].value
    assert sorted(table["Faculty review"]) == ["Awaiting faculty review", "Reviewed"]
    assert "R2-05" not in text_of(at) and "R2-05" not in table.to_string()


# --- the views compute nothing new (§154X, §154Z, §154AF) --------------------------------------------

def _goal(objective_id, observations, **definition):
    import objectives
    return {**objectives.OBJECTIVES[objective_id], "objective_id": objective_id, "observations": observations,
            **definition}


def _observation(identifier, attempt, contributions=None, voided=False, satisfactory=True):
    return {"id": identifier, "attempt_id": attempt, "satisfactory": satisfactory, "voided": voided,
            "created_at": 1_790_000_000, "context": "Shock", "notes": "",
            "provenance": {"contributions": contributions} if contributions is not None else None}


def test_one_observation_counts_once_under_a_code_however_many_links_lead_there():
    # R2-01 links Royal College ME 1.6 twice; the observation is one contribution there.
    links = [{"framework": "Royal College", "code": "ME 1.6", "contribution": "direct"}] * 2
    rows = evidence_views.framework_rows([_goal("R2-01", [_observation("o1", "a1", links)])], "Royal College")
    me16 = next(row for row in rows if row["code"] == "ME 1.6")
    assert (len(me16["observations"]), me16["direct"], me16["partial"], me16["not_recorded"]) == (1, 1, 0, 0)


def test_a_voided_or_legacy_observation_is_never_given_a_contribution():
    goals = [_goal("R1-03", [_observation("o1", "a1"), _observation("o2", "a2", voided=True)])]
    pc4 = next(row for row in evidence_views.framework_rows(goals, "ACGME") if row["code"] == "PC4")
    assert (len(pc4["observations"]), pc4["direct"], pc4["not_recorded"]) == (1, 0, 1)


def test_limited_evidence_is_about_how_much_was_observed():
    goals = [_goal("C14", [_observation(f"o{i}", f"a{i}") for i in range(3)]),
             _goal("C1", [_observation(f"p{i}", f"b{i}") for i in range(5)]), _goal("F1", [])]
    rows, not_yet = evidence_views.limited_rows(goals, {"domains": {"D5": {"encounters": 4}}})
    assert [row["n"] for row in rows] == [3, 4] and rows[0]["area"].startswith("C14 ·")
    assert not_yet == ["F1"]


def test_only_confirmed_safety_events_are_listed():
    reviews = [{"attempt_id": "a1", "encounter_at": 1, "created_at": 2, "reviewer": "f", "critical_events": [
        {"event_id": "e1", "status": "confirmed", "action": "Stress test ordered"},
        {"event_id": "e2", "status": "dismissed"}, {"event_id": "e3", "status": "proposed"}]}]
    assert [row["event_id"] for row in evidence_views.safety_rows(reviews)] == ["e1"]


# --- the portfolio (§154AG–§154AL, §154DN, §154DO, §154EG) --------------------------------------------

def test_the_complete_portfolio_holds_the_final_documents_and_says_what_they_are(program, monkeypatch):
    store, _, _, people, reviewed = program
    resident = people["resident-one"]
    _completed(store, resident["token"], challenge="R2-05")   # neither a Trace nor a confirmed rubric
    asked = []
    monkeypatch.setattr(prose_translation, "translate",
                        lambda texts, language="es", **kwargs: asked.append(kwargs.get("api_key")) or {})
    monkeypatch.setattr(portfolio, "_language", lambda record: "es")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-never-used-in-this-test")
    context = {"store": store, "token": resident["token"], "user": store.get_user(resident["token"])}
    data, manifest = portfolio.complete_zip(context)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert sorted(name.split("/")[0] for name in names) == ["Management_Traces", "README.txt", "Rubrics",
                                                            "manifest.json"]
    assert all(reviewed[:12] in name for name in names if "/" in name)
    rubric_entry = next(item for item in manifest if item["document"] == "rubric_assessment")
    assert rubric_entry["faculty_reviewer"] == "faculty-one" and rubric_entry["review_revision"] == 1
    assert rubric_entry["resident"] == "resident-one" and len(rubric_entry["sha256"]) == 64
    stored = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("manifest.json"))
    assert stored["documents"] == manifest
    # Built from what is saved: the provider key never reaches a translation call.
    assert all(key == "" for key in asked)


def test_a_document_that_cannot_be_rebuilt_is_named_and_the_rest_still_comes(program, monkeypatch):
    store, _, _, people, reviewed = program
    resident = people["resident-one"]
    import resident_portal

    def unreadable(*args, **kwargs):
        raise AccountError("The saved analysis needs to be generated again.")
    monkeypatch.setattr(resident_portal, "_trace_pdf", unreadable)
    context = {"store": store, "token": resident["token"], "user": store.get_user(resident["token"])}
    data, manifest = portfolio.complete_zip(context)
    stored = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("manifest.json"))
    [lost] = stored["not_included"]
    assert (lost["document"], lost["encounter_id"]) == ("management_trace", reviewed)
    assert lost["reason"] == "The saved analysis needs to be generated again."
    # The confirmed rubric of the same encounter still comes.
    assert [item["document"] for item in manifest] == ["rubric_assessment"]


def test_a_draft_rubric_is_never_part_of_the_portfolio(program):
    store, _, faculty, people, _ = program
    resident = people["resident-one"]
    draft = _completed(store, resident["token"], challenge="R2-05")
    RubricStore(store).save_review(faculty, draft, scores={d: 3 for d in rubric.DOMAIN_IDS}, status="draft")
    context = {"store": store, "token": resident["token"], "user": store.get_user(resident["token"])}
    _, manifest = portfolio.complete_zip(context)
    assert draft not in {item["encounter_id"] for item in manifest}


def test_nobody_reaches_another_resident_s_portfolio_by_naming_them(program):
    store, _, faculty, people, reviewed = program
    other = people["resident-two"]
    context = {"store": store, "token": other["token"], "user": store.get_user(other["token"])}
    with pytest.raises(AccountError):
        portfolio.complete_zip(context, people["resident-one"]["id"])
    owner, rows = portfolio.entries(context)
    assert owner["username"] == "resident-two" and rows == []
    # Faculty reach it, and the documents are the resident's own.
    staff = {"store": store, "token": faculty, "user": store.get_user(faculty)}
    _, manifest = portfolio.complete_zip(staff, people["resident-one"]["id"])
    assert {item["resident"] for item in manifest} == {"resident-one"}
    assert {item["encounter_id"] for item in manifest} == {reviewed}


# --- faculty and admin read the same views (§154K, §154AL, §154AQ) -------------------------------------

def test_faculty_open_the_same_evidence_and_portfolio_from_a_card(program):
    store, _, faculty, people, _ = program
    at = open_app(faculty)
    next(b for b in at.button if b.key == "_cohort_open_" + people["resident-one"]["id"]).click().run()
    assert not at.exception
    assert "Faculty-confirmed objective observations: 2" in text_of(at)
    assert any(item.label == "Evidence by framework and portfolio" for item in at.expander)
    show(at, "_cohort_evidence_view", "ACGME Milestones")
    assert "No Milestone level is assigned or inferred" in text_of(at)
    show(at, "_cohort_evidence_view", "Portfolio")
    assert any(b.label == "Prepare the complete portfolio" for b in at.button)
    assert not re.search(RANKING, text_of(at).lower())


def test_the_administrator_tells_active_from_inactive_accounts(program):
    store, admin, _, people, _ = program
    store.update_user(admin, people["resident-two"]["id"], active=False)
    at = open_app(admin)
    tables = [element.value for element in at.sidebar.dataframe]
    accounts = next(table for table in tables if "Status" in table.columns)
    status = dict(zip(accounts["Account"], accounts["Status"]))
    assert (status["resident-two"], status["resident-one"]) == ("Inactive", "Active")
