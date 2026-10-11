import json
from pathlib import Path
import pytest
from tools.normalize_power_context import BBOX,clip_segment,normalize

ROOT=Path(__file__).resolve().parents[1]

def test_clipping_retains_crossing_segments_without_extending_coverage():
    assert clip_segment([-101,33.77],[-100,33.77])==[[-100.9,33.77],[-100.83,33.77]]
    assert clip_segment([-101,34],[-100,34]) is None
    assert clip_segment([-100.87,33.74],[-100.87,33.81])==[[-100.87,33.75],[-100.87,33.8]]

def test_full_source_geometry_and_native_voltage_are_independent_of_display():
    raw=b'<osm><node id="1" lon="-101" lat="33.77"/><node id="2" lon="-100.86" lat="33.77"/><way id="20" version="3" timestamp="2017-01-01T00:00:00Z"><nd ref="1"/><nd ref="2"/><tag k="power" v="line"/><tag k="voltage" v="345000"/></way></osm>'
    data=normalize(raw,'2026-10-11T00:00:00Z');f=data['features'][0]
    assert f['geometry']['coordinates'][0]==[-101,33.77]
    assert f['display_paths'][0][0]==[-100.9,33.77]
    assert f['tags']['voltage']=='345000' and f['edited_at'].startswith('2017')
    assert data['captured_at'].startswith('2026') and data['license']=='ODbL-1.0'
    assert not {'project_id','it_mw','connection','height','operating_status'}&set(f)

def test_incomplete_or_empty_capture_cannot_replace_source_context():
    with pytest.raises(ValueError,match='Incomplete'):
        normalize(b'<osm><way id="20"><nd ref="1"/><tag k="power" v="line"/></way></osm>','2026-10-11')
    with pytest.raises(ValueError,match='Empty'):
        normalize(b'<osm/>','2026-10-11')

def test_pinned_snapshot_retains_licensed_native_objects_and_bounded_paths():
    data=json.loads((ROOT/'data/layers/helios-power.json').read_text());features=data['features']
    assert len(features)==38 and len({f['id'] for f in features})==38
    assert sum(f['tags']['power']=='substation' for f in features)==5
    assert data['coverage_bbox']==list(BBOX) and len(data['response_sha256'])==64
    for f in features:
        assert f['url']==f"https://www.openstreetmap.org/way/{f['osm_id']}"
        assert f['version']>0 and f['edited_at']<=data['captured_at']
        assert not {'user','uid','it_mw','project_id','height'}&set(f)
        assert all(BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3] for path in f['display_paths'] for x,y in path)
