#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp,sys,shutil,datetime
mode,path=sys.argv[1],Path(sys.argv[2])
if mode=='copy':sp.run(['wl-copy','--type','image/png'],input=path.read_bytes(),check=True)
elif mode=='save':
    folder=Path.home()/'Pictures/Screenshots';folder.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,folder/('Captura_'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')+'.png'))
elif mode!='preview':raise SystemExit('Acción desconocida')
