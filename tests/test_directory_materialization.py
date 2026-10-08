import hashlib,io,json,zipfile
from pathlib import Path
import pytest
from server.store import ROOT
from tools.materialize_reviewed_directory import materialize


def fixture():
    d=json.loads((ROOT/'data/catalog/operator-directory.json').read_text());review=d.pop('review');d['review']=None
    raw=(json.dumps(d,indent=2)+'\n').encode();buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('candidate.json',raw)
    d['review']=review;out=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
    return dict(artifact_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),candidate_sha256=hashlib.sha256(raw).hexdigest(),publication_sha256=hashlib.sha256(out).hexdigest(),expected_records=253,review=review),buf.getvalue(),out


def test_only_exact_reviewed_projection_is_materialized():
    manifest,archive,out=fixture()
    assert materialize(manifest,archive)==out


@pytest.mark.parametrize('key',['artifact_sha256','candidate_sha256','publication_sha256'])
def test_changed_content_fails_closed(key):
    manifest,archive,out=fixture();manifest[key]='0'*64
    with pytest.raises(ValueError):materialize(manifest,archive)


def test_denominator_and_review_are_part_of_acceptance():
    manifest,archive,out=fixture();manifest['expected_records']=1
    with pytest.raises(ValueError):materialize(manifest,archive)
    manifest,archive,out=fixture();manifest['review']={}
    with pytest.raises(ValueError):materialize(manifest,archive)


def test_checked_in_snapshot_matches_review_receipt():
    manifest=json.loads((ROOT/'data/catalog/operator-directory-review.json').read_text())
    assert hashlib.sha256((ROOT/'data/catalog/operator-directory.json').read_bytes()).hexdigest()==manifest['publication_sha256']
    assert json.loads((ROOT/'data/catalog/operator-directory.json').read_text())['review']==manifest['review']
