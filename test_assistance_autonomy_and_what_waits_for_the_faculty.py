"""Assistance, performance and autonomy, kept apart; and what waits for the faculty.

Faculty specification of 2026-09-24, sections 1-10. With the assistance
context at "unknown" -- its default -- the brief's contract forced every
autonomy to be empty, and an empty autonomy could not be recorded, so a batch
declared "independent" to get through. Now:

* "not reported" is a valid state and blocks nothing: the encounter, the AI
  suggestions and every document are saved and generated either way;
* the assistance context is a declaration of its own, with who made it and
  when, completed or corrected later without overwriting anything;
* an autonomy the record cannot establish is left empty -- "not determined:
  requires faculty confirmation" -- and asked for only when that objective is
  confirmed, where the faculty may also record that it could not be determined;
* saving the encounter, the AI analysis, a draft, and a confirmed observation
  are four different things, and only the last one counts;
* a synthetic run is recorded as what it is, and shows no resident's autonomy.

The six situations of section 10 are named in the test names.
"""
import json
import time
import uuid
from copy import deepcopy
from types import SimpleNamespace

import pytest

import encounter_context
from account_store import AccountError, AccountStore
from faculty_analysis import (FacultyAnalysisError, PROMPT_VERSION, build_analysis_source,
                              generate_faculty_brief, source_fingerprint, validate_brief)
from faculty_analysis_store import FacultyBriefStore
from progress_store import AUTONOMY_NOT_DETERMINED, ProgressStore
from test_faculty_analysis import StubClient, sample_analysis


@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty", "faculty", None), ("admin", "admin", None),
                                     ("resident", "resident", 3), ("residente_prueba_r3", "resident", 3),
                                     ("other", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, users


def completed(accounts, token):
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic encounter"})
    accounts.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {
            "review_completed": True,
            "precomparison_decision_review": {"decision-1": {
                "working_model_update": "Septic shock.", "priority_trigger": "Hypotension.",
                "alternative_action": "Earlier vasopressor.", "expected_response_reassessment": "MAP."}},
            "management_trace": [
                {"execution_status": "executed", "learner_input": "Give 500 mL crystalloid.",
                 "decision_time_min": 0, "response_time_min": 10,
                 "reasoning": {"problem_representation": "Septic shock",
                               "slot_provenance": {"problem_representation": "completed"}},
                 "reasoning_gate": {"required": True, "status": "complete", "missing": [],
                                    "sealed_at_min": 0, "asked_for": ["working_model"],
                                    "answered_via": "form"},
                 "state_before": {"observable": {"mental_status": "alert"}},
                 "state_after": {"observable": {"mental_status": "alert"}}},
                {"execution_status": "executed", "learner_input": "Start norepinephrine.",
                 "decision_time_min": 10, "response_time_min": 20,
                 "state_before": {"observable": {"mental_status": "alert"}},
                 "state_after": {"observable": {"mental_status": "alert"}}}],
        },
    }, status="completed")
    return attempt_id


def _suggesting(autonomy, refs=("trace:0",)):
    analysis = sample_analysis()
    row = analysis["objectives"][0]
    row.update(recommendation="satisfactory", depth="integrated", autonomy=autonomy,
               evidence_refs=list(refs))
    return analysis


