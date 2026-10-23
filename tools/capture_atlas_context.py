"""Capture bounded, source-native map context at published global compute anchors.

These features are surroundings, not inferred campus ownership, service or
project/building matches. Source responses and failed batches remain auditable.
"""
import hashlib,json,time,urllib.request,urllib.parse,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/global-context.json'
CACHE=ROOT/'work/context-captures'
UA='ComputeAtlas/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'

def anchors():
    rows=json.loads((ROOT/'data/catalog/gpu-clusters.json').read_text())['records']
    points={}
    for r in rows:
        if r['anonymous'] or r['lat'] is None:continue
        key=(round(r['lat'],5),round(r['lon'],5))
        points.setdefault(key,{'lat':r['lat'],'lon':r['lon'],'ids':[],'country':r['country']})['ids'].append(r['id'])
    # Source addresses have a separate, explicit geocoding provenance.
    p=ROOT/'data/catalog/atlas-locations.json'
    if p.exists():
        for r in json.loads(p.read_text())['records']:
            if not r['response']:continue
            hit=r['response'][0]
            if int(hit.get('place_rank',0))<26:continue
            lat,lon=float(hit['lat']),float(hit['lon']);key=(round(lat,5),round(lon,5))
            points.setdefault(key,{'lat':lat,'lon':lon,'ids':[],'country':r['source_country']})['ids'].append(r['id'])
    return list(points.values())

def query_for(batch):
    return '[out:json][timeout:45];('+''.join(f'way(around:750,{p["lat"]},{p["lon"]})[~"^(building|highway|power|telecom|waterway)$"~"."];node(around:750,{p["lat"]},{p["lon"]})["power"~"substation|plant|generator"];' for p in batch)+');out meta geom;'

def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    locations=anchors();captures=[];elements={};failures=[]
    plans=[]
    for start in range(0,len(locations),4):
        batch=locations[start:start+4];query=query_for(batch);key=hashlib.sha256(query.encode()).hexdigest()
        if not (CACHE/(key+'.json')).exists():plans.extend([[anchor] for anchor in batch])
        else:plans.append(batch)
    print('Published map anchors:',len(locations),flush=True)
    completed=0
    for batch in plans:
        start=completed;completed+=len(batch);query=query_for(batch)
        key=hashlib.sha256(query.encode()).hexdigest();cache=CACHE/(key+'.json');raw=None
        if cache.exists():raw=cache.read_bytes()
        else:
            for host in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
                try:
                    url=host+'?'+urllib.parse.urlencode({'data':query})
                    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=65) as response:raw=response.read(40000001)
                    if len(raw)>40000000:raise ValueError('Oversized bounded response')
                    data=json.loads(raw)
                    if 'remark' in data:raise ValueError(data['remark'])
                    if 'elements' not in data:raise ValueError('Missing elements')
                    cache.write_bytes(raw);break
                except Exception as error:raw=None;print('Retry',start,str(error),flush=True)
                time.sleep(2)
            time.sleep(1.1)
        if raw is None:
            failures.append({'anchors':batch,'query':query});print('Unavailable',completed,'of',len(locations),flush=True);continue
        data=json.loads(raw);ids=[]
        for e in data['elements']:
            eid=f'osm-{e["type"]}-{e["id"]}';ids.append(eid)
            if eid not in elements or e.get('version',0)>=elements[eid].get('version',0):elements[eid]=e
        captures.append({'id':key,'anchors':batch,'radius_m':750,'query':query,'response_sha256':hashlib.sha256(raw).hexdigest(),'osm_base':data.get('osm3s',{}).get('timestamp_osm_base'),'element_ids':ids})
        publication={'schema_version':1,'captured_at':datetime.now(timezone.utc).isoformat(),'publisher':'OpenStreetMap via Overpass','url':'https://www.openstreetmap.org','license':'ODbL-1.0','license_url':'https://www.openstreetmap.org/copyright','attribution':'© OpenStreetMap contributors','policy':'Native nearby map context around published or address-geocoded compute anchors. Proximity does not establish campus membership, ownership, utility service, energized state, fiber connectivity or IT power. Native object revisions and tags remain separate from project disclosures.','captures':captures,'failures':failures,'elements':elements}
        temporary=OUT.with_suffix('.tmp');temporary.write_text(json.dumps(publication,ensure_ascii=False,separators=(',',':'))+'\n');temporary.replace(OUT)
        print(f'{completed}/{len(locations)} anchors; {len(elements)} native features; {len(failures)} failed batches',flush=True)

    if captures:
        publication.update(captures=captures,failures=failures,elements=elements)
        temporary=OUT.with_suffix('.tmp');temporary.write_text(json.dumps(publication,ensure_ascii=False,separators=(',',':'))+'\n');temporary.replace(OUT)
    if failures:raise SystemExit(f'{len(failures)} source batches unavailable; cached successes retained. Rerun to retry smaller source queries.')

if __name__=='__main__':main()
