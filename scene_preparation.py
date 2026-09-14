"""Prepare one initial image privately while a compiled case is being reviewed.

The local owner transfers its screened-image job to one browser session only
after the case has passed independent review and any required attempt storage.
No job, draft or image is part of the persisted encounter payload.
"""
from functools import partial

from patient_appearance import appearance_signature
from scene_jobs import SceneJobs
from scene_pipeline import screened_scene, screened_appearance


def _source_fingerprint(state):
    spec = state.get("encounter_spec") or {}
    return (spec.get("provenance") or {}).get("raw_case_sha256")


class ScenePreparation:
    def __init__(self, api_key, model="gpt-image-1.5", review_model="gpt-5-mini"):
        self._api_key = api_key
        self._model = model
        self._review_model = review_model
        self._jobs = None
        self._fingerprint = None
        self._signature = None
        self._adopted = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self._adopted:
            self.discard()
        self._api_key = None

    def discard(self):
        if self._jobs is not None:
            self._jobs.discard()
        self._jobs = None
        self._fingerprint = self._signature = None

    def on_case_compiled(self, snapshot, case_fingerprint):
        if not self._api_key or self._jobs is not None:
            return
        jobs = SceneJobs()
        self._jobs = jobs
        self._fingerprint = case_fingerprint
        self._signature = appearance_signature(snapshot)
        try:
            jobs.request(self._signature, snapshot, self._api_key, self._model,
                         partial(screened_scene, review_model=self._review_model),
                         partial(screened_appearance, review_model=self._review_model),
                         progress_supported=True)
        except Exception:
            # Failure to schedule optional visual work must not bypass or abort
            # the independent clinical review. Normal room rendering can retry.
            self.discard()

    def adopt(self, session, state, attempt_id=None):
        """Called after clinical approval and save/restore, never by the worker."""
        if (self._jobs is None or not self._fingerprint
                or self._fingerprint != _source_fingerprint(state)
                or self._signature != appearance_signature(state)):
            self.discard()
            return False
        previous = session.pop("_prepared_scene", None)
        if previous:
            previous["jobs"].discard()
        session["_prepared_scene"] = {
            "owner": session.get("_account_user_id"), "attempt_id": attempt_id,
            "case_id": state.get("case_id"), "source_sha256": self._fingerprint,
            "signature": self._signature, "jobs": self._jobs,
        }
        self._adopted = True
        self._jobs = None
        return True


def consume_prepared_scene(session, state, attempt_id=None):
    """Consume once and only for the exact reviewed case, owner and appearance."""
    prepared = session.pop("_prepared_scene", None)
    if prepared is None:
        return None
    if (prepared["owner"] != session.get("_account_user_id")
            or prepared["attempt_id"] != attempt_id
            or prepared["case_id"] != state.get("case_id")
            or prepared["source_sha256"] != _source_fingerprint(state)
            or prepared["signature"] != appearance_signature(state)):
        prepared["jobs"].discard()
        return None
    return prepared["jobs"]
