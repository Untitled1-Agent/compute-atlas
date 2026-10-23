"""Complete analyst sessions: compare, revisions, citations, import, storage and tour."""
import json, os, shutil, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True)
checks=[]
def check(name,ok):
    checks.append({'test':name,'pass':bool(ok)})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
def downloaded(page,selector):
    with page.expect_download() as event:page.locator(selector).click()
    return json.loads(Path(event.value.path()).read_text())
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-gpu','--no-zygote','--renderer-process-limit=1'])
        for entry in ('index.html','compute_atlas.html'):
            context=browser.new_context(viewport={'width':1440,'height':1080})
            page=context.new_page();page.set_default_timeout(15000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry+'#overview');ready(page)
            page.evaluate('ATLAS.workspace.compareDrawer()')
            check(entry+' empty comparison is directly searchable',page.locator('#workspace-compare-query').is_visible())
            for query,project in [('Helios','coreweave-helios'),('New Carlisle','amazon-anthropic-new-carlisle'),('Ellendale','coreweave-ellendale')]:
                page.locator('#workspace-compare-query').fill(query)
                page.locator(f'[data-workspace-add-compare="{project}"]').click()
            check(entry+' comparison caps at three and preserves search focus',page.locator('[data-workspace-remove-compare]').count()==3 and page.locator('#workspace-compare-query').evaluate('e=>e===document.activeElement'))
            page.locator('#workspace-compare-query').fill('Prometheus')
            check(entry+' fourth project cannot be added',page.locator('[data-workspace-add-compare]').first.is_disabled())
            page.locator('[data-workspace-remove-compare="coreweave-ellendale"]').click()
            page.locator('[data-workspace-add-compare="meta-prometheus"]').click()
            check(entry+' selected columns retain unknown quantities and power boundaries','Not quantified' in page.locator('.workspace-project-comparison').inner_text() and 'IT' in page.locator('.workspace-project-comparison').inner_text())
            page.evaluate("saved.notes['coreweave-helios']='PRIVATE PROJECT NOTE';save()")
            payload=downloaded(page,'[data-workspace-export-compare]')
            check(entry+' shared comparison omits private notes by default',not payload['private_notes_included'] and all('private_note' not in x for x in payload['projects']))
            page.locator('[data-workspace-compare-notes]').check()
            payload=downloaded(page,'[data-workspace-export-compare]')
            check(entry+' private notes export requires explicit choice',payload['private_notes_included'] and 'PRIVATE PROJECT NOTE' in json.dumps(payload))
            page.locator('#drawer-content [data-atlas-action="source"]').first.click()
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' source return retains comparison query and privacy choice',page.locator('#workspace-compare-query').input_value()=='Prometheus' and page.locator('[data-workspace-compare-notes]').is_checked())
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844})
                check(entry+f' comparison fits {width}px with internal table scroll',page.locator('#drawer').evaluate('e=>e.scrollWidth<=e.clientWidth+1') and page.locator('.workspace-comparison-scroll').evaluate('e=>e.scrollWidth>e.clientWidth'))
            page.screenshot(path=str(OUT/(entry+'-analyst-comparison-mobile.png')))
            page.set_viewport_size({'width':1440,'height':1080})
            page.evaluate("closeDrawer();ATLAS.evidence.open('coreweave-ellendale')")
            revision=page.locator('[data-revision="ellendale-live-october"]');revision.locator('summary').click()
            check(entry+' revision comparison retains 175 and 250 MW', '175 MW' in revision.inner_text() and '250 MW' in revision.inner_text())
            pair=downloaded(page,'[data-export-revision="ellendale-live-october"]')
            check(entry+' revision export pairs exact predecessor and sources',pair['previous']['id']=='ellendale-live-july' and {s['id'] for s in pair['sources']}=={'P13','P14'})
            page.set_viewport_size({'width':320,'height':844})
            check(entry+' revision comparison fits 320px',page.locator('#drawer').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
            page.screenshot(path=str(OUT/(entry+'-analyst-revisions-mobile.png')))
            page.evaluate("openDrawer('primary-source','P14')")
            check(entry+' primary source has a reusable citation','P14' in page.locator('#atlas-citation-text').input_value())
            page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('unavailable')}}})")
            page.locator('[data-copy-citation]').click()
            check(entry+' unavailable clipboard offers selected text and export','Export citation' in page.locator('.atlas-citation-status').inner_text() and page.locator('#atlas-citation-text').evaluate('e=>e.selectionEnd===e.value.length'))
            page.set_viewport_size({'width':1440,'height':1080})
            page.evaluate("closeDrawer();openDrawer('company','coreweave')")
            page.locator('.company-shelf-action [data-action="favorite"]').click()
            page.locator('#company-local-note').fill('PRIVATE COMPANY NOTE')
            page.evaluate("closeDrawer();ATLAS.navigate('watchlist')")
            check(entry+' company and company note appear on shelf',page.locator('.shelf-company [data-action="company"]').count()==1 and 'PRIVATE COMPANY NOTE' in page.locator('#content').inner_text())
            session=downloaded(page,'#content [data-action="export-session"]')
            session['notes']['osm-way-1121454055']='PRIVATE MAPPED NOTE'
            session['notes']['unavailable-record']='RETAINED NOTE'
            with page.expect_file_chooser() as chooser:page.locator('[data-action="import-session"]').click()
            chooser.value.set_files({'name':'session.json','mimeType':'application/json','buffer':json.dumps(session).encode()})
            page.wait_for_function("saved.notes['osm-way-1121454055']==='PRIVATE MAPPED NOTE'")
            page.reload();ready(page)
            check(entry+' imported project company mapped and unavailable notes survive reload',page.evaluate("saved.notes['coreweave-helios']==='PRIVATE PROJECT NOTE'&&saved.notes.coreweave==='PRIVATE COMPANY NOTE'&&saved.notes['osm-way-1121454055']==='PRIVATE MAPPED NOTE'&&saved.notes['unavailable-record']==='RETAINED NOTE'&&saved.favorites.includes('coreweave')"))
            check(entry+' mapped note links to its actual source record',page.locator('[data-catalog-open="osm-way-1121454055"]').count()>0)
            page.evaluate("ATLAS.navigate('globe');ATLAS.spatial.setLevel(1)")
            page.locator('.atlas-filter-panel summary').click()
            page.locator('#atlas-stage-filter').select_option('unknown')
            filtered=page.url
            check(entry+' missing estimate refinement excludes quantified records',page.evaluate("spatialFiltered().length>0&&spatialFiltered().every(s=>!s.snapshot&&!s.target)"))
            page.reload();ready(page)
            check(entry+' estimate refinement survives shared URL',page.url==filtered and page.evaluate("state.filter.stage==='unknown'"))
            page.locator('[data-workspace-clear="stage"]').click()
            check(entry+' estimate refinement can be removed',page.evaluate("state.filter.stage==='all'"))
            before=page.url
            page.evaluate('startTour()')
            for i in range(4):
                check(entry+f' tour stop {i+1} selects correct campus',page.evaluate('state.spatialLevel===4&&state.spatialSelected===STOPS[state.tour].site().id'))
                page.locator('[data-action="tour-next"]').click()
            check(entry+' tour reaches working scenario model',page.locator('#scenario-unit').count()==1)
            page.locator('[data-action="tour-next"]').click()
            check(entry+' completing tour restores original exploration URL',page.url==before and page.locator('#tour').is_hidden())
            page.evaluate('startTour()');page.locator('[data-action="tour-close"]').click()
            check(entry+' early tour exit restores original exploration URL',page.url==before)
            check(entry+' no uncaught errors',not errors)
            if errors:print(errors,flush=True)
            context.close()
            context=browser.new_context(viewport={'width':390,'height':844})
            context.add_init_script("Storage.prototype.setItem=function(){throw new DOMException('Storage unavailable','QuotaExceededError')}")
            page=context.new_page();page.set_default_timeout(15000)
            page.goto(base+entry+'#overview');ready(page)
            page.evaluate("openDrawer('company','coreweave')")
            page.locator('#company-local-note').fill('RECOVERABLE SESSION NOTE')
            check(entry+' failed storage immediately identifies session-only note','Session-only' in page.locator('[data-storage-status]').inner_text())
            page.evaluate('closeDrawer()')
            check(entry+' failed storage exposes persistent recovery action',page.locator('#atlas-storage-warning').is_visible())
            recovery=downloaded(page,'#atlas-storage-warning [data-action="export-session"]')
            check(entry+' recovery export retains unsaved work',recovery['notes']['coreweave']=='RECOVERABLE SESSION NOTE')
            context.close()
        browser.close()
finally:server.shutdown();server.server_close()
report={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/analyst_results.json').write_text(json.dumps(report,indent=2))
print(f"{report['passed']}/{report['total']} passed",flush=True)
raise SystemExit(report['passed']!=report['total'])
