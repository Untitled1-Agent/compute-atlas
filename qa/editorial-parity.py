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
   before=page.evaluate('JSON.stringify(globe.snapshot())');page.locator('[data-ui-phase]').first.click();check(entry+' selecting a power scope retains the physical camera',page.evaluate('JSON.stringify(globe.snapshot())')==before)
   check(entry+' power scope does not highlight a physical roof',page.evaluate('globe.features.every(f=>!f.selected)'))
   check(entry+' power scope has its own shared identity',page.evaluate('!!uaState.phase&&uaURL().includes("phase=")&&uaState.feature===null'))
   page.locator('.ua-topics [data-ua-topic="sources"]').click();check(entry+' source topic retains physical hero',page.locator('#ua-map').count()==1 and page.locator('.ua-source-list').count()==1)
   page.locator('.ua-topics [data-ua-topic="overview"]').click();page.locator('[data-ui-claim]').first.click();check(entry+' precise source claim opens over atlas',page.locator('#drawer [data-research-claim]').count()==1);page.keyboard.press('Escape');check(entry+' closing a claim restores its control',page.evaluate('document.activeElement.hasAttribute("data-ui-claim")'))
   page.evaluate('uiPreset("world")');settle(page);page.locator('[data-ui-measure="power"]').click();check(entry+' metric explains its native boundary','not critical IT load' in page.locator('#drawer-content').inner_text());page.keyboard.press('Escape')
   page.locator('[data-ua-guide]').click();check(entry+' guided journey begins at world',page.evaluate('uaState.scale===0&&!document.querySelector("#tour").hidden'))
   for step in range(1,6):page.locator('#tour [data-ua-guide-next="'+str(step)+'"]').click();settle(page)
   check(entry+' guided journey reaches physical feature',page.evaluate('uaState.scale===5&&!!uaState.feature'));page.locator('[data-ui-return-guide]').click();settle(page);check(entry+' tour restores original exploration',page.evaluate('uaState.scale===0&&document.querySelector("#tour").hidden'))
   for width,height in [(1280,720),(768,1024),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('uiPreset("world");scrollTo(0,0)');settle(page);capture(page,entry+'-world-'+str(width))
    check(entry+' responsive world at '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.querySelector("#ua-map").getBoundingClientRect().height>=250'))
    if width==768:check(entry+' tablet retains adjacent analysis rail',page.evaluate('document.querySelector(".ua-rail").getBoundingClientRect().left>document.querySelector("#ua-map").getBoundingClientRect().right'))
    if width==1280:check(entry+' short-desktop analysis cards fit',page.locator('.ua-rail').evaluate('e=>e.scrollHeight<=e.clientHeight+1'))
    if width==1280:check(entry+' short-desktop metrics visible',page.locator('.ua-kpis').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
    page.evaluate('uiPreset("facility");scrollTo(0,0)');page.wait_for_function('globe.imageReady&&!globe.dirty');capture(page,entry+'-facility-'+str(width))
    check(entry+' responsive physical view at '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    if width==390:
     page.locator('[data-ui-mobile-details]').click();check(entry+' mobile dossier expands on demand',page.locator('.ua-rail').evaluate('e=>e.classList.contains("ui-mobile-open")'))
   check(entry+' no runtime errors',not errors);print('ERRORS',errors,flush=True);ctx.close()
  browser.close()
finally:
 server.shutdown();(ROOT/'qa/editorial_parity_results.json').write_text(json.dumps({'total':len(checks),'passed':sum(c['pass'] for c in checks),'checks':checks,'captures':captures},indent=2)+'\n')
assert checks and all(c['pass'] for c in checks)
