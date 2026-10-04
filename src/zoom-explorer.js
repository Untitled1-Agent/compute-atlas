'use strict';
/* Six semantic scales, independently sourced observations, and explicit uncertainty.
   The original research graph remains intact. Mockups are never used as data. */
const ATLAS_SCALE_LEVELS = [
  {id:0,key:'world',label:'World',sub:'Global evidence'},
  {id:1,key:'continent',label:'Continent',sub:'Regional systems'},
  {id:2,key:'region',label:'Region',sub:'Country / market'},
  {id:3,key:'metro',label:'Metro',sub:'Local corridor'},
  {id:4,key:'campus',label:'Campus',sub:'Named project'},
  {id:5,key:'facility',label:'Facility',sub:'Evidence detail'},
];
const ATLAS_PRIMARY = JSON.parse(document.getElementById('evidence-data')?.textContent || '{"sources":[],"observations":[],"facts":[],"relationships":[],"discoveries":[]}');
const atlasSpatial = globalThis.AtlasSpatialMath || {};
const spatialFinite = value => typeof value === 'number' && Number.isFinite(value);
const primarySource = id => ATLAS_PRIMARY.sources.find(s => s.id === id);
const effectivePrimary = rows => {
  // Follow the complete chain, including withdrawn intermediate revisions.
  // The history partition is audit context and never contributes extra capacity.
  const all=new Map([...Object.values(ATLAS_PRIMARY.revision_history||{}).flat(),...rows].map(o=>[o.id,o]));
  const accepted=rows.filter(o=>o.review_status==='accepted'), old=new Set();
  for(const row of accepted){const visited=new Set([row.id]);let prior=row.supersedes;
    while(prior&&!visited.has(prior)){visited.add(prior);old.add(prior);prior=all.get(prior)?.supersedes;}}
  return accepted.filter(o=>!old.has(o.id));
};
const primaryObservations = s => effectivePrimary(ATLAS_PRIMARY.observations).filter(o => o.site_id === s?.id && o.review_status === 'accepted');
const primaryFacts = s => effectivePrimary(ATLAS_PRIMARY.facts).filter(o => o.site_id === s?.id);
const primaryRelationships = s => effectivePrimary(ATLAS_PRIMARY.relationships).filter(o => o.site_id === s?.id);
const primarySourceIds = s => [...new Set([...primaryObservations(s), ...primaryFacts(s), ...primaryRelationships(s)].map(o => o.source_id))];
const spatialPower = (s, phase = spatialState().spatialPhase) => spatialFinite(s?.[phase]?.it_mw) ? s[phase].it_mw : null;
const spatialComparable = (s, phase = spatialState().spatialPhase) => ['reviewed-model', 'archive'].includes(s.review) && spatialPower(s, phase) != null;
const spatialEvidenceLabel = review => ({'reviewed-model':'Reviewed independent model','archive':'Imported estimate','primary-noncomparable':'Native-unit disclosure','contract-record':'Contract record'})[review] || 'Research record';
const spatialEvidenceClass = review => ({'reviewed-model':'model','archive':'archive','primary-noncomparable':'primary','contract-record':'target'})[review] || '';
const boundaryLabel = value => ({critical_it:'Critical IT load',gross_facility:'Gross facility power',utility_capacity:'Utility supply capacity',annual_pue:'Annual PUE',reported_energy_savings:'Annual energy saving',base_lease_value:'Base-term lease value',generation:'Power generation',unspecified_compute:'Unspecified compute power',site_area:'Site area',contract_term:'Lease term',building_count:'Buildings',regional_investment:'Regional investment',construction_cost:'Registered construction cost',building_area:'Registered floor area',equipment_count:'Equipment count'})[value] || value;
const statusLabel = value => ({delivered:'Delivered',energized:'Energized',contracted:'Contracted',approved:'Approved envelope',under_construction:'Under construction',planned:'Planned',announced:'Announced',disclosed:'Disclosed',operating:'Operating',historical:'Historical snapshot',not_disclosed:'Not disclosed'})[value] || value;
const primaryDate = source => source?.published_at || source?.retrieved_at || '';
const primaryRef = id => `<button class="atlas-source-ref" data-atlas-action="source" data-id="${esc(id)}" aria-label="Read source ${esc(id)}">${esc(id)} ↗</button>`;
const atlasKicker = (text, arrow = true) => `<div class="atlas-card-kicker">${esc(text)}${arrow ? '<span aria-hidden="true">↗</span>' : ''}</div>`;
const atlasRow = (label, value) => `<div class="atlas-data-row"><span>${esc(label)}</span><strong>${value}</strong></div>`;

