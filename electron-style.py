#!/usr/bin/env python3
"""CSS-only adapters in private client copies; stock applications remain untouched."""
from pathlib import Path
import json, struct, hashlib, shutil, subprocess, os, tempfile

ROOT=Path(__file__).resolve().parent
STYLE=ROOT/'obsidian/application-style'

def metadata(data):
    block=4*1024*1024
    return {'size':len(data),'integrity':{'algorithm':'SHA256','hash':hashlib.sha256(data).hexdigest(),
        'blockSize':block,'blocks':[hashlib.sha256(data[i:i+block]).hexdigest() for i in range(0,len(data),block)]}}

def archive_header(path):
    with path.open('rb') as f:
        first=f.read(16); _,length,_,jsonlength=struct.unpack('<IIII',first)
        if length<8 or jsonlength>length-8: raise ValueError('Invalid ASAR header')
        header=json.loads(f.read(jsonlength))
    return header,8+length

def read_entry(path, header, start, name):
    entry=header
    for part in Path(name).parts: entry=entry['files'][part]
    with path.open('rb') as f:
        f.seek(start+int(entry['offset'])); return f.read(entry['size'])

def append_styles(source, target, css_path):
    header,start=archive_header(source)
    package=json.loads(read_entry(source,header,start,'package.json'))
    original=package['main']; package['main']='obsidian-bootstrap.cjs'
    host_setup=''
    if css_path.stem=='discord':
        host=str(source.parent.parent/'Discord')
        host_setup='process.execPath='+json.dumps(host)+'; app.setPath("exe",'+json.dumps(host)+');' 
    js=(ROOT/'styles/applications/electron-bootstrap.cjs').read_text().replace('HOST_SETUP',host_setup).replace('CSS_PATH',json.dumps(str(css_path))).replace('ORIGINAL_MAIN',json.dumps('./'+original)).replace('CONTEXT_MENU_MODULE',json.dumps(str(ROOT/'styles/applications/electron-context-menu.cjs'))).replace('NATIVE_PALETTE_PATH',json.dumps(str(STYLE/'native/palette.json')))
    offset=source.stat().st_size-start; appended=[]
    for name,data in [('package.json',json.dumps(package,separators=(',',':')).encode()),('obsidian-bootstrap.cjs',js.encode())]:
        header['files'][name]=dict(metadata(data),offset=str(offset));offset+=len(data);appended.append(data)
    encoded=json.dumps(header,separators=(',',':')).encode(); padding=(-len(encoded))%4
    pickle=struct.pack('<II',4+len(encoded)+padding,len(encoded))+encoded+b'\0'*padding
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=target.parent)
    with os.fdopen(fd,'wb') as out,source.open('rb') as f:
        out.write(struct.pack('<II',4,len(pickle)));out.write(pickle);f.seek(start)
        shutil.copyfileobj(f,out,1024*1024)
        for data in appended:out.write(data)
    os.replace(temp,target)
    h,s=archive_header(target)
    assert json.loads(read_entry(target,h,s,'package.json'))['main']=='obsidian-bootstrap.cjs'

def prepare(name, executable):
    executable=Path(executable).resolve(); folder=executable.parent
    source=folder/'resources/app.asar'
    if not source.exists(): raise FileNotFoundError(source)
    target=STYLE/'clients'/name
    stamp=target/'obsidian-source.json'
    signature={'source':str(source),'mtime':source.stat().st_mtime_ns,
               'adapter':hashlib.sha256(Path(__file__).read_bytes()+(ROOT/'styles/applications/electron-bootstrap.cjs').read_bytes()).hexdigest()}
    if stamp.exists() and json.loads(stamp.read_text())==signature:return target/executable.name
    target.mkdir(parents=True,exist_ok=True)
    for p in folder.iterdir():
        if p.name=='resources':continue
        q=target/p.name
        if p==executable:
            fresh=q.with_name(q.name+'.new')
            subprocess.run(['cp','--reflink=auto',str(p),str(fresh)],check=True)
            fresh.replace(q)
        else:
            if q.is_symlink():q.unlink()
            if not q.exists():q.symlink_to(p)
    resources=target/'resources';resources.mkdir(exist_ok=True)
    for p in (folder/'resources').iterdir():
        q=resources/p.name
        if p.name=='app.asar':continue
        if q.is_symlink():q.unlink()
        if not q.exists():q.symlink_to(p)
    append_styles(source,resources/'app.asar',STYLE/(name+'.css'))
    stamp.write_text(json.dumps(signature))
    return target/executable.name

if __name__=='__main__':
    import sys
    print(prepare(sys.argv[1],sys.argv[2]))
