#!/usr/bin/env python3
from pathlib import Path
import shutil,os
root=Path.home()/'.local/share/rice-profiles'
if not root.exists():raise SystemExit('Install Steel first.')
profile=root/'firefox/steel-profile'
profile.mkdir(parents=True,exist_ok=True,mode=0o700)
(profile/'chrome').mkdir(exist_ok=True)
for name in ['userChrome.css','userContent.css']:
 shutil.copy2(root/'obsidian/firefox'/name,profile/'chrome'/name)
user=profile/'user.js';s=user.read_text() if user.exists() else ''
pref='user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'
if pref not in s:user.write_text(s+'\n'+pref+'\n')
record=root/'firefox-profile-path';record.write_text(str(profile.resolve())+'\n');record.chmod(0o600)
print('Clean Steel Firefox profile prepared for Hyprland. KDE profile, cookies and browser preferences untouched. No sessions were copied. Start Firefox from its Steel launcher and configure Dark Reader with the public palette recipe.')
