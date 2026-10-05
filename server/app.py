"""Same-origin, read-only publication API and deliberately allowlisted static app."""
from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from .store import ROOT, Store, canonical, digest
from .acquire import Monitor
from .identity import identity_document

log = logging.getLogger('compute_atlas')


def create_app(db_path: Path | None = None, *, background: bool = True, root: Path = ROOT, monitor_factory=Monitor) -> FastAPI:
    path = db_path or root/'var/atlas.sqlite3'
    store = Store(path); store.seed(root)

    async def worker(monitor):
        while True:
            try:
                worked = await asyncio.to_thread(monitor.run_once)
                if not worked: await asyncio.sleep(30)
            except asyncio.CancelledError: raise
            except Exception:
                log.exception('Source monitor iteration failed; retrying without changing publication')
                await asyncio.sleep(30)

    @asynccontextmanager
    async def lifespan(app):
        monitor = monitor_factory(store,path.parent/'blobs') if background else None
        task = asyncio.create_task(worker(monitor)) if monitor else None
        app.state.background_refresh = bool(task)
        try: yield
        finally:
            app.state.background_refresh = False
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError): await task
            # In-flight bounded network requests may finish in the executor before process exit.
            if monitor: monitor.close()

    app = FastAPI(title='Compute Atlas evidence API',version='1.0.0',lifespan=lifespan,docs_url='/api/docs',openapi_url='/api/openapi.json',redoc_url=None)
    app.state.store = store
    app.state.background_refresh = False

    @app.middleware('http')
    async def security_headers(request,call_next):
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['X-Frame-Options']='DENY'
        if request.url.path.startswith('/api/'):
            response.headers.setdefault('Cache-Control','no-store')
        return response

    @app.get('/api/health')
    def health():
        with store.connect() as db: db.execute('SELECT 1').fetchone()
        return {'status':'ok','database':'ready'}

    @app.get('/api/status')
    def status(): return store.status(app.state.background_refresh)

    @app.get('/api/review-queue')
    def queue(limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0)):
        return store.queue(limit,offset)

    @app.get('/api/publication')
    def publication(request:Request):
        data=store.publication(); etag='"'+data['publication_hash']+'"'
        headers={'ETag':etag,'Cache-Control':'no-cache'}
        if request.headers.get('if-none-match')==etag: return Response(status_code=304,headers=headers)
        return JSONResponse(data,headers=headers)

    @app.get('/api/sites')
    def sites(q:str=Query('',max_length=500),country:str|None=None,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0)):
        return store.site_page(q,country,limit,offset)

    @app.get('/api/sites/{site_id}')
    def site(site_id:str):
        import json
        with store.connect() as db:
            row=db.execute('SELECT payload FROM sites WHERE id=?',(site_id,)).fetchone()
            if not row: raise HTTPException(404,'Unknown site')
            claims=[{'kind':r['kind'],**json.loads(r['payload'])} for r in db.execute('SELECT kind,payload FROM accepted_claims WHERE site_id=? ORDER BY kind,id',(site_id,))]
        return {'archive':json.loads(row['payload']),'accepted_claims':claims,'archive_warning':'Historical independent estimates; not silently replaced by new source captures.'}

    @app.get('/api/sites/{site_id}/identity')
    def identity(site_id: str):
        data = identity_document(store, site_id)
        if data is None: raise HTTPException(404, 'Unknown site')
        return data

    @app.get('/api/claims/{claim_id}/history')
    def claim_history(claim_id:str):
        data=store.claim_history(claim_id)
        if not data or not any(x['claim']['id']==claim_id for x in data['items']):
            raise HTTPException(404,'No reviewed claim with this identity')
        return data

    @app.get('/api/source-activity')
    def source_activity(limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0)):
        return store.source_activity(limit,offset)

    @app.get('/api/sources/{source_id}/events')
    def source_events(source_id:str,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0)):
        data=store.source_events(source_id,limit,offset)
        if data is None: raise HTTPException(404,'Unknown source')
        return data

    @app.get('/api/sources/{source_id}/versions')
    def versions(source_id:str,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0)):
        with store.connect() as db:
            if not db.execute('SELECT 1 FROM sources WHERE id=?',(source_id,)).fetchone(): raise HTTPException(404,'Unknown source')
            total=db.execute('SELECT COUNT(*) FROM source_versions WHERE source_id=?',(source_id,)).fetchone()[0]
            rows=[dict(r) for r in db.execute('SELECT * FROM source_versions WHERE source_id=? ORDER BY captured_at DESC,rowid DESC LIMIT ? OFFSET ?',(source_id,limit,offset))]
        return {'items':rows,'total':total,'next_offset':offset+len(rows) if offset+len(rows)<total else None,'raw_snapshots':'Private local evidence store; not distributed through the public API.'}

    @app.get('/api/audit')
    def audit(limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0)):
        import json
        with store.connect() as db:
            total=db.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
            rows=[{**dict(r),'payload':json.loads(r['payload'])} for r in db.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?',(limit,offset))]
        return {'items':rows,'total':total,'next_offset':offset+len(rows) if offset+len(rows)<total else None}

    @app.get('/')
    @app.get('/index.html')
    def index():
        text=(root/'index.html').read_text()
        text=text.replace('<head>','<head><script>window.ATLAS_SERVICE={base:"/api"};</script>',1)
        text=text.replace("load('evidence-data','data/evidence.json')", "load('evidence-data','/api/publication').catch(()=>{window.ATLAS_SERVICE_WARNING=true;return load('evidence-data','data/evidence.json')})")
        return HTMLResponse(text,headers={'Cache-Control':'no-cache'})

    @app.get('/{path:path}')
    def assets(path:str):
        candidate=Path(path)
        allowed=(len(candidate.parts)>1 and candidate.parts[0] in {'src','data','originals'}) or path=='compute_atlas.html'
        if not allowed or any(part.startswith('.') for part in candidate.parts) or '\\' in path:
            raise HTTPException(404)
        full=(root/candidate).resolve()
        if not full.is_relative_to(root.resolve()) or not full.is_file(): raise HTTPException(404)
        # Source .py is never a web asset; no ledger, backups, snapshots, environment or server code.
        if full.suffix not in {'.js','.css','.json','.html','.png','.webp','.jpg','.pdf','.xlsx','.docx','.txt'}: raise HTTPException(404)
        return FileResponse(full,headers={'Cache-Control':'public,max-age=300'})
    return app
