"""Production six-scale composition and connected inspection acceptance.
Screenshots require human visual inspection; geometry checks alone are not a visual grade.
"""
import json, os, shutil, threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/screenshots/editorial';OUT.mkdir(parents=True,exist_ok=True)
checks=[];captures=[]
def check(name,ok):
    checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=os.environ.get('ATLAS_TEST_BASE') or f'http://127.0.0.1:{server.server_port}/'
def settle(page):
    page.wait_for_function('globe&&!globe.dirty');page.wait_for_timeout(180)
def capture(page,name):
    page.evaluate('scrollTo(0,0)');settle(page);page.screenshot(path=str(OUT/(name+'.png')))
    captures.append({'name':name,'url':page.url.split('#')[-1],'viewport':page.viewport_size})
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
  for entry in (['index.html'] if os.environ.get('ATLAS_TEST_BASE') else ['index.html','compute_atlas.html']):
   ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+entry);page.wait_for_function('document.documentElement.classList.contains("atlas-ready")');page.wait_for_function('document.querySelector("#ua-map").dataset.terrain==="natural-earth"');settle(page)
   if entry=='compute_atlas.html':ctx.set_offline(True)
   for preset in ['world','atlantic','region','metro','campus','facility']:
    page.evaluate('id=>uiPreset(id)',preset);settle(page)
    if preset in ['campus','facility']:page.wait_for_function('globe.imageReady&&!globe.dirty')
    capture(page,entry+'-'+preset)
    check(entry+' '+preset+' map dominates the primary content',page.evaluate('(()=>{const map=document.querySelector("#ua-map").getBoundingClientRect(),rail=document.querySelector(".ua-rail").getBoundingClientRect();return map.width>rail.width*2&&map.height>=350&&map.right<rail.left&&map.top<innerHeight*.27})()'))
    check(entry+' '+preset+' all content fits viewport width',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    if preset in ['world','atlantic','region','metro']:
     check(entry+' '+preset+' metric edge remains visible',page.locator('.ua-kpis').evaluate('e=>e.getBoundingClientRect().bottom<innerHeight'))
    else:
     check(entry+' '+preset+' evidence sits under the map',page.evaluate('(()=>{const map=document.querySelector("#ua-map").getBoundingClientRect(),deck=document.querySelector(".ui-evidence-deck").getBoundingClientRect();return deck.left===map.left&&Math.abs(deck.width-map.width)<2&&deck.top<innerHeight*.83})()'))
    if preset=='atlantic':check(entry+' Atlantic scope includes both continents only',page.evaluate('uaRows().length>3000&&new Set(uaRows().map(r=>r.region)).size===2&&uaRows().every(r=>["Europe","North America"].includes(r.region))'))
    if preset=='metro':check(entry+' metro viewport includes Chicago and New Carlisle',page.evaluate('uaRows().some(r=>r.lon< -87.5)&&uaRows().some(r=>r.id==="amazon-anthropic-new-carlisle")'))
   check(entry+' feature inspector matches selected roof',page.evaluate('document.querySelector("#ua-feature-selection h2").textContent===globe.inspected.name&&uaState.feature===globe.inspected.id'))
   page.locator('[data-ui-save-feature]').click();check(entry+' physical evidence saves source versions',page.evaluate('saved.sourceFeatures.some(r=>r.feature_id===uaState.feature&&r.image_sha256===globe.manifest.image.sha256)'))
   page.locator('[data-ui-refine]').click();page.locator('#ua-query').fill('no matching facility xyz');page.wait_for_timeout(350)
   check(entry+' physical refinements retain selected identity and render empty results',page.evaluate('uaState.selected==="coreweave-helios"&&uaRows().length===0&&document.querySelector(".ui-active-filters").textContent.includes("no matching facility xyz")'))
   page.locator('[data-ui-clear-filter="q"]').click();settle(page);page.evaluate('scrollTo(0,0)')
   before=page.evaluate('JSON.stringify(globe.snapshot())');page.locator('[data-ui-phase]').first.click();check(entry+' selecting a power scope retains the physical camera',page.evaluate('JSON.stringify(globe.snapshot())')==before)
   check(entry+' power scope does not highlight a physical roof',page.evaluate('globe.features.every(f=>!f.selected)'))
   check(entry+' power scope has its own shared identity',page.evaluate('!!uaState.phase&&ATLAS.explorer.url().includes("phase=")&&uaState.feature===null'))
   phase=page.evaluate('uaState.phase');page.evaluate('location.hash=uaURL()+"&topic=power"');settle(page)
   check(entry+' shared phase restores camera and highlighted scope',page.evaluate('uaState.phase')==phase and page.evaluate('JSON.stringify(globe.snapshot())')==before and page.locator('[data-ui-phase][aria-pressed="true"]').count()>0)
   page.evaluate('uiPreset("facility")');settle(page)
   check(entry+' shared roof pins image and review versions',page.evaluate('uaURL().includes("imageversion="+globe.manifest.image.sha256)&&uaURL().includes("featureversion="+globe.inspected.review_sha256)'))
   for version in ['imageversion','featureversion','contextversion']:
    if version=='contextversion':
     page.evaluate('uaGo({selected:uaRecords().find(r=>r.collection==="gpu"&&r.mapped&&uaCaptureFor(r)).id,scale:4,scene:null,camera:null,sceneCamera:null})');settle(page)
    page.evaluate('key=>{const params=new URLSearchParams(uaURL().split("?")[1]);params.set(key,"0".repeat(64));location.hash="#atlas?"+params}',version)
    page.wait_for_selector('.ui-source-recovery')
    check(entry+' '+version+' mismatch preserves requested identity without substitution',page.evaluate('globe===null&&uaURL().includes("0".repeat(64))'))
    page.locator('[data-ui-recover-source]').click();settle(page)
    check(entry+' '+version+' explicit recovery opens available evidence',page.locator('.ui-source-recovery').count()==0 and page.evaluate('!uaURL().includes("0".repeat(64))'))
   page.evaluate('uiPreset("facility");uaGo({phase:"unavailable-phase",feature:null})');settle(page)
   check(entry+' missing phase has explicit recovery','Power scope unavailable' in page.locator('.ua-rail').inner_text())
   page.locator('[data-ui-clear-phase]').click();settle(page)
   page.locator('.ua-topics [data-ua-topic="sources"]').click();check(entry+' source topic retains physical hero',page.locator('#ua-map').count()==1 and page.locator('.ua-source-list').count()==1)
   page.locator('.ua-topics [data-ua-topic="overview"]').click();page.locator('[data-ui-claim]').first.click();check(entry+' precise source claim opens over atlas',page.locator('#drawer [data-research-claim]').count()==1);page.keyboard.press('Escape');check(entry+' closing a claim restores its control',page.evaluate('document.activeElement.hasAttribute("data-ui-claim")'))
   page.evaluate('uiPreset("campus")');page.wait_for_function('globe.imageReady&&!globe.dirty')
   power=page.evaluate('globe.features.find(f=>f.record.tags?.power).record.id');page.locator('#ua-feature-choice').select_option(power);settle(page)
   check(entry+' native electricity keeps its own capture and export action',page.locator('[data-ui-save-feature]').count()==0 and page.evaluate('uaURL().includes("contextversion="+energyCollection(globe.inspected.capture_id).response_sha256)'))
   with page.expect_download() as export:page.locator('.ua-rail [data-ua-export-feature]').first.click()
   evidence=json.loads(Path(export.value.path()).read_text());check(entry+' native electricity export retains the exact source object and capture',evidence['record']['id']==power and evidence['capture']['id']==evidence['record']['capture_id'])
   page.evaluate('const params=new URLSearchParams(uaURL().split("?")[1]);params.set("contextversion","0".repeat(64));location.hash="#atlas?"+params');page.wait_for_selector('.ui-source-recovery');page.locator('[data-ui-recover-source]').click();settle(page)
   check(entry+' electricity recovery retains the native feature identity',page.evaluate('uaState.feature')==power and page.evaluate('globe.inspected.id')==power)
   page.evaluate('uiPreset("world")');settle(page);page.locator('[data-ui-measure="power"]').click();check(entry+' metric explains its native boundary','not critical IT load' in page.locator('#drawer-content').inner_text());page.keyboard.press('Escape')
   page.locator('[data-ua-guide]').click();check(entry+' guided journey begins at world',page.evaluate('uaState.scale===0&&!document.querySelector("#tour").hidden'))
   for step in range(1,6):page.locator('#tour [data-ua-guide-next="'+str(step)+'"]').click();settle(page)
   check(entry+' guided journey reaches physical feature',page.evaluate('uaState.scale===5&&!!uaState.feature'));page.locator('[data-ui-return-guide]').click();settle(page);check(entry+' tour restores original exploration',page.evaluate('uaState.scale===0&&document.querySelector("#tour").hidden'))
   for width,height in [(1280,720),(768,1024),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('uiPreset("world");scrollTo(0,0)');settle(page);capture(page,entry+'-world-'+str(width))
    check(entry+' responsive world at '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.querySelector("#ua-map").getBoundingClientRect().height>=250'))
    check(entry+' unique geographic labels at '+str(width),page.evaluate('new Set(globe.markerLabels.map(r=>r.title)).size===globe.markerLabels.length'))
    if width<=390:check(entry+' usable phone scale and zoom targets at '+str(width),page.evaluate('[...document.querySelectorAll(".ua-scales button,.ua-map-buttons button")].every(b=>b.getBoundingClientRect().height>=44)'))
    if width==768:check(entry+' tablet retains adjacent analysis rail',page.evaluate('document.querySelector(".ua-rail").getBoundingClientRect().left>document.querySelector("#ua-map").getBoundingClientRect().right'))
    if width==1280:check(entry+' short-desktop analysis cards fit',page.locator('.ua-rail').evaluate('e=>e.scrollHeight<=e.clientHeight+1'))
    if width==1280:check(entry+' short-desktop metrics visible',page.locator('.ua-kpis').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
    page.evaluate('uiPreset("facility");scrollTo(0,0)');page.wait_for_function('globe.imageReady&&!globe.dirty');capture(page,entry+'-facility-'+str(width))
    check(entry+' responsive physical view at '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    if width==320:check(entry+' narrow phone image selector clears map controls',page.evaluate('document.querySelector(".ua-scene-choice").getBoundingClientRect().right<=document.querySelector(".ua-layer-control").getBoundingClientRect().left'))
    if width==390:
     page.locator('[data-ui-mobile-details]').click();check(entry+' mobile dossier expands on demand',page.locator('.ua-rail').evaluate('e=>e.classList.contains("ui-mobile-open")'))
   for width,height in [(1440,1000),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height})
    for view in ['inventory','companies','contracts','investment','reports','data']:
     page.evaluate('view=>ATLAS.navigate(view)',view)
     check(entry+' connected '+view+' fits at '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    page.evaluate('ATLAS.navigate("reports")')
    failures=page.evaluate('(()=>{const failed=[];for(let r=0;r<A.reports.length;r++){state.report=r;for(let s=0;s<A.reports[r].sections.length;s++){state.section=s;render();if(document.documentElement.scrollWidth>innerWidth)failed.push([r,s]);}}return failed})()')
    check(entry+' every original report section fits at '+str(width),not failures)
    if failures:print('REPORT OVERFLOW',width,failures,flush=True)
   page.evaluate('state.report=0;state.section=0;render()')
   check(entry+' original tables support keyboard scrolling',page.evaluate('[...document.querySelectorAll(".report-body .table-wrap")].every(e=>e.tabIndex===0&&e.getAttribute("aria-label"))'))
   check(entry+' no runtime errors',not errors);print('ERRORS',errors,flush=True);ctx.close()
  browser.close()
finally:
 server.shutdown();(ROOT/'qa/editorial_parity_results.json').write_text(json.dumps({'total':len(checks),'passed':sum(c['pass'] for c in checks),'checks':checks,'captures':captures},indent=2)+'\n')
assert checks and all(c['pass'] for c in checks)
