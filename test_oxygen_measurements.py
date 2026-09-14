"""Measurements cannot turn into treatment orders or invert stated expectations."""

import pytest

from test_curriculum_trajectories import initialize, load_engine


REPORTED_REASSESSMENT = (
    "Reassess blood pressure, heart rate and rhythm, capillary refill, mental "
    "status, oxygen saturation, and work of breathing now. My priority is to "
    "establish the current perfusion and respiratory status. I do not expect "
    "reassessment alone to improve the patient's physiology; I will use the "
    "findings to determine my next management action."
)


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def test_reported_reassessment_has_no_treatment_or_reasoning_gate(engine):
    initialize(engine, engine["INITIAL_STATE"])
    parsed = engine["clinical_interpreter"](REPORTED_REASSESSMENT)
    assert parsed["actions"] == [{"type": "reassessment", "delay_min": 0, "focus": "perfusion"}]
    assert engine["reasoning_gate_missing"](parsed) == []
    assert parsed["reasoning"]["expected_effect"] == (
        "I do not expect reassessment alone to improve the patient's physiology"
    )


@pytest.mark.parametrize("text", [
    "Reassess blood pressure, oxygen saturation, and respiratory rate now.",
    "Recheck blood pressure and O2 saturation now.",
    "Assess oxygen saturation.",
    "Monitor blood pressure, oxygen levels, and respiratory rate.",
    "Continue monitoring oxygen saturation.",
    "Increase oxygen saturation to 94%.",
    "Set monitoring alarms for oxygen saturation to 90%.",
    "Reevaluar presión arterial, saturación de oxígeno y frecuencia respiratoria.",
    "Medir oxígeno.",
    "Reassess respiratory effort and nasal cannula fit.",
    "Give fluids, reassess oxygen support.",
])
def test_oxygen_measurements_and_observation_lists_are_not_orders(engine, text):
    assert engine["explicit_oxygen_actions"](text) == []


@pytest.mark.parametrize("text, flow", [
    ("Administer oxygen via nasal cannula at 3 L/min to target saturation 94%.", 3),
    ("Reassess oxygen saturation, then start oxygen via nasal cannula at 3 L/min.", 3),
    ("Start oxygen via nasal cannula at 3 L/min and monitor oxygen saturation.", 3),
    ("Increase nasal cannula oxygen from 3 L/min to 4 L/min.", 4),
    ("Decrease nasal cannula oxygen from 4 L/min to 2 L/min.", 2),
    ("Continue oxygen via nasal cannula at 3 L/min.", 3),
    ("O2 3 L/min nasal cannula.", 3),
    ("Administrar oxígeno por cánula nasal a 3 L/min para saturación de 94%.", 3),
    ("Mantener oxígeno por cánula nasal a 3 L/min.", 3),
    ("Aumentar oxígeno por cánula nasal a 4 L/min.", 4),
    ("Disminuir oxígeno por cánula nasal a 2 L/min.", 2),
])
def test_actual_oxygen_directives_keep_their_device_and_flow(engine, text, flow):
    assert engine["explicit_oxygen_actions"](text) == [
        {"type": "oxygen", "device": "Nasal cannula", "flow_lpm": flow}
    ]


@pytest.mark.parametrize("prefix", [
    "I do not expect", "I don't expect", "I don’t expect", "We would not expect",
    "I wouldn't anticipate",
])
def test_negative_expectations_preserve_the_learners_negation(engine, prefix):
    expectation = prefix + " reassessment alone to improve the patient's physiology"
    reasoning = engine["extract_explicit_reasoning"](
        "Reassess perfusion now. " + expectation + "."
    )
    assert reasoning["expected_effect"] == expectation
    assert engine["_immediate_expectation_text"](reasoning["expected_effect"], {}) == ""


def test_positive_expectation_still_retains_its_full_subject(engine):
    reasoning = engine["extract_explicit_reasoning"](
        "I expect pressure to increase and perfusion to improve. Reassess in 5 minutes."
    )
    assert reasoning["expected_effect"] == "pressure to increase and perfusion to improve"


@pytest.mark.parametrize("negative_first", [False, True])
def test_mixed_expectations_keep_positive_and_negative_clauses(engine, negative_first):
    positive = "I expect pressure to increase"
    negative = "I do not expect oxygenation to improve"
    clauses = [negative, positive] if negative_first else [positive, negative]
    reasoning = engine["extract_explicit_reasoning"](
        ". ".join(clauses) + ". Reassess in 5 minutes."
    )
    expected = [negative, "pressure to increase"] if negative_first else ["pressure to increase", negative]
    assert reasoning["expected_effect"] == "; ".join(expected)
    assert engine["_immediate_expectation_text"](reasoning["expected_effect"], {}) == "pressure to increase"


@pytest.mark.parametrize('text',[
    'Continue monitoring oxygen saturation.',
    'Recheck blood pressure and O2 saturation now.',
    'Assess oxygen saturation.',
    'Monitor blood pressure, oxygen levels, and respiratory rate.',
    'Reevaluar presión arterial, saturación de oxígeno y frecuencia respiratoria.',
    'Medir oxígeno.',
])
def test_generated_observation_does_not_change_active_support(text):
    from family_parser import parse_family_actions
    from generated_engine import execute_generated_bundle
    from test_generated_engine import make_state, rule
    from copy import deepcopy
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('oxygen','oxygen',{},device='nasal cannula',dose_field='flow_lpm',reference_dose=3))
    assert execute_generated_bundle(state,parse_family_actions('Start oxygen NC 3 L/min; reassess in 0 minutes'))['executed']
    before=deepcopy(state['treatments']); at=state['sim_time']
    parsed=parse_family_actions(text)
    assert parsed['actions'] and all(a['type']=='reassessment' for a in parsed['actions'])
    assert execute_generated_bundle(state,parsed)['executed']
    assert state['treatments']==before and state['sim_time']==at


def test_generated_oxygen_then_monitoring_executes_one_treatment():
    from family_parser import parse_family_actions
    from generated_engine import execute_generated_bundle
    from test_generated_engine import make_state,rule
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('oxygen','oxygen',{},device='nasal cannula',dose_field='flow_lpm',reference_dose=3))
    parsed=parse_family_actions('Start oxygen via nasal cannula at 3 L/min and monitor oxygen saturation.')
    assert execute_generated_bundle(state,parsed)['executed']
    assert len(state['treatments']['order_history'])==1
    assert state['treatments']['oxygen_flow_lpm']==3


@pytest.mark.parametrize('text',['Increase oxygen saturation to 94%.','Set monitoring alarms for oxygen saturation to 90%.'])
def test_saturation_target_is_not_an_oxygen_order(text):
    from family_parser import parse_family_actions
    assert all(a['type']!='oxygen' for a in parse_family_actions(text)['actions'])


def test_observation_list_keeps_requested_delay():
    from family_parser import parse_family_actions
    from generated_engine import execute_generated_bundle
    from test_generated_engine import make_state
    state=make_state()
    parsed=parse_family_actions('Monitor blood pressure in 5 minutes and heart rate and mental status')
    assert execute_generated_bundle(state,parsed)['executed']
    assert state['sim_time']==5
    assert not state['treatments'].get('order_history', [])


def test_observation_list_does_not_swallow_requested_study():
    from family_parser import parse_family_actions
    actions=parse_family_actions('Check blood pressure and lactate')['actions']
    assert actions==[{'type':'reassessment','delay_min':0},{'type':'diagnostic','diagnostic':'lactate'}]
