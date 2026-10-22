'use strict';
/* A common discovery index, not a cross-source identity merge. Native records
   remain the authority; no coordinates, power or roles are transferred. */
const inventoryState={q:'',collection:'all',country:'all',operator:'',company:'all',coverage:'all',sort:'name',page:0,selected:null};
const INVENTORY_COLLECTIONS={projects:'Research projects',osm:'Community map',equinix:'Equinix directory',digital:'Digital Realty directory'};
let inventoryCache={inputs:[],rows:[]};
const inventoryValues=value=>value==null?'':Array.isArray(value)?value.map(inventoryValues).join(' '):typeof value==='object'?Object.values(value).map(inventoryValues).join(' '):String(value);
const inventoryText=value=>String(value??'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
function inventoryRecords(){
  const inputs=[CATALOG,OPERATOR_DIRECTORY,DIGITAL_REALTY,ATLAS_PRIMARY.facts,ATLAS_PRIMARY.observations,ATLAS_PRIMARY.relationships];
  if(inputs.some((x,i)=>x!==inventoryCache.inputs[i])){
    const project=D.sites.map(s=>{
      const p=atlasResearchProfile(s);
      return {id:s.id,collection:'projects',name:s.name,country:s.country,place:s.location,operator:s.owner_label,
        lat:s.lat,lon:s.lon,geometry:null,kind:'Research project',date:p.latest||s.snapshot?.date||s.target?.date||null,
        snapshot_mw:spatialPower(s,'snapshot'),target_mw:spatialPower(s,'target'),claims:p.rows.length,
        coordinate_basis:s.coordinate_precision||'Approximate archival anchor',source_urls:p.sources.map(r=>r.url).filter(Boolean),native:s,
        search:[inventoryValues(s.hardware),...p.searchRows.map(r=>r.text)].join(' ')};
    });
    const osm=CATALOG.records.map(r=>({...r,collection:'osm',place:[r.city,r.address].filter(Boolean).join(' · '),
      date:r.updated_at,snapshot_mw:null,target_mw:null,claims:0,source_urls:[r.source_url],native:r,search:Object.values(r.tags||{}).join(' ')}));
    const directory=(d,collection)=>d.records.map(r=>({...r,collection,country:r.source_country||'Not supplied',place:r.metro,
      lat:r.coordinates?.lat??null,lon:r.coordinates?.lon??null,geometry:null,kind:r.facility_type,
      coordinate_basis:r.coordinates?.basis||'No source coordinates',date:d.captured_at,snapshot_mw:null,target_mw:null,claims:0,
      source_urls:[r.source_url],native:r,search:[r.code,r.service_coverage].join(' ')}));
    const rows=[...project,...osm,...directory(OPERATOR_DIRECTORY,'equinix'),...directory(DIGITAL_REALTY,'digital')];
    rows.forEach(r=>{r.search=inventoryText([r.id,r.name,r.country,r.place,r.operator,r.search].join(' '));r.mapped=spatialFinite(r.lat)&&spatialFinite(r.lon);});
    inventoryCache={inputs,rows};
  }
  return inventoryCache.rows;
}
const inventoryRecord=id=>inventoryRecords().find(r=>r.id===id);
function inventoryRows(){
  const st=inventoryState,tokens=inventoryText(st.q).trim().split(/\s+/).filter(Boolean),operator=inventoryText(st.operator).trim();
  return inventoryRecords().filter(r=>(st.collection==='all'||r.collection===st.collection)&&(st.country==='all'||r.country===st.country)
    &&(st.company==='all'||r.collection==='projects'&&[...r.native.company_ids,...primaryRelationships(r.native).map(x=>x.company_id)].includes(st.company))
    &&(!operator||inventoryText(r.operator).includes(operator))&&tokens.every(q=>r.search.includes(q))
    &&(st.coverage==='all'||st.coverage==='mapped'&&r.mapped||st.coverage==='footprint'&&r.geometry
      ||st.coverage==='power'&&(r.snapshot_mw!=null||r.target_mw!=null)||st.coverage==='claims'&&r.claims>0||st.coverage==='unmapped'&&!r.mapped))
    .sort((a,b)=>(st.sort==='newest'?String(b.date||'').localeCompare(String(a.date||'')):st.sort==='power'?(b.snapshot_mw??-1)-(a.snapshot_mw??-1):st.sort==='country'?a.country.localeCompare(b.country):0)||a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
}
function inventoryURL(){
  const p=new URLSearchParams();for(const [k,v] of Object.entries(inventoryState))if(v!=null&&v!==''&&v!=='all'&&!(k==='sort'&&v==='name')&&!(k==='page'&&!v))p.set(k,String(v));
  return '#inventory'+(p.size?'?'+p:'');
}
function inventoryGo(patch={},replace=false){
  const alreadyHere=state.view==='inventory';clearTimeout(inventoryTimer);if(state.tour>=0)endTour();closeDrawer();
  Object.assign(inventoryState,{page:0},patch);state.view='inventory';
  history[replace?'replaceState':'pushState'](null,'',inventoryURL());render();history.replaceState(null,'',inventoryURL());
  document.querySelector('#sidebar')?.classList.remove('open');if(!alreadyHere)window.scrollTo({top:0,behavior:'instant'});
}
function inventoryRoute(query){
  const p=new URLSearchParams(query),countries=new Set(inventoryRecords().map(r=>r.country));
  Object.assign(inventoryState,{q:(p.get('q')||'').slice(0,500),operator:(p.get('operator')||'').slice(0,200),company:company(p.get('company'))?p.get('company'):'all',
    collection:Object.hasOwn(INVENTORY_COLLECTIONS,p.get('collection'))?p.get('collection'):'all',country:countries.has(p.get('country'))?p.get('country'):'all',
    coverage:['mapped','footprint','power','claims','unmapped'].includes(p.get('coverage'))?p.get('coverage'):'all',sort:['newest','power','country'].includes(p.get('sort'))?p.get('sort'):'name',
    page:Math.max(0,Math.min(1000,parseInt(p.get('page'))||0)),selected:(p.get('selected')||'').slice(0,500)||null});
  navigate('inventory',{hash:true});
}
function inventoryCounts(rows){return Object.fromEntries(Object.keys(INVENTORY_COLLECTIONS).map(k=>[k,rows.filter(r=>r.collection===k).length]));}
function inventoryList(rows=inventoryRows()){
  const size=20,pages=Math.max(1,Math.ceil(rows.length/size));inventoryState.page=Math.min(pages-1,inventoryState.page);
  return `<div class="inventory-results-head"><p role="status">${fmt(rows.length)} source records${rows.length?' · '+(inventoryState.page*size+1)+'–'+Math.min(rows.length,(inventoryState.page+1)*size):''}</p><label>Sort <select id="inventory-sort">${[['name','Name'],['country','Country'],['newest','Latest source date'],['power','Snapshot IT estimate']].map(([v,t])=>`<option value="${v}" ${inventoryState.sort===v?'selected':''}>${t}</option>`).join('')}</select></label></div>
  <div class="inventory-records">${rows.slice(inventoryState.page*size,(inventoryState.page+1)*size).map(r=>`<button class="inventory-record ${r.id===inventoryState.selected?'selected':''}" data-inventory-select="${esc(r.id)}" aria-pressed="${r.id===inventoryState.selected}"><span><small>${INVENTORY_COLLECTIONS[r.collection]}</small><strong>${esc(r.name)}</strong><span>${esc([r.place,r.country].filter(Boolean).join(' · '))}</span></span><span class="inventory-record-meta"><span>${esc(r.operator||'Operator not tagged')}</span><small>${r.geometry?'Source footprint':r.mapped?'Map location':'No source coordinates'}${r.claims?' · '+r.claims+' cited claims':''}</small><b>${r.snapshot_mw!=null?fmt(r.snapshot_mw)+' MW · snapshot IT':r.target_mw!=null?fmt(r.target_mw)+' MW · target IT':esc(r.kind||'Source record')}</b></span></button>`).join('')||'<div class="empty"><h2>No matching records.</h2><p>Try a broader place, company or coverage filter.</p><button class="btn" data-inventory-reset>Clear filters</button></div>'}</div>
  <div class="operator-pagination"><button class="btn small" data-inventory-page="-1" ${inventoryState.page===0?'disabled':''}>← Previous</button><span>Page ${inventoryState.page+1} of ${pages}</span><button class="btn small" data-inventory-page="1" ${inventoryState.page>=pages-1?'disabled':''}>Next →</button></div>`;
}
function inventoryLink(r){
  if(r.collection==='projects')return `<button class="btn primary" data-atlas-action="campus" data-id="${esc(r.id)}">Explore campus →</button><button class="btn" data-atlas-action="evidence-desk" data-id="${esc(r.id)}">Read evidence</button><button class="text-button" data-workspace-compare="${esc(r.id)}">${saved.projectCompare.includes(r.id)?'✓ Comparing':'Compare +'}</button>`;
  if(r.collection==='osm')return `<button class="btn primary" data-catalog-open="${esc(r.id)}">${r.geometry?'Explore source geometry':'Explore map location'} →</button>`;
  if(r.collection==='equinix')return `<button class="btn primary" data-inventory-native="${esc(r.id)}">Operator details & map candidates →</button>`;
  return `<button class="btn primary" data-inventory-native="${esc(r.id)}">Explore publisher location →</button>`;
}
function inventoryPreview(r){
  if(!r.mapped)return `<div class="inventory-no-location"><span>${icon('facilities')}</span><strong>${esc(r.place||r.country)}</strong><p>The publisher lists this facility without coordinates. Its source details remain available below.</p></div>`;
  if(r.collection==='osm'&&r.geometry)return `<div class="inventory-scene"><canvas id="inventory-scene" tabindex="0" aria-label="Source footprint preview. Drag or arrow keys to orbit, scroll or plus and minus to zoom; Home resets."></canvas><span>Community outline · illustrative height disabled</span></div>`;
  const lon=r.lon,lat=r.lat,project=coordinates=>coordinates.map(([x,y])=>[(x+180)/360*400,(90-y)/180*200]);
  // A location overview uses bundled Natural Earth geometry, never a generated footprint.
  const paths=W.lines.map(ring=>project(ring).map(([x,y],i)=>(i?'L':'M')+x.toFixed(1)+','+y.toFixed(1)).join(' ')+' Z').join(' ');
  return `<div class="inventory-location"><svg viewBox="0 0 400 200" role="img" aria-label="Location overview of ${esc(r.name)}"><path d="${paths}"/><circle cx="${(lon+180)/360*400}" cy="${(90-lat)/180*200}" r="4"/></svg><p>${fmt(lat,4)}°, ${fmt(lon,4)}° · ${esc(r.coordinate_basis)}</p></div>`;
}
function inventoryInspector(rows=inventoryRows()){
  const id=inventoryState.selected,r=inventoryRecord(id);
  if(id&&!r)return `<section class="inventory-inspector"><h2>Record unavailable.</h2><p><code>${esc(id)}</code> is absent from this publication. The bookmark and private note are preserved.</p><button class="btn" data-inventory-close>Browse records</button>${inventoryNote(id)}</section>`;
  if(!r)return `<section class="inventory-inspector inventory-welcome"><div class="eyebrow">ONE DIRECTORY / DISTINCT SOURCES</div><h2>Find a place.<br>Follow its evidence.</h2><p>Search names, places, operators, addresses and project disclosures. Select a record to inspect its source and open its map or dossier.</p><dl>${Object.entries(inventoryCounts(inventoryRecords())).map(([k,n])=>`<div><dt>${INVENTORY_COLLECTIONS[k]}</dt><dd>${fmt(n)}</dd></div>`).join('')}</dl><p>These collections can describe the same place. Their record counts are shown separately and do not form a facility census.</p><button class="btn" data-action="nav" data-id="catalog">Explore the worldwide map →</button></section>`;
  const source=r.collection==='osm'?CATALOG:r.collection==='equinix'?OPERATOR_DIRECTORY:r.collection==='digital'?DIGITAL_REALTY:null,p=r.collection==='projects'?atlasResearchProfile(r.native):null;
  return `<section class="inventory-inspector" data-inventory-detail="${esc(r.id)}"><header><div><div class="eyebrow">${INVENTORY_COLLECTIONS[r.collection]}</div><h2 tabindex="-1" id="inventory-detail-title">${esc(r.name)}</h2></div><button class="text-button" data-inventory-close aria-label="Close selected record">×</button></header>${!rows.some(x=>x.id===id)?'<div class="notice">Selected record is outside these filters. <button class="text-button" data-inventory-reveal>Show in results</button></div>':''}
    ${inventoryPreview(r)}<p>${esc([r.place,r.country].filter(Boolean).join(' · '))}</p><div class="inventory-detail-actions">${inventoryLink(r)}</div>
    <dl><div><dt>Source identity</dt><dd><code>${esc(r.id)}</code></dd></div><div><dt>Operator / association</dt><dd>${esc(r.operator||'Not supplied')}</dd></div><div><dt>Record type</dt><dd>${esc(r.kind||'Source feature')}</dd></div>${p?`<div><dt>Snapshot IT estimate</dt><dd>${r.snapshot_mw==null?'Not quantified':fmt(r.snapshot_mw)+' MW'}<small>${esc(r.native.snapshot?.date||'')}</small></dd></div><div><dt>Target IT estimate</dt><dd>${r.target_mw==null?'Not quantified':fmt(r.target_mw)+' MW'}<small>${esc(r.native.target?.date||'')}</small></dd></div>`:`<div><dt>Source captured</dt><dd>${esc(source?.captured_at?.slice(0,10)||'Not supplied')}</dd></div>${r.collection==='osm'?`<div><dt>Map version / edited</dt><dd>${esc(r.native.source_version)} · ${esc(r.date?.slice(0,10)||'Undated')}</dd></div>`:''}<div><dt>IT power</dt><dd>Not established by this record</dd></div>`}</dl>
    ${p?`<h3>Recent project evidence</h3>${p.rows.slice(0,3).map(atlasResearchClaim).join('')}${p.rows.length>3?`<button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(r.id)}">Read all ${p.rows.length} project claims →</button>`:''}`:`${catalogLink(r.source_urls[0],'Open original source →','btn')}<p class="footnote">${esc(source?.count_boundary||source?.policy||'')}</p>`}
    <button class="btn" data-inventory-export-record="${esc(r.id)}">Export cited record ↓</button>${inventoryNote(r.id)}</section>`;
}
function inventoryNote(id,prefix='inventory'){return `<details class="inventory-note"><summary>Private research note${saved.notes[id]?' · saved':''}</summary><label for="${prefix}-note">Questions to revisit</label><textarea id="${prefix}-note" data-note="${esc(id)}">${esc(saved.notes[id]||'')}</textarea><p data-storage-status>${storageOK?'Private · saved in this browser':'Session-only · export before closing'}</p></details>`;}
function inventoryView(){
  const rows=inventoryRows(),counts=inventoryCounts(rows),countries=[...new Set(inventoryRecords().map(r=>r.country))].sort();
  return `<div class="inventory-page">${pagehead('FACILITY DIRECTORY','Find the infrastructure.','Projects, source geometry and operator listings in one searchable workspace. Every record retains its own evidence and identity.',`<button class="btn" data-inventory-export>Export filtered records ↓</button>`)}
    <div class="inventory-collections" aria-label="Source collections"><button data-inventory-collection="all" aria-pressed="${inventoryState.collection==='all'}">All sources<span>Browse together</span></button>${Object.entries(INVENTORY_COLLECTIONS).map(([k,label])=>`<button data-inventory-collection="${k}" aria-pressed="${inventoryState.collection===k}">${label}<span>${fmt(counts[k])} matching records</span></button>`).join('')}</div>
    <div class="inventory-filters"><label>Find a place or disclosure<input id="inventory-query" type="search" value="${esc(inventoryState.q)}" placeholder="Frankfurt, cooling, FR2, Helios…" maxlength="500"></label><label>Country / source group<select id="inventory-country"><option value="all">All countries</option>${countries.map(c=>`<option value="${esc(c)}" ${inventoryState.country===c?'selected':''}>${esc(c)}</option>`).join('')}</select></label><label>Operator<input id="inventory-operator" type="search" value="${esc(inventoryState.operator)}" placeholder="Any operator" maxlength="200"></label><label>Available evidence<select id="inventory-coverage">${[['all','All records'],['footprint','Source footprint'],['mapped','Map coordinates'],['power','IT estimate'],['claims','Project disclosures'],['unmapped','No coordinates']].map(([v,t])=>`<option value="${v}" ${inventoryState.coverage===v?'selected':''}>${t}</option>`).join('')}</select></label><button class="text-button" data-inventory-reset>Reset</button></div>
    ${inventoryState.company!=='all'?`<p class="notice">Projects associated with ${esc(company(inventoryState.company)?.name)} <button class="text-button" data-inventory-clear-company>Remove company filter ×</button></p>`:''}
    <div class="inventory-layout"><section id="inventory-results" aria-label="Facility source records">${inventoryList(rows)}</section><aside id="inventory-inspector" aria-label="Selected source record">${inventoryInspector(rows)}</aside></div>
    <footer class="catalog-provenance">Community geometry © OpenStreetMap contributors · ODbL. Directory locations follow each publisher’s geography. Overlapping records are not deduplicated or summed as capacity.<button class="text-button" data-action="nav" data-id="facilities">Open original capacity archive →</button></footer></div>`;
}
function inventoryMount(){
  const r=inventoryRecord(inventoryState.selected),canvas=$('#inventory-scene');
  if(canvas&&r){globe=new FacilityScene(canvas,r.native);globe.assumptions=false;globe.pitch=1.48;globe.dirty=true;}
}
function inventoryUpdate(){
  if(state.view!=='inventory')return;inventoryState.page=0;
  if(globe){globe.destroy();globe=null;}
  const rows=inventoryRows();$('#inventory-results').innerHTML=inventoryList(rows);$('#inventory-inspector').innerHTML=inventoryInspector(rows);
  const counts=inventoryCounts(rows);for(const b of $$('[data-inventory-collection]'))if(b.dataset.inventoryCollection!=='all')b.querySelector('span').textContent=fmt(counts[b.dataset.inventoryCollection])+' matching records';
  history.replaceState(null,'',inventoryURL());inventoryMount();
}
function inventoryExportRows(rows){
  return {schema_version:1,exported_at:new Date().toISOString(),filters:{...inventoryState},counts_by_collection:inventoryCounts(rows),
    policy:'Source records may overlap. No cross-source identity, capacity, ownership or service relationship is inferred. Private notes excluded.',
    publications:{projects:{published_at:ATLAS_PRIMARY.published_at},osm:{captured_at:CATALOG.captured_at,license:CATALOG.license,attribution:CATALOG.attribution,attribution_url:CATALOG.attribution_url},equinix:{captured_at:OPERATOR_DIRECTORY.captured_at,url:OPERATOR_DIRECTORY.url,rights:OPERATOR_DIRECTORY.rights},digital:{captured_at:DIGITAL_REALTY.captured_at,url:DIGITAL_REALTY.url,rights:DIGITAL_REALTY.rights}},
    records:rows.map(r=>{if(r.collection==='projects'){const {private_note,...dossier}=atlasCitedDossier(r.native);return {collection:r.collection,id:r.id,dossier};}return {collection:r.collection,id:r.id,record:r.native};})};
}
let inventoryTimer;
document.addEventListener('input',e=>{if(!['inventory-query','inventory-operator'].includes(e.target.id))return;inventoryState[e.target.id==='inventory-query'?'q':'operator']=e.target.value;clearTimeout(inventoryTimer);inventoryTimer=setTimeout(inventoryUpdate,120);});
document.addEventListener('change',e=>{const key={'inventory-country':'country','inventory-coverage':'coverage','inventory-sort':'sort'}[e.target.id];if(key){inventoryState[key]=e.target.value;inventoryUpdate();}});
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b||b.disabled)return;
  if(b.hasAttribute('data-inventory-open'))inventoryGo({q:'',collection:'all',country:'all',operator:'',company:'all',coverage:'all',selected:b.dataset.inventoryOpen});
  if(b.hasAttribute('data-inventory-collection'))inventoryGo({collection:b.dataset.inventoryCollection});
  if(b.hasAttribute('data-inventory-select')){inventoryGo({selected:b.dataset.inventorySelect,page:inventoryState.page});$('#inventory-detail-title')?.focus({preventScroll:innerWidth>900});}
  if(b.hasAttribute('data-inventory-close'))inventoryGo({selected:null,page:inventoryState.page});
  if(b.hasAttribute('data-inventory-reset')||b.hasAttribute('data-inventory-reveal'))inventoryGo({q:'',collection:'all',country:'all',operator:'',company:'all',coverage:'all',sort:'name',page:0});
  if(b.hasAttribute('data-inventory-clear-company'))inventoryGo({company:'all'});
  if(b.hasAttribute('data-inventory-page')){inventoryState.page+=Number(b.dataset.inventoryPage);$('#inventory-results').innerHTML=inventoryList();history.replaceState(null,'',inventoryURL());(document.querySelector(`[data-inventory-page="${b.dataset.inventoryPage}"]:not(:disabled)`)||document.querySelector('[data-inventory-page]:not(:disabled)'))?.focus({preventScroll:true});}
  if(b.hasAttribute('data-inventory-export'))download('compute-atlas-directory.json',inventoryExportRows(inventoryRows()));
  if(b.hasAttribute('data-inventory-export-record')){const r=inventoryRecord(b.dataset.inventoryExportRecord);if(r)download('compute-atlas-'+r.id+'.json',inventoryExportRows([r]));}
  if(b.hasAttribute('data-inventory-native')){const r=inventoryRecord(b.dataset.inventoryNative);if(r?.collection==='equinix')operatorGo({region:'All',country:'All',q:'',match:'All',selected:r.id});if(r?.collection==='digital')publisherGo({region:'All',country:'All',q:'',review:'All',selected:r.id});}
});
NAV.splice(NAV.findIndex(([id])=>id==='facilities'),0,['inventory','Facility directory']);
NAV.find(([id])=>id==='facilities')[1]='Capacity archive';
const inventoryBaseRender=render;
render=function(){if(window.ATLAS_BOOTSTRAPPING)return;if(state.view!=='inventory')return inventoryBaseRender();if(globe){globe.destroy();globe=null;}renderNav();$('#content').innerHTML=inventoryView();inventoryMount();};
const inventoryBaseRoute=routeFromHash;window.removeEventListener('hashchange',inventoryBaseRoute);
routeFromHash=function(){if(window.ATLAS_BOOTSTRAPPING)return;const [path,q='']=location.hash.slice(1).split('?');if(path==='inventory')return inventoryRoute(q);inventoryBaseRoute();};
window.addEventListener('hashchange',routeFromHash);
ATLAS.inventory={state:inventoryState,records:inventoryRecords,record:inventoryRecord,rows:inventoryRows,go:inventoryGo,export:inventoryExportRows};
if(!window.ATLAS_BOOTSTRAPPING){if(location.hash.startsWith('#inventory'))routeFromHash();else render();}
