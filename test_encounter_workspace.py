from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from encounter_workspace import encounter_sections


def test_record_preserves_all_content_without_changing_source():
    events = [
        {'kind': 'presentation', 'text': 'Arrival facts', 'time': 0},
        {'kind': 'you', 'text': 'First order', 'time': 0},
        {'kind': 'diagnostic_result', 'text': 'Earlier result', 'time': 2},
        {'kind': 'you', 'text': 'Second order', 'time': 3},
        {'kind': 'clarification', 'text': 'Order held', 'time': 3},
        {'kind': 'clinical_update', 'text': 'Patient update', 'time': 4},
    ]
    original = deepcopy(events)
    arrival, latest, results, record = encounter_sections(events)
    assert record == original
    assert events == original
    assert arrival == events[:1]
    assert latest == events[3:]
    assert results == events[2:3]
    assert encounter_sections([]) == ([], [], [], [])


def test_both_clinical_surfaces_render_handover_and_complete_record(monkeypatch):
    monkeypatch.setenv('MRS_AUTH_MODE', 'shared')
    for index in (0, 1):
        at = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=20)
        at.secrets['APP_PASSWORD'] = 'local-test-only'
        at.session_state['_shared_access_granted'] = True
        at.run()
        at.selectbox[0].select_index(index).run()
        next(b for b in at.button if b.label == 'Begin Encounter').click().run()
        assert not at.exception
        assert [t.label for t in at.tabs][:3] == [
            'Current exchange', 'Investigation reports', 'Complete encounter record']
        source = next(e['text'] for e in at.session_state.events if e['kind'] == 'presentation')
        assert sum(m.value == source for m in at.markdown) >= 2
        assert not any('Developer' in e.label for e in at.expander)
