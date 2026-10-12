"""Initial I/O deadlines, dated fallbacks, terminal failure and real reload recovery."""
import json,os,shutil,socket,sys,tempfile,threading,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1] if __file__.endswith('/qa/startup.py') else Path('/home/username1/workspace/compute-atlas')
OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):
 checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
base=os.environ.get('ATLAS_TEST_BASE');server=None;folder=None;thread=None
if not base:
 sys.path.insert(0,str(ROOT));import uvicorn
 from server.app import create_app
 folder=tempfile.TemporaryDirectory(prefix='compute-atlas-startup-');app=create_app(Path(folder.name)/'atlas.sqlite3',background=False)
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 server=uvicorn.Server(uvicorn.Config(app,log_level='warning',access_log=False));thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start();base=f'http://127.0.0.1:{port}/'
 for attempt in range(100):
  try:
   with urllib.request.urlopen(base+'api/health',timeout=1) as response:
    if response.status==200:break
  except Exception:time.sleep(.1)
 else:raise RuntimeError('Real startup acceptance service did not become healthy')
fragment='#overview?scale=facility&site=amazon-anthropic-new-carlisle&scene=new-carlisle-sr2-2025&selection=feature&feature=new-carlisle-sr2-2025-roof-west-upper'
def ready(page):page.wait_for_function('document.documentElement.classList.contains("layers-ready")&&typeof globe!=="undefined"&&globe&&!globe.dirty&&!globe.target')
def terminal(page):return page.evaluate('window.ATLAS_BOOT_FAILED===true&&window.ATLAS_BOOTSTRAPPING===true&&!document.documentElement.classList.contains("atlas-ready")&&document.querySelector(".app-shell").inert&&document.activeElement.id==="atlas-boot-reload"')
def covers_viewport(page):return page.evaluate('(()=>{const p=document.querySelector("#atlas-boot-failure"),r=p.getBoundingClientRect();return Math.abs(r.x)<1&&Math.abs(r.y)<1&&Math.abs(r.width-innerWidth)<1&&Math.abs(r.height-innerHeight)<1&&document.documentElement.scrollWidth<=innerWidth+1&&[".app-shell",".sidebar",".skip"].every(s=>document.querySelector(s).inert&&getComputedStyle(document.querySelector(s)).visibility==="hidden")})()')

