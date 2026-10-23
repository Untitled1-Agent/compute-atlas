"""Capture public-domain NAIP context at published US compute coordinates.

Images describe a dated geographic window, not a verified campus boundary or
building inventory. Native raster metadata, export recipes and bytes are kept.
Network acquisition is explicit; the application build never uses the network.
"""
import concurrent.futures, hashlib, io, json, math, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/maps/anchor-imagery'
SERVICE = 'https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer'
LICENSE = 'https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip'
IMAGE_QUALITY = 68  # Native server export, with room for the complete offline archive.

def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'ComputeAtlas/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(2 * (attempt + 1))

def capture(anchor):
    key = hashlib.sha256(f'{anchor["lat"]:.5f},{anchor["lon"]:.5f}'.encode()).hexdigest()[:20]
    path = OUT / (key + '.json')
    previous = None
    if path.exists():
        cached = json.loads(path.read_text())
        if cached.get('image') and (ROOT / cached['image']['path']).exists():
            previous = cached
            if f'compressionQuality={IMAGE_QUALITY}' in cached['export_url']: return cached
    result = {'id':key, 'anchor':anchor, 'captured_at':datetime.now(timezone.utc).isoformat(), 'status':'unavailable'}
    try:
        lon, lat = anchor['lon'], anchor['lat']
        x = 6378137 * math.radians(lon)
        y = 6378137 * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        span = 900 / math.cos(math.radians(lat))
        bbox = [x-span, y-span*.75, x+span, y+span*.75]
        params = {'f':'json', 'where':'Category=1', 'geometry':','.join(map(str,bbox)), 'geometryType':'esriGeometryEnvelope', 'inSR':3857, 'spatialRel':'esriSpatialRelIntersects', 'outFields':'*', 'returnGeometry':'true', 'outSR':3857, 'orderByFields':'acquisition_date DESC', 'resultRecordCount':100}
        query = SERVICE + '/query?' + urllib.parse.urlencode(params)
        catalog = json.loads(fetch(query))
        if catalog.get('error'): raise ValueError(str(catalog['error']))
        rows = catalog.get('features', [])
        if not rows: raise ValueError('No native NAIP raster intersects this window')
        year = max(r['attributes']['Year'] for r in rows)
        chosen = [r for r in rows if r['attributes']['Year'] == year]
        ids = [r['attributes']['OBJECTID'] for r in chosen]
        if len(ids) > 20: raise ValueError('Source mosaic exceeds 20-raster bound')
        dates = sorted({datetime.fromtimestamp(r['attributes']['acquisition_date']/1000, timezone.utc).date().isoformat() for r in chosen if r['attributes'].get('acquisition_date') is not None})
        acquired = (' – '.join([dates[0], dates[-1]]) if len(dates)>1 else dates[0]) if dates else str(year)+' (day not supplied)'
        if dates and any(r['attributes'].get('acquisition_date') is None for r in chosen): acquired += ' · some raster dates unreported'
        recipe = {'f':'json', 'bbox':','.join(map(str,bbox)), 'bboxSR':3857, 'imageSR':3857, 'size':'1024,768', 'format':'jpg', 'compressionQuality':IMAGE_QUALITY, 'mosaicRule':json.dumps({'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':ids,'ascending':True}), 'renderingRule':json.dumps({'rasterFunction':'NaturalColor'})}
        export_url = SERVICE + '/exportImage?' + urllib.parse.urlencode(recipe)
        exported = json.loads(fetch(export_url))
        if exported.get('error'): raise ValueError(str(exported['error']))
        raw = fetch(exported['href'])
        from PIL import Image, ImageStat
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        if image.size != (1024,768) or max(ImageStat.Stat(image).stddev) < 4:
            raise ValueError('Empty or invalid native image export')
        pixels = list(image.resize((64,48)).getdata())
        if sum(min(p)>248 or max(p)<3 for p in pixels)/len(pixels) > .25:
            raise ValueError('Native export has excessive uncovered pixels')
        image_path = OUT / (key + '.jpg')
        image_path.write_bytes(raw)
        result.update(status='captured', query_url=query, catalog=catalog, selected_raster_ids=ids, export_url=export_url, export=exported, image={'path':str(image_path.relative_to(ROOT)), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw), 'width':1024, 'height':768, 'extent_3857':exported['extent'], 'acquired_at':acquired, 'acquisition_dates':dates, 'native_resolution_m':sorted({r['attributes']['resolution_value'] for r in chosen if r['attributes'].get('resolution_value') is not None}), 'publisher':'USDA NAIP / USGS National Map', 'license':'Public domain', 'license_url':LICENSE})
    except Exception as error:
        if previous: return previous
        result['reason'] = str(error)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    index=json.loads((ROOT/'data/layers/global-context-index.json').read_text())
    anchors=[a for c in index['captures'] for a in c['anchors'] if a['country']=='United States']
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(capture,anchors):
            records.append(result)
            print(f'{len(records)}/{len(anchors)} {result["status"]} {result["id"]} {result.get("reason","")}',flush=True)
    published=[]
    for record in records:
        item={k:v for k,v in record.items() if k not in ['catalog','export']}
        native_path=OUT/(record['id']+'.json');raw=native_path.read_bytes()
        item['metadata']={'path':str(native_path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        published.append(item)
    publication={'schema_version':1,'captured_at':datetime.now(timezone.utc).isoformat(),'publisher':'USDA NAIP / USGS National Map','license':'Public domain','license_url':LICENSE,'policy':'Dated imagery around published source coordinates. This does not verify campus ownership, current condition, building identity, phase allocation or utility service. Native coordinates and raster acquisition dates retain their own provenance.','records':published}
    (ROOT/'data/maps/anchor-imagery.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'captured':sum(r['status']=='captured' for r in records),'total':len(records),'image_bytes':sum(r.get('image',{}).get('bytes',0) for r in records)}),flush=True)

if __name__=='__main__':main()
