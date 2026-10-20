#!/usr/bin/env python3
"""Hyprland-only application palette. Personal settings are linked, never exported."""
import shlex
from pathlib import Path
import os, sys, json, re, shutil, configparser, tempfile, subprocess, importlib.util

ROOT = Path(__file__).resolve().parent
STYLE = ROOT / 'obsidian/application-style'
CONFIG = STYLE / 'config'
ORIGINAL = Path.home() / '.config'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, 'w') as f: f.write(value)
    os.replace(tmp, path)

def mirror(src, dst, exclude=()):
    dst.mkdir(parents=True, exist_ok=True)
    if not src.exists(): return
    for p in src.iterdir():
        if p.name in exclude: continue
        q = dst / p.name
        if not q.exists() and not q.is_symlink(): q.symlink_to(p)

def jsonc(text):
    # Remove comments outside strings; keep URLs and escaped quotes intact.
    out=[]; i=0; quoted=False; escaped=False
    while i<len(text):
        c=text[i]
        if quoted:
            out.append(c)
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
            i+=1; continue
        if c=='"': quoted=True; out.append(c); i+=1; continue
        if text[i:i+2]=='//':
            j=text.find('\n',i); i=len(text) if j<0 else j; continue
        if text[i:i+2]=='/*':
            j=text.find('*/',i+2); i=len(text) if j<0 else j+2; continue
        out.append(c); i+=1
    text=''.join(out); out=[]; i=0; quoted=False; escaped=False
    while i<len(text):
        c=text[i]
        if quoted:
            out.append(c)
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True; out.append(c)
        elif c==',':
            j=i+1
            while j<len(text) and text[j].isspace(): j+=1
            if j==len(text) or text[j] not in '}]': out.append(c)
        else: out.append(c)
        i+=1
    return json.loads(''.join(out))

def webkit_library():
    source=STYLE/'webkit-style.c'; library=STYLE/'webkit-style.so'
    if not source.exists(): return None
    if not library.exists() or source.stat().st_mtime_ns>library.stat().st_mtime_ns:
        flags=subprocess.run(['pkg-config','--cflags','--libs','webkit2gtk-4.1'],capture_output=True,text=True)
        if flags.returncode or not shutil.which('cc'): return None
        fd, temporary=tempfile.mkstemp(prefix='.webkit-style-',suffix='.so',dir=STYLE);os.close(fd)
        try:
            subprocess.run(['cc','-shared','-fPIC',str(source),'-o',temporary,*shlex.split(flags.stdout),'-ldl'],check=True,timeout=30)
            os.chmod(temporary,0o755);os.replace(temporary,library)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return library


def qbit_palette_library():
    source=ROOT/'styles/applications/qt-inactive-palette.cpp'
    library=STYLE/'qbittorrent/qt-inactive-palette.so'
    if not source.exists(): return None
    if not library.exists() or source.stat().st_mtime_ns>library.stat().st_mtime_ns:
        flags=subprocess.run(['pkg-config','--cflags','Qt6Widgets'],capture_output=True,text=True)
        compiler=shutil.which('c++')
        if flags.returncode or not compiler: return None
        library.parent.mkdir(parents=True,exist_ok=True)
        pending=library.with_suffix('.so.tmp')
        subprocess.run([compiler,'-shared','-fPIC','-std=c++17',str(source),'-o',str(pending),
                        *shlex.split(flags.stdout),'-ldl'],check=True,timeout=30)
        os.replace(pending,library)
    return library

def retroarch_client(args, e):
    client=STYLE/'clients/retroarch'
    binary=client/'retroarch'
    if not binary.exists(): return
    args[0]=str(binary)
    # Explicit user configurations take precedence over the default Steel copy.
    if any(x in ('-c','--config') or x.startswith('--config=') for x in args[1:]): return
    local=STYLE/'retroarch/config'
    config=local/'retroarch/retroarch.cfg'
    native=ORIGINAL/'retroarch'
    mirror(native,config.parent,('retroarch.cfg',))
    if not config.exists():
        write(config,(native/'retroarch.cfg').read_text() if (native/'retroarch.cfg').exists() else '')
    overlay=client/'steel.cfg'
    write(overlay,f'''# Generated cosmetic overrides; user settings stay in the private config copy.
assets_directory = "{client / 'assets'}"
menu_driver = "ozone"
ozone_menu_color_theme = "1"
menu_use_preferred_system_color_theme = "false"
ozone_font = ""
''')
    args[1:1]=['--config',str(config),'--appendconfig',str(overlay)]
    e['XDG_CONFIG_HOME']=str(local)

