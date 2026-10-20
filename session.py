#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp,os,json,time,signal,sys,fcntl
ROOT=Path(__file__).resolve().parent

def env():
    e=dict(os.environ)
    if not e.get('HYPRLAND_INSTANCE_SIGNATURE'):
        instances=json.loads(sp.check_output(['hyprctl','instances','-j'],text=True))
        if len(instances)!=1: raise RuntimeError('Se necesita una única sesión de Hyprland')
        i=instances[0]
        e.update(HYPRLAND_INSTANCE_SIGNATURE=i['instance'],WAYLAND_DISPLAY=i['wl_socket'])
    e.setdefault('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
    e.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+e['XDG_RUNTIME_DIR']+'/bus')
    e['XDG_CURRENT_DESKTOP']='Hyprland'
    e['XDG_SESSION_TYPE']='wayland'
    e['GDK_BACKEND']='wayland'
    e.setdefault('WAYLAND_DISPLAY','wayland-1')
    return e
E=env()
runtime_path=str(ROOT/"web-runtime/bin")
E["PATH"]=os.pathsep.join(p for p in E.get("PATH", "").split(os.pathsep) if p!=runtime_path)
if (ROOT/"active").read_text().strip()=="obsidian":
    E["PATH"]=str(ROOT/"web-runtime/bin")+os.pathsep+E.get("PATH", "")
    import importlib.util
    style_spec=importlib.util.spec_from_file_location('application_style',ROOT/'app-style.py')
    style_module=importlib.util.module_from_spec(style_spec)
    style_spec.loader.exec_module(style_module)
    style_module.prepare()
    E=style_module.environment(E)

def call(args,**kw): return sp.run(args,env=E,**kw)

def stop():
    for record in ROOT.glob('*.pid'):
        try:
            pid=int(record.read_text())
            cmd=Path(f'/proc/{pid}/cmdline').read_bytes()
            if str(ROOT).encode() in cmd or (record.stem=='ui' and cmd==b'qs\x00-c\x00obsidian\x00'): os.kill(pid,signal.SIGTERM)
        except (ValueError,FileNotFoundError,ProcessLookupError): pass
        record.unlink(missing_ok=True)
    time.sleep(.25)

def start(name,args):
    pidfile=ROOT/(name+'.pid')
    if pidfile.exists():
        try:
            pid=int(pidfile.read_text())
            cmd=Path(f'/proc/{pid}/cmdline').read_bytes()
            if str(ROOT).encode() in cmd or (name=='ui' and cmd==b'qs\x00-c\x00obsidian\x00'): return
        except (ValueError,FileNotFoundError): pass
    with (ROOT/(name+'.log')).open('a') as log:
        p=sp.Popen(args,env=E,stdout=log,stderr=log,start_new_session=True)
    pidfile.write_text(str(p.pid))
    time.sleep(.6)
    if p.poll() is not None: raise RuntimeError(name+' no inició; revisa '+str(ROOT/(name+'.log')))

