#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp,os,json,sys,tempfile,fcntl
root=Path(__file__).resolve().parent
e=dict(os.environ)
if not e.get('HYPRLAND_INSTANCE_SIGNATURE'):
    instances=json.loads(sp.check_output(['hyprctl','instances','-j'],text=True))
    if len(instances)!=1:raise SystemExit('Se necesita una única sesión de Hyprland')
    e.update(HYPRLAND_INSTANCE_SIGNATURE=instances[0]['instance'],WAYLAND_DISPLAY=instances[0]['wl_socket'])
e.setdefault('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
e.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+e['XDG_RUNTIME_DIR']+'/bus')
cache=root/'ui/cache/screenshots';cache.mkdir(parents=True,exist_ok=True)
with (cache/'.capture-lock').open('w') as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit(0)
    monitor=next(m for m in json.loads(sp.check_output(['hyprctl','monitors','-j'],env=e)) if m['focused'])
    mode=sys.argv[1] if len(sys.argv)>1 else 'region'
    selection=None;scale=monitor['scale'];width=monitor['width']/scale;height=monitor['height']/scale
    if mode=='screen':selection=[0,0,width,height]
    elif mode=='window':
        win=json.loads(sp.check_output(['hyprctl','activewindow','-j'],env=e))
        if not win.get('address'):raise SystemExit(0)
        selection=[win['at'][0]-monitor['x'],win['at'][1]-monitor['y'],*win['size']]
    elif mode!='region':raise SystemExit('Usa region, window o screen')
    with tempfile.TemporaryDirectory(prefix='overlay-',dir=cache) as temp:
        image=Path(temp)/'screen.png';export=Path(temp)/'selected.png'
        sp.run(['grim','-o',monitor['name'],str(image)],env=e,check=True)
        e.update(OBSIDIAN_CAPTURE_IMAGE=str(image),OBSIDIAN_CAPTURE_EXPORT=str(export),OBSIDIAN_CAPTURE_MONITOR=monitor['name'],OBSIDIAN_CAPTURE_ROOT=str(root),OBSIDIAN_CAPTURE_SCALE=str(scale),OBSIDIAN_CAPTURE_SELECTION=json.dumps(selection) if selection else '')
        sp.run([str(root/'web-runtime/bin/qs'),'-p',str(root/'capture-ui')],env=e,check=True)
