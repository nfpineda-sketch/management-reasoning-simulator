"""Visual, read-only bedside view driven exclusively by observed treatment state."""
from html import escape
import streamlit as st


def device_labels(t, language="en"):
    """The support running now, one label each (M-04 in Spanish, faculty, 2026-10-07; drugs with V-9)."""
    spanish = language == "es"
    if spanish:
        import language as languages
    labels = []
    if t.get('invasive_ventilation'):
        labels.append(f"{'Ventilador' if spanish else 'Ventilator'} · {t.get('ventilator_mode') or 'VC/AC'} · FiO₂ {t.get('ventilator_fio2_percent', 100)}% · PEEP {t.get('ventilator_peep_cmh2o', 8)}")
    elif t.get('bag_mask'):
        labels.append('Ventilación con bolsa-mascarilla' if spanish else 'Bag-mask ventilation')
    elif t.get('niv'):
        mode = t.get('niv_mode') or 'NIV'
        if spanish and mode == 'NIV':
            mode = 'VMNI'
        labels.append(f"{mode} · FiO₂ {t.get('niv_fio2_percent', '—')}%")
    elif t.get('oxygen'):
        device = t.get('oxygen_device') or ('Oxígeno' if spanish else 'Oxygen')
        if spanish:
            device = languages.say(str(device), "es")
        labels.append(f"{device} · {t.get('oxygen_flow_lpm', '—')} L/min")
    for flag, rate, unit in [('norepinephrine', 'norepinephrine_rate', t.get('norepinephrine_units') or 'mcg/kg/min'), ('dobutamine', 'dobutamine_rate', 'mcg/kg/min'), ('nitroglycerin', 'nitroglycerin_rate_mcg_min', 'mcg/min')]:
        if t.get(flag):
            name = languages.drug(flag.capitalize(), "es") if spanish else flag.capitalize()
            labels.append(f"{name} · {t.get(rate, '—')} {unit}")
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


ROOM_RENDER_VERSION = 10


#: The monitor's labels in Spanish (M-01, faculty, 2026-10-07); SpO₂ is the same.
MONITOR_WORDS_ES = {'BEDSIDE MONITOR': 'MONITOR DE CABECERA', 'HR': 'FC', 'NIBP': 'PANI', 'RR': 'FR', 'SpO₂': 'SpO₂'}


def monitor_html(o, time_label, profile='baseline', seed=0, language='en'):
    from ecg12 import monitor_wave_svg
    pulse = o.get('pulse_present', True)
    words = MONITOR_WORDS_ES if language == 'es' else {}
    values = [(words.get('HR', 'HR'), str(o.get('hr', '—')), '/min', '#72efa5'),
              ('SpO₂', str(o.get('spo2', '—')) if pulse else '—', '%', '#64dced'),
              (words.get('NIBP', 'NIBP'), f"{o.get('sbp', '—')}/{o.get('dbp', '—')}" if pulse else '—', 'mmHg', '#f6c77a'),
              (words.get('RR', 'RR'), str(o.get('respiratory_rate', '—')), '/min', '#f1efff')]
    # A value is never split across lines: a pressure reads 132/80, whole (UX of the
    # clinical encounter, 2026-10-02); the size follows the monitor's width (BEDSPACE_CSS).
    cards = ''.join(f'<div style="color:{c}"><small>{label} <span class="monitor-unit">{unit}</span></small><div class="monitor-value">{escape(v)}</div></div>' for label,v,unit,c in values)
    wave = monitor_wave_svg(o, profile=profile, seed=seed)
    # The room says the simulated time once, beside the information; the monitor shows
    # the patient now, and carries a time only when one is given.
    heading = words.get('BEDSIDE MONITOR', 'BEDSIDE MONITOR') + (f' · {escape(time_label)}' if time_label else '')
    return (f'<div class="monitor-body"><div class="monitor-heading">{heading}</div>'
            + wave + f'<div class="monitor-values">{cards}</div></div>')


def render_room(state, events, ecg_svg, render_event, time_label, context=None):
    """The room, drawn with the page; it also redraws itself every 2 s, but only while a
    photograph is being prepared, so that the photograph appears when it is ready.

    Every redraw fades the room while it runs, and on the deployment that lasted about a
    second, every 2 s, even with no photograph to wait for (2026-10-05). Streamlit forgets
    these redraws at every run of the page, so each run asks for the photograph first and
    decides again.
    """
    from clinical_scene import scene_image
    st.session_state['_room_image'] = scene_image(state, events, context)
    every = 2 if st.session_state.get('_scene_pending', False) else None
    st.fragment(_room, run_every=every)(state, events, ecg_svg, render_event, time_label, context)


