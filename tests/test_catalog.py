import copy, json, sqlite3
from collections import Counter
from pathlib import Path
import pytest
from server.catalog import CatalogStore, validate
from tools.normalize_catalog import meters, stitch, geometry, normalize
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def data():return json.loads((ROOT/'data/catalog/osm.json').read_text())
@pytest.fixture
def small(data):
    data['records']=data['records'][:5];data['counts']['features']=5
    for field,label in [('country','countries'),('continent','continents'),('kind','kinds'),('lifecycle','lifecycle')]:data['counts'][label]=dict(Counter(r[field] for r in data['records']))
    return data

def test_global_geographic_denominators(data):
    validate(data)
    assert len(data['records'])==5265
    assert data['counts']['continents']['Europe']==1908
    assert data['counts']['countries']['Germany']==320
    assert data['counts']['countries']['France']==382
    assert all(r['it_mw'] is None for r in data['records'])
    assert all(r['lifecycle']!='operating' for r in data['records'])
    assert len({r['country'] for r in data['records'] if r['country']!='Unknown'})==115

@pytest.mark.parametrize('value,expected', [('15',15),('12 m',12),('100 ft',30.48),('10-15',None),('5001',None),('NaN',None),('-2',None)])
def test_only_explicit_height_units(value,expected):assert meters(value)==expected

def test_incomplete_relations_never_closed():
    assert stitch([[[0,0],[1,0]],[[1,0],[1,1]]])==[]
    assert len(stitch([[[0,0],[1,0]],[[1,1],[1,0]],[[1,1],[0,0]]]))==1

def test_catalog_stage_is_not_acceptance(tmp_path,small):
    c=CatalogStore(tmp_path/'a.db');key=c.stage(small)
    assert c.current() is None and c.page()['total']==0
    c.accept(key,actor='Reviewer',note='Verified source boundary',expected_current=None)
    assert c.page(limit=2)['total']==5 and len(c.page(offset=4)['items'])==1
    newer=copy.deepcopy(small);newer['records'][0]['name']='Changed name'
    second=c.stage(newer);assert c.feature(newer['records'][0]['id'])['name']!='Changed name'
    with pytest.raises(ValueError):c.accept(second,actor='Reviewer',note='review',expected_current='stale')
    c.accept(second,actor='Reviewer',note='review',expected_current=key)
    assert c.feature(newer['records'][0]['id'])['name']=='Changed name'
    assert len(c.status()['snapshots'])==2
    with c.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):db.execute('UPDATE catalog_snapshots SET captured_at=\'fake\'')

def test_invalid_snapshot_leaves_publication(tmp_path,small):
    c=CatalogStore(tmp_path/'a.db');key=c.stage(small);c.accept(key,actor='r',note='review',expected_current=None)
    broken=copy.deepcopy(small);broken['records'][0]['it_mw']=100
    with pytest.raises(ValueError):c.stage(broken)
    assert c.current()==key

@pytest.mark.parametrize('mutation', [lambda r:r.update(lat=float('nan')),lambda r:r.update(lon=181),lambda r:r.update(it_mw=0),lambda r:r.update(source_url='javascript:alert(1)'),lambda r:r.update(height_m='10'),lambda r:r.update(geometry={'type':'Point','coordinates':[1,2]})])
def test_validation_rejects_invented_or_type_confused_fields(small,mutation):
    mutation(small['records'][0])
    with pytest.raises(ValueError):validate(small)

def test_catalog_search_filters_before_pagination(tmp_path,data):
    c=CatalogStore(tmp_path/'a.db');key=c.stage(data);c.accept(key,actor='r',note='review',expected_current=None)
    assert c.page(country='France',limit=1)['total']==382
    assert c.page(q='Equinix',country='France')['total']>3
    assert c.page(q="%' OR 1=1 --")['total']==0
    assert c.page(continent='Europe',kind='building')['total']>500
    assert c.page(bbox=[2,48,3,49])['total']>20
    assert c.page(bbox=[170,-90,-170,90])['total']>=0
    with pytest.raises(ValueError):c.page(bbox=[0,90,180,-90])

def test_four_operator_reviews_keep_units_and_no_geometry_claim(data):
    reviews=json.loads((ROOT/'data/catalog/reviews.json').read_text())['reviews'];ids={r['id'] for r in data['records']}
    assert len(reviews)==4
    assert all(r['feature_id'] in ids and r['it_mw'] is None and not r['geometry_verified'] for r in reviews)
    pa=next(r for r in reviews if r['id']=='CAT-PA9X')
    assert pa['measurements'][0]['value']==9600 and pa['measurements'][0]['unit']=='kVA'

def test_catalog_api_accepted_only_and_source_monitor(tmp_path):
    from fastapi.testclient import TestClient
    from server.app import create_app
    app=create_app(tmp_path/'a.db',background=False)
    with TestClient(app) as client:
        response=client.get('/api/catalog/features?country=Germany&limit=3')
        assert response.status_code==200 and response.json()['total']==320 and len(response.json()['items'])==3
        response=client.get('/api/catalog/publication');assert response.status_code==200
        assert client.get('/api/catalog/publication',headers={'If-None-Match':response.headers['ETag']}).status_code==304
        assert client.get('/api/catalog/features/osm-way-1121454055').json()['name']=='Equinix PA9X'
        assert client.get('/api/catalog/features/no-such-record').status_code==404
        assert client.get('/api/catalog/features?bbox=NaN,0,20,30').status_code==422
        assert client.get('/api/catalog/features?limit=0').status_code==422
        assert client.post('/api/catalog/features').status_code in (404,405)
        assert all(s['id']!='CAT-PA9X' for s in client.get('/api/publication').json()['sources'])
        jobs=client.get('/api/status').json()['jobs'];assert any(j['source_id']=='CAT-PA9X' for j in jobs)


def test_classification_denominators_cannot_be_fabricated(small):
    small['counts']['continents']['Europe']=999999
    with pytest.raises(ValueError):validate(small)

def test_catalog_decisions_and_records_immutable(tmp_path,small):
    c=CatalogStore(tmp_path/'a.db');key=c.stage(small)
    with c.connect() as db:
        for table in ('catalog_records','catalog_decisions'):
            with pytest.raises(sqlite3.IntegrityError):db.execute('DELETE FROM '+table)
