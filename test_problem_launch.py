"""Learner launch uses newly authored cases; failed generation starts nothing."""
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from curriculum import CHALLENGES
from test_generated_case import AuthorClient, novel_payload, approval
from conftest import onboarded


def install_author(monkeypatch, payload_factory=None, review=None):
    import generated_case
    real_author = generated_case.generate_ai_encounter
    records = []
    def author(challenge_id, base_state, api_key="", model="", seed=None, client=None, review_model=None, progress=None, on_case_compiled=None):
        payload = payload_factory(len(records)) if payload_factory else novel_payload()
        fake = AuthorClient(payload, review)
        records.append(fake)
        return real_author(challenge_id, base_state, api_key, model, seed, fake, review_model, progress=progress,
                           on_case_compiled=on_case_compiled)
    monkeypatch.setattr(generated_case, "generate_ai_encounter", author)
    return records


def open_shared(monkeypatch):
    monkeypatch.setenv('MRS_AUTH_MODE', 'shared')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    app = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=30)
    app.secrets['APP_PASSWORD'] = 'test-only'
    app.session_state['_shared_access_granted'] = True
    app.run()
    assert not app.exception
    return app


def test_launch_offers_only_problems_and_generates_selected_new_case(monkeypatch):
    author_calls = install_author(monkeypatch, lambda index: novel_payload(age=42 + index, sex='female' if index % 2 == 0 else 'male'))
    for index, problem in enumerate(CHALLENGES):
        app = open_shared(monkeypatch)
        app.session_state['selected_case'] = 'PS002 · Acute Dyspnea with Shock'
        app.run()
        selector = next(s for s in app.selectbox if s.label == 'Clinical problem')
        assert len(selector.options) == len(CHALLENGES)
        assert not any('PS001' in s or 'PS002' in s for s in selector.options)
        selector.set_value(problem).run()
        next(b for b in app.button if b.label == 'Begin Encounter').click().run()
        assert not app.exception
        state = app.session_state.state
        assert state['encounter_spec']['challenge_id'] == problem
        assert state['engine_family'] == 'generated'
        assert state['encounter_spec']['provenance']['authoring'] == 'novel_structured_case'
        assert state['encounter_facts']['age_years'] == 42 + index
        assert 'adrenal crisis' in state['encounter_spec']['clinical_case']['faculty']['diagnosis']
        assert app.session_state.selected_case == problem
        assert state['sim_time'] == 0
        assert any(b.label == 'ECG' for b in app.button)
    assert len(author_calls) == len(CHALLENGES)
    assert all(len(client.calls) == 2 for client in author_calls)


def test_missing_generation_key_shows_retryable_message_and_keeps_patient_unlaunched(monkeypatch):
    app = open_shared(monkeypatch)
    next(b for b in app.button if b.label == 'Begin Encounter').click().run()
    assert not app.exception
    assert any('OPENAI_API_KEY' in item.value for item in app.error)
    assert not app.session_state.started
    assert not any(item.label == 'Encounter' for item in app.radio)
    assert any(b.label == 'Begin Encounter' for b in app.button)


def test_failed_independent_review_does_not_show_unreviewed_patient(monkeypatch):
    failed = approval()
    failed['coherent'] = False
    failed['checks']['visual_consistency'] = False
    failed['issues'] = ['Appearance is inconsistent with physiology.']
    calls = install_author(monkeypatch, review=failed)
    app = open_shared(monkeypatch)
    next(b for b in app.button if b.label == 'Begin Encounter').click().run()
    assert not app.exception
    assert any('consistency screen' in item.value for item in app.error)
    assert not app.session_state.started
    assert not any(item.label == 'Encounter' for item in app.radio)
    # With one review round a rejected case is reported, not repaired: author and
    # review, and no clinical correction whose own re-review could not run.
    # Raising this raises the price of every failed encounter, so pin it.
    assert len(calls) == 1
    stages = [call['max_output_tokens'] for call in calls[0].calls]
    assert stages == [24000, 6000]


