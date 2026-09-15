from copy import deepcopy
import unittest
from case_authoring import collapse_identical_study_fields, expand_author_case
from generated_case_schema import compile_case
from test_compact_authoring import fixture, compact

class DuplicateTests(unittest.TestCase):
 def test_identical_rows_collapse_without_mutation(self):
  raw=fixture();study=raw['investigations'][0]
  study['result'].append(deepcopy(study['result'][0]));before=deepcopy(raw)
  cleaned=collapse_identical_study_fields(raw)
  compile_case(cleaned)
  self.assertEqual(raw,before)
  self.assertEqual(collapse_identical_study_fields(cleaned),cleaned)
 def test_conflicting_duplicates_still_rejected(self):
  raw=fixture();study=raw['investigations'][0];row=deepcopy(study['result'][0]);row['value']+=1;study['result'].append(row)
  with self.assertRaises(ValueError):compile_case(collapse_identical_study_fields(raw))
 def test_missing_bedside_measurement_uses_existing_baseline(self):
  raw=compact(fixture())
  for study in raw['investigations']:
   if study['id'] in ('poc_glucose','temperature'):
    study['result']=[{'field':'report','value':'Bedside measurement.'}]
  result=expand_author_case(raw);compile_case(result)
  for study in result['investigations']:
   field={'poc_glucose':'glucose_mg_dl','temperature':'temperature_c'}.get(study['id'])
   if field:self.assertEqual(next(r['value'] for r in study['result'] if r['field']==field),raw['observable'][field])
