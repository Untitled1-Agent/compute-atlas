'use strict';
const GPU_CLUSTERS=JSON.parse(document.getElementById('gpu-clusters-data').textContent);
const gpuRecord=id=>GPU_CLUSTERS.records.find(r=>r.id===id);
const gpuInventoryRows=GPU_CLUSTERS.records.map(r=>({...r,collection:'gpu',geometry:null,kind:'GPU cluster · '+r.status,date:r.date,
  coordinate_basis:'Epoch AI published coordinates; precision not independently verified',snapshot_mw:null,target_mw:null,claims:0,
  native:r,mapped:Number.isFinite(r.lat)&&Number.isFinite(r.lon),search:[r.id,...Object.values(r.fields)].join(' ').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase()}));
const EPOCH_CENTERS=JSON.parse(document.getElementById('epoch-centers-data').textContent);
const epochCenterRows=EPOCH_CENTERS.tables.centers.records.map(r=>({...r,collection:'epochdc',country:r.fields.Country||'Not supplied',operator:r.fields.Owner||null,place:r.fields.Address||null,lat:null,lon:null,geometry:null,kind:'AI data center · Epoch model',coordinate_basis:'No coordinates in this source table',date:EPOCH_CENTERS.published_at,snapshot_mw:null,target_mw:null,claims:0,source_urls:[EPOCH_CENTERS.url],native:r,mapped:false,search:[r.id,...Object.values(r.fields)].join(' ').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase()}));
