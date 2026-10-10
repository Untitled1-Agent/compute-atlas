"""Cited project research on real HTTP: SQLite service and standalone publication.

The one explicitly labeled synthetic update lives only in this temporary ledger.
No production credentials or third-party requests are used by this audit.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import uvicorn
from playwright.sync_api import sync_playwright
from server.app import create_app
from server.store import ROOT

out = ROOT/'qa/screenshots'; out.mkdir(exist_ok=True)
checks = []


def check(name, passed, detail=None):
    checks.append({'test': name, 'pass': bool(passed), 'detail': detail})
    print(('PASS ' if passed else 'FAIL ')+name, flush=True)


with tempfile.TemporaryDirectory() as directory:
    app = create_app(Path(directory)/'atlas.sqlite3', background=False)
    publication = app.state.store.publication()
    sock = socket.socket(); sock.bind(('127.0.0.1', 0))
    base = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning'))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    for _ in range(100):
        try:
            if httpx.get(base+'/api/health', timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(.1)
    try:
        with sync_playwright() as p:
            exe = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'],
                **({'executable_path': exe} if exe else {}))
            for entry, label in [('/index.html', 'sqlite'), ('/compute_atlas.html', 'standalone')]:
                page = browser.new_page(viewport={'width':1440, 'height':1080}, accept_downloads=True)
                page.set_default_timeout(10000)
                page.set_default_navigation_timeout(30000)
                errors = []; external = []; requests = []; failed = []; console_errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('requestfailed', lambda r: failed.append({'url':r.url,'error':r.failure}))
                page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
                page.on('request', lambda r: requests.append(r.url))
                page.on('request', lambda r: external.append(r.url) if r.url.startswith('http') and not r.url.startswith(base) else None)
                check(label+' actual HTTP entrypoint', page.goto(base+entry, wait_until='networkidle').status == 200)
                try:
                    page.wait_for_function('document.documentElement.classList.contains("research-ready")', timeout=30000)
                except Exception:
                    print(json.dumps({'entry':entry,'url':page.url,'browser_errors':errors,
                        'failed_requests':failed,'console_errors':console_errors,
                        'requests':requests[-20:]}, indent=2), flush=True)
                    raise
                check(label+' complete research reaches the browser', page.evaluate('ATLAS_PRIMARY.research_coverage.projects.length') == 79)
                page.evaluate("ATLAS.openDrawer('site','microsoft-fairwater-wisconsin')")
                check(label+' regional investment remains wider context in the dossier',
                    page.locator('#drawer .atlas-research-topic [data-research-claim="wisconsin-regional-investment"]').count() == 0
                    and page.locator('#drawer .atlas-research-context [data-research-claim="wisconsin-regional-investment"]').count() == 1)
                check(label+' regional investment export preserves the source boundary without project allocation',
                    page.evaluate("(()=>{const x=ATLAS.evidence.export(ATLAS.data.sites.find(s=>s.id==='microsoft-fairwater-wisconsin'));return x.contextual_claim_ids.includes('wisconsin-regional-investment')&&!x.project_claim_ids.includes('wisconsin-regional-investment')&&x.primary_observations.some(r=>r.id==='wisconsin-regional-investment'&&r.value===7&&r.boundary==='regional_investment');})()"))
                page.locator('[data-action="close-drawer"]').click()
                if label == 'sqlite':
                    check('SQLite publication hash reaches the browser', page.evaluate('ATLAS_PRIMARY.publication_hash') == publication['publication_hash'])
                else:
                    check('Standalone never probes the API', not [r for r in requests if '/api/' in r])
                page.locator('[data-research-index]').first.click()
                check(label+' searchable index includes all 79 projects', '79 matching projects' in page.locator('#atlas-research-count').inner_text())
                check(label+' index paginates projects', page.locator('[data-research-project]').count() == 15)
                page.locator('[data-research-page="next"]').click()
                check(label+' pagination keeps keyboard focus', page.locator('[data-research-page="next"]').evaluate('el=>document.activeElement===el'))
                page.locator('#atlas-research-query').fill('D15')
                check(label+' research text search finds a new project detail', page.locator('[data-research-site="baidu-yangquan-cloud-center"]').count() == 1)
                check(label+' search preserves input focus', page.locator('#atlas-research-query').evaluate('el=>document.activeElement===el'))
                page.locator('[data-research-site="baidu-yangquan-cloud-center"]').click()
                check(label+' project dossier shows six research categories', page.locator('#drawer [data-research-topic]').count() == 6)
                check(label+' every displayed project claim has a citation', page.locator('#drawer .atlas-research-topic .atlas-research-claim').count() == page.locator('#drawer .atlas-research-topic .atlas-research-claim .atlas-source-ref').count())
                context = page.locator('#drawer .atlas-research-context')
                context.locator('summary').first.click()
                check(label+' city compute stays separate from Baidu project', '7,000' in context.inner_text() and page.locator('#drawer .atlas-research-topic [data-research-claim="research-20261010-yangquan-7000-context"]').count() == 0)
                page.screenshot(path=str(out/f'project-research-{label}-desktop.png'))
                source = page.locator('#drawer .atlas-research-topic .atlas-source-ref').first
                source_id = source.get_attribute('data-id')
                original_url = page.evaluate('id=>primarySource(id).url', source_id)
                source.click()
                check(label+' source opens its original disclosure link', page.locator('#drawer a.btn.primary').get_attribute('href') == original_url)
                page.locator('[data-action="drawer-back"]').click()
                check(label+' source back restores the researched dossier', page.locator('#drawer [data-project-research="baidu-yangquan-cloud-center"]').count() == 1)
                with page.expect_download() as transfer:
                    page.locator('#drawer .atlas-project-research [data-atlas-action="export"]').click()
                exported = json.loads(Path(transfer.value.path()).read_text())
                check(label+' export distinguishes project and contextual claims', 'research-20261010-yangquan-7000-context' in exported['contextual_claim_ids'] and 'research-20261010-yangquan-7000-context' not in exported['project_claim_ids'])
                check(label+' export includes review and original archive', exported['archive']['id'] == 'baidu-yangquan-cloud-center' and exported['research_review']['site_id'] == 'baidu-yangquan-cloud-center' and len(exported['topic_claim_ids']) == 6)
                check(label+' dossier retains a site deep-link', '#site/baidu-yangquan-cloud-center' in page.url, page.url)
                reloaded=page.reload(wait_until='networkidle')
                check(label+' deep-link reload returns HTML', reloaded.status == 200 and 'text/html' in reloaded.headers.get('content-type',''), {'url':page.url,'status':reloaded.status})
                page.wait_for_function('document.documentElement.classList.contains("research-ready")', timeout=30000)
                check(label+' deep-link reload includes the new research', page.locator('#drawer [data-project-research="baidu-yangquan-cloud-center"]').count() == 1)
                page.locator('[data-action="close-drawer"]').click()
                page.evaluate("ATLAS.navigate('globe');ATLAS.spatial.select('baidu-yangquan-cloud-center');ATLAS.spatial.setLevel(5)")
                check(label+' facility map includes the same researched dossier', page.locator('main [data-project-research="baidu-yangquan-cloud-center"]').count() == 1)
                page.evaluate("state.filter.q='D15'")
                check(label+' map filters search reviewed claims', 'baidu-yangquan-cloud-center' in page.evaluate('spatialFiltered().map(s=>s.id)'))
                page.evaluate("state.filter.q='';openSearch()")
                page.locator('#global-search').fill('D15')
                page.wait_for_selector('#search-results [data-research-site="baidu-yangquan-cloud-center"]')
                check(label+' global search links new project evidence', page.locator('#search-results [data-research-site="baidu-yangquan-cloud-center"]').count() == 1)
                page.locator('#search-results [data-research-site="baidu-yangquan-cloud-center"]').click()
                check(label+' search selection dismisses command overlay', page.locator('#search-modal').is_hidden())
                page.evaluate("ATLAS.openDrawer('site','sensetime-qianhai-intelligent-computing-center')")
                check(label+' native FP16 precision and planned status are visible', 'PFLOPS FP16' in page.locator('#drawer [data-research-claim="research-20261010-qianhai-fp16"]').inner_text() and 'Planned' in page.locator('#drawer [data-research-claim="research-20261010-qianhai-fp16"]').inner_text())
                page.set_viewport_size({'width':390, 'height':844})
                page.locator('#drawer').evaluate('el=>el.scrollTop=0')
                page.wait_for_timeout(300)
                check(label+' mobile dossier has no horizontal overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
                page.screenshot(path=str(out/f'project-research-{label}-mobile.png'))
                page.locator('[data-action="close-drawer"]').click()
                page.locator('.mobile-menu').click()
                page.locator('#sidebar [data-research-index]').click()
                check(label+' mobile research navigation closes the menu', page.locator('#sidebar').get_attribute('aria-hidden') == 'true' and page.locator('.app-shell').evaluate('el=>!el.inert'))
                page.locator('#atlas-research-query').fill('D15')
                check(label+' returning to research retains search', '1 matching projects' in page.locator('#atlas-research-count').inner_text())
                page.locator('#atlas-research-query').fill('')
                page.locator('#atlas-research-outcome').select_option('unresolved')
                check(label+' unresolved identities are findable', page.locator('[data-research-project]').count() > 0 and all(x == 'Identity unresolved' for x in page.locator('.atlas-research-outcome').all_inner_texts()))
                page.screenshot(path=str(out/f'project-research-{label}-index-mobile.png'))
                if label == 'sqlite':
                    page.locator('#atlas-research-outcome').select_option('all')
                    page.locator('#atlas-research-query').fill('SYNTHETIC QA RESEARCH UPDATE')
                    fixture = {'id':'synthetic-qa-research-update', 'site_id':'google-mesa',
                        'label':'SYNTHETIC QA RESEARCH UPDATE', 'value':'Temporary test ledger only',
                        'source_id':'P01', 'as_of':None, 'topic':'technical', 'scope':'Synthetic UI fixture',
                        'source_locator':'Synthetic test, not a publisher disclosure', 'applies_to':'project'}
                    app.state.store.submit_claim('fact', fixture, 'qa-test')
                    app.state.store.decide(fixture['id'], 'accepted', 'qa-test', 'Test temporary publication refresh')
                    page.evaluate('ATLAS.publication.check()')
                    check('Publication update leaves current research snapshot stable', page.locator('[data-research-project]').count() == 0)
                    page.locator('#drawer [data-service-publication="apply"]').click()
                    check('Applying SQLite update refreshes research while retaining query', page.locator('[data-research-site="google-mesa"]').count() == 1 and page.locator('#atlas-research-query').input_value() == 'SYNTHETIC QA RESEARCH UPDATE')
                check(label+' all original dossiers and scoped exports remain available', not page.evaluate("ATLAS.data.sites.filter(s=>ATLAS.evidence.export(s).archive.id!==s.id||ATLAS.research.profile(s).topics.length!==6).map(s=>s.id)"))
                check(label+' no unhandled browser exceptions', not errors, errors)
                check(label+' no third-party asset or API requests', not external, external)
                page.close()
            browser.close()
    finally:
        server.should_exit = True; thread.join(timeout=10); sock.close()

report = {'execution':'real HTTP SQLite service and standalone Chromium',
    'passed':sum(x['pass'] for x in checks), 'total':len(checks), 'checks':checks}
(ROOT/'qa/project_research_results.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'checks'}, indent=2))
if report['passed'] != report['total']:
    raise SystemExit(1)
