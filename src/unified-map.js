'use strict';
const uaNativeCache=new Map();
function uaCaptureFor(record){
  if(!record?.mapped)return null;
  const exact=UA_CONTEXT_INDEX.captures.find(c=>c.anchors.some(p=>p.ids.includes(record.id)));if(exact)return exact;
  return UA_CONTEXT_INDEX.captures.find(c=>c.anchors.some(p=>spatialDistance(p,record)<.75))||null;
}
async function uaLoadContext(record=uaRecord(uaState.selected)){
  const capture=uaCaptureFor(record);if(!capture){uaContext=null;return null;}
  if(uaNativeCache.has(capture.id)){uaContext=uaNativeCache.get(capture.id);return uaContext;}
  if(uaContextPromise?.id===capture.id)return uaContextPromise.promise;
  const promise=(async()=>{
    try{
      let bytes;const embedded=document.getElementById('global-context-pack');
      if(embedded){const chunk=document.getElementById('global-context-'+capture.id);if(!chunk)throw new Error('Embedded context chunk unavailable');const raw=atob(chunk.textContent);bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));}
      else {const response=await fetch(new URL(capture.path+'?v='+capture.sha256.slice(0,12),location.href),{signal:AbortSignal.timeout(20000)});if(!response.ok)throw new Error('Context HTTP '+response.status);bytes=new Uint8Array(await response.arrayBuffer());}
      if(globalThis.crypto?.subtle){const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');if(digest!==capture.sha256)throw new Error('Source-context checksum mismatch');}
      const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));const raw=await new Response(stream).text(),data=JSON.parse(raw);
      if(!Array.isArray(data.elements))throw new Error('Invalid native context');
      const result={capture,source:data,features:data.elements.map(uaNativeFeature).filter(Boolean)};
      uaNativeCache.set(capture.id,result);if(uaNativeCache.size>4)uaNativeCache.delete(uaNativeCache.keys().next().value);
      if(uaCaptureFor(uaRecord(uaState.selected))?.id===capture.id)uaContext=result;
      uaContextError=null;return result;
    }catch(error){uaContextError=error.message;return null;}
  })();uaContextPromise={id:capture.id,promise};promise.finally(()=>{if(uaContextPromise?.promise===promise)uaContextPromise=null;});return promise;
}
function uaNativeFeature(e){
  const tags=e.tags||{},points=(e.geometry||[]).filter(p=>Number.isFinite(p.lon)&&Number.isFinite(p.lat)).map(p=>[p.lon,p.lat]);
  if(!points.length&&Number.isFinite(e.lat)&&Number.isFinite(e.lon))points.push([e.lon,e.lat]);if(!points.length)return null;
  const closed=points.length>3&&points[0][0]===points.at(-1)[0]&&points[0][1]===points.at(-1)[1],building=!!tags.building,lon=points.reduce((n,p)=>n+p[0],0)/points.length,lat=points.reduce((n,p)=>n+p[1],0)/points.length;
  const height=tags.height&&/^\d+(?:\.\d+)?\s*(?:m)?$/.test(tags.height)?parseFloat(tags.height):null;
  return {id:`osm-${e.type}-${e.id}`,name:tags.name||tags['name:en']||(building?'Mapped building':tags.power?'Mapped '+tags.power:tags.highway?'Mapped '+tags.highway:tags.telecom?'Mapped '+tags.telecom:'Mapped feature'),kind:building?'building':closed?'area':'context',lat,lon,height_m:height,geometry:closed?{type:'MultiPolygon',coordinates:[[points]]}:null,line:points,tags,source_version:e.version,updated_at:e.timestamp,source_url:`https://www.openstreetmap.org/${e.type}/${e.id}`,native:e};
}
function uaContextNearby(record){
  if(!uaContext||!record?.mapped&&(!Number.isFinite(record?.lat)||!Number.isFinite(record?.lon)))return [];
  const key=record.id+':'+record.lat+':'+record.lon;
  uaContext.nearbyCache??=new Map();if(uaContext.nearbyCache.has(key))return uaContext.nearbyCache.get(key);
  const scaleX=111.32*Math.cos(record.lat*Math.PI/180),scaleY=111.32;
  const rows=uaContext.features.filter(f=>{if(spatialDistance(f,record)<1.5)return true;
    let previous=null;for(const [lon,lat] of f.line){const p=[(lon-record.lon)*scaleX,(lat-record.lat)*scaleY];if(Math.hypot(...p)<1.5)return true;
      if(previous){const dx=p[0]-previous[0],dy=p[1]-previous[1],length=dx*dx+dy*dy,t=length?Math.max(0,Math.min(1,-(previous[0]*dx+previous[1]*dy)/length)):0;if(Math.hypot(previous[0]+t*dx,previous[1]+t*dy)<1.5)return true;}previous=p;
    }return false;
  });uaContext.nearbyCache.set(key,rows);return rows;
}
function uaImageSource(manifest){
  if(!manifest)return '';const im=manifest.image;
  return `<h2>${esc(manifest.title)}</h2><p>${esc(manifest.review.limitations)}</p><dl class="ua-facts"><div><dt>Image observation</dt><dd>${esc(im.acquired_at)} · ${esc(im.date_precision||'Publisher acquisition date')}</dd></div><div><dt>Publisher</dt><dd>${esc(im.publisher)}</dd></div><div><dt>Reuse terms</dt><dd>${esc(im.license)}</dd></div><div><dt>Native resolution</dt><dd>${esc(im.native_resolution_m)} m</dd></div><div><dt>Geometry review</dt><dd>${esc(manifest.review.basis)}</dd></div></dl><p class="ua-source-code">Image SHA-256: ${esc(im.sha256)}</p>${catalogLink(im.license_url,'Image license','btn')}${catalogLink(im.metadata_url,'Native image metadata','btn')}${manifest.sources.map(s=>catalogLink(s.url,s.label,'btn')).join('')}<p>Roof outlines are reviewed historical interpretations. Heights, current operation and building-level power are not inferred.</p>`;
}
function uaContextSource(){
  const r=uaRecord(uaState.selected),capture=uaCaptureFor(r);openDrawer('atlas-context-source');$('#drawer-type').textContent='MAP SOURCES & COVERAGE';
  $('#drawer-content').innerHTML=`<h1>A source for the physical world.</h1>${uaImageSource(globe?.manifest)}<p>${esc(UA_CONTEXT_INDEX.policy||'Native map geometry is independent of project evidence.')}</p><dl class="ua-facts"><div><dt>Global captured context</dt><dd>${fmt(UA_CONTEXT_INDEX.feature_count||0)} native map features</dd></div><div><dt>Published anchor locations</dt><dd>${fmt(UA_CONTEXT_INDEX.anchor_count||0)}</dd></div><div><dt>Countries / territories</dt><dd>${esc((UA_CONTEXT_INDEX.countries||[]).join(', '))}</dd></div><div><dt>Capture date</dt><dd>${esc(UA_CONTEXT_INDEX.captured_at?.slice(0,10)||'Not supplied')}</dd></div><div><dt>License</dt><dd>${catalogLink('https://www.openstreetmap.org/copyright','ODbL · OpenStreetMap contributors')}</dd></div></dl><button class="btn" data-ua-context-index>Export complete context manifest ↓</button><h2>Independent source layers</h2><p>Natural Earth supplies generalized global reference geography. Native OpenStreetMap context supplies captured buildings, roads, power and telecommunications tags around published compute locations. Live street tiles are optional and are loaded only for the visible map. No route establishes a facility’s utility service or fiber connection.</p>${capture?`<h2>Selected location capture</h2><p>${fmt(capture.feature_count)} native objects in this bounded source batch. OSM database timestamp: ${esc(capture.osm_base)}.</p><pre class="ua-source-code">${esc(capture.query)}</pre><p class="ua-source-code">SHA-256: ${esc(capture.response_sha256)}</p><button class="btn" data-ua-context-export>Export this native capture ↓</button>`:'<p>No bounded context capture matches this selected record. Its native footprint, if supplied, remains available.</p>'}<h2>Geometry and identity</h2><p>Building outlines, tagged heights, power voltage and source edit dates retain their native meanings. Features around a compute anchor are mapped surroundings, not an inferred campus inventory. Licensed aerial scenes and reviewed roof interpretations keep their own provenance.</p>`;
}
class UnifiedAtlasMap extends CatalogMap {
  constructor(canvas){
    super(canvas);this.ua=true;this.skipCatalogSave=true;this.scope={sites:uaRows(false).filter(r=>r.mapped),bounds:[-180,-80,180,80]};this.labels=uaState.layers.labels;this.level=uaState.scale;this.markerLabels=[];
    const selected=uaRecord(uaState.selected),center=catalogCameras[uaState.region]||catalogCameras.All;
    Object.assign(this,{flat:uaState.scale>=2,lat:center[0],lon:center[1],zoom:uaState.scale===1?1.7:1});
    if(uaState.camera)Object.assign(this,{...uaState.camera,bounds:[...uaState.camera.bounds]});
    else if(this.flat){const span=uaState.scale===2?18:uaState.scale===3?1.6:.035;if(selected?.mapped)this.bounds=[selected.lon-span/2,Math.max(-80,selected.lat-span*.3),selected.lon+span/2,Math.min(80,selected.lat+span*.3)];else this.bounds=uaFitBounds(this.scope.sites,null,.7,.5);}
    this.scope.sites=uaRows().filter(r=>r.mapped);this.dirty=true;this.tiles=new Map();
    this.on('keydown',e=>{if(['+','=','-','Home'].includes(e.key)){e.preventDefault();e.stopPropagation();if(e.key==='Home')uaMapAction('reset');else this.cameraZoom(e.key==='-'?1/1.25:1.25);}});
    if(selected?.mapped&&uaState.scale>=3)uaLoadContext(selected).then(()=>{if(!this.destroyed)this.dirty=true;});
  }
  destroy(){clearTimeout(this.cameraTimer);this.skipCatalogSave=true;super.destroy();}
  markCustom(){}
  persistCamera(){
    if(!this.ua)return;
    const level=this.flat?((this.bounds[2]-this.bounds[0])<5?3:2):(this.zoom>=1.5?1:0);
    if(uaState.scale<4&&uaState.scale!==level){uaState.scale=level;document.querySelectorAll('[data-ua-scale]').forEach(b=>{if(b.tagName==='BUTTON')b.setAttribute('aria-pressed',String(Number(b.dataset.uaScale)===level));});}
    const snapshot=catalogCameraSnapshot(this),token=catalogCameraToken(snapshot);if(token===this.lastCameraToken)return;
    this.lastCameraToken=token;uaState.camera=snapshot;clearTimeout(this.cameraTimer);this.cameraTimer=setTimeout(()=>{if(this.destroyed||state.view!=='atlas'||state.drawer)return;history.replaceState(null,'',uaURL());if(uaState.scope==='viewport')uaRefreshData();},220);
  }
  drawMarkers(){
    if(!this.ua)return;
    if(this.flat){if(uaState.layers.tiles)this.drawTiles();this.drawContext();}
    const c=this.ctx,grid=new Map(),selected=uaState.selected;this.groups=[];this.markerLabels=[];
    const rows=[...this.scope.sites],r=uaRecord(selected);if(r?.mapped&&!rows.some(x=>x.id===r.id))rows.push(r);
    for(const r of rows){const p=this.project(r.lon,r.lat);if(p.z<.02||p.x<8||p.x>this.w-8||p.y<40||p.y>this.h-55)continue;const cell=this.flat?(this.bounds[2]-this.bounds[0]<.08?10:25):35,key=Math.floor(p.x/cell)+':'+Math.floor(p.y/cell);let g=grid.get(key);if(!g){g={x:0,y:0,r:4,sites:[],selected:false};grid.set(key,g);}g.x+=p.x;g.y+=p.y;g.sites.push(r);g.selected||=r.id===selected;}
    for(const g of grid.values()){
      g.x/=g.sites.length;g.y/=g.sites.length;g.r=Math.min(22,3+Math.sqrt(g.sites.length)*1.3);this.groups.push(g);
      const representative=g.sites.find(r=>r.id===selected)||g.sites.find(r=>['gpu','epochdc','projects'].includes(r.collection))||g.sites[0];g.representative=representative;const color=UA_COLORS[representative.collection];
      const glow=c.createRadialGradient(g.x,g.y,1,g.x,g.y,g.r*2.2);glow.addColorStop(0,color+'24');glow.addColorStop(1,color+'00');c.fillStyle=glow;c.beginPath();c.arc(g.x,g.y,g.r*2.2,0,Math.PI*2);c.fill();c.fillStyle=color+'35';c.strokeStyle=g.selected?'#eafff4':color;c.lineWidth=g.selected?2:1;c.beginPath();c.arc(g.x,g.y,g.r,0,Math.PI*2);c.fill();c.stroke();c.fillStyle=g.selected?'#ffffff':color;c.beginPath();c.arc(g.x,g.y,g.selected?3:1.7,0,Math.PI*2);c.fill();
    }
    if(this.labels){const budget=this.w<450?3:this.flat?7:5;
      for(const g of [...this.groups].sort((a,b)=>Number(b.selected)-Number(a.selected)||b.sites.length-a.sites.length)){
        if(this.markerLabels.length>=budget)break;const r=g.representative,name=g.sites.length>1&&!g.selected?(new Set(g.sites.map(x=>x.country)).size>1?(new Set(g.sites.map(x=>x.region)).size===1?r.region+' cluster':'Multi-region cluster'):(r.native.city||r.country)+' cluster'):r.name,title=name.length>31?name.slice(0,29)+'…':name;
        c.font='12px Arial,sans-serif';const width=Math.max(100,c.measureText(title).width+14),height=38;
        const positions=[{x:g.x+g.r+9,y:g.y-24},{x:g.x-width-g.r-9,y:g.y-24},{x:g.x-width/2,y:g.y+g.r+8}];
        const box=positions.find(b=>b.x>8&&b.x+width<this.w-8&&b.y>48&&b.y+height<this.h-120&&!this.markerLabels.some(a=>researchLabelOverlap({...b,w:width,h:height},a,7)));
        if(!box)continue;this.markerLabels.push({...box,w:width,h:height});c.fillStyle='#071a23e8';c.fillRect(box.x,box.y,width,height);c.strokeStyle='#23434b';c.strokeRect(box.x,box.y,width,height);c.fillStyle='#e6f3f1';c.fillText(title,box.x+7,box.y+15);c.font='10px ui-monospace,monospace';c.fillStyle='#93b9c6';c.fillText(g.sites.length>1?g.sites.length+' source records':UA_SHORT[r.collection],box.x+7,box.y+30);
      }
    }
    this.persistCamera();const status=$('#ua-coordinate');if(status)status.textContent=this.flat?`${Math.abs((this.bounds[1]+this.bounds[3])/2).toFixed(3)}° ${this.bounds[1]+this.bounds[3]>=0?'N':'S'} · ${Math.abs((this.bounds[0]+this.bounds[2])/2).toFixed(3)}° ${this.bounds[0]+this.bounds[2]>=0?'E':'W'}`:`${this.lat.toFixed(1)}° N · ${Math.abs(this.lon).toFixed(1)}° ${this.lon<0?'W':'E'} · DRAG TO ROTATE`;
  }
  pointerMove(e){if(this.drag){ResearchMap.prototype.pointerMove.call(this,e);return;}const rect=this.canvas.getBoundingClientRect(),hit=this.groups.find(g=>Math.hypot(g.x-e.clientX+rect.left,g.y-e.clientY+rect.top)<g.r+7);this.canvas.style.cursor=hit?'pointer':'grab';if(hit)showTip(e.clientX,e.clientY,`<b>${esc(hit.representative.name)}</b><br>${hit.sites.length} independent source record${hit.sites.length===1?'':'s'}<br><small>Click to inspect without moving the map</small>`);else hideTip();}
  pointerUp(e){if(!this.drag)return;const moved=this.drag.moved;this.drag=null;if(moved)return;const rect=this.canvas.getBoundingClientRect(),hit=this.groups.find(g=>Math.hypot(g.x-e.clientX+rect.left,g.y-e.clientY+rect.top)<g.r+8);if(!hit)return;hideTip();uaRemember();if(hit.sites.length===1)uaSelect(hit.sites[0].id);else{uaState.members=uaSort(hit.sites).map(r=>r.id);$('#ua-cluster-members').innerHTML=uaMembersHTML();$('#ua-cluster-members button')?.focus({preventScroll:true});}}
  drawContext(){
    if(!uaContext||this.bounds[2]-this.bounds[0]>3)return;const c=this.ctx;
    for(const f of uaContextNearby(uaRecord(uaState.selected))){const tags=f.tags;if(tags.building&&!uaState.layers.buildings||tags.highway&&!uaState.layers.roads||tags.power&&!uaState.layers.power||tags.telecom&&!uaState.layers.telecom)continue;const color=tags.power?'#c6a0efaa':tags.highway?'#6e89967a':tags.waterway?'#368aab90':'#86acb18a';this.path(f.line,color,tags.power?1.6:tags.highway?.9:.8,tags.building&&f.geometry?'#40656e40':null);if(f.line.length===1){const p=this.project(f.lon,f.lat);c.strokeStyle=color;c.beginPath();c.arc(p.x,p.y,4,0,Math.PI*2);c.stroke();}}
  }
  drawTiles(){
    if(!this.flat||!uaState.layers.tiles)return;const c=this.ctx,natural=Math.log2(this.scale*2*Math.PI/256),z=Math.max(3,Math.min(18,Math.floor(natural))),n=2**z;
    const bounds=this.bounds,x0=Math.floor((bounds[0]+180)/360*n)-1,x1=Math.ceil((bounds[2]+180)/360*n)+1,ty=lat=>(1-mercatorY(lat)/Math.PI)/2*n,y0=Math.max(0,Math.floor(ty(bounds[3]))-1),y1=Math.min(n-1,Math.ceil(ty(bounds[1]))+1);
    if((x1-x0+1)*(y1-y0+1)>48)return;
    c.save();c.globalAlpha=.7;c.filter='invert(1) hue-rotate(170deg) saturate(.55) brightness(.75)';
    for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){
      const key=z+'/'+((x%n+n)%n)+'/'+y;let tile=this.tiles.get(key);
      if(!tile){tile=new Image();tile.crossOrigin='anonymous';tile.onload=()=>{if(!this.destroyed)this.dirty=true;};tile.onerror=()=>{tile.failed=true;};tile.src='https://tile.openstreetmap.org/'+key+'.png';this.tiles.set(key,tile);}
      if(!tile.complete||!tile.naturalWidth)continue;const lat=y=>Math.atan(Math.sinh(Math.PI*(1-2*y/n)))/geographicRadians,a=this.project(x/n*360-180,lat(y)),b=this.project((x+1)/n*360-180,lat(y+1));c.drawImage(tile,a.x,a.y,b.x-a.x+.6,b.y-a.y+.6);
    }c.restore();if(this.tiles.size>160){const keys=[...this.tiles.keys()];for(const key of keys.slice(0,keys.length-120))this.tiles.delete(key);}
  }
}
function uaHitContext(scene,event){const rect=scene.canvas.getBoundingClientRect(),x=event.clientX-rect.left,y=event.clientY-rect.top;return (scene.powerPaths||[]).find(row=>row.pts.some((b,i)=>{if(!i)return Math.hypot(x-b.x,y-b.y)<7;const a=row.pts[i-1],dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-a.x-t*dx,y-a.y-t*dy)<7;}))?.feature;}
class UnifiedFacilityScene extends FacilityScene {
  setContext(enabled){this.showContext=enabled;const points=this.features.find(f=>f.record.id===this.record.id)?.polygons.flat(2)||[];this.extent=points.length?Math.max(90,...points.map(p=>Math.hypot(...p)*1.4)):750;this.baseExtent=this.extent;this.frameCenter=[0,0];this.zoom=1;this.pan={x:0,y:0};this.dirty=true;}
  hit(event){return FacilityScene.prototype.hit.call(this,event)||uaHitContext(this,event);}

