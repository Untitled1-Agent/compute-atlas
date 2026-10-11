"""Build the offline, dependency-free Compute Atlas HTML.

Run from anywhere with Python 3.10+. All UI, structured data, world geometry,
report figures and original research files are embedded. No network is required.
"""
import base64,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def safe_json(x):
    return json.dumps(x,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
template=(ROOT/'src/index.html').read_text()
css='\n'.join((ROOT/p).read_text() for p in ('src/styles.css','src/enhancements.css','src/zoom-explorer.css','src/evidence-desk.css','src/source-health.css','src/global-coverage.css','src/site-identity.css','src/catalog-explorer.css','src/operator-directory.css','src/publisher-explorer.css','src/project-research.css','src/experience.css'))
js='\n'.join((ROOT/p).read_text() for p in ('src/directory-schema.js','src/digital-realty-schema.js','src/spatial-math.js','src/pointer-gestures.js','src/app.js','src/enhancements.js','src/cartography.js','src/zoom-explorer.js','src/evidence-desk.js','src/service-client.js','src/source-health.js','src/global-coverage.js','src/site-identity.js','src/responsive-nav.js','src/facility-scene.js','src/catalog-explorer.js','src/operator-directory.js','src/publisher-explorer.js','src/project-research.js'))
template=template.replace('/*__CSS__*/',css).replace('/*__JS__*/',js)
for key,path in [('DATA','data/atlas.json'),('ARCHIVE','data/archive.json'),('WORLD','data/world.json'),('EVIDENCE','data/evidence.json'),('CONTEXT','data/context.json'),('CATALOG','data/catalog/osm.json'),('CATALOG_REVIEWS','data/catalog/reviews.json'),('OPERATOR_DIRECTORY','data/catalog/operator-directory.json'),('DIGITAL_REALTY','data/catalog/digital-realty.json')]:
    template=template.replace('/*__'+key+'__*/',safe_json(json.loads((ROOT/path).read_text())))
manifest=json.loads((ROOT/'data/manifest.json').read_text())
files={}
for item in manifest:
    path=ROOT/'originals'/item['filename']
    if not path.exists():path=Path('/mnt/data')/item['filename']
    content=path.read_bytes()
    if hashlib.sha256(content).hexdigest()!=item['sha256']:
        raise ValueError('Original-file checksum mismatch: '+str(path))
    files[item['filename']]=base64.b64encode(content).decode()
marker='<script type="application/json" id="atlas-data">'
template=template.replace(marker,'<script type="application/json" id="original-files">'+safe_json(files)+'</script>'+marker)
if '/*__' in template:raise ValueError('Unreplaced build placeholder')
output=ROOT/'compute_atlas.html'
output.write_text(template)
print(f'Built {output} ({output.stat().st_size/1048576:.2f} MiB)')
