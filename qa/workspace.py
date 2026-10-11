"""Map-led composition and phase selection through both shipped entrypoints.

ATLAS_TEST_BASE can point at an isolated live-ledger candidate or deployed service.
"""
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
server=None
base=os.environ.get('ATLAS_TEST_BASE')
if not base:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox'])
        for entry in ('index.html','compute_atlas.html'):
            page=browser.new_page(viewport={'width':1440,'height':1080})
            page.set_default_timeout(60000 if os.environ.get('ATLAS_TEST_BASE') else 30000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            check(entry+' HTTP entrypoint',page.goto(base+entry).status==200)
            page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            check(entry+' fresh visit opens world capacity landscape',page.evaluate("state.view==='overview'&&state.spatialLevel===0"))
            check(entry+' source monitor remains directly accessible',page.locator('[data-atlas-action="monitor"]').is_visible())
            check(entry+' map dominates usable desktop area',page.locator('.atlas-map-panel').evaluate('e=>{const r=e.getBoundingClientRect();return r.width>innerWidth*.5&&r.height>innerHeight*.5}'))
            check(entry+' context points explicitly exclude capacity', 'no capacity implied' in page.locator('.atlas-map-legend').inner_text())
            for level in range(6):
                page.locator(f'[data-spatial-action="stage"][data-id="{level}"]').click()
                check(entry+f' scale {level} retains analysis rail',page.locator('.atlas-spatial-rail').is_visible())
                page.screenshot(path=str(OUT/f'{entry}-workspace-scale-{level}.png'))
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(4)")
            before=page.url
            phase=page.locator('[data-workspace-phase]').nth(1)
            claim=phase.get_attribute('data-workspace-phase');label=phase.locator('b').inner_text()
            phase.click()
            check(entry+' phase selection updates facility and rail',page.evaluate('state.spatialLevel')==5 and page.locator('.workspace-selected-phase h2').inner_text()==label)
            check(entry+' phase selection retains keyboard focus',page.locator(f'[data-workspace-phase="{claim}"]').evaluate('e=>e===document.activeElement'))
            selected_url=page.url
            page.reload();page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            check(entry+' shared phase reload restores evidence',page.url==selected_url and page.locator('.workspace-selected-phase h2').inner_text()==label)
            page.go_back();page.wait_for_function('state.spatialLevel===4')
            check(entry+' browser Back restores campus',page.url==before)
            page.locator('[data-workspace-location="true"]').click()
            check(entry+' approximate map is interactive and explicitly bounded',page.locator('#globe-canvas').is_visible() and 'no site footprint established' in page.locator('.workspace-location-map').inner_text())
            page.locator('[data-workspace-location="false"]').click()
            page.locator('[data-research-topic-target="energy"]').click()
            check(entry+' energy evidence remains accessible',page.locator('#drawer [data-research-topic="energy"]').is_visible())
            page.keyboard.press('Escape')
            page.evaluate("ATLAS.navigate('catalog');ATLAS.catalog.select('osm-way-1121454055');catalogSetScale(4)")
            check(entry+' geometry inspector sits beside source scene',page.locator('.atlas-spatial-rail .catalog-inspector').is_visible())
            check(entry+' context geometry is framed in canvas',page.evaluate('(()=>{const g=ATLAS.getGlobe();g.draw();const p=g.hitSurfaces.flatMap(s=>s.rings.flat());return p.length>0&&Math.min(...p.map(x=>x.x))>=0&&Math.max(...p.map(x=>x.x))<=g.w&&Math.min(...p.map(x=>x.y))>=0&&Math.max(...p.map(x=>x.y))<=g.h})()'))
            page.screenshot(path=str(OUT/f'{entry}-workspace-source-campus.png'))
            page.set_viewport_size({'width':1366,'height':768})
            page.evaluate("ATLAS.navigate('overview');ATLAS.spatial.setLevel(0)")
            check(entry+' landscape KPIs fit short desktop',page.locator('.atlas-kpi-grid').first.evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
            page.screenshot(path=str(OUT/f'{entry}-workspace-short-desktop.png'))
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844})
                for level in (0,4,5):
                    page.evaluate(f'ATLAS.spatial.setLevel({level})')
                    check(entry+f' mobile {width} scale {level} fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                page.screenshot(path=str(OUT/f'{entry}-workspace-mobile-{width}.png'),full_page=True)
            check(entry+' no browser errors',not errors)
            page.close()
        browser.close()
finally:
    if server:server.shutdown()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/workspace_results.json').write_text(json.dumps(result,indent=2))
print(f"{result['passed']}/{result['total']} passed")
raise SystemExit(result['passed']!=result['total'])
