"""Source-only identity changes, native context and offscreen geometry regression."""
import base64,hashlib,json,re,subprocess
from pathlib import Path
import pytest
from tools.normalize_power_context import normalize,BBOX

ROOT=Path(__file__).resolve().parents[1]

def test_screen_geometry_preserves_crossings_enclosing_areas_and_seams():
    script=r"""
const assert=require('node:assert/strict'),context={module:{exports:{}}};
require('node:vm').runInNewContext(require('node:fs').readFileSync('./src/spatial-math.js','utf8'),context);
const m=context.module.exports;
const a={x:-500,y:50},b={x:500,y:50};
assert.deepEqual(JSON.parse(JSON.stringify(m.clipScreenSegment(a,b,100,100))),[{x:0,y:50},{x:100,y:50}]);
assert.deepEqual(a,{x:-500,y:50});
assert.equal(m.screenPathVisible([a,b],100,100),true);
assert.equal(m.screenPathVisible([{x:-1,y:-50},{x:101,y:-50}],100,100),false);
assert.equal(m.screenPathVisible([{x:25,y:25},{x:25,y:25}],100,100),true);
assert.equal(m.clipScreenSegment({x:-1,y:25},{x:-1,y:25},100,100),null);
assert.equal(m.clipScreenSegment({x:NaN,y:25},b,100,100),null);
assert.equal(m.screenPathVisible([a,{x:Infinity,y:50}],100,100),false);
const enclosing=[{x:-50,y:-50},{x:150,y:-50},{x:150,y:150},{x:-50,y:150},{x:-50,y:-50}];
assert.equal(m.screenPathVisible(enclosing,100,100,true),true);
assert.equal(m.screenPathVisible(enclosing,100,100,false),false);
assert.equal(m.insideScreenPolygon({x:50,y:50},enclosing),true);
assert.equal(m.longitudeNear(-179,180),181);
const points=[{x:-500,y:50,z:1,lon:179},{x:500,y:50,z:1,lon:181}];
assert.equal(m.screenPaths(points,{flat:true,width:100}).length,1);
assert.equal(m.screenPaths(points,{flat:false,width:100}).length,0);
assert.equal(m.screenPaths([points[0],{...points[1],lon:-179}],{flat:true,width:100}).length,0);
assert.equal(m.screenPaths([points[0],{x:0,y:0,z:-1},points[1]],{flat:false,width:100}).length,0);
assert.equal(m.screenPaths([{x:-500,y:50},{x:500,y:50}],{scene:true,width:100}).length,1);
"""
    subprocess.run(['node','-e',script],cwd=ROOT,check=True)

def test_local_roads_are_a_separate_cited_derivative_of_the_existing_capture():
    roads=json.loads((ROOT/'data/layers/helios-roads.json').read_text())
    power=json.loads((ROOT/'data/layers/helios-power.json').read_text())
    assert roads['response_sha256']==power['response_sha256']
    assert roads['captured_at']==power['captured_at'] and roads['coverage_bbox']==list(BBOX)
    assert roads['license']=='ODbL-1.0' and len(roads['features'])==36
    assert any(f['tags'].get('access')=='private' for f in roads['features'])
    assert any(f['tags'].get('name')=='County Road 112' for f in roads['features'])
    for f in roads['features']:
        assert f['geometry']['type']=='LineString' and f['tags']['highway']
        assert len(f['node_refs'])==len(f['geometry']['coordinates'])
        assert f['edited_at']<=roads['captured_at'] and f['version']>0
        assert not {'user','uid','project_id','it_mw','public_access'}&set(f)
        assert all(BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3] for path in f['display_paths'] for x,y in path)

def test_road_normalization_keeps_private_access_and_complete_original_geometry():
    raw=b'<osm><node id="1" lon="-101" lat="33.77"/><node id="2" lon="-100.86" lat="33.77"/><way id="20" version="3" timestamp="2017-01-01T00:00:00Z"><nd ref="1"/><nd ref="2"/><tag k="highway" v="service"/><tag k="access" v="private"/></way></osm>'
    f=normalize(raw,'2026-10-11T00:00:00Z',kind='roads')['features'][0]
    assert f['geometry']['coordinates'][0][0]==-101 and f['display_paths'][0][0][0]==-100.9
    assert f['tags']['access']=='private'
    with pytest.raises(ValueError,match='Incomplete'):
        normalize(b'<osm><way id="20"><nd ref="1"/><tag k="highway" v="service"/></way></osm>','2026-10-11',kind='roads')

def test_hosted_release_pins_sources_scripts_styles_and_source_only_identity():
    html=(ROOT/'index.html').read_text()
    pins=json.loads(re.search(r'const ASSET_INTEGRITY=(.*?);\n',html)[1])
    paths=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').iterdir() if p.suffix in ('.css','.js'))
    paths+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data').rglob('*') if p.is_file())
    fingerprints={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    identity=lambda d:hashlib.sha256(json.dumps(d,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:12]
    assert identity(fingerprints)==re.search(r"const ASSET_VERSION='([^']+)'",html)[1]
    changed={**fingerprints,'data/layers/helios-roads.json':'0'*64}
    assert identity(changed)!=identity(fingerprints)
    assert pins['data/layers/helios-roads.json']=='sha256-'+base64.b64encode(hashlib.sha256((ROOT/'data/layers/helios-roads.json').read_bytes()).digest()).decode()
    assert 'integrity:ASSET_INTEGRITY[url]' in html and 'el.integrity=ASSET_INTEGRITY[src]' in html
    for path in ['src/styles.css','src/experience.css','src/directory-schema.js','src/digital-realty-schema.js']:
        assert re.search(r'(?:href|src)="'+re.escape(path)+r'\?v=[^"]+" integrity="'+re.escape(pins[path])+'"',html)
