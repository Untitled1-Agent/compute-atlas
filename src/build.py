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
for key,path in [('CSS','src/styles.css'),('JS','src/app.js')]:
    template=template.replace('/*__'+key+'__*/',(ROOT/path).read_text())
for key,path in [('DATA','data/atlas.json'),('ARCHIVE','data/archive.json'),('WORLD','data/world.json')]:
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
# The embedded attachment JSON appears before app logic starts.
marker='<script type="application/json" id="atlas-data">'
template=template.replace(marker,'<script type="application/json" id="original-files">'+safe_json(files)+'</script>'+marker)
if '/*__' in template:raise ValueError('Unreplaced build placeholder')
output=ROOT/'compute_atlas.html'
output.write_text(template)
print(f'Built {output} ({output.stat().st_size/1048576:.2f} MiB)')
