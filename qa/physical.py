"""Physical feature, phase, source, shelf and coordinate journeys through HTTP."""
import json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):
    checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page,scene=True):
    page.wait_for_function('window.ATLAS_BOOTSTRAPPING===false&&document.documentElement.classList.contains("layers-ready")')
    page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    page.wait_for_function(('globe instanceof CampusScene&&globe.imageReady&&' if scene else 'globe instanceof ResearchMap&&')+'!globe.dirty&&globe.w===globe.canvas.parentElement.clientWidth')
    page.wait_for_timeout(300)
def capture(page,entry,name):
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-physical-'+name+'.png')),full_page=True)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox']+(['--disable-gpu','--no-zygote','--renderer-process-limit=1'] if os.environ.get('ATLAS_LIGHT_BROWSER') else []))
        for entry in ('index.html','compute_atlas.html'):
            ctx=browser.new_context(viewport={'width':1440,'height':1080},accept_downloads=True);page=ctx.new_page();page.set_default_timeout(120000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry+'#overview?scale=facility&site=coreweave-helios');ready(page)
            check(entry+' Facility defaults to explicit physical identity',page.evaluate('ATLAS.workspace.activeSelection().type==="feature"') and page.locator('.campus-feature-inspector h2').inner_text()=='Original long roof')
            check(entry+' Facility breadcrumb does not imply phase identity','Original long roof' in page.locator('#breadcrumb').inner_text() and 'Phase I' not in page.locator('#breadcrumb').inner_text())
            check(entry+' physical inspector separates dates and allocation','2022-09-05' in page.locator('.campus-feature-inspector').inner_text() and '2026-07' in page.locator('.campus-feature-inspector').inner_text() and '133 MW' not in page.locator('.campus-feature-inspector').inner_text())
            check(entry+' overview exposes four compact attributes and sources',page.locator('.atlas-compact-attributes>.atlas-data-row').count()==4 and page.locator('.atlas-compact-sources>.atlas-document-row').count()==4)
            page.locator('.atlas-compact-attributes .atlas-evidence-more>summary').click();page.locator('.atlas-compact-sources .atlas-evidence-more>summary').click()
            check(entry+' evidence expanders retain all additional records',page.locator('.atlas-compact-attributes details .atlas-data-row').count()>=4 and page.locator('.atlas-compact-sources details .atlas-document-row').count()==4)
            page.locator('.atlas-compact-attributes .atlas-evidence-more>summary').click();page.locator('.atlas-compact-sources .atlas-evidence-more>summary').click();capture(page,entry,'helios-feature')
            page.locator('[data-campus-mode="oblique"]').click();ready(page);page.locator('#globe-canvas').focus();page.keyboard.press('ArrowRight');page.keyboard.press('Shift+ArrowDown');page.keyboard.press('+');ready(page)
            old=page.evaluate('globe.snapshot()');page.locator('.campus-view-toggle [data-campus-mode="evidence"]').click()
            check(entry+' explicit Evidence selects a claim',page.evaluate('ATLAS.workspace.activeSelection().type==="claim"') and page.locator('.workspace-selected-phase').is_visible())
            page.locator('[data-workspace-phase="helios-phase2-it"]').click();page.locator('[data-campus-mode="physical"]').click();ready(page)
            check(entry+' phase return restores physical identity and camera',page.evaluate('ATLAS.workspace.activeSelection().type==="feature"') and page.evaluate('globe.snapshot()')==old and page.locator('.campus-feature-inspector h2').inner_text()=='Original long roof')
            check(entry+' physical share has one active selection','selection=feature' in page.url and 'feature=helios-naip2022-roof-01' in page.url and 'claim=' not in page.url)
            page.locator('.campus-feature-inspector [data-campus-source]').click()
            check(entry+' identity source retains review basis and independent publication','Separately reviewed physical identity' in page.locator('#drawer-content').inner_text() and '2026-08-05' in page.locator('#drawer-content').inner_text() and 'not photogrammetric' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
            page.goto(base+entry+'#overview?scale=facility&site=amazon-anthropic-new-carlisle');ready(page)
            anchors=page.evaluate('JSON.stringify(D.sites.map(s=>[s.id,s.lon,s.lat]))')
            check(entry+' New Carlisle loads its dated licensed component',page.evaluate('globe.image.naturalWidth===1200&&globe.image.naturalHeight===1600') and '2025' in page.locator('.campus-historic-badge').inner_text() and 'CC0' in page.locator('.campus-scene-foot').inner_text())
            check(entry+' multiple roofs require explicit selection',page.locator('.campus-project-inspector').is_visible() and page.locator('.campus-feature-inspector').count()==0 and page.evaluate('campusState.feature===null'))
            check(entry+' all three reviewed roofs are independently hittable',page.evaluate('globe.features.length===3&&globe.hitSurfaces.length===3'))
            check(entry+' campus chooser keeps every feature action inside its rail',page.locator('.campus-project-inspector').evaluate('e=>{const r=e.getBoundingClientRect();return [...e.querySelectorAll("button")].every(b=>{const q=b.getBoundingClientRect();return q.left>=r.left-1&&q.right<=r.right+1})}'))
            check(entry+' desktop image gives roofs a useful inspection scale',page.evaluate('(()=>{const g=globe,points=g.features[0].polygons[0][0].map(v=>g.project3(...v));return Math.max(...points.map(p=>p.y))-Math.min(...points.map(p=>p.y))>200})()'))
            check(entry+' roof vertices use the returned image extent',page.evaluate('(()=>{const g=globe,[a,b,d]=g.imageCorners.map(p=>g.project3(...p));return g.features.every(f=>{const source=g.manifest.features.find(s=>s.id===f.record.id);return f.polygons[0][0].every((v,i)=>{const q=g.project3(...v),p=source.pixel_vertices[i];return Math.hypot(q.x-(a.x+(b.x-a.x)*p[0]/1200+(d.x-a.x)*p[1]/1600),q.y-(a.y+(b.y-a.y)*p[0]/1200+(d.y-a.y)*p[1]/1600))<.03})})})()'))
            capture(page,entry,'new-carlisle-chooser');canvas=page.evaluate('window.physicalCanvas=globe.canvas;globe.snapshot()')
            button=page.locator('[data-campus-feature="new-carlisle-edison-2025-roof-central"]');button.focus();page.keyboard.press('Enter');ready(page)
            check(entry+' keyboard roof selection retains the canvas and camera',page.evaluate('globe.canvas===window.physicalCanvas') and page.evaluate('globe.snapshot()')==canvas and page.locator('.campus-feature-inspector h2').inner_text()=='Central long roof')
            check(entry+' roof identity stays positional and capacity unallocated','permit building label not assigned' in page.locator('.campus-feature-inspector').inner_text() and '910 MW' not in page.locator('.campus-feature-inspector').inner_text())
            capture(page,entry,'new-carlisle-feature')
            page.locator('[data-campus-save]').click();check(entry+' feature shelf does not alter starred project IDs',page.evaluate('saved.sourceFeatures.length===1&&saved.favorites.length===0'))
            with page.expect_download() as event:page.locator('.campus-feature-inspector [data-campus-export]').click()
            data=json.loads(Path(event.value.path()).read_text())
            check(entry+' export carries exact feature image and native source IDs',data['feature']['id']=='new-carlisle-edison-2025-roof-central' and data['feature']['observed_at']=='2025' and len(data['image']['native_rasters'])==16 and data['image']['sha256']=='52316a7735481740b973fdb3de07781d20a8c0113b26f2acf20046a9a128087e')
            check(entry+' export excludes invented allocation and embedded image',data['feature']['phase_id'] is None and data['feature']['it_power_mw'] is None and data['feature']['operating_status'] is None and 'data_url' not in data['image'])
            url=page.url;page.reload();ready(page);check(entry+' selected roof and shelf survive reload',page.locator('.campus-feature-inspector h2').inner_text()=='Central long roof' and page.locator('[data-campus-save]').inner_text()=='★ Feature saved')
            page.locator('.campus-feature-inspector [data-campus-source]').click();page.locator('.campus-native-rasters>summary').click()
            check(entry+' source drawer exposes tile IDs year precision and other component','in2025_10752345_3in' in page.locator('#drawer-content').inner_text() and 'exact mosaic day not established' in page.locator('#drawer-content').inner_text() and 'SR2 / IEC-3' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');check(entry+' source return retains selected roof URL',page.url==url)
            page.evaluate('navigate("watchlist")');page.locator('[data-campus-reopen]').click();ready(page)
            check(entry+' saved source feature reopens the physical inspector',page.locator('.campus-feature-inspector h2').inner_text()=='Central long roof')
            page.evaluate('navigate("watchlist")')
            with page.expect_download() as event:page.locator('[data-action="export-session"]').click()
            session=json.loads(Path(event.value.path()).read_text());check(entry+' session export keeps typed source feature references',session['sourceFeatures'][0]['type']=='source_feature' and session['favorites']==[])
            check(entry+' stale or unknown shelf references are rejected on import',page.evaluate('ATLAS.campus.importShelf([{type:"source_feature",project_id:"amazon-anthropic-new-carlisle",feature_id:"unknown-roof",image_sha256:"0".repeat(64)}]).length===0'))
            page.locator('[data-campus-reopen]').click();ready(page)
            for width,height in ((1024,768),(768,1024),(390,844),(320,844)):
                page.set_viewport_size({'width':width,'height':height});ready(page)
                if width<=640 and page.locator('[data-workspace-inspector]').get_attribute('aria-expanded')!='true':page.locator('[data-workspace-inspector]').click()
                check(entry+f' {width}px selected identity remains legible',page.locator('.campus-feature-inspector').is_visible() and page.locator('.campus-feature-inspector').evaluate('e=>e.getBoundingClientRect().width')>250 and page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                capture(page,entry,f'new-carlisle-{width}')
                if width<=640:
                    for mode in ('aerial','oblique'):
                        page.locator(f'[data-campus-mode="{mode}"]').click();ready(page)
                        check(entry+f' {width}px {mode} compass clears roof date and controls',page.evaluate('''(()=>{const g=globe,c=g.compassRect,l=g.labelRect,b=g.canvas.getBoundingClientRect(),overlap=(a,d)=>a.x<d.x+d.width&&a.x+a.width>d.x&&a.y<d.y+d.height&&a.y+a.height>d.y;return c&&l&&!overlap(c,l)&&c.x>=0&&c.y>=0&&c.x+c.width<=g.w&&c.y+c.height<=g.h&&[...document.querySelectorAll('.campus-scene-head,.campus-historic-badge,.campus-scene-foot,.campus-spatial-hero .atlas-map-tools,.workspace-toolbar')].filter(e=>e.getClientRects().length).every(e=>{const r=e.getBoundingClientRect();return !overlap(c,{x:r.x-b.x,y:r.y-b.y,width:r.width,height:r.height});});})()'''))
                        capture(page,entry,f'new-carlisle-{width}-{mode}')
                    page.locator('[data-campus-mode="aerial"]').click();ready(page)
            page.set_viewport_size({'width':1440,'height':1080});page.goto(base+entry+'#overview?scale=metro&site=amazon-anthropic-new-carlisle');ready(page,False)
            check(entry+' metro frame follows Chicago to New Carlisle',page.evaluate('globe.bounds[2]-globe.bounds[0]<2&&globe.bounds[3]-globe.bounds[1]<1') and page.locator('.atlas-map-head h2').inner_text()=='Chicago–New Carlisle')
            check(entry+' nearby context names its separate 250km scope','250 km' in page.locator('.atlas-map-head p').inner_text() and 'outside the frame' in page.locator('.workspace-map-context').inner_text())
            capture(page,entry,'corridor')
            page.evaluate('globe.bounds=globe.bounds.map((x,i)=>x+(i%2?0:8));globe.dirty=true');ready(page,False)
            check(entry+' offscreen selected anchor has explicit locate',page.locator('.workspace-selection-notice').is_visible() and page.locator('[data-workspace-locate]').is_visible())
            span=page.evaluate('[globe.bounds[2]-globe.bounds[0],mercatorY(globe.bounds[3])-mercatorY(globe.bounds[1]),globe.zoom]');page.locator('[data-workspace-locate]').click();ready(page,False)
            check(entry+' locate translates camera without changing map scale',page.evaluate('(()=>{const old='+json.dumps(span)+';return Math.abs(globe.bounds[2]-globe.bounds[0]-old[0])<1e-9&&Math.abs(mercatorY(globe.bounds[3])-mercatorY(globe.bounds[1])-old[1])<1e-9&&globe.zoom===old[2]})()'))
            page.locator('[data-campus-locate-scene]').click();ready(page,False)
            check(entry+' reviewed scene locate preserves archival source anchors',page.evaluate('globe.bounds[2]-globe.bounds[0]<.02') and page.evaluate('JSON.stringify(D.sites.map(s=>[s.id,s.lon,s.lat]))')==anchors)
            page.goto(base+entry+'#overview?scale=facility&site=coreweave-helios&energy=1&selection=context&energyfeature=osm-way-1490401522&feature=helios-naip2022-roof-01&claim=helios-phase2-it');ready(page)
            check(entry+' context selection overrides competing feature and claim route',page.evaluate('ATLAS.workspace.activeSelection().type==="context"') and 'selection=context' in page.url and '&feature=' not in page.url and '&claim=' not in page.url)
            page.locator('.energy-feature-inspector [data-energy-source]').click()
            check(entry+' utility review keeps native missing voltage independent','Not tagged' in page.locator('#drawer-content').inner_text() and '345 kV · operator statement' in page.locator('#drawer-content').inner_text() and 'Native tags remain unchanged' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');page.locator('[data-campus-feature]').click();ready(page)
            check(entry+' explicit roof selection clears context identity',page.evaluate('ATLAS.workspace.activeSelection().type==="feature"&&ATLAS.layers.state.feature===null'))
            page.goto(base+entry+'#site/coreweave-helios');page.wait_for_function('window.ATLAS_BOOTSTRAPPING===false&&document.documentElement.classList.contains("layers-ready")')
            check(entry+' direct archival dossier works with retained physical scale',page.locator('#drawer').is_visible() and 'Helios' in page.locator('#drawer-content').inner_text() and page.url.endswith('#site/coreweave-helios'))
            page.reload();page.wait_for_function('window.ATLAS_BOOTSTRAPPING===false&&document.documentElement.classList.contains("layers-ready")')
            check(entry+' direct archival dossier survives reload',page.locator('#drawer').is_visible() and 'Helios' in page.locator('#drawer-content').inner_text())
            check(entry+' no uncaught physical journey errors',not errors)
            ctx.close()
        browser.close()
finally:
    if server:server.shutdown()
(ROOT/'qa/physical_results.json').write_text(json.dumps({'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks},indent=2))
print(f"{sum(c['pass'] for c in checks)}/{len(checks)} passed",flush=True)
raise SystemExit(0 if all(c['pass'] for c in checks) else 1)
