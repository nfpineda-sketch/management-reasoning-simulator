"""R1-03, R1-04 and R2-01 as observational objectives (DF-2, 2026-09-27).

What the faculty's authorisation of cycle 3 asks of them (§58, §59, §61):
each link says whether it is a direct or a partial contribution, the component
observed, what stays outside it, and its source, version and page; no link is
a score or a weight; an encounter generated for a challenge is an opportunity
and never evidence by itself; and one confirmed observation is one evidence
unit, however many links it contributes through.
"""
import time
import uuid

import pytest

from account_store import AccountError, AccountStore
from competency_mapping import CHALLENGE_MAPPINGS, CONTRIBUTION_TYPES, SOURCES, mapping_for_challenge
from objectives import OBJECTIVES
from progress_store import ProgressStore

FOUNDATION = ("R1-03", "R1-04", "R2-01")


@pytest.mark.parametrize("objective_id", FOUNDATION)
def test_each_link_states_its_contribution_component_limit_and_source(objective_id):
    objective = OBJECTIVES[objective_id]
    assert objective["supported"] and objective["target"] == 3
    assert objective["assessment_scope"] == "simulated_reasoning_component"
    assert "Not an ACGME or Royal College requirement" in objective["target_source"]
    links = objective["competency_mapping"]
    assert {link["framework"] for link in links} == {"ACGME", "Royal College"}
    for link in links:
        assert link["contribution"] in CONTRIBUTION_TYPES
        assert link["component_observed"].strip() and link["element"].strip()
        if link["contribution"] == "partial":
            assert link["limitation"] and link["limitation"].strip()
        else:
            assert link["limitation"] is None
        source = SOURCES[link["source_id"]]
        assert link["source_version"] == source["version"] and link["pdf_page"] > 0
        if link["framework"] == "ACGME":
            assert link["source_id"] == "acgme_em_2021" and link["level_described"] in range(1, 6)
            assert link["source_url"] == source["url"] + f"#page={link['pdf_page']}"
        else:
            # Pathway to Competence names the stage milestone; its public
            # address was not verified, so no link is invented.
            assert link["source_id"] == "rc_em_pathway_2018" and link["source_url"] is None
            assert link["stage"] in {"Foundations of Discipline", "Core of Discipline"}
            if link["epa_context"]:
                assert link["epa_context"]["source_id"] == "rc_em_epa_2018"
                assert "not a contribution to the whole EPA" in link["epa_context"]["note"]


def test_the_contributions_are_those_the_verification_supports():
    kinds = {key: [(link["code"], link["contribution"]) for link in OBJECTIVES[key]["competency_mapping"]]
             for key in FOUNDATION}
    assert kinds == {
        "R1-03": [("PC4", "direct"), ("MK2", "partial"), ("ME 2.2", "partial")],
        "R1-04": [("PC1", "direct"), ("PC6", "partial"), ("ME 4.1", "partial")],
        "R2-01": [("PC1", "direct"), ("PC4", "direct"), ("MK1", "partial"), ("MK2", "partial"),
                  ("ME 1.6", "direct"), ("ME 1.6", "direct")],
    }
    # MK1 is the faculty's example of a partial contribution: knowledge applied,
    # not the whole of scientific knowledge.
    mk1 = next(link for link in OBJECTIVES["R2-01"]["competency_mapping"] if link["code"] == "MK1")
    assert "application" in mk1["limitation"]
    # R1-04's milestone is listed under F2, whose context these encounters
    # contradict, so no EPA is attributed to it.
    me41 = next(link for link in OBJECTIVES["R1-04"]["competency_mapping"] if link["code"] == "ME 4.1")
    assert me41["epa_context"] is None and "F2" in me41["limitation"]


@pytest.mark.parametrize("objective_id", FOUNDATION)
def test_direct_and_partial_are_labels_never_weights(objective_id):
    for link in OBJECTIVES[objective_id]["competency_mapping"]:
        assert isinstance(link["contribution"], str)
        assert not {"weight", "score", "value", "percentage", "confidence"} & set(link)
        assert not any(isinstance(value, float) for value in link.values())


