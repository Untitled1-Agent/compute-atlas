"""A ledger restored without its blobs must not claim a successful revalidation."""
import hashlib

import httpx
import pytest

from test_service import store, monitor, only_job


@pytest.mark.parametrize('damage',['missing','same_size_corruption'])
def test_missing_or_corrupt_baseline_is_refetched_unconditionally(store,tmp_path,damage):
    body=b'<article>Disclosed project facts</article>'
    answer=lambda:httpx.Response(200,content=body,headers={'content-type':'text/html','etag':'"baseline"','last-modified':'Wed, 01 Jul 2026 10:00:00 GMT'})
    m,requests=monitor(store,tmp_path,[answer(),answer(),httpx.Response(304)])
    original=store.publication()
    assert m.run_once()
    path=tmp_path/'blobs'/hashlib.sha256(body).hexdigest()
    if damage=='missing':path.unlink()
    else:path.write_bytes(b'x'*len(body))
    only_job(store);assert m.run_once()
    source_requests=[r for r in requests if r.url.path!='/robots.txt']
    assert 'if-none-match' not in source_requests[1].headers
    assert 'if-modified-since' not in source_requests[1].headers
    assert path.read_bytes()==body
    only_job(store);assert m.run_once()
    assert requests[-1].headers['if-none-match']=='"baseline"'
    assert store.source_events('P01')['items'][0]['outcome']=='not-modified'
    assert store.status()['capture_storage']['unavailable_bodies']==0
    assert store.publication()==original
    m.close()


def test_unsolicited_304_without_body_is_not_success(store,tmp_path):
    body=b'<article>Original source</article>'
    m,_=monitor(store,tmp_path,[httpx.Response(200,content=body,headers={'etag':'"a"'}),httpx.Response(304)])
    assert m.run_once()
    (tmp_path/'blobs'/hashlib.sha256(body).hexdigest()).unlink()
    only_job(store);assert m.run_once()
    event=store.source_events('P01')['items'][0]
    assert event['outcome']=='deferred'
    assert 'verified captured body' in event['error']
    assert store.status()['capture_storage']['unavailable_bodies']==1
    m.close()


def test_capture_inventory_counts_distinct_bodies_and_rejects_symlinks(store,tmp_path):
    body=b'<article>Shared public document</article>'
    m,_=monitor(store,tmp_path,[httpx.Response(200,content=body)])
    m.run_once()
    status=store.capture_storage()
    assert status['referenced_bodies']==status['present_bodies']==1
    capture=tmp_path/'blobs'/hashlib.sha256(body).hexdigest()
    other=tmp_path/'outside-body';capture.rename(other);capture.symlink_to(other)
    assert store.capture_storage()['unavailable_bodies']==1
    m.close()