def sync():
    profile=(ROOT/'active').read_text().strip()
    with (ROOT/'.session-lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if profile=='ii':
            stop()
            call(['qs','-c','ii','-n','-d'],check=True,capture_output=True,timeout=15)
            return
        # Only this configuration is stopped; other Quickshell apps are retained.
        call(['qs','kill','-c','ii'],capture_output=True,timeout=10)
        wall = (ROOT/'wallpaper-path').read_text().strip() if (ROOT/'wallpaper-path').exists() else str(ROOT/'obsidian/wallpaper.svg')
        stamp=ROOT/'palette-source.json'
        previous=json.loads(stamp.read_text()) if stamp.exists() else {}
        from theme import fingerprint
        if previous.get('theme')!=fingerprint(ROOT) or previous.get('wallpaper')!=wall or previous.get('mtime')!=Path(wall).stat().st_mtime_ns:
            from palette import palette
            palette(wall)
        start('wallpaper',[str(ROOT/'bin/swaybg'),'-i',wall,'-m','fill'])
        start('ui',[str(ROOT/'web-runtime/bin/qs'),'-c','obsidian'])
        call(['python3',str(ROOT/'tools/update-tray.py')],check=True,timeout=15)

def menu(items,prompt):
    r=call(['rofi','-no-config','-theme',str(ROOT/'menu.rasi'),'-dmenu','-no-custom','-p',prompt],input='\n'.join(items),text=True,capture_output=True)
    return r.stdout.strip() if r.returncode==0 else ''

def spotlight():
    # Match Overview's top margin in logical pixels, including scaled displays.
    monitors=json.loads(sp.check_output(['hyprctl','monitors','-j'],env=E,text=True))
    monitor=next((m for m in monitors if m.get('focused')),monitors[0])
    width=monitor['width']/monitor['scale']
    height=monitor['height']/monitor['scale']
    if monitor.get('transform',0) % 2: width,height=height,width
    geometry=(f'mainbox {{ width: {int(min(720,width-32))}px; }} '
              f'icon-dismiss-top {{ size: {int(max(96,height*.28))}px; }}')
    call(['rofi','-no-config','-theme',str(ROOT/'spotlight.rasi'),'-theme-str',geometry,'-show','drun'],check=False)

try:
    action=sys.argv[1]
    if action=='sync': sync()
    elif action=='stop': stop()
    elif action=='terminal': call(['kitty','--start-as=normal','--config',str(ROOT/'obsidian/kitty.conf')],check=True)
    elif action=='web-chat': call(['qs','-c','obsidian','ipc','call','sidebarLeft','open'],check=True)
    elif action=='settings': call([str(ROOT/'web-runtime/bin/qs'),'-p',str(ROOT/'ui/settings.qml')],check=True)
    elif action=='launcher': call(['rofi','-no-config','-theme',str(ROOT/'launcher.rasi'),'-show','drun'],check=True)
    elif action=='spotlight': spotlight()
    elif action=='windows': call(['rofi','-no-config','-theme',str(ROOT/'menu.rasi'),'-show','window'],check=True)
    elif action=='notifications': call(['qs','-c','obsidian','ipc','call','sidebarRight','toggle'],check=True)
    elif action=='lock': call(['hyprlock','-c',str(ROOT/'obsidian/hyprlock.conf')],check=True)
    elif action=='clipboard':
        entries=sp.check_output(['cliphist','list'],env=E,text=True)
        r=call(['rofi','-no-config','-theme',str(ROOT/'menu.rasi'),'-dmenu','-p','Portapapeles'],input=entries,text=True,capture_output=True)
        if r.returncode==0:
            data=sp.check_output(['cliphist','decode'],input=r.stdout.encode(),env=E)
            call(['wl-copy'],input=data,check=True)
    elif action=='screenshot': call(['python3',str(ROOT/'capture-overlay.py'),'region'],check=True)
    elif action=='wallpaper-set':
        files=[Path(arg).expanduser() for arg in sys.argv[2:] if not arg.startswith('--')]
        chosen=next((f.resolve() for f in files if f.is_file() and f.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.avif','.bmp','.svg')),None)
        if chosen:
            (ROOT/'wallpaper-path').write_text(str(chosen)+'\n')
            settings=ROOT/'ui/settings/config.json'
            data=json.loads(settings.read_text());data['background']['wallpaperPath']=str(chosen)
            settings.write_text(json.dumps(data,indent=2))
            record=ROOT/'wallpaper.pid'
            if record.exists():
                pid=int(record.read_text())
                if str(ROOT).encode() in Path(f'/proc/{pid}/cmdline').read_bytes(): os.kill(pid,signal.SIGTERM)
                record.unlink()
            sync()
        elif not any(arg in ('--noswitch','--mode','--color') for arg in sys.argv[2:]):
            call(['python3',str(ROOT/'session.py'),'wallpaper'],check=True)
    elif action=='wallpaper':
        wall=ROOT/'obsidian/wallpaper.svg'
        folders=[ROOT/'obsidian/wallpapers',Path.home()/'Pictures/Wallpapers']
        images={}
        for folder in folders:
            if folder.is_dir():
                for f in sorted(folder.rglob('*')):
                    if f.is_file() and f.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.avif','.bmp','.svg'):
                        images.setdefault(f.name,f.resolve())
        files=list(images.values())
        choices=['Obsidian Glass']+[f.name for f in files]
        selected=menu(choices,'Wallpaper')
        if selected:
            source=ROOT/'obsidian/wallpaper.svg' if selected=='Obsidian Glass' else files[choices.index(selected)-1]
            call(['python3',str(ROOT/'session.py'),'wallpaper-set',str(source)],check=True)
    elif action=='session':
        selected=menu(['Bloquear','Cerrar sesión','Cancelar'],'Sesión')
        if selected=='Bloquear': call(['hyprlock','-c',str(ROOT/'obsidian/hyprlock.conf')],check=True)
        elif selected=='Cerrar sesión':
            if menu(['Cancelar','Cerrar sesión'],'Confirmar cierre')=='Cerrar sesión': call(['hyprctl','dispatch','exit'],check=True)
    else: raise ValueError('Acción desconocida')
except Exception as e:
    print(e,file=sys.stderr)
    if len(sys.argv)>1 and sys.argv[1] not in ('sync','stop'):
        call(['notify-send','Obsidian',str(e)],capture_output=True)
    sys.exit(1)
