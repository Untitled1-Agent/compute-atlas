'use strict';
/* The reviewed publication owns claims. Categories organize evidence, not scores. */
const ATLAS_RESEARCH_TOPICS = [
  ['identity','Identity & location'], ['technical','Technical design'],
  ['energy','Power & energy'], ['development','Development & milestones'],
  ['commercial','Commercial relationships'], ['finance','Investment & financing']
];
const atlasResearchState = {query:'',outcome:'all',topic:'all',country:'all',operator:'all',sort:'name',offset:0};
const atlasResearchQueries = new Map();
let atlasResearchCache = {inputs:[],profiles:new Map()};
const atlasResearchReview = s => ATLAS_PRIMARY.research_coverage?.projects?.find(p=>p.site_id===s?.id);
const atlasResearchDateOrder = (a,b) => String(b.as_of||'').localeCompare(String(a.as_of||'')) || a.id.localeCompare(b.id);
const atlasResearchLabel = row => row.label || row.role || boundaryLabel(row.boundary);
function atlasResearchPlainValue(row) {
  return row.kind==='observations' ? observationValue(row).replaceAll('&gt;','>').replaceAll('&lt;','<')+(row.value===null?'':' '+row.unit)
    : String((row.kind==='relationships' ? company(row.company_id)?.name || row.company_id : row.value)??'');
}
const atlasResearchValue = row => esc(atlasResearchPlainValue(row));
function atlasResearchText(row) {
  const source=primarySource(row.source_id);
  return [atlasResearchLabel(row),row.value,atlasResearchPlainValue(row),row.unit,row.scope,row.qualifier,row.source_locator,
    row.as_of,row.period,row.id,row.source_id,source?.title,source?.publisher,
    row.kind==='relationships'?company(row.company_id)?.name:''].filter(v=>v!=null).join(' ');
}
// Escape each text segment before inserting the literal search term as markup.
function atlasResearchHighlight(value,query) {
  const text=String(value??''),q=query.trim().toLocaleLowerCase();
  if (!q) return esc(text);
  const lower=text.toLocaleLowerCase();let result='',start=0,index=lower.indexOf(q);
  while(index!==-1) {
    result+=esc(text.slice(start,index))+'<mark>'+esc(text.slice(index,index+q.length))+'</mark>';
    start=index+q.length;index=lower.indexOf(q,start);
  }
  return result+esc(text.slice(start));
}
function atlasResearchTopic(row) {
  if (ATLAS_RESEARCH_TOPICS.some(([id])=>id===row.topic)) return row.topic;
  if (row.identity) return 'identity';
  if (row.kind==='relationships') return 'commercial';
  const text=[row.metric,row.boundary,row.label,row.scope].join(' ').toLowerCase();
  if (/lease.value|investment|cost|financ|capex/.test(text)) return 'finance';
  if (/commission|commence|opening|deliver|construction|expansion|schedule|milestone|date/.test(text)) return 'development';
  if (/power|energy|pue|generation|utility/.test(text)) return 'energy';
  if (/location|address|identity|land|site.area/.test(text)) return 'identity';
  return 'technical';
}
function atlasResearchRows(s, context=false) {
  const p=atlasResearchProfile(s);
  return context?p.context:p.rows;
}
function atlasResearchProfile(s) {
  // Applying a reviewed publication replaces these inputs together. Rebuild once
  // per publication, rather than following every revision chain for each keypress.
  const inputs=[ATLAS_PRIMARY.observations,ATLAS_PRIMARY.facts,ATLAS_PRIMARY.relationships,
    ATLAS_PRIMARY.sources,ATLAS_PRIMARY.revision_history,ATLAS_PRIMARY.research_coverage];
  if (inputs.some((value,i)=>value!==atlasResearchCache.inputs[i])) {
    const bySite=new Map(),sourcesById=new Map(ATLAS_PRIMARY.sources.map(r=>[r.id,r]));
    for(const kind of ATLAS_EVIDENCE_KINDS) for(const row of effectivePrimary(ATLAS_PRIMARY[kind]||[])) {
      if (!bySite.has(row.site_id)) bySite.set(row.site_id,[]);
      bySite.get(row.site_id).push({...row,kind,effective:true});
    }
    const profiles=new Map();
    for(const item of D.sites) {
      const all=(bySite.get(item.id)||[]).sort(atlasResearchDateOrder);
      const rows=all.filter(r=>!primaryIsContext(r)),context=all.filter(r=>primaryIsContext(r));
      const sources=[...new Set(all.map(r=>r.source_id))].map(id=>sourcesById.get(id)).filter(Boolean);
      const topics=ATLAS_RESEARCH_TOPICS.map(([id,label])=>({id,label,rows:rows.filter(r=>atlasResearchTopic(r)===id)}));
      profiles.set(item.id,{site:item,rows,context,review:atlasResearchReview(item),sources,
        publishers:[...new Set(sources.map(r=>r.publisher))],topics,
        latest:rows.find(r=>r.as_of)?.as_of||null,
        searchRows:all.map(row=>({row,text:atlasResearchText(row).toLocaleLowerCase()}))});
    }
    atlasResearchCache={inputs,profiles};
  }
  return atlasResearchCache.profiles.get(s?.id)||{site:s,rows:[],context:[],sources:[],publishers:[],topics:[],latest:null,searchRows:[]};
}
function atlasResearchClaim(row) {
  const label=atlasResearchLabel(row);
  return `<article class="atlas-research-claim" data-research-claim="${esc(row.id)}" tabindex="-1"><header><b>${esc(label)}</b>${primaryRef(row.source_id)}</header><p class="atlas-research-value">${atlasResearchValue(row)}</p><div class="atlas-research-meta"><span>${esc(row.as_of||'Claim date not stated')}</span><span>${esc(row.scope||label)}</span>${row.status?`<span>${esc(statusLabel(row.status))}</span>`:''}${row.period?`<span>Applies to ${esc(row.period)}</span>`:''}</div>${row.qualifier?`<p class="atlas-research-qualification">${esc(row.qualifier)}</p>`:''}${row.source_locator?`<details class="atlas-research-locator"><summary>Find this claim in the source</summary><p>${esc(row.source_locator)}</p></details>`:''}</article>`;
}
function atlasResearchTopicContent(topic,query='') {
  const q=query.trim().toLocaleLowerCase(),rows=topic.rows.filter(r=>!q||atlasResearchText(r).toLocaleLowerCase().includes(q));
  return `<header><h3>${topic.label}</h3><span>${q?rows.length+' / ':''}${topic.rows.length} ${topic.rows.length===1?'claim':'claims'}</span></header>${rows.length?rows.slice(0,2).map(atlasResearchClaim).join('')+(rows.length>2?`<details class="atlas-research-more" ${q?'open':''}><summary>Read ${rows.length-2} more claims</summary>${rows.slice(2).map(atlasResearchClaim).join('')}</details>`:''):`<p class="atlas-research-missing">${q?'No matching project claim.': 'No project-specific primary claim in this category.'}</p>`}`;
}
function atlasResearchRecent(p) {
  const topics=new Set(),rows=p.rows.filter(row=>{
    const topic=atlasResearchTopic(row);
    if (!row.as_of||topic==='identity'||topics.has(topic)) return false;
    topics.add(topic);return true;
  }).slice(0,3);
  return rows.length?`<section class="atlas-research-brief"><h3>Recent dated disclosures</h3><p>Dates are reported / as-of dates. Targets and operating milestones retain their stated scope.</p><div>${rows.map(row=>`<article data-research-highlight="${esc(row.id)}"><header><span>${esc(row.as_of)} · ${esc(ATLAS_RESEARCH_TOPICS.find(([id])=>id===atlasResearchTopic(row))?.[1])}</span>${primaryRef(row.source_id)}</header><button class="text-button" data-research-jump-claim="${esc(row.id)}">${esc(atlasResearchLabel(row))} ↘</button><p>${atlasResearchValue(row)}</p><small>${esc(row.scope||atlasResearchLabel(row))}${row.period?' · Applies to '+esc(row.period):''}</small>${row.qualifier?`<p class="atlas-research-qualification">${esc(row.qualifier)}</p>`:''}</article>`).join('')}</div></section>`:'';
}
function atlasResearchTimeline(p) {
  const rows=p.rows.filter(r=>atlasResearchTopic(r)==='development'&&r.as_of).slice().sort((a,b)=>-atlasResearchDateOrder(a,b));
  return rows.length?`<details class="atlas-research-timeline"><summary>Dated development disclosures · ${rows.length}</summary><p>Ordered by each claim’s reported / as-of date, not an inferred completion date. Announcements, targets and commissioning statements remain distinct.</p><ol>${rows.map(row=>`<li><time datetime="${esc(row.as_of)}">${esc(row.as_of)}</time><div><button class="text-button" data-research-jump-claim="${esc(row.id)}">${esc(atlasResearchLabel(row))} ↘</button><p>${atlasResearchValue(row)}</p><small>${esc(row.scope||atlasResearchLabel(row))}</small>${row.qualifier?`<p class="atlas-research-qualification">${esc(row.qualifier)}</p>`:''}${primaryRef(row.source_id)}</div></li>`).join('')}</ol></details>`:'';
}
function atlasResearchSources(p) {
  return p.sources.length?`<details class="atlas-research-source-list"><summary>Primary source trail · ${p.sources.length} documents</summary><p>Publisher labels identify attribution; they do not establish independent corroboration.</p>${p.sources.map(source=>{
    const project=p.rows.filter(r=>r.source_id===source.id).length,context=p.context.filter(r=>r.source_id===source.id).length;
    return `<article><button class="text-button" data-atlas-action="source" data-id="${esc(source.id)}">${esc(source.title)} ↗</button><span>${esc(source.publisher)}</span><small>${project} project claims · ${context} context · ${source.published_at?'Published '+esc(source.published_at):'Publication date not stated'} · Retrieved ${esc(source.retrieved_at||'date not stated')}</small></article>`;
  }).join('')}</details>`:'';
}
function atlasResearchPanel(s) {
  if (!s) return '';
  const p=atlasResearchProfile(s),review=p.review,query=atlasResearchQueries.get(s.id)||'';
  const q=query.trim().toLocaleLowerCase(),matches=row=>!q||atlasResearchText(row).toLocaleLowerCase().includes(q);
  const context=p.context.filter(matches);
  return `<section class="atlas-project-research" data-project-research="${esc(s.id)}">
    <header class="atlas-research-heading"><div><div class="atlas-eyebrow">PROJECT RESEARCH / CITED DISCLOSURES</div><h2>Disclosures & development.</h2><p>${p.rows.length} project claims · ${p.context.length} contextual claims · ${p.sources.length} ${p.sources.length===1?'source':'sources'} · ${p.publishers.length} ${p.publishers.length===1?'publisher':'publishers'}</p></div><button class="btn" data-research-index>Explore all project research ↗</button></header>
    ${review?`<div class="atlas-research-identity ${review.outcome==='unresolved'?'unresolved':''}"><b>${review.outcome==='unresolved'?'Identity needs resolution':review.outcome==='partial'?'Partial identity or evidence':'Research identity and boundaries'}</b><p>${esc(review.identity_note)}</p><small>Reviewed ${esc(ATLAS_PRIMARY.research_coverage.reviewed_at)}</small></div>`:''}
    ${atlasResearchRecent(p)}
    <nav class="atlas-research-topic-nav" aria-label="Project disclosure topics">${p.topics.map(t=>`<button data-research-jump-topic="${t.id}">${t.label}<span>${t.rows.length||'—'}</span></button>`).join('')}</nav>
    <div class="atlas-research-dossier-search"><label>Search this project’s claims<input type="search" data-research-query="${esc(s.id)}" value="${esc(query)}" placeholder="Cooling, milestone, source, date…" autocomplete="off" maxlength="500"></label><button class="text-button" data-research-clear ${query?'':'disabled'}>Clear</button></div>
    <p class="atlas-research-query-status" role="status">${q?`${p.rows.filter(matches).length} matching project claims · ${context.length} matching context claims. No match does not mean zero capacity.`:`${p.rows.length} project claims · ${p.context.length} context. Dated claims appear newest first; undated disclosures follow.`}</p>
    <div class="atlas-research-topic-grid">${p.topics.map(topic=>`<section class="atlas-research-topic ${topic.rows.length?'':'empty'}" data-research-topic="${topic.id}" tabindex="-1" ${q&&!topic.rows.some(matches)?'hidden':''}>${atlasResearchTopicContent(topic,query)}</section>`).join('')}</div>
    ${p.context.length?`<details class="atlas-research-context" ${q&&context.length?'open':''} ${q&&!context.length?'hidden':''}><summary>Wider context and unresolved associations · ${q?context.length+' / ':''}${p.context.length} claims</summary><p>These sources describe a wider area, portfolio, or project whose match to the archived name needs review. Their values do not establish this project’s capacity.</p><div class="atlas-research-context-claims">${context.map(atlasResearchClaim).join('')}</div></details>`:''}
    ${atlasResearchTimeline(p)}${atlasResearchSources(p)}
    ${review?.gaps?.length?`<div class="atlas-research-gaps"><h3>Open research questions</h3><ul>${review.gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul></div>`:''}
    <footer><span>Claim dates remain separate from this research review.</span><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">All claims & earlier revisions ↗</button><button class="text-button" data-atlas-action="export" data-id="${esc(s.id)}">Export cited dossier ↓</button></footer>
  </section>`;
}
function atlasResearchApplyQuery(panel) {
  if (!panel) return;
  const p=atlasResearchProfile(site(panel.dataset.projectResearch)),query=atlasResearchQueries.get(p.site.id)||'',q=query.trim().toLocaleLowerCase();
  const matches=row=>!q||atlasResearchText(row).toLocaleLowerCase().includes(q);
  for(const topic of p.topics) {
    const element=panel.querySelector(`[data-research-topic="${topic.id}"]`);
    element.innerHTML=atlasResearchTopicContent(topic,query);
    element.hidden=!!q&&!topic.rows.some(matches);
  }
  const context=panel.querySelector('.atlas-research-context'),contextRows=p.context.filter(matches);
  if(context) {
    context.querySelector('.atlas-research-context-claims').innerHTML=contextRows.map(atlasResearchClaim).join('');
    context.hidden=!!q&&!contextRows.length;
    context.querySelector('summary').textContent=`Wider context and unresolved associations · ${q?contextRows.length+' / ':''}${p.context.length} claims`;
    if(q&&contextRows.length)context.open=true;
  }
  panel.querySelector('.atlas-research-query-status').textContent=q
    ? `${p.rows.filter(matches).length} matching project claims · ${contextRows.length} matching context claims. No match does not mean zero capacity.`
    : `${p.rows.length} project claims · ${p.context.length} context. Dated claims appear newest first; undated disclosures follow.`;
  panel.querySelector('[data-research-clear]').disabled=!query;
}
function atlasResearchReveal(panel,{claim,topic}) {
  if(!panel)return;
  if(atlasResearchQueries.get(panel.dataset.projectResearch)) {
    atlasResearchQueries.delete(panel.dataset.projectResearch);
    panel.querySelector('[data-research-query]').value='';atlasResearchApplyQuery(panel);
  }
  const target=claim?panel.querySelector(`[data-research-claim="${CSS.escape(claim)}"]`):panel.querySelector(`[data-research-topic="${CSS.escape(topic)}"]`);
  if(!target)return;
  for(let parent=target.parentElement;parent&&parent!==panel;parent=parent.parentElement) {
    if(parent.tagName==='DETAILS')parent.open=true;
  }
  target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'instant'});
}
function atlasResearchProfiles() {
  const st=atlasResearchState,q=st.query.trim().toLocaleLowerCase();
  return D.sites.map(atlasResearchProfile).filter(p=>(st.outcome==='all'||p.review?.outcome===st.outcome)
    && (st.country==='all'||p.site.country===st.country) && (st.operator==='all'||p.site.primary_company===st.operator)
    && (st.topic==='all'||p.topics.find(t=>t.id===st.topic)?.rows.length)
    && (!q || [p.site.name,p.site.location,p.site.owner_label,p.review?.identity_note,...(p.review?.gaps||[])].join(' ').toLocaleLowerCase().includes(q)
      || p.searchRows.some(r=>r.text.includes(q)&&(st.topic==='all'||!primaryIsContext(r.row)&&atlasResearchTopic(r.row)===st.topic))))
    .sort((a,b)=>(st.sort==='date'?String(b.latest||'').localeCompare(String(a.latest||'')):0)
      || a.site.name.localeCompare(b.site.name)||a.site.id.localeCompare(b.site.id));
}
function atlasResearchMatch(p) {
  const query=atlasResearchState.query,q=query.trim().toLocaleLowerCase();
  if(!q)return '';
  const match=p.searchRows.filter(r=>r.text.includes(q)&&(atlasResearchState.topic==='all'||!primaryIsContext(r.row)&&atlasResearchTopic(r.row)===atlasResearchState.topic))
    .sort((a,b)=>Number(primaryIsContext(a.row))-Number(primaryIsContext(b.row)))[0]?.row;
  if(match) {
    const context=primaryIsContext(match),source=primarySource(match.source_id);
    return `<div class="atlas-research-match ${context?'context':''}" data-research-match="${esc(match.id)}"><span>${context?'Matched wider context':'Matched project disclosure'} · ${esc(match.as_of||'Date not stated')}</span><button class="text-button" data-research-site="${esc(p.site.id)}" data-research-claim-target="${esc(match.id)}">${atlasResearchHighlight(atlasResearchLabel(match),query)} ↘</button><p>${atlasResearchHighlight(atlasResearchPlainValue(match),query)}</p><small>${atlasResearchHighlight(match.scope||atlasResearchLabel(match),query)}${match.period?' · Applies to '+atlasResearchHighlight(match.period,query):''}${match.qualifier?' · '+atlasResearchHighlight(match.qualifier,query):''}</small>${match.source_locator?.toLocaleLowerCase().includes(q)?`<p class="atlas-research-match-locator">Source locator: ${atlasResearchHighlight(match.source_locator,query)}</p>`:''}<div class="atlas-research-match-source">${primaryRef(match.source_id)}<span>${atlasResearchHighlight([source?.publisher,source?.title].filter(Boolean).join(' · '),query)}</span></div></div>`;
  }
  const gap=p.review?.gaps?.find(text=>text.toLocaleLowerCase().includes(q));
  if(gap)return `<div class="atlas-research-match review"><span>Matched open research question</span><p>${atlasResearchHighlight(gap,query)}</p></div>`;
  return '';
}
function atlasResearchIndexProject(p) {
  return `<article class="atlas-research-project" data-research-project="${esc(p.site.id)}"><header><button data-research-site="${esc(p.site.id)}"><h3>${atlasResearchHighlight(p.site.name,atlasResearchState.query)}</h3><span>${esc(p.site.owner_label)} · ${esc(p.site.location)} ↗</span></button><span class="atlas-research-outcome">${esc(({enriched:'Enriched',partial:'Partial',unresolved:'Identity unresolved'})[p.review?.outcome]||'Not yet researched')}</span></header><p>${p.rows.length} project claims · ${p.context.length} context · ${p.sources.length} sources / ${p.publishers.length} publishers</p><div class="atlas-research-fields">${p.topics.map(t=>`<button class="${t.rows.length?'present':'absent'}" data-research-site="${esc(p.site.id)}" data-research-topic-target="${t.id}" aria-label="${esc(p.site.name)}: ${t.label}, ${t.rows.length} project claims">${t.label}<b>${t.rows.length||'—'}</b></button>`).join('')}</div>${atlasResearchMatch(p)}${p.review?.identity_note?`<p class="atlas-research-index-note">${esc(p.review.identity_note)}</p>`:''}<footer><span>${p.latest?'Newest dated project claim: '+esc(p.latest):'No dated project claim'}</span><button class="text-button" data-research-site="${esc(p.site.id)}">Read dossier ↗</button></footer></article>`;
}
function atlasResearchIndexResults() {
  if (state.drawer?.kind!=='research-index') return;
  const all=atlasResearchProfiles(),st=atlasResearchState;
  st.offset=Math.max(0,Math.min(st.offset,Math.max(0,Math.ceil(all.length/15)-1)*15));
  $('#atlas-research-count').textContent=`${all.length} matching ${all.length===1?'project':'projects'} · categories count project claims, not completeness`;
  $('#atlas-research-projects').innerHTML=all.slice(st.offset,st.offset+15).map(atlasResearchIndexProject).join('') || '<div class="atlas-research-empty"><h3>No matching research project.</h3><p>Adjust your search or clear the filters. Missing evidence does not mean zero capacity.</p></div>';
  $('#atlas-research-pages').innerHTML=`<button class="btn small" data-research-page="previous" ${st.offset===0?'disabled':''}>← Previous</button><span>${all.length?st.offset+1:0}–${Math.min(st.offset+15,all.length)} / ${all.length}</span><button class="btn small" data-research-page="next" ${st.offset+15>=all.length?'disabled':''}>Next →</button>`;
  const active=['outcome','topic','country','operator'].filter(key=>st[key]!=='all').length;
  $('#atlas-research-refine-label').textContent=active?`Refine projects · ${active} active ${active===1?'filter':'filters'}`:'Refine projects';
  const chips=[['topic',ATLAS_RESEARCH_TOPICS.find(([id])=>id===st.topic)?.[1]],['country',st.country],['operator',company(st.operator)?.name||st.operator],['sort','Newest dated project claim']];
  $('#atlas-research-active-filters').innerHTML=chips.filter(([key])=>st[key]!== (key==='sort'?'name':'all')).map(([key,label])=>`<button data-research-remove-filter="${key}" aria-label="Remove ${esc(label)} ${key==='sort'?'ordering':'filter'}">${esc(label)} <span aria-hidden="true">×</span></button>`).join('');
  $('#atlas-research-reset').disabled=!st.query&&!active&&st.sort==='name';
  atlasResearchURL();
}
function atlasResearchOptions(values,current,allLabel) {
  return [['all',allLabel],...values].map(([id,label])=>`<option value="${esc(id)}" ${current===id?'selected':''}>${esc(label)}</option>`).join('');
}
function atlasResearchURL() {
  const params=new URLSearchParams(),st=atlasResearchState;
  if(st.query)params.set('q',st.query);
  for(const key of ['outcome','topic','country','operator'])if(st[key]!=='all')params.set(key,st[key]);
  if(st.sort!=='name')params.set('sort',st.sort);
  if(st.offset)params.set('page',String(st.offset/15+1));
  try{sessionStorage.setItem('atlas-research-view',params.toString());}catch(_){/* URL and in-session navigation remain available. */}
  history.replaceState(null,'','#research'+(params.size?'?'+params.toString():''));
}
function atlasResearchIndex() {
  const profiles=D.sites.map(atlasResearchProfile),covered=profiles.filter(p=>p.rows.length).length;
  const searched=ATLAS_PRIMARY.research_coverage?.projects.length||0;
  const countries=[...new Set(D.sites.map(s=>s.country))].sort().map(value=>[value,value]);
  const operators=[...new Set(D.sites.map(s=>s.primary_company))].map(id=>[id,company(id)?.name||id]).sort((a,b)=>a[1].localeCompare(b[1]));
  $('#drawer-type').textContent='PROJECT RESEARCH / COVERAGE & OPEN QUESTIONS';
  $('#drawer-content').innerHTML=`<section class="atlas-research-index"><div class="atlas-eyebrow">FACILITY DOSSIERS</div><h1>Every project.<br><span>Follow the evidence.</span></h1><p>${searched} projects investigated · ${covered} with project-specific primary claims · ${profiles.filter(p=>p.review?.outcome==='unresolved').length} identities unresolved. Research reviewed ${esc(ATLAS_PRIMARY.research_coverage?.reviewed_at||ATLAS_PRIMARY.published_at)}.</p><p>Explore technical design, power, milestones, relationships and financing. Each search result shows its matching disclosure. Empty categories remain open questions.</p>
    <div class="atlas-research-controls"><label>Search projects and their evidence<input type="search" id="atlas-research-query" value="${esc(atlasResearchState.query)}" placeholder="Cooling, utility, address, partner…" autocomplete="off" maxlength="500"></label><label>Research outcome<select id="atlas-research-outcome">${atlasResearchOptions([['enriched','Enriched'],['partial','Partial'],['unresolved','Identity unresolved']],atlasResearchState.outcome,'All projects')}</select></label></div>
    <details class="atlas-research-refine" ${['topic','country','operator'].some(key=>atlasResearchState[key]!=='all')||atlasResearchState.sort!=='name'?'open':''}><summary id="atlas-research-refine-label">Refine projects</summary><div>
      <label>Project claim topic<select data-research-filter="topic">${atlasResearchOptions(ATLAS_RESEARCH_TOPICS,atlasResearchState.topic,'Any topic')}</select></label>
      <label>Geography<select data-research-filter="country">${atlasResearchOptions(countries,atlasResearchState.country,'All countries')}</select></label>
      <label>Archived operator association<select data-research-filter="operator">${atlasResearchOptions(operators,atlasResearchState.operator,'All operators')}</select></label>
      <label>Order projects<select data-research-filter="sort">${[['name','Project name'],['date','Newest dated project claim']].map(([id,label])=>`<option value="${id}" ${atlasResearchState.sort===id?'selected':''}>${label}</option>`).join('')}</select></label>
    </div><p>Topic filters require project-specific evidence. Geography and operator filters follow the archived collection; unresolved identities remain labeled. A recent disclosure is not proof of current operating capacity.</p></details>
    <div id="atlas-research-active-filters" aria-label="Active research refinements"></div><div class="atlas-research-index-actions"><span>Bookmark this URL to retain your search and filters.</span><button class="text-button" id="atlas-research-reset" data-research-reset>Clear search & filters</button></div>
    <p id="atlas-research-count" role="status"></p><div id="atlas-research-projects"></div><nav id="atlas-research-pages" aria-label="Project research pages"></nav></section>`;
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
  if(kind==='site'&&site(id))$('#drawer-type').textContent='FACILITY DOSSIER / '+site(id).name;
  if (kind==='research-index') atlasResearchIndex();
  if (kind==='primary-source') {
    const claims=ATLAS_EVIDENCE_KINDS.slice(0,2).flatMap(type=>(ATLAS_PRIMARY[type]||[])
      .filter(row=>row.source_id===id).map(row=>({...row,kind:type})));
    $('#drawer-content').querySelectorAll('.atlas-source-observation').forEach((element,i)=>{
      const row=claims[i];
      if (row) element.innerHTML=`<h3>${esc(site(row.site_id)?.name||row.site_id)}</h3>${primaryIsContext(row)?'<p class="atlas-source-context-label">Wider context / not a project total</p>':''}${atlasResearchClaim(row)}`;
    });
  }
  document.querySelectorAll('.atlas-project-research').forEach(panel=>{
    if(atlasResearchQueries.get(panel.dataset.projectResearch))atlasResearchApplyQuery(panel);
  });
};
ATLAS.openDrawer=openDrawer;
const atlasResearchPreviousExport=atlasCitedDossier;
atlasCitedDossier=function(s) {
  const p=atlasResearchProfile(s);
  return {...atlasResearchPreviousExport(s),research_review:p.review||null,
    research_reviewed_at:ATLAS_PRIMARY.research_coverage?.reviewed_at||null,
    project_claim_ids:p.rows.map(r=>r.id),contextual_claim_ids:p.context.map(r=>r.id),
    topic_claim_ids:Object.fromEntries(p.topics.map(t=>[t.id,t.rows.map(r=>r.id)])),
    development_disclosures:p.rows.filter(r=>atlasResearchTopic(r)==='development'&&r.as_of)
      .slice().sort((a,b)=>-atlasResearchDateOrder(a,b)).map(r=>({claim_id:r.id,as_of:r.as_of,source_id:r.source_id})),
    development_date_policy:'Ordered by reported/as-of dates; targets and completion dates are not inferred from those dates.'};
};
ATLAS.evidence.export=atlasCitedDossier;
const atlasResearchPreviousPower=primaryPowerRows;
primaryPowerRows=function(s){return atlasResearchPreviousPower(s).filter(r=>!primaryIsContext(r));};
function atlasResearchMatches(s,q) {
  return [s.name,s.location,s.owner_label,JSON.stringify(s.hardware),JSON.stringify(s.facts),
    ...atlasResearchProfile(s).searchRows.map(r=>r.text)]
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
  const query=q.trim().toLocaleLowerCase();
  if (!query) return;
  const rows=D.sites.map(atlasResearchProfile).map(profile=>({profile,
    match:profile.searchRows.find(r=>!primaryIsContext(r.row)&&r.text.includes(query))?.row
      || profile.searchRows.find(r=>r.text.includes(query))?.row})).filter(r=>r.match);
  if (rows.length) $('#search-results').insertAdjacentHTML('afterbegin',`<div class="command-hint">Project research · ${rows.length} matching dossiers</div>`+rows.slice(0,6).map(({profile:p,match})=>`<button class="search-result" data-research-site="${esc(p.site.id)}" data-research-claim-target="${esc(match.id)}"><span class="result-type">${primaryIsContext(match)?'WIDER CONTEXT':'PROJECT EVIDENCE'}</span><span><b>${esc(p.site.name)}</b><small>${esc(atlasResearchLabel(match))} · ${esc(match.source_id)} · ${esc(match.as_of||'Date not stated')}</small></span></button>`).join(''));
  const results=$('#search-results');
  if(results.querySelector('.search-result'))results.querySelector('.search-empty')?.remove();
};
document.addEventListener('click',event=>{
  if (event.target.closest('[data-research-index]')) openDrawer('research-index','projects');
  const selected=event.target.closest('[data-research-site]');
  if (selected) {
    if(!$('#search-modal').hidden)closeSearch();
    openDrawer('site',selected.dataset.researchSite,{focus:!(selected.dataset.researchClaimTarget||selected.dataset.researchTopicTarget)});
    if(selected.dataset.researchClaimTarget||selected.dataset.researchTopicTarget)atlasResearchReveal($('#drawer .atlas-project-research'),{claim:selected.dataset.researchClaimTarget,topic:selected.dataset.researchTopicTarget});
  }
  const jump=event.target.closest('[data-research-jump-claim],[data-research-jump-topic]');
  if(jump)atlasResearchReveal(jump.closest('.atlas-project-research'),{claim:jump.dataset.researchJumpClaim,topic:jump.dataset.researchJumpTopic});
  const clear=event.target.closest('[data-research-clear]');
  if(clear) {
    const panel=clear.closest('.atlas-project-research');atlasResearchQueries.delete(panel.dataset.projectResearch);
    const input=panel.querySelector('[data-research-query]');input.value='';atlasResearchApplyQuery(panel);input.focus({preventScroll:true});
  }
  if(event.target.closest('[data-research-reset]')) {
    Object.assign(atlasResearchState,{query:'',outcome:'all',topic:'all',country:'all',operator:'all',sort:'name',offset:0});
    $('#atlas-research-query').value='';$('#atlas-research-outcome').value='all';
    document.querySelectorAll('[data-research-filter]').forEach(select=>select.value=select.dataset.researchFilter==='sort'?'name':'all');
    atlasResearchIndexResults();$('#atlas-research-query').focus({preventScroll:true});
  }
  const remove=event.target.closest('[data-research-remove-filter]');
  if(remove) {
    const key=remove.dataset.researchRemoveFilter;atlasResearchState[key]=key==='sort'?'name':'all';atlasResearchState.offset=0;
    document.querySelector(`[data-research-filter="${key}"]`).value=atlasResearchState[key];
    atlasResearchIndexResults();$('#atlas-research-query').focus({preventScroll:true});
  }
  const pager=event.target.closest('[data-research-page]');
  if (pager) {
    atlasResearchState.offset+=pager.dataset.researchPage==='next'?15:-15;atlasResearchIndexResults();
    const first=$('#atlas-research-projects .atlas-research-project>header>button');
    first?.focus({preventScroll:true});first?.closest('.atlas-research-project').scrollIntoView({block:'start',behavior:'instant'});
  }
});
document.addEventListener('input',event=>{
  if (event.target.id==='atlas-research-query') {atlasResearchState.query=event.target.value;atlasResearchState.offset=0;atlasResearchIndexResults();}
  if(event.target.matches('[data-research-query]')) {
    atlasResearchQueries.set(event.target.dataset.researchQuery,event.target.value);
    atlasResearchApplyQuery(event.target.closest('.atlas-project-research'));
  }
});
document.addEventListener('change',event=>{
  if (event.target.id==='atlas-research-outcome') {atlasResearchState.outcome=event.target.value;atlasResearchState.offset=0;atlasResearchIndexResults();}
  if(event.target.matches('[data-research-filter]')) {
    atlasResearchState[event.target.dataset.researchFilter]=event.target.value;atlasResearchState.offset=0;atlasResearchIndexResults();
  }
});
const atlasResearchPreviousRoute=routeFromHash;
window.removeEventListener('hashchange',atlasResearchPreviousRoute);
function atlasResearchRestore(query) {
  const params=new URLSearchParams(query),pick=(key,values)=>values.includes(params.get(key))?params.get(key):'all';
  Object.assign(atlasResearchState,{query:(params.get('q')||'').slice(0,500),
    outcome:pick('outcome',['enriched','partial','unresolved']),topic:pick('topic',ATLAS_RESEARCH_TOPICS.map(([id])=>id)),
    country:pick('country',D.sites.map(s=>s.country)),operator:pick('operator',D.sites.map(s=>s.primary_company)),
    sort:params.get('sort')==='date'?'date':'name',offset:Math.max(0,Math.min(5,(parseInt(params.get('page'),10)||1)-1))*15});
}
routeFromHash=function() {
  const [path,query='']=location.hash.slice(1).split('?');
  if(path!=='research')return atlasResearchPreviousRoute();
  atlasResearchRestore(query);
  navigate('catalog',{hash:true});openDrawer('research-index','projects',{back:true});
};
window.addEventListener('hashchange',routeFromHash);
ATLAS.research={open:()=>openDrawer('research-index','projects'),profile:atlasResearchProfile,rows:atlasResearchProfiles};
try{const previous=sessionStorage.getItem('atlas-research-view');if(previous)atlasResearchRestore(previous);}catch(_){/* Storage is optional. */}
if (['overview','globe'].includes(state.view)) render();
if (state.drawer?.kind==='site') openDrawer('site',state.drawer.id,{back:true});
if(location.hash.split('?')[0]==='#research')routeFromHash();
document.documentElement.classList.add('research-ready');
