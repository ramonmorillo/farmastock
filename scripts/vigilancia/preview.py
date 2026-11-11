"""Pilot previews only. No SMTP, delivery SDK, network requests or delivery state."""
import argparse,datetime,json,pathlib,re,hashlib
SOURCE='https://cima.aemps.es/cima/publico/listadesabastecimiento.html'
def records(report):
    pages=[r for r in report['requests'] if '/rest/psuministro?' in r['url']]
    first=pages[0]['payload']; total=first['totalFilas'];size=first['tamanioPagina']
    if not isinstance(total,int) or not isinstance(size,int) or total<=0 or size<=0:raise ValueError('Invalid pagination')
    count=(total+size-1)//size
    if len(pages)!=count:raise ValueError('Incomplete pagination')
    rows=[]
    for expected,p in enumerate(pages,1):
        d=p.get('payload',{})
        if p.get('status')!=200 or d.get('pagina')!=expected or d.get('totalFilas')!=total or d.get('tamanioPagina')!=size:raise ValueError('Inconsistent page')
        batch=d.get('resultados')
        if not isinstance(batch,list) or len(batch)!=min(size,total-len(rows)):raise ValueError('Incomplete page')
        rows.extend(batch)
    seen=set()
    for r in rows:
        if not re.fullmatch(r'\d{6}',r.get('cn','')) or type(r.get('activo')) is not bool or not isinstance(r.get('fini'),int):raise ValueError('Invalid record')
        key=(r['cn'],r['fini'])
        if key in seen:raise ValueError('Duplicate incident; review source')
        seen.add(key)
    return rows

def signature(row):
    return hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def changes(current,previous=None):
    """First download is baseline, missing records are never marked resolved."""
    old={(r['cn'],r['fini']):r for r in previous or []}
    out=[]
    for r in current:
        key=(r['cn'],r['fini']);before=old.get(key)
        kind='situacion-inicial' if previous is None else ('nueva' if before is None else 'modificada' if signature(r)!=signature(before) else 'sin-cambios')
        out.append(dict(r,change=kind))
    return out,[dict(r,change='ausente-revisar') for key,r in old.items() if key not in {(n['cn'],n['fini']) for n in current}]

def classify(row,medicine=None,external_cns=()):
    areas=[];reasons=[]
    # Candidate rule, pending professional approval. L02 is intentionally excluded.
    atcs=[a.get('codigo','') for a in (medicine or {}).get('atcs',[]) if isinstance(a,dict)]
    if any(re.fullmatch(r'L01[A-Z0-9]{0,4}',code) for code in atcs):
        areas.append('oncologia');reasons.append('ATC L01: candidato antineoplásico; regla pendiente de aprobación')
    if row['cn'] in external_cns:
        areas.append('consultas-externas');reasons.append('CN seleccionado explícitamente para Consultas externas')
    return areas,reasons

def date(value):
    if value is None:return 'No indicada'
    if not isinstance(value,int):return 'Dato pendiente de revisión'
    return datetime.datetime.fromtimestamp(value/1000,datetime.timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y')

def build(report,recipients,external_cns=()):
    rows=records(report); enriched={}
    for response in report.get('medicines',[]):
        if response.get('status')==200 and isinstance(response.get('payload'),dict):
            cn=response['url'].split('cn=')[-1]
            medicine=response['payload']
            # Require exact presentation membership; do not trust a returned generic drug.
            if any(str(p.get('cn'))==cn for p in medicine.get('presentaciones',[])):
                enriched[cn]=medicine
    digests={a:[] for a in ['oncologia','consultas-externas']};pending=[]
    for row in changes(rows)[0]:
        areas,reasons=classify(row,enriched.get(row['cn']),external_cns)
        if not areas:pending.append(row);continue
        for a in areas:digests[a].append(dict(row,reasons=reasons))
    result={'mode':'preview-no-delivery','checked_at':report['checked_at'],'total':len(rows),'enriched_presentations':len(enriched),'pending_review':len(pending),'classification_approved':False,'digests':{}}
    for area,items in digests.items():
        lines=['PRUEBA · NO ENVIADO · REGLAS PENDIENTES DE APROBACIÓN',f'Área: {area}',f'Consulta: {datetime.datetime.fromisoformat(report["checked_at"]).astimezone(__import__("zoneinfo").ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M %Z")}',f'Fuente: {SOURCE}','Primera captura: situación inicial, no novedades desde ayer.','Metadatos farmacológicos revisados solo para una muestra. No es cobertura completa.','']
        if not items:lines+=['Sin asignaciones en esta prueba. Esto NO significa ausencia de problemas de suministro.']
        for r in items:
            lines += [f'CN {r["cn"]} · {r["nombre"]}',f'Estado declarado: {"activo" if r["activo"] else "no activo"}; inicio: {date(r["fini"])}; fin declarado: {date(r.get("ffin"))} (no garantiza reposición)',f'Motivo: {"; ".join(r["reasons"])}',f'Observaciones de la fuente: {r.get("observ", "No indicadas")}', '']
        result['digests'][area]={'recipients':recipients.get(area,[]),'count':len(items),'subject':f'[PRUEBA SIN ENVÍO] FarmaStock · {area} · situación inicial','body':'\n'.join(lines)}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--recipients',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    output=pathlib.Path(a.out)
    if not output.parent.is_dir():raise SystemExit('Create a private output directory first')
    result=build(json.loads(pathlib.Path(a.report).read_text()),json.loads(pathlib.Path(a.recipients).read_text()))
    import os
    fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    os.chmod(output,0o600)
    print(json.dumps({k:v for k,v in result.items() if k!='digests'},ensure_ascii=False))
    print('Borradores privados generados. Envíos: 0.')
