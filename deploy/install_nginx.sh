#!/usr/bin/env bash
# Self-contained: paste this entire file into the Untitled1 server terminal.
# It needs no checkout, Python package, or sibling configuration file.
sudo /usr/bin/python3 - "$@" <<'PY'
import argparse
import grp
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
site = Path('/etc/nginx/sites-available/untitled1.cc')
auth = Path('/etc/nginx/.compute-atlas-htpasswd')
block = '''    # BEGIN compute-atlas
    location = /compute {
        return 308 /compute/;
    }
    location ^~ /compute/ {
        auth_basic "Compute Atlas";
        auth_basic_user_file /etc/nginx/.compute-atlas-htpasswd;
        proxy_pass http://127.0.0.1:8137/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization "";
        proxy_cache off;
        proxy_read_timeout 60s;
    }
    # END compute-atlas
'''
if not args.dry_run and os.geteuid() != 0:
    raise SystemExit('Run this script with sudo on the Untitled1 server.')
os.umask(0o077)
if not site.is_file():
    raise SystemExit('This is not the expected server: Nginx site untitled1.cc is absent.')
try:
    with build_opener(ProxyHandler({})).open('http://127.0.0.1:8137/api/health', timeout=5) as response:
        ready = json.load(response)
    if ready.get('status') != 'ok' or ready.get('database') != 'ready':
        raise ValueError('Database is not ready')
except Exception:
    raise SystemExit('Atlas service is not healthy on 127.0.0.1:8137. No Nginx changes made.')
original = site.read_text()
start, end = '    # BEGIN compute-atlas\n', '    # END compute-atlas\n'
anchor = '    location / {\n        try_files $uri $uri/ $uri/index.html =404;\n    }\n'
if start in original or end in original:
    if original.count(start) != 1 or original.count(end) != 1:
        raise SystemExit('Ambiguous Compute Atlas block; no changes made.')
    a = original.index(start)
    b = original.index(end, a) + len(end)
    proposed = original[:a] + block + original[b:]
else:
    if any(s in original for s in ('location = /compute', 'location /compute', 'location ^~ /compute')):
        raise SystemExit('An existing unmarked compute route needs review; no changes made.')
    if original.count(anchor) != 1 or 'ssl_certificate ' not in original:
        raise SystemExit('Expected TLS configuration is absent; no changes made.')
    proposed = original.replace(anchor, block + '\n' + anchor, 1)
if not auth.exists() and not Path('/etc/nginx/.files-htpasswd').is_file():
    raise SystemExit('Existing /files password file is absent; no changes made.')
if args.dry_run:
    print('Dry run OK: healthy Atlas, expected Nginx site, protected route prepared. No changes made.')
    raise SystemExit(0)

def write_site(content):
    with tempfile.NamedTemporaryFile(mode='w', dir=site.parent, delete=False) as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
        name = stream.name
    os.chmod(name, 0o644)
    os.replace(name, site)

def wait_for_auth(paths, origin='https://untitled1.cc/compute/', resolve='untitled1.cc:443:127.0.0.1'):
    # nginx -s reload signals the master; new workers may not be ready yet.
    deadline = time.monotonic() + 20
    waiting = False
    for path in paths:
        while True:
            command = ['/usr/bin/curl', '--silent', '--show-error',
                       '--connect-timeout', '2', '--max-time', '3', '--noproxy', '*',
                       '--output', '/dev/null', '--write-out', '%{http_code}']
            if resolve:
                command += ['--resolve', resolve]
            code = subprocess.check_output(command + [origin + path], text=True).strip()
            if code == '401':
                break
            if code != '404' or time.monotonic() >= deadline:
                raise RuntimeError('Auth check failed for /compute/' + path + ': HTTP ' + code)
            if not waiting:
                print('Waiting for Nginx to activate the protected route...', flush=True)
                waiting = True
            time.sleep(0.25)

backup_dir = Path('/etc/nginx/compute-atlas-backups')
backup_dir.mkdir(mode=0o700, exist_ok=True)
backup = backup_dir / ('untitled1.cc-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
shutil.copy2(site, backup)
if not auth.exists():
    shutil.copyfile('/etc/nginx/.files-htpasswd', auth)
    os.chown(auth, 0, grp.getgrnam('www-data').gr_gid)
    os.chmod(auth, 0o640)
try:
    write_site(proposed)
    subprocess.run(['/usr/sbin/nginx', '-t'], check=True)
    subprocess.run(['/usr/bin/systemctl', 'reload', 'nginx'], check=True)
    wait_for_auth(('', 'api/publication', 'src/app.js', 'data/evidence.json',
                   'originals/compute_infrastructure_report.pdf', 'compute_atlas.html'))
except Exception:
    write_site(original)
    subprocess.run(['/usr/sbin/nginx', '-t'], check=True)
    subprocess.run(['/usr/bin/systemctl', 'reload', 'nginx'], check=True)
    print('Installation failed; previous Nginx site restored. Backup:', backup)
    raise
print('Installed; six HTTPS auth checks passed. Backup:', backup)
print('Open https://untitled1.cc/compute/ and use your existing /files login.')
PY
