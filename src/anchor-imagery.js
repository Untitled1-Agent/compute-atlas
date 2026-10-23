"use strict";
/* Dated, licensed imagery is geographic context. It does not assign buildings to projects. */
const GEO_IMAGERY = JSON.parse(document.getElementById('anchor-imagery-data').textContent);
const geoImageryCache = new Map();
function geoImageryFor(record) {
  if (!record?.mapped) return null;
  if (geoImageryCache.has(record.id)) return geoImageryCache.get(record.id);
  const candidates=GEO_IMAGERY.records.filter(r=>r.status==='captured');
  const exact=candidates.find(r=>r.anchor.ids.includes(record.id));
  const nearby=candidates.filter(r=>spatialDistance(r.anchor,record)<.6).sort((a,b)=>spatialDistance(a.anchor,record)-spatialDistance(b.anchor,record))[0];
  const result=exact||nearby||null;geoImageryCache.set(record.id,result);return result;
}
function geoImageryMetadata(capture) {
  if(!capture)return null;
  const {native_capture,...metadata}=capture;
  return {...metadata,image:Object.fromEntries(Object.entries(capture.image).filter(([k])=>k!=='data_url'))};
}
async function geoCheckedBytes(path, sha256) {
  const response=await fetch(new URL(path+'?v='+sha256.slice(0,12),location.href),{signal:AbortSignal.timeout(20000)});
  if(!response.ok)throw new Error('Source HTTP '+response.status);
  const bytes=new Uint8Array(await response.arrayBuffer());
  if(globalThis.crypto?.subtle){const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');if(hash!==sha256)throw new Error('Source checksum mismatch');}
  return bytes;
}
// Use the same Mercator ground plane for the raster and native outline coordinates.
UnifiedFacilityScene.prototype.local=CampusScene.prototype.local;
UnifiedFacilityScene.prototype.project3=CampusScene.prototype.project3;
const geoNativeSetContext=UnifiedFacilityScene.prototype.setContext;
UnifiedFacilityScene.prototype.setContext=function(enabled){geoNativeSetContext.call(this,enabled);if(geoImageryFor(uaRecord(this.record.id))){this.extent=Math.max(300,this.extent);this.baseExtent=this.extent;}};
const geoNativeHeight=UnifiedFacilityScene.prototype.height;
UnifiedFacilityScene.prototype.height=function(feature){return uaState.mode==='3d'?geoNativeHeight.call(this,feature):0;};
const geoNativeGround=UnifiedFacilityScene.prototype.drawGround;
UnifiedFacilityScene.prototype.drawGround=function(){
  if(this.groundImageReady&&uaState.mode!=='plan'){
    const [a,b,d]=this.groundImageCorners.map(p=>this.project3(...p)),im=this.groundCapture.image,c=this.ctx;
    c.save();c.transform((b.x-a.x)/im.width,(b.y-a.y)/im.width,(d.x-a.x)/im.height,(d.y-a.y)/im.height,a.x,a.y);
    c.filter='saturate(.55) brightness(.72)';c.drawImage(this.groundImage,0,0,im.width,im.height);c.restore();
  }
  geoNativeGround.call(this);
};
const geoNativeDestroy=UnifiedFacilityScene.prototype.destroy;
UnifiedFacilityScene.prototype.destroy=function(){if(this.groundObjectURL)URL.revokeObjectURL(this.groundObjectURL);geoNativeDestroy.call(this);};
async function geoMountImage(scene,capture) {
  scene.groundCapture=capture;scene.canvas.dataset.groundImage='loading';
  const im=capture.image,e=im.extent_3857,lon=x=>x/6378137*180/Math.PI,lat=y=>Math.atan(Math.sinh(y/6378137))*180/Math.PI;
  scene.groundImageCorners=[[e.xmin,e.ymax],[e.xmax,e.ymax],[e.xmin,e.ymin]].map(([x,y])=>scene.local(lon(x),lat(y)));
  const badge=document.createElement('div');badge.className='geo-image-date';badge.setAttribute('role','status');badge.textContent='Loading dated aerial context…';scene.canvas.parentElement.append(badge);
  const attribution=$('.ua-map-attribution');attribution.innerHTML=catalogLink(im.license_url,im.publisher+' · '+im.license)+'<button class="text-button" data-ua-context-source>Image & map provenance →</button>';
  try {
    let url=im.data_url;
    if(!url){const bytes=await geoCheckedBytes(im.path,im.sha256);if(scene.destroyed)return;url=scene.groundObjectURL=URL.createObjectURL(new Blob([bytes],{type:'image/jpeg'}));}
    const image=new Image();scene.groundImage=image;
    await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error('Image decode failed'));image.src=url;});
    if(scene.destroyed)return;scene.groundImageReady=true;scene.canvas.dataset.groundImage='ready';scene.dirty=true;
    badge.textContent=(uaState.mode==='plan'?'Aerial source available · ':'Aerial context · ')+im.acquired_at;
  }catch(error){if(scene.destroyed)return;scene.canvas.dataset.groundImage='error';badge.dataset.state='error';badge.textContent='Aerial context unavailable · native outlines retained';badge.title=error.message;badge.style.pointerEvents='auto';}
}
const geoImageryMount=uaMount;
uaMount=function(){geoImageryMount();if(globe instanceof UnifiedFacilityScene){const capture=geoImageryFor(uaRecord(uaState.selected));if(capture&&(!uaState.scene||uaState.scene==='anchor-'+capture.id)){if(uaState.scene)$('#ua-context-status').textContent='Native outlines and independently captured surroundings';geoMountImage(globe,capture);}}};
const geoImageMap=uiMap;
uiMap=function(record,rows,physical,scenes){
  let html=geoImageMap(record,rows,physical,scenes);
  const capture=physical&&geoImageryFor(record);
  if(capture&&!scenes.length)html=html.replace(/(<div class="ua-mode-tabs">[\s\S]*?)(<\/div>)/,(_,a,b)=>a+`<button data-ua-mode="aerial" aria-pressed="${uaState.mode==='aerial'}">Satellite</button>`+b);
  if(capture&&scenes.length){const id='anchor-'+capture.id,option=`<option value="${id}" ${uaState.scene===id?'selected':''}>NAIP geographic context · ${esc(capture.image.acquired_at)}</option>`;html=html.replace(/<option selected value="anchor-[^"]+">Requested image unavailable<\/option>/,'').replace(/(<select data-ua-scene>[\s\S]*?)(<\/select>)/,(_,a,b)=>a+option+b);}
  return html;
};
const geoImageVersions=uiSourceVersions;
uiSourceVersions=function(){const versions=geoImageVersions(),capture=geoImageryFor(uaRecord(uaState.selected));if(uaState.scale>=4&&!versions.imageversion&&capture&&(!CAMPUS_SCENES.scenes.some(s=>s.project_id===uaState.selected)||uaState.scene==='anchor-'+capture.id))versions.imageversion=capture.image.sha256;return versions;};
const geoImageDossier=uiCompactDossier;
uiCompactDossier=function(record,rows){let html=geoImageDossier(record,rows);const capture=geoImageryFor(record),reviewed=CAMPUS_SCENES.scenes.some(s=>s.project_id===record.id&&(!uaState.scene||s.id===uaState.scene));if(uaState.scale>=4&&capture&&!reviewed)html=html.replace('</dl>',`<div><dt>Aerial context</dt><dd>${esc(capture.image.acquired_at)}</dd></div></dl>`);return html;};
const geoImageSource=uaContextSource;
uaContextSource=function(){
  geoImageSource();
  $('#drawer-content').insertAdjacentHTML('beforeend',`<h2>Aerial context library</h2><p>${GEO_IMAGERY.records.filter(r=>r.status==='captured').length} captured US windows around published source coordinates. Each retains original image bytes, acquisition dates and raster metadata. Other locations retain their available native outlines and mapped context.</p><button class="btn" data-geo-image-library>Browse all aerial captures →</button><button class="btn" data-geo-image-manifest>Export imagery manifest ↓</button>`);
  const capture=geoImageryFor(uaRecord(uaState.selected));if(!capture||globe instanceof UnifiedCampusScene)return;
  const im=capture.image;
  $('#drawer-content').insertAdjacentHTML('afterbegin',`<section class="geo-imagery-source"><div class="eyebrow">DATED AERIAL CONTEXT</div><h2>The source beneath this view.</h2><p>${esc(GEO_IMAGERY.policy)}</p><dl><dt>Image acquisition</dt><dd>${esc(im.acquired_at)}</dd><dt>Publisher & reuse</dt><dd>${esc(im.publisher)} · ${esc(im.license)}</dd><dt>Native source resolution</dt><dd>${im.native_resolution_m.map(n=>esc(n)+' m').join(' / ')} · display export ${im.width} × ${im.height}</dd><dt>Captured window</dt><dd>1.8 × 1.35 km around a published source coordinate, not a campus boundary.</dd><dt>Native rasters</dt><dd>${capture.selected_raster_ids.join(', ')}</dd></dl><p class="ua-source-code">Image SHA-256: ${im.sha256}</p>${catalogLink(im.license_url,'Reuse terms','btn')}${catalogLink(capture.query_url,'Native raster catalog','btn')}<button class="btn" data-geo-image-export>Export image provenance ↓</button><button class="btn" data-geo-image-download>Download native image ↓</button></section>`);
};
function geoImageLibrary(){
  openDrawer('aerial-context-library');$('#drawer-type').textContent='DATED PHYSICAL SOURCES';
  $('#drawer-content').innerHTML=`<div class="eyebrow">USDA NAIP / USGS NATIONAL MAP</div><h1>Aerial evidence,<br>in its own time.</h1><p>${esc(GEO_IMAGERY.policy)}</p><div class="geo-market-list">${GEO_IMAGERY.records.map(c=>{const r=c.anchor.ids.map(uaRecord).find(Boolean);return `<button data-geo-image-select="${esc(r?.id||'')}" data-geo-image-capture="${c.id}" ${r&&c.status==='captured'?'':'disabled'}><span><strong>${esc(r?.name||c.anchor.ids[0])}</strong><small>${c.status==='captured'?esc(c.image.acquired_at):'Unavailable · '+esc(c.reason)}</small></span>${uiIcon('arrow')}</button>`;}).join('')}</div><button class="btn" data-geo-image-manifest>Export complete imagery manifest ↓</button>`;
}
// All native physical selections can be retained using the existing portable,
// version-pinned saved-view format, including their parent source and camera.
const geoPhysicalRail=uaPhysicalRail;
uaPhysicalRail=function(record,source){
  const html=geoPhysicalRail(record,source);
  if(globe?.manifest?.features.some(f=>f.id===record.id))return html;
  return html.replace('data-ua-export-feature="'+esc(record.id)+'">'+uiIcon('source')+' Export physical evidence','data-geo-save-physical>'+uiIcon('source')+' Save physical evidence');
};
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.hasAttribute('data-geo-image-library'))geoImageLibrary();
  if(button.hasAttribute('data-geo-image-manifest'))download('compute-atlas-aerial-manifest.json',{...GEO_IMAGERY,records:GEO_IMAGERY.records.map(r=>r.status==='captured'?geoImageryMetadata(r):Object.fromEntries(Object.entries(r).filter(([k])=>k!=='native_capture')))});
  if(button.dataset.geoImageSelect)uaGo({region:'All',country:'All',q:'',operator:'',collection:'all',coverage:'all',selected:button.dataset.geoImageSelect,scale:4,feature:null,phase:null,scene:'anchor-'+button.dataset.geoImageCapture,camera:null,sceneCamera:null,mode:'aerial',scope:'geography'});
  if(button.hasAttribute('data-geo-save-physical')){
    uaRemember();const hash=uaURL(),record=globe.features.find(f=>f.record.id===uaState.feature)?.record;if(!record)return;
    if(saved.views.some(v=>v.hash===hash)){toast('This physical view is already on your research shelf.');return;}
    if(saved.views.length>=100){toast('100 views saved. Export your session and remove a view to add another.');return;}
    saved.views.push({id:'view-'+(globalThis.crypto?.randomUUID?.()||Date.now().toString(36)),name:('Physical evidence · '+record.name).slice(0,120),hash,saved_at:new Date().toISOString()});save();toast(storageOK?'Physical evidence saved to your research shelf.':'Saved for this session. Export before closing.');
  }
  if(button.hasAttribute('data-geo-image-export')||button.hasAttribute('data-geo-image-download')){
    const capture=geoImageryFor(uaRecord(uaState.selected));if(!capture)return;
    try{
      if(button.hasAttribute('data-geo-image-export')){
        const native=capture.native_capture||JSON.parse(new TextDecoder().decode(await geoCheckedBytes(capture.metadata.path,capture.metadata.sha256)));
        download('compute-atlas-imagery-'+capture.id+'.json',{...geoImageryMetadata(capture),native_capture:native,policy:GEO_IMAGERY.policy});
      }else{
        const im=capture.image,bytes=im.data_url?Uint8Array.from(atob(im.data_url.split(',')[1]),c=>c.charCodeAt(0)):await geoCheckedBytes(im.path,im.sha256);
        const url=URL.createObjectURL(new Blob([bytes],{type:'image/jpeg'})),a=document.createElement('a');a.href=url;a.download='compute-atlas-'+capture.id+'-'+(im.acquisition_dates[0]||'undated')+'.jpg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      }
    }catch(error){toast('Source export unavailable: '+error.message+'. Retry from the provenance panel.');}
  }
});
document.addEventListener('click',event=>{
  if(!event.target.closest('[data-ui-recover-source]'))return;
  const capture=geoImageryFor(uaRecord(uaState.selected));
  if(capture&&uaState.scene==='anchor-'+capture.id){event.stopImmediatePropagation();uaGo({imageversion:null,featureversion:null,contextversion:null},true);}
},true);
