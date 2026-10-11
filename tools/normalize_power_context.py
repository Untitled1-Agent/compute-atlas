"""Normalize a bounded public OSM capture; preserve native tags and full ways.

Display paths are clipped independently. Edit time is not a survey/operating date.
No project identity, power allocation, operator match or circuit is inferred.
"""
import hashlib,json,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

BBOX=(-100.90,33.75,-100.83,33.80)
QUERY='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,BBOX))

def clip_segment(a,b,bounds=BBOX):
    xmin,ymin,xmax,ymax=bounds;dx=b[0]-a[0];dy=b[1]-a[1];lo,hi=0.,1.
    for p,q in [(-dx,a[0]-xmin),(dx,xmax-a[0]),(-dy,a[1]-ymin),(dy,ymax-a[1])]:
        if not p:
            if q<0:return None
        else:
            t=q/p
            if p<0:lo=max(lo,t)
            else:hi=min(hi,t)
            if lo>hi:return None
    return [[round(a[0]+lo*dx,7),round(a[1]+lo*dy,7)],[round(a[0]+hi*dx,7),round(a[1]+hi*dy,7)]]

def clip_paths(coords):
    paths=[]
    for a,b in zip(coords,coords[1:]):
        segment=clip_segment(a,b)
        if not segment or segment[0]==segment[1]:continue
        if paths and paths[-1][-1]==segment[0]:paths[-1].append(segment[1])
        else:paths.append(segment)
    return paths

def normalize(raw,captured_at):
    root=ET.fromstring(raw);nodes={x.attrib['id']:x for x in root.findall('node')};features=[]
    for way in root.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
        if tags.get('power') not in ('line','minor_line','substation'):continue
        refs=[n.attrib['ref'] for n in way.findall('nd')]
        if not refs or any(ref not in nodes for ref in refs):raise ValueError('Incomplete source way '+way.attrib['id'])
        coords=[[float(nodes[ref].attrib['lon']),float(nodes[ref].attrib['lat'])] for ref in refs]
        if any(not(-180<=x<=180 and -90<y<90) for x,y in coords):raise ValueError('Invalid source coordinates')
        paths=clip_paths(coords)
        if not paths:continue
        area=tags['power']=='substation'
        if area and (len(coords)<4 or coords[0]!=coords[-1]):raise ValueError('Substation area is not a closed way')
        sid=way.attrib['id']
        features.append({'id':'osm-way-'+sid,'osm_type':'way','osm_id':int(sid),'version':int(way.attrib['version']),'edited_at':way.attrib['timestamp'],'tags':tags,'node_refs':refs,'geometry':{'type':'Polygon' if area else 'LineString','coordinates':[coords] if area else coords},'display_paths':paths,'url':'https://www.openstreetmap.org/way/'+sid})
    if not features:raise ValueError('Empty capture cannot replace the context snapshot')
    return {'schema_version':1,'collection':'Bounded community electricity context','license':'ODbL-1.0','attribution':'© OpenStreetMap contributors','license_url':'https://www.openstreetmap.org/copyright','captured_at':captured_at,'coverage_bbox':list(BBOX),'query_url':QUERY,'response_sha256':hashlib.sha256(raw).hexdigest(),'method':'Complete OSM ways with native tags; independent display-path clipping to query bounds. Editor account metadata excluded.','policy':'Community mapping, not a survey, operating-status confirmation, project ownership, service connection or IT-capacity measurement. Edit times are not commissioning or image dates. Coverage is partial; absence is not proof of absence.','features':features}

if __name__=='__main__':
    source=Path(sys.argv[1]);out=Path(sys.argv[2]);date=sys.argv[3] if len(sys.argv)>3 else datetime.fromtimestamp(source.stat().st_mtime,timezone.utc).isoformat()
    data=normalize(source.read_bytes(),date);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f"{len(data['features'])} independently sourced context features; no capacity records added")
