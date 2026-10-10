import json,time,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError
import shutil
ROOT=Path(__file__).resolve().parents[1]
results=[];errors=[];network=[]
def record(name,passed,**detail):
 item={'test':name,'pass':bool(passed),**detail};results.append(item);return bool(passed)
server=ThreadingHTTPServer(('127.0.0.1',8765),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('chromium-browser') or p.chromium.executable_path,headless=True,args=['--no-sandbox','--allow-file-access-from-files'])
 page=browser.new_page(viewport={'width':1500,'height':1040},device_scale_factor=1)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http://','https://')) else None)
 page.goto((ROOT/'compute_atlas.html').as_uri(),wait_until='load')
 page.wait_for_function('document.documentElement.classList.contains("research-ready")')
 page.wait_for_timeout(1500)
 page.screenshot(path=str(ROOT/'qa/overview.png'),full_page=True)
 record('initial boot',page.locator('h1').inner_text().startswith('A global view'))
 counts=page.evaluate('({sites:ATLAS.data.sites.length,companies:ATLAS.data.companies.length,sources:ATLAS.data.sources.length,reportSections:ATLAS.archive.reports.map(x=>x.sections.length),workbooks:ATLAS.archive.workbooks.map(x=>x.sheets.length)})')
 for route in ['globe','facilities','companies','contracts','costs','investment','reports','data','stories','watchlist']:
  page.evaluate('(route)=>ATLAS.navigate(route)',route)
  page.wait_for_timeout(170)
  record('route '+route,len(page.locator('#content').inner_text())>150)
 page.evaluate("ATLAS.navigate('globe')")
 page.wait_for_timeout(250)
 page.screenshot(path=str(ROOT/'qa/globe.png'),full_page=True)
 page.locator('[data-atlas-action="fly"][data-id="asia"]').click()
 try:
  page.wait_for_function("Math.abs((((ATLAS.getGlobe().lon-105)+540)%360)-180)<3",timeout=4000)
  asia_ok=True
 except PlaywrightTimeoutError:
  asia_ok=False
 actual_lon=page.evaluate('ATLAS.getGlobe().lon')
 record('globe fly Asia',asia_ok,longitude=actual_lon)
 page.screenshot(path=str(ROOT/'qa/asia.png'),full_page=True)
 page.evaluate("ATLAS.openDrawer('site',ATLAS.data.sites.find(x=>x.name==='Zhangbei').id)")
 page.wait_for_timeout(200)
 page.screenshot(path=str(ROOT/'qa/facility.png'),full_page=False)
 record('facility full dossier',page.locator('#drawer-content').inner_text().find('213,200')>=0)
 page.locator('[data-action="close-drawer"]').click()
 page.evaluate("ATLAS.navigate('costs')")
 page.locator('[data-action="cost-tab"][data-id="scenario"]').click()
 a=page.locator('#scenario-unit').inner_text()
 page.locator('#s-util').fill('40')
 page.locator('#s-util').dispatch_event('input')
 b=page.locator('#scenario-unit').inner_text()
 record('cost sensitivity changes',a!=b,before=a,after=b)
 page.screenshot(path=str(ROOT/'qa/costs.png'),full_page=True)
 page.evaluate("ATLAS.navigate('investment')")
 page.screenshot(path=str(ROOT/'qa/investment.png'),full_page=True)
 page.evaluate("ATLAS.navigate('reports')")
 page.screenshot(path=str(ROOT/'qa/report.png'),full_page=True)
 page.evaluate("ATLAS.state.dataTab='workbooks';ATLAS.navigate('data')")
 page.screenshot(path=str(ROOT/'qa/workbook.png'),full_page=False)
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("ATLAS.navigate('overview')")
 page.wait_for_timeout(300)
 page.screenshot(path=str(ROOT/'qa/mobile.png'),full_page=True)
 record('mobile no page-wide horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'))
 browser.close()
server.shutdown()
report={'tests':results,'errors':errors,'requests':network,'counts':counts,'passed':sum(t['pass'] for t in results),'total':len(results)}
(ROOT/'qa/smoke_results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if report['passed']!=report['total'] or errors or network:
 raise SystemExit(1)
