import importlib.util,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/vigilancia'))
import review
spec=importlib.util.spec_from_file_location('fixtures_review',ROOT/'tests/vigilancia/test_preview.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)

class ReviewTests(unittest.TestCase):
 def test_sample_strips_email_without_mutation(self):
  result=t.m.build(t.report(),t.assignments())
  sample=review.sample_result(result,t.report())
  self.assertNotIn('email',sample['owners'][1]['recipient'])
  self.assertIn('email',result['owners'][1]['recipient'])
  self.assertEqual(sample['owners'][1]['total_assigned'],1)
  html=review.render_review(sample,sample['owners'][1])
  self.assertNotIn('@example.invalid',html)
  self.assertIn('Descargar mis decisiones',html)
  self.assertIn('no envía correos',html)

 def test_sample_diversifies_atc_and_limits(self):
  items=[dict(t.row(cn=f'{i:06}'),areas=['Neurología']) for i in range(1,10)]
  owner={'areas':['Neurología'],'items':items}
  metadata={r['cn']:{'atcs':[{'codigo':'N03AX09' if i<5 else 'N04BA02'}]} for i,r in enumerate(items)}
  selected=review.select_items(owner,metadata)
  self.assertEqual(len(selected),2)

 def test_unverified_records_not_used_as_clinical_examples(self):
  owner={'areas':['Pendientes de clasificación · revisión'],'items':[dict(t.row(),areas=['Pendientes de clasificación · revisión'])]}
  self.assertEqual(review.select_items(owner,{}),[])

 def test_shared_use_prioritized_without_assigning_specialty(self):
  label='Pendientes de clasificación · revisión'
  rows=[dict(t.row(cn=f'{i:06}'),areas=[label]) for i in range(1,4)]
  metadata={rows[0]['cn']:{'atcs':[{'codigo':'A02BC01'}]},rows[1]['cn']:{'atcs':[{'codigo':'L04AD02'}]},rows[2]['cn']:{'atcs':[{'codigo':'L04AD01'}]}}
  selected=review.select_items({'areas':[label],'items':rows},metadata,doubtful=2)
  self.assertEqual([r['cn'] for r in selected],['000002','000003'])
  self.assertTrue(all(r['areas']==[label] for r in selected))

if __name__=='__main__':unittest.main()
