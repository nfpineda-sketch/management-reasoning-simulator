"""Case-conditioned photography and source-only clinical exploration."""
import base64
import hashlib
import json
import os
import re
from io import BytesIO
from html import escape
from PIL import Image
import streamlit as st

SCENE_RENDER_VERSION = 12

# Defined in history_topics, a leaf module with no imports, so that a PDF
# renderer or a rubric declaration can read them without importing Streamlit
# and PIL through this module. Re-exported here for every existing reader.
from history_topics import HISTORY_TOPIC_LABELS          # noqa: F401  (re-export)


def _clinical_case(state):
    spec = state.get('encounter_spec') if isinstance(state, dict) else None
    case = spec.get('clinical_case') if isinstance(spec, dict) else None
    return case if isinstance(case, dict) else {}


def _case_history(state):
    history = _clinical_case(state).get('history')
    if not isinstance(history, dict):
        return {}
    return {key: [fact.strip() for fact in history[key]
                  if isinstance(fact, str) and fact.strip() and len(fact) <= 4000]
            for key in HISTORY_TOPIC_LABELS if isinstance(history.get(key), list)}


def history_topics(state):
    """Available authored topics, without hints about the hidden diagnosis."""
    return [HISTORY_TOPIC_LABELS[key] for key, facts in _case_history(state).items() if facts]


def history_topic_facts(state, topic):
    """Return isolated source sentences for a topic key or its UI label."""
    key = next((key for key, label in HISTORY_TOPIC_LABELS.items()
                if topic in (key, label)), None)
    return list(_case_history(state).get(key, []))


def _patient_description(state):
    spec = state.get('encounter_spec') or {}
    if isinstance(spec, dict) and 'clinical_case' in spec:
        patient = _clinical_case(state).get('patient')
        if not isinstance(patient, dict):
            raise ValueError('Patient demographics are not available for this encounter.')
        age, sex = patient.get('age_years'), patient.get('sex')
        if type(age) is not int or not 18 <= age <= 110 or sex not in ('male', 'female'):
            raise ValueError('Patient demographics are not supported for this encounter image.')
        return f"{age}-year-old {'man' if sex == 'male' else 'woman'}"
    legacy = {'PS001': '70-year-old man', 'PS002': '64-year-old woman'}
    if state.get('case_id') not in legacy:
        raise ValueError('Patient demographics are not available for this encounter.')
    return legacy[state['case_id']]


def setting(name, default=''):
    from offline_cases import withhold
    try:
        return withhold(name, str(st.secrets.get(name, os.environ.get(name, default))))
    except Exception:
        return withhold(name, os.environ.get(name, default))


def scene_prompt(state):
    person = _patient_description(state)
    from patient_appearance import appearance_state
    return scene_prompt_for(person, appearance_state(state))


def scene_prompt_for(person, visible):
    """The first photograph of a person in a visible state (the image bank passes an identity)."""
    from patient_appearance import contract_brief
    return ('Photorealistic emergency department encounter, clinician viewpoint from the foot of a bed. '
            'Wide landscape photograph with a lifelike fictional '+person+' in a hospital gown, '
            'head and hands clearly visible, body covered by a white blanket. Patient centered at 40% '
            'of image width, realistic hospital bay, soft clinical lighting, natural skin texture. '
            'Reserve the entire rightmost 34% for empty dark hospital wall; a live monitor will be '
            'composited there by software. No monitor screens anywhere, no numbers, text, logos, '
            'diagnostic labels, annotations, charts or UI. ECG electrodes, a BP cuff and finger '
            'oximeter. Add only the active support equipment explicitly listed in the observations. '
            'Do not invent wounds, cyanosis, bleeding or other clinical signs. Mottling is permitted only when explicitly true below. '
            'Depict only these established visible '
            'observations conservatively: '+json.dumps(visible)+'. '+contract_brief(visible)+' '
            'Clinical findings must remain visible and proportionate, not a posed wellness portrait. Documentary medical photography, '
            'not a cartoon, icon, diagram, doll or 3D game render.')


def generate_scene(state, api_key, model='gpt-image-1.5', client=None):
    from scene_errors import SceneImageError, provider_image_error
    if not api_key and client is None:
        raise SceneImageError('CONFIG', 'CREATE')
    try:
        prompt = scene_prompt(state)
    except (ValueError, TypeError, KeyError):
        raise SceneImageError('CONTRACT', 'CREATE') from None
    try:
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, timeout=120, max_retries=0)
        result = client.images.generate(model=model, prompt=prompt,
                                       size='1536x1024', quality='low', output_format='png', n=1)
    except Exception as error:
        raise provider_image_error(error, 'CREATE') from None
    from patient_appearance import _validated_image
    try:
        raw, _ = _validated_image(result.data[0].b64_json, output=True)
    except (ValueError, AttributeError, IndexError, TypeError):
        raise SceneImageError('INVALID_IMAGE', 'CREATE') from None
    return base64.b64encode(raw).decode('ascii')


def scene_image(state, events, context=None):
    """The current-state photograph: from the image bank with an account database, else per session."""
    import image_scene
    if image_scene.enabled(context):
        return image_scene.scene_image(state, events, context)
    return _session_scene_image(state, events, context)


