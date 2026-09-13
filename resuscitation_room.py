"""Visual, read-only bedside view driven exclusively by observed treatment state."""
from html import escape
import streamlit as st
from encounter_workspace import encounter_sections


def device_labels(t):
    labels = []
    if t.get('invasive_ventilation'):
        labels.append(f"Ventilator · {t.get('ventilator_mode') or 'VC/AC'} · FiO₂ {t.get('ventilator_fio2_percent', 100)}% · PEEP {t.get('ventilator_peep_cmh2o', 8)}")
    elif t.get('niv'):
        labels.append(f"{t.get('niv_mode') or 'NIV'} · FiO₂ {t.get('niv_fio2_percent', '—')}%")
    elif t.get('oxygen'):
        labels.append(f"{t.get('oxygen_device') or 'Oxygen'} · {t.get('oxygen_flow_lpm', '—')} L/min")
    for flag, rate, unit in [('norepinephrine', 'norepinephrine_rate', t.get('norepinephrine_units') or 'mcg/kg/min'), ('dobutamine', 'dobutamine_rate', 'mcg/kg/min'), ('nitroglycerin', 'nitroglycerin_rate_mcg_min', 'mcg/min')]:
        if t.get(flag):
            labels.append(f"{flag.capitalize()} · {t.get(rate, '—')} {unit}")
    return labels


def patient_svg(t):
    """Schematic equipment view, deliberately not a depiction of physical signs."""
    support = bool(t.get('oxygen') or t.get('niv') or t.get('invasive_ventilation'))
    mask = ''
    if support:
        tubing = '<path d="M270 123 C340 110 325 225 393 223" fill="none" stroke="#43bed0" stroke-width="7"/>'
        device = str(t.get('oxygen_device') or '').lower()
        if t.get('invasive_ventilation'):
            mask = '<path d="M252 122 H274 V148 H305" fill="none" stroke="#43bed0" stroke-width="8"/>' + tubing
        elif not t.get('niv') and ('cannula' in device or 'nasal' in device):
            mask = '<path d="M222 110 Q255 131 288 110 M250 119 V112 M261 119 V112" fill="none" stroke="#168da4" stroke-width="3"/>' + tubing
        else:
            mask = '<path d="M237 107 Q255 97 273 107 L271 129 Q255 144 239 129Z" fill="#a7ecf3" stroke="#168da4" stroke-width="3"/>' + tubing
    pump = ''
    if any(t.get(k) for k in ('norepinephrine', 'dobutamine', 'nitroglycerin')):
        pump = '<path d="M99 75 V327 M77 328 H121" stroke="#718b9e" stroke-width="7"/><rect x="74" y="133" width="51" height="57" rx="8" fill="#e1edf4" stroke="#718b9e"/><rect x="81" y="144" width="37" height="22" rx="3" fill="#70dac5"/><path d="M125 170 Q159 174 170 223" fill="none" stroke="#70dac5" stroke-width="3"/>'
    return f'''<svg viewBox="0 0 510 365" role="img" aria-label="Schematic patient bed and active support equipment" xmlns="http://www.w3.org/2000/svg">
    <rect width="510" height="365" rx="22" fill="#eaf0f4"/><path d="M0 270 H510" stroke="#d5e0e7"/>
    <rect x="147" y="48" width="216" height="279" rx="29" fill="#a6b8c7"/><rect x="158" y="54" width="194" height="257" rx="23" fill="#fff"/>
    <rect x="184" y="65" width="142" height="72" rx="20" fill="#dce7ec"/>
    <ellipse cx="255" cy="105" rx="33" ry="39" fill="#cba88f"/><path d="M224 92 Q230 55 260 64 Q285 68 287 96" fill="#68717a"/>
    <path d="M240 144 Q211 141 195 165 L176 234 L193 239 L218 190 L220 262 H292 L293 188 L316 239 L334 233 L315 165 Q300 143 270 144" fill="#b5d3e0"/>
    <path d="M200 214 Q256 196 314 214 L332 303 H179Z" fill="#36748b"/><path d="M193 250 Q255 233 319 253" fill="none" stroke="#6291a4" stroke-width="3"/>
    <path d="M141 159 V272 M369 159 V272" stroke="#70899d" stroke-width="9" stroke-linecap="round"/>
    <circle cx="177" cy="335" r="10" fill="#405565"/><circle cx="333" cy="335" r="10" fill="#405565"/>{mask}{pump}</svg>'''


def monitor_html(o, time_label):
    pulse = o.get('pulse_present', True)
    values = [('HR', str(o.get('hr', '—')), '/min', '#72efa5'),
              ('SpO₂', str(o.get('spo2', '—')) if pulse else '—', '%', '#64dced'),
              ('BP', f"{o.get('sbp', '—')}/{o.get('dbp', '—')}" if pulse else '—', 'mmHg', '#f6c77a'),
              ('RR', str(o.get('respiratory_rate', '—')) if pulse else '0', '/min', '#f1efff')]
    cards = ''.join(f'<div style="color:{c};padding:12px"><div style="font-size:13px">{label}</div><div style="font:700 clamp(24px,3.5vw,48px) monospace">{escape(v)}</div><small>{unit}</small></div>' for label,v,unit,c in values)
    return f'<div style="background:#0c1924;border:3px solid #294354;border-radius:16px;padding:14px"><div style="color:#c3d4df;font:14px monospace">BEDSIDE MONITOR · {escape(time_label)}</div><div style="display:grid;grid-template-columns:1fr 1fr">{cards}</div></div>'


def render_room(state, events, ecg_svg, render_event, time_label):
    from clinical_scene import scene_image, scene_html
    image = scene_image(state, events)
    st.markdown(scene_html(image, monitor_html(state['observable'], time_label), ecg_svg(state['observable'])), unsafe_allow_html=True)
    @st.dialog('ECG · synthetic lead II', width='large')
    def enlarged_ecg():
        st.markdown(ecg_svg(state['observable']), unsafe_allow_html=True)
    if st.button('Enlarge ECG'):
        enlarged_ecg()
    labels = device_labels(state['treatments'])
    if labels:
        st.caption('Current support · ' + ' | '.join(labels))
    _, latest, _, _ = encounter_sections(events)
    if latest:
        with st.container(border=True, height=180):
            for event in latest:
                render_event(event)
