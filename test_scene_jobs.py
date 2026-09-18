from concurrent.futures import Future
from copy import deepcopy

from scene_jobs import SceneJobs


class PendingPool:
    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        future = Future()
        self.calls.append((function, args, future))
        return future


def test_late_result_keeps_its_frozen_state_and_does_not_replace_current(monkeypatch):
    pool = PendingPool()
    monkeypatch.setattr('scene_jobs._POOL', pool)
    jobs = SceneJobs()
    initial, edit = object(), object()
    state = {'observable': {'mental_status': 'Alert'}}
    jobs.request('alert', state, 'key', 'model', initial, edit)
    state['observable']['mental_status'] = 'Drowsy'
    assert pool.calls[0][1][0]['observable']['mental_status'] == 'Alert'
    jobs.request('drowsy', state, 'key', 'model', initial, edit)
    assert len(pool.calls) == 1  # One in-flight job per encounter.
    pool.calls[0][2].set_result('original-image')
    assert jobs.current('drowsy') is None
    jobs.request('drowsy', state, 'key', 'model', initial, edit)
    assert pool.calls[1][1][0] == 'original-image'
    pool.calls[1][2].set_result('drowsy-image')
    assert jobs.current('drowsy') == 'drowsy-image'
    assert jobs.current('alert') == 'original-image'
    state['observable']['mental_status'] = 'Obtunded'
    jobs.request('obtunded', state, 'key', 'model', initial, edit)
    assert pool.calls[2][1][0] == 'original-image'  # Never edit a prior edit.
    other_encounter = SceneJobs()
    assert other_encounter.current('alert') is None


def test_failed_signature_does_not_repeat_requests_and_can_retry(monkeypatch):
    pool = PendingPool()
    monkeypatch.setattr('scene_jobs._POOL', pool)
    jobs = SceneJobs()
    state = {'observable': {'mental_status': 'Alert'}}
    before = deepcopy(state)
    jobs.request('a', state, 'key', 'model', object(), object())
    pool.calls[0][2].set_exception(ValueError('provider failure'))
    assert jobs.current('a') is None
    jobs.request('a', state, 'key', 'model', object(), object())
    assert len(pool.calls) == 1 and state == before
    jobs.failed.discard('a')
    jobs.request('a', state, 'key', 'model', object(), object())
    assert len(pool.calls) == 2
