from copy import deepcopy
import unittest
from family_parser import parse_family_actions
from generated_case_schema import compile_case
from test_compact_authoring import fixture
from coupled_encounter import initialize, execute
TEXT='patient in shock. Give 1000 NS, start oxygen 4l/m nasal cannula. POCUS, VBG, lactate need to improve oxygentaion and prefusion. Reassess in 10 min, hr,bp, O2'
class ParityTests(unittest.TestCase):
    def test_exact_original_order(self):
        a=parse_family_actions(TEXT)['actions']
        self.assertEqual([x['type'] for x in a],['fluid','oxygen','diagnostic','diagnostic','diagnostic','reassessment'])
        self.assertEqual(a[0]['volume_ml'],1000)
        self.assertEqual(a[1]['flow_lpm'],4)
        self.assertEqual(a[-1]['delay_min'],10)
    def test_native_studies_use_explicit_baseline_and_execute(self):
        raw=fixture();case=compile_case(raw)
        self.assertEqual(case['investigations']['vbg']['result']['pco2_mm_hg'],raw['engine']['initial_labs']['pco2_mm_hg'])
        state={'engine_family':'generated','seed':17,'sim_time':0,'observable':deepcopy(case['observable']),
               'encounter_spec':{'clinical_case':case},'treatments':{},'hidden':{},'diagnostics':{}}
        initialize(state)
        result=execute(state,parse_family_actions(TEXT))
        self.assertTrue(result['executed'],result)
        self.assertGreater(state['family_state']['fluid_delivered_ml'],0)
        self.assertEqual(state['family_state']['oxygen_device'],'Nasal cannula')
    def test_no_execution_inferred_from_conditional_or_reasoning(self):
        for text in ('I expect oxygen to improve perfusion.', 'If saturation falls start oxygen 4l/m nasal cannula.', 'Do not start oxygen 4l/m nasal cannula.'):
            self.assertFalse(any(a['type']=='oxygen' for a in parse_family_actions(text)['actions']))
