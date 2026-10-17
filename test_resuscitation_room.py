from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import resuscitation_room
from resuscitation_room import device_labels, patient_svg, monitor_html


def test_active_devices_and_monitor_do_not_mutate_state():
    t = {'oxygen': False, 'norepinephrine': False, 'norepinephrine_rate': 0.2}
    original = deepcopy(t)
    assert device_labels(t) == []
    assert 'mcg' not in patient_svg(t)
    assert t == original
    t.update(oxygen=True, oxygen_device='nasal cannula', oxygen_flow_lpm=4,
             norepinephrine=True, norepinephrine_units='mcg/kg/min')
    assert device_labels(t) == ['nasal cannula · 4 L/min', 'Norepinephrine · 0.2 mcg/kg/min']
    cannula = patient_svg(t)
    t.update(invasive_ventilation=True, ventilator_fio2_percent=60)
    assert device_labels(t)[0].startswith('Ventilator')
    assert patient_svg(t) != cannula


def test_pulseless_monitor_suppresses_unreliable_numbers():
    html = monitor_html({'pulse_present':False, 'hr':180, 'spo2':98, 'sbp':120, 'dbp':80}, '05:00')
    assert '120/80' not in html and '>98<' not in html
    assert '180' in html and '05:00' in html


def test_an_inactive_room_fragment_renders_nothing(monkeypatch):
    """A queued bedside fragment after navigation must clear itself, not repaint old state."""
    rendered = []
    fake = SimpleNamespace(
        session_state={
            'started': False,
            'encounter_ended': False,
            '_attempt_status': 'abandoned',
            '_room_image': 'stale-image',
        },
        markdown=lambda *args, **kwargs: rendered.append((args, kwargs)),
    )
    monkeypatch.setattr(resuscitation_room, 'st', fake)

    # The stale fragment still carries its old arguments, but session state says it is gone.
    resuscitation_room._room({'observable': {}}, [], None, None, '', None, active=True)

    assert rendered == []
    assert '_room_image' not in fake.session_state


def test_room_uses_no_streamlit_fragment():
    """The bedside is ordinary page output, so no previous fragment DOM can coexist."""
    source = Path('resuscitation_room.py').read_text(encoding='utf-8')
    start = source.index('def render_room(')
    stop = source.index('def clear_room_fragment', start)
    block = source[start:stop]
    assert '@st.fragment' not in source
    assert 'st.fragment(' not in source
    assert 'run_every=' not in source
    assert '_room(' in block



def test_app_keeps_bedside_in_a_stable_keyed_slot():
    """The bedside keeps one Streamlit element path across processing and result reruns."""
    source = Path('app.py').read_text(encoding='utf-8')
    start = source.index('_in_room = not st.session_state.encounter_ended')
    stop = source.index('_ecg_acquired, _ecg_notice = False, None', start)
    block = source[start:stop]
    assert 'st.container(key="enc-bedside-slot")' in block
    assert 'if _in_room and not _FAST_PENDING_SUBMISSION:' in block
    assert 'render_room(' in block
    assert 'else:' in block and 'st.empty()' in block

def test_dashboard_explicitly_clears_bedside_state_before_rendering():
    """The dashboard full rerun clears bedside transient state before rendering."""
    source = Path('app.py').read_text(encoding='utf-8')
    start = source.index('if not st.session_state.started:')
    stop = source.index('st.stop()', start)
    block = source[start:stop]
    clear = '_room.clear_room_fragment(ACCOUNT_CONTEXT)'
    dashboard = 'render_dashboard(ACCOUNT_CONTEXT, INITIAL_STATE, reset_session)'
    assert clear in block and dashboard in block
    assert block.index(clear) < block.index(dashboard)
