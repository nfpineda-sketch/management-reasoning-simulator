"""One paid request per person and state, reserved before it is sent (2026-09-26).

The broker is the only code that asks the provider for a patient photograph
when the image bank is in use. What it guarantees:

* **One job per person and state.** In this process a second request for the
  same identity and visible state joins the running job; across processes the
  bank's claim does the same, with a lease so that a job which died does not
  block the state forever.
* **Nothing is sent that the budget cannot cover.** A job reserves the worst
  case of every call it may make -- the image, the screen, the one correction
  and its screen -- before the first one leaves, and gives back what it did
  not use. A retry is reserved again; a failure keeps its reservation charged.
* **Retries by kind of failure.** A busy or unreachable provider gets one more
  try after a pause. A timeout does not: the request may have been processed
  and billed. A refusal, a quota or an authentication failure is not retried.
  A failed state is not requested again automatically for a while (``COOLDOWN``);
  a person may still ask again, and pay again.
* **Every result is kept.** An accepted image becomes an asset of its identity
  in its state, whether or not anyone is still looking at that state -- a late
  answer is saved for the next time, never shown for another state. A rejected
  candidate is kept too, excluded, with the screen's reasons; a candidate whose
  screen could not run is kept unscreened and screened again next time instead
  of being paid for twice.
* **Identity.** Every state of a person is an edit of that person's anchor: one
  photograph in a neutral state (``ANCHOR_CONTRACT``), made first and only once.
  Repeating a description or a seed is not relied on to keep a face.

The screen is the same one the room always used (``image_consistency``), with
the same single correction after a definite mismatch; no check is relaxed to
make a picture appear. Nothing here advances the clinical clock or waits on the
page: jobs run in background threads and the room polls.
"""
from __future__ import annotations

import base64
import os
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from io import BytesIO

from image_bank import SCREEN_EXCLUSION, BudgetRefused, contract_key, drawn_contract
from image_pricing import IMAGE_REQUESTS, PriceUnknown, ceiling, cost_from_usage, usage_record
from scene_errors import SceneImageError, provider_image_error

BROKER_VERSION = "1.0"
IMAGE_SIZE = "1536x1024"
IMAGE_QUALITY = "low"

from image_bank import ANCHOR_CONTRACT, ANCHOR_KEY  # noqa: E402  (one definition, used by the bank)

# What the bank adds to the room's prompts (pilot, batch 1, 2026-09-26). Both
# candidates of the first anchor had IV bags and lines hanging beside the bed:
# a resident could read them as an infusion that was never ordered. And the
# first "drowsy" edit kept the anchor's open, camera-directed gaze, because the
# edit brief asks for conservative changes. Neither addition names a condition,
# and neither relaxes the screen: the same targets are checked afterwards.
# bank-1.4 (faculty decision 3): equipment hanging unconnected on the wall or
# beside the bed is not a treatment for the screen either; a line that reaches
# the patient still is. bank-1.5: no wristband beside the finger clip, and a
# marked discomfort or effort drawn so that it shows.
PROMPT_VERSION = "bank-1.5"
ROOM_WITHOUT_TREATMENT = (
    " No intravenous bags, IV poles, infusion lines, syringes, pumps or drains anywhere in the room: "
    "nothing in the bed space may suggest a treatment beyond the listed monitoring and support."
    # Batch 3: an anchor came with a cannula and its line taped to the wrist.
    " No intravenous cannula, catheter, dressing or tubing on the patient's arms or hands: the only things "
    "attached to the patient are the listed monitors and support."
    # Second authorization, batches 1-3: 10 of 10 rejections were "active treatment"
    # with a clean wall, beside an identification band next to the finger clip.
    " No wristband, bracelet, watch or tape on either wrist; the pulse oximeter is only a small clip on one "
    "fingertip with a thin cable. Remove any the reference shows.")
