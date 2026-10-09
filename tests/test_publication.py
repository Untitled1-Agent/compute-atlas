"""Source-reviewed regression examples; no mockup values are inputs."""
import json
from server.store import ROOT,Store

def test_expanded_primary_publication_and_archival_separation(tmp_path):
    s=Store(tmp_path/'atlas.sqlite3'); s.seed(); pub=s.publication()
    archive=json.loads((ROOT/'data/atlas.json').read_text())
    assert len(archive['sites'])==79
    assert len(pub['sources'])==27
    assert len({o['site_id'] for k in ('observations','facts','relationships') for o in pub[k]})==14
    assert all(x['review_status']=='accepted' for k in ('observations','facts','relationships') for x in pub[k])
    assert pub['published_at']=='2026-10-09'
    sources={x['id'] for x in pub['sources']}
    assert all(x['source_id'] in sources for k in ('observations','facts','relationships') for x in pub[k])

def test_primary_values_retain_their_actual_measurement_boundaries(tmp_path):
    s=Store(tmp_path/'atlas.sqlite3');s.seed();pub=s.publication()
    rows={x['id']:x for x in pub['observations']}
    assert rows['ellendale-live-october']['value']==250
    assert rows['ellendale-live-october']['supersedes']=='ellendale-live-july'
    assert 'ellendale-live-july' not in rows
    assert pub['revision_history']['observations'][0]['value']==175
    assert rows['ellendale-contracted-it']['status']=='contracted'
    assert rows['riverbend-contract-it']['value']==245
    assert rows['riverbend-utility']['boundary']=='utility_capacity'
    assert rows['riverbend-lease-value']['boundary']=='base_lease_value'
    assert rows['uae-initial-tranche']['status']=='planned'
    assert rows['uae-initial-tranche']['boundary']=='unspecified_compute'
    assert rows['prometheus-it-undisclosed']['value'] is None
    assert rows['lingang-reported-pue']['comparison']=='lt'
    assert rows['lingang-energy-saving']['unit']=='kWh/year'
    assert rows['lingang-energy-saving']['metric']!='power'


def test_new_location_sources_are_candidates_not_capacity(tmp_path):
    s=Store(tmp_path/'atlas.sqlite3');s.seed();pub=s.publication()
    candidates=[row for row in pub['discoveries'] if row['source_id'] in ('P19','P20','P21','P22')]
    assert len(candidates)==4 and len(pub['discoveries'])==8
    assert all(row['review_status']=='candidate' and row['latitude'] is None and row['longitude'] is None for row in candidates)
    assert all('power_mw' not in row and 'next_review' in row for row in candidates)
    assert not any(row['source_id'] in ('P19','P20','P21','P22') for kind in ('observations','facts','relationships') for row in pub[kind])
    assert len(pub['observations'])==40
    assert len(json.loads((ROOT/'data/atlas.json').read_text())['sites'])==79
    with s.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM jobs WHERE source_id IN ('P19','P20','P21','P22')").fetchone()[0]==4
    assert all(row['published_at'] is None and row['refresh_hours']==168 for row in pub['sources'] if row['id'] in ('P19','P20','P21','P22'))
