"""Native source reconstruction and non-default component coverage contracts."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from tools.normalize_power_context import BBOX,normalize
ROOT=Path(__file__).resolve().parents[1]
RAW=b'<osm><node id="1" version="7" timestamp="2026-01-01T00:00:00Z" lon="-88" lat="41.5"/><node id="2" version="2" timestamp="2026-01-02T00:00:00Z" lon="-86.5" lat="41.5"/><way id="20" version="3" timestamp="2026-01-03T00:00:00Z"><nd ref="1"/><nd ref="2"/><tag k="power" v="line"/><tag k="voltage" v="345000;345000"/></way></osm>'

def test_non_default_bounds_clip_display_without_replacing_native_geometry():
    bounds=(-87,41,-86,42);data=normalize(RAW,'2026-10-11T00:00:00Z',bounds=bounds,retain_node_versions=True);f=data['features'][0]
    assert data['coverage_bbox']==list(bounds)
    assert f['geometry']['coordinates']==[[-88,41.5],[-86.5,41.5]]
    assert f['display_paths']==[[[-87,41.5],[-86.5,41.5]]]
    assert BBOX==(-100.90,33.75,-100.83,33.80)
    assert f['tags']['voltage']=='345000;345000'

def test_node_versions_preserve_captured_reference_order_and_coordinates():
    f=normalize(RAW,'2026-10-11T00:00:00Z',bounds=(-87,41,-86,42),retain_node_versions=True)['features'][0]
    assert f['referenced_node_versions']==[{'osm_id':1,'version':7,'edited_at':'2026-01-01T00:00:00Z','coordinates':[-88.0,41.5]},{'osm_id':2,'version':2,'edited_at':'2026-01-02T00:00:00Z','coordinates':[-86.5,41.5]}]

def test_missing_node_version_cannot_publish_a_component_snapshot():
    with pytest.raises(ValueError,match='Missing referenced node version'):
        normalize(RAW.replace(b' version="7"',b''),'2026-10-11T00:00:00Z',bounds=(-87,41,-86,42),retain_node_versions=True)

def test_pinned_core_inventory_matches_each_complete_native_capture():
    data=json.loads((ROOT/'data/layers/campus-power.json').read_text());collections=data['collections']
    assert [len(c['features']) for c in collections]==[13,12]
    assert sum(f['tags']['power']=='line' for c in collections for f in c['features'])==22
    assert sum(f['tags']['power']=='substation' for c in collections for f in c['features'])==3
    for c in collections:
        raw=(ROOT/c['source_snapshot_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==c['response_sha256']
        source=ET.fromstring(raw);nodes={int(n.attrib['id']):n for n in source.findall('node')};ways={int(w.attrib['id']):w for w in source.findall('way')}
        assert c['captured_at'].startswith('2026-10-11T21:07:31.') and c['infrastructure_observed_at'] is None
        assert c['license']=='ODbL-1.0' and c['scene_id'] in {'new-carlisle-edison-2025','new-carlisle-sr2-2025'}
        for f in c['features']:
            way=ways[f['osm_id']];refs=[int(n.attrib['ref']) for n in way.findall('nd')]
            assert f['version']==int(way.attrib['version']) and f['edited_at']==way.attrib['timestamp']
            assert f['tags']=={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
            assert refs==list(map(int,f['node_refs']))==[n['osm_id'] for n in f['referenced_node_versions']]
            coords=[]
            for n in f['referenced_node_versions']:
                rawnode=nodes[n['osm_id']];point=[float(rawnode.attrib['lon']),float(rawnode.attrib['lat'])];coords.append(point)
                assert n['version']==int(rawnode.attrib['version']) and n['edited_at']==rawnode.attrib['timestamp'] and n['coordinates']==point
            assert f['geometry']['coordinates']==([coords] if f['tags']['power']=='substation' else coords)
            assert not {'it_power_mw','project_id','service','owner','operating_status','user','uid'}&set(f)
            west,south,east,north=c['coverage_bbox'];assert all(west<=x<=east and south<=y<=north for p in f['display_paths'] for x,y in p)

def test_existing_helios_context_publication_is_unchanged():
    source=ROOT/'data/layers/helios-power.json'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='c1ae86c535014cf0ce59ed7f9ff50719a8f9735b9a0b4c2e98ae996dac9a8f5a'
