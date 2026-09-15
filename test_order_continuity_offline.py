import unittest
from copy import deepcopy
from family_parser import parse_family_actions
from pending_family_orders import hold_incomplete_bundle,complete_bundle
from test_compact_authoring import fixture
from generated_case_schema import compile_case
from coupled_encounter import initialize,execute
from case_study_compatibility import upgrade_studies

def state():
 c=compile_case(fixture());s={'engine_family':'generated','seed':17,'sim_time':0,'observable':deepcopy(c['observable']),'encounter_spec':{'clinical_case':c},'treatments':{},'hidden':{},'diagnostics':{}}
 initialize(s);return s
class ContinuityTests(unittest.TestCase):
 def test_aliases_and_ambiguity(self):
  for text,name in [('VBG','vbg'),('venous blood gases','vbg'),('gases venosos','vbg'),('ABG','abg'),('arterial blood gases','abg'),('gases arteriales','abg')]:
   self.assertEqual(parse_family_actions(text)['actions'],[{'type':'diagnostic','diagnostic':name}])
  for text in ['gases','gasometria','blood gases']:
   p=hold_incomplete_bundle(parse_family_actions('Give 1000 NS. '+text))
   self.assertIsNotNone(p)
   self.assertEqual(complete_bundle(p,'VBG')['parsed']['actions'][0]['volume_ml'],1000)
 def test_duration_and_async_tests(self):
  s=state();p=parse_family_actions('Give 1000 NS over 10 min. Start oxygen 4l/m nasal cannula. VBG')
  self.assertEqual(p['actions'][0]['volume_ml'],1000)
  self.assertEqual(p['actions'][0]['administration_duration_min'],10)
  self.assertTrue(execute(s,p)['executed']);self.assertEqual(s['sim_time'],0)
  self.assertTrue(s['pending_investigations']);self.assertEqual(s['family_state']['fluid_delivered_ml'],0)
  execute(s,parse_family_actions('Reassess in 1 min'))
  self.assertEqual(s['family_state']['fluid_delivered_ml'],100)
 def test_replacement_preserves_treatments_and_reassessment(self):
  s=state();p=parse_family_actions('Give 1000 NS. Start oxygen 4l/m nasal cannula. Troponin. Reassess in 1 min')
  s['encounter_spec']['clinical_case']['investigations'].pop('troponin',None)
  self.assertFalse(execute(s,p)['executed']);self.assertEqual(s['sim_time'],0)
  held=hold_incomplete_bundle(p,s)
  resolved=complete_bundle(held,'ok basic labs')['parsed']
  self.assertEqual([a['type'] for a in resolved['actions']],['fluid','oxygen','diagnostic','reassessment'])
  self.assertTrue(execute(s,resolved)['executed'])
  self.assertEqual(s['family_state']['fluid_delivered_ml'],50)
 def test_explicit_saved_case_upgrade_does_not_reset(self):
  s=state();s['encounter_spec']['clinical_case']['investigations'].pop('vbg')
  before=deepcopy(s['observable']);self.assertIn('vbg',upgrade_studies(s))
  self.assertEqual(s['observable'],before);self.assertEqual(upgrade_studies(s),[])
