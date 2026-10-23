"""Primary global-to-facility journeys through both distributed entrypoints."""
import json,shutil,threading,os
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True);checks=[]
def check(name,value):
 checks.append({'test':name,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):page.wait_for_function('document.documentElement.classList.contains("atlas-ready")&&!!document.querySelector("#ua-map")')
def frame(page):page.wait_for_function('globe&&!globe.dirty')
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
  for entry in (['index.html'] if os.environ.get('ATLAS_TEST_BASE') else ['index.html','compute_atlas.html']):
   ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto((os.environ.get('ATLAS_TEST_BASE') or base)+entry);ready(page);frame(page)
   check(entry+' default landscape contains every collection',page.evaluate('state.view==="atlas"&&uaRows().length===inventoryRecords().length&&new Set(uaRows().map(r=>r.collection)).size===6'))
   check(entry+' primary navigation has one landscape',page.locator('#navigation [data-id="atlas"]').count()==1)
   check(entry+' Pacific neighbors fit across the antimeridian',page.evaluate('(()=>{const b=uaFitBounds([{lon:179,lat:10},{lon:-179,lat:11}],null,.1,.1);return b[2]-b[0]<3&&catalogParseCamera(catalogCameraToken({flat:true,lat:10,lon:180,zoom:1,bounds:b}))!==null})()'));
   check(entry+' no horizontal desktop overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   page.screenshot(path=str(OUT/(entry+'-unified-world.png')))
   if entry=='compute_atlas.html':ctx.set_offline(True)
   point=page.evaluate('globe.groups.find(g=>g.sites.length>1&&g.x>globe.w*.3&&g.x<globe.w*.8&&g.y>65&&g.y<globe.h-135)')
   if point:
    before=page.evaluate('catalogCameraToken(catalogCameraSnapshot(globe))');rect=page.locator('#ua-map').bounding_box();page.mouse.click(rect['x']+point['x'],rect['y']+point['y'])
    check(entry+' canvas cluster click opens its actual members',page.evaluate('uaState.members.length')==len(point['sites']))
    check(entry+' cluster inspection leaves camera in place',page.evaluate('catalogCameraToken(catalogCameraSnapshot(globe))')==before)
    page.locator('[data-ua-fit-members]').click();frame(page);check(entry+' cluster drill fits its records',page.evaluate('globe.flat&&uaState.scale>=2'))
   page.evaluate('uaGo({region:"All",country:"All",collection:"all",selected:null,scale:0,camera:null})');frame(page)
   page.locator('#ua-map').scroll_into_view_if_needed();rect=page.locator('#ua-map').bounding_box();before=page.evaluate('globe.lon');page.mouse.move(rect['x']+rect['width']*.52,rect['y']+rect['height']*.55);page.mouse.down();page.mouse.move(rect['x']+rect['width']*.65,rect['y']+rect['height']*.55,steps=8);page.mouse.up();frame(page)
   check(entry+' dragging the globe changes its actual camera',page.evaluate('globe.lon')!=before)
   page.locator('[data-ua-region="Europe"]').first.click();frame(page)
   check(entry+' continent changes camera and scope',page.evaluate('uaRows().length>100&&uaRows().every(r=>r.region==="Europe")&&globe.zoom>1&&uaState.scale===1'))
   page.locator('summary').filter(has_text='Refine the atlas').click();page.locator('[data-ua-filter="country"]').select_option('Germany');frame(page)
   check(entry+' country fits its own geography',page.evaluate('uaRows().length>100&&uaRows().every(r=>r.country==="Germany")&&globe.flat&&globe.bounds[0]>0&&globe.bounds[2]<30'))
   page.evaluate('uaGo({region:"All",country:"All",collection:"gpu",selected:null,scale:0,camera:null})');page.locator('summary').filter(has_text='Refine the atlas').click();page.locator('#ua-query').fill('colossus');page.wait_for_timeout(300)
   check(entry+' search and collection intersect without deleting source rows',page.evaluate('uaRows().length>0&&uaRows().every(r=>r.collection==="gpu"&&r.search.includes("colossus"))&&uaRecords().length===6471'))
   page.locator('.ua-row [data-ua-select]').first.click();frame(page);selected=page.evaluate('uaState.selected');camera=page.evaluate('catalogCameraToken(catalogCameraSnapshot(globe))')
   check(entry+' selection retains the shared map',page.evaluate('!!uaState.selected&&state.view==="atlas"') and page.locator('.ua-detail').count()==1)
   page.locator('[data-ua-topic="sources"]').last.click();check(entry+' GPU evidence retains every native field',page.locator('#ua-topic-content .gpu-native-fields dt').count()==57)
   check(entry+' topic selection does not move camera',page.evaluate('catalogCameraToken(catalogCameraSnapshot(globe))')==camera)
   page.locator('[data-ua-scale="3"]').click();frame(page);check(entry+' metro drill changes camera extent',page.evaluate('globe.flat&&globe.bounds[2]-globe.bounds[0]<2&&uaState.selected')==selected)
   page.locator('[data-ua-scale="4"]').click();page.wait_for_function('!document.querySelector("#ua-context-status").textContent.includes("Loading")',timeout=40000);frame(page)
   check(entry+' selected global anchor loads native physical context',page.evaluate('globe instanceof UnifiedFacilityScene&&globe.features.some(f=>f.polygons.length)&&!!uaContext'))
   check(entry+' no untagged building heights are invented',page.evaluate('!globe.assumptions&&globe.features.filter(f=>f.record.height_m==null).every(f=>globe.height(f)===0)'))
   options=page.locator('#ua-feature-choice option');check(entry+' native geometry is keyboard selectable',options.count()>1)
   if options.count()>1:
    feature=options.nth(1).get_attribute('value');page.locator('#ua-feature-choice').select_option(feature);frame(page)
    check(entry+' selected physical source owns the adjacent inspector',page.locator('#ua-feature-selection h2').inner_text()==page.evaluate('globe.inspected.name'));
    check(entry+' physical feature opens facility inspection',page.evaluate('uaState.scale===5&&uaState.feature===globe.inspected.id'))
   page.locator('[data-ua-mode="3d"]').click();frame(page);check(entry+' 3D mode changes physical camera',page.evaluate('globe.pitch<1&&uaState.mode==="3d"'))
   page.locator('[data-ua-map="in"]').click();frame(page);page.locator('[data-ua-share]').click();shared=page.locator('#ua-share-url').input_value();page.locator('[data-action="close-drawer"]').first.click()
   before=page.evaluate('JSON.stringify({selected:uaState.selected,feature:uaState.feature,mode:uaState.mode,camera:globe.snapshot()})')
   ctx.set_offline(False);page.goto(shared);ready(page);page.wait_for_function('!document.querySelector("#ua-context-status").textContent.includes("Loading")',timeout=40000);frame(page)
   check(entry+' share restores selected geometry and physical camera',page.evaluate('JSON.stringify({selected:uaState.selected,feature:uaState.feature,mode:uaState.mode,camera:globe.snapshot()})')==before)
   if entry=='compute_atlas.html':ctx.set_offline(True)
   page.evaluate('uaGo({region:"All",country:"All",q:"",collection:"all",selected:EPOCH_CENTERS.tables.centers.records[0].id,scale:0,camera:null,topic:"timeline"})');frame(page)
   page.locator('[data-epoch-metric]').select_option('Power (MW)');check(entry+' data-center timeline remains inside atlas',page.evaluate('state.view==="atlas"') and page.locator('.epoch-timeline').count()==1)
   check(entry+' timeline measure is shareable',page.evaluate('uaURL().includes("metric=Power")'));page.locator('.epoch-timeline details summary').click();page.locator('[data-epoch-open]').first.click();check(entry+' source row opens over the preserved atlas',page.evaluate('state.view==="atlas"') and page.locator('#drawer .epoch-inspector').count()==1);page.locator('#drawer [data-epoch-close]').click();check(entry+' source close returns to atlas',page.locator('#drawer').is_hidden());
   page.locator('[data-ua-topic="hardware"]').click();check(entry+' deployment evidence is present',page.locator('#ua-topic-content').inner_text().startswith('Published accelerator deployments'))
   page.evaluate('uaGo({selected:"amazon-anthropic-new-carlisle",scale:4,camera:null,sceneCamera:null,mode:"aerial",topic:"overview"})');page.wait_for_function('globe.imageReady&&!globe.dirty');page.screenshot(path=str(OUT/(entry+'-unified-campus.png')))
   check(entry+' project imagery retains reviewed roof identities',page.evaluate('globe instanceof UnifiedCampusScene&&globe.features.length>=3&&!!globe.manifest.image.sha256'))
   page.locator('[data-ua-scene]').select_option('new-carlisle-sr2-2025');page.wait_for_function('globe.imageReady&&!globe.dirty');check(entry+' imagery attribution names the actual publisher','Indiana' in page.locator('.ua-map-attribution').inner_text());check(entry+' source electricity features are available',page.evaluate('globe.features.some(f=>f.record.tags?.power)'));check(entry+' component selection changes imagery and roofs',page.evaluate('globe.manifest.id==="new-carlisle-sr2-2025"&&globe.features.filter(f=>f.polygons.length).length===5'))
   page.locator('[data-ua-topic="timeline"]').click();check(entry+' project timeline uses dated development evidence',page.locator('[data-workspace-topic-content="development"]').count()==1);page.locator('[data-ua-topic="finance"]').click();check(entry+' project finance retains its own claims',page.locator('[data-workspace-topic-content="finance"]').count()==1);
   page.locator('[data-ua-topic="notes"]').click();page.locator('#ua-note').fill('Review source assumptions');page.wait_for_timeout(400);check(entry+' notes persist on original record identity',page.evaluate('saved.notes[uaState.selected]==="Review source assumptions"'))
   page.evaluate('uaGo({scale:0,camera:null,sceneCamera:null,selected:null,compare:["amazon-anthropic-new-carlisle",GPU_CLUSTERS.records[0].id,EPOCH_CENTERS.tables.centers.records[0].id]})')
   check(entry+' cross-source comparison labels incompatible measures',page.locator('.ua-comparison').count()==1 and 'H100e' in page.locator('.ua-comparison').inner_text() and 'MW IT' in page.locator('.ua-comparison').inner_text())
   with page.expect_download() as event:page.locator('[data-ua-export-compare]').click()
   exported=json.loads(Path(event.value.path()).read_text());check(entry+' comparison export excludes private notes','Review source assumptions' not in json.dumps(exported))
   page.locator('[data-ua-map="expand"]').click();check(entry+' expanded map fits viewport',page.locator('.ua-expanded').count()==1);page.keyboard.press('Escape');check(entry+' Escape restores layout',page.locator('.ua-expanded').count()==0)
   page.evaluate('uaGo({region:"All",country:"All",collection:"all",q:"",selected:null,compare:[],scale:0,camera:null})')
   for width,height in [(1280,720),(768,1024),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('window.scrollTo(0,0);document.querySelector("#toast").classList.remove("visible")');page.wait_for_timeout(350);frame(page);page.screenshot(path=str(OUT/(entry+'-unified-'+str(width)+'.png')))
    check(entry+' usable map at '+str(width),page.locator('#ua-map').bounding_box()['height']>=250 and page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   page.evaluate('uaGo({selected:uaRecords().find(r=>r.collection==="equinix").id,scale:0,camera:null,scene:null})');unmapped=page.evaluate('uaState.selected');page.locator('[data-ua-scale="4"]').click();check(entry+' unmapped selection is never replaced with another facility',page.evaluate('uaState.selected')==unmapped and page.evaluate('uaState.scale<4'));
   page.evaluate('uaGo({selected:"amazon-anthropic-new-carlisle",scale:4,scene:"unavailable-image",camera:null,sceneCamera:null})');frame(page);check(entry+' unavailable image identity is retained without substitution',page.evaluate('uaState.scene==="unavailable-image"&&!(globe instanceof UnifiedCampusScene)') and 'unavailable-image' in page.locator('#ua-context-status').inner_text());
   check(entry+' no runtime errors',not errors);print('ERRORS',errors,flush=True);ctx.close()
  browser.close()
finally:
 server.shutdown();(ROOT/'qa/unified-atlas_results.json').write_text(json.dumps(checks,indent=2))
assert checks and all(c['pass'] for c in checks)
