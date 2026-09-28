"""SQLite evidence ledger: immutable claims, source versions, queue leases, audit log.

The archive is imported as a separate historical dataset. Acquiring a new page is
not an editorial decision and cannot change accepted observations.
"""
from __future__ import annotations
import hashlib
import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
TABLES = {'observations': 'observation', 'facts': 'fact', 'relationships': 'relationship', 'discoveries': 'discovery'}

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()

SCHEMA = """
CREATE TABLE IF NOT EXISTS migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS datasets(hash TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)), imported_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sites(id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)));
CREATE TABLE IF NOT EXISTS companies(id TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)));
CREATE VIRTUAL TABLE IF NOT EXISTS site_search USING fts5(id UNINDEXED, name, location, owner, tokenize='unicode61');
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE, publisher TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)));
CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('observation','fact','relationship','discovery')), site_id TEXT REFERENCES sites(id), source_id TEXT NOT NULL REFERENCES sources(id), supersedes TEXT REFERENCES claims(id), content_hash TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)), created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS successors ON claims(supersedes);
CREATE INDEX IF NOT EXISTS claims_site ON claims(site_id,kind);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id), decision TEXT NOT NULL CHECK(decision IN ('accepted','rejected')), actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE VIEW IF NOT EXISTS current_decisions AS SELECT d.* FROM decisions d WHERE d.id=(SELECT MAX(x.id) FROM decisions x WHERE x.claim_id=d.claim_id);
CREATE VIEW IF NOT EXISTS accepted_claims AS SELECT c.* FROM claims c JOIN current_decisions d ON d.claim_id=c.id AND d.decision='accepted' WHERE NOT EXISTS (SELECT 1 FROM claims n JOIN current_decisions nd ON nd.claim_id=n.id AND nd.decision='accepted' WHERE n.supersedes=c.id);
CREATE TABLE IF NOT EXISTS source_versions(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), sha256 TEXT NOT NULL, semantic_sha256 TEXT NOT NULL, content_type TEXT NOT NULL, final_url TEXT NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length >= 0), captured_at TEXT NOT NULL, UNIQUE(source_id,sha256));
CREATE INDEX IF NOT EXISTS versions_source ON source_versions(source_id,captured_at);
CREATE TABLE IF NOT EXISTS fetch_events(id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), version_id TEXT REFERENCES source_versions(id), status INTEGER, outcome TEXT NOT NULL, error TEXT, attempted_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(source_id TEXT PRIMARY KEY REFERENCES sources(id), next_fetch_at TEXT NOT NULL, lease_until TEXT, lease_token TEXT, failures INTEGER NOT NULL DEFAULT 0, etag TEXT, last_modified TEXT, last_status INTEGER, last_success TEXT, last_error TEXT, refresh_hours REAL NOT NULL CHECK(refresh_hours>=1));
CREATE TABLE IF NOT EXISTS review_queue(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), version_id TEXT REFERENCES source_versions(id), kind TEXT NOT NULL, fingerprint TEXT NOT NULL UNIQUE, payload TEXT NOT NULL CHECK(json_valid(payload)), status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','acknowledged','rejected')), actor TEXT, reason TEXT, created_at TEXT NOT NULL, resolved_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY, action TEXT NOT NULL, actor TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)), created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS immutable_claim_update BEFORE UPDATE ON claims BEGIN SELECT RAISE(ABORT,'Claims are immutable; append a revision'); END;
CREATE TRIGGER IF NOT EXISTS immutable_claim_delete BEFORE DELETE ON claims BEGIN SELECT RAISE(ABORT,'Claims are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_version_update BEFORE UPDATE ON source_versions BEGIN SELECT RAISE(ABORT,'Source versions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_version_delete BEFORE DELETE ON source_versions BEGIN SELECT RAISE(ABORT,'Source versions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_audit_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT,'Audit events are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_audit_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT,'Audit events are immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_decision_update BEFORE UPDATE ON decisions BEGIN SELECT RAISE(ABORT,'Append a new decision'); END;
CREATE TRIGGER IF NOT EXISTS immutable_decision_delete BEFORE DELETE ON decisions BEGIN SELECT RAISE(ABORT,'Decisions are immutable'); END;
"""

