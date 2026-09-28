"""Observation opportunities: declared by the case, frozen with the encounter (DF-1).

The acceptance criteria of the faculty's authorisation of cycle 3 (2026-09-27,
§55). The declarations here are test fixtures, not clinical review: they are
written into a bank case for the length of one test, frozen through the real
path (``evaluation_basis.freeze``) and read back from the record. The bank's own
C14 declarations, approved by the faculty on 2026-09-28, are tested in
test_c14_opportunities.
"""
import time
import uuid

import pytest

import case_assessment_bank
import evaluation_basis
import observation_opportunities as opportunities
from account_store import AccountError, AccountStore
from progress_store import ProgressStore

CASE = "trauma_hemothorax_41m"
FIXTURE_REVIEW = {"by": "test fixture, not a clinical review", "on": "2026-09-27"}
DECLARED = {
    "C14": {"opportunity": "yes", "rationale": "A fixture: an E-FAST finding changes the next step.",
            "observable_component": "Using the POCUS finding to guide management.",
            "expected_evidence": ("requests the POCUS", "acts on the finding"), "reviewed": FIXTURE_REVIEW},
    "C3": {"opportunity": "no", "reason": "A fixture: this case offers no airway decision.",
           "reviewed": FIXTURE_REVIEW},
    "R1-05": {"opportunity": "yes", "rationale": "A fixture: an incidental opportunity.",
              "observable_component": "Revisiting the first explanation.",
              "expected_evidence": ("a later decision revisits it",), "reviewed": FIXTURE_REVIEW},
}


@pytest.fixture
def declared(monkeypatch):
    """The bank case with the fixture's objectives block, for this test only."""
    monkeypatch.setitem(case_assessment_bank.CASES, CASE,
                        {**case_assessment_bank.CASES[CASE], "objectives": DECLARED})
    return DECLARED


def record(challenge_id="R2-03", basis=None):
    return {"id": "fixture", "challenge_id": challenge_id,
            "encounter": {"evaluation_basis": basis} if basis is not None else {},
            "payload": {"session": {}}}


# --- 1 and 2: a case declares, and the three states stay three ------------------------

def test_a_case_declares_an_opportunity_and_the_three_states_stay_apart(declared):
    frozen = evaluation_basis.freeze(CASE)
    view = opportunities.summary(record(basis=frozen))
    assert (view["C14"]["state"], view["C14"]["eligible"], view["C14"]["rule"]) == ("yes", True, "declared")
    assert (view["C3"]["state"], view["C3"]["eligible"], view["C3"]["rule"]) == ("no", False, "declared")
    assert view["C3"]["reason"] == DECLARED["C3"]["reason"]
    # Not declared either way: not reviewed, and never read as "no". (C4 is declared by the
    # observation environment since cycle 7, so C1 is the example here.)
    assert (view["C1"]["state"], view["C1"]["rule"]) == ("not_reviewed", "transition_fallback")
    assert view["C14"]["expected_evidence"] == DECLARED["C14"]["expected_evidence"]
    assert view["C14"]["reviewed"] == FIXTURE_REVIEW


# --- 3: not reviewed is never no, and the transition keeps what was observable ----------

def test_c14_and_c4_are_declared_and_td_f_c_keep_the_transition():
    # Cycle 7 (faculty, 2026-09-28): C14 is reviewed in all 31 cases and C4 is NO in every
    # one (TDFC-7/8, H4); TD1, F1, C1 and C3 are not reviewed anywhere yet.
    for case_id in case_assessment_bank.CASES:
        declared = case_assessment_bank.CASES[case_id].get("objectives") or {}
        assert set(declared) == {"C14", "C4"}, case_id
        view = opportunities.summary(record(basis=evaluation_basis.freeze(case_id)))
        for objective_id in set(opportunities.TRANSITION_OBJECTIVES) - {"C14", "C4"}:
            assert view[objective_id]["state"] == "not_reviewed"
            assert view[objective_id]["eligible"] is True
            assert view[objective_id]["rule"] == "transition_fallback"
        assert view["C14"]["rule"] == "declared", case_id
        assert (view["C4"]["state"], view["C4"]["eligible"], view["C4"]["rule"]) == ("no", False, "declared")


def test_a_basis_frozen_before_opportunities_existed_is_labelled_as_such():
    frozen = evaluation_basis.freeze(CASE)
    frozen["versions"].pop("opportunities")
    # A basis that old never carried a declaration either, and its fingerprint said so.
    frozen["declaration"].pop("objectives", None)
    frozen["fingerprint"] = evaluation_basis.fingerprint(frozen["declaration"])
    view = opportunities.resolve("C14", record(basis=frozen))
    assert view["declaration_source"] == "frozen_before_opportunities"
    assert (view["state"], view["eligible"]) == ("not_reviewed", True)


