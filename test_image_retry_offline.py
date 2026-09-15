"""No-provider regressions for exact-candidate review retries."""
import json
import unittest
from concurrent.futures import Future
from unittest.mock import patch
from scene_jobs import SceneJobs
from image_consistency import _result, ImageConsistencyError
from scene_errors import CHECK_IDS, SceneImageError

class Pool:
    def submit(self, fn, *args):
        self.fn,self.args=fn,args
        return Future()

class RetryTests(unittest.TestCase):
    def test_retry_reuses_exact_candidate_and_reference(self):
        for base in (None,'approved-original'):
            jobs=SceneJobs();jobs.base=base
            jobs.failed.add('current')
            jobs._diagnostic_candidate=('current','existing-pixels')
            self.assertTrue(jobs.retry('current'))
            pool=Pool();calls=[]
            def review(*args,**kwargs):calls.append((args,kwargs))
            def generate(*args,**kwargs):self.fail('Generation must not run')
            with patch('scene_jobs._POOL',pool):
                jobs.request('current',{'sim_time':0},'test','image-model',generate,generate,recheck=review)
            pool.fn(*pool.args)
            self.assertEqual(calls[0][0][0],'existing-pixels')
            self.assertEqual(calls[0][1]['reference'],base)
            self.assertNotIn('current',jobs.images)

    def test_changed_appearance_does_not_reuse_rejected_pixels(self):
        jobs=SceneJobs();jobs.failed.add('old');jobs._diagnostic_candidate=('old','old-pixels')
        jobs.retry('old');pool=Pool()
        def generate(*args):pass
        with patch('scene_jobs._POOL',pool):
            jobs.request('new',{},'test','model',generate,generate,recheck=lambda:None)
        self.assertIs(pool.fn,generate)

    def test_specific_safe_parse_diagnostics(self):
        cases=[('not json','RESULT_JSON'),('{}','RESULT_SCHEMA'),
               (json.dumps({'checks':dict.fromkeys(CHECK_IDS,False),'uncertain_checks':[], 'conflict_evidence':[]}), 'RESULT_EVIDENCE')]
        for payload,code in cases:
            with self.assertRaises(ImageConsistencyError) as caught:_result(payload)
            self.assertEqual(caught.exception.code,code)
            self.assertNotIn(payload,str(caught.exception))

if __name__=='__main__':unittest.main()