def _session_scene_image(state, events, context=None):
    from functools import partial
    from patient_appearance import appearance_signature, APPEARANCE_VERSION
    from scene_pipeline import screened_scene, screened_appearance, screened_existing_scene, SCENE_PIPELINE_VERSION
    from scene_jobs import SceneJobs
    from scene_preparation import consume_prepared_scene
    arrival = next((e for e in events if e.get('kind') == 'presentation'), None)
    if not arrival:
        return None
    # Invalidate older unscreened pictures on a running session's hot update.
    spec = state.get('encounter_spec') or {}
    patient_identity = (state.get('case_id'), spec.get('content_sha256')) if spec.get('content_sha256') else (id(arrival), state.get('case_id'))
    key = (st.session_state.get('_attempt_id'), patient_identity,
           SCENE_RENDER_VERSION, APPEARANCE_VERSION, SCENE_PIPELINE_VERSION)
    if st.session_state.get('_scene_identity') != key or '_scene_jobs' not in st.session_state:
        previous = st.session_state.get('_scene_jobs')
        rejected = None
        prior_identity = st.session_state.get('_scene_identity')
        if previous is not None and isinstance(prior_identity, tuple) and prior_identity[:2] == key[:2]:
            diagnostic = getattr(previous, 'diagnostic_candidate', None)
            if callable(diagnostic):
                rejected = diagnostic(appearance_signature(state))
        if previous is not None:
            discard = getattr(previous, 'discard', None)
            if callable(discard):
                discard()
            else:
                # Objects already in a v0.17.2 session retain their old class
                # after importlib.reload. Drop them without invoking new APIs.
                pending = getattr(previous, 'pending', None)
                if pending is not None:
                    pending[1].cancel()
        st.session_state['_scene_identity'] = key
        st.session_state['_scene_jobs'] = consume_prepared_scene(
            st.session_state, state, st.session_state.get('_attempt_id')) or SceneJobs()
        if rejected and st.session_state['_scene_jobs'].base is None:
            from scene_pipeline import screened_existing_scene
            review_model = setting('MRS_IMAGE_REVIEW_MODEL', 'gpt-5-mini').strip() or 'gpt-5-mini'
            st.session_state['_scene_jobs'].review_candidate = partial(screened_existing_scene, rejected, review_model=review_model)
        st.session_state['_scene_failure_notified'] = None
    jobs = st.session_state['_scene_jobs']
    signature = appearance_signature(state)
    review_model = setting('MRS_IMAGE_REVIEW_MODEL', 'gpt-5-mini').strip() or 'gpt-5-mini'
    # The launch withholds the picture's key from a role the paid gate refuses and
    # from a case opened for review (faculty B1); the room used to read the key
    # itself and pay anyway (found 2026-09-26).
    from image_scene import generation_allowed
    role = ((context or {}).get('user') or {}).get('role')
    review_case = bool((st.session_state.get('encounter_assignment') or {}).get('review_case'))
    # Faculty decision 10 (2026-09-26): without an account database there is no
    # persistent budget, so this path pays for nothing.
    no_accounts = not (context or {}).get('store')
    if no_accounts or not generation_allowed(role, review_case):
        current = jobs.current(signature)
        st.session_state['_scene_current'] = current is not None
        st.session_state['_scene_failed'] = False
        st.session_state['_scene_pending'] = False
        st.session_state['_scene_status'] = {'state': 'unavailable',
                                             'code': 'NO_ACCOUNTS' if no_accounts else 'NOT_ALLOWED'}
        return current
    jobs.request(signature, state, setting('OPENAI_API_KEY'),
                 setting('MRS_IMAGE_MODEL', 'gpt-image-1.5'),
                 partial(screened_scene, review_model=review_model),
                 partial(screened_appearance, review_model=review_model),
                 progress_supported=True,
                 recheck=partial(screened_existing_scene, review_model=review_model))
    current = jobs.current(signature)
    st.session_state['_scene_current'] = current is not None
    st.session_state['_scene_failed'] = signature in jobs.failed
    st.session_state['_scene_pending'] = jobs.pending is not None
    st.session_state['_scene_status'] = jobs.status(signature)
    # A label cannot neutralize a contradictory visual cue. Never substitute a
    # previous appearance while the current one is pending, rejected or failed.
    return current


#: Shown, identically, beside every current photograph: a still image never
#: shows every finding, and saying WHICH ones it does not show would tell the
#: resident what the case defines before they examine. Neutral and constant,
#: its presence carries no information about this patient.
STILL_VIEW_NOTE = ('A still photograph does not show every clinical sign; '
                   'examine the patient to assess what it cannot carry.')
#: The same note in Spanish, in the faculty's wording (J-64, 2026-10-07).
STILL_VIEW_NOTE_ES = ('Una fotografía fija no muestra todos los signos clínicos; examina al paciente para evaluar lo '
                      'que no puede mostrar.')
#: The bed space's heading and its three states (M-02, faculty, 2026-10-07).
SCENE_WORDS_ES = {
    'ED / Bed 03': 'Urgencias / Cama 03',
    'Patient illustration · current state': 'Imagen del paciente · estado actual',
    'Updating patient appearance': 'Actualizando la apariencia del paciente',
    'Current patient image unavailable': 'Imagen actual del paciente no disponible',
}