function spatialState() {
  if (!Number.isInteger(state.spatialLevel)) state.spatialLevel = 0;
  state.spatialLevel = Math.max(0, Math.min(5, state.spatialLevel));
  if (!['snapshot','target'].includes(state.spatialPhase)) state.spatialPhase = 'snapshot';
  if (!['all','primary','reviewed-model','archive','native'].includes(state.spatialEvidence)) state.spatialEvidence = 'all';
  if (!site(state.spatialSelected)) state.spatialSelected = null;
  return state;
}
function spatialFiltered() {
  const filter = state.filter, evidence = spatialState().spatialEvidence;
  return D.sites.filter(s =>
    (!filter.q || (s.name + ' ' + s.location + ' ' + s.owner_label).toLowerCase().includes(filter.q.toLowerCase())) &&
    (!filter.country || filter.country === 'all' || s.country === filter.country) &&
    (!filter.company || filter.company === 'all' || s.company_ids.includes(filter.company) || primaryRelationships(s).some(r => r.company_id === filter.company)) &&
    (evidence === 'all' || evidence === 'primary' && primarySourceIds(s).length > 0 || evidence === s.review || evidence === 'native' && ['primary-noncomparable','contract-record'].includes(s.review))
  );
}
function spatialMapped() { return spatialFiltered().filter(s => spatialFinite(s.lat) && spatialFinite(s.lon)); }
function spatialDefaultSite() {
  const pool = spatialFiltered(), st = spatialState();
  const selected = pool.find(s => s.id === st.spatialSelected) || pool.find(s => s.id === 'amazon-anthropic-new-carlisle') || pool[0];
  st.spatialSelected = selected?.id || null;
  return selected || null;
}
function spatialDistance(a, b) {
  if (!a || !b || !spatialFinite(a.lat) || !spatialFinite(b.lat)) return Infinity;
  const rad = Math.PI / 180, dlat = (b.lat-a.lat)*rad, dlon=(b.lon-a.lon)*rad;
  const q = Math.sin(dlat/2)**2 + Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dlon/2)**2;
  return 6371 * 2 * Math.atan2(Math.sqrt(q),Math.sqrt(Math.max(0,1-q)));
}
function spatialContinent(s) {
  const c = s?.country || '';
  if (['United States','Canada','Mexico'].includes(c)) return 'North America';
  if (['China','Japan','South Korea','India','Singapore','Malaysia','Indonesia','Taiwan','Vietnam','Thailand'].includes(c)) return 'Asia';
  if (['United Arab Emirates','Saudi Arabia','Israel','Qatar'].includes(c)) return 'Middle East';
  if (['Australia','New Zealand'].includes(c)) return 'Oceania';
  if (['Brazil','Chile','Argentina','Colombia','Peru'].includes(c)) return 'South America';
  if (['South Africa','Kenya','Nigeria','Egypt','Morocco'].includes(c)) return 'Africa';
  if (['United Kingdom','Norway','Sweden','Finland','Denmark','Iceland','France','Germany','Spain','Portugal','Italy','Ireland','Netherlands','Switzerland','Poland','Austria','Belgium'].includes(c)) return 'Europe';
  return 'Other';
}
function spatialFitBounds(xs, selected, padLon=3, padLat=2) {
  const pts = xs.filter(s => spatialFinite(s.lon) && spatialFinite(s.lat));
  if (!pts.length && selected && spatialFinite(selected.lat)) pts.push(selected);
  if (!pts.length) return [-180,-60,180,80];
  let x0=Math.min(...pts.map(s=>s.lon)),x1=Math.max(...pts.map(s=>s.lon)),y0=Math.min(...pts.map(s=>s.lat)),y1=Math.max(...pts.map(s=>s.lat));
  if(x1-x0<padLon){const mid=(x0+x1)/2;x0=mid-padLon/2;x1=mid+padLon/2;}
  if(y1-y0<padLat){const mid=(y0+y1)/2;y0=mid-padLat/2;y1=mid+padLat/2;}
  return [Math.max(-180,x0-padLon*.2),Math.max(-80,y0-padLat*.2),Math.min(180,x1+padLon*.2),Math.min(80,y1+padLat*.2)];
}
function spatialScope(level, selected) {
  const all = spatialMapped(), inside = (s,b) => s.lon>=b[0] && s.lon<=b[2] && s.lat>=b[1] && s.lat<=b[3];
  if (level === 0) return {label:'Global compute map', sites:all, bounds:[-180,-60,180,80], note:'Named research records · not a global census'};
  const continent = spatialContinent(selected);
  if (level === 1) {
    const transatlantic = ['North America','Europe'].includes(continent);
    const xs = all.filter(s => transatlantic ? ['North America','Europe'].includes(spatialContinent(s)) : spatialContinent(s)===continent);
    return {label:transatlantic?'North America ↔ Europe':continent,sites:xs,bounds:spatialFitBounds(xs,selected),note:'Regional system · partial research coverage'};
  }
  if (level === 2) {
    let xs = all.filter(s=>s.country===selected?.country), label=selected?.country||'No matching region', bounds;
    if (selected?.country === 'United States') {
      if (selected.lon < -106) {bounds=[-127,29,-102,50];label='Western United States';}
      else if(selected.lon < -97 && selected.lat < 38) {bounds=[-107,25,-91,39];label='Texas & the southern power markets';}
      else {bounds=[-98,27,-66,50];label='US East & Midwest';}
      xs=xs.filter(s=>inside(s,bounds));
    } else bounds=spatialFitBounds(xs,selected,5,4);
    return {label,sites:xs,bounds,note:'Geographic market window · generalized roads and boundaries'};
  }
  if (level === 3) {
    const xs=all.filter(s=>spatialDistance(selected,s)<=250);
    return {label:selected?.id==='amazon-anthropic-new-carlisle'?'Chicago–Northern Indiana':(selected?.location?.split(',')[0]||'Local')+' corridor',sites:xs,bounds:spatialFitBounds(xs,selected,4,2.5),note:'Within 250 km of the approximate selected anchor · not a metro census'};
  }
  // A campus is one named project. Nearby sites never become part of its capacity.
  return {label:selected?.name||'No matching facility',sites:selected?[selected]:[],bounds:spatialFitBounds(selected?[selected]:[],selected,.8,.6),note:'Evidence schematic · no surveyed parcels or building footprints'};
}
function spatialAggregate(xs, phase) {
  const comparable=xs.filter(s=>spatialComparable(s,phase));
  return {count:xs.length,mapped:xs.filter(s=>spatialFinite(s.lat)).length,known:comparable.length,mw:comparable.reduce((n,s)=>n+spatialPower(s,phase),0),
    reviewedMw:comparable.filter(s=>s.review==='reviewed-model').reduce((n,s)=>n+spatialPower(s,phase),0),
    archiveMw:comparable.filter(s=>s.review==='archive').reduce((n,s)=>n+spatialPower(s,phase),0),unknown:xs.length-comparable.length};
}
function spatialTopSites(xs,phase,n=5){return [...xs].sort((a,b)=>(spatialPower(b,phase)??-1)-(spatialPower(a,phase)??-1)).slice(0,n);}
function spatialCompanies(xs) {
  const counts=new Map();for(const s of xs)for(const id of s.company_ids||[])if(company(id))counts.set(id,(counts.get(id)||0)+1);
  return [...counts].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([id,count])=>({c:company(id),count}));
}
function spatialStageStrip(level) {
  return `<div class="atlas-scale-strip" role="tablist" aria-label="Map scale">${ATLAS_SCALE_LEVELS.map(s=>`<button role="tab" aria-selected="${s.id===level}" tabindex="${s.id===level?0:-1}" class="atlas-scale-step ${s.id===level?'active':''}" data-spatial-action="stage" data-id="${s.id}"><span>${String(s.id+1).padStart(2,'0')}</span><b>${s.label}</b><small>${s.sub}</small></button>`).join('')}</div>`;
}
function spatialHeadline(level,scope,s) {
  if(level===0)return ['A global view<br>of compute capital.','Explore the places, power, and counterparties behind AI. Follow the evidence from a global perspective to a single facility.'];
  if(level===1)return [esc(scope.label)+'.<br>The physical network behind AI.','Explore a connected regional system without mistaking a partial collection of named sites for total market capacity.'];
  if(level===2)return [scope.label==='US East & Midwest'?'The Midwest and East Coast,<br>from power to compute.':esc(scope.label)+'.<br>Follow the physical footprint.','Move from broad markets to individual projects. Models, disclosures, and unknowns remain visibly distinct at every scale.'];
  if(level===3)return [esc(scope.label)+'.', 'Power, land, and compute meet at the local scale. Select a named project to inspect its sources, counterparties, and phase evidence.'];
  return [esc(s?.name||'No matching project')+(level===4?' campus.':' — facility dossier.'),'Every number has a boundary. Inspect delivered capacity, future commitments, and the original models without conflating them.'];
}
function atlasPhaseToggle(phase) {
  return `<div class="atlas-phase-toggle" aria-label="Independent estimate layer"><button class="${phase==='snapshot'?'active':''}" data-spatial-action="phase" data-id="snapshot" aria-pressed="${phase==='snapshot'}">Snapshot</button><button class="${phase==='target'?'active':''}" data-spatial-action="phase" data-id="target" aria-pressed="${phase==='target'}">Target</button></div>`;
}
function atlasMapControls(level) {
  return `<div class="atlas-map-tools">${level<4?`<button class="icon-button" data-atlas-action="labels" aria-label="Toggle map labels" aria-pressed="${state.spatialLabels!==false}">Aa</button>`:''}<button class="icon-button" data-spatial-action="zoom-in" aria-label="Zoom in to next scale" ${level===5?'disabled':''}>+</button><button class="icon-button" data-spatial-action="zoom-out" aria-label="Zoom out to previous scale" ${level===0?'disabled':''}>−</button><button class="icon-button" data-atlas-action="expand" aria-label="Expand map">⛶</button><button class="icon-button" data-spatial-action="reset" aria-label="Reset to the world view">◎</button></div>`;
}
function spatialMap(scope,s,level,phase) {
  if(level>=4)return spatialFacilitySchematic(s,phase,level);
  const places=[['all','All regions'],['americas','Americas'],['europe','Europe'],['asia','Asia'],['middle-east','Middle East']];
  return `<div class="atlas-map-stage" data-level="${level}"><canvas id="globe-canvas" tabindex="0" aria-label="Interactive ${esc(scope.label)}. Drag to rotate or pan. Arrow keys move the map; plus and minus change scale." aria-describedby="globe-live"></canvas><div class="atlas-marker-layer">${scope.sites.map(x=>`<button class="atlas-map-marker ${x.id===s?.id?'selected':''}" data-spatial-action="select" data-id="${esc(x.id)}" aria-label="Explore ${esc(x.name)}, ${esc(x.location)}; ${spatialPower(x,phase)==null?'IT power not quantified':fmt(spatialPower(x,phase))+' MW independent estimate'}"><span class="sr-only">${esc(x.name)}</span></button>`).join('')}</div>
    <div class="atlas-map-head"><div><h2>${esc(scope.label)}</h2><p>${scope.sites.length} mapped records · ${phase==='target'?'target estimates':'dated snapshot estimates'}</p></div>${atlasPhaseToggle(phase)}</div>
    <div class="atlas-map-legend"><span><i class="legend-reviewed"></i>${level<=1?'Reviewed / mixed estimate cluster':'Reviewed independent model'}</span><span><i class="legend-archive"></i>${level<=1?'Imported estimate cluster':'Imported estimate'}</span><span><i class="legend-other"></i>Native-unit / contract record</span>${level>=2?'<span class="atlas-line-key">Generalized roads & boundaries</span>':''}</div>
    <div class="atlas-map-bottom"><div class="atlas-map-chips">${level<=1?places.map(([id,label])=>`<button data-atlas-action="fly" data-id="${id}" class="${(state.spatialFly||'all')===id?'active':''}">${label}</button>`).join(''):`<button data-atlas-action="roads" aria-pressed="${state.spatialRoads!==false}">${state.spatialRoads!==false?'✓ ':''}Road context</button><button data-atlas-action="source-context">Map attribution ↗</button>`}</div><div id="geo-position" class="atlas-coordinate"></div></div>
    ${atlasMapControls(level)}<span id="globe-live" class="sr-only" role="status"></span></div>`;
}
function observationValue(o){return spatialFinite(o.value)?(o.comparison==='gt'?'&gt; ':o.comparison==='lt'?'&lt; ':o.comparison==='approximate'?'≈ ':'')+fmt(o.value):'Not quantified';}
function primaryPowerRows(s) {const rank={operating:0,delivered:0.5,under_construction:1,contracted:2,planned:3,announced:3,historical:9};return primaryObservations(s).filter(o=>o.metric==='power'&&spatialFinite(o.value)).sort((a,b)=>(rank[a.status]??5)-(rank[b.status]??5)||String(b.as_of||'').localeCompare(String(a.as_of||''))||a.id.localeCompare(b.id));}
function spatialFacilitySchematic(s,phase,level=5) {
  if(!s)return '<div class="atlas-evidence-schematic atlas-empty"><h2>No matching facility</h2><p>Clear the filters to return to the collection.</p></div>';
  const primary=primaryPowerRows(s).filter(o=>o.boundary==='critical_it'&&!o.id.endsWith('building-it'));
  const models=[['snapshot','Dated snapshot'],['target','Projected end-state']].filter(([key])=>spatialPower(s,key)!=null).map(([key,label])=>({id:key,scope:label,value:spatialPower(s,key),unit:'MW',status:'modeled',period:s[key].date,qualifier:key==='target'?'End-state, not incremental capacity':'Independent / imported estimate'}));
  const rows=primary.length?primary.slice(0,3):models;
  const title=primary.length?'From commitment to delivery.':'What the current evidence establishes.';
  const max=Math.max(...rows.map(o=>o.value||0),1);
  return `<div class="atlas-evidence-schematic" data-level="${level}"><div class="atlas-schematic-badge">EVIDENCE SCHEMATIC · NOT A PARCEL / BUILDING SURVEY</div><div class="atlas-schematic-heading"><span class="atlas-eyebrow">${esc(s.location)} · ${esc(s.country)}</span><h2>${title}</h2><p>${primary.length?'Published critical-IT quantities, kept in their original phase and contract scopes.':'Independent estimates shown as evidence cards, not fictional building footprints.'}</p></div>
    <div class="atlas-phase-diagram">${rows.length?rows.map((o,i)=>`<article class="atlas-phase-node ${['delivered','operating'].includes(o.status)?'delivered':''}"><div class="atlas-node-number">${String(i+1).padStart(2,'0')} / ${esc(o.scope)}</div><strong>${fmt(o.value)} <small>${esc(o.unit)}</small></strong><div class="atlas-node-bar"><i style="width:${Math.max(2,o.value/max*100)}%"></i></div><span class="atlas-node-status">${esc(statusLabel(o.status))}${o.period?' · '+esc(o.period):''}</span><p>${esc(o.qualifier||'Published measurement boundary retained.')}</p>${o.source_id?primaryRef(o.source_id):srefs(s[o.id]?.sources||s.sources)}</article>`).join(''):`<div class="atlas-native-evidence"><span>≠</span><h3>Unknown is not zero.</h3><p>This record has no defensible comparable IT-MW quantity. Its native disclosures and contract evidence remain available in the source dossier.</p></div>`}</div>
    <div class="atlas-schematic-caption"><span class="atlas-schematic-icon">◇</span><p><b>${primary.length?'These are not additive bars.':'No intermediate phases invented.'}</b> ${primary.length?'A multi-phase commitment can include an already delivered phase. Neither one measures live utilization.':'Snapshot and target describe separate dates; the target is not added to the snapshot.'}</p></div>
    <div class="atlas-schematic-foot"><span>Physical geometry: not established in this source set</span><button data-atlas-action="context" data-id="${esc(s.id)}">View approximate geographic context ↗</button></div>${atlasMapControls(level)}</div>`;
}
function atlasRankRows(xs,phase) {
  return xs.map((s,i)=>`<button class="atlas-rank-row" data-spatial-action="select" data-id="${esc(s.id)}"><span class="atlas-rank-number">${i+1}</span><span>${esc(s.name)}<small>${esc(s.location)}</small></span><b>${spatialPower(s,phase)==null?'—':fmt(spatialPower(s,phase))+' MW'}</b><span aria-hidden="true">↗</span></button>`).join('');
}
function spatialRail(level,scope,s,phase) {
  if(level>=4)return spatialFacilityRail(s,phase,level);
  const agg=spatialAggregate(scope.sites,phase), countries=new Set(scope.sites.map(s=>s.country)).size, primaryCount=scope.sites.filter(x=>primarySourceIds(x).length).length;
  const updates=scope.sites.filter(x=>primarySourceIds(x).length).sort((a,b)=>Math.max(...primarySourceIds(b).map(id=>Date.parse(primaryDate(primarySource(id)))||0))-Math.max(...primarySourceIds(a).map(id=>Date.parse(primaryDate(primarySource(id)))||0))).slice(0,3);
  if(level===3)return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / SELECTED PROJECT')}<h2>${esc(s?.name||'No matching project')}</h2><p>${esc(s?.location||'')} · ${esc(s?.country||'')}</p><div class="atlas-badge-row"><span>Approximate anchor</span><span>${esc(spatialEvidenceLabel(s?.review))}</span></div>${atlasRow('Snapshot IT estimate',spatialPower(s,'snapshot')==null?'Not quantified':fmt(spatialPower(s,'snapshot'))+' MW')}${atlasRow('Target IT estimate',spatialPower(s,'target')==null?'Not quantified':fmt(spatialPower(s,'target'))+' MW')}${atlasRow('Primary source reviews',String(primarySourceIds(s).length))}<button class="btn primary atlas-wide" data-atlas-action="campus" data-id="${esc(s?.id||'')}">Explore this campus →</button></section><section class="atlas-insight-card">${atlasKicker('02 / NEARBY NAMED PROJECTS')}<p>Within 250 km of the approximate anchor. Proximity does not establish common ownership or a shared power connection.</p>${atlasRankRows(spatialTopSites(scope.sites,phase,3),phase)}</section><section class="atlas-insight-card">${atlasKicker('03 / PHYSICAL INFRASTRUCTURE')}<h2>Context, without invented connections.</h2><p>Roads and boundaries are sourced reference geography. Unverified substations, transmission routes, and parcels are deliberately absent.</p></section></div>`;
  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / '+(level===0?'THE GLOBAL VIEW':'REGIONAL PERSPECTIVE'))}<h2>${level===0?'Compute is physical.<br>Start with the evidence.':esc(scope.label)+', site by site.'}</h2><p>${agg.count} mapped projects across ${countries} ${countries===1?'country':'countries'}. This is a curated research collection, not a census of installed capacity.</p><div class="atlas-coverage"><span><b>${agg.known}</b> quantified estimates</span><span><b>${agg.unknown}</b> without comparable IT-MW</span></div></section>
    <section class="atlas-insight-card">${atlasKicker('02 / '+(level===0?'RECENT PRIMARY EVIDENCE':'LARGEST NAMED ESTIMATES'))}${level===0?updates.map(x=>{const ids=primarySourceIds(x),src=primarySource(ids[0]);return `<button class="atlas-update-row" data-atlas-action="campus" data-id="${esc(x.id)}"><span class="atlas-update-dot"></span><span><b>${esc(x.name)}</b><small>${esc(src.publisher)} · ${esc(src.published_at || ('Retrieved '+src.retrieved_at))}</small></span><span>↗</span></button>`}).join('')+'<p class="atlas-card-footnote">'+primaryCount+' projects have an additional primary-source layer. Original model records remain unchanged.</p>':atlasRankRows(spatialTopSites(scope.sites,phase,3),phase)+'<p class="atlas-card-footnote">IT estimates only · not issuer-reported live loads</p>'}</section>
    <section class="atlas-insight-card">${atlasKicker('03 / OWNERS & COUNTERPARTIES')}<h2>Who’s building it.</h2><div class="atlas-company-cloud">${spatialCompanies(scope.sites).map(({c,count})=>`<button data-action="company" data-id="${esc(c.id)}"><i style="background:${esc(c.color)}"></i>${esc(c.name)}<small>${count}</small></button>`).join('')}</div><p class="atlas-card-footnote">Linked site records, not complete company fleets.</p></section></div>`;
}
function spatialFacilityRail(s,phase,level) {
  if(!s)return '<section class="atlas-insight-card"><h2>No project matches.</h2><p>Clear the filters to continue.</p></section>';
  const observations=primaryObservations(s), disclosed=primaryPowerRows(s).find(o=>o.boundary==='critical_it'&&['delivered','operating'].includes(o.status)), power=primaryPowerRows(s), relationships=primaryRelationships(s), sources=primarySourceIds(s);
  const primary=disclosed||power.find(o=>o.boundary==='critical_it'&&o.id.endsWith('total-it'))||power[0];
  const value=primary?`${fmt(primary.value)} ${primary.unit}`:spatialPower(s,phase)==null?'Not quantified':fmt(spatialPower(s,phase))+' MW';
  return `<div class="atlas-insight-stack"><section class="atlas-insight-card accent">${atlasKicker('01 / FACILITY DOSSIER')}<div class="atlas-badge-row"><span>${primary?esc(statusLabel(primary.status)):esc(spatialEvidenceLabel(s.review))}</span><span>${primary?'PRIMARY DISCLOSURE':'DATED RESEARCH'}</span></div><h2>${esc(s.name)}</h2><p>${esc(s.location)}, ${esc(s.country)}</p><div class="atlas-feature-number">${value}</div><p class="atlas-number-boundary">${primary?esc(boundaryLabel(primary.boundary))+' · '+esc(primary.scope):'IT power · '+phase+' estimate'}</p>${atlasRow('Reported / modeled date',esc(primary?.as_of||s[phase]?.date||'Not supplied'))}${atlasRow('Primary / archive source links',`${sources.length} / ${(s.sources||[]).length}`)}<button class="btn primary atlas-wide" data-spatial-action="dossier" data-id="${esc(s.id)}">Open full site dossier →</button><button class="atlas-secondary-action" data-atlas-action="export" data-id="${esc(s.id)}">Export cited dossier ↓</button></section>
    <section class="atlas-insight-card">${atlasKicker('02 / COUNTERPARTIES')}${relationships.length?relationships.map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><button data-action="company" data-id="${esc(r.company_id)}">${esc(company(r.company_id)?.name||r.company_id)} ↗</button>${primaryRef(r.source_id)}</div>`).join(''):(s.roles||[]).slice(0,4).map(r=>`<div class="atlas-role-row"><span>${esc(r.role)}</span><b>${esc(r.entity)}</b><small>${esc(r.basis||'Archive attribution')}</small></div>`).join('')}<p class="atlas-card-footnote">${relationships.length?'Source-specific roles; other archival associations may be broader.':'Historical source attributions; speculative relationships are not upgraded to confirmed contracts.'}</p></section>
    <section class="atlas-insight-card">${atlasKicker('03 / EVIDENCE QUALITY')}<h2>${sources.length?'Traceable, not absolute.':'An honest boundary.'}</h2><p>${sources.length?'Primary statements and independent models answer different questions. The app preserves both and does not convert announced or contracted power into delivered capacity.':'A reviewed estimate is not telemetry. A location anchor is not a surveyed centroid. Missing detail stays visibly missing.'}</p><div class="atlas-quality-checks"><span>✓ Source dates retained</span><span>✓ Original archive preserved</span><span class="uncertain">○ Surveyed site geometry unavailable</span></div></section></div>`;
}
function atlasPowerLadder(s) {
  const rows=primaryPowerRows(s), primary=rows.filter(o=>o.boundary==='critical_it'&&!o.id.endsWith('building-it'));
  const display=primary.length?primary:[['snapshot','Snapshot estimate'],['target','Target estimate']].filter(([key])=>spatialPower(s,key)!=null).map(([key,label])=>({scope:label,value:spatialPower(s,key),unit:'MW',status:'model',as_of:s[key].date,source_ids:s[key].sources}));
  const max=Math.max(...display.map(o=>o.value||0),1);
  return `<section class="atlas-detail-card">${atlasKicker('04 / POWER LADDER',false)}<h3>${primary.length?'Critical IT load by evidence scope':'Independent model: snapshot & target'}</h3>${display.length?display.map(o=>`<div class="atlas-power-row"><span>${esc(o.scope)}<small>${esc(statusLabel(o.status))}</small></span><b>${fmt(o.value)} MW</b><div class="atlas-power-track"><i class="${['delivered','operating'].includes(o.status)?'delivered':''}" style="width:${Math.max(2,o.value/max*100)}%"></i></div>${o.source_id?primaryRef(o.source_id):srefs(o.source_ids)}</div>`).join(''):'<p>No comparable IT-MW disclosure. Native quantities have not been converted.</p>'}<p class="atlas-card-footnote">Rows have different scopes or dates. Do not sum them. Gross power and generation are excluded.</p></section>`;
}
function atlasAttributes(s) {
  const facts=primaryFacts(s).slice(0,4), obs=primaryObservations(s).filter(o=>o.metric!=='power').slice(0,3);
  return `<section class="atlas-detail-card">${atlasKicker('05 / FACILITY ATTRIBUTES',false)}${facts.map(f=>atlasRow(f.label,esc(f.value)+' '+primaryRef(f.source_id))).join('')}${obs.map(o=>atlasRow(boundaryLabel(o.boundary),observationValue(o)+' '+esc(o.unit)+' '+primaryRef(o.source_id))).join('')}${!facts.length&&!obs.length?atlasRow('Location',esc(s.location))+atlasRow('Primary archive association',esc(s.owner_label)):''}${atlasRow('Coordinate precision',esc(s.coordinate_precision||'Not mapped'))}<p class="atlas-card-footnote">${facts[0]?.qualifier?esc(facts[0].qualifier):'Attributes retain their original scope; no parcel geometry is inferred.'}</p></section>`;
}
function atlasSourcesPanel(s) {
  const fresh=primarySourceIds(s).map(primarySource), historical=(s.sources||[]).map(source).filter(Boolean).slice(0,3);
  return `<section class="atlas-detail-card">${atlasKicker('06 / SOURCES & EVIDENCE',false)}${fresh.map(x=>`<button class="atlas-document-row" data-atlas-action="source" data-id="${esc(x.id)}"><span>▤</span><span>${esc(x.title)}<small>${esc(x.publisher)} · primary disclosure</small></span><time>${esc(x.published_at||('Retrieved '+x.retrieved_at))}</time><span>↗</span></button>`).join('')}${historical.map(x=>`<button class="atlas-document-row" data-action="source" data-id="${esc(x.id)}"><span>▤</span><span>${esc(x.title)}<small>${esc(x.issuer)} · historical / model source</small></span><time>${esc(x.date||'Dated source')}</time><span>↗</span></button>`).join('')}<p class="atlas-card-footnote">Review date ${esc(ATLAS_PRIMARY.published_at||D.meta.built)} · click any record to inspect its source and measurement boundaries.</p></section>`;
}
function atlasNotePanel(s) {
  return `<section class="atlas-detail-card atlas-note-card">${atlasKicker('07 / ANALYST NOTES',false)}<label for="atlas-local-note">Your diligence questions</label><textarea id="atlas-local-note" data-note="${esc(s.id)}" placeholder="What would change your view of this project?" aria-label="Private local research note for ${esc(s.name)}">${esc(saved.notes[s.id]||'')}</textarea><div class="atlas-note-footer"><span>${storageOK?'Private · saved in this browser':'Session-only · storage unavailable'}</span><button class="btn small" data-action="favorite" data-id="${esc(s.id)}">${saved.favorites?.includes(s.id)?'★ On research shelf':'☆ Add to research shelf'}</button></div></section>`;
}
function spatialKpis(scope,phase) {
  const a=spatialAggregate(scope.sites,phase), primary=scope.sites.filter(s=>primarySourceIds(s).length).length;
  return `<div class="atlas-kpi-grid">${metric(a.known?fmt(a.mw/1000,3)+' GW':'—','Named-site '+phase+' IT estimate','Partial, mixed-vintage model subtotal')}${metric(fmt(a.count),'Named projects in this view',a.mapped+' with approximate map anchors')}${metric(fmt(a.known),'Comparable IT-MW estimates',a.unknown+' native / unknown / contract-only')}${metric(fmt(primary),'Projects with primary-source review','Reviewed disclosure layer · not telemetry')}</div>`;
}
function atlasFilterbar() {
  const st=spatialState();
  return `<div class="atlas-filterbar"><label><span>Find a place</span><input id="atlas-map-query" value="${esc(state.filter.q||'')}" placeholder="Site, city, or operator…" autocomplete="off"></label><label><span>Company</span><select id="atlas-company-filter"><option value="all">All companies</option>${D.companies.map(c=>`<option value="${esc(c.id)}" ${state.filter.company===c.id?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label><label><span>Country</span><select id="atlas-country-filter"><option value="all">All countries</option>${[...new Set(D.sites.map(s=>s.country))].sort().map(country=>`<option value="${esc(country)}" ${state.filter.country===country?'selected':''}>${esc(country)}</option>`).join('')}</select></label><label><span>Evidence</span><select id="atlas-evidence-filter">${[['all','All evidence'],['primary','Primary review available'],['reviewed-model','Reviewed models'],['archive','Imported estimates'],['native','Native / contract records']].map(([id,label])=>`<option value="${id}" ${st.spatialEvidence===id?'selected':''}>${label}</option>`).join('')}</select></label><button class="atlas-clear-filters" data-atlas-action="clear-filters">Reset filters</button><button class="atlas-monitor-badge" data-atlas-action="monitor"><i></i><span id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button></div>`;
}
function atlasRecordList(scope,phase) {
  return `<details class="atlas-record-list"><summary><span>Accessible record list</span><span>${scope.sites.length} projects · select without using the map</span></summary><div>${scope.sites.map(s=>`<button data-atlas-action="campus" data-id="${esc(s.id)}"><span>${esc(s.name)}<small>${esc(s.location)} · ${esc(spatialEvidenceLabel(s.review))}</small></span><b>${spatialPower(s,phase)==null?'IT not quantified':fmt(spatialPower(s,phase))+' MW · estimate'}</b><span>↗</span></button>`).join('')||'<p>No records match these filters.</p>'}</div></details>`;
}
function sixScaleGlobeView() {
  const st=spatialState(),s=spatialDefaultSite(),level=st.spatialLevel,phase=st.spatialPhase,scope=spatialScope(level,s),[title,description]=spatialHeadline(level,scope,s);
  return `<div class="atlas-experience atlas-level-${level}"><header class="atlas-intro"><div><div class="atlas-eyebrow">${level>=4?'FACILITY & CAMPUS':'COMPUTE, FROM THE GROUND UP'}</div><h1>${title}</h1>${level>=4&&s?`<p class="atlas-location">⌖ ${esc(s.location)}, ${esc(s.country)}</p>`:''}</div><div class="atlas-intro-aside"><p>${description}</p><button class="btn primary" data-atlas-action="journey">${level>=4?'Return to the guided exploration':'Take the five-stop tour'} ↗</button></div></header>${spatialStageStrip(level)}${atlasFilterbar()}
    <div class="atlas-spatial-layout"><div class="atlas-map-column"><section class="atlas-map-panel">${spatialMap(scope,s,level,phase)}</section>${level>=4&&s?`<div class="atlas-detail-pair">${atlasPowerLadder(s)}${atlasAttributes(s)}</div>`:''}</div><aside class="atlas-spatial-rail" aria-label="Analysis and evidence">${spatialRail(level,scope,s,phase)}</aside></div>
    ${level>=4&&s?`<div class="atlas-bottom-evidence">${atlasSourcesPanel(s)}${atlasNotePanel(s)}</div>`:spatialKpis(scope,phase)}
    <div class="atlas-map-footnote"><span>${esc(scope.note)}</span><button data-atlas-action="source-context">Made with Natural Earth · source details ↗</button></div>${level<4?atlasRecordList(scope,phase):''}</div>`;
}

// Preserve all investment/research depth below the new landscape instead of
// discarding it to achieve a prettier first screen.
overviewView = () => sixScaleGlobeView()+`<details class="atlas-research-depth"><summary>Research depth: evidence lanes, company capital & original analysis <span>↓</span></summary>${evidenceMixPanel()}${investorDashboard()}${countryProfile()}</details>`;
globeView = sixScaleGlobeView;

function spatialURL(view=state.view) {
  if(!['overview','globe'].includes(view))return '#'+view;
  const st=spatialState(),params=new URLSearchParams();params.set('scale',ATLAS_SCALE_LEVELS[st.spatialLevel].key);
  if(st.spatialSelected)params.set('site',st.spatialSelected);
  if(st.spatialPhase!=='snapshot')params.set('phase',st.spatialPhase);
  if(state.filter.company&&state.filter.company!=='all')params.set('company',state.filter.company);
  if(state.filter.country&&state.filter.country!=='all')params.set('country',state.filter.country);
  if(state.filter.q)params.set('q',state.filter.q);
  if(st.spatialEvidence!=='all')params.set('evidence',st.spatialEvidence);
  return '#'+view+'?'+params.toString();
}
function spatialTransition({level,selected,phase,evidence,replace=false}={}) {
  if(selected&&site(selected))state.spatialSelected=selected;
  if(level!=null)state.spatialLevel=Math.max(0,Math.min(5,Math.trunc(Number(level)||0)));
  if(['snapshot','target'].includes(phase)){state.spatialPhase=phase;state.globeLayer=phase;}
  if(evidence)state.spatialEvidence=evidence;
  if(!['overview','globe'].includes(state.view))state.view='globe';
  closeDrawer();
  history[replace?'replaceState':'pushState'](null,'',spatialURL());render();
  const active=document.querySelector('.atlas-scale-step.active');active?.focus({preventScroll:true});
  updateMonitorLabel();
}
const atlasOriginalNavigate=navigate;
navigate=function(view,opts={}) {
  if(![...NAV.map(v=>v[0]),'watchlist','compare'].includes(view))view='overview';
  if(!opts.keepDrawer)closeDrawer();state.view=view;$('#sidebar').classList.remove('open');
  if(!opts.hash)history.pushState(null,'',spatialURL(view));render();window.scrollTo({top:0,behavior:'instant'});updateMonitorLabel();
};
const atlasOldRoute=routeFromHash;
window.removeEventListener('hashchange',atlasOldRoute);
routeFromHash=function() {
  const hash=location.hash.slice(1), [path,query='']=hash.split('?'), params=new URLSearchParams(query);
  if(['overview','globe',''].includes(path)) {
    const key=params.get('scale'), found=ATLAS_SCALE_LEVELS.find(x=>x.key===key);
    state.spatialLevel=found?.id??0;state.spatialSelected=site(params.get('site'))?.id||null;
    state.spatialPhase=params.get('phase')==='target'?'target':'snapshot';state.globeLayer=state.spatialPhase;
    state.spatialEvidence=params.get('evidence')||'all';state.filter.q=params.get('q')||'';
    state.filter.company=company(params.get('company'))?.id||'all';state.filter.country=params.get('country')||'all';
    navigate(path||'overview',{hash:true});return;
  }
  const parts=path.split('/'),kind=parts[0];let id;try{id=decodeURIComponent(parts.slice(1).join('/'));}catch(_){id='';}
  if(['site','company','source'].includes(kind)&&id){
    if(kind==='site'&&site(id))state.spatialSelected=id;
    navigate(kind==='site'?'globe':kind==='company'?'companies':'data',{hash:true});openDrawer(kind,id);return;
  }
  navigate(path||'overview',{hash:true});
};
window.addEventListener('hashchange',routeFromHash);

const atlasOriginalOpenDrawer=openDrawer;
openDrawer=function(kind,id,opts={}) {
  atlasOriginalOpenDrawer(kind,id,opts);
  if(kind==='primary-source') {
    const src=primarySource(id);
    $('#drawer-type').textContent='PRIMARY SOURCE & MEASUREMENT BOUNDARIES';
    $('#drawer-content').innerHTML=src?`<div class="atlas-eyebrow">${esc(src.publisher)} · ${esc(src.id)}</div><h1>${esc(src.title)}</h1><p>${src.published_at?'Published '+esc(src.published_at):'Publication date not stated'} · reviewed ${esc(src.retrieved_at)}</p><a class="btn primary" href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">Open the original disclosure ↗</a><h2>What this source supports</h2>${ATLAS_PRIMARY.observations.filter(o=>o.source_id===id).map(o=>`<div class="atlas-source-observation"><b>${esc(site(o.site_id)?.name||o.site_id)} · ${esc(o.scope)}</b><strong>${observationValue(o)} ${esc(o.unit)}</strong><p>${esc(boundaryLabel(o.boundary))} · ${esc(statusLabel(o.status))}<br>${esc(o.qualifier)}</p></div>`).join('')}${ATLAS_PRIMARY.facts.filter(o=>o.source_id===id).map(o=>`<div class="atlas-source-observation"><b>${esc(o.label)}</b><p>${esc(o.value)}<br>${esc(o.qualifier||'')}</p></div>`).join('')}<h2>Publication policy</h2><p>${esc(ATLAS_PRIMARY.policy)}</p><p>${esc(src.rights)}</p>`:'<p>Source not found.</p>';
  }
  if(kind==='site'&&site(id))$('#drawer-content').insertAdjacentHTML('afterbegin',`<button class="atlas-dossier-map-link" data-atlas-action="campus" data-id="${esc(id)}">← Open this project in the campus atlas</button>`);
};
const atlasOriginalCloseDrawer=closeDrawer;
closeDrawer=function(){const wasOpen=!$('#drawer').hidden;atlasOriginalCloseDrawer();if(wasOpen&&['overview','globe'].includes(state.view))history.replaceState(null,'',spatialURL());};

function atlasContextDrawer() {
  openDrawer('context','geography');$('#drawer-type').textContent='MAP SOURCES & PRECISION';
  $('#drawer-content').innerHTML=`<div class="atlas-eyebrow">NO INVENTED INFRASTRUCTURE</div><h1>A map with an honest boundary.</h1><p>${esc(ATLAS_CONTEXT.attribution||W.attribution||'Natural Earth reference geography')}</p><p>Facility markers use the archived city, county, or region anchors. They are not surveyed site centroids. Land stippling is background cartography, not additional facility records. Roads are generalized reference lines, never represented as power or fiber routes.</p><h2>Reference layers</h2>${(ATLAS_CONTEXT.sources||[]).map(s=>`<div class="atlas-source-observation"><b>${esc(s.layer)} · ${esc(s.scale)}</b><p>${fmt(s.features)} features · ${esc(s.license)}<br>Retrieved ${esc(s.retrieved_at)}</p><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">Original dataset ↗</a><details><summary>Source ZIP SHA-256</summary><code>${esc(s.sha256)}</code></details></div>`).join('')}<h2>At campus / facility scale</h2><p>No exact parcel boundaries, building footprints, transmission routes, or substations are established by this archive. The campus hero is therefore an explicitly labeled evidence schematic, not a fabricated satellite plan.</p>`;
}
let atlasMonitorStatus=null,atlasMonitorError=null,atlasMonitorQueue=[];
function updateMonitorLabel(){const label=$('#atlas-monitor-label');if(!label)return;if(!globalThis.ATLAS_SERVICE)label.textContent='Source-cited · offline ready';else if(atlasMonitorError)label.textContent='Monitor unavailable · cached evidence';else if(atlasMonitorStatus)label.textContent=(atlasMonitorStatus.background_refresh?'Monitoring':'Refresh paused')+' · '+atlasMonitorStatus.counts.pending_review+' awaiting review';}
async function pollAtlasMonitor(){if(!globalThis.ATLAS_SERVICE)return;try{const response=await fetch(ATLAS_SERVICE.base+'/status',{signal:AbortSignal.timeout(5000)});if(!response.ok)throw Error('HTTP '+response.status);atlasMonitorStatus=await response.json();const queue=await fetch(ATLAS_SERVICE.base+'/review-queue',{signal:AbortSignal.timeout(5000)});if(!queue.ok)throw Error('Review queue HTTP '+queue.status);atlasMonitorQueue=(await queue.json()).items;atlasMonitorError=null;}catch(error){atlasMonitorError=String(error.message||error);}updateMonitorLabel();}
function atlasMonitorDrawer(){
  openDrawer('monitor','sources');$('#drawer-type').textContent='SOURCE MONITOR & REVIEW QUEUE';
  const status=atlasMonitorStatus, candidates=ATLAS_PRIMARY.discoveries||[];
  $('#drawer-content').innerHTML=`<div class="atlas-eyebrow">ACQUIRE → VERSION → REVIEW → PUBLISH</div><h1>Fresh sources.<br>Reviewed facts.</h1><p>${globalThis.ATLAS_SERVICE?'This app is connected to the SQLite evidence service.':'This is the self-contained publication. Live acquisition runs in the optional Python service or the scheduled repository workflow, not in an offline HTML file.'}</p><div class="notice">${esc(ATLAS_PRIMARY.policy)}</div>${status?`<div class="metric-grid">${metric(status.counts.source_versions,'Captured source versions','Immutable content hashes')}${metric(status.counts.pending_review,'Awaiting review','Never silently published')}${metric(status.counts.accepted_observations,'Accepted observations','Original scopes retained')}</div><h2>Acquisition status</h2>${status.jobs.map(j=>`<div class="atlas-source-observation"><b>${esc(j.source_id)} · ${j.last_status?'HTTP '+j.last_status:'Not checked yet'}</b><p>Last successful fetch: ${esc(j.last_success||'None')}<br>Next attempt: ${esc(j.next_fetch_at)}${j.last_error?'<br>'+esc(j.last_error):''}</p></div>`).join('')}`:`<h2>Publication reviewed ${esc(ATLAS_PRIMARY.published_at||'at build')}</h2><p>${ATLAS_PRIMARY.sources.length} primary sources, ${ATLAS_PRIMARY.observations.length} typed observations. No claim is made that a background job is running on this static page.</p>`}${globalThis.ATLAS_SERVICE?'<button class="btn" data-atlas-action="monitor-refresh">Refresh monitor status ↻</button><h2>Acquisition review queue</h2>'+atlasMonitorQueue.map(q=>'<div class="atlas-source-observation"><b>'+esc(q.payload.title||q.payload.name||q.kind)+'</b><p>'+esc(q.source_id)+' · '+esc(q.created_at)+'<br>'+esc(q.payload.note||q.payload.url||'Candidate awaiting explicit review.')+'</p></div>').join(''):''}<h2>Research candidates, not accepted site totals</h2>${candidates.map(x=>`<div class="atlas-source-observation"><b>${esc(x.name)}</b><p>${esc(x.location)}<br>${esc(x.note)}</p>${primaryRef(x.source_id)}</div>`).join('')}<h2>Run the evidence service</h2><pre class="atlas-command">pip install -r requirements.txt\npython -m server serve</pre><p>Source checks use conditional requests, immutable hashes, a retry queue, and publisher robots rules. Changed pages and newly discovered feed articles wait for explicit review.</p>`;
}

document.addEventListener('click',event=>{
  const shelf=event.target.closest('.atlas-note-footer [data-action="favorite"]');if(shelf)shelf.textContent=saved.favorites.includes(shelf.dataset.id)?'★ On research shelf':'☆ Add to research shelf';
  const button=event.target.closest('[data-spatial-action]');
  if(button){const action=button.dataset.spatialAction,id=button.dataset.id,st=spatialState();
    if(action==='stage')spatialTransition({level:Number(id)});
    if(action==='phase')spatialTransition({phase:id});
    if(action==='zoom-in')spatialTransition({level:st.spatialLevel+1});
    if(action==='zoom-out')spatialTransition({level:st.spatialLevel-1});
    if(action==='select')spatialTransition({selected:id,level:Math.min(5,st.spatialLevel+1)});
    if(action==='dossier')openDrawer('site',id);
    if(action==='reset'){state.filter={q:'',company:'all',country:'all',review:'all',stage:'all'};state.spatialSelected=null;state.spatialFly='all';state.spatialCamera={};if(globe)globe.skipCameraSave=true;spatialTransition({level:0,evidence:'all',phase:'snapshot'});}
    return;
  }
  const control=event.target.closest('[data-atlas-action]');if(!control)return;
  const action=control.dataset.atlasAction,id=control.dataset.id;
  if(action==='source')openDrawer('primary-source',id);
  if(action==='source-context')atlasContextDrawer();
  if(action==='monitor')atlasMonitorDrawer();
  if(action==='monitor-refresh')pollAtlasMonitor().then(atlasMonitorDrawer);
  if(action==='campus'){state.filter={q:'',company:'all',country:'all',review:'all',stage:'all'};state.spatialEvidence='all';spatialTransition({selected:id,level:4});window.scrollTo({top:0,behavior:'instant'});}
  if(action==='context')spatialTransition({selected:id,level:3});
  if(action==='clear-filters'){state.filter={q:'',company:'all',country:'all',review:'all',stage:'all'};spatialTransition({evidence:'all',replace:true});}
  if(action==='labels'){state.spatialLabels=state.spatialLabels===false;if(globe){globe.labels=state.spatialLabels;globe.dirty=true;}control.setAttribute('aria-pressed',String(state.spatialLabels));}
  if(action==='roads'){state.spatialRoads=state.spatialRoads===false;spatialTransition({replace:true});}
  if(action==='expand'){const panel=control.closest('.atlas-map-panel');panel.classList.toggle('atlas-map-expanded');control.setAttribute('aria-label',panel.classList.contains('atlas-map-expanded')?'Exit expanded map':'Expand map');globe?.resize();}
  if(action==='fly'){
    state.spatialFly=id;
    const views={all:[24,-48,1],americas:[28,-91,1.3],europe:[48,10,1.6],asia:[30,105,1.35],'middle-east':[27,47,1.65]};
    if(globe&&views[id])globe.flyTo(...views[id]);
    document.querySelectorAll('[data-atlas-action="fly"]').forEach(b=>b.classList.toggle('active',b.dataset.id===id));
  }
  if(action==='journey'){state.spatialLevel=0;state.spatialSelected='amazon-anthropic-new-carlisle';startTour();}
  if(action==='export'){const s=site(id);if(s)download(id+'-cited-dossier.json',{publication_date:ATLAS_PRIMARY.published_at,archive:s,primary_observations:primaryObservations(s),primary_facts:primaryFacts(s),primary_relationships:primaryRelationships(s),primary_sources:primarySourceIds(s).map(primarySource),private_note:saved.notes[id]||'',policy:ATLAS_PRIMARY.policy});}
});

document.addEventListener('change',event=>{
  if(event.target.id==='atlas-company-filter'){state.filter.company=event.target.value;spatialTransition({replace:true});}
  if(event.target.id==='atlas-country-filter'){state.filter.country=event.target.value;spatialTransition({replace:true});}
  if(event.target.id==='atlas-evidence-filter')spatialTransition({evidence:event.target.value,replace:true});
});
let atlasQueryTimer;
document.addEventListener('input',event=>{if(event.target.id!=='atlas-map-query')return;const value=event.target.value,start=event.target.selectionStart;clearTimeout(atlasQueryTimer);atlasQueryTimer=setTimeout(()=>{state.filter.q=value;spatialTransition({replace:true});const input=$('#atlas-map-query');input?.focus();input?.setSelectionRange(start,start);},180);});
document.addEventListener('keydown',event=>{
  if(!['overview','globe'].includes(state.view)||/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName)||!$('#drawer').hidden||!$('#search-modal').hidden)return;
  if(event.key==='Escape'){const panel=$('.atlas-map-expanded');if(panel){panel.classList.remove('atlas-map-expanded');globe?.resize();}}
  const tab=event.target.closest('.atlas-scale-step');
  if(tab&&['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const n=event.key==='Home'?0:event.key==='End'?5:Math.max(0,Math.min(5,state.spatialLevel+(event.key==='ArrowRight'?1:-1)));spatialTransition({level:n});return;}
  if(['+','=','-','_'].includes(event.key)){event.preventDefault();spatialTransition({level:state.spatialLevel+(['+','='].includes(event.key)?1:-1)});}
});

// Fresh source context is available in the full archival facility drawer as well.
const atlasPreviousSiteDossier=siteDossier;
siteDossier=function(s){const base=atlasPreviousSiteDossier(s);if(!s||!primarySourceIds(s).length)return base;const first=base.indexOf('<h2>');return base.slice(0,first)+`<section class="atlas-primary-dossier"><h2>New primary-source evidence</h2><p>Reviewed ${esc(ATLAS_PRIMARY.published_at)}. Separate from the dated estimates above.</p>${atlasPowerLadder(s)}${atlasAttributes(s)}${atlasSourcesPanel(s)}</section>`+base.slice(first);};
const atlasPreviousDataView=dataView;
dataView=()=>`<section class="atlas-publication-banner"><span><b>Reviewed primary-source layer</b><small>${ATLAS_PRIMARY.sources.length} sources · ${ATLAS_PRIMARY.observations.length} typed observations · ${esc(ATLAS_PRIMARY.published_at||'')}</small></span><button class="btn" data-atlas-action="monitor">Source monitor & review queue ↗</button></section>`+atlasPreviousDataView();

ATLAS.navigate=navigate;ATLAS.openDrawer=openDrawer;ATLAS.primary=ATLAS_PRIMARY;ATLAS.context=ATLAS_CONTEXT;
ATLAS.spatial={levels:ATLAS_SCALE_LEVELS,state:spatialState,scope:()=>spatialScope(spatialState().spatialLevel,spatialDefaultSite()),aggregate:spatialAggregate,select:id=>{if(site(id))spatialTransition({selected:id});},setLevel:n=>spatialTransition({level:n})};
const buildDate=document.querySelector('.top-date b');if(buildDate){const date=new Date((ATLAS_PRIMARY.published_at||'2026-09-11')+'T00:00:00Z');buildDate.textContent=date.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).toUpperCase();}
routeFromHash();document.documentElement.classList.add('atlas-ready');
// Optional same-origin monitor startup is owned by service-client.js.
