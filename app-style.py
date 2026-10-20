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

def native_library(toolkit):
    """Each ABI gets its own library; never preload a system Qt into AppImages."""
    source=ROOT/'styles/applications'/('qt-live-palette.cpp' if toolkit.startswith('Qt') else 'gtk-live-palette.c')
    library=STYLE/'native'/(toolkit.lower()+'.so')
    if not library.exists() or source.stat().st_mtime_ns>library.stat().st_mtime_ns:
        library.parent.mkdir(parents=True,exist_ok=True)
        flags=subprocess.check_output(['pkg-config','--cflags','--libs',toolkit],text=True)
        temporary=library.with_suffix('.so.tmp')
        subprocess.run(['c++' if toolkit.startswith('Qt') else 'cc','-shared','-fPIC',str(source),'-o',str(temporary),
                        *shlex.split(flags),'-ldl'],check=True,timeout=45)
        os.replace(temporary,library)
    return library

def resolve_executable(command,e):
    wrapper=ROOT/'web-runtime/bin'
    candidate=Path(command)
    if not candidate.is_absolute() or candidate.parent.resolve()==wrapper.resolve():
        path=os.pathsep.join(p for p in e.get('PATH',os.defpath).split(os.pathsep) if Path(p).resolve()!=wrapper.resolve())
        native=shutil.which(candidate.name,path=path)
        if native:
            candidate=Path(native)
            if candidate.parent==Path.home()/'.local/bin' and candidate.is_file():
                text=candidate.open('rb').read(2400).decode(errors='replace')
                system=Path('/usr/bin')/candidate.name
                if 'obsidian-terminal-colors' in text and system.is_file():return str(system)
            return native
    return command

def unwrap_environment(args,e):
    """Support normal desktop Exec=env NAME=value app without losing its toolkit."""
    if Path(args[0]).name!='env':return args,e
    result=dict(e);i=1
    while i<len(args):
        value=args[i]
        if value=='--':i+=1;break
        if value in ('-u','--unset') and i+1<len(args):result.pop(args[i+1],None);i+=2;continue
        if value.startswith('--unset='):result.pop(value.split('=',1)[1],None);i+=1;continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=',value):
            key,value=value.split('=',1);result[key]=value;i+=1;continue
        if value.startswith('-'):return args,e
        break
    return (args[i:],result) if i<len(args) else (args,e)

def electron_menu_arguments(args):
    """Native Chromium menus must use the same GTK provider as their launcher.

    Electron may otherwise choose its optional Qt shim and bypass the GTK menu
    palette. Detect a runtime, not an app's name, and preserve an explicit choice.
    """
    runtime=Path(args[0]).resolve().parent
    if ((runtime/'resources/app.asar').is_file() and
        (runtime/'snapshot_blob.bin').is_file() and
        not any(x=='--ui-toolkit' or x.startswith('--ui-toolkit=') for x in args[1:])):
        args.insert(1,'--ui-toolkit=gtk')

