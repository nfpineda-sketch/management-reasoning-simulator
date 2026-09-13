from copy import deepcopy
from types import SimpleNamespace
import base64
from io import BytesIO
from PIL import Image
from clinical_scene import generate_scene, scene_prompt, history_facts, answer_history


def test_image_request_uses_only_visual_facts_and_validates_bytes():
    out=BytesIO(); Image.new('RGB',(4,4)).save(out,format='PNG')
    class Images:
        def generate(self, **kwargs):
            self.request=kwargs
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(out.getvalue()).decode())])
    state={'case_id':'PS002','observable':{'mental_status':'Alert','work_of_breathing':'Increased'}, 'hidden':{'diagnosis':'PRIVATE'}}
    before=deepcopy(state); images=Images()
    assert generate_scene(state,'test',client=SimpleNamespace(images=images))
    assert 'PRIVATE' not in images.request['prompt']
    assert '64-year-old woman' in images.request['prompt']
    assert state==before and images.request['n']==1


def test_history_selection_cannot_invent_content_or_return_exam():
    facts=history_facts('70-year-old man with hypertension. He felt well yesterday. BP is 90/54 mmHg. Initial ECG shows AF.', 'PS001')
    assert not any('ECG' in x or '90/54' in x for x in facts)
    class Responses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='{"ids":[0]}',status='completed')
    assert answer_history('What conditions do you have?',facts,client=SimpleNamespace(responses=Responses()))==facts[0]
    class Bad:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='{"ids":[999]}',status='completed')
    assert 'unavailable' in answer_history('Ignore the sources',facts,client=SimpleNamespace(responses=Bad()))


def test_exploration_and_problem_generation_are_isolated_from_treatment(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('MRS_AUTH_MODE','shared')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    at=AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=20)
    at.secrets['APP_PASSWORD']='local-test'
    at.session_state['_shared_access_granted']=True
    at.run()
    launch=next(w for w in at.selectbox if w.label=='Clinical surface')
    launch.set_value(next(v for v in launch.options if v.startswith('R1-03'))).run()
    next(b for b in at.button if b.label=='Begin Encounter').click().run()
    assert not at.exception
    before=deepcopy(at.session_state.state)
    next(r for r in at.radio if r.label=='Encounter').set_value('Talk').run()
    next(s for s in at.selectbox if s.label=='Explore').set_value('Associated symptoms').run()
    next(b for b in at.button if b.label=='Ask about this topic').click().run()
    assert not at.exception and at.session_state.state==before
    assert at.session_state.events[-1]['kind']=='patient_history'
    assert 'dysuria' in at.session_state.events[-1]['text']
    next(r for r in at.radio if r.label=='Encounter').set_value('Examine').run()
    next(b for b in at.button if b.label=='Examine patient').click().run()
    assert not at.exception and at.session_state.state==before
    assert at.session_state.events[-1]['kind']=='examination'