# Batch 3: on dark brown skin, two candidates of "marked" sweating showed dry skin.
# Sweat is texture and light, visible on every skin tone; it is not a colour.
DIAPHORESIS_VISIBLE = {
    "marked": ("The marked sweating must be visible on any skin tone as texture and light, never as a change "
               "of skin color: distinct beads of sweat on the forehead, temples and upper lip, and a wet sheen "
               "that catches the light, in proportion, without dripping or theatrical exaggeration."),
}
# Second authorization: the screen accepted "markedly uncomfortable" and "markedly
# increased" states drawn with a calm face and a relaxed posture. Neither names a
# condition; the screen checks the same targets afterwards.
EXPRESSION_VISIBLE = {
    "markedly uncomfortable": ("The marked discomfort must be recognizable at normal viewing size: brow "
                               "drawn together, eyes tight, a strained mouth. Not a calm or neutral face."),
}
EFFORT_VISIBLE = {
    "markedly increased": ("The breathing effort must be visible in the posture: sitting more upright, "
                           "shoulders raised, neck muscles tense, lips parted."),
    "severe": ("The breathing effort must be visible in the posture: sitting upright and leaning slightly "
               "forward, shoulders raised, neck muscles tense, mouth open."),
}
MENTAL_STATUS_VISIBLE = {
    "drowsy": ("The drowsiness must be recognizable at normal viewing size, in proportion: eyelids "
               "clearly lowered about halfway and a gaze that drifts away from the camera instead of "
               "meeting it. Do not keep the reference's open, camera-directed gaze."),
    "obtunded": ("The obtundation must be recognizable at normal viewing size: eyes mostly closed, the "
                 "head resting passively and slightly turned on the pillow, no engagement with the camera."),
    "unresponsive": ("Eyes closed, head resting passively, no engagement with the camera; the reference's "
                     "open eyes must not remain."),
    "sedated": "Eyes closed and the face relaxed; the reference's open eyes must not remain.",
}

MONITORS = ("ecg_electrodes", "blood_pressure_cuff", "pulse_oximeter")

# Contracts the pilot could not draw: a request for them pays for a rejection
# (faculty, 2026-09-26: avoid spending that ends in a rejected image). The room
# shows its neutral view and says why; a photograph a person approved over the
# automated screen is still shown (decision 5), and the case is never changed.
def known_to_fail(identity_record, contract):
    """Why this person in this state is not requested, or None."""
    if contract.get("respiratory_support") == "non-rebreather mask":
        return "The automated screen did not recognise the reservoir mask in 10 of 10 candidates."
    if contract.get("diaphoresis") == "marked" and int(identity_record.get("skin_tone") or 0) >= 5:
        return "Marked sweat was not drawn on dark skin in 4 of 4 candidates (faculty decision 6)."
    return None


TRANSIENT = frozenset({"RATE", "PROVIDER", "CONNECTION"})
RETRY_PAUSE_SECONDS = 3.0
MINUTE, HOUR = 60, 3600
COOLDOWN = {
    "RATE": 10 * MINUTE, "PROVIDER": 10 * MINUTE, "CONNECTION": 10 * MINUTE, "TIMEOUT": 15 * MINUTE,
    "INCOMPLETE": HOUR, "INVALID_IMAGE": HOUR, "INTERNAL": HOUR,
    "UNCERTAIN": 6 * HOUR, "INVALID_RESPONSE": 6 * HOUR, "RESULT_JSON": 6 * HOUR, "RESULT_SCHEMA": 6 * HOUR,
    "RESULT_EVIDENCE": 6 * HOUR, "RESULT_OBSERVATIONS": 6 * HOUR,
    "MISMATCH": 24 * HOUR, "REFUSED": 24 * HOUR, "CONTRACT": 24 * HOUR,
    "AUTH": 24 * HOUR, "ACCESS": 24 * HOUR, "QUOTA": 24 * HOUR, "MODEL": 24 * HOUR,
    "REQUEST": 24 * HOUR, "FORMAT": 24 * HOUR, "CONFIG": 24 * HOUR, "BUDGET": 0,
}

OWNER = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="image-bank")
_LOCK = threading.Lock()
_INFLIGHT = {}


def devices_for(contract):
    """What the photograph shows attached to the patient: the monitors, and the executed support."""
    from visual_review_contract import RESPIRATORY
    support = contract.get("respiratory_support")
    return list(MONITORS) + ([RESPIRATORY[support]] if support in RESPIRATORY else [])


@dataclass
class Outcome:
    """What the room can know about one person in one state, right now."""
    state: str                       # ready | pending | failed | unavailable
    asset: dict | None = None
    code: str = ""
    stage: str = ""
    started: float | None = None     # time.monotonic() of the running job, for the elapsed label
    elsewhere: bool = False          # the job runs in another process
    details: dict = field(default_factory=dict)


