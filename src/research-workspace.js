'use strict';
/* Local research bookmarks reference native identities. They never merge publications. */
const researchState={pending:null,removed:null};
const researchString=(value,max=500)=>typeof value==='string'?value.slice(0,max):'';
function researchHash(value){
  if(typeof value!=='string'||value.length>12000||!value.startsWith('#')||/[\u0000-\u001f\u007f]/.test(value))return null;
  try{decodeURIComponent(value);}catch{return null;}
  const path=value.slice(1).split(/[?/]/)[0];
  return [...NAV.map(([id])=>id),'watchlist','compare','research','site','company','source'].includes(path)?value:null;
}
function researchRecords(raw){
  const rows=Array.isArray(raw)?raw:[];
  return rows.filter(r=>r&&typeof r.id==='string'&&r.id.length>0&&r.id.length<=500&&['osm','equinix','digital'].includes(r.collection))
    .filter(r=>!inventoryRecord(r.id)||inventoryRecord(r.id).collection===r.collection)
    .filter((r,i,a)=>a.findIndex(x=>x.id===r.id)===i).slice(0,500)
    .map(r=>({id:r.id,collection:r.collection,name:researchString(r.name)||r.id,source_version:researchString(r.source_version,200),captured_at:researchString(r.captured_at,50),saved_at:researchString(r.saved_at,50)}));
}
function researchViews(raw){
  return (Array.isArray(raw)?raw:[]).filter(r=>r&&typeof r.id==='string'&&/^view-[a-zA-Z0-9_-]{1,80}$/.test(r.id)&&typeof r.name==='string'&&r.name.trim()&&researchHash(r.hash))
    .filter((r,i,a)=>a.findIndex(x=>x.id===r.id)===i).slice(0,100)
    .map(r=>({id:r.id,name:r.name.trim().slice(0,120),hash:r.hash,saved_at:researchString(r.saved_at,50)}));
}
function researchImport(x){saved.records=researchRecords(x.records);saved.views=researchViews(x.views);researchState.removed=null;}
researchImport(saved);
function researchPublication(r){return r.collection==='osm'?CATALOG:r.collection==='equinix'?OPERATOR_DIRECTORY:r.collection==='digital'?DIGITAL_REALTY:null;}
function researchVersion(r){const publication=researchPublication(r);return {source_version:String(r.native.source_version||publication?.source_version||publication?.captured_at||''),captured_at:publication?.captured_at||''};}
function researchPinned(id){return site(id)?isSaved(id):saved.records.some(r=>r.id===id);}
function researchPin(id){return `<button class="btn research-pin" data-research-pin="${esc(id)}" aria-pressed="${researchPinned(id)}">${researchPinned(id)?'Saved to shelf':'Save to shelf'}</button>`;}
function researchRefreshPins(){for(const button of document.querySelectorAll('[data-research-pin]')){const active=researchPinned(button.dataset.researchPin);button.setAttribute('aria-pressed',String(active));button.textContent=active?'Saved to shelf':'Save to shelf';}}
function researchToggle(id){
  const r=inventoryRecord(id);if(!r)return;
  if(r.collection==='projects'){saved.favorites=isSaved(id)?saved.favorites.filter(x=>x!==id):[...saved.favorites,id];}
  else if(researchPinned(id))saved.records=saved.records.filter(x=>x.id!==id);
  else{if(saved.records.length>=500){toast('500 source bookmarks saved. Export your session and remove a bookmark to add another.');return;}saved.records.push({id:r.id,collection:r.collection,name:r.name,...researchVersion(r),saved_at:new Date().toISOString()});}
  save();researchRefreshPins();toast(researchPinned(id)?'Saved to your research shelf.':'Bookmark removed. Your notes are retained.');
}
function researchCurrentHash(){
  if(state.drawer?.kind==='research-index'&&researchHash(location.hash))return location.hash;
  if(['site','company','source'].includes(state.drawer?.kind)&&researchHash(location.hash))return location.hash;
  if(state.drawer?.kind==='mapped-location')return '#inventory?selected='+encodeURIComponent(state.drawer.id);
  if(['overview','globe'].includes(state.view)){workspaceSyncURL();return spatialURL();}
  if(state.view==='inventory')return inventoryURL();
  if(state.view==='contracts')return connectionURL();
  if(state.view==='search')return discoveryURL();
  if(state.view==='catalog')return catalogURL();
  if(state.view==='operators')return operatorURL();
  if(state.view==='publisher')return publisherURL();
  if(state.view==='investment'||state.view==='costs'&&state.costTab==='scenario'){const model=modelCurrent();if(model.assumptions)return new URL(modelShareURL(model)).hash;}
  if(RESEARCH_COLLECTION_VIEWS.includes(state.view))return researchCollectionURL();
  return researchHash(location.hash)||'#'+state.view;
}
function researchSaveDrawer(id){
  const current=saved.views.find(r=>r.id===id);
  researchState.pending=current?{...current}:{hash:researchCurrentHash(),name:document.querySelector('#breadcrumb')?.textContent||'Research view'};
  $('#sidebar')?.classList.remove('open');
  openDrawer('research-view');
  $('#drawer-type').textContent=current?'RENAME SAVED VIEW':'SAVE RESEARCH VIEW';
  $('#drawer-content').innerHTML=`<h1>${current?'Name this view.':'Return to this research.'}</h1><p>Keep the current address, including its available filters and map selection. Names and notes stay private in this browser; export a session to move them.</p><form id="research-view-form"><label for="research-view-name">View name</label><input id="research-view-name" maxlength="120" required value="${esc(researchState.pending.name)}"><p class="research-saved-address">${esc(researchState.pending.hash)}</p><button class="btn primary" type="submit">${current?'Save name':'Save view'}</button><p id="research-view-status" role="status"></p></form>`;
  setTimeout(()=>$('#research-view-name')?.focus(),40);
}
function researchShelf(){
  return `<section class="research-shelf section-gap"><header><h2>Saved views</h2><p>Reopen your filters, selection and shareable model assumptions.</p></header><div class="research-shelf-grid">${saved.views.map(r=>`<article><h3>${esc(r.name)}</h3><p>${esc(NAV.find(([id])=>id===r.hash.slice(1).split('?')[0])?.[1]||'Research record')} · ${esc(r.saved_at.slice(0,10)||'Date not supplied')}</p><div><button class="btn" data-research-open-view="${esc(r.id)}">Open view →</button><button class="text-button" data-research-rename="${esc(r.id)}">Rename</button><button class="text-button" data-research-remove-view="${esc(r.id)}" aria-label="Remove view ${esc(r.name)}">Remove</button></div></article>`).join('')||'<p>Use “Save this view” in the navigation to keep a search, filtered directory, map selection or model.</p>'}</div><h2>Saved source records</h2><p>Native map and operator records remain independent of projects and each other.</p><div class="research-shelf-grid">${saved.records.map(r=>{const current=inventoryRecord(r.id),version=current?researchVersion(current):null,changed=current&&(version.source_version!==r.source_version||version.captured_at!==r.captured_at);return `<article data-research-bookmark="${esc(r.id)}"><small>${esc(INVENTORY_COLLECTIONS[r.collection])}</small><h3>${esc(r.name)}</h3><p>Saved ${esc(r.saved_at.slice(0,10)||'date not supplied')} · source capture ${esc(r.captured_at.slice(0,10)||'not supplied')}</p>${!current?'<p class="notice">Unavailable in this publication. Your bookmark and notes are retained.</p>':changed?'<p class="notice">The source publication has changed since you saved this record. Opening shows the current record; this bookmark retains its earlier version reference.</p>':''}<div><button class="btn" data-inventory-open="${esc(r.id)}">${current?'Open source record':'Inspect unavailable record'} →</button><button class="text-button" data-research-remove-record="${esc(r.id)}" aria-label="Remove bookmark ${esc(r.name)}">Remove</button></div></article>`;}).join('')||'<p>Save a mapped location or operator listing from its detail panel.</p>'}</div>${researchState.removed?'<p class="research-undo" role="status">Removed from your shelf. Private notes retained. <button class="btn small" data-research-undo>Undo removal</button></p>':''}</section>`;
}
const researchOldShelf=watchlistView;
watchlistView=function(){
  const container=document.createElement('div');container.innerHTML=researchOldShelf();
  if(!saved.models.length)container.querySelector('.model-shelf')?.remove();
  if(!Object.values(saved.notes).some(note=>note.trim()))for(const heading of container.querySelectorAll('h3'))if(heading.textContent==='Saved notes')heading.closest('section')?.remove();
  if(saved.views.length||saved.records.length||researchState.removed)container.querySelector('.page-heading')?.insertAdjacentHTML('afterend',researchShelf());
  else container.insertAdjacentHTML('beforeend',researchShelf());
  return container.innerHTML;
};
const researchOldInspector=inventoryInspector;
inventoryInspector=function(rows){const html=researchOldInspector(rows),r=inventoryRecord(inventoryState.selected);return r?html.replace('<div class="inventory-detail-actions">','<div class="inventory-detail-actions">'+researchPin(r.id)):html;};
const researchOldLocation=mappedLocationContent;
mappedLocationContent=id=>researchOldLocation(id)+ (inventoryRecord(id)?researchPin(id):'');
const researchOldOperatorRail=operatorRail;
operatorRail=()=>researchOldOperatorRail()+(inventoryRecord(operatorState.selected)?researchPin(operatorState.selected):'');
const researchOldPublisherRail=publisherRail;
publisherRail=()=>researchOldPublisherRail()+(publisherRecord(publisherState.selected)?researchPin(publisherState.selected):'');
const researchOldSceneInspector=catalogInspectScene;
catalogInspectScene=function(...args){researchOldSceneInspector(...args);const r=catalogFeature(catalogState.inspected||catalogState.feature);if(r)$('#scene-inspector-detail')?.insertAdjacentHTML('beforeend',researchPin(r.id));};
/* CSV fields remain native, dated and non-additive. Escape spreadsheet formula text. */
function researchCSV(rows){return '\ufeff'+rows.map(row=>row.map(value=>{let text=String(value??'');if(typeof value==='string'&&/^[\s\u0000-\u001f]*[=+@-]|^[\t\r\n]/.test(text))text="'"+text;return '"'+text.replace(/"/g,'""')+'"';}).join(',')).join('\r\n');}
function researchSourceMetadata(r){
  const publication=researchPublication(r);
  if(!publication)return {publication_date:ATLAS_PRIMARY.published_at,sources:atlasResearchProfile(r.native).sources};
  return {collection:r.collection,captured_at:publication.captured_at,license:publication.license||publication.rights,attribution:publication.attribution,attribution_url:publication.attribution_url,publisher_url:publication.url,record_url:r.native.source_url,source_version:researchVersion(r).source_version};
}
function researchSearchSources(r){
  if(['project','location','listing'].includes(r.type))return researchSourceMetadata(inventoryRecord(r.id));
  if(r.type==='claim')return [primarySource(r.record.source_id)].filter(Boolean);
  if(r.type==='source')return [r.record];
  if(['company','contract','cost'].includes(r.type))return ids(r.record.sources).map(source).filter(Boolean);
  return {original_file:r.record.filename||r.record.section?.filename||r.title,policy:'Original research archive; cached workbook values are not recalculated.'};
}
function researchCSVRows(kind){
  if(kind==='inventory')return [['collection','record_id','name','country','place','operator','latitude','longitude','coordinate_basis','source_date','snapshot_it_mw_estimate','snapshot_date','target_it_mw_estimate','target_date','source_version','source_capture','source_urls','source_metadata_json','native_record_json'],...inventoryRows().map(r=>[r.collection,r.id,r.name,r.country,r.place,r.operator,r.lat,r.lon,r.coordinate_basis,r.date,r.snapshot_mw,r.native.snapshot?.date,r.target_mw,r.native.target?.date,researchVersion(r).source_version,researchVersion(r).captured_at,r.source_urls.join(' | '),JSON.stringify(researchSourceMetadata(r)),JSON.stringify(r.native)])];
  if(kind==='connections')return [['record_id','kind','topic','project_id','company_ids','title','native_value','source_date','association_basis','source_ids','source_urls','source_metadata_json','native_record_json'],...connectionRows().map(r=>[r.id,r.kind,r.topic,r.site_id,r.company_ids.join(' | '),r.title,r.value,r.date,r.association,r.source_ids.join(' | '),r.source_ids.map(id=>(r.primary?primarySource(id):source(id))?.url).filter(Boolean).join(' | '),JSON.stringify(r.source_ids.map(id=>r.primary?primarySource(id):source(id)).filter(Boolean)),JSON.stringify(r.row)])];
  return [['type','record_id','title','source_context','source_metadata_json','native_record_json'],...discoveryRows().map(r=>[r.type,r.id,r.title,r.text,JSON.stringify(researchSearchSources(r)),JSON.stringify(r.record)])];
}
function researchCSVButton(kind){return `<button class="btn" data-research-csv="${kind}" ${kind==='search'&&!discoveryState.q.trim()?'disabled':''}>Export spreadsheet CSV ↓</button>`;}
const researchOldInventoryView=inventoryView;inventoryView=()=>researchOldInventoryView().replace('<button class="btn" data-inventory-export>',researchCSVButton('inventory')+'<button class="btn" data-inventory-export>');
const researchOldContractsView=contractsView;contractsView=()=>researchOldContractsView().replace('<button class="btn" data-connection-export>',researchCSVButton('connections')+'<button class="btn" data-connection-export>');
const researchOldDiscoveryView=discoveryView;discoveryView=()=>researchOldDiscoveryView().replace('<button class="btn" data-discovery-export',researchCSVButton('search')+'<button class="btn" data-discovery-export');
document.addEventListener('submit',e=>{if(e.target.id!=='research-view-form')return;e.preventDefault();const pending=researchState.pending,name=$('#research-view-name').value.trim();if(!name||!pending||!researchHash(pending.hash)){$('#research-view-status').textContent='Enter a name for a valid research view.';return;}if(!pending.id&&saved.views.length>=100){$('#research-view-status').textContent='100 views saved. Export your session and remove a view before saving another.';return;}const row={...pending,name,id:pending.id||'view-'+crypto.randomUUID(),saved_at:pending.saved_at||new Date().toISOString()},index=saved.views.findIndex(r=>r.id===row.id);if(index>=0)saved.views[index]=row;else saved.views.push(row);save();closeDrawer();if(state.view==='watchlist')render();toast('Research view saved.');});
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||b.disabled)return;
  if(b.hasAttribute('data-research-pin'))researchToggle(b.dataset.researchPin);
  if(b.hasAttribute('data-research-save-view'))researchSaveDrawer();
  if(b.hasAttribute('data-research-rename'))researchSaveDrawer(b.dataset.researchRename);
  if(b.hasAttribute('data-research-open-view')){const row=saved.views.find(r=>r.id===b.dataset.researchOpenView);if(row&&researchHash(row.hash)){closeDrawer();history.pushState(null,'',row.hash);routeFromHash();}}
  for(const [attr,key] of [['data-research-remove-view','views'],['data-research-remove-record','records']])if(b.hasAttribute(attr)){const id=b.getAttribute(attr);researchState.removed={key,row:saved[key].find(r=>r.id===id)};saved[key]=saved[key].filter(r=>r.id!==id);save();render();document.querySelector('[data-research-undo]')?.focus({preventScroll:true});}
  if(b.hasAttribute('data-research-undo')){const removed=researchState.removed;if(removed?.row&&!saved[removed.key].some(r=>r.id===removed.row.id))saved[removed.key].push(removed.row);researchState.removed=null;save();render();}
  if(b.hasAttribute('data-research-csv'))download('compute-atlas-'+b.dataset.researchCsv+'.csv',researchCSV(researchCSVRows(b.dataset.researchCsv)),'text/csv;charset=utf-8');
});
ATLAS.shelf={import:researchImport,records:researchRecords,views:researchViews,hash:researchHash,csv:researchCSV,csvRows:researchCSVRows,currentHash:researchCurrentHash};
/* Older collection screens now have restorable addresses as well as map routes. */
const RESEARCH_COLLECTION_VIEWS=['companies','reports','data','facilities','costs','compare'];
function researchCollectionURL(){
  const p=new URLSearchParams({saved:'1'}),put=values=>Object.entries(values).forEach(([k,v])=>p.set(k,String(v??'')));
  if(state.view==='companies')put({q:state.companyQ,region:state.companyRegion});
  if(state.view==='reports')put({report:state.report,section:state.section,q:state.reportQ});
  if(state.view==='data')put({tab:state.dataTab,book:state.book,sheet:state.sheet,q:state.dataQ});
  if(state.view==='facilities')put({...state.filter,layout:state.layout,sort:state.sort});
  if(state.view==='costs')put({tab:state.costTab,layer:state.costLayer,q:state.costQ});
  if(state.view==='compare')put({companies:state.compare.join(',')});
  return '#'+state.view+'?'+p;
}
const researchPreviousRoute=routeFromHash;window.removeEventListener('hashchange',researchPreviousRoute);
routeFromHash=function(){
  if(window.ATLAS_BOOTSTRAPPING)return;
  const hash=location.hash,[path,q='']=hash.slice(1).split('?'),p=new URLSearchParams(q);
  if(!RESEARCH_COLLECTION_VIEWS.includes(path)||p.get('saved')!=='1')return researchPreviousRoute();
  const text=key=>(p.get(key)||'').slice(0,500),pick=(key,values,fallback)=>values.includes(p.get(key))?p.get(key):fallback;
  const index=(key,length)=>Math.min(Math.max(0,(parseInt(p.get(key),10)||0)),Math.max(0,length-1));
  if(path==='companies'){state.companyQ=text('q');state.companyRegion=pick('region',['US','China','Europe'],'all');}
  if(path==='reports'){state.report=index('report',A.reports.length);state.section=index('section',A.reports[state.report].sections.length);state.reportQ=text('q');}
  if(path==='data'){state.dataTab=pick('tab',['sources','corrections','workbooks','models','files'],'sources');state.book=index('book',A.workbooks.length);state.sheet=index('sheet',A.workbooks[state.book].sheets.length);state.dataQ=text('q');}
  if(path==='facilities'){Object.assign(state.filter,{q:text('q'),company:company(p.get('company'))?.id||'all',country:pick('country',D.sites.map(s=>s.country),'all'),review:pick('review',D.sites.map(s=>s.review),'all'),stage:pick('stage',['snapshot','target','unknown'],'all')});state.layout=pick('layout',['table','cards','chart'],'table');state.sort=pick('sort',['power','name','compute','target'],'power');}
  if(path==='costs'){state.costTab=pick('tab',['benchmarks','hardware','company'],'benchmarks');state.costLayer=pick('layer',D.costs.map(r=>r.layer),'all');state.costQ=text('q');}
  if(path==='compare')state.compare=[...new Set(text('companies').split(',').filter(id=>company(id)))].slice(0,4);
  navigate(path,{hash:true});history.replaceState(null,'',hash);
};window.addEventListener('hashchange',routeFromHash);

if(!window.ATLAS_BOOTSTRAPPING)routeFromHash();
