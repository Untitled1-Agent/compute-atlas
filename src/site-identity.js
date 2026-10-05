'use strict';
/* Source-locality review never mutates D.sites or certifies an archive pin.
   Multiple effective sources remain separate; there is no proximity deduplication. */
const atlasIdentityPolicy='Source-established identities and localities are separate from historical map anchors. Matching anchors do not establish a common campus. No surveyed coordinates, parcel boundaries, building geometry or capacity total is supplied.';
const atlasIdentityPrecision={municipality:'Municipality',county_or_parish:'County / parish',region:'Region',country:'Country'};
function atlasIdentityValid(row,sources=ATLAS_PRIMARY.sources) {
  const x=row?.identity,keys=['canonical_name','place','place_precision','project_scope','coordinate_evidence','related_sites'];
  const text=v=>typeof v==='string'&&v.trim().length>0;
  const date=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;
  if(!x||typeof x!=='object'||Object.keys(x).length!==keys.length||!keys.every(k=>Object.hasOwn(x,k)))return false;
  if(!text(x.canonical_name)||x.canonical_name.length>400||!text(x.place)||x.place.length>400
    ||typeof x.place_precision!=='string'||!Object.hasOwn(atlasIdentityPrecision,x.place_precision)||x.project_scope!=='campus'||x.coordinate_evidence!=='not_established'
    ||!date(row.as_of)||!date(row.reviewed_at)||row.reviewed_at<row.as_of||!sources.some(s=>s.id===row.source_id)
    ||!Array.isArray(x.related_sites)||x.related_sites.length>20)return false;
  const ids=new Set();
  return x.related_sites.every(r=>{if(!r||Object.keys(r).length!==4||!['site_id','relation','source_id','note'].every(k=>text(r[k]))
      ||r.site_id===row.site_id||ids.has(r.site_id)||!site(r.site_id)||r.relation!=='adjacent_project'||r.note.length>2000||!sources.some(s=>s.id===r.source_id))return false;ids.add(r.site_id);return true;});
}
function atlasIdentityRows(s) {return primaryFacts(s).filter(r=>r.identity&&atlasIdentityValid(r)).sort((a,b)=>a.id.localeCompare(b.id));}
function atlasSharedArchiveAnchors(s) {
  return s&&spatialFinite(s.lat)&&spatialFinite(s.lon)?D.sites.filter(other=>other.id!==s.id&&other.lat===s.lat&&other.lon===s.lon).sort((a,b)=>a.id.localeCompare(b.id)):[];
}
function atlasIdentityExport(s) {
  if(!s)return null;
  const rows=atlasIdentityRows(s),ids=new Set(rows.map(r=>r.source_id));
  rows.forEach(r=>r.identity.related_sites.forEach(link=>ids.add(link.source_id)));
  return {schema_version:1,site_id:s.id,policy:atlasIdentityPolicy,identity_claims:rows,
    sources:[...ids].sort().map(primarySource).filter(Boolean),
    archive_anchor:{latitude:spatialFinite(s.lat)?s.lat:null,longitude:spatialFinite(s.lon)?s.lon:null,
      location:s.location,precision:s.coordinate_precision,basis:'historical_archive',source_verified:false},
    shared_archive_anchors:atlasSharedArchiveAnchors(s).map(({id,name,country})=>({id,name,country})),surveyed_geometry:null};
}
function atlasIdentityLaunch(s) {
  const rows=atlasIdentityRows(s);
  return `<div class="atlas-identity-launch"><span class="atlas-card-kicker">IDENTITY & LOCATION</span><p>${rows.length===1?esc(rows[0].identity.place):rows.length?'Multiple source-established descriptions':'Locality review not yet available'}</p><button class="text-button" data-identity-open="${esc(s.id)}">${rows.length?'Inspect source & map precision':'Inspect archival map precision'} <span aria-hidden="true">↗</span></button></div>`;
}
function atlasIdentityClaimCard(row) {
  const x=row.identity,src=primarySource(row.source_id);
  return `<article class="atlas-identity-claim" data-identity-claim="${esc(row.id)}"><header><span class="atlas-card-kicker">SOURCE-ESTABLISHED IDENTITY</span>${primaryRef(row.source_id)}</header><h2>${esc(x.canonical_name)}</h2><p class="atlas-identity-place">${esc(x.place)}</p><dl><div><dt>Locality precision</dt><dd>${esc(atlasIdentityPrecision[x.place_precision])}</dd></div><div><dt>Record scope</dt><dd>Campus, not individual building positions</dd></div><div><dt>Reported</dt><dd>${esc(row.as_of)}</dd></div><div><dt>Identity reviewed</dt><dd>${esc(row.reviewed_at)}</dd></div></dl><p>${esc(row.qualifier)}</p><footer>${esc(src?.publisher||'Unknown publisher')} · <code>${esc(row.id)}</code></footer>${x.related_sites.length?`<section class="atlas-identity-related"><h3>Separately identified adjacent project</h3>${x.related_sites.map(link=>`<article><button class="text-button" data-identity-open="${esc(link.site_id)}">${esc(site(link.site_id)?.name||link.site_id)} ↗</button><p>${esc(link.note)}</p>${primaryRef(link.source_id)}</article>`).join('')}</section>`:''}</article>`;
}
function atlasIdentityDrawer(s) {
  if(!s)return '<section class="atlas-identity-desk"><h1>Site not found.</h1><p>No identity or location is inferred for this record.</p></section>';
  const data=atlasIdentityExport(s),rows=data.identity_claims,a=data.archive_anchor;
  const invalid=primaryFacts(s).filter(r=>r.identity&&!atlasIdentityValid(r)).length;
  return `<section class="atlas-identity-desk" data-identity-site="${esc(s.id)}"><div class="atlas-eyebrow">PLACE ≠ PARCEL ≠ BUILDING</div><h1>${esc(s.name)}<br><span>Identity & location.</span></h1><p class="atlas-identity-intro">Know which project you are looking at—and how precisely it can be placed on the map.</p><div class="atlas-identity-boundary">A named place is not a surveyed pin. Source-backed identity is shown beside, not substituted for, the original map context.</div><div class="atlas-identity-toolbar"><span>${rows.length} current identity ${rows.length===1?'claim':'claims'} · ${new Set(rows.map(r=>r.source_id)).size} identity ${new Set(rows.map(r=>r.source_id)).size===1?'source':'sources'}</span><button class="btn small" data-identity-export="${esc(s.id)}">Export cited identity ↓</button></div>${invalid?'<p class="notice" role="alert">An identity record failed schema validation and is not displayed. The archival context is retained.</p>':''}<div class="atlas-identity-columns"><div>${rows.map(atlasIdentityClaimCard).join('')||'<article class="atlas-identity-claim"><h2>Not yet source-reviewed.</h2><p>The loaded publication does not establish this project’s identity and locality in the typed review layer. That does not mean the facility is absent.</p></article>'}</div><aside class="atlas-identity-anchor"><span class="atlas-card-kicker">ARCHIVE MAP CONTEXT / UNVERIFIED PIN</span><h2>Approximate anchor.</h2><p>${esc(a.location||'Location not resolved')}</p><div class="atlas-identity-coordinates">${a.latitude===null||a.longitude===null?'Not mapped':esc(a.latitude+'°, '+a.longitude+'°')}</div><p>${esc(a.precision||'Precision not recorded')}</p><dl><div><dt>Source of coordinates</dt><dd>Original research archive</dd></div><div><dt>Verified by identity source</dt><dd>No</dd></div><div><dt>Surveyed parcel / buildings</dt><dd>Not supplied</dd></div></dl><p>Coordinates stay unchanged. No geocoding, campus boundary or building outline is inferred from a publisher’s place name.</p></aside></div>${data.shared_archive_anchors.length?`<section class="atlas-identity-collision"><span class="atlas-card-kicker">SHARED ARCHIVAL PIN / NOT A MERGE</span><h2>Different records can share one map anchor.</h2><p>${data.shared_archive_anchors.length} other ${data.shared_archive_anchors.length===1?'record uses':'records use'} this exact archival point. A shared archival approximation is not proof of common ownership, buildings or additive power.</p>${data.shared_archive_anchors.map(r=>`<button class="btn" data-identity-open="${esc(r.id)}">${esc(r.name)} ↗</button>`).join('')}</section>`:''}<footer class="atlas-identity-footer"><button class="text-button" data-identity-dossier="${esc(s.id)}">Open complete facility dossier →</button><button class="text-button" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">Review quantities & revision history ↗</button><p>Identity source dates and editorial reviews are not source-fetch timestamps or operating-status updates.</p></footer></section>`;
}
const atlasIdentityPreviousAttributes=atlasAttributes;
atlasAttributes=function(s){return atlasIdentityPreviousAttributes(s).replace('</section>',atlasIdentityLaunch(s)+'</section>');};
const atlasIdentityPreviousDrawer=openDrawer;
openDrawer=function(kind,id,options={}) {
  atlasIdentityPreviousDrawer(kind,id,options);
  if(kind==='site'&&site(id))$('#drawer-content').insertAdjacentHTML('afterbegin',`<button class="atlas-dossier-map-link" data-identity-open="${esc(id)}">Inspect source identity & map precision ↗</button>`);
  if(kind==='identity'){$('#drawer-type').textContent='SITE IDENTITY / LOCATION PRECISION';$('#drawer-content').innerHTML=atlasIdentityDrawer(site(id));}
};
const atlasIdentityPreviousDossier=atlasCitedDossier;
atlasCitedDossier=function(s){return {...atlasIdentityPreviousDossier(s),identity_evidence:atlasIdentityExport(s)};};
const atlasIdentityPreviousValidator=atlasValidatePublication;
atlasValidatePublication=function(data) {
  const checked=atlasIdentityPreviousValidator(data);
  for(const kind of ATLAS_EVIDENCE_KINDS)for(const row of checked[kind])if(Object.hasOwn(row,'identity')&&(kind!=='facts'||!atlasIdentityValid(row,checked.sources)))throw Error('Invalid reviewed site identity');
  return checked;
};
document.addEventListener('click',event=>{
  const open=event.target.closest('[data-identity-open]');
  if(open)openDrawer('identity',open.dataset.identityOpen);
  const exp=event.target.closest('[data-identity-export]');
  if(exp){const s=site(exp.dataset.identityExport);if(s)download('compute-atlas-identity-'+s.id+'.json',atlasIdentityExport(s));}
  const dossier=event.target.closest('[data-identity-dossier]');
  if(dossier)openDrawer('site',dossier.dataset.identityDossier);
});
ATLAS.openDrawer=openDrawer;
ATLAS.evidence.export=atlasCitedDossier;
ATLAS.identity={open:id=>openDrawer('identity',id),rows:atlasIdentityRows,export:atlasIdentityExport,sharedAnchors:atlasSharedArchiveAnchors};
if(['overview','globe'].includes(state.view))render();
