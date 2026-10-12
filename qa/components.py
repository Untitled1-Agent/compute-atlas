"""Reviewed component, version recovery and responsive camera journeys over HTTP."""
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
def ready(page):
    page.wait_for_function('window.ATLAS_BOOTSTRAPPING===false&&document.documentElement.classList.contains("layers-ready")&&globe instanceof CampusScene&&globe.imageReady&&!globe.dirty&&globe.w===globe.canvas.parentElement.clientWidth')
    page.wait_for_timeout(350)
def camera(page):return page.evaluate('campusCameraParam(globe.snapshot())')
def capture(page,entry,name):
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-components-'+name+'.png')))
try:
    with sync_playwright() as driver:
        browser=driver.chromium.launch(executable_path=shutil.which('chromium') or driver.chromium.executable_path,args=['--no-sandbox']+(['--disable-gpu','--no-zygote','--renderer-process-limit=1'] if os.environ.get('ATLAS_LIGHT_BROWSER') else []))
        for entry in ('index.html','compute_atlas.html'):
            ctx=browser.new_context(viewport={'width':1440,'height':1080},accept_downloads=True);page=ctx.new_page();page.set_default_timeout(120000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry+'#overview?scale=facility&site=coreweave-helios');ready(page)
            check(entry+' direct selected roof is framed at a useful scale',page.evaluate('(()=>{const g=globe,p=g.features[0].polygons[0][0].map(v=>g.project3(...v));return Math.max(...p.map(q=>q.x))-Math.min(...p.map(q=>q.x))>g.w*.65})()'))
            print(entry,'FIRST_CITED_SOURCE',page.locator('.atlas-compact-sources>.atlas-document-row').first.bounding_box(),flush=True)
            check(entry+' first cited source fits the desktop overview',page.locator('.atlas-compact-sources>.atlas-document-row').first.evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight'))
            capture(page,entry,'helios-desktop')
            page.goto(base+entry+'#overview?scale=facility&site=amazon-anthropic-new-carlisle');ready(page)
            anchors=page.evaluate('JSON.stringify(D.sites.map(s=>[s.id,s.lon,s.lat]))')
            edison='new-carlisle-edison-2025';sr2='new-carlisle-sr2-2025';roof='new-carlisle-sr2-2025-roof-west-upper'
            check(entry+' project exposes its two separate reviewed components',page.locator('[data-campus-component] option').count()==2 and page.evaluate('globe.manifest.id')==edison)
            page.locator('[data-campus-feature="new-carlisle-edison-2025-roof-central"]').click();ready(page)
            page.locator('[data-campus-mode="oblique"]').click();ready(page);page.locator('#globe-canvas').focus();page.keyboard.press('Shift+ArrowRight');ready(page)
            edison_camera=camera(page)
            page.locator('[data-campus-component]').select_option(sr2);ready(page)
            check(entry+' SR2 decodes the independently pinned image',page.evaluate('globe.manifest.id==="new-carlisle-sr2-2025"&&globe.image.naturalWidth===1200&&globe.image.naturalHeight===1000&&globe.manifest.image.sha256==="5e81f60be78dceda1ef8cdb8026f7d01d1afe2c10a81b42887dcb7a4defe0714"'))
            check(entry+' every SR2 roof has geometry and a hit surface',page.evaluate('globe.features.length===5&&globe.hitSurfaces.length===5&&globe.features.every(f=>globe.manifest.features.some(s=>s.id===f.record.id))'))
            check(entry+' component change requires explicit roof selection',page.evaluate('campusState.feature===null&&ATLAS.workspace.activeSelection().type==="project"') and page.locator('.campus-project-inspector').is_visible())
            check(entry+' five-roof chooser includes an explicit empty state',page.locator('.campus-feature-strip [data-campus-feature-select] option').count()==6 and page.locator('.campus-feature-strip [data-campus-feature-select]').input_value()=='')
            capture(page,entry,'chooser')
            page.locator('[data-campus-mode="aerial"]').click();ready(page);before=camera(page);page.evaluate('window.componentCanvas=globe.canvas')
            page.locator('.campus-project-inspector [data-campus-feature-select]').select_option(roof);ready(page)
            check(entry+' keyboard chooser retains the source canvas and camera',page.evaluate('globe.canvas===window.componentCanvas') and camera(page)==before and page.locator('.campus-feature-inspector h2').inner_text()=='West upper roof')
            check(entry+' replaced inspector retains focus on the persistent chooser',page.evaluate('document.activeElement===document.querySelector(".campus-feature-strip [data-campus-feature-select]")'))
            version=page.evaluate('campusFeature().review_sha256')
            check(entry+' share identifies scene image and interpretation versions',page.evaluate('(()=>{const p=new URLSearchParams(location.hash.split("?")[1]),m=campusScene(),f=campusFeature();return p.get("scene")===m.id&&p.get("imageversion")===m.image.sha256&&p.get("featureversion")===f.review_sha256&&p.get("selection")==="feature"})()'))
            check(entry+' source-outline fact does not invent height or allocation','about 20,000 m²' in page.locator('.campus-feature-inspector').inner_text() and page.evaluate('campusFeature().height_m===null&&campusFeature().phase_id===null&&campusFeature().it_power_mw===null&&campusFeature().operating_status===null'))
            page.locator('[data-campus-frame="feature"]').click();ready(page);selected=camera(page)
            check(entry+' selected framing fits a large visible roof',page.evaluate('(()=>{const g=globe,f=g.features.find(f=>f.selected),p=f.polygons[0][0].map(v=>g.project3(...v));return Math.max(...p.map(q=>q.x))-Math.min(...p.map(q=>q.x))>200&&p.every(q=>q.x>=0&&q.x<=g.w&&q.y>=g.labelMinY&&q.y<g.h-70)})()'))
            page.locator('[data-campus-frame="context"]').click();ready(page)
            check(entry+' context framing restores the whole registered image',camera(page)!=selected and page.evaluate('globe.imageCorners.map(p=>globe.project3(...p)).every(q=>q.x>=0&&q.x<=globe.w&&q.y>=globe.labelMinY&&q.y<globe.h-65)'))
            page.locator('[data-campus-frame="feature"]').click();ready(page);page.locator('#globe-canvas').focus();page.keyboard.press('Shift+ArrowDown');page.keyboard.press('-');ready(page);sr2_camera=camera(page)
            check(entry+' new camera carries the explicit source-image focus',len(sr2_camera.split(','))==7 and page.evaluate('campusCameraParse(campusCameraParam(globe.snapshot())).pitch===Math.PI/2'))
            page.locator('[data-campus-component]').select_option(edison);ready(page)
            check(entry+' returning component restores its roof view and camera',camera(page)==edison_camera and page.evaluate('campusState.feature==="new-carlisle-edison-2025-roof-central"&&campusState.mode==="oblique"'))
            page.locator('[data-campus-component]').select_option(sr2);ready(page)
            check(entry+' SR2 retains its independent Aerial camera and identity',camera(page)==sr2_camera and page.evaluate('campusState.feature==="new-carlisle-sr2-2025-roof-west-upper"&&campusState.mode==="aerial"'))
            page.reload();ready(page)
            check(entry+' versioned SR2 share survives a full reload',camera(page)==sr2_camera and page.evaluate('campusScene().id==="new-carlisle-sr2-2025"&&campusFeature().review_sha256==='+json.dumps(version)))
            stage=page.evaluate('globe.h');page.locator('.campus-spatial-hero [data-atlas-action="expand"]').click();ready(page)
            check(entry+' expanded component map uses the remaining panel height',page.evaluate('globe.h')>stage and page.locator('.atlas-map-panel').evaluate('e=>e.classList.contains("atlas-map-expanded")'))
            page.locator('.campus-spatial-hero [data-atlas-action="expand"]').click();ready(page)
            check(entry+' closing expanded map retains source camera and selection',page.evaluate('globe.h')==stage and camera(page)==sr2_camera and page.evaluate('campusFeature().id==='+json.dumps(roof)))
            page.locator('.campus-view-toggle [data-campus-mode="evidence"]').click()
            check(entry+' phase evidence retains the separate component identity',page.evaluate('campusScene().id==="new-carlisle-sr2-2025"&&ATLAS.workspace.activeSelection().type==="claim"') and page.locator('.campus-component-evidence-header').is_visible())
            page.locator('[data-campus-mode="physical"]').click();ready(page)
            check(entry+' phase return restores reviewed roof and exact camera',camera(page)==sr2_camera and page.evaluate('ATLAS.workspace.activeSelection().type==="feature"'))
            page.locator('.campus-feature-inspector [data-campus-source]').click();page.locator('.campus-native-rasters>summary').click()
            check(entry+' provenance exposes twenty native records and separate dates',page.locator('.campus-native-rasters .atlas-data-row').count()==20 and 'exact mosaic day not established' in page.locator('#drawer-content').inner_text() and version in page.locator('#drawer-content').inner_text() and 'not surveyed' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
            with page.expect_download() as event:page.locator('.campus-feature-inspector [data-campus-export]').click()
            data=json.loads(Path(event.value.path()).read_text())
            check(entry+' cited export carries exact component and review provenance',data['scene_id']==sr2 and data['review_sha256']==version and len(data['image']['native_rasters'])==20 and data['feature']['derived_outline_area']['rounded_m2']==20000 and 'data_url' not in data['image'])
            page.locator('[data-campus-save]').click()
            check(entry+' shelf binds review version without starring the parent',page.evaluate('saved.sourceFeatures.length===1&&saved.sourceFeatures[0].scene_id==="new-carlisle-sr2-2025"&&saved.sourceFeatures[0].review_sha256==='+json.dumps(version)+'&&saved.favorites.length===0'))
            page.locator('.campus-feature-strip [data-campus-feature-select]').select_option('');ready(page)
            check(entry+' empty chooser clears identity without resetting the canvas',camera(page)==sr2_camera and page.evaluate('ATLAS.workspace.activeSelection().type==="project"&&globe.features.every(f=>!f.selected)') and page.locator('[data-campus-frame="feature"]').is_disabled())
            page.locator('.campus-feature-strip [data-campus-feature-select]').select_option(roof);ready(page)
            for width,height in ((1440,1080),(1366,768),(1024,768),(768,1024),(390,844),(320,844)):
                page.set_viewport_size({'width':width,'height':height});ready(page);page.locator('[data-campus-frame="feature"]').click();ready(page)
                check(entry+f' {width}px reserves a usable drawing stage',page.evaluate('globe.h>=300&&document.documentElement.scrollWidth<=innerWidth+1') and page.locator('.campus-component-header').evaluate('e=>e.getBoundingClientRect().bottom<=document.querySelector("#globe-canvas").getBoundingClientRect().top'))
                check(entry+f' {width}px orientation clears roof date and controls',page.evaluate('''(()=>{const g=globe,c=g.compassRect,l=g.labelRect,b=g.canvas.getBoundingClientRect(),overlap=(a,d)=>a.x<d.x+d.width&&a.x+a.width>d.x&&a.y<d.y+d.height&&a.y+a.height>d.y;return c&&l&&!overlap(c,l)&&c.x>=0&&c.y>=0&&c.x+c.width<=g.w&&c.y+c.height<=g.h&&[...document.querySelectorAll('.campus-component-header,.campus-historic-badge,.campus-scene-foot,.campus-spatial-hero .atlas-map-tools,.workspace-toolbar')].filter(e=>e.getClientRects().length).every(e=>{const r=e.getBoundingClientRect();return !overlap(c,{x:r.x-b.x,y:r.y-b.y,width:r.width,height:r.height});});})()'''))
                capture(page,entry,str(width))
                if width<=390:
                    page.locator('.campus-feature-inspector').scroll_into_view_if_needed();page.screenshot(path=str(OUT/(entry+'-components-inspector-'+str(width)+'.png')))
            page.set_viewport_size({'width':1440,'height':1080})
            stale=base+entry+'#overview?scale=facility&site=amazon-anthropic-new-carlisle&scene='+sr2+'&selection=feature&feature='+roof+'&featureversion='+'0'*64+'&scenecamera=0,1.5708,8,300,300,0,0'
            page.goto(stale);ready(page)
            check(entry+' changed review version gets a named recovery without geometry',page.locator('.campus-route-recovery').is_visible() and page.evaluate('campusState.feature===null&&ATLAS.workspace.activeSelection().type==="project"&&globe.zoom!==8') and 'requestedfeatureversion=' in page.url)
            page.locator('[data-campus-recover]').click();ready(page)
            check(entry+' explicit recovery opens the current default component',page.evaluate('campusScene().id==="new-carlisle-edison-2025"&&campusState.recovery===null&&campusState.feature===null') and 'requestedfeatureversion=' not in page.url)
            page.goto(base+entry+'#overview?scale=facility&site=amazon-anthropic-new-carlisle&scene='+sr2+'&feature=new-carlisle-edison-2025-roof-central');ready(page)
            check(entry+' conflicting component feature never silently reopens',page.locator('.campus-route-recovery').is_visible() and page.evaluate('campusState.feature===null&&globe.features.every(f=>!f.selected)'))
            page.goto(base+entry+'#overview?scale=facility&site=amazon-anthropic-new-carlisle&scene=unavailable-component');ready(page)
            reason=page.evaluate('campusState.recovery.reason')
            check(entry+' unavailable component keeps its valid parent identity',reason=='This component is unavailable for the requested project.' and page.evaluate('campusState.recovery.project==="amazon-anthropic-new-carlisle"&&campusState.feature===null'))
            page.reload();ready(page)
            check(entry+' recovery explanation survives canonical URL and reload',page.evaluate('campusState.recovery.reason')==reason and 'requestedscene=unavailable-component' in page.url and page.evaluate('campusState.feature===null'))
            check(entry+' unavailable shelf versions remain bounded identities',page.evaluate('(()=>{const r=ATLAS.campus.importShelf([{type:"source_feature",project_id:"amazon-anthropic-new-carlisle",scene_id:"new-carlisle-sr2-2025",feature_id:"new-carlisle-sr2-2025-roof-west-upper",image_sha256:"0".repeat(64),review_sha256:"0".repeat(64),name:"Prior reviewed roof",geometry:{fake:true},it_power_mw:999}]);return r.length===1&&!campusSavedMatch(r[0])&&r[0].name==="Prior reviewed roof"&&!r[0].geometry&&r[0].it_power_mw===undefined})()'))
            check(entry+' framing and component navigation preserve research anchors',page.evaluate('JSON.stringify(D.sites.map(s=>[s.id,s.lon,s.lat]))')==anchors)
            check(entry+' no uncaught component journey errors',not errors)
            ctx.close()
        browser.close()
finally:
    if server:server.shutdown()
(ROOT/'qa/components_results.json').write_text(json.dumps({'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks},indent=2))
print(f"{sum(c['pass'] for c in checks)}/{len(checks)} passed",flush=True)
raise SystemExit(0 if all(c['pass'] for c in checks) else 1)
