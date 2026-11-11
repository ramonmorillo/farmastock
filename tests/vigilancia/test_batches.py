import importlib.util
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/vigilancia'))
spec=importlib.util.spec_from_file_location('batches',ROOT/'scripts/vigilancia/batches.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/vigilancia/test_preview.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)

class BatchTests(unittest.TestCase):
 def test_resumes_from_persisted_cache_and_finishes(self):
  partial=t.report();partial['medicines']=[]
  calls=[];persisted=[]
  def collect(cache,budget):
   calls.append(str(cache))
   return partial if len(calls)==1 else t.report()
  result=b.run_batches(pathlib.Path('/initial.json'),pathlib.Path('/private-public-worktree'),collect=collect,persist=lambda *args:persisted.append(args))
  self.assertTrue(result['complete']);self.assertEqual(len(persisted),2)
  self.assertEqual(calls[1],'/private-public-worktree/reports/cima-probe.json')

 def test_rate_limit_preserves_partial_and_stops(self):
  partial=t.report();partial['medicines']=[{'status':429,'error':'HTTPError'}]
  persisted=[]
  result=b.run_batches('cache','output',collect=lambda *args:partial,persist=lambda *args:persisted.append(args))
  self.assertEqual(result['reason'],'rate-limit-stop');self.assertEqual(len(persisted),1)

 def test_invalid_listing_never_published(self):
  invalid=t.report();invalid['requests'][0]['payload']['totalFilas']=999
  persisted=[]
  with self.assertRaises(ValueError):b.run_batches('cache','output',collect=lambda *args:invalid,persist=lambda *args:persisted.append(args))
  self.assertEqual(persisted,[])

 def test_stalled_and_limit_are_not_success(self):
  partial=t.report();partial['medicines']=[]
  result=b.run_batches('cache','output',collect=lambda *args:partial,persist=lambda *args:None)
  self.assertFalse(result['complete']);self.assertEqual(result['reason'],'no-progress-stop');self.assertEqual(len(result['batches']),3)
  result=b.run_batches('cache','output',max_batches=1,collect=lambda *args:partial,persist=lambda *args:None)
  self.assertEqual(result['reason'],'batch-limit')

 def test_complete_source_needs_matching_metadata(self):
  invalid=t.report();invalid['medicines'][0]['payload']['presentaciones']=[]
  self.assertEqual(b.coverage(invalid)['pending'],1)

if __name__=='__main__':unittest.main()
