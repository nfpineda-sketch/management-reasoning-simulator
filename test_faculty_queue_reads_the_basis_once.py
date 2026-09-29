"""The faculty queue reads each encounter's frozen basis once (TD-09, cycle 10).

The night audit of cycle 5 profiled the queue: it resolved eligibility objective by objective, checking the
frozen basis's fingerprint again 17 times an encounter (3.2 s with 1000 encounters waiting, 14.5 s with
5000). It now resolves every objective from one reading (``observation_opportunities.summary``).
"""
from progress_store import ProgressStore
from test_resident_pages import program  # noqa: F401 -- the fixture


def test_the_faculty_queue_reads_each_encounters_basis_once(program, monkeypatch):  # noqa: F811
    """TD-09: the queue checked the frozen basis once per objective, 17 times an encounter."""
    import observation_opportunities
    store, _, faculty, _, _ = program
    reads = []
    original = observation_opportunities.basis_of
    monkeypatch.setattr(observation_opportunities, "basis_of", lambda record: reads.append(record["id"]) or original(record))
    waiting = ProgressStore(store).pending_reviews(faculty)
    assert waiting and len(reads) == len(waiting) == len(set(reads))
