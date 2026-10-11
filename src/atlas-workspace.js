'use strict';
/* Shared map-led workspace. Collections stay separate; presentation and navigation do not. */
const workspaceState={phaseBySite:new Map(),tab:'overview',location:false};
const WORKSPACE_TOPICS=[['overview','Overview'],['energy','Power & phases'],['technical','Technical design'],['development','Timeline'],['commercial','Counterparties'],['finance','Investment'],['evidence','Sources & evidence']];
saved.projectCompare=Array.isArray(saved.projectCompare)?saved.projectCompare.filter(id=>site(id)).slice(0,3):[];
function workspaceFilterChips(){
  const entries=[['q',state.filter.q],['company',state.filter.company!=='all'&&company(state.filter.company)?.name],['country',state.filter.country!=='all'&&state.filter.country],['evidence',state.spatialEvidence!=='all'&&state.spatialEvidence]];
  return `<div class="workspace-filter-chips">${entries.filter(([,value])=>value).map(([key,value])=>`<button data-workspace-clear="${key}" aria-label="Remove ${esc(value)} filter">${esc(value)} <span>×</span></button>`).join('')}</div>`;
}
function workspaceSelectionRail(s,scope){
  const members=(state.spatialCluster||[]).map(site).filter(Boolean),cluster=members.length>1;
  return `<section class="atlas-insight-card workspace-selection">${atlasKicker(cluster?'01 / SELECTED CLUSTER':'01 / SELECTED PROJECT')}<h2>${esc(cluster?researchClusterName(members):s.name)}</h2><p>${cluster?members.length+' research records · visual grouping, not a common campus':esc(s.location)}</p>${cluster?`<div class="workspace-cluster-members">${members.map(x=>`<button data-workspace-select="${esc(x.id)}">${esc(x.name)}<small>${esc(x.location)}</small></button>`).join('')}</div>`:`${atlasRow('Snapshot IT estimate',spatialPower(s,'snapshot')==null?'Not quantified':fmt(spatialPower(s,'snapshot'))+' MW')}${atlasRow('Target IT estimate',spatialPower(s,'target')==null?'Not quantified':fmt(spatialPower(s,'target'))+' MW')}`}<p class="atlas-card-footnote">Independent, mixed-vintage estimates; the target is not added to the snapshot.</p><div class="workspace-dossier-actions"><button class="btn primary" data-workspace-enter>Explore ${state.spatialLevel<3?'next scale':'this campus'} →</button><button class="text-button" data-workspace-compare="${esc(s.id)}">${saved.projectCompare.includes(s.id)?'✓ Comparing':'Compare +'}</button></div></section>`;
}
function workspaceTopicContent(s){
  if(workspaceState.tab==='overview')return `<div class="atlas-detail-pair">${atlasPowerLadder(s)}${atlasAttributes(s)}</div><div class="workspace-evidence-bottom">${atlasSourcesPanel(s)}${atlasNotePanel(s)}</div>`;
  if(workspaceState.tab==='evidence')return `<div class="workspace-evidence-bottom">${atlasSourcesPanel(s)}${atlasNotePanel(s)}</div>${atlasResearchPanel(s)}`;
  const p=atlasResearchProfile(s),topic=p.topics.find(t=>t.id===workspaceState.tab),rows=topic?.rows||[];
  const timeline=workspaceState.tab==='development';
  return `<section class="workspace-topic-content" data-workspace-topic-content="${workspaceState.tab}"><header>${atlasKicker('PROJECT RESEARCH / '+(topic?.label||''),false)}<h2>${esc(topic?.label||'Project research')}</h2><p>${rows.length} project-specific claims · each reporting date and source boundary retained</p></header>${workspaceState.tab==='energy'?atlasPowerLadder(s):''}<div class="workspace-topic-claims ${timeline?'workspace-timeline':''}">${(timeline?rows.slice().sort((a,b)=>-atlasResearchDateOrder(a,b)):rows).map(row=>timeline?`<div class="workspace-timeline-entry"><time>${esc(row.as_of||'Undated')}</time>${atlasResearchClaim(row)}</div>`:atlasResearchClaim(row)).join('')||'<p>No accepted project-specific disclosure in this category. Open the original dossier to inspect the dated archive.</p>'}</div><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">All claims & revision history ↗</button></section>`;
}
function workspaceCompareContent(){
  const projects=saved.projectCompare.map(site).filter(Boolean);
  return `<h1>Compare projects.</h1><p>Independent estimates and source-reported scopes retain their dates. These columns do not establish complete fleets or additive capacity.</p>${projects.length?`<div class="table-wrap"><table class="workspace-project-comparison"><thead><tr><th>Dimension</th>${projects.map(s=>`<th>${esc(s.name)}<button data-workspace-remove-compare="${esc(s.id)}" aria-label="Remove ${esc(s.name)}">Remove ×</button></th>`).join('')}</tr></thead><tbody>${[['Location',s=>esc(s.location)],['Snapshot IT estimate',s=>spatialPower(s,'snapshot')==null?'Not quantified':fmt(spatialPower(s,'snapshot'))+' MW<br><small>'+esc(s.snapshot.date)+' · independent model</small>'],['Target IT estimate',s=>spatialPower(s,'target')==null?'Not quantified':fmt(spatialPower(s,'target'))+' MW<br><small>'+esc(s.target.date)+' · independent model</small>'],['Source-reported power',s=>workspacePhases(s).filter(r=>r.source_id).map(r=>`<p>${esc(r.scope)}: ${fmt(r.value)} ${esc(r.unit)}<br><small>${esc(statusLabel(r.status))} · ${esc(r.as_of||'Undated')}</small>${primaryRef(r.source_id)}</p>`).join('')||'No comparable disclosure'],['Counterparties',s=>primaryRelationships(s).map(r=>`${esc(r.role)}: ${esc(company(r.company_id)?.name||r.company_id)} ${primaryRef(r.source_id)}`).join('<br>')||esc(s.owner_label)],['Sources',s=>primarySourceIds(s).map(primaryRef).join(' ')+srefs(s.sources)],['Inspect',s=>`<button data-atlas-action="campus" data-id="${esc(s.id)}">Explore campus ↗</button>`]].map(([label,value])=>`<tr><th>${label}</th>${projects.map(s=>`<td>${value(s)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><button class="btn" data-workspace-export-compare>Export cited comparison ↓</button>`:'<p>Select Compare on a map selection or project to add up to three projects.</p>'}`;
}
function workspaceCompareDrawer(){openDrawer('project-comparison');}
function workspacePhases(s){
  const primary=primaryPowerRows(s).filter(o=>o.boundary==='critical_it'&&o.unit==='MW'&&!primaryIsContext(o));
  if(primary.length)return primary;
  return ['snapshot','target'].filter(key=>spatialPower(s,key)!=null).map(key=>({id:key,scope:key==='snapshot'?'Dated snapshot':'Projected end-state',value:spatialPower(s,key),unit:'MW',status:'modeled',as_of:s[key]?.date,qualifier:'Independent estimate; separate dates and scopes are not additive.',source_ids:s[key]?.sources||s.sources}));
}
function workspaceSelected(s){const rows=workspacePhases(s);return rows.find(r=>r.id===workspaceState.phaseBySite.get(s.id))||rows[0];}
function workspaceCollections(){return `<nav class="catalog-mode-switch workspace-collections" aria-label="Atlas collections"><button data-action="nav" data-id="overview" class="${['overview','globe'].includes(state.view)?'active':''}">Capacity</button><button data-action="nav" data-id="catalog" class="${state.view==='catalog'?'active':''}">Locations <span>${fmt(CATALOG.records.length)}</span></button><button data-action="nav" data-id="operators">Directories</button><button data-coverage-candidates>Research leads</button></nav>`;}
function workspaceToolbar(scale,filters=''){return `<div class="workspace-toolbar">${scale}<div class="workspace-tools">${filters}<button class="atlas-monitor-launch" data-atlas-action="monitor" aria-label="Source monitor and review queue" title="Source monitor and review queue">▤<span class="sr-only" id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button></div></div>`;}
function workspaceRefine(){return `<details class="atlas-filter-panel" ${state.spatialFiltersOpen?'open':''}><summary class="atlas-filter-toggle">Refine view</summary>${atlasFilterbar()}</details>`;}
function workspacePhaseDiagram(s,level){
  if(!s)return spatialFacilitySchematic(s,'snapshot',level);
  const rows=workspacePhases(s),selected=workspaceSelected(s),max=Math.max(1,...rows.map(r=>r.value));
  return `<section class="atlas-evidence-schematic workspace-phase-scene ${level===5?'workspace-phase-focus':''}" aria-label="Interactive project phase evidence">
    <header class="workspace-scene-head"><div><h2>${level===4?'Campus capacity & commitments':'Phase detail'}</h2><p>${esc(s.location)} · source-reported scopes</p></div><div class="workspace-view-toggle"><button data-workspace-location="false" aria-pressed="${!workspaceState.location}">Evidence</button><button data-workspace-location="true" aria-pressed="${workspaceState.location}">Location</button></div></header>
    ${workspaceState.location?`<div class="workspace-location-map"><canvas id="globe-canvas" tabindex="0" aria-label="Approximate project location and generalized geographic context"></canvas><span>Approximate ${esc(s.coordinate_precision||'research anchor')} · no site footprint established</span></div>`:''}
    <div class="workspace-phase-plot" ${workspaceState.location?'hidden':''}>
      <div class="workspace-plot-label"><span>EVIDENCE SCHEMATIC · GEOMETRY NOT ESTABLISHED</span><span>Select a scope to inspect</span></div>
      ${rows.length?`<div class="workspace-phase-rows">${rows.map((r,i)=>`<button class="workspace-phase-row ${r.id===selected?.id?'selected':''}" data-workspace-phase="${esc(r.id)}" data-site="${esc(s.id)}" aria-pressed="${r.id===selected?.id}"><span class="workspace-phase-label"><b>${esc(r.scope)}</b></span><strong>${fmt(r.value)} <small>${esc(r.unit)}</small></strong><span class="workspace-phase-status">${esc(statusLabel(r.status))}<small>${esc(r.as_of||'Date not disclosed')}</small></span></button>`).join('')}</div><p class="workspace-phase-boundary">Separate dated scopes · not additive · phase scopes are not building identities</p>`:`<div class="workspace-native"><strong>Not disclosed.</strong><p>No comparable IT-power quantity is established. Open the technical and commercial evidence to inspect the source's native units.</p><button class="btn" data-spatial-action="dossier" data-id="${esc(s.id)}">Open research dossier ↗</button></div>`}
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
      <p class="atlas-number-boundary">${row?.source_id?'Critical IT load · disclosed':'Independent IT estimate'}${level===4&&row?' · '+esc(row.scope):''}</p>
      <p class="workspace-phase-qualifier">${esc(row?.qualifier||'Native units and uncertainty remain attached to each source.')}</p>
      ${row?.source_id?primaryRef(row.source_id):srefs(row?.source_ids||s.sources)}
      <div class="workspace-dossier-actions"><button class="btn primary" data-spatial-action="dossier" data-id="${esc(s.id)}">Full dossier ↗</button><button class="text-button" data-workspace-compare="${esc(s.id)}">${saved.projectCompare.includes(s.id)?"✓ Comparing":"Compare +"}</button><button class="text-button" data-atlas-action="export" data-id="${esc(s.id)}">Export ↓</button></div>
    </section>
    <section class="atlas-insight-card">${atlasKicker('02 / COUNTERPARTIES')}${relationships.slice(0,4).map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} ↗</button>${primaryRef(r.source_id)}</div>`).join('')||`<p>${esc(s.owner_label)} · archived association</p>`}</section>
    <section class="atlas-insight-card">${atlasKicker('03 / EVIDENCE QUALITY')}<h2>${profile.sources.length} documents.<br>One traceable project.</h2><p>${profile.rows.length} project-specific claims. Surveyed building geometry is not established for this dossier.</p><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">Sources & revision history ↗</button></section>
  </div>`;
}
function workspaceRail(level,scope,s,phase){
  if(level>=4)return workspacePhaseRail(s,level);
  if(level>=2){const base=spatialRail(level,scope,s,phase);if(!s)return base;const node=document.createElement('div');node.innerHTML=base;node.querySelector('.atlas-insight-card')?.remove();return '<div class="atlas-insight-stack">'+workspaceSelectionRail(s,scope)+(node.querySelector('.atlas-insight-stack')?.innerHTML||'')+'</div>';}
  if(state.spatialSelectionActive&&s)return '<div class="atlas-insight-stack">'+workspaceSelectionRail(s,scope)+'<section class="atlas-insight-card">'+atlasKicker('02 / SELECTED EVIDENCE')+'<h2>Follow the source.</h2><p>Inspect this project without losing the map. Choose a member, enter the next scale, compare or read the dossier.</p><button class="text-button" data-spatial-action="dossier" data-id="'+esc(s.id)+'">Full project dossier ↗</button></section><section class="atlas-insight-card">'+atlasKicker('03 / CONTEXT')+'<p>'+scope.sites.length+' named records in this scope. Source locations remain separate from capacity estimates.</p></section></div>';
  const agg=spatialAggregate(scope.sites,phase),targets=spatialAggregate(scope.sites,'target'),companies=spatialCompanies(scope.sites);
  const countries=new Set(scope.sites.map(r=>r.country)).size;
  const ranked=spatialTopSites(scope.sites,phase==='snapshot'?'target':phase,3);
  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / THE GLOBAL TAKEAWAY')}<h2>${level===0?'Compute is a<br>physical asset class.':esc(scope.label)+'.<br>A connected system.'}</h2><p>${agg.count} projects across ${countries} countries. Follow their power, ownership and capital.</p><p class="atlas-card-footnote">${agg.known} IT estimates · ${agg.unknown} native / unknown. Partial coverage.</p></section>
    <section class="atlas-insight-card">${atlasKicker('02 / PROJECTED BUILDOUT')}<h2>Where capacity<br>is being planned.</h2>${atlasRankRows(ranked,'target')}<p class="atlas-card-footnote">${targets.known} dated target estimates. Targets are neither incremental additions nor live capacity.</p></section>
    <section class="atlas-insight-card">${atlasKicker('03 / CAPITAL & COUNTERPARTIES')}<h2>The companies<br>behind it.</h2><div class="atlas-company-cloud">${companies.map(({c})=>`<button data-action="company" data-id="${esc(c.id)}"><i style="background:${esc(c.color)}"></i>${esc(c.name)}</button>`).join('')}</div><button class="text-button" data-action="nav" data-id="investment">Open the investment lens ↗</button></section></div>`;
}
function workspaceProjectTabs(s){
  return `<nav class="workspace-project-tabs atlas-project-shortcuts" role="tablist" aria-label="Facility research sections">${WORKSPACE_TOPICS.map(([topic,label])=>`<button role="tab" aria-selected="${workspaceState.tab===topic}" tabindex="${workspaceState.tab===topic?0:-1}" data-workspace-topic="${topic}" class="${workspaceState.tab===topic?'active':''}">${label}</button>`).join('')}</nav>`;
}
function workspaceResearchView(){
  const st=spatialState(),s=spatialDefaultSite(),level=st.spatialLevel,phase=st.spatialPhase,scope=spatialScope(level,s),[title,description]=spatialHeadline(level,scope,s),campus=level>=4;
  const excluded=s&&!spatialFiltered().some(x=>x.id===s.id);
  const mapHTML=campus?workspacePhaseDiagram(s,level):spatialMap(scope,s,level,phase).replace('<div class="atlas-map-legend">','<div class="atlas-map-legend"><span class="workspace-context-key">· OSM locations · no capacity implied</span>');
  return `<article class="atlas-experience atlas-workspace atlas-editorial atlas-level-${level}">
    ${globalThis.ATLAS_CATALOG_WARNING?'<p class="workspace-data-warning" role="status">Catalog service unavailable · showing the dated community-map snapshot.</p>':''}
    <header class="atlas-intro"><div><div class="atlas-eyebrow">${campus?'FACILITY & CAMPUS':'COMPUTE, FROM THE GROUND UP'}</div><h1>${campus?esc(s?.name||'No matching project'):title}</h1>${campus?`<p class="atlas-location">⌖ ${esc(s?.location||'')} · ${esc(s?.country||'')}</p>`:''}</div><div class="atlas-intro-aside"><p>${description}</p>${campus&&s?`<button class="btn primary" data-action="favorite" data-id="${esc(s.id)}">${saved.favorites.includes(s.id)?'★ On research shelf':'Add to research shelf +'}</button>`:'<button class="btn primary" data-atlas-action="journey">Take the five-stop tour ↗</button>'}</div></header>
    ${workspaceFilterChips()}${excluded?'<p class="workspace-data-warning" role="status">Selected project is outside the current refinements. Its identity is retained. <button class="text-button" data-atlas-action="clear-filters">Clear refinements ↗</button></p>':''}
    ${campus&&s?workspaceProjectTabs(s):''}
    <div class="atlas-spatial-layout"><div class="atlas-map-column"><section class="atlas-map-panel">${workspaceToolbar(spatialStageStrip(level),workspaceRefine())}${mapHTML}</section>${campus&&s?workspaceTopicContent(s):spatialKpis(scope,phase)}<div class="workspace-map-context"><span>${esc(scope.note)}</span><button class="text-button" data-atlas-action="source-context">Sources, coverage & methodology ↗</button></div>${workspaceCollections()}</div><aside class="atlas-spatial-rail" aria-label="Analysis and evidence">${workspaceRail(level,scope,s,phase)}</aside></div>
    ${campus&&s?`<details class="workspace-research-detail"><summary>All project claims & dated disclosures <span>↓</span></summary>${atlasCampusBrief(s)}${atlasResearchPanel(s)}</details>`:atlasRecordList(scope,phase)}
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
  const stats=root.querySelector('#catalog-stats');if(stats)root.querySelector('.atlas-map-column')?.append(stats);
  const strip=root.querySelector('.catalog-scale-strip');if(strip){const bar=document.createElement('div');bar.className='workspace-toolbar';strip.before(bar);bar.append(strip);bar.insertAdjacentHTML('beforeend',workspaceCollections());}
  if(root.classList.contains('catalog-facility')){
    const inspector=root.querySelector('.catalog-inspector'),rail=root.querySelector('.atlas-spatial-rail .atlas-insight-stack');
    if(inspector&&rail){rail.querySelector('.atlas-insight-card.accent')?.remove();rail.prepend(inspector);}
  }
  return container.innerHTML;
};
// Project selection is explicit, source-backed and inspectable on the same screen.
document.addEventListener('click',event=>{
  const favorite=event.target.closest('.atlas-intro [data-action="favorite"]');if(favorite)favorite.textContent=saved.favorites.includes(favorite.dataset.id)?'★ On research shelf':'Add to research shelf +';
  const topic=event.target.closest('[data-workspace-topic]');
  if(topic){workspaceState.tab=topic.dataset.workspaceTopic;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-workspace-topic="${workspaceState.tab}"]`)?.focus({preventScroll:true});}
  const selection=event.target.closest('[data-workspace-select]');
  if(selection){state.spatialCluster=[];spatialTransition({selected:selection.dataset.workspaceSelect});}
  if(event.target.closest('[data-workspace-enter]'))spatialTransition({level:Math.min(4,state.spatialLevel+1)});
  const clear=event.target.closest('[data-workspace-clear]');
  if(clear){const key=clear.dataset.workspaceClear;if(key==='evidence')state.spatialEvidence='all';else state.filter[key]=key==='q'?'':'all';state.spatialFiltersOpen=false;spatialTransition({replace:true});}
  const compare=event.target.closest('[data-workspace-compare]');
  if(compare){const id=compare.dataset.workspaceCompare;if(!site(id))return;if(saved.projectCompare.includes(id))saved.projectCompare=saved.projectCompare.filter(x=>x!==id);else if(saved.projectCompare.length<3)saved.projectCompare.push(id);else{toast('Compare up to three projects. Remove one to add another.');workspaceCompareDrawer();return;}save();compare.textContent=saved.projectCompare.includes(id)?'✓ Comparing':'Compare +';toast(saved.projectCompare.length+' projects in comparison');}
  if(event.target.closest('[data-workspace-open-compare]'))workspaceCompareDrawer();
  const remove=event.target.closest('[data-workspace-remove-compare]');if(remove){saved.projectCompare=saved.projectCompare.filter(x=>x!==remove.dataset.workspaceRemoveCompare);save();$('#drawer-content').innerHTML=workspaceCompareContent();$('#drawer-content [data-workspace-export-compare]')?.focus();}
  if(event.target.closest('[data-workspace-export-compare]'))download('compute-atlas-project-comparison.json',{published_at:ATLAS_PRIMARY.published_at,policy:'Different dated scopes are not additive. Partial research, not complete fleets.',projects:saved.projectCompare.map(site).filter(Boolean).map(atlasCitedDossier)});
  const phase=event.target.closest('[data-workspace-phase]');
  if(phase){const s=site(phase.dataset.site);if(!s||!workspacePhases(s).some(r=>r.id===phase.dataset.workspacePhase))return;workspaceState.phaseBySite.set(s.id,phase.dataset.workspacePhase);state.spatialLevel=5;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-workspace-phase="${CSS.escape(phase.dataset.workspacePhase)}"]`)?.focus({preventScroll:true});}
  const location=event.target.closest('[data-workspace-location]');if(location){workspaceState.location=location.dataset.workspaceLocation==='true';render();document.querySelector(`[data-workspace-location="${workspaceState.location}"]`)?.focus({preventScroll:true});}
  if(event.target.closest('[data-workspace-overview]'))document.querySelector('.atlas-map-panel')?.scrollIntoView({block:'start',behavior:'smooth'});
});
document.addEventListener('keydown',event=>{
  const tab=event.target.closest('[data-workspace-topic]');if(!tab||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  event.preventDefault();const i=WORKSPACE_TOPICS.findIndex(([id])=>id===tab.dataset.workspaceTopic),next=event.key==='Home'?0:event.key==='End'?WORKSPACE_TOPICS.length-1:(i+(event.key==='ArrowLeft'?-1:1)+WORKSPACE_TOPICS.length)%WORKSPACE_TOPICS.length;
  document.querySelector(`[data-workspace-topic="${WORKSPACE_TOPICS[next][0]}"]`)?.click();
});
const workspaceUtility=document.createElement('button');workspaceUtility.className='side-tool';workspaceUtility.dataset.workspaceOpenCompare='';workspaceUtility.textContent='⇄ Compare projects';document.querySelector('.side-bottom')?.prepend(workspaceUtility);
const workspaceRenderNav=renderNav;
renderNav=function(){
  workspaceRenderNav();
  const primary=['overview','facilities','companies','contracts','investment','reports'];
  const navButton=([id,label])=>`<button class="nav-button ${state.view===id?'active':''}" data-action="nav" data-id="${id}">${icon(id)}${id==='reports'?'Research library':label}</button>`;
  $('#navigation').innerHTML=primary.map(id=>NAV.find(([key])=>key===id)).filter(Boolean).map(navButton).join('')+`<details class="workspace-nav-more" ${primary.includes(state.view)?'':'open'}><summary>More research tools</summary>${NAV.filter(([id])=>!primary.includes(id)).map(navButton).join('')}</details>`;
  if(['overview','globe'].includes(state.view)){
    const s=spatialDefaultSite(),level=state.spatialLevel,scope=spatialScope(level,s);
    const parts=['The landscape'];if(level>=1)parts.push(spatialScope(1,s).label);if(level>=2)parts.push(spatialScope(2,s).label);if(level>=3)parts.push(spatialScope(3,s).label);if(level>=4&&s)parts.push(s.name);if(level===5&&s)parts.push(workspaceSelected(s)?.scope||'Evidence detail');
    $('#breadcrumb').textContent=parts.join(' › ');
  }
};
// Reading a source must preserve the campus/topic/phase return point.
const workspaceOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts={}){workspaceOpenDrawer(kind,id,opts);if(kind==='project-comparison'){$('#drawer-type').textContent='PROJECT COMPARISON';$('#drawer-content').innerHTML=workspaceCompareContent();}};
ATLAS.openDrawer=openDrawer;
const workspaceCloseDrawer=closeDrawer;
closeDrawer=function(){const wasOpen=!$('#drawer').hidden;workspaceCloseDrawer();if(wasOpen&&['overview','globe'].includes(state.view))history.replaceState(null,'',spatialURL());};
// Phase inspection survives sharing and reload without changing the research ledger.
const workspaceSpatialURL=spatialURL;
spatialURL=function(view=state.view){const url=workspaceSpatialURL(view);if(!['overview','globe'].includes(view))return url;const s=site(state.spatialSelected),id=s&&workspaceState.phaseBySite.get(s.id);return url+(id?'&claim='+encodeURIComponent(id):'')+(workspaceState.tab!=='overview'?'&topic='+workspaceState.tab:'');};
const workspaceRoute=routeFromHash;window.removeEventListener('hashchange',workspaceRoute);
routeFromHash=function(){const p=new URLSearchParams(location.hash.split('?')[1]||''),s=site(p.get('site'));workspaceState.tab=WORKSPACE_TOPICS.some(([id])=>id===p.get('topic'))?p.get('topic'):'overview';if(s){if(workspacePhases(s).some(r=>r.id===p.get('claim')))workspaceState.phaseBySite.set(s.id,p.get('claim'));else workspaceState.phaseBySite.delete(s.id);}workspaceRoute();};window.addEventListener('hashchange',routeFromHash);
// Preserve existing explicit catalog links. A fresh visit opens the approved landscape.
if(!ATLAS_ENTRY_HASH){state.spatialLevel=0;state.view='overview';if(location.protocol!=='about:')history.replaceState(null,'',spatialURL('overview'));render();}else routeFromHash();
ATLAS.workspace={phases:workspacePhases,selected:workspaceSelected,state:workspaceState,compare:()=>saved.projectCompare,compareDrawer:workspaceCompareDrawer};
document.documentElement.classList.add('research-ready','atlas-ready','workspace-ready');
