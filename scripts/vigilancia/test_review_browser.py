"""Review form and offline JSON export, synthetic data and no mail capability."""
import functools,http.server,importlib.util,json,pathlib,shutil,tempfile,threading
from playwright.sync_api import sync_playwright,expect
import review
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('fixtures_review_browser',ROOT/'tests/vigilancia/test_preview.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
report=t.report([dict(t.row(),nombre='<script>window.injected=true</script>')])
result=review.sample_result(t.m.build(report,t.assignments()),report)
OUT=pathlib.Path(tempfile.mkdtemp(prefix='farmastock-review-browser-'))
for owner in result['owners']:(OUT/(owner['id']+'.html')).write_text(review.render_review(result,owner))
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(OUT)))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
  page=browser.new_page(accept_downloads=True);errors=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:external.append(r.url) if not r.url.startswith((base,'blob:')) else None)
  for owner in result['owners']:
   page.goto(base+owner['id']+'.html')
   assert page.locator('tbody tr').count()==len(owner['items'])
   for width in [360,390,768,1440]:
    page.set_viewport_size({'width':width,'height':900})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   if owner['items']:
    select=page.get_by_label('Decisión para CN 000001')
    select.select_option('other-area');select.focus();page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.id')=='note-0'
    page.get_by_label('Área correcta o motivo (opcional)').fill('Ejemplo <script>window.injected=true</script>')
   with page.expect_download() as event:page.get_by_role('button',name='Descargar mis decisiones (JSON)').click()
   download=event.value;file=OUT/(owner['id']+'.json');download.save_as(file);data=json.loads(file.read_text())
   assert data['mode']=='review-only-no-delivery'
   assert len(data['decisions'])==len(owner['items'])
   if owner['items']:assert data['decisions'][0]['decision']=='other-area'
   assert '@example.invalid' not in file.read_text()
   assert not page.evaluate('Boolean(window.injected)')
   page.set_viewport_size({'width':390,'height':850});page.screenshot(path=str(OUT/(owner['id']+'-mobile.png')),full_page=True)
  assert not errors,errors;assert not external,external
  browser.close()
 print('Revisión: tres responsables, móvil, teclado, decisiones y JSON offline sin direcciones ni envío: OK')
 print('Artefactos sintéticos:',OUT)
finally:server.shutdown()