def native_environment(executable,e):
    """Inspect linked toolkit without executing the application or changing global defaults."""
    try:
        linked=subprocess.run(['readelf','-d',executable],capture_output=True,text=True,timeout=3).stdout
    except (OSError,subprocess.TimeoutExpired):return
    toolkit=next((name for token,name in [('libQt5Widgets','Qt5Widgets'),('libQt6Gui','Qt6Widgets'),
                  ('libgtk-3','gtk+-3.0'),('libgtk-4','gtk4')] if token in linked),None)
    if not toolkit:return
    library=native_library(toolkit)
    e['LD_PRELOAD']=str(library)+(':'+e['LD_PRELOAD'] if e.get('LD_PRELOAD') else '')
    e['OBSIDIAN_NATIVE_PALETTE']=str(STYLE/'native/palette.json')
    e['OBSIDIAN_GTK_CSS']=str(CONFIG/('gtk-4.0' if toolkit=='gtk4' else 'gtk-3.0')/'gtk.css')
    if toolkit=='gtk4':
        # GTK 4.24 sends an empty blur region through this protocol. Hyprland
        # treats it as an application opt-out, overriding compositor glass rules.
        previous=e.get('GDK_WAYLAND_DISABLE','')
        e['OBSIDIAN_GDK_WAYLAND_PREVIOUS']=previous
        e['GDK_WAYLAND_DISABLE']=','.join(filter(None,[previous,'ext_background_effect_manager_v1']))
    if toolkit=='Qt5Widgets':
        e['OBSIDIAN_QT_STYLE_PREVIOUS']=e.get('QT_STYLE_OVERRIDE','')
        e['QT_QPA_PLATFORMTHEME']='gtk3'
        e['QT_STYLE_OVERRIDE']='Fusion'
    if 'libKF6TextEditor' in linked or Path(executable).name in ('kate','kwrite'):
        library=editor_library()
        e['LD_PRELOAD']=str(library)+':'+e['LD_PRELOAD']

def editor_library():
    source=ROOT/'styles/applications/editor-live-palette.cpp';library=STYLE/'native/editor.so'
    if not library.exists() or source.stat().st_mtime_ns>library.stat().st_mtime_ns:
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets'],text=True))
        temporary=library.with_suffix('.so.tmp')
        subprocess.run(['c++','-shared','-fPIC',str(source),'-o',str(temporary),*flags,
                        *['-I'+str(p) for p in Path('/usr/include/KF6').iterdir() if p.is_dir()],
                        '-lKF6TextEditor','-lKF6SyntaxHighlighting'],check=True,timeout=45)
        os.replace(temporary,library)
    return library

