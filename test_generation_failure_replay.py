"""Offline regression for adapter continuity and repair evidence."""
from copy import deepcopy
import unittest
from test_compact_authoring import fixture, compact
from case_authoring import AUTHOR_SCHEMA, NATIVE_ONLY
from generated_case import _draft_preview
from coupled_encounter import initialize, project

class FailureReplayTests(unittest.TestCase):
    def test_terminal_projection_preserves_last_visible_findings(self):
        case=fixture()
        state={'seed':17,'sim_time':0,'observable':deepcopy(case['observable']),
               'encounter_spec':{'clinical_case':case},'treatments':{},'hidden':{},'diagnostics':{}}
        initialize(state)
        state['observable'].setdefault('visual',{})['mottling']=True
        native=state['coupled_state']
        native['hidden']['terminal_collapse']=True
        native['observable'].update(sbp=0,dbp=0,rhythm='PEA',pulse_present=False,mental_status='Unresponsive')
        project(state)
        self.assertTrue(state['observable']['visual']['mottling'])
        self.assertEqual(state['observable']['sbp'],0)
        self.assertEqual(state['observable']['rhythm'],'PEA')
        self.assertFalse(state['observable']['pulse_present'])

    def test_structural_repair_gets_offline_native_evidence(self):
        result=_draft_preview(fixture(),17)
        self.assertEqual(result['status'],'available')
        self.assertEqual(result['shared_engine_preview'][0]['time_min'],0)
        self.assertGreater(len(result['shared_engine_preview']),1)
        self.assertEqual(_draft_preview({},17)['status'],'unavailable')

    def test_native_only_rules_excluded_but_extensions_retained(self):
        allowed=AUTHOR_SCHEMA['properties']['engine']['properties']['response_rules']['items']['properties']['action_type']['enum']
        self.assertFalse(set(allowed)&NATIVE_ONLY)
        self.assertIn('cardioversion',allowed)
        self.assertIn('diuretic',allowed)

if __name__=='__main__': unittest.main()
