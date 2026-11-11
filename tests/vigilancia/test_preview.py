import copy
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('preview', ROOT/'scripts/vigilancia/preview.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RULES = m.load_rules()


def row(cn='000001', **kw):
    return dict(cn=cn, nombre='Ejemplo', fini=1794265200000, activo=True, **kw)


def report(rows=None, atcs=None):
    rows = [row()] if rows is None else rows
    return {
        'checked_at': '2026-11-11T10:00:00+00:00',
        'requests': [{'url': 'https://cima.aemps.es/cima/rest/psuministro?pagina=1', 'status': 200,
                      'payload': {'totalFilas': len(rows), 'tamanioPagina': 200, 'pagina': 1, 'resultados': rows}}],
        'medicines': [{'url': 'https://cima.aemps.es/cima/rest/medicamento?cn=000001', 'status': 200,
                       'payload': {'atcs': [{'codigo': c} for c in (atcs or ['L01BA01'])],
                                   'presentaciones': [{'cn': '000001'}]}}]}


def assignments():
    return {'mode': 'preview-no-delivery', 'assignments': [
        {'recipient': {'email': 'a@example.invalid'}, 'areas': ['infecciosas', 'neurologia', 'hipercolesterolemia']},
        {'recipient': {'email': 'b@example.invalid'}, 'areas': ['oncohematologia']},
        {'recipient': {'email': 'c@example.invalid'}, 'areas': ['inmunomediadas', 'pediatria', m.REVIEW]}]}


class PreviewTests(unittest.TestCase):
    def test_baseline_not_new(self):
        self.assertEqual(m.changes([row()])[0][0]['change'], 'situacion-inicial')

    def test_change_states(self):
        self.assertEqual(m.changes([row()],[row()])[0][0]['change'], 'sin-cambios')
        self.assertEqual(m.changes([row(observ='cambio')],[row()])[0][0]['change'], 'modificada')
        self.assertEqual(m.changes([row()],[])[0][0]['change'], 'nueva')
        inactive = dict(row(), activo=False)
        self.assertEqual(m.changes([inactive],[row()])[0][0]['change'], 'inactiva-en-fuente')
        self.assertEqual(m.changes([row()],[inactive])[0][0]['change'], 'reactivada')

    def test_missing_not_resolved(self):
        self.assertEqual(m.changes([],[row()])[1][0]['change'], 'ausente-revisar')

    def test_past_estimate_not_resolved(self):
        self.assertEqual(m.changes([row(ffin=1000)])[0][0]['activo'], True)

    def test_irrelevant_extra_metadata_not_changed(self):
        self.assertEqual(m.changes([row(extra='new')],[row()])[0][0]['change'], 'sin-cambios')

    def test_expected_candidate_groups(self):
        for code, area in [('J05AB01','infecciosas'),('P01BA02','infecciosas'),('N03AX09','neurologia'),('N02CC01','neurologia'),('C10AX13','hipercolesterolemia'),('L01BA01','oncohematologia'),('L02BG04','oncohematologia'),('B02BD02','oncohematologia'),('L04AC07','inmunomediadas')]:
            with self.subTest(code=code):
                self.assertEqual(m.classify(row(),{'atcs':[{'codigo':code}]},RULES)[0],[area])

    def test_specific_exception_over_parent(self):
        med = {'atcs': [{'codigo': c} for c in ['L04','L04A','L04AX','L04AX04']]}
        self.assertEqual(m.classify(row(),med,RULES)[0],['oncohematologia'])
        self.assertEqual(m.classify(row(),{'atcs':[{'codigo':'L03AB07'}]},RULES)[0],['neurologia'])

    def test_no_pediatrics_inference(self):
        med = {'nombre':'PEDIATRICO SOLUCION 1 mg', 'atcs':[{'codigo':'J01CA04'}]}
        self.assertNotIn('pediatria',m.classify(row(),med,RULES)[0])

    def test_no_name_routing(self):
        self.assertEqual(m.classify(dict(row(),nombre='ONCO INFECCIOSAS'),{'atcs':[]},RULES)[0],[m.REVIEW])

    def test_unknown_and_unverified_review(self):
        self.assertEqual(m.classify(row(),None,RULES)[0],[m.REVIEW])
        self.assertEqual(m.classify(row(),{'atcs':[{'codigo':'A02BC01'}]},RULES)[0],[m.REVIEW])

    def test_cn_multi_area_override(self):
        rules = copy.deepcopy(RULES)
        rules['cn_overrides']['000001']=['infecciosas','pediatria']
        self.assertEqual(m.classify(row(),None,rules)[0],['infecciosas','pediatria'])

    def test_no_general_neuro_psychiatry(self):
        self.assertEqual(m.classify(row(),{'atcs':[{'codigo':'N06AB06'}]},RULES)[0],[m.REVIEW])

    def test_incomplete_rejected(self):
        r = report();r['requests'][0]['payload']['totalFilas']=201
        with self.assertRaises(ValueError):m.records(r)

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):m.records(report([row(),row()]))

    def test_invalid_cn_and_state_rejected(self):
        for change in [{'cn':'1'},{'activo':'true'},{'fini':True},{'nombre':None}]:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):m.records(report([dict(row(),**change)]))

    def test_source_host_not_trusted(self):
        r = report();r['requests'][0]['url']='https://example.invalid/cima/rest/psuministro?pagina=1'
        with self.assertRaises(ValueError):m.records(r)

    def test_empty_valid_source(self):
        self.assertEqual(m.records(report([])),[])

    def test_metadata_membership(self):
        r=report();r['medicines'][0]['payload']['presentaciones']=[]
        output=m.build(r,assignments())
        self.assertEqual(output['unverified_presentations'],1)
        self.assertEqual(len(output['owners'][2]['items']),1)

    def test_partial_metadata_not_hidden(self):
        r=report([row(),row(cn='000002')])
        output=m.build(r,assignments())
        self.assertEqual(output['enriched_presentations'],1)
        self.assertEqual(output['unverified_presentations'],1)
        self.assertEqual(len(output['owners'][1]['items']),1)
        self.assertEqual(len(output['owners'][2]['items']),1)

    def test_same_owner_deduplicated_across_areas(self):
        r=report(atcs=['L04AC07']);rules=copy.deepcopy(RULES)
        rules['cn_overrides']['000001']=['inmunomediadas','pediatria']
        out=m.build(r,assignments(),rules)
        self.assertEqual(len(out['owners'][2]['items']),1)
        self.assertEqual(len(out['owners'][2]['items'][0]['areas']),2)

    def test_unchanged_suppressed_after_baseline(self):
        old=report();old['checked_at']='2026-11-10T10:00:00+00:00'
        out=m.build(report(),assignments(),previous=old)
        self.assertEqual(out['unchanged'],1)
        self.assertTrue(all(not p['items'] for p in out['owners']))

    def test_inactive_initial_not_alerted(self):
        out=m.build(report([dict(row(),activo=False)]),assignments())
        self.assertEqual(out['active'],0)
        self.assertTrue(all(not p['items'] for p in out['owners']))

    def test_missing_retains_review_label(self):
        old=report();old['checked_at']='2026-11-10T10:00:00+00:00'
        out=m.build(report([]),assignments(),previous=old)
        self.assertEqual(out['owners'][1]['items'][0]['change'],'ausente-revisar')

    def test_previous_order_rejected(self):
        with self.assertRaises(ValueError):m.build(report(),assignments(),previous=report())

    def test_unassigned_area_fails_closed(self):
        a=assignments();a['assignments'].pop()
        with self.assertRaises(ValueError):m.build(report(),a)

    def test_html_escaped_and_no_recipient_address(self):
        r=report([dict(row(),nombre='<script>alert(1)</script>',observ='<img src=x onerror=alert(1)>')])
        out=m.build(r,assignments());text=m.render(out,out['owners'][1])
        self.assertNotIn('<script>alert(1)</script>',text);self.assertIn('&lt;script&gt;',text)
        self.assertEqual(text.count('<script>'),1)
        self.assertNotIn('b@example.invalid',text)
        self.assertIn('PRUEBA · NO ENVIADO',text)
        self.assertIn('scope="col"',text)

    def test_private_write_mode_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'preview.json';m.write_private(p,'{}')
            self.assertEqual(p.stat().st_mode&0o077,0)
            link=pathlib.Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):m.write_private(link,'bad')
            self.assertEqual(p.read_text(),'{}')

    def test_rules_remain_unapproved(self):
        self.assertFalse(RULES['approved'])
        self.assertFalse(m.build(report(),assignments())['classification_approved'])

    def test_private_overview_links_and_no_emails(self):
        output=m.build(report(),assignments())
        text=m.render_index(output)
        self.assertNotIn('@example.invalid',text)
        for owner in output['owners']:
            self.assertIn(owner['id']+'.html',text)
            self.assertIn('[PRUEBA SIN ENVÍO]',owner['subject'])


if __name__=='__main__':unittest.main()