# --- 4 and 5: frozen when the encounter starts; later changes do not reach it ------------

def test_the_opportunity_is_frozen_when_the_encounter_starts(declared, monkeypatch):
    before = record(basis=evaluation_basis.freeze(CASE))
    changed = {**DECLARED, "C14": {"opportunity": "no", "reason": "A later fixture review.",
                                   "reviewed": FIXTURE_REVIEW}}
    monkeypatch.setitem(case_assessment_bank.CASES, CASE,
                        {**case_assessment_bank.CASES[CASE], "objectives": changed})
    assert opportunities.resolve("C14", before)["state"] == "yes"
    assert opportunities.resolve("C14", record(basis=evaluation_basis.freeze(CASE)))["state"] == "no"


def test_a_record_without_a_frozen_copy_never_takes_the_current_declarations(declared):
    legacy = {"id": "fixture", "challenge_id": "R2-03", "encounter": {},
              "payload": {"session": {"state": {"encounter_spec": {"clinical_case": {"id": CASE}}}}}}
    view = opportunities.resolve("C3", legacy)
    assert view["declaration_source"] == "record_without_frozen_declaration"
    assert (view["state"], view["rule"], view["eligible"]) == ("not_reviewed", "transition_fallback", True)


# --- 10, 11 and 12: several objectives, the target does not limit them, incidental ----

def test_the_target_is_one_source_of_opportunity_and_the_case_can_offer_others(declared):
    view = opportunities.summary(record("R2-03", evaluation_basis.freeze(CASE)))
    assert view["R2-03"]["rule"] == "generation_target" and view["R2-03"]["eligible"]
    # An objective the encounter was not generated for, declared by its case.
    assert view["R1-05"]["rule"] == "declared" and view["R1-05"]["eligible"]
    assert view["R2-02"]["rule"] == "transition_fallback" and not view["R2-02"]["eligible"]
    assert {key for key, item in view.items() if item["eligible"]} >= {"R2-03", "R1-05", "C14", "TD1"}


# --- malformed declarations are defects of the case --------------------------------------

@pytest.mark.parametrize("entry, problem", [
    ({"opportunity": "maybe", "reviewed": FIXTURE_REVIEW}, "must be 'yes' or 'no'"),
    ({"opportunity": "yes", "observable_component": "x", "expected_evidence": ("y",),
      "reviewed": FIXTURE_REVIEW}, "needs its rationale"),
    ({"opportunity": "yes", "rationale": "x", "observable_component": "x", "expected_evidence": (),
      "reviewed": FIXTURE_REVIEW}, "needs its expected_evidence"),
    ({"opportunity": "no", "reviewed": FIXTURE_REVIEW}, "needs its reason"),
    ({"opportunity": "no", "reason": "x"}, "who reviewed it and when"),
])
def test_a_malformed_declaration_is_found_before_any_encounter_uses_it(monkeypatch, entry, problem):
    import case_assessment
    # case_assessment keeps its own copy of the bank's declarations.
    monkeypatch.setitem(case_assessment.CASES, CASE,
                        {**case_assessment.CASES[CASE], "objectives": {"C14": entry}})
    assert any(problem in item for item in case_assessment.verify(CASE))


def test_an_unknown_objective_cannot_be_declared():
    assert opportunities.verify_block(CASE, {"C99": {"opportunity": "yes"}}, {"C14": {}}) == [
        f"{CASE} C99: unknown objective."]


# --- 6 to 9, 13 and 14: through the progress store ---------------------------------------

@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty", "faculty", None), ("resident", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-password-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, ProgressStore(accounts), users


def completed(accounts, token, challenge_id="R2-03", basis=None):
    attempt_id = accounts.create_attempt(token, challenge_id, {"evaluation_basis": basis} if basis else {})
    accounts.save_attempt(token, attempt_id, {"schema_version": "mrs_attempt_v1", "session": {
        "review_completed": True, "management_trace": [{
            "execution_status": "executed", "learner_input": "E-FAST now",
            "reasoning": {"problem_representation": "A fixture working model"}}]}}, status="completed")
    return attempt_id


def assessment(**changes):
    return {"satisfactory": True, "depth": "integrated", "autonomy": "independent",
            "context": "Fixture encounter", "evidence_refs": ["trace:0"],
            "notes": "The faculty read the recorded decision.", **changes}


