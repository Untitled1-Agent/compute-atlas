"use strict";
/* Geographic navigation uses the full native catalog, including every continent. */
const geoPlaceCache = new Map();
let geoBrowseRegion = "All", geoBrowseQuery = "";

function geoCountries(rows = uaRecords()) {
  const groups = new Map();
  for (const row of rows) {
    if (["Unknown", "Not supplied", ""].includes(row.country)) continue;
    if (!groups.has(row.country)) groups.set(row.country, {name:row.country, rows:[], regions:new Set()});
    const group = groups.get(row.country); group.rows.push(row); group.regions.add(row.region);
  }
  return [...groups.values()].sort((a,b)=>b.rows.length-a.rows.length||a.name.localeCompare(b.name));
}
function geoPlace(row) {
  if (geoPlaceCache.has(row.id)) return geoPlaceCache.get(row.id);
  const native = row.native.city;
  let label = typeof native === "string" && native.trim() ? native.trim() : "", distance = 100;
  if (!label) for (const place of ATLAS_CONTEXT.places || []) {
    const d = spatialDistance(place,row);
    if (d < distance) { distance=d; label=place.name; }
  }
  if (!label) label = `${row.country} · ${row.lat.toFixed(1)}°, ${row.lon.toFixed(1)}°`;
  geoPlaceCache.set(row.id,label); return label;
}
function geoMarkets(rows) {
  const groups = new Map();
  for (const row of rows.filter(r=>r.mapped)) {
    const name=geoPlace(row), key=row.country+"|"+inventoryText(name);
    if (!groups.has(key)) groups.set(key,{key,name,country:row.country,rows:[]});
    groups.get(key).rows.push(row);
  }
  return [...groups.values()].sort((a,b)=>b.rows.length-a.rows.length||a.name.localeCompare(b.name));
}
function geoRepresentative(rows) {
  const scored = rows.filter(r=>r.mapped).map(r=>({r,score:
    (CAMPUS_SCENES.scenes.some(s=>s.project_id===r.id)?100000:0)+
    (r.geometry?10000:0)+(uaCaptureFor(r)?2000:0)+
    (r.operator&&!/unknown|not supplied/i.test(r.operator)?100:0)+
    (!/^(mapped|unnamed|data cent[er]+$|[\d\s-]+$)/i.test(r.name)?200:0)+Math.min(Object.keys(r.native.tags||{}).length,30)}));
  return scored.sort((a,b)=>b.score-a.score||a.r.name.localeCompare(b.r.name))[0]?.r;
}
function geoIsReferenceRegion() {
  const b=uaState.camera?.bounds;
  return uaState.scale===2&&uaState.country==="United States"&&uaState.scope==="viewport"&&b&&b.every((v,i)=>Math.abs(v-[-96,30,-69,47][i])<.01);
}
function geoCountry(name, clear=false) {
  uaGo({...(clear?{q:"",operator:"",coverage:"all",collection:"all"}:{}), region:"All", country:name, selected:null, feature:null, phase:null, scene:null, sceneCamera:null, scale:2, camera:null, scope:"geography"});
}
function geoMarket(key) {
  const group=geoMarkets(uaRows()).find(g=>g.key===key); if (!group) return;
  const bounds=uaFitBounds(group.rows,null,.12,.09), lon=(bounds[0]+bounds[2])/2, lat=(bounds[1]+bounds[3])/2;
  uaGo({country:group.country,region:"All",scale:3,selected:null,feature:null,phase:null,scene:null,sceneCamera:null,scope:"viewport",camera:{flat:true,lat,lon,zoom:1,bounds}});
}
function geoMarketRows(groups, count=5) {
  return `<div class="ua-ranks ui-source-ranking">${groups.slice(0,count).map((g,i)=>`<button data-geo-market="${esc(g.key)}"><span>${String(i+1).padStart(2,"0")}</span><b>${esc(g.name)}</b><strong>${fmt(g.rows.length)}</strong></button>`).join("")}</div><small>Source locations grouped by published city or nearby reference place.</small>`;
}
function geoLocalHeading() {
  const markets=geoMarkets(uaRows());
  return markets[0] ? markets[0].name+" area" : uaState.country!=="All"?uaState.country:"Local infrastructure";
}
const geoOriginalTitle=uiTitle;
uiTitle=function(record) {
  if (uaState.scale===2&&uaState.country==="United States"&&!geoIsReferenceRegion()) return ["United States.<br>Infrastructure in focus.",""];
  if (uaState.scale===3&&!record) return [esc(geoLocalHeading())+".","Explore the places, operators and physical sources in this map."];
  return geoOriginalTitle(record);
};
const geoOriginalRail=uaWorldRail;
uaWorldRail=function(rows) {
  const global=uaState.region==="All"&&uaState.country==="All"&&uaState.scale===0;
  const atlantic=uaState.scale===1&&uaState.country==="All"&&["All","Atlantic"].includes(uaState.region);
  if (global||atlantic||geoIsReferenceRegion()) return geoOriginalRail(rows);
  const country=uaState.country!=="All", local=uaState.scale===3, label=local?geoLocalHeading():country?uaState.country:uaState.region;
  const countries=geoCountries(rows), markets=geoMarkets(rows), next=geoRepresentative(rows), model=uiModel(rows);
  const action=country&&markets[0]?`data-geo-market="${esc(markets[0].key)}"`:countries[0]?`data-geo-country="${esc(countries[0].name)}"`:"data-geo-browse";
  const nextLabel=country&&markets[0]?"Explore "+markets[0].name:countries[0]?"Explore "+countries[0].name:"Browse the world";
  return `<section class="ua-editorial geo-scope-rail">${uiKicker("01 / "+(local?"LOCAL LANDSCAPE":country?"COUNTRY FOCUS":"REGIONAL TAKEAWAY"))}<h2>${esc(label)}.<br>Compute, in place.</h2><p>${fmt(rows.length)} native source records across ${new Set(rows.map(r=>r.collection)).size} publications. Follow the mapped locations, operators and original evidence in this scope.</p><dl class="ua-facts"><div><dt>Mapped locations</dt><dd>${fmt(rows.filter(r=>r.mapped).length)}</dd></div><div><dt>Native outlines</dt><dd>${fmt(rows.filter(r=>r.geometry).length)}</dd></div><div><dt>Published facility power</dt><dd>${uiPower(model.power)}</dd></div></dl><small>Epoch current-power model · ${model.known} quantified centers. Native publications may overlap.</small><button class="text-button" ${action}>${esc(nextLabel)} ${uiIcon("arrow")}</button></section><section class="ua-editorial">${uiKicker("02 / "+(country?"LOCAL CONCENTRATIONS":"COUNTRIES & TERRITORIES"))}<h2>${country?"Places behind<br>the footprint.":"A connected<br>regional landscape."}</h2>${country?geoMarketRows(markets):uiSourceRanking(rows,"country",5)}<button class="text-button" ${country?"data-geo-markets":"data-geo-browse"}>${country?"All local source groups":"Browse every country"} ${uiIcon("arrow")}</button></section><section class="ua-editorial">${uiKicker("03 / "+(next?"GO INSIDE A LOCATION":"SOURCE COVERAGE"))}<h2>${next?esc(next.name):"Keep every source<br>in view."}</h2><p>${next?esc(next.operator||next.country)+" · "+(next.geometry?"Inspect its native mapped outline and original source fields.":CAMPUS_SCENES.scenes.some(s=>s.project_id===next.id)?"Explore dated imagery and independently reviewed physical evidence.":"Explore the published location and independently mapped surroundings."):"Unlocated records remain available in the directory and exports. No location or capacity is invented."}</p><button class="text-button" ${next?`data-geo-inside="${esc(next.id)}"`:"data-geo-browse"}>${next?"Inspect physical context":"Browse source geography"} ${uiIcon("arrow")}</button></section>`;
};
function geoMapLabel() {
  if (uaState.scale>=4) return "Campus site map";
  if (uaState.scale===3) return "Local facilities & infrastructure";
  if (geoIsReferenceRegion()) return "US East & Midwest compute map";
  if (uaState.country!=="All") return uaState.country+" compute map";
  if (uaState.scale===1&&["All","Atlantic"].includes(uaState.region)) return "North America – Europe";
  if (uaState.region!=="All") return uaState.region+" compute map";
  return uaState.scale===2?"Regional compute map":"Global compute map";
}
const geoOriginalMap=uiMap;
uiMap=function(...args) { return geoOriginalMap(...args).replace(/(<div class="ua-map-head"><div><h2>)[\s\S]*?(<\/h2>)/,(_,a,b)=>a+esc(geoMapLabel())+b); };

