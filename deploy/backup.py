"""Snapshot committed WAL and exactly the immutable bodies that snapshot references."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.store import Store


def backup(state: Path) -> Path:
    os.umask(0o077)
    state=state.resolve()
    if not (state/'atlas.sqlite3').is_file():
        raise FileNotFoundError('The live ledger must exist before a backup')
    with sqlite3.connect(state/'atlas.sqlite3') as db:
        database_bytes=db.execute('PRAGMA page_count').fetchone()[0]*db.execute('PRAGMA page_size').fetchone()[0]
        hashes={row[0] for row in db.execute('SELECT sha256 FROM source_versions')}
    if any(not re.fullmatch('[0-9a-f]{64}',digest) for digest in hashes):
        raise ValueError('Invalid content-addressed body')
    body_bytes=sum((state/'blobs'/digest).stat().st_size for digest in hashes)
    if shutil.disk_usage(state).free < database_bytes+body_bytes+64*1024*1024:
        raise OSError('Backup deferred: insufficient space for the snapshot and 64 MiB disk reserve')
    backups=state/'backups';backups.mkdir(mode=0o700,exist_ok=True)
    token=uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='.staging-',dir=backups) as folder:
        staging=Path(folder)
        Store(state/'atlas.sqlite3').backup(staging/'atlas.sqlite3')
        with sqlite3.connect(staging/'atlas.sqlite3') as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Backup database integrity check failed')
            hashes={row[0] for row in db.execute('SELECT sha256 FROM source_versions')}
        (staging/'blobs').mkdir(mode=0o700)
        for digest in sorted(hashes):
            if not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Invalid content-addressed body')
            source=state/'blobs'/digest
            if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
                raise ValueError('Referenced capture is missing or corrupt')
            shutil.copyfile(source,staging/'blobs'/digest)
        manifest={'created_at':datetime.now(timezone.utc).isoformat(),'sqlite_sha256':hashlib.sha256((staging/'atlas.sqlite3').read_bytes()).hexdigest(),'blobs':sorted(hashes),'policy':'Committed database snapshot and all referenced immutable captures; retain outside the web root.'}
        (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        target=backups/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+token[:8])
        staging.rename(target)
        return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True)
    print(backup(parser.parse_args().state))