def test_the_eight_decision_challenges_keep_their_links_as_they_were():
    for challenge_id, definition in CHALLENGE_MAPPINGS.items():
        if challenge_id in FOUNDATION:
            continue
        assert "contributions" not in definition
        assert all("contribution" not in link for link in mapping_for_challenge(challenge_id)["competency_mapping"])


# --- through the progress store -------------------------------------------------------

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


def completed(accounts, token, challenge_id):
    attempt_id = accounts.create_attempt(token, challenge_id, {})
    accounts.save_attempt(token, attempt_id, {"schema_version": "mrs_attempt_v1", "session": {
        "review_completed": True, "management_trace": [{
            "execution_status": "executed", "learner_input": "Diltiazem 10 mg IV, reassess HR and BP in 10 minutes",
            "reasoning": {"problem_representation": "Rapid AF contributing to poor perfusion",
                          "expected_effect": "slower rate and better perfusion"}}]}}, status="completed")
    return attempt_id


def assessment(**changes):
    return {"satisfactory": True, "depth": "integrated", "autonomy": "prompted",
            "context": "Fixture encounter", "evidence_refs": ["trace:0"],
            "notes": "The faculty read the recorded decision.", **changes}


def progress_of(progress, token, objective_id):
    return next(item for item in progress.get_progress(token)["objectives"] if item["objective_id"] == objective_id)


@pytest.mark.parametrize("objective_id", FOUNDATION)
def test_an_encounter_generated_for_a_challenge_is_an_opportunity_not_evidence(cohort, objective_id):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, objective_id)
    before = progress_of(progress, resident, objective_id)
    assert before["observations"] == [] and before["count"] == 0 and before["status"] == "not_observed"
    # Only the faculty's assessment of the recorded performance observes it.
    assert progress.assess(faculty, attempt_id, objective_id, assessment())["status"] == "credited"
    after = progress_of(progress, resident, objective_id)
    assert after["count"] == 1 and not after["confirmed"]


def test_one_observation_is_one_evidence_unit_with_its_contributions(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, "R2-01")
    progress.assess(faculty, attempt_id, "R2-01", assessment())
    observations = progress_of(progress, resident, "R2-01")["observations"]
    assert len(observations) == 1
    unit = observations[0]
    provenance = unit["provenance"]
    assert provenance["evidence_source"] == "management_reasoning_simulator"
    assert provenance["opportunity"]["rule"] == "generation_target"
    assert len(provenance["contributions"]) == 6
    assert {item["contribution"] for item in provenance["contributions"]} == {"direct", "partial"}
    assert all(item["source_version"] for item in provenance["contributions"])
    # Six contributions and still one observation, counted once.
    assert progress_of(progress, resident, "R2-01")["count"] == 1


def test_a_foundation_challenge_is_not_offered_by_another_encounter(cohort):
    accounts, progress, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"], "R1-04")
    with pytest.raises(AccountError, match="does not match"):
        progress.assess(users["faculty"]["token"], attempt_id, "R1-03", assessment())


def test_a_challenge_observation_still_needs_a_recorded_decision(cohort):
    accounts, progress, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"], "R1-03")
    import competency_mapping
    # A reflection alone does not support it; a recorded decision does.
    assert not competency_mapping.objective_evidence_is_eligible("R1-03", [{"kind": "reflection"}])
    assert competency_mapping.objective_evidence_is_eligible("R1-03", [{"kind": "decision"}])
    assert progress.assess(users["faculty"]["token"], attempt_id, "R1-03",
                           assessment(evidence_refs=["trace:0"]))["status"] == "credited"


def test_a_brief_written_before_keeps_the_list_it_was_written_against(cohort):
    accounts, _, users = cohort
    import faculty_analysis
    attempt_id = completed(accounts, users["resident"]["token"], "R1-03")
    record = accounts.get_attempt(users["resident"]["token"], attempt_id)
    assert "R1-03" in faculty_analysis.supported_objectives(record)
    assert "R1-03" in faculty_analysis.supported_objectives(record, "1.6")
    assert "R1-03" not in faculty_analysis.supported_objectives(record, "1.5")
    assert set(faculty_analysis.supported_objectives(record, "1.5")) == {"TD1", "F1", "C1", "C3", "C4", "C14"}
