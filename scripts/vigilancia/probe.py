"""Read-only bounded CIMA connectivity probe. Never emails or reads recipients."""
import datetime,json,pathlib,urllib.request,urllib.error,re
BASE='https://cima.aemps.es'
URLS=[BASE+'/cima/publico/listadesabastecimiento.html',BASE+'/cima/rest/psuministro?pagina=1',BASE+'/cima/resources/docs/CIMA_REST_API.pdf']
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
    pathlib.Path('reports').mkdir(exist_ok=True)
    pathlib.Path('reports/cima-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for r in report['requests']:print(r['url'],r.get('status'),r.get('error',''))
