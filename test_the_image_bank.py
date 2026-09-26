"""The image bank and its broker, with a simulated provider (no paid call, no network).

What these show is the handling: what is sent, reserved, kept and shown. They
say nothing about the quality of a real photograph -- that needs the provider.
"""
import base64
import hashlib
import json
import threading
import time
import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

import image_bank
import image_broker
from account_store import AccountStore
from image_bank import BudgetRefused, ImageBank, contract_key
from image_identities import identity
from image_pricing import DEFAULT_BUDGET, MICRO
from scene_errors import CHECK_IDS

IMAGE_MODEL, REVIEW_MODEL = "gpt-image-1.5", "gpt-5-mini"
ARRIVAL = {"mental_status": "drowsy", "expression": "uncomfortable", "work_of_breathing": "normal",
           "skin_color": "mild pallor", "diaphoresis": "marked", "mottling": False, "respiratory_support": "none"}
MASKED = {**ARRIVAL, "respiratory_support": "non-rebreather mask"}


def png(seed):
    """A valid 1536x1024 PNG whose colour depends on the seed: different requests, different bytes."""
    digest = hashlib.sha256(str(seed).encode()).digest()
    output = BytesIO()
    Image.new("RGB", (1536, 1024), tuple(digest[:3])).save(output, format="PNG")
    return output.getvalue()


def passing(limitations=False):
    return {"checks": {name: True for name in CHECK_IDS}, "uncertain_checks": []}


def mismatch(check="expression"):
    return {"checks": {name: name != check for name in CHECK_IDS}, "uncertain_checks": [],
            "conflict_evidence": [{"check": check, "finding": "A smile where discomfort is required."}]}


class ProviderError(Exception):
    def __init__(self, status):
        super().__init__(f"status {status}")
        self.status_code = status
        self.body = {}


class Provider:
    """An OpenAI-shaped client: records every call, answers from queues or with success."""

    def __init__(self, screens=(), failures=None, delay=0.0):
        self.calls = []
        self.screens = list(screens)
        self.failures = dict(failures or {})   # kind -> list of exceptions, raised in order
        self.delay = delay
        self.gate = None                       # a threading.Event the provider waits on, when set
        outer = self

        class Images:
            def generate(self, **kwargs):
                return outer._image("create", kwargs)

            def edit(self, **kwargs):
                images = kwargs["image"] if isinstance(kwargs["image"], list) else [kwargs["image"]]
                kind = "repair" if any("rejected" in getattr(i, "name", "") for i in images) else "edit"
                return outer._image(kind, kwargs)

        class Responses:
            def create(self, **kwargs):
                outer._enter("screen", kwargs)
                result = outer.screens.pop(0) if outer.screens else passing()
                return SimpleNamespace(status="completed", output_text=json.dumps(result),
                                       output=[], usage=SimpleNamespace(input_tokens=9000, output_tokens=700))

        self.images = Images()
        self.responses = Responses()

    def _enter(self, kind, kwargs):
        self.calls.append((kind, kwargs))
        if self.gate is not None:
            assert self.gate.wait(10), "the test never released the provider"
        if self.delay:
            time.sleep(self.delay)
        queue = self.failures.get(kind)
        if queue:
            raise queue.pop(0)

    def _image(self, kind, kwargs):
        self._enter(kind, kwargs)
        raw = png(f"{kind}:{len(self.calls)}:{kwargs.get('prompt', '')[:40]}")
        usage = SimpleNamespace(input_tokens=7200 if kind != "create" else 700, output_tokens=406,
                                input_tokens_details=SimpleNamespace(
                                    image_tokens=6500 if kind != "create" else 0,
                                    text_tokens=700))
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode("ascii"))], usage=usage)

    def kinds(self):
        return [kind for kind, _ in self.calls]


@pytest.fixture
def bank(tmp_path):
    return ImageBank(AccountStore(f"sqlite:///{tmp_path / 'bank.sqlite3'}", allow_sqlite=True))


@pytest.fixture(autouse=True)
def quick_retries(monkeypatch):
    monkeypatch.setattr(image_broker, "RETRY_PAUSE_SECONDS", 0.0)
    image_broker.wait(30)
    yield
    image_broker.wait(30)


