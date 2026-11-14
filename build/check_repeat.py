#!/usr/bin/env python3
"""Fail if a repeated conversion changes any data file."""
import hashlib
import json
from pathlib import Path
import sys

def manifest(root):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(root)/'data').glob('*.json'))}
a,b=map(manifest,sys.argv[1:3])
result={'passed':a==b,'files':len(a),'changed':[k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)]}
p=Path(sys.argv[1])/'reports'/'idempotence.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));sys.exit(0 if result['passed'] else 2)