def retroarch_client(args, e):
    client=STYLE/'clients/retroarch'
    binary=client/'retroarch'
    if not binary.exists(): return
    args[0]=str(binary)
    e['OBSIDIAN_RETROARCH_PALETTE']=str(STYLE/'native/retroarch.palette')
    # Explicit user configurations take precedence over the managed copy.
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
video_context_driver = "wayland"
input_driver = "wayland"
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
    client=STYLE/'clients/aerion/aerion'
    if client.is_file():
        args[0]=str(client)
        if e.get('STEEL_AUTOSTART')=='1' and '--background' not in args:
            args.insert(1,'--background')
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
    for toolkit in ('Qt5Widgets','Qt6Widgets','gtk+-3.0','gtk4'):native_library(toolkit)
    editor_library()
    mirror(ORIGINAL,CONFIG,('gtk-3.0','gtk-4.0','kdeglobals','Code','MiniMeters','alacritty','qBittorrent','ktexteditorrc','katerc','kwriterc','btop','cava'))
    btop_config=CONFIG/'btop'
    if btop_config.is_symlink():btop_config.unlink()
    if not btop_config.exists():btop_config.symlink_to(ROOT/'obsidian/btop',target_is_directory=True)
    cava=CONFIG/'cava'
    if cava.is_symlink():cava.unlink()
    mirror(ORIGINAL/'cava',cava,('config',))
    source=ORIGINAL/'cava/config';c=configparser.ConfigParser(interpolation=None,strict=False)
    if source.is_file():c.read(source)
    if not c.has_section('color'):c.add_section('color')
    c['color'].update(background="'default'",foreground="'"+p['accent']+"'",gradient='1',gradient_count='4',
                      gradient_color_1="'"+p['selection']+"'",gradient_color_2="'"+p['accent']+"'",
                      gradient_color_3="'"+p['text']+"'",gradient_color_4="'"+p['text']+"'")
    from io import StringIO
    output=StringIO();c.write(output);write(cava/'config',output.getvalue())
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
        # Preserve the pre-KDE typeface even when Plasma regenerated GTK defaults.
        if c['Settings'].get('gtk-font-name','').startswith('Arc Steel'):
            c['Settings']['gtk-font-name']='Google Sans Flex, Medium 11'
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
        # Breeze GTK3 uses suffixed named colors, including unfocused trees.
        colors.update({key+'_breeze':value for key,value in list(colors.items())})
        css='/* Obsidian: scoped GTK surfaces; existing fonts and widget geometry retained. */\n'
        css+=''.join(f'@define-color {k} {v};\n' for k,v in colors.items())
        if version=='gtk-4.0':
            css+=':root {\n'+''.join(f'  --{k.replace("_","-")}: {v};\n' for k,v in colors.items())+'}\n'
        css+=f'''window, .background, headerbar, .sidebar, .navigation-sidebar,
notebook > stack, scrolledwindow > viewport, .view, textview, textview text,
listview, columnview, treeview.view, treeview.view:backdrop, .view:backdrop,
popover > contents, .card {{ background-color: {bg}; background-image: none; color: {fg}; }}
headerbar {{ background-image: none; }}
row:selected, .navigation-sidebar row:selected {{ background-color: {sel}; color: {fg}; }}
selection {{ background-color: {sel}; color: {fg}; }}
/* The menu surface owns its padding; its outer popup paints no halo. */
popover, popover.background {{ background: transparent; border: 0; box-shadow: none; padding: 0; margin: 0; }}
menu, .menu, popover > contents {{ background-color: {high}; background-image: none; color: {fg}; border: 0; box-shadow: none; border-radius: 8px; padding: 4px; }}
menuitem, modelbutton {{ border: 0; border-radius: 4px; padding: 6px 10px; margin: 0 4px; }}
menuitem:hover, menuitem:selected, menuitem:active, modelbutton:hover {{ background-color: {sel}; background-image: none; color: {fg}; box-shadow: none; }}
'''
        write(dst/'gtk.css',css); write(dst/'colors.css',css)
    # VS Code: isolated settings; extensions, accounts and workspace state remain local.
    mirror(ORIGINAL/'Code', CONFIG/'Code', ('User','SingletonLock','SingletonSocket','SingletonCookie'))
    mirror(ORIGINAL/'Code/User',CONFIG/'Code/User',('settings.json','profiles'))
    code_src=ORIGINAL/'Code/User/settings.json'
    code_dst=CONFIG/'Code/User/settings.json'
    settings=jsonc(code_dst.read_text()) if code_dst.exists() else (jsonc(code_src.read_text()) if code_src.exists() else {})
    settings['editor.rulers']=[]  # Only the requested persistent vertical rulers.
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
    original_alacritty=ORIGINAL/'alacritty/alacritty.toml'
    imports=[str(original_alacritty)] if original_alacritty.exists() else []
    toml=f'[general]\nimport = {json.dumps(imports)}\n[colors.primary]\nbackground = "{bg}"\nforeground = "{terminal_text}"\n[colors.cursor]\ntext = "{bg}"\ncursor = "{terminal_accent}"\n'
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
        'Link':accent,'LinkVisited':accent,'Light':high,'Midlight':high,'Mid':sel,'Dark':bg,'Shadow':bg,
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
    if (ROOT/'styles/applications/editor.theme.json').exists():
        syntax=json.loads((ROOT/'styles/applications/editor.theme.json').read_text())
        def resolve_syntax(value):
            if isinstance(value,dict):return {k:resolve_syntax(v) for k,v in value.items()}
            if isinstance(value,list):return [resolve_syntax(v) for v in value]
            if isinstance(value,str) and re.fullmatch(r'\{[a-z_]+\}',value):return p[value[1:-1]]
            return value
        syntax=resolve_syntax(syntax)
        syntax['metadata']['name']='Obsidian'
        syntax['metadata']['revision']=14
        editor=syntax['editor-colors']
        roles={'BackgroundColor':bg,'IconBorder':bg,'CurrentLine':p['low'],'LineNumbers':p['muted'],
               'CurrentLineNumber':fg,'TextSelection':sel,'SearchHighlight':sel,'ReplaceHighlight':sel,
               'IndentationLine':high,'WordWrapMarker':high,'Separator':high,'TabMarker':p['muted'],
               'TemplateBackground':high,'TemplatePlaceholder':sel,'TemplateFocusedPlaceholder':sel,
               'TemplateReadOnlyPlaceholder':high,'BracketMatching':sel}
        editor.update(roles)
        for name in ('Normal','Others'):
            if name in syntax['text-styles']:syntax['text-styles'][name].update({'text-color':fg,'selected-text-color':fg})
        write(native_theme,json.dumps(syntax,indent=2)+'\n')
        for name in ('ktexteditorrc','katerc','kwriterc'):
            dst=CONFIG/name;src=ORIGINAL/name
            if dst.is_symlink():dst.unlink()
            c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str
            if dst.exists():c.read(dst)
            elif src.exists():c.read(src)
            if not c.has_section('KTextEditor Renderer'):c.add_section('KTextEditor Renderer')
            c['KTextEditor Renderer']['Color Theme']='Obsidian'
            s=StringIO();c.write(s,space_around_delimiters=False);write(dst,s.getvalue())
    # Prepare installed CSS adapters now, rather than leaving a stale client copy
    # until its next manual launch. Live Electron windows watch the CSS itself.
    for name,executable in [('chatgpt',Path('/usr/lib/chatgpt/ChatGPT')),('discord',ORIGINAL/'discord/Discord')]:
        if executable.exists():electron_client(name,executable)
    if Path('/opt/spotify/spotify').exists():spotify_client(environment())
    # Publish native colors last: watchers can now reload the complete editor theme.
    write(STYLE/'native/retroarch.palette',''.join(f'{key} {value[1:]}\n' for key,value in p.items()))
    write(STYLE/'native/palette.json',json.dumps(p,indent=2)+'\n')
    return p

