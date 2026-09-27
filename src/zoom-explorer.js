'use strict';
/* Six-scale semantic map explorer. Uses only the checked-in research graph.
   Exact parcel/building geometry is never inferred from the visual mockups. */

const ATLAS_SCALE_LEVELS = [
  {id:0,key:'world',label:'World',sub:'Global evidence'},
  {id:1,key:'continent',label:'Continent',sub:'Regional systems'},
  {id:2,key:'region',label:'Region',sub:'Country / market'},
  {id:3,key:'metro',label:'Metro',sub:'Local cluster'},
  {id:4,key:'campus',label:'Campus',sub:'Named project'},
  {id:5,key:'facility',label:'Facility',sub:'Evidence detail'},
];
const atlasSpatial = globalThis.AtlasSpatialMath || {};
const spatialFinite = v => typeof v === 'number' && Number.isFinite(v);
const spatialState = () => {
  if (!Number.isInteger(state.spatialLevel)) state.spatialLevel = 0;
  if (!['snapshot','target'].includes(state.spatialPhase)) state.spatialPhase = 'snapshot';
  if (!D.sites.some(s => s.id === state.spatialSelected)) state.spatialSelected = null;
  return state;
};
const spatialPower = (s,phase=spatialState().spatialPhase) => spatialFinite(s?.[phase]?.it_mw) ? s[phase].it_mw : null;
const spatialMapped = () => D.sites.filter(s => spatialFinite(s.lat) && spatialFinite(s.lon));
const spatialComparable = (s,phase=spatialState().spatialPhase) => ['reviewed-model','archive'].includes(s.review) && spatialPower(s,phase) != null;
const spatialDistance = (a,b) => atlasSpatial.distance ? atlasSpatial.distance(a,b) : (()=>{
  const r=Math.PI/180,dlat=(b.lat-a.lat)*r,dlon=(b.lon-a.lon)*r;
  const q=Math.sin(dlat/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dlon/2)**2;
  return 6371*2*Math.atan2(Math.sqrt(q),Math.sqrt(1-q));
})();

