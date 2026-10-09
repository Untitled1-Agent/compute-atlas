/* Primary-source directory: visible even when no geographic match exists. */
const OPERATOR_DIRECTORY = DirectorySchema.validate(JSON.parse($('#operator-directory-data').textContent));
const operatorState = {region:'All',country:'All',q:'',match:'All',page:0,selected:null};
let operatorMatchCache = null, operatorMatchCatalog = null;
function operatorMatches(id){
  if(operatorMatchCatalog!==CATALOG){
    operatorMatchCatalog=CATALOG;
    const features=CATALOG.records.filter(r=>/\bequinix\b/i.test((r.operator||'')+' '+r.name));
    operatorMatchCache=new Map(OPERATOR_DIRECTORY.records.map(r=>[r.id,DirectorySchema.matches(r,features)]));
  }
  return operatorMatchCache.get(id)||[];
}
function operatorRows(){
  const q=operatorState.q.trim().toLocaleLowerCase();
  return OPERATOR_DIRECTORY.records.filter(r=>(operatorState.region==='All'||r.source_region===operatorState.region) &&
    (operatorState.country==='All'||r.source_country===operatorState.country) &&
    (!q||[r.name,r.metro,r.source_country].join(' ').toLocaleLowerCase().includes(q)) &&
    (operatorState.match==='All'||(operatorState.match==='linked'?operatorMatches(r.id).length>0:operatorMatches(r.id).length===0)));
}
function operatorURL(){
  const p=new URLSearchParams();for(const k of ['region','country','q','match','selected'])if(operatorState[k]&&operatorState[k]!=='All')p.set(k,operatorState[k]);
  if(operatorState.page)p.set('page',String(operatorState.page));
  return '#operators'+(p.size?'?'+p:'');
}
function operatorGo(patch={},replace=false){
  clearTimeout(operatorTimer);if(state.tour>=0)endTour();Object.assign(operatorState,{page:0},patch);state.view='operators';closeDrawer();
  history[replace?'replaceState':'pushState'](null,'',operatorURL());render();
}
function operatorRoute(q){
  const p=new URLSearchParams(q);
  Object.assign(operatorState,{region:['EMEA','Americas','APAC'].includes(p.get('region'))?p.get('region'):'All',country:Object.hasOwn(OPERATOR_DIRECTORY.counts.countries,p.get('country'))?p.get('country'):'All',q:(p.get('q')||'').slice(0,500),match:['linked','unlinked'].includes(p.get('match'))?p.get('match'):'All',page:Math.max(0,Math.min(100,parseInt(p.get('page'))||0)),selected:OPERATOR_DIRECTORY.records.some(r=>r.id===p.get('selected'))?p.get('selected'):null});
  navigate('operators',{hash:true});
}
function operatorExport(){
  download('compute-atlas-operator-directory.json',{...OPERATOR_DIRECTORY,records:operatorRows(),
    counts:undefined,publication_counts:OPERATOR_DIRECTORY.counts,filters:{...operatorState},
    match_boundary:'Code, operator and country matches are proposals only. Directory entries have no asserted coordinates or IT power.',
    proposed_map_matches:operatorRows().map(r=>({directory_id:r.id,osm_feature_ids:operatorMatches(r.id)}))});
}
function operatorTable(){
  const rows=operatorRows(),size=12,pages=Math.max(1,Math.ceil(rows.length/size));operatorState.page=Math.min(operatorState.page,pages-1);
  return `<div class="operator-list-head"><span role="status">${fmt(rows.length)} publisher-listed codes${rows.length?' · '+(operatorState.page*size+1)+'–'+Math.min(rows.length,(operatorState.page+1)*size):''}</span><span>Map links are provisional</span></div>
  <div class="operator-list">${rows.slice(operatorState.page*size,(operatorState.page+1)*size).map(r=>{const matches=operatorMatches(r.id);return `<button class="operator-record ${operatorState.selected===r.id?'selected':''}" data-operator-select="${esc(r.id)}" aria-pressed="${operatorState.selected===r.id}"><span class="operator-code">${esc(r.code)}</span><span><strong>${esc(r.metro)}</strong><small>${esc(r.source_country)} · ${esc(r.facility_type)}</small></span><span class="operator-link-state ${matches.length?'linked':''}">${matches.length?matches.length+' proposed map '+(matches.length===1?'link':'links'):'Location review needed'}<small>View source details ↗</small></span></button>`;}).join('')||'<div class="empty"><h3>No directory entries in this selection.</h3><p>This is a coverage gap in this source, not evidence of zero data centers or zero capacity.</p></div>'}</div>
  <div class="operator-pagination"><button class="btn small" data-operator-page="-1" ${operatorState.page===0?'disabled':''}>← Previous</button><span>Page ${operatorState.page+1} of ${pages}</span><button class="btn small" data-operator-page="1" ${operatorState.page===pages-1?'disabled':''}>Next →</button></div>`;
}
function operatorRail(){
  const d=OPERATOR_DIRECTORY,r=d.records.find(r=>r.id===operatorState.selected),matches=r?operatorMatches(r.id):[];
  return `<div class="atlas-insight-stack">${r?`<section class="atlas-insight-card accent">${atlasKicker('01 / OPERATOR-LISTED FACILITY',false)}<h2 id="operator-detail-title" tabindex="-1">${esc(r.name)}</h2><p>${esc(r.metro)} · ${esc(r.source_country)}</p>${atlasRow('Directory type',esc(r.facility_type))}${atlasRow('Service coverage',esc(r.service_coverage||'Not stated'))}${atlasRow('Coordinates','Not established')}${atlasRow('Critical IT load','Not disclosed here')}<p class="atlas-card-footnote">Service staffing is not available capacity, occupancy or commissioned IT load.</p>${catalogLink(r.source_url,'Read the original directory ↗','btn primary')}</section><section class="atlas-insight-card">${atlasKicker('02 / GEOGRAPHIC CROSS-CHECK',false)}<h2>${matches.length?'Compare the map.<br>Do not assume a match.':'Listed, without<br>a resolved map link.'}</h2><p>${matches.length?'Exact operator, facility code and country produced these candidates. Building and campus records may overlap. The directory does not certify their geometry.':'This operator record remains searchable even without a matching community feature. No city centroid or building has been invented.'}</p>${matches.map(id=>{const f=catalogFeature(id);return `<button class="operator-map-link" data-catalog-open="${esc(id)}"><strong>${esc(f.name)}</strong><span>${esc(f.kind)} · ${esc(f.country)}</span><small>${f.geometry&&f.kind==='building'?'Inspect source-outline 3D':'Inspect community map record'} ↗</small></button>`;}).join('')}</section>`:
  `<section class="atlas-insight-card accent">${atlasKicker('01 / COVERAGE, NOT A CENSUS',false)}<h2>A second source.<br>A wider view.</h2><p>Operator-published locations remain visible even where the community map has no matching feature. Explore Europe, Asia-Pacific and the Americas without treating missing map coverage as missing infrastructure.</p><p class="atlas-card-footnote">One publisher’s table. Not a complete operator fleet or global facility census.</p></section><section class="atlas-insight-card">${atlasKicker('02 / KEEP THE BOUNDARIES',false)}<h2>A code is not<br>a building survey.</h2><p>The same campus can have points, buildings and land areas in the map. Proposed links are shown separately; neither these counts nor the 79-project capacity archive are added together.</p><button class="btn" data-action="nav" data-id="catalog">Return to the worldwide map ↗</button></section>`}
  <section class="atlas-insight-card operator-source">${atlasKicker('03 / PRIMARY SOURCE',false)}<h3>${esc(d.publisher)}</h3><p>${esc(d.title)}</p>${atlasRow('Captured',esc(d.captured_at.slice(0,10)))}${atlasRow('Editorial review',esc(d.review.reviewed_at.slice(0,10)))}${atlasRow('Published date','Not stated')}${catalogLink(d.url,'Inspect the source table ↗','catalog-primary-link')}<details><summary>Source identity & review</summary><p class="operator-hash">SHA-256 ${esc(d.source_sha256)}</p><p>${esc(d.review.note)}</p><p>${esc(d.rights)}</p></details><p class="atlas-card-footnote">Background checks queue changes for review. They do not silently replace this publication. Reload to load a newer accepted directory.</p></section></div>`;
}
function operatorDirectoryView(){
  const d=OPERATOR_DIRECTORY,linked=d.records.filter(r=>operatorMatches(r.id).length>0).length;
  const groups=['All','EMEA','APAC','Americas'],regionLabel={All:'All locations',EMEA:'Europe, Middle East & Africa',APAC:'Asia-Pacific',Americas:'Americas'};
  return `<div class="atlas-experience operator-experience">${catalogModeTabs()}<header class="atlas-intro"><div><div class="atlas-eyebrow">PRIMARY-SOURCE LOCATION DIRECTORY</div><h1>Beyond the map.<br>Direct from the operator.</h1></div><div class="atlas-intro-aside"><p>Explore ${fmt(d.records.length)} Equinix facility codes from its published directory. Keep source-listed locations and community geometry distinct.</p><button class="btn primary" data-operator-export>Export cited selection ↓</button></div></header>
  ${window.ATLAS_DIRECTORY_WARNING?'<div class="operator-warning" role="status">Operator publication unavailable or invalid. Showing the dated checked-in snapshot, not live database data.</div>':''}
  <div class="operator-kpis">${[['Publisher-listed codes',fmt(d.records.length),'One captured directory, not a census'],['Published country groups',Object.keys(d.counts.countries).length,'Publisher’s geographic grouping'],['Codes with proposed map links',linked,'Unreviewed cross-source candidates'],['Still needing a map link',d.records.length-linked,'Retained without fabricated coordinates']].map(([label,note,sub])=>`<div class="metric-card"><span class="metric-label">${label}</span><strong class="metric-value">${note}</strong><span class="metric-note">${sub}</span></div>`).join('')}</div>
  <div class="atlas-spatial-layout"><div class="operator-main"><div class="operator-regions" aria-label="Publisher regions">${groups.map(g=>`<button data-operator-region="${g}" class="${operatorState.region===g?'active':''}" aria-pressed="${operatorState.region===g}"><span>${regionLabel[g]}</span><strong>${g==='All'?d.records.length:d.counts.regions[g]||0}</strong></button>`).join('')}</div>
  <div class="catalog-filterbar operator-filters"><label><span>FIND A FACILITY</span><input id="operator-query" value="${esc(operatorState.q)}" placeholder="Frankfurt, FR2, Singapore…" maxlength="500"></label><label><span>SOURCE COUNTRY GROUP</span><select id="operator-country"><option value="All">All countries</option>${Object.keys(d.counts.countries).sort().map(c=>`<option ${operatorState.country===c?'selected':''} value="${esc(c)}">${esc(c)}</option>`).join('')}</select></label><label><span>MAP COVERAGE</span><select id="operator-match"><option value="All">All records</option><option value="linked" ${operatorState.match==='linked'?'selected':''}>Proposed map links</option><option value="unlinked" ${operatorState.match==='unlinked'?'selected':''}>No map link yet</option></select></label><button class="text-button" data-operator-reset>Reset</button></div>
  <section class="operator-results" id="operator-results" aria-label="Operator facility directory">${operatorTable()}</section><div class="catalog-provenance"><span>${esc(d.count_boundary)}</span><span>Country headings and localities follow the publisher; they do not resolve jurisdictional or mapping differences.</span></div></div>
  <aside class="atlas-spatial-rail" id="operator-rail" aria-label="Operator evidence and map cross-check">${operatorRail()}</aside></div></div>`;
}
function operatorUpdate(){
  if(state.view!=='operators')return;
  operatorState.page=0;operatorState.selected=null;history.replaceState(null,'',operatorURL());
  $('#operator-results').innerHTML=operatorTable();$('#operator-rail').innerHTML=operatorRail();
}
let operatorTimer;
document.addEventListener('input',e=>{if(e.target.id==='operator-query'){operatorState.q=e.target.value;clearTimeout(operatorTimer);operatorTimer=setTimeout(operatorUpdate,100);}});
document.addEventListener('change',e=>{if(e.target.id==='operator-country'){operatorState.country=e.target.value;operatorState.region='All';operatorGo({...operatorState,page:0,selected:null});$('#operator-country')?.focus({preventScroll:true});}if(e.target.id==='operator-match'){operatorState.match=e.target.value;operatorUpdate();}});
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||b.disabled)return;
  if(b.hasAttribute('data-operator-region'))operatorGo({region:b.dataset.operatorRegion,country:'All',selected:null});
  if(b.hasAttribute('data-operator-select')){if(!$('#search-modal').hidden){closeSearch();operatorGo({region:'All',country:'All',q:'',match:'All',selected:b.dataset.operatorSelect});}else operatorGo({selected:b.dataset.operatorSelect,page:operatorState.page});$('#operator-detail-title')?.focus({preventScroll:innerWidth>900});}
  if(b.hasAttribute('data-operator-page')){operatorState.page+=Number(b.dataset.operatorPage);$('#operator-results').innerHTML=operatorTable();history.replaceState(null,'',operatorURL());(document.querySelector(`[data-operator-page="${b.dataset.operatorPage}"]:not(:disabled)`)||document.querySelector('[data-operator-page]:not(:disabled)'))?.focus({preventScroll:true});}
  if(b.hasAttribute('data-operator-reset'))operatorGo({region:'All',country:'All',q:'',match:'All',selected:null});
  if(b.hasAttribute('data-operator-export'))operatorExport();
});
ATLAS.operators={data:OPERATOR_DIRECTORY,state:operatorState,rows:operatorRows,matches:operatorMatches,go:operatorGo,export:operatorExport};