def scene_html(image_b64, monitor, ecg='', *, current=True, pending=False, observations='', image_status=None,
               photo_apart=False, language='en'):
    """The bed space. With ``photo_apart`` the photograph is its own element (``image_scene``) and
    this overlay carries no image bytes, so a monitor change does not send the photograph again."""
    if not current:
        image_b64 = None
    current = bool(current and image_b64)
    ecg = ''.join(line.strip() for line in ecg.splitlines())
    mime = getattr(image_b64, 'mime', 'image/png')
    # The photograph is the scene's first layer, framed on the patient (image_scene.framing_style).
    photo = ''
    if image_b64 and not photo_apart:
        from image_scene import framing_style
        photo = (f'<div class="scene-photo-img" style="background-image:url(data:{mime};base64,{image_b64});'
                 f'{framing_style(image_b64)}"></div>')
    bg = 'background:transparent;' if image_b64 and photo_apart else ''
    status = 'Patient illustration · current state' if current else (
        'Updating patient appearance' if pending else 'Current patient image unavailable')
    spanish = language == 'es'
    place = SCENE_WORDS_ES['ED / Bed 03'] if spanish else 'ED / Bed 03'
    if spanish:
        status = SCENE_WORDS_ES[status]
    detail = scene_status_text(image_status, language) if not current else ''
    # One fixed sentence beside every photograph (faculty instruction of
    # 2026-09-26, point 6). Naming the findings a photograph does not show
    # told the resident what there was to find -- "breathing effort: not
    # discernible" says the case defines a breathing effort -- so the room's
    # warning is neutral and identical for every patient, and the specific
    # codes stay where they belong: the display log and the faculty's review
    # (image_scene._log, image_pack.read_observations).
    limitation = (STILL_VIEW_NOTE_ES if spanish else STILL_VIEW_NOTE) if current else ''
    # The monitor above, the patient below it: the monitor never covers the patient's head.
    return ("<style>" + BEDSPACE_CSS + "</style>" +
            '<div class="clinical-scene">' +
            f'<div class="scene-monitor">{monitor}{ecg}</div>' +
            f'<div class="scene-stage" style="{bg}">' + photo +
            f'<div class="scene-time">{escape(place)} · {escape(status)}</div>' +
            (f'<div class="scene-image-status" role="status">{escape(detail)}</div>' if detail else '') +
            (f'<div class="scene-observations scene-note" role="note">{limitation}</div>' if limitation else '') +
            (f'<div class="scene-observations">{escape(observations)}</div>' if not current else '') + '</div></div>')


def scene_status_text(status, language='en'):
    """Render only fixed labels and safe diagnostics; never job/provider text.

    In Spanish the room says why there is no photograph (M-03, faculty, 2026-10-07); the states
    that need an image key to prepare one are staff tools outside the pilot (X-1, §1, point 5).
    """
    if not isinstance(status, dict):
        return ''
    if language == 'es' and status.get('state') == 'unavailable' and status.get('code') in UNAVAILABLE_ES:
        return UNAVAILABLE_ES[status['code']]
    if status.get('state') == 'failed':
        from scene_errors import SceneImageError
        error = SceneImageError(status.get('code'), status.get('stage'), status.get('failed_checks', ()))
        detail = str(error)
        if error.code in ('MISMATCH', 'UNCERTAIN') and error.failed_checks:
            domains = {'expression': 'expression', 'gaze_and_eyelids': 'gaze and eyelids',
                       'skin_color': 'skin color', 'mottling': 'mottling', 'diaphoresis': 'sweating',
                       'respiratory_posture': 'breathing posture', 'respiratory_support': 'respiratory equipment',
                       'identity_and_framing': 'patient identity or framing',
                       'no_unrequested_signs': 'unrequested visible findings'}
            detail += ' Review flagged: ' + ', '.join(domains[key] for key in error.failed_checks) + '.'
        if status.get('correction_attempted') is True:
            detail += ' One image correction was attempted.'
        return detail
    if status.get('state') == 'unavailable' and status.get('code') in UNAVAILABLE:
        return UNAVAILABLE[status['code']]
    if status.get('state') == 'pending':
        labels = {'QUEUED': 'Waiting to prepare patient image', 'CREATE': 'Creating patient image',
                  'EDIT': 'Updating patient appearance', 'REPAIR': 'Correcting patient image',
                  'SCREEN': 'Checking patient appearance'}
        stage = 'QUEUED' if status.get('queued') is True else status.get('stage')
        label = labels.get(stage, 'Preparing patient image') if isinstance(stage, str) else 'Preparing patient image'
        elapsed = status.get('elapsed_seconds')
        return f'{label} · {int(elapsed)}s elapsed' if type(elapsed) in (int, float) and 0 <= elapsed < 86400 else label
    return ''


