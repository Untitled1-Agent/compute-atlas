"""Shared camera, scoped records and phone inspection through both real entrypoints."""
import json, os, shutil, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):
    checks.append({'test':name,'pass':bool(ok)})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page):
    page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
    page.wait_for_function('!globe||(!globe.dirty&&!globe.target)')
    page.wait_for_timeout(350) # Camera publication deliberately settles after 220 ms.
def ids(page):return page.locator('[data-workspace-record]').evaluate_all('rows=>rows.map(r=>r.dataset.workspaceRecord)')
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox']+(['--disable-gpu','--no-zygote','--renderer-process-limit=1'] if os.environ.get('ATLAS_LIGHT_BROWSER') else []))
        for entry in ('index.html','compute_atlas.html'):
            context=browser.new_context(viewport={'width':1440,'height':1080});page=context.new_page();page.set_default_timeout(120000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry);ready(page)
            page.locator('.workspace-records summary').click()
            check(entry+' record pagination limits DOM to twelve rows',len(ids(page))==12)
            first=set(ids(page));page.locator('[data-workspace-page="next"]').click()
            check(entry+' second page contains distinct projects',not first.intersection(ids(page)) and len(ids(page))==12)
            second=ids(page);page.reload();ready(page)
            check(entry+' geographic page survives sharing',ids(page)==second)
            page.locator('#workspace-record-sort').select_option('name')
            names=page.locator('.workspace-record-name').all_text_contents()
            check(entry+' name sort resets pagination',names==sorted(names,key=str.casefold) and 'Page 1 of' in page.locator('.workspace-record-footer').inner_text())
            with page.expect_download() as event:page.locator('[data-workspace-export-records]').click()
            export=json.loads(Path(event.value.path()).read_text())
            check(entry+' scoped export includes every match and citations',len(export['projects'])>12 and all('primary_sources' in s and 'archival_sources' in s and 'private_note' not in s for s in export['projects']) and export['record_scope']=='geography')
            page.locator('[data-atlas-action="fly"][data-id="americas"]').click();ready(page)
            page.locator('#workspace-record-scope').select_option('visible')
            check(entry+' visible scope excludes far-side Chinese anchors',page.evaluate("workspaceRecordData(spatialScope(state.spatialLevel,spatialDefaultSite()),state.spatialPhase).rows.every(s=>s.country!=='China')"))
            before=page.evaluate('workspaceRecordData(spatialScope(state.spatialLevel,spatialDefaultSite()),state.spatialPhase).rows.map(s=>s.id)');canvas=page.locator('#globe-canvas');canvas.focus();
            for _ in range(10):page.keyboard.press('ArrowRight')
            ready(page)
            check(entry+' pan updates visible records and retains canvas',page.evaluate('workspaceRecordData(spatialScope(state.spatialLevel,spatialDefaultSite()),state.spatialPhase).rows.map(s=>s.id)')!=before and page.locator('#globe-canvas').count()==1)
            moved=page.evaluate('({lat:globe.lat,lon:globe.lon,zoom:globe.zoom})');url=page.url
            page.reload();ready(page)
            restored=page.evaluate('({lat:globe.lat,lon:globe.lon,zoom:globe.zoom})')
            check(entry+' shared moved globe restores exact camera',all(abs(moved[k]-restored[k])<.00002 for k in moved))
            check(entry+' record scope and sort survive reload',page.locator('#workspace-record-scope').input_value()=='visible' and page.locator('#workspace-record-sort').input_value()=='name' and page.locator('.workspace-records').get_attribute('open') is not None)
            page.locator('[data-atlas-action="labels"]').click()
            check(entry+' labels update the share route','labels=0' in page.url and not page.evaluate('globe.labels'))
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(2)");ready(page)
            page.locator('[data-atlas-action="roads"]').click();ready(page)
            canvas=page.locator('#globe-canvas');box=canvas.bounding_box();page.mouse.move(box['x']+box['width']*.6,box['y']+box['height']*.5);page.mouse.down();page.mouse.move(box['x']+box['width']*.6+80,box['y']+box['height']*.5+30,steps=5);page.mouse.up();ready(page)
            bounds=page.evaluate('globe.bounds');regional_url=page.url
            page.reload();ready(page)
            check(entry+' regional pan restores Mercator bounds',all(abs(a-b)<.00002 for a,b in zip(bounds,page.evaluate('globe.bounds'))))
            check(entry+' labels and roads survive reload',page.evaluate('state.spatialLabels===false&&state.spatialRoads===false'))
            page.evaluate('ATLAS.spatial.setLevel(3)');ready(page)
            page.go_back();ready(page)
            check(entry+' Back restores regional scale and camera',page.evaluate('state.spatialLevel===2') and all(abs(a-b)<.00002 for a,b in zip(bounds,page.evaluate('globe.bounds'))))
            page.go_forward();ready(page)
            check(entry+' Forward restores the metro scale',page.evaluate('state.spatialLevel===3'))
            page.go_back();ready(page)
            page.locator('[data-workspace-share]').click()
            shared=page.locator('#workspace-share-url').input_value()
            check(entry+' share link is selectable and excludes private storage','camera=' in shared and 'roads=0' in shared and 'notes=' not in shared and page.locator('#workspace-share-url').get_attribute('readonly') is not None)
            page.locator('[data-workspace-copy-link]').click()
            check(entry+' clipboard fallback is usable',any(x in page.locator('.workspace-share-status').inner_text() for x in ('copied','selected')))
            page.keyboard.press('Escape')
            page.locator('#workspace-record-scope').select_option('selection')
            check(entry+' selection scope is independent from geographic page',ids(page)==['coreweave-helios'])
            page.locator('.workspace-record-name').click();ready(page)
            check(entry+' table selection retains scale',page.evaluate('state.spatialLevel===2&&state.spatialSelected==="coreweave-helios"'))
            page.locator('.workspace-record-table [data-atlas-action="campus"]').click();ready(page)
            page.locator('[data-workspace-location="true"]').click();ready(page)
            page.reload();ready(page)
            check(entry+' campus location view survives sharing',page.locator('.workspace-location-map').is_visible() and page.evaluate('state.spatialLevel===4'))
            page.locator('[data-workspace-location="false"]').click()
            page.evaluate('ATLAS.spatial.setLevel(0)');ready(page)
            groups=page.evaluate('globe.groups.filter(g=>g.sites.length>1).map(g=>g.sites.map(s=>s.id))')
            if groups:
                group=groups[0]
                page.evaluate('(members)=>{state.spatialCluster=members;spatialTransition({selected:members[0]})}',group);ready(page)
                page.reload();ready(page)
                check(entry+' cluster membership survives shared link',page.evaluate('state.spatialCluster')==group and page.locator('.workspace-cluster-members button').count()==len(group))
            else:check(entry+' cluster available for shared-link test',False)
            page.goto(base+entry+'#overview?scale=region&site=coreweave-helios&camera=m,NaN,1,2,3,1&labels=garbage&records=garbage');ready(page)
            check(entry+' malformed shared state falls back to finite map and defaults',page.evaluate('globe.bounds.every(Number.isFinite)&&state.spatialLabels===true&&state.spatialRoads===true&&workspaceState.records.scope==="geography"'))
            page.goto(base+entry+'#overview?scale=world&camera=g,85,-140,3&records=visible&recordsopen=1');ready(page)
            check(entry+' empty visible map retains geographic coverage and explains recovery',page.locator('[data-workspace-record]').count()==0 and 'No records match' in page.locator('.workspace-record-table').inner_text() and page.evaluate('ATLAS.spatial.scope().sites.length>0'))
            page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios&inspect=1');ready(page)
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844});ready(page)
                summary=page.locator('[data-workspace-inspector]');detail=page.locator('#workspace-selection-detail')
                check(entry+f' phone {width} starts with compact selection',summary.is_visible() and detail.is_hidden())
                check(entry+f' phone {width} selection precedes topic evidence',summary.bounding_box()['y']<page.locator('.atlas-detail-pair').bounding_box()['y'])
                camera=page.evaluate('workspaceCurrentCamera()')
                summary.click()
                check(entry+f' phone {width} expands inspector without changing selection',detail.is_visible() and page.evaluate('state.spatialSelected==="coreweave-helios"&&state.spatialLevel===4') and page.evaluate('workspaceCurrentCamera()')==camera)
                page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+f'-exploration-phone-expanded-{width}.png')),full_page=True)
                page.locator('.workspace-selected-phase [data-atlas-action="source"]').first.click();page.keyboard.press('Escape')
                check(entry+f' phone {width} source return keeps inspector expanded',detail.is_visible())
                page.keyboard.press('Escape')
                check(entry+f' phone {width} Escape collapses and restores focus',detail.is_hidden() and summary.evaluate('e=>e===document.activeElement'))
                page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+f'-exploration-phone-compact-{width}.png')),full_page=True)
                check(entry+f' phone {width} has no page overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            page.set_viewport_size({'width':1366,'height':768});page.evaluate('ATLAS.spatial.setLevel(2)');ready(page)
            page.locator('.workspace-records summary').click()
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-exploration-records-desktop.png')),full_page=True)
            check(entry+' desktop retains full adjacent inspector',page.locator('#workspace-selection-detail').is_visible() and page.locator('[data-workspace-inspector]').is_hidden())
            check(entry+' desktop table uses full available width',page.locator('.workspace-record-scroll').bounding_box()['width']>=page.locator('.workspace-records').bounding_box()['width']*.95 and page.locator('.workspace-record-scroll').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
            check(entry+' page controls remain below all twelve records',page.locator('.workspace-record-footer').bounding_box()['y']>=page.locator('.workspace-record-table').bounding_box()['y']+page.locator('.workspace-record-table').bounding_box()['height'])
            check(entry+' no uncaught exploration errors',not errors)
            if errors:print(errors,flush=True)
            context.close()
        browser.close()
finally:
    if server:server.shutdown()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/exploration_results.json').write_text(json.dumps(result,indent=2));print(f"{result['passed']}/{result['total']} passed",flush=True)
raise SystemExit(result['passed']!=result['total'])
