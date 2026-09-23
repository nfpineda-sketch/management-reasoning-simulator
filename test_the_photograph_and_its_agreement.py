"""The first identifiable personal data this application stores, and its rules.

Faculty decision of 2026-09-23: a face beside the initials and the training
year helps a reviewer working at a distance. Four rules came with it, and each
one is a test here.

  * nothing is stored without a signed agreement;
  * it is shown in one place, to the owner and to faculty, never to a peer;
  * the file is re-encoded, so nothing of the original survives -- including
    the EXIF block, which on a phone photograph carries where and when;
  * it can be removed, and the agreement record stays.
"""
import base64
import io
import time
import uuid

import pytest
from PIL import Image

import resident_profile
import rubric_radar
from account_store import AccountError, AccountStore, hash_password


def photo_bytes(size=(600, 400), fmt="PNG", exif=None):
    image = Image.new("RGB", size, (90, 110, 150))
    buffer = io.BytesIO()
    if exif is not None:
        image.save(buffer, format=fmt, exif=exif)
    else:
        image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def cohort(tmp_path):
    store = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    people = {}
    with store._transaction(write=True) as connection:
        for username, role, year in (("faculty_one", "faculty", None),
                                     ("resident_one", "resident", 1),
                                     ("resident_two", "resident", 2)):
            user_id = uuid.uuid4().hex
            store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                           (user_id, username, hash_password("a-password-for-tests"),
                            role, year, int(time.time())))
            people[username] = {"id": user_id, "username": username, "role": role,
                                "training_year": year,
                                "token": store._new_session(connection, user_id)}
    return store, people, resident_profile.ProfileStore(store)


# --- nothing without the agreement -----------------------------------------

def test_a_photograph_is_refused_before_the_agreement(cohort):
    _, people, profiles = cohort
    with pytest.raises(AccountError) as error:
        profiles.save(people["resident_one"]["token"], photo=photo_bytes())
    assert "agreement" in str(error.value)


def test_initials_alone_are_refused_too(cohort):
    _, people, profiles = cohort
    with pytest.raises(AccountError):
        profiles.save(people["resident_one"]["token"], initials="NP")