# Why there is no photograph of the current state (image bank, 2026-09-26). Fixed
# sentences: the monitor and the examination are current either way.
UNAVAILABLE = {
    'NOT_ALLOWED': 'No photograph is prepared for this encounter. The monitor and the examination are current.',
    'CONFIG': 'Patient image generation is not configured. The monitor and the examination are current.',
    'UNSUPPORTED': ('No synthetic patient in the image bank fits this case. The monitor and the examination '
                    'are current.'),
    'CONTRACT': ('This appearance has no supported photograph. The monitor and the examination are current.'),
    'UNRENDERABLE': ('The image generator could not draw this appearance reliably, so no photograph is requested. '
                     'The monitor and the examination are current.'),
    'REVIEW_PENDING': ('The photograph of this appearance is awaiting faculty review. The monitor and the '
                       'examination are current.'),
    'NO_ACCOUNTS': ('Without the account database there is no image budget, so no photograph is requested. The '
                    'monitor and the examination are current.'),
    'PRICE': ('The configured image model has no verified price, so no photograph is requested. The monitor '
              'and the examination are current.'),
    'BUDGET_DOLLARS': ('The image budget of this environment is used up; saved photographs are still shown. '
                       'The monitor and the examination are current.'),
    'BUDGET_REQUESTS': ('The image budget of this environment is used up; saved photographs are still shown. '
                        'The monitor and the examination are current.'),
    'BUDGET_CONFIG': 'The image budget is not configured correctly. The monitor and the examination are current.',
    'INTERNAL': 'The saved photograph could not be read. The monitor and the examination are current.',
}
#: The same notices in Spanish (M-03, XR-25, faculty, 2026-10-07). NO_ACCOUNTS is left out: the
#: pilot runs with accounts.
_CURRENT_ES = ' El monitor y el examen están al día.'
UNAVAILABLE_ES = {
    'NOT_ALLOWED': 'No hay una fotografía preparada para este encuentro.' + _CURRENT_ES,
    'CONFIG': 'La generación de imágenes del paciente no está configurada.' + _CURRENT_ES,
    'UNSUPPORTED': 'Ningún paciente sintético del banco de imágenes corresponde a este caso.' + _CURRENT_ES,
    'CONTRACT': 'Esta apariencia no tiene una fotografía disponible.' + _CURRENT_ES,
    'UNRENDERABLE': ('El generador de imágenes no pudo dibujar esta apariencia de forma confiable, así que no se pide '
                     'una fotografía.' + _CURRENT_ES),
    'REVIEW_PENDING': 'La fotografía de esta apariencia espera la revisión docente.' + _CURRENT_ES,
    'PRICE': ('El modelo de imágenes configurado no tiene un precio verificado, así que no se pide una '
              'fotografía.' + _CURRENT_ES),
    'BUDGET_DOLLARS': ('El presupuesto de imágenes de este entorno se agotó; las fotografías guardadas se siguen '
                       'mostrando.' + _CURRENT_ES),
    'BUDGET_REQUESTS': ('El presupuesto de imágenes de este entorno se agotó; las fotografías guardadas se siguen '
                        'mostrando.' + _CURRENT_ES),
    'BUDGET_CONFIG': 'El presupuesto de imágenes no está bien configurado.' + _CURRENT_ES,
    'INTERNAL': 'No se pudo leer la fotografía guardada.' + _CURRENT_ES,
}


