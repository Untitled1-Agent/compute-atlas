"""Primary directory UI, provisional matching and accepted SQL publication over HTTP.
--in-memory exercises only the embedded document, never claims HTTP coverage.
"""
from __future__ import annotations
import argparse,json,sys,tempfile,threading,time
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.operator_directory import proposed_matches
parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 checks.append({'test':name,'pass':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def overflow(p):return p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=None;service=None;thread=None
if not args.in_memory:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/' if server else ''
publication=json.loads((ROOT/'data/catalog/operator-directory.json').read_text());features=json.loads((ROOT/'data/catalog/osm.json').read_text())['records']
expected={r['id']:proposed_matches(r,features) for r in publication['records']}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for entry in (['compute_atlas.html'] if args.in_memory else ['index.html','compute_atlas.html']):
   page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True);page.set_default_timeout(10000);errors=[];external=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
   if args.in_memory:page.set_content((ROOT/entry).read_text(),wait_until='load')
   else:check(entry+' HTTP response',page.goto(base+entry).status==200)
   page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
   page.locator('.catalog-mode-switch [data-id="operators"]').click()
   check(entry+' primary directory is reachable from the map',page.evaluate('ATLAS.state.view')=='operators')
   check(entry+' captured primary denominator remains 253 / 33',page.evaluate('ATLAS.operators.data.records.length===253 && Object.keys(ATLAS.operators.data.counts.countries).length===33'))
   check(entry+' directory fields do not manufacture coordinates or power',page.evaluate('ATLAS.operators.data.records.every(r=>r.coordinates===null&&r.it_mw===null)'))
   actual=page.evaluate('Object.fromEntries(ATLAS.operators.data.records.map(r=>[r.id,ATLAS.operators.matches(r.id)]))')
   check(entry+' all 253 proposed links match the backend algorithm',actual==expected)
   page.locator('[data-operator-region="EMEA"]').click()
   check(entry+' EMEA source scope reaches all 93 codes',page.evaluate('ATLAS.operators.rows().length')==93)
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-operator-emea.png'),full_page=True)
   page.locator('#operator-country').select_option('Germany')
   check(entry+' country selection clears incompatible regional filter',page.evaluate('ATLAS.operators.state.region==="All" && ATLAS.operators.rows().length===13'))
   page.locator('[data-operator-page="1"]').click()
   check(entry+' pagination reaches the thirteenth German entry',page.locator('.operator-record').count()==1 and page.evaluate('ATLAS.operators.state.page')==1)
   page.locator('#operator-query').fill('FR2');page.wait_for_timeout(160)
   check(entry+' live query resets pagination without losing focus',page.evaluate('ATLAS.operators.state.page')==0 and page.locator('#operator-query').evaluate('e=>e===document.activeElement'))
   page.locator('[data-operator-select="equinix-fr2"]').click()
   check(entry+' FR2 does not match the separate FR2.6 feature',page.evaluate('ATLAS.operators.matches("equinix-fr2").includes("osm-way-380134092") && !ATLAS.operators.matches("equinix-fr2").includes("osm-way-619486957")'))
   check(entry+' provisional geometry and undisclosed power are explicit','not certify' in page.locator('#operator-rail').inner_text() and 'Not disclosed here' in page.locator('#operator-rail').inner_text())
   with page.expect_download() as transfer:page.locator('[data-operator-export]').click()
   exported=json.loads(Path(transfer.value.path()).read_text())
   check(entry+' cited export retains source hashes, nulls and proposal boundary',exported['records'][0]['it_mw'] is None and exported['records'][0]['source_url']==publication['url'] and exported['source_sha256']==publication['source_sha256'] and exported['proposed_map_matches'][0]['osm_feature_ids']==expected['equinix-fr2'])
   page.evaluate("ATLAS.operators.go({q:'',country:'Germany',selected:'equinix-du1'})")
   check(entry+' missing service coverage stays not stated, not zero','Not stated' in page.locator('#operator-rail').inner_text())
   page.evaluate("ATLAS.operators.go({q:'',country:'France',selected:'equinix-pa7'})")
   check(entry+' overlapping map proposals are retained, never collapsed',page.locator('.operator-map-link').count()==2)
   page.evaluate("ATLAS.operators.go({q:'',country:'France',selected:'equinix-pa9x'})")
   check(entry+' source service restriction is not turned into operating status','Smart Hands not available' in page.locator('#operator-rail').inner_text())
   page.locator('.operator-map-link').click();page.wait_for_timeout(100)
   check(entry+' a proposed link opens its actual source-outline 3D',page.evaluate('ATLAS.catalog.state.feature==="osm-way-1121454055" && ATLAS.catalog.scene().features[0].polygons.length>0'))
   box=page.locator('#globe-canvas').bounding_box();z=page.evaluate('ATLAS.catalog.scene().zoom');page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.5);page.mouse.wheel(0,-1)
   check(entry+' wheel remains continuous after directory-to-3D navigation',page.evaluate('ATLAS.catalog.scene().zoom')>z)
   page.screenshot(path=str(OUT/f'{Path(entry).stem}-operator-to-3d.png'),full_page=True)
   if not args.in_memory:
    page.go_back();page.wait_for_function('ATLAS.state.view==="operators"')
    check(entry+' back restores selected operator and country',page.evaluate('ATLAS.operators.state.country==="France" && ATLAS.operators.state.selected==="equinix-pa9x"'))
    page.reload();page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check(entry+' directory deep link survives reload',page.evaluate('ATLAS.state.view==="operators" && ATLAS.operators.state.selected==="equinix-pa9x"'))
   else:page.evaluate("ATLAS.operators.go({country:'France',selected:'equinix-pa9x'})")
   page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);check(entry+' mobile 390px has no horizontal overflow',overflow(page));page.screenshot(path=str(OUT/f'{Path(entry).stem}-operator-mobile.png'),full_page=True)
   page.set_viewport_size({'width':320,'height':780});check(entry+' narrow mobile 320px remains readable',overflow(page))
   page.locator('#operator-match').select_option('unlinked');page.wait_for_timeout(100)
   check(entry+' unmatched records remain searchable with no manufactured pin',page.evaluate('ATLAS.operators.rows().length>0 && ATLAS.operators.rows().every(r=>ATLAS.operators.matches(r.id).length===0)'))
   page.locator('#operator-query').fill('<img src=x onerror=alert(1)>');page.wait_for_timeout(160)
   check(entry+' empty search is a coverage gap and query cannot inject HTML','coverage gap' in page.locator('#operator-results').inner_text() and page.locator('#operator-results img').count()==0)
   page.set_viewport_size({'width':1440,'height':1080});page.evaluate("ATLAS.navigate('catalog');openSearch()")
   page.locator('#global-search').fill('FR2');page.wait_for_timeout(200)
   check(entry+' global search includes primary operator listings',page.locator('#search-results [data-operator-select="equinix-fr2"]').count()==1)
   page.locator('#search-results [data-operator-select="equinix-fr2"]').click()
   check(entry+' global result clears old incompatible filters',page.evaluate('ATLAS.operators.state.country==="All" && ATLAS.operators.state.q==="" && ATLAS.operators.state.selected==="equinix-fr2"'))
   check(entry+' original research and geographic catalog remain intact',page.evaluate('ATLAS.data.sites.length===79 && ATLAS.catalog.data.records.length===5265 && ATLAS.catalog.data.counts.continents.Europe===1908'))
   check(entry+' no uncaught JavaScript exceptions',not errors,errors);check(entry+' no third-party browser requests',not external,external)
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
    page.goto(origin+'#operators?country=Germany');page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check('SQL directory boot has no fallback warning',not page.evaluate('!!window.ATLAS_DIRECTORY_WARNING'))
    check('SQL-backed directory matches accepted snapshot',page.evaluate('ATLAS.operators.data')==app.state.directory.publication())
    pending={**publication,'review':None,'title':'Pending synthetic test title'}
    key=app.state.directory.stage(pending)
    page.reload();page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check('Pending directory cannot leak into browser publication',page.evaluate('ATLAS.operators.data.title')==publication['title'])
    app.state.directory.accept(key,actor='QA reviewer',note='Synthetic service fixture only',expected_current=app.state.directory.current())
    check('Acceptance does not silently mutate an open view',page.evaluate('ATLAS.operators.data.title')==publication['title'])
    page.reload();page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check('Reload reads accepted revision with actual editorial decision',page.evaluate('ATLAS.operators.data.title')=='Pending synthetic test title' and page.evaluate('ATLAS.operators.data.review.actor')=='QA reviewer')
    unsafe={**publication,'records':[dict(r) for r in publication['records']]};unsafe['records'][0]['it_mw']=999
    page.route('**/api/operators/publication',lambda route:route.fulfill(json=unsafe))
    page.reload();page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check('Malformed service data falls back visibly without corrupting known facts',page.evaluate('!!window.ATLAS_DIRECTORY_WARNING') and page.evaluate('ATLAS.operators.data.records[0].it_mw') is None and 'checked-in snapshot' in page.locator('#content').inner_text())
    page.unroute('**/api/operators/publication');page.route('**/api/operators/publication',lambda route:route.fulfill(status=503,body='unavailable'))
    page.reload();page.wait_for_function('document.documentElement.classList.contains("operator-ready")')
    check('Publication outage is explicit, not a fabricated live status',page.evaluate('!!window.ATLAS_DIRECTORY_WARNING') and page.evaluate('ATLAS.operators.data.title')==publication['title'])
    check('Service boundary cases cause no unhandled browser errors',not errors,errors)
    page.close();service.should_exit=True;thread.join(timeout=5);service=None
  browser.close()
finally:
 if server:server.shutdown()
 if service:service.should_exit=True
 result={'execution':'embedded Chromium only' if args.in_memory else 'real HTTP hosted, offline and SQLite-backed Chromium','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
 (ROOT/'qa/operator_directory_results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if not checks or not all(c['pass'] for c in checks):raise SystemExit(1)