def test_repeat_authors_new_patient_from_prior_problem_without_old_case_or_answers(monkeypatch):
    from test_curriculum_trajectories import load_engine, initialize
    from encounter_generator import generate_encounter
    calls = install_author(monkeypatch, lambda index: novel_payload(age=42 + index, sex='female' if index == 0 else 'male'))
    engine = load_engine()
    engine['_runtime_secret'] = lambda key: ''
    from test_generation_progress import RecordingStatus
    engine['st'].status = lambda *args, **kwargs: RecordingStatus()
    original = generate_encounter('R1-04', engine['INITIAL_STATE'], seed=17)
    session = initialize(engine, original['state'])
    session.selected_case = 'PS001 · Tachyarrhythmia in an Acutely Ill Patient'
    session.attempt_number = 1
    engine['begin_repeat_encounter']({})
    assert session.state['encounter_spec']['challenge_id'] == 'R1-04'
    assert session.state['encounter_spec']['seed'] != 17
    assert session.state['encounter_facts']['age_years'] == 43
    assert session.state['encounter_facts']['sex'] == 'male'
    assert session.state['case_id'] != original['state']['case_id']
    assert session.selected_case == 'R1-04'
    assert session.attempt_number == 2
    assert not session.management_trace
    assert len(calls) == 2


def test_new_ai_case_is_persisted_and_resumed_without_reauthoring(tmp_path, monkeypatch):
    from account_store import AccountStore, hash_password
    calls = install_author(monkeypatch)
    url = 'sqlite:///' + str(tmp_path / 'novel-accounts.sqlite3')
    monkeypatch.setenv('MRS_AUTH_MODE', 'accounts')
    monkeypatch.setenv('MRS_DATABASE_URL', url)
    monkeypatch.setenv('MRS_ALLOW_LOCAL_SQLITE', 'true')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin('teacher', hash_password('local-test-password'))
    teacher = store.authenticate('teacher', 'local-test-password')
    invite = store.create_invite(teacher, 'resident', 1)
    token = store.register('novel-resident', 'local-resident-password', invite)
    onboarded(store, token)

    def open_resident():
        app = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=30)
        app.session_state['_account_token'] = token
        app.run()
        assert not app.exception
        return app

    first = open_resident()
    next(b for b in first.button if b.label == 'Begin Encounter').click().run()
    assert not first.exception
    assert first.session_state.state['engine_family'] == 'generated'
    frozen = deepcopy(first.session_state.state['encounter_spec'])
    next(w for w in first.radio if w.label == 'Encounter').set_value('Tests').run()
    first.text_area[0].set_value('Measure temperature')
    next(b for b in first.button if b.label == 'Submit').click().run()
    assert not first.exception
    # An ordered study no longer advances the clock on its own. It stays visibly
    # pending with its expected time until the resident reassesses explicitly.
    assert first.session_state.state['sim_time'] == 0
    assert [item['diagnostic_type'] for item in
            first.session_state.state['pending_investigations']] == ['temperature']
    assert any('Temperature: pending' in str(c.value) for c in first.caption)
    first.text_area[0].set_value('Reassess in 5 minutes')
    next(b for b in first.button if b.label == 'Submit').click().run()
    assert not first.exception
    expected = deepcopy(first.session_state.state)
    trace = deepcopy(first.session_state.management_trace)
    assert 'temperature' in expected['diagnostics'] and trace
    assert not expected['pending_investigations']
    assert expected['encounter_spec'] == frozen
    saved = store.list_attempts(token)
    assert len(saved) == 1
    assert saved[0]['payload']['session']['state'] == expected
    second = open_resident()
    next(b for b in second.button if b.label == 'Resume encounter').click().run()
    assert not second.exception
    assert second.session_state.state == expected
    assert second.session_state.management_trace == trace
    assert len(calls) == 1
    assert not any('faculty brief' in b.label.lower() or 'faculty pdf' in b.label.lower() for b in second.button)
