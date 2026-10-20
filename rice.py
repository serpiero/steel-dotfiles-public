#!/usr/bin/env python3
"""Optional compositor palette profiles; never controls background services."""
from pathlib import Path
import argparse, fcntl, os, subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parent
# Resolve a single active compositor even when invoked from an external terminal.
if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
    try:
        instances = __import__('json').loads(subprocess.check_output(['hyprctl','instances','-j'],text=True))
        if len(instances)==1:
            os.environ.update(HYPRLAND_INSTANCE_SIGNATURE=instances[0]['instance'], WAYLAND_DISPLAY=instances[0]['wl_socket'])
            os.environ.setdefault('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
            os.environ.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus')
    except Exception: pass
CONFIG = Path.home()/'.config/hypr/hyprland.lua'
PROFILES = {'ii': 'Illogical Impulse — original', 'obsidian': 'Steel — dark tactical'}

def atomic(path, data):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.rice-')
    try:
        with os.fdopen(fd,'w') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def check(profile):
    env = dict(os.environ, RICE_PROFILE_VERIFY=profile, RICE_ROOT=str(ROOT))
    result = subprocess.run(['Hyprland','--verify-config','-c',str(CONFIG)],env=env,capture_output=True,text=True,timeout=30)
    if result.returncode or 'config ok' not in result.stdout:
        raise RuntimeError(result.stdout + result.stderr)
    print(profile + ': configuración válida')

def select(profile):
    if profile not in PROFILES: raise ValueError('Perfil desconocido')
    with (ROOT/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for candidate in PROFILES: check(candidate)
        previous = (ROOT/'active').read_text().strip()
        active_session = bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'))
        if active_session:
            errors = subprocess.check_output(['hyprctl','configerrors'],text=True,timeout=10).strip()
            if errors: raise RuntimeError('Resuelve primero los errores actuales: '+errors)
        atomic(ROOT/'active',profile+'\n')
        if active_session:
            try:
                subprocess.run(['hyprctl','reload'],check=True,capture_output=True,text=True,timeout=15)
                errors = subprocess.check_output(['hyprctl','configerrors'],text=True,timeout=10).strip()
                if errors: raise RuntimeError(errors)
                subprocess.run(['python3',str(ROOT/'session.py'),'sync'],check=True,timeout=30)
            except Exception:
                atomic(ROOT/'active',previous+'\n')
                subprocess.run(['hyprctl','reload'],capture_output=True,timeout=15)
                subprocess.run(['python3',str(ROOT/'session.py'),'sync'],capture_output=True,timeout=30)
                raise
        print(PROFILES[profile]+(' aplicado.' if active_session else ' preparado para la próxima sesión de Hyprland.'))

parser=argparse.ArgumentParser()
parser.add_argument('action', choices=['menu','check','status','set','terminal','launcher'])
parser.add_argument('profile',nargs='?',choices=list(PROFILES))
args=parser.parse_args()
try:
    if args.action=='check':
        for profile in PROFILES: check(profile)
    elif args.action=='status': print((ROOT/'active').read_text().strip())
    elif args.action=='set':
        if not args.profile: parser.error('set requiere un perfil')
        select(args.profile)
    elif args.action=='terminal': subprocess.run(['kitty','--config',str(ROOT/'obsidian/kitty.conf')],check=True)
    elif args.action=='launcher': subprocess.run(['rofi','-no-config','-theme',str(ROOT/'menu.rasi'),'-show','drun'],check=True)
    else:
        labels=list(PROFILES.values())
        r=subprocess.run(['rofi','-no-config','-theme',str(ROOT/'menu.rasi'),'-dmenu','-no-custom','-format','i','-p','Perfil','-mesg','Perfil completo: ventanas, barra, wallpaper y notificaciones.'],input='\n'.join(labels),text=True,capture_output=True)
        if r.returncode==0 and r.stdout.strip(): select(list(PROFILES)[int(r.stdout.strip())])
except Exception as e:
    print(str(e),file=sys.stderr)
    if args.action=='menu': subprocess.run(['notify-send','Selector de perfiles',str(e)],capture_output=True)
    sys.exit(1)
