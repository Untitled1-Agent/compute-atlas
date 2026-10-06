"""Weekly global OSM capture. Fixed public endpoints; no app facts are published.

The output is a candidate capture. Normalize and explicitly accept it after review.
No user-supplied URL or source tag is ever fetched by this program.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

QUERY='[out:json][timeout:240][maxsize:268435456];('+''.join('nwr["'+k+'"="'+v+'"];' for k in ('telecom','building','industrial','construction:telecom','proposed:telecom','disused:telecom','abandoned:telecom','construction','proposed') for v in ('data_center','data_centre'))+');out meta geom;'
ENDPOINTS=('https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter')
COUNTRIES='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson'

def fetch(url, query=None):
    if url not in (*ENDPOINTS,COUNTRIES):raise ValueError('Unregistered endpoint')
    command=['curl','--fail','--silent','--show-error','--proto','=https','--connect-timeout','20','--max-time','280','--max-filesize','30000000','--user-agent','ComputeAtlasResearch/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)',url]
    if query is not None:command+=['--data-urlencode','data='+query]
    return subprocess.run(command,check=True,capture_output=True,timeout=290).stdout

def capture(output):
    output.mkdir(parents=True,exist_ok=True);errors=[]
    try:
        country=fetch(COUNTRIES);json.loads(country)
        for endpoint in ENDPOINTS:
            try:
                raw=fetch(endpoint,QUERY);data=json.loads(raw)
                if data.get('remark') or not data.get('elements'):raise ValueError('Incomplete/empty response: '+str(data.get('remark')))
                break
            except (ValueError,subprocess.SubprocessError) as e:
                errors.append(endpoint+': '+str(e));time.sleep(5)
        else:raise ValueError('All source endpoints failed')
        for row in data['elements']:row.pop('user',None);row.pop('uid',None)
        body=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
        manifest={'schema_version':1,'retrieved_at':datetime.now(timezone.utc).isoformat(),'osm_timestamp':data['osm3s']['timestamp_osm_base'],'endpoint':endpoint,'query':QUERY,'query_sha256':hashlib.sha256(QUERY.encode()).hexdigest(),'response_sha256':hashlib.sha256(raw).hexdigest(),'sanitized_sha256':hashlib.sha256(body).hexdigest(),'element_count':len(data['elements']),'license':'ODbL-1.0','license_url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors','attribution_url':'https://www.openstreetmap.org/copyright','countries':{'url':COUNTRIES,'sha256':hashlib.sha256(country).hexdigest(),'license':'Public domain; Natural Earth'},'errors_before_success':errors,'limitations':'Candidate community map features, not a census, operating status or IT-power publication.'}
        for name,value in [('osm-datacenters.json',body),('countries.geojson',country),('manifest.json',json.dumps(manifest,indent=2).encode())]:
            path=output/name;temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(value);temp.replace(path)
        return manifest
    except Exception as e:
        (output/'failure.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'error':str(e),'attempts':errors,'publication_unchanged':True},indent=2));raise

def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();print(json.dumps(capture(args.output),indent=2))
if __name__=='__main__':main()
