"""The score and the challenge record are two things, and stay two things.

Faculty (2026-09-23): the rubric assigns a score to the encounter; achieving a
decision challenge and recording it as an observed achievement is separate. A
high score does not award a challenge, and a challenge does not raise a score.

These checks exist because the two would be easy to couple later by accident,
and coupling them would quietly turn a pilot instrument into a credential.
"""
import uuid
import time

import pytest

import rubric
from account_store import AccountStore
from progress_store import ProgressStore
from rubric_store import RubricStore
from test_rubric_portal import attempt_on_case
from test_faculty_analysis_store import cohort           # noqa: F401  (fixture)


def progress_of(accounts, users):
    return ProgressStore(accounts).get_progress(users["resident"]["token"])


def counted(progress):
    return sum(row["count"] for row in progress["objectives"])


def test_confirming_a_perfect_rubric_awards_no_challenge(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    before = counted(progress_of(accounts, users))

    store = RubricStore(accounts)
    saved = store.save_review(users["faculty"]["token"], attempt_id,
                              scores={d: 3 for d in rubric.DOMAIN_IDS}, status="confirmed")
    assert saved["totals"]["base"] == 15 and saved["status"] == "confirmed"

    after = progress_of(accounts, users)
    assert counted(after) == before == 0
    assert all(row["assessed_count"] == 0 for row in after["objectives"])


def test_a_rubric_of_zero_revokes_nothing_either(cohort):
    """The rubric does not take a recorded achievement away."""
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    store = RubricStore(accounts)
    store.save_review(users["faculty"]["token"], attempt_id,
                      scores={d: 0 for d in rubric.DOMAIN_IDS}, status="confirmed")
    progress = progress_of(accounts, users)
    assert all(row["count"] == 0 for row in progress["objectives"])
    # Nothing in the progress record mentions a score.
    assert "rubric" not in str(progress).lower()


def test_neither_module_imports_the_other():
    """The separation is structural, not a habit."""
    import ast
    from pathlib import Path
    root = Path(__file__).parent
    rubric_files = ["rubric.py", "rubric_analysis.py", "rubric_store.py",
                    "rubric_portal.py", "rubric_presentation.py",
                    "rubric_radar.py", "rubric_progress.py", "rubric_report.py",
                    "case_assessment.py", "case_assessment_bank.py"]
    progress_files = ["progress_store.py", "progress_portal.py", "objectives.py"]

    def imports(path):
        names = set()
        for node in ast.walk(ast.parse((root / path).read_text())):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        return names

    for path in rubric_files:
        assert not (imports(path) & {"progress_store", "progress_portal", "objectives"}), path
    for path in progress_files:
        assert not {name for name in imports(path) if name.startswith(("rubric", "case_assessment"))}, path
    # The rubric profile appears beside the objective dashboard on the resident
    # and faculty pages. The page composes them; neither module learns about
    # the other to make that happen (2026-09-23).
    assert "rubric" not in (root / "progress_portal.py").read_text().split(
        "def render_progress_dashboard")[0].lower()


def test_the_two_records_live_in_different_tables(cohort):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    ProgressStore(accounts)          # its tables exist; they simply stay empty
    RubricStore(accounts).save_review(users["faculty"]["token"], attempt_id,
                                      scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    with accounts._transaction() as connection:
        rubric_rows = accounts._execute(
            connection, "SELECT COUNT(*) AS n FROM mrs_rubric_reviews").fetchone()["n"]
        progress_rows = accounts._execute(
            connection, "SELECT COUNT(*) AS n FROM mrs_progress_observations").fetchone()["n"]
    assert rubric_rows == 1 and progress_rows == 0
