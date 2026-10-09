import hashlib
import json
import sqlite3

import pytest

from deploy.backup import backup
from deploy.install_nginx import proposed_config
from server.store import ROOT, Store


def test_backup_preserves_committed_ledger_and_exact_referenced_bodies(tmp_path):
    store=Store(tmp_path/'atlas.sqlite3');store.seed()
    body=b'Original immutable source response'
    digest=hashlib.sha256(body).hexdigest()
    (tmp_path/'blobs').mkdir();(tmp_path/'blobs'/digest).write_bytes(body)
    (tmp_path/'blobs'/'unreferenced.tmp').write_text('Incomplete capture')
    with store.connect() as db:
        db.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?,?,?)',('version-backup','P01',digest,digest,'text/html','https://example.com',len(body),'2026-10-09T00:00:00Z'))
    saved=backup(tmp_path)
    restored=Store(saved/'atlas.sqlite3')
    assert restored.publication()==store.publication()
    assert (saved/'blobs'/digest).read_bytes()==body
    assert set(p.name for p in (saved/'blobs').iterdir())=={digest}
    manifest=json.loads((saved/'manifest.json').read_text())
    assert manifest['blobs']==[digest]
    with sqlite3.connect(saved/'atlas.sqlite3') as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_backup_never_publishes_a_missing_or_corrupt_capture(tmp_path):
    store=Store(tmp_path/'atlas.sqlite3');store.seed()
    digest='a'*64
    with store.connect() as db:
        db.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?,?,?)',('missing-backup','P01',digest,digest,'text/html','https://example.com',3,'2026-10-09T00:00:00Z'))
    with pytest.raises(FileNotFoundError):backup(tmp_path)
    assert all(p.name.startswith('.staging-') for p in (tmp_path/'backups').iterdir())


def test_nginx_installer_preserves_other_routes_and_is_idempotent():
    base='server {\n    ssl_certificate /cert;\n    location /files/ { auth_basic "Files"; }\n    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n}\n'
    block=(ROOT/'deploy/nginx-compute.conf').read_text()
    proposed=proposed_config(base,block)
    assert proposed.replace(block+'\n','',1)==base
    assert proposed_config(proposed,block)==proposed
    assert 'location ^~ /compute/' in proposed and 'Authorization ""' in proposed
    with pytest.raises(ValueError):proposed_config(base.replace('location / {','location /compute {'),block)
