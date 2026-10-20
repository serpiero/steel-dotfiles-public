#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,os,shutil,datetime,sys
root=Path.home()/'.local/share/rice-profiles';manifest=root/'INSTALLATION.json'
if not manifest.exists():raise SystemExit('Only installations made by this portable installer can be restored here.')
m=json.loads(manifest.read_text());config=Path.home()/'.config/hypr/hyprland.lua';backup=Path(m['backup'])
if config.exists() and hashlib.sha256(config.read_bytes()).hexdigest()!=m['configSha256']:raise SystemExit('Hyprland entry point changed since installation; restore it manually from '+str(backup)+' to preserve your edits.')
if m['originalConfigExisted']:shutil.copy2(backup/'hyprland.lua',config)
else:config.unlink(missing_ok=True)
apps=Path.home()/'.local/share/applications'
for record in (root/'obsidian/application-style/desktop-backups').glob('*.json'):
 data=json.loads(record.read_text());target=apps/record.name[:-5]
 if target.exists() and str(root/'app-style.py') not in target.read_text():continue
 if data['hadOriginal']:target.write_text(data['original'])
 else:target.unlink(missing_ok=True)
link=Path.home()/'.config/quickshell/obsidian'
if link.is_symlink() and link.resolve()==root/'ui':link.unlink()
archive=backup/('removed-installation-'+datetime.datetime.now().strftime('%H%M%S'));shutil.move(root,archive)
print('Previous configuration restored. Local generated state was preserved at',archive,'\nLog out of Hyprland and back in to finish restoration. Firefox CSS and optional Spicetify installation have separate backups.')
