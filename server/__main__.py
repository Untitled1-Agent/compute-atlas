"""python -m server: local service, capture, editorial review, export and backup."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from .store import ROOT, Store, canonical


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=Path(os.getenv('ATLAS_DB',str(ROOT/'var/atlas.sqlite3'))))
    sub=parser.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve'); serve.add_argument('--host',default='127.0.0.1'); serve.add_argument('--port',type=int,default=8000); serve.add_argument('--no-refresh',action='store_true')
    refresh=sub.add_parser('refresh'); refresh.add_argument('--limit',type=int,default=20)
    sub.add_parser('status')
    export=sub.add_parser('export'); export.add_argument('path',type=Path)
    backup=sub.add_parser('backup'); backup.add_argument('path',type=Path)
    submit=sub.add_parser('submit'); submit.add_argument('kind',choices=['observation','fact','relationship','discovery']); submit.add_argument('path',type=Path); submit.add_argument('--actor',required=True)
    review=sub.add_parser('review'); review.add_argument('id'); review.add_argument('decision',choices=['accepted','rejected']); review.add_argument('--actor',required=True); review.add_argument('--reason',required=True)
    queue=sub.add_parser('queue'); queue.add_argument('--limit',type=int,default=100); queue.add_argument('--offset',type=int,default=0)
    resolve=sub.add_parser('resolve'); resolve.add_argument('id'); resolve.add_argument('decision',choices=['acknowledged','rejected']); resolve.add_argument('--actor',required=True); resolve.add_argument('--reason',required=True)
    args=parser.parse_args()
    if args.command=='serve':
        import uvicorn
        from .app import create_app
        uvicorn.run(create_app(args.db,background=not args.no_refresh),host=args.host,port=args.port,workers=1)
        return
    store=Store(args.db); store.seed()
    if args.command=='refresh':
        from .acquire import Monitor
        monitor=Monitor(store,args.db.parent/'blobs')
        try:
            for _ in range(max(0,min(args.limit,500))):
                if not monitor.run_once(): break
        finally: monitor.close()
        print(json.dumps(store.status(),indent=2))
    elif args.command=='status': print(json.dumps(store.status(),indent=2))
    elif args.command=='queue': print(json.dumps(store.queue(min(100,max(1,args.limit)),max(0,args.offset)),indent=2))
    elif args.command=='export':
        args.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=args.path.with_suffix(args.path.suffix+'.tmp'); tmp.write_text(json.dumps(store.publication(),indent=2,ensure_ascii=False)+'\n'); os.replace(tmp,args.path)
        print(f'Exported accepted publication to {args.path}; rebuild standalone after a reviewed repository update.')
    elif args.command=='backup': store.backup(args.path)
    elif args.command=='submit': store.submit_claim(args.kind,json.loads(args.path.read_text()),args.actor)
    elif args.command=='review': store.decide(args.id,args.decision,args.actor,args.reason)
    elif args.command=='resolve': store.resolve_queue(args.id,args.decision,args.actor,args.reason)

if __name__=='__main__': main()
