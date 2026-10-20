#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1];bad=[];count=0
for p in root.rglob('*'):
 rel=p.relative_to(root)
 if '.git' in rel.parts:continue
 if p.is_symlink():bad.append(str(rel)+' (symlink: destination could be private)');continue
 if not p.is_file():continue
 count+=1
 if any(x in rel.parts for x in ('cache','__pycache__','clients','desktop-backups','backups','web-profile','screenshots')):bad.append(str(rel))
 if p.name in ('Cookies','History','Login Data','Visited Links','Trust Tokens','Preferences','installer.db','states.json','notes.txt','todo.json') or p.suffix in ('.sqlite','.sqlite3','.db','.pyc','.log','.pid','.so'):bad.append(str(rel))
 if rel.parts[:2]==('ui','state') and str(rel)!='ui/state/user/generated/colors.json':bad.append(str(rel))
 if rel.parts[:3]==('obsidian','application-style','config'):bad.append(str(rel))
 if p.suffix in ('.json','.qml','.lua','.conf','.sh','.rc','.ini'):
  s=p.read_text()
  if re.search(r'/home/[a-zA-Z0-9_.-]+/',s):bad.append(str(rel)+' (personal absolute path)')
  if re.search(r'\b(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_]{12,}',s):bad.append(str(rel)+' (credential pattern)')
config=json.loads((root/'ui/settings/config.json').read_text())
def secrets(v,path=''):
 if isinstance(v,dict):
  for k,value in v.items():
   name=path+'.'+k
   if re.search(r'^(api.?key|access.?token|password|secret|token)$',k,re.I) and value not in ('',None,False,[],{}):bad.append(name+' (configured secret)')
   secrets(value,name)
 elif isinstance(v,list):
  for item in v:secrets(item,path)
secrets(config)
if bad:print('\n'.join(sorted(set(bad))),file=sys.stderr);sys.exit(1)
print(f'Export audit passed: {count} source files; no caches, sessions or personal absolute paths.')
