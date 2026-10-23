"""Country-to-physical-source journeys on every inhabited continent, online and offline."""
import hashlib, json, os, shutil, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/screenshots/global';OUT.mkdir(parents=True,exist_ok=True)
checks=[];captures=[]
def check(name, value):
    checks.append({'test':name,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=os.environ.get('ATLAS_TEST_BASE') or f'http://127.0.0.1:{server.server_port}/'
def settle(page):
    page.wait_for_function('globe&&!globe.dirty');page.wait_for_timeout(300)
def capture(page,name):
    page.evaluate('scrollTo(0,0)');settle(page);page.screenshot(path=str(OUT/(name+'.png')))
    captures.append({'name':name,'hash':page.url.split('#')[-1],'viewport':page.viewport_size})
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
  entries=[os.environ['ATLAS_GLOBAL_ENTRY']] if os.environ.get('ATLAS_GLOBAL_ENTRY') else ['index.html','compute_atlas.html']
  for entry in entries:
   context=browser.new_context(viewport={'width':1280,'height':960},accept_downloads=True);page=context.new_page();errors=[];requests=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
   page.goto(base+entry);page.wait_for_function('document.documentElement.classList.contains("atlas-ready")');settle(page)
   if entry=='compute_atlas.html':context.set_offline(True);requests.clear()
   page.locator('[data-geo-browse]').first.click()
   check(entry+' all 122 named destinations are available',page.locator('.geo-destination').count()==122)
   page.locator('#geo-country-query').fill('Japan');check(entry+' country search selects one native destination',page.locator('.geo-destination').count()==1)
   page.locator('[data-geo-open-country="Japan"]').click();settle(page)
   check(entry+' destination opens complete country scope',page.evaluate('uaState.country==="Japan"&&uaState.region==="All"&&uaRows().length===uaRecords().filter(r=>r.country==="Japan").length'))
   for region,country in [('Europe','Germany'),('Asia','Japan'),('South America','Brazil'),('Africa','South Africa'),('Oceania','Australia'),('North America','United States')]:
    page.evaluate('region=>uaGo({region,country:"All",selected:null,scale:1,camera:null,scope:"geography"})',region);settle(page)
    check(entry+' '+region+' rail offers an in-scope physical location',page.evaluate('region=>{const id=document.querySelector("[data-geo-inside]")?.dataset.geoInside;return id&&uaRecord(id).region===region}',region))
    page.evaluate('country=>geoCountry(country,true)',country);settle(page)
    check(entry+' '+country+' title and map describe selected geography',country in page.locator('.ua-intro h1').inner_text() and country in page.locator('.ua-map-head h2').inner_text())
    check(entry+' '+country+' complete source scope',page.evaluate('country=>uaRows().length===uaRecords().filter(r=>r.country===country).length',country))
    capture(page,entry+'-'+country.lower().replace(' ','-'))
    page.locator('.ua-rail [data-geo-market]').first.click();settle(page)
    check(entry+' '+country+' local journey retains country and mapped records',page.evaluate('country=>uaState.country===country&&uaState.scale===3&&uaState.scope==="viewport"&&uaRows().length>0&&uaRows().every(r=>r.country===country)',country))
    candidate=page.locator('[data-geo-inside]').first.get_attribute('data-geo-inside');page.locator('[data-geo-inside]').first.click();settle(page)
    check(entry+' '+country+' local action opens its actual source identity',page.evaluate('id=>uaState.selected===id&&globe instanceof FacilityScene',candidate))
    if page.evaluate('!!uaCaptureFor(uaRecord(uaState.selected))'):page.wait_for_function('!uaContextPromise')
    check(entry+' '+country+' physical view preserves original geometry',page.evaluate('globe.features.some(f=>f.record.id===uaState.selected)'))
    capture(page,entry+'-'+country.lower().replace(' ','-')+'-physical')
    page.locator('#breadcrumb [data-geo-country]').click();settle(page)
    check(entry+' '+country+' breadcrumb returns to full country scope',page.evaluate('country=>uaState.country===country&&uaState.selected===null&&uaRows().length===uaRecords().filter(r=>r.country===country).length',country))
   page.evaluate('uaGo({region:"Europe",country:"All",selected:null,scale:1,camera:null,scope:"geography"})');settle(page)
   page.locator('[data-ui-refine]').click();page.locator('[data-ua-filter="country"]').select_option('Japan');settle(page)
   check(entry+' changing country clears an incompatible continent',page.evaluate('uaState.region==="All"&&uaRows().length>0&&uaRows().every(r=>r.country==="Japan")'))
   page.evaluate('uiPreset("world");uaState.members=uaRecords().slice(0,3).map(r=>r.id);document.querySelector("#ua-cluster-members").innerHTML=uaMembersHTML()');settle(page)
   page.locator('[data-ui-refine]').click();page.locator('#ua-query').fill('Tokyo');page.wait_for_timeout(400)
   check(entry+' text refinements clear stale cluster membership',page.evaluate('uaState.members.length===0&&!document.querySelector("#ua-cluster-members").textContent'))
   page.keyboard.press('Escape');page.evaluate('uiPreset("world")');settle(page)
   page.evaluate('globe.zoom=1.8;globe.dirty=true');page.wait_for_timeout(600)
   check(entry+' semantic zoom refreshes the title and breadcrumb',page.evaluate('uaState.scale===1&&document.querySelector(".ui-editorial-atlas").dataset.uaScale==="1"&&document.querySelector("#breadcrumb [aria-current]").textContent==="Continent"') and 'global view' not in page.locator('.ua-intro h1').inner_text())
   image_record=page.evaluate('uaRecords().find(r=>r.mapped&&r.geometry&&geoImageryFor(r)&&!CAMPUS_SCENES.scenes.some(s=>s.project_id===r.id))?.id')
   check(entry+' native outline and aerial-context fixture exists',bool(image_record))
   if image_record:
    page.evaluate('id=>uaGo({region:"All",country:"All",q:"",operator:"",collection:"all",coverage:"all",selected:id,scale:5,scene:null,feature:id,phase:null,camera:null,sceneCamera:null,mode:"aerial",scope:"geography"})',image_record)
    page.wait_for_function('globe?.groundImageReady&&!globe.dirty');page.wait_for_function('!uaContextPromise');settle(page)
    check(entry+' aerial view keeps native outline and dated raster separate',page.evaluate('globe.inspected.id===uaState.selected&&!!globe.inspected.geometry&&!globe.manifest&&globe.groundCapture.image.acquisition_dates.length>0'))
    check(entry+' aerial image and geometry share one ground projection',page.evaluate('(()=>{const s=globe,e=s.groundCapture.image.extent_3857,lon=e.xmin/6378137*180/Math.PI,lat=Math.atan(Math.sinh(e.ymax/6378137))*180/Math.PI,a=s.local(lon,lat),b=s.groundImageCorners[0];return Math.hypot(a[0]-b[0],a[1]-b[1])<.000001&&s.height(s.features[0])===0})()'))
    check(entry+' imagery is pinned in the share URL',page.evaluate('uaURL().includes("imageversion="+globe.groundCapture.image.sha256)'))
    capture(page,entry+'-native-aerial')
    before=page.evaluate('globe.groundCapture.image.sha256');page.locator('[data-geo-save-physical]').click()
    check(entry+' native physical evidence saves a portable view',page.evaluate('saved.views.some(v=>v.hash.includes("feature="+encodeURIComponent(uaState.feature))&&v.hash.includes("imageversion="+globe.groundCapture.image.sha256))'))
    page.evaluate('ATLAS.navigate("watchlist")');page.locator('[data-research-open-view]').last.click();page.wait_for_function('globe?.groundImageReady&&!globe.dirty')
    check(entry+' native saved physical view reopens the exact evidence',page.evaluate('globe.groundCapture.image.sha256')==before and page.evaluate('uaState.selected')==image_record)
    page.locator('.ua-rail [data-ua-context-source]').first.click()
    with page.expect_download() as exported:page.locator('[data-geo-image-export]').click()
    provenance=json.loads(Path(exported.value.path()).read_text())
    check(entry+' imagery export includes native catalog and source recipe',provenance['native_capture']['catalog']['features'] and provenance['native_capture']['image']['sha256']==before)
    with page.expect_download() as exported:page.locator('[data-geo-image-download]').click()
    check(entry+' downloaded image is byte-identical to the pinned source',hashlib.sha256(Path(exported.value.path()).read_bytes()).hexdigest()==before)
    page.keyboard.press('Escape');page.locator('[data-ua-mode="plan"]').click();settle(page)
    check(entry+' plan mode keeps native physical selection',page.evaluate('uaState.feature===uaState.selected&&uaState.mode==="plan"&&globe.height(globe.features[0])===0'))
    page.evaluate('uaGo({imageversion:"0".repeat(64)})');page.wait_for_selector('.ui-source-recovery')
    check(entry+' unavailable imagery versions cannot silently substitute',page.evaluate('globe===null&&uaURL().includes("0".repeat(64))'))
    page.locator('[data-ui-recover-source]').click();page.wait_for_function('globe?.groundImageReady&&!globe.dirty')
   page.evaluate('uiPreset("campus")');page.wait_for_function('globe?.imageReady&&!globe.dirty')
   page.locator('.ua-map-attribution [data-ua-context-source]').click();page.locator('[data-geo-image-library]').click()
   check(entry+' image library exposes every source attempt',page.locator('[data-geo-image-select]').count()==81)
   choice=page.locator('[data-geo-image-select]:enabled').first;image_id=choice.get_attribute('data-geo-image-capture');source_id=choice.get_attribute('data-geo-image-select');choice.click();page.wait_for_function('globe?.groundImageReady&&!globe.dirty')
   check(entry+' library opens the exact image and original anchor identity',page.evaluate('globe.groundCapture.id')==image_id and page.evaluate('uaState.selected')==source_id and page.evaluate('uaState.scene==="anchor-"+globe.groundCapture.id&&!globe.manifest&&uaURL().includes("imageversion="+globe.groundCapture.image.sha256)'))
   page.evaluate('uiPreset("campus")');page.wait_for_function('globe?.imageReady&&!globe.dirty')
   page.locator('[data-ua-scene]').select_option('new-carlisle-sr2-2025');page.wait_for_function('globe?.imageReady&&!globe.dirty')
   check(entry+' component selection restores its separate reviewed imagery',page.evaluate('globe.manifest.id==="new-carlisle-sr2-2025"&&uaURL().includes("imageversion="+globe.manifest.image.sha256)'))
   for width,height in [(1280,720),(768,1024),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('geoCountry("Japan",true)');settle(page)
    check(entry+' country layout fits '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    if width==1280:check(entry+' short desktop country analysis remains fully visible',page.locator('.ua-rail').evaluate('e=>e.scrollHeight<=e.clientHeight+1'))
    page.locator('[data-geo-browse]').first.click();page.locator('#geo-country-query').fill('Japan')
    check(entry+' destination drawer fits '+str(width),page.locator('#drawer').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
    page.screenshot(path=str(OUT/(entry+'-destinations-'+str(width)+'.png')));page.keyboard.press('Escape')
   check(entry+' no runtime errors',not errors)
   if errors:print(json.dumps(errors),flush=True)
   if entry=='compute_atlas.html':check(entry+' global journeys and imagery work without external requests',not requests)
   context.close()
  browser.close()
finally:
 server.shutdown()
 result={'passed':sum(r['pass'] for r in checks),'total':len(checks),'tests':checks,'captures':captures}
 (ROOT/'qa/global_journeys_results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'total':result['total']}),flush=True)
assert checks and all(r['pass'] for r in checks)