# The room's layers are fixed to the main area, not to the window: a transformed
# element is the containing block of its fixed descendants. Against the window,
# Streamlit's open sidebar covered the room's left edge -- the minute and the
# start of the note on what the photograph cannot show (2026-09-26). On a phone
# the room is stacked: the patient above, the information and the writing below.
#
# UX of the clinical encounter (faculty instruction of 2026-10-02): the patient on
# the left half, nearly its whole height, with a compact monitor over its upper left
# corner; on the right half the information above (it scrolls on its own) and the
# writing area below, always in view. During the encounter the sidebar is not drawn
# at all (the room's menu replaces it), so the two halves share the whole width.
BEDSPACE_CSS = """
[data-testid="stMain"]{transform:translate(0)}
[data-testid="stMain"]{--scene-w:calc(50vw - 1.5rem);--mon-val:clamp(20px,2.65vw,42px);--scene-gap:.6rem;
 --note-h:2.6rem;--note-gap:.35rem;--mon-h:calc(68px + (var(--scene-w) - 30px) / 6 + 1.05 * var(--mon-val))}
.clinical-scene{position:fixed;top:3.4rem;bottom:1rem;left:1rem;width:calc(50% - 1.5rem);z-index:1}
.scene-stage,.scene-photo{background:#18252e;border-radius:14px;overflow:hidden;container-type:size}
.scene-stage{position:absolute;left:0;right:0;top:calc(var(--mon-h) + var(--scene-gap));bottom:0}
.scene-photo{position:fixed;top:calc(3.4rem + var(--mon-h) + var(--scene-gap));bottom:calc(1rem + var(--note-h) + var(--note-gap));
 left:1rem;width:calc(50% - 1.5rem);z-index:0}
.scene-photo-empty{display:none}
.scene-photo-img{position:absolute;inset:0;background-repeat:no-repeat;background-size:var(--fw) auto;
 --fw:max(calc(100cqw * var(--fz,1)),calc(var(--ph,100cqh) * var(--fa,1.5)));
 background-position:clamp(calc(100cqw - var(--fw)),calc(50cqw - var(--fx,.5) * var(--fw)),0px) 30%}
.scene-stage:has(.scene-note) .scene-photo-img{bottom:calc(var(--note-h) + var(--note-gap));
 --ph:calc(100cqh - var(--note-h) - var(--note-gap))}
.scene-monitor{position:absolute;top:0;left:0;right:0;box-sizing:border-box;background:linear-gradient(180deg,#0c1f2e,#06121b);
 border:1px solid #3b5a6e;border-radius:12px;box-shadow:0 6px 18px #08131b40,inset 0 1px 0 #ffffff1a;overflow:hidden}
.monitor-body{padding:8px 14px 10px}
.monitor-heading{color:#b8cedc;font:700 10.5px/1.3 system-ui,sans-serif;letter-spacing:.1em;height:22px;
 display:flex;align-items:center;padding-right:4.4rem}
.scene-monitor svg{display:block;width:100%;height:auto;margin:4px 0 6px;border-radius:6px}
.monitor-values{display:grid;grid-template-columns:repeat(4,auto);justify-content:space-between;column-gap:.7rem;min-width:0}
.monitor-values>div{min-width:0}
.monitor-values small{display:block;font:700 11px/14px system-ui,sans-serif;letter-spacing:.03em;white-space:nowrap}
.monitor-unit{opacity:.75;font-weight:500}
.monitor-value{font:700 var(--mon-val)/1.05 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:nowrap}
.scene-time{position:absolute;right:.8rem;top:.8rem;max-width:calc(100% - 1.6rem);background:#08131cb3;color:#e8eff4;padding:4px 11px;
 font:500 11.5px/1.35 system-ui,sans-serif;border-radius:999px;backdrop-filter:blur(3px)}
.scene-observations{position:absolute;left:.8rem;bottom:.8rem;width:fit-content;max-width:calc(100% - 1.6rem);
 background:#0c1822e0;color:#f1f6f9;padding:8px 12px;border-radius:10px;font:13px/1.45 system-ui,sans-serif;
 border:1px solid #ffffff1a;box-shadow:0 4px 16px #0006}
.scene-note{top:auto;left:0;right:0;bottom:0;width:auto;max-width:none;min-height:var(--note-h);box-sizing:border-box;
 display:flex;align-items:center;justify-content:center;gap:.55rem;padding:4px 12px;background:#f3f6f9;color:#2c3e50;
 border:1px solid #d6dfe7;border-radius:10px;font:12.5px/1.35 system-ui,sans-serif;box-shadow:none}
.scene-note::before{content:"i";flex:0 0 auto;width:15px;height:15px;border:1.4px solid currentColor;border-radius:50%;
 font:700 10px/12.6px Georgia,serif;text-align:center;opacity:.8}
.scene-image-status{position:absolute;left:.8rem;top:42%;max-width:calc(100% - 1.6rem);color:#dce8ef;
 font:15px/1.5 system-ui;padding:12px;background:#0e1b24;border-radius:8px}
.st-key-encounter-console{position:fixed!important;top:3.4rem;bottom:1rem;right:1rem;width:calc(50% - 1.5rem)!important;
 display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;gap:.5rem!important;
 overflow:hidden!important;z-index:2;background:#fff;padding:12px 14px;border:1px solid #cfdae3;
 border-radius:14px;box-shadow:0 10px 30px rgba(15,35,55,.12);color:#122130;color-scheme:light}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]{width:100%;min-width:0}
.st-key-enc-status{position:fixed!important;top:.5rem;left:calc(50% + .5rem);right:15rem;z-index:999991;
 display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;align-items:center;gap:1rem;width:auto!important}
.st-key-enc-status>div{width:auto!important;flex:0 0 auto}
.st-key-enc-ecg{position:fixed!important;z-index:999990;width:3.9rem!important;top:calc(3.4rem + 6px);
 left:calc(50% - .5rem - 3.9rem - 14px)}
.st-key-enc-ecg [data-testid="stElementContainer"],.st-key-enc-ecg .stButton{width:100%!important}
.st-key-enc-ecg button{width:100%;min-height:1.55rem;height:1.55rem;padding:0 .4rem;background:#12301f;color:#c9f7dd;
 border:1px solid #3d8c69;border-radius:7px}
.st-key-enc-ecg button p{font-size:.72rem;font-weight:800;letter-spacing:.08em}
.st-key-enc-ecg button:hover{color:#fff;border-color:#72efa5;background:#18402a}
.st-key-enc-feedback{padding:6px 10px!important;gap:.25rem!important;border-left:4px solid #7f93a4!important;background:#fbfcfd}
.st-key-enc-feedback:has(.enc-order--outcome){border-left-color:#cf2f47!important;background:#fffafb}
.st-key-enc-feedback:has([data-testid="stAlert"],.enc-order--held){border-left-color:#b45309!important;background:#fffcf3}
.st-key-enc-feedback [data-testid="stMarkdownContainer"],.st-key-enc-feedback [data-testid="stCaptionContainer"]{margin-bottom:0!important}
.st-key-enc-feedback p,.st-key-enc-feedback li{font-size:.9rem;margin:0 0 .15rem!important}
.st-key-enc-feedback [data-testid="stCaptionContainer"] p{color:#0b4f9c;font-weight:600}
[data-testid="stMarkdownContainer"]:has(>.enc-title,>.enc-order,>.enc-clock,>.enc-ev-head){margin-bottom:0!important}
.st-key-enc-feedback [data-testid="stAlert"]{padding:.4rem .6rem}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-info){flex:1 1 0;min-height:20%;
 overflow-y:auto;overflow-x:hidden;padding-right:4px}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-action){flex:0 0 auto;max-height:66%;
 overflow-y:auto;overflow-x:hidden;border-top:2px solid #d5dee6;padding-top:.5rem}
.st-key-encounter-console:has([class*="st-key-reasoning_model_"],.st-key-close_kind)>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-action){max-height:84%}
.st-key-encounter-console:has([class*="st-key-reasoning_model_"],.st-key-close_kind)>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-info){min-height:10%}
.st-key-enc-info [data-testid="stTabs"] [role="tablist"]{position:sticky;top:0;z-index:3;background:#fff;gap:.2rem}
.st-key-enc-info [role="tab"]{padding:.3rem .7rem!important;border-radius:8px 8px 0 0}
.st-key-enc-info [role="tab"] p{font-weight:650;color:#4a5b6b}
.st-key-enc-info [role="tab"][aria-selected="true"]{background:#e9f1fc}
.st-key-enc-info [role="tab"][aria-selected="true"] p{color:#0b4f9c;font-weight:800}
.st-key-enc-info [role="tab"] .react-aria-SelectionIndicator{background-color:#1d5fbf!important;border-color:#1d5fbf!important}
.st-key-enc-pending{background:#fff8ea;border:1px solid #f3d38c;border-radius:9px;padding:4px 10px!important}
.st-key-enc-pending p{color:#7a4a00!important;font-weight:650}
.enc-title{font:800 clamp(.95rem,1.15vw,1.08rem)/1.3 system-ui;color:#0f2b40;white-space:nowrap}
.st-key-enc-action h4{font-size:.98rem!important;padding:.2rem 0 0!important}
.st-key-encounter-console .mrs-vitals-grid--response{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:8px}
.st-key-encounter-console .mrs-vital-cell{min-width:0;border:1px solid #d7e0e8;border-radius:8px;background:#fff;padding:6px 8px}
.st-key-encounter-console .mrs-vital-label{color:#5f7184;font-size:.62rem;font-weight:800;letter-spacing:.04em;line-height:1.2;text-transform:uppercase}
.st-key-encounter-console .mrs-vital-value{color:#172433;font-size:.88rem;font-weight:700;line-height:1.25;margin-top:3px;overflow-wrap:anywhere}
.st-key-encounter-console [data-testid="stForm"]{padding:8px 10px}
.st-key-encounter-console [data-testid="stCaptionContainer"]{font-size:.82rem}
.st-key-enc-action [data-testid="stCaptionContainer"] p{font-size:.78rem;line-height:1.35}
.st-key-encounter-console [data-testid="stVerticalBlock"]{gap:.5rem}
.st-key-encounter-console [data-testid="stExpander"]{background:#f7f9fb}
.st-key-encounter-console [data-testid="stMarkdownContainer"]{overflow-wrap:anywhere}
.enc-clock{font:800 1.02rem/1.2 system-ui;color:#0f2b40;white-space:nowrap;background:#eef3f8;border:1px solid #d3dee8;
 border-radius:999px;padding:.32rem .95rem}
.enc-order{white-space:normal;overflow-wrap:anywhere;font-size:.9rem;color:#33424f}
.enc-order--words{color:#1f2d3a;background:#fff;border:1px solid #dde3ea;border-radius:7px;padding:4px 8px;font-style:italic}
.enc-order--outcome strong{color:#1f2d3a}
.enc-order--held strong{color:#8a4b00}
[class*="st-key-enc-ev-"]{position:relative;gap:.2rem!important;padding:7px 11px 6px 12px!important;border-radius:9px!important;
 background:var(--evbg,#f7f9fb)!important;border:1px solid var(--evb,#e1e7ed)!important;border-left:4px solid var(--evc,#8a9aa8)!important}
[class*="st-key-enc-ev-talk-"]{--evc:#2563eb;--evbg:#f4f8ff;--evb:#d7e4fb}
[class*="st-key-enc-ev-examine-"]{--evc:#0d8a5f;--evbg:#f2fbf7;--evb:#cdebdc}
[class*="st-key-enc-ev-tests-"]{--evc:#7444cc;--evbg:#f8f5ff;--evb:#e2d9f7}
[class*="st-key-enc-ev-treat-"]{--evc:#cf2f47;--evbg:#fff6f7;--evb:#f5d3d9}
[class*="st-key-enc-ev-response-"]{--evc:#0b7f8a;--evbg:#f1fbfc;--evb:#c9ebee}
[class*="st-key-enc-ev-alert-"]{--evc:#b45309;--evbg:#fffaec;--evb:#f3e0aa}
[class*="st-key-enc-ev-resident-"]{--evc:#3e4c5e;--evbg:#f6f7f9;--evb:#dde2e8}
[class*="st-key-enc-ev-arrival-"]{--evc:#48616f;--evbg:#f6f9fb;--evb:#d9e3ea}
[class*="st-key-enc-ev-"] [data-testid="stVerticalBlock"]{border:0!important;padding:0!important;background:transparent!important}
.enc-ev-head{display:flex;align-items:center;gap:.5rem;margin:0 0 .1rem!important}
.enc-ev-head strong{display:contents}
.enc-ev-label{color:var(--evc,#33424f);font:800 .72rem/1.3 system-ui,sans-serif;letter-spacing:.07em;text-transform:uppercase}
.enc-ev-sep{display:none}
.enc-ev-time{order:-1;flex:0 0 auto;font:700 .72rem/1 system-ui,sans-serif;color:#33424f;background:#fff;
 border:1px solid var(--evb,#d9e1e8);border-radius:999px;padding:.2rem .5rem}
[class*="st-key-enc-ev-"] .stButton button{min-height:1.9rem;padding:.12rem .75rem;background:#fff;color:var(--evc);
 border:1px solid var(--evc);border-radius:8px}
[class*="st-key-enc-ev-"] .stButton button p{font-size:.84rem;font-weight:700}
.st-key-enc-modes [data-testid="stElementContainer"],.st-key-enc-modes .stRadio{width:100%!important}
.st-key-enc-modes [role="radiogroup"]{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:.4rem;width:100%}
.st-key-enc-modes [role="radiogroup"]>div:nth-child(1){--m:#2563eb;--mbg:#eef4ff;--mbd:#bdd2fa}
.st-key-enc-modes [role="radiogroup"]>div:nth-child(2){--m:#0d8a5f;--mbg:#ebf8f2;--mbd:#b4e2cc}
.st-key-enc-modes [role="radiogroup"]>div:nth-child(3){--m:#7444cc;--mbg:#f4effe;--mbd:#d4c6f3}
.st-key-enc-modes [role="radiogroup"]>div:nth-child(4){--m:#cf2f47;--mbg:#fff0f2;--mbd:#f3c2ca}
.st-key-enc-modes label[data-testid="stRadioOption"]{border:1.5px solid var(--mbd,#9fb3bf);border-radius:10px;padding:.42rem .5rem;
 justify-content:center;margin:0!important;background:var(--mbg,#fff);cursor:pointer}
.st-key-enc-modes label[data-testid="stRadioOption"] p{color:var(--m,#28404f);font-weight:650}
.st-key-enc-modes label[data-testid="stRadioOption"]>div>div:not([data-testid="stMarkdownContainer"]){display:none}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked){background:var(--m,#0b5cad);border:2px solid var(--m,#062f5c);
 box-shadow:0 4px 12px -4px var(--m,#0b5cad)}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked) p{color:#fff;font-weight:800}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked) p::before{content:"\\2713\\00a0"}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:focus-visible){outline:3px solid #f59e0b;outline-offset:2px}
.st-key-encounter-console [data-testid="stForm"]:has(textarea:not([disabled])),
.st-key-encounter-console [data-testid="stForm"]:has(input[type="text"]){border:2px solid #1d5fbf;border-radius:12px;background:#fff;
 box-shadow:0 6px 18px -10px rgba(29,95,191,.55);padding:10px 12px}
.st-key-encounter-console [data-testid="stForm"] textarea{font-size:.97rem;line-height:1.45}
.st-key-encounter-console [data-testid="stForm"]:has(textarea[aria-label="Enter your clinical reasoning and/or actions"])>[data-testid="stVerticalBlock"],
.st-key-encounter-console [data-testid="stForm"]:has(input[type="text"])>[data-testid="stVerticalBlock"]{display:grid!important;
 grid-template-columns:minmax(0,1fr) auto;align-items:end;column-gap:.65rem;row-gap:.4rem}
.st-key-encounter-console [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
.st-key-encounter-console [data-testid="stForm"]:has(input[type="text"]) [data-testid="stFormSubmitButton"] button{background:#1d5fbf;
 border:1px solid #1d5fbf;color:#fff;min-height:2.45rem;padding:.3rem 1.5rem;box-shadow:0 4px 12px -5px rgba(29,95,191,.8)}
.st-key-encounter-console [data-testid="stFormSubmitButton"] button p{font-weight:800}
.st-key-encounter-console [data-testid="stFormSubmitButton"] button:hover{background:#174d9b;border-color:#174d9b;color:#fff}
.st-key-enc-action>[data-testid="stElementContainer"]:has([data-testid="stSelectbox"])+[data-testid="stElementContainer"] .stButton button{
 background:#0d8a5f;border:1px solid #0d8a5f;color:#fff;min-height:2.3rem;padding:.3rem 1.3rem}
.st-key-enc-action>[data-testid="stElementContainer"]:has([data-testid="stSelectbox"])+[data-testid="stElementContainer"] .stButton button p{font-weight:800}
.st-key-cancel_pending_orders button{color:#8a4b00;border-color:#e8c27a;background:#fffaf0}
.st-key-enc-close{padding-top:.35rem!important;border-top:1px dashed #d5dde5;align-items:flex-end}
.st-key-enc-close .stButton button{min-height:1.8rem;padding:.12rem .8rem;color:#475569;background:#f8fafc;border:1px solid #c5d0da}
.st-key-enc-close .stButton button p{font-size:.84rem;font-weight:600}
@media(max-width:760px){
 /* One column that scrolls: monitor, then the patient, the photograph's note, and the console below. */
 [data-testid="stMain"]{--scene-w:calc(100vw - .8rem);--mon-val:clamp(18px,5.6vw,28px);--scene-gap:.4rem;--note-gap:.3rem;
  --note-h:2.75rem;--pic-h:calc(var(--scene-w) * .75);--mon-h:calc(51px + (var(--scene-w) - 20px) / 6 + 1.05 * var(--mon-val));
  --console-top:calc(5.6rem + var(--mon-h) + var(--scene-gap) + var(--pic-h) + var(--note-gap) + var(--note-h) + .6rem)}
 .clinical-scene{top:5.6rem;left:.4rem;right:.4rem;width:auto;bottom:auto;
  height:calc(var(--mon-h) + var(--scene-gap) + var(--pic-h) + var(--note-gap) + var(--note-h))}
 .scene-photo{top:calc(5.6rem + var(--mon-h) + var(--scene-gap));left:.4rem;right:.4rem;width:auto;bottom:auto;height:var(--pic-h)}
 .monitor-body{padding:5px 9px 6px}
 .monitor-heading{font-size:9px;height:19px;padding-right:3.6rem}
 .scene-monitor svg{margin:2px 0 3px}
 .monitor-values small{font-size:9.5px;line-height:12px}
 .scene-time{font-size:10px;padding:3px 8px;max-width:calc(100% - 1rem)}
 .scene-observations{font-size:11px;padding:5px}
 .scene-note{font-size:12px;padding:3px 10px}
 .scene-image-status{font-size:11px;padding:6px;top:55%}
 .st-key-enc-ecg{width:3.2rem!important;top:calc(5.6rem + 4px);left:auto;right:calc(.4rem + 9px)}
 .st-key-enc-ecg button{min-height:1.3rem;height:1.3rem}
 .st-key-enc-ecg button p{font-size:.64rem}
 .st-key-encounter-console{left:.4rem;right:.4rem;width:auto!important;top:var(--console-top);bottom:auto;
  height:calc(100vh - 4.4rem);height:calc(100dvh - 4.4rem);padding:8px}
 /* The header is transparent (encounter_screen.MENU_CSS) and the page scrolls under it: Streamlit's own
    buttons get a backing, so that they never sit on the text or the photograph. */
 [data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],
 [data-testid="stStatusWidget"]{background:#ffffff;border-radius:8px}
 .st-key-enc-status{top:3rem;left:.4rem;right:.4rem;gap:.5rem;justify-content:space-between}
 .enc-clock{font-size:.95rem}
}
@media(max-width:379px){[data-testid="stMain"]{--note-h:3.75rem}}
@media(min-width:761px) and (max-width:800px){[data-testid="stMain"]{--note-h:3.6rem}}
@media(prefers-reduced-motion:reduce){.scene-monitor *{animation:none!important}}
"""


