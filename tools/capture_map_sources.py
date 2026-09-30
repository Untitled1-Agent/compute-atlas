"""Capture public, attributed source data; never infer facility geometry from a mockup.

Network acquisition is explicit and separate from the offline application build.
Only the public URLs below are requested. Raw CSVs and a hash manifest are retained.
"""
from __future__ import annotations
import csv, hashlib, io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'vendor' / 'epoch'
OUT.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(timezone.utc).isoformat()
manifest = {'retrieved_at': STAMP, 'publisher': 'Epoch AI', 'license': 'CC BY; credit Epoch AI', 'documentation': 'https://epoch.ai/data/data-centers-documentation', 'files': [], 'page_inventory': []}

def fetch(url):
    req = Request(url, headers={'User-Agent': 'ComputeAtlasResearch/1.0 (+https://github.com/Untitled1-Agent/compute-atlas)'})
    with urlopen(req, timeout=90) as r:
        return r.read(), r.headers.get('Last-Modified'), r.geturl()

url = 'https://epoch.ai/data/data_centers/data_centers.zip'
payload, modified, final = fetch(url)
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    for member in z.infolist():
        if member.is_dir() or not member.filename.lower().endswith('.csv'):
            continue
        name = Path(member.filename).name
        raw = z.read(member)
        (OUT/name).write_bytes(raw)
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        manifest['files'].append({'filename':name, 'url':url, 'archive_member':member.filename, 'last_modified':modified, 'sha256':hashlib.sha256(raw).hexdigest(), 'rows':len(rows), 'fields':list(rows[0]) if rows else [], 'sample':rows[:1]})
        print(name, len(rows), 'rows', list(rows[0]) if rows else [])
        print('SAMPLE',json.dumps(rows[:1],ensure_ascii=False)[:18000])

for slug in ['anthropic-amazon-new-carlisle','coreweave-helios','openai-stargate-abilene','microsoft-fairwater-wisconsin','alibaba-zhangbei','huawei-horinger']:
    url = 'https://epoch.ai/data/ai-data-centers/directory/'+slug
    try:
        raw, modified, final = fetch(url)
        text=raw.decode('utf-8')
        # Inspection snippets are public page metadata, not a scrape of licensed satellite imagery.
        snippets=[]
        for term in ['latitude','longitude','coordinates','bounds','satellite','geojson','imageUrl']:
            found=list(re.finditer(term,text,re.I))
            snippets.extend({'term':term,'text':text[max(0,m.start()-120):m.start()+450]} for m in found[:3])
        scripts=re.findall(r'<script[^>]*src=[\"\x27]([^\"\x27]+)',text)
        entry={'slug':slug,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'last_modified':modified,'snippets':snippets,'scripts':scripts}
        manifest['page_inventory'].append(entry)
        print('PAGE',slug,json.dumps(entry,ensure_ascii=False)[:14000])
    except Exception as exc:
        manifest['page_inventory'].append({'slug':slug,'url':url,'error':str(exc)})
        print('PAGE FAILED',slug,str(exc))
(OUT/'capture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Capture complete. Data must be interpreted using explicit IT/facility power boundaries.')
