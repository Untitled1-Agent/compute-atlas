"""Editorial scope and import history regressions, including native measurements."""
import copy
import json
import sqlite3

import pytest
from server.store import Store, ROOT
from server.research import validate_research_claim, validate_research_coverage
from tools.merge_project_research import merge


def claim(**changes):
    return {'id':'research-test','site_id':'google-mesa','label':'Cooling',
        'value':'Air cooling','source_id':'P01','as_of':None,
        'topic':'technical','scope':'Named campus','applies_to':'project',
        'source_locator':'Cooling design section','review_status':'accepted',**changes}


@pytest.mark.parametrize('changes', [
    {'applies_to':'nearby'}, {'scope':''}, {'source_locator':None},
    {'topic':'guess'}, {'as_of':'2026-02-31'}, {'value':{'inferred_mw':500}}
])
def test_enriched_claims_cannot_lose_their_boundaries(changes):
    with pytest.raises(ValueError):
        validate_research_claim('fact', claim(**changes))


def test_legacy_claims_and_explicit_wider_context_are_supported():
    validate_research_claim('fact', {'id':'legacy','label':'Opening','value':'2020'})
    validate_research_claim('fact', claim(applies_to='context',scope='County program'))


def test_merge_deduplicates_urls_and_preserves_older_claims():
    original={'sources':[{'id':'P01','url':'https://example.org/disclosure'}],
        'facts':[claim(id='older')], 'observations':[], 'relationships':[]}
    bundle={'sources':[{'id':'R01','url':'https://example.org/disclosure'}],
        'facts':[claim(id='newer',source_id='R01')],
        'coverage':[{'site_id':'google-mesa','outcome':'partial','source_ids':['R01']}]}
    result=merge(original,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')
    assert original['facts']==[claim(id='older')]
    assert result['sources']==original['sources']
    assert result['facts'][0]==original['facts'][0]
    assert result['facts'][1]['source_id']=='P01'
    assert result['research_coverage']['projects'][0]['source_ids']==['P01']
    assert merge(result,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')==result
    bundle['facts'][0]['value']='Invented new capacity'
    with pytest.raises(ValueError,match='Immutable claim collision'):
        merge(result,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')


def test_merge_remaps_nested_and_supporting_citations_idempotently():
    original={'sources':[{'id':'P01','url':'https://example.org/a'},
                         {'id':'P02','url':'https://example.org/b'}],
        'facts':[], 'observations':[], 'relationships':[]}
    bundle={'sources':[{'id':'R01','url':'https://example.org/a'},
                       {'id':'R02','url':'https://example.org/b'}],
        'facts':[claim(source_id='R01',identity={'related_sites':[{'source_id':'R02'}]})],
        'discoveries':[{'id':'candidate-test','site_id':'candidate-test','source_id':'R01',
          'supporting_source_ids':['R02'],'candidate_measurements':[{'source_id':'R02'}]}],
        'coverage':[]}
    before=copy.deepcopy(bundle)
    result=merge(original,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')
    assert result['facts'][0]['identity']['related_sites'][0]['source_id']=='P02'
    candidate=result['discoveries'][0]
    assert candidate['source_id']=='P01' and candidate['supporting_source_ids']==['P02']
    assert candidate['candidate_measurements'][0]['source_id']=='P02'
    assert merge(result,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')==result
    assert bundle==before


def test_merge_rejects_a_reused_bundle_source_id_with_a_different_url():
    original={'sources':[{'id':'P01','url':'https://example.org/a'},
                         {'id':'P02','url':'https://example.org/b'}], 'facts':[]}
    bundle={'sources':[{'id':'R01','url':'https://example.org/a'},
                       {'id':'R01','url':'https://example.org/b'}],
        'facts':[claim(source_id='R01')],'coverage':[]}
    with pytest.raises(ValueError,match='Source identifier collision'):
        merge(original,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')


@pytest.mark.parametrize('field',['supporting','measurement','identity','coverage'])
def test_merge_rejects_unregistered_secondary_citations(field):
    original={'sources':[{'id':'P01','url':'https://example.org/a'}], 'facts':[]}
    bundle={'sources':[],'facts':[],'coverage':[]}
    if field=='coverage':bundle['coverage']=[{'site_id':'google-mesa','source_ids':['unknown']}]
    elif field=='identity':bundle['facts']=[claim(identity={'related_sites':[{'source_id':'unknown'}]})]
    else:
        candidate={'id':'candidate-test','site_id':'candidate-test','source_id':'P01'}
        if field=='supporting':candidate['supporting_source_ids']=['unknown']
        else:candidate['candidate_measurements']=[{'source_id':'unknown'}]
        bundle['discoveries']=[candidate]
    with pytest.raises(ValueError,match='Unregistered research source'):
        merge(original,[bundle],reviewed_by='editor',reviewed_at='2026-10-10')


def test_research_coverage_rejects_unknown_sources_and_duplicate_sites(tmp_path):
    store=Store(tmp_path/'atlas.sqlite3');store.seed()
    coverage={'reviewed_at':'2026-10-10','policy':'Editorial findings, not completeness',
        'projects':[{'site_id':'google-mesa','outcome':'partial','identity_note':'Campus established',
          'gaps':['Current measured power'],'source_ids':['does-not-exist']}]}
    with store.connect() as db:
        with pytest.raises(ValueError,match='Unknown research source'):
            validate_research_coverage(db,coverage)
        coverage['projects'][0]['source_ids']=['P01']
        coverage['projects'].append(copy.deepcopy(coverage['projects'][0]))
        with pytest.raises(ValueError,match='Duplicate or unknown research project'):
            validate_research_coverage(db,coverage)


def test_native_china_figures_carry_identity_and_precision_boundaries():
    bundle=json.loads((ROOT/'data/research/china-2026-10-10.json').read_text())
    rows={r['id']:r for r in bundle['observations']+bundle['facts']}
    fp16=rows['research-20261010-qianhai-fp16']
    assert (fp16['value'],fp16['unit'],fp16['status'])==(500,'PFLOPS FP16','planned')
    assert fp16['applies_to']=='project'
    assert rows['research-20261010-qingxin-solar-mw']['boundary']=='generation'
    assert rows['research-20261010-qingxin-solar-mw']['applies_to']=='context'
    assert rows['research-20261010-yangquan-7000-context']['applies_to']=='context'
    assert rows['research-20261010-guian-design-pue']['boundary']=='design_pue'
    assert rows['research-20261010-zhangbei-heat-2026']['unit']=='GJ'
    assert rows['research-20261010-zhangbei-heat-2026']['applies_to']=='context'


def test_published_research_and_claims_survive_backup_and_reimport(tmp_path):
    store=Store(tmp_path/'atlas.sqlite3');store.seed()
    # Covers the actual accepted publication, rather than a parallel JSON-only fixture.
    pub=store.publication()
    research=pub.get('research_coverage')
    assert research is not None
    sites=json.loads((ROOT/'data/atlas.json').read_text())['sites']
    assert {p['site_id'] for p in research['projects']}=={s['id'] for s in sites}
    sources={s['id'] for s in pub['sources']}
    assert all(set(p['source_ids'])<=sources for p in research['projects'])
    before=json.dumps(pub,sort_keys=True)
    store.seed()
    assert json.dumps(store.publication(),sort_keys=True)==before
    backup=tmp_path/'backup.sqlite3';store.backup(backup)
    assert Store(backup).publication()==pub
    with sqlite3.connect(backup) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_capture_disk_reserve_preserves_publication_and_records_retry(tmp_path,monkeypatch):
    import httpx
    from types import SimpleNamespace
    from server.acquire import Monitor, CAPTURE_DISK_RESERVE
    store=Store(tmp_path/'atlas.sqlite3');store.seed();before=store.publication()
    body=b'<main>Synthetic source capture for disk reserve regression</main>'
    transport=httpx.MockTransport(lambda request:httpx.Response(404) if request.url.path=='/robots.txt'
        else httpx.Response(200,content=body,headers={'content-type':'text/html'}))
    monkeypatch.setattr('server.acquire.shutil.disk_usage',lambda _:SimpleNamespace(free=CAPTURE_DISK_RESERVE+len(body)-1))
    with httpx.Client(transport=transport) as client:
        monitor=Monitor(store,tmp_path/'blobs',client,resolve_dns=False,min_host_interval=0)
        assert monitor.run_once()
    assert list((tmp_path/'blobs').iterdir())==[]
    assert store.publication()==before
    with store.connect() as db:
        job=db.execute('SELECT failures,last_error,lease_token FROM jobs WHERE failures>0').fetchone()
        assert job['failures']==1 and 'disk reserve' in job['last_error'] and job['lease_token'] is None
        assert db.execute('SELECT COUNT(*) FROM source_versions').fetchone()[0]==0
