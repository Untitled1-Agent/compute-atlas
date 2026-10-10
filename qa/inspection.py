"""Actual HTTP Chromium: touch, geometry selection, research and protected prefix.

The Basic Auth proxy and its credentials are temporary test fixtures, not the
production authentication configuration. Every geometry comes from app data.
"""
from __future__ import annotations
import base64
import json
import shutil
import socket
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import uvicorn
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.app import create_app

OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True)
checks=[]
def check(name,condition,detail=None):
    checks.append({'test':name,'pass':bool(condition),'detail':detail})
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def touch(page,center,scale=1.4,translation=(18,11)):
    """CDP delivers real browser touch/pointer events, including capture."""
    session=page.context.new_cdp_session(page)
    x,y=center;dx,dy=translation
    def points(distance,cx,cy):
        return [{'id':1,'x':cx-distance,'y':cy,'radiusX':3,'radiusY':3},
                {'id':2,'x':cx+distance,'y':cy,'radiusX':3,'radiusY':3}]
    session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':points(38,x,y)})
    for step in range(1,7):
        f=step/6
        session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':points(38*(1+(scale-1)*f),x+dx*f,y+dy*f)})
    session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});session.detach()
    page.wait_for_timeout(60)

static=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=static.serve_forever,daemon=True).start()
static_base=f'http://127.0.0.1:{static.server_port}/'

