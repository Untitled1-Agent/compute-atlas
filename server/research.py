"""Typed editorial research context; no acquisition can accept these findings."""
from datetime import date

TOPICS = {'identity', 'technical', 'energy', 'development', 'commercial', 'finance'}


def _text(value, limit, label):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'Invalid research {label}')


def _date(value, label):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError(f'Invalid research {label}') from None


def validate_research_claim(kind, claim):
    """Legacy claims remain importable; enriched claims require a clear scope."""
    if not any(key in claim for key in ('topic', 'applies_to', 'source_locator')):
        return
    if kind not in ('fact', 'observation', 'relationship') or claim.get('topic') not in TOPICS:
        raise ValueError('Invalid research topic')
    if claim.get('applies_to') not in ('project', 'context'):
        raise ValueError('Research must distinguish project evidence from wider context')
    _text(claim.get('scope'), 1200, 'scope')
    _text(claim.get('source_locator'), 1200, 'source locator')
    if kind == 'fact':
        _text(claim.get('label'), 200, 'label')
        _text(claim.get('value'), 3000, 'value')
    if claim.get('as_of') is not None:
        _date(claim['as_of'], 'reporting date')


def validate_research_coverage(db, coverage):
    if not isinstance(coverage, dict):
        raise ValueError('Invalid research coverage')
    _date(coverage.get('reviewed_at'), 'review date')
    _text(coverage.get('policy'), 3000, 'coverage policy')
    projects = coverage.get('projects')
    if not isinstance(projects, list) or len(projects) > 10000:
        raise ValueError('Invalid research project list')
    seen = set()
    for item in projects:
        if not isinstance(item, dict):
            raise ValueError('Invalid research project')
        sid = item.get('site_id')
        if sid in seen or not db.execute('SELECT 1 FROM sites WHERE id=?', (sid,)).fetchone():
            raise ValueError('Duplicate or unknown research project')
        seen.add(sid)
        if item.get('outcome') not in ('enriched', 'partial', 'unresolved'):
            raise ValueError('Invalid research outcome')
        _text(item.get('identity_note'), 3000, 'identity note')
        for field, limit in [('gaps', 30), ('source_ids', 150), ('searched', 60)]:
            values = item.get(field, [])
            if not isinstance(values, list) or len(values) > limit:
                raise ValueError(f'Invalid research {field}')
            for value in values:
                _text(value, 1200, field)
                if field == 'source_ids' and not db.execute('SELECT 1 FROM sources WHERE id=?', (value,)).fetchone():
                    raise ValueError('Unknown research source')
