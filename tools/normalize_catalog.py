"""Normalize a checksum-verified OSM capture without inventing facility capacity.

Standard library only. Outputs an ODbL map-feature database, NOT a facility census.
Geographic containment and relation membership are explicit, never entity merges.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from collections import Counter
from pathlib import Path

LICENSE = 'ODbL-1.0'
POLICY = ('Community map features, not a complete or deduplicated facility census. '
          'Buildings, campus areas and points can overlap. Tags do not certify '
          'operation, ownership, surveyed geometry or available IT power.')

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def point(value):
    return isinstance(value, (list, tuple)) and len(value) == 2 and all(finite(v) for v in value) and -180 <= value[0] <= 180 and -90 <= value[1] <= 90

def ring_inside(p, ring):
    x, y = p; inside = False
    for a, b in zip(ring, ring[1:]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0]) * (y-a[1]) / (b[1]-a[1]) + a[0]:
            inside = not inside
    return inside

def box(ring):
    return [min(p[0] for p in ring), min(p[1] for p in ring), max(p[0] for p in ring), max(p[1] for p in ring)]

def in_box(p, b):
    return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]

def closed_ring(raw):
    pts = [[p.get('lon'), p.get('lat')] for p in raw if isinstance(p, dict)]
    return pts if len(pts) >= 4 and pts[0] == pts[-1] and all(point(p) for p in pts) else None

def stitch(segments):
    """Join only actual shared endpoints. Never close an incomplete relation by guess."""
    pending = [s for s in segments if len(s) >= 2 and all(point(p) for p in s)]
    rings = []
    while pending:
        chain = pending.pop(0)
        while chain[0] != chain[-1]:
            found = False
            for i, s in enumerate(pending):
                if chain[-1] == s[0]: chain += s[1:]
                elif chain[-1] == s[-1]: chain += list(reversed(s))[1:]
                elif chain[0] == s[-1]: chain = s[:-1] + chain
                elif chain[0] == s[0]: chain = list(reversed(s))[:-1] + chain
                else: continue
                pending.pop(i); found = True; break
            if not found: break
        if len(chain) >= 4 and chain[0] == chain[-1]: rings.append(chain)
    return rings

def geometry(row):
    if row['type'] == 'way':
        ring = closed_ring(row.get('geometry', []))
        return {'type':'MultiPolygon', 'coordinates':[[ring]]} if ring else None
    if row['type'] != 'relation' or row.get('tags', {}).get('type') != 'multipolygon': return None
    roles = {'outer':[], 'inner':[]}
    for m in row.get('members', []):
        if m.get('type') == 'way' and m.get('role', 'outer') in ('outer', 'inner', ''):
            roles[m.get('role') or 'outer'].append([[p.get('lon'), p.get('lat')] for p in m.get('geometry', [])])
    outer, inner = stitch(roles['outer']), stitch(roles['inner'])
    polys = [[r] + [h for h in inner if ring_inside(h[0], r)] for r in outer]
    return {'type':'MultiPolygon', 'coordinates':polys} if polys else None

def meters(text):
    match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(m|ft|feet|\')?\s*', str(text or ''), re.I)
    if not match: return None
    n = float(match[1]) * (0.3048 if match[2] and match[2].lower() in ('ft', 'feet', "'") else 1)
    return round(n, 3) if 0 < n <= 500 else None

def normalize(raw, manifest, countries):
    if raw.get('remark') or not isinstance(raw.get('elements'), list) or not raw['elements']:
        raise ValueError('Incomplete or empty Overpass response')
    country_polys = []
    for f in countries['features']:
        props = f['properties']; g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            country_polys.append((box(poly[0]), poly, props))
    records = []; seen = set(); skipped = []
    for row in sorted(raw['elements'], key=lambda r:(r['type'], r['id'])):
        typ, ident = row.get('type'), row.get('id')
        if typ not in ('node','way','relation') or type(ident) is not int: raise ValueError('Invalid OSM identity')
        rid = f'osm-{typ}-{ident}'
        if rid in seen: raise ValueError('Duplicate OSM source identity')
        seen.add(rid); tags = row.get('tags', {}); g = geometry(row)
        pts = [p for poly in g['coordinates'] for p in poly[0]] if g else []
        if pts:
            b = box(pts); p = [(b[0]+b[2])/2, (b[1]+b[3])/2]
        elif point([row.get('lon'),row.get('lat')]): p = [row['lon'],row['lat']]
        elif all(finite(row.get('bounds',{}).get(k)) for k in ('minlon','minlat','maxlon','maxlat')):
            b=row['bounds'];p=[(b['minlon']+b['maxlon'])/2,(b['minlat']+b['maxlat'])/2]
        else: skipped.append(rid);continue
        if not point(p): skipped.append(rid);continue
        props = next((q for b,poly,q in country_polys if in_box(p,b) and ring_inside(p,poly[0]) and not any(ring_inside(p,h) for h in poly[1:])), {})
        country = props.get('ADMIN','Unknown'); code = props.get('ISO_A2_EH') or props.get('ISO_A2') or ''
        continent = props.get('CONTINENT','Unknown')
        if continent == 'Seven seas (open ocean)': continent = 'Unknown'
        country = {'United States of America':'United States'}.get(country,country)
        is_building = bool(tags.get('building') and tags['building'] not in ('no','construction'))
        if tags.get('construction') == 'data_center': is_building = True
        kind = 'building' if is_building and g else 'campus' if tags.get('industrial') in ('data_centre','data_center') and g else 'area' if g else 'point'
        lifecycle = next((prefix for prefix in ('abandoned','disused','demolished','proposed','construction') if any(k.startswith(prefix+':') and v in ('data_center','data_centre') or k==prefix and v in ('data_center','data_centre') for k,v in tags.items())), 'unspecified')
        # Preserve useful source tags, not contributors' identities or contact details.
        keep = {k:v for k,v in tags.items() if k in ('name','name:en','ref','operator','owner','brand','website','contact:website','telecom','building','industrial','height','building:levels','start_date','type') or k.startswith('addr:') or k.endswith(':telecom')}
        records.append({'id':rid,'name':tags.get('name:en') or tags.get('name') or tags.get('ref') or tags.get('operator') or f'Unnamed mapped {kind}',
            'operator':tags.get('operator'), 'country':country, 'country_code':code, 'continent':continent,
            'city':tags.get('addr:city'), 'address':' '.join(str(tags[k]) for k in ('addr:housenumber','addr:street','addr:postcode') if k in tags),
            'lat':round(p[1],7),'lon':round(p[0],7),'kind':kind,'lifecycle':lifecycle,
            'height_m':meters(tags.get('height')) if kind=='building' else None,'it_mw':None,
            'geometry':g,'tags':keep,'source_url':f'https://www.openstreetmap.org/{typ}/{ident}',
            'source_version':row.get('version'),'updated_at':row.get('timestamp'),'member_of':[],
            'coordinate_basis':'OSM source point' if typ=='node' else 'Center of OSM geometry bounds; not a surveyed entrance'})
    index = {r['id']:r for r in records}
    for row in raw['elements']:
        if row['type'] == 'relation':
            for m in row.get('members',[]):
                member = index.get(f"osm-{m.get('type')}-{m.get('ref')}")
                if member and f"osm-relation-{row['id']}" in index: member['member_of'].append(f"osm-relation-{row['id']}")
    counts = lambda key: dict(sorted(Counter(r[key] for r in records).items()))
    return {'schema_version':1,'license':LICENSE,'license_url':'https://opendatacommons.org/licenses/odbl/1-0/',
            'attribution':'© OpenStreetMap contributors','attribution_url':'https://www.openstreetmap.org/copyright',
            'policy':POLICY,'captured_at':manifest['retrieved_at'],'osm_timestamp':manifest['osm_timestamp'],
            'source_manifest':manifest,'country_basis':'Point in Natural Earth 10m country polygons; geographic classification, not sovereignty adjudication.',
            'counts':{'features':len(records),'countries':counts('country'),'continents':counts('continent'),'kinds':counts('kind'),'lifecycle':counts('lifecycle'),'skipped':skipped},'records':records}

def main():
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    m=json.loads((a.capture/'manifest.json').read_text());raw=(a.capture/'osm-datacenters.json').read_bytes();c=(a.capture/'countries.geojson').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['sanitized_sha256'] or hashlib.sha256(c).hexdigest()!=m['countries']['sha256']:raise ValueError('Source checksum mismatch')
    result=normalize(json.loads(raw),m,json.loads(c));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(canonical(result)+'\n');print(json.dumps(result['counts'],indent=2))
if __name__=='__main__': main()