class JobFailure(Exception):
    def __init__(self, code, stage, asset_id=None, failed_checks=()):
        self.code, self.stage, self.asset_id = code, stage, asset_id
        self.failed_checks = tuple(failed_checks)
        super().__init__(f"{stage}:{code}")


class _Job:
    def __init__(self, future, started):
        self.future = future
        self.started = started


def _inflight_key(bank, identity_id, state_key):
    return (bank.key, identity_id, state_key)


def running(bank, identity_id, state_key):
    with _LOCK:
        job = _INFLIGHT.get(_inflight_key(bank, identity_id, state_key))
    return job if job is not None and not job.future.done() else None


def wait(timeout=30):
    """Wait for every job this process started. For tests and the command-line tool."""
    deadline = time.monotonic() + timeout
    while True:
        with _LOCK:
            futures = [job.future for job in _INFLIGHT.values()]
        if not futures:
            return
        for future in futures:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Image jobs are still running.")
            try:
                future.result(timeout=remaining)
            except Exception:
                pass


def _plan(bank, identity_id, state_key, image_model, review_model):
    """The worst case of the calls one job may make: its picture, the screen, one correction, its screen."""
    if _unscreened(bank, identity_id, state_key) is not None:
        # A saved candidate whose screen never finished: screen it, and correct once.
        return [("screen", review_model), ("repair", image_model), ("screen", review_model)]
    first = "create" if state_key == ANCHOR_KEY else "edit"
    return [(first, image_model), ("screen", review_model), ("repair", image_model), ("screen", review_model)]


def _unscreened(bank, identity_id, state_key):
    """A kept candidate still waiting for a screen: an anchor, or a state of the current anchor."""
    anchor = None if state_key == ANCHOR_KEY else bank.current_anchor(identity_id)
    for asset in bank.assets(identity_id):
        if (asset["state_key"] == state_key and asset["screen"] == "not_screened"
                and asset["technical_check"] == "passed" and not asset["excluded"]
                and (state_key == ANCHOR_KEY or (anchor is not None and asset["reference_asset_id"] == anchor["id"]))):
            return asset
    return None


def cooling_down(bank, identity_id, state_key, now=None):
    """The last failure of this person in this state, while it still holds automatic requests back."""
    last = bank.last_job(identity_id, state_key)
    if last is None or last["outcome"] == "stored":
        return None
    pause = COOLDOWN.get(last["code"], HOUR)
    now = time.time() if now is None else now
    return last if now - int(last["finished_at"]) < pause else None


def request(bank, identity_record, contract, *, api_key, allowed, image_model, review_model,
            requested_by, budget, client_factory=None, force=False):
    """Ready, pending, failed or unavailable -- and start the job when it is allowed to start."""
    identity_id = identity_record["id"]
    contract = drawn_contract(contract)
    state_key = contract_key(contract)
    asset = bank.usable_asset(identity_id, state_key)
    if asset is not None:
        return Outcome("ready", asset=asset)
    if known_to_fail(identity_record, contract):
        return Outcome("unavailable", code="UNRENDERABLE")
    anchor_first = state_key != ANCHOR_KEY and bank.current_anchor(identity_id) is None
    if anchor_first:
        # First the person's reference photograph, as a job of its own: two states
        # asked for at once must not each draw a different first photograph.
        state_key, contract = ANCHOR_KEY, dict(ANCHOR_CONTRACT)
    job = running(bank, identity_id, state_key)
    if job is not None:
        return Outcome("pending", started=job.started, stage="ANCHOR" if anchor_first else "QUEUED")
    claim = bank.claimed(identity_id, state_key)
    if claim is not None and claim["owner"] != OWNER:
        return Outcome("pending", elsewhere=True, stage="ELSEWHERE")
    if not allowed:
        return Outcome("unavailable", code="NOT_ALLOWED")
    if not api_key and client_factory is None:
        return Outcome("unavailable", code="CONFIG")
    if not force:
        failure = cooling_down(bank, identity_id, state_key)
        if failure is not None:
            return Outcome("failed", code=failure["code"], stage=failure["stage"],
                           details={"finished_at": failure["finished_at"]})
    job_id = uuid.uuid4().hex
    try:
        items = []
        for kind, model in _plan(bank, identity_id, state_key, image_model, review_model):
            items.append((kind, model, ceiling(model, kind), kind in IMAGE_REQUESTS, None))
        entries = bank.reserve(budget, items, job_id=job_id, identity_id=identity_id, state_key=state_key,
                               requested_by=requested_by)
    except PriceUnknown:
        return Outcome("unavailable", code="PRICE")
    except BudgetRefused as refusal:
        return Outcome("unavailable", code="BUDGET_" + refusal.reason.upper(), details=refusal.summary)
    if not bank.claim(identity_id, state_key, OWNER):
        bank.release_reservations(entries)
        return Outcome("pending", elsewhere=True, stage="ELSEWHERE")
    started = time.monotonic()
    key = _inflight_key(bank, identity_id, state_key)
    with _LOCK:
        if key in _INFLIGHT and not _INFLIGHT[key].future.done():
            bank.release_reservations(entries)
            return Outcome("pending", started=_INFLIGHT[key].started, stage="QUEUED")
        ledger = _Ledger(bank, budget, job_id, identity_id, state_key, requested_by,
                         [(entry, item[0], item[1]) for entry, item in zip(entries, items)])
        future = _POOL.submit(_run, bank, identity_record, dict(contract), ledger, api_key, image_model,
                              review_model, requested_by, client_factory, job_id)
        _INFLIGHT[key] = _Job(future, started)
    return Outcome("pending", started=started, stage="ANCHOR" if anchor_first else "QUEUED")


