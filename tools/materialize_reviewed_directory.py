"""Materialize a reviewer-selected capture; never accept the latest capture implicitly.

A repository writer commits the exact artifact/content hashes and editorial decision
under data/catalog/operator-directory-review.json. CI may materialize only those bytes
on a review branch. The resulting publication is tracked, so later offline builds do
not depend on artifact retention or network access. This tool does not merge or push.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from server.operator_directory import validate_directory


def materialize(manifest, archive):
    if hashlib.sha256(archive).hexdigest()!=manifest['artifact_sha256']:
        raise ValueError('Captured artifact checksum differs from review')
    if len(archive)>10_000_000:
        raise ValueError('Directory artifact exceeds size limit')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        files=bundle.infolist()
        if len(files)!=1 or files[0].filename!='candidate.json' or files[0].file_size>2_000_000:
            raise ValueError('Unexpected directory artifact contents')
        raw=bundle.read(files[0])
    if hashlib.sha256(raw).hexdigest()!=manifest['candidate_sha256']:
        raise ValueError('Candidate bytes differ from review')
    data=validate_directory(json.loads(raw))
    if data['review'] is not None or len(data['records'])!=manifest['expected_records']:
        raise ValueError('Unexpected candidate review or denominator')
    data['review']=manifest['review']
    validate_directory(data)
    result=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    if hashlib.sha256(result).hexdigest()!=manifest['publication_sha256']:
        raise ValueError('Publication does not match the reviewed projection')
    return result


def main():
    manifest_path=ROOT/'data/catalog/operator-directory-review.json'
    if not manifest_path.exists():return
    manifest=json.loads(manifest_path.read_text())
    target=ROOT/'data/catalog/operator-directory.json'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==manifest['publication_sha256']:
        validate_directory(json.loads(target.read_text()))
        print('Reviewed operator publication already matches; no network needed.')
        return
    repo=os.environ.get('GITHUB_REPOSITORY')
    if repo!='Untitled1-Agent/compute-atlas' or not os.environ.get('GITHUB_REF_NAME','').startswith('review/'):
        raise ValueError('Only the repository review workflow may retrieve a selected artifact')
    artifact=manifest.get('artifact_id')
    if type(artifact) is not int or artifact<=0:raise ValueError('Invalid artifact identity')
    raw=subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{artifact}/zip'],check=True,capture_output=True,timeout=60).stdout
    result=materialize(manifest,raw)
    tmp=target.with_suffix('.json.tmp');tmp.write_bytes(result);tmp.replace(target)
    print('Materialized only the explicitly reviewed directory. Tests must pass before committing.')

if __name__=='__main__':main()