def enabled(base=None):
    e=os.environ if base is None else base
    desktop=e.get('XDG_CURRENT_DESKTOP','').lower()
    if 'kde' in desktop or 'plasma' in desktop: return False
    return (ROOT/'active').read_text().strip()=='obsidian' and ('hyprland' in desktop or bool(e.get('HYPRLAND_INSTANCE_SIGNATURE')))

def original_environment(base=None):
    e=dict(os.environ if base is None else base)
    # A service manager can outlive Plasma. Drop only its Arc Steel variables
    # before constructing this desktop's independent application environment.
    desktop=e.get('XDG_CURRENT_DESKTOP','').lower()
    if 'kde' not in desktop and 'plasma' not in desktop:
        kde_root=Path.home()/'.local/share/kde-arc-steel'
        if e.get('FONTCONFIG_FILE')==str(kde_root/'fonts/fontconfig.conf'):e.pop('FONTCONFIG_FILE',None)
        if e.get('XDG_CONFIG_HOME')==str(kde_root/'apps/desktop-config'):e['XDG_CONFIG_HOME']=str(ORIGINAL)
        for key,owned in [('QML_IMPORT_PATH',str(kde_root/'qml-imports')),('QT_PLUGIN_PATH',str(Path.home()/'.local/lib/qt6/plugins')),('PATH',str(kde_root/'kitty/command-bin'))]:
            if key in e:
                value=':'.join(p for p in e[key].split(':') if p!=owned)
                if value:e[key]=value
                else:e.pop(key,None)
    if e.get('XDG_CONFIG_HOME')==str(CONFIG):e['XDG_CONFIG_HOME']=str(ORIGINAL)
    if e.get('KDE_COLOR_SCHEME_PATH')==str(STYLE/'Obsidian.colors'):e.pop('KDE_COLOR_SCHEME_PATH',None)
    if e.get('GTK2_RC_FILES')==str(STYLE/'gtk2.rc'):e.pop('GTK2_RC_FILES',None)
    e['XDG_DATA_DIRS']=':'.join(x for x in e.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if x!=str(STYLE/'share'))
    owned={(STYLE/'webkit-style.so').resolve(),(STYLE/'qbittorrent/qt-inactive-palette.so').resolve()}
    owned.update(p.resolve() for p in (STYLE/'native').glob('*.so'))
    inherited=[p for p in re.split(r'[:\s]+',e.get('LD_PRELOAD','')) if p and Path(p).resolve() not in owned]
    if inherited: e['LD_PRELOAD']=':'.join(inherited)
    else: e.pop('LD_PRELOAD',None)
    if e.get('OBSIDIAN_WEBKIT_CSS')==str(STYLE/'webkit.css'): e.pop('OBSIDIAN_WEBKIT_CSS',None)
    for key in ('OBSIDIAN_NATIVE_PALETTE','OBSIDIAN_GTK_CSS','OBSIDIAN_RETROARCH_PALETTE'):e.pop(key,None)
    previous=e.pop('OBSIDIAN_QT_STYLE_PREVIOUS',None)
    if previous is not None:
        if previous:e['QT_STYLE_OVERRIDE']=previous
        else:e.pop('QT_STYLE_OVERRIDE',None)
    previous=e.pop('OBSIDIAN_GDK_WAYLAND_PREVIOUS',None)
    if previous is not None:
        if previous:e['GDK_WAYLAND_DISABLE']=previous
        else:e.pop('GDK_WAYLAND_DISABLE',None)

    return e

