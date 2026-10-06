"""Bounded, conditional acquisition of editor-registered public sources.

No extracted sentence is automatically promoted into a site or numerical claim.
The raw and semantic hashes, HTTP outcome and editorial queue are independent.
"""
from __future__ import annotations
import hashlib
import ipaddress
import re
import secrets
import socket
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from .store import Store, canonical, digest, now

USER_AGENT = 'ComputeAtlasSourceMonitor/1.0 (+https://github.com/Untitled1-Agent/compute-atlas; evidence review, daily checks)'
MAX_BYTES = 8 * 1024 * 1024
LEASE_SECONDS = 180

class AcquisitionError(Exception):
    def __init__(self, message: str, status: int | None = None, retry_after: float = 0):
        super().__init__(message)
        self.status, self.retry_after = status, retry_after


def safe_url(url: str, allowed_hosts: set[str], resolve: bool = True) -> str:
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise AcquisitionError('Only public HTTPS source URLs on port 443 are permitted')
    host = p.hostname.lower()
    if host not in allowed_hosts or host in {'localhost'} or host.endswith(('.local', '.internal')):
        raise AcquisitionError('Source or redirect host is not editor-registered')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise AcquisitionError('Private, reserved and loopback addresses are forbidden')
    if resolve:
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except OSError as e:
            raise AcquisitionError('DNS resolution failed') from e
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise AcquisitionError('Source resolves to a non-public address')
    return urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, ''))


def semantic_text(raw: bytes, content_type: str) -> str:
    """Prefer article content to reduce navigation / tracking-only change alerts."""
    if 'html' in content_type:
        soup = BeautifulSoup(raw, 'html.parser')
        for node in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'form']):
            node.decompose()
        article = soup.find('article') or soup.find('main') or soup
        return re.sub(r'\s+', ' ', article.get_text(' ', strip=True)).strip()
    if any(x in content_type for x in ('xml', 'text', 'json')):
        return re.sub(r'\s+', ' ', raw.decode('utf-8', 'replace')).strip()
    # Do not pretend a binary PDF is extracted or reviewed.
    return hashlib.sha256(raw).hexdigest()


def feed_items(raw: bytes, source_url: str) -> list[dict]:
    root = ElementTree.fromstring(raw)
    items = []
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] not in ('item', 'entry'):
            continue
        values = {}; links = []
        for child in element:
            tag = child.tag.rsplit('}', 1)[-1]
            if tag == 'link':
                if child.attrib.get('rel', 'alternate') == 'alternate':
                    links.append(child.attrib.get('href') or child.text or '')
            else:
                values[tag] = ''.join(child.itertext()).strip()
        url = urljoin(source_url, next((v for v in links if v.strip()), ''))
        p = urlsplit(url)
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            continue
        items.append({'title': values.get('title', 'Untitled source item')[:500], 'url': urlunsplit((p.scheme,p.netloc,p.path,p.query,'')), 'published_at': values.get('published') or values.get('pubDate') or values.get('updated'), 'note': 'Feed discovery only. URL, relevance, identity and claims require review; this URL is not automatically fetched.'})
        if len(items) >= 100: break
    return items


