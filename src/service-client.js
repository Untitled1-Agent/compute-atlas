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
  if(offset!==null)pollAtlasMonitor({offset}).then(atlasMonitorDrawer);
});
// A service publication failure falls back to the checked-in evidence, not an empty graph.
if(globalThis.ATLAS_SERVICE_WARNING){
  const banner=document.createElement('div');banner.className='atlas-service-warning';banner.setAttribute('role','status');
  banner.textContent='Using the checked-in publication because the evidence API did not respond. Source dates remain visible.';
  document.querySelector('.app-shell')?.prepend(banner);
}

if(globalThis.ATLAS_SERVICE){pollAtlasMonitor({offset:0});setInterval(()=>{if(!document.hidden)pollAtlasMonitor();},300000);}
