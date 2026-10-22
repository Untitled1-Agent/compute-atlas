"""Global datasets through both shipped entrypoints, including fully offline use."""
import hashlib,json,shutil,threading
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
def ready(page):page.wait_for_function('document.documentElement.classList.contains("atlas-ready")')
def exported(page,selector,kind='json'):
 with page.expect_download() as event:page.locator(selector).first.click()
 raw=Path(event.value.path()).read_bytes()
 return json.loads(raw) if kind=='json' else raw
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
  for entry in ('index.html','compute_atlas.html'):
   context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+entry+'#gpu');ready(page)
   check(entry+' defaults expose the complete GPU publication',page.evaluate('gpuRows().length===482&&GPU_CLUSTERS.columns.length===57&&gpuState.owner==="all"'))
   check(entry+' six inventory collections retain unique identities',page.evaluate('inventoryRecords().length===6471&&new Set(inventoryRecords().map(r=>r.id)).size===6471&&Object.keys(INVENTORY_COLLECTIONS).length===6'))
   check(entry+' all new source tables are indexed',page.evaluate('discoveryRecords().filter(r=>["gpu","datacenter","infrastructure"].includes(r.type)).length===2085'))
   if entry=='compute_atlas.html':context.set_offline(True)
   page.locator('[data-gpu-filter="country"]').select_option('Japan');page.locator('[data-gpu-filter="certainty"]').select_option('Confirmed')
   check(entry+' GPU refinements intersect',page.evaluate('gpuRows().length>0&&gpuRows().every(r=>r.country==="Japan"&&r.certainty==="Confirmed")'))
   bookmark=page.url
   context.set_offline(False);page.reload();ready(page)
   if entry=='compute_atlas.html':context.set_offline(True)
   check(entry+' GPU filter state survives reload',page.url==bookmark and page.evaluate('gpuState.country==="Japan"&&gpuState.certainty==="Confirmed"'))
   page.locator('.gpu-record [data-gpu-open]').first.click();selected=page.evaluate('gpuState.selected')
   check(entry+' selected cluster exposes every raw field',page.locator('.gpu-native-fields dt').count()==57)
   before=page.evaluate('JSON.stringify(globe.bounds)');page.locator('[data-gpu-map="in"]').click()
   check(entry+' GPU map zoom changes camera',page.evaluate('JSON.stringify(globe.bounds)')!=before)
   page.locator('#gpu-detail [data-research-pin]').click()
   check(entry+' cluster can be saved without becoming a project',page.evaluate('saved.records.some(r=>r.id===gpuState.selected&&r.collection==="gpu")&&!saved.sites?.includes(gpuState.selected)'))
   record=exported(page,'[data-gpu-export-record]')
   check(entry+' cluster export retains source fields and CC BY attribution',len(record['records'])==1 and len(record['records'][0]['fields'])==57 and record['license']=='CC-BY-4.0')
   page.locator('#gpu-detail [data-gpu-compare]').click()
   check(entry+' cluster comparison preserves unknown quantities',page.locator('.gpu-comparison').count()==1 and 'Not disclosed' in page.locator('.gpu-comparison').inner_text())
   page.locator('[data-gpu-reset]').click();page.locator('[data-gpu-filter="history"]').select_option('superseded')
   check(entry+' all superseded phases are available',page.evaluate('gpuRows().length===30'))
   page.locator('.gpu-record [data-gpu-open]').first.click();page.locator('.gpu-lineage [data-gpu-open]').last.click()
   check(entry+' successor links open actual source records',page.evaluate('!!gpuRecord(gpuState.selected)'))
   page.evaluate('gpuGo({country:"China",history:"all",certainty:"all",q:"",owner:"all",selected:null})')
   check(entry+' anonymous Chinese records remain accessible',page.evaluate('gpuRows().length===188&&gpuRows().every(r=>r.anonymous)'))
   page.locator('.gpu-record [data-gpu-open]').first.click()
   check(entry+' anonymity is explicit in the inspector','Anonymized by Epoch AI' in page.locator('#gpu-detail').inner_text())
   page.evaluate('ATLAS.navigate("datacenters")')
   check(entry+' complete six-table package is reachable',page.locator('.epoch-tabs button').count()==6 and page.evaluate('epochRows().length===95'))
   raw=exported(page,'[data-epoch-original]','bytes')
   check(entry+' original ZIP download is byte-exact',hashlib.sha256(raw).hexdigest()==page.evaluate('EPOCH_CENTERS.source_sha256'))
   page.locator('[data-epoch-filter="country"]').select_option('Malaysia')
   check(entry+' center geography filter exposes Malaysia',page.evaluate('epochRows().length===3'))
   page.locator('.epoch-record').first.click()
   check(entry+' selection preserves active country filter',page.evaluate('epochState.country==="Malaysia"'))
   check(entry+' selected center links actual timeline and deployments',page.locator('.epoch-timeline svg').count()==1 and page.locator('.epoch-chip-rows button').count()>0)
   page.locator('[data-epoch-metric]').select_option('Power (MW)')
   check(entry+' independent power metric is shareable','metric=Power' in page.url and page.locator('.epoch-timeline svg').get_attribute('aria-label').startswith('Power (MW)'))
   page.locator('#epoch-detail [data-research-pin]').click()
   page.locator('[data-epoch-compare]').first.click()
   check(entry+' center comparison uses dated native fields',page.locator('.gpu-comparison').count()==1 and '2025 USD' in page.locator('.gpu-comparison').inner_text())
   selected_center=page.evaluate('epochState.selected');page.locator('.epoch-chip-rows button').first.click()
   check(entry+' deployment retains linked parent and source confidence',page.evaluate('epochState.table==="deployments"') and page.locator('.epoch-fields dt').count()==11 and 'Number of Units source' in page.locator('.epoch-fields').inner_text())
   page.locator('#epoch-detail [data-epoch-table="centers"]').first.click()
   check(entry+' deployment parent returns exact data center',page.evaluate('epochState.selected')==selected_center)
   for table,total in [('timelines',567),('deployments',239),('chillers',143),('towers',527),('chips',32)]:
    page.locator('[data-epoch-tab="'+table+'"]').click();check(entry+' all '+table+' rows are reachable',page.evaluate('epochRows().length')==total)
    exported_rows=exported(page,'[data-epoch-export]')
    check(entry+' '+table+' export includes offscreen pages',len(exported_rows['records'])==total and exported_rows['license']=='CC-BY-4.0')
   page.locator('[data-epoch-tab="towers"]').click();page.locator('[data-epoch-page="1"]').click();bookmark=page.url
   context.set_offline(False);page.reload();ready(page)
   if entry=='compute_atlas.html':context.set_offline(True)
   check(entry+' equipment table and page survive reload',page.url==bookmark and page.evaluate('epochState.table==="towers"&&epochState.page===1'))
   page.evaluate('ATLAS.discovery.go({q:"ACCPS161",type:"infrastructure"})');page.locator('[data-epoch-open]').first.click()
   check(entry+' complete search opens exact equipment row',page.evaluate('epochState.table==="chillers"') and 'ACCPS161' in page.locator('#epoch-detail h2').inner_text())
   page.evaluate('ATLAS.navigate("markets")');page.locator('#markets-query').fill('Japan')
   check(entry+' global coverage exposes collection-specific counts',page.locator('.markets-table tbody tr').count()==1)
   page.locator('[data-market-country="Japan"][data-market-collection="gpu"]').click()
   check(entry+' coverage drilldown opens exact native directory scope',page.evaluate('inventoryState.country==="Japan"&&inventoryState.collection==="gpu"&&inventoryRows().length===25'))
   page.locator('[data-inventory-select]').first.click()
   check(entry+' common directory opens native GPU dossier',page.locator('[data-gpu-detail]').count()==1)
   check(entry+' directory source inspector has one bookmark control',page.locator('#inventory-inspector [data-research-pin]').count()==1)
   page.locator('[data-inventory-close]').click()
   check(entry+' directory source selection dismisses cleanly',page.evaluate('inventoryState.selected===null'))
   page.evaluate('ATLAS.inventory.go({collection:"epochdc",country:"all",selected:EPOCH_CENTERS.tables.centers.records[0].id})')
   bookmark=page.url;page.locator('[data-epoch-metric]').select_option('Power (MW)')
   check(entry+' directory timeline metric retains directory route',page.url==bookmark and page.locator('.epoch-timeline svg').get_attribute('aria-label').startswith('Power (MW)'))
   page.evaluate('ATLAS.navigate("watchlist")')
   check(entry+' shelf retains both new native collection types',page.evaluate('saved.records.some(r=>r.collection==="gpu")&&saved.records.some(r=>r.collection==="epochdc")'))
   check(entry+' source types survive session validation',page.evaluate('researchRecords(saved.records).length===saved.records.length'))
   for route in ['gpu','datacenters','markets']:
    page.evaluate('ATLAS.navigate('+json.dumps(route)+')')
    for width,height in [(1440,1000),(1024,768),(390,844),(320,844)]:
     page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
     check(entry+f' {route} fits {width}px',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
     if width in (1440,390):page.screenshot(path=str(OUT/f'{entry}-{route}-{width}.png'),full_page=True)
   check(entry+' no uncaught errors',not errors)
   context.close()
  browser.close()
finally:server.shutdown()
result={'passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks};(ROOT/'qa/global_publications_results.json').write_text(json.dumps(result,indent=2));print(f"{result['passed']}/{result['total']} passed");raise SystemExit(result['passed']!=result['total'])
