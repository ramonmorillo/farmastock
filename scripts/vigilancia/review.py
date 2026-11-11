"""Small private review packs from validated previews; no mail transport."""
import argparse
import copy
import json
import pathlib

from preview import enrichments, render, render_index, write_private


def atc_key(item, metadata):
    codes=tuple(sorted(a['codigo'] for a in metadata.get(item['cn'],{}).get('atcs',[]) if isinstance(a,dict) and isinstance(a.get('codigo'),str) and len(a['codigo'])==7))
    return codes or (item['cn'],)


def select_items(owner, metadata, per_area=3, doubtful=4):
    selected={}
    review_label='Pendientes de clasificación · revisión'
    for area in owner['areas']:
        if area==review_label:continue
        seen=set();count=0
        for item in owner['items']:
            if area not in item['areas']:continue
            key=atc_key(item,metadata)
            if key in seen:continue
            seen.add(key);selected[(item['cn'],item['fini'])]=item;count+=1
            if count>=per_area:break
    pending=[item for item in owner['items'] if review_label in item['areas'] and item['cn'] in metadata]
    def shared(item):
        return any(code.startswith(('L04AD','L04AA','L03AB')) for code in atc_key(item,metadata))
    pending.sort(key=lambda item:not shared(item))
    seen=set()
    for item in pending:
        key=atc_key(item,metadata)
        if key in seen:continue
        seen.add(key);selected[(item['cn'],item['fini'])]=item
        if len(seen)>=doubtful:break
    return list(selected.values())


def sample_result(result,report):
    sampled=copy.deepcopy(result)
    metadata=enrichments(report)
    for owner in sampled['owners']:
        owner['total_assigned']=len(owner['items'])
        owner['items']=select_items(owner,metadata)
        # Names help reviewers; addresses do not belong in downloadable samples.
        owner['recipient']={'name':owner['recipient'].get('name','Tus áreas')}
    return sampled


REVIEW_SCRIPT='''<style>select,button{font:inherit;min-height:44px;padding:8px}button{margin:12px 0;position:sticky;top:8px;z-index:1;background:#07505b;color:white;border:0;border-radius:8px}select{max-width:100%}
.review-ready .table{overflow:visible;background:transparent}.review-ready table{display:block;min-width:0}.review-ready caption{display:block}
.review-ready thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
.review-ready tbody{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,32rem),1fr));gap:16px}
.review-ready tr{display:grid;grid-template-columns:1fr 1fr;border:1px solid #d8e1e8;border-radius:12px;background:#fff;padding:8px}
.review-ready tr[hidden]{display:none}.review-ready td{display:block;min-width:0;padding:10px;border:0;overflow-wrap:anywhere}
.review-ready td::before{content:attr(data-label);display:block;font-size:.875rem;font-weight:650;color:#436174}
.review-ready td:nth-child(2),.review-ready td:nth-child(3),.review-ready td:nth-child(n+8){grid-column:1/-1}
.review-ready td:nth-child(2){font-weight:650}.review-ready td:last-child{border-top:1px solid #d8e1e8;margin-top:8px}
@media(max-width:500px){.review-ready tbody{display:block}.review-ready tr{display:block;margin-bottom:16px}}
</style><script>
const exportButton=document.createElement('button');exportButton.textContent='Descargar mis decisiones (JSON)';
const help=document.createElement('p');help.textContent='Valida las propuestas o indica el área correcta. Esto no envía correos ni modifica las reglas. Descarga el JSON para conservar tus respuestas.';
const tableRegion=document.querySelector('.table');tableRegion.before(help,exportButton);
const header=document.createElement('th');header.scope='col';header.textContent='Tu revisión';document.querySelector('thead tr').append(header);
for(const [index,row] of [...document.querySelectorAll('tbody tr')].entries()){
 const cell=row.insertCell();const select=document.createElement('select');select.id='decision-'+index;
 const label=document.createElement('label');label.htmlFor=select.id;label.textContent='Decisión para CN '+row.cells[0].textContent;
 for(const [value,text] of [['pending','Pendiente'],['correct','Correcta'],['other-area','Otra área'],['shared-use','Uso compartido: revisar']]){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
 const note=document.createElement('input');note.type='text';note.id='note-'+index;note.maxLength=300;
 const noteLabel=document.createElement('label');noteLabel.htmlFor=note.id;noteLabel.textContent='Área correcta o motivo (opcional)';
 cell.append(label,document.createElement('br'),select,document.createElement('br'),noteLabel,document.createElement('br'),note);
 for(const [i,td] of [...row.cells].entries())td.dataset.label=document.querySelectorAll('thead th')[i].textContent;
 row.setAttribute('aria-label','CN '+row.cells[0].textContent);
}
document.documentElement.classList.add('review-ready');
exportButton.addEventListener('click',()=>{
 const decisions=[...document.querySelectorAll('tbody tr')].map(row=>({cn:row.cells[0].textContent,name:row.cells[1].textContent,proposedAreas:row.cells[2].textContent,decision:row.querySelector('select').value,note:row.querySelector('input').value}));
 const data={mode:'review-only-no-delivery',createdAt:new Date().toISOString(),decisions};
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='farmastock-revision.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
</script>'''


def render_review(result,owner):
    text=render(result,owner)
    redundant=f'<p>Este borrador contiene {len(owner["items"])} incidencias, deduplicadas entre tus áreas. Una tabla vacía no demuestra ausencia de problemas. La fecha de fin declarada no garantiza reposición; un registro ausente requiere revisión.</p>'
    text=text.replace(redundant,'').replace('Reglas candidatas pendientes de revisión profesional. No constituye una comunicación oficial de AEMPS.','Datos de CIMA; asignaciones propuestas para revisión profesional.')
    notice=f'<p class="notice"><strong>Muestra breve para validar reglas:</strong> {len(owner["items"])} ejemplos de {owner["total_assigned"]} incidencias en tu resumen completo. No es un listado exhaustivo. Los casos sin regla se muestran como pendientes, sin asignarles una especialidad.</p>'
    return text.replace('<div class="table"',notice+'<div class="table"',1).replace('</html>',REVIEW_SCRIPT+'</html>')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--drafts',required=True);parser.add_argument('--report',required=True);parser.add_argument('--out-dir',required=True)
    args=parser.parse_args();folder=pathlib.Path(args.out_dir).resolve()
    repo=pathlib.Path(__file__).resolve().parents[2]
    if folder.is_relative_to(repo) or not folder.is_dir() or folder.stat().st_mode&0o077:raise SystemExit('Usa un directorio privado 700 fuera del repositorio.')
    result=sample_result(json.loads(pathlib.Path(args.drafts).read_text()),json.loads(pathlib.Path(args.report).read_text()))
    for owner in result['owners']:write_private(folder/(owner['id']+'.html'),render_review(result,owner))
    write_private(folder/'index.html',render_index(result).replace('Resúmenes privados por responsable','Muestras breves para validar reglas').replace('Incidencias incluidas en esta prueba','Distribución candidata de la captura completa'))
    print('Muestras privadas generadas:',[len(o['items']) for o in result['owners']],'; envíos: 0.')
