'use strict';
/* Read-only analysis of the publication, not a second source of numerical truth. */
const ATLAS_EVIDENCE_KINDS = ['observations','facts','relationships'];
let atlasDeskFilter = 'all', atlasDeskQuery = '';
function atlasEvidenceRows(s) {
  if (!s) return [];
  const current = ATLAS_EVIDENCE_KINDS.flatMap(kind => effectivePrimary(ATLAS_PRIMARY[kind] || [])
    .filter(row => row.site_id === s.id).map(row => ({...row,kind,effective:true})));
  const ids = new Set(current.map(row => row.id));
  const historical = ATLAS_EVIDENCE_KINDS.flatMap(kind => [
    ...(ATLAS_PRIMARY.revision_history?.[kind] || []), ...(ATLAS_PRIMARY[kind] || [])
  ].filter(row => row.site_id === s.id && !ids.has(row.id) && ['accepted','rejected'].includes(row.review_status))
    .map(row => ({...row,kind,effective:false})));
  return [...new Map([...current,...historical].map(row => [row.id,row])).values()]
    .sort((a,b) => String(b.as_of || '').localeCompare(String(a.as_of || '')) || a.id.localeCompare(b.id));
}
function atlasCitedDossier(s) {
  const rows = atlasEvidenceRows(s);
  const history = Object.fromEntries(ATLAS_EVIDENCE_KINDS.map(kind => [kind,rows.filter(r => r.kind === kind && !r.effective)
    .map(({kind,effective,...row}) => row)]));
  return {
    publication_date:ATLAS_PRIMARY.published_at, publication_hash:ATLAS_PRIMARY.publication_hash || null,
    archive:s, primary_observations:primaryObservations(s), primary_facts:primaryFacts(s),
    primary_relationships:primaryRelationships(s), revision_history:history,
    primary_sources:[...new Set(rows.map(r => r.source_id))].map(primarySource).filter(Boolean),
    archival_sources:(s.sources || []).map(source).filter(Boolean), private_note:saved.notes[s.id] || '',
    policy:ATLAS_PRIMARY.policy,
    revision_policy:'Earlier and rejected revisions are audit context, not current values or additional capacity. Archive estimates remain separate from issuer disclosures.'
  };
}
function atlasEvidenceCard(row) {
  const quantity = row.kind === 'observations', relation = row.kind === 'relationships';
  const title = quantity ? boundaryLabel(row.boundary) : relation ? row.role : row.label;
  const value = quantity ? observationValue(row)+(row.value === null ? '' : ' <small>'+esc(row.unit)+'</small>')
    : esc(relation ? company(row.company_id)?.name || row.company_id : row.value);
  const scope = row.scope || (relation ? 'Source-scoped counterparty role' : row.label);
  const label = row.effective ? 'Current publication' : row.review_status === 'rejected' ? 'Withdrawn interpretation' : 'Earlier revision · not current';
  return `<article class="atlas-evidence-record ${row.effective?'':'historical'}" data-claim-id="${esc(row.id)}">
    <div class="atlas-evidence-record-head"><span class="atlas-card-kicker">${esc(title)}</span><span class="atlas-revision-state">${label}</span></div>
    <h3>${value}</h3><p class="atlas-claim-scope">${esc(scope)}${primaryIsContext(row)?' · WIDER CONTEXT / NOT A PROJECT TOTAL':''}</p>
    <dl><div><dt>Reported</dt><dd>${esc(row.as_of || 'Date not stated')}</dd></div><div><dt>Status</dt><dd>${esc(statusLabel(row.status || 'disclosed'))}</dd></div>${row.period?`<div><dt>Applies to</dt><dd>${esc(row.period)}</dd></div>`:''}</dl>
    ${row.qualifier?`<p class="atlas-claim-qualifier">${esc(row.qualifier)}</p>`:''}
    ${row.source_locator?`<details><summary>Find the claim in the source</summary><p>${esc(row.source_locator)}</p></details>`:''}
    ${row.supersedes?`<p class="atlas-revision-link">Replaces <code>${esc(row.supersedes)}</code>. Prior values are not added.</p>`:''}
    <footer>${primaryRef(row.source_id)}<details><summary>Record identity</summary><code>${esc(row.id)}</code></details></footer>
  </article>`;
}
function atlasDeskResults(s) {
  const rows = atlasEvidenceRows(s), query = atlasDeskQuery.trim().toLocaleLowerCase();
  const visible = rows.filter(row => (atlasDeskFilter === 'all' ? row.effective : atlasDeskFilter === 'history' ? !row.effective : row.effective && row.kind === atlasDeskFilter)
    && (!query || [row.scope,row.label,row.value,row.role,row.qualifier,row.id,row.source_id,row.boundary,company(row.company_id)?.name]
      .filter(v => v != null).join(' ').toLocaleLowerCase().includes(query)));
  $('#atlas-desk-count').textContent = visible.length+' '+(visible.length===1?'record':'records')+' shown · '+(atlasDeskFilter==='history'?'audit history, not additional capacity':'current reviewed publication');
  $('#atlas-desk-records').innerHTML = visible.map(atlasEvidenceCard).join('') || '<div class="atlas-desk-empty"><h2>No matching reviewed records.</h2><p>This is not a zero capacity value. Clear the search or inspect the original archival dossier.</p></div>';
  document.querySelectorAll('[data-evidence-filter]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.evidenceFilter === atlasDeskFilter)));
}
function atlasEvidenceDesk(s) {
  if (!s) return '<p>Site not found.</p>';
  const rows = atlasEvidenceRows(s), current = rows.filter(r => r.effective), history = rows.filter(r => !r.effective);
  return `<section class="atlas-evidence-desk" data-site="${esc(s.id)}">
    <div class="atlas-eyebrow">SOURCE → CLAIM → REVIEW → PUBLICATION</div><h1>${esc(s.name)}<br><span>Evidence desk.</span></h1>
    <p>${esc(s.location)} · publication reviewed ${esc(ATLAS_PRIMARY.published_at)}. A source date is not live telemetry.</p>
    <div class="atlas-desk-summary"><div><strong>${current.length}</strong><span>Current records</span></div><div><strong>${new Set(rows.map(r=>r.source_id)).size}</strong><span>Primary sources</span></div><div><strong>${history.length}</strong><span>Earlier revisions</span></div></div>
    <div class="atlas-desk-boundary">Read the scope, not just the number. Delivered, contracted, planned, utility power and native units stay separate. Overlapping quantities are never totaled here.</div>
    <div class="atlas-desk-toolbar"><label for="atlas-evidence-query">Search the evidence<input id="atlas-evidence-query" type="search" autocomplete="off" placeholder="Capacity, lease, cooling, source…" value="${esc(atlasDeskQuery)}"></label><button class="btn" data-atlas-action="export" data-id="${esc(s.id)}">Export cited dossier ↓</button></div>
    <div class="atlas-evidence-filters" role="group" aria-label="Evidence category">${[['all','All current'],['observations','Quantities'],['facts','Attributes'],['relationships','Counterparties'],['history','Earlier revisions']].map(([id,label])=>`<button data-evidence-filter="${id}" aria-pressed="${atlasDeskFilter===id}">${label}</button>`).join('')}</div>
    <p id="atlas-desk-count" role="status"></p><div id="atlas-desk-records"></div>
    <button class="text-button" data-action="site" data-id="${esc(s.id)}">Read the separate historical research dossier ↗</button>
  </section>`;
}
const atlasDeskPreviousOpen = openDrawer;
openDrawer = function(kind,id,opts={}) {
  atlasDeskPreviousOpen(kind,id,opts);
  if (kind === 'evidence') {
    if (!opts.back) {atlasDeskFilter='all';atlasDeskQuery='';}
    $('#drawer-type').textContent='EVIDENCE DESK / REVIEWED PUBLICATION';
    $('#drawer-content').innerHTML=atlasEvidenceDesk(site(id));
    if (site(id)) atlasDeskResults(site(id));
  }
  if (kind === 'primary-source') {
    const earlier = D.sites.flatMap(atlasEvidenceRows).filter(r => !r.effective && r.source_id === id);
    if (earlier.length) $('#drawer-content').insertAdjacentHTML('beforeend',`<h2>Retained revision history</h2><p>These earlier interpretations are audit context, not current quantities.</p>${earlier.map(atlasEvidenceCard).join('')}`);
  }
};
ATLAS.openDrawer = openDrawer;
ATLAS.evidence = {rows:atlasEvidenceRows,export:atlasCitedDossier,open:id=>openDrawer('evidence',id)};
document.addEventListener('click',event => {
  const launch=event.target.closest('[data-atlas-action="evidence-desk"]');
  if (launch) openDrawer('evidence',launch.dataset.id);
  const filter=event.target.closest('[data-evidence-filter]');
  if (filter) {atlasDeskFilter=filter.dataset.evidenceFilter;atlasDeskResults(site(state.drawer?.id));}
});
document.addEventListener('input',event => {
  if (event.target.id === 'atlas-evidence-query') {atlasDeskQuery=event.target.value;atlasDeskResults(site(state.drawer?.id));}
});
// Native details gives a keyboard-operable, compact toolbar without hiding active filters.
document.addEventListener('toggle',event => {
  if (event.target.isConnected && event.target.matches?.('.atlas-filter-panel')) state.spatialFiltersOpen=event.target.open;
},true);
document.addEventListener('keydown',event => {
  const panel=document.querySelector('.atlas-filter-panel[open]');
  if (event.key==='Escape' && panel && panel.contains(document.activeElement)) {
    panel.open=false;panel.querySelector('summary').focus();event.preventDefault();
  }
});
document.addEventListener('click',event => {
  const summary=event.target.closest('.atlas-filter-toggle');
  if (summary) state.spatialFiltersOpen=!summary.parentElement.open;
},true);
document.addEventListener('change',event => {
  const panel=event.target.closest('.atlas-filter-panel');
  if (panel) state.spatialFiltersOpen=panel.open;
},true);