def outcome_of(bank, identity_id, state_key):
    """A finished job's asset, or None. For a room that watched its own job end."""
    return bank.usable_asset(identity_id, state_key)


# --- the job --------------------------------------------------------------------------------------
class _Ledger:
    """The reservations of one job, spent one call at a time."""

    def __init__(self, bank, budget, job_id, identity_id, state_key, requested_by, reserved):
        self.bank, self.budget, self.job_id = bank, budget, job_id
        self.identity_id, self.state_key, self.requested_by = identity_id, state_key, requested_by
        self.reserved = list(reserved)       # (entry id, kind, model), not yet sent
        self.used = []

    def take(self, kind, model, retry_of=None):
        if retry_of is None:
            for index, (entry, entry_kind, entry_model) in enumerate(self.reserved):
                if entry_kind == kind and entry_model == model:
                    del self.reserved[index]
                    self.used.append(entry)
                    return entry
        entries = self.bank.reserve(self.budget, [(kind, model, ceiling(model, kind), kind in IMAGE_REQUESTS,
                                                   retry_of)],
                                    job_id=self.job_id, identity_id=self.identity_id, state_key=self.state_key,
                                    requested_by=self.requested_by)
        self.used.append(entries[0])
        return entries[0]

    def release_unused(self):
        self.bank.release_reservations([entry for entry, _, _ in self.reserved])
        self.reserved = []


class _Metered:
    """The provider client, with every call reserved, marked as sent and settled in the ledger."""

    def __init__(self, inner, ledger, pause=RETRY_PAUSE_SECONDS):
        self._inner, self._ledger, self._pause = inner, ledger, pause
        outer = self

        class _Images:
            def generate(self, **kwargs):
                return outer._call("create", kwargs["model"], lambda: outer._inner.images.generate(**kwargs))

            def edit(self, **kwargs):
                kind = kwargs.pop("_kind", "edit")
                return outer._call(kind, kwargs["model"], lambda: outer._inner.images.edit(**kwargs))

        class _Responses:
            def create(self, **kwargs):
                return outer._call("screen", kwargs["model"], lambda: outer._inner.responses.create(**kwargs))

        self.images = _Images()
        self.responses = _Responses()

    def _call(self, kind, model, invoke):
        stage = {"create": "CREATE", "edit": "EDIT", "repair": "REPAIR", "screen": "SCREEN"}[kind]
        entry = self._ledger.take(kind, model)
        retried = False
        while True:
            self._ledger.bank.mark_sent(entry)
            try:
                result = invoke()
            except Exception as error:
                code = error.code if isinstance(error, SceneImageError) else provider_image_error(error, stage).code
                self._ledger.bank.settle(entry, "failed", error_code=code)
                if code not in TRANSIENT or retried:
                    raise
                try:
                    # The retry is reserved before the pause; without room for it the
                    # provider's failure stands as it is.
                    entry = self._ledger.take(kind, model, retry_of=entry)
                except (BudgetRefused, PriceUnknown):
                    raise error from None
                retried = True
                time.sleep(self._pause)
                continue
            usage = usage_record(getattr(result, "usage", None))
            cost = cost_from_usage(model, kind, usage) if usage is not None else None
            self._ledger.bank.settle(entry, "succeeded", usage=usage, cost_micro=cost)
            return result


