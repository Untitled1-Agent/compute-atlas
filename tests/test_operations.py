import hashlib
import ast
import io
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request

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
    assert not (tmp_path/'backups').exists()


def test_backup_defers_before_allocating_when_disk_space_is_low(tmp_path,monkeypatch):
    from types import SimpleNamespace
    store=Store(tmp_path/'atlas.sqlite3');store.seed();before=store.publication()
    monkeypatch.setattr('deploy.backup.shutil.disk_usage',lambda _:SimpleNamespace(free=1))
    with pytest.raises(OSError,match='Backup deferred'):
        backup(tmp_path)
    assert not (tmp_path/'backups').exists()
    assert store.publication()==before


def test_repeated_corrupt_backups_remove_staging_and_preserve_live_state(tmp_path):
    store=Store(tmp_path/'atlas.sqlite3');store.seed()
    before=store.publication()
    digest='a'*64
    (tmp_path/'blobs').mkdir();(tmp_path/'blobs'/digest).write_bytes(b'corrupt')
    with store.connect() as db:
        db.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?,?,?)',('corrupt-backup','P01',digest,digest,'text/html','https://example.com',7,'2026-10-09T00:00:00Z'))
    for _ in range(3):
        with pytest.raises(ValueError,match='missing or corrupt'):backup(tmp_path)
        assert list((tmp_path/'backups').iterdir())==[]
    assert store.publication()==before
    assert (tmp_path/'blobs'/digest).read_bytes()==b'corrupt'


def test_nginx_installer_preserves_other_routes_and_is_idempotent():
    base='server {\n    ssl_certificate /cert;\n    location /files/ { auth_basic "Files"; }\n    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n}\n'
    block=(ROOT/'deploy/nginx-compute.conf').read_text()
    proposed=proposed_config(base,block)
    assert proposed.replace(block+'\n','',1)==base
    assert proposed_config(proposed,block)==proposed
    assert 'location ^~ /compute/' in proposed and 'Authorization ""' in proposed
    with pytest.raises(ValueError):proposed_config(base.replace('location / {','location /compute {'),block)


@pytest.mark.parametrize('markers',[
    '    # END compute-atlas\n',
    '    # BEGIN compute-atlas\n',
    '    # END compute-atlas\n    # BEGIN compute-atlas\n',
])
def test_nginx_installer_rejects_incomplete_or_reversed_markers(markers):
    original='server {\n    ssl_certificate /cert;\n'+markers+'    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n}\n'
    with pytest.raises(ValueError,match='Ambiguous Compute Atlas block'):
        proposed_config(original,(ROOT/'deploy/nginx-compute.conf').read_text())


def test_python_installer_restores_and_reloads_after_a_failed_reload(tmp_path,monkeypatch):
    from deploy import install_nginx
    site=tmp_path/'untitled1.cc';auth=tmp_path/'auth'
    original='server {\n    ssl_certificate /cert;\n    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n}\n'
    site.write_text(original);auth.write_text('dummy-test-hash')
    monkeypatch.setattr(install_nginx,'CONFIG',site)
    monkeypatch.setattr(install_nginx,'AUTH',auth)
    monkeypatch.setattr(install_nginx,'BACKUPS',tmp_path/'backups')
    monkeypatch.setattr(sys,'argv',['install_nginx'])
    monkeypatch.setattr(os,'geteuid',lambda:0)
    calls=[]
    def run(argv,**_):
        calls.append(argv)
        if len(calls)==2:raise subprocess.CalledProcessError(1,argv)
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(subprocess.CalledProcessError):install_nginx.main()
    assert site.read_text()==original
    assert calls==[['/usr/sbin/nginx','-t'],['/usr/bin/systemctl','reload','nginx'],
                  ['/usr/sbin/nginx','-t'],['/usr/bin/systemctl','reload','nginx']]


def standalone_installer_source():
    script=(ROOT/'deploy/install_nginx.sh').read_text()
    return script.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]


def test_standalone_installer_embeds_the_canonical_auth_configuration():
    parsed=ast.parse(standalone_installer_source())
    embedded=next(ast.literal_eval(node.value) for node in parsed.body
                  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='block' for t in node.targets))
    assert embedded==(ROOT/'deploy/nginx-compute.conf').read_text()


