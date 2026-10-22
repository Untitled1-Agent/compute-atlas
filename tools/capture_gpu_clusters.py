"""Capture the complete CC BY 4.0 Epoch AI public GPU-cluster publication.

No row is discarded, no anonymous cluster is identified, and source estimates
never enter the independently reviewed project capacity ledger.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, io, json, math, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = 'https://epoch.ai/data/gpu_clusters.csv'
PAGE = 'https://epoch.ai/data/gpu-clusters'
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
REQUIRED = {'Name','Country','Owner','Status','latitude','longitude','H100 equivalents','Power Capacity (MW)','Source 1','Superseded by'}

def number(value):
    if not str(value).strip(): return None
    try: n = float(value)
    except ValueError: raise ValueError('Invalid numeric source field')
    if not math.isfinite(n): raise ValueError('Non-finite source field')
    return n

def normalize(raw, captured_at, page_date=None):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    fields = reader.fieldnames or []
    if not REQUIRED.issubset(fields): raise ValueError('Source schema is incomplete')
    rows = list(reader)
    if not rows or len(rows)>50000: raise ValueError('Empty or excessive publication')
    counts=collections.Counter(); records=[]; named=set()
    for index, row in enumerate(rows, 1):
        if None in row or any(v is None for v in row.values()) or not row['Name']: raise ValueError('Incomplete CSV row')
        anonymous='anonymized' in row['Name'].lower()
        digest=hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        identity=digest if anonymous else hashlib.sha256(row['Name'].encode()).hexdigest()
        counts[identity]+=1
        if not anonymous and identity in named: raise ValueError('Ambiguous named cluster identity')
        named.add(identity)
        ident='epoch-'+identity[:20]+(('-'+str(counts[identity])) if anonymous else '')
        lat,lon=number(row['latitude']),number(row['longitude'])
        if (lat is None)!=(lon is None) or lat is not None and (abs(lat)>90 or abs(lon)>180): raise ValueError('Invalid coordinate pair')
        records.append({'id':ident,'name':row['Name'],'country':{'United States of America':'United States','Philippines (the)':'Philippines'}.get(row['Country'],row['Country']) or 'Not supplied',
            'operator':row['Owner'] or None,'status':row['Status'],'certainty':row['Certainty'],'sector':row['Sector'] or None,
            'lat':lat,'lon':lon,'place':row['Location'] or None,'date':row['First Operational Date'] or None,'anonymous':anonymous,
            'h100_equivalents':number(row['H100 equivalents']),'chips':number(row['Total number of AI chips']),
            'power_mw':number(row['Power Capacity (MW)']),'calculated_power_mw':number(row['Calculated Power Capacity (MW)']),
            'reported_power_mw':number(row['Reported Power Capacity (MW)']),
            'superseded_by':row['Superseded by'] or None,'builds_upon':row['Builds Upon'] or None,
            'source_urls':[row['Source '+str(i)] for i in range(1,6) if row['Source '+str(i)]],
            'source_row':index,'source_version':digest,'fields':row})
    return {'schema_version':1,'id':'epoch-gpu-clusters','publisher':'Epoch AI','title':'GPU clusters','url':PAGE,'download_url':URL,
        'documentation_url':'https://epoch.ai/data/gpu-clusters-documentation','license':'CC-BY-4.0','license_url':LICENSE,
        'attribution':'Epoch AI, Data on GPU clusters (2025), public dataset. Normalized for Compute Atlas; original fields preserved.',
        'captured_at':captured_at,'publisher_page_date':page_date,'source_sha256':hashlib.sha256(raw).hexdigest(),'columns':fields,
        'policy':'Complete captured public dataset, not a census or live inventory. Records include historical cluster phases and may overlap other collections. Power is Epoch reported or calculated cluster/facility power, not reviewed critical IT load. H100 equivalents are theoretical performance. Source-anonymized records remain anonymous; their content-based identities are publication-specific.',
        'counts':{'records':len(records),'countries':len({r['country'] for r in records if r['country']!='Not supplied'}),'mapped':sum(r['lat'] is not None for r in records),'anonymous':sum(r['anonymous'] for r in records),'superseded':sum(bool(r['superseded_by']) for r in records)},'records':records}

def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--input',type=Path);p.add_argument('--captured-at');p.add_argument('--publisher-page-date');a=p.parse_args()
    if a.input: raw=a.input.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'ComputeAtlasResearch/1.0'}),timeout=45) as response:
            raw=response.read(10_000_001)
        if len(raw)>10_000_000: raise ValueError('Source exceeds capture limit')
    publication=normalize(raw,a.captured_at or datetime.now(timezone.utc).isoformat(),a.publisher_page_date)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'epoch-gpu-clusters.csv').write_bytes(raw)
    (a.output/'gpu-clusters.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(publication['counts']))
if __name__=='__main__': main()
