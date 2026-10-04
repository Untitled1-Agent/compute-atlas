
// Keep the analyst's current snapshot stable until they explicitly apply a new
// reviewed publication. Source acquisition alone cannot trigger this notice.
let atlasPublicationPending=null,atlasPublicationBusy=false,atlasPublicationError=null;
let atlasPublicationETag=ATLAS_PRIMARY.publication_hash ? '"'+ATLAS_PRIMARY.publication_hash+'"' : null;
function atlasValidatePublication(data) {
  if (!data || typeof data.publication_hash!=='string' || !/^[a-f0-9]{64}$/.test(data.publication_hash)
      || !Array.isArray(data.sources) || !ATLAS_EVIDENCE_KINDS.every(k=>Array.isArray(data[k]))) throw Error('Invalid reviewed publication');
  const sources=new Set(data.sources.map(s=>s.id)),ids=new Set();
  for (const kind of ATLAS_EVIDENCE_KINDS) for (const row of data[kind]) {
    if (!row.id || ids.has(row.id) || row.review_status!=='accepted' || !sources.has(row.source_id) || !site(row.site_id)) throw Error('Invalid publication claim');
    ids.add(row.id);
    if (kind==='observations' && row.value!==null && (typeof row.value!=='number' || !Number.isFinite(row.value) || row.value<0)) throw Error('Invalid publication quantity');
  }
  return data;
}
function atlasPublicationNotice() {
  let banner=document.getElementById('atlas-publication-update');
  if (!banner) {banner=document.createElement('section');banner.id='atlas-publication-update';banner.className='atlas-publication-update';banner.setAttribute('aria-label','Reviewed publication status');document.querySelector('.app-shell').prepend(banner);}
  banner.hidden=!atlasPublicationPending&&!atlasPublicationError;
  if (atlasPublicationPending) banner.innerHTML=`<span role="status"><b>A reviewed publication is available.</b> Dated ${esc(atlasPublicationPending.published_at)}. Your current view is unchanged until you apply it.</span><button class="btn primary" data-service-publication="apply">Apply reviewed update ↻</button>`;
  else if (atlasPublicationError) banner.innerHTML='<span role="status">The reviewed-publication check is unavailable. Your last loaded evidence remains visible with its original dates.</span><button class="btn" data-service-publication="check">Retry publication check ↻</button>';
  else banner.replaceChildren();
}
async function pollAtlasPublication() {
  if (!globalThis.ATLAS_SERVICE || atlasPublicationBusy) return;
  atlasPublicationBusy=true;
  try {
    const response=await fetch(ATLAS_SERVICE.base+'/publication',{cache:'no-cache',headers:atlasPublicationETag?{'If-None-Match':atlasPublicationETag}:{},signal:AbortSignal.timeout(8000)});
    if (response.status===304) {atlasPublicationError=null;return;}
    if (!response.ok) throw Error('Publication HTTP '+response.status);
    const data=atlasValidatePublication(await response.json());
    // Only advance the validator after a complete, valid response.
    atlasPublicationETag='"'+data.publication_hash+'"';
    atlasPublicationPending=data.publication_hash===ATLAS_PRIMARY.publication_hash ? null : data;
    atlasPublicationError=null;
  } catch(error) {atlasPublicationError=String(error.message||error);}
  finally {atlasPublicationBusy=false;atlasPublicationNotice();}
}
function applyAtlasPublication() {
  if (!atlasPublicationPending) return;
  const update=atlasValidatePublication(atlasPublicationPending),scroll=window.scrollY;
  // Preserve archive, selection, filters, local shelf and private notes. Only the
  // explicitly reviewed overlay is replaced; no numerical merge is performed.
  Object.keys(ATLAS_PRIMARY).forEach(key=>delete ATLAS_PRIMARY[key]);Object.assign(ATLAS_PRIMARY,update);
  atlasPublicationPending=null;atlasPublicationError=null;globalThis.ATLAS_SERVICE_WARNING=false;
  document.querySelector('.atlas-service-warning')?.remove();
  const stamp=document.querySelector('.top-date b');
  if(stamp)stamp.textContent=String(update.published_at);
  const drawer=state.drawer;render();updateMonitorLabel();atlasPublicationNotice();
  if(drawer?.kind==='evidence')openDrawer('evidence',drawer.id,{back:true});
  else if(drawer?.kind==='primary-source')openDrawer('primary-source',drawer.id,{back:true});
  else if(drawer?.kind==='site')openDrawer('site',drawer.id,{back:true});
  window.scrollTo({top:scroll,behavior:'instant'});
  toast('Reviewed publication applied. Your research context and notes were retained.');
}
document.addEventListener('click',event=>{
  const action=event.target.closest('[data-service-publication]')?.dataset.servicePublication;
  if(action==='apply')applyAtlasPublication();
  if(action==='check')pollAtlasPublication();
});
ATLAS.publication={check:pollAtlasPublication,apply:applyAtlasPublication,pending:()=>atlasPublicationPending};
if(globalThis.ATLAS_SERVICE){pollAtlasPublication();setInterval(()=>{if(!document.hidden)pollAtlasPublication();},300000);}
