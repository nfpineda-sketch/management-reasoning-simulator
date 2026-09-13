from copy import deepcopy
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
