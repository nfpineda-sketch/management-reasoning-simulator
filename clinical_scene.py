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


def scene_html(image_b64, monitor, ecg='', *, current=True, pending=False, observations='', image_status=None,
               photo_apart=False):
    """The bed space. With ``photo_apart`` the photograph is its own element (``image_scene``) and
    this overlay carries no image bytes, so a monitor change does not send the photograph again."""
    if not current:
        image_b64 = None
    current = bool(current and image_b64)
    ecg = ''.join(line.strip() for line in ecg.splitlines())
    mime = getattr(image_b64, 'mime', 'image/png')
    bg = (f'background-image:url(data:{mime};base64,{image_b64});' if image_b64 and not photo_apart else
          ('background:transparent;' if image_b64 else ''))
    status = 'Patient illustration · current state' if current else (
        'Updating patient appearance' if pending else 'Current patient image unavailable')
    detail = scene_status_text(image_status) if not current else ''
    # One fixed sentence beside every photograph (faculty instruction of
    # 2026-09-26, point 6). Naming the findings a photograph does not show
    # told the resident what there was to find -- "breathing effort: not
    # discernible" says the case defines a breathing effort -- so the room's
    # warning is neutral and identical for every patient, and the specific
    # codes stay where they belong: the display log and the faculty's review
    # (image_scene._log, image_pack.read_observations).
    limitation = STILL_VIEW_NOTE if current else ''
    return ("<style>" + BEDSPACE_CSS + "</style>" +
            f'<div class="clinical-scene" style="{bg}">' +
            f'<div class="scene-monitor">{monitor}{ecg}</div>' +
            f'<div class="scene-time">ED / Bed 03 · {escape(status)}</div>' +
            (f'<div class="scene-image-status" role="status">{escape(detail)}</div>' if detail else '') +
            (f'<div class="scene-observations">{limitation}</div>' if limitation else '') +
            (f'<div class="scene-observations">{escape(observations)}</div>' if not current else '') + '</div>')


def scene_status_text(status):
    """Render only fixed labels and safe diagnostics; never job/provider text."""
    if not isinstance(status, dict):
        return ''
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
.clinical-scene{position:fixed;top:3.4rem;bottom:1rem;left:1rem;width:calc(50% - 1.5rem);background:#18252e;
 background-size:cover;background-position:center;border-radius:14px;overflow:hidden;z-index:1}
.scene-photo{position:fixed;top:3.4rem;bottom:1rem;left:1rem;width:calc(50% - 1.5rem);background-size:cover;
 background-position:center;border-radius:14px;overflow:hidden;z-index:0}
