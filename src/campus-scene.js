'use strict';
/* Reviewed historical imagery and interpreted features. Independent of OSM and
 * accepted capacity claims; a source feature never becomes a capacity record. */
const CAMPUS_SCENES=JSON.parse(document.getElementById('campus-scenes').textContent);
const campusState={mode:'aerial',physicalMode:'aerial',feature:null,camera:null,routeCamera:null,viewCameras:{}};
function campusScene(s=spatialDefaultSite()){return CAMPUS_SCENES.scenes.find(x=>x.project_id===s?.id);}
function campusSpatial(){return campusScene()&&state.spatialLevel>=4&&!workspaceState.location&&campusState.mode!=='evidence';}
function campusFeature(){return campusScene()?.features.find(f=>f.id===campusState.feature);}
function campusEnsureSelection(){const m=campusScene();if(m&&state.spatialLevel===5&&campusState.mode!=='evidence'&&!workspaceState.location&&!campusFeature()&&m.features.length===1)campusState.feature=m.features[0].id;}
function workspaceActiveSelection(){const s=spatialDefaultSite(),context=globalThis.ATLAS?.layers?.state?.feature;if(context&&layerOn('energy'))return {type:'context',id:context,project_id:s?.id};if(campusSpatial()&&campusFeature())return {type:'feature',id:campusState.feature,project_id:s?.id};if(state.spatialLevel>=4&&!workspaceState.location&&(campusState.mode==='evidence'||!campusScene())){const claim=s&&workspaceSelected(s);if(claim)return {type:'claim',id:claim.id,project_id:s.id};}return {type:'project',id:s?.id,project_id:s?.id};}
function campusRememberCamera(){if(globe instanceof CampusScene){campusState.camera=globe.snapshot();campusState.physicalMode=globe.campusMode;campusState.viewCameras[globe.campusMode]=campusState.camera;globe.skipCameraSave=true;}}
function campusChangeMode(mode){campusRememberCamera();if(mode==='physical')mode=campusState.physicalMode;campusState.mode=mode;workspaceState.location=false;if(mode!=='evidence'){campusState.physicalMode=mode;campusState.camera=campusState.viewCameras[mode]||null;campusState.routeCamera=null;}campusEnsureSelection();render();history.pushState(null,'',spatialURL());document.querySelector(`[data-campus-mode="${mode}"]`)?.focus({preventScroll:true});}

