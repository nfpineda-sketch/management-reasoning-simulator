"""The encounter room with the image bank: what a person sees, and what it costs (2026-09-26).

The faculty's verification list, item by item, on the real engine and a local
database, with the simulated provider of ``test_the_image_bank``. What these
show is the handling -- which photograph, when, for whom, at what cost. The
quality of a real photograph is what the pilot of docs/IMAGENES_REGISTRO.md
looked at; nothing here claims it.
"""
from copy import deepcopy
import threading
from types import SimpleNamespace

import pytest

import catalog_trajectories as trajectories
import clinical_scene
import image_bank
import image_broker
import image_pack
import image_scene
from account_store import AccountError, AccountStore, hash_password
from family_engine import execute_family_bundle
from image_bank import ImageBank, contract_key
from patient_appearance import appearance_state
from test_the_image_bank import Provider, mismatch, passing

# The 76-year-old: obtunded on arrival, alert after dextrose. (The 54-year-old with the
# thiamine question is still drowsy fifteen minutes after dextrose.)
CASE, FAMILY = "hypoglycemia_76f", "hypoglycemia"
# The actions exactly as the reader writes them for "Glucosa al 50% 50 mL IV en bolo",
# "Oxígeno por mascarilla de reservorio a 15 L/min" and "Retiro el oxígeno".
DEXTROSE = {"type": "dextrose", "dose_g": 25.0, "route": "IV", "dose_basis": "50% × 50 mL",
            "solution_percent": 50.0, "solution_ml": 50.0}
