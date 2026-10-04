'use strict';
/* Optional same-origin service. The standalone never probes a network. */
let atlasQueueOffset=0,atlasQueueNext=null,atlasQueueTotal=0,atlasMonitorBusy=false;
const monitorTime = value => value ? new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}) : 'Not yet captured';
const queueURL = value => {try {const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}};
pollAtlasMonitor = async function({offset=atlasQueueOffset}={}) {
  if(!globalThis.ATLAS_SERVICE||atlasMonitorBusy)return;
  atlasMonitorBusy=true;
  try{
    const [status,queue]=await Promise.all([
      fetch(ATLAS_SERVICE.base+'/status',{cache:'no-store',signal:AbortSignal.timeout(8000)}),
      fetch(ATLAS_SERVICE.base+'/review-queue?limit=20&offset='+Math.max(0,offset),{cache:'no-store',signal:AbortSignal.timeout(8000)})
    ]);
    if(!status.ok||!queue.ok)throw Error('Service HTTP '+(!status.ok?status.status:queue.status));
    const [s,q]=await Promise.all([status.json(),queue.json()]);
    if(!s.counts||!Array.isArray(s.jobs)||!Array.isArray(q.items))throw Error('Unexpected monitor response');
    atlasMonitorStatus=s;atlasMonitorQueue=q.items;atlasQueueNext=q.next_offset;atlasQueueTotal=q.total;atlasQueueOffset=offset;atlasMonitorError=null;
  }catch(error){atlasMonitorError=String(error.message||error);}
  finally{atlasMonitorBusy=false;updateMonitorLabel();}
};
const originalMonitorDrawer=atlasMonitorDrawer;
atlasMonitorDrawer=function(){
  originalMonitorDrawer();
  const body=$('#drawer-content');
  if(!globalThis.ATLAS_SERVICE)return;
  if(atlasMonitorError){
    const warning=document.createElement('div');warning.className='notice';warning.setAttribute('role','status');
    warning.textContent='Live monitor unavailable: '+atlasMonitorError+'. The dated publication is still usable. Any status below is from the last successful status check, not a current capture.';
    body.prepend(warning);
  }
  const old=body.querySelector('[data-atlas-action="monitor-refresh"]');
  if(old){
    let next=old.nextElementSibling;
    while(next&&!(next.tagName==='H2'&&next.textContent.startsWith('Research candidates'))){const following=next.nextElementSibling;next.remove();next=following;}
    const section=document.createElement('section');section.className='atlas-live-review';
    section.innerHTML=`<h2>Acquisition review queue</h2><p>${atlasQueueTotal} pending items · ${atlasQueueTotal?atlasQueueOffset+1:0}–${atlasQueueOffset+atlasMonitorQueue.length} shown. Acknowledging a capture does not accept a claim.</p>${atlasMonitorQueue.map(q=>{const url=queueURL(q.payload.url);return `<article class="atlas-source-observation"><div class="atlas-card-kicker">${esc(q.kind)} · ${esc(q.source_id)}</div><h3>${esc(q.payload.title||q.payload.name||'Source update')}</h3><p>${esc(q.payload.note||'Pending explicit editorial review')}</p><p>Captured ${esc(monitorTime(q.created_at))}</p>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="text-button">Read publisher source ↗</a>`:''}<p class="atlas-card-footnote">Queue ID: ${esc(q.id)}</p></article>`;}).join('')||'<div class="notice">No items pending in this page of the review queue. This is not a claim that every source is current; inspect the acquisition outcomes above.</div>'}<div class="atlas-queue-pager"><button class="btn small" data-service-page="previous" ${atlasQueueOffset===0?'disabled':''}>← Previous</button><span>${atlasQueueTotal} pending</span><button class="btn small" data-service-page="next" ${atlasQueueNext===null?'disabled':''}>Next →</button></div><h3>Explicit editorial review</h3><p>Review happens through the local command line with an actor and a reason. The public web API is read-only. Captures never automatically become published site facts.</p><pre class="atlas-command">python -m server queue
python -m server submit observation claim.json --actor analyst
python -m server review CLAIM_ID accepted --actor analyst --reason "Source and boundary checked"
python -m server export data/evidence.json</pre>`;
    old.after(section);
  }
  if(atlasMonitorStatus){
    const stamp=document.createElement('p');stamp.className='atlas-card-footnote';stamp.textContent='Status fetched '+monitorTime(atlasMonitorStatus.checked_at)+'. Worker '+(atlasMonitorStatus.background_refresh?'running':'paused')+'. Source capture time and editorial publication date are deliberately separate.';
    body.prepend(stamp);
  }
};
document.addEventListener('click',event=>{
  const button=event.target.closest('[data-service-page]');if(!button)return;
  const offset=button.dataset.servicePage==='next'?atlasQueueNext:Math.max(0,atlasQueueOffset-20);
  if(offset!==null)pollAtlasMonitor({offset}).then(()=>{if(state.drawer?.kind==='monitor'&&!$('#drawer').hidden)atlasMonitorDrawer();});
});
// A service publication failure falls back to the checked-in evidence, not an empty graph.
if(globalThis.ATLAS_SERVICE_WARNING){
  const banner=document.createElement('div');banner.className='atlas-service-warning';banner.setAttribute('role','status');
  banner.textContent='Using the checked-in publication because the evidence API did not respond. Source dates remain visible.';
  document.querySelector('.app-shell')?.prepend(banner);
}

if(globalThis.ATLAS_SERVICE){pollAtlasMonitor({offset:0});setInterval(()=>{if(!document.hidden)pollAtlasMonitor();},300000);}

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
