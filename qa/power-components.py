"""Component-specific native electricity, exact versions and physical return over HTTP."""
import json,os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode,urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('ATLAS_TEST_OUT',ROOT/'qa/screenshots'));OUT.mkdir(parents=True,exist_ok=True)
collections=json.loads((ROOT/'data/layers/campus-power.json').read_text())['collections'];checks=[]
def check(name,ok):
    checks.append({'test':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
base=os.environ.get('ATLAS_TEST_BASE');server=None
if not base:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
def ready(page,physical=True):
    page.wait_for_function('document.documentElement.classList.contains("layers-ready")&&globe&&!globe.dirty&&!globe.target&&Math.abs(globe.w-globe.canvas.parentElement.clientWidth)<1')
    if physical:page.wait_for_function('globe instanceof CampusScene&&globe.imageReady')
    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
def camera(page):return page.evaluate('campusCameraParam(globe.snapshot())')
def shot(page,entry,name):
    # Keep six-size visual evidence once; both entrypoints still run every assertion.
    if entry=='index.html':page.screenshot(path=str(OUT/('power-'+name+'.png')))
try:
 with sync_playwright() as driver:
    browser=driver.chromium.launch(executable_path=shutil.which('chromium') or driver.chromium.executable_path,args=['--no-sandbox'])
    for entry in ['index.html','compute_atlas.html']:
        ctx=browser.new_context(viewport={'width':1440,'height':1080},accept_downloads=True);page=ctx.new_page();page.set_default_timeout(120000)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+entry+'#overview?scale=campus&site=amazon-anthropic-new-carlisle');ready(page)
        baseline=page.evaluate('JSON.stringify([D.sites,CATALOG.records,ATLAS_PRIMARY.observations])')
        check(entry+' electricity is opt-in on each physical component',page.evaluate('!ATLAS.layers.on("energy")&&globe.energyPaths.length===0'))
        selected_routes=[]
        for c in collections:
            page.locator('[data-campus-component]').select_option(c['scene_id']);ready(page)
            page.locator('[data-campus-frame="context"]').click();ready(page)
            framed=page.evaluate('''(()=>{const [a,b,d]=globe.imageCorners,p=[a,b,d,[b[0]+d[0]-a[0],b[1]+d[1]-a[1]]].map(p=>globe.project3(...p));return {height:Math.max(...p.map(p=>p.y))-Math.min(...p.map(p=>p.y)),top:Math.min(...p.map(p=>p.y)),bottom:Math.max(...p.map(p=>p.y)),canvas:globe.h};})()''')
            check(entry+' '+c['scene_id']+' full image has a useful unobscured inspection size',framed['height']>=250 and framed['top']>=70 and framed['bottom']<=framed['canvas']-65)
            page.locator('[data-layer-open]').first.click();page.locator('[data-map-layer="energy"]').check()
            check(entry+' '+c['scene_id']+' layer panel lists all three independently attributed captures',page.locator('.energy-collection-card').count()==3 and c['title'] in page.locator('.energy-collection-card.current').inner_text())
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden');ready(page)
            check(entry+' '+c['scene_id']+' draws only its own native collection',page.evaluate('(id)=>globe.energyPaths.length>0&&globe.energyPaths.every(r=>r.collection.id===id)',c['id']))
            check(entry+' '+c['scene_id']+' retains dated image and independent mapping capture','2025' in page.locator('.campus-historic-badge').inner_text() and '2026-10-11' in page.locator('.energy-legend').inner_text())
            roof=page.evaluate('campusScene().features[0].id')
            if page.locator('[data-campus-feature-select]').count():page.locator('[data-campus-feature-select]').first.select_option(roof)
            else:page.locator('[data-campus-feature="'+roof+'"]').click()
            ready(page);page.locator('[data-campus-frame="context"]').click();ready(page)
            # Test roof-first hit priority where a utility target shares a roof point.
            priority=page.evaluate('''(()=>{const surface=globe.hitSurfaces.find(s=>s.feature.record.id===campusState.feature),ring=surface.rings[0],x=ring.reduce((n,p)=>n+p.x,0)/ring.length,y=ring.reduce((n,p)=>n+p.y,0)/ring.length,paths=globe.energyPaths,f=paths[0].feature,r=globe.canvas.getBoundingClientRect();globe.energyPaths=[{feature:f,pts:[{x:x-12,y},{x:x+12,y}],closed:false}];const native=energyHit(globe,x,y),hit=globe.hit({clientX:r.left+x,clientY:r.top+y});globe.energyPaths=paths;return !!native&&hit?.record.id===campusState.feature&&!hit.energy;})()''')
            check(entry+' '+c['scene_id']+' overlapping utility hit cannot replace roof identity',priority)
            native=page.evaluate('''(()=>{const r=globe.canvas.getBoundingClientRect();for(const row of globe.energyPaths)for(let i=1;i<row.pts.length;i++){const pair=AtlasSpatialMath.clipScreenSegment(row.pts[i-1],row.pts[i],globe.w,globe.h);if(!pair)continue;const x=(pair[0].x+pair[1].x)/2,y=(pair[0].y+pair[1].y)/2;if(x<20||x>globe.w-20||y<90||y>globe.h-85)continue;const hit=globe.hit({clientX:r.left+x,clientY:r.top+y});if(hit?.energy)return {x,y,id:hit.record.id};}return null;})()''')
            if native:
                box=page.locator('#globe-canvas').bounding_box();page.mouse.click(box['x']+native['x'],box['y']+native['y']);ready(page)
                check(entry+' '+c['scene_id']+' actual native path click selects its captured object',page.evaluate('energyState.feature')==native['id'] and page.evaluate('energyState.collection')==c['id'])
                page.locator('[data-energy-clear]').click();ready(page)
            else:check(entry+' '+c['scene_id']+' actual native path click selects its captured object',False)
            before=camera(page);page.evaluate('window.powerCanvas=globe.canvas')
            f=next(f for f in c['features'] if ';' in f['tags'].get('voltage',''))
            page.locator('[data-layer-open]').first.click();page.locator('.map-layer-feature-list summary').click()
            page.locator('[data-energy-feature="'+f['id']+'"]').focus();page.keyboard.press('Enter');ready(page)
            check(entry+' '+c['scene_id']+' keyboard native selection preserves roof camera and canvas',page.evaluate('globe.canvas===window.powerCanvas&&campusState.feature')==roof and camera(page)==before)
            check(entry+' '+c['scene_id']+' semicolon voltage stays separate from IT allocation','345 kV / 345 kV' in page.locator('.energy-feature-inspector').inner_text() and 'not IT power' in page.locator('.energy-feature-inspector').inner_text())
            check(entry+' '+c['scene_id']+' selected utility cannot frame the remembered roof',page.locator('[data-campus-frame="feature"]').is_disabled())
            route=page.url;selected_routes.append(route);q=parse_qs(urlsplit(route).fragment.split('?',1)[1])
            check(entry+' '+c['scene_id']+' share binds collection capture native object and physical return',q.get('energycollection')==[c['id']] and q.get('energyversion')==[c['response_sha256']] and q.get('energyobjectversion')==[str(f['version'])] and 'physicalreturn' in q)
            page.go_back();ready(page)
            check(entry+' '+c['scene_id']+' Back restores independent roof selection',page.evaluate('energyState.feature===null&&campusState.feature')==roof)
            page.go_forward();ready(page)
            check(entry+' '+c['scene_id']+' Forward restores exact native identity',page.evaluate('energyState.feature')==f['id'] and page.evaluate('energyState.collection')==c['id'])
            page.reload();ready(page)
            check(entry+' '+c['scene_id']+' reload preserves native identity and roof return camera',page.evaluate('energyState.feature')==f['id'] and page.evaluate('campusState.feature')==roof and camera(page)==before)
            shot(page,entry,c['scene_id']+'-aerial')
            page.locator('.energy-feature-inspector [data-energy-source]').click()
            source=page.locator('#drawer-content').inner_text()
            check(entry+' '+c['scene_id']+' source shows native way capture hash mixed dates and node revisions',str(f['osm_id']) in source and c['response_sha256'] in source and '2025 aerial' in source and page.locator('.energy-native-nodes summary').count()==1 and page.locator('a:has-text("Immutable captured XML")').count()==1)
            page.locator('.energy-native-nodes summary').click()
            check(entry+' '+c['scene_id']+' node order versions and coordinates remain reconstructable',page.evaluate('energySourceFeature().referenced_node_versions.map(n=>[n.osm_id,n.version,n.coordinates])')==[[n['osm_id'],n['version'],n['coordinates']] for n in f['referenced_node_versions']])
            shot(page,entry,c['scene_id']+'-source')
            with page.expect_download() as event:page.locator('#drawer-content [data-energy-export]').click()
            exported=json.loads(Path(event.value.path()).read_text());sv=exported['source_version']
            check(entry+' '+c['scene_id']+' export retains full native paths and exact selected version',exported['features']==c['features'] and exported['license']=='ODbL-1.0' and sv=={'collection_id':c['id'],'response_sha256':c['response_sha256'],'feature_id':f['id'],'native_version':f['version']})
            page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
            check(entry+' '+c['scene_id']+' closing source returns to the exact selected route',page.url==route)
            page.locator('[data-campus-mode="oblique"]').click();ready(page)
            check(entry+' '+c['scene_id']+' oblique retains matching native selection',page.evaluate('energyState.feature')==f['id'] and page.evaluate('(id)=>globe.energyPaths.length>0&&globe.energyPaths.every(r=>r.collection.id===id)',c['id']))
            shot(page,entry,c['scene_id']+'-oblique')
            return_camera=camera(page)
            page.locator('[data-layer-open]').first.click();page.locator('[data-layer-coverage]').click();ready(page,False)
            check(entry+' '+c['scene_id']+' capture explorer preserves selected native object and physical return',page.evaluate('globe instanceof ResearchMap&&state.spatialLevel===3&&energyState.feature')==f['id'] and page.evaluate('!!energyState.returnPhysical'))
            page.locator('[data-energy-clear]').click();ready(page)
            check(entry+' '+c['scene_id']+' Return physical restores component roof view and latest camera',page.evaluate('globe.manifest.id')==c['scene_id'] and page.evaluate('campusState.feature')==roof and page.evaluate('campusState.mode')=='oblique' and camera(page)==return_camera)
            check(entry+' '+c['scene_id']+' returning from utility re-enables roof framing',not page.locator('[data-campus-frame="feature"]').is_disabled())
        # Changing components keeps the opt-in layer but clears the old source identity.
        page.goto(selected_routes[0]);ready(page);edison_camera=camera(page)
        page.locator('[data-campus-component]').select_option(collections[1]['scene_id']);ready(page)
        check(entry+' switching component keeps layer on and clears old utility identity',page.evaluate('ATLAS.layers.on("energy")&&energyState.feature===null&&energyState.recovery===null') and page.evaluate('(id)=>globe.energyPaths.every(r=>r.collection.id===id)',collections[1]['id']))
        page.locator('[data-campus-component]').select_option(collections[0]['scene_id']);ready(page)
        check(entry+' returning component restores its prior roof and camera',page.evaluate('campusState.feature')== 'new-carlisle-edison-2025-roof-west' and camera(page)==edison_camera)
        page.goto(base+entry+'#overview?scale=campus&site=coreweave-helios&energy=1');ready(page)
        page.locator('[data-layer-open]').first.click();page.locator('[data-energy-collection-source="'+collections[1]['id']+'"]').click()
        page.locator('.map-layer-feature-list summary').click();target=collections[1]['features'][0]
        page.locator('[data-energy-feature="'+target['id']+'"]').click();ready(page)
        check(entry+' selecting another collection opens its matching physical component',page.evaluate('globe.manifest.id')==collections[1]['scene_id'] and page.evaluate('energyState.collection')==collections[1]['id'] and page.evaluate('energyState.feature')==target['id'])
        # Malformed links preserve the first recovery reason and original identity on reload.
        original=dict((k,v[0]) for k,v in parse_qs(urlsplit(selected_routes[0]).fragment.split('?',1)[1]).items())
        for field,value,reason in [('energycollection','missing-capture','collection is unavailable'),('energyversion','0'*64,'capture version is unavailable'),('energyfeature','osm-way-missing','feature is unavailable'),('energyobjectversion','99999','object version is unavailable'),('physicalreturn','#overview?scale=facility&scene=missing','physical return')]:
            q={**original,field:value};page.goto(base+entry+'#overview?'+urlencode(q));ready(page)
            text=page.locator('.energy-route-recovery').inner_text()
            check(entry+' '+field+' gives named recovery without substituting current object',reason in text and page.evaluate('energyState.feature===null') and page.evaluate('energyState.recovery') is not None)
            page.reload();ready(page)
            check(entry+' '+field+' recovery and requested identity survive rewrite and reload',page.locator('.energy-route-recovery').inner_text()==text and page.evaluate('energyState.feature===null'))
            page.locator('[data-energy-recover]').click();ready(page)
            check(entry+' '+field+' explicit recovery opens context without arbitrary selection',page.locator('.energy-route-recovery').count()==0 and page.evaluate('energyState.feature===null'))
        wrong={**original,'scene':collections[1]['scene_id']};wrong.pop('imageversion',None);wrong.pop('featureversion',None);wrong.pop('lastfeature',None);wrong.pop('physicalreturn',None)
        page.goto(base+entry+'#overview?'+urlencode(wrong));ready(page)
        check(entry+' different component capture is rejected with named association recovery','different bounded component' in page.locator('.energy-route-recovery').inner_text() and page.evaluate('energyState.feature===null'))
        page.goto(selected_routes[1]);ready(page)
        for width,height in [(1440,1080),(1366,768),(1024,1080),(768,1080),(390,844),(320,844)]:
            page.set_viewport_size({'width':width,'height':height});ready(page)
            check(entry+f' {width}px native source inspector and physical controls fit',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('.energy-feature-inspector').count()==1 and page.locator('[data-campus-frame="feature"]').is_disabled())
            shot(page,entry,'sr2-'+str(width))
        page.set_viewport_size({'width':320,'height':844});ready(page);page.locator('[data-layer-open]').first.click()
        check(entry+' phone native collection list fits and preserves accessible controls',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('.energy-collection-card').count()==3)
        shot(page,entry,'sr2-phone-layers');page.keyboard.press('Escape');page.locator('#drawer').wait_for(state='hidden')
        check(entry+' source overlay leaves project and capacity inventories unchanged',page.evaluate('JSON.stringify([D.sites,CATALOG.records,ATLAS_PRIMARY.observations])')==baseline)
        check(entry+' native electricity journeys have no uncaught errors',not errors)
        ctx.close()
    browser.close()
finally:
 if server:server.shutdown()
result={'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)}
(ROOT/'qa/power_components_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(str(result['passed'])+'/'+str(result['total'])+' passed',flush=True)
raise SystemExit(0 if result['passed']==result['total'] else 1)
