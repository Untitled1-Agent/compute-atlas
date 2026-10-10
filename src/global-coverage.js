'use strict';
/* A coverage denominator is a count of research records, never market share.
   Quantities are deliberately displayed/exported row-by-row, without totals. */
const atlasCoverageState={tab:'coverage',country:'all',boundary:'all',status:'all',query:'',candidateQuery:'',offset:0};
const atlasCoverageOpen=()=>state.drawer?.kind==='coverage'&&!$('#drawer').hidden;
function atlasCoverageRows() {
  return D.sites.flatMap(s=>primaryObservations(s).map(row=>({...row,site:s,source:primarySource(row.source_id)})));
}
function atlasCoverageFiltered() {
  const st=atlasCoverageState,q=st.query.trim().toLocaleLowerCase();
  return atlasCoverageRows().filter(row=>(st.country==='all'||row.site.country===st.country)
    &&(st.boundary==='all'||row.boundary===st.boundary)&&(st.status==='all'||row.status===st.status)
    &&(!q||[row.site.name,row.site.location,row.site.owner_label,row.scope,row.boundary,row.source_id,row.qualifier]
      .join(' ').toLocaleLowerCase().includes(q)))
    .sort((a,b)=>String(b.as_of||'').localeCompare(String(a.as_of||''))||a.site.name.localeCompare(b.site.name)||a.id.localeCompare(b.id));
}
function atlasCoverageMetrics() {
  const sites=D.sites,reviewed=sites.filter(s=>primarySourceIds(s).length),mapped=sites.filter(s=>spatialFinite(s.lat)&&spatialFinite(s.lon));
  return {total:sites.length,reviewed:reviewed.length,mapped:mapped.length,unreviewed:sites.length-reviewed.length,
    countries:new Set(sites.filter(s=>s.country!=='Location not resolved').map(s=>s.country)).size,
    quantities:atlasCoverageRows().length,unknown:atlasCoverageRows().filter(r=>r.value===null).length,
    candidates:(ATLAS_PRIMARY.discoveries||[]).length};
}
function atlasCoverageCountries() {
  return [...new Set(D.sites.map(s=>s.country))].sort().map(country=>{
    const sites=D.sites.filter(s=>s.country===country),reviewed=sites.filter(s=>primarySourceIds(s).length);
    const rows=sites.flatMap(primaryObservations);
    return {country,total:sites.length,reviewed:reviewed.length,quantified:rows.filter(o=>o.value!==null).length,
      native:rows.filter(o=>o.metric!=='power').length,unmapped:sites.filter(s=>!spatialFinite(s.lat)||!spatialFinite(s.lon)).length};
  });
}
function atlasCoverageOverview() {
  const m=atlasCoverageMetrics();
  return `<div class="atlas-coverage-section-head"><div><h2>What is actually covered?</h2><p>A primary citation may establish a lease, a native-unit quantity, or a commissioning date. It does not automatically verify an archived IT-power estimate.</p></div></div>
    <div class="atlas-coverage-summary"><div><strong>${m.total}</strong><span>Named research records</span></div><div><strong>${m.reviewed}</strong><span>With primary review</span></div><div><strong>${m.unreviewed}</strong><span>Without this review layer</span></div></div>
    <p class="atlas-coverage-boundary">These are counts within this collection, not total facilities, market share, utilization, or a confidence score. ${m.mapped} records have approximate map anchors; ${m.total-m.mapped} remain unmapped.</p>
    <div class="atlas-coverage-country-head"><span>Geography</span><span>Primary / records</span></div>
    <div class="atlas-coverage-geographies">${atlasCoverageCountries().map(row=>`<article><div><h3>${esc(row.country)}</h3><strong>${row.reviewed} <span>/ ${row.total}</span></strong></div><div class="atlas-coverage-track" aria-hidden="true"><i style="width:${100*row.reviewed/row.total}%"></i></div><footer><span>${row.quantified} quantified disclosures · ${row.unmapped} unmapped</span><button class="text-button" data-coverage-country="${esc(row.country)}">Inspect disclosures →</button></footer></article>`).join('')}</div>
    <section class="atlas-coverage-guide"><h3>The missing data stays visible.</h3><p>Unquantified observations remain null. Historical revisions remain in each facility’s evidence desk. This screen does not turn gross power, utility supply, critical IT, leases or native compute metrics into one denominator.</p><button class="text-button" data-coverage-tab="candidates">Review ${m.candidates} unmapped research candidates ↗</button></section>`;
}
function atlasCoverageControls() {
  const st=atlasCoverageState,rows=atlasCoverageRows();
  const options=(values,selected,labeler=x=>x)=>`<option value="all">All</option>${[...new Set(values)].sort().map(value=>`<option value="${esc(value)}" ${value===selected?'selected':''}>${esc(labeler(value))}</option>`).join('')}`;
  return `<div class="atlas-coverage-filters"><label class="atlas-coverage-search">Search disclosures<input id="atlas-coverage-query" type="search" value="${esc(st.query)}" placeholder="Site, source, scope or counterparty…" autocomplete="off"></label><label>Geography<select data-coverage-filter="country">${options(D.sites.map(s=>s.country),st.country)}</select></label><label>Measurement boundary<select data-coverage-filter="boundary">${options(rows.map(r=>r.boundary),st.boundary,boundaryLabel)}</select></label><label>Disclosure status<select data-coverage-filter="status">${options(rows.map(r=>r.status),st.status,statusLabel)}</select></label></div><div class="atlas-coverage-actions"><button class="text-button" data-coverage-action="reset">Reset filters</button><button class="btn small" data-coverage-action="export">Export cited rows ↓</button></div>`;
}
function atlasCoverageDisclosure(row) {
  const date=row.as_of||'Reporting date not stated';
  return `<article class="atlas-coverage-disclosure" data-coverage-record="${esc(row.id)}"><header><span class="atlas-card-kicker">${esc(row.site.country)} / ${esc(statusLabel(row.status))}</span>${row.applies_to==='context'?'<span class="atlas-coverage-context-label">Wider context / match unresolved</span>':''}<span>${esc(date)}</span></header><h3><button data-coverage-site="${esc(row.site_id)}">${esc(row.site.name)} <span>↗</span></button></h3><div class="atlas-coverage-value"><strong>${row.value===null?'Not disclosed':observationValue(row)}</strong>${row.value===null?'':`<span>${esc(row.unit)}</span>`}</div><p class="atlas-coverage-measurement">${esc(boundaryLabel(row.boundary))}</p><p class="atlas-coverage-scope">${esc(row.scope)}</p>${row.qualifier?`<p>${esc(row.qualifier)}</p>`:''}<footer>${primaryRef(row.source_id)}<span>${esc(row.source?.publisher||'Source not found')} · ${row.source?.published_at?'published '+esc(row.source.published_at):'retrieved '+esc(row.source?.retrieved_at||'date unknown')}</span></footer></article>`;
}
function atlasCoverageResults() {
  if(!atlasCoverageOpen()||atlasCoverageState.tab!=='disclosures')return;
  const rows=atlasCoverageFiltered(),st=atlasCoverageState;
  st.offset=Math.min(st.offset,Math.max(0,Math.ceil(rows.length/10)-1)*10);
  $('#atlas-coverage-count').textContent=rows.length+' matching disclosure rows · no cross-boundary total';
  $('#atlas-coverage-records').innerHTML=rows.slice(st.offset,st.offset+10).map(atlasCoverageDisclosure).join('')||'<div class="atlas-coverage-empty"><h3>No matching reviewed disclosures.</h3><p>No result is not zero capacity. The source may be absent, undisclosed, or outside this collection.</p></div>';
  $('#atlas-coverage-pagination').innerHTML=`<button class="btn small" data-coverage-page="previous" ${st.offset===0?'disabled':''}>← Previous</button><span>${rows.length?st.offset+1:0}–${Math.min(st.offset+10,rows.length)} of ${rows.length}</span><button class="btn small" data-coverage-page="next" ${st.offset+10>=rows.length?'disabled':''}>Next →</button>`;
}
function atlasCandidateRows(query=atlasCoverageState.candidateQuery) {
  const q=query.trim().toLocaleLowerCase();
  return (ATLAS_PRIMARY.discoveries||[]).filter(row=>!q||[row.name,row.location,row.operator,row.note,row.source_id,primarySource(row.source_id)?.publisher,...(row.candidate_measurements||[]).map(m=>m.label+' '+m.scope)].join(' ').toLocaleLowerCase().includes(q));
}
function atlasCandidateCard(row) {
  const citations=[...new Set([row.source_id,...(row.supporting_source_ids||[])])];
  return `<article class="atlas-coverage-candidate" data-research-candidate="${esc(row.id)}"><span class="atlas-card-kicker">RESEARCH CANDIDATE / NOT IN MAPPED TOTALS</span><h3>${esc(row.name)}</h3><p class="atlas-coverage-candidate-place">${esc(row.location)}</p>${row.candidate_measurements?`<div class="atlas-candidate-measurements">${row.candidate_measurements.map(m=>`<div><span>${esc(m.label)}<small>${esc(m.scope)} · ${esc(m.status)}</small></span><strong>${m.value===null?'Undisclosed':(m.comparison==='lte'?'≤ ':'')+fmt(m.value)+' '+esc(m.unit)}</strong>${primaryRef(m.source_id)}</div>`).join('')}</div><p class="atlas-card-footnote">Native source scopes; no total is computed. Planned quantities are not operating load.</p>`:''}<p>${esc(row.note)}</p>${row.next_review?`<div class="atlas-coverage-next"><b>Before adding this site</b><p>${esc(row.next_review)}</p></div>`:''}<footer>${citations.map(primaryRef).join('')}<span>Source retrieved ${esc(primarySource(row.source_id)?.retrieved_at||'date not recorded')}</span></footer></article>`;
}
function atlasCandidateResults() {
  const rows=atlasCandidateRows();
  $('#atlas-candidate-count').textContent=`${rows.length} source-linked leads · excluded from map and power totals`;
  $('#atlas-candidate-results').innerHTML=rows.map(atlasCandidateCard).join('')||'<p class="atlas-coverage-empty">No matching research lead. This is not zero facilities or capacity.</p>';
}
function atlasCandidateExport() {
  const rows=atlasCandidateRows(),ids=new Set(rows.flatMap(r=>[r.source_id,...(r.supporting_source_ids||[])]));
  return {schema_version:1,published_at:ATLAS_PRIMARY.published_at,query:atlasCoverageState.candidateQuery,
    policy:'Unmapped research candidates and native disclosed scopes. No approved site identities, operating IT total or surveyed geometry is asserted.',
    candidates:rows,sources:ATLAS_PRIMARY.sources.filter(s=>ids.has(s.id))};
}
function atlasCoverageCandidates() {
  return `<h2>Research candidates, not mapped capacity.</h2><p class="atlas-coverage-boundary">These source-linked leads are excluded from mapped project counts and all power subtotals. A publisher’s location page is not a surveyed site plan. Geographic identity and claim boundaries still require explicit review before adding a dossier.</p><div class="atlas-candidate-controls"><label for="atlas-candidate-query">Find a research lead<input id="atlas-candidate-query" type="search" maxlength="500" placeholder="Salo, atNorth, Finland, Google…" value="${esc(atlasCoverageState.candidateQuery)}"></label><button class="btn small" data-candidate-export>Export cited leads ↓</button></div><p id="atlas-candidate-count" role="status">${atlasCandidateRows().length} source-linked leads · excluded from map and power totals</p><div id="atlas-candidate-results">${atlasCandidateRows().map(atlasCandidateCard).join('')}</div>`;
}
function atlasCoverageRender() {
  if(!atlasCoverageOpen())return;
  const st=atlasCoverageState,root=$('#drawer-content'),scroll=$('#drawer').scrollTop;
  const active=document.activeElement;
  const focused=active?.dataset?.coverageTab,filter=active?.dataset?.coverageFilter;
  const editing=['atlas-coverage-query','atlas-candidate-query'].includes(active?.id),editingId=active?.id;
  const selection=editing?[active.selectionStart,active.selectionEnd]:null;
  $('#drawer-type').textContent='GLOBAL EVIDENCE / COVERAGE & BOUNDARIES';
  root.innerHTML=`<section class="atlas-coverage-desk"><div class="atlas-eyebrow">THE COLLECTION IS NOT THE MARKET</div><h1>A global view.<br><span>An honest denominator.</span></h1><p class="atlas-coverage-intro">Explore what the primary sources disclose—and what this research collection does not establish.</p><p class="atlas-coverage-publication">Reviewed publication: ${esc(ATLAS_PRIMARY.published_at)} · acquisition recency is tracked separately.</p><div class="atlas-coverage-tabs" role="group" aria-label="Global evidence sections">${[['coverage','Coverage'],['disclosures','Disclosures'],['candidates','Research candidates']].map(([id,label])=>`<button data-coverage-tab="${id}" aria-pressed="${st.tab===id}">${label}</button>`).join('')}</div>${st.tab==='coverage'?atlasCoverageOverview():st.tab==='candidates'?atlasCoverageCandidates():`<h2>Disclosures, in their own units.</h2><p class="atlas-coverage-boundary">One row, one scope, one source. Even rows with the same unit may overlap or describe different dates; they are not additive.</p>${atlasCoverageControls()}<p id="atlas-coverage-count" role="status"></p><div id="atlas-coverage-records"></div><nav class="atlas-coverage-pagination" id="atlas-coverage-pagination" aria-label="Disclosure pages"></nav>`}</section>`;
  atlasCoverageResults();
  if(focused)root.querySelector(`[data-coverage-tab="${CSS.escape(focused)}"]`)?.focus({preventScroll:true});
  if(filter)root.querySelector(`[data-coverage-filter="${CSS.escape(filter)}"]`)?.focus({preventScroll:true});
  if(editing){const input=$('#'+editingId);input?.focus({preventScroll:true});if(selection)input?.setSelectionRange(...selection);}
  $('#drawer').scrollTop=scroll;
}
function atlasCoverageExport() {
  const rows=atlasCoverageFiltered();
  // Export is JSON rather than a lossy, formula-interpretable spreadsheet. Null
  // stays null; comparators, status and reporting/retrieval dates all survive.
  return {schema_version:1,published_at:ATLAS_PRIMARY.published_at,exported_at:new Date().toISOString(),
    policy:'Filtered current reviewed disclosure rows. No total is computed; scopes and dates can overlap. Not a global inventory.',
    filters:{country:atlasCoverageState.country,boundary:atlasCoverageState.boundary,status:atlasCoverageState.status,query:atlasCoverageState.query},
    rows:rows.map(({site,source,...row})=>({...row,site_name:site.name,location:site.location,country:site.country,
      source:{id:source.id,publisher:source.publisher,title:source.title,url:source.url,published_at:source.published_at,retrieved_at:source.retrieved_at}}))};
}
const atlasCoveragePreviousDrawer=openDrawer;
openDrawer=function(kind,id,options={}) {
  atlasCoveragePreviousDrawer(kind,id,options);
  if(kind==='coverage')atlasCoverageRender();
};
ATLAS.openDrawer=openDrawer;
const atlasCoveragePreviousRail=spatialRail;
spatialRail=function(level,...rest) {
  const html=atlasCoveragePreviousRail(level,...rest);
  return level>=4?html:html+'<button class="atlas-coverage-launch" data-coverage-open><span>Source coverage & disclosure explorer</span><span>↗</span></button>';
};
const atlasCoveragePreviousKpis=spatialKpis;
spatialKpis=function(scope,phase) {
  const html=atlasCoveragePreviousKpis(scope,phase);
  // Convert only the review KPI, leaving scoped model math and other cards intact.
  const template=document.createElement('template');template.innerHTML=html;
  const target=[...template.content.querySelectorAll('.metric-card')].find(card=>card.querySelector('.metric-label')?.textContent==='Projects with primary-source review');
  if(target){
    const button=document.createElement('button');button.className='metric-card interactive';button.setAttribute('data-coverage-open','');
    button.innerHTML=target.innerHTML;
    button.querySelector('.metric-note').textContent='Reviewed disclosure layer · inspect coverage ↗';
    target.replaceWith(button);
  }
  return template.innerHTML;
};
const atlasCoveragePreviousMonitorLabel=updateMonitorLabel;
updateMonitorLabel=function(){atlasCoveragePreviousMonitorLabel();atlasCoverageRender();};
document.addEventListener('click',event=>{
  const candidate=event.target.closest('[data-coverage-candidate]');
  if(event.target.closest('[data-coverage-candidates]')||candidate){
    atlasCoverageState.tab='candidates';atlasCoverageState.candidateQuery=candidate?((ATLAS_PRIMARY.discoveries||[]).find(r=>r.id===candidate.dataset.coverageCandidate)?.name||''):'';
    if(!$('#search-modal').hidden)closeSearch();openDrawer('coverage','global');
  }
  if(event.target.closest('[data-candidate-export]'))download('compute-atlas-research-leads.json',atlasCandidateExport());
  if(event.target.closest('[data-coverage-open]'))openDrawer('coverage','global');
  const tab=event.target.closest('[data-coverage-tab]');
  if(tab){atlasCoverageState.tab=tab.dataset.coverageTab;atlasCoverageRender();}
  const country=event.target.closest('[data-coverage-country]');
  if(country){Object.assign(atlasCoverageState,{tab:'disclosures',country:country.dataset.coverageCountry,boundary:'all',status:'all',query:'',offset:0});atlasCoverageRender();$('#atlas-coverage-query')?.focus({preventScroll:true});}
  const selected=event.target.closest('[data-coverage-site]');
  if(selected){state.filter={q:'',company:'all',country:'all',review:'all',stage:'all'};state.spatialEvidence='all';spatialTransition({selected:selected.dataset.coverageSite,level:5});window.scrollTo({top:0,behavior:'instant'});}
  const action=event.target.closest('[data-coverage-action]')?.dataset.coverageAction;
  if(action==='reset'){Object.assign(atlasCoverageState,{country:'all',boundary:'all',status:'all',query:'',offset:0});atlasCoverageRender();}
  if(action==='export'){
    const url=URL.createObjectURL(new Blob([JSON.stringify(atlasCoverageExport(),null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='compute-atlas-reviewed-disclosures.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const pager=event.target.closest('[data-coverage-page]');
  if(pager){atlasCoverageState.offset+=pager.dataset.coveragePage==='next'?10:-10;atlasCoverageResults();const available=$(`[data-coverage-page="${pager.dataset.coveragePage}"]:not(:disabled)`)||$('[data-coverage-page]:not(:disabled)');available?.focus({preventScroll:true});}
});
document.addEventListener('change',event=>{
  const filter=event.target.closest('[data-coverage-filter]');
  if(filter){atlasCoverageState[filter.dataset.coverageFilter]=filter.value;atlasCoverageState.offset=0;atlasCoverageResults();}
});
document.addEventListener('input',event=>{
  if(event.target.id==='atlas-candidate-query'){atlasCoverageState.candidateQuery=event.target.value;atlasCandidateResults();}
  if(event.target.id==='atlas-coverage-query'){atlasCoverageState.query=event.target.value;atlasCoverageState.offset=0;atlasCoverageResults();}
});
ATLAS.coverage={open:()=>openDrawer('coverage','global'),metrics:atlasCoverageMetrics,rows:atlasCoverageFiltered,export:atlasCoverageExport};
ATLAS.coverage.candidates=atlasCandidateRows;ATLAS.coverage.exportCandidates=atlasCandidateExport;
const candidatePreviousSearch=searchAll;
searchAll=function(q){candidatePreviousSearch(q);if(!q.trim())return;const rows=atlasCandidateRows(q);if(rows.length)$('#search-results').insertAdjacentHTML('afterbegin',`<div class="command-hint">${rows.length} unmapped research leads · excluded from capacity totals</div>`+rows.slice(0,6).map(r=>`<button class="search-result" data-coverage-candidate="${esc(r.id)}"><span class="result-type">RESEARCH LEAD</span><span><b>${esc(r.name)}</b><small>${esc(r.location)} · identity review pending</small></span></button>`).join(''));};
if(['overview','globe'].includes(state.view))render();
