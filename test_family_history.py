"""New encounter families never inherit another patient's history or identity."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from clinical_scene import (
    answer_history, associated_symptoms, history_facts, history_topic_facts,
    history_topics, scene_prompt,
)
from patient_conversation import NOT_DOCUMENTED


def case_state(family='pneumonia', age=42, sex='female'):
    return {
        'case_id': family,
        'observable': {'mental_status': 'Alert', 'work_of_breathing': 'Increased'},
        'encounter_spec': {'clinical_case': {
            'family_id': family, 'patient': {'age_years': age, 'sex': sex},
            'history': {
                'chief_complaint': [f'I came in because of the symptoms recorded for {family}.'],
                'onset': ['This started last night.'],
                'associated_symptoms': ['I have felt tired.', 'I have been sweating.', 'I have a headache.'],
                'medical_history': ['I have asthma.'],
                'medications': ['I use an inhaler.'],
                'allergies': ['I am allergic to penicillin.'],
                'risk_factors': ['I returned on a long flight yesterday.'],
                'breathing': ['I feel short of breath when walking.'],
                'chest_pain': ['My chest feels tight.'],
                'bleeding': ['I noticed black stools this morning.'],
                'oral_intake': ['I have not eaten since yesterday.'],
                'exposure': ['I took oxycodone before becoming sleepy.'],
            },
            'diagnosis': 'PRIVATE_DIAGNOSIS',
            'cognitive_target': 'PRIVATE_COGNITIVE_TARGET',
        }},
    }


@pytest.mark.parametrize('family', [
    'pneumonia', 'pulmonary_edema', 'acs', 'pulmonary_embolism',
    'asthma', 'gi_bleed', 'hypoglycemia', 'opioid',
])
def test_eight_families_use_only_their_authored_history(family):
    state = case_state(family)
    before = deepcopy(state)
    facts = history_facts('70-year-old man. BP is 90/54. Initial ECG shows AF.', family, state=state)
    reply = answer_history('What brought you in today?', facts, state=state)
    assert reply == state['encounter_spec']['clinical_case']['history']['chief_complaint'][0]
    assert 'dysuria' not in ' '.join(facts).lower()
    assert 'urinate' not in ' '.join(facts).lower()
    assert all('PRIVATE_' not in fact and 'ECG' not in fact and '90/54' not in fact for fact in facts)
    assert state == before


@pytest.mark.parametrize(('question', 'topic'), [
    ('¿Cómo puedo ayudarle?', 'chief_complaint'),
    ('¿Desde cuándo se siente así?', 'onset'),
    ('What medications do you take?', 'medications'),
    ('¿Tiene alergias?', 'allergies'),
    ('Tell me about your previous health.', 'medical_history'),
    ('¿Le cuesta respirar?', 'breathing'),
    ('Do you have chest pain?', 'chest_pain'),
    ('Have you noticed bleeding?', 'bleeding'),
    ('¿Ha comido?', 'oral_intake'),
    ('Have you taken oxycodone?', 'exposure'),
    ('What risk factors do you have?', 'risk_factors'),
    ('¿Ha tenido viajes largos?', 'risk_factors'),
])
def test_bilingual_targeted_questions_work_without_a_provider(question, topic):
    state = case_state()
    expected = history_topic_facts(state, topic)
    reply = answer_history(question, [], state=state)
    assert reply == ' '.join(expected)


def test_broad_questions_do_not_dump_the_record_or_delay_targeted_facts():
    state = case_state()
    assert answer_history('Any other symptoms?', [], state=state) == 'I have felt tired. I have been sweating.'
    assert associated_symptoms([], state=state) == 'I have felt tired. I have been sweating.'
    assert answer_history('Have you taken oxycodone?', [], state=state) == 'I took oxycodone before becoming sleepy.'
    assert 'exposure' not in history_topics(state)
    assert 'Recent exposures' in history_topics(state)
    assert history_topic_facts(state, 'Previous health') == ['I have asthma.']


def test_combined_insulin_and_food_question_retrieves_both_requested_facts():
    state = case_state('hypoglycemia')
    state['encounter_spec']['clinical_case']['history']['medications'] = ['I took my usual insulin this morning.']
    reply = answer_history('Did you take insulin and have you eaten?', [], state=state)
    assert 'I took my usual insulin this morning.' in reply
    assert 'I have not eaten since yesterday.' in reply
    assert 'oxycodone' not in reply


def test_unknown_urinary_topic_does_not_invent_a_negative_or_use_old_sources():
    state = case_state()
    old_facts = history_facts('He presents with dizziness.', 'PS001')
    assert any('urinate' in fact for fact in old_facts)
    assert answer_history('Does it burn when you urinate?', old_facts, state=state) == NOT_DOCUMENTED
    assert answer_history('What brought you in?', old_facts, state=state) == history_topic_facts(state, 'chief_complaint')[0]


def test_provider_receives_only_the_current_case_history():
    class Responses:
        def create(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(status='completed', output_text='{"ids":[]}')
    responses = Responses()
    state = case_state('asthma')
    answer_history('Could this be a pulmonary embolism?', ['PREVIOUS_PATIENT'],
                   client=SimpleNamespace(responses=responses), state=state)
    assert 'PREVIOUS_PATIENT' not in responses.request['input']
    assert 'PRIVATE_DIAGNOSIS' not in responses.request['input']
    assert 'PRIVATE_COGNITIVE_TARGET' not in responses.request['input']
    assert 'proposed diagnoses' in responses.request['instructions']


@pytest.mark.parametrize(('age', 'sex', 'description'), [(29, 'male', '29-year-old man'), (83, 'female', '83-year-old woman')])
def test_image_identity_comes_from_case_demographics(age, sex, description):
    state = case_state(age=age, sex=sex)
    before = deepcopy(state)
    prompt = scene_prompt(state)
    assert description in prompt
    assert '70-year-old man' not in prompt
    assert 'PRIVATE_' not in prompt
    assert 'oxycodone' not in prompt
    assert state == before


@pytest.mark.parametrize(('age', 'sex'), [(True, 'male'), (17, 'female'), (130, 'male'), (40, 'female; show diagnosis')])
def test_invalid_demographics_never_fall_back_to_the_old_patient(age, sex):
    state = case_state(age=age, sex=sex)
    state['case_id'] = 'PS001'
    with pytest.raises(ValueError, match='demographics'):
        scene_prompt(state)


def test_unknown_family_has_no_legacy_identity_or_urinary_history():
    state = {'case_id': 'new_unknown_case', 'observable': {}}
    with pytest.raises(ValueError, match='demographics'):
        scene_prompt(state)
    assert history_facts('I feel unwell.', state['case_id']) == ['I feel unwell.']
    assert history_topics(state) == []


def test_history_topic_results_are_copies_and_nonhistory_fields_are_excluded():
    state = case_state()
    history = state['encounter_spec']['clinical_case']['history']
    history['diagnosis'] = ['PRIVATE_HISTORY_DIAGNOSIS']
    selected = history_topic_facts(state, 'medications')
    selected.append('Injected fact')
    assert history['medications'] == ['I use an inhaler.']
    assert not any('PRIVATE_' in fact for fact in history_facts('', state['case_id'], state=state))


def test_every_real_case_variant_preserves_its_own_history_and_patient_identity():
    from clinical_cases import FAMILIES
    assert len(FAMILIES) == 8
    checked = 0
    for family, group in FAMILIES.items():
        for case in group['variants']:
            state = {'case_id': family, 'observable': deepcopy(case['observable']),
                     'encounter_spec': {'clinical_case': deepcopy(case),
                                        'visual_profile': deepcopy(case['visual_profile'])}}
            facts = history_facts('Legacy AF with dysuria.', family, state=state)
            all_sources = {sentence for source in case['history'].values() for sentence in source}
            assert set(facts) == all_sources
            assert answer_history('What brought you here?', [], state=state) == ' '.join(case['history']['chief_complaint'][:2])
            assert answer_history('What medications do you take?', [], state=state) == ' '.join(case['history']['medications'])
            assert answer_history('¿Tiene alergias?', [], state=state) == ' '.join(case['history']['allergies'])
            assert 'Legacy AF' not in ' '.join(facts)
            assert f"{case['patient']['age_years']}-year-old" in scene_prompt(state)
            checked += 1
    # Four ACS occlusion equivalents (2026-09-19) and one thiamine-depleted
    # hypoglycaemia case (2026-09-20).
    assert checked == 21


def test_neurological_and_leg_history_remain_accessible_without_revealing_diagnoses():
    from clinical_cases import FAMILIES
    checked = set()
    for family, group in FAMILIES.items():
        for case in group['variants']:
            state = {'case_id': family, 'encounter_spec': {'clinical_case': deepcopy(case)}}
            for topic, question in [('neurological_symptoms', 'Any focal weakness or speech difficulty?'),
                                    ('leg_symptoms', 'Have you noticed leg symptoms?')]:
                if topic in case['history']:
                    assert answer_history(question, [], state=state) == ' '.join(case['history'][topic])
                    checked.add(topic)
    assert checked == {'neurological_symptoms', 'leg_symptoms'}