function spatialDefaultSite(){
  const st=spatialState();
  if(st.spatialSelected) return site(st.spatialSelected);
  let xs=spatialMapped();
  if(state.filter.company && state.filter.company!=='all') xs=xs.filter(s=>s.company_ids.includes(state.filter.company));
  if(state.filter.country && state.filter.country!=='all') xs=xs.filter(s=>s.country===state.filter.country);
  xs.sort((a,b)=>(spatialPower(b,'snapshot')||spatialPower(b,'target')||0)-(spatialPower(a,'snapshot')||spatialPower(a,'target')||0));
  const preferred=xs.find(s=>s.id==='amazon-anthropic-new-carlisle')||xs[0]||spatialMapped()[0];
  if(preferred) st.spatialSelected=preferred.id;
  return preferred;
}
function spatialContinent(s){
  const c=s?.country||'';
  if(['United States','Canada','Mexico'].includes(c))return 'North America';
  if(['China','Japan','South Korea','India','Singapore','Malaysia','Indonesia','Taiwan'].includes(c))return 'Asia';
  if(['United Arab Emirates','Saudi Arabia','Israel','Qatar'].includes(c))return 'Middle East';
  if(['Australia','New Zealand'].includes(c))return 'Oceania';
  if(['Brazil','Chile','Argentina','Colombia'].includes(c))return 'South America';
  if(['South Africa','Kenya','Nigeria','Egypt','Morocco'].includes(c))return 'Africa';
  return 'Europe';
}
function spatialContinentBounds(name){
  return ({
    'North America':[-170,5,-45,78], 'South America':[-90,-58,-28,16],
    'Europe':[-25,33,45,72], 'Asia':[45,-5,155,75], 'Middle East':[25,10,70,45],
    'Africa':[-22,-38,55,38], 'Oceania':[105,-50,180,5],
  })[name]||[-180,-60,180,85];
}
function spatialScope(level,selected){
  const all=spatialMapped();
  if(level===0)return {label:'Global research collection',sites:all,bounds:[-180,-60,180,85]};
  const continent=spatialContinent(selected);
  if(level===1){const xs=all.filter(s=>spatialContinent(s)===continent);return {label:continent,sites:xs,bounds:spatialContinentBounds(continent)};}
  if(level===2){const country=selected?.country||'Unknown';const xs=all.filter(s=>s.country===country);return {label:country,sites:xs,bounds:spatialFitBounds(xs,selected,8,6)};}
  if(level===3){const xs=all.filter(s=>selected&&spatialDistance(selected,s)<=650);return {label:spatialMetroLabel(selected),sites:xs,bounds:spatialFitBounds(xs,selected,3.8,2.8)};}
  if(level===4){const xs=all.filter(s=>selected&&spatialDistance(selected,s)<=140);return {label:selected?.name||'Campus',sites:xs,bounds:spatialFitBounds(xs,selected,1.1,.85)};}
  return {label:selected?.name||'Facility',sites:selected?[selected]:[],bounds:selected?[selected.lon-.16,selected.lat-.11,selected.lon+.16,selected.lat+.11]:[-1,-1,1,1]};
}
function spatialMetroLabel(s){
  if(!s)return 'Local cluster';
  const first=(s.location||'').split(',')[0].trim();
  return first ? first+' area' : 'Local cluster';
}
function spatialFitBounds(xs,selected,padLon,padLat){
  if(!xs.length&&selected)return [selected.lon-padLon,selected.lat-padLat,selected.lon+padLon,selected.lat+padLat];
  const pts=xs.length?xs:[selected].filter(Boolean); if(!pts.length)return [-180,-60,180,85];
  let minLon=Math.min(...pts.map(x=>x.lon)),maxLon=Math.max(...pts.map(x=>x.lon)),minLat=Math.min(...pts.map(x=>x.lat)),maxLat=Math.max(...pts.map(x=>x.lat));
  if(maxLon-minLon<padLon*2){const m=(minLon+maxLon)/2;minLon=m-padLon;maxLon=m+padLon}else{minLon-=padLon;maxLon+=padLon}
  if(maxLat-minLat<padLat*2){const m=(minLat+maxLat)/2;minLat=m-padLat;maxLat=m+padLat}else{minLat-=padLat;maxLat+=padLat}
  return [Math.max(-180,minLon),Math.max(-85,minLat),Math.min(180,maxLon),Math.min(85,maxLat)];
}
function spatialProject(lon,lat,bounds){
  const [x0,y0,x1,y1]=bounds;return {x:(lon-x0)/(x1-x0)*100,y:(1-(lat-y0)/(y1-y0))*100};
}
function spatialPath(line,bounds){
  return line.map(([lon,lat],i)=>{const p=spatialProject(lon,lat,bounds);return (i?'L':'M')+p.x.toFixed(2)+' '+p.y.toFixed(2)}).join(' ');
}
function spatialEvidenceLabel(review){
  return ({'reviewed-model':'Reviewed model','archive':'Imported estimate','primary-noncomparable':'Native-unit disclosure','contract-record':'Contract record'})[review]||'Research record';
}
function spatialEvidenceClass(review){return ({'reviewed-model':'model','archive':'archive','primary-noncomparable':'primary','contract-record':'target'})[review]||'';}
function spatialAggregate(xs,phase){
  const comparable=xs.filter(s=>spatialComparable(s,phase));
  const reviewed=comparable.filter(s=>s.review==='reviewed-model');
  const archive=comparable.filter(s=>s.review==='archive');
  return {count:xs.length,mapped:xs.length,known:comparable.length,mw:comparable.reduce((n,s)=>n+spatialPower(s,phase),0),reviewedMw:reviewed.reduce((n,s)=>n+spatialPower(s,phase),0),archiveMw:archive.reduce((n,s)=>n+spatialPower(s,phase),0),unknown:xs.length-comparable.length};
}
function spatialTopSites(xs,phase,n=6){return [...xs].sort((a,b)=>(spatialPower(b,phase)||0)-(spatialPower(a,phase)||0)).slice(0,n);}
function spatialCompanies(xs){
  const m=new Map();for(const s of xs)for(const id of s.company_ids||[]){const c=company(id);if(c)m.set(id,(m.get(id)||0)+1)}
  return [...m.entries()].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([id,count])=>({c:company(id),count}));
}
function spatialStageStrip(level){return `<div class="atlas-scale-strip" role="tablist" aria-label="Map scale">${ATLAS_SCALE_LEVELS.map(x=>`<button role="tab" aria-selected="${x.id===level}" class="atlas-scale-step ${x.id===level?'active':''}" data-spatial-action="stage" data-id="${x.id}"><span>${String(x.id+1).padStart(2,'0')}</span><b>${x.label}</b><small>${x.sub}</small></button>`).join('')}</div>`;}
function spatialMap(scope,selected,level,phase){
  if(level===5)return spatialFacilitySchematic(selected,phase);
  const bounds=scope.bounds;
  const lines=(W.lines||[]).map(line=>`<path d="${spatialPath(line,bounds)}"/>`).join('');
  const grid=[20,40,60,80].map(n=>`<line x1="${n}" y1="0" x2="${n}" y2="100"/><line x1="0" y1="${n}" x2="100" y2="${n}"/>`).join('');
  const markers=scope.sites.map(s=>{const p=spatialProject(s.lon,s.lat,bounds);const mw=spatialPower(s,phase);const size=Math.max(10,Math.min(34,10+Math.sqrt(mw||0)*.7));const sel=s.id===selected?.id;return `<button class="atlas-map-marker ${sel?'selected':''} evidence-${s.review}" style="left:${p.x}%;top:${p.y}%;--marker-size:${size}px" data-spatial-action="select" data-id="${esc(s.id)}" aria-label="${esc(s.name)}, ${mw==null?'power not quantified':fmt(mw)+' MW IT'}"><i></i>${sel||level>=3?`<span>${esc(s.name)}${mw!=null?`<small>${fmt(mw)} MW</small>`:''}</span>`:''}</button>`}).join('');
  return `<div class="atlas-map-stage"><svg class="atlas-vector-map" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="atlasSea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#102533"/><stop offset="1" stop-color="#07131e"/></linearGradient></defs><rect width="100" height="100" fill="url(#atlasSea)"/><g class="atlas-grid">${grid}</g><g class="atlas-world-lines">${lines}</g></svg>${markers}<div class="atlas-map-legend"><span><i class="legend-reviewed"></i>Reviewed model</span><span><i class="legend-archive"></i>Imported estimate</span><span><i class="legend-other"></i>Non-comparable / contract</span></div><div class="atlas-map-disclaimer">Approximate research anchors · not surveyed site coordinates</div></div>`;
}
function spatialFacilitySchematic(s,phase){
  if(!s)return '<div class="atlas-evidence-schematic empty">No facility selected.</div>';
  const timeline=(s.timeline||[]).filter(x=>spatialFinite(x.mw));
  const bars=timeline.length?timeline:([s.snapshot,s.target].filter(Boolean).map((x,i)=>({label:i?'Projected end-state':'Snapshot',date:x.date,mw:x.it_mw,kind:i?'projected':'modeled'})));
  const max=Math.max(...bars.map(x=>spatialFinite(x.mw)?x.mw:0),1);
  return `<div class="atlas-evidence-schematic"><div class="atlas-schematic-badge">EVIDENCE SCHEMATIC · NOT A PARCEL / BUILDING SURVEY</div><div class="atlas-schematic-grid"><div class="atlas-schematic-site"><div class="schematic-halo"></div><div class="schematic-core"><strong>${esc(s.name)}</strong><span>${esc(s.location)}</span><small>${esc(s.coordinate_precision||'Approximate anchor')}</small></div>${bars.slice(-6).map((x,i)=>`<div class="schematic-phase" style="--x:${12+(i%3)*29}%;--y:${18+Math.floor(i/3)*34}%;--w:${22+Math.max(0,Number(x.mw||0)/max*12)}%"><b>${esc(x.label||('Phase '+(i+1)))}</b><span>${spatialFinite(x.mw)?fmt(x.mw)+' MW':'MW not quantified'}</span><small>${esc(x.date||'Date not supplied')}</small></div>`).join('')}</div><div class="atlas-schematic-note"><h3>What the evidence establishes</h3><p>Capacity phases, dates, owners and source references are drawn from the facility record. Exact building footprints, parcel boundaries, roads and substations are not inferred when the dataset does not contain them.</p></div></div></div>`;
}
function spatialRail(level,scope,selected,phase){
  const agg=spatialAggregate(scope.sites,phase),top=spatialTopSites(scope.sites,phase),cos=spatialCompanies(scope.sites);
  if(level<=2)return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent"><div class="atlas-card-kicker">${String(level+1).padStart(2,'0')} / ${ATLAS_SCALE_LEVELS[level].label.toUpperCase()}</div><h2>${esc(scope.label)}</h2><p>${agg.count} mapped research records at this scale. Comparable IT-load totals include only reviewed or imported site estimates with finite ${phase} IT-MW values.</p><div class="atlas-rail-metrics"><div><span>Comparable ${phase} IT power</span><strong>${agg.known?fmt(agg.mw/1000,3)+' GW':'—'}</strong></div><div><span>Quantified / mapped</span><strong>${agg.known} / ${agg.count}</strong></div><div><span>Unquantified here</span><strong>${agg.unknown}</strong></div></div></section><section class="atlas-insight-card"><div class="atlas-card-kicker">LARGEST NAMED RECORDS</div>${top.map(s=>`<button class="atlas-rank-row" data-spatial-action="select" data-id="${esc(s.id)}"><span>${esc(s.name)}<small>${esc(s.location)}</small></span><b>${spatialPower(s,phase)!=null?fmt(spatialPower(s,phase))+' MW':'—'}</b></button>`).join('')}</section><section class="atlas-insight-card"><div class="atlas-card-kicker">OPERATORS / COUNTERPARTIES</div><div class="atlas-company-cloud">${cos.map(x=>`<button data-action="company" data-id="${x.c.id}"><i style="background:${x.c.color}"></i>${esc(x.c.name)} <small>${x.count}</small></button>`).join('')||'<span class="muted">No linked companies at this scale.</span>'}</div></section></div>`;
  if(level===3)return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent"><div class="atlas-card-kicker">04 / METRO CLUSTER</div><h2>${esc(scope.label)}</h2><p>Nearby named projects within approximately 650 km of ${esc(selected?.name||'the selected site')}. Distance is based on approximate research anchors.</p><div class="atlas-rail-metrics"><div><span>Comparable ${phase}</span><strong>${agg.known?fmt(agg.mw/1000,3)+' GW':'—'}</strong></div><div><span>Named projects</span><strong>${agg.count}</strong></div></div></section><section class="atlas-insight-card"><div class="atlas-card-kicker">LOCAL PROJECTS</div>${top.map(s=>`<button class="atlas-rank-row" data-spatial-action="select" data-id="${esc(s.id)}"><span>${esc(s.name)}<small>${esc(s.owner_label)}</small></span><b>${spatialPower(s,phase)!=null?fmt(spatialPower(s,phase))+' MW':'—'}</b></button>`).join('')}</section></div>`;
  return spatialFacilityRail(selected,phase,level);
}
function spatialFacilityRail(s,phase,level){
  if(!s)return '<div class="atlas-insight-card">Select a facility.</div>';
  const cur=spatialPower(s,'snapshot'),target=spatialPower(s,'target');
  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent"><div class="atlas-card-kicker">${level===4?'05 / CAMPUS':'06 / FACILITY EVIDENCE'}</div><h2>${esc(s.name)}</h2><p>${esc(s.location)} · ${esc(s.owner_label)}</p><div class="tag-row"><span class="pill ${spatialEvidenceClass(s.review)}">${spatialEvidenceLabel(s.review)}</span>${s.snapshot?'<span class="pill model">Snapshot</span>':''}${s.target?'<span class="pill target">Target</span>':''}</div><div class="atlas-rail-metrics"><div><span>Snapshot IT</span><strong>${cur!=null?fmt(cur)+' MW':'—'}</strong></div><div><span>Target IT</span><strong>${target!=null?fmt(target)+' MW':'—'}</strong></div><div><span>Sources</span><strong>${(s.sources||[]).length}</strong></div></div><button class="btn primary atlas-wide" data-spatial-action="dossier" data-id="${esc(s.id)}">Open full site dossier →</button></section>${(s.roles||[]).length?`<section class="atlas-insight-card"><div class="atlas-card-kicker">OWNERSHIP & RELATIONSHIPS</div>${s.roles.map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><b>${esc(r.entity)}</b><small>${esc(r.basis||'')}</small></div>`).join('')}</section>`:''}${(s.timeline||[]).length?`<section class="atlas-insight-card"><div class="atlas-card-kicker">FACILITY TIMELINE</div>${s.timeline.slice(-7).map(t=>`<div class="atlas-timeline-row"><time>${esc(t.date||'—')}</time><span>${esc(t.label)}${spatialFinite(t.mw)?`<small>${fmt(t.mw)} MW</small>`:''}</span></div>`).join('')}</section>`:''}${(s.caveats||[]).length?`<section class="atlas-insight-card warning"><div class="atlas-card-kicker">EVIDENCE BOUNDARIES</div>${s.caveats.slice(0,3).map(x=>`<p>${esc(x)}</p>`).join('')}</section>`:''}</div>`;
}
function spatialHeadline(level,scope,selected){
  if(level===0)return ['A global view of compute capital.','Start with the physical layer, then descend into the facility evidence.'];
  if(level===1)return [`${scope.label}: the regional compute system.`,`Compare named facilities without turning partial coverage into a fleet census.`];
  if(level===2)return [`${scope.label}: where capacity becomes geography.`,`Projects, companies and evidence at country / market scale.`];
  if(level===3)return [`${scope.label}: the local compute cluster.`,`Follow nearby projects, then descend into a single campus.`];
  if(level===4)return [`${selected?.name||'Campus'}: project-level evidence.`,`Power phases, counterparties and sources — not invented parcel geometry.`];
  return [`${selected?.name||'Facility'}: evidence at the finest scale.`,`Sourced phases and relationships, with unknown physical geometry left unknown.`];
}
function spatialKpis(scope,phase){
  const a=spatialAggregate(scope.sites,phase);return `<div class="atlas-kpi-grid">${metric(a.known?fmt(a.mw/1000,3)+' GW':'—','Comparable '+phase+' IT power','Named-site subtotal only')}${metric(fmt(a.count),'Mapped records','At this semantic scale')}${metric(fmt(a.known),'Quantified IT-MW','Reviewed/imported records')}${metric(fmt(a.unknown),'Not comparable here','Unknown/native/contract-only')}</div>`;
}
function sixScaleGlobeView(){
  const st=spatialState(),selected=spatialDefaultSite(),level=st.spatialLevel,phase=st.spatialPhase,scope=spatialScope(level,selected),[title,sub]=spatialHeadline(level,scope,selected);
  return `${pagehead('COMPUTE, FROM THE GROUND UP',title,sub,`<div class="atlas-phase-toggle"><button class="${phase==='snapshot'?'active':''}" data-spatial-action="phase" data-id="snapshot">Snapshot</button><button class="${phase==='target'?'active':''}" data-spatial-action="phase" data-id="target">Target</button></div>`)}${spatialStageStrip(level)}<div class="atlas-spatial-layout"><section class="panel atlas-map-panel"><div class="atlas-map-head"><div><span class="eyebrow">${esc(ATLAS_SCALE_LEVELS[level].label.toUpperCase())} SCALE</span><h2>${esc(scope.label)}</h2><p>${scope.sites.length} mapped records · ${phase} layer</p></div><div class="atlas-map-tools"><button class="icon-button" data-spatial-action="zoom-out" aria-label="Zoom out" ${level===0?'disabled':''}>−</button><button class="icon-button" data-spatial-action="zoom-in" aria-label="Zoom in" ${level===5?'disabled':''}>+</button><button class="icon-button" data-spatial-action="reset" aria-label="Reset to world">⌂</button></div></div>${spatialMap(scope,selected,level,phase)}<div class="atlas-map-footer"><span>${selected?`Selected: <b>${esc(selected.name)}</b> · ${esc(selected.location)}`:'Select a facility'}</span><span>Power boundary: IT load where explicitly modeled</span></div></section><aside class="atlas-spatial-rail">${spatialRail(level,scope,selected,phase)}</aside></div>${spatialKpis(scope,phase)}<section class="panel panel-pad atlas-method-strip"><strong>Evidence-first spatial model</strong><span>Coordinates are approximate research anchors. Site totals are partial. Contracted, announced, gross facility and IT power are never silently combined.</span><button class="text-button" data-action="method">Read methodology ↗</button></section>`;
}

