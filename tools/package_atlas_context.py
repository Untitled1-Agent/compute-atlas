"""Package bounded context into independently loadable, checksum-pinned chunks."""
import base64,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=json.loads((ROOT/'work/global-context.json').read_text())
    from capture_atlas_context import anchors
    expected={id for p in anchors() for id in p['ids']}
    captured={id for c in source['captures'] for p in c['anchors'] for id in p['ids']}
    if source['failures'] or expected!=captured:raise ValueError('Context capture is incomplete; accepted publication was not replaced')
    directory=ROOT/'data/layers/global-context';directory.mkdir(exist_ok=True)
    index={k:v for k,v in source.items() if k not in ['elements','captures']}
    index.update(feature_count=len(source['elements']),anchor_count=sum(len(c['anchors']) for c in source['captures']),captures=[])
    countries=set()
    for capture in source['captures']:
        raw=(ROOT/'work/context-captures'/f'{capture["id"]}.json').read_bytes()
        compressed=gzip.compress(raw,compresslevel=9,mtime=0);path=directory/(capture['id']+'.json.gz');path.write_bytes(compressed)
        meta={k:v for k,v in capture.items() if k!='element_ids'}
        meta.update(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(compressed).hexdigest(),feature_count=len(capture['element_ids']),bytes=len(compressed))
        index['captures'].append(meta);countries.update(p['country'] for p in capture['anchors'])
    keep={Path(c['path']).name for c in index['captures']}
    for path in directory.glob('*.json.gz'):
        if path.name not in keep:path.unlink()
    index['countries']=sorted(countries)
    (ROOT/'data/layers/global-context-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    print(index['anchor_count'],'anchors;',index['feature_count'],'features;',len(countries),'countries;',sum(c['bytes'] for c in index['captures']),'compressed bytes')

if __name__=='__main__':main()
