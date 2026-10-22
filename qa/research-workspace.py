"""Portable native bookmarks, named views and complete safe spreadsheet exports."""
import csv,io,json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];checks=[]
def check(name,value):
 checks.append({'test':name,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
server=None;base=os.environ.get('ATLAS_TEST_BASE')
if not base:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):page.wait_for_function('document.documentElement.classList.contains("atlas-ready")')
def export(page,selector):
 with page.expect_download() as event:page.locator(selector).click()
 return Path(event.value.path()).read_text(encoding='utf-8-sig')
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
  for entry in ['index.html','compute_atlas.html']:
   ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
   page.goto(base+entry+'#inventory');ready(page)
   check(entry+' shelf preserves the existing project research interface',page.evaluate('typeof ATLAS.research.open==="function"&&typeof ATLAS.research.profile==="function"&&typeof ATLAS.shelf.import==="function"'))
   selected=page.evaluate('inventoryRecords().find(r=>r.collection==="equinix").id')
   page.evaluate('id=>inventoryGo({selected:id})',selected)
   page.locator('[data-research-pin]').click()
   check(entry+' operator listing saves without becoming a project',page.evaluate('saved.records.length===1&&saved.favorites.length===0'))
   page.locator('.inventory-note summary').click();page.locator('#inventory-note').fill('Private investigation: do not export to public CSV')
   check(entry+' note and bookmark count one source identity',page.locator('#shelf-count').inner_text()=='1')
   page.evaluate("inventoryGo({q:'Frankfurt',collection:'equinix',selected:null})")
   address=page.evaluate('inventoryURL()');page.locator('[data-research-save-view]').click();page.locator('#research-view-name').fill('Frankfurt operator study');page.locator('#research-view-form button[type=submit]').click()
   check(entry+' named view saves exact filtered address',page.evaluate('saved.views[0].hash')==address)
   page.evaluate("ATLAS.navigate('watchlist')");page.reload();ready(page)
   check(entry+' bookmarks notes and views survive reload',page.locator('[data-research-bookmark]').count()==1 and page.locator('[data-research-open-view]').count()==1)
   page.locator('[data-research-open-view]').click()
   check(entry+' saved view restores filters and collection',page.evaluate('inventoryURL()')==address and page.locator('#inventory-query').input_value()=='Frankfurt')
   expected=page.evaluate('inventoryRows().length');content=export(page,'[data-research-csv="inventory"]');rows=list(csv.DictReader(io.StringIO(content)))
   check(entry+' inventory CSV includes every filtered record and source identity',len(rows)==expected and all(r['collection']=='equinix' and r['source_urls'] for r in rows))
   check(entry+' CSV excludes private notes', 'Private investigation' not in content)
   page.evaluate("ATLAS.navigate('watchlist')");page.locator('[data-research-rename]').click();page.locator('#research-view-name').fill('Renamed study');page.locator('#research-view-form button[type=submit]').click()
   check(entry+' renamed view keeps its route',page.evaluate('saved.views[0].name==="Renamed study"') and page.evaluate('saved.views[0].hash')==address)
   page.locator('[data-research-remove-record]').click();check(entry+' removal retains notes',page.evaluate('saved.records.length===0&&Object.keys(saved.notes).length===1'));page.locator('[data-research-undo]').click();check(entry+' undo restores source bookmark',page.locator('[data-research-bookmark]').count()==1)
   session=json.loads(export(page,'[data-action="export-session"]'))
   check(entry+' portable session includes views and versioned native records',len(session['views'])==1 and len(session['records'])==1 and session['records'][0]['source_version'])
   page.evaluate('saved.records=[];saved.views=[];saved.notes={};save();render()')
   with page.expect_file_chooser() as chooser:page.locator('[data-action="import-session"]').click()
   chooser.value.set_files({'name':'research.json','mimeType':'application/json','buffer':json.dumps(session).encode()});page.locator('[data-research-bookmark]').wait_for()
   check(entry+' imported session restores records views and private notes',page.evaluate('saved.records.length===1&&saved.views.length===1&&Object.keys(saved.notes).length===1'))
   page.evaluate("saved.records[0].source_version='old';saved.records.push({id:'osm:way:999999999999',name:'Earlier source',collection:'osm',source_version:'1',captured_at:'2020-01-01',saved_at:'2020-01-01'});save();render()")
   check(entry+' changed publication and unavailable source stay explicit','has changed' in page.locator('.research-shelf').inner_text() and 'Unavailable in this publication' in page.locator('.research-shelf').inner_text())
   page.locator('[data-research-bookmark="osm:way:999999999999"] [data-inventory-open]').click()
   check(entry+' missing bookmark opens recoverable source identity','Record unavailable' in page.locator('#inventory-inspector').inner_text())
   check(entry+' unsafe and malformed imported view routes rejected',page.evaluate("researchViews([{id:'view-a',name:'x',hash:'javascript:alert(1)'},{id:'view-b',name:'x',hash:'#inventory?q=%E0'},{id:'view-c',name:'x',hash:'#unknown'},{id:'view-d',name:'safe',hash:'#inventory?q=Frankfurt'}]).length===1"))
   check(entry+' CSV protects formula text and preserves negative numeric data',page.evaluate('researchCSV([["=SUM(1,2)"," +cmd","@x",-10,"line\\nquote\\\""]])')=='\ufeff"\'=SUM(1,2)","\' +cmd","\'@x","-10","line\nquote"""')
   for collection in ['osm','digital']:
    native=page.evaluate('(collection)=>inventoryRecords().find(r=>r.collection===collection).id',collection);page.evaluate('id=>inventoryGo({selected:id,q:"",collection:"all"})',native);page.locator('[data-research-pin]').click()
    check(entry+' '+collection+' native bookmark keeps source version',page.evaluate('id=>saved.records.some(r=>r.id===id&&r.source_version)',native))
    page.locator('[data-catalog-open]' if collection=='osm' else '[data-inventory-native]').click()
    check(entry+' '+collection+' native explorer exposes the saved source bookmark',page.locator('[data-research-pin][aria-pressed=\"true\"]').count()==1)
   page.evaluate("inventoryGo({collection:'osm',q:'Frankfurt'})");rows=list(csv.DictReader(io.StringIO(export(page,'[data-research-csv=\"inventory\"]'))))
   check(entry+' geometry spreadsheet preserves licensing and attribution',all(json.loads(r['source_metadata_json']).get('license') and json.loads(r['source_metadata_json']).get('attribution') for r in rows))
   page.evaluate("ATLAS.navigate('contracts')");expected=page.evaluate('connectionRows().length');rows=list(csv.DictReader(io.StringIO(export(page,'[data-research-csv="connections"]'))))
   check(entry+' connection CSV retains all source-linked native claims',len(rows)==expected and len(rows)>16 and all(r['source_ids'] and r['native_record_json'] for r in rows))
   page.evaluate("discoveryGo({q:'Microsoft',type:'cell'})");expected=page.evaluate('discoveryRows().length');rows=list(csv.DictReader(io.StringIO(export(page,'[data-research-csv="search"]'))))
   check(entry+' workbook search CSV exports uncapped cached native records',len(rows)==expected and len(rows)>25 and all('cell' in json.loads(r['native_record_json']) for r in rows))
   page.evaluate("ATLAS.navigate('overview');ATLAS.spatial.select('amazon-anthropic-new-carlisle');ATLAS.spatial.setLevel(4)");page.locator('[data-campus-feature="new-carlisle-edison-2025-roof-central"]').click()
   expected=page.evaluate('researchCurrentHash()');page.locator('[data-research-save-view]').click();page.locator('#research-view-name').fill('Campus roof evidence');page.locator('#research-view-form button[type=submit]').click();page.evaluate("ATLAS.navigate('watchlist')");page.locator('[data-research-open-view]').last.click()
   check(entry+' saved campus view restores exact dated roof',page.evaluate('researchCurrentHash()')==expected and 'Central long roof' in page.locator('#breadcrumb').inner_text())
   for view,setup,verify in [
    ('companies',"state.companyQ='GDS';state.companyRegion='China'", "state.companyQ==='GDS'&&state.companyRegion==='China'"),
    ('reports',"state.report=1;state.section=3;state.reportQ='power'", "state.report===1&&state.section===3&&state.reportQ==='power'"),
    ('data',"state.dataTab='workbooks';state.book=1;state.sheet=1;state.dataQ='NVIDIA'", "state.dataTab==='workbooks'&&state.book===1&&state.sheet===1&&state.dataQ==='NVIDIA'"),
    ('facilities',"state.filter.country='China';state.filter.q='';state.layout='cards';state.sort='name'", "state.filter.country==='China'&&state.layout==='cards'&&state.sort==='name'"),
    ('costs',"state.costTab='hardware';state.costQ='GPU'", "state.costTab==='hardware'&&state.costQ==='GPU'"),
    ('compare',"state.compare=['amazon','microsoft']", "state.compare.join(',')==='amazon,microsoft'")]:
    page.evaluate(setup+";ATLAS.navigate('"+view+"')");address=page.evaluate('researchCurrentHash()');page.goto(base+entry+address);ready(page)
    check(entry+' saved '+view+' view restores its exact collection state',page.evaluate(verify))
   page.evaluate("ATLAS.research.open()")
   check(entry+' project research index has a savable address',page.evaluate("researchHash(researchCurrentHash())?.startsWith('#research')"))
   page.keyboard.press('Escape');page.evaluate("openDrawer('help')")
   check(entry+' help explains import replacement and offline mode','Import session replaces' in page.locator('#drawer-content').inner_text() and ('This standalone contains' if entry=='compute_atlas.html' else 'This hosted app loads') in page.locator('#drawer-content').inner_text())
   if entry=='index.html':check(entry+' hosted help offers a downloadable standalone',page.locator('a[download="compute-atlas.html"]').count()==1)
   page.keyboard.press('Escape');page.evaluate("ATLAS.navigate('watchlist')")
   for width in [390,320]:
    page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(250);check(entry+f' research shelf fits {width}px',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   page.locator('[data-action=\"menu\"]').click();page.locator('[data-research-save-view]').click()
   check(entry+' saving a view on phone closes navigation and focuses its name',page.locator('#sidebar').get_attribute('aria-hidden')=='true' and page.locator('#research-view-name').is_visible())
   page.keyboard.press('Escape')
   check(entry+' no browser exceptions',not errors)
   if errors:print(errors,flush=True)
   ctx.close()
  browser.close()
finally:
 if server:server.shutdown();server.server_close()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks};(ROOT/'qa/research_workspace_results.json').write_text(json.dumps(result,indent=2)+'\n');print(f"{result['passed']}/{result['total']} passed");raise SystemExit(result['passed']!=result['total'])
