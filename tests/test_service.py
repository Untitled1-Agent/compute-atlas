from __future__ import annotations
import copy
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from server.store import Store, ROOT, canonical, now, digest
from server.acquire import Monitor, safe_url, AcquisitionError, feed_items, semantic_text, delay_seconds
from server.app import create_app

@pytest.fixture
def store(tmp_path):
    s=Store(tmp_path/'atlas.sqlite3'); s.seed()
    return s

@pytest.fixture
def observation():
    return copy.deepcopy(json.loads((ROOT/'data/evidence.json').read_text())['observations'][0])

def only_job(store,sid='P01'):
    with store.connect() as db:
        db.execute("UPDATE jobs SET next_fetch_at='2099-01-01T00:00:00+00:00'")
        db.execute("UPDATE jobs SET next_fetch_at='2000-01-01T00:00:00+00:00' WHERE source_id=?",(sid,))

def monitor(store,tmp_path,responses,source='P01'):
    only_job(store,source); requests=[]
    def handler(req):
        requests.append(req)
        if req.url.path=='/robots.txt': return httpx.Response(200,text='User-agent: *\nAllow: /')
        answer=responses.pop(0)
        return answer(req) if callable(answer) else answer
    m=Monitor(store,tmp_path/'blobs',httpx.Client(transport=httpx.MockTransport(handler)),resolve_dns=False,min_host_interval=0)
    return m,requests

def test_seed_is_idempotent_and_archive_is_separate(store):
    before=store.publication(); store.seed(); after=store.publication()
    assert before==after
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM sites').fetchone()[0]==79
        assert db.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM current_decisions').fetchone()[0]==sum(len(before[k])+len(before.get('revision_history',{}).get(k,[])) for k in ('observations','facts','relationships'))

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1,True,'133'])
def test_reject_invalid_numeric_claim(store,observation,value):
    observation.update(id='invalid',value=value)
    with pytest.raises(ValueError): store.submit_claim('observation',observation,'test')

@pytest.mark.parametrize('boundary',['gross_it','guess','',None])
def test_explicit_measurement_boundary(store,observation,boundary):
    observation.update(id='bad-boundary',boundary=boundary)
    with pytest.raises(ValueError): store.submit_claim('observation',observation,'test')

def test_unknown_is_null_not_zero(store,observation):
    observation.update(id='unknown',value=None)
    store.submit_claim('observation',observation,'test'); store.decide('unknown','accepted','editor','No comparable disclosed value')
    assert next(x for x in store.publication()['observations'] if x['id']=='unknown')['value'] is None

def test_claims_are_immutable_and_need_review(store,observation):
    old=observation['id']; baseline=store.publication()
    observation['value']=999
    with pytest.raises(ValueError,match='changed'): store.submit_claim('observation',observation,'editor')
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError): db.execute('DELETE FROM claims WHERE id=?',(old,))
    observation.update(id='revision',supersedes=old)
    store.submit_claim('observation',observation,'editor')
    assert store.publication()==baseline
    store.decide('revision','accepted','editor','Explicitly reviewed revision, source interpretation recorded')
    pub=store.publication(); assert any(x['id']=='revision' for x in pub['observations'])
    assert not any(x['id']==old for x in pub['observations'])
    store.decide('revision','rejected','editor','Correction reversed')
    assert any(x['id']==old for x in store.publication()['observations'])
    # Reseeding must not silently reaccept an editor-rejected claim.
    store.decide(old,'rejected','editor','Withdrawn pending re-verification'); store.seed()
    assert not any(x['id']==old for x in store.publication()['observations'])

def test_competing_accepted_revisions_are_rejected(store,observation):
    old=observation['id']
    for cid in ('r1','r2'):
        observation.update(id=cid,supersedes=old); store.submit_claim('observation',observation,'editor')
    store.decide('r1','accepted','editor','First reviewed revision')
    with pytest.raises(ValueError,match='Conflicting'): store.decide('r2','accepted','editor','Cannot silently overwrite')

def test_relationship_requires_known_company(store):
    data={'id':'rel','site_id':'coreweave-helios','company_id':'imaginary','source_id':'P01','role':'tenant'}
    with pytest.raises(ValueError,match='counterparty'): store.submit_claim('relationship',data,'editor')

def test_fts_queries_are_literal_and_parameterized(store):
    assert store.search('Helios')[0]['id']=='coreweave-helios'
    assert store.search('New Carlisle')
    assert store.search('" OR 1=1 --')==[]

