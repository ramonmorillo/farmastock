"""Bounded read-only CIMA pilot collection. No recipients, no email transport."""
import argparse,concurrent.futures,datetime,json,pathlib,time,urllib.request,urllib.error,re,threading
BASE='https://cima.aemps.es'
RATE_LIMITED=threading.Event()
DEADLINE=None
URLS=[BASE+'/cima/publico/listadesabastecimiento.html',BASE+'/cima/rest/psuministro?pagina=1',BASE+'/cima/resources/docs/CIMA_REST_API.pdf']
def probe(url):
    result={'url':url}
    for attempt in range(3):
        if DEADLINE is not None and time.monotonic()>=DEADLINE:
            return dict(result,error='TimeBudgetExceeded')
        if RATE_LIMITED.is_set():
            return dict(result,error='RateLimited',detail='Collection stopped after HTTP 429; retry in a later run.')
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
            if exc.code==429:
                RATE_LIMITED.set()
                return dict(result,error='HTTPError',status=429,retry_after=exc.headers.get('Retry-After',''))
            if exc.code in (500,502,503,504) and attempt<2:
                retry=exc.headers.get('Retry-After','')
                time.sleep(min(60,int(retry)) if retry.isdigit() else 2**(attempt+1));continue
            return dict(result,error='HTTPError',status=exc.code)
        except Exception as exc:
            if attempt<2:time.sleep(2**attempt);continue
            return dict(result,error=type(exc).__name__,detail=str(exc)[:200])
    return result

def metadata(cn):
    response=probe(BASE+'/cima/rest/medicamento?cn='+cn)
    if response.get('error') in ('TimeBudgetExceeded','RateLimited'):return response
    response['fetched_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    data=response.get('payload')
    if isinstance(data,dict):
        # Only public fields needed to inspect classification; no leaflets or rich HTML.
        response['payload']={k:data[k] for k in ['nregistro','nombre','atcs','principiosActivos','viasAdministracion','formaFarmaceutica','formaFarmaceuticaSimplificada','dosis'] if k in data}
        response['payload']['presentaciones']=[{'cn':p.get('cn'),'nombre':p.get('nombre')} for p in data.get('presentaciones',[]) if isinstance(p,dict)]
    time.sleep(.2) # Pilot bounded to two workers, no unbounded bursts.
    return response

def save_report(report):
    folder=pathlib.Path('reports')
    folder.mkdir(exist_ok=True)
    temporary=folder/'cima-probe.json.tmp'
    temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(folder/'cima-probe.json')

def cached_metadata(report,rows,now=None):
    """Reuse at most seven-day-old ATC metadata, preserving its original date."""
    from preview import enrichments
    now=now or datetime.datetime.now(datetime.timezone.utc)
    verified=enrichments(report)
    names={r['cn']:r['nombre'] for r in rows}
    cached={}
    for response in report.get('medicines',[]):
        cn=response.get('url','').split('cn=')[-1]
        if cn not in verified or cn not in names:continue
        try:
            original_date=response.get('fetched_at',report['checked_at'])
            checked=datetime.datetime.fromisoformat(original_date)
            age=now-checked
        except (ValueError,TypeError,KeyError):continue
        if not datetime.timedelta(0)<=age<datetime.timedelta(days=7):continue
        if not any(p.get('cn')==cn and p.get('nombre')==names[cn] for p in verified[cn]['presentaciones']):continue
        cached[cn]=dict(response,fetched_at=original_date,reused=True)
    return cached

if __name__=='__main__':
    from preview import records
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache')
    parser.add_argument('--budget-seconds',type=int,default=360)
    args=parser.parse_args()
    if not 30<=args.budget_seconds<=1200:raise SystemExit('Budget must be between 30 and 1200 seconds.')
    DEADLINE=time.monotonic()+args.budget_seconds
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Full-list pilot with candidate area rules. No automatic monitoring or email delivery activated.','requests':[probe(u) for u in URLS]}
    first=report['requests'][1].get('payload',{})
    total=first.get('totalFilas',0);size=first.get('tamanioPagina',0)
    if type(total)is int and type(size)is int and 0<size<=1000 and 0<total<=10000:
        for page in range(2,(total+size-1)//size+1):report['requests'].append(probe(BASE+'/cima/rest/psuministro?pagina='+str(page)))
    rows=records(report) # Fail closed on partial/inconsistent listing before enrichment.
    report['listing_complete']=True;report['listing_count']=len(rows)
    cns=sorted({r['cn'] for r in rows})
    report['enrichment_scope']='All distinct CNs in the validated listing, with per-CN errors reported.'
    cache=cached_metadata(json.loads(pathlib.Path(args.cache).read_text()),rows) if args.cache else {}
    report['medicines']=list(cache.values())
    report['metadata_reused']=len(cache)
    report['metadata_requested']=len(cns)
    report['metadata_processing_complete']=False
    save_report(report)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(metadata,cn) for cn in cns if cn not in cache]
        for future in concurrent.futures.as_completed(futures):
            report['medicines'].append(future.result())
            if len(report['medicines'])%50==0:
                save_report(report)
                print('Metadata processed:',len(report['medicines']),'of',len(cns),flush=True)
    report['medicines'].sort(key=lambda response:response['url'])
    report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['metadata_successes']=sum(r.get('status')==200 and 'error' not in r for r in report['medicines'])
    report['metadata_requested']=len(cns)
    report['metadata_processing_complete']=all(r.get('error')!='TimeBudgetExceeded' for r in report['medicines'])
    save_report(report)
    print('Validated records:',len(rows),'Metadata HTTP successes:',report['metadata_successes'],'of',len(cns))