def _client(api_key, client_factory):
    if client_factory is not None:
        return client_factory()
    from openai import OpenAI
    return OpenAI(api_key=api_key, timeout=120, max_retries=0)


def _png(result, stage):
    from patient_appearance import _validated_image
    try:
        raw, _ = _validated_image(result.data[0].b64_json, output=True)
    except (ValueError, AttributeError, IndexError, TypeError):
        raise JobFailure("INVALID_IMAGE", stage) from None
    return raw


def _stream(raw, name):
    from PIL import Image
    with Image.open(BytesIO(raw)) as image:
        extension = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[image.format]
    stream = BytesIO(raw)
    stream.name = f"{name}.{extension}"
    return stream


def _edit_request(model, images, prompt, kind):
    request = dict(model=model, image=images if len(images) > 1 else images[0], prompt=prompt,
                   size=IMAGE_SIZE, quality=IMAGE_QUALITY, output_format="png", n=1, _kind=kind)
    # GPT Image 2 inputs are already high fidelity and reject this parameter.
    if model in {"gpt-image-1.5", "gpt-image-1"}:
        request["input_fidelity"] = "high"
    return request


# Batch 2: both candidates of the non-rebreather state showed the mask and its
# reservoir with no oxygen tubing at all, and were rejected. An interface that
# is not connected delivers nothing; the executed support must look connected.
SUPPORT_VISIBLE = {
    "nasal cannula": ("The oxygen tubing must be clearly visible, running from the cannula over the ears "
                      "and down to the oxygen flowmeter on the wall outlet."),
    "simple mask": ("The oxygen tubing must be clearly visible, running from the mask's connector to the "
                    "oxygen flowmeter on the wall outlet."),
    "non-rebreather mask": ("The reservoir bag hangs below the mask, partly inflated, and the oxygen tubing "
                            "must be clearly visible, running from the mask's connector to the oxygen "
                            "flowmeter on the wall outlet: a mask that is not connected delivers nothing."),
}


def edit_prompt(contract):
    """The room's edit brief, with the bank's clarifications."""
    from patient_appearance import edit_prompt_for
    extra = [MENTAL_STATUS_VISIBLE.get(contract.get("mental_status"), ""),
             EXPRESSION_VISIBLE.get(contract.get("expression"), ""),
             EFFORT_VISIBLE.get(contract.get("work_of_breathing"), ""),
             DIAPHORESIS_VISIBLE.get(contract.get("diaphoresis"), ""),
             SUPPORT_VISIBLE.get(contract.get("respiratory_support"), "")]
    return edit_prompt_for(contract) + "".join(" " + item for item in extra if item) + ROOM_WITHOUT_TREATMENT


def display_bytes(raw):
    """The copy the room sends to a browser: WebP, a tenth of the provider's PNG, same pixels size."""
    from PIL import Image
    with Image.open(BytesIO(raw)) as image:
        output = BytesIO()
        image.convert("RGB").save(output, format="WEBP", quality=82, method=4)
    return output.getvalue()


def _screen(client, candidate, contract, review_model, reference):
    from image_consistency import inspect_image
    return inspect_image(base64.b64encode(candidate).decode("ascii"), contract, None, model=review_model,
                         reference_b64=base64.b64encode(reference).decode("ascii") if reference else None,
                         client=client)


def _store(bank, identity_record, contract, role, raw, *, screen, details, reference, generation):
    from image_identities import IDENTITIES_VERSION
    master = bank.put_blob(raw)
    display = bank.put_blob(display_bytes(raw))
    return bank.add_asset(identity_id=identity_record["id"], identity_version=IDENTITIES_VERSION, role=role,
                          contract=contract, devices=devices_for(contract), display_sha256=display,
                          master_sha256=master, reference_asset_id=reference["id"] if reference else None,
                          generation=generation, screen=screen, screen_details=details,
                          excluded=screen == "rejected",
                          exclusion_reason=SCREEN_EXCLUSION if screen == "rejected" else "")


