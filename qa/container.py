"""Exercise the actual non-root image with a read-only root and persistent volume.

CI builds from a restrictive-permission checkout. --image can test a locally
built image when the environment requires its own proxy/certificate setup.
"""
import argparse, json, shutil, subprocess, tempfile, time, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--image');args=parser.parse_args()
name='compute-atlas-qa-'+uuid.uuid4().hex[:12]
image=args.image or name;volume=name+'-data';checks=[]
def run(*cmd,check=True):
    return subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)
def check(label,ok):
    checks.append({'test':label,'pass':bool(ok)})
    print(('PASS ' if ok else 'FAIL ')+label,flush=True)
def start():
    run('docker','run','-d','--name',name,'--network','none','--read-only','--tmpfs','/tmp:size=64m','--mount',f'source={volume},target=/app/var','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','512m','--cpus','1',image,'python','-m','server','serve','--host','127.0.0.1','--no-refresh')
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        result=run('docker','exec',name,'python','-c',"import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=1)",check=False)
        if result.returncode==0:return
        state=run('docker','inspect',name,'--format','{{.State.Status}}',check=False).stdout.strip()
        if state=='exited':break
        time.sleep(.5)
    raise RuntimeError('Container failed to become healthy: '+run('docker','logs','--tail','20',name,check=False).stderr)
def inside(code):
    return json.loads(run('docker','exec',name,'python','-c',code).stdout)
try:
    if not args.image:
        with tempfile.TemporaryDirectory(prefix='atlas-container-context-') as tmp:
            target=Path(tmp)
            for item in ('Dockerfile','requirements.txt','server','src','data','originals','index.html','compute_atlas.html'):
                path=ROOT/item
                if path.is_dir():shutil.copytree(path,target/item,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                else:shutil.copy2(path,target/item)
            # Docker preserves these modes. COPY ownership must allow the service
            # account to read every runtime asset even with a private checkout.
            for path in target.rglob('*'):path.chmod(0o700 if path.is_dir() else 0o600)
            result=run('docker','build','-t',image,str(target),check=False)
            if result.returncode:raise RuntimeError('Docker build failed:\n'+result.stderr[-6000:])
    run('docker','volume','create',volume)
    start()
    result=inside("""import hashlib,json,os,sqlite3,urllib.request,urllib.error
base='http://127.0.0.1:8000'
def get(path):
 with urllib.request.urlopen(base+path,timeout=10) as r:return r.status,r.read(),dict(r.headers)
health=json.loads(get('/api/health')[1]);publication=get('/api/publication')[1]
assets={p:get(p)[0] for p in ['/','/index.html','/compute_atlas.html','/src/app.js','/data/evidence.json']}
blocked={}
for path in ['/server/store.py','/Dockerfile','/var/atlas.sqlite3']:
 try:blocked[path]=get(path)[0]
 except urllib.error.HTTPError as e:blocked[path]=e.code
with sqlite3.connect('/app/var/atlas.sqlite3') as db:
 db.execute('CREATE TABLE container_delivery_probe (value TEXT)');db.execute('INSERT INTO container_delivery_probe VALUES (?)',('persisted',))
print(json.dumps({'uid':os.getuid(),'health':health,'observations':len(json.loads(publication)['observations']),'hash':hashlib.sha256(publication).hexdigest(),'assets':assets,'blocked':blocked}))
""")
    check('service runs as non-root',result['uid']!=0)
    check('SQLite service healthy with read-only root',result['health']['status']=='ok' and result['health']['database']=='ready')
    check('accepted publication contains reviewed observations',result['observations']>0)
    check('hosted standalone and source assets readable',all(v==200 for v in result['assets'].values()))
    check('implementation and database are not public assets',all(v in (403,404) for v in result['blocked'].values()))
    run('docker','rm','-f',name)
    start()
    restored=inside("""import hashlib,json,sqlite3,urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/api/publication',timeout=10) as r:publication=r.read()
with sqlite3.connect('/app/var/atlas.sqlite3') as db:value=db.execute('SELECT value FROM container_delivery_probe').fetchone()[0]
print(json.dumps({'value':value,'hash':hashlib.sha256(publication).hexdigest()}))
""")
    check('database survives replacement of service container',restored['value']=='persisted')
    check('restart preserves accepted publication exactly',restored['hash']==result['hash'])
finally:
    run('docker','rm','-f',name,check=False)
    run('docker','volume','rm',volume,check=False)
    if not args.image:run('docker','image','rm',image,check=False)
report={'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(ROOT/'qa/container_results.json').write_text(json.dumps(report,indent=2))
print(f"{report['passed']}/{report['total']} passed",flush=True)
raise SystemExit(report['passed']!=report['total'])