def delay_seconds(value: str | None) -> float:
    if not value: return 0
    try: return min(7 * 86400, max(0, float(value)))
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            return min(7 * 86400, max(0, (parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError): return 0


class Monitor:
    def __init__(self, store: Store, blob_dir: Path, client: httpx.Client | None = None, *, resolve_dns: bool = True, min_host_interval: float = 2):
        self.store, self.blob_dir = store, Path(blob_dir)
        self.blob_dir.mkdir(parents=True, exist_ok=True)
        self.client = client or httpx.Client(timeout=httpx.Timeout(25, connect=10), follow_redirects=False, trust_env=False, headers={'User-Agent': USER_AGENT})
        self.owns_client = client is None
        self.resolve_dns = resolve_dns
        self.min_host_interval = min_host_interval
        self.robots: dict[str, tuple[float, RobotFileParser | None]] = {}
        self.last_request: dict[str, float] = {}

    def close(self):
        if self.owns_client: self.client.close()

    def lease(self) -> dict | None:
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT j.*,s.url,s.kind,s.payload FROM jobs j JOIN sources s ON s.id=j.source_id WHERE next_fetch_at<=? AND (lease_until IS NULL OR lease_until<?) ORDER BY next_fetch_at,source_id LIMIT 1', (now(),now())).fetchone()
            if not row: return None
            token = secrets.token_hex(16)
            until = (datetime.now(timezone.utc)+timedelta(seconds=LEASE_SECONDS)).isoformat(timespec='seconds')
            db.execute('UPDATE jobs SET lease_token=?,lease_until=? WHERE source_id=?', (token,until,row['source_id']))
            return {**dict(row), 'lease_token':token}

    def _pace(self, host: str, delay: float = 0):
        wait = max(self.min_host_interval, delay)-(time.monotonic()-self.last_request.get(host, 0))
        if wait > 0: time.sleep(wait)
        self.last_request[host] = time.monotonic()

    def _get(self, url: str, hosts: set[str], headers: dict | None = None, *, robots: bool = False) -> tuple[int, dict, bytes, str]:
        for _ in range(5):
            url = safe_url(url, hosts, self.resolve_dns)
            host = urlsplit(url).hostname
            crawl_delay = 0
            if not robots:
                parser = self._robots(url, hosts)
                if parser:
                    if not parser.can_fetch('ComputeAtlasSourceMonitor', url): raise AcquisitionError('robots.txt disallows this source')
                    crawl_delay = parser.crawl_delay('ComputeAtlasSourceMonitor') or parser.crawl_delay('*') or 0
                    if crawl_delay > 60: raise AcquisitionError('robots crawl delay exceeds this bounded worker; use a slower registered schedule')
            self._pace(host, crawl_delay)
            with self.client.stream('GET', url, headers={'User-Agent':USER_AGENT, **(headers or {})}) as response:
                if response.status_code in (301,302,303,307,308):
                    location = response.headers.get('location')
                    if not location: raise AcquisitionError('Redirect has no location', response.status_code)
                    url = urljoin(url, location)
                    continue
                if response.status_code == 304: return 304, dict(response.headers), b'', url
                if response.status_code >= 400:
                    raise AcquisitionError(f'HTTP {response.status_code}', response.status_code, delay_seconds(response.headers.get('retry-after')))
                length = response.headers.get('content-length')
                if length and length.isdigit() and int(length) > MAX_BYTES: raise AcquisitionError('Response exceeds byte limit')
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES: raise AcquisitionError('Response exceeds decompressed byte limit')
                return response.status_code, dict(response.headers), bytes(body), url
        raise AcquisitionError('Redirect limit exceeded')

    def _robots(self, url: str, hosts: set[str]) -> RobotFileParser | None:
        p = urlsplit(url); origin = f'{p.scheme}://{p.netloc}'
        cached = self.robots.get(origin)
        if cached and time.monotonic()-cached[0] < 3600: return cached[1]
        try:
            _, _, raw, _ = self._get(origin+'/robots.txt',hosts,robots=True)
        except AcquisitionError as e:
            if e.status == 404:
                self.robots[origin] = (time.monotonic(), None); return None
            raise AcquisitionError('robots.txt unavailable; acquisition deferred',e.status,e.retry_after) from e
        parser = RobotFileParser(); parser.parse(raw.decode('utf-8','replace').splitlines())
        self.robots[origin] = (time.monotonic(), parser)
        return parser

    def run_once(self) -> bool:
        job = self.lease()
        if not job: return False
        import json
        source = json.loads(job['payload'])
        hosts = {urlsplit(job['url']).hostname.lower(), *[h.lower() for h in source.get('allowed_redirect_hosts',[])]}
        headers = {}
        if job['etag']: headers['If-None-Match'] = job['etag']
        if job['last_modified']: headers['If-Modified-Since'] = job['last_modified']
        try:
            status, response_headers, raw, final_url = self._get(job['url'],hosts,headers)
            self._success(job,status,response_headers,raw,final_url)
        except (AcquisitionError, httpx.HTTPError, OSError, ValueError, ParseError, DefusedXmlException) as e:
            self._failure(job,e)
        return True

    def _success(self, job, status, headers, raw, final_url):
        captured = now(); raw_hash = hashlib.sha256(raw).hexdigest()
        content_type = headers.get('content-type','application/octet-stream').split(';')[0].lower()
        if status != 304 and not raw: raise AcquisitionError('Empty source body')
        text = semantic_text(raw,content_type) if status != 304 else ''
        semantic_hash = hashlib.sha256(text.encode()).hexdigest()
        entries = feed_items(raw,final_url) if status != 304 and job['kind']=='feed' else []
        if status != 304:
            # Content-addressed raw snapshots stay local; never exposed by the web server.
            dest = self.blob_dir / raw_hash
            if not dest.exists():
                import os
                tmp = self.blob_dir / (raw_hash+'.'+secrets.token_hex(8)+'.tmp')
                try:
                    tmp.write_bytes(raw); os.replace(tmp,dest)
                finally:
                    tmp.unlink(missing_ok=True)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            live = db.execute('SELECT lease_token FROM jobs WHERE source_id=?',(job['source_id'],)).fetchone()
            if live['lease_token'] != job['lease_token']: return # A recovered worker owns the job now.
            # A representation may recur (A -> B -> A). Content-addressed versions
            # retain their *first* capture time; the event ledger records which
            # representation was most recently observed, including 304 responses.
            event = db.execute('SELECT id,version_id FROM fetch_events WHERE source_id=? AND version_id IS NOT NULL ORDER BY id DESC LIMIT 1',(job['source_id'],)).fetchone()
            previous = db.execute('SELECT * FROM source_versions WHERE id=?',(event['version_id'],)).fetchone() if event else None
            vid = previous['id'] if previous else None
            outcome = 'not-modified'
            if status == 304 and not previous: raise AcquisitionError('304 returned without a captured baseline',304)
            if status != 304:
                vid = 'v-'+digest([job['source_id'],raw_hash])[:32]
                db.execute('INSERT OR IGNORE INTO source_versions VALUES(?,?,?,?,?,?,?,?)',(vid,job['source_id'],raw_hash,semantic_hash,content_type,final_url,len(raw),captured))
                meaningful = previous is None or previous['semantic_sha256'] != semantic_hash
                outcome = 'baseline' if previous is None else ('changed' if meaningful else 'unchanged-content')
                if meaningful and job['kind'] in ('page','catalog-page'):
                    self.store.enqueue(db,job['source_id'],vid,outcome,{'title': json_title(job['payload']), 'url':final_url, 'note':'New captured baseline; not retroactive verification of historical claims.' if previous is None else 'Source content changed. Accepted claims remain unchanged until editorial review.', 'previous_version_id': previous['id'] if previous else None, 'sha256':raw_hash,'semantic_sha256':semantic_hash,'excerpt':text[:1200] if 'html' in content_type or content_type.startswith('text/') else 'Binary source retained; document extraction has not been performed.'},digest([job['source_id'],event['id'] if event else None,vid,outcome]))
                for item in entries:
                    self.store.enqueue(db,job['source_id'],vid,'discovery',item,digest([job['source_id'],item['url']]))
            db.execute('INSERT INTO fetch_events(source_id,version_id,status,outcome,attempted_at) VALUES(?,?,?,?,?)',(job['source_id'],vid,status,outcome,captured))
            next_time = (datetime.now(timezone.utc)+timedelta(hours=job['refresh_hours'])).isoformat(timespec='seconds')
            # A full representation replaces validators; missing validators must
            # not leak from an older body. A 304 revalidates the current body.
            etag = headers.get('etag',job['etag']) if status == 304 else headers.get('etag')
            modified = headers.get('last-modified',job['last_modified']) if status == 304 else headers.get('last-modified')
            db.execute('UPDATE jobs SET lease_token=NULL,lease_until=NULL,failures=0,last_status=?,last_success=?,last_error=NULL,next_fetch_at=?,etag=?,last_modified=? WHERE source_id=?',(status,captured,next_time,etag,modified,job['source_id']))

    def _failure(self, job, error):
        failures = job['failures']+1
        delay = max(getattr(error,'retry_after',0),min(86400,300*2**min(failures-1,8)))
        delay += secrets.randbelow(60)
        next_time = (datetime.now(timezone.utc)+timedelta(seconds=delay)).isoformat(timespec='seconds')
        message = str(error)[:500]; status=getattr(error,'status',None)
        with self.store.connect() as db:
            changed = db.execute('UPDATE jobs SET lease_token=NULL,lease_until=NULL,failures=?,last_status=?,last_error=?,next_fetch_at=? WHERE source_id=? AND lease_token=?',(failures,status,message,next_time,job['source_id'],job['lease_token'])).rowcount
            if changed: db.execute('INSERT INTO fetch_events(source_id,status,outcome,error,attempted_at) VALUES(?,?,?,?,?)',(job['source_id'],status,'deferred',message,now()))


def json_title(payload: str) -> str:
    import json
    source=json.loads(payload)
    return source.get('title') or source.get('publisher','Source capture')
