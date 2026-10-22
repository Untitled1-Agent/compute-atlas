'use strict';
/* Evidence joins use explicit project IDs and company role records. An archive
   company association is a discovery aid, never a newly asserted role. */
const connectionState={q:'',company:'all',site:'all',kind:'all',topic:'commercial',page:0};
function connectionProjectCompanies(s){return [...new Set([...(s?.company_ids||[]),...primaryRelationships(s).map(r=>r.company_id)])];}
function connectionRecords(){
  const rows=[];
  for(const s of D.sites){
    for(const r of atlasResearchProfile(s).rows){
      if(r.kind!=='relationships'&&!['commercial','finance'].includes(atlasResearchTopic(r)))continue;
      rows.push({id:r.id,kind:r.kind==='relationships'?'role':'disclosure',topic:atlasResearchTopic(r),site_id:s.id,
        company_ids:r.kind==='relationships'?[r.company_id]:connectionProjectCompanies(s),title:atlasResearchLabel(r),
        value:atlasResearchPlainValue(r),date:r.as_of||null,source_ids:[r.source_id],primary:true,row:r,
        association:r.kind==='relationships'?'Source-reported company role':'Project association; read the claim for its counterparties'});
    }
  }
  for(const c of D.contracts)rows.push({id:c.id,kind:'contract',topic:'commercial',site_id:null,company_ids:c.company_ids,
    title:c.vendor+' → '+c.counterparty,value:[c.capacity_type,c.status,c.price_basis,c.near_term,c.overlap_note].join(' '),
    date:null,source_ids:ids(c.sources),primary:false,row:c,association:'Archived commercial record; no project allocation inferred'});
  return rows;
}
function connectionRows(){const st=connectionState,q=inventoryText(st.q).trim().split(/\s+/).filter(Boolean);
  return connectionRecords().filter(r=>(st.topic==='all'||r.topic===st.topic)&&(st.company==='all'||r.company_ids.includes(st.company))
    &&(st.site==='all'||r.site_id===st.site)&&(st.kind==='all'||r.kind===st.kind)
    &&q.every(x=>inventoryText([r.title,r.value,site(r.site_id)?.name,...r.company_ids.map(id=>company(id)?.name),r.row.qualifier,r.row.source_locator,...r.source_ids.map(id=>r.primary?primarySource(id)?.title:source(id)?.title)].join(' ')).includes(x)))
    .sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||a.title.localeCompare(b.title)||a.id.localeCompare(b.id));
}
function connectionURL(){const p=new URLSearchParams();for(const [k,v] of Object.entries(connectionState))if(v&&v!=='all'&&!(k==='topic'&&v==='commercial'))p.set(k,String(v));if(connectionState.topic==='all')p.set('topic','all');return '#contracts'+(p.size?'?'+p:'');}
function connectionGo(patch={},replace=false){clearTimeout(connectionTimer);closeDrawer();if(state.tour>=0)endTour();Object.assign(connectionState,{page:0},patch);state.view='contracts';history[replace?'replaceState':'pushState'](null,'',connectionURL());render();window.scrollTo({top:0,behavior:'instant'});}
function connectionCard(r){
  const project=site(r.site_id);
  return `<article class="connection-card" data-connection-record="${esc(r.id)}"><header><span class="eyebrow">${({role:'DISCLOSED ROLE',disclosure:r.topic==='finance'?'FINANCING DISCLOSURE':'COMMERCIAL DISCLOSURE',contract:'ARCHIVED CONTRACT'})[r.kind]}</span><time>${esc(r.date||'Claim date not supplied')}</time></header>
  ${project?`<button class="text-button" data-atlas-action="campus" data-id="${esc(project.id)}">${esc(project.name)} · ${esc(project.location)} →</button>`:''}
  ${r.primary?atlasResearchClaim(r.row):`<h3>${esc(r.title)}</h3><p>${esc(r.row.capacity_type)} · ${esc(r.row.status)}</p><dl><div><dt>Referenced capacity</dt><dd>${r.row.capacity_gw==null?'Not disclosed':fmt(r.row.capacity_gw,3)+' GW'}</dd></div><div><dt>Nominal value</dt><dd>${r.row.contract_value_b==null?'Not disclosed':money(r.row.contract_value_b)}</dd></div><div><dt>Term</dt><dd>${r.row.term_years==null?'Not disclosed':fmt(r.row.term_years)+' years'}</dd></div></dl><p>${esc(r.row.price_basis)}</p><p>${esc(r.row.near_term)}</p><small>${esc(r.row.overlap_note)}</small>${srefs(r.source_ids)}<button class="text-button" data-action="contract" data-id="${esc(r.id)}">Full contract record →</button>`}
  <footer><span>${esc(r.association)}</span><div>${r.company_ids.map(id=>`<button class="text-button" data-action="company" data-id="${esc(id)}">${esc(company(id)?.name||id)} →</button>`).join('')}</div></footer></article>`;
}
function connectionGraph(rows){
  const roles=rows.filter(r=>r.kind==='role'),visible=roles.slice(0,12);
  if(!roles.length)return '';
  return `<section class="connection-graph" aria-label="Source-reported company to project roles"><header><div><div class="eyebrow">COMPANY → DISCLOSED ROLE → PROJECT</div><h2>Who does what.</h2></div><span>${roles.length} matching role records${roles.length>12?' · first 12 shown':''}</span></header><div>${visible.map(r=>`<div class="connection-edge"><button data-connection-company="${esc(r.row.company_id)}">${esc(company(r.row.company_id)?.name||r.row.company_id)}</button><span><small>${esc(r.row.role)}</small><i aria-hidden="true"></i>${primaryRef(r.row.source_id)}</span><button data-connection-site="${esc(r.site_id)}">${esc(site(r.site_id)?.name)}<small>${esc(r.date||'Undated')}</small></button></div>`).join('')}</div><p>Each line has a cited role. Selecting either end filters the evidence below. Service contracts and project investment statements retain their own boundaries.</p></section>`;
}
function connectionList(rows=connectionRows()){
  const size=16,pages=Math.max(1,Math.ceil(rows.length/size));connectionState.page=Math.min(connectionState.page,pages-1);
  return `<p class="connection-count" role="status">${rows.length} matching records · ${rows.filter(r=>r.kind==='role').length} roles · ${rows.filter(r=>r.kind==='disclosure').length} disclosures · ${rows.filter(r=>r.kind==='contract').length} archived contracts</p>${connectionGraph(rows)}<div class="connection-grid">${rows.slice(connectionState.page*size,(connectionState.page+1)*size).map(connectionCard).join('')||'<div class="empty"><h2>No matching evidence.</h2><p>Broaden the company, project, category or search terms.</p><button class="btn" data-connection-reset>Clear filters</button></div>'}</div><div class="operator-pagination"><button class="btn small" data-connection-page="-1" ${connectionState.page===0?'disabled':''}>← Previous</button><span>Page ${connectionState.page+1} of ${pages}</span><button class="btn small" data-connection-page="1" ${connectionState.page>=pages-1?'disabled':''}>Next →</button></div>`;
}
function connectionExport(rows=connectionRows()){
  const primaryIds=new Set(rows.filter(r=>r.primary).flatMap(r=>r.source_ids)),archiveIds=new Set(rows.filter(r=>!r.primary).flatMap(r=>r.source_ids));
  return {published_at:ATLAS_PRIMARY.published_at,filters:{...connectionState},policy:'Roles, project disclosures and archived contracts are independent source records. Project company associations do not assert a role. Values are not additive. No private notes included.',records:rows.map(r=>({kind:r.kind,topic:r.topic,association:r.association,record:r.row})),primary_sources:[...primaryIds].map(primarySource).filter(Boolean),archive_sources:[...archiveIds].map(source).filter(Boolean)};
}
const connectionOldContracts=contractsView;
contractsView=function(){
  return pagehead('CONTRACTS & CONNECTIONS','Follow the companies.<br>Read the commitments.','Explore the cited roles, commercial terms and financing behind named projects. Source dates and financial boundaries stay attached to every claim.',`<button class="btn" data-connection-export>Export cited selection ↓</button>`)
    +`<div class="connection-filters"><label>Search evidence<input type="search" id="connection-query" value="${esc(connectionState.q)}" placeholder="Lease, credit support, cooling, partner…" maxlength="500"></label><label>Company / project association<select id="connection-company"><option value="all">All companies</option>${D.companies.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(c=>`<option value="${c.id}" ${connectionState.company===c.id?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label><label>Project<select id="connection-site"><option value="all">All projects</option>${D.sites.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(s=>`<option value="${s.id}" ${connectionState.site===s.id?'selected':''}>${esc(s.name)} · ${esc(s.owner_label)}</option>`).join('')}</select></label><label>Topic<select id="connection-topic">${[['commercial','Commercial & roles'],['finance','Investment & financing'],['all','All topics']].map(([v,t])=>`<option value="${v}" ${connectionState.topic===v?'selected':''}>${t}</option>`).join('')}</select></label><label>Record type<select id="connection-kind">${[['all','All records'],['role','Disclosed roles'],['disclosure','Project disclosures'],['contract','Archived contracts']].map(([v,t])=>`<option value="${v}" ${connectionState.kind===v?'selected':''}>${t}</option>`).join('')}</select></label><button class="text-button" data-connection-reset>Reset</button></div><section id="connection-results">${connectionList()}</section><details class="connection-archive"><summary>Original contract table & illustrative chain</summary>${connectionOldContracts()}</details>`;
};
function companyEvidence(c){
  if(!c)return '';
  const projects=D.sites.filter(s=>connectionProjectCompanies(s).includes(c.id));
  const facts=projects.flatMap(s=>atlasResearchProfile(s).rows.map(r=>({...r,project:s}))).sort(atlasResearchDateOrder);
  const commercial=connectionRecords().filter(r=>r.company_ids.includes(c.id));
  return `<section class="company-evidence"><div class="eyebrow">CONNECTED PROJECT RESEARCH</div><h2>${projects.length} projects. ${facts.length} cited claims.</h2><p>Projects associated with ${esc(c.name)} in the archive or a disclosed role. A project’s claim may concern another counterparty; each statement retains its source.</p><div class="company-evidence-actions"><button class="btn" data-company-connections="${esc(c.id)}">Explore ${commercial.length} commercial & finance records →</button><button class="btn" data-company-inventory="${esc(c.id)}">Browse project directory →</button></div>
  <div class="company-project-links">${projects.map(s=>`<button data-atlas-action="campus" data-id="${esc(s.id)}"><strong>${esc(s.name)}</strong><span>${esc(s.location)}</span><small>${primaryRelationships(s).filter(r=>r.company_id===c.id).map(r=>esc(r.role)).join(' · ')||'Archived project association'}</small></button>`).join('')||'<p>No named project is linked in the accepted collection.</p>'}</div>
  ${facts.length?`<h3>Recent project disclosures</h3>${facts.slice(0,4).map(r=>`<div class="company-evidence-claim"><button class="text-button" data-atlas-action="campus" data-id="${esc(r.project.id)}">${esc(r.project.name)} →</button>${atlasResearchClaim(r)}</div>`).join('')}`:''}</section>`;
}
const connectionOldCompany=companyDossier;
companyDossier=function(c){return connectionOldCompany(c)+companyEvidence(c);};
const connectionOldInvestment=investmentView;
investmentView=function(){const c=company(state.invest),rows=connectionRecords().filter(r=>r.topic==='finance'&&r.company_ids.includes(c?.id));
  return connectionOldInvestment()+`<section class="investment-project-evidence"><div class="panel-head"><div><div class="eyebrow">PRIMARY PROJECT DISCLOSURES</div><h2>Capital at the project level.</h2><p>${rows.length} financing disclosures associated with ${esc(c?.name||'this company')}. Project investment is separate from consolidated capex and market value.</p></div><button class="btn" data-company-finance="${esc(c?.id)}">Explore cited financing →</button></div><div class="connection-grid">${rows.slice(0,4).map(connectionCard).join('')||'<p>No accepted project financing claim for this association. The company’s archived financial context remains available above.</p>'}</div></section>`;
};
function connectionUpdate(){if(state.view!=='contracts')return;connectionState.page=0;$('#connection-results').innerHTML=connectionList();history.replaceState(null,'',connectionURL());}
let connectionTimer;
document.addEventListener('input',e=>{if(e.target.id==='connection-query'){connectionState.q=e.target.value;clearTimeout(connectionTimer);connectionTimer=setTimeout(connectionUpdate,120);}});
document.addEventListener('change',e=>{const key={'connection-company':'company','connection-site':'site','connection-topic':'topic','connection-kind':'kind'}[e.target.id];if(key){connectionState[key]=e.target.value;connectionUpdate();}});
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b||b.disabled)return;
  if(b.hasAttribute('data-connection-company'))connectionGo({company:b.dataset.connectionCompany});
  if(b.hasAttribute('data-connection-site'))connectionGo({site:b.dataset.connectionSite});
  if(b.hasAttribute('data-connection-reset'))connectionGo({q:'',company:'all',site:'all',kind:'all',topic:'commercial'});
  if(b.hasAttribute('data-connection-export'))download('compute-atlas-connections.json',connectionExport());
  if(b.hasAttribute('data-connection-page')){connectionState.page+=Number(b.dataset.connectionPage);$('#connection-results').innerHTML=connectionList();history.replaceState(null,'',connectionURL());$('#connection-results').scrollIntoView({block:'start'});}
  if(b.hasAttribute('data-company-connections')||b.hasAttribute('data-company-finance'))connectionGo({company:b.dataset.companyConnections||b.dataset.companyFinance,site:'all',q:'',kind:'all',topic:b.hasAttribute('data-company-finance')?'finance':'all'});
  if(b.hasAttribute('data-company-inventory'))inventoryGo({collection:'projects',q:'',operator:'',company:b.dataset.companyInventory,country:'all',coverage:'all',selected:null});
});
const connectionBaseRoute=routeFromHash;window.removeEventListener('hashchange',connectionBaseRoute);
routeFromHash=function(){if(window.ATLAS_BOOTSTRAPPING)return;const [path,q='']=location.hash.slice(1).split('?');if(path==='contracts'){
  const p=new URLSearchParams(q);Object.assign(connectionState,{q:(p.get('q')||'').slice(0,500),company:company(p.get('company'))?p.get('company'):'all',site:site(p.get('site'))?p.get('site'):'all',kind:['role','disclosure','contract'].includes(p.get('kind'))?p.get('kind'):'all',topic:['finance','all'].includes(p.get('topic'))?p.get('topic'):'commercial',page:Math.max(0,Math.min(1000,parseInt(p.get('page'))||0))});
  navigate('contracts',{hash:true});return;
}connectionBaseRoute();};window.addEventListener('hashchange',routeFromHash);
ATLAS.connections={state:connectionState,records:connectionRecords,rows:connectionRows,go:connectionGo,export:connectionExport};
// Source and company drawers are overlays on these filtered workspaces. Closing
// them must restore the complete discovery URL, not just the destination name.
let connectedDrawerReturn=null;
const connectedOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts={}){
  if(!state.drawer&&['inventory','contracts'].includes(state.view))connectedDrawerReturn={view:state.view,url:state.view==='inventory'?inventoryURL():connectionURL()};
  connectedOpenDrawer(kind,id,opts);
};ATLAS.openDrawer=openDrawer;
const connectedCloseDrawer=closeDrawer;
closeDrawer=function(){const wasOpen=!$('#drawer').hidden,back=connectedDrawerReturn;connectedCloseDrawer();if(wasOpen){connectedDrawerReturn=null;if(back&&state.view===back.view)history.replaceState(null,'',back.url);}};
const connectedNavigate=navigate;
navigate=function(view,opts={}){connectedNavigate(view,opts);if(!opts.hash&&state.view===view&&['inventory','contracts'].includes(view))history.replaceState(null,'',view==='inventory'?inventoryURL():connectionURL());};ATLAS.navigate=navigate;
if(!window.ATLAS_BOOTSTRAPPING)routeFromHash();