def _room(state, events, ecg_svg, render_event, time_label, context=None):
    from clinical_scene import scene_image, scene_html
    from patient_appearance import appearance_signature, appearance_summary
    # The page has just asked for the photograph; a redraw of the room on its own asks again.
    if '_room_image' in st.session_state:
        image = st.session_state.pop('_room_image')
    else:
        image = scene_image(state, events, context)
    # A bank photograph is its own element, always present (empty when there is
    # none), so the element tree keeps its shape and the monitor can change
    # without sending the photograph again (image bank, 2026-09-26).
    from image_scene import View, scene_photo_html
    photo_apart = isinstance(st.session_state.get('_scene_jobs'), View)
    if photo_apart:
        st.markdown(scene_photo_html(image if st.session_state.get('_scene_current', False) else None),
                    unsafe_allow_html=True)
    # A background image failure must never restart the whole app: a full rerun
    # here consumes form-submit events before the learner's order is processed.
    o = state['observable']
    import language as languages
    reading = languages.current()
    description = appearance_summary(state) + ' Work of breathing: ' + str(o.get('work_of_breathing', 'Not recorded'))
    if reading == 'es':
        # I-3: the summary and the work of breathing, each said whole (``language.examination``).
        description = (languages.examination(appearance_summary(state), 'es') + ' Trabajo respiratorio: '
                       + languages.observed_value(str(o.get('work_of_breathing', 'Not recorded')), 'es'))
    profile = state.get('ecg_profile', state.get('encounter_spec', {}).get('ecg_profile', 'baseline'))
    st.markdown(scene_html(image, monitor_html(o, time_label, profile, state.get('seed', 0), reading),
                          current=st.session_state.get('_scene_current', False),
                          pending=st.session_state.get('_scene_pending', False),
                          observations=description,
                          image_status=st.session_state.get('_scene_status'),
                          photo_apart=photo_apart, language=reading), unsafe_allow_html=True)


#: The ECG's words in Spanish (E-01 to E-05, XR-26, faculty, 2026-10-07).
ECG_WORDS_ES = {
    'ECG · 12 leads': 'ECG · 12 derivaciones',
    'Synthetic educational tracing · Clinical pattern validation pending.':
        'Trazado educativo sintético · Validación clínica del patrón pendiente.',
    'Download ECG': 'Descargar el ECG',
    'Acquire a 12-lead ECG at the current simulation time.':
        'Tomar un ECG de 12 derivaciones en el tiempo simulado actual.',
    '12-lead ECG acquired. Available in ECG recordings.': 'ECG de 12 derivaciones tomado. Está en «Registros de ECG».',
    'ECG recordings': 'Registros de ECG', 'Acquisition': 'Registro', 'View recording': 'Ver el registro',
    'ECG unavailable for this electrical state.': 'No se puede tomar un ECG en este estado eléctrico.',
    'ECG unavailable': 'ECG no disponible', 'Recording unavailable.': 'Registro no disponible.',
    'This electrical rhythm has no waveform model yet.': 'Este ritmo eléctrico todavía no tiene un modelo de trazado.',
    "Heart rate is outside this waveform model's range (20–300/min).":
        'La frecuencia cardíaca está fuera del rango de este modelo de trazado (20–300/min).',
    'Invalid heart rate.': 'Frecuencia cardíaca no válida.',
    'This ECG morphology profile has not been implemented.': 'Este perfil de morfología del ECG no está implementado.',
    'This morphology/rhythm combination has not been implemented.':
        'Esta combinación de morfología y ritmo no está implementada.',
    'Electrical morphology for PEA has not been specified.': 'La morfología eléctrica de la AESP no está especificada.',
    'This recording requires its original waveform model version.':
        'Este registro requiere la versión original de su modelo de trazado.',
}


def ecg_words(text, language=None):
    """One of the ECG's fixed sentences in the reading language; anything else as it came."""
    if language is None:
        import language as languages
        language = languages.current()
    return ECG_WORDS_ES.get(text, text) if language == 'es' else text


def _show_ecg(snapshot):
    """One recording, exactly as it was acquired. Viewing it acquires nothing and changes nothing."""
    from ecg12 import render_ecg_svg
    svg = render_ecg_svg(snapshot)
    st.markdown(''.join(line.strip() for line in svg.splitlines()), unsafe_allow_html=True)
    st.caption(ecg_words('Synthetic educational tracing · Clinical pattern validation pending.'))
    st.download_button(ecg_words('Download ECG'), svg, file_name='ecg_12_leads.svg', mime='image/svg+xml')


