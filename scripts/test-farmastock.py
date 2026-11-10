#!/usr/bin/env python3
"""Pruebas reales de navegador y XLSX, sin librerías de hojas de cálculo.
Requiere Playwright y Chromium; artefactos temporales fuera del checkout.
"""
import datetime
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from urllib.parse import urljoin, urlsplit
from xml.sax.saxutils import escape
import zipfile
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(tempfile.mkdtemp(prefix='farmastock-pruebas-'))
WEB=OUT/'servidor'
WEB.mkdir()
(WEB/'farmastock').symlink_to(ROOT,target_is_directory=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*_args):
        pass


server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(WEB)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=f'http://127.0.0.1:{server.server_port}/farmastock/'


def xlsx(path,rows,formula=False,macro=False,compress=True):
    strings=[]
    output=[]
    for i,row in enumerate(rows,1):
        cells=[]
        for j,value in enumerate(row):
            ref=chr(65+j)+str(i)
            if isinstance(value,tuple):
                raw,style=value
                cells.append(f'<c r="{ref}" s="{style}"><v>{raw}</v></c>')
            else:
                strings.append(str(value))
                cells.append(f'<c r="{ref}" t="s"><v>{len(strings)-1}</v></c>')
        if formula and i==2:
            cells.append('<c r="J2"><f>1+1</f><v>2</v></c>')
        output.append(f'<row r="{i}">'+''.join(cells)+'</row>')
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Datos ficticios" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{ns}">'+''.join('<si><t>'+escape(s)+'</t></si>' for s in strings)+'</sst>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{ns}"><numFmts count="2"><numFmt numFmtId="164" formatCode="000000"/><numFmt numFmtId="165" formatCode="yyyy-mm-dd"/></numFmts><cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="164"/><xf numFmtId="165"/></cellXfs></styleSheet>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData>'+''.join(output)+'</sheetData></worksheet>')
        if macro:
            z.writestr('xl/vbaProject.bin',b'fake macro not executed')


def compare(page):
    page.locator('#source-reviewed').check()
    page.locator('#compare').click()
    expect(page.locator('#results')).to_be_visible()


def widths(page):
    for width in [360,390,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),(page.url,width)


