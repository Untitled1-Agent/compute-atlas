"""Lossless publication contracts: independent raw source bytes are the oracle."""
import base64,csv,hashlib,io,json,zipfile
from pathlib import Path
import pytest
from tools.capture_gpu_clusters import normalize as gpu_normalize
from tools.capture_data_centers import normalize as centers_normalize
ROOT=Path(__file__).resolve().parents[1]
GPU=json.loads((ROOT/'data/catalog/gpu-clusters.json').read_text())
CENTERS=json.loads((ROOT/'data/catalog/epoch-data-centers.json').read_text())

def test_gpu_every_source_cell_and_row_survives():
    raw=(ROOT/'data/catalog/epoch-gpu-clusters.csv').read_bytes()
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    assert [r['fields'] for r in GPU['records']]==rows
    assert len(rows)==GPU['counts']['records']==482
    assert len({r['id'] for r in GPU['records']})==len(rows)
    assert hashlib.sha256(raw).hexdigest()==GPU['source_sha256']
    assert gpu_normalize(raw,GPU['captured_at'],GPU['publisher_page_date'])==GPU

def test_anonymity_missingness_and_history_are_preserved():
    anonymous=[r for r in GPU['records'] if r['anonymous']]
    assert len(anonymous)==190
    for r in anonymous:
        assert r['name']=='Anonymized Chinese System'
        assert r['operator'] is None and not r['source_urls']
    assert sum(r['lat'] is not None for r in GPU['records'])==447
    assert sum(bool(r['superseded_by']) for r in GPU['records'])==30
    for r in GPU['records']:
        assert (r['reported_power_mw'] is None)==(r['fields']['Reported Power Capacity (MW)']=='')
        assert 'it_mw' not in r
        assert (r['lat'] is None)==(r['lon'] is None)

def test_all_six_tables_match_the_original_archive_exactly():
    raw=base64.b64decode(CENTERS['archive_base64']);assert hashlib.sha256(raw).hexdigest()==CENTERS['source_sha256']
    z=zipfile.ZipFile(io.BytesIO(raw));expected={'centers':95,'timelines':567,'deployments':239,'chillers':143,'towers':527,'chips':32}
    identities=[]
    for key,table in CENTERS['tables'].items():
        reader=csv.DictReader(io.StringIO(z.read(table['filename']).decode('utf-8-sig')))
        rows=list(reader);assert table['columns']==reader.fieldnames
        assert [r['fields'] for r in table['records']]==rows
        assert len(rows)==expected[key]
        identities.extend(r['id'] for r in table['records'])
    assert len(set(identities))==len(identities)==1603
    assert centers_normalize(raw,CENTERS['captured_at'],CENTERS['published_at'])==CENTERS

def test_all_timeline_and_deployment_parent_links_resolve():
    names={r['name'] for r in CENTERS['tables']['centers']['records']}
    for key in ('timelines','deployments'):
        assert all(r['fields']['Data center'] in names for r in CENTERS['tables'][key]['records'])

def test_capture_rejects_partial_source_and_nonfinite_coordinates():
    with pytest.raises(ValueError):gpu_normalize(b'Name,Country\nExample,UK','2026-10-22')
    raw=(ROOT/'data/catalog/epoch-gpu-clusters.csv').read_text()
    rows=list(csv.DictReader(io.StringIO(raw)));rows[0]['latitude']='NaN'
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with pytest.raises(ValueError):gpu_normalize(buf.getvalue().encode(),'2026-10-22')
