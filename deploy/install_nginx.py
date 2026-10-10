"""Install only the Compute Atlas location in the existing untitled1.cc TLS server.

Run as the host administrator after the loopback service and checks are ready.
Existing locations are preserved. The original site config is backed up before
an atomic edit; validation failure restores it before any reload.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import grp
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CONFIG=Path('/etc/nginx/sites-available/untitled1.cc')
AUTH=Path('/etc/nginx/.compute-atlas-htpasswd')
BACKUPS=Path('/etc/nginx/compute-atlas-backups')


def proposed_config(original: str, block: str) -> str:
    start='    # BEGIN compute-atlas\n';end='    # END compute-atlas\n'
    if start in original or end in original:
        if original.count(start)!=1 or original.count(end)!=1 or original.index(end)<original.index(start):
            raise ValueError('Ambiguous Compute Atlas block')
        a=original.index(start);b=original.index(end,a)+len(end)
        return original[:a]+block+original[b:]
    if 'location = /compute' in original or 'location /compute' in original or 'location ^~ /compute' in original:
        raise ValueError('Existing Compute Atlas location requires explicit reconciliation')
    anchor='    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n'
    if original.count(anchor)!=1:raise ValueError('Expected TLS static location is absent or ambiguous')
    if 'ssl_certificate ' not in original:raise ValueError('TLS server is required')
    return original.replace(anchor,block+'\n'+anchor,1)


def atomic_write(path: Path, content: str):
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,delete=False) as stream:
        stream.write(content);stream.flush();os.fsync(stream.fileno());temp=Path(stream.name)
    os.chmod(temp,0o644);os.replace(temp,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    original=CONFIG.read_text()
    proposed=proposed_config(original,(ROOT/'deploy/nginx-compute.conf').read_text())
    if args.dry_run:
        print('Compute Atlas TLS location prepared; all other locations preserved.');return
    if os.geteuid()!=0:raise SystemExit('Administrator access is required to update Nginx.')
    # Copy hashes without exposing or changing the existing /files credentials.
    if not AUTH.exists():
        shutil.copyfile('/etc/nginx/.files-htpasswd',AUTH)
        os.chown(AUTH,0,grp.getgrnam('www-data').gr_gid);os.chmod(AUTH,0o640)
    backups=BACKUPS;backups.mkdir(mode=0o700,exist_ok=True)
    target=backups/('untitled1.cc-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    shutil.copy2(CONFIG,target)
    atomic_write(CONFIG,proposed)
    try:
        subprocess.run(['/usr/sbin/nginx','-t'],check=True)
        subprocess.run(['/usr/bin/systemctl','reload','nginx'],check=True)
    except (subprocess.CalledProcessError,OSError):
        atomic_write(CONFIG,original)
        subprocess.run(['/usr/sbin/nginx','-t'],check=True)
        subprocess.run(['/usr/bin/systemctl','reload','nginx'],check=True)
        raise
    print('Compute Atlas protected TLS route installed. Existing /files login credentials apply.')


if __name__=='__main__':main()
