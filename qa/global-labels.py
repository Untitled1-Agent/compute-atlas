"""Broad-scale label contrast, physical placement, identity and accessible markers."""
import json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):
 page.wait_for_function('document.documentElement.classList.contains("layers-ready")&&globe&&!globe.dirty&&!globe.target&&Math.abs(globe.canvas.getBoundingClientRect().width-globe.canvas.parentElement.clientWidth)<1&&Math.abs(globe.canvas.getBoundingClientRect().height-globe.canvas.parentElement.clientHeight)<1')
 page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');page.wait_for_function('!globe.dirty&&!globe.target')
try:
 with sync_playwright() as d:
  browser=d.chromium.launch(executable_path=shutil.which('chromium') or d.chromium.executable_path,args=['--no-sandbox'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1080});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+entry+'#overview');ready(page)
   inventory=page.evaluate('JSON.stringify([D.sites.map(s=>[s.id,s.lon,s.lat]),CATALOG.records.map(r=>r.id),ATLAS_PRIMARY.observations])')
   for width,height in [(1440,1080),(1366,768),(1024,1080),(768,1080),(390,844),(320,844)]:
    page.set_viewport_size({'width':width,'height':height});ready(page)
    checks_here=page.evaluate('''(()=>{const boxes=globe.markerLabels,limit=innerWidth<=500?2:innerWidth<=1050?3:5;const overlap=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;return {budget:boxes.length>0&&boxes.length<=limit,placement:boxes.every((b,i)=>b.x>=0&&b.y>=0&&b.x+b.w<=globe.w&&b.y+b.h<=globe.h&&!boxes.slice(i+1).some(a=>overlap(a,b))&&!globe.labelExclusions.some(a=>overlap(a,b))),identity:boxes.every(b=>globe.groups.some(g=>g.sites.some(s=>s.id===b.project_id)))};})()''')
    check(entry+f'{width}px broad labels are selective and retain native identities',all(checks_here.values()) and page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.screenshot(path=str(OUT/(entry+'-global-labels-'+str(width)+'.png')))
   page.set_viewport_size({'width':1440,'height':1080});ready(page)
   before=page.evaluate('JSON.stringify(globe.groups.map(g=>[g.sites.map(s=>s.id),g.mw,g.known]))')
   page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="labels"]').uncheck();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' disabling labels preserves every group and estimate',page.evaluate('globe.markerLabels.length===0') and page.evaluate('JSON.stringify(globe.groups.map(g=>[g.sites.map(s=>s.id),g.mw,g.known]))')==before)
   page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="labels"]').check();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' unquantified records retain a representative label',page.evaluate('globe.groups.some(g=>g.mw==null)&&globe.markerLabels.some(b=>b.native)'))
   page.evaluate('ATLAS.spatial.select("coreweave-helios")');ready(page)
   check(entry+' selected group has first label priority',page.evaluate('state.spatialSelected==="coreweave-helios"&&globe.markerLabels[0]?.project_id==="coreweave-helios"'))
   native=page.evaluate('globe.groups.find(g=>g.mw==null)?.sites[0].id');page.evaluate('(id)=>ATLAS.spatial.select(id)',native);ready(page)
   check(entry+' selected unquantified group does not erase comparable context',page.evaluate('globe.markerLabels[0]?.native&&globe.markerLabels.some(b=>!b.native)'))
   page.locator('.atlas-scale-step[data-id="1"]').click();ready(page)
   check(entry+' continent uses source-backed plates with retained markers',page.evaluate('state.spatialLevel===1&&globe.markerLabels.length>0&&globe.groups.length>=globe.markerLabels.length&&globe.markerLabels.every(b=>b.h===38)'))
   page.screenshot(path=str(OUT/(entry+'-global-labels-continent.png')))
   check(entry+' labels do not mutate data or capacity claims',page.evaluate('JSON.stringify([D.sites.map(s=>[s.id,s.lon,s.lat]),CATALOG.records.map(r=>r.id),ATLAS_PRIMARY.observations])')==inventory)
   check(entry+' broad-scale label journeys have no uncaught errors',not errors)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown()
result={'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)};(ROOT/'qa/global_labels_results.json').write_text(json.dumps(result,indent=2)+'\n');print(str(result['passed'])+'/'+str(result['total'])+' passed',flush=True);raise SystemExit(0 if result['passed']==result['total'] else 1)
