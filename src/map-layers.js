'use strict';
/* Independent context layers. Native OSM voltage and geometry never become IT MW. */
const POWER_CONTEXT=JSON.parse(document.getElementById('power-context').textContent);
const POWER_REVIEWS=JSON.parse(document.getElementById('power-reviews').textContent);
const ROAD_CONTEXT=JSON.parse(document.getElementById('road-context').textContent);
const layerFields={research:'spatialResearch',locations:'spatialLocations',labels:'spatialLabels',roads:'spatialRoads',boundaries:'spatialBoundaries',energy:'spatialEnergy'};
const energyState={feature:null,collection:null,sourceCollection:null,recovery:null,returnPhysical:null,focusReturn:false};
const CAMPUS_POWER_CONTEXT=JSON.parse(document.getElementById('campus-power-context').textContent);
const ENERGY_COLLECTIONS=[{...POWER_CONTEXT,id:'helios-osm-power-20261011',title:'Helios-area electricity snapshot',scene_id:'helios-naip-20220905'},...CAMPUS_POWER_CONTEXT.collections];
function energyCollection(id){return ENERGY_COLLECTIONS.find(c=>c.id===id);}
function energyCurrentCollection(){return energyState.feature&&energyCollection(energyState.collection)||ENERGY_COLLECTIONS.find(c=>c.scene_id===campusScene()?.id)||energyCollection(energyState.collection)||ENERGY_COLLECTIONS[0];}
function energySourceCollection(){return energyCollection(energyState.sourceCollection)||energyCurrentCollection();}
function energySourceFeature(){return energySourceCollection().id===energyState.collection?energyFeature():null;}
function energyDrawCollections(map){return map instanceof CampusScene?ENERGY_COLLECTIONS.filter(c=>c.scene_id===map.manifest.id):ENERGY_COLLECTIONS;}
function energyRecoveryContent(){const r=energyState.recovery;return r?`<div class="campus-route-recovery energy-route-recovery" role="status"><p>${esc(r.reason)} Requested native feature: ${esc(r.feature||'none')}. Requested capture: ${esc(r.collection||'unspecified')}.</p><button class="text-button" data-energy-recover>Use the current scene's mapped context →</button></div>`:'';}
function energyValidateReturn(value){
 if(typeof value!=='string'||value.length>5000||!/^#(?:overview|globe)\?/.test(value))return null;
 const p=new URLSearchParams(value.split('?')[1]),s=site(p.get('site')),m=CAMPUS_SCENES.scenes.find(m=>m.project_id===s?.id&&m.id===p.get('scene'));
 if(!m||p.get('imageversion')!==m.image.sha256||!['campus','facility'].includes(p.get('scale')))return null;
 const roof=p.get('feature')||p.get('lastfeature'),f=m.features.find(f=>f.id===roof);if(roof&&(!f||p.get('featureversion')!==f.review_sha256))return null;if(f)p.set('feature',f.id);p.delete('lastfeature');
 if(p.get('scenecamera')&&!campusCameraParse(p.get('scenecamera'),m))return null;
 p.delete('energyfeature');p.delete('energycollection');p.delete('energyversion');p.delete('energyobjectversion');p.delete('physicalreturn');p.delete('requestedphysicalreturn');p.set('selection',f?'feature':'project');p.set('energy','1');
 for(const key of [...p.keys()])if(key.startsWith('requestedenergy'))p.delete(key);return '#overview?'+p;
}
function energyReadRoute(p){
 if(!state.spatialEnergy){energyState.feature=null;energyState.collection=null;energyState.recovery=null;energyState.returnPhysical=null;return;}
 const requested={collection:p.get('requestedenergycollection')||p.get('energycollection')||'',version:p.get('requestedenergyversion')||p.get('energyversion')||'',feature:p.get('requestedenergyfeature')||p.get('energyfeature')||'',objectversion:p.get('requestedenergyobjectversion')||p.get('energyobjectversion')||''};
 const scene=CAMPUS_SCENES.scenes.find(m=>m.project_id===p.get('site')&&(!p.get('scene')||m.id===p.get('scene')));let c=requested.collection?energyCollection(requested.collection):ENERGY_COLLECTIONS.find(c=>c.scene_id===scene?.id)||ENERGY_COLLECTIONS[0],reason='';
 if(requested.collection&&!c)reason='The requested electricity collection is unavailable.';
 if(!c)c=energyCurrentCollection();
 if(!reason&&requested.version&&requested.version!==c.response_sha256)reason='The requested native capture version is unavailable; no current object has been reopened.';
 const f=c.features.find(f=>f.id===requested.feature);
 if(!reason&&requested.feature&&!f)reason='The requested native feature is unavailable in this capture.';
 if(!reason&&requested.feature&&requested.collection&&(!requested.version||!requested.objectversion))reason='The requested electricity selection is missing its native capture or object version.';
 if(!reason&&requested.objectversion&&String(f?.version)!==requested.objectversion)reason='The requested native object version is unavailable in this capture.';
 const physical=['campus','facility'].includes(p.get('scale')),s=site(p.get('site')),m=CAMPUS_SCENES.scenes.find(m=>m.project_id===s?.id&&(p.get('scene')?m.id===p.get('scene'):true));
 if(!reason&&requested.feature&&physical&&c.scene_id!==m?.id)reason='The requested native feature belongs to a different bounded component capture.';
 const physicalreturn=p.get('requestedphysicalreturn')||p.get('physicalreturn');energyState.returnPhysical=energyValidateReturn(physicalreturn);if(!reason&&physicalreturn&&!energyState.returnPhysical)reason='The requested physical return has an unavailable image, roof or camera version.';energyState.collection=c.id;energyState.recovery=reason?{...requested,...(physicalreturn?{physicalreturn}:{}),reason}:null;
 energyState.feature=state.spatialEnergy&&!reason&&(!p.get('selection')||p.get('selection')==='context')?f?.id||null:null;
}
function energyClearSelection(){
 const physical=energyState.returnPhysical;energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;
 if(physical&&!(globe instanceof CampusScene)){location.hash=physical;return;}
 energyRefreshRail();if(globe)globe.dirty=true;layerDecorate();history.pushState(null,'',spatialURL());
}
function energyExploreCapture(id){
 const c=energyCollection(id)||energyCurrentCollection(),f=energyFeature(),returnPhysical=globe instanceof CampusScene?spatialURL():energyState.returnPhysical;
 closeDrawer();state.spatialEnergy=true;const s=CAMPUS_SCENES.scenes.find(m=>m.id===c.scene_id);
 spatialTransition({level:3,selected:s?.project_id||'coreweave-helios'});energyState.collection=c.id;energyState.returnPhysical=energyValidateReturn(returnPhysical);energyState.feature=f&&c.features.some(x=>x.id===f.id)?f.id:null;
 if(globe instanceof ResearchMap){const b=c.coverage_bbox;globe.bounds=[b[0]-.002,b[1]-.002,b[2]+.002,b[3]+.002];globe.zoom=1;globe.target=null;globe.dirty=true;state.spatialCamera[globe.cameraKey]=globe.snapshot();energyRefreshRail();workspaceSyncURL();}
}
function energyNativeNodes(f){return f?.referenced_node_versions?`<details class="energy-native-nodes"><summary>Inspect ${f.referenced_node_versions.length} captured node references</summary>${f.referenced_node_versions.map(n=>atlasRow('Node '+n.osm_id+' · version '+n.version,esc(sourceUTC(n.edited_at))+'<small>'+n.coordinates.join(', ')+'</small>')).join('')}<p>Reference order reconstructs the complete native way; node edit time is not an infrastructure observation date.</p></details>`:'';}

function layerOn(id){return id==='energy'?state.spatialEnergy===true:state[layerFields[id]]!==false;}
function energyFeature(id=energyState.feature,collectionId=energyState.collection){return (energyCollection(collectionId)?.features||ENERGY_COLLECTIONS.flatMap(c=>c.features)).find(f=>f.id===id);}
function energyName(f){return f.tags.name||(f.tags.power==='substation'?'Mapped substation':'Mapped power line')+' · '+f.osm_id;}
function energyVoltage(f){const parts=(f.tags.voltage||'').split(';');return parts.length&&parts.every(x=>x.trim()&&Number.isFinite(Number(x))&&Number(x)>0)?parts.map(x=>(Number(x)/1000).toLocaleString('en-US',{maximumFractionDigits:3})+' kV').join(' / '):'Not tagged';}
function sourceUTC(value){const date=new Date(value);return Number.isFinite(date.getTime())?date.toLocaleString('en-GB',{timeZone:'UTC',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})+' UTC':value;}
function contextPaths(map,data){
 const scene=map instanceof CampusScene,rows=[];
 const point=([lon,lat])=>scene?map.project3(...map.local(lon,lat)):map.project(lon,lat);
 for(const feature of data.features)for(const path of feature.display_paths){
  if(path.length<2||path.some(p=>!Array.isArray(p)||p.length!==2||!p.every(AtlasSpatialMath.finite)||Math.abs(p[0])>180||Math.abs(p[1])>=90))continue;
  const parts=AtlasSpatialMath.screenPaths(path.map(point),{scene,flat:!scene&&map.flat,width:map.w});
  for(const pts of parts){
   const closed=parts.length===1&&pts.length===path.length&&path.length>3&&path[0][0]===path.at(-1)[0]&&path[0][1]===path.at(-1)[1];
   if(AtlasSpatialMath.screenPathVisible(pts,map.w,map.h,closed))rows.push({feature,pts,closed});
  }
 }
 return rows;
}
function contextCaptureVisible(map,data){const [x0,y0,x1,y1]=data.coverage_bbox;return contextPaths(map,{features:[{display_paths:[[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]]}]}).length>0;}
function localRoadDraw(map){
 map.localRoadPaths=layerOn('roads')&&(map instanceof CampusScene||map.flat)&&['overview','globe'].includes(state.view)?contextPaths(map,ROAD_CONTEXT):[];
 const c=map.ctx;c.save();c.setLineDash([]);
 for(const row of map.localRoadPaths){const main=['primary','secondary'].includes(row.feature.tags.highway);c.strokeStyle=main?'#92aaba99':'#809b9a78';c.lineWidth=main?1.25:.8;c.beginPath();row.pts.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));c.stroke();}
 c.restore();
 const visible=map.localRoadPaths.length>0;if(map.localRoadAttribution!==visible){map.localRoadAttribution=visible;layerDecorate();}
}
function localRoadLabels(map){
 if(!map.labels||map.level<3||!map.flat)return;
 const c=map.ctx,occupied=[...(map.markerLabels||[]),...(map.placeLabels||[])],named=new Set();map.roadLabels=[];c.font='10px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif';c.textAlign='left';let count=0;
 for(const row of [...(map.localRoadPaths||[])].sort((a,b)=>Number(['primary','secondary'].includes(b.feature.tags.highway))-Number(['primary','secondary'].includes(a.feature.tags.highway)))){
  const name=row.feature.tags.name||row.feature.tags.ref;if(!name||named.has(name)||count>=4)continue;
  const segments=row.pts.slice(1).map((p,i)=>AtlasSpatialMath.clipScreenSegment(row.pts[i],p,map.w,map.h)).filter(Boolean).sort((a,b)=>Math.hypot(b[1].x-b[0].x,b[1].y-b[0].y)-Math.hypot(a[1].x-a[0].x,a[1].y-a[0].y));
  const segment=segments[0];if(!segment||Math.hypot(segment[1].x-segment[0].x,segment[1].y-segment[0].y)<100)continue;
  const x=(segment[0].x+segment[1].x)/2,y=(segment[0].y+segment[1].y)/2,w=c.measureText(name).width;
  const box=[{x:x-w/2,y:y-19,w,h:14},{x:x-w/2,y:y+5,w,h:14}].find(b=>b.x>12&&b.x+b.w<map.w-12&&b.y>90&&b.y+b.h<map.h-70&&!map.labelExclusions.some(e=>researchLabelOverlap(b,e))&&!occupied.some(e=>researchLabelOverlap(b,e))&&!map.groups.some(g=>researchLabelCircle(b,g,g.r)));
  if(!box)continue;occupied.push(box);named.add(name);map.roadLabels.push({...box,name});count++;c.shadowColor='#051019';c.shadowBlur=5;c.fillStyle='#adc0c2';c.fillText(name,box.x,box.y+11);c.shadowBlur=0;
 }
}
function roadSourceContent(){return `<div class="atlas-eyebrow">INDEPENDENT COMMUNITY ROAD CONTEXT</div><h1>Local roads.<br>Separate vintages.</h1><p>${esc(ROAD_CONTEXT.policy)}</p>${atlasRow('Snapshot',esc(sourceUTC(ROAD_CONTEXT.captured_at)))}${atlasRow('Source', 'OpenStreetMap contributors')}${atlasRow('License','ODbL 1.0')}${atlasRow('Coverage',esc(ROAD_CONTEXT.coverage_bbox.join(', ')))}<p>These ${ROAD_CONTEXT.features.length} local ways supplement generalized Natural Earth roads. They are not worldwide street coverage. The 2022 aerial, generalized basemap and this community snapshot remain independently dated.</p><details class="map-layer-feature-list"><summary>Inspect ${ROAD_CONTEXT.features.length} native road records</summary>${ROAD_CONTEXT.features.map(f=>`<details><summary>${esc(f.tags.name||f.tags.ref||f.tags.highway)} · ${f.osm_id}</summary>${atlasRow('Source edit',esc(sourceUTC(f.edited_at)))}${atlasRow('Version',String(f.version))}${Object.entries(f.tags).map(([k,v])=>atlasRow(esc(k),esc(v))).join('')}<p><a href="${esc(f.url)}" target="_blank" rel="noopener">Original way →</a> · <a href="${esc(f.url)}/history" target="_blank" rel="noopener">History →</a></p></details>`).join('')}</details><p>Complete original geometry remains in the export. Display paths stop at the capture rectangle; these are not surveyed road endpoints. A mapped line does not establish a campus service connection or public access.</p><p><a href="${esc(ROAD_CONTEXT.license_url)}" target="_blank" rel="noopener">© OpenStreetMap contributors · license →</a><br><a href="${esc(ROAD_CONTEXT.query_url)}" target="_blank" rel="noopener">Original bounded API query →</a></p><p class="campus-source-hash">Capture response SHA-256: ${esc(ROAD_CONTEXT.response_sha256)}</p><button class="btn" data-road-export>Export complete cited road snapshot ↓</button>`;}
function energyFeatureList(c){return `<details class="map-layer-feature-list"><summary>Inspect ${c.features.length} mapped context features</summary>${c.features.slice().sort((a,b)=>Number(b.tags.power==='substation')-Number(a.tags.power==='substation')||a.osm_id-b.osm_id).map(f=>`<button data-energy-feature="${esc(f.id)}" data-energy-collection="${esc(c.id)}"><b>${esc(energyName(f))}</b><small>${esc(f.tags.power)} · ${esc(energyVoltage(f))} · edited ${esc(f.edited_at.slice(0,10))} · version ${f.version}</small></button>`).join('')}</details>`;}
function layerPanelContent(){
 const c=energyCurrentCollection(),rows=[['research','Research anchors',`${D.sites.length} named projects · independent dated estimates`],['locations','Community locations',`${fmt(CATALOG.records.length)} OSM map features · no capacity implied`],['labels','Map labels','Project and place names · same source as their geometry'],['roads','Road context',`Generalized Natural Earth + ${ROAD_CONTEXT.features.length} local OSM ways · ${ROAD_CONTEXT.captured_at.slice(0,10)}`],['boundaries','Administrative boundaries','Generalized Natural Earth reference boundaries'],['energy','Electricity context',`${ENERGY_COLLECTIONS.reduce((n,c)=>n+c.features.length,0)} source ways · three independent local captures`]];
 return `<h1>Map layers.</h1><p>Choose the context you need. Layer controls preserve the camera, selected project, refinements and research records.</p><div class="map-layer-options">${rows.map(([id,title,note])=>`<label><input type="checkbox" data-map-layer="${id}" ${layerOn(id)?'checked':''}><span><b>${title}</b><small>${note}</small></span></label>`).join('')}</div><p>Anchor, road and boundary controls apply to geographic maps. The campus image and interpreted roof keep their own dated Aerial/Evidence views.</p><div class="map-layer-sources"><button class="text-button" data-atlas-action="source-context">Reference geography sources & vintage →</button><button class="text-button" data-action="nav" data-id="catalog">Community location sources →</button></div><section class="map-layer-roads"><h2>Road detail has its own source.</h2><p>Generalized Natural Earth roads are supplemented by a bounded Helios-area community capture. Native access tags are retained; public or campus access is not inferred.</p><button class="btn" data-road-coverage>Explore local road capture →</button><button class="text-button" data-road-source>Road sources, native tags & export →</button></section><section class="map-layer-electricity"><h2>Electricity has bounded coverage.</h2><p>Each component has an independent capture. Physical views show only the matching collection; geographic views can show all three. Mapping dates do not establish current conditions or service.</p><div class="energy-collection-cards">${ENERGY_COLLECTIONS.map(x=>`<article class="energy-collection-card ${x.id===c.id?'current':''}"><h3>${esc(x.title)}</h3><p>${x.features.length} source ways · ${esc(x.captured_at.slice(0,10))} · partial coverage</p><button class="text-button" data-energy-collection-source="${esc(x.id)}">Source, native objects & export →</button><button class="text-button" data-energy-collection-coverage="${esc(x.id)}">Frame native capture →</button>${x.id===c.id?energyFeatureList(x):''}</article>`).join('')}</div><button class="btn" data-layer-coverage>Explore captured area →</button><button class="text-button" data-energy-source>Source, native tags & export →</button></section><section class="map-layer-unavailable"><h2>Fiber / connectivity</h2><p>No licensed route snapshot or reviewed service-connection geometry is available. Contract counterparties remain in their separately cited research view.</p></section>`;
}