try:
    with sync_playwright() as p:
        chromium=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        browser=p.chromium.launch(**({'executable_path':chromium} if chromium else {}),headless=True,args=['--no-sandbox'])
        context=browser.new_context(accept_downloads=True,permissions=['clipboard-read','clipboard-write'],locale='es-ES')
        page=context.new_page()
        errors,external,bad_http=[],[],[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:external.append(r.url) if not r.url.startswith((BASE,'blob:','data:')) else None)
        page.on('response',lambda r:bad_http.append((r.status,r.url)) if r.status>=400 else None)
        page.on('dialog',lambda dialog:dialog.accept())
        page.goto(BASE)
        page.locator('#compare').click()
        expect(page.locator('#errors')).to_contain_text('ambos ficheros')
        page.locator('#demo').click()
        page.locator('#compare').click()
        expect(page.locator('#errors')).to_contain_text('Confirma')
        compare(page)
        expect(page.locator('#report-rows tr')).to_have_count(3)
        expect(page.locator('#counts')).to_contain_text('1 fuera del catálogo')
        expect(page.locator('#report-rows tr').filter(has_text='000001')).to_contain_text('Activa según fichero')
        expect(page.locator('#report-rows tr').filter(has_text='000002')).to_contain_text('no informado')
        page.locator('#prepare-mail').click()
        expect(page.locator('#status')).to_contain_text('Selecciona')
        for code in ['000001','000002']:
            page.locator('#report-rows tr').filter(has_text=code).locator('input').check()
        page.locator('#prepare-mail').click()
        page.wait_for_function("document.getElementById('mail-text').value.includes('DEMOSTRACIÓN FICTICIA')")
        assert page.evaluate("localStorage.getItem('farmastock.demo.v1')") is None
        page.locator('#copy-mail').click()
        expect(page.locator('#status')).to_contain_text('Borrador copiado')
        assert '000001' in page.evaluate('navigator.clipboard.readText()')
        with page.expect_download() as event:
            page.locator('#download-mail').click()
        target=OUT/'borrador.txt'
        event.value.save_as(target)
        assert 'No es una alerta AEMPS real' in target.read_text()
        page.locator('#mark-sent').click()
        expect(page.locator('#status')).to_contain_text('Confirma')
        page.locator('#sent-confirm').check()
        page.locator('#mark-sent').click()
        expect(page.locator('#counts')).to_contain_text('2 ya comunicadas')
        expect(page.locator('#report-rows tr').filter(has_text='000001').locator('input')).to_be_disabled()
        assert page.evaluate("localStorage.getItem('farmastock.comunicadas.v1')") is None
        page.reload()
        page.locator('#updated-demo').click()
        compare(page)
        expect(page.locator('#report-rows tr').filter(has_text='000001')).to_contain_text('Modificada')
        expect(page.locator('#not-observed')).to_contain_text('1 incidencias')
        assert 'resuelta' not in page.locator('#not-observed li').inner_text().lower()
        widths(page)
        page.set_viewport_size({'width':1440,'height':1000})
        page.screenshot(path=str(OUT/'revision.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(OUT/'revision-movil.png'),full_page=True)
        print('PASS demo, cambios, ausencia no resuelta, correo no enviado, confirmación y persistencia separada',flush=True)

        serial=(datetime.date(2026,1,1)-datetime.date(1899,12,30)).days
        cat=OUT/'catalogo.xlsx'
        inc=OUT/'incidencias.xlsx'
        xlsx(cat,[['cn','nombre'],[(1,1),'Medicamento FICTICIO A'],[(2,1),'Medicamento FICTICIO B']],compress=False)
        payload='<img src=x onerror="window.PWNED=1"> =SUM(1)'
        xlsx(inc,[['id','cn','inicio','fin','descripcion','estado'],['TEST-X',(1,1),(serial,2),'',payload,'activa'],['TEST-Y',(2,1),(serial,2),'','=HYPERLINK("https://example.org")','activo']])
        page.locator('#catalog-file').set_input_files(cat)
        expect(page.locator('#catalog-info')).to_contain_text('Datos ficticios')
        expect(page.locator('#results')).to_be_hidden()
        page.locator('#incidents-file').set_input_files(inc)
        expect(page.locator('#incidents-info')).to_contain_text('Datos ficticios')
        page.locator('#source-title-input').fill('FICHERO FICTICIO DE PRUEBA, no descarga oficial')
        page.locator('#source-date').fill('2026-01-06')
        page.locator('#source-url').fill('https://aemps.es.attacker.com')
        page.locator('#source-reviewed').check()
        page.locator('#compare').click()
        expect(page.locator('#errors')).to_contain_text('oficial')
        page.locator('#source-url').fill('https://cima.aemps.es/cima/publico/home.html')
        compare(page)
        expect(page.locator('#report-rows tr')).to_have_count(2)
        expect(page.locator('#report-rows')).to_contain_text('000001')
        expect(page.locator('#report-rows')).to_contain_text('2026-01-01')
        expect(page.locator('#report-rows')).to_contain_text(payload)
        assert page.evaluate('window.PWNED') is None
        with page.expect_download() as event:
            page.locator('#export-report').click()
        target=OUT/'revision.csv'
        event.value.save_as(target)
        assert "'=HYPERLINK" in target.read_text()
        assert '000001' in target.read_text()
        page.locator('#source-date').fill('2026-01-07')
        expect(page.locator('#results')).to_be_hidden()
        expect(page.locator('#source-reviewed')).not_to_be_checked()
        print('PASS XLSX ZIP almacenado/deflate, cadenas compartidas, CN 000000, fechas, estado, XSS literal y CSV saneado',flush=True)

        formula=OUT/'formulas.xlsx'
        xlsx(formula,[['cn','nombre'],[(1,1),'Ficticio']],formula=True)
        page.locator('#catalog-file').set_input_files(formula)
        expect(page.locator('#errors')).to_contain_text('fórmulas')
        macro=OUT/'macros.xlsx'
        xlsx(macro,[['cn','nombre'],[(1,1),'Ficticio']],macro=True)
        page.locator('#catalog-file').set_input_files(macro)
        expect(page.locator('#errors')).to_contain_text('macros')
        malformed=OUT/'invalido.csv'
        malformed.write_text('cn;nombre\n000001;"sin cierre')
        page.locator('#catalog-file').set_input_files(malformed)
        expect(page.locator('#errors')).to_contain_text('sin cerrar')
        print('PASS rechazo de fórmulas, macros y CSV malformado sin falso informe vacío',flush=True)

        # CSV real de prueba y más de una página: se exportan todas las filas.
        csvcat=OUT/'catalogo.csv'
        csvinc=OUT/'incidencias.csv'
        csvcat.write_text('cn;nombre\n000001;FICTICIO')
        csvinc.write_text('id;cn;inicio;descripcion;estado\n'+'\n'.join(f'I-{i};000001;2026-01-01;Incidencia ficticia {i};activa' for i in range(55)))
        page.locator('#catalog-file').set_input_files(csvcat)
        expect(page.locator('#catalog-info')).to_contain_text('1 filas')
        page.locator('#incidents-file').set_input_files(csvinc)
        expect(page.locator('#incidents-info')).to_contain_text('55 filas')
        page.locator('#source-url').fill('https://cima.aemps.es/cima/publico/home.html')
        page.locator('#source-date').fill('2026-01-06')
        compare(page)
        expect(page.locator('#report-rows tr')).to_have_count(50)
        page.locator('#next').click()
        expect(page.locator('#report-rows tr')).to_have_count(5)
        with page.expect_download() as event:
            page.locator('#export-report').click()
        target=OUT/'revision-completa.csv'
        event.value.save_as(target)
        assert len(target.read_text().splitlines())==56
        widths(page)
        for control in page.locator('input,select,textarea').all():
            assert control.evaluate('(e)=>e.labels.length>0'),control.get_attribute('id')
        page.locator('#report-rows input').first.focus()
        page.keyboard.press('Space')
        expect(page.locator('#report-rows input').first).to_be_checked()
        page.locator('#sent-confirm').check()
        page.locator('#mark-sent').click()
        expect(page.locator('#counts')).to_contain_text('1 ya comunicadas')
        with page.expect_download() as event:
            page.locator('#export-history').click()
        target=OUT/'historial.json'
        event.value.save_as(target)
        history=json.loads(target.read_text())
        assert history['demo'] is False and len(history['entries'])==1
        page.evaluate("localStorage.setItem('otra-app','conservar')")
        page.locator('#clear').click()
        expect(page.locator('#results')).to_be_hidden()
        assert page.evaluate("localStorage.getItem('otra-app')")=='conservar'
        page.evaluate("localStorage.setItem('farmastock.demo.v1','roto')")
        page.locator('#demo').click()
        page.locator('#source-reviewed').check()
        page.locator('#compare').click()
        expect(page.locator('#errors')).to_contain_text('dañado')
        expect(page.locator('#results')).to_be_hidden()
        page.locator('#clear').click()
        print('PASS paginación sin pérdida en exportación, teclado, etiquetas, historial JSON y borrado sin tocar otras apps',flush=True)

        page.goto(BASE+'tutorial.html')
        for section in page.locator('section[id^=paso-]').all():
            section.locator('summary').click()
            expect(section.locator('[data-doc]')).to_have_attribute('data-loaded','true')
            section.locator('[data-progress]').check()
        expect(page.locator('#tutorial-progress')).to_contain_text('6 de 6')
        page.get_by_role('button',name='Copiar especificación reproducible').click()
        expect(page.locator('#tutorial-status')).to_contain_text('Documento copiado')
        assert 'CN de seis' in page.evaluate('navigator.clipboard.readText()')
        page.get_by_role('button',name='Copiar prompts de auditoría y mejora').click()
        page.wait_for_function("async()=>(await navigator.clipboard.readText()).includes('Prompt de auditoría')")
        page.reload()
        expect(page.locator('#tutorial-progress')).to_contain_text('6 de 6')
        page.locator('#tutorial-reset').click()
        expect(page.locator('#tutorial-progress')).to_contain_text('0 de 6')
        for detail in page.locator('section[id^=paso-] details').all():
            detail.locator('summary').click()
        widths(page)
        for link in page.locator('a[href]').all():
            href=link.get_attribute('href')
            resolved=urljoin(page.url,href)
            if urlsplit(resolved).netloc==urlsplit(BASE).netloc:
                assert urlsplit(resolved).path.startswith('/farmastock/'),href
                assert context.request.get(resolved).ok,href
        assert not errors,errors
        assert not external,external
        assert not bad_http,bad_http
        no_js=browser.new_context(java_script_enabled=False)
        fallback=no_js.new_page()
        fallback.goto(BASE+'tutorial.html')
        fallback.locator('#paso-1 summary').click()
        expect(fallback.locator('a[href$="01-problema-y-requisitos.md"]')).to_be_visible()
        no_js.close()
        print('PASS tutorial, prompts, progreso, enlaces, cuatro anchuras y alternativa sin JS; sin tráfico externo ni errores JS/HTTP',flush=True)
        browser.close()
finally:
    server.shutdown()
print('Artefactos:',OUT)
