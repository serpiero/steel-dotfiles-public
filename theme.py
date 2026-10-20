#!/usr/bin/env python3
"""Theme tokens and portable style compilation. No application state lives here."""
from pathlib import Path
import argparse
import copy
import colorsys
import json
import os
import re
import tempfile
import hashlib

ROOT = Path(__file__).resolve().parent
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")
ALIAS = re.compile(r"\{([a-z][a-z0-9_]*)\}\Z")
PLACEHOLDER = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")


def merge(base, patch):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load(root=ROOT):
    root = Path(root)
    selected = root / 'theme-selection.json'
    name = json.loads(selected.read_text()).get('theme', 'steel') if selected.exists() else 'steel'
    if not re.fullmatch(r'[a-z0-9_-]+', name):
        raise ValueError('Theme name must be a simple filename')
    specification = json.loads((root / 'themes' / f'{name}.json').read_text())
    local = root / 'local-theme.json'
    if local.exists():
        specification = merge(specification, json.loads(local.read_text()))
    if specification.get('version') != 1:
        raise ValueError('Unsupported theme format')
    if specification['palette'].get('mode') not in ('fixed', 'wallpaper'):
        raise ValueError('Palette mode must be fixed or wallpaper')
    phone = specification['layout']['phone']
    if not 1 <= phone['contentZoom'] <= 3 or not 1 <= phone['chromeZoom'] <= 2:
        raise ValueError('Phone zoom is outside the supported range')
    sidebar = specification['layout']['whatsapp']
    if not 160 <= sidebar['minWidth'] <= sidebar['width'] <= sidebar['maxWidth'] <= 1000:
        raise ValueError('Invalid chat list width bounds')
    if not 48 <= sidebar['compactWidth'] <= 120:
        raise ValueError('Invalid avatar column width')
    if not 200 <= sidebar['chatMinWidth'] <= 1000 or not 400 <= sidebar['autoCompactAt'] <= 2000:
        raise ValueError('Invalid responsive chat dimensions')
    search = specification['layout']['search']
    if not 600 <= search['maxWidth'] <= 4000 or not 16 <= search['sideMargin'] <= 200 or not 600 <= search['wideFrom'] <= 4000:
        raise ValueError('Invalid search dimensions')
    if not 320 <= phone['maxDeviceWidth'] <= 2000 or not 1 <= phone['minDppx'] <= 4 or not 300 <= phone['spotifyMaxWidth'] <= 2000:
        raise ValueError('Invalid phone dimensions')
    if not re.fullmatch(r'[\w .-]{1,32}', specification.get('prompt', {}).get('label', 'STEEL')):
        raise ValueError('Prompt label must be plain text, up to 32 characters')
    return specification


