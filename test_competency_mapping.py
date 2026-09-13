"""Source integrity and conditional evidence for new reasoning objectives."""
from cognitive_catalog import BIAS_CHALLENGES
from competency_mapping import (
    CHALLENGE_MAPPINGS, SOURCES, mapping_for_challenge,
    objective_is_eligible, objective_evidence_is_eligible, record_challenge_id,
)
from objectives import OBJECTIVES


def test_every_cognitive_challenge_has_specific_traceable_links_to_both_frameworks():
    assert set(CHALLENGE_MAPPINGS) == set(BIAS_CHALLENGES)
    for key, challenge in BIAS_CHALLENGES.items():
        mapping = mapping_for_challenge(key)
        assert {link['framework'] for link in mapping['competency_mapping']} == {'ACGME', 'Royal College'}
        assert len(mapping['observable_behaviors']) == 3
        assert len(mapping['evidence_requirements']) >= 3
        for link in mapping['competency_mapping']:
            source = SOURCES[link['source_id']]
            assert link['source_url'] == source['url'] + f"#page={link['pdf_page']}"
            assert link['source_version'] == source['version']
            assert link['source_locator']
            assert link['code']
            assert link['evidence_condition']
            if link['framework'] == 'Royal College':
                assert link['epa_id'] in {'C5', 'TP6'}
                assert link['milestone_items']
        assert OBJECTIVES[key]['competency_mapping'] == challenge['competency_mapping']
        assert OBJECTIVES[key]['assessment_scope'] == 'simulated_reasoning_component'
        assert OBJECTIVES[key]['supported'] is True
        assert 'Not an ACGME or Royal College requirement' in OBJECTIVES[key]['target_source']
        assert 'whole-EPA' in OBJECTIVES[key]['limitation']


def test_source_page_identifiers_match_the_reviewed_editions():
    pages = {link['code']: link['pdf_page'] for key in BIAS_CHALLENGES
             for link in mapping_for_challenge(key)['competency_mapping'] if link['framework'] == 'ACGME'}
    assert pages == {'PC1': 7, 'PC2': 8, 'PC3': 9, 'PC4': 10, 'PC5': 11, 'PC6': 12, 'MK2': 16}
    for key in BIAS_CHALLENGES:
        for link in mapping_for_challenge(key)['competency_mapping']:
            if link['framework'] == 'Royal College':
                assert link['pdf_page'] == {'C5': 25, 'TP6': 57}[link['epa_id']]
    # A specific differential-vs-test distinction must not collapse into a
    # generic CanMEDS label that loses the source behavior.
    links = mapping_for_challenge('R2-02')['competency_mapping']
    assert sorted(link['milestone_items'] for link in links if link['code'] == 'ME 2.2') == [[4], [5]]


def test_new_objective_eligibility_requires_matching_structured_challenge():
    for key in BIAS_CHALLENGES:
        record = {'challenge_id': key, 'payload': {'session': {}},
                  'encounter': {'spec': {'challenge_id': key}}}
        assert objective_is_eligible(key, record)
        for other in set(BIAS_CHALLENGES) - {key}:
            assert not objective_is_eligible(other, record)
        assert not objective_is_eligible(key, {'payload': {'session': {'learner_input': key}}})
        assert not objective_is_eligible(key, {})
    assert not objective_is_eligible('invented_objective', {})
    assert not objective_is_eligible('C2', {})
    assert not objective_is_eligible('C15', {})


def test_conflicting_metadata_fails_closed_and_payload_only_records_work():
    record = {'challenge_id': 'R1-05', 'encounter': {'spec': {'challenge_id': 'R2-02'}}}
    assert record_challenge_id(record) is None
    assert not objective_is_eligible('R1-05', record)
    payload = {'session': {'state': {'encounter_spec': {'challenge_id': 'R1-05'}},
                           'encounter_assignment': {'challenge_id': 'R1-05'}}}
    assert record_challenge_id(payload) == 'R1-05'
    payload['session']['encounter_assignment']['challenge_id'] = 'R3-01'
    assert record_challenge_id(payload) is None
    assert not objective_is_eligible('R1-05', payload)
    for invalid in (None, [], 'R1-05', {'payload': []}, {'session': []}):
        assert not objective_is_eligible('R1-05', invalid)


def test_a_reflection_or_patient_outcome_cannot_replace_observed_decision():
    assert not objective_evidence_is_eligible('R1-05', [{'kind': 'reflection'}])
    assert not objective_evidence_is_eligible('R1-05', [{'outcome': 'recovered'}])
    assert not objective_evidence_is_eligible('R1-05', [])
    # A poor or incompletely documented decision remains assessable by faculty.
    assert objective_evidence_is_eligible('R1-05', [{'kind': 'decision', 'details': {}}])
    assert objective_evidence_is_eligible('C4', [{'kind': 'reflection'}])


def test_original_simulated_clinical_scopes_remain_available():
    for key in ('TD1', 'F1', 'C1', 'C3', 'C4', 'C14'):
        assert OBJECTIVES[key]['supported'] is True
        assert OBJECTIVES[key]['assessment_scope'] == 'simulated_management_component'
        assert objective_is_eligible(key, {})
    assert OBJECTIVES['C4']['target'] == 20
    assert not OBJECTIVES['C2']['supported']
    assert not OBJECTIVES['C15']['supported']


def test_callers_cannot_mutate_versioned_source_or_another_call():
    original = mapping_for_challenge('R1-05')
    changed = mapping_for_challenge('R1-05')
    changed['competency_mapping'][0]['code'] = 'not-a-competency'
    changed['observable_behaviors'][0] = 'award competence'
    assert mapping_for_challenge('R1-05') == original
    assert mapping_for_challenge('unknown') == {}