def environment(base=None):
    e=original_environment(base)
    e.update(XDG_CONFIG_HOME=str(CONFIG),KDE_COLOR_SCHEME_PATH=str(STYLE/'Obsidian.colors'),
        QT_QPA_PLATFORMTHEME='kde',GTK2_RC_FILES=str(STYLE/'gtk2.rc'),GTK_USE_PORTAL='0',XDG_CURRENT_DESKTOP='Hyprland')
    wrappers=str(ROOT/'web-runtime/bin')
    e['PATH']=wrappers+os.pathsep+os.pathsep.join(p for p in e.get('PATH',os.defpath).split(os.pathsep) if p!=wrappers)
    data=e.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
    e['XDG_DATA_DIRS']=str(STYLE/'share')+':'+data
    return e

def electron_client(name, executable):
    spec=importlib.util.spec_from_file_location('electronstyle',ROOT/'electron-style.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return str(module.prepare(name,executable))

def firefox_profile(args,e):
    e.update(GDK_BACKEND='wayland',MOZ_ENABLE_WAYLAND='1',XDG_CONFIG_HOME=str(ORIGINAL))
    if any(x.lower() in ('-profilemanager','--profilemanager','-p') for x in args):return
    spec=importlib.util.spec_from_file_location('steel_firefox_profile',ROOT/'tools/firefox-theme.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    profile=module.refresh(ROOT)
    explicit=next((args.index(key) for key in ('-profile','--profile') if key in args),None)
    if explicit is not None:
        if explicit+1>=len(args):raise ValueError('Missing Firefox profile argument')
        requested=Path(args[explicit+1]).expanduser().resolve()
        if requested!=profile:raise ValueError('Steel Firefox uses its isolated profile; open shared profiles with stock Firefox.')
    else:args[1:1]=['--profile',str(profile)]
    live=importlib.util.spec_from_file_location('steel_firefox_live',ROOT/'tools/firefox-live.py')
    adapter=importlib.util.module_from_spec(live);live.loader.exec_module(adapter)
    args[0]=str(adapter.prepare(ROOT))


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


def application_directories():
    home=Path.home();data=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))
    folders=[data/'applications']
    folders += [Path(p)/'applications' for p in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if p and Path(p)!=STYLE/'share']
    folders += [home/'.local/share/flatpak/exports/share/applications',Path('/var/lib/flatpak/exports/share/applications')]
    return list(dict.fromkeys(folders))

