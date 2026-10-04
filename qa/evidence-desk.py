"""Read-only analyst workflow and fresh screenshots, both HTTP entrypoints in CI.

--in-memory uses real Chromium rendering of embedded HTML only. It never claims
HTTP transport, server publication updates, or persistent-origin coverage.
"""
from __future__ import annotations
import argparse
import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
checks=[]
def check(name,condition,detail=None):
    checks.append({'test':name,'pass':bool(condition),'detail':detail})
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_): pass
server=None
if not args.in_memory:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/' if server else ''
try:
    with sync_playwright() as p:
        exe=shutil.which('chromium') or shutil.which('chromium-browser')
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for entry in (('compute_atlas.html',) if args.in_memory else ('index.html','compute_atlas.html')):
            label=Path(entry).stem
            page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True)
            page.set_default_timeout(8000);errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
            if args.in_memory: page.set_content((ROOT/entry).read_text(),wait_until='load')
            else: check(entry+' HTTP response',page.goto(base+entry,wait_until='load').status==200)
            page.wait_for_function('window.ATLAS?.evidence && window.ATLAS?.publication')
            page.evaluate("ATLAS.navigate('globe');ATLAS.spatial.select('coreweave-ellendale');ATLAS.spatial.setLevel(5)")
            check(entry+' October commissioned subtotal is 250 MW','250 MW' in page.locator('.atlas-feature-number').inner_text())
            check(entry+' historical July subtotal absent from headline cards','175' not in page.locator('.atlas-evidence-schematic').inner_text())
            page.screenshot(path=str(OUT/f'{label}-ellendale-desktop.png'),full_page=True)
            page.locator('[data-atlas-action="evidence-desk"]').first.click()
            check(entry+' desk has five current records',page.locator('.atlas-evidence-record').count()==5)
            page.locator('[data-evidence-filter="observations"]').click()
            check(entry+' quantities preserve distinct scopes',set(page.locator('.atlas-claim-scope').all_inner_texts())=={'Campus commissioned subtotal','Building 2 completed','Full campus buildout'})
            page.locator('[data-evidence-filter="history"]').click()
            check(entry+' July retained as earlier revision','175' in page.locator('#atlas-desk-records').inner_text() and 'not current' in page.locator('#atlas-desk-records').inner_text())
            page.screenshot(path=str(OUT/f'{label}-ellendale-history.png'))
            page.locator('#atlas-desk-records [data-atlas-action="source"]').click()
            check(entry+' old source exposes historical claim','Retained revision history' in page.locator('#drawer-content').inner_text() and '175' in page.locator('#drawer-content').inner_text())
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' drawer back restores history category',page.locator('[data-evidence-filter="history"]').get_attribute('aria-pressed')=='true')
            page.locator('[data-evidence-filter="all"]').click()
            page.locator('#atlas-evidence-query').fill('commissioned')
            check(entry+' claim search filters without losing input focus',page.locator('.atlas-evidence-record').count()==1 and page.locator('#atlas-evidence-query').evaluate('el=>document.activeElement===el'))
            page.locator('#atlas-evidence-query').fill('zzzz_missing')
            check(entry+' empty evidence search is not zero capacity','not a zero capacity' in page.locator('.atlas-desk-empty').inner_text())
            page.locator('#atlas-evidence-query').fill('')
            with page.expect_download() as transfer:
                page.locator('.atlas-evidence-desk [data-atlas-action="export"]').click()
            exported=json.loads(Path(transfer.value.path()).read_text())
            check(entry+' cited export includes current and prior sources',{'P13','P14'}.issubset({s['id'] for s in exported['primary_sources']}))
            check(entry+' cited export separates current 250 from prior 175',any(o['value']==250 for o in exported['primary_observations']) and exported['revision_history']['observations'][0]['value']==175)
            page.locator('[data-action="close-drawer"]').click()
            page.evaluate("ATLAS.evidence.open('hut8-river-bend')")
            check(entry+' utility allocation is not labeled IT','Utility supply capacity' in page.locator('[data-claim-id="riverbend-utility"]').inner_text())
            check(entry+' lease value is not construction cost','USD billion' in page.locator('[data-claim-id="riverbend-lease-value"]').inner_text() and 'not construction cost' in page.locator('[data-claim-id="riverbend-lease-value"]').inner_text())
            page.evaluate("ATLAS.evidence.open('meta-prometheus')")
            check(entry+' primary unknown remains unquantified','Not quantified' in page.locator('[data-claim-id="prometheus-it-undisclosed"]').inner_text())
            page.evaluate("ATLAS.evidence.open('sensetime-lingang-aidc')")
            check(entry+' PUE precision and inequality retained','< 1.28' in page.locator('[data-claim-id="lingang-reported-pue"] h3').inner_text())
            check(entry+' native annual energy is not converted to MW','3,000,000 kWh/year' in page.locator('[data-claim-id="lingang-energy-saving"] h3').inner_text())
            page.set_viewport_size({'width':390,'height':844})
            check(entry+' mobile desk has no horizontal overflow',page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
            page.wait_for_timeout(2800)  # Allow the export toast and drawer transition to settle.
            check(entry+' mobile research surface is fully opaque',page.locator('#drawer').evaluate("el=>getComputedStyle(el).opacity==='1' && getComputedStyle(el).backgroundColor==='rgb(13, 23, 36)'"))
            page.screenshot(path=str(OUT/f'{label}-native-evidence-mobile.png'))
            page.locator('[data-claim-id="lingang-reported-pue"]').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/f'{label}-native-quantity-mobile.png'))
            page.locator('[data-action="close-drawer"]').click()
            page.locator('.atlas-filter-toggle').click()
            page.locator('#atlas-map-query').fill('Ellendale');page.wait_for_timeout(250)
            check(entry+' mobile refinement retains focus and open state',page.locator('.atlas-filter-panel').get_attribute('open') is not None and page.locator('#atlas-map-query').evaluate('el=>document.activeElement===el'))
            page.locator('#atlas-map-query').press('Escape')
            check(entry+' Escape dismisses refinement with focus restored',page.locator('.atlas-filter-toggle').evaluate('el=>document.activeElement===el') and page.locator('.atlas-filter-panel').get_attribute('open') is None)
            page.screenshot(path=str(OUT/f'{label}-ellendale-mobile.png'),full_page=True)
            check(entry+' mobile facility has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            # Exercise every archive site with the new read-only renderer, including
            # sites with no additional reviewed evidence. No external APIs or mock facts.
            stats=page.evaluate("""() => {let bad=[];for(const s of ATLAS.data.sites){const rows=ATLAS.evidence.rows(s);const out=ATLAS.evidence.export(s);if(!Array.isArray(rows)||out.archive.id!==s.id)bad.push(s.id);}return bad;}""")
            check(entry+' all 79 sites support evidence and cited export',not stats,stats)
            check(entry+' no uncaught browser errors',not errors,errors)
            check(entry+' static evidence desk makes no external requests',not external,external)
            page.close()
        browser.close()
finally:
    if server: server.shutdown();server.server_close()
report={'execution':'embedded Chromium only' if args.in_memory else 'real HTTP hosted and standalone Chromium','passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/evidence_desk_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
