"""Two independent source collections, publisher map, and pointer-anchored 3D.
Default: actual hosted/standalone/SQLite-backed HTTP. --in-memory: embedded only.
"""
from __future__ import annotations
import argparse, copy, json, sys, tempfile, threading, time
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.digital_realty import validate
parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 checks.append({'test':name,'pass':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def overflow(p):return p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=None;service=None
if not args.in_memory:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/' if server else ''
publication=json.loads((ROOT/'data/catalog/digital-realty.json').read_text())
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('chromium-browser') or p.chromium.executable_path,args=['--no-sandbox'])
  for entry in (['compute_atlas.html'] if args.in_memory else ['index.html','compute_atlas.html']):
   page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True);page.set_default_timeout(10000)
   errors=[];external=[];http_errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
   page.on('response',lambda r:http_errors.append(r.url) if r.status>=400 else None)
   if args.in_memory:page.set_content((ROOT/entry).read_text(),wait_until='load')
   else:check(entry+' returns actual HTTP 200',page.goto(base+entry).status==200)
   page.wait_for_function('document.documentElement.classList.contains("publisher-ready")');page.wait_for_timeout(120)
   check(entry+' world map keeps all four headline metrics visible',page.locator('.catalog-kpis').first.evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
   original=page.evaluate('JSON.stringify([ATLAS.data,ATLAS.catalog.data,ATLAS.operators.data])')
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-publisher-world-layout.png'))
   page.locator('.catalog-mode-switch [data-id="operators"]').click();page.locator('[data-publisher-home]').click()
   check(entry+' operator switching opens a separate publisher map',page.evaluate('ATLAS.state.view==="publisher"') and page.locator('#publisher-map').count()==1)
   check(entry+' all 261 browser records match the accepted source projection',page.evaluate('ATLAS.publisher.data')==publication)
   check(entry+' no publisher pin claims an IT load or polygon',page.evaluate('ATLAS.publisher.data.records.every(r=>r.it_mw===null&&!r.geometry&&r.coordinates.basis==="publisher_pin")'))
   page.locator('[data-publisher-region="Europe"]').first.click();page.wait_for_timeout(100)
   check(entry+' Europe has 111 source entries rather than an empty map',page.evaluate('ATLAS.publisher.rows().length')==111)
   check(entry+' all selected European pins fit the usable map viewport',page.evaluate('(()=>{const s=ATLAS.publisher.scene();s.prepare();return s.scope.sites.every(r=>{const p=s.project(r.lon,r.lat);return p.x>10&&p.x<s.w-10&&p.y>85&&p.y<s.h-110;});})()'))
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-publisher-europe.png'))
   page.locator('[data-publisher-region="EMEA"]').click()
   check(entry+' EMEA remains a distinct 128-entry source group',page.evaluate('ATLAS.publisher.rows().length')==128)
   page.locator('#publisher-country').select_option('Germany')
   check(entry+' raw country filtering clears incompatible regional selection',page.evaluate('ATLAS.publisher.state.region==="All"&&ATLAS.publisher.rows().length===27'))
   page.locator('[data-publisher-page="1"]').click()
   check(entry+' publisher pagination changes the actual records and retains focus',page.evaluate('ATLAS.publisher.state.page===1') and page.locator('[data-publisher-page="1"]').evaluate('e=>e===document.activeElement'))
   page.locator('#publisher-query').fill('FRA1');page.wait_for_timeout(180)
   check(entry+' typing preserves query focus and resets pagination',page.evaluate('ATLAS.publisher.state.page===0') and page.locator('#publisher-query').evaluate('e=>e===document.activeElement'))
   check(entry+' text filtering updates map and list to the same source scope',page.evaluate('ATLAS.publisher.scene().scope.sites.length===ATLAS.publisher.rows().length'))
   with page.expect_download() as transfer:page.locator('[data-publisher-export]').click()
   exported=json.loads(Path(transfer.value.path()).read_text())
   check(entry+' cited export preserves pins, raw groups, hash and non-additive denominator',exported['source_sha256']==publication['source_sha256'] and exported['publication_counts']==publication['counts'] and all(r['it_mw'] is None and r['coordinates']['basis']=='publisher_pin' for r in exported['records']) and 'not identity matches' in exported['boundary'])
   page.locator('[data-publisher-home]').click();page.locator('#publisher-query').fill('DUB1');page.wait_for_timeout(180)
   dub=page.evaluate('ATLAS.publisher.rows().find(r=>r.code==="DUB1").id');page.locator(f'[data-publisher-select="{dub}"]').click()
   check(entry+' Dublin source contradiction is visible, not silently repaired','Source locality/group conflict' in page.locator('#publisher-rail').inner_text() and 'United Kingdom' in page.locator('#publisher-rail').inner_text())
   check(entry+' selection has a direct official facility citation',page.locator('#publisher-rail a').first.get_attribute('href')==next(r['source_url'] for r in publication['records'] if r['id']==dub))
   check(entry+' publisher point never fabricates a 3D footprint',page.evaluate('!(ATLAS.publisher.scene() instanceof FacilityScene)') and page.locator('.publisher-map-stage').count()==1)
   page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(80)
   check(entry+' source contradiction fits a 390px mobile screen',overflow(page));page.screenshot(path=str(OUT/f'{Path(entry).stem}-publisher-dublin-mobile.png'),full_page=True)
   page.set_viewport_size({'width':320,'height':780});check(entry+' narrow publisher panel fits 320px',overflow(page))
   page.locator('[data-publisher-home]').click();page.locator('#publisher-country').select_option('Not specified')
   check(entry+' both missing country headings stay searchable as unknown',page.evaluate('ATLAS.publisher.rows().length===2&&ATLAS.publisher.rows().every(r=>r.source_country===null)'))
   page.locator('[data-publisher-home]').click();page.locator('#publisher-query').fill('HND10');page.wait_for_timeout(180)
   check(entry+' compound publisher code stays one record, not fabricated buildings',page.evaluate('ATLAS.publisher.rows().length===1&&ATLAS.publisher.flags(ATLAS.publisher.rows()[0]).some(x=>x.includes("Compound"))'))
   page.locator('[data-publisher-home]').click();page.locator('#publisher-review').select_option('notes')
   check(entry+' review-notes filter exposes only source anomalies or compound entries',page.evaluate('ATLAS.publisher.rows().length>0&&ATLAS.publisher.rows().every(r=>ATLAS.publisher.flags(r).length>0)'))
   page.locator('#publisher-query').fill('<img src=x onerror=alert(1)>');page.wait_for_timeout(180)
   check(entry+' unmatched text is a coverage gap and cannot inject markup','Missing coverage' in page.locator('#publisher-results').inner_text() and page.locator('#publisher-results img').count()==0)
   page.set_viewport_size({'width':1440,'height':1080});page.locator('[data-publisher-home]').click();page.locator('#publisher-country').select_option('Germany');page.wait_for_timeout(80)
   box=page.locator('#publisher-map').bounding_box()
   before=page.evaluate('(()=>{const s=ATLAS.publisher.scene();s.prepare();return {point:s.project(8.7,50.1),span:s.bounds[2]-s.bounds[0]};})()')
   page.mouse.move(box['x']+before['point']['x'],box['y']+before['point']['y']);page.mouse.wheel(0,-1);page.wait_for_timeout(60)
   after=page.evaluate('(()=>{const s=ATLAS.publisher.scene();s.prepare();return {point:s.project(8.7,50.1),span:s.bounds[2]-s.bounds[0]};})()')
   check(entry+' fine wheel input zooms continuously around the source-map cursor',after['span']<before['span'] and abs(after['point']['x']-before['point']['x'])<.05 and abs(after['point']['y']-before['point']['y'])<.05,{'before':before,'after':after})
   page.locator('#publisher-map').focus();span=after['span'];page.keyboard.press('+')
   check(entry+' keyboard plus provides an accessible map zoom alternative',page.evaluate('ATLAS.publisher.scene().bounds[2]-ATLAS.publisher.scene().bounds[0]')<span)
   page.evaluate('ATLAS.publisher.go({country:"All",region:"All",q:"",review:"All",selected:null})');page.evaluate('openSearch()');page.locator('#global-search').fill('FRA1');page.wait_for_timeout(180)
   check(entry+' global search includes independent publisher locations',page.locator('#search-results [data-publisher-select="digital-realty-2324"]').count()==1)
   page.locator('#search-results [data-publisher-select="digital-realty-2324"]').click()
   check(entry+' global selection clears stale source filters',page.evaluate('ATLAS.publisher.state.selected==="digital-realty-2324"&&ATLAS.publisher.state.country==="All"&&ATLAS.publisher.state.q===""'))
   check(entry+' nearby outlines are explicitly not certified matches','No ownership or identity match' in page.locator('#publisher-rail').inner_text() and page.locator('#publisher-rail [data-catalog-open="osm-way-168961561"]').count()==1)
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-publisher-frankfurt.png'),full_page=True)
   page.locator('#publisher-rail [data-catalog-open="osm-way-168961561"]').click();page.wait_for_timeout(80)
   check(entry+' nearby inspection opens an actual source-polygon 3D',page.evaluate('ATLAS.catalog.state.feature==="osm-way-168961561"&&ATLAS.catalog.scene().features[0].polygons.length>0'))
   canvas=page.locator('#globe-canvas');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
   page.mouse.move(box['x']+box['width']*.45,box['y']+box['height']*.46);page.mouse.down();page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.49,steps=3);page.mouse.up()
   check(entry+' facility orbit responds to actual pointer dragging',page.evaluate('Math.abs(ATLAS.catalog.scene().yaw+.65)>.1'))
   page.keyboard.down('Shift');page.mouse.down();page.mouse.move(box['x']+box['width']*.53,box['y']+box['height']*.51,steps=3);page.mouse.up();page.keyboard.up('Shift')
   check(entry+' shift drag pans the 3D scene',page.evaluate('ATLAS.catalog.scene().pan.x>5'))
   a=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {point:s.project3(3,7,5),zoom:s.zoom};})()')
   page.mouse.move(box['x']+a['point']['x'],box['y']+a['point']['y']);page.mouse.wheel(0,-100);page.wait_for_timeout(80)
   b=page.evaluate('(()=>{const s=ATLAS.catalog.scene();return {point:s.project3(3,7,5),zoom:s.zoom};})()')
   check(entry+' facility wheel keeps the cursor anchor fixed after orbit and pan',b['zoom']>a['zoom'] and abs(b['point']['x']-a['point']['x'])<1 and abs(b['point']['y']-a['point']['y'])<1,{'before':a,'after':b})
   page.mouse.wheel(0,-.5);page.wait_for_timeout(40)
   check(entry+' subpixel trackpad input is not discarded',page.evaluate('ATLAS.catalog.scene().zoom')>b['zoom'])
   ctrl=canvas.evaluate('e=>{const s=ATLAS.catalog.scene(),z=s.zoom,ev=new WheelEvent("wheel",{deltaY:-10,ctrlKey:true,bubbles:true,cancelable:true});e.dispatchEvent(ev);return s.zoom===z&&!ev.defaultPrevented;}')
   check(entry+' browser control-wheel accessibility zoom is not intercepted',ctrl)
   check(entry+' line and page wheel modes use their actual input units',canvas.evaluate('e=>{const s=ATLAS.catalog.scene(),b=e.getBoundingClientRect();let z=s.zoom;e.dispatchEvent(new WheelEvent("wheel",{deltaY:-1,deltaMode:1,clientX:b.x+s.w/2,clientY:b.y+s.h/2,cancelable:true}));let line=s.zoom/z;z=s.zoom;e.dispatchEvent(new WheelEvent("wheel",{deltaY:1,deltaMode:2,clientX:b.x+s.w/2,clientY:b.y+s.h/2,cancelable:true}));return Math.abs(line-Math.exp(.04))<1e-8&&s.zoom<z;}'))
   canvas.focus();page.keyboard.press('Home');check(entry+' keyboard Home resets 3D camera and pan',page.evaluate('ATLAS.catalog.scene().zoom===1&&ATLAS.catalog.scene().pan.x===0'))
   canvas.evaluate('e=>e.blur()');page.evaluate("document.querySelector('#toast')?.classList.remove('visible')");page.wait_for_timeout(120)
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-publisher-source-outline-3d.png'),full_page=True)
   # Same-document history is testable in embedded mode too: exercise the exact
   # child route, not only the direct button handler that bypassed legacy NAV.
   length=page.evaluate('history.length')
   page.go_back();page.wait_for_function('ATLAS.state.view==="publisher"',timeout=5000)
   check(entry+' back restores publisher selection after independent 3D inspection',page.evaluate('ATLAS.publisher.state.selected==="digital-realty-2324"'))
   page.go_forward();page.wait_for_function('ATLAS.state.view==="catalog"',timeout=5000)
   check(entry+' forward restores the independent source-outline facility',page.evaluate('ATLAS.catalog.state.feature==="osm-way-168961561"&&ATLAS.catalog.scene() instanceof FacilityScene'))
   page.go_back();page.wait_for_function('ATLAS.state.view==="publisher"',timeout=5000)
   check(entry+' history traversal does not append duplicate route entries',page.evaluate('history.length')==length)
   page.evaluate('ATLAS.navigate("publisher",{hash:true})')
   check(entry+' registered publisher navigation preserves source scope and history',page.evaluate('ATLAS.state.view==="publisher"&&ATLAS.publisher.state.selected==="digital-realty-2324"') and page.evaluate('history.length')==length)
   if not args.in_memory:
    page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check(entry+' publisher deep link survives real HTTP reload',page.evaluate('ATLAS.state.view==="publisher"&&ATLAS.publisher.state.selected==="digital-realty-2324"'))
   check(entry+' every source and archival record remains unchanged',page.evaluate('JSON.stringify([ATLAS.data,ATLAS.catalog.data,ATLAS.operators.data])')==original and page.evaluate('ATLAS.publisher.data')==publication)
   invalid=[]
   for key,value in [('schema_version',True),('review',None),('captured_at','2026-02-30T00:00:00Z')]:
    d=copy.deepcopy(publication);d[key]=value;invalid.append(d)
   d=copy.deepcopy(publication);d['records'][0]['coordinates']['lat']=True;invalid.append(d)
   d=copy.deepcopy(publication);d['records'][0]['it_mw']=0;invalid.append(d)
   d=copy.deepcopy(publication);d['records'][0]['geometry']={};invalid.append(d)
   check(entry+' malformed source projections cannot manufacture public geometry or power',page.evaluate('(items)=>items.every(d=>{try{DigitalRealtySchema.validate(d);return false;}catch(_){return true;}})',invalid))
   check(entry+' no unhandled JavaScript exceptions',not errors,errors);check(entry+' no third-party requests',not external,external);check(entry+' no unexpected HTTP failures',not http_errors,http_errors)
   page.close()
  if not args.in_memory:
   import uvicorn,socket
   from server.app import create_app
   with tempfile.TemporaryDirectory() as tmp:
    app=create_app(Path(tmp)/'service.sqlite3',background=False)
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    service=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'));thread=threading.Thread(target=service.run,daemon=True);thread.start()
    for _ in range(100):
     if service.started:break
     time.sleep(.05)
    origin=f'http://127.0.0.1:{port}/';page=browser.new_page(viewport={'width':1440,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(origin+'#publisher?region=Europe');page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check('SQL publisher boot uses the independently accepted Digital Realty source',page.evaluate('ATLAS.publisher.data')==app.state.directories['digital-realty'].publication() and not page.evaluate('!!window.ATLAS_DIGITAL_REALTY_WARNING'))
    pending={**publication,'review':None,'title':'Pending synthetic publisher fixture'};store=app.state.directories['digital-realty'];key=store.stage(pending)
    page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check('Pending publisher capture is not published on browser reload',page.evaluate('ATLAS.publisher.data.title')==publication['title'])
    store.accept(key,actor='QA reviewer',note='Synthetic source fixture only',expected_current=store.current())
    check('Acceptance never silently changes a currently open research view',page.evaluate('ATLAS.publisher.data.title')==publication['title'])
    page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check('Explicit reload applies reviewed publisher revision, preserving scope',page.evaluate('ATLAS.publisher.data.title')==pending['title'] and page.evaluate('ATLAS.publisher.state.region')=='Europe')
    check('Digital Realty acceptance leaves the Equinix source untouched',page.evaluate('ATLAS.operators.data')==app.state.directory.publication())
    unsafe=copy.deepcopy(publication);unsafe['records'][0]['it_mw']=999
    endpoint='**/api/operators/publication?publisher=digital-realty'
    page.route(endpoint,lambda route:route.fulfill(json=unsafe));page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check('Malformed publisher API response falls back visibly to the reviewed file',page.evaluate('!!window.ATLAS_DIGITAL_REALTY_WARNING') and page.evaluate('ATLAS.publisher.data')==publication and 'checked-in' in page.locator('#content').inner_text())
    page.unroute(endpoint);page.route(endpoint,lambda route:route.fulfill(status=503,body='unavailable'));page.reload();page.wait_for_function('document.documentElement.classList.contains("publisher-ready")')
    check('Publisher outage is explicit while both source collections remain usable',page.evaluate('!!window.ATLAS_DIGITAL_REALTY_WARNING&&ATLAS.operators.data.records.length===253&&ATLAS.publisher.data.records.length===261'))
    check('Service boundary tests produce no unhandled errors',not errors,errors)
    page.close();service.should_exit=True;thread.join(timeout=5);service=None
  browser.close()
finally:
 if server:server.shutdown()
 if service:service.should_exit=True
 result={'execution':'embedded Chromium only' if args.in_memory else 'real HTTP hosted, standalone and SQLite-backed Chromium','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
 (ROOT/'qa/publisher_explorer_results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if not checks or not all(c['pass'] for c in checks):raise SystemExit(1)
