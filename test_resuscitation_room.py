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


def test_dashboard_explicitly_replaces_the_bedside_fragment():
    """The dashboard full rerun emits an empty instance of the bedside fragment first."""
    source = Path('app.py').read_text(encoding='utf-8')
    start = source.index('if not st.session_state.started:')
    stop = source.index('st.stop()', start)
    block = source[start:stop]
    clear = '_room.clear_room_fragment(ACCOUNT_CONTEXT)'
    dashboard = 'render_dashboard(ACCOUNT_CONTEXT, INITIAL_STATE, reset_session)'
    assert clear in block and dashboard in block
    assert block.index(clear) < block.index(dashboard)
