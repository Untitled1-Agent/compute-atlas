"""Bounded weekly primary directory capture. Output is never an accepted publication."""
from pathlib import Path
import sys,json,argparse
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.acquire import Monitor
from server.digital_realty import parse,SOURCE_URL


def capture(out):
    out.mkdir(parents=True,exist_ok=True)
    monitor=Monitor(None,out/'private',min_host_interval=3)
    try:
        status,headers,raw,final=monitor._get(SOURCE_URL,{'www.digitalrealty.com'})
        if status!=200 or 'html' not in headers.get('content-type',''):raise ValueError('Source is not successful HTML')
        candidate=parse(raw,captured_at=datetime.now(timezone.utc).isoformat(),final_url=final)
        (out/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'counts':candidate['counts'],'source_sha256':candidate['source_sha256'],'publication_unchanged':True}))
    except Exception as e:
        (out/'failure.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'error':str(e),'publication_unchanged':True}))
        raise
    finally:monitor.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);capture(p.parse_args().output)
