"""Regional landing analysis and physical entry, through both shipped HTTP entrypoints."""
import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'qa/screenshots'
OUT.mkdir(exist_ok=True)
checks = []


def check(name, condition):
    checks.append({'test': name, 'pass': bool(condition)})
    print(('PASS ' if condition else 'FAIL ') + name, flush=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path, args=['--no-sandbox'])
        for entry in ('index.html', 'compute_atlas.html'):
            page = browser.new_page(viewport={'width': 1366, 'height': 768})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))

            def ready():
                page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')

            def go(query=''):
                page.goto(base + entry + query)
                ready()

            go()
            check(entry + ' regional totals reconstruct the raw comparable target models', page.evaluate('''(()=>{
                const scope=spatialScope(0,spatialDefaultSite()),rows=workspaceRegionalRows(scope);
                const raw=D.sites.filter(s=>Number.isFinite(s.lat)&&Number.isFinite(s.lon));
                const comparable=raw.filter(s=>['archive','reviewed-model'].includes(s.review)&&typeof s.target?.it_mw==='number'&&Number.isFinite(s.target.it_mw));
                return rows.reduce((n,r)=>n+r.count,0)===raw.length && rows.reduce((n,r)=>n+r.known,0)===comparable.length && Math.abs(rows.reduce((n,r)=>n+r.mw,0)-comparable.reduce((n,s)=>n+s.target.it_mw,0))<1e-6;
            })()'''))
            asia = page.locator('[data-workspace-region="Asia"]')
            check(entry + ' unknown-only Asia is visible without invented zero GW', 'Not quantified' in asia.inner_text() and '0 quantified · 8 unquantified' in asia.inner_text() and '0.000 GW' not in asia.inner_text())
            check(entry + ' metrics span map and rail and fit a short desktop', page.locator('.atlas-kpi-grid').evaluate('e=>{const r=e.getBoundingClientRect(),a=document.querySelector(".atlas-spatial-layout").getBoundingClientRect();return r.bottom<=innerHeight&&Math.abs(r.width-a.width)<2}'))
            page.screenshot(path=str(OUT / f'{entry}-landing-short.png'), full_page=True)
            world_url = page.url
            europe = page.locator('[data-workspace-region="Europe"]')
            europe.focus()
            page.keyboard.press('Enter')
            page.wait_for_function('state.spatialRegion==="Europe"&&state.spatialLevel===1')
            check(entry + ' keyboard entry opens exact multi-country Europe', page.evaluate('(()=>{const s=spatialScope(1,spatialDefaultSite());return s.label==="Europe"&&s.sites.length===2&&new Set(s.sites.map(s=>s.country)).size===2&&s.sites.every(s=>["United Kingdom","Norway"].includes(s.country))})()'))
            check(entry + ' Europe camera faces Europe', page.evaluate('Math.abs(globe.lat-51)<1&&Math.abs(globe.lon-12)<1'))
            check(entry + ' absent imagery offers project evidence without unrelated preview', page.locator('.workspace-campus-preview img').count() == 0 and 'imagery unavailable' in page.locator('.workspace-campus-preview').inner_text())
            page.reload()
            ready()
            check(entry + ' reload retains the exact regional scope', page.evaluate('state.spatialRegion==="Europe"&&spatialScope(1,spatialDefaultSite()).sites.length===2'))
            # An explicit camera in a shared regional URL takes priority over default framing.
            go('#overview?scale=continent&region=Europe&camera=g,44,18,2')
            check(entry + ' explicit regional camera takes precedence', page.evaluate('globe.lat===44&&globe.lon===18&&globe.zoom===2'))
            page.locator('[data-workspace-share]').click()
            shared = page.locator('#workspace-share-url').input_value()
            check(entry + ' sharing preserves region and camera', 'region=Europe' in shared and 'camera=g%2C44%2C18%2C2' in shared)
            page.locator('[data-action="close-drawer"]').click()
            # Return to an unmodified navigation history before checking Back/Forward.
            go()
            page.locator('[data-workspace-region="Europe"]').click()
            page.wait_for_function('state.spatialRegion==="Europe"')
            page.go_back()
            page.wait_for_function('!state.spatialRegion&&state.spatialLevel===0')
            check(entry + ' Back restores global records', page.evaluate('spatialScope(0,spatialDefaultSite()).sites.length===75'))
            page.go_forward()
            page.wait_for_function('state.spatialRegion==="Europe"')
            page.locator('[data-workspace-clear="region"]').click()
            check(entry + ' region chip returns to global scope', page.evaluate('!state.spatialRegion&&spatialScope(state.spatialLevel,spatialDefaultSite()).sites.length===75'))
            go('#overview?scale=world&company=coreweave')
            link = page.locator('[data-workspace-region="North America"]').get_attribute('href')
            check(entry + ' regional entry preserves active refinements', 'company=coreweave' in link)
            page.locator('[data-workspace-region="North America"]').click()
            page.wait_for_function('state.spatialRegion==="North America"')
            check(entry + ' filtered regional records retain the selected company', page.evaluate('state.filter.company==="coreweave"&&spatialScope(1,spatialDefaultSite()).sites.every(s=>s.company_ids.includes("coreweave")||primaryRelationships(s).some(r=>r.company_id==="coreweave"))'))
            go('#overview?scale=continent&region=Europe&q=no-such-project-xyz')
            check(entry + ' empty regional scope stays explicit without unrelated projects', page.evaluate('spatialScope(1,spatialDefaultSite()).sites.length===0') and 'No mapped research projects' in page.locator('.workspace-region-ranks').inner_text() and page.locator('.workspace-campus-preview').count() == 0)
            go()
            preview = page.locator('[data-workspace-preview]')
            scene = preview.get_attribute('data-workspace-preview')
            check(entry + ' physical preview exposes its historical date', '2022-09-05' in preview.inner_text())
            preview.click()
            page.wait_for_function('state.spatialLevel===4&&globe instanceof CampusScene')
            check(entry + ' preview opens the exact accepted historical scene', page.evaluate('campusScene().id') == scene and 'imageversion=' in page.url)
            page.go_back()
            page.wait_for_function('state.spatialLevel===0')
            for width, height in ((1440, 900), (1024, 768), (768, 1024), (390, 844), (320, 844)):
                page.set_viewport_size({'width': width, 'height': height})
                page.wait_for_function('document.documentElement.scrollWidth<=innerWidth+1')
                check(entry + f' {width}px layout fits without page overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                if width >= 1100:
                    check(entry + f' {width}px metrics fit viewport', page.locator('.atlas-kpi-grid').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
                elif width > 640:
                    check(entry + f' {width}px map stays useful and precedes metrics then analysis', page.evaluate('(()=>{const m=document.querySelector(".atlas-map-column").getBoundingClientRect(),k=document.querySelector(".workspace-map-lower").getBoundingClientRect(),r=document.querySelector(".atlas-spatial-rail").getBoundingClientRect();return m.width>500&&m.bottom<=k.top+2&&k.bottom<=r.top+2})()'))
                else:
                    check(entry + f' {width}px metrics immediately follow the map', page.evaluate('(()=>{const k=document.querySelector(".workspace-map-lower").getBoundingClientRect(),r=document.querySelector(".atlas-spatial-rail").getBoundingClientRect();return k.bottom<=r.top+2})()'))
                page.screenshot(path=str(OUT / f'{entry}-landing-{width}.png'), full_page=True)
            check(entry + ' no uncaught browser errors', not errors)
            page.close()
        browser.close()
finally:
    server.shutdown()
result = {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}
(ROOT / 'qa/landing_results.json').write_text(json.dumps(result, indent=2))
print(f"{result['passed']}/{result['total']} passed")
raise SystemExit(result['passed'] != result['total'])
