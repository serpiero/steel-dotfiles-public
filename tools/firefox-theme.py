#!/usr/bin/env python3
"""Refresh Firefox CSS for Steel while preserving shared/KDE profiles."""
import argparse
import configparser
import importlib.util
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PREFERENCE = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'


def atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.steel-firefox-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def detect_profile(base):
    """Resolve the installation/default profile without guessing among multiple users."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(base / 'profiles.ini')
    candidates = []
    for section in config.sections():
        if section.startswith('Install') and config[section].get('Default'):
            candidates.append(base / config[section]['Default'])
    if not candidates:
        for section in config.sections():
            if section.startswith('Profile') and config[section].get('Default') == '1':
                path = Path(config[section]['Path']).expanduser()
                candidates.append(base / path if config[section].get('IsRelative', '1') == '1' else path)
    if not candidates:
        sections = [s for s in config.sections() if s.startswith('Profile') and config[s].get('Path')]
        if len(sections) == 1:
            settings = config[sections[0]]
            path = Path(settings['Path']).expanduser()
            candidates.append(base / path if settings.get('IsRelative', '1') == '1' else path)
    unique = {path.resolve() for path in candidates}
    return unique.pop() if len(unique) == 1 else None


def refresh(root=ROOT, firefox_base=None):
    root = Path(root).resolve()
    if not (root / 'INSTALLATION.json').is_file():
        raise ValueError('Run this adapter from an installed Steel profile.')
    base = Path(firefox_base) if firefox_base is not None else Path.home() / '.mozilla/firefox'
    detected = detect_profile(base)
    owned = (root / 'firefox').resolve()
    record = root / 'firefox-profile-path'
    profile = Path(record.read_text().strip()).expanduser().resolve() if record.exists() else None
    if profile is not None and not profile.is_relative_to(owned):
        raise ValueError('Recorded Firefox profile is shared or outside Steel; nothing changed.')
    if profile is None:
        profile = detected if detected is not None and detected.is_relative_to(owned) else owned / 'steel-profile'
    # Render current palette before copying; never copy accounts or preferences from a detected shared profile.
    spec = importlib.util.spec_from_file_location('steel_firefox_theme', root / 'theme.py')
    theme = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme)
    theme.render(root)
    contents = {name: (root / 'obsidian/firefox' / name).read_text() for name in ('userChrome.css', 'userContent.css')}
    user = profile / 'user.js'
    previous = user.read_text() if user.exists() else ''
    previous = re.sub(r'^\s*user_pref\(\s*["\']toolkit\.legacyUserProfileCustomizations\.stylesheets["\']\s*,\s*(?:true|false)\s*\);\s*$', '', previous, flags=re.M)
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, content in contents.items():
        atomic(profile / 'chrome' / name, content)
    atomic(user, previous.rstrip() + '\n' + PREFERENCE + '\n')
    atomic(record, str(profile) + '\n')
    print(f'Steel Firefox CSS updated: {profile}. Restart this Firefox instance to load CSS.')
    if detected is not None and detected != profile:
        print('Detected default Firefox profile preserved; Steel launcher uses its isolated profile.')
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    refresh(args.root)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, configparser.Error) as error:
        raise SystemExit(str(error))
