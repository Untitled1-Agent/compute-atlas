"""Real HTTP + Chromium tests for the SQLite-backed application (never simulated)."""
from __future__ import annotations
import json
import shutil
import socket
import tempfile
import threading
import time
from pathlib import Path

import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import uvicorn
from playwright.sync_api import sync_playwright
from server.app import create_app
from server.store import ROOT, digest

OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True)
checks=[]
def check(name,condition,detail=None):
    checks.append({'test':name,'pass':bool(condition),'detail':detail})
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)

with tempfile.TemporaryDirectory() as folder:
    app=create_app(Path(folder)/'atlas.sqlite3',background=False)
    store=app.state.store
    with store.connect() as db:
        for i in range(25):
            store.enqueue(db,'P01',None,'test-fixture',{'title':f'Review fixture {i} <script>window.xss=true</script>','url':'https://www.galaxy.com/','note':'Synthetic queue item used only in this temporary test database.'},digest(['service-test',i]))
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='warning'))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    base=f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            try:
                if httpx.get(base+'/api/health',timeout=1).status_code==200: break
            except httpx.HTTPError: pass
            time.sleep(.1)
        with sync_playwright() as p:
            exe=shutil.which('chromium') or shutil.which('chromium-browser')
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
            page=browser.new_page(viewport={'width':1440,'height':1080})
            page.set_default_timeout(10000); errors=[]; external=[]; requested=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:requested.append(r.url))
            page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base) else None)
            response=page.goto(base,wait_until='networkidle')
            page.wait_for_function('window.ATLAS && document.documentElement.classList.contains("atlas-ready")')
            check('Service-hosted app returns HTTP 200',response.status==200)
            check('Hosted bootstrap reads accepted SQL publication',base+'/api/publication' in requested)
            check('Service config uses same-origin API',page.evaluate('ATLAS_SERVICE.base')=='/api')
            page.evaluate('pollAtlasMonitor()')
            check('Paused worker is not labeled live acquisition','Refresh paused' in page.locator('#atlas-monitor-label').inner_text())
            page.locator('[data-atlas-action="monitor"]').click()
            check('Monitor queue displays first page',page.locator('.atlas-live-review article').count()==20)
            check('Untrusted source title is escaped',page.evaluate('window.xss !== true'))
            page.locator('[data-service-page="next"]').click(); page.wait_for_function('atlasQueueOffset===20')
            check('Monitor next page uses API pagination',page.locator('.atlas-live-review article').count()==5)
            page.screenshot(path=str(OUT/'service-review-queue.png'))
            page.locator('[data-action="close-drawer"]').click()
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(5)")
            check('SQL publication retains delivered critical IT boundary','133 MW' in page.locator('.atlas-feature-number').inner_text() and 'Critical IT' in page.locator('.atlas-number-boundary').inner_text())
            page.locator('#atlas-local-note').fill('Persistent service-origin research note')
            page.locator('#atlas-local-note').blur();page.reload(wait_until='networkidle')
            check('Private notes persist on the actual service origin',page.locator('#atlas-local-note').input_value()=='Persistent service-origin research note')
            page.screenshot(path=str(OUT/'service-helios-desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            check('Closed mobile sidebar cannot cover content after resizing',page.locator('#sidebar').evaluate("el=>getComputedStyle(el).visibility==='hidden' && el.inert"))
            page.locator('.mobile-menu').click()
            check('Mobile navigation opens as an accessible modal',page.locator('.mobile-menu').get_attribute('aria-expanded')=='true' and page.locator('.app-shell').evaluate('el=>el.inert'))
            page.keyboard.press('Escape')
            check('Escape closes navigation and restores keyboard focus',page.locator('.mobile-menu').evaluate('el=>document.activeElement===el') and not page.locator('.app-shell').evaluate('el=>el.inert'))
            page.locator('.mobile-menu').click();page.locator('.nav-backdrop').click(position={'x':350,'y':400})
            check('Mobile navigation dismisses through the backdrop',page.locator('.mobile-menu').get_attribute('aria-expanded')=='false')
            page.screenshot(path=str(OUT/'service-helios-mobile.png'),full_page=True)
            check('Service facility mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            page.route('**/api/status',lambda route:route.fulfill(status=503,body='Unavailable'))
            page.evaluate('pollAtlasMonitor()');page.locator('[data-atlas-action="monitor"]').click()
            check('Monitor outage is disclosed, not hidden by cached status','Live monitor unavailable' in page.locator('#drawer-content').inner_text())
            page.unroute('**/api/status')
            page.route('**/api/publication',lambda route:route.fulfill(status=503,body='Unavailable'))
            page.reload(wait_until='networkidle');page.wait_for_function('window.ATLAS && document.documentElement.classList.contains("atlas-ready")')
            check('Publication outage falls back visibly to checked-in evidence',page.locator('.atlas-service-warning').count()==1 and page.evaluate('ATLAS.primary.observations.length')>0)
            check('Service app has no uncaught browser errors',not errors,errors)
            check('Service browser makes no third-party requests',not external,external)
            browser.close()
    finally:
        server.should_exit=True;thread.join(timeout=10);sock.close()
report={'execution':'real HTTP service with Chromium','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/service_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
