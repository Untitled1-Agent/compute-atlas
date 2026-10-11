"""User journeys that were missing from the catalog and campus experience."""
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
def check(name, value):
    checks.append({'test': name, 'pass': bool(value)})
    print(('PASS ' if value else 'FAIL ') + name, flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path, args=['--no-sandbox'])
        for entry in ['index.html', 'compute_atlas.html']:
            page = browser.new_page(viewport={'width':1440,'height':1000})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry)
            page.wait_for_function('document.documentElement.classList.contains("research-ready")')
            page.wait_for_timeout(300)
            check(entry+' worldwide landing', page.evaluate('ATLAS.state.view')=='catalog')
            page.screenshot(path=str(OUT/(entry+'-experience-world.png')))
            check(entry+' KPIs visible in desktop overview',page.locator('#catalog-stats').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
            page.set_viewport_size({'width':1366,'height':768})
            page.wait_for_timeout(150)
            check(entry+' KPIs visible on short desktop',page.locator('#catalog-stats').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
            page.screenshot(path=str(OUT/(entry+'-experience-short-desktop.png')))
            page.set_viewport_size({'width':1440,'height':1000})
            page.locator('[data-catalog-region="Europe"]').first.click()
            page.locator('#catalog-query').fill('Equinix')
            page.wait_for_timeout(250)
            page.locator('#catalog-kind').select_option('building')
            page.locator('#catalog-country').select_option('Germany')
            check(entry+' country retains query and geometry filter',page.locator('#catalog-query').input_value()=='Equinix' and page.locator('#catalog-kind').input_value()=='building')
            page.locator('[data-catalog-reset]').click()
            page.locator('[data-catalog-page="1"]').click()
            first=page.locator('.catalog-result').first.inner_text()
            page.locator('#globe-canvas').scroll_into_view_if_needed()
            page.locator('#globe-canvas').focus()
            page.keyboard.press('ArrowRight');page.keyboard.press('+')
            page.wait_for_timeout(350)
            camera=page.evaluate('catalogCameraToken(catalogState.camera)')
            page.locator('.catalog-result').first.click()
            check(entry+' opening feature preserves results page',page.evaluate('ATLAS.catalog.state.page')==1)
            page.locator('[data-catalog-back]').click()
            check(entry+' back preserves result page',page.locator('.catalog-result').first.inner_text()==first)
            page.wait_for_timeout(300)
            check(entry+' back preserves map camera',page.evaluate('catalogCameraToken(catalogState.camera)')==camera)
            print('Reloading',page.url,flush=True)
            page.reload()
            try: page.wait_for_function('document.documentElement.classList.contains("research-ready")')
            except Exception:
                print('Boot failure:',page.locator('#content').inner_text()[:700],errors,flush=True)
                raise
            page.wait_for_timeout(300)
            check(entry+' reload preserves page and camera',page.locator('.catalog-result').first.inner_text()==first and page.evaluate('catalogCameraToken(catalogState.camera)')==camera)
            catalog_url=page.url
            for dismissal in ['Escape','scrim']:
                page.evaluate("ATLAS.openDrawer('help')")
                if dismissal=='Escape': page.keyboard.press('Escape')
                else: page.locator('#drawer-scrim').click(position={'x':10,'y':100})
                check(entry+f' {dismissal} restores complete catalog bookmark',page.url==catalog_url)
            for level in range(4):
                page.locator(f'[data-catalog-scale="{level}"]').click();page.wait_for_timeout(250)
                check(entry+f' geographic scale {level}',page.locator(f'[data-catalog-scale="{level}"]').get_attribute('aria-pressed')=='true')
            page.locator('[data-catalog-scale="4"]').click()
            check(entry+' campus requires an explicit source selection',page.locator('.catalog-result').first.evaluate('e=>e===document.activeElement'))
            page.evaluate("ATLAS.catalog.select('osm-way-1121454055')")
            page.locator('[data-catalog-scale="4"]').click()
            check(entry+' campus enables sourced context without merging identities',page.locator('#scene-context').is_checked())
            page.reload();page.wait_for_function('document.documentElement.classList.contains("research-ready")')
            check(entry+' campus selection survives reload',page.locator('#scene-context').is_checked())
            page.locator('[data-catalog-scale="5"]').click()
            check(entry+' facility focuses the selected source',not page.locator('#scene-context').is_checked())
            page.locator('[data-catalog-tool="expand"]').click();page.keyboard.press('Escape')
            check(entry+' Escape closes expanded geometry',page.locator('.atlas-map-expanded').count()==0)
            page.evaluate("ATLAS.navigate('overview');ATLAS.spatial.setLevel(4)")
            check(entry+' campus exposes dated project evidence and section navigation',page.locator('.atlas-campus-disclosure').count()>0 and page.locator('.atlas-project-shortcuts button').count()==6)
            page.screenshot(path=str(OUT/(entry+'-experience-campus.png')))
            page.locator('.atlas-project-shortcuts [data-research-topic-target="energy"]').click()
            check(entry+' energy shortcut focuses full cited claims',page.locator('#drawer [data-research-topic="energy"]').evaluate('e=>e===document.activeElement'))
            page.locator('[data-action="close-drawer"]').click()
            for level in range(6):
                page.evaluate(f'ATLAS.spatial.setLevel({level})');page.wait_for_timeout(100)
                page.screenshot(path=str(OUT/(entry+f'-experience-scale-{level}.png')))
            for width in [390,320]:
                page.set_viewport_size({'width':width,'height':844})
                page.evaluate("ATLAS.navigate('catalog');ATLAS.catalog.go({feature:null});catalogGeo('All')")
                page.wait_for_timeout(300)
                check(entry+f' mobile {width} no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                check(entry+f' mobile {width} closed nav cannot cover content',page.locator('#sidebar').evaluate('e=>getComputedStyle(e).visibility==="hidden"&&e.inert'))
                page.screenshot(path=str(OUT/(entry+f'-experience-mobile-{width}.png')))
                page.locator('.mobile-menu').click()
                check(entry+f' mobile {width} navigation opens accessibly',page.locator('#sidebar').evaluate('e=>!e.inert') and page.locator('.mobile-menu').get_attribute('aria-expanded')=='true')
                page.keyboard.press('Escape')
            check(entry+' no JavaScript errors',not errors)
            page.close()
        browser.close()
finally:
    server.shutdown()
result={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/experience_results.json').write_text(json.dumps(result,indent=2))
print(f"{result['passed']}/{result['total']} passed")
raise SystemExit(result['passed']!=result['total'])