  constructor(canvas,record,features){
    super(canvas,record,features);this.ua=true;this.assumptions=false;this.showContext=true;this.labels=uaState.layers.labels;this.labelBasis=record.geometry?'NATIVE SOURCE OUTLINE':'PUBLISHED LOCATION · INDEPENDENT CONTEXT';this.pitch=uaState.mode==='3d'?.78:1.48;this.yaw=uaState.mode==='3d'?-.4:0;this.setContext(true);
    if(this.extent<80)this.extent=250;this.baseExtent=this.extent;
    if(uaState.sceneCamera)Object.assign(this,uaState.sceneCamera,{pan:{...uaState.sceneCamera.pan}});
    if(uaState.feature)this.inspect(uaState.feature,false);this.dirty=true;
  }
  buildGeometry(neighbors){this.frameCenter=[0,0];this.extent=250;this.baseExtent=250;const seen=new Set();this.features=[this.record,...neighbors].filter(r=>!seen.has(r.id)&&seen.add(r.id)).map(record=>({record,selected:record.id===this.record.id,polygons:(record.geometry?.coordinates||[]).map(poly=>poly.map(ring=>ring.map(p=>this.local(...p))))}));}
  snapshot(){return {yaw:this.yaw,pitch:this.pitch,zoom:this.zoom,pan:{...this.pan}};}
  inspect(id,notify=true){const result=super.inspect(id,false);if(result&&notify)this.canvas.dispatchEvent(new CustomEvent('ua-feature-select',{bubbles:true,detail:{id}}));return result;}
  drawGround(){
    this.powerPaths=[];if(!this.ua)return;const c=this.ctx;
    for(const f of uaContextNearby(this.record)){if(f.tags?.building)continue;const power=!!f.tags?.power,road=!!f.tags?.highway;if(power&&!uaState.layers.power||road&&!uaState.layers.roads||f.tags?.telecom&&!uaState.layers.telecom)continue;c.beginPath();f.line.forEach((p,i)=>{const q=this.project3(...this.local(...p));i?c.lineTo(q.x,q.y):c.moveTo(q.x,q.y);});c.strokeStyle=power?'#c6a0efa0':road?'#658d9b90':'#4a919c80';c.lineWidth=power?1.6:1;c.stroke();if(f.line.length===1){const q=this.project3(...this.local(...f.line[0]));c.beginPath();c.arc(q.x,q.y,4,0,Math.PI*2);c.stroke();}if(power||f.tags?.telecom){const feature=this.features.find(x=>x.record.id===f.id);if(feature)this.powerPaths.push({feature,pts:f.line.map(p=>this.project3(...this.local(...p)))});}}
  }
  draw(){const all=this.features;if(this.ua&&!uaState.layers.buildings)this.features=all.filter(f=>f.record.id===this.record.id||f.record.id===this.inspected.id||!f.record.tags?.building);super.draw();this.features=all;if(this.ua){const token=JSON.stringify(this.snapshot());if(token!==this.lastToken){this.lastToken=token;uaState.sceneCamera=this.snapshot();clearTimeout(this.uaTimer);this.uaTimer=setTimeout(()=>{if(!this.destroyed&&state.view==='atlas'&&!state.drawer)history.replaceState(null,'',uaURL());},220);}}}
  destroy(){clearTimeout(this.uaTimer);super.destroy();}
}
class UnifiedCampusScene extends CampusScene {
  hit(event){const roof=FacilityScene.prototype.hit.call(this,event);if(roof)return roof;if(!uaState.layers.power)return null;const r=this.canvas.getBoundingClientRect(),x=event.clientX-r.left,y=event.clientY-r.top;return (this.powerPaths||[]).find(row=>row.pts.some((b,i)=>{if(!i)return false;const a=row.pts[i-1],dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-a.x-t*dx,y-a.y-t*dy)<7;}))?.feature;}
  drawGround(){CampusScene.prototype.drawGround.call(this);this.powerPaths=[];if(!this.ua||!uaState.layers.power)return;const c=this.ctx;for(const collection of this.powerCollections)for(const row of contextPaths(this,collection)){const feature=this.features.find(f=>f.record.id===row.feature.id);if(!feature)continue;this.powerPaths.push({...row,feature});c.beginPath();row.pts.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));c.strokeStyle=this.inspected.id===feature.record.id?'#ffe0a4':'#d9ac68c9';c.lineWidth=1.6;c.stroke();}}

  constructor(canvas,manifest){const old={mode:campusState.mode,camera:campusState.camera,routeCamera:campusState.routeCamera,feature:campusState.feature};Object.assign(campusState,{mode:uaState.mode==='3d'?'oblique':'aerial',camera:null,routeCamera:null,feature:null});super(canvas,manifest);Object.assign(campusState,old);this.ua=true;this.skipCameraSave=true;this.labels=uaState.layers.labels;
    this.powerCollections=ENERGY_COLLECTIONS.filter(c=>c.scene_id===manifest.id);
    for(const collection of this.powerCollections)for(const native of collection.features){
      const line=native.geometry.coordinates,center=line[Math.floor(line.length/2)],record={id:native.id,name:energyName(native),kind:'context',lat:center[1],lon:center[0],line,tags:native.tags,height_m:null,updated_at:native.edited_at,source_version:native.version,source_url:native.url,native,capture_id:collection.id};
      this.features.push({record,selected:false,polygons:[]});
    }
    this.image.onerror=()=>{if(this.destroyed)return;this.imageReady=false;this.canvas.dataset.image='error';const status=$('#ua-context-status');if(status)status.innerHTML='Historical image unavailable; reviewed outlines remain accessible. <button class="text-button" data-ua-retry-context>Retry image</button>';this.dirty=true;};
    if(uaState.sceneCamera)Object.assign(this,uaState.sceneCamera,{pan:{...uaState.sceneCamera.pan}});if(uaState.feature)this.inspect(uaState.feature,false);this.dirty=true;}
  inspect(id,notify=true){const result=FacilityScene.prototype.inspect.call(this,id,false);if(result&&notify)this.canvas.dispatchEvent(new CustomEvent('ua-feature-select',{bubbles:true,detail:{id}}));return result;}
  draw(){FacilityScene.prototype.draw.call(this);if(!this.ua)return;const token=JSON.stringify(this.snapshot());if(token!==this.lastToken){this.lastToken=token;uaState.sceneCamera=this.snapshot();clearTimeout(this.uaTimer);this.uaTimer=setTimeout(()=>{if(!this.destroyed&&state.view==='atlas'&&!state.drawer)history.replaceState(null,'',uaURL());},220);}}
  destroy(){clearTimeout(this.uaTimer);this.skipCameraSave=true;FacilityScene.prototype.destroy.call(this);}
}
function uaMount(){
  const canvas=$('#ua-map'),r=uaRecord(uaState.selected);if(!canvas)return;
  if(uaState.scale>=4&&r?.mapped){
    const scenes=CAMPUS_SCENES.scenes.filter(s=>s.project_id===r.id),manifest=uaState.scene?scenes.find(s=>s.id===uaState.scene):scenes[0];
    if(manifest){uaState.scene=manifest.id;globe=new UnifiedCampusScene(canvas,manifest);$('.ua-map-attribution').innerHTML=catalogLink(manifest.image.license_url,manifest.image.attribution||manifest.image.publisher+' · '+manifest.image.license)+'<button class="text-button" data-ua-context-source>Image & map provenance →</button>';const status=$('#ua-context-status');status.textContent=`${manifest.image.acquired_at} historical imagery · ${manifest.features.length} reviewed roof interpretations`;}
    else{
      const source=r.collection==='osm'?r.native:{id:r.id,name:r.name,lat:r.lat,lon:r.lon,kind:'point',height_m:null,geometry:null};
      const neighbors=CATALOG.records.filter(f=>f.geometry&&spatialDistance(f,r)<1.2),context=uaCaptureFor(r)?.id===uaContext?.capture.id?uaContextNearby(r).filter(f=>f.geometry||f.tags?.power||f.tags?.telecom):[];
      globe=new UnifiedFacilityScene(canvas,source,[...neighbors,...context]);const scene=globe,status=$('#ua-context-status');
      if(uaCaptureFor(r)){status.textContent=context.length?`${context.length} native nearby features · independent context`:'Loading captured source context…';uaLoadContext(r).then(data=>{if(scene.destroyed||globe!==scene)return;if(data){const camera=scene.snapshot();scene.buildGeometry([...neighbors,...uaContextNearby(r).filter(f=>f.geometry||f.tags?.power||f.tags?.telecom)]);scene.setContext(true);if(uaState.sceneCamera)Object.assign(scene,camera);if(uaState.feature)scene.inspect(uaState.feature,false);status.textContent=`${uaContextNearby(r).filter(f=>f.geometry||f.tags?.power||f.tags?.telecom).length} native nearby features · independent context`;scene.dirty=true;uaPhysicalInspector(uaState.feature);}else status.innerHTML=`Captured context unavailable. ${esc(uaContextError||'The native record remains available.')} <button class="text-button" data-ua-retry-context>Retry capture</button>`;});}
      else status.textContent=neighbors.length?'Native nearby outlines · independent source records':'Source location · no building outline supplied here';
    }
    if(uaState.scene&&!manifest)$('#ua-context-status').innerHTML=`Requested image ${esc(uaState.scene)} is unavailable for this record. <button class="text-button" data-ua-reset-scene>Use an available source</button>`;
    if(!uaState.feature&&r.geometry){uaState.feature=r.id;globe.inspect(r.id,false);}
    uaPhysicalInspector(uaState.feature);
  }else globe=new UnifiedAtlasMap(canvas);
}
function uaPhysicalRail(record,source){
  const voltage=record.tags?.power&&record.tags?.voltage,area=record.derived_outline_area,measure=uaMeasure(source),value=voltage?energyVoltage(record):area?'≈ '+fmt(area.rounded_m2)+' m²':record.height_m!=null?fmt(record.height_m,1)+' m':'Source geometry',label=voltage?'Native voltage tag':area?'Interpreted roof outline':record.height_m!=null?'Community height tag':'No measured height supplied';
  return `<section id="ua-feature-selection" class="ua-editorial ua-selected"><div class="ua-selection-top"><span class="ua-source" style="--source-color:#9fefd7">Physical source feature</span><button class="text-button" data-ua-clear-feature aria-label="Clear physical selection">×</button></div><h2 tabindex="-1">${esc(record.name)}</h2><p>${esc(record.id)}</p><div class="ua-selected-number"><b>${esc(value)}</b><span>${esc(label)}</span></div><dl class="ua-facts"><div><dt>${record.observed_at?'Image observation':'Source edited'}</dt><dd>${esc(record.observed_at||record.updated_at||'Not supplied')}</dd></div><div><dt>Height</dt><dd>${record.height_m==null?'Not supplied':fmt(record.height_m,1)+' m · source tag'}</dd></div><div><dt>Record version</dt><dd>${esc(record.source_version||record.review_sha256?.slice(0,12)||'Reviewed interpretation')}</dd></div></dl><div class="ua-actions"><button class="btn primary" data-ua-context-source>Inspect source provenance →</button><button class="text-button" data-ua-export-feature="${esc(record.id)}">Export physical record ↓</button></div></section><section class="ua-editorial"><div class="eyebrow">02 / ${source.collection==='projects'?'PROJECT-LEVEL CONTEXT':'SELECTED SOURCE RECORD'}</div><h2>${esc(source.name)}</h2><p>${esc(source.operator||source.country)}</p>${measure.value!=null?`<strong class="ua-parent-measure">${esc(compact(measure.value)+' '+measure.unit)}</strong><p>${esc(measure.label)} · ${esc(measure.date||source.date||'Undated')}</p>`:''}<small>Project identity, capacity and utility service are independently evidenced. No allocation to this physical feature is inferred.</small><button class="text-button" data-ua-clear-feature>Return to record overview →</button></section>`;
}
function uaPhysicalInspector(id){
  if(!globe?.ua||!(globe instanceof FacilityScene))return;const record=globe.features.find(f=>f.record.id===id)?.record;
  const target=$('#ua-physical-inspector');if(!target)return;const source=uaRecord(uaState.selected);if(source&&$('.ua-rail'))$('.ua-rail').innerHTML=record?uaPhysicalRail(record,source):uaSelectedRail(source,uaRows());
  const features=globe.features.filter(f=>f.polygons.length||f.record.tags?.power||f.record.tags?.telecom);
  target.innerHTML=`<section class="ua-physical"><header><h3>Inspect the physical source</h3><label>Mapped feature<select id="ua-feature-choice"><option value="">Choose a source feature</option>${features.map(f=>`<option value="${esc(f.record.id)}" ${id===f.record.id?'selected':''}>${esc(f.record.name)} · ${esc(f.record.id)}</option>`).join('')}</select></label></header>${record?`<div class="ua-physical-facts"><div><b>${esc(record.name)}</b><p>${esc(record.id)} · ${esc(record.kind)}</p></div><dl class="ua-facts"><div><dt>Height</dt><dd>${record.height_m==null?'Not supplied · no measured height inferred':fmt(record.height_m)+' m · source tag'}</dd></div><div><dt>Source date / revision</dt><dd>${esc(record.updated_at||record.observed_at||'Not supplied')} · ${esc(record.source_version||'reviewed interpretation')}</dd></div><div><dt>Power / service</dt><dd>Not inferred from geometry</dd></div></dl>${record.tags?`<details><summary>All native feature tags</summary><dl class="ua-facts">${Object.entries(record.tags).map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl></details>`:''}${record.derivation?`<p>${esc(record.derivation)}</p>`:''}${record.derived_outline_area?`<p>Interpreted outline: about ${fmt(record.derived_outline_area.rounded_m2)} m². ${esc(record.derived_outline_area.boundary)}</p>`:''}${(record.identity_reviews||[]).map(v=>`<p>${esc(v.interpretation)} ${catalogLink(v.source_url,v.locator)}</p>`).join('')}${record.source_url?catalogLink(record.source_url,'Open native source','btn'):''}<button class="btn" data-ua-export-feature="${esc(record.id)}">Export selected physical record ↓</button></div>`:`<p>${id?'Requested physical record '+esc(id)+' is unavailable in this capture. ':''}Select a mapped outline on the canvas or in the list. Nearby features are not automatically assigned to the project.</p>`}</section>`;
}
document.addEventListener('ua-feature-select',e=>{uaState.feature=e.detail.id;uaState.scale=5;uaRemember();history.pushState(null,'',uaURL());uaPhysicalInspector(e.detail.id);document.querySelectorAll('button[data-ua-scale]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.uaScale)===5)));});
document.addEventListener('change',e=>{if(e.target.id==='ua-feature-choice'){if(e.target.value)globe?.inspect(e.target.value);else{uaState.feature=null;uaPhysicalInspector(null);history.replaceState(null,'',uaURL());}}});
document.addEventListener('click',e=>{const b=e.target.closest('[data-ua-export-feature]');if(!b||!globe?.ua)return;const r=globe.features.find(f=>f.record.id===b.dataset.uaExportFeature)?.record;if(r)download('physical-source-'+r.id+'.json',{record:r,capture:globe.manifest?(r.capture_id?energyCollection(r.capture_id):globe.manifest):uaContext?.capture,policy:'Physical source record; no project ownership, phase capacity, service or unreported height inferred.'});});
function uaMapAction(action){
  if(!globe?.ua)return;
  if(action==='in'||action==='out'){if(globe instanceof ResearchMap)globe.cameraZoom(action==='in'?1.3:1/1.3);else globe.zoomTo(globe.zoom*(action==='in'?1.3:1/1.3));return;}
  if(action==='labels'){uaState.layers.labels=!uaState.layers.labels;globe.labels=uaState.layers.labels;globe.dirty=true;history.replaceState(null,'',uaURL());return;}
  if(action==='reset'){uaGo({camera:null,sceneCamera:null},true);return;}
  if(action==='expand'){const panel=$('.ua-map-panel'),open=!panel.classList.contains('ua-expanded');panel.classList.toggle('ua-expanded',open);document.body.classList.toggle('ua-map-open',open);panel.querySelector('[data-ua-map="expand"]').setAttribute('aria-label',open?'Exit expanded map':'Expand map');globe.resize();}
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('.ua-map-panel.ua-expanded')){uaMapAction('expand');$('[data-ua-map="expand"]')?.focus();}});

document.addEventListener('click',e=>{if(!e.target.closest('[data-ua-clear-feature]')||state.view!=='atlas')return;uaState.feature=null;uaPhysicalInspector(null);if(globe?.features){globe.features.forEach(f=>f.selected=false);globe.dirty=true;}history.replaceState(null,'',uaURL());});