function geoBreadcrumbs() {
  if (state.view!=="atlas") return;
  const r=uaRecord(uaState.selected), parts=[`<button data-geo-world>The landscape</button>`];
  const region=uaState.region!=="All"?uaState.region:uaState.scale>=2?r?.region:null;
  const country=uaState.country!=="All"?uaState.country:uaState.scale>=3?r?.country:null;
  if (region&&region!=="Not supplied") parts.push(`<button data-ua-region="${esc(region)}">${esc(region)}</button>`);
  if (country&&country!=="Not supplied") parts.push(`<button data-geo-country="${esc(country)}">${esc(country)}</button>`);
  if (r&&uaState.scale>=3) parts.push(`<button data-geo-parent="${esc(r.id)}">${esc(r.name)}</button>`);
  parts.push(`<span aria-current="page">${esc(UA_SCALES[uaState.scale])}</span>`);
  $("#breadcrumb").innerHTML=`<span class="geo-breadcrumb" aria-label="Atlas location">${parts.join('<span aria-hidden="true">›</span>')}</span>`;
}
const geoOriginalNav=renderNav;
renderNav=function(){geoOriginalNav();geoBreadcrumbs();};
const geoOriginalView=uaView;
uaView=function(){return geoOriginalView().replace(/(<nav class="ua-regions"[\s\S]*?)(<\/nav>)/,(_,a,b)=>a+`<button class="geo-browse-link" data-geo-browse>Browse the world ${uiIcon("arrow")}</button>`+b);};
const geoOriginalRefresh=uaRefreshData;
uaRefreshData=function(){
  geoOriginalRefresh(); if(state.view!=="atlas")return;
  const r=uaRecord(uaState.selected),[title,subtitle]=uiTitle(r),intro=$('.ua-intro > div:first-child');
  if(intro){intro.querySelector('h1').innerHTML=title;let p=intro.querySelector('.ui-subtitle');if(subtitle&&!p){p=document.createElement('p');p.className='ui-subtitle';intro.append(p);}if(p){p.textContent=subtitle;p.hidden=!subtitle;}}
  $('.ui-editorial-atlas')?.setAttribute('data-ua-scale',String(uaState.scale));
  const caption=$('.ua-map-head h2');if(caption)caption.textContent=geoMapLabel();
  const chips=$('.ui-active-filters');if(chips)chips.innerHTML=uiFilterChips();geoBreadcrumbs();
};