def ask(bank, provider, contract, *, person="V27", budget=None, force=False, allowed=True, model=IMAGE_MODEL):
    return image_broker.request(bank, identity(person), contract, api_key="", allowed=allowed,
                                image_model=model, review_model=REVIEW_MODEL, requested_by="test",
                                budget=budget or dict(DEFAULT_BUDGET), client_factory=lambda: provider,
                                force=force)


def settle(bank, provider, contract, **kwargs):
    """Ask, let the job finish, and ask again until the answer is no longer 'pending'.

    A new person's first request makes their anchor; the state follows on the next one.
    """
    first = outcome = ask(bank, provider, contract, **kwargs)
    for _ in range(4):
        if outcome.state != "pending":
            break
        image_broker.wait(30)
        outcome = ask(bank, provider, contract, **kwargs)
    return first, outcome


# --- identity: the anchor first, every state an edit of it ------------------------------------------------
def test_a_new_person_is_drawn_once_in_a_neutral_state_and_every_state_is_an_edit_of_that_photograph(bank):
    provider = Provider()
    first, second = settle(bank, provider, ARRIVAL)
    assert first.state == "pending"
    assert second.state == "ready"
    assert provider.kinds() == ["create", "screen", "edit", "screen"]
    anchor = bank.usable_asset("V27", image_broker.ANCHOR_KEY)
    assert anchor["role"] == "anchor" and anchor["contract"] == image_broker.ANCHOR_CONTRACT
    assert second.asset["reference_asset_id"] == anchor["id"]
    # The edit was sent the anchor's own bytes, not a description of the person.
    edit = provider.calls[2][1]
    assert edit["image"].name.startswith("anchor.")
    assert edit["image"].getvalue() == bank.blob(anchor["master_sha256"])
    assert edit["input_fidelity"] == "high"


