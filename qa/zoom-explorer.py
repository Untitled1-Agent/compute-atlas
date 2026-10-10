"""Six-scale browser contracts, evidence boundaries, mobile and screenshot review.

Default: real HTTP, both entrypoints. --in-memory is explicitly for environments
that prohibit browser navigation. It tests only the embedded build and never
claims HTTP or persistent-origin coverage. The real HTTP mode is mandatory in CI.
"""
from __future__ import annotations
import argparse
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
parser = argparse.ArgumentParser()
parser.add_argument('--in-memory', action='store_true')
ARGS = parser.parse_args()
CHECKS = []


def check(name, ok, detail=None):
    CHECKS.append({'test': name, 'pass': bool(ok), 'detail': detail})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok:
        print(detail, flush=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


server = None
if not ARGS.in_memory:
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/' if server else ''
try:
    with sync_playwright() as p:
        exe = shutil.which('chromium') or shutil.which('chromium-browser')
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **({'executable_path': exe} if exe else {}))
        for entry in (('compute_atlas.html',) if ARGS.in_memory else ('index.html', 'compute_atlas.html')):
            page = browser.new_page(viewport={'width': 1440, 'height': 1080}, accept_downloads=True)
            page.set_default_timeout(8000)
            errors, external, bad_responses, requests = [], [], [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: requests.append(r.url))
            page.on('request', lambda r: external.append(r.url) if r.url.startswith(('http://', 'https://')) and not r.url.startswith(base or 'about:') else None)
            page.on('response', lambda r: bad_responses.append((r.status, r.url)) if r.status >= 400 else None)
            if ARGS.in_memory:
                page.set_content((ROOT / entry).read_text(), wait_until='load')
            else:
                response = page.goto(base + entry, wait_until='load', timeout=30000)
                check(entry + ' returns real HTTP 200', response.status == 200)
            page.wait_for_function('window.ATLAS && ATLAS.spatial && document.documentElement.classList.contains("catalog-ready")')
            page.evaluate("ATLAS.navigate('globe')")
            labels = page.locator('.atlas-scale-step b').all_inner_texts()
            check(entry + ' exposes six named scales', labels == ['World', 'Continent', 'Region', 'Metro', 'Campus', 'Facility'], labels)
            check(entry + ' has five attributed geographic layer manifests', page.evaluate('ATLAS.context.sources.length') == 5)
            for level, label in enumerate(labels):
                page.locator(f'[data-spatial-action="stage"][data-id="{level}"]').click()
                page.wait_for_timeout(160)
                check(entry + ' selects ' + label, page.evaluate('ATLAS.state.spatialLevel') == level)
                check(entry + ' ' + label + ' has evidence rail', page.locator('.atlas-spatial-rail .atlas-insight-card').count() >= 2)
                page.screenshot(path=str(OUT / f'{Path(entry).stem}-{level+1:02d}-{label.lower()}.png'), full_page=True)
            page.locator('[data-spatial-action="stage"][data-id="0"]').click()
            page.wait_for_timeout(160)
            check(entry + ' uses actual mapped records', page.locator('.atlas-map-marker').count() == 75)
            marker = page.locator('.atlas-map-marker:visible').first
            selected = marker.get_attribute('data-id')
            marker.click()
            check(entry + ' real marker selects and drills', page.evaluate('({level:ATLAS.state.spatialLevel,id:ATLAS.state.spatialSelected})') == {'level': 1, 'id': selected})
            page.locator('[data-spatial-action="phase"][data-id="target"]').click()
            check(entry + ' target toggle retains selection', page.evaluate('({phase:ATLAS.state.spatialPhase,id:ATLAS.state.spatialSelected})') == {'phase': 'target', 'id': selected})
            page.keyboard.press('+')
            check(entry + ' keyboard plus advances scale', page.evaluate('ATLAS.state.spatialLevel') == 2)
            page.keyboard.press('-')
            check(entry + ' keyboard minus reverses scale', page.evaluate('ATLAS.state.spatialLevel') == 1)
            page.locator('.atlas-scale-step.active').press('End')
            check(entry + ' stage-strip End reaches facility', page.evaluate('ATLAS.state.spatialLevel') == 5)
            page.locator('.atlas-scale-step.active').press('Home')
            check(entry + ' stage-strip Home reaches world', page.evaluate('ATLAS.state.spatialLevel') == 0)
            page.locator('#globe-canvas').hover(position={'x': 300, 'y': 300})
            before_zoom=page.evaluate('ATLAS.getGlobe().zoom')
            page.mouse.wheel(0, -120)
            page.wait_for_timeout(200)
            check(entry + ' wheel zooms continuously without replacing the map', page.evaluate('ATLAS.getGlobe().zoom') > before_zoom and page.evaluate('ATLAS.state.spatialLevel') == 0)
            for _ in range(5):
                page.mouse.wheel(0,-120);page.wait_for_timeout(60)
            check(entry + ' continued wheel zoom advances scale',page.evaluate('ATLAS.state.spatialLevel') == 1)
            page.locator('[data-spatial-action="stage"][data-id="0"]').click()
            page.locator('[data-atlas-action="fly"][data-id="asia"]').click()
            page.wait_for_function('Math.abs(ATLAS.getGlobe().lon-105)<2')
            before = page.evaluate('ATLAS.getGlobe().lon')
            page.locator('[data-spatial-action="phase"][data-id="snapshot"]').click()
            page.wait_for_timeout(100)
            check(entry + ' phase toggle preserves map camera', abs(page.evaluate('ATLAS.getGlobe().lon') - before) < 2)
            page.locator('.atlas-filter-toggle').click()
            check(entry + ' filter panel opens accessibly', page.locator('.atlas-filter-panel').get_attribute('open') is not None)
            page.locator('#atlas-country-filter').select_option('China')
            check(entry + ' country filter is visible and scopes records', page.evaluate("ATLAS.spatial.scope().sites.every(s=>s.country==='China')") and page.evaluate('ATLAS.spatial.scope().sites.length') == 7)
            page.locator('#atlas-evidence-filter').select_option('native')
            check(entry + ' native filter excludes comparable model records', page.evaluate("ATLAS.spatial.scope().sites.every(s=>!['archive','reviewed-model'].includes(s.review))"))
            check(entry + ' unknown IT is not rendered as a zero aggregate', '—' in page.locator('.atlas-kpi-grid').inner_text())
            page.locator('[data-atlas-action="clear-filters"]').click()
            page.locator('#atlas-map-query').fill('zzzz_no_matching_facility')
            page.wait_for_timeout(400)
            check(entry + ' empty search has explicit result state', page.evaluate('ATLAS.spatial.scope().sites.length') == 0 and 'No records match' in page.locator('.atlas-record-list').text_content())
            page.locator('[data-atlas-action="clear-filters"]').click()
            page.evaluate("ATLAS.spatial.select('anthropic-fluidstack-lake-mariner');ATLAS.spatial.setLevel(5)")
            check(entry + ' Lake Mariner operating capacity excludes historical and construction totals', '102 MW' in page.locator('.atlas-feature-number').inner_text())
            check(entry + ' Lake Mariner phases retain operating and construction scopes', '336 MW' in page.locator('.atlas-evidence-schematic').inner_text() and 'Historical snapshot' in page.locator('.atlas-power-row').last.inner_text())
            page.evaluate("ATLAS.spatial.select('microsoft-narvik');ATLAS.spatial.setLevel(5)")
            check(entry + ' Narvik unspecified design is not relabeled critical IT', '230 MW' not in ' '.join(page.locator('.atlas-power-row').all_inner_texts()))
            page.locator('[data-atlas-action="source"][data-id="P12"]').first.click()
            check(entry + ' undated source is explicitly identified', 'Publication date not stated' in page.locator('#drawer-content').inner_text())
            page.locator('[data-action="close-drawer"]').click()
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(5)")
            check(entry + ' campus never aggregates neighboring sites', page.evaluate('ATLAS.spatial.scope().sites.map(s=>s.id)') == ['coreweave-helios'])
            text = page.locator('.atlas-evidence-schematic').inner_text()
            check(entry + ' schematic cannot be mistaken for a survey', 'NOT A PARCEL / BUILDING SURVEY' in text and 'not additive' in text)
            check(entry + ' delivered and contracted IT are separate', '133 MW' in text and '526 MW' in text)
            check(entry + ' approved gross power never enters IT ladder', '1,630' not in ' '.join(page.locator('.atlas-power-row').all_inner_texts()))
            check(entry + ' original independent model remains 132 MW', page.evaluate("ATLAS.data.sites.find(s=>s.id==='coreweave-helios').snapshot.it_mw") == 132)
            with page.expect_download() as info:
                page.locator('.atlas-insight-stack [data-atlas-action="export"]').click()
            dossier = json.loads(Path(info.value.path()).read_text())
            powers = {(o['value'], o['boundary'], o['status']) for o in dossier['primary_observations'] if o['metric'] == 'power'}
            check(entry + ' export preserves distinct measurement boundaries', {(133, 'critical_it', 'delivered'), (526, 'critical_it', 'contracted'), (1630, 'gross_facility', 'approved')}.issubset(powers), sorted(powers))
            page.locator('[data-atlas-action="source"][data-id="P01"]').first.click()
            check(entry + ' source opens original disclosure with dates', page.locator('#drawer-content a[target="_blank"]').first.get_attribute('href').startswith('https://www.galaxy.com/') and '2026-07-06' in page.locator('#drawer-content').inner_text())
            page.locator('[data-action="close-drawer"]').click()
            page.locator('#atlas-local-note').fill('Verify delivered critical IT, not gross power.')
            page.locator('.atlas-note-footer [data-action="favorite"]').click()
            check(entry + ' research shelf button updates immediately', 'On research shelf' in page.locator('.atlas-note-footer button').inner_text())
            page.evaluate("ATLAS.navigate('watchlist')")
            check(entry + ' local note reaches research shelf', 'Verify delivered critical IT' in page.locator('#content').inner_text())
            page.evaluate("ATLAS.navigate('globe')")
            if not ARGS.in_memory:
                page.reload(wait_until='load')
                page.wait_for_function('window.ATLAS && ATLAS.spatial')
                check(entry + ' deep link restores selected facility and level', page.evaluate('({id:ATLAS.state.spatialSelected,level:ATLAS.state.spatialLevel})') == {'id': 'coreweave-helios', 'level': 5})
                check(entry + ' private note persists after HTTP reload', page.locator('#atlas-local-note').input_value().startswith('Verify delivered'))
                page.locator('[data-spatial-action="stage"][data-id="3"]').click()
                page.locator('[data-spatial-action="stage"][data-id="4"]').click()
                page.go_back()
                page.wait_for_function('ATLAS.state.spatialLevel===3')
                check(entry + ' browser back restores prior scale', page.evaluate('ATLAS.state.spatialLevel') == 3)
                page.go_forward()
                page.wait_for_function('ATLAS.state.spatialLevel===4')
                check(entry + ' browser forward restores campus', page.evaluate('ATLAS.state.spatialLevel') == 4)
            for level in range(6):
                page.set_viewport_size({'width': 390, 'height': 844})
                page.evaluate('(n)=>ATLAS.spatial.setLevel(n)', level)
                page.wait_for_timeout(120)
                check(entry + ' mobile ' + labels[level] + ' keeps closed navigation hidden', page.locator('#sidebar').evaluate("el=>getComputedStyle(el).visibility==='hidden' && el.inert"))
                check(entry + ' mobile ' + labels[level] + ' has no page-wide overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                if level in (0, 5):
                    page.screenshot(path=str(OUT / f'{Path(entry).stem}-mobile-{labels[level].lower()}.png'), full_page=True)
            page.locator('[data-atlas-action="monitor"]').click()
            check(entry + ' static monitor does not pretend a worker is running', 'self-contained publication' in page.locator('#drawer-content').inner_text() and 'No claim is made that a background job is running' in page.locator('#drawer-content').inner_text())
            check(entry + ' has zero JavaScript exceptions', not errors, errors)
            check(entry + ' has zero external requests', not external, external)
            check(entry + ' has zero HTTP errors', not bad_responses, bad_responses)
            if entry == 'compute_atlas.html':
                check(entry + ' is self-contained', not requests if ARGS.in_memory else all(url.split('#')[0]==base+entry for url in requests), requests)
            page.close()
        browser.close()
finally:
    if server:
        server.shutdown(); server.server_close()
result = {'execution': 'embedded Chromium; HTTP and persistent-origin tests not run' if ARGS.in_memory else 'real Chromium over HTTP; both entrypoints', 'passed': sum(x['pass'] for x in CHECKS), 'total': len(CHECKS), 'checks': CHECKS}
(ROOT / 'qa/zoom_explorer_results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
raise SystemExit(0 if result['passed'] == result['total'] else 1)
