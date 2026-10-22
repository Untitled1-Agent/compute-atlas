'use strict';
/* Inspect source context without turning proximity into project identity. */
const locationDiscovery={query:'',page:0};
function mappedLocationHit(map,x,y){return (map.locationHits||[]).map(p=>({...p,d:Math.hypot(p.x-x,p.y-y)})).filter(p=>p.d<7).sort((a,b)=>a.d-b.d)[0]?.record||null;}
function locationDiscoveryRows(){
  const q=inventoryText(locationDiscovery.query).trim();
  return (globe instanceof ResearchMap?globe.locationHits||[]:[]).map(p=>p.record)
    .filter(r=>!q||inventoryText([r.name,r.operator,r.city,r.address,r.country].join(' ')).includes(q))
    .sort((a,b)=>a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
}
function locationDiscoveryList(){
  const rows=locationDiscoveryRows(),size=10,pages=Math.max(1,Math.ceil(rows.length/size));locationDiscovery.page=Math.min(pages-1,locationDiscovery.page);
  return `<p role="status">${fmt(rows.length)} matching visible community records · source capture ${esc(CATALOG.captured_at.slice(0,10))}</p><div class="location-discovery-list">${rows.slice(locationDiscovery.page*size,(locationDiscovery.page+1)*size).map(r=>`<button data-location-inspect="${esc(r.id)}"><strong>${esc(r.name)}</strong><span>${esc(r.operator||'Operator not tagged')} · ${esc(r.country)}</span><small>${r.geometry?'Source geometry':'Point only'} · ${esc(r.kind)}</small></button>`).join('')||'<p>No community records in this view match. Pan, zoom out, or clear the search.</p>'}</div><div class="operator-pagination"><button class="btn small" data-location-page="-1" ${locationDiscovery.page===0?'disabled':''}>← Previous</button><span>${locationDiscovery.page+1} / ${pages}</span><button class="btn small" data-location-page="1" ${locationDiscovery.page>=pages-1?'disabled':''}>Next →</button></div>`;
}
function locationDiscoverySection(){return `<details class="location-discovery"><summary>Mapped locations in this view <span>Inspect source records ↓</span></summary><p>Community map features are independent of the capacity projects. Select a point on the map or a record below to inspect it without moving the camera.</p><label>Find a visible location<input id="location-discovery-query" type="search" value="${esc(locationDiscovery.query)}" placeholder="Name, operator, country or address…"></label><div id="location-discovery-results">${locationDiscoveryList()}</div></details>`;}
function projectGeography(s){
  if(!s||!spatialFinite(s.lat)||!spatialFinite(s.lon)||/state-level|region anchor|county anchor/i.test(s.location))return '';
  const rows=CATALOG.records.map(r=>({record:r,distance:spatialDistance(s,r)})).filter(x=>x.distance<=15).sort((a,b)=>a.distance-b.distance||a.record.id.localeCompare(b.record.id));
  if(!rows.length)return '';
  return `<details class="location-discovery project-geography"><summary>Explore local map records <span>${rows.length} within 15 km of the archive anchor ↓</span></summary><p>The project anchor is approximate. These nearby records may describe unrelated operators or overlapping features; proximity does not establish this project’s buildings or ownership.</p><div class="location-discovery-list">${rows.slice(0,12).map(({record:r,distance})=>`<button data-location-inspect="${esc(r.id)}"><strong>${esc(r.name)}</strong><span>${esc(r.operator||'Operator not tagged')} · ${fmt(distance,1)} km from archive anchor</span><small>${esc(r.kind)} · ${r.geometry?'source geometry':'point only'}</small></button>`).join('')}</div>${rows.length>12?'<p>Nearest 12 shown. Explore the worldwide map to inspect the wider collection.</p>':''}<button class="btn" data-action="nav" data-id="inventory">Search all source records →</button></details>`;
}
function locationFootprint(r){
  if(!r.geometry)return '';
  const points=r.geometry.coordinates.flat(2),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),minx=Math.min(...xs),miny=Math.min(...ys),dx=Math.max(...xs)-minx,dy=Math.max(...ys)-miny,k=Math.cos(r.lat*Math.PI/180);
  const scale=Math.min(360/Math.max(dx*k,.000001),200/Math.max(dy,.000001)),cx=minx+dx/2,cy=miny+dy/2;
  const path=r.geometry.coordinates.map(poly=>poly.map(ring=>ring.map(([x,y],i)=>(i?'L':'M')+(200+(x-cx)*k*scale).toFixed(2)+','+(120-(y-cy)*scale).toFixed(2)).join(' ')+' Z').join(' ')).join(' ');
  return `<svg class="location-footprint" viewBox="0 0 400 240" role="img" aria-label="Plan of the source mapped ${esc(r.kind)} outline"><path d="${path}" fill-rule="evenodd"/></svg>`;
}
function mappedLocationContent(id){
  const r=catalogFeature(id);if(!r)return '<h1>Source location unavailable.</h1><p>This record is absent from the current publication.</p>';
  return `<div class="eyebrow">COMMUNITY MAP RECORD</div><h1>${esc(r.name)}</h1><p>${esc([r.address,r.city,r.country].filter(Boolean).join(' · '))}</p>${locationFootprint(r)}<div class="inventory-detail-actions"><button class="btn primary" data-catalog-open="${esc(id)}">${r.geometry?'Explore geometry in 3D':'Explore map location'} →</button><button class="btn" data-inventory-export-record="${esc(id)}">Export cited record ↓</button></div>${atlasRow('Operator',esc(r.operator||'Not tagged'))}${atlasRow('Feature',esc(r.kind))}${atlasRow('Source version',esc(r.source_version))}${atlasRow('Last source edit',esc(r.updated_at||'Not supplied'))}${atlasRow('Captured',esc(CATALOG.captured_at.slice(0,10)))}${atlasRow('IT power','Not established by this map record')}<p>${esc(r.coordinate_basis)}. This feature is independent of the selected capacity project. Its name, location and geometry do not establish a project or phase correspondence.</p>${catalogLink(r.source_url,'Open original OpenStreetMap record →','btn')}<p class="footnote">© OpenStreetMap contributors · ODbL. ${r.height_m==null?'No measured height is supplied.':'Source-tagged height: '+esc(r.height_m)+' m.'}</p>${inventoryNote(id,'mapped-location')}`;
}
const locationOldTopic=workspaceTopicContent;
workspaceTopicContent=s=>locationOldTopic(s)+(workspaceState.tab==='overview'?projectGeography(s):'');
const locationOldRecords=atlasRecordList;
atlasRecordList=function(scope,phase){return locationOldRecords(scope,phase)+locationDiscoverySection();};
const locationOldOpen=openDrawer;
openDrawer=function(kind,id,opts={}){locationOldOpen(kind,id,opts);if(kind==='mapped-location'){$('#drawer-type').textContent='MAPPED SOURCE LOCATION';$('#drawer-content').innerHTML=mappedLocationContent(id);}};ATLAS.openDrawer=openDrawer;
function locationDiscoveryUpdate(){const target=$('#location-discovery-results');if(target&&target.closest('details').open)target.innerHTML=locationDiscoveryList();}
document.addEventListener('atlas-camera-change',locationDiscoveryUpdate);
document.addEventListener('toggle',e=>{if(e.target.matches?.('.location-discovery')&&e.target.open)locationDiscoveryUpdate();},true);
document.addEventListener('input',e=>{if(e.target.id==='location-discovery-query'){locationDiscovery.query=e.target.value.slice(0,500);locationDiscovery.page=0;locationDiscoveryUpdate();}});
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||b.disabled)return;if(b.hasAttribute('data-location-inspect'))openDrawer('mapped-location',b.dataset.locationInspect);if(b.hasAttribute('data-location-page')){locationDiscovery.page+=Number(b.dataset.locationPage);locationDiscoveryUpdate();}});
ATLAS.locations={rows:locationDiscoveryRows,hit:mappedLocationHit,open:id=>openDrawer('mapped-location',id)};
