from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from curriculum import CHALLENGES


def test_launch_offers_only_problems_and_generates_selected_case(monkeypatch):
    monkeypatch.setenv('MRS_AUTH_MODE','shared')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    for problem in CHALLENGES:
        app=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=20)
        app.secrets['APP_PASSWORD']='test-only'
        app.session_state['_shared_access_granted']=True
        # A previous shared session may have retained the legacy label.
        app.session_state['selected_case']='PS002 · Acute Dyspnea with Shock'
        app.run()
        assert not app.exception
        selector=next(s for s in app.selectbox if s.label=='Clinical problem')
        assert len(selector.options)==len(CHALLENGES)
        assert not any('PS001' in s or 'PS002' in s for s in selector.options)
        selector.set_value(problem).run()
        next(b for b in app.button if b.label=='Begin Encounter').click().run()
        assert not app.exception
        assert app.session_state.state['encounter_spec']['challenge_id']==problem
        assert app.session_state.selected_case==problem
        assert app.session_state.state['sim_time']==0


def test_repeat_generates_from_prior_problem_instead_of_legacy_surface():
    from contextlib import nullcontext
    from test_curriculum_trajectories import load_engine, initialize
    from encounter_generator import generate_encounter
    engine=load_engine()
    engine['_runtime_secret']=lambda key: ''
    engine['st'].spinner=lambda *args: nullcontext()
    original=generate_encounter('R1-04',engine['INITIAL_STATE'],seed=17)
    session=initialize(engine,original['state'])
    session.selected_case='PS001 · Tachyarrhythmia in an Acutely Ill Patient'
    session.attempt_number=1
    engine['begin_repeat_encounter']({})
    assert session.state['encounter_spec']['challenge_id']=='R1-04'
    assert session.state['encounter_spec']['seed']!=17
    assert session.selected_case=='R1-04'
    assert session.attempt_number==2
