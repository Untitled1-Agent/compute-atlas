"""Nordic source scopes survive without adding sites or operating capacity."""
import copy
import json
import pytest
from server.store import ROOT, Store


@pytest.fixture
def store(tmp_path):
    result=Store(tmp_path/'atlas.sqlite3');result.seed();return result


def test_nordic_leads_retain_primary_sources_and_nonadditive_scopes(store):
    pub=store.publication();leads={r['id']:r for r in pub['discoveries'] if r['id'].startswith('atnorth-')}
    assert len(leads)==3 and len(pub['discoveries'])==8 and len(pub['observations'])==40
    assert len(json.loads((ROOT/'data/atlas.json').read_text())['sites'])==79
    assert all(r['review_status']=='candidate' and r['latitude'] is None and r['longitude'] is None and r['operating_it_mw'] is None for r in leads.values())
    fin=leads['atnorth-fin05-candidate']['candidate_measurements']
    assert [(m['value'],m['boundary']) for m in fin]==[(230,'gross_facility'),(160,'critical_it'),(60,'critical_it'),(75,'secured_power')]
    assert fin[1]['comparison']=='lte' and all(m['status']=='planned' for m in fin)
    assert 'Q3 2028' in fin[2]['scope']
    den=leads['atnorth-den01-candidate']
    assert 'Q4 2025' in den['note'] and 'Q1 2026' in den['note'] and den['supporting_source_ids']==['P26']
    assert den['candidate_measurements'][0]['boundary']=='campus_power'
    assert all(m['boundary']=='site_power' and m['status']=='planned' for m in leads['atnorth-nor01-candidate']['candidate_measurements'])
    assert not any(r['source_id'] in {'P23','P24','P25','P26','P27'} for k in ('observations','facts','relationships') for r in pub[k])
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM jobs WHERE source_id IN ('P23','P24','P25','P26','P27')").fetchone()[0]==5


@pytest.mark.parametrize('field,value',[('value',True),('value',-1),('value',float('inf')),('value','160'),('unit','MWh'),('boundary','operating_it'),('source_id','P01'),('comparison','estimate'),('status','operating'),('as_of','2026-02-30'),('scope','')])
def test_candidate_measurement_validation(store,field,value):
    candidate=copy.deepcopy(next(r for r in store.publication()['discoveries'] if r['id']=='atnorth-fin05-candidate'))
    candidate['id']='invalid-candidate';candidate['candidate_measurements'][0][field]=value
    with pytest.raises(ValueError): store.submit_claim('discovery',candidate,'test')


def test_lead_review_does_not_promote_it_to_a_site_and_rejection_survives_restart(store):
    candidate=copy.deepcopy(next(r for r in store.publication()['discoveries'] if r['id']=='atnorth-fin05-candidate'))
    candidate['id']='new-unmapped-lead';candidate['candidate_measurements'][0]['value']=None
    store.submit_claim('discovery',candidate,'analyst');store.decide(candidate['id'],'accepted','analyst','Reviewed source lead; geographic identity still unresolved')
    lead=next(r for r in store.publication()['discoveries'] if r['id']==candidate['id'])
    assert lead['review_status']=='candidate' and lead['candidate_measurements'][0]['value'] is None
    assert store.site_page('FIN05')['total']==0
    store.decide(candidate['id'],'rejected','analyst','Withdraw pending identity review');store.seed()
    assert not any(r['id']==candidate['id'] for r in store.publication()['discoveries'])