with tempfile.TemporaryDirectory() as folder:
    app=create_app(Path(folder)/'atlas.sqlite3',background=False,root_path='/compute')
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    service=uvicorn.Server(uvicorn.Config(app,log_level='warning'))
    thread=threading.Thread(target=lambda:service.run(sockets=[sock]),daemon=True);thread.start()
    origin=f'http://127.0.0.1:{port}'
    token='Basic '+base64.b64encode(b'researcher:temporary-qa').decode()
    class ProtectedProxy(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):
            if not self.path.startswith('/compute/'):
                self.send_error(404);return
            if self.headers.get('Authorization')!=token:
                self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="Atlas QA"');self.end_headers();return
            response=httpx.get(origin+self.path[len('/compute'):],timeout=30,trust_env=False)
            self.send_response(response.status_code)
            for key,value in response.headers.items():
                if key.lower() not in {'content-length','connection','transfer-encoding'}:self.send_header(key,value)
            self.send_header('Content-Length',str(len(response.content)));self.end_headers();self.wfile.write(response.content)
    proxy=ThreadingHTTPServer(('127.0.0.1',0),ProtectedProxy)
    threading.Thread(target=proxy.serve_forever,daemon=True).start()
    protected=f'http://127.0.0.1:{proxy.server_port}/compute/'
    try:
        for _ in range(100):
            try:
                if httpx.get(origin+'/api/health',timeout=1).status_code==200:break
            except httpx.HTTPError:pass
            time.sleep(.1)
        for path in ('','api/publication','src/app.js','data/evidence.json','originals/compute_infrastructure_report.pdf','compute_atlas.html'):
            check('Unauthenticated protected '+(path or 'entry')+' returns 401',httpx.get(protected+path).status_code==401)
        with sync_playwright() as p:
            exe=shutil.which('chromium') or shutil.which('chromium-browser') or p.chromium.executable_path
            browser=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
            for label,url in [('hosted',static_base+'index.html'),('standalone',static_base+'compute_atlas.html'),('protected-service',protected)]:
                context=browser.new_context(viewport={'width':1440,'height':1080},has_touch=True,accept_downloads=True,http_credentials={'username':'researcher','password':'temporary-qa'})
                page=context.new_page();page.set_default_timeout(12000);errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
                check(label+' launches over actual HTTP',page.goto(url).status==200)
                page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
                before=page.evaluate('({sites:ATLAS.data.sites.length,quantities:ATLAS.coverage.metrics().quantities,features:ATLAS.catalog.data.records.length})')
                page.locator('[data-coverage-candidates]').first.click();page.locator('#atlas-candidate-query').fill('atNorth')
                check(label+' research search finds three Nordic leads',page.locator('.atlas-coverage-candidate').count()==3)
                page.locator('#atlas-candidate-query').fill('FIN05')
                text=page.locator('#atlas-candidate-results').inner_text()
                check(label+' planned IT, gross and secured power stay separate',all(s in text for s in ('230 MW','≤ 160 MW','60 MW','75 MW','planned','no total is computed')))
                with page.expect_download() as transfer:page.locator('[data-candidate-export]').click()
                exported=json.loads(Path(transfer.value.path()).read_text())
                check(label+' lead export keeps null geography and exact source scopes',len(exported['candidates'])==1 and exported['candidates'][0]['latitude'] is None and {s['id'] for s in exported['sources']}=={'P23','P24'} and exported['candidates'][0]['candidate_measurements'][1]['comparison']=='lte')
                page.locator('.atlas-candidate-measurements [data-id="P24"]').click()
                check(label+' lead quantity opens dated primary evidence','2026-10-05' in page.locator('#drawer-content').inner_text() and page.locator('#drawer-content a[href*="atnorth-to-develop"]').count()==1)
                page.locator('[data-action="drawer-back"]').click()
                check(label+' source Back retains candidate query',page.locator('#atlas-candidate-query').input_value()=='FIN05')
                page.locator('#atlas-candidate-query').fill('<img src=x onerror=window.candidateXSS=true>')
                check(label+' lead input is escaped and absent is not zero',page.locator('#atlas-candidate-results img').count()==0 and page.evaluate('window.candidateXSS!==true') and 'not zero' in page.locator('#atlas-candidate-results').inner_text())
                page.locator('[data-action="close-drawer"]').click();page.evaluate('openSearch()');page.locator('#global-search').fill('Salo')
                page.locator('[data-coverage-candidate="atnorth-fin05-candidate"]').click()
                check(label+' global search opens the actual research lead',page.locator('[data-research-candidate="atnorth-fin05-candidate"]').count()==1 and page.locator('#search-modal').is_hidden())
                page.screenshot(path=str(OUT/f'{label}-nordic-research.png'))
                page.locator('[data-action="close-drawer"]').click()
                check(label+' leads do not increase sites, features or accepted quantities',before==page.evaluate('({sites:ATLAS.data.sites.length,quantities:ATLAS.coverage.metrics().quantities,features:ATLAS.catalog.data.records.length})'))

                page.evaluate("ATLAS.catalog.select('osm-way-1121454055')")
                page.locator('#scene-context').check();page.wait_for_timeout(80)
                other=page.evaluate('ATLAS.catalog.scene().features.find(f=>f.record.kind==="building"&&f.record.id!==ATLAS.catalog.scene().record.id).record.id')
                camera=page.evaluate('JSON.stringify([ATLAS.catalog.scene().yaw,ATLAS.catalog.scene().pitch,ATLAS.catalog.scene().zoom,ATLAS.catalog.scene().pan])')
                page.locator('#scene-feature').select_option(other)
                check(label+' accessible geometry selection preserves the camera',camera==page.evaluate('JSON.stringify([ATLAS.catalog.scene().yaw,ATLAS.catalog.scene().pitch,ATLAS.catalog.scene().zoom,ATLAS.catalog.scene().pan])') and page.evaluate('ATLAS.catalog.scene().inspected.id')==other)
                check(label+' inspector links actual geometry and keeps identity uncertain',page.locator('#scene-inspector-detail a').first.get_attribute('href')==page.evaluate('ATLAS.catalog.feature(ATLAS.catalog.scene().inspected.id).source_url') and 'common ownership' in page.locator('#scene-inspector-detail').inner_text())
                saved_url=page.url
                page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
                check(label+' deep link restores the inspected source feature',page.url==saved_url and page.evaluate('ATLAS.catalog.scene().inspected.id')==other and page.locator('#scene-context').is_checked())
                # Find a genuinely visible sourced surface, then select it with the mouse.
                hit=page.evaluate('''(()=>{const s=ATLAS.catalog.scene();s.draw();for(let y=110;y<s.h-100;y+=8)for(let x=30;x<s.w-30;x+=8){const rect=s.canvas.getBoundingClientRect(),f=s.hit({clientX:rect.left+x,clientY:rect.top+y});if(f&&f.record.id!==s.inspected.id)return {x,y,id:f.record.id};}return null;})()''')
                box=page.locator('#globe-canvas').bounding_box()
                if hit:page.mouse.click(box['x']+hit['x'],box['y']+hit['y'])
                check(label+' actual visible surface click selects its source record',hit is not None and page.evaluate('ATLAS.catalog.scene().inspected.id')==hit['id'],hit)
                page.locator('#globe-canvas').focus();page.keyboard.press('ArrowRight');page.keyboard.press('Shift+ArrowDown')
                anchor=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {point:s.project3(0,0),yaw:s.yaw,pitch:s.pitch,zoom:s.zoom};})()')
                touch(page,(box['x']+anchor['point']['x'],box['y']+anchor['point']['y']))
                after=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {point:s.project3(0,0),yaw:s.yaw,pitch:s.pitch,zoom:s.zoom};})()')
                check(label+' real two-finger pinch zooms after orbit and keyboard pan',after['zoom']>anchor['zoom'] and after['yaw']==anchor['yaw'] and after['pitch']==anchor['pitch'])
                check(label+' pinch anchors the projected point while translating',abs(after['point']['x']-anchor['point']['x']-18)<1 and abs(after['point']['y']-anchor['point']['y']-11)<1,{'before':anchor,'after':after})
                point=after['point'];page.mouse.move(box['x']+point['x'],box['y']+point['y']);page.mouse.wheel(0,-.5);page.wait_for_timeout(50)
                fine=page.evaluate('ATLAS.catalog.scene().project3(0,0)')
                check(label+' tiny trackpad wheel stays anchored after pinch',page.evaluate('ATLAS.catalog.scene().zoom')>after['zoom'] and abs(fine['x']-point['x'])<.1 and abs(fine['y']-point['y'])<.1)
                page.screenshot(path=str(OUT/f'{label}-geometry-inspection.png'))
                with page.expect_download() as transfer:page.locator('#scene-inspector-detail [data-catalog-export]').click()
                exported=json.loads(Path(transfer.value.path()).read_text())
                check(label+' selected geometry export contains no illustrative height',exported['feature']['id']==page.evaluate('ATLAS.catalog.scene().inspected.id') and 'displayHeight' not in exported and exported['feature']==page.evaluate('ATLAS.catalog.scene().inspected'))

                page.evaluate("ATLAS.catalog.go({feature:null,region:'Europe',country:'Germany',camera:null})")
                page.wait_for_timeout(60)
                anchor=page.evaluate('(()=>{const s=ATLAS.getGlobe();s.prepare();return {p:s.project(8.7,50.1),span:s.bounds[2]-s.bounds[0]};})()');box=page.locator('#globe-canvas').bounding_box()
                touch(page,(box['x']+anchor['p']['x'],box['y']+anchor['p']['y']),translation=(12,9))
                after=page.evaluate('(()=>{const s=ATLAS.getGlobe();s.prepare();return {p:s.project(8.7,50.1),span:s.bounds[2]-s.bounds[0]};})()')
                check(label+' map pinch preserves the geographic anchor and selection',after['span']<anchor['span'] and abs(after['p']['x']-anchor['p']['x']-12)<1 and abs(after['p']['y']-anchor['p']['y']-9)<1 and page.evaluate('ATLAS.catalog.state.feature===null'))
                page.set_viewport_size({'width':390,'height':844});page.evaluate("ATLAS.catalog.select('osm-way-1121454055')");page.locator('#scene-context').check();page.locator('#scene-feature').select_option(other)
                check(label+' mobile inspector and source selection fit the viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                page.locator('#globe-canvas').scroll_into_view_if_needed()
                mobile_anchor=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {p:s.project3(0,0),yaw:s.yaw,zoom:s.zoom,id:s.inspected.id};})()')
                mobile_box=page.locator('#globe-canvas').bounding_box()
                touch(page,(mobile_box['x']+mobile_anchor['p']['x'],mobile_box['y']+mobile_anchor['p']['y']),scale=1.2,translation=(5,4))
                mobile_after=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {p:s.project3(0,0),yaw:s.yaw,zoom:s.zoom,id:s.inspected.id};})()')
                check(label+' mobile two-finger gesture preserves selection and anchors geometry',mobile_after['zoom']>mobile_anchor['zoom'] and mobile_after['yaw']==mobile_anchor['yaw'] and mobile_after['id']==mobile_anchor['id'] and abs(mobile_after['p']['x']-mobile_anchor['p']['x']-5)<1 and abs(mobile_after['p']['y']-mobile_anchor['p']['y']-4)<1)
                # A canceled single-finger orbit must release capture and keep the record.
                session=context.new_cdp_session(page)
                x=mobile_box['x']+120;y=mobile_box['y']+180
                session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':7,'x':x,'y':y}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':7,'x':x+30,'y':y+5}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});session.detach()
                check(label+' canceled mobile orbit releases gesture without selecting another feature',page.evaluate('(()=>{const s=ATLAS.catalog.scene();return s.gestures.pointers.size===0&&s.drag===null;})()') and page.evaluate('ATLAS.catalog.scene().inspected.id')==mobile_anchor['id'])
                page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(60)
                page.screenshot(path=str(OUT/f'{label}-geometry-mobile.png'),full_page=True)
                if label=='protected-service':
                    http_requests=[r for r in requests if r.startswith('http')]
                    check('Protected service assets and API calls all stay under /compute/',all(r.startswith(protected) for r in http_requests),[r for r in http_requests if not r.startswith(protected)])
                    check('Protected service loads accepted SQLite publications',any('/compute/api/catalog/publication' in r for r in requests) and page.evaluate('ATLAS_SERVICE.base')=='/compute/api' and not page.evaluate('!!window.ATLAS_SERVICE_WARNING'))
                check(label+' no unexpected third-party browser requests',all(r.startswith(static_base) or r.startswith(protected) for r in requests if r.startswith('http')))
                check(label+' no uncaught JavaScript exceptions',not errors,errors)
                context.close()
            browser.close()
    finally:
        proxy.shutdown();proxy.server_close();static.shutdown();static.server_close()
        service.should_exit=True;thread.join(timeout=10)

report={'execution':'actual HTTP hosted + standalone + Basic Auth proxy /compute/ SQLite service; CDP touch events','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/inspection_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
raise SystemExit(0 if report['passed']==report['total'] else 1)
