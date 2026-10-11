"""Geography-to-evidence and project-comparison journeys in both entrypoints."""
import json, os, shutil, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name, ok):
    checks.append({'test':name,'pass':bool(ok)})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
server=None;base=os.environ.get('ATLAS_TEST_BASE')
if not base:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox']+(['--disable-gpu','--no-zygote','--renderer-process-limit=1'] if os.environ.get('ATLAS_LIGHT_BROWSER') else []))
        for entry in ('index.html','compute_atlas.html'):
            context=browser.new_context(viewport={'width':1440,'height':1080})
            page=context.new_page();page.set_default_timeout(120000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry);page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            page.wait_for_function('!ATLAS.getGlobe().dirty')
            page.screenshot(path=str(OUT/(entry+'-editorial-world.png')))
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(4)")
            campus=page.url
            for topic in ('energy','technical','development','commercial','finance','evidence'):
                page.locator(f'[data-workspace-topic="{topic}"]').click()
                check(entry+' '+topic+' stays in campus',page.evaluate('state.spatialSelected==="coreweave-helios"&&state.spatialLevel===4') and page.locator('#drawer').is_hidden())
                if topic not in ('evidence',):check(entry+' '+topic+' has in-place evidence',page.locator(f'[data-workspace-topic-content="{topic}"]').is_visible())
            page.locator('[data-workspace-topic="development"]').click()
            timeline_url=page.url
            page.reload();page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            check(entry+' topic survives sharing/reload',page.url==timeline_url and page.locator('[data-workspace-topic-content="development"]').is_visible())
            page.screenshot(path=str(OUT/(entry+'-editorial-timeline.png')),full_page=True)
            page.locator('[data-workspace-topic="overview"]').click()
            page.locator('[data-workspace-phase="helios-phase2-it"]').click()
            phase_url=page.url
            page.locator('.workspace-selected-phase [data-atlas-action="source"]').first.click()
            check(entry+' selected phase opens original source',page.locator('#drawer').is_visible())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
            if page.url!=phase_url:print('SOURCE_RETURN_URL',phase_url,page.url,flush=True)
            check(entry+' source close preserves phase/topic URL',page.url==phase_url)
            page.locator('[data-workspace-topic="energy"]').focus();page.keyboard.press('ArrowRight')
            check(entry+' topic arrow keys select and focus',page.locator('[data-workspace-topic="technical"]').evaluate('e=>e===document.activeElement&&e.getAttribute("aria-selected")==="true"'))
            page.locator('.atlas-intro [data-action="favorite"]').click()
            check(entry+' shelf action reflects saved state','On research shelf' in page.locator('.atlas-intro [data-action="favorite"]').inner_text())
            page.locator('.workspace-selected-phase [data-workspace-compare]').click()
            page.evaluate("ATLAS.spatial.select('amazon-anthropic-new-carlisle');ATLAS.spatial.setLevel(4)")
            page.locator('.workspace-selected-phase [data-workspace-compare]').click()
            page.locator('[data-workspace-open-compare]').click()
            check(entry+' compares project quantities with sources',page.locator('.workspace-project-comparison').is_visible() and 'Snapshot IT estimate' in page.locator('#drawer-content').inner_text() and page.locator('#drawer-content [data-atlas-action="source"]').count()>0)
            page.screenshot(path=str(OUT/(entry+'-editorial-comparison.png')),full_page=True)
            page.locator('#drawer-content [data-atlas-action="source"]').first.click()
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' source Back restores project comparison',page.locator('.workspace-project-comparison').is_visible())
            with page.expect_download() as event:page.locator('[data-workspace-export-compare]').click()
            payload=json.loads(Path(event.value.path()).read_text())
            check(entry+' comparison export contains two cited dossiers',len(payload['projects'])==2 and all(p.get('project_claim_ids') for p in payload['projects']))
            page.locator('[data-workspace-remove-compare="coreweave-helios"]').click()
            check(entry+' comparison remove retains the other project',page.locator('[data-workspace-remove-compare]').count()==1)
            page.keyboard.press('Escape');page.reload();page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            check(entry+' comparison persists only in local research storage',page.evaluate('saved.projectCompare.length===1&&saved.projectCompare[0]==="amazon-anthropic-new-carlisle"'))
            page.evaluate("ATLAS.navigate('watchlist')")
            with page.expect_download() as event:page.locator('[data-action="export-session"]').click()
            session=json.loads(Path(event.value.path()).read_text())
            check(entry+' research-session export retains project comparison',session.get('projectCompare')==['amazon-anthropic-new-carlisle'])
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(2)")
            page.locator('.atlas-filter-panel summary').click();page.locator('#atlas-country-filter').select_option('China')
            check(entry+' excluded selected project retains identity',page.evaluate('state.spatialSelected==="coreweave-helios"') and 'outside the current refinements' in page.locator('.workspace-data-warning').inner_text())
            page.locator('[data-workspace-clear="country"]').click()
            check(entry+' removable refinement restores scope',page.evaluate('state.filter.country==="all"') and page.locator('.workspace-data-warning').count()==0)
            page.evaluate("ATLAS.spatial.setLevel(0);state.spatialSelectionActive=false;render()")
            for level in range(6):
                page.evaluate(f'ATLAS.spatial.setLevel({level})')
                page.wait_for_function('!ATLAS.getGlobe()||!ATLAS.getGlobe().dirty')
                page.screenshot(path=str(OUT/(entry+f'-editorial-scale-{level}.png')))
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844})
                for level in (0,4,5):
                    page.evaluate(f'ATLAS.spatial.setLevel({level})')
                    check(entry+f' editorial mobile {width}/{level} fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                page.screenshot(path=str(OUT/(entry+f'-editorial-mobile-{width}.png')),full_page=True)
            check(entry+' no uncaught errors',not errors)
            if errors:print(errors,flush=True)
            context.close()
        browser.close()
finally:
    if server:server.shutdown()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/editorial_results.json').write_text(json.dumps(result,indent=2))
print(f"{result['passed']}/{result['total']} passed",flush=True)
raise SystemExit(result['passed']!=result['total'])
