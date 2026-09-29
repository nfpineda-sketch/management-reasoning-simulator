"""Screens the formative pilot relies on (cycle 10, C10-07: TD-42, TD-43).

TD-42: two encounters that read alike in the faculty selector are told apart.
TD-43: a portfolio ZIP prepared before another document was confirmed is not offered as current.
"""
import rubric
from curriculum_runtime import faculty_encounter_labels
from rubric_store import RubricStore
from test_curriculum_app import open_app
from test_resident_pages import _completed, navigate, program  # noqa: F401 -- the fixture


def test_two_encounters_of_the_same_minute_read_apart_in_the_faculty_selector():
    same = {"username": "resident-one", "challenge_id": "R1-03", "status": "completed", "updated_at": 1_790_000_000}
    labels = faculty_encounter_labels([{**same, "id": "b"}, {**same, "id": "a"},
                                       {**same, "id": "c", "challenge_id": "R2-05"}])
    assert len(set(labels.values())) == 3
    assert labels["a"].endswith(" · #1") and labels["b"].endswith(" · #2")
    assert "#" not in labels["c"]


def test_a_prepared_zip_is_dropped_when_another_document_is_confirmed(program):  # noqa: F811
    store, _, faculty, people, _ = program
    resident = people["resident-one"]["token"]
    other = _completed(store, resident, challenge="R2-05")
    at = open_app(resident)
    navigate(at, "My portfolio")
    next(b for b in at.button if b.label == "Prepare the complete portfolio").click().run()
    assert not at.exception
    assert any(item.label == "Download the complete portfolio (ZIP)" for item in at.get("download_button"))
    before = [str(caption.value) for caption in at.caption if "document(s)" in str(caption.value)]
    RubricStore(store).save_review(faculty, other, scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    at.run()
    assert not at.exception
    assert not any(item.label == "Download the complete portfolio (ZIP)" for item in at.get("download_button"))
    next(b for b in at.button if b.label == "Prepare the complete portfolio").click().run()
    after = [str(caption.value) for caption in at.caption if "document(s)" in str(caption.value)]
    assert before != after


def test_a_card_draws_its_radar_at_its_own_width_so_the_labels_keep_their_size():
    import re
    import faculty_cohort
    person = {"username": "resident-one", "summary": {}, "latest": None, "badge": None, "training_year": 1}
    for size in (180, 240):
        html = faculty_cohort._chart_html(person, "en", size)
        box = float(re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ', html).group(1))
        # A fixed 240 px drew the labels at 6.5-7.7 px; at most its own width, at the 10.5 px drawn.
        assert f"max-width:{box:.0f}px" in html
    assert "max-width: 240px" not in faculty_cohort._CARD_STYLE


def test_the_through_column_keeps_a_medium_width(monkeypatch):
    import evidence_views
    seen = {}
    monkeypatch.setattr(evidence_views.st, "dataframe", lambda data, **kwargs: seen.update(kwargs))
    row = {"code": "EPA-1", "label": "Title", "observations": [], "direct": 0, "partial": 0, "encounters": [],
           "objectives": [f"OBJ-{n}" for n in range(12)], "not_recorded": 0, "sources": []}
    evidence_views._framework_table([row])
    assert seen["column_config"]["Through"]["width"] == "medium"


def test_the_resident_s_evidence_opens_under_their_header_not_after_every_record(program):  # noqa: F811
    store, _, faculty, people, _ = program
    at = open_app(faculty)
    next(b for b in at.button if b.key == "_cohort_open_" + people["resident-one"]["id"]).click().run()
    assert not at.exception
    order = [item.label for item in at.expander]
    assert order.index("Evidence by framework and portfolio") < order.index("Resident activity and recorded evidence")
