"""Merge explicitly reviewed factual research, preserving immutable older claims.

This is an editorial repository tool, not an acquisition parser. Inspect the
cited bundles before invoking it. The SQLite importer independently validates
the publication and never overrides an editor's existing decisions.
"""
from __future__ import annotations
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.store import TABLES, canonical, digest


def merge(evidence, bundles, *, reviewed_by, reviewed_at):
    if not reviewed_by.strip():
        raise ValueError('An editorial reviewer is required')
    result = copy.deepcopy(evidence)
    urls = {s['url']: s['id'] for s in result['sources']}
    source_ids = {s['id'] for s in result['sources']}
    claims = {c['id']: c for k in TABLES for c in result.get(k, []) + result.get('revision_history', {}).get(k, [])}
    projects = {p['site_id']: p for p in result.get('research_coverage', {}).get('projects', [])}
    for bundle in bundles:
        aliases = {}; bundle_urls = {}
        for s in bundle['sources']:
            if s['id'] in bundle_urls and bundle_urls[s['id']] != s['url']:
                raise ValueError('Source identifier collision: ' + s['id'])
            bundle_urls[s['id']] = s['url']
            if s['url'] in urls:
                aliases[s['id']] = urls[s['url']]
            else:
                if s['id'] in source_ids:
                    raise ValueError('Source identifier collision: ' + s['id'])
                result['sources'].append(copy.deepcopy(s))
                source_ids.add(s['id']); urls[s['url']] = s['id']; aliases[s['id']] = s['id']

        def citation(source_id):
            resolved = aliases.get(source_id, source_id)
            if resolved not in source_ids:
                raise ValueError('Unregistered research source')
            return resolved

        for key in TABLES:
            for original in bundle.get(key, []):
                claim = copy.deepcopy(original)
                claim['source_id'] = citation(claim['source_id'])
                if 'supporting_source_ids' in claim:
                    claim['supporting_source_ids'] = [citation(sid) for sid in claim['supporting_source_ids']]
                for measurement in claim.get('candidate_measurements', []) or []:
                    measurement['source_id'] = citation(measurement['source_id'])
                for link in (claim.get('identity') or {}).get('related_sites', []):
                    link['source_id'] = citation(link['source_id'])
                if claim['id'] in claims:
                    if canonical(claim) != canonical(claims[claim['id']]):
                        raise ValueError('Immutable claim collision: ' + claim['id'])
                    continue
                if key != 'discoveries' and claim.get('review_status') != 'accepted':
                    raise ValueError('Bundle contains an unreviewed claim')
                result.setdefault(key, []).append(claim); claims[claim['id']] = claim
        for original in bundle['coverage']:
            project = copy.deepcopy(original)
            project['source_ids'] = sorted(set(citation(sid) for sid in project.get('source_ids', [])))
            project['reviewed_by'] = reviewed_by
            projects[project['site_id']] = project
    result['published_at'] = reviewed_at
    result['research_coverage'] = {'reviewed_at': reviewed_at,
        'policy': 'Research outcomes describe this editorial pass, not completeness or confidence scores. Project claims and wider context stay separate; ambiguous aliases and undisclosed fields remain open. Reporting dates do not prove present operating status.',
        'projects': sorted(projects.values(), key=lambda p: p['site_id'])}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundles', type=Path, nargs='+')
    parser.add_argument('--reviewed-by', required=True)
    parser.add_argument('--reviewed-at', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = json.loads((ROOT/'data/evidence.json').read_text())
    result = merge(original, [json.loads(p.read_text()) for p in args.bundles],
                   reviewed_by=args.reviewed_by, reviewed_at=args.reviewed_at)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'hash': digest(result), 'sources': len(result['sources']),
        'claims': {k: len(result.get(k, [])) for k in TABLES},
        'projects_researched': len(result['research_coverage']['projects'])}))


if __name__ == '__main__':
    main()
