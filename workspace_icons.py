#!/usr/bin/env python3
"""Resolve workspace artwork to files, independent of QApplication's maximum DPR."""
from pathlib import Path
import configparser
import json
import os
import re

ROOT = Path(__file__).resolve().parent


def icon_theme(root):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read(Path(root) / 'obsidian/app-settings/kdeglobals')
    return config.get('Icons', 'Theme', fallback='breeze')


def sources(theme, search_paths):
    result = {}
    seen = set()

    def visit(name):
        if name in seen or not re.fullmatch(r'[\w .-]+', name):
            return
        seen.add(name)
        folders = [Path(base) / name for base in search_paths]
        configs = []
        candidates = []
        for folder in folders:
            config = configparser.ConfigParser(interpolation=None, strict=False)
            if not (folder / 'index.theme').is_file(): continue
            config.read(folder / 'index.theme'); configs.append(config)
            for directory in config.get('Icon Theme', 'Directories', fallback='').split(','):
                part = Path(directory.strip())
                if not directory or part.is_absolute() or '..' in part.parts: continue
                location = folder / part
                if not location.is_dir(): continue
                size = config.getint(directory.strip(), 'Size', fallback=48)
                # Prefer a native vector, with the theme's 48 px application artwork first.
                for file in sorted(location.iterdir()):
                    if file.is_file() and file.suffix.lower() in ('.svg', '.png', '.xpm'):
                        candidates.append((file.suffix.lower() != '.svg', abs(size - 48), str(file), file))
        for _, _, _, file in sorted(candidates):
            result.setdefault(file.stem, file.resolve().as_uri())
        for config in configs:
            for parent in config.get('Icon Theme', 'Inherits', fallback='').split(','):
                if parent.strip(): visit(parent.strip())

    visit(theme)
    visit('breeze')
    visit('hicolor')
    return result


def compile_index(root=ROOT, search_paths=None):
    if search_paths is None:
        data = os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')
        search_paths = [Path.home() / '.local/share/icons', Path.home() / '.icons']
        search_paths += [Path(p) / 'icons' for p in data if p]
        search_paths += [Path('/usr/share/icons')]
        search_paths = list(dict.fromkeys(search_paths))
    values = sources(icon_theme(root), search_paths)
    return '.pragma library\n// Generated locally: direct artwork files for workspace icons only.\nvar sources = ' + json.dumps(values, sort_keys=True, separators=(',', ':')) + ';\nfunction source(name) { return sources[name] || sources[name.toLowerCase()] || ""; }\n'


if __name__ == '__main__':
    import argparse
    from theme import atomic
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    atomic(args.root / 'ui/generated/WorkspaceIconSources.js', compile_index(args.root))
    print('Workspace artwork index refreshed; other application settings unchanged.')
