"""Source-established place names are not surveyed coordinates.

Identity facts use the existing immutable claim/decision ledger. This module
never writes the archive, relocates markers, or merges sites by proximity.
"""
from __future__ import annotations
import json
from datetime import date

POLICY = ('Source-established identities and localities are separate from historical '
          'map anchors. Matching anchors do not establish a common campus. No surveyed '
          'coordinates, parcel boundaries, building geometry or capacity total is supplied.')
PRECISIONS = {'municipality', 'county_or_parish', 'region', 'country'}


def validate_identity_claim(db, kind: str, claim: dict) -> None:
    if 'identity' not in claim:
        return
    identity = claim['identity']
    fields = {'canonical_name', 'place', 'place_precision', 'project_scope',
              'coordinate_evidence', 'related_sites'}
    if kind != 'fact' or not isinstance(identity, dict) or set(identity) != fields:
        raise ValueError('Identity must be a typed fact with the exact supported fields')
    for key in ('canonical_name', 'place'):
        if not isinstance(identity[key], str) or not identity[key].strip() or len(identity[key]) > 400:
            raise ValueError('Identity name and place must be bounded nonempty text')
    if (not isinstance(identity['place_precision'], str) or identity['place_precision'] not in PRECISIONS
            or identity['project_scope'] != 'campus'):
        raise ValueError('Unsupported identity precision or project scope')
    if identity['coordinate_evidence'] != 'not_established':
        raise ValueError('Locality review cannot certify coordinates or geometry')
    for key in ('reviewed_at', 'as_of'):
        try:
            value = claim[key]
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise ValueError('Identity requires explicit ISO reporting and review dates') from None
    if claim['reviewed_at'] < claim['as_of']:
        raise ValueError('Identity review cannot predate the reporting date')
    links = identity['related_sites']
    if not isinstance(links, list) or len(links) > 20:
        raise ValueError('Related sites must be a bounded list')
    seen = set()
    for link in links:
        if not isinstance(link, dict) or set(link) != {'site_id', 'relation', 'source_id', 'note'}:
            raise ValueError('Each identity relationship needs its own source and note')
        if any(not isinstance(link[key], str) or not link[key].strip() for key in link):
            raise ValueError('Identity relationship fields must be nonempty text')
        sid = link['site_id']
        if sid == claim.get('site_id') or sid in seen or not db.execute('SELECT 1 FROM sites WHERE id=?', (sid,)).fetchone():
            raise ValueError('Related site must be a distinct, existing, unique record')
        if link['relation'] != 'adjacent_project' or len(link['note']) > 2000:
            raise ValueError('Unsupported identity relationship')
        if not db.execute('SELECT 1 FROM sources WHERE id=?', (link['source_id'],)).fetchone():
            raise ValueError('Unknown identity relationship source')
        seen.add(sid)


def identity_document(store, site_id: str) -> dict | None:
    """One consistent read; pending/rejected/superseded facts cannot escape."""
    with store.connect() as db:
        db.execute('BEGIN')
        row = db.execute('SELECT payload FROM sites WHERE id=?', (site_id,)).fetchone()
        if row is None:
            return None
        archive = json.loads(row['payload'])
        claims = [dict(json.loads(r['payload']), review_status='accepted') for r in db.execute(
            "SELECT payload FROM accepted_claims WHERE kind='fact' AND site_id=? "
            "AND json_type(payload,'$.identity')='object' ORDER BY id", (site_id,))]
        source_ids = {c['source_id'] for c in claims}
        source_ids.update(link['source_id'] for c in claims for link in c['identity']['related_sites'])
        sources = [json.loads(r['payload']) for sid in sorted(source_ids) for r in db.execute(
            'SELECT payload FROM sources WHERE id=?', (sid,))]
        lat, lon = archive.get('lat'), archive.get('lon')
        shared = []
        if lat is not None and lon is not None:
            shared = [dict(r) for r in db.execute(
                "SELECT id,name,country FROM sites WHERE id<>? "
                "AND json_extract(payload,'$.lat')=? AND json_extract(payload,'$.lon')=? ORDER BY id",
                (site_id, lat, lon))]
        return {'schema_version': 1, 'site_id': site_id, 'policy': POLICY,
                'identity_claims': claims, 'sources': sources,
                'archive_anchor': {'latitude': lat, 'longitude': lon,
                    'location': archive.get('location'), 'precision': archive.get('coordinate_precision'),
                    'basis': 'historical_archive', 'source_verified': False},
                'shared_archive_anchors': shared, 'surveyed_geometry': None}
