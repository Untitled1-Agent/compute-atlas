"""Regression contracts for multi-generation editorial revisions and portable snapshots."""
import copy
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from server.store import ROOT, Store

@pytest.fixture
def store(tmp_path):
    ledger=Store(tmp_path/'ledger.sqlite3'); ledger.seed(); return ledger

@pytest.fixture
def observation():
    return copy.deepcopy(json.loads((ROOT/'data/evidence.json').read_text())['observations'][0])

def revise(store, observation, name, parent, *, accept=True):
    claim={**observation,'id':name,'supersedes':parent,'value':144}
    store.submit_claim('observation',claim,'test-editor')
    if accept: store.decide(name,'accepted','test-editor','Reviewed new disclosure in this series')
    return claim

def active(store):
    return {x['id'] for x in store.publication()['observations']}

def test_rejected_middle_revision_does_not_resurrect_old_capacity(store,observation):
    root=observation['id']
    revise(store,observation,'r1',root)
    revise(store,observation,'r2','r1')
    store.decide('r1','rejected','test-editor','Intermediary interpretation withdrawn')
    assert active(store).intersection({root,'r1','r2'})=={'r2'}
    store.decide('r2','rejected','test-editor','Latest interpretation withdrawn too')
    assert active(store).intersection({root,'r1','r2'})=={root}

def test_competing_cousin_of_accepted_grandchild_cannot_publish(store,observation):
    root=observation['id']
    revise(store,observation,'r1',root)
    revise(store,observation,'r2','r1')
    revise(store,observation,'sibling',root,accept=False)
    with pytest.raises(ValueError,match='Conflicting'):
        store.decide('sibling','accepted','test-editor','Would create two versions of one series')
    revise(store,observation,'cousin','sibling',accept=False)
    with pytest.raises(ValueError,match='Conflicting'):
        store.decide('cousin','accepted','test-editor','Deep fork also conflicts')
    assert active(store).intersection({root,'r1','r2','sibling','cousin'})=={'r2'}

def test_concurrent_reviewers_cannot_publish_conflicting_revisions(store,observation):
    root=observation['id']
    for cid in ('left','right'): revise(store,observation,cid,root,accept=False)
    barrier=Barrier(2)
    def decide(cid):
        barrier.wait(timeout=5)
        try:
            store.decide(cid,'accepted',cid,'Independent reviewer decision')
            return 'accepted'
        except ValueError: return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(decide,['left','right']))
    assert sorted(results)==['accepted','conflict']
    assert len(active(store).intersection({'left','right'}))==1

@pytest.mark.parametrize('field,value',[('unit','GW'),('boundary','gross_facility'),('metric','generation'),('scope','Entire fleet')])
def test_revision_cannot_silently_change_measurement_series(store,observation,field,value):
    claim={**observation,'id':'bad-revision','supersedes':observation['id'],field:value}
    with pytest.raises(ValueError): store.submit_claim('observation',claim,'test-editor')

def test_export_can_be_imported_with_revision_ancestors_and_rejections(store,observation,tmp_path):
    root=observation['id']
    revise(store,observation,'r1',root)
    revise(store,observation,'r2','r1')
    store.decide('r1','rejected','test-editor','Corrected interpretation')
    pub=store.publication()
    history={x['id']:x for x in pub['revision_history']['observations']}
    assert history[root]['review_status']=='accepted'
    assert history['r1']['review_status']=='rejected'
    assert root not in {x['id'] for x in pub['observations']}
    destination=tmp_path/'portable'; (destination/'data').mkdir(parents=True)
    shutil.copy(ROOT/'data/atlas.json',destination/'data/atlas.json')
    # Dependency order, not alphabetic or incidental JSON order, controls import.
    pub['revision_history']['observations'].reverse()
    (destination/'data/evidence.json').write_text(json.dumps(pub))
    restored=Store(tmp_path/'restored.sqlite3'); restored.seed(destination)
    assert active(restored)==active(store)
    assert restored.publication()==store.publication()
    restored.seed(destination)  # Reseeding is idempotent, including withdrawn ancestors.
    assert restored.publication()==store.publication()

def test_missing_revision_parent_fails_seed_atomically(tmp_path,observation):
    root=tmp_path/'missing'; (root/'data').mkdir(parents=True)
    shutil.copy(ROOT/'data/atlas.json',root/'data/atlas.json')
    evidence=json.loads((ROOT/'data/evidence.json').read_text())
    evidence['observations'].append({**observation,'id':'orphan','supersedes':'missing-parent'})
    (root/'data/evidence.json').write_text(json.dumps(evidence))
    ledger=Store(tmp_path/'orphan.sqlite3')
    with pytest.raises(ValueError,match='ancestry'): ledger.seed(root)
    with ledger.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM claims').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]==0

def test_version_one_database_is_upgraded_without_losing_data(store,observation):
    root=observation['id']
    revise(store,observation,'r1',root)
    revise(store,observation,'r2','r1')
    store.decide('r1','rejected','editor','Withdraw intermediary')
    with store.connect() as db:
        count=db.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
        db.execute('DELETE FROM migrations WHERE version=2')
        db.execute('DROP VIEW accepted_claims')
        db.execute("""CREATE VIEW accepted_claims AS SELECT c.* FROM claims c JOIN current_decisions d
          ON c.id=d.claim_id AND d.decision='accepted' WHERE NOT EXISTS
          (SELECT 1 FROM claims n JOIN current_decisions nd ON nd.claim_id=n.id
           WHERE n.supersedes=c.id AND nd.decision='accepted')""")
    upgraded=Store(store.path)
    assert active(upgraded).intersection({root,'r1','r2'})=={'r2'}
    with upgraded.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]==count
        assert db.execute('SELECT MAX(version) FROM migrations').fetchone()[0]==2

def test_history_api_is_read_only_and_excludes_pending_editorial_drafts(tmp_path,observation):
    app=create_app(tmp_path/'api.sqlite3',background=False)
    ledger=app.state.store; root=observation['id']
    revise(ledger,observation,'reviewed',root)
    revise(ledger,observation,'pending','reviewed',accept=False)
    with TestClient(app) as client:
        result=client.get(f'/api/claims/{root}/history')
        assert result.status_code==200
        entries={x['claim']['id']:x for x in result.json()['items']}
        assert entries[root]['effective'] is False
        assert entries['reviewed']['effective'] is True
        assert entries['reviewed']['decisions'][0]['actor']=='test-editor'
        assert 'pending' not in entries
        assert client.get('/api/claims/pending/history').status_code==404
        assert client.post(f'/api/claims/{root}/history',json={}).status_code==405
        assert client.get('/api/claims/unknown/history').status_code==404
