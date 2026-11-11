import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/'scripts/vigilancia/preview.py'
s=importlib.util.spec_from_file_location('preview',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def row(cn='000001',**kw):return dict(cn=cn,nombre='Ejemplo',fini=1,activo=True,**kw)
class PreviewTests(unittest.TestCase):
 def test_baseline_not_new(self):self.assertEqual(m.changes([row()])[0][0]['change'],'situacion-inicial')
 def test_unchanged(self):self.assertEqual(m.changes([row()],[row()])[0][0]['change'],'sin-cambios')
 def test_modified(self):self.assertEqual(m.changes([row(observ='cambio')],[row()])[0][0]['change'],'modificada')
 def test_missing_not_resolved(self):self.assertEqual(m.changes([],[row()])[1][0]['change'],'ausente-revisar')
 def test_multiarea(self):self.assertEqual(m.classify(row(),{'atcs':[{'codigo':'L01BA01'}]},['000001'])[0],['oncologia','consultas-externas'])
 def test_not_all_l_or_name(self):self.assertEqual(m.classify(dict(row(),nombre='ONCO'),{'atcs':[{'codigo':'L04AA01'}]})[0],[])
 def test_no_external_default(self):self.assertEqual(m.classify(row())[0],[])
 def test_incomplete_rejected(self):
  with self.assertRaises(ValueError):m.records({'requests':[{'url':'/rest/psuministro?pagina=1','status':200,'payload':{'totalFilas':201,'tamanioPagina':200,'pagina':1,'resultados':[]}}]})
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):m.records({'requests':[{'url':'/rest/psuministro?pagina=1','status':200,'payload':{'totalFilas':2,'tamanioPagina':200,'pagina':1,'resultados':[row(),row()]}}]})
 def test_preview_and_metadata_membership(self):
  r=row();medicine={'atcs':[{'codigo':'L01BA01'}],'presentaciones':[{'cn':'000001'}]}
  report={'checked_at':'2026-11-11T10:51:12+00:00','requests':[{'url':'/rest/psuministro?pagina=1','status':200,'payload':{'totalFilas':1,'tamanioPagina':200,'pagina':1,'resultados':[r]}}],'medicines':[{'url':'/rest/medicamento?cn=000001','status':200,'payload':medicine}]}
  preview=m.build(report,{'oncologia':[{'email':'test@example.invalid'}]})
  self.assertEqual(preview['mode'],'preview-no-delivery');self.assertFalse(preview['classification_approved'])
  self.assertEqual(preview['digests']['oncologia']['count'],1)
  self.assertIn('Primera captura',preview['digests']['oncologia']['body'])
  medicine['presentaciones']=[]
  self.assertEqual(m.build(report,{})['digests']['oncologia']['count'],0)
if __name__=='__main__':unittest.main()