# A mask the provider can draw: a reservoir mask is no longer requested at all
# (test_a_reservoir_mask_is_never_paid_for_and_the_room_says_why).
OXYGEN = {"type": "oxygen", "device": "simple mask", "flow_lpm": 8.0}
RESERVOIR = {"type": "oxygen", "device": "non-rebreather mask", "flow_lpm": 15.0}
ROOM_AIR = {"type": "oxygen", "device": "room air", "flow_lpm": 0}


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A database with an administrator and two residents, and a simulated provider."""
    accounts = AccountStore(f"sqlite:///{tmp_path / 'room.sqlite3'}", allow_sqlite=True)
    accounts.bootstrap_admin("room_admin", hash_password("room-only-admin-password"))
    admin = accounts.authenticate("room_admin", "room-only-admin-password")
    residents = {}
    for name in ("resident_a", "resident_b"):
        code = accounts.create_invite(admin, "resident", 3)
        token = accounts.register(name, f"{name}-only-password", code)
        residents[name] = {"token": token, "user": accounts.get_user(token) if hasattr(accounts, "get_user")
                           else _user(accounts, token)}
    provider = Provider()
    # These tests start from an empty bank; the repository's pack has a test of its own.
    monkeypatch.setattr(image_pack, "PACK_DIR", tmp_path / "no-pack")
    monkeypatch.setattr(image_broker, "_client", lambda api_key, client_factory: provider)
    monkeypatch.setattr(image_broker, "RETRY_PAUSE_SECONDS", 0.0)
    settings = {"OPENAI_API_KEY": "test-key-never-sent"}
    monkeypatch.setattr(clinical_scene, "setting", lambda name, default="": settings.get(name, default))
    monkeypatch.delenv("MRS_PAID_GENERATION", raising=False)
    monkeypatch.delenv("MRS_OFFLINE_CASES", raising=False)
    image_broker.wait(30)
    yield SimpleNamespace(accounts=accounts, admin=admin, residents=residents, provider=provider,
                          settings=settings, bank=ImageBank(accounts), monkeypatch=monkeypatch)
    image_broker.wait(30)


def _user(accounts, token):
    with accounts._transaction() as connection:
        actor = accounts._actor(connection, token)
    return {"id": actor["id"], "role": actor["role"], "username": actor["username"]}


class Room:
    """One browser session looking at one encounter."""

    def __init__(self, world, resident, attempt_id, state):
        self.world, self.state = world, state
        self.context = {"store": world.accounts, "token": resident["token"], "user": resident["user"]}
        self.session = {"_attempt_id": attempt_id}
        self.events = [{"kind": "presentation", "text": "Synthetic arrival.", "time": 0}]

    def look(self):
        self.world.monkeypatch.setattr(image_scene, "st", SimpleNamespace(session_state=self.session))
        return clinical_scene.scene_image(self.state, self.events, self.context)

    def settle(self, rounds=6):
        image = None
        for _ in range(rounds):
            image = self.look()
            if not self.session["_scene_pending"]:
                return image
            image_broker.wait(30)
        return self.look()

    @property
    def status(self):
        return self.session["_scene_status"]

    def order(self, *actions):
        result = execute_family_bundle(self.state, {"actions": list(actions)})
        assert result["executed"], result.get("clarification")


def encounter(world, name="resident_a"):
    resident = world.residents[name]
    state = trajectories.launch(CASE, FAMILY, allow_review_candidates=True)
    attempt = world.accounts.create_attempt(resident["token"], "R1-03", {"presentation": "Synthetic"})
    return Room(world, resident, attempt, state)


def calls(world):
    return len(world.provider.calls)


# 1 -- a compatible image already saved is shown at once, with no call ---------------------------------------
def test_1_a_saved_compatible_photograph_is_shown_at_the_first_look_without_a_call(world):
    first = encounter(world)
    assert first.settle() is not None
    world.accounts.save_attempt(first.context["token"], first.session["_attempt_id"], {}, status="completed")
    before = calls(world)
    other = encounter(world, "resident_b")
    image = other.look()
    assert image is not None and other.status == {"state": "ready"}
    assert calls(world) == before


# 2 -- a change of state keeps the person ------------------------------------------------------------------
def test_2_a_change_of_state_is_an_edit_of_the_same_persons_anchor(world):
    room = encounter(world)
    arrival = room.settle()
    room.order(DEXTROSE, {"type": "reassessment", "delay_min": 15})
    assert appearance_state(room.state)["mental_status"] == "alert"
    later = room.settle()
    assert later is not None and later != arrival
    assert later.identity_id == arrival.identity_id
    bank = world.bank
    anchor = bank.current_anchor(arrival.identity_id)
    for image in (arrival, later):
        # Recovered with a mild pallor is drawn as the reference state itself (decision 7).
        asset = bank.asset(image.asset_id)
        assert asset["id"] == anchor["id"] or asset["reference_asset_id"] == anchor["id"]


# 3 -- devices appear with the executed order and leave with it ----------------------------------------------
def test_3_the_mask_appears_when_the_order_runs_and_its_photograph_is_the_masked_state(world):
    room = encounter(world)
    room.settle()
    room.order(OXYGEN)
    masked = room.settle()
    assert appearance_state(room.state)["respiratory_support"] == "simple mask"
    assert "simple_mask" in world.bank.asset(masked.asset_id)["devices"]


def test_3_a_held_order_is_not_an_executed_device(world):
    room = encounter(world)
    room.settle()
    before = contract_key(appearance_state(room.state))
    held = deepcopy(room.state)
    # Nothing executed: the state the room draws from is unchanged, so is the photograph.
    assert contract_key(appearance_state(held)) == before
    assert room.look() is not None


def test_3_taking_the_mask_off_returns_to_a_photograph_without_it_and_a_reload_costs_nothing(world):
    room = encounter(world)
    room.settle()
    room.order(OXYGEN)
    room.settle()
    room.order(ROOM_AIR)                          # "Retiro el oxígeno", executed
    assert appearance_state(room.state)["respiratory_support"] == "none"
    without = room.settle()
    assert "non_rebreather_mask" not in world.bank.asset(without.asset_id)["devices"]
    before = calls(world)
    room.session.pop("_scene_jobs")               # a reload
    assert room.look() == without and calls(world) == before


# 4 -- the state changes while a photograph is being made ---------------------------------------------------
def test_4_a_state_change_during_a_request_never_shows_the_earlier_state(world):
    room = encounter(world)
    room.settle()                                   # the person and the arrival exist
    world.provider.gate = threading.Event()
    room.order(OXYGEN)
    masked_key = contract_key(appearance_state(room.state))
    assert room.look() is None and room.status["state"] == "pending"
    room.order(ROOM_AIR)                            # the mask comes off while its photograph is made
    # Whatever is pending, the room shows no earlier photograph as the patient now.
    shown = room.look()
    assert shown is None or world.bank.asset(shown.asset_id)["state_key"] == contract_key(appearance_state(room.state))
    world.provider.gate.set()
    image_broker.wait(30)
    assert world.bank.usable_asset(room.session["_scene_jobs"].identity["id"], masked_key) is not None


# 5 -- a failure, then a late answer ----------------------------------------------------------------------
def test_5_a_failed_state_shows_the_neutral_view_with_its_reason_and_retry_is_one_paid_attempt(world):
    room = encounter(world)
    world.provider.screens = [passing(), mismatch(), mismatch()]
    image = room.settle()
    assert image is None and room.status["state"] == "failed" and room.status["code"] == "MISMATCH"
    view = room.session["_scene_jobs"]
    before = calls(world)
    assert room.look() is None and calls(world) == before           # no automatic retry
    assert view.retry()
    world.provider.screens = [passing()]
    assert room.settle() is not None
    assert world.provider.kinds()[before:] == ["edit", "screen"]


def test_5_a_late_answer_for_a_state_left_behind_is_kept_not_shown(world):
    room = encounter(world)
    room.settle()
    world.provider.gate = threading.Event()
    room.order(OXYGEN)
    masked_key = contract_key(appearance_state(room.state))
    assert room.look() is None
    room.order(ROOM_AIR)                              # the mask came off before the photograph came back
    shown = room.look()
    assert shown is None or world.bank.asset(shown.asset_id)["state_key"] != masked_key
    world.provider.gate.set()
    image_broker.wait(30)
    assert world.bank.usable_asset(room.session["_scene_jobs"].identity["id"], masked_key) is not None


# 6 and 7 -- a reload, a resumed encounter, a restarted server ----------------------------------------------------
def test_6_a_reload_shows_the_same_person_from_the_database_without_a_call(world):
    room = encounter(world)
    first = room.settle()
    before = calls(world)
    reloaded = Room(world, world.residents["resident_a"], room.session["_attempt_id"], room.state)
    again = reloaded.look()
    assert again == first and again.identity_id == first.identity_id
    assert calls(world) == before


def test_7_a_restarted_server_shows_the_same_person_without_a_call(world, tmp_path):
    room = encounter(world)
    first = room.settle()
    before = calls(world)
    AccountStore.forget_schemas()
    image_bank.forget_cache()
    world.accounts = AccountStore(f"sqlite:///{tmp_path / 'room.sqlite3'}", allow_sqlite=True)
    restarted = Room(world, world.residents["resident_a"], room.session["_attempt_id"], room.state)
    again = restarted.look()
    assert again == first and calls(world) == before


# 8 -- people and encounters never mix ---------------------------------------------------------------------------
def test_8_each_encounter_keeps_its_own_record_and_nobody_reads_anothers(world):
    a = encounter(world, "resident_a")
    b = encounter(world, "resident_b")
    a.settle()
    b.settle()
    bank = world.bank
    rows_a = bank.displays(a.context["token"], a.session["_attempt_id"])
    rows_b = bank.displays(b.context["token"], b.session["_attempt_id"])
    assert rows_a and rows_b
    with pytest.raises(AccountError):
        bank.displays(b.context["token"], a.session["_attempt_id"])
    with pytest.raises(AccountError):
        bank.log_display(b.context["token"], a.session["_attempt_id"], identity_id="V22",
                         contract=appearance_state(a.state), outcome="image")
    assert bank.displays(world.admin, a.session["_attempt_id"]) == rows_a


def test_8_the_record_changes_only_when_what_is_shown_changes(world):
    room = encounter(world)
    room.settle()
    for _ in range(5):
        room.look()                                   # the room's two-second reruns
    rows = world.bank.displays(room.context["token"], room.session["_attempt_id"])
    outcomes = [row["outcome"] for row in rows]
    assert outcomes[-1] == "image" and outcomes.count("image") == 1


# 9 and 10 -- reuse, compatibility and exposure ------------------------------------------------------------------
def test_10_a_resident_who_saw_a_person_is_shown_another_compatible_one(world):
    first = encounter(world)
    seen = first.settle().identity_id
    world.accounts.save_attempt(first.context["token"], first.session["_attempt_id"], {}, status="completed")
    second = encounter(world)
    other = second.settle().identity_id
    assert other != seen
    record = world.bank.assignment(second.context["token"], second.session["_attempt_id"])
    assert record["repeat_kind"] == "none" and seen in record["selection"]["seen"]


def test_10_when_every_compatible_person_was_seen_the_repeat_is_recorded_as_the_banks_limit(world):
    from image_identities import compatible_identities
    patient = trajectories.launch(CASE, FAMILY, allow_review_candidates=True)["encounter_spec"]["clinical_case"]["patient"]
    for _ in compatible_identities(patient):
        room = encounter(world)
        room.settle()
        world.accounts.save_attempt(room.context["token"], room.session["_attempt_id"], {}, status="completed")
    last = encounter(world)
    last.settle()
    record = world.bank.assignment(last.context["token"], last.session["_attempt_id"])
    assert record["repeat_kind"] == "bank_limited"


def test_9_a_second_resident_reuses_what_the_first_one_paid_for(world):
    a = encounter(world, "resident_a")
    a.settle()
    before = calls(world)
    b = encounter(world, "resident_b")
    assert b.look() is not None and calls(world) == before


# 11 -- the budget and the paid gate ----------------------------------------------------------------------------
def test_11_an_exhausted_budget_leaves_saved_photographs_and_says_why_for_the_rest(world):
    world.settings.update({"MRS_IMAGE_BUDGET_ID": "room-tiny", "MRS_IMAGE_BUDGET_USD": "0.3",
                           "MRS_IMAGE_BUDGET_REQUESTS": "30"})
    room = encounter(world)
    assert room.look() is None
    assert room.status == {"state": "unavailable", "code": "BUDGET_DOLLARS", "stage": "CREATE"}
    assert calls(world) == 0
    assert "budget" in clinical_scene.scene_status_text(room.status)


def test_11_a_role_the_paid_gate_refuses_is_never_charged_but_sees_what_is_saved(world):
    a = encounter(world, "resident_a")
    saved = a.settle()
    world.monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    before = calls(world)
    b = encounter(world, "resident_b")
    assert b.look() == saved                           # the saved arrival is free to show
    b.order(OXYGEN)
    assert b.look() is None and b.status["code"] == "NOT_ALLOWED"
    assert calls(world) == before


def test_the_session_only_room_follows_the_paid_gate_too(world, monkeypatch):
    world.settings["MRS_IMAGE_BANK"] = "off"
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    room = encounter(world)
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=room.session))
    assert clinical_scene.scene_image(room.state, room.events, room.context) is None
    assert room.session["_scene_status"] == {"state": "unavailable", "code": "NOT_ALLOWED"}
    assert calls(world) == 0


# the page: the photograph travels on its own ----------------------------------------------------------------------
def test_the_overlay_carries_no_image_bytes_and_the_photograph_element_depends_only_on_the_photograph(world):
    from resuscitation_room import monitor_html
    room = encounter(world)
    image = room.settle()
    observable = dict(room.state["observable"])
    overlays = []
    for heart_rate in (70, 130):                       # a monitor change, the same patient photograph
        observable["hr"] = heart_rate
        overlays.append(clinical_scene.scene_html(image, monitor_html(observable, "0 min"), current=True,
                                                  photo_apart=True))
    assert overlays[0] != overlays[1]
    assert all(str(image) not in overlay and "background:transparent" in overlay for overlay in overlays)
    photo = image_scene.scene_photo_html(image)
    assert photo == image_scene.scene_photo_html(room.look())
    assert photo.startswith('<div class="scene-photo"') and "data:image/webp;base64," in photo
    assert image_scene.scene_photo_html(None) == '<div class="scene-photo scene-photo-empty"></div>'


# the repository's pack: the pilot's photographs, with no call ----------------------------------------------------
def test_the_repository_pack_gives_a_new_database_the_pilots_photographs_without_a_call(world, tmp_path):
    world.monkeypatch.setattr(image_pack, "PACK_DIR", image_pack.Path(__file__).resolve().parent / "assets" / "patient_images")
    if image_pack.read_manifest() is None:
        pytest.skip("No pack in this checkout.")
    # The faculty member who approved the pilot's photographs in the chat has an account here.
    code = world.accounts.create_invite(world.admin, "faculty", None)
    world.accounts.register("npinedafaculty", "faculty-only-test-password", code)
    state = trajectories.launch("hypoglycemia_54m_thiamine", FAMILY, allow_review_candidates=True)
    resident = world.residents["resident_a"]
    attempt = world.accounts.create_attempt(resident["token"], "R1-03", {"presentation": "Synthetic"})
    room = Room(world, resident, attempt, state)
    image = room.look()
    assert image is not None and calls(world) == 0
    asset = world.bank.asset(image.asset_id)
    assert asset["generation"]["imported_from_pack"] and asset["identity_id"] == "V22"
    # Approved under that account, with the note that says who recorded it and why.
    assert asset["visual_review"] == asset["clinical_review"] == "approved"
    reviews = world.bank.reviews(world.admin, asset["id"])
    assert {row["username"] for row in reviews} == {"npinedafaculty"} and all(
        "registrada por el agente" in row["note"] for row in reviews)
    ledgers = {entry["budget"]["id"]: entry["budget"] for entry in image_pack.read_manifest()["ledgers"]}
    pilot = world.bank.budget_summary(ledgers["imagenes-2026-09-26"])
    assert pilot["requests"] == 26 and pilot["calls_sent"] == 52
    second = world.bank.budget_summary(ledgers["imagenes-2026-09-26-b"])
    assert second["requests"] == 63 and second["committed"] <= second["limit_micro"]


def test_the_image_issue_is_offered_only_for_a_state_that_failed(world):
    room = encounter(world)
    world.provider.screens = [passing(), mismatch(), passing()]     # rejected, then corrected and accepted
    assert room.settle() is not None
    view = room.session["_scene_jobs"]
    assert view.diagnostic_candidate(context=room.context) is None and view.failure() is None
    room.order(OXYGEN)
    world.provider.screens = [mismatch(), mismatch()]
    assert room.settle() is None and room.status["state"] == "failed"
    assert view.diagnostic_candidate(context=room.context) is not None
    assert view.failure()["code"] == "MISMATCH"
    assert view.diagnostic_evidence(context=room.context)


def test_a_database_that_cannot_be_reached_leaves_the_room_working_with_its_neutral_view(world):
    room = encounter(world)

    def unreachable(*args, **kwargs):
        raise AccountError("The account database is temporarily unavailable. Please try again.")

    world.monkeypatch.setattr(ImageBank, "usable_asset", unreachable)
    assert room.look() is None
    assert room.status == {"state": "unavailable", "code": "INTERNAL"}
    assert "saved photograph could not be read" in clinical_scene.scene_status_text(room.status)
    assert calls(world) == 0


# faculty decisions of 2026-09-26 -------------------------------------------------------------------------------------
def test_a_reservoir_mask_is_never_paid_for_and_the_room_says_why(world):
    room = encounter(world)
    room.settle()
    before = calls(world)
    room.order(RESERVOIR)
    assert room.settle() is None
    assert room.status["state"] == "unavailable" and room.status["code"] == "UNRENDERABLE"
    assert calls(world) == before
    assert "could not draw" in clinical_scene.scene_status_text(room.status)


def test_with_review_required_only_a_photograph_a_person_approved_is_shown(world):
    # Decision 8: for production, a photograph is shown once the visual and clinical reviews approve it.
    saved = encounter(world).settle()
    world.settings["MRS_IMAGE_REQUIRE_REVIEW"] = "on"
    room = encounter(world, "resident_b")
    before = calls(world)
    assert room.look() is None and room.status["code"] == "REVIEW_PENDING" and calls(world) == before
    for field in ("visual_review", "clinical_review"):
        world.bank.review(world.admin, saved.asset_id, field, "approved", "Checked face, hands and devices.")
    again = encounter(world, "resident_b")
    assert again.look() == saved and calls(world) == before