# --- the declaration --------------------------------------------------------
def test_nobody_declared_anything_is_a_valid_state_not_independence(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    assert store.current(users["faculty"]["token"], attempt_id) == {"assistance": None, "execution": None}
    snapshot = encounter_context.snapshot(store.current(users["faculty"]["token"], attempt_id))
    assert snapshot["assistance"]["value"] == "not_reported"
    assert snapshot["assistance"]["label"] == "Not reported"


def test_the_resident_declares_the_faculty_completes_and_nothing_is_overwritten(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    before = accounts.get_attempt(users["resident"]["token"], attempt_id)
    store.declare(users["resident"]["token"], attempt_id, value="none")
    store.declare(users["faculty"]["token"], attempt_id, value="external_help",
                  description="A colleague suggested the vasopressor.", affected_refs=["trace:1"],
                  note="Told at the debrief.")
    history = store.history(users["faculty"]["token"], attempt_id)
    assert [(row["value"], row["declared_by_role"]) for row in history] == [
        ("none", "resident"), ("external_help", "faculty")]
    current = store.current(users["resident"]["token"], attempt_id)["assistance"]
    assert current["affected_refs"] == ["trace:1"] and current["sequence"] == 2
    # Beside the record, not inside it: no revision, no fingerprint moved, so no
    # saved brief, proposal or confirmed assessment is invalidated.
    after = accounts.get_attempt(users["resident"]["token"], attempt_id)
    assert after["revision"] == before["revision"]
    assert source_fingerprint(after) == source_fingerprint(before)


def test_what_a_declaration_may_and_may_not_say(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    with pytest.raises(AccountError):
        store.declare(users["other"]["token"], attempt_id, value="none")
    with pytest.raises(AccountError, match="only when external help"):
        store.declare(users["resident"]["token"], attempt_id, value="none", description="x")
    with pytest.raises(AccountError, match="not part of this encounter"):
        store.declare(users["resident"]["token"], attempt_id, value="external_help",
                      affected_refs=["trace:9"])
    with pytest.raises(AccountError, match="valid assistance"):
        store.declare(users["resident"]["token"], attempt_id, value="independent")


def test_a_synthetic_run_is_recorded_apart_and_only_by_who_may_say_so(cohort):
    accounts, users = cohort
    store = encounter_context.EncounterContextStore(accounts)
    test_run = completed(accounts, users["residente_prueba_r3"]["token"])
    real = completed(accounts, users["resident"]["token"])
    with pytest.raises(AccountError, match="test account"):
        store.declare(users["resident"]["token"], real, field="execution", value="synthetic_agent",
                      synthetic_accounts={"residente_prueba_r3"})
    store.declare(users["residente_prueba_r3"]["token"], test_run, field="execution",
                  value="synthetic_agent", synthetic_accounts={"residente_prueba_r3"})
    current = store.current(users["faculty"]["token"], test_run)
    assert current["assistance"] is None
    assert encounter_context.label("execution", current["execution"]["value"], "es") == (
        "Prueba sintética: ejecución automatizada sin asistencia externa")
    # A provenance correction by an administrator says why.
    with pytest.raises(AccountError, match="Say why"):
        store.declare(users["admin"]["token"], real, field="execution", value="synthetic_agent")
    store.declare(users["admin"]["token"], real, field="execution", value="synthetic_agent",
                  note="Run by the batch agent under this account.")


# --- section 10, situations 1-3 and 6: the brief -----------------------------
def _brief(record, snapshot, autonomy, refs=("trace:0",)):
    return generate_faculty_brief(record, api_key="k", model="m", context=snapshot,
                                  client=StubClient(_suggesting(autonomy, refs)))


def test_1_not_reported_the_brief_is_generated_and_autonomy_is_left_for_the_faculty(cohort):
    accounts, users = cohort
    record = accounts.get_attempt(users["faculty"]["token"], completed(accounts, users["resident"]["token"]))
    brief = _brief(record, encounter_context.not_reported(), "independent")
    assert brief["prompt_version"] == PROMPT_VERSION
    row = brief["analysis"]["objectives"][0]
    assert row["autonomy"] is None and row["recommendation"] == "satisfactory"
    assert brief["autonomy_withheld"] == [row["objective_id"]]
    assert brief["assistance_snapshot"]["assistance"]["value"] == "not_reported"
    # Saved like any brief; a stored brief with the value the context forbids is refused.
    saved = FacultyBriefStore(accounts).save(users["faculty"]["token"], record["id"], brief)
    assert saved["brief_id"]
    tampered = deepcopy(brief)
    tampered["analysis"]["objectives"][0]["autonomy"] = "independent"
    with pytest.raises(FacultyAnalysisError, match="infer or upgrade"):
        validate_brief(tampered, record)


def test_2_no_external_help_does_not_make_independence_but_allows_a_supported_level(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    store.declare(users["resident"]["token"], attempt_id, value="none")
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    snapshot = encounter_context.snapshot(store.current(users["faculty"]["token"], attempt_id))
    kept = _brief(record, snapshot, "independent")
    assert kept["analysis"]["objectives"][0]["autonomy"] == "independent"
    assert kept["autonomy_withheld"] == []
    empty = _brief(record, snapshot, None)
    assert empty["analysis"]["objectives"][0]["autonomy"] is None


def test_3_declared_help_withholds_independence_where_the_help_reached(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    store.declare(users["resident"]["token"], attempt_id, value="external_help",
                  description="A colleague suggested the vasopressor.", affected_refs=["trace:1"])
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    snapshot = encounter_context.snapshot(store.current(users["faculty"]["token"], attempt_id))
    touched = _brief(record, snapshot, "independent", refs=("trace:0", "trace:1"))
    assert touched["analysis"]["objectives"][0]["autonomy"] is None
    untouched = _brief(record, snapshot, "independent", refs=("trace:0",))
    assert untouched["analysis"]["objectives"][0]["autonomy"] == "independent"
    guided = _brief(record, snapshot, "guided", refs=("trace:1",))
    assert guided["analysis"]["objectives"][0]["autonomy"] == "guided"


def test_6_a_synthetic_run_shows_no_resident_autonomy(cohort):
    accounts, users = cohort
    store = encounter_context.EncounterContextStore(accounts)
    attempt_id = completed(accounts, users["residente_prueba_r3"]["token"])
    store.declare(users["residente_prueba_r3"]["token"], attempt_id, field="execution",
                  value="synthetic_agent", synthetic_accounts={"residente_prueba_r3"})
    store.declare(users["residente_prueba_r3"]["token"], attempt_id, value="none")
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    snapshot = encounter_context.snapshot(store.current(users["faculty"]["token"], attempt_id))
    brief = _brief(record, snapshot, "guided")
    assert brief["analysis"]["objectives"][0]["autonomy"] is None
    assert brief["assistance_snapshot"]["execution"]["value"] == "synthetic_agent"


def test_the_source_says_who_declared_and_what_was_asked_for_never_an_account(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    store = encounter_context.EncounterContextStore(accounts)
    store.declare(users["resident"]["token"], attempt_id, value="none")
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    snapshot = encounter_context.snapshot(store.current(users["faculty"]["token"], attempt_id))
    source = build_analysis_source(record, "unknown", snapshot)
    assert source["assistance_declaration"]["value"] == "none"
    assert source["assistance_declaration"]["declared_by_role"] == "resident"
    assert "assistance_context" not in source
    assert "resident" not in json.dumps(source["assistance_declaration"]).replace('"resident"', "")
    first = source["decision_events"][0]
    # Situation 4: the neutral follow-up is recorded, so what was prompted is visible.
    assert first["reasoning_prompted"] == {"held_for_reasoning": True,
                                           "categories_asked_for": ["working_model"],
                                           "answered_via": "form"}
    assert first["reasoning_provenance"] == {"problem_representation": "completed"}


def test_an_old_autonomy_level_is_no_longer_chosen_before_the_analysis(cohort):
    accounts, users = cohort
    record = accounts.get_attempt(users["faculty"]["token"], completed(accounts, users["resident"]["token"]))
    with pytest.raises(FacultyAnalysisError, match="declared on its own"):
        generate_faculty_brief(record, api_key="k", model="m", assistance_context="independent",
                               client=StubClient())


# --- sections 7 and 8: drafts, confirmation, and what waits -----------------
def test_a_draft_keeps_what_is_pending_and_counts_for_nothing(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    progress = ProgressStore(accounts)
    kept = progress.save_draft(users["faculty"]["token"], attempt_id, "TD1", {
        "satisfactory": True, "depth": "integrated", "evidence_refs": ["trace:0"],
        "notes": "Recognised and supported the hypotension."})
    assert kept["pending"] == ["the autonomy (a level, or that it could not be determined)",
                               "the clinical context"]
    assert progress.latest_draft(users["faculty"]["token"], attempt_id, "TD1")["draft"]["depth"] == "integrated"
    goal = next(g for g in progress.get_progress(users["faculty"]["token"], users["resident"]["id"])["objectives"]
                if g["objective_id"] == "TD1")
    assert goal["count"] == 0 and goal["assessed_count"] == 0
    with pytest.raises(AccountError):
        progress.save_draft(users["resident"]["token"], attempt_id, "TD1", {"depth": "integrated"})


def test_autonomy_is_asked_for_only_at_confirmation_and_can_be_left_undetermined(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    progress = ProgressStore(accounts)
    assessment = {"satisfactory": True, "depth": "integrated", "context": "Septic shock",
                  "evidence_refs": ["trace:0"], "notes": "Recognised and supported the hypotension."}
    with pytest.raises(AccountError, match="could not be determined"):
        progress.assess(users["faculty"]["token"], attempt_id, "TD1", {**assessment, "autonomy": None})
    result = progress.assess(users["faculty"]["token"], attempt_id, "TD1",
                             {**assessment, "autonomy": AUTONOMY_NOT_DETERMINED})
    # Not a negative result and not independence: the component counts on its
    # own merits, as a guided observation would, and says its autonomy is unknown.
    assert result["status"] == "credited"
    goal = next(g for g in progress.get_progress(users["faculty"]["token"], users["resident"]["id"])["objectives"]
                if g["objective_id"] == "TD1")
    assert goal["observations"][0]["autonomy"] == AUTONOMY_NOT_DETERMINED
    # And a second recording of the same objective is not a second observation.
    again = progress.assess(users["faculty"]["token"], attempt_id, "TD1",
                            {**assessment, "autonomy": "guided"})
    assert again["status"] == "duplicate"


def test_the_administrator_finds_what_still_waits(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    progress = ProgressStore(accounts)
    progress.save_draft(users["faculty"]["token"], attempt_id, "TD1", {"depth": "integrated"})
    waiting = {row["attempt_id"]: row for row in progress.pending_reviews(users["admin"]["token"])}
    assert "TD1" in waiting[attempt_id]["pending_objectives"]
    assert waiting[attempt_id]["drafted_objectives"] == ["TD1"]
    with pytest.raises(AccountError):
        progress.pending_reviews(users["resident"]["token"])
    # The staff listing says it beside the encounter: the rubric and the
    # objectives are still the faculty's to decide, and a draft counts for nothing.
    from curriculum_runtime import _awaiting_review
    listed = _awaiting_review({"store": accounts, "token": users["admin"]["token"]})
    assert listed[attempt_id].startswith("rubric · ")
    assert "challenge objective(s), 1 drafted" in listed[attempt_id]
    assert _awaiting_review({"store": accounts, "token": users["resident"]["token"]}) == {}


def test_completing_the_declaration_later_rewrites_no_confirmed_assessment(cohort):
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    progress = ProgressStore(accounts)
    progress.assess(users["faculty"]["token"], attempt_id, "TD1", {
        "satisfactory": True, "depth": "integrated", "autonomy": "prompted", "context": "Septic shock",
        "evidence_refs": ["trace:0"], "notes": "Faculty judgment."})
    before = progress.get_progress(users["faculty"]["token"], users["resident"]["id"])
    encounter_context.EncounterContextStore(accounts).declare(
        users["resident"]["token"], attempt_id, value="external_help", description="A colleague.")
    after = progress.get_progress(users["faculty"]["token"], users["resident"]["id"])
    assert after == before


def test_challenges_and_the_rubric_are_confirmed_independently(cohort):
    """Confirming one never confirms the other (section 8)."""
    import rubric
    from rubric_store import RubricStore
    accounts, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"])
    progress = ProgressStore(accounts)
    reviews = RubricStore(accounts)
    reviews.save_review(users["faculty"]["token"], attempt_id,
                        scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    assert all(goal["assessed_count"] == 0 for goal in
               progress.get_progress(users["faculty"]["token"], users["resident"]["id"])["objectives"])
    other = completed(accounts, users["other"]["token"])
    progress.assess(users["faculty"]["token"], other, "TD1", {
        "satisfactory": True, "depth": "integrated", "autonomy": "prompted", "context": "x",
        "evidence_refs": ["trace:0"], "notes": "Faculty judgment."})
    assert reviews.latest_review(users["faculty"]["token"], other) is None


# --- section 6: every document is generated whatever the context -----------
def test_the_briefs_render_with_nothing_declared_and_say_what_is_undetermined(cohort, monkeypatch):
    from io import BytesIO
    from pypdf import PdfReader
    import language
    from faculty_report import render_faculty_brief_pdf
    accounts, users = cohort
    record = accounts.get_attempt(users["faculty"]["token"], completed(accounts, users["resident"]["token"]))
    brief = _brief(record, encounter_context.not_reported(), None)
    for compact in (True, False):
        text = " ".join(page.extract_text() for page in PdfReader(BytesIO(
            render_faculty_brief_pdf(brief, record, compact=compact))).pages)
        assert "Not reported (nobody has declared it)" in " ".join(text.split())
    monkeypatch.setattr(language, "current", lambda: "es")
    full = " ".join(" ".join(page.extract_text() for page in PdfReader(BytesIO(
        render_faculty_brief_pdf(brief, record, compact=False))).pages).split())
    assert "No informado (nadie lo ha declarado)" in full


# --- section 5: a neutral prompt is recorded as what it was ------------------
from test_the_four_questions_and_where_the_answers_came_from import encounter, engine  # noqa: E402,F401


def test_4_the_categories_asked_for_and_how_they_came_back_are_recorded(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR impairing filling. I expect the rate to fall. "
        "Reassess HR and BP in 5 minutes.")
    gate = resolved["parsed"]["reasoning_gate"]
    assert gate["asked_for"] == ["working_model", "expected_effect", "reassessment_target"]
    assert gate["answered_via"] == "free_text"
    assert len(gate["prompts"]) == 1 and gate["prompts"][0]["minute"] == 0


def test_a_partial_answer_keeps_what_was_asked_and_when_it_was_first_held(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    partial = engine["resolve_pending_reasoning"]("I think this is AF with RVR impairing filling.")
    assert partial.get("missing")
    pending = engine["st"].session_state["pending_reasoning"]
    assert pending["held_at_min"] == 0 and len(pending["asked"]) == 2
    done = engine["complete_pending_reasoning_fields"](
        "AF with RVR impairing filling", "", "the rate to fall", "HR and BP", 5)
    gate = done["parsed"]["reasoning_gate"]
    assert gate["answered_via"] == "form"
    assert gate["asked_for"][0] == "working_model" and "expected_effect" in gate["asked_for"]
