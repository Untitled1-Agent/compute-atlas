"""Debounced physical/geographic camera writes cannot steal a pending route."""
import json,os,shutil,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True);checks=[]
def check(name,ok):
 checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page,physical=True):
 page.wait_for_function('document.documentElement.classList.contains("layers-ready")&&globe&&!globe.dirty&&!globe.target')
 if physical:page.wait_for_function('globe instanceof CampusScene&&globe.imageReady')
 page.wait_for_timeout(300)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1080});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+entry+'#overview?scale=campus&site=amazon-anthropic-new-carlisle');ready(page)
   inventory=page.evaluate('JSON.stringify([D.sites,CATALOG.records,ATLAS_PRIMARY.observations])')
   prior=page.url;page.evaluate('globe.pan.y+=12;globe.dirty=true');ready(page)
   check(entry+' current physical camera publishes normally',page.url!=prior and page.evaluate('new URLSearchParams(location.hash.split("?")[1]).get("scenecamera")===campusCameraParam(globe.snapshot())'))
   requested='#overview?scale=facility&site=amazon-anthropic-new-carlisle&scene=new-carlisle-sr2-2025&requestedenergycollection=missing-capture&energy=1'
   # Hold the router while publishing the next intent. This is a deterministic
   # event-queue interval, rather than relying on a fast machine to hit a race.
   result=page.evaluate('''async requested=>{globe.pan.y+=12;globe.publishedCamera=null;globe.draw();history.pushState(null,'',requested);await new Promise(resolve=>setTimeout(resolve,350));return location.hash===requested;}''',requested)
   check(entry+' delayed physical camera cannot overwrite a requested source route',result)
   page.evaluate('routeFromHash()');ready(page)
   check(entry+' queued source route opens matching component and named recovery',page.evaluate('campusScene().id==="new-carlisle-sr2-2025"&&energyState.feature===null&&energyState.recovery?.collection==="missing-capture"') and page.locator('.energy-route-recovery').is_visible())
   page.reload();ready(page)
   check(entry+' preserved recovery remains bound after canonical rewrite and reload',page.evaluate('campusScene().id==="new-carlisle-sr2-2025"&&energyState.recovery?.collection==="missing-capture"'))
   page.locator('[data-energy-recover]').click();ready(page)
   check(entry+' explicit recovery clears only its requested source state',page.evaluate('energyState.recovery===null&&energyState.feature===null&&campusScene().id==="new-carlisle-sr2-2025"'))
   page.goto(base+entry+'#overview?scale=metro&site=amazon-anthropic-new-carlisle');ready(page,False)
   prior=page.url;page.evaluate('globe.zoom*=1.1;globe.dirty=true;document.dispatchEvent(new CustomEvent("atlas-camera-change",{detail:globe}))');ready(page,False)
   check(entry+' current geographic camera publishes normally',page.url!=prior and page.evaluate('new URLSearchParams(location.hash.split("?")[1]).get("camera")===workspaceCameraParam(globe.snapshot())'))
   requested='#overview?scale=facility&site=coreweave-helios&selection=feature&feature=helios-naip2022-roof-01'
   result=page.evaluate('''async requested=>{globe.zoom*=1.1;document.dispatchEvent(new CustomEvent('atlas-camera-change',{detail:globe}));history.pushState(null,'',requested);await new Promise(resolve=>setTimeout(resolve,350));return location.hash===requested;}''',requested)
   check(entry+' delayed geographic camera cannot overwrite a physical destination',result)
   page.evaluate('routeFromHash()');ready(page)
   check(entry+' queued geographic-to-physical route opens the exact roof',page.evaluate('campusScene().id==="helios-naip-20220905"&&campusState.feature==="helios-naip2022-roof-01"') and page.locator('.campus-feature-inspector').is_visible())
   page.screenshot(path=str(OUT/(entry+'-camera-route-helios.png')))
   destination=page.url;page.go_back();ready(page,False)
   check(entry+' Back restores geographic identity after the protected destination',page.evaluate('globe instanceof ResearchMap&&state.spatialSelected==="amazon-anthropic-new-carlisle"'))
   page.go_forward();ready(page)
   check(entry+' Forward restores the exact protected physical URL',page.url==destination and page.evaluate('campusState.feature==="helios-naip2022-roof-01"'))
   check(entry+' route ownership preserves source and capacity records',page.evaluate('JSON.stringify([D.sites,CATALOG.records,ATLAS_PRIMARY.observations])')==inventory)
   check(entry+' route ownership has no uncaught errors',not errors)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown()
result={'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)};(ROOT/'qa/camera_routes_results.json').write_text(json.dumps(result,indent=2)+'\n');print(str(result['passed'])+'/'+str(result['total'])+' passed',flush=True);raise SystemExit(0 if result['passed']==result['total'] else 1)