def progress_of(progress, token, objective_id):
    return next(item for item in progress.get_progress(token)["objectives"] if item["objective_id"] == objective_id)


def test_an_objective_the_case_declares_absent_cannot_be_confirmed(declared, cohort):
    accounts, progress, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"], basis=evaluation_basis.freeze(CASE))
    with pytest.raises(AccountError, match="declares no opportunity"):
        progress.assess(users["faculty"]["token"], attempt_id, "C3", assessment())
    assert progress_of(progress, users["resident"]["token"], "C3")["observations"] == []


def test_an_opportunity_is_not_a_demonstration_and_the_faculty_confirms(declared, cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, basis=evaluation_basis.freeze(CASE))
    # Offered, and nothing is observed until a faculty member assesses it.
    assert progress_of(progress, resident, "C14")["observations"] == []
    assert progress_of(progress, resident, "C14")["count"] == 0
    assert progress.assess(faculty, attempt_id, "C14", assessment(satisfactory=False))["status"] == "recorded"
    unit = progress_of(progress, resident, "C14")["observations"][0]
    assert unit["assessor"] == "faculty" and unit["satisfactory"] is False
    assert unit["provenance"]["opportunity"]["rule"] == "declared"
    assert unit["provenance"]["opportunity"]["basis_fingerprint"]
    assert progress_of(progress, resident, "C14")["count"] == 0


def test_several_objectives_are_observed_in_one_encounter_each_once(declared, cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, basis=evaluation_basis.freeze(CASE))
    for objective_id in ("C14", "TD1", "R2-03", "R1-05"):
        assert progress.assess(faculty, attempt_id, objective_id, assessment())["status"] == "credited"
    rules = {objective_id: progress_of(progress, resident, objective_id)["observations"][0]["provenance"]
             ["opportunity"]["rule"] for objective_id in ("C14", "TD1", "R2-03", "R1-05")}
    assert rules == {"C14": "declared", "TD1": "transition_fallback", "R2-03": "generation_target",
                     "R1-05": "declared"}


def test_an_observation_recorded_before_provenance_existed_reads_as_legacy(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident)
    progress.assess(faculty, attempt_id, "C4", assessment())
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, "UPDATE mrs_progress_observations SET provenance_json = NULL")
    assert progress_of(progress, resident, "C4")["observations"][0]["provenance"] is None


def test_an_older_database_gains_the_provenance_column_without_losing_rows(tmp_path):
    url = f"sqlite:///{tmp_path / 'older.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, """CREATE TABLE mrs_progress_observations (
            id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL, user_id TEXT NOT NULL,
            objective_id TEXT NOT NULL, assessor_id TEXT NOT NULL, satisfactory INTEGER NOT NULL,
            depth TEXT NOT NULL, autonomy TEXT NOT NULL, context TEXT NOT NULL,
            evidence_json TEXT NOT NULL, notes TEXT NOT NULL, source_revision INTEGER NOT NULL,
            payload_sha TEXT NOT NULL, created_at BIGINT NOT NULL,
            voided_at BIGINT, voided_by TEXT, void_reason TEXT)""")
    AccountStore.forget_schemas()
    ProgressStore(accounts)
    with accounts._transaction() as connection:
        columns = {row["name"] for row in accounts._execute(
            connection, "PRAGMA table_info(mrs_progress_observations)").fetchall()}
    assert "provenance_json" in columns


# --- the AI brief is told what the case declared, as guidance ---------------------------

def test_the_brief_gets_a_declared_opportunity_as_guidance_and_nothing_else(declared):
    import faculty_analysis
    frozen = record(basis=evaluation_basis.freeze(CASE))
    row = faculty_analysis._objective_rubric("C14", frozen)
    assert row["observation_opportunity"]["expected_evidence"] == DECLARED["C14"]["expected_evidence"]
    assert "not evidence that it happened" in row["observation_opportunity"]["guidance"]
    assert "observation_opportunity" not in faculty_analysis._objective_rubric("TD1", frozen)
    # An objective the case declares absent is not listed for the brief at all.
    assert "C3" not in faculty_analysis.supported_objectives(frozen)


def test_the_bank_names_only_objectives_that_exist(monkeypatch):
    # The rubric side checks the shape; the objectives' side checks the names.
    assert opportunities.verify_bank() == []
    monkeypatch.setitem(case_assessment_bank.CASES, CASE, {**case_assessment_bank.CASES[CASE], "objectives": {
        "C99": {"opportunity": "no", "reason": "A fixture.", "reviewed": FIXTURE_REVIEW}}})
    assert opportunities.verify_bank() == [f"{CASE} C99: unknown objective."]
