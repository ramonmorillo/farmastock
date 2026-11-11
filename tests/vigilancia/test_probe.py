import importlib.util
import io
import json
import pathlib
import unittest
import urllib.error
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('probe',ROOT/'scripts/vigilancia/probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Response(io.BytesIO):
    status=200
    url='https://cima.aemps.es/cima/rest/medicamento?cn=000001'
    headers={'Content-Type':'application/json'}

class ProbeTests(unittest.TestCase):
    def test_success(self):
        with patch.object(p.urllib.request,'urlopen',return_value=Response(b'{"ok":true}')):
            result=p.probe(p.BASE+'/test')
        self.assertTrue(result['payload']['ok'])
        self.assertEqual(result['status'],200)

    def test_oversize_never_parsed(self):
        with patch.object(p.urllib.request,'urlopen',return_value=Response(b'x'*2_000_001)):
            result=p.probe(p.BASE+'/test')
        self.assertEqual(result['error'],'response_over_limit')
        self.assertNotIn('payload',result)

    def test_404_not_retried(self):
        error=urllib.error.HTTPError(p.BASE,404,'not found',{},None)
        with patch.object(p.urllib.request,'urlopen',side_effect=error) as call:
            result=p.probe(p.BASE+'/test')
        self.assertEqual(call.call_count,1)
        self.assertEqual(result['status'],404)

    def test_transient_failure_bounded(self):
        error=urllib.error.HTTPError(p.BASE,503,'unavailable',{},None)
        with patch.object(p.urllib.request,'urlopen',side_effect=error) as call,patch.object(p.time,'sleep'):
            result=p.probe(p.BASE+'/test')
        self.assertEqual(call.call_count,3)
        self.assertEqual(result['status'],503)

    def test_metadata_minimization(self):
        data={'nombre':'Ejemplo','atcs':[{'codigo':'J01CA04'}],'presentaciones':[{'cn':'000001','nombre':'Ejemplo','extra':'not needed'}],'docs':[{'url':'not fetched'}]}
        with patch.object(p,'probe',return_value={'status':200,'payload':data}),patch.object(p.time,'sleep'):
            result=p.metadata('000001')['payload']
        self.assertNotIn('docs',result)
        self.assertEqual(result['presentaciones'],[{'cn':'000001','nombre':'Ejemplo'}])

if __name__=='__main__':unittest.main()
