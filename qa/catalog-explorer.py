"""Global catalog, source-outline 3D, continuous wheel, and HTTP/service contracts.
--in-memory covers only the embedded build; real HTTP is mandatory in Actions.
"""
from __future__ import annotations
import argparse, json, sys, tempfile, threading, time
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 checks.append({'test':name,'pass':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def overflow(page):return page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=None;service=None
if not args.in_memory:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/' if server else ''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for entry in (['compute_atlas.html'] if args.in_memory else ['index.html','compute_atlas.html']):
   page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True);page.set_default_timeout(10000);errors=[];external=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
   if args.in_memory:page.set_content((ROOT/entry).read_text(),wait_until='load')
   else:check(entry+' HTTP 200',page.goto(base+entry,wait_until='load').status==200)
   page.wait_for_function('document.documentElement.classList.contains("catalog-ready")');page.wait_for_timeout(150)
   check(entry+' broad catalog is the default landing',page.evaluate('ATLAS.state.view')=='catalog')
   check(entry+' catalog counts match captured source, not fabricated sites',page.evaluate('ATLAS.catalog.data.records.length===5265 && ATLAS.data.sites.length===79'))
   check(entry+' visible globe has real mapped clusters',page.evaluate('ATLAS.getGlobe().groups.length>30'))
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-catalog-world.png'))
   before=page.evaluate('ATLAS.getGlobe().zoom');box=page.locator('#globe-canvas').bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
   page.mouse.wheel(0,-1);page.wait_for_timeout(70);check(entry+' tiny trackpad wheel is continuous',page.evaluate('ATLAS.getGlobe().zoom')>before)
   page.evaluate('window.testCanvas=document.querySelector("#globe-canvas")');page.mouse.wheel(0,-120);page.wait_for_timeout(70)
   check(entry+' wheel preserves actual canvas instead of rebuilding route',page.evaluate('window.testCanvas===document.querySelector("#globe-canvas")'))
   before=page.evaluate('ATLAS.getGlobe().zoom');page.locator('#globe-canvas').dispatch_event('wheel',{'deltaY':-3,'deltaMode':1,'cancelable':True});check(entry+' line-mode wheel changes camera',page.evaluate('ATLAS.getGlobe().zoom')>before)
   for _ in range(6):page.mouse.wheel(0,-140);page.wait_for_timeout(30)
   check(entry+' wheel moves globe to regional map',page.evaluate('ATLAS.getGlobe().flat'))
   page.mouse.wheel(0,-200);page.wait_for_timeout(50)
   check(entry+' regional wheel retains canvas',page.evaluate('window.testCanvas===document.querySelector("#globe-canvas")'))
   # Screen point remains fixed under a Mercator wheel zoom.
   page.evaluate('window.anchor=ATLAS.getGlobe().projectNow(ATLAS.getGlobe().bounds[0]+(ATLAS.getGlobe().bounds[2]-ATLAS.getGlobe().bounds[0])*.6,(ATLAS.getGlobe().bounds[1]+ATLAS.getGlobe().bounds[3])/2);window.anchorGeo=[ATLAS.getGlobe().bounds[0]+(ATLAS.getGlobe().bounds[2]-ATLAS.getGlobe().bounds[0])*.6,(ATLAS.getGlobe().bounds[1]+ATLAS.getGlobe().bounds[3])/2]')
   anchor=page.evaluate('window.anchor');page.mouse.move(box['x']+anchor['x'],box['y']+anchor['y']);page.mouse.wheel(0,-80);page.wait_for_timeout(60)
   check(entry+' regional zoom is cursor anchored',page.evaluate('(()=>{let p=ATLAS.getGlobe().projectNow(...anchorGeo);return Math.hypot(p.x-anchor.x,p.y-anchor.y)<1})()'))
   page.locator('[data-catalog-region="Europe"]').first.click();check(entry+' Europe has 1908 mapped features',page.evaluate('ATLAS.catalog.filtered().length')==1908)
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-catalog-europe.png'))
   page.locator('#catalog-country').select_option('Germany');check(entry+' Germany query reaches all 320 features',page.evaluate('ATLAS.catalog.filtered().length')==320)
   page.locator('#catalog-query').fill('Equinix');page.wait_for_timeout(180);check(entry+' query retains focus and geographic scope',page.locator('#catalog-query').evaluate('el=>el===document.activeElement') and page.evaluate('ATLAS.catalog.filtered().every(r=>r.country==="Germany")'))
   page.locator('#catalog-query').fill('<img src=x onerror=alert(1)>');page.wait_for_timeout(200);check(entry+' query is inert and absent mapping is not zero capacity','coverage gap' in page.locator('#catalog-directory').inner_text() and page.locator('#catalog-directory img').count()==0)
   page.evaluate("ATLAS.catalog.select('osm-way-1121454055')");page.wait_for_timeout(150)
   check(entry+' facility has orbitable 3D using original polygon',page.evaluate('ATLAS.catalog.scene().record.geometry===ATLAS.catalog.feature("osm-way-1121454055").geometry && ATLAS.catalog.scene().features[0].polygons.length>0'))
   check(entry+' missing height is labeled as illustrative','Illustrative height: 12 m' in page.locator('#catalog-height-badge').inner_text())
   check(entry+' specifications retain apparent power rather than fake IT MW','9,600 kVA' in page.locator('#content').inner_text() and 'Not established' in page.locator('#content').inner_text())
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-facility-3d-pa9x.png'),full_page=True)
   box=page.locator('#globe-canvas').bounding_box();yaw=page.evaluate('ATLAS.catalog.scene().yaw');page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.55);page.mouse.down();page.mouse.move(box['x']+box['width']*.5+90,box['y']+box['height']*.55+35,steps=5);page.mouse.up()
   check(entry+' actual pointer drag orbits the 3D camera',abs(page.evaluate('ATLAS.catalog.scene().yaw')-yaw)>.2)
   z=page.evaluate('ATLAS.catalog.scene().zoom');page.mouse.wheel(0,-120);check(entry+' 3D wheel zoom is dynamic',page.evaluate('ATLAS.catalog.scene().zoom')>z)
   page.locator('#scene-height').fill('25');check(entry+' display height changes only the renderer',page.evaluate('ATLAS.catalog.scene().height(ATLAS.catalog.scene().features[0])===25 && ATLAS.catalog.feature("osm-way-1121454055").height_m===null'))
   page.locator('#scene-assumptions').uncheck();check(entry+' illustrative volume can be disabled',page.evaluate('ATLAS.catalog.scene().height(ATLAS.catalog.scene().features[0])===0'))
   page.locator('[data-catalog-tool="plan"]').click();check(entry+' plan view tilts camera overhead',page.evaluate('ATLAS.catalog.scene().pitch')>1.4)
   page.locator('#globe-canvas').focus();page.keyboard.press('Home');page.keyboard.press('ArrowRight');check(entry+' keyboard camera controls work',page.evaluate('ATLAS.catalog.scene().yaw>-.65'))
   with page.expect_download() as transfer:page.locator('[data-catalog-export]').click()
   exported=json.loads(Path(transfer.value.path()).read_text());check(entry+' exported record never invents height or IT MW',exported['feature']['height_m'] is None and exported['feature']['it_mw'] is None and exported['license']=='ODbL-1.0')
   page.locator('#catalog-note').fill('Verify operator and outline independently.');page.wait_for_timeout(100);check(entry+' facility note saves privately',page.evaluate('saved.notes["osm-way-1121454055"]')=='Verify operator and outline independently.')
   if not args.in_memory:
    page.reload(wait_until='networkidle');page.wait_for_function('document.documentElement.classList.contains("catalog-ready")');check(entry+' facility deep link and note survive reload',page.evaluate('ATLAS.catalog.state.feature')=='osm-way-1121454055' and 'Verify operator' in page.locator('#catalog-note').input_value())
   page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);check(entry+' facility mobile fits 390px',overflow(page));page.screenshot(path=str(OUT/f'{Path(entry).stem}-facility-3d-mobile.png'),full_page=True)
   page.set_viewport_size({'width':320,'height':780});check(entry+' facility mobile fits 320px',overflow(page))
   page.evaluate("ATLAS.catalog.select('osm-node-4753473931')");check(entry+' point-only record has no invented building',page.evaluate('ATLAS.catalog.scene().features[0].polygons.length===0 && ATLAS.catalog.scene().height(ATLAS.catalog.scene().features[0])===0'))
   page.evaluate('ATLAS.catalog.select(ATLAS.catalog.data.records.find(r=>r.kind==="campus"&&r.geometry).id)');check(entry+' campus land is never extruded as a building',page.evaluate('ATLAS.catalog.scene().height(ATLAS.catalog.scene().features[0])===0'))
   page.evaluate('ATLAS.catalog.select(ATLAS.catalog.data.records.find(r=>r.kind==="building"&&r.height_m).id)');check(entry+' mapped height is shown as an OSM tag','OSM height tag:' in page.locator('#catalog-height-badge').inner_text())
   page.set_viewport_size({'width':1440,'height':1080});page.evaluate("ATLAS.catalog.go({region:'Europe',country:'All',feature:null,q:'',kind:'All'})");page.locator('[data-catalog-page="1"]').click();check(entry+' directory paginates beyond the first 20',page.evaluate('ATLAS.catalog.state.page')==1 and page.locator('.catalog-result').count()==20)
   page.locator('.search-trigger').click();page.locator('#global-search').fill('PA9');page.wait_for_timeout(200);check(entry+' global search includes geographic records',page.locator('#search-results [data-catalog-open]').count()>0);page.locator('#search-results [data-catalog-open]').first.click();check(entry+' global search opens real 3D facility',page.evaluate('ATLAS.catalog.scene()!==null'))
   check(entry+' original 79 research records remain intact',page.evaluate('ATLAS.data.sites.length===79 && ATLAS.data.sites.find(s=>s.name==="Helios").target.it_mw===528'))
   check(entry+' no uncaught exceptions',not errors,errors);check(entry+' no unexpected third-party requests',not external,external);page.close()
  if not args.in_memory:
   # A separate real HTTP service boot must use the accepted SQL publication.
   import socket,uvicorn
   from server.app import create_app
   with tempfile.TemporaryDirectory() as temp:
    app=create_app(Path(temp)/'test.sqlite3',background=False);sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    service=uvicorn.Server(uvicorn.Config(app,log_level='error'));thread=threading.Thread(target=lambda:service.run(sockets=[sock]),daemon=True);thread.start()
    for _ in range(100):
     if service.started:break
     time.sleep(.05)
    page=browser.new_page(viewport={'width':1440,'height':1080});requested=[];page.on('request',lambda r:requested.append(r.url))
    page.goto(f'http://127.0.0.1:{port}/',wait_until='networkidle');page.wait_for_function('document.documentElement.classList.contains("catalog-ready")')
    check('service catalog boots from accepted SQL publication',any('/api/catalog/publication' in u for u in requested) and page.evaluate('ATLAS.catalog.data.records.length')==5265)
    page.route('**/api/catalog/publication',lambda route:route.fulfill(status=200,content_type='application/json',body='{"records":[]}'))
    page.reload(wait_until='networkidle');page.wait_for_function('document.documentElement.classList.contains("catalog-ready")')
    check('invalid service publication visibly falls back to the dated snapshot','Catalog service unavailable' in page.locator('#content').inner_text() and page.evaluate('ATLAS.catalog.data.records.length')==5265)
    page.close();service.should_exit=True;thread.join(5)
  browser.close()
finally:
 if server:server.shutdown()
 if service:service.should_exit=True
result={'execution':'embedded Chromium only' if args.in_memory else 'real HTTP Chromium: hosted, standalone, and SQLite service','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/catalog_explorer_results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if result['passed']!=result['total']:raise SystemExit(1)