def _generation(identity_record, image_model, review_model, job_id, requested_by, stage, repaired=False):
    from clinical_scene import SCENE_RENDER_VERSION
    from image_identities import IDENTITIES_VERSION
    from patient_appearance import APPEARANCE_VERSION
    from scene_pipeline import SCENE_PIPELINE_VERSION
    return {"model": image_model, "review_model": review_model, "size": IMAGE_SIZE, "quality": IMAGE_QUALITY,
            "output_format": "png", "input_fidelity": "high" if image_model in {"gpt-image-1.5", "gpt-image-1"} else None,
            "stage": stage, "repaired": repaired, "job_id": job_id, "requested_by": requested_by,
            "versions": {"broker": BROKER_VERSION, "prompt": PROMPT_VERSION, "scene_render": SCENE_RENDER_VERSION,
                         "appearance": APPEARANCE_VERSION, "pipeline": SCENE_PIPELINE_VERSION,
                         "identities": IDENTITIES_VERSION},
            "identity": identity_record["id"]}


NO_VERDICT = frozenset({"provider_unavailable", "invalid_response", "uncertain"})


def _make(bank, client, identity_record, contract, role, reference, image_model, review_model, job_id,
          requested_by):
    """One photograph of this person in this state: made, screened, corrected once, stored.

    Three screen outcomes are kept apart. Accepted: stored and usable. No
    verdict (the reviewer failed, answered unreadably or could not tell): the
    picture is kept unscreened and screened again next time, never paid for
    twice. A definite mismatch: the candidate is kept as rejected and the one
    correction is made; its result is screened like any other picture.
    """
    from clinical_scene import scene_prompt_for
    from image_consistency import ImageConsistencyError
    from image_identities import person_phrase
    from scene_repair import repair_prompt_for

    reference_raw = None
    if reference is not None:
        reference_raw = bank.blob(reference.get("master_sha256") or reference["display_sha256"])
        if reference_raw is None:
            raise JobFailure("INTERNAL", "EDIT")
    stage = "CREATE" if reference is None else "EDIT"
    generation = _generation(identity_record, image_model, review_model, job_id, requested_by, stage)
    pending = _unscreened(bank, identity_record["id"], contract_key(contract))
    try:
        if pending is not None:
            raw = bank.blob(pending.get("master_sha256") or pending["display_sha256"])
            if raw is None:
                raise JobFailure("INTERNAL", "SCREEN")
            stage = "SCREEN"
        elif reference is None:
            result = client.images.generate(
                model=image_model,
                prompt=scene_prompt_for(person_phrase(identity_record), contract) + ROOM_WITHOUT_TREATMENT,
                size=IMAGE_SIZE, quality=IMAGE_QUALITY, output_format="png", n=1)
            raw = _png(result, stage)
        else:
            result = client.images.edit(**_edit_request(image_model, [_stream(reference_raw, "anchor")],
                                                        edit_prompt(contract), "edit"))
            raw = _png(result, stage)
    except (JobFailure, BudgetRefused, PriceUnknown):
        raise
    except Exception as error:
        raise JobFailure(provider_image_error(error, stage).code, stage) from None

    def keep(candidate, screen, details, repaired=False):
        if pending is not None and candidate is raw:
            bank.update_screen(pending["id"], screen, details)
            return bank.asset(pending["id"])
        return _store(bank, identity_record, contract, role, candidate, screen=screen, details=details,
                      reference=reference, generation={**generation, "repaired": repaired})

    def screened(candidate, repaired):
        """Accepted -> the stored asset. No verdict or mismatch -> an ImageConsistencyError."""
        result = _screen(client, candidate, contract, review_model, reference_raw)
        limitations = [item for item in result.get("limitations", ())
                       if item in ("mild_skin_moisture", "breathing_effort", "mild_skin_color")]
        return keep(candidate, "accepted_with_limitations" if limitations else "accepted",
                    {"limitations": limitations, "uncertain_checks": list(result.get("uncertain_checks", []))},
                    repaired)

    try:
        return screened(raw, False)
    except (BudgetRefused, PriceUnknown):
        raise
    except ImageConsistencyError as failure:
        if failure.reason_code in NO_VERDICT:
            kept = keep(raw, "not_screened", {"last_screen": failure.code,
                                              "failed_checks": list(failure.failed_checks)})
            raise JobFailure(failure.code, "SCREEN", kept["id"], failure.failed_checks) from None
        if failure.reason_code != "mismatch" or not failure.failed_checks:
            raise JobFailure(failure.code, "SCREEN") from None
        checks = failure.failed_checks
        evidence = [dict(item) for item in getattr(failure, "conflict_evidence", ())]
    rejected = keep(raw, "rejected", {"failed_checks": list(checks), "evidence": evidence})
    try:
        clarifications = [DIAPHORESIS_VISIBLE.get(contract.get("diaphoresis"), "") if "diaphoresis" in checks else "",
                          SUPPORT_VISIBLE.get(contract.get("respiratory_support"), "")]
        prompt = (repair_prompt_for(person_phrase(identity_record), contract, checks,
                                    has_reference=reference_raw is not None)
                  + "".join(" " + item for item in clarifications if item) + ROOM_WITHOUT_TREATMENT)
        images = [_stream(raw, "rejected-candidate")] + (
            [_stream(reference_raw, "approved-original")] if reference_raw is not None else [])
        result = client.images.edit(**_edit_request(image_model, images, prompt, "repair"))
        corrected = _png(result, "REPAIR")
    except (JobFailure, BudgetRefused, PriceUnknown):
        raise
    except Exception as error:
        raise JobFailure(provider_image_error(error, "REPAIR").code, "REPAIR", rejected["id"]) from None
    try:
        stored = screened(corrected, True)
    except (BudgetRefused, PriceUnknown):
        raise
    except ImageConsistencyError as failure:
        verdict = "not_screened" if failure.reason_code in NO_VERDICT else "rejected"
        kept = keep(corrected, verdict, {"failed_checks": list(failure.failed_checks), "last_screen": failure.code,
                                         "evidence": [dict(item) for item in getattr(failure, "conflict_evidence", ())],
                                         "corrects": rejected["id"]}, True)
        raise JobFailure(failure.code, "SCREEN", kept["id"], failure.failed_checks) from None
    bank.note_correction(stored["id"], rejected["id"])
    return bank.asset(stored["id"])


