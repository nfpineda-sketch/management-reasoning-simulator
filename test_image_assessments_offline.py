import json
import unittest
from image_consistency import _result, ImageConsistencyError
from scene_errors import CHECK_IDS

class AssessmentTests(unittest.TestCase):
    def payload(self):
        return {'assessments':{k:{'verdict':'compatible','finding':'No visible conflict.'} for k in CHECK_IDS},
                'observations':{'devices':[],'unexpected_findings':[],'skin':'natural_or_subtle_pallor'}}
    def expected(self):
        return {'expression':'uncomfortable','skin_color':'mild pallor','mottling':False,
                'diaphoresis':'mild','mental_status':'drowsy','work_of_breathing':'increased','respiratory_support':'none'}
    def test_accepts_complete_consistent_assessments(self):
        self.assertTrue(_result(json.dumps(self.payload()),self.expected())['accepted'])
    def test_conflict_still_rejects_with_its_evidence(self):
        p=self.payload();p['assessments']['expression']={'verdict':'conflict','finding':'Cheerful smile on face; discomfort required.'}
        with self.assertRaises(ImageConsistencyError) as c:_result(json.dumps(p),self.expected())
        self.assertEqual(c.exception.reason_code,'mismatch')
        self.assertEqual(c.exception.conflict_evidence[0]['check'],'expression')
    def test_uncertain_identity_still_rejects(self):
        p=self.payload();p['assessments']['identity_and_framing']['verdict']='uncertain'
        with self.assertRaises(ImageConsistencyError) as c:_result(json.dumps(p),self.expected())
        self.assertEqual(c.exception.reason_code,'uncertain')
    def test_missing_domain_rejects(self):
        p=self.payload();del p['assessments']['mottling']
        with self.assertRaises(ImageConsistencyError):_result(json.dumps(p),self.expected())
