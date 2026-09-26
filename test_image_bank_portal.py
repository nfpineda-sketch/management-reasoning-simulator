"""The image bank in the application: its panel for faculty, the reviews, and the room (2026-09-26)."""
import pytest

import image_pack
from account_store import AccountError
from image_bank import ImageBank
from test_curriculum_app import click, cohort, open_app  # noqa: F401  (fixture)

HAS_PACK = image_pack.read_manifest() is not None


def _panel(at):
    return next((exp for exp in at.expander if exp.label == "Patient image bank (faculty)"), None)


def test_faculty_see_the_bank_and_residents_do_not(cohort):
    store, admin, resident = cohort
    assert _panel(open_app(resident)) is None
    at = open_app(admin)
    panel = _panel(at)
    assert panel is not None
    text = " ".join(str(item.value) for item in panel.markdown)
    assert "Budget `imagenes-2026-09-26`" in text


def test_the_budget_line_shows_dollars_not_a_formula(cohort):
    # Streamlit's markdown reads the text between two dollar signs as a formula:
    # in a browser the line came out as "US2.50ofUS10.00(US2.50fromtheprovider..."
    # (2026-09-26). Every dollar sign it shows is escaped.
    import re
    _, admin, _ = cohort
    line = next(str(item.value) for item in _panel(open_app(admin)).markdown
                if str(item.value).startswith("**Budget"))
    assert "US\\$" in line
    assert not re.search(r"(?<!\\)\$", line)


@pytest.mark.skipif(not HAS_PACK, reason="No pack in this checkout.")
def test_every_budget_in_the_ledger_has_its_line(cohort):
    # The second authorization was spent in reviewed batches outside the app; the
    # app spends from the first. Both stay visible, each with its own totals.
    _, admin, _ = cohort
    lines = [str(item.value) for item in _panel(open_app(admin)).markdown if "Budget" in str(item.value)]
    assert any("imagenes-2026-09-26`" in line and "not the one" not in line for line in lines)
    assert any("imagenes-2026-09-26-b" in line and "not the one this app spends from" in line for line in lines)


@pytest.mark.skipif(not HAS_PACK, reason="No pack in this checkout.")
def test_the_pilots_photographs_are_there_with_every_review_pending(cohort):
    store, admin, _ = cohort
    at = open_app(admin)
    panel = _panel(at)
    captions = " ".join(str(item.value) for item in panel.caption)
    assert "visual review Pending · clinical review Pending" in captions
    assert "Approved" not in captions
    assets = ImageBank(store).assets()
    assert assets and all(a["visual_review"] == a["clinical_review"] == "pending" for a in assets)


@pytest.mark.skipif(not HAS_PACK, reason="No pack in this checkout.")
def test_a_review_is_recorded_with_the_account_that_records_it(cohort):
    store, admin, resident = cohort
    at = open_app(admin)
    panel = _panel(at)
    form_select = next(w for w in at.selectbox if w.label == "Image")
    chosen = form_select.options[0]
    next(w for w in at.radio if w.label == "Record").set_value("Visual review")
    next(w for w in at.radio if w.label == "Decision (for a review)").set_value("approved")
    next(w for w in at.text_area if w.label == "What you looked at and why").set_value("Face, hands, devices.")
    next(b for b in at.button if b.label == "Record").click().run()
    assert not at.exception
    bank = ImageBank(store)
    asset = next(a for a in bank.assets() if a["id"] == form_select.value)
    assert asset["visual_review"] == "approved" and asset["clinical_review"] == "pending"
    reviews = bank.reviews(admin, asset["id"])
    assert reviews[-1]["username"] == "teacher" and reviews[-1]["note"] == "Face, hands, devices."
    with pytest.raises(AccountError):
        bank.review(resident, asset["id"], "clinical_review", "approved")
    with pytest.raises(AccountError):
        bank.exclude(admin, asset["id"], "")              # an exclusion says why


def test_a_residents_encounter_room_uses_the_bank(cohort):
    store, _, resident = cohort
    at = open_app(resident)
    click(at, "Begin Encounter")
    assert not at.exception
    import image_scene
    assert isinstance(at.session_state["_scene_jobs"], image_scene.View)
    status = at.session_state["_scene_status"]
    # No key in this test: a photograph is shown only if the bank already has it.
    assert status["state"] in ("ready", "unavailable")
    if status["state"] == "unavailable":
        assert status["code"] in ("CONFIG", "NOT_ALLOWED")