def _run(bank, identity_record, contract, ledger, api_key, image_model, review_model, requested_by,
         client_factory, job_id):
    """One picture: the person's anchor, or one state edited from the current anchor."""
    identity_id = identity_record["id"]
    state_key = contract_key(contract)
    started = time.time()
    stage = "CREATE" if state_key == ANCHOR_KEY else "EDIT"
    try:
        client = _Metered(_client(api_key, client_factory), ledger)
        if state_key == ANCHOR_KEY:
            result = _make(bank, client, identity_record, dict(ANCHOR_CONTRACT), "anchor", None, image_model,
                           review_model, job_id, requested_by)
        else:
            anchor = bank.current_anchor(identity_id)
            if anchor is None:
                # Withdrawn while this job waited: the next request draws a new one.
                raise JobFailure("INTERNAL", "EDIT")
            result = _make(bank, client, identity_record, contract, "state", anchor, image_model, review_model,
                           job_id, requested_by)
        bank.record_job(identity_id=identity_id, state_key=state_key, outcome="stored", code="", stage="",
                        asset_id=result["id"], requested_by=requested_by, started_at=started)
        return result
    except JobFailure as failure:
        bank.record_job(identity_id=identity_id, state_key=state_key,
                        outcome="rejected" if failure.code == "MISMATCH" else "failed", code=failure.code,
                        stage=failure.stage, asset_id=failure.asset_id, requested_by=requested_by,
                        started_at=started)
        raise
    except (BudgetRefused, PriceUnknown) as refusal:
        bank.record_job(identity_id=identity_id, state_key=state_key, outcome="failed", code="BUDGET",
                        stage=stage, asset_id=None, requested_by=requested_by, started_at=started)
        raise JobFailure("BUDGET", stage) from refusal
    except Exception:
        bank.record_job(identity_id=identity_id, state_key=state_key, outcome="failed", code="INTERNAL",
                        stage=stage, asset_id=None, requested_by=requested_by, started_at=started)
        raise JobFailure("INTERNAL", stage) from None
    finally:
        try:
            ledger.release_unused()
        finally:
            bank.release(identity_id, state_key, OWNER)
            with _LOCK:
                key = _inflight_key(bank, identity_id, state_key)
                job = _INFLIGHT.get(key)
                if job is not None and job.future.done() is False:
                    # Called from inside the future: it is not done yet, but it is ending.
                    _INFLIGHT.pop(key, None)
