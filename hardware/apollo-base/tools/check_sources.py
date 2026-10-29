#!/usr/bin/env python3
"""Source publication checks. These do not test the phone hardware."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SOURCE-SHA256.json').read_text())
for name,expected in manifest.items():
    p=root/name
    assert p.resolve().is_relative_to(root) and p.is_file(),name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,name+' checksum mismatch'
    if p.suffix=='.png': continue  # Real captures were reviewed before publication.
    text=p.read_text(encoding='utf-8')
    # Split literal patterns here so the checker does not match its own source.
    assert '-----BEGIN '+'OPENSSH PRIVATE KEY-----' not in text,name
    assert not re.search(r'\bgh[pousr]_'+'[A-Za-z0-9]{30,}',text),name
    if p.suffix=='.py' or name=='system/install-persistent': ast.parse(text,filename=name)
    if text.startswith('#!/bin/bash'): subprocess.run(['bash','-n',str(p)],check=True)
    elif text.startswith('#!/bin/sh'): subprocess.run(['sh','-n',str(p)],check=True)
print(f'PASS: {len(manifest)} file checksums, Python parsing and shell syntax. No hardware claim.')
