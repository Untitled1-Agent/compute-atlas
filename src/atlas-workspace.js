'use strict';
/* Shared map-led workspace. Collections stay separate; presentation and navigation do not. */
const workspaceState={phaseBySite:new Map(),tab:'overview',location:false};
function workspacePhases(s){
  const primary=primaryPowerRows(s).filter(o=>o.boundary==='critical_it'&&o.unit==='MW'&&!primaryIsContext(o));
  if(primary.length)return primary;
  return ['snapshot','target'].filter(key=>spatialPower(s,key)!=null).map(key=>({id:key,scope:key==='snapshot'?'Dated snapshot':'Projected end-state',value:spatialPower(s,key),unit:'MW',status:'modeled',as_of:s[key]?.date,qualifier:'Independent estimate; separate dates and scopes are not additive.',source_ids:s[key]?.sources||s.sources}));
}
function workspaceSelected(s){const rows=workspacePhases(s);return rows.find(r=>r.id===workspaceState.phaseBySite.get(s.id))||rows[0];}
function workspaceCollections(){return `<nav class="catalog-mode-switch workspace-collections" aria-label="Atlas collections"><button data-action="nav" data-id="overview" class="${['overview','globe'].includes(state.view)?'active':''}">Capacity</button><button data-action="nav" data-id="catalog" class="${state.view==='catalog'?'active':''}">Locations <span>${fmt(CATALOG.records.length)}</span></button><button data-action="nav" data-id="operators">Directories</button><button data-coverage-candidates>Research leads</button></nav>`;}
function workspaceToolbar(scale,filters=''){return `<div class="workspace-toolbar">${scale}<div class="workspace-tools">${filters}<button class="atlas-monitor-launch" data-atlas-action="monitor" aria-label="Source monitor and review queue" title="Source monitor and review queue">▤<span class="sr-only" id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button>${workspaceCollections()}</div></div>`;}
function workspaceRefine(){return `<details class="atlas-filter-panel" ${state.spatialFiltersOpen?'open':''}><summary class="atlas-filter-toggle">Refine view</summary>${atlasFilterbar()}</details>`;}
function workspacePhaseDiagram(s,level){
  if(!s)return spatialFacilitySchematic(s,'snapshot',level);
  const rows=workspacePhases(s),selected=workspaceSelected(s),max=Math.max(1,...rows.map(r=>r.value));
  return `<section class="atlas-evidence-schematic workspace-phase-scene ${level===5?'workspace-phase-focus':''}" aria-label="Interactive project phase evidence">
    <header class="workspace-scene-head"><div><h2>${level===4?'Campus capacity & commitments':'Phase detail'}</h2><p>${esc(s.location)} · source-reported scopes</p></div><div class="workspace-view-toggle"><button data-workspace-location="false" aria-pressed="${!workspaceState.location}">Evidence</button><button data-workspace-location="true" aria-pressed="${workspaceState.location}">Location</button></div></header>
    ${workspaceState.location?`<div class="workspace-location-map"><canvas id="globe-canvas" tabindex="0" aria-label="Approximate project location and generalized geographic context"></canvas><span>Approximate ${esc(s.coordinate_precision||'research anchor')} · no site footprint established</span></div>`:''}
    <div class="workspace-phase-plot" ${workspaceState.location?'hidden':''}>
      <div class="workspace-plot-label"><span>CRITICAL IT POWER</span><span>${level===4?'Select a scope to inspect →':'Independent source statements'}</span></div>
      ${rows.length?`<div class="workspace-phase-rows">${rows.map((r,i)=>`<button class="workspace-phase-row ${r.id===selected?.id?'selected':''}" data-workspace-phase="${esc(r.id)}" data-site="${esc(s.id)}" aria-pressed="${r.id===selected?.id}"><span class="workspace-phase-index">${String(i+1).padStart(2,'0')}</span><span class="workspace-phase-label"><b>${esc(r.scope)}</b><small>${esc(statusLabel(r.status))} · ${esc(r.as_of||'Date not disclosed')}</small></span><span class="workspace-phase-bar"><i class="${['delivered','operating'].includes(r.status)?'delivered':''}" style="width:${Math.max(2,r.value/max*100)}%"></i></span><strong>${fmt(r.value)} <small>${esc(r.unit)}</small></strong><span>↗</span></button>`).join('')}</div>`:`<div class="workspace-native"><strong>Not disclosed.</strong><p>No comparable IT-power quantity is established. Open the technical and commercial evidence to inspect the source's native units.</p><button class="btn" data-spatial-action="dossier" data-id="${esc(s.id)}">Open research dossier ↗</button></div>`}
      <footer class="workspace-phase-axis"><span>0</span><span>Separate scopes · not additive</span><span>${fmt(max)} MW</span></footer>
    </div>
    <footer class="workspace-scene-foot"><span>EVIDENCE SCHEMATIC · NOT A PARCEL / BUILDING SURVEY</span><button class="text-button" data-atlas-action="source-context">Map & evidence boundary ↗</button></footer>
    ${atlasMapControls(level)}
  </section>`;
}
function workspacePhaseRail(s,level){
  if(!s)return spatialFacilityRail(s,'snapshot',level);
  const row=workspaceSelected(s),relationships=primaryRelationships(s),profile=atlasResearchProfile(s);
  return `<div class="atlas-insight-stack">
    <section class="atlas-insight-card accent workspace-selected-phase">${atlasKicker(level===4?'01 / CAMPUS DOSSIER':'01 / SELECTED PHASE')}
      <div class="atlas-badge-row"><span>${esc(row?statusLabel(row.status):'Not quantified')}</span><span>${esc(row?.as_of||'Date not supplied')}</span></div>
      <h2>${esc(level===5?(row?.scope||s.name):s.name)}</h2><p>${esc(level===5?s.name:s.location)}</p>
      <div class="atlas-feature-number">${row?fmt(row.value)+' '+esc(row.unit):'Not quantified'}</div>
      <p class="atlas-number-boundary">${row?.source_id?'Disclosed critical IT load':'Independent IT estimate'}${level===4&&row?' · '+esc(row.scope):''}</p>
      <p class="workspace-phase-qualifier">${esc(row?.qualifier||'Native units and uncertainty remain attached to each source.')}</p>
      ${row?.source_id?primaryRef(row.source_id):srefs(row?.source_ids||s.sources)}
      <div class="workspace-dossier-actions"><button class="btn primary" data-spatial-action="dossier" data-id="${esc(s.id)}">Full dossier ↗</button><button class="text-button" data-atlas-action="export" data-id="${esc(s.id)}">Export ↓</button></div>
    </section>
    <section class="atlas-insight-card">${atlasKicker('02 / COUNTERPARTIES')}${relationships.slice(0,4).map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} ↗</button>${primaryRef(r.source_id)}</div>`).join('')||`<p>${esc(s.owner_label)} · archived association</p>`}</section>
    <section class="atlas-insight-card">${atlasKicker('03 / EVIDENCE QUALITY')}<h2>${profile.sources.length} documents.<br>One traceable project.</h2><p>${profile.rows.length} project-specific claims. Surveyed building geometry is not established for this dossier.</p><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">Sources & revision history ↗</button></section>
  </div>`;
}
function workspaceRail(level,scope,s,phase){
  if(level>=4)return workspacePhaseRail(s,level);
  if(level>=2)return spatialRail(level,scope,s,phase);
  const agg=spatialAggregate(scope.sites,phase),targets=spatialAggregate(scope.sites,'target'),companies=spatialCompanies(scope.sites);
  const countries=new Set(scope.sites.map(r=>r.country)).size;
  const ranked=spatialTopSites(scope.sites,phase==='snapshot'?'target':phase,3);
  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / THE GLOBAL TAKEAWAY')}<h2>${level===0?'Compute is a<br>physical asset class.':esc(scope.label)+'.<br>A connected system.'}</h2><p>${agg.count} projects across ${countries} countries. Follow their power, ownership and capital.</p><p class="atlas-card-footnote">${agg.known} IT estimates · ${agg.unknown} native / unknown. Partial coverage.</p></section>
    <section class="atlas-insight-card">${atlasKicker('02 / PROJECTED BUILDOUT')}<h2>Where capacity<br>is being planned.</h2>${atlasRankRows(ranked,'target')}<p class="atlas-card-footnote">${targets.known} dated target estimates. Targets are neither incremental additions nor live capacity.</p></section>
    <section class="atlas-insight-card">${atlasKicker('03 / CAPITAL & COUNTERPARTIES')}<h2>The companies<br>behind it.</h2><div class="atlas-company-cloud">${companies.map(({c})=>`<button data-action="company" data-id="${esc(c.id)}"><i style="background:${esc(c.color)}"></i>${esc(c.name)}</button>`).join('')}</div><button class="text-button" data-action="nav" data-id="investment">Open the investment lens ↗</button></section></div>`;
}
function workspaceProjectTabs(s){
  return `<nav class="workspace-project-tabs atlas-project-shortcuts" aria-label="Facility research sections">${[['overview','Overview'],['energy','Power & energy'],['technical','Technical design'],['development','Timeline'],['commercial','Counterparties'],['finance','Investment']].map(([topic,label])=>`<button ${topic==='overview'?'data-workspace-overview':`data-research-site="${esc(s.id)}" data-research-topic-target="${topic}"`} class="${topic==='overview'?'active':''}">${label}${topic==='overview'?'':' ↗'}</button>`).join('')}</nav>`;
}
function workspaceResearchView(){
  const st=spatialState(),s=spatialDefaultSite(),level=st.spatialLevel,phase=st.spatialPhase,scope=spatialScope(level,s),[title,description]=spatialHeadline(level,scope,s),campus=level>=4;
  return `<article class="atlas-experience atlas-workspace atlas-level-${level}">
    <header class="atlas-intro"><div><div class="atlas-eyebrow">${campus?'FACILITY & CAMPUS':'COMPUTE, FROM THE GROUND UP'}</div><h1>${campus?esc(s?.name||'No matching project'):title}</h1>${campus?`<p class="atlas-location">⌖ ${esc(s?.location||'')} · ${esc(s?.country||'')}</p>`:''}</div><div class="atlas-intro-aside"><p>${description}</p><button class="btn primary" data-atlas-action="journey">Take the five-stop tour ↗</button></div></header>
    ${workspaceToolbar(spatialStageStrip(level),workspaceRefine())}
    ${campus&&s?workspaceProjectTabs(s):''}
    <div class="atlas-spatial-layout"><div class="atlas-map-column"><section class="atlas-map-panel">${campus?workspacePhaseDiagram(s,level):spatialMap(scope,s,level,phase).replace('<div class="atlas-map-legend">','<div class="atlas-map-legend"><span class="workspace-context-key">· OSM locations · no capacity implied</span>')}</section>${campus&&s?`<div class="atlas-detail-pair">${atlasPowerLadder(s)}${atlasAttributes(s)}</div>`:''}</div><aside class="atlas-spatial-rail" aria-label="Analysis and evidence">${workspaceRail(level,scope,s,phase)}</aside></div>
    ${campus&&s?`<div class="workspace-evidence-bottom">${atlasSourcesPanel(s)}${atlasNotePanel(s)}</div><details class="workspace-research-detail"><summary>All project claims & dated disclosures <span>↓</span></summary>${atlasCampusBrief(s)}${atlasResearchPanel(s)}</details>`:spatialKpis(scope,phase)}
    <div class="atlas-map-footnote"><span>${esc(scope.note)}</span><button data-atlas-action="source-context">Natural Earth · sources & methodology ↗</button></div>
    ${campus?'':atlasRecordList(scope,phase)}
  </article>`;
}
// One workspace composition across the two independently sourced collections.
sixScaleGlobeView=workspaceResearchView;globeView=workspaceResearchView;
overviewView=()=>workspaceResearchView()+`<details class="atlas-research-depth"><summary>Company capital, original analysis & financial context <span>↓</span></summary>${evidenceMixPanel()}${investorDashboard()}${countryProfile()}</details>`;
const workspaceLandscapeIndex=NAV.findIndex(([id])=>id==='overview');NAV.unshift(...NAV.splice(workspaceLandscapeIndex,1));
const workspaceCatalogView=catalogView;
catalogView=function(){
  const container=document.createElement('div');container.innerHTML=workspaceCatalogView();const root=container.firstElementChild;if(!root)return container.innerHTML;
  root.classList.add('atlas-workspace');root.querySelector('.catalog-mode-switch')?.remove();
  const strip=root.querySelector('.catalog-scale-strip');if(strip){const bar=document.createElement('div');bar.className='workspace-toolbar';strip.before(bar);bar.append(strip);bar.insertAdjacentHTML('beforeend',workspaceCollections());}
  if(root.classList.contains('catalog-facility')){
    const inspector=root.querySelector('.catalog-inspector'),rail=root.querySelector('.atlas-spatial-rail .atlas-insight-stack');
    if(inspector&&rail){rail.querySelector('.atlas-insight-card.accent')?.remove();rail.prepend(inspector);}
  }
  return container.innerHTML;
};
// Project selection is explicit, source-backed and inspectable on the same screen.
document.addEventListener('click',event=>{
  const phase=event.target.closest('[data-workspace-phase]');
  if(phase){const s=site(phase.dataset.site);if(!s||!workspacePhases(s).some(r=>r.id===phase.dataset.workspacePhase))return;workspaceState.phaseBySite.set(s.id,phase.dataset.workspacePhase);state.spatialLevel=5;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-workspace-phase="${CSS.escape(phase.dataset.workspacePhase)}"]`)?.focus({preventScroll:true});}
  const location=event.target.closest('[data-workspace-location]');if(location){workspaceState.location=location.dataset.workspaceLocation==='true';render();document.querySelector(`[data-workspace-location="${workspaceState.location}"]`)?.focus({preventScroll:true});}
  if(event.target.closest('[data-workspace-overview]'))document.querySelector('.atlas-map-panel')?.scrollIntoView({block:'start',behavior:'smooth'});
});
// Phase inspection survives sharing and reload without changing the research ledger.
const workspaceSpatialURL=spatialURL;
spatialURL=function(view=state.view){const url=workspaceSpatialURL(view);if(!['overview','globe'].includes(view))return url;const s=site(state.spatialSelected),id=s&&workspaceState.phaseBySite.get(s.id);return id?url+'&claim='+encodeURIComponent(id):url;};
const workspaceRoute=routeFromHash;window.removeEventListener('hashchange',workspaceRoute);
routeFromHash=function(){const p=new URLSearchParams(location.hash.split('?')[1]||''),s=site(p.get('site'));if(s){if(workspacePhases(s).some(r=>r.id===p.get('claim')))workspaceState.phaseBySite.set(s.id,p.get('claim'));else workspaceState.phaseBySite.delete(s.id);}workspaceRoute();};window.addEventListener('hashchange',routeFromHash);
// Preserve existing explicit catalog links. A fresh visit opens the approved landscape.
if(!ATLAS_ENTRY_HASH){state.spatialLevel=0;state.view='overview';if(location.protocol!=='about:')history.replaceState(null,'',spatialURL('overview'));render();}else routeFromHash();
ATLAS.workspace={phases:workspacePhases,selected:workspaceSelected,state:workspaceState};
document.documentElement.classList.add('research-ready','atlas-ready','workspace-ready');
