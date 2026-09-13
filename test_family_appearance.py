"""Case-authored illness, hypoventilation and active manual support stay distinct."""
import base64
from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace

from PIL import Image
import pytest

from clinical_cases import FAMILIES
from image_consistency import CHECK_IDS, ImageConsistencyError, inspect_image
from patient_appearance import appearance_brief, appearance_signature, appearance_state, edit_prompt
from resuscitation_room import device_labels


CASES = [case for family in FAMILIES.values() for case in family['variants']]


def state_for(case):
    return {'case_id': case['engine']['family'], 'observable': deepcopy(case['observable']),
            'treatments': {}, 'encounter_spec': {'clinical_case': deepcopy(case),
                                                'visual_profile': deepcopy(case['visual_profile'])}}


def opioid_state():
    return state_for(FAMILIES['opioid']['variants'][0])


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['id'])
def test_all_authored_families_have_a_supported_non_wellness_contract(case):
    from image_consistency import _contract
    state = state_for(case)
    before = deepcopy(state)
    visible = appearance_state(state)
    assert _contract(visible) == visible
    assert visible['expression'] in {'uncomfortable', 'markedly uncomfortable', 'passive'}
    assert visible['work_of_breathing'] != 'not recorded'
    assert visible['skin_color'] != 'not recorded'
    brief = appearance_brief(state)
    assert case['faculty']['diagnosis'] not in brief
    assert state == before


def test_opioid_reduced_effort_does_not_become_normal_or_labored_breathing():
    state = opioid_state()
    assert appearance_state(state)['work_of_breathing'] == 'reduced'
    assert appearance_state(state)['expression'] == 'passive'
    brief = appearance_brief(state)
    assert 'shallow spontaneous respiratory effort' in brief
    assert 'restful wellbeing' in brief
    assert 'Eyes closed' in brief or 'Eyes mostly closed' in brief
    normal = deepcopy(state)
    normal['observable']['work_of_breathing'] = 'Normal'
    assert appearance_signature(state) != appearance_signature(normal)


def test_manual_ventilation_uses_executed_state_and_preserves_depressed_drive():
    state = opioid_state()
    original = appearance_signature(state)
    state['pending_order'] = 'Provide bag-mask ventilation'
    assert appearance_signature(state) == original
    state['treatments'].update(bag_mask=True, oxygen=True, oxygen_device='Nasal cannula', niv=True)
    state['observable']['spo2'] = 97
    visible = appearance_state(state)
    assert visible['respiratory_support'] == 'bag-mask ventilation'
    assert visible['work_of_breathing'] == 'reduced'
    assert visible['expression'] == 'passive'
    assert device_labels(state['treatments']) == ['Bag-mask ventilation']
    prompt = edit_prompt(state)
    assert 'necessary gloved clinician hands' in prompt
    assert 'no extra personnel or bodies' in prompt
    assert 'not a loose oxygen mask' in prompt
    assert 'No extra personnel or clinician hands.' not in prompt


def test_invasive_support_supersedes_bag_mask_and_hands_are_removed():
    state = opioid_state()
    state['treatments'].update(bag_mask=True, invasive_ventilation=True, niv=True, oxygen=True)
    assert appearance_state(state)['respiratory_support'] == 'invasive ventilation'
    assert len(device_labels(state['treatments'])) == 1
    assert device_labels(state['treatments'])[0].startswith('Ventilator')
    prompt = edit_prompt(state)
    assert 'No extra personnel or clinician hands.' in prompt
    assert 'necessary gloved clinician hands' not in prompt


def test_stopping_manual_support_removes_the_device_without_inventing_recovery():
    state = opioid_state()
    state['treatments']['bag_mask'] = True
    supported = appearance_signature(state)
    state['treatments']['bag_mask'] = False
    assert appearance_state(state)['respiratory_support'] == 'none'
    assert appearance_signature(state) != supported
    assert appearance_state(state)['work_of_breathing'] == 'reduced'
    assert 'No extra personnel or clinician hands.' in edit_prompt(state)


