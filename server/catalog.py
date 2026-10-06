"""Versioned, separately licensed geographic catalog. No automatic fact promotion."""
from __future__ import annotations
import hashlib, json, math, sqlite3
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1 or data.get('license') != 'ODbL-1.0':
        raise ValueError('Unsupported catalog schema or license')
    rows = data.get('records'); seen = set()
    if not isinstance(rows, list) or not rows or len(rows) > 100000: raise ValueError('Invalid catalog size')
    for r in rows:
        if not isinstance(r, dict): raise ValueError('Invalid catalog record')
        rid = r.get('id')
        if not isinstance(rid, str) or not rid.startswith(('osm-node-','osm-way-','osm-relation-')) or rid in seen: raise ValueError('Duplicate or invalid catalog identity')
        seen.add(rid)
        if not all(type(r.get(k)) in (float,int) and math.isfinite(r[k]) for k in ('lat','lon')) or not -90 <= r['lat'] <= 90 or not -180 <= r['lon'] <= 180: raise ValueError('Invalid catalog coordinate')
        if r.get('it_mw') is not None: raise ValueError('Map tags cannot become IT power')
        if r.get('kind') not in ('point','building','campus','area'): raise ValueError('Invalid feature kind')
        if not all(isinstance(r.get(k),str) for k in ('name','country','continent','source_url')):raise ValueError('Invalid catalog strings')
        typ, ident = rid[4:].rsplit('-',1)
        if not ident.isdigit() or r['source_url'] != f'https://www.openstreetmap.org/{typ}/{ident}':raise ValueError('Invalid source identity URL')
        height = r.get('height_m')
        if height is not None and (type(height) not in (float,int) or not math.isfinite(height) or not 0 < height <= 500 or r['kind']!='building'):raise ValueError('Invalid mapped height')
        g=r.get('geometry')
        if g is not None:
            if not isinstance(g,dict) or g.get('type')!='MultiPolygon' or not isinstance(g.get('coordinates'),list) or not g['coordinates']:raise ValueError('Invalid geometry')
            for poly in g['coordinates']:
                if not isinstance(poly,list) or not poly:raise ValueError('Invalid polygon')
                for ring in poly:
                    if not isinstance(ring,list) or len(ring)<4 or len(ring)>20000 or ring[0]!=ring[-1]:raise ValueError('Unclosed source geometry')
                    for p in ring:
                        if not isinstance(p,list) or len(p)!=2 or not all(type(v) in (float,int) and math.isfinite(v) for v in p) or not -180<=p[0]<=180 or not -90<=p[1]<=90:raise ValueError('Invalid geometry coordinate')
    if data.get('counts',{}).get('features') != len(rows):raise ValueError('Catalog denominator mismatch')
    for field, label in [('country','countries'),('continent','continents'),('kind','kinds'),('lifecycle','lifecycle')]:
        if data.get('counts',{}).get(label) != dict(Counter(r[field] for r in rows)):
            raise ValueError('Catalog classification counts do not match records')
    try:
        if datetime.fromisoformat(data['captured_at'].replace('Z','+00:00')).tzinfo is None:raise ValueError('Capture date requires timezone')
    except (KeyError,TypeError,AttributeError) as error:raise ValueError('Invalid capture date') from error
    # JSON finite validation protects fields not used for indexing as well.
    canonical(data)
    return data


