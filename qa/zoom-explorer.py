"""Real-browser checks for the six-scale semantic map explorer."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import json, threading, shutil, sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,ok,detail=None):
    checks.append({'test':name,'pass':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_address[1]}/'
try:
  with sync_playwright() as p:
    exe=shutil.which('chromium') or shutil.which('chromium-browser')
    browser=p.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}),args=['--no-sandbox'])
    for entry in ('index.html','compute_atlas.html'):
      page=browser.new_page(viewport={'width':1500,'height':1000});errors=[];external=[]
      page.on('pageerror',lambda e:errors.append(str(e)))
      page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(base) else None)
      res=page.goto(base+entry,wait_until='load',timeout=30000)
      page.wait_for_function('window.ATLAS && document.documentElement.classList.contains("atlas-ready")',timeout=30000)
      page.evaluate("ATLAS.navigate('globe')");page.wait_for_selector('.atlas-scale-strip')
      check(entry+' boots six-scale explorer',res.status==200 and page.locator('.atlas-scale-step').count()==6)
      labels=page.locator('.atlas-scale-step b').all_inner_texts();check(entry+' exposes six semantic labels',labels==['World','Continent','Region','Metro','Campus','Facility'],labels)
      for level,label in enumerate(labels):
        page.locator(f'[data-spatial-action="stage"][data-id="{level}"]').click();page.wait_for_timeout(80)
        current=page.evaluate('ATLAS.state.spatialLevel');check(entry+' stage '+label+' selectable',current==level,current)
        check(entry+' '+label+' renders analytical rail',page.locator('.atlas-spatial-rail .atlas-insight-card').count()>0)
      page.locator('[data-spatial-action="stage"][data-id="0"]').click();
      markers=page.locator('.atlas-map-marker').count();check(entry+' world scale renders mapped facilities',markers>=50,markers)
      page.locator('.atlas-map-marker').first.click();page.wait_for_timeout(80);check(entry+' marker drill-down advances semantic scale',page.evaluate('ATLAS.state.spatialLevel')==1)
      page.locator('[data-spatial-action="phase"][data-id="target"]').click();check(entry+' target layer toggles',page.evaluate('ATLAS.state.spatialPhase')=='target')
      page.locator('[data-spatial-action="stage"][data-id="5"]').click();
      text=page.locator('.atlas-evidence-schematic').inner_text();check(entry+' finest scale labels schematic boundary','NOT A PARCEL / BUILDING SURVEY' in text)
      check(entry+' finest scale retains full dossier action',page.locator('[data-spatial-action="dossier"]').count()==1)
      page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);check(entry+' mobile explorer avoids page-wide overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
      check(entry+' has no browser exceptions',not errors,errors)
      if entry=='compute_atlas.html':check(entry+' remains offline/self-contained',not external,external)
      page.close()
    browser.close()
finally:
  server.shutdown();server.server_close()
result={'passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/zoom_explorer_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'total':result['total']},indent=2))
raise SystemExit(0 if result['passed']==result['total'] else 1)
