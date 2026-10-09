"""Independent, versioned primary directories; map matches are proposals, never facts."""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from .catalog import canonical
from . import digital_realty

DIRECTORIES = {'equinix': ('DIR-EQUINIX-AVAILABILITY', 'data/catalog/operator-directory.json'),
               'digital-realty': (digital_realty.SOURCE_ID, digital_realty.FILE)}

SOURCE_ID = 'DIR-EQUINIX-AVAILABILITY'
SOURCE_URL = 'https://docs.equinix.com/colocation/availability/'
ROW_KEYS = {'id','operator','code','name','source_region','source_country','metro','facility_type',
            'service_coverage','source_id','source_url','coordinates','it_mw'}


def validate_directory(data):
    if isinstance(data,dict) and data.get('id') == digital_realty.SOURCE_ID:
        return digital_realty.validate(data)
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1 or data.get('id') != SOURCE_ID:
        raise ValueError('Unsupported operator directory')
    if data.get('url') != SOURCE_URL or data.get('final_url') != SOURCE_URL or data.get('publisher') != 'Equinix':
        raise ValueError('Unregistered primary directory source')
    if not re.fullmatch(r'[0-9a-f]{64}', str(data.get('source_sha256', ''))):
        raise ValueError('Missing source response identity')
    try:
        if datetime.fromisoformat(data['captured_at'].replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Capture requires timezone')
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Invalid capture date') from error
    for key in ('title', 'count_boundary', 'service_boundary', 'rights'):
        if not isinstance(data.get(key), str) or not data[key].strip() or len(data[key]) > 2000:
            raise ValueError('Invalid directory metadata')
    if data.get('published_at') is not None or data.get('parser_version') != 1:
        raise ValueError('Unsupported source publication metadata')
    rows = data.get('records')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 2000:
        raise ValueError('Invalid directory size')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError('Unknown directory record fields')
        for key in ROW_KEYS - {'service_coverage', 'coordinates', 'it_mw'}:
            if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 500:
                raise ValueError('Invalid directory text')
        code = row['code']
        if not re.fullmatch(r'[A-Z]{2}[0-9]{1,3}X?', code) or row['id'] != 'equinix-'+code.lower() or code in seen:
            raise ValueError('Invalid or duplicate operator code')
        seen.add(code)
        if row['source_id'] != SOURCE_ID or row['source_url'] != SOURCE_URL or row['operator'] != 'Equinix' or row['name'] != 'Equinix '+code:
            raise ValueError('Directory identity/source mismatch')
        if row['source_region'] not in {'EMEA','APAC','Americas'}:
            raise ValueError('Unknown source region')
        if row['coordinates'] is not None or row['it_mw'] is not None:
            raise ValueError('Directory cannot certify coordinates or IT capacity')
        if row['service_coverage'] is not None and (not isinstance(row['service_coverage'], str) or not row['service_coverage'].strip() or len(row['service_coverage']) > 500):
            raise ValueError('Invalid service coverage')
    counts = {'records':len(rows), 'countries':dict(Counter(r['source_country'] for r in rows)),
              'regions':dict(Counter(r['source_region'] for r in rows))}
    if data.get('counts') != counts:
        raise ValueError('Directory denominator mismatch')
    review = data.get('review')
    if review is not None:
        if not isinstance(review, dict) or not all(isinstance(review.get(k), str) and review[k].strip() for k in ('actor','note','reviewed_at')):
            raise ValueError('Invalid directory editorial review')
        if datetime.fromisoformat(review['reviewed_at'].replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Review requires timezone')
    canonical(data)
    return data


def proposed_matches(row, features):
    """Exact operator, code and country candidates. No fuzzy automatic merges."""
    country = {'USA':'United States','UK':'United Kingdom', 'UAE':'United Arab Emirates'}.get(row['source_country'],row['source_country'])
    token = re.compile(r'(?<![A-Z0-9])'+re.escape(row['code'])+r'(?![A-Z0-9.])', re.I)
    return sorted(r['id'] for r in features if r['country'] == country
                  and re.search(r'\bequinix\b', str(r.get('operator') or '')+' '+r['name'], re.I)
                  and token.search(r['name']))


class DirectoryStore:
    def __init__(self, path: Path, publisher='equinix'):
        if publisher not in DIRECTORIES: raise ValueError('Unknown directory publisher')
        self.publisher = publisher
        self.source_id, self.seed_file = DIRECTORIES[publisher]
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS directory_snapshots(hash TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS directory_records(snapshot TEXT NOT NULL REFERENCES directory_snapshots(hash),id TEXT NOT NULL,country TEXT NOT NULL,region TEXT NOT NULL,search_text TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(snapshot,id));
            CREATE INDEX IF NOT EXISTS directory_geography ON directory_records(snapshot,country,region);
            CREATE TABLE IF NOT EXISTS directory_current(slot INTEGER PRIMARY KEY CHECK(slot=1),hash TEXT NOT NULL REFERENCES directory_snapshots(hash));
            CREATE TABLE IF NOT EXISTS directory_heads(source_id TEXT PRIMARY KEY,hash TEXT NOT NULL REFERENCES directory_snapshots(hash));
            INSERT OR IGNORE INTO directory_heads SELECT 'DIR-EQUINIX-AVAILABILITY',hash FROM directory_current WHERE slot=1;
            CREATE TABLE IF NOT EXISTS directory_decisions(id INTEGER PRIMARY KEY,hash TEXT NOT NULL REFERENCES directory_snapshots(hash),action TEXT NOT NULL,actor TEXT NOT NULL,note TEXT NOT NULL,created_at TEXT NOT NULL);
            ''')
            for table in ('directory_snapshots','directory_records','directory_decisions'):
                for action in ('UPDATE','DELETE'):
                    db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Directory history is immutable'); END")

    def connect(self):
        db=sqlite3.connect(self.path,timeout=20);db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def current(self):
        with self.connect() as db:
            r=db.execute('SELECT hash FROM directory_heads WHERE source_id=?',(self.source_id,)).fetchone()
            return r['hash'] if r else None

    def stage(self, data):
        validate_directory(data)
        if data['id'] != self.source_id: raise ValueError('Cross-publisher directory stage')
        payload=canonical(data);key=hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('INSERT OR IGNORE INTO directory_snapshots VALUES(?,?,?)',(key,payload,datetime.now(timezone.utc).isoformat())).rowcount:
                db.executemany('INSERT INTO directory_records VALUES(?,?,?,?,?,?)',[(key,r['id'],r['source_country'] or 'Not specified',r['source_region'],' '.join([r['name'],r['metro'],r['source_country'] or '']).casefold(),canonical(r)) for r in data['records']])
                db.execute('INSERT INTO directory_decisions(hash,action,actor,note,created_at) VALUES(?,?,?,?,?)',(key,'staged','acquisition','Awaiting review; no map identity or capacity established.',datetime.now(timezone.utc).isoformat()))
        return key

    def accept(self,key,*,actor,note,expected_current):
        if not isinstance(actor,str) or not actor.strip() or not isinstance(note,str) or not note.strip():
            raise ValueError('Named reviewer and reason required')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute('SELECT hash FROM directory_heads WHERE source_id=?',(self.source_id,)).fetchone()
            if (r['hash'] if r else None)!=expected_current:
                raise ValueError('Publication changed; re-review current directory')
            snapshot = db.execute('SELECT payload FROM directory_snapshots WHERE hash=?',(key,)).fetchone()
            if snapshot is None:
                raise ValueError('Unknown directory snapshot')
            if json.loads(snapshot['payload'])['id'] != self.source_id: raise ValueError('Cross-publisher directory acceptance')
            db.execute('INSERT INTO directory_heads VALUES(?,?) ON CONFLICT(source_id) DO UPDATE SET hash=excluded.hash',(self.source_id,key))
            if self.publisher == 'equinix':
                db.execute('INSERT INTO directory_current VALUES(1,?) ON CONFLICT(slot) DO UPDATE SET hash=excluded.hash',(key,))
            db.execute('INSERT INTO directory_decisions(hash,action,actor,note,created_at) VALUES(?,?,?,?,?)',(key,'accepted',actor,note,datetime.now(timezone.utc).isoformat()))

    def publication(self):
        with self.connect() as db:
            r=db.execute('SELECT s.payload,s.hash FROM directory_snapshots s JOIN directory_heads c ON s.hash=c.hash WHERE c.source_id=?',(self.source_id,)).fetchone()
            if r is None:return None
            data=json.loads(r['payload'])
            # Acquisition candidates carry no review. The accepted publication exposes
            # the actual editorial decision without mutating the captured snapshot.
            if data.get('review') is None:
                event=db.execute("SELECT actor,note,created_at FROM directory_decisions WHERE hash=? AND action='accepted' ORDER BY id DESC LIMIT 1",(r['hash'],)).fetchone()
                data['review']={'actor':event['actor'],'note':event['note'],'reviewed_at':event['created_at']}
            return data

    def page(self, q='', country=None, region=None, limit=30, offset=0):
        if not 1<=limit<=100 or offset<0: raise ValueError('Invalid directory page')
        where=['snapshot=?']; args=[self.current() or '']
        for field,value in [('country',country),('region',region)]:
            if value:where.append(field+'=?');args.append(value)
        if q:where.append('instr(search_text,?)>0');args.append(q.casefold())
        clause=' AND '.join(where)
        with self.connect() as db:
            total=db.execute('SELECT count(*) FROM directory_records WHERE '+clause,args).fetchone()[0]
            rows=db.execute('SELECT payload FROM directory_records WHERE '+clause+' ORDER BY id LIMIT ? OFFSET ?',[*args,limit,offset]).fetchall()
        return {'snapshot':args[0] or None,'items':[json.loads(r['payload']) for r in rows], 'total':total,'limit':limit,'offset':offset}

    def status(self):
        with self.connect() as db:
            events=[dict(r) for r in db.execute("SELECT d.* FROM directory_decisions d JOIN directory_snapshots s ON s.hash=d.hash WHERE json_extract(s.payload,'$.id')=? ORDER BY d.id DESC LIMIT 50",(self.source_id,))]
        return {'current':self.current(),'decisions':events,'boundary':'Directory codes and proposed map matches are not capacity facts.'}

    def seed(self, root):
        file=Path(root)/self.seed_file
        if not file.exists():return
        data=validate_directory(json.loads(file.read_text()))
        if not data.get('review'):raise ValueError('Checked-in directory requires editorial review')
        key=self.stage(data)
        if self.current() is None:
            try:self.accept(key,actor=data['review']['actor'],note=data['review']['note'],expected_current=None)
            except ValueError:
                if self.current() is None:raise
        # The ordinary source monitor captures changes for review, not auto publication.
        with self.connect() as db:
            old=db.execute('SELECT url FROM sources WHERE id=?',(self.source_id,)).fetchone()
            if old and old['url']!=data['url']:raise ValueError('Registered directory URL changed')
            source={'id':self.source_id,'url':data['url'],'publisher':data['publisher'],'title':data['title'],
                    'retrieved_at':data['captured_at'],'refresh_hours':168,'rights':data['rights']}
            db.execute('INSERT INTO sources VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(self.source_id,data['url'],data['publisher'],'page',canonical(source)))
            db.execute('INSERT OR IGNORE INTO jobs(source_id,next_fetch_at,refresh_hours) VALUES(?,?,?)',(self.source_id,datetime.now(timezone.utc).isoformat(),168))
