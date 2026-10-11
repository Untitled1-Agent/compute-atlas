"""Dated aerial -> historical roof -> source -> phase, through real entrypoints."""
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
    page.wait_for_function('typeof CampusScene!=="undefined"&&typeof globe!=="undefined"&&globe instanceof CampusScene&&globe.imageReady&&!globe.dirty')
    page.wait_for_timeout(300)
def camera(page):return page.evaluate('globe.snapshot()')
def capture(page,entry,name):
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(entry+'-campus-'+name+'.png')),full_page=True)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox']+(['--disable-gpu','--no-zygote','--renderer-process-limit=1'] if os.environ.get('ATLAS_LIGHT_BROWSER') else []))
        for entry in ('index.html','compute_atlas.html'):
            page=browser.new_page(viewport={'width':1440,'height':1080});page.set_default_timeout(120000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios');page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            page.evaluate("ATLAS.spatial.select('coreweave-helios');ATLAS.spatial.setLevel(4)");ready(page)
            check(entry+' campus decodes a pinned real aerial',page.locator('[data-campus]').get_attribute('data-image')=='ready' and page.evaluate('globe.image.naturalWidth===1200&&globe.image.naturalHeight===1000'))
            check(entry+' date and historical boundary are visible','2022-09-05' in page.locator('.campus-historic-badge').inner_text() and 'predates AI conversion' in page.locator('.campus-scene-head').inner_text())
            check(entry+' public-domain attribution is on canvas','USDA NAIP / USGS · Public domain' in page.locator('.campus-scene-foot').inner_text())
            check(entry+' plan outline aligns with its georeferenced image',page.evaluate('(()=>{const g=globe,[a,b,d]=g.imageCorners.map(p=>g.project3(...p)),f=g.features[0],pixel=g.manifest.features[0].pixel_vertices[0],q=g.project3(...f.polygons[0][0][0]);const x=a.x+(b.x-a.x)*pixel[0]/1200+(d.x-a.x)*pixel[1]/1000,y=a.y+(b.y-a.y)*pixel[0]/1200+(d.y-a.y)*pixel[1]/1000;return Math.hypot(q.x-x,q.y-y)<.03})()'))
            capture(page,entry,'aerial')
            page.evaluate('window.campusCanvas=globe.canvas');before=camera(page)
            # Select the actual roof surface rather than a synthetic marker.
            point=page.evaluate('(()=>{const g=globe,q=g.project3(...g.local(g.record.lon,g.record.lat)),r=g.canvas.getBoundingClientRect();return {x:r.left+q.x,y:r.top+q.y}})()');page.mouse.click(point['x'],point['y']);ready(page)
            check(entry+' roof click selects a feature without replacing canvas',page.evaluate('globe.canvas===window.campusCanvas&&state.spatialLevel===5') and page.locator('.campus-feature-inspector h2').inner_text()=='Original long roof')
            check(entry+' roof selection retains camera',camera(page)==before)
            check(entry+' feature inspector does not allocate project IT','Not established.' in page.locator('.campus-feature-boundary').inner_text() and '133 MW' not in page.locator('.campus-feature-inspector').inner_text())
            check(entry+' feature selection updates breadcrumb and scale','Original long roof' in page.locator('#breadcrumb').inner_text() and page.locator('.atlas-scale-step.active').get_attribute('data-id')=='5')
            check(entry+' feature source and height boundaries are explicit','2022-09-05' in page.locator('.campus-feature-inspector').inner_text() and 'Not measured' in page.locator('.campus-feature-inspector').inner_text())
            capture(page,entry,'roof')
            with page.expect_download() as event:page.locator('.campus-feature-inspector [data-campus-export]').click()
            export=json.loads(Path(event.value.path()).read_text())
            check(entry+' feature export retains geometry date hash and citations',export['feature']['observed_at']=='2022-09-05' and len(export['feature']['geometry']['coordinates'][0][0])==5 and len(export['image']['sha256'])==64 and len(export['sources'])==5)
            check(entry+' export excludes private data invented heights and phase MW','private_note' not in export and 'data_url' not in export['image'] and export['feature']['height_m'] is None and export['feature']['phase_id'] is None and export['feature']['it_power_mw'] is None)
            oldurl=page.url;oldcam=camera(page);page.locator('.campus-feature-inspector [data-campus-source]').click()
            check(entry+' source drawer explains match and registry accuracy','17,483 m' in page.locator('#drawer-content').inner_text() and 'not a survey' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
            check(entry+' source return restores exact feature URL and camera',page.url==oldurl and camera(page)==oldcam)
            page.locator('.workspace-map-context [data-atlas-action="source-context"]').click()
            check(entry+' map context distinguishes image interpretation from archive anchors',page.locator('#drawer-content [data-campus-source]').is_visible() and 'Separately reviewed historical imagery' in page.locator('#drawer-content').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
            page.locator('[data-workspace-topic="technical"]').click();ready(page)
            check(entry+' topic retains selected feature and camera',page.locator('.campus-feature-inspector').is_visible() and camera(page)==oldcam and page.locator('[data-workspace-topic-content="technical"]').is_visible())
            page.locator('[data-campus-mode="oblique"]').click();ready(page)
            check(entry+' oblique mode changes ground projection without fake height',page.evaluate('globe.pitch<1.5&&globe.features.every(f=>globe.height(f)===0)'))
            check(entry+' oblique outline stays aligned to image',page.evaluate('(()=>{const g=globe,[a,b,d]=g.imageCorners.map(p=>g.project3(...p)),v=g.manifest.features[0].pixel_vertices[2],q=g.project3(...g.features[0].polygons[0][0][2]);return Math.hypot(q.x-(a.x+(b.x-a.x)*v[0]/1200+(d.x-a.x)*v[1]/1000),q.y-(a.y+(b.y-a.y)*v[0]/1200+(d.y-a.y)*v[1]/1000))<.03})()'))
            page.locator('#globe-canvas').focus();page.keyboard.press('ArrowRight');page.keyboard.press('Shift+ArrowDown');page.keyboard.press('+');ready(page)
            moved=camera(page);share=page.url;page.reload();ready(page)
            restored=camera(page)
            check(entry+' shared orbit pan and zoom restore',all(abs(restored[k]-moved[k])<.00002 for k in ('yaw','pitch','zoom')) and restored['pan']==moved['pan'] and 'feature=helios-naip2022-roof-01' in page.url)
            check(entry+' shared topic and oblique view restore','campusview=oblique' in page.url and page.locator('[data-workspace-topic-content="technical"]').is_visible())
            capture(page,entry,'oblique')
            page.locator('[data-campus-tool="reset"]').click();ready(page)
            check(entry+' reset retains feature but restores camera',page.evaluate('campusState.feature==="helios-naip2022-roof-01"&&globe.zoom===1.45&&globe.pan.x===0&&globe.pan.y===0'))
            page.locator('[data-workspace-phase="helios-phase2-it"]').click()
            check(entry+' phase selection switches to a distinct evidence view',page.locator('.workspace-selected-phase h2').inner_text()=='Phase II' and page.locator('.campus-feature-inspector').count()==0 and page.locator('.atlas-evidence-schematic').is_visible())
            phase=page.url;page.reload();page.wait_for_function('document.documentElement.classList.contains("workspace-ready")')
            check(entry+' phase link remains evidence after reload',page.locator('.workspace-selected-phase h2').inner_text()=='Phase II' and page.evaluate('campusState.mode')=='evidence')
            page.go_back();ready(page)
            check(entry+' Back restores the prior roof and aerial view',page.locator('.campus-feature-inspector').is_visible() and page.evaluate('campusState.mode')=='oblique')
            page.locator('[data-campus-mode="aerial"]').click();ready(page)
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844});ready(page)
                # Keyboard/list parity and phone selection expansion.
                page.locator('[data-campus-feature]').focus();page.keyboard.press('Enter');ready(page)
                check(entry+f' phone {width} list selects and expands inspector',page.locator('.campus-feature-inspector').is_visible() and page.locator('[data-workspace-inspector]').get_attribute('aria-expanded')=='true')
                check(entry+f' phone {width} summary retains image date and allocation boundary','2022-09-05' in page.locator('.workspace-mobile-summary').inner_text() and 'IT not allocated' in page.locator('.workspace-mobile-summary').inner_text())
                page.evaluate('window.scrollTo(0,0)')
                check(entry+f' phone {width} view controls are exposed',page.locator('[data-campus-mode="oblique"]').evaluate('e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest("button")===e}') and page.locator('[data-campus-mode="aerial"]').evaluate('e=>e.getBoundingClientRect().height>=44'))
                check(entry+f' phone {width} has no page overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                capture(page,entry,f'phone-{width}')
                page.locator('.campus-feature-inspector [data-campus-source]').click();page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
                check(entry+f' phone {width} source return keeps feature expanded',page.locator('.campus-feature-inspector').is_visible())
            page.set_viewport_size({'width':1366,'height':768});ready(page);capture(page,entry,'short-desktop')
            page.evaluate("globe.image.src='data:image/jpeg;base64,bm90LWFuLWltYWdl'")
            page.wait_for_function('globe.canvas.dataset.image==="error"')
            check(entry+' image decode failure leaves source selection usable',page.locator('.campus-image-status').is_visible() and page.locator('[data-campus-feature]').is_visible() and page.locator('.campus-feature-inspector').is_visible())
            fallback_cam=camera(page);page.locator('[data-campus-retry]').click();ready(page)
            check(entry+' image retry restores imagery and retains selection camera',page.locator('.campus-image-status').is_hidden() and page.locator('.campus-feature-inspector').is_visible() and camera(page)==fallback_cam)
            page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios&scenecamera=NaN,99,-1,Infinity,0&feature=unknown');ready(page)
            check(entry+' invalid shared scene safely falls back',page.evaluate('globe.zoom===1.45&&campusState.feature===null&&Number.isFinite(globe.yaw)'))
            page.evaluate("ATLAS.spatial.select('tencent-qingyuan');ATLAS.spatial.setLevel(4)")
            check(entry+' unavailable campuses retain native evidence fallback',page.locator('.campus-spatial-hero').count()==0 and page.locator('.workspace-native').is_visible())
            check(entry+' historical feature leaves inventories unchanged',page.evaluate('D.sites.length===79&&CATALOG.records.length===5265'))
            check(entry+' no uncaught campus errors',not errors)
            page.close()
        browser.close()
finally:
    if server:server.shutdown();server.server_close()
result={'passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/campus_results.json').write_text(json.dumps(result,indent=2))
print(f"{result['passed']}/{result['total']} passed",flush=True)
raise SystemExit(0 if result['passed']==result['total'] else 1)