@pytest.fixture
def standalone_installation(tmp_path,monkeypatch):
    nginx=tmp_path/'nginx';(nginx/'sites-available').mkdir(parents=True)
    site=nginx/'sites-available/untitled1.cc'
    original='server {\n    ssl_certificate /cert;\n    location /files/ { auth_basic "Files"; }\n    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n}\n'
    site.write_text(original)
    (nginx/'.files-htpasswd').write_text('researcher:dummy-test-hash\n')
    source=standalone_installer_source().replace('/etc/nginx',str(nginx))
    calls=[]
    monkeypatch.setattr(sys,'argv',['install_nginx'])
    monkeypatch.setattr(os,'geteuid',lambda:0)
    monkeypatch.setattr(os,'umask',lambda _:0)
    monkeypatch.setattr(os,'chown',lambda *_:None)
    class Healthy:
        def open(self,*_,**__):return io.BytesIO(b'{"status":"ok","database":"ready"}')
    monkeypatch.setattr(urllib.request,'build_opener',lambda *_:Healthy())
    monkeypatch.setattr(subprocess,'run',lambda argv,**_:calls.append(argv))
    monkeypatch.setattr(subprocess,'check_output',lambda argv,**_:calls.append(argv) or '401')
    def execute():exec(compile(source,'standalone-nginx-install','exec'),{'__name__':'__main__'})
    return nginx,site,original,calls,execute


def test_standalone_installation_checks_six_auth_routes_and_preserves_credentials(standalone_installation):
    nginx,site,original,calls,execute=standalone_installation
    execute()
    installed=site.read_text()
    block=(ROOT/'deploy/nginx-compute.conf').read_text().replace('/etc/nginx',str(nginx))
    assert installed.replace(block+'\n','',1)==original
    assert (nginx/'.compute-atlas-htpasswd').read_bytes()==(nginx/'.files-htpasswd').read_bytes()
    assert (nginx/'.compute-atlas-htpasswd').stat().st_mode & 0o777 == 0o640
    assert len([c for c in calls if c[0]=='/usr/bin/curl'])==6
    assert all('--noproxy' in c and '--resolve' in c for c in calls if c[0]=='/usr/bin/curl')
    assert next((nginx/'compute-atlas-backups').iterdir()).read_text()==original
    execute()
    assert site.read_text()==installed


@pytest.mark.parametrize('failure',['nginx-validation','auth-gate'])
def test_standalone_installer_restores_and_reloads_the_previous_site(standalone_installation,monkeypatch,failure):
    _,site,original,calls,execute=standalone_installation
    if failure=='nginx-validation':
        def run(argv,**_):
            calls.append(argv)
            if len(calls)==1:raise subprocess.CalledProcessError(1,argv)
        monkeypatch.setattr(subprocess,'run',run)
    else:
        monkeypatch.setattr(subprocess,'check_output',lambda *_,**__:'200')
    with pytest.raises((subprocess.CalledProcessError,RuntimeError)):execute()
    assert site.read_text()==original
    assert calls[-1]==['/usr/bin/systemctl','reload','nginx']


def test_standalone_installer_checks_health_before_creating_auth_or_editing_nginx(standalone_installation,monkeypatch):
    nginx,site,original,calls,execute=standalone_installation
    monkeypatch.setattr(urllib.request,'build_opener',lambda *_:None)
    with pytest.raises(SystemExit,match='No Nginx changes made'):execute()
    assert site.read_text()==original and not calls
    assert not (nginx/'.compute-atlas-htpasswd').exists()
    assert not (nginx/'compute-atlas-backups').exists()


def test_standalone_installer_waits_for_reload_instead_of_rolling_back_on_old_route(standalone_installation,monkeypatch):
    _,site,original,calls,execute=standalone_installation
    statuses=iter(['404','404','401']+['401']*5)
    def response(argv,**_):
        calls.append(argv)
        return next(statuses)
    sleeps=[]
    monkeypatch.setattr(subprocess,'check_output',response)
    monkeypatch.setattr(time,'sleep',sleeps.append)
    execute()
    assert site.read_text()!=original and 'auth_basic "Compute Atlas"' in site.read_text()
    assert len(sleeps)==2
    assert len([c for c in calls if c[0]=='/usr/bin/curl'])==8
    assert [c for c in calls if c[0]=='/usr/bin/systemctl']==[['/usr/bin/systemctl','reload','nginx']]


def test_standalone_installer_bounds_reload_wait_and_rolls_back_a_persistent_404(standalone_installation,monkeypatch):
    _,site,original,calls,execute=standalone_installation
    ticks=iter([0,21])
    monkeypatch.setattr(time,'monotonic',lambda:next(ticks,21))
    monkeypatch.setattr(subprocess,'check_output',lambda *_,**__:'404')
    with pytest.raises(RuntimeError,match='HTTP 404'):execute()
    assert site.read_text()==original
    assert calls[-1]==['/usr/bin/systemctl','reload','nginx']