def install_command_wrappers():
    """Give terminal invocations the same adapter as a desktop entry."""
    e=original_environment();commands={'btop','kitty','alacritty','konsole','aerion','firefox','code','chatgpt','discord','dolphin','spotify-launcher','zenity','kate','kwrite','seahorse','retroarch','cava'}
    for folder in application_directories():
        for path in folder.rglob('*.desktop') if folder.is_dir() else []:
            c=configparser.ConfigParser(interpolation=None,strict=False)
            try:
                c.read(path);entry=c['Desktop Entry']
                if entry.get('Type')!='Application' or entry.get('Hidden')=='true':continue
                args=shlex.split(entry.get('Exec',''))
                if str(ROOT/'app-style.py') in args and '--' in args:args=args[args.index('--')+1:]
                if not args:continue
                args,_=unwrap_environment(args,e)
                commands.add(Path(args[0]).name)
            except (configparser.Error,KeyError,ValueError):continue
    excluded={'sh','bash','zsh','fish','env','python','python3','perl','ruby','node','flatpak','snap','pkexec','sudo','gio','xdg-open','qs','quickshell'}
    for name in commands-excluded:
        if not re.fullmatch(r'[A-Za-z0-9_.+-]+',name):continue
        native=resolve_executable(name,e)
        if not Path(native).is_absolute() or not Path(native).is_file():continue
        target=ROOT/'web-runtime/bin'/name
        # Existing runtime binaries and user-created files are never replaced.
        if target.exists() and (target.is_symlink() or target.read_bytes()[:2]!=b'#!'):continue
        text='#!/bin/sh\nexec /usr/bin/python3 '+shlex.quote(str(ROOT/'app-style.py'))+' launch -- '+shlex.quote(native)+' "$@"\n'
        if not target.exists() or target.read_text()!=text:write(target,text);target.chmod(0o755)


def install_launchers():
    """Build conditional desktop launchers locally, without exporting personal entries."""
    folders=application_directories();target=folders[0];target.mkdir(parents=True,exist_ok=True)
    private=STYLE/'desktop-backups';private.mkdir(parents=True,exist_ok=True,mode=0o700)
    prefix='Exec=/usr/bin/python3 '+str(ROOT/'app-style.py')+' launch -- '
    seen=set();count=0
    for folder in folders:
        for src in sorted(folder.rglob('*.desktop')) if folder.is_dir() else []:
            desktop_id='-'.join(src.relative_to(folder).parts)
            if desktop_id in seen:continue
            seen.add(desktop_id)
            c=configparser.ConfigParser(interpolation=None,strict=False)
            try:c.read(src);entry=c['Desktop Entry']
            except (configparser.Error,KeyError):continue
            if entry.get('Type')!='Application' or entry.get('Hidden')=='true' or entry.get('NoDisplay')=='true' or not entry.get('Exec'):continue
            text=src.read_text();dst=target/desktop_id
            terminal=entry.get('Terminal','false').lower()=='true'
            terminal_prefix='Exec=/usr/bin/python3 '+str(ROOT/'app-style.py')+' terminal-launch -- '
            if prefix in text and not terminal:continue
            if terminal_prefix in text:continue
            record=private/(desktop_id+'.json')
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
    install_command_wrappers()
    if count:subprocess.run(['update-desktop-database',str(target)],capture_output=True)
    print('New conditional launchers:',count)
    return count

