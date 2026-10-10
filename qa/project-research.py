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
                check(label+' pagination focuses the new page of projects', page.locator('.atlas-research-project>header>button').first.evaluate('el=>document.activeElement===el'))
                check(label+' pagination brings new results into view', 62 <= page.locator('.atlas-research-project').first.bounding_box()['y'] < 200)
                page.locator('.atlas-research-refine>summary').click()
                page.locator('[data-research-filter="country"]').select_option('China')
                page.locator('[data-research-filter="topic"]').select_option('finance')
                check(label+' geography and topic filters intersect known disclosures', set(page.locator('[data-research-project]').evaluate_all('els=>els.map(el=>el.dataset.researchProject)')) == {
                    'huawei-gui-an-cloud-data-center', 'sensetime-qianhai-intelligent-computing-center', 'baidu-yangquan-cloud-center'})
                page.locator('[data-research-filter="operator"]').select_option('microsoft')
                check(label+' contradictory filters have a truthful empty state', page.locator('[data-research-project]').count() == 0 and 'does not mean zero capacity' in page.locator('.atlas-research-empty').inner_text())
                page.locator('[data-research-reset]').click()
                check(label+' reset clears all filters and restores search focus', '79 matching projects' in page.locator('#atlas-research-count').inner_text() and page.locator('#atlas-research-query').evaluate('el=>document.activeElement===el'))
                page.locator('#atlas-research-query').fill('3,000,000')
                check(label+' formatted native quantities are searchable with their units', page.locator('[data-research-match="lingang-energy-saving"]').count() == 1
                    and 'kWh/year' in page.locator('[data-research-match="lingang-energy-saving"]').inner_text())
                page.locator('#atlas-research-query').fill('D15')
                check(label+' research text search finds a new project detail', page.locator('[data-research-project="baidu-yangquan-cloud-center"]').count() == 1)
                match=page.locator('[data-research-project="baidu-yangquan-cloud-center"] .atlas-research-match')
                check(label+' search explains the matching project disclosure', 'Matched project disclosure' in match.inner_text() and 'D15' in match.inner_text() and match.locator('mark').count() > 0)
                check(label+' search preserves input focus', page.locator('#atlas-research-query').evaluate('el=>document.activeElement===el'))
                page.locator('[data-research-filter="country"]').select_option('China')
                page.locator('[data-research-filter="topic"]').select_option('finance')
                page.locator('[data-research-filter="sort"]').select_option('date')
                page.reload(wait_until='networkidle')
                page.wait_for_function('document.documentElement.classList.contains("research-ready")',timeout=30000)
                check(label+' research URL restores search, geography, topic and order', '#research?' in page.url
                    and page.locator('#atlas-research-query').input_value() == 'D15'
                    and page.locator('[data-research-filter="country"]').input_value() == 'China'
                    and page.locator('[data-research-filter="topic"]').input_value() == 'finance'
                    and page.locator('[data-research-filter="sort"]').input_value() == 'date')
                match=page.locator('[data-research-project="baidu-yangquan-cloud-center"] .atlas-research-match')
                check(label+' topic refinement matches finance evidence directly', match.get_attribute('data-research-match') == 'research-20261010-yangquan-d15-investment')
                page.locator('[data-research-remove-filter="sort"]').click()
                check(label+' removing one refinement retains the others and search focus', page.locator('[data-research-filter="sort"]').input_value() == 'name'
                    and page.locator('[data-research-filter="topic"]').input_value() == 'finance'
                    and page.locator('[data-research-filter="country"]').input_value() == 'China'
                    and page.locator('#atlas-research-query').evaluate('el=>document.activeElement===el'))
                page.locator('[data-research-filter="sort"]').select_option('date')
                page.locator('.atlas-research-refine>summary').click()
                page.locator('#drawer').evaluate('el=>el.scrollTop=0')
                page.screenshot(path=str(out/f'research-refined-{label}-index-desktop.png'))
                match.locator('[data-research-site]').click()
                page.wait_for_timeout(80)  # The default drawer focus must not override the requested claim.
                check(label+' matched disclosure opens and receives keyboard focus', page.locator('#drawer [data-research-claim="research-20261010-yangquan-d15-investment"]').evaluate('el=>document.activeElement===el'))
                check(label+' project dossier shows six research categories', page.locator('#drawer [data-research-topic]').count() == 6)
                check(label+' every displayed project claim has a citation', page.locator('#drawer .atlas-research-topic .atlas-research-claim').count() == page.locator('#drawer .atlas-research-topic .atlas-research-claim .atlas-source-ref').count())
                check(label+' dated brief excludes contextual claims', page.locator('#drawer [data-research-highlight="research-20261010-yangquan-7000-context"]').count() == 0
                    and page.locator('#drawer [data-research-highlight]').count() > 0)
                dossier_query=page.locator('#drawer [data-research-query]')
                dossier_query.fill('7,000P')
                check(label+' dossier search reveals wider context without project allocation', '0 matching project claims' in page.locator('#drawer .atlas-research-query-status').inner_text()
                    and page.locator('#drawer .atlas-research-context').evaluate('el=>el.open && !el.hidden')
                    and '7,000P' in page.locator('#drawer .atlas-research-context').inner_text())
                check(label+' dossier filtering keeps search focus', dossier_query.evaluate('el=>document.activeElement===el'))
                dossier_query.fill('zzzz_no_claim')
                check(label+' dossier no-match is explicit without a zero-capacity claim', 'No match does not mean zero capacity' in page.locator('#drawer .atlas-research-query-status').inner_text()
                    and page.locator('#drawer [data-research-topic]:visible').count() == 0)
                page.locator('#drawer [data-research-clear]').click()
                check(label+' dossier clear restores six categories and input focus', page.locator('#drawer [data-research-topic]:visible').count() == 6 and dossier_query.evaluate('el=>document.activeElement===el'))
                page.locator('#drawer [data-research-jump-topic="technical"]').click()
                check(label+' topic shortcut scrolls and focuses its section', page.locator('#drawer [data-research-topic="technical"]').evaluate('el=>document.activeElement===el')
                    and page.locator('#drawer [data-research-topic="technical"]').bounding_box()['y'] >= 62)
                context = page.locator('#drawer .atlas-research-context')
                if not context.evaluate('el=>el.open'): context.locator('summary').first.click()
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
                check(label+' export retains date semantics and only project milestones', exported['development_disclosures'] == [{'claim_id':'research-20261010-yangquan-d15-start','as_of':'2025-06-03','source_id':'RC014'}]
                    and 'not inferred' in exported['development_date_policy'])
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
                page.evaluate('openSearch()')
                page.locator('#global-search').fill('Training-room')
                locator_match=page.locator('#search-results [data-research-site="huawei-gui-an-cloud-data-center"]')
                locator_match.wait_for(state='visible')
                check(label+' supplemental search match clears the generic empty state',
                    page.locator('#search-results .search-empty').count() == 0)
                title_box=locator_match.locator('b').bounding_box()
                citation_box=locator_match.locator('small').bounding_box()
                check(label+' global result citation has a separate readable line',
                    citation_box['y'] >= title_box['y']+title_box['height']-0.5)
                check(label+' global search includes source locators and identifies the cited claim',
                    locator_match.count() == 1
                    and locator_match.get_attribute('data-research-claim-target') == 'research-20261010-guian-training'
                    and 'RC009' in locator_match.inner_text())
                locator_match.click()
                check(label+' global source-locator match reveals and focuses the actual claim',
                    page.locator('#drawer [data-research-claim="research-20261010-guian-training"]').evaluate('el=>document.activeElement===el && el.getClientRects().length>0'))
                page.evaluate("state.filter.q='Training-room'")
                check(label+' map and directory filters search the same source locators',
                    'huawei-gui-an-cloud-data-center' in page.evaluate('spatialFiltered().map(s=>s.id)')
                    and 'huawei-gui-an-cloud-data-center' in page.evaluate('filteredSites().map(s=>s.id)'))
                page.evaluate("state.filter.q='';openSearch()")
                page.locator('#global-search').fill('3,000,000 kWh/year')
                page.locator('#search-results [data-research-site="sensetime-lingang-aidc"]').wait_for(state='visible')
                check(label+' global search recognizes formatted native quantities with units',
                    page.locator('#search-results [data-research-site="sensetime-lingang-aidc"]').count() == 1)
                page.locator('#global-search').fill('2026-06-23')
                page.locator('#search-results [data-research-site="microsoft-fairwater-wisconsin"][data-research-claim-target]').wait_for(state='visible')
                check(label+' global search recognizes disclosure dates',
                    page.locator('#search-results [data-research-site="microsoft-fairwater-wisconsin"][data-research-claim-target]').count() == 1)
                page.locator('#global-search').fill('zz-no-atlas-result-visual-regression')
                page.locator('#search-results .search-empty').wait_for(state='visible')
                check(label+' genuinely unmatched global query retains the empty state',
                    page.locator('#search-results .search-result').count() == 0
                    and 'No results found' in page.locator('#search-results .search-empty').inner_text())
                page.evaluate('closeSearch()')
                page.evaluate("ATLAS.openDrawer('site','sensetime-qianhai-intelligent-computing-center')")
                check(label+' native FP16 precision and planned status are visible', 'PFLOPS FP16' in page.locator('#drawer [data-research-claim="research-20261010-qianhai-fp16"]').inner_text() and 'Planned' in page.locator('#drawer [data-research-claim="research-20261010-qianhai-fp16"]').inner_text())
                page.set_viewport_size({'width':390, 'height':844})
                page.locator('#drawer').evaluate('el=>el.scrollTop=0')
                page.wait_for_timeout(300)
                check(label+' mobile dossier has no horizontal overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
                page.evaluate('openSearch()')
                page.locator('#global-search').fill('Training-room')
                mobile_match=page.locator('#search-results [data-research-site="huawei-gui-an-cloud-data-center"]')
                mobile_match.wait_for(state='visible')
                title_box=mobile_match.locator('b').bounding_box()
                citation_box=mobile_match.locator('small').bounding_box()
                check(label+' mobile global result separates title and citation without overflow',
                    citation_box['y'] >= title_box['y']+title_box['height']-0.5
                    and page.locator('#search-results').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
                page.evaluate('closeSearch()')
                check(label+' mobile drawer retains a single-line back control', page.locator('[data-action="drawer-back"]').bounding_box()['height'] <= 44)
                page.screenshot(path=str(out/f'project-research-{label}-mobile.png'))
                page.set_viewport_size({'width':320, 'height':780})
                check(label+' narrow mobile dossier fits 320 pixels', page.locator('#drawer').evaluate('el=>el.scrollWidth<=el.clientWidth+1'))
                page.set_viewport_size({'width':390, 'height':844})
                page.locator('[data-action="close-drawer"]').click()
                page.locator('.mobile-menu').click()
                page.locator('#sidebar [data-research-index]').click()
                check(label+' mobile research navigation closes the menu', page.locator('#sidebar').get_attribute('aria-hidden') == 'true' and page.locator('.app-shell').evaluate('el=>!el.inert'))
                page.locator('#atlas-research-query').fill('D15')
                check(label+' returning to research retains search', '1 matching project ·' in page.locator('#atlas-research-count').inner_text())
                check(label+' returning to research retains topic and geography', page.locator('[data-research-filter="topic"]').input_value() == 'finance' and page.locator('[data-research-filter="country"]').input_value() == 'China')
                page.locator('[data-research-reset]').click()
                page.locator('#atlas-research-outcome').select_option('unresolved')
                check(label+' unresolved identities are findable', page.locator('[data-research-project]').count() > 0 and all(x == 'Identity unresolved' for x in page.locator('.atlas-research-outcome').all_inner_texts()))
                page.screenshot(path=str(out/f'project-research-{label}-index-mobile.png'))
                page.locator('#atlas-research-outcome').select_option('all')
                page.locator('#atlas-research-query').fill('1.5 GW potential across Lordstown and Milam')
                lordstown=page.locator('[data-research-project="openai-lordstown"] .atlas-research-match')
                check(label+' context-only match visibly retains unresolved association', lordstown.count() == 1 and lordstown.evaluate('el=>el.classList.contains("context")') and 'Matched wider context' in lordstown.inner_text())
                page.locator('[data-research-reset]').click()
                page.locator('#atlas-research-query').fill('<img src=x onerror=alert(1)>')
                check(label+' literal HTML search remains inert', page.locator('#drawer img').count() == 0 and page.locator('[data-research-project]').count() == 0)
                page.locator('[data-research-reset]').click()
                page.set_viewport_size({'width':1440,'height':1080})
                page.evaluate("ATLAS.openDrawer('site','microsoft-fairwater-wisconsin')")
                page.locator('#drawer .atlas-project-research').scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'research-refined-{label}-brief-desktop.png'))
                page.set_viewport_size({'width':390,'height':844})
                page.locator('#drawer .atlas-research-brief').scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'research-refined-{label}-brief-mobile.png'))
                page.set_viewport_size({'width':1440,'height':1080})
                development=page.locator('#drawer [data-research-topic="development"]')
                check(label+' new operating disclosure precedes the old planned schedule', development.locator('[data-research-claim]').first.get_attribute('data-research-claim') == 'rg-microsoft-fairwater-wisconsin-operational')
                check(label+' regional investment stays outside project financing', page.locator('#drawer .atlas-research-topic [data-research-claim="wisconsin-regional-investment"]').count() == 0
                    and page.locator('#drawer .atlas-research-context [data-research-claim="wisconsin-regional-investment"]').count() == 1)
                check(label+' regional investment export retains its original boundary and contextual classification', page.evaluate("(()=>{const x=ATLAS.evidence.export(ATLAS.data.sites.find(s=>s.id==='microsoft-fairwater-wisconsin'));return x.contextual_claim_ids.includes('wisconsin-regional-investment')&&!x.project_claim_ids.includes('wisconsin-regional-investment')&&x.primary_observations.some(r=>r.id==='wisconsin-regional-investment'&&r.value===7&&r.boundary==='regional_investment');})()"))
                chronology=page.locator('#drawer .atlas-research-timeline')
                chronology.locator('summary').click()
                dates=chronology.locator('time').all_inner_texts()
                check(label+' chronology orders disclosure dates and retains dated plan wording', dates == sorted(dates) and 'Early 2026 start planned in September 2025' in chronology.inner_text() and 'not an inferred completion date' in chronology.inner_text())
                sources=page.locator('#drawer .atlas-research-source-list')
                sources.locator('summary').click()
                check(label+' new source trail attributes documents and undated publications', sources.locator('article').count() > 0 and 'Retrieved ' in sources.inner_text() and 'do not establish independent corroboration' in sources.inner_text())
                source_button=sources.locator('[data-atlas-action="source"]').first
                source_id=source_button.get_attribute('data-id')
                source_url=page.evaluate('id=>primarySource(id).url',source_id)
                source_button.click()
                check(label+' primary source trail opens its exact source URL', page.locator('#drawer a.btn.primary').get_attribute('href') == source_url)
                page.locator('[data-action="close-drawer"]').click()
                page.evaluate('ATLAS.research.open()')
                latency=page.evaluate("""() => new Promise(resolve=>{
                    const input=document.querySelector('#atlas-research-query'),start=performance.now();
                    input.value='D15';input.dispatchEvent(new Event('input',{bubbles:true}));
                    requestAnimationFrame(()=>resolve(performance.now()-start));
                })""")
                check(label+' evidence search renders within one second', latency < 1000, {'input_to_animation_frame_ms':round(latency,2)})
                page.locator('[data-research-reset]').click()
                if label == 'sqlite':
                    page.locator('#atlas-research-outcome').select_option('all')
                    page.locator('.atlas-research-refine>summary').click()
                    page.locator('[data-research-filter="country"]').select_option('United States')
                    page.locator('[data-research-filter="operator"]').select_option('google')
                    page.locator('[data-research-filter="topic"]').select_option('technical')
                    page.locator('[data-research-filter="sort"]').select_option('date')
                    page.locator('#atlas-research-query').fill('SYNTHETIC QA RESEARCH UPDATE')
                    fixture = {'id':'synthetic-qa-research-update', 'site_id':'google-mesa',
                        'label':'SYNTHETIC QA RESEARCH UPDATE', 'value':'Temporary test ledger only <img src=x onerror=window.researchInjection=true>',
                        'source_id':'P01', 'as_of':None, 'topic':'technical', 'scope':'Synthetic UI fixture',
                        'source_locator':'Synthetic test, not a publisher disclosure', 'applies_to':'project'}
                    app.state.store.submit_claim('fact', fixture, 'qa-test')
                    app.state.store.decide(fixture['id'], 'accepted', 'qa-test', 'Test temporary publication refresh')
                    page.evaluate('ATLAS.publication.check()')
                    check('Publication update leaves current research snapshot stable', page.locator('[data-research-project]').count() == 0)
                    page.locator('#drawer [data-service-publication="apply"]').click()
                    check('Applying SQLite update refreshes research while retaining query', page.locator('[data-research-project="google-mesa"]').count() == 1 and page.locator('#atlas-research-query').input_value() == 'SYNTHETIC QA RESEARCH UPDATE')
                    check('Publication update retains geography, operator, topic and order', all(page.locator(f'[data-research-filter="{key}"]').input_value() == value
                        for key,value in [('country','United States'),('operator','google'),('topic','technical'),('sort','date')]))
                    page.locator('#atlas-research-query').fill('img')
                    check('Matched untrusted text is escaped before search highlighting', page.locator('.atlas-research-match mark').count() > 0
                        and page.locator('#drawer img').count() == 0 and page.evaluate('window.researchInjection!==true'))
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