const coreGlobeView = globeView;
globeView = sixScaleGlobeView;

document.addEventListener('click',e=>{
  const b=e.target.closest('[data-spatial-action]'); if(!b)return;
  const action=b.dataset.spatialAction,id=b.dataset.id,st=spatialState();
  if(action==='stage'){st.spatialLevel=Math.max(0,Math.min(5,Number(id)));render();return;}
  if(action==='phase'){st.spatialPhase=id==='target'?'target':'snapshot';render();return;}
  if(action==='zoom-in'){st.spatialLevel=Math.min(5,st.spatialLevel+1);render();return;}
  if(action==='zoom-out'){st.spatialLevel=Math.max(0,st.spatialLevel-1);render();return;}
  if(action==='reset'){st.spatialLevel=0;st.spatialSelected=null;state.filter={q:'',company:'all',country:'all',review:'all',stage:'all'};render();return;}
  if(action==='select'){
    const s=site(id);if(!s)return;st.spatialSelected=id;
    if(st.spatialLevel<4)st.spatialLevel++;
    render();return;
  }
  if(action==='dossier'){openDrawer('site',id);return;}
});

document.addEventListener('keydown',e=>{
  if(state.view!=='globe'||/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName))return;
  const st=spatialState();
  if(e.key==='+'||e.key==='='){e.preventDefault();st.spatialLevel=Math.min(5,st.spatialLevel+1);render();}
  if(e.key==='-'||e.key==='_'){e.preventDefault();st.spatialLevel=Math.max(0,st.spatialLevel-1);render();}
});

// Extend QA/debug surface without changing the underlying research graph.
if(globalThis.ATLAS){
  ATLAS.spatial={levels:ATLAS_SCALE_LEVELS,state:spatialState,scope:()=>spatialScope(spatialState().spatialLevel,spatialDefaultSite()),select:id=>{if(site(id)){state.spatialSelected=id;render();}},setLevel:n=>{state.spatialLevel=Math.max(0,Math.min(5,Number(n)||0));render();}};
}
if(state.view==='globe')render();
