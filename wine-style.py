#!/usr/bin/env python3
"""Display colors for an explicitly owned Hyprland Wine prefix."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
STYLE = ROOT / 'obsidian/application-style'


def registry(colors):
    roles = {'ActiveBorder':'high','ActiveTitle':'high','AppWorkSpace':'background','Background':'background',
        'ButtonFace':'background','ButtonText':'text','ButtonShadow':'low','ButtonHilight':'high',
        'GrayText':'muted','Hilight':'selection','HilightText':'text','HotTrackingColor':'accent',
        'InactiveBorder':'low','InactiveTitle':'low','InactiveTitleText':'muted','InfoText':'text',
        'InfoWindow':'high','Menu':'background','MenuText':'text','MenuHilight':'selection',
        'Scrollbar':'low','TitleText':'text','Window':'background','WindowFrame':'high','WindowText':'text'}
    text = 'Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\Control Panel\\Colors]\n'
    for name, token in roles.items():
        rgb = ' '.join(str(int(colors[token][i:i+2],16)) for i in (1,3,5))
        text += f'"{name}"="{rgb}"\n'
    return text + '\n[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\ThemeManager]\n"ThemeActive"="0"\n'


def apply(prefix=None, restore=False, runtime=None):
    owned = (STYLE / 'wine-prefix').resolve()
    prefix = Path(prefix or os.environ.get('WINEPREFIX', owned)).expanduser().resolve()
    if not prefix.is_relative_to(owned):
        return {'status':'shared-prefix-preserved'}
    colors = json.loads((ROOT/'obsidian/generated/spectrum.json').read_text())
    target = STYLE / 'native/wine-palette.reg'
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_suffix('.tmp');pending.write_text(registry(colors));pending.replace(target)
    if restore or not (prefix/'user.reg').exists():
        return {'status':'generated-prefix-not-initialized'}
    env = dict(os.environ, WINEPREFIX=str(prefix), WINEDEBUG='-all')
    env.pop('LD_PRELOAD', None)
    subprocess.run([str(runtime or '/usr/bin/wine'),'reg','import',str(target)],env=env,
                   capture_output=True,text=True,timeout=30,check=True)
    return {'status':'applied-owned-prefix'}


if __name__ == '__main__':
    print(json.dumps(apply(restore='--restore' in __import__('sys').argv)))
