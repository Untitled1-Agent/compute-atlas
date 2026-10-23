"""Bounded global context must remain native, attributable and reproducible."""
import gzip,hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
INDEX=json.loads((ROOT/'data/layers/global-context-index.json').read_text())
LOCATIONS=json.loads((ROOT/'data/catalog/atlas-locations.json').read_text())

def test_every_published_center_has_an_explicit_location_outcome():
    centers=json.loads((ROOT/'data/catalog/epoch-data-centers.json').read_text())['tables']['centers']['records']
    assert {r['id'] for r in LOCATIONS['records']}=={r['id'] for r in centers}
    by_id={r['id']:r for r in centers}
    for row in LOCATIONS['records']:
        assert row['source_address']==by_id[row['id']]['fields']['Address'].strip()
        assert row['source_country']==by_id[row['id']]['fields']['Country'].strip()
        assert row['status'] in {'resolved','no_match','no_address','unavailable'}
        if row['status']=='resolved':
            assert row['response'] and row['response_sha256']
            hit=row['response'][0]
            assert -90<=float(hit['lat'])<=90 and -180<=float(hit['lon'])<=180
            country_codes={'Australia':'au','China':'cn','Finland':'fi','Iceland':'is','Indonesia':'id','Malaysia':'my','Norway':'no','Portugal':'pt','Sweden':'se','United Arab Emirates':'ae','United Kingdom':'gb','United States':'us'}
            assert hit['address']['country_code']==country_codes[row['source_country']]
            assert hit['osm_type'] in {'way','node','relation'}
        elif row['status']=='no_address':
            assert not row['source_address'] and not row['response']

def test_context_is_worldwide_but_does_not_claim_campus_identity():
    assert INDEX['anchor_count']>=70 and len(INDEX['countries'])>=20
    assert all(country in INDEX['countries'] for country in ['United States','Japan','Germany','Australia','Brazil'])
    assert 'does not establish' in INDEX['policy']
    assert INDEX['license']=='ODbL-1.0'
    assert INDEX['attribution']=='© OpenStreetMap contributors'

@pytest.mark.parametrize('capture',INDEX['captures'],ids=lambda c:c['id'][:12])
def test_context_chunk_retains_exact_captured_source(capture):
    raw=(ROOT/capture['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==capture['sha256']
    assert len(raw)==capture['bytes']
    source=gzip.decompress(raw)
    assert hashlib.sha256(source).hexdigest()==capture['response_sha256']
    data=json.loads(source)
    assert 'remark' not in data
    assert len(data['elements'])==capture['feature_count']
    assert data['osm3s']['timestamp_osm_base']==capture['osm_base']
    assert hashlib.sha256(capture['query'].encode()).hexdigest()==capture['id']
    assert capture['radius_m']==750 and 'around:750' in capture['query']
    for row in data['elements']:
        assert row['type'] in {'node','way'} and row['id']>0 and row['version']>0
        assert row.get('timestamp') and row.get('tags')
        assert 'geometry' in row or 'lat' in row
        assert not any(k in row for k in ['project_id','it_power_mw','campus_owner'])

def test_context_manifest_counts_unique_native_identities():
    identities=set();anchors=[]
    for capture in INDEX['captures']:
        data=json.loads(gzip.decompress((ROOT/capture['path']).read_bytes()))
        identities.update((r['type'],r['id']) for r in data['elements'])
        anchors.extend((p['lat'],p['lon']) for p in capture['anchors'])
    assert len(identities)==INDEX['feature_count']
    assert len(anchors)==len(set(anchors))==INDEX['anchor_count']
    assert {p.name for p in (ROOT/'data/layers/global-context').glob('*.json.gz')}=={Path(c['path']).name for c in INDEX['captures']}


def test_service_delivers_the_exact_compressed_context(tmp_path):
    from fastapi.testclient import TestClient
    from server.app import create_app
    capture=INDEX['captures'][0]
    with TestClient(create_app(tmp_path/'atlas.sqlite3',background=False)) as client:
        response=client.get('/'+capture['path'])
        assert response.status_code==200
        assert not response.headers.get('content-encoding')
        assert hashlib.sha256(response.content).hexdigest()==capture['sha256']
        assert client.get('/work/global-context.json').status_code==404
        assert client.get('/data/layers/global-context/unknown.json.gz').status_code==404


def test_every_eligible_published_anchor_is_captured():
    gpu=json.loads((ROOT/'data/catalog/gpu-clusters.json').read_text())['records']
    expected={r['id'] for r in gpu if not r['anonymous'] and r['lat'] is not None}
    expected.update(r['id'] for r in LOCATIONS['records'] if r['response'] and int(r['response'][0].get('place_rank',0))>=26)
    captured={id for c in INDEX['captures'] for p in c['anchors'] for id in p['ids']}
    assert expected==captured
    assert not INDEX['failures']
