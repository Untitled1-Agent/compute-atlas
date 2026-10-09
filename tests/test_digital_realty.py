"""Synthetic parser fixtures and real accepted-publication contracts; no live network."""
import copy,json,hashlib,io,zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.digital_realty import parse,validate,SOURCE_ID,SOURCE_URL
from server.operator_directory import DirectoryStore
from server.store import ROOT,Store
from server.app import create_app
from tools.materialize_digital_realty import materialize

@pytest.fixture
def publication():return json.loads((ROOT/'data/catalog/digital-realty.json').read_text())

def fixture():
    rows=[dict(node_id=str(i),title=f'FRA{i}',region='EMEA',country='Germany',metro='Frankfurt',
        **{'url-alias':f'/data-centers/emea/frankfurt/fra{i}',
           'field_facility_location':[{'field_continent':'Europe'}],
           'field_site_code_location':[{'value':f'FRA{i}'}],
           'field_latitude':[{'value':'50.1'}],'field_longitude':[{'value':'8.6'}]}) for i in range(1,101)]
    return {'props':{'pageProps':{'data':{'facilities':rows,'metros':[{'latitude':0,'longitude':0}]}}}}

def html(x):return ('<script id="__NEXT_DATA__" type="application/json">'+json.dumps(x)+'</script>').encode()

def test_parser_uses_facilities_not_metro_centroids():
    d=parse(html(fixture()),captured_at='2026-10-09T20:00:00Z')
    assert len(d['records'])==100 and d['review'] is None
    assert d['records'][0]['coordinates']==dict(lat=50.1,lon=8.6,basis='publisher_pin')
    assert all(r['it_mw'] is None for r in d['records'])

@pytest.mark.parametrize('mutation',[
 lambda x:x['props']['pageProps']['data'].pop('facilities'),
 lambda x:x['props']['pageProps']['data'].update(facilities=[]),
 lambda x:x['props']['pageProps']['data']['facilities'][0].update(field_latitude=[]),
 lambda x:x['props']['pageProps']['data']['facilities'].append(x['props']['pageProps']['data']['facilities'][0]),
 lambda x:x['props']['pageProps']['data']['facilities'][0].update(field_facility_location=[]),
])
def test_source_drift_fails_closed(mutation):
    x=fixture();mutation(x)
    with pytest.raises(ValueError):parse(html(x),captured_at='2026-10-09T20:00:00Z')

@pytest.mark.parametrize('mutation',[
 lambda d:d.update(schema_version=True),lambda d:d.update(final_url='https://example.com'),
 lambda d:d['records'][0].update(it_mw=0),lambda d:d['records'][0].update(geometry={}),
 lambda d:d['records'][0]['coordinates'].update(lat=True),lambda d:d['records'][0]['coordinates'].update(lon=float('nan')),
 lambda d:d['records'][0]['coordinates'].update(lat=91),lambda d:d['records'][0].update(source_url='javascript:alert(1)'),
 lambda d:d.update(captured_at='2026-02-30T00:00:00Z'),lambda d:d['review'].update(reviewed_at='2026-10-09'),
 lambda d:d['counts'].update(records=999),lambda d:d['records'].append(d['records'][0]),
])
def test_unsafe_publications_rejected(publication,mutation):
    mutation(publication)
    with pytest.raises(ValueError):validate(publication)

def test_real_source_boundaries_and_review_receipt(publication):
    validate(publication)
    assert publication['counts']['regions']==dict(EMEA=128,Americas=111,APAC=22)
    assert len(publication['records'])==261
    assert len([r for r in publication['records'] if r['source_country'] is None])==2
    assert next(r for r in publication['records'] if r['code']=='DUB1')['source_country']=='United Kingdom'
    assert len([r for r in publication['records'] if r['source_title']=='HND10 + HND11'])==1
    receipt=json.loads((ROOT/'data/catalog/digital-realty-review.json').read_text())
    assert hashlib.sha256((ROOT/'data/catalog/digital-realty.json').read_bytes()).hexdigest()==receipt['publication_sha256']
    assert all(r['it_mw'] is None and r['coordinates']['basis']=='publisher_pin' for r in publication['records'])

def test_source_heads_are_isolated_and_reviewed(tmp_path,publication):
    path=tmp_path/'test.sqlite';Store(path).seed(ROOT)
    eq=DirectoryStore(path);eq.seed(ROOT);before=eq.current()
    dl=DirectoryStore(path,'digital-realty');publication['review']=None;key=dl.stage(publication)
    assert dl.current() is None and eq.current()==before
    with pytest.raises(ValueError,match='Cross-publisher'):eq.accept(key,actor='a',note='n',expected_current=before)
    with pytest.raises(ValueError,match='Cross-publisher'):eq.stage(publication)
    dl.accept(key,actor='a',note='review',expected_current=None)
    assert dl.publication()['review']['actor']=='a' and eq.current()==before
    dl.seed(ROOT);assert dl.current()==key
    with pytest.raises(ValueError,match='changed'):dl.accept(key,actor='a',note='n',expected_current=None)
    assert len(dl.status()['decisions'])==3 and all(x['hash']!=before for x in dl.status()['decisions'])
    assert dl.page(country='Germany',limit=2)['total']==27
    assert dl.page(country='Not specified')['total']==2
    assert dl.page(q="' OR 1=1")['total']==0
    with dl.connect() as db:
        assert db.execute('SELECT refresh_hours FROM jobs WHERE source_id=?',(SOURCE_ID,)).fetchone()[0]==168

def test_existing_slot_is_migrated_without_losing_acceptance(tmp_path):
    path=tmp_path/'test.sqlite';Store(path).seed(ROOT);eq=DirectoryStore(path);eq.seed(ROOT);key=eq.current()
    with eq.connect() as db:db.execute('DROP TABLE directory_heads')
    assert DirectoryStore(path).current()==key
    assert DirectoryStore(path,'digital-realty').current() is None

def test_read_only_api_publisher_isolation(tmp_path):
    with TestClient(create_app(tmp_path/'app.sqlite',background=False)) as c:
        d=c.get('/api/operators/publication?publisher=digital-realty');assert d.status_code==200
        assert d.json()['counts']['records']==261
        assert c.get('/api/operators/publication').json()['counts']['records']==253
        assert c.get('/api/operators/publication?publisher=digital-realty',headers={'If-None-Match':d.headers['etag']}).status_code==304
        assert c.get('/api/operators/records?publisher=digital-realty&country=Germany&limit=2').json()['total']==27
        assert c.get('/api/operators/status?publisher=unknown').status_code==422
        assert c.post('/api/operators/publication?publisher=digital-realty',json={}).status_code==405

def test_materialization_requires_exact_source_and_projection():
    raw=html(fixture());date='2026-10-09T20:00:00Z';d=parse(raw,captured_at=date)
    review=dict(actor='fixture',note='synthetic test',reviewed_at=date);d['review']=review
    projected=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:z.writestr('global.html',raw)
    archive=buf.getvalue();r=dict(member='global.html',artifact_sha256=hashlib.sha256(archive).hexdigest(),source_sha256=hashlib.sha256(raw).hexdigest(),captured_at=date,expected_records=100,review=review,publication_sha256=hashlib.sha256(projected).hexdigest())
    assert materialize(r,archive)==projected
    for k in ('source_sha256','publication_sha256','artifact_sha256'):
        changed={**r,k:'0'*64}
        with pytest.raises(ValueError):materialize(changed,archive)
