"""Session-owned image jobs. Workers never access Streamlit or clinical state."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
import logging
from threading import Lock
from time import monotonic

from scene_errors import SceneImageError, STAGES, safe_image_error

_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="patient-image")
_LOG = logging.getLogger(__name__)


class SceneJobs:
    def __init__(self):
        self.base = None
        self.images = {}
        self.failed = set()
        self.pending = None
        self._statuses = {}
        self._status_lock = Lock()
        self._discarded = False

    def _stage(self, signature, stage):
        # Called by the background worker, never with Streamlit or patient data.
        if not isinstance(stage, str) or stage not in STAGES:
            return
        with self._status_lock:
            record = self._statuses.get(signature)
            if not self._discarded and record and record["state"] == "pending":
                record.update(stage=stage, queued=False)
                if stage == 'REPAIR':
                    record['correction_attempted'] = True

    def _finish(self, signature, state, error=None):
        with self._status_lock:
            if self._discarded:
                return
            record = self._statuses.setdefault(signature, {"started": monotonic(), "stage": "CREATE"})
            record.update(state=state, finished=monotonic(), queued=False)
            if error is not None:
                record.update(stage=error.stage, code=error.code, reference=error.reference,
                              message=error.message, failed_checks=error.failed_checks)
            while len(self._statuses) > 16:
                del self._statuses[next(iter(self._statuses))]

    def status(self, signature):
        """Return a detached record with fixed labels and durations only."""
        self.poll()
        with self._status_lock:
            record = dict(self._statuses.get(signature, {}))
        started = record.pop("started", None)
        finished = record.pop("finished", None)
        end = finished if finished is not None else monotonic()
        record["elapsed_seconds"] = round(max(0.0, end - started), 1) if started is not None else 0.0
        record.setdefault("state", "ready" if signature in self.images else "unavailable")
        return record

    def failure(self, signature):
        status = self.status(signature)
        return status if status["state"] == "failed" else None

    def retry(self, signature):
        """Allow a new request only for an explicitly failed, unapproved state."""
        self.poll()
        if (self._discarded or signature not in self.failed or signature in self.images
                or (self.pending is not None and self.pending[0] == signature)):
            return False
        self.failed.discard(signature)
        with self._status_lock:
            self._statuses.pop(signature, None)
        return True

    def discard(self):
        """Abandon an unpublished preparation without accepting a late result.

        A provider request already running cannot be interrupted here. Its future
        and eventual image are dropped, and its progress callbacks become inert.
        """
        with self._status_lock:
            self._discarded = True
            self._statuses.clear()
        pending, self.pending = self.pending, None
        if pending is not None:
            pending[1].cancel()
        self.base = None
        self.images.clear()
        self.failed.clear()

    def poll(self):
        if self.pending is None or not self.pending[1].done():
            return
        signature, future = self.pending
        self.pending = None
        try:
            image = future.result()
            self.images[signature] = image
            if self.base is None:
                self.base = image
            # Keep the reference separately; bound per-session memory.
            while len(self.images) > 8:
                del self.images[next(iter(self.images))]
            self._finish(signature, "ready")
        except Exception as failure:
            with self._status_lock:
                stage = self._statuses.get(signature, {}).get("stage", "CREATE")
            error = safe_image_error(failure, stage)
            self.failed.add(signature)
            self._finish(signature, "failed", error)
            # Reconstructed allowlisted diagnostics; never an exception traceback.
            _LOG.warning("patient_image_failed reference=%s checks=%s",
                         error.reference, ",".join(error.failed_checks))

    def request(self, signature, state, api_key, model, initial, edit, *, progress_supported=False):
        self.poll()
        if self._discarded or signature in self.images or signature in self.failed or self.pending:
            return
        stage = "CREATE" if self.base is None else "EDIT"
        if not api_key:
            self.failed.add(signature)
            self._finish(signature, "failed", SceneImageError("CONFIG", stage))
            return
        frozen = deepcopy(state)
        with self._status_lock:
            self._statuses[signature] = {"state": "pending", "stage": stage, "started": monotonic(),
                                         "queued": bool(progress_supported)}
        if self.base is None:
            function, args = initial, (frozen, api_key, model)
        else:
            function, args = edit, (self.base, frozen, api_key, model)
        if progress_supported:
            function = partial(function, progress=partial(self._stage, signature))
        future = _POOL.submit(function, *args)
        self.pending = (signature, future)

    def current(self, signature):
        self.poll()
        return self.images.get(signature)

    def previous(self):
        return next(reversed(self.images.values()), self.base)
