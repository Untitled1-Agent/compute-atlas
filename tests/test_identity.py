"""Typed locality evidence never certifies geometry or merges shared city pins."""
import copy
import json
import shutil
import sqlite3

import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from server.identity import identity_document
from server.store import ROOT, Store

@pytest.fixture
def store(tmp_path):
    ledger = Store(tmp_path/'identity.sqlite3'); ledger.seed(); return ledger

@pytest.fixture
def claim():
    return copy.deepcopy(next(f for f in json.loads((ROOT/'data/evidence.json').read_text())['facts']
                              if f['id']=='abilene-flagship-identity-20261005'))

def ids(store, site):
    return {row['id'] for row in identity_document(store, site)['identity_claims']}

def test_six_source_identities_preserve_archive_and_existing_quantities(store):
    archive_before = (ROOT/'data/atlas.json').read_bytes()
    pub=store.publication(); typed=[f for f in pub['facts'] if 'identity' in f]
    assert len(typed)==6 and len(pub['facts'])==35 and len(pub['observations'])==40
    assert len(pub['sources'])==27 and len(pub['discoveries'])==8
    assert all(f['identity']['coordinate_evidence']=='not_established' for f in typed)
    assert all(f['reviewed_at']=='2026-10-05' for f in typed)
    archive=json.loads(archive_before)
    with store.connect() as db:
        assert {s['id']:s for s in archive['sites']} == {
            r['id']:json.loads(r['payload']) for r in db.execute('SELECT id,payload FROM sites')}
    assert (ROOT/'data/atlas.json').read_bytes()==archive_before

def test_same_city_anchor_is_not_a_site_merge_and_link_keeps_own_source(store):
    original=identity_document(store,'oracle-openai-stargate-abilene')
    new=identity_document(store,'crusoe-abilene-expansion')
    assert original['archive_anchor']['latitude']==new['archive_anchor']['latitude']==32.45
    assert original['archive_anchor']['longitude']==new['archive_anchor']['longitude']==-99.73
    assert original['site_id']!=new['site_id']
    assert {s['id'] for s in original['sources']}=={'P02','P03'}
    assert original['identity_claims'][0]['source_id']=='P02'
    assert original['identity_claims'][0]['identity']['related_sites'][0]['source_id']=='P03'
    assert new['site_id'] in {s['id'] for s in original['shared_archive_anchors']}
    assert original['surveyed_geometry'] is None
    assert original['archive_anchor']['source_verified'] is False
    assert 'capacity' not in original and 'total_mw' not in original

def test_parish_name_does_not_upgrade_archive_pin_and_alias_does_not_rename_archive(store):
    rb=identity_document(store,'hut8-river-bend')
    assert rb['identity_claims'][0]['identity']['place_precision']=='county_or_parish'
    assert 'West Feliciana' in rb['identity_claims'][0]['identity']['place']
    assert rb['archive_anchor']['location']=='Louisiana (state-level anchor)'
    helios=identity_document(store,'coreweave-helios')
    assert helios['identity_claims'][0]['identity']['place_precision']=='region'
    assert 'Afton' in helios['archive_anchor']['location']
    ellendale=identity_document(store,'coreweave-ellendale')
    assert ellendale['identity_claims'][0]['identity']['canonical_name']=='Polaris Forge 1'
    assert ellendale['site_id']=='coreweave-ellendale'

def test_identity_revisions_follow_editorial_acceptance_and_retained_history(store,claim):
    root=claim['id']; sid=claim['site_id']
    revision={**claim,'id':'identity-review-test','supersedes':root}
    revision['identity']=copy.deepcopy(claim['identity'])
    revision['identity']['canonical_name']='Synthetic revised identity (test only)'
    store.submit_claim('fact',revision,'test-editor')
    assert ids(store,sid)=={root}
    store.decide(revision['id'],'accepted','test-editor','Synthetic unit-test review')
    assert ids(store,sid)=={revision['id']}
    assert root in {f['id'] for f in store.publication()['revision_history']['facts']}
    store.decide(revision['id'],'rejected','test-editor','Synthetic unit-test withdrawal')
    assert ids(store,sid)=={root}
    assert revision['id'] not in json.dumps(identity_document(store,sid))

def test_independent_identity_descriptions_are_not_silently_selected_or_collapsed(store,claim):
    other={**claim,'id':'identity-independent-test','source_id':'P03'}
    store.submit_claim('fact',other,'test-editor')
    store.decide(other['id'],'accepted','test-editor','Synthetic independent source')
    assert ids(store,claim['site_id'])=={claim['id'],other['id']}

