"""Derive local road context from the same independently dated bounded capture."""
import json,sys
from pathlib import Path
from tools.normalize_power_context import normalize

if __name__=='__main__':
    source,out,date=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
    data=normalize(source.read_bytes(),date,kind='roads')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f"{len(data['features'])} independently sourced road ways; no public access or project match inferred")
