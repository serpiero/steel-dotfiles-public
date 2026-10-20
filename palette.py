#!/usr/bin/env python3
"""Generate native application palettes from the canonical Steel theme."""
from pathlib import Path
import subprocess, json, colorsys, re, sys, os, tempfile, configparser, signal
ROOT = Path(__file__).resolve().parent

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.spectrum-')
    with os.fdopen(fd, 'w') as f:
        f.write(value)
    os.replace(tmp, path)

def palette(wall):
    wall = Path(wall)
    if wall.suffix.lower() == '.svg':
        vals = re.findall(r'#[0-9a-fA-F]{6}\b', wall.read_text())
        pixels = [tuple(int(v[i:i+2], 16)/255 for i in (1,3,5)) for v in vals]
    else:
        data = subprocess.check_output(['ffmpeg','-v','error','-i',str(wall),'-vf','scale=32:32','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'], timeout=15)
        pixels = [tuple(c/255 for c in data[i:i+3]) for i in range(0,len(data)-2,3)]
    candidates = [p for p in pixels if .10 < colorsys.rgb_to_hls(*p)[1] < .88]
    candidates = candidates or pixels or [(0.1,0.1,0.1)]
    avg = tuple(sum(p[i] for p in candidates)/len(candidates) for i in range(3))
    wallpaper_hue, _, sat = colorsys.rgb_to_hls(*avg)
    anchor = 210/360
    delta = (wallpaper_hue-anchor+.5)%1-.5
    hue = anchor + max(-.035, min(.035, delta*.12*min(1,sat*3)))
    settings = json.loads((ROOT/"ui/settings/config.json").read_text())
    tint = max(.5, min(1.5, settings.get("appearance",{}).get("obsidianTint",1.0)))
    def color(light, saturation, offset=0):
        return '#'+''.join(f'{round(c*255):02x}' for c in colorsys.hls_to_rgb((hue+offset)%1, light, min(.8,saturation*tint)))
    p = dict(background=color(.105,.17), low=color(.13,.18), surface=color(.105,.17),
             high=color(.19,.16), highest=color(.235,.14), text=color(.86,.14),
             muted=color(.65,.13), accent=color(.68,.24), selection=color(.27,.20),
             wine=color(.65,.20,.35), sage=color(.65,.15,-.25), warm=color(.65,.15,-.45))
    # Approved fixed base shared with Firefox; wallpaper tint affects accents only.
    from theme import palette as resolve_palette, terminal as terminal_theme, fingerprint
    p = resolve_palette(ROOT, derived=p)
    terminal_tokens = terminal_theme(ROOT, p)
    tokens = json.loads((ROOT/'ui/state/user/generated/colors.json').read_text())
    for key in tokens:
        if key.startswith('on_'):
            tokens[key] = p['background'] if key in ('on_primary','on_secondary','on_tertiary','on_error','on_success') or ('fixed' in key and 'variant' not in key) else p['text']
        elif key in ('inverse_surface','inverse_primary'): tokens[key] = p['text']
        elif key == 'inverse_on_surface': tokens[key] = p['background']
        elif key in ('primary','secondary','tertiary','surface_tint') or key.endswith('_fixed') or key.endswith('_fixed_dim'): tokens[key] = p['accent']
        elif key in ('background','surface','surface_dim','shadow','scrim'): tokens[key] = p['background']
        elif key in ('surface_container_low','surface_container_lowest'): tokens[key] = p['low']
        elif key == 'surface_container': tokens[key] = p['surface']
        elif key.endswith('_container'): tokens[key] = p['high']
        elif key in ('surface_container_high','outline_variant'): tokens[key] = p['high']
        elif key in ('surface_bright','surface_variant','surface_container_highest'): tokens[key] = p['highest']
        elif key == 'outline': tokens[key] = p['muted']
    tokens.update(error=p['wine'], success=p['sage'])
    write(ROOT/'ui/state/user/generated/colors.json', json.dumps(tokens,indent=2)+'\n')
    write(ROOT/'obsidian/generated/spectrum.json', json.dumps(p,indent=2)+'\n')
    ansi = [p['low'], p['wine'], p['sage'], p['warm'], p['accent'], p['wine'], p['terminal_accent'], p['text'], p['muted'], p['wine'], p['sage'], p['warm'], p['accent'], p['wine'], p['terminal_accent'], p['text']]
    kitty = ROOT/'obsidian/kitty.conf'
    terminal_text = terminal_tokens['foreground']
    terminal_accent = terminal_tokens['accent']
    settings = dict(background=p['surface'],foreground=terminal_text,cursor=terminal_accent,
                    background_opacity='0.76',
                    selection_background=p['selection'],selection_foreground=p['text'],
                    active_tab_background=p['selection'],active_tab_foreground=p['text'],
                    inactive_tab_background=p['low'],inactive_tab_foreground=p['muted'],url_color=p['accent'])
    for index, value in terminal_tokens['ansi_overrides'].items(): ansi[index] = value
    settings.update({f'color{i}':v for i,v in enumerate(ansi)})
    contents=kitty.read_text()
    for key,value in settings.items():
        contents=re.sub(r'^'+key+r'\s+.*$',key+' '+value,contents,flags=re.M)
    write(kitty,contents)
    prompt = '''# Obsidian: Kali-style two-line prompt without Powerline separators.
add_newline = true
palette = "obsidian_steel"
format = "[╭─](accent)[@PROMPT_LABEL@](bold text) $directory$git_branch$git_status\\n[╰─](accent)$character"

[directory]
style = "accent"
format = "[$path]($style)"
truncation_length = 3
truncation_symbol = "…/"

[git_branch]
format = "[ · $branch](muted)"

[git_status]
format = "[ $all_status$ahead_behind](wine)"

[character]
success_symbol = '[\\$](text)'
error_symbol = '[\\$](wine)'
vimcmd_symbol = '[\\$](sage)'
format = "$symbol "

[palettes.obsidian_steel]
'''
    prompt = prompt.replace('@PROMPT_LABEL@', terminal_tokens['prompt_label'])
    prompt_colors = dict(p, text=terminal_text, accent=terminal_accent)
    prompt += ''.join(f'{k} = "{prompt_colors[k]}"\n' for k in ('text','accent','muted','wine','sage'))
    write(ROOT/'obsidian/starship.toml',prompt)
    btop = ROOT/'obsidian/btop/themes/obsidian-cybr.theme'
    contents=btop.read_text()
    def monitor(match):
        key=match[1]
        if key in ('main_bg','graph_bg'): value=p['background']
        elif key in ('main_fg','title','selected_fg'): value=p['text']
        elif key in ('selected_bg','meter_bg','inactive_fg','div_line'): value=p['selection']
        elif key.startswith('temp_') or key == 'used_end': value=p['wine'] if key.endswith('end') else p['warm']
        elif key.startswith(('free_','available_')): value=p['sage']
        else: value=p['accent']
        return f'theme[{key}]="{value}"'
    write(btop,re.sub(r'theme\[([^]]+)\]="#[0-9a-fA-F]+"',monitor,contents))
    # Native Qt palette only for Dolphin launched through our scoped wrapper.
    qt = ROOT/'obsidian/app-settings/kdeglobals'
    if qt.exists():
        config = configparser.ConfigParser(interpolation=None, strict=False)
        config.optionxform = str
        config.read(qt)
        def rgb(value):
            return ','.join(str(int(value[i:i+2],16)) for i in (1,3,5))
        for section in config.sections():
            if not section.startswith('Colors:'): continue
            selection = section == 'Colors:Selection'
            for key, value in dict(BackgroundNormal=p['selection'] if selection else p['surface'],
                                   BackgroundAlternate=p['high'], ForegroundNormal=p['text'],
                                   ForegroundInactive=p['muted'], ForegroundLink=p['accent'],
                                   ForegroundVisited=p['accent'], ForegroundNegative=p['wine'],
                                   ForegroundNeutral=p['warm'], ForegroundPositive=p['sage'],
                                   DecorationFocus=p['accent'], DecorationHover=p['accent']).items():
                config[section][key] = rgb(value)
        from io import StringIO
        output = StringIO()
        config.write(output, space_around_delimiters=False)
        write(qt, output.getvalue())
    if (ROOT/'app-style.py').exists():
        subprocess.run([sys.executable,str(ROOT/'app-style.py'),'prepare'],check=True,timeout=180)
    # Refresh only this desktop's owned profiles; do not change shared KDE state.
    from importlib.util import spec_from_file_location, module_from_spec
    if (ROOT/'INSTALLATION.json').is_file() or (ROOT == (Path.home()/'.local/share/rice-profiles').resolve() and (ROOT/'active').is_file()):
        spec=spec_from_file_location('steel_firefox_refresh',ROOT/'tools/firefox-theme.py')
        adapter=module_from_spec(spec);spec.loader.exec_module(adapter);adapter.refresh(ROOT)
    sequences='\033]10;'+terminal_text+'\007\033]11;'+p['background']+'\007\033]12;'+terminal_accent+'\007'
    sequences+=''.join('\033]4;'+str(i)+';'+value+'\007' for i,value in enumerate(ansi))
    write(ROOT/'obsidian/generated/terminal-sequences.txt',sequences)
    desktop=os.environ.get('XDG_CURRENT_DESKTOP','').lower()
    if 'hyprland' in desktop and 'kde' not in desktop and 'plasma' not in desktop:
        subprocess.run([sys.executable,str(ROOT/'wine-style.py')],check=True,timeout=40)
        if os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
            subprocess.run(['hyprctl','reload'],check=True,capture_output=True,timeout=15)
    write(ROOT/'palette-source.json',json.dumps({'wallpaper':str(wall),'mtime':wall.stat().st_mtime_ns,'theme':fingerprint(ROOT),'hue':round(hue,4),'scheme':'steel-v2'}))
    # Refresh only terminals explicitly using this profile's configuration.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            args = (proc/'cmdline').read_bytes().split(b'\0')
            if b'--config' in args and str(kitty).encode() in args and b'kitty' in args[0]:
                os.kill(int(proc.name), signal.SIGUSR1)
        except (OSError, IndexError): pass
    return tokens

if __name__ == '__main__':
    palette((ROOT/"wallpaper-path").read_text().strip() if sys.argv[1]=="--current" else sys.argv[1])