def test_lease_is_exclusive_and_recoverable(store,tmp_path):
    only_job(store)
    m=Monitor(store,tmp_path/'blobs',resolve_dns=False,min_host_interval=0)
    job=m.lease(); assert job; assert m.lease() is None
    with store.connect() as db: db.execute("UPDATE jobs SET lease_until='2000-01-01' WHERE source_id='P01'")
    recovered=m.lease(); assert recovered['lease_token'] != job['lease_token']
    m.close()

def test_capture_304_semantic_change_and_immutable_publication(store,tmp_path):
    baseline=store.publication()
    responses=[httpx.Response(200,headers={'content-type':'text/html','etag':'"one"'},text='<main><article>133 MW critical IT delivered.</article></main>'),httpx.Response(304),httpx.Response(200,headers={'content-type':'text/html','etag':'"two"'},text='<nav>changed nav</nav><article>133 MW critical IT delivered.</article>'),httpx.Response(200,headers={'content-type':'text/html'},text='<article>Phase II remains under construction.</article>')]
    m,requests=monitor(store,tmp_path,responses)
    assert m.run_once(); assert store.queue()['total']==1
    only_job(store); assert m.run_once()
    assert requests[-1].headers['If-None-Match']=='"one"'
    only_job(store); assert m.run_once(); assert store.queue()['total']==1
    only_job(store); assert m.run_once(); assert store.queue()['total']==2
    assert store.publication()==baseline
    status=store.status(); assert status['counts']['source_versions']==3
    assert status['counts']['fetch_attempts']==4
    assert len(list((tmp_path/'blobs').iterdir()))==3
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError): db.execute("UPDATE source_versions SET byte_length=0")

def test_feed_discovery_dedup_does_not_publish(store,tmp_path):
    feed='<rss><channel><item><title>New facility</title><link>https://blogs.microsoft.com/new-site/</link></item></channel></rss>'
    responses=[httpx.Response(200,headers={'content-type':'application/rss+xml'},text=feed)]*2
    m,_=monitor(store,tmp_path,responses,'microsoft-news'); before=store.publication()
    assert m.run_once(); only_job(store,'microsoft-news'); assert m.run_once()
    assert store.queue()['total']==1
    assert store.publication()==before
    item=store.queue()['items'][0]
    store.resolve_queue(item['id'],'acknowledged','editor','Reviewed item; no new supported claim')
    assert store.queue()['total']==0
    assert store.publication()==before

@pytest.mark.parametrize('url',['http://example.com','https://u:p@example.com','https://localhost/x','https://127.0.0.1','https://169.254.169.254','https://example.com:444/x','https://evil.test'])
def test_private_and_unregistered_urls_rejected(url):
    with pytest.raises(AcquisitionError): safe_url(url,{'example.com','127.0.0.1','169.254.169.254','localhost'},False)

def test_redirect_cannot_escape_registered_host(store,tmp_path):
    m,requests=monitor(store,tmp_path,[httpx.Response(302,headers={'location':'https://evil.test/steal'})])
    m.run_once(); assert len(requests)==2
    assert store.status()['counts']['source_versions']==0
    assert 'registered' in next(x for x in store.status()['jobs'] if x['source_id']=='P01')['last_error']

def test_dns_private_answer_rejected(monkeypatch):
    monkeypatch.setattr('socket.getaddrinfo',lambda *a,**k:[(2,1,6,'',('10.0.0.1',443))])
    with pytest.raises(AcquisitionError,match='non-public'): safe_url('https://example.com',{'example.com'})

@pytest.mark.parametrize('code',[403,429,503])
def test_failure_and_retry_after_are_persisted(store,tmp_path,code):
    m,_=monitor(store,tmp_path,[httpx.Response(code,headers={'retry-after':'3600'})]); before=now()
    m.run_once(); job=next(x for x in store.status()['jobs'] if x['source_id']=='P01')
    assert job['last_status']==code and job['failures']==1 and job['last_success'] is None
    assert (datetime.fromisoformat(job['next_fetch_at'])-datetime.fromisoformat(before)).total_seconds()>=3600
    assert store.queue()['total']==0

def test_robots_denial_never_fetches_source(store,tmp_path):
    only_job(store); requests=[]
    def handler(req):
        requests.append(req); return httpx.Response(200,text='User-agent: *\nDisallow: /')
    m=Monitor(store,tmp_path/'blobs',httpx.Client(transport=httpx.MockTransport(handler)),resolve_dns=False,min_host_interval=0)
    m.run_once(); assert len(requests)==1
    assert 'robots' in next(x for x in store.status()['jobs'] if x['source_id']=='P01')['last_error']

