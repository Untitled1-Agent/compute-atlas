"""Capture an operator's complete published directory, never a guessed facility census.

The registered URL is fixed. Robots, redirects, DNS and byte limits reuse the source
monitor. Output is a review candidate; this command cannot update app publications.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.acquire import Monitor

URL = 'https://docs.equinix.com/colocation/availability/'
SOURCE_ID = 'DIR-EQUINIX-AVAILABILITY'
CODE = re.compile(r'[A-Z]{2}[0-9]{1,3}x?', re.I)


def parse_directory(raw: bytes) -> list[dict]:
    """Read every directory table; abort on schema drift instead of dropping rows."""
    soup = BeautifulSoup(raw, 'html.parser')
    main = soup.find('main')
    if main is None:
        raise ValueError('Operator page has no main document')
    region = country = None
    records, seen, tables = [], set(), 0
    for element in main.find_all(['h2', 'h3', 'table']):
        text = element.get_text(' ', strip=True).replace('\u200b', '').strip()
        if element.name == 'h2':
            region, country = text, None
        elif element.name == 'h3':
            country = text
        else:
            if region not in {'Americas', 'APAC', 'EMEA'} or not country:
                raise ValueError('Directory table has missing or unknown region/country')
            rows = element.find_all('tr')
            header = [c.get_text(' ', strip=True).replace('\xa0', ' ') for c in rows[0].find_all(['th', 'td'])] if rows else []
            if header != ['Metro', 'IBX Type', 'IBX Name', 'Coverage Type']:
                raise ValueError('Directory table header changed')
            tables += 1
            if len(rows) < 2:
                raise ValueError('Empty directory table')
            for row in rows[1:]:
                cells = [c.get_text(' ', strip=True) for c in row.find_all(['td', 'th'])]
                if len(cells) != 4 or not all(cells[:3]) or not CODE.fullmatch(cells[2]):
                    raise ValueError('Malformed directory row')
                metro, facility_type, code, coverage = cells
                code = code.upper()
                if code in seen:
                    raise ValueError('Duplicate facility code: ' + code)
                seen.add(code)
                records.append({'id': 'equinix-' + code.lower(), 'operator': 'Equinix',
                                'code': code, 'name': 'Equinix ' + code,
                                'source_region': region, 'source_country': country,
                                'metro': metro, 'facility_type': facility_type,
                                'service_coverage': coverage or None,
                                'source_id': SOURCE_ID, 'source_url': URL,
                                'coordinates': None, 'it_mw': None})
    if tables == 0 or not records:
        raise ValueError('No operator directory rows found')
    return sorted(records, key=lambda r: (r['source_region'], r['source_country'], r['code']))


def capture(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    monitor = Monitor(None, output / 'raw', min_host_interval=2)
    try:
        status, headers, raw, final_url = monitor._get(URL, {'docs.equinix.com'})
        if status != 200 or 'html' not in headers.get('content-type', ''):
            raise ValueError('Directory response is not successful HTML')
        records = parse_directory(raw)
        # A large unexpected shrink is a quarantine, never an empty publication.
        if len(records) < 100 or len(records) > 2000:
            raise ValueError('Directory row count outside review bounds')
        now = datetime.now(timezone.utc).isoformat()
        data = {'schema_version': 1, 'id': SOURCE_ID, 'publisher': 'Equinix',
                'url': URL, 'final_url': final_url, 'title': 'Equinix Colocation Availability',
                'captured_at': now, 'published_at': None, 'review': None,
                'source_sha256': hashlib.sha256(raw).hexdigest(), 'parser_version': 1,
                'count_boundary': 'Publisher-listed facility codes; not unique buildings, available inventory or a global census.',
                'service_boundary': 'Coverage describes on-site service coverage, not utilization or available capacity.',
                'rights': 'Extracted factual directory entries. Source publication rights remain with Equinix. Independent from the ODbL map catalog.',
                'counts': {'records': len(records),
                           'countries': dict(Counter(r['source_country'] for r in records)),
                           'regions': dict(Counter(r['source_region'] for r in records))},
                'records': records}
        (output / 'candidate.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
        # Hash the exact source response, but do not distribute the publisher's full HTML.
        print(json.dumps({k:v for k,v in data.items() if k != 'records'}, indent=2))
        return data
    except Exception as exc:
        (output / 'failure.json').write_text(json.dumps({'at': datetime.now(timezone.utc).isoformat(),
           'source_url': URL, 'error': str(exc), 'publication_unchanged': True}, indent=2))
        raise
    finally:
        monitor.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    capture(parser.parse_args().output)
