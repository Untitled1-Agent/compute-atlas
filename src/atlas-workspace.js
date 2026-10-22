'use strict';
/* Shared map-led workspace. Collections stay separate; presentation and navigation do not. */
const workspaceState={phaseBySite:new Map(),tab:'overview',location:false,mobileExpanded:false,records:{scope:'geography',sort:'power',page:0,open:false},visibleIds:null};
const WORKSPACE_TOPICS=[['overview','Overview'],['energy','Power & phases'],['technical','Technical design'],['development','Timeline'],['commercial','Counterparties'],['finance','Investment'],['evidence','Sources & evidence']];
saved.projectCompare=Array.isArray(saved.projectCompare)?saved.projectCompare.filter(id=>site(id)).slice(0,3):[];
function workspaceFilterChips(){
  const entries=[['region',state.spatialRegion],['stage',state.filter.stage!=='all'&&({snapshot:'Has snapshot estimate',target:'Has target estimate',unknown:'No snapshot or target'})[state.filter.stage]],['q',state.filter.q],['company',state.filter.company!=='all'&&company(state.filter.company)?.name],['country',state.filter.country!=='all'&&state.filter.country],['evidence',state.spatialEvidence!=='all'&&state.spatialEvidence]];
  return `<div class="workspace-filter-chips">${entries.filter(([,value])=>value).map(([key,value])=>`<button data-workspace-clear="${key}" aria-label="Remove ${esc(value)} filter">${esc(value)} <span>×</span></button>`).join('')}</div>`;
}
function workspaceSelectionRail(s,scope){
  const members=(state.spatialCluster||[]).map(site).filter(Boolean),cluster=members.length>1;
  return `<section class="atlas-insight-card workspace-selection">${atlasKicker(cluster?'01 / SELECTED CLUSTER':'01 / SELECTED PROJECT')}<h2>${esc(cluster?researchClusterName(members):s.name)}</h2><p>${cluster?members.length+' research records · visual grouping, not a common campus':esc(s.location)}</p>${cluster?`<div class="workspace-cluster-members">${members.map(x=>`<button data-workspace-select="${esc(x.id)}">${esc(x.name)}<small>${esc(x.location)}</small></button>`).join('')}</div>`:`${atlasRow('Snapshot IT estimate',spatialPower(s,'snapshot')==null?'Not quantified':fmt(spatialPower(s,'snapshot'))+' MW')}${atlasRow('Target IT estimate',spatialPower(s,'target')==null?'Not quantified':fmt(spatialPower(s,'target'))+' MW')}`}<p class="atlas-card-footnote">Independent, mixed-vintage estimates; the target is not added to the snapshot.</p><div class="workspace-dossier-actions"><button class="btn primary" data-workspace-enter>Explore ${state.spatialLevel<3?'next scale':'this campus'} →</button><button class="text-button" data-workspace-compare="${esc(s.id)}">${saved.projectCompare.includes(s.id)?'✓ Comparing':'Compare +'}</button></div></section>`;
}
function workspaceTopicContent(s){
  if(workspaceState.tab==='overview')return `<div class="workspace-evidence-bottom">${atlasSourcesPanel(s,{compact:true})}${atlasNotePanel(s)}</div><div class="atlas-detail-pair">${atlasPowerLadder(s)}${atlasAttributes(s,{compact:true})}</div>`;
  if(workspaceState.tab==='evidence')return `<div class="workspace-evidence-bottom">${atlasSourcesPanel(s)}${atlasNotePanel(s)}</div>${atlasResearchPanel(s)}`;
  const p=atlasResearchProfile(s),topic=p.topics.find(t=>t.id===workspaceState.tab),rows=topic?.rows||[];
  const timeline=workspaceState.tab==='development';
  return `<section class="workspace-topic-content" data-workspace-topic-content="${workspaceState.tab}"><header>${atlasKicker('PROJECT RESEARCH / '+(topic?.label||''),false)}<h2>${esc(topic?.label||'Project research')}</h2><p>${rows.length} project-specific claims · each reporting date and source boundary retained</p></header>${workspaceState.tab==='energy'?atlasPowerLadder(s):''}<div class="workspace-topic-claims ${timeline?'workspace-timeline':''}">${(timeline?rows.slice().sort((a,b)=>-atlasResearchDateOrder(a,b)):rows).map(row=>timeline?`<div class="workspace-timeline-entry"><time>${esc(row.as_of||'Undated')}</time>${atlasResearchClaim(row)}</div>`:atlasResearchClaim(row)).join('')||'<p>No accepted project-specific disclosure in this category. Open the original dossier to inspect the dated archive.</p>'}</div><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">All claims & revision history →</button></section>`;
}
function workspaceCompareResults(){
  const q=(workspaceState.compareQuery||'').trim().toLocaleLowerCase();
  const rows=D.sites.filter(s=>[s.name,s.location,s.owner_label,s.country].join(' ').toLocaleLowerCase().includes(q)).sort((a,b)=>a.name.localeCompare(b.name));
  return `<p role="status">${rows.length} matching projects · ${saved.projectCompare.length}/3 selected${rows.length>8?' · first 8 shown; refine your search':''}</p><div class="workspace-compare-options">${rows.slice(0,8).map(s=>`<button data-workspace-add-compare="${esc(s.id)}" ${saved.projectCompare.includes(s.id)||saved.projectCompare.length>=3?'disabled':''}><span><strong>${esc(s.name)}</strong><small>${esc(s.location)} · ${esc(s.owner_label)}</small></span><span>${saved.projectCompare.includes(s.id)?'Selected':'Add +'}</span></button>`).join('')||'<p>No projects match. Try a place, operator or shorter name.</p>'}</div>`;
}
function workspaceRefreshComparison(focus='workspace-compare-query'){
  $('#drawer-content').innerHTML=workspaceCompareContent();
  document.getElementById(focus)?.focus({preventScroll:true});
}
function workspaceCompareTopic(s,id){
  const topic=atlasResearchProfile(s).topics.find(t=>t.id===id);
  if(!topic?.rows.length)return '<span class="muted">No accepted project-specific disclosure</span>';
  return `<details class="workspace-compare-claims"><summary>${topic.rows.length} dated ${topic.rows.length===1?'claim':'claims'}</summary>${topic.rows.map(atlasResearchClaim).join('')}</details>`;
}
function workspaceCompareContent(){
  const projects=saved.projectCompare.map(site).filter(Boolean);
  return `<h1>Compare projects.</h1><p>Independent estimates and source-reported scopes retain their dates. These columns do not establish complete fleets or additive capacity.</p><section class="workspace-compare-picker" aria-label="Choose projects to compare"><label for="workspace-compare-query">Find a project, location or operator</label><input id="workspace-compare-query" type="search" value="${esc(workspaceState.compareQuery||'')}" placeholder="New Carlisle, Helios, Tencent…" autocomplete="off"><div id="workspace-compare-results">${workspaceCompareResults()}</div>${projects.length===3?'<p>Three projects selected. Remove a column to choose another.</p>':''}</section>${projects.length?`<div class="table-wrap workspace-comparison-scroll" tabindex="0" role="region" aria-label="Project comparison; scroll horizontally for all columns"><table class="workspace-project-comparison"><thead><tr><th>Dimension</th>${projects.map(s=>`<th>${esc(s.name)}<button data-workspace-remove-compare="${esc(s.id)}" aria-label="Remove ${esc(s.name)}">Remove ×</button></th>`).join('')}</tr></thead><tbody>${[['Location',s=>esc(s.location)],['Snapshot IT estimate',s=>spatialPower(s,'snapshot')==null?'Not quantified':fmt(spatialPower(s,'snapshot'))+' MW<br><small>'+esc(s.snapshot.date)+' · independent model</small>'],['Target IT estimate',s=>spatialPower(s,'target')==null?'Not quantified':fmt(spatialPower(s,'target'))+' MW<br><small>'+esc(s.target.date)+' · independent model</small>'],['Source-reported power',s=>primaryObservations(s).filter(r=>r.metric==='power'&&!primaryIsContext(r)).map(r=>`<p>${esc(r.scope)}: ${observationValue(r)}${r.value==null?'':' '+esc(r.unit)}<br><small>${esc(boundaryLabel(r.boundary))} · ${esc(statusLabel(r.status))} · ${esc(r.as_of||'Undated')}</small>${primaryRef(r.source_id)}</p>`).join('')||'No comparable disclosure'],['Counterparties',s=>primaryRelationships(s).map(r=>`${esc(r.role)}: ${esc(company(r.company_id)?.name||r.company_id)} ${primaryRef(r.source_id)}`).join('<br>')||esc(s.owner_label)],['Technical design',s=>workspaceCompareTopic(s,'technical')],['Development & milestones',s=>workspaceCompareTopic(s,'development')],['Investment & financing',s=>workspaceCompareTopic(s,'finance')],['Sources',s=>primarySourceIds(s).map(primaryRef).join(' ')+srefs(s.sources)],['Inspect',s=>`<button data-atlas-action="campus" data-id="${esc(s.id)}">Explore campus →</button>`]].map(([label,value])=>`<tr><th>${label}</th>${projects.map(s=>`<td>${value(s)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><label class="workspace-compare-private"><input type="checkbox" data-workspace-compare-notes ${workspaceState.compareNotes?'checked':''}> Include my private project notes in the export</label><button class="btn" data-workspace-export-compare>Export cited comparison ↓</button>`:'<p>Choose up to three projects above, or select Compare while exploring the map.</p>'}`;
}
function workspaceCompareDrawer(){openDrawer('project-comparison');}
function workspacePhases(s){
  const primary=primaryPowerRows(s).filter(o=>o.boundary==='critical_it'&&o.unit==='MW'&&!primaryIsContext(o));
  if(primary.length)return primary;
  return ['snapshot','target'].filter(key=>spatialPower(s,key)!=null).map(key=>({id:key,scope:key==='snapshot'?'Dated snapshot':'Projected end-state',value:spatialPower(s,key),unit:'MW',status:'modeled',as_of:s[key]?.date,qualifier:'Independent estimate; separate dates and scopes are not additive.',source_ids:s[key]?.sources||s.sources}));
}
function workspaceSelected(s){const rows=workspacePhases(s);return rows.find(r=>r.id===workspaceState.phaseBySite.get(s.id))||rows[0];}
function workspaceCollections(){return `<nav class="catalog-mode-switch workspace-collections" aria-label="Atlas collections"><button data-action="nav" data-id="overview" class="${['overview','globe'].includes(state.view)?'active':''}">Capacity</button><button data-action="nav" data-id="catalog" class="${state.view==='catalog'?'active':''}">Locations <span>${fmt(CATALOG.records.length)}</span></button><button data-action="nav" data-id="operators">Directories</button><button data-coverage-candidates>Research leads</button></nav>`;}
function workspaceToolbar(scale,filters=''){return `<div class="workspace-toolbar">${scale}<div class="workspace-tools">${filters}<button class="workspace-share-button" data-workspace-share>Share view →</button><button class="atlas-monitor-launch" data-atlas-action="monitor" aria-label="Source monitor and review queue" title="Source monitor and review queue">▤<span class="sr-only" id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button></div></div>`;}
function workspaceRefine(){return `<details class="atlas-filter-panel" ${state.spatialFiltersOpen?'open':''}><summary class="atlas-filter-toggle">Refine view</summary>${atlasFilterbar()}</details>`;}
function workspacePhaseDiagram(s,level){
  if(!s)return spatialFacilitySchematic(s,'snapshot',level);
  const rows=workspacePhases(s),selected=workspaceSelected(s),max=Math.max(1,...rows.map(r=>r.value));
  return `<section class="atlas-evidence-schematic workspace-phase-scene ${level===5?'workspace-phase-focus':''}" aria-label="Interactive project phase evidence">
    <header class="workspace-scene-head"><div><h2>${level===4?'Campus capacity & commitments':'Phase detail'}</h2><p>${esc(s.location)} · source-reported scopes</p></div><div class="workspace-view-toggle"><button data-workspace-location="false" aria-pressed="${!workspaceState.location}">Evidence</button><button data-workspace-location="true" aria-pressed="${workspaceState.location}">Location</button></div></header>
    ${workspaceState.location?`<div class="workspace-location-map"><canvas id="globe-canvas" tabindex="0" aria-label="Approximate project location and generalized geographic context"></canvas><span>Approximate ${esc(s.coordinate_precision||'research anchor')} · no site footprint established</span></div>`:''}
    <div class="workspace-phase-plot" ${workspaceState.location?'hidden':''}>
      <div class="workspace-plot-label"><span>EVIDENCE SCHEMATIC · GEOMETRY NOT ESTABLISHED</span><span>Select a scope to inspect</span></div>
      ${rows.length?`<div class="workspace-phase-rows">${rows.map((r,i)=>`<button class="workspace-phase-row ${r.id===selected?.id?'selected':''}" data-workspace-phase="${esc(r.id)}" data-site="${esc(s.id)}" aria-pressed="${r.id===selected?.id}"><span class="workspace-phase-label"><b>${esc(r.scope)}</b></span><strong>${fmt(r.value)} <small>${esc(r.unit)}</small></strong><span class="workspace-phase-status">${esc(statusLabel(r.status))}<small>${esc(r.as_of||'Date not disclosed')}</small></span></button>`).join('')}</div><p class="workspace-phase-boundary">Separate dated scopes · not additive · phase scopes are not building identities</p>`:`<div class="workspace-native"><strong>Not disclosed.</strong><p>No comparable IT-power quantity is established. Open the technical and commercial evidence to inspect the source's native units.</p><button class="btn" data-spatial-action="dossier" data-id="${esc(s.id)}">Open research dossier →</button></div>`}
    </div>
    <footer class="workspace-scene-foot"><span>EVIDENCE SCHEMATIC · NOT A PARCEL / BUILDING SURVEY</span><button class="text-button" data-atlas-action="source-context">Map & evidence boundary →</button></footer>
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
      <div class="workspace-dossier-actions"><button class="btn primary" data-spatial-action="dossier" data-id="${esc(s.id)}">Full dossier →</button><button class="text-button" data-workspace-compare="${esc(s.id)}">${saved.projectCompare.includes(s.id)?"✓ Comparing":"Compare +"}</button><button class="text-button" data-atlas-action="export" data-id="${esc(s.id)}">Export ↓</button></div>
    </section>
    <section class="atlas-insight-card">${atlasKicker('02 / COUNTERPARTIES')}${relationships.slice(0,4).map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} →</button>${primaryRef(r.source_id)}</div>`).join('')||`<p>${esc(s.owner_label)} · archived association</p>`}</section>
    <section class="atlas-insight-card">${atlasKicker('03 / EVIDENCE QUALITY')}<h2>${profile.sources.length} documents.<br>One traceable project.</h2><p>${profile.rows.length} project-specific claims. Surveyed building geometry is not established for this dossier.</p><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">Sources & revision history →</button></section>
  </div>`;
}
// Geographic analysis uses the same comparable-estimate rule as the map.
const WORKSPACE_REGIONS=['North America','Europe','Asia','Middle East','Oceania','South America','Africa','Other'];
const workspaceBaseDefaultSite=spatialDefaultSite;
spatialDefaultSite=function(){
  if(state.spatialLevel<=1&&WORKSPACE_REGIONS.includes(state.spatialRegion)&&!state.spatialSelectionActive){
    const rows=spatialFiltered().filter(s=>spatialContinent(s)===state.spatialRegion);
    const selected=rows.find(s=>s.id===state.spatialSelected)||rows[0];
    state.spatialSelected=selected?.id||null;
    return selected||null;
  }
  return workspaceBaseDefaultSite();
};
const workspaceBaseScope=spatialScope;
spatialScope=function(level,selected){
  if(level<=1&&WORKSPACE_REGIONS.includes(state.spatialRegion)){
    const rows=spatialMapped().filter(s=>spatialContinent(s)===state.spatialRegion);
    return {label:state.spatialRegion,region:state.spatialRegion,sites:rows,bounds:spatialFitBounds(rows,null),note:'Regional research scope · partial, mixed-vintage estimates; not a market census'};
  }
  return workspaceBaseScope(level,selected);
};
function workspaceRegionalRows(scope){
  return WORKSPACE_REGIONS.map(name=>({name,...spatialAggregate(scope.sites.filter(s=>spatialContinent(s)===name),'target')})).filter(r=>r.count).sort((a,b)=>b.mw-a.mw||b.count-a.count||a.name.localeCompare(b.name));
}
function workspaceRegionLink(name){
  const p=new URLSearchParams(spatialURL().split('?')[1]||'');
  for(const key of ['site','inspect','camera','preset','members','claim','topic','page'])p.delete(key);
  p.set('scale','continent');p.set('region',name);
  return '#overview?'+p.toString();
}
function workspaceRegionalAnalysis(scope){
  const rows=workspaceRegionalRows(scope),max=Math.max(1,...rows.map(r=>r.mw));
  return `<div class="workspace-region-ranks">${rows.map(r=>`<a class="workspace-region-row" href="${esc(workspaceRegionLink(r.name))}" data-workspace-region="${esc(r.name)}"><span class="workspace-region-name">${esc(r.name)} <span aria-hidden="true">→</span></span><strong>${r.known?fmt(r.mw/1000,3)+' GW':'Not quantified'}</strong><small>${r.known} quantified · ${r.unknown} unquantified</small><span class="workspace-region-track" aria-hidden="true"><i style="width:${r.mw/max*100}%"></i></span></a>`).join('')||'<p>No mapped research projects match these refinements.</p>'}</div><p class="atlas-card-footnote">Independent target IT estimates · partial, mixed-vintage subtotals. Targets are not incremental additions or live capacity. Unquantified is not zero.</p>`;
}
function workspaceCampusPreview(scope){
  const scenes=JSON.parse(document.getElementById('campus-scenes')?.textContent||'{"scenes":[]}').scenes;
  const m=scenes.find(m=>scope.sites.some(s=>s.id===m.project_id)&&m.features.length),s=scope.sites.find(s=>s.id===m?.project_id)||scope.sites[0];
  if(!s)return '<p>No campus matches these refinements. Broaden the view to explore the research collection.</p>';
  const p=new URLSearchParams(spatialURL().split('?')[1]||'');
  for(const key of ['camera','preset','members','claim','topic','page','region','feature','featureversion','scenecamera'])p.delete(key);
  p.set('scale','campus');p.set('site',s.id);p.set('inspect','1');
  if(m){p.set('scene',m.id);p.set('imageversion',m.image.sha256);p.set('campusview','aerial');}
  return `<a class="workspace-campus-preview" href="#overview?${esc(p.toString())}" data-workspace-preview="${esc(m?.id||s.id)}">${m?`<img src="${esc(m.image.data_url||m.image.path)}" alt="${esc(s.name)} historical source image, ${esc(m.image.acquired_at)}" loading="lazy">`:''}<strong>${esc(s.name)} <span aria-hidden="true">→</span></strong><small>${m?esc(m.image.acquired_at)+' imagery · interpreted roofs':'Accepted historical imagery unavailable'}</small></a><p class="atlas-card-footnote">${m?'Historical physical context. Roofs do not establish current operations or phase-level IT allocation.':'Project evidence remains available. No building geometry or capacity assignment is inferred.'}</p>`;
}
function workspaceRail(level,scope,s,phase){
  if(level>=4)return workspacePhaseRail(s,level);
  if(level>=2){const base=spatialRail(level,scope,s,phase);if(!s)return base;const node=document.createElement('div');node.innerHTML=base;node.querySelector('.atlas-insight-card')?.remove();return '<div class="atlas-insight-stack">'+workspaceSelectionRail(s,scope)+(node.querySelector('.atlas-insight-stack')?.innerHTML||'')+'</div>';}
  if(state.spatialSelectionActive&&s)return '<div class="atlas-insight-stack">'+workspaceSelectionRail(s,scope)+'<section class="atlas-insight-card">'+atlasKicker('02 / SELECTED EVIDENCE')+'<h2>Follow the source.</h2><p>Inspect this project without losing the map. Choose a member, enter the next scale, compare or read the dossier.</p><button class="text-button" data-spatial-action="dossier" data-id="'+esc(s.id)+'">Full project dossier →</button></section><section class="atlas-insight-card">'+atlasKicker('03 / CONTEXT')+'<p>'+scope.sites.length+' named records in this scope. Source locations remain separate from capacity estimates.</p></section></div>';
  const agg=spatialAggregate(scope.sites,phase);
  const countries=new Set(scope.sites.map(r=>r.country)).size;

  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / THE GLOBAL TAKEAWAY')}<h2>${level===0?'Compute is a<br>physical asset class.':esc(scope.label)+'.<br>A connected system.'}</h2><p>${agg.count} projects across ${countries} countries. Follow their power, ownership and capital.</p><p class="atlas-card-footnote">${agg.known} IT estimates · ${agg.unknown} native / unknown. Partial coverage.</p></section>
    <section class="atlas-insight-card">${atlasKicker('02 / PROJECTED BUILDOUT')}<h2>Where capacity is planned.</h2>${workspaceRegionalAnalysis(scope)}</section>
    <section class="atlas-insight-card">${atlasKicker('03 / GO INSIDE A CAMPUS')}${workspaceCampusPreview(scope)}</section></div>`;
}
function workspaceProjectTabs(s){
  return `<nav class="workspace-project-tabs atlas-project-shortcuts" role="tablist" aria-label="Facility research sections">${WORKSPACE_TOPICS.map(([topic,label])=>`<button role="tab" aria-selected="${workspaceState.tab===topic}" tabindex="${workspaceState.tab===topic?0:-1}" data-workspace-topic="${topic}" class="${workspaceState.tab===topic?'active':''}">${label}</button>`).join('')}</nav>`;
}
function workspaceMobileRail(level,scope,s,phase){
  const members=(state.spatialCluster||[]).map(site).filter(Boolean),selected=s&&(state.spatialSelectionActive||level>=2),row=level>=4&&s?workspaceSelected(s):null;
  const title=selected?(members.length>1?researchClusterName(members):s.name):'Analysis & evidence';
  const quantity=row?row.scope+' · '+fmt(row.value)+' '+row.unit+' · '+statusLabel(row.status)+' · '+(row.as_of||'Undated'):selected?spatialPower(s,phase)==null?'IT not quantified':fmt(spatialPower(s,phase))+' MW · '+phase+' estimate · '+(s[phase]?.date||'Undated'):scope.sites.length+' named research projects';
  return `<aside class="atlas-spatial-rail workspace-mobile-rail" data-expanded="${workspaceState.mobileExpanded}" aria-label="Analysis and evidence"><button class="workspace-mobile-summary" data-workspace-inspector aria-expanded="${workspaceState.mobileExpanded}" aria-controls="workspace-selection-detail"><span><small>${selected?'SELECTED '+(members.length>1?'CLUSTER':'PROJECT'):'IN THIS VIEW'}</small><strong>${esc(title)}</strong><span>${esc(quantity)}</span></span><span class="workspace-mobile-expand">${workspaceState.mobileExpanded?'Close ↑':'Inspect ↓'}</span></button><div id="workspace-selection-detail">${workspaceRail(level,scope,s,phase)}</div></aside>`;
}
function workspaceResearchView(){
  const st=spatialState(),s=spatialDefaultSite(),level=st.spatialLevel,phase=st.spatialPhase,scope=spatialScope(level,s),[title,description]=spatialHeadline(level,scope,s),campus=level>=4;
  const excluded=s&&!spatialFiltered().some(x=>x.id===s.id);
  const mapHTML=campus?workspacePhaseDiagram(s,level):spatialMap(scope,s,level,phase).replace('<div class="atlas-map-legend">','<div class="atlas-map-legend"><span class="workspace-context-key">· OSM locations · no capacity implied</span>');
  return `<article class="atlas-experience atlas-workspace atlas-editorial atlas-level-${level} ${level<=1?'workspace-landscape':''}">
    ${globalThis.ATLAS_CATALOG_WARNING?'<p class="workspace-data-warning" role="status">Catalog service unavailable · showing the dated community-map snapshot.</p>':''}
    <header class="atlas-intro"><div><div class="atlas-eyebrow">${campus?'FACILITY & CAMPUS':'COMPUTE, FROM THE GROUND UP'}</div><h1>${campus?esc(s?.name||'No matching project'):title}</h1>${campus?`<p class="atlas-location">⌖ ${esc(s?.location||'')} · ${esc(s?.country||'')}</p>`:''}</div><div class="atlas-intro-aside"><p>${description}</p>${campus&&s?`<button class="btn primary" data-action="favorite" data-id="${esc(s.id)}">${saved.favorites.includes(s.id)?'★ On research shelf':'Add to research shelf +'}</button>`:'<button class="btn primary" data-atlas-action="journey">Take the five-stop tour →</button>'}</div></header>
    ${workspaceFilterChips()}${excluded?'<p class="workspace-data-warning" role="status">Selected project is outside the current refinements. Its identity is retained. <button class="text-button" data-atlas-action="clear-filters">Clear refinements →</button></p>':''}
    ${campus&&s?workspaceProjectTabs(s):''}
    <div class="atlas-spatial-layout"><div class="atlas-map-column"><section class="atlas-map-panel">${workspaceToolbar(spatialStageStrip(level),workspaceRefine())}${mapHTML}</section></div>${workspaceMobileRail(level,scope,s,phase)}<div class="workspace-map-lower">${campus&&s?workspaceTopicContent(s):spatialKpis(scope,phase)}<div class="workspace-map-context"><span>${esc(scope.note)}</span><button class="text-button" data-atlas-action="source-context">Sources, coverage & methodology →</button></div>${workspaceCollections()}</div></div>
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
const WORKSPACE_PAGE_SIZE=12;
function workspaceVisibleIds(map){
  map.prepare();
  return map.scope.sites.filter(s=>{const p=map.project(s.lon,s.lat);return p.z>.015&&p.x>=10&&p.x<=map.w-10&&p.y>=64&&p.y<=map.h-58;}).map(s=>s.id);
}
function workspaceRecordData(scope,phase){
  const r=workspaceState.records;
  let rows=scope.sites,pending=false;
  if(r.scope==='visible'){
    const visible=globe instanceof ResearchMap&&!globe.destroyed?workspaceVisibleIds(globe):workspaceState.visibleIds;
    pending=visible===null;rows=rows.filter(s=>(visible||[]).includes(s.id));
  } else if(r.scope==='selection'){
    const selected=state.spatialCluster?.length?state.spatialCluster:[state.spatialSelected];
    rows=spatialFiltered().filter(s=>selected.includes(s.id));
  }
  rows=rows.slice().sort((a,b)=>r.sort==='power'?(spatialPower(b,phase)??-1)-(spatialPower(a,phase)??-1)||a.name.localeCompare(b.name):String(r.sort==='location'?a.location:a.name).localeCompare(String(r.sort==='location'?b.location:b.name))||a.id.localeCompare(b.id));
  const pages=Math.max(1,Math.ceil(rows.length/WORKSPACE_PAGE_SIZE));
  if(!pending)r.page=Math.min(Math.max(0,r.page),pages-1);
  return {rows,pages,pending,page:rows.slice(r.page*WORKSPACE_PAGE_SIZE,(r.page+1)*WORKSPACE_PAGE_SIZE)};
}
function workspaceRecordTable(scope,phase){
  const r=workspaceState.records,data=workspaceRecordData(scope,phase);
  return `<div class="table-wrap workspace-record-scroll"><table class="workspace-record-table"><caption class="sr-only">${esc(r.scope)} research projects, ${esc(phase)} independent IT estimates</caption><thead><tr><th scope="col">Project & location</th><th scope="col">${phase==='target'?'Target':'Snapshot'} IT estimate</th><th scope="col">Evidence</th><th scope="col">Research actions</th></tr></thead><tbody>${data.page.map(s=>`<tr data-workspace-record="${esc(s.id)}" class="${s.id===state.spatialSelected&&state.spatialSelectionActive?'selected':''}"><td><button class="workspace-record-name" data-workspace-select="${esc(s.id)}" aria-label="Select ${esc(s.name)} on the current map">${esc(s.name)}</button><small>${esc(s.location)}</small></td><td>${spatialPower(s,phase)==null?'Not quantified':fmt(spatialPower(s,phase))+' MW'}<small>${esc(s[phase]?.date||'No comparable date')} · independent estimate</small></td><td>${esc(spatialEvidenceLabel(s.review))}${srefs(s.sources)}</td><td><button data-atlas-action="campus" data-id="${esc(s.id)}">Campus →</button><button data-workspace-compare="${esc(s.id)}" aria-pressed="${saved.projectCompare.includes(s.id)}">${saved.projectCompare.includes(s.id)?'✓ Comparing':'Compare +'}</button></td></tr>`).join('')||`<tr><td colspan="4">${data.pending?'Updating visible map records…':'No records match these filters'}${r.scope==='visible'?' in the visible map. Pan the map or choose Geographic scope':r.scope==='selection'?' in the selection. Select a project or clear refinements':''}.</td></tr>`}</tbody></table></div><footer class="workspace-record-footer"><span role="status">${data.rows.length} matching projects · ${data.rows.length?r.page*WORKSPACE_PAGE_SIZE+1:0}–${Math.min((r.page+1)*WORKSPACE_PAGE_SIZE,data.rows.length)} shown</span><div><button data-workspace-page="previous" ${r.page===0?'disabled':''}>← Previous</button><span>Page ${r.page+1} of ${data.pages}</span><button data-workspace-page="next" ${r.page+1>=data.pages?'disabled':''}>Next →</button></div></footer>`;
}
atlasRecordList=function(scope,phase){
  const r=workspaceState.records;
  return `<details class="atlas-record-list workspace-records" ${r.open?'open':''}><summary><span>Map-linked research records</span><span>${scope.sites.length} in geographic scope · select without the map</span></summary><div class="workspace-record-controls"><label>Record scope <select id="workspace-record-scope"><option value="geography" ${r.scope==='geography'?'selected':''}>Geographic scope</option><option value="visible" ${r.scope==='visible'?'selected':''}>Visible map</option><option value="selection" ${r.scope==='selection'?'selected':''}>Selection</option></select></label><label>Sort <select id="workspace-record-sort"><option value="power" ${r.sort==='power'?'selected':''}>IT estimate · largest first</option><option value="name" ${r.sort==='name'?'selected':''}>Project name</option><option value="location" ${r.sort==='location'?'selected':''}>Location</option></select></label><button data-workspace-export-records>Export all matching projects ↓</button></div><div data-workspace-record-table>${workspaceRecordTable(scope,phase)}</div><p class="workspace-record-boundary">Research estimates only · dates and scopes retained · community-map locations are a separate collection. Unmapped projects remain in the <button data-action="nav" data-id="facilities">facility directory →</button>.</p></details>`;
};
function workspaceRefreshRecords(){
  const panel=document.querySelector('[data-workspace-record-table]');if(!panel)return;
  panel.innerHTML=workspaceRecordTable(spatialScope(state.spatialLevel,spatialDefaultSite()),state.spatialPhase);
}
function workspaceCurrentCamera(){
  const key=researchCameraKey(state.spatialLevel,spatialScope(state.spatialLevel,spatialDefaultSite()));
  if(globe instanceof ResearchMap&&!globe.destroyed&&globe.cameraKey===key)return globe.snapshot();
  return state.spatialRouteCamera||state.spatialCamera?.[key];
}
function workspaceCameraParam(camera){
  if(!camera)return '';
  const values=camera.flat?['m',...camera.bounds,camera.zoom]:['g',camera.lat,((camera.lon+540)%360)-180,camera.zoom];
  return values.map(v=>typeof v==='number'?Number(v.toFixed(5)):v).join(',');
}
function workspaceParseCamera(value){
  if(!value)return null;
  const [type,...raw]=value.split(','),n=raw.map(Number);
  if(raw.some(x=>x.trim()==='')||n.some(x=>!Number.isFinite(x)))return null;
  if(type==='g'&&n.length===3&&Math.abs(n[0])<=85&&Math.abs(n[1])<=180&&n[2]>=.6&&n[2]<=12)return {flat:false,lat:n[0],lon:n[1],zoom:n[2],bounds:[-180,-60,180,80]};
  if(type==='m'&&n.length===5&&Math.abs(n[0])<=1080&&Math.abs(n[2])<=1080&&n[2]>n[0]&&n[2]-n[0]<=720&&n[1]>=-83&&n[3]<=83&&n[3]>n[1]&&n[4]>=.6&&n[4]<=12)return {flat:true,lat:(n[1]+n[3])/2,lon:(n[0]+n[2])/2,zoom:n[4],bounds:n.slice(0,4)};
  return null;
}
function workspaceSyncURL(){
  if(['overview','globe'].includes(state.view)&&document.querySelector('#drawer')?.hidden)history.replaceState(null,'',spatialURL());
}
let workspaceCameraTimer;
document.addEventListener('atlas-camera-change',event=>{
  const map=event.detail,route=location.hash;clearTimeout(workspaceCameraTimer);
  workspaceCameraTimer=setTimeout(()=>{
    if(map.destroyed||globe!==map||location.hash!==route)return;
    state.spatialCamera||={};state.spatialCamera[map.cameraKey]=map.snapshot();
    workspaceState.visibleIds=workspaceVisibleIds(map);
    if(workspaceState.records.scope==='visible'&&workspaceState.records.open){if(map.workspacePublished)workspaceState.records.page=0;workspaceRefreshRecords();}map.workspacePublished=true;
    workspaceSyncURL();
  },220);
});
function workspaceShareContent(){return `<h1>Share this view.</h1><p>The link retains the map, selected project, refinements, layers and research topic. Private notes, shelf and comparison storage stay in your browser.</p><label for="workspace-share-url">View link</label><input id="workspace-share-url" type="text" readonly value="${esc(workspaceState.shareURL)}"><button class="btn primary" data-workspace-copy-link>Copy link</button><p class="workspace-share-status" role="status">You can also select and copy the link above.</p>`;}
const workspaceOriginalTransition=spatialTransition;
spatialTransition=function(update={}){
  workspaceState.records.page=0;
  if(Number(update.level)===0)state.spatialRegion=null;
  if(Number(update.level)>=4)state.spatialCluster=[];
  if(update.selected){workspaceState.mobileExpanded=false;workspaceState.visibleIds=null;}
  workspaceOriginalTransition(update);
  if(update.selected&&matchMedia('(max-width:640px)').matches)document.querySelector('[data-workspace-inspector]')?.focus({preventScroll:true});
};
document.addEventListener('input',event=>{if(event.target.id==='workspace-compare-query'){workspaceState.compareQuery=event.target.value;document.getElementById('workspace-compare-results').innerHTML=workspaceCompareResults();}});
document.addEventListener('change',event=>{
  if(event.target.hasAttribute('data-workspace-compare-notes'))workspaceState.compareNotes=event.target.checked;
  if(event.target.id==='workspace-record-scope'){workspaceState.records.scope=event.target.value;workspaceState.records.page=0;workspaceRefreshRecords();workspaceSyncURL();}
  if(event.target.id==='workspace-record-sort'){workspaceState.records.sort=event.target.value;workspaceState.records.page=0;workspaceRefreshRecords();workspaceSyncURL();}
});
document.addEventListener('toggle',event=>{
  if(!event.target.matches?.('.workspace-records'))return;
  workspaceState.records.open=event.target.open;if(event.target.open)workspaceRefreshRecords();workspaceSyncURL();
},true);
document.addEventListener('click',async event=>{
  const inspector=event.target.closest('[data-workspace-inspector]');
  if(inspector){workspaceState.mobileExpanded=!workspaceState.mobileExpanded;inspector.closest('aside').dataset.expanded=String(workspaceState.mobileExpanded);inspector.setAttribute('aria-expanded',String(workspaceState.mobileExpanded));inspector.querySelector('.workspace-mobile-expand').textContent=workspaceState.mobileExpanded?'Close ↑':'Inspect ↓';}
  const pager=event.target.closest('[data-workspace-page]');
  if(pager){workspaceState.records.page+=pager.dataset.workspacePage==='next'?1:-1;workspaceRefreshRecords();workspaceSyncURL();const next=document.querySelector(`[data-workspace-page="${pager.dataset.workspacePage}"]:not(:disabled)`);(next||document.querySelector('.workspace-records summary'))?.focus({preventScroll:true});}
  if(event.target.closest('[data-workspace-export-records]')){
    const phase=state.spatialPhase,scope=spatialScope(state.spatialLevel,spatialDefaultSite()),rows=workspaceRecordData(scope,phase).rows;
    download('compute-atlas-map-records.json',{published_at:ATLAS_PRIMARY.published_at,collection:'Named research projects; community-map locations excluded',record_scope:workspaceState.records.scope,geographic_scope:scope.label,estimate_layer:phase,policy:'Independent, mixed-vintage scopes are not additive. Unquantified is not zero.',projects:rows.map(s=>{const {private_note,...dossier}=atlasCitedDossier(s);return dossier;})});
  }
  if(event.target.closest('[data-workspace-share]')){workspaceSyncURL();workspaceState.shareURL=new URL(spatialURL(),location.href).href;openDrawer('workspace-share');}
  if(event.target.closest('[data-workspace-copy-link]')){
    const input=document.querySelector('#workspace-share-url'),status=document.querySelector('.workspace-share-status');
    try{await navigator.clipboard.writeText(input.value);status.textContent='View link copied.';}catch(_){input.focus();input.select();status.textContent='Link selected. Copy it with your browser or keyboard.';}
  }
  const layers=event.target.closest('[data-atlas-action="labels"],[data-atlas-action="fly"]');if(layers)workspaceSyncURL();
  
});
document.addEventListener('keydown',event=>{if(event.key==='Escape')workspaceState.escapeFromOverlay=!document.querySelector('#drawer')?.hidden||!document.querySelector('#search-modal')?.hidden;},true);
document.addEventListener('keydown',event=>{
  if(workspaceState.escapeFromOverlay||event.key!=='Escape'||!matchMedia('(max-width:640px)').matches||!workspaceState.mobileExpanded||!document.querySelector('#drawer')?.hidden||!document.querySelector('#search-modal')?.hidden)return;
  const button=document.querySelector('[data-workspace-inspector]');if(button){event.preventDefault();button.click();button.focus({preventScroll:true});}
});

// Project selection is explicit, source-backed and inspectable on the same screen.
document.addEventListener('click',event=>{
  const favorite=event.target.closest('.atlas-intro [data-action="favorite"]');if(favorite)favorite.textContent=saved.favorites.includes(favorite.dataset.id)?'★ On research shelf':'Add to research shelf +';
  const topic=event.target.closest('[data-workspace-topic]');
  if(topic){workspaceState.tab=topic.dataset.workspaceTopic;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-workspace-topic="${workspaceState.tab}"]`)?.focus({preventScroll:true});}
  const selection=event.target.closest('[data-workspace-select]');
  if(selection){state.spatialCluster=[];spatialTransition({selected:selection.dataset.workspaceSelect});}
  if(event.target.closest('[data-workspace-enter]'))spatialTransition({level:Math.min(4,state.spatialLevel+1)});
  const clear=event.target.closest('[data-workspace-clear]');
  if(clear){const key=clear.dataset.workspaceClear;if(key==='region')state.spatialRegion=null;else if(key==='evidence')state.spatialEvidence='all';else state.filter[key]=key==='q'?'':'all';state.spatialFiltersOpen=false;spatialTransition({replace:true,...(key==='region'?{level:0}:{})});}
  const addCompare=event.target.closest('[data-workspace-add-compare]');
  if(addCompare&&!addCompare.disabled&&site(addCompare.dataset.workspaceAddCompare)&&saved.projectCompare.length<3){saved.projectCompare.push(addCompare.dataset.workspaceAddCompare);save();workspaceRefreshComparison();}
  const compare=event.target.closest('[data-workspace-compare]');
  if(compare){const id=compare.dataset.workspaceCompare;if(!site(id))return;if(saved.projectCompare.includes(id))saved.projectCompare=saved.projectCompare.filter(x=>x!==id);else if(saved.projectCompare.length<3)saved.projectCompare.push(id);else{toast('Compare up to three projects. Remove one to add another.');workspaceCompareDrawer();return;}save();compare.textContent=saved.projectCompare.includes(id)?'✓ Comparing':'Compare +';compare.setAttribute('aria-pressed',String(saved.projectCompare.includes(id)));toast(saved.projectCompare.length+' projects in comparison');}
  if(event.target.closest('[data-workspace-open-compare]'))workspaceCompareDrawer();
  const remove=event.target.closest('[data-workspace-remove-compare]');if(remove){saved.projectCompare=saved.projectCompare.filter(x=>x!==remove.dataset.workspaceRemoveCompare);save();workspaceRefreshComparison();}
  if(event.target.closest('[data-workspace-export-compare]'))download('compute-atlas-project-comparison.json',{published_at:ATLAS_PRIMARY.published_at,policy:'Different dated scopes are not additive. Partial research, not complete fleets.',private_notes_included:Boolean(workspaceState.compareNotes),projects:saved.projectCompare.map(site).filter(Boolean).map(s=>{const dossier=atlasCitedDossier(s);if(!workspaceState.compareNotes)delete dossier.private_note;return dossier;})});
  const phase=event.target.closest('[data-workspace-phase]');
  if(phase){const s=site(phase.dataset.site);if(!s||!workspacePhases(s).some(r=>r.id===phase.dataset.workspacePhase))return;workspaceState.phaseBySite.set(s.id,phase.dataset.workspacePhase);state.spatialLevel=5;history.pushState(null,'',spatialURL());render();document.querySelector(`[data-workspace-phase="${CSS.escape(phase.dataset.workspacePhase)}"]`)?.focus({preventScroll:true});}
  const location=event.target.closest('[data-workspace-location]');if(location){workspaceState.location=location.dataset.workspaceLocation==='true';render();document.querySelector(`[data-workspace-location="${workspaceState.location}"]`)?.focus({preventScroll:true});workspaceSyncURL();}
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
  const primary=['overview','inventory','companies','contracts','investment','reports'];
  const navButton=([id,label])=>`<button class="nav-button ${state.view===id?'active':''}" data-action="nav" data-id="${id}">${icon(id==='inventory'?'facilities':id)}${id==='reports'?'Research library':label}</button>`;
  $('#navigation').innerHTML=primary.map(id=>NAV.find(([key])=>key===id)).filter(Boolean).map(navButton).join('')+`<details class="workspace-nav-more" ${primary.includes(state.view)?'':'open'}><summary>More research tools</summary>${NAV.filter(([id])=>!primary.includes(id)).map(navButton).join('')}</details>`;
  if(['overview','globe'].includes(state.view)){
    const s=spatialDefaultSite(),level=state.spatialLevel,scope=spatialScope(level,s);
    const parts=['The landscape'];if(level>=1)parts.push(spatialScope(1,s).label);if(level>=2)parts.push(spatialScope(2,s).label);if(level>=3)parts.push(spatialScope(3,s).label);if(level>=4&&s)parts.push(s.name);if(level===5&&s)parts.push(workspaceSelected(s)?.scope||'Evidence detail');
    $('#breadcrumb').textContent=parts.join(' › ');
  }
};
// Reading a source must preserve the campus/topic/phase return point.
const workspaceOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts={}){
  if(!state.drawer&&['overview','globe'].includes(state.view))workspaceState.drawerRoute=spatialURL();
  const map=globe instanceof ResearchMap?globe:null,camera=map?.snapshot();
  workspaceOpenDrawer(kind,id,opts);
  // Reading a dossier must not run the legacy locate animation behind its drawer.
  if(kind==='site'&&map===globe&&camera){Object.assign(map,camera);map.target=null;map.dirty=true;}
  if(kind==='project-comparison'){$('#drawer-type').textContent='PROJECT COMPARISON';$('#drawer-content').innerHTML=workspaceCompareContent();}if(kind==='workspace-share'){$('#drawer-type').textContent='SHARE EXPLORATION';$('#drawer-content').innerHTML=workspaceShareContent();}};
ATLAS.openDrawer=openDrawer;
const workspaceCloseDrawer=closeDrawer;
closeDrawer=function(){const wasOpen=!$('#drawer').hidden,returnRoute=workspaceState.drawerRoute;workspaceCloseDrawer();if(wasOpen){workspaceState.drawerRoute=null;if(['overview','globe'].includes(state.view))history.replaceState(null,'',returnRoute||spatialURL());}};
// Phase inspection survives sharing and reload without changing the research ledger.
const workspaceSpatialURL=spatialURL;
spatialURL=function(view=state.view){
  const url=workspaceSpatialURL(view);if(!['overview','globe'].includes(view))return url;
  const p=new URLSearchParams(url.split('?')[1]||''),s=site(state.spatialSelected),id=s&&workspaceState.phaseBySite.get(s.id),r=workspaceState.records;
  if(WORKSPACE_REGIONS.includes(state.spatialRegion))p.set('region',state.spatialRegion);
  if(id)p.set('claim',id);if(workspaceState.tab!=='overview')p.set('topic',workspaceState.tab);
  const camera=workspaceCameraParam(workspaceCurrentCamera());if(camera)p.set('camera',camera);
  if(state.spatialLabels===false)p.set('labels','0');if(state.spatialRoads===false)p.set('roads','0');
  if(state.spatialFly&&state.spatialFly!=='all')p.set('preset',state.spatialFly);
  const members=(state.spatialCluster||[]).filter(id=>site(id));if(members.length>1)p.set('members',members.join(','));
  if(workspaceState.location)p.set('mapview','location');
  if(r.scope!=='geography')p.set('records',r.scope);if(r.sort!=='power')p.set('sort',r.sort);if(r.open)p.set('recordsopen','1');if(r.page)p.set('page',String(r.page+1));
  return '#'+view+'?'+p.toString();
};
const workspaceRoute=routeFromHash;window.removeEventListener('hashchange',workspaceRoute);
routeFromHash=function(){if(window.ATLAS_BOOTSTRAPPING)return;
  const [path,query='']=location.hash.slice(1).split('?'),p=new URLSearchParams(query),s=site(p.get('site'));
  workspaceState.tab=WORKSPACE_TOPICS.some(([id])=>id===p.get('topic'))?p.get('topic'):'overview';
  if(s){if(workspacePhases(s).some(r=>r.id===p.get('claim')))workspaceState.phaseBySite.set(s.id,p.get('claim'));else workspaceState.phaseBySite.delete(s.id);}
  if(['','overview','globe'].includes(path)){
    if(globe instanceof ResearchMap)globe.skipCameraSave=true;
    state.spatialRegion=WORKSPACE_REGIONS.includes(p.get('region'))?p.get('region'):null;
    state.spatialCamera={};state.spatialRouteCamera=workspaceParseCamera(p.get('camera'));
    state.spatialLabels=p.get('labels')!=='0';state.spatialRoads=p.get('roads')!=='0';
    state.spatialFly=['americas','europe','asia','middle-east','custom'].includes(p.get('preset'))?p.get('preset'):'all';
    workspaceState.location=p.get('mapview')==='location';workspaceState.mobileExpanded=false;workspaceState.visibleIds=null;
    const r=workspaceState.records;r.scope=['visible','selection'].includes(p.get('records'))?p.get('records'):'geography';r.sort=['name','location'].includes(p.get('sort'))?p.get('sort'):'power';r.open=p.get('recordsopen')==='1';r.page=Math.max(0,Math.min(999,(Number.parseInt(p.get('page'),10)||1)-1));
  }
  workspaceRoute();
};window.addEventListener('hashchange',routeFromHash);
// Preserve existing explicit catalog links. A fresh visit opens the approved landscape.
if(!ATLAS_ENTRY_HASH){state.spatialLevel=0;state.view='overview';if(location.protocol!=='about:')history.replaceState(null,'',spatialURL('overview'));render();}else routeFromHash();
ATLAS.workspace={phases:workspacePhases,selected:workspaceSelected,state:workspaceState,compare:()=>saved.projectCompare,compareDrawer:workspaceCompareDrawer,records:workspaceRecordData,parseCamera:workspaceParseCamera};
// The final campus integration marks the complete workspace ready.