def history_facts(presentation, case_id, *, state=None):
    if isinstance(state, dict) and 'clinical_case' in (state.get('encounter_spec') or {}):
        return list(dict.fromkeys(fact for facts in _case_history(state).values() for fact in facts))
    # Every original sentence is retained; no generated clinical content.
    facts = re.split(r'(?<=[.!?])\s+', presentation.strip())
    if case_id == 'PS002':
        facts += ['I have felt feverish and had chills since last night.', 'I have a new cough with phlegm.', 'I have no burning when I urinate or pain in my flank.', 'I have not vomited or noticed any bleeding.']
    elif case_id == 'PS001':
        facts += ['It has burned when I urinate for two days, and I have been going more often.', 'I have had chills.', 'I have not been eating or drinking much.', 'I have felt progressively weaker today.', 'I have no chest pain.', 'I have not noticed gastrointestinal bleeding.', 'I have not had vomiting or diarrhea.', 'I have no cough or focal neurological symptoms.']
    return [f for f in facts if not re.search(r'BP |blood pressure|heart rate|SpO|capillary|extremities|ECG|Respiratory rate|speaking in short|alert|external bleeding|cause of her', f, re.I)]


def associated_symptoms(facts, *, state=None):
    if isinstance(state, dict) and 'clinical_case' in (state.get('encounter_spec') or {}):
        from patient_conversation import NOT_DOCUMENTED
        return ' '.join(history_topic_facts(state, 'associated_symptoms')[:2]) or NOT_DOCUMENTED
    # Keep an informative positive symptom available immediately, but do not
    # turn a broad question into a complete review of systems or a diagnosis.
    positives = [f for f in facts if f.startswith(("It has burned", "I have had chills", "I have felt feverish", "I have a new cough"))]
    return " ".join(positives[:2])


def answer_history(question, facts, api_key='', client=None, *, state=None):
    from patient_conversation import answer_from_sources
    model = setting('MRS_CONVERSATION_MODEL', setting('OPENAI_MODEL', 'gpt-5-mini')).strip() or 'gpt-5-mini'
    authored = None
    if isinstance(state, dict) and 'clinical_case' in (state.get('encounter_spec') or {}):
        authored = _case_history(state)
        # Source selection is tied to this encounter even if a caller holds an
        # older list from a previously viewed patient.
        facts = history_facts('', state.get('case_id'), state=state)
    return answer_from_sources(question, facts, api_key=api_key, model=model, client=client,
                               history=authored)
