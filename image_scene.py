"""The room's patient photograph from the image bank (faculty request of 2026-09-26).

Used when the application has its account database (``MRS_AUTH_MODE=accounts``);
the shared-password mode keeps the session-only pictures of ``clinical_scene``.
``MRS_IMAGE_BANK=off`` returns an account deployment to those as well.

What changes for the person at the bedside:

* **The same person, every time.** The encounter draws one synthetic identity
  compatible with its case, stored with the encounter; a reload, a resumed
  encounter or a restarted server shows the same person, and never pays again
  for a photograph already made.
* **The current state or nothing.** The photograph shown is the one of this
  person in exactly the state the engine recorded, devices included. While it
  is being made, or when none can be, the room shows its neutral view and says
  so; the monitor and the examination stay current. A photograph of an earlier
  state is never labelled as the patient now.
* **The wait blocks nothing.** Requests run in the background (``image_broker``);
  orders and the clinical clock do not wait for them.
* **What was shown is kept.** Every change -- a photograph, a wait, a failure and
  why -- is written with the encounter (``mrs_image_displays``), so a reviewer
  can tell a limitation of the simulator from an omission of the resident. That
  record is also each resident's visual exposure, which the next encounter's
  choice of identity reads.

Only the room of the encounter's owner writes that record. Nothing here reads a
diagnosis, a rubric or an expected action.
"""
from __future__ import annotations

import base64
import time

import streamlit as st

BANK_SETTING = "MRS_IMAGE_BANK"
VIEW_VERSION = 1
_LEGACY_DEMOGRAPHICS = {"PS001": {"age_years": 70, "sex": "male"},
                        "PS002": {"age_years": 64, "sex": "female"}}


class DisplayImage(str):
    """A photograph for the browser: base64 bytes plus what the room needs to label it."""

    def __new__(cls, encoded, *, mime, limitations=(), asset_id=None, identity_id=None):
        value = super().__new__(cls, encoded)
        value.mime = mime
        value.limitations = tuple(x for x in limitations
                                  if x in ("mild_skin_moisture", "breathing_effort", "mild_skin_color"))
        value.asset_id = asset_id
        value.identity_id = identity_id
        return value


def _setting(name, default=""):
    from clinical_scene import setting
    return setting(name, default)


def enabled(context):
    """The bank serves this room: an account database, and not switched off."""
    if not context or context.get("store") is None:
        return False
    return str(_setting(BANK_SETTING, "on")).strip().lower() not in {"off", "0", "false", "no"}


def generation_allowed(role, review_case=False):
    """Whether this session may pay for a photograph: the same rule as the launch (faculty B1).

    ``launch_options`` withholds the picture's key from a role the paid gate
    refuses and from a case opened for review; until 2026-09-26 the room read
    the key directly and paid anyway.
    """
    from offline_cases import offline_cases_enabled, paid_generation_allowed
    return not offline_cases_enabled() and paid_generation_allowed(role) and not review_case


def patient_demographics(state):
    spec = state.get("encounter_spec") or {}
    if isinstance(spec, dict) and "clinical_case" in spec:
        patient = (spec.get("clinical_case") or {}).get("patient")
        return patient if isinstance(patient, dict) else None
    return _LEGACY_DEMOGRAPHICS.get(state.get("case_id"))


def _bank(context):
    from image_bank import ImageBank
    import image_pack
    bank = ImageBank(context["store"])
    try:
        image_pack.ensure_imported(bank)
    except Exception:
        # A pack that cannot be read must not take the room down; its images are
        # simply not there, and the room makes or waits for its own.
        import logging
        logging.getLogger(__name__).warning("image_pack_import_failed")
    return bank


class View:
    """This browser session's view of one encounter's photographs."""

    def __init__(self, key):
        self.key = key
        self.identity = None
        self.identity_reason = None
        self.cache = {}
        self.pending_since = {}
        self.force = set()
        self.logged = None
        self.current_key = None
        self.current_status = {}

    # --- what the bedside tools ask of the session's image jobs -------------------------------
    @property
    def pending(self):
        return self.current_key if self.current_status.get("state") == "pending" else None

    def discard(self):
        """Nothing to cancel: a job keeps running and its photograph is kept for later."""
        self.cache.clear()

    def failure(self, signature=None):
        return dict(self.current_status) if self.current_status.get("state") == "failed" else None

    def retry(self, signature=None):
        """Ask once more for the current state after a failure. It goes through the budget again."""
        if self.current_key is None or self.current_status.get("state") != "failed":
            return False
        self.force.add(self.current_key)
        return True

    def _rejected(self, context):
        # Only for a state that failed now, as the session's jobs always did: a state
        # whose photograph was corrected and accepted has no "issue" to show.
        if self.identity is None or self.current_key is None or self.current_status.get("state") != "failed":
            return None
        rejected = [asset for asset in _bank(context).assets(self.identity["id"])
                    if asset["state_key"] == self.current_key and asset["screen"] == "rejected"]
        return max(rejected, key=lambda asset: asset["created_at"]) if rejected else None

    def diagnostic_candidate(self, signature=None, context=None):
        context = context or st.session_state.get("_image_context")
        asset = self._rejected(context) if context else None
        if asset is None:
            return None
        return base64.b64encode(_bank(context).blob(asset["display_sha256"])).decode("ascii")

    def diagnostic_evidence(self, signature=None, context=None):
        context = context or st.session_state.get("_image_context")
        asset = self._rejected(context) if context else None
        return tuple((asset or {}).get("screen_details", {}).get("evidence", ()))


