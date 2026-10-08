"""Publication, provenance, no-geocoding and immutable directory contracts."""
import copy
import json
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.operator_directory import DirectoryStore, validate_directory, proposed_matches, SOURCE_ID
from server.app import create_app
from server.store import ROOT, Store

@pytest.fixture
def publication():
    return json.loads((ROOT/'data/catalog/operator-directory.json').read_text())

@pytest.fixture
def ledger(tmp_path):
    path=tmp_path/'atlas.sqlite3';Store(path).seed(ROOT)
    return DirectoryStore(path)

def test_reviewed_directory_counts_and_separate_domains(publication):
    d=validate_directory(publication)
    assert len(d['records'])==253 and len(d['counts']['countries'])==33
    assert d['counts']['regions']=={'EMEA':93,'APAC':53,'Americas':107}
    assert len([r for r in d['records'] if r['source_country']=='Germany'])==13
    assert all(r['coordinates'] is None and r['it_mw'] is None for r in d['records'])
    assert next(r for r in d['records'] if r['code']=='DU1')['service_coverage'] is None
    assert next(r for r in d['records'] if r['code']=='PA9X')['service_coverage']=='Smart Hands not available'

@pytest.mark.parametrize('mutation',[
    lambda d:d.update(schema_version=True), lambda d:d.update(source_sha256='a'),
    lambda d:d.update(final_url='https://example.org/'), lambda d:d.update(published_at='2026-10-09'),
    lambda d:d.update(records=[]), lambda d:d['records'].append(d['records'][0]),
    lambda d:d['records'][0].update(coordinates=[1,2]),lambda d:d['records'][0].update(it_mw=0),
    lambda d:d['records'][0].update(code='FR2/FR4'),lambda d:d['records'][0].update(status='operating'),
    lambda d:d['records'][0].update(source_url='javascript:alert(1)'),lambda d:d['counts'].update(records=0),
    lambda d:d.update(captured_at='2026-02-30T00:00:00Z'),lambda d:d.update(captured_at='2026-10-09'),
    lambda d:d['review'].update(reviewed_at='2026-10-09'),lambda d:d['review'].update(actor=''),
])
def test_malformed_directory_rejected(publication,mutation):
    mutation(publication)
    with pytest.raises(ValueError):validate_directory(publication)

def test_staging_is_not_publication_and_acceptance_is_leased(ledger,publication):
    publication['review']=None
    key=ledger.stage(publication)
    assert ledger.publication() is None and ledger.page()['items']==[]
    assert ledger.stage(publication)==key and len(ledger.status()['decisions'])==1
    ledger.accept(key,actor='Reviewer',note='Verified directory rows only',expected_current=None)
    result=ledger.publication()
    assert result['review']['actor']=='Reviewer' and result['review']['reviewed_at']
    assert result['records']==publication['records']
    with pytest.raises(ValueError,match='changed'):ledger.accept(key,actor='Other',note='stale',expected_current=None)
    with ledger.connect() as db:
        assert json.loads(db.execute('SELECT payload FROM directory_snapshots').fetchone()[0])['review'] is None

def test_accept_requires_existing_snapshot_and_reviewer(ledger,publication):
    with pytest.raises(ValueError):ledger.accept('missing',actor='a',note='n',expected_current=None)
    key=ledger.stage(publication)
    with pytest.raises(ValueError):ledger.accept(key,actor='',note='n',expected_current=None)
    assert ledger.current() is None

@pytest.mark.parametrize('table',['directory_snapshots','directory_records','directory_decisions'])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_history_cannot_be_overwritten(ledger,publication,table,operation):
    key=ledger.stage(publication)
    column='payload' if table!='directory_decisions' else 'note'
    with ledger.connect() as db, pytest.raises(sqlite3.IntegrityError,match='immutable'):
        db.execute(f'DELETE FROM {table}' if operation=='DELETE' else f'UPDATE {table} SET {column}={column}')
    assert ledger.stage(publication)==key

def test_country_filter_and_search_apply_before_pagination(ledger,publication):
    ledger.seed(ROOT)
    first=ledger.page(country='Germany',limit=2)
    assert first['total']==13 and len(first['items'])==2
    nextpage=ledger.page(country='Germany',limit=2,offset=2)
    assert {r['id'] for r in first['items']}.isdisjoint(r['id'] for r in nextpage['items'])
    assert ledger.page(q='FR',country='Germany')['total']==8
    assert ledger.page(q='%')['total']==0 and ledger.page(q="' OR 1=1")["total"]==0
    with pytest.raises(ValueError):ledger.page(limit=101)

def test_match_proposals_require_exact_code_operator_country(publication):
    row=next(r for r in publication['records'] if r['code']=='FR2')
    f=lambda id,name,operator='Equinix',country='Germany':dict(id=id,name=name,operator=operator,country=country)
    features=[f('a','Equinix FR2'),f('b','Equinix FR2.6'),f('c','Equinix FR20'),f('d','FR2',operator='Another'),f('e','Equinix FR2',country='France'),f('f','Equinix FR2 campus')]
    assert proposed_matches(row,features)==['a','f']
    row=next(r for r in publication['records'] if r['code']=='LD4')
    assert proposed_matches(row,[f('uk','Equinix LD4',country='United Kingdom')])==['uk']

def test_seed_registers_recapture_without_replacing_manual_acceptance(ledger,publication):
    ledger.seed(ROOT);current=ledger.current()
    with ledger.connect() as db:
        source=db.execute('SELECT * FROM sources WHERE id=?',(SOURCE_ID,)).fetchone()
        assert source['kind']=='page'
        assert db.execute('SELECT refresh_hours FROM jobs WHERE source_id=?',(SOURCE_ID,)).fetchone()[0]==168
    publication['review']=None;publication['captured_at']='2026-10-09T02:00:00Z'
    key=ledger.stage(publication);ledger.accept(key,actor='a',note='new capture',expected_current=current)
    ledger.seed(ROOT)
    assert ledger.current()==key

def test_directory_api_is_read_only_and_etag_matches_acceptance(tmp_path):
    app=create_app(tmp_path/'atlas.sqlite3',background=False)
    with TestClient(app) as client:
        reply=client.get('/api/operators/publication');assert reply.status_code==200
        assert reply.json()['review'] and reply.json()['counts']['records']==253
        assert client.get('/api/operators/publication',headers={'If-None-Match':reply.headers['etag']}).status_code==304
        assert client.get('/api/operators/records',params={'country':'Germany','limit':2,'offset':2}).json()['total']==13
        assert client.get('/api/operators/records',params={'limit':500}).status_code==422
        assert client.get('/api/operators/status').json()['current']
        assert client.post('/api/operators/publication',json={}).status_code==405
        html=client.get('/').text
        assert '/api/operators/publication' in html and 'ATLAS_DIRECTORY_WARNING' in html