if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'prepare'
    if action=='prepare': prepare(); print('Prepared isolated application palette')
    elif action=='env': print(json.dumps(environment()))
    elif action=='install-launchers': prepare();install_launchers()
    elif action=='refresh-launchers':
        if enabled():install_launchers()
    elif action=='service-environment':
        # D-Bus/systemd services must not retain the private config root for KDE.
        e=original_environment();e['XDG_CONFIG_HOME']=str(ORIGINAL);e['KDE_COLOR_SCHEME_PATH']=''
        e['GTK2_RC_FILES']=e.get('GTK2_RC_FILES','')
        # D-Bus cannot remove keys with --all. Explicit neutral defaults prevent
        # the previous Plasma session's font and plugin aliases from surviving.
        e.setdefault('FONTCONFIG_FILE','/etc/fonts/fonts.conf')
        e.setdefault('QML_IMPORT_PATH','')
        e.setdefault('QT_PLUGIN_PATH','')
        subprocess.run(['dbus-update-activation-environment','--systemd','--all'],env=e,check=True)
    elif action=='terminal-launch':
        args=sys.argv[2:]
        if args and args[0]=='--':args=args[1:]
        if not args:raise SystemExit('Missing terminal application command')
        e=original_environment()
        terminal=resolve_executable('kitty',e)
        if not terminal:raise SystemExit('Kitty is required for terminal application launchers')
        command=[terminal]
        if enabled():
            command+=['--config',str(ROOT/'obsidian/kitty.conf')]
            e['STARSHIP_CONFIG']=str(ROOT/'obsidian/starship.toml')
        command+=['--',sys.executable,str(ROOT/'app-style.py'),'launch','--',*args]
        os.execvpe(terminal,command,e)
    elif action=='aerion-activate-once':activate_aerion_once(sys.argv[2],int(sys.argv[3]))
    elif action=='launch':
        args=sys.argv[2:]
        if args and args[0]=='--': args=args[1:]
        if not args: raise SystemExit('Missing application command')
        e=original_environment()
        args,e=unwrap_environment(args,e)
        args[0]=resolve_executable(args[0],e)
        if not enabled(e) and Path(args[0]).name in ('wine','wine64','winetricks'):
            subprocess.run([sys.executable,str(ROOT/'wine-style.py'),'--all','--restore'],check=True,timeout=75)
        if enabled(e):
            if not (STYLE/'Obsidian.colors').exists(): prepare()
            e=environment(e); name=Path(args[0]).name
            if name=='code': args[1:1]=['--user-data-dir',str(CONFIG/'Code')]
            elif name=='kitty' and not any(x in ('-c','--config') or x.startswith('--config=') for x in args[1:]):
                args[1:1]=['--config',str(ROOT/'obsidian/kitty.conf')]
            elif name=='btop' and not any(x=='--config' or x.startswith('--config=') for x in args[1:]):
                args[1:1]=['--config',str(ROOT/'obsidian/btop/btop.conf'),'--themes-dir',str(ROOT/'obsidian/btop/themes')]
            elif name=='konsole': args[1:1]=['-p','ColorScheme=Obsidian']
            elif name.lower().startswith('qbittorrent'):
                library=qbit_palette_library()
                if library:
                    inherited=e.get('LD_PRELOAD','')
                    e['LD_PRELOAD']=str(library)+(':'+inherited if inherited else '')
            elif name=='alacritty' and not any(x in ('-c','--config-file') or x.startswith('--config-file=') for x in args[1:]):
                args[1:1]=['--config-file',str(CONFIG/'alacritty/alacritty.toml')]
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
                    subprocess.Popen([sys.executable,str(ROOT/'app-style.py'),'aerion-activate-once',args[0],str(os.getpid())],env=original_environment(e),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)

            elif name in ('firefox','firefox-bin'):firefox_profile(args,e)
            elif name in ('wine','wine64','winetricks'):
                spec=importlib.util.spec_from_file_location('wine_style',ROOT/'wine-style.py')
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                prefix=Path(e.get('WINEPREFIX',str(STYLE/'wine-prefix'))).expanduser().resolve()
                e['WINEPREFIX']=str(prefix)
                module.apply(prefix=prefix)
            electron_menu_arguments(args)
            native_environment(args[0],e)
            if name in ('btop','cava','gping','genact','hollywood') and sys.stdout.isatty():
                sys.stdout.write((ROOT/'obsidian/generated/terminal-sequences.txt').read_text());sys.stdout.flush()
            if name in ('kitty','alacritty','konsole'):e['STARSHIP_CONFIG']=str(ROOT/'obsidian/starship.toml')
        os.execvpe(args[0],args,e)