def _view_key(state, attempt_id):
    from image_bank import BANK_VERSION
    spec = state.get("encounter_spec") or {}
    patient = (state.get("case_id"), spec.get("content_sha256"))
    return (attempt_id, patient, BANK_VERSION, VIEW_VERSION)


def _choose_identity(bank, context, state, attempt_id):
    """The encounter's identity: stored, prepared, or chosen now and stored."""
    from image_identities import compatible_identities, identity
    from image_selection import choose_identity
    from image_bank import contract_key
    from patient_appearance import appearance_state
    token, user = context["token"], context["user"]
    if attempt_id:
        stored = bank.assignment(token, attempt_id)
        if stored is not None:
            return identity(stored["identity_id"]), stored["selection"]
    patient = patient_demographics(state)
    candidates = compatible_identities(patient) if patient else []
    arrival = contract_key(appearance_state(state))
    ready = {candidate["id"] for candidate in candidates if bank.usable_asset(candidate["id"], arrival)}
    spec = state.get("encounter_spec") or {}
    family = (spec.get("clinical_case") or {}).get("engine", {}).get("family") or state.get("case_id") or ""
    chosen, why = choose_identity(candidates, exposures=bank.exposures(user["id"]), usage=bank.usage(),
                                  ready=ready, family=family, seed=attempt_id or state.get("case_id") or "")
    if chosen is None:
        return None, why
    if attempt_id:
        stored = bank.assign(token, attempt_id, identity_id=chosen["id"], family=family,
                             case_id=(spec.get("clinical_case") or {}).get("id") or state.get("case_id") or "",
                             repeat_kind=why["repeat_kind"], selection=why)
        return identity(stored["identity_id"]), stored["selection"]
    return chosen, why


def _preload(bank, identity_id):
    """Every usable photograph of this person into this process's memory, in the background."""
    from image_broker import _POOL
    from image_selection import usable

    def load():
        for asset in bank.assets(identity_id):
            if usable(asset):
                bank.blob(asset["display_sha256"])
    try:
        _POOL.submit(load)
    except Exception:
        pass


def _display(bank, asset):
    raw = bank.blob(asset["display_sha256"])
    if raw is None:
        return None
    facts = bank.blob_facts(asset["display_sha256"]) or {}
    return DisplayImage(base64.b64encode(raw).decode("ascii"), mime=facts.get("content_type", "image/webp"),
                        limitations=(asset.get("screen_details") or {}).get("limitations", ()),
                        asset_id=asset["id"], identity_id=asset["identity_id"])


def _log(bank, context, view, attempt_id, state, contract, status, image):
    """One row per change in what the room shows; never one per rerun."""
    if not attempt_id or context["user"].get("id") is None:
        return
    outcome = {"ready": "image", "pending": "pending", "failed": "failed"}.get(status.get("state"), "unavailable")
    signature = (view.current_key, outcome, getattr(image, "asset_id", None), status.get("code", ""))
    if signature == view.logged:
        return
    try:
        bank.log_display(context["token"], attempt_id, identity_id=view.identity["id"] if view.identity else "",
                         contract=contract, outcome=outcome, asset_id=getattr(image, "asset_id", None),
                         code=status.get("code", ""), limitations=getattr(image, "limitations", ()),
                         sim_time=state.get("sim_time"))
        view.logged = signature
    except Exception:
        # The record of what was shown must not stop the room from showing it.
        import logging
        logging.getLogger(__name__).warning("image_display_log_failed")