def test_after_accepting_it_stores(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.accept(token)
    profiles.save(token, initials="NP", photo=photo_bytes())
    stored = profiles.get(token)
    assert stored["initials"] == "NP" and stored["photo"]


def test_a_new_agreement_version_has_to_be_accepted_again(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.accept(token, version="1.0-pilot")
    with pytest.raises(AccountError):
        profiles.save(token, initials="NP", version="2.0")


def test_nobody_accepts_on_another_persons_behalf(cohort):
    _, people, profiles = cohort
    # accept() takes no user: it is always the signed-in person's own.
    profiles.accept(people["faculty_one"]["token"])
    assert profiles.accepted(people["resident_one"]["token"]) is None


# --- who may see it ---------------------------------------------------------

def stored(profiles, people, who="resident_one"):
    token = people[who]["token"]
    profiles.accept(token)
    profiles.save(token, initials="NP", photo=photo_bytes())
    return token


def test_the_owner_reads_their_own(cohort):
    _, people, profiles = cohort
    token = stored(profiles, people)
    assert profiles.get(token)["photo"]


def test_faculty_read_a_residents(cohort):
    _, people, profiles = cohort
    stored(profiles, people)
    seen = profiles.get(people["faculty_one"]["token"], people["resident_one"]["id"])
    assert seen["initials"] == "NP" and seen["photo"]


def test_a_resident_cannot_read_a_peers(cohort):
    _, people, profiles = cohort
    stored(profiles, people)
    with pytest.raises(AccountError):
        profiles.get(people["resident_two"]["token"], people["resident_one"]["id"])


def test_a_peers_badge_is_absent_rather_than_an_error(cohort):
    store, people, profiles = cohort
    stored(profiles, people)
    assert resident_profile.badge(store, people["resident_two"]["token"],
                                  people["resident_one"]["id"], 1) is None


def test_a_faculty_member_may_read_it_and_may_not_write_it(cohort):
    store, people, profiles = cohort
    stored(profiles, people)
    profiles.accept(people["faculty_one"]["token"])
    profiles.save(people["faculty_one"]["token"], initials="XX")
    # It wrote the faculty member's own profile, not the resident's.
    assert profiles.get(people["resident_one"]["token"])["initials"] == "NP"


# --- what is kept -----------------------------------------------------------

def test_the_stored_image_is_a_fresh_square_jpeg(cohort):
    encoded = resident_profile.normalise(photo_bytes((900, 300)))
    image = Image.open(io.BytesIO(base64.b64decode(encoded)))
    assert image.format == "JPEG"
    assert image.size == (resident_profile.THUMBNAIL, resident_profile.THUMBNAIL)


def test_where_and_when_the_photograph_was_taken_is_discarded():
    exif = Image.Exif()
    exif[271] = "A camera make"
    exif[306] = "2026:09:23 11:22:33"
    original = photo_bytes(exif=exif.tobytes(), fmt="JPEG")
    assert b"A camera make" in original
    encoded = resident_profile.normalise(original)
    raw = base64.b64decode(encoded)
    assert b"A camera make" not in raw
    assert not Image.open(io.BytesIO(raw)).getexif()


@pytest.mark.parametrize("payload", [b"", b"not an image at all", None, "a string"])
def test_a_file_that_is_not_an_image_is_refused(payload):
    with pytest.raises(AccountError):
        resident_profile.normalise(payload)


def test_an_enormous_file_is_refused():
    with pytest.raises(AccountError) as error:
        resident_profile.normalise(b"\x89PNG" + b"0" * (5 * 1024 * 1024))
    assert "too large" in str(error.value)


@pytest.mark.parametrize("typed, expected", [
    ("NP", "NP"), ("np", "NP"), ("Nicolas Pineda", "NP"), ("n.f. pineda", "NFP"),
    ("Ana Maria Rojas Soto", "AMRS"), ("ABCDEFG", "ABCD"), ("  ", ""), (None, ""),
])
def test_the_initials_field_reads_as_initials(typed, expected):
    assert resident_profile.initials_of(typed) == expected


# --- removing it ------------------------------------------------------------

def test_it_can_be_removed_without_giving_a_reason(cohort):
    _, people, profiles = cohort
    token = stored(profiles, people)
    profiles.forget(token)
    gone = profiles.get(token)
    assert gone["photo"] == "" and gone["initials"] == ""


def test_removing_it_keeps_the_record_that_it_was_agreed(cohort):
    _, people, profiles = cohort
    token = stored(profiles, people)
    profiles.forget(token)
    assert profiles.accepted(token) is not None


def test_removing_a_peers_is_not_possible(cohort):
    _, people, profiles = cohort
    stored(profiles, people)
    profiles.forget(people["resident_two"]["token"])
    assert profiles.get(people["resident_one"]["token"])["photo"]


# --- where it appears -------------------------------------------------------

def test_the_chart_draws_it_at_the_centre_and_under_the_data(cohort):
    store, people, profiles = cohort
    token = stored(profiles, people)
    badge = resident_profile.badge(store, token, people["resident_one"]["id"], 1)
    drawn = rubric_radar.svg([{"values": {"D1": 3, "D2": 2, "D3": 0, "D4": 2, "D5": 1}}],
                             badge=badge)
    assert "<image" in drawn and "clipPath" in drawn
    # Under the data: the image element comes before the outline path.
    assert drawn.index("<image") < drawn.index("<path")
    assert "R1" in drawn and "NP" in drawn


def test_a_zero_keeps_a_ring_of_its_own_over_the_photograph(cohort):
    store, people, profiles = cohort
    token = stored(profiles, people)
    badge = resident_profile.badge(store, token, people["resident_one"]["id"], 1)
    drawn = rubric_radar.svg([{"values": {d: 0 for d in ("D1", "D2", "D3", "D4", "D5")}}],
                             badge=badge)
    assert 'stroke="#FFFFFF"' in drawn


def test_without_a_badge_no_ring_is_added():
    drawn = rubric_radar.svg([{"values": {"D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0}}])
    assert 'stroke="#FFFFFF"' not in drawn
    assert "<image" not in drawn


def test_initials_alone_become_the_badge(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.accept(token)
    profiles.save(token, initials="AMR")
    badge = {"image": "", "initials": "AMR", "year": 2}
    drawn = rubric_radar.svg([{"values": {"D1": 2}}], badge=badge)
    assert "<image" not in drawn
    assert "AMR" in drawn and "R2" in drawn


def test_a_resident_with_nothing_stored_has_no_badge(cohort):
    store, people, _ = cohort
    assert resident_profile.badge(store, people["resident_one"]["token"],
                                  people["resident_one"]["id"], 1) is None


def test_the_document_draws_it_too(cohort):
    store, people, profiles = cohort
    token = stored(profiles, people)
    import faculty_report
    faculty_report._fonts()
    badge = resident_profile.badge(store, token, people["resident_one"]["id"], 1)
    with_badge = rubric_radar.drawing([{"values": {"D1": 2}}], badge=badge)
    without = rubric_radar.drawing([{"values": {"D1": 2}}])
    assert len(with_badge.contents) > len(without.contents)


def test_a_photograph_that_cannot_be_decoded_still_draws_the_chart():
    import faculty_report
    faculty_report._fonts()
    art = rubric_radar.drawing([{"values": {"D1": 2}}],
                               badge={"image": "data:image/jpeg;base64,!!!not base64!!!",
                                      "initials": "NP", "year": 1})
    assert art.contents


# --- asked once, at the start ----------------------------------------------

def test_a_new_resident_has_not_been_asked_yet(cohort):
    _, people, profiles = cohort
    assert profiles.decision(people["resident_one"]["token"]) is None


def test_agreeing_records_the_decision(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.accept(token)
    assert profiles.decision(token) == "accepted"


def test_declining_records_it_too_so_the_question_stops(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.decline(token)
    assert profiles.decision(token) == "declined"


def test_declining_stores_nothing_about_the_person(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.decline(token)
    stored = profiles.get(token)
    assert stored["photo"] == "" and stored["initials"] == ""
    # And it is not an acceptance: storing anything is still refused.
    assert profiles.accepted(token) is None
    with pytest.raises(AccountError):
        profiles.save(token, initials="NP")


def test_declining_and_then_agreeing_later_works(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.decline(token)
    profiles.accept(token)
    assert profiles.decision(token) == "accepted"
    profiles.save(token, initials="NP")
    assert profiles.get(token)["initials"] == "NP"


def test_a_new_agreement_version_is_asked_about_again(cohort):
    _, people, profiles = cohort
    token = people["resident_one"]["token"]
    profiles.accept(token, version="1.0-pilot")
    assert profiles.decision(token, version="1.0-pilot") == "accepted"
    assert profiles.decision(token, version="2.0") is None


def test_one_residents_decision_is_not_anothers(cohort):
    _, people, profiles = cohort
    profiles.accept(people["resident_one"]["token"])
    assert profiles.decision(people["resident_two"]["token"]) is None


def test_a_resident_cannot_read_a_peers_decision(cohort):
    _, people, profiles = cohort
    profiles.accept(people["resident_one"]["token"])
    with pytest.raises(AccountError):
        profiles.decision(people["resident_two"]["token"], people["resident_one"]["id"])


# --- the year belongs to the person, not to the reader ---------------------

PROFILE_APP = """
import streamlit as st
from account_store import AccountStore
from rubric_portal import render_rubric_profile
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
target = st.session_state.get('target')
# The page computes the year and passes it in; the rubric must not import the
# objective record to find it out.
import ast, pathlib
from curriculum_runtime import _training_year
render_rubric_profile(context, target, training_year=_training_year(context, target))
"""


def profile_page(store, token, target=None):
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_string(PROFILE_APP, default_timeout=20)
    app.session_state["database_url"] = store._url
    app.session_state["test_token"] = token
    app.session_state["target"] = target
    app.run()
    assert not app.exception
    return " ".join(item.value for item in app.markdown)


def assessed(store, people, who="resident_two"):
    import rubric
    from rubric_store import RubricStore
    token = people[who]["token"]
    attempt = store.create_attempt(token, "R1-03", {"presentation": "x"})
    store.save_attempt(token, attempt, {"schema_version": "mrs_attempt_v1", "session": {
        "review_completed": True, "encounter": {"authored_case_id": "acs_48m_wellens"},
        "management_trace": [{"execution_status": "executed", "learner_input": "Give aspirin.",
                              "decision_time_min": 0, "response_time_min": 1,
                              "reasoning": {"problem_representation": "m"},
                              "state_before": {"observable": {}},
                              "state_after": {"observable": {}}}]}}, status="completed")
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt,
                                   scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    return attempt


def test_the_badge_carries_the_year_on_the_residents_own_page(cohort):
    store, people, profiles = cohort
    token = people["resident_two"]["token"]           # a second-year resident
    profiles.accept(token)
    profiles.save(token, initials="AM", photo=photo_bytes())
    assessed(store, people)
    own = profile_page(store, token)
    assert "R2" in own and "<image" in own


def test_a_faculty_reader_sees_the_residents_year_and_not_their_own(cohort):
    store, people, profiles = cohort
    token = people["resident_two"]["token"]
    profiles.accept(token)
    profiles.save(token, initials="AM", photo=photo_bytes())
    assessed(store, people)
    # A faculty member has no training year of their own; the badge must still
    # carry the resident's, which is the whole point of showing it.
    seen = profile_page(store, people["faculty_one"]["token"], people["resident_two"]["id"])
    assert "R2" in seen and "<image" in seen
    assert "R1" not in seen


def test_the_rubric_never_learns_about_the_objective_record():
    """Where the year is read from is the page's business, not the rubric's."""
    import ast
    from pathlib import Path
    names = set()
    for node in ast.walk(ast.parse(Path("rubric_portal.py").read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not (names & {"progress_store", "progress_portal", "objectives"})
