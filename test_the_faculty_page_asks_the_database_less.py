"""A rerun of the faculty page asks the database only what it needs (2026-09-26).

Streamlit builds every store again on each rerun, and each store ran its
"CREATE TABLE IF NOT EXISTS" statements every time; the rubric panel and the
assistance context also read the same history twice. One change in the rubric
panel took twenty round trips to the database and now takes twelve, which on
the development app's remote database is most of the wait between a change and
the page settling.
"""
import pytest

import catalog_reviews
import encounter_context
import encounter_directives
import faculty_analysis_store
import management_trace_store
import progress_store
import resident_profile
import rubric_store
from account_store import AccountStore
from rubric_store import RubricStore
from test_faculty_analysis_store import cohort  # noqa: F401  (fixture)
from test_rubric_portal import attempt_on_case, page

STORES = (rubric_store.RubricStore, progress_store.ProgressStore, resident_profile.ProfileStore,
          faculty_analysis_store.FacultyBriefStore, encounter_context.EncounterContextStore,
          management_trace_store.ManagementTraceStore, catalog_reviews.CatalogReviewStore,
          encounter_directives.DirectiveStore)


def _count_transactions(monkeypatch):
    opened = []
    real = AccountStore._transaction

    def counting(self, *args, **kwargs):
        opened.append(1)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(AccountStore, "_transaction", counting)
    return opened


@pytest.mark.parametrize("store_class", STORES, ids=lambda store_class: store_class.__name__)
def test_a_store_creates_its_tables_once_per_database(tmp_path, monkeypatch, store_class):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    opened = _count_transactions(monkeypatch)
    store_class(accounts)
    created = len(opened)
    assert created >= 1
    store_class(accounts)  # the next rerun builds it again
    assert len(opened) == created


def test_another_database_still_gets_its_tables(tmp_path):
    for name in ("first", "second"):
        accounts = AccountStore(f"sqlite:///{tmp_path / (name + '.sqlite3')}", allow_sqlite=True)
        RubricStore(accounts)
        with accounts._transaction() as connection:
            tables = {row[0] for row in accounts._execute(
                connection, "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        assert {"mrs_rubric_reviews", "mrs_rubric_proposals"} <= tables, name


def test_the_rubric_panel_reads_its_revisions_once_per_rerun(cohort, monkeypatch):
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"])
    app = page(cohort, attempt_id)
    reads = []
    real = RubricStore.history

    def counting(self, token, attempt):
        reads.append(attempt)
        return real(self, token, attempt)

    monkeypatch.setattr(RubricStore, "history", counting)
    next(item for item in app.selectbox if item.label == "Your score").set_value(2).run()
    assert not app.exception
    assert reads == [attempt_id]


def test_the_current_declaration_is_the_latest_of_each_kind():
    history = [{"field": "assistance", "sequence": 1, "value": "a"},
               {"field": "assistance", "sequence": 2, "value": "b"},
               {"field": "execution", "sequence": 1, "value": "c"}]
    current = encounter_context.current_of(history)
    assert current["assistance"]["value"] == "b" and current["execution"]["value"] == "c"
    assert encounter_context.current_of([]) == {"assistance": None, "execution": None}


def test_a_database_made_again_at_the_same_path_gets_its_tables_again(tmp_path):
    """A local check deletes its database and starts from a clean one in the same process."""
    path = tmp_path / "accounts.sqlite3"
    url = f"sqlite:///{path}"
    RubricStore(AccountStore(url, allow_sqlite=True))
    path.unlink()
    accounts = AccountStore(url, allow_sqlite=True)
    RubricStore(accounts)
    with accounts._transaction() as connection:
        tables = {row[0] for row in accounts._execute(
            connection, "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    assert "mrs_rubric_reviews" in tables
