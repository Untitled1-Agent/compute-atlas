"""Full research search: uncapped workbook hits, exact claims, sources and files."""
import json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True);checks=[]
def check(name,value):checks.append({'test':name,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=None;base=os.environ.get('ATLAS_TEST_BASE')
if not base:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):page.wait_for_function('document.documentElement.classList.contains("atlas-ready")')
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
   page.goto(base+entry+'#search');ready(page)
   check(entry+' search indexes every original workbook cell and attachment',page.evaluate('discoveryRecords().filter(r=>r.type==="cell").length===A.workbooks.flatMap(b=>b.sheets.flatMap(s=>s.cells)).length&&discoveryRecords().filter(r=>r.type==="attachment").length===8'))
   page.evaluate("ATLAS.discovery.go({q:'Microsoft',type:'cell'})")
   expected=page.evaluate('A.workbooks.flatMap(b=>b.sheets.flatMap(s=>s.cells.map(c=>[b.filename,c.value??"",c.formula??""].join(" ")))).filter(t=>t.toLowerCase().includes("microsoft")).length')
   check(entry+' workbook matches are not capped at 25',expected>25 and page.evaluate('discoveryRows().length')==expected)
   initial=page.locator('.discovery-result').first.inner_text();page.locator('[data-discovery-page="1"]').click();second=page.locator('.discovery-result').first.inner_text();bookmark=page.url
   check(entry+' next page reaches previously hidden workbook matches',second!=initial and page.evaluate('discoveryState.page')==1)
   page.reload();ready(page)
   check(entry+' search query type and page survive reload',page.url==bookmark and page.locator('.discovery-result').first.inner_text()==second)
   exact=page.locator('.discovery-result').first.get_attribute('data-id');page.locator('.discovery-result').first.click()
   check(entry+' workbook result opens exact original sheet and cell',page.evaluate('state.book')==int(exact.split('|')[0]) and page.evaluate('state.sheet')==int(exact.split('|')[1]) and exact.split('|')[2] in page.locator('#drawer-content h1').inner_text())
   page.keyboard.press('Escape');page.go_back();ready(page)
   check(entry+' Back restores full search page after workbook inspection',page.evaluate('state.view')=='search' and page.evaluate('discoveryState.page')==1)
   page.evaluate("ATLAS.discovery.go({q:'helios',type:'claim'})")
   check(entry+' primary claims include source locators and exact project targets',page.locator('[data-research-site="coreweave-helios"]').count()>0)
   bookmark=page.url;target=page.locator('[data-research-claim-target]').first.get_attribute('data-research-claim-target');page.locator('[data-research-claim-target]').first.click()
   check(entry+' claim result reveals exact cited statement',page.locator(f'#drawer [data-research-claim="{target}"]').is_visible())
   page.keyboard.press('Escape')
   check(entry+' claim drawer returns to exact search filters',page.url==bookmark)
   page.evaluate("ATLAS.discovery.go({q:'ellendale-live-july',type:'claim'})")
   check(entry+' earlier evidence remains searchable with revision boundary','Earlier / rejected revision' in page.locator('.discovery-result').inner_text())
   page.locator('[data-discovery-history]').click()
   check(entry+' historical result opens evidence revision desk',page.locator('#drawer').is_visible() and page.evaluate('state.drawer.kind')=='evidence')
   page.keyboard.press('Escape')
   page.evaluate("ATLAS.discovery.go({q:'Frankfurt',type:'listing'})")
   check(entry+' operator results cross both primary directories',page.evaluate('new Set(discoveryRows().map(r=>r.record.collection)).size')==2)
   selected=page.locator('[data-discovery-inventory]').first.get_attribute('data-discovery-inventory');page.locator('[data-discovery-inventory]').first.click()
   check(entry+' directory result keeps its native source identity',page.evaluate('inventoryState.selected')==selected)
   page.locator('.inventory-note summary').click();page.locator('#inventory-note').fill('Check publisher coordinate source')
   page.evaluate("ATLAS.navigate('watchlist')")
   check(entry+' source directory note is discoverable on the research shelf',page.locator('[data-inventory-open]').count()==1 and page.locator('#shelf-count').inner_text()=='1')
   page.reload();ready(page);page.locator('[data-inventory-open]').click()
   check(entry+' saved note returns to the exact native source after reload',page.evaluate('inventoryState.selected')==selected and page.locator('#inventory-note').input_value()=='Check publisher coordinate source')
   page.evaluate("ATLAS.discovery.go({q:'SUM(',type:'cell'})")
   check(entry+' formula text is searchable even when a cached numeric value exists',page.evaluate('discoveryRows().some(r=>r.record.cell.formula&&r.record.cell.value!=null)'))
   page.evaluate("ATLAS.discovery.go({q:'Helios',type:'all'})")
   with page.expect_download() as event:page.locator('[data-discovery-export]').click()
   exported=json.loads(Path(event.value.path()).read_text())
   check(entry+' search export includes every matching result and claim sources',len(exported['records'])==page.evaluate('discoveryRows().length') and len(exported['claim_sources'])>0 and 'Private notes excluded' in exported['policy'])
   check(entry+' search previews contain readable native metadata', '[object Object]' not in page.locator('.discovery-results').inner_text())
   page.screenshot(path=str(OUT/(entry+'-discovery-desktop.png')))
   page.evaluate('openSearch()');page.locator('#global-search').fill('helios');page.locator('[data-discovery-all]').wait_for(state='visible');page.locator('[data-discovery-all]').click()
   check(entry+' command search exposes complete paginated results',page.locator('#search-modal').is_hidden() and page.evaluate('state.view')=='search' and page.locator('#discovery-query').input_value()=='helios')
   for width in [390,320]:
    page.set_viewport_size({'width':width,'height':844})
    page.wait_for_timeout(250)
    check(entry+f' mobile navigation is hidden at {width}px',page.locator('#sidebar').get_attribute('aria-hidden')=='true' and not page.locator('#navigation .nav-button').first.is_visible())
    check(entry+f' full research search fits {width}px',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.screenshot(path=str(OUT/(entry+f'-discovery-{width}.png')))
   page.evaluate("ATLAS.discovery.go({q:'',type:'all'})")
   check(entry+' empty search shows corpus coverage and disables empty export',page.locator('.discovery-start').is_visible() and page.locator('[data-discovery-export]').is_disabled())
   page.evaluate("ATLAS.discovery.go({q:'<script>unexpected</script>',type:'all'})")
   check(entry+' arbitrary input is rendered safely',page.locator('.discovery-results script').count()==0 and page.locator('.empty').count()>0)
   check(entry+' no browser exceptions',not errors)
   if errors:print(errors,flush=True)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown();server.server_close()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks};(ROOT/'qa/discovery_results.json').write_text(json.dumps(result,indent=2)+'\n');print(f"{result['passed']}/{result['total']} passed");raise SystemExit(result['passed']!=result['total'])
