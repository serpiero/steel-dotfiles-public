#!/usr/bin/env python3
"""Private Firefox application snapshot with live Steel user stylesheet refresh."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/usr/lib/firefox')


def prepare(root=ROOT, source=SOURCE):
    root, source = Path(root).resolve(), Path(source).resolve()
    output = root / 'obsidian/application-style'
    target = output / 'clients/firefox'
    output.mkdir(parents=True, exist_ok=True)
    chrome = output / 'firefox-chrome.css'
    text = '@-moz-document url-prefix("chrome://") {\n' + (root / 'obsidian/firefox/userChrome.css').read_text() + '\n}\n'
    if not chrome.exists() or chrome.read_text() != text:
        pending = chrome.with_suffix('.tmp'); pending.write_text(text); pending.replace(chrome)
    sheets = [chrome.as_uri(), (root / 'obsidian/firefox/userContent.css').as_uri()]
    bootstrap = '''// Steel styles apply only to this private Hyprland Firefox application.
if (/hyprland/i.test(getenv("XDG_CURRENT_DESKTOP") || "")) {
 const Cc=Components.classes,Ci=Components.interfaces;
 const io=Cc["@mozilla.org/network/io-service;1"].getService(Ci.nsIIOService);
 const service=Cc["@mozilla.org/content/style-sheet-service;1"].getService(Ci.nsIStyleSheetService);
 const entries=SHEETS.map((uri,index)=>({uri,type:index===0?service.AGENT_SHEET:service.USER_SHEET,
   file:io.newURI(uri).QueryInterface(Ci.nsIFileURL).file,revision:"",active:null}));
 const refresh=()=>{for(const entry of entries){try{
   if(!entry.file.exists())continue;
   const revision=entry.file.lastModifiedTime+":"+entry.file.fileSize;
   if(revision===entry.revision)continue;
   const uri=io.newURI(entry.uri+"?steel="+encodeURIComponent(revision));
   service.loadAndRegisterSheet(uri,entry.type);
   if(entry.active&&service.sheetRegistered(entry.active,entry.type))service.unregisterSheet(entry.active,entry.type);
   entry.active=uri;entry.revision=revision;
 }catch(error){Components.utils.reportError("Steel style refresh: "+error);}}};
 refresh();
 globalThis.SteelStylesTimer=Cc["@mozilla.org/timer;1"].createInstance(Ci.nsITimer);
 SteelStylesTimer.initWithCallback({notify:refresh},1000,Ci.nsITimer.TYPE_REPEATING_SLACK);
}
'''.replace('SHEETS', json.dumps(sheets))
    signature = {'files': {name: [(source / name).stat().st_mtime_ns, (source / name).stat().st_size]
        for name in ('firefox', 'libxul.so', 'omni.ja', 'browser/omni.ja', 'application.ini')},
        'bootstrap': hashlib.sha256(bootstrap.encode()).hexdigest()}
    stamp = output / 'firefox-live-source.json'
    with (output / 'firefox-live.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if target.is_dir() and stamp.exists() and json.loads(stamp.read_text()) == signature:
            return target / 'firefox'
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='firefox-', dir=target.parent))
        previous = target.with_name('firefox-previous')
        try:
            subprocess.run(['cp', '-a', '--reflink=auto', str(source) + '/.', str(stage)], check=True)
            (stage / 'defaults/pref').mkdir(parents=True, exist_ok=True)
            (stage / 'defaults/pref/steel.js').write_text('pref("general.config.filename", "steel.cfg");\npref("general.config.obscure_value", 0);\npref("general.config.sandbox_enabled", false);\n')
            (stage / 'steel.cfg').write_text(bootstrap)
            if previous.exists():shutil.rmtree(previous)
            if target.exists():target.rename(previous)
            stage.rename(target)
            pending=stamp.with_suffix('.tmp');pending.write_text(json.dumps(signature));pending.replace(stamp)
            if previous.exists():shutil.rmtree(previous)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            if not target.exists() and previous.exists():previous.rename(target)
            raise
    return target / 'firefox'
