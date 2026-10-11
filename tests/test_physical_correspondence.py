"""Reviewed utility interpretation cannot alter native geometry, status or MW."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_utility_interpretations_pin_original_native_records_and_capture():
    native=json.loads((ROOT/'data/layers/helios-power.json').read_text())
    reviews=json.loads((ROOT/'data/layers/helios-power-reviews.json').read_text())
    assert len(reviews['reviews'])==3
    for review in reviews['reviews']:
        feature=next(f for f in native['features'] if f['id']==review['native_feature_id'])
        assert feature['version']==review['native_version']
        assert review['captured_response_sha256']==native['response_sha256']
        content=json.dumps(feature,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        assert hashlib.sha256(content).hexdigest()==review['native_record_sha256']
        assert review['it_power_mw'] is None and review['energized_status'] is None
        assert review['reported_voltage_kv']==345
        assert review['depiction_period']=='2026-07' and review['published_at']=='2026-08-05'
    onsite=reviews['reviews'][0]
    assert onsite['transformer_scope']['value']==900
    assert onsite['transformer_scope']['comparison']=='up_to'
    assert 'not delivered power or critical IT' in onsite['transformer_scope']['boundary']
    pitchfork=next(f for f in native['features'] if f['osm_id']==1490401522)
    assert 'voltage' not in pitchfork['tags'] and pitchfork['tags']['construction']=='yes'