# A dialog's title is fixed when it is declared: one dialog per language.
_show_ecg_en = st.dialog('ECG · 12 leads', width='large')(_show_ecg)
_show_ecg_es = st.dialog(ECG_WORDS_ES['ECG · 12 leads'], width='large')(_show_ecg)


def show_ecg(snapshot):
    """Open one recording in the reading language's dialog."""
    import language as languages
    (_show_ecg_es if languages.current() == 'es' else _show_ecg_en)(snapshot)


def acquire_ecg_button(state, events):
    """Acquire a frozen 12-lead ECG at the current minute, announce it once and show it.

    Returns ``(acquired, notice)``: ``notice`` is what the room says when no tracing could be
    acquired, as ``(kind, text)`` with ``kind`` "info" or "error", for the caller to say where
    the room speaks -- the button sits in a one-line band.
    """
    from ecg12 import acquire_ecg
    # A closed encounter acquires nothing new; its recordings stay viewable.
    if st.session_state.get('encounter_ended') or not st.button(
            'ECG', help=ecg_words('Acquire a 12-lead ECG at the current simulation time.')):
        return False, None
    try:
        snapshot = acquire_ecg(state)
        if snapshot.get('status') != 'available':
            return False, ('info', ecg_words(snapshot.get('reason', 'ECG unavailable for this electrical state.')))
        state.setdefault('diagnostics', {}).setdefault('ecg', []).append(snapshot)
        # The record keeps the English sentence; the room says it in the reading language (render_event).
        events.append({'kind': 'diagnostic', 'time': state.get('sim_time', 0),
                       'text': '12-lead ECG acquired. Available in ECG recordings.'})
        show_ecg(snapshot)
        return True, None
    except ValueError as error:
        return False, ('error', ecg_words(str(error)))


def ecg_recordings(state):
    """Every recording of this encounter; viewing an older acquisition never changes its data."""
    recordings = state.get('diagnostics', {}).get('ecg', [])
    if recordings:
        with st.expander(ecg_words('ECG recordings')):
            recording = st.selectbox(ecg_words('Acquisition'), list(range(len(recordings))),
                                    format_func=lambda i: f"ECG {i+1} · {recordings[i].get('acquired_at_minutes', 0):g} min",
                                    index=len(recordings)-1)
            if st.button(ecg_words('View recording')):
                show_ecg(recordings[recording])


def image_tools(state):
    """Troubleshooting of the patient image: for faculty and administrators only.

    They are development controls, not part of the encounter (UX of the clinical
    encounter, 2026-10-02, section 10): the page draws them only for staff, and they
    keep the behaviour they had.
    """
    from clinical_scene import setting
    from patient_appearance import appearance_signature
    jobs = st.session_state.get('_scene_jobs')
    if jobs is not None and st.button('Image issue details', help='Inspect a rejected illustration separately for troubleshooting. It is not the current clinical image.'):
        diagnostic = getattr(jobs, 'diagnostic_candidate', None)
        candidate = diagnostic(appearance_signature(state)) if callable(diagnostic) else None
        if candidate:
            @st.dialog('Image issue · rejected illustration', width='large')
            def show_image_issue():
                from patient_appearance import _validated_image
                st.warning('Rejected illustration for troubleshooting only. Do not use it to interpret the clinical encounter.')
                st.image(_validated_image(candidate)[0], caption='Rejected candidate — not the current patient image.')
                st.caption(str(jobs.failure(appearance_signature(state)).get('reference', '')))
                evidence = getattr(jobs, 'diagnostic_evidence', lambda signature: ())
                for item in evidence(appearance_signature(state)):
                    st.text(f"Reviewer observation · {item['check']}: {item['finding']}")
            show_image_issue()
        else:
            st.info('No rejected illustration is available for this appearance.')
    retry_image = getattr(jobs, 'retry', None)
    if callable(retry_image) and not st.session_state.get('encounter_ended') and setting('OPENAI_API_KEY'):
        if st.button('Retry patient image', help='Recheck the saved image when available; otherwise create it. Your encounter and decisions are preserved.'):
            if retry_image(appearance_signature(state)):
                st.rerun()
            elif jobs.pending is not None:
                st.info('The patient image is still being prepared. Its progress appears beside the monitor.')


def study_upgrade(state):
    """A case saved before its studies were modelled can enable them; its state and results are kept."""
    from case_study_compatibility import missing_native_studies, upgrade_studies
    missing = missing_native_studies(state.get('encounter_spec', {}).get('clinical_case', {}))
    if missing:
        st.info('This saved case can enable modeled studies: ' + ', '.join(sorted(missing)) + '. Patient state and existing results are preserved.')
        if st.button('Enable modeled studies for this saved case'):
            upgrade_studies(state)
            st.rerun()
