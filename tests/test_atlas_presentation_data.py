"""Geographic presentation must retain licensed data and worldwide scope."""
import base64
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_relief_has_attribution_and_an_exact_offline_copy():
    manifest = json.loads((ROOT / 'data/maps/terrain.json').read_text())
    content = (ROOT / manifest['path']).read_bytes()
    assert hashlib.sha256(content).hexdigest() == manifest['sha256']
    assert manifest['license'] == 'Public domain'
    assert manifest['bounds'] == [-180, -90, 180, 90]
    assert manifest['source_url'].startswith('https://naturalearth.s3.amazonaws.com/')
    assert len(manifest['source_raster_sha256']) == 64
    html = (ROOT / 'compute_atlas.html').read_text()
    embedded = re.search(r'id="atlas-terrain-image"[^>]*src="data:image/webp;base64,([^"]+)"', html)
    assert embedded and base64.b64decode(embedded[1]) == content

def test_reference_roads_and_boundaries_are_worldwide():
    data = json.loads((ROOT / 'data/context.json').read_text())
    assert all(len(data[key]) > 100 for key in ['roads', 'states', 'lakes', 'places'])
    regions = {'South America': (-80,-40,-35,5), 'Africa': (-15,-35,45,30),
               'Oceania': (110,-45,155,-10), 'Asia': (70,5,145,60),
               'Europe': (-10,35,35,65), 'North America': (-130,25,-65,60)}
    for region,(x0,y0,x1,y1) in regions.items():
        assert any(any(x0 < x < x1 and y0 < y < y1 for x,y in line) for line in data['roads']), region
    for source in data['sources']:
        assert source['license'] == 'Public domain'
        assert len(source['sha256']) == 64
        assert source['features'] == len(data[source['layer']])
