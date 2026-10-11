"""Publication constraints for the reviewed historical imagery layer."""
import hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/campus/scenes.json').read_text())

def test_historical_features_do_not_duplicate_capacity_or_osm_records():
    projects={s['id'] for s in json.loads((ROOT/'data/atlas.json').read_text())['sites']}
    osm={s['id'] for s in json.loads((ROOT/'data/catalog/osm.json').read_text())['records']}
    for scene in DATA['scenes']:
        assert scene['project_id'] in projects
        assert scene['review']['status']=='accepted_historical_interpretation'
        for feature in scene['features']:
            assert feature['id'] not in projects|osm
            assert feature['phase_id'] is None
            assert feature['it_power_mw'] is None
            assert feature['height_m'] is None
            assert feature['operating_status'] is None

def test_reviewed_naip_bytes_and_image_date_are_pinned():
    for scene in DATA['scenes']:
        im=scene['image'];path=ROOT/im['path']
        assert path.stat().st_size==im['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==im['sha256']
        assert im['license']=='Public domain'
        assert im['publisher']=='USDA NAIP / USGS National Map'
        assert im['acquired_at'].replace('-','') in im['raster_name']
        assert 'esriMosaicLockRaster' in im['export_url']
        assert str(im['raster_id']) in im['export_url']

def test_roof_interpretation_uses_returned_export_extent():
    for scene in DATA['scenes']:
        im=scene['image'];e=im['extent_3857']
        assert e['spatialReference']['latestWkid']==3857
        for f in scene['features']:
            assert f['observed_at']==im['acquired_at']
            ring=f['geometry']['coordinates'][0][0]
            assert ring[0]==ring[-1]
            for (lon,lat),(px,py) in zip(ring,f['pixel_vertices'],strict=True):
                x=6378137*math.radians(lon)
                y=6378137*math.log(math.tan(math.pi/4+math.radians(lat)/2))
                actual_x=(x-e['xmin'])/(e['xmax']-e['xmin'])*im['width']
                actual_y=(e['ymax']-y)/(e['ymax']-e['ymin'])*im['height']
                assert abs(actual_x-px)<.02 and abs(actual_y-py)<.02
                assert 0<=px<=im['width'] and 0<=py<=im['height']
