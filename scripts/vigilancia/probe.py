"""Bounded read-only CIMA pilot collection. No recipients, no email transport."""
import concurrent.futures,datetime,json,pathlib,time,urllib.request,urllib.error,re
BASE='https://cima.aemps.es'
URLS=[BASE+'/cima/publico/listadesabastecimiento.html',BASE+'/cima/rest/psuministro?pagina=1',BASE+'/cima/resources/docs/CIMA_REST_API.pdf']
def probe(url):
    result={'url':url}
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'FarmaStock-Pilot/0.2','Accept':'application/json,text/html,application/pdf'})
            with urllib.request.urlopen(req,timeout=25) as r:
                raw=r.read(2_000_001)
                result.update(status=r.status,content_type=r.headers.get('Content-Type',''),bytes=len(raw),final_url=r.url)
                if len(raw)>2_000_000: result['error']='response_over_limit'; return result
                if 'json' in result['content_type']:result['payload']=json.loads(raw)
                elif 'html' in result['content_type']:
                    text=raw.decode('utf-8',errors='replace')
                    result['title']=re.findall(r'<title>(.*?)</title>',text,re.S)[:1]
            return result
        except urllib.error.HTTPError as exc:
            if exc.code in (429,500,502,503,504) and attempt<2:
                retry=exc.headers.get('Retry-After','')
                time.sleep(min(60,int(retry)) if retry.isdigit() else 2**(attempt+1));continue
            return dict(result,error='HTTPError',status=exc.code)
        except Exception as exc:
            if attempt<2:time.sleep(2**attempt);continue
            return dict(result,error=type(exc).__name__,detail=str(exc)[:200])
    return result

def metadata(cn):
    response=probe(BASE+'/cima/rest/medicamento?cn='+cn)
    data=response.get('payload')
    if isinstance(data,dict):
        # Only public fields needed to inspect classification; no leaflets or rich HTML.
        response['payload']={k:data[k] for k in ['nregistro','nombre','atcs','principiosActivos','viasAdministracion','formaFarmaceutica','formaFarmaceuticaSimplificada','dosis'] if k in data}
        response['payload']['presentaciones']=[{'cn':p.get('cn'),'nombre':p.get('nombre')} for p in data.get('presentaciones',[]) if isinstance(p,dict)]
    time.sleep(.2) # Pilot bounded to two workers, no unbounded bursts.
    return response

if __name__=='__main__':
    from preview import records
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Full-list pilot with candidate area rules. No automatic monitoring or email delivery activated.','requests':[probe(u) for u in URLS]}
    first=report['requests'][1].get('payload',{})
    total=first.get('totalFilas',0);size=first.get('tamanioPagina',0)
    if type(total)is int and type(size)is int and 0<size<=1000 and 0<total<=10000:
        for page in range(2,(total+size-1)//size+1):report['requests'].append(probe(BASE+'/cima/rest/psuministro?pagina='+str(page)))
    rows=records(report) # Fail closed on partial/inconsistent listing before enrichment.
    report['listing_complete']=True;report['listing_count']=len(rows)
    cns=sorted({r['cn'] for r in rows})
    report['enrichment_scope']='All distinct CNs in the validated listing, with per-CN errors reported.'
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:report['medicines']=list(pool.map(metadata,cns))
    report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['metadata_successes']=sum(r.get('status')==200 and 'error' not in r for r in report['medicines'])
    report['metadata_requested']=len(cns)
    pathlib.Path('reports').mkdir(exist_ok=True)
    pathlib.Path('reports/cima-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Validated records:',len(rows),'Metadata HTTP successes:',report['metadata_successes'],'of',len(cns))
