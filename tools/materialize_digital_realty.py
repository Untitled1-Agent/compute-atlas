"""Build only a hash-pinned, explicitly reviewed source projection. Never fetch latest."""
import hashlib,io,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.digital_realty import parse,validate

def materialize(receipt,archive):
    if len(archive)>10_000_000 or hashlib.sha256(archive).hexdigest()!=receipt['artifact_sha256']:raise ValueError('Review artifact mismatch')
    if receipt['member']!='global.html':raise ValueError('Unexpected source member')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        info=z.getinfo(receipt['member'])
        if info.file_size>3_000_000:raise ValueError('Source size limit')
        raw=z.read(info)
    if hashlib.sha256(raw).hexdigest()!=receipt['source_sha256']:raise ValueError('Source response mismatch')
    d=parse(raw,captured_at=receipt['captured_at'])
    if len(d['records'])!=receipt['expected_records']:raise ValueError('Reviewed denominator mismatch')
    d['review']=receipt['review'];validate(d)
    result=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
    if hashlib.sha256(result).hexdigest()!=receipt['publication_sha256']:raise ValueError('Reviewed projection mismatch')
    return result

def main():
    manifest=ROOT/'data/catalog/digital-realty-review.json'
    if not manifest.exists():return
    r=json.loads(manifest.read_text());target=ROOT/'data/catalog/digital-realty.json'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==r['publication_sha256']:
        validate(json.loads(target.read_text()));print('Reviewed Digital Realty snapshot matches; offline rebuild.');return
    repo=os.environ.get('GITHUB_REPOSITORY')
    if repo!='Untitled1-Agent/compute-atlas' or not os.environ.get('GITHUB_REF_NAME','').startswith('review/'):raise ValueError('Review branch required to retrieve source artifact')
    ident=r['artifact_id']
    if type(ident) is not int or ident<=0:raise ValueError('Invalid artifact ID')
    archive=subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{ident}/zip'],check=True,capture_output=True,timeout=60).stdout
    result=materialize(r,archive);tmp=target.with_suffix('.json.tmp');tmp.write_bytes(result);tmp.replace(target)
    print('Materialized exact reviewed publisher fields. CI must pass before commit.')

if __name__=='__main__':main()