class CatalogStore:
    def __init__(self, path: Path):
        self.path = path
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS catalog_snapshots(hash TEXT PRIMARY KEY, captured_at TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS catalog_records(snapshot TEXT NOT NULL, id TEXT NOT NULL, name TEXT NOT NULL, country TEXT NOT NULL, continent TEXT NOT NULL, kind TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, search_text TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(snapshot,id));
            CREATE INDEX IF NOT EXISTS catalog_geography ON catalog_records(snapshot,continent,country,kind);
            CREATE INDEX IF NOT EXISTS catalog_position ON catalog_records(snapshot,lat,lon);
            CREATE TABLE IF NOT EXISTS catalog_current(slot INTEGER PRIMARY KEY CHECK(slot=1), hash TEXT NOT NULL REFERENCES catalog_snapshots(hash));
            CREATE TABLE IF NOT EXISTS catalog_decisions(id INTEGER PRIMARY KEY, hash TEXT NOT NULL REFERENCES catalog_snapshots(hash), action TEXT NOT NULL, actor TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS catalog_immutable BEFORE UPDATE ON catalog_snapshots BEGIN SELECT RAISE(ABORT,'Catalog snapshots are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS catalog_no_delete BEFORE DELETE ON catalog_snapshots BEGIN SELECT RAISE(ABORT,'Catalog snapshots are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS catalog_records_immutable BEFORE UPDATE ON catalog_records BEGIN SELECT RAISE(ABORT,'Catalog records are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS catalog_records_no_delete BEFORE DELETE ON catalog_records BEGIN SELECT RAISE(ABORT,'Catalog records are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS catalog_decisions_immutable BEFORE UPDATE ON catalog_decisions BEGIN SELECT RAISE(ABORT,'Catalog decisions are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS catalog_decisions_no_delete BEFORE DELETE ON catalog_decisions BEGIN SELECT RAISE(ABORT,'Catalog decisions are immutable'); END;
            ''')

    def connect(self):
        db=sqlite3.connect(self.path,timeout=20);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');return db

    def stage(self, data):
        validate(data); payload=canonical(data); key=hashlib.sha256(payload.encode()).hexdigest()
        now=datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            added=db.execute('INSERT OR IGNORE INTO catalog_snapshots VALUES(?,?,?,?)',(key,data['captured_at'],payload,now)).rowcount
            if added:
                db.executemany('INSERT INTO catalog_records VALUES(?,?,?,?,?,?,?,?,?,?)',[(key,r['id'],r['name'],r['country'],r['continent'],r['kind'],r['lat'],r['lon'],' '.join(str(r.get(k) or '') for k in ('id','name','operator','city','address','country')).casefold(),canonical(r)) for r in data['records']])
                db.execute('INSERT INTO catalog_decisions(hash,action,actor,note,created_at) VALUES(?,?,?,?,?)',(key,'staged','acquisition','Awaiting explicit catalog review; no power facts created.',now))
        return key

    def accept(self, key, *, actor, note, expected_current):
        if not actor.strip() or not note.strip():raise ValueError('Named reviewer and review note required')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT hash FROM catalog_current WHERE slot=1').fetchone()
            if (current['hash'] if current else None)!=expected_current:raise ValueError('Publication changed; re-review the current snapshot')
            if not db.execute('SELECT 1 FROM catalog_snapshots WHERE hash=?',(key,)).fetchone():raise ValueError('Unknown staged snapshot')
            db.execute('INSERT INTO catalog_current VALUES(1,?) ON CONFLICT(slot) DO UPDATE SET hash=excluded.hash',(key,))
            db.execute('INSERT INTO catalog_decisions(hash,action,actor,note,created_at) VALUES(?,?,?,?,?)',(key,'accepted',actor,note,datetime.now(timezone.utc).isoformat()))

    def seed(self, root):
        file=Path(root)/'data/catalog/osm.json'
        if not file.exists():return
        key=self.stage(json.loads(file.read_text()))
        if self.current() is None:
            try:self.accept(key,actor='checked-in publication',note='Initial reviewed ODbL map-feature snapshot. Not a capacity review.',expected_current=None)
            except ValueError:
                if self.current() is None:raise

    def register_review_sources(self, root):
        path=Path(root)/'data/catalog/reviews.json'
        if not path.exists():return
        from .acquire import safe_url
        now=datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            for r in json.loads(path.read_text())['reviews']:
                safe_url(r['url'],{'www.equinix.com'},resolve=False)
                old=db.execute('SELECT url FROM sources WHERE id=?',(r['id'],)).fetchone()
                if old and old['url']!=r['url']:raise ValueError('Catalog source identity changed URL')
                source={**r,'retrieved_at':r['reviewed_at'],'refresh_hours':168,'rights':'Linked factual specifications; source publication rights remain with publisher.'}
                db.execute('INSERT INTO sources VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(r['id'],r['url'],r['publisher'],'catalog-page',canonical(source)))
                db.execute('INSERT OR IGNORE INTO jobs(source_id,next_fetch_at,refresh_hours) VALUES(?,?,?)',(r['id'],now,168))

    def current(self):
        with self.connect() as db:
            row=db.execute('SELECT hash FROM catalog_current WHERE slot=1').fetchone()
            return row['hash'] if row else None

    def publication(self):
        with self.connect() as db:
            row=db.execute('SELECT s.payload FROM catalog_snapshots s JOIN catalog_current c ON s.hash=c.hash').fetchone()
        return json.loads(row['payload']) if row else None

    def page(self, q='', country=None, continent=None, kind=None, bbox=None, limit=30, offset=0):
        if not 1<=limit<=100 or offset<0:raise ValueError('Invalid page')
        key=self.current();where=['snapshot=?'];args=[key or '']
        for field,value in [('country',country),('continent',continent),('kind',kind)]:
            if value:where.append(field+'=?');args.append(value)
        if q:where.append('instr(search_text,?)>0');args.append(q.casefold())
        if bbox is not None:
            if len(bbox)!=4 or not all(math.isfinite(x) for x in bbox):raise ValueError('Invalid bounds')
            west,south,east,north=bbox
            if not -180<=west<=180 or not -180<=east<=180 or not -90<=south<=north<=90:raise ValueError('Invalid bounds')
            where.append('lat BETWEEN ? AND ?');args.extend([south,north])
            where.append('(lon>=? OR lon<=?)' if west>east else '(lon>=? AND lon<=?)');args.extend([west,east])
        clause=' AND '.join(where)
        with self.connect() as db:
            total=db.execute('SELECT COUNT(*) FROM catalog_records WHERE '+clause,args).fetchone()[0]
            rows=db.execute('SELECT payload FROM catalog_records WHERE '+clause+' ORDER BY name,id LIMIT ? OFFSET ?',[*args,limit,offset]).fetchall()
        return {'snapshot':key,'total':total,'limit':limit,'offset':offset,'items':[json.loads(r['payload']) for r in rows],'count_boundary':'OSM map features; not unique facilities or operating capacity'}

    def feature(self, ident):
        with self.connect() as db:row=db.execute('SELECT payload FROM catalog_records WHERE snapshot=? AND id=?',(self.current() or '',ident)).fetchone()
        return json.loads(row['payload']) if row else None

    def status(self):
        with self.connect() as db:
            rows=db.execute('SELECT s.hash,s.captured_at,s.created_at,(SELECT count(*) FROM catalog_records r WHERE r.snapshot=s.hash) AS features, (s.hash=COALESCE((SELECT hash FROM catalog_current),\'\')) AS current FROM catalog_snapshots s ORDER BY s.created_at DESC').fetchall()
            events=db.execute('SELECT * FROM catalog_decisions ORDER BY id DESC LIMIT 50').fetchall()
        return {'current':self.current(),'snapshots':[dict(r) for r in rows],'decisions':[dict(r) for r in events]}
