"""Real unprivileged Nginx: reproduce a delayed reload and verify the installer.

Only the temporary instance's master is paused; the host Nginx is untouched.
HTTP is used on a random loopback port to exercise the native reload/auth phases.
Production checks continue to use certificate-verified HTTPS.
"""
from __future__ import annotations

import ast
import json
import os
import signal
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
NGINX='/usr/sbin/nginx'
checks=[]


def check(name,passed,**detail):
    checks.append({'test':name,'pass':bool(passed),**detail})
    print(('PASS ' if passed else 'FAIL ')+name,flush=True)


source=(ROOT/'deploy/install_nginx.sh').read_text().split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
function=next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='wait_for_auth')
scope={'subprocess':subprocess,'time':time}
exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-installer-auth-check','exec'),scope)

with tempfile.TemporaryDirectory(prefix='compute-atlas-nginx-qa-') as folder:
    prefix=Path(folder)
    public=prefix/'public/compute';public.mkdir(parents=True)
    (public/'index.html').write_text('Compute Atlas isolated reload fixture')
    hashed=subprocess.check_output(['/usr/bin/openssl','passwd','-apr1','-stdin'],input='temporary-qa\n',text=True).strip()
    (prefix/'auth').write_text('researcher:'+hashed+'\n')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    config=prefix/'nginx.conf'
    base=f'''pid {prefix}/nginx.pid;
error_log {prefix}/error.log warn;
worker_processes 1;
events {{ worker_connections 32; }}
http {{
    access_log off;
    server {{
        listen 127.0.0.1:{port};
        root {prefix}/public;
        ROUTES
        location / {{ return 404; }}
    }}
}}
'''
    config.write_text(base.replace('ROUTES',''))
    process=subprocess.Popen([NGINX,'-p',str(prefix)+'/', '-c',str(config),'-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    origin=f'http://127.0.0.1:{port}/compute/'
    resume=None
    try:
        with httpx.Client(trust_env=False,timeout=2) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read().decode())
                try:
                    if client.get(origin).status_code==404:break
                except httpx.HTTPError:pass
                time.sleep(.02)
            check('actual Nginx initially serves the previous 404 route',client.get(origin).status_code==404)
            protected=f'''location /compute/ {{
                auth_basic "Compute Atlas QA";
                auth_basic_user_file {prefix}/auth;
                try_files $uri /compute/index.html;
            }}'''
            config.write_text(base.replace('ROUTES',protected))
            subprocess.run([NGINX,'-p',str(prefix)+'/', '-c',str(config),'-t'],check=True,capture_output=True)
            # Queue HUP while this isolated master is paused. Existing workers
            # still serve the old config, exactly the state the installer hit.
            os.kill(process.pid,signal.SIGSTOP)
            subprocess.run([NGINX,'-p',str(prefix)+'/', '-c',str(config),'-s','reload'],check=True,capture_output=True)
            immediate=client.get(origin).status_code
            check('reload command returns before the new auth route is active',immediate==404,status=immediate)
            resume=threading.Timer(.35,lambda:os.kill(process.pid,signal.SIGCONT));resume.start()
            started=time.monotonic()
            paths=('', 'api/publication','src/app.js','data/evidence.json',
                   'originals/compute_infrastructure_report.pdf','compute_atlas.html')
            scope['wait_for_auth'](paths,origin=origin,resolve=None)
            check('actual installer waits for real Nginx activation',time.monotonic()-started>=.25)
            for path in paths:
                check('anonymous '+(path or 'entry')+' is protected',client.get(origin+path).status_code==401)
            check('valid Basic Auth loads content',client.get(origin,auth=('researcher','temporary-qa')).status_code==200)
            check('incorrect Basic Auth remains denied',client.get(origin,auth=('researcher','wrong-fixture')).status_code==401)
    finally:
        if resume:
            resume.cancel();resume.join()
        if process.poll() is None:
            os.kill(process.pid,signal.SIGCONT)
            os.kill(process.pid,signal.SIGQUIT)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate();process.wait(timeout=5)
        process.stderr.close()

report={'execution':'actual isolated Nginx on loopback HTTP; delayed master reload; canonical installer auth helper',
        'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/nginx_reload_results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
raise SystemExit(0 if report['passed']==report['total'] else 1)