def aerion_environment(args, base):
    # Resolve past the rice wrapper exactly once; preserve the application's config identity.
    e=original_environment(base)
    executable=Path(args[0])
    wrapper=ROOT/'web-runtime/bin/aerion'
    if not executable.is_absolute() or executable.resolve()==wrapper.resolve():
        path=os.pathsep.join(p for p in e.get('PATH',os.defpath).split(os.pathsep) if Path(p).resolve()!=wrapper.parent.resolve())
        native=shutil.which('aerion',path=path)
        if not native: raise RuntimeError('Native Aerion executable missing')
        args[0]=native
    e['XDG_CONFIG_HOME']=str(ORIGINAL)
    library=webkit_library()
    if library:
        inherited=e.get('LD_PRELOAD','')
        e['LD_PRELOAD']=str(library)+(':'+inherited if inherited else '')
        e['OBSIDIAN_WEBKIT_CSS']=str(STYLE/'webkit.css')
    return e


def prepare():
    p=json.loads((ROOT/'obsidian/generated/spectrum.json').read_text())
    from theme import render, terminal
    render(ROOT, p)
    terminal_tokens = terminal(ROOT, p)
    terminal_text = terminal_tokens['foreground']; terminal_accent = terminal_tokens['accent']
    bg=p['background']; fg=p['text']; high=p['high']; sel=p['selection']; accent=p['accent']
    mirror(ORIGINAL,CONFIG,('gtk-3.0','gtk-4.0','kdeglobals','Code','MiniMeters','alacritty','qBittorrent','ktexteditorrc','katerc','kwriterc'))
    q=CONFIG/'kdeglobals'
    if not q.exists(): q.symlink_to(ROOT/'obsidian/app-settings/kdeglobals')
    webkit_library()
    write(STYLE/'gtk2.rc',f'''include "/usr/share/themes/Breeze-Dark/gtk-2.0/gtkrc"
gtk-color-scheme = "bg_color:{bg}\\nbase_color:{bg}\\nfg_color:{fg}\\ntext_color:{fg}\\nselected_bg_color:{sel}\\nselected_fg_color:{fg}"
''')
    for version in ('gtk-3.0','gtk-4.0'):
        src=ORIGINAL/version; dst=CONFIG/version
        mirror(src,dst,('gtk.css','colors.css','settings.ini'))
        c=configparser.ConfigParser(interpolation=None,strict=False); c.optionxform=str
        if (src/'settings.ini').exists(): c.read(src/'settings.ini')
        if not c.has_section('Settings'): c.add_section('Settings')
        c['Settings']['gtk-application-prefer-dark-theme']='true'
        c['Settings']['gtk-theme-name']='Breeze-Dark'
        from io import StringIO
        s=StringIO(); c.write(s,space_around_delimiters=False); write(dst/'settings.ini',s.getvalue())
        colors={'theme_bg_color':bg,'theme_base_color':bg,'theme_fg_color':fg,'theme_text_color':fg,
            'theme_selected_bg_color':sel,'theme_selected_fg_color':fg,'theme_unfocused_bg_color':bg,
            'theme_unfocused_base_color':bg,'theme_unfocused_fg_color':fg,'theme_unfocused_text_color':fg,
            'theme_unfocused_selected_bg_color':sel,'theme_unfocused_selected_fg_color':fg,
            'borders':high,'unfocused_borders':high,'accent_color':accent,'accent_bg_color':sel,
            'accent_fg_color':fg,'destructive_color':p['wine'],'destructive_bg_color':p['wine'],
            'destructive_fg_color':bg,'success_color':p['sage'],'success_bg_color':p['sage'],
            'success_fg_color':bg,'warning_color':p['warm'],'warning_bg_color':p['warm'],'warning_fg_color':bg}
        for surface in ('window','headerbar','card','sidebar','secondary_sidebar','view','overview','popover','dialog'):
            colors[surface+'_bg_color']=bg; colors[surface+'_fg_color']=fg
        for name in ('headerbar_backdrop_color','sidebar_backdrop_color','sidebar_border_color','secondary_sidebar_backdrop_color'): colors[name]=bg
        css='/* Obsidian: scoped GTK surfaces; existing fonts and widget geometry retained. */\n'
        css+=''.join(f'@define-color {k} {v};\n' for k,v in colors.items())
        if version=='gtk-4.0':
            css+=':root {\n'+''.join(f'  --{k.replace("_","-")}: {v};\n' for k,v in colors.items())+'}\n'
        css+=f'''window, .background, headerbar, .sidebar, .navigation-sidebar,
notebook > stack, scrolledwindow > viewport, .view, textview, textview text,
listview, columnview, popover > contents, .card {{ background-color: {bg}; color: {fg}; }}
headerbar {{ background-image: none; }}
row:selected, .navigation-sidebar row:selected {{ background-color: {sel}; color: {fg}; }}
selection {{ background-color: {sel}; color: {fg}; }}
'''
        write(dst/'gtk.css',css); write(dst/'colors.css',css)
    # VS Code: isolated settings; extensions, accounts and workspace state remain local.
    mirror(ORIGINAL/'Code', CONFIG/'Code', ('User','SingletonLock','SingletonSocket','SingletonCookie'))
    mirror(ORIGINAL/'Code/User',CONFIG/'Code/User',('settings.json','profiles'))
    code_src=ORIGINAL/'Code/User/settings.json'
    code_dst=CONFIG/'Code/User/settings.json'
    settings=jsonc(code_dst.read_text()) if code_dst.exists() else (jsonc(code_src.read_text()) if code_src.exists() else {})
    custom=settings.setdefault('workbench.colorCustomizations',{})
    for area in ('editor','sideBar','sideBarSectionHeader','activityBar','panel','statusBar','titleBar','tab','editorGroupHeader','breadcrumb','input','dropdown','menu','terminal','quickInput','settings','notifications','peekViewEditor','peekViewResult'):
        keys={'titleBar':['activeBackground','inactiveBackground'], 'tab':['activeBackground','inactiveBackground','unfocusedActiveBackground'], 'editorGroupHeader':['tabsBackground'],'terminal':['background'],'settings':['dropdownBackground','textInputBackground']}.get(area,['background'])
        for key in keys: custom[area+'.'+key]=bg
    custom.update({'editor.foreground':fg,'sideBar.foreground':fg,'activityBar.foreground':accent,
        'statusBar.foreground':fg,'titleBar.activeForeground':fg,'titleBar.inactiveForeground':p['muted'],
        'list.activeSelectionBackground':sel,'list.inactiveSelectionBackground':high,
        'list.hoverBackground':high,'editor.selectionBackground':sel,'focusBorder':accent,
        'panel.border':high,'sideBar.border':bg,'activityBar.border':bg,
        'terminal.foreground':terminal_text,'terminalCursor.foreground':terminal_accent})
    for key,value in list(custom.items()):
        if key.startswith('[') and isinstance(value,dict):
            value.update({k:v for k,v in custom.items() if not k.startswith('[')})
    write(CONFIG/'Code/User/settings.json',json.dumps(settings,indent=2)+'\n')
    profiles=CONFIG/'Code/User/profiles'
    if profiles.is_symlink(): profiles.unlink()
    profiles.mkdir(exist_ok=True)
    original_profiles=ORIGINAL/'Code/User/profiles'
    if original_profiles.exists():
        for src in original_profiles.iterdir():
            if not src.is_dir():continue
            dst=profiles/src.name;mirror(src,dst,('settings.json',))
            file=dst/'settings.json'
            cfg=jsonc(file.read_text()) if file.exists() else (jsonc((src/'settings.json').read_text()) if (src/'settings.json').exists() else {})
            profile_colors=cfg.setdefault('workbench.colorCustomizations',{})
            profile_colors.update({k:v for k,v in custom.items() if not k.startswith('[')})
            for key,value in profile_colors.items():
                if key.startswith('[') and isinstance(value,dict):value.update({k:v for k,v in custom.items() if not k.startswith('[')})
            write(file,json.dumps(cfg,indent=2)+'\n')
    # MiniMeters: only theme selection is changed in the isolated config copy.
    mirror(ORIGINAL/'MiniMeters',CONFIG/'MiniMeters',('settings.mms','Themes'))
    mirror(ORIGINAL/'MiniMeters/Themes',CONFIG/'MiniMeters/Themes')
    def rgb(c): return ','.join(str(int(c[i:i+2],16)) for i in (1,3,5))
    mm='credit = Obsidian fork\n\n[All]\n'+''.join(f'{k} = {rgb(v)}\n' for k,v in {'primary':accent,'secondary':p['muted'],'selection':sel,'text':fg,'background':bg,'background_secondary':bg}.items())
    write(CONFIG/'MiniMeters/Themes/Obsidian.ini',mm)
    mm_src=ORIGINAL/'MiniMeters/settings.mms'
    mm_dst=CONFIG/'MiniMeters/settings.mms'
    if mm_src.exists(): write(mm_dst,re.sub(r'string theme "[^"]*"','string theme "Obsidian"',(mm_dst if mm_dst.exists() else mm_src).read_text(),count=1))
    # Alacritty's palette override is imported after the original config.
    mirror(ORIGINAL/'alacritty',CONFIG/'alacritty',('alacritty.toml',))
    kitty=(ROOT/'obsidian/kitty.conf').read_text()
    ansi=[re.search(r'^color'+str(i)+r'\s+(#[0-9a-fA-F]{6})',kitty,re.M)[1] for i in range(16)]
    toml=f'[general]\nimport = ["{ORIGINAL}/alacritty/alacritty.toml"]\n[colors.primary]\nbackground = "{bg}"\nforeground = "{terminal_text}"\n[colors.cursor]\ntext = "{bg}"\ncursor = "{terminal_accent}"\n'
    for group,offset in (('normal',0),('bright',8)):
        toml+=f'[colors.{group}]\n'+''.join(f'{k} = "{ansi[offset+i]}"\n' for i,k in enumerate(('black','red','green','yellow','blue','magenta','cyan','white')))
    write(CONFIG/'alacritty/alacritty.toml',toml)
    # Konsole keeps its original profile and uses only our colorscheme.
    scheme='[General]\nDescription=Obsidian Steel\nOpacity=0.82\nBlur=true\n'
    for name,c in [('Background',bg),('Foreground',terminal_text)]+[(f'Color{i}',ansi[i]) for i in range(8)]+[(f'Color{i}Intense',ansi[i+8]) for i in range(8)]:
        scheme+=f'[{name}]\nColor={rgb(c)}\n'
    write(STYLE/'share/konsole/Obsidian.colorscheme',scheme)
    # Reuse the proven Qt palette across KDE/Qt applications.
    c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str;c.read(ROOT/'obsidian/app-settings/kdeglobals')
    public=configparser.ConfigParser(interpolation=None);public.optionxform=str
    for section in c.sections():
        if section.startswith(('Colors:','ColorEffects:')):public[section]=dict(c[section])
    public['General']={'Name':'Obsidian Steel'}
    from io import StringIO
    s=StringIO();public.write(s,space_around_delimiters=False);write(STYLE/'Obsidian.colors',s.getvalue())
    # qBittorrent's AppImage may bundle Qt; use its native theme format too.
    mirror(ORIGINAL/'qBittorrent',CONFIG/'qBittorrent',('qBittorrent.conf',))
    theme=STYLE/'qbittorrent';theme.mkdir(exist_ok=True)
    colors={f'Palette.{k}':v for k,v in {'Window':bg,'Base':bg,'AlternateBase':bg,'WindowText':fg,'Text':fg,
        'Button':high,'ButtonText':fg,'ToolTipBase':bg,'ToolTipText':fg,'Highlight':sel,'HighlightedText':fg,
        'Link':accent,'LinkVisited':accent,'Light':high,'Midlight':high,'Mid':sel,'Dark':bg,'Shadow':'#000000',
        'WindowTextDisabled':p['muted'],'TextDisabled':p['muted'],'ButtonTextDisabled':p['muted']}.items()}
    write(theme/'config.json',json.dumps({'colors':colors,'colors.dark':colors},indent=2))
    write(theme/'stylesheet.qss',f'QMainWindow, QDialog, QMenuBar, QToolBar, QStatusBar, QAbstractItemView, QAbstractItemView:!active {{ background-color: {bg}; color: {fg}; }}\nQAbstractItemView::item:selected, QAbstractItemView::item:selected:!active {{ background-color: {sel}; }}\n')
    write(theme/'resources.qrc','<RCC><qresource prefix="/"><file>config.json</file><file>stylesheet.qss</file></qresource></RCC>')
    compiler = shutil.which('rcc') or ('/usr/lib/qt6/rcc' if Path('/usr/lib/qt6/rcc').exists() else None)
    bundle = theme/'steel.qbtheme'
    if compiler:
        import hashlib
        digest = hashlib.sha256((theme/'config.json').read_bytes() + (theme/'stylesheet.qss').read_bytes()).hexdigest()
        stamp = theme/'.bundle-inputs'
        if not bundle.exists() or not stamp.exists() or stamp.read_text() != digest:
            pending = theme/'steel.qbtheme.tmp'
            subprocess.run([compiler,'--binary',str(theme/'resources.qrc'),'-o',str(pending)],check=True,timeout=15)
            os.replace(pending,bundle)
            write(stamp,digest)
    qb_src=ORIGINAL/'qBittorrent/qBittorrent.conf';qb_dst=CONFIG/'qBittorrent/qBittorrent.conf'
    if qb_src.exists() and bundle.exists():
        text=(qb_dst if qb_dst.exists() else qb_src).read_text()
        for key,value in [('General\\UseCustomUITheme','true'),('General\\CustomUIThemePath',str(theme/'steel.qbtheme'))]:
            pattern=re.compile('^'+re.escape(key)+'=.*$',re.M)
            if pattern.search(text):text=pattern.sub(lambda _:key+'='+value,text)
            else:text=text.replace('[Preferences]','[Preferences]\n'+key+'='+value,1)
        write(qb_dst,text)
    # Kate/KWrite use a separate syntax theme for the editor canvas.
    native_theme=STYLE/'share/org.kde.syntax-highlighting/themes/Obsidian.theme'
    if native_theme.exists():
        for name in ('ktexteditorrc','katerc','kwriterc'):
            dst=CONFIG/name;src=ORIGINAL/name
            if dst.is_symlink():dst.unlink()
            c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str
            if dst.exists():c.read(dst)
            elif src.exists():c.read(src)
            if not c.has_section('KTextEditor Renderer'):c.add_section('KTextEditor Renderer')
            c['KTextEditor Renderer']['Color Theme']='Obsidian Steel'
            s=StringIO();c.write(s,space_around_delimiters=False);write(dst,s.getvalue())
    return p

