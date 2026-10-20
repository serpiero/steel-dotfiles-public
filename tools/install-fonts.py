#!/usr/bin/env python3
from pathlib import Path
import json,urllib.request,hashlib,tempfile,os,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/'.local/share/rice-profiles'
base=root/'ui/assets/fonts';meta=json.loads((base/'source.json').read_text());dst=base/'MaterialSymbolsRounded.ttf'
if dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest()==meta['sha256']:raise SystemExit(0)
url='https://raw.githubusercontent.com/google/material-design-icons/'+meta['revision']+'/'+urllib.parse.quote(meta['path'])
data=urllib.request.urlopen(url,timeout=60).read()
if hashlib.sha256(data).hexdigest()!=meta['sha256']:raise SystemExit('Material Symbols digest mismatch')
fd,name=tempfile.mkstemp(dir=base)
with os.fdopen(fd,'wb') as f:f.write(data)
os.replace(name,dst)
print('Verified Google Material Symbols installed locally.')