function campusCameraParse(value){
  const raw=value?.split(',');if(!raw||raw.length!==5||raw.some(x=>x.trim()===''))return null;
  const n=raw.map(Number);if(n.some(x=>!Number.isFinite(x))||Math.abs(n[0])>Math.PI*4||n[1]<.16||n[1]>Math.PI/2+.000005||n[2]<.3||n[2]>8||Math.abs(n[3])>5000||Math.abs(n[4])>5000)return null;
  return {yaw:n[0],pitch:Math.min(n[1],Math.PI/2),zoom:n[2],pan:{x:n[3],y:n[4]}};
}
function campusCameraParam(c){return c?[c.yaw,c.pitch,c.zoom,c.pan.x,c.pan.y].map(x=>Number(x.toFixed(5))).join(','):'';}
class CampusScene extends FacilityScene {
  constructor(canvas,manifest){
    super(canvas,manifest.features[0],manifest.features.slice(1));
    this.campusMode=campusState.mode;this.manifest=manifest;this.showContext=true;this.assumptions=false;this.labels=state.spatialLabels!==false;this.labelBasis='ROOF INTERPRETATION · '+manifest.image.acquired_at;
    const e=manifest.image.extent_3857,R=6378137;
    const ll=(x,y)=>[x/R*180/Math.PI,(2*Math.atan(Math.exp(y/R))-Math.PI/2)*180/Math.PI];
    this.imageCorners=[ll(e.xmin,e.ymax),ll(e.xmax,e.ymax),ll(e.xmin,e.ymin)].map(p=>this.local(...p));
    const [a,b,d]=this.imageCorners,focus=(this.w<500?manifest.image.mobile_focus_pixel:null)||manifest.image.focus_pixel||[manifest.image.width/2,manifest.image.height/2];this.frameCenter=[a[0]+(b[0]-a[0])*focus[0]/manifest.image.width,a[1]+(d[1]-a[1])*focus[1]/manifest.image.height];
    this.extent=Math.max(Math.abs(b[0]-a[0]),Math.abs(d[1]-a[1]))/2;
    this.baseExtent=this.extent;
    this.image=new Image();this.image.onload=()=>{if(this.destroyed)return;this.imageReady=true;this.dirty=true;canvas.dataset.image='ready';const status=document.querySelector('.campus-image-status');if(status)status.hidden=true;};
    this.image.onerror=()=>{if(this.destroyed)return;this.imageReady=false;canvas.dataset.image='error';const status=document.querySelector('.campus-image-status');if(status){status.hidden=false;status.innerHTML='Historical image unavailable. The interpreted outline and source record remain accessible. <button class="text-button" data-campus-retry>Retry image ↻</button>';}this.dirty=true;};
    this.image.src=manifest.image.data_url||new URL(manifest.image.path+'?v='+manifest.image.sha256.slice(0,12),location.href).href;
    this.reset();
    const camera=campusState.routeCamera||campusState.camera;if(camera)Object.assign(this,camera,{pan:{...camera.pan}});
    campusState.routeCamera=null;
    if(campusFeature())this.inspect(campusState.feature,false);else this.features.forEach(f=>f.selected=false);
    this.dirty=true;
  }
  local(lon,lat){const R=6378137,rad=Math.PI/180,merc=x=>Math.log(Math.tan(Math.PI/4+x*rad/2)),k=Math.cos(this.lat*rad);return [R*(lon-this.lon)*rad*k,R*(merc(lat)-merc(this.lat))*k];}
  resize(){super.resize();this.labelMinY=this.w<500?273:122;
    // Keep the rotating north arrow above the phone's roof-label region and
    // beside the dated-image badge, clear of the source caption and controls.
    this.compassPosition=this.w<500?{x:this.w-30,y:this.labelMinY-30}:null;
  }
  // Orthographic ground projection keeps the georeferenced image and outline
  // aligned under pan, zoom and orbit, without making up building heights.
  project3(x,y,z=0){
    x-=this.frameCenter[0];y-=this.frameCenter[1];
    const a=x*Math.cos(this.yaw)-y*Math.sin(this.yaw),b=x*Math.sin(this.yaw)+y*Math.cos(this.yaw),scale=Math.min(this.w*.5,this.h*.5)/this.extent*this.zoom;
    return {x:this.w*.5+this.pan.x+a*scale,y:this.h*.53+this.pan.y-b*Math.sin(this.pitch)*scale-z*Math.cos(this.pitch)*scale,depth:b*Math.cos(this.pitch)-z*Math.sin(this.pitch)};
  }
  drawGround(){
    if(this.imageReady){
      const [a,b,d]=this.imageCorners.map(p=>this.project3(...p)),c=this.ctx,im=this.manifest.image;
      c.save();c.transform((b.x-a.x)/im.width,(b.y-a.y)/im.width,(d.x-a.x)/im.height,(d.y-a.y)/im.height,a.x,a.y);c.drawImage(this.image,0,0,im.width,im.height);c.fillStyle='#05141f35';c.fillRect(0,0,im.width,im.height);c.restore();
    }
    if(typeof localRoadDraw==='function')localRoadDraw(this);
  }
  reset(){this.yaw=campusState.mode==='oblique'?-.32:0;this.pitch=campusState.mode==='oblique'?.84:Math.PI/2;this.zoom=(this.w<500?this.manifest.image.mobile_zoom:null)||this.manifest.image.default_zoom||1.45;this.pan={x:0,y:this.w<500?(this.manifest.image.mobile_pan_y||0):0};this.dirty=true;}
  snapshot(){return {yaw:this.yaw,pitch:this.pitch,zoom:this.zoom,pan:{...this.pan}};}
  inspect(id,notify=true){const result=super.inspect(id,false);if(result&&notify)this.canvas.dispatchEvent(new CustomEvent('atlas-campus-feature',{bubbles:true,detail:{id}}));return result;}
  draw(){super.draw();const readout=document.getElementById('scene-readout');if(readout)readout.textContent=`${Math.round(this.pitch*180/Math.PI)}° tilt · ${this.zoom.toFixed(2)}× · historic ground plane`;
    const value=campusCameraParam(this.snapshot());if(value!==this.publishedCamera){this.publishedCamera=value;clearTimeout(this.cameraTimer);this.cameraTimer=setTimeout(()=>{if(this.destroyed||globe!==this)return;campusState.camera=this.snapshot();workspaceSyncURL();},220);}
  }
  destroy(){if(!this.skipCameraSave){campusState.camera=this.snapshot();campusState.viewCameras[this.campusMode]=campusState.camera;}clearTimeout(this.cameraTimer);super.destroy();this.image.onload=null;this.image.onerror=null;}
}
function campusViewToggle(){return `<div class="workspace-view-toggle campus-view-toggle">${[['aerial','Aerial'],['oblique','Oblique'],['evidence','Evidence']].map(([id,name])=>`<button data-campus-mode="${id}" aria-pressed="${campusState.mode===id&&!workspaceState.location}">${name}</button>`).join('')}<button data-workspace-location="true" aria-pressed="${workspaceState.location}">Location</button></div>`;}
const campusOriginalDiagram=workspacePhaseDiagram;
workspacePhaseDiagram=function(s,level){
  const m=campusScene(s);if(!m)return campusOriginalDiagram(s,level);
  if(!campusSpatial())return campusOriginalDiagram(s,level).replace(/<div class="workspace-view-toggle">[\s\S]*?<\/div>/,campusViewToggle())+`<div class="campus-return-feature"><button class="btn" data-campus-mode="physical">Return to ${esc(campusFeature()?.name||'physical features')} →</button><span>Restore the dated scene and camera</span></div>`;
  return `<section class="campus-spatial-hero" aria-label="Historical campus imagery and interpreted roof">
    <canvas id="globe-canvas" data-campus="${esc(s.id)}" tabindex="0" aria-label="${esc(s.name)} dated aerial. Drag to orbit; Shift and drag to pan; scroll to zoom. Select a roof or use the feature buttons below."></canvas>
    <header class="campus-scene-head"><div><h2>${esc(m.title)}</h2><p>${esc(m.image.short_publisher||'NAIP')} · ${esc(m.image.acquired_at)} · ${esc(m.image.context_label||'predates AI conversion')}</p></div>${campusViewToggle()}</header>
    <div class="campus-image-status" role="status" hidden></div>
    <div class="campus-historic-badge">HISTORICAL IMAGERY <b>${esc(m.image.acquired_at)}</b></div>
    <div class="campus-scene-foot"><span>${esc(m.image.attribution||'USDA NAIP / USGS · Public domain')}</span><button class="text-button" data-campus-source>Image & geometry sources ↗</button><small id="scene-readout"></small></div>
    <div class="atlas-map-tools"><button class="icon-button" data-campus-tool="in" aria-label="Zoom campus in">+</button><button class="icon-button" data-campus-tool="out" aria-label="Zoom campus out">−</button><button class="icon-button" data-atlas-action="expand" aria-label="Expand campus map">⛶</button><button class="icon-button" data-campus-tool="reset" aria-label="Reset campus camera">◎</button></div>
  </section><div class="campus-feature-strip">${m.features.map(f=>`<button data-campus-feature="${esc(f.id)}" aria-pressed="${f.id===campusState.feature}">⌑ ${esc(f.name)} <small>${esc(f.observed_at)} · interpreted</small></button>`).join('')}<span>${m.features.length} reviewed ${m.features.length===1?'roof':'roofs'} · incomplete inventory</span></div><details class="campus-phase-shortcuts" aria-label="Select disclosed phase evidence"><summary>Choose a phase disclosure <span>Separate from roof identity</span></summary><div>${workspacePhases(s).map(r=>`<button data-workspace-phase="${esc(r.id)}" data-site="${esc(s.id)}"><b>${esc(r.scope)}</b> ${fmt(r.value)} ${esc(r.unit)} <small>${esc(r.as_of||'Undated')}</small></button>`).join('')}</div></details>`;
};
function campusIdentityReview(f){return f.identity_reviews?.find(r=>r.status==='reviewed_visual_correspondence');}
function campusSavedShape(r){return r&&r.type==='source_feature'&&site(r.project_id)&&typeof r.feature_id==='string'&&/^[a-z0-9-]{1,140}$/.test(r.feature_id)&&typeof r.image_sha256==='string'&&/^[a-f0-9]{64}$/.test(r.image_sha256);}
function campusSavedMatch(r){const m=CAMPUS_SCENES.scenes.find(m=>m.project_id===r.project_id);return m?.image.sha256===r.image_sha256&&m.features.some(f=>f.id===r.feature_id);}
function campusShelfEntry(f=campusFeature(),m=campusScene()){return f&&m?{type:'source_feature',project_id:m.project_id,feature_id:f.id,image_sha256:m.image.sha256}:null;}
function campusIsSaved(f){return saved.sourceFeatures.some(r=>r.feature_id===f.id&&r.project_id===campusScene().project_id&&campusSavedMatch(r));}
saved.sourceFeatures=Array.isArray(saved.sourceFeatures)?saved.sourceFeatures.filter(campusSavedShape).slice(0,100):[];
function campusFeatureRail(s,f){
 const m=campusScene(s),review=campusIdentityReview(f),roles=primaryRelationships(s).slice(0,4);
 return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent campus-feature-inspector">
  ${atlasKicker('01 / SELECTED PHYSICAL FEATURE')}<div class="atlas-badge-row"><span>Image interpretation</span><span>Geometry ${esc(f.observed_at)}</span></div>
  <h2>${esc(f.name)}</h2><p>${esc(m.component||s.name)} · ${esc(s.location)}</p>
  <div class="campus-feature-boundary">IT allocation<strong>Not established.</strong><small>Project MW is not allocated to this roof</small></div>
  <ol class="campus-takeaways" aria-label="Feature takeaways"><li><b>Geometry observation</b><span>${esc(f.observed_at)} · approximate roof; height not measured</span></li><li><b>${review?'Reviewed physical identity':'Positional identity'}</b><span>${review?'Operator depiction '+esc(review.depiction_period)+' · filed '+esc(review.published_at):'Roof position in '+esc(m.component||s.name)+'; permit building label not assigned'}</span></li><li><b>Current building status</b><span>Not established; phase and IT allocation unreviewed</span></li></ol>
  <div class="workspace-dossier-actions"><button class="btn primary" data-campus-save>${campusIsSaved(f)?'★ Feature saved':'Add feature to shelf +'}</button><button class="text-button" data-campus-export>Export feature ↓</button></div>
  <button class="text-button campus-source-launch" data-campus-source>Source & interpretation ↗</button>
 </section><section class="atlas-insight-card campus-parent-roles">${atlasKicker('02 / PARENT PROJECT COUNTERPARTIES')}
  ${roles.map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} ↗</button>${primaryRef(r.source_id)}</div>`).join('')||`<p>${esc(s.owner_label)} · archival association</p>`}
  <p class="atlas-card-footnote">Roles apply to the parent project. The source image does not allocate a lease or electrical service to this roof.</p>
  <div class="workspace-dossier-actions"><button class="text-button" data-campus-mode="evidence">Inspect phase evidence →</button><button class="text-button" data-workspace-compare="${esc(s.id)}">Compare parent project +</button></div>
  <button class="text-button" data-spatial-action="dossier" data-id="${esc(s.id)}">Full project dossier ↗</button>
 </section></div>`;
}
function campusProjectRail(s){const m=campusScene(s);return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent campus-project-inspector">${atlasKicker('01 / SELECTED CAMPUS')}<h2>${esc(s.name)}</h2><p>${esc(s.location)} · ${esc(s.country)}</p>${atlasRow('Physical evidence',m.features.length+' reviewed roof '+(m.features.length===1?'interpretation':'interpretations'))}${atlasRow('Image observation',esc(m.image.acquired_at))}<p>Inspect a physical feature or a separately dated phase disclosure. Project power scopes remain below the map.</p><div class="workspace-dossier-actions">${m.features.map(f=>`<button class="btn primary" data-campus-open-feature="${esc(f.id)}">Inspect ${esc(f.name)} →</button>`).join('')}<button class="text-button" data-campus-mode="evidence">Phase evidence →</button><button class="text-button" data-workspace-compare="${esc(s.id)}">Compare parent project +</button><button class="text-button" data-spatial-action="dossier" data-id="${esc(s.id)}">Full project dossier ↗</button></div></section><section class="atlas-insight-card">${atlasKicker('02 / COUNTERPARTIES')}${primaryRelationships(s).slice(0,4).map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} ↗</button>${primaryRef(r.source_id)}</div>`).join('')}</section><section class="atlas-insight-card">${atlasKicker('03 / SOURCE COVERAGE')}<h2>Physical identity.<br>Separate evidence.</h2><p>Historical imagery, reviewed identity and phase claims have independent dates. Current imagery and the full physical inventory remain incomplete.</p><button class="text-button" data-campus-source>Image & reviewed identity ↗</button><button class="text-button" data-spatial-action="dossier" data-id="${esc(s.id)}">Full project dossier ↗</button></section></div>`;}
const campusOriginalRail=workspaceRail;
workspaceRail=function(level,scope,s,phase){if(campusScene(s)&&level>=4&&workspaceState.location)return campusProjectRail(s);if(campusSpatial())return campusFeature()?campusFeatureRail(s,campusFeature()):campusProjectRail(s);return campusOriginalRail(level,scope,s,phase);};
const campusOriginalResearchView=workspaceResearchView;
workspaceResearchView=function(){campusEnsureSelection();let html=campusOriginalResearchView();const s=spatialDefaultSite();if(campusScene(s)&&state.spatialLevel>=4)html=html.replace(`<h1>${esc(s.name)}</h1>`,`<h1>${esc(s.name)} Data Center Campus</h1>`);return campusSpatial()?html.replace('Evidence schematic · no surveyed parcels or building footprints','Dated aerial · reviewed roof interpretations · no surveyed parcels or building-to-phase link'):html;};sixScaleGlobeView=workspaceResearchView;globeView=workspaceResearchView;
const campusOriginalMobile=workspaceMobileRail;
workspaceMobileRail=function(level,scope,s,phase){const f=campusSpatial()&&campusFeature();if(!f){if(!campusSpatial()&&!(campusScene(s)&&level>=4&&workspaceState.location))return campusOriginalMobile(level,scope,s,phase);const m=campusScene(s);return `<aside class="atlas-spatial-rail workspace-mobile-rail" data-expanded="${workspaceState.mobileExpanded}" aria-label="Campus project inspection"><button class="workspace-mobile-summary" data-workspace-inspector aria-expanded="${workspaceState.mobileExpanded}" aria-controls="workspace-selection-detail"><span><small>SELECTED CAMPUS</small><strong>${esc(s.name)}</strong><span>${m.features.length} reviewed ${m.features.length===1?'roof':'roofs'} · image ${esc(m.image.acquired_at)}</span></span><span class="workspace-mobile-expand">${workspaceState.mobileExpanded?'Close ↑':'Inspect ↓'}</span></button><div id="workspace-selection-detail">${campusProjectRail(s)}</div></aside>`;}return `<aside class="atlas-spatial-rail workspace-mobile-rail" data-expanded="${workspaceState.mobileExpanded}" aria-label="Historical feature inspection"><button class="workspace-mobile-summary" data-workspace-inspector aria-expanded="${workspaceState.mobileExpanded}" aria-controls="workspace-selection-detail"><span><small>HISTORICAL SOURCE FEATURE</small><strong>${esc(f.name)}</strong><span>${esc(f.observed_at)} · roof interpretation · IT not allocated</span></span><span class="workspace-mobile-expand">${workspaceState.mobileExpanded?'Close ↑':'Inspect ↓'}</span></button><div id="workspace-selection-detail">${campusFeatureRail(s,f)}</div></aside>`;};
const campusOriginalGlobe=AtlasGlobe;
AtlasGlobe=function(canvas){return canvas.dataset.campus?new CampusScene(canvas,campusScene(site(canvas.dataset.campus))):new campusOriginalGlobe(canvas);};
function campusSelectFeature(id){const m=campusScene(),f=m?.features.find(f=>f.id===id);if(!f||!(globe instanceof CampusScene))return;if(ATLAS.layers?.state)ATLAS.layers.state.feature=null;campusState.feature=id;state.spatialLevel=5;globe.inspect(id,false);workspaceState.mobileExpanded=true;
  const scope=spatialScope(5,spatialDefaultSite()),old=document.querySelector('.workspace-mobile-rail');old.outerHTML=workspaceMobileRail(5,scope,spatialDefaultSite(),state.spatialPhase);renderNav();document.querySelectorAll('[data-campus-feature]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.campusFeature===id)));document.querySelectorAll('.atlas-scale-step').forEach(b=>{const selected=b.dataset.id==='5';b.classList.toggle('active',selected);b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});history.pushState(null,'',spatialURL());
}
function campusSourceContent(){
 const m=campusScene(),im=m.image,f=campusFeature(),review=f&&campusIdentityReview(f);
 const rasters=im.native_rasters;
 return `<div class="atlas-eyebrow">DATED IMAGE / REVIEWED INTERPRETATION</div><h1>${esc(m.title)}</h1><p>${esc(m.review.limitations)}</p><h2>Image provenance</h2>
  ${atlasRow('Image observation',esc(im.acquired_at)+(im.date_precision?' · '+esc(im.date_precision):''))}${im.acquisition_range?atlasRow('Project acquisition range',esc(im.acquisition_range.from)+' – '+esc(im.acquisition_range.to)+'<small>'+esc(im.acquisition_range.scope)+'</small>'):''}
  ${atlasRow('Retrieved',esc(sourceUTC(im.captured_at)))}${atlasRow('Publisher',esc(im.publisher))}${atlasRow('License',esc(im.license))}${atlasRow('Native resolution',im.native_resolution_m+' m')}
  ${rasters?`<details class="campus-native-rasters"><summary>Inspect ${rasters.length} pinned native image records</summary>${rasters.map(r=>atlasRow('Raster '+r.OBJECTID,esc(r.Name))).join('')}<p>Native year/county/pixel-size fields were null. Image year and native resolution come from the separately linked project metadata.</p></details>`:atlasRow('Raster',esc(im.raster_name))}
  <p class="campus-source-hash">Derivative SHA-256: ${esc(im.sha256)}</p>
  <p><a href="${esc(im.license_url)}" target="_blank" rel="noopener">Publisher attribution and license ↗</a><br><a href="${esc(im.metadata_url)}" target="_blank" rel="noopener">Native raster metadata ↗</a><br><a href="${esc(im.export_url)}" target="_blank" rel="noopener">Locked raster export and returned georeferenced extent ↗</a>${im.project_metadata_url?`<br><a href="${esc(im.project_metadata_url)}" target="_blank" rel="noopener">Project acquisition dates and reuse terms ↗</a>`:''}</p>
  <h2>Geometry and project match</h2><p>${esc(m.review.basis)}</p><p>Review: ${esc(m.review.reviewed_at)} · historical interpretation accepted. The roof polygon is manually interpreted from this image; it is approximate, not a survey. No present-day operating status, measured height or phase/IT allocation is supplied.</p>
  ${review?`<section class="campus-identity-review"><h2>Separately reviewed physical identity</h2><p>${esc(review.interpretation)}</p>${atlasRow('Operator depiction',esc(review.depiction_period)+' · '+esc(review.depiction_date_precision))}${atlasRow('Source published',esc(review.published_at))}${atlasRow('Identity review',esc(review.reviewed_at)+' · '+esc(review.reviewed_by))}<p>${esc(review.basis)}</p><p>${esc(review.relation_scope)}. The historical geometry has not been verified as current.</p><a href="${esc(review.source_url)}" target="_blank" rel="noopener">${esc(review.locator)} ↗</a></section>`:''}
  ${m.sources.map(s=>`<p><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)} ↗</a></p>`).join('')}
  ${m.review.registry_anchors?.length?`<h3>Registry coordinate boundaries</h3>${m.review.registry_anchors.map(a=>`<p>${esc(a.fac_name)} · FRS ${esc(a.registry_id)}<br>${esc(a.fac_street)}, ${esc(a.fac_city)}, ${esc(a.fac_zip)}<br>${a.fac_lat}, ${a.fac_long} · ${esc(a.fac_collection_method||'Method unavailable')} · reported accuracy ${fmt(a.fac_accuracy_meters)} m</p>`).join('')}`:''}
  ${m.other_components?.length?`<h3>Separate campus components</h3>${m.other_components.map(c=>`<p><b>${esc(c.name)}</b> · ${esc(c.address)}<br>${esc(c.imagery_state)}</p>`).join('')}`:''}
  <p>Original research anchor: ${esc(spatialDefaultSite().lon)}, ${esc(spatialDefaultSite().lat)}. The reviewed image extent and source-feature coordinates are independent; the archival anchor is unchanged.</p>
  <button class="btn" data-campus-export ${f?'':'disabled'}>Export the selected cited feature ↓</button>`;
}

const campusOriginalOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts){campusOriginalOpenDrawer(kind,id,opts);if(kind==='campus-source'){$('#drawer-type').textContent='CAMPUS IMAGE & GEOMETRY';$('#drawer-content').innerHTML=campusSourceContent();}};ATLAS.openDrawer=openDrawer;
document.addEventListener('atlas-campus-feature',e=>campusSelectFeature(e.detail.id));
document.addEventListener('click',event=>{
  const mode=event.target.closest('[data-campus-mode]');if(mode)campusChangeMode(mode.dataset.campusMode);
  const feature=event.target.closest('[data-campus-feature],[data-campus-open-feature]');if(feature){campusSelectFeature(feature.dataset.campusFeature||feature.dataset.campusOpenFeature);document.querySelector(`[data-campus-feature="${feature.dataset.campusFeature||feature.dataset.campusOpenFeature}"]`)?.focus({preventScroll:true});}
  const tool=event.target.closest('[data-campus-tool]');if(tool&&globe instanceof CampusScene){tool.dataset.campusTool==='reset'?globe.reset():globe.zoomTo(globe.zoom*(tool.dataset.campusTool==='in'?1.2:1/1.2));}
  if(event.target.closest('[data-campus-retry]')&&globe instanceof CampusScene){const im=globe.manifest.image;globe.image.src=im.data_url||new URL(im.path+'?v='+im.sha256.slice(0,12)+'&retry='+Date.now(),location.href).href;}
  if(event.target.closest('[data-campus-source]'))openDrawer('campus-source');
  if(event.target.closest('[data-campus-export]')){const m=campusScene(),f=campusFeature()||m.features[0],{data_url,...image}=m.image;download(f.id+'-cited-feature.json',{collection:'Historical campus interpretation; excluded from project and OSM capacity inventories',project_id:m.project_id,feature:f,image,review:m.review,sources:m.sources});}
});
// Set the selection type before the existing phase handler renders its view.
document.addEventListener('click',event=>{if(event.target.closest('[data-workspace-phase]')){campusRememberCamera();campusState.mode='evidence';workspaceState.location=false;}},true);
const campusOriginalURL=spatialURL;
spatialURL=function(view=state.view){
 const url=campusOriginalURL(view);if(!['overview','globe'].includes(view)||!campusScene()||state.spatialLevel<4)return url;
 const p=new URLSearchParams(url.split('?')[1]||''),active=workspaceActiveSelection();p.set('campusview',campusState.mode);p.set('selection',active.type);
 p.delete('feature');p.delete('lastfeature');
 if(active.type==='feature'){p.set('feature',campusState.feature);p.delete('claim');}
 else {if(campusState.feature)p.set('lastfeature',campusState.feature);if(active.type!=='claim')p.delete('claim');}
 if(campusState.physicalMode!=='aerial')p.set('physicalview',campusState.physicalMode);
 const c=globe instanceof CampusScene?globe.snapshot():campusState.camera||campusState.routeCamera;if(c)p.set('scenecamera',campusCameraParam(c));
 return '#'+view+'?'+p.toString();
};
const campusOriginalRoute=routeFromHash;window.removeEventListener('hashchange',campusOriginalRoute);
routeFromHash=function(){if(window.ATLAS_BOOTSTRAPPING)return;
 const [,query='']=location.hash.slice(1).split('?'),p=new URLSearchParams(query),s=site(p.get('site')),m=campusScene(s),type=p.get('selection');if(globe instanceof CampusScene)globe.skipCameraSave=true;
 campusState.mode=['aerial','oblique','evidence'].includes(p.get('campusview'))?p.get('campusview'):p.get('claim')?'evidence':'aerial';
 const requested=p.get('feature')||p.get('lastfeature');campusState.feature=m?.features.some(f=>f.id===requested)?requested:null;
 campusState.physicalMode=p.get('physicalview')==='oblique'||campusState.mode==='oblique'?'oblique':'aerial';
 if(type==='context')campusState.mode=campusState.physicalMode;
 if(type==='feature'&&campusState.feature)campusState.mode=campusState.physicalMode;
 if(type==='claim'&&s&&workspacePhases(s).some(r=>r.id===p.get('claim')))campusState.mode='evidence';
 campusState.camera=null;campusState.routeCamera=campusCameraParse(p.get('scenecamera'));campusState.viewCameras={};if(campusState.routeCamera)campusState.viewCameras[campusState.physicalMode]=campusState.routeCamera;
 campusOriginalRoute();
};window.addEventListener('hashchange',routeFromHash);
const campusOriginalTransition=spatialTransition;
spatialTransition=function(update={}){if(update.selected&&update.selected!==state.spatialSelected){if(globe instanceof CampusScene)globe.skipCameraSave=true;campusState.mode='aerial';campusState.physicalMode='aerial';campusState.feature=null;campusState.camera=null;campusState.routeCamera=null;campusState.viewCameras={};}campusOriginalTransition(update);if(globe instanceof CampusScene)workspaceSyncURL();};
const campusOriginalNav=renderNav;
renderNav=function(){campusEnsureSelection();campusOriginalNav();$('#shelf-count').textContent=saved.favorites.length+(saved.sourceFeatures?.length||0);if(state.spatialLevel===5&&workspaceActiveSelection().type==='project')$('#breadcrumb').textContent=$('#breadcrumb').textContent.replace(/[^›]+$/, ' Choose a physical feature');if(workspaceActiveSelection().type==='feature')$('#breadcrumb').textContent=$('#breadcrumb').textContent.replace(/[^›]+$/, ' '+campusFeature().name);};
ATLAS.campus={scene:campusScene,state:campusState,parseCamera:campusCameraParse,select:campusSelectFeature};ATLAS.workspace.activeSelection=workspaceActiveSelection;
const campusOriginalShelf=watchlistView;
watchlistView=function(){
 let html=campusOriginalShelf();if(!saved.sourceFeatures.length)return html;
 const root=document.createElement('div');root.innerHTML=html;root.querySelector('.empty')?.remove();
 return root.innerHTML+`<section class="panel panel-pad section-gap campus-shelf"><h3>Saved source features</h3><p>Physical feature identities remain separate from starred projects. Changed image versions require a new review.</p>${saved.sourceFeatures.map(r=>{const m=CAMPUS_SCENES.scenes.find(m=>m.project_id===r.project_id),f=m?.features.find(f=>f.id===r.feature_id),current=campusSavedMatch(r);return `<article><div><button class="text-button" data-campus-reopen="${esc(r.feature_id)}" data-project="${esc(r.project_id)}" ${current?'':'disabled'}>${esc(f?.name||r.feature_id)} ↗</button><small>${esc(site(r.project_id)?.name)} · ${esc(f?.observed_at||'Saved source version')}${current?'':' · source version changed; review required'}</small></div><button class="text-button" data-campus-unsave="${esc(r.feature_id)}" data-project="${esc(r.project_id)}">Remove ×</button></article>`;}).join('')}</section>`;
};
function campusImportShelf(rows){return Array.isArray(rows)?rows.filter(campusSavedShape).filter(campusSavedMatch).filter((r,i,a)=>a.findIndex(x=>x.feature_id===r.feature_id&&x.project_id===r.project_id)===i).slice(0,100).map(r=>({type:'source_feature',project_id:r.project_id,feature_id:r.feature_id,image_sha256:r.image_sha256})):[];}
document.addEventListener('click',event=>{
 if(event.target.closest('[data-campus-save]')){const r=campusShelfEntry();if(!r)return;const exists=campusIsSaved(campusFeature());saved.sourceFeatures=saved.sourceFeatures.filter(x=>x.feature_id!==r.feature_id||x.project_id!==r.project_id);if(!exists)saved.sourceFeatures.push(r);save();event.target.closest('[data-campus-save]').textContent=exists?'Add feature to shelf +':'★ Feature saved';toast(exists?'Physical feature removed from shelf.':'Physical feature saved in this browser.');}
 const remove=event.target.closest('[data-campus-unsave]');if(remove){saved.sourceFeatures=saved.sourceFeatures.filter(x=>x.feature_id!==remove.dataset.campusUnsave||x.project_id!==remove.dataset.project);save();render();}
 const reopen=event.target.closest('[data-campus-reopen]');if(reopen&&!reopen.disabled){const r=saved.sourceFeatures.find(x=>x.feature_id===reopen.dataset.campusReopen&&x.project_id===reopen.dataset.project);if(!r||!campusSavedMatch(r))return;location.hash='#overview?scale=facility&site='+encodeURIComponent(r.project_id)+'&campusview=aerial&selection=feature&feature='+encodeURIComponent(r.feature_id);}
});
ATLAS.campus.importShelf=campusImportShelf;
const campusOriginalSelectionRail=workspaceSelectionRail;
workspaceSelectionRail=function(s,scope){const html=campusOriginalSelectionRail(s,scope);return campusScene(s)?html.replace('<button class="text-button" data-workspace-compare=', '<button class="text-button" data-campus-locate-scene>Locate reviewed scene ↗</button><button class="text-button" data-workspace-compare='):html;};
function workspaceSelectionNotice(){
 const root=document.querySelector('.atlas-workspace'),s=spatialDefaultSite();if(!root||!(globe instanceof ResearchMap)||!s||!(state.spatialSelectionActive||state.spatialLevel>=2))return;
 let node=root.querySelector('.workspace-selection-notice');if(!node){node=document.createElement('div');node.className='workspace-selection-notice';node.hidden=true;node.setAttribute('role','status');root.querySelector('.atlas-map-panel')?.append(node);}
 const excluded=!spatialFiltered().some(x=>x.id===s.id);globe.prepare();const p=globe.project(s.lon,s.lat),offscreen=p.z<=.015||p.x<10||p.x>globe.w-10||p.y<64||p.y>globe.h-58;
 const hidden=excluded||layerOn('research')&&!offscreen,changed=node.hidden!==hidden;node.hidden=hidden;
 if(changed){const map=globe;requestAnimationFrame(()=>{if(!map.destroyed&&globe===map)map.dirty=true;});}
 if(!node.hidden)node.innerHTML=layerOn('research')?`Selected project anchor is outside the current map view. <button class="text-button" data-workspace-locate>Locate project anchor →</button>`:`Selected project anchor is hidden by the Research anchors layer. <button class="text-button" data-workspace-show-anchor>Show research anchors →</button>`;
}
document.addEventListener('click',event=>{
 if(event.target.closest('[data-workspace-show-anchor]')){state.spatialResearch=true;if(globe)globe.dirty=true;layerDecorate();workspaceSelectionNotice();workspaceSyncURL();}
 if(event.target.closest('[data-workspace-locate]')&&globe instanceof ResearchMap){const s=spatialDefaultSite(),g=globe;if(g.flat){const [x0,y0,x1,y1]=g.bounds,dy=mercatorY(s.lat)-(mercatorY(y0)+mercatorY(y1))/2,dx=AtlasSpatialMath.longitudeNear(s.lon,(x0+x1)/2)-(x0+x1)/2,inv=y=>(2*Math.atan(Math.exp(y))-Math.PI/2)/geographicRadians;g.bounds=[x0+dx,inv(mercatorY(y0)+dy),x1+dx,inv(mercatorY(y1)+dy)];}else{g.lon=s.lon;g.lat=s.lat;}g.target=null;g.dirty=true;state.spatialCamera[g.cameraKey]=g.snapshot();workspaceSyncURL();}
 if(event.target.closest('[data-campus-locate-scene]')&&globe instanceof ResearchMap){const m=campusScene(),e=m.image.extent_3857,inv=y=>(2*Math.atan(Math.exp(y/6378137))-Math.PI/2)/geographicRadians;globe.flat=true;globe.bounds=[e.xmin/6378137/geographicRadians,inv(e.ymin),e.xmax/6378137/geographicRadians,inv(e.ymax)];globe.zoom=1;globe.target=null;globe.dirty=true;state.spatialCamera[globe.cameraKey]=globe.snapshot();workspaceSyncURL();toast('Framed the reviewed '+m.image.acquired_at+' scene. Archival project anchor unchanged.');}
});

routeFromHash();
// The final map-layer integration marks the complete workspace ready.
