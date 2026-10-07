"""Identity, precision and shared-pin regressions. Default tests both HTTP entrypoints.

--in-memory uses the exact standalone in Chromium, not a deployment test.
Synthetic identity revisions below are temporary test data and never saved.
"""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.identity import identity_document
from server.store import Store
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
    with tempfile.TemporaryDirectory() as folder, sync_playwright() as p:
        store=Store(Path(folder)/'identity.sqlite3');store.seed()
        exe=shutil.which('chromium') or shutil.which('chromium-browser')
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for entry in (('compute_atlas.html',) if args.in_memory else ('index.html','compute_atlas.html')):
            label=Path(entry).stem;page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True)
            page.set_default_timeout(10000);errors=[];external=[];http_errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base or 'about:') else None)
            page.on('response',lambda r:http_errors.append(str(r.status)+' '+r.url) if r.status>=400 else None)
            if args.in_memory:page.set_content((ROOT/entry).read_text(),wait_until='load')
            else:check(entry+' HTTP response',page.goto(base+entry,wait_until='load').status==200)
            page.wait_for_function('window.ATLAS?.identity');page.wait_for_function('document.documentElement.classList.contains("catalog-ready")')
            baseline=page.evaluate('JSON.stringify(D.sites)')
            page.evaluate("ATLAS.spatial.select('hut8-river-bend');ATLAS.spatial.setLevel(5)")
            check(entry+' facility attributes have a reachable locality control',page.locator('.atlas-identity-launch [data-identity-open]').count()==1)
            page.locator('.atlas-identity-launch [data-identity-open]').click()
            check(entry+' primary parish stays beside original state-level anchor','West Feliciana Parish' in page.locator('.atlas-identity-claim').inner_text() and 'state-level anchor' in page.locator('.atlas-identity-anchor').inner_text())
            check(entry+' reporting and editorial dates remain separate',all(t in page.locator('.atlas-identity-claim').inner_text() for t in ('2025-12-17','2026-10-05')))
            check(entry+' source-established locality never certifies a pin','No' in page.locator('.atlas-identity-anchor').inner_text() and 'not a surveyed pin' in page.locator('.atlas-identity-boundary').inner_text())
            page.locator('#drawer').evaluate('el=>el.scrollTop=0');page.screenshot(path=str(OUT/f'{label}-identity-riverbend-desktop.png'))
            with page.expect_download() as transfer:page.locator('[data-identity-export]').click()
            exported=json.loads(Path(transfer.value.path()).read_text())
            check(entry+' JSON export is identical to the read-only database contract',exported==identity_document(store,'hut8-river-bend'))
            page.locator('.atlas-identity-claim [data-id="P15"]').click()
            check(entry+' source drill-down retains the filing link',page.locator('#drawer-content a[href*="sec.gov/Archives/edgar"]').count()==1)
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' source back restores the exact identity record',page.locator('[data-identity-site="hut8-river-bend"]').count()==1)
            page.locator('[data-identity-dossier]').click()
            check(entry+' full historical dossier remains independently reachable','River Bend' in page.locator('#drawer-content').inner_text() and page.evaluate('ATLAS.state.drawer.kind')=='site')
            page.evaluate("ATLAS.identity.open('coreweave-ellendale')")
            check(entry+' reviewed project alias does not rename the archived site',page.locator('.atlas-identity-claim h2').inner_text()=='Polaris Forge 1' and page.evaluate("site('coreweave-ellendale').name")=='Ellendale')
            full=page.evaluate("ATLAS.evidence.export(site('coreweave-ellendale'))")
            check(entry+' complete dossier export contains cited identity',full['identity_evidence']==identity_document(store,'coreweave-ellendale'))
            page.evaluate("ATLAS.identity.open('oracle-openai-stargate-abilene')")
            check(entry+' adjacent Microsoft project has a separately cited relationship',page.locator('.atlas-identity-related [data-id="P03"]').count()==1)
            check(entry+' shared city pin is visible without merging projects',page.locator('.atlas-identity-collision [data-identity-open="crusoe-abilene-expansion"]').count()==1)
            page.locator('.atlas-identity-related [data-identity-open]').click()
            check(entry+' related project navigation resolves Microsoft campus',page.locator('.atlas-identity-claim h2').inner_text()=='Crusoe Abilene campus for Microsoft')
            page.locator('[data-action="drawer-back"]').click()
            check(entry+' adjacent project back navigation preserves original identity',page.locator('[data-identity-site="oracle-openai-stargate-abilene"]').count()==1)
            parity=page.evaluate("D.sites.map(s=>[s.id,ATLAS.identity.export(s)])")
            check(entry+' all 79 browser identity exports match accepted database reads',all(doc==identity_document(store,sid) for sid,doc in parity),[sid for sid,doc in parity if doc!=identity_document(store,sid)])
            page.set_viewport_size({'width':390,'height':844});page.locator('#drawer').evaluate('el=>el.scrollTop=0')
            page.wait_for_function("getComputedStyle(document.querySelector('#toast')).opacity==='0'")
            page.screenshot(path=str(OUT/f'{label}-identity-abilene-mobile.png'))
            check(entry+' mobile identity panel fits 390px',page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1') and page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            page.locator('.atlas-identity-collision').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/f'{label}-identity-shared-pin-mobile.png'))
            page.set_viewport_size({'width':320,'height':740})
            check(entry+' narrow mobile identity panel fits 320px',page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
            page.evaluate("ATLAS.identity.open(D.sites.find(s=>s.lat===null||s.lat===undefined).id)")
            check(entry+' unreviewed unmapped record says not mapped, never zero',page.locator('.atlas-identity-coordinates').inner_text()=='Not mapped' and 'Not yet source-reviewed' in page.locator('.atlas-identity-claim').inner_text() and page.locator('.atlas-identity-collision').count()==0)
            page.evaluate("ATLAS.identity.open('not-a-site')")
            check(entry+' unknown site returns explicit empty state','Site not found.' in page.locator('#drawer-content').inner_text())
            page.set_viewport_size({'width':1440,'height':1080})
            # Synthetic in-browser mutations are restored before screenshots and exit.
            page.evaluate('window.identityOriginal=JSON.parse(JSON.stringify(ATLAS_PRIMARY))')
            page.evaluate("""()=>{const row=structuredClone(ATLAS_PRIMARY.facts.find(f=>f.identity));row.id='test-pending';row.review_status='pending';row.identity.canonical_name='Never publish pending';ATLAS_PRIMARY.facts.push(row);ATLAS.identity.open(row.site_id);}""")
            check(entry+' pending identity text is not exposed','Never publish pending' not in page.locator('#drawer-content').inner_text())
            page.evaluate("""()=>{const row=structuredClone(ATLAS_PRIMARY.facts.find(f=>f.identity));row.id='test-rejected';row.review_status='rejected';row.identity.canonical_name='Never publish rejected';ATLAS_PRIMARY.facts.push(row);ATLAS.identity.open(row.site_id);}""")
            check(entry+' rejected identity text is not exposed','Never publish rejected' not in page.locator('#drawer-content').inner_text())
            check(entry+' unsafe schema cannot certify invented coordinates',page.evaluate("""()=>{const d=structuredClone(identityOriginal);d.publication_hash='a'.repeat(64);d.facts.find(f=>f.identity).identity.coordinates=[33,-100];try{atlasValidatePublication(d);return false}catch{return true}}"""))
            check(entry+' type-confused precision is rejected safely',page.evaluate("""()=>{const d=structuredClone(identityOriginal);d.publication_hash='a'.repeat(64);d.facts.find(f=>f.identity).identity.place_precision=[];try{atlasValidatePublication(d);return false}catch{return true}}"""))
            check(entry+' secondary relationship cannot lose its own source',page.evaluate("""()=>{const d=structuredClone(identityOriginal);d.publication_hash='a'.repeat(64);d.facts.find(f=>f.identity?.related_sites.length).identity.related_sites[0].source_id='unknown';try{atlasValidatePublication(d);return false}catch{return true}}"""))
            page.evaluate("""()=>{const row=ATLAS_PRIMARY.facts.find(f=>f.identity);row.identity.canonical_name='<img src=x onerror=window.identityXSS=true>';ATLAS.identity.open(row.site_id);}""")
            check(entry+' identity text is escaped without creating external image requests',page.locator('.atlas-identity-claim img').count()==0 and page.evaluate('window.identityXSS!==true'))
            page.evaluate("""()=>{Object.keys(ATLAS_PRIMARY).forEach(k=>delete ATLAS_PRIMARY[k]);Object.assign(ATLAS_PRIMARY,structuredClone(identityOriginal));ATLAS.identity.open('coreweave-helios');window.identityHistoryLength=state.drawerHistory.length;window.identitySelected=state.spatialSelected;const d=structuredClone(identityOriginal);d.publication_hash='b'.repeat(64);d.facts.find(f=>f.id==='helios-identity-20261005').identity.canonical_name='Synthetic reviewed update';atlasPublicationPending=d;ATLAS.publication.apply();}""")
            check(entry+' explicit reviewed refresh rerenders an open identity desk',page.locator('.atlas-identity-claim h2').inner_text()=='Synthetic reviewed update')
            check(entry+' explicit refresh preserves selection and does not grow history',page.evaluate('state.spatialSelected===identitySelected && state.drawerHistory.length===identityHistoryLength'))
            page.evaluate("""()=>{atlasPublicationPending=structuredClone(identityOriginal);atlasPublicationPending.publication_hash='c'.repeat(64);ATLAS.publication.apply();delete window.identityOriginal;}""")
            check(entry+' all archival records remain byte-equivalent after exploration',page.evaluate('JSON.stringify(D.sites)')==baseline)
            page.locator('[data-action="close-drawer"]').click()
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(5)")
            page.locator('.atlas-identity-launch button').focus();page.keyboard.press('Enter')
            check(entry+' keyboard opens the same locality desk',page.locator('[data-identity-site="coreweave-helios"]').count()==1)
            page.keyboard.press('Escape')
            check(entry+' Escape dismisses identity and restores focus',page.locator('#drawer').is_hidden() and page.locator('.atlas-identity-launch button').evaluate('el=>el===document.activeElement'))
            page.wait_for_function("getComputedStyle(document.querySelector('#toast')).opacity==='0'")
            page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
            page.screenshot(path=str(OUT/f'{label}-identity-helios-facility.png'),full_page=True)
            check(entry+' zero unhandled browser exceptions',not errors,errors)
            check(entry+' zero unexpected external requests',not external,external)
            check(entry+' zero HTTP errors',not http_errors,http_errors)
            page.close()
        browser.close()
finally:
    if server:server.shutdown();server.server_close()
report={'execution':'in-memory Chromium; not HTTP' if args.in_memory else 'real HTTP hosted + standalone Chromium','passed':sum(r['pass'] for r in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/site_identity_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