class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)
            db.execute('INSERT OR IGNORE INTO migrations VALUES(1,?)', (now(),))

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=15000')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def audit(db: sqlite3.Connection, action: str, actor: str, payload: Any) -> None:
        db.execute('INSERT INTO audit_log(action,actor,payload,created_at) VALUES(?,?,?,?)', (action, actor, canonical(payload), now()))

    def seed(self, root: Path = ROOT) -> None:
        atlas = json.loads((root/'data/atlas.json').read_text())
        evidence = json.loads((root/'data/evidence.json').read_text())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for name, data in [('archive', atlas), ('publication', evidence)]:
                db.execute('INSERT OR IGNORE INTO datasets VALUES(?,?,?,?)', (digest(data), name, canonical(data), now()))
            for item in atlas['companies']:
                db.execute('INSERT OR IGNORE INTO companies VALUES(?,?,?)', (item['id'], item['name'], canonical(item)))
            for item in atlas['sites']:
                db.execute('INSERT OR IGNORE INTO sites VALUES(?,?,?,?)', (item['id'],item['name'],item['country'],canonical(item)))
            if db.execute('SELECT COUNT(*) FROM site_search').fetchone()[0] != len(atlas['sites']):
                db.execute('DELETE FROM site_search')
                db.executemany('INSERT INTO site_search VALUES(?,?,?,?)', [(s['id'],s['name'],s['location'],s['owner_label']) for s in atlas['sites']])
            for source in evidence['sources'] + evidence.get('feeds', []):
                sid=source['id']; kind='feed' if source in evidence.get('feeds',[]) else 'page'
                previous=db.execute('SELECT url FROM sources WHERE id=?',(sid,)).fetchone()
                if previous and previous['url'] != source['url']:
                    raise ValueError(f'Source identity {sid} changed URL; use a new source ID')
                db.execute('INSERT INTO sources VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (sid, source['url'], source['publisher'], kind, canonical(source)))
                db.execute('INSERT OR IGNORE INTO jobs(source_id,next_fetch_at,refresh_hours) VALUES(?,?,?)', (sid, now(), source.get('refresh_hours',24)))
            for key, kind in TABLES.items():
                for claim in evidence.get(key,[]):
                    self._insert_claim(db, kind, claim)
                    decision='accepted' if claim.get('review_status')=='accepted' else None
                    if decision and not db.execute('SELECT 1 FROM decisions WHERE claim_id=?',(claim['id'],)).fetchone():
                        self._decide(db,claim['id'],decision,'checked-in-publication','Imported explicitly reviewed, source-cited publication')
            for key in ('schema_version','published_at','policy'):
                if key in evidence:
                    db.execute('INSERT INTO metadata VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, canonical(evidence[key])))

    def _insert_claim(self, db: sqlite3.Connection, kind: str, claim: dict) -> None:
        required=['id','source_id'] + ([] if kind=='discovery' else ['site_id'])
        if any(not claim.get(k) for k in required):
            raise ValueError('Missing claim identity, site or source')
        if kind=='observation':
            if any(k not in claim for k in ('metric','value','unit','boundary','status','scope','as_of','qualifier','confidence')):
                raise ValueError('Observation lacks a measurement boundary or provenance')
            value=claim['value']
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0):
                raise ValueError('Observation value must be nonnegative finite number or null')
            if claim['metric']=='power' and (claim['unit']!='MW' or claim['boundary'] not in ('critical_it','gross_facility','generation','unspecified_compute','contracted_power')):
                raise ValueError('Unsupported power unit / measurement boundary')
        if kind=='relationship' and not db.execute('SELECT 1 FROM companies WHERE id=?',(claim.get('company_id'),)).fetchone():
            raise ValueError('Unknown counterparty')
        # Review decisions are separate from immutable claim content.
        payload={k:v for k,v in claim.items() if k!='review_status'}
        old=db.execute('SELECT content_hash FROM claims WHERE id=?',(claim['id'],)).fetchone()
        if old:
            if old['content_hash'] != digest(payload):
                raise ValueError(f'Claim {claim["id"]} changed; use a new ID and supersedes')
            return
        prior=claim.get('supersedes')
        if prior:
            p=db.execute('SELECT * FROM claims WHERE id=?',(prior,)).fetchone()
            if not p or p['kind']!=kind or p['site_id']!=claim.get('site_id'):
                raise ValueError('Revision must replace an existing claim of the same site and kind')
        db.execute('INSERT INTO claims VALUES(?,?,?,?,?,?,?,?)', (claim['id'],kind,claim.get('site_id'),claim['source_id'],prior,digest(payload),canonical(payload),now()))

    def submit_claim(self, kind: str, claim: dict, actor: str) -> None:
        if not actor.strip(): raise ValueError('Actor is required')
        with self.connect() as db:
            self._insert_claim(db,kind,claim)
            self.audit(db,'claim-submitted',actor,{'id':claim['id']})

    def _decide(self, db: sqlite3.Connection, claim_id: str, decision: str, actor: str, reason: str) -> None:
        if decision not in ('accepted','rejected') or not actor.strip() or not reason.strip():
            raise ValueError('Decision, actor and editorial reason are required')
        if not db.execute('SELECT 1 FROM claims WHERE id=?',(claim_id,)).fetchone(): raise ValueError('Unknown claim')
        if decision == 'accepted':
            c=db.execute('SELECT supersedes FROM claims WHERE id=?',(claim_id,)).fetchone()
            if c['supersedes'] and db.execute('SELECT c.id FROM accepted_claims c WHERE c.supersedes=? AND c.id!=?',(c['supersedes'],claim_id)).fetchone():
                raise ValueError('Conflicting accepted revision; reject or supersede the other revision first')
        db.execute('INSERT INTO decisions(claim_id,decision,actor,reason,created_at) VALUES(?,?,?,?,?)',(claim_id,decision,actor,reason,now()))
        self.audit(db,'claim-'+decision,actor,{'claim_id':claim_id,'reason':reason})

    def decide(self, claim_id: str, decision: str, actor: str, reason: str) -> None:
        with self.connect() as db: self._decide(db,claim_id,decision,actor,reason)

    def enqueue(self, db: sqlite3.Connection, sid: str, vid: str | None, kind: str, payload: dict, fingerprint: str) -> None:
        db.execute('INSERT OR IGNORE INTO review_queue(id,source_id,version_id,kind,fingerprint,payload,created_at) VALUES(?,?,?,?,?,?,?)', ('q-'+fingerprint[:24],sid,vid,kind,fingerprint,canonical(payload),now()))

    def resolve_queue(self, item_id: str, decision: str, actor: str, reason: str) -> None:
        if decision not in ('acknowledged','rejected') or not actor.strip() or not reason.strip(): raise ValueError('Invalid review decision')
        with self.connect() as db:
            n=db.execute("UPDATE review_queue SET status=?,actor=?,reason=?,resolved_at=? WHERE id=? AND status='pending'", (decision,actor,reason,now(),item_id)).rowcount
            if not n: raise ValueError('Item missing or already resolved')
            self.audit(db,'queue-'+decision,actor,{'id':item_id,'reason':reason})

    def publication(self) -> dict:
        with self.connect() as db:
            meta={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
            meta.update(sources=[json.loads(r['payload']) for r in db.execute("SELECT payload FROM sources WHERE kind='page' ORDER BY id")],feeds=[json.loads(r['payload']) for r in db.execute("SELECT payload FROM sources WHERE kind='feed' ORDER BY id")])
            for key,kind in TABLES.items():
                rows=db.execute('SELECT payload FROM accepted_claims WHERE kind=? ORDER BY id',(kind,)).fetchall()
                meta[key]=[{**json.loads(r['payload']),'review_status':'accepted'} for r in rows]
            # Candidates are disclosed, but never treated as accepted sites or estimates.
            meta['discoveries']=[{**json.loads(r['payload']),'review_status':'candidate'} for r in db.execute("SELECT c.payload FROM claims c LEFT JOIN current_decisions d ON d.claim_id=c.id WHERE c.kind='discovery' AND (d.decision IS NULL OR d.decision!='rejected') ORDER BY c.id")]
            latest=db.execute("SELECT MAX(created_at) FROM decisions WHERE actor!='checked-in-publication'").fetchone()[0]
            if latest: meta['published_at']=latest[:10]
            meta['publication_hash']=digest(meta)
            return meta

    def queue(self, limit: int=100, offset: int=0) -> dict:
        with self.connect() as db:
            total=db.execute("SELECT count(*) FROM review_queue WHERE status='pending'").fetchone()[0]
            rows=[{**dict(r),'payload':json.loads(r['payload'])} for r in db.execute("SELECT * FROM review_queue WHERE status='pending' ORDER BY created_at DESC,id LIMIT ? OFFSET ?", (limit,offset))]
            return {'items':rows,'total':total,'limit':limit,'offset':offset,'next_offset':offset+len(rows) if offset+len(rows)<total else None}

    def status(self, background: bool=False) -> dict:
        with self.connect() as db:
            counts={name:db.execute(sql).fetchone()[0] for name,sql in {
                'sites':'SELECT COUNT(*) FROM sites','sources':'SELECT COUNT(*) FROM sources',
                'source_versions':'SELECT COUNT(*) FROM source_versions','pending_review':"SELECT COUNT(*) FROM review_queue WHERE status='pending'",
                'accepted_observations':"SELECT COUNT(*) FROM accepted_claims WHERE kind='observation'",
                'fetch_attempts':'SELECT COUNT(*) FROM fetch_events'}.items()}
            jobs=[dict(r) for r in db.execute('SELECT source_id,next_fetch_at,last_status,last_success,last_error,failures FROM jobs ORDER BY source_id')]
            return {'schema_version':1,'background_refresh':background,'checked_at':now(),'counts':counts,'jobs':jobs,'publication_date':self.publication().get('published_at'),'policy':'Acquisition is not publication. Changed sources require an explicit editorial decision.'}

    def search(self, query: str, limit: int=30) -> list[dict]:
        words=query.split()[:12]
        if not words:return []
        expression=' AND '.join('"'+w.replace('"','""')+'"*' for w in words)
        with self.connect() as db:
            return [json.loads(r['payload']) for r in db.execute('SELECT s.payload FROM site_search f JOIN sites s ON s.id=f.id WHERE site_search MATCH ? ORDER BY rank LIMIT ?', (expression,limit))]

    def backup(self, target: Path) -> None:
        target.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db, sqlite3.connect(target) as dest: db.backup(dest)
