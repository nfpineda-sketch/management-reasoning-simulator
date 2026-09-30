"""P-10 (faculty, 2026-09-30): an inactive account's complete portfolio is an administrator's export.

Faculty keep inspecting the historical record of an inactive resident with their usual permissions; the
complete portfolio, the official export for delivery to the former user, is prepared and downloaded only by
an administrator. Nothing in the record is removed or changed, and an active resident's portfolio is as
before for every reader.
"""
import io
import zipfile

import pytest

import portfolio
from account_store import AccountError
from test_curriculum_app import open_app
from test_resident_pages import program, show, text_of  # noqa: F401 -- the fixture


def _context(store, token):
    return {"store": store, "token": token, "user": store.get_user(token)}


def test_only_the_administrator_prepares_an_inactive_account_s_complete_portfolio(program):  # noqa: F811
    store, admin, faculty, people, reviewed = program
    resident = people["resident-one"]["id"]
    before, _ = portfolio.complete_zip(_context(store, faculty), resident)
    store.update_user(admin, resident, active=False)
    with pytest.raises(AccountError, match="Only an administrator"):
        portfolio.complete_zip(_context(store, faculty), resident)
    # Faculty still inspect the record: the same encounters and final documents, nothing removed.
    owner, rows = portfolio.entries(_context(store, faculty), resident)
    assert owner["active"] is False and [row["record"]["id"] for row in rows] == [reviewed]
    assert rows[0]["trace"] and rows[0]["review"]
    data, manifest = portfolio.complete_zip(_context(store, admin), resident)
    assert manifest and zipfile.ZipFile(io.BytesIO(data)).namelist() == zipfile.ZipFile(io.BytesIO(before)).namelist()


def test_an_active_resident_s_portfolio_is_prepared_as_before(program):  # noqa: F811
    store, admin, faculty, people, _ = program
    for token in (faculty, admin):
        _, manifest = portfolio.complete_zip(_context(store, token), people["resident-one"]["id"])
        assert manifest
    _, own = portfolio.complete_zip(_context(store, people["resident-one"]["token"]))
    assert own


def test_the_faculty_page_says_who_prepares_it_and_the_administrator_s_page_offers_it(program):  # noqa: F811
    store, admin, faculty, people, _ = program
    resident = people["resident-one"]["id"]
    store.update_user(admin, resident, active=False)
    for token, may in ((faculty, False), (admin, True)):
        at = open_app(token)
        next(b for b in at.button if b.key == "_cohort_open_" + resident).click().run()
        assert not at.exception
        show(at, "_cohort_evidence_view", "Portfolio")
        offered = any(b.label == "Prepare the complete portfolio" for b in at.button)
        assert offered is may
        assert ("is prepared by an administrator" in text_of(at)) is (not may)
        # The encounter's own documents are still there to inspect.
        assert any(b.label == "Prepare the documents" for b in at.button)
