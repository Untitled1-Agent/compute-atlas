'use strict';
/* The reviewed publication owns claims. Categories organize evidence, not scores. */
const ATLAS_RESEARCH_TOPICS = [
  ['identity','Identity & location'], ['technical','Technical design'],
  ['energy','Power & energy'], ['development','Development & milestones'],
  ['commercial','Commercial relationships'], ['finance','Investment & financing']
];
const atlasResearchState = {query:'',outcome:'all',offset:0};
const atlasResearchReview = s => ATLAS_PRIMARY.research_coverage?.projects?.find(p=>p.site_id===s?.id);
function atlasResearchTopic(row) {
  if (ATLAS_RESEARCH_TOPICS.some(([id])=>id===row.topic)) return row.topic;
  if (row.identity) return 'identity';
  if (row.kind==='relationships') return 'commercial';
  const text=[row.metric,row.boundary,row.label,row.scope].join(' ').toLowerCase();
  if (/lease.value|investment|cost|financ|capex/.test(text)) return 'finance';
  if (/commission|commence|opening|deliver|construction|expansion|date/.test(text)) return 'development';
  if (/power|energy|pue|generation|utility/.test(text)) return 'energy';
  if (/location|address|identity|land|site.area/.test(text)) return 'identity';
  return 'technical';
}
function atlasResearchRows(s, context=false) {
  return atlasEvidenceRows(s).filter(r=>r.effective && (context ? primaryIsContext(r) : !primaryIsContext(r)));
}
function atlasResearchProfile(s) {
  const rows=atlasResearchRows(s),context=atlasResearchRows(s,true),review=atlasResearchReview(s);
  const sources=[...new Set([...rows,...context].map(r=>r.source_id))].map(primarySource).filter(Boolean);
  return {site:s,rows,context,review,sources,publishers:[...new Set(sources.map(r=>r.publisher))],
    topics:ATLAS_RESEARCH_TOPICS.map(([id,label])=>({id,label,rows:rows.filter(r=>atlasResearchTopic(r)===id)}))};
}
function atlasResearchClaim(row) {
  const value=row.kind==='observations' ? observationValue(row)+(row.value===null?'':' '+esc(row.unit))
    : esc(row.kind==='relationships' ? company(row.company_id)?.name || row.company_id : row.value);
  const label=row.label || row.role || boundaryLabel(row.boundary);
  return `<article class="atlas-research-claim" data-research-claim="${esc(row.id)}"><header><b>${esc(label)}</b>${primaryRef(row.source_id)}</header><p class="atlas-research-value">${value}</p><div class="atlas-research-meta"><span>${esc(row.as_of||'Publication date not stated')}</span><span>${esc(row.scope||label)}</span>${row.status?`<span>${esc(statusLabel(row.status))}</span>`:''}</div>${row.qualifier?`<p class="atlas-research-qualification">${esc(row.qualifier)}</p>`:''}${row.source_locator?`<details class="atlas-research-locator"><summary>Find this claim in the source</summary><p>${esc(row.source_locator)}</p></details>`:''}</article>`;
}
function atlasResearchPanel(s) {
  if (!s) return '';
  const p=atlasResearchProfile(s),review=p.review;
  return `<section class="atlas-project-research" data-project-research="${esc(s.id)}"><header class="atlas-research-heading"><div><div class="atlas-eyebrow">PROJECT RESEARCH / CITED DISCLOSURES</div><h2>Inside ${esc(s.name)}.</h2><p>${p.rows.length} project claims · ${p.context.length} contextual claims · ${p.sources.length} sources · ${p.publishers.length} publishers</p></div><button class="btn" data-research-index>Explore all project research ↗</button></header>${review?`<div class="atlas-research-identity ${review.outcome==='unresolved'?'unresolved':''}"><b>${review.outcome==='unresolved'?'Identity needs resolution':review.outcome==='partial'?'Partial identity or evidence':'Research identity and boundaries'}</b><p>${esc(review.identity_note)}</p><small>Reviewed ${esc(ATLAS_PRIMARY.research_coverage.reviewed_at)}</small></div>`:''}<div class="atlas-research-topic-grid">${p.topics.map(topic=>`<section class="atlas-research-topic" data-research-topic="${topic.id}"><header><h3>${topic.label}</h3><span>${topic.rows.length} ${topic.rows.length===1?'claim':'claims'}</span></header>${topic.rows.length?topic.rows.slice(0,2).map(atlasResearchClaim).join('')+ (topic.rows.length>2?`<details class="atlas-research-more"><summary>Read ${topic.rows.length-2} more claims</summary>${topic.rows.slice(2).map(atlasResearchClaim).join('')}</details>`:''):'<p class="atlas-research-missing">No project-specific primary claim in this category.</p>'}</section>`).join('')}</div>${p.context.length?`<details class="atlas-research-context"><summary>Wider context and unresolved associations · ${p.context.length} claims</summary><p>These sources describe a wider area, portfolio, or project whose match to the archived name needs review. Their values do not establish this project’s capacity.</p>${p.context.map(atlasResearchClaim).join('')}</details>`:''}${review?.gaps?.length?`<div class="atlas-research-gaps"><h3>Open research questions</h3><ul>${review.gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul></div>`:''}<footer><span>Source reporting dates remain separate from this research review.</span><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">All claims & earlier revisions ↗</button><button class="text-button" data-atlas-action="export" data-id="${esc(s.id)}">Export cited dossier ↓</button></footer></section>`;
}
function atlasResearchProfiles() {
  const q=atlasResearchState.query.trim().toLocaleLowerCase();
  return D.sites.map(atlasResearchProfile).filter(p=>(atlasResearchState.outcome==='all'||p.review?.outcome===atlasResearchState.outcome)
    && (!q || [p.site.name,p.site.location,p.site.owner_label,p.review?.identity_note,...(p.review?.gaps||[]),
      ...p.sources.map(r=>r.publisher+' '+r.title),...p.rows.map(r=>[r.label,r.value,r.scope,r.qualifier].join(' ')),
      ...p.context.map(r=>[r.label,r.value,r.scope,r.qualifier].join(' '))].join(' ').toLocaleLowerCase().includes(q)))
    .sort((a,b)=>a.site.name.localeCompare(b.site.name)||a.site.id.localeCompare(b.site.id));
}
function atlasResearchIndexResults() {
  if (state.drawer?.kind!=='research-index') return;
  const all=atlasResearchProfiles(),st=atlasResearchState;
  st.offset=Math.min(st.offset,Math.max(0,Math.ceil(all.length/15)-1)*15);
  $('#atlas-research-count').textContent=`${all.length} matching projects · categories count project claims, not completeness`;
  $('#atlas-research-projects').innerHTML=all.slice(st.offset,st.offset+15).map(p=>`<article class="atlas-research-project" data-research-project="${esc(p.site.id)}"><header><button data-research-site="${esc(p.site.id)}"><h3>${esc(p.site.name)}</h3><span>${esc(p.site.owner_label)} · ${esc(p.site.location)} ↗</span></button><span class="atlas-research-outcome">${esc(({enriched:'Enriched',partial:'Partial',unresolved:'Identity unresolved'})[p.review?.outcome]||'Not yet researched')}</span></header><p>${p.rows.length} project claims · ${p.context.length} context · ${p.sources.length} sources / ${p.publishers.length} publishers</p><div class="atlas-research-fields">${p.topics.map(t=>`<span class="${t.rows.length?'present':'absent'}" title="${esc(t.label)}: ${t.rows.length} project-specific claims">${t.label}<b>${t.rows.length||'—'}</b></span>`).join('')}</div>${p.review?.identity_note?`<p class="atlas-research-index-note">${esc(p.review.identity_note)}</p>`:''}</article>`).join('') || '<p>No matching research project. Missing evidence does not mean zero capacity.</p>';
  $('#atlas-research-pages').innerHTML=`<button class="btn small" data-research-page="previous" ${st.offset===0?'disabled':''}>← Previous</button><span>${all.length?st.offset+1:0}–${Math.min(st.offset+15,all.length)} / ${all.length}</span><button class="btn small" data-research-page="next" ${st.offset+15>=all.length?'disabled':''}>Next →</button>`;
}
function atlasResearchIndex() {
  const profiles=D.sites.map(atlasResearchProfile),covered=profiles.filter(p=>p.rows.length).length;
  const searched=ATLAS_PRIMARY.research_coverage?.projects.length||0;
  $('#drawer-type').textContent='PROJECT RESEARCH / COVERAGE & OPEN QUESTIONS';
  $('#drawer-content').innerHTML=`<section class="atlas-research-index"><div class="atlas-eyebrow">FACILITY DOSSIERS</div><h1>Every project.<br><span>Follow the evidence.</span></h1><p>${searched} projects investigated · ${covered} with project-specific primary claims · ${profiles.filter(p=>p.review?.outcome==='unresolved').length} identities unresolved. Research reviewed ${esc(ATLAS_PRIMARY.research_coverage?.reviewed_at||ATLAS_PRIMARY.published_at)}.</p><p>Read technical design, power, development, commercial relationships and financing together. Empty categories remain open questions. A dated announcement does not prove today’s operating status.</p><div class="atlas-research-controls"><label>Search projects and their evidence<input type="search" id="atlas-research-query" value="${esc(atlasResearchState.query)}" placeholder="Cooling, utility, address, partner…" autocomplete="off"></label><label>Research outcome<select id="atlas-research-outcome">${[['all','All projects'],['enriched','Enriched'],['partial','Partial'],['unresolved','Identity unresolved']].map(([id,label])=>`<option value="${id}" ${atlasResearchState.outcome===id?'selected':''}>${label}</option>`).join('')}</select></label></div><p id="atlas-research-count" role="status"></p><div id="atlas-research-projects"></div><nav id="atlas-research-pages" aria-label="Project research pages"></nav></section>`;
  atlasResearchIndexResults();
  $('#drawer-content').insertAdjacentHTML('afterbegin','<section id="atlas-research-publication-notice" class="atlas-research-update" aria-label="Reviewed publication update" hidden></section>');
  atlasPublicationNotice();
}

const atlasResearchPreviousNotice=atlasPublicationNotice;
atlasPublicationNotice=function() {
  atlasResearchPreviousNotice();
  const notice=$('#atlas-research-publication-notice');
  if (!notice) return;
  notice.hidden=!atlasPublicationPending&&!atlasPublicationError;
  notice.innerHTML=atlasPublicationPending ? `<p>A reviewed update dated ${esc(atlasPublicationPending.published_at)} is available. Your current research stays unchanged until you apply it.</p><button class="btn" data-service-publication="apply">Apply reviewed update ↻</button>`
    : atlasPublicationError ? '<p>The publication check is unavailable. Your loaded research remains available.</p><button class="btn" data-service-publication="check">Retry publication check ↻</button>' : '';
};

// Campus and deep-linked site dossiers expose the same reviewed evidence.
const atlasResearchPreviousView=sixScaleGlobeView;
sixScaleGlobeView=function() {
  const html=atlasResearchPreviousView(),s=site(state.spatialSelected);
  return state.spatialLevel>=4&&s ? html.replace('<div class="atlas-bottom-evidence">',atlasResearchPanel(s)+'<div class="atlas-bottom-evidence">') : html;
};
globeView=sixScaleGlobeView;
const atlasResearchPreviousDossier=siteDossier;
siteDossier=function(s) {
  if (!s) return atlasResearchPreviousDossier(s);
  return atlasResearchPreviousDossier(s).replace('<div class="metric-grid">',atlasResearchPanel(s)+'<h2>Historical models & original research</h2><div class="metric-grid">');
};
const atlasResearchPreviousDrawer=openDrawer;
openDrawer=function(kind,id,options={}) {
  atlasResearchPreviousDrawer(kind,id,options);
  if (kind==='research-index') atlasResearchIndex();
  if (kind==='primary-source') {
    const claims=ATLAS_EVIDENCE_KINDS.slice(0,2).flatMap(type=>(ATLAS_PRIMARY[type]||[])
      .filter(row=>row.source_id===id).map(row=>({...row,kind:type})));
    $('#drawer-content').querySelectorAll('.atlas-source-observation').forEach((element,i)=>{
      const row=claims[i];
      if (row) element.innerHTML=`<h3>${esc(site(row.site_id)?.name||row.site_id)}</h3>${primaryIsContext(row)?'<p class="atlas-source-context-label">Wider context / not a project total</p>':''}${atlasResearchClaim(row)}`;
    });
  }
};
ATLAS.openDrawer=openDrawer;
const atlasResearchPreviousExport=atlasCitedDossier;
atlasCitedDossier=function(s) {
  const p=atlasResearchProfile(s);
  return {...atlasResearchPreviousExport(s),research_review:p.review||null,
    research_reviewed_at:ATLAS_PRIMARY.research_coverage?.reviewed_at||null,
    project_claim_ids:p.rows.map(r=>r.id),contextual_claim_ids:p.context.map(r=>r.id),
    topic_claim_ids:Object.fromEntries(p.topics.map(t=>[t.id,t.rows.map(r=>r.id)]))};
};
ATLAS.evidence.export=atlasCitedDossier;
const atlasResearchPreviousPower=primaryPowerRows;
primaryPowerRows=function(s){return atlasResearchPreviousPower(s).filter(r=>!primaryIsContext(r));};
function atlasResearchMatches(s,q) {
  return [s.name,s.location,s.owner_label,JSON.stringify(s.hardware),JSON.stringify(s.facts),
    ...atlasEvidenceRows(s).filter(r=>r.effective).map(r=>[r.label,r.value,r.role,r.scope,r.qualifier,primarySource(r.source_id)?.publisher].join(' '))]
    .join(' ').toLocaleLowerCase().includes(q.trim().toLocaleLowerCase());
}
function atlasResearchFilter(previous) {
  return function(...args) {
    const query=state.filter.q;
    if (!query) return previous(...args);
    try {state.filter.q='';return previous(...args).filter(s=>atlasResearchMatches(s,query));}
    finally {state.filter.q=query;}
  };
}
filteredSites=atlasResearchFilter(filteredSites);
spatialFiltered=atlasResearchFilter(spatialFiltered);
const atlasResearchPreviousSearch=searchAll;
searchAll=function(q) {
  atlasResearchPreviousSearch(q);
  if (!q.trim()) return;
  const rows=D.sites.filter(s=>atlasResearchRows(s).concat(atlasResearchRows(s,true)).some(r=>
    [r.label,r.value,r.scope,r.qualifier,primarySource(r.source_id)?.publisher].join(' ').toLocaleLowerCase().includes(q.trim().toLocaleLowerCase())));
  if (rows.length) $('#search-results').insertAdjacentHTML('afterbegin',`<div class="command-hint">Project research · ${rows.length} matching dossiers</div>`+rows.slice(0,6).map(s=>`<button class="search-result" data-research-site="${esc(s.id)}"><span class="result-type">PROJECT EVIDENCE</span><span><b>${esc(s.name)}</b><small>${esc(s.location)} · cited project research</small></span></button>`).join(''));
};
document.addEventListener('click',event=>{
  if (event.target.closest('[data-research-index]')) openDrawer('research-index','projects');
  const selected=event.target.closest('[data-research-site]');
  if (selected) {if(!$('#search-modal').hidden)closeSearch();openDrawer('site',selected.dataset.researchSite);}
  const pager=event.target.closest('[data-research-page]');
  if (pager) {atlasResearchState.offset+=pager.dataset.researchPage==='next'?15:-15;atlasResearchIndexResults();const button=$(`[data-research-page="${pager.dataset.researchPage}"]:not(:disabled)`)||$('[data-research-page]:not(:disabled)');button?.focus({preventScroll:true});}
});
document.addEventListener('input',event=>{
  if (event.target.id==='atlas-research-query') {atlasResearchState.query=event.target.value;atlasResearchState.offset=0;atlasResearchIndexResults();}
});
document.addEventListener('change',event=>{
  if (event.target.id==='atlas-research-outcome') {atlasResearchState.outcome=event.target.value;atlasResearchState.offset=0;atlasResearchIndexResults();}
});
ATLAS.research={open:()=>openDrawer('research-index','projects'),profile:atlasResearchProfile,rows:atlasResearchProfiles};
if (['overview','globe'].includes(state.view)) render();
if (state.drawer?.kind==='site') openDrawer('site',state.drawer.id,{back:true});
document.documentElement.classList.add('research-ready');
