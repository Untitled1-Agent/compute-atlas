"""Independent native raster metadata governs the published aerial context."""
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse,parse_qs

ROOT=Path(__file__).resolve().parents[1]

def test_every_us_context_anchor_has_a_capture_or_explicit_unavailability():
    manifest=json.loads((ROOT/'data/maps/anchor-imagery.json').read_text())
    context=json.loads((ROOT/'data/layers/global-context-index.json').read_text())
    expected=[a for c in context['captures'] for a in c['anchors'] if a['country']=='United States']
    assert [r['anchor'] for r in manifest['records']]==expected
    assert len({r['id'] for r in manifest['records']})==len(expected)==81
    assert sum(r['status']=='captured' for r in manifest['records'])>=75
    assert 'does not verify campus ownership' in manifest['policy']

def test_image_bytes_and_catalogs_retain_native_identity_dates_and_georeferencing():
    manifest=json.loads((ROOT/'data/maps/anchor-imagery.json').read_text())
    for record in manifest['records']:
        metadata=record['metadata'];raw=(ROOT/metadata['path']).read_bytes()
        assert len(raw)==metadata['bytes']
        assert hashlib.sha256(raw).hexdigest()==metadata['sha256']
        native=json.loads(raw)
        assert native['anchor']==record['anchor'] and native['status']==record['status']
        if record['status']!='captured':
            assert record['reason'] and 'image' not in record
            continue
        im=record['image'];image=(ROOT/im['path']).read_bytes()
        assert image.startswith(b'\xff\xd8\xff') and b'\xff\xd9' in image[-4096:]
        assert len(image)==im['bytes'] and hashlib.sha256(image).hexdigest()==im['sha256']
        assert native['image']==im
        selected=[r['attributes'] for r in native['catalog']['features'] if r['attributes']['OBJECTID'] in record['selected_raster_ids']]
        assert {r['OBJECTID'] for r in selected}==set(record['selected_raster_ids'])
        dates=sorted({datetime.fromtimestamp(r['acquisition_date']/1000,timezone.utc).date().isoformat() for r in selected if r.get('acquisition_date') is not None})
        assert im['acquisition_dates']==dates
        assert all(date in im['acquired_at'] or dates[0]<date<dates[-1] for date in dates)
        if any(r.get('acquisition_date') is None for r in selected):assert 'unreported' in im['acquired_at'] or 'not supplied' in im['acquired_at']
        recipe=parse_qs(urlparse(native['export_url']).query)
        assert json.loads(recipe['mosaicRule'][0])['lockRasterIds']==record['selected_raster_ids']
        assert recipe['size']==[f"{im['width']},{im['height']}"]
        assert recipe['bboxSR']==recipe['imageSR']==['3857']
        assert im['extent_3857']==native['export']['extent']
        e=im['extent_3857'];anchor=record['anchor'];x=6378137*math.radians(anchor['lon']);y=6378137*math.log(math.tan(math.pi/4+math.radians(anchor['lat'])/2))
        assert e['xmin']<x<e['xmax'] and e['ymin']<y<e['ymax']
        assert abs((e['xmax']-e['xmin'])*math.cos(math.radians(anchor['lat']))-1800)<1
        assert abs((e['ymax']-e['ymin'])*math.cos(math.radians(anchor['lat']))-1350)<1
        assert 'features' not in record and 'owner' not in record and 'power_mw' not in record
        assert im['license']=='Public domain' and im['license_url'].startswith('https://www.usgs.gov/')

def test_full_offline_download_remains_deliverable_without_git_lfs():
    assert (ROOT/'compute_atlas.html').stat().st_size<100*1024*1024
