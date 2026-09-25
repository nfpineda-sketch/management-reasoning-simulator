"""An observation with an undetermined autonomy accumulates, and meets no required level.

Faculty decision 10 of 2026-09-25 ("Autonomía no determinada: opción C,
distinguiendo observaciones de logro"). A validated observation whose autonomy
could not be determined is counted like any other, and the progress says how
many have that condition. When completing an objective requires a level of
autonomy, such an observation does not satisfy it automatically. An encounter
declared as a synthetic run keeps saying so wherever its observations appear.
"""
import pytest

import encounter_context
import objectives
import progress_portal
from account_store import AccountError
from progress_store import AUTONOMY_NOT_DETERMINED, ProgressStore, meets_autonomy
from test_assistance_autonomy_and_what_waits_for_the_faculty import cohort, completed  # noqa: F401

ASSESSMENT = {"satisfactory": True, "depth": "integrated", "context": "Septic shock",
              "evidence_refs": ["trace:0"], "notes": "Recognised and supported the hypotension."}


def _observe(accounts, users, progress, resident, autonomy):
    attempt_id = completed(accounts, users[resident]["token"])
    progress.assess(users["faculty"]["token"], attempt_id, "TD1", {**ASSESSMENT, "autonomy": autonomy})
    return attempt_id


def _td1(progress, users, resident="resident"):
    return next(goal for goal in progress.get_progress(users["faculty"]["token"], users[resident]["id"])["objectives"]
                if goal["objective_id"] == "TD1")


@pytest.mark.parametrize("autonomy, required, meets", [
    ("independent", "prompted", True), ("prompted", "prompted", True), ("guided", "prompted", False),
    (AUTONOMY_NOT_DETERMINED, "guided", False), (AUTONOMY_NOT_DETERMINED, None, True), ("guided", None, True),
])
def test_what_meets_a_required_level(autonomy, required, meets):
    assert meets_autonomy(autonomy, required) is meets


def test_without_a_required_level_every_satisfactory_observation_counts_and_is_shown_apart(cohort):
    accounts, users = cohort
    progress = ProgressStore(accounts)
    _observe(accounts, users, progress, "resident", AUTONOMY_NOT_DETERMINED)
    _observe(accounts, users, progress, "resident", "independent")
    goal = _td1(progress, users)
    assert (goal["count"], goal["satisfactory_count"], goal["autonomy_not_determined_count"]) == (2, 2, 1)
    assert goal["required_autonomy"] is None and goal["below_required_autonomy_count"] == 0


def test_a_required_level_is_never_met_by_an_undetermined_autonomy(cohort, monkeypatch):
    accounts, users = cohort
    monkeypatch.setitem(objectives.OBJECTIVES, "TD1", {**objectives.OBJECTIVES["TD1"], "required_autonomy": "prompted"})
    progress = ProgressStore(accounts)
    progress.set_target(users["admin"]["token"], "TD1", 2, "A small target for this test.")
    _observe(accounts, users, progress, "resident", AUTONOMY_NOT_DETERMINED)
    _observe(accounts, users, progress, "resident", "independent")
    _observe(accounts, users, progress, "resident", "guided")
    goal = _td1(progress, users)
    # Three satisfactory observations accumulate; one meets the required level.
    assert (goal["satisfactory_count"], goal["count"], goal["below_required_autonomy_count"]) == (3, 1, 2)
    assert goal["autonomy_not_determined_count"] == 1
    assert goal["status"] == "developing" and not goal["target_reached"]
    with pytest.raises(AccountError, match="could not be determined does not meet it"):
        progress.confirm(users["faculty"]["token"], users["resident"]["id"], "TD1", "Reviewed.")
    _observe(accounts, users, progress, "resident", "prompted")
    goal = _td1(progress, users)
    assert goal["count"] == 2 and goal["status"] == "target_reached"
    assert progress.confirm(users["faculty"]["token"], users["resident"]["id"], "TD1", "Reviewed.")["changed"]
    assert progress_portal._satisfactory_cell(goal) == "2/2 at prompted or above (4 satisfactory)"


def test_a_synthetic_run_keeps_saying_so_in_the_progress(cohort):
    accounts, users = cohort
    progress = ProgressStore(accounts)
    attempt_id = _observe(accounts, users, progress, "residente_prueba_r3", AUTONOMY_NOT_DETERMINED)
    _observe(accounts, users, progress, "residente_prueba_r3", AUTONOMY_NOT_DETERMINED)
    encounter_context.EncounterContextStore(accounts).declare(
        users["residente_prueba_r3"]["token"], attempt_id, field="execution", value="synthetic_agent",
        synthetic_accounts={"residente_prueba_r3"})
    goal = _td1(progress, users, "residente_prueba_r3")
    assert goal["synthetic_count"] == 1 and goal["autonomy_not_determined_count"] == 2
    flagged = [row["synthetic_execution"] for row in goal["observations"]]
    assert sorted(flagged) == [False, True]
    rows = progress_portal._history_rows(goal["observations"])
    assert {row["Execution"] for row in rows} == {"—", progress_portal.SYNTHETIC_RUN}
    # Nobody else's progress carries the column.
    _observe(accounts, users, progress, "resident", "guided")
    assert "Execution" not in progress_portal._history_rows(_td1(progress, users)["observations"])[0]


def test_a_progress_store_without_any_declaration_table_reads_no_synthetic_run(cohort):
    accounts, users = cohort
    progress = ProgressStore(accounts)
    _observe(accounts, users, progress, "resident", "guided")
    assert _td1(progress, users)["synthetic_count"] == 0
