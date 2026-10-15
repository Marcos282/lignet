"""Optional UI QA. Run against a local dev server; every diagnostic API is mocked.
Uses installed Chrome; never starts real Globalping measurements or fetches tiles.
"""
import base64
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

BASE=os.environ.get('LIGNET_PREVIEW_URL','http://127.0.0.1:8097')
OUT=Path('/tmp/lignet-globalping-qa');OUT.mkdir(exist_ok=True)
ID='12345678-1234-4234-8234-123456789abc'
PIXEL=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGN8AAAAASUVORK5CYII=')


def result(kind):
    row={'city':'São Paulo','country':'BR','network':'Rede de teste','asn':64500,'latitude':-23.5,'longitude':-46.6,'status':'finished','address':'1.1.1.1','hostname':'example.com','raw_output':'<img src=x onerror=alert(1)> texto retornado','min':0,'avg':1.5,'max':2,'loss':0,'hops':[{'number':1,'address':None,'hostname':None,'rtts':[],'no_reply':True},{'number':2,'address':'1.1.1.1','hostname':'example.com','rtts':[1,2],'no_reply':False}],'answers':[{'name':'example.com.','type':'A','class':'IN','ttl':30,'value':'1.1.1.1'}],'resolver':'8.8.8.8','dns_status':'NOERROR','dns_code':0,'total':12,'http_status':301,'http_status_name':'Moved Permanently','location':'https://example.com/new','timings':{'total':25,'tcp':0,'tls':None,'dns':1,'firstByte':20,'download':4},'tls':None}
    rows=[row]
    if kind=='dns':rows.append({**row,'city':'Frankfurt','country':'DE','latitude':50.1,'longitude':8.6,'resolver':'1.1.1.1','answers':[{**row['answers'][0],'value':'8.8.8.8'}]})
    return {'id':ID,'type':kind,'target':'example.com','status':'finished','created_at':'2026-10-15T20:00:00Z','measured_at':'2026-10-15T20:00:01Z','expires_at':'2026-10-16T20:00:00Z','from_cache':False,'probes_requested':len(rows),'probes_count':len(rows),'remote_id':'testRemote','usage':{'consumed':len(rows),'remaining':248,'limit':250},'error':'','results':{'rows':rows,'completed':len(rows),'dns_different':True if kind=='dns' else None},'poll_after':2}


with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/opt/google/chrome/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in [1440,390]:
        context=browser.new_context(viewport={'width':width,'height':1000})
        page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('https://tile.openstreetmap.org/**',lambda r:r.fulfill(status=200,content_type='image/png',body=PIXEL))
        page.route('https://cdn.jsdelivr.net/**',lambda r:r.abort())
        state={'kind':'ping','requests':[]}
        def api(route):
            request=route.request
            if '/historico/' in request.url:body={'measurements':[],'history_hours':24}
            elif request.method=='POST':
                payload=request.post_data_json;state['requests'].append(payload);state['kind']=payload['kind'];body={'id':ID,'status':'queued'}
                assert payload['authorized'] is True
                assert payload['locations']==['country:BR']
            else:body=result(state['kind'])
            route.fulfill(status=202 if request.method=='POST' else 200,content_type='application/json',body=json.dumps(body))
        page.route('**/api/globalping/**',api)
        for kind,slug in [('ping','ping-mundial'),('traceroute','traceroute-mundial'),('dns','dns-mundial'),('http','http-mundial')]:
            page.goto(BASE+'/ferramentas/'+slug+'/');expect(page.locator('#gp-map .leaflet-control-attribution')).to_contain_text('OpenStreetMap')
            page.locator('[name=target]').fill('example.com');page.locator('[name=locations]').select_option(['country:BR']);page.locator('[name=probes]').fill('1');page.locator('[name=authorized]').check();page.locator('#gp-submit').click()
            expect(page.locator('#gp-state')).to_have_text('Concluído');expect(page.locator('#gp-results')).to_contain_text('São Paulo')
            expect(page.locator('#gp-map .leaflet-marker-icon')).to_have_count(2 if kind=='dns' else 1)
            assert page.locator('#gp-results img').count()==0
            if kind=='traceroute':expect(page.locator('#gp-results')).to_contain_text('Sem resposta')
            if kind=='dns':expect(page.locator('#gp-summary')).to_contain_text('Há diferenças')
            if kind=='http':expect(page.locator('#gp-results')).to_contain_text('https://example.com/new')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),(width,kind,'horizontal overflow')
            page.screenshot(path=str(OUT/f'{kind}-{width}.png'),full_page=True)
        assert len(state['requests'])==4
        assert not errors,errors
        print(f'UI {width}px: 4 tipos, mapa, tabelas e autorização OK; sem erros JavaScript.')
        context.close()
    browser.close()
