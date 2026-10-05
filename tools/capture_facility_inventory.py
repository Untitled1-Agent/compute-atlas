"""Capture licensed, global OSM data-center geometry for review, not publication.

No accounts, tiles, private datasets or network-contact details are collected.
Run with Python 3.10+: python tools/capture_facility_inventory.py --output var/inventory-capture
A complete Overpass response is required; partial responses fail closed. The raw
capture is an ODbL database. A successful fetch does not certify operation or IT MW.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, time, urllib.request
from pathlib import Path

QUERY = '''[out:json][timeout:240];
(nwr["telecom"="data_center"];
 nwr["building"="data_center"];
 nwr["industrial"~"^(data_centre|data_center)$"];
 nwr["construction:telecom"="data_center"];
 nwr["proposed:telecom"="data_center"];
 nwr["construction"="data_center"];
 nwr["disused:telecom"="data_center"];
 nwr["abandoned:telecom"="data_center"];
);out meta geom;'''
ENDPOINTS = ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter')
COUNTRIES = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson'
AGENT = 'ComputeAtlasResearch/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'
MAX_BYTES = 80 * 1024 * 1024


def capture(url: str, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={'User-Agent': AGENT, 'Accept': 'application/json', 'Content-Type': 'text/plain; charset=utf-8'})
    with urllib.request.urlopen(req, timeout=300) as response:
        if response.status != 200:
            raise ValueError(f'Unexpected response: {response.status}')
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError('Capture exceeds size limit')
        return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('var/inventory-capture'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    errors = []
    for endpoint in ENDPOINTS:
        try:
            body = capture(endpoint, QUERY.encode())
            payload = json.loads(body)
            if payload.get('remark') or not isinstance(payload.get('elements'), list) or len(payload['elements']) < 100:
                raise ValueError('Incomplete or unexpectedly small Overpass capture')
            break
        except Exception as exc:
            errors.append({'url': endpoint, 'error': str(exc)})
            time.sleep(10)
    else:
        (args.output / 'failure.json').write_text(json.dumps(errors, indent=2))
        raise SystemExit('No complete capture available; existing publication is unchanged')
    # Do not redistribute mapper account names/IDs, although the source API is public.
    for row in payload['elements']:
        row.pop('user', None)
        row.pop('uid', None)
    sanitized = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    (args.output / 'osm-datacenters.json').write_bytes(sanitized)
    countries = capture(COUNTRIES)
    json.loads(countries)
    (args.output / 'countries.geojson').write_bytes(countries)
    manifest = {'schema_version': 1, 'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'osm_timestamp': payload.get('osm3s', {}).get('timestamp_osm_base'), 'endpoint': endpoint,
        'query': QUERY, 'query_sha256': hashlib.sha256(QUERY.encode()).hexdigest(),
        'response_sha256': hashlib.sha256(body).hexdigest(), 'sanitized_sha256': hashlib.sha256(sanitized).hexdigest(),
        'element_count': len(payload['elements']), 'license': 'ODbL-1.0',
        'license_url': 'https://opendatacommons.org/licenses/odbl/1-0/',
        'attribution': '© OpenStreetMap contributors', 'attribution_url': 'https://www.openstreetmap.org/copyright',
        'countries': {'url': COUNTRIES, 'sha256': hashlib.sha256(countries).hexdigest(), 'license': 'Public domain; Natural Earth'},
        'errors_before_success': errors,
        'limitations': 'Community mapping, not a complete facility census. Tagged buildings, campus areas and points may overlap. Geometry is not surveyed. No IT capacity or operating status is inferred from a map tag.'}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(manifest, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
