/* Shared, fail-closed publication contract. Independent from the ODbL map catalog. */
window.DirectorySchema = (() => {
  const id = 'DIR-EQUINIX-AVAILABILITY';
  const url = 'https://docs.equinix.com/colocation/availability/';
  const keys = ['id','operator','code','name','source_region','source_country','metro','facility_type','service_coverage','source_id','source_url','coordinates','it_mw'].sort();
  const text = (s, max=500) => typeof s==='string' && s.trim().length>0 && s.length<=max;
  const date = s => typeof s==='string' && /(?:Z|[+-]\d\d:\d\d)$/.test(s) && Number.isFinite(Date.parse(s));
  function validate(d) {
    if(!d || d.schema_version!==1 || d.id!==id || d.url!==url || d.final_url!==url || d.publisher!=='Equinix' || !/^[a-f0-9]{64}$/.test(d.source_sha256||'') || !date(d.captured_at)) throw Error('Invalid operator directory identity');
    if(['title','count_boundary','service_boundary','rights'].some(k=>!text(d[k],2000)) || d.published_at!==null || d.parser_version!==1) throw Error('Invalid directory metadata');
    if(!d.review || !text(d.review.actor,2000) || !text(d.review.note,2000) || !date(d.review.reviewed_at)) throw Error('Directory has no editorial acceptance');
    if(!Array.isArray(d.records) || d.records.length<1 || d.records.length>2000 || d.counts?.records!==d.records.length) throw Error('Invalid directory denominator');
    const seen=new Set(),countries={},regions={};
    for(const r of d.records){
      if(!r || Object.keys(r).sort().join('|')!==keys.join('|') || keys.filter(k=>!['service_coverage','coordinates','it_mw'].includes(k)).some(k=>!text(r[k]))) throw Error('Malformed directory record');
      if(!/^[A-Z]{2}\d{1,3}X?$/.test(r.code) || seen.has(r.code) || r.id!=='equinix-'+r.code.toLowerCase() || r.operator!=='Equinix' || r.name!=='Equinix '+r.code || r.source_id!==id || r.source_url!==url || !['EMEA','APAC','Americas'].includes(r.source_region)) throw Error('Directory source or code mismatch');
      if(r.coordinates!==null || r.it_mw!==null || (r.service_coverage!==null && !text(r.service_coverage))) throw Error('Directory cannot certify geometry or IT power');
      seen.add(r.code); countries[r.source_country]=(countries[r.source_country]||0)+1; regions[r.source_region]=(regions[r.source_region]||0)+1;
    }
    for(const [key,expected] of Object.entries({countries,regions})){
      const actual=d.counts[key];
      if(!actual || Object.keys(actual).length!==Object.keys(expected).length || Object.keys(expected).some(k=>actual[k]!==expected[k])) throw Error('Directory geography denominator mismatch');
    }
    return d;
  }
  function matches(row, features){
    if(!row || !/^[A-Z]{2}\d{1,3}X?$/.test(row.code||'')) return [];
    const country=({USA:'United States',UK:'United Kingdom',UAE:'United Arab Emirates'})[row.source_country]||row.source_country;
    const token=new RegExp('(^|[^A-Z0-9])'+row.code+'(?![A-Z0-9.])','i');
    return features.filter(r=>r.country===country && /\bequinix\b/i.test((r.operator||'')+' '+r.name) && token.test(r.name)).map(r=>r.id).sort();
  }
  return {validate,matches};
})();
