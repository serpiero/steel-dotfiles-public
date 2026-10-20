#!/usr/bin/env python3
"""Arch + Hyprland Lua installer. Backup first; no private data in source."""
from pathlib import Path
import argparse,os,sys,shutil,subprocess as sp,json,tempfile,datetime,hashlib,configparser
SOURCE=Path(__file__).resolve().parents[1]
HOME=Path.home();ROOT=HOME/'.local/share/rice-profiles';CONFIG=HOME/'.config/hypr/hyprland.lua'
PACKAGES=['base-devel','cmake','ninja','git','python','qt6-base','qt6-declarative','qt6-wayland','qt6-svg','qt6-shadertools','qt6-webengine','qt6-5compat','qt6-multimedia','qt6-imageformats','cli11','libdrm','vulkan-headers','jemalloc','libpipewire','wayland','wayland-protocols','libxcb','pam','polkit','kitty','fish','starship','swaybg','rofi','grim','wl-clipboard','cliphist','btop','breeze','breeze-icons','ttf-jetbrains-mono-nerd','noto-fonts','xdg-desktop-portal-hyprland','xdg-desktop-portal-gtk']
def run(args,**kw):return sp.run([str(x) for x in args],check=True,**kw)
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 with os.fdopen(fd,'wb') as f:f.write(data)
 os.replace(tmp,path)
def check_dependencies():
 absent=[]
 for name in ['Hyprland','git','cmake','ninja','python3','pkg-config','swaybg','kitty','fish','starship','grim','wl-copy','wl-paste','cliphist','rofi']:
  if not shutil.which(name):absent.append(name)
 for package in ['qt6-webengine','qt6-declarative','qt6-5compat','qt6-shadertools','cli11','jemalloc','libpipewire','vulkan-headers']:
  if sp.run(['pacman','-Q',package],capture_output=True).returncode:absent.append(package)
 if absent:raise RuntimeError('Missing dependencies: '+', '.join(absent)+'. Run ./install.sh --dependencies on the destination computer.')
def build(binary):run(['bash',SOURCE/'tools/build-runtime.sh',binary])
def deploy(binary):
 if ROOT.exists():raise RuntimeError(f'{ROOT} already exists. Nothing overwritten; use its own backup/update workflow.')
 old=CONFIG.read_bytes() if CONFIG.exists() else None
 backup=HOME/'.local/state/obsidian/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
 backup.mkdir(parents=True,mode=0o700)
 if old is not None:atomic(backup/'hyprland.lua',old)
 original_link=HOME/'.config/quickshell/obsidian'
 if original_link.exists() or original_link.is_symlink():raise RuntimeError('A Quickshell obsidian configuration already exists; preserve it before installation.')
 try:
  shutil.copytree(SOURCE,ROOT,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','INSTALLATION.json'))
  ROOT.chmod(0o700)
  # Expand only config/text templates, never other users' profile/session data.
  for p in ROOT.rglob('*'):
   if not p.is_file() or p.suffix not in ('.json','.qml','.lua','.conf','.rasi','.rc','.md','.txt','.ini','.sh'):continue
   try:s=p.read_text()
   except UnicodeDecodeError:continue
   if '@HOME@' in s or '@ROOT@' in s:p.write_text(s.replace('@HOME@',str(HOME)).replace('@ROOT@',str(ROOT)))
  q=ROOT/'web-runtime/bin/qs';shutil.copy2(binary,q);q.chmod(0o755)
  q=ROOT/'bin';q.mkdir(exist_ok=True);(q/'swaybg').symlink_to(shutil.which('swaybg'))
  run(['python3',ROOT/'tools/install-fonts.py',ROOT])
  (ROOT/'active').write_text('obsidian\n')
  (ROOT/'wallpaper-path').write_text(str(ROOT/'obsidian/wallpaper.svg')+'\n')
  (ROOT/'original-hyprland.lua').write_bytes(old or b'')
  # Start from destination Qt preferences, then apply this fork's palette locally.
  stock=HOME/'.config/kdeglobals'
  if stock.exists():shutil.copy2(stock,ROOT/'obsidian/app-settings/kdeglobals')
  original_link.parent.mkdir(parents=True,exist_ok=True);original_link.symlink_to(ROOT/'ui')
  atomic(CONFIG,(ROOT/'hyprland.lua').read_bytes())
  verify=dict(os.environ,RICE_ROOT=str(ROOT),RICE_PROFILE_VERIFY='obsidian')
  result=sp.run(['Hyprland','--verify-config','-c',str(CONFIG)],env=verify,capture_output=True,text=True)
  if result.returncode or 'config ok' not in result.stdout:raise RuntimeError(result.stdout+result.stderr)
  run(['python3',ROOT/'palette.py',ROOT/'obsidian/wallpaper.svg'])
  run(['python3',ROOT/'app-style.py','install-launchers'])
  manifest={'backup':str(backup),'originalConfigExisted':old is not None,'configSha256':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),'root':str(ROOT)}
  (ROOT/'INSTALLATION.json').write_text(json.dumps(manifest,indent=2)+'\n')
 except Exception:
  if old is None:CONFIG.unlink(missing_ok=True)
  else:atomic(CONFIG,old)
  if original_link.is_symlink() and original_link.resolve()==ROOT/'ui':original_link.unlink()
  # Preserve failed installation for inspection; never erase local generated state.
  if ROOT.exists():ROOT.rename(backup/'failed-installation')
  raise
 print(f'Installed and verified. Backup: {backup}\nNo current apps were closed and Hyprland was not reloaded. Log in to Hyprland to activate.\nFirefox: apply its CSS/recipe with ./tools/firefox-theme.py; see README.md.\nSpotify: install the native spotify package and use the Steel launcher; CSS is applied automatically.')
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--check',action='store_true');g.add_argument('--dependencies',action='store_true');g.add_argument('--install',action='store_true');g.add_argument('--verify-source',action='store_true');p.add_argument('--runtime',type=Path,help='Use an already built compatible Quickshell executable')
 args=p.parse_args()
 if args.verify_source:run(['python3',SOURCE/'tools/audit-export.py']);return
 if args.dependencies:
  if not shutil.which('pacman'):raise RuntimeError('This installer targets Arch/CachyOS.')
  run(['sudo','pacman','-Syu','--needed',*PACKAGES]);return
 if not shutil.which('pacman'):raise RuntimeError('This installer targets Arch/CachyOS.')
 check_dependencies()
 print('Core dependencies present. Installation target:',ROOT)
 if not args.install:return
 binary=args.runtime
 if binary is None:
  binary=HOME/'.cache/obsidian-build/quickshell-obsidian';build(binary)
 if not binary.is_file():raise RuntimeError('Runtime executable missing')
 deploy(binary.resolve())
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