function energySourceContent(){
 const c=energySourceCollection(),f=energySourceFeature(),m=CAMPUS_SCENES.scenes.find(m=>m.id===c.scene_id),raw=c.source_snapshot_path&&c.source_capture_revision?`<a href="https://github.com/Untitled1-Agent/compute-atlas/blob/${esc(c.source_capture_revision)}/${esc(c.source_snapshot_path)}" target="_blank" rel="noopener">Immutable captured XML →</a>`:'';
 return `<div class="atlas-eyebrow">COMMUNITY ELECTRICITY CONTEXT</div><h1>${f?esc(energyName(f)):esc(c.title)}</h1><p>${esc(c.policy)}</p>${atlasRow('Collection',esc(c.title))}${atlasRow('Snapshot',esc(sourceUTC(c.captured_at)))}${atlasRow('Source','OpenStreetMap contributors')}${atlasRow('License','ODbL 1.0')}${atlasRow('Coverage',esc(c.coverage_bbox.join(', ')))}${atlasRow('Aerial vintage',esc(m?.image.acquired_at||'No associated image'))}<p>Original complete ways remain in the export. Display paths are clipped to the capture rectangle; their clipped ends are not surveyed endpoints. This does not establish completeness outside or inside the rectangle.</p>${f?`${atlasRow('Source object','way/'+f.osm_id+' · version '+f.version)}${atlasRow('Source edit',esc(sourceUTC(f.edited_at)))}<h2>Native source tags</h2><dl class="energy-native-tags">${Object.entries(f.tags).map(([k,v])=>atlasRow(esc(k),esc(v))).join('')}</dl>${energyNativeNodes(f)}<p><a href="${esc(f.url)}" target="_blank" rel="noopener">Original OSM object →</a><br><a href="${esc(f.url)}/history" target="_blank" rel="noopener">Object revision history →</a></p>`:energyFeatureList(c)}<p><a href="${esc(c.license_url)}" target="_blank" rel="noopener">© OpenStreetMap contributors · source license →</a><br><a href="${esc(c.query_url)}" target="_blank" rel="noopener">Original bounded API query →</a>${raw?'<br>'+raw:''}</p><p class="campus-source-hash">Capture response SHA-256: ${esc(c.response_sha256)}</p><p>The query is live and may change; this app retains its dated snapshot. A source edit date is neither an image date nor an operating/commissioning date. The ${esc(m?.image.acquired_at.slice(0,4)||'dated')} aerial and this community snapshot are separate vintages.</p><button class="btn" data-energy-export>Export the independent cited snapshot ↓</button>`;
}

