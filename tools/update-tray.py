#!/usr/bin/env python3
"""Keep the optional native Arch/Cachy updater tray alive in this Hyprland session."""
from pathlib import Path
import os, re, shutil, subprocess

updater = shutil.which('cachy-update') or shutil.which('arch-update')
if not updater:
    raise SystemExit(0)
config = Path.home()/'.config/arch-update/arch-update.conf'
if config.exists():
    current = config.read_text()
    updated = re.sub(r'^([ \t]*)ShowTrayWhenRelevant[ \t]*$',
                     r'\1# ShowTrayWhenRelevant — Steel keeps the tray visible', current, flags=re.M)
    if current != updated:
        backup = config.with_suffix('.conf.before-steel-tray')
        if not backup.exists(): backup.write_text(current)
        config.write_text(updated)
unit = Path.home()/'.config/systemd/user/steel-update-tray.service'
text = f'''[Unit]
Description=Steel native updater tray
PartOf=graphical-session.target

[Service]
Type=forking
GuessMainPID=yes
Environment=XDG_CONFIG_HOME=%h/.config
Environment=QT_QPA_PLATFORM=wayland
ExecStart={updater} --tray
Restart=always
RestartSec=5
'''
if not unit.exists() or unit.read_text() != text:
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(text)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','start','steel-update-tray.service'],check=True)