def test_identity_publication_roundtrip_and_reseed_preserve_review_decisions(store,claim,tmp_path):
    revision={**claim,'id':'identity-portable-test','supersedes':claim['id']}
    store.submit_claim('fact',revision,'test-editor')
    store.decide(revision['id'],'accepted','test-editor','Test export review')
    exported=store.publication()
    dest=tmp_path/'copy'; (dest/'data').mkdir(parents=True)
    shutil.copy(ROOT/'data/atlas.json',dest/'data/atlas.json')
    (dest/'data/evidence.json').write_text(json.dumps(exported))
    restored=Store(tmp_path/'restored.sqlite3'); restored.seed(dest); restored.seed(dest)
    assert restored.publication()==exported
    assert identity_document(restored,claim['site_id'])==identity_document(store,claim['site_id'])
    store.seed()  # old checked-in fact cannot override later explicit acceptance
    assert ids(store,claim['site_id'])=={revision['id']}

@pytest.mark.parametrize('field,value',[
    ('canonical_name',''),('canonical_name',12),('canonical_name','x'*401),
    ('place',' '),('place',None),('place_precision','parcel'),('place_precision',[]),
    ('project_scope','building'),('coordinate_evidence','surveyed'),('related_sites',None),
])
def test_invalid_identity_fields_fail_atomically(store,claim,field,value):
    claim['id']='invalid-identity';claim['identity'][field]=value
    with pytest.raises(ValueError):store.submit_claim('fact',claim,'test-editor')
    with store.connect() as db:
        assert db.execute('SELECT 1 FROM claims WHERE id=?',(claim['id'],)).fetchone() is None

@pytest.mark.parametrize('field,value',[
    ('reviewed_at','2025-01-01'),('reviewed_at','2026-02-30'),
    ('as_of',None),('as_of','2026-1-1'),('reviewed_at',False),
])
def test_identity_dates_are_required_real_dates(store,claim,field,value):
    claim['id']='invalid-date';claim[field]=value
    with pytest.raises(ValueError):store.submit_claim('fact',claim,'test-editor')

@pytest.mark.parametrize('change',['extra_coordinates','missing_place','unknown_link_source',
    'self_link','duplicate_link','unknown_link_site','extra_link_field','wrong_relation','unknown_source'])
def test_identity_cannot_smuggle_geometry_or_uncited_relationships(store,claim,change):
    claim['id']='invalid-relationship';x=claim['identity'];link=x['related_sites'][0]
    if change=='extra_coordinates':x['coordinates']=[32.45,-99.73]
    if change=='missing_place':del x['place']
    if change=='unknown_link_source':link['source_id']='unknown'
    if change=='self_link':link['site_id']=claim['site_id']
    if change=='duplicate_link':x['related_sites'].append(copy.deepcopy(link))
    if change=='unknown_link_site':link['site_id']='unknown'
    if change=='extra_link_field':link['latitude']=32.45
    if change=='wrong_relation':link['relation']='same_campus'
    if change=='unknown_source':claim['source_id']='unknown'
    with pytest.raises((ValueError,sqlite3.IntegrityError)):
        store.submit_claim('fact',claim,'test-editor')

@pytest.mark.parametrize('kind',['observation','relationship','discovery'])
def test_identity_cannot_hide_inside_another_claim_kind(store,claim,kind):
    claim['id']='wrong-kind'
    with pytest.raises(ValueError,match='typed fact'):store.submit_claim(kind,claim,'test-editor')

def test_identity_and_ordinary_fact_revision_series_stay_separate(store,claim):
    ordinary=copy.deepcopy(claim);ordinary.pop('identity');ordinary['id']='ordinary'
    ordinary['supersedes']=claim['id']
    with pytest.raises(ValueError,match='Identity revisions'):store.submit_claim('fact',ordinary,'test-editor')
    ordinary.pop('supersedes');store.submit_claim('fact',ordinary,'test-editor')
    claim['id']='typed-from-ordinary';claim['supersedes']='ordinary'
    with pytest.raises(ValueError,match='Identity revisions'):store.submit_claim('fact',claim,'test-editor')

def test_missing_identity_is_not_zero_capacity_and_null_pins_do_not_match(store):
    archive=json.loads((ROOT/'data/atlas.json').read_text())
    unreviewed=next(s for s in archive['sites'] if s.get('lat') is None)
    doc=identity_document(store,unreviewed['id'])
    assert doc['identity_claims']==[] and doc['shared_archive_anchors']==[]
    assert doc['archive_anchor']['latitude'] is None and doc['surveyed_geometry'] is None
    assert identity_document(store,'not-a-site') is None

def test_read_only_identity_api_has_cache_boundary_and_no_pending_drafts(tmp_path,claim):
    app=create_app(tmp_path/'api.sqlite3',background=False)
    claim['id']='pending-secret';claim['identity']['place']='Pending editorial draft'
    app.state.store.submit_claim('fact',claim,'test-editor')
    with TestClient(app) as client:
        response=client.get('/api/sites/'+claim['site_id']+'/identity')
        assert response.status_code==200 and {'private','no-store'}<=set(response.headers['cache-control'].replace(' ','').split(','))
        assert response.json()==identity_document(app.state.store,claim['site_id'])
        assert 'Pending editorial draft' not in response.text
        assert client.post('/api/sites/'+claim['site_id']+'/identity',json={}).status_code==405
        assert client.get('/api/sites/unknown/identity').status_code==404