function energyRail(f){return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent energy-feature-inspector">${atlasKicker('01 / SELECTED CONTEXT FEATURE')}<div class="atlas-badge-row"><span>Community mapping</span><span>${esc(f.tags.power)}</span></div><h2>${esc(energyName(f))}</h2><p>OSM way ${f.osm_id} · version ${f.version}</p><div class="atlas-feature-number">${esc(energyVoltage(f))}</div><p class="atlas-number-boundary">Source-tagged voltage · not IT power</p>${atlasRow('Collection',esc(energyCurrentCollection().title))}${atlasRow('Source edit',esc(f.edited_at.slice(0,10)))}${atlasRow('Snapshot',esc(energyCurrentCollection().captured_at.slice(0,10)))}${atlasRow('Tagged operator',esc(f.tags.operator||'Not tagged'))}${atlasRow('Construction tag',esc(f.tags.construction||'Not tagged'))}<p>Community geometry, not a survey. These tags do not establish present operation, project ownership or which campus is served.</p><button class="btn primary" data-energy-source>Source & native attributes →</button><button class="text-button" data-energy-export>Export cited context ↓</button></section><section class="atlas-insight-card">${atlasKicker('02 / CONNECTION EVIDENCE')}<h2>Context.<br>Connection unestablished.</h2><p>Proximity does not prove service. No project MW is allocated to this feature and no native voltage is converted to capacity.</p><button class="text-button" data-energy-clear>Return to physical / project inspection →</button></section><section class="atlas-insight-card">${atlasKicker('03 / SOURCE COVERAGE')}<h2>A local snapshot.</h2><p>${energyCurrentCollection().features.length} source features in the bounded capture. Absence elsewhere is a coverage gap, not proof of no infrastructure.</p><button class="text-button" data-layer-open>Layers & captured feature list →</button></section></div>`;}
function energyRefreshRail(){const old=document.querySelector('.workspace-mobile-rail');if(old)old.outerHTML=workspaceMobileRail(state.spatialLevel,spatialScope(state.spatialLevel,spatialDefaultSite()),spatialDefaultSite(),state.spatialPhase);renderNav();}
function energySelect(id,collectionId){
 const c=collectionId?energyCollection(collectionId):ENERGY_COLLECTIONS.find(c=>c.features.some(f=>f.id===id)),f=c?.features.find(f=>f.id===id);if(!f)return;
 if(globe instanceof CampusScene&&globe.manifest.id!==c.scene_id){const m=CAMPUS_SCENES.scenes.find(m=>m.id===c.scene_id);if(!m)return;if(m.project_id===state.spatialSelected)campusChangeComponent(m.id);else {spatialTransition({level:4,selected:m.project_id});if(campusScene()?.id!==m.id)campusChangeComponent(m.id);}}
 const physical=globe instanceof CampusScene?energyState.returnPhysical||spatialURL():energyState.returnPhysical;
 state.spatialEnergy=true;energyState.collection=c.id;energyState.sourceCollection=null;energyState.recovery=null;energyState.returnPhysical=energyValidateReturn(physical);energyState.feature=id;workspaceState.mobileExpanded=true;if(!$('#drawer').hidden)closeDrawer();if(globe)globe.dirty=true;energyRefreshRail();layerDecorate();history.pushState(null,'',spatialURL());
}

function energyDraw(map){
 map.energyPaths=[];if(!layerOn('energy')||!['overview','globe'].includes(state.view))return;
 if(!globalThis.ATLAS?.layers)return;
 const c=map.ctx;c.save();c.setLineDash([]);
 const collections=energyDrawCollections(map);
 for(const collection of collections)for(const row of contextPaths(map,collection)){row.collection=collection;
  const {feature:f,pts,closed}=row,selected=energyState.feature===f.id&&energyState.collection===collection.id;c.strokeStyle=selected?'#ffe0a4':'#d9ac68c9';c.lineWidth=selected?2.8:1.3;c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));
  if(closed){c.closePath();c.fillStyle=selected?'#e7b96630':'#e7b96612';c.fill();}c.stroke();map.energyPaths.push(row);
 }
 c.restore();
 const coverage=document.querySelector('.map-layer-coverage-state');if(coverage)coverage.textContent=map.energyPaths.length?'Local source geometry in view':collections.some(c=>contextCaptureVisible(map,c))?'Inside capture · no mapped feature in this view':'Outside captured geometry · use Explore captured area in Layers';
}
function energyHit(map,x,y){if(!layerOn('energy')||!['overview','globe'].includes(state.view)||map instanceof ResearchMap&&map.level<2)return null;const distance=(p,a,b)=>{const dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);};return [...(map.energyPaths||[])].reverse().find(row=>{let inside=false;if(row.closed)for(let i=0,j=row.pts.length-1;i<row.pts.length;j=i++){const a=row.pts[i],b=row.pts[j];if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;}return inside||row.pts.some((b,i)=>i&&distance({x,y},row.pts[i-1],b)<7);})?.feature;}
const layerOriginalSceneDraw=CampusScene.prototype.draw;
CampusScene.prototype.draw=function(){const labels=this.labels;if(energyFeature())this.labels=false;layerOriginalSceneDraw.call(this);this.labels=labels;energyDraw(this);};
const layerOriginalHit=CampusScene.prototype.hit;
CampusScene.prototype.hit=function(event){const roof=layerOriginalHit.call(this,event);if(roof)return roof;const r=this.canvas.getBoundingClientRect(),f=energyHit(this,event.clientX-r.left,event.clientY-r.top);return f?{record:{id:f.id},energy:true}:null;};
const layerOriginalInspect=CampusScene.prototype.inspect;
CampusScene.prototype.inspect=function(id,notify=true){if(energyFeature(id)){energySelect(id);return true;}if(notify)energyState.feature=null;return layerOriginalInspect.call(this,id,notify);};
const layerOriginalRail=workspaceRail;
workspaceRail=function(...args){const f=layerOn('energy')&&energyFeature();return f?energyRail(f):layerOriginalRail(...args);};
const layerOriginalMobileRail=workspaceMobileRail;
workspaceMobileRail=function(...args){const html=layerOriginalMobileRail(...args),f=layerOn('energy')&&energyFeature();if(!f)return html;const n=document.createElement('div');n.innerHTML=html;n.querySelector('#workspace-selection-detail').innerHTML=energyRail(f);const b=n.querySelector('[data-workspace-inspector]');b.querySelector('small').textContent='SELECTED CONTEXT FEATURE';b.querySelector('strong').textContent=energyName(f);b.querySelector('span>span').textContent=energyVoltage(f)+' · snapshot '+energyCurrentCollection().captured_at.slice(0,10);return n.innerHTML;};
const layerOriginalToolbar=workspaceToolbar;
workspaceToolbar=function(...args){return layerOriginalToolbar(...args).replace('<div class="workspace-tools">','<div class="workspace-tools"><button class="map-layer-launch" data-layer-open>Layers ▱</button>');};
function layerLegend(){return `${layerOn('locations')||layerOn('energy')||layerOn('roads')&&globe?.localRoadPaths?.length?`<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors · ODbL</a>`:''}${layerOn('roads')&&globe?.localRoadPaths?.length?`<span class="road-legend">— Local OSM roads · ${ROAD_CONTEXT.captured_at.slice(0,10)}</span>`:''}${layerOn('energy')?`<span class="energy-legend">— ${esc(globe instanceof CampusScene?energyCurrentCollection().title:'Electricity · three local captures')} · ${energyCurrentCollection().captured_at.slice(0,10)}</span><span class="map-layer-coverage-state">Updating view coverage…</span>`:''}`;}
function layerDecorate(){workspaceSelectionNotice();document.querySelectorAll('[data-campus-frame=feature]').forEach(el=>el.disabled=!!energyFeature()||!campusFeature());if(!['overview','globe'].includes(state.view))return;const panel=document.querySelector('.atlas-workspace .atlas-map-panel');if(!panel)return;panel.querySelector('.energy-route-recovery')?.remove();if(energyState.recovery)panel.insertAdjacentHTML('afterbegin',energyRecoveryContent());let legend=panel.querySelector('.map-layer-attribution');if(!legend){legend=document.createElement('div');legend.className='map-layer-attribution';panel.append(legend);}legend.innerHTML=layerLegend();legend.hidden=!legend.innerHTML;panel.querySelectorAll('.atlas-map-legend>span').forEach(node=>{node.hidden=node.classList.contains('workspace-context-key')?!layerOn('locations'):node.classList.contains('atlas-line-key')?!layerOn('roads')&&!layerOn('boundaries'):!layerOn('research');if(node.classList.contains('atlas-line-key'))node.textContent=layerOn('roads')&&layerOn('boundaries')?'Generalized roads & boundaries':layerOn('roads')?'Generalized roads':'Generalized boundaries';});}
const layerOriginalRender=render;render=function(){if(window.ATLAS_BOOTSTRAPPING)return;layerOriginalRender();layerDecorate();};
const layerOriginalNav=renderNav;renderNav=function(){layerOriginalNav();const f=energyFeature();if(f&&['overview','globe'].includes(state.view))$('#breadcrumb').textContent+=' › Context: '+energyName(f);};
const layerOriginalURL=spatialURL;spatialURL=function(view=state.view){
 const url=layerOriginalURL(view);if(!['overview','globe'].includes(view))return url;const p=new URLSearchParams(url.split('?')[1]||'');
 for(const id of ['research','locations','boundaries'])if(!layerOn(id))p.set(id,'0');if(layerOn('energy'))p.set('energy','1');
 const c=energyCollection(energyState.collection),f=energyFeature();
 if(layerOn('energy')&&c){p.set('energycollection',c.id);p.set('energyversion',c.response_sha256);}
 if(layerOn('energy')&&f){p.set('energyfeature',f.id);p.set('energyobjectversion',String(f.version));p.set('selection','context');p.delete('feature');p.delete('claim');if(campusState.feature)p.set('lastfeature',campusState.feature);}
 if(layerOn('energy')&&energyState.returnPhysical)p.set('physicalreturn',energyState.returnPhysical);
 if(layerOn('energy')&&energyState.recovery?.physicalreturn)p.set('requestedphysicalreturn',energyState.recovery.physicalreturn);
 if(layerOn('energy')&&energyState.recovery)for(const key of ['collection','version','feature','objectversion'])if(energyState.recovery[key])p.set('requestedenergy'+key,energyState.recovery[key]);
 return '#'+view+'?'+p.toString();
};
const layerOriginalRoute=routeFromHash;window.removeEventListener('hashchange',layerOriginalRoute);
routeFromHash=function(){if(window.ATLAS_BOOTSTRAPPING)return;const [path,q='']=location.hash.slice(1).split('?'),p=new URLSearchParams(q);if(['','overview','globe'].includes(path)){for(const id of ['research','locations','boundaries'])state[layerFields[id]]=p.get(id)!=='0';state.spatialEnergy=p.get('energy')==='1';energyState.sourceCollection=null;energyReadRoute(p);}layerOriginalRoute();};window.addEventListener('hashchange',routeFromHash);
const layerOriginalTransition=spatialTransition;spatialTransition=function(update={}){if(update.selected){energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;}layerOriginalTransition(update);};
const layerOriginalOpen=openDrawer;openDrawer=function(kind,id,opts){layerOriginalOpen(kind,id,opts);if(kind==='map-layers'){energyState.focusReturn=true;$('#drawer-type').textContent='MAP LAYERS & COVERAGE';$('#drawer-content').innerHTML=layerPanelContent();}if(kind==='road-source'){$('#drawer-type').textContent='LOCAL ROADS / NATIVE SOURCE';$('#drawer-content').innerHTML=roadSourceContent();}if(kind==='electricity-source'){energyState.sourceCollection=id||null;$('#drawer-type').textContent='ELECTRICITY / NATIVE SOURCE';$('#drawer-content').innerHTML=energySourceContent();}};ATLAS.openDrawer=openDrawer;
const layerOriginalClose=closeDrawer;closeDrawer=function(){const focus=energyState.focusReturn;layerOriginalClose();if(focus&&$('#drawer').hidden){energyState.focusReturn=false;document.querySelector('[data-layer-open]')?.focus({preventScroll:true});}};
document.addEventListener('change',event=>{const id=event.target.dataset.mapLayer;if(!layerFields[id])return;state[layerFields[id]]=event.target.checked;if(id==='energy'&&!event.target.checked){energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;energyRefreshRail();}if(globe){if(id==='labels')globe.labels=event.target.checked;globe.dirty=true;}layerDecorate();workspaceState.drawerRoute=spatialURL();history.replaceState(null,'',workspaceState.drawerRoute);});
document.addEventListener('click',event=>{
 if(event.target.closest('[data-layer-open]'))openDrawer('map-layers');if(event.target.closest('[data-energy-source]'))openDrawer('electricity-source');
 const source=event.target.closest('[data-energy-collection-source]');if(source)openDrawer('electricity-source',source.dataset.energyCollectionSource);
 const f=event.target.closest('[data-energy-feature]');if(f)energySelect(f.dataset.energyFeature,f.dataset.energyCollection);
 if(event.target.closest('[data-energy-clear]'))energyClearSelection();
 const coverage=event.target.closest('[data-energy-collection-coverage]');if(coverage)energyExploreCapture(coverage.dataset.energyCollectionCoverage);else if(event.target.closest('[data-layer-coverage]'))energyExploreCapture(energyCurrentCollection().id);
 if(event.target.closest('[data-energy-recover]')){energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;energyState.collection=ENERGY_COLLECTIONS.find(c=>c.scene_id===campusScene()?.id)?.id||ENERGY_COLLECTIONS[0].id;render();history.pushState(null,'',spatialURL());}
 if(event.target.closest('[data-energy-export]')){const c=$('#drawer').hidden?energyCurrentCollection():energySourceCollection(),f=c.id===energyState.collection?energyFeature():null;download('compute-atlas-'+c.id+'.json',{...c,source_version:{collection_id:c.id,response_sha256:c.response_sha256,feature_id:f?.id||null,native_version:f?.version||null}});}
});
document.addEventListener('click',event=>{if(event.target.closest('[data-campus-feature],[data-campus-open-feature],[data-workspace-phase],[data-campus-mode="evidence"],[data-campus-component-button],[data-workspace-location="true"]')){energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;}},true);
document.addEventListener('atlas-campus-feature',()=>{energyState.feature=null;energyState.recovery=null;energyState.returnPhysical=null;},true);
document.addEventListener('change',event=>{if(event.target.matches('[data-campus-component]')){energyState.feature=null;energyState.collection=null;energyState.recovery=null;energyState.returnPhysical=null;}},true);
document.addEventListener('click',event=>{
 if(event.target.closest('[data-road-source]'))openDrawer('road-source');
 if(event.target.closest('[data-road-export]'))download('compute-atlas-community-road-context.json',ROAD_CONTEXT);
 if(event.target.closest('[data-road-coverage]')){
  closeDrawer();state.spatialRoads=true;spatialTransition({level:3,selected:'coreweave-helios'});
  if(globe instanceof ResearchMap){const b=ROAD_CONTEXT.coverage_bbox;globe.bounds=[b[0]-.008,b[1]-.008,b[2]+.008,b[3]+.008];globe.zoom=1;globe.target=null;globe.dirty=true;state.spatialCamera[globe.cameraKey]=globe.snapshot();workspaceSyncURL();}
 }
});
function energyReview(f){return f&&POWER_REVIEWS.reviews.find(r=>r.native_feature_id===f.id&&r.native_version===f.version&&r.captured_response_sha256===energyCurrentCollection().response_sha256);}
function energyReviewContent(f){const r=energyReview(f);if(!r)return '';return `<section class="energy-reviewed-identity"><h2>Separately reviewed interpretation</h2><p><b>${esc(r.name)}</b> · ${esc(r.precision)}</p>${atlasRow('Reported operator',esc(r.reported_operator))}${atlasRow('Reported voltage',fmt(r.reported_voltage_kv)+' kV · operator statement')}${atlasRow('Operator depiction',esc(r.depiction_period)+' · exact photo day unknown')}${atlasRow('Source published',esc(r.published_at))}${atlasRow('Identity reviewed',esc(r.reviewed_at)+' · '+esc(r.reviewed_by))}<p>${esc(r.basis)}</p>${r.transformer_scope?`<p>Up to ${fmt(r.transformer_scope.value)} ${esc(r.transformer_scope.unit)} · ${esc(r.transformer_scope.boundary)}.</p>`:''}<p>${esc(r.scope)}. No energized status or IT load is established. Native tags remain unchanged.</p><a href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.locator)} →</a><p class="campus-source-hash">Reviewed native record SHA-256: ${esc(r.native_record_sha256)}</p><button class="btn" data-energy-review-export>Export reviewed correspondence ↓</button></section>`;}
const energyNativeSourceContent=energySourceContent;
energySourceContent=function(){const f=energySourceFeature();return energyNativeSourceContent()+(f?atlasRow('Source-tagged voltage',esc(energyVoltage(f))):'')+energyReviewContent(f);};
const energyNativeRail=energyRail;
energyRail=function(f){const r=energyReview(f),html=energyNativeRail(f);return r?html.replace('<h2>'+esc(energyName(f))+'</h2>','<h2>'+esc(energyName(f))+'</h2><p class="energy-reviewed-caption">Reviewed correspondence: '+esc(r.name)+'<small>'+esc(r.precision)+' · operator depiction '+esc(r.depiction_period)+'</small></p>'):html;};
document.addEventListener('click',event=>{if(event.target.closest('[data-energy-review-export]')){const f=energyFeature(),r=energyReview(f);if(r)download(r.id+'.json',{policy:POWER_REVIEWS.policy,native_feature:f,review:r});}});

ATLAS.layers={state:energyState,data:POWER_CONTEXT,collections:ENERGY_COLLECTIONS,collection:energyCollection,roads:ROAD_CONTEXT,select:energySelect,hit:energyHit,on:layerOn};
if(ATLAS_ENTRY_HASH)history.replaceState(null,'',ATLAS_ENTRY_HASH);
routeFromHash();
// Install the selection notice only once this module's layer helpers exist.
// Hosted scripts load separately while the geographic map is already drawing.
document.addEventListener('atlas-camera-change',workspaceSelectionNotice);
if(!window.ATLAS_BOOTSTRAPPING)document.documentElement.classList.add('research-ready','atlas-ready','workspace-ready','campus-ready','layers-ready');
