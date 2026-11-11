"""Browser checks with synthetic addresses only; no source requests or mail delivery."""
import functools
import http.server
import importlib.util
import pathlib
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('pilot_tests',ROOT/'tests/vigilancia/test_preview.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
OUT=pathlib.Path(tempfile.mkdtemp(prefix='farmastock-vigilancia-browser-'))
result=t.m.build(t.report([dict(t.row(),nombre='PRUEBA <script>window.bad=true</script>')]),t.assignments())
for owner in result['owners']:(OUT/(owner['id']+'.html')).write_text(t.m.render(result,owner))
(OUT/'index.html').write_text(t.m.render_index(result))
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(OUT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as p:
  chromium=shutil.which('chromium')
  browser=p.chromium.launch(**({'executable_path':chromium} if chromium else {}),headless=True,args=['--no-sandbox'])
  page=browser.new_page();errors=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:external.append(r.url) if not r.url.startswith(base) else None)
  page.goto(base+'index.html')
  expect(page.get_by_role('heading',name='FarmaStock Alert · prueba por áreas')).to_be_visible()
  assert page.locator('a[href^="responsable-"]').count()==3
  page.set_viewport_size({'width':360,'height':850})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  for owner in result['owners']:
   page.goto(base+owner['id']+'.html')
   expect(page.get_by_role('heading',level=1)).to_be_visible()
   assert not page.evaluate('Boolean(window.bad)')
   assert '@example.invalid' not in page.content()
   for width in [360,390,768,1440]:
    page.set_viewport_size({'width':width,'height':900})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   if owner['items']:
    search=page.get_by_label('Filtrar por medicamento, CN o área')
    search.fill('NO-COINCIDE');expect(page.locator('tbody tr:visible')).to_have_count(0)
    search.fill('000001');expect(page.locator('tbody tr:visible')).to_have_count(1)
    search.fill('');search.focus();page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.classList.contains("table")')
    page.get_by_text('Reglas y límites de esta prueba').click()
    expect(page.get_by_text('Pediatría sigue pendiente',exact=False)).to_be_visible()
   page.set_viewport_size({'width':390,'height':850});page.screenshot(path=str(OUT/(owner['id']+'-movil.png')),full_page=True)
  assert not errors,errors
  assert not external,external
  browser.close()
 print('Navegador: tres resúmenes, cuatro anchos, filtro, teclado, escape HTML y ausencia de peticiones externas: OK')
 print('Artefactos sintéticos:',OUT)
finally:server.shutdown()
