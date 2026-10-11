"""Independent native-source context, shared layer state and retained camera."""
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
 page.wait_for_function('window.ATLAS_BOOTSTRAPPING===false&&document.documentElement.classList.contains("layers-ready")')
 page.wait_for_function('!globe||(!globe.dirty&&!globe.target)');page.wait_for_timeout(300)
def capture(page,entry,name):
 page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-layers-'+name+'.png')),full_page=True)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1080});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+entry);ready(page)
   check(entry+' independent electricity starts disabled',not page.evaluate('ATLAS.layers.on("energy")'))
   check(entry+' community context has visible attribution',page.locator('.map-layer-attribution a').is_visible())
   inventory=page.evaluate('[D.sites.length,CATALOG.records.length]')
   page.locator('[data-layer-open]').first.click();capture(page,entry,'panel-desktop')
   check(entry+' layer panel explains dates coverage and missing fiber','bounded coverage' in page.locator('#drawer-content').inner_text() and 'No licensed route snapshot' in page.locator('#drawer-content').inner_text())
   page.evaluate('window.layerCanvas=globe.canvas;window.layerCamera=workspaceCurrentCamera()')
   for name in ['research','locations','labels','roads','boundaries']:
    page.locator(f'[data-map-layer="{name}"]').uncheck()
   check(entry+' toggles retain canvas and camera',page.evaluate('globe.canvas===window.layerCanvas&&JSON.stringify(workspaceCurrentCamera())===JSON.stringify(window.layerCamera)'))
   page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' no hidden research hit targets remain',page.evaluate('globe.groups.length===0') and not page.locator('.atlas-map-marker:visible').count())
   check(entry+' closing layers restores toolbar focus',page.locator('[data-layer-open]').first.evaluate('e=>e===document.activeElement'))
   route=page.url;page.reload();ready(page)
   check(entry+' all independent disabled layers survive reload',page.evaluate('["research","locations","labels","roads","boundaries"].every(x=>!ATLAS.layers.on(x))'))
   page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios&energy=1');ready(page);page.wait_for_function('globe.imageReady')
   check(entry+' shared electricity loads without replacing historical image date','2022-09-05' in page.locator('.campus-historic-badge').inner_text() and '2026-10-11' in page.locator('.energy-legend').inner_text())
   # A native interior coordinate west of the busbars; the polygon centroid
   # lands on a separately mapped line, which correctly takes click priority.
   point=page.evaluate('globe.project3(...globe.local(-100.87215,33.77572))')
   page.evaluate('window.layerCanvas=globe.canvas;window.layerCamera=globe.snapshot()');box=page.locator('#globe-canvas').bounding_box();page.mouse.click(box['x']+point['x'],box['y']+point['y']);ready(page)
   check(entry+' actual source area click inspects the native feature',page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"') and page.locator('.energy-feature-inspector').is_visible())
   check(entry+' geometry selection retains canvas camera and campus scale',page.evaluate('globe.canvas===window.layerCanvas&&JSON.stringify(globe.snapshot())===JSON.stringify(window.layerCamera)&&state.spatialLevel===4'))
   check(entry+' native voltage remains distinct from IT capacity','345 kV' in page.locator('.energy-feature-inspector').inner_text() and 'not IT power' in page.locator('.energy-feature-inspector').inner_text())
   page.go_back();ready(page)
   check(entry+' Back restores the prior independent selection',page.evaluate('ATLAS.layers.state.feature===null&&ATLAS.layers.on("energy")'))
   page.go_forward();ready(page)
   check(entry+' Forward restores the native source feature',page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"'))
   capture(page,entry,'aerial-electricity')
   selected_route=page.url;page.locator('.energy-feature-inspector [data-energy-source]').click()
   check(entry+' native source retains object history and mixed vintage','way/1130569621' in page.locator('#drawer-content').inner_text() and '2022 aerial' in page.locator('#drawer-content').inner_text())
   with page.expect_download() as event:page.locator('#drawer-content [data-energy-export]').click()
   exported=json.loads(Path(event.value.path()).read_text())
   check(entry+' independent source export preserves complete geometry tags and license',len(exported['features'])==38 and exported['license']=='ODbL-1.0' and all('node_refs' in f and 'geometry' in f and 'display_paths' in f and 'tags' in f and 'project_id' not in f and 'it_mw' not in f for f in exported['features']))
   page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
   check(entry+' source return retains exact feature route',page.url==selected_route)
   page.locator('[data-workspace-topic="technical"]').click();ready(page)
   check(entry+' topic retains electricity source selection and camera',page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"&&JSON.stringify(globe.snapshot())===JSON.stringify(window.layerCamera)'))
   page.reload();ready(page);page.wait_for_function('globe.imageReady')
   check(entry+' context feature survives share and reload',page.locator('.energy-feature-inspector').is_visible() and page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"'))
   point=page.evaluate('globe.project3(...globe.local(-100.8717331,33.7745141))');box=page.locator('#globe-canvas').bounding_box()
   page.mouse.click(box['x']+point['x'],box['y']+point['y']);ready(page)
   check(entry+' actual native line click takes priority inside the area',page.evaluate('ATLAS.layers.state.feature==="osm-way-1490401533"'))
   check(entry+' native line inspector identifies its own source',page.locator('.energy-feature-inspector').is_visible() and '1490401533' in page.locator('.energy-feature-inspector').inner_text())
   page.go_back();ready(page)
   check(entry+' Back returns from native line to independent area',page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"'))
   page.locator('[data-campus-feature]').click();ready(page)
   check(entry+' historical roof is an independent selection',page.evaluate('ATLAS.layers.state.feature===null&&ATLAS.campus.state.feature==="helios-naip2022-roof-01"') and page.locator('.campus-feature-inspector').is_visible())
   page.locator('[data-layer-open]').first.click();page.locator('.map-layer-feature-list summary').click();page.locator('[data-energy-feature="osm-way-1130569621"]').focus();page.keyboard.press('Enter');ready(page)
   check(entry+' accessible source list matches geometry selection',page.evaluate('ATLAS.layers.state.feature==="osm-way-1130569621"'))
   for width in [390,320]:
    page.set_viewport_size({'width':width,'height':844});ready(page);capture(page,entry,'phone-'+str(width))
    page.locator('.campus-spatial-hero').screenshot(path=str(OUT/(entry+'-layers-phone-map-'+str(width)+'.png')))
    check(entry+f' phone {width} context inspector expands with source identity',page.locator('.energy-feature-inspector').is_visible() and 'CONTEXT FEATURE' in page.locator('[data-workspace-inspector]').inner_text())
    check(entry+f' phone {width} controls and source have no overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('[data-layer-open]').first.is_visible())
    check(entry+f' phone {width} toolbar clears image date and view controls',page.evaluate('(()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return r(".workspace-toolbar").bottom<=r(".campus-historic-badge").top&&r(".campus-scene-head").bottom<=r(".workspace-toolbar").top})()'))
    page.locator('[data-layer-open]').first.click();capture(page,entry,'panel-phone-'+str(width));page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
    check(entry+f' phone {width} panel return retains expanded inspector',page.locator('.energy-feature-inspector').is_visible())
   page.set_viewport_size({'width':1440,'height':1080});page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="energy"]').uncheck();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
   check(entry+' disabling context restores historical roof inspection',page.locator('.campus-feature-inspector').is_visible() and page.evaluate('ATLAS.layers.state.feature===null&&globe.energyPaths.length===0'))
   page.locator('[data-layer-open]').first.click();page.locator('[data-layer-coverage]').click();ready(page);capture(page,entry,'regional-electricity')
   check(entry+' explicit coverage action frames source geometry',page.evaluate('state.spatialLevel===3&&globe instanceof ResearchMap&&globe.energyPaths.length>0'))
   page.goto(base+entry+'#overview?scale=region&site=google-new-carlisle&energy=1&camera=m,-86,40,-85,42,1');ready(page)
   check(entry+' unavailable viewport distinguishes coverage from absence','Outside captured geometry' in page.locator('.map-layer-coverage-state').inner_text())
   page.goto(base+entry+'#overview?scale=world&energy=garbage&energyfeature=unknown&research=garbage');ready(page)
   check(entry+' invalid source state falls back safely',page.evaluate('!ATLAS.layers.on("energy")&&ATLAS.layers.state.feature===null&&ATLAS.layers.on("research")'))
   check(entry+' source context leaves capacity and community inventories unchanged',page.evaluate('[D.sites.length,CATALOG.records.length]')==inventory)
   check(entry+' no uncaught layer errors',not errors)
   if errors:print(errors,flush=True)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks};(ROOT/'qa/layers_results.json').write_text(json.dumps(result,indent=2));print(f"{result['passed']}/{result['total']} passed",flush=True);raise SystemExit(result['passed']!=result['total'])