def test_a_second_state_of_the_same_person_is_one_edit_of_the_same_anchor(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    before = len(provider.calls)
    _, masked = settle(bank, provider, MASKED)
    assert provider.kinds()[before:] == ["edit", "screen"]
    anchor = bank.usable_asset("V27", image_broker.ANCHOR_KEY)
    assert masked.asset["reference_asset_id"] == anchor["id"]
    assert "non_rebreather_mask" in masked.asset["devices"]


def test_the_anchor_prompt_names_the_person_by_appearance_and_never_by_the_case(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    prompt = provider.calls[0][1]["prompt"]
    assert "man in his late sixties" in prompt and "deep brown skin" in prompt
    # The case never reaches the photograph: no condition, no finding the contract does not state.
    for word in ("glucose", "hypoglyc", "sepsis", "overdose", "insulin", "diabet", "opioid"):
        assert word not in prompt.lower()


# --- reuse and persistence --------------------------------------------------------------------------------
def test_a_saved_image_is_shown_again_without_any_call_even_after_a_restart(bank, tmp_path):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    calls = len(provider.calls)
    # A new process: nothing in memory, the same database.
    AccountStore.forget_schemas()
    image_bank.forget_cache()
    reopened = ImageBank(AccountStore(f"sqlite:///{tmp_path / 'bank.sqlite3'}", allow_sqlite=True))
    outcome = ask(reopened, provider, ARRIVAL)
    assert outcome.state == "ready"
    assert len(provider.calls) == calls
    assert reopened.blob(outcome.asset["display_sha256"]).startswith(b"RIFF")  # WebP for the browser


def test_the_browser_copy_is_webp_and_much_smaller_than_the_providers_png(bank):
    provider = Provider()
    _, ready = settle(bank, provider, ARRIVAL)
    master = bank.blob_facts(ready.asset["master_sha256"])
    display = bank.blob_facts(ready.asset["display_sha256"])
    assert master["content_type"] == "image/png" and display["content_type"] == "image/webp"
    assert (display["width"], display["height"]) == (master["width"], master["height"]) == (1536, 1024)


def test_the_same_bytes_are_stored_once(bank):
    raw = png("same")
    assert bank.put_blob(raw) == bank.put_blob(raw)
    with bank.accounts._transaction() as connection:
        count = bank._execute(connection, "SELECT COUNT(*) AS n FROM mrs_image_blobs").fetchone()["n"]
    assert count == 1


# --- one job per person and state -----------------------------------------------------------------------
def test_two_requests_for_the_same_person_and_state_make_one_job(bank):
    provider = Provider()
    provider.gate = threading.Event()
    first = ask(bank, provider, ARRIVAL)
    second = ask(bank, provider, ARRIVAL)
    assert first.state == second.state == "pending"
    provider.gate.set()
    settle(bank, provider, ARRIVAL)
    assert provider.kinds() == ["create", "screen", "edit", "screen"]


def test_two_states_asked_for_at_once_share_one_first_photograph(bank):
    provider = Provider()
    provider.gate = threading.Event()
    assert ask(bank, provider, ARRIVAL).stage == "ANCHOR"
    assert ask(bank, provider, MASKED).stage == "ANCHOR"     # joins the same anchor job
    provider.gate.set()
    settle(bank, provider, ARRIVAL)
    settle(bank, provider, MASKED)
    anchors = [a for a in bank.assets("V27") if a["role"] == "anchor"]
    assert len(anchors) == 1
    assert provider.kinds().count("create") == 1
    for contract in (ARRIVAL, MASKED):
        assert bank.usable_asset("V27", contract_key(contract))["reference_asset_id"] == anchors[0]["id"]


def test_a_job_running_in_another_process_is_waited_for_not_repeated(bank):
    provider = Provider()
    # Another process is drawing this person's first photograph.
    assert bank.claim("V27", image_broker.ANCHOR_KEY, "another-host:1:abc")
    outcome = ask(bank, provider, ARRIVAL)
    assert outcome.state == "pending" and outcome.elsewhere
    assert provider.calls == []
    bank.release("V27", image_broker.ANCHOR_KEY, "another-host:1:abc")
    settle(bank, provider, image_broker.ANCHOR_CONTRACT)
    calls = len(provider.calls)
    # And now another process is editing the state itself.
    assert bank.claim("V27", contract_key(ARRIVAL), "another-host:1:abc")
    outcome = ask(bank, provider, ARRIVAL)
    assert outcome.state == "pending" and outcome.elsewhere
    assert len(provider.calls) == calls


def test_a_claim_left_by_a_process_that_died_expires(bank):
    provider = Provider()
    assert bank.claim("V27", contract_key(ARRIVAL), "dead-host:1:abc", lease_seconds=-1)
    first, second = settle(bank, provider, ARRIVAL)
    assert second.state == "ready"


# --- money ------------------------------------------------------------------------------------------------
def test_every_call_is_reserved_before_it_is_sent_and_unused_reservations_are_given_back(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    ledger = bank.ledger(DEFAULT_BUDGET["id"])
    sent = sorted((row for row in ledger if row["status"] != "released"), key=lambda row: row["sent_order"])
    released = [row for row in ledger if row["status"] == "released"]
    assert [row["kind"] for row in sent] == ["create", "screen", "edit", "screen"]
    assert sorted(row["kind"] for row in released) == ["repair", "repair", "screen", "screen"]
    assert all(row["sent_at"] is not None for row in sent)
    summary = bank.budget_summary(dict(DEFAULT_BUDGET))
    assert summary["requests"] == 2 and summary["calls_sent"] == 4 and summary["in_flight"] == 0


def test_the_cost_comes_from_the_usage_the_provider_reports(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    create = next(row for row in bank.ledger(DEFAULT_BUDGET["id"]) if row["kind"] == "create")
    assert create["cost_basis"] == "provider_usage"
    # 700 text tokens at 5.00 + 406 output tokens at 32.00, per million.
    assert create["cost_micro"] == 700 * 5 + 406 * 32


def test_nothing_starts_when_the_worst_case_does_not_fit(bank):
    provider = Provider()
    small = {"id": "small-test-budget", "limit_micro": 300_000, "limit_requests": 30, "authorization": "test"}
    outcome = ask(bank, provider, ARRIVAL, budget=small)
    # An anchor and a state, each with its correction, cannot fit in US$0.30.
    assert outcome.state == "unavailable" and outcome.code == "BUDGET_DOLLARS"
    assert provider.calls == []
    assert bank.budget_summary(small)["committed"] == 0


def test_the_request_limit_counts_every_image_request_including_retries(bank):
    provider = Provider(failures={"create": [ProviderError(503)]})
    budget = {"id": "requests-test-budget", "limit_micro": 10 * MICRO, "limit_requests": 30, "authorization": "t"}
    settle(bank, provider, ARRIVAL, budget=budget)
    rows = sorted((row for row in bank.ledger(budget["id"]) if row["status"] != "released"),
                  key=lambda row: row["sent_order"])
    creates = [row for row in rows if row["kind"] == "create"]
    assert [row["status"] for row in creates] == ["failed", "succeeded"]
    assert creates[1]["retry_of"] == creates[0]["id"]
    summary = bank.budget_summary(budget)
    assert summary["requests"] == 3 and summary["retries"] == 1


def test_a_timeout_is_not_retried_and_stays_charged(bank):
    import httpx
    from openai import APITimeoutError
    provider = Provider(failures={"create": [APITimeoutError(request=httpx.Request("POST", "https://x"))]})
    first, second = settle(bank, provider, ARRIVAL)
    assert second.state == "failed" and second.code == "TIMEOUT"
    creates = [row for row in bank.ledger(DEFAULT_BUDGET["id"]) if row["kind"] == "create"]
    assert len(creates) == 1 and creates[0]["status"] == "failed"
    assert creates[0]["cost_basis"] == "estimate"
    assert bank.budget_summary(dict(DEFAULT_BUDGET))["committed"] == creates[0]["reserved_micro"]


def test_a_refusal_or_an_authentication_failure_is_never_retried(bank):
    provider = Provider(failures={"create": [ProviderError(401)]})
    settle(bank, provider, ARRIVAL)
    assert provider.kinds() == ["create"]


def test_the_last_request_is_the_last(bank):
    provider = Provider()
    budget = {"id": "tight-requests", "limit_micro": 10 * MICRO, "limit_requests": 1, "authorization": "t"}
    # A picture reserves two image requests, itself and its possible correction: one does not fit.
    assert ask(bank, provider, ARRIVAL, budget=budget).code == "BUDGET_REQUESTS"
    assert provider.calls == []
    roomy = {"id": "roomier-requests", "limit_micro": 10 * MICRO, "limit_requests": 3, "authorization": "t"}
    _, first = settle(bank, provider, image_broker.ANCHOR_CONTRACT, budget=roomy)
    assert first.state == "ready"                       # one request used, its correction given back
    _, state = settle(bank, provider, ARRIVAL, budget=roomy)
    assert state.state == "ready"                       # 1 + 2 reserved fit in 3
    assert bank.budget_summary(roomy)["requests"] == 2
    assert ask(bank, provider, MASKED, budget=roomy).code == "BUDGET_REQUESTS"   # 2 + 2 do not


def test_two_workers_never_take_the_last_dollar_twice(bank):
    budget = {"id": "race-budget", "limit_micro": 2 * image_broker.ceiling(IMAGE_MODEL, "edit"),
              "limit_requests": 30, "authorization": "t"}
    item = [("edit", IMAGE_MODEL, image_broker.ceiling(IMAGE_MODEL, "edit"), True, None)]
    results = []

    def reserve():
        try:
            results.append(bank.reserve(budget, item, job_id=uuid.uuid4().hex, identity_id="V27",
                                        state_key="k", requested_by="race"))
        except BudgetRefused as refusal:
            results.append(refusal.reason)

    threads = [threading.Thread(target=reserve) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(1 for result in results if isinstance(result, list)) == 2
    assert bank.budget_summary(budget)["committed"] <= budget["limit_micro"]


def test_a_restart_does_not_reset_the_budget(bank, tmp_path):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    spent = bank.budget_summary(dict(DEFAULT_BUDGET))
    AccountStore.forget_schemas()
    reopened = ImageBank(AccountStore(f"sqlite:///{tmp_path / 'bank.sqlite3'}", allow_sqlite=True))
    assert reopened.budget_summary(dict(DEFAULT_BUDGET)) == spent


def test_a_budget_identifier_cannot_change_its_limits(bank):
    bank.ensure_budget(dict(DEFAULT_BUDGET))
    with pytest.raises(ValueError):
        bank.ensure_budget({**DEFAULT_BUDGET, "limit_micro": 50 * MICRO})


def test_a_model_without_a_verified_price_is_not_used(bank):
    provider = Provider()
    outcome = ask(bank, provider, ARRIVAL, model="gpt-image-2")
    assert outcome.state == "unavailable" and outcome.code == "PRICE"
    assert provider.calls == []


# --- the screen: accepted, corrected once, or kept for another screen ------------------------------------
def test_a_definite_mismatch_is_kept_as_rejected_and_corrected_once(bank):
    provider = Provider(screens=[passing(), mismatch("expression"), passing()])
    _, ready = settle(bank, provider, ARRIVAL)
    assert provider.kinds() == ["create", "screen", "edit", "screen", "repair", "screen"]
    assert ready.state == "ready" and ready.asset["generation"]["repaired"]
    states = bank.assets("V27")
    rejected = [a for a in states if a["screen"] == "rejected"]
    assert len(rejected) == 1 and rejected[0]["excluded"]
    assert rejected[0]["screen_details"]["failed_checks"] == ["expression"]
    assert ready.asset["screen_details"]["corrects"] == rejected[0]["id"]
    # The correction was sent the rejected candidate and the approved anchor, in that order.
    repair = provider.calls[4][1]
    assert [image.name.split(".")[0] for image in repair["image"]] == ["rejected-candidate", "approved-original"]


def test_a_second_mismatch_fails_without_a_loop(bank):
    provider = Provider(screens=[passing(), mismatch(), mismatch()])
    _, second = settle(bank, provider, ARRIVAL)
    assert second.state == "failed" and second.code == "MISMATCH"
    assert provider.kinds().count("repair") == 1


def test_a_screen_that_could_not_run_keeps_the_picture_and_screens_it_again_without_paying_for_it_twice(bank):
    provider = Provider(failures={"screen": [None]})  # placeholder, replaced below
    provider.failures = {"screen": [ProviderError(400)]}   # a screen request refused: no verdict
    provider.screens = []
    first = ask(bank, provider, image_broker.ANCHOR_CONTRACT)
    image_broker.wait(30)
    kept = [a for a in bank.assets("V27") if a["screen"] == "not_screened"]
    assert len(kept) == 1
    assert ask(bank, provider, image_broker.ANCHOR_CONTRACT).state == "failed"   # cooling down
    retried = ask(bank, provider, image_broker.ANCHOR_CONTRACT, force=True)
    image_broker.wait(30)
    assert provider.kinds() == ["create", "screen", "screen"]
    assert ask(bank, provider, image_broker.ANCHOR_CONTRACT).state == "ready"
    assert bank.asset(kept[0]["id"])["screen"] == "accepted"


def test_a_failed_state_is_not_asked_for_again_automatically_until_its_pause_ends(bank, monkeypatch):
    provider = Provider(failures={"create": [ProviderError(503), ProviderError(503)]})
    settle(bank, provider, ARRIVAL)
    assert ask(bank, provider, ARRIVAL).state == "failed"
    calls = len(provider.calls)
    later = time.time() + image_broker.COOLDOWN["PROVIDER"] + 1
    monkeypatch.setattr(image_broker.time, "time", lambda: later)
    assert ask(bank, provider, ARRIVAL).state == "pending"
    image_broker.wait(30)
    assert len(provider.calls) > calls


def test_a_person_without_permission_or_a_key_is_never_charged(bank):
    provider = Provider()
    assert ask(bank, provider, ARRIVAL, allowed=False).code == "NOT_ALLOWED"
    outcome = image_broker.request(bank, identity("V27"), ARRIVAL, api_key="", allowed=True,
                                   image_model=IMAGE_MODEL, review_model=REVIEW_MODEL, requested_by="t",
                                   budget=dict(DEFAULT_BUDGET))
    assert outcome.code == "CONFIG"
    assert provider.calls == [] and bank.ledger(DEFAULT_BUDGET["id"]) == []


def test_a_late_result_is_kept_for_its_own_state(bank):
    provider = Provider()
    settle(bank, provider, image_broker.ANCHOR_CONTRACT)
    provider.gate = threading.Event()
    ask(bank, provider, ARRIVAL)
    # The patient moved on before the picture came back.
    assert ask(bank, provider, MASKED).state == "pending"
    provider.gate.set()
    image_broker.wait(30)
    arrival = bank.usable_asset("V27", contract_key(ARRIVAL))
    assert arrival is not None and arrival["contract"] == ARRIVAL
    assert "non_rebreather_mask" not in arrival["devices"]


def test_devices_are_those_of_the_contract_and_nothing_else():
    assert image_broker.devices_for(ARRIVAL) == ["ecg_electrodes", "blood_pressure_cuff", "pulse_oximeter"]
    assert image_broker.devices_for(MASKED)[-1] == "non_rebreather_mask"
    assert image_broker.devices_for({**ARRIVAL, "respiratory_support": "invasive ventilation"})[-1] == "endotracheal_tube"


# --- continuity: one anchor per person at a time ------------------------------------------------------------
def test_withdrawing_an_anchor_takes_its_states_along_and_the_next_state_starts_from_a_new_anchor(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    old_anchor = bank.current_anchor("V27")
    old_state = bank.usable_asset("V27", contract_key(ARRIVAL))
    withdrawn = bank.withdraw(old_anchor["id"], "Superseded in a test", by="test")
    assert set(withdrawn) == {old_anchor["id"], old_state["id"]}
    assert bank.current_anchor("V27") is None
    assert bank.usable_asset("V27", contract_key(ARRIVAL)) is None
    _, again = settle(bank, provider, ARRIVAL)
    new_anchor = bank.current_anchor("V27")
    assert new_anchor["id"] != old_anchor["id"]
    assert again.asset["reference_asset_id"] == new_anchor["id"]
    assert "Superseded in a test (test, " in bank.asset(old_state["id"])["exclusion_reason"]


def test_a_state_edited_from_another_anchor_is_never_shown_with_this_one(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    state = bank.usable_asset("V27", contract_key(ARRIVAL))
    # A newer anchor of the same person, made some other way.
    raw = png("another anchor")
    sha = bank.put_blob(raw)
    bank.add_asset(identity_id="V27", identity_version="1.0", role="anchor", contract=image_broker.ANCHOR_CONTRACT,
                   devices=image_broker.devices_for(image_broker.ANCHOR_CONTRACT), display_sha256=sha,
                   master_sha256=sha, generation={}, screen="accepted", created_at=int(time.time()) + 60)
    assert bank.current_anchor("V27")["id"] != state["reference_asset_id"]
    assert bank.usable_asset("V27", contract_key(ARRIVAL)) is None


def test_the_bank_asks_for_a_room_without_treatment_and_a_mental_status_that_can_be_seen(bank):
    provider = Provider()
    settle(bank, provider, ARRIVAL)
    create, edit = provider.calls[0][1]["prompt"], provider.calls[2][1]["prompt"]
    assert "No intravenous bags, IV poles, infusion lines" in create
    assert "No intravenous bags, IV poles, infusion lines" in edit
    assert "eyelids clearly lowered about halfway" in edit        # the state asked for is drowsy
    anchor_edit = image_broker.edit_prompt(image_broker.ANCHOR_CONTRACT)
    assert "eyelids clearly lowered" not in anchor_edit           # alert: nothing to add


def test_an_oxygen_interface_is_asked_for_connected_to_the_wall(bank):
    provider = Provider()
    settle(bank, provider, MASKED)
    edit = next(kwargs for kind, kwargs in provider.calls if kind == "edit")["prompt"]
    assert "oxygen tubing must be clearly visible" in edit and "a mask that is not connected delivers nothing" in edit
    assert "oxygen tubing must be clearly visible" not in image_broker.edit_prompt(ARRIVAL)


def test_marked_sweat_is_asked_for_as_texture_and_light_on_any_skin_tone():
    marked = {**ARRIVAL, "diaphoresis": "marked"}
    prompt = image_broker.edit_prompt(marked)
    assert "visible on any skin tone as texture and light, never as a change of skin color" in prompt
    assert "texture and light" not in image_broker.edit_prompt({**ARRIVAL, "diaphoresis": "mild"})
    assert "No intravenous cannula, catheter, dressing or tubing on the patient's arms" in prompt
