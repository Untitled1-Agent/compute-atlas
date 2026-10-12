"""Throwaway, read-only Atlas visual design. Run: python tools/preview_atlas_design.py.

Three structural variants on /compute/?variant=A|B|C. No production modules,
API, database, private notes or authentication state are read or changed.
"""
import argparse
import base64
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / 'src/prototype-atlas'


def document():
    atlas = json.loads((ROOT / 'data/atlas.json').read_text())
    evidence = json.loads((ROOT / 'data/evidence.json').read_text())
    scenes = json.loads((ROOT / 'data/campus/scenes.json').read_text())['scenes']
    world = json.loads((ROOT / 'data/world.json').read_text())
    context = json.loads((ROOT / 'data/context.json').read_text())
    locations = json.loads((ROOT / 'data/catalog/osm.json').read_text())['records']
    project_ids = {'amazon-anthropic-new-carlisle', 'coreweave-helios'}
    site_keys = ['id', 'name', 'location', 'country', 'owner_label', 'company_ids',
                 'lat', 'lon', 'review', 'snapshot', 'target', 'sources', 'timeline']
    sites = [{k: s.get(k) for k in site_keys} for s in atlas['sites']]
    for scene in scenes:
        scene['image']['embedded'] = 'data:image/jpeg;base64,' + base64.b64encode(
            (ROOT / scene['image']['path']).read_bytes()).decode()
    def intersects(line):
        return any(-108 < x < -65 and 25 < y < 55 for x, y in line)
    payload = {'sites': sites, 'companies': atlas['companies'], 'world': world,
               'scenes': scenes, 'sources': evidence['sources'],
               'observations': [r for r in evidence['observations'] if r.get('site_id') in project_ids],
               'facts': [r for r in evidence['facts'] if r.get('site_id') in project_ids],
               'relationships': [r for r in evidence['relationships'] if r.get('site_id') in project_ids],
               'roads': [line for line in context['roads'] if intersects(line)],
               'states': [line for line in context['states'] if intersects(line)],
               'lakes': [line for line in context['lakes'] if intersects(line)],
               'locations': [{k: r[k] for k in ['id', 'lat', 'lon']} for r in locations],
               'places': [p for p in context['places'] if -108 < p['lon'] < -65 and 25 < p['lat'] < 55],
               'catalog_count': len(locations),
               'publication_date': evidence['published_at']}
    html = (PROTOTYPE / 'index.html').read_text()
    return html.replace('/* PROTOTYPE_CSS */', (PROTOTYPE / 'design.css').read_text()).replace(
        '/* PROTOTYPE_DATA */', 'const DATA=' + json.dumps(payload, separators=(',', ':')).replace('</', '<\\/') + ';').replace(
        '/* PROTOTYPE_JS */', (PROTOTYPE / 'design.js').read_text())


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.split('?')[0] not in ['/', '/compute/', '/compute/index.html']:
            self.send_error(404)
            return
        # Serve the exported study: do not repeatedly parse the full research
        # inputs inside the deliberately small preview-service memory cap.
        data = (ROOT / 'docs/design/atlas-redesign-review.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self.send_error(405)

    do_PUT = do_PATCH = do_DELETE = do_POST


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8142)
    parser.add_argument('--export', type=Path)
    args = parser.parse_args()
    if args.export:
        args.export.write_text(document())
        print(args.export)
    else:
        print(f'Atlas design prototype: http://127.0.0.1:{args.port}/compute/?variant=A', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
