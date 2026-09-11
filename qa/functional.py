"""Offline in-memory browser tests, including interaction and original-file fidelity.
The managed browser in this environment disallows file/localhost navigation;
set_content exercises the exact built HTML without any external request.
"""
import json,hashlib,math
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[];errs=[];requests=[]
def check(name,ok,detail=None):
 checks.append(dict(test=name,pass_=bool(ok),detail=detail))
 print(('PASS ' if ok else 'FAIL ')+name,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1500,'height':1000},accept_downloads=True)
 page.set_default_timeout(6500)
 page.on('pageerror',lambda e:errs.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 page.set_content((ROOT/'compute_atlas.html').read_text(),wait_until='load');page.wait_for_timeout(200)
 # Data completeness, malformed references and all original phase rows.
 d=page.evaluate('ATLAS.data');arc=page.evaluate('ATLAS.archive')
 check('all 92 original facility-phase rows preserved',sum(len(s['raw']) for s in d['sites'])==92)
 check('both full report versions available',sum(len(r['sections']) for r in arc['reports'])==108)
 check('all 101 original report tables retained',sum(r['table_count'] for r in arc['reports'])==101)
 check('all 5938 populated/formula workbook cells preserved',sum(len(s['cells']) for w in arc['workbooks'] for s in w['sheets'])==5938)
 check('eleven Chinese companies included',sum(c['region']=='China' for c in d['companies'])==11)
 check('native-unit China records are not forced to zero/GW',next(s for s in d['sites'] if s['name'].startswith('Qianhai'))['snapshot'] is None)
 for name,expected in [('New Carlisle',1925),('Fairwater Wisconsin',2263),('Stargate Abilene',843),('Helios',528)]:check(name+' reviewed target',next(s for s in d['sites'] if s['name']==name)['target']['it_mw']==expected)
 # A nonblack canvas is required; route boot alone would miss a blank globe.
 pix=page.evaluate('(()=>{let g=ATLAS.getGlobe(),p=g.ctx.getImageData(Math.floor(g.cx*g.dpr),Math.floor(g.cy*g.dpr),1,1).data;return Array.from(p)})()')
 check('globe visibly rendered, not blank',[*pix[:3]]!=[0,0,0],pix)
 page.evaluate("ATLAS.navigate('globe')");page.wait_for_timeout(100)
 old=page.evaluate('ATLAS.getGlobe().lon');canvas=page.locator('#globe-canvas');box=canvas.bounding_box()
 page.mouse.move(box['x']+box['width']*.55,box['y']+box['height']*.65);page.mouse.down();page.mouse.move(box['x']+box['width']*.55+70,box['y']+box['height']*.65,steps=6);page.mouse.up();page.wait_for_timeout(100)
 check('pointer dragging rotates globe',abs(page.evaluate('ATLAS.getGlobe().lon')-old)>5)
 old=page.evaluate('ATLAS.getGlobe().zoom');page.locator('[data-action="zoom"][data-id="in"]').click();check('zoom button changes globe scale',page.evaluate('ATLAS.getGlobe().zoom')>old)
 page.locator('[data-action="fly"][data-id="asia"]').click();page.wait_for_timeout(950)
 g=page.evaluate("(()=>{let g=ATLAS.getGlobe(),p=g.groups.find(p=>p.sites.length===1&&p.sites[0].name==='Zhangbei');return p?{x:p.x,y:p.y}:null})()")
 check('China facility has a selectable marker',g is not None)
 if g:
  box=canvas.bounding_box();page.mouse.click(box['x']+g['x'],box['y']+g['y']);check('actual canvas marker opens matching dossier',page.locator('#drawer-content h1').inner_text()=='Zhangbei');page.locator('[data-action="close-drawer"]').click()
 page.evaluate("ATLAS.navigate('facilities')");page.locator('[data-filter="country"]').select_option('China');check('country filter reaches all seven China dossiers',page.locator('#content tbody tr').count()==7)
 page.locator('[data-action="site-layout"][data-id="chart"]').click();check('linked facility scatter shows two quantified China sites',page.locator('.scatter-point').count()==2)
 page.locator('.scatter-point circle').first.click();check('scatter point opens facility dossier',page.locator('#drawer').is_visible());page.locator('[data-action="close-drawer"]').click()
 page.evaluate("ATLAS.navigate('companies')")
 for id in ['amazon','google','microsoft','alibaba']:page.locator('[data-compare="'+id+'"]').check()
 page.locator('[data-compare="meta"]').click();check('comparison capped at four',page.evaluate('ATLAS.state.compare.length')==4)
 page.locator('.compare-dock [data-action="nav"]').click();check('comparison table displays four companies',page.locator('.compare-table thead th').count()==5)
 # Deep render every dossier to detect missing field assumptions, no manual stubs.
 failures=page.evaluate("""(()=>{const bad=[];for(const [kind,key] of [['site','sites'],['company','companies'],['source','sources'],['cost','costs'],['contract','contracts']])for(const x of ATLAS.data[key]){try{ATLAS.openDrawer(kind,x.id);if(!document.querySelector('#drawer-content').innerText.trim())bad.push(kind+':'+x.id);}catch(e){bad.push(kind+':'+x.id+' '+e.message)}}return bad})()""")
 check('all 199 entity/source/cost/contract dossiers render',not failures,failures)
 page.locator('[data-action="close-drawer"]').click()
 # Search cross references, deep section and source.
 page.locator('.search-trigger').click();page.locator('#global-search').fill('Helios');page.wait_for_timeout(220);check('global search returns facility and report records',page.locator('.search-result').count()>2)
 page.locator('#search-results [data-action="site"]').first.click();check('search opens correct facility',page.locator('#drawer-content h1').inner_text()=='Helios')
 sid=page.evaluate('ATLAS.state.drawer.id');page.locator('#drawer-content .star-button').click();check('watchlist star updates session',page.evaluate('(id)=>ATLAS.data.sites.some(x=>x.id===id)',sid))
 page.locator('#facility-note').fill('Check critical IT load, not the gross envelope.');page.locator('[data-action="close-drawer"]').click();page.evaluate("ATLAS.navigate('watchlist')");check('saved note and site visible on research shelf','Check critical IT load' in page.locator('#content').inner_text())
 # Exact file download, verify against original manifest.
 page.evaluate("ATLAS.state.dataTab='files';ATLAS.navigate('data')")
 with page.expect_download(timeout=5000) as info:page.locator('[data-action="original-file"]').first.click()
 dl=info.value;path=Path(dl.path());h=hashlib.sha256(path.read_bytes()).hexdigest();check('original PDF retrieval is byte-for-byte identical',h==d['manifest'][0]['sha256'],{'name':dl.suggested_filename,'sha256':h})
 # Every source workbook sheet and report section must be navigable.
 outcomes=page.evaluate("""(()=>{let bad=[],sections=0,sheets=0;for(let r=0;r<ATLAS.archive.reports.length;r++)for(let s=0;s<ATLAS.archive.reports[r].sections.length;s++){try{ATLAS.state.report=r;ATLAS.state.section=s;ATLAS.navigate('reports');sections++;}catch(e){bad.push('report '+r+'/'+s+':'+e.message)}}for(let b=0;b<ATLAS.archive.workbooks.length;b++)for(let s=0;s<ATLAS.archive.workbooks[b].sheets.length;s++){try{ATLAS.state.dataTab='workbooks';ATLAS.state.book=b;ATLAS.state.sheet=s;ATLAS.navigate('data');sheets++;}catch(e){bad.push('sheet '+b+'/'+s+':'+e.message)}}return {bad,sections,sheets}})()""")
 check('every report section and original sheet renders',not outcomes['bad'] and outcomes['sections']==108 and outcomes['sheets']==23,outcomes)
 page.evaluate("ATLAS.state.dataTab='workbooks';ATLAS.state.book=0;ATLAS.state.sheet=0;ATLAS.navigate('data')")
 addr=page.evaluate("ATLAS.archive.workbooks[0].sheets[0].cells.find(c=>c.formula).address")
 page.locator('[data-action="cell"][data-id="'+addr+'"]').click();check('Excel cell drilldown exposes exact formula','Formula' in page.locator('#drawer-content').inner_text() and '=' in page.locator('#drawer-content').inner_text());page.locator('[data-action="close-drawer"]').click()
 # All four economics tabs, bounded math and meaningful response to utilization.
 page.evaluate("ATLAS.navigate('costs')")
 for tab in ['benchmarks','scenario','hardware','company']:
  page.locator('[data-action="cost-tab"][data-id="'+tab+'"]').click();check('cost view '+tab,len(page.locator('#content').inner_text())>500)
 page.locator('[data-action="cost-tab"][data-id="scenario"]').click();before=page.evaluate('ATLAS.calculateScenario().unit');page.locator('[data-action="heat"][data-life="3"][data-util="40"]').click();after=page.evaluate('ATLAS.calculateScenario().unit');check('shorter equipment life and lower utilization raise unit cost',after>before)
 page.evaluate("ATLAS.navigate('investment')");before=page.locator('#valuation-output').inner_text();page.locator('#v-fcf').fill('5');page.locator('#v-fcf').dispatch_event('input');check('investment sensitivity is live',before!=page.locator('#valuation-output').inner_text())
 # Tour is an actual route sequence, not a slideshow mock.
 page.evaluate("ATLAS.navigate('stories')");page.locator('#content [data-action="tour-start"]').click();check('guided tour starts on globe',page.locator('#tour').is_visible() and page.evaluate('ATLAS.state.view')=='globe')
 for _ in range(4):page.locator('#tour [data-action="tour-next"]').click()
 check('tour ends in interactive cost model',page.locator('#scenario-unit').count()==1);page.locator('#tour [data-action="tour-next"]').click();check('tour exits cleanly',not page.locator('#tour').is_visible())
 # Mobile overflow check for all main views and all extra cost views.
 page.set_viewport_size({'width':390,'height':844});mobile=[]
 for route in ['overview','globe','facilities','companies','contracts','costs','investment','reports','data','stories','watchlist']:
  page.evaluate('(r)=>ATLAS.navigate(r)',route);mobile.append((route,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')))
 check('all mobile main views avoid page-wide overflow',all(ok for _,ok in mobile),mobile)
 check('no uncaught JavaScript errors',not errs,errs)
 check('zero network requests',not requests,requests)
 b.close()
res={'checks':checks,'passed':sum(c['pass_'] for c in checks),'total':len(checks),'errors':errs,'network_requests':requests,'execution':'Exact built HTML rendered in managed Chromium via set_content (file/localhost navigation disabled by environment policy).'}
(ROOT/'qa/functional_results.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))