def test_byte_cap_is_enforced(store,tmp_path):
    m,_=monitor(store,tmp_path,[httpx.Response(200,headers={'content-length':'99999999'})]); m.run_once()
    assert store.status()['counts']['source_versions']==0
    assert 'byte limit' in next(x for x in store.status()['jobs'] if x['source_id']=='P01')['last_error']

def test_304_without_baseline_is_not_success(store,tmp_path):
    m,_=monitor(store,tmp_path,[httpx.Response(304)]); m.run_once()
    assert next(x for x in store.status()['jobs'] if x['source_id']=='P01')['last_success'] is None

def test_xml_external_entities_are_rejected():
    with pytest.raises(Exception): feed_items(b'<!DOCTYPE doc [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss><item>&xxe;</item></rss>','https://example.com')

def test_queue_pagination_and_audit(store):
    with store.connect() as db:
        for i in range(5): store.enqueue(db,'P01',None,'test',{'i':i},digest(['test',i]))
    page=store.queue(2); assert len(page['items'])==2 and page['total']==5 and page['next_offset']==2
    assert store.queue(2,4)['next_offset'] is None
    store.resolve_queue(page['items'][0]['id'],'rejected','reviewer','Not pertinent')
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM audit_log WHERE action='queue-rejected'").fetchone()[0]==1
        with pytest.raises(sqlite3.IntegrityError): db.execute('DELETE FROM audit_log')

def test_backup_includes_wal_changes(store,tmp_path):
    store.backup(tmp_path/'backup.sqlite3'); backup=Store(tmp_path/'backup.sqlite3')
    assert backup.publication()==store.publication()

def test_same_origin_api_publication_and_static_allowlist(tmp_path):
    app=create_app(tmp_path/'db.sqlite3',background=False)
    with TestClient(app) as client:
        assert client.get('/api/health').json()['status']=='ok'
        status=client.get('/api/status').json(); assert status['background_refresh'] is False
        pub=client.get('/api/publication'); assert pub.status_code==200
        assert client.get('/api/publication',headers={'If-None-Match':pub.headers['etag']}).status_code==304
        assert 'ATLAS_SERVICE' in client.get('/').text
        assert "load('evidence-data','/api/publication')" in client.get('/').text
        assert client.get('/api/sites?q=Helios').json()['total']==1
        assert client.get('/api/sites/coreweave-helios').json()['accepted_claims']
        assert client.get('/api/sources/P01/versions').json()['total']==0
        assert client.get('/api/audit').json()['total']>0
        assert client.get('/src/zoom-explorer.js').status_code==200
        for path in ('/var/atlas.sqlite3','/server/store.py','/.env','/src/build.py','/api/sites/not-real','/api/sources/not-real/versions'):
            assert client.get(path).status_code==404,path
        assert client.get('/api/review-queue?limit=101').status_code==422
        assert client.post('/api/publication',json={}).status_code==405
        assert 'access-control-allow-origin' not in client.get('/api/status',headers={'origin':'https://untrusted.test'}).headers


def test_background_lifespan_starts_and_stops(tmp_path):
    class FakeMonitor:
        called=False; closed=False
        def __init__(self,*a): pass
        def run_once(self): FakeMonitor.called=True; return False
        def close(self): FakeMonitor.closed=True
    app=create_app(tmp_path/'db.sqlite3',background=True,monitor_factory=FakeMonitor)
    with TestClient(app) as client:
        assert client.get('/api/status').json()['background_refresh'] is True
        for _ in range(20):
            if FakeMonitor.called: break
            time.sleep(.01)
        assert FakeMonitor.called
    assert FakeMonitor.closed and app.state.background_refresh is False

def test_invalid_feed_releases_lease_with_visible_failure(store,tmp_path):
    m,_=monitor(store,tmp_path,[httpx.Response(200,headers={'content-type':'text/xml'},text='<broken>')],'microsoft-news')
    m.run_once()
    job=next(x for x in store.status()['jobs'] if x['source_id']=='microsoft-news')
    assert job['failures']==1 and job['last_error'] and job['last_success'] is None
    with store.connect() as db:
        assert db.execute("SELECT lease_until FROM jobs WHERE source_id='microsoft-news'").fetchone()[0] is None