try:
 with sync_playwright() as driver:
  browser=driver.chromium.launch(executable_path=shutil.which('chromium') or driver.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1366,'height':768});page=ctx.new_page();page.set_default_timeout(120000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   start=time.monotonic();page.goto(base+entry+fragment,wait_until='domcontentloaded');ready(page);page.wait_for_function('globe.imageReady&&!globe.dirty');print(entry,'COLD_READY_SECONDS',round(time.monotonic()-start,2),flush=True)
   check(entry+' complete startup keeps the requested roof',page.locator('.campus-feature-inspector h2').inner_text()=='West upper roof')
   camera=page.evaluate('campusCameraParam(globe.snapshot())');url=page.url
   page.reload(wait_until='domcontentloaded');ready(page);page.wait_for_function('globe.imageReady&&!globe.dirty')
   check(entry+' normal reload preserves component and source camera',page.url==url and page.evaluate('campusCameraParam(globe.snapshot())')==camera and page.locator('.campus-feature-inspector h2').inner_text()=='West upper roof')
   check(entry+' normal startup has no loading error or false warning',not page.locator('#atlas-boot-failure').count() and page.evaluate('!window.ATLAS_SERVICE_WARNING&&!window.ATLAS_CATALOG_WARNING&&!window.ATLAS_DIRECTORY_WARNING&&!window.ATLAS_DIGITAL_REALTY_WARNING'))
   check(entry+' normal startup has no uncaught errors',not errors)
   page.screenshot(path=str(OUT/(entry+'-startup-healthy.png')),full_page=True);ctx.close()
  ctx=browser.new_context(viewport={'width':1366,'height':768});page=ctx.new_page();page.set_default_timeout(120000);held=[]
  # Only the four initial publication routes are stalled; every fallback is real,
  # integrity-pinned repository data, with its own dated warning.
  for endpoint in ['publication','catalog/publication','operators/publication*']:
   page.route('**/api/'+endpoint,lambda route:held.append(route))
  page.goto(base+'index.html'+fragment,wait_until='domcontentloaded')
  hosted=page.evaluate('Boolean(window.ATLAS_SERVICE)')
  if hosted:
   ready(page);page.wait_for_function('globe.imageReady&&!globe.dirty')
   check('stalled live publication uses all four named snapshot fallbacks',page.evaluate('window.ATLAS_SERVICE_WARNING&&window.ATLAS_CATALOG_WARNING&&window.ATLAS_DIRECTORY_WARNING&&window.ATLAS_DIGITAL_REALTY_WARNING'))
   evidence=json.loads((ROOT/'data/evidence.json').read_text());check('fallback retains the exact bundled evidence publication',page.evaluate('ATLAS_PRIMARY')==evidence)
   check('fallback retains the selected roof and its historical image',page.locator('.campus-feature-inspector h2').inner_text()=='West upper roof' and '2025' in page.locator('.campus-historic-badge').inner_text())
   check('fallback explains evidence service failure visibly','checked-in publication' in page.locator('.atlas-service-warning').inner_text())
   page.screenshot(path=str(OUT/'index.html-startup-fallback.png'),full_page=True)
   for view,selector,warning in [('catalog','.notice.warning','dated checked-in map snapshot'),('operators','.operator-warning','dated checked-in snapshot'),('publisher','.operator-warning','dated checked-in Digital Realty publication')]:
    page.goto(base+'index.html#'+view,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.classList.contains("layers-ready")')
    check(view+' fallback is dated and visible',warning in page.locator(selector).inner_text())
  else:check('static hosted entry keeps no live-service dependency',not held)
  for route in held:
   try:route.abort()
   except Exception:pass
  ctx.unroute_all(behavior='ignoreErrors');ctx.close()
  for asset,kind in [('data/world.json','Data request'),('src/map-layers.js','Script'),('src/directory-schema.js','Script'),('src/styles.css','Stylesheet')]:
   ctx=browser.new_context(viewport={'width':390,'height':844});page=ctx.new_page();page.set_default_timeout(120000);held=[];optional=[]
   page.on('request',lambda request:optional.append(request.url) if any(part in request.url for part in ['/api/status','/api/review-queue','/api/publication?']) else None)
   pattern='**/'+asset+'*';page.route(pattern,lambda route:held.append(route));page.goto(base+'index.html'+fragment,wait_until='domcontentloaded')
   page.locator('#atlas-boot-failure').wait_for()
   check(asset+' stalled I/O becomes named accessible failure',terminal(page) and kind+' timed out' in page.locator('#boot-error-message').inner_text() and asset in page.locator('#boot-error-message').inner_text())
   check(asset+' failure starts no optional service polling',not optional)
   check(asset+'390px failure covers the viewport and hides the incomplete shell',covers_viewport(page))
   page.screenshot(path=str(OUT/('index.html-startup-failure-'+asset.split('/')[-1]+'.png')))
   mime='application/json' if asset.endswith('.json') else 'text/css' if asset.endswith('.css') else 'text/javascript'
   page.set_viewport_size({'width':320,'height':844});page.wait_for_timeout(150)
   check(asset+'320px failure remains readable across the whole viewport',covers_viewport(page))
   page.screenshot(path=str(OUT/('index.html-startup-failure320-'+asset.split('/')[-1]+'.png')))
   for route in held:
    try:route.fulfill(status=200,body=(ROOT/asset).read_bytes(),content_type=mime)
    except Exception:pass # Aborted requests can no longer be fulfilled.
   page.wait_for_timeout(800)
   check(asset+' late matching asset cannot mark failed startup ready',terminal(page) and not optional)
   page.unroute(pattern);page.locator('#atlas-boot-reload').click();ready(page);page.wait_for_function('globe.imageReady&&!globe.dirty')
   check(asset+' real reload recovers the requested component',not page.locator('#atlas-boot-failure').count() and page.locator('.campus-feature-inspector h2').inner_text()=='West upper roof')
   ctx.close()
  browser.close()
finally:
 if server:server.should_exit=True;thread.join(timeout=10)
 if folder:folder.cleanup()
result={'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)}
(ROOT/'qa/startup_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(str(result['passed'])+'/'+str(result['total'])+' passed',flush=True)
raise SystemExit(0 if all(c['pass'] for c in checks) else 1)
