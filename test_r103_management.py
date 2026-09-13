from copy import deepcopy
from clinical_scene import history_facts, associated_symptoms, answer_history
from encounter_generator import generate_encounter, PROFILES
from test_curriculum_trajectories import load_engine, initialize, execute_turn, PROCEDURE


def test_broad_history_keeps_positive_cues_without_full_review_or_gate():
    facts=history_facts('70-year-old man with hypertension.', 'PS001')
    reply=associated_symptoms(facts)
    assert 'urinate' in reply and 'chills' in reply
    assert 'chest pain' not in reply and 'neurological' not in reply
    assert answer_history('más síntomas?',facts)==reply
    assert any('chest pain' in f for f in facts)
    assert any('eating or drinking' in f for f in facts)


def test_same_history_does_not_determine_rhythm_response():
    engine=load_engine()
    for seed in (17,83):
        responses={}; histories=[]
        for profile in PROFILES:
            case=generate_encounter('R1-03',engine['INITIAL_STATE'],seed=seed,profile_id=profile)
            histories.append(case['state']['encounter_facts']['focused_history'])
            before=deepcopy(case['state'])
            outcomes={}
            for action, command in [('wait','Reassess in 3 minutes.'),('rhythm',PROCEDURE)]:
                ss=initialize(engine,case['state']); execute_turn(engine,command)
                outcomes[action]=deepcopy(ss.state['observable'])
                assert ss.state['sim_time']==3
            assert case['state']==before
            assert outcomes['wait']['sbp'] <= before['observable']['sbp']+6
            assert outcomes['rhythm']['rhythm']=='Sinus rhythm'
            responses[profile]=outcomes
        assert len(set(histories))==1
        assert responses['mixed_low_flow']['rhythm']['crt'] >= 3
        assert responses['volume_limited']['rhythm']['crt'] > responses['rhythm_contributor']['rhythm']['crt']
        gains={p:r['rhythm']['sbp']-r['wait']['sbp'] for p,r in responses.items()}
        assert gains['rhythm_contributor'] > gains['volume_limited']


def test_other_challenges_keep_legacy_engine_coupling():
    engine=load_engine()
    for challenge in ('R1-04','R2-01'):
        case=generate_encounter(challenge,engine['INITIAL_STATE'],seed=17,generation_mode='authored')
        assert not case['state']['hidden'].get('rhythm_coupling_v2')
