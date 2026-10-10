"""Coverage and disclosure interaction tests on both HTTP entrypoints in CI.

--in-memory renders the exact standalone in real Chromium, but does not test
HTTP, persistent origin storage, or deployment. Source candidates never become
capacity fixtures. Local mutations used to check rendering are restored.
"""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/screenshots';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--in-memory',action='store_true');args=parser.parse_args()
checks=[]
def check(name,passed,detail=None):
    checks.append({'test':name,'pass':bool(passed),'detail':detail})
    print(('PASS ' if passed else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
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
            label=Path(entry).stem;page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True)
            page.set_default_timeout(10000);errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
            if args.in_memory:page.set_content((ROOT/entry).read_text(),wait_until='load')
            else:check(entry+' HTTP response',page.goto(base+entry,wait_until='load').status==200)
            page.wait_for_function('window.ATLAS?.coverage',timeout=30000);page.wait_for_function('document.documentElement.classList.contains("research-ready")',timeout=30000)
            page.evaluate("ATLAS.navigate('overview')")
            check(entry+' scoped primary-review KPI is an actual button',page.locator('.atlas-kpi-grid button[data-coverage-open]').count()==1)
            page.screenshot(path=str(OUT/f'{label}-coverage-world.png'),full_page=True)
            page.locator('.atlas-kpi-grid button[data-coverage-open]').click()
            metrics=page.evaluate('ATLAS.coverage.metrics()')
            check(entry+' coverage counts do not add research candidates',metrics=={'total':79,'reviewed':79,'mapped':75,'unreviewed':0,'countries':6,'quantities':47,'unknown':2,'candidates':8},metrics)
            check(entry+' geography overview is a collection denominator','not total facilities, market share' in page.locator('.atlas-coverage-boundary').inner_text())
            check(entry+' all geographic coverage categories are represented',page.locator('.atlas-coverage-geographies article').count()==7)
            page.screenshot(path=str(OUT/f'{label}-coverage-desktop.png'))
            page.locator('[data-coverage-country="Indonesia"]').click()
            check(entry+' absent review is not zero installed capacity','No result is not zero capacity' in page.locator('.atlas-coverage-empty').inner_text())
            page.locator('[data-coverage-action="reset"]').click()
            check(entry+' reviewed disclosures paginate ten per page',page.locator('.atlas-coverage-disclosure').count()==10)
            page.locator('[data-coverage-page="next"]').click()
            check(entry+' pagination preserves keyboard focus',page.locator('[data-coverage-page="next"]').evaluate('el=>document.activeElement===el') and page.evaluate('atlasCoverageState.offset')==10)
            page.locator('[data-coverage-filter="status"]').select_option('not_disclosed')
            check(entry+' unknown observations render as undisclosed not zero',page.locator('.atlas-coverage-disclosure').count()==2 and page.locator('.atlas-coverage-value strong').all_inner_texts()==['Not disclosed','Not disclosed'])
            with page.expect_download() as transfer:page.locator('[data-coverage-action="export"]').click()
            export=json.loads(Path(transfer.value.path()).read_text())
            check(entry+' cited JSON preserves nulls, boundaries and primary URLs',len(export['rows'])==2 and all(row['value'] is None and row['boundary']=='critical_it' and row['source']['url'].startswith('https://') for row in export['rows']))
            page.locator('[data-coverage-action="reset"]').click()
            page.locator('[data-coverage-filter="country"]').select_option('China')
            units=set(page.locator('.atlas-coverage-value>span').all_inner_texts())
            check(entry+' China-native disclosures retain precision, energy and land units',units=={'ratio','kWh/year','GJ','PFLOPS FP16','MW','ha','mu'},sorted(units))
            check(entry+' strict PUE comparison is retained','< 1.28' in page.locator('.atlas-coverage-value strong').all_inner_texts())
            rows=page.evaluate('ATLAS.coverage.export().rows')
            check(entry+' energy, design PUE and generation retain distinct boundaries', {'annual_pue','reported_energy_savings','design_pue','generation'}.issubset({row['boundary'] for row in rows}) and any(row.get('comparison')=='lt' for row in rows) and all(row['boundary']=='generation' and row['applies_to']=='context' for row in rows if row['unit']=='MW'))
            check(entry+' wider-context quantities are visibly labeled',page.locator('.atlas-coverage-context-label').count()==sum(row.get('applies_to')=='context' for row in rows))
            page.set_viewport_size({'width':390,'height':844});page.locator('#drawer').evaluate('el=>el.scrollTop=480')
            page.screenshot(path=str(OUT/f'{label}-coverage-native-mobile.png'))
            check(entry+' disclosure filters have no mobile overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
            page.set_viewport_size({'width':1440,'height':1080})
            page.locator('[data-coverage-action="reset"]').click()
            page.locator('#atlas-coverage-query').fill('Ellendale')
            rows=page.evaluate('ATLAS.coverage.export().rows')
            check(entry+' current revision excludes historical 175 MW',len(rows)==3 and any(row['value']==250 for row in rows) and not any(row['value']==175 for row in rows))
            check(entry+' site-level scopes are visible, not mechanically summed',any('Included within' in row.get('qualifier','') for row in rows) and 'no cross-boundary total' in page.locator('#atlas-coverage-count').inner_text())
            page.evaluate("document.getElementById('atlas-coverage-query').setSelectionRange(2,5);updateMonitorLabel()")
            check(entry+' status refresh retains query focus and caret',page.locator('#atlas-coverage-query').evaluate('el=>document.activeElement===el&&el.selectionStart===2&&el.selectionEnd===5') and page.locator('#atlas-coverage-query').input_value()=='Ellendale')
            page.screenshot(path=str(OUT/f'{label}-coverage-disclosures.png'))
            page.locator('.atlas-coverage-disclosure [data-atlas-action="source"]').first.click()
            check(entry+' disclosure source opens original provenance','Applied Digital' in page.locator('#drawer-content').inner_text())
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' source back preserves disclosure filters',page.locator('#atlas-coverage-query').input_value()=='Ellendale' and page.locator('.atlas-coverage-disclosure').count()==3)
            page.locator('#atlas-coverage-query').fill('<script>window.coverageXSS=true</script>')
            check(entry+' search cannot inject markup',page.locator('.atlas-coverage-empty').count()==1 and page.evaluate('window.coverageXSS!==true'))
            page.locator('[data-coverage-tab="candidates"]').click()
            check(entry+' eight candidates stay explicitly unmapped',page.locator('.atlas-coverage-candidate').count()==8 and 'excluded from mapped project counts' in page.locator('.atlas-coverage-boundary').inner_text())
            check(entry+' candidate scopes expose common measurement traps',all(text in page.locator('.atlas-coverage-desk').inner_text() for text in ('solar purchase agreement','country-wide','agricultural water project')))
            page.set_viewport_size({'width':390,'height':844});page.locator('#drawer').evaluate('el=>el.scrollTop=0')
            page.screenshot(path=str(OUT/f'{label}-coverage-candidates-mobile.png'))
            check(entry+' candidate research is readable at mobile width',page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
            page.locator('.atlas-coverage-candidate [data-id="P19"]').click()
            check(entry+' new source preserves undated publication boundary','Publication date not stated' in page.locator('#drawer-content').inner_text() and 'Hamina' in page.locator('#drawer-content').inner_text())
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' source back restores research-candidate tab',page.locator('[data-coverage-tab="candidates"]').get_attribute('aria-pressed')=='true')
            page.locator('[data-coverage-tab="disclosures"]').click();page.locator('[data-coverage-action="reset"]').click()
            page.locator('#atlas-coverage-query').fill('Ellendale')
            page.evaluate("ATLAS.state.filter.country='China'")
            page.locator('[data-coverage-site="coreweave-ellendale"]').first.click()
            check(entry+' cross-geography dossier drill-down is not trapped by old map filters',page.evaluate('ATLAS.state.spatialSelected')=='coreweave-ellendale' and '250 MW' in page.locator('.atlas-feature-number').inner_text())
            check(entry+' mobile facility remains within viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            check(entry+' no unhandled JavaScript errors',not errors,errors)
            check(entry+' no third-party network requests',not external,external)
            page.close()
        browser.close()
finally:
    if server:server.shutdown();server.server_close()
report={'execution':'in-memory Chromium; not HTTP' if args.in_memory else 'real HTTP hosted + standalone Chromium','passed':sum(row['pass'] for row in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/global_coverage_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
