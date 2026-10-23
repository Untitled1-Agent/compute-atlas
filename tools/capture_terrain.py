"""Publish a reproducible, public-domain geographic relief texture.

Requires Pillow. This is geospatial raster resampling; no synthetic map content.
"""
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://naturalearth.s3.amazonaws.com/50m_raster/NE2_50M_SR_W.zip'

def main():
    request = Request(URL, headers={'User-Agent': 'ComputeAtlas/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'})
    with urlopen(request, timeout=120) as response:
        archive_bytes = response.read(100 * 1024 * 1024 + 1)
    if len(archive_bytes) > 100 * 1024 * 1024:
        raise ValueError('Unexpected source archive size')
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        raster = archive.read('NE2_50M_SR_W/NE2_50M_SR_W.tif')
    image = Image.open(io.BytesIO(raster))
    if image.size != (10800, 5400):
        raise ValueError('Source grid changed; review its georeferencing first')
    target = ROOT / 'data/maps/terrain.webp'
    target.parent.mkdir(parents=True, exist_ok=True)
    image.resize((4096, 2048), Image.Resampling.LANCZOS).save(target, quality=84, method=6)
    manifest = {
        'publisher': 'Natural Earth', 'title': 'Natural Earth II with Shaded Relief and Water',
        'source_url': URL, 'license': 'Public domain',
        'license_url': 'https://www.naturalearthdata.com/about/terms-of-use/',
        'captured_at': datetime.now(timezone.utc).date().isoformat(),
        'source_sha256': hashlib.sha256(archive_bytes).hexdigest(),
        'source_raster_sha256': hashlib.sha256(raster).hexdigest(),
        'path': str(target.relative_to(ROOT)), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'width': 4096, 'height': 2048, 'projection': 'Geographic WGS84, equirectangular',
        'bounds': [-180, -90, 180, 90], 'scale': '1:50 million',
        'transformation': 'Lanczos downsample; WebP quality 84. Display tint and illumination are cartographic styling, not observed night lighting.'
    }
    target.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Published', target, target.stat().st_size, 'bytes')

if __name__ == '__main__':
    main()
