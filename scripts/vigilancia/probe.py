"""Read-only bounded CIMA connectivity probe. Never emails or reads recipients."""
import datetime,json,pathlib,urllib.request,urllib.error,re
BASE='https://cima.aemps.es'
URLS=[BASE+'/cima/publico/listadesabastecimiento.html',BASE+'/cima/rest/psuministro?pagina=1',BASE+'/cima/resources/docs/CIMA_REST_API.pdf',BASE+'/cima/rest/medicamento?cn=604450']
def probe(url):
    result={'url':url}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'FarmaStock-Access-Test/0.1','Accept':'application/json,text/html,application/pdf'})
        with urllib.request.urlopen(req,timeout=35) as r:
            raw=r.read(2_000_001)
            result.update(status=r.status,content_type=r.headers.get('Content-Type',''),bytes=len(raw),final_url=r.url)
            if len(raw)>2_000_000: result['error']='response_over_limit'; return result
            if 'json' in result['content_type']:
                data=json.loads(raw)
                result['payload']=data
            elif 'html' in result['content_type']:
                text=raw.decode('utf-8',errors='replace')
                result['scripts']=re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',text)
                result['title']=re.findall(r'<title>(.*?)</title>',text,re.S)[:1]
    except Exception as exc:
        result.update(error=type(exc).__name__,detail=str(exc)[:300])
    return result
if __name__=='__main__':
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Connectivity and schema inspection only. No classification, monitoring or email delivery activated.','requests':[probe(u) for u in URLS]}
    first=report['requests'][1].get('payload',{})
    rows=list(first.get('resultados',[]))
    total=first.get('totalFilas',0)
    size=first.get('tamanioPagina',0)
    if isinstance(total,int) and isinstance(size,int) and 0<size<=1000 and total<=10000:
        for page in range(2,(total+size-1)//size+1):
            page_result=probe(BASE+'/cima/rest/psuministro?pagina='+str(page))
            report['requests'].append(page_result)
            rows.extend(page_result.get('payload',{}).get('resultados',[]))
    report['listing_complete']=len(rows)==total and total>0
    report['listing_count']=len(rows)
    # Sampling by name is only for inspecting metadata, NEVER a routing rule.
    candidates=[r for r in rows if re.search(r'cisplatino|paclitaxel|docetaxel|capecitabina|metotrexato|ciclofosfamida|fluorouracilo',r.get('nombre',''),re.I)][:10]
    sample={r['cn']:r for r in (rows[:2]+candidates)}
    report['enrichment_scope']='Non-exhaustive metadata sample, first two records plus selected names for inspection. Name sampling is not classification.'
    report['medicines']=[]
    for cn in sample:
        report['medicines'].append(probe(BASE+'/cima/rest/medicamento?cn='+cn))
    pathlib.Path('reports').mkdir(exist_ok=True)
    pathlib.Path('reports/cima-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for r in report['requests']:print(r['url'],r.get('status'),r.get('error',''))
