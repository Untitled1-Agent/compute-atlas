"""Build the offline, dependency-free Compute Atlas HTML.

Run from anywhere with Python 3.10+. All UI, structured data, world geometry,
report figures and original research files are embedded. No network is required.
"""
import base64,json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def safe_json(x):
    return json.dumps(x,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
template=(ROOT/'src/index.html').read_text()
css='\n'.join((ROOT/p).read_text() for p in ('src/styles.css','src/enhancements.css','src/zoom-explorer.css','src/evidence-desk.css','src/source-health.css','src/global-coverage.css','src/site-identity.css','src/catalog-explorer.css','src/operator-directory.css','src/publisher-explorer.css','src/project-research.css','src/experience.css'))
js='\n'.join((ROOT/p).read_text() for p in ('src/directory-schema.js','src/digital-realty-schema.js','src/spatial-math.js','src/pointer-gestures.js','src/app.js','src/enhancements.js','src/cartography.js','src/zoom-explorer.js','src/evidence-desk.js','src/service-client.js','src/source-health.js','src/global-coverage.js','src/site-identity.js','src/responsive-nav.js','src/facility-scene.js','src/catalog-explorer.js','src/operator-directory.js','src/publisher-explorer.js','src/project-research.js','src/atlas-workspace.js','src/campus-scene.js','src/map-layers.js'))
# Source-only updates also change release identity. Native browser integrity checks
# reject stale HTML receiving changed scripts, styles or publication JSON.
asset_paths=sorted({str(p.relative_to(ROOT)) for p in (ROOT/'src').iterdir() if p.suffix in ('.css','.js')})
asset_paths+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data').rglob('*') if p.is_file())
asset_hashes={path:hashlib.sha256((ROOT/path).read_bytes()).digest() for path in asset_paths}
integrity={path:'sha256-'+base64.b64encode(digest).decode() for path,digest in asset_hashes.items()}
asset_version=hashlib.sha256(safe_json({p:h.hex() for p,h in asset_hashes.items()}).encode()).hexdigest()[:12]
hosted_path=ROOT/'index.html'
hosted=hosted_path.read_text()
hosted=re.sub(r"const ASSET_VERSION='[^']*'",f"const ASSET_VERSION='{asset_version}'",hosted)
hosted=re.sub(r'const ASSET_INTEGRITY=.*?;\n',f'const ASSET_INTEGRITY={safe_json(integrity)};\n',hosted)
# Fetch initial module bytes in parallel while the loader executes in order.
preload_paths=list(dict.fromkeys(re.findall(r"loadScript\('([^']+)'\)",hosted)))
preloads='<!-- ATLAS_SCRIPT_PRELOADS -->\n'+'\n'.join('<link rel="preload" as="script" href="'+path+'?v='+asset_version+'" integrity="'+integrity[path]+'" crossorigin="anonymous">' for path in preload_paths)+'\n<!-- /ATLAS_SCRIPT_PRELOADS -->'
hosted,count=re.subn(r'<!-- ATLAS_SCRIPT_PRELOADS -->.*?<!-- /ATLAS_SCRIPT_PRELOADS -->',lambda match:preloads,hosted,flags=re.S)
if count!=1:raise ValueError('Missing initial script preload boundary')
hosted=re.sub(r'((?:href|src)="src/[^"?]+\.(?:css|js))(?:\?v=[^"]+)?(")',lambda m:m[1]+'?v='+asset_version+m[2],hosted)
def pin_tag(match):
    tag=match[0];path=re.search(r'(?:href|src)="(src/[^"?]+)',tag)[1]
    tag=re.sub(r' (?:integrity|crossorigin)="[^"]*"','',tag)
    return tag[:-1]+' integrity="'+integrity[path]+'" crossorigin="anonymous">'
hosted=re.sub(r'<(?:link|script)\b[^>]*(?:href|src)="src/[^"?]+\.(?:css|js)(?:\?v=[^"]+)?"[^>]*>',pin_tag,hosted)
hosted_path.write_text(hosted)
template=template.replace('/*__CSS__*/',css).replace('/*__JS__*/',js)
for key,path in [('CAMPUS_POWER_CONTEXT','data/layers/campus-power.json'),('POWER_REVIEWS','data/layers/helios-power-reviews.json'),('ROAD_CONTEXT','data/layers/helios-roads.json'),('POWER_CONTEXT','data/layers/helios-power.json'),('DATA','data/atlas.json'),('ARCHIVE','data/archive.json'),('WORLD','data/world.json'),('EVIDENCE','data/evidence.json'),('CONTEXT','data/context.json'),('CATALOG','data/catalog/osm.json'),('CATALOG_REVIEWS','data/catalog/reviews.json'),('OPERATOR_DIRECTORY','data/catalog/operator-directory.json'),('DIGITAL_REALTY','data/catalog/digital-realty.json')]:
    template=template.replace('/*__'+key+'__*/',safe_json(json.loads((ROOT/path).read_text())))
from campus_versions import validate_physical_versions
campus=json.loads((ROOT/'data/campus/scenes.json').read_text())
validate_physical_versions(campus)
for scene in campus['scenes']:
    image=scene['image'];content=(ROOT/image['path']).read_bytes()
    if hashlib.sha256(content).hexdigest()!=image['sha256']:
        raise ValueError('Campus imagery checksum mismatch: '+image['path'])
    image['data_url']='data:image/jpeg;base64,'+base64.b64encode(content).decode()
template=template.replace('/*__CAMPUS_SCENES__*/',safe_json(campus))
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
