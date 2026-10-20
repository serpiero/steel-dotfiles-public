#!/usr/bin/env python3
"""Build the stock Ozone interface with a live semantic palette adapter.

Uses a user-owned cache and installs only a private executable/assets. Re-run
once after adapter changes; changing colors never requires recompilation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.22.2'
SOURCE_SHA256 = '245ef18c8fa8fbd9fbb5eb25cf43e17c6aace2f95c1ed99873cbd794012bb232'
FFMPEG_FIX = 'f5b422d5a81f0b4d263e2f52c8419ea9ce7467f6'
FFMPEG_FIX_SHA256 = '4b2ff0d688d6415ee21ef8a30be668852121d2465989053a9303ff664dee4351'


def patch_ozone(source, colors):
    """Only replace the built-in dark palette, retaining Ozone and its assets."""
    roles = {
        'background': 'background', 'header_footer_separator': 'high',
        'text': 'text', 'selection': 'selection', 'selection_border': 'accent',
        'entries_border': 'high', 'entries_icon': 'text',
        'text_selected': 'accent', 'message_background': 'elevated',
        'text_rgba': 'text', 'text_sidebar_rgba': 'text',
        'text_selected_rgba': 'accent', 'text_sublabel_rgba': 'muted',
        'screensaver_tint': 'accent',
    }
    match = re.search(r'static ozone_theme_t ozone_theme_dark\s*=\s*\{.*?\n\};', source, re.S)
    if not match:
        raise ValueError('Unsupported Ozone theme structure')
    block = match[0]
    for field, token in roles.items():
        color = colors[token][1:].upper()
        if field.endswith('_rgba'):
            value = f'0x{color}FF'
        elif field == 'screensaver_tint':
            value = f'0x{color}'
        else:
            value = f'COLOR_HEX_TO_FLOAT(0x{color}, 1.00f)'
        pattern = r'(?m)^\s*(?:COLOR_HEX_TO_FLOAT\([^\n]+?\)|0x[0-9A-Fa-f]+),\s*/\* ' + field + r' \*/'
        block, count = re.subn(pattern, '   ' + value + ', /* ' + field + ' */', block)
        if count != 1:
            raise ValueError(f'Unsupported Ozone color field: {field}')
    source = source[:match.start()] + block + source[match.end():]
    arrays = {
        'sidebar_background': 'background', 'sidebar_gradient_top': 'background',
        'sidebar_gradient_bottom': 'background', 'background_libretro_running': 'background',
        'border_0': 'accent', 'border_1': 'accent_pressed',
    }
    for name, token in arrays.items():
        rgb = [int(colors[token][i:i+2], 16)/255 for i in (1, 3, 5)]
        lines = []
        for vertex in range(4):
            alpha = .75 if name == 'background_libretro_running' and vertex < 2 else 1.
            lines.append('   ' + ', '.join(f'{v:.7f}f' for v in (*rgb, alpha)) + ',')
        value = '{\n' + '\n'.join(lines) + '\n};'
        pattern = r'(static float ozone_' + name + r'_dark\[16\]\s*=\s*)(?:\{.*?\};|COLOR_HEX_TO_FLOAT\([^;]+;)'
        source, count = re.subn(pattern, lambda m: m[1] + value, source, flags=re.S)
        if count != 1:
            raise ValueError(f'Unsupported Ozone color array: {name}')
    return source


def runtime_ozone(source):
    adapter=(ROOT/'styles/applications/retroarch-palette.c').read_text()
    marker='static void ozone_set_color_theme('
    if source.count(marker)!=1:raise ValueError('Unsupported Ozone theme entry point')
    source=source.replace(marker,adapter+'\n'+marker,1)
    marker='   ozone_theme_t *theme = ozone_default_theme;'
    source=source.replace(marker,marker+'\n   obsidian_palette_reload();',1)
    start=source.index('static void ozone_frame(')
    marker='   /* Reset thumbnail bar when starting/closing content */'
    index=source.index(marker,start)
    source=source[:index]+'''   if (obsidian_palette_reload())
      ozone_set_color_theme(ozone, OZONE_COLOR_THEME_BASIC_BLACK);

'''+source[index:]
    return '#include <sys/stat.h>\n'+source


def download(url, target):
    if target.exists():
        return
    pending = target.with_suffix(target.suffix + '.part')
    try:
        with urllib.request.urlopen(url, timeout=30) as response, pending.open('wb') as output:
            shutil.copyfileobj(response, output)
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)


def install_assets(cache, destination):
    assets = destination / 'assets'
    if (assets/'ozone/regular.ttf').exists() and (assets/'xmb/monochrome/png/retroarch.png').exists():
        return assets
    assets.mkdir(parents=True, exist_ok=True)
    for kind in ('ozone', 'xmb'):
        package = cache / f'{kind}.pkg.tar.zst'
        url = subprocess.check_output(['pacman', '-Sp', '--print-format', '%l',
                                      f'retroarch-assets-{kind}'], text=True).splitlines()[-1]
        # The official geo mirror also works when a distribution mirror stalls.
        official = 'https://geo.mirror.pkgbuild.com/extra/os/x86_64/' + url.rsplit('/', 1)[-1]
        signature = package.with_suffix(package.suffix + '.sig')
        download(official, package)
        download(official + '.sig', signature)
        subprocess.run(['pacman-key', '--verify', str(signature), str(package)], check=True)
        member = f'usr/share/retroarch/assets/{kind}'
        subprocess.run(['bsdtar', '-xf', str(package), '--strip-components', '4',
                        '-C', str(assets), member], check=True)
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'steel/retroarch')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8:
        parser.error('--jobs must be between 1 and 8')
    cache = args.cache_dir.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / f'retroarch-v{VERSION}.tar.gz'
    download(f'https://github.com/libretro/RetroArch/archive/refs/tags/v{VERSION}.tar.gz', archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError('RetroArch source checksum mismatch')
    source = cache / f'RetroArch-{VERSION}'
    member = f'RetroArch-{VERSION}/menu/drivers/ozone.c'
    with tarfile.open(archive) as tar:
        if not source.exists():
            tar.extractall(cache, filter='data')
        pristine = tar.extractfile(member).read().decode()
    # Upstream's version-gated FFmpeg 9 compatibility fix, also used by Arch.
    compatibility = cache / 'ffmpeg9.patch'
    download(f'https://github.com/libretro/RetroArch/commit/{FFMPEG_FIX}.patch', compatibility)
    if hashlib.sha256(compatibility.read_bytes()).hexdigest() != FFMPEG_FIX_SHA256:
        raise RuntimeError('RetroArch compatibility patch checksum mismatch')
    marker = source / '.steel-ffmpeg9'
    if not marker.exists():
        subprocess.run(['patch','--batch','-p1','-i',str(compatibility)],cwd=source,check=True)
        marker.touch()
    sys.path.insert(0, str(ROOT))
    from theme import palette
    spectrum = ROOT / 'obsidian/generated/spectrum.json'
    colors = palette(ROOT, derived=json.loads(spectrum.read_text()) if spectrum.exists() else None)
    patched = runtime_ozone(patch_ozone(pristine, colors))
    target = source / 'menu/drivers/ozone.c'
    if target.read_text() != patched:
        target.write_text(patched)
    if not (source/'.steel-configured').exists():
        subprocess.run(['./configure', '--enable-ozone', '--enable-qt'], cwd=source, check=True)
        (source/'.steel-configured').touch()
    subprocess.run(['nice', '-n', '10', 'make', f'-j{args.jobs}'], cwd=source, check=True)
    destination = ROOT/'obsidian/application-style/clients/retroarch'
    destination.mkdir(parents=True, exist_ok=True)
    assets = install_assets(cache, destination)
    pending = destination/'retroarch.new'
    shutil.copy2(source/'retroarch', pending)
    pending.replace(destination/'retroarch')
    (destination/'build.json').write_text(json.dumps({'version': VERSION, 'palette_mode':'runtime-v1',
                                                     'adapter_sha256':hashlib.sha256((ROOT/'styles/applications/retroarch-palette.c').read_bytes()).hexdigest(),
                                                     'ffmpeg_fix': FFMPEG_FIX}, indent=2)+'\n')
    print(f'Installed theme-aware RetroArch: {destination / "retroarch"}')
    print(f'Ozone assets: {assets}')


if __name__ == '__main__':
    main()
