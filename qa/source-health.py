"""Source-health UI, request races and uncertainty states on the actual SQLite API.

Default is real HTTP + Chromium (mandatory CI mode). --in-memory uses the same
ASGI app via TestClient, with a browser-to-Python fetch bridge: no browser HTTP,
origin persistence or network-policy coverage is claimed in that mode.
Synthetic fixtures exist only in the temporary ledger and are labeled as such.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import uvicorn
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from server.app import create_app
from server.store import ROOT, canonical, digest, now

parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
checks=[];out=ROOT/'qa/screenshots';out.mkdir(exist_ok=True)
def check(name,passed,detail=None):
    checks.append({'test':name,'pass':bool(passed),'detail':detail})
    print(('PASS ' if passed else 'FAIL ')+name,flush=True)

def seed_fixtures(store):
    with store.connect() as db:
        payload=json.loads(db.execute("SELECT payload FROM sources WHERE id='P01'").fetchone()[0])
        payload['title']='SYNTHETIC QA source <img src=x onerror="window.healthXSS=true">'
        db.execute("UPDATE sources SET payload=? WHERE id='P01'",(canonical(payload),))
        ids=[]
        for text in ('A','B'):
            sha=hashlib.sha256(text.encode()).hexdigest();vid='fixture-version-'+text;ids.append(vid)
            db.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?,?,?)',(vid,'P01',sha,sha,'text/html','https://www.galaxy.com/',1,'2026-01-01T00:00:00+00:00'))
        for i in range(25):
            db.execute('INSERT INTO fetch_events(source_id,version_id,status,outcome,attempted_at) VALUES(?,?,?,?,?)',('P01',ids[i%2],200,'baseline' if i==0 else 'changed',now()))
            store.enqueue(db,'P01',ids[i%2],'test-fixture',{'title':f'SYNTHETIC QA queue {i} <script>window.healthXSS=true</script>','url':'javascript:alert(1)','note':'Temporary test ledger only; not a research claim.'},digest(['health',i]))
        db.execute("UPDATE jobs SET last_success=?,last_status=200 WHERE source_id='P01'",(now(),))
        stale=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat()
        db.execute("UPDATE jobs SET last_success=?,last_status=503,last_error='SYNTHETIC QA HTTP 503 <script>window.healthXSS=true</script>' WHERE source_id='P02'",(stale,))

with tempfile.TemporaryDirectory() as directory:
    app=create_app(Path(directory)/'atlas.sqlite3',background=False);seed_fixtures(app.state.store)
    client=TestClient(app);server=None;thread=None;sock=None
    if not args.in_memory:
        sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app,log_level='warning'))
        thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
        base=f'http://127.0.0.1:{port}'
        for _ in range(100):
            try:
                if httpx.get(base+'/api/health',timeout=1).status_code==200:break
            except httpx.HTTPError:pass
            time.sleep(.1)
    else:base=''
    try:
        with sync_playwright() as p:
            exe=shutil.which('chromium') or shutil.which('chromium-browser')
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
            page=browser.new_page(viewport={'width':1440,'height':1080});page.set_default_timeout(10000)
            errors=[];requests=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:requests.append(request.url))
            if args.in_memory:
                def bridge(url,headers):
                    if not url.startswith('/api/'):raise ValueError('Test bridge only exposes this ASGI API')
                    response=client.get(url,headers=headers)
                    return {'status':response.status_code,'body':response.text,'headers':dict(response.headers)}
                page.expose_function('_atlasHealthTestAPI',bridge)
                inject="""window.ATLAS_SERVICE={base:'/api'};
                window.fetch=async(input,options={})=>{const result=await window._atlasHealthTestAPI(String(input),Object.fromEntries(new Headers(options.headers).entries()));return new Response(result.status===304?null:result.body,{status:result.status,headers:result.headers});};"""
                html=(ROOT/'compute_atlas.html').read_text().replace('<script>','<script>'+inject,1)
                page.set_content(html,wait_until='load')
            else:
                response=page.goto(base,wait_until='networkidle');check('Health console boot returns HTTP 200',response.status==200)
            page.wait_for_function('window.ATLAS?.monitor && document.documentElement.classList.contains("catalog-ready")')
            page.evaluate("ATLAS.navigate('overview')")
            page.evaluate('pollAtlasMonitor()')
            page.locator('[data-atlas-action="monitor"]').click()
            page.wait_for_selector('.atlas-health-source')
            check('Worker paused is explicit','Refresh paused' in page.locator('.atlas-health-worker').inner_text())
            check('Source activity is fetched from paginated SQLite API',page.locator('.atlas-health-source').count()==12)
            check('Capture and editorial dates are separate',page.locator('.atlas-health-dates').first.locator('dt').all_inner_texts()==['Successful fetch','Editorial retrieval'])
            check('Fetch window is not factual confidence','does not mean the claims were re-reviewed' in page.locator('.atlas-health-policy').inner_text())
            check('Capture failure is visible and escaped','HTTP 503 <script>' in page.locator('[data-health-source-id="P02"]').inner_text() and page.evaluate('window.healthXSS!==true'))
            check('Unknown capture is not zero','Not yet captured' in page.locator('[data-health-source-id="P03"]').inner_text())
            page.locator('[data-health-source-id="P01"] summary').click()
            check('Full immutable content hash is inspectable',hashlib.sha256(b'A').hexdigest() in page.locator('[data-health-source-id="P01"]').inner_text())
            page.locator('[data-health-source-id="P01"] summary').click()
            page.screenshot(path=str(out/'source-health-fixture-desktop.png'))
            page.locator('[data-health-page="next"]').click();page.wait_for_function('atlasHealth.offset===12&&!atlasHealth.busy')
            check('Source next page preserves SQL pagination',page.locator('.atlas-health-source').count()==len(app.state.store.source_activity(12,12)['items']))
            page.locator('[data-health-page="previous"]').click();page.wait_for_function('atlasHealth.offset===0&&!atlasHealth.busy')
            page.locator('[data-health-source-id="P01"] h3 button').click();page.wait_for_selector('[data-health-event]')
            check('Source history is separate from accepted claims',page.locator('[data-health-event]').count()==20 and 'not editorial decisions' in page.locator('.atlas-health-policy').inner_text())
            check('Recurring A-B-A keeps original version identities',page.locator('[data-health-event] code').all_inner_texts()[:3]==['fixture-version-A','fixture-version-B','fixture-version-A'])
            check('History navigation retains useful keyboard focus',page.locator('[data-health-action="back"]').evaluate('el=>document.activeElement===el'))
            page.locator('[data-health-page="next"]').click();page.wait_for_function('atlasHealth.eventOffset===20&&!atlasHealth.busy')
            check('History next page reaches older events',page.locator('[data-health-event]').count()==5)
            check('History pagination moves focus to an available control',page.locator('[data-health-page="previous"]').evaluate('el=>document.activeElement===el'))
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#drawer').evaluate('el=>el.scrollTop=0')
            page.screenshot(path=str(out/'source-history-fixture-mobile.png'))
            check('Mobile event history has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
            page.locator('[data-health-action="back"]').click()
            page.locator('[data-health-source-id="P03"] h3 button').click();page.wait_for_function('atlasHealth.events?.total===0&&!atlasHealth.busy')
            check('No event history is an honest empty state','No fetch attempts recorded' in page.locator('.atlas-health-empty').inner_text())
            page.locator('[data-health-action="back"]').click()
            # Only fault injection is stubbed; successful requests continue to the real API.
            page.evaluate("""window.healthOriginalFetch=window.fetch;window.healthFault=null;
            window.fetch=(input,options)=>{
              if(String(input).includes('/source-activity')&&window.healthFault==='error')return Promise.resolve(new Response('Unavailable',{status:503}));
              if(String(input).includes('/source-activity')&&window.healthFault==='malformed')return Promise.resolve(new Response('{"items":null,"total":0}',{status:200}));
              if(String(input).includes('/source-activity')&&window.healthFault==='delay')return new Promise(resolve=>{window.healthRelease=()=>window.healthOriginalFetch(input,options).then(resolve);});
              return window.healthOriginalFetch(input,options);
            };void 0;""")
            old=page.evaluate('atlasHealth.activity.checked_at')
            page.evaluate("window.healthFault='error';ATLAS.monitor.refresh()")
            check('Outage retains dated results and visible warning',page.locator('.atlas-health-source').count()==12 and 'HTTP 503' in page.locator('.atlas-health-warning').inner_text() and page.evaluate('atlasHealth.activity.checked_at')==old)
            page.evaluate("window.healthFault='malformed';ATLAS.monitor.refresh()")
            check('Malformed response cannot erase good activity data','Unexpected acquisition response' in page.locator('.atlas-health-warning').inner_text() and page.locator('.atlas-health-source').count()==12)
            page.evaluate("window.healthFault=null;ATLAS.monitor.refresh()")
            check('Retry recovers without hiding the publication',page.locator('.atlas-health-warning').count()==0)
            page.locator('[data-health-tab="queue"]').click()
            check('Queue is separate and paginated',page.locator('.atlas-live-review article').count()==20)
            check('Unsafe source links are never clickable',page.locator('.atlas-live-review a[href^="javascript:"]').count()==0 and page.evaluate('window.healthXSS!==true'))
            page.locator('[data-service-page="next"]').click();page.wait_for_function('atlasQueueOffset===20')
            check('Queue next page renders last five candidates',page.locator('.atlas-live-review article').count()==5)
            page.locator('[data-health-tab="publication"]').click()
            check('Publication view never adds candidate capacities','Candidates are not accepted site totals' in page.locator('#atlas-health-panel').inner_text())
            page.locator('[data-health-tab="sources"]').click()
            page.evaluate("window.healthFault='delay';void ATLAS.monitor.refresh()")
            page.locator('[data-action="close-drawer"]').click()
            page.evaluate('window.healthRelease()')
            page.wait_for_function('!atlasHealth.busy')
            check('Late response cannot reopen a closed drawer',page.locator('#drawer').is_hidden() and page.evaluate('ATLAS.state.drawer===null'))
            # Late source-list response also cannot overwrite a newly selected history.
            page.evaluate("window.healthFault=null;ATLAS.monitor.open()")
            page.evaluate("window.healthFault='delay';void ATLAS.monitor.refresh()")
            page.locator('[data-health-source-id="P03"] h3 button').click();page.wait_for_function('atlasHealth.source?.id==="P03"&&!atlasHealth.busy')
            page.evaluate('window.healthRelease()')
            check('Request identity prevents stale cross-source overwrite',page.evaluate('atlasHealth.source.id')=='P03' and page.locator('.atlas-health-empty').count()==1)
            check('No unhandled browser exceptions',not errors,errors)
            check('No unexpected third-party requests',not [url for url in requests if url.startswith('http') and (not base or not url.startswith(base))],requests if args.in_memory else None)
            page.close()
            offline=browser.new_page(viewport={'width':390,'height':844});offline_requests=[]
            offline.on('request',lambda request:offline_requests.append(request.url))
            if args.in_memory:offline.set_content((ROOT/'compute_atlas.html').read_text(),wait_until='load')
            else:offline.goto(base+'/compute_atlas.html',wait_until='networkidle');offline_requests.clear()
            offline.wait_for_function('window.ATLAS?.monitor')
            offline.locator('[data-atlas-action="monitor"]').click()
            check('Standalone never pretends the worker is running','self-contained publication' in offline.locator('#drawer-content').inner_text())
            check('Standalone monitor never probes API or remote assets',not offline_requests,offline_requests)
            browser.close()
    finally:
        client.close()
        if server:server.should_exit=True;thread.join(timeout=10);sock.close()
report={'execution':'in-memory Chromium + real SQLite ASGI test bridge (not browser HTTP)' if args.in_memory else 'real HTTP service + Chromium','passed':sum(item['pass'] for item in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/source_health_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