.scene-photo-empty{display:none}
.scene-monitor{position:absolute;left:.7rem;top:.7rem;width:min(44%,24rem);background:#07141df0;
 border:2px solid #263a48;border-radius:10px;box-shadow:0 6px 18px #0008;overflow:hidden}
.monitor-body{padding:4px 9px 6px}
.monitor-heading{color:#c3d4df;font:10px/1.3 monospace;letter-spacing:.04em}
.scene-monitor svg{width:100%;height:auto;display:block;max-height:5.5vh}
.monitor-values{display:grid;grid-template-columns:repeat(4,auto);justify-content:space-between;column-gap:.5rem;min-width:0}
.monitor-values>div{min-width:0}
.monitor-values small{font-size:10px;white-space:nowrap}.monitor-unit{opacity:.75}
.monitor-value{font:700 clamp(15px,1.45vw,26px)/1.1 monospace;white-space:nowrap}
.scene-time{position:absolute;right:0;top:0;background:#000b;color:#eee;padding:6px 12px;font:12px system-ui;
 max-width:48%;border-bottom-left-radius:8px}
.scene-observations{position:absolute;left:.8rem;bottom:.8rem;width:fit-content;max-width:calc(100% - 1.6rem);
 background:#17222eee;color:white;padding:8px 12px;border-radius:8px;font:13px/1.4 system-ui}
.scene-image-status{position:absolute;left:.8rem;top:42%;max-width:calc(100% - 1.6rem);color:#dce8ef;
 font:15px/1.5 system-ui;padding:12px;background:#0e1b24;border-radius:8px}
.st-key-encounter-console{position:fixed!important;top:3.4rem;bottom:1rem;right:1rem;width:calc(50% - 1.5rem)!important;
 display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;gap:.5rem!important;
 overflow:hidden!important;z-index:2;background:rgba(248,250,252,.98);padding:12px 14px;border:1px solid #b8c6cd;
 border-radius:12px;box-shadow:0 8px 28px #0003;color:#17232d;color-scheme:light}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]{width:100%;min-width:0}
.st-key-enc-status{position:fixed!important;top:.5rem;left:calc(50% + .5rem);right:15rem;z-index:999991;
 display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;align-items:center;gap:1rem;width:auto!important}
.st-key-enc-status>div{width:auto!important;flex:0 0 auto}
.st-key-enc-status button{min-height:2.1rem;padding:.2rem .9rem}
.st-key-enc-feedback{padding:6px 10px!important;gap:.25rem!important}
.st-key-enc-feedback [data-testid="stMarkdownContainer"],.st-key-enc-feedback [data-testid="stCaptionContainer"]{margin-bottom:0!important}
.st-key-enc-feedback p,.st-key-enc-feedback li{font-size:.9rem;margin:0 0 .15rem!important}
[data-testid="stMarkdownContainer"]:has(>.enc-title,>.enc-order,>.enc-clock){margin-bottom:0!important}
.st-key-enc-feedback [data-testid="stAlert"]{padding:.4rem .6rem}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-info){flex:1 1 0;min-height:20%;
 overflow-y:auto;overflow-x:hidden;padding-right:4px}
.st-key-encounter-console>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-action){flex:0 0 auto;max-height:66%;
 overflow-y:auto;overflow-x:hidden;border-top:2px solid #cfd8dc;padding-top:.5rem}
.st-key-encounter-console:has([class*="st-key-reasoning_model_"],.st-key-close_kind)>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-action){max-height:84%}
.st-key-encounter-console:has([class*="st-key-reasoning_model_"],.st-key-close_kind)>[data-testid="stLayoutWrapper"]:has(>.st-key-enc-info){min-height:10%}
.st-key-enc-info [data-testid="stTabs"] [role="tablist"]{position:sticky;top:0;z-index:3;background:#f8fafc}
.enc-title{font:700 clamp(.9rem,1.1vw,1.05rem)/1.3 system-ui;color:#0f2b40;white-space:nowrap}
.st-key-enc-action h4{font-size:.98rem!important;padding:.2rem 0 0!important}
.st-key-encounter-console .mrs-vitals-grid--response{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:8px}
.st-key-encounter-console .mrs-vital-cell{min-width:0;border:1px solid #d7e0e8;border-radius:8px;background:#f7fafc;padding:6px 8px}
.st-key-encounter-console .mrs-vital-label{color:#667789;font-size:.62rem;font-weight:800;letter-spacing:.04em;line-height:1.2;text-transform:uppercase}
.st-key-encounter-console .mrs-vital-value{color:#172433;font-size:.88rem;font-weight:700;line-height:1.25;margin-top:3px;overflow-wrap:anywhere}
.st-key-encounter-console [data-testid="stForm"]{padding:8px 10px}
.st-key-encounter-console [data-testid="stCaptionContainer"]{font-size:.82rem}
.st-key-encounter-console [data-testid="stVerticalBlock"]{gap:.5rem}
.st-key-encounter-console [data-testid="stExpander"]{background:#f7f9fb}
.st-key-encounter-console [data-testid="stMarkdownContainer"]{overflow-wrap:anywhere}
.enc-clock{font:700 1.1rem/1.3 system-ui;color:#0f2b40;white-space:nowrap}
.enc-order{white-space:normal;overflow-wrap:anywhere;font-size:.9rem;color:#33424f}
.st-key-enc-modes [data-testid="stElementContainer"],.st-key-enc-modes .stRadio{width:100%!important}
.st-key-enc-modes [role="radiogroup"]{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:.4rem;width:100%}
.st-key-enc-modes label[data-testid="stRadioOption"]{border:1px solid #9fb3bf;border-radius:10px;padding:.4rem .5rem;
 justify-content:center;margin:0!important;background:#fff;color:#28404f;cursor:pointer}
.st-key-enc-modes label[data-testid="stRadioOption"]>div>div:not([data-testid="stMarkdownContainer"]){display:none}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked){background:#0b5cad;border:2px solid #062f5c;color:#fff}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked) p{font-weight:700}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:checked) p::before{content:"\\2713\\00a0"}
.st-key-enc-modes label[data-testid="stRadioOption"]:has(input:focus-visible){outline:3px solid #f59e0b;outline-offset:2px}
@media(max-width:760px){
 .clinical-scene,.scene-photo{top:5.6rem;left:.4rem;right:.4rem;width:auto;bottom:auto;height:36vh}
 .scene-monitor{width:56%;left:.4rem;top:.4rem}
 .monitor-values{grid-template-columns:repeat(2,auto)}
 .scene-time{font-size:10px;padding:4px}
 .scene-observations{font-size:11px;padding:5px}
 .scene-image-status{font-size:11px;padding:6px;top:55%}
 .st-key-encounter-console{left:.4rem;right:.4rem;width:auto!important;top:calc(5.6rem + 37vh);bottom:.4rem;padding:8px}
 .st-key-enc-status{top:3rem;left:.4rem;right:.4rem;gap:.5rem;justify-content:space-between}
 .enc-clock{font-size:.95rem}
}
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
