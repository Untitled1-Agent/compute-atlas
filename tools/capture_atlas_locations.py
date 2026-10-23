"""Resolve published center addresses without altering publisher coordinates.

Nominatim's one-request-per-second policy is respected. Responses are cached,
including misses, and retained with original response digests. Address results are contextual map
anchors, not verified project identities or surveyed facility coordinates.
"""
import hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = 'ComputeAtlas/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'
OUT = ROOT / 'data/catalog/atlas-locations.json'

def main():
    centers=json.loads((ROOT/'data/catalog/epoch-data-centers.json').read_text())['tables']['centers']['records']
    previous=json.loads(OUT.read_text()) if OUT.exists() else {'records':[]}
    cache={r['id']:r for r in previous['records']}
    for center in centers:
        fields=center['fields'];address=fields.get('Address','').strip();country=fields.get('Country','').strip()
        query=', '.join(x for x in [address,country] if x)
        if center['id'] in cache and cache[center['id']]['query']==query:continue
        row={'id':center['id'],'source_address':address,'source_country':country,'query':query,'captured_at':datetime.now(timezone.utc).isoformat(),'response':[],'status':'no_address'}
        if address:
            url='https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode({'q':query,'format':'jsonv2','limit':1,'addressdetails':1})
            row['url']=url
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=25) as response:raw=response.read(100000)
                row['response']=json.loads(raw);row['response_sha256']=hashlib.sha256(raw).hexdigest();row['status']='resolved' if row['response'] else 'no_match'
            except Exception as error:row['status']='unavailable';row['error']=str(error)
            time.sleep(1.1)
        cache[row['id']]=row
        publication={'schema_version':1,'publisher':'OpenStreetMap Nominatim','captured_at':datetime.now(timezone.utc).isoformat(),'license':'ODbL-1.0','license_url':'https://www.openstreetmap.org/copyright','attribution':'© OpenStreetMap contributors','policy':'Geocoded publisher addresses, independent from source coordinates. A match identifies an address or locality, not a reviewed project-to-building correspondence. Source fields and native identities are unchanged.','records':list(cache.values())}
        OUT.write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n')
        print(center['name'],row['status'],flush=True)

if __name__=='__main__':main()
