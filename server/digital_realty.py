"""Publisher-listed locations, not a surveyed or operational-facility census."""
from __future__ import annotations
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime
from bs4 import BeautifulSoup

SOURCE_ID = 'DIR-DIGITAL-REALTY-LOCATIONS'
SOURCE_URL = 'https://www.digitalrealty.com/data-centers'
FILE = 'data/catalog/digital-realty.json'
KEYS = {'id','operator','code','name','source_region','source_country','metro','facility_type',
        'service_coverage','source_id','source_url','coordinates','it_mw',
        'source_node_id','source_title','source_continent'}


def timestamp(value):
    if not isinstance(value, str) or not re.search(r'(Z|[+-]\d\d:\d\d)$', value):
        raise ValueError('Timestamp requires a timezone')
    try:
        if datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Timestamp requires a timezone')
    except (TypeError, ValueError) as error:
        raise ValueError('Invalid timestamp') from error


def counts(rows):
    return {'records':len(rows),
            'countries':dict(sorted(Counter(r['source_country'] or 'Not specified' for r in rows).items())),
            'regions':dict(sorted(Counter(r['source_region'] for r in rows).items()))}


def validate(data):
    if not isinstance(data,dict) or type(data.get('schema_version')) is not int or data.get('schema_version')!=1:
        raise ValueError('Unsupported Digital Realty schema')
    if data.get('id')!=SOURCE_ID or data.get('publisher')!='Digital Realty' or data.get('url')!=SOURCE_URL or data.get('final_url')!=SOURCE_URL:
        raise ValueError('Unregistered Digital Realty source')
    if not re.fullmatch('[0-9a-f]{64}', str(data.get('source_sha256',''))):
        raise ValueError('Source identity is missing')
    timestamp(data.get('captured_at'))
    if type(data.get('parser_version')) is not int or data['parser_version']!=1 or data.get('published_at') is not None:
        raise ValueError('Unsupported source metadata')
    for k in ('title','rights','count_boundary','service_boundary'):
        if not isinstance(data.get(k),str) or not data[k].strip() or len(data[k])>2000:
            raise ValueError('Invalid source metadata')
    rows=data.get('records')
    if not isinstance(rows,list) or not 1<=len(rows)<=2000:
        raise ValueError('Invalid directory size')
    seen=set(); urls=set()
    for r in rows:
        if not isinstance(r,dict) or set(r)!=KEYS:raise ValueError('Unexpected publisher record fields')
        for k in KEYS-{'coordinates','it_mw','service_coverage','source_country','source_continent'}:
            if not isinstance(r[k],str) or not r[k].strip() or len(r[k])>500:raise ValueError('Invalid publisher text')
        for k in ('source_country','source_continent'):
            if r[k] is not None and (not isinstance(r[k],str) or not r[k].strip() or len(r[k])>500):raise ValueError('Invalid source geography')
        if not re.fullmatch(r'[1-9][0-9]*',r['source_node_id']) or r['id']!='digital-realty-'+r['source_node_id'] or r['id'] in seen:
            raise ValueError('Duplicate or malformed source identity')
        if r['operator']!='Digital Realty' or r['source_id']!=SOURCE_ID or r['name']!='Digital Realty '+r['source_title'].strip():
            raise ValueError('Publisher identity mismatch')
        if not re.fullmatch(r'https://www\.digitalrealty\.com/data-centers/(emea|americas|asia-pacific)/[a-z0-9-]+/[a-z0-9-]+',r['source_url']) or r['source_url'] in urls:
            raise ValueError('Unregistered or duplicate facility URL')
        if r['source_region'] not in ('EMEA','APAC','Americas') or r['service_coverage'] is not None or r['it_mw'] is not None:
            raise ValueError('Directory cannot certify IT load or availability')
        p=r['coordinates']
        if not isinstance(p,dict) or set(p)!={'lat','lon','basis'} or p['basis']!='publisher_pin':raise ValueError('Invalid publisher pin')
        if any(type(p[k]) not in (int,float) or not math.isfinite(p[k]) for k in ('lat','lon')) or not -90<=p['lat']<=90 or not -180<=p['lon']<=180:
            raise ValueError('Invalid publisher coordinates')
        seen.add(r['id']);urls.add(r['source_url'])
    if data.get('counts')!=counts(rows):raise ValueError('Directory denominator mismatch')
    review=data.get('review')
    if review is not None:
        if not isinstance(review,dict) or not all(isinstance(review.get(k),str) and review[k].strip() for k in ('actor','note','reviewed_at')):raise ValueError('Invalid editorial review')
        timestamp(review['reviewed_at'])
    json.dumps(data,allow_nan=False)
    return data


def parse(raw, *, captured_at, final_url=SOURCE_URL):
    """Extract the public page's facilities array only, never metro centroids."""
    soup=BeautifulSoup(raw,'html.parser');nodes=soup.find_all('script',id='__NEXT_DATA__')
    if len(nodes)!=1:raise ValueError('Missing or ambiguous public page data')
    try: data=json.loads(nodes[0].string)['props']['pageProps']['data']; facilities=data['facilities']
    except (KeyError,TypeError,json.JSONDecodeError) as e:raise ValueError('Publisher schema changed') from e
    if not isinstance(facilities,list) or not 100<=len(facilities)<=2000:raise ValueError('Incomplete publisher directory')
    def one(r,key,optional=False):
        a=r.get(key)
        if optional and a==[]:return None
        if not isinstance(a,list) or len(a)!=1 or not isinstance(a[0],dict) or 'value' not in a[0]:raise ValueError('Malformed publisher field: '+key)
        return a[0]['value']
    rows=[]
    for r in facilities:
        loc=r.get('field_facility_location')
        if not isinstance(loc,list) or len(loc)!=1:raise ValueError('Ambiguous source locality')
        rows.append({'id':'digital-realty-'+r['node_id'],'operator':'Digital Realty',
            'code':one(r,'field_site_code_location',True) or r['title'].strip(),
            'name':'Digital Realty '+r['title'].strip(),'source_region':r['region'],
            'source_country':r['country'],'metro':r['metro'],'facility_type':'Publisher location entry',
            'service_coverage':None,'source_id':SOURCE_ID,'source_url':'https://www.digitalrealty.com'+r['url-alias'],
            'coordinates':{'lat':float(one(r,'field_latitude')),'lon':float(one(r,'field_longitude')),'basis':'publisher_pin'},
            'it_mw':None,'source_node_id':r['node_id'],'source_title':r['title'],
            'source_continent':loc[0].get('field_continent')})
    rows.sort(key=lambda r:r['id'])
    return validate({'schema_version':1,'id':SOURCE_ID,'publisher':'Digital Realty','url':SOURCE_URL,
        'final_url':final_url,'title':'Digital Realty data center locations',
        'captured_at':captured_at,'published_at':None,'review':None,'parser_version':1,
        'source_sha256':hashlib.sha256(raw).hexdigest(),
        'count_boundary':'Publisher location entries, including compound codes. Not unique buildings, current availability, the entire operator fleet or a global census.',
        'service_boundary':'Pins and locality labels are publisher data, not surveyed geometry or verified jurisdiction. Country headings contain inconsistencies; raw labels are retained. IT load and operational status are not established.',
        'rights':'Factual location fields extracted from the public Digital Realty directory. Source publication rights remain with Digital Realty. Independent from the ODbL community map.',
        'counts':counts(rows),'records':rows})