// Join the existing modular route/render extension chain without rewriting the archive app.
NAV.splice(NAV.findIndex(x=>x[0]==='facilities')+1,0,['operators','Operator directory']);
const operatorBaseTabs=catalogModeTabs;
catalogModeTabs=function(){return operatorBaseTabs().replace(/<\/div>$/,`<button data-action="nav" data-id="operators" class="${state.view==='operators'?'active':''}">▤ Operator directory <span>${OPERATOR_DIRECTORY.records.length}</span></button></div>`);};
const operatorBaseRender=render;
render=function(){
  if(state.view!=='operators')return operatorBaseRender();
  if(globe){globe.destroy();globe=null;}
  renderNav();$('#content').innerHTML=operatorDirectoryView();
  if(state.tour>=0)renderTour();
};
const operatorBaseRoute=routeFromHash;window.removeEventListener('hashchange',operatorBaseRoute);
routeFromHash=function(){const [path,q='']=location.hash.slice(1).split('?');if(path==='operators'){operatorRoute(q);return;}operatorBaseRoute();};
window.addEventListener('hashchange',routeFromHash);
const operatorBaseSearch=searchAll;
searchAll=function(q){operatorBaseSearch(q);if(!q.trim())return;const query=q.toLocaleLowerCase(),hits=OPERATOR_DIRECTORY.records.filter(r=>[r.name,r.metro,r.source_country].join(' ').toLocaleLowerCase().includes(query));if(hits.length)$('#search-results').insertAdjacentHTML('afterbegin',`<div class="command-hint">${hits.length} primary-directory codes · first ${Math.min(8,hits.length)} · separate from map features</div>`+hits.slice(0,8).map(r=>`<button class="search-result" data-operator-select="${esc(r.id)}"><span class="result-type">OPERATOR LISTING</span><span><b>${esc(r.name)}</b><small>${esc(r.metro)} · ${esc(r.source_country)}</small></span></button>`).join(''));};
if(location.hash.startsWith('#operators'))routeFromHash();else render();
document.documentElement.classList.add('operator-ready');
