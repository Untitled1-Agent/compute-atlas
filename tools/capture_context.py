"""Capture public-domain Natural Earth reference geography, not facility geometry.

Run explicitly or through context-data.yml. Source ZIP digests, feature counts,
retrieval times and license are retained. Generalized roads are NOT utility or
fiber corridors. Never infer parcels, building footprints, or exact site anchors.
"""
from __future__ import annotations
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import shapefile

ROOT = Path(__file__).resolve().parents[1]
LAYERS = {
    'coast': ('50m_physical', 'ne_50m_coastline'),
    'states': ('10m_cultural', 'ne_10m_admin_1_states_provinces_lines'),
    'roads': ('10m_cultural', 'ne_10m_roads'),
    'lakes': ('10m_physical', 'ne_10m_lakes'),
    'places': ('10m_cultural', 'ne_10m_populated_places'),
}
WINDOWS = [(-130, 22, -60, 53), (-15, 34, 38, 64), (73, 17, 136, 54)]


def intersects(bbox, windows=WINDOWS):
    a, b, c, d = bbox
    return any(a <= x1 and c >= x0 and b <= y1 and d >= y0 for x0, y0, x1, y1 in windows)


def thin(points, threshold):
    result = []
    for x, y in points:
        point = [round(x, 4), round(y, 4)]
        if not result or math.hypot(point[0] - result[-1][0], point[1] - result[-1][1]) >= threshold:
            result.append(point)
    if len(points) > 1:
        last = [round(points[-1][0], 4), round(points[-1][1], 4)]
        if result[-1] != last:
            result.append(last)
    return result


def main():
    output = {'schema_version': 1, 'attribution': 'Made with Natural Earth. Public domain. Generalized reference geography; not surveyed facility, utility or fiber geometry.',
              'license_url': 'https://www.naturalearthdata.com/about/terms-of-use/',
              'sources': [], 'coast': [], 'states': [], 'roads': [], 'lakes': [], 'places': []}
    for kind, (category, name) in LAYERS.items():
        url = f'https://naturalearth.s3.amazonaws.com/{category}/{name}.zip'
        request = Request(url, headers={'User-Agent': 'ComputeAtlasResearch/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'})
        with urlopen(request, timeout=90) as response:
            raw = response.read(40 * 1024 * 1024 + 1)
            if len(raw) > 40 * 1024 * 1024:
                raise ValueError('Source ZIP too large')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = {Path(p).suffix: p for p in archive.namelist() if Path(p).suffix in ('.shp', '.dbf', '.shx')}
            if sum(archive.getinfo(p).file_size for p in entries.values()) > 200 * 1024 * 1024:
                raise ValueError('Uncompressed source too large')
            reader = shapefile.Reader(**{ext[1:]: io.BytesIO(archive.read(path)) for ext, path in entries.items()}, encoding='utf-8', encodingErrors='replace')
            for record in reader.iterShapeRecords():
                shape, attrs = record.shape, record.record.as_dict()
                if not shape.points:
                    continue
                if kind == 'places':
                    if not shape.points:
                        continue
                    lon, lat = shape.points[0]
                    if int(attrs.get('POP_MAX') or 0) < 100000:
                        continue
                    output[kind].append({'name': attrs.get('NAMEASCII') or attrs.get('NAME'), 'lon': round(lon, 4), 'lat': round(lat, 4), 'rank': int(attrs.get('SCALERANK') or 10)})
                    continue
                if kind != 'coast' and not intersects(shape.bbox):
                    continue
                if kind == 'roads' and not intersects(shape.bbox, [WINDOWS[0]]):
                    continue
                parts = list(shape.parts) + [len(shape.points)]
                for begin, end in zip(parts, parts[1:]):
                    line = thin(shape.points[begin:end], .035 if kind == 'coast' else .018)
                    if len(line) >= 2:
                        output[kind].append(line)
        output['sources'].append({'layer': kind, 'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'retrieved_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'features': len(output[kind]), 'scale': '1:50m' if kind == 'coast' else '1:10m', 'license': 'Public domain'})
        print(kind, len(output[kind]), hashlib.sha256(raw).hexdigest(), flush=True)
    target = ROOT / 'data/context.json'
    target.write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
    print('Wrote', target, target.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
