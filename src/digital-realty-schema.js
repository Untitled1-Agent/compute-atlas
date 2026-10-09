/* Publisher data is a separate reviewed projection, never OSM geometry or IT load. */
window.DigitalRealtySchema = (() => {
  const id='DIR-DIGITAL-REALTY-LOCATIONS',url='https://www.digitalrealty.com/data-centers';
  const keys=['id','operator','code','name','source_region','source_country','metro','facility_type','service_coverage','source_id','source_url','coordinates','it_mw','source_node_id','source_title','source_continent'].sort();
  const text=(s,max=500)=>typeof s==='string'&&s.trim().length>0&&s.length<=max;
  const date=s=>{
    if(typeof s!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(s)||!Number.isFinite(Date.parse(s)))return false;
    const [y,m,d]=s.slice(0,10).split('-').map(Number);return m>=1&&m<=12&&d>=1&&d<=new Date(Date.UTC(y,m,0)).getUTCDate();
  };
  function validate(d){
    if(!d||d.schema_version!==1||d.parser_version!==1||d.id!==id||d.url!==url||d.final_url!==url||d.publisher!=='Digital Realty'||!/^[a-f0-9]{64}$/.test(d.source_sha256||'')||!date(d.captured_at)||d.published_at!==null)throw Error('Invalid Digital Realty source');
    if(['title','rights','count_boundary','service_boundary'].some(k=>!text(d[k],2000))||!d.review||!text(d.review.actor,2000)||!text(d.review.note,2000)||!date(d.review.reviewed_at))throw Error('Missing Digital Realty editorial acceptance');
    if(!Array.isArray(d.records)||d.records.length<1||d.records.length>2000||d.counts?.records!==d.records.length)throw Error('Invalid publisher denominator');
    const seen=new Set(),urls=new Set(),countries=Object.create(null),regions=Object.create(null);
    for(const r of d.records){
      if(!r||Object.keys(r).sort().join('|')!==keys.join('|')||keys.filter(k=>!['coordinates','it_mw','service_coverage','source_country','source_continent'].includes(k)).some(k=>!text(r[k])))throw Error('Malformed publisher record');
      if(['source_country','source_continent'].some(k=>r[k]!==null&&!text(r[k]))||!/^\d+$/.test(r.source_node_id)||r.source_node_id[0]==='0'||r.id!=='digital-realty-'+r.source_node_id||seen.has(r.id)||urls.has(r.source_url))throw Error('Invalid publisher identity');
      if(r.operator!=='Digital Realty'||r.source_id!==id||r.name!=='Digital Realty '+r.source_title.trim()||!/^https:\/\/www\.digitalrealty\.com\/data-centers\/(emea|americas|asia-pacific)\/[a-z0-9-]+\/[a-z0-9-]+$/.test(r.source_url)||!['EMEA','APAC','Americas'].includes(r.source_region))throw Error('Unregistered publisher record');
      const p=r.coordinates;
      if(!p||Object.keys(p).sort().join('|')!=='basis|lat|lon'||p.basis!=='publisher_pin'||!Number.isFinite(p.lat)||!Number.isFinite(p.lon)||Math.abs(p.lat)>90||Math.abs(p.lon)>180||r.it_mw!==null||r.service_coverage!==null)throw Error('Publisher pin is not geometry or IT capacity');
      seen.add(r.id);urls.add(r.source_url);const c=r.source_country||'Not specified';countries[c]=(countries[c]||0)+1;regions[r.source_region]=(regions[r.source_region]||0)+1;
    }
    for(const [k,x] of Object.entries({countries,regions})){const a=d.counts[k];if(!a||Object.keys(a).length!==Object.keys(x).length||Object.keys(x).some(key=>a[key]!==x[key]))throw Error('Publisher grouping denominator mismatch');}
    return d;
  }
  function flags(r){
    const result=[];
    if(r.source_country===null)result.push('Country group is missing in the source.');
    if(r.metro==='Dublin'&&r.source_country==='United Kingdom')result.push('Source locality/group conflict: Dublin is grouped under United Kingdom. Preserved as published, not verified jurisdiction.');
    if(['Cile','Bogota'].includes(r.source_country))result.push('Nonstandard source country heading: '+r.source_country+'. Not silently normalized.');
    if(r.code.includes('+')||r.source_title.includes('+'))result.push('Compound publisher entry. Not split into individual buildings.');
    return result;
  }
  return {validate,flags};
})();