function geoBrowseContent() {
  const rows=geoCountries().filter(g=>(geoBrowseRegion==="All"||g.regions.has(geoBrowseRegion))&&inventoryText(g.name).includes(inventoryText(geoBrowseQuery)));
  return rows.map(g=>`<button class="geo-destination" data-geo-open-country="${esc(g.name)}"><span>${esc([...g.regions].join(' · '))}</span><strong>${esc(g.name)}</strong><div><b>${fmt(g.rows.length)}</b> source records ${uiIcon("arrow")}</div><small>${fmt(g.rows.filter(r=>r.mapped).length)} mapped · ${fmt(g.rows.filter(r=>r.geometry).length)} native outlines</small></button>`).join('')||'<p class="empty">No matching country or territory. Clear the search or choose another region.</p>';
}
function geoBrowse() {
  geoBrowseRegion="All";geoBrowseQuery="";openDrawer("global-destinations");
  $('#drawer-type').textContent="GLOBAL EXPLORATION";
  $('#drawer-content').innerHTML=`<div class="geo-browser"><div class="eyebrow">ALL SIX SOURCE COLLECTIONS</div><h1>Choose a place.<br>Follow the evidence.</h1><p>${fmt(uaRecords().length)} source records across ${geoCountries().length} named countries and territories. Each destination opens the full local source scope.</p><label for="geo-country-query">Find a country or territory</label><input type="search" id="geo-country-query" placeholder="Japan, Germany, Brazil…"><nav class="geo-region-tabs" aria-label="Destination regions">${catalogRegions.map(r=>`<button data-geo-browser-region="${esc(r)}" aria-pressed="${r==='All'}">${r==='All'?'All regions':esc(r)}</button>`).join('')}</nav><div class="geo-destinations" id="geo-destinations">${geoBrowseContent()}</div><p class="geo-boundary">Counts are native source records, not a deduplicated facility census. Records without coordinates remain in the directory and exports.</p><button class="btn" data-geo-unmapped>Explore records without map coordinates</button></div>`;
  $('#geo-country-query').focus();
}
function geoAllMarkets() {
  const groups=geoMarkets(uaRows());openDrawer('local-source-groups');$('#drawer-type').textContent='LOCAL SOURCE GEOGRAPHY';
  $('#drawer-content').innerHTML=`<h1>Explore the local landscape.</h1><p>${groups.length} groups in the current scope. Names use the source city or a nearby Natural Earth reference place; map bounds cover the actual source records.</p><div class="geo-market-list">${groups.map(g=>`<button data-geo-market="${esc(g.key)}"><span><strong>${esc(g.name)}</strong><small>${esc(g.country)} · ${new Set(g.rows.map(r=>r.collection)).size} source collections</small></span><b>${fmt(g.rows.length)}</b>${uiIcon('arrow')}</button>`).join('')||'<p>No mapped locations match this scope. Records without coordinates remain available below the map.</p>'}</div>`;
}
document.addEventListener('input',event=>{
  if(event.target.id==='geo-country-query'){geoBrowseQuery=event.target.value;$('#geo-destinations').innerHTML=geoBrowseContent();}
});
document.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;const d=button.dataset;
  if('geoBrowse'in d)geoBrowse();
  if('geoBrowserRegion'in d){geoBrowseRegion=d.geoBrowserRegion;document.querySelectorAll('[data-geo-browser-region]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.geoBrowserRegion===geoBrowseRegion)));$('#geo-destinations').innerHTML=geoBrowseContent();}
  if('geoOpenCountry'in d)geoCountry(d.geoOpenCountry,true);
  if('geoCountry'in d)geoCountry(d.geoCountry);
  if('geoMarkets'in d)geoAllMarkets();
  if('geoMarket'in d)geoMarket(d.geoMarket);
  if('geoInside'in d){const r=uaRecord(d.geoInside);if(r)uaGo({selected:r.id,scale:r.geometry?5:4,camera:null,sceneCamera:null,feature:r.geometry?r.id:null,phase:null,scene:null,mode:'3d',scope:'geography'});}
  if('geoParent'in d)uaGo({selected:d.geoParent,scale:uaRecord(d.geoParent)?.geometry?3:4,feature:null,phase:null,camera:null,sceneCamera:null});
  if('geoWorld'in d)uaGo({scale:0,region:'All',country:'All',selected:null,feature:null,phase:null,scene:null,camera:null,sceneCamera:null,scope:'geography'});
  if('geoUnmapped'in d)uaGo({scale:0,region:'All',country:'All',q:'',operator:'',collection:'all',coverage:'unmapped',selected:null,feature:null,phase:null,camera:null,sceneCamera:null,scope:'geography'});
});
