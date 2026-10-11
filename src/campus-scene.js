'use strict';
/* Reviewed historical imagery and interpreted features. Independent of OSM and
 * accepted capacity claims; a source feature never becomes a capacity record. */
const CAMPUS_SCENES=JSON.parse(document.getElementById('campus-scenes').textContent);
const campusState={mode:'aerial',feature:null,camera:null,routeCamera:null};
function campusScene(s=spatialDefaultSite()){return CAMPUS_SCENES.scenes.find(x=>x.project_id===s?.id);}
function campusSpatial(){return campusScene()&&state.spatialLevel>=4&&!workspaceState.location&&campusState.mode!=='evidence';}
function campusFeature(){return campusScene()?.features.find(f=>f.id===campusState.feature);}
function campusCameraParse(value){
  const raw=value?.split(',');if(!raw||raw.length!==5||raw.some(x=>x.trim()===''))return null;
  const n=raw.map(Number);if(n.some(x=>!Number.isFinite(x))||Math.abs(n[0])>Math.PI*4||n[1]<.16||n[1]>Math.PI/2||n[2]<.3||n[2]>8||Math.abs(n[3])>5000||Math.abs(n[4])>5000)return null;
  return {yaw:n[0],pitch:n[1],zoom:n[2],pan:{x:n[3],y:n[4]}};
}
function campusCameraParam(c){return c?[c.yaw,c.pitch,c.zoom,c.pan.x,c.pan.y].map(x=>Number(x.toFixed(5))).join(','):'';}
class CampusScene extends FacilityScene {
  constructor(canvas,manifest){
    super(canvas,manifest.features[0],manifest.features.slice(1));
    this.manifest=manifest;this.showContext=true;this.assumptions=false;this.labelBasis='ROOF INTERPRETATION · 2022';
    const e=manifest.image.extent_3857,R=6378137;
    const ll=(x,y)=>[x/R*180/Math.PI,(2*Math.atan(Math.exp(y/R))-Math.PI/2)*180/Math.PI];
    this.imageCorners=[ll(e.xmin,e.ymax),ll(e.xmax,e.ymax),ll(e.xmin,e.ymin)].map(p=>this.local(...p));
    const [a,b,d]=this.imageCorners;this.frameCenter=[(b[0]+a[0])/2,(d[1]+a[1])/2];
    this.extent=Math.max(Math.abs(b[0]-a[0]),Math.abs(d[1]-a[1]))/2;
    this.baseExtent=this.extent;
    this.image=new Image();this.image.onload=()=>{if(this.destroyed)return;this.imageReady=true;this.dirty=true;canvas.dataset.image='ready';const status=document.querySelector('.campus-image-status');if(status)status.hidden=true;};
    this.image.onerror=()=>{if(this.destroyed)return;this.imageReady=false;canvas.dataset.image='error';const status=document.querySelector('.campus-image-status');if(status){status.hidden=false;status.innerHTML='Historical image unavailable. The interpreted outline and source record remain accessible. <button class="text-button" data-campus-retry>Retry image ↻</button>';}this.dirty=true;};
    this.image.src=manifest.image.data_url||new URL(manifest.image.path+'?v='+manifest.image.sha256.slice(0,12),location.href).href;
    this.reset();
    const camera=campusState.routeCamera||campusState.camera;if(camera)Object.assign(this,camera,{pan:{...camera.pan}});
    campusState.routeCamera=null;
    if(campusFeature())this.inspect(campusState.feature,false);
    this.dirty=true;
  }
  local(lon,lat){const R=6378137,rad=Math.PI/180,merc=x=>Math.log(Math.tan(Math.PI/4+x*rad/2)),k=Math.cos(this.lat*rad);return [R*(lon-this.lon)*rad*k,R*(merc(lat)-merc(this.lat))*k];}
  resize(){super.resize();this.labelMinY=this.w<500?273:122;}
  // Orthographic ground projection keeps the georeferenced image and outline
  // aligned under pan, zoom and orbit, without making up building heights.
  project3(x,y,z=0){
    x-=this.frameCenter[0];y-=this.frameCenter[1];
    const a=x*Math.cos(this.yaw)-y*Math.sin(this.yaw),b=x*Math.sin(this.yaw)+y*Math.cos(this.yaw),scale=Math.min(this.w*.5,this.h*.5)/this.extent*this.zoom;
    return {x:this.w*.5+this.pan.x+a*scale,y:this.h*.53+this.pan.y-b*Math.sin(this.pitch)*scale-z*Math.cos(this.pitch)*scale,depth:b*Math.cos(this.pitch)-z*Math.sin(this.pitch)};
  }
  drawGround(){
    if(!this.imageReady)return;
    const [a,b,d]=this.imageCorners.map(p=>this.project3(...p)),c=this.ctx,im=this.manifest.image;
    c.save();c.transform((b.x-a.x)/im.width,(b.y-a.y)/im.width,(d.x-a.x)/im.height,(d.y-a.y)/im.height,a.x,a.y);c.drawImage(this.image,0,0,im.width,im.height);c.fillStyle='#05141f35';c.fillRect(0,0,im.width,im.height);c.restore();
  }
  reset(){this.yaw=campusState.mode==='oblique'?-.32:0;this.pitch=campusState.mode==='oblique'?.84:Math.PI/2;this.zoom=1.45;this.pan={x:0,y:0};this.dirty=true;}
  snapshot(){return {yaw:this.yaw,pitch:this.pitch,zoom:this.zoom,pan:{...this.pan}};}
  inspect(id,notify=true){const result=super.inspect(id,false);if(result&&notify)this.canvas.dispatchEvent(new CustomEvent('atlas-campus-feature',{bubbles:true,detail:{id}}));return result;}
  draw(){super.draw();const readout=document.getElementById('scene-readout');if(readout)readout.textContent=`${Math.round(this.pitch*180/Math.PI)}° tilt · ${this.zoom.toFixed(2)}× · historic ground plane`;
    const value=campusCameraParam(this.snapshot());if(value!==this.publishedCamera){this.publishedCamera=value;clearTimeout(this.cameraTimer);this.cameraTimer=setTimeout(()=>{if(this.destroyed||globe!==this)return;campusState.camera=this.snapshot();workspaceSyncURL();},220);}
  }
  destroy(){if(!this.skipCameraSave)campusState.camera=this.snapshot();clearTimeout(this.cameraTimer);super.destroy();this.image.onload=null;this.image.onerror=null;}
}
function campusViewToggle(){return `<div class="workspace-view-toggle campus-view-toggle">${[['aerial','Aerial'],['oblique','Oblique'],['evidence','Evidence']].map(([id,name])=>`<button data-campus-mode="${id}" ${id==='evidence'?'data-workspace-location="false"':''} aria-pressed="${campusState.mode===id&&!workspaceState.location}">${name}</button>`).join('')}<button data-workspace-location="true" aria-pressed="${workspaceState.location}">Location</button></div>`;}
const campusOriginalDiagram=workspacePhaseDiagram;
workspacePhaseDiagram=function(s,level){
  const m=campusScene(s);if(!m)return campusOriginalDiagram(s,level);
  if(!campusSpatial())return campusOriginalDiagram(s,level).replace(/<div class="workspace-view-toggle">[\s\S]*?<\/div>/,campusViewToggle());
  return `<section class="campus-spatial-hero" aria-label="Historical campus imagery and interpreted roof">
    <canvas id="globe-canvas" data-campus="${esc(s.id)}" tabindex="0" aria-label="Helios historical aerial. Drag to orbit; Shift and drag to pan; scroll to zoom. Select the historical roof or use the feature button below."></canvas>
    <header class="campus-scene-head"><div><h2>${esc(m.title)}</h2><p>NAIP · ${esc(m.image.acquired_at)} · predates AI conversion</p></div>${campusViewToggle()}</header>
    <div class="campus-image-status" role="status" hidden></div>
    <div class="campus-historic-badge">HISTORICAL IMAGERY <b>${esc(m.image.acquired_at)}</b></div>
    <div class="campus-scene-foot"><span>USDA NAIP / USGS · Public domain</span><button class="text-button" data-campus-source>Image & geometry sources ↗</button><small id="scene-readout"></small></div>
    <div class="atlas-map-tools"><button class="icon-button" data-campus-tool="in" aria-label="Zoom campus in">+</button><button class="icon-button" data-campus-tool="out" aria-label="Zoom campus out">−</button><button class="icon-button" data-atlas-action="expand" aria-label="Expand campus map">⛶</button><button class="icon-button" data-campus-tool="reset" aria-label="Reset campus camera">◎</button></div>
  </section><div class="campus-feature-strip">${m.features.map(f=>`<button data-campus-feature="${esc(f.id)}" aria-pressed="${f.id===campusState.feature}">⌑ ${esc(f.name)} <small>${esc(f.observed_at)} · interpreted</small></button>`).join('')}<span>One historical roof · incomplete inventory</span></div><div class="campus-phase-shortcuts" aria-label="Select disclosed phase evidence">${workspacePhases(s).map(r=>`<button data-workspace-phase="${esc(r.id)}" data-site="${esc(s.id)}"><b>${esc(r.scope)}</b> ${fmt(r.value)} ${esc(r.unit)} <small>${esc(r.as_of||'Undated')}</small></button>`).join('')}<span>Phase scopes are separate from roof identity</span></div>`;
};
function campusFeatureRail(s,f){const m=campusScene(s);return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent campus-feature-inspector">${atlasKicker('01 / HISTORICAL SOURCE FEATURE')}<div class="atlas-badge-row"><span>Image interpretation</span><span>${esc(f.observed_at)}</span></div><h2>${esc(f.name)}</h2><p>${esc(s.name)} · ${esc(s.location)}</p><div class="campus-feature-boundary">IT allocation<br><strong>Not established.</strong></div>${atlasRow('Geometry', 'Approximate historical roof')}${atlasRow('Height','Not measured')}${atlasRow('Current building status','Not established')}<p>${esc(f.derivation)}. The imagery predates the AI conversion.</p><div class="workspace-dossier-actions"><button class="btn primary" data-campus-source>Source & interpretation ↗</button><button class="text-button" data-campus-export>Export feature ↓</button></div></section><section class="atlas-insight-card">${atlasKicker('02 / PARENT PROJECT')}<h2>${esc(s.name)}</h2><p>Read separately dated capacity scopes and counterparties. No project MW is allocated to this roof.</p><button class="text-button" data-campus-mode="evidence">Inspect phase evidence →</button><button class="text-button" data-spatial-action="dossier" data-id="${esc(s.id)}">Full project dossier ↗</button></section><section class="atlas-insight-card">${atlasKicker('03 / COVERAGE')}<h2>One roof.<br>A dated interpretation.</h2><p>Partial historical geometry. Current imagery, complete buildings, parcel boundaries and building-to-phase links remain unreviewed.</p><button class="text-button" data-campus-source>Review the source match ↗</button></section></div>`;}
const campusOriginalRail=workspaceRail;
workspaceRail=function(level,scope,s,phase){if(campusSpatial()&&campusFeature())return campusFeatureRail(s,campusFeature());const html=campusOriginalRail(level,scope,s,phase);return campusSpatial()?html.replace('Surveyed building geometry is not established for this dossier.','One historical roof interpretation is available; current building inventory and phase links are not established.'):html;};
const campusOriginalResearchView=workspaceResearchView;
workspaceResearchView=function(){let html=campusOriginalResearchView();const s=spatialDefaultSite();if(campusScene(s)&&state.spatialLevel>=4)html=html.replace(`<h1>${esc(s.name)}</h1>`,`<h1>${esc(s.name)} Data Center Campus</h1>`);return campusSpatial()?html.replace('Evidence schematic · no surveyed parcels or building footprints','Historical aerial · one interpreted roof · no surveyed parcels or building-to-phase link'):html;};sixScaleGlobeView=workspaceResearchView;globeView=workspaceResearchView;
const campusOriginalMobile=workspaceMobileRail;
workspaceMobileRail=function(level,scope,s,phase){const f=campusSpatial()&&campusFeature();if(!f)return campusOriginalMobile(level,scope,s,phase);return `<aside class="atlas-spatial-rail workspace-mobile-rail" data-expanded="${workspaceState.mobileExpanded}" aria-label="Historical feature inspection"><button class="workspace-mobile-summary" data-workspace-inspector aria-expanded="${workspaceState.mobileExpanded}" aria-controls="workspace-selection-detail"><span><small>HISTORICAL SOURCE FEATURE</small><strong>${esc(f.name)}</strong><span>${esc(f.observed_at)} · roof interpretation · IT not allocated</span></span><span class="workspace-mobile-expand">${workspaceState.mobileExpanded?'Close ↑':'Inspect ↓'}</span></button><div id="workspace-selection-detail">${campusFeatureRail(s,f)}</div></aside>`;};
const campusOriginalGlobe=AtlasGlobe;
AtlasGlobe=function(canvas){return canvas.dataset.campus?new CampusScene(canvas,campusScene(site(canvas.dataset.campus))):new campusOriginalGlobe(canvas);};
function campusSelectFeature(id){const m=campusScene(),f=m?.features.find(f=>f.id===id);if(!f||!(globe instanceof CampusScene))return;campusState.feature=id;state.spatialLevel=5;globe.inspect(id,false);workspaceState.mobileExpanded=true;
  const scope=spatialScope(5,spatialDefaultSite()),old=document.querySelector('.workspace-mobile-rail');old.outerHTML=workspaceMobileRail(5,scope,spatialDefaultSite(),state.spatialPhase);renderNav();document.querySelectorAll('[data-campus-feature]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.campusFeature===id)));document.querySelectorAll('.atlas-scale-step').forEach(b=>{const selected=b.dataset.id==='5';b.classList.toggle('active',selected);b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});history.pushState(null,'',spatialURL());
}
function campusSourceContent(){const m=campusScene(),im=m.image;return `<div class="atlas-eyebrow">DATED IMAGE / REVIEWED INTERPRETATION</div><h1>${esc(m.title)}</h1><p>${esc(m.review.limitations)}</p><h2>Image provenance</h2>${atlasRow('Captured by NAIP',esc(im.acquired_at))}${atlasRow('Retrieved',esc(im.captured_at))}${atlasRow('Publisher',esc(im.publisher))}${atlasRow('License',esc(im.license))}${atlasRow('Native resolution',im.native_resolution_m+' m')}${atlasRow('Raster',esc(im.raster_name))}<p class="campus-source-hash">SHA-256: ${esc(im.sha256)}</p><p><a href="${esc(im.license_url)}" target="_blank" rel="noopener">USGS NAIP attribution and license ↗</a><br><a href="${esc(im.metadata_url)}" target="_blank" rel="noopener">Original raster metadata ↗</a><br><a href="${esc(im.export_url)}" target="_blank" rel="noopener">Locked raster export and georeferenced extent ↗</a></p><h2>Geometry and project match</h2><p>${esc(m.review.basis)}</p><p>Review: ${esc(m.review.reviewed_at)} · historical interpretation accepted. The roof polygon is manually interpreted from this image; it is approximate, not a survey. No present-day operating status, measured height or phase/IT allocation is supplied.</p>${m.sources.map(s=>`<p><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)} ↗</a></p>`).join('')}<h3>Registry coordinate boundaries</h3>${m.review.registry_anchors.map(a=>`<p>${esc(a.fac_name)} · FRS ${esc(a.registry_id)}<br>${esc(a.fac_street)}, ${esc(a.fac_city)}, ${esc(a.fac_zip)}<br>${a.fac_lat}, ${a.fac_long} · ${esc(a.fac_collection_method||'Method unavailable')} · reported accuracy ${fmt(a.fac_accuracy_meters)} m</p>`).join('')}<button class="btn" data-campus-export>Export the cited historical feature ↓</button>`;}
const campusOriginalOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts){campusOriginalOpenDrawer(kind,id,opts);if(kind==='campus-source'){$('#drawer-type').textContent='CAMPUS IMAGE & GEOMETRY';$('#drawer-content').innerHTML=campusSourceContent();}};ATLAS.openDrawer=openDrawer;
document.addEventListener('atlas-campus-feature',e=>campusSelectFeature(e.detail.id));
document.addEventListener('click',event=>{
  const mode=event.target.closest('[data-campus-mode]');if(mode){campusState.mode=mode.dataset.campusMode;if(globe instanceof CampusScene)globe.skipCameraSave=true;if(campusState.mode==='evidence'){campusState.feature=null;state.spatialLevel=4;}else workspaceState.location=false;campusState.camera=null;campusState.routeCamera=null;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-campus-mode="${campusState.mode}"]`)?.focus({preventScroll:true});}
  const feature=event.target.closest('[data-campus-feature]');if(feature){campusSelectFeature(feature.dataset.campusFeature);document.querySelector(`[data-campus-feature="${feature.dataset.campusFeature}"]`)?.focus({preventScroll:true});}
  const tool=event.target.closest('[data-campus-tool]');if(tool&&globe instanceof CampusScene){tool.dataset.campusTool==='reset'?globe.reset():globe.zoomTo(globe.zoom*(tool.dataset.campusTool==='in'?1.2:1/1.2));}
  if(event.target.closest('[data-campus-retry]')&&globe instanceof CampusScene){const im=globe.manifest.image;globe.image.src=im.data_url||new URL(im.path+'?v='+im.sha256.slice(0,12)+'&retry='+Date.now(),location.href).href;}
  if(event.target.closest('[data-campus-source]'))openDrawer('campus-source');
  if(event.target.closest('[data-campus-export]')){const m=campusScene(),f=campusFeature()||m.features[0],{data_url,...image}=m.image;download(f.id+'-cited-feature.json',{collection:'Historical campus interpretation; excluded from project and OSM capacity inventories',project_id:m.project_id,feature:f,image,review:m.review,sources:m.sources});}
});
// Set the selection type before the existing phase handler renders its view.
document.addEventListener('click',event=>{if(event.target.closest('[data-workspace-phase]')){campusState.mode='evidence';campusState.feature=null;}},true);
const campusOriginalURL=spatialURL;
spatialURL=function(view=state.view){const url=campusOriginalURL(view);if(!['overview','globe'].includes(view)||!campusScene()||state.spatialLevel<4)return url;const p=new URLSearchParams(url.split('?')[1]||'');p.set('campusview',campusState.mode);if(campusState.feature)p.set('feature',campusState.feature);const c=globe instanceof CampusScene?globe.snapshot():campusState.camera||campusState.routeCamera;if(c)p.set('scenecamera',campusCameraParam(c));return '#'+view+'?'+p.toString();};
const campusOriginalRoute=routeFromHash;window.removeEventListener('hashchange',campusOriginalRoute);
routeFromHash=function(){const [,query='']=location.hash.slice(1).split('?'),p=new URLSearchParams(query),s=site(p.get('site')),m=campusScene(s);if(globe instanceof CampusScene)globe.skipCameraSave=true;campusState.mode=['aerial','oblique','evidence'].includes(p.get('campusview'))?p.get('campusview'):p.get('claim')?'evidence':'aerial';campusState.feature=m?.features.some(f=>f.id===p.get('feature'))?p.get('feature'):null;campusState.camera=null;campusState.routeCamera=campusCameraParse(p.get('scenecamera'));campusOriginalRoute();};window.addEventListener('hashchange',routeFromHash);
const campusOriginalTransition=spatialTransition;
spatialTransition=function(update={}){if(update.selected&&update.selected!==state.spatialSelected){if(globe instanceof CampusScene)globe.skipCameraSave=true;campusState.mode='aerial';campusState.feature=null;campusState.camera=null;campusState.routeCamera=null;}campusOriginalTransition(update);if(globe instanceof CampusScene)workspaceSyncURL();};
const campusOriginalNav=renderNav;
renderNav=function(){campusOriginalNav();if(campusSpatial()&&campusFeature())$('#breadcrumb').textContent=$('#breadcrumb').textContent.replace(/[^›]+$/, ' '+campusFeature().name);};
ATLAS.campus={scene:campusScene,state:campusState,parseCamera:campusCameraParse,select:campusSelectFeature};
routeFromHash();
document.documentElement.classList.add('research-ready','atlas-ready','workspace-ready','campus-ready');