def enabled():
    desktop=os.environ.get('XDG_CURRENT_DESKTOP','').lower()
    if 'kde' in desktop or 'plasma' in desktop: return False
    return (ROOT/'active').read_text().strip()=='obsidian' and ('hyprland' in desktop or bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')))

def original_environment(base=None):
    e=dict(os.environ if base is None else base)
    if e.get('XDG_CONFIG_HOME')==str(CONFIG):e['XDG_CONFIG_HOME']=str(ORIGINAL)
    if e.get('KDE_COLOR_SCHEME_PATH')==str(STYLE/'Obsidian.colors'):e.pop('KDE_COLOR_SCHEME_PATH',None)
    if e.get('GTK2_RC_FILES')==str(STYLE/'gtk2.rc'):e.pop('GTK2_RC_FILES',None)
    e['XDG_DATA_DIRS']=':'.join(x for x in e.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if x!=str(STYLE/'share'))
    owned={(STYLE/'webkit-style.so').resolve(),(STYLE/'qbittorrent/qt-inactive-palette.so').resolve()}
    inherited=[p for p in re.split(r'[:\s]+',e.get('LD_PRELOAD','')) if p and Path(p).resolve() not in owned]
    if inherited: e['LD_PRELOAD']=':'.join(inherited)
    else: e.pop('LD_PRELOAD',None)
    if e.get('OBSIDIAN_WEBKIT_CSS')==str(STYLE/'webkit.css'): e.pop('OBSIDIAN_WEBKIT_CSS',None)

    return e

def environment(base=None):
    e=dict(os.environ if base is None else base)
    e.update(XDG_CONFIG_HOME=str(CONFIG),KDE_COLOR_SCHEME_PATH=str(STYLE/'Obsidian.colors'),
        QT_QPA_PLATFORMTHEME='kde',GTK2_RC_FILES=str(STYLE/'gtk2.rc'),GTK_USE_PORTAL='0',XDG_CURRENT_DESKTOP='Hyprland')
    data=e.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
    e['XDG_DATA_DIRS']=str(STYLE/'share')+':'+data
    return e

def electron_client(name, executable):
    spec=importlib.util.spec_from_file_location('electronstyle',ROOT/'electron-style.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return str(module.prepare(name,executable))

def firefox_profile(args,e):
    e["GDK_BACKEND"]="wayland"
    e["MOZ_ENABLE_WAYLAND"]="1"
    # Mozilla's lock/remote identity must not use two aliases for the same profile.
    e['XDG_CONFIG_HOME']=str(ORIGINAL)
    if any(x.lower() in ('-profilemanager','--profilemanager','-p') for x in args):return
    for key in ('-profile','--profile'):
        if key in args:
            i=args.index(key)
            if i+1<len(args):args[i+1]=str(Path(args[i+1]).expanduser().resolve())
            return
    owned=ROOT/'firefox-profile-path'
    if owned.exists():
        profile=Path(owned.read_text().strip()).resolve()
        if not profile.is_dir():raise RuntimeError('Steel Firefox profile missing')
        empty=len(args)==1
        args[1:1]=['--profile',str(profile)]
        if empty:args+=['--new-window','about:newtab']
        return
    base=ORIGINAL/'mozilla/firefox'
    if not base.exists():base=Path.home()/'.mozilla/firefox'
    c=configparser.ConfigParser(interpolation=None);c.read(base/'installs.ini')
    default=next((c[s].get('Default') for s in c.sections() if c[s].get('Default')),None)
    if default:
        path=Path(default);path=path if path.is_absolute() else base/path
        empty=len(args)==1
        args[1:1]=['--profile',str(path.resolve())]
        if empty:args+=['--new-window','about:newtab']

def spotify_client(e):
    # Copy a matched application snapshot and add only a CSS resource.
    # Never splice native binaries with another version or patch Spotify JavaScript.
    import zipfile
    source=Path('/opt/spotify');css=STYLE/'spotify-steel.css'
    client=STYLE/'clients/spotify';stamp=STYLE/'spotify-source.json'
    def fingerprint():
        return {'kind':'native-css-v1','source':str(source),
                'files':{name:[(source/name).stat().st_mtime_ns,(source/name).stat().st_size] for name in ('spotify','libcef.so','Apps/xpui.spa')},
                'css_mtime':css.stat().st_mtime_ns}
    signature=fingerprint()
    if stamp.exists() and json.loads(stamp.read_text())==signature and (client/'spotify').exists():return str(client/'spotify')
    client.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='spotify-build-',dir=client.parent))
    try:
        shutil.copytree(source,stage,dirs_exist_ok=True)
        if fingerprint()!=signature:raise RuntimeError('Spotify updated during preparation; retry after the update finishes')
        archive=stage/'Apps/xpui.spa';patched=archive.with_suffix('.spa.new')
        with zipfile.ZipFile(archive) as original,zipfile.ZipFile(patched,'w') as modified:
            for info in original.infolist():
                data=original.read(info.filename)
                if info.filename=='index.html':
                    html=data.decode();assert '</head>' in html
                    data=html.replace('</head>','<link rel="stylesheet" href="/steel.css"></head>',1).encode()
                modified.writestr(info,data)
            modified.writestr('steel.css',css.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
        patched.replace(archive)
        subprocess.run([str(stage/'spotify'),'--version'],env=e,stdout=subprocess.DEVNULL,timeout=10,check=True)
        previous=client.with_name('spotify-previous')
        if previous.exists():shutil.rmtree(previous)
        if client.exists():client.rename(previous)
        stage.rename(client);write(stamp,json.dumps(signature))
        if previous.exists():shutil.rmtree(previous)
    except Exception:
        if stage.exists():shutil.rmtree(stage)
        raise
    return str(client/'spotify')

def activate_aerion_once(executable, owner_pid):
    # Existing-instance launches already activate themselves. Fresh manual launches
    # must show the window after Aerion applies its own start-hidden preference.
    import time
    seen=False
    for attempt in range(32):
        try: os.kill(owner_pid,0)
        except ProcessLookupError: return
        try:
            result=subprocess.run(['hyprctl','clients','-j'],capture_output=True,text=True,timeout=1)
            visible=any(client.get('pid')==owner_pid for client in json.loads(result.stdout)) if result.returncode==0 else False
        except (ValueError,subprocess.TimeoutExpired): visible=False
        if visible: seen=True
        elif seen or attempt==31:
            subprocess.run([executable],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
            return
        time.sleep(0.25)


def update_aerion_autostart():
    target=ORIGINAL/'autostart/io.github.hkdb.Aerion.desktop'
    if not target.exists(): return
    prefix='Exec=/usr/bin/env STEEL_AUTOSTART=1 /usr/bin/python3 '+str(ROOT/'app-style.py')+' launch -- '
    legacy='Exec=/usr/bin/python3 '+str(ROOT/'app-style.py')+' launch -- '
    text=target.read_text()
    if prefix in text: return
    backup=STYLE/'desktop-backups/aerion-autostart.desktop.json'
    if not backup.exists(): write(backup,json.dumps({'original':text}))
    updated='\n'.join(prefix+line[len(legacy):] if line.startswith(legacy) else prefix+line[5:] if line.startswith('Exec=') else line for line in text.splitlines())+'\n'
    write(target,updated)


def install_launchers():
    """Build conditional desktop launchers locally, without exporting personal entries."""
    target=Path.home()/'.local/share/applications';target.mkdir(parents=True,exist_ok=True)
    private=STYLE/'desktop-backups';private.mkdir(parents=True,exist_ok=True,mode=0o700)
    prefix='Exec=/usr/bin/python3 '+str(ROOT/'app-style.py')+' launch -- '
    seen=set();count=0
    for folder in (target,Path('/usr/share/applications')):
        for src in sorted(folder.glob('*.desktop')):
            if src.name in seen:continue
            seen.add(src.name)
            c=configparser.ConfigParser(interpolation=None,strict=False)
            try:c.read(src);entry=c['Desktop Entry']
            except (configparser.Error,KeyError):continue
            if entry.get('Type')!='Application' or entry.get('Hidden')=='true' or entry.get('NoDisplay')=='true' or not entry.get('Exec'):continue
            text=src.read_text();dst=target/src.name
            terminal=entry.get('Terminal','false').lower()=='true'
            terminal_prefix='Exec=/usr/bin/python3 '+str(ROOT/'app-style.py')+' terminal-launch -- '
            if prefix in text and not terminal:continue
            if terminal_prefix in text:continue
            record=private/(src.name+'.json')
            if not record.exists():
                write(record,json.dumps({'hadOriginal':dst.exists(),'original':dst.read_text() if dst.exists() else None}))
            lines=[]
            for line in text.splitlines():
                if line.startswith('Exec=') and line[5:].strip():
                    command=line[len(prefix):] if line.startswith(prefix) else line[5:]
                    line=(terminal_prefix if terminal else prefix)+command
                if terminal and line=='Terminal=true':line='Terminal=false'
                if line=='DBusActivatable=true':line='DBusActivatable=false'
                lines.append(line)
            write(dst,'\n'.join(lines)+'\n');count+=1
    update_aerion_autostart()
    subprocess.run(['update-desktop-database',str(target)],capture_output=True)
    print('New conditional launchers:',count)

if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'prepare'
    if action=='prepare': prepare(); print('Prepared isolated application palette')
    elif action=='env': print(json.dumps(environment()))
    elif action=='install-launchers': prepare();install_launchers()
    elif action=='service-environment':
        # D-Bus/systemd services must not retain the private config root for KDE.
        e=original_environment();e['XDG_CONFIG_HOME']=str(ORIGINAL);e['KDE_COLOR_SCHEME_PATH']=''
        e['GTK2_RC_FILES']=e.get('GTK2_RC_FILES','')
        subprocess.run(['dbus-update-activation-environment','--systemd','--all'],env=e,check=True)
    elif action=='aerion-activate-once':activate_aerion_once(sys.argv[2],int(sys.argv[3]))
    elif action=='terminal-launch':
        args=sys.argv[2:]
        if args and args[0]=='--':args=args[1:]
        if not args:raise SystemExit('Missing terminal application command')
        e=original_environment()
        terminal=shutil.which('kitty',path=e.get('PATH'))
        if not terminal:raise SystemExit('Kitty is required for terminal application launchers')
        command=[terminal]
        if enabled():command+=['--config',str(ROOT/'obsidian/kitty.conf')]
        command+=['--',sys.executable,str(ROOT/'app-style.py'),'launch','--',*args]
        os.execvpe(terminal,command,e)
    elif action=='launch':
        args=sys.argv[2:]
        if args and args[0]=='--': args=args[1:]
        if not args: raise SystemExit('Missing application command')
        e=original_environment()
        if enabled():
            if not (STYLE/'Obsidian.colors').exists(): prepare()
            e=environment(e); name=Path(args[0]).name
            if name=='code': args[1:1]=['--user-data-dir',str(CONFIG/'Code')]
            elif name=='konsole': args[1:1]=['-p','ColorScheme=Obsidian']
            elif name.lower().startswith('qbittorrent'):
                library=qbit_palette_library()
                if library:
                    inherited=e.get('LD_PRELOAD','')
                    e['LD_PRELOAD']=str(library)+(':'+inherited if inherited else '')
            elif name=='alacritty': args[1:1]=['--config-file',str(CONFIG/'alacritty/alacritty.toml')]
            elif name=='retroarch': retroarch_client(args,e)
            elif name in ('spotify','spotify-launcher'):
                args[0]=spotify_client(e)
                if not any(x.startswith('--ozone-platform') for x in args):args.insert(1,'--ozone-platform=wayland')
            elif name in ('chatgpt','codex-launcher','ChatGPT'): args[0]=electron_client('chatgpt','/usr/lib/chatgpt/ChatGPT')
            elif name.lower()=='discord':
                # Preserve the stock updater's host/module path relationships.
                e['XDG_CONFIG_HOME']=str(ORIGINAL)
                args[0]=electron_client('discord',ORIGINAL/'discord/Discord')
            elif name=='aerion':
                e=aerion_environment(args,e)
                if len(args)==1 and e.get('STEEL_AUTOSTART')!='1':
                    subprocess.Popen([sys.executable,str(ROOT/'app-style.py'),'aerion-activate-once',args[0],str(os.getpid())],
                        env=original_environment(e),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)

            elif name in ('firefox','firefox-bin'):firefox_profile(args,e)
        os.execvpe(args[0],args,e)
