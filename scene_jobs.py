"""Session-owned image jobs. Workers never access Streamlit or clinical state."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="patient-image")


class SceneJobs:
    def __init__(self):
        self.base = None
        self.images = {}
        self.failed = set()
        self.pending = None

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
        except Exception:
            self.failed.add(signature)

    def request(self, signature, state, api_key, model, initial, edit):
        self.poll()
        if signature in self.images or signature in self.failed or self.pending or not api_key:
            return
        frozen = deepcopy(state)
        if self.base is None:
            future = _POOL.submit(initial, frozen, api_key, model)
        else:
            future = _POOL.submit(edit, self.base, frozen, api_key, model)
        self.pending = (signature, future)

    def current(self, signature):
        self.poll()
        return self.images.get(signature)

    def previous(self):
        return next(reversed(self.images.values()), self.base)
