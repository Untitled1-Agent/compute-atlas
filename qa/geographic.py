"""Close-range native geometry, road provenance and mixed-release recovery."""
import json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):
 checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):
 page.wait_for_function('document.documentElement.classList.contains("layers-ready")');page.wait_for_function('globe&&!globe.dirty&&!globe.target')
def capture(page,entry,name):
 page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-geographic-'+name+'.png')),full_page=True)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1080});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios&energy=1');ready(page);page.wait_for_function('globe.imageReady')
   inventory=page.evaluate('[D.sites.length,CATALOG.records.length]')
   check(entry+' local roads supplement the independently dated aerial',page.evaluate('globe.localRoadPaths.length>0') and '2026-10-11' in page.locator('.road-legend').inner_text() and '2022-09-05' in page.locator('.campus-historic-badge').inner_text())
   capture(page,entry,'aerial')
   page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="locations"]').uncheck();page.locator('[data-map-layer="energy"]').uncheck();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' roads retain OSM attribution with locations and electricity disabled',page.locator('.map-layer-attribution a').is_visible() and page.evaluate('!ATLAS.layers.on("energy")&&!ATLAS.layers.on("locations")&&globe.localRoadPaths.length>0'))
   page.locator('[data-layer-open]').first.click();page.locator('[data-road-source]').click()
   check(entry+' road source distinguishes access geometry and vintage','public access' in page.locator('#drawer-content').inner_text() and '2022 aerial' in page.locator('#drawer-content').inner_text())
   check(entry+' source timestamp is readable UTC','11 Oct 2026, 17:04 UTC' in page.locator('#drawer-content').inner_text() and 'T17:04:49.964903' not in page.locator('#drawer-content').inner_text())
   page.locator('.map-layer-feature-list>summary').click();page.locator('.map-layer-feature-list details').filter(has=page.locator('summary',has_text='County Road 112')).locator('summary').click()
   check(entry+' native road inspection exposes original object and history',page.locator('a[href="https://www.openstreetmap.org/way/20841402/history"]').is_visible())
   with page.expect_download() as event:page.locator('[data-road-export]').click()
   exported=json.loads(Path(event.value.path()).read_text())
   check(entry+' road export preserves complete native ways and private access',len(exported['features'])==36 and exported['license']=='ODbL-1.0' and any(f['tags'].get('access')=='private' for f in exported['features']) and all('geometry' in f and 'node_refs' in f and 'it_mw' not in f and 'project_id' not in f for f in exported['features']))
   for width in [390,320]:
    page.set_viewport_size({'width':width,'height':844});page.locator('#drawer').evaluate('e=>e.scrollTop=0');capture(page,entry,'road-source-phone-'+str(width))
    check(entry+f' phone {width} road source fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');page.set_viewport_size({'width':1440,'height':1080})
   page.locator('[data-layer-open]').first.click();page.locator('[data-road-coverage]').click();ready(page)
   check(entry+' explicit road coverage does not enable electricity',page.evaluate('state.spatialLevel===3&&globe.localRoadPaths.length>0&&!ATLAS.layers.on("energy")'))
   check(entry+' native road labels are source named and deduplicated',page.evaluate('globe.roadLabels.length>0&&new Set(globe.roadLabels.map(r=>r.name)).size===globe.roadLabels.length&&globe.roadLabels.every(r=>ROAD_CONTEXT.features.some(f=>[f.tags.name,f.tags.ref].includes(r.name)))'))
   capture(page,entry,'local-roads')
   camera=page.evaluate('globe.snapshot()');route=page.url
   page.locator('[data-layer-open]').first.click();page.locator('[data-road-source]').click();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
   check(entry+' road source return retains camera and route',page.url==route and page.evaluate('globe.snapshot()')==camera)
   page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="roads"]').uncheck();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' disabling roads clears local paths and sole OSM attribution',page.evaluate('globe.localRoadPaths.length===0') and not page.locator('.map-layer-attribution a').count())
   page.reload();ready(page)
   check(entry+' road preference survives shared reload',page.evaluate('!ATLAS.layers.on("roads")&&globe.localRoadPaths.length===0'))
   page.goto(base+entry+'#overview?scale=metro&site=coreweave-helios&energy=1')
   page.wait_for_function('globe instanceof ResearchMap&&state.spatialLevel===3&&state.spatialEnergy===true&&state.spatialRoads!==false');ready(page)
   crossing=page.evaluate('''(()=>{const f=ROAD_CONTEXT.features.find(f=>f.id==='osm-way-20841402'),path=f.display_paths[0],a=path[0],b=path[1],x=(a[0]+b[0])/2,y=(a[1]+b[1])/2;globe.bounds=[x-.00001,y-.00001,x+.00001,y+.00001];globe.target=null;globe.prepare();globe.dirty=true;return f.id})()''');ready(page)
   check(entry+' native road remains visible with every vertex offscreen',page.evaluate('(id)=>globe.localRoadPaths.some(r=>r.feature.id===id&&!r.pts.some(p=>p.x>=0&&p.x<=globe.w&&p.y>=0&&p.y<=globe.h))',crossing))
   check(entry+' reference path painter retains a real crossing segment',page.evaluate('''(()=>{const line=ROAD_CONTEXT.features.find(f=>f.id==='osm-way-20841402').display_paths[0],original=globe.ctx.lineTo;let calls=0;globe.ctx.lineTo=function(...args){calls++;return original.apply(this,args)};try{globe.path(line,'#fff',1)}finally{globe.ctx.lineTo=original;globe.dirty=true}return calls>0})()'''))
   page.evaluate('''(()=>{const f=POWER_CONTEXT.features.find(f=>f.id==='osm-way-1490401533'),a=f.display_paths[0][0],b=f.display_paths[0][1],x=(a[0]+b[0])/2,y=(a[1]+b[1])/2;globe.bounds=[x-.000002,y-.000002,x+.000002,y+.000002];globe.prepare();globe.dirty=true})()''');ready(page)
   check(entry+' native power line remains inspectable with offscreen endpoints',page.evaluate('''(()=>{const row=globe.energyPaths.find(r=>r.feature.id==='osm-way-1490401533');return row&&!row.pts.some(p=>p.x>=0&&p.x<=globe.w&&p.y>=0&&p.y<=globe.h)&&energyHit(globe,globe.cx,globe.cy)?.id===row.feature.id})()'''))
   page.evaluate('globe.bounds=[-100.872155,33.775715,-100.872145,33.775725];globe.prepare();globe.dirty=true');ready(page)
   check(entry+' enclosing native area stays filled and inspectable',page.evaluate('''(()=>{const row=globe.energyPaths.find(r=>r.feature.id==='osm-way-1130569621');return row?.closed&&!row.pts.some(p=>p.x>=0&&p.x<=globe.w&&p.y>=0&&p.y<=globe.h)&&energyHit(globe,globe.cx,globe.cy)?.id===row.feature.id})()'''))
   page.evaluate('globe.bounds=[-100.89,33.7501,-100.889,33.7511];globe.prepare();globe.dirty=true');ready(page)
   check(entry+' empty mapped viewport differs from outside capture','Inside capture' in page.locator('.map-layer-coverage-state').inner_text())
   page.goto(base+entry+'#overview?scale=region&site=amazon-anthropic-new-carlisle&camera=m,170,-5,190,5,1');ready(page)
   check(entry+' Mercator uses nearby longitudes across the dateline',page.evaluate('Math.abs(globe.project(-179,0).x-globe.project(179,0).x)<globe.w*.2'))
   page.goto(base+entry+'#overview?scale=metro&site=amazon-anthropic-new-carlisle');ready(page);capture(page,entry,'chicago-new-carlisle')
   for width,height in [(1366,768),(768,1080),(390,844),(320,844)]:
    page.set_viewport_size({'width':width,'height':height});ready(page);capture(page,entry,'metro-'+str(width))
    check(entry+f' metro {width} preserves map controls and fits',page.locator('[data-layer-open]').first.is_visible() and page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   check(entry+' geography does not change project or catalog inventory',page.evaluate('[D.sites.length,CATALOG.records.length]')==inventory)
   if errors:print('GEOGRAPHIC ERRORS',json.dumps(errors),flush=True)
   check(entry+' no uncaught geographic errors',not errors)
   ctx.close()
  # Native browser integrity: valid-but-changed assets must fail before mixing.
  for asset,body,mime in [('data/layers/helios-roads.json','{}','application/json'),('src/map-layers.js','window.mixedReleaseExecuted=true','text/javascript'),('src/experience.css','body{background:red}','text/css')]:
   ctx=browser.new_context(viewport={'width':390,'height':844});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));pattern='**/'+asset+'*'
   page.route(pattern,lambda route:route.fulfill(status=200,body=body,content_type=mime));page.goto(base+'index.html');page.locator('#atlas-boot-failure').wait_for()
   check(asset+' mismatched asset provides accessible recovery',page.locator('#atlas-boot-reload').is_visible() and page.evaluate('document.querySelector(".app-shell").inert&&document.activeElement.id==="atlas-boot-reload"&&!window.mixedReleaseExecuted'))
   page.unroute(pattern);page.locator('#atlas-boot-reload').click();ready(page)
   check(asset+' explicit reload opens matching complete release',not page.locator('#atlas-boot-failure').count() and not errors)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown()
result={'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)}
(ROOT/'qa/geographic_results.json').write_text(json.dumps(result,indent=2));print(f"{result['passed']}/{result['total']} passed",flush=True)
if result['passed']!=result['total']:raise SystemExit(1)
