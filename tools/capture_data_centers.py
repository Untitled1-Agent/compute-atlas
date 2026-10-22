"""Losslessly normalize all six tables in Epoch AI's CC BY data-center ZIP."""
from __future__ import annotations
import argparse, base64, collections, csv, hashlib, io, json, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
URL='https://epoch.ai/data/data_centers/data_centers.zip'
TABLES={'centers':('data_centers.csv','AI data centers','Name'),'timelines':('data_center_timelines.csv','Development timelines','Data center'),'deployments':('data_center_chip_quantities.csv','Chip deployments','Handle'),'chillers':('data_center_chillers.csv','Chillers','Model'),'towers':('data_center_cooling_towers.csv','Cooling towers','Model'),'chips':('chip_types.csv','Accelerator reference','Name')}
def normalize(raw,captured_at,published_at):
    z=zipfile.ZipFile(io.BytesIO(raw));tables={};manifest=[]
    if sum(i.file_size for i in z.infolist())>30_000_000:raise ValueError('Excessive expanded archive')
    readme=z.read('README.md').decode()
    if 'https://creativecommons.org/licenses/by/4.0/' not in readme:raise ValueError('Expected redistribution license absent')
    for key,(filename,label,name_field) in TABLES.items():
        body=z.read(filename);reader=csv.DictReader(io.StringIO(body.decode('utf-8-sig')));columns=reader.fieldnames;rows=list(reader)
        if not rows or name_field not in columns:raise ValueError('Incomplete source table: '+key)
        occurrences=collections.Counter();records=[]
        for index,row in enumerate(rows,1):
            if None in row or any(v is None for v in row.values()):raise ValueError('Truncated CSV row')
            version=hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            identity=hashlib.sha256(row[name_field].encode()).hexdigest() if key=='centers' else version
            occurrences[identity]+=1
            if key=='centers' and occurrences[identity]>1:raise ValueError('Duplicate center identity')
            records.append({'id':'epoch-dc-'+key+'-'+identity[:20]+('' if key=='centers' else '-'+str(occurrences[identity])),
                'name':row[name_field] or ('Source row '+str(index)),'source_row':index,'source_version':version,'fields':row})
        tables[key]={'label':label,'filename':filename,'columns':columns,'records':records}
        manifest.append({'filename':filename,'rows':len(rows),'columns':len(columns),'sha256':hashlib.sha256(body).hexdigest()})
    return {'schema_version':1,'publisher':'Epoch AI','title':'AI data centers','url':'https://epoch.ai/data/ai-data-centers','download_url':URL,'captured_at':captured_at,'published_at':published_at,
        'license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':'Epoch AI, AI data centers (2026). Normalized for Compute Atlas; all original fields and archive bytes preserved.',
        'policy':'Complete captured public publication. Source models and timeline projections are not live telemetry or independently verified operating capacity. Native IT power, facility power, costs and hardware counts remain distinct. Equipment reference tables do not establish installed equipment at a campus. No cross-collection identity match is inferred.',
        'source_sha256':hashlib.sha256(raw).hexdigest(),'source_readme':readme,'archive_base64':base64.b64encode(raw).decode(),'manifest':manifest,'tables':tables}
def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--input',type=Path);p.add_argument('--published-at',required=True);a=p.parse_args()
    if a.input:raw=a.input.read_bytes()
    else:
        with urllib.request.urlopen(URL,timeout=45) as r:raw=r.read(10_000_001)
        if len(raw)>10_000_000:raise ValueError('Archive exceeds limit')
    d=normalize(raw,datetime.now(timezone.utc).isoformat(),a.published_at);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(d['manifest']))
if __name__=='__main__':main()