def fingerprint(root=ROOT):
    """Invalidate generated output when tokens, templates or adapters change."""
    root = Path(root)
    digest = hashlib.sha256(json.dumps(load(root), sort_keys=True).encode())
    files = list((root / 'styles').rglob('*')) + list((root / 'features').glob('*/*.user.js.in'))
    files += [root / name for name in ('theme.py', 'palette.py', 'app-style.py', 'workspace_icons.py', 'electron-style.py', 'wine-style.py', 'tools/firefox-theme.py', 'tools/firefox-live.py')]
    for path in sorted(p for p in files if p.is_file()):
        digest.update(str(path.relative_to(root)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def resolve_colors(values):
    resolved = {}
    visiting = set()

    def resolve(name):
        if name in resolved:
            return resolved[name]
        if name in visiting:
            raise ValueError(f'Color alias cycle at {name}')
        if name not in values:
            raise ValueError(f'Unknown color token: {name}')
        visiting.add(name)
        value = values[name]
        alias = ALIAS.fullmatch(value) if isinstance(value, str) else None
        value = resolve(alias[1]) if alias else value
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise ValueError(f'Invalid color token: {name}')
        visiting.remove(name)
        resolved[name] = value.lower()
        return resolved[name]

    for name in values:
        resolve(name)
    return resolved


def palette(root=ROOT, derived=None):
    specification = load(root)
    configured = specification['palette']['colors']
    if specification['palette']['mode'] == 'wallpaper' and derived:
        # In wallpaper mode, only explicitly selected tokens override the derived spectrum.
        configured = dict(derived, **configured)
    return resolve_colors(configured)


def terminal(root=ROOT, colors=None):
    specification = load(root)
    colors = colors or palette(root)
    def color(value):
        alias = ALIAS.fullmatch(value)
        value = colors[alias[1]] if alias else value
        if not HEX.fullmatch(value):
            raise ValueError('Invalid terminal color')
        return value
    settings = specification['terminal']
    return {
        'foreground': color(settings['foreground']),
        'accent': color(settings['accent']),
        'ansi_overrides': {int(k): color(v) for k, v in settings['ansi_overrides'].items() if 0 <= int(k) <= 15},
        'prompt_label': specification.get('prompt', {}).get('label', 'STEEL'),
    }


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.theme-')
    with os.fdopen(descriptor, 'w') as output:
        output.write(content)
    os.replace(temporary, path)


def render(root=ROOT, colors=None):
    root = Path(root)
    specification = load(root)
    colors = colors or palette(root)
    from workspace_icons import compile_index
    atomic(root / 'ui/generated/WorkspaceIconSources.js', compile_index(root))
    context = copy.deepcopy(specification)
    settings_path = root / 'ui/settings/config.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    main_font = settings.get('appearance', {}).get('fonts', {}).get('main', 'Google Sans Flex')
    # Overview uses 15 logical px (11.25 Pango points), weight 450 and width 100.
    context['fonts'] = {'main_pango': json.dumps(f'{main_font} 11.25 @wght=450,wdth=100')}
    context['palette'] = dict(colors)
    context['palette'].update({k + '_hex': v[1:] for k, v in colors.items()})
    for name, value in colors.items():
        hue, lightness, saturation = colorsys.rgb_to_hls(*(int(value[i:i+2], 16) / 255 for i in (1, 3, 5)))
        context['palette'][name + '_hsl'] = f'{hue * 360:.3f} {saturation * 100:.3f}% {lightness * 100:.3f}%'

    context['palette']['background_rgb'] = ','.join(str(int(colors['background'][i:i+2], 16)) for i in (1, 3, 5))
    context['layout']['search']['sideMarginTwice'] = 2 * context['layout']['search']['sideMargin']
    context['layout']['whatsapp_json'] = json.dumps(context['layout']['whatsapp'], separators=(',', ':'))
    tokens = ':root {\n' + ''.join(f'  --steel-{k.replace("_", "-")}: {v};\n' for k, v in sorted(colors.items())) + '}\n'

    def compile_style(source):
        def substitute(match):
            value = context
            for part in match[1].split('.'):
                if not isinstance(value, dict) or part not in value:
                    raise ValueError(f'Unknown style token: {match[1]}')
                value = value[part]
            if isinstance(value, (dict, list)):
                raise ValueError(f'Non-scalar style token: {match[1]}')
            return str(value)
        return PLACEHOLDER.sub(substitute, source)

    outputs = []
    for folder, destination in [('firefox', 'obsidian/firefox'), ('applications', 'obsidian/application-style')]:
        for source in sorted((root / 'styles' / folder).glob('*.css')):
            path = root / destination / source.name
            atomic(path, '/* Generated by theme.py; edit styles/ or themes/ instead. */\n' + tokens + compile_style(source.read_text()))
            outputs.append(path)
    for filename, destination in [('menu.rasi', 'menu.rasi'), ('spotlight.rasi', 'spotlight.rasi'), ('hyprlock.conf', 'obsidian/hyprlock.conf')]:
        source = root / 'styles/native' / filename
        if source.exists():
            target = root / destination
            atomic(target, compile_style(source.read_text())); outputs.append(target)
    # Compatibility names consumed by the existing Hyprland Lua theme.
    roles = {'no0': 'background', 'no1': 'surface', 'no2': 'low',
             're0': 'accent', 're1': 'selection', 're2': 'low',
             'gr0': 'sage', 'ye0': 'warm', 'bl0': 'accent', 'vi0': 'wine',
             'cy0': 'selection', 'wh0': 'text', 'wh1': 'muted', 'wh2': 'low',
             'me0': 'muted', 'or0': 'warm', 'pi0': 'wine'}
    lua = '-- Generated by theme.py; compatibility roles for the inherited Lua theme.\nlocal colors = {\n'
    lua += ''.join(f'  {name} = "{colors[role][1:]}",\n' for name, role in roles.items())
    lua += '  tr0 = "00", tr2 = "20", tr5 = "50", tr7 = "70", trF = "FF",\n}\nreturn colors\n'
    atomic(root / 'obsidian/colors.lua', lua)
    atomic(root / 'obsidian/generated/theme.css', tokens)
    for userscript in sorted((root / 'features').glob('*/*.user.js.in')):
        target = userscript.with_suffix('')
        atomic(target, compile_style(userscript.read_text()))
        outputs.append(target)
    recipe = root / 'obsidian/firefox/darkreader-palette.json'
    if recipe.exists():
        data = json.loads(recipe.read_text())
        recipe_theme = data.get('theme', data)
        if 'selectionColor' in recipe_theme: recipe_theme['selectionColor'] = colors['selection']
        for name in ('darkSchemeBackgroundColor', 'lightSchemeBackgroundColor'):
            if name in recipe_theme: recipe_theme[name] = colors['background']
        for name in ('darkSchemeTextColor', 'lightSchemeTextColor'):
            if name in recipe_theme: recipe_theme[name] = colors['text']
        atomic(recipe, json.dumps(data, indent=2) + '\n')
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'render', 'apply'), nargs='?', default='render')
    parser.add_argument('--root', type=Path, default=ROOT)
    arguments = parser.parse_args()
    colors = palette(arguments.root)
    terminal(arguments.root, colors)
    if arguments.action == 'check':
        print(f'Theme valid: {len(colors)} semantic colors')
    elif arguments.action == 'render':
        print(f'Rendered {len(render(arguments.root, colors))} style/feature files')
    else:
        # Existing palette generation refreshes Qt/GTK, Quickshell and terminal adapters.
        import importlib.util
        spec = importlib.util.spec_from_file_location('steel_palette', arguments.root / 'palette.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        wallpaper = arguments.root / 'wallpaper-path'
        module.palette(wallpaper.read_text().strip() if wallpaper.exists() else arguments.root / 'obsidian/wallpaper.svg')
        print('Theme applied through all palette adapters')


if __name__ == '__main__':
    main()
