"""Acquisition history is an event stream, not a sort of deduplicated bodies."""
from __future__ import annotations

import hashlib
import json
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.store import Store, canonical
from test_service import store, monitor, only_job  # Reuse the bounded mock transport.


def page(text: str, **headers) -> httpx.Response:
    return httpx.Response(200, text='<article>'+text+'</article>',
                          headers={'content-type':'text/html', **headers})


def test_recurrent_representations_follow_last_event_not_first_capture(store, tmp_path):
    before=store.publication()
    a=page('Original disclosure', etag='"a"')
    b=page('Revised disclosure', etag='"b"')
    monitor_, requests=monitor(store,tmp_path,[a,b,a,httpx.Response(304),a,b,a])
    for _ in range(7):
        only_job(store); assert monitor_.run_once()
    events=store.source_events('P01')['items'][::-1]
    assert [x['outcome'] for x in events]==[
        'baseline','changed','changed','not-modified','unchanged-content','changed','changed']
    assert len({x['version_id'] for x in events})==2
    assert events[0]['version_id']==events[2]['version_id']==events[3]['version_id']==events[-1]['version_id']
    assert store.queue()['total']==5  # Each real transition remains reviewable.
    changes=[x for x in store.queue()['items'] if x['kind']=='changed']
    assert len({x['id'] for x in changes})==4
    for change in changes:
        assert change['payload']['previous_version_id']!=change['version_id']
    activity=next(x for x in store.source_activity()['items'] if x['id']=='P01')
    assert activity['version_id']==events[-1]['version_id']
    assert activity['sha256']==hashlib.sha256(a.content).hexdigest()
    assert store.publication()==before  # Fetches cannot accept or revise claims.
    assert requests[-1].headers['if-none-match']=='"b"'
    assert len(list((tmp_path/'blobs').iterdir()))==2


def test_acknowledged_transition_can_recur_without_losing_new_review(store,tmp_path):
    m,_=monitor(store,tmp_path,[page('A'),page('B'),page('A'),page('B')])
    for _ in range(2): only_job(store); m.run_once()
    for item in store.queue()['items']:
        store.resolve_queue(item['id'],'acknowledged','reviewer','No supported numerical change')
    assert store.queue()['total']==0
    for _ in range(2): only_job(store); m.run_once()
    assert store.queue()['total']==2
    assert all(x['kind']=='changed' for x in store.queue()['items'])


def test_full_responses_replace_validators_304_keeps_them(store,tmp_path):
    modified='Wed, 01 Jul 2026 10:00:00 GMT'
    m,requests=monitor(store,tmp_path,[
        page('A',etag='"a"',**{'last-modified':modified}),
        httpx.Response(304),page('B'),page('C',etag='"c"'),httpx.Response(304)])
    for _ in range(5): only_job(store); m.run_once()
    source=[r for r in requests if r.url.path!='/robots.txt']
    assert source[1].headers['if-none-match']==source[2].headers['if-none-match']=='"a"'
    assert source[2].headers['if-modified-since']==modified
    assert 'if-none-match' not in source[3].headers
    assert 'if-modified-since' not in source[3].headers
    assert source[4].headers['if-none-match']=='"c"'
    assert 'if-modified-since' not in source[4].headers
    with store.connect() as db:
        job=db.execute("SELECT etag,last_modified FROM jobs WHERE source_id='P01'").fetchone()
    assert tuple(job)==('"c"',None)


def test_failure_does_not_replace_latest_observed_representation(store,tmp_path):
    m,_=monitor(store,tmp_path,[page('A',etag='"a"'),httpx.Response(503),httpx.Response(304)])
    for _ in range(3): only_job(store); m.run_once()
    events=store.source_events('P01')['items']
    assert [x['outcome'] for x in events]==['not-modified','deferred','baseline']
    assert events[0]['version_id']==events[2]['version_id']
    assert events[1]['version_id'] is None
    assert store.queue()['total']==1