def test_simple_oxygen_mask_is_supported_and_distinct_from_reservoir_or_manual_bag():
    from image_consistency import _contract
    state = state_for(FAMILIES['pneumonia']['variants'][0])
    state['treatments'].update(oxygen=True, oxygen_device='Simple mask')
    visible = appearance_state(state)
    assert visible['respiratory_support'] == 'simple mask'
    assert _contract(visible) == visible
    assert 'without a reservoir bag, manual resuscitation bag or NIV' in appearance_brief(state)
    assert 'necessary gloved clinician hands' not in edit_prompt(state)


def test_improved_pressure_does_not_clear_authored_illness_or_glucose_sweating():
    state = state_for(FAMILIES['hypoglycemia']['variants'][0])
    before = appearance_state(state)
    state['observable'].update(sbp=130, dbp=80, hr=75, spo2=99)
    assert appearance_state(state) == before
    assert before['diaphoresis'] != 'absent'
    assert before['expression'] != 'neutral'


def test_vision_screen_accepts_supported_bag_mask_contract_and_rejects_device_conflict():
    state = opioid_state()
    state['treatments']['bag_mask'] = True
    image = BytesIO()
    Image.new('RGB', (32, 32)).save(image, format='PNG')
    encoded = base64.b64encode(image.getvalue()).decode('ascii')

    class Responses:
        conflict = False

        def create(self, **kwargs):
            self.request = kwargs
            checks = {key: True for key in CHECK_IDS}
            checks['respiratory_support'] = not self.conflict
            return SimpleNamespace(status='completed', output_text=json.dumps({
                'checks': checks, 'uncertain_checks': []}))

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    assert inspect_image(encoded, appearance_state(state), '', client=client)['accepted']
    request = responses.request
    assert 'necessary gloved clinician hands' in request['instructions']
    assert 'manual support does not prove recovered respiratory drive' in request['instructions']
    assert 'opioid' not in json.dumps(request['input']).lower()
    responses.conflict = True
    with pytest.raises(ImageConsistencyError) as error:
        inspect_image(encoded, appearance_state(state), '', client=client)
    assert error.value.reason_code == 'mismatch'
    assert error.value.failed_checks == ('respiratory_support',)


def test_same_visual_state_from_a_new_patient_never_reuses_the_prior_photo(monkeypatch):
    import clinical_scene
    from cognitive_catalog import BIAS_CHALLENGES
    from cognitive_generator import generate_cognitive_encounter

    first_case = FAMILIES['acs']['variants'][1]
    challenge = next(key for key, value in BIAS_CHALLENGES.items() if 'acs' in value['families'])
    first = generate_cognitive_encounter(challenge, {'sim_time': 0}, seed=1,
                                        family_id='acs', variant_id=first_case['id'])['state']
    second = generate_cognitive_encounter(challenge, {'sim_time': 0}, seed=2,
                                         family_id='acs', variant_id=first_case['id'])['state']
    # Reproduce retaining/recycling the arrival event in anonymous mode. The
    # clinical phenotype is identical, but the generated encounter is different.
    arrival = {'kind': 'presentation', 'text': first_case['presentation']}
    session = {}
    monkeypatch.setattr(clinical_scene, 'st', SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, 'setting', lambda name, default='': '' if name == 'OPENAI_API_KEY' else default)
    assert clinical_scene.scene_image(first, [arrival]) is None
    previous_jobs = session['_scene_jobs']
    signature = appearance_signature(first)
    previous_jobs.images[signature] = 'first-patient-photo'
    previous_jobs.base = 'first-patient-photo'
    assert clinical_scene.scene_image(first, [arrival]) == 'first-patient-photo'
    assert appearance_signature(second) == signature
    assert clinical_scene.scene_image(second, [arrival]) is None
    assert session['_scene_jobs'] is not previous_jobs
    assert session['_scene_jobs'].base is None
