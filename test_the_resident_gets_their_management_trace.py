"""A resident's own Management Trace, rebuilt from the analysis already saved.

Batch scenario 1 on the development app (2026-09-25): "My progress" said "No AI
reading of this encounter was saved" beside a valid saved analysis. The document
was checked against the whole saved record, not against the frozen evidence the
analysis was written from and saved against. No provider is called here.
"""
import resident_portal
from test_management_trace_analysis import sample_report
from test_management_trace_store import cohort, session_payload  # noqa: F401  (fixture)


def _completed_with_analysis(accounts, store, token):
    attempt_id = accounts.create_attempt(token, "R1-05", {"presentation": "Synthetic test encounter"})
    accounts.save_attempt(token, attempt_id, session_payload(), status="completed")
    store.save(token, attempt_id, sample_report())
    return attempt_id


def test_my_progress_rebuilds_the_saved_management_trace(cohort):
    accounts, store, users = cohort
    token = users["resident"]["token"]
    attempt_id = _completed_with_analysis(accounts, store, token)
    context = {"store": accounts, "token": token, "user": accounts.get_user(token)}
    pdf = resident_portal._trace_pdf(context, accounts.get_attempt(token, attempt_id))
    assert pdf and pdf.startswith(b"%PDF")


def test_an_encounter_without_a_saved_analysis_still_says_so(cohort):
    accounts, store, users = cohort
    token = users["resident"]["token"]
    attempt_id = accounts.create_attempt(token, "R1-05", {"presentation": "Synthetic test encounter"})
    accounts.save_attempt(token, attempt_id, session_payload(), status="completed")
    context = {"store": accounts, "token": token, "user": accounts.get_user(token)}
    assert resident_portal._trace_pdf(context, accounts.get_attempt(token, attempt_id)) is None
