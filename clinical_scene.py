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

# Only recorded patient-history topics are exposed to conversational retrieval.
# The full case specification also includes diagnoses and teaching objectives.
HISTORY_TOPIC_LABELS = {
    'chief_complaint': 'Presenting symptoms',
    'onset': 'Onset and course',
    'associated_symptoms': 'Associated symptoms',
    'medical_history': 'Previous health',
    'medications': 'Medications',
    'allergies': 'Allergies',
    'risk_factors': 'Relevant exposures and risk factors',
    'chest_pain': 'Chest discomfort',
    'breathing': 'Breathing symptoms',
    'bleeding': 'Bleeding symptoms',
    'oral_intake': 'Eating and drinking',
    'exposure': 'Recent exposures',
    'urinary_symptoms': 'Urinary symptoms',
    'neurological_symptoms': 'Neurological symptoms',
    'leg_symptoms': 'Leg symptoms',
}


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
    try:
        return str(st.secrets.get(name, os.environ.get(name, default)))
    except Exception:
        return os.environ.get(name, default)


def scene_prompt(state):
    person = _patient_description(state)
    from patient_appearance import appearance_state, appearance_brief
    visible = appearance_state(state)
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
            'observations conservatively: '+json.dumps(visible)+'. '+appearance_brief(state)+' '
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


def scene_image(state, events):
    from functools import partial
    from patient_appearance import appearance_signature, APPEARANCE_VERSION
    from scene_pipeline import screened_scene, screened_appearance, SCENE_PIPELINE_VERSION
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
    jobs.request(signature, state, setting('OPENAI_API_KEY'),
                 setting('MRS_IMAGE_MODEL', 'gpt-image-1.5'),
                 partial(screened_scene, review_model=review_model),
                 partial(screened_appearance, review_model=review_model),
                 progress_supported=True)
    current = jobs.current(signature)
    st.session_state['_scene_current'] = current is not None
    st.session_state['_scene_failed'] = signature in jobs.failed
    st.session_state['_scene_pending'] = jobs.pending is not None
    st.session_state['_scene_status'] = jobs.status(signature)
    # A label cannot neutralize a contradictory visual cue. Never substitute a
    # previous appearance while the current one is pending, rejected or failed.
    return current


def scene_html(image_b64, monitor, ecg='', *, current=True, pending=False, observations='', image_status=None):
    if not current:
        image_b64 = None
    current = bool(current and image_b64)
    ecg = ''.join(line.strip() for line in ecg.splitlines())
    bg = f'background-image:url(data:image/png;base64,{image_b64});' if image_b64 else ''
    status = 'Patient illustration · current state' if current else (
        'Updating patient appearance' if pending else 'Current patient image unavailable')
    detail = scene_status_text(image_status) if not current else ''
    limitations = getattr(image_b64, 'limitations', ()) if current else ()
    limited_details = []
    if 'mild_skin_color' in limitations:
        limited_details.append('Mild pallor')
    if 'mild_skin_moisture' in limitations:
        limited_details.append('Skin moisture')
    if 'breathing_effort' in limitations:
        limited_details.append('Breathing effort')
    limitation = (', '.join(limited_details) + ': not discernible in this still view; assess during examination.'
                  if limited_details else '')
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
    if status.get('state') == 'pending':
        labels = {'QUEUED': 'Waiting to prepare patient image', 'CREATE': 'Creating patient image',
                  'EDIT': 'Updating patient appearance', 'REPAIR': 'Correcting patient image',
                  'SCREEN': 'Checking patient appearance'}
        stage = 'QUEUED' if status.get('queued') is True else status.get('stage')
        label = labels.get(stage, 'Preparing patient image') if isinstance(stage, str) else 'Preparing patient image'
        elapsed = status.get('elapsed_seconds')
        return f'{label} · {int(elapsed)}s elapsed' if type(elapsed) in (int, float) and 0 <= elapsed < 86400 else label
    return ''


BEDSPACE_CSS = """
.clinical-scene{position:fixed;inset:3.4rem 1rem 1rem;background:#18252e;
 background-size:cover;background-position:38% center;border-radius:14px;overflow:hidden;z-index:1}
.scene-monitor{position:absolute;right:1.2%;top:1.5%;width:36%;background:#07141d;
 border:5px solid #263a48;border-radius:14px;box-shadow:0 8px 24px #0008;max-height:37vh;overflow:hidden}
.scene-monitor svg{width:100%;height:auto;display:block;max-height:12vh}
.monitor-values{min-width:0}.monitor-values>div{min-width:0}
.scene-time{position:absolute;left:0;top:0;background:#000b;color:#eee;padding:8px 14px;font:12px system-ui;max-width:59%}
.scene-observations{position:absolute;left:2%;bottom:3%;max-width:54%;background:#17222eee;color:white;padding:10px;border-radius:8px}
.scene-image-status{position:absolute;left:3%;top:38%;max-width:53%;color:#dce8ef;font:16px/1.5 system-ui;padding:12px;background:#0e1b24;border-radius:8px}
.st-key-encounter-console{position:fixed!important;right:2.2rem;top:calc(3.4rem + 39vh);
 bottom:1.8rem;width:35%!important;overflow-y:auto!important;overflow-x:hidden;z-index:2;
 background:rgba(248,250,252,.96);padding:14px;border:1px solid #b8c6cd;border-radius:12px;
 box-shadow:0 8px 28px #0005;color:#17232d;color-scheme:light}
.st-key-encounter-console h3{font-size:1.1rem!important;margin:0!important;padding-top:0!important}
.st-key-encounter-console [data-testid="stForm"]{padding:10px}
.st-key-encounter-console [data-testid="stCaptionContainer"]{font-size:.8rem}
.st-key-encounter-console [data-testid="stVerticalBlock"]{gap:.6rem}
.st-key-encounter-console [data-testid="stExpander"]{background:#f7f9fb}
.st-key-encounter-console [role="radiogroup"]{gap:.6rem;flex-wrap:wrap}
.st-key-encounter-console [data-testid="stMarkdownContainer"]{overflow-wrap:anywhere}
@media(max-width:760px){
 .clinical-scene{inset:3.2rem .4rem auto;height:39vh;background-position:25% center}
 .scene-monitor{width:43%;max-height:35vh;right:1%;top:5%}
 .scene-monitor .monitor-values{grid-template-columns:repeat(2,1fr)!important}
 .scene-monitor .monitor-values>div{padding:2px!important}
 .scene-monitor .monitor-values small{font-size:10px}
 .scene-monitor svg{max-height:9vh}.scene-time{font-size:10px;max-width:52%;padding:4px}
 .scene-observations{font-size:11px;max-width:49%;padding:5px}
 .scene-image-status{font-size:11px;max-width:48%;padding:6px;top:20%}
 .st-key-encounter-console{left:.4rem;right:.4rem;top:calc(3.2rem + 40vh);bottom:.4rem;width:auto!important;padding:10px}
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
