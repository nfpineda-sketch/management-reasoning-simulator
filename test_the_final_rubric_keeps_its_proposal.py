"""The final faculty rubric keeps the traceability of the AI proposal it started from.

Faculty decision 15 of 2026-09-25 ("Rúbrica provisional imprimible: aprobar A").
The proposal can be printed for faculty before any decision, marked as an AI
proposal, and it counts for nothing until a faculty member decides. Once the
decision is confirmed or modified, the final faculty version names the proposal
it started from -- its number and identifier, model, prompt and the record it
read -- and how far the decision moved from it. A proposal generated afterwards
never takes its place, and the original stays stored unchanged.
"""
import faculty_portal
import rubric
import rubric_presentation
from faculty_analysis import source_fingerprint
from rubric_store import RubricStore
from test_rubric_document import page_text
from test_rubric_store import cohort, completed_attempt, proposal_for  # noqa: F401


def _decide(store, token, attempt_id, proposal_id, status="confirmed"):
    scores = {domain: 2 for domain in rubric.DOMAIN_IDS}
    scores["D1"] = 3
    return store.save_review(token, attempt_id, proposal_id=proposal_id, scores=scores,
                             justifications={"D1": "The contingency was named before it was needed."},
                             events=[{"event_id": "acs_no_antiplatelet", "status": "dismissed",
                                      "justification": "Aspirin was executed at minute 0."}],
                             status=status)


def test_the_final_document_names_the_proposal_it_started_from_and_what_moved(cohort):
    accounts, store, users = cohort
    token = users["faculty"]["token"]
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(token, attempt_id)
    first = store.save_proposal(token, attempt_id, proposal_for(record, events=("acs_no_antiplatelet",)))
    _decide(store, token, attempt_id, first["proposal_id"])
    # Another reading is generated afterwards; the decision did not start from it.
    store.save_proposal(token, attempt_id, proposal_for(record, scores={d: 1 for d in rubric.DOMAIN_IDS}))
    saved = store.latest_review(token, attempt_id)
    chosen = faculty_portal.proposal_for_document(store, token, record, saved)
    assert (chosen["proposal_id"], chosen["sequence"]) == (first["proposal_id"], 1)
    rows = dict(rubric_presentation.traceability(saved, chosen))
    assert rows["AI proposal"] == f"#1 ({first['proposal_id'][:12]})"
    assert rows["Record read by the proposal"] == source_fingerprint(record)[:16]
    assert rows["From the proposal"] == (
        "4 of 5 domain values kept, 1 changed with a written justification; 0 proposed event(s) "
        "confirmed, 1 dismissed, 0 added by the faculty")
    words = page_text(review=saved, proposal=chosen, record=record)
    assert f"AI proposal: #1 ({first['proposal_id'][:12]})" in words
    assert "4 of 5 domain values kept" in words
    # The resident's copy of the confirmed decision reads the same proposal.
    review, proposal = store.released(users["resident"]["token"], attempt_id)
    assert proposal["proposal_id"] == first["proposal_id"]
    # And the proposal itself is unchanged by the decision that moved away from it.
    assert store.proposal(token, attempt_id, first["proposal_id"])["proposal"] == first["proposal"]


def test_before_a_decision_the_latest_proposal_is_what_is_printed_and_it_counts_for_nothing(cohort):
    accounts, store, users = cohort
    token = users["faculty"]["token"]
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(token, attempt_id)
    store.save_proposal(token, attempt_id, proposal_for(record))
    later = store.save_proposal(token, attempt_id, proposal_for(record, scores={d: 1 for d in rubric.DOMAIN_IDS}))
    chosen = faculty_portal.proposal_for_document(store, token, record, None)
    assert chosen["proposal_id"] == later["proposal_id"]
    words = page_text(review=None, proposal=chosen, record=record)
    assert "AI proposal" in words
    # Nothing enters the resident's profile until a faculty member confirms.
    assert store.progress(token, users["resident"]["id"]) == []


def test_a_decision_made_without_a_proposal_says_so(cohort):
    accounts, store, users = cohort
    token = users["faculty"]["token"]
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(token, attempt_id)
    store.save_review(token, attempt_id, scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    store.save_proposal(token, attempt_id, proposal_for(record))
    saved = store.latest_review(token, attempt_id)
    assert faculty_portal.proposal_for_document(store, token, record, saved) is None
    assert dict(rubric_presentation.traceability(saved, None))["AI proposal"] == "none used for this decision"


def test_a_proposal_of_another_encounter_is_not_read_through_this_one(cohort):
    accounts, store, users = cohort
    token = users["faculty"]["token"]
    first = completed_attempt(accounts, users["resident"]["token"])
    second = completed_attempt(accounts, users["resident"]["token"])
    saved = store.save_proposal(token, first, proposal_for(accounts.get_attempt(token, first)))
    assert store.proposal(token, second, saved["proposal_id"]) is None
    assert isinstance(store, RubricStore)