def test_stale_worker_cannot_append_success_or_reorder_history(store,tmp_path):
    m,_=monitor(store,tmp_path,[])
    old=m.lease()
    with store.connect() as db:
        db.execute("UPDATE jobs SET lease_until='2000-01-01' WHERE source_id='P01'")
    new=m.lease()
    m._success(new,200,{'content-type':'text/html'},b'<article>Current</article>',new['url'])
    m._success(old,200,{'content-type':'text/html'},b'<article>Stale</article>',old['url'])
    assert store.source_events('P01')['total']==1
    assert store.queue()['total']==1
    assert store.source_activity()['items'][0]['sha256']==hashlib.sha256(b'<article>Current</article>').hexdigest()


@pytest.mark.parametrize('statement',[
    "UPDATE fetch_events SET outcome='fabricated'",
    'DELETE FROM fetch_events',
])
def test_fetch_event_audit_is_append_only(store,tmp_path,statement):
    m,_=monitor(store,tmp_path,[page('A')]);m.run_once()
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError,match='immutable'):
            db.execute(statement)
    assert store.source_events('P01')['total']==1


def test_activity_distinguishes_capture_age_from_editorial_date(store,tmp_path,monkeypatch):
    m,_=monitor(store,tmp_path,[page('A')]);m.run_once()
    monkeypatch.setattr('server.store.now',lambda:'2040-01-03T00:00:00+00:00')
    with store.connect() as db:
        db.execute("UPDATE jobs SET last_success='2040-01-01T00:00:00+00:00',refresh_hours=24 WHERE source_id='P01'")
    item=store.source_activity()['items'][0]
    assert item['capture_state']=='recent'  # Exactly two configured intervals.
    assert item['reviewed_retrieval_at']!='2040-01-03'
    with store.connect() as db:
        db.execute("UPDATE jobs SET last_success='2039-12-31T23:59:59+00:00',last_error='HTTP 503' WHERE source_id='P01'")
    item=store.source_activity()['items'][0]
    assert item['capture_state']=='stale' and item['fetch_state']=='deferred'
    assert store.source_activity()['items'][1]['capture_state']=='never'
    assert 'lease_token' not in item


def test_activity_and_event_api_are_paginated_read_only_and_private(tmp_path):
    app=create_app(tmp_path/'atlas.sqlite3',background=False)
    with TestClient(app) as client:
        response=client.get('/api/source-activity?limit=2')
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        data=response.json()
        assert len(data['items'])==2 and data['next_offset']==2
        assert all(x['capture_state']=='never' for x in data['items'])
        assert 'claims' in data['policy'] and 're-reviewed' in data['policy']
        assert client.get('/api/source-activity?offset=999').json()['next_offset'] is None
        assert client.get('/api/source-activity?limit=101').status_code==422
        assert client.get('/api/sources/P01/events').json()['total']==0
        assert client.get('/api/sources/unknown/events').status_code==404
        assert client.post('/api/source-activity',json={}).status_code==405
        assert client.get('/var/blobs/arbitrary').status_code==404


def test_search_filters_before_pagination_without_a_hidden_hit_limit(store):
    with store.connect() as db:
        for i in range(153):
            row={'id':f'fixture-{i:03}','name':f'Regression campus {i:03}',
                 'country':'Target' if i>=143 else 'Other','location':'Test only','owner_label':'Test'}
            db.execute('INSERT INTO sites VALUES(?,?,?,?)',(row['id'],row['name'],row['country'],canonical(row)))
            db.execute('INSERT INTO site_search VALUES(?,?,?,?)',(row['id'],row['name'],row['location'],row['owner_label']))
    page1=store.site_page('Regression',limit=100)
    assert page1['total']==153 and page1['next_offset']==100
    assert len(store.site_page('Regression',limit=100,offset=100)['items'])==53
    filtered=store.site_page('Regression','Target',limit=4,offset=4)
    assert filtered['total']==10 and len(filtered['items'])==4 and filtered['next_offset']==8
    assert all(x['country']=='Target' for x in filtered['items'])
    assert store.site_page('Regression','Target',offset=20)['items']==[]
    assert store.site_page('" OR 1=1 --')['total']==0
