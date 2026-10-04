'use strict';
/* Read-only acquisition console. Fetching a page never publishes a claim.
   Keep request identity separate from drawer identity: a late response must not
   reopen a closed drawer, change the selected source, or overwrite a new page. */
const atlasHealth = {
  tab:'sources', source:null, activity:null, events:null,
  offset:0, eventOffset:0, busy:false, error:null, request:0
};
const atlasHealthTime = value => {
  if (!value) return 'Not recorded';
  const date=new Date(value);
  return Number.isNaN(date.getTime()) ? 'Invalid source timestamp' :
    new Intl.DateTimeFormat('en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:'UTC'}).format(date)+' UTC';
};
const atlasHealthOpen = () => state.drawer?.kind==='monitor' && !$('#drawer').hidden;
const atlasHealthCounts = () => atlasMonitorStatus?.counts || {};
function atlasHealthValidate(data, type) {
  if (!data || !Array.isArray(data.items) || !Number.isSafeInteger(data.total) || data.total<0 ||
      !(data.next_offset===null || Number.isSafeInteger(data.next_offset) && data.next_offset>=0)) {
    throw Error('Unexpected acquisition response');
  }
  for (const row of data.items) {
    if (!row || typeof row!=='object' || (type==='sources' ? typeof row.id!=='string' : !Number.isSafeInteger(row.id))) {
      throw Error('Invalid acquisition record');
    }
  }
  return data;
}
async function atlasHealthLoad({source=atlasHealth.source,offset=0}={}) {
  if (!globalThis.ATLAS_SERVICE) return;
  const request=++atlasHealth.request;
  const focusedPage=document.activeElement?.getAttribute('data-health-page');
  const changedSource=source?.id!==atlasHealth.source?.id;
  atlasHealth.source=source;
  if (changedSource) {atlasHealth.events=null;atlasHealth.eventOffset=0;}
  atlasHealth.busy=true;atlasHealth.error=null;atlasHealthRender();
  try {
    const path=source ? '/sources/'+encodeURIComponent(source.id)+'/events?limit=20' : '/source-activity?limit=12';
    const response=await fetch(ATLAS_SERVICE.base+path+'&offset='+Math.max(0,offset),{
      cache:'no-store',signal:AbortSignal.timeout(8000)
    });
    if (!response.ok) throw Error('Acquisition HTTP '+response.status);
    const data=atlasHealthValidate(await response.json(),source?'events':'sources');
    if (request!==atlasHealth.request) return;
    if (source) {atlasHealth.events=data;atlasHealth.eventOffset=offset;}
    else {atlasHealth.activity=data;atlasHealth.offset=offset;}
  } catch(error) {
    if (request===atlasHealth.request) atlasHealth.error=String(error.message||error);
  } finally {
    if (request===atlasHealth.request) {
      atlasHealth.busy=false;atlasHealthRender();
      if (focusedPage && atlasHealthOpen()) {
        const pager=document.querySelector(`[data-health-page="${CSS.escape(focusedPage)}"]`);
        (pager&&!pager.disabled?pager:document.querySelector('[data-health-page]:not(:disabled)'))?.focus({preventScroll:true});
      }
    }
  }
}
function atlasHealthPager(data, offset, type, size) {
  if (!data) return '';
  return `<nav class="atlas-health-pager" aria-label="${type==='events'?'Event':'Source'} pages">
    <button class="btn small" data-health-page="previous" data-health-size="${size}" ${offset===0||atlasHealth.busy?'disabled':''}>← Previous</button>
    <span>${data.total?offset+1:0}–${offset+data.items.length} of ${data.total}</span>
    <button class="btn small" data-health-page="next" data-health-size="${size}" ${data.next_offset===null||atlasHealth.busy?'disabled':''}>Next →</button>
  </nav>`;
}
function atlasHealthSource(row) {
  const capture=({recent:'Within fetch window',stale:'Capture overdue',never:'Not captured'})[row.capture_state] || 'Capture state unknown';
  const url=queueURL(row.url), deferred=row.fetch_state==='deferred';
  return `<article class="atlas-health-source" data-health-source-id="${esc(row.id)}">
    <header><span class="atlas-card-kicker">${esc(row.id)} / ${esc(row.publisher)}</span><span class="atlas-health-badge" data-state="${deferred?'deferred':esc(row.capture_state)}">${deferred?'Retry deferred':capture}</span></header>
    <h3><button data-health-source="${esc(row.id)}">${esc(row.title || row.id)} <span>↗</span></button></h3>
    <dl class="atlas-health-dates"><div><dt>Successful fetch</dt><dd>${row.last_success?esc(atlasHealthTime(row.last_success)):'Not yet captured'}</dd></div><div><dt>Editorial retrieval</dt><dd>${esc(row.reviewed_retrieval_at || 'Not reviewed')}</dd></div></dl>
    ${row.last_error?`<p class="atlas-health-error-detail">${esc(row.last_error)}</p>`:''}
    <footer><span>${Number(row.pending_review)||0} awaiting review · ${row.last_status?'HTTP '+esc(row.last_status):'No HTTP result'}</span><button class="text-button" data-health-source="${esc(row.id)}">Fetch history →</button></footer>
    <details class="atlas-health-identity"><summary>Source identity & schedule</summary><dl><div><dt>Publisher date</dt><dd>${esc(row.published_at || 'Not stated')}</dd></div><div><dt>Next attempt</dt><dd>${esc(atlasHealthTime(row.next_fetch_at))}</dd></div><div><dt>First capture of this body</dt><dd>${esc(atlasHealthTime(row.first_captured_at))}</dd></div><div><dt>Latest observation of this body</dt><dd>${esc(atlasHealthTime(row.observed_at))}</dd></div></dl><p>Body SHA-256 <code>${esc(row.sha256 || 'No captured body')}</code></p><p>Semantic SHA-256 <code>${esc(row.semantic_sha256 || 'No captured body')}</code></p>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Read publisher source ↗</a>`:''}</details>
  </article>`;
}
function atlasHealthActivity() {
  const data=atlasHealth.activity;
  return `<div class="atlas-health-section-head"><div><h2>Source activity</h2><p>Capture recency and editorial review are different dates.</p></div><button class="btn small" data-health-action="refresh" ${atlasHealth.busy?'disabled':''}>Refresh status ↻</button></div>
    <p class="atlas-health-policy">${esc(data?.policy || 'A recent fetch only confirms that a source was retrieved. It does not re-review claims or establish that facility facts are current.')}</p>
    ${data?`<p class="atlas-health-stamp">Activity checked ${esc(atlasHealthTime(data.checked_at))}</p>${data.items.map(atlasHealthSource).join('') || '<div class="notice">No sources on this page. This is not a claim that every source is current.</div>'}${atlasHealthPager(data,atlasHealth.offset,'sources',12)}`:atlasHealth.busy?'<p class="atlas-health-loading" role="status">Loading source activity…</p>':'<p>No acquisition results loaded.</p>'}`;
}
function atlasHealthEvents() {
  const source=atlasHealth.source,data=atlasHealth.events;
  const names={'baseline':'First captured representation','changed':'Changed representation','not-modified':'Not modified (HTTP 304)','unchanged-content':'Same content retrieved','deferred':'Attempt deferred'};
  return `<button class="text-button" data-health-action="back">← All source activity</button><div class="atlas-health-section-head"><div><p class="atlas-card-kicker">${esc(source.id)} / FETCH EVENT HISTORY</p><h2>${esc(source.title || source.id)}</h2></div><button class="btn small" data-health-action="refresh" ${atlasHealth.busy?'disabled':''}>Refresh ↻</button></div>
    <p class="atlas-health-policy">Each attempt is retained, including A → B → A changes. A returning body keeps its original version identity; it is still a new observation. These events are not editorial decisions.</p>
    ${data?`<ol class="atlas-health-timeline">${data.items.map(row=>`<li data-health-event="${row.id}"><div><span class="atlas-card-kicker">${esc(atlasHealthTime(row.attempted_at))}</span><span class="atlas-health-badge" data-state="${row.error?'deferred':'event'}">${row.status?'HTTP '+esc(row.status):'No response'}</span></div><h3>${esc(names[row.outcome] || row.outcome)}</h3>${row.error?`<p class="atlas-health-error-detail">${esc(row.error)}</p>`:''}<p>Version <code>${esc(row.version_id || 'None · no body captured')}</code></p><small>Event ${row.id} · acquisition only</small></li>`).join('') || '<li class="atlas-health-empty">No fetch attempts recorded for this source. A checked-in citation is not evidence that the background worker fetched it.</li>'}</ol>${atlasHealthPager(data,atlasHealth.eventOffset,'events',20)}`:atlasHealth.busy?'<p class="atlas-health-loading" role="status">Loading immutable fetch history…</p>':'<p>No event history loaded.</p>'}`;
}
function atlasHealthQueue() {
  return `<section class="atlas-live-review"><div class="atlas-health-section-head"><div><h2>Acquisition review queue</h2><p>${atlasQueueTotal} pending items. Acknowledging a capture does not accept a claim.</p></div><button class="btn small" data-health-action="queue-refresh">Refresh queue ↻</button></div>
    ${atlasMonitorQueue.map(row=>{const url=queueURL(row.payload.url);return `<article class="atlas-source-observation"><div class="atlas-card-kicker">${esc(row.kind)} / ${esc(row.source_id)}</div><h3>${esc(row.payload.title || row.payload.name || 'Source update')}</h3><p>${esc(row.payload.note || 'Pending explicit editorial review')}</p><p>Captured ${esc(atlasHealthTime(row.created_at))}</p>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="text-button">Read publisher source ↗</a>`:''}<details><summary>Queue identity</summary><code>${esc(row.id)}</code></details></article>`;}).join('') || '<div class="notice">No pending items on this page. This does not establish that all sources are current or all facility facts are reviewed.</div>'}
    <div class="atlas-health-pager"><button class="btn small" data-service-page="previous" ${atlasQueueOffset===0||atlasMonitorBusy?'disabled':''}>← Previous</button><span>${atlasQueueTotal?atlasQueueOffset+1:0}–${atlasQueueOffset+atlasMonitorQueue.length} of ${atlasQueueTotal}</span><button class="btn small" data-service-page="next" ${atlasQueueNext===null||atlasMonitorBusy?'disabled':''}>Next →</button></div>
    <h3>Explicit editorial review</h3><p>The web API is read-only. Review through the local command line with an actor, source, measurement boundary and reason.</p><pre class="atlas-command">python -m server queue
python -m server submit observation claim.json --actor analyst
python -m server review CLAIM_ID accepted --actor analyst --reason "Source and boundary checked"
python -m server export data/evidence.json</pre></section>`;
}
function atlasHealthPublication() {
  return `<h2>Published claims, not fetch outcomes.</h2><p>Loaded publication: <b>${esc(ATLAS_PRIMARY.published_at)}</b>. New reviewed publications are offered separately; you choose when to apply them.</p><p class="atlas-health-policy">${esc(ATLAS_PRIMARY.policy)}</p><p>${ATLAS_PRIMARY.sources.length} primary sources and ${ATLAS_PRIMARY.observations.length} current quantity records. These are coverage counts, not a complete industry inventory.</p><h3>Research candidates</h3><p>Candidates are not accepted site totals.</p>${(ATLAS_PRIMARY.discoveries||[]).map(row=>`<article class="atlas-source-observation"><h3>${esc(row.name)}</h3><p>${esc(row.location)} · ${esc(row.note)}</p>${primaryRef(row.source_id)}</article>`).join('') || '<p>No candidates in the loaded publication.</p>'}<h3>Persistent evidence service</h3><pre class="atlas-command">python -m server serve
python -m server backup /path/to/backup.sqlite3</pre><p>Raw source bodies stay in the private local evidence store. They are not exposed by this read-only console. Use a persistent volume and maintain independent backups.</p>`;
}
function atlasHealthRender() {
  if (!atlasHealthOpen() || !globalThis.ATLAS_SERVICE) return;
  const root=$('#drawer-content'),counts=atlasHealthCounts(),active=document.activeElement;
  const focusAttribute=['data-health-tab','data-health-action','data-health-page','data-service-page'].find(key=>active?.hasAttribute?.(key));
  const focusKey=focusAttribute?active.getAttribute(focusAttribute):null;
  const scroll=$('#drawer').scrollTop;
  const status=atlasMonitorStatus;
  root.innerHTML=`<section class="atlas-health-console" aria-label="Source acquisition health"><div class="atlas-eyebrow">ACQUIRE → VERSION → REVIEW → PUBLISH</div><h1>Sources checked.<br><span>Facts reviewed.</span></h1><p class="atlas-health-intro">A transparent record of what the worker fetched, what changed, and what still needs a human decision.</p>
    <div class="atlas-health-worker"><span class="atlas-health-badge" data-state="${atlasMonitorError?'deferred':status?.background_refresh?'running':'paused'}">${atlasMonitorError?'Monitor unavailable':status?status.background_refresh?'Worker running':'Refresh paused':'Connecting to service'}</span><span>Publication ${esc(ATLAS_PRIMARY.published_at)}</span></div>
    ${atlasMonitorError?`<p class="atlas-health-warning" role="status">Live monitor unavailable: ${esc(atlasMonitorError)}. Last-loaded results may be stale. The dated publication is still usable.</p>`:''}
    <div class="atlas-health-summary">${[['source_versions','Source versions'],['pending_review','Awaiting review'],['fetch_attempts','Fetch attempts']].map(([key,label])=>`<div><strong>${esc(counts[key]??'—')}</strong><span>${label}</span></div>`).join('')}</div>
    <p class="atlas-health-stamp">${status?'Status checked '+esc(atlasHealthTime(status.checked_at)):'No live status loaded yet.'} · All times UTC.</p>
    <div class="atlas-health-tabs" role="group" aria-label="Source monitor sections">${[['sources','Source activity'],['queue','Review queue'],['publication','Publication']].map(([id,label])=>`<button data-health-tab="${id}" aria-pressed="${atlasHealth.tab===id}">${label}</button>`).join('')}</div>
    ${atlasHealth.error&&atlasHealth.tab==='sources'?`<div class="atlas-health-warning" role="status">${esc(atlasHealth.error)}. ${(atlasHealth.source?atlasHealth.events:atlasHealth.activity)?'Previously loaded results are retained with their original timestamps.':'No current activity could be loaded.'}<button class="text-button" data-health-action="refresh">Retry acquisition check ↻</button></div>`:''}
    <section id="atlas-health-panel" aria-busy="${atlasHealth.busy}">${atlasHealth.tab==='sources'?(atlasHealth.source?atlasHealthEvents():atlasHealthActivity()):atlasHealth.tab==='queue'?atlasHealthQueue():atlasHealthPublication()}</section></section>`;
  if (focusKey) root.querySelector(`[${focusAttribute}="${CSS.escape(focusKey)}"]`)?.focus({preventScroll:true});
  $('#drawer').scrollTop=scroll;
}
const atlasHealthPreviousDrawer=atlasMonitorDrawer;
atlasMonitorDrawer=function() {
  if (!globalThis.ATLAS_SERVICE) {atlasHealthPreviousDrawer();return;}
  if (!atlasHealthOpen()) openDrawer('monitor','sources');
  $('#drawer-type').textContent='SOURCE HEALTH / ACQUISITION & REVIEW';
  atlasHealthRender();
  if (!atlasHealth.activity && !atlasHealth.busy && !atlasHealth.error) atlasHealthLoad();
};
const atlasHealthPreviousOpenDrawer=openDrawer;
openDrawer=function(kind,id,options={}) {
  atlasHealthPreviousOpenDrawer(kind,id,options);
  if (kind==='monitor' && globalThis.ATLAS_SERVICE) atlasHealthRender();
  if (kind==='primary-source' && globalThis.ATLAS_SERVICE) {
    $('#drawer-content').insertAdjacentHTML('beforeend',`<button class="btn atlas-health-source-link" data-health-open="${esc(id)}">Inspect acquisition history ↗</button>`);
  }
};
ATLAS.openDrawer=openDrawer;
const atlasHealthPreviousLabel=updateMonitorLabel;
updateMonitorLabel=function() {
  atlasHealthPreviousLabel();
  const button=document.querySelector('.atlas-monitor-launch'),label=$('#atlas-monitor-label');
  if (button && label) {button.setAttribute('title',label.textContent);button.setAttribute('aria-label','Source health: '+label.textContent);}
  atlasHealthRender();
};
document.addEventListener('click',event=>{
  const tab=event.target.closest('[data-health-tab]');
  if (tab) {atlasHealth.tab=tab.dataset.healthTab;atlasHealthRender();}
  const sourceButton=event.target.closest('[data-health-source]');
  if (sourceButton) {
    const source=atlasHealth.activity?.items.find(row=>row.id===sourceButton.dataset.healthSource);
    if (source) {atlasHealthLoad({source});$('#atlas-health-panel [data-health-action="back"]')?.focus({preventScroll:true});}
  }
  const open=event.target.closest('[data-health-open]');
  if (open) {atlasHealth.tab='sources';atlasMonitorDrawer();atlasHealthLoad({source:primarySource(open.dataset.healthOpen) || {id:open.dataset.healthOpen}});}
  const action=event.target.closest('[data-health-action]')?.dataset.healthAction;
  if (action==='back') {
    const sourceId=atlasHealth.source?.id;
    ++atlasHealth.request;atlasHealth.source=null;atlasHealth.busy=false;atlasHealth.error=null;
    atlasHealthRender();
    if (sourceId) document.querySelector(`[data-health-source="${CSS.escape(sourceId)}"]`)?.focus({preventScroll:true});
    if (!atlasHealth.activity) atlasHealthLoad();
  }
  if (action==='refresh') {
    pollAtlasMonitor().then(atlasHealthRender);
    atlasHealthLoad({offset:atlasHealth.source?atlasHealth.eventOffset:atlasHealth.offset});
  }
  if (action==='queue-refresh') pollAtlasMonitor().then(atlasHealthRender);
  const pager=event.target.closest('[data-health-page]');
  if (pager && !atlasHealth.busy) {
    const data=atlasHealth.source?atlasHealth.events:atlasHealth.activity;
    const current=atlasHealth.source?atlasHealth.eventOffset:atlasHealth.offset;
    const offset=pager.dataset.healthPage==='next'?data?.next_offset:Math.max(0,current-Number(pager.dataset.healthSize));
    if (offset!==null && offset!==undefined) atlasHealthLoad({offset});
  }
});
ATLAS.monitor={open:()=>atlasMonitorDrawer(),activity:()=>atlasHealth.activity,events:()=>atlasHealth.events,refresh:atlasHealthLoad};