def scene_image(state, events, context):
    """The photograph of the current state, or None; sets the room's image flags either way.

    Nothing about the photograph may stop the encounter: a database that
    cannot be reached, or any other failure here, leaves the room with its
    neutral view and the reason, and the monitor, the examination and the
    orders work as before.
    """
    try:
        return _scene_image(state, events, context)
    except Exception as error:
        import logging
        logging.getLogger(__name__).warning("image_scene_failed %s", type(error).__name__)
        st.session_state["_scene_current"] = False
        st.session_state["_scene_failed"] = False
        st.session_state["_scene_pending"] = False
        st.session_state["_scene_status"] = {"state": "unavailable", "code": "INTERNAL"}
        view = st.session_state.get("_scene_jobs")
        if isinstance(view, View):
            view.current_status = st.session_state["_scene_status"]
        return None


def _scene_image(state, events, context):
    from image_bank import contract_key
    from patient_appearance import appearance_state
    import image_broker
    arrival = next((e for e in events if e.get("kind") == "presentation"), None)
    if not arrival:
        return None
    st.session_state["_image_context"] = context
    attempt_id = st.session_state.get("_attempt_id")
    key = _view_key(state, attempt_id)
    view = st.session_state.get("_scene_jobs")
    if not isinstance(view, View) or view.key != key:
        view = View(key)
        st.session_state["_scene_jobs"] = view
        st.session_state["_scene_identity"] = key
    bank = _bank(context)
    contract = appearance_state(state)
    try:
        state_key = contract_key(contract)
        from image_consistency import _contract
        _contract(contract)
    except Exception:
        state_key = None
    view.current_key = state_key
    image = None
    if view.identity is None:
        # A database error is not "no compatible person": it reaches scene_image's
        # handler, which says so, and the next rerun asks again.
        view.identity, view.identity_reason = _choose_identity(bank, context, state, attempt_id)
        if view.identity is not None:
            _preload(bank, view.identity["id"])
    if view.identity is None:
        status = {"state": "unavailable", "code": "UNSUPPORTED"}
    elif state_key is None:
        status = {"state": "unavailable", "code": "CONTRACT"}
    elif state_key in view.cache:
        image, status = view.cache[state_key], {"state": "ready"}
    elif state_key in view.pending_since and image_broker.running(bank, view.identity["id"], state_key) is not None:
        status = {"state": "pending", "stage": "CREATE",
                  "elapsed_seconds": round(time.monotonic() - view.pending_since[state_key], 1)}
    else:
        from image_pricing import configured_budget
        role = context["user"].get("role")
        review_case = bool((st.session_state.get("encounter_assignment") or {}).get("review_case"))
        allowed = generation_allowed(role, review_case)
        try:
            budget = configured_budget(_setting)
        except ValueError:
            budget = None
        if budget is None:
            outcome = image_broker.Outcome("unavailable", code="BUDGET_CONFIG")
            asset = bank.usable_asset(view.identity["id"], state_key)
            if asset is not None:
                outcome = image_broker.Outcome("ready", asset=asset)
        else:
            outcome = image_broker.request(
                bank, view.identity, contract, api_key=_setting("OPENAI_API_KEY") if allowed else "",
                allowed=allowed, image_model=_setting("MRS_IMAGE_MODEL", "gpt-image-1.5").strip() or "gpt-image-1.5",
                review_model=_setting("MRS_IMAGE_REVIEW_MODEL", "gpt-5-mini").strip() or "gpt-5-mini",
                requested_by=f"user:{context['user'].get('id')}", budget=budget,
                force=state_key in view.force)
            view.force.discard(state_key)
        if outcome.state == "ready":
            image = _display(bank, outcome.asset)
            if image is not None:
                view.cache[state_key] = image
                view.pending_since.pop(state_key, None)
                status = {"state": "ready"}
            else:
                status = {"state": "unavailable", "code": "INTERNAL"}
        elif outcome.state == "pending":
            started = view.pending_since.setdefault(state_key, time.monotonic())
            status = {"state": "pending", "stage": "CREATE" if outcome.stage in ("ANCHOR", "QUEUED") else "SCREEN",
                      "queued": outcome.stage == "ELSEWHERE",
                      "elapsed_seconds": round(time.monotonic() - started, 1)}
        else:
            view.pending_since.pop(state_key, None)
            status = {"state": outcome.state, "code": outcome.code, "stage": outcome.stage or "CREATE"}
    view.current_status = status
    _log(bank, context, view, attempt_id, state, contract, status, image)
    st.session_state["_scene_current"] = image is not None
    st.session_state["_scene_failed"] = status.get("state") == "failed"
    st.session_state["_scene_pending"] = status.get("state") == "pending"
    st.session_state["_scene_status"] = status
    return image


def scene_photo_html(image):
    """The photograph as its own element: it only changes when the photograph does."""
    if not image:
        return '<div class="scene-photo scene-photo-empty"></div>'
    mime = getattr(image, "mime", "image/png")
    return f'<div class="scene-photo" style="background-image:url(data:{mime};base64,{image})"></div>'
